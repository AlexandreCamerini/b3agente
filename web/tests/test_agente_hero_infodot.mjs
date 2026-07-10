// qa/34 (§7 da auditoria + mock v2 §10) — Guardião: aba Operador IA com
// CARD-HERÓI de estado + agrupamento "Regras & limites", e affordance única
// de disclaimer (ⓘ → AboutModal) por tela.
//
// Decisões aprovadas pelo Alex (AskUserQuestion):
//  • A aba Operador IA promove UM estado dominante (ATIVO/INATIVO · modo) no
//    topo, com o toggle como único CTA de peso; regras (stop/alvo/trailing),
//    tetos e intervalo do ciclo agrupados num card "REGRAS & LIMITES";
//    link de notificações no rodapé. NADA removido — só reorganizado.
//  • ⓘ ao lado do título nas 4 telas principais (Watchlist, Portfólio, Radar,
//    Operador IA) abrindo o ponto único do aviso legal (AboutModal).
// Roda sem build: `node web/tests/test_agente_hero_infodot.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

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

// ---- card-herói + Regras & limites -------------------------------------------
const ag = functionBody("AgenteScreen");
ok("AgenteScreen: função localizada", !!ag);
if (ag) {
  ok("herói: estado dominante ATIVO/INATIVO no topo",
    /"ATIVO" : "INATIVO"/.test(ag));
  ok("herói: kicker OPERADOR NO SERVIDOR",
    ag.includes("OPERADOR NO SERVIDOR"));
  ok("agrupamento REGRAS & LIMITES existe",
    ag.includes("REGRAS & LIMITES"));
  // nada removido: todos os controles seguem presentes
  ok("nada removido: toggle do servidor", ag.includes("setServer(!ag.serverEnabled)"));
  ok("nada removido: Executar/Sinalizar", ag.includes('"executar", "sinalizar"'));
  ok("nada removido: regras stop/alvo/trailing", ag.includes('["stop", "Regra: stop"]') && ag.includes('"trailing"'));
  ok("nada removido: tetos (ops/dia e valor máx.)", ag.includes("maxOpsDia") && ag.includes("maxValorOp"));
  ok("nada removido: intervalo do ciclo (5/15/30/60)", ag.includes("intervalMin: mn"));
  ok("nada removido: modo local + executar ciclo", ag.includes("Modo local (com o app aberto)") && ag.includes("Executar ciclo agora"));
  ok("rodapé: link de notificações + disclaimer no fim",
    ag.indexOf("A.openNotifCentral()") > ag.indexOf("EVENTOS E AVISOS RECENTES")
    && ag.indexOf("Opera somente a carteira simulada") > ag.indexOf("A.openNotifCentral()"));
}

// ---- ⓘ por tela ---------------------------------------------------------------
ok("InfoDot: componente existe e abre o AboutModal (openAbout)",
  /const InfoDot = \(\{ onClick \}\)/.test(src));
for (const [tela, fn] of [["Watchlist", "MercadoScreen"], ["Portfólio", "CarteiraScreen"], ["Radar", "RadarScreen"], ["Operador IA", "AgenteScreen"]]) {
  const body = functionBody(fn);
  ok(`ⓘ na tela ${tela} (${fn})`, !!body && /<InfoDot onClick=\{(ctx\.)?A\.openAbout\}/.test(body));
}

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
