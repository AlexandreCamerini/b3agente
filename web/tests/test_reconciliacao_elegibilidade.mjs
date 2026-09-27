// Fase 43 (HIER-03, D-07/D-08/D-11/D-12/D-13) — Parte A: helper puro de
// copy.js (reconciliacaoTxt/reconciliacaoPorQueImporta) e os rótulos da
// "Leitura da IA" (CHIP-03, sinal.leituraIa). A Parte B (fiação no
// App.jsx/HistoricoPill/AnalysisView) entra no 43-04 — este guardião não lê
// App.jsx.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { COPY, reconciliacaoTxt, reconciliacaoPorQueImporta } from "../src/copy.js";

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

{
  const semN = reconciliacaoTxt("operador", "inelegivel", { n: null, janela: "2024", expR: 0.005 });
  ok('n null vira "n=?" (nunca "n=0")', semN.includes("n=?") && !semN.includes("n=0"), semN);

  const semExpR = reconciliacaoTxt("operador", "elegivel", { n: 80, janela: "2025", expR: null });
  ok('expR null termina em ", ?)"', semExpR.endsWith(", ?)"), semExpR);

  const expRZero = reconciliacaoTxt("operador", "elegivel", { n: 80, janela: "2025", expR: 0 });
  ok('expR 0 (número real) vira "+0,000R"', expRZero.includes("+0,000R"), expRZero);
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

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
