"""Operacoes de estado sobre o kv store. Funcoes recebem a conexao para
ficarem testaveis (o pytest cria a sua propria conexao em arquivo temporario).
"""
import threading
from datetime import datetime

from . import db, defaults
from .catalog import CATALOG, CATALOG_TICKERS, is_catalog_ticker

SECTIONS = ["config", "skill", "skillOperador", "llmPrompts", "watchlist", "cash", "positions", "history", "agent", "analyses", "profile", "custom", "optionPositions", "pendingOrders"]

# Fase 2 (MERC-02..04): trava ÚNICA de PROCESSO sobre o read-modify-write de
# `cash`/`positions`. Nasce aqui (não em pending_orders.py) porque o dono
# desses dois campos é este módulo, e o caminho de ordem IMEDIATA
# (/api/buy, /api/sell em main.py, plano 02-02) precisa adquirir EXATAMENTE
# esta mesma trava — pending_orders.ORDER_LOCK é um ALIAS deste objeto, não
# uma trava distinta. Motivo: `db._ThreadLocalConnection` dá uma conexão
# SQLite por thread do pool do FastAPI, então o SQLite sozinho não serializa
# duas requisições concorrentes lendo e escrevendo o mesmo `cash` — sem esta
# trava, duas escritas concorrentes reservariam/gastariam o mesmo caixa
# (lost update / double-spend, ameaça T-02-02). Vale para UM processo; o
# deploy do Railway é um serviço único (server/railway.json), então basta.
# NÃO criar uma segunda trava de processo para ordens em nenhum outro módulo
# do backend — esta é a ÚNICA.
ORDER_LOCK = threading.RLock()

# WR-01 (12-REVIEW.md): trava dedicada para o read-modify-write de
# `watchlist` (PUT /api/watchlist, POST /api/watchlist/add em main.py).
# Mesma classe de bug que ORDER_LOCK resolve para cash/positions — sem
# trava, dois PUT/ADD concorrentes leem o mesmo `atual`, e o último a
# escrever vence, perdendo a adição do outro. Deliberadamente NÃO é
# ORDER_LOCK: watchlist não é domínio de ordem de compra/venda, e o
# comentário acima proíbe uma segunda trava para ESSE domínio — não
# proíbe travas dedicadas para domínios diferentes.
WATCHLIST_LOCK = threading.RLock()

# Plano 04-02 (FIX-C02): teto de entradas `status == "rejeitada"` mantidas em
# `history` — a poda em `registrar_rejeicao` descarta só as rejeições MAIS
# ANTIGAS acima deste teto; execuções nunca são descartadas por ele (T-04-02).
CAP_REJEICOES = 100


def _eh_default_antigo(conn, chave: str, texto: str) -> bool:
    """O texto salvo é um default de GERAÇÃO ANTERIOR (nunca editado)? Duas
    fontes de hash conhecido, UNIÃO: `defaults.LEGACY_PROMPT_SHA256` (gerações
    de código, commits antigos) + `prompt_default_history` no banco (ADR-013:
    gerações publicadas por um admin em runtime). Texto que não bate com
    nenhuma das duas é edição de verdade do usuário — fica intocado."""
    import hashlib
    legado = set(defaults.LEGACY_PROMPT_SHA256.get(chave) or set())
    legado |= db.prompt_history_hashes(conn, chave)
    return hashlib.sha256(texto.encode()).hexdigest() in legado


