from app import technical_models


def _candles(n=140):
    out = []
    price = 20.0
    for i in range(n):
        price += 0.08
        out.append({
            "date": f"2026-01-{(i%28)+1:02d}",
            "open": price - 0.05,
            "high": price + 0.20,
            "low": price - 0.20,
            "close": price,
            "volume": 1000000 + i * 1000,
        })
    return out


def test_build_context_envia_candles_e_modelo():
    ctx = technical_models.build_context("PETR4", {"price": 31.2}, _candles(), "momentum")
    assert ctx["model"] == "momentum"
    assert ctx["modelLabel"] == "Momentum"
    assert len(ctx["candles"]) == 120
    assert ctx["momentum"]["rsi14"] is not None
    assert ctx["historyStats"]["candlesSentToLLM"] == 120


def test_modelo_invalido_vira_completo():
    ctx = technical_models.build_context("PETR4", {}, _candles(80), "qualquer")
    assert ctx["model"] == "completo"
    assert ctx["focus"] == "Usar todos os blocos."


def test_compact_response_nao_carrega_candles():
    ctx = technical_models.build_context("PETR4", {}, _candles(), "swing_trade")
    compact = technical_models.compact_for_response(ctx)
    assert "candles" not in compact
    assert compact["riskPlanReference"]["stopReference"] is not None
