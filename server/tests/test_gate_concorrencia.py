"""Quick 261006-oav (2026-10-06) — limitador do gate de liquidez.

GET /api/options/gate/* nunca roda mais que GATE_CONCORRENCIA chamadas ao
provedor ao mesmo tempo e gasta no máximo a fatia de descoberta (21/min) da
cota do mydata, deixando a reserva do usuário intacta.
"""
import asyncio
from datetime import datetime

import pytest

from app import mydata_budget, obslog, options_api, options_provider_mydata as opm
from app.options_quant import FAIXA_SEM_MERCADO

OK = {"providerStatus": "ok", "underlyingPrice": 30.0, "expiration": "2099-01-15",
      "expirations": ["2099-01-15"], "puts": [],
      "calls": [{"contractSymbol": "X", "optionType": "call", "strike": 30.0,
                 "volume": 5000, "openInterest": 3000, "bid": 1.0, "ask": 1.05}]}


@pytest.fixture(autouse=True)
def _limpo(monkeypatch):
    mydata_budget.reset()
    obslog.reset()
    opm._cache.clear()
    opm._venc_cache.clear()
    yield
    mydata_budget.reset()
    obslog.reset()
    opm._cache.clear()
    opm._venc_cache.clear()


def test_no_maximo_2_simultaneos_e_contexto_descoberta(monkeypatch):
    estado = {"atual": 0, "max": 0, "ctx": []}

    async def _fake(t, *a, **k):
        estado["atual"] += 1
        estado["max"] = max(estado["max"], estado["atual"])
        estado["ctx"].append((mydata_budget.prioridade_atual(), mydata_budget.origem_atual()))
        await asyncio.sleep(0.05)
        estado["atual"] -= 1
        return OK
    monkeypatch.setattr(options_api, "get_options", _fake)

    async def _roda():
        return await asyncio.gather(*[options_api.liquidity_gate(f"ATIV{i}") for i in range(8)])
    res = asyncio.run(_roda())
    assert estado["max"] <= options_api.GATE_CONCORRENCIA == 2
    assert len(res) == 8 and all(r["providerStatus"] == "ok" and r["liquida"] for r in res)
    assert set(estado["ctx"]) == {("descoberta", "GET /api/options/gate")}
    assert mydata_budget.prioridade_atual() == "fundo"


def test_excecao_nao_vaza_slot(monkeypatch):
    n = {"i": 0}

    async def _fake(t, *a, **k):
        n["i"] += 1
        if n["i"] <= 3:
            raise RuntimeError("boom")
        return OK
    monkeypatch.setattr(options_api, "get_options", _fake)

    async def _roda():
        falhas = 0
        for i in range(3):
            try:
                await options_api.liquidity_gate(f"ATIV{i}")
            except RuntimeError:
                falhas += 1
        ok = await asyncio.wait_for(
            asyncio.gather(*[options_api.liquidity_gate(f"OKAY{i}") for i in range(4)]), 2)
        return falhas, ok
    falhas, ok = asyncio.run(_roda())
    assert falhas == 3 and len(ok) == 4


def test_fatia_de_descoberta_com_orcamento_real(monkeypatch):
    class _C:
        async def get_vencimentos(self, *a, **k):
            return [{"dt_vencimento": "2099-01-15"}]

        async def get_options_chain(self, *a, **k):
            return [{"contrato": "X", "tipo": "CALL", "strike": 30.0, "premio": 1.0,
                     "preco_objeto": 30.0, "quantidade_negociada": 5000}]
    c = _C()
    monkeypatch.setattr(opm.mydata_client, "get_vencimentos", c.get_vencimentos)
    monkeypatch.setattr(opm.mydata_client, "get_options_chain", c.get_options_chain)
    monkeypatch.setattr(mydata_budget, "_chave_minuto", lambda now=None: "2026-10-06 10:00")
    monkeypatch.setattr(options_api, "get_options", opm.get_options)

    async def _roda():
        return [await options_api.liquidity_gate(f"ATIV{i}") for i in range(15)]
    res = asyncio.run(_roda())
    snap = mydata_budget.snapshot()
    assert snap["gastoDescobertaMinuto"] <= 21
    degradados = [r for r in res if r["providerStatus"] != "ok"]
    assert degradados, "15 tickers x 2 requisicoes passam de 21"
    for r in degradados:
        assert r == {"ticker": r["ticker"], "liquida": False, "providerStatus": "degraded",
                     "faixa": FAIXA_SEM_MERCADO, "melhorScore": None}
    with mydata_budget.contexto(prioridade="usuario"):
        assert mydata_budget.pode_gastar(2) is True
