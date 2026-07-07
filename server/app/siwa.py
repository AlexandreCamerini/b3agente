"""FASE 4 (Bloco 2) — Sign in with Apple: troca de código e REVOKE de token.

Por quê: a diretriz de exclusão de conta da Apple (5.1.1(v)) exige que apps
com Sign in with Apple REVOGUEM os tokens do usuário ao excluir a conta
(endpoint /auth/revoke). Para revogar é preciso ter um refresh_token — que só
existe se, NO LOGIN, trocarmos o `authorizationCode` (validade ~5 min) em
/auth/token. Este módulo faz as duas pontas, sempre BEST-EFFORT: nenhuma
falha aqui bloqueia login nem exclusão (a exclusão dos DADOS acontece de
qualquer forma); o resultado fica no Diário via retorno estruturado.

Config (Railway):
  SIWA_KEY_ID       — Key ID da chave "Sign in with Apple" (portal → Keys)
  SIWA_PRIVATE_KEY  — conteúdo do .p8 dessa chave (BEGIN/END incluídos)
  APNS_TEAM_ID      — reusado (Team ID é o mesmo da conta)
  APPLE_CLIENT_ID   — bundle id (já usado na validação do id_token)

Segurança: refresh_token fica no kv do usuário (chave "siwaRefresh") e NUNCA
é logado — mesmo tratamento da chave BYOK. A chave .p8 nunca entra no git.
"""
from __future__ import annotations

import os
import time
from typing import Optional

from . import db

APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
APPLE_REVOKE_URL = "https://appleid.apple.com/auth/revoke"
KV_KEY = "siwaRefresh"


def configured() -> bool:
    return all(os.environ.get(k) for k in ("SIWA_KEY_ID", "SIWA_PRIVATE_KEY", "APNS_TEAM_ID", "APPLE_CLIENT_ID"))


def _client_secret() -> str:
    """JWT ES256 exigido pela Apple como client_secret (validade curta)."""
    import jwt  # PyJWT[crypto] — já em requirements (validação OIDC)

    now = int(time.time())
    return jwt.encode(
        {
            "iss": os.environ["APNS_TEAM_ID"],
            "iat": now,
            "exp": now + 300,  # 5 min — gerado a cada chamada, nunca armazenado
            "aud": "https://appleid.apple.com",
            "sub": os.environ["APPLE_CLIENT_ID"],
        },
        os.environ["SIWA_PRIVATE_KEY"],
        algorithm="ES256",
        headers={"kid": os.environ["SIWA_KEY_ID"]},
    )


async def _post_form(url: str, data: dict) -> tuple[int, dict]:
    import httpx  # já em requirements (llm.py)

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(url, data=data,
                              headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            body = r.json()
        except Exception:  # noqa: BLE001 — revoke devolve corpo vazio em sucesso
            body = {}
        return r.status_code, body


async def exchange_and_store(conn, user_id: str, authorization_code: str) -> dict:
    """No LOGIN: troca o code por refresh_token e guarda no kv do usuário.
    Best-effort: devolve {ok, motivo} e nunca levanta exceção."""
    if not authorization_code:
        return {"ok": False, "motivo": "sem authorizationCode (login antigo ou ponte web)"}
    if not configured():
        return {"ok": False, "motivo": "SIWA não configurado (SIWA_KEY_ID/SIWA_PRIVATE_KEY)"}
    try:
        status, body = await _post_form(APPLE_TOKEN_URL, {
            "client_id": os.environ["APPLE_CLIENT_ID"],
            "client_secret": _client_secret(),
            "grant_type": "authorization_code",
            "code": authorization_code,
        })
        if status != 200 or not body.get("refresh_token"):
            return {"ok": False, "motivo": f"Apple /auth/token HTTP {status}: {body.get('error', 'sem refresh_token')}"}
        db.kv_set(conn, KV_KEY, body["refresh_token"], user_id=user_id)  # nunca logar o valor
        return {"ok": True, "motivo": "refresh_token armazenado para revoke futuro"}
    except Exception as e:  # noqa: BLE001 — login nunca falha por causa do SIWA
        return {"ok": False, "motivo": f"exceção na troca: {type(e).__name__}"}


async def revoke_for_user(conn, user_id: str) -> dict:
    """Na EXCLUSÃO: revoga o refresh_token na Apple (se existir) e apaga do kv.
    Best-effort: a exclusão dos dados acontece independente do resultado."""
    token = db.kv_get(conn, KV_KEY, user_id=user_id)
    if not token:
        return {"ok": True, "motivo": "sem token SIWA armazenado (conta e-mail/Google ou login antigo)"}
    if not configured():
        return {"ok": False, "motivo": "token existe mas SIWA não está configurado no servidor"}
    try:
        status, body = await _post_form(APPLE_REVOKE_URL, {
            "client_id": os.environ["APPLE_CLIENT_ID"],
            "client_secret": _client_secret(),
            "token": token,
            "token_type_hint": "refresh_token",
        })
        ok = status == 200
        return {"ok": ok, "motivo": "revogado na Apple" if ok else f"Apple /auth/revoke HTTP {status}: {body.get('error', '?')}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "motivo": f"exceção no revoke: {type(e).__name__}"}
