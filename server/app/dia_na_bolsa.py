"""Job de fechamento "Seu dia na bolsa" (Fase 51, plano 51-05).

POR QUE EXISTE (CONTEXT D-03/D-05/D-12): o app devolve ao usuário, no fim do
pregão, o que o mercado fez com o que ele viu (família 1, o "e se"), o que o
motor fez na carteira dele (família 2) e um fato raro do mercado (família 3).
Todo número do card sai do motor determinístico (`dia_na_bolsa_regras`,
`analysis_outcomes`, `store`); este módulo só ORQUESTRA: registra os setups
vistos (preços vindos do servidor, nunca do cliente — T-50-13), coleta candles
sem o provedor pago, monta o card por conta, envia o push com consentimento e
expõe as leituras das rotas. Zero chamada de IA, zero chamada do provedor pago
(emendas D-06/P-B e D-12/P-A do CONTEXT, confirmadas pelo Alex em 2026-11-18).

Molde: `snapshot_diario.py` (janela, idempotência por K_FEITAS, `maybe_run`
que nunca propaga). NÃO importa `agent` (regra de ciclo de import).

Chaves kv (contrato do plano):
  por escopo `diaNaBolsaVistos` — lista de vistos (ver `registrar_vistos`);
  por escopo `diaNaBolsa`       — card do dia ({data, vazio, familias, ...});
  globais `diaNaBolsaLastRun`, `diaNaBolsaFeitas`, `diaNaBolsaTentativa`,
          `diaNaBolsaYahooDia`.
"""
import asyncio
import os
import re
import time
from datetime import date as _date, datetime, timedelta, timezone
from typing import Optional

from . import (benchmark, candle_cache, candles as candles_mod, db,
               dia_na_bolsa_regras as R, obslog, pregao, radar_daily, setups,
               skill_ref, snapshot_diario, store, technical_snapshot, yahoo)

BRT = timezone(timedelta(hours=-3))
JOB_NOME = "diaNaBolsa"
K_LAST_RUN = "diaNaBolsaLastRun"          # kv global: data do dia FECHADO
K_FEITAS = "diaNaBolsaFeitas"             # kv global: {"data", "escopos": [...]}
K_TENTATIVA = "diaNaBolsaTentativa"       # kv global: ISO da última passada
K_YAHOO_DIA = "diaNaBolsaYahooDia"        # kv global: {"data", "chamadas", "semDado"}
K_VISTOS = "diaNaBolsaVistos"             # kv por escopo
K_CARD = "diaNaBolsa"                     # kv por escopo
VISTOS_TETO = 300
TICKERS_MAX = 60
PODA_RESOLVIDO_DIAS = 28
PODA_ABERTO_DIAS = 40
ORIGENS = ("radar", "watchlist", "carteira")
_RE_TICKER = re.compile(r"^[A-Z]{4}[0-9]{1,2}$")


# ==========================================================================
# Registro de vistos (D-03)
# ==========================================================================
def _agora() -> datetime:
    """Ponto único de relógio (patchável em teste)."""
    return datetime.now(BRT)


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v


def _plano_do_snapshot(ticker: str):
    """Fallback do visto fora do Radar: motor sobre o cache local, SEM rede.
    Devolve (plano, dataBase, close) ou None."""
    cs = candle_cache.peek(ticker, "1d")
    if not cs:
        return None
    try:
        snap = technical_snapshot.build(ticker, cs, candles_mod.normalize_period(None))
        close = snap.get("close")
        if not _num(close):
            close = cs[-1].get("close")
        plano = setups.plano_do_resultado(snap.get("setups"), close=close)
    except Exception:  # noqa: BLE001 — sem histórico válido = sem plano
        return None
    return plano, str(cs[-1].get("date") or "")[:10], close


def _podar_vistos(vistos: list, hoje: _date) -> list:
    corte_res = (hoje - timedelta(days=PODA_RESOLVIDO_DIAS)).isoformat()
    corte_ab = (hoje - timedelta(days=PODA_ABERTO_DIAS)).isoformat()
    out = []
    for v in vistos:
        est = v.get("estado")
        if isinstance(est, dict) and est.get("aberto") is False:
            if str(est.get("resolvidoEm") or v.get("vistoEm") or "") < corte_res:
                continue
        elif str(v.get("dataBase") or "") < corte_ab:
            continue
        out.append(v)
    out.sort(key=lambda v: str(v.get("vistoEm") or ""))
    return out[-VISTOS_TETO:]


