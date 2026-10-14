"""Snapshot de fechamento do patrimonio de cada conta (quick 261013-u7w, 2026-10-13).

Antes, `equitySnapshots` so ganhava ponto quando o app abria (web: POST
/api/snapshot; iOS: so no aparelho), com data UTC. Este job grava, em todo dia
de pregao, UM ponto de fechamento por conta, calculado por regra deterministica
(`store.patrimonio_conta`, principio 5) e carimbado com origem/fonte/hora
(principio 3).

Contrato (resumo das decisoes D1-D7 do CONTEXT):

  * Janela [HHMM, 17:15) BRT de dia de pregao (`pregao.is_trading_day`), HHMM
    default 17:05. O limite 17:15 e o fim do orcamento da brapi
    (`brapi_budget._ORCAMENTO_FIM`): depois disso o getter nao teria cotacao.
  * Cada tick da janela processa so as contas AINDA NAO gravadas no dia (kv
    `snapshotDiarioFeitas`, sobrevive a reinicio). Conta pulada por ticker sem
    cotacao ou por excecao individual volta no tick seguinte.
  * `snapshotDiarioLastRun` = hoje FECHA o dia: quando nao sobra conta pendente,
    ou no primeiro tick com `now >= 17:15` (que so fecha e NAO chama o getter).
  * Ativo aberto sem cotacao valida => a conta nao ganha ponto (principio 4: o
    servidor nunca grava patrimonio com preco medio silencioso).
  * `hora` = horario BRT da GRAVACAO do ponto, nao da cotacao (o cache de spot
    pode servir um preco de minutos antes). `fonte` = `source` efetiva das
    cotacoes usadas pela conta, ou None para conta sem acao.
  * Pressupoe `B3_AGENT_INTERVAL_S <= 300` (default): so assim cabem >= 2 ticks
    na janela de 10 min. O status expoe `intervaloOk` e `perdido`.
  * O kill-switch do agente NAO bloqueia este job: ele mede e nao executa ordem
    (decisao do orquestrador, 2026-10-13, quick 261013-u7w).
  * Posicoes e caixa sao lidos juntos, sem `await` entre a leitura e o upsert:
    o ponto e o patrimonio "na hora da gravacao", nao garantidamente a carteira
    de 16:55 (existem caminhos que executam fora do pregao — ver SUMMARY).
"""
import asyncio
import math
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import db, obslog, pregao, store

JOB_NOME = "snapshotDiario"
K_LAST_RUN = "snapshotDiarioLastRun"      # kv global: data do dia FECHADO
K_FEITAS = "snapshotDiarioFeitas"         # kv global: {"data", "escopos": [...]}
K_TENTATIVA = "snapshotDiarioTentativa"   # kv global: data do ultimo dia com tick
HHMM_DEFAULT = "17:05"
INICIO_MIN = pregao.FECHAMENTO            # (16, 55): antes disso seria valor intraday
FIM = (17, 15)                            # = brapi_budget._ORCAMENTO_FIM
INTERVALO_MAX_S = 300                     # W2: >= 2 ticks em [17:05, 17:15)
INTERVALO_DEFAULT_S = 300                 # = agent.INTERVAL_S_DEFAULT (sem importar agent)
BRT = timezone(timedelta(hours=-3))
MAX_TICKERS_SEM_COTACAO = 20

_CHAVES = ("date", "atLabel", "duracaoS", "contas", "gravadas", "puladasSemCotacao", "erros",
           "perdidasNaJanela", "perdido", "tickers", "tickersSemCotacao", "fonte", "erro")

# Telemetria em memoria + espelho no kv via `db.marcar_job` (260911-axj).
# Contagens e tickers de mercado; NUNCA user_id/e-mail (T-u7w-04).
# `tickers` = quantos tickers distintos o ultimo tick pediu ao getter.
LAST_RUN = {"date": None, "atLabel": None, "duracaoS": None, "contas": None, "gravadas": None,
            "puladasSemCotacao": None, "erros": None, "perdidasNaJanela": None, "perdido": None,
            "tickers": None, "tickersSemCotacao": None, "fonte": None, "erro": None}


def _agora() -> datetime:
    """Ponto unico de relogio (patchavel em teste)."""
    return datetime.now(BRT)


def _hhmm() -> str:
    raw = (os.environ.get("B3_SNAPSHOT_DIARIO_HHMM") or HHMM_DEFAULT).strip()
    try:
        h, m = raw.split(":")
        h, m = int(h), int(m)
        assert 0 <= h <= 23 and 0 <= m <= 59
        assert INICIO_MIN <= (h, m) < FIM
        return f"{h:02d}:{m:02d}"
    except Exception:  # noqa: BLE001 — invalido ou fora de [16:55, 17:15) cai no default
        return HHMM_DEFAULT


def janela_hhmm() -> str:
    return _hhmm()


def enabled() -> bool:
    return not os.environ.get("B3_SNAPSHOT_DIARIO_OFF")


def intervalo_ok() -> bool:
    try:
        iv = int(os.environ.get("B3_AGENT_INTERVAL_S") or INTERVALO_DEFAULT_S)
    except ValueError:
        iv = INTERVALO_DEFAULT_S
    return iv <= INTERVALO_MAX_S