def ensure_defaults(conn, user_id=None) -> None:
    d = defaults.default_state()
    # ADR-013 (Decisão 5a): o default de llmPrompts que semeia conta nova e
    # que a migração abaixo compara é o ATIVO (override do admin, se houver)
    # — nunca o código puro isolado do que o admin publicou.
    d["llmPrompts"] = defaults.default_llm_prompts_ativo(conn)
    for key in SECTIONS:
        # `user_id` faltava nas DUAS chamadas: o laço lia e escrevia sempre no
        # escopo legado, então semear a conta de um usuário novo não gravava
        # nada no escopo dele — funcionava só porque `store.get` cai no default
        # na leitura. Passou a importar quando o web deixou de herdar o escopo
        # anônimo: agora esta é a única semeadura de uma conta nova.
        if db.kv_get(conn, key, None, user_id=user_id) is None:
            db.kv_set(conn, key, d[key], user_id=user_id)
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
    if isinstance(cfg, dict) and ("theme" not in cfg or "userName" not in cfg or "notif" not in cfg or "onboarded" not in cfg or "streak" not in cfg or "candlePeriod" not in cfg or "appMode" not in cfg or "vozAtiva" not in cfg):
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
        # Tela de configuração do Boris (backfill de docs antigos)
        cfg.setdefault("vozAtiva", d["config"]["vozAtiva"])
        cfg.setdefault("vozId", d["config"]["vozId"])
        cfg.setdefault("fabVisivel", d["config"]["fabVisivel"])
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
        elif lp[k] != v and _eh_default_antigo(conn, k, lp[k]):
            # Migração (auditoria 2026-08-01): o texto salvo é um DEFAULT de
            # geração anterior — o usuário nunca editou; sobe para o default
            # novo (que compõe do canônico). Texto editado nunca entra aqui.
            lp[k] = v
            changed = True
    if changed:
        db.kv_set(conn, "llmPrompts", lp, user_id=user_id)
    migrar_carteira_demo(conn, user_id=user_id)


# Assinatura EXATA da carteira fabricada que o app trazia de fábrica até
# F10-20260809-05 (defaults.py e catalog.js). Fica aqui, e não em defaults,
# porque é história: o default novo já nasce vazio.
_CARTEIRA_DEMO = [("PETR4", 300, 36.8), ("ITUB4", 200, 31.1), ("VALE3", 100, 63.4)]


def _e_a_carteira_demo(positions, cash, cfg) -> bool:
    """As posições são a carteira de fábrica, e NUNCA foram pagas?

    Os dois lados importam. A assinatura sozinha não basta (alguém poderia ter
    comprado esses papéis nessas quantidades); o caixa INTACTO no orçamento é o
    que prova que ninguém pagou por elas — numa carteira real, comprar debita.
    """
    if not isinstance(positions, list) or len(positions) != len(_CARTEIRA_DEMO):
        return False
    achado = {(p.get("t"), p.get("qty"), p.get("avg")) for p in positions if isinstance(p, dict)}
    if achado != set(_CARTEIRA_DEMO):
        return False
    orcamento = (cfg or {}).get("initialBudget")
    return isinstance(cash, (int, float)) and isinstance(orcamento, (int, float)) \
        and round(float(cash), 2) == round(float(orcamento), 2)


