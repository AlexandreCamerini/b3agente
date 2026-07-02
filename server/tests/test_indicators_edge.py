"""Objetivo 3 — bordas dos indicadores técnicos: série curta, divisão por zero,
candle do dia em aberto, valores nulos. Todas as funções definidas ANTES do
runner (no fim do arquivo) para serem de fato executadas."""
from app import indicators as ind


def _rising(n, start=10.0, step=0.5):
    return [start + step * i for i in range(n)]


def test_serie_curta_tudo_none():
    # com menos dados que a janela, tudo é None (nada de número fabricado)
    assert all(x is None for x in ind.sma([1, 2, 3], 20))
    assert all(x is None for x in ind.ema([1, 2, 3], 21))
    assert all(x is None for x in ind.rsi([1, 2, 3], 14))
    h = [2, 3, 4]; l = [1, 2, 3]; c = [1.5, 2.5, 3.5]
    assert all(x is None for x in ind.atr(h, l, c, 14))


def test_rsi_sem_perdas_vai_a_100():
    # série estritamente crescente => sem perdas => RSI satura em 100 (sem div/0)
    r = ind.rsi(_rising(40), 14)
    ult = next(x for x in reversed(r) if x is not None)
    assert ult == 100.0


def test_rsi_dentro_de_0_100():
    closes = [10, 11, 10.5, 12, 11.8, 13, 12.5, 14, 13.7, 15, 14.2, 16, 15.5, 17, 16.1, 18]
    for x in ind.rsi(closes, 14):
        assert x is None or (0.0 <= x <= 100.0)


def test_estocastico_flat_nao_divide_por_zero():
    # high==low em toda a janela => (hh-ll)==0 => devolve 50 (neutro), sem crash
    n = 20
    highs = [5.0] * n; lows = [5.0] * n; closes = [5.0] * n
    k, d = ind.stochastic(highs, lows, closes, 14, 3)
    ult = next(x for x in reversed(k) if x is not None)
    assert ult == 50.0


def test_obv_com_volume_nulo():
    closes = [10, 11, 10, 12]
    volumes = [None, 100, None, 50]  # nulos tratados como 0, sem crash
    o = ind.obv(closes, volumes)
    assert o[0] == 0.0
    assert o[1] == 100.0      # subiu, soma 100
    assert o[2] == 100.0      # caiu, mas volume None=0 => inalterado
    assert o[3] == 150.0      # subiu, soma 50


def test_compute_serie_vazia_nao_quebra():
    out = ind.compute([])
    assert out["summary"]["close"] is None
    assert out["summary"]["rsi14"] is None
    assert out["summary"]["trend"] == "lateral"


def test_compute_serie_minima_sem_nan():
    candles = ind.sanitize_candles(
        [{"date": f"d{i}", "open": 10, "high": 10.5, "low": 9.5, "close": 10 + (i % 3) * 0.1, "volume": 100} for i in range(5)]
    )
    out = ind.compute(candles)
    # com 5 candles, indicadores de janela longa ficam None — e nada de NaN/Infinity
    for arr in out["indicators"].values():
        for x in arr:
            assert x is None or (x == x and x not in (float("inf"), float("-inf")))


def test_sanitize_descarta_close_invalido():
    raw = [
        {"date": "d1", "open": 10, "high": 11, "low": 9, "close": 10, "volume": 1},
        {"date": "d2", "open": 10, "high": 11, "low": 9, "close": None, "volume": 1},
        {"date": "d3", "open": 10, "high": 11, "low": 9, "close": 0, "volume": 1},
        {"date": "d4", "open": 10, "high": 11, "low": 9, "close": -5, "volume": 1},
    ]
    clean = ind.sanitize_candles(raw)
    assert [c["date"] for c in clean] == ["d1"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE BORDA DE INDICADORES PASSARAM")