def ler_vistos(conn, uid: str) -> list:
    v = db.kv_get(conn, K_VISTOS, [], user_id=uid)
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def registrar_vistos(conn, uid: str, tickers: list, origem: str,
                     agora: Optional[datetime] = None) -> dict:
    """Registra, para a conta `uid`, os setups que ela viu (D-03).

    Os preços (entrada/stop/alvo) vêm SEMPRE do servidor: da linha do arquivo
    do Radar do dia (`radar_daily.arquivo_ate`) ou, fora do Radar, do motor
    sobre o cache local (`technical_snapshot` + `setups.plano_do_resultado`).
    A função não recebe preço: o corpo do cliente nunca decide o número
    (T-50-13/T-51-11). Devolve {"registrados", "semPlano", "ignorados"}.
    """
    if origem not in ORIGENS:
        raise ValueError("origem inválida")
    if not isinstance(tickers, (list, tuple)):
        raise ValueError("tickers deve ser uma lista")
    if len(tickers) > TICKERS_MAX:
        raise ValueError(f"no máximo {TICKERS_MAX} tickers por chamada")
    if not uid:
        raise ValueError("conta obrigatória")  # nunca o balde anônimo (T-51-12)
    agora = agora or _agora()
    hoje = agora.date()
    hoje_iso = hoje.isoformat()

    res = {"registrados": 0, "semPlano": 0, "ignorados": 0}
    arq = radar_daily.arquivo_ate(conn, hoje_iso)
    por_ticker = {}
    base_arq = None
    if arq:
        data_arq, dados = arq
        base_arq = dados.get("dataBase") or data_arq
        por_ticker = {l.get("ticker"): l for l in (dados.get("linhas") or []) if isinstance(l, dict)}

    vistos = ler_vistos(conn, uid)
    chaves = {(v.get("ticker"), v.get("setup"), v.get("dataBase")) for v in vistos}
    vistos_acao = False
    vistos_no_lote = set()
    for bruto in tickers:
        t = str(bruto or "").strip().upper()
        if not _RE_TICKER.match(t) or t in vistos_no_lote:
            res["ignorados"] += 1
            continue
        vistos_no_lote.add(t)
        linha = por_ticker.get(t)
        if linha:
            novo = {"setup": linha.get("setup"), "dataBase": str(base_arq)[:10],
                    "entrada": linha.get("entrada"), "stop": linha.get("stop"),
                    "alvo": linha.get("alvo"), "entradaAMercado": bool(linha.get("entradaAMercado")),
                    "precoBase": linha.get("close"), "fonte": "radar"}
        else:
            snap = _plano_do_snapshot(t)
            plano = snap[0] if snap else None
            if (not plano or str(plano.get("decisao") or "").upper() not in ("COMPRAR", "VENDER")
                    or not all(_num(plano.get(k)) for k in ("entrada", "stop", "alvo")) or not snap[1]):
                res["semPlano"] += 1
                continue
            novo = {"setup": plano.get("setup"), "dataBase": snap[1],
                    "entrada": plano["entrada"], "stop": plano["stop"], "alvo": plano["alvo"],
                    "entradaAMercado": str(plano.get("tipo") or "").startswith("a mercado"),
                    "precoBase": snap[2] if _num(snap[2]) else None, "fonte": "snapshot"}
        if not novo.get("setup") or not _num(novo.get("entrada")) or not _num(novo.get("stop")) \
                or not _num(novo.get("alvo")):
            res["semPlano"] += 1
            continue
        if (t, novo["setup"], novo["dataBase"]) in chaves:
            continue  # já visto (dedupe): não conta como novo registro
        novo.update({"ticker": t, "origem": origem, "vistoEm": hoje_iso, "estado": None})
        vistos.append(novo)
        chaves.add((t, novo["setup"], novo["dataBase"]))
        res["registrados"] += 1
        vistos_acao = True

    vistos = _podar_vistos(vistos, hoje)
    if vistos_acao or vistos != ler_vistos(conn, uid):
        db.kv_set(conn, K_VISTOS, vistos, user_id=uid)
    return res


# ==========================================================================
# Janela e gating do job (D-12, divergências 3 e 11)
# ==========================================================================
# 17:20, não 17:15: o snapshot de fechamento ocupa [17:05, 17:15) e o Yahoo tem
# cerca de 15 min de atraso; "por volta das 17:15" (D-12) vira 17:20 para que a
# barra de hoje já esteja finalizada quando o job pedir. O texto do convite
# mantém "17:15" como horário aproximado prometido ao usuário.
HHMM_DEFAULT = "17:20"
INICIO_MIN = (17, 10)
FIM = (20, 0)
ESPERA_SNAPSHOT = (17, 40)       # espera o snapshot até aqui; depois segue sem ele
INTERVALO_PASSADAS_S = 600       # >= 10 min entre passadas (não martelar o Yahoo)
YAHOO_MAX_DEFAULT = 120          # teto diário de buscas Yahoo (somando as passadas)
MIN_BARRAS = 253                 # 252 anteriores (p95 e 52 semanas) + hoje
JANELA_YAHOO = "2y"              # a mesma janela da calibração (51-04)
CONCORRENCIA = 4
TIMEOUT_BUSCA_S = 25
EOD_FINAL = (17, 10)             # barra de hoje só é final se buscada depois disso
IBOV = "^IBOV"                   # marcador interno na lista de prioridade
MAX_LINHAS_F1 = 3
MAX_LINHAS_F2 = 10

LAST_RUN = {"date": None, "atLabel": None, "duracaoS": None, "contas": None, "cards": None,
            "vazios": None, "pushes": None, "pendentes": None, "yahooChamadas": None,
            "cacheHits": None, "semDado": None, "erros": None, "erro": None}


def enabled() -> bool:
    return not os.environ.get("B3_DIA_NA_BOLSA_OFF")


def _hhmm() -> str:
    raw = (os.environ.get("B3_DIA_NA_BOLSA_HHMM") or HHMM_DEFAULT).strip()
    try:
        h, m = (int(x) for x in raw.split(":"))
        assert 0 <= h <= 23 and 0 <= m <= 59 and INICIO_MIN <= (h, m) < FIM
        return f"{h:02d}:{m:02d}"
    except Exception:  # noqa: BLE001 — inválido cai no default
        return HHMM_DEFAULT


