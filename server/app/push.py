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
                    detalhes.append(f"{tk[:10]}…: HTTP {r.status_code} {reason}".strip())
                    if reason in ("BadDeviceToken", "Unregistered") and tk in keep:
                        keep.remove(tk)
            except Exception as e:  # noqa: BLE001 — push é best-effort
                detalhes.append(f"{tk[:10]}…: erro de rede ({e})")
    if keep != toks:
        db.kv_set(conn, "pushTokens", keep, user_id=user_id)
    return {"sent": sent, "total": len(toks), "detalhes": detalhes}
