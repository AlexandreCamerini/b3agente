"""Operacoes de estado sobre o kv store. Funcoes recebem a conexao para
ficarem testaveis (o pytest cria a sua propria conexao em arquivo temporario).
"""
from datetime import datetime

from . import db, defaults
from .catalog import CATALOG, CATALOG_TICKERS, is_catalog_ticker

SECTIONS = ["config", "skill", "skillOperador", "llmPrompts", "watchlist", "cash", "positions", "history", "agent", "analyses", "profile", "custom", "optionPositions"]


def _eh_default_antigo(chave: str, texto: str) -> bool:
    """O texto salvo é um default de GERAÇÃO ANTERIOR (nunca editado)? A lista
    de hashes vive em defaults.LEGACY_PROMPT_SHA256 — ver o comentário lá."""
    import hashlib
    legado = defaults.LEGACY_PROMPT_SHA256.get(chave) or set()
    return hashlib.sha256(texto.encode()).hexdigest() in legado


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
    if isinstance(cfg, dict) and ("theme" not in cfg or "userName" not in cfg or "notif" not in cfg or "onboarded" not in cfg or "streak" not in cfg or "candlePeriod" not in cfg or "appMode" not in cfg):
        cfg.setdefault("theme", d["config"]["theme"])
        cfg.setdefault("userName", d["config"]["userName"])
        cfg.setdefault("notif", dict(d["config"]["notif"]))
        cfg.setdefault("onboarded", d["config"]["onboarded"])
        cfg.setdefault("streak", dict(d["config"]["streak"]))
        cfg.setdefault("candlePeriod", d["config"].get("candlePeriod", "1y"))
        # FASE 7 (F7.1): modo de trabalho + risco (backfill de docs antigos)
        cfg.setdefault("appMode", "estudo")
        cfg.setdefault("operadorTermo", None)
        cfg.setdefault("risco", dict(d["config"].get("risco") or {"pctPorTrade": 1.0, "capital": None}))
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
        elif lp[k] != v and _eh_default_antigo(k, lp[k]):
            # Migração (auditoria 2026-08-01): o texto salvo é um DEFAULT de
            # geração anterior — o usuário nunca editou; sobe para o default
            # novo (que compõe do canônico). Texto editado nunca entra aqui.
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
    # qa/49: parâmetros por-modelo (temperatura / teto de saída). null com a chave
    # presente = limpar → volta ao default do catálogo (llm._params_efetivos).
    if "maxTokens" in patch:
        mt = patch.get("maxTokens")
        if isinstance(mt, (int, float)) and not isinstance(mt, bool):
            cfg["maxTokens"] = max(256, min(200_000, int(mt)))
        elif mt is None:
            cfg.pop("maxTokens", None)
    if "temperature" in patch:
        tp = patch.get("temperature")
        if isinstance(tp, (int, float)) and not isinstance(tp, bool):
            cfg["temperature"] = max(0.0, min(2.0, round(float(tp), 2)))
        elif tp is None:
            cfg.pop("temperature", None)
    if isinstance(patch.get("initialBudget"), (int, float)):
        cfg["initialBudget"] = max(100.0, min(100_000_000.0, round(float(patch["initialBudget"]), 2)))
    if patch.get("theme") in ("dark", "light", "system"):
        cfg["theme"] = patch["theme"]
    if isinstance(patch.get("userName"), str):
        cfg["userName"] = patch["userName"].strip()[:40]
    if "onboarded" in patch:
        cfg["onboarded"] = bool(patch["onboarded"])
    if "tourSeen" in patch:  # qa/38 (Help): tour de 1º uso só aparece 1x
        cfg["tourSeen"] = bool(patch["tourSeen"])
    if patch.get("candlePeriod") in ("1mo", "3mo", "6mo", "1y", "2y"):
        cfg["candlePeriod"] = patch["candlePeriod"]
    if isinstance(patch.get("streak"), dict):
        st = patch["streak"]
        days = st.get("days"); last = st.get("last")
        cfg["streak"] = {"days": int(days) if isinstance(days, (int, float)) else 0, "last": str(last or "")}
    if isinstance(patch.get("notif"), dict):
        base = cfg.get("notif") if isinstance(cfg.get("notif"), dict) else {}
        for k in ("enabled", "stop", "alvo", "agente", "variacao", "gatilho"):
            if k in patch["notif"]:
                base[k] = bool(patch["notif"][k])
        cfg["notif"] = base
    # Camada de entendimento: UNIÃO, nunca substituição — dois aparelhos do
    # mesmo usuário não podem apagar o que o outro já marcou como visto.
    if isinstance(patch.get("conceitosVistos"), list):
        atual = cfg.get("conceitosVistos") if isinstance(cfg.get("conceitosVistos"), list) else []
        for cid in patch["conceitosVistos"]:
            cid = str(cid or "")[:40]
            if cid and cid not in atual:
                atual.append(cid)
        cfg["conceitosVistos"] = atual[:200]
    # FASE 7 (F7.1) — Modo Operador: modo de trabalho, termo aceito e risco.
    # Regra: ativar "operador" EXIGE o termo (aceitoEm+versao) já registrado ou
    # vindo no MESMO patch — nunca liga sem aceite explícito.
    if isinstance(patch.get("operadorTermo"), dict):
        t = patch["operadorTermo"]
        if t.get("aceitoEm") and t.get("versao"):
            cfg["operadorTermo"] = {"aceitoEm": str(t["aceitoEm"])[:40], "versao": str(t["versao"])[:10]}
    if patch.get("appMode") in ("estudo", "operador"):
        if patch["appMode"] == "operador" and not isinstance(cfg.get("operadorTermo"), dict):
            pass  # sem termo aceito, o modo NÃO muda (silencioso e seguro)
        else:
            cfg["appMode"] = patch["appMode"]
    if isinstance(patch.get("risco"), dict):
        base = cfg.get("risco") if isinstance(cfg.get("risco"), dict) else {}
        r = patch["risco"]
        if isinstance(r.get("pctPorTrade"), (int, float)):
            base["pctPorTrade"] = max(0.25, min(5.0, round(float(r["pctPorTrade"]), 2)))
        if r.get("capital") is None:
            base["capital"] = None
        elif isinstance(r.get("capital"), (int, float)):
            base["capital"] = max(100.0, min(100_000_000.0, round(float(r["capital"]), 2)))
        cfg["risco"] = base
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
    db.kv_set(conn, "optionPositions", [], user_id=user_id)
    db.kv_set(conn, "history", [], user_id=user_id)
    ag = get(conn, "agent", user_id=user_id)
    ag["events"] = [{"time": "Inicio", "kind": "info", "text": "Carteira reiniciada com o orcamento simulado de R$ " + ("%.2f" % budget) + "."}]
    db.kv_set(conn, "agent", ag, user_id=user_id)
    db.kv_set(conn, "analyses", {}, user_id=user_id)
    return public_state(conn, user_id=user_id)


