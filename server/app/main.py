"""Boris+ - backend FastAPI.
Persistencia em SQLite (web). Cotacoes via Yahoo, analise via LLM.
O cliente iOS persiste no proprio aparelho e envia config/skill no corpo do
/api/analyze; o cliente web usa a config persistida aqui.
"""
import asyncio
import hmac
import os
from typing import Optional
from datetime import datetime
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import db, defaults, indicators, llm, pending_orders, plan, setups, store, technical_models, tickers, yahoo
from . import candles as candles_mod  # Objetivo 4: período de candles configurável
from . import brapi_budget  # ADR-008: orçamento de requisições da brapi (Fase 2)
from . import candle_cache  # Objetivo 5: cache de candles (delta + revalida último)
from . import regime  # qa/44 (B, ADR-009): classifica regime p/ gravar no outcome
from . import scanner  # BLOCO 3: radar de mercado (varredura do universo)
from . import radar_daily  # FASE 4 (1.3): varredura automática 1x/dia + sob demanda
from . import analysis_outcomes  # qa/30 (Fase A): autoavaliação da IA (N1/N2 vs. comportamento real)
from . import automacao  # ADR-012 (Fase 3): eficiência das operações automáticas do Operador
from . import ai_activity  # qa/45: custo (R$) + histórico de comportamento da IA
from . import fundamentals  # qa/36 (F10.2): fundamento × técnica (score, cache, rebaixamento)
from . import scan_deep  # FASE 1 (N1): aprofundamento IA do top-N do Radar
from . import candle_provider  # ADR-001: ponto único de entrada de candles
from . import options_provider  # v2: cotação de contratos (ADR-003/004/005), provedor selecionável
from . import technical_snapshot  # FASE 1 (STU): fonte única de N1/N2/N3
from . import model_catalog  # qa/49: catálogo de modelos por provedor + parâmetros aceitos
from . import agent as agent_mod  # FASE 3: agente autônomo server-side
from . import timing_watch  # FASE 3 (C-35): 2º kill-switch — push do gatilho
from . import siwa  # FASE 4 (Bloco 2): Sign in with Apple — exchange + revoke
from . import push  # FASE 3.3b: APNs (no-op sem configuração)
from . import obslog  # FASE 5: observabilidade (log estruturado + ring buffer)
from . import conceitos  # camada de entendimento: catálogo determinístico (custo zero)
from . import explicacao_det  # FIX-C01: fallback determinístico do Passo 7 sem IA
from . import benchmark  # FIX-C03: série diária do Ibovespa (comparação no Passo 8)
from . import analytics  # qa/47: eventos de comportamento (ingest + rollup + purga)
from . import signal_ledger  # ADR-017 (Bloco 1): histórico medido por setup (ledger de sinais)
from .catalog import is_catalog_ticker
from .options_api import router as options_router, _spot_from_chain_or_quote
from .options_provider import get_options as _get_options_for_status
from . import opcoes_lastreadas  # Fase 14 (Plano 03): motor de proposta lastreada (venda coberta/put)
from . import skill_ref  # Fase 14 (Plano 03): frase canônica da proposta lastreada por modo

app = FastAPI(title="Boris+ API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=False,
)

_conn = db.shared()  # FIX: conexão POR THREAD (pool do FastAPI) — ver db.py
store.ensure_defaults(_conn)
_analytics_conn = analytics.shared()  # qa/47: banco SEPARADO (ver analytics.default_db_path)
# FASE 5 (performance): liga o L2 persistente do cache de candles (SQLite no
# volume /data) — redeploy do Railway reidrata e busca só o delta recente.
candle_cache.configure_db(_conn)
# ADR-008 (Fase 2): o contador de orçamento da brapi persiste no mesmo SQLite —
# sem isto o teto diário zeraria a cada deploy (degrada a proteção da cota).
brapi_budget.configure_db(_conn)
# ADR-013: kill-switch do agente ganha override em runtime (admin), mesmo
# padrão memória→DB→env da brapi acima — sem isto o toggle admin nunca
# checaria o SQLite.
agent_mod.configure_db(_conn)
# C-35 (REPORT-01): o 2º kill-switch (push do gatilho) ganha o MESMO override
# em runtime — sem isto o toggle admin nunca checaria o SQLite, igual ao caso
# do agente acima.
timing_watch.configure_db(_conn)
# ADR-017 (Bloco 1): liga o provedor de histórico medido a detect_setups —
# sem esta linha, detect_setups nunca anexa `historico` e regime.ranquear
# nunca vê `elegivel`: todo o ledger existiria sem consequência nenhuma na
# tela. Lambda (não import direto dentro de setups.py) de propósito: mantém
# setups.py puro — sem I/O, sem banco —, o que permite a suíte inteira rodar
# sem banco e evita I/O no caminho síncrono quente do STU (detect_setups
# roda por request, em 8+ rotas).
setups.set_historico_provider(lambda: signal_ledger.historico_snapshot(_conn))
app.include_router(options_router)


# FIX (diagnóstico): erro não tratado vira JSON {"detail": ...} em vez de
# "Internal Server Error" opaco — o api.js já sabe exibir `detail`, então o
# app mostra a causa real (ex.: no Radar). O traceback completo SEGUE nos logs
# do Railway (o Starlette re-lança a exceção após enviar a resposta).
@app.exception_handler(Exception)
async def _unhandled_exception(request: Request, exc: Exception):
    # FASE 5: todo erro não tratado entra no log estruturado (categoria err) —
    # visível no Railway E na tela Perfil → Observabilidade (/api/obs/logs).
    obslog.log("err", f"{request.method} {request.url.path}: {type(exc).__name__}: {exc}", level="error")
    return JSONResponse(
        status_code=500,
        content={"detail": type(exc).__name__ + ": " + (str(exc) or "erro interno")},
    )


# ===========================================================================
# FASE 2 — autenticação multiusuário (aditivo).
# Decisão A: app abre SEM login. Sem Bearer token => scope=None => escopo
# anônimo/legado (comportamento atual preservado). Com token válido => escopo
# por user_id. Decisão D: BYOK intacto (a chave segue em config, por escopo).
# ===========================================================================
from fastapi import Depends, Header  # noqa: E402
from . import auth  # noqa: E402
from . import managed, metering  # noqa: E402 — FASE 3: IA gerenciada (cota/rate)
from . import rbac, audit  # noqa: E402 — ADR-013: RBAC por macro função + auditoria de escrita admin
from . import semente_id  # noqa: E402 — Fase 4 (ADR-23): relying party do portal semente.id

managed.configure_db(_conn)  # ADR-013: override de provider/model/cota via admin, antes do env


def current_scope(authorization: Optional[str] = Header(default=None)) -> Optional[str]:
    """Resolve o user_id pelo Bearer token. Token ausente/ inválido/expirado =>
    None (escopo anônimo). NUNCA levanta — rotas de dados funcionam sem login."""
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    user = auth.resolve_session(_conn, parts[1].strip())
    return user["id"] if user else None


def _plano_do_escopo(scope: Optional[str]) -> dict:
    """C-31: resolve o plano REAL da conta logada (`plan.current_plan`, código
    órfão desde o ADR-013 — nenhum call site de gate passava `plan=`/`user=`,
    então TODOS caíam no fallback global `ACTIVE_PLAN`, inclusive contas
    'pro'). O eixo comercial NUNCA pode derrubar uma rota de dado/análise:
    qualquer falha ao ler o usuário (ou escopo anônimo) degrada para
    `plan.ACTIVE_PLAN` — o plano MENOS privilegiado, nunca um superior
    (fail-closed, ver T-03-13/T-03-14 do threat model da fase 3)."""
    try:
        user = db.get_user_by_id(_conn, scope) if scope else None
        return plan.current_plan(user)
    except Exception:
        return plan.ACTIVE_PLAN


def require_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """Exige sessão válida (rotas de conta: /me, /logout, DELETE /account)."""
    if not authorization:
        raise HTTPException(401, "Faça login para continuar.")
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(401, "Token de sessão ausente ou malformado.")
    user = auth.resolve_session(_conn, parts[1].strip())
    if not user:
        raise HTTPException(401, "Sessão expirada. Faça login novamente.")
    return user


# ADR-013 — RBAC por macro função: SEMPRE no backend, via Depends() — nunca só
# escondendo botão na UI (restrição do ADR). Composição: require_permission()
# exige sessão válida (require_user) E a permissão nomeada; substitui o antigo
# `_is_obs_admin` binário nas 9 rotas admin que já existiam.
def require_permission(perm: str):
    def _dep(user: dict = Depends(require_user)) -> dict:
        # Achado de revisão: só login/`/me` disparavam o bootstrap do
        # `role_admin` — uma sessão/token anterior ao deploy desta feature
        # (ou qualquer chamador que bata direto numa rota admin sem passar
        # por `/me` antes) tomava 403 mesmo sendo admin legítimo. O antigo
        # `_is_obs_admin` reavaliava a regra em TODA request; isto restaura
        # esse comportamento no caminho que realmente importa (rota admin).
        rbac.ensure_bootstrap_role(_conn, user)
        if not rbac.user_has_permission(_conn, user["id"], perm):
            raise HTTPException(403, f"Requer a permissão '{perm}'.")
        return user
    return _dep


def require_any_admin_permission():
    """Para telas transversais (ex.: Auditoria) — qualquer papel administrativo
    serve, não uma permissão específica."""
    def _dep(user: dict = Depends(require_user)) -> dict:
        rbac.ensure_bootstrap_role(_conn, user)
        if not rbac.permissions_for_user(_conn, user["id"]):
            raise HTTPException(403, "Requer algum papel administrativo.")
        return user
    return _dep


def _public_user(u: dict) -> dict:
    """Nunca devolve pass_hash nem provider_sub ao cliente. ADR-013: inclui
    `permissions` (cosmético — a UI esconde botão pela lista, mas toda rota
    de escrita valida de novo no backend) e `plan` (eixo de monetização)."""
    if not u:
        return None
    return {
        "id": u.get("id"), "email": u.get("email"), "name": u.get("name"), "provider": u.get("provider"),
        "plan": u.get("plan") or "free",
        "permissions": sorted(rbac.permissions_for_user(_conn, u["id"])) if u.get("id") else [],
    }


def _apply_seed(user_id: str, body: dict) -> None:
    """Decisão B: 1º login com conta vazia adota o dado local como semente.
      - body["seed"] dict  => semente explícita (iOS envia o doc local, com BYOK).
      - body["seed"] False => começa limpo (só defaults).
      - ausente/None       => web: adota o escopo anônimo/global do servidor
                              (que contém a chave BYOK; nunca trafega ao cliente).
    Em todos os casos só semeia se a conta ainda estiver vazia."""
    seed = body.get("seed", "__default__") if isinstance(body, dict) else "__default__"
    if isinstance(seed, dict):
        # iOS: o doc é local-first e pertence a quem está no aparelho — semear
        # com ele preserva o que a pessoa já fez ali (inclusive a chave BYOK).
        store.seed_user_from(_conn, user_id, seed)
    else:
        # WEB: conta nova COMEÇA LIMPA (09/08/2026).
        #
        # Antes o web caía em `export_sections(user_id=None)` — uma cópia do
        # escopo ANÔNIMO/global. Isso fazia sentido enquanto existia "usar sem
        # conta": a pessoa acumulava dados antes de se cadastrar e não podia
        # perdê-los. Removido o modo anônimo, ninguém mais acumula nada ali —
        # e o escopo anônimo é um BALDE ÚNICO do servidor: num servidor
        # compartilhado, toda conta nova nascia herdando a sobra de quem passou
        # por ali antes (foi assim que a carteira-demo apareceu numa conta nova).
        store.ensure_defaults(_conn, user_id=user_id)


def _auth_payload(user: dict) -> dict:
    # ADR-013: bootstrap aditivo do papel administrativo — quem bate na MESMA
    # lógica que `_is_obs_admin` usava (B3_ADMIN_EMAILS ou 1ª conta) recebe
    # `role_admin` aqui, a cada login, sem precisar de script de migração.
    rbac.ensure_bootstrap_role(_conn, user)
    token = auth.create_session(_conn, user["id"])
    return {"token": token, "user": _public_user(user), "state": store.public_state(_conn, user_id=user["id"])}


def _client_ip(request: Request) -> str:
    """IP real atrás do proxy do Railway (X-Forwarded-For), com fallback."""
    fwd = request.headers.get("x-forwarded-for") or ""
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "?"


@app.post("/api/auth/register")
async def auth_register(request: Request, body: dict = Body(default={})):
    # FASE 5 (lançamento): freio de força bruta/enumeração também no registro.
    # F10-20260819: chave (ip,email) sozinha é contornável trocando o IP a
    # cada tentativa (X-Forwarded-For é auto-declarado) — chave email-only em
    # PARALELO faz o e-mail-alvo acumular tentativas mesmo variando o IP.
    rl_key = auth.throttle_key(_client_ip(request), str(body.get("email", "")))
    rl_key_email = auth.throttle_key_email_only(str(body.get("email", "")))
    try:
        auth.throttle_check(rl_key)
        auth.throttle_check(rl_key_email)
        user = auth.register_email(_conn, body.get("email", ""), body.get("password", ""), body.get("name", ""))
    except auth.AuthError as e:
        auth.throttle_fail(rl_key)
        auth.throttle_fail(rl_key_email)
        raise HTTPException(400, str(e))
    auth.throttle_clear(rl_key)
    auth.throttle_clear(rl_key_email)
    _apply_seed(user["id"], body)
    return _auth_payload(user)


@app.post("/api/auth/login")
async def auth_login(request: Request, body: dict = Body(default={})):
    # FASE 5 (lançamento): rate limit por (ip, e-mail) — sucesso zera o contador.
    # F10-20260819: chave email-only em PARALELO — ver comentário em /api/auth/register.
    rl_key = auth.throttle_key(_client_ip(request), str(body.get("email", "")))
    rl_key_email = auth.throttle_key_email_only(str(body.get("email", "")))
    try:
        auth.throttle_check(rl_key)
        auth.throttle_check(rl_key_email)
        user = auth.login_email(_conn, body.get("email", ""), body.get("password", ""))
    except auth.AuthError as e:
        auth.throttle_fail(rl_key)
        auth.throttle_fail(rl_key_email)
        obslog.log("auth", "login falhou (ip=" + _client_ip(request) + ")", level="warn")
        raise HTTPException(401, str(e))
    auth.throttle_clear(rl_key)
    auth.throttle_clear(rl_key_email)
    _apply_seed(user["id"], body)   # idempotente: só semeia conta vazia
    return _auth_payload(user)


@app.post("/api/auth/oauth")
async def auth_oauth(request: Request, body: dict = Body(default={})):
    provider = str(body.get("provider", "")).lower()
    id_token = body.get("idToken") or body.get("id_token") or ""
    # FASE 5 (lançamento): mesmo freio das demais rotas de auth (por ip+provedor).
    # F10-20260819: chave email-only em PARALELO — ver comentário em /api/auth/register.
    rl_key = auth.throttle_key(_client_ip(request), "oauth:" + provider)
    rl_key_email = auth.throttle_key_email_only("oauth:" + provider)
    try:
        auth.throttle_check(rl_key)
        auth.throttle_check(rl_key_email)
        claims = auth.verify_oauth_token(provider, id_token)
        if not claims.get("sub"):
            raise auth.AuthError("Token sem identificador de usuário.")
        # FASE 4 (Bloco 2): a Apple só envia o nome no PRIMEIRO consentimento e
        # fora do id_token — a ponte nativa o repassa como hint; usado apenas
        # na criação (upsert ignora em contas existentes).
        name = claims.get("name") or (str(body.get("name") or "").strip() or None)
        user = auth.upsert_oauth_user(_conn, provider, claims["sub"], claims.get("email"), name,
                                       email_verified=bool(claims.get("email_verified")))
    except auth.AuthError as e:
        auth.throttle_fail(rl_key)
        auth.throttle_fail(rl_key_email)
        raise HTTPException(401, str(e))
    auth.throttle_clear(rl_key)
    auth.throttle_clear(rl_key_email)
    # FASE 4 (Bloco 2): SIWA — guarda o refresh_token para o revoke exigido na
    # exclusão de conta (5.1.1(v)). Best-effort: nunca bloqueia o login; o
    # resultado vai para o Diário (motivo exato, sem nunca logar o token).
    if provider == "apple" and body.get("authorizationCode"):
        r = await siwa.exchange_and_store(_conn, user["id"], str(body.get("authorizationCode")))
        store.push_agent_log(_conn, [{"time": agent_mod._now_str(), "kind": "auth",
                                      "text": "SIWA: " + ("token de revogação armazenado." if r.get("ok") else "troca do code falhou — " + str(r.get("motivo")))}],
                             user_id=user["id"])
    _apply_seed(user["id"], body)
    return _auth_payload(user)


@app.get("/api/auth/me")
async def auth_me(user: dict = Depends(require_user)):
    # ADR-013: idempotente — cobre sessões que já existiam antes do deploy
    # desta feature (senão o bootstrap só rodaria no PRÓXIMO login de verdade).
    rbac.ensure_bootstrap_role(_conn, user)
    return {"user": _public_user(user), "state": store.public_state(_conn, user_id=user["id"])}


@app.post("/api/auth/logout")
async def auth_logout(authorization: Optional[str] = Header(default=None)):
    if authorization:
        parts = authorization.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            auth.revoke_session(_conn, parts[1].strip())
    return {"ok": True}


# ADR-23 (Fase 4) — Boris+ como relying party do portal semente.id. Segundo
# caminho de entrada do painel admin, ao lado do login por e-mail+senha
# (que continua idêntico). Prefixo /api/auth/ já está em
# _GATE_ALLOWLIST_PREFIXES (abaixo) — funciona antes de haver sessão, que é
# o ponto. Deságua no MESMO handoff do ADR-014 (POST /api/admin/mobile-
# handoff/exchange) que o app nativo já usa — nenhum caminho de troca novo
# no front.
@app.get("/api/auth/semente-id/inicio")
async def auth_semente_id_inicio():
    if not semente_id.configurado():
        raise HTTPException(
            503,
            "Login pelo portal semente.id não configurado no servidor "
            "(defina SEMENTE_ID_CLIENT_ID e SEMENTE_ID_CLIENT_SECRET no Railway).",
        )
    url = semente_id.iniciar_login(_conn, "/admin/")
    return RedirectResponse(url, status_code=302)


@app.get("/api/auth/semente-id/callback")
async def auth_semente_id_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    # Mesmo freio das demais rotas de auth — martelar o callback não pode
    # virar força bruta de state/code.
    rl_key = auth.throttle_key(_client_ip(request), "semente-id")
    try:
        auth.throttle_check(rl_key)
        sub, email, destino = await semente_id.concluir_login(_conn, state, code, error)
        # Unificação por e-mail VERIFICADO pelo portal — mesmo caminho que
        # Apple/Google já usam (auth.upsert_oauth_user); anexa a identidade
        # nova à conta que o Alex já tem, preservando o role_admin dela.
        user = auth.upsert_oauth_user(_conn, "semente-id", sub, email, email_verified=True)
    except (auth.AuthError, semente_id.ErroSementeId) as e:
        auth.throttle_fail(rl_key)
        # Falha do portal vira redirect — NUNCA stack trace na cara do
        # navegador, e o log nunca inclui token/code/segredo (a própria
        # ErroSementeId já garante isso na mensagem).
        obslog.log("auth", "semente-id: callback falhou — " + str(e), level="warn")
        return RedirectResponse("/admin/", status_code=302)
    # PRIMEIRA trava: RBAC do ADR-013. Conta do portal sem NENHUM papel
    # administrativo não recebe handoff — redireciona sem sessão plena.
    rbac.ensure_bootstrap_role(_conn, user)
    if not rbac.permissions_for_user(_conn, user["id"]):
        auth.throttle_fail(rl_key)
        obslog.log("auth", "semente-id: login ok, sem papel administrativo", level="warn")
        return RedirectResponse(destino or "/admin/", status_code=302)
    auth.throttle_clear(rl_key)
    # Mesmo mint do ADR-014 (main.py, admin_mobile_handoff): código de ~90s,
    # uso único, trocado por sessão plena em /api/admin/mobile-handoff/exchange.
    # Fragmento (#), não query — não vai a log de servidor nem a Referer.
    codigo = auth.create_session(_conn, user["id"], ttl_days=90 / 86400)
    obslog.log("auth", "semente-id: login concluído", level="info")
    return RedirectResponse(f"{destino or '/admin/'}#handoff={codigo}", status_code=302)


# ===========================================================================
# F4 completo (2026-08-02) — cadastro obrigatório, SÓ nos domínios listados.
#
# Decisão do Alex: acamerini.app fecha (sem modo convidado); a URL do Railway
# e o app iOS continuam exatamente como estão (Decisão A permanece intacta
# para eles). B3_GATED_HOSTS vazio = ninguém é afetado — dormente até o
# Railway apontar de verdade para acamerini.app (mesmo padrão do
# web_dist/ios_dist: existe no código, só liga quando configurado).
#
# Allowlist por PREFIXO (não por rota individual, então uma rota de auth nova
# amanhã já nasce acessível): /api/auth/* (senão ninguém consegue logar),
# /api/health (monitoramento não é dado de usuário) e /api/market (Fase 2,
# MERC-01/D-08): status de pregão é dado PÚBLICO de calendário da B3 — sem
# isto a tela de LOGIN no domínio gated não conseguiria mostrar o badge de
# mercado aberto/fechado, e o gate devolveria 401 justamente na tela que ele
# existe para empurrar o usuário a usar.
# ===========================================================================
_GATED_HOSTS = {h.strip().lower() for h in (os.environ.get("B3_GATED_HOSTS") or "").split(",") if h.strip()}
_GATE_ALLOWLIST_PREFIXES = ("/api/auth/", "/api/health", "/api/market")


def _has_valid_session(request: Request) -> bool:
    header = request.headers.get("authorization") or ""
    parts = header.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False
    return auth.resolve_session(_conn, parts[1].strip()) is not None


@app.middleware("http")
async def gate_cadastro_obrigatorio(request: Request, call_next):
    path = request.url.path
    if _GATED_HOSTS and path.startswith("/api/") and not path.startswith(_GATE_ALLOWLIST_PREFIXES):
        host = (request.headers.get("host") or "").split(":")[0].lower()
        if host in _GATED_HOSTS and not _has_valid_session(request):
            return JSONResponse(status_code=401, content={
                "detail": "Cadastro obrigatório neste domínio. Faça login ou crie sua conta.",
                "code": "cadastro_obrigatorio",
            })
    return await call_next(request)


