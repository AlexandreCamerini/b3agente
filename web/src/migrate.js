// Backfill ESTRUTURAL de um doc carregado do aparelho (iPhone).
//
// Garante que os campos que o render ASSUME como objetos/arrays existam — mesmo
// num doc de versão antiga ou gravado pela metade. Sem isso, acessos como
// `data.watchlist.join(...)`, `data.positions.reduce(...)` ou `agent.events.map(...)`
// estouram em runtime e desmontam a árvore React => TELA BRANCA, sem recuperação.
//
// Puro e SEM imports nativos (não importa @capacitor/* nem catalog.js), para
// poder ser testado fora do WebView. `defaults` é o resultado de defaultState().
// Regra: nunca FABRICA dados do usuário — posições e histórico ausentes viram
// listas VAZIAS (jamais as posições-demo), para não injetar operações falsas
// num usuário real cujo doc se corrompeu.
export function backfillStructural(doc, defaults) {
  const d = doc && typeof doc === "object" ? doc : {};
  const def = defaults && typeof defaults === "object" ? defaults : {};

  if (!d.config || typeof d.config !== "object") d.config = { ...(def.config || {}) };
  if (!d.agent || typeof d.agent !== "object") d.agent = { ...(def.agent || {}) };
  if (!Array.isArray(d.agent.events)) {
    d.agent.events = def.agent && Array.isArray(def.agent.events) ? [...def.agent.events] : [];
  }
  if (!d.skill || typeof d.skill !== "object") d.skill = { ...(def.skill || {}) };

  if (!Array.isArray(d.watchlist)) d.watchlist = Array.isArray(def.watchlist) ? [...def.watchlist] : [];
  if (!Array.isArray(d.positions)) d.positions = []; // nunca fabrica posições
  if (!Array.isArray(d.history)) d.history = [];      // nunca fabrica histórico
  if (!Array.isArray(d.optionPositions)) d.optionPositions = []; // v2 (ADR-003): idem, nunca fabrica

  if (typeof d.cash !== "number" || !Number.isFinite(d.cash)) {
    d.cash = d.config && typeof d.config.initialBudget === "number" ? d.config.initialBudget : 10000;
  }
  return d;
}

// Assinatura EXATA da carteira fabricada que o app trazia de fábrica até
// F10-20260810-01 (espelho de `store._CARTEIRA_DEMO`).
const CARTEIRA_DEMO = [["PETR4", 300, 36.8], ["ITUB4", 200, 31.1], ["VALE3", 100, 63.4]];

/**
 * Remove a carteira de fábrica de um doc JÁ EXISTENTE no aparelho.
 *
 * Corrigir o estado padrão só resolveu instalações novas. No iOS o doc é
 * local-first: quem já tinha o app seguia com R$ 23.600 em ações NUNCA PAGAS,
 * +236% de retorno acumulado na abertura e três COMPRAS de junho no histórico
 * que ninguém fez.
 *
 * Não é reset. Só apaga o que casa com a assinatura de fábrica E tem o caixa
 * intacto no orçamento — numa carteira real, comprar debita o caixa, então
 * qualquer operação de verdade faz o doc passar incólume. Idempotente.
 */
export function limparCarteiraDemo(doc) {
  const d = doc && typeof doc === "object" ? doc : {};
  const pos = Array.isArray(d.positions) ? d.positions : [];
  if (pos.length !== CARTEIRA_DEMO.length) return d;
  const chave = (t, q, a) => `${t}|${q}|${a}`;
  const achado = new Set(pos.map((p) => chave(p && p.t, p && p.qty, p && p.avg)));
  if (CARTEIRA_DEMO.some(([t, q, a]) => !achado.has(chave(t, q, a)))) return d;
  const orcamento = d.config && d.config.initialBudget;
  if (typeof d.cash !== "number" || typeof orcamento !== "number") return d;
  if (Math.round(d.cash * 100) !== Math.round(orcamento * 100)) return d;  // já operou

  d.positions = [];
  const tickers = new Set(CARTEIRA_DEMO.map(([t]) => t));
  d.history = (Array.isArray(d.history) ? d.history : [])
    .filter((h) => !(h && h.type === "COMPRA" && tickers.has(h.t)));
  d.equitySnapshots = [];   // a série foi medida sobre o patrimônio inflado
  return d;
}
