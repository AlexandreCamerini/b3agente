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

  if (typeof d.cash !== "number" || !Number.isFinite(d.cash)) {
    d.cash = d.config && typeof d.config.initialBudget === "number" ? d.config.initialBudget : 10000;
  }
  return d;
}