def migrar_carteira_demo(conn, user_id=None) -> bool:
    """Remove a carteira de fábrica de estados JÁ EXISTENTES.

    Corrigir `defaults.py` só resolveu instalações novas: quem já tinha o app
    seguia com R$ 23.600 em ações não pagas, retorno acumulado de +236% na
    abertura e três COMPRAS de junho no histórico que ninguém fez.

    Não é um reset: só apaga o que casa com a assinatura de fábrica E tem o
    caixa intacto. Qualquer operação real (uma compra, uma venda, um ajuste de
    quantidade) quebra a assinatura ou move o caixa, e o estado passa incólume.
    Idempotente — rodar de novo não faz nada.
    """
    positions = db.kv_get(conn, "positions", None, user_id=user_id)
    cash = db.kv_get(conn, "cash", None, user_id=user_id)
    cfg = db.kv_get(conn, "config", None, user_id=user_id)
    if not _e_a_carteira_demo(positions, cash, cfg):
        return False
    db.kv_set(conn, "positions", [], user_id=user_id)
    # O histórico some junto: eram os registros das MESMAS compras fabricadas.
    hist = db.kv_get(conn, "history", None, user_id=user_id) or []
    tickers = {t for t, _q, _a in _CARTEIRA_DEMO}
    sobra = [h for h in hist if not (isinstance(h, dict) and h.get("type") == "COMPRA"
                                     and h.get("t") in tickers)]
    db.kv_set(conn, "history", sobra, user_id=user_id)
    # A série de patrimônio foi medida sobre esse patrimônio inflado.
    db.kv_set(conn, "equitySnapshots", [], user_id=user_id)
    print(f"[migracao] carteira de fábrica removida (user={user_id or 'legado'})")
    return True


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
        # O CAIXA ACOMPANHA — enquanto a simulação não começou. Escolher o
        # orçamento (no onboarding ou na Config) só mexia em `config`, e o
        # "disponível" continuava no valor antigo: a pessoa punha R$ 50.000 e
        # via R$ 10.000 para operar. Com posição ou histórico já existentes o
        # caixa NÃO é mexido — ali ele é resultado das operações, e sobrescrever
        # seria inventar ou destruir dinheiro no meio da simulação.
        if not get(conn, "positions", user_id=user_id) and not get(conn, "history", user_id=user_id):
            db.kv_set(conn, "cash", cfg["initialBudget"], user_id=user_id)
    if patch.get("theme") in ("dark", "light", "system"):
        cfg["theme"] = patch["theme"]
    if isinstance(patch.get("userName"), str):
        cfg["userName"] = patch["userName"].strip()[:40]
    if "onboarded" in patch:
        cfg["onboarded"] = bool(patch["onboarded"])
    if "tourSeen" in patch:  # qa/38 (Help): tour de 1º uso só aparece 1x
        cfg["tourSeen"] = bool(patch["tourSeen"])
    if "borisIntroVisto" in patch:  # F6: apresentação do Boris só aparece 1x
        cfg["borisIntroVisto"] = bool(patch["borisIntroVisto"])
    if patch.get("candlePeriod") in ("1mo", "3mo", "6mo", "1y", "2y"):
        cfg["candlePeriod"] = patch["candlePeriod"]
    if isinstance(patch.get("streak"), dict):
        st = patch["streak"]
        days = st.get("days"); last = st.get("last")
        cfg["streak"] = {"days": int(days) if isinstance(days, (int, float)) else 0, "last": str(last or "")}
    if isinstance(patch.get("notif"), dict):
        base = cfg.get("notif") if isinstance(cfg.get("notif"), dict) else {}
        # 260824-kc2: as três classes de push do SERVIDOR entram na mesma
        # allowlist — chave ausente daqui é descartada em SILÊNCIO pelo
        # PUT /api/config (o modo de falha que já queimou o `agent.*`). A
        # paridade é com `deviceStore.putConfig` (persistence.js), na MESMA
        # ordem: as duas listas são uma coisa só.
        for k in ("enabled", "stop", "alvo", "agente", "variacao", "gatilho",
                  "radar", "execucao", "protecao"):
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
    # Toque longo: contadores MONOTÔNICOS (max, nunca substituição) — dois
    # aparelhos do mesmo usuário não rebobinam a dica nem a medição um do outro.
    if isinstance(patch.get("gestoUso"), dict):
        base = cfg.get("gestoUso") if isinstance(cfg.get("gestoUso"), dict) else {}
        for k in ("aberturas", "gesto", "botao"):
            v = patch["gestoUso"].get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                base[k] = max(int(base.get(k) or 0), min(int(v), 100_000))
        cfg["gestoUso"] = base
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
            # Fase A, D1 — migração silenciosa: quem SAI do Modo Operador com
            # `agent.mode="executar"` salvo não pode ficar em Modo Estudo com
            # uma ordem automática ainda armada até o próximo set_agent. A
            # trava de LEITURA (agent.agent_params) já cobre o ciclo, mas o
            # dado salvo ficaria inconsistente com o que a UI e o Diário
            # mostram. Só mexe ao SAIR de "operador" — entrar nele não
            # precisa (set_agent já trava a escrita de "executar" fora dele).
            if cfg["appMode"] != "operador":
                ag = get(conn, "agent", user_id=user_id)
                mudou = False
                if ag.get("mode") == "executar":
                    ag["mode"] = "sinalizar"
                    mudou = True
                # Fase B — mesma migração: entrada automática armada não pode
                # sobreviver à saída do Operador (a trava de LEITURA em
                # `_avaliar_entradas` já cobre o ciclo, mas o dado salvo
                # ficaria inconsistente com a UI/Diário até o próximo set_agent).
                if ag.get("entradaAuto"):
                    ag["entradaAuto"] = False
                    mudou = True
                if mudou:
                    db.kv_set(conn, "agent", ag, user_id=user_id)
    # Tela de configuração do Boris: voz, presença do FAB. O aviso espontâneo
    # (5º controle) não tem campo próprio — usa o `notif.gatilho` já tratado
    # acima, então não precisa de handler aqui.
    if "vozAtiva" in patch:
        cfg["vozAtiva"] = bool(patch["vozAtiva"])
    if isinstance(patch.get("vozId"), str):
        cfg["vozId"] = patch["vozId"][:200]
    if "fabVisivel" in patch:
        cfg["fabVisivel"] = bool(patch["fabVisivel"])
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
    # A SÉRIE DE PATRIMÔNIO TAMBÉM ZERA. Ela sobrevivia ao "Recomeçar do zero":
    # a curva exibida e o drawdown passavam a misturar os pontos da simulação
    # anterior com os da nova, com bases diferentes — número sem significado.
    db.kv_set(conn, "equitySnapshots", [], user_id=user_id)
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


