// Fase 42 (COR-01; D-03/D-04/D-05) — guardião do canal de confiabilidade.
// 4 combinações tema×modo (não 8: PALETTE tem 2 temas e MODE_OPERADOR 2
// overrides — correção factual do 42-CONTEXT).
//
// Cobre: (1) contraste WCAG do par texto T.warn × tint T.warnTint10 blendado
// sobre bgCard, nas 4 combinações efetivas tema×modo; (2) ban list de cor —
// HISTORICO_PILL_STYLE sem T.positive/T.negative (ROADMAP SC#1); (3) arco do
// ConfluenceRing sem P.positive/P.negative/P.accent, dependendo de
// TIER_FILL/tierOf; (4) TIER_FILL/tierOf inalterados (4 hex + 4 rótulos).
//
// Roda sem build: `node web/tests/test_cor_confiabilidade.mjs`.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const appSrc = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- helpers de extração (texto do fonte, sem build) ----------------------
function objectBody(decl, src) {
  const i = src.indexOf(decl);
  if (i < 0) return null;
  let depth = 0, start = src.indexOf("{", i), j = start;
  for (; j < src.length; j++) {
    if (src[j] === "{") depth++;
    else if (src[j] === "}") { depth--; if (depth === 0) break; }
  }
  return src.slice(start, j + 1);
}
function scheme(block, name) {
  if (!block) return {};
  const i = block.indexOf(name + ": {");
  if (i < 0) return {};
  let depth = 0, start = block.indexOf("{", i), j = start;
  for (; j < block.length; j++) {
    if (block[j] === "{") depth++;
    else if (block[j] === "}") { depth--; if (depth === 0) break; }
  }
  const body = block.slice(start, j + 1);
  const out = {};
  for (const m of body.matchAll(/(\w+):\s*"(#[0-9a-fA-F]{6})"/g)) out[m[1]] = m[2].toLowerCase();
  for (const m of body.matchAll(/(\w+):\s*"(rgba\([^)]+\))"/g)) out[m[1]] = m[2];
  return out;
}

const paletteBlock = objectBody("const PALETTE = ", appSrc);
const modeBlock = objectBody("const MODE_OPERADOR = ", appSrc);
const estudo = { dark: scheme(paletteBlock, "dark"), light: scheme(paletteBlock, "light") };
const operadorOverride = { dark: scheme(modeBlock, "dark"), light: scheme(modeBlock, "light") };
// Combinações efetivas: Operador = spread do tema base + override do modo
// (mesma composição de usePalette em runtime).
const combos = {
  "dark · estudo": estudo.dark,
  "dark · operador": { ...estudo.dark, ...operadorOverride.dark },
  "light · estudo": estudo.light,
  "light · operador": { ...estudo.light, ...operadorOverride.light },
};

ok("PALETTE.dark declara warnTint10", !!estudo.dark.warnTint10);
ok("PALETTE.light declara warnTint10", !!estudo.light.warnTint10);

// ---- contraste WCAG --------------------------------------------------------
const lin = (x) => (x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4));
function luminanceRGB([r, g, b]) {
  const [lr, lg, lb] = [r, g, b].map((v) => lin(v / 255));
  return 0.2126 * lr + 0.7152 * lg + 0.0722 * lb;
}
function hexToRgb(hex) {
  const h = hex.replace("#", "");
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
}
function parseRgba(str) {
  const m = /rgba?\(([^)]+)\)/.exec(str);
  const parts = m[1].split(",").map((s) => parseFloat(s.trim()));
  return { r: parts[0], g: parts[1], b: parts[2], a: parts.length > 3 ? parts[3] : 1 };
}
// blend do tint (rgba) sobre um fundo sólido (hex), alpha compositing simples.
function blend(tintRgba, bgHex) {
  const { r, g, b, a } = parseRgba(tintRgba);
  const [br, bg2, bb] = hexToRgb(bgHex);
  return [r * a + br * (1 - a), g * a + bg2 * (1 - a), b * a + bb * (1 - a)];
}
function contrast(lumA, lumB) {
  return (Math.max(lumA, lumB) + 0.05) / (Math.min(lumA, lumB) + 0.05);
}

