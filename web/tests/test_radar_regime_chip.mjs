// ADR-009 (Refactor A) — indicador visual do regime no card do Radar.
// O eixo de ordenação (regime + momentum) é invisível na UI desde o merge do
// Refactor A; este chip é o que torna a ordem nova explicável para quem olha
// a tela. Guardião: trava que o RegimeChip existe, está wireado no card do
// Radar, degradação (SMA50) se declara e "indefinido" nunca aparece (mesma
// postura do FundamentoChip sem score — dado insuficiente não vira chip).
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const appSrc = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const chipFn = appSrc.slice(appSrc.indexOf("function RegimeChip"), appSrc.indexOf("function RegimeChip") + 900);

ok("RegimeChip existe", appSrc.includes("function RegimeChip"));
ok("indefinido nunca vira chip (mesma postura do FundamentoChip sem score)",
  /regime\.regime\s*===\s*"indefinido"\)\s*return null/.test(chipFn));
ok("tendencia_alta mapeia pra cor positive", /tendencia_alta:\s*\["positive"/.test(appSrc));
ok("tendencia_baixa mapeia pra cor negative", /tendencia_baixa:\s*\["negative"/.test(appSrc));
ok("degradação (SMA50) se declara no chip — CLAUDE.md: dado insuficiente avisa, não estima",
  /confiavel\s*===\s*false/.test(chipFn) && /SMA50/.test(chipFn));
ok("chip wireado no card do Radar (RadarScreen)", /<RegimeChip regime=\{r\.regime\}/.test(appSrc));
ok("chip vem depois do FundamentoChip no mesmo grupo de badges",
  appSrc.indexOf("<FundamentoChip f={r.fundamento}") < appSrc.indexOf("<RegimeChip regime={r.regime}"));
ok("gatilhoAlinhado aparece como texto quando true (sem novo componente)",
  /r\.gatilhoAlinhado \? " · alinhado ao regime" : ""/.test(appSrc));

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
