"""Fase 50 (50-03, D-09): ordem pendente carrega os marcos do motor e os
revalida ao preço de execução."""
import asyncio
import os
import tempfile

from app import db, pending_orders, store

MARCOS = {"stop": 19.5, "alvo": 23.5, "gatilho": 20.0, "invalidacao": 19.6}


def _fresh():
    conn = db.connect(os.path.join(tempfile.mkdtemp(prefix="b3_marcos_pend_"), "t.db"))
    store.ensure_defaults(conn)
    return conn


def _getter(preco):
    return lambda t: {"price": preco, "source": "teste"}


def _rodar(conn, preco):
    return asyncio.run(pending_orders.executar_pendentes(conn, None, _getter(preco)))


def _pos(conn):
    return next(p for p in store.get(conn, "positions") if p["t"] == "PETR4")


def test_criar_compra_grava_marcos_e_ignora_meta():
    conn = _fresh()
    r = pending_orders.criar_compra(conn, None, "PETR4", 100, 20.0,
                                    meta={"stop": 1.0, "alvo": 2.0}, marcos=MARCOS)
    assert r["marcos"] == MARCOS
    r2 = pending_orders.criar_compra(conn, None, "VALE3", 100, 20.0, meta={"stop": 1.0, "alvo": 2.0})
    assert "marcos" not in r2


def test_executa_a_20_grava_marcos_e_evento():
    conn = _fresh()
    pending_orders.criar_compra(conn, None, "PETR4", 100, 20.0, marcos=MARCOS)
    ev = _rodar(conn, 20.0)
    p = _pos(conn)
    assert (p["stop"], p["alvo"], p["stopInicial"]) == (19.5, 23.5, 19.5)
    assert any("nasce com os marcos" in e["text"] or "já nasce com os marcos" in e["text"] for e in ev)
    assert any(e["text"].startswith("Ordem pendente de compra executada: 100 PETR4 a R$ 20.00") for e in ev)


def test_executa_a_22_rr_baixo_sem_marcos():
    conn = _fresh()
    # sem gatilho/invalidação, para isolar o corte por R:R (com eles, a
    # perseguição de D-03 dispararia primeiro a 22,0)
    pending_orders.criar_compra(conn, None, "PETR4", 100, 20.0, marcos={"stop": 19.5, "alvo": 23.5})
    ev = _rodar(conn, 22.0)
    p = _pos(conn)
    assert p["stop"] is None and p["alvo"] is None
    assert any("sem os marcos do motor" in e["text"] and "R:R" in e["text"] for e in ev)


def test_executa_a_20_25_nao_persiga():
    conn = _fresh()
    pending_orders.criar_compra(conn, None, "PETR4", 100, 20.0, marcos=MARCOS)
    ev = _rodar(conn, 20.25)
    assert _pos(conn)["stop"] is None
    assert any("não persiga" in e["text"] for e in ev)


def test_ordem_sem_marcos_comportamento_atual():
    conn = _fresh()
    pending_orders.criar_compra(conn, None, "PETR4", 100, 20.0)
    ev = _rodar(conn, 20.0)
    assert len(ev) == 1
    assert ev[0]["text"] == "Ordem pendente de compra executada: 100 PETR4 a R$ 20.00 (fonte: teste)."
    assert _pos(conn)["stop"] is None
