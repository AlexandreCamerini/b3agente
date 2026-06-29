"""Operacoes de estado sobre o kv store. Funcoes recebem a conexao para
ficarem testaveis (o pytest cria a sua propria conexao em arquivo temporario).
"""
from datetime import datetime

from . import db, defaults
from .catalog import CATALOG, CATALOG_TICKERS, is_catalog_ticker

SECTIONS = ["config", "skill", "llmPrompts", "watchlist", "cash", "positions", "history", "agent", "analyses", "profile", "custom"]


def ensure_defaults(conn, user_id=None) -> None:
    d = defaults.default_state()
    for key in SECTIONS:
        if db.kv_get(conn, key, None) is None:
            db.kv_set(conn, key, d[key])
    # backfill de campos novos em estados ja existentes
    ag = db.kv_get(conn, "agent", None, user_id=user_id)
    if isinstance(ag, dict) and "intervalMin" not in ag:
        ag["intervalMin"] = d["agent"]["intervalMin"]
        db.kv_set(conn, "agent", ag, user_id=user_id)
    cfg = db.kv_get(conn, "config", None, user_id=user_id)
    if isinstance(cfg, dict) and "initialBudget" not in cfg:
        # usa o caixa atual como orcamento inicial, senao o padrao
        cur_cash = db.kv_get(conn, "cash", None, user_id=user_id)
        cfg["initialBudget"] = float(cur_cash) if isinstance(cur_cash, (int, float)) else d["config"]["initialBudget"]
        db.kv_set(conn, "config", cfg, user_id=user_id)
    cfg = db.kv_get(conn, "config", None, user_id=user_id)
    if isinstance(cfg, dict) and ("theme" not in cfg or "userName" not in cfg or "notif" not in cfg or "onboarded" not in cfg or "streak" not in cfg):
        cfg.setdefault("theme", d["config"]["theme"])
        cfg.setdefault("userName", d["config"]["userName"])
        cfg.setdefault("notif", dict(d["config"]["notif"]))
        cfg.setdefault("onboarded", d["config"]["onboarded"])
        cfg.setdefault("streak", dict(d["config"]["streak"]))
        db.kv_set(conn, "config", cfg, user_id=user_id)
    # FASE 2: backfill da coleção de prompts e de chaves novas, preservando
    # prompts já editados pelo usuário.
    lp = db.kv_get(conn, "llmPrompts", None, user_id=user_id)
    if not isinstance(lp, dict):
        lp = {}
    changed = False
    for k, v in d["llmPrompts"].items():
        if not isinstance(lp.get(k), str):
            lp[k] = v
            changed = True
    if changed:
        db.kv_set(conn, "llmPrompts", lp, user_id=user_id)


def get(conn, key, user_id=None):
    return db.kv_get(conn, key, defaults.default_state().get(key), user_id=user_id)


def put(conn, key, value, user_id=None) -> None:
    db.kv_set(conn, key, value, user_id=user_id)


def now_str() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


# ---------- mutadores ----------
def set_config(conn, patch: dict, user_id=None) -> dict:
    cfg = get(conn, "config", user_id=user_id)
    for k in ("provider", "model", "baseUrl"):
        if isinstance(patch.get(k), str):
            cfg[k] = patch[k]
    if patch.get("keySource") in ("env", "manual"):
        cfg["keySource"] = patch["keySource"]
    if isinstance(patch.get("apiKey"), str) and patch["apiKey"]:
        cfg["apiKey"] = patch["apiKey"]
    if patch.get("clearKey") is True:
        cfg["apiKey"] = ""
    if isinstance(patch.get("initialBudget"), (int, float)):
        cfg["initialBudget"] = max(100.0, min(100_000_000.0, round(float(patch["initialBudget"]), 2)))
    if patch.get("theme") in ("dark", "light", "system"):
        cfg["theme"] = patch["theme"]
    if isinstance(patch.get("userName"), str):
        cfg["userName"] = patch["userName"].strip()[:40]
    if "onboarded" in patch:
        cfg["onboarded"] = bool(patch["onboarded"])
    if isinstance(patch.get("streak"), dict):
        st = patch["streak"]
        days = st.get("days"); last = st.get("last")
        cfg["streak"] = {"days": int(days) if isinstance(days, (int, float)) else 0, "last": str(last or "")}
    if isinstance(patch.get("notif"), dict):
        base = cfg.get("notif") if isinstance(cfg.get("notif"), dict) else {}
        for k in ("enabled", "stop", "alvo", "agente", "variacao"):
            if k in patch["notif"]:
                base[k] = bool(patch["notif"][k])
        cfg["notif"] = base
    db.kv_set(conn, "config", cfg, user_id=user_id)
    return cfg


