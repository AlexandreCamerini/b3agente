// Ganchos para o futuro modelo FREEMIUM — ESTRUTURA, sem cobrança hoje.
// Espelha server/app/plan.py. Hoje tudo é liberado (limites = null).
//
// Pilar de custo: BYOK (o usuário usa a própria chave de LLM, na Config), o que
// permite um tier gratuito generoso. Quando a monetização entrar:
//  - PLAN_FREE recebe limites (ex.: maxWatchlist, maxAnalysesPerMonth);
//  - um gate de assinatura (requiresSubscription) consulta o recibo VALIDADO da
//    loja (App Store / Google Play) — validação server-side, nunca só no cliente.

export const PLAN_FREE = { id: "free", maxWatchlist: null, maxAnalysesPerMonth: null };
export const PLAN_PRO = { id: "pro", maxWatchlist: null, maxAnalysesPerMonth: null };

// Plano vigente HOJE (tudo liberado). No futuro: resolver por usuário/recibo.
export const ACTIVE_PLAN = PLAN_FREE;

// HOOK: limite de tamanho da watchlist. Retorna { ok, reason }.
export function canAddTicker(count, plan = ACTIVE_PLAN) {
  if (plan.maxWatchlist != null && count >= plan.maxWatchlist) {
    return { ok: false, reason: `O plano ${plan.id} permite até ${plan.maxWatchlist} ativos. Faça upgrade para adicionar mais.` };
  }
  return { ok: true };
}

// HOOK: limite de análises por mês. Retorna { ok, reason }.
export function canAnalyze(usedThisMonth, plan = ACTIVE_PLAN) {
  if (plan.maxAnalysesPerMonth != null && usedThisMonth >= plan.maxAnalysesPerMonth) {
    return { ok: false, reason: `Você atingiu o limite de ${plan.maxAnalysesPerMonth} análises/mês do plano ${plan.id}.` };
  }
  return { ok: true };
}

// HOOK: gate de assinatura por recurso premium. HOJE: nunca exige.
export function requiresSubscription(/* feature */) {
  return false;
}
