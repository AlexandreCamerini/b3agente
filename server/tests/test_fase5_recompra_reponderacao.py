"""Fase 5, Plano 01 — FIX-C26: guardião da reponderação de preço médio na
recompra após venda parcial (`store.buy`/`store.sell`, motor determinístico,
sem TestClient — a conta é do motor, não da rota HTTP).

Correção do exemplo do 05-CONTEXT.md: a sequência lá proposta
(`buy(100@30) → sell(qty=40) → buy(60@40)`) não roda no motor real porque
`buy`/`sell` normalizam toda quantidade para o lote de 100 mais próximo
(`max(100, round(qty/100)*100)`) — `qty=40` vira uma venda TOTAL de 100 (a
posição inteira de 100), e `qty=60` vira uma recompra de 100, não 60. A
sequência abaixo usa a MESMA aritmética, escalada ×10, para caber nos lotes
de 100 sem disparar a normalização de forma inesperada:

  1. `buy(qty=1000, price=30.0)`  → posição `qty=1000`, `avg=30.00`
  2. `sell(qty=400, price=X)`     → parcial: `qty=600`, `avg` INALTERADO (30.00)
  3. `buy(qty=600, price=40.0)`   → `qty=1200`, `avg=35.00`
     (30×600 + 40×600) / 1200 = 35.00 — reponderação usa as 600 REMANESCENTES,
     não as 1000 originais (33.75 seria o resultado errado se usasse 1000).
"""
import os
import tempfile

from app import db, store


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_f5_recompra_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)
    _zera(conn)  # seed demo traz posições — zera para o teste
    return conn


def _zera(conn, user_id=None):
    db.kv_set(conn, "positions", [], user_id=user_id)
    db.kv_set(conn, "history", [], user_id=user_id)
    # caixa alto o bastante para 1000 ações a 30 (30.000) + folga
    db.kv_set(conn, "cash", 100_000.0, user_id=user_id)


def test_recompra_apos_venda_parcial_repondera_com_qty_remanescente():
    conn = _fresh_db()
    store.buy(conn, "PETR4", 1000, 30.0)
    pos = store.get(conn, "positions")[0]
    assert pos["qty"] == 1000 and pos["avg"] == 30.0

    store.sell(conn, "PETR4", 32.0, qty=400)  # parcial: 600 remanescentes
    pos = store.get(conn, "positions")[0]
    assert pos["qty"] == 600
    assert pos["avg"] == 30.0, "venda parcial não pode mexer no preço médio"

    store.buy(conn, "PETR4", 600, 40.0)
    pos = store.get(conn, "positions")[0]
    assert pos["qty"] == 1200
    assert pos["avg"] == 35.0, "reponderação certa: (30×600 + 40×600) / 1200"
    assert pos["avg"] != 33.75, (
        "33.75 seria o resultado ERRADO se a reponderação usasse as 1000 "
        "cotas ORIGINAIS em vez das 600 remanescentes após a venda parcial "
        "— é essa a regressão que este teste existe para pegar"
    )
    conn.close()


def test_pnl_realizado_da_venda_parcial_e_proporcional_as_cotas_vendidas():
    conn = _fresh_db()
    cash0 = store.get(conn, "cash")
    store.buy(conn, "PETR4", 1000, 30.0)  # debita 30.000
    cash_pos_compra = store.get(conn, "cash")
    assert cash_pos_compra == round(cash0 - 1000 * 30.0, 2)

    pnl = store.sell(conn, "PETR4", 32.0, qty=400)
    assert pnl == round((32.0 - 30.0) * 400, 2)  # (preco_venda - avg) × qty vendida

    cash_pos_venda = store.get(conn, "cash")
    assert cash_pos_venda == round(cash_pos_compra + 400 * 32.0, 2)

    store.buy(conn, "PETR4", 600, 40.0)  # debita 600×40 = 24.000
    cash_final = store.get(conn, "cash")
    assert cash_final == round(cash_pos_venda - 600 * 40.0, 2)
    # soma das 3 operações bate com o caixa final calculado direto do zero
    esperado = round(cash0 - 1000 * 30.0 + 400 * 32.0 - 600 * 40.0, 2)
    assert cash_final == esperado
    conn.close()


def test_historico_da_sequencia_completa_tem_3_entradas_executadas():
    conn = _fresh_db()
    store.buy(conn, "PETR4", 1000, 30.0)
    store.sell(conn, "PETR4", 32.0, qty=400)
    store.buy(conn, "PETR4", 600, 40.0)

    history = store.get(conn, "history")
    assert len(history) == 3
    assert all(h["status"] == "executada" for h in history)
    tipos = [h["type"] for h in history]
    # history.insert(0, ...) — mais recente primeiro
    assert tipos == ["COMPRA", "VENDA", "COMPRA"]
    conn.close()


def test_normalizacao_de_lote_venda_de_40_sobre_100_vende_a_posicao_toda():
    """Documenta a regra que invalida o exemplo original do 05-CONTEXT.md:
    `sell(qty=40)` sobre uma posição de 100 NÃO vende 40 — normaliza pro
    lote de 100 mais próximo (`max(100, round(40/100)*100) == 100`), então
    vende a posição INTEIRA. Pedir 40 nunca resulta numa posição de 60
    remanescente; só pedindo qty>=50 (arredonda pra 100) é que o motor
    aceita normalizar para baixo até o lote — abaixo disso, sempre 100."""
    conn = _fresh_db()
    store.buy(conn, "VALE3", 100, 60.0)
    pos = store.get(conn, "positions")[0]
    assert pos["qty"] == 100

    pnl = store.sell(conn, "VALE3", 65.0, qty=40)
    assert store.get(conn, "positions") == [], "qty=40 sobre 100 normaliza para venda TOTAL"
    assert pnl == round((65.0 - 60.0) * 100, 2), "PnL calculado sobre as 100 cotas vendidas, não 40"
    conn.close()