# Cabeçalhos de segurança — universais, de baixo risco (não dependem do
# B3_GATED_HOSTS): nenhum deles muda comportamento visível do app, só reduz
# superfície de ataque. CSP fica de fora aqui de propósito: o app é um SPA
# React com estilo INLINE em toda parte (style={{...}}) — uma CSP errada
# quebraria a renderização inteira sem aviso; entra como tarefa própria,
# testada visualmente antes de ir para produção (ver PENDÊNCIAS-F4.md).
@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return resp


@app.delete("/api/account")
async def delete_account(user: dict = Depends(require_user)):
    """Item 5 — exclusão de conta in-app: apaga todos os dados do usuário,
    a linha em users e as sessões. Irreversível.
    FASE 4 (Bloco 2): contas Sign in with Apple têm o token REVOGADO na Apple
    antes da limpeza (exigência da 5.1.1(v)); best-effort — a exclusão dos
    dados acontece independentemente do resultado do revoke."""
    revoke = await siwa.revoke_for_user(_conn, user["id"])
    store.delete_user_data(_conn, user["id"])
    return {"ok": True, "deleted": user["id"], "siwaRevoke": revoke}


# ===========================================================================
# FASE 3 (item 2) — IA gerenciada: caminho PARALELO ao BYOK.
# BYOK (chave no config) tem prioridade e NÃO consome cota. Sem BYOK, usuário
# LOGADO cai na IA gerenciada (modelo barato do servidor) sob cota diária +
# rate limit por usuário. Anônimo e sem BYOK seguem o comportamento atual.
# ===========================================================================
def _ai_apply_managed(scope, config, custo: int = 1):
    """Retorna (config_efetiva, consume). Levanta 402 se a cota/rate bloquear.
    Chame consume() APÓS o LLM responder com sucesso (falha não gasta cota).

    qa/42 (FinOps): `custo` = quantas análises este request pode disparar
    (o /api/scan/deep faz até MAX_TOP_N). Sem isso, o check media 1 e o
    consume contava N — a cota era furada em até +9 por request."""
    if llm.resolve_key(config):                      # BYOK utilizável → sem cota
        return config, (lambda: None)
    mcfg = managed.managed_config()
    if scope and mcfg:                               # logado + gerenciada habilitada
        ok, reason = metering.check(_conn, scope, quota=managed.daily_quota(),
                                    rate_per_min=managed.rate_per_min(), custo=custo,
                                    cap_global=managed.global_daily_cap())
        if not ok:
            raise HTTPException(402, reason)
        # FASE 8B (B4): a config gerenciada é só a CHAVE/modelo — o modo de
        # trabalho do usuário viaja junto (senão a mesa falava como professor).
        # qa/42 (FinOps): `candlePeriod` TAMBÉM viaja. A config gerenciada
        # substituía a do usuário e o candlePeriod se perdia → normalize_period
        # (None) caía no default "1y" = 252 candles, mesmo com "1mo" escolhido:
        # ~7x mais tokens de input, JUSTO no caminho que gasta a chave do
        # servidor. Quem paga era quem mandava o prompt mais caro.
        return ({**mcfg, "appMode": (config or {}).get("appMode"),
                 "candlePeriod": (config or {}).get("candlePeriod")},
                (lambda: metering.consume(_conn, scope)))
    return config, (lambda: None)                    # sem BYOK e sem gerenciada: llm dará erro acionável


def _gate_analise(scope, config, custo: int = 1):
    """C-32: ponto ÚNICO de decisão de gate de análise por requisição. Antes,
    dois gates coexistiam na MESMA requisição (`plan.can_analyze` e
    `metering.check`), cada um com sua própria noção de janela — plano é
    MENSAL, metering é DIÁRIO. Aqui eles passam a ser um único ponto de
    decisão, com precedência EXPLÍCITA: o gate de PLANO decide se a conta tem
    direito ao recurso; o de METERING (dentro de `_ai_apply_managed`) decide
    se ainda há cota da chave do servidor hoje. O CONTADOR é sempre o de
    `metering` — `plan.can_analyze` nunca mantém contagem própria (ver
    contrato em plan.py). Retorna (config_efetiva, consume), igual
    `_ai_apply_managed`."""
    plano = _plano_do_escopo(scope)
    # C-33 (fase 5): a contagem passada ao gate de plano é a REAL do mês
    # corrente, lida do ledger único de `metering` (contrato escrito em
    # plan.py) — nunca um segundo contador paralelo. Escopo anônimo (None)
    # também resolve: `metering.month_used` devolve 0 para o balde sem user_id.
    allowed, reason = plan.can_analyze(metering.month_used(_conn, scope), plan=plano)
    if not allowed:
        raise HTTPException(402, reason)
    config, consume = _ai_apply_managed(scope, config, custo=custo)
    return config, consume


@app.get("/api/ai/quota")
async def ai_quota(scope: Optional[str] = Depends(current_scope)):
    """Estado da IA do app para a UI: se a gerenciada existe, se o usuário tem
    BYOK e quanta cota resta hoje.
    C-33 (fase 5): `monthUsed`/`monthLimit` em nível RAIZ (não dentro de
    `quota`, que só existe com IA gerenciada sem BYOK) — o front consome
    esse contrato no Plano 05-07. `monthUsed` vem do ledger de `metering`,
    `monthLimit` do plano real da conta — limite mensal do FREE ativo (30)
    desde a v1.3/Fase 12 (ADR-010); `None` agora só acontece para conta pro
    (ilimitada) e para o escopo anônimo (early return acima)."""
    avail = managed.is_available()
    if not scope:
        return {"managed": avail, "loggedIn": False, "byok": False, "quota": None,
                "monthUsed": None, "monthLimit": None}
    cfg = store.get(_conn, "config", user_id=scope)
    byok = bool(llm.resolve_key(cfg))
    snap = metering.snapshot(_conn, scope, managed.daily_quota()) if (avail and not byok) else None
    return {"managed": avail, "loggedIn": True, "byok": byok, "quota": snap,
            "monthUsed": metering.month_used(_conn, scope),
            "monthLimit": _plano_do_escopo(scope).get("max_analyses_per_month")}


@app.get("/api/ai/models")
async def ai_models():
    """qa/49: catálogo de modelos por provedor + parâmetros aceitos (fonte única
    p/ a listbox do app). `temperatureDefault` = valor sugerido quando o modelo
    aceita temperatura."""
    return {"catalog": model_catalog.catalog_publico(), "temperatureDefault": llm.LLM_TEMPERATURE}


def now_str() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # FASE 3 (Operador) + FASE 5 (observabilidade): loga TODA request de API com
    # método, rota, origem, status e DURAÇÃO — no stdout (Railway) e no ring
    # buffer (/api/obs/logs). Requests lentos (>2s) sobem para categoria "slow"
    # nível warn; erros 5xx para nível error. A rota /api/obs não se auto-loga
    # (evita ruído em quem está olhando os logs pela tela).
    path = request.url.path
    is_api = path.startswith("/api") and not path.startswith("/api/obs")
    import time as _t
    t0 = _t.monotonic()
    resp = await call_next(request)
    if is_api:
        dur = _t.monotonic() - t0
        client = _client_ip(request)
        status = getattr(resp, "status_code", 0)
        if dur > 2.0:
            obslog.log("slow", f"{request.method} {path} levou {dur:.1f}s (status {status})", level="warn", ip=client)
        elif status >= 500:
            obslog.log("req", f"{request.method} {path} -> {status} em {dur * 1000:.0f}ms", level="error", ip=client)
        else:
            obslog.log("req", f"{request.method} {path} -> {status} em {dur * 1000:.0f}ms", ip=client)
    return resp


# ---- FASE 5: observabilidade consultável (Perfil → Observabilidade) --------
# ADR-013: o gate binário `_is_obs_admin` foi substituído por
# `require_permission(...)` nomeada por grupo (macro função) — ver rbac.py.
# O bootstrap (`B3_ADMIN_EMAILS` ou 1ª conta) preserva EXATAMENTE quem tinha
# acesso antes, via `rbac.ensure_bootstrap_role`.
@app.get("/api/obs/logs")
async def obs_logs(n: int = 200, level: Optional[str] = None, cat: Optional[str] = None,
                   user: dict = Depends(require_permission("observabilidade.ver"))):
    return {"logs": obslog.recent(n, level=level, cat=cat), "stats": obslog.stats()}


# qa/42 (FinOps) — quanto a IA custou HOJE. Antes não havia como responder:
# nenhum caller lia o `usage` e não existia contador agregado (só cota por
# usuário). Restrito ao admin: é dado do servidor, não do usuário.
def _usage_snapshot() -> dict:
    cap = managed.global_daily_cap()
    analises_hoje = metering.global_snapshot(_conn, cap)  # persistido, todos os usuários
    # FIX-C38 (fase 5): alerta PREVENTIVO — mesma grandeza que o hard stop
    # acima já limita (análises gerenciadas do dia), não tokens. A leitura da
    # série (banco de analytics SEPARADO, ver `_analytics_conn`) é degradada
    # honestamente: o painel de observabilidade nunca pode cair inteiro
    # porque esse banco está indisponível (mesmo princípio do try/except do
    # rollup em `analytics.maybe_run`).
    limiar = db.admin_config_get(_conn, "llmAlertaGastoPct")
    janela = db.admin_config_get(_conn, "llmAlertaJanelaDias") or metering.ALERTA_JANELA_PADRAO
    try:
        serie = analytics.serie_metrica(_analytics_conn, "ia_analises_gerenciadas_dia", dias=janela + 3)
        alerta_gasto_ia = metering.alerta_gasto(analises_hoje["used"], serie, limiar, janela)
    except Exception:  # noqa: BLE001 — série indisponível não pode derrubar /api/obs/usage
        alerta_gasto_ia = {
            "configurado": bool(limiar), "avaliavel": False, "motivo": "série indisponível",
            "hoje": analises_hoje["used"], "media": None, "desvioPct": None,
            "limiarPct": limiar, "janelaDias": janela, "acima": False,
        }
    return {
        "tokens": llm.usage_snapshot(),              # por modelo, do dia (memória: zera no deploy)
        "analisesGerenciadas": analises_hoje,
        "iaGerenciadaAtiva": bool(managed.managed_config()),
        "tetoGlobalDia": cap,                        # None = ilimitado (B3_MANAGED_GLOBAL_DAILY_CAP)
        "cotaPorUsuarioDia": managed.daily_quota(),
        # ADR-001 (Decisão 5): o fetch de candles é instrumentado como a IA já
        # era. `candles.alerta=true` é o gatilho declarado do plano B — taxa de
        # não-200 acima de 2% em 3 pregões reabre a decisão de provedor.
        "candles": candle_provider.snapshot(),
        # A2a (auditoria): uso da rota legada /api/analyze desde o deploy —
        # zero sustentado = builds antigos morreram, a rota pode aposentar.
        "legacyAnalyze": dict(LEGACY_ANALYZE),
        # qa/46 (Fase 2): candle_cache.stats() já existia, sem endpoint — só
        # liga o fio (L2/SQLite: nº de candles + idade por symbol@interval).
        "cacheCandles": candle_cache.stats(),
        "alertaGastoIA": alerta_gasto_ia,
    }


@app.get("/api/obs/usage")
async def obs_usage(user: dict = Depends(require_permission("observabilidade.ver"))):
    return _usage_snapshot()


# ADR-008 (controle de utilização): o INTERVALO entre atualizações de spot é o
# parâmetro; a projeção responde NA HORA quantas chamadas/mês ele custa. GET
# simula sem aplicar; POST só aplica com {"aplicar": true} explícito.
@app.get("/api/obs/brapi/projecao")
async def obs_brapi_projecao(intervaloS: Optional[int] = None,
                             user: dict = Depends(require_permission("fontes_dados.configurar"))):
    alvo = intervaloS if intervaloS is not None else brapi_budget.spot_intervalo_s()
    return {
        "vigenteS": brapi_budget.spot_intervalo_s(),
        "projecao": brapi_budget.projecao(alvo, brapi_budget._universo_n()),
        "aplicado": False,
    }


@app.post("/api/obs/brapi/projecao")
async def obs_brapi_projecao_aplicar(body: dict = Body(default={}),
                                     user: dict = Depends(require_permission("fontes_dados.configurar"))):
    try:
        alvo = int(body.get("intervaloS"))
    except (TypeError, ValueError):
        raise HTTPException(400, "Informe intervaloS (segundos, inteiro >= 30).")
    proj = brapi_budget.projecao(alvo, brapi_budget._universo_n())
    if not body.get("aplicar"):
        return {"vigenteS": brapi_budget.spot_intervalo_s(), "projecao": proj, "aplicado": False}
    anterior = brapi_budget.spot_intervalo_s()
    vigente = brapi_budget.set_spot_intervalo(alvo)
    # ADR-013: primeira rota migrada para o audit log — já era admin-gated e
    # já escrevia estado em runtime, sem nenhum registro de quem mudou o quê.
    audit.record(_conn, user["id"], "brapi_spot_intervalo", None, "intervaloS", anterior, vigente)
    return {"vigenteS": vigente, "projecao": proj, "aplicado": True}


# qa/47 (Fase 1 — infra só, sem client SDK/dashboard): ingest genérico de
# eventos de comportamento. Rate limit reusa metering.py com uma SEÇÃO
# própria (não mistura com a cota de IA gerenciada). 429 (não 402: não é
# "cota paga", é proteção contra flood) — a mensagem de metering.check é
# específica de IA, por isso não é repassada ao chamador aqui.
def _analytics_quota_dia() -> int:
    return int(os.environ.get("B3_ANALYTICS_QUOTA_DIA") or 5000)


def _analytics_rate_min() -> int:
    return int(os.environ.get("B3_ANALYTICS_RATE_MIN") or 30)


@app.post("/api/analytics/events")
async def analytics_events(body: dict = Body(default={}), user: dict = Depends(require_user)):
    events = body.get("events")
    ok, _reason = metering.check(
        _conn, user["id"], quota=_analytics_quota_dia(), rate_per_min=_analytics_rate_min(),
        custo=len(events) if isinstance(events, list) else 1,
        section="analyticsEvents", global_section="analyticsEventsGlobal",
    )
    if not ok:
        raise HTTPException(429, "Limite de envio de eventos de analytics excedido. Tente novamente mais tarde.")
    try:
        result = analytics.ingest(_analytics_conn, user["id"], events)
    except ValueError as e:
        obslog.log("analytics", f"ingest rejeitado (uid={user['id'][:8]}…): {e}", level="warn")
        raise HTTPException(400, str(e))
    metering.consume(_conn, user["id"], custo=result["accepted"],
                     section="analyticsEvents", global_section="analyticsEventsGlobal")
    return result


@app.get("/api/analytics/summary")
async def analytics_summary(dias: int = 30, passos: Optional[str] = None,
                            user: dict = Depends(require_permission("observabilidade.ver"))):
    lista_passos = [p.strip() for p in passos.split(",") if p.strip()] if passos else None
    return {
        "adocaoPorFeature": analytics.adocao_por_feature(_analytics_conn, dias=dias),
        "funil": analytics.funil(_analytics_conn, lista_passos, dias=dias),
        "shownVsDismissed": analytics.shown_vs_dismissed(_analytics_conn, dias=dias),
        # ADR-012 (Fase 2): série diária por evento — habilita o gráfico de
        # tendência no portal. Direto de analytics_daily (persistido).
        "serieDiariaPorEvento": analytics.serie_diaria_por_evento(_analytics_conn, dias=dias),
    }


# ADR-012 (Fase 1): agregado cross-usuário de "Eficiência da IA" (mesmo motor
# de analysis_outcomes.compute_stats que já roda por-usuário em
# /api/analysis-outcomes/stats) pro portal admin. Recomputado 1x/dia pelo
# hook do scheduler (analysis_outcomes.maybe_run, cache_conn=_analytics_conn)
# — o GET só lê o cache. Cold-start (cache ainda não rodou 1x, ex. logo após
# o deploy desta feature): calcula uma vez na hora em vez de deixar o admin
# com tela vazia até a próxima passada diária.
@app.get("/api/analytics/ia-eficiencia")
async def analytics_ia_eficiencia(user: dict = Depends(require_permission("operador_ia.ver"))):
    cached = analytics.get_cache(_analytics_conn, "ia_eficiencia")
    if cached is None:
        analytics.set_cache(_analytics_conn, "ia_eficiencia", analysis_outcomes.compute_stats_all_users(_conn))
        cached = analytics.get_cache(_analytics_conn, "ia_eficiencia")
    return {**cached["value"], "computedAt": cached["computedAt"]}


# ADR-012 (Fase 3): eficiência das operações automáticas (origem manual ×
# automatico × sistema) + correlação com as análises que a IA registrou (via
# snapshotId). Mesmo padrão de cache diário de ia-eficiencia — o hook do
# scheduler (automacao.maybe_refresh_cache) recomputa 1x/dia; cold-start
# calcula uma vez na hora.
@app.get("/api/analytics/automacao")
async def analytics_automacao(user: dict = Depends(require_permission("execucao_automatica.ver"))):
    resumo = analytics.get_cache(_analytics_conn, "automacao_resumo")
    correlacao = analytics.get_cache(_analytics_conn, "automacao_correlacao")
    if resumo is None or correlacao is None:
        analytics.set_cache(_analytics_conn, "automacao_resumo", automacao.resumo_por_origem(_conn))
        analytics.set_cache(_analytics_conn, "automacao_correlacao", automacao.correlacao_analise_operacao(_conn))
        resumo = analytics.get_cache(_analytics_conn, "automacao_resumo")
        correlacao = analytics.get_cache(_analytics_conn, "automacao_correlacao")
    return {**resumo["value"], "correlacaoAnaliseOperacao": correlacao["value"], "computedAt": resumo["computedAt"]}


# ADR-012 (Fase 4): série diária dos campos hoje só em memória (custo de IA,
# orçamento brapi, cache de candles, falhas de push, duração do radar) — o
# que habilita gráfico de tendência em Visão Geral/Custos. Leitura direta
# (sem cache: índice PRIMARY KEY(day,metric) já torna o SELECT barato) —
# quem grava é o hook diário do scheduler (agent._maybe_registrar_metricas_diarias).
@app.get("/api/analytics/tendencias")
async def analytics_tendencias(dias: int = 30, user: dict = Depends(require_permission("observabilidade.ver"))):
    return analytics.series_metricas(_analytics_conn, dias=dias)


# F5 (2026-08-02, decisão do Alex: v1 SÓ VER — sem ação nenhuma). Painel que
# junta o que já existia espalhado (uso de IA, usuários cadastrados, saúde
# do agente) num lugar só.
@app.get("/api/admin/summary")
async def admin_summary(user: dict = Depends(require_permission("observabilidade.ver"))):
    usuarios = db.list_users(_conn)
    return {
        "usuarios": usuarios,
        "totalUsuarios": len(usuarios),
        "usoIA": _usage_snapshot(),
        "agente": agent_mod.status_snapshot(_conn),
        "gate": {
            "hostsFechados": sorted(_GATED_HOSTS),
            "ativo": bool(_GATED_HOSTS),
        },
    }


# ===========================================================================
# ADR-013 — central de administração (web-admin/ deixa de ser SÓ VER). Cada
# rota de ESCRITA grava uma linha em admin_audit_log, sem exceção "por
# enquanto" (restrição do ADR). `apiKey`/`baseUrl` da IA gerenciada NUNCA
# entram aqui — seguem só em env (segredo).
# ===========================================================================
_CONFIG_IA_CAMPOS = ("llmProvider", "llmModel", "llmDailyQuota", "llmRatePerMin", "llmGlobalDailyCap",
                     "llmAlertaGastoPct", "llmAlertaJanelaDias")  # FIX-C38 (fase 5): alerta preventivo
_LLM_PROVIDERS_VALIDOS = ("openai", "anthropic", "google", "local")
# FIX-C38 (fase 5): os 2 campos novos do alerta preventivo de gasto exigem
# número > 0 quando presentes (vazio continua limpando o override, igual aos
# demais campos) — rótulo por campo pra mensagem 400 nomear o que falhou.
_CONFIG_IA_CAMPOS_NUMERICOS_POSITIVOS = {
    "llmAlertaGastoPct": "Limiar de alerta de gasto",
    "llmAlertaJanelaDias": "Janela do alerta de gasto",
}


@app.get("/api/admin/config/ia")
async def admin_config_ia_get(user: dict = Depends(require_permission("llm.configurar"))):
    return {campo: db.admin_config_get(_conn, campo) for campo in _CONFIG_IA_CAMPOS}


@app.put("/api/admin/config/ia")
async def admin_config_ia_put(body: dict = Body(default={}), user: dict = Depends(require_permission("llm.configurar"))):
    """Achados de revisão corrigidos aqui:
    - `llmProvider` só era validado contra a whitelist quando havia `baseUrl`
      (managed.py) — um provider inválido digitado aqui quebrava a IA
      gerenciada pra todo mundo, em silêncio. Valida ANTES de gravar.
    - Não havia como limpar um override (campo vazio era omitido do body,
      nunca chegava a apagar nada). `null`/`""` agora significa "reverter
      pro env" — `db.admin_config_delete`."""
    body = body or {}
    provider = body.get("llmProvider")
    if provider not in (None, "") and provider not in _LLM_PROVIDERS_VALIDOS:
        raise HTTPException(400, "Provider inválido — use um de: " + ", ".join(_LLM_PROVIDERS_VALIDOS) + " (ou vazio para limpar o override).")
    # FIX-C38 (fase 5): valida ANTES de gravar — vazio segue limpando o
    # override (mesma semântica dos demais campos); valor presente tem de
    # converter para número > 0, senão o alerta fica configurado com um
    # limiar/janela inválido e nunca dispara em silêncio.
    for campo, rotulo in _CONFIG_IA_CAMPOS_NUMERICOS_POSITIVOS.items():
        bruto = body.get(campo)
        if campo not in body or bruto in (None, ""):
            continue
        try:
            numero = float(bruto)
        except (TypeError, ValueError):
            numero = None
        if numero is None or numero <= 0:
            raise HTTPException(400, f"{rotulo}: use um número maior que zero (ou vazio para desligar o alerta).")
    alterado = {}
    for campo in _CONFIG_IA_CAMPOS:
        if campo not in body:
            continue
        anterior = db.admin_config_get(_conn, campo)
        bruto = body[campo]
        if campo in _CONFIG_IA_CAMPOS_NUMERICOS_POSITIVOS and bruto not in (None, ""):
            numero = float(bruto)
            # janela em dias fica inteira no payload (7, não 7.0); o limiar
            # de gasto (%) preserva casas decimais quando o admin digitar
            bruto = int(numero) if campo == "llmAlertaJanelaDias" else numero
        novo = None if bruto in (None, "") else bruto
        if anterior == novo:
            continue
        if novo is None:
            db.admin_config_delete(_conn, campo)
        else:
            db.admin_config_set(_conn, campo, novo, updated_by=user["id"])
        audit.record(_conn, user["id"], "config_ia", None, campo, anterior, novo)
        alterado[campo] = novo
    if alterado:
        managed.reset_cache()
    return {"ok": True, "alterado": alterado, "vigente": {c: db.admin_config_get(_conn, c) for c in _CONFIG_IA_CAMPOS}}


