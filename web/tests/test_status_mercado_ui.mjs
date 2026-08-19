// Fase 2 (MERC-01, D-08) — Guardião do status real de mercado na UI.
//
// Este arquivo cresce em 3 tasks do plano 02-05:
//  Task 1: textos do badge em copy.js (chaves simétricas, sem invenção de horário).
//  Task 2: estado único `mercado` no root + componente MarketStatusBadge.
//  Task 3: render pré-login (WelcomeAuthScreen) e pós-login (Topbar) + o
//          patrimônio (portfolioMetrics) contando o caixa reservado.
//
// App.jsx não é importável fora de um build (single-file, sem export das
// funções internas) — por isso as tasks 2/3 verificam por INSPEÇÃO ESTÁTICA
// da fonte (readFileSync + grep/regex), técnica já usada no resto da suíte
// web (test_copy_theme.mjs, test_brand_book_v2_tokens.mjs).
// Roda sem build: `node web/tests/test_status_mercado_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { copyFor } from "../src/copy.js";
import { portfolioMetrics } from "../src/finance.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- Task 1: textos do badge em copy.js ------------------------------------
for (const modo of ["estudo", "operador"]) {
  const cp = copyFor(modo);
  ok(`${modo}: mercadoAberto existe e é string`, typeof cp.mercadoAberto === "string" && cp.mercadoAberto.length > 0);
  ok(`${modo}: mercadoFechado é função`, typeof cp.mercadoFechado === "function");
  ok(`${modo}: mercadoFechado("10:00") contém o horário`, cp.mercadoFechado("10:00").includes("10:00"));
  ok(`${modo}: mercadoFechado() sem argumento não inventa horário`, !/\d{1,2}:\d{2}/.test(cp.mercadoFechado()));
  ok(`${modo}: mercadoIndisponivel existe e é string`, typeof cp.mercadoIndisponivel === "string" && cp.mercadoIndisponivel.length > 0);
  ok(`${modo}: mercadoIndisponivel não afirma aberto nem fechado`, !/aberto|fechado/i.test(cp.mercadoIndisponivel));
}
ok("chaves do badge não quebram a simetria estudo × operador (já coberto por test_copy_theme.mjs, reforço aqui)",
  ["mercadoAberto", "mercadoFechado", "mercadoIndisponivel"].every((k) => k in copyFor("estudo") && k in copyFor("operador")));
ok("vocabulário de ordem proibido no ramo estudo não vazou pelas chaves novas",
  !/comprar|vender|compre|venda/i.test(
    copyFor("estudo").mercadoAberto + copyFor("estudo").mercadoFechado("10:00") + copyFor("estudo").mercadoFechado() + copyFor("estudo").mercadoIndisponivel
  ));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
