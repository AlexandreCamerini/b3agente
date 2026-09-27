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
  // REVERSÃO DELIBERADA (2026-09-26, Fase 42, HIER-01/HIER-02/D-08/D-09):
  // P1 — o motivo do plano no Estudo e o plano operacional completo não são
  // mais gated dentro de RadarScreen: ambos migraram para o AtivoCard/
  // PlanoOperacionalBloco, o mesmo componente da Watchlist (HIER-02). A
  // GARANTIA original sobrevive: motivo aparece no Estudo, plano completo
  // segue exclusivo do Operador — só a localização mudou.
  const av = src.slice(src.indexOf("function PlanoOperacionalBloco("), src.indexOf("function AtivoCard("));
  ok("P1: motivo do plano exibido também no Estudo (gate !operador && motivo &&, dentro de PlanoOperacionalBloco)",
    /!operador\s*&&\s*motivo\s*&&/.test(av));
  ok("P1: AtivoCard passa motivo={sc && sc.plano ? sc.plano.motivo : null} (subconjunto explícito de sc)",
    /motivo=\{sc && sc\.plano \? sc\.plano\.motivo : null\}/.test(src));
  // O plano OPERACIONAL completo (entrada/stop/alvo/sizing) continua gated ao
  // Operador — a leitura do Estudo é só a prosa, não o painel de execução.
  ok("P1: plano operacional segue exclusivo do Operador (plano={operador && sc ? sc.plano : null})",
    /plano=\{operador && sc \? sc\.plano : null\}/.test(src));
  ok("P1: radarVm.sc leva plano: r.plano (subconjunto explícito, ADR-017 Bloco 3)",
    /sc: \{[^}]*plano: r\.plano/.test(radar));

  // P3a — sparkline com o `spark` do payload. qa/49 (v11): o Radar passa
  // `r.spark` ao CARD ÚNICO (radarVm.sc.spark) e o AtivoCard o renderiza.
  ok("P3a: Radar alimenta o card único com r.spark (→ Sparkline no AtivoCard)",
    /sc: \{ spark: r\.spark/.test(radar) && /<Sparkline data=\{sc\.spark\}/.test(src));

  // REVERSÃO DELIBERADA (2026-09-26, Fase 42, HIER-01/D-08/D-09): a pill
  // "confiança {tierLabel}" solta e a contagem "x/y critérios" do cabeçalho
  // do Radar saem — o tier + o lado + o setup passam a viver no rótulo do
  // anel de confluência, uma vez só, dentro do SinalChip peso="primario"
  // (mesmo anel da Watchlist). Prova negativa dupla (HIER-01: nunca duas
  // vezes o tier no mesmo card).
  ok("P3b: tier + lado + setup no rótulo do anel (AtivoCard, tierOf(sc.confluencia)[1] + rotuloAnel)",
    /tierOf\(sc\.confluencia\)\[1\]/.test(src) && /rotuloAnel\(/.test(src));
  ok("P3b: RadarScreen NÃO contém mais a pill solta \"confiança {tierLabel\" (HIER-01, tier uma vez por card)",
    !/confiança \{tierLabel/.test(radar));
  ok("P3b: RadarScreen NÃO contém mais a contagem \"x/y critérios\" no cabeçalho (D-09, absorvida pelo anel)",
    !/critOk/.test(radar));
}

// Fonte do dado: o scanner do servidor precisa continuar emitindo `spark` —
// sem ele P3a degrada silenciosamente (Sparkline devolve null).
const scanner = readFileSync(join(here, "..", "..", "server", "app", "scanner.py"), "utf8");
ok("scanner.py: payload do scan segue emitindo o campo `spark`", /["']spark["']\s*:/.test(scanner));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
