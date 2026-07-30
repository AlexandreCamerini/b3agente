// qa/40 — Guardião: no MODO OPERADOR nenhuma pill de decisão mostra o
// veredito educacional ("Estudar alta/baixa") — a decisão exibida vem do
// PLANO determinístico via decisaoDoModo(item, operador).
//
// Reporte do Alex: "continua mostrando estudar alta/baixa no perfil operador".
// Superfícies corrigidas: hero da home, lista de setups da home e linha da
// Watchlist (o Radar já usava plano.decisao desde F7.1).
// Roda sem build: `node web/tests/test_decisao_modo.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

ok("helper decisaoDoModo definido (plano.decisao na mesa, veredito no estudo)",
  /const decisaoDoModo = \(item, operador\) =>/.test(app) && /item\.plano\.decisao/.test(app));

// nenhuma superfície de card renderiza `.veredito` CRU como conteúdo de pill —
// tudo passa pelo helper. (usos legítimos restantes: metadados/buyMeta, não render.)
const renders = (app.match(/>\{(r|it|sc)\.veredito\}</g) || []);
ok("nenhuma pill renderiza veredito cru (todas via decisaoDoModo)", renders.length === 0);
ok("home (hero + lista) usa decisaoDoModo", (app.match(/decisaoDoModo\((r|it), operador\)/g) || []).length >= 3);
ok("watchlist usa decisaoDoModo", /rotuloDec = decisaoDoModo\(sc, operador\)/.test(app));

// as duas telas têm a flag operador em escopo (senão: ReferenceError em runtime)
const evo = app.slice(app.indexOf("function EvolucaoScreen("), app.indexOf("function ModoTrabalhoCard("));
const mer = app.slice(app.lastIndexOf("function MercadoScreen("), app.indexOf("function StopAlvoModal("));
ok("EvolucaoScreen define operador", /const operador = \(data\.config && data\.config\.appMode\) === "operador"/.test(evo));
ok("MercadoScreen define operador", /const operador = \(data\.config && data\.config\.appMode\) === "operador"/.test(mer));

// qa/40: o KpiBlock (análise expandida no Monitoramento) troca o rótulo
// "PLANO EDUCACIONAL" por "DECISÃO DA MESA" no operador — e recebe a flag.
ok("KpiBlock é mode-aware (rótulo por modo)",
  /operador \? "DECISÃO DA MESA" : "PLANO EDUCACIONAL"/.test(app));
// qa/49 (v11): o KpiBlock saiu do card do ativo — a decisão virou a MANCHETE
// única `decM` (decisaoDoModo do plano, com fallback p/ recDoModo da IA), que
// segue mode-aware ("DECISÃO DA MESA" no operador).
ok("watchlist: decisão é a manchete única decM (mode-aware)",
  /const decM = rotuloDec \|\| \(kp\.recomendacao/.test(app)
  && /operador \? "DECISÃO DA MESA" : "PLANO EDUCACIONAL"/.test(app));

// qa/40: o VALOR da decisão no KpiBlock também é mapeado no render (cache antigo
// de estudo → mesa), não só o rótulo. Reporte do Alex: "no DECISÃO DA MESA
// está estudar baixa".
ok("recDoModo mapeia estudo→mesa no render", /recDoModo = \(rec, operador\) =>/.test(app)
  && /REC_PRO_MAP = \{/.test(app) && /"Estudar baixa": "VENDER"/.test(app));
ok("KpiBlock exibe rec mapeado (não kpis.recomendacao cru)",
  /const rec = recDoModo\(kpis\.recomendacao, operador\)/.test(app) && /fontSize: "14px", color: recColor \}\}>\{rec\}</.test(app));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
