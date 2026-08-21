"""ADR-017 (Decisão 2, "Guard do bug de granularidade do Yahoo") — o guard de
`_confere_granularidade` que hoje só existia em `scripts/backtest_sinal.py`
vira produção em `yahoo.confere_granularidade`, cobrindo diário/semanal/
mensal/trimestral, não só intraday.

Medição de 2026-08-20 (ADR-016): PETR4/max devolveu 320 barras MENSAIS
rotuladas como diárias — o guard existente em `yahoo.get_history` (linha
~226) só cobria `INTRADAY_INTERVALS`, deixando esse caso passar batido.

Casos offline chamam `yahoo.confere_granularidade` direto com candles
sintéticos (sem mock de HTTP). O caso de `meta.dataGranularity` mais grossa
que o pedido é testado via `get_history` com `_yfetch` monkeypatchado — mesma
técnica de `test_yahoo_intraday.py`. O caso ao vivo é gated por
`B3_TESTE_REDE=1` e comprova o comportamento contra a API real.
"""
import asyncio
import os
from datetime import date, timedelta

import pytest

from app import yahoo


def _candles(dias):
    return [{"date": d.isoformat()} for d in dias]


def test_serie_mensal_rotulada_como_diaria_e_recusada():
    base = date(2000, 2, 1)
    dias = [base + timedelta(days=30 * i) for i in range(10)]
    with pytest.raises(RuntimeError, match="PETR4"):
        yahoo.confere_granularidade(_candles(dias), "1d", "PETR4", "max")


def test_serie_diaria_legitima_passa():
    # Espaçamento 1-3 dias, com fins de semana (sexta -> segunda = 3 dias).
    base = date(2026, 8, 3)  # segunda-feira
    dias, d = [], base
    for _ in range(10):
        dias.append(d)
        d = d + timedelta(days=3 if d.weekday() == 4 else 1)
    yahoo.confere_granularidade(_candles(dias), "1d", "PETR4", "15y")  # não levanta


def test_serie_semanal_legitima_passa():
    base = date(2026, 1, 5)
    dias = [base + timedelta(weeks=i) for i in range(20)]
    yahoo.confere_granularidade(_candles(dias), "1wk", "PETR4", "10y")  # não levanta


def test_menos_de_3_candles_nao_levanta():
    yahoo.confere_granularidade([], "1d", "PETR4", "5d")
    yahoo.confere_granularidade(_candles([date(2026, 1, 1), date(2026, 1, 2)]),
                                 "1d", "PETR4", "5d")


def test_intervalo_desconhecido_intraday_nao_e_barrado_pelo_espacamento():
    # Espaçamento absurdo para 15m, mas o intervalo não está na tabela de
    # espaçamento (é intraday — coberto pelo guard de meta.dataGranularity).
    dias = [date(2026, 1, 1) + timedelta(days=30 * i) for i in range(5)]
    yahoo.confere_granularidade(_candles(dias), "15m", "PETR4", "1mo")  # não levanta


def _payload(interval, n, granularidade, passo=86400, start=1785416400):
    ts = [start + i * passo for i in range(n)]
    return {"chart": {"result": [{
        "meta": {"currency": "BRL", "gmtoffset": -10800, "dataGranularity": granularidade},
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


def test_meta_mais_grossa_que_pedido_e_recusada(monkeypatch):
    # pedido 1d, meta 1mo — exatamente o caso do ADR-016 (PETR4/max).
    _com_payload(monkeypatch, _payload("1d", 5, granularidade="1mo"))
    with pytest.raises(RuntimeError, match="granularidade"):
        asyncio.run(yahoo.get_history("PETR4", rng="max", interval="1d"))


def test_meta_igual_ao_pedido_nao_e_recusada(monkeypatch):
    _com_payload(monkeypatch, _payload("1d", 5, granularidade="1d", passo=86400))
    h = asyncio.run(yahoo.get_history("PETR4", rng="5d", interval="1d"))
    assert len(h["candles"]) == 5


def test_meta_mais_fina_que_pedido_nao_e_recusada(monkeypatch):
    # pedido 1wk, meta 1d (mais fina) — não é o bug (degradação), não recusa.
    _com_payload(monkeypatch, _payload("1wk", 8, granularidade="1d", passo=7 * 86400))
    h = asyncio.run(yahoo.get_history("PETR4", rng="10y", interval="1wk"))
    assert len(h["candles"]) == 8


@pytest.mark.skipif(not os.environ.get("B3_TESTE_REDE"),
                     reason="teste ao vivo contra a API real do Yahoo — gated por B3_TESTE_REDE=1")
def test_ao_vivo_15y_1d_passa_e_max_1d_e_recusado():
    h = asyncio.run(yahoo.get_history("PETR4", rng="15y", interval="1d"))
    assert len(h["candles"]) >= 3000
    with pytest.raises(RuntimeError):
        asyncio.run(yahoo.get_history("PETR4", rng="max", interval="1d"))
