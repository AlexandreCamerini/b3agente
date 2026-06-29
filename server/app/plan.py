"""Ganchos para um futuro modelo FREEMIUM — ESTRUTURA, sem cobranca.

NADA aqui cobra ou bloqueia hoje: todas as funcoes liberam tudo. O objetivo e
deixar os PONTOS DE EXTENSAO explicitos e centralizados para quando a fase de
monetizacao chegar (assinatura via IAP na App Store / Google Play).

Estrategia de custo (pilar): BYOK — o usuario pluga a PROPRIA chave de LLM
(Config -> Modelo de IA). Assim o custo de inferencia nao recai sobre o app, o
que viabiliza um tier gratuito generoso.

Quando a monetizacao entrar, os limites abaixo passam a valer para o tier
gratuito (PLAN_FREE) e o tier pago (PLAN_PRO) os afrouxa. O gate de assinatura
(`requires_subscription`) deve consultar o recibo validado da loja (server-side
receipt validation) — NUNCA confiar so no cliente.
"""
from typing import Optional

# Limites por plano. None = ilimitado. Hoje TODOS ilimitados (sem cobranca).
PLAN_FREE = {
    "id": "free",
    "max_watchlist": None,        # futuro: ex. 10 ativos no gratuito
    "max_analyses_per_month": None,  # futuro: ex. 30 analises/mes no gratuito
    "byok_required": False,       # futuro: gratuito pode exigir BYOK
}
PLAN_PRO = {
    "id": "pro",
    "max_watchlist": None,
    "max_analyses_per_month": None,
    "byok_required": False,
}

# Plano vigente do app HOJE: tudo liberado. No futuro isso vira por-usuario,
# resolvido a partir do recibo de assinatura validado.
ACTIVE_PLAN = PLAN_FREE


def current_plan(user: Optional[dict] = None) -> dict:
    """HOJE: sempre o plano aberto. FUTURO: resolver pelo recibo do usuario."""
    return ACTIVE_PLAN


# ---- GANCHOS (hoje retornam sempre permitido) ----
def can_add_ticker(current_count: int, plan: Optional[dict] = None) -> tuple:
    """HOOK: limite de tamanho da watchlist no tier gratuito.
    Retorna (permitido: bool, motivo: str|None)."""
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_watchlist")
    if limit is not None and current_count >= limit:
        return (False, f"O plano {plan['id']} permite ate {limit} ativos. Faca upgrade para adicionar mais.")
    return (True, None)


def can_analyze(used_this_month: int, plan: Optional[dict] = None) -> tuple:
    """HOOK: limite de analises/mes no tier gratuito.
    Retorna (permitido: bool, motivo: str|None)."""
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_analyses_per_month")
    if limit is not None and used_this_month >= limit:
        return (False, f"Voce atingiu o limite de {limit} analises/mes do plano {plan['id']}.")
    return (True, None)


def requires_subscription(feature: str, user: Optional[dict] = None) -> bool:
    """HOOK: gate de assinatura por recurso premium (ex.: 'agente_autonomo',
    'analises_ilimitadas'). HOJE: nunca exige. FUTURO: validar recibo da loja."""
    return False
