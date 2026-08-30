// Ganchos do modelo FREEMIUM — espelha server/app/plan.py. Os campos `null`
// abaixo são o fallback "sem limite conhecido localmente": o limite REAL
// chega sempre do endpoint em runtime (GET /api/watchlist/quota, Fase 13) e é
// injetado nestes hooks como objeto de plano ({ id: quota.planId, maxWatchlist:
// quota.limit }) — a fonte de verdade é sempre server/app/plan.py. O critério
// de sucesso 6 do ROADMAP da Fase 13 proíbe `10`/`30` hardcodado no front
// (contrato C-32/C-33, fonte única); não trocar `null` por número aqui.
//
// Pilar de custo: BYOK (o usuário usa a própria chave de LLM, na Config), o que
// permite um tier gratuito generoso. Quando a monetização entrar:
//  - um gate de assinatura (requiresSubscription) consulta o recibo VALIDADO da
//    loja (App Store / Google Play) — validação server-side, nunca só no cliente.

export const PLAN_FREE = { id: "free", maxWatchlist: null, maxAnalysesPerMonth: null };
export const PLAN_PRO = { id: "pro", maxWatchlist: null, maxAnalysesPerMonth: null };

// Plano vigente HOJE (tudo liberado). No futuro: resolver por usuário/recibo.
export const ACTIVE_PLAN = PLAN_FREE;

// HOOK: limite de tamanho da watchlist (item-a-item: `count` é quantos
// existem ANTES desta adição). Retorna { ok, reason }. CAP-07: fato+motivo,
// sem CTA de upgrade — mesmo tom de can_add_ticker em plan.py (o "Voce" sem
// acento no backend é convenção ASCII do .py; aqui o texto acentuado é o que
// o usuário lê).
export function canAddTicker(count, plan = ACTIVE_PLAN) {
  if (plan.maxWatchlist != null && count >= plan.maxWatchlist) {
    return { ok: false, reason: `Você atingiu o limite de ${plan.maxWatchlist} ativos do plano ${plan.id}.` };
  }
  return { ok: true };
}

// HOOK: variante EM MASSA de canAddTicker, espelho de can_grow_watchlist_to
// (plan.py, WR-02 do 12-REVIEW.md). Recebe o tamanho FINAL de uma troca em
// massa (PUT /api/watchlist substitui a lista inteira) e compara com `>`, NÃO
// `>=` — semântica diferente de canAddTicker, que compara "quantos existem
// ANTES de somar 1" com `>=`. Mesma reason do item acima.
export function canGrowWatchlistTo(finalSize, plan = ACTIVE_PLAN) {
  if (plan.maxWatchlist != null && finalSize > plan.maxWatchlist) {
    return { ok: false, reason: `Você atingiu o limite de ${plan.maxWatchlist} ativos do plano ${plan.id}.` };
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
