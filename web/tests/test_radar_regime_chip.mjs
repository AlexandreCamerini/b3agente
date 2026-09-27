// ADR-009 (Refactor A) — indicador visual do regime no card do Radar.
// O eixo de ordenação (regime + momentum) é invisível na UI desde o merge do
// Refactor A; o indicador é o que torna a ordem nova explicável para quem
// olha a tela.
//
// REVERSÃO DELIBERADA (2026-09-26, Fase 42, HIER-01/CHIP-01/D-05/D-06/D-07):
// RegimeChip/REGIME_STYLE foram apagados — o regime agora é um `SinalChip
// peso="contexto"` dentro de `LinhaContexto` (mesmo componente da
// Watchlist), com o "x/y critérios" e " · alinhado ao regime" saindo do
// cabeçalho do Radar (D-09). As GARANTIAS originais sobrevivem, só a
// implementação mudou: (1) "indefinido" nunca vira chip; (2) degradação
// SMA50 se declara; (3) regime deixa de ter cor de direção — ganha marca de
// alinhamento neutra (↗/↘) em vez de tendencia_alta=positive/baixa=negative.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { regimeRotulo, alinhamentoDoMotor } from "../src/sinal.js";

const here = dirname(fileURLToPath(import.meta.url));
const appSrc = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// (1) "indefinido" nunca vira chip — mesma postura de fundamento sem score.
ok("regimeRotulo(indefinido) === null (nunca vira chip)",
  regimeRotulo({ regime: "indefinido" }) === null);
ok("regimeRotulo(sem regime) === null",
  regimeRotulo(null) === null);

// alinhamentoDoMotor: lateral não tem tendência para estar a favor/contra.
ok("alinhamentoDoMotor em regime lateral === null (sem tendência, sem marca)",
  alinhamentoDoMotor({ decisao: "COMPRAR", regime: { regime: "lateral" }, gatilhoAlinhado: true }) === null);
ok("alinhamentoDoMotor com gatilhoAlinhado=true e tendência === \"a_favor\"",
  alinhamentoDoMotor({ decisao: "COMPRAR", regime: { regime: "tendencia_alta" }, gatilhoAlinhado: true }) === "a_favor");
ok("alinhamentoDoMotor com gatilhoAlinhado=false e tendência === \"contra\"",
  alinhamentoDoMotor({ decisao: "VENDER", regime: { regime: "tendencia_baixa" }, gatilhoAlinhado: false }) === "contra");

// LinhaContexto: degradação SMA50 declarada, ordem regime < fundamento.
// Corpo isolado por casamento de chaves (não por slice até a próxima
// função) — senão o comentário de PlanoOperacionalBloco (que cita
// T.negative/T.positive como nível de preço, D-05) contaminaria a ban list.
function functionBodyLC(name, src) {
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
const lc = functionBodyLC("LinhaContexto", appSrc);
ok("LinhaContexto existe", appSrc.includes("function LinhaContexto("));
ok("degradação (SMA50) se declara — CLAUDE.md: dado insuficiente avisa, não estima",
  /regime\.confiavel === false/.test(lc) && /cp\.degradadoSufixo/.test(lc));
ok("LinhaContexto renderiza regime ANTES de fundamento (ordem de leitura, UI-SPEC)",
  lc.indexOf('label="REGIME"') < lc.indexOf('label="FUNDAMENTO"'));

// (3) regime deixa de ter cor de direção — ban list D-05/D-06 dentro do corpo.
ok("corpo de LinhaContexto NÃO usa T.positive/T.negative (regime é neutro, D-06)",
  !/T\.positive|T\.negative/.test(lc));

// radarVm.sc leva os campos que a marca de alinhamento e o chip de regime
// precisam — subconjunto explícito (ADR-017 Bloco 3), nunca `r` inteiro.
ok("radarVm.sc leva regime: r.regime", /sc: \{[^}]*regime: r\.regime/.test(appSrc));
ok("radarVm.sc leva gatilhoAlinhado: r.gatilhoAlinhado", /sc: \{[^}]*gatilhoAlinhado: r\.gatilhoAlinhado/.test(appSrc));

// REVERSÃO DELIBERADA (D-09): "x/y critérios" e "alinhado ao regime" saíram
// do cabeçalho do Radar — prova negativa dentro do corpo de RadarScreen.
function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(appSrc);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < appSrc.length; i++) {
    if (appSrc[i] === "{") depth++;
    else if (appSrc[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return appSrc.slice(m.index, i);
}
const radar = functionBody("RadarScreen");
ok("RadarScreen: função localizada em App.jsx", !!radar);
ok("ausência do texto \" · alinhado ao regime\" (substituído pela marca de alinhamento, D-07)",
  radar && !/ · alinhado ao regime/.test(radar));
ok("RegimeChip não existe mais (apagado, CHIP-01)", !appSrc.includes("function RegimeChip"));

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
