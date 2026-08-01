"""BolsIA - backend FastAPI.
Persistencia em SQLite (web). Cotacoes via Yahoo, analise via LLM.
O cliente iOS persiste no proprio aparelho e envia config/skill no corpo do
/api/analyze; o cliente web usa a config persistida aqui.
"""
import asyncio
import os
from typing import Optional
from datetime import datetime
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import db, indicators, llm, plan, setups, store, technical_models, tickers, yahoo
from . import candles as candles_mod  # Objetivo 4: período de candles configurável
from . import candle_cache  # Objetivo 5: cache de candles (delta + revalida último)
from . import scanner  # BLOCO 3: radar de mercado (varredura do universo)
from . import radar_daily  # FASE 4 (1.3): varredura automática 1x/dia + sob demanda
from . import analysis_outcomes  # qa/30 (Fase A): autoavaliação da IA (N1/N2 vs. comportamento real)
from . import ai_activity  # qa/45: custo (R$) + histórico de comportamento da IA
from . import fundamentals  # qa/36 (F10.2): fundamento × técnica (score, cache, rebaixamento)
from . import scan_deep  # FASE 1 (N1): aprofundamento IA do top-N do Radar
from . import candle_provider  # ADR-001: ponto único de entrada de candles
from . import technical_snapshot  # FASE 1 (STU): fonte única de N1/N2/N3
from . import model_catalog  # qa/49: catálogo de modelos por provedor + parâmetros aceitos
from . import agent as agent_mod  # FASE 3: agente autônomo server-side
from . import siwa  # FASE 4 (Bloco 2): Sign in with Apple — exchange + revoke
from . import push  # FASE 3.3b: APNs (no-op sem configuração)
from . import obslog  # FASE 5: observabilidade (log estruturado + ring buffer)
from .catalog import is_catalog_ticker
from .options_api import router as options_router
from .options_provider_yahoo import get_options as _get_options_for_status

app = FastAPI(title="BolsIA API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=False,
)

_conn = db.shared()  # FIX: conexão POR THREAD (pool do FastAPI) — ver db.py
store.ensure_defaults(_conn)
# FASE 5 (performance): liga o L2 persistente do cache de candles (SQLite no
# volume /data) — redeploy do Railway reidrata e busca só o delta recente.
candle_cache.configure_db(_conn)
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


def _public_user(u: dict) -> dict:
    """Nunca devolve pass_hash nem provider_sub ao cliente."""
    if not u:
        return None
    return {"id": u.get("id"), "email": u.get("email"), "name": u.get("name"), "provider": u.get("provider")}


def _apply_seed(user_id: str, body: dict) -> None:
    """Decisão B: 1º login com conta vazia adota o dado local como semente.
      - body["seed"] dict  => semente explícita (iOS envia o doc local, com BYOK).
      - body["seed"] False => começa limpo (só defaults).
      - ausente/None       => web: adota o escopo anônimo/global do servidor
                              (que contém a chave BYOK; nunca trafega ao cliente).
    Em todos os casos só semeia se a conta ainda estiver vazia."""
    seed = body.get("seed", "__default__") if isinstance(body, dict) else "__default__"
    if seed is False:
        store.ensure_defaults(_conn, user_id=user_id)
    elif isinstance(seed, dict):
        store.seed_user_from(_conn, user_id, seed)
    else:
        store.seed_user_from(_conn, user_id, store.export_sections(_conn, user_id=None))


def _auth_payload(user: dict) -> dict:
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
    rl_key = auth.throttle_key(_client_ip(request), str(body.get("email", "")))
    try:
        auth.throttle_check(rl_key)
        user = auth.register_email(_conn, body.get("email", ""), body.get("password", ""), body.get("name", ""))
    except auth.AuthError as e:
        auth.throttle_fail(rl_key)
        raise HTTPException(400, str(e))
    auth.throttle_clear(rl_key)
    _apply_seed(user["id"], body)
    return _auth_payload(user)


