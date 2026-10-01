// Fase 45 (plano 45-04, UI-SPEC §Contraste AA) — 7 pares de texto do card de
// Posição estruturada x 4 combinações tema x modo. Helpers copiados de
// test_cor_confiabilidade.mjs. Roda sem build.
// Fase 46 (D-17, UI-SPEC Contraste, 2026-09-30): pares do card v6 (46-08).
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

// 2026-10-01 (revert 261001-0or + design v6): o card v6 NÃO lê mais os neutros
// globais (PALETTE/MODE_OPERADOR) — lê as cores escopadas de
// src/cartaoV6Cores.js (escuro = paleta literal do design v6; claro = derivado),
// aplicadas como CSS vars no wrapper do card. As asserções abaixo medem essas
// cores nas 4 combinações. As asserções originais (7 pares da 45 + gráficos da
// 46-08) seguem, agora sobre as cores efetivas do card; a dívida legada do
// PALETTE global (revertida pelo Alex) deixa de ser medida aqui.
import { coresCartaoV6, ALFA_ZONA_V6, ALFA_ZONA_MEIO_V6, varsCartaoV6 } from "../src/cartaoV6Cores.js";
ok("App.jsx aplica varsCartaoV6 no wrapper do card (escopo; sem tocar T global)", /\.\.\.varsCartaoV6\(themeKey, operador \? "operador" : "estudo"\)/.test(appSrc));

const COMBOS = [["dark", "estudo"], ["dark", "operador"], ["light", "estudo"], ["light", "operador"]];
const cartao = {};
for (const [t, m] of COMBOS) cartao[`${t} · ${m}`] = coresCartaoV6(t, m);

const bgOf = (c, k) => ({ bgCard: c.bgCard, bgBase: c.bgBase, knob: c.knob, accent: c.accent, accSurf: c.accentTint10, warnTint: c.warnTint10 }[k]);
// [rotulo, fg(cores)->hex, fundo, mínimo]
const T45 = 4.5;
const paresTexto = [
  ["textPrimary/bgCard", (c) => c.textPrimary, "bgCard"],
  ["textPrimary/bgBase", (c) => c.textPrimary, "bgBase"],
  ["textSecondary/bgCard", (c) => c.textSecondary, "bgCard"],
  ["textSecondary/bgBase", (c) => c.textSecondary, "bgBase"],
  ["textMuted/bgCard", (c) => c.textMuted, "bgCard"],
  ["textMuted/bgBase", (c) => c.textMuted, "bgBase"],
  ["accent/bgCard", (c) => c.accent, "bgCard"],
  ["accent/bgBase", (c) => c.accent, "bgBase"],
  ["accent/accSurf", (c) => c.accent, "accSurf"],
  ["textPrimary/accSurf", (c) => c.textPrimary, "accSurf"],
  ["onAccent(accInk)/accent", (c) => c.onAccent, "accent"],
  ["positive/bgCard", (c) => c.positive, "bgCard"],
  ["positive/bgBase", (c) => c.positive, "bgBase"],
  ["negative/bgCard", (c) => c.negative, "bgCard"],
  ["negative/bgBase", (c) => c.negative, "bgBase"],
  ["warn/warnTint(bg status)", (c) => c.warn, "warnTint"],
  ["warn/bgCard", (c) => c.warn, "bgCard"],
  ["status info texto/bg", (c) => c.status.info.texto, "#info"],
  ["status ok texto/bg", (c) => c.status.ok.texto, "#ok"],
  ["status pendente texto/bg", (c) => c.status.pendente.texto, "#pendente"],
  // 46-UAT (2026-10-01, G-01..G-03): motivo âmbar sobre a superfície do card; chip da
  // meta (textSecondary/bgBase, já medido acima); linhas Ações usam positive/negative
  // sobre bgCard (já medidos acima).
  ["status pendente texto/bgCard", (c) => c.status.pendente.texto, "bgCard"],
  ["status info texto/bgCard", (c) => c.status.info.texto, "bgCard"],
  ["zona1 texto/bgBase", (c) => c.zonas[1].texto, "bgBase"],
  ["zona2 texto/bgBase", (c) => c.zonas[2].texto, "bgBase"],
  ["zona3 texto/bgBase", (c) => c.zonas[3].texto, "bgBase"],
];
for (const [nome, c] of Object.entries(cartao)) {
  for (const [rot, fgFn, fundo, ] of paresTexto) {
    const bgHex = fundo.startsWith("#") ? c.status[fundo.slice(1)].bg : bgOf(c, fundo);
    const r = contrast(luminanceRGB(hexToRgb(fgFn(c))), luminanceRGB(hexToRgb(bgHex)));
    ok(`${nome}: ${rot} = ${r.toFixed(2)} >= 4.5`, r >= T45);
  }
}