def _max_yahoo() -> int:
    try:
        return max(0, int(os.environ.get("B3_DIA_NA_BOLSA_MAX_YAHOO") or YAHOO_MAX_DEFAULT))
    except ValueError:
        return YAHOO_MAX_DEFAULT


def _alvo(now: datetime) -> datetime:
    hh, mm = _hhmm().split(":")
    return now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)


def _fim(now: datetime) -> datetime:
    return now.replace(hour=FIM[0], minute=FIM[1], second=0, microsecond=0)


def should_run(now: Optional[datetime] = None, last_date: Optional[str] = None) -> bool:
    """PURA: dia de PREGÃO (`is_trading_day`: fim de semana e feriado da B3 não
    rodam), dentro de [HHMM, 20:00) e dia ainda aberto."""
    now = now or _agora()
    if not pregao.is_trading_day(now.date()):
        return False
    return _alvo(now) <= now < _fim(now) and last_date != now.date().isoformat()


def deve_fechar(now: Optional[datetime] = None, last_date: Optional[str] = None) -> bool:
    """PURA: dia de pregão, passou das 20:00 e o dia ainda não fechou. É a
    passada final: gera os cards com o que houver (faltante fica fora)."""
    now = now or _agora()
    if not pregao.is_trading_day(now.date()):
        return False
    return now >= _fim(now) and last_date != now.date().isoformat()


def last_run_date(conn) -> Optional[str]:
    return db.kv_get(conn, K_LAST_RUN, None, user_id=None)


def _ler_feitas(conn, hoje: str) -> set:
    v = db.kv_get(conn, K_FEITAS, None, user_id=None)
    if not isinstance(v, dict) or v.get("data") != hoje:
        return set()
    return {u for u in (v.get("escopos") or []) if isinstance(u, str)}


def _gravar_feitas(conn, hoje: str, feitas: set) -> None:
    db.kv_set(conn, K_FEITAS, {"data": hoje, "escopos": sorted(feitas)}, user_id=None)


# ==========================================================================
# Coleta de candles: cache primeiro, Yahoo para os faltantes, teto por dia
# ==========================================================================
# Emenda D-12/P-A (51-CONTEXT.md, confirmada pelo Alex em 2026-11-18,
# reversível por B3_DIA_NA_BOLSA_MAX_YAHOO): o job NÃO usa o provedor pago.
# O cache L2 é só a primeira tentativa — o job funciona com cache vazio.
# Prioridade: vistos abertos > posições > IBOV > watchlist > universo do Radar.
_MEMO = {"data": None, "series": {}, "ibov": None, "ibovFonte": None}


def _memo(hoje: str) -> dict:
    if _MEMO["data"] != hoje:
        _MEMO.update(data=hoje, series={}, ibov=None, ibovFonte=None)
    return _MEMO


def _yahoo_dia(conn, hoje: str) -> dict:
    v = db.kv_get(conn, K_YAHOO_DIA, None, user_id=None)
    if not isinstance(v, dict) or v.get("data") != hoje:
        return {"data": hoje, "chamadas": 0, "semDado": []}
    return {"data": hoje, "chamadas": int(v.get("chamadas") or 0),
            "semDado": [t for t in (v.get("semDado") or []) if isinstance(t, str)]}


def _rotulo_fonte(src) -> str:
    return {"yahoo": "Yahoo", "brapi": "brapi"}.get(str(src or "").lower(), "cache local")


def _eod_epoch(hoje: str) -> float:
    y, m, d = (int(x) for x in hoje.split("-"))
    return datetime(y, m, d, EOD_FINAL[0], EOD_FINAL[1], tzinfo=BRT).timestamp()


def _finalizada(meta: dict, hoje: str) -> bool:
    """Barra de hoje FINALIZADA no cache: último candle de hoje E busca feita
    depois das 17:10 BRT (uma barra de hoje revalidada no meio do pregão é
    parcial e não vale como fechamento) E histórico suficiente."""
    cs = meta.get("candles") or []
    return (len(cs) >= MIN_BARRAS and cs[-1].get("date") == hoje
            and float(meta.get("at") or 0) >= _eod_epoch(hoje))


async def _buscar(t: str, sem: asyncio.Semaphore):
    async with sem:
        try:
            if t == IBOV:
                benchmark.limpar_cache()  # TTL de 15 min poderia servir a série de ontem
                d = await asyncio.wait_for(benchmark.serie_ibov(JANELA_YAHOO), TIMEOUT_BUSCA_S)
            else:
                d = await asyncio.wait_for(yahoo.get_history(t, JANELA_YAHOO, "1d"), TIMEOUT_BUSCA_S)
            return t, list((d or {}).get("candles") or [])
        except Exception:  # noqa: BLE001 — falha = sem dado nesta passada, nunca estimativa
            return t, None


