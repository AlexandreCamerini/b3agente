"""F5 (2026-08-02) — painel de administração, v1 SÓ VER (decisão do Alex: sem
ação nenhuma nesta versão). Mesmo portão de admin que /api/obs/usage e
/api/obs/logs já usavam (_is_obs_admin) — nada novo em quem pode acessar.

Isolamento igual ao test_gate_cadastro.py: B3_DB_PATH temporário (senão
`_is_obs_admin` bate no banco real do dev pra decidir quem foi o 1º usuário)
e restauração do `app.main` original ao final de cada teste.
"""
import importlib
import os
import sys
import tempfile

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


def _client(monkeypatch, admin_emails=None):
    if admin_emails is None:
        monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    else:
        monkeypatch.setenv("B3_ADMIN_EMAILS", admin_emails)
    d = tempfile.mkdtemp(prefix="b3_admin_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_sem_login_e_401():
    from app.main import app
    c = TestClient(app)
    assert c.get("/api/admin/summary").status_code == 401


def test_usuario_comum_e_403_sem_b3_admin_emails(monkeypatch):
    """Sem a env, só o PRIMEIRO usuário criado é admin — o segundo é comum."""
    c, _ = _client(monkeypatch)
    _registra(c, "primeiro@teste.com")
    token2 = _registra(c, "segundo@teste.com")
    r = c.get("/api/admin/summary", headers={"authorization": f"Bearer {token2}"})
    assert r.status_code == 403


def test_primeiro_usuario_e_admin_por_default(monkeypatch):
    c, _ = _client(monkeypatch)
    token = _registra(c, "dono@teste.com")
    r = c.get("/api/admin/summary", headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["totalUsuarios"] == 1
    assert body["usuarios"][0]["email"] == "dono@teste.com"
    assert "usoIA" in body and "agente" in body and "gate" in body


def test_lista_de_usuarios_nunca_vaza_pass_hash(monkeypatch):
    c, _ = _client(monkeypatch)
    token = _registra(c, "dono@teste.com")
    _registra(c, "outro@teste.com")
    r = c.get("/api/admin/summary", headers={"authorization": f"Bearer {token}"})
    for u in r.json()["usuarios"]:
        assert "pass_hash" not in u
        assert "provider_sub" not in u or u["provider_sub"] is None


def test_b3_admin_emails_tem_prioridade_sobre_o_primeiro_usuario(monkeypatch):
    c, _ = _client(monkeypatch, admin_emails="admin@teste.com")
    token_primeiro = _registra(c, "primeiro@teste.com")   # 1º, mas NÃO está na lista
    token_admin = _registra(c, "admin@teste.com")         # 2º, mas ESTÁ na lista
    assert c.get("/api/admin/summary", headers={"authorization": f"Bearer {token_primeiro}"}).status_code == 403
    assert c.get("/api/admin/summary", headers={"authorization": f"Bearer {token_admin}"}).status_code == 200


def test_resumo_reflete_o_gate_de_cadastro(monkeypatch):
    monkeypatch.setenv("B3_GATED_HOSTS", "acamerini.app")
    c, _ = _client(monkeypatch)
    token = _registra(c, "dono@teste.com")
    r = c.get("/api/admin/summary", headers={"authorization": f"Bearer {token}"})
    assert r.json()["gate"] == {"hostsFechados": ["acamerini.app"], "ativo": True}