@app.post("/api/auth/login")
async def auth_login(request: Request, body: dict = Body(default={})):
    # FASE 5 (lançamento): rate limit por (ip, e-mail) — sucesso zera o contador.
    rl_key = auth.throttle_key(_client_ip(request), str(body.get("email", "")))
    try:
        auth.throttle_check(rl_key)
        user = auth.login_email(_conn, body.get("email", ""), body.get("password", ""))
    except auth.AuthError as e:
        auth.throttle_fail(rl_key)
        obslog.log("auth", "login falhou (ip=" + _client_ip(request) + ")", level="warn")
        raise HTTPException(401, str(e))
    auth.throttle_clear(rl_key)
    _apply_seed(user["id"], body)   # idempotente: só semeia conta vazia
    return _auth_payload(user)


@app.post("/api/auth/oauth")
async def auth_oauth(request: Request, body: dict = Body(default={})):
    provider = str(body.get("provider", "")).lower()
    id_token = body.get("idToken") or body.get("id_token") or ""
    # FASE 5 (lançamento): mesmo freio das demais rotas de auth (por ip+provedor).
    rl_key = auth.throttle_key(_client_ip(request), "oauth:" + provider)
    try:
        auth.throttle_check(rl_key)
        claims = auth.verify_oauth_token(provider, id_token)
        if not claims.get("sub"):
            raise auth.AuthError("Token sem identificador de usuário.")
        # FASE 4 (Bloco 2): a Apple só envia o nome no PRIMEIRO consentimento e
        # fora do id_token — a ponte nativa o repassa como hint; usado apenas
        # na criação (upsert ignora em contas existentes).
        name = claims.get("name") or (str(body.get("name") or "").strip() or None)
        user = auth.upsert_oauth_user(_conn, provider, claims["sub"], claims.get("email"), name)
    except auth.AuthError as e:
        auth.throttle_fail(rl_key)
        raise HTTPException(401, str(e))
    auth.throttle_clear(rl_key)
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
    return {"user": _public_user(user), "state": store.public_state(_conn, user_id=user["id"])}


@app.post("/api/auth/logout")
async def auth_logout(authorization: Optional[str] = Header(default=None)):
    if authorization:
        parts = authorization.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            auth.revoke_session(_conn, parts[1].strip())
    return {"ok": True}


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


@app.get("/api/ai/quota")
async def ai_quota(scope: Optional[str] = Depends(current_scope)):
    """Estado da IA do app para a UI: se a gerenciada existe, se o usuário tem
    BYOK e quanta cota resta hoje."""
    avail = managed.is_available()
    if not scope:
        return {"managed": avail, "loggedIn": False, "byok": False, "quota": None}
    cfg = store.get(_conn, "config", user_id=scope)
    byok = bool(llm.resolve_key(cfg))
    snap = metering.snapshot(_conn, scope, managed.daily_quota()) if (avail and not byok) else None
    return {"managed": avail, "loggedIn": True, "byok": byok, "quota": snap}


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
def _is_obs_admin(user: dict) -> bool:
    """Quem pode ver os logs do SERVIDOR (são globais, não por usuário):
      - B3_ADMIN_EMAILS definido (lista separada por vírgula) => e-mail na lista;
      - sem a env => apenas a PRIMEIRA conta criada (a do dono do app)."""
    emails = [e.strip().lower() for e in (os.environ.get("B3_ADMIN_EMAILS") or "").split(",") if e.strip()]
    if emails:
        return bool(user.get("email")) and user["email"].lower() in emails
    row = _conn.execute("SELECT id FROM users ORDER BY created_at ASC LIMIT 1").fetchone()
    return bool(row) and row[0] == user.get("id")


@app.get("/api/obs/logs")
async def obs_logs(n: int = 200, level: Optional[str] = None, cat: Optional[str] = None,
                   user: dict = Depends(require_user)):
    if not _is_obs_admin(user):
        raise HTTPException(403, "Logs do servidor são restritos ao administrador (defina B3_ADMIN_EMAILS no Railway).")
    return {"logs": obslog.recent(n, level=level, cat=cat), "stats": obslog.stats()}