// ---- pares GRÁFICOS / borda (>= 3,0), D-17 -----------------------------------
// positive/negative compostos sobre a trilha (knob) e sobre bgBase (mix alfa).
// A UI-SPEC previa 0,5; a medição da 46-08 reprovou e subiu para 0,75 nos
// segmentos extremos. O segmento do meio (lucro cresce) é mais claro por desenho
// (gradação) e usa ALFA_ZONA_MEIO_V6. Os valores vêm de cartaoV6Cores.js e o
// App.jsx tem de usar essas MESMAS constantes (travado abaixo).
const nUsos = (re) => (appSrc.match(re) || []).length;
ok("App.jsx: segmentos extremos (Faixa + Simulador) usam ALFA_ZONA_V6", nUsos(/T\.negative, ALFA_ZONA_V6\)/g) >= 2 && nUsos(/T\.positive, ALFA_ZONA_V6\)/g) >= 2);
ok("App.jsx: segmento do meio usa a cor de ponto da zona 2 com ALFA_ZONA_MEIO_V6", nUsos(/"var\(--cv-zona-meio\)", ALFA_ZONA_MEIO_V6\)/g) >= 2);
ok("ALFA_ZONA_V6 = 0.75 (>= 0.75 medido) e meio < extremos (gradação)", ALFA_ZONA_V6 >= 0.75 && ALFA_ZONA_MEIO_V6 < ALFA_ZONA_V6);
function mixSobre(fgHex, a, bgHex) {
  const [fr, fg2, fb] = hexToRgb(fgHex), [br, bg2, bb] = hexToRgb(bgHex);
  return [fr * a + br * (1 - a), fg2 * a + bg2 * (1 - a), fb * a + bb * (1 - a)];
}
for (const [nome, c] of Object.entries(cartao)) {
  const graf = [];
  for (const [fundoNome, fundoHex] of [["bgBase", c.bgBase], ["knob", c.knob], ["bgCard", c.bgCard]]) {
    const lumF = luminanceRGB(hexToRgb(fundoHex));
    graf.push([`warn/${fundoNome}`, luminanceRGB(hexToRgb(c.warn)), lumF]);
    graf.push([`negative/${fundoNome} (borda)`, luminanceRGB(hexToRgb(c.negative)), lumF]);
    graf.push([`positive@${ALFA_ZONA_V6}/${fundoNome}`, luminanceRGB(mixSobre(c.positive, ALFA_ZONA_V6, fundoHex)), lumF]);
    graf.push([`negative@${ALFA_ZONA_V6}/${fundoNome}`, luminanceRGB(mixSobre(c.negative, ALFA_ZONA_V6, fundoHex)), lumF]);
    graf.push([`zona-meio@${ALFA_ZONA_MEIO_V6}/${fundoNome}`, luminanceRGB(mixSobre(c.zonaMeio, ALFA_ZONA_MEIO_V6, fundoHex)), lumF]);
    graf.push([`accent/${fundoNome} (linha hoje)`, luminanceRGB(hexToRgb(c.accent)), lumF]);
    graf.push([`textPrimary/${fundoNome} (marcas)`, luminanceRGB(hexToRgb(c.textPrimary)), lumF]);
  }
  for (const [rot, lumFg, lumF] of graf) {
    const r = contrast(lumFg, lumF);
    ok(`${nome}: ${rot} = ${r.toFixed(2)} >= 3.0`, r >= 3.0);
  }
}

// vars do wrapper cobrem as chaves lidas pelo card
const v = varsCartaoV6("dark", "estudo");
ok("varsCartaoV6 emite --bg-card/--accent/--cv-zona-meio", v["--bg-card"] === "#111b29" && v["--accent"] === "#55cfbe" && v["--cv-zona-meio"] === "#9fd9c6");
ok("escuro estudo/operador = paleta literal do design v6", coresCartaoV6("dark", "operador").accent === "#e4be60" && coresCartaoV6("dark", "operador").onAccent === "#231a04" && coresCartaoV6("dark", "estudo").textPrimary === "#edf2fa");

// 46-UAT (2026-10-01, G-01..G-03): vars dos estados pendente/info chegam ao card.
// A borda #465d7b do cadeado é decorativa (o texto carrega a informação): não é
// medida como gráfico >= 3.0.
ok("varsCartaoV6 emite vars pendente/info do escuro", v["--cv-pendente-bg"] === "#2d2618" && v["--cv-pendente-texto"] === "#ffe3a0" && v["--cv-info-bg"] === "#16233a" && v["--cv-info-texto"] === "#d6deeb");

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\nOK");
