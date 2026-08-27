"""Fase 9, Plano 03 — seletor `options_provider.py` (alavanca de rollback por
env, D-04: NUNCA fallback automático).

O que estes testes protegem:
  • `provider_name()` sem env devolve "yahoo" — default de produção
    INALTERADO nesta fase (a virada é o checkpoint humano do Plano 09-06);
  • com `B3_OPTIONS_PROVIDER=mydata`, `get_options()` despacha para o
    adaptador do mydata, e o provedor Yahoo NÃO é chamado;
  • nome desconhecido levanta `ValueError` citando as opções válidas.
"""
import asyncio

import pytest

from app import options_provider as p


@pytest.fixture(autouse=True)
def _sem_env(monkeypatch):
    monkeypatch.delenv("B3_OPTIONS_PROVIDER", raising=False)
    yield
    monkeypatch.delenv("B3_OPTIONS_PROVIDER", raising=False)


def test_provider_name_sem_env_devolve_yahoo():
    assert p.provider_name() == "yahoo"


def test_provider_name_com_env_mydata(monkeypatch):
    monkeypatch.setenv("B3_OPTIONS_PROVIDER", "mydata")
    assert p.provider_name() == "mydata"


def test_provider_name_e_case_insensitive_e_trim(monkeypatch):
    monkeypatch.setenv("B3_OPTIONS_PROVIDER", "  MyData  ")
    assert p.provider_name() == "mydata"


def test_get_options_com_env_banana_levanta_value_error_citando_opcoes(monkeypatch):
    monkeypatch.setenv("B3_OPTIONS_PROVIDER", "banana")
    with pytest.raises(ValueError, match="banana"):
        asyncio.run(p.get_options("PETR4"))


def test_get_options_despacha_para_mydata_quando_env_mydata(monkeypatch):
    monkeypatch.setenv("B3_OPTIONS_PROVIDER", "mydata")
    chamadas = []

    async def fake_mydata_get_options(ticker, expiration=None):
        chamadas.append((ticker, expiration))
        return {"providerStatus": "ok", "source": "mydata"}

    async def fake_yahoo_get_options(ticker, expiration=None):
        raise AssertionError("o provedor yahoo NÃO deveria ser chamado quando o env é mydata")

    monkeypatch.setattr(p.options_provider_mydata, "get_options", fake_mydata_get_options)
    monkeypatch.setattr(p.options_provider_yahoo, "get_options", fake_yahoo_get_options)
    monkeypatch.setitem(p._PROVEDORES, "mydata", fake_mydata_get_options)
    monkeypatch.setitem(p._PROVEDORES, "yahoo", fake_yahoo_get_options)

    out = asyncio.run(p.get_options("PETR4"))
    assert out["source"] == "mydata"
    assert chamadas == [("PETR4", None)]


def test_get_options_despacha_para_yahoo_por_default_sem_chamar_mydata(monkeypatch):
    chamadas = []

    async def fake_yahoo_get_options(ticker, expiration=None):
        chamadas.append((ticker, expiration))
        return {"providerStatus": "ok", "source": "yahoo"}

    async def fake_mydata_get_options(ticker, expiration=None):
        raise AssertionError("o provedor mydata NÃO deveria ser chamado sem B3_OPTIONS_PROVIDER=mydata")

    monkeypatch.setitem(p._PROVEDORES, "yahoo", fake_yahoo_get_options)
    monkeypatch.setitem(p._PROVEDORES, "mydata", fake_mydata_get_options)

    out = asyncio.run(p.get_options("PETR4", "2026-09-19"))
    assert out["source"] == "yahoo"
    assert chamadas == [("PETR4", "2026-09-19")]
