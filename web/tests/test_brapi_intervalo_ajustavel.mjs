// qa/45 (pedido do Alex, 2026-08-12): "a sessão fonte de dados deve ser
// parametrizável apresentando a possibilidade de mudar o parâmetro de tempo
// de atualização e a partir daí é calculado para ver se o número de
// requisições vai ser suficiente ou não." O endpoint /api/obs/brapi/projecao
// (GET simula, POST aplica) já existia no backend (ADR-008) desde a Fase 6,
// mas tinha ZERO fio até o front (nem api.js, nem persistence.js liam
// "brapi" em lugar nenhum) — guardião: trava a existência do fio completo.
// Roda sem device nem build: `node web/tests/test_brapi_intervalo_ajustavel.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const api = readFileSync(join(here, "..", "src", "api.js"), "utf8");
const persist = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) cliente HTTP: GET simula, POST aplica -----------------------------
ok("api.brapiProjecao chama GET /api/obs/brapi/projecao com intervaloS na query",
  /brapiProjecao: \(intervaloS\) => req\("GET", "\/api\/obs\/brapi\/projecao"/.test(api));
ok("api.brapiProjecaoAplicar chama POST com { intervaloS, aplicar: true }",
  /brapiProjecaoAplicar: \(intervaloS\) => req\("POST", "\/api\/obs\/brapi\/projecao", \{ intervaloS, aplicar: true \}/.test(api));

// ---- 2) paridade obrigatória dos DOIS stores (CLAUDE.md) -------------------
ok("serverStore expõe brapiProjecao", /brapiProjecao: \(intervaloS\) => api\.brapiProjecao\(intervaloS\)/.test(persist));
ok("serverStore expõe brapiProjecaoAplicar", /brapiProjecaoAplicar: \(intervaloS\) => api\.brapiProjecaoAplicar\(intervaloS\)/.test(persist));
ok("deviceStore expõe brapiProjecao", /async brapiProjecao\(intervaloS\) \{ ensure\(\); return api\.brapiProjecao\(intervaloS\); \}/.test(persist));
ok("deviceStore expõe brapiProjecaoAplicar", /async brapiProjecaoAplicar\(intervaloS\) \{ ensure\(\); return api\.brapiProjecaoAplicar\(intervaloS\); \}/.test(persist));

// ---- 3) FonteDadosScreen: o controle existe e é parametrizável -------------
const fdIdx = app.indexOf("function FonteDadosScreen(");
const fdBlock = app.slice(fdIdx, app.indexOf("/* BLOCO 3 — Radar de mercado", fdIdx));
ok("FonteDadosScreen localizada", fdIdx > -1);
ok("seção AJUSTAR INTERVALO DO SPOT existe", fdBlock.includes("AJUSTAR INTERVALO DO SPOT"));
ok("input numérico de intervalo, mínimo 30s", /<input type="number" min=\{30\}/.test(fdBlock));

// simula ao digitar (GET), SEM aplicar sozinho — só via debounce + store.brapiProjecao
ok("simula via store.brapiProjecao (GET) num debounce (setTimeout)",
  /setTimeout\(async \(\) => \{[\s\S]{0,80}setSim\(await store\.brapiProjecao\(n\)\)/.test(fdBlock));
ok("não aplica sozinho: aplicarIntervalo só roda no onClick do botão 'Aplicar'",
  /<button onClick=\{aplicarIntervalo\}/.test(fdBlock));
ok("aplicação real via store.brapiProjecaoAplicar (POST aplicar:true, no backend)",
  /const aplicarIntervalo = async \(\) => \{[\s\S]{0,400}store\.brapiProjecaoAplicar\(intervaloNum\)/.test(fdBlock));

// botão Aplicar desabilitado enquanto inválido/simulando/sem mudança — não deixa
// aplicar lixo nem reaplicar o que já está vigente
ok("Aplicar desabilita se inválido, simulando ou intervalo igual ao vigente",
  /disabled=\{applyBusy \|\| simBusy \|\| !intervaloValido \|\| intervaloInalterado\}/.test(fdBlock));

// mostra o cálculo de suficiência (é o pedido central: "vai ser suficiente ou não")
ok("mostra chamadas/mês projetadas vs a cota", /simProj\.chamadasMes\}\/\{simProj\.cotaMes\}/.test(fdBlock));
ok("marca claramente quando NÃO CABE NA COTA", /NÃO CABE NA COTA/.test(fdBlock));
ok("sugere o intervalo mínimo seguro quando não cabe", /intervaloMinimoSeguro/.test(fdBlock));
ok("erro de rede/servidor aparece tratado (nunca invisível — princípio #4 do CLAUDE.md)",
  /setSimErr\(\(e && e\.message\) \|\| String\(e\)\)/.test(fdBlock) && /\{simErr && /.test(fdBlock));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