# qa/42 (FinOps) — quanto a IA custou HOJE. Antes não havia como responder:
# nenhum caller lia o `usage` e não existia contador agregado (só cota por
# usuário). Restrito ao admin: é dado do servidor, não do usuário.
@app.get("/api/obs/usage")
async def obs_usage(user: dict = Depends(require_user)):
    if not _is_obs_admin(user):
        raise HTTPException(403, "Uso da IA é restrito ao administrador (defina B3_ADMIN_EMAILS no Railway).")
    cap = managed.global_daily_cap()
    return {
        "tokens": llm.usage_snapshot(),              # por modelo, do dia (memória: zera no deploy)
        "analisesGerenciadas": metering.global_snapshot(_conn, cap),  # persistido, todos os usuários
        "iaGerenciadaAtiva": bool(managed.managed_config()),
        "tetoGlobalDia": cap,                        # None = ilimitado (B3_MANAGED_GLOBAL_DAILY_CAP)
        "cotaPorUsuarioDia": managed.daily_quota(),
        # ADR-001 (Decisão 5): o fetch de candles é instrumentado como a IA já
        # era. `candles.alerta=true` é o gatilho declarado do plano B — taxa de
        # não-200 acima de 2% em 3 pregões reabre a decisão de provedor.
        "candles": candle_provider.snapshot(),
    }


# FASE 8B (diagnóstico): carimbo de build do BACKEND — confirma qual código o
# Railway está rodando (o front tem o dele em web/src/version.js).
SERVER_BUILD_ID = "F10-20260731-01"  # Auditoria dos prompts LLM (A1-A8, M1-M5): fonte canônica ampliada, guardrails e paridade cliente.
# Normalmente sincronizado pelo entregar.sh a partir de web/src/version.js; num deploy
# SÓ de backend (sem rebuild do front) bumpamos aqui para /api/health rastrear o servidor.


@app.get("/api/health")
async def health(scope: Optional[str] = Depends(current_scope)):
    return {"ok": True, "build": SERVER_BUILD_ID}


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
    store.set_watchlist(_conn, body.get("tickers") or [], user_id=scope)
    return store.public_state(_conn, user_id=scope)




@app.post("/api/watchlist/add")
async def watchlist_add(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    """Adiciona um ticker digitado pelo usuario. A EXISTENCIA e confirmada pelo
    Yahoo Finance (sufixo .SA) — a IA nao decide isso."""
    t = _normalize_ticker(str(body.get("ticker", "")))
    if not t or len(t) < 4:
        raise HTTPException(400, "Informe um ticker valido da B3 (ex.: PETR4).")
    try:
        q = await yahoo.get_quote(t)
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
    # GANCHO FREEMIUM (hoje sempre permite): limite de ativos do tier gratuito.
    allowed, reason = plan.can_add_ticker(len(store.get(_conn, "watchlist", user_id=scope)))
    if not allowed:
        raise HTTPException(402, reason)  # 402 Payment Required (fase futura)
    name = res["n"]
    store.add_custom(_conn, t, name, user_id=scope)
    wl = store.get(_conn, "watchlist", user_id=scope)
    if t not in wl:
        store.set_watchlist(_conn, wl + [t], user_id=scope)
    out = store.public_state(_conn, user_id=scope)
    out["added"] = {"t": t, "n": name, "price": res["price"], "change": res["change"]}
    return out


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
        q = await yahoo.get_quote(t)
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
    data = await yahoo.get_quotes(wanted)
    return {"quotes": data, "at": now_str()}


@app.get("/api/history/{ticker}")
async def history(ticker: str, period: Optional[str] = None, scope: Optional[str] = Depends(current_scope)):
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    h = await candle_provider.get_history(t, rng=candles_mod.period_to_range(period))  # Objetivo 4
    h["candles"] = indicators.sanitize_candles(h.get("candles"))
    return h


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
            "source": chain.get("source") or "yfinance",
            "expiration": chain.get("expiration"),
            "expirationsCount": len(chain.get("expirations") or []),
            "callsCount": len(calls),
            "putsCount": len(puts),
            "warning": chain.get("warning"),
        }
    except Exception as e:  # noqa: BLE001
        return {
            "available": False,
            "source": "yfinance",
            "reason": str(e) or "O yfinance não retornou cadeia de opções para este ativo.",
        }

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
    }
    return payload


