// FASE 5 — Guardião: inserção de ativos na watchlist DIRETO do Radar.
//
// BUG que motivou este teste: A.addToWatchlist e ctx.openAvaliar usavam
// store.putWatchlist([...watchlist, t]). Nos DOIS stores o putWatchlist filtra
// a lista contra knownTickers() (catálogo de 20 + custom) — um ticker do Radar
// fora do catálogo (o universo tem ~74) era DESCARTADO em silêncio, enquanto a
// UI dizia "adicionado ✓". O caminho correto é store.addWatchlistTicker(t),
// que valida o ticker e o REGISTRA em `custom` (web: /api/watchlist/add; iOS:
// validação via servidor + custom local).
//
// Regras impostas aqui:
//  1) addToWatchlist NÃO usa putWatchlist; usa addWatchlistTicker.
//  2) openAvaliar NÃO usa putWatchlist; usa addWatchlistTicker.
//  3) o card do Radar continua ligado em ctx.A.addToWatchlist.
//  4) deviceStore.addWatchlistTicker registra o ticker validado em doc.custom
//     quando fora do catálogo (propriedade que faz o putWatchlist futuro mantê-lo).
// Roda sem build: `node web/tests/test_radar_watchlist.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const pers = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

// util: extrai o corpo de uma função "chave: async (args) => {...}" por chaves
function bodyOf(src, anchor) {
  const at = src.indexOf(anchor);
  if (at < 0) return null;
  const open = src.indexOf("{", at + anchor.length);
  if (open < 0) return null;
  let depth = 0;
  for (let i = open; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) return src.slice(open, i + 1); }
  }
  return null;
}

// ---- 1) addToWatchlist usa o caminho que aceita ativos fora do catálogo ----
const addBody = bodyOf(app, "addToWatchlist: async (t) =>");
ok("A.addToWatchlist localizado", !!addBody);
ok("addToWatchlist usa store.addWatchlistTicker", !!addBody && addBody.includes("store.addWatchlistTicker(t)"));
ok("addToWatchlist NÃO usa putWatchlist (descartava fora do catálogo)", !!addBody && !addBody.includes("putWatchlist"));
ok("addToWatchlist confere se o ticker realmente entrou", !!addBody && /watchlist\s*\|\|\s*\[\]\)\.includes\(t\)/.test(addBody));

// ---- 2) openAvaliar (ponte Descobrir → Avaliar) usa o mesmo caminho -------
const avBody = bodyOf(app, "openAvaliar: async (t) =>");
ok("ctx.openAvaliar localizado", !!avBody);
ok("openAvaliar usa store.addWatchlistTicker", !!avBody && avBody.includes("store.addWatchlistTicker(t)"));
ok("openAvaliar NÃO usa putWatchlist", !!avBody && !avBody.includes("putWatchlist"));

// ---- 3) o card do Radar segue ligado no A.addToWatchlist ------------------
ok("card do Radar chama ctx.A.addToWatchlist(r.ticker)", app.includes("ctx.A.addToWatchlist(r.ticker)"));

// ---- 4) deviceStore.addWatchlistTicker registra custom fora do catálogo ---
const devAdd = bodyOf(pers, "async addWatchlistTicker(ticker)");
ok("deviceStore.addWatchlistTicker localizado", !!devAdd);
ok("deviceStore registra ticker validado em doc.custom", !!devAdd && devAdd.includes("doc.custom = [...(doc.custom || [])"));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
