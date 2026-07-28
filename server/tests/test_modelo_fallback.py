"""qa/48 (reporte do Alex: "nenhuma análise funciona") — um modelo VAZIO na
config derrubava TODA análise com missing_model. Agora cai num default por
provedor (o usuário sobrepõe em Configurações → Modelo de IA). Guardião: modelo
vazio + provedor conhecido → usa o fallback e chega até a checagem de chave.
"""
import asyncio
import pytest
from app import llm


def test_modelo_vazio_usa_fallback_por_provedor(monkeypatch):
    visto = {}

    async def fake_anthropic(config, key, system, user, max_tokens):
        visto["model"] = config["model"]
        return "ok"

    monkeypatch.setattr(llm, "_call_anthropic", fake_anthropic)
    out = asyncio.run(llm._call_llm(
        {"provider": "anthropic", "model": ""}, "k", "sys", "usr", 100))
    assert out == "ok"
    assert visto["model"] == llm._MODELO_DEFAULT["anthropic"]


def test_modelo_vazio_provedor_desconhecido_ainda_erra():
    # sem provedor mapeável não há default seguro → mantém o erro claro
    with pytest.raises(Exception) as e:
        asyncio.run(llm._call_llm(
            {"provider": "??", "model": ""}, "k", "sys", "usr", 100))
    assert "missing_model" in str(e.value) or "modelo" in str(e.value).lower()


def test_modelo_preenchido_nao_e_sobrescrito(monkeypatch):
    visto = {}

    async def fake_anthropic(config, key, system, user, max_tokens):
        visto["model"] = config["model"]
        return "ok"

    monkeypatch.setattr(llm, "_call_anthropic", fake_anthropic)
    asyncio.run(llm._call_llm(
        {"provider": "anthropic", "model": "claude-sonnet-5"}, "k", "s", "u", 100))
    assert visto["model"] == "claude-sonnet-5"
