"""Quick 261006-dvg (2026-10-06) — conta nova SEMPRE nasce limpa.

Decisão do Alex: a "Decisão B" (adotar o documento local do iPhone como semente
no 1º login) foi revogada (invariante "conta nova nasce limpa"; achado 3 do
46.1-05-SUMMARY). Binários iOS antigos ainda instalados continuam mandando
`body.seed` — por isso o SERVIDOR é a garantia: register/login/oauth ignoram
`seed` por completo e a conta nova nasce de `ensure_defaults`.
"""
import importlib
import os
import re
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _app_main_isolado():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _reimporta(monkeypatch):
    monkeypatch.delenv("B3_GATED_HOSTS", raising=False)
    d = tempfile.mkdtemp(prefix="b3_limpa_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


SEED_HOSTIL = {
    "cash": 1.0,
    "positions": [{"t": "VALE3", "qty": 100, "avg": 60}],
    "history": [{"type": "COMPRA", "t": "VALE3"}],
    "equitySnapshots": [{"data": "2026-01-02", "patrimonio": 1}],
    "watchlist": ["ZZZZ3"],
    "config": {"apiKey": "LOCALKEY", "initialBudget": 12345, "userName": "DoAparelho"},
}


def _assert_limpa(state, ref):
    assert state["positions"] == []
    assert state["history"] == []
    assert state["equitySnapshots"] == []
    assert state["cash"] == ref["cash"]
    assert "ZZZZ3" not in state["watchlist"]
    assert state["config"]["keyStored"] is False
    assert state["config"].get("userName") != "DoAparelho"


def test_register_ignora_seed(monkeypatch):
    c, main = _reimporta(monkeypatch)
    ref = c.post("/api/auth/register", json={"email": "ref@t.com", "password": "senhaboa123"}).json()
    r = c.post("/api/auth/register", json={"email": "n1@t.com", "password": "senhaboa123", "seed": SEED_HOSTIL})
    assert r.status_code == 200, r.text
    j = r.json()
    _assert_limpa(j["state"], ref["state"])
    cfg = main.store.get(main._conn, "config", user_id=j["user"]["id"])
    assert cfg.get("apiKey") != "LOCALKEY"


def test_login_existente_ignora_seed(monkeypatch):
    c, main = _reimporta(monkeypatch)
    j = c.post("/api/auth/register", json={"email": "e1@t.com", "password": "senhaboa123"}).json()
    uid = j["user"]["id"]
    main.store.set_watchlist(main._conn, ["PETR4"], user_id=uid)
    main.store.set_config(main._conn, {"userName": "DoServidor"}, user_id=uid)
    r = c.post("/api/auth/login", json={"email": "e1@t.com", "password": "senhaboa123", "seed": SEED_HOSTIL})
    assert r.status_code == 200, r.text
    st = r.json()["state"]
    assert st["watchlist"] == ["PETR4"]
    assert st["config"]["userName"] == "DoServidor"
    assert st["positions"] == []


def test_oauth_conta_nova_ignora_seed(monkeypatch):
    c, main = _reimporta(monkeypatch)
    ref = c.post("/api/auth/register", json={"email": "ref@t.com", "password": "senhaboa123"}).json()
    monkeypatch.setattr(main.auth, "verify_oauth_token",
                        lambda p, t: {"sub": "g-123", "email": "g@t.com", "email_verified": True})
    r = c.post("/api/auth/oauth", json={"provider": "google", "idToken": "x", "seed": SEED_HOSTIL})
    assert r.status_code == 200, r.text
    _assert_limpa(r.json()["state"], ref["state"])


def test_guardiao_estatico_main_nao_le_seed():
    src = (Path(__file__).resolve().parent.parent / "app" / "main.py").read_text(encoding="utf-8")
    # remove docstring de _apply_seed e linhas de comentário
    src = re.sub(r'(def _apply_seed\([^)]*\) -> None:\s*)""".*?"""', r"\1", src, flags=re.S)
    code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    assert "seed_user_from" not in code
    assert 'body.get("seed"' not in code
    assert 'body["seed"]' not in code
