"""Fase 13 (v1.3, ADR-010) — guardião de CONTRATO de GET /api/watchlist/quota.

CAP-06 (visibilidade) + CAP-12 (fecha o bypass do iOS, CR-01): o
`deviceStore` do app nativo grava direto no `localStorage` e NAO pode
hardcodar `10` — este endpoint e a UNICA fonte de `max_watchlist` para o
cliente. Este arquivo trava o contrato de 3 campos ({count, limit, planId})
consumido pelos planos 13-02 e 13-03; se o contrato mudar de forma, os dois
planos seguintes quebram em silencio sem este guardiao.

Isolamento igual a test_fase12_cap_watchlist.py/test_fase5_gate_mensal.py
(B3_DB_PATH temporario, reimport de app.main por teste) — necessario porque
`_conn`/caches em memoria (managed, kill-switch, orcamento brapi) sao
globais de modulo.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    from app import agent, brapi_budget, managed
    original = sys.modules.get("app.main")
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, env=None):
    d = tempfile.mkdtemp(prefix="b3_watchlist_quota_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    for k, v in (env or {}).items():
        monkeypatch.setenv(k, v)
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def _semeia(main, scope, n):
    """Semeia a watchlist com N tickers do catalogo padrao (sempre
    'conhecidos' — sobrevivem a normalizacao de store.set_watchlist sem
    precisar de add_custom, evitando I/O de rede)."""
    catalogo = main.store.CATALOG_TICKERS
    assert len(catalogo) >= n, f"catalogo padrao so tem {len(catalogo)} tickers, precisa de {n}"
    tickers_n = list(catalogo[:n])
    gravado = main.store.set_watchlist(main._conn, tickers_n, user_id=scope)
    assert len(gravado) == n, f"semeadura encolheu: esperado {n}, gravado {len(gravado)}"
    return tickers_n


def test_a_free_logada_0_tickers_devolve_count_0_limit_10_plan_free(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "quota-free0@teste.com")
    scope = payload["user"]["id"]
    # conta nova nasce com watchlist padrao (defaults.default_state) — zera
    # explicitamente para medir o caso "0 tickers" descrito no plano.
    main.store.set_watchlist(main._conn, [], user_id=scope)

    r = c.get("/api/watchlist/quota", headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] == 0
    # fonte unica: compara contra plan.py, nao contra o literal 10.
    assert body["limit"] == main.plan.PLAN_FREE["max_watchlist"]
    assert body["planId"] == "free"


def test_b_free_logada_com_n_tickers_count_reflete_n(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "quota-freeN@teste.com")
    scope = payload["user"]["id"]
    _semeia(main, scope, 4)

    r = c.get("/api/watchlist/quota", headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] == 4
    assert body["limit"] == main.plan.PLAN_FREE["max_watchlist"]
    assert body["planId"] == "free"


def test_c_escopo_anonimo_devolve_200_limit_10_plan_free(monkeypatch):
    c, main = _client(monkeypatch)

    r = c.get("/api/watchlist/quota")
    assert r.status_code == 200, r.text
    body = r.json()
    # DIFERENTE de /api/ai/quota: anonimo aqui tem limit REAL (nao None) —
    # a watchlist anonima existe de verdade no balde user_id=None.
    assert body["limit"] == main.plan.PLAN_FREE["max_watchlist"]
    assert body["planId"] == "free"


def test_d_conta_pro_devolve_limit_none_sem_chave_extra_de_teto(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "quota-pro@teste.com")
    scope = payload["user"]["id"]
    main.db.set_user_plan(main._conn, scope, "pro")
    _semeia(main, scope, 3)

    r = c.get("/api/watchlist/quota", headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["limit"] is None
    assert body["planId"] == "pro"
    assert body["count"] == 3
    assert set(body.keys()) == {"count", "limit", "planId"}
