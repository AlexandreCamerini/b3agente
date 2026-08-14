"""ADR-012 (Fase 1) — agregação cross-usuário de "Eficiência da IA" pro
portal admin: `analysis_outcomes.compute_stats_all_users`, cache genérico em
`analytics.py` (admin_cache), hook em `analysis_outcomes.maybe_run` e a rota
`GET /api/analytics/ia-eficiencia`. Mesmo padrão de test_analytics.py
(módulo + TestClient) e de test_analysis_outcomes.py (seed via registrar()).
"""
import asyncio
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import analysis_outcomes as ao
from app import analytics
from app import db


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_ia_efic_")
    return db.connect(os.path.join(d, "b3_agente.db"))


def _analytics_conn():
    d = tempfile.mkdtemp(prefix="b3_ia_efic_analytics_")
    return analytics.connect(os.path.join(d, "analytics.db"))


@pytest.fixture(autouse=True)
def _reset_last_eval():
    ao.LAST_EVAL.update(date=None, avaliadas=0, erro=None)
    yield


# ------------------------ compute_stats_all_users (módulo) ------------------

def test_compute_stats_all_users_soma_varios_escopos():
    conn = _fresh_db()
    ao.registrar(conn, ticker="PETR4", modo="operador", tipo="n1", modelo="x",
                 setup="IFR2", recomendacao="COMPRAR", stop=37.0, alvo=40.0, preco=38.0,
                 snapshot_id="s1", user_id="u1")
    ao.registrar(conn, ticker="VALE3", modo="estudo", tipo="n2", modelo="x",
                 setup=None, recomendacao="Monitorar", stop=60.0, alvo=65.0, preco=62.0,
                 snapshot_id="s2", user_id="u2")
    stats = ao.compute_stats_all_users(conn)
    assert stats["totalAnalises"] == 2, "precisa agregar os DOIS escopos, não só o primeiro"
    conn.close()


def test_compute_stats_all_users_nao_devolve_user_id_nem_lista_bruta():
    conn = _fresh_db()
    ao.registrar(conn, ticker="PETR4", modo="operador", tipo="n1", modelo="x",
                 setup="IFR2", recomendacao="COMPRAR", stop=37.0, alvo=40.0, preco=38.0,
                 snapshot_id="s1", user_id="u1")
    stats = ao.compute_stats_all_users(conn)
    assert "user_id" not in stats and "userId" not in stats and "outcomes" not in stats
    assert isinstance(stats.get("porSetup"), dict)  # só agregado, formato de compute_stats
    conn.close()


def test_compute_stats_all_users_sem_nenhum_escopo_e_vazio():
    conn = _fresh_db()
    stats = ao.compute_stats_all_users(conn)
    assert stats["totalAnalises"] == 0
    conn.close()


def test_compute_stats_all_users_respeita_filtro_modo():
    conn = _fresh_db()
    ao.registrar(conn, ticker="PETR4", modo="operador", tipo="n1", modelo="x",
                 setup="IFR2", recomendacao="COMPRAR", stop=37.0, alvo=40.0, preco=38.0,
                 snapshot_id="s1", user_id="u1")
    ao.registrar(conn, ticker="VALE3", modo="estudo", tipo="n2", modelo="x",
                 setup=None, recomendacao="Monitorar", stop=60.0, alvo=65.0, preco=62.0,
                 snapshot_id="s2", user_id="u2")
    stats = ao.compute_stats_all_users(conn, modo="operador")
    assert stats["totalAnalises"] == 1
    conn.close()


# ------------------------------- admin_cache (analytics.py) -----------------

def test_admin_cache_ausente_devolve_none():
    c = _analytics_conn()
    assert analytics.get_cache(c, "x") is None
    c.close()


def test_admin_cache_roundtrip():
    c = _analytics_conn()
    analytics.set_cache(c, "x", {"a": 1})
    got = analytics.get_cache(c, "x")
    assert got["value"] == {"a": 1}
    assert got["computedAt"]
    c.close()


def test_admin_cache_upsert_sobrescreve():
    c = _analytics_conn()
    analytics.set_cache(c, "x", {"a": 1})
    analytics.set_cache(c, "x", {"a": 2})
    assert analytics.get_cache(c, "x")["value"] == {"a": 2}
    c.close()


# ------------------------- maybe_run(cache_conn=...) hook --------------------

