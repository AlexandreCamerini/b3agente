// Quick 261013-u7w (2026-10-13): paridade servidor x front do patrimonio da conta.
// MESMA fixture lida por server/tests/test_patrimonio_conta_paridade.py
// (store.patrimonio_conta). Aqui o espelho de verdade e portfolioMetrics.
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { portfolioMetrics } from "../src/finance.js";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const near = (a, b, eps = 1e-9) => Math.abs(a - b) <= eps;

const fixture = JSON.parse(readFileSync(
  join(here, "..", "..", "server", "tests", "fixtures", "patrimonio_conta_paridade.json"), "utf8"));
ok("fixture tem 7 casos", fixture.casos.length === 7);

for (const c of fixture.casos) {
  const m = portfolioMetrics(c.positions, c.quotes, c.cash, c.reservado, c.optionPositions, c.optionQuotes);
  const e = c.esperado;
  ok(`${c.nome}: patr`, near(m.patr, e.patr));
  ok(`${c.nome}: posVal`, near(m.posVal, e.posVal));
  ok(`${c.nome}: opcoesVal`, near(m.opcoesVal, e.opcoesVal));
}

process.exit(fails ? 1 : 0);
