"""ADR-012 (Fase 4) — série diária dos campos hoje só em memória (custo de
IA, orçamento brapi, cache de candles, falhas de push, duração do radar):
obs_daily_metrics (analytics.py), coleta em agent.py e a rota
GET /api/analytics/tendencias. Mesmo padrão dos demais arquivos desta série.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import agent as agent_mod
from app import analytics, db


def _analytics_conn():
    d = tempfile.mkdtemp(prefix="b3_tendencias_analytics_")
    return analytics.connect(os.path.join(d, "analytics.db"))


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_tendencias_")
    return db.connect(os.path.join(d, "b3_agente.db"))


@pytest.fixture(autouse=True)
def _reset_last_metricas():
    agent_mod.LAST_METRICAS_DIARIAS.update(date=None)
    agent_mod.PUSH_FAIL_TODAY.update(date=None, falhas=0)
    yield


# ------------------------- analytics.py: escrita/leitura ---------------------

def test_registrar_e_ler_serie_metrica_com_now_controlado():
    c = _analytics_conn()
    t0 = 1_800_000_000.0
    dia0 = analytics._dia(t0)
    dia1 = analytics._dia(t0 + 86400)
    analytics.registrar_metricas_diarias(c, dia0, {"custo_ia_tokens_dia": 100})
    analytics.registrar_metricas_diarias(c, dia1, {"custo_ia_tokens_dia": 150})
    r = analytics.serie_metrica(c, "custo_ia_tokens_dia", dias=30, _now=t0 + 86400)
    dias = {p["day"]: p["value"] for p in r}
    assert dias[dia0] == 100.0 and dias[dia1] == 150.0
    c.close()


def test_registrar_metricas_diarias_e_upsert_idempotente():
    c = _analytics_conn()
    t0 = 1_800_000_000.0
    dia0 = analytics._dia(t0)
    analytics.registrar_metricas_diarias(c, dia0, {"custo_ia_tokens_dia": 100})
    analytics.registrar_metricas_diarias(c, dia0, {"custo_ia_tokens_dia": 200})
    r = analytics.serie_metrica(c, "custo_ia_tokens_dia", dias=30, _now=t0)
    assert len(r) == 1 and r[0]["value"] == 200.0
    c.close()


def test_registrar_metricas_diarias_ignora_valor_none():
    c = _analytics_conn()
    t0 = 1_800_000_000.0
    dia0 = analytics._dia(t0)
    analytics.registrar_metricas_diarias(c, dia0, {"radar_diario_duracao_s": None})
    r = analytics.serie_metrica(c, "radar_diario_duracao_s", dias=30, _now=t0)
    assert r == []  # None nunca vira linha — nunca fabrica 0 no lugar de "sem dado"
    c.close()


def test_series_metricas_devolve_todas_as_conhecidas_mesmo_vazias():
    c = _analytics_conn()
    r = analytics.series_metricas(c, dias=30)
    assert set(r.keys()) == set(analytics.METRICAS_CONHECIDAS)
    assert all(v == [] for v in r.values())
    c.close()


# --------------------------- agent.py: coleta + gate --------------------------

def test_coletar_metricas_diarias_traz_as_chaves_esperadas(monkeypatch):
    conn = _fresh_db()
    agent_mod.PUSH_FAIL_TODAY.update(date=agent_mod._today(), falhas=3)
    m = agent_mod._coletar_metricas_diarias(conn)
    assert set(m.keys()) == set(analytics.METRICAS_CONHECIDAS)
    assert m["push_automatico_falhas_dia"] == 3
    conn.close()


def test_maybe_registrar_metricas_diarias_grava_e_respeita_gate(monkeypatch):
    conn = _fresh_db()
    cache_conn = _analytics_conn()
    chamadas = []
    original = agent_mod._coletar_metricas_diarias
    monkeypatch.setattr(agent_mod, "_coletar_metricas_diarias", lambda c: (chamadas.append(1), original(c))[1])

    agent_mod._maybe_registrar_metricas_diarias(conn, cache_conn)
    hoje = agent_mod._today()
    r = analytics.serie_metrica(cache_conn, "custo_ia_tokens_dia", dias=1, _now=__import__("time").time())
    assert any(p["day"] == hoje for p in r)
    assert len(chamadas) == 1

    agent_mod._maybe_registrar_metricas_diarias(conn, cache_conn)  # mesmo dia — gate impede recálculo
    assert len(chamadas) == 1
    conn.close()
    cache_conn.close()


# ================================ rotas (TestClient) =========================
@pytest.fixture(autouse=True)
def _app_main_isolado():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, admin_emails=None):
    if admin_emails is None:
        monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    else:
        monkeypatch.setenv("B3_ADMIN_EMAILS", admin_emails)
    d = tempfile.mkdtemp(prefix="b3_tendencias_route_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3_agente.db"))
    sys.modules.pop("app.main", None)
    sys.modules.pop("app.analytics", None)
    sys.modules.pop("app.agent", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main, d


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_rota_tendencias_e_admin_only(monkeypatch):
    c, _main, _d = _client(monkeypatch)
    token_admin = _registra(c, "dono@teste.com")
    token_comum = _registra(c, "outro@teste.com")
    r_comum = c.get("/api/analytics/tendencias", headers={"authorization": f"Bearer {token_comum}"})
    assert r_comum.status_code == 403
    r_admin = c.get("/api/analytics/tendencias", headers={"authorization": f"Bearer {token_admin}"})
    assert r_admin.status_code == 200
    body = r_admin.json()
    assert set(body.keys()) == set(analytics.METRICAS_CONHECIDAS)


def test_rota_tendencias_devolve_serie_apos_registro_manual(monkeypatch):
    c, main, _d = _client(monkeypatch)
    token_admin = _registra(c, "dono@teste.com")
    hoje = analytics._dia(__import__("time").time())
    analytics.registrar_metricas_diarias(main._analytics_conn, hoje, {"custo_ia_tokens_dia": 42})
    r = c.get("/api/analytics/tendencias", headers={"authorization": f"Bearer {token_admin}"})
    assert r.status_code == 200
    serie = r.json()["custo_ia_tokens_dia"]
    assert any(p["day"] == hoje and p["value"] == 42.0 for p in serie)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
