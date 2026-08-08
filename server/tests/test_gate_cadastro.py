"""F4 completo (2026-08-02) — portão de cadastro obrigatório POR DOMÍNIO.

O que trava aqui:
  • B3_GATED_HOSTS vazio (default) => NINGUÉM é afetado — Railway URL e iOS
    continuam com o modo convidado intacto (Decisão A original preservada).
  • Host listado + sem sessão válida => 401 em /api/*, EXCETO /api/auth/* e
    /api/health (senão ninguém consegue logar nem o monitoramento funciona).
  • Host listado + sessão válida (Bearer correto) => passa normal.
  • Host NÃO listado (ex.: a URL do Railway) => passa normal mesmo com
    B3_GATED_HOSTS configurado — o portão é POR DOMÍNIO, não global.
  • Cabeçalhos de segurança básicos em toda resposta.

Reimporta `app.main` por teste (monkeypatch de env antes do import) porque
_GATED_HOSTS é lido no import do módulo, não por request. Isolamento em DOIS
níveis, senão este arquivo suja o resto da suíte:
  1. B3_DB_PATH aponta para um SQLite TEMPORÁRIO — sem isto, `db.shared()`
     bate no banco real do dev (foi assim que "e-mail já existe" apareceu:
     o teste registrava de verdade e a 2ª rodada achava o usuário da 1ª).
  2. `_app_main_isolado` restaura o `app.main` ORIGINAL em sys.modules ao
     final de CADA teste — sem isto, o próximo arquivo da suíte que fizer
     `from app.main import app` herdava o módulo reimportado (banco
     temporário já apagado, env já revertido pelo monkeypatch).
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


def _reimporta(monkeypatch, hosts=None):
    if hosts is None:
        monkeypatch.delenv("B3_GATED_HOSTS", raising=False)
    else:
        monkeypatch.setenv("B3_GATED_HOSTS", hosts)
    d = tempfile.mkdtemp(prefix="b3_gate_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _client_com_gate(monkeypatch, hosts):
    return _reimporta(monkeypatch, hosts)


def _client_sem_gate(monkeypatch):
    return _reimporta(monkeypatch, None)


def test_gate_desligado_por_default_nao_afeta_ninguem(monkeypatch):
    c, _ = _client_sem_gate(monkeypatch)
    r = c.get("/api/state", headers={"host": "acamerini.app"})
    assert r.status_code == 200, "sem B3_GATED_HOSTS, até o próprio acamerini.app passa"


def test_host_listado_sem_sessao_e_401(monkeypatch):
    c, _ = _client_com_gate(monkeypatch, "acamerini.app")
    r = c.get("/api/state", headers={"host": "acamerini.app"})
    assert r.status_code == 401
    assert r.json()["code"] == "cadastro_obrigatorio"


def test_host_nao_listado_passa_mesmo_com_gate_ativo(monkeypatch):
    """A URL do Railway e o app iOS não usam esse Host — continuam livres."""
    c, _ = _client_com_gate(monkeypatch, "acamerini.app")
    r = c.get("/api/state", headers={"host": "boris.semente.dev"})
    assert r.status_code == 200


def test_rotas_de_auth_e_health_ficam_fora_do_portao(monkeypatch):
    """Senão ninguém consegue logar no domínio fechado, e o monitoramento
    (Railway healthcheck) não pode exigir sessão de usuário."""
    c, _ = _client_com_gate(monkeypatch, "acamerini.app")
    headers = {"host": "acamerini.app"}
    assert c.get("/api/health", headers=headers).status_code == 200
    r = c.post("/api/auth/login", json={"email": "x@x.com", "password": "errada123"}, headers=headers)
    assert r.status_code in (400, 401)  # rejeita credencial, mas NÃO por cadastro_obrigatorio
    assert r.json().get("detail") != "Cadastro obrigatório neste domínio. Faça login ou crie sua conta."


def test_sessao_valida_passa_no_host_fechado(monkeypatch):
    c, main = _client_com_gate(monkeypatch, "acamerini.app")
    headers = {"host": "acamerini.app"}
    reg = c.post("/api/auth/register", json={"email": "f4@teste.com", "password": "senhaboa123"}, headers=headers)
    assert reg.status_code == 200, reg.text
    token = reg.json()["token"]
    r = c.get("/api/state", headers={**headers, "authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_lista_aceita_multiplos_hosts_e_ignora_espacos(monkeypatch):
    c, _ = _client_com_gate(monkeypatch, " acamerini.app , www.acamerini.app ")
    for h in ("acamerini.app", "www.acamerini.app"):
        assert c.get("/api/state", headers={"host": h}).status_code == 401, h


def test_cabecalhos_de_seguranca_sempre_presentes(monkeypatch):
    c, _ = _client_sem_gate(monkeypatch)
    r = c.get("/api/health")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert "max-age=31536000" in (r.headers.get("strict-transport-security") or "")
