"""ADR-001 (Decisões 1 e 5) — fronteira do provedor de candles e instrumentação.

O que estes testes protegem:
  • trocar de fonte é CONFIGURAÇÃO (env), não refatoração — é o que torna o
    risco de depender do Yahoo sem contrato reversível barato;
  • o plano B falha ALTO e explica o que falta, em vez de existir meia-boca;
  • o gatilho do plano B é um NÚMERO observável (taxa de não-200 > 2% em 3
    pregões), não uma impressão — sem isso, "temos plano B" é conversa.
Offline: o provedor é injetável.
"""
import asyncio

import pytest

from app import candle_provider as cp


class _Fake(cp.CandleProvider):
    nome = "yahoo"   # se passa pelo memo de get_provider()

    def __init__(self, erro_em=()):
        self.chamadas = []
        self.erro_em = set(erro_em)

    async def history(self, ticker, rng, interval="1d"):
        self.chamadas.append((ticker, rng, interval))
        if ticker in self.erro_em:
            raise RuntimeError("provedor fora do ar")
        return {"t": ticker, "currency": "BRL",
                "candles": [{"date": "2026-07-30", "open": 1, "high": 2, "low": 1, "close": 2, "volume": 10}]}


def _limpa():
    cp.set_provider(None)
    cp.reset()


def test_ponto_unico_delega_ao_provedor_ativo():
    _limpa()
    fake = _Fake()
    cp.set_provider(fake)
    try:
        out = asyncio.run(cp.get_history("PETR4", rng="1d", interval="15m"))
        assert out["t"] == "PETR4"
        assert fake.chamadas == [("PETR4", "1d", "15m")]
    finally:
        _limpa()


def test_provedor_vem_do_ambiente(monkeypatch):
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "yahoo")
    assert cp.get_provider().nome == "yahoo"
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "brapi")
    assert cp.get_provider().nome == "brapi"      # troca sem tocar em código
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "inexistente")
    with pytest.raises(ValueError, match="desconhecido"):
        cp.get_provider()
    monkeypatch.delenv("B3_CANDLE_PROVIDER")
    _limpa()
    assert cp.get_provider().nome == "yahoo"      # default


def test_plano_b_falha_alto_e_diz_o_que_falta():
    """Um provedor não implementado tem que gritar. Silêncio aqui viraria
    'sem histórico disponível' genérico no dia em que o Yahoo cair."""
    with pytest.raises(NotImplementedError) as e:
        asyncio.run(cp.BrapiProvider().history("PETR4", "1d", "15m"))
    msg = str(e.value)
    assert "BRAPI_TOKEN" in msg and "ADR-001" in msg


def test_instrumentacao_conta_requisicoes_e_erros():
    _limpa()
    cp.set_provider(_Fake(erro_em={"RUIM3"}))
    try:
        for _ in range(3):
            asyncio.run(cp.get_history("PETR4", "1d", "15m"))
        with pytest.raises(RuntimeError):
            asyncio.run(cp.get_history("RUIM3", "1d", "15m"))
        snap = cp.snapshot()
        assert snap["requisicoes"] == 4 and snap["erros"] == 1
        dia = list(snap["porDia"].values())[0]
        assert dia["15m"]["req"] == 4 and dia["15m"]["velas"] == 3
        assert dia["15m"]["msMedio"] >= 0
    finally:
        _limpa()


def test_gatilho_do_plano_b_e_um_numero():
    """2% de não-200 em 3 pregões reabre a Decisão 1 do ADR-001. Abaixo de 50
    requisições não alerta — amostra pequena viraria alarme falso a cada deploy."""
    _limpa()
    cp.set_provider(_Fake(erro_em={"RUIM3"}))
    try:
        for _ in range(99):
            asyncio.run(cp.get_history("PETR4", "1d", "15m"))
        assert cp.snapshot()["alerta"] is False          # 0 erros
        with pytest.raises(RuntimeError):
            asyncio.run(cp.get_history("RUIM3", "1d", "15m"))
        s = cp.snapshot()
        assert s["requisicoes"] == 100 and s["taxaErro"] == 0.01
        assert s["alerta"] is False                      # 1% < limiar
        for _ in range(2):
            with pytest.raises(RuntimeError):
                asyncio.run(cp.get_history("RUIM3", "1d", "15m"))
        s = cp.snapshot()
        assert s["taxaErro"] > cp._LIMIAR_ERRO and s["alerta"] is True
    finally:
        _limpa()


def test_amostra_pequena_nao_dispara_alarme():
    _limpa()
    cp.set_provider(_Fake(erro_em={"RUIM3"}))
    try:
        with pytest.raises(RuntimeError):
            asyncio.run(cp.get_history("RUIM3", "1d", "15m"))
        s = cp.snapshot()
        assert s["taxaErro"] == 1.0 and s["alerta"] is False   # 1 requisição só
    finally:
        _limpa()
