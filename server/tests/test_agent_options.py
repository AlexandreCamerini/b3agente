"""v2 — opções no ciclo do agente (ADR-003/004/005)."""
import asyncio
import os
import re
import tempfile

from app import agent, db, mydata_budget, options_provider_mydata, store


def _conn():
    d = tempfile.mkdtemp()
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    # Fase A (trava Modo Estudo): estes testes exercitam a EXECUÇÃO de opções
    # (mode="executar"), não a trava em si — precisam do Modo Operador para o
    # comportamento de antes desta entrega continuar valendo.
    store.set_config(c, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"}, "appMode": "operador"}, user_id="u1")
    return c


def _seed_opts(c, opts, ag=None):
    db.kv_set(c, "optionPositions", opts, user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    db.kv_set(c, "agent", {"autonomous": True, "serverEnabled": True, "mode": "executar",
                            "maxOpsDia": 5, **(ag or {})}, user_id="u1")


def _empty_quotes():
    async def getter(tickers):
        return {}
    return getter


def _option_payload(underlying, expiration, contract_symbol, last_price, spot,
                     option_type="call", strike=34.0, provider_status="ok"):
    contrato = {"contractSymbol": contract_symbol, "optionType": option_type,
                "strike": strike, "lastPrice": last_price}
    calls = [contrato] if option_type == "call" else []
    puts = [contrato] if option_type == "put" else []
    return {"providerStatus": provider_status, "underlyingPrice": spot,
            "calls": calls, "puts": puts, "expiration": expiration}


def _option_getter(payloads: dict):
    """payloads: {(underlying, expiration): payload}"""
    async def getter(underlying, expiration):
        return payloads.get((underlying, expiration))
    return getter


def _run(c, option_getter):
    return asyncio.run(agent.run_cycle_for(c, "u1", _empty_quotes(), option_quotes_getter=option_getter))


# ---------------------------------------------------------------------------
# intrinseco_opcao — pura
# ---------------------------------------------------------------------------
def test_intrinseco_call_otm_e_zero():
    pos = {"optionType": "call", "strike": 34.0}
    assert agent.intrinseco_opcao(pos, 30.0) == 0.0


def test_intrinseco_call_itm_e_a_diferenca():
    pos = {"optionType": "call", "strike": 34.0}
    assert agent.intrinseco_opcao(pos, 40.0) == 6.0


def test_intrinseco_put_itm_e_a_diferenca():
    pos = {"optionType": "put", "strike": 34.0}
    assert agent.intrinseco_opcao(pos, 30.0) == 4.0


# ---------------------------------------------------------------------------
# store.py — buy_option/sell_option/close_option_vencida
# ---------------------------------------------------------------------------
def test_buy_option_debita_caixa_e_cria_posicao():
    c = _conn()
    store.buy_option(c, {"id": "PETRH340", "underlying": "PETR4", "optionType": "call",
                          "strike": 34.0, "expiration": "2099-01-01"}, 100, 1.25, user_id="u1")
    opts = store.get(c, "optionPositions", user_id="u1")
    assert len(opts) == 1 and opts[0]["avg"] == 1.25 and opts[0]["qty"] == 100
    assert store.get(c, "cash", user_id="u1") == round(10000.0 - 125.0, 2)


def test_sell_option_total_fecha_posicao_e_registra_motivo():
    c = _conn()
    store.buy_option(c, {"id": "PETRH340", "underlying": "PETR4", "optionType": "call",
                          "strike": 34.0, "expiration": "2099-01-01"}, 100, 1.0, user_id="u1")
    pnl = store.sell_option(c, "PETRH340", 2.5, user_id="u1", motivo="alvo")
    assert pnl == 150.0
    assert store.get(c, "optionPositions", user_id="u1") == []
    h = store.get(c, "history", user_id="u1")[0]
    assert h["motivo"] == "alvo" and h["kind"] == "opcao"


def test_close_option_vencida_pode_liquidar_a_zero():
    c = _conn()
    store.buy_option(c, {"id": "PETRH340", "underlying": "PETR4", "optionType": "call",
                          "strike": 34.0, "expiration": "2020-01-01"}, 100, 1.0, user_id="u1")
    pnl = store.close_option_vencida(c, "PETRH340", 0.0, user_id="u1")
    assert pnl == -100.0
    h = store.get(c, "history", user_id="u1")[0]
    assert h["motivo"] == "vencimento" and h["price"] == 0.0


def test_reset_portfolio_zera_optionpositions():
    c = _conn()
    store.buy_option(c, {"id": "X", "underlying": "PETR4", "optionType": "call",
                          "strike": 34.0, "expiration": "2099-01-01"}, 100, 1.0, user_id="u1")
    out = store.reset_portfolio(c, user_id="u1")
    assert out["optionPositions"] == []


# ---------------------------------------------------------------------------
# agent.py — ciclo avalia optionPositions (ADR-005: vencimento tem prioridade)
# ---------------------------------------------------------------------------
def test_ciclo_liquida_por_vencimento_mesmo_sem_stop_alvo():
    c = _conn()
    _seed_opts(c, [{"id": "PETRH340", "underlying": "PETR4", "optionType": "call", "strike": 34.0,
                     "expiration": "2020-01-01", "qty": 100, "avg": 1.0, "stop": None, "alvo": None}])
    payload = _option_payload("PETR4", "2020-01-01", "PETRH340", last_price=0.05, spot=30.0)
    r = _run(c, _option_getter({("PETR4", "2020-01-01"): payload}))
    assert r["executed"] == 1
    assert store.get(c, "optionPositions", user_id="u1") == []
    h = store.get(c, "history", user_id="u1")[0]
    assert h["motivo"] == "vencimento" and h["price"] == 0.0  # call OTM


def test_ciclo_fecha_no_stop_de_premio():
    c = _conn()
    _seed_opts(c, [{"id": "PETRH340", "underlying": "PETR4", "optionType": "call", "strike": 34.0,
                     "expiration": "2099-01-01", "qty": 100, "avg": 1.0, "stop": 0.5, "alvo": None}])
    payload = _option_payload("PETR4", "2099-01-01", "PETRH340", last_price=0.4, spot=32.0)
    r = _run(c, _option_getter({("PETR4", "2099-01-01"): payload}))
    assert r["executed"] == 1
    h = store.get(c, "history", user_id="u1")[0]
    assert h["motivo"] == "stop"


def test_ciclo_fecha_no_alvo_de_premio():
    c = _conn()
    _seed_opts(c, [{"id": "PETRH340", "underlying": "PETR4", "optionType": "call", "strike": 34.0,
                     "expiration": "2099-01-01", "qty": 100, "avg": 1.0, "stop": None, "alvo": 2.0}])
    payload = _option_payload("PETR4", "2099-01-01", "PETRH340", last_price=2.2, spot=38.0)
    r = _run(c, _option_getter({("PETR4", "2099-01-01"): payload}))
    assert r["executed"] == 1
    h = store.get(c, "history", user_id="u1")[0]
    assert h["motivo"] == "alvo" and h["price"] == 2.2


def test_ciclo_nao_age_sobre_cotacao_degradada():
    """ADR-004: providerStatus != 'ok' — nem stop/alvo nem vencimento agem,
    a posição segue aberta para tentar de novo no próximo ciclo."""
    c = _conn()
    _seed_opts(c, [{"id": "PETRH340", "underlying": "PETR4", "optionType": "call", "strike": 34.0,
                     "expiration": "2020-01-01", "qty": 100, "avg": 1.0, "stop": 0.1, "alvo": None}])
    payload = _option_payload("PETR4", "2020-01-01", "PETRH340", last_price=0.05, spot=30.0,
                               provider_status="degraded")
    r = _run(c, _option_getter({("PETR4", "2020-01-01"): payload}))
    assert r["executed"] == 0
    assert len(store.get(c, "optionPositions", user_id="u1")) == 1


def test_ciclo_sem_option_quotes_getter_nao_quebra():
    c = _conn()
    _seed_opts(c, [{"id": "PETRH340", "underlying": "PETR4", "optionType": "call", "strike": 34.0,
                     "expiration": "2020-01-01", "qty": 100, "avg": 1.0, "stop": None, "alvo": None}])
    r = asyncio.run(agent.run_cycle_for(c, "u1", _empty_quotes()))  # sem option_quotes_getter
    assert r["executed"] == 0
    assert len(store.get(c, "optionPositions", user_id="u1")) == 1


def test_alvo_dinamico_nao_se_aplica_a_opcao():
    """F3 é exclusivo do ativo — mesmo com alvoDinamico ligado, opção fecha
    normalmente no alvo, sem tentativa de extensão (unidade quebrada: ATR do
    ativo-objeto não é prêmio)."""
    c = _conn()
    _seed_opts(c, [{"id": "PETRH340", "underlying": "PETR4", "optionType": "call", "strike": 34.0,
                     "expiration": "2099-01-01", "qty": 100, "avg": 1.0, "stop": None, "alvo": 2.0}],
               ag={"alvoDinamico": True})
    payload = _option_payload("PETR4", "2099-01-01", "PETRH340", last_price=2.5, spot=40.0)
    r = _run(c, _option_getter({("PETR4", "2099-01-01"): payload}))
    assert r["executed"] == 1
    assert store.get(c, "optionPositions", user_id="u1") == []  # fechou, não estendeu


def test_modo_sinalizar_nao_liquida_opcao():
    c = _conn()
    _seed_opts(c, [{"id": "PETRH340", "underlying": "PETR4", "optionType": "call", "strike": 34.0,
                     "expiration": "2099-01-01", "qty": 100, "avg": 1.0, "stop": 0.5, "alvo": None}],
               ag={"mode": "sinalizar"})
    payload = _option_payload("PETR4", "2099-01-01", "PETRH340", last_price=0.3, spot=30.0)
    r = _run(c, _option_getter({("PETR4", "2099-01-01"): payload}))
    assert r["executed"] == 0
    assert len(store.get(c, "optionPositions", user_id="u1")) == 1


def test_teto_diario_bloqueia_execucao_de_opcao():
    c = _conn()
    _seed_opts(c, [{"id": "PETRH340", "underlying": "PETR4", "optionType": "call", "strike": 34.0,
                     "expiration": "2099-01-01", "qty": 100, "avg": 1.0, "stop": 0.5, "alvo": None}],
               ag={"maxOpsDia": 1})
    db.kv_set(c, "agent", {**db.kv_get(c, "agent", {}, user_id="u1"),
                           "opsToday": 1, "opsDate": agent._today()}, user_id="u1")
    payload = _option_payload("PETR4", "2099-01-01", "PETRH340", last_price=0.3, spot=30.0)
    r = _run(c, _option_getter({("PETR4", "2099-01-01"): payload}))
    assert r["executed"] == 0
    assert len(store.get(c, "optionPositions", user_id="u1")) == 1


def test_um_fetch_por_vencimento_nao_por_contrato():
    """Proposta §5: 2 posições no mesmo (underlying, expiration) dividem 1
    chamada ao provider."""
    c = _conn()
    _seed_opts(c, [
        {"id": "PETRH340", "underlying": "PETR4", "optionType": "call", "strike": 34.0,
         "expiration": "2099-01-01", "qty": 100, "avg": 1.0, "stop": None, "alvo": None},
        {"id": "PETRH360", "underlying": "PETR4", "optionType": "call", "strike": 36.0,
         "expiration": "2099-01-01", "qty": 100, "avg": 0.5, "stop": None, "alvo": None},
    ])
    chamadas = []

    async def getter(underlying, expiration):
        chamadas.append((underlying, expiration))
        return {"providerStatus": "ok", "underlyingPrice": 38.0, "expiration": expiration,
                "calls": [{"contractSymbol": "PETRH340", "optionType": "call", "strike": 34.0, "lastPrice": 4.5},
                          {"contractSymbol": "PETRH360", "optionType": "call", "strike": 36.0, "lastPrice": 2.5}],
                "puts": []}

    _run(c, getter)
    assert chamadas == [("PETR4", "2099-01-01")]


def test_textos_de_opcao_sem_verbo_de_ordem():
    c = _conn()
    _seed_opts(c, [{"id": "PETRH340", "underlying": "PETR4", "optionType": "call", "strike": 34.0,
                     "expiration": "2099-01-01", "qty": 100, "avg": 1.0, "stop": None, "alvo": 2.0}])
    payload = _option_payload("PETR4", "2099-01-01", "PETRH340", last_price=2.5, spot=40.0)
    r = _run(c, _option_getter({("PETR4", "2099-01-01"): payload}))
    todos = " ".join(e["text"].lower() for e in r["events"])
    for pat in (r"\bcompre\b", r"\bvenda\s+agora\b", r"\bentre\s+agora\b", r"\bdeve\s+comprar\b"):
        assert not re.search(pat, todos), pat


# ---------------------------------------------------------------------------
# OPTGATE-01 / WR-01 (Fase 0/Plano 02) — o ciclo do agente sobrevive ao
# estouro de orçamento do mydata: degrada em vez de bloquear o ciclo.
# ---------------------------------------------------------------------------
def test_ciclo_com_orcamento_estourado_nao_trava_nem_executa(monkeypatch):
    c = _conn()
    _seed_opts(c, [{"id": "PETRH340", "underlying": "PETR4", "optionType": "call", "strike": 34.0,
                     "expiration": "2020-01-01", "qty": 100, "avg": 1.0, "stop": 0.1, "alvo": None}])
    chamadas = []

    async def fake_vencimentos(ticker, pregao=None, *, fetch_json=None):
        chamadas.append(("vencimentos", ticker))
        return []

    async def fake_chain(ticker, vencimento=None, pregao=None, tipo=None, *, fetch_json=None):
        chamadas.append(("chain", ticker))
        return []

    mydata_budget.reset()
    monkeypatch.setattr(options_provider_mydata.mydata_client, "get_vencimentos", fake_vencimentos)
    monkeypatch.setattr(options_provider_mydata.mydata_client, "get_options_chain", fake_chain)
    monkeypatch.setattr(mydata_budget, "pode_gastar", lambda n=1, now=None: False)
    options_provider_mydata._cache.clear()

    r = _run(c, options_provider_mydata.get_options)  # não levanta

    assert r["executed"] == 0
    assert len(store.get(c, "optionPositions", user_id="u1")) == 1
    assert chamadas == []

    mydata_budget.reset()
