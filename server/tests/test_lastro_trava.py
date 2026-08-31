"""Guardião da trava de lastro no motor de carteira (Fase 14, Plano 01, D-3).

O que estes testes protegem:
  • `qty_livre(pos)` é a ÚNICA aritmética de quantidade vendável no backend
    (fonte única — mesma disciplina de `caixa_reservado`/`RR_MIN`);
  • `store.sell` nunca vende a parte travada, e livre==0 vira rejeição
    registrada, sem mover caixa nem tocar `positions` (T-14-01);
  • `pending_orders.criar_venda` nunca reserva o travado (T-14-02);
  • a parte livre da mesma posição continua vendável normalmente.

Padrão da casa: `_fresh_db()` com SQLite temp por teste, sem conftest.
"""
import os
import re
import tempfile
from pathlib import Path

import pytest

from app import db, pending_orders, store


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_test_lastro_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)
    return conn, path


def _travar(conn, t: str, qty_travada: int, user_id=None):
    positions = store.get(conn, "positions", user_id=user_id)
    pos = next(p for p in positions if p["t"] == t)
    pos["qtyTravada"] = qty_travada
    store.put(conn, "positions", positions, user_id=user_id)


# --------------------------------------------------------------------------
# qty_livre — fonte única da aritmética
# --------------------------------------------------------------------------

def test_qty_livre_sem_chave_devolve_qty():
    assert store.qty_livre({"qty": 300}) == 300


def test_qty_livre_com_travado_subtrai():
    assert store.qty_livre({"qty": 300, "qtyTravada": 200}) == 100


def test_qty_livre_nunca_negativo():
    assert store.qty_livre({"qty": 100, "qtyTravada": 100}) == 0
    assert store.qty_livre({"qty": 0, "qtyTravada": 0}) == 0


# --------------------------------------------------------------------------
# store.sell — guarda de trava (T-14-01)
# --------------------------------------------------------------------------

def test_sell_vende_so_a_parte_livre_com_trava_parcial():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 300, 38.0)
    _travar(conn, "PETR4", 200)
    pnl = store.sell(conn, "PETR4", 40.0, qty=300)  # pede tudo, só o livre executa
    assert pnl is not None
    pos = next(p for p in store.get(conn, "positions") if p["t"] == "PETR4")
    assert pos["qty"] == 200
    assert pos["qtyTravada"] == 200


def test_sell_com_100_por_cento_travado_e_recusada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    _travar(conn, "PETR4", 200)
    cash_antes = store.get(conn, "cash")
    resultado = store.sell(conn, "PETR4", 40.0)
    assert resultado is None
    assert store.get(conn, "cash") == cash_antes
    history = store.get(conn, "history")
    executadas = [h for h in history if h.get("status") == "executada"]
    rejeitadas = [h for h in history if h.get("status") == "rejeitada"]
    assert not any(h.get("type") == "VENDA" for h in executadas)
    assert len(rejeitadas) == 1
    assert "travadas" in rejeitadas[0]["motivo"]
    assert rejeitadas[0]["type"] == "VENDA"
    assert rejeitadas[0]["t"] == "PETR4"
    # posição intocada (nem qty nem qtyTravada mudam)
    pos = next(p for p in store.get(conn, "positions") if p["t"] == "PETR4")
    assert pos["qty"] == 200
    assert pos["qtyTravada"] == 200


def test_sell_posicao_sem_trava_continua_normal():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    pnl = store.sell(conn, "PETR4", 40.0)
    assert pnl == round((40.0 - 38.0) * 200, 2)
    assert not any(p["t"] == "PETR4" for p in store.get(conn, "positions"))


# --------------------------------------------------------------------------
# pending_orders.criar_venda — guarda de reserva (T-14-02)
# --------------------------------------------------------------------------

def test_criar_venda_recusa_quando_so_ha_travado():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    _travar(conn, "PETR4", 200)
    with pytest.raises(pending_orders.PosicaoInsuficiente):
        pending_orders.criar_venda(conn, None, "PETR4", 100)


def test_criar_venda_reserva_so_a_parte_livre_e_preserva_travado():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 300, 38.0)
    _travar(conn, "PETR4", 200)
    registro = pending_orders.criar_venda(conn, None, "PETR4", 100)
    assert registro["qty"] == 100
    pos = next(p for p in store.get(conn, "positions") if p["t"] == "PETR4")
    assert pos["qty"] == 200
    assert pos["qtyTravada"] == 200


def test_criar_venda_pedido_maior_que_livre_e_recusado():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 300, 38.0)
    _travar(conn, "PETR4", 200)
    with pytest.raises(pending_orders.PosicaoInsuficiente):
        pending_orders.criar_venda(conn, None, "PETR4", 200)  # só 100 livres


# --------------------------------------------------------------------------
# Fonte única — nenhum outro módulo recalcula `qty - qtyTravada`
# --------------------------------------------------------------------------

def test_fonte_unica_nenhum_outro_modulo_subtrai_qty_travada():
    app_dir = Path(store.__file__).parent
    padrao = re.compile(r"qty\b.{0,20}-.{0,20}qtyTravada|qtyTravada.{0,20}-.{0,20}qty\b")
    ofensores = []
    for py in app_dir.glob("*.py"):
        if py.name == "store.py":
            continue
        texto = py.read_text(encoding="utf-8")
        if padrao.search(texto):
            ofensores.append(py.name)
    assert ofensores == [], f"subtração qty-qtyTravada fora de store.py: {ofensores}"
