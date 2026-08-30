"""Boris+ como relying party do portal semente.id (Fase 4 do ADR-23).

Segundo caminho de entrada do painel administrativo, ao lado do login por
e-mail+senha que já existe — o portal soma um caminho, nunca substitui
(mesmo princípio do ADR-19 do MyData). A sessão que nasce daqui é a MESMA
sessão de sempre (`auth.create_session`, via o handoff do ADR-014); só a
origem muda.

Authorization Code + PKCE (S256) contra o portal, como qualquer relying
party OIDC. Duas travas de confiança, não uma no lugar da outra:
  1. o id_token é validado por assinatura (JWKS do portal), issuer,
     audience, expiração e nonce — feito aqui;
  2. `SEMENTE_ID_EMAIL_DONO`, se definida, é a SEGUNDA trava — o portal é
     multiusuário (outros sistemas do portfólio o compartilham) e o painel
     deste repo continua sendo de dono único. A PRIMEIRA trava é o RBAC do
     ADR-013 deste repo, aplicada no exchange do handoff (conta sem
     `permissions` não abre sessão) — as duas juntas, porque o SPEC aceita
     qualquer uma, e entregar as duas cobre o caso de nenhuma das duas
     variáveis estar configurada.

Porte ADAPTADO de `~/dev/cvm-financas/app/api/semente_id.py` (Fase 2 do
ADR-23, MyData): mesmo protocolo, mesma ordem de travas — mas com as
dependências DESTE repositório (`httpx` no lugar de `requests`,
`PyJWT[crypto]` no lugar de `authlib`) e uma diferença real de contrato: o
MyData autentica com uma sessão-cookie única e não precisa de um `sub`
estável (só do e-mail); este repo tem `identities` multi-provedor
(`auth.upsert_oauth_user`), que EXIGE (provider, sub) para não colidir
contas. Por isso `concluir_login` aqui devolve (sub, email, destino), e não
só (email, destino) como na referência.

Configuração, toda por env (nunca commitada, nunca em log/erro):
  SEMENTE_ID_CLIENT_ID       client_id registrado no portal (registro é
                             produção de OUTRO repositório — ver o Alex
                             rodar `railway ssh --service semente-id ...`)
  SEMENTE_ID_CLIENT_SECRET   client_secret do mesmo registro; segredo
  SEMENTE_ID_URL             default "https://id.semente.dev"
  SEMENTE_ID_REDIRECT_BASE   default "https://boris.semente.dev"; o
                             redirect_uri final é montado NUM ÚNICO LUGAR
                             (`_redirect_uri`) — "{base}/api/auth/
                             semente-id/callback" — e usado idêntico no
                             authorize e na troca do code (o portal compara
                             por igualdade exata, sem prefixo/wildcard)
  SEMENTE_ID_EMAIL_DONO      segunda trava (ver acima); vazio = só o RBAC
                             do ADR-013 decide
"""
from __future__ import annotations

import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt

from . import db

MINUTOS_DE_FLUXO = 10


class ErroSementeId(Exception):
    """A federação com o portal falhou. Mensagem SEGURA para o usuário —
    nunca eco de client_secret, code ou id_token; a mensagem diz o QUE
    falhou, nunca com quê."""


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def configurado() -> bool:
    return bool(os.environ.get("SEMENTE_ID_CLIENT_ID") and os.environ.get("SEMENTE_ID_CLIENT_SECRET"))


def _url_portal() -> str:
    return (os.environ.get("SEMENTE_ID_URL") or "https://id.semente.dev").rstrip("/")


def _redirect_uri() -> str:
    """Montado num ÚNICO lugar — idêntico no authorize e na troca do code."""
    base = (os.environ.get("SEMENTE_ID_REDIRECT_BASE") or "https://boris.semente.dev").rstrip("/")
    return f"{base}/api/auth/semente-id/callback"


def _s256(verifier: str) -> str:
    resumo = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(resumo).rstrip(b"=").decode()


def iniciar_login(conn, destino: str) -> str:
    """Grava o estado do fluxo (PKCE, nonce, destino) e devolve a URL de
    autorização do portal. Purga fluxos vencidos (>10min) antes de gravar o
    novo — mesmo padrão do MyData: sem isto a tabela cresceria sem fim com
    fluxos abandonados no meio do redirect."""
    db.semente_id_flow_purge(conn, _iso(_agora() - timedelta(minutes=MINUTOS_DE_FLUXO)))
    verifier = secrets.token_urlsafe(48)
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(16)
    db.semente_id_flow_insert(conn, state, verifier, nonce, destino, _iso(_agora()))
    params = {
        "client_id": os.environ["SEMENTE_ID_CLIENT_ID"],
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": _s256(verifier),
        "code_challenge_method": "S256",
    }
    return f"{_url_portal()}/authorize?" + urlencode(params)


