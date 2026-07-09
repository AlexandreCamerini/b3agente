"""FASE 3 — Agente autônomo SERVER-SIDE.

O ciclo que rodava só com o app aberto (setInterval no App.jsx chamando
/api/cycle) agora TAMBÉM roda no servidor, por usuário logado com o agente
habilitado — o app pode estar fechado. A lógica do /api/cycle foi PORTADA
para cá (run_cycle_for) e o endpoint passou a reusá-la: uma implementação só.

Parâmetros por usuário (seção `agent`, decisão 3.2):
  serverEnabled  bool   — liga o modo servidor (exige conta; anônimo segue foreground)
  mode           str    — "executar" (vende no stop/alvo) | "sinalizar" (só registra/avisa)
  rules          dict   — {stop: bool, alvo: bool, trailing: bool}
  trailingPct    float  — distância do trailing stop (default 5%)
  maxOpsDia      int    — teto de operações executadas por dia (default 3)
  maxValorOp     float  — teto de valor por operação (0 = sem teto)

Guardrails: opera SOMENTE a carteira simulada; textos descritivos, nunca
imperativos; kill-switch global (env B3_AGENT_KILL=1) e por usuário
(serverEnabled=false). Fora do pregão (~10h–18h BRT, seg–sex) não roda.
"""
import asyncio
import os
import time
from datetime import datetime, timedelta, timezone

from . import db, store

INTERVAL_S_DEFAULT = 300
BRT = timezone(timedelta(hours=-3))

# BLOCO D3 — visibilidade: o scheduler grava aqui o resultado da última
# passada; GET /api/agent/status expõe (fim do "não sei por que não roda").
LAST_RUN = {"at": None, "usuarios": 0, "executadas": 0, "erro": None}

# FASE 3 (Operador): observabilidade de verdade — anel com as últimas passadas
# (duração, usuários, execuções, erros) + próxima passada + guard de
# sobreposição de ciclo por usuário (um run-now não colide com o scheduler).
RUN_HISTORY: list = []           # [{at, duracaoS, usuarios, executadas, erros:[..]}]
RUN_HISTORY_MAX = 12
NEXT_RUN_AT = {"ts": None}       # epoch da próxima passada do scheduler
_CYCLE_BUSY: set = set()          # escopos com ciclo em andamento


def _push_run_history(entry: dict):
    RUN_HISTORY.append(entry)
    del RUN_HISTORY[:-RUN_HISTORY_MAX]


def _today() -> str:
    return datetime.now(BRT).strftime("%Y-%m-%d")


def _now_str() -> str:
    return datetime.now(BRT).strftime("%d/%m %H:%M")


def kill_switch_on() -> bool:
    return (os.environ.get("B3_AGENT_KILL") or "").strip() in ("1", "true", "TRUE", "yes")


def in_market_hours(now: datetime = None) -> bool:
    """Janela aproximada do pregão B3 (BRT): seg–sex, 10:00–17:59."""
    now = now or datetime.now(BRT)
    return now.weekday() < 5 and 10 <= now.hour < 18


def agent_params(ag: dict) -> dict:
    """Normaliza a seção agent para os parâmetros do servidor (defaults sãos)."""
    ag = ag or {}
    rules = ag.get("rules") if isinstance(ag.get("rules"), dict) else {}
    return {
        "serverEnabled": bool(ag.get("serverEnabled")),
        "mode": ag.get("mode") if ag.get("mode") in ("executar", "sinalizar") else ("executar" if ag.get("autonomous") else "sinalizar"),
        "rules": {"stop": rules.get("stop", True) is not False,
                  "alvo": rules.get("alvo", True) is not False,
                  "trailing": bool(rules.get("trailing"))},
        "trailingPct": float(ag.get("trailingPct") or 5.0),
        "maxOpsDia": int(ag.get("maxOpsDia") or 3),
        "maxValorOp": float(ag.get("maxValorOp") or 0),
    }


def _ops_today(ag: dict) -> int:
    return int(ag.get("opsToday") or 0) if ag.get("opsDate") == _today() else 0


def _bump_ops(conn, scope, ag):
    n = _ops_today(ag) + 1
    db.kv_set(conn, "agent", {**ag, "opsToday": n, "opsDate": _today()}, user_id=scope)
    return n


