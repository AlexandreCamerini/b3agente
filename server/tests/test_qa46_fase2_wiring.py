"""qa/46 (Fase 2) — os 4 contadores que já existiam em memória mas não tinham
endpoint: aquecimento de fundamentos, passada intraday, push automático falho
e candle_cache.stats(). Este arquivo só cobre o WIRING (o cálculo em si já
tinha guardião próprio em cada módulo)."""
import importlib
import os
import sqlite3
import sys
import tempfile

import pytest

from app import agent, candle_cache, fundamentals, intraday


def _conn():
    from app import db
    c = sqlite3.connect(":memory:")
    db.init_db(c)
    return c


@pytest.fixture(autouse=True)
def _reset_contadores():
    agent.PUSH_FAIL_TODAY.update(date=None, falhas=0)
    yield
    agent.PUSH_FAIL_TODAY.update(date=None, falhas=0)


def test_status_snapshot_expoe_os_3_contadores_novos():
    c = _conn()
    st = agent.status_snapshot(c, interval_s=60)
    assert set(["aquecimentoFundamentos", "intraday", "pushAutomaticoFalhasHoje"]) <= set(st)
    assert st["aquecimentoFundamentos"] == dict(fundamentals.LAST_WARM)
    assert st["intraday"] == dict(intraday.LAST_PASS)
    assert st["pushAutomaticoFalhasHoje"] == dict(agent.PUSH_FAIL_TODAY)


def test_registrar_push_falho_incrementa_e_reseta_por_dia():
    agent._registrar_push_falho()
    agent._registrar_push_falho()
    assert agent.PUSH_FAIL_TODAY["falhas"] == 2
    # simula virada de dia: a próxima chamada zera antes de contar
    agent.PUSH_FAIL_TODAY["date"] = "2000-01-01"
    agent._registrar_push_falho()
    assert agent.PUSH_FAIL_TODAY["falhas"] == 1
    assert agent.PUSH_FAIL_TODAY["date"] == agent._today()


def test_scheduler_loop_registra_push_falho_no_except_certo():
    """Ancoragem (mesmo padrão de test_qa42_finops.py/test_radar_daily.py):
    antes disto era `except: pass` silencioso — uma ordem executada cujo
    push falhasse não deixava rastro nenhum. Reconstruir um cenário real de
    compra+push aqui duplicaria o cenário completo de test_agent.py só para
    provar 1 linha; a ancoragem no texto-fonte garante que o call site certo
    (dentro do laço de push por AÇÃO EXECUTADA, não o de aviso de gatilho)
    chama o contador em vez de engolir a exceção."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "agent.py").read_text(encoding="utf-8")
    assert src.count("except Exception:  # noqa: BLE001 — push é best-effort\n                                    _registrar_push_falho()") == 1, \
        "o except do push por ação executada não está chamando _registrar_push_falho()"


# --------------------------------------------------------------------------
# candle_cache.stats() → /api/obs/usage (_usage_snapshot, em main.py)
# --------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _app_main_isolado():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def test_usage_snapshot_inclui_cache_candles(monkeypatch):
    d = tempfile.mkdtemp(prefix="b3_qa46f2_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3_agente.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    candle_cache.reset()
    candle_cache._CACHE["PETR4@1d"] = {"candles": [{"date": "2026-01-01"}], "at": 123.0}
    try:
        snap = main._usage_snapshot()
        assert "cacheCandles" in snap
        assert snap["cacheCandles"]["PETR4@1d"] == {"n": 1, "at": 123.0}
    finally:
        candle_cache.reset()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