def normalize_watchlist(conn, tickers: list, user_id=None) -> list:
    """Fonte unica do tamanho FINAL efetivo da watchlist (Fase 12, CAP-01).

    Extraida de set_watchlist: filtra a lista crua contra known_tickers,
    deduplica e reordena (catalogo+custom primeiro, escolhidos fora da
    ordenacao depois) SEM gravar nada. O gate de plano do PUT /api/watchlist
    precisa saber esse tamanho ANTES de escrever — duplicar esta regra no
    main.py criaria uma segunda fonte de verdade (o mesmo tipo de contador
    paralelo que o contrato C-32/C-33 proibe).
    """
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
    return valid


def set_watchlist(conn, tickers: list, user_id=None) -> list:
    valid = normalize_watchlist(conn, tickers, user_id=user_id)
    db.kv_set(conn, "watchlist", valid, user_id=user_id)
    return valid


def set_agent(conn, patch: dict, user_id=None) -> dict:
    ag = get(conn, "agent", user_id=user_id)
    # Trava estrutural (Fase A, D1): Modo Estudo nunca executa ordem
    # automática — vale na ESCRITA, não só na leitura (agent.agent_params).
    # Sem isto, um patch {"mode": "executar"} gravaria o valor mesmo fora do
    # Modo Operador; a leitura protegeria o ciclo, mas o dado salvo ficaria
    # inconsistente com o que a UI mostra e com qualquer outro lugar que leia
    # `agent.mode` direto do kv.
    cfg = get(conn, "config", user_id=user_id)
    operador = isinstance(cfg, dict) and cfg.get("appMode") == "operador"
    if isinstance(patch.get("autonomous"), bool):
        # Campo legado (fallback de `mode` em agent_params): mesma trava —
        # "autonomous=True" fora do Operador equivale a "executar" fora dele.
        ag["autonomous"] = patch["autonomous"] and operador
    if isinstance(patch.get("allocPct"), (int, float)):
        ag["allocPct"] = max(1, min(20, round(patch["allocPct"])))
    if isinstance(patch.get("entradaAuto"), bool):
        # Fase B, mesma trava de `mode="executar"` acima: entrada automática
        # também exige Modo Operador — reusa a MESMA leitura de `cfg`/`operador`
        # já calculada nesta função, sem repetir a query.
        ag["entradaAuto"] = patch["entradaAuto"] if operador else False
    if isinstance(patch.get("intervalMin"), (int, float)):
        ag["intervalMin"] = max(1, min(240, round(patch["intervalMin"])))
    # FASE 3.2 — parâmetros do agente server-side (aditivo)
    if isinstance(patch.get("serverEnabled"), bool):
        ag["serverEnabled"] = patch["serverEnabled"]
    if patch.get("mode") in ("executar", "sinalizar"):
        novo_modo = patch["mode"]
        if novo_modo == "executar" and not operador:
            novo_modo = "sinalizar"  # trava: só o Modo Operador pode gravar "executar"
        ag["mode"] = novo_modo
        # Acoplamento mode="executar" ↔ serverEnabled (Fase A): "quero
        # executar" sem "rodar em background" é exatamente o estado ambíguo
        # descrito em agent.py:486-500 (proteção só avaliada com o app
        # aberto) — a hipótese principal do stop batido com a posição
        # mantida. Só liga quando o patch NÃO trouxe serverEnabled junto (não
        # sobrescreve uma escolha explícita do mesmo request) e o valor salvo
        # ainda não é True (idempotente).
        if novo_modo == "executar" and "serverEnabled" not in patch and ag.get("serverEnabled") is not True:
            ag["serverEnabled"] = True
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


