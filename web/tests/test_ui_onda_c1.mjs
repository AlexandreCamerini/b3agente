// Onda C1 (2026-10-08) — quick 261008-1qw. Escala tipográfica inteira:
// nenhum fontSize/font-size literal com parte fracionária em web/src. Allowlist vazia.
// Fora do alcance (por desenho): unidades relativas (em/rem/%) e fatores multiplicativos
// (`size * 0.26`); linhas de comentário.
import { readFileSync, readdirSync, statSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join, relative } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const raiz = join(here, "..", "src");
const arquivos = [];
(function varre(d) {
  for (const n of readdirSync(d)) {
    const p = join(d, n);
    if (statSync(p).isDirectory()) varre(p);
    else if (/\.(js|jsx)$/.test(n)) arquivos.push(p);
  }
})(raiz);

const viol = [];
for (const f of arquivos) {
  readFileSync(f, "utf8").split("\n").forEach((l, i) => {
    if (l.trim().startsWith("//")) return;
    for (const m of l.matchAll(/(?:fontSize|font-size)\s*[=:]\s*([^,;}]*)/g)) {
      for (const n of m[1].matchAll(/(?<![\d.*])(\d+\.\d+)(?!\d)(?!\s*(?:em|rem|%))/g)) {
        const antes = m[1].slice(0, n.index).trimEnd();
        if (antes.endsWith("*")) continue;
        viol.push(`${relative(raiz, f)}:${i + 1} fontSize ${n[1]}`);
      }
    }
  });
}

let falhas = 0;
const ok = (nome, cond) => { if (!cond) { falhas++; console.error("FALHA:", nome); } };
ok("varreu arquivos de web/src", arquivos.length > 20);
ok("zero fontSize fracionário em web/src", viol.length === 0);
if (viol.length) console.error(viol.join("\n"));
// sanidade da regex: pega os formatos reais e ignora os relativos
const pega = (s) => /(?:fontSize|font-size)\s*[=:]\s*([^,;}]*)/.exec(s) && [...(/(?:fontSize|font-size)\s*[=:]\s*([^,;}]*)/.exec(s)[1]).matchAll(/(?<![\d.*])(\d+\.\d+)(?!\d)(?!\s*(?:em|rem|%))/g)].length;
ok("sanidade: pega 11.5px", pega('fontSize: "11.5px"') === 1);
ok("sanidade: pega css", pega("font-size:12.5px;") === 1);
ok("sanidade: pega ternário", pega('fontSize: c ? "12px" : "13.5px"') === 1);
ok("sanidade: ignora em", pega('fontSize: "0.92em"') === 0);

if (falhas) { console.error(`${falhas} falha(s)`); process.exit(1); }
console.log("test_ui_onda_c1: ok");
