"""ADR-014 — handoff de sessão pro web-admin/ dentro do browser in-app.

O que este teste protege:
  - só quem já tem alguma permissão admin minta um código de handoff;
  - o código troca por uma sessão plena, funcional em rota admin de verdade;
  - o código é de USO ÚNICO — a segunda troca falha;
  - código inválido/inexistente não vira sessão.

Isolamento e fixtures iguais a test_adr013_rbac.py (mesmo `_client`/`_registra`).
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


def _client(monkeypatch):
    monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    d = tempfile.mkdtemp(prefix="b3_adr014_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def test_usuario_comum_nao_minta_codigo_de_handoff(monkeypatch):
    c, _ = _client(monkeypatch)
    _registra(c, "dono@teste.com")  # 1º usuário: bootstrap admin
    comum = _registra(c, "comum@teste.com")
    r = c.post("/api/admin/mobile-handoff", headers=_auth(comum["token"]))
    assert r.status_code == 403


def test_admin_minta_e_troca_codigo_por_sessao_plena(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")

    r = c.post("/api/admin/mobile-handoff", headers=_auth(admin["token"]))
    assert r.status_code == 200, r.text
    codigo = r.json()["codigo"]
    assert codigo and codigo != admin["token"]  # nunca reaproveita o token de sessão real

    r = c.post("/api/admin/mobile-handoff/exchange", json={"codigo": codigo})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token"] and body["user"]["id"] == admin["user"]["id"]
    assert body["user"]["permissions"] == admin["user"]["permissions"]

    # a sessão plena resultante funciona numa rota admin de verdade
    r = c.get("/api/admin/audit", headers=_auth(body["token"]))
    assert r.status_code == 200


def test_codigo_de_handoff_e_uso_unico(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    codigo = c.post("/api/admin/mobile-handoff", headers=_auth(admin["token"])).json()["codigo"]

    primeira = c.post("/api/admin/mobile-handoff/exchange", json={"codigo": codigo})
    assert primeira.status_code == 200

    segunda = c.post("/api/admin/mobile-handoff/exchange", json={"codigo": codigo})
    assert segunda.status_code == 401


def test_codigo_invalido_falha(monkeypatch):
    c, _ = _client(monkeypatch)
    r = c.post("/api/admin/mobile-handoff/exchange", json={"codigo": "isso-nao-existe"})
    assert r.status_code == 401


def test_exchange_recusa_codigo_de_usuario_sem_permissao_admin(monkeypatch):
    """Defesa em profundidade: mesmo que um código de sessão comum vaze até
    aqui (não deveria — /mobile-handoff já barra na mint), exchange também
    reconfirma permissão antes de emitir sessão plena."""
    c, main = _client(monkeypatch)
    _registra(c, "dono@teste.com")
    comum = _registra(c, "comum@teste.com")
    # simula um "código" que na verdade é a própria sessão de um usuário comum
    r = c.post("/api/admin/mobile-handoff/exchange", json={"codigo": comum["token"]})
    assert r.status_code == 403
