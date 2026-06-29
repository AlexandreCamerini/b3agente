// C1 — trava o bug de TELA BRANCA: um doc de aparelho antigo/parcial sem
// watchlist/positions/history/agent.events fazia o render estourar
// (data.watchlist.join, data.positions.reduce, agent.events.map).
// backfillStructural() precisa devolver sempre a forma segura, SEM fabricar
// operações do usuário e SEM sobrescrever o que já existe.
import { backfillStructural } from "../src/migrate.js";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const defaults = {
  config: { initialBudget: 5000, theme: "dark" },
  agent: { events: [{ time: "Inicio", kind: "info", text: "x" }] },
  skill: { name: "s", text: "t" },
  watchlist: ["PETR4", "VALE3"],
};

// 1) doc null -> estrutura completa, sem quebrar
{
  const d = backfillStructural(null, defaults);
  ok("null -> arrays presentes", Array.isArray(d.watchlist) && Array.isArray(d.positions) && Array.isArray(d.history));
  ok("null -> agent.events array", Array.isArray(d.agent.events));
}

// 2) doc PARCIAL (o vetor real da tela branca)
{
  const d = backfillStructural({ config: {} }, defaults);
  ok("parcial -> watchlist herda default", JSON.stringify(d.watchlist) === JSON.stringify(["PETR4", "VALE3"]));
  ok("parcial -> positions VAZIO (nao fabrica)", d.positions.length === 0);
  ok("parcial -> history VAZIO (nao fabrica)", d.history.length === 0);
  let threw = false;
  try { d.watchlist.join(","); d.positions.reduce((s) => s, 0); d.agent.events.map((e) => e); } catch { threw = true; }
  ok("derefs de render nao quebram", !threw);
}

// 3) NAO sobrescreve valores existentes do usuario
{
  const d = backfillStructural({ watchlist: ["BBAS3"], positions: [{ t: "BBAS3", qty: 100 }], history: [{ t: "BBAS3" }], cash: 999 }, defaults);
  ok("preserva watchlist existente", d.watchlist.length === 1 && d.watchlist[0] === "BBAS3");
  ok("preserva positions existentes", d.positions.length === 1);
  ok("preserva history existente", d.history.length === 1);
  ok("preserva cash existente", d.cash === 999);
}

// 4) cash ausente herda initialBudget; sem ele, cai para 10000
{
  const a = backfillStructural({ config: { initialBudget: 7777 } }, defaults);
  ok("cash herda initialBudget do proprio doc", a.cash === 7777);
  const b = backfillStructural({ config: {} }, {});
  ok("cash fallback 10000 sem defaults", b.cash === 10000);
}

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DE MIGRACAO PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
