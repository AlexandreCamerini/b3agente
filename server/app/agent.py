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
# Intervalo do ciclo POR USUÁRIO (agent.intervalMin, min): o laço acorda na
# cadência base (env B3_AGENT_INTERVAL_S) e só roda o ciclo de um usuário se já
# passou o intervalo DELE desde a última passada — assim cada conta escolhe a
# frequência (default 15 min). A granularidade mínima é a cadência base.
LAST_USER_RUN: dict = {}          # {uid: epoch da última passada efetiva}


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
        "intervalMin": max(1, min(240, int(ag.get("intervalMin") or 15))),
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


def _agent_rows(conn) -> list:
    """(uid, ag) de todo usuário com seção `agent` no kv. Extraído de
    list_server_users para ser reusado sem duplicar a query — o contrato de
    list_server_users NÃO muda (mesma varredura, mesmo retorno)."""
    rows = conn.execute("SELECT key, value FROM kv WHERE key LIKE 'u:%:agent'").fetchall()
    out = []
    import json as _json
    for key, value in rows:
        try:
            ag = _json.loads(value)
        except (ValueError, TypeError):
            continue
        if isinstance(ag, dict):
            out.append((key[len("u:"):-len(":agent")], ag))
    return out


def list_server_users(conn) -> list:
    """Usuários com o agente server-side LIGADO (varre o kv 'u:<id>:agent')."""
    return [uid for uid, ag in _agent_rows(conn) if ag.get("serverEnabled")]


def list_protecao_sem_operador(conn) -> list:
    """qa/41 (H6): usuários com stop/alvo ARMADO numa posição e o Operador no
    servidor DESLIGADO.

    Por que isto existe: "proteção armada" (stop/alvo na posição) e "Operador
    no servidor" (serverEnabled) são controles SEPARADOS, e armar o primeiro
    não liga o segundo. `/api/cycle` e `/api/agent/run-now` — os caminhos do
    app ABERTO — chamam run_cycle_for direto, sem consultar serverEnabled;
    este laço consulta. Resultado: quem arma o stop sem ligar o Operador vê a
    ordem executar com o app aberto e NADA acontecer com o app fechado.
    Parece bug do agente; é assimetria de contrato entre os dois caminhos.

    O laço não pode ligar o Operador por conta própria (é decisão do usuário —
    e ligar sozinho seria pior: executaria ordem que ninguém pediu). O que ele
    PODE é parar de ser silencioso: contar no status e avisar no Diário."""
    out = []
    for uid, ag in _agent_rows(conn):
        if ag.get("serverEnabled"):
            continue                                   # já é cuidado pelo laço
        par = agent_params(ag)
        if not (par["rules"]["stop"] or par["rules"]["alvo"]):
            continue                                   # nem stop nem alvo valem para ele
        for p in (store.get(conn, "positions", user_id=uid) or []):
            if ((par["rules"]["stop"] and p.get("stop") is not None) or
                    (par["rules"]["alvo"] and p.get("alvo") is not None)):
                out.append(uid)
                break
    return out


