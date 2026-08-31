"""Guardião do fim de vida da operação lastreada (Fase 14, Plano 04):

  Parte 1 — `store.liquidar_lastreada_vencida`: a regra determinística única
  para o que acontece quando a CALL coberta vence sem ter sido fechada à
  mão (D-2 de `.planning/notes/opcoes-mecanica-lastreada-decisoes.md`).
  Prova, nos dois desfechos (ITM/OTM), que a posição de AÇÕES nunca é
  tocada — nenhuma simulação de exercício/atribuição em lugar nenhum do
  sistema.

  Parte 2 (Task 2) — ramo lastreado em `agent._avaliar_opcoes`: o ciclo do
  agente dispara a liquidação forçada e NUNCA aplica stop/alvo/trailing a
  uma posição lastreada (o ciclo dela é só abrir/fechar/vencer).

Padrão da casa: `_fresh_db()`/SQLite temp por teste, sem conftest (mesmo
padrão de `test_lastro_trava.py`/`test_opcoes_lastreadas_store.py`).
"""
import os
import tempfile

import pytest

from app import db, store


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_test_opcoes_lastreadas_vencimento_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)
    return conn, path


def _contract_call(id_="PETR4O123", underlying="PETR4", strike=38.0, expiration="2020-01-01"):
    return {"id": id_, "underlying": underlying, "optionType": "call", "strike": strike,
            "expiration": expiration, "ivEntrada": 0.35, "deltaEntrada": 0.5, "hv21Entrada": 0.3}


def _contract_put(id_="PETR4P456", underlying="PETR4", strike=40.0, expiration="2020-01-01"):
    return {"id": id_, "underlying": underlying, "optionType": "put", "strike": strike,
            "expiration": expiration, "ivEntrada": 0.30, "deltaEntrada": -0.4, "hv21Entrada": 0.28}


# ---------------------------------------------------------------------------
# Parte 1 — store.liquidar_lastreada_vencida (motor puro)
# ---------------------------------------------------------------------------
def test_liquidar_call_coberta_itm_debita_intrinseco_e_nao_toca_acoes():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 35.0)
    positions_antes = store.get(conn, "positions")
    qty_acao_antes = next(p for p in positions_antes if p["t"] == "PETR4")["qty"]
    store.abrir_call_coberta(conn, _contract_call(strike=38.0), 2, 1.50)
    cash_antes = store.get(conn, "cash")

    pnl = store.liquidar_lastreada_vencida(conn, "PETR4O123", 41.0)

    assert pnl == round((1.50 - 3.00) * 200, 2)
    cash_depois = store.get(conn, "cash")
    assert cash_depois == round(cash_antes - 200 * 3.00, 2)
    # nenhuma ação foi vendida/entregue por exercício — mesma quantidade de antes
    pos_acao = next(p for p in store.get(conn, "positions") if p["t"] == "PETR4")
    assert pos_acao["qty"] == qty_acao_antes
    assert pos_acao["qtyTravada"] == 0
    assert store.get(conn, "optionPositions") == []
    h = store.get(conn, "history")[0]
    assert h["motivo"] == "vencimento" and h["origem"] == "sistema"
    assert h["price"] == 3.00 and h["pnl"] == pnl


def test_liquidar_call_coberta_otm_debita_zero_premio_fica_com_vendedor():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 35.0)
    positions_antes = store.get(conn, "positions")
    qty_acao_antes = next(p for p in positions_antes if p["t"] == "PETR4")["qty"]
    store.abrir_call_coberta(conn, _contract_call(strike=38.0), 2, 1.50)
    cash_antes = store.get(conn, "cash")

    pnl = store.liquidar_lastreada_vencida(conn, "PETR4O123", 35.0)  # OTM

    assert pnl == round(1.50 * 200, 2)  # prêmio integral fica com quem vendeu
    assert store.get(conn, "cash") == cash_antes  # débito zero
    pos_acao = next(p for p in store.get(conn, "positions") if p["t"] == "PETR4")
    assert pos_acao["qty"] == qty_acao_antes  # nenhuma ação tocada
    assert pos_acao["qtyTravada"] == 0  # lastro destravado igual ao caso ITM
    assert store.get(conn, "optionPositions") == []
    h = store.get(conn, "history")[0]
    assert h["motivo"] == "vencimento" and h["origem"] == "sistema"
    assert h["price"] == 0.0


def test_liquidar_put_protecao_vencida_itm_credita_intrinseco_sem_mexer_trava():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 100, 38.0)
    store.comprar_put_protecao(conn, _contract_put(strike=40.0), 1, 0.80)
    cash_antes = store.get(conn, "cash")
    pos_acao_antes = next(p for p in store.get(conn, "positions") if p["t"] == "PETR4")
    assert pos_acao_antes.get("qtyTravada", 0) == 0  # put nunca trava

    pnl = store.liquidar_lastreada_vencida(conn, "PETR4P456", 36.0)  # ITM: strike 40 > spot 36

    assert pnl == round((4.0 - 0.80) * 100, 2)  # sell_option: (price - avg) * qty
    assert store.get(conn, "cash") == round(cash_antes + 100 * 4.0, 2)
    pos_acao = next(p for p in store.get(conn, "positions") if p["t"] == "PETR4")
    assert pos_acao.get("qtyTravada", 0) == 0  # nada a destravar
    assert store.get(conn, "optionPositions") == []


def test_liquidar_posicao_sem_lastro_e_recusada_caminho_legado_intacto():
    conn, _ = _fresh_db()
    store.buy_option(conn, {"id": "PETRH340", "underlying": "PETR4", "optionType": "call",
                             "strike": 34.0, "expiration": "2020-01-01"}, 100, 1.0)
    with pytest.raises(ValueError):
        store.liquidar_lastreada_vencida(conn, "PETRH340", 40.0)
    # caminho legado continua funcionando para essa mesma posição
    pnl = store.close_option_vencida(conn, "PETRH340", 6.0)
    assert pnl == round((6.0 - 1.0) * 100, 2)
