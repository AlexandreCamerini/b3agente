"""Testes do hook diário do ledger de sinais (Fase 07, Plano 04, ADR17-B1-03).

Task 1: candle_cache.peek — leitura sem rede (fonte única do hook).
Task 2: signal_ledger_job.run_incremental — avanço incremental, cursor
        derivado do próprio ledger.
Task 3: signal_ledger_job.should_run / maybe_fechar_janela / maybe_run —
        gate diário, fechamento de janela anual, execução assíncrona.
"""
from __future__ import annotations

import asyncio
import sqlite3
import threading
from datetime import date, datetime, timedelta

from app import candle_cache, db, signal_ledger, signal_ledger_job, signal_replay
from app.signal_ledger_job import BRT


def _conn():
    c = sqlite3.connect(":memory:")
    db.init_db(c)
    return c


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


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


MIN_CANDLES = signal_replay.JANELA + signal_replay.HORIZONTE + 10  # 272


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


# --------------------------------------------------------------------------- #
# Task 2: signal_ledger_job.run_incremental
# --------------------------------------------------------------------------- #

def _fake_cs(n, start="2026-01-01"):
    d0 = date.fromisoformat(start)
    return [{"date": (d0 + timedelta(days=i)).isoformat(), "close": 10.0} for i in range(n)]


def _linha(ticker: str, data: str) -> dict:
    return {"ticker": ticker, "setup": "S1", "lado": "alta", "data": data,
            "resultado": "alvo", "r": 1.0, "dataResolucao": data}


class TestRunIncremental:
    def setup_method(self):
        candle_cache.reset()
        candle_cache.configure_db(None, enabled=False)

    def teardown_method(self):
        candle_cache.reset()
        candle_cache.configure_db(None, enabled=False)
        signal_ledger.reset_cache()

    def _seed_cache(self, ticker, n=MIN_CANDLES, start="2026-01-01"):
        cs = _fake_cs(n, start)
        candle_cache._CACHE[f"{ticker}@1d"] = {
            "candles": cs, "currency": "BRL", "at": 0.0, "src": "yahoo",
        }
        return cs

    def test_ledger_vazio_processa_janela_de_recuperacao(self, monkeypatch):
        conn = _conn()
        self._seed_cache("PETR4")
        chamadas = []

        def fake_replay(ticker, cs_arg, dias, **kw):
            chamadas.append(dias)
            return [_linha(ticker, cs_arg[-1]["date"])]

        monkeypatch.setattr(signal_ledger_job.signal_replay, "replay", fake_replay)
        resumo = signal_ledger_job.run_incremental(conn, universo=["PETR4"])
        assert chamadas == [signal_ledger_job.DIAS_RECUPERACAO]
        assert resumo == {"tickers": 1, "novas": 1, "pulados": 0, "erros": []}

    def test_cursor_so_reprocessa_dias_apos_a_ultima_data(self, monkeypatch):
        conn = _conn()
        signal_ledger.registrar_linhas(conn, [_linha("PETR4", "2026-08-10")])
        cs = self._seed_cache("PETR4", n=MIN_CANDLES + 40, start="2026-01-01")
        capturado = {}

        def fake_replay(ticker, cs_arg, dias, **kw):
            capturado["dias"] = dias
            return []

        monkeypatch.setattr(signal_ledger_job.signal_replay, "replay", fake_replay)
        signal_ledger_job.run_incremental(conn, universo=["PETR4"])
        depois = sum(1 for c in cs if c["date"] > "2026-08-10")
        assert depois > 0  # a fixture precisa ter candle após a última data gravada
        assert capturado["dias"] == depois + signal_ledger_job.MARGEM_REPROCESSO

    def test_rodar_duas_vezes_grava_zero_na_segunda(self, monkeypatch):
        conn = _conn()
        self._seed_cache("PETR4")

        def fake_replay(ticker, cs_arg, dias, **kw):
            return [_linha(ticker, "2026-08-15")]  # sempre a mesma linha

        monkeypatch.setattr(signal_ledger_job.signal_replay, "replay", fake_replay)
        primeira = signal_ledger_job.run_incremental(conn, universo=["PETR4"])
        segunda = signal_ledger_job.run_incremental(conn, universo=["PETR4"])
        assert primeira["novas"] == 1
        assert segunda["novas"] == 0

    def test_ticker_pulado_quando_peek_vazio(self):
        conn = _conn()
        resumo = signal_ledger_job.run_incremental(conn, universo=["ZZZZ9"])
        assert resumo == {"tickers": 1, "novas": 0, "pulados": 1, "erros": []}

    def test_replay_levanta_isola_erro_por_ticker(self, monkeypatch):
        conn = _conn()
        self._seed_cache("PETR4")
        self._seed_cache("VALE3")

        def fake_replay(ticker, cs_arg, dias, **kw):
            if ticker == "PETR4":
                raise RuntimeError("boom replay")
            return []

        monkeypatch.setattr(signal_ledger_job.signal_replay, "replay", fake_replay)
        resumo = signal_ledger_job.run_incremental(conn, universo=["PETR4", "VALE3"])
        assert resumo["tickers"] == 2
        assert len(resumo["erros"]) == 1
        assert "PETR4" in resumo["erros"][0]

    def test_registrar_linhas_levanta_isola_erro_por_ticker(self, monkeypatch):
        """Achado do plan-checker (07-04, warning): o try/except cobre
        replay E registrar_linhas juntos — uma falha SÓ em registrar_linhas
        (não no replay) precisa isolar o ticker sem derrubar os demais."""
        conn = _conn()
        self._seed_cache("PETR4")
        self._seed_cache("VALE3")

        def fake_replay(ticker, cs_arg, dias, **kw):
            return [_linha(ticker, cs_arg[-1]["date"])]

        real_registrar = signal_ledger.registrar_linhas

        def fake_registrar(conn_arg, linhas):
            if linhas and linhas[0]["ticker"] == "PETR4":
                raise sqlite3.IntegrityError("boom registrar")
            return real_registrar(conn_arg, linhas)

        monkeypatch.setattr(signal_ledger_job.signal_replay, "replay", fake_replay)
        monkeypatch.setattr(signal_ledger_job.signal_ledger, "registrar_linhas", fake_registrar)
        resumo = signal_ledger_job.run_incremental(conn, universo=["PETR4", "VALE3"])
        assert resumo["tickers"] == 2
        assert len(resumo["erros"]) == 1
        assert "PETR4" in resumo["erros"][0]
        assert resumo["novas"] == 1  # VALE3 gravou normalmente

    def test_agregar_cumulativo_chamado_so_quando_ha_linhas_novas(self, monkeypatch):
        conn = _conn()
        self._seed_cache("PETR4")
        chamado = {"n": 0}
        real_agregar = signal_ledger.agregar_cumulativo

        def fake_agregar(conn_arg):
            chamado["n"] += 1
            return real_agregar(conn_arg)

        monkeypatch.setattr(signal_ledger_job.signal_ledger, "agregar_cumulativo", fake_agregar)

        def fake_replay_vazio(ticker, cs_arg, dias, **kw):
            return []

        monkeypatch.setattr(signal_ledger_job.signal_replay, "replay", fake_replay_vazio)
        signal_ledger_job.run_incremental(conn, universo=["PETR4"])
        assert chamado["n"] == 0

        def fake_replay_com_linha(ticker, cs_arg, dias, **kw):
            return [_linha(ticker, cs_arg[-1]["date"])]

        monkeypatch.setattr(signal_ledger_job.signal_replay, "replay", fake_replay_com_linha)
        signal_ledger_job.run_incremental(conn, universo=["PETR4"])
        assert chamado["n"] == 1


