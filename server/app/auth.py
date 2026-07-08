"""Autenticação multiusuário (FASE 2).

Decisões travadas relevantes:
  - A (identidade): local-first, conta OPCIONAL. Sem token => escopo anônimo
    (kv global/legado). Com token => escopo por user_id.
  - D (BYOK): intacto. Auth não toca no fluxo BYOK; a chave do usuário continua
    no `config` (server-side por usuário quando logado; no aparelho no iOS).

Este módulo é STDLIB-ONLY no caminho e-mail/senha + sessões (testável offline,
sem FastAPI nem rede). A verificação de ID token de Apple/Google é um caminho
PARALELO, opcional, que só carrega PyJWT/rede quando de fato acionado — assim a
ausência da dependência nunca quebra o boot nem as suítes.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import re
import secrets

from . import db

# PBKDF2-HMAC-SHA256. Iterações altas o suficiente para 2026, formato
# auto-descritivo para permitir migração futura sem reescrever o verificador.
_PBKDF2_ITER = 240_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SESSION_TTL_DAYS = int(os.environ.get("B3_SESSION_TTL_DAYS", "90"))


class AuthError(Exception):
    """Erro de autenticação com mensagem segura para o cliente (sem vazar se o
    e-mail existe ou não em falhas de login)."""


# ------------------------------- senhas -------------------------------------
# FASE 5 (lançamento): teto de tamanho. PBKDF2 com 240k iterações sobre uma
# senha arbitrariamente longa é um vetor de DoS barato (CPU no servidor).
_PASSWORD_MAX = 128


def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 8:
        raise AuthError("A senha precisa ter ao menos 8 caracteres.")
    if len(password) > _PASSWORD_MAX:
        raise AuthError("A senha pode ter no máximo %d caracteres." % _PASSWORD_MAX)
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITER)
    return "pbkdf2_sha256$%d$%s$%s" % (_PBKDF2_ITER, salt.hex(), dk.hex())


def verify_password(password: str, stored: str) -> bool:
    if isinstance(password, str) and len(password) > _PASSWORD_MAX:
        return False  # nunca gasta PBKDF2 com entrada gigante (DoS)
    try:
        algo, iter_s, salt_hex, hash_hex = (stored or "").split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), bytes.fromhex(salt_hex), int(iter_s))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


# ------------------------------- ids/tokens ---------------------------------
def new_user_id() -> str:
    return secrets.token_hex(16)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


# ----------------------------- e-mail / senha -------------------------------
def normalize_email(email: str) -> str:
    e = (email or "").strip().lower()
    if not _EMAIL_RE.match(e):
        raise AuthError("Informe um e-mail válido.")
    return e


def register_email(conn, email: str, password: str, name: str = "") -> dict:
    e = normalize_email(email)
    if db.get_user_by_email(conn, e):
        raise AuthError("Já existe uma conta com este e-mail.")
    user = {
        "id": new_user_id(),
        "email": e,
        "provider": "email",
        "provider_sub": None,
        "pass_hash": hash_password(password),
        "name": (name or "").strip()[:40] or None,
        "created_at": _iso(_now()),
    }
    db.insert_user(conn, user)
    return db.get_user_by_id(conn, user["id"])


def login_email(conn, email: str, password: str) -> dict:
    e = normalize_email(email)
    u = db.get_user_by_email(conn, e)
    # Mensagem genérica nos dois ramos: não revela se o e-mail existe.
    if not u or not u.get("pass_hash") or not verify_password(password, u["pass_hash"]):
        raise AuthError("E-mail ou senha incorretos.")
    return db.get_user_by_id(conn, u["id"])


# ------------------------------- sessões ------------------------------------
def create_session(conn, user_id: str, ttl_days: int = None) -> str:
    ttl = _SESSION_TTL_DAYS if ttl_days is None else ttl_days
    token = new_session_token()
    now = _now()
    db.insert_session(conn, token, user_id, _iso(now), _iso(now + timedelta(days=ttl)))
    return token


def resolve_session(conn, token: str):
    """Devolve o user dict do token ou None. Sessão expirada é apagada (lazy)."""
    if not token:
        return None
    s = db.get_session(conn, token)
    if not s:
        return None
    try:
        exp = datetime.fromisoformat(s["expires_at"])
    except (ValueError, TypeError):
        exp = None
    if exp is not None and exp < _now():
        db.delete_session(conn, token)
        return None
    return db.get_user_by_id(conn, s["user_id"])


def revoke_session(conn, token: str) -> None:
    db.delete_session(conn, token)


def purge_expired_sessions(conn) -> int:
    """FASE 5 (lançamento): remove sessões vencidas em lote. O resolve_session
    já apaga a sessão consultada quando expirada (lazy), mas tokens nunca mais
    usados ficariam para sempre na tabela. Chamado pelo scheduler diário e no
    boot; devolve quantas linhas saíram (vai para o log de observabilidade)."""
    cur = conn.execute("DELETE FROM sessions WHERE expires_at < ?", (_iso(_now()),))
    conn.commit()
    return cur.rowcount


# --------------------------- rate limit (login) ------------------------------
# FASE 5 (lançamento): freio de força bruta nas rotas de autenticação, em
# memória por processo (stdlib; espelha o padrão do metering). Janela deslizante
# por chave (ip + e-mail): até _RL_MAX tentativas FALHAS por _RL_WINDOW s.
# Sucesso limpa a chave (não pune quem errou a senha 2x e acertou na 3ª).
_RL_MAX = int(os.environ.get("B3_AUTH_RL_MAX", "10"))
_RL_WINDOW = float(os.environ.get("B3_AUTH_RL_WINDOW_S", "900"))  # 15 min
_rl_attempts: dict = {}  # key -> [timestamps de FALHA]


def throttle_key(ip: str, email: str = "") -> str:
    return (ip or "?") + "|" + (email or "").strip().lower()


def throttle_check(key: str, now: float = None) -> None:
    """Levanta AuthError se a chave estourou o limite. Chamar ANTES de validar."""
    import time as _t
    t = now if now is not None else _t.time()
    hits = [x for x in _rl_attempts.get(key, []) if t - x < _RL_WINDOW]
    _rl_attempts[key] = hits
    if len(hits) >= _RL_MAX:
        espera = int(max(1, _RL_WINDOW - (t - hits[0])))
        raise AuthError("Muitas tentativas de login. Aguarde %d min e tente de novo." % max(1, espera // 60))
    # higiene: não deixa o dict crescer sem fim (chaves velhas sem hits saem)
    if len(_rl_attempts) > 10000:
        for k in [k for k, v in _rl_attempts.items() if not v][:5000]:
            _rl_attempts.pop(k, None)


def throttle_fail(key: str, now: float = None) -> None:
    """Registra uma tentativa FALHA (chamar no except das rotas de auth)."""
    import time as _t
    t = now if now is not None else _t.time()
    _rl_attempts.setdefault(key, []).append(t)


def throttle_clear(key: str) -> None:
    """Sucesso: zera o contador da chave."""
    _rl_attempts.pop(key, None)


def throttle_reset() -> None:
    """Para testes."""
    _rl_attempts.clear()


# --------------------------- OAuth (Apple/Google) ---------------------------
# Caminho paralelo e opcional. A verificação real do ID token exige PyJWT[crypto]
# (assinatura RS256/ES256 + JWKS) e rede. Importado tarde e guardado: a ausência
# da dependência só afeta quem tentar logar por Apple/Google, com erro acionável.
_OIDC = {
    "google": {
        "iss": ("https://accounts.google.com", "accounts.google.com"),
        "jwks": "https://www.googleapis.com/oauth2/v3/certs",
        "aud_env": "GOOGLE_CLIENT_ID",
    },
    "apple": {
        "iss": ("https://appleid.apple.com",),
        "jwks": "https://appleid.apple.com/auth/keys",
        "aud_env": "APPLE_CLIENT_ID",
    },
}


def verify_oauth_token(provider: str, id_token: str) -> dict:
    """Valida um ID token OIDC e devolve {sub, email, name}. Levanta AuthError
    com mensagem acionável se a dependência/configuração não estiver presente."""
    cfg = _OIDC.get(provider)
    if not cfg:
        raise AuthError("Provedor não suportado: " + str(provider))
    aud = os.environ.get(cfg["aud_env"])
    if not aud:
        raise AuthError(
            "Login " + provider + " não configurado no servidor "
            "(defina " + cfg["aud_env"] + " com o client_id do app)."
        )
    try:
        import jwt  # PyJWT
        from jwt import PyJWKClient
    except ImportError:
        raise AuthError(
            "Login " + provider + " indisponível: o servidor precisa de "
            "'PyJWT[crypto]' instalado (adicione a requirements e redeploy)."
        )
    try:
        signing_key = PyJWKClient(cfg["jwks"]).get_signing_key_from_jwt(id_token).key
        claims = jwt.decode(
            id_token,
            signing_key,
            algorithms=["RS256", "ES256"],
            audience=aud,
            issuer=list(cfg["iss"]) if len(cfg["iss"]) > 1 else cfg["iss"][0],
            options={"require": ["exp", "iss", "sub"]},
        )
    except Exception as e:  # noqa: BLE001 — mensagem segura ao cliente
        raise AuthError("Não foi possível validar o login " + provider + ": " + str(e))
    return {
        "sub": claims.get("sub"),
        "email": (claims.get("email") or "").strip().lower() or None,
        "name": claims.get("name") or claims.get("given_name") or None,
    }


def upsert_oauth_user(conn, provider: str, sub: str, email: str = None, name: str = None) -> dict:
    """Encontra-ou-cria o usuário do provedor (idempotente por (provider, sub))."""
    existing = db.get_user_by_provider(conn, provider, sub)
    if existing:
        return existing
    e = (email or "").strip().lower() or None
    # Evita colisão de UNIQUE(email) se o mesmo e-mail já existe por outro meio:
    # nesse caso, registra a conta OAuth sem e-mail (vínculo por (provider,sub)).
    if e and db.get_user_by_email(conn, e):
        e = None
    user = {
        "id": new_user_id(),
        "email": e,
        "provider": provider,
        "provider_sub": sub,
        "pass_hash": None,
        "name": (name or "").strip()[:40] or None if name else None,
        "created_at": _iso(_now()),
    }
    db.insert_user(conn, user)
    return db.get_user_by_id(conn, user["id"])