def _alvo(now: datetime) -> datetime:
    hh, mm = _hhmm().split(":")
    return now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)


def _fim(now: datetime) -> datetime:
    return now.replace(hour=FIM[0], minute=FIM[1], second=0, microsecond=0)


def should_run(now: Optional[datetime] = None, last_date: Optional[str] = None) -> bool:
    """PURA: dia de pregao, dentro de [HHMM, 17:15) e dia ainda aberto. Aceita
    QUALQUER tick da janela (nao so o primeiro): e o que permite retentar."""
    now = now or _agora()
    if not pregao.is_trading_day(now.date()):
        return False
    return _alvo(now) <= now < _fim(now) and last_date != now.date().isoformat()


def deve_fechar(now: Optional[datetime] = None, last_date: Optional[str] = None) -> bool:
    """PURA: dia de pregao, janela encerrada (>= 17:15) e dia ainda aberto."""
    now = now or _agora()
    if not pregao.is_trading_day(now.date()):
        return False
    return now >= _fim(now) and last_date != now.date().isoformat()


def last_run_date(conn) -> Optional[str]:
    return db.kv_get(conn, K_LAST_RUN, None, user_id=None)


def _ler_feitas(conn, hoje: str) -> set:
    """Contas ja gravadas no dia. `data` diferente de hoje => zera (J24)."""
    v = db.kv_get(conn, K_FEITAS, None, user_id=None)
    if not isinstance(v, dict) or v.get("data") != hoje:
        return set()
    return {u for u in (v.get("escopos") or []) if isinstance(u, str)}


# 2026-10-13 (quick 261013-u7w, orquestrador): a versao anterior relia, ordenava e
# regravava a lista INTEIRA a cada conta — O(n^2) no event loop (teste de fumaca
# com 52.642 contas do banco de carga levou minutos). O upsert do snapshot e
# idempotente por `data` (fechamento sobre fechamento), entao basta persistir o
# conjunto em LOTES: um reinicio no meio regrava no maximo um lote, sem efeito.
LOTE_FEITAS = 200


def _gravar_feitas(conn, hoje: str, feitas: set) -> None:
    """Persiste o conjunto do dia (chamado a cada LOTE_FEITAS contas e no fim)."""
    db.kv_set(conn, K_FEITAS, {"data": hoje, "escopos": sorted(feitas)}, user_id=None)


def _preco_valido(q) -> bool:
    p = q.get("price") if isinstance(q, dict) else None
    return isinstance(p, (int, float)) and not isinstance(p, bool) and math.isfinite(p) and p > 0


def _qty(p) -> float:
    q = p.get("qty") if isinstance(p, dict) else None
    if isinstance(q, bool):
        return 0.0
    try:
        v = float(q)
    except (TypeError, ValueError):
        return 0.0
    return v if math.isfinite(v) else 0.0


def _fonte_conta(positions, quotes) -> Optional[str]:
    fontes = set()
    for p in positions:
        if _qty(p) == 0:
            continue
        s = (quotes.get(p.get("t")) or {}).get("source")
        if isinstance(s, str) and s:
            fontes.add(s)
    return "+".join(sorted(fontes)) or None


