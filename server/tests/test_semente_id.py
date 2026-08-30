"""Fase 4 do ADR-23 — Boris+ como relying party do portal semente.id.

O que estes testes protegem:
  - `configurado()` reflete a presença das DUAS variáveis (client_id + secret);
  - `iniciar_login` monta a URL de authorize com PKCE S256 completo e grava
    o fluxo (code_verifier, nonce, destino) — nada disso trafega pro cliente
    fora do que a URL já expõe (state, nonce, code_challenge);
  - `concluir_login` valida o id_token por ASSINATURA (JWKS do portal),
    issuer, audience, exp e nonce — cada trava falhando isoladamente;
  - o `state` é de USO ÚNICO, inclusive quando o portal recusou
    (`error=access_denied` consome o fluxo, não deixa reentrada);
  - `SEMENTE_ID_EMAIL_DONO` é a segunda trava (comparação case-insensitive);
  - falha do `/token` nunca eco o client_secret na mensagem de erro.

Offline por natureza: o id_token é assinado por uma chave RSA gerada em
memória (nunca a chave real do portal) e `httpx.AsyncClient` é substituído
por um fake que nunca toca a rede — mesmo padrão de
`server/tests/test_mydata_client.py`.
"""
import asyncio
import json
import os
import tempfile
import time
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from app import db, semente_id

CLIENT_ID = "boris-teste"
PORTAL = "https://id.semente.dev"


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_semente_id_")
    return db.connect(os.path.join(d, "b3.db"))


@pytest.fixture()
def env_semente_id(monkeypatch):
    monkeypatch.setenv("SEMENTE_ID_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("SEMENTE_ID_CLIENT_SECRET", "segredo-teste")
    monkeypatch.setenv("SEMENTE_ID_URL", PORTAL)
    monkeypatch.setenv("SEMENTE_ID_REDIRECT_BASE", "https://boris.semente.dev")
    monkeypatch.delenv("SEMENTE_ID_EMAIL_DONO", raising=False)


@pytest.fixture()
def chave_portal():
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
    """Substitui `httpx.AsyncClient` — a ÚNICA fronteira de rede do módulo
    `semente_id`. Nunca toca a rede real."""

    _JWKS = None
    _TOKEN_STATUS = 200
    _ID_TOKEN = ""
    CHAMADAS = []

    def __init__(self, timeout=None):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url):
        _FakeAsyncClient.CHAMADAS.append(("GET", url))
        return _FakeResposta(200, _FakeAsyncClient._JWKS)

    async def post(self, url, data=None):
        _FakeAsyncClient.CHAMADAS.append(("POST", url, data))
        return _FakeResposta(_FakeAsyncClient._TOKEN_STATUS, {"id_token": _FakeAsyncClient._ID_TOKEN})


def _mock_portal(monkeypatch, chave, id_token, status_token=200, kid="k1"):
    _FakeAsyncClient._JWKS = _jwks(chave, kid=kid)
    _FakeAsyncClient._TOKEN_STATUS = status_token
    _FakeAsyncClient._ID_TOKEN = id_token
    _FakeAsyncClient.CHAMADAS = []
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)


# ---------------------------------------------------------------------------
# configurado()
# ---------------------------------------------------------------------------
def test_sem_client_id_e_secret_nao_esta_configurado(monkeypatch):
    monkeypatch.delenv("SEMENTE_ID_CLIENT_ID", raising=False)
    monkeypatch.delenv("SEMENTE_ID_CLIENT_SECRET", raising=False)
    assert semente_id.configurado() is False


def test_com_as_duas_variaveis_esta_configurado(env_semente_id):
    assert semente_id.configurado() is True


# ---------------------------------------------------------------------------
# iniciar_login — PKCE de ponta, state gravado
# ---------------------------------------------------------------------------
def test_iniciar_login_monta_url_com_pkce_e_grava_o_fluxo(env_semente_id):
    conn = _fresh_db()
    url = semente_id.iniciar_login(conn, "/admin/")
    q = parse_qs(urlparse(url).query)
    assert q["client_id"] == [CLIENT_ID]
    assert q["response_type"] == ["code"]
    assert q["scope"] == ["openid email profile"]
    assert q["code_challenge_method"] == ["S256"]
    assert "code_challenge" in q and "state" in q and "nonce" in q
    # redirect_uri é montado num único lugar e usado idêntico depois
    assert q["redirect_uri"] == ["https://boris.semente.dev/api/auth/semente-id/callback"]

    linha = db.semente_id_flow_get(conn, q["state"][0])
    assert linha is not None
    assert linha["destino"] == "/admin/"
    assert linha["nonce"] == q["nonce"][0]


# ---------------------------------------------------------------------------
# concluir_login — o ciclo completo
# ---------------------------------------------------------------------------
def test_concluir_login_feliz_devolve_sub_email_destino(env_semente_id, chave_portal, monkeypatch):
    conn = _fresh_db()
    url = semente_id.iniciar_login(conn, "/admin/")
    q = parse_qs(urlparse(url).query)
    state, nonce = q["state"][0], q["nonce"][0]
    _mock_portal(monkeypatch, chave_portal, _id_token(chave_portal, nonce=nonce, sub="conta-1"))

    sub, email, destino = asyncio.run(semente_id.concluir_login(conn, state, "code-falso", None))
    assert sub == "conta-1"
    assert email == "alex@example.com"
    assert destino == "/admin/"

    # state é de uso único
    assert db.semente_id_flow_get(conn, state) is None