async def run_cycle_for(conn, scope, quotes_getter, origem: str = "agendado") -> dict:
    """UM ciclo do agente para UM escopo (usuário ou anônimo). Portado do
    /api/cycle e estendido com modo/tetos/trailing. Retorna {events, executed}.
    `quotes_getter(tickers) -> {t: {price, ...}}` é injetado (fake nos testes).

    FASE 3 (Operador): instrumentado — guard de sobreposição, duração medida,
    início/erros registrados no agentLog (o Diário da UI mostra o que houve)."""
    key = scope or "__anon__"
    if key in _CYCLE_BUSY:
        return {"events": [], "executed": 0, "skipped": "ciclo já em andamento"}
    _CYCLE_BUSY.add(key)
    t0 = time.monotonic()
    try:
        return await _run_cycle_inner(conn, scope, quotes_getter, origem, t0)
    except Exception as e:  # noqa: BLE001 — erro do ciclo vira LOG, nunca silêncio
        if scope:
            store.push_agent_log(conn, [{"time": _now_str(), "kind": "error",
                                         "text": f"Ciclo ({origem}) FALHOU após {time.monotonic()-t0:.1f}s: {e}"}], user_id=scope)
        raise
    finally:
        _CYCLE_BUSY.discard(key)


async def _run_cycle_inner(conn, scope, quotes_getter, origem: str, t0: float) -> dict:
    positions = store.get(conn, "positions", user_id=scope) or []
    ag = store.get(conn, "agent", user_id=scope) or {}
    par = agent_params(ag)
    quotes_data = await quotes_getter([p["t"] for p in positions]) if positions else {}
    sem_cotacao = [p["t"] for p in positions if (quotes_data.get(p["t"]) or {}).get("price") is None]
    events, executed = [], 0
    for pos in list(positions):
        q = quotes_data.get(pos["t"]) or {}
        price = q.get("price")
        if price is None:
            continue
        # Trailing stop (regra opcional): SOBE o stop conforme o preço avança;
        # nunca desce. Registro descritivo — o app ensina o mecanismo.
        if par["rules"]["trailing"] and pos.get("stop") is not None:
            novo = round(price * (1 - par["trailingPct"] / 100.0), 2)
            if novo > pos["stop"]:
                store.set_position(conn, pos["t"], stop=novo, alvo=None, has_stop=True, has_alvo=False, user_id=scope)
                events.append({"time": _now_str(), "kind": "info",
                               "text": f"Trailing: stop de {pos['t']} ajustado para R$ {novo:.2f} ({par['trailingPct']:.0f}% abaixo do preço)."})
                pos = {**pos, "stop": novo}
        breach_stop = par["rules"]["stop"] and pos.get("stop") is not None and price <= pos["stop"]
        hit_alvo = par["rules"]["alvo"] and pos.get("alvo") is not None and price >= pos["alvo"]
        if not (breach_stop or hit_alvo):
            continue
        motivo = "stop atingido" if breach_stop else "alvo atingido"
        valor_op = price * (pos.get("qty") or 0)
        if par["mode"] != "executar":
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Sinal do agente: {pos['t']} com {motivo} (R$ {price:.2f}). Modo 'apenas sinalizar' — nenhuma operação feita."})
            continue
        if _ops_today(ag) + executed >= par["maxOpsDia"]:
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Teto diário de operações atingido ({par['maxOpsDia']}). {pos['t']} com {motivo} ficou registrado, sem execução."})
            continue
        if par["maxValorOp"] > 0 and valor_op > par["maxValorOp"]:
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Teto por operação (R$ {par['maxValorOp']:.2f}) excedido em {pos['t']} (R$ {valor_op:.2f}). Registrado, sem execução."})
            continue
        store.sell(conn, pos["t"], price, user_id=scope)
        executed += 1
        _bump_ops(conn, scope, store.get(conn, "agent", user_id=scope) or ag)
        events.append({"time": _now_str(), "kind": "buy",
                       "text": f"Proteção simulada: {pos['t']} vendido ({motivo}) a R$ {price:.2f}."})
    dur = time.monotonic() - t0
    resumo = f"Ciclo ({origem}) em {dur:.1f}s · {len(positions)} posição(ões) · {executed} execução(ões)"
    if sem_cotacao:
        resumo += f" · SEM cotação: {', '.join(sem_cotacao)} (provável rate-limit do provedor — tento no próximo ciclo)"
        events.append({"time": _now_str(), "kind": "warn", "text": resumo})
    elif not events:
        events.append({"time": _now_str(), "kind": "info",
                       "text": resumo + ". Nenhum stop/alvo atingido."})
    else:
        events.append({"time": _now_str(), "kind": "info", "text": resumo})
    store.push_events(conn, events, user_id=scope)
    if scope:  # log persistente do agente (3.3a) só faz sentido por usuário
        store.push_agent_log(conn, events, user_id=scope)
    return {"events": events, "executed": executed}