# FASE 8B (R2): a instrução do agente tem UMA versão por modo — "skill"
# (Estudo, seção original intocada) e "skillOperador" (mesa). `modo` seleciona.
def _skill_section(modo=None) -> str:
    return "skillOperador" if modo == "operador" else "skill"


def set_skill(conn, name=None, text=None, user_id=None, modo=None) -> dict:
    sec = _skill_section(modo)
    sk = get(conn, sec, user_id=user_id)
    if isinstance(name, str):
        sk["name"] = name
    if isinstance(text, str):
        sk["text"] = text
    db.kv_set(conn, sec, sk, user_id=user_id)
    return sk


def restore_skill(conn, user_id=None, modo=None) -> dict:
    sec = _skill_section(modo)
    sk = get(conn, sec, user_id=user_id)
    sk["text"] = defaults.default_skill_text_operador() if modo == "operador" else defaults.default_skill_text()
    db.kv_set(conn, sec, sk, user_id=user_id)
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
    # FASE 3.2 — parâmetros do agente server-side (aditivo)
    if isinstance(patch.get("serverEnabled"), bool):
        ag["serverEnabled"] = patch["serverEnabled"]
    if patch.get("mode") in ("executar", "sinalizar"):
        ag["mode"] = patch["mode"]
    if isinstance(patch.get("rules"), dict):
        cur = ag.get("rules") if isinstance(ag.get("rules"), dict) else {}
        ag["rules"] = {**cur, **{k: bool(v) for k, v in patch["rules"].items() if k in ("stop", "alvo", "trailing")}}
    if isinstance(patch.get("trailingPct"), (int, float)):
        ag["trailingPct"] = max(1.0, min(20.0, float(patch["trailingPct"])))
    # F2 — trailing dinâmico. Os limites espelham os de `agent.agent_params`:
    # aqui é a fronteira de ENTRADA (nada inválido entra no kv), lá é a rede de
    # segurança de LEITURA (dado antigo ou escrito por outra via não quebra).
    if patch.get("trailingMode") in ("percentual", "atr", "estrutura"):
        ag["trailingMode"] = patch["trailingMode"]
    if isinstance(patch.get("trailingAtrMult"), (int, float)):
        ag["trailingAtrMult"] = max(1.0, min(4.0, float(patch["trailingAtrMult"])))
    if isinstance(patch.get("trailingLookback"), (int, float)):
        ag["trailingLookback"] = max(2, min(20, round(patch["trailingLookback"])))
    # F3 — alvo dinâmico: mesmo padrão de entrada validada do F2.
    if isinstance(patch.get("alvoDinamico"), bool):
        ag["alvoDinamico"] = patch["alvoDinamico"]
    if isinstance(patch.get("maxOpsDia"), (int, float)):
        ag["maxOpsDia"] = max(1, min(20, round(patch["maxOpsDia"])))
    if isinstance(patch.get("maxValorOp"), (int, float)):
        ag["maxValorOp"] = max(0.0, float(patch["maxValorOp"]))
    if isinstance(patch.get("lastSeenAt"), str):
        ag["lastSeenAt"] = patch["lastSeenAt"]
    db.kv_set(conn, "agent", ag, user_id=user_id)
    return ag