def scopes_com_history(conn) -> list:
    """ADR-012 (Fase 3): todo user_id (+ escopo legado, `None`) com `history`
    gravado — mesmo padrão de `analysis_outcomes._scopes_com_outcomes`,
    reaproveitado por `automacao.py` pra agregar ordens cross-usuário."""
    rows = conn.execute(
        "SELECT key FROM kv WHERE key LIKE 'u:%:history' OR key = 'history'"
    ).fetchall()
    out = []
    for (key,) in rows:
        if key == "history":
            out.append(None)
        else:
            out.append(key[len("u:"):-len(":history")])
    return out


def scopes_com_pendentes(conn) -> list:
    """Fase 2 (MERC-02..04): todo user_id (+ escopo legado, `None`) com
    `pendingOrders` gravado — mesma estrutura de `scopes_com_history`. É isto
    que o scheduler (plano 02-03) varre para executar ordens pendentes na
    abertura, e NÃO `agent.list_server_users`: uma ordem pendente é do
    usuário mesmo que ele nunca tenha ligado o Modo Operador."""
    rows = conn.execute(
        "SELECT key FROM kv WHERE key LIKE 'u:%:pendingOrders' OR key = 'pendingOrders'"
    ).fetchall()
    out = []
    for (key,) in rows:
        if key == "pendingOrders":
            out.append(None)
        else:
            out.append(key[len("u:"):-len(":pendingOrders")])
    return out


def caixa_reservado(conn, user_id=None) -> float:
    """Soma dos `caixaReservado` das ordens pendentes de COMPRA — valor
    DERIVADO, calculado na leitura a partir da lista de `pendingOrders`, não
    é um segundo saldo persistido nem um segundo livro-caixa. É por isso que
    NÃO viola D-05: o que D-05 proibiu foi criar um campo de saldo paralelo a
    `cash` que precisasse ser sincronizado à mão (risco de dois ledgers
    divergirem); aqui `cash` continua sendo a única fonte de verdade do
    dinheiro livre, o débito segue o caminho de sempre (`buy`/`sell`), e
    `caixaReservado` é só a soma dos reservados, exposta porque MERC-03 exige
    mostrar esse valor na tela. Coincidência de nome com o termo citado em
    D-05 é isso: coincidência de nome.

    Implementado AQUI (não em `pending_orders.py`) para `public_state` poder
    chamá-lo sem import circular — `pending_orders` importa `store`, nunca o
    inverso. `pending_orders.caixa_reservado` delega para este (fonte
    ÚNICA da aritmética, sem duplicação)."""
    pendentes = get(conn, "pendingOrders", user_id=user_id) or []
    total = sum((o.get("caixaReservado") or 0) for o in pendentes if isinstance(o, dict) and o.get("tipo") == "COMPRA")
    return round(total, 2)


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