def test_maybe_run_com_cache_conn_popula_cache_admin():
    conn = _fresh_db()
    cache_conn = _analytics_conn()
    ao.registrar(conn, ticker="PETR4", modo="operador", tipo="n1", modelo="x",
                 setup="IFR2", recomendacao="COMPRAR", stop=37.0, alvo=40.0, preco=38.0,
                 snapshot_id="s1", user_id="u1")

    async def fetch(ticker, rng="6mo"):
        return {"candles": []}  # sem candle novo: outcome fica pendente, mas o cache roda igual

    n = asyncio.run(ao.maybe_run(conn, fetch, cache_conn=cache_conn))
    assert n == 0  # nada resolvido (sem candle), mas o job rodou
    cached = analytics.get_cache(cache_conn, "ia_eficiencia")
    assert cached is not None
    assert cached["value"]["totalAnalises"] == 1
    conn.close()
    cache_conn.close()


def test_maybe_run_sem_cache_conn_nao_quebra():
    conn = _fresh_db()

    async def fetch(ticker, rng="6mo"):
        return {"candles": []}

    n = asyncio.run(ao.maybe_run(conn, fetch, cache_conn=None))
    assert n == 0
    conn.close()


# ================================ rotas (TestClient) =========================
# Mesmo padrão de test_analytics.py: reimporta app.main a cada teste (relê env
# de módulo), banco novo por teste.
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
    d = tempfile.mkdtemp(prefix="b3_ia_efic_route_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3_agente.db"))
    sys.modules.pop("app.main", None)
    sys.modules.pop("app.analytics", None)
    sys.modules.pop("app.analysis_outcomes", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main, d


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["token"], body["user"]["id"]


def test_rota_ia_eficiencia_e_admin_only(monkeypatch):
    c, _main, _d = _client(monkeypatch)
    token_admin, _ = _registra(c, "dono@teste.com")       # 1º usuário = admin por default
    token_comum, _ = _registra(c, "outro@teste.com")
    r_comum = c.get("/api/analytics/ia-eficiencia", headers={"authorization": f"Bearer {token_comum}"})
    assert r_comum.status_code == 403
    r_admin = c.get("/api/analytics/ia-eficiencia", headers={"authorization": f"Bearer {token_admin}"})
    assert r_admin.status_code == 200
    body = r_admin.json()
    assert "totalAnalises" in body and "computedAt" in body


def test_rota_ia_eficiencia_cold_start_agrega_todos_os_usuarios(monkeypatch):
    c, main, _d = _client(monkeypatch)
    token_admin, uid_admin = _registra(c, "dono@teste.com")
    _token_outro, uid_outro = _registra(c, "outro@teste.com")
    ao.registrar(main._conn, ticker="PETR4", modo="operador", tipo="n1", modelo="x",
                 setup="IFR2", recomendacao="COMPRAR", stop=37.0, alvo=40.0, preco=38.0,
                 snapshot_id="s1", user_id=uid_admin)
    ao.registrar(main._conn, ticker="VALE3", modo="estudo", tipo="n2", modelo="x",
                 setup=None, recomendacao="Monitorar", stop=60.0, alvo=65.0, preco=62.0,
                 snapshot_id="s2", user_id=uid_outro)
    assert analytics.get_cache(main._analytics_conn, "ia_eficiencia") is None, \
        "não pode haver cache antes do 1º GET (cold-start é o cenário testado)"
    r = c.get("/api/analytics/ia-eficiencia", headers={"authorization": f"Bearer {token_admin}"})
    assert r.status_code == 200
    body = r.json()
    assert body["totalAnalises"] == 2  # agregou os DOIS usuários, não só o admin
    assert "userId" not in body and "outcomes" not in body
    assert analytics.get_cache(main._analytics_conn, "ia_eficiencia") is not None, \
        "cold-start precisa gravar o cache pra não recalcular em todo GET seguinte"


def test_rota_ia_eficiencia_serve_do_cache_quando_ja_existe(monkeypatch):
    c, main, _d = _client(monkeypatch)
    token_admin, _ = _registra(c, "dono@teste.com")
    analytics.set_cache(main._analytics_conn, "ia_eficiencia", {"totalAnalises": 999, "porSetup": {}})
    r = c.get("/api/analytics/ia-eficiencia", headers={"authorization": f"Bearer {token_admin}"})
    assert r.status_code == 200
    assert r.json()["totalAnalises"] == 999  # serviu do cache existente, não recalculou


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