def reset_portfolio(conn, user_id=None) -> dict:
    """Recomeca do zero: caixa = orcamento inicial (config.initialBudget),
    sem posicoes nem historico. Mantem watchlist, skill, perfil e config."""
    cfg = get(conn, "config", user_id=user_id)
    budget = cfg.get("initialBudget")
    if not isinstance(budget, (int, float)):
        budget = defaults.default_state()["config"]["initialBudget"]
    db.kv_set(conn, "cash", round(float(budget), 2), user_id=user_id)
    db.kv_set(conn, "positions", [], user_id=user_id)
    db.kv_set(conn, "history", [], user_id=user_id)
    ag = get(conn, "agent", user_id=user_id)
    ag["events"] = [{"time": "Inicio", "kind": "info", "text": "Carteira reiniciada com o orcamento simulado de R$ " + ("%.2f" % budget) + "."}]
    db.kv_set(conn, "agent", ag, user_id=user_id)
    db.kv_set(conn, "analyses", {}, user_id=user_id)
    return public_state(conn, user_id=user_id)


def set_skill(conn, name=None, text=None, user_id=None) -> dict:
    sk = get(conn, "skill", user_id=user_id)
    if isinstance(name, str):
        sk["name"] = name
    if isinstance(text, str):
        sk["text"] = text
    db.kv_set(conn, "skill", sk, user_id=user_id)
    return sk


def restore_skill(conn, user_id=None) -> dict:
    sk = get(conn, "skill", user_id=user_id)
    sk["text"] = defaults.default_skill_text()
    db.kv_set(conn, "skill", sk, user_id=user_id)
    return sk


def set_llm_prompts(conn, patch: dict, user_id=None) -> dict:
    """FASE 2: salva/atualiza a coleção de prompts. Mescla apenas valores
    string; aceita chaves novas sem mudar a interface."""
    lp = get(conn, "llmPrompts", user_id=user_id)
    if not isinstance(lp, dict):
        lp = {}
    if isinstance(patch, dict):
        for k, v in patch.items():
            if isinstance(v, str):
                lp[str(k)] = v[:8000]
    db.kv_set(conn, "llmPrompts", lp, user_id=user_id)
    return lp


def custom_list(conn, user_id=None) -> list:
    c = get(conn, "custom", user_id=user_id)
    return c if isinstance(c, list) else []


def custom_tickers(conn, user_id=None) -> list:
    return [c["t"] for c in custom_list(conn, user_id=user_id) if isinstance(c, dict) and c.get("t")]


def known_tickers(conn, user_id=None) -> list:
    """Catalogo de 20 blue chips + tickers custom validados no Yahoo."""
    return list(CATALOG_TICKERS) + [t for t in custom_tickers(conn, user_id=user_id) if t not in CATALOG_TICKERS]


def is_known(conn, t: str, user_id=None) -> bool:
    return (t or "").upper() in set(known_tickers(conn, user_id=user_id))


def add_custom(conn, t: str, n: str = "", user_id=None) -> list:
    """Registra um ticker custom (ja validado no Yahoo). Idempotente."""
    t = (t or "").upper().strip()
    cur = custom_list(conn, user_id=user_id)
    if t and t not in CATALOG_TICKERS and not any(c.get("t") == t for c in cur):
        cur.append({"t": t, "n": n or t})
        db.kv_set(conn, "custom", cur, user_id=user_id)
    return cur


def set_profile(conn, patch: dict, user_id=None) -> dict:
    pf = dict(get(conn, "profile", user_id=user_id))
    if patch.get("risco") in ("conservador", "moderado", "agressivo"):
        pf["risco"] = patch["risco"]
    if patch.get("horizonte") in ("intraday", "swing", "posicao"):
        pf["horizonte"] = patch["horizonte"]
    if patch.get("objetivo") in ("preservacao", "renda", "crescimento"):
        pf["objetivo"] = patch["objetivo"]
    if patch.get("experiencia") in ("iniciante", "intermediario", "avancado"):
        pf["experiencia"] = patch["experiencia"]
    if isinstance(patch.get("toleranciaPerdaPct"), (int, float)):
        pf["toleranciaPerdaPct"] = max(0.5, min(20.0, round(float(patch["toleranciaPerdaPct"]), 2)))
    db.kv_set(conn, "profile", pf, user_id=user_id)
    return pf


