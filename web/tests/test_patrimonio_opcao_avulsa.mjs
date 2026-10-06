// Guardião quick 261006-bwv (2026-10-06): perna de opção comprada SEM lastro
// (buy_option, "perna avulsa") entra no patrimônio. Caso real: PUT VALEV731W2,
// 100 x R$ 0,92 debitou R$ 92 do caixa e sumia do patrimônio.
// Paridade: MESMA fixture lida por server/tests/test_patrimonio_opcao_avulsa.py.
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { portfolioMetrics } from "../src/finance.js";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const near = (a, b, eps = 1e-9) => Math.abs(a - b) <= eps;

const fixture = JSON.parse(readFileSync(
  join(here, "..", "..", "server", "tests", "fixtures", "patrimonio_opcoes_paridade.json"), "utf8"));
ok("fixture tem 7 casos", fixture.casos.length === 7);

for (const c of fixture.casos) {
  const m = portfolioMetrics([], {}, c.cash, c.reservado, c.optionPositions, c.optionQuotes);
  const e = c.esperado;
  ok(`${c.nome}: opcoesVal`, near(m.opcoesVal, e.opcoesVal));
  ok(`${c.nome}: opcoesPnL`, near(m.opcoesPnL, e.opcoesPnL));
  ok(`${c.nome}: opcoesSemMarcacao`, m.opcoesSemMarcacao === e.semMarcacao);
  ok(`${c.nome}: patr`, near(m.patr, e.patr));
}

{
  const perna = [{ id: "VALEV731W2", optionType: "put", qty: 100, avg: 0.92 }];
  const antes = portfolioMetrics([], {}, 10000, 0, []);
  const depois = portfolioMetrics([], {}, 9908, 0, perna);
  ok("VALEV731W2: patrimônio igual antes e depois da compra", near(antes.patr, depois.patr));
  const vivo = portfolioMetrics([], {}, 9908, 0, perna, { VALEV731W2: 1.10 });
  ok("VALEV731W2 com cotação 1.10 -> 10018", near(vivo.patr, 10018));
}
{
  const m = portfolioMetrics([], {}, 1000, 0);
  ok("4 argumentos: opcoesVal 0 e opcoesSemMarcacao 0", m.opcoesVal === 0 && m.opcoesSemMarcacao === 0);
}

// ---- sinalização na UI (estático) ----
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const count = (s, sub) => s.split(sub).length - 1;
ok("App.jsx: 'opcoesSemMarcacao > 0' aparece >= 2 vezes", count(app, "opcoesSemMarcacao > 0") >= 2);
ok("App.jsx: condição antiga por lastro removida", !app.includes(".some((p) => p && p.lastro) && ("));
ok("App.jsx: continua com exatamente 7 chamadas de portfolioMetrics(",
  (app.match(/portfolioMetrics\(/g) || []).length === 7);
for (const modo of ["estudo", "operador"]) {
  const t = COPY[modo].linhaPatrimonioOpcoes;
  ok(`COPY.${modo}.linhaPatrimonioOpcoes diz prêmio de abertura e sem cotação ao vivo`,
    typeof t === "string" && t.includes("prêmio de abertura") && t.includes("sem cotação ao vivo"));
}
ok("COPY.estudo.linhaPatrimonioOpcoes não diz mais 'lastreadas'",
  !COPY.estudo.linhaPatrimonioOpcoes.includes("lastreadas"));

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntudo ok");
