// Fase 43 (HIER-03, D-07/D-08/D-11/D-12/D-13) — Parte A: helper puro de
// copy.js (reconciliacaoTxt/reconciliacaoPorQueImporta) e os rótulos da
// "Leitura da IA" (CHIP-03, sinal.leituraIa). A Parte B (fiação no
// App.jsx/HistoricoPill/AnalysisView) entra no 43-04 — este guardião não lê
// App.jsx.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { COPY, copyFor, reconciliacaoTxt, reconciliacaoPorQueImporta } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};

// ---------------------------------------------------------------------------
// reconciliacaoTxt — comportamento por modo/estado
// ---------------------------------------------------------------------------

ok('reconciliacaoTxt("operador","inelegivel",...) fato curto com n/janela/expR',
  reconciliacaoTxt("operador", "inelegivel", { n: 123, janela: "2024", expR: 0.005 }) ===
    "Critérios ok · sem vantagem medida (n=123, 2024, +0,005R)");

ok('reconciliacaoTxt("estudo","inelegivel",...) frase educacional sem expR',
  reconciliacaoTxt("estudo", "inelegivel", { n: 123, janela: "2024", expR: 0.005 }) ===
    "O padrão bateu os critérios, mas em 123 ocorrências na janela 2024 não houve vantagem medida.");

{
  const neg = reconciliacaoTxt("operador", "elegivel", { n: 80, janela: "2025", expR: -0.099 });
  ok("expR negativo usa U+2212, não hífen", neg.includes("−0,099R") && !neg.includes("-0,099R"), neg);
}

// REVERSÃO DELIBERADA (2026-09-27, Fase 43, DP-3): ausência cai para
// nunca_medido, nunca "?" nem "0".
{
  const semN = reconciliacaoTxt("operador", "inelegivel", { n: null, janela: "2024", expR: 0.005 });
  ok("n null cai em nunca_medido do modo",
    semN === copyFor("operador").reconciliacaoElegibilidade.nunca_medido, semN);

  const semExpR = reconciliacaoTxt("operador", "elegivel", { n: 80, janela: "2025", expR: null });
  ok("expR null cai em nunca_medido do modo",
    semExpR === copyFor("operador").reconciliacaoElegibilidade.nunca_medido, semExpR);

  const semExpRInelegivel = reconciliacaoTxt("operador", "inelegivel", { n: 80, janela: "2025", expR: null });
  ok("expR null (inelegivel) cai em nunca_medido do modo",
    semExpRInelegivel === copyFor("operador").reconciliacaoElegibilidade.nunca_medido, semExpRInelegivel);

  const semJanela = reconciliacaoTxt("estudo", "inelegivel", { n: 80, janela: "", expR: 0.005 });
  ok("janela vazia no estudo cai em nunca_medido do modo",
    semJanela === copyFor("estudo").reconciliacaoElegibilidade.nunca_medido, semJanela);

  const nZero = reconciliacaoTxt("operador", "insuficiente", { n: 0, janela: "2025" });
  ok('n=0 é valor presente — continua "n=0" (não cai)', nZero.includes("n=0"), nZero);

  const expRZero = reconciliacaoTxt("operador", "elegivel", { n: 80, janela: "2025", expR: 0 });
  ok('expR 0 (número real) vira "+0,000R"', expRZero.includes("+0,000R"), expRZero);

  // varredura modo × estado × combinações de ausência — nunca "?" no retorno
  const combosAusencia = [
    { n: null, janela: "2024", expR: 0.005 },
    { n: 80, janela: "", expR: 0.005 },
    { n: 80, janela: "2024", expR: null },
    { n: null, janela: "", expR: null },
    { n: 0, janela: "2025", expR: 0 },
  ];
  for (const modo of ["estudo", "operador"]) {
    for (const estado of Object.keys(copyFor(modo).reconciliacaoElegibilidade)) {
      for (const vals of combosAusencia) {
        const t = reconciliacaoTxt(modo, estado, vals);
        ok(`reconciliacaoTxt(${modo},${estado},${JSON.stringify(vals)}) sem "?"`, !t.includes("?"), t);
      }
    }
  }
}

ok('modo "xyz" cai no fallback "estudo"',
  reconciliacaoTxt("xyz", "inelegivel", { n: 1, janela: "x", expR: 0 }) ===
    reconciliacaoTxt("estudo", "inelegivel", { n: 1, janela: "x", expR: 0 }));

{
  const nuncaMedidoEstudo = reconciliacaoTxt("estudo", "nunca_medido", {});
  ok('estado "xpto" cai em nunca_medido do modo',
    reconciliacaoTxt("estudo", "xpto", {}) === nuncaMedidoEstudo);
  ok("estado undefined cai em nunca_medido do modo",
    reconciliacaoTxt("estudo", undefined, {}) === nuncaMedidoEstudo);
}

// ---------------------------------------------------------------------------
// Templates crus em COPY — Estudo nunca interpola expR
// ---------------------------------------------------------------------------

