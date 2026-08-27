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


# ---------------------------------------------------------------------------
# Task 2 — roteador com gate por provedor e degradação mydata→brapi→Yahoo
# ---------------------------------------------------------------------------
def _cadeia(monkeypatch, *, mydata_kw=None, brapi_kw=None, yahoo_kw=None,
            mydata_pode=True, brapi_pode=True):
    """Monta primário 'mydata' + cadeia ['brapi', 'yahoo'], cota liberada."""
    from app import brapi_budget as bb
    from app import mydata_budget as mb
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "mydata")
    prim = _FakeNome("mydata", **(mydata_kw or {}))
    fb_brapi = _FakeNome("brapi", **(brapi_kw or {}))
    fb_yahoo = _FakeNome("yahoo", **(yahoo_kw or {}))
    cp.set_provider(prim)
    cp.set_fallbacks([fb_brapi, fb_yahoo])
    monkeypatch.setattr(mb, "pode_gastar", lambda n=1, now=None: mydata_pode)
    monkeypatch.setattr(bb, "pode_gastar", lambda fatia, now=None: brapi_pode)
    debitos_mydata = []
    debitos_brapi = []
    monkeypatch.setattr(mb, "debita", lambda n=1, now=None: debitos_mydata.append(n))
    monkeypatch.setattr(bb, "debita", lambda fatia, n=1, now=None: debitos_brapi.append(fatia))
    return prim, fb_brapi, fb_yahoo, debitos_mydata, debitos_brapi


def test_primario_mydata_sadio_serve_e_marca_source(monkeypatch):
    prim, fb_brapi, fb_yahoo, deb_my, deb_br = _cadeia(monkeypatch)
    try:
        out = asyncio.run(cp.get_history("PETR4", rng="1mo"))
        assert out["source"] == "mydata" and out["candles"]
        assert fb_brapi.chamadas == [] and fb_yahoo.chamadas == []
        assert deb_my == [1]
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_cadeia_mydata_falha_cai_na_brapi_sem_tocar_yahoo(monkeypatch):
    prim, fb_brapi, fb_yahoo, deb_my, deb_br = _cadeia(
        monkeypatch, mydata_kw={"erro_em": {"PETR4"}})
    try:
        out = asyncio.run(cp.get_history("PETR4", rng="1mo"))
        assert out["source"] == "brapi"
        assert fb_yahoo.chamadas == []
        assert deb_br == ["delta"]
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_cadeia_dois_saltos_mydata_brapi_yahoo(monkeypatch):
    """Mydata e brapi falhando: cai no Yahoo, prova a cadeia de DOIS saltos."""
    prim, fb_brapi, fb_yahoo, deb_my, deb_br = _cadeia(
        monkeypatch, mydata_kw={"erro_em": {"PETR4"}}, brapi_kw={"erro_em": {"PETR4"}})
    try:
        out = asyncio.run(cp.get_history("PETR4", rng="1mo"))
        assert out["source"] == "yahoo" and out["candles"]
        assert len(fb_brapi.chamadas) == 1 and len(fb_yahoo.chamadas) == 1
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_cadeia_tres_falhas_relanca_o_ultimo_erro(monkeypatch):
    prim, fb_brapi, fb_yahoo, deb_my, deb_br = _cadeia(
        monkeypatch, mydata_kw={"erro_em": {"PETR4"}},
        brapi_kw={"erro_em": {"PETR4"}}, yahoo_kw={"erro_em": {"PETR4"}})
    try:
        with pytest.raises(RuntimeError):
            asyncio.run(cp.get_history("PETR4", rng="1mo"))
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_cadeia_serie_vazia_do_primario_tenta_proximo(monkeypatch):
    prim, fb_brapi, fb_yahoo, deb_my, deb_br = _cadeia(
        monkeypatch, mydata_kw={"vazio_em": {"PETR4"}})
    try:
        out = asyncio.run(cp.get_history("PETR4", rng="1mo"))
        assert out["source"] == "brapi" and out["candles"]
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_primario_mydata_intraday_nao_toca_o_mydata(monkeypatch):
    """O ponto central de D-03: interval='15m' nunca chega ao MydataProvider —
    a cadeia inteira serve, e o Yahoo é quem responde (ADR-001 intocada)."""
    prim, fb_brapi, fb_yahoo, deb_my, deb_br = _cadeia(monkeypatch)
    try:
        out = asyncio.run(cp.get_history("PETR4", rng="1d", interval="15m"))
        assert prim.chamadas == []
        assert out["source"] == "yahoo"
        assert deb_my == []
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_primario_mydata_sem_cota_pula_pro_proximo_sem_tocar_rede(monkeypatch):
    prim, fb_brapi, fb_yahoo, deb_my, deb_br = _cadeia(monkeypatch, mydata_pode=False)
    try:
        out = asyncio.run(cp.get_history("PETR4", rng="1mo"))
        assert prim.chamadas == []
        assert out["source"] == "brapi"
        assert deb_my == []
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_primario_mydata_com_vaga_debita_uma_vez(monkeypatch):
    prim, fb_brapi, fb_yahoo, deb_my, deb_br = _cadeia(monkeypatch)
    try:
        asyncio.run(cp.get_history("PETR4", rng="1mo"))
        assert deb_my == [1]
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_cadeia_brapi_fallback_fora_do_plano_e_pulada_sem_rede(monkeypatch):
    """Quando a brapi é FALLBACK (não primário) e o pedido está fora do plano
    gratuito dela, ela é pulada SEM tocar a rede — o Yahoo serve."""
    prim, fb_brapi, fb_yahoo, deb_my, deb_br = _cadeia(
        monkeypatch, mydata_kw={"erro_em": {"PETR4"}})
    try:
        out = asyncio.run(cp.get_history("PETR4", rng="2y"))
        assert out["source"] == "yahoo"
        assert fb_brapi.chamadas == []
        assert deb_br == []
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_cadeia_brapi_fallback_sem_orcamento_e_pulada(monkeypatch):
    prim, fb_brapi, fb_yahoo, deb_my, deb_br = _cadeia(
        monkeypatch, mydata_kw={"erro_em": {"PETR4"}}, brapi_pode=False)
    try:
        out = asyncio.run(cp.get_history("PETR4", rng="1mo"))
        assert out["source"] == "yahoo"
        assert fb_brapi.chamadas == []
        assert deb_br == []
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


def test_primario_brapi_fora_do_plano_continua_indo_direto_ao_yahoo(monkeypatch):
    """Comportamento pré-existente intacto: primário brapi (não mydata) com
    ForaDoPlano continua indo direto ao Yahoo e debitando a fatia 'delta'
    quando serve normalmente."""
    from app import brapi_budget as bb
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "brapi")
    prim = _FakeNome("brapi")
    fb = _FakeNome("yahoo")
    cp.set_provider(prim)
    cp.set_fallbacks([fb])
    monkeypatch.setattr(bb, "pode_gastar", lambda fatia, now=None: True)
    debitos = []
    monkeypatch.setattr(bb, "debita", lambda fatia, n=1, now=None: debitos.append(fatia))
    try:
        out = asyncio.run(cp.get_history("PETR4", rng="1d", interval="15m"))
        assert out["source"] == "yahoo" and prim.chamadas == []
        assert debitos == []

        out2 = asyncio.run(cp.get_history("PETR4", rng="1mo", interval="1d"))
        assert out2["source"] == "brapi" and debitos == ["delta"]
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()
