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

// ---- Task 2: estado único no root + MarketStatusBadge -----------------------
const countOcorr = (re) => (app.match(re) || []).length;
ok("store.marketStatus( aparece exatamente 1 vez em App.jsx (uma única fonte)",
  countOcorr(/store\.marketStatus\(/g) === 1);

function funcBody(nome) {
  const i = app.indexOf(`function ${nome}(`);
  if (i < 0) return "";
  // pula a lista de parâmetros (pode ter chaves de destructuring, ex.:
  // `function X({ a, b })`) até achar o "(" que fecha os parâmetros.
  let pDepth = 0, k = app.indexOf("(", i);
  for (; k < app.length; k++) {
    if (app[k] === "(") pDepth++;
    else if (app[k] === ")") { pDepth--; if (!pDepth) break; }
  }
  let depth = 0, start = app.indexOf("{", k), j = start;
  for (; j < app.length; j++) {
    if (app[j] === "{") depth++;
    else if (app[j] === "}") { depth--; if (!depth) break; }
  }
  return app.slice(start, j + 1);
}
const badgeSrc = funcBody("MarketStatusBadge");
ok("MarketStatusBadge está definido", badgeSrc.length > 0);
ok("MarketStatusBadge é definido ANTES de Topbar", app.indexOf("function MarketStatusBadge") < app.indexOf("function Topbar"));
ok("MarketStatusBadge usa T.positive, T.negative e T.warn (3 estados)",
  badgeSrc.includes("T.positive") && badgeSrc.includes("T.negative") && badgeSrc.includes("T.warn"));
ok("MarketStatusBadge NUNCA usa T.accent (precisa renderizar igual pré-login e nos dois modos)",
  !/T\.accent/.test(badgeSrc));

// efeito de boot: consulta + cleanup de listener/timer (T-02-25)
const iEfeito = app.indexOf("const [mercado, setMercado] = useState(null);");
const efeitoSrc = iEfeito >= 0 ? app.slice(iEfeito, iEfeito + 1800) : "";
ok("useState(null) para `mercado` existe no root (carregando = nada afirmado)", iEfeito >= 0);
ok("efeito de boot chama store.marketStatus()", efeitoSrc.includes("store.marketStatus()"));
ok("falha de rede cai em { erro: true }, sem flash (não é erro do usuário)",
  efeitoSrc.includes("setMercado({ erro: true })") && !/flash\(/.test(efeitoSrc.slice(0, efeitoSrc.indexOf("erro: true"))));
ok("reconsulta em visibilitychange/focus", efeitoSrc.includes('"visibilitychange"') && efeitoSrc.includes('"focus"'));
ok("cleanup remove os listeners e o intervalo (removeEventListener + clearInterval)",
  efeitoSrc.includes("removeEventListener") && efeitoSrc.includes("clearInterval"));

// tela de diagnóstico do Operador continua lendo srv.pregaoAberto (status do
// SERVIDOR), coexistindo de propósito com ctx.mercado (status público) — não
// deve ter sido substituída/removida por este plano.
ok("diagnóstico do Operador continua lendo srv.pregaoAberto (dado diferente de ctx.mercado)",
  app.includes("srv.pregaoAberto"));

// ---- Task 3: render pré/pós-login + portfolioMetrics com caixa reservado ---
const welcomeSrc = funcBody("WelcomeAuthScreen");
ok("WelcomeAuthScreen contém MarketStatusBadge", welcomeSrc.includes("<MarketStatusBadge"));
ok("WelcomeAuthScreen NÃO passou a referenciar ctx.data (contrato self-contained/undefined-safe)",
  !welcomeSrc.includes("ctx.data"));
ok("badge da tela de login usa ctx.mercado/ctx.cp (mesmo canal de sempre, sem sessão)",
  /<MarketStatusBadge\s+mercado=\{ctx\.mercado\}\s+cp=\{ctx\.cp\}/.test(welcomeSrc));

const topbarSrc = funcBody("Topbar");
ok("Topbar contém MarketStatusBadge", topbarSrc.includes("<MarketStatusBadge"));
ok("Topbar aceita mercado/cp como props", /function Topbar\(\{[^}]*\bmercado\b[^}]*\bcp\b[^}]*\}\)/.test(app));

const chamadasPM = app.match(/portfolioMetrics\(([^)]*)\)/g) || [];
ok("existem as 7 chamadas de portfolioMetrics( esperadas", chamadasPM.length === 7);
ok("nenhuma chamada de portfolioMetrics( ficou com só 3 argumentos",
  chamadasPM.every((call) => call.split(",").length >= 4));
ok("as 7 chamadas de portfolioMetrics( passam data.caixaReservado (ou equivalente undefined-safe)",
  chamadasPM.filter((c) => c.includes("caixaReservado")).length === 7);

// caso numérico sobre a função PURA (não sobre o DOM): caixa reservado > 0
// não faz o patrimônio cair — mesma prova que o guardião de 02-04 já faz em
// finance.js, reforçada aqui do ponto de vista da UI que agora a alimenta.
{
  const semReserva = portfolioMetrics([{ t: "PETR4", qty: 100, avg: 30 }], { PETR4: { price: 30 } }, 1000, 0);
  const comReserva = portfolioMetrics([{ t: "PETR4", qty: 100, avg: 30 }], { PETR4: { price: 30 } }, 700, 300);
  ok("criar uma ordem pendente (cash -300, reservado +300) não faz o patrimônio da Topbar cair",
    semReserva.patr === comReserva.patr);
}

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
