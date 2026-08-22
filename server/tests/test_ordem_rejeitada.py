"""Guardiao do rastro da ordem rejeitada (FIX-C02, Plano 04-02).

Cobre: entrada rejeitada com os 9 campos do contrato, price=None preservado,
motivo truncado em 200 chars, poda de CAP_REJEICOES=100 preservando TODAS as
executadas intercaladas, buy/sell carimbando status="executada", e histórico
legado (sem a chave status) continuando legível e intocado.

Padrao da casa: `_fresh_db()` com SQLite temp por teste, sem conftest, sem
mock de SQLite (ver test_ordens_pendentes.py).
"""
import os
import tempfile

import pytest

from app import db, store


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_test_rejeicao_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)
    return conn, path


# --------------------------------------------------------------------------
# registrar_rejeicao — contrato da entrada
# --------------------------------------------------------------------------

def test_registrar_rejeicao_grava_contrato_completo():
    conn, _ = _fresh_db()
    entry = store.registrar_rejeicao(conn, "COMPRA", "PETR4", 200, 33.5, "Caixa insuficiente para esta ordem.")
    topo = store.get(conn, "history")[0]
    assert topo == entry
    assert topo["status"] == "rejeitada"
    assert topo["pnl"] is None
    assert topo["motivo"]
    assert topo["type"] == "COMPRA"
    assert topo["t"] == "PETR4"
    assert topo["qty"] == 200
    assert topo["price"] == 33.5
    assert topo["origem"] == "manual"
    assert "date" in topo
    campos_esperados = {"date", "type", "t", "qty", "price", "pnl", "status", "motivo", "origem"}
    assert set(topo.keys()) == campos_esperados


def test_registrar_rejeicao_tipo_invalido_levanta_valueerror():
    conn, _ = _fresh_db()
    with pytest.raises(ValueError):
        store.registrar_rejeicao(conn, "TROCA", "PETR4", 100, 30.0, "motivo qualquer")


def test_registrar_rejeicao_nao_move_dinheiro():
    conn, _ = _fresh_db()
    cash_antes = store.get(conn, "cash")
    positions_antes = store.get(conn, "positions")
    store.registrar_rejeicao(conn, "COMPRA", "PETR4", 200, 33.5, "Caixa insuficiente")
    assert store.get(conn, "cash") == cash_antes
    assert store.get(conn, "positions") == positions_antes


def test_registrar_rejeicao_price_none_sobrevive():
    conn, _ = _fresh_db()
    entry = store.registrar_rejeicao(conn, "COMPRA", "PETR4", 100, None, "Cotacao indisponivel")
    assert entry["price"] is None
    assert store.get(conn, "history")[0]["price"] is None


def test_registrar_rejeicao_trunca_motivo_em_200_chars():
    conn, _ = _fresh_db()
    motivo_longo = "x" * 500
    entry = store.registrar_rejeicao(conn, "VENDA", "VALE3", 100, 60.0, motivo_longo)
    assert len(entry["motivo"]) == 200


# --------------------------------------------------------------------------
# Poda (T-04-02) — CAP_REJEICOES = 100
# --------------------------------------------------------------------------

def test_poda_mantem_cap_rejeicoes_e_preserva_execucoes():
    conn, _ = _fresh_db()
    # 3 execucoes intercaladas com 105 rejeicoes
    store.buy(conn, "PETR4", 100, 30.0)
    for _ in range(50):
        store.registrar_rejeicao(conn, "COMPRA", "PETR4", 100, 30.0, "Caixa insuficiente")
    store.buy(conn, "VALE3", 100, 60.0)
    for _ in range(55):
        store.registrar_rejeicao(conn, "COMPRA", "PETR4", 100, 30.0, "Caixa insuficiente")
    store.buy(conn, "ITUB4", 100, 25.0)

    history = store.get(conn, "history")
    rejeitadas = [h for h in history if h.get("status") == "rejeitada"]
    executadas = [h for h in history if h.get("status") == "executada"]
    assert len(rejeitadas) == 100
    assert len(executadas) == 3


def test_poda_descarta_a_mais_antiga_primeiro():
    conn, _ = _fresh_db()
    for i in range(store.CAP_REJEICOES + 1):
        store.registrar_rejeicao(conn, "COMPRA", "PETR4", 100, 30.0, f"motivo {i}")
    history = store.get(conn, "history")
    rejeitadas = [h for h in history if h.get("status") == "rejeitada"]
    assert len(rejeitadas) == store.CAP_REJEICOES
    # a 101a chamada (motivo "motivo 0", a mais antiga) foi descartada
    motivos = {h["motivo"] for h in rejeitadas}
    assert "motivo 0" not in motivos
    assert f"motivo {store.CAP_REJEICOES}" in motivos


# --------------------------------------------------------------------------
# buy/sell carimbam status="executada"
# --------------------------------------------------------------------------

def test_buy_grava_status_executada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 100, 30.0)
    assert store.get(conn, "history")[0]["status"] == "executada"


def test_sell_grava_status_executada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 100, 30.0)
    store.sell(conn, "PETR4", 35.0)
    assert store.get(conn, "history")[0]["status"] == "executada"
    assert store.get(conn, "history")[0]["type"] == "VENDA"


# --------------------------------------------------------------------------
# Histórico legado (sem a chave `status`) não é reescrito
# --------------------------------------------------------------------------

def test_historico_legado_continua_legivel_e_nao_e_reescrito():
    conn, _ = _fresh_db()
    legado = {"date": "01/01/2026 10:00", "type": "COMPRA", "t": "VALE3", "qty": 100, "price": 60, "pnl": None}
    history = store.get(conn, "history")
    history.append(legado)
    db.kv_set(conn, "history", history)

    store.buy(conn, "PETR4", 100, 30.0)

    history_depois = store.get(conn, "history")
    entrada_legada = next(h for h in history_depois if h.get("t") == "VALE3" and h.get("date") == "01/01/2026 10:00")
    assert entrada_legada == legado
    assert "status" not in entrada_legada
    assert entrada_legada.get("status") is None
