# FASE 4 (1.3) — Radar diário: 1 varredura automática por dia útil + manual
# sob demanda. Sem rede e sem pytest-only: roda no mini-runner e no pytest.
import asyncio
import sqlite3
from datetime import datetime

from app import db, radar_daily
from app.radar_daily import BRT


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _conn():
    c = sqlite3.connect(":memory:")
    db.init_db(c)
    return c


def _fake_fetch(symbol, rng):
    async def go():
        base = 10.0 + (hash(symbol) % 7)
        closes = [base + i * 0.1 for i in range(260)]
        candles = [{"time": 1700000000 + i * 86400, "open": v, "high": v * 1.01,
                    "low": v * 0.99, "close": v, "volume": 1000000} for i, v in enumerate(closes)]
        return {"candles": candles, "currency": "BRL"}
    return go()


# ---------------------------- gating puro (should_run) ----------------------
def test_should_run_dia_util_apos_horario():
    seg_0900 = datetime(2026, 7, 6, 9, 0, tzinfo=BRT)   # segunda 09:00 > 08:45
    assert radar_daily.should_run(now=seg_0900, last_date=None) is True


def test_should_run_bloqueia_antes_do_horario():
    seg_0800 = datetime(2026, 7, 6, 8, 0, tzinfo=BRT)
    assert radar_daily.should_run(now=seg_0800, last_date=None) is False


def test_should_run_bloqueia_fim_de_semana():
    sab = datetime(2026, 7, 4, 12, 0, tzinfo=BRT)
    dom = datetime(2026, 7, 5, 12, 0, tzinfo=BRT)
    assert radar_daily.should_run(now=sab, last_date=None) is False
    assert radar_daily.should_run(now=dom, last_date=None) is False


def test_should_run_no_maximo_uma_vez_por_dia():
    seg_1500 = datetime(2026, 7, 6, 15, 0, tzinfo=BRT)
    assert radar_daily.should_run(now=seg_1500, last_date="2026-07-06") is False
    assert radar_daily.should_run(now=seg_1500, last_date="2026-07-03") is True  # sexta anterior


# ---------------------------- armazenar e servir -----------------------------
def test_run_daily_armazena_e_get_stored_serve():
    import os
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3,BBBB3"
    try:
        c = _conn()
        r = _run(radar_daily.run_daily(c, _fake_fetch))
        assert r["scanAuto"] is True and r["scanOrigem"] == "automática"
        assert r.get("results") is not None and r.get("scanAtLabel")
        stored = radar_daily.get_stored(c, r["period"])
        assert stored and stored["scanAt"] == r["scanAt"]
        assert radar_daily.last_run_date(c) == datetime.now(BRT).date().isoformat()
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


def test_manual_substitui_o_do_dia_sem_marcar_automatica():
    import os
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3"
    try:
        c = _conn()
        auto = _run(radar_daily.run_daily(c, _fake_fetch, origem="automática"))
        manual = _run(radar_daily.run_daily(c, _fake_fetch, origem="manual"))
        stored = radar_daily.get_stored(c, manual["period"])
        assert stored["scanOrigem"] == "manual" and stored["scanAuto"] is False
        # a data do ciclo AUTOMÁTICO não é sobrescrita pela manual
        assert radar_daily.last_run_date(c) == datetime.now(BRT).date().isoformat()
        assert auto["scanAt"] != stored["scanAt"] or auto["scanAt"] == stored["scanAt"]  # ambos válidos
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


def test_maybe_run_respeita_gating_e_nunca_estoura():
    import os
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3"
    try:
        c = _conn()
        db.kv_set(c, "radarDailyLastRun", datetime.now(BRT).date().isoformat(), user_id=None)
        assert _run(radar_daily.maybe_run(c, _fake_fetch)) is None  # já rodou hoje

        def _boom(symbol, rng):
            async def go():
                raise RuntimeError("provider caiu")
            return go()
        db.kv_set(c, "radarDailyLastRun", "2000-01-01", user_id=None)
        # se o gating permitir agora, a falha do provedor NÃO pode propagar
        _run(radar_daily.maybe_run(c, _boom))
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


def test_push_best_effort_para_quem_tem_token():
    import os
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3"
    try:
        c = _conn()
        c.execute("INSERT INTO users(id, provider, provider_sub, created_at) VALUES ('u1','t','s1','2026-01-01')")
        c.execute("INSERT INTO users(id, provider, provider_sub, created_at) VALUES ('u2','t','s2','2026-01-01')")
        db.kv_set(c, "pushTokens", ["tok"], user_id="u1")  # só u1 ativou push
        enviados = []

        async def fake_push(uid, title, body):
            enviados.append(uid)
            assert "Radar do dia" in title
        _run(radar_daily.run_daily(c, _fake_fetch, notify_push=fake_push))
        assert enviados == ["u1"]
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)
