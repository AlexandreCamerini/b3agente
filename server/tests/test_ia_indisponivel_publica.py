"""Quick 261015 — IA fora do ar precisa ser VISÍVEL ao cliente.

Contexto: a IA ficou ~2 semanas fora em produção (saldo do provedor zerado,
`provider_http_400` "credit balance is too low") e ninguém percebeu: as rotas
N2 caíam no fallback determinístico e o scan/deep engolia o erro. O sinal é
`iaIndisponivel: {code, motivo, mensagem}` (N2) e `iaIndisponivel: {code,
motivo}` no topo do /api/scan/deep. Invariante: NUNCA texto cru do provedor,
chave, URL ou host no payload.
"""
import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app import candle_provider, llm, main, scan_deep, technical_snapshot, yahoo

T = "ZZZZ9"
CRU = "Your credit balance is too low to access the Anthropic API. api.anthropic.com sk-ant-abcdefghij"


def _erro_credito():
    return llm._provider_error({"provider": "anthropic", "model": "claude-x"}, 400, CRU)


def test_publico_provider_http_nao_vaza_texto_do_provedor():
    pub = llm.ia_indisponivel_publico(_erro_credito())
    assert pub["code"] == "provider_http_400"
    assert set(pub) == {"code", "motivo"}
    assert "credit" not in json.dumps(pub).lower() and "sk-" not in json.dumps(pub)


def test_publico_codigos_conhecidos_e_desconhecido():
    assert llm.ia_indisponivel_publico(llm.LLMUserError("x", code="missing_key"))["code"] == "missing_key"
    generico = llm.ia_indisponivel_publico(RuntimeError("boom sk-ant-abcdefghij"))
    assert generico["code"] == "ia_falha" and "sk-" not in generico["motivo"]


def test_run_deep_expoe_ia_indisponivel_sem_texto_cru():
    async def deep_call(_item):
        raise _erro_credito()
    payload = {"results": [{"ticker": "T1234", "confluencia": 1, "condicoes_detectadas": ["a"]}]}
    scan_deep.reset()
    r = asyncio.run(scan_deep.run_deep(payload, 1, "1y", deep_call))
    assert r["iaIndisponivel"]["code"] == "provider_http_400"
    assert r["errors"][0]["code"] == "provider_http_400"
    assert "credit" not in json.dumps(r).lower() and "sk-" not in json.dumps(r)


def test_run_deep_sem_falha_de_ia_devolve_none():
    async def deep_call(_item):
        return {"leitura": "ok"}
    payload = {"results": [{"ticker": "T1234", "confluencia": 1, "condicoes_detectadas": ["a"]}]}
    scan_deep.reset()
    r = asyncio.run(scan_deep.run_deep(payload, 1, "1y", deep_call))
    assert r["iaIndisponivel"] is None


def test_run_deep_falha_nao_ia_mantem_erro_antigo_e_none():
    async def deep_call(_item):
        raise ValueError("Sem historico")
    payload = {"results": [{"ticker": "T1234", "confluencia": 1, "condicoes_detectadas": ["a"]}]}
    scan_deep.reset()
    r = asyncio.run(scan_deep.run_deep(payload, 1, "1y", deep_call))
    assert r["iaIndisponivel"] is None and r["errors"][0]["erro"] == "Sem historico"


def _candles(_symbol, rng=None, **_kw):
    async def go():
        cs = [{"date": f"2026-01-01+{i}", "open": 10 + i * 0.1, "high": 10.2 + i * 0.1,
               "low": 9.8 + i * 0.1, "close": 10 + i * 0.1, "volume": 1_000_000}
              for i in range(260)]
        return {"candles": cs, "currency": "BRL"}
    return go()


async def _quote(_t):
    return {"price": 35.9, "change": -0.4}


@pytest.fixture
def cli(monkeypatch):
    monkeypatch.setattr(candle_provider, "get_history", _candles)
    monkeypatch.setattr(yahoo, "get_quote", _quote)
    technical_snapshot.reset()
    with TestClient(main.app) as c:
        yield c
    technical_snapshot.reset()


@pytest.mark.parametrize("rota,alvo", [
    (f"/api/technical/analyze/{T}", "analyze_structured"),
    (f"/api/analyze/{T}", "analyze"),
])
def test_rotas_n2_devolvem_code_motivo_sem_texto_cru(cli, monkeypatch, rota, alvo):
    async def _falha(*_a, **_k):
        raise _erro_credito()
    monkeypatch.setattr(main.llm, alvo, _falha)
    r = cli.post(rota, json={"model": "completo"})
    assert r.status_code == 200
    body = r.json()
    ia = body["iaIndisponivel"]
    assert ia["code"] == "provider_http_400" and ia["motivo"] and ia["mensagem"] == ia["motivo"]
    assert body["fonte"] == "deterministico"
    txt = json.dumps(body).lower()
    for vazamento in ("credit balance", "api.anthropic.com", "sk-ant"):
        assert vazamento not in txt
