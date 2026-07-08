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


def test_senha_gigante_e_rejeitada():
    # FASE 5 (lançamento): PBKDF2 (240k iterações) sobre senha arbitrariamente
    # longa é DoS barato. Registro rejeita; verify devolve False SEM computar.
    try:
        auth.hash_password("x" * 5000)
        assert False
    except auth.AuthError as e:
        assert "máximo" in str(e)
    h = auth.hash_password("senha-normal-123")
    assert auth.verify_password("x" * 5000, h) is False


def test_throttle_de_login():
    # FASE 5 (lançamento): freio de força bruta por (ip, e-mail) — janela
    # deslizante. Falhas contam; sucesso limpa; janela expira sozinha.
    auth.throttle_reset()
    k = auth.throttle_key("1.2.3.4", "alvo@x.com")
    t0 = 1000.0
    for i in range(auth._RL_MAX):
        auth.throttle_check(k, now=t0 + i)   # ainda dentro do limite
        auth.throttle_fail(k, now=t0 + i)
    try:
        auth.throttle_check(k, now=t0 + auth._RL_MAX)
        assert False, "deveria ter travado após o limite de falhas"
    except auth.AuthError as e:
        assert "tentativas" in str(e).lower()
    # outra chave (outro e-mail/ip) não é afetada
    auth.throttle_check(auth.throttle_key("1.2.3.4", "outro@x.com"), now=t0)
    # a janela expira: mesmas falhas, muito depois => liberado
    auth.throttle_check(k, now=t0 + auth._RL_WINDOW + 61)
    # sucesso limpa o contador
    auth.throttle_fail(k, now=t0)
    auth.throttle_clear(k)
    auth.throttle_check(k, now=t0 + 1)
    auth.throttle_reset()


def test_aud_em_lista_e_peek():
    # FASE 8 (A2): env aceita lista separada por vírgula (bundle id + Services
    # ID); _peek_aud lê o aud do token SEM validar (só para a mensagem de erro).
    assert auth._aud_list("com.alexandrecamerini.bolsia") == ["com.alexandrecamerini.bolsia"]
    assert auth._aud_list(" a.b.c , d.e.f ,") == ["a.b.c", "d.e.f"]
    assert auth._aud_list("") == [] and auth._aud_list(None) == []
    import base64
    import json as _json
    payload = base64.urlsafe_b64encode(_json.dumps({"aud": "com.alexandrecamerini.bolsia"}).encode()).decode().rstrip("=")
    assert auth._peek_aud("h." + payload + ".s") == "com.alexandrecamerini.bolsia"
    assert auth._peek_aud("token-invalido") == "?"


def test_oauth_sem_env_menciona_bundle_id_e_lista():
    os.environ.pop("APPLE_CLIENT_ID", None)
    try:
        auth.verify_oauth_token("apple", "x.y.z")
        assert False
    except auth.AuthError as e:
        msg = str(e)
        assert "bundle id" in msg and "vírgula" in msg


def test_oauth_atualiza_email_ao_recompartilhar():
    # FASE 8B (R5): usuário entrou com "Ocultar e-mail" (relay); depois refez o
    # consentimento compartilhando o e-mail REAL — o novo login atualiza a conta.
    conn, _ = _fresh_db()
    u1 = auth.upsert_oauth_user(conn, "apple", "sub-relay", "abc123@privaterelay.appleid.com", "Alex")
    assert "privaterelay" in (u1["email"] or "")
    u2 = auth.upsert_oauth_user(conn, "apple", "sub-relay", "alex@exemplo.com", None)
    assert u2["id"] == u1["id"]
    assert u2["email"] == "alex@exemplo.com"
    # colisão com e-mail de outra conta => mantém o atual (UNIQUE preservado)
    auth.register_email(conn, "ocupado@exemplo.com", "senha-forte-1")
    u3 = auth.upsert_oauth_user(conn, "apple", "sub-relay", "ocupado@exemplo.com", None)
    assert u3["email"] == "alex@exemplo.com"


def test_purga_de_sessoes_expiradas():
    conn, _ = _fresh_db()
    u = auth.register_email(conn, "purge@x.com", "senha-purge-1")
    viva = auth.create_session(conn, u["id"])            # 90 dias
    morta = auth.create_session(conn, u["id"], ttl_days=-1)  # já expirada
    n = auth.purge_expired_sessions(conn)
    assert n == 1
    assert auth.resolve_session(conn, viva) is not None
    assert db.get_session(conn, morta) is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE AUTH PASSARAM")
