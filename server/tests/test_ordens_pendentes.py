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


# --------------------------------------------------------------------------
# cancelar — devolução IMEDIATA (D-03), sem esperar o scheduler
# --------------------------------------------------------------------------

def test_cancelar_compra_devolve_caixa_sem_gravar_history():
    conn, _ = _fresh_db()
    cash_antes = store.get(conn, "cash")
    registro = pending_orders.criar_compra(conn, None, "PETR4", 100, 30.0)
    cancelado = pending_orders.cancelar(conn, None, registro["id"])
    assert cancelado["id"] == registro["id"]
    assert store.get(conn, "cash") == cash_antes
    assert pending_orders.listar(conn, None) == []
    assert store.get(conn, "history") == []


def test_cancelar_venda_parcial_restaura_qty_e_avg():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 300, 30.0, user_id=None)
    registro = pending_orders.criar_venda(conn, None, "PETR4", 100)
    pending_orders.cancelar(conn, None, registro["id"])
    positions = store.get(conn, "positions")
    pos = next(p for p in positions if p["t"] == "PETR4")
    assert pos["qty"] == 300
    assert pos["avg"] == 30.0  # nenhuma reponderação espúria


def test_cancelar_venda_total_faz_posicao_reaparecer():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 100, 30.0, user_id=None)
    registro = pending_orders.criar_venda(conn, None, "PETR4", 100)
    assert store.get(conn, "positions") == []
    pending_orders.cancelar(conn, None, registro["id"])
    positions = store.get(conn, "positions")
    pos = next(p for p in positions if p["t"] == "PETR4")
    assert pos["qty"] == 100
    assert pos["avg"] == 30.0


def test_cancelar_venda_com_recompra_no_meio_repondera_avg():
    """100@10 (venda pendente) + usuário recompra 100@20 => cancelar devolve
    100@10, resultado deve ser 200@15,00 (mesma fórmula de store.buy)."""
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 100, 10.0, user_id=None)
    registro = pending_orders.criar_venda(conn, None, "PETR4", 100)
    assert store.get(conn, "positions") == []
    store.buy(conn, "PETR4", 100, 20.0, user_id=None)  # recompra enquanto a venda está pendente
    pending_orders.cancelar(conn, None, registro["id"])
    positions = store.get(conn, "positions")
    pos = next(p for p in positions if p["t"] == "PETR4")
    assert pos["qty"] == 200
    assert pos["avg"] == 15.0


def test_cancelar_id_inexistente_levanta_erro_e_nao_muda_nada():
    conn, _ = _fresh_db()
    cash_antes = store.get(conn, "cash")
    with pytest.raises(pending_orders.OrdemNaoPendente):
        pending_orders.cancelar(conn, None, "po_inexistente")
    assert store.get(conn, "cash") == cash_antes


def test_cancelar_ordem_ja_cancelada_levanta_erro():
    conn, _ = _fresh_db()
    registro = pending_orders.criar_compra(conn, None, "PETR4", 100, 30.0)
    pending_orders.cancelar(conn, None, registro["id"])
    with pytest.raises(pending_orders.OrdemNaoPendente):
        pending_orders.cancelar(conn, None, registro["id"])


# --------------------------------------------------------------------------
# executar_pendentes — preço do MOTOR (D-01), nunca inventado
# --------------------------------------------------------------------------

def _price_getter_fixo(preco, source="yahoo"):
    chamadas = {"n": 0}

    async def fake(ticker):
        chamadas["n"] += 1
        return {"price": preco, "source": source}
    fake.chamadas = chamadas
    return fake


def test_executar_compra_usa_preco_do_motor_nao_a_referencia():
    conn, _ = _fresh_db()
    cash_antes = store.get(conn, "cash")
    pending_orders.criar_compra(conn, None, "PETR4", 100, 30.0)
    eventos = asyncio.run(pending_orders.executar_pendentes(conn, None, _price_getter_fixo(32.0)))
    history = store.get(conn, "history")
    assert history[0]["type"] == "COMPRA"
    assert history[0]["origem"] == "pendente"
    assert history[0]["price"] == 32.0
    assert pending_orders.listar(conn, None) == []
    assert pending_orders.caixa_reservado(conn, None) == 0
    # preço de execução MAIOR que a referência: a diferença é acertada, não ignorada.
    assert store.get(conn, "cash") == round(cash_antes - 100 * 32.0, 2)
    assert any(e.get("tag") == "pendente-executada" and e.get("kind") == "buy" for e in eventos)


