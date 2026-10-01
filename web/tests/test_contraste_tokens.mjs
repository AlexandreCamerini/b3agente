// Guardião AA dos tokens de cor (2026-10-01, opção C de identidade de modo).
//
// Por que existe: a opção C deu aos 4 esquemas (Estudo/Operador x escuro/claro)
// neutros com matiz própria (azul no Estudo, âmbar no Operador). Trocar fundo
// muda o contraste de TODO token de texto. O guardião antigo
// (test_brand_book_v2_tokens) media só alguns tokens contra o card, e essa
// omissão de superfície foi a origem do FIX-C16. Este mede TODOS os tokens de
// texto contra as TRÊS superfícies (bgBase, bgPanel, bgCard) nos 4 esquemas,
// mais onAccent sobre accent e os textos coloridos sobre seus tints compostos
// (alpha blend sobre bgCard).
// Roda sem build: `node web/tests/test_contraste_tokens.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function objectBody(decl) {
  const i = src.indexOf(decl);
  if (i < 0) return null;
  let depth = 0, start = src.indexOf("{", i), j = start;
  for (; j < src.length; j++) {
    if (src[j] === "{") depth++;
    else if (src[j] === "}") { depth--; if (depth === 0) break; }
  }
  return src.slice(start, j + 1);
}
function scheme(block, name, BRAND) {
  const i = block.indexOf(name + ": {");
  if (i < 0) return {};
  let depth = 0, start = block.indexOf("{", i), j = start;
  for (; j < block.length; j++) {
    if (block[j] === "{") depth++;
    else if (block[j] === "}") { depth--; if (depth === 0) break; }
  }
  // remove comentários de linha para não casar hex dentro de prosa
  const body = block.slice(start, j + 1).replace(/\/\/[^\n]*/g, "");
  const out = {};
  for (const m of body.matchAll(/(\w+):\s*"(#[0-9a-fA-F]{6})"/g)) out[m[1]] = m[2].toLowerCase();
  for (const m of body.matchAll(/(\w+):\s*"(rgba\([^)]+\))"/g)) out[m[1]] = m[2];
  for (const m of body.matchAll(/(\w+):\s*BRAND\.(\w+)/g)) out[m[1]] = BRAND[m[2]];
  return out;
}
const brandBlock = objectBody("const BRAND = ");
const BRAND = {};
for (const m of brandBlock.matchAll(/(\w+):\s*"(#[0-9a-fA-F]{6})"/g)) BRAND[m[1]] = m[2].toLowerCase();

const paletteBlock = objectBody("const PALETTE = ");
const modeBlock = objectBody("const MODE_OPERADOR = ");
const estudo = { dark: scheme(paletteBlock, "dark", BRAND), light: scheme(paletteBlock, "light", BRAND) };
const ovr = { dark: scheme(modeBlock, "dark", BRAND), light: scheme(modeBlock, "light", BRAND) };
const operador = { dark: { ...estudo.dark, ...ovr.dark }, light: { ...estudo.light, ...ovr.light } };

const lin = (x) => (x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4));
function luminance(hex) {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => lin(parseInt(h.slice(i, i + 2), 16) / 255));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contrast(a, b) {
  const [x, y] = [luminance(a), luminance(b)];
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}
// compõe rgba(r,g,b,a) sobre um hex opaco -> hex
function blend(rgba, bgHex) {
  const m = rgba.match(/rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)/);
  if (!m) return null;
  const [r, g, b] = [m[1], m[2], m[3]].map(Number), a = Number(m[4]);
  const h = bgHex.replace("#", "");
  const bg = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  const mix = [r, g, b].map((c, i) => Math.round(c * a + bg[i] * (1 - a)));
  return "#" + mix.map((c) => c.toString(16).padStart(2, "0")).join("");
}

