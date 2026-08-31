"""Guardião do provider MOCK de opções (Fase 14, Plano 01).

O que estes testes protegem:
  • payload "ok" tem todas as chaves do contrato de `options_provider_yahoo`;
  • determinismo: duas chamadas seguidas com o mesmo ticker devolvem
    contractSymbol/strike/lastPrice IDÊNTICOS;
  • liquidez sintética passa no gate (`options_quant.liquidity_score` >= 40);
  • `B3_OPTIONS_MOCK_STATUS=degraded` devolve payload degradado e vazio —
    é esta perna que exercita o bloqueio do ADR-004 sem depender do Yahoo
    falhar de verdade;
  • roteamento via `options_provider.get_options` com
    `B3_OPTIONS_PROVIDER=mock`;
  • sem monkeypatch nenhum, `options_provider.provider_name()` continua
    "yahoo" — "mock" nunca é default de produção.
"""
import asyncio
import os

import pytest

from app import options_provider as p
from app import options_provider_mock as mock
from app import options_quant


@pytest.fixture(autouse=True)
def _sem_env(monkeypatch):
    monkeypatch.delenv("B3_OPTIONS_PROVIDER", raising=False)
    monkeypatch.delenv("B3_OPTIONS_MOCK_STATUS", raising=False)
    yield
    monkeypatch.delenv("B3_OPTIONS_PROVIDER", raising=False)
    monkeypatch.delenv("B3_OPTIONS_MOCK_STATUS", raising=False)


CHAVES_TOPO_CONTRATO = {
    "ticker", "symbol", "source", "providerStatus", "underlyingPrice",
    "currency", "expirations", "expiration", "calls", "puts",
}

CHAVES_CONTRATO_ITEM = {
    "contractSymbol", "optionType", "strike", "lastPrice", "bid", "ask",
    "change", "percentChange", "volume", "openInterest",
    "impliedVolatility", "inTheMoney", "currency", "distancePct",
}


def test_payload_ok_tem_todas_as_chaves_do_contrato():
    payload = asyncio.run(mock.get_options("PETR4"))
    assert payload["providerStatus"] == "ok"
    assert CHAVES_TOPO_CONTRATO <= set(payload)
    assert len(payload["calls"]) == 9
    assert len(payload["puts"]) == 9
    for item in payload["calls"] + payload["puts"]:
        assert CHAVES_CONTRATO_ITEM <= set(item)


def test_duas_chamadas_seguidas_devolvem_payload_identico():
    p1 = asyncio.run(mock.get_options("PETR4"))
    p2 = asyncio.run(mock.get_options("PETR4"))
    assert [c["contractSymbol"] for c in p1["calls"]] == [c["contractSymbol"] for c in p2["calls"]]
    assert [c["strike"] for c in p1["calls"]] == [c["strike"] for c in p2["calls"]]
    assert [c["lastPrice"] for c in p1["calls"]] == [c["lastPrice"] for c in p2["calls"]]


def test_liquidity_score_do_primeiro_contrato_aceita_gate():
    payload = asyncio.run(mock.get_options("PETR4"))
    primeiro = payload["calls"][0]
    liq = options_quant.liquidity_score(
        primeiro["volume"], primeiro["openInterest"], primeiro["bid"], primeiro["ask"])
    assert liq["score"] >= 40


def test_ticker_sem_spot_conhecido_usa_default():
    payload = asyncio.run(mock.get_options("BOVA11"))
    assert payload["underlyingPrice"] == mock.MOCK_SPOT_DEFAULT


def test_status_degradado_via_env(monkeypatch):
    monkeypatch.setenv("B3_OPTIONS_MOCK_STATUS", "degraded")
    payload = asyncio.run(mock.get_options("PETR4"))
    assert payload["providerStatus"] == "degraded"
    assert payload["calls"] == []
    assert payload["puts"] == []
    assert payload["expirations"] == []
    assert payload["underlyingPrice"] is None
    assert "warning" in payload


def test_provider_roteia_para_mock_com_env(monkeypatch):
    monkeypatch.setenv("B3_OPTIONS_PROVIDER", "mock")
    out = asyncio.run(p.get_options("PETR4"))
    assert out["providerStatus"] == "ok"
    assert out["source"] == "mock"


def test_provider_default_continua_yahoo_sem_env():
    assert p.provider_name() == "yahoo"
