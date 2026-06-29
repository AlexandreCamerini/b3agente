"""FASE 2 — autenticação: senha (PBKDF2), registro/login e-mail, sessões e
upsert OAuth. Stdlib-only; o caminho Apple/Google é só verificado quanto à
degradação limpa (sem dependência/config não derruba o servidor).

Roda standalone (`python -m tests.test_auth`) e via pytest.
"""
import os
import tempfile

from app import db
from app import auth


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_auth_")
    path = os.path.join(d, "b3_agente.db")
    return db.connect(path), path


def test_hash_de_senha_roundtrip():
    h = auth.hash_password("uma-senha-boa-123")
    assert h.startswith("pbkdf2_sha256$")
    assert auth.verify_password("uma-senha-boa-123", h) is True
    assert auth.verify_password("errada", h) is False
    # mesma senha gera hashes diferentes (salt aleatório)
    assert auth.hash_password("uma-senha-boa-123") != h


def test_senha_curta_e_rejeitada():
    try:
        auth.hash_password("curta")
        assert False, "deveria ter levantado AuthError"
    except auth.AuthError:
        pass


def test_registro_e_login_email():
    conn, _ = _fresh_db()
    u = auth.register_email(conn, "Alex@Example.com ", "senha-forte-123", name="Alex")
    assert u["email"] == "alex@example.com"     # normalizado
    assert u["provider"] == "email"
    assert u["name"] == "Alex"
    # duplicado rejeitado
    try:
        auth.register_email(conn, "alex@example.com", "outra-senha-123")
        assert False
    except auth.AuthError:
        pass
    # login ok
    u2 = auth.login_email(conn, "alex@example.com", "senha-forte-123")
    assert u2["id"] == u["id"]
    # senha errada -> mensagem genérica
    try:
        auth.login_email(conn, "alex@example.com", "errada")
        assert False
    except auth.AuthError as e:
        assert "incorret" in str(e).lower()
    # e-mail inexistente -> MESMA mensagem genérica (não revela existência)
    try:
        auth.login_email(conn, "ninguem@example.com", "qualquer-123")
        assert False
    except auth.AuthError as e:
        assert "incorret" in str(e).lower()
    conn.close()


def test_email_invalido():
    conn, _ = _fresh_db()
    try:
        auth.register_email(conn, "sem-arroba", "senha-forte-123")
        assert False
    except auth.AuthError:
        pass
    conn.close()


def test_sessao_cria_resolve_revoga():
    conn, _ = _fresh_db()
    u = auth.register_email(conn, "s@x.com", "senha-forte-123")
    tok = auth.create_session(conn, u["id"])
    assert isinstance(tok, str) and len(tok) > 20
    who = auth.resolve_session(conn, tok)
    assert who and who["id"] == u["id"]
    auth.revoke_session(conn, tok)
    assert auth.resolve_session(conn, tok) is None
    assert auth.resolve_session(conn, "token-inexistente") is None
    assert auth.resolve_session(conn, "") is None


def test_sessao_expirada_resolve_none():
    conn, _ = _fresh_db()
    u = auth.register_email(conn, "exp@x.com", "senha-forte-123")
    tok = auth.create_session(conn, u["id"], ttl_days=-1)   # já expirada
    assert auth.resolve_session(conn, tok) is None
    # e foi apagada (lazy)
    assert db.get_session(conn, tok) is None


def test_upsert_oauth_idempotente():
    conn, _ = _fresh_db()
    a = auth.upsert_oauth_user(conn, "google", "sub-123", email="g@x.com", name="G")
    b = auth.upsert_oauth_user(conn, "google", "sub-123", email="g@x.com", name="G")
    assert a["id"] == b["id"]               # mesmo (provider, sub) => mesmo user
    assert a["provider"] == "google"
    # mesmo sub em provider diferente => usuário diferente
    c = auth.upsert_oauth_user(conn, "apple", "sub-123", email=None, name=None)
    assert c["id"] != a["id"]
    conn.close()


def test_oauth_sem_config_degrada_limpo():
    # Sem GOOGLE_CLIENT_ID/APPLE_CLIENT_ID no ambiente, verify_oauth_token deve
    # levantar AuthError acionável — NUNCA derrubar o processo.
    os.environ.pop("GOOGLE_CLIENT_ID", None)
    try:
        auth.verify_oauth_token("google", "qualquer.token.jwt")
        assert False
    except auth.AuthError as e:
        assert "configurado" in str(e).lower() or "indisponível" in str(e).lower()
    # provedor desconhecido
    try:
        auth.verify_oauth_token("facebook", "x")
        assert False
    except auth.AuthError:
        pass


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE AUTH PASSARAM")
