// Quick 261008-16z — Onda A da UI (diagnóstico de 2026-10-08).
// Guardião de 3 contratos de acessibilidade, lidos do fonte (roda sem build):
//  1) alvos de toque: nenhum <button> com height/minHeight numérico < 44 (allowlist vazia)
//     e o Toggle não anima `left` (layout-anim);
//  2) diálogos/abas: os 4 modais têm role="dialog" + aria-modal + Esc; a BottomNav usa
//     aria-current e NÃO aria-pressed;
//  3) contraste: todo token de texto dos 4 temas (claro/escuro × Estudo/Operador) >= 4,5:1
//     contra o PIOR entre bgBase/bgPanel/bgCard (exceto chartAxis, decorativo).
// `node web/tests/test_ui_onda_a.mjs` (a partir da raiz ou de web/).
import { readFileSync, readdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, "..", "src");
const appPath = join(src, "App.jsx");
const app = readFileSync(appPath, "utf8");
const falhas = [];
const falha = (m) => falhas.push(m);

// ---------------------------------------------------------------- parte 1
// Extrai a tag de abertura de cada <button ...> (respeita {} aninhado, strings e
// template literals; o `>` de `=>` não fecha a tag).
function tagsBotao(texto) {
  const out = [];
  let i = 0;
  while ((i = texto.indexOf("<button", i)) !== -1) {
    const prox = texto[i + 7];
    if (prox && !/[\s>]/.test(prox)) { i += 7; continue; }
    let j = i + 7, depth = 0, q = null;
    for (; j < texto.length; j++) {
      const c = texto[j];
      if (q) {
        if (c === "\\") { j++; continue; }
        if (c === q) q = null;
        continue;
      }
      if (c === '"' || c === "'" || c === "`") { q = c; continue; }
      if (c === "{") depth++;
      else if (c === "}") depth--;
      else if (c === ">" && depth === 0 && texto[j - 1] !== "=") break;
    }
    out.push({ idx: i, tag: texto.slice(i, j + 1) });
    i = j + 1;
  }
  return out;
}
const arquivos = [appPath, ...readdirSync(join(src, "opcoes")).filter((f) => f.endsWith(".jsx")).map((f) => join(src, "opcoes", f))];
let nBotoes = 0;
for (const f of arquivos) {
  const t = readFileSync(f, "utf8");
  for (const { idx, tag } of tagsBotao(t)) {
    nBotoes++;
    for (const m of tag.matchAll(/\b(min[Hh]eight|height)\s*:\s*"?(\d+(?:\.\d+)?)(?:px)?"?/g)) {
      if (parseFloat(m[2]) < 44) {
        const linha = t.slice(0, idx).split("\n").length;
        falha(`[A1] <button> com ${m[1]}: ${m[2]} < 44 em ${f.split("/src/")[1]}:${linha}`);
      }
    }
  }
}
if (nBotoes < 100) falha(`[A1] parser achou só ${nBotoes} botões — esperado >= 100 (parser quebrado?)`);
{
  const a = app.indexOf("function Toggle(");
  const corpo = app.slice(a, app.indexOf("\nfunction ", a + 10));
  if (/transition:\s*"left/.test(corpo) || /\bleft:\s*s\.knob/.test(corpo)) falha("[A1] Toggle anima `left` (usar transform)");
  if (!/transform:/.test(corpo)) falha("[A1] Toggle sem transform no knob");
}

// ---------------------------------------------------------------- parte 2
for (const nome of ["BuyModal", "SellModal", "CatalogModal", "TechnicalModal"]) {
  const a = app.search(new RegExp(`function ${nome}\\(`));
  if (a < 0) { falha(`[A2] ${nome} não encontrado`); continue; }
  const prox = app.indexOf("\nfunction ", a + 10);
  let corpo = app.slice(a, prox < 0 ? undefined : prox);
  if (nome === "TechnicalModal") {
    // TechnicalModal delega o invólucro ao BottomSheet (único consumidor): o contrato vive lá.
    if (!/<BottomSheet[^>]*label=/.test(corpo)) falha("[A2] TechnicalModal não passa label ao BottomSheet");
    const b = app.search(/function BottomSheet\(/);
    corpo += app.slice(b, app.indexOf("\nfunction ", b + 10));
  }
  if (!/role="dialog"/.test(corpo)) falha(`[A2] ${nome} sem role="dialog"`);
  if (!/aria-modal="true"|aria-modal(?![-\w])/.test(corpo)) falha(`[A2] ${nome} sem aria-modal`);
  if (!/aria-label/.test(corpo)) falha(`[A2] ${nome} sem aria-label/labelledby`);
  if (!/useDialogA11y\(/.test(corpo)) falha(`[A2] ${nome} não usa useDialogA11y (Esc + foco)`);
}
{
  const hook = readFileSync(join(src, "useDialogA11y.js"), "utf8");
  if (!/Escape/.test(hook)) falha("[A2] useDialogA11y sem handler de Escape");
  if (!/\.focus\(/.test(hook)) falha("[A2] useDialogA11y não move/devolve foco");
  if (!/removeEventListener\(\s*"keydown"/.test(hook)) falha("[A2] useDialogA11y não remove o listener keydown");
}
{
  const a = app.search(/function BottomNav\(/);
  const corpo = app.slice(a, app.indexOf("\nfunction ", a + 10));
  if (!/aria-current/.test(corpo)) falha("[A2] BottomNav sem aria-current");
  if (/aria-pressed/.test(corpo)) falha("[A2] BottomNav ainda usa aria-pressed");
  if (!/<nav[^>]*aria-label="Navegação principal"/.test(corpo)) falha('[A2] BottomNav sem <nav aria-label="Navegação principal">');
}

// ---------------------------------------------------------------- parte 3
function objeto(nomeDecl) {
  const a = app.indexOf(nomeDecl);
  let j = app.indexOf("{", a), d = 0, k = j;
  for (; k < app.length; k++) { if (app[k] === "{") d++; else if (app[k] === "}" && --d === 0) break; }
  return app.slice(j, k + 1);
}
const BRAND = { green: "#34d399", red: "#f26d6d" };
// avalia só hex literal / BRAND.x; ignora comentários de linha
const limpa = (s) => s.replace(/\/\/[^\n]*/g, "");
function parseTema(bloco) {
  const o = {};
  for (const m of limpa(bloco).matchAll(/(\w+):\s*(?:"(#[0-9a-fA-F]{6})"|BRAND\.(\w+))/g)) o[m[1]] = m[2] || BRAND[m[3]];
  return o;
}
function sub(texto, nome) {
  const a = texto.indexOf(`${nome}: {`);
  let j = texto.indexOf("{", a), d = 0, k = j;
  for (; k < texto.length; k++) { if (texto[k] === "{") d++; else if (texto[k] === "}" && --d === 0) break; }
  return texto.slice(j, k + 1);
}
const PAL = objeto("const PALETTE = {");
const OPR = objeto("const MODE_OPERADOR = {");
const base = { dark: parseTema(sub(PAL, "dark")), light: parseTema(sub(PAL, "light")) };
const opr = { dark: parseTema(sub(OPR, "dark")), light: parseTema(sub(OPR, "light")) };
const lum = (h) => {
  const c = [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
};
const razao = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const TEXTO = ["textPrimary", "textSecondary", "textMuted", "textDim", "textFaint", "textBright", "accent", "accentSoft", "positive", "negative", "warn"];
const temas = {
  "claro/estudo": base.light, "claro/operador": { ...base.light, ...opr.light },
  "escuro/estudo": base.dark, "escuro/operador": { ...base.dark, ...opr.dark },
};
export const razoes = {};
for (const [nome, p] of Object.entries(temas)) {
  for (const tk of TEXTO) {
    if (!p[tk]) { falha(`[A3] ${nome}: token ${tk} não lido`); continue; }
    const pior = Math.min(...["bgBase", "bgPanel", "bgCard"].map((b) => razao(p[tk], p[b])));
    razoes[`${nome}.${tk}`] = pior;
    if (pior < 4.5) falha(`[A3] ${nome}.${tk} ${p[tk]} = ${pior.toFixed(2)}:1 < 4,5`);
  }
  // texto sobre fundo de acento (CTA)
  const ca = razao(p.onAccent, p.accent);
  razoes[`${nome}.onAccent/accent`] = ca;
  if (ca < 4.5) falha(`[A3] ${nome}: onAccent ${p.onAccent} sobre accent ${p.accent} = ${ca.toFixed(2)}:1 < 4,5`);
}
if (process.argv.includes("--razoes")) for (const [k, v] of Object.entries(razoes)) console.log(k, v.toFixed(3));

if (falhas.length) {
  console.error(`FALHOU (${falhas.length}):\n- ` + falhas.join("\n- "));
  process.exit(1);
}
console.log(`ok test_ui_onda_a (${nBotoes} botões varridos; 4 temas; modais/nav)`);