for (const estado of Object.keys(COPY.estudo.reconciliacaoElegibilidade)) {
  ok(`COPY.estudo.reconciliacaoElegibilidade.${estado} não contém "{expR}"`,
    !COPY.estudo.reconciliacaoElegibilidade[estado].includes("{expR}"));
}
for (const estado of ["elegivel", "inelegivel"]) {
  const t = COPY.operador.reconciliacaoElegibilidade[estado];
  ok(`COPY.operador.reconciliacaoElegibilidade.${estado} contém {n}/{janela}/{expR}`,
    t.includes("{n}") && t.includes("{janela}") && t.includes("{expR}"));
}
for (const modo of ["estudo", "operador"]) {
  ok(`COPY.${modo}.reconciliacaoElegibilidade.insuficiente contém {n}`,
    COPY[modo].reconciliacaoElegibilidade.insuficiente.includes("{n}"));
}

// ---------------------------------------------------------------------------
// reconciliacaoPorQueImporta — igual ao valor Python
// ---------------------------------------------------------------------------

const caminhoSkillRef = process.env.B3_SKILL_REF_PATH
  ? process.env.B3_SKILL_REF_PATH
  : fileURLToPath(new URL("../../server/app/skill_ref.py", import.meta.url));
const skillRefSrc = readFileSync(caminhoSkillRef, "utf8");
const mPy = skillRefSrc.match(/^RECONCILIACAO_POR_QUE_IMPORTA = "([^"]*)"/m);
ok("RECONCILIACAO_POR_QUE_IMPORTA encontrado em skill_ref.py", !!mPy);
ok('reconciliacaoPorQueImporta === "sinal técnico e histórico medido são coisas diferentes"',
  reconciliacaoPorQueImporta === "sinal técnico e histórico medido são coisas diferentes");
if (mPy) {
  ok("reconciliacaoPorQueImporta (js) igual ao valor Python", reconciliacaoPorQueImporta === mPy[1],
    `js="${reconciliacaoPorQueImporta}" python="${mPy[1]}"`);
}

// ---------------------------------------------------------------------------
// sinal.leituraIa — rótulos da "Leitura da IA" (CHIP-03), idênticos nos dois modos
// ---------------------------------------------------------------------------

ok('COPY.estudo.sinal.leituraIa.rotulo === "LEITURA DA IA"',
  COPY.estudo.sinal.leituraIa.rotulo === "LEITURA DA IA");
ok('COPY.operador.sinal.leituraIa.rotulo === "LEITURA DA IA"',
  COPY.operador.sinal.leituraIa.rotulo === "LEITURA DA IA");

for (const modo of ["estudo", "operador"]) {
  const campos = COPY[modo].sinal.leituraIa.campos;
  ok(`COPY.${modo}.sinal.leituraIa.campos = {DIREÇÃO, CONVICÇÃO, QUALIDADE}`,
    campos.direcao === "DIREÇÃO" && campos.conviccao === "CONVICÇÃO" && campos.qualidade === "QUALIDADE");

  const aria = COPY[modo].sinal.leituraIa.aria;
  ok(`COPY.${modo}.sinal.leituraIa.aria("direcao","Alta")`,
    aria("direcao", "Alta") === "Direção da leitura da IA: Alta");
  ok(`COPY.${modo}.sinal.leituraIa.aria("conviccao","Alto")`,
    aria("conviccao", "Alto") === "Convicção da leitura da IA: Alto");
  ok(`COPY.${modo}.sinal.leituraIa.aria("qualidade","Boa")`,
    aria("qualidade", "Boa") === "Qualidade da leitura da IA: Boa");
}

// ---------------------------------------------------------------------------
// Parte B — fiação no App.jsx (43-04, D-07/D-09/D-10/D-11/D-12)
//
// A Parte A (acima) só cobre o helper puro de copy.js. Esta parte lê App.jsx
// como TEXTO (sem build, sem DOM) — mesmo padrão de test_sinal_chip_ui.mjs/
// test_historico_ui.mjs — para confirmar que HistoricoPill/AtivoCard de fato
// consomem reconciliacaoTxt/reconciliacaoPorQueImporta, e que nenhuma string
// da frase é literal no componente (SC#1).
// ---------------------------------------------------------------------------

const appSrc = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(appSrc);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < appSrc.length; i++) {
    if (appSrc[i] === "{") depth++;
    else if (appSrc[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return appSrc.slice(m.index, i);
}
function semComentarios(body) {
  return (body || "").split("\n").filter((l) => !/^\s*\/\//.test(l.trim())).join("\n");
}

// ---- import ----------------------------------------------------------------
ok("App.jsx importa reconciliacaoTxt e reconciliacaoPorQueImporta de \"./copy.js\"",
  /import \{[^}]*reconciliacaoTxt[^}]*reconciliacaoPorQueImporta[^}]*\}\s*from\s*"\.\/copy\.js"/.test(appSrc)
  || /import \{[^}]*reconciliacaoPorQueImporta[^}]*reconciliacaoTxt[^}]*\}\s*from\s*"\.\/copy\.js"/.test(appSrc));