// ---- 1) contraste do par T.warn (texto) × T.warnTint10 blendado sobre
//         bgCard, nas 4 combinações efetivas -------------------------------
for (const [nome, cores] of Object.entries(combos)) {
  const warn = cores.warn;
  const warnTint10 = cores.warnTint10 || estudo[nome.startsWith("dark") ? "dark" : "light"].warnTint10;
  const bgCard = cores.bgCard;
  ok(`combinação ${nome} tem warn/warnTint10/bgCard resolvidos`, !!warn && !!warnTint10 && !!bgCard);
  if (!warn || !warnTint10 || !bgCard) continue;
  const blended = blend(warnTint10, bgCard);
  const lumBlend = luminanceRGB(blended);
  const lumWarn = luminanceRGB(hexToRgb(warn));
  const razao = contrast(lumWarn, lumBlend);
  ok(`${nome}: T.warn × T.warnTint10 sobre bgCard = ${razao.toFixed(2)}:1 (AA ≥ 4,5)`, razao >= 4.5);
}

// ---- 2) ban list: HISTORICO_PILL_STYLE sem T.positive/T.negative (SC#1) --
const iniStyle = appSrc.indexOf("const HISTORICO_PILL_STYLE");
const fimStyle = appSrc.indexOf("};", iniStyle);
const objStyle = (iniStyle >= 0 && fimStyle > iniStyle) ? appSrc.slice(iniStyle, fimStyle + 2) : "";
ok("recorte de HISTORICO_PILL_STYLE não veio vazio", objStyle.length > 50);
const objStyleSemComentario = objStyle.split("\n").filter((l) => !l.trim().startsWith("//")).join("\n");
ok("HISTORICO_PILL_STYLE não referencia T.positive nem T.negative (ROADMAP SC#1)",
  !objStyleSemComentario.includes("T.positive") && !objStyleSemComentario.includes("T.negative"));

// ---- 3) ConfluenceRing: arco depende de TIER_FILL/tierOf, nunca de
//         P.positive/P.negative/P.accent -----------------------------------
const iniRing = appSrc.indexOf("function ConfluenceRing");
const fimRingNl = appSrc.indexOf("\n}", iniRing);
const ringBloco = (iniRing >= 0 && fimRingNl > iniRing) ? appSrc.slice(iniRing, fimRingNl + 2) : "";
ok("recorte de ConfluenceRing não veio vazio", ringBloco.length > 100);
ok("ConfluenceRing usa TIER_FILL[tierOf(", ringBloco.includes("TIER_FILL[tierOf("));
ok("ConfluenceRing não usa P.positive/P.negative/P.accent no arco",
  !ringBloco.includes("P.positive") && !ringBloco.includes("P.negative") && !ringBloco.includes("P.accent"));

// ---- 4) TIER_FILL/tierOf inalterados (4 hex + 4 rótulos) ------------------
const iniTierFill = appSrc.indexOf("const TIER_FILL");
const fimTierFill = appSrc.indexOf("};", iniTierFill);
const tierFillBloco = (iniTierFill >= 0 && fimTierFill > iniTierFill) ? appSrc.slice(iniTierFill, fimTierFill + 2) : "";
for (const hex of ["#22c55e", "#f59e0b", "#9ca3af", "#ef4444"]) {
  ok(`TIER_FILL contém ${hex}`, tierFillBloco.includes(hex));
}
const iniTierOf = appSrc.indexOf("function tierOf");
const fimTierOfNl = appSrc.indexOf("\n}", iniTierOf);
const tierOfBloco = (iniTierOf >= 0 && fimTierOfNl > iniTierOf) ? appSrc.slice(iniTierOf, fimTierOfNl + 2) : "";
for (const rotulo of ["forte", "Forte", "moderada", "Moderada", "neutra", "Neutra", "fraca", "Fraca"]) {
  ok(`tierOf devolve o rótulo "${rotulo}"`, tierOfBloco.includes(rotulo));
}

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