# --------------------------------------------------------------------------- #
# Task 3: gate diário, fechamento de janela anual, maybe_run assíncrono
# --------------------------------------------------------------------------- #

class TestShouldRun:
    def test_bloqueia_fim_de_semana(self):
        sab = datetime(2026, 7, 4, 12, 0, tzinfo=BRT)
        dom = datetime(2026, 7, 5, 12, 0, tzinfo=BRT)
        assert signal_ledger_job.should_run(now=sab, last_date=None) is False
        assert signal_ledger_job.should_run(now=dom, last_date=None) is False

    def test_bloqueia_antes_do_horario_e_libera_depois(self, monkeypatch):
        monkeypatch.delenv("B3_LEDGER_DAILY_HHMM", raising=False)
        antes = datetime(2026, 7, 6, 9, 0, tzinfo=BRT)   # segunda, < 09:15
        depois = datetime(2026, 7, 6, 9, 20, tzinfo=BRT)  # segunda, > 09:15
        assert signal_ledger_job.should_run(now=antes, last_date=None) is False
        assert signal_ledger_job.should_run(now=depois, last_date=None) is True

    def test_bloqueia_quando_ja_rodou_hoje(self):
        seg = datetime(2026, 7, 6, 15, 0, tzinfo=BRT)
        assert signal_ledger_job.should_run(now=seg, last_date="2026-07-06") is False
        assert signal_ledger_job.should_run(now=seg, last_date="2026-07-03") is True


def test_hhmm_invalido_cai_no_default(monkeypatch):
    monkeypatch.setenv("B3_LEDGER_DAILY_HHMM", "não-é-hora")
    assert signal_ledger_job._hhmm() == signal_ledger_job.HHMM_DEFAULT