def set_position(conn, t: str, stop=None, alvo=None, has_stop=False, has_alvo=False,
                  alvo_extensoes=None, user_id=None) -> None:
    positions = get(conn, "positions", user_id=user_id)
    for p in positions:
        if p["t"] == t:
            if has_stop:
                p["stop"] = None if stop in (None, "") else float(stop)
            if has_alvo:
                p["alvo"] = None if alvo in (None, "") else float(alvo)
            # F3 — alvo dinâmico: contador de quantas vezes JÁ estendeu (o
            # freio de MAX_ALVO_EXTENSOES em agent.py lê daqui). None = não
            # mexe (chamadas antigas, ex. o trailing ajustando só o stop).
            if alvo_extensoes is not None:
                p["alvoExtensoes"] = int(alvo_extensoes)
    db.kv_set(conn, "positions", positions, user_id=user_id)


def _sanitize_trade_meta(meta) -> dict:
    """FASE 2 (2.4): contexto de ENTRADA registrado na compra — setup que a
    originou (do STU da F1), gatilho/invalidação e snapshotId. Só campos
    conhecidos, tipos validados; nada disso é recomendação (é telemetria
    didática para o card do Portfólio mostrar o status do gatilho)."""
    if not isinstance(meta, dict):
        return {}
    out = {}
    for k in ("setup", "lado", "veredito", "snapshotId"):
        v = meta.get(k)
        if isinstance(v, str) and v.strip():
            out[k] = v.strip()[:80]
    for k in ("gatilho", "invalidacao", "confluencia"):
        v = meta.get(k)
        if isinstance(v, (int, float)):
            out[k] = round(float(v), 2)
    return out


def buy(conn, t: str, qty: int, price: float, user_id=None, meta=None) -> None:
    qty = max(100, round(qty / 100) * 100)
    positions = get(conn, "positions", user_id=user_id)
    cash = get(conn, "cash", user_id=user_id)
    history = get(conn, "history", user_id=user_id)
    m = _sanitize_trade_meta(meta)
    existing = next((p for p in positions if p["t"] == t), None)
    if existing:
        total = existing["qty"] + qty
        existing["avg"] = round((existing["avg"] * existing["qty"] + price * qty) / total, 2)
        existing["qty"] = total
        if m:
            existing["setupEntrada"] = m  # última entrada define o contexto
    else:
        pos = {"t": t, "qty": qty, "avg": round(price, 2), "stop": None, "alvo": None,
               "abertaEm": now_str()}
        if m:
            pos["setupEntrada"] = m
        positions.append(pos)
    cash = round(cash - qty * price, 2)
    entry = {"date": now_str(), "type": "COMPRA", "t": t, "qty": qty, "price": round(price, 2), "pnl": None}
    if m.get("setup"):
        entry["setup"] = m["setup"]
    if m.get("snapshotId"):
        entry["snapshotId"] = m["snapshotId"]
    history.insert(0, entry)
    db.kv_set(conn, "positions", positions, user_id=user_id)
    db.kv_set(conn, "cash", cash, user_id=user_id)
    db.kv_set(conn, "history", history, user_id=user_id)


