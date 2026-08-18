"""Guardiões do motor de ordens pendentes (Fase 2, MERC-02..04).

Cobre o ciclo de vida completo: criar (reserva de caixa/posição no PEDIDO,
D-02/D-05/D-06), cancelar (devolução IMEDIATA, D-03), executar (preço do
motor via price_getter injetável, D-01/D-04), múltiplas ordens no mesmo
ticker (D-07) e a trava única de processo (T-02-02).

Padrão da casa: `_fresh_db()` com SQLite temp por teste, sem conftest, sem
mock de SQLite (ver .planning/codebase/TESTING.md).
"""
import asyncio
import os
import tempfile

import pytest

from app import db, pending_orders, store


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_test_pendentes_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)
    return conn, path


# --------------------------------------------------------------------------
# Trava única (T-02-02) — pending_orders.ORDER_LOCK é o MESMO objeto do store
# --------------------------------------------------------------------------

def test_order_lock_e_alias_do_store():
    """A trava de pending_orders é IDENTIDADE do objeto de store.py — não uma
    trava distinta (é isto que o plano 02-02 vai reusar no caminho de ordem
    imediata /api/buy e /api/sell)."""
    assert pending_orders.ORDER_LOCK is store.ORDER_LOCK


# --------------------------------------------------------------------------
# criar_compra — reserva de caixa no PEDIDO (D-02/D-05)
# --------------------------------------------------------------------------

def test_criar_compra_reserva_caixa_e_preserva_patrimonio():
    conn, _ = _fresh_db()
    cash_antes = store.get(conn, "cash")
    registro = pending_orders.criar_compra(conn, None, "PETR4", 100, 30.0)
    cash_depois = store.get(conn, "cash")
    assert registro["caixaReservado"] == 3000.0
    # Guardião: patrimônio não muda ao criar pendente — o que saiu de cash
    # aparece em caixaReservado (must_have da fase).
    assert round(cash_depois + registro["caixaReservado"], 2) == round(cash_antes, 2)
    lista = pending_orders.listar(conn, None)
    assert len(lista) == 1
    assert lista[0]["tipo"] == "COMPRA"
    assert lista[0]["t"] == "PETR4"
    assert lista[0]["id"].startswith("po_")
    assert lista[0]["avgReservado"] is None
    assert lista[0]["ultimaTentativaEm"] is None
    assert lista[0]["ultimoErro"] is None


def test_criar_compra_normaliza_qty_em_lote_de_100():
    conn, _ = _fresh_db()
    registro = pending_orders.criar_compra(conn, None, "PETR4", 150, 30.0)
    assert registro["qty"] == 200  # round(150/100)*100 == 200, mesma regra de store.buy


def test_criar_compra_caixa_insuficiente_nao_grava_nada():
    conn, _ = _fresh_db()
    cash_antes = store.get(conn, "cash")
    with pytest.raises(pending_orders.CaixaInsuficiente, match="Caixa insuficiente"):
        pending_orders.criar_compra(conn, None, "PETR4", 100, cash_antes)  # 100 * cash_antes > cash_antes
    # Guardião: recusa não deixa rastro — nem em pendingOrders, nem em cash.
    assert pending_orders.listar(conn, None) == []
    assert store.get(conn, "cash") == cash_antes


def test_criar_compra_meta_sanitizado():
    conn, _ = _fresh_db()
    registro = pending_orders.criar_compra(
        conn, None, "PETR4", 100, 30.0,
        meta={"setup": "rompimento", "gatilho": 31.5, "campoDesconhecido": "x"})
    assert registro["meta"]["setup"] == "rompimento"
    assert registro["meta"]["gatilho"] == 31.5
    assert "campoDesconhecido" not in registro["meta"]


# --------------------------------------------------------------------------
# criar_venda — reserva de posição no PEDIDO (D-02/D-06)
# --------------------------------------------------------------------------

