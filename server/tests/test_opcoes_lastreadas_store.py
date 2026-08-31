"""Guardião das três operações lastreadas no motor (Fase 14, Plano 02):
vender para abrir uma CALL coberta, recomprar para fechar essa mesma call, e
comprar uma PUT de proteção vinculada a uma posição real.

O que estes testes protegem:
  • `abrir_call_coberta` credita o prêmio, cria a posição vendida com
    `lastro` e trava exatamente `contratos * 100` ações — sem lastro livre
    suficiente é recusado, com rejeição registrada e caixa intacto;
  • `fechar_call_coberta` debita a recompra, realiza o pnl da perna
    (`avg - price`) e destrava exatamente o que fecha (parcial destrava só a
    parte fechada);
  • `comprar_put_protecao` exige posição real do lastro, debita o caixa e
    NUNCA trava ações;
  • posições de opção pré-existentes (sem `lastro`) seguem intocadas por
    este novo caminho.

Padrão da casa: `_fresh_db()` com SQLite temp por teste, sem conftest (mesmo
padrão de `test_lastro_trava.py`).
"""
import os
import tempfile

import pytest

from app import db, store


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_test_opcoes_lastreadas_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)
    return conn, path


def _contract_call(id_="PETR4O123", underlying="PETR4", strike=40.0, expiration="2026-09-18"):
    return {"id": id_, "underlying": underlying, "optionType": "call", "strike": strike,
            "expiration": expiration, "ivEntrada": 0.35, "deltaEntrada": 0.5, "hv21Entrada": 0.3}


def _contract_put(id_="PETR4P456", underlying="PETR4", strike=35.0, expiration="2026-09-18"):
    return {"id": id_, "underlying": underlying, "optionType": "put", "strike": strike,
            "expiration": expiration, "ivEntrada": 0.30, "deltaEntrada": -0.4, "hv21Entrada": 0.28}


# --------------------------------------------------------------------------
# abrir_call_coberta (T-14-05, T-14-06, T-14-07)
# --------------------------------------------------------------------------

def test_abrir_call_coberta_credita_premio_cria_lastro_trava_acoes():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 300, 38.0)
    cash_antes = store.get(conn, "cash")
    store.abrir_call_coberta(conn, _contract_call(), 2, 1.50)
    cash_depois = store.get(conn, "cash")
    assert cash_depois == round(cash_antes + 2 * 100 * 1.50, 2)
    opts = store.get(conn, "optionPositions")
    pos_opcao = next(p for p in opts if p["id"] == "PETR4O123")
    assert pos_opcao["side"] == "vendida"
    assert pos_opcao["qty"] == 200
    assert pos_opcao["avg"] == 1.50
    assert pos_opcao["lastro"] == {"t": "PETR4", "qty": 200}
    pos_acao = next(p for p in store.get(conn, "positions") if p["t"] == "PETR4")
    assert pos_acao["qtyTravada"] == 200


def test_abrir_call_coberta_sem_lastro_livre_e_recusada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 100, 38.0)
    cash_antes = store.get(conn, "cash")
    with pytest.raises(ValueError):
        store.abrir_call_coberta(conn, _contract_call(), 2, 1.50)
    assert store.get(conn, "cash") == cash_antes
    pos_acao = next(p for p in store.get(conn, "positions") if p["t"] == "PETR4")
    assert pos_acao.get("qtyTravada", 0) == 0
    history = store.get(conn, "history")
    rejeitadas = [h for h in history if h.get("status") == "rejeitada"]
    assert len(rejeitadas) == 1
    assert rejeitadas[0]["type"] == "VENDA"


def test_abrir_call_coberta_sem_posicao_no_ativo_e_recusada():
    conn, _ = _fresh_db()
    with pytest.raises(ValueError):
        store.abrir_call_coberta(conn, _contract_call(), 1, 1.50)


def test_abrir_call_coberta_com_put_e_recusada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 100, 38.0)
    contrato = _contract_call()
    contrato["optionType"] = "put"
    with pytest.raises(ValueError):
        store.abrir_call_coberta(conn, contrato, 1, 1.50)


def test_abrir_call_coberta_reabertura_soma_qty_pondera_avg():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 400, 38.0)
    store.abrir_call_coberta(conn, _contract_call(), 2, 1.00)
    store.abrir_call_coberta(conn, _contract_call(), 2, 2.00)
    opts = store.get(conn, "optionPositions")
    pos_opcao = next(p for p in opts if p["id"] == "PETR4O123")
    assert pos_opcao["qty"] == 400
    assert pos_opcao["avg"] == round((200 * 1.00 + 200 * 2.00) / 400, 2)
    assert pos_opcao["lastro"]["qty"] == 400
    pos_acao = next(p for p in store.get(conn, "positions") if p["t"] == "PETR4")
    assert pos_acao["qtyTravada"] == 400
