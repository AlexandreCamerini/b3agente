"""Fase 4 do ADR-23 — ida e volta HTTP do relying party semente.id.

O que estes testes protegem, exercitando a ROTA real (não só a função):
  - `/inicio` redireciona ao portal com PKCE completo (302), e SEM
    configuração responde 503 acionável (nunca 500, nunca redirect);
  - `/callback` com code/state válidos e conta ADMIN devolve 302 pro
    handoff (`/admin/#handoff=<código>`), que troca por sessão plena com
    `permissions` não vazio via /api/admin/mobile-handoff/exchange — o MESMO
    endpoint que o app nativo já usa (ADR-014), sem caminho de troca novo;
  - conta do portal SEM papel administrativo não recebe handoff (redirect
    para /admin/ sem hash, nenhuma sessão plena nasce);
  - regressão explícita: /api/auth/login e /api/auth/oauth respondem
    exatamente como antes (o portal SOMA um caminho, não substitui).

Isolamento e fixtures no molde de test_adr014_mobile_handoff.py. id_token
assinado por chave RSA gerada em memória; `httpx.AsyncClient` é o único
ponto de rede, sempre um fake — zero rede real, inclusive nesta suíte HTTP.
"""
import importlib
import json
import os
import sys
import tempfile
import time
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

CLIENT_ID = "boris-teste-http"
PORTAL = "https://id.semente.dev"


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


def _client(monkeypatch, com_portal_configurado=True):
    monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    if com_portal_configurado:
        monkeypatch.setenv("SEMENTE_ID_CLIENT_ID", CLIENT_ID)
        monkeypatch.setenv("SEMENTE_ID_CLIENT_SECRET", "segredo-teste")
        monkeypatch.setenv("SEMENTE_ID_URL", PORTAL)
        monkeypatch.setenv("SEMENTE_ID_REDIRECT_BASE", "https://boris.semente.dev")
    else:
        monkeypatch.delenv("SEMENTE_ID_CLIENT_ID", raising=False)
        monkeypatch.delenv("SEMENTE_ID_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("SEMENTE_ID_EMAIL_DONO", raising=False)
    d = tempfile.mkdtemp(prefix="b3_semente_id_http_")
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


def _chave_portal():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwks(chave, kid="k1"):
    jwk = json.loads(RSAAlgorithm.to_jwk(chave.public_key()))
    jwk["kid"] = kid
    return {"keys": [jwk]}


def _id_token(chave, kid="k1", **extra):
    agora = int(time.time())
    claims = {
        "iss": PORTAL, "sub": "conta-1", "aud": CLIENT_ID,
        "iat": agora, "exp": agora + 600,
        "email": "alex@example.com", "email_verified": True,
    }
    claims.update(extra)
    return jwt.encode(claims, chave, algorithm="RS256", headers={"kid": kid})


class _FakeResposta:
    def __init__(self, status_code=200, json_body=None):
        self.status_code = status_code
        self._json_body = json_body if json_body is not None else {}

    def json(self):
        return self._json_body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("erro", request=None, response=self)


class _FakeAsyncClient:
    _JWKS = None
    _ID_TOKEN = ""

    def __init__(self, timeout=None):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url):
        return _FakeResposta(200, _FakeAsyncClient._JWKS)

    async def post(self, url, data=None):
        return _FakeResposta(200, {"id_token": _FakeAsyncClient._ID_TOKEN})


def _mock_portal(monkeypatch, chave, id_token):
    _FakeAsyncClient._JWKS = _jwks(chave)
    _FakeAsyncClient._ID_TOKEN = id_token
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)


def test_inicio_sem_configuracao_responde_503_nunca_500_nunca_redirect(monkeypatch):
    c, _ = _client(monkeypatch, com_portal_configurado=False)
    r = c.get("/api/auth/semente-id/inicio", follow_redirects=False)
    assert r.status_code == 503
    assert "SEMENTE_ID" in r.json()["detail"]


def test_inicio_configurado_redireciona_ao_portal_com_pkce(monkeypatch):
    c, _ = _client(monkeypatch)
    r = c.get("/api/auth/semente-id/inicio", follow_redirects=False)
    assert r.status_code == 302
    q = parse_qs(urlparse(r.headers["location"]).query)
    assert q["client_id"] == [CLIENT_ID]
    assert q["code_challenge_method"] == ["S256"]
    assert "state" in q and "nonce" in q


def test_callback_conta_admin_abre_painel_de_ponta_a_ponta(monkeypatch):
    c, main = _client(monkeypatch)
    _registra(c, "dono@teste.com")  # 1º usuário: bootstrap admin

    r = c.get("/api/auth/semente-id/inicio", follow_redirects=False)
    q = parse_qs(urlparse(r.headers["location"]).query)
    state, nonce = q["state"][0], q["nonce"][0]

    chave = _chave_portal()
    _mock_portal(monkeypatch, chave, _id_token(chave, nonce=nonce, email="dono@teste.com", sub="conta-dono"))

    r = c.get(f"/api/auth/semente-id/callback?state={state}&code=x", follow_redirects=False)
    assert r.status_code == 302
    location = r.headers["location"]
    assert location.startswith("/admin/#handoff=")
    codigo = location.split("#handoff=", 1)[1]

    # MESMO endpoint do ADR-014 — sem caminho de troca novo no front.
    r = c.post("/api/admin/mobile-handoff/exchange", json={"codigo": codigo})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token"]
    assert body["user"]["permissions"]  # não vazio


def test_callback_conta_sem_papel_admin_nao_recebe_handoff(monkeypatch):
    c, main = _client(monkeypatch)
    _registra(c, "dono@teste.com")           # 1º usuário: bootstrap admin
    # 2ª conta do portal, e-mail DIFERENTE — nunca logou antes, nasce sem
    # nenhum papel administrativo (mesma regra de qualquer conta comum).

    r = c.get("/api/auth/semente-id/inicio", follow_redirects=False)
    q = parse_qs(urlparse(r.headers["location"]).query)
    state, nonce = q["state"][0], q["nonce"][0]

    chave = _chave_portal()
    _mock_portal(monkeypatch, chave, _id_token(chave, nonce=nonce, email="comum@teste.com", sub="conta-comum"))

    r = c.get(f"/api/auth/semente-id/callback?state={state}&code=x", follow_redirects=False)
    assert r.status_code == 302
    # SEM handoff — a URL não carrega #handoff=
    assert "#handoff=" not in r.headers["location"]


def test_callback_erro_do_portal_nunca_mostra_stack_trace(monkeypatch):
    c, _ = _client(monkeypatch)
    r = c.get("/api/auth/semente-id/inicio", follow_redirects=False)
    state = parse_qs(urlparse(r.headers["location"]).query)["state"][0]
    r = c.get(f"/api/auth/semente-id/callback?state={state}&error=access_denied", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/admin/"


def test_regressao_login_email_senha_intacto(monkeypatch):
    c, _ = _client(monkeypatch)
    r = c.post("/api/auth/register", json={"email": "regressao@teste.com", "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    r = c.post("/api/auth/login", json={"email": "regressao@teste.com", "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    assert r.json()["token"]


def test_regressao_oauth_sem_config_continua_401_nao_500(monkeypatch):
    c, _ = _client(monkeypatch)
    monkeypatch.delenv("APPLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    r = c.post("/api/auth/oauth", json={"provider": "google", "idToken": "qualquer"})
    assert r.status_code == 401