async def _validar_id_token(id_token: str, nonce_esperado: str) -> dict:
    """Valida assinatura (JWKS do portal), issuer, audience, exp e nonce.
    `httpx` é a ÚNICA fronteira de rede deste módulo — I/O síncrono no event
    loop é proibido neste repositório."""
    async with httpx.AsyncClient(timeout=15) as client:
        resposta = await client.get(f"{_url_portal()}/jwks")
    resposta.raise_for_status()
    keys = (resposta.json() or {}).get("keys") or []
    if not keys:
        raise ErroSementeId("O portal não publicou nenhuma chave de assinatura.")
    try:
        header = jwt.get_unverified_header(id_token)
    except Exception as e:  # noqa: BLE001 — mensagem segura, sem eco do token
        raise ErroSementeId("O token de identidade do portal não pôde ser lido.") from e
    kid = header.get("kid")
    chave_data = next((k for k in keys if k.get("kid") == kid), None)
    if chave_data is None and len(keys) == 1:
        chave_data = keys[0]
    if chave_data is None:
        raise ErroSementeId("Nenhuma chave do portal confere com o token recebido.")
    try:
        signing_key = jwt.PyJWK(chave_data).key
        claims = jwt.decode(
            id_token, signing_key, algorithms=["RS256", "ES256"],
            audience=os.environ["SEMENTE_ID_CLIENT_ID"], issuer=_url_portal(),
            options={"require": ["exp", "iss", "sub", "aud"]},
        )
    except Exception as e:  # noqa: BLE001 — assinatura/issuer/audience/exp inválidos
        raise ErroSementeId("O token de identidade do portal não pôde ser validado.") from e
    if nonce_esperado and claims.get("nonce") != nonce_esperado:
        raise ErroSementeId("O nonce do login não confere.")
    return claims


async def concluir_login(conn, state: str | None, code: str | None, erro_do_portal: str | None) -> tuple[str, str, str]:
    """Troca o code, valida o id_token e devolve (sub, email, destino).

    O estado é consumido mesmo quando o portal recusou (`erro_do_portal`):
    um fluxo abortado não continua vivo para uma segunda tentativa com o
    mesmo state.
    """
    linha = db.semente_id_flow_get(conn, state or "")
    if linha is not None:
        db.semente_id_flow_delete(conn, state)
    if erro_do_portal:
        raise ErroSementeId(f"O portal recusou: {erro_do_portal}")
    if linha is None:
        raise ErroSementeId("Fluxo de login não encontrado ou vencido. Tente de novo.")
    if not code:
        raise ErroSementeId("O portal não devolveu um código de autorização.")

    async with httpx.AsyncClient(timeout=15) as client:
        resposta = await client.post(f"{_url_portal()}/token", data={
            "grant_type": "authorization_code", "code": code,
            "redirect_uri": _redirect_uri(), "code_verifier": linha["code_verifier"],
            "client_id": os.environ["SEMENTE_ID_CLIENT_ID"],
            "client_secret": os.environ["SEMENTE_ID_CLIENT_SECRET"],
        })
    if resposta.status_code != 200:
        # NUNCA eco do client_secret nem do corpo devolvido pelo portal —
        # só o desfecho.
        raise ErroSementeId("O portal recusou a troca do código de autorização.")
    id_token = (resposta.json() or {}).get("id_token", "")

    claims = await _validar_id_token(id_token, linha["nonce"])
    if not claims.get("email_verified") or not claims.get("email"):
        raise ErroSementeId("O portal não confirmou um e-mail verificado.")
    sub = claims.get("sub")
    if not sub:
        raise ErroSementeId("O token de identidade não trouxe um identificador de usuário.")

    dono = (os.environ.get("SEMENTE_ID_EMAIL_DONO") or "").strip().lower()
    email = str(claims["email"]).strip().lower()
    if dono and email != dono:
        raise ErroSementeId("Esta conta do portal não tem acesso a esta administração.")
    return str(sub), email, linha["destino"]