def test_state_desconhecido_falha(env_semente_id):
    conn = _fresh_db()
    with pytest.raises(semente_id.ErroSementeId):
        asyncio.run(semente_id.concluir_login(conn, "inventado", "code", None))


def test_erro_do_portal_consome_o_fluxo_e_falha(env_semente_id):
    conn = _fresh_db()
    url = semente_id.iniciar_login(conn, "/admin/")
    state = parse_qs(urlparse(url).query)["state"][0]
    with pytest.raises(semente_id.ErroSementeId):
        asyncio.run(semente_id.concluir_login(conn, state, None, "access_denied"))
    # consumido mesmo em erro — sem segunda tentativa com o mesmo state
    assert db.semente_id_flow_get(conn, state) is None


def test_nonce_errado_falha(env_semente_id, chave_portal, monkeypatch):
    conn = _fresh_db()
    url = semente_id.iniciar_login(conn, "/admin/")
    state = parse_qs(urlparse(url).query)["state"][0]
    _mock_portal(monkeypatch, chave_portal, _id_token(chave_portal, nonce="outro-nonce"))
    with pytest.raises(semente_id.ErroSementeId):
        asyncio.run(semente_id.concluir_login(conn, state, "code-falso", None))


def test_issuer_diferente_falha(env_semente_id, chave_portal, monkeypatch):
    conn = _fresh_db()
    url = semente_id.iniciar_login(conn, "/admin/")
    q = parse_qs(urlparse(url).query)
    _mock_portal(monkeypatch, chave_portal, _id_token(chave_portal, nonce=q["nonce"][0], iss="https://mal.example"))
    with pytest.raises(semente_id.ErroSementeId):
        asyncio.run(semente_id.concluir_login(conn, q["state"][0], "code-falso", None))


def test_audience_diferente_falha(env_semente_id, chave_portal, monkeypatch):
    conn = _fresh_db()
    url = semente_id.iniciar_login(conn, "/admin/")
    q = parse_qs(urlparse(url).query)
    _mock_portal(monkeypatch, chave_portal, _id_token(chave_portal, nonce=q["nonce"][0], aud="outro-client"))
    with pytest.raises(semente_id.ErroSementeId):
        asyncio.run(semente_id.concluir_login(conn, q["state"][0], "code-falso", None))


def test_id_token_expirado_falha(env_semente_id, chave_portal, monkeypatch):
    conn = _fresh_db()
    url = semente_id.iniciar_login(conn, "/admin/")
    q = parse_qs(urlparse(url).query)
    passado = int(time.time()) - 1000
    _mock_portal(monkeypatch, chave_portal, _id_token(chave_portal, nonce=q["nonce"][0], iat=passado - 600, exp=passado))
    with pytest.raises(semente_id.ErroSementeId):
        asyncio.run(semente_id.concluir_login(conn, q["state"][0], "code-falso", None))


def test_email_nao_verificado_falha(env_semente_id, chave_portal, monkeypatch):
    conn = _fresh_db()
    url = semente_id.iniciar_login(conn, "/admin/")
    q = parse_qs(urlparse(url).query)
    _mock_portal(monkeypatch, chave_portal, _id_token(chave_portal, nonce=q["nonce"][0], email_verified=False))
    with pytest.raises(semente_id.ErroSementeId):
        asyncio.run(semente_id.concluir_login(conn, q["state"][0], "code-falso", None))


def test_email_dono_restringe_quando_definido(env_semente_id, chave_portal, monkeypatch):
    monkeypatch.setenv("SEMENTE_ID_EMAIL_DONO", "outro@example.com")
    conn = _fresh_db()
    url = semente_id.iniciar_login(conn, "/admin/")
    q = parse_qs(urlparse(url).query)
    _mock_portal(monkeypatch, chave_portal, _id_token(chave_portal, nonce=q["nonce"][0]))
    with pytest.raises(semente_id.ErroSementeId):
        asyncio.run(semente_id.concluir_login(conn, q["state"][0], "code-falso", None))


def test_email_dono_deixa_passar_case_insensitive(env_semente_id, chave_portal, monkeypatch):
    monkeypatch.setenv("SEMENTE_ID_EMAIL_DONO", "Alex@Example.com")
    conn = _fresh_db()
    url = semente_id.iniciar_login(conn, "/admin/")
    q = parse_qs(urlparse(url).query)
    _mock_portal(monkeypatch, chave_portal, _id_token(chave_portal, nonce=q["nonce"][0]))
    sub, email, _ = asyncio.run(semente_id.concluir_login(conn, q["state"][0], "code-falso", None))
    assert email == "alex@example.com"
    assert sub == "conta-1"


def test_token_endpoint_recusado_falha_sem_expor_secret(env_semente_id, chave_portal, monkeypatch):
    conn = _fresh_db()
    url = semente_id.iniciar_login(conn, "/admin/")
    q = parse_qs(urlparse(url).query)
    _mock_portal(monkeypatch, chave_portal, _id_token(chave_portal, nonce=q["nonce"][0]), status_token=400)
    with pytest.raises(semente_id.ErroSementeId) as exc:
        asyncio.run(semente_id.concluir_login(conn, q["state"][0], "code-falso", None))
    assert "segredo-teste" not in str(exc.value)
