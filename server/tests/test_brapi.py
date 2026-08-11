"""ADR-008, Fase 1 (qa/43) — cliente brapi do plano gratuito.

O que estes testes protegem:
  • a validação de plano roda ANTES da rede — recusa da brapi DEBITA cota
    (medição de 11/08/2026), então "tentar para ver" custa orçamento;
  • a chave da vela sai no fuso da bolsa (diário e intraday), a mesma
    identidade que `merge_candles` usa — o bug de colapso de velas do ADR-001;
  • `close` vem de `close`, nunca de `adjustedClose` (25/62 velas do ITSA4
    divergiam entre os dois na medição);
  • granularidade fora do pedido é DESCARTADA, não servida (regra do Yahoo);
  • sem token a falha é ALTA e diz o que falta.
Offline: `fetch_json` é injetável; a fixture é payload REAL do spike de 11/08.
"""
import asyncio

import pytest

from app import brapi

# Payload real (spike 11/08/2026, sandbox): epoch diário = meia-noite BRT.
FIXTURE_DIARIO = {
    "results": [{
        "symbol": "PETR4",
        "currency": "BRL",
        "usedInterval": "1d",
        "usedRange": "5d",
        "historicalDataPrice": [
            {"date": 1786071600, "open": 40.9, "high": 41.35, "low": 40.68,
             "close": 40.87, "volume": 31647900, "adjustedClose": 40.55},
            {"date": 1786330800, "open": 41.32, "high": 42.47, "low": 41.06,
             "close": 42.23, "volume": 74915200, "adjustedClose": 42.23},
            {"date": 1786417200, "open": 42.30, "high": 42.31, "low": 42.29,
             "close": None, "volume": 0},   # vela sem fechamento: descartar
        ],
    }],
}


def _fake(payload):
    async def fetch_json(symbol, params):
        fetch_json.chamadas.append((symbol, dict(params)))
        return payload
    fetch_json.chamadas = []
    return fetch_json


def test_parse_do_payload_real(monkeypatch):
    monkeypatch.setenv("BRAPI_TOKEN", "tok-teste")
    fake = _fake(FIXTURE_DIARIO)
    out = asyncio.run(brapi.get_history("petr4.sa ", rng="5d", interval="1d",
                                        fetch_json=fake))
    # ticker normalizado SEM .SA (brapi não usa o sufixo do Yahoo)
    assert fake.chamadas == [("PETR4", {"range": "5d", "interval": "1d"})]
    assert out["t"] == "PETR4" and out["currency"] == "BRL"
    assert [c["date"] for c in out["candles"]] == ["2026-08-07", "2026-08-10"]
    # close vem de `close` (40.87), NUNCA de adjustedClose (40.55)
    assert out["candles"][0]["close"] == 40.87
    assert out["candles"][1]["volume"] == 74915200


def test_chave_intraday_carrega_horario_no_fuso_da_bolsa():
    # 1786454100 = 2026-08-11 10:15 BRT (padrão observado no sandbox 15m).
    # O plano free não serve 15m, mas a identidade fica pronta para upgrade —
    # é o bug de colapso de velas do ADR-001 (617 velas viravam 22 chaves).
    assert brapi._candle_key(1786330800, "1d") == "2026-08-10"
    assert brapi._candle_key(1786454100, "15m") == "2026-08-11 10:15"


def test_fora_do_plano_nao_toca_a_rede(monkeypatch):
    monkeypatch.setenv("BRAPI_TOKEN", "tok-teste")
    fake = _fake(FIXTURE_DIARIO)
    with pytest.raises(brapi.ForaDoPlano, match="15m"):
        asyncio.run(brapi.get_history("PETR4", rng="1d", interval="15m",
                                      fetch_json=fake))
    with pytest.raises(brapi.ForaDoPlano, match="2y"):
        asyncio.run(brapi.get_history("PETR4", rng="2y", interval="1d",
                                      fetch_json=fake))
    assert fake.chamadas == []   # recusa por plano debita cota: rede intocada


def test_sem_token_falha_alto(monkeypatch):
    monkeypatch.delenv("BRAPI_TOKEN", raising=False)
    with pytest.raises(RuntimeError) as e:
        asyncio.run(brapi.get_history("PETR4", rng="1mo", interval="1d",
                                      fetch_json=_fake(FIXTURE_DIARIO)))
    msg = str(e.value)
    assert "BRAPI_TOKEN" in msg and "ADR-008" in msg


def test_erro_da_api_vira_indisponivel(monkeypatch):
    monkeypatch.setenv("BRAPI_TOKEN", "tok-teste")
    # envelope real de violação de plano (medição 11/08)
    erro = {"error": True, "code": "INVALID_RANGE",
            "message": 'O range "2y" não está disponível no seu plano.'}
    with pytest.raises(brapi.BrapiIndisponivel, match="INVALID_RANGE"):
        asyncio.run(brapi.get_history("PETR4", rng="1mo", interval="1d",
                                      fetch_json=_fake(erro)))
    with pytest.raises(brapi.BrapiIndisponivel, match="sem resultados"):
        asyncio.run(brapi.get_history("PETR4", rng="1mo", interval="1d",
                                      fetch_json=_fake({"results": []})))


def test_granularidade_divergente_e_descartada(monkeypatch):
    monkeypatch.setenv("BRAPI_TOKEN", "tok-teste")
    troca = {"results": [{**FIXTURE_DIARIO["results"][0], "usedInterval": "1mo"}]}
    with pytest.raises(brapi.BrapiIndisponivel, match="granularidade"):
        asyncio.run(brapi.get_history("PETR4", rng="1mo", interval="1d",
                                      fetch_json=_fake(troca)))