def test_executar_compra_custo_real_excede_caixa_livre_auto_cancela():
    """Preço de abertura sobe o suficiente para o caixa reservado + livre não
    cobrir mais o custo: a ordem é CANCELADA automaticamente, o caixa volta
    integralmente e o evento leva a tag pendente-cancelada (T-02-36)."""
    conn, _ = _fresh_db()
    registro = pending_orders.criar_compra(conn, None, "PETR4", 100, 30.0)  # reserva 3000
    # simula o resto do caixa livre já ter sido gasto noutra operação,
    # sobrando só R$ 1,00 livre — não cobre 100 ações a R$ 1000,00.
    db.kv_set(conn, "cash", 1.0, user_id=None)
    eventos = asyncio.run(pending_orders.executar_pendentes(conn, None, _price_getter_fixo(1000.0)))
    assert pending_orders.listar(conn, None) == []
    assert any(e.get("tag") == "pendente-cancelada" and e.get("kind") == "warn" for e in eventos)
    # caixa reservado da COMPRA cancelada voltou integralmente (mais o resto usado na VALE3)
    assert round(store.get(conn, "cash"), 2) == round(1.0 + registro["caixaReservado"], 2)
    assert store.get(conn, "positions") == [] or all(p["t"] != "PETR4" for p in store.get(conn, "positions"))
    history = store.get(conn, "history")
    assert not any(h["t"] == "PETR4" for h in history)


def test_executar_venda_usa_preco_do_motor_e_calcula_pnl_contra_avg_reservado():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 100, 10.0, user_id=None)
    pending_orders.criar_venda(conn, None, "PETR4", 100)
    eventos = asyncio.run(pending_orders.executar_pendentes(conn, None, _price_getter_fixo(15.0)))
    history = store.get(conn, "history")
    assert history[0]["type"] == "VENDA"
    assert history[0]["origem"] == "pendente"
    assert history[0]["pnl"] == 500.0  # (15-10)*100
    assert store.get(conn, "positions") == []
    assert any(e.get("tag") == "pendente-executada" for e in eventos)


def test_executar_sem_preco_mantem_ordem_pendente_e_registra_erro():
    conn, _ = _fresh_db()
    cash_antes = store.get(conn, "cash")
    positions_antes = store.get(conn, "positions")
    pending_orders.criar_compra(conn, None, "PETR4", 100, 30.0)

    async def sem_preco(ticker):
        return {"price": None, "source": "yahoo"}

    eventos = asyncio.run(pending_orders.executar_pendentes(conn, None, sem_preco))
    assert eventos == []
    lista = pending_orders.listar(conn, None)
    assert len(lista) == 1
    assert lista[0]["ultimoErro"] is not None
    assert lista[0]["ultimaTentativaEm"] is not None
    # cash idêntico ao caixa JÁ reservado na criação — não muda de novo aqui.
    assert store.get(conn, "cash") == cash_antes - 3000.0
    assert store.get(conn, "positions") == positions_antes


def test_executar_price_getter_levanta_excecao_mantem_ordem_pendente():
    """price_getter que levanta (ex.: candle_provider.QuoteUnavailable) cai no
    mesmo caminho de erro do payload sem preço — nenhuma exceção de uma ordem
    derruba as demais nem fabrica preço."""
    conn, _ = _fresh_db()
    cash_antes = store.get(conn, "cash")
    pending_orders.criar_compra(conn, None, "PETR4", 100, 30.0)

    async def explode(ticker):
        raise RuntimeError("provedor fora do ar")

    eventos = asyncio.run(pending_orders.executar_pendentes(conn, None, explode))
    assert eventos == []
    lista = pending_orders.listar(conn, None)
    assert len(lista) == 1
    assert "provedor fora do ar" in lista[0]["ultimoErro"]
    assert store.get(conn, "cash") == cash_antes - 3000.0


def test_executar_ordem_cancelada_durante_await_nao_ressuscita():
    """T-02-04: se a ordem for cancelada ENQUANTO a cotação está sendo obtida,
    executar_pendentes não deve ressuscitá-la nem aplicá-la — a re-checagem
    do id dentro do lock deve pular a ordem silenciosamente."""
    conn, _ = _fresh_db()
    registro = pending_orders.criar_compra(conn, None, "PETR4", 100, 30.0)

    async def cancela_no_meio_do_caminho(ticker):
        pending_orders.cancelar(conn, None, registro["id"])
        return {"price": 32.0, "source": "yahoo"}

    eventos = asyncio.run(pending_orders.executar_pendentes(conn, None, cancela_no_meio_do_caminho))
    assert eventos == []
    assert pending_orders.listar(conn, None) == []
    history = store.get(conn, "history")
    assert not any(h.get("t") == "PETR4" for h in history)


def test_executar_ordem_sincrona_tambem_funciona():
    """price_getter pode ser SYNC (não só async) — inspect.isawaitable resolve."""
    conn, _ = _fresh_db()
    pending_orders.criar_compra(conn, None, "PETR4", 100, 30.0)

    def sincrono(ticker):
        return {"price": 30.0, "source": "yahoo"}

    eventos = asyncio.run(pending_orders.executar_pendentes(conn, None, sincrono))
    assert any(e.get("tag") == "pendente-executada" for e in eventos)
    assert pending_orders.listar(conn, None) == []
