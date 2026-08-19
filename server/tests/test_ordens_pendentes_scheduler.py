"""Fase 2 (MERC-02, plano 02-03) — guardiões do hook de execução de ordens
pendentes dentro de `scheduler_loop` e dos contadores em `status_snapshot`.

Todos os testes usam banco temp real + `asyncio.run(agent.scheduler_loop(...,
once=True))`, com `monkeypatch` de `agent.in_market_hours`/`agent.
kill_switch_on` (mesmo padrão de `test_intraday.py`) — NUNCA depende do
horário real do relógio.
"""
import asyncio
import os
import tempfile

from app import agent, db, pending_orders, store


def _conn():
    d = tempfile.mkdtemp()
    return db.connect(os.path.join(d, "b3.db"))


def _fake_quotes(prices: dict, calls: list = None):
    async def getter(tickers):
        if calls is not None:
            calls.append(list(tickers))
        return {t: {"price": prices.get(t)} for t in tickers}
    return getter


def _sem_operador(monkeypatch, aberto: bool, kill: bool = False):
    """Padrão comum: liga/desliga o gate sem tocar no relógio real e garante
    que nenhum usuário está no laço do Operador (`list_server_users`) — assim
    o único chamador de `quotes_getter` nestes testes é o bloco de pendentes,
    o que isola a contagem de chamadas."""
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **k: aberto)
    monkeypatch.setattr(agent, "kill_switch_on", lambda: kill)
    monkeypatch.setattr(agent, "list_server_users", lambda conn: [])


def test_gate_fechado_nao_toca_pendentes(monkeypatch):
    c = _conn()
    store.ensure_defaults(c, user_id="u1")
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)
    antes = pending_orders.listar(c, user_id="u1")
    _sem_operador(monkeypatch, aberto=False)

    async def getter(_tickers):
        raise AssertionError("quotes_getter não deveria ser chamado com o gate fechado")

    asyncio.run(agent.scheduler_loop(c, getter, once=True))
    assert pending_orders.listar(c, user_id="u1") == antes


def test_kill_switch_bloqueia_execucao_de_pendentes(monkeypatch):
    c = _conn()
    store.ensure_defaults(c, user_id="u1")
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)
    antes = pending_orders.listar(c, user_id="u1")
    _sem_operador(monkeypatch, aberto=True, kill=True)

    async def getter(_tickers):
        raise AssertionError("quotes_getter não deveria ser chamado com kill-switch ligado")

    asyncio.run(agent.scheduler_loop(c, getter, once=True))
    assert pending_orders.listar(c, user_id="u1") == antes


def test_usuario_sem_operador_ligado_tem_ordem_executada(monkeypatch):
    """Este é o erro fácil de cometer: a fila varre `scopes_com_pendentes`,
    não `list_server_users` — um usuário que nunca ligou o Operador no
    servidor precisa ver a ordem executar do mesmo jeito."""
    c = _conn()
    store.ensure_defaults(c, user_id="u1")  # sem agent.serverEnabled
    ag = store.get(c, "agent", user_id="u1") or {}
    assert not ag.get("serverEnabled")
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)
    _sem_operador(monkeypatch, aberto=True)
    getter = _fake_quotes({"EEEE3": 10.0})

    asyncio.run(agent.scheduler_loop(c, getter, once=True))

    assert pending_orders.listar(c, user_id="u1") == []
    pos = store.get(c, "positions", user_id="u1")
    assert any(p["t"] == "EEEE3" and p["qty"] == 100 for p in pos)


def test_lote_unico_de_cotacao_por_ticker_distinto(monkeypatch):
    c = _conn()
    store.ensure_defaults(c, user_id="u1")
    store.ensure_defaults(c, user_id="u2")
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)
    pending_orders.criar_compra(c, "u2", "EEEE3", 100, 10.0)
    pending_orders.criar_compra(c, "u2", "FFFF3", 100, 10.0)
    _sem_operador(monkeypatch, aberto=True)
    chamadas = []
    getter = _fake_quotes({"EEEE3": 10.0, "FFFF3": 10.0}, calls=chamadas)

    asyncio.run(agent.scheduler_loop(c, getter, once=True))

    # UMA chamada de lote por passada, com os tickers distintos e ordenados —
    # não uma chamada por ordem (haveria 3) nem por usuário (haveria 2).
    assert len(chamadas) == 1
    assert chamadas[0] == ["EEEE3", "FFFF3"]


