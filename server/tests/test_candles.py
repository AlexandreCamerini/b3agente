"""Objetivo 4 — seleção de período de candles."""
from app import candles as cm
from app import technical_models as tm


def test_normalize_period():
    assert cm.normalize_period("6mo") == "6mo"
    assert cm.normalize_period("6MO") == "6mo"
    assert cm.normalize_period(" 1y ") == "1y"
    assert cm.normalize_period("xpto") == cm.DEFAULT_PERIOD
    assert cm.normalize_period(None) == cm.DEFAULT_PERIOD


def test_resolve_keep():
    assert cm.resolve_keep("1mo") == 22
    assert cm.resolve_keep("3mo") == 66
    assert cm.resolve_keep("6mo") == 126
    assert cm.resolve_keep("1y") == 252
    assert cm.resolve_keep("2y") == 504
    assert cm.resolve_keep(None) == cm.PERIOD_BARS[cm.DEFAULT_PERIOD]
    assert cm.resolve_keep("lixo") == cm.PERIOD_BARS[cm.DEFAULT_PERIOD]


def test_period_to_range():
    assert cm.period_to_range("3mo") == "3mo"
    assert cm.period_to_range("1y") == "1y"
    assert cm.period_to_range("invalido") == cm.PERIOD_RANGE[cm.DEFAULT_PERIOD]


def test_interval():
    assert cm.normalize_interval("1wk") == "1wk"
    assert cm.normalize_interval("1d") == "1d"
    assert cm.normalize_interval("mensal") == cm.DEFAULT_INTERVAL


def _mk_candles(n):
    out = []
    base = 10.0
    for i in range(n):
        base += (0.1 if i % 2 == 0 else -0.05)
        out.append({"date": f"2026-01-{(i % 28) + 1:02d}", "open": base, "high": base + 0.2,
                    "low": base - 0.2, "close": base, "volume": 1000 + i})
    return out


def test_build_context_tail_n_recorta_janela():
    candles = _mk_candles(400)
    ctx_small = tm.build_context("PETR4", {"price": candles[-1]["close"]}, candles, "completo", None, tail_n=22)
    ctx_big = tm.build_context("PETR4", {"price": candles[-1]["close"]}, candles, "completo", None, tail_n=252)
    # a janela enviada à IA respeita o período (com piso de 20)
    assert ctx_small["historyStats"]["candlesSentToLLM"] == 22
    assert ctx_big["historyStats"]["candlesSentToLLM"] == 252
    assert len(ctx_small["candles"]) == 22
    assert len(ctx_big["candles"]) == 252
    # indicadores de média longa continuam calculados (warmup na série cheia):
    # com 400 candles, SMA50 do resumo não é None nos dois casos
    assert ctx_small["trend"]["sma50"] is not None
    assert ctx_big["trend"]["sma50"] is not None


def test_build_context_tail_n_piso():
    candles = _mk_candles(100)
    ctx = tm.build_context("VALE3", None, candles, "completo", None, tail_n=1)
    assert ctx["historyStats"]["candlesSentToLLM"] >= 20  # piso protege o contexto


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE PERIODO DE CANDLES PASSARAM")
