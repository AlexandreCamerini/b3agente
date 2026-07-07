from app.options_quant import black_scholes, breakeven, historical_volatility, liquidity_score


def test_black_scholes_call_basic():
    r = black_scholes("call", spot=100, strike=100, t_years=30/365, rate=0.10, vol=0.25)
    assert r is not None
    assert r.theoretical > 0
    assert 0 < r.delta < 1
    assert r.gamma > 0
    assert r.vega > 0
    assert 0 < r.prob_itm < 1


def test_breakeven_call_and_put():
    assert breakeven("call", 38, 0.72) == 38.72
    assert breakeven("put", 38, 0.72) == 37.28


def test_historical_volatility_needs_window():
    assert historical_volatility([10, 11], 21) is None
    hv = historical_volatility([10 + i * 0.1 for i in range(40)], 21)
    assert hv is not None and hv >= 0


def test_liquidity_score_penalizes_no_market():
    weak = liquidity_score(0, 0, 0, 0)
    strong = liquidity_score(1000, 5000, 1.00, 1.02)
    assert weak["score"] < strong["score"]