def set_watchlist(conn, tickers: list, user_id=None) -> list:
    allowed = set(known_tickers(conn, user_id=user_id))
    ordered = known_tickers(conn, user_id=user_id)
    chosen = [t for t in tickers if (t or "").upper() in allowed]
    seen = set()
    valid = []
    # mantem a ordem do catalogo+custom, sem duplicar
    for t in ordered:
        if t in chosen and t not in seen:
            valid.append(t)
            seen.add(t)
    # inclui quaisquer escolhidos fora da ordenacao (defensivo)
    for t in chosen:
        tu = t.upper()
        if tu not in seen:
            valid.append(tu)
            seen.add(tu)
    db.kv_set(conn, "watchlist", valid, user_id=user_id)
    return valid


def set_agent(conn, patch: dict, user_id=None) -> dict:
    ag = get(conn, "agent", user_id=user_id)
    if isinstance(patch.get("autonomous"), bool):
        ag["autonomous"] = patch["autonomous"]
    if isinstance(patch.get("allocPct"), (int, float)):
        ag["allocPct"] = max(1, min(20, round(patch["allocPct"])))
    if isinstance(patch.get("intervalMin"), (int, float)):
        ag["intervalMin"] = max(1, min(240, round(patch["intervalMin"])))
    db.kv_set(conn, "agent", ag, user_id=user_id)
    return ag


def set_position(conn, t: str, stop=None, alvo=None, has_stop=False, has_alvo=False, user_id=None) -> None:
    positions = get(conn, "positions", user_id=user_id)
    for p in positions:
        if p["t"] == t:
            if has_stop:
                p["stop"] = None if stop in (None, "") else float(stop)
            if has_alvo:
                p["alvo"] = None if alvo in (None, "") else float(alvo)
    db.kv_set(conn, "positions", positions, user_id=user_id)


def buy(conn, t: str, qty: int, price: float, user_id=None) -> None:
    qty = max(100, round(qty / 100) * 100)
    positions = get(conn, "positions", user_id=user_id)
    cash = get(conn, "cash", user_id=user_id)
    history = get(conn, "history", user_id=user_id)
    existing = next((p for p in positions if p["t"] == t), None)
    if existing:
        total = existing["qty"] + qty
        existing["avg"] = round((existing["avg"] * existing["qty"] + price * qty) / total, 2)
        existing["qty"] = total
    else:
        positions.append({"t": t, "qty": qty, "avg": round(price, 2), "stop": None, "alvo": None})
    cash = round(cash - qty * price, 2)
    history.insert(0, {"date": now_str(), "type": "COMPRA", "t": t, "qty": qty, "price": round(price, 2), "pnl": None})
    db.kv_set(conn, "positions", positions, user_id=user_id)
    db.kv_set(conn, "cash", cash, user_id=user_id)
    db.kv_set(conn, "history", history, user_id=user_id)


def sell(conn, t: str, price: float, user_id=None):
    positions = get(conn, "positions", user_id=user_id)
    pos = next((p for p in positions if p["t"] == t), None)
    if not pos:
        return None
    cash = get(conn, "cash", user_id=user_id)
    history = get(conn, "history", user_id=user_id)
    pnl = round((price - pos["avg"]) * pos["qty"], 2)
    positions = [p for p in positions if p["t"] != t]
    cash = round(cash + pos["qty"] * price, 2)
    history.insert(0, {"date": now_str(), "type": "VENDA", "t": t, "qty": pos["qty"], "price": round(price, 2), "pnl": pnl})
    db.kv_set(conn, "positions", positions, user_id=user_id)
    db.kv_set(conn, "cash", cash, user_id=user_id)
    db.kv_set(conn, "history", history, user_id=user_id)
    return pnl


def push_events(conn, events: list, cap: int = 50, user_id=None) -> dict:
    ag = get(conn, "agent", user_id=user_id)
    ag["events"] = (events + ag.get("events", []))[:cap]
    db.kv_set(conn, "agent", ag, user_id=user_id)
    return ag