# ---- BLOCO D: AutoFill nativo do iOS (Chaveiro) ----
# O iOS só oferece usuário+senha salvos dentro do app se o domínio declarar o
# vínculo via este arquivo + capability "Associated Domains" no Xcode com
# `webcredentials:b3agente-production.up.railway.app`. O appID vem da env
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
    if tickers:
        return await _enrich_fundamentos(await scanner.run_scan(period=period, universe=tickers, fetch=candle_provider.get_history))
    p = candles_mod.normalize_period(period)
    if not force:
        stored = await asyncio.to_thread(radar_daily.get_stored, _conn, p)
        if stored:
            return await _enrich_fundamentos(stored)
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
    return scan_deep.estimate(payload, n, p, modo=modo)


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
        with llm.collect_usage() as _uso:  # qa/45: custo desta leitura do Radar
            res = await llm.analyze_deep(ai_config, profile, t, snap["context"], setups_payload, modo=modo)
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
                    user_id=scope,
                )
        except Exception as e:  # noqa: BLE001 — registro é best-effort
            print(f"[analysis-outcomes] registro N1 falhou p/ {t}: {e}")
        return res

    try:
        return await scan_deep.run_deep(payload, n, p, deep_call, modo=modo)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, llm.public_error(e))


# ---- Analise pela LLM (config opcional no corpo, para o handset) ----
@app.post("/api/technical/analyze/{ticker}")
async def analyze_technical_model(ticker: str, body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    allowed, reason = plan.can_analyze(0)
    if not allowed:
        raise HTTPException(402, reason)
    body = body or {}
    model = technical_models.normalize_model(body.get("model") or body.get("technicalModel"))
    config = body.get("config") or store.get(_conn, "config", user_id=scope)
    # FASE 8B (B3): captura o modo ANTES do managed (que pode recriar a config)
    modo = (config or {}).get("appMode")
    config, _consume_ai = _ai_apply_managed(scope, config)
    # FASE 8B (R2): a instrução do agente é POR MODO — a mesa usa a skill do
    # operador (iOS manda a certa no corpo; web escolhe pela config do escopo).
    skill = body.get("skill") or store.get(_conn, "skillOperador" if modo == "operador" else "skill", user_id=scope)
    profile = body.get("profile") or store.get(_conn, "profile", user_id=scope)
    account = body.get("account") or {
        "cash": store.get(_conn, "cash", user_id=scope),
        "budget": (store.get(_conn, "config", user_id=scope) or {}).get("initialBudget"),
    }
    try:
        quote = await yahoo.get_quote(t)
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
    try:
        with llm.collect_usage() as _uso:  # qa/45: captura tokens desta chamada
            result = await llm.analyze_structured(config, skill, profile, account, t, context, modo=modo)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, llm.public_error(e))
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
            user_id=scope,
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
        "setupsRadar": context.get("setupsRadar"),
        # qa/36: fundamento (score + métricas) + resultado do rebaixamento.
        "fundamento": fundamento,
        "confiancaFinal": conf_final,
        "rebaixadoPorFundamento": rebaixado,
        "at": now_str(),
    }
    if not body.get("config"):
        store.set_analysis(_conn, t, payload, user_id=scope)
    return {"t": t, "quote": quote, **payload}