def buy(conn, t: str, qty: int, price: float, user_id=None, meta=None, origem: str = "manual") -> None:
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
    # ADR-012 (Fase 3): `origem` (manual|automatico) — quem disparou a ordem,
    # não confundir com `motivo` de sell_option (POR QUE vendeu). Sempre
    # gravado (nunca condicional como setup/snapshotId) — histórico ANTERIOR
    # a esta mudança fica sem a chave (None no .get), não é reescrito.
    entry = {"date": now_str(), "type": "COMPRA", "t": t, "qty": qty, "price": round(price, 2), "pnl": None,
             "status": "executada", "origem": origem}
    if m.get("setup"):
        entry["setup"] = m["setup"]
    if m.get("snapshotId"):
        entry["snapshotId"] = m["snapshotId"]
    history.insert(0, entry)
    db.kv_set(conn, "positions", positions, user_id=user_id)
    db.kv_set(conn, "cash", cash, user_id=user_id)
    db.kv_set(conn, "history", history, user_id=user_id)


def sell(conn, t: str, price: float, user_id=None, qty=None, motivo: str = "manual", origem: str = "manual"):
    """Venda simulada TOTAL (comportamento original, qty=None) ou PARCIAL
    (FASE 2/2.4): qty é normalizado para lotes de 100; parcial mantém o preço
    médio (PnL realizado proporcional); >= posição vira total.

    `motivo` (ADR-015/ADR15-04): POR QUE vendeu — 'manual'|'stop'|'alvo'|
    'vencimento' — mesmo contrato de `sell_option` (ADR-005), agora com
    paridade também do lado de AÇÃO. `origem` (ADR-012, Fase 3): QUEM
    disparou (manual|automatico|sistema), eixo independente de `motivo`. Um
    stop batido pelo Operador automático é motivo='stop', origem='automatico';
    o mesmo stop fechado à mão pelo usuário é motivo='stop', origem='manual'.

    Histórico gravado ANTES desta mudança não tem a chave `motivo` — fica
    `None` via `.get`, não é reescrito (mesmo padrão adotado quando `origem`
    entrou, ADR-012)."""
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
    history.insert(0, {"date": now_str(), "type": "VENDA", "t": t, "qty": sold, "price": round(price, 2), "pnl": pnl,
                        "status": "executada", "motivo": motivo, "origem": origem})
    db.kv_set(conn, "positions", positions, user_id=user_id)
    db.kv_set(conn, "cash", cash, user_id=user_id)
    db.kv_set(conn, "history", history, user_id=user_id)
    return pnl


def registrar_rejeicao(conn, tipo: str, t: str, qty, price, motivo: str, user_id=None, origem: str = "manual") -> dict:
    """FIX-C02 (Plano 04-02): grava o rastro de uma tentativa de ordem que NÃO
    executou (caixa insuficiente, dado indisponível, etc.) — precedente exato
    é `ultimoErro`/`ultimaTentativaEm` de `pending_orders.py` (Fase 2): uma
    tentativa que falhou não pode sumir em silêncio, o caso mais educativo
    (estourou risco) precisa ficar revisável no histórico (CLAUDE.md, "Modelo
    de simulação").

    NÃO toca `cash`/`positions`/`pendingOrders`/`caixaReservado` — rejeição
    não move dinheiro nenhum. `price=None` é aceito e preservado como `None`
    (nunca 0.0 — convenção da casa, mesma razão de
    `test_m3_format_pede_null_nunca_zero`, aqui por CLAUDE.md item 4)."""
    if tipo not in ("COMPRA", "VENDA"):
        raise ValueError(f"tipo de ordem invalido: {tipo!r}")
    motivo_norm = str(motivo).strip()[:200]
    entry = {
        "date": now_str(), "type": tipo, "t": t, "qty": qty,
        "price": (round(price, 2) if isinstance(price, (int, float)) else None),
        "pnl": None, "status": "rejeitada", "motivo": motivo_norm, "origem": origem,
    }
    history = get(conn, "history", user_id=user_id)
    history.insert(0, entry)
    # Poda: mantém no máximo CAP_REJEICOES entradas rejeitadas, descartando as
    # mais antigas primeiro. Entradas executadas (ou legadas sem `status`)
    # nunca são tocadas por esta varredura (T-04-02).
    rejeitadas_idx = [i for i, h in enumerate(history) if isinstance(h, dict) and h.get("status") == "rejeitada"]
    if len(rejeitadas_idx) > CAP_REJEICOES:
        # rejeitadas_idx está em ordem de mais recente (índice menor) para
        # mais antiga (índice maior), pois `history` é populado com insert(0).
        descartar = set(rejeitadas_idx[CAP_REJEICOES:])
        history = [h for i, h in enumerate(history) if i not in descartar]
    db.kv_set(conn, "history", history, user_id=user_id)
    return entry