async def run_tick(conn, quotes_getter, now: datetime) -> dict:
    """Um tick da janela: processa so as contas pendentes (ver docstring do
    modulo). Devolve {contas, gravadas, pendentesRestantes, puladasSemCotacao,
    erros, tickers, tickersSemCotacao, fonte, erro}."""
    hoje = now.date().isoformat()
    db.kv_set(conn, K_TENTATIVA, hoje, user_id=None)   # "houve rodada hoje" (perdido)
    todas = store.scopes_com_carteira(conn)
    feitas = _ler_feitas(conn, hoje)
    pendentes = [u for u in todas if u not in feitas]
    res = {"contas": len(todas), "gravadas": len(feitas), "pendentesRestantes": len(pendentes),
           "puladasSemCotacao": 0, "erros": 0, "tickers": 0, "tickersSemCotacao": [],
           "fonte": None, "erro": None}

    tickers = set()
    for uid in pendentes:
        try:
            for p in (store.get(conn, "positions", user_id=uid) or []):
                if isinstance(p, dict) and isinstance(p.get("t"), str) and _qty(p) != 0:
                    tickers.add(p["t"])
        except Exception:  # noqa: BLE001 — conta corrompida e contada no passo por conta
            continue
    tickers = sorted(tickers)
    res["tickers"] = len(tickers)

    quotes = {}
    if tickers:
        # W1: UM getter por tick; o getter faz N chamadas brapi seriais (cache
        # de spot primeiro). Orcamento esgotado no meio vira `price: None`.
        quotes = await quotes_getter(tickers) or {}
        validas = [t for t in tickers if _preco_valido(quotes.get(t))]
        if not validas:
            res["erro"] = "nenhuma cotação válida no lote"
            res["tickersSemCotacao"] = tickers[:MAX_TICKERS_SEM_COTACAO]
            return res
        res["fonte"] = _fonte_conta([{"t": t, "qty": 1} for t in validas], quotes)

    sem_cot = set()
    gravadas_tick = 0
    feitas_acum = set(feitas)
    for uid in pendentes:
        try:
            positions = store.get(conn, "positions", user_id=uid) or []
            cash = store.get(conn, "cash", user_id=uid)
            opcoes = store.get(conn, "optionPositions", user_id=uid) or []
            reservado = store.caixa_reservado(conn, user_id=uid)
            # opcoes: sem cotacao de contrato => regra vigente de `valor_opcoes`
            # (premio de abertura), igual ao patrimonio exibido hoje (D2).
            r = store.patrimonio_conta(positions, quotes, cash, reservado, opcoes, None)
            if r["semCotacao"]:
                res["puladasSemCotacao"] += 1
                sem_cot.update(r["semCotacao"])
            else:
                # `hora` e a da GRAVACAO, nao a da cotacao (W3). Sem await entre
                # a leitura acima e este upsert (SQLite sincrono no event loop).
                store.upsert_snapshot(
                    conn,
                    {"data": hoje, "patrimonio": r["patr"], "caixa": r["cash"], "posicoesValor": r["posVal"]},
                    user_id=uid, origem="fechamento", fonte=_fonte_conta(positions, quotes),
                    hora=now.strftime("%H:%M"))
                feitas_acum.add(uid)
                gravadas_tick += 1
                if gravadas_tick % LOTE_FEITAS == 0:
                    _gravar_feitas(conn, hoje, feitas_acum)
        except Exception:  # noqa: BLE001 — erro por conta isolado; ela volta no proximo tick
            res["erros"] += 1
        await asyncio.sleep(0)
    if gravadas_tick:
        _gravar_feitas(conn, hoje, feitas_acum)
    res["gravadas"] += gravadas_tick
    res["pendentesRestantes"] = len(pendentes) - gravadas_tick
    res["tickersSemCotacao"] = sorted(sem_cot)[:MAX_TICKERS_SEM_COTACAO]
    return res


def _fechar_dia(conn, now: datetime) -> dict:
    """Janela encerrada (>= 17:15): fecha o dia SEM chamar o getter."""
    hoje = now.date().isoformat()
    todas = store.scopes_com_carteira(conn)
    feitas = _ler_feitas(conn, hoje)
    perdidas = len([u for u in todas if u not in feitas])
    tentou = db.kv_get(conn, K_TENTATIVA, None, user_id=None) == hoje
    perdido = (not tentou) and perdidas > 0
    LAST_RUN.update(date=hoje, atLabel=now.strftime("%d/%m %H:%M"), contas=len(todas),
                    gravadas=len(feitas), perdidasNaJanela=perdidas, perdido=perdido)
    db.marcar_job(conn, JOB_NOME, LAST_RUN)
    db.kv_set(conn, K_LAST_RUN, hoje, user_id=None)
    if perdidas:
        obslog.log("agent", f"snapshot-diario: {perdidas} conta(s) sem ponto de fechamento (janela encerrada)",
                   level="warn", perdido=perdido)
    return {"fechado": True, "perdidasNaJanela": perdidas, "perdido": perdido}


async def maybe_run(conn, quotes_getter, now: Optional[datetime] = None) -> Optional[dict]:
    """Hook do scheduler. NUNCA propaga excecao (nao derruba heartbeat, stop/alvo
    nem os demais jobs). `snapshotDiarioLastRun` so e gravado quando o dia FECHA
    (tudo gravado, ou janela encerrada)."""
    try:
        now = now or _agora()
        if not enabled():
            return None
        last = last_run_date(conn)
        if deve_fechar(now, last):
            return _fechar_dia(conn, now)
        if not should_run(now, last):
            return None
        t0 = time.monotonic()
        res = await run_tick(conn, quotes_getter, now)
        LAST_RUN.update(
            date=now.date().isoformat(), atLabel=now.strftime("%d/%m %H:%M"),
            duracaoS=round(time.monotonic() - t0, 1), contas=res["contas"], gravadas=res["gravadas"],
            puladasSemCotacao=res["puladasSemCotacao"], erros=res["erros"], perdidasNaJanela=0,
            perdido=False, tickers=res["tickers"], tickersSemCotacao=res["tickersSemCotacao"],
            fonte=res["fonte"], erro=res["erro"])
        db.marcar_job(conn, JOB_NOME, LAST_RUN)
        obslog.log("agent", f"snapshot-diario: gravadas={res['gravadas']}/{res['contas']} "
                            f"semCotacao={res['puladasSemCotacao']} erros={res['erros']}",
                   tickersSemCotacao=",".join(res["tickersSemCotacao"]))
        if res["pendentesRestantes"] == 0 and res["erro"] is None:
            db.kv_set(conn, K_LAST_RUN, now.date().isoformat(), user_id=None)
        return res
    except Exception as e:  # noqa: BLE001 — nunca derruba o laco do agente
        LAST_RUN["erro"] = str(e)[:200]
        print(f"[snapshot-diario] rodada falhou: {type(e).__name__}")
        return None
