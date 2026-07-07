import asyncio

from app import llm


def test_llm_test_connection_returns_actionable_missing_key():
    cfg = {"provider": "openai", "model": "gpt-4o-mini", "keySource": "manual", "apiKey": ""}
    r = asyncio.run(llm.test_connection(cfg))
    assert r["ok"] is False
    assert "chave" in r["message"].lower()
    assert r["provider"] == "openai"
    assert r["model"] == "gpt-4o-mini"
    assert r["keySource"] == "manual"
    assert "action" in r