# ---------- optionPositions (ADR-003: coleção própria, nunca mistura com `positions`) ----------
def buy_option(conn, contract: dict, qty: int, price: float, user_id=None, meta=None, origem: str = "manual") -> None:
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
             "kind": "opcao", "qty": qty, "price": round(price, 2), "pnl": None, "origem": origem}
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


def sell_option(conn, contract_id: str, price: float, user_id=None, qty=None, motivo: str = "manual",
                 origem: str = "manual"):
    """Venda simulada TOTAL ou PARCIAL de um contrato. `motivo` (ADR-005):
    'manual' | 'stop' | 'alvo' | 'vencimento' — estruturado desde o início,
    ao contrário do texto descartável que `positions`/history de ação usa
    hoje. Vencimento passa por `close_option_vencida`, nunca chama esta
    função com preço negociado.

    `origem` (ADR-012, Fase 3): manual|automatico — QUEM disparou a venda,
    independente de `motivo` (POR QUE). Um stop batido pelo Operador
    automático é motivo='stop', origem='automatico'; o mesmo stop fechado
    manualmente pelo usuário é motivo='stop', origem='manual'."""
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
                        "kind": "opcao", "qty": sold, "price": round(price, 2), "pnl": pnl, "motivo": motivo,
                        "origem": origem})
    db.kv_set(conn, "optionPositions", opts, user_id=user_id)
    db.kv_set(conn, "cash", cash, user_id=user_id)
    db.kv_set(conn, "history", history, user_id=user_id)
    return pnl


def close_option_vencida(conn, contract_id: str, valor_intrinseco: float, user_id=None):
    """ADR-005: liquidação por expiração. Preço = valor intrínseco na data do
    vencimento — pode ser ZERO (perda total do prêmio), sem que nenhum stop
    tenha sido rompido. Nunca chamada com preço negociado; motivo sempre
    'vencimento'.

    `origem='sistema'` (ADR-012, Fase 3): NÃO é 'automatico' — expiração é
    liquidação mecânica obrigatória, roda IGUAL com o Operador ligado ou
    desligado, não é uma decisão do agente. Misturar com 'automatico' inflaria
    ou distorceria a métrica de eficiência da automação com eventos que o
    Operador não escolheu."""
    return sell_option(conn, contract_id, max(0.0, float(valor_intrinseco)), user_id=user_id,
                       motivo="vencimento", origem="sistema")


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
    # BASE DA SÉRIE: o capital com que ESTA simulação começou, carimbado no
    # snapshot. Sem isto, o "retorno acumulado" era medido contra
    # `config.initialBudget` — um campo que a pessoa edita a qualquer momento,
    # sem que caixa ou posições mudem. Digitar 380 num patrimônio de 37.908
    # produzia +9876% sem nenhuma operação ter acontecido. O carimbo é gravado
    # UMA vez (o 1º snapshot da série manda) e não é reescrito depois.
    cfg = get(conn, "config", user_id=user_id) or {}
    base_atual = cfg.get("initialBudget")
    anteriores = [s for s in cur if isinstance(s, dict) and isinstance(s.get("base"), (int, float))]
    base = anteriores[0]["base"] if anteriores else _snap_num(base_atual)
    rec = {
        "data": data,
        "patrimonio": _snap_num((snap or {}).get("patrimonio")),
        "caixa": _snap_num((snap or {}).get("caixa")),
        "posicoesValor": _snap_num((snap or {}).get("posicoesValor")),
        "base": base,
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
        "pendingOrders": get(conn, "pendingOrders", user_id=user_id),      # Fase 2 (MERC-02..04)
        "caixaReservado": caixa_reservado(conn, user_id=user_id),         # Fase 2: DERIVADO, ver caixa_reservado()
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