def set_analysis(conn, t: str, payload: dict, cap: int = 40, user_id=None) -> dict:
    analyses = get(conn, "analyses", user_id=user_id)
    if not isinstance(analyses, dict):
        analyses = {}
    analyses[t] = payload
    # limita o numero de analises guardadas (mantem as mais recentes por data)
    if len(analyses) > cap:
        items = sorted(analyses.items(), key=lambda kv: kv[1].get("at", ""), reverse=True)[:cap]
        analyses = dict(items)
    db.kv_set(conn, "analyses", analyses, user_id=user_id)
    return analyses



def _snap_num(v) -> float:
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return 0.0


def upsert_snapshot(conn, snap: dict, user_id=None) -> list:
    """Grava UM snapshot de patrimonio por dia (chave = `data`, formato YYYY-MM-DD).
    Reabrir no mesmo dia SOBRESCREVE o registro do dia, sem duplicar."""
    data = str((snap or {}).get("data") or "").strip()
    cur = get(conn, "equitySnapshots", user_id=user_id) or []
    if not data:
        return cur
    rec = {
        "data": data,
        "patrimonio": _snap_num((snap or {}).get("patrimonio")),
        "caixa": _snap_num((snap or {}).get("caixa")),
        "posicoesValor": _snap_num((snap or {}).get("posicoesValor")),
    }
    snaps = [s for s in cur if isinstance(s, dict) and s.get("data") != data]
    snaps.append(rec)
    snaps.sort(key=lambda s: s.get("data") or "")
    snaps = snaps[-400:]  # cap defensivo (~1 ano)
    db.kv_set(conn, "equitySnapshots", snaps, user_id=user_id)
    return snaps


def public_state(conn, user_id=None) -> dict:
    """Estado para o cliente: nunca expoe a apiKey; indica se ha chave salva."""
    cfg = dict(get(conn, "config", user_id=user_id))
    api_key = cfg.pop("apiKey", "")
    cfg["keyStored"] = bool(api_key)
    catalog = list(CATALOG) + [c for c in custom_list(conn, user_id=user_id) if isinstance(c, dict) and c.get("t") not in CATALOG_TICKERS]
    return {
        "catalog": catalog,
        "config": cfg,
        "skill": get(conn, "skill", user_id=user_id),
        "llmPrompts": get(conn, "llmPrompts", user_id=user_id),
        "watchlist": get(conn, "watchlist", user_id=user_id),
        "cash": get(conn, "cash", user_id=user_id),
        "positions": get(conn, "positions", user_id=user_id),
        "history": get(conn, "history", user_id=user_id),
        "agent": get(conn, "agent", user_id=user_id),
        "analyses": get(conn, "analyses", user_id=user_id),
        "profile": get(conn, "profile", user_id=user_id),
        "equitySnapshots": get(conn, "equitySnapshots", user_id=user_id) or [],
        "custom": custom_list(conn, user_id=user_id),
    }


# ----------------------- FASE 2: multiusuário (aditivo) ----------------------
# Seções persistidas por usuário (mesmas do KV legado + equitySnapshots).
USER_SECTIONS = SECTIONS + ["equitySnapshots"]


def export_sections(conn, user_id=None) -> dict:
    """Lê TODAS as seções de um escopo (cru, INCLUINDO config.apiKey). Usado para
    montar a semente do first-login (web: escopo legado -> escopo do usuário)."""
    return {k: get(conn, k, user_id=user_id) for k in USER_SECTIONS}


def seed_user_from(conn, user_id: str, seed: dict, only_if_empty: bool = True) -> bool:
    """Decisão B: no primeiro login com conta VAZIA, adota o dado local como
    semente. Retorna True se semeou. `seed` é um dict de seções (pode conter
    config.apiKey — BYOK preservado). Por padrão só semeia se o escopo do
    usuário ainda não tem `config` (conta nova)."""
    if only_if_empty and db.kv_get(conn, "config", None, user_id=user_id) is not None:
        ensure_defaults(conn, user_id=user_id)
        return False
    if isinstance(seed, dict):
        for k in USER_SECTIONS:
            if k in seed and seed[k] is not None:
                db.kv_set(conn, k, seed[k], user_id=user_id)
    ensure_defaults(conn, user_id=user_id)  # completa o que faltar
    return True


def delete_user_data(conn, user_id: str) -> int:
    """Item 5 (exclusão de conta): apaga TODAS as seções do usuário + a linha em
    users + sessões. Não toca no escopo global/legado. Retorna nº de seções
    removidas do kv."""
    n = db.kv_delete_user(conn, user_id)
    db.delete_user(conn, user_id)
    return n
