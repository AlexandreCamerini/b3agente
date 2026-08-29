"""Ganchos do modelo FREEMIUM do Boris+ — plano comercial (ADR-010).

A partir da v1.3 (Fase 12), os dois limites do PLAN_FREE estao ATIVOS: 10
ativos na watchlist e 30 analises/mes. PLAN_PRO continua com ambos os
limites `None` (ilimitado) POR DECISAO comercial — nao existe loja/IAP neste
milestone, entao "pro" e um estado alcancavel so por atribuicao manual
(`users.plan`), nao por compra.

Estrategia de custo (pilar): BYOK — o usuario pluga a PROPRIA chave de LLM
(Config -> Modelo de IA). Assim o custo de inferencia nao recai sobre o app, o
que viabiliza um tier gratuito generoso.

O gate de assinatura (`requires_subscription`) deve consultar o recibo
validado da loja (server-side receipt validation) quando a loja/IAP existir —
NUNCA confiar so no cliente. Continua HOOK (sempre False) nesta fase.

Contrato de contagem (C-32, fixado na fase 3 — server/app/main.py::_gate_analise):
`server/app/metering.py` e o CONTADOR UNICO de uso de IA do app (cota DIARIA
por usuario + teto global, persistidos no kv). `can_analyze` aqui embaixo e o
gate de TIER comercial (MENSAL) e NUNCA mantem contagem propria — ele so LE o
limite do plano e decide permitido/negado. Com o ADR-010 tendo ligado
`max_analyses_per_month` (Fase 12), o valor de `used_this_month` passado a
`can_analyze` TEM de derivar do ledger de `metering` (C-33, fase 5) — nunca de
um segundo contador paralelo. Os dois gates (plano e metering) sao aplicados
num UNICO ponto de decisao por requisicao (`_gate_analise`), nunca em
paralelo.
"""
from typing import Optional

# Limites por plano. None = ilimitado.
PLAN_FREE = {
    "id": "free",
    "max_watchlist": 10,             # ATIVO desde a v1.3 (Fase 12, ADR-010)
    "max_analyses_per_month": 30,    # ATIVO desde a v1.3 (Fase 12, ADR-010)
    "byok_required": False,          # futuro: gratuito pode exigir BYOK
}
PLAN_PRO = {
    "id": "pro",
    "max_watchlist": None,
    "max_analyses_per_month": None,
    "byok_required": False,
}

# ACTIVE_PLAN e o fallback de quem nao tem `user` (escopo anonimo, D-06) —
# aponta para PLAN_FREE, entao anonimo passa a valer os mesmos dois limites
# ativados acima (comportamento intencional, Fase 12).
ACTIVE_PLAN = PLAN_FREE

PLANOS_POR_ID = {"free": PLAN_FREE, "pro": PLAN_PRO}
_ORDEM_PLANO = ["free", "pro"]


def current_plan(user: Optional[dict] = None) -> dict:
    """ADR-013: resolve pelo campo persistido `users.plan` (free|pro) em vez
    do ACTIVE_PLAN global fixo. A VALIDACAO do recibo de loja que decide esse
    campo continua pendente do ADR-010 — aqui so liga a leitura ao dado que
    ja existe em `db.users.plan` (default 'free', sem override manual nesta
    rodada). `user=None` (anonimo) cai no fallback ACTIVE_PLAN, igual antes."""
    if not user:
        return ACTIVE_PLAN
    return PLANOS_POR_ID.get(user.get("plan") or "free", PLAN_FREE)


def plan_at_least(plan_atual: dict, min_plan_id: str) -> bool:
    """ADR-013: usado por `require_plan()` (server/app/main.py) para gates
    futuros de plano — nenhuma rota usa isto ainda (ver ADR-013, item c)."""
    atual_id = (plan_atual or {}).get("id", "free")
    try:
        return _ORDEM_PLANO.index(atual_id) >= _ORDEM_PLANO.index(min_plan_id)
    except ValueError:
        return False


# ---- GATES DE PLANO (ATIVOS desde a v1.3 para o PLAN_FREE) ----
def can_add_ticker(current_count: int, plan: Optional[dict] = None) -> tuple:
    """HOOK: limite de tamanho da watchlist no tier gratuito.
    Retorna (permitido: bool, motivo: str|None)."""
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_watchlist")
    if limit is not None and current_count >= limit:
        return (False, f"Voce atingiu o limite de {limit} ativos do plano {plan['id']}.")
    return (True, None)


def can_grow_watchlist_to(final_size: int, plan: Optional[dict] = None) -> tuple:
    """HOOK: variante EM MASSA de can_add_ticker, para PUT /api/watchlist
    (WR-02, 12-REVIEW.md). `can_add_ticker(current_count, ...)` documenta
    `current_count` como "quantos itens existem ANTES desta adição" — semantica
    de item-a-item que nao existe numa troca em massa (o PUT substitui a lista
    inteira de uma vez). O call site antigo reusava esse hook passando
    `len(final) - 1` só para fazer a comparacao `>=` coincidir com "bloqueia
    sse o tamanho FINAL ultrapassa o limite"; estava aritmeticamente certo,
    mas por coincidencia com o operador atual, nao pelo contrato da funcao.
    Aqui a checagem é honesta: recebe o tamanho FINAL e compara direto.
    Retorna (permitido: bool, motivo: str|None)."""
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_watchlist")
    if limit is not None and final_size > limit:
        return (False, f"Voce atingiu o limite de {limit} ativos do plano {plan['id']}.")
    return (True, None)


def can_analyze(used_this_month: int, plan: Optional[dict] = None) -> tuple:
    """HOOK: limite de analises/mes no tier gratuito.
    Retorna (permitido: bool, motivo: str|None).

    Esta funcao NUNCA mantem contador proprio — `used_this_month` e sempre
    fornecido pelo chamador. O contador real de uso de IA e o de
    `metering.py` (cota diaria); quando o limite mensal for ativado, o valor
    aqui tem de vir do ledger de `metering` (C-33, fase 5)."""
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_analyses_per_month")
    if limit is not None and used_this_month >= limit:
        return (False, f"Voce atingiu o limite de {limit} analises/mes do plano {plan['id']}.")
    return (True, None)


def requires_subscription(feature: str, user: Optional[dict] = None) -> bool:
    """HOOK: gate de assinatura por recurso premium (ex.: 'agente_autonomo',
    'analises_ilimitadas'). HOJE: nunca exige. FUTURO: validar recibo da loja."""
    return False