def test_quotes_getter_explode_nao_derruba_o_laco(monkeypatch):
    c = _conn()
    store.ensure_defaults(c, user_id="u1")
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)
    antes = pending_orders.listar(c, user_id="u1")
    # Diferente dos outros testes: aqui o usuário FICA no laço do Operador
    # (list_server_users) para provar que o ciclo por usuário continua
    # acontecendo mesmo com o bloco de pendentes tendo explodido.
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **k: True)
    monkeypatch.setattr(agent, "kill_switch_on", lambda: False)
    store.set_config(c, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                          "appMode": "operador"}, user_id="u1")
    db.kv_set(c, "agent", {"serverEnabled": True, "mode": "executar", "autonomous": True}, user_id="u1")
    agent.LAST_USER_RUN.clear()

    async def getter(_tickers):
        raise RuntimeError("fonte de cotação fora do ar")

    asyncio.run(agent.scheduler_loop(c, getter, once=True))

    assert pending_orders.listar(c, user_id="u1") == antes  # ordem continua pendente
    assert agent.LAST_PENDING["erro"]  # o bloco registrou o próprio erro
    assert agent.LAST_RUN["usuarios"] >= 1  # o ciclo do Operador rodou mesmo assim


def test_push_execucao_e_cancelamento_ignora_warn_preexistente(monkeypatch):
    c = _conn()
    store.ensure_defaults(c, user_id="u1")
    store.ensure_defaults(c, user_id="u2")
    # u1: ordem que vai EXECUTAR (preço sobe pouco, cabe no caixa reservado + livre)
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)
    # u2: ordem que vai ser AUTO-CANCELADA (preço sobe muito além do reservado)
    pending_orders.criar_compra(c, "u2", "FFFF3", 100, 10.0)
    # warn pré-existente no log de u1 — não pode virar push (o filtro roda só
    # sobre a lista devolvida por executar_pendentes, não sobre agentLog inteiro)
    store.push_agent_log(c, [{"time": "01/01 10:00", "kind": "warn",
                              "text": "aviso qualquer do Operador, sem relação com pendentes"}],
                         user_id="u1")
    _sem_operador(monkeypatch, aberto=True)
    getter = _fake_quotes({"EEEE3": 10.5, "FFFF3": 500.0})
    pushes = []

    async def fake_notify(uid, title, body):
        pushes.append((uid, title, body))

    asyncio.run(agent.scheduler_loop(c, getter, notify_push=fake_notify, once=True))

    assert len(pushes) == 2  # 1 execução (u1) + 1 cancelamento (u2), nada do warn pré-existente
    titulos = {p[1] for p in pushes}
    assert titulos == {"Agente Boris+ (simulado)"}
    textos = [p[2] for p in pushes]
    assert any("executada" in t for t in textos)
    cancelado = [t for t in textos if "cancelada" in t]
    assert cancelado and "R$" in cancelado[0]  # motivo (preço antes/depois) no texto
    assert pending_orders.listar(c, user_id="u1") == []
    assert pending_orders.listar(c, user_id="u2") == []  # cancelada some da fila
    assert agent.LAST_PENDING["executadas"] == 1
    assert agent.LAST_PENDING["canceladas"] == 1


# --------------------------- Task 2: status_snapshot ------------------------

def test_status_snapshot_ordens_pendentes_vazio():
    c = _conn()
    store.ensure_defaults(c, user_id="u1")
    st = agent.status_snapshot(c)
    assert "ordensPendentes" in st  # estado vazio é estado (princípio 9) — a chave nunca some
    op = st["ordensPendentes"]
    assert set(["total", "escopos", "ultimoCiclo"]) <= set(op)
    assert op["total"] == 0
    assert set(["at", "executadas", "canceladas", "erro"]) <= set(op["ultimoCiclo"])


def test_status_snapshot_ordens_pendentes_conta_por_escopo():
    c = _conn()
    store.ensure_defaults(c, user_id="u1")
    store.ensure_defaults(c, user_id="u2")
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)
    pending_orders.criar_compra(c, "u1", "FFFF3", 100, 10.0)
    pending_orders.criar_compra(c, "u2", "GGGG3", 100, 10.0)
    st = agent.status_snapshot(c)
    assert st["ordensPendentes"]["total"] == 3
    assert st["ordensPendentes"]["escopos"] == 2


def test_status_snapshot_kill_switch_com_pendentes_denuncia_fila_represada():
    c = _conn()
    store.ensure_defaults(c, user_id="u1")
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)
    os.environ["B3_AGENT_KILL"] = "1"
    try:
        st = agent.status_snapshot(c)
        assert st["killSwitch"] is True
        assert st["ordensPendentes"]["total"] > 0
    finally:
        os.environ.pop("B3_AGENT_KILL", None)
