// Guardião da Fase 21 (v1.5, Redesenho de UI), requisitos DEDUP-01,
// DEDUP-03 e FIX-03 — remoção da CapitalCurve duplicada em Portfólio,
// consolidação dos 4 cards de KPI num único card denso 2×2, e o placeholder
// de "poucos dias" que substitui a reta de escala degenerada quando há só
// 1 ou 2 snapshots de patrimônio.
//
// Este arquivo é o único guardião da Fase 21 (nasceu no plano 21-01; a
// seção FIX-03 foi adicionada no plano 21-03). O que vier a tratar DEDUP-02
// (card de status do Operador IA) já foi resolvido no plano 21-02, que
// reescreveu guardiões dedicados em vez de estender este arquivo (ver nota
// no 21-02-SUMMARY.md). Qualquer novo achado sobre CapitalCurve/Portfólio
// nesta fase entra AQUI, não num arquivo novo.
//
// Roda sem build: `node web/tests/test_fase21_dedup_consolidacao.mjs`.
// Padrão da casa: regex sobre App.jsx lido com readFileSync — o módulo
// importa @capacitor/core e não é importável fora do build (ver
// test_fase3_c19_card_status.mjs, test_fase20_fundacao_visual.mjs). A
// Seção A (FIX-03) é a exceção: `finance.js` e `copy.js` são módulos ES
// puros, sem import de @capacitor/core, e por isso são importáveis de
// verdade via `await import(...)` (mesmo padrão de
// test_numeros_fundamentados.mjs e test_copy_theme.mjs) — testando
// comportamento real da função pura, não só grep sobre texto.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// --- Isolamento dos dois componentes envolvidos ---------------------------
// Mesmo padrão de isolamento de test_fase3_c19_card_status.mjs: do
// `function Xxx(` até o próximo `\nfunction ` no arquivo. Aborta com
// mensagem explícita se o marcador sumir — nunca passa em silêncio.

const inicioEvolucao = app.indexOf("function EvolucaoScreen(");
if (inicioEvolucao < 0) {
  console.error("FALHOU: função EvolucaoScreen não encontrada em App.jsx — guardião não pode isolar o componente");
  process.exit(1);
}
const fimEvolucao = app.indexOf("\nfunction ", inicioEvolucao + 10);
const evolucaoScreen = app.slice(inicioEvolucao, fimEvolucao > inicioEvolucao ? fimEvolucao : undefined);

const inicioCarteira = app.indexOf("function CarteiraScreen(");
if (inicioCarteira < 0) {
  console.error("FALHOU: função CarteiraScreen não encontrada em App.jsx — guardião não pode isolar o componente");
  process.exit(1);
}
const fimCarteira = app.indexOf("\nfunction ", inicioCarteira + 10);
const carteiraScreen = app.slice(inicioCarteira, fimCarteira > inicioCarteira ? fimCarteira : undefined);

// --- DEDUP-01: CapitalCurve existe em exatamente UMA tela ------------------

const totalCapitalCurve = (app.match(/<CapitalCurve/g) || []).length;
ok("DEDUP-01: exatamente 1 ocorrência de <CapitalCurve no arquivo inteiro", totalCapitalCurve === 1);

ok("DEDUP-01: a chamada sobrevivente de <CapitalCurve> está dentro de EvolucaoScreen", evolucaoScreen.includes("<CapitalCurve"));

ok("DEDUP-01: CarteiraScreen (rota Portfólio) NÃO contém <CapitalCurve", !carteiraScreen.includes("<CapitalCurve"));

// --- DEDUP-03: card consolidado 2×2 no lugar dos 4 cards kpi() -------------