@app.get("/api/admin/agent/kill-switch")
async def admin_kill_switch_get(user: dict = Depends(require_permission("execucao_automatica.ver"))):
    # C-37 (REPORT-01) / D-04 (03-CONTEXT.md): a duração é best-effort a
    # partir do audit log — `desde` vem `None` quando não rastreável
    # (ativação por env var `B3_AGENT_KILL`, sem registro de auditoria).
    # `rastreavel` só é True quando `on` E `desde` existem — nunca afirmamos
    # uma duração que não conseguimos provar.
    on = agent_mod.kill_switch_on()
    desde = agent_mod.kill_switch_ligado_desde(_conn) if on else None
    horas = None
    if desde is not None:
        try:
            from datetime import timezone as _tz
            momento = datetime.fromisoformat(desde)
            if momento.tzinfo is None:
                momento = momento.replace(tzinfo=_tz.utc)
            horas = int((datetime.now(_tz.utc) - momento).total_seconds() // 3600)
        except Exception:  # noqa: BLE001 — parse ruim nunca derruba a rota
            horas = None
    return {"on": on, "desde": desde, "horas": horas, "rastreavel": bool(on and desde)}


@app.put("/api/admin/agent/kill-switch")
async def admin_kill_switch_put(body: dict = Body(default={}), user: dict = Depends(require_permission("execucao_automatica.controlar"))):
    anterior = agent_mod.kill_switch_on()
    novo = bool((body or {}).get("on"))
    agent_mod.set_kill_switch(novo, actor=user["id"])
    if anterior != novo:
        audit.record(_conn, user["id"], "agent_kill_switch", None, "on", anterior, novo)
    return {"on": novo}


# C-35 (REPORT-01): par de rotas irmão do kill-switch do agente acima —
# adjacência deliberada (os dois interruptores lidos juntos). MESMAS
# permissões (`execucao_automatica.ver`/`.controlar`) — nenhuma permissão
# nova é criada; o 2º interruptor entra no grupo que já existia.
@app.get("/api/admin/timing-watch/kill-switch")
async def admin_timing_watch_kill_switch_get(user: dict = Depends(require_permission("execucao_automatica.ver"))):
    return {"on": timing_watch.kill_switch_on()}


@app.put("/api/admin/timing-watch/kill-switch")
async def admin_timing_watch_kill_switch_put(body: dict = Body(default={}), user: dict = Depends(require_permission("execucao_automatica.controlar"))):
    anterior = timing_watch.kill_switch_on()
    novo = bool((body or {}).get("on"))
    timing_watch.set_kill_switch(novo, actor=user["id"])
    if anterior != novo:
        audit.record(_conn, user["id"], "timing_watch_kill_switch", None, "on", anterior, novo)
    return {"on": novo}


@app.get("/api/admin/prompts")
async def admin_prompts_get(user: dict = Depends(require_permission("prompts.editar"))):
    """Para cada chave: o texto ATIVO (override do admin, se houver — senão o
    default de código), se há override, e o default de código puro (para a
    UI mostrar "diff contra o padrão")."""
    codigo = defaults.default_llm_prompts()
    overrides = db.prompt_override_get_all(_conn)
    return {
        chave: {
            "ativo": overrides.get(chave, texto_codigo),
            "temOverride": chave in overrides,
            "codigoDefault": texto_codigo,
        }
        for chave, texto_codigo in codigo.items()
    }


@app.put("/api/admin/prompts/{chave}")
async def admin_prompts_put(chave: str, body: dict = Body(default={}), user: dict = Depends(require_permission("prompts.editar"))):
    """Publica um novo default GLOBAL para `chave`. NUNCA sobrescreve a edição
    PESSOAL de um usuário (`PUT /api/llm-prompts`) — essa sempre tem
    prioridade; ver `defaults.publicar_override_admin`/`store._eh_default_antigo`."""
    novo_texto = (body or {}).get("texto")
    if not isinstance(novo_texto, str) or not novo_texto.strip():
        raise HTTPException(400, "Informe o campo 'texto' (não vazio).")
    anterior = db.prompt_override_get(_conn, chave) or defaults.default_llm_prompts().get(chave)
    try:
        defaults.publicar_override_admin(_conn, chave, novo_texto, user["id"])
    except ValueError as e:
        raise HTTPException(400, str(e))
    audit.record(_conn, user["id"], "prompt_default", chave, "texto", anterior, novo_texto)
    return {"ok": True, "chave": chave}


@app.get("/api/admin/users")
async def admin_users_get(user: dict = Depends(require_permission("usuarios.gerenciar"))):
    usuarios = db.list_users(_conn)
    for u in usuarios:
        u["roles"] = rbac.roles_for_user(_conn, u["id"])
    return {"usuarios": usuarios, "gruposDisponiveis": sorted(rbac.GRUPOS) + [rbac.ROLE_ADMIN]}


@app.post("/api/admin/users/{user_id}/roles")
async def admin_users_roles_post(user_id: str, body: dict = Body(default={}), user: dict = Depends(require_permission("usuarios.gerenciar"))):
    """`acao`: 'conceder' | 'revogar'. Sem override de plano nesta rodada
    (decisão do Alex, ADR-013) — só papel de governança."""
    role = str((body or {}).get("role") or "")
    acao = str((body or {}).get("acao") or "conceder")
    if not db.get_user_by_id(_conn, user_id):
        raise HTTPException(404, "Usuário não encontrado.")
    anterior = rbac.roles_for_user(_conn, user_id)
    if acao == "revogar":
        rbac.revoke_role(_conn, user_id, role)
    else:
        # Escalação de privilégio: "usuarios.gerenciar" concede QUALQUER papel
        # (inclusive role_admin, o bootstrap com todas as permissões) — sem
        # este freio, um titular só do grupo "usuarios" vira admin total de
        # si mesmo ou de terceiros. Só quem já É role_admin pode conceder
        # role_admin.
        if role == rbac.ROLE_ADMIN and rbac.ROLE_ADMIN not in rbac.roles_for_user(_conn, user["id"]):
            raise HTTPException(403, "Só um administrador (role_admin) pode conceder o papel role_admin.")
        try:
            rbac.grant_role(_conn, user_id, role, granted_by=user["id"])
        except ValueError as e:
            raise HTTPException(400, str(e))
    novo = rbac.roles_for_user(_conn, user_id)
    audit.record(_conn, user["id"], "user_role", user_id, "roles", anterior, novo)
    return {"ok": True, "userId": user_id, "roles": novo}


@app.get("/api/admin/audit")
async def admin_audit_get(n: int = 200, user: dict = Depends(require_any_admin_permission())):
    # ADR-013: "filtrado ao que a pessoa administra" — ver mapeamento e
    # critério em rbac.ENTIDADES_POR_PERMISSAO. role_admin vê tudo porque a
    # união das próprias permissões já cobre todas as entidades mapeadas.
    eventos = audit.recent(_conn, limit=max(1, min(1000, n)))
    entidades = rbac.entidades_visiveis(_conn, user["id"])
    eventos = [e for e in eventos if e.get("entity") in entidades]
    return {"eventos": eventos}


# ADR-014: handoff de sessão pro web-admin/ dentro do browser in-app do app
# nativo. O bundle do web-admin/ é separado do app consumidor e não conhece
# o token de sessão nativo — em vez de levar o token de sessão de verdade
# (longa duração) pela URL do browser, mint um código de ~90s, uso único, e
# só depois de trocado (endpoint seguinte) uma sessão plena nasce — nunca
# na URL.
@app.post("/api/admin/mobile-handoff")
async def admin_mobile_handoff(user: dict = Depends(require_any_admin_permission())):
    codigo = auth.create_session(_conn, user["id"], ttl_days=90 / 86400)
    return {"codigo": codigo}


@app.post("/api/admin/mobile-handoff/exchange")
async def admin_mobile_handoff_exchange(body: dict = Body(default={})):
    codigo = str(body.get("codigo", "")).strip()
    user = auth.resolve_session(_conn, codigo)
    if not user:
        raise HTTPException(401, "Código de handoff inválido ou expirado.")
    rbac.ensure_bootstrap_role(_conn, user)
    if not rbac.permissions_for_user(_conn, user["id"]):
        # NÃO revoga aqui: um token de sessão comum passado por engano/curiosidade
        # não pode derrubar a sessão de quem não tinha nada a ver com handoff.
        raise HTTPException(403, "Requer algum papel administrativo.")
    auth.revoke_session(_conn, codigo)  # uso único — nunca reaproveitável
    token = auth.create_session(_conn, user["id"])
    return {"token": token, "user": _public_user(user)}


# FASE 8B (diagnóstico): carimbo de build do BACKEND — confirma qual código o
# Railway está rodando (o front tem o dele em web/src/version.js).
SERVER_BUILD_ID = "F10-20260831-01"  # Fase 13 Plano 05: publica os 3 contadores + gate iOS (front republicado).
# Normalmente sincronizado pelo entregar.sh a partir de web/src/version.js; num deploy
# SÓ de backend (sem rebuild do front) bumpamos aqui para /api/health rastrear o servidor.


@app.get("/api/health")
async def health(scope: Optional[str] = Depends(current_scope)):
    return {"ok": True, "build": SERVER_BUILD_ID}


# ADR-23 (Fase 4) — contrato mínimo de observabilidade publicado para o
# console admin.semente.dev agregar. Na RAIZ (não sob /api/): o contrato é
# literalmente "GET <sistema>/observabilidade" — precisa vir ANTES do mount
# catch-all da raiz no fim do arquivo, senão ele engole o caminho (mesma
# classe de defeito que /admin já tinha que evitar; ver
# test_observabilidade_registrada_antes_do_mount_raiz).
#
# Autenticação — dois caminhos, NUNCA público (T-eqm-06): chave de máquina
# (X-Observabilidade-Chave, comparação constant-time) OU sessão com
# observabilidade.ver. B3_OBSERVABILIDADE_CHAVE ausente/vazia desliga o
# caminho de máquina (fail-closed) — não vira "qualquer um passa". Não usa
# Depends(require_permission(...)) porque aquele exige sessão e não conhece
# a chave de máquina; os dois caminhos são resolvidos aqui no corpo.
@app.get("/observabilidade")
async def observabilidade_raiz(request: Request):
    chave_recebida = request.headers.get("x-observabilidade-chave") or ""
    chave_esperada = os.environ.get("B3_OBSERVABILIDADE_CHAVE") or ""
    via_chave_maquina = bool(chave_esperada) and hmac.compare_digest(chave_recebida, chave_esperada)
    if not via_chave_maquina:
        cabecalho_auth = request.headers.get("authorization") or ""
        partes = cabecalho_auth.split(None, 1)
        user = None
        if len(partes) == 2 and partes[0].lower() == "bearer":
            user = auth.resolve_session(_conn, partes[1].strip())
        if not user:
            raise HTTPException(401, "Autenticação necessária: chave de máquina (X-Observabilidade-Chave) ou sessão administrativa.")
        rbac.ensure_bootstrap_role(_conn, user)
        if "observabilidade.ver" not in rbac.permissions_for_user(_conn, user["id"]):
            raise HTTPException(403, "Requer a permissão 'observabilidade.ver'.")

    # Nenhuma coleta nova, nenhuma chamada a fonte externa aqui dentro — é
    # uma rota de STATUS e não pode gastar orçamento da brapi nem cota de
    # LLM. Tudo abaixo já existe (agent.status_snapshot, brapi_budget,
    # obslog, timing_watch) — só rearranjado no formato do contrato.
    snap = agent_mod.status_snapshot(_conn)
    orcamento = brapi_budget.snapshot()
    logs = obslog.stats()

    alertas = []
    if snap["killSwitch"]:
        alertas.append({
            "severidade": "critico", "titulo": "Execução automática desligada (kill-switch)",
            "detalhe": "O Operador não executa ordens automáticas enquanto o kill-switch estiver ligado.",
            "acao": "Desligar em Execução automática",
        })
    if not snap["heartbeat"]["lacoVivo"]:
        alertas.append({
            "severidade": "critico", "titulo": "Laço do agente sem heartbeat recente",
            "detalhe": "O ciclo do Operador não bateu dentro da janela esperada.",
            "acao": "Ver Perfil → Observabilidade",
        })
    if snap["killSwitch"] and snap["ordensPendentes"]["total"] > 0:
        # C-35/incidente v1.0: kill-switch ligado + ordem pendente presa é
        # exatamente o mascaramento que já derrubou a base por 2,5 dias.
        alertas.append({
            "severidade": "critico", "titulo": "Ordens pendentes com kill-switch ligado",
            "detalhe": f"{snap['ordensPendentes']['total']} ordem(ns) pendente(s) presa(s) enquanto o Operador está desligado.",
            "acao": "Revisar ordens pendentes",
        })
    if timing_watch.kill_switch_on():
        alertas.append({
            "severidade": "atencao", "titulo": "Push do gatilho desligado (2º kill-switch)",
            "detalhe": "Avisos automáticos de gatilho de timing não estão sendo enviados.",
            "acao": "Ver Perfil → Observabilidade",
        })
    for fatia, info in (orcamento.get("fatias") or {}).items():
        if info.get("degradado"):
            alertas.append({
                "severidade": "atencao", "titulo": f"Orçamento da brapi degradado (fatia '{fatia}')",
                "detalhe": "A fatia passou de 80% do limite diário de requisições.",
                "acao": "Ver Perfil → Observabilidade",
            })
    erros_desde_boot = sum((v or {}).get("error", 0) for v in (logs.get("porCategoria") or {}).values())
    if erros_desde_boot > 0:
        alertas.append({
            "severidade": "atencao", "titulo": f"{erros_desde_boot} erro(s) registrado(s) desde o boot",
            "detalhe": "Erros no log estruturado desde a última subida do processo.",
            "acao": "Perfil → Observabilidade",
        })

    # Semáforo derivado da PRÓPRIA lista — nunca uma segunda regra paralela
    # que possa discordar dela (o defeito clássico deste tipo de endpoint).
    situacao = "critico" if any(a["severidade"] == "critico" for a in alertas) else ("atencao" if alertas else "ok")

    proximas = []
    if snap.get("proximaPassadaEmS") is not None:
        proximas.append({"tipo": "passada_agente", "emS": snap["proximaPassadaEmS"]})
    radar = snap.get("radarDiario") or {}
    if radar.get("date"):
        proximas.append({"tipo": "radar_diario", "data": radar.get("date"), "atLabel": radar.get("atLabel")})

    return {
        "situacao": situacao,
        "alertas": alertas,
        # já vem da mais recente para a mais antiga (agent.RUN_HISTORY).
        # Contagens, nunca identidade — mesma regra de ordensPendentes/
        # protecaoSemOperador em status_snapshot.
        "ultimas_execucoes": [
            {"quando": p.get("at"), "duracaoS": p.get("duracaoS"), "usuarios": p.get("usuarios"),
             "executadas": p.get("executadas"), "erros": p.get("erros") or []}
            for p in (snap.get("passadas") or [])[:10]
        ],
        "proximas": proximas,
    }


# Fase 2 (MERC-01/D-08): status real do pregão, consumido pela tela de LOGIN
# ANTES de autenticar — por isso é PÚBLICA de propósito, sem
# `Depends(current_scope)`/`require_user` e sem NENHUM parâmetro de sessão
# (essa ausência é a própria mitigação de T-02-08: a rota não pode nem
# acidentalmente ler estado de usuário). É segura porque devolve só um
# booleano de calendário público — nenhum `user_id`, nada de carteira —
# calculado inteiramente por `pregao.py` (fonte única), nunca recalculado
# aqui.
@app.get("/api/market/status")
async def market_status():
    from . import pregao  # import local: sem ciclo (mesmo padrão de agent.py:216)
    agora = datetime.now(pregao.BRT)
    return {
        "aberto": pregao.in_market_hours(),
        "diaDePregao": pregao.is_trading_day(agora.date()),
        "abertura": "%02d:%02d" % pregao.ABERTURA,
        "fechamento": "%02d:%02d" % pregao.FECHAMENTO,
        "agoraBRT": agora.strftime("%d/%m %H:%M"),
        "afterMarket": pregao.after_market_ligado(),
    }


@app.get("/api/state")
async def get_state(scope: Optional[str] = Depends(current_scope)):
    return store.public_state(_conn, user_id=scope)


# ---- Config (persistente no servidor / web) ----
@app.put("/api/config")
async def put_config(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    store.set_config(_conn, body or {}, user_id=scope)
    return store.public_state(_conn, user_id=scope)


@app.post("/api/config/test")
async def test_config(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    cfg = dict(store.get(_conn, "config", user_id=scope))
    cfg.update({k: v for k, v in (body or {}).items() if v is not None})
    if isinstance(body, dict) and body.get("apiKey") == "":
        cfg.pop("apiKey", None)
    return await llm.test_connection(cfg)


@app.post("/api/reset")
async def reset(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    """Recomeca a carteira simulada do zero, com o orcamento inicial."""
    return store.reset_portfolio(_conn, user_id=scope)


# ---- Skill ----
@app.put("/api/skill")
async def put_skill(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    # FASE 8B (R2): body.modo escolhe a seção (skill × skillOperador)
    store.set_skill(_conn, body.get("name"), body.get("text"), user_id=scope, modo=body.get("modo"))
    return store.public_state(_conn, user_id=scope)


@app.post("/api/skill/restore")
async def restore_skill(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    store.restore_skill(_conn, user_id=scope, modo=(body or {}).get("modo"))
    return store.public_state(_conn, user_id=scope)


# ---- Config de LLMs e Prompts (FASE 2) ----
@app.put("/api/llm-prompts")
async def put_llm_prompts(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    store.set_llm_prompts(_conn, body or {}, user_id=scope)
    return store.public_state(_conn, user_id=scope)


# ---- Watchlist ----
@app.post("/api/snapshot")
async def post_snapshot(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    """Fase B1: grava o snapshot de patrimonio do dia (um por dia; sobrescreve)."""
    store.upsert_snapshot(_conn, body or {}, user_id=scope)
    return store.public_state(_conn, user_id=scope)


@app.put("/api/watchlist")
async def put_watchlist(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    # Fase 12 (CAP-01/D-02): este endpoint era o bypass do cap (front usa
    # ele no quick-add do push e na selecao em massa do catalogo). Compara o
    # tamanho NORMALIZADO (nao o cru do body, senao ticker desconhecido/
    # repetido gera recusa falsa — CAP-05). So barra CRESCIMENTO (D-03);
    # quem ja tinha mais de 10 nao perde nada (D-04, grandfather clause).
    novos = body.get("tickers")
    if novos is not None and not isinstance(novos, list):
        # WR-03 (12-REVIEW.md): sem isto, um `tickers` truthy nao-lista (string,
        # bool, dict) cai direto em normalize_watchlist — uma string itera por
        # CARACTERE (zera a watchlist em silencio, 200) e um bool nao-iteravel
        # estoura TypeError sem tratamento (vira 500 opaco pro cliente).
        raise HTTPException(400, "tickers deve ser uma lista de codigos.")
    novos = novos or []
    # WR-01 (12-REVIEW.md): leitura+checagem+escrita precisam da MESMA trava —
    # sem ela, dois PUT concorrentes leem o mesmo `atual` e o gate compara
    # contra um estado que já ficou stale quando a escrita acontece.
    with store.WATCHLIST_LOCK:
        final = store.normalize_watchlist(_conn, novos, user_id=scope)
        atual = store.get(_conn, "watchlist", user_id=scope)
        if len(final) > len(atual):
            # WR-02 (12-REVIEW.md): hook honesto pro caso BULK — can_add_ticker
            # espera "tamanho ANTES de uma adição"; aqui é uma troca da lista
            # inteira, então comparamos o tamanho FINAL direto, sem valor sintético.
            allowed, reason = plan.can_grow_watchlist_to(len(final), plan=_plano_do_escopo(scope))
            if not allowed:
                raise HTTPException(402, reason)
        store.set_watchlist(_conn, novos, user_id=scope)
    return store.public_state(_conn, user_id=scope)




@app.post("/api/watchlist/add")
async def watchlist_add(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    """Adiciona um ticker digitado pelo usuario. A EXISTENCIA e confirmada pelo
    Yahoo Finance (sufixo .SA) — a IA nao decide isso."""
    t = _normalize_ticker(str(body.get("ticker", "")))
    if not t or len(t) < 4:
        raise HTTPException(400, "Informe um ticker valido da B3 (ex.: PETR4).")
    try:
        q = await candle_provider.get_quote(t)
        transient = False
    except yahoo.QuoteUnavailable:
        q, transient = None, True
    except Exception:
        q, transient = None, False
    res = tickers.validation_outcome(q, transient)
    if res["status"] == "unavailable":
        raise HTTPException(503, "Cotacoes indisponiveis no momento (Yahoo). Tente novamente em instantes.")
    if res["status"] != "ok":
        raise HTTPException(404, f"Ticker {t} nao encontrado na B3 (Yahoo Finance). Verifique o codigo.")
    name = res["n"]
    # WR-01 (12-REVIEW.md): leitura+checagem+escrita precisam da MESMA trava —
    # sem ela, dois ADD concorrentes de tickers DIFERENTES leem o mesmo `wl`
    # e o último a escrever `wl + [t]` sobrescreve a adição do outro.
    with store.WATCHLIST_LOCK:
        # GANCHO FREEMIUM (hoje sempre permite): limite de ativos do tier gratuito.
        allowed, reason = plan.can_add_ticker(len(store.get(_conn, "watchlist", user_id=scope)),
                                              plan=_plano_do_escopo(scope))
        if not allowed:
            raise HTTPException(402, reason)  # 402 Payment Required (fase futura)
        store.add_custom(_conn, t, name, user_id=scope)
        wl = store.get(_conn, "watchlist", user_id=scope)
        if t not in wl:
            store.set_watchlist(_conn, wl + [t], user_id=scope)
    out = store.public_state(_conn, user_id=scope)
    out["added"] = {"t": t, "n": name, "price": res["price"], "change": res["change"]}
    return out


@app.get("/api/watchlist/quota")
async def watchlist_quota(scope: Optional[str] = Depends(current_scope)):
    """Fase 13 (CAP-06/CAP-12): fonte unica de `count`/`limit`/`planId` da
    watchlist para o cliente — o `deviceStore` do iOS grava direto no
    localStorage e NAO pode hardcodar `10`; este endpoint e a UNICA fonte
    de `max_watchlist` fora de `plan.py`. Contrato travado (consumido pelos
    planos 02/03): {"count": int, "limit": int|null, "planId": "free"|"pro"}.
    `limit` null == plano sem teto (pro) — o front OMITE o contador (D-03).
    Read-only: nao muta estado, so le.

    DIFERENCA deliberada em relacao a `/api/ai/quota`: NAO ha early-return
    especial para escopo anonimo. `_plano_do_escopo(None)` ja degrada para
    `plan.ACTIVE_PLAN` (= PLAN_FREE, fail-closed), e a watchlist anonima
    existe de verdade no balde `user_id=None` — anonimo recebe `limit: 10`
    real, coerente com o gate que `POST /api/watchlist/add` ja aplica ao
    mesmo escopo desde a Fase 12."""
    plano = _plano_do_escopo(scope)
    count = len(store.get(_conn, "watchlist", user_id=scope) or [])
    return {"count": count, "limit": plano.get("max_watchlist"), "planId": plano.get("id")}


@app.put("/api/profile")
async def put_profile(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    store.set_profile(_conn, body or {}, user_id=scope)
    return store.public_state(_conn, user_id=scope)


@app.get("/api/validate/{ticker}")
async def validate(ticker: str, scope: Optional[str] = Depends(current_scope)):
    """Confirma no Yahoo (sufixo .SA) se o ticker existe. Nao altera estado —
    usado pelo app nativo, que guarda o custom no proprio aparelho."""
    t = _normalize_ticker(ticker)
    if not t or len(t) < 4:
        raise HTTPException(400, "Informe um ticker valido da B3 (ex.: PETR4).")
    try:
        q = await candle_provider.get_quote(t)
        transient = False
    except yahoo.QuoteUnavailable:
        q, transient = None, True
    except Exception:
        q, transient = None, False
    res = tickers.validation_outcome(q, transient)
    if res["status"] == "unavailable":
        raise HTTPException(503, "Cotacoes indisponiveis no momento (Yahoo). Tente novamente em instantes.")
    if res["status"] != "ok":
        raise HTTPException(404, f"Ticker {t} nao encontrado na B3 (Yahoo Finance). Verifique o codigo.")
    return {"ok": True, "t": res["t"], "n": res["n"], "price": res["price"], "change": res["change"]}


# ---- Cotacoes ----
@app.get("/api/quotes")
async def quotes(symbols: Optional[str] = None, scope: Optional[str] = Depends(current_scope)):
    if symbols:
        wanted = [_normalize_ticker(s) for s in symbols.split(",")]
        wanted = [w for w in wanted if len(w) >= 4]
    else:
        wl = store.get(_conn, "watchlist", user_id=scope)
        pos = [p["t"] for p in store.get(_conn, "positions", user_id=scope)]
        wanted = list(dict.fromkeys(wl + pos))
    data = await candle_provider.get_quotes(wanted)
    return {"quotes": data, "at": now_str()}


@app.get("/api/history/{ticker}")
async def history(ticker: str, period: Optional[str] = None, scope: Optional[str] = Depends(current_scope)):
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    h = await candle_provider.get_history(t, rng=candles_mod.period_to_range(period))  # Objetivo 4
    h["candles"] = indicators.sanitize_candles(h.get("candles"))
    return h


# FIX-C03: série diária do Ibovespa para o Passo 8 comparar com a carteira
# simulada. Sem parâmetro de símbolo — `benchmark.SIMBOLO` é constante,
# nunca vem do cliente (T-04-04: senão a rota vira proxy aberto pro Yahoo).
# `scope` fica só por consistência com as demais rotas de dado de mercado;
# a curva é pública, não decide nada por conta.
@app.get("/api/benchmark/ibov")
async def benchmark_ibov(period: Optional[str] = None, scope: Optional[str] = Depends(current_scope)):
    try:
        return await benchmark.serie_ibov(period)
    except benchmark.BenchmarkIndisponivel:
        raise HTTPException(502, "Comparação com o Ibovespa indisponível agora.")


# ---- Analise tecnica: candles + indicadores (serie continua ~1 ano) ----
_TECH_KEEP = 252         # ~1 ano util exibido (calculo usa warmup maior)
import re as _re
def _normalize_ticker(s: str) -> str:
    return tickers.normalize_ticker(s)





@app.get("/api/technical/models")
async def technical_model_list(scope: Optional[str] = Depends(current_scope)):
    return {"models": [{"id": k, **v} for k, v in technical_models.MODELS.items()]}


async def _options_status_for_llm(t: str) -> dict:
    try:
        chain = await _get_options_for_status(t)
        calls = chain.get("calls") or []
        puts = chain.get("puts") or []
        return {
            "available": bool((chain.get("expirations") or []) or calls or puts),
            "source": chain.get("source") or options_provider.provider_name(),
            "expiration": chain.get("expiration"),
            "expirationsCount": len(chain.get("expirations") or []),
            "callsCount": len(calls),
            "putsCount": len(puts),
            "warning": chain.get("warning"),
        }
    except Exception as e:  # noqa: BLE001
        return {
            "available": False,
            "source": options_provider.provider_name(),
            "reason": str(e) or "O provedor de opções não retornou cadeia para este ativo.",
        }

def _degradado_spot() -> bool:
    """C-30 (REPORT-01): indicador de orçamento nunca pode derrubar o painel
    técnico. Devolve False quando o provedor vigente não é brapi (não existe
    orçamento brapi para degradar) ou quando o cálculo falha por qualquer
    motivo — principio 4 do CLAUDE.md exige mostrar o estado correto, e
    "não sei" aqui é False, nunca uma invenção."""
    try:
        if candle_provider.provider_name() != "brapi":
            return False
        return bool(brapi_budget.degradado("spot"))
    except Exception:  # noqa: BLE001
        return False


@app.get("/api/technicals/{ticker}")
async def technicals(ticker: str, period: Optional[str] = None, scope: Optional[str] = Depends(current_scope)):
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    # FASE 1 (STU): o gráfico mostra EXATAMENTE os números que N1/N2/N3 leem —
    # candle_cache + compute + slice agora vivem no snapshot, fonte única.
    # O cache de payload de 10 min foi removido: ele mascarava snapshots mais
    # novos (gráfico com snapshotId diferente do Radar); o STU já é fingerprint-
    # cached e o candle_cache já protege a rede (fresh < 45s).
    try:
        snap = await technical_snapshot.get(t, period, lambda rng: candle_provider.get_history(t, rng=rng))
    except ValueError:
        raise HTTPException(502, "Sem historico para " + t)
    payload = {
        "t": t,
        "currency": snap.get("currency", "BRL"),
        "candles": snap["candles"],
        "indicators": snap["indicators"],
        "summary": snap["summary"],
        "periodChangePct": snap["variacaoPeriodoPct"],
        "snapshotId": snap["snapshotId"],
        "snapshotAt": snap["asOf"],
        "at": now_str(),
        # C-11/C-30 (REPORT-01): proveniência real do dado + estado do
        # orçamento brapi (TTL 3x quando degradado), para o painel técnico
        # nunca mais afirmar uma fonte fixa incorreta nem esconder dado mais
        # velho que o habitual.
        "source": snap.get("source"),
        "degradado": _degradado_spot(),
    }
    return payload


# ---- BLOCO D: AutoFill nativo do iOS (Chaveiro) ----
# O iOS só oferece usuário+senha salvos dentro do app se o domínio declarar o
# vínculo via este arquivo + capability "Associated Domains" no Xcode com
# `webcredentials:boris.semente.dev`. O appID vem da env
# B3_APPLE_APP_ID no formato TEAMID.bundleid (ex.: ABCDE12345.com.b3.agente).
@app.get("/.well-known/apple-app-site-association")
async def apple_app_site_association():
    app_id = os.environ.get("B3_APPLE_APP_ID", "").strip()
    apps = [app_id] if app_id else []
    return JSONResponse({"webcredentials": {"apps": apps}}, media_type="application/json")


# ---- BLOCO 3: Radar de mercado ----
# Varre o universo (default: aproximação do IBOV; sobreponível por env
# B3_SCAN_UNIVERSE ou ?tickers=) com o período do usuário e devolve a lista
# rankeada de condições técnicas detectadas + disclaimer no payload. A 1ª
# varredura aquece o candle_cache (pode levar dezenas de segundos); as
# seguintes são rápidas (cache fresh/delta + cache do resultado por 60s).
# qa/36 (F10.2): anexa o fundamento (score A/B/C + métricas) a cada ativo do
# scan — SÓ do cache (get_cached nunca vai à rede; o job semanal aquece). Fora
# do scanner de propósito: mantém o scanner sem dependência de db e o
# fundamento atualiza independente do resultado do dia. Ticker não aquecido →
# sem campo (a UI mostra "sem dado"), nunca inferência.
def _enrich_fundamentos_sync(payload: dict) -> dict:
    # Best-effort TOTAL: o fundamento é um overlay — NADA aqui pode derrubar o
    # scan (o Radar/Mesa é core). Qualquer falha → devolve o payload intacto.
    try:
        results = (payload or {}).get("results")
        if not isinstance(results, list):
            return payload
        for r in results:
            f = fundamentals.get_cached(_conn, r.get("ticker") or "")
            if f and f.get("score"):
                r["fundamento"] = {k: f.get(k) for k in
                                   ("score", "pl", "roe", "dy", "margemLiquida",
                                    "dividaEbitda", "crescReceita", "crescLucro",
                                    "setor", "referencia", "fonte")}
    except Exception as e:  # noqa: BLE001 — overlay nunca quebra o scan
        print(f"[fundamentals] enrich falhou (scan segue): {e}")
    return payload


async def _enrich_fundamentos(payload: dict) -> dict:
    """qa/42 (FinOps): o overlay faz UMA leitura SQLite por resultado — 74 no
    universo default. Rodava SÍNCRONO dentro do `async def scan`, travando o
    event loop inteiro (1 worker: ninguém mais é atendido). `db.py` é
    thread-local, então a thread tem conexão própria — seguro."""
    return await asyncio.to_thread(_enrich_fundamentos_sync, payload)


# qa/37 (F10.2): diagnóstico de fundamento por ticker — confirma a fonte real
# (bolsai/brapi) e o parse assim que a BOLSAI_API_KEY entra no Railway (o
# cliente da bolsai foi construído contra o formato documentado, sem validação
# ao vivo). Cache-first (TTL 7d); ?force=1 refaz o fetch. I/O bloqueante via
# thread (não congela o event loop). Dado público, sem escopo.
@app.get("/api/fundamentals/{ticker}")
async def fundamentals_one(ticker: str, force: Optional[int] = None):
    f = await asyncio.to_thread(fundamentals.get_fundamentals, _conn, ticker, force=bool(force))
    return {
        "ticker": ticker.upper(),
        "temChaveBolsai": bool(fundamentals._bolsai_key()),
        "fundamento": f,
    }


# Serializa a revalidação do Radar (varredura do universo inteiro): sem ele,
# o primeiro acesso após um fechamento de pregão dispara uma varredura por
# usuário simultâneo.
_revalida_radar = asyncio.Lock()


@app.get("/api/scan")
async def scan(period: Optional[str] = None, tickers: Optional[str] = None,
               force: Optional[int] = None, scope: Optional[str] = Depends(current_scope)):
    # FASE 4 (1.3) — Radar 1x/dia: subconjunto explícito (watchlist) segue
    # computando na hora (barato); universo completo serve o RESULTADO DO DIA
    # armazenado, e só recomputa no primeiro acesso do dia ou com ?force=1
    # (botão "Varrer novamente"). A varredura manual substitui a do dia.
    # qa/42 (FinOps): todo o I/O SQLite deste caminho vai para thread — o
    # overlay lê 74 linhas e o store_result grava ~150 KB de JSON; síncronos
    # aqui, congelavam o event loop a cada Radar.
    p = candles_mod.normalize_period(period)
    if tickers:
        payload = await scanner.run_scan(period=p, universe=tickers, fetch=candle_provider.get_history)
        # UM ATIVO, UMA LEITURA: o que a Watchlist acabou de calcular passa a
        # valer para o Radar também. Sem isto, as duas telas exibiam vereditos
        # contraditórios do mesmo papel durante o pregão.
        await asyncio.to_thread(radar_daily.merge_leituras, _conn, p, payload.get("results"))
        return await _enrich_fundamentos(payload)
    if not force:
        stored = await asyncio.to_thread(radar_daily.get_stored, _conn, p)
        if stored:
            return await _enrich_fundamentos(stored)
        # Vencida (um pregão fechou depois dela) e sem varredura do dia ainda.
        # O lock evita que N usuários abrindo o Radar no mesmo minuto disparem
        # N varreduras do universo inteiro — a 1ª grava, as demais servem.
        async with _revalida_radar:
            stored = await asyncio.to_thread(radar_daily.get_stored, _conn, p)
            if stored:
                return await _enrich_fundamentos(stored)
            payload = await scanner.run_scan(period=p, fetch=candle_provider.get_history)
            salvo = await asyncio.to_thread(radar_daily.store_result, _conn, p, payload,
                                            origem="revalidação")
            return await _enrich_fundamentos(salvo)
    payload = await scanner.run_scan(period=p, fetch=candle_provider.get_history)
    salvo = await asyncio.to_thread(radar_daily.store_result, _conn, p, payload, origem="manual")
    return await _enrich_fundamentos(salvo)


# FASE 1 (N1) — aprofundamento IA do Radar: híbrido por custo (scanner grátis
# varre tudo; IA só no top-N por confluência). Cache por (ticker, período, dia).
@app.get("/api/scan/progress")
async def scan_progress():
    """BLOCO B1 — progresso da varredura para o gauge da UI (sem auth: é
    telemetria de processo, sem dado de usuário)."""
    return dict(scanner.SCAN_PROGRESS)


@app.get("/api/scan/deep/estimate")
async def scan_deep_estimate(period: Optional[str] = None, topN: Optional[int] = None,
                             tickers: Optional[str] = None, appMode: Optional[str] = None,
                             scope: Optional[str] = Depends(current_scope)):
    """Custo ANTES de rodar: quantas chamadas novas de IA o deep fará agora."""
    p = candles_mod.normalize_period(period)
    cfg = store.get(_conn, "config", user_id=scope) or {}
    n = scan_deep.resolve_top_n(topN, cfg)
    # FASE 8B (B3): cache do deep é por MODO — iOS manda ?appMode; web usa a config
    modo = appMode or (cfg or {}).get("appMode")
    payload = await scanner.run_scan(period=p, universe=tickers, fetch=candle_provider.get_history)
    # Mesma identidade de leitor da rota que gasta — senão a estimativa promete
    # "já está em cache" e o deep cobra a chamada assim mesmo.
    leitor = scan_deep.leitor_fp(store.get(_conn, "profile", user_id=scope), cfg)
    return scan_deep.estimate(payload, n, p, modo=modo, leitor=leitor)


@app.post("/api/scan/deep")
async def scan_deep_run(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    p = candles_mod.normalize_period((body or {}).get("period"))
    config = (body or {}).get("config") or store.get(_conn, "config", user_id=scope) or {}
    # FASE 8B (B3): modo do cliente — o iOS manda appMode no corpo (local-first);
    # o web cai na config do escopo. Capturado ANTES do managed recriar a config.
    modo = (body or {}).get("appMode") or (config or {}).get("appMode")
    profile = (body or {}).get("profile") or store.get(_conn, "profile", user_id=scope)
    n = scan_deep.resolve_top_n((body or {}).get("topN"), config)
    # qa/42 (FinOps): `custo=n` — este request dispara ATÉ n chamadas de LLM
    # (1 por ticker do top-N). Reservar na cota impede o overrun de +9.
    ai_config, _consume_ai = _ai_apply_managed(scope, config, custo=n)  # cota/rate ANTES de gastar
    payload = await scanner.run_scan(period=p, universe=(body or {}).get("tickers"), fetch=candle_provider.get_history)
    # F1/A6b: a passada intraday GLOBAL (se fresca) vira o 2º timeframe REAL do
    # N1 — lida UMA vez por request (kv, sem fetch); por ticker só o resumo.
    from . import intraday as intraday_mod
    from . import timing as timing_mod
    intra_stored = await asyncio.to_thread(intraday_mod.get_stored, _conn)
    intra_fresca = intraday_mod.passada_fresca(intra_stored)

    async def deep_call(item):
        t = item["ticker"]
        # FASE 1 (STU): contexto E setups saem do MESMO snapshot do scan —
        # antes o deep refazia build_context com outro corte e podia divergir.
        snap = await technical_snapshot.get(t, p, lambda rng: candle_provider.get_history(t, rng=rng))
        sres = snap["setups"]
        plano = setups.plano_do_resultado(sres, close=snap.get("close"))
        setups_payload = {
            "snapshotId": snap["snapshotId"],
            "confluencia": sres.get("confluencia"), "veredito": sres.get("veredito"),
            "melhorSetup": sres.get("melhor"), "setups": sres.get("setups"),
            "condicoesDetectadas": snap["conditions"],
            # FASE 8B (B3): o plano determinístico entra no pacote — a mesa é
            # OBRIGADA a ser coerente com ele (regra 10 do OPERADOR_PRO).
            "planoOperacional": plano,
        }
        # F1/A6b: bloco intraday15m no pacote => dataQuality.multiTimeframe
        # vira true e o teto de `confianca` do N1 sobe para 'alta' (PROCESSO
        # §9). enriquecer_contexto é pura e copia — o snap é cacheado e
        # compartilhado; mutar o dict do cache vazaria o bloco.
        contexto = timing_mod.enriquecer_contexto(
            snap["context"], intraday_mod.resumo_do_ticker(intra_stored, t), intra_fresca)
        with llm.collect_usage() as _uso:  # qa/45: custo desta leitura do Radar
            res = await llm.analyze_deep(ai_config, profile, t, contexto, setups_payload, modo=modo)
        _consume_ai()  # cota gasta POR CHAMADA bem-sucedida (cache não gasta)
        try:
            ai_activity.registrar_uso(_conn, scope=scope, ticker=t, tipo="Radar", usos=_uso)
        except Exception as e:  # noqa: BLE001
            print(f"[ai-activity] registro N1 falhou p/ {t}: {e}")
        # qa/30 (Fase A): registra a análise pra autoavaliação futura (10
        # pregões — job em analysis_outcomes.py). Só quando há plano acionável
        # (COMPRAR/VENDER com stop/alvo1 definidos); AGUARDAR/NÃO OPERAR não
        # tem risco definido pra virar estatística. Best-effort: nunca derruba
        # a resposta ao usuário.
        try:
            if plano.get("decisao") in (setups.DECISAO_COMPRAR, setups.DECISAO_VENDER):
                analysis_outcomes.registrar(
                    _conn, ticker=t, modo=modo, tipo="n1",
                    modelo=f"{ai_config.get('provider')}:{ai_config.get('model')}",
                    setup=sres.get("melhor"), recomendacao=res.get("planoEstudo"),
                    stop=plano.get("stop"), alvo=plano.get("alvo1"),
                    preco=snap.get("close"), snapshot_id=snap.get("snapshotId"),
                    confianca=res.get("confianca"),  # qa/35 P2c: calibração declarada×real
                    # qa/44 (B, ADR-009): regime NO MOMENTO da análise — classificado
                    # aqui, não lido de snap (o A anexa regime ao resultado do SCAN,
                    # não ao snapshot técnico que o N1 recebe).
                    regime=regime.classificar(snap).get("regime"),
                    user_id=scope,
                    # ADR-015 / ADR15-01: `entrada`/`alvo2`/`rr2` reusam o `plano`
                    # já em escopo (não recalcular o plano do resultado nem
                    # refazer o snapshot). `alvo=plano.get("alvo1")` acima
                    # PERMANECE —
                    # trocar a barreira de resolução de alvo1 para alvo2 seria
                    # uma segunda mudança de comportamento fora do escopo deste
                    # plano (06-CONTEXT.md, ADR15-02, último bullet).
                    entrada=plano.get("entrada"), alvo2=plano.get("alvo2"), rr2=plano.get("rr2"),
                    confluencia=sres.get("confluencia"),
                    # setups.py:602-612 põe entrada=close (não o gatilho) quando o
                    # gatilho já rompeu dentro da zona de perseguição; nesse caso
                    # plano["tipo"] vale "a mercado (gatilho já rompido, dentro da
                    # zona)". Sem esse marcador o Plano 02 exigiria "toque no
                    # gatilho" num plano cuja entrada é IMEDIATA — um gap contra a
                    # posição no candle seguinte (o caso ADVERSO) viraria
                    # sem_gatilho e sairia do denominador: o mesmo viés otimista
                    # que o ADR-015 existe para matar. startswith("a mercado") e
                    # não igualdade com a frase inteira: o prefixo é o contrato,
                    # o resto da frase é explicação para humano.
                    entrada_a_mercado=str(plano.get("tipo") or "").startswith("a mercado"),
                )
        except Exception as e:  # noqa: BLE001 — registro é best-effort
            print(f"[analysis-outcomes] registro N1 falhou p/ {t}: {e}")
        return res

    try:
        # O cache do N1 é GLOBAL: sem a identidade do leitor, a leitura escrita
        # para um perfil era servida a outro, e a resposta paga com a chave de
        # um usuário ia para outro.
        return await scan_deep.run_deep(payload, n, p, deep_call, modo=modo,
                                        leitor=scan_deep.leitor_fp(profile, ai_config))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, llm.public_error(e))


# ---- Analise pela LLM (config opcional no corpo, para o handset) ----
@app.post("/api/technical/analyze/{ticker}")
async def analyze_technical_model(ticker: str, body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    body = body or {}
    model = technical_models.normalize_model(body.get("model") or body.get("technicalModel"))
    config = body.get("config") or store.get(_conn, "config", user_id=scope)
    # FASE 8B (B3): captura o modo ANTES do managed (que pode recriar a config)
    modo = (config or {}).get("appMode")
    # FIX-C01: o gate de plano/cota pode negar (402, ex.: cota gerenciada
    # esgotada) — em vez de estourar pro cliente, marca a IA como indisponível
    # e segue com o fallback determinístico (nunca 502 por falta de crédito).
    ia_indisponivel = None
    _consume_ai = lambda: None
    try:
        config, _consume_ai = _gate_analise(scope, config)
    except HTTPException as e:
        if e.status_code == 402:
            ia_indisponivel = {"code": "quota", "mensagem": str(e.detail)}
        else:
            raise
    # FASE 8B (R2): a instrução do agente é POR MODO — a mesa usa a skill do
    # operador (iOS manda a certa no corpo; web escolhe pela config do escopo).
    skill = body.get("skill") or store.get(_conn, "skillOperador" if modo == "operador" else "skill", user_id=scope)
    profile = body.get("profile") or store.get(_conn, "profile", user_id=scope)
    account = body.get("account") or {
        "cash": store.get(_conn, "cash", user_id=scope),
        "budget": (store.get(_conn, "config", user_id=scope) or {}).get("initialBudget"),
    }
    try:
        quote = await candle_provider.get_quote(t)
    except Exception:
        quote = None
    # FASE 1 (STU): N2 lê o MESMO snapshot que o Radar (N1) — nunca refetch,
    # nunca recálculo. O contexto sai pronto do snapshot (com snapshotId e
    # setupsRadar); cotação ao vivo e posição do usuário entram POR FORA do
    # snapshot determinístico (não afetam o id).
    try:
        snap = await technical_snapshot.get(t, (config or {}).get("candlePeriod"),
                                            lambda rng: candle_provider.get_history(t, rng=rng))
    except ValueError:
        raise HTTPException(502, "Sem historico para " + t)
    opt_status = await _options_status_for_llm(t) if model in ("opcoes", "completo") else {"available": None, "reason": "Não consultado para este modelo."}
    context = dict(snap["context"])
    context["quote"] = quote or {}
    context["options"] = opt_status
    technical_models.refocus(context, model)
    # FASE 2 (2.4): reanálise SITUADA — a posição do usuário entra no pacote.
    if isinstance(body.get("position"), dict):
        context["userPosition"] = {k: body["position"].get(k) for k in ("qty", "avg", "stop", "alvo", "resultadoAtual")}
    # UM ATIVO, UMA LEITURA (camada de IA): a análise guardada continua válida
    # enquanto a PERGUNTA for a mesma. `promptFp` é o hash do prompt final —
    # muda o snapshot, o perfil, a conta, a posição, o modo ou o modelo, e ela
    # vence sozinha. Vale para os dois stores: o cliente manda a impressão do
    # que está exibindo e o servidor diz se ainda serve, sem gastar IA nem cota.
    #
    # Não é só economia: sem isto a análise NUNCA vencia — o `snapshotId` era
    # gravado e nunca comparado, então uma leitura de outro pregão ficava no
    # card ao lado do veredito fresco, sem nada dizendo a idade dela.
    prompt_fp = llm.prompt_fingerprint(config, skill, profile, account, t, context, modo=modo)
    # Na web o servidor guarda a análise, então ele consulta a PRÓPRIA cópia em
    # vez de confiar no que o cliente mandou — o `A.analyze` do front é
    # memoizado sem `analysis` nas dependências e enviaria uma impressão velha.
    # No aparelho (iOS manda `config`) nada é persistido aqui: aí vale a
    # impressão que o device envia, e ele fica com a cópia dele.
    guardada = None if body.get("config") else (store.get(_conn, "analyses", user_id=scope) or {}).get(t)
    fp_conhecida = body.get("promptFp") or (guardada or {}).get("promptFp")
    if fp_conhecida and fp_conhecida == prompt_fp:
        if guardada:
            return {"t": t, "quote": quote, "reaproveitada": True, **guardada}
        return {"t": t, "quote": quote, "reaproveitada": True, "promptFp": prompt_fp,
                "snapshotId": snap["snapshotId"], "snapshotAt": snap["asOf"], "at": now_str()}
    if ia_indisponivel is None:
        try:
            with llm.collect_usage() as _uso:  # qa/45: captura tokens desta chamada
                result = await llm.analyze_structured(config, skill, profile, account, t, context, modo=modo)
        except Exception as e:  # noqa: BLE001
            pub = llm.public_error(e)
            # T-04-01: SÓ o payload público sanitizado vira `mensagem` — nunca
            # str(e)/repr(e)/traceback (poderiam carregar chave/URL/host do provedor).
            ia_indisponivel = {"code": pub.get("code"), "mensagem": pub.get("message") or pub.get("detail")}

    if ia_indisponivel is not None:
        # FIX-C01: sem IA disponível (gate ou chamada) — explicação mínima
        # determinística a partir do que o motor já calculou, no lugar de um
        # card vazio ou 502. Efêmera por desenho: NÃO consome cota, NÃO
        # persiste (o reuso por promptFp serviria o fallback pra sempre depois
        # que a chave voltasse) e NÃO alimenta ai_activity/analysis_outcomes.
        det = explicacao_det.montar(
            t, snap, modo=("operador" if modo == "operador" else "educacional"), quote=quote)
        payload = {
            "kpis": None,
            "detail": None,
            "proposal": None,
            "markdown": det["markdown"],
            "text": None,
            "model": model,
            "modelLabel": context.get("modelLabel"),
            "technicalContext": technical_models.compact_for_response(context),
            "candles": snap["periodBars"],
            "candlesSentToLLM": (context.get("historyStats") or {}).get("candlesSentToLLM"),
            "snapshotId": snap["snapshotId"],
            "snapshotAt": snap["asOf"],
            "promptFp": prompt_fp,
            "setupsRadar": context.get("setupsRadar"),
            "fundamento": None,
            "confiancaFinal": None,
            "rebaixadoPorFundamento": None,
            "at": now_str(),
            "fonte": "deterministico",
            "iaIndisponivel": ia_indisponivel,
            "verbetes": det["verbetes"],
            "semDados": det["semDados"],
        }
        return {"t": t, "quote": quote, **payload}

    try:
        ai_activity.registrar_uso(_conn, scope=scope, ticker=t, tipo="Análise", usos=_uso)
    except Exception as e:  # noqa: BLE001 — atividade é overlay, nunca quebra a análise
        print(f"[ai-activity] registro N2 falhou p/ {t}: {e}")
    _consume_ai()  # conta a cota só no sucesso
    # qa/30 (Fase A): registra a análise pra autoavaliação futura (N2, texto
    # livre — só entra na estatística quando o modelo devolveu proposal com
    # stop E alvo definidos; registrar() já descarta o resto). Best-effort.
    try:
        prop = result.get("proposal") or {}
        analysis_outcomes.registrar(
            _conn, ticker=t, modo=modo, tipo="n2",
            modelo=f"{config.get('provider')}:{config.get('model')}",
            setup=None, recomendacao=(result.get("kpis") or {}).get("recomendacao"),
            stop=prop.get("stop"), alvo=prop.get("alvo"),
            preco=(quote or {}).get("price"), snapshot_id=snap.get("snapshotId"),
            # qa/35 P2c: no N2 a confiança declarada é a `conviccao` dos kpis
            # (Muito Alto|Alto|Médio|Baixo) — normalizar_confianca traduz.
            confianca=(result.get("kpis") or {}).get("conviccao"),
            # qa/44 (B, ADR-009): mesma classificação do N1, no momento da análise.
            regime=regime.classificar(snap).get("regime"),
            user_id=scope,
            # ADR-015 / ADR15-01: só `confluencia` — descritiva do snapshot,
            # sem o problema abaixo. `entrada`/`alvo2`/`rr2`/`entrada_a_mercado`
            # ficam de fora (None por default) DELIBERADAMENTE: no N2 o
            # stop/alvo gravados acima vêm da `proposal` da LLM, ancorada no
            # preço de mercado do momento — enxertar o `entrada` do plano
            # determinístico (que não está em escopo aqui, e não deve passar
            # a estar) produziria geometria incoerente (gatilho de um plano
            # com stop/alvo de outro), a mesma classe de erro que o ADR-015
            # corrige. Consequência que o Plano 02 honra explicitamente: um
            # registro N2 é metodologiaVersao=2 mas resolve pela âncora de
            # PREÇO, não pela de gatilho — a âncora efetiva é carimbada na
            # resolução (campo `ancora`), nunca inferida da versão.
            confluencia=(snap.get("setups") or {}).get("confluencia"),
        )
    except Exception as e:  # noqa: BLE001 — registro é best-effort
        print(f"[analysis-outcomes] registro N2 falhou p/ {t}: {e}")
    # qa/36 (F10.2): fundamento no N2 — busca INLINE (1 ticker, latência ok) +
    # rebaixamento de confiança quando técnica operável diverge de fundamento
    # fraco (score C). O fundamento NÃO muda o plano (stop/alvo/gatilho); só
    # filtra a confiança pra baixo. Best-effort: falha não derruba a análise.
    fundamento = None
    conf_final = analysis_outcomes.normalizar_confianca((result.get("kpis") or {}).get("conviccao"))
    rebaixado = False
    try:
        # get_fundamentals faz I/O de rede BLOQUEANTE (httpx síncrono) — roda
        # em thread para não congelar o event loop durante a resposta do N2.
        fundamento = await asyncio.to_thread(fundamentals.get_fundamentals, _conn, t)
        operavel = prop.get("stop") is not None and prop.get("alvo") is not None
        conf_final, rebaixado = fundamentals.rebaixa_confianca(
            conf_final, (fundamento or {}).get("score"), operavel)
    except Exception as e:  # noqa: BLE001 — fundamento é overlay, nunca bloqueia
        print(f"[fundamentals] N2 falhou p/ {t}: {e}")
    payload = {
        "kpis": result.get("kpis"),
        "detail": result.get("detail"),
        "proposal": result.get("proposal"),
        "markdown": result.get("markdown"),
        "text": result.get("text"),
        "model": model,
        "modelLabel": context.get("modelLabel"),
        "technicalContext": technical_models.compact_for_response(context),
        "candles": snap["periodBars"],
        "candlesSentToLLM": (context.get("historyStats") or {}).get("candlesSentToLLM"),
        "snapshotId": snap["snapshotId"],
        "snapshotAt": snap["asOf"],
        "promptFp": prompt_fp,   # identidade da pergunta — governa o reuso
        "setupsRadar": context.get("setupsRadar"),
        # qa/36: fundamento (score + métricas) + resultado do rebaixamento.
        "fundamento": fundamento,
        "confiancaFinal": conf_final,
        "rebaixadoPorFundamento": rebaixado,
        "at": now_str(),
        "fonte": "ia",
        "iaIndisponivel": None,
    }
    if not body.get("config"):
        store.set_analysis(_conn, t, payload, user_id=scope)
    return {"t": t, "quote": quote, **payload}


# A2a (auditoria de prompts): nenhum cliente ATUAL chama esta rota (o store
# usa o N2). Ela vive para builds antigos; este contador diz QUANDO ela morreu
# de verdade — zerado por deploy, visível em /api/obs/usage. Quando ficar em
# zero por algumas semanas de builds novos, aposentar a rota.
LEGACY_ANALYZE = {"count": 0, "last": None}


@app.post("/api/analyze/{ticker}")
async def analyze(ticker: str, body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    LEGACY_ANALYZE["count"] += 1
    LEGACY_ANALYZE["last"] = now_str()
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    config = (body or {}).get("config") or store.get(_conn, "config", user_id=scope)
    # FASE 8B (B3)/FIX-C01: modo capturado ANTES do gate (que pode recriar a config).
    modo = (config or {}).get("appMode")
    # FIX-C01: mesmo padrão da rota nova — 402 vira fallback determinístico, nunca 502.
    ia_indisponivel = None
    _consume_ai = lambda: None
    try:
        # GANCHO FREEMIUM (hoje sempre permite) + C-33 (fase 5): contagem real do mes do usuario
        config, _consume_ai = _gate_analise(scope, config)
    except HTTPException as e:
        if e.status_code == 402:
            ia_indisponivel = {"code": "quota", "mensagem": str(e.detail)}
        else:
            raise
    skill = (body or {}).get("skill") or store.get(_conn, "skill", user_id=scope)
    profile = (body or {}).get("profile") or store.get(_conn, "profile", user_id=scope)
    # capital simulado disponivel: handset envia no corpo; web usa o estado
    account = (body or {}).get("account") or {
        "cash": store.get(_conn, "cash", user_id=scope),
        "budget": (store.get(_conn, "config", user_id=scope) or {}).get("initialBudget"),
    }
    try:
        quote = await candle_provider.get_quote(t)
    except Exception:
        quote = None
    # FASE 1 (STU): a mesma janela/candles do snapshot que N1/N2/N3 leem —
    # nada de fetch/slice paralelo (era o BLOCO C; a disciplina agora vive no
    # technical_snapshot, com o mesmo candle_cache por baixo).
    try:
        snap = await technical_snapshot.get(t, (config or {}).get("candlePeriod"),
                                            lambda rng: candle_provider.get_history(t, rng=rng))
    except ValueError:
        raise HTTPException(502, "Sem historico para " + t)
    history_data = {
        "candles": snap["candles"],
        "currency": snap.get("currency"),
        "periodLabel": snap["period"],
        "snapshotId": snap["snapshotId"],
        "snapshotAt": snap["asOf"],
    }
    if ia_indisponivel is None:
        try:
            with llm.collect_usage() as _uso:  # qa/45
                result = await llm.analyze(config, skill, profile, account, t, quote, history_data)
        except Exception as e:  # noqa: BLE001
            pub = llm.public_error(e)
            ia_indisponivel = {"code": pub.get("code"), "mensagem": pub.get("message") or pub.get("detail")}

    if ia_indisponivel is not None:
        # FIX-C01: mesmo fallback da rota nova (ver comentário lá) — efêmero,
        # sem custo, sem persistência.
        det = explicacao_det.montar(
            t, snap, modo=("operador" if modo == "operador" else "educacional"), quote=quote)
        payload = {
            "kpis": None,
            "detail": None,
            "proposal": None,
            "markdown": det["markdown"],
            "text": None,
            "snapshotId": snap["snapshotId"],
            "snapshotAt": snap["asOf"],
            "at": now_str(),
            "fonte": "deterministico",
            "iaIndisponivel": ia_indisponivel,
            "verbetes": det["verbetes"],
            "semDados": det["semDados"],
        }
        return {"t": t, "quote": quote, "candles": len(history_data["candles"]), **payload}

    try:
        ai_activity.registrar_uso(_conn, scope=scope, ticker=t, tipo="Análise", usos=_uso)
    except Exception as e:  # noqa: BLE001
        print(f"[ai-activity] registro (analyze) falhou p/ {t}: {e}")
    _consume_ai()  # conta a cota só no sucesso
    at = now_str()
    payload = {
        "kpis": result.get("kpis"),
        "detail": result.get("detail"),
        "proposal": result.get("proposal"),
        "markdown": result.get("markdown"),
        "text": result.get("text"),
        "snapshotId": snap["snapshotId"],
        "snapshotAt": snap["asOf"],
        "at": at,
        "fonte": "ia",
        "iaIndisponivel": None,
    }
    # persiste a ultima analise do ativo (versao web); o handset persiste no aparelho
    if not (body or {}).get("config"):
        store.set_analysis(_conn, t, payload, user_id=scope)
    return {"t": t, "quote": quote, "candles": len(history_data["candles"]), **payload}


# ---- Stop/alvo individual da carteira (FASE 3): prompt configurável + BYOK ----
@app.post("/api/carteira-stopalvo/{ticker}")
async def carteira_stopalvo(ticker: str, body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    config = (body or {}).get("config") or store.get(_conn, "config", user_id=scope)
    modo = (config or {}).get("appMode")  # FASE 8B (N4): antes do managed recriar a config
    config, _consume_ai = _ai_apply_managed(scope, config)
    profile = (body or {}).get("profile") or store.get(_conn, "profile", user_id=scope)
    account = (body or {}).get("account") or {
        "cash": store.get(_conn, "cash", user_id=scope),
        "budget": (store.get(_conn, "config", user_id=scope) or {}).get("initialBudget"),
    }
    # FASE 8B (N4): a coleção de prompts tem UMA versão por modo — professor
    # (carteiraStopAlvo) × mesa (carteiraStopAlvoOperador). O cliente pode
    # mandar o prompt explícito; sem ele, escolhemos pelo modo do escopo, com
    # fallback no educacional (contas antigas sem backfill).
    _lp = store.get(_conn, "llmPrompts", user_id=scope) or {}
    _key_prompt = "carteiraStopAlvoOperador" if modo == "operador" else "carteiraStopAlvo"
    prompt = (body or {}).get("prompt") or _lp.get(_key_prompt) or _lp.get("carteiraStopAlvo") or ""
    try:
        quote = await candle_provider.get_quote(t)
    except Exception:
        quote = None
    # FASE 1 (STU): o N3 responde OUTRA pergunta (gestão de risco) mas lê os
    # MESMOS números do snapshot que N1/N2 — ATR(14), suportes/resistências,
    # bandas, viés e os setups detectados — nunca um cálculo paralelo.
    snap = None
    try:
        snap = await technical_snapshot.get(t, (config or {}).get("candlePeriod"),
                                            lambda rng: candle_provider.get_history(t, rng=rng))
    except Exception:  # noqa: BLE001 — histórico indisponível não bloqueia (IA declara)
        snap = None
    history_data = {
        "candles": (snap or {}).get("candles") or [],
        "currency": (snap or {}).get("currency"),
        "periodLabel": (snap or {}).get("period") or candles_mod.normalize_period((config or {}).get("candlePeriod")),
    }
    tech_context = None
    if snap:
        _ctx = snap["context"]
        tech_context = {
            "snapshotId": snap["snapshotId"],
            "snapshotAt": snap["asOf"],
            "atr14": (_ctx.get("volatility") or {}).get("atr14"),
            "atr14Pct": (_ctx.get("volatility") or {}).get("atr14Pct"),
            "suportes": (_ctx.get("levels") or {}).get("supports"),
            "resistencias": (_ctx.get("levels") or {}).get("resistances"),
            "bandaSuperior": (_ctx.get("volatility") or {}).get("bollingerUpper"),
            "bandaInferior": (_ctx.get("volatility") or {}).get("bollingerLower"),
            "viesTendencia": (_ctx.get("trend") or {}).get("bias"),
            "minimaLocal": (_ctx.get("historyStats") or {}).get("low63"),
            "maximaLocal": (_ctx.get("historyStats") or {}).get("high63"),
            "referencias": _ctx.get("riskPlanReference"),
            "setupsRadar": _ctx.get("setupsRadar"),
            "dataQuality": _ctx.get("dataQuality"),
        }
    try:
        with llm.collect_usage() as _uso:  # qa/45
            res = await llm.analyze_carteira(config, profile, account, t, quote, history_data, prompt, tech_context=tech_context)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, llm.public_error(e))
    try:
        ai_activity.registrar_uso(_conn, scope=scope, ticker=t, tipo="Carteira", usos=_uso)
    except Exception as e:  # noqa: BLE001
        print(f"[ai-activity] registro N3 falhou p/ {t}: {e}")
    _consume_ai()  # conta a cota só no sucesso
    return {"t": t, "quote": quote, "at": now_str(),
            "snapshotId": (snap or {}).get("snapshotId"), "snapshotAt": (snap or {}).get("asOf"), **res}


# ---- Carteira (preco do servidor = cotacao atual) ----
# Fase 2 (MERC-02/03, D-01): fora do horário de pregão a ordem não executa ao
# preço do momento — vira PENDENTE, com caixa/posição reservados na hora do
# pedido (D-02/D-05/D-06), e só executa de verdade na abertura seguinte
# (scheduler, plano 02-03). O booleano "mercado fechado" NUNCA vem do corpo
# da requisição (T-02-10) — é sempre `pregao.in_market_hours()`, a autoridade
# do servidor, porque é ela que decide se a ordem escapa do preço do momento.
@app.post("/api/buy")
async def buy(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    from . import pregao  # import local: sem ciclo (mesmo padrão de agent.py:216)
    t = str(body.get("t", "")).upper()
    qty = int(body.get("qty") or 0)
    t = _normalize_ticker(t)
    if len(t) < 4:
        # FIX-C02: toda tentativa REJEITADA de conta logada fica no histórico
        # — o balde anônimo é compartilhado (T-04-12/T-02-07), então não registra.
        if scope is not None:
            store.registrar_rejeicao(_conn, "COMPRA", t, qty, None,
                                      f"{t} não é um ativo reconhecido pelo simulador.",
                                      user_id=scope, origem="manual")
        raise HTTPException(400, "Ticker invalido.")
    # cotação continua sendo buscada mesmo com o mercado fechado: é ela que dá
    # o precoReferencia da reserva (D-02) — sem preço não dá para reservar.
    quote = await candle_provider.get_quote(t)
    if not quote or quote.get("price") is None:
        if scope is not None:
            store.registrar_rejeicao(_conn, "COMPRA", t, qty, None,
                                      f"Sem cotação disponível para {t} no momento do pedido.",
                                      user_id=scope, origem="manual")
        raise HTTPException(502, "Sem cotacao para " + t)
    price = quote["price"]

    if pregao.in_market_hours():
        # T-02-35: caminho IMEDIATO e execução de PENDENTES (scheduler) escrevem
        # o mesmo cash/positions da mesma conta na janela da abertura — a
        # checagem de caixa e o débito precisam estar DENTRO da MESMA trava que
        # pending_orders usa, senão duas escritas concorrentes reservam/gastam
        # o mesmo caixa (lost update). A cotação (I/O de rede) já foi obtida
        # ACIMA, fora da trava — nunca segurar um lock atravessando um await.
        with store.ORDER_LOCK:
            # F10-20260819: `store.buy` normaliza qty pro lote de 100 mais
            # próximo ANTES de debitar — checar caixa com a qty bruta do
            # corpo permitia estourar o caixa (ex.: qty=150 passa na checagem
            # bruta mas store.buy debita 200). Normaliza AQUI, na mesma forma,
            # antes de comparar — espelha pending_orders.criar_compra.
            qty = max(100, round(qty / 100) * 100)
            cash_disp = store.get(_conn, "cash", user_id=scope)
            if qty * price > cash_disp:
                if scope is not None:
                    store.registrar_rejeicao(
                        _conn, "COMPRA", t, qty, price,
                        f"Caixa insuficiente para {qty} {t} a R$ {price} — disponível: R$ {cash_disp}.",
                        user_id=scope, origem="manual")
                raise HTTPException(400, "Caixa insuficiente.")
            store.buy(_conn, t, qty, price, user_id=scope, meta=body.get("meta"))  # FASE 2 (2.4)
        _disparar_ciclo_imediato(scope)  # 2026-08-07: reavalia na hora, não espera o próximo tick
        out = store.public_state(_conn, user_id=scope)
        out["priceUsed"] = round(price, 2)
        return out

    # Mercado fechado: vira ordem pendente (D-01).
    if scope is None:
        # T-02-07: o escopo anônimo é um balde kv COMPARTILHADO entre todos os
        # anônimos (App.jsx:669-674) — reservar caixa lá seria dinheiro de um
        # aparecendo para outro. Mesma razão o histórico de rejeição não grava.
        raise HTTPException(401, "Ordens fora do horário de pregão exigem conta conectada — "
                                  "entre para que a ordem fique guardada na sua carteira.")
    try:
        order = pending_orders.criar_compra(_conn, scope, t, qty, price, meta=body.get("meta"))
    except pending_orders.CaixaInsuficiente as e:
        # mesma normalização de lote que `criar_compra` já aplicou internamente
        # antes de recusar — o motivo grava a quantidade que de fato foi avaliada.
        qty_norm = max(100, round(qty / 100) * 100)
        cash_disp = store.get(_conn, "cash", user_id=scope)
        store.registrar_rejeicao(
            _conn, "COMPRA", t, qty_norm, price,
            f"Caixa insuficiente para {qty_norm} {t} a R$ {price} — disponível: R$ {cash_disp}.",
            user_id=scope, origem="manual")
        raise HTTPException(400, str(e))
    # sem _disparar_ciclo_imediato: não há posição nova para o agente avaliar ainda.
    out = store.public_state(_conn, user_id=scope)
    out["pendente"] = True
    out["order"] = order
    out["priceUsed"] = None
    out["precoReferencia"] = round(price, 2)
    return out


@app.post("/api/sell")
async def sell(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    from . import pregao  # import local: sem ciclo (mesmo padrão de agent.py:216)
    # T-04-03: `t` gravado no histórico é sempre o normalizado — nunca a
    # string crua do corpo (o antigo `.upper()` isolado deixava passar
    # espaço/sufixo .SA/caractere fora de A-Z0-9 sem normalizar).
    t = _normalize_ticker(str(body.get("t", "")))
    pos = next((p for p in store.get(_conn, "positions", user_id=scope) if p["t"] == t), None)
    if not pos:
        if scope is not None:
            store.registrar_rejeicao(_conn, "VENDA", t, body.get("qty"), None,
                                      f"Você não tem posição em {t} para vender.",
                                      user_id=scope, origem="manual")
        raise HTTPException(400, "Sem posicao em " + t)
    quote = await candle_provider.get_quote(t)
    if not quote or quote.get("price") is None:
        if scope is not None:
            store.registrar_rejeicao(_conn, "VENDA", t, body.get("qty"), None,
                                      f"Sem cotação disponível para {t} no momento do pedido.",
                                      user_id=scope, origem="manual")
        raise HTTPException(502, "Sem cotacao para " + t)
    price = quote["price"]
    _qty = body.get("qty")  # FASE 2 (2.4): venda parcial opcional (lotes de 100)
    # F10-20260819: `int(_qty) if _qty else None` tratava 0 (falsy em Python)
    # como "campo ausente" e vendia a posição INTEIRA — pedir qty=0 de
    # propósito virava venda total silenciosa. Distingue AUSENTE (None) de
    # ZERO/NEGATIVO explícito (`is not None`) e rejeita o segundo caso.
    _qty_val = None
    if _qty is not None:
        try:
            _qty_val = int(_qty)
        except (TypeError, ValueError):
            if scope is not None:
                store.registrar_rejeicao(_conn, "VENDA", t, _qty, price,
                                          f"Quantidade inválida: {_qty}. A venda usa lotes de 100.",
                                          user_id=scope, origem="manual")
            raise HTTPException(400, "Quantidade inválida.")
        if _qty_val <= 0:
            if scope is not None:
                store.registrar_rejeicao(_conn, "VENDA", t, _qty_val, price,
                                          f"Quantidade inválida: {_qty_val}. A venda usa lotes de 100.",
                                          user_id=scope, origem="manual")
            raise HTTPException(400, "Quantidade inválida.")

    if pregao.in_market_hours():
        # Mesma trava do caminho imediato de compra (T-02-35). A leitura de
        # `pos` acima pode ficar fora, como estava, mas DENTRO da trava é
        # obrigatório reler `positions` e revalidar: uma venda pendente
        # executada no intervalo (scheduler) pode ter zerado a posição.
        with store.ORDER_LOCK:
            positions_atual = store.get(_conn, "positions", user_id=scope)
            pos_atual = next((p for p in positions_atual if p["t"] == t), None)
            if not pos_atual:
                if scope is not None:
                    store.registrar_rejeicao(_conn, "VENDA", t, _qty_val, price,
                                              f"Você não tem posição em {t} para vender.",
                                              user_id=scope, origem="manual")
                raise HTTPException(400, "Sem posicao em " + t)
            resultado_venda = store.sell(_conn, t, price, user_id=scope, qty=_qty_val)
            if resultado_venda is None:
                # Fase 14 (D-3): `store.sell` devolve `None` e já grava a
                # rejeição no histórico (`registrar_rejeicao`, dentro dela
                # mesma) quando a posição existe mas está 100% travada como
                # lastro de uma CALL coberta aberta (`qty_livre(pos) <= 0`).
                # Sem este check a rota devolvia 200 silencioso — a venda não
                # executava, mas o cliente não tinha como saber sem reler o
                # histórico. `/api/buy`/`/api/sell` levantam 400 explícito
                # para toda outra rejeição (caixa insuficiente, sem posição,
                # quantidade inválida); esta era a única exceção silenciosa.
                raise HTTPException(
                    400,
                    f"{pos_atual.get('qtyTravada') or 0} ação(ões) de {t} estão travadas "
                    "como lastro de uma CALL coberta aberta — recompre a call para liberar.")
        _disparar_ciclo_imediato(scope)  # 2026-08-07: reavalia na hora, não espera o próximo tick
        out = store.public_state(_conn, user_id=scope)
        out["priceUsed"] = round(price, 2)
        return out

    # Mercado fechado: vira ordem pendente (D-01), reservando a quantidade
    # (D-06 — impede vender a mesma ação duas vezes em duas pendentes).
    if scope is None:
        # T-02-07/T-04-12: balde anônimo compartilhado — não registra rejeição.
        raise HTTPException(401, "Ordens fora do horário de pregão exigem conta conectada — "
                                  "entre para que a ordem fique guardada na sua carteira.")
    try:
        order = pending_orders.criar_venda(_conn, scope, t, _qty_val if _qty_val is not None else pos["qty"])
    except pending_orders.PosicaoInsuficiente as e:
        # texto da própria exceção — já é específico (disponível × pedido).
        store.registrar_rejeicao(_conn, "VENDA", t, _qty_val if _qty_val is not None else pos["qty"],
                                  price, str(e), user_id=scope, origem="manual")
        raise HTTPException(400, str(e))
    out = store.public_state(_conn, user_id=scope)
    out["pendente"] = True
    out["order"] = order
    out["priceUsed"] = None
    out["precoReferencia"] = round(price, 2)
    return out


# Fase 2 (MERC-04, D-03): cancela uma ordem pendente a qualquer momento antes
# da execução, devolvendo caixa/posição imediatamente (sem esperar o próximo
# tick do scheduler). T-02-09 (IDOR): `pending_orders.cancelar` só enxerga a
# lista do `user_id` recebido — não há busca cross-escopo. Um id de outra
# conta simplesmente não aparece na lista do chamador, então vira o mesmo 404
# de "não encontrada" — sem vazar se o id existe em outra conta.
@app.delete("/api/orders/pending/{order_id}")
async def cancel_pending_order(order_id: str, scope: Optional[str] = Depends(current_scope)):
    if scope is None:
        raise HTTPException(401, "Faça login para continuar.")
    try:
        pending_orders.cancelar(_conn, scope, order_id)
    except pending_orders.OrdemNaoPendente as e:
        raise HTTPException(404, str(e))
    return store.public_state(_conn, user_id=scope)


@app.put("/api/position/{ticker}")
async def position(ticker: str, body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    store.set_position(_conn, ticker.upper(), stop=body.get("stop"), alvo=body.get("alvo"), has_stop=("stop" in body), has_alvo=("alvo" in body), user_id=scope)
    _disparar_ciclo_imediato(scope)  # 2026-08-07: stop/alvo recém-armado é avaliado na hora
    return store.public_state(_conn, user_id=scope)


# ---- Carteira: opções (v2 — ADR-003/004/005) ----
@app.post("/api/options/buy")
async def buy_option(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    """Compra simulada de UM contrato de opção. ADR-004: bloqueia a execução
    quando o provedor está degradado — nunca preenche `avg` com um preço que
    o próprio sistema classificou como não confiável."""
    underlying = _normalize_ticker(str(body.get("underlying") or ""))
    contract_symbol = str(body.get("contractSymbol") or "")
    qty = int(body.get("qty") or 0)
    if len(underlying) < 4 or not contract_symbol or qty <= 0:
        raise HTTPException(400, "Contrato de opção inválido.")
    chain = await options_provider.get_options(underlying, body.get("expiration"))
    if chain.get("providerStatus") != "ok":
        raise HTTPException(502, "Cotação de opções indisponível no momento — tente novamente.")
    contrato = next((c for c in [*chain.get("calls", []), *chain.get("puts", [])]
                      if c.get("contractSymbol") == contract_symbol), None)
    if not contrato:
        raise HTTPException(404, "Contrato não encontrado na cadeia atual.")
    price = contrato.get("lastPrice")
    if not isinstance(price, (int, float)) or price <= 0:
        raise HTTPException(502, "Sem prêmio disponível para este contrato.")
    # F10-20260819: mesma correção de /api/buy — `store.buy_option` normaliza
    # qty pro lote de 100 mais próximo ANTES de debitar; normaliza AQUI antes
    # de checar caixa, senão a checagem valida a qty bruta e o débito real sai
    # maior.
    qty = max(100, round(qty / 100) * 100)
    if qty * price > store.get(_conn, "cash", user_id=scope):
        raise HTTPException(400, "Caixa insuficiente.")
    contract = {
        "id": contract_symbol, "underlying": underlying,
        "optionType": contrato.get("optionType"), "strike": contrato.get("strike"),
        "expiration": chain.get("expiration"),
        "ivEntrada": contrato.get("impliedVolatility"),
    }
    store.buy_option(_conn, contract, qty, price, user_id=scope, meta=body.get("meta"))
    out = store.public_state(_conn, user_id=scope)
    out["priceUsed"] = round(price, 2)
    return out


@app.post("/api/options/sell")
async def sell_option(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    contract_symbol = str(body.get("contractSymbol") or "")
    pos = next((p for p in store.get(_conn, "optionPositions", user_id=scope) if p["id"] == contract_symbol), None)
    if not pos:
        raise HTTPException(400, "Sem posição em " + contract_symbol)
    chain = await options_provider.get_options(pos["underlying"], pos.get("expiration"))
    if chain.get("providerStatus") != "ok":
        raise HTTPException(502, "Cotação de opções indisponível no momento — tente novamente.")
    contrato = next((c for c in [*chain.get("calls", []), *chain.get("puts", [])]
                      if c.get("contractSymbol") == contract_symbol), None)
    price = contrato.get("lastPrice") if contrato else None
    if not isinstance(price, (int, float)):
        raise HTTPException(502, "Sem prêmio disponível para este contrato.")
    _qty = body.get("qty")
    store.sell_option(_conn, contract_symbol, price, user_id=scope, qty=int(_qty) if _qty else None, motivo="manual")
    out = store.public_state(_conn, user_id=scope)
    out["priceUsed"] = round(price, 2)
    return out


@app.put("/api/options/position/{contract_id}")
async def option_position(contract_id: str, body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    store.set_option_position(_conn, contract_id, stop=body.get("stop"), alvo=body.get("alvo"),
                               has_stop=("stop" in body), has_alvo=("alvo" in body), user_id=scope)
    return store.public_state(_conn, user_id=scope)


# ---- Carteira: opções lastreadas (Fase 14, Plano 03 — D-1 redesenho, rotas
# próprias; NÃO tocam /api/options/buy|sell, que continuam servindo o modelo
# antigo long-only) ----
@app.get("/api/options/proposta/{ticker}")
async def options_proposta(ticker: str, scope: Optional[str] = Depends(current_scope)):
    """Proposta determinística de venda coberta ou put de proteção sobre a
    posição real do escopo em `ticker`. ADR-004 (postura best-effort): toda
    exceção do provedor de cadeia ou do pipeline técnico vira
    `providerStatus: "degraded"` + `motivo: "degradado"` — a rota NUNCA cai
    em 500 por indisponibilidade de dado de mercado (T-14-13: reusa o cache
    de 300s do provider e o mesmo pipeline técnico já existente)."""
    import datetime as dt
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker inválido.")
    cfg = store.get(_conn, "config", user_id=scope) or {}
    modo = cfg.get("appMode") or "estudo"
    positions = store.get(_conn, "positions", user_id=scope)
    posicao = next((p for p in positions if p["t"] == t), None)
    cash = store.get(_conn, "cash", user_id=scope)
    # Fetch adiantado (era feito só depois do bloco try/except abaixo):
    # necessário AQUI porque a proposta de FECHAMENTO de uma posição já
    # aberta é decidida antes de qualquer chamada a `propor()` — ver bloco
    # `pos_op_aberta` logo abaixo (bugfix checkpoint humano, Plano 08).
    option_positions = store.get(_conn, "optionPositions", user_id=scope)
    pos_op_aberta = next(
        (p for p in option_positions if p.get("underlying") == t and p.get("lastro")), None)
    try:
        if pos_op_aberta:
            # Posição lastreada JÁ ABERTA neste `underlying`: a proposta é de
            # FECHAMENTO do MESMO contrato, nunca uma nova escolha de
            # `propor()` — cadeia técnica nem é buscada aqui (otimização real,
            # não só atalho: nenhum uso é feito do plano técnico neste ramo).
            chain_pos = await options_provider.get_options(t, pos_op_aberta.get("expiration"))
            provider_status = chain_pos.get("providerStatus")
            resultado = opcoes_lastreadas.proposta_fechar(pos_op_aberta, chain_pos, modo, dt.date.today())
        else:
            chain = await options_provider.get_options(t)
            provider_status = chain.get("providerStatus")
            # Mesmas duas primeiras portas de `opcoes_lastreadas.propor`
            # checadas AQUI antes do fetch técnico — sem isto, um usuário sem
            # posição (ou cadeia degradada) ainda pagaria o custo de
            # candles+indicators+setups para receber a MESMA ausência que já
            # dava para saber sem tocar rede de novo (T-14-13: nenhuma
            # chamada nova por card além da que o gate já faz).
            if provider_status != "ok":
                resultado = {"proposta": None, "motivo": "degradado"}
            elif not isinstance(posicao, dict) or store.qty_livre(posicao) < 100:
                resultado = {"proposta": None, "motivo": "sem_lastro"}
            else:
                try:
                    quote = await candle_provider.get_quote(t)
                except Exception:
                    quote = None
                spot = _spot_from_chain_or_quote(chain, quote)
                p = candles_mod.normalize_period(None)   # período CANÔNICO, mesmo da análise técnica
                snap = await technical_snapshot.get(t, p, lambda rng: candle_provider.get_history(t, rng=rng))
                plano = setups.plano_do_resultado(snap["setups"], close=snap.get("close"))
                resultado = opcoes_lastreadas.propor(t, chain, spot, plano, posicao, cash, modo, dt.date.today())
    except Exception:
        resultado = {"proposta": None, "motivo": "degradado"}
        provider_status = "degraded"
    motivo = resultado["motivo"]
    motivo_texto = skill_ref.opcoes_lastreadas_txt(modo, motivo, ticker=t)
    put_sem_lastro_ids = opcoes_lastreadas.put_sem_lastro(option_positions, positions)
    return {
        "ticker": t, "providerStatus": provider_status, "modo": modo,
        "proposta": resultado["proposta"], "motivo": motivo, "motivoTexto": motivo_texto,
        "putSemLastro": put_sem_lastro_ids,
    }


@app.post("/api/options/lastreada/abrir")
async def options_lastreada_abrir(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    """Abre a operação lastreada (venda coberta OU put de proteção) a partir
    da proposta que o motor já ofereceu. Trava de ESCRITA (D-5, T-14-09):
    Modo Estudo nunca executa — a mesma trava do `set_agent`, agravada aqui
    porque é a única deste par que faltava um 403 explícito de servidor."""
    cfg = store.get(_conn, "config", user_id=scope) or {}
    if cfg.get("appMode") != "operador":
        raise HTTPException(403, "Modo Estudo não executa ordens — troque para o Modo Operador para operar.")
    underlying = _normalize_ticker(str(body.get("underlying") or ""))
    contract_symbol = str(body.get("contractSymbol") or "")
    contratos = body.get("contratos")
    if len(underlying) < 4 or not contract_symbol or not isinstance(contratos, (int, float)) or contratos < 1:
        raise HTTPException(400, "Operação lastreada inválida.")
    chain = await options_provider.get_options(underlying, body.get("expiration"))
    if chain.get("providerStatus") != "ok":
        raise HTTPException(502, "Cotação de opções indisponível no momento — tente novamente.")
    contrato = next((c for c in [*chain.get("calls", []), *chain.get("puts", [])]
                      if c.get("contractSymbol") == contract_symbol), None)
    if not contrato:
        raise HTTPException(404, "Contrato não encontrado na cadeia atual.")
    price = contrato.get("lastPrice")
    if not isinstance(price, (int, float)) or price <= 0:
        raise HTTPException(502, "Sem prêmio disponível para este contrato.")
    contract = {
        "id": contract_symbol, "underlying": underlying,
        "optionType": contrato.get("optionType"), "strike": contrato.get("strike"),
        "expiration": chain.get("expiration"),
        "ivEntrada": contrato.get("impliedVolatility"),
    }
    try:
        if contrato.get("optionType") == "call":
            store.abrir_call_coberta(_conn, contract, int(contratos), price, user_id=scope)
        elif contrato.get("optionType") == "put":
            store.comprar_put_protecao(_conn, contract, int(contratos), price, user_id=scope)
        else:
            raise HTTPException(400, "Tipo de contrato inválido para operação lastreada.")
    except ValueError as e:
        raise HTTPException(400, str(e))
    _disparar_ciclo_imediato(scope)
    out = store.public_state(_conn, user_id=scope)
    out["priceUsed"] = round(price, 2)
    return out


@app.post("/api/options/lastreada/fechar")
async def options_lastreada_fechar(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    """Fecha a operação lastreada aberta pela rota irmã de abertura acima.
    Mesma trava de Modo Operador (D-5) e mesmo bloqueio por `providerStatus`
    da abertura — fechar também é execução, não só abrir."""
    cfg = store.get(_conn, "config", user_id=scope) or {}
    if cfg.get("appMode") != "operador":
        raise HTTPException(403, "Modo Estudo não executa ordens — troque para o Modo Operador para operar.")
    contract_symbol = str(body.get("contractSymbol") or "")
    pos = next((p for p in store.get(_conn, "optionPositions", user_id=scope) if p["id"] == contract_symbol), None)
    if not pos:
        raise HTTPException(400, "Sem posição em " + contract_symbol)
    chain = await options_provider.get_options(pos["underlying"], pos.get("expiration"))
    if chain.get("providerStatus") != "ok":
        raise HTTPException(502, "Cotação de opções indisponível no momento — tente novamente.")
    contrato = next((c for c in [*chain.get("calls", []), *chain.get("puts", [])]
                      if c.get("contractSymbol") == contract_symbol), None)
    price = contrato.get("lastPrice") if contrato else None
    if not isinstance(price, (int, float)):
        raise HTTPException(502, "Sem prêmio disponível para este contrato.")
    contratos_body = body.get("contratos")
    contratos_n = int(contratos_body) if isinstance(contratos_body, (int, float)) and contratos_body > 0 else None
    if pos.get("side") == "vendida":
        store.fechar_call_coberta(_conn, contract_symbol, price, user_id=scope, contratos=contratos_n)
    elif pos.get("side") == "comprada":
        qty = contratos_n * 100 if contratos_n else None
        store.sell_option(_conn, contract_symbol, price, user_id=scope, qty=qty, motivo="manual")
    else:
        raise HTTPException(400, "Sem posição em " + contract_symbol)
    _disparar_ciclo_imediato(scope)
    out = store.public_state(_conn, user_id=scope)
    out["priceUsed"] = round(price, 2)
    return out


@app.put("/api/agent")
async def agent(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    store.set_agent(_conn, body or {}, user_id=scope)
    return store.public_state(_conn, user_id=scope)


async def _intraday_fetch(ticker: str, rng: str, interval: str):
    """ADR-001 (item 7): fetch da passada intraday. Passa pelo provedor único,
    então a instrumentação e o gatilho do plano B valem aqui também — é
    justamente o caminho onde o feed de B3 sumiu em 31/07."""
    return await candle_provider.get_history(ticker, rng=rng, interval=interval)


@app.get("/api/intraday")
async def intraday_pass(scope: Optional[str] = Depends(current_scope)):
    """Última passada intraday (GLOBAL — o universo é o mesmo para todos).

    Serve o ARMAZENADO, nunca dispara varredura: a passada é do laço, e um
    endpoint que varre sob demanda transformaria custo O(1) em O(requisições).
    """
    from . import intraday as intraday_mod
    stored = intraday_mod.get_stored(_conn)
    if not stored:
        return {"disponivel": False, "interval": intraday_mod.INTERVALO,
                "motivo": "nenhuma passada ainda (roda dentro do pregão)",
                "ultima": intraday_mod.LAST_PASS}
    return {"disponivel": True, **stored}


@app.get("/api/timing/{ticker}")
async def timing_de_entrada(ticker: str, appMode: Optional[str] = None,
                            scope: Optional[str] = Depends(current_scope)):
    """F1 — timing de entrada de UM ativo: plano diário × barra 15m FECHADA.

    Determinístico e O(1): lê os DOIS armazenados globais (Radar diário +
    passada intraday), nunca dispara fetch nem LLM. O vocabulário segue o modo
    (iOS manda ?appMode; web cai na config do escopo) — enquadramento
    regulatório: condição objetiva do plano, nunca "sinal em tempo real".
    """
    from . import intraday as intraday_mod
    from . import timing as timing_mod
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    cfg = store.get(_conn, "config", user_id=scope) or {}
    modo = appMode or cfg.get("appMode") or "estudo"
    p = candles_mod.normalize_period(None)   # período CANÔNICO do Radar diário
    radar_stored = await asyncio.to_thread(radar_daily.get_stored, _conn, p)
    intra_stored = await asyncio.to_thread(intraday_mod.get_stored, _conn)
    return timing_mod.montar(radar_stored, intra_stored, t, modo)


# --------------------- Camada de entendimento (didática) ---------------------
# ISOLAMENTO POR CONSTRUÇÃO: estes endpoints são NOVOS e o `/api/timing` acima
# fica intocado. É deliberado — a spec sugeria embutir o conceito na resposta
# que já existe, mas aí "o payload do Operador é idêntico ao de hoje" viraria
# promessa a ser testada em vez de fato estrutural. Rota nova não muda rota
# velha, e o guardião de isolamento não tem como ser burlado.
# Custo: zero LLM em qualquer caminho — texto determinístico servido do
# backend, como `skill_ref.TIMING` já faz com as frases de estado.
@app.get("/api/conceitos")
async def get_conceitos(modo: Optional[str] = None, resumido: bool = False,
                        scope: Optional[str] = Depends(current_scope)):
    """Catálogo genérico (sem os números de nenhum card) + estado das chaves de
    desligamento. O front busca uma vez e usa para saber o que existe."""
    cfg = store.get(_conn, "config", user_id=scope) or {}
    voc = "operador" if (modo or cfg.get("appMode")) == "operador" else "educacional"
    return {"ligada": conceitos.didatica_ligada(),
            "assistente": conceitos.assistente_ligado(),
            "modo": voc,
            # Toque longo: setorId → conceito primário. O front declara as
            # regiões; o QUE cada uma explica decide-se aqui — repontear um
            # setor é deploy do Railway, não build de iOS.
            "setores": conceitos.setores(),
            "conceitos": conceitos.catalogo(voc, resumido)}


@app.post("/api/conceito/{cid}")
async def post_conceito(cid: str, body: dict = Body(default={}),
                        scope: Optional[str] = Depends(current_scope)):
    """Conceito ANCORADO nos números que o card está exibindo agora.

    Os números vêm do chamador (o front já os tem de `/api/timing`) e passam
    pelo formatador; campo ausente derruba o parágrafo que dependia dele —
    nenhuma estimativa entra no lugar (Princípio 1). É POST por causa do corpo,
    não por ter efeito: a rota não escreve nada."""
    b = body or {}
    # Camada desligada NÃO é 404: o front precisa distinguir "some a afordância"
    # de "id errado", e 404 nos dois casos deixava a UI sem como decidir.
    if not conceitos.didatica_ligada():
        return {"ligada": False, "id": str(cid)[:40]}
    cfg = store.get(_conn, "config", user_id=scope) or {}
    voc = "operador" if (b.get("modo") or cfg.get("appMode")) == "operador" else "educacional"
    c = conceitos.montar(str(cid)[:40], voc,
                         b.get("dados") if isinstance(b.get("dados"), dict) else None,
                         bool(b.get("resumido")))
    if c is None:
        raise HTTPException(404, "Conceito não existe no catálogo.")
    return {"ligada": True, **c}


# O PET — resumo determinístico da tela, para o mascote falar/exibir.
# Custo zero: nenhuma LLM aqui, nenhum fetch ao vivo (Yahoo) — só o que já
# está armazenado (posições/config/agentLog no KV, radar/intraday nas
# passadas periódicas). Toda frase sai pronta do servidor (lei do
# vocabulário): as de estado vêm de timing.montar (skill_ref.TIMING) quando
# aplicável, e as conectivas moram NESTAS funções — o front nunca compõe
# texto. "O que o app NÃO faz" vem SEMPRE primeiro (regra de conceitos.py).
_PET_NAO_FAZ = ("O app não compra nem vende nada: a carteira é simulada e a "
                "decisão é sempre sua.")


def _pet_resumo_mercado(scope: Optional[str], radar_stored: Optional[dict],
                        intra_stored: Optional[dict], operador: bool) -> dict:
    """`pet:mercado` — formato ORIGINAL, intocado (F1). Itens da watchlist com
    o timing de entrada de cada um."""
    from . import timing as timing_mod
    wl = [t for t in (store.get(_conn, "watchlist", user_id=scope) or []) if isinstance(t, str)][:12]
    itens = []
    for t in wl:
        r = timing_mod.montar(radar_stored, intra_stored, t, "operador" if operador else "estudo")
        if r and r.get("estado") not in (None, "sem_plano") and r.get("frase"):
            itens.append({"ticker": t, "estado": r["estado"], "frase": r["frase"]})
    fala = [_PET_NAO_FAZ]
    if itens:
        fala.append("Na sua lista de hoje:")
        fala += [f"{i['ticker']}: {i['frase']}" for i in itens]
        fala.append("As leituras têm a idade da barra de 15 minutos — "
                    "nunca são o agora.")
    else:
        fala.append("O Radar ainda não tem planos armazenados para os ativos "
                    "que você acompanha. Assim que houver, eu explico cada um.")
    if operador:
        perguntas = ["Qual ativo da lista está mais perto do gatilho?",
                     "Por que a leitura tem até 15 minutos de atraso?"]
        if itens:
            perguntas.insert(0, f"O que fazer com {itens[0]['ticker']} nesse estado?")
    else:
        perguntas = ["O que esse estado de timing quer dizer?",
                     "Por que a leitura muda a cada 15 minutos?"]
        if itens:
            perguntas.insert(0, f"Por que {itens[0]['ticker']} está em \"{itens[0]['estado']}\"?")
    return {"itens": itens, "fala": fala, "perguntas": perguntas[:3]}


def _pet_resumo_carteira(scope: Optional[str], intra_stored: Optional[dict], operador: bool) -> dict:
    """`pet:carteira` — posições, preço médio, caixa e resultado aberto. O
    preço de marcação é o ÚLTIMO FECHAMENTO DE 15 MIN armazenado (mesma fonte
    do intraday do pet:mercado) — nunca um fetch ao vivo nesta rota."""
    from . import intraday as intraday_mod
    positions = [p for p in (store.get(_conn, "positions", user_id=scope) or []) if isinstance(p, dict)]
    cash = float(store.get(_conn, "cash", user_id=scope) or 0)
    perguntas = (["Qual posição está mais perto do stop?", "Por que 'aberto' não é o mesmo que realizado?"]
                 if operador else
                 ["O que é preço médio?", "Por que meu resultado aberto muda sem eu vender?"])
    fala = [_PET_NAO_FAZ]
    if not positions:
        fala.append(f"Sua carteira simulada ainda não tem posições. Caixa disponível: R$ {cash:.2f}.")
        return {"fala": fala, "posicoes": 0, "caixa": cash, "perguntas": perguntas}
    linhas, pnl_total, com_preco = [], 0.0, 0
    for p in positions[:12]:
        t = p.get("t"); qty = float(p.get("qty") or 0); avg = float(p.get("avg") or 0)
        r = intraday_mod.resumo_do_ticker(intra_stored, t) if t else None
        close = r.get("close") if (r and isinstance(r.get("close"), (int, float))) else None
        if close is not None:
            pnl = (close - avg) * qty
            pnl_total += pnl; com_preco += 1
            sinal = "+" if pnl >= 0 else "-"
            linhas.append(f"{t}: {qty:.0f} cotas, PM R$ {avg:.2f}, resultado aberto {sinal}R$ {abs(pnl):.2f}.")
        else:
            linhas.append(f"{t}: {qty:.0f} cotas, PM R$ {avg:.2f} — sem cotação intraday armazenada agora.")
    fala.append(f"Você tem {len(positions)} posição(ões) na carteira simulada, caixa de R$ {cash:.2f}.")
    fala += linhas
    if com_preco:
        sinal = "+" if pnl_total >= 0 else "-"
        fala.append(f"Resultado aberto das posições com cotação disponível: {sinal}R$ {abs(pnl_total):.2f}.")
    fala.append("Os preços usam o fechamento da barra de 15 minutos — nunca são o agora.")
    return {"fala": fala, "posicoes": len(positions), "caixa": cash, "perguntas": perguntas}


def _pet_resumo_evolucao(scope: Optional[str], intra_stored: Optional[dict], operador: bool) -> dict:
    """`pet:evolucao` — patrimônio agora e retorno acumulado desde o orçamento
    inicial. Mesma fórmula de `finance.js: equityCurve` (base = orçamento
    inicial; sem ele, o 1º snapshot). Sem quotes ao vivo, "resultado do dia"
    (que depende da variação % do pregão) fica fora — simplificação
    deliberada desta rota custo-zero.

    Fase 2 (02-02): soma `caixaReservado` (ordens pendentes de compra) ao
    patrimônio — sem isto o Boris anunciaria um patrimônio MENOR que o da
    tela no instante em que o usuário cria uma ordem pendente (o valor sai de
    `cash` e entra em `caixaReservado`, mas continua sendo patrimônio do
    usuário: volta ao caixa se a ordem for cancelada). Essa é exatamente a
    classe de defeito "a tela está certa, só o Boris erra" da auditoria de
    v1.0 — o `public_state` da tela já soma os dois (`store.py`), este
    resumo tinha ficado para trás."""
    from . import intraday as intraday_mod
    positions = [p for p in (store.get(_conn, "positions", user_id=scope) or []) if isinstance(p, dict)]
    cash = float(store.get(_conn, "cash", user_id=scope) or 0)
    reservado = store.caixa_reservado(_conn, user_id=scope)
    cfg = store.get(_conn, "config", user_id=scope) or {}
    budget = cfg.get("initialBudget")
    snaps = [s for s in (store.get(_conn, "equitySnapshots", user_id=scope) or [])
             if isinstance(s, dict) and isinstance(s.get("patrimonio"), (int, float))]
    pos_val = 0.0
    for p in positions:
        t = p.get("t"); qty = float(p.get("qty") or 0); avg = float(p.get("avg") or 0)
        r = intraday_mod.resumo_do_ticker(intra_stored, t) if t else None
        close = r.get("close") if (r and isinstance(r.get("close"), (int, float))) else None
        pos_val += qty * (close if close is not None else avg)
    patrimonio = cash + reservado + pos_val
    base = float(budget) if isinstance(budget, (int, float)) and budget > 0 else (
        snaps[0]["patrimonio"] if snaps else patrimonio)
    ret_acum = ((patrimonio - base) / base * 100) if base > 0 else 0.0
    fala = [_PET_NAO_FAZ,
           f"Seu patrimônio simulado agora é R$ {patrimonio:.2f} (caixa R$ {cash:.2f} + posições R$ {pos_val:.2f})."]
    if reservado > 0:
        fala.append(f"Desse total, R$ {reservado:.2f} está reservado para ordem(ns) pendente(s) — "
                     "volta ao caixa se você cancelar antes da execução.")
    if snaps or (isinstance(budget, (int, float)) and budget > 0):
        fala.append(f"Desde o orçamento inicial, o retorno acumulado é de {ret_acum:+.1f}%.")
    else:
        fala.append("Ainda não há orçamento inicial nem snapshots suficientes para traçar a curva de patrimônio.")
    fala.append("O valor das posições usa o fechamento da barra de 15 minutos — nunca é o agora.")
    perguntas = (["O que está puxando o resultado desde o início?", "Como leio esse drawdown?"]
                 if operador else
                 ["O que é retorno acumulado?", "Por que meu patrimônio pode cair sem eu operar?"])
    return {"fala": fala, "patrimonio": patrimonio, "retornoAcumuladoPct": ret_acum, "perguntas": perguntas}


def _pet_resumo_radar(p: str, operador: bool) -> dict:
    """`pet:radar` — os candidatos da varredura DO DIA já armazenada
    (`radar_daily.get_stored`), a MESMA fonte que a aba usa quando não força
    uma varredura nova. Nenhum scan é disparado aqui."""
    radar_stored = radar_daily.get_stored(_conn, p)
    results = [r for r in ((radar_stored or {}).get("results") or []) if isinstance(r, dict)]
    perguntas = (["Qual setup tem mais confluência agora?", "O que essa varredura NÃO garante?"]
                 if operador else
                 ["O que é confluência?", "Por que um ativo aparece no topo da varredura?"])
    fala = [_PET_NAO_FAZ]
    if not results:
        fala.append("O Radar ainda não tem uma varredura do dia armazenada. Assim que houver, eu explico os destaques.")
        return {"fala": fala, "candidatos": 0, "perguntas": perguntas}
    top = sorted(results, key=lambda r: -(r.get("confluencia") or 0))[:8]
    fala.append(f"A varredura do dia encontrou {len(results)} ativo(s); os de maior confluência:")
    for r in top:
        conf = r.get("confluencia")
        conf_txt = f"{conf:.0f}%" if isinstance(conf, (int, float)) else "—"
        setup = r.get("melhorSetup") or "sem setup nomeado"
        fala.append(f"{r.get('ticker')}: confluência {conf_txt} · {setup}")
    fala.append("Confluência é quantas famílias de indicadores concordam — não é garantia de resultado.")
    return {"fala": fala, "candidatos": len(top), "perguntas": perguntas}


def _pet_resumo_agente(scope: Optional[str], operador: bool) -> dict:
    """`pet:agente` — estado do Operador, regras ativas e as últimas decisões
    do Diário (`agentLog`, o mesmo que alimenta /api/agent/log)."""
    ag = store.get(_conn, "agent", user_id=scope) or {}
    ativo = bool(ag.get("serverEnabled"))
    modo_ag = ag.get("mode") or ("executar" if ag.get("autonomous") else "sinalizar")
    rules = ag.get("rules") if isinstance(ag.get("rules"), dict) else {}
    regras_on = [k for k in ("stop", "alvo") if rules.get(k) is not False]
    if rules.get("trailing"):
        regras_on.append("trailing")
    fala = [_PET_NAO_FAZ]
    if ativo:
        fala.append(f"O Operador está ATIVO no servidor, modo \"{'executar' if modo_ag == 'executar' else 'apenas sinalizar'}\".")
    else:
        fala.append("O Operador está INATIVO no servidor — ele só age enquanto o app estiver aberto, no modo atual.")
    fala.append("Regras ligadas: " + ", ".join(regras_on) + "." if regras_on else "Nenhuma regra de proteção está ligada agora.")
    log = [e for e in (store.get(_conn, "agentLog", user_id=scope) or []) if isinstance(e, dict)]
    ultimas = log[-3:]
    if ultimas:
        fala.append("Últimas decisões registradas:")
        fala += [f"· {e.get('text') or e.get('kind') or 'evento'}" for e in reversed(ultimas)]
    else:
        fala.append("Ainda não há decisões registradas no Diário do agente.")
    perguntas = (["Por que essa regra está desligada?", "O que motivou a última decisão do Diário?"]
                 if operador else
                 ["O que muda entre 'sinalizar' e 'executar'?", "Por que o Operador só age com o app aberto às vezes?"])
    return {"fala": fala, "ativo": ativo, "modo": modo_ag, "perguntas": perguntas}


def _pet_resumo_historico(scope: Optional[str], operador: bool) -> dict:
    """`pet:historico` — operações fechadas e o agregado de resultado."""
    hist = [h for h in (store.get(_conn, "history", user_id=scope) or []) if isinstance(h, dict)]
    perguntas = (["Qual foi minha operação mais recente?", "Como está minha taxa de acerto?"]
                 if operador else
                 ["O que esse resultado agregado me ensina?", "Uma operação fechada positiva sempre foi uma decisão boa?"])
    fala = [_PET_NAO_FAZ]
    if not hist:
        fala.append("Ainda não há operações no seu histórico simulado.")
        return {"fala": fala, "operacoes": 0, "perguntas": perguntas}
    fechadas = [h for h in hist if isinstance(h.get("pnl"), (int, float))]
    fala.append(f"Seu histórico simulado tem {len(hist)} operação(ões) registradas.")
    if fechadas:
        pnl_total = sum(h["pnl"] for h in fechadas)
        ganhas = sum(1 for h in fechadas if h["pnl"] > 0)
        sinal = "+" if pnl_total >= 0 else "-"
        fala.append(f"Das {len(fechadas)} com resultado calculado, {ganhas} fecharam positivas; agregado {sinal}R$ {abs(pnl_total):.2f}.")
    ultimo = hist[-1]
    fala.append(f"Mais recente: {ultimo.get('type')} de {ultimo.get('t')} em {ultimo.get('date')}.")
    return {"fala": fala, "operacoes": len(hist), "perguntas": perguntas}


def _pet_resumo_perfil(scope: Optional[str], cfg: dict, operador: bool) -> dict:
    """`pet:perfil` — modo, orçamento, risco e notificações. A tela com menos
    "o que explicar"; resumo deliberadamente mais simples que as demais.

    `operador` (não `cfg.get("appMode")` sozinho) decide o texto E as
    perguntas — mesma regra das demais telas: o app nativo manda seu
    `appMode` LOCAL via query `modo` (persistence.js), que pode estar à
    frente do que o servidor tem gravado; usar só `cfg` aqui mostraria um
    modo desatualizado justamente na tela que fala sobre o modo."""
    prof = store.get(_conn, "profile", user_id=scope) or {}
    modo_app = "operador" if operador else "estudo"
    budget = cfg.get("initialBudget")
    risco = prof.get("risco")
    notif_on = bool((cfg.get("notif") or {}).get("enabled"))
    fala = [_PET_NAO_FAZ, f"Você está no modo {'Operador' if modo_app == 'operador' else 'Estudo'}."]
    if isinstance(budget, (int, float)) and budget > 0:
        fala.append(f"Orçamento inicial simulado: R$ {float(budget):.2f}.")
    if risco:
        fala.append(f"Seu perfil de risco cadastrado é \"{risco}\".")
    fala.append("Notificações estão " + ("ativas" if notif_on else "desativadas") + ".")
    perguntas = (["O que trava se eu ligar entrada automática?", "Onde ajusto o % de risco por trade?"]
                 if operador else
                 ["O que muda entre Modo Estudo e Modo Operador?", "Por que meu perfil de risco importa?"])
    return {"fala": fala, "modo": modo_app, "notificacoesAtivas": notif_on, "perguntas": perguntas}


@app.get("/api/pet/resumo")
async def get_pet_resumo(modo: Optional[str] = None, tela: Optional[str] = None,
                         scope: Optional[str] = Depends(current_scope)):
    """F4: `tela` escolhe QUAL aba resumir — mesma allowlist do /api/assistente
    (`conceitos.PET_TELAS`); tela ausente ou desconhecida cai em "mercado"
    (comportamento de antes da F4, quando só essa tela existia)."""
    from . import intraday as intraday_mod
    if not conceitos.didatica_ligada():
        return {"ligada": False}
    aba = tela if tela in conceitos.PET_TELAS else "mercado"
    cfg = store.get(_conn, "config", user_id=scope) or {}
    operador = (modo or cfg.get("appMode")) == "operador"
    voc = "operador" if operador else "educacional"
    if aba == "mercado":
        p = candles_mod.normalize_period(None)
        radar_stored = await asyncio.to_thread(radar_daily.get_stored, _conn, p)
        intra_stored = await asyncio.to_thread(intraday_mod.get_stored, _conn)
        extra = _pet_resumo_mercado(scope, radar_stored, intra_stored, operador)
    elif aba == "carteira":
        intra_stored = await asyncio.to_thread(intraday_mod.get_stored, _conn)
        extra = _pet_resumo_carteira(scope, intra_stored, operador)
    elif aba == "evolucao":
        intra_stored = await asyncio.to_thread(intraday_mod.get_stored, _conn)
        extra = _pet_resumo_evolucao(scope, intra_stored, operador)
    elif aba == "radar":
        p = candles_mod.normalize_period(None)
        extra = _pet_resumo_radar(p, operador)
    elif aba == "agente":
        extra = _pet_resumo_agente(scope, operador)
    elif aba == "historico":
        extra = _pet_resumo_historico(scope, operador)
    else:  # "perfil"
        extra = _pet_resumo_perfil(scope, cfg, operador)
    return {"ligada": True, "modo": voc, "tela": aba, **extra}


# Fase F3 — a KB (grátis, pública) tenta responder ANTES da LLM (paga, exige
# conta). `GET /api/kb/buscar` expõe a mesma busca por conta própria: útil
# para quem quer consultar o glossário sem passar pelo fluxo do assistente
# (uso futuro/opcional do front), e serve de prova em separado de que a busca
# funciona sem autenticação nenhuma.
@app.get("/api/kb/buscar")
async def get_kb_buscar(q: str = "", modo: Optional[str] = None,
                        scope: Optional[str] = Depends(current_scope)):
    """Busca pública na base de conhecimento — sem custo, sem conta.

    Sem corte de confiança (isso é `kb.resolver()`, usado só dentro de
    `/api/assistente`): aqui é busca de verdade, devolve os verbetes mais
    relevantes mesmo quando a pontuação é baixa — quem decide o que fazer com
    isso é quem chamou."""
    from . import kb
    cfg = store.get(_conn, "config", user_id=scope) or {}
    voc = "operador" if (modo or cfg.get("appMode")) == "operador" else "educacional"
    achados = kb.buscar(q, limite=5)
    return {"query": q, "resultados": [kb.formatar(v, voc) for v in achados]}


# Fase 4/F3 — ASSISTENTE de entendimento. A KB (grátis) responde primeiro; só
# quando ela não cobre a pergunta com confiança é que a rota cai para a LLM
# (paga, sob conta).
@app.post("/api/assistente")
async def post_assistente(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    """Pergunta livre sobre a tela atual, respondida no vocabulário do modo.

    Roteamento KB → LLM (Fase F3): `kb.resolver(...)` tenta a base determinís-
    tica primeiro — grátis, sem conta, sem tocar `ai_activity` nem o teto de
    custo. Só quando ela devolve `None` (não cobre com confiança) é que a rota
    exige conta e cai para a LLM. EXIGIR CONTA no caminho LLM é motivo
    técnico, não comercial: `ai_activity` grava com `user_id=scope`, e
    `scope=None` é UM balde compartilhado por TODOS os anônimos — um teto por
    escopo ali deixaria um usuário esgotar a cota de todo mundo. Quem não tem
    conta e faz uma pergunta que a KB não cobre continua com a camada
    determinística completa (o "?" de cada card) — só não tem a LLM.
    """
    from . import assistente as assist, kb
    b = body or {}
    pergunta = str(b.get("pergunta") or "").strip()
    if not pergunta:
        raise HTTPException(400, "Escreva a sua pergunta sobre esta tela.")
    # `tela: "setor:<id>"` e `tela: "pet:<id>"` validam contra os REGISTROS,
    # antes de gastar qualquer coisa: id que o backend não conhece é 400,
    # nunca contexto de prompt. As allowlists são SETORES e PET_TELAS — as
    # mesmas fontes que o catálogo e o pet servem.
    tela = str(b.get("tela") or "")
    if tela.startswith("setor:") and tela[len("setor:"):] not in conceitos.SETORES:
        raise HTTPException(400, "Setor desconhecido.")
    if tela.startswith("pet:") and tela[len("pet:"):] not in conceitos.PET_TELAS:
        raise HTTPException(400, "Tela desconhecida.")
    # `config` no CORPO é o caminho do iPhone: lá o modelo e a chave vivem no
    # aparelho, e o servidor não os tem. Omitir isto foi o que produziu
    # "Nenhum modelo de IA configurado" em produção no scanDeep (qa/29).
    config = b.get("config") or store.get(_conn, "config", user_id=scope)
    modo = b.get("modo") or (config or {}).get("appMode") or "estudo"
    voc = "operador" if modo == "operador" else "educacional"
    resolvido_pela_kb = kb.resolver(pergunta, voc)
    if resolvido_pela_kb is not None:
        return resolvido_pela_kb
    if not scope:
        raise HTTPException(401, "Faça login para continuar.")
    # Chave PRÓPRIA dispensa o teto: ele protege o bolso do Alex, e barrar
    # alguém de gastar o próprio dinheiro é atrito que faz o app parecer
    # quebrado. Quem usa a chave gerenciada segue sob cota e sob teto.
    byok = bool(llm.resolve_key(config))
    config, _consume_ai = _ai_apply_managed(scope, config)
    # F5: `historico` (últimos turnos da MESMA conversa) é opcional — sem ele
    # o comportamento é o de antes, pergunta isolada. Vem do CORPO porque é
    # estado da conversa que o front já tem (mensagens trocadas), não algo
    # que o servidor guarda entre chamadas.
    historico = b.get("historico")
    try:
        r = await assist.responder(_conn, config, scope, modo,
                                   b.get("tela"), b.get("snapshot"), pergunta,
                                   byok=byok, historico=historico)
    except assist.TetoAtingido as e:
        raise HTTPException(429, str(e))
    except Exception as e:  # noqa: BLE001 — erro do provedor vira texto público
        raise HTTPException(502, llm.public_error(e))
    _consume_ai()
    r["fonte"] = "llm"
    return r


def _disparar_ciclo_imediato(scope: Optional[str]) -> None:
    """2026-08-07: quando o usuário MEXE numa posição (compra, venda, define
    stop/alvo), o gatilho recém-armado só era avaliado no próximo tick do
    scheduler — até `intervalMin` (60min hoje na conta que motivou isto).
    Dispara o MESMO ciclo em background (mesma técnica de /api/agent/run-now:
    task solta, nunca bloqueia a resposta da compra/venda/stop) pra reavaliar
    na hora. Só pra quem tem conta — anônimo não tem Operador no servidor."""
    if not scope or agent_mod.kill_switch_on():
        return

    async def _bg():
        try:
            await agent_mod.run_cycle_for(_conn, scope, candle_provider.get_quotes_exclusive, origem="imediato",
                                          snapshot_getter=_snapshot_para_trailing,
                                          option_quotes_getter=options_provider.get_options)
        except Exception as e:  # noqa: BLE001 — o erro já foi para o agentLog
            print(f"[agent] ciclo imediato de {scope} falhou: {e}")

    asyncio.get_event_loop().create_task(_bg())


async def _snapshot_para_trailing(ticker: str):
    """F2: insumo técnico do trailing dinâmico (ATR e velas), pelo MESMO STU que
    N1/N2/N3 leem — nada de um segundo caminho de candles com outro número.

    Custo: usa o `candle_cache` (`_MIN_DELTA_INTERVAL` de 45 s), então dentro de
    um ciclo de 5 min é no máximo 1 requisição por ticker EM POSIÇÃO — não pelo
    universo. Candles DIÁRIOS: a F2 não depende do ADR do intraday.
    Falha vira None: o agente cai para o percentual e registra a troca.
    """
    try:
        return await technical_snapshot.get(ticker, None,
                                            lambda rng: candle_provider.get_history(ticker, rng=rng))
    except Exception:  # noqa: BLE001 — insumo do trailing nunca derruba o ciclo
        return None


@app.post("/api/cycle")
async def cycle(scope: Optional[str] = Depends(current_scope)):
    # FASE 3.1: o motor de regras foi PORTADO para agent.py (roda também no
    # scheduler do servidor) — este endpoint (ciclo foreground) o reusa.
    positions = store.get(_conn, "positions", user_id=scope)
    await agent_mod.run_cycle_for(_conn, scope, candle_provider.get_quotes_exclusive,
                                  snapshot_getter=_snapshot_para_trailing,  # F2
                                  option_quotes_getter=options_provider.get_options)  # v2
    out = store.public_state(_conn, user_id=scope)
    out["quotes"] = await candle_provider.get_quotes_exclusive([p["t"] for p in positions]) if positions else {}
    return out


# FASE 2 (2.5) — telemetria didática: histórico de análises por ativo.
@app.post("/api/analysis-log/{ticker}")
async def analysis_log(ticker: str, body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    t = _normalize_ticker(ticker)
    entry = dict(body or {})
    entry.setdefault("at", now_str())
    store.push_analysis_log(_conn, t, entry, user_id=scope)
    return store.public_state(_conn, user_id=scope)


# qa/30 (Fase A) — autoavaliação da IA: lista crua (debug/detalhe) e
# estatísticas agregadas (painel "Eficiência da IA" em Observabilidade).
# Fora do public_state DE PROPÓSITO — pode crescer até 500 registros e não
# precisa ir em toda resposta de ação da carteira, só quando a tela é aberta.
@app.get("/api/analysis-outcomes")
async def get_analysis_outcomes(scope: Optional[str] = Depends(current_scope)):
    return {"outcomes": db.kv_get(_conn, "analysisOutcomes", [], user_id=scope) or []}


@app.get("/api/analysis-outcomes/stats")
async def get_analysis_outcomes_stats(modo: Optional[str] = None, tipo: Optional[str] = None,
                                       scope: Optional[str] = Depends(current_scope)):
    outcomes = db.kv_get(_conn, "analysisOutcomes", [], user_id=scope) or []
    return analysis_outcomes.compute_stats(outcomes, modo=modo, tipo=tipo)


# qa/45: Atividade da IA — custo estimado (R$) acumulado + histórico por chamada.
@app.get("/api/ai-activity")
async def get_ai_activity(scope: Optional[str] = Depends(current_scope)):
    return ai_activity.snapshot(_conn, scope)


# qa/35 (P2): export CSV do registro bruto — o usuário leva a estatística pra
# planilha. Texto simples (o app compartilha/copia); célula vazia = sem dado.
@app.get("/api/analysis-outcomes/export.csv")
async def get_analysis_outcomes_csv(scope: Optional[str] = Depends(current_scope)):
    outcomes = db.kv_get(_conn, "analysisOutcomes", [], user_id=scope) or []
    csv = analysis_outcomes.to_csv(outcomes)
    return PlainTextResponse(csv, media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": "attachment; filename=boris-eficiencia-ia.csv"})


# FASE 3.3b — registro do token de push do aparelho (exige conta).
# 2026-08-05: a chamada passa a carregar TAMBÉM o consentimento, o modo e o
# universo de ativos. Motivo: no aparelho a `config` é local (deviceStore grava
# em localStorage e nunca chama a API), então o servidor não tem outro jeito de
# saber se a pessoa quer o aviso de gatilho, em que vocabulário, e sobre quais
# ativos. Este é o único caminho que SEMPRE chega ao servidor nos dois stores.
@app.post("/api/push/register-token")
async def push_register(body: dict = Body(default={}), user: dict = Depends(require_user)):
    uid = user["id"]
    b = body or {}
    antes = len(push.tokens_for(_conn, uid))
    toks = push.register_token(_conn, uid, b.get("token") or "")
    if any(k in b for k in ("prefs", "modo", "universo")):
        prefs = dict(b.get("prefs") or {})
        if b.get("modo"):
            prefs["modo"] = b["modo"]
        if isinstance(b.get("universo"), list):
            prefs["universo"] = b["universo"]
        push.set_prefs(_conn, uid, prefs)
    # FASE 3 (observabilidade do push): a ativação também entra no Diário —
    # antes, uma falha no registro (ou sucesso silencioso) não deixava rastro.
    # 2026-08-05: só quando um aparelho NOVO entra. A mesma rota passou a ser o
    # canal de sincronismo das preferências (`syncPushPrefs` chama com token
    # vazio a cada troca de watchlist) — logar sempre encheria o Diário do
    # usuário de "aparelho registrado (0 token(s))", que é falso.
    configurado = push.is_configured()
    if len(toks) > antes:
        store.push_agent_log(_conn, [{
            "time": now_str(), "kind": "info" if configurado else "warn",
            "text": f"Push: aparelho registrado ({len(toks)} token(s) no total). APNs no servidor: "
                    + ("configurado ✓" if configurado else "AINDA NÃO configurado — rode scripts/configurar-apns.sh"),
        }], user_id=uid)
    return {"ok": True, "tokens": len(toks), "apnsConfigured": configurado}


# BLOCO D3/D4/E2 — Operador IA: visibilidade e demonstração.
@app.get("/api/agent/status")
async def agent_status(scope: Optional[str] = Depends(current_scope)):
    st = agent_mod.status_snapshot(_conn)
    ag = store.get(_conn, "agent", user_id=scope) or {}
    st["meuServerEnabled"] = bool(ag.get("serverEnabled"))
    # qa/41 (H6): EU tenho stop/alvo armado com o Operador desligado? Se True,
    # minha proteção só é avaliada com o app aberto — e isso não é bug do laço.
    st["minhaProtecaoSemOperador"] = bool(scope) and scope in agent_mod.list_protecao_sem_operador(_conn)
    st["push"] = {"configurado": push.is_configured(),
                  "topic": os.environ.get("APNS_TOPIC") or None,
                  "sandbox": os.environ.get("APNS_SANDBOX") == "1",
                  "meusAparelhos": len(push.tokens_for(_conn, scope)) if scope else 0}
    # C-35 (REPORT-01): estado do 2º kill-switch (push do gatilho) exposto AQUI
    # (não dentro de agent.status_snapshot() — o snapshot é do agente; o push
    # do gatilho é outro subsistema, misturar os dois criaria acoplamento que
    # a rota não precisa).
    st["timingWatchKillSwitch"] = timing_watch.kill_switch_on()
    return st


@app.post("/api/agent/run-now")
async def agent_run_now(user: dict = Depends(require_user)):
    """BLOCO D4 + FASE 3 (Operador): ciclo imediato em BACKGROUND.

    Antes o ciclo rodava DENTRO da request — com o Yahoo rate-limitado no
    Railway (fallback 1-a-1 + retries), estourava os 15s do cliente e o
    usuário via 'timeout'. Agora: dispara a task, responde na hora; o
    resultado aparece no Diário (/api/agent/log) e no status."""
    if agent_mod.kill_switch_on():
        raise HTTPException(409, "Kill-switch global ligado (B3_AGENT_KILL=1) — desligue para rodar.")
    uid = user["id"]

    async def _bg():
        try:
            await agent_mod.run_cycle_for(_conn, uid, candle_provider.get_quotes_exclusive, origem="manual",
                                          snapshot_getter=_snapshot_para_trailing,  # F2
                                          option_quotes_getter=options_provider.get_options)  # v2
        except Exception as e:  # noqa: BLE001 — o erro já foi para o agentLog
            print(f"[agent] run-now de {uid} falhou: {e}")

    asyncio.get_event_loop().create_task(_bg())
    store.push_agent_log(_conn, [{"time": now_str(), "kind": "info",
                                  "text": "Ciclo manual solicitado — rodando em segundo plano; o resultado entra aqui no Diário."}], user_id=uid)
    return {"ok": True, "iniciado": True,
            "mensagem": "Ciclo iniciado em segundo plano — acompanhe no Diário do operador."}


@app.get("/api/agent/log")
async def agent_log(n: int = 50, user: dict = Depends(require_user)):
    """FASE 3 (Operador): Diário — cauda do log persistente do agente."""
    log = db.kv_get(_conn, "agentLog", [], user_id=user["id"]) or []
    n = max(1, min(200, int(n or 50)))
    return {"log": list(reversed(log[-n:])), "total": len(log)}


@app.post("/api/push/test")
async def push_test(user: dict = Depends(require_user)):
    """BLOCO E2 + FASE 3 (observabilidade): smoke test do APNs, com o MOTIVO
    exato de qualquer falha gravado no Diário — antes as 3 causas possíveis
    (não configurado / sem token / token rejeitado) caíam na mesma mensagem
    genérica e não deixavam rastro nenhum no servidor."""
    uid = user["id"]
    if not push.is_configured():
        store.push_agent_log(_conn, [{"time": now_str(), "kind": "error",
                                      "text": "Push: teste pedido, mas APNs NÃO está configurado no servidor (faltam variáveis no Railway — rode scripts/configurar-apns.sh)."}], user_id=uid)
        raise HTTPException(409, "APNs não configurado no servidor — rode scripts/configurar-apns.sh e confira as 4 variáveis no Railway.")
    r = await push.send_to_user(_conn, uid, "Boris+ — teste de push", "Push do Operador IA funcionando. ✓")
    if r["total"] == 0:
        store.push_agent_log(_conn, [{"time": now_str(), "kind": "warn",
                                      "text": "Push: teste pedido, mas NENHUM aparelho está registrado — toque em 'Ativar push das ações' no iPhone primeiro."}], user_id=uid)
        raise HTTPException(409, "Nenhum aparelho registrado — toque em 'Ativar push das ações' no iPhone e tente de novo.")
    if r["sent"] == 0:
        detalhes = "; ".join(r.get("detalhes") or [])[:280]
        store.push_agent_log(_conn, [{"time": now_str(), "kind": "error",
                                      "text": f"Push: teste pedido — {r['total']} token(s) registrado(s), TODOS rejeitados pela Apple. {detalhes} — provável mismatch de bundle id (APNS_TOPIC) ou ambiente (sandbox×produção)."}], user_id=uid)
        raise HTTPException(409, f"Todos os {r['total']} token(s) foram rejeitados pela Apple — provável mismatch de bundle id/ambiente (sandbox×produção). Veja o Diário (Observabilidade) para os detalhes.")
    store.push_agent_log(_conn, [{"time": now_str(), "kind": "buy",
                                  "text": f"Push: teste enviado com sucesso a {r['sent']}/{r['total']} aparelho(s)."}], user_id=uid)
    return {"ok": True, "enviados": r["sent"], "total": r["total"]}


# FASE 3.1 — scheduler do agente server-side (kill-switch: B3_AGENT_KILL=1).
@app.on_event("startup")
async def _start_agent_scheduler():
    # Higiene de env (2026-08-01): achamos em produção uma variável chamada
    # "B3_MANAGED_LLM_KEY " (espaço no fim) — os.environ.get do nome exato
    # nunca a lê e a feature fica DESLIGADA em silêncio. Um aviso no boot
    # transforma esse silêncio em diagnóstico de 1 linha.
    suspeitas = [k for k in os.environ
                 if k != k.strip() and k.strip().startswith(("B3_", "APNS_", "APPLE_", "BOLSAI"))]
    if suspeitas:
        obslog.log("env", "variáveis com espaço no NOME (nunca são lidas): "
                   + ", ".join(repr(k) for k in suspeitas), level="error")

    async def _notify(uid, title, body, extra=None):
        # `extra` (260824-i45, item 1): sem isto o payload chega sem `data.t`,
        # `web/src/notify.js:382` descarta em silêncio e o toque no push abre o
        # app sem destino. `send_to_user` já sabia tratar `extra`/`None`.
        await push.send_to_user(_conn, uid, title, body, extra=extra)
    asyncio.get_event_loop().create_task(
        agent_mod.scheduler_loop(_conn, candle_provider.get_quotes_exclusive, notify_push=_notify,
                                 radar_fetch=candle_provider.get_history,  # FASE 4 (1.3)
                                 snapshot_getter=_snapshot_para_trailing,  # F2
                                 intraday_fetch=_intraday_fetch,  # ADR-001 item 7
                                 option_quotes_getter=options_provider.get_options,  # v2
                                 analytics_conn=_analytics_conn)  # qa/47
    )
    # FASE 5 (lançamento): higiene de sessões — purga as expiradas no boot e a
    # cada 24h (o resolve_session já apaga lazy a sessão consultada; isto cobre
    # tokens abandonados que nunca mais são usados).
    async def _session_gc():
        while True:
            try:
                n = auth.purge_expired_sessions(_conn)
                if n:
                    obslog.log("auth", f"purga de sessões expiradas: {n} removida(s)")
            except Exception as e:  # noqa: BLE001 — GC nunca derruba o servidor
                obslog.log("auth", "purga de sessões falhou: " + str(e), level="error")
            await asyncio.sleep(24 * 3600)
    asyncio.get_event_loop().create_task(_session_gc())


# ---- Instalar o iOS Ad Hoc via link (fora do TestFlight) — 2026-08-01 ------
# NÃO é distribuição pública: só funciona em aparelhos cujo UDID foi
# registrado no Apple Developer portal ANTES do build (pegue o UDID plugando
# o iPhone no Mac — Xcode > Window > Devices and Simulators — nunca por um
# "coletor" web: aquele protocolo depende de um payload assinado que não dá
# ---- qa/20 (B3): política de privacidade em URL PÚBLICA ----
# O App Store Connect exige uma Privacy Policy URL; até aqui o texto existia
# só como POLITICA-PRIVACIDADE.md no repo, sem rota nenhuma. Fonte ÚNICA: o
# próprio .md (o que se versiona é o que se publica). Render mínimo de
# markdown — títulos, negrito e listas, o dialeto que o documento usa — para
# leitura confortável no navegador; nada de dependência nova.
#
# 2026-08-17: vivia na RAIZ do repo (um nível acima de server/). Achado
# investigando os dados pro OAuth consent screen do Google (que EXIGE essa
# URL): /privacidade estava 404 em produção — mesma classe de bug que
# server/web_dist e server/admin_dist existem para evitar. rootDirectory do
# Railway é /server (ver server/railway.json via publicar-web.sh/publicar-
# admin.sh); qualquer coisa fora dessa árvore não vai no deploy, mesmo
# versionada e mesmo passando nos testes locais (que rodam do checkout
# completo, não do container). O .md morou "fora" desde o dia em que a rota
# foi criada; só a IDA A PRODUÇÃO revelou.
_POLITICA_MD = Path(__file__).resolve().parent.parent / "POLITICA-PRIVACIDADE.md"


def _politica_html(md: str) -> str:
    import html as _html
    import re as _re

    def inline(t: str) -> str:
        t = _html.escape(t)
        return _re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)

    corpo, lista, para = [], [], []

    def fecha_lista():
        nonlocal lista
        if lista:
            corpo.append("<ul>" + "".join(f"<li>{x}</li>" for x in lista) + "</ul>")
            lista = []

    def fecha_para():
        nonlocal para
        if para:
            # O .md é prosa com quebra "dura" a ~76 colunas; em markdown a
            # quebra simples é espaço. Juntar ANTES do inline também deixa o
            # **negrito** que atravessa linhas ser convertido.
            corpo.append("<p>" + inline(" ".join(para)) + "</p>")
            para = []

    for raw in md.split("\n"):
        linha = raw.rstrip()
        if not linha.strip():
            fecha_para(); fecha_lista(); continue
        m = _re.match(r"^(#{1,3})\s+(.*)$", linha)
        if m:
            fecha_para(); fecha_lista()
            corpo.append(f"<h{len(m.group(1))}>{inline(m.group(2))}</h{len(m.group(1))}>")
            continue
        b = _re.match(r"^\s*-\s+(.*)$", linha)
        if b:
            fecha_para(); lista.append(inline(b.group(1))); continue
        # Continuação de item: no .md a prosa do bullet segue nas linhas
        # seguintes com indentação — pertence ao MESMO <li>, não a um <p>.
        if lista and raw.startswith("  "):
            lista[-1] += " " + inline(linha.strip()); continue
        i = _re.match(r"^\*([^*].*)\*$", linha.strip())
        if i:
            fecha_para(); fecha_lista()
            corpo.append(f"<p><em>{_html.escape(i.group(1))}</em></p>")
            continue
        fecha_lista(); para.append(linha)
    fecha_para(); fecha_lista()
    return (
        "<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\"/>"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>"
        "<title>Política de Privacidade — Boris+</title>"
        "<style>body{margin:0;background:#10121a;color:#eef1f8;font:16px/1.6 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}"
        "main{max-width:720px;margin:0 auto;padding:40px 22px}h1{font-size:26px}h2{font-size:19px;margin-top:28px}"
        "p,li{color:#c6cede}em{color:#9aa6b6}strong{color:#eef1f8}ul{padding-left:22px}</style></head>"
        "<body><main>" + "".join(corpo) + "</main></body></html>"
    )


@app.get("/privacidade")
@app.get("/privacy")
async def politica_privacidade():
    try:
        md = _POLITICA_MD.read_text(encoding="utf-8")
    except OSError:
        raise HTTPException(404, "Política indisponível.")
    from fastapi.responses import HTMLResponse
    return HTMLResponse(_politica_html(md))


# pra verificar sem um iPhone físico, risco alto para uma ferramenta de teste
# só usada por pouca gente). server/ios_dist é publicado por
# scripts/publicar-ipa.sh a partir do .ipa exportado no Xcode como Ad Hoc
# (nunca "App Store Connect"). Dormente até esse diretório existir — mesmo
# padrão do web_dist. Precisa ser ABERTO NO SAFARI do iPhone (itms-services
# não funciona em outro navegador nem em preview de app de mensagem).
_IOS_DIST = Path(__file__).resolve().parent.parent / "ios_dist"
if _IOS_DIST.exists():
    @app.get("/ios/manifest.plist")
    async def _ios_manifest():
        # Content-Type text/xml é a convenção da Apple p/ OTA distribution;
        # StaticFiles não reconhece a extensão .plist e serviria octet-stream.
        return FileResponse(str(_IOS_DIST / "manifest.plist"), media_type="text/xml")
    app.mount("/ios", StaticFiles(directory=str(_IOS_DIST), html=True), name="ios")

# ---- ADR-011/qa/47: portal de observabilidade em /admin/* (mesmo container,
# sem infra nova — decisão do Alex, 2026-08-14). Bundle PÚBLICO (como o do
# app consumidor abaixo) — o gate de verdade é `require_permission(...)`
# (ADR-013) nas rotas /api/obs/*, /api/admin/*, /api/analytics/*, não no
# arquivo estático. Precisa vir ANTES do mount "/" (catch-all), senão nunca
# seria alcançado. Publicado com scripts/publicar-admin.sh.
_ADMIN_DIST = Path(__file__).resolve().parent.parent / "admin_dist"
if _ADMIN_DIST.exists():
    app.mount("/admin", StaticFiles(directory=str(_ADMIN_DIST), html=True), name="admin")

# ---- Servir o app web em producao (mesma origem) — F4 mínimo (2026-08-01) ---
# O serviço do Railway tem rootDirectory=/server (ver server/railway.json): o
# builder NUNCA enxerga a árvore ../web fora dessa raiz. Por isso o bundle vive
# em server/web_dist — TRACKED no git (não é `web/dist`, que segue efêmero e
# gitignored) — publicado com `scripts/publicar-web.sh`, que builda, copia e
# sincroniza o carimbo (mesmo padrão do entregar.sh, sem o passo de iOS).
# Same-origin: web/src/api.js já resolve caminho relativo fora do modo nativo,
# então nenhuma mudança de CORS foi necessária.
_DIST = Path(__file__).resolve().parent.parent / "web_dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="web")
