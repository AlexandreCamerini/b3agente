// Fase 45 (plano 45-04, UI-SPEC §Contraste AA) — 7 pares de texto do card de
// Posição estruturada x 4 combinações tema x modo. Helpers copiados de
// test_cor_confiabilidade.mjs. Roda sem build.
// Informativo (não assertado): dívida AA do legado, negative sobre negativeTint10.
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


// Tema escuro declara positive/negative como `BRAND.x` (não literal): resolve pelo objeto BRAND.
const brandBlock = objectBody("const BRAND = ", appSrc) || "";
const brand = {};
for (const m of brandBlock.matchAll(/(\w+):\s*"(#[0-9a-fA-F]{6})"/g)) brand[m[1]] = m[2].toLowerCase();
for (const cores of Object.values(combos)) {
  for (const k of ["positive", "negative"]) {
    if (!cores[k]) {
      const ref = new RegExp(`${k}:\\s*BRAND\\.(\\w+)`).exec(paletteBlock);
      if (ref && brand[ref[1]]) cores[k] = brand[ref[1]];
    }
  }
}
ok("BRAND resolvido para positive/negative do escuro", !!combos["dark · estudo"].positive && !!combos["dark · estudo"].negative);

const bg = (cores, chave) => (chave === "bgCard" ? cores.bgCard : cores.bgBase);
const pares = [
  ["textSecondary", "bgCard"],
  ["textMuted", "bgCard"],
  ["textMuted", "bgBase"],
  ["textFaint", "bgCard"],
  ["warn", "warnTint10@bgCard"],
  ["positive", "bgCard"],
  ["negative", "bgCard"],
];
for (const [nome, cores] of Object.entries(combos)) {
  const tema = nome.startsWith("dark") ? "dark" : "light";
  for (const [fg, fundo] of pares) {
    const fgHex = cores[fg];
    let lumBg;
    if (fundo.includes("@")) {
      const tint = cores.warnTint10 || estudo[tema].warnTint10;
      lumBg = luminanceRGB(blend(tint, cores.bgCard));
    } else {
      lumBg = luminanceRGB(hexToRgb(bg(cores, fundo)));
    }
    const ok1 = !!fgHex && /^#/.test(fgHex);
    const r = ok1 ? contrast(luminanceRGB(hexToRgb(fgHex)), lumBg) : 0;
    ok(`${nome}: ${fg}/${fundo} = ${r.toFixed(2)} >= 4.5`, r >= 4.5);
  }
  // informativo: legado
  const tintN = cores.negativeTint10 || estudo[tema].negativeTint10;
  if (tintN && cores.negative) {
    const rl = contrast(luminanceRGB(hexToRgb(cores.negative)), luminanceRGB(blend(tintN, cores.bgCard)));
    console.log(`info ${nome}: negative/negativeTint10@bgCard (legado) = ${rl.toFixed(2)}`);
  }
}

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\nOK");