def test_criar_venda_parcial_preserva_avg():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 300, 30.0, user_id=None)
    registro = pending_orders.criar_venda(conn, None, "PETR4", 100)
    positions = store.get(conn, "positions")
    pos = next(p for p in positions if p["t"] == "PETR4")
    assert pos["qty"] == 200
    assert pos["avg"] == 30.0  # avg INALTERADO na reserva parcial
    assert registro["avgReservado"] == 30.0
    assert registro["caixaReservado"] is None


def test_criar_venda_total_some_da_posicao_mas_preserva_avg_reservado():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 100, 30.0, user_id=None)
    registro = pending_orders.criar_venda(conn, None, "PETR4", 100)
    positions = store.get(conn, "positions")
    assert not any(p["t"] == "PETR4" for p in positions)
    assert registro["avgReservado"] == 30.0


def test_criar_venda_sem_posicao_levanta_erro():
    conn, _ = _fresh_db()
    with pytest.raises(pending_orders.PosicaoInsuficiente, match="Sem posicao em PETR4"):
        pending_orders.criar_venda(conn, None, "PETR4", 100)


def test_criar_venda_quantidade_maior_que_disponivel_apos_outra_pendente():
    """D-06: não dá para vender a mesma ação duas vezes em duas pendentes."""
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 30.0, user_id=None)
    pending_orders.criar_venda(conn, None, "PETR4", 100)  # reserva 100, sobra 100
    with pytest.raises(pending_orders.PosicaoInsuficiente):
        pending_orders.criar_venda(conn, None, "PETR4", 200)  # só sobrou 100
    # a posição não deve ter sido tocada pela tentativa recusada
    positions = store.get(conn, "positions")
    pos = next(p for p in positions if p["t"] == "PETR4")
    assert pos["qty"] == 100


def test_duas_ordens_pendentes_mesmo_ticker_coexistem():
    """D-07: sem bloqueio nem substituição, cada uma com seu id."""
    conn, _ = _fresh_db()
    r1 = pending_orders.criar_compra(conn, None, "PETR4", 100, 30.0)
    r2 = pending_orders.criar_compra(conn, None, "PETR4", 100, 31.0)
    assert r1["id"] != r2["id"]
    lista = pending_orders.listar(conn, None)
    assert len(lista) == 2
    assert [o["id"] for o in lista] == [r1["id"], r2["id"]]  # FIFO


# --------------------------------------------------------------------------
# listar / caixa_reservado / qty_reservada
# --------------------------------------------------------------------------

def test_listar_ordem_de_criacao():
    conn, _ = _fresh_db()
    r1 = pending_orders.criar_compra(conn, None, "PETR4", 100, 10.0)
    r2 = pending_orders.criar_compra(conn, None, "VALE3", 100, 20.0)
    r3 = pending_orders.criar_compra(conn, None, "ITUB4", 100, 15.0)
    lista = pending_orders.listar(conn, None)
    assert [o["id"] for o in lista] == [r1["id"], r2["id"], r3["id"]]


def test_caixa_reservado_soma_apenas_compras():
    conn, _ = _fresh_db()
    store.buy(conn, "VALE3", 100, 20.0, user_id=None)  # cash 10000 -> 8000
    pending_orders.criar_compra(conn, None, "PETR4", 100, 10.0)  # reserva 1000
    pending_orders.criar_compra(conn, None, "ITUB4", 200, 15.0)  # reserva 3000
    pending_orders.criar_venda(conn, None, "VALE3", 100)  # venda não soma em caixa_reservado
    assert pending_orders.caixa_reservado(conn, None) == 1000.0 + 3000.0


def test_qty_reservada_soma_vendas_do_ticker():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 300, 30.0, user_id=None)
    pending_orders.criar_venda(conn, None, "PETR4", 100)
    assert pending_orders.qty_reservada(conn, None, "PETR4") == 100
    assert pending_orders.qty_reservada(conn, None, "VALE3") == 0
