"""ADR-008 (controle de utilização) — endpoint admin da projeção.

O que este teste protege: a projeção responde NA HORA sem aplicar nada; a
aplicação exige {"aplicar": true} explícito; o portão é o mesmo admin das
rotas obs/*. Isolamento igual ao test_admin_summary (B3_DB_PATH temporário).
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    from app import brapi_budget
    original = sys.modules.get("app.main")
    brapi_budget.reset()
    yield
    brapi_budget.reset()
    brapi_budget.configure_db(None, enabled=False)
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch):
    monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    d = tempfile.mkdtemp(prefix="b3_proj_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app)


def _admin_token(c):
    r = c.post("/api/auth/register", json={"email": "dono@teste.com",
                                           "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_get_simula_sem_aplicar_e_post_exige_confirmacao(monkeypatch):
    from app import brapi_budget as bb
    c = _client(monkeypatch)
    h = {"authorization": "Bearer " + _admin_token(c)}

    r = c.get("/api/obs/brapi/projecao", params={"intervaloS": 600}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["aplicado"] is False
    assert body["projecao"]["intervaloS"] == 600
    assert {"chamadasMes", "percentualDaCota", "cabeNaCota",
            "intervaloMinimoSeguro"} <= set(body["projecao"])
    assert bb.spot_intervalo_s() != 600 or bb.SPOT_INTERVALO_DEFAULT_S == 600

    # POST sem aplicar: só projeta
    r = c.post("/api/obs/brapi/projecao", json={"intervaloS": 900}, headers=h)
    assert r.status_code == 200 and r.json()["aplicado"] is False

    # POST com aplicar: vira o intervalo vigente
    r = c.post("/api/obs/brapi/projecao", json={"intervaloS": 900, "aplicar": True}, headers=h)
    assert r.status_code == 200
    assert r.json()["aplicado"] is True and r.json()["vigenteS"] == 900


def test_portao_de_admin(monkeypatch):
    c = _client(monkeypatch)
    assert c.get("/api/obs/brapi/projecao").status_code == 401
    _admin_token(c)   # primeiro usuário = admin
    r = c.post("/api/auth/register", json={"email": "comum@teste.com",
                                           "password": "senhaboa123"})
    h2 = {"authorization": "Bearer " + r.json()["token"]}
    assert c.get("/api/obs/brapi/projecao", headers=h2).status_code == 403
