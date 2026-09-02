"""Fase 15, Plano 03 — motor de proposta: limite interno `rastrear()`/`avaliar()`
(ENG-01, ENG-04), mais os adaptadores contrato ADR-004 -> perna de payoff.

Módulo PURO sob teste (`server/app/opcoes_motor.py`): sem rede, sem banco, sem
LLM. Cadeia sintética montada no próprio teste, mesmo padrão de
`test_opcoes_lastreadas_proposta.py`.

Parte 1 (Task 1): `rastrear()` — a régua de seleção já em produção
(liquidez >= 40 + strike extremo), generalizada para N resultados, e o corte
de liquidez com fonte única (`opcoes_motor.LIQUIDEZ_MINIMA`).

Parte 2 (Task 2): `avaliar()` e os adaptadores `perna_de_contrato`/
`perna_de_acao` — o segundo lado do limite interno.
"""
from app import opcoes_motor


# ─────────────────────────────────────────────────────────────────────────
# Parte 1: rastrear() — fixtures
# ─────────────────────────────────────────────────────────────────────────

_SPOT = 29.0


def _contrato(symbol, kind, strike, price=1.5, volume=5000, oi=None,
              bid=1.48, ask=1.52, delta=None, **extra):
    """Contrato no formato ADR-004 (`options_provider_mydata._clean_contract`)."""
    d = {
        "contractSymbol": symbol, "optionType": kind, "strike": strike,
        "lastPrice": price, "bid": bid, "ask": ask, "volume": volume,
        "openInterest": oi, "impliedVolatility": 0.3, "inTheMoney": False,
        "currency": "BRL", "distancePct": None,
        "greeks": {"delta": delta, "gamma": None, "vega": None, "theta": None, "rho": None},
        "expiration": "2026-09-30",
    }
    d.update(extra)
    return d


def _cadeia_base():
    """Cadeia sintética do `<behavior>`: spot 29.0, calls 30/32/34, puts
    28/26/24, todos líquidos (liquidity_score = 60.0, acima do corte)."""
    calls = [_contrato(f"C{s}", "call", s) for s in (30, 32, 34)]
    puts = [_contrato(f"P{s}", "put", s) for s in (28, 26, 24)]
    return {"providerStatus": "ok", "underlyingPrice": _SPOT,
            "expiration": "2026-09-30", "expirations": ["2026-09-30"],
            "calls": calls, "puts": puts}


# ─────────────────────────────────────────────────────────────────────────
# Parte 1: rastrear() — testes
# ─────────────────────────────────────────────────────────────────────────

def test_rastrear_call_acima_min_retorna_a_mais_proxima():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "call", "referencia": _SPOT, "relacao": "acima", "criterio": "min"})
    assert len(r) == 1
    assert r[0]["strike"] == 30


def test_rastrear_put_abaixo_ou_igual_max_retorna_a_mais_proxima():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "put", "referencia": _SPOT, "relacao": "abaixo_ou_igual", "criterio": "max"})
    assert len(r) == 1
    assert r[0]["strike"] == 28


def test_rastrear_n2_calls_devolve_na_ordem_do_criterio_min():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "call", "referencia": _SPOT, "relacao": "acima", "criterio": "min", "n": 2})
    assert [c["strike"] for c in r] == [30, 32]


def test_rastrear_n2_puts_devolve_na_ordem_do_criterio_max():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "put", "referencia": _SPOT, "relacao": "abaixo_ou_igual", "criterio": "max", "n": 2})
    assert [c["strike"] for c in r] == [28, 26]


def test_rastrear_n_maior_que_candidatos_devolve_todos_sem_levantar():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "call", "referencia": _SPOT, "relacao": "acima", "criterio": "min", "n": 99})
    assert [c["strike"] for c in r] == [30, 32, 34]


def test_rastrear_exclui_last_price_none_zero_negativo():
    cadeia = {"providerStatus": "ok", "calls": [
        _contrato("X40", "call", 40, price=None),
        _contrato("X41", "call", 41, price=0),
        _contrato("X42", "call", 42, price=-1),
        _contrato("X43", "call", 43, price=1.5),
    ], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min", "n": 10})
    assert [c["strike"] for c in r] == [43]


def test_rastrear_exclui_contrato_com_liquidez_abaixo_do_corte():
    cadeia = {"providerStatus": "ok", "calls": [
        _contrato("Y50", "call", 50, price=1.5, volume=10, oi=None, bid=None, ask=None),
    ], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert r == []


def test_rastrear_inclui_caso_real_mydata_sem_open_interest():
    cadeia = {"providerStatus": "ok", "calls": [
        _contrato("Z60", "call", 60, price=1.5, volume=100, oi=None, bid=1.48, ask=1.52),
    ], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert [c["strike"] for c in r] == [60]


def test_rastrear_liquidez_minima_explicita_sobrescreve_default():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "call", "referencia": _SPOT, "relacao": "acima",
                 "criterio": "min", "liquidez_minima": 99})
    assert r == []


def test_rastrear_nenhum_candidato_devolve_lista_vazia_nunca_none():
    cadeia = {"providerStatus": "ok", "calls": [], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert r == []
    assert r is not None


def test_rastrear_cadeia_degradada_devolve_lista_vazia():
    cadeia = _cadeia_base()
    cadeia["providerStatus"] = "degraded"
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert r == []


def test_rastrear_cadeia_invalida_devolve_lista_vazia_sem_excecao():
    assert opcoes_motor.rastrear(None, {"tipo": "call"}) == []
    assert opcoes_motor.rastrear({}, {"tipo": "call"}) == []
    assert opcoes_motor.rastrear("nao-e-dict", {"tipo": "call"}) == []


def test_rastrear_sem_relacao_referencia_nao_filtra_por_spot():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "max"})
    assert [c["strike"] for c in r] == [34]


def test_rastrear_preserva_chaves_originais_do_contrato_adr004():
    cadeia = {"providerStatus": "ok", "calls": [
        _contrato("PETRA30", "call", 30, delta=0.42, distancePct=3.4)
    ], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert len(r) == 1
    assert r[0]["contractSymbol"] == "PETRA30"
    assert r[0]["greeks"]["delta"] == 0.42
    assert r[0]["distancePct"] == 3.4
    assert set(r[0].keys()) >= {"contractSymbol", "optionType", "strike", "lastPrice",
                                 "bid", "ask", "volume", "openInterest", "greeks", "expiration"}


def test_corte_de_liquidez_tem_fonte_unica():
    from app import opcoes_lastreadas
    assert opcoes_lastreadas._LIQUIDEZ_MINIMA == 40
    assert opcoes_lastreadas._LIQUIDEZ_MINIMA is opcoes_motor.LIQUIDEZ_MINIMA
