// Fase 51 (51-10) — guardião da integração do card "Seu dia na bolsa" no App.
// Lê App.jsx e notify.js como texto; remove linhas de comentário antes das
// buscas de ausência. Roda sem build: `node web/tests/test_dia_na_bolsa_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const bruto = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const notifBruto = readFileSync(join(here, "..", "src", "notify.js"), "utf8");
const semComent = (t) => t.split("\n").filter((l) => !/^\s*(\/\/|\*|\{\/\*)/.test(l)).join("\n");
const app = semComent(bruto);
const notify = semComent(notifBruto);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// (a) slot do card antes do OperadorIACard, dentro de EvolucaoScreen
const ini = app.indexOf("function EvolucaoScreen");
const fim = app.indexOf("\nfunction ", ini + 10);
const evo = app.slice(ini, fim > 0 ? fim : undefined);
const iCard = evo.indexOf("<DiaNaBolsaCard");
const iOper = evo.indexOf("<OperadorIACard");
ok("EvolucaoScreen: <DiaNaBolsaCard antes de <OperadorIACard", iCard >= 0 && iOper > iCard);

// (b) streak por abertura e data UTC fora
ok("sem toISOString().slice(0, 10) no App", !app.includes("toISOString().slice(0, 10)"));
ok("sem streakRanRef no App", !app.includes("streakRanRef"));

// (c) registrarDecisao usa hojeBRT()
const bd = app.slice(app.indexOf("registrarDecisao: (origem)"), app.indexOf("registrarDecisao: (origem)") + 900);
ok("registrarDecisao usa hojeBRT()", bd.includes("hojeBRT()"));
ok("decision_day emitido 1x com modo e origem", (app.match(/track\("decision_day"/g) || []).length === 1 && /track\("decision_day", \{ modo: appMode, origem \}\)/.test(app));

// (d) origens só card|plano|stop
const origens = new Set([...app.matchAll(/registrarDecisao\("([^"]+)"\)/g)].map((m) => m[1]));
ok("origens de registrarDecisao(...) só card|plano|stop", [...origens].every((o) => ["card", "plano", "stop"].includes(o)) && origens.has("stop"));
ok("guarda de origem no registrarDecisao", /origem !== "card" && origem !== "plano" && origem !== "stop"/.test(app));
ok("sem 'não entrar' como origem de decisão (emenda D-16)", !/registrarDecisao\("(nao_entrar|naoEntrar|não entrar)"\)/.test(app));

// (e) radar_result_opened leva setup
ok("radar_result_opened leva setup", /track\("radar_result_opened", \{ ticker: t, setup: setupRadar \}\)/.test(app));

// (f) vistos: radar, watchlist e carteira
ok("registrarVistos radar", /registrarVistos\(\[t\], "radar"\)/.test(app));
ok("registrarVistos watchlist", /registrarVistos\([^)]*"watchlist"\)/.test(app));
ok("registrarVistos carteira", /registrarVistos\([^\n]*"carteira"\)/.test(app));
ok("vistos diários 1x por dia BRT (chave b3-dnb-vistos-dia)", app.includes("b3-dnb-vistos-dia"));

// (g) convite/config pela rota única; fechamento nunca em notif
ok("decidirFechamento( presente (>=2)", (app.match(/decidirFechamento\(/g) || []).length >= 2);
ok("nenhum notif com fechamento", !/notif[^;\n]*fechamento|fechamento:[^;\n]*notif/.test(app));

// (h) notify.js aceita só o kind exato "fechamento" sem ticker
ok("notify.js aceita kind fechamento", /d\.kind \|\| ""\) === "fechamento"/.test(notify) && notify.includes('handler(null, "fechamento")'));
ok("App roteia kind fechamento para o Acompanhar", /kind === "fechamento"[\s\S]{0,200}setTab\("evolucao"\)/.test(app));

if (fails) { console.log(`\n${fails} FALHOU`); process.exit(1); }
console.log("\ntodos os testes passaram");