// ---- corpo de HistoricoPill --------------------------------------------------
const corpoHistoricoPill = functionBody("HistoricoPill") || "";
ok("corpo de HistoricoPill encontrado (não vazio)", corpoHistoricoPill.length > 200);

ok("assinatura de HistoricoPill inclui microtexto, A, didatica, dados",
  /function HistoricoPill\(\{[^}]*microtexto[^}]*A[^}]*didatica[^}]*dados[^}]*\}\)/.test(appSrc));

const semComentariosHistoricoPill = semComentarios(corpoHistoricoPill);

ok('corpo de HistoricoPill contém reconciliacaoTxt(modoJS, estado, { n: nJanela, janela: janelaRef, expR: expRJanela })',
  semComentariosHistoricoPill.includes("reconciliacaoTxt(modoJS, estado, { n: nJanela, janela: janelaRef, expR: expRJanela })"));

ok('gate "!microtexto && !compacto &&" no bloco de números',
  semComentariosHistoricoPill.includes("!microtexto && !compacto &&"));

ok('gate "!operador &&" antes de setorId="analise"', (() => {
  const idxOperadorGate = semComentariosHistoricoPill.indexOf("!operador &&");
  const idxSetorAnalise = semComentariosHistoricoPill.indexOf('setorId="analise"');
  return idxOperadorGate > 0 && idxSetorAnalise > idxOperadorGate;
})());

ok("{reconciliacaoPorQueImporta} dentro do SetorAlvo (corpo de HistoricoPill)",
  semComentariosHistoricoPill.includes("{reconciliacaoPorQueImporta}"));

ok("SUBLINHADO usado no corpo de HistoricoPill",
  semComentariosHistoricoPill.includes("SUBLINHADO"));

ok("ariaLabel ainda vem de historicoTxt( no corpo de HistoricoPill",
  /ariaLabel\s*=\s*historicoTxt\(/.test(semComentariosHistoricoPill));

ok('o "⏱" continua depois do trecho da frase (índice de ⏱ > índice de reconciliacaoTxt)', (() => {
  const idxFato = corpoHistoricoPill.indexOf("reconciliacaoTxt(modoJS, estado,");
  const idxRelogio = corpoHistoricoPill.indexOf("⏱");
  return idxFato > 0 && idxRelogio > idxFato;
})());

// ---- call sites de HistoricoPill --------------------------------------------
const callSitesComMicrotexto = (appSrc.match(/<HistoricoPill[^>]*\bmicrotexto\b[^>]*\/>/g) || []);
ok("exatamente 1 call site de <HistoricoPill contém microtexto",
  callSitesComMicrotexto.length === 1, `encontrados: ${callSitesComMicrotexto.length}`);

ok("o call site com microtexto está no corpo de AtivoCard, com A={A} didatica={didatica} dados={dadosDoCard}", (() => {
  if (callSitesComMicrotexto.length !== 1) return false;
  const call = callSitesComMicrotexto[0];
  const corpoAtivoCard = functionBody("AtivoCard") || "";
  return corpoAtivoCard.includes(call)
    && call.includes("A={A}") && call.includes("didatica={didatica}") && call.includes("dados={dadosDoCard}");
})());

ok('call site `<HistoricoPill historico={s.historico}` NÃO contém microtexto', (() => {
  const re = /<HistoricoPill historico=\{s\.historico\}[^>]*\/>/;
  const m = re.exec(appSrc);
  return !!m && !m[0].includes("microtexto");
})());

// ---- nenhuma string literal da frase no componente (SC#1) -------------------
ok('App.jsx não contém literalmente o texto de reconciliacaoPorQueImporta',
  !appSrc.includes("sinal técnico e histórico medido são coisas diferentes"));
ok('App.jsx não contém literalmente "Critérios ok"', !appSrc.includes("Critérios ok"));
ok('App.jsx não contém literalmente "O padrão bateu os critérios"', !appSrc.includes("O padrão bateu os critérios"));

// ---- cor do span da frase — nunca T.positive/T.negative/T.warn/T.accent ----
ok('span da frase de microtexto não usa T.positive/T.negative/T.warn/T.accent (cor em T.textSecondary)', (() => {
  // recorte: do início de "{microtexto && fato && (" até o fechamento do bloco
  // condicional correspondente, dentro do corpo de HistoricoPill.
  const idxInicio = corpoHistoricoPill.indexOf("{microtexto && fato && (");
  if (idxInicio < 0) return false;
  let depth = 0, i = idxInicio, achouAbertura = false;
  for (; i < corpoHistoricoPill.length; i++) {
    const c = corpoHistoricoPill[i];
    if (c === "(") { depth++; achouAbertura = true; }
    else if (c === ")") { depth--; if (achouAbertura && depth === 0) { i++; break; } }
  }
  const bloco = corpoHistoricoPill.slice(idxInicio, i);
  return bloco.includes("T.textSecondary")
    && !/T\.(positive|negative|warn|accent)\b/.test(bloco);
})());

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