def sell(conn, t: str, price: float, user_id=None, qty=None):
    """Venda simulada TOTAL (comportamento original, qty=None) ou PARCIAL
    (FASE 2/2.4): qty é normalizado para lotes de 100; parcial mantém o preço
    médio (PnL realizado proporcional); >= posição vira total."""
    positions = get(conn, "positions", user_id=user_id)
    pos = next((p for p in positions if p["t"] == t), None)
    if not pos:
        return None
    cash = get(conn, "cash", user_id=user_id)
    history = get(conn, "history", user_id=user_id)
    sold = pos["qty"]
    if isinstance(qty, (int, float)) and qty > 0:
        sold = min(pos["qty"], max(100, round(qty / 100) * 100))
    pnl = round((price - pos["avg"]) * sold, 2)
    if sold >= pos["qty"]:
        positions = [p for p in positions if p["t"] != t]
    else:
        pos["qty"] = pos["qty"] - sold  # parcial: avg preservado
    cash = round(cash + sold * price, 2)
    history.insert(0, {"date": now_str(), "type": "VENDA", "t": t, "qty": sold, "price": round(price, 2), "pnl": pnl})
    db.kv_set(conn, "positions", positions, user_id=user_id)
    db.kv_set(conn, "cash", cash, user_id=user_id)
    db.kv_set(conn, "history", history, user_id=user_id)
    return pnl


# ---------- optionPositions (ADR-003: coleção própria, nunca mistura com `positions`) ----------
def buy_option(conn, contract: dict, qty: int, price: float, user_id=None, meta=None) -> None:
    """Compra simulada de UM contrato de opção. `contract` traz id (contractSymbol,
    chave primária e de cotação — ADR-003) / underlying / optionType / strike /
    expiration, vindos do provider. `price` é o PRÊMIO por ação, mesma unidade
    de `avg` — nunca o preço do ativo-objeto."""
    qty = max(100, round(qty / 100) * 100)
    opts = get(conn, "optionPositions", user_id=user_id)
    cash = get(conn, "cash", user_id=user_id)
    history = get(conn, "history", user_id=user_id)
    m = _sanitize_trade_meta(meta)
    cid = contract.get("id")
    existing = next((p for p in opts if p["id"] == cid), None)
    if existing:
        total = existing["qty"] + qty
        existing["avg"] = round((existing["avg"] * existing["qty"] + price * qty) / total, 2)
        existing["qty"] = total
        if m:
            existing["setupEntrada"] = m
    else:
        pos = {
            "id": cid, "underlying": contract.get("underlying"),
            "optionType": contract.get("optionType"), "strike": contract.get("strike"),
            "expiration": contract.get("expiration"),
            "qty": qty, "avg": round(price, 2), "stop": None, "alvo": None,
            "abertaEm": now_str(),
            "ivEntrada": contract.get("ivEntrada"), "deltaEntrada": contract.get("deltaEntrada"),
            "hv21Entrada": contract.get("hv21Entrada"),
        }
        if m:
            pos["setupEntrada"] = m
        opts.append(pos)
    cash = round(cash - qty * price, 2)
    entry = {"date": now_str(), "type": "COMPRA", "t": cid, "underlying": contract.get("underlying"),
             "kind": "opcao", "qty": qty, "price": round(price, 2), "pnl": None}
    if m.get("setup"):
        entry["setup"] = m["setup"]
    if m.get("snapshotId"):
        entry["snapshotId"] = m["snapshotId"]
    history.insert(0, entry)
    db.kv_set(conn, "optionPositions", opts, user_id=user_id)
    db.kv_set(conn, "cash", cash, user_id=user_id)
    db.kv_set(conn, "history", history, user_id=user_id)


def set_option_position(conn, contract_id: str, stop=None, alvo=None, has_stop=False, has_alvo=False, user_id=None) -> None:
    opts = get(conn, "optionPositions", user_id=user_id)
    for p in opts:
        if p["id"] == contract_id:
            if has_stop:
                p["stop"] = None if stop in (None, "") else float(stop)
            if has_alvo:
                p["alvo"] = None if alvo in (None, "") else float(alvo)
    db.kv_set(conn, "optionPositions", opts, user_id=user_id)


