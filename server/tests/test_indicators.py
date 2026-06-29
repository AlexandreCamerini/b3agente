"""Testa o modulo de indicadores tecnicos (item: gráfico/indicadores)."""
from app import indicators as ind


def _const(n, val=10.0):
    return [{"open": val, "high": val, "low": val, "close": val, "volume": 100} for _ in range(n)]


def test_sma_de_serie_constante():
    out = ind.sma([10.0] * 30, 20)
    assert out[18] is None
    assert out[19] == 10.0
    assert out[-1] == 10.0


def test_rsi_em_faixa_0_100():
    closes = [10 + (i % 5) - 2 for i in range(60)]
    r = ind.rsi([float(x) for x in closes], 14)
    vals = [x for x in r if x is not None]
    assert vals, "RSI deve produzir valores"
    assert all(0 <= x <= 100 for x in vals)


def test_macd_hist_e_diferenca():
    closes = [float(20 + i * 0.3) for i in range(60)]
    line, signal, hist = ind.macd(closes)
    for i in range(len(hist)):
        if hist[i] is not None and line[i] is not None and signal[i] is not None:
            assert abs(hist[i] - (line[i] - signal[i])) < 1e-9


def test_compute_e_slice_alinhados():
    candles = _const(80)
    # leve variacao para nao zerar tudo
    for i, c in enumerate(candles):
        c["close"] = 10 + (i % 7) * 0.5
        c["high"] = c["close"] + 0.3
        c["low"] = c["close"] - 0.3
        c["open"] = c["close"]
    full = ind.compute(candles)
    assert set(["sma20", "sma50", "rsi14", "macd", "bbUpper", "stochK", "atr14", "obv"]).issubset(full["indicators"].keys())
    sl = ind.slice_tail(candles, full["indicators"], full["summary"], 22)
    nc = len(sl["candles"])
    assert nc == 22
    assert all(len(arr) == nc for arr in sl["indicators"].values())
    # sma50 calculada sobre a serie completa permanece valida no recorte
    assert sl["indicators"]["sma50"][-1] is not None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE INDICADORES PASSARAM")

def test_sanitize_candles_protege_escala():
    from app import indicators as ind
    raw = [
        {"date": "d1", "open": 40, "high": 41, "low": 39.5, "close": 40.5, "volume": 100},
        {"date": "d2", "open": 40.5, "high": 41.2, "low": 40.1, "close": 41.0, "volume": 120},
        {"date": "d3", "open": 0, "high": None, "low": 0, "close": 41.1, "volume": 0},   # dia em aberto
        {"date": "d4", "open": 0, "high": 0, "low": 0, "close": 999999, "volume": 0},     # corrompido
        {"date": "d5", "open": 10, "high": 11, "low": 9, "close": 0, "volume": 1},         # close invalido
    ]
    clean = ind.sanitize_candles(raw)
    closes = [c["close"] for c in clean]
    assert 999999 not in closes          # outlier descartado (nao estoura o eixo)
    assert 0 not in closes               # close zero/null removido
    last = next(c for c in clean if c["date"] == "d3")
    assert last["low"] > 0               # nao ha low=0 puxando a vela ao chao
    assert last["high"] >= last["close"] and last["low"] <= last["open"]
    # coerencia OHLC em todas as velas validas
    for c in clean:
        assert c["high"] >= c["low"] > 0
        assert c["high"] >= c["open"] and c["high"] >= c["close"]
        assert c["low"] <= c["open"] and c["low"] <= c["close"]
