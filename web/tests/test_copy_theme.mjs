// FASE 8B (B1/B2/B4) — Guardião: "dois apps em um" de verdade.
//
// Contratos trancados:
//  1) copy.js: chaves espelhadas nos dois modos; vocabulário de ordem proibido
//     no ramo ESTUDO; fallback seguro para modo desconhecido;
//  2) B1: as telas leem ctx.cp.* — os textos sensíveis não estão mais
//     hardcodados no App.jsx (títulos, botões, empty states, toasts, saudação);
//  3) B2: override de tema .b3-mode-operador (verde #22c55e), classe aplicada
//     no html, chip do modo no Topbar, theme-color por modo, transição só na troca;
//  4) B4: notificações (stop/alvo/variação) na voz do modo; managed preserva
//     o appMode; N3 ganha a camada de mesa no modo operador.
// Roda sem build: `node web/tests/test_copy_theme.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY, copyFor } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const mainPy = readFileSync(join(here, "..", "..", "server", "app", "main.py"), "utf8");
const llmPy = readFileSync(join(here, "..", "..", "server", "app", "llm.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) copy.js íntegro -----------------------------------------------------
const e = Object.keys(COPY.estudo).sort(), o = Object.keys(COPY.operador).sort();
ok("chaves espelhadas nos dois modos (" + e.length + ")", JSON.stringify(e) === JSON.stringify(o));
const estTxt = JSON.stringify(Object.values(COPY.estudo).map((v) => (typeof v === "function" ? v("X", "Y", "Z") + v(null, 0, 0) : v)));
ok("ramo ESTUDO sem vocabulário de ordem", !/registrar entrada|registrar saída|execute a saída|COMPRAR|VENDER/i.test(estTxt.replace(/Simular compra|Simular venda|venda simulada|compra simulada/gi, "")));
ok("fallback para modo desconhecido = estudo", copyFor("banana") === COPY.estudo);

// ---- 2) B1: telas leem cp.* (sem texto sensível hardcodado) -----------------
for (const [nome, usado, proibido] of [
  ["título do Radar", "cp.tituloRadar", ">Radar de mercado</h1>"],
  ["título da Watchlist", "cp.tituloWatchlist", ">Watchlist</h1>"],
  ["título do Portfólio", "cp.tituloPortfolio", ">Portfólio</h1>"],
  ["botão comprar", "cp.btnComprar", ">Simular compra"],
  ["botão vender", "cp.btnVender", ">Simular venda"],
  ["botão aprofundar", "cp.btnAprofundar", ': "Aprofundar com IA"}'],
  ["empty da watchlist", "cp.vazioWatchlist", ">Sua watchlist está vazia<"],
  ["empty do portfólio", "cp.vazioPortfolio", ">Você ainda não tem posições."],
]) {
  ok(nome + " vem do copy.js", app.includes(usado) && !app.includes(proibido));
}
ok("saudação + resumo do dia na voz do modo", app.includes("cp.saudacao(") && app.includes("cp.resumoDia("));
ok("toasts de compra/venda na voz do modo", app.includes("cp.toastCompra(") && app.includes("cp.toastVenda("));
ok("nav fala a língua do modo", app.includes('["mercado", (cp && cp.tituloWatchlist)'));

// ---- 3) B2: tema por modo ----------------------------------------------------
ok("override .b3-mode-operador com verde-mercado", app.includes('accent: "#22c55e"') && app.includes("b3-mode-operador.b3-theme-dark"));
ok("classe aplicada no html pelo appMode", app.includes('html.classList.toggle("b3-mode-operador", appMode === "operador")'));
ok("chip do modo no Topbar", app.includes("modeChip={cp.chipModo}") && app.includes("{modeChip && <span"));
ok("theme-color acompanha o modo", app.includes('appMode === "operador" ? "#0a0d10"'));
ok("transição só durante a troca (classe temporária)", app.includes("b3-mode-switch") && app.includes('html.classList.remove("b3-mode-switch")'));

// ---- 4) B4: notificações + backend ------------------------------------------
ok("notificações de stop/alvo/variação na voz do modo",
  app.includes("cp.notifStopTitulo(") && app.includes("cp.notifAlvoTitulo(") && app.includes("cp.notifVarTitulo("));
ok("managed preserva o appMode (mesa não vira professor)", mainPy.includes('{**mcfg, "appMode": (config or {}).get("appMode")}'));
ok("N3 ganha a camada de mesa no modo operador", llmPy.includes("is_operador(config)") && llmPy.includes("Fale como mesa de opera"));

// ---- UX: prevenções de plataforma -------------------------------------------
ok("inputs com 16px (sem zoom automático do Safari)", app.includes("font-size:16px"));
ok("sem flash cinza de toque do iOS", app.includes("-webkit-tap-highlight-color: transparent"));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
