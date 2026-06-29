"""B3 Agente - backend FastAPI.
Persistencia em SQLite (web). Cotacoes via Yahoo, analise via LLM.
O cliente iOS persiste no proprio aparelho e envia config/skill no corpo do
/api/analyze; o cliente web usa a config persistida aqui.
"""
from typing import Optional
from datetime import datetime
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import db, indicators, llm, plan, store, technical_models, tickers, yahoo
from .catalog import is_catalog_ticker
from .options_api import router as options_router
from .options_provider_yahoo import get_options as _get_options_for_status

app = FastAPI(title="B3 Agente API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=False,
)

_conn = db.connect()
store.ensure_defaults(_conn)
app.include_router(options_router)


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


@app.post("/api/auth/register")
async def auth_register(body: dict = Body(default={})):
    try:
        user = auth.register_email(_conn, body.get("email", ""), body.get("password", ""), body.get("name", ""))
    except auth.AuthError as e:
        raise HTTPException(400, str(e))
    _apply_seed(user["id"], body)
    return _auth_payload(user)


@app.post("/api/auth/login")
async def auth_login(body: dict = Body(default={})):
    try:
        user = auth.login_email(_conn, body.get("email", ""), body.get("password", ""))
    except auth.AuthError as e:
        raise HTTPException(401, str(e))
    _apply_seed(user["id"], body)   # idempotente: só semeia conta vazia
    return _auth_payload(user)


