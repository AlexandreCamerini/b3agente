// qa/32 — Guardião: MODE_OPERADOR.light precisa diferenciar fundo/cartão/
// bordas/texto do Modo Estudo, não só acento/positivo/negativo. Antes deste
// fix, o override em tema CLARO só trocava 3 cores — Estudo e Operador
// ficavam com o MESMO chrome (bgBase/bgPanel/bgCard/borders/textMuted) em
// light, o que é a causa mais provável de "as paletas ainda estão iguais"
// para quem testa em tema claro.
// Roda sem device nem build: `node web/tests/test_mode_operador_light_palette.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const m = /const MODE_OPERADOR = \{[\s\S]*?\n\};/.exec(src);
ok("MODE_OPERADOR localizado em App.jsx", !!m);
const block = m ? m[0] : "";
const lightMatch = /light:\s*\{([\s\S]*?)\n  \},\n\};/.exec(block);
ok("bloco MODE_OPERADOR.light localizado", !!lightMatch);
const light = lightMatch ? lightMatch[1] : "";

// As mesmas chaves de CHROME que já existiam em dark precisam existir em
// light — não só accent/positive/negative/tints.
for (const key of ["bgBase", "bgPanel", "bgCard", "borderSubtle", "textMuted", "textDim", "textFaint"]) {
  ok(`MODE_OPERADOR.light define ${key} (chrome diferenciado, não só acento)`, new RegExp(`\\b${key}:`).test(light));
}

// Valores não podem ser idênticos aos do tema Estudo light (PALETTE.light) —
// checagem pontual dos 2 mais visíveis (bgBase e textMuted).
const estudoLightMatch = /light:\s*\{([\s\S]*?)\n  \},\n\};/.exec(/const PALETTE = \{[\s\S]*?\n\};/.exec(src)[0]);
const estudoLight = estudoLightMatch ? estudoLightMatch[1] : "";
const bgBaseEstudo = (/bgBase:\s*"(#[0-9a-fA-F]+)"/.exec(estudoLight) || [])[1];
const bgBaseOperador = (/bgBase:\s*"(#[0-9a-fA-F]+)"/.exec(light) || [])[1];
ok("bgBase do Operador (light) é diferente do Estudo (light)", !!bgBaseEstudo && !!bgBaseOperador && bgBaseEstudo !== bgBaseOperador);

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