async def _coletar(conn, hoje: str, ordem: list, stats: dict) -> None:
    """Preenche `_MEMO` para os tickers de `ordem` (já em ordem de prioridade)."""
    memo = _memo(hoje)
    ydia = _yahoo_dia(conn, hoje)
    por_buscar = []
    for t in ordem:
        if t == IBOV:
            if memo["ibov"] is None:
                por_buscar.append(t)
            continue
        if t in memo["series"]:
            continue
        meta = candle_cache.peek_meta(t, "1d")
        if _finalizada(meta, hoje):
            memo["series"][t] = {"candles": meta["candles"], "fonte": _rotulo_fonte(meta.get("src"))}
            stats["cacheHits"] += 1
        else:
            por_buscar.append(t)
    restante = max(0, _max_yahoo() - ydia["chamadas"])
    autorizados, fora = por_buscar[:restante], por_buscar[restante:]
    ydia["chamadas"] += len(autorizados)
    sem = asyncio.Semaphore(CONCORRENCIA)
    resultados = await asyncio.gather(*[_buscar(t, sem) for t in autorizados])
    falhos = []
    for t, cs in resultados:
        if not cs or cs[-1].get("date") != hoje:   # sem a barra de hoje não vale
            falhos.append(t)
        elif t == IBOV:
            memo["ibov"], memo["ibovFonte"] = cs, "Yahoo"
        else:
            memo["series"][t] = {"candles": cs, "fonte": "Yahoo"}
    sem_dado = [t for t in ordem if t not in memo["series"] and not (t == IBOV and memo["ibov"] is not None)]
    ydia["semDado"] = sem_dado[:200]
    db.kv_set(conn, K_YAHOO_DIA, ydia, user_id=None)
    stats["yahooChamadas"] = ydia["chamadas"]
    stats["semDado"] = sem_dado
    stats["alemDoTeto"] = fora
    if fora:
        obslog.log("agent", f"dia-na-bolsa: teto Yahoo atingido, {len(fora)} ticker(s) sem dado",
                   level="warn", tickers=",".join(fora[:20]))


# ==========================================================================
# Formatação (vals já em pt-BR; desconhecido = ausente, nunca 0)
# ==========================================================================
def _fmt_r(r) -> Optional[str]:
    if not _num(r):
        return None
    v = round(float(r), 1)
    return "0,0R" if v == 0 else f"{v:+.1f}".replace(".", ",") + "R"


def _fmt_pct(p, sinal: bool = True) -> Optional[str]:
    if not _num(p):
        return None
    v = round(float(p), 1)
    if v == 0:
        return "0,0%"
    return (f"{v:+.1f}" if sinal else f"{abs(v):.1f}").replace(".", ",") + "%"


