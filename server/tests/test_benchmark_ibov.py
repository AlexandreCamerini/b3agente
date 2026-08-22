"""Guardiao da serie diaria do Ibovespa (FIX-C03, Plano 04-02).

`_yfetch` monkeypatchado (sem rede): payload feliz, close=None no meio,
dataGranularity degradada, payload vazio, QuoteUnavailable do provedor, e
cache TTL (2a chamada dentro da janela nao invoca o fetch de novo).
"""
import pytest

from app import benchmark, yahoo


def _payload(timestamps, closes, granularity="1d", gmtoffset=-10800):
    return {
        "chart": {
            "result": [{
                "meta": {"gmtoffset": gmtoffset, "dataGranularity": granularity},
                "timestamp": timestamps,
                "indicators": {"quote": [{"close": closes}]},
            }]
        }
    }


@pytest.fixture(autouse=True)
def _limpa_cache():
    benchmark.limpar_cache()
    yield
    benchmark.limpar_cache()


class _FakeFetch:
    def __init__(self, payload=None, exc=None):
        self.payload = payload
        self.exc = exc
        self.chamadas = 0

    async def __call__(self, client, path, params, retries=3):
        self.chamadas += 1
        if self.exc:
            raise self.exc
        return self.payload


def test_payload_feliz_devolve_contrato(monkeypatch):
    ts = [1735707600, 1735794000, 1735880400, 1735966800, 1736053200]  # 5 timestamps
    closes = [130000.0, 130500.0, 131000.0, 130800.0, 131200.0]
    fake = _FakeFetch(payload=_payload(ts, closes))
    monkeypatch.setattr(yahoo, "_yfetch", fake)

    r = _run(benchmark.serie_ibov())

    assert len(r["candles"]) == 5
    assert r["t"] == "^BVSP"
    assert r["nome"] == "Ibovespa"
    assert r["fonte"] == "yahoo"
    assert r["asOf"] == r["candles"][-1]["date"]


def test_close_none_no_meio_e_pulado(monkeypatch):
    ts = [1735707600, 1735794000, 1735880400]
    closes = [130000.0, None, 131000.0]
    fake = _FakeFetch(payload=_payload(ts, closes))
    monkeypatch.setattr(yahoo, "_yfetch", fake)

    r = _run(benchmark.serie_ibov())

    assert len(r["candles"]) == 2
    assert all(c["close"] != 0 for c in r["candles"])


def test_granularidade_degradada_levanta_indisponivel(monkeypatch):
    ts = [1735707600, 1735794000, 1735880400]
    closes = [130000.0, 130500.0, 131000.0]
    fake = _FakeFetch(payload=_payload(ts, closes, granularity="1mo"))
    monkeypatch.setattr(yahoo, "_yfetch", fake)

    with pytest.raises(benchmark.BenchmarkIndisponivel):
        _run(benchmark.serie_ibov())


def test_payload_vazio_levanta_indisponivel(monkeypatch):
    fake = _FakeFetch(payload=_payload([], []))
    monkeypatch.setattr(yahoo, "_yfetch", fake)

    with pytest.raises(benchmark.BenchmarkIndisponivel):
        _run(benchmark.serie_ibov())


def test_quote_unavailable_do_provedor_nao_vaza_detalhe(monkeypatch):
    fake = _FakeFetch(exc=yahoo.QuoteUnavailable("Yahoo HTTP 429 crumb=abc123 cookie=xyz host=query1.finance.yahoo.com"))
    monkeypatch.setattr(yahoo, "_yfetch", fake)

    with pytest.raises(benchmark.BenchmarkIndisponivel) as exc_info:
        _run(benchmark.serie_ibov())

    msg = str(exc_info.value)
    assert "crumb" not in msg
    assert "cookie" not in msg
    assert "query1.finance.yahoo.com" not in msg


def test_cache_ttl_evita_segunda_chamada(monkeypatch):
    ts = [1735707600, 1735794000, 1735880400]
    closes = [130000.0, 130500.0, 131000.0]
    fake = _FakeFetch(payload=_payload(ts, closes))
    monkeypatch.setattr(yahoo, "_yfetch", fake)

    _run(benchmark.serie_ibov(period="1y"))
    _run(benchmark.serie_ibov(period="1y"))

    assert fake.chamadas == 1


def _run(coro):
    import asyncio
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)
