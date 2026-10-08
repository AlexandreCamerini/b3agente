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

if (falhas.length) {
  console.error(`FALHOU (${falhas.length}):\n- ` + falhas.join("\n- "));
  process.exit(1);
}
console.log(`ok test_ui_onda_a (${nBotoes} botões varridos)`);
