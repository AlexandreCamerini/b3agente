// Fase 43 (CHIP-03 premissa corrigida, D-01..D-05; fold-in D-17) — guardião
// da "Leitura da IA": os 3 SinalChip contexto neutros (direção/convicção/
// qualidade) voltam a existir dentro de AnalysisView, NUNCA no card do
// ativo; KpiBlock/KpiCell e o que era órfão só deles (DIR_STYLE/SCALE_STYLE/
// REC_PRO_MAP/recDoModo) saem por inteiro; FundamentoTabela perde o
// "FUNDAMENTO" duplicado (D-17). Lê App.jsx/copy.js como TEXTO (sem build,
// sem DOM), mesmo padrão de test_sinal_chip_ui.mjs.
// Roda sem build: `node web/tests/test_leitura_ia_chips.mjs`.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { copyFor } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Corpo de função top-level (mesma convenção dos demais guardiões).
function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(src);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(m.index, i);
}

// Corpo sem linhas de comentário (// ...) — evita falso-positivo de token
// citado em prosa explicativa.
function semComentarios(body) {
  return (body || "").split("\n").filter((l) => !/^\s*\/\//.test(l.trim())).join("\n");
}

const srcSemComentarios = semComentarios(src);

// ---------------------------------------------------------------------------
// KpiBlock/KpiCell e órfãos apagados (D-05)
// ---------------------------------------------------------------------------
ok("nenhum `function KpiBlock(` sobrevive em App.jsx", !/function KpiBlock\(/.test(src));
ok("nenhum `function KpiCell(` sobrevive em App.jsx", !/function KpiCell\(/.test(src));
ok("nenhum `<KpiBlock` sobrevive em App.jsx", !/<KpiBlock/.test(src));
ok("nenhum `<KpiCell` sobrevive em App.jsx", !/<KpiCell/.test(src));
ok("DIR_STYLE/SCALE_STYLE/recDoModo/REC_PRO_MAP não existem mais em App.jsx (inclusive comentários)",
  !/DIR_STYLE/.test(src) && !/SCALE_STYLE/.test(src) && !/recDoModo/.test(src) && !/REC_PRO_MAP/.test(src));

// ---------------------------------------------------------------------------
// Recorte de AnalysisView (mesma técnica de test_fonte_explicacao.mjs)
// ---------------------------------------------------------------------------
const iAnalysisView = src.indexOf("function AnalysisView(");
const iAnalysisViewEnd = src.indexOf("\nfunction hasAnalysis(", iAnalysisView);
const analysisView = iAnalysisView >= 0 && iAnalysisViewEnd > iAnalysisView ? src.slice(iAnalysisView, iAnalysisViewEnd) : "";
ok("AnalysisView localizado", analysisView.length > 0);
const avSemComentarios = semComentarios(analysisView);

ok("AnalysisView recebe { an, operador }", /function AnalysisView\(\{ an, operador \}\)/.test(analysisView));
ok("AnalysisView contém `an.kpis &&`", analysisView.includes("an.kpis &&"));
ok("AnalysisView usa `leituraIa`", analysisView.includes("leituraIa"));

const idxKpis = analysisView.indexOf("an.kpis &&");
const idxFatos = analysisView.indexOf("Array.isArray(d.fatos)");
ok("bloco Leitura da IA vem DEPOIS de <Markdown e ANTES de Array.isArray(d.fatos)",
  idxKpis >= 0 && idxFatos > idxKpis && analysisView.indexOf("<Markdown") < idxKpis);

const blocoLeituraIa = (idxKpis >= 0 && idxFatos > idxKpis) ? analysisView.slice(idxKpis, idxFatos) : "";
const blocoSemComentarios = semComentarios(blocoLeituraIa);

ok("bloco Leitura da IA tem exatamente 3 `<SinalChip peso=\"contexto\"`",
  (blocoSemComentarios.match(/<SinalChip peso="contexto"/g) || []).length === 3);
ok("bloco Leitura da IA não usa prop `estado=` em nenhum dos 3 chips",
  !/<SinalChip peso="contexto"[^>]*estado=/.test(blocoSemComentarios));
ok("bloco Leitura da IA não usa kpis.recomendacao (D-03)",
  !blocoSemComentarios.includes("kpis.recomendacao"));
ok("bloco Leitura da IA não usa T.positive/T.negative/T.accent/T.warn (D-02, neutro)",
  !/T\.(positive|negative|accent|warn)/.test(blocoSemComentarios));
ok("↗ dentro de elemento aria-hidden=\"true\"", /aria-hidden="true"[^>]*>[\s\S]{0,80}↗/.test(blocoSemComentarios));
ok("↘ dentro de elemento aria-hidden=\"true\"", /aria-hidden="true"[^>]*>[\s\S]{0,80}↘/.test(blocoSemComentarios));

ok("call site é `<AnalysisView an={an} operador={operador} />`",
  /<AnalysisView an=\{an\} operador=\{operador\} \/>/.test(src));

// ---------------------------------------------------------------------------
// AtivoCard sem kpis.* (D-02 da Fase 42)
// ---------------------------------------------------------------------------
function functionBodyAtivoCard() { return functionBody("AtivoCard") || ""; }
const ativoCardSemComentarios = semComentarios(functionBodyAtivoCard());
ok("AtivoCard não contém kpis.direcao/conviccao/qualidade (D-02 da 42)",
  !/kpis\.direcao/.test(ativoCardSemComentarios) &&
  !/kpis\.conviccao/.test(ativoCardSemComentarios) &&
  !/kpis\.qualidade/.test(ativoCardSemComentarios));

// ---------------------------------------------------------------------------
// FundamentoTabela — D-17 (rótulo saiu, cabeçalho fica)
// ---------------------------------------------------------------------------
const fundamentoTabela = functionBody("FundamentoTabela") || "";
ok("FundamentoTabela: `<SinalChip peso=\"contexto\" value={f.score}` presente",
  fundamentoTabela.includes('<SinalChip peso="contexto" value={f.score}'));
ok("FundamentoTabela: `label=\"FUNDAMENTO\"` ausente do corpo (D-17)",
  !semComentarios(fundamentoTabela).includes('label="FUNDAMENTO"'));
ok("FundamentoTabela: `>FUNDAMENTO<` (cabeçalho) presente exatamente 1 vez",
  (semComentarios(fundamentoTabela).match(/>FUNDAMENTO</g) || []).length === 1);

// ---------------------------------------------------------------------------
// copy.js — rótulo comum aos 2 modos
// ---------------------------------------------------------------------------
ok('copyFor("estudo").sinal.leituraIa.rotulo === copyFor("operador").sinal.leituraIa.rotulo === "LEITURA DA IA"',
  copyFor("estudo").sinal.leituraIa.rotulo === "LEITURA DA IA" &&
  copyFor("operador").sinal.leituraIa.rotulo === "LEITURA DA IA");

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
