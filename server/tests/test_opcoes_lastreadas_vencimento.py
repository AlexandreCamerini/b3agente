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
import asyncio
import os
import tempfile

import pytest

from app import agent, db, store


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


# ---------------------------------------------------------------------------
# Parte 2 — ramo lastreado em agent._avaliar_opcoes
# ---------------------------------------------------------------------------
def _conn():
    d = tempfile.mkdtemp(prefix="b3_test_agent_lastreada_")
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    store.set_config(c, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"}, "appMode": "operador"},
                      user_id="u1")
    return c


def _seed_agent(c, ag=None):
    db.kv_set(c, "agent", {"autonomous": True, "serverEnabled": True, "mode": "executar",
                            "maxOpsDia": 5, **(ag or {})}, user_id="u1")


def _empty_quotes():
    async def getter(tickers):
        return {}
    return getter


def _option_payload(underlying, expiration, contract_symbol, spot, option_type="call",
                     strike=38.0, last_price=1.0, provider_status="ok"):
    contrato = {"contractSymbol": contract_symbol, "optionType": option_type,
                "strike": strike, "lastPrice": last_price}
    calls = [contrato] if option_type == "call" else []
    puts = [contrato] if option_type == "put" else []
    return {"providerStatus": provider_status, "underlyingPrice": spot,
            "calls": calls, "puts": puts, "expiration": expiration}


def _option_getter(payloads: dict):
    async def getter(underlying, expiration):
        return payloads.get((underlying, expiration))
    return getter


def _run(c, option_getter):
    return asyncio.run(agent.run_cycle_for(c, "u1", _empty_quotes(), option_quotes_getter=option_getter))


def test_ciclo_liquida_call_coberta_vencida_itm_gera_evento_com_pnl():
    c = _conn()
    store.buy(c, "PETR4", 200, 35.0, user_id="u1")
    store.abrir_call_coberta(c, _contract_call(strike=38.0), 2, 1.50, user_id="u1")
    _seed_agent(c)
    payload = _option_payload("PETR4", "2020-01-01", "PETR4O123", spot=41.0, strike=38.0)

    r = _run(c, _option_getter({("PETR4", "2020-01-01"): payload}))

    assert r["executed"] == 1
    assert store.get(c, "optionPositions", user_id="u1") == []
    pos_acao = next(p for p in store.get(c, "positions", user_id="u1") if p["t"] == "PETR4")
    assert pos_acao["qty"] == 200  # nenhuma ação vendida por exercício
    assert pos_acao["qtyTravada"] == 0
    ev = next(e for e in r["events"] if e.get("t") == "PETR4")
    assert ev["kind"] == "warn"
    assert ev.get("tag") == "protecao-opcao"
    assert isinstance(ev.get("pnl"), (int, float))


def test_ciclo_lastreada_nao_vencida_ignora_stop_forcado():
    """Prova que o ramo lastreado sai ANTES de qualquer avaliação de
    stop/alvo/trailing — mesmo com `stop` gravado à força na posição, o
    ciclo não vende nada (D-1: o ciclo dela é só abrir/fechar/vencer)."""
    c = _conn()
    store.buy(c, "PETR4", 200, 35.0, user_id="u1")
    store.abrir_call_coberta(c, _contract_call(strike=38.0, expiration="2099-01-01"), 2, 1.50, user_id="u1")
    opts = store.get(c, "optionPositions", user_id="u1")
    opts[0]["stop"] = 0.10  # forçado: nunca gravado por caminho lastreado de verdade
    db.kv_set(c, "optionPositions", opts, user_id="u1")
    _seed_agent(c)
    # preço de prêmio abaixo do "stop" forçado — se o ramo legado rodasse, venderia
    payload = _option_payload("PETR4", "2099-01-01", "PETR4O123", spot=36.0, strike=38.0, last_price=0.05)

    r = _run(c, _option_getter({("PETR4", "2099-01-01"): payload}))

    assert r["executed"] == 0
    assert len(store.get(c, "optionPositions", user_id="u1")) == 1


def test_ciclo_lastreada_com_payload_degradado_nao_liquida():
    c = _conn()
    store.buy(c, "PETR4", 200, 35.0, user_id="u1")
    store.abrir_call_coberta(c, _contract_call(strike=38.0), 2, 1.50, user_id="u1")
    _seed_agent(c)
    payload = _option_payload("PETR4", "2020-01-01", "PETR4O123", spot=41.0, strike=38.0,
                               provider_status="degraded")

    r = _run(c, _option_getter({("PETR4", "2020-01-01"): payload}))

    assert r["executed"] == 0
    assert len(store.get(c, "optionPositions", user_id="u1")) == 1


def test_ciclo_liquida_lastreada_e_legada_no_mesmo_ciclo():
    """Os dois modelos coexistem: uma posição legada (sem `lastro`) vencida
    continua sendo liquidada pelo caminho antigo (`close_option_vencida`) no
    MESMO ciclo em que uma lastreada é liquidada pela regra nova."""
    c = _conn()
    store.buy(c, "PETR4", 200, 35.0, user_id="u1")
    store.abrir_call_coberta(c, _contract_call(id_="PETR4O123", strike=38.0), 2, 1.50, user_id="u1")
    store.buy_option(c, {"id": "PETRH340", "underlying": "PETR4", "optionType": "call",
                          "strike": 34.0, "expiration": "2020-01-01"}, 100, 1.0, user_id="u1")
    _seed_agent(c)
    payload = _option_payload("PETR4", "2020-01-01", "PETR4O123", spot=41.0, strike=38.0)
    payload["calls"].append({"contractSymbol": "PETRH340", "optionType": "call", "strike": 34.0,
                              "lastPrice": 7.0})

    r = _run(c, _option_getter({("PETR4", "2020-01-01"): payload}))

    assert r["executed"] == 2
    assert store.get(c, "optionPositions", user_id="u1") == []
    motivos = {h.get("t"): h.get("motivo") for h in store.get(c, "history", user_id="u1")[:2]}
    assert motivos.get("PETR4O123") == "vencimento"
    assert motivos.get("PETRH340") == "vencimento"