def test_off_desliga_enabled_e_maybe_run(monkeypatch):
    monkeypatch.setenv("B3_LEDGER_DAILY_OFF", "1")
    assert signal_ledger_job.enabled() is False
    conn = _conn()
    assert _run(signal_ledger_job.maybe_run(conn)) is None


class TestMaybeFecharJanela:
    def test_marcador_ausente_fecha_ano_anterior_e_grava(self, monkeypatch):
        conn = _conn()
        monkeypatch.setattr(signal_ledger_job.pregao, "is_trading_day", lambda d=None: True)
        now = datetime(2026, 8, 20, 10, 0, tzinfo=BRT)
        resultado = signal_ledger_job.maybe_fechar_janela(conn, now=now)
        assert resultado == "2025"
        assert db.kv_get(conn, "signalLedgerJanelaFechada", user_id=None) == "2025"

    def test_mesmo_ano_de_novo_devolve_none_e_nao_regrava(self, monkeypatch):
        conn = _conn()
        monkeypatch.setattr(signal_ledger_job.pregao, "is_trading_day", lambda d=None: True)
        now = datetime(2026, 8, 20, 10, 0, tzinfo=BRT)
        signal_ledger_job.maybe_fechar_janela(conn, now=now)
        assert signal_ledger_job.maybe_fechar_janela(conn, now=now) is None

    def test_dia_nao_util_devolve_none(self, monkeypatch):
        conn = _conn()
        monkeypatch.setattr(signal_ledger_job.pregao, "is_trading_day", lambda d=None: False)
        now = datetime(2026, 8, 20, 10, 0, tzinfo=BRT)
        assert signal_ledger_job.maybe_fechar_janela(conn, now=now) is None
        assert db.kv_get(conn, "signalLedgerJanelaFechada", user_id=None) is None


class TestMaybeRun:
    def test_ja_rodou_hoje_devolve_none(self):
        conn = _conn()
        hoje = datetime.now(BRT).date().isoformat()
        db.kv_set(conn, "signalLedgerLastRun", hoje, user_id=None)
        assert _run(signal_ledger_job.maybe_run(conn)) is None

    def test_excecao_em_run_incremental_e_capturada_e_registrada(self, monkeypatch):
        conn = _conn()
        monkeypatch.setattr(signal_ledger_job, "should_run", lambda **kw: True)
        monkeypatch.setattr(signal_ledger_job, "enabled", lambda: True)

        def _boom(conn_arg):
            raise RuntimeError("boom incremental")

        monkeypatch.setattr(signal_ledger_job, "run_incremental", _boom)
        resultado = _run(signal_ledger_job.maybe_run(conn))
        assert resultado is None
        assert signal_ledger_job.LAST_RUN["erro"] is not None
        assert "boom incremental" in signal_ledger_job.LAST_RUN["erro"]
        # falha não grava o carimbo — precisa poder tentar de novo no próximo tick
        assert signal_ledger_job.last_run_date(conn) is None

    def test_sucesso_grava_last_run_e_atualiza_telemetria(self, monkeypatch):
        conn = _conn()
        monkeypatch.setattr(signal_ledger_job, "should_run", lambda **kw: True)
        monkeypatch.setattr(signal_ledger_job, "enabled", lambda: True)
        resumo_fake = {"tickers": 0, "novas": 0, "pulados": 0, "erros": []}
        monkeypatch.setattr(signal_ledger_job, "run_incremental", lambda conn_arg: resumo_fake)
        monkeypatch.setattr(signal_ledger_job, "maybe_fechar_janela", lambda conn_arg: None)
        resultado = _run(signal_ledger_job.maybe_run(conn))
        assert resultado == resumo_fake
        assert signal_ledger_job.last_run_date(conn) == datetime.now(BRT).date().isoformat()
        assert signal_ledger_job.LAST_RUN["erro"] is None
        assert signal_ledger_job.LAST_RUN["novas"] == 0

    def test_run_incremental_roda_fora_do_laco_de_eventos(self, monkeypatch):
        conn = _conn()
        monkeypatch.setattr(signal_ledger_job, "should_run", lambda **kw: True)
        monkeypatch.setattr(signal_ledger_job, "enabled", lambda: True)
        thread_ids = {"main": threading.get_ident()}

        def fake_incremental(conn_arg):
            thread_ids["worker"] = threading.get_ident()
            return {"tickers": 0, "novas": 0, "pulados": 0, "erros": []}

        monkeypatch.setattr(signal_ledger_job, "run_incremental", fake_incremental)
        _run(signal_ledger_job.maybe_run(conn))
        assert thread_ids["worker"] != thread_ids["main"]
