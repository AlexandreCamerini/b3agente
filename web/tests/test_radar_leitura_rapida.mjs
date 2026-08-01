// qa/34 (P1+P3) — Guardião: "leitura inicial rápida" nos cards do Radar.
//
// QUEIXA (checkout, pendência "Radar sem análise inicial rápida"): ao abrir a
// aba Radar em Modo Estudo o card era só chips/anel/números — nenhuma frase
// interpretativa antes do CTA pago "Aprofundar com IA". O diagnóstico mostrou
// que TODO o dado necessário já vinha no payload determinístico do scan
// (server/app/scanner.py): `plano.motivo` (prosa pronta do setups.py, antes
// exibida SÓ no Modo Operador), `confluencia` (tierOf), `setups[0].criterios`
// e `spark` (série de fechamentos, usada só na Watchlist).
//
// Este guardião tranca as 3 partes do fix (zero custo de LLM):
//   P1 — o `plano.motivo` aparece TAMBÉM no Estudo (gate `!operador`);
//   P3a — o card do Radar renderiza <Sparkline> com o `spark` do payload;
//   P3b — pill de confiança (tierOf) + contagem de critérios no card.
// Roda sem build: `node web/tests/test_radar_leitura_rapida.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Corpo de função top-level (mesma convenção dos demais guardiões).
function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(src);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(m.index, i);
}

const radar = functionBody("RadarScreen");
ok("RadarScreen: função localizada em App.jsx", !!radar);

if (radar) {
  // P1 — leitura em prosa no Estudo: o motivo do plano não pode mais ser
  // exclusivo do Operador. Gate esperado: `!operador && r.plano && r.plano.motivo`.
  ok("P1: motivo do plano exibido também no Estudo (gate !operador)",
    /\{!operador\s*&&\s*r\.plano\s*&&\s*r\.plano\.motivo\s*&&/.test(radar));
  // O plano OPERACIONAL completo (entrada/stop/alvo/sizing) continua gated ao
  // Operador — a leitura do Estudo é só a prosa, não o painel de execução.
  ok("P1: plano operacional segue exclusivo do Operador (operador ? r.plano : null)",
    /operador\s*\?\s*r\.plano\s*:\s*null/.test(radar));

  // P3a — sparkline com o `spark` do payload. qa/49 (v11): o Radar passa
  // `r.spark` ao CARD ÚNICO (radarVm.sc.spark) e o AtivoCard o renderiza.
  ok("P3a: Radar alimenta o card único com r.spark (→ Sparkline no AtivoCard)",
    /sc: \{ spark: r\.spark/.test(radar) && /<Sparkline data=\{sc\.spark\}/.test(src));

  // P3b — pill de confiança derivada de tierOf + contagem de critérios.
  ok("P3b: pill de confiança usa tierOf(r.confluencia)",
    /tierLabel\s*=\s*tierOf\(r\.confluencia\)/.test(radar) && /confiança \{tierLabel/.test(radar));
  ok("P3b: contagem de critérios atendidos (critOk/critTot) no card",
    /critOk\s*=/.test(radar) && /critOk\}\/\$\{critTot\}/.test(radar));
}

// Fonte do dado: o scanner do servidor precisa continuar emitindo `spark` —
// sem ele P3a degrada silenciosamente (Sparkline devolve null).
const scanner = readFileSync(join(here, "..", "..", "server", "app", "scanner.py"), "utf8");
ok("scanner.py: payload do scan segue emitindo o campo `spark`", /["']spark["']\s*:/.test(scanner));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
