"""Fase 9, Plano 02 — MydataProvider no registro + cadeia de fallback de N
saltos + roteador com gate por provedor (D-01/D-03 do 09-CONTEXT.md).

O que estes testes protegem:
  • `mydata` é selecionável por env sem tocar nenhum call site (D-01);
  • a degradação mydata→brapi→Yahoo acontece na MESMA requisição (D-03);
  • intraday NUNCA toca o mydata (ADR-001 intocada);
  • cota do mydata é consultada e debitada por elo, antes da rede;
  • esgotada a cadeia inteira, o erro sobe — nada é inventado (princípio 4).
Offline: todos os provedores são injetáveis via `set_provider`/`set_fallbacks`.
"""
import asyncio

import pytest

from app import candle_provider as cp
from tests.test_candle_provider import _Fake, _limpa


class _FakeNome(_Fake):
    """_Fake com nome configurável — mesma forma de test_candle_provider.py."""

    def __init__(self, nome, **kw):
        super().__init__(**kw)
        self.nome = nome


# ---------------------------------------------------------------------------
# Task 1 — registro + cadeia de fallback de N saltos
# ---------------------------------------------------------------------------
def test_tres_provedores_no_registro():
    assert sorted(cp._PROVEDORES) == ["brapi", "mydata", "yahoo"]


def test_mydata_selecionavel_por_env(monkeypatch):
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "mydata")
    try:
        assert cp.get_provider().nome == "mydata"
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_fallback_names_default_mydata_e_dois_saltos(monkeypatch):
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "mydata")
    monkeypatch.delenv("B3_CANDLE_FALLBACK", raising=False)
    try:
        assert cp.fallback_names() == ["brapi", "yahoo"]
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_fallback_names_default_brapi_preserva_comportamento_de_hoje(monkeypatch):
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "brapi")
    monkeypatch.delenv("B3_CANDLE_FALLBACK", raising=False)
    try:
        assert cp.fallback_names() == ["yahoo"]
        assert cp.fallback_name() == "yahoo"
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_fallback_names_default_yahoo_vazio(monkeypatch):
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "yahoo")
    monkeypatch.delenv("B3_CANDLE_FALLBACK", raising=False)
    try:
        assert cp.fallback_names() == []
        assert cp.fallback_name() == ""
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_fallback_names_explicito_por_env(monkeypatch):
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "mydata")
    monkeypatch.setenv("B3_CANDLE_FALLBACK", "brapi,yahoo")
    try:
        assert cp.fallback_names() == ["brapi", "yahoo"]
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        monkeypatch.delenv("B3_CANDLE_FALLBACK", raising=False)
        _limpa()


def test_fallback_names_vazio_desliga(monkeypatch):
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "mydata")
    monkeypatch.setenv("B3_CANDLE_FALLBACK", "")
    try:
        assert cp.fallback_names() == []
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        monkeypatch.delenv("B3_CANDLE_FALLBACK", raising=False)
        _limpa()


def test_fallback_names_remove_o_proprio_primario_e_nome_desconhecido(monkeypatch):
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "mydata")
    monkeypatch.setenv("B3_CANDLE_FALLBACK", "mydata,inexistente,brapi,brapi,yahoo")
    try:
        assert cp.fallback_names() == ["brapi", "yahoo"]
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        monkeypatch.delenv("B3_CANDLE_FALLBACK", raising=False)
        _limpa()


def test_set_fallback_provedor_unico_continua_funcionando():
    _limpa()
    fb = _FakeNome("yahoo")
    cp.set_fallback(fb)
    try:
        assert cp.get_fallbacks() == [fb]
        assert cp.get_fallback() is fb
    finally:
        _limpa()


def test_set_fallbacks_injeta_cadeia_inteira():
    _limpa()
    fb1 = _FakeNome("brapi")
    fb2 = _FakeNome("yahoo")
    cp.set_fallbacks([fb1, fb2])
    try:
        assert cp.get_fallbacks() == [fb1, fb2]
        assert cp.get_fallback() is fb1
    finally:
        _limpa()
