"""Fase 3, C-12 — `get_quote` (singular) não pode vazar exceção crua do provedor.

Origem: REPORT-01 §C-12 reproduziu ao vivo `POST /api/buy {"t":"XXXXX9"}`
devolvendo HTTP 500 com a URL completa do Yahoo e o parâmetro `crumb` no
corpo da resposta. A causa era uma assimetria: `get_quotes` (plural) já
envolvia `yahoo.get_quote` em try/except há mais tempo (falha por ticker
vira `{"price": None, "error": "..."}`), mas `get_quote` (singular) — o
caminho usado por `/api/buy`, `/api/sell` e a watchlist — não tinha o
mesmo tratamento nos DOIS ramos (brapi-com-fallback e provedor-não-brapi).

Este guardião trava:
  • exceção crua (com URL/`crumb`) nunca sobe de `get_quote`, nos dois ramos;
  • `QuoteUnavailable` continua sendo RELEVANTADA sem alteração — é o
    contrato de indisponibilidade transitória (503) que os chamadores já
    tratam, e não pode regredir;
  • a rota `/api/buy` devolve 502 "Sem cotacao para X" (nunca 500), sem
    vazar `crumb`/URL no corpo;
  • a watchlist continua classificando ticker inexistente como 404
    ("not_found"), não como falha transiente.
"""
import asyncio
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import candle_provider as cp
from app import tickers
from app import yahoo

_URL_SUJA = ("Expecting value: line 1 column 1 (char 0) — "
             "https://query1.finance.yahoo.com/v7/finance/quote?symbols=XXXXX9.SA&"
             "crumb=rZaCr5Q9WJs")


def _limpa():
    cp.set_provider(None)
    cp.set_fallback(None)
    cp.reset()


def test_get_quote_provedor_nao_brapi_erro_cru_vira_preco_nulo(monkeypatch):
    """Ramo provedor-não-brapi: exceção crua do Yahoo nunca sobe."""
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "yahoo")

    async def _explode(_t):
        raise RuntimeError(_URL_SUJA)
    monkeypatch.setattr(yahoo, "get_quote", _explode)

    try:
        out = asyncio.run(cp.get_quote("XXXXX9"))
    finally:
        _limpa()

    assert out["price"] is None
    assert out["t"] == "XXXXX9"
    erro = out["error"].lower()
    assert "http" not in erro
    assert "://" not in erro
    assert "crumb" not in erro
    assert "query1.finance.yahoo.com" not in erro
    assert "runtimeerror" not in erro


def test_get_quote_ramo_brapi_com_fallback_erro_cru_vira_preco_nulo(monkeypatch):
    """Ramo brapi-com-fallback: _quote_brapi devolve None (sem token/orçamento
    ou falha), backup Yahoo levanta exceção crua — ainda assim vira preço
    nulo limpo, nunca sobe."""
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "brapi")
    monkeypatch.setenv("B3_CANDLE_FALLBACK", "yahoo")

    async def _sem_brapi(_t):
        return None
    monkeypatch.setattr(cp, "_quote_brapi", _sem_brapi)

    class _FallbackFake(cp.CandleProvider):
        nome = "yahoo"

    cp.set_fallback(_FallbackFake())

    async def _explode(_t):
        raise RuntimeError(_URL_SUJA)
    monkeypatch.setattr(yahoo, "get_quote", _explode)

    try:
        out = asyncio.run(cp.get_quote("XXXXX9"))
    finally:
        _limpa()

    assert out["price"] is None
    assert out["t"] == "XXXXX9"
    erro = out["error"].lower()
    assert "http" not in erro
    assert "crumb" not in erro


def test_get_quote_unavailable_continua_relancada(monkeypatch):
    """O contrato de indisponibilidade transitória (503 nos chamadores) não
    pode regredir: brapi sem token/orçamento e nenhum backup configurado
    continua levantando QuoteUnavailable."""
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "brapi")
    # "" desliga o backup explicitamente (fallback_name(): string vazia
    # sinaliza "sem backup" — o default implícito de ADR-008 seria "yahoo").
    monkeypatch.setenv("B3_CANDLE_FALLBACK", "")
    monkeypatch.delenv("BRAPI_TOKEN", raising=False)

    try:
        with pytest.raises(cp.QuoteUnavailable):
            asyncio.run(cp.get_quote("XXXXX9"))
    finally:
        _limpa()


def test_api_buy_ticker_inexistente_devolve_502_sem_vazar_detalhe(monkeypatch):
    """Teste de rota: `/api/buy` com ticker inexistente devolve 502 limpo,
    nunca 500, nunca URL/crumb no corpo."""
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "yahoo")
    original_main = sys.modules.get("app.main")
    d = tempfile.mkdtemp(prefix="b3_get_quote_erro_limpo_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    try:
        main = importlib.import_module("app.main")

        async def _explode(_t):
            raise RuntimeError(_URL_SUJA)
        monkeypatch.setattr(main.yahoo, "get_quote", _explode)

        client = TestClient(main.app)
        resp = client.post("/api/buy", json={"t": "XXXXX9", "qty": 10})

        assert resp.status_code == 502, resp.text
        body = resp.json()
        assert body["detail"] == "Sem cotacao para XXXXX9"
        assert "crumb" not in resp.text
        assert "http" not in resp.text.lower()
    finally:
        if original_main is not None:
            sys.modules["app.main"] = original_main
        else:
            sys.modules.pop("app.main", None)
        _limpa()


def test_validation_outcome_ticker_inexistente_continua_not_found():
    """A watchlist continua classificando o resultado limpo (price=None,
    error genérico) como 404 amigável, nunca como falha transiente."""
    quote = {"t": "XXXXX9", "price": None, "change": 0,
             "error": "sem cotação (falha do provedor de dados)"}
    outcome = tickers.validation_outcome(quote, False)
    assert outcome["status"] == "not_found"
