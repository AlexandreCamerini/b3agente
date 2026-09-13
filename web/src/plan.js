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

// 25-06: CÓDIGO da recusa por limite de watchlist — espelho de
// `main.COD_WATCHLIST` (server/app/main.py). Ele viaja em `detail.code` no 402
// das duas rotas de watchlist e `api.js` já o anexa ao Error como `err.code`.
// Existe para a tela não precisar RASPAR a frase para saber que classe de
// recusa é esta: erro técnico (fonte fora do ar) e recusa de plano são
// categorias diferentes (princípio 4 do CLAUDE.md) e não podem cair no mesmo
// aviso. Não é número de limite — o guardrail do topo deste arquivo continua
// valendo, nenhum `10`/`30` aqui.
export const COD_LIMITE_WATCHLIST = "watchlist_limite";

// HOOK: limite de tamanho da watchlist (item-a-item: `count` é quantos
// existem ANTES desta adição). Retorna { ok, reason }. CAP-07: fato+motivo,
// sem CTA de upgrade — mesmo tom de can_add_ticker em plan.py (o "Voce" sem
// acento no backend é convenção ASCII do .py; aqui o texto acentuado é o que
// o usuário lê).
// 25-06: a RECUSA carrega também `code`/`limite`/`usado`, os mesmos campos do
// `detail` do 402. `reason` fica byte a byte — ele é o texto de fallback e o
// que os guardiões de Fase 12/13 travam.
export function canAddTicker(count, plan = ACTIVE_PLAN) {
  if (plan.maxWatchlist != null && count >= plan.maxWatchlist) {
    return {
      ok: false,
      reason: `Você atingiu o limite de ${plan.maxWatchlist} ativos do plano ${plan.id}.`,
      code: COD_LIMITE_WATCHLIST,
      limite: plan.maxWatchlist,
      usado: count,
    };
  }
  return { ok: true };
}

// HOOK: variante EM MASSA de canAddTicker, espelho de can_grow_watchlist_to
// (plan.py, WR-02 do 12-REVIEW.md). Recebe o tamanho FINAL de uma troca em
// massa (PUT /api/watchlist substitui a lista inteira) e compara com `>`, NÃO
// `>=` — semântica diferente de canAddTicker, que compara "quantos existem
// ANTES de somar 1" com `>=`. Mesma reason do item acima.
// 25-06: sem `usado` aqui de propósito. `usado` significa "quantos a conta tem
// HOJE" (mesmo sentido do 402 do servidor) e esta função só recebe o tamanho
// PEDIDO — inventar `usado: finalSize` publicaria um número com outro
// significado no mesmo campo. Quem tem o valor de hoje é o chamador, e é ele
// que o passa a `erroDeLimiteWatchlist`.
export function canGrowWatchlistTo(finalSize, plan = ACTIVE_PLAN) {
  if (plan.maxWatchlist != null && finalSize > plan.maxWatchlist) {
    return {
      ok: false,
      reason: `Você atingiu o limite de ${plan.maxWatchlist} ativos do plano ${plan.id}.`,
      code: COD_LIMITE_WATCHLIST,
      limite: plan.maxWatchlist,
    };
  }
  return { ok: true };
}

// 25-06: transforma a recusa do gate LOCAL num Error com a MESMA forma do que
// `api.js` produz a partir do 402 do servidor (`err.code` + `err.detail`).
// Sem isto o banner compartilhado seria código morto no iOS: lá o gate de
// watchlist é client-side e autoritativo (o aparelho é a fonte da verdade,
// local-first — CR-01 da Fase 13), então a recusa nunca passa por um 402.
// `usado` é sempre o tamanho de HOJE, informado pelo chamador.
export function erroDeLimiteWatchlist(gate, usado) {
  const g = gate || {};
  const e = new Error(g.reason || "");
  e.code = COD_LIMITE_WATCHLIST;
  e.detail = {
    code: COD_LIMITE_WATCHLIST,
    message: e.message,
    limite: g.limite != null ? g.limite : null,
    usado: usado != null ? usado : (g.usado != null ? g.usado : null),
  };
  return e;
}

// 25-06: leitura ÚNICA da recusa por limite de watchlist, venha ela do 402 do
// servidor ou do gate local. Devolve `null` para qualquer outro erro — é o que
// impede o aviso de limite de aparecer sobre falha de rede, ticker inexistente
// ou provedor fora do ar. Números não-numéricos viram `null` (nunca 0, que
// afirmaria "você não tem nenhum").
export function limiteDeWatchlist(erro) {
  if (!erro || erro.code !== COD_LIMITE_WATCHLIST) return null;
  const d = erro.detail && typeof erro.detail === "object" ? erro.detail : {};
  const num = (v) => (typeof v === "number" && isFinite(v) ? v : null);
  return { limite: num(d.limite), usado: num(d.usado) };
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