@app.post("/api/analyze/{ticker}")
async def analyze(ticker: str, body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    # GANCHO FREEMIUM (hoje sempre permite): limite de analises/mes do gratuito.
    allowed, reason = plan.can_analyze(0)  # FUTURO: passar a contagem do mes do usuario
    if not allowed:
        raise HTTPException(402, reason)
    config = (body or {}).get("config") or store.get(_conn, "config", user_id=scope)
    config, _consume_ai = _ai_apply_managed(scope, config)
    skill = (body or {}).get("skill") or store.get(_conn, "skill", user_id=scope)
    profile = (body or {}).get("profile") or store.get(_conn, "profile", user_id=scope)
    # capital simulado disponivel: handset envia no corpo; web usa o estado
    account = (body or {}).get("account") or {
        "cash": store.get(_conn, "cash", user_id=scope),
        "budget": (store.get(_conn, "config", user_id=scope) or {}).get("initialBudget"),
    }
    try:
        quote = await yahoo.get_quote(t)
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
    try:
        with llm.collect_usage() as _uso:  # qa/45
            result = await llm.analyze(config, skill, profile, account, t, quote, history_data)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, llm.public_error(e))
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
        quote = await yahoo.get_quote(t)
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
@app.post("/api/buy")
async def buy(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    t = str(body.get("t", "")).upper()
    qty = int(body.get("qty") or 0)
    t = _normalize_ticker(t)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    quote = await yahoo.get_quote(t)
    if not quote or quote.get("price") is None:
        raise HTTPException(502, "Sem cotacao para " + t)
    price = quote["price"]
    if qty * price > store.get(_conn, "cash", user_id=scope):
        raise HTTPException(400, "Caixa insuficiente.")
    store.buy(_conn, t, qty, price, user_id=scope, meta=body.get("meta"))  # FASE 2 (2.4)
    out = store.public_state(_conn, user_id=scope)
    out["priceUsed"] = round(price, 2)
    return out


@app.post("/api/sell")
async def sell(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    t = str(body.get("t", "")).upper()
    pos = next((p for p in store.get(_conn, "positions", user_id=scope) if p["t"] == t), None)
    if not pos:
        raise HTTPException(400, "Sem posicao em " + t)
    quote = await yahoo.get_quote(t)
    if not quote or quote.get("price") is None:
        raise HTTPException(502, "Sem cotacao para " + t)
    _qty = body.get("qty")  # FASE 2 (2.4): venda parcial opcional (lotes de 100)
    store.sell(_conn, t, quote["price"], user_id=scope, qty=int(_qty) if _qty else None)
    out = store.public_state(_conn, user_id=scope)
    out["priceUsed"] = round(quote["price"], 2)
    return out


@app.put("/api/position/{ticker}")
async def position(ticker: str, body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    store.set_position(_conn, ticker.upper(), stop=body.get("stop"), alvo=body.get("alvo"), has_stop=("stop" in body), has_alvo=("alvo" in body), user_id=scope)
    return store.public_state(_conn, user_id=scope)


@app.put("/api/agent")
async def agent(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    store.set_agent(_conn, body or {}, user_id=scope)
    return store.public_state(_conn, user_id=scope)


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
    await agent_mod.run_cycle_for(_conn, scope, yahoo.get_quotes,
                                  snapshot_getter=_snapshot_para_trailing)  # F2
    out = store.public_state(_conn, user_id=scope)
    out["quotes"] = await yahoo.get_quotes([p["t"] for p in positions]) if positions else {}
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
                             headers={"Content-Disposition": "attachment; filename=bolsia-eficiencia-ia.csv"})


# FASE 3.3b — registro do token de push do aparelho (exige conta).
@app.post("/api/push/register-token")
async def push_register(body: dict = Body(default={}), user: dict = Depends(require_user)):
    uid = user["id"]
    toks = push.register_token(_conn, uid, (body or {}).get("token") or "")
    # FASE 3 (observabilidade do push): a ativação também entra no Diário —
    # antes, uma falha no registro (ou sucesso silencioso) não deixava rastro.
    configurado = push.is_configured()
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
            await agent_mod.run_cycle_for(_conn, uid, yahoo.get_quotes, origem="manual",
                                          snapshot_getter=_snapshot_para_trailing)  # F2
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
    r = await push.send_to_user(_conn, uid, "BolsIA — teste de push", "Push do Operador IA funcionando. ✓")
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
    async def _notify(uid, title, body):
        await push.send_to_user(_conn, uid, title, body)
    asyncio.get_event_loop().create_task(
        agent_mod.scheduler_loop(_conn, yahoo.get_quotes, notify_push=_notify,
                                 radar_fetch=candle_provider.get_history,  # FASE 4 (1.3)
                                 snapshot_getter=_snapshot_para_trailing)  # F2
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


# ---- Servir o app web em producao (mesma origem) ----
_DIST = Path(__file__).resolve().parent.parent.parent / "web" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="web")
