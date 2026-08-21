"""Testes do hook diário do ledger de sinais (Fase 07, Plano 04, ADR17-B1-03).

Task 1: candle_cache.peek — leitura sem rede (fonte única do hook).
Task 2: signal_ledger_job.run_incremental — avanço incremental, cursor
        derivado do próprio ledger.
Task 3: signal_ledger_job.should_run / maybe_fechar_janela / maybe_run —
        gate diário, fechamento de janela anual, execução assíncrona.
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from app import candle_cache, db


def _conn():
    c = sqlite3.connect(":memory:")
    db.init_db(c)
    return c


def _candles(n=5, base_date="2026-08-01"):
    d0 = date.fromisoformat(base_date)
    return [
        {
            "date": (d0 + timedelta(days=i)).isoformat(),
            "open": 10.0 + i, "high": 10.5 + i, "low": 9.5 + i,
            "close": 10.2 + i, "volume": 1_000_000,
        }
        for i in range(n)
    ]


# --------------------------------------------------------------------------- #
# Task 1: candle_cache.peek
# --------------------------------------------------------------------------- #

class TestPeek:
    def setup_method(self):
        candle_cache.reset()
        candle_cache.configure_db(None, enabled=False)

    def teardown_method(self):
        candle_cache.reset()
        candle_cache.configure_db(None, enabled=False)

    def test_peek_l1_populado_devolve_exatamente_o_l1(self):
        cs = _candles(3)
        candle_cache._CACHE["PETR4@1d"] = {
            "candles": cs, "currency": "BRL", "at": 0.0, "src": "yahoo",
        }
        assert candle_cache.peek("PETR4") == cs

    def test_peek_l1_vazio_l2_populado_reidrata_e_devolve(self):
        conn = _conn()
        candle_cache.configure_db(conn, enabled=True)
        cs = _candles(4)
        candle_cache._db_put(
            "VALE3@1d", {"candles": cs, "currency": "BRL", "at": 0.0, "src": "yahoo"}
        )
        # L1 vazio (nada em _CACHE ainda) — peek reidrata do L2.
        assert candle_cache.peek("VALE3") == cs

    def test_peek_sem_nada_em_cache_devolve_vazio(self):
        assert candle_cache.peek("XXXX9") == []

    def test_peek_intraday_com_l1_vazio_devolve_vazio_sem_consultar_l2(self):
        conn = _conn()
        candle_cache.configure_db(conn, enabled=True)
        # Grava direto no L2 (via _db_put) para provar que peek NUNCA olha o
        # L2 em intraday, mesmo que por acidente haja algo lá (ADR-001 Decisão 4).
        candle_cache._db_put(
            "XPTO4@15m", {"candles": _candles(2), "currency": "BRL", "at": 0.0, "src": "yahoo"}
        )
        assert candle_cache.peek("XPTO4", interval="15m") == []

    def test_peek_nunca_faz_chamada_de_rede(self, monkeypatch):
        async def _explode(*_a, **_kw):
            raise AssertionError("peek não deveria tocar em nenhuma rota de fetch")

        monkeypatch.setattr(candle_cache, "load", _explode)
        assert candle_cache.peek("ITUB4") == []
