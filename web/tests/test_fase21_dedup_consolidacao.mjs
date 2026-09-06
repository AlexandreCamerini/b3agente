// Guardião da Fase 21 (v1.5, Redesenho de UI), requisitos DEDUP-01 e
// DEDUP-03 — remoção da CapitalCurve duplicada em Portfólio e consolidação
// dos 4 cards de KPI num único card denso 2×2.
//
// Este arquivo é o único guardião da Fase 21 (plano 21-01). Os planos 21-03
// (FIX-03, placeholder "poucos dias" da própria CapitalCurve) e o que vier a
// tratar DEDUP-02 (card de status do Operador IA) devem ESTENDER este mesmo
// arquivo com as novas asserções — não criar um segundo arquivo paralelo de
// guardião para a mesma tela/fase.
//
// Roda sem build: `node web/tests/test_fase21_dedup_consolidacao.mjs`.
// Padrão da casa: regex sobre App.jsx lido com readFileSync — o módulo
// importa @capacitor/core e não é importável fora do build (ver
// test_fase3_c19_card_status.mjs, test_fase20_fundacao_visual.mjs).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// --- Isolamento dos dois componentes envolvidos ---------------------------
// Mesmo padrão de isolamento de test_fase3_c19_card_status.mjs: do
// `function Xxx(` até o próximo `\nfunction ` no arquivo. Aborta com
// mensagem explícita se o marcador sumir — nunca passa em silêncio.

const inicioEvolucao = app.indexOf("function EvolucaoScreen(");
if (inicioEvolucao < 0) {
  console.error("FALHOU: função EvolucaoScreen não encontrada em App.jsx — guardião não pode isolar o componente");
  process.exit(1);
}
const fimEvolucao = app.indexOf("\nfunction ", inicioEvolucao + 10);
const evolucaoScreen = app.slice(inicioEvolucao, fimEvolucao > inicioEvolucao ? fimEvolucao : undefined);

const inicioCarteira = app.indexOf("function CarteiraScreen(");
if (inicioCarteira < 0) {
  console.error("FALHOU: função CarteiraScreen não encontrada em App.jsx — guardião não pode isolar o componente");
  process.exit(1);
}
const fimCarteira = app.indexOf("\nfunction ", inicioCarteira + 10);
const carteiraScreen = app.slice(inicioCarteira, fimCarteira > inicioCarteira ? fimCarteira : undefined);

// --- DEDUP-01: CapitalCurve existe em exatamente UMA tela ------------------

const totalCapitalCurve = (app.match(/<CapitalCurve/g) || []).length;
ok("DEDUP-01: exatamente 1 ocorrência de <CapitalCurve no arquivo inteiro", totalCapitalCurve === 1);

ok("DEDUP-01: a chamada sobrevivente de <CapitalCurve> está dentro de EvolucaoScreen", evolucaoScreen.includes("<CapitalCurve"));

ok("DEDUP-01: CarteiraScreen (rota Portfólio) NÃO contém <CapitalCurve", !carteiraScreen.includes("<CapitalCurve"));

// --- DEDUP-03: card consolidado 2×2 no lugar dos 4 cards kpi() -------------

ok("DEDUP-03: helper kpi( não existe mais em App.jsx", !/\bkpi\(/.test(app));

const numBodySpreadCount = (carteiraScreen.match(/\.\.\.numBody/g) || []).length;
ok("DEDUP-03: card consolidado usa ...numBody (pelo menos 4 ocorrências, uma por célula)", numBodySpreadCount >= 4);

const numMicroSpreadCount = (carteiraScreen.match(/\.\.\.numMicro/g) || []).length;
ok("DEDUP-03: card consolidado usa ...numMicro (pelo menos 1, sub-linha de percentual)", numMicroSpreadCount >= 1);

ok('DEDUP-03: grid 2 colunas presente (gridTemplateColumns: "1fr 1fr")', carteiraScreen.includes('gridTemplateColumns: "1fr 1fr"'));

ok("DEDUP-03: rótulo PATRIMÔNIO TOTAL presente em CarteiraScreen", carteiraScreen.includes("PATRIMÔNIO TOTAL"));
ok("DEDUP-03: rótulo RESULTADO ABERTO presente em CarteiraScreen", carteiraScreen.includes("RESULTADO ABERTO"));
ok("DEDUP-03: rótulo CAIXA DISPONÍVEL presente em CarteiraScreen", carteiraScreen.includes("CAIXA DISPONÍVEL"));
ok("DEDUP-03: rótulo EM POSIÇÕES presente em CarteiraScreen", carteiraScreen.includes("EM POSIÇÕES"));

ok("DEDUP-03: valor de patrimônio total continua vindo de {money(total)} (sem conta refeita no JSX)", carteiraScreen.includes("{money(total)}"));
ok("DEDUP-03: valor de resultado aberto continua vindo de {moneySigned(openPnL)}", carteiraScreen.includes("{moneySigned(openPnL)}"));
ok("DEDUP-03: sub-linha de percentual continua vindo de {pct(openPct)}", carteiraScreen.includes("{pct(openPct)}"));
ok("DEDUP-03: valor de caixa disponível continua vindo de {money(data.cash)}", carteiraScreen.includes("{money(data.cash)}"));
ok("DEDUP-03: valor em posições continua vindo de {money(positionsValue)}", carteiraScreen.includes("{money(positionsValue)}"));

ok(
  'DEDUP-03: grid antigo de 4 cards (gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))") não existe mais',
  !carteiraScreen.includes('gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))"')
);

console.log(fails === 0 ? "\ntodos os testes passaram — DEDUP-01 e DEDUP-03 (Fase 21, plano 21-01)" : `\n${fails} asserção(ões) falharam`);
process.exit(fails);
