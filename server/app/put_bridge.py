"""server/app/put_bridge.py — ponte gatilho→put (Fase 10, Plano 01, Task 2).

Este módulo é a PONTE entre um sinal de setup (gatilho de baixa detectado
pelo motor determinístico) e a put de proteção candidata — mas, NESTE
plano, só a metade "escolher o contrato certo dentro de uma cadeia já
carregada": função pura, sem rede, sem hook, sem gravação. O Plano 02
pendura o hook que chama `options_provider` e alimenta `triar_put` de
verdade; este plano garante que, quando ele pendurar, escolher um contrato
inventado é estruturalmente impossível.

D-10-A (por que a sugestão de put não mora no `signal_ledger`, ver
`db.init_db`/`10-01-PLAN.md`): a agregação `GROUP BY setup` do ADR-017 não
tem coluna discriminadora de tipo de linha — gravar ali mudaria o ranking
VISÍVEL do Radar por um caminho que nenhum grep de front-end pegaria. Este
módulo nem importa `signal_ledger`.

D-10-E (por que o piso de liquidez usa `volume`, não `total_negocios`): o
`find_tradable_options` do MCP do mydata (referência de desenho de outro
repositório, não código importável) filtra por `total_negocios` — campo que
NÃO existe no contrato ADR-004 (o adaptador de opções do mydata, função
`_clean_contract`, mapeia `quantidade_negociada → volume`). Usar o campo que
existe é o correto; inventar o que não existe seria fabricação de dado.

Escopo: Fase 10 é EOD de ponta a ponta, só put COMPRADA, uma perna, sem
margem e sem atribuição — este módulo nunca lê a perna de opção de compra
do payload e nunca produz um resultado que represente venda a descoberto.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import db, put_suggestions
from .tickers import normalize_ticker

PISO_LIQUIDEZ = 100     # quantidade_negociada mínima na sessão (D-10-E)
COLCHAO_PCT = 0.05       # alvo de strike = spot * (1 - 0,05)
OPTION_TYPE = "put"

BRT = timezone(timedelta(hours=-3))


def _numero_positivo(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def triar_put(payload: dict) -> tuple[Optional[dict], str]:
    """Escolhe UM contrato de put comprada, determinístico, a partir de uma
    cadeia real (formato devolvido pelo adaptador de opções do mydata). Nunca
    levanta: falha de dado sempre volta como `(None, motivo)`.

    Ordem exata das guardas — a primeira que fecha determina o motivo
    (parada dura #1 e #2 do contrato de autonomia vivem aqui: sem estilo de
    exercício real ou sem IV real, o contrato é PULADO, nunca completado por
    default)."""
    if not payload or payload.get("providerStatus") != "ok":
        return None, "fonte degradada"

    spot = payload.get("underlyingPrice")
    if not _numero_positivo(spot):
        return None, "sem preço do ativo-objeto"

    puts = payload.get("puts") or []
    if not puts:
        return None, "sem cadeia de puts"

    alvo = spot * (1 - COLCHAO_PCT)

    elegiveis = []
    pulados_sem_estilo = 0
    pulados_sem_iv = 0
    pulados_sem_liquidez = 0

    for contrato in puts:
        if contrato.get("optionType") != "put":
            continue  # defesa em profundidade: nunca deveria vir aqui vindo de "puts"

        strike = contrato.get("strike")
        if not isinstance(strike, (int, float)) or isinstance(strike, bool) or strike > spot:
            continue  # proteção é abaixo do preço atual — sem contador dedicado

        iv = contrato.get("impliedVolatility")
        if not _numero_positivo(iv):
            pulados_sem_iv += 1
            continue

        estilo = contrato.get("exerciseStyle")
        if not estilo:
            pulados_sem_estilo += 1
            continue

        volume = contrato.get("volume") or 0
        if volume < PISO_LIQUIDEZ:
            pulados_sem_liquidez += 1
            continue

        if not contrato.get("contractSymbol") or not contrato.get("expiration"):
            continue  # sem contador dedicado — dado estrutural ausente da fonte

        elegiveis.append(contrato)

    if not elegiveis:
        return None, "nenhuma put elegível"

    # Ordem TOTAL: distância ao alvo, depois maior volume, depois menor
    # strike, depois o próprio símbolo — sem a quádrupla completa, o teste
    # de determinismo seria uma loteria sobre listas que chegam em ordem
    # diferente (sorted é estável, mas só ajuda se a chave já for total).
    elegiveis.sort(
        key=lambda c: (
            abs(c["strike"] - alvo),
            -(c.get("volume") or 0),
            c["strike"],
            c.get("contractSymbol") or "",
        )
    )
    escolhido = elegiveis[0]

    prov = payload.get("provenance") or {}

    candidato = {
        "contrato": escolhido.get("contractSymbol"),
        "optionType": OPTION_TYPE,
        "strike": escolhido.get("strike"),
        "vencimento": escolhido.get("expiration"),
        "estiloExercicio": escolhido.get("exerciseStyle"),
        "iv": escolhido.get("impliedVolatility"),
        "delta": (escolhido.get("greeks") or {}).get("delta"),
        "premio": escolhido.get("lastPrice"),
        "volume": escolhido.get("volume"),
        "spot": spot,
        "fonte": payload.get("source"),
        "asOf": payload.get("pregao"),
        "provSha256": prov.get("sha256"),
        "provDtCaptura": prov.get("dt_captura"),
        "provCaptura": prov.get("captura"),
        "puladosSemEstilo": pulados_sem_estilo,
        "puladosSemIv": pulados_sem_iv,
        "puladosSemLiquidez": pulados_sem_liquidez,
    }
    return candidato, ""


# --------------------------------------------------------------------------- #
# Fase 10, Plano 02 — cruzamento gatilho×carteira, consulta sequencial e
# gravação com proveniência. Molde estrutural: `signal_ledger_job.py`
# (mesmo formato de gate diário/telemetria/maybe_run que nunca propaga).
# --------------------------------------------------------------------------- #

LADO_GATILHO = "baixa"      # D-10-F: só setup de baixa sobre posição comprada
MAX_TICKERS_DIA = 10        # D-10-H, mitigação 2: teto duro de tickers/dia
HHMM_DEFAULT = "09:30"      # depois do ledger (09:15), que já é depois do Radar (08:45)
K_LAST_RUN = "putBridgeLastRun"  # chave kv global (user_id=None)

# Telemetria em memória, formato copiado de `signal_ledger_job.LAST_RUN`
# (D-10-L: NÃO entra em `agent.status_snapshot` — o portal admin é superfície
# proibida por PUT-03; só aqui, para a Fase 11 poder plugar se aprovado).
LAST_RUN = {"date": None, "atLabel": None, "duracaoS": None, "erro": None,
            "sugestoes": None, "tickersAvaliados": None, "pulados": None,
            "motivo": None}


# --------------------------------------------------------------------------- #
# Gate diário (cópia estrutural de signal_ledger_job._hhmm/enabled/should_run)
# --------------------------------------------------------------------------- #

def _hhmm() -> str:
    raw = (os.environ.get("B3_PUT_BRIDGE_HHMM") or HHMM_DEFAULT).strip()
    try:
        h, m = raw.split(":")
        assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
        return f"{int(h):02d}:{int(m):02d}"
    except Exception:  # noqa: BLE001 — valor inválido cai no default
        return HHMM_DEFAULT


def enabled() -> bool:
    return not os.environ.get("B3_PUT_BRIDGE_OFF")


def should_run(now: Optional[datetime] = None, last_date: Optional[str] = None) -> bool:
    """Gating PURO (testável): dia útil, horário atingido, ainda não rodou hoje.

    Cópia estrutural de `signal_ledger_job.should_run` — mesmo gate, chave de
    env e telemetria próprias."""
    now = now or datetime.now(BRT)
    if now.weekday() >= 5:
        return False
    hh, mm = _hhmm().split(":")
    alvo = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    if now < alvo:
        return False
    return last_date != now.date().isoformat()


def last_run_date(conn) -> Optional[str]:
    return db.kv_get(conn, K_LAST_RUN, user_id=None)


# --------------------------------------------------------------------------- #
# Cruzamento (funções síncronas e puras o suficiente para teste offline)
# --------------------------------------------------------------------------- #

def tickers_com_gatilho(radar_payload: dict) -> dict[str, dict]:
    """Percorre `radar_payload["results"]` e devolve, por ticker normalizado,
    o primeiro setup ATIVO (não aposentado) de lado `LADO_GATILHO` — a mesma
    condição que faria `setups.plano_operacional` dizer VENDER (D-10-F).
    Ticker sem setup de baixa ativo fica fora do mapa."""
    out: dict[str, dict] = {}
    for r in (radar_payload or {}).get("results") or []:
        ticker = r.get("ticker")
        if not ticker:
            continue
        for s in (r.get("setups") or []):
            if s.get("lado") == LADO_GATILHO and not s.get("aposentado"):
                out[normalize_ticker(ticker)] = {
                    "setup": s.get("nome"),
                    "lado": s.get("lado"),
                    "confluencia": s.get("confluencia") or 0,
                }
                break
    return out


def carteiras_por_ticker(conn) -> dict[str, list[str]]:
    """`SELECT key, value FROM kv WHERE key LIKE 'u:%:positions'` — mesmo
    idioma de `agent._agent_rows`: `json.loads` com try/except POR LINHA
    (linha ruim é pulada, nunca aborta). O balde anônimo (chave `positions`
    sem prefixo `u:`) não casa com o LIKE — é assim que D-10-J se cumpre
    sozinho, sem filtro explícito."""
    rows = conn.execute("SELECT key, value FROM kv WHERE key LIKE 'u:%:positions'").fetchall()
    out: dict[str, set] = {}
    for key, value in rows:
        try:
            positions = json.loads(value)
        except (ValueError, TypeError):
            continue
        if not isinstance(positions, list):
            continue
        uid = key[len("u:"):-len(":positions")]
        for p in positions:
            if not isinstance(p, dict):
                continue
            t = p.get("t")
            if not t:
                continue
            out.setdefault(normalize_ticker(t), set()).add(uid)
    return {t: sorted(uids) for t, uids in out.items()}


# --------------------------------------------------------------------------- #
# Orquestração
# --------------------------------------------------------------------------- #

async def run_diario(conn, now: Optional[datetime] = None) -> dict:
    """Cruza o Radar diário JÁ ARMAZENADO (D-10-G, custo de rede zero) com as
    carteiras de todos os usuários, consulta a cadeia de opções UMA vez por
    TICKER elegível — SEQUENCIALMENTE, sem nenhum mecanismo de concorrência
    (nada de fan-out assíncrono, nada de corrotinas paralelas — D-10-H,
    mitigação 1: a ponte não pode abrir concorrência nova sobre o gate de
    orçamento compartilhado do mydata) — e grava uma sugestão por usuário com
    proveniência.

    NÃO vai para `asyncio.to_thread`: ao contrário de `signal_ledger_job`
    (CPU-bound sobre o universo inteiro), esta rodada é I/O-bound com no
    máximo `MAX_TICKERS_DIA` `await`s — mandá-la para outra thread quebraria
    a garantia de sequencialidade do laço de eventos de que a mitigação 1
    depende (dois loops de eventos concorrentes voltariam a abrir a janela
    que D-10-H fecha por construção)."""
    from . import candles as candles_mod, radar_daily  # imports locais: evita ciclo

    p = candles_mod.normalize_period(None)
    radar = radar_daily.get_stored(conn, p)
    if not radar:
        return {"sugestoes": 0, "tickers": 0, "pulados": [], "erros": [],
                "motivo": "radar do dia indisponível"}

    gatilhos = tickers_com_gatilho(radar)
    carteiras = carteiras_por_ticker(conn)
    elegiveis = sorted(
        set(gatilhos) & set(carteiras),
        key=lambda t: (-(gatilhos[t]["confluencia"]), t),
    )[:MAX_TICKERS_DIA]

    if not elegiveis:
        return {"sugestoes": 0, "tickers": 0, "pulados": [], "erros": [],
                "motivo": "nenhum gatilho sobre carteira"}

    data_pregao = (now or datetime.now(BRT)).date().isoformat()  # D-10-K

    sugestoes = 0
    pulados: list = []
    erros: list = []

    # SEQUENCIAL de propósito — PROIBIDO qualquer fan-out concorrente (gather
    # ou tasks paralelas) aqui (D-10-H, mitigação 1). Cada ticker é isolado
    # por try/except PRÓPRIO: um ticker ruim nunca aborta os demais.
    for ticker in elegiveis:
        try:
            from . import options_provider  # import local: sem ciclo de import
            payload = await options_provider.get_options(ticker)  # sem `expiration`
            candidato, motivo = triar_put(payload)
            if candidato is None:
                # Cota esgotada (OPTGATE-01) cai aqui como "fonte degradada" —
                # parada dura por item, nunca exceção.
                pulados.append({"ticker": ticker, "motivo": motivo})
                continue
            for uid in carteiras[ticker]:
                linha = {
                    "user_id": uid, "ticker": ticker, "data_pregao": data_pregao,
                    "setup": gatilhos[ticker]["setup"], "lado": gatilhos[ticker]["lado"],
                    "contrato": candidato["contrato"], "strike": candidato["strike"],
                    "vencimento": candidato["vencimento"],
                    "estilo_exercicio": candidato["estiloExercicio"],
                    "iv": candidato["iv"], "delta": candidato["delta"],
                    "premio": candidato["premio"], "volume": candidato["volume"],
                    "spot": candidato["spot"], "fonte": candidato["fonte"],
                    "as_of": candidato["asOf"], "prov_sha256": candidato["provSha256"],
                    "prov_dt_captura": candidato["provDtCaptura"],
                    "prov_captura": candidato["provCaptura"],
                }
                sugestoes += put_suggestions.registrar(conn, linha)
        except Exception as e:  # noqa: BLE001 — isola erro por ticker, nunca aborta os demais
            erros.append(f"{ticker}: {str(e)[:120]}")
            continue

    return {"sugestoes": sugestoes, "tickers": len(elegiveis), "pulados": pulados,
            "erros": erros, "motivo": None}


async def maybe_run(conn) -> Optional[dict]:
    """Hook do scheduler: roda no máximo 1x/dia útil no horário configurado.

    Cópia estrutural de `signal_ledger_job.maybe_run`: `putBridgeLastRun` só
    é gravado no caminho de SUCESSO — se a rodada falhou, ela precisa poder
    tentar de novo no próximo tick, não ficar travada até amanhã. NUNCA
    propaga exceção — este hook não pode derrubar o heartbeat, o kill-switch
    nem o ciclo de stop/alvo de nenhum usuário."""
    if not enabled():
        return None
    if not should_run(last_date=last_run_date(conn)):
        return None
    try:
        t0 = time.monotonic()
        resumo = await run_diario(conn)
        now = datetime.now(BRT)
        LAST_RUN.update(
            date=now.date().isoformat(),
            atLabel=now.strftime("%d/%m %H:%M"),
            duracaoS=round(time.monotonic() - t0, 1),
            sugestoes=resumo.get("sugestoes"),
            tickersAvaliados=resumo.get("tickers"),
            pulados=resumo.get("pulados"),
            motivo=resumo.get("motivo"),
            erro=None,
        )
        db.kv_set(conn, K_LAST_RUN, now.date().isoformat(), user_id=None)
        return resumo
    except Exception as e:  # noqa: BLE001 — nunca derruba o laço do agente
        LAST_RUN["erro"] = str(e)[:200]
        print(f"[put-bridge] rodada diária falhou: {e}")
        return None
