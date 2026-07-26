"""FASE 3.5 — agente server-side com relógio e provedor FAKES."""
import asyncio
import os
import re
import tempfile
from datetime import datetime, timezone, timedelta

from app import agent, db, store


def _conn():
    d = tempfile.mkdtemp()
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    return c


def _seed(c, positions, ag):
    db.kv_set(c, "positions", positions, user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    ag_full = {"autonomous": True, **ag}
    db.kv_set(c, "agent", ag_full, user_id="u1")


def _quotes(prices):
    async def getter(tickers):
        return {t: {"price": prices.get(t)} for t in tickers}
    return getter


def _run(c, prices):
    return asyncio.run(agent.run_cycle_for(c, "u1", _quotes(prices)))


def test_executa_venda_no_stop_e_registra_log():
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = _run(c, {"PETR4": 37.5})
    assert r["executed"] == 1
    assert db.kv_get(c, "positions", user_id="u1") == []           # vendeu
    log = db.kv_get(c, "agentLog", [], user_id="u1")
    # F3: o ciclo grava uma linha-resumo APÓS a execução ("Ciclo ... em Xs"),
    # então a venda não é mais necessariamente log[-1] — checar por conteúdo.
    assert log and any("stop atingido" in e["text"] for e in log)


def test_modo_sinalizar_nao_opera():
    c = _conn()
    _seed(c, [{"t": "VALE3", "qty": 100, "avg": 60.0, "stop": 58.0}],
          {"serverEnabled": True, "mode": "sinalizar"})
    r = _run(c, {"VALE3": 57.0})
    assert r["executed"] == 0
    assert len(db.kv_get(c, "positions", user_id="u1")) == 1       # posição intacta
    assert any("apenas sinalizar" in e["text"] for e in r["events"])


def test_teto_diario_de_operacoes():
    c = _conn()
    _seed(c, [{"t": "AAAA3", "qty": 100, "avg": 10, "stop": 9.5},
              {"t": "BBBB4", "qty": 100, "avg": 10, "stop": 9.5}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 1})
    r = _run(c, {"AAAA3": 9.0, "BBBB4": 9.0})
    assert r["executed"] == 1
    assert len(db.kv_get(c, "positions", user_id="u1")) == 1       # 2ª ficou
    assert any("Teto diário" in e["text"] for e in r["events"])


def test_teto_por_valor_de_operacao():
    c = _conn()
    _seed(c, [{"t": "CCCC3", "qty": 1000, "avg": 50.0, "stop": 49.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 5, "maxValorOp": 1000.0})
    r = _run(c, {"CCCC3": 48.0})                                    # op = 48.000
    assert r["executed"] == 0
    assert any("Teto por operação" in e["text"] for e in r["events"])


def test_trailing_sobe_o_stop_e_nunca_desce():
    c = _conn()
    _seed(c, [{"t": "DDDD3", "qty": 100, "avg": 10.0, "stop": 9.0}],
          {"serverEnabled": True, "mode": "executar", "rules": {"trailing": True}, "trailingPct": 5})
    _run(c, {"DDDD3": 12.0})                                        # stop deve ir p/ 11.40
    pos = db.kv_get(c, "positions", user_id="u1")[0]
    assert pos["stop"] == 11.4
    _run(c, {"DDDD3": 11.5})                                        # 10.93 < 11.40 → não desce
    assert db.kv_get(c, "positions", user_id="u1") == [] or db.kv_get(c, "positions", user_id="u1")[0]["stop"] == 11.4


def test_kill_switch_e_janela_de_pregao():
    os.environ["B3_AGENT_KILL"] = "1"
    try:
        assert agent.kill_switch_on()
    finally:
        os.environ.pop("B3_AGENT_KILL", None)
    assert not agent.kill_switch_on()
    brt = timezone(timedelta(hours=-3))
    assert agent.in_market_hours(datetime(2026, 7, 1, 14, 0, tzinfo=brt))      # qua 14h
    assert not agent.in_market_hours(datetime(2026, 7, 4, 14, 0, tzinfo=brt))  # sábado
    assert not agent.in_market_hours(datetime(2026, 7, 1, 20, 0, tzinfo=brt))  # após pregão


def test_scheduler_uma_passada_so_usuarios_habilitados():
    c = _conn()
    _seed(c, [{"t": "EEEE3", "qty": 100, "avg": 10, "stop": 9.5}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    store.ensure_defaults(c, user_id="u2")                          # u2 SEM serverEnabled
    db.kv_set(c, "positions", [{"t": "FFFF3", "qty": 100, "avg": 10, "stop": 9.5}], user_id="u2")
    db.kv_set(c, "agent", {"autonomous": True}, user_id="u2")
    assert agent.list_server_users(c) == ["u1"]
    # qa/42: LAST_USER_RUN é estado global do módulo (gate de intervalMin) e
    # test_fase3_operador.py roda o mesmo scheduler com o mesmo uid — sem este
    # clear, o teste passa ou falha CONFORME A ORDEM da suíte.
    agent.LAST_USER_RUN.clear()
    brt_ok = datetime(2026, 7, 1, 14, 0, tzinfo=timezone(timedelta(hours=-3)))
    assert agent.in_market_hours(brt_ok)
    asyncio.run(agent.scheduler_loop(c, _quotes({"EEEE3": 9.0, "FFFF3": 9.0}), interval_s=1, once=True))
    if agent.in_market_hours():                                     # roda de fato só em horário de pregão
        assert db.kv_get(c, "positions", user_id="u1") == []
    assert len(db.kv_get(c, "positions", user_id="u2")) == 1        # u2 NUNCA é tocado pelo servidor


def test_textos_do_agente_sem_verbo_de_ordem():
    c = _conn()
    _seed(c, [{"t": "GGGG3", "qty": 100, "avg": 10, "stop": 9.5, "alvo": 12.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = _run(c, {"GGGG3": 12.5})
    todos = " ".join(e["text"].lower() for e in r["events"])
    for pat in (r"\bcompre\b", r"\bvenda\s+agora\b", r"\bentre\s+agora\b", r"\bdeve\s+comprar\b"):
        assert not re.search(pat, todos), pat


def test_status_snapshot_shape():
    c = _conn()
    _seed(c, [], {"serverEnabled": True})
    st = agent.status_snapshot(c, interval_s=60)
    assert set(["killSwitch", "pregaoAberto", "intervaloS", "usuariosHabilitados", "ultimoCiclo", "agoraBRT"]) <= set(st)
    assert st["usuariosHabilitados"] == 1 and st["intervaloS"] == 60


def test_heartbeat_persistido_prova_laco_vivo_fora_do_pregao():
    """P2: sem heartbeat, status_snapshot não distingue vivo de morto. Antes de
    qualquer tick, lacoVivo=False; após um tick do laço (mesmo FORA do pregão),
    o heartbeat persiste e lacoVivo=True — sobrevive a deploy (é kv/SQLite)."""
    c = _conn()
    _seed(c, [], {"serverEnabled": True})
    # nada bateu ainda → não há prova de vida
    st0 = agent.status_snapshot(c, interval_s=60)
    assert st0["heartbeat"]["lacoVivo"] is False and st0["heartbeat"]["haS"] is None
    # um tick FORA do pregão (sábado): corpo do ciclo não roda, mas o heartbeat sim
    sabado = datetime(2026, 7, 4, 14, 0, tzinfo=timezone(timedelta(hours=-3)))
    assert not agent.in_market_hours(sabado)
    agent.LAST_USER_RUN.clear()
    asyncio.run(agent.scheduler_loop(c, _quotes({}), interval_s=1, once=True))
    st1 = agent.status_snapshot(c, interval_s=60)
    assert st1["heartbeat"]["lacoVivo"] is True
    assert st1["heartbeat"]["haS"] is not None and st1["heartbeat"]["haS"] < 60
    assert st1["heartbeat"]["atBRT"]  # rótulo do último tick presente