def _avisar_protecao_sem_operador(conn) -> int:
    """qa/41 (H6): avisa NO DIÁRIO, 1x/dia, quem tem proteção armada sem o
    Operador ligado. Gate persistido no kv (não em memória) — senão o deploy
    zeraria e o aviso repetiria. Best-effort: nunca derruba o laço."""
    n = 0
    hoje = _today()
    for uid in list_protecao_sem_operador(conn):
        try:
            if db.kv_get(conn, "avisoProtecaoSemOperador", None, user_id=uid) == hoje:
                continue
            store.push_agent_log(conn, [{"time": _now_str(), "kind": "warn", "text": (
                "Você tem stop/alvo armado numa posição, mas o Operador no servidor está "
                "DESLIGADO. Sem ele, a proteção só é avaliada enquanto o app está aberto — "
                "com o app fechado, ninguém acompanha o preço por você. Ligue em "
                "Perfil → Operador para o servidor acompanhar suas posições no pregão."
            )}], user_id=uid)
            db.kv_set(conn, "avisoProtecaoSemOperador", hoje, user_id=uid)
            n += 1
        except Exception as e:  # noqa: BLE001 — aviso nunca derruba o laço
            print(f"[agent] aviso de proteção sem operador falhou para {uid[:8]}…: {e}")
    return n


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
        # P2 (liveness): heartbeat PERSISTIDO a CADA tick, FORA do gate de pregão.
        # O corpo do ciclo (e o registro de passada) só roda dentro do pregão, então
        # off-hours não havia sinal nenhum e o deploy zerava o estado em memória —
        # impossível distinguir "vivo, pregão fechado" de "morto". O heartbeat bate
        # sempre, sobrevive ao deploy (kv/SQLite) e é o que o status expõe como lacoVivo.
        try:
            db.kv_set(conn, "agentHeartbeat", {
                "ts": time.time(),
                "pregaoAberto": in_market_hours(),
                "atBRT": datetime.now(BRT).strftime("%d/%m %H:%M"),
            }, user_id=None)
        except Exception as e:  # noqa: BLE001 — heartbeat nunca derruba o laço
            print(f"[agent] heartbeat: {e}")
        try:
            if radar_fetch is not None and not kill_switch_on():
                from . import radar_daily  # import local: sem ciclo de import
                await radar_daily.maybe_run(conn, radar_fetch, notify_push=notify_push)
                from . import analysis_outcomes  # qa/30 (Fase A): import local, sem ciclo de import
                await analysis_outcomes.maybe_run(conn, radar_fetch)
                # qa/36 (F10.2): aquece o cache de fundamentos do universo 1x/dia
                # (o TTL de 7 dias garante que só rebusca o vencido). Cache-only
                # no scan → o job é a única via de rede; best-effort.
                from . import fundamentals, scanner  # import local: sem ciclo
                await fundamentals.maybe_warm(conn, scanner.get_universe())
            if not kill_switch_on() and in_market_hours():
                # qa/41 (H6): durante o pregão, quem tem proteção armada e o
                # Operador desligado é avisado no Diário (1x/dia). O laço passa
                # por cima dessa gente por contrato — mas em silêncio ela achava
                # que estava protegida.
                _avisar_protecao_sem_operador(conn)
                _t0 = time.monotonic()
                _erros = []
                LAST_RUN.update(at=datetime.now(BRT).strftime("%d/%m %H:%M"), usuarios=0, executadas=0, erro=None)
                _agora = time.time()
                for uid in list_server_users(conn):
                    # Gate por usuário: respeita o intervalMin DELE (default 15).
                    _ag = store.get(conn, "agent", user_id=uid) or {}
                    _int_s = agent_params(_ag)["intervalMin"] * 60
                    _ult = LAST_USER_RUN.get(uid, 0)
                    if _agora - _ult < _int_s - 1:
                        continue  # ainda não deu o intervalo deste usuário
                    LAST_USER_RUN[uid] = _agora
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
    # P2 (liveness): heartbeat persistido (sobrevive a deploy e bate fora do pregão).
    intervalo = interval_s or int(os.environ.get("B3_AGENT_INTERVAL_S") or INTERVAL_S_DEFAULT)
    hb = db.kv_get(conn, "agentHeartbeat", None, user_id=None) or {}
    hb_ha_s = int(time.time() - hb["ts"]) if hb.get("ts") else None
    # vivo se bateu dentro de ~2,5 intervalos (tolera 1 tick perdido + folga)
    laco_vivo = hb_ha_s is not None and hb_ha_s < intervalo * 2.5
    return {
        "killSwitch": kill_switch_on(),
        "pregaoAberto": in_market_hours(),
        "heartbeat": {
            "atBRT": hb.get("atBRT"),
            "haS": hb_ha_s,
            "pregaoAbertoNoTick": hb.get("pregaoAberto"),
            "lacoVivo": laco_vivo,
        },
        "radarDiario": dict(radar_daily.LAST_DAILY),  # FASE 4 (1.3)
        "avaliacaoAnalises": dict(analysis_outcomes.LAST_EVAL),  # qa/30 (Fase A)
        "intervaloS": interval_s or int(os.environ.get("B3_AGENT_INTERVAL_S") or INTERVAL_S_DEFAULT),
        "usuariosHabilitados": len(list_server_users(conn)),
        # qa/41 (H6): quantos têm stop/alvo armado com o Operador DESLIGADO —
        # o laço os ignora por contrato e eles executam só com o app aberto.
        # > 0 aqui explica "o Operador só funciona quando abro o app" sem que
        # exista bug nenhum no laço. Contagem, nunca identidade (sem PII).
        "protecaoSemOperador": len(list_protecao_sem_operador(conn)),
        "ultimoCiclo": dict(LAST_RUN),
        "proximaPassadaEmS": prox,
        "passadas": list(reversed(RUN_HISTORY)),  # mais recente primeiro
        "agoraBRT": datetime.now(BRT).strftime("%d/%m %H:%M"),
    }