def list_server_users(conn) -> list:
    """Usuários com o agente server-side LIGADO (varre o kv 'u:<id>:agent')."""
    rows = conn.execute("SELECT key, value FROM kv WHERE key LIKE 'u:%:agent'").fetchall()
    out = []
    import json as _json
    for key, value in rows:
        try:
            ag = _json.loads(value)
        except (ValueError, TypeError):
            continue
        if isinstance(ag, dict) and ag.get("serverEnabled"):
            out.append(key[len("u:"):-len(":agent")])
    return out


async def scheduler_loop(conn, quotes_getter, notify_push=None, interval_s: int = None, once: bool = False,
                         radar_fetch=None):
    """Laço do servidor: a cada N min (env B3_AGENT_INTERVAL_S), dentro do
    pregão e sem kill-switch, roda o ciclo de cada usuário habilitado.
    `notify_push(user_id, title, body)` (opcional) envia APNs por ação executada.
    FASE 4 (1.3): `radar_fetch` (opcional) habilita a varredura diária do Radar
    — 1x/dia útil no horário configurado, FORA do gate de pregão (8h45 é
    pré-abertura), reusando este mesmo laço (sem segundo scheduler).
    qa/30 (Fase A): o mesmo `radar_fetch` também alimenta a avaliação diária
    das análises pendentes (analysis_outcomes) — outro hook no mesmo laço,
    sem scheduler novo."""
    interval = interval_s or int(os.environ.get("B3_AGENT_INTERVAL_S") or INTERVAL_S_DEFAULT)
    while True:
        try:
            if radar_fetch is not None and not kill_switch_on():
                from . import radar_daily  # import local: sem ciclo de import
                await radar_daily.maybe_run(conn, radar_fetch, notify_push=notify_push)
                from . import analysis_outcomes  # qa/30 (Fase A): import local, sem ciclo de import
                await analysis_outcomes.maybe_run(conn, radar_fetch)
            if not kill_switch_on() and in_market_hours():
                _t0 = time.monotonic()
                _erros = []
                LAST_RUN.update(at=datetime.now(BRT).strftime("%d/%m %H:%M"), usuarios=0, executadas=0, erro=None)
                for uid in list_server_users(conn):
                    LAST_RUN["usuarios"] += 1
                    try:
                        r = await run_cycle_for(conn, uid, quotes_getter, origem="agendado")
                        LAST_RUN["executadas"] += r["executed"]
                        if notify_push and r["executed"]:
                            acts = [e["text"] for e in r["events"] if e.get("kind") == "buy"]
                            for txt in acts:
                                try:
                                    await notify_push(uid, "Agente BolsIA (simulado)", txt)
                                except Exception:  # noqa: BLE001 — push é best-effort
                                    pass
                    except Exception as e:  # noqa: BLE001 — 1 usuário não derruba o laço
                        _erros.append(f"{uid[:8]}…: {e}")
                        print(f"[agent] ciclo de {uid} falhou: {e}")
                _push_run_history({"at": LAST_RUN["at"], "duracaoS": round(time.monotonic() - _t0, 1),
                                   "usuarios": LAST_RUN["usuarios"], "executadas": LAST_RUN["executadas"],
                                   "erros": _erros})
                if _erros:
                    LAST_RUN["erro"] = "; ".join(_erros)[:300]
        except Exception as e:  # noqa: BLE001
            print(f"[agent] laço: {e}")
        if once:
            return
        NEXT_RUN_AT["ts"] = time.time() + interval
        await asyncio.sleep(interval)


def status_snapshot(conn, interval_s: int = None) -> dict:
    """BLOCO D3 — estado observável do Operador IA no servidor."""
    prox = None
    if NEXT_RUN_AT["ts"]:
        prox = max(0, int(NEXT_RUN_AT["ts"] - time.time()))
    from . import radar_daily  # import local: sem ciclo de import
    from . import analysis_outcomes  # qa/30 (Fase A): import local, sem ciclo de import
    return {
        "killSwitch": kill_switch_on(),
        "pregaoAberto": in_market_hours(),
        "radarDiario": dict(radar_daily.LAST_DAILY),  # FASE 4 (1.3)
        "avaliacaoAnalises": dict(analysis_outcomes.LAST_EVAL),  # qa/30 (Fase A)
        "intervaloS": interval_s or int(os.environ.get("B3_AGENT_INTERVAL_S") or INTERVAL_S_DEFAULT),
        "usuariosHabilitados": len(list_server_users(conn)),
        "ultimoCiclo": dict(LAST_RUN),
        "proximaPassadaEmS": prox,
        "passadas": list(reversed(RUN_HISTORY)),  # mais recente primeiro
        "agoraBRT": datetime.now(BRT).strftime("%d/%m %H:%M"),
    }
