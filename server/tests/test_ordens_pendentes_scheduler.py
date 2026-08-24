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

    # Quick task 260824-i45: o espião ganhou o 4º argumento (`extra`) junto com
    # a correção do deep link. Ele SÓ COLETA — `agent.py` aguarda `notify_push`
    # dentro de um `except Exception`, e `AssertionError` é subclasse de
    # `Exception`: um assert aqui dentro seria engolido e o guardião viraria
    # vácuo. As asserções ficam depois do `asyncio.run`.
    async def fake_notify(uid, title, body, extra=None):
        pushes.append((uid, title, body, extra))

    asyncio.run(agent.scheduler_loop(c, getter, notify_push=fake_notify, once=True))

    assert len(pushes) == 2  # 1 execução (u1) + 1 cancelamento (u2), nada do warn pré-existente
    # NOTA (260824-i45, item 2): este assert travava
    # `titulos == {"Agente Boris+ (simulado)"}` — ou seja, travava o PRÓPRIO
    # defeito. O título genérico era o sintoma relatado ("o push não diz o que
    # aconteceu"); o guardião mudou de lado de propósito e agora exige o marco
    # real no título, com a declaração de simulação preservada (princípio 1 do
    # CLAUDE.md — o corpo da ordem pendente não diz "simulado").
    titulos = {p[1] for p in pushes}
    assert titulos == {"Pendente executada (simulada) · EEEE3",
                       "Pendente cancelada (simulada) · FFFF3"}
    # item 1: o toque precisa ter destino — `t` no formato que
    # `web/src/notify.js:382` valida, senão o cliente descarta em silêncio.
    destinos = {p[0]: (p[3] or {}).get("t") for p in pushes}
    assert destinos == {"u1": "EEEE3", "u2": "FFFF3"}
    textos = [p[2] for p in pushes]
    assert any("executada" in t for t in textos)
    cancelado = [t for t in textos if "cancelada" in t]
    assert cancelado and "R$" in cancelado[0]  # motivo (preço antes/depois) no texto
    assert pending_orders.listar(c, user_id="u1") == []
    assert pending_orders.listar(c, user_id="u2") == []  # cancelada some da fila
    assert agent.LAST_PENDING["executadas"] == 1
    assert agent.LAST_PENDING["canceladas"] == 1


def test_venda_pendente_tambem_executa_pelo_hook_do_scheduler(monkeypatch):
    """`executar_pendentes` já tinha guardião próprio pra VENDA (plano 02-01),
    mas por um caminho de chamada direto — este teste prova a mesma coisa
    através da FIAÇÃO NOVA do scheduler (uid vindo de `scopes_com_pendentes`,
    lote batido pelo `quotes_getter`, push filtrado), que é um caminho de
    código diferente e não coberto pelos testes de `pending_orders.py`."""
    c = _conn()
    store.ensure_defaults(c, user_id="u1")
    db.kv_set(c, "positions", [{"t": "EEEE3", "qty": 200, "avg": 8.0, "stop": None, "alvo": None}],
             user_id="u1")
    pending_orders.criar_venda(c, "u1", "EEEE3", 100)  # reserva 100, sobram 100 em positions
    _sem_operador(monkeypatch, aberto=True)
    getter = _fake_quotes({"EEEE3": 9.0})
    pushes = []

    # 260824-i45: 4º argumento (`extra`) e espião que SÓ COLETA — ver a nota no
    # teste acima.
    async def fake_notify(uid, title, body, extra=None):
        pushes.append((uid, title, body, extra))

    asyncio.run(agent.scheduler_loop(c, getter, notify_push=fake_notify, once=True))

    assert pending_orders.listar(c, user_id="u1") == []  # ordem executou, some da fila
    pos = store.get(c, "positions", user_id="u1")
    assert next(p for p in pos if p["t"] == "EEEE3")["qty"] == 100  # 200 - 100 vendidas
    historico = store.get(c, "history", user_id="u1")
    assert historico and historico[0]["type"] == "VENDA" and historico[0]["origem"] == "pendente"
    assert len(pushes) == 1 and "venda" in pushes[0][2].lower() and "executada" in pushes[0][2]
    assert pushes[0][1] == "Pendente executada (simulada) · EEEE3"
    assert (pushes[0][3] or {}).get("t") == "EEEE3"  # item 1: o toque tem destino
    assert agent.LAST_PENDING["executadas"] == 1


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
