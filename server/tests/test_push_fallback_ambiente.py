"""Push: fallback de ambiente por token (2026-11-18).

O servidor fala com UM host do APNs (APNS_SANDBOX), mas o iPhone com build do
Xcode gera token de sandbox e o do TestFlight/App Store gera de produção.
Antes, BadDeviceToken no host principal descartava o token na hora — o build
do Xcode nunca recebia push com o servidor em produção. Agora o servidor tenta
o outro host antes de descartar.
"""
import asyncio
import os
import tempfile

from app import db
from app import push

PROD = "https://api.push.apple.com"
SANDBOX = "https://api.sandbox.push.apple.com"


class _Resp:
    def __init__(self, status, reason=""):
        self.status_code = status
        self._reason = reason

    def json(self):
        return {"reason": self._reason} if self._reason else {}


class _Cli:
    """Responde por (host, token) e registra as chamadas."""

    def __init__(self, respostas):
        self.respostas = respostas
        self.chamadas = []

    async def post(self, url, headers=None, content=None):
        host, tk = url.split("/3/device/")
        self.chamadas.append((host, tk))
        return self.respostas.get((host, tk), _Resp(400, "BadDeviceToken"))


def _setup(monkeypatch, sandbox=False):
    for k, v in (("APNS_TEAM_ID", "T"), ("APNS_KEY_ID", "K"), ("APNS_AUTH_KEY", "-----BEGIN x"), ("APNS_TOPIC", "com.x")):
        monkeypatch.setenv(k, v)
    if sandbox:
        monkeypatch.setenv("APNS_SANDBOX", "1")
    else:
        monkeypatch.delenv("APNS_SANDBOX", raising=False)
    monkeypatch.setattr(push, "_jwt", lambda: "jwt")
    d = tempfile.mkdtemp(prefix="b3_push_fb_")
    return db.connect(os.path.join(d, "b3_agente.db"))


def _enviar(conn, cli):
    return asyncio.run(push.send_to_user(conn, "u1", "t", "b", client=cli))


def test_token_de_sandbox_entrega_com_servidor_em_producao(monkeypatch):
    conn = _setup(monkeypatch)
    push.register_token(conn, "u1", "tokxcode")
    cli = _Cli({(SANDBOX, "tokxcode"): _Resp(200)})
    r = _enviar(conn, cli)
    assert r["sent"] == 1 and r["detalhes"] == []
    assert cli.chamadas == [(PROD, "tokxcode"), (SANDBOX, "tokxcode")]
    assert push.tokens_for(conn, "u1") == ["tokxcode"]   # não descartou


def test_token_de_producao_entrega_com_servidor_em_sandbox(monkeypatch):
    conn = _setup(monkeypatch, sandbox=True)
    push.register_token(conn, "u1", "tokprod")
    cli = _Cli({(PROD, "tokprod"): _Resp(200)})
    r = _enviar(conn, cli)
    assert r["sent"] == 1
    assert cli.chamadas == [(SANDBOX, "tokprod"), (PROD, "tokprod")]


def test_host_principal_aceita_nao_tenta_o_outro(monkeypatch):
    conn = _setup(monkeypatch)
    push.register_token(conn, "u1", "tokprod")
    cli = _Cli({(PROD, "tokprod"): _Resp(200)})
    assert _enviar(conn, cli)["sent"] == 1
    assert cli.chamadas == [(PROD, "tokprod")]


def test_recusado_nos_dois_descarta_e_diz_os_dois_ambientes(monkeypatch):
    conn = _setup(monkeypatch)
    push.register_token(conn, "u1", "toklixo")
    r = _enviar(conn, _Cli({}))
    assert r["sent"] == 0
    assert "BadDeviceToken" in r["detalhes"][0]
    assert "produção e sandbox" in r["detalhes"][0]
    assert push.tokens_for(conn, "u1") == []


def test_chave_restrita_no_outro_host_reporta_o_motivo_real(monkeypatch):
    # Chave restrita a produção: sandbox responde BadEnvironmentKeyInToken.
    # O motivo útil é esse (problema da chave), e o token ainda é descartado
    # porque produção já o recusou como BadDeviceToken.
    conn = _setup(monkeypatch)
    push.register_token(conn, "u1", "tokxcode")
    cli = _Cli({(SANDBOX, "tokxcode"): _Resp(403, "BadEnvironmentKeyInToken")})
    r = _enviar(conn, cli)
    assert r["sent"] == 0
    assert "BadEnvironmentKeyInToken" in r["detalhes"][0]


def test_outros_motivos_nao_disparam_fallback(monkeypatch):
    conn = _setup(monkeypatch)
    push.register_token(conn, "u1", "tokvelho")
    cli = _Cli({(PROD, "tokvelho"): _Resp(410, "Unregistered")})
    r = _enviar(conn, cli)
    assert cli.chamadas == [(PROD, "tokvelho")]
    assert "Unregistered" in r["detalhes"][0]
    assert push.tokens_for(conn, "u1") == []
