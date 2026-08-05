// F1 — Guardião do TIMING DE ENTRADA na UI: o card único do ativo (AtivoCard)
// exibe o estado determinístico de /api/timing (plano diário × barra 15m
// FECHADA) como badge honesto — hora da barra (asOf), ressalvas do backend
// (atraso ~15 min; lacuna) e a FRASE por modo vinda pronta do servidor.
// Contratos travados: sem_plano é silêncio (não ruído); paridade dos DOIS
// stores (deviceStore manda appMode local-first, como o scanDeep).
// Roda sem build: `node web/tests/test_timing_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const api = readFileSync(join(here, "..", "src", "api.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// cliente HTTP: endpoint real, com appMode opcional (iOS local-first)
ok("api.timing chama GET /api/timing/{ticker}", /timing: \(t, appMode\) => req\("GET", "\/api\/timing\/"/.test(api));
ok("api.timing propaga appMode como query", /appMode \? "\?appMode=" \+ encodeURIComponent\(appMode\)/.test(api));

// paridade dos DOIS stores (persistence.js): método novo entra nos dois
ok("serverStore expõe timing (modo fica com o servidor)", /timing: \(t\) => api\.timing\(t\)/.test(persistence));
ok("deviceStore expõe timing com appMode local-first", /async timing\(t\) \{ ensure\(\); return api\.timing\(t, doc\.config\.appMode \|\| "estudo"\); \}/.test(persistence));

// badge no card único
ok("TimingBadge existe e busca via store.timing", /function TimingBadge\(\{ t, operador,/.test(app) && /store\.timing\(t\)/.test(app));
ok("AtivoCard renderiza <TimingBadge> (todas as superfícies)", /<TimingBadge t=\{t\} operador=\{operador\}/.test(app));

// honestidade: sem_plano não vira ruído; estados cobertos são os 4 visíveis
ok("sem_plano é silêncio (estado fora do TIMING_STYLE => null)", /if \(!r \|\| !TIMING_STYLE\[r\.estado\]\) return null;/.test(app) && !/sem_plano:/.test(app));
ok("estados visíveis: gatilho, armado, esticado, sem_dado", /gatilho: \[/.test(app) && /armado: \[/.test(app) && /esticado: \[/.test(app) && /sem_dado: \[/.test(app));

// carimbo e ressalvas: a hora da barra fechada (asOf) + ressalvas do backend
ok("badge mostra a hora da barra 15m fechada (asOf)", /barra 15m de \$\{hora\}/.test(app) && /r\.asOf\.split\(" "\)\[1\]\.slice\(0, 5\)/.test(app));
ok("badge exibe as ressalvas do backend (atraso/lacuna)", /r\.ressalvas\.join\(" "\)/.test(app));

// HONESTIDADE DA IDADE DO DADO (2026-08-05): o mesmo estado `sem_dado` tem três
// leituras diferentes, e confundi-las já produziu card mentindo — "sem dado
// confiável" toda noite (era pregão fechado) e "armado/gatilho" de manhã com a
// barra de ONTEM. As variantes vêm de flags do backend, não de estado novo.
ok("variante fora do pregão (foraDoPregao => rótulo próprio)",
   /fora_pregao: \[/.test(app) && /r\.foraDoPregao \? "fora_pregao"/.test(app));
ok("variante barra do pregão anterior (barraDeOutroDia => rótulo próprio)",
   /aguardando_barra: \[/.test(app) && /r\.barraDeOutroDia \? "aguardando_barra"/.test(app));
ok("barra de outro dia mostra a DATA, não só a hora (senão esconde a idade)",
   /r\.barraDeOutroDia \? `última barra \$\{r\.asOf\}`/.test(app));

// vocabulário por modo: frase pronta do servidor; rótulo do estudo sem verbo de ordem
ok("frase por modo vem PRONTA do backend ({r.frase})", /\{r\.frase\}/.test(app));
ok("rótulo do estudo descreve condição (sem verbo de ordem)", /CONDIÇÃO ATINGIDA/.test(app) && /CONDIÇÃO ARMADA/.test(app));

// números que sustentam o estado: distância/excedente em R
ok("armado mostra distância em R até o nível", /r\.estado === "armado" && r\.distanciaEmR != null/.test(app));
ok("gatilho/esticado mostram excedente em R", /r\.excedenteEmR != null/.test(app));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