const ESQUEMAS = [
  ["Estudo/dark", estudo.dark], ["Estudo/light", estudo.light],
  ["Operador/dark", operador.dark], ["Operador/light", operador.light],
];
const TEXTOS = ["textPrimary", "textSecondary", "textMuted", "textDim", "textFaint", "accent", "accentSoft", "positive", "negative", "warn"];
const SUPERFICIES = ["bgBase", "bgPanel", "bgCard"];

// 1. cada token de texto x 3 superfícies x 4 esquemas
for (const [nome, p] of ESQUEMAS) {
  for (const t of TEXTOS) for (const s of SUPERFICIES) {
    const r = p[t] && p[s] ? contrast(p[t], p[s]) : 0;
    ok(`${nome}: ${t} ${p[t]} sobre ${s} ${p[s]} = ${r.toFixed(2)}:1 (AA 4.5)`, r >= 4.5);
  }
}
// 2. onAccent sobre accent
for (const [nome, p] of ESQUEMAS) {
  const r = p.onAccent && p.accent ? contrast(p.onAccent, p.accent) : 0;
  ok(`${nome}: onAccent ${p.onAccent} sobre accent ${p.accent} = ${r.toFixed(2)}:1 (AA 4.5)`, r >= 4.5);
}
// 3. texto colorido sobre o tint composto sobre bgCard
for (const [nome, p] of ESQUEMAS) {
  for (const [tx, tint] of [["accent", "accentTint10"], ["positive", "positiveTint10"], ["negative", "negativeTint10"], ["warn", "warnTint10"]]) {
    const fundo = p[tint] && p.bgCard ? blend(p[tint], p.bgCard) : null;
    const r = fundo && p[tx] ? contrast(p[tx], fundo) : 0;
    ok(`${nome}: ${tx} ${p[tx]} sobre ${tint} composto ${fundo} = ${r.toFixed(2)}:1 (AA 4.5)`, r >= 4.5);
  }
}
// 4. neutros aprovados (opção C, protótipo Modos.dc.html), literais
const NEUTROS = {
  "Estudo/dark": { bgBase: "#0c1424", bgCard: "#15203a", borderSubtle: "#26345a", borderFaint: "#1c2845" },
  "Operador/dark": { bgBase: "#12100b", bgCard: "#1e1a12", borderSubtle: "#3a3322", borderFaint: "#2a2418" },
  "Estudo/light": { bgBase: "#eaf1fc", bgCard: "#ffffff", borderSubtle: "#cfdbf0", borderFaint: "#dde7f6" },
  "Operador/light": { bgBase: "#f5efe0", bgCard: "#fffcf4", borderSubtle: "#e3d8b8", borderFaint: "#ede4c8" },
};
const porNome = Object.fromEntries(ESQUEMAS);
for (const [nome, tab] of Object.entries(NEUTROS)) for (const [k, v] of Object.entries(tab)) {
  ok(`${nome}: neutro ${k} = ${v}`, porNome[nome][k] === v);
}
// 5. acentos/sinais do claro (valores aprovados; ajuste forçado por medição só se registrado no SUMMARY)
ok("Estudo/light: accent #1c746d", estudo.light.accent === "#1c746d");
ok("Operador/light: accent #7f6318", operador.light.accent === "#7f6318");
ok("claro: positive #197a56", estudo.light.positive === "#197a56" && operador.light.positive === "#197a56");
ok("claro: negative #b83a41", estudo.light.negative === "#b83a41" && operador.light.negative === "#b83a41");
// 6. painel do claro fica ENTRE base e card (não mais escuro que a base)
for (const nome of ["Estudo/light", "Operador/light"]) {
  const p = porNome[nome];
  const L = (h) => luminance(h);
  ok(`${nome}: bgPanel entre bgBase e bgCard`, L(p.bgPanel) > L(p.bgBase) && L(p.bgPanel) < L(p.bgCard));
}

console.log(fails ? `\n${fails} verificação(ões) falharam` : "\ntodas as verificações passaram");
process.exit(fails ? 1 : 0);
