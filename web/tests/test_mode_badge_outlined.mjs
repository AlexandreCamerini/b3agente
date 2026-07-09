// qa/32 — Guardião: o chip "MODO OPERADOR" no Topbar precisa ser CONTORNADO
// (borda + tint translúcido), não mais preenchimento sólido — decisão do
// Alex (AskUserQuestion) sobre o redesenho do badge no header.
// Roda sem device nem build: `node web/tests/test_mode_badge_outlined.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const m = /\{modeChip && <span style=\{\{[\s\S]*?\}\}>\{modeChip\}<\/span>\}/.exec(src);
ok("chip do modo localizado no Topbar", !!m);
const chip = m ? m[0] : "";

ok("chip usa borda (contornado)", /border:\s*`1px solid \$\{T\.accent\}`/.test(chip));
ok("chip usa fundo translúcido (accentTint), não T.accent sólido", /background:\s*T\.accentTint/.test(chip));
ok("chip NÃO usa mais background: T.accent (preenchimento sólido)", !/background:\s*T\.accent[,}]/.test(chip));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