@app.post("/api/auth/oauth")
async def auth_oauth(body: dict = Body(default={})):
    provider = str(body.get("provider", "")).lower()
    id_token = body.get("idToken") or body.get("id_token") or ""
    try:
        claims = auth.verify_oauth_token(provider, id_token)
        if not claims.get("sub"):
            raise auth.AuthError("Token sem identificador de usuário.")
        user = auth.upsert_oauth_user(_conn, provider, claims["sub"], claims.get("email"), claims.get("name"))
    except auth.AuthError as e:
        raise HTTPException(401, str(e))
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
    a linha em users e as sessões. Irreversível."""
    store.delete_user_data(_conn, user["id"])
    return {"ok": True, "deleted": user["id"]}


# ===========================================================================
# FASE 3 (item 2) — IA gerenciada: caminho PARALELO ao BYOK.
# BYOK (chave no config) tem prioridade e NÃO consome cota. Sem BYOK, usuário
# LOGADO cai na IA gerenciada (modelo barato do servidor) sob cota diária +
# rate limit por usuário. Anônimo e sem BYOK seguem o comportamento atual.
# ===========================================================================
def _ai_apply_managed(scope, config):
    """Retorna (config_efetiva, consume). Levanta 402 se a cota/rate bloquear.
    Chame consume() APÓS o LLM responder com sucesso (falha não gasta cota)."""
    if llm.resolve_key(config):                      # BYOK utilizável → sem cota
        return config, (lambda: None)
    mcfg = managed.managed_config()
    if scope and mcfg:                               # logado + gerenciada habilitada
        ok, reason = metering.check(_conn, scope, quota=managed.daily_quota(), rate_per_min=managed.rate_per_min())
        if not ok:
            raise HTTPException(402, reason)
        return mcfg, (lambda: metering.consume(_conn, scope))
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


def now_str() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path.startswith("/api"):
        client = request.client.host if request.client else "?"
        print(f"[req] {request.method} {request.url.path} <- {client}")
    return await call_next(request)


@app.get("/api/health")
async def health(scope: Optional[str] = Depends(current_scope)):
    return {"ok": True}


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
    store.set_skill(_conn, body.get("name"), body.get("text"), user_id=scope)
    return store.public_state(_conn, user_id=scope)


@app.post("/api/skill/restore")
async def restore_skill(scope: Optional[str] = Depends(current_scope)):
    store.restore_skill(_conn, user_id=scope)
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
async def history(ticker: str, scope: Optional[str] = Depends(current_scope)):
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    h = await yahoo.get_history(t)
    h["candles"] = indicators.sanitize_candles(h.get("candles"))
    return h


# ---- Analise tecnica: candles + indicadores (serie continua ~1 ano) ----
_TECH_CACHE: dict = {}   # ticker -> (ts, payload)
_TECH_TTL = 600          # 10 min
_TECH_KEEP = 252         # ~1 ano util exibido (calculo usa warmup maior)
import re as _re
import time as _time
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
async def technicals(ticker: str, scope: Optional[str] = Depends(current_scope)):
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker invalido.")
    hit = _TECH_CACHE.get(t)
    if hit and (_time.time() - hit[0]) < _TECH_TTL:
        return hit[1]
    # janela longa (warmup p/ medias) recortada para ~1 ano exibido
    hist = await yahoo.get_history(t, rng="2y")
    candles = indicators.sanitize_candles(hist["candles"])
    if not candles:
        raise HTTPException(502, "Sem historico para " + t)
    full = indicators.compute(candles)
    keep = min(len(candles), _TECH_KEEP)
    sliced = indicators.slice_tail(candles, full["indicators"], full["summary"], keep)
    last = sliced["candles"][-1]
    first = sliced["candles"][0]
    change_pct = ((last["close"] - first["close"]) / first["close"] * 100) if first["close"] else 0
    payload = {
        "t": t,
        "currency": hist.get("currency", "BRL"),
        "candles": sliced["candles"],
        "indicators": sliced["indicators"],
        "summary": sliced["summary"],
        "periodChangePct": round(change_pct, 2),
        "at": now_str(),
    }
    _TECH_CACHE[t] = (_time.time(), payload)
    return payload


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
    config, _consume_ai = _ai_apply_managed(scope, config)
    skill = body.get("skill") or store.get(_conn, "skill", user_id=scope)
    profile = body.get("profile") or store.get(_conn, "profile", user_id=scope)
    account = body.get("account") or {
        "cash": store.get(_conn, "cash", user_id=scope),
        "budget": (store.get(_conn, "config", user_id=scope) or {}).get("initialBudget"),
    }
    try:
        quote = await yahoo.get_quote(t)
    except Exception:
        quote = None
    hist = await yahoo.get_history(t, rng="2y")
    candles = indicators.sanitize_candles(hist.get("candles"))
    if not candles:
        raise HTTPException(502, "Sem historico para " + t)
    opt_status = await _options_status_for_llm(t) if model in ("opcoes", "completo") else {"available": None, "reason": "Não consultado para este modelo."}
    context = technical_models.build_context(t, quote, candles, model, opt_status)
    try:
        result = await llm.analyze_structured(config, skill, profile, account, t, context)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, llm.public_error(e))
    _consume_ai()  # conta a cota só no sucesso
    payload = {
        "kpis": result.get("kpis"),
        "detail": result.get("detail"),
        "proposal": result.get("proposal"),
        "markdown": result.get("markdown"),
        "text": result.get("text"),
        "model": model,
        "modelLabel": context.get("modelLabel"),
        "technicalContext": technical_models.compact_for_response(context),
        "candles": len(candles),
        "candlesSentToLLM": min(len(candles), 120),
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
    history_data = await yahoo.get_history(t)
    history_data["candles"] = indicators.sanitize_candles(history_data.get("candles"))
    try:
        result = await llm.analyze(config, skill, profile, account, t, quote, history_data)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, llm.public_error(e))
    _consume_ai()  # conta a cota só no sucesso
    at = now_str()
    payload = {
        "kpis": result.get("kpis"),
        "detail": result.get("detail"),
        "proposal": result.get("proposal"),
        "markdown": result.get("markdown"),
        "text": result.get("text"),
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
    config, _consume_ai = _ai_apply_managed(scope, config)
    profile = (body or {}).get("profile") or store.get(_conn, "profile", user_id=scope)
    account = (body or {}).get("account") or {
        "cash": store.get(_conn, "cash", user_id=scope),
        "budget": (store.get(_conn, "config", user_id=scope) or {}).get("initialBudget"),
    }
    prompt = (body or {}).get("prompt") or (store.get(_conn, "llmPrompts", user_id=scope) or {}).get("carteiraStopAlvo") or ""
    try:
        quote = await yahoo.get_quote(t)
    except Exception:
        quote = None
    history_data = await yahoo.get_history(t)
    history_data["candles"] = indicators.sanitize_candles(history_data.get("candles"))
    try:
        res = await llm.analyze_carteira(config, profile, account, t, quote, history_data, prompt)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, llm.public_error(e))
    _consume_ai()  # conta a cota só no sucesso
    return {"t": t, "quote": quote, "at": now_str(), **res}


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
    store.buy(_conn, t, qty, price, user_id=scope)
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
    store.sell(_conn, t, quote["price"], user_id=scope)
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


@app.post("/api/cycle")
async def cycle(scope: Optional[str] = Depends(current_scope)):
    positions = store.get(_conn, "positions", user_id=scope)
    ag = store.get(_conn, "agent", user_id=scope)
    quotes_data = await yahoo.get_quotes([p["t"] for p in positions])
    events = []
    for pos in list(positions):
        q = quotes_data.get(pos["t"]) or {}
        price = q.get("price")
        if price is None:
            continue
        breach_stop = pos.get("stop") is not None and price <= pos["stop"]
        hit_alvo = pos.get("alvo") is not None and price >= pos["alvo"]
        if breach_stop or hit_alvo:
            motivo = "stop atingido" if breach_stop else "alvo atingido"
            if ag.get("autonomous"):
                store.sell(_conn, pos["t"], price, user_id=scope)
                events.append({"time": "Agora", "kind": "buy", "text": f"Protecao automatica: {pos['t']} vendido ({motivo}) a R$ {price:.2f}."})
            else:
                events.append({"time": "Agora", "kind": "warn", "text": f"Atencao: {pos['t']} com {motivo} (R$ {price:.2f}). Modo autonomo desligado."})
    if not events:
        events.append({"time": "Agora", "kind": "info", "text": "Ciclo executado - posicoes remarcadas a mercado. Nenhum stop/alvo atingido."})
    store.push_events(_conn, events, user_id=scope)
    out = store.public_state(_conn, user_id=scope)
    out["quotes"] = quotes_data
    return out


# ---- Servir o app web em producao (mesma origem) ----
_DIST = Path(__file__).resolve().parent.parent.parent / "web" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="web")