def sell_option(conn, contract_id: str, price: float, user_id=None, qty=None, motivo: str = "manual"):
    """Venda simulada TOTAL ou PARCIAL de um contrato. `motivo` (ADR-005):
    'manual' | 'stop' | 'alvo' | 'vencimento' — estruturado desde o início,
    ao contrário do texto descartável que `positions`/history de ação usa
    hoje. Vencimento passa por `close_option_vencida`, nunca chama esta
    função com preço negociado."""
    opts = get(conn, "optionPositions", user_id=user_id)
    pos = next((p for p in opts if p["id"] == contract_id), None)
    if not pos:
        return None
    cash = get(conn, "cash", user_id=user_id)
    history = get(conn, "history", user_id=user_id)
    sold = pos["qty"]
    if isinstance(qty, (int, float)) and qty > 0:
        sold = min(pos["qty"], max(100, round(qty / 100) * 100))
    pnl = round((price - pos["avg"]) * sold, 2)
    if sold >= pos["qty"]:
        opts = [p for p in opts if p["id"] != contract_id]
    else:
        pos["qty"] = pos["qty"] - sold  # parcial: avg preservado
    cash = round(cash + sold * price, 2)
    history.insert(0, {"date": now_str(), "type": "VENDA", "t": contract_id, "underlying": pos.get("underlying"),
                        "kind": "opcao", "qty": sold, "price": round(price, 2), "pnl": pnl, "motivo": motivo})
    db.kv_set(conn, "optionPositions", opts, user_id=user_id)
    db.kv_set(conn, "cash", cash, user_id=user_id)
    db.kv_set(conn, "history", history, user_id=user_id)
    return pnl


def close_option_vencida(conn, contract_id: str, valor_intrinseco: float, user_id=None):
    """ADR-005: liquidação por expiração. Preço = valor intrínseco na data do
    vencimento — pode ser ZERO (perda total do prêmio), sem que nenhum stop
    tenha sido rompido. Nunca chamada com preço negociado; motivo sempre
    'vencimento'."""
    return sell_option(conn, contract_id, max(0.0, float(valor_intrinseco)), user_id=user_id, motivo="vencimento")


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
        "skillOperador": get(conn, "skillOperador", user_id=user_id),  # FASE 8B (R2)
        "llmPrompts": get(conn, "llmPrompts", user_id=user_id),
        "watchlist": get(conn, "watchlist", user_id=user_id),
        "cash": get(conn, "cash", user_id=user_id),
        "positions": get(conn, "positions", user_id=user_id),
        "optionPositions": get(conn, "optionPositions", user_id=user_id),  # ADR-003
        "history": get(conn, "history", user_id=user_id),
        "agent": get(conn, "agent", user_id=user_id),
        "analyses": get(conn, "analyses", user_id=user_id),
        "profile": get(conn, "profile", user_id=user_id),
        "equitySnapshots": get(conn, "equitySnapshots", user_id=user_id) or [],
        "custom": custom_list(conn, user_id=user_id),
        "analysisLog": db.kv_get(conn, "analysisLog", {}, user_id=user_id) or {},   # FASE 2 (2.5)
        "agentLog": db.kv_get(conn, "agentLog", [], user_id=user_id) or [],         # FASE 3 (3.3a)
    }


# ----------------------- FASE 2: multiusuário (aditivo) ----------------------
# Seções persistidas por usuário (mesmas do KV legado + equitySnapshots).
USER_SECTIONS = SECTIONS + ["equitySnapshots", "analysisLog", "agentLog", "pushTokens"]


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


# ===========================================================================
# FASE 2 (2.5) + FASE 3 (3.3a) — logs didáticos.
# ===========================================================================
def push_analysis_log(conn, ticker: str, entry: dict, user_id=None) -> dict:
    """Histórico de análises POR ATIVO (telemetria didática: o que a IA disse
    antes vs. o que aconteceu). Cap de 20 entradas por ticker."""
    log = db.kv_get(conn, "analysisLog", {}, user_id=user_id) or {}
    t = (ticker or "").upper()
    cur = log.get(t) or []
    cur = (cur + [entry])[-20:]
    log[t] = cur
    db.kv_set(conn, "analysisLog", log, user_id=user_id)
    return log


def push_agent_log(conn, events: list, user_id=None) -> list:
    """Registro persistente das ações/sinais do agente (cap 200)."""
    log = db.kv_get(conn, "agentLog", [], user_id=user_id) or []
    log = (log + [e for e in (events or []) if isinstance(e, dict)])[-200:]
    db.kv_set(conn, "agentLog", log, user_id=user_id)
    return log
