import asyncio

from app import options_provider_yahoo as provider
from app.yahoo import QuoteUnavailable


def test_options_provider_degrades_instead_of_raising_on_yahoo_401(monkeypatch):
    async def fake_yfetch(client, path, params, retries=3):
        raise QuoteUnavailable("Yahoo HTTP 401")

    provider._cache.clear()
    monkeypatch.setattr(provider, "_yfetch", fake_yfetch)

    data = asyncio.run(provider.get_options("PETR4"))

    assert data["providerStatus"] == "degraded"
    assert data["calls"] == []
    assert data["puts"] == []
    assert "Yahoo Finance" in data["warning"]
    assert "401" in data["providerError"]