ok("DEDUP-03: helper kpi( não existe mais em App.jsx", !/\bkpi\(/.test(app));

const numBodySpreadCount = (carteiraScreen.match(/\.\.\.numBody/g) || []).length;
ok("DEDUP-03: card consolidado usa ...numBody (pelo menos 4 ocorrências, uma por célula)", numBodySpreadCount >= 4);

const numMicroSpreadCount = (carteiraScreen.match(/\.\.\.numMicro/g) || []).length;
ok("DEDUP-03: card consolidado usa ...numMicro (pelo menos 1, sub-linha de percentual)", numMicroSpreadCount >= 1);

ok('DEDUP-03: grid 2 colunas presente (gridTemplateColumns: "1fr 1fr")', carteiraScreen.includes('gridTemplateColumns: "1fr 1fr"'));

ok("DEDUP-03: rótulo PATRIMÔNIO TOTAL presente em CarteiraScreen", carteiraScreen.includes("PATRIMÔNIO TOTAL"));
ok("DEDUP-03: rótulo RESULTADO ABERTO presente em CarteiraScreen", carteiraScreen.includes("RESULTADO ABERTO"));
ok("DEDUP-03: rótulo CAIXA DISPONÍVEL presente em CarteiraScreen", carteiraScreen.includes("CAIXA DISPONÍVEL"));
ok("DEDUP-03: rótulo EM POSIÇÕES presente em CarteiraScreen", carteiraScreen.includes("EM POSIÇÕES"));

ok("DEDUP-03: valor de patrimônio total continua vindo de {money(total)} (sem conta refeita no JSX)", carteiraScreen.includes("{money(total)}"));
ok("DEDUP-03: valor de resultado aberto continua vindo de {moneySigned(openPnL)}", carteiraScreen.includes("{moneySigned(openPnL)}"));
ok("DEDUP-03: sub-linha de percentual continua vindo de {pct(openPct)}", carteiraScreen.includes("{pct(openPct)}"));
ok("DEDUP-03: valor de caixa disponível continua vindo de {money(data.cash)}", carteiraScreen.includes("{money(data.cash)}"));
ok("DEDUP-03: valor em posições continua vindo de {money(positionsValue)}", carteiraScreen.includes("{money(positionsValue)}"));

ok(
  'DEDUP-03: grid antigo de 4 cards (gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))") não existe mais',
  !carteiraScreen.includes('gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))"')
);

// --- FIX-03 (plano 21-03): placeholder "poucos dias" em CapitalCurve ------
//
// Seção A — prova unitária do defeito: `equityCurve` é função pura de
// finance.js, importável de verdade (sem @capacitor/core no módulo).
// Padrão de import: test_numeros_fundamentados.mjs / test_copy_theme.mjs.

const { equityCurve } = await import(join(here, "..", "src", "finance.js"));

const umSnapshotHoje = equityCurve(
  [{ data: "2026-09-05", patrimonio: 10500, base: 10000 }],
  10000,
  10500,
  "2026-09-05"
);
ok("FIX-03: 1 snapshot datado de HOJE → ec.days === 1", umSnapshotHoje.days === 1);
// A prova da escala degenerada: com o snapshot de hoje SUBSTITUÍDO pelo
// valor ao vivo (finance.js:191-199, ramo "last.data === todayYmd"), a
// curva colapsa para [base, livePatr] — exatamente 2 pontos. min/max saem
// de dois valores, span é a diferença deles, e o resultado plotado é um
// único segmento reto, não uma curva com forma.
ok("FIX-03: mesmo caso → curve.length === 2 (a escala degenerada que motiva o placeholder)", umSnapshotHoje.curve.length === 2);

const umSnapshotOntem = equityCurve(
  [{ data: "2026-09-04", patrimonio: 10500, base: 10000 }],
  10000,
  10500,
  "2026-09-05"
);
ok("FIX-03: 1 snapshot datado de ONTEM → ec.days === 1 (mesmo gate, sub-caso diferente)", umSnapshotOntem.days === 1);
// Ramo de ANEXAR (finance.js:196-199): snapshot de ontem + valor ao vivo de
// hoje viram 2 entradas em `plot`, mais o ponto-base → 3 pontos ao todo.
// Ainda não é uma curva com forma, mas prova que os dois sub-casos de
// "1 dia" (mesmo-dia × dia-anterior) são cobertos uniformemente pelo gate
// em `ec.days`, sem precisar de caso especial.
ok("FIX-03: mesmo caso → curve.length === 3 (ramo de anexar, não de substituir)", umSnapshotOntem.curve.length === 3);

const doisSnapshots = equityCurve(
  [
    { data: "2026-09-03", patrimonio: 10200, base: 10000 },
    { data: "2026-09-04", patrimonio: 10500, base: 10000 },
  ],
  10000,
  10800,
  "2026-09-05"
);
ok("FIX-03: 2 snapshots → ec.days === 2", doisSnapshots.days === 2);

const zeroSnapshots = equityCurve([], 10000, 10000, "2026-09-05");
ok("FIX-03: 0 snapshots (conta nova) → ec.days === 0, mantém o texto de hoje", zeroSnapshots.days === 0);

// Seção B — limiar e ramo em App.jsx (grep sobre o corpo isolado de
// CapitalCurve). Mesmo padrão de isolamento de EvolucaoScreen/CarteiraScreen
// acima: indexOf("function CapitalCurve(") até o próximo "\nfunction ".

const inicioCapitalCurve = app.indexOf("function CapitalCurve(");
if (inicioCapitalCurve < 0) {
  console.error("FALHOU: função CapitalCurve não encontrada em App.jsx — guardião não pode isolar o componente");
  process.exit(1);
}
const fimCapitalCurve = app.indexOf("\nfunction ", inicioCapitalCurve + 10);
const capitalCurve = app.slice(inicioCapitalCurve, fimCapitalCurve > inicioCapitalCurve ? fimCapitalCurve : undefined);

ok("FIX-03: corpo de CapitalCurve contém o limiar novo \"ec.days >= 3\"", capitalCurve.includes("ec.days >= 3"));

ok("FIX-03: corpo de CapitalCurve NÃO contém mais o limiar antigo \"ec.days >= 1;\"", !capitalCurve.includes("ec.days >= 1;"));

ok(
  "FIX-03: flag poucosDias definido como \"ec.days >= 1 && ec.days < 3\"",
  capitalCurve.includes("ec.days >= 1 && ec.days < 3")
);

ok("FIX-03: ramo novo chama cp.curvaPoucosDias(ec.days) — nunca frase hardcodada", capitalCurve.includes("cp.curvaPoucosDias(ec.days)"));

ok(
  "FIX-03: CapitalCurve desestrutura cp de ctx (const { data, quotes, cp } = ctx;)",
  /const \{ data, quotes, cp \} = ctx;/.test(capitalCurve)
);

ok(
  "FIX-03: texto do estado ZERO segue byte a byte igual (\"Sua curva começa amanhã. Volte para vê-la crescer\")",
  capitalCurve.includes("Sua curva começa amanhã. Volte para vê-la crescer")
);

const estiloPlaceholderCount = (
  capitalCurve.match(/fontSize: "11\.5px", color: T\.textFaint, marginTop: "10px", lineHeight: 1\.5/g) || []
).length;
ok(
  "FIX-03: os dois ramos de placeholder (poucosDias e zero) usam o MESMO objeto de estilo (>= 2 ocorrências)",
  estiloPlaceholderCount >= 2
);

ok(
  "FIX-03: o rabisco tracejado do SVG segue intocado (mesma regex de test_benchmark_curva.mjs)",
  /M0,72 C60,66 110,58 150,52 C200,45 250,40 300,30/.test(capitalCurve)
);

// Seção C — a chave de copy nos dois modos (importa copy.js de verdade,
// padrão de test_copy_theme.mjs).

const { COPY } = await import(join(here, "..", "src", "copy.js"));

ok("FIX-03: COPY.estudo.curvaPoucosDias é função", typeof COPY.estudo.curvaPoucosDias === "function");
ok("FIX-03: COPY.operador.curvaPoucosDias é função", typeof COPY.operador.curvaPoucosDias === "function");

const callSafe = (fn, ...args) => {
  try { return typeof fn === "function" ? fn(...args) : undefined; } catch { return undefined; }
};

const estudo1 = callSafe(COPY.estudo.curvaPoucosDias, 1);
const estudo2 = callSafe(COPY.estudo.curvaPoucosDias, 2);
ok("FIX-03: COPY.estudo.curvaPoucosDias(1) menciona \"1 dia\" (singular)", typeof estudo1 === "string" && /\b1 dia\b/.test(estudo1));
ok("FIX-03: COPY.estudo.curvaPoucosDias(2) menciona \"2 dias\" (plural, texto diferente de dias=1)", typeof estudo2 === "string" && /\b2 dias\b/.test(estudo2) && estudo2 !== estudo1);
ok("FIX-03: COPY.estudo.curvaPoucosDias(1) menciona o 3º dia (casa com o limiar do código)", typeof estudo1 === "string" && /3º dia/.test(estudo1));
ok("FIX-03: COPY.estudo.curvaPoucosDias(2) menciona o 3º dia (casa com o limiar do código)", typeof estudo2 === "string" && /3º dia/.test(estudo2));

const operador1 = callSafe(COPY.operador.curvaPoucosDias, 1);
const operador2 = callSafe(COPY.operador.curvaPoucosDias, 2);
ok("FIX-03: COPY.operador.curvaPoucosDias(1) menciona \"1 dia\" (singular)", typeof operador1 === "string" && /\b1 dia\b/.test(operador1));
ok("FIX-03: COPY.operador.curvaPoucosDias(2) menciona \"2 dias\" (plural, texto diferente de dias=1)", typeof operador2 === "string" && /\b2 dias\b/.test(operador2) && operador2 !== operador1);
ok("FIX-03: COPY.operador.curvaPoucosDias(1) menciona o 3º dia (casa com o limiar do código)", typeof operador1 === "string" && /3º dia/.test(operador1));
ok("FIX-03: COPY.operador.curvaPoucosDias(2) menciona o 3º dia (casa com o limiar do código)", typeof operador2 === "string" && /3º dia/.test(operador2));

console.log(fails === 0 ? "\ntodos os testes passaram — DEDUP-01, DEDUP-03 (plano 21-01) e FIX-03 (plano 21-03)" : `\n${fails} asserção(ões) falharam`);
process.exit(fails);
