// FASE 7 (F7.1) — Guardião: Modo Operador (seletor + termo + Radar + sizing).
//
// Contratos trancados:
//  1) sizingPlano (finance.js): aritmética EXECUTÁVEL de position sizing —
//     lote de 100, risco = capital × pct, corta quando não cabe 1 lote;
//  2) config: appMode/operadorTermo/risco existem nos defaults e o deviceStore
//     NUNCA liga "operador" sem termo aceito (espelho do store.py);
//  3) Perfil: card do modo + termo com rolagem obrigatória + checkbox;
//  4) Radar: plano só aparece no modo operador (Estudo intocado — veredito
//     educacional continua no ramo else) e o disclaimer troca para o da persona.
// Roda sem build: `node web/tests/test_modo_operador.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { sizingPlano } from "../src/finance.js";
import { defaultState } from "../src/catalog.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const pers = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const disc = readFileSync(join(here, "..", "src", "disclaimers.js"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

// ---- 1) sizingPlano: contrato executável ------------------------------------
const plano = { decisao: "COMPRAR", entrada: 38.55, stop: 37.60, riscoPorAcao: 0.95, rr2: 2.0 };
const s1 = sizingPlano(plano, 50000, 1);            // risco R$500 / 0.95 = 526 → 500
ok("sizing: 500 ações p/ 50k a 1%", s1.qtd === 500 && s1.riscoFinanceiro === 500);
ok("sizing: valor aproximado correto", s1.valorAprox === 19275);
const s2 = sizingPlano(plano, 5000, 0.5);           // risco R$25 → não cabe 1 lote
ok("sizing: capital insuficiente => qtd 0 + aviso", s2.qtd === 0 && !!s2.aviso);
ok("sizing: NÃO OPERAR/AGUARDAR => null", sizingPlano({ decisao: "NÃO OPERAR" }, 50000, 1) === null);
ok("sizing: pct clampado em 5%", sizingPlano(plano, 50000, 99).riscoFinanceiro === 2500);
ok("sizing: sem capital => null", sizingPlano(plano, null, 1) === null);

// ---- 2) config: defaults + regra do termo nos dois stores -------------------
const cfg = defaultState().config;
ok("default appMode = estudo", cfg.appMode === "estudo");
ok("default operadorTermo = null", cfg.operadorTermo === null);
ok("default risco = 1% sem capital", cfg.risco.pctPorTrade === 1.0 && cfg.risco.capital === null);
ok("deviceStore: operador só com termo aceito",
  pers.includes('patch.appMode === "operador" && !(c.operadorTermo'));
ok("deviceStore: risco com clamps (0.25–5%)", /pctPorTrade = Math\.max\(0\.25, Math\.min\(5,/.test(pers));

// ---- 3) Perfil: card do modo + termo obrigatório ----------------------------
ok("card MODO DE TRABALHO no PerfilHub", app.includes("MODO DE TRABALHO") && app.includes("<ModoTrabalhoCard ctx={ctx} />"));
ok("1ª ativação abre o termo (sem aceite não liga)", app.includes("if (m === \"operador\" && !c.operadorTermo) { setTermoOpen(true); return; }"));
ok("termo exige rolagem até o fim", app.includes("setLiTudo(true)") && app.includes("disabled={!liTudo}"));
ok("aceite grava termo + modo no MESMO patch", app.includes("operadorTermo: { aceitoEm: new Date().toISOString(), versao: TERMO_OPERADOR_VERSAO }, appMode: \"operador\""));
ok("versão do termo é fonte única (disclaimers.js)", disc.includes('TERMO_OPERADOR_VERSAO = "1.0"'));

// ---- 4) Radar: plano gated pelo modo; Estudo intocado -----------------------
ok("plano só no modo operador", app.includes('const operador = (data.config && data.config.appMode) === "operador";') && app.includes("const plano = operador ? r.plano : null;"));
ok("decisões coloridas (COMPRAR/VENDER/AGUARDAR)", app.includes('"COMPRAR": [T.positive') && app.includes('"VENDER": [T.negative') && app.includes('"AGUARDAR CONFIRMAÇÃO": [T.accent'));
// qa/40: o fallback passou a usar decisaoDoModo(r, operador) — no ESTUDO o
// helper devolve exatamente r.veredito (comportamento preservado); na mesa,
// se um cache antigo vier sem plano, devolve a decisão em vez de "Estudar alta".
ok("veredito educacional segue no ramo estudo (via decisaoDoModo)",
  /plano \? \(\s*<span[^]*?\) : \([^]*?\{decisaoDoModo\(r, operador\)\}/.test(app)
  && /\(operador && item && item\.plano && item\.plano\.decisao\) \? item\.plano\.decisao : \(item \|\| \{\}\)\.veredito/.test(app));
ok("stop rotulado como invalidação do setup", app.includes("Stop (invalidação do setup)"));
ok("sizing usa capital real OU simulado com aviso", app.includes("capital simulado — defina o real na Config"));
ok("disclaimer da persona no modo operador", app.includes('=== "operador" ? DISCLAIMERS.operador : DISCLAIMERS.radar'));
ok("aviso do modo operador cita que o app não envia ordens", disc.includes("não envia ordens a corretoras"));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
