"""FASE 3.3b — Push (APNs) para as ações do agente. Sub-fase condicionada à
conta Apple Developer PAGA (confirmada pelo Alex). No-op se não configurado.

Env necessárias (Railway → Variables):
  APNS_TEAM_ID    — Team ID da conta Apple Developer
  APNS_KEY_ID     — Key ID da chave de push (.p8)
  APNS_AUTH_KEY   — conteúdo do .p8 (colar o PEM inteiro) OU caminho do arquivo
  APNS_TOPIC      — bundle id do app (ex.: com.bolsia.app)
  APNS_SANDBOX    — "1" para o ambiente de desenvolvimento (TestFlight usa produção)

Tokens de aparelho ficam na seção kv `pushTokens` por usuário (cap 5,
registrados via POST /api/push/register-token). Ver APNS-PUSH.md para o
passo a passo (chave no portal, capability no Xcode, plugin no app).
"""
import json
import os
import time
from typing import Optional

from . import db

_JWT_CACHE = {"token": None, "at": 0.0}


def is_configured() -> bool:
    return all(os.environ.get(k) for k in ("APNS_TEAM_ID", "APNS_KEY_ID", "APNS_AUTH_KEY", "APNS_TOPIC"))


def _auth_key() -> str:
    raw = os.environ.get("APNS_AUTH_KEY") or ""
    if raw.strip().startswith("-----BEGIN"):
        return raw
    try:
        with open(raw, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return raw


def _jwt() -> str:
    """JWT ES256 do APNs, cacheado por ~45min (Apple aceita até 60)."""
    now = time.time()
    if _JWT_CACHE["token"] and now - _JWT_CACHE["at"] < 45 * 60:
        return _JWT_CACHE["token"]
    import jwt  # PyJWT[crypto] — já nas requirements
    token = jwt.encode(
        {"iss": os.environ["APNS_TEAM_ID"], "iat": int(now)},
        _auth_key(),
        algorithm="ES256",
        headers={"kid": os.environ["APNS_KEY_ID"]},
    )
    _JWT_CACHE.update(token=token, at=now)
    return token


def _host() -> str:
    return "https://api.sandbox.push.apple.com" if os.environ.get("APNS_SANDBOX") == "1" else "https://api.push.apple.com"


# ------------------------- tokens por usuário (kv) -------------------------
def register_token(conn, user_id: str, token: str) -> list:
    toks = db.kv_get(conn, "pushTokens", [], user_id=user_id) or []
    token = (token or "").strip()
    if token and token not in toks:
        toks = (toks + [token])[-5:]
        db.kv_set(conn, "pushTokens", toks, user_id=user_id)
    return toks


def tokens_for(conn, user_id: str) -> list:
    return db.kv_get(conn, "pushTokens", [], user_id=user_id) or []


# --------------------------------- envio -----------------------------------
# FASE 6 (fix 5): tradutor dos `reason` do APNs em instrução EXATA (pt-BR).
# O caso que motivou: BadEnvironmentKeyInToken — a chave .p8 foi criada no
# portal Apple RESTRITA a um ambiente (Development ou Production) e o servidor
# está falando com o host do outro ambiente. Não é problema do token do
# aparelho: trocar APNS_SANDBOX ou gerar chave sem restrição resolve.
_REASON_HELP = {
    "BadEnvironmentKeyInToken": (
        "a chave .p8 (APNS_AUTH_KEY) é RESTRITA a um ambiente e não bate com o host em uso. "
        "Corrija no portal Apple (Keys → sua chave APNs → Environment: 'Sandbox & Production') "
        "OU alinhe APNS_SANDBOX no Railway: 1 = build do Xcode (sandbox); remova a variável = TestFlight/App Store (produção)."
    ),
    "BadDeviceToken": (
        "o token deste aparelho pertence ao OUTRO ambiente (build do Xcode gera token de sandbox; "
        "TestFlight/App Store gera de produção). Alinhe APNS_SANDBOX e toque de novo em 'Ativar push neste aparelho' — o token inválido foi descartado."
    ),
    "Unregistered": "o aparelho removeu o app ou o token expirou — token descartado; reative o push no aparelho.",
    "DeviceTokenNotForTopic": "o token não pertence a este app (APNS_TOPIC) — token descartado; confira o bundle id e reative o push.",
    "BadTopic": "APNS_TOPIC inválido — deve ser exatamente o bundle id do app (com.alexandrecamerini.bolsia).",
    "TopicDisallowed": "a chave APNs não tem direito sobre este APNS_TOPIC — confira o App ID no portal Apple.",
    "InvalidProviderToken": "APNS_TEAM_ID / APNS_KEY_ID / APNS_AUTH_KEY não batem entre si — confira os três no Railway com os valores do portal Apple.",
    "ExpiredProviderToken": "JWT do provedor expirado — transitório; se persistir, confira o relógio do servidor.",
    "MissingTopic": "faltou APNS_TOPIC no Railway.",
}
# reasons que INVALIDAM o token do aparelho (aí sim descartamos):
_DROP_TOKEN_REASONS = ("BadDeviceToken", "Unregistered", "DeviceTokenNotForTopic")


def explain_reason(reason: str) -> str:
    """Instrução acionável para um reason do APNs ('' se desconhecido)."""
    return _REASON_HELP.get((reason or "").strip(), "")


def env_label() -> str:
    return "sandbox (APNS_SANDBOX=1)" if os.environ.get("APNS_SANDBOX") == "1" else "produção"
async def send_to_user(conn, user_id: str, title: str, body: str) -> dict:
    """Envia o push a todos os aparelhos do usuário.

    FASE 3 (observabilidade do push): devolve um DIAGNÓSTICO completo, não
    mais um int — quem chama (main.py) precisa distinguir "não configurado"
    de "sem token" de "token(s) rejeitado(s)" para logar (e mostrar) o motivo
    certo, em vez da mensagem genérica que escondia qual dos três era.
    {"sent": int, "total": int, "detalhes": [str, ...]}
    """
    if not is_configured():
        return {"sent": 0, "total": 0, "detalhes": ["APNs não configurado no servidor (variáveis do Railway ausentes)"]}
    toks = tokens_for(conn, user_id)
    if not toks:
        return {"sent": 0, "total": 0, "detalhes": []}
    import httpx
    payload = {"aps": {"alert": {"title": title, "body": body}, "sound": "default"}}
    sent = 0
    keep = list(toks)
    detalhes = []
    async with httpx.AsyncClient(http2=True, timeout=10) as client:
        for tk in toks:
            try:
                r = await client.post(
                    _host() + "/3/device/" + tk,
                    headers={
                        "authorization": "bearer " + _jwt(),
                        "apns-topic": os.environ["APNS_TOPIC"],
                        "apns-push-type": "alert",
                        "apns-priority": "10",
                    },
                    content=json.dumps(payload),
                )
                if r.status_code == 200:
                    sent += 1
                else:
                    try:
                        reason = (r.json() or {}).get("reason", "")
                    except Exception:  # noqa: BLE001
                        reason = ""
                    # FASE 6 (fix 5): reason cru + ambiente em uso + instrução exata
                    ajuda = explain_reason(reason)
                    detalhes.append(
                        (f"{tk[:10]}…: HTTP {r.status_code} {reason} [ambiente: {env_label()}]"
                         + (f" → {ajuda}" if ajuda else "")).strip()
                    )
                    if reason in _DROP_TOKEN_REASONS and tk in keep:
                        keep.remove(tk)
            except Exception as e:  # noqa: BLE001 — push é best-effort
                detalhes.append(f"{tk[:10]}…: erro de rede ({e})")
    if keep != toks:
        db.kv_set(conn, "pushTokens", keep, user_id=user_id)
    return {"sent": sent, "total": len(toks), "detalhes": detalhes}
