// qa/mock v2 (racionalização de design) — Guardião: o badge de modo no Topbar
// virou uma LINHA DE MODO própria sob o wordmark (ponto na cor do modo, com
// halo accentTint, + rótulo em T.accent), no lugar do pill contornado antigo
// (qa/32). Motivo: o pill ficava apertado contra o patrimônio ("badge mal
// colocado", feedback do Alex). O badge segue SIMÉTRICO nos dois modos —
// estudo.chipModo deixou de ser null.
// Roda sem device nem build: `node web/tests/test_mode_badge_outlined.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// A linha de modo é renderizada condicionalmente ao modeChip (fragmento, não pill).
const m = /\{modeChip && \(<>[\s\S]*?<\/>\)\}/.exec(src);
ok("linha de modo localizada no Topbar", !!m);
const line = m ? m[0] : "";

ok("ponto na cor do modo com halo accentTint", /background: T\.accent[,}][\s\S]*?boxShadow: `0 0 0 3px \$\{T\.accentTint\}`/.test(line));
ok("rótulo do modo em T.accent", /color: T\.accent\b/.test(line) && /\{modeChip\}/.test(line));
ok("NÃO é mais pill contornado (sem borderRadius 999px no badge)", !/borderRadius:\s*"999px"/.test(line));

// Badge simétrico: os DOIS modos têm chipModo (antes só o Operador).
ok("badge simétrico — estudo e operador têm chipModo", !!COPY.estudo.chipModo && !!COPY.operador.chipModo);

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
