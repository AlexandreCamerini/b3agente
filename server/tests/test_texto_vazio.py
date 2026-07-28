"""qa/48 (reporte do Alex "A LLM não retornou texto") — resposta 200 SEM texto
virava um erro opaco. Agora carrega o motivo de parada do provedor e o tipo de
bloco, distinguindo 'cortou por tamanho' de 'recusou' de 'vazio'.
"""
import asyncio
import pytest
import httpx
from app import llm


def _resp(payload):
    return httpx.Response(200, json=payload, request=httpx.Request("POST", "http://x"))


def test_helper_classifica_max_tokens():
    e = llm._texto_vazio_error({"provider": "openai", "model": "o1"}, "length", None)
    assert e.payload["code"] == "empty_response"
    assert "tamanho" in e.payload["message"].lower()
    assert "length" in e.payload["message"]


def test_helper_classifica_recusa():
    e = llm._texto_vazio_error({"provider": "anthropic", "model": "x"}, "refusal", None)
    assert "recusou" in e.payload["message"].lower()


def test_helper_generico_quando_sem_motivo():
    e = llm._texto_vazio_error({"provider": "openai", "model": "x"}, None, None)
    assert "vazia" in e.payload["message"].lower()
    assert e.payload["code"] == "empty_response"


def test_anthropic_200_sem_texto_levanta_diagnostico(monkeypatch):
    async def fake_post(self, url, **kw):
        return _resp({"stop_reason": "max_tokens",
                      "content": [{"type": "thinking", "text": ""}]})
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    with pytest.raises(llm.LLMUserError) as e:
        asyncio.run(llm._call_anthropic(
            {"provider": "anthropic", "model": "claude-haiku-4-5"}, "k", "s", "u", 100))
    assert e.value.payload["code"] == "empty_response"
    assert "max_tokens" in e.value.payload["message"]


def test_anthropic_aplica_piso_de_max_tokens(monkeypatch):
    """qa/48 (BEEF3): modelos com thinking gastavam max_tokens pensando e eram
    cortados antes do texto. O caminho Anthropic agora impõe um piso generoso
    (teto, não alvo → grátis p/ modelos curtos)."""
    visto = {}

    async def fake_post(self, url, **kw):
        visto["max_tokens"] = kw["json"]["max_tokens"]
        return _resp({"stop_reason": "end_turn",
                      "content": [{"type": "text", "text": "leitura ok"}]})
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    out = asyncio.run(llm._call_anthropic(
        {"provider": "anthropic", "model": "claude-sonnet-5"}, "k", "s", "u", 1800))
    assert out == "leitura ok"
    assert visto["max_tokens"] >= llm._ANTHROPIC_MAX_TOKENS_FLOOR


def test_openai_200_sem_conteudo_levanta_diagnostico(monkeypatch):
    async def fake_post(self, url, **kw):
        return _resp({"choices": [{"finish_reason": "length",
                                   "message": {"content": ""}}]})
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    with pytest.raises(llm.LLMUserError) as e:
        asyncio.run(llm._call_openai_compatible(
            "https://api.openai.com/v1",
            {"provider": "openai", "model": "o1"}, "k", "s", "u", 100))
    assert e.value.payload["code"] == "empty_response"
