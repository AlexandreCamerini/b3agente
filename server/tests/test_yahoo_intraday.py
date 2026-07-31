"""ADR-001 (item 5) — a IDENTIDADE da vela vinda do Yahoo.

Medido em 30/07/2026 contra a API real:
  • no diário, `date` é "AAAA-MM-DD" — e assim continua, o app inteiro depende;
  • no intraday, a data sozinha colapsa a série: 617 velas de `15m x 1mo` viram
    22 chaves e 96% dos candles somem em silêncio no `merge_candles`;
  • o horário tem que vir no FUSO DA BOLSA (America/Sao_Paulo, gmtoffset
    -10800), não em UTC — senão a vela das 10:00 da B3 aparece como 13:00;
  • `range=max` com intervalo intraday devolve HTTP 200 com velas MENSAIS
    (dataGranularity="1mo"): degrada em silêncio, e servir isso como intraday
    seria pior que falhar.

Tudo offline: exercita as funções puras e injeta o payload do Yahoo.
"""
import asyncio

import pytest

from app import candle_cache as cc
from app import yahoo


# 2026-07-30 13:00:00Z = 10:00 em São Paulo (gmtoffset -10800): a abertura da B3.
ABERTURA_UTC = 1785416400
OFFSET_B3 = -10800


def test_diario_mantem_a_chave_de_hoje():
    assert yahoo._candle_key(ABERTURA_UTC, "1d", OFFSET_B3) == "2026-07-30"
    assert yahoo._candle_key(ABERTURA_UTC, "1wk", OFFSET_B3) == "2026-07-30"


def test_intraday_carrega_o_horario_no_fuso_da_bolsa():
    # 13:00Z é a ABERTURA (10:00 BRT). Em UTC apareceria como 13:00 — errado.
    assert yahoo._candle_key(ABERTURA_UTC, "15m", OFFSET_B3) == "2026-07-30 10:00"
    assert yahoo._candle_key(ABERTURA_UTC + 900, "15m", OFFSET_B3) == "2026-07-30 10:15"
    assert yahoo._candle_key(ABERTURA_UTC + 60, "1m", OFFSET_B3) == "2026-07-30 10:01"


def test_sem_gmtoffset_cai_no_fuso_da_b3():
    """O offset vem do próprio Yahoo; se faltar, -3h é a B3 — nunca UTC."""
    assert yahoo._candle_key(ABERTURA_UTC, "5m", None) == "2026-07-30 10:00"
    assert yahoo._candle_key(ABERTURA_UTC, "5m", "lixo") == "2026-07-30 10:00"


def _payload(interval, n=26, granularidade=None, passo=900):
    ts = [ABERTURA_UTC + i * passo for i in range(n)]
    return {"chart": {"result": [{
        "meta": {"currency": "BRL", "gmtoffset": OFFSET_B3,
                 "exchangeTimezoneName": "America/Sao_Paulo",
                 "dataGranularity": granularidade or interval},
        "timestamp": ts,
        "indicators": {"quote": [{
            "open": [40 + i * 0.1 for i in range(n)],
            "high": [40.3 + i * 0.1 for i in range(n)],
            "low": [39.8 + i * 0.1 for i in range(n)],
            "close": [40.1 + i * 0.1 for i in range(n)],
            "volume": [1000 + i for i in range(n)],
        }]},
    }]}}


def _com_payload(monkeypatch, payload):
    async def fake(_client, _path, params, retries=3):
        return payload
    monkeypatch.setattr(yahoo, "_yfetch", fake)


def test_get_history_intraday_nao_colapsa_a_serie(monkeypatch):
    _com_payload(monkeypatch, _payload("15m", n=26))
    h = asyncio.run(yahoo.get_history("PETR4", rng="1d", interval="15m"))
    assert len(h["candles"]) == 26
    chaves = [c["date"] for c in h["candles"]]
    assert len(set(chaves)) == 26, "cada vela precisa de chave própria"
    # e o merge do cache preserva as 26 (era aqui que 617 viravam 22)
    assert len(cc.merge_candles([], h["candles"])) == 26
    assert chaves[0] == "2026-07-30 10:00"


def test_get_history_diario_inalterado(monkeypatch):
    _com_payload(monkeypatch, _payload("1d", n=5, passo=86400))
    h = asyncio.run(yahoo.get_history("PETR4", rng="5d"))
    assert [c["date"] for c in h["candles"]] == [
        "2026-07-30", "2026-07-31", "2026-08-01", "2026-08-02", "2026-08-03"]


def test_granularidade_divergente_e_recusada(monkeypatch):
    """`range=max` com 15m devolve 200 + velas MENSAIS. Servir isso como
    intraday seria pior que falhar: o indicador calcularia sobre outro
    timeframe sem ninguém perceber."""
    _com_payload(monkeypatch, _payload("15m", n=10, granularidade="1mo"))
    with pytest.raises(RuntimeError, match="granularidade"):
        asyncio.run(yahoo.get_history("PETR4", rng="max", interval="15m"))


def test_60m_e_1h_sao_o_mesmo_intervalo(monkeypatch):
    """O Yahoo aceita `60m` e responde `dataGranularity: "1h"` — não é
    divergência, é sinônimo, e recusar aqui quebraria o intervalo horário."""
    _com_payload(monkeypatch, _payload("60m", n=8, granularidade="1h", passo=3600))
    h = asyncio.run(yahoo.get_history("PETR4", rng="1d", interval="60m"))
    assert len(h["candles"]) == 8
