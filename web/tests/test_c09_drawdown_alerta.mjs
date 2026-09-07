// C-09 (REPORT-01) — Guardião: com drawdown acima de LIMIAR_DRAWDOWN_ALERTA
// (15%), o card de Patrimônio Simulado (CapitalCurve) mostra um aviso
// não-bloqueante com sugestão de ação; com drawdown de 15% ou menos, nada
// aparece. Formato estático espelhando test_concentracao_carteira.mjs, mais
// uma unidade da condição via equityCurve (finance.js).
// Roda sem build: `node web/tests/test_c09_drawdown_alerta.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";
import { equityCurve } from "../src/finance.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- (a) LIMIAR_DRAWDOWN_ALERTA = 15 e condição de render estrita ----------
ok("LIMIAR_DRAWDOWN_ALERTA declarado = 15", /const LIMIAR_DRAWDOWN_ALERTA = 15;/.test(app));
ok("LIMIAR_DRAWDOWN_ALERTA usado ao menos 2x (declaração + uso)", (app.match(/LIMIAR_DRAWDOWN_ALERTA/g) || []).length >= 2);
ok("condição de render é dd > LIMIAR_DRAWDOWN_ALERTA (15% exatos não dispara)",
  app.includes("dd > LIMIAR_DRAWDOWN_ALERTA"));

// ---- isola o corpo de CapitalCurve (mesmo padrão de test_fase21) ----------
const inicioCapitalCurve = app.indexOf("function CapitalCurve(");
if (inicioCapitalCurve < 0) throw new Error("função CapitalCurve não encontrada em App.jsx — re-grep necessário.");
const fimCapitalCurve = app.indexOf("\nfunction ", inicioCapitalCurve + 10);
const capitalCurve = app.slice(inicioCapitalCurve, fimCapitalCurve > inicioCapitalCurve ? fimCapitalCurve : undefined);

ok("corpo de CapitalCurve contém o bloco novo (LIMIAR_DRAWDOWN_ALERTA)", capitalCurve.includes("LIMIAR_DRAWDOWN_ALERTA"));

// bloco do card: do gate `dd > LIMIAR_DRAWDOWN_ALERTA` até o fechamento do
// bloco condicional que o renderiza — mesmo recorte usado no card de
// concentração (test_concentracao_carteira.mjs), adaptado ao formato
// `{cond && (<div>...</div>)}` (sem IIFE aqui).
const iniCard = capitalCurve.indexOf("dd > LIMIAR_DRAWDOWN_ALERTA");
if (iniCard === -1) throw new Error("Card de drawdown não encontrado em CapitalCurve.");
const fimCard = capitalCurve.indexOf(")}", iniCard);
const blocoCard = capitalCurve.slice(iniCard, fimCard === -1 ? iniCard + 1200 : fimCard);

ok("card usa T.warn", /T\.warn/.test(blocoCard));
ok("card NÃO usa T.negative dentro do bloco (aviso educacional, não erro)", !/T\.negative/.test(blocoCard));

// ---- (c) card NÃO chama abrirVerbete (fora de escopo) ----------------------
ok("card NÃO chama abrirVerbete (sem verbete de drawdown — fora de escopo)", !blocoCard.includes("abrirVerbete"));

// ---- (d) kicker próprio, sem colidir com o grep de CONCENTRAÇÃO ALTA ------
ok("grep único de 'CONCENTRAÇÃO ALTA' segue com exatamente 1 ocorrência em App.jsx",
  (app.match(/CONCENTRAÇÃO ALTA/g) || []).length === 1);
ok("kicker do card novo é 'DRAWDOWN ALTO' (texto próprio)", blocoCard.includes("DRAWDOWN ALTO"));

// ---- (e) CapitalCurve não introduz nenhum `disabled=` ----------------------
ok("CapitalCurve não introduz nenhum `disabled=`", !capitalCurve.includes("disabled="));

// ---- (f) as 2 chaves de copy nos DOIS modos --------------------------------
ok("chave drawdownAlertaTitulo existe nos dois modos", "drawdownAlertaTitulo" in COPY.estudo && "drawdownAlertaTitulo" in COPY.operador);
ok("chave drawdownAlertaCorpo existe nos dois modos", "drawdownAlertaCorpo" in COPY.estudo && "drawdownAlertaCorpo" in COPY.operador);
ok("drawdownAlertaTitulo é idêntico nos dois modos (rótulo, não voz)",
  COPY.estudo.drawdownAlertaTitulo === COPY.operador.drawdownAlertaTitulo && COPY.estudo.drawdownAlertaTitulo === "Drawdown alto");

// ---- (g) corpo contém o percentual passado (verbatim contra o texto escrito) ----
const corpoEstudo23 = COPY.estudo.drawdownAlertaCorpo(23);
const corpoOperador23 = COPY.operador.drawdownAlertaCorpo(23);
ok("drawdownAlertaCorpo(23) do modo estudo contém '23'", corpoEstudo23.includes("23"));
ok("drawdownAlertaCorpo(23) do modo operador contém '23'", corpoOperador23.includes("23"));
ok("corpo do modo estudo é IDÊNTICO byte a byte à copy escrita",
  corpoEstudo23 === "Sua carteira já caiu 23% desde o pico. Quedas grandes pedem mais cautela: considere reduzir o tamanho das próximas posições até recuperar confiança no plano.");
ok("corpo do modo operador é IDÊNTICO byte a byte à copy escrita",
  corpoOperador23 === "Drawdown de 23% desde o pico. Perda dessa magnitude pede revisão de tamanho antes da próxima entrada — não force recuperação com posição maior.");

// ---- (h) vocabulário de ordem proibido no ramo estudo ----------------------
ok("corpo do modo estudo não usa vocabulário de ordem de operação", !/comprar|vender/i.test(corpoEstudo23));

// ---- guardião geral test_copy_theme.mjs: função não pode lançar com args
//      arbitrários — reproduz a chamada v("X","Y","Z") / v(null,0,0) daquele
//      guardião só para drawdownAlertaCorpo, como smoke test local.
ok("drawdownAlertaCorpo não lança com v(\"X\",\"Y\",\"Z\")", (() => {
  try { COPY.estudo.drawdownAlertaCorpo("X", "Y", "Z"); COPY.operador.drawdownAlertaCorpo("X", "Y", "Z"); return true; } catch { return false; }
})());
ok("drawdownAlertaCorpo não lança com v(null,0,0)", (() => {
  try { COPY.estudo.drawdownAlertaCorpo(null, 0, 0); COPY.operador.drawdownAlertaCorpo(null, 0, 0); return true; } catch { return false; }
})());

// ---- (i) unidade da CONDIÇÃO: equityCurve produz drawdown > 15 e <= 15 -----
const ecAlto = equityCurve(
  [
    { data: "2026-09-01", patrimonio: 10000, base: 10000 },
    { data: "2026-09-02", patrimonio: 12000 },
  ],
  10000,
  9000,
  "2026-09-03"
);
ok("equityCurve: cenário de queda forte produz ec.drawdown > 15", ecAlto.drawdown > 15);

const ecBaixo = equityCurve(
  [
    { data: "2026-09-01", patrimonio: 10000, base: 10000 },
    { data: "2026-09-02", patrimonio: 10500 },
  ],
  10000,
  9700,
  "2026-09-03"
);
ok("equityCurve: cenário de queda leve produz ec.drawdown <= 15", ecBaixo.drawdown <= 15);

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DE C-09 (DRAWDOWN ALTO) PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