def _sem_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def _data_br(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def _iso_do_historico(s) -> Optional[str]:
    """`history[].date` = "DD/MM/AAAA HH:MM" -> AAAA-MM-DD."""
    try:
        d, m, y = str(s).split(" ")[0].split("/")
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    except (ValueError, TypeError):
        return None


def _ultimos_pregoes(hoje: str, n: int) -> list:
    d = _date.fromisoformat(hoje)
    out = []
    for _ in range(40):
        if len(out) >= n:
            break
        if pregao.is_trading_day(d):
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return out


def _pregao_anterior(hoje: str) -> Optional[str]:
    d = _date.fromisoformat(hoje) - timedelta(days=1)
    for _ in range(15):
        if pregao.is_trading_day(d):
            return d.isoformat()
        d -= timedelta(days=1)
    return None


def _variante(uid: str, hoje: str, chave: str, extra: str = "") -> Optional[int]:
    """Índice determinístico de variante; `extra` (ex.: o ticker) entra no hash
    mas não na contagem de variantes da chave."""
    return R.variante(uid, hoje, chave + extra, skill_ref.dia_na_bolsa_n_variantes(chave))


# ==========================================================================
# Montagem do card de UMA conta
# ==========================================================================
def _contas(conn) -> list:
    rows = conn.execute("SELECT key FROM kv WHERE key LIKE 'u:%:" + K_VISTOS + "'").fetchall()
    com_vistos = set()
    for (key,) in rows:
        uid = key[len("u:"):-len(":" + K_VISTOS)]
        if uid and ler_vistos(conn, uid):
            com_vistos.add(uid)
    return sorted(set(store.scopes_com_carteira(conn)) | com_vistos)


def _tickers_posicoes(conn, uid: str) -> list:
    out = []
    for p in (store.get(conn, "positions", user_id=uid) or []):
        if isinstance(p, dict) and isinstance(p.get("t"), str) and _num(p.get("qty")) and p["qty"] != 0:
            if p["t"] not in out:
                out.append(p["t"])
    return out


def _watchlist(conn, uid: str) -> list:
    wl = store.get(conn, "watchlist", user_id=uid) or []
    return [t for t in wl if isinstance(t, str)]


def _aberto(v: dict) -> bool:
    est = v.get("estado")
    return not (isinstance(est, dict) and est.get("aberto") is False)


def _operados(conn, uid: str) -> list:
    out = []
    for h in (store.get(conn, "history", user_id=uid) or []):
        if isinstance(h, dict) and h.get("type") in ("COMPRA", "VENDA") and h.get("kind") != "opcao":
            iso = _iso_do_historico(h.get("date"))
            if iso and isinstance(h.get("t"), str):
                out.append((h["t"], iso))
    return out


def _foi_operado(v: dict, operados: list) -> bool:
    base = str(v.get("dataBase") or "")[:10]
    return any(t == v.get("ticker") and iso >= base for t, iso in operados)


def _familia1(uid: str, hoje: str, vistos: list, series: dict, operados: list, now: datetime):
    """Avalia os vistos ABERTOS (muta `estado`) e monta a família 1. Devolve
    (familia|None, vistos_mutados)."""
    ult5 = set(_ultimos_pregoes(hoje, 5))
    estados_placar, resolvidos, sem_dado, fontes = [], [], 0, set()
    for v in vistos:
        if _foi_operado(v, operados):
            continue          # visto e depois operado: não entra no "e se"
        prev = v.get("estado") if isinstance(v.get("estado"), dict) else None
        if prev is None or prev.get("aberto") is not False:
            serie = series.get(v.get("ticker"))
            est = R.estado_do_visto(v, serie["candles"], hoje) if serie else None
            if est is None:
                sem_dado += 1
                continue
            res = est.get("resultado")
            if est.get("aberto"):
                novo = {"resultado": None, "r": None, "resolvidoEm": None, "aberto": True,
                        "decorridos": est.get("decorridos")}
            else:
                hoje_res = bool(est.get("resolvidoHoje")) or (
                    res in ("expirou", "sem_gatilho") and est.get("resolvidoEm") in (None, hoje)
                    and (prev is None or prev.get("aberto") is not False))
                novo = {"resultado": res, "r": est.get("r"),
                        "resolvidoEm": hoje if hoje_res else (est.get("resolvidoEm") or hoje),
                        "aberto": False, "decorridos": est.get("decorridos")}
            v["estado"] = novo
            fontes.add(serie.get("fonte") or "")
            prev = novo
        if v.get("vistoEm") in ult5:
            estados_placar.append(prev)
        if prev.get("aberto") is False and prev.get("resolvidoEm") == hoje:
            resolvidos.append(v)
    if not resolvidos:
        return None, sem_dado
    resolvidos.sort(key=lambda v: (v.get("ticker") or "", v.get("setup") or ""))   # ticker, nunca resultado (D-04)
    linhas = []
    for v in resolvidos[:MAX_LINHAS_F1]:
        est = v["estado"]
        res = est["resultado"]
        chave = "f1_" + res
        linhas.append({
            "chave": chave, "variante": _variante(uid, hoje, chave, ":" + v["ticker"]),
            "vals": _sem_none({"T": v["ticker"], "setup": v.get("setup"),
                               "R": _fmt_r(est.get("r")) if res in ("alvo", "stop") else None,
                               "N": est.get("decorridos")}),
            "chip": "chip_" + res, "resultado": res, "ticker": v["ticker"], "setup": v.get("setup"),
            "entrada": v.get("entrada"), "stop": v.get("stop"), "alvo": v.get("alvo"), "r": est.get("r")})
    p = R.placar_semanal(estados_placar)
    return {"linhas": linhas, "excedente": max(0, len(resolvidos) - MAX_LINHAS_F1),
            "placar": {"vals": {"X": p["vistos"], "Y": p["alvo"], "Z": p["stop"], "W": p["abertos"]},
                       "semDado": sem_dado},
            "fonte": "+".join(sorted(f for f in fontes if f)) or "cache local",
            "calculadoEm": now.strftime("%H:%M")}, sem_dado


def _eventos_do_motor(conn, uid: str) -> list:
    vistos, out = set(), []
    fontes = [db.kv_get(conn, "agentLog", [], user_id=uid) or [],
              (store.get(conn, "agent", user_id=uid) or {}).get("events") or []]
    for lista in fontes:
        for e in lista:
            if not isinstance(e, dict):
                continue
            k = (e.get("time"), e.get("tag"), e.get("t"), str(e.get("marcoMotor")), e.get("text"))
            if k not in vistos:
                vistos.add(k)
                out.append(e)
    return out


def _preco_venda_do_dia(conn, uid: str, ticker: str, hoje: str) -> Optional[float]:
    for h in (store.get(conn, "history", user_id=uid) or []):
        if (isinstance(h, dict) and h.get("type") == "VENDA" and h.get("t") == ticker
                and _iso_do_historico(h.get("date")) == hoje and _num(h.get("price"))):
            return h["price"]
    return None


def _familia2(conn, uid: str, hoje: str, ibov: Optional[list], now: datetime):
    evs = R.eventos_motor_do_dia(_eventos_do_motor(conn, uid), _data_br(hoje))
    if not evs:
        return None   # carteira × IBOV sozinha é contexto, não gera card (emenda D-06/P-B)
    linhas = []
    for e in evs[:MAX_LINHAS_F2]:
        stop = e.get("stop")
        if e["chave"] == "f2_stop_executado" and stop is None:
            stop = _preco_venda_do_dia(conn, uid, e["ticker"], hoje)
        linhas.append({"chave": e["chave"], "variante": _variante(uid, hoje, e["chave"], ":" + e["ticker"]),
                       "vals": _sem_none({"T": e["ticker"], "stop": skill_ref.num_br(stop) if _num(stop) else None}),
                       "ticker": e["ticker"], "hora": e["hora"]})
    cart = R.retorno_dia(db.kv_get(conn, "equitySnapshots", [], user_id=uid) or [], hoje, "patrimonio")
    ibv = R.retorno_dia(ibov, hoje, "close") if ibov else None
    fam = {"linhas": linhas, "fonte": "motor da carteira simulada", "calculadoEm": now.strftime("%H:%M")}
    if cart is not None or ibv is not None:
        fam["carteiraIbov"] = {"carteiraPct": cart, "ibovPct": ibv,
                               "vals": _sem_none({"carteira": _fmt_pct(cart), "ibov": _fmt_pct(ibv)})}
    return fam


_SELO = {"ibov_raro": "selo_p95", "atr_ativo": "selo_atr"}


def _fato_para_card(uid: str, hoje: str, f: dict) -> dict:
    regra = f["regra"]
    chave = "f3_" + regra
    t = f.get("ticker") or "IBOV"
    vals = {"T": t}
    dados = None
    if regra == "ibov_raro":
        vals.update(pct=_fmt_pct(f.get("pct"), sinal=False),
                    direcao="subiu" if (f.get("pct") or 0) > 0 else "caiu")
    elif regra == "amplitude":
        fr = f.get("fracao")
        vals.update(fracao=f"{round(fr * 100)}%" if _num(fr) else None,
                    direcao="subiram" if f.get("direcao") == "alta" else "caíram")
        dados = {"fracao": fr, "n": f.get("n"), "direcao": f.get("direcao"), "data": hoje}
    elif regra == "gap":
        vals.update(pct=_fmt_pct(f.get("pct"), sinal=False),
                    direcao="acima" if f.get("direcao") == "alta" else "abaixo")
    elif regra == "atr_ativo":
        vals.update(multiplo=skill_ref.num_br(f["multiplo"]) if _num(f.get("multiplo")) else None)
    elif regra in ("max52", "min52"):
        dados = {"ticker": t, "lado": "máxima" if regra == "max52" else "mínima",
                 "preco": f.get("valor"), "data": hoje}
    return {"regra": regra, "chave": chave, "variante": _variante(uid, hoje, chave),
            "vals": _sem_none(vals), "perguntaChave": "f3_pergunta_" + regra,
            "selo": _SELO.get(regra),
            "conceito": {"fonte": f["conceito"]["fonte"], "id": f["conceito"]["id"], "dados": dados},
            "doUsuario": bool(f.get("doUsuario"))}


def _fatos_do_mercado(hoje: str, ibov: Optional[list], universo_series: dict) -> list:
    out = []
    if ibov:
        for f in (R.regra_ibov_raro(ibov, hoje), R.regra_extremo_52s(ibov, hoje, None)):
            if f:
                out.append({**f, "doUsuario": False})
    f = R.regra_amplitude({t: s["candles"] for t, s in universo_series.items()}, hoje)
    if f:
        out.append({**f, "doUsuario": False})
    return out


def _familia3(uid: str, hoje: str, mercado: list, tickers_usuario: list, series: dict, now: datetime):
    cands = list(mercado)
    fontes = set()
    for t in tickers_usuario:
        s = series.get(t)
        if not s:
            continue
        for f in (R.regra_atr_ativo(s["candles"], hoje, t), R.regra_gap(s["candles"], hoje, t),
                  R.regra_extremo_52s(s["candles"], hoje, t)):
            if f:
                cands.append({**f, "doUsuario": True})
                fontes.add(s.get("fonte") or "")
    escolhido = R.escolher_fato(cands)
    if not escolhido:
        return None
    if not escolhido.get("doUsuario"):
        fontes.add("Yahoo")
    return {"fato": _fato_para_card(uid, hoje, escolhido),
            "fonte": "+".join(sorted(f for f in fontes if f)) or "Yahoo",
            "calculadoEm": now.strftime("%H:%M")}


def _montar_card(conn, uid: str, hoje: str, now: datetime, memo: dict, mercado: list) -> dict:
    series = memo["series"]
    vistos = ler_vistos(conn, uid)
    f1, _sem = _familia1(uid, hoje, vistos, series, _operados(conn, uid), now)
    db.kv_set(conn, K_VISTOS, vistos, user_id=uid)     # estados atualizados
    f2 = _familia2(conn, uid, hoje, memo["ibov"], now)
    usuario = []
    for t in _tickers_posicoes(conn, uid) + _watchlist(conn, uid) + [v["ticker"] for v in vistos]:
        if t not in usuario:
            usuario.append(t)
    f3 = _familia3(uid, hoje, mercado, usuario, series, now)
    familias = {k: f for k, f in (("1", f1), ("2", f2), ("3", f3)) if f}
    card = {"data": hoje, "vazio": not familias, "geradoEm": now.isoformat(),
            "calculadoEm": now.strftime("%H:%M")}
    if familias:
        card.update(familias=familias, pushEnviado=False,
                    chamadas={k: {"chave": f"chamada_f{k}",
                                  "variante": _variante(uid, hoje, f"chamada_f{k}"), "vals": {}}
                              for k in familias})
    else:
        card = {"data": hoje, "vazio": True}
    return card


# ==========================================================================
# O job
# ==========================================================================
def _tentativa_recente(conn, now: datetime) -> bool:
    v = db.kv_get(conn, K_TENTATIVA, None, user_id=None)
    try:
        ult = datetime.fromisoformat(v)
    except (TypeError, ValueError):
        return False
    return 0 <= (now - ult).total_seconds() < INTERVALO_PASSADAS_S


async def _run(conn, now: datetime, final: bool) -> dict:
    hoje = now.date().isoformat()
    t0 = time.monotonic()
    contas = _contas(conn)
    feitas = _ler_feitas(conn, hoje)
    pendentes_job = [u for u in contas if u not in feitas]
    stats = {"yahooChamadas": 0, "cacheHits": 0, "semDado": [], "alemDoTeto": []}
    res = {"contas": len(contas), "cards": 0, "vazios": 0, "pushes": 0, "pendentes": 0, "erros": 0}
    if not pendentes_job:
        return {**res, **stats, "fechou": True}

    # Ordem de prioridade (emenda D-12/P-A): vistos abertos > posições > IBOV >
    # watchlist > universo do Radar. Sem duplicata, mantém a 1ª posição.
    ordem, vistos_por, pos_por, wl_por = [], {}, {}, {}

    def add(t):
        if t and t not in ordem:
            ordem.append(t)
    for uid in pendentes_job:
        vistos_por[uid] = ler_vistos(conn, uid)
        pos_por[uid] = _tickers_posicoes(conn, uid)
        wl_por[uid] = _watchlist(conn, uid)
        for v in vistos_por[uid]:
            if _aberto(v):
                add(v["ticker"])
    for uid in pendentes_job:
        for t in pos_por[uid]:
            add(t)
    add(IBOV)
    for uid in pendentes_job:
        for t in wl_por[uid]:
            add(t)
    arq = radar_daily.get_arquivo(conn, hoje)
    from . import scanner  # import local: scanner puxa módulos pesados
    universo = [t for t in ((arq or {}).get("universo") or []) if isinstance(t, str)] \
        or list(scanner.DEFAULT_UNIVERSE)
    for t in universo:
        add(t)

    await _coletar(conn, hoje, ordem, stats)
    memo = _memo(hoje)
    mercado = _fatos_do_mercado(hoje, memo["ibov"], {t: memo["series"][t] for t in universo if t in memo["series"]})

    feitas_acum = set(feitas)
    for uid in pendentes_job:
        try:
            deps = [v["ticker"] for v in vistos_por[uid] if _aberto(v)] + pos_por[uid]
            falta = [t for t in deps if t not in memo["series"]] + ([IBOV] if memo["ibov"] is None else [])
            if falta and not final:
                res["pendentes"] += 1      # W5: sem card parcial; tenta de novo no próximo ciclo
                continue
            card = _montar_card(conn, uid, hoje, now, memo, mercado)
            db.kv_set(conn, K_CARD, card, user_id=uid)
            res["vazios" if card.get("vazio") else "cards"] += 1
            if not card.get("vazio"):
                res["pushes"] += await _enviar_push(conn, uid, card, hoje)
            feitas_acum.add(uid)
        except Exception as e:  # noqa: BLE001 — erro por conta isolado; volta no próximo ciclo
            res["erros"] += 1
            print(f"[dia-na-bolsa] conta falhou: {type(e).__name__}")
        await asyncio.sleep(0)
    if feitas_acum != feitas:
        _gravar_feitas(conn, hoje, feitas_acum)
    res["duracaoS"] = round(time.monotonic() - t0, 1)
    res["fechou"] = final or res["pendentes"] == 0
    return {**res, **stats}


def _linha_do_card(familias: dict, k: str) -> Optional[dict]:
    """Primeira linha renderizável da família `k` (chave, variante, vals)."""
    f = familias.get(k)
    if not isinstance(f, dict):
        return None
    if k == "3":
        return f.get("fato") if isinstance(f.get("fato"), dict) else None
    linhas = f.get("linhas") or []
    return linhas[0] if linhas else None


def _corpo_push(card: dict, modo_prefs: str) -> str:
    """Corpo = 1ª linha da 1ª família na ordem do modo da conta (D-13)."""
    fams = card.get("familias") or {}
    voc = "operador" if modo_prefs == "operador" else "educacional"
    for k in R.ordem_familias(modo_prefs, [int(x) for x in fams]):
        linha = _linha_do_card(fams, str(k))
        if linha:
            txt = skill_ref.dia_na_bolsa_txt(voc, linha["chave"], linha.get("variante") or 0,
                                             linha.get("vals") or {})
            if txt:
                return txt
    return ""


async def _enviar_push(conn, uid: str, card: dict, hoje: str) -> int:
    """Push "Seu dia na bolsa" (D-13). Só sai com: card não vazio, consentimento
    (`quer_fechamento`, FAIL-CLOSED), token registrado, reserva do teto de
    engajamento e nenhum envio anterior no dia. Devolve 1 se enviou, 0 se não.

    `extra` leva só `kind` e NUNCA `t` (mesma razão de `radar_daily.run_daily`):
    o cliente filtra o toque por ticker válido em `t`, e o card não tem ticker
    único; eleger um repetiria o erro de ticker trocado. Web/PWA sem token APNs
    não recebe push (D-13)."""
    try:
        from . import push  # import local: sem ciclo de import
        if card.get("vazio") or card.get("pushEnviado") or not card.get("familias"):
            return 0
        if not push.quer_fechamento(conn, uid):
            return 0
        if not (db.kv_get(conn, "pushTokens", [], user_id=uid) or []):
            return 0
        modo = push.prefs_for(conn, uid).get("modo")
        corpo = _corpo_push(card, modo if modo in ("estudo", "operador") else "estudo")
        if not corpo:
            return 0
        if not push.reservar_engajamento(conn, uid, hoje, "fechamento"):
            return 0
        voc = "operador" if modo == "operador" else "educacional"
        card["pushEnviado"] = True          # antes do envio: no máximo 1 por conta por dia
        db.kv_set(conn, K_CARD, card, user_id=uid)
        await push.send_to_user(conn, uid, skill_ref.DIA_NA_BOLSA[voc]["titulo"], corpo,
                                som=False, prioridade="5", extra={"kind": "fechamento"})
        return 1
    except Exception as e:  # noqa: BLE001 — push é best-effort; o card já está gravado
        print(f"[dia-na-bolsa] push falhou: {type(e).__name__}")
        return 0


def e_se_de_ontem(conn, uid: str, hoje) -> Optional[dict]:
    """O "e se" de ONTEM para o Radar (51-07): o primeiro visto resolvido em
    alvo OU stop no pregão anterior, por ordem de ticker (sem preferir alvo,
    D-04). `{"chave": "corpo_ontem_alvo"|"corpo_ontem_stop", "T": ticker}`."""
    hoje_iso = hoje.isoformat() if isinstance(hoje, _date) else str(hoje)
    ant = _pregao_anterior(hoje_iso)
    if not ant:
        return None
    operados = _operados(conn, uid)
    achados = []
    for v in ler_vistos(conn, uid):
        est = v.get("estado")
        if (isinstance(est, dict) and est.get("aberto") is False and est.get("resolvidoEm") == ant
                and est.get("resultado") in ("alvo", "stop") and not _foi_operado(v, operados)):
            achados.append(v)
    if not achados:
        return None
    v = sorted(achados, key=lambda x: (x.get("ticker") or "", x.get("setup") or ""))[0]
    return {"chave": "corpo_ontem_" + v["estado"]["resultado"], "T": v["ticker"]}


async def maybe_run(conn, now: Optional[datetime] = None) -> Optional[dict]:
    """Hook do scheduler. NUNCA propaga. `diaNaBolsaLastRun` só é gravado quando
    o dia FECHA: nenhuma conta pendente por falta de dado, ou a passada final
    (>= 20:00), que gera os cards com o que houver."""
    try:
        now = now or _agora()
        if not enabled():
            return None
        hoje = now.date().isoformat()
        last = last_run_date(conn)
        final = deve_fechar(now, last)
        if not final and not should_run(now, last):
            return None
        if not final:
            if snapshot_diario.last_run_date(conn) != hoje and (now.hour, now.minute) < ESPERA_SNAPSHOT:
                return None            # espera o ponto de fechamento da carteira
            if _tentativa_recente(conn, now):
                return None
        db.kv_set(conn, K_TENTATIVA, now.isoformat(), user_id=None)
        res = await _run(conn, now, final)
        LAST_RUN.update(date=hoje, atLabel=now.strftime("%d/%m %H:%M"), duracaoS=res.get("duracaoS"),
                        contas=res["contas"], cards=res["cards"], vazios=res["vazios"],
                        pushes=res["pushes"], pendentes=res["pendentes"],
                        yahooChamadas=res["yahooChamadas"], cacheHits=res["cacheHits"],
                        semDado=res["semDado"][:20], erros=res["erros"], erro=None)
        db.marcar_job(conn, JOB_NOME, LAST_RUN)
        obslog.log("agent", f"dia-na-bolsa: cards={res['cards']} vazios={res['vazios']} "
                            f"pendentes={res['pendentes']} yahoo={res['yahooChamadas']} "
                            f"cache={res['cacheHits']} semDado={len(res['semDado'])}")
        if res.get("fechou"):
            db.kv_set(conn, K_LAST_RUN, hoje, user_id=None)
        return res
    except Exception as e:  # noqa: BLE001 — nunca derruba o laço do agente
        LAST_RUN["erro"] = str(e)[:200]
        print(f"[dia-na-bolsa] rodada falhou: {type(e).__name__}")
        return None


# ==========================================================================
# Leitura para as rotas (contrato do payload do card)
# ==========================================================================
def _ultimas_4_semanas(hoje: _date) -> list:
    return [{"data": (d := hoje - timedelta(days=27 - i)).isoformat(), "pregao": pregao.is_trading_day(d)}
            for i in range(28)]


def _rotulo_conceito(conc: dict, modo: str) -> str:
    voc = "operador" if modo == "operador" else "educacional"
    try:
        if conc.get("fonte") == "conceito":
            from . import conceitos
            return conceitos.CONCEITOS[conc["id"]]["titulo"][voc]
        from . import kb
        v = kb.verbete(conc["id"])
        return kb.formatar(v, modo)["titulo"] if v else ""
    except Exception:  # noqa: BLE001 — rótulo é decoração; o id basta
        return ""


def payload_para(conn, uid: str, modo: str, agora: Optional[datetime] = None) -> dict:
    """Payload da rota GET do card (51-07) e do componente (51-08). `vals` já
    formatados; conceito com rótulo no vocabulário do modo."""
    from . import push
    agora = agora or _agora()
    hoje = agora.date()
    card = db.kv_get(conn, K_CARD, None, user_id=uid)
    saida = None
    if isinstance(card, dict) and not card.get("vazio") and isinstance(card.get("familias"), dict):
        fams = card["familias"]
        ordem = R.ordem_familias(modo, [int(k) for k in fams])
        chamadas = card.get("chamadas") or {}
        primeira = chamadas.get(str(ordem[0])) if ordem else None
        familias = {k: dict(v) for k, v in fams.items()}
        f3 = familias.get("3")
        if f3 and isinstance(f3.get("fato"), dict):
            fato = dict(f3["fato"])
            fato["conceito"] = {**fato["conceito"], "rotulo": _rotulo_conceito(fato["conceito"], modo)}
            familias["3"] = {**f3, "fato": fato}
        atrasado = bool(pregao.is_trading_day(hoje) and (agora.hour, agora.minute) >= (17, 30)
                        and str(card.get("data")) < hoje.isoformat())
        saida = {"data": card["data"], "dataLabel": _data_br(card["data"])[:5],
                 "calculadoEm": card.get("calculadoEm"), "atrasado": atrasado, "ordem": ordem,
                 "chamada": primeira, "familias": familias}
    est = push.estado_fechamento(conn, uid)
    return {"card": saida, "convite": not est["decidido"], "fechamento": est,
            "ultimas4Semanas": _ultimas_4_semanas(hoje)}
