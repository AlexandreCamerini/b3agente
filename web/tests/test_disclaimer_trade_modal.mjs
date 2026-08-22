// FIX-C13/FIX-C14 (REPORT-01) — guardião do disclaimer de operação simulada
// e da declaração tudo-ou-nada nos modais de compra/venda.
//
// Contrato:
//  (a) DISCLAIMERS.trade renderiza em BuyModal e SellModal;
//  (b) posicionado ANTES da linha de botões em cada um (índice de string);
//  (c) a frase de tudo-ou-nada presente nos dois modais;
//  (d) a string de disclaimers.js permanece inalterada byte a byte;
//  (e) CLAUDE.md contém a declaração de tudo-ou-nada, citando C-14.
// Roda sem build: `node web/tests/test_disclaimer_trade_modal.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const disclaimers = readFileSync(join(here, "..", "src", "disclaimers.js"), "utf8");
const claudeMd = readFileSync(join(here, "..", "..", "CLAUDE.md"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// -------------------------------------------------------- localizar blocos
const iBuyStart = app.indexOf("function BuyModal(");
const iSellStart = app.indexOf("function SellModal(");
const candEndFn = app.indexOf("\nfunction ", iSellStart + 1);
const candEndExport = app.indexOf("\nexport default function ", iSellStart + 1);
const iSellEnd = [candEndFn, candEndExport].filter((n) => n >= 0).sort((a, b) => a - b)[0] ?? -1;
ok("BuyModal localizado antes de SellModal", iBuyStart >= 0 && iSellStart > iBuyStart);
ok("SellModal tem fim localizável", iSellEnd > iSellStart);
const buy = iBuyStart >= 0 && iSellStart > iBuyStart ? app.slice(iBuyStart, iSellStart) : "";
const sell = iSellStart >= 0 && iSellEnd > iSellStart ? app.slice(iSellStart, iSellEnd) : "";

// --------------------------------------------------- (a) DISCLAIMERS.trade
const totalTrade = (app.match(/DISCLAIMERS\.trade/g) || []).length;
ok("DISCLAIMERS.trade aparece exatamente 2x no arquivo (BuyModal + SellModal)", totalTrade === 2);
ok("BuyModal renderiza DISCLAIMERS.trade", buy.includes("DISCLAIMERS.trade"));
ok("SellModal renderiza DISCLAIMERS.trade", sell.includes("DISCLAIMERS.trade"));

// ------------------------------------------- (b) acima da linha de botões
const iTradeBuy = buy.indexOf("DISCLAIMERS.trade");
const iBtnBuy = buy.indexOf("A.confirmBuy");
ok("no BuyModal, DISCLAIMERS.trade vem ANTES do botão de confirmar",
   iTradeBuy >= 0 && iBtnBuy > iTradeBuy);

const iTradeSell = sell.indexOf("DISCLAIMERS.trade");
const iBtnSell = sell.indexOf("A.confirmSell");
ok("no SellModal, DISCLAIMERS.trade vem ANTES do botão de confirmar",
   iTradeSell >= 0 && iBtnSell > iTradeSell);

// estilo: 10.5px, T.textFaint, lineHeight 1.4, marginTop 10px — um degrau
// mais discreto que a nota secundária (11px) logo acima.
ok("estilo do disclaimer é 10.5px/T.textFaint/lineHeight 1.4/marginTop 10px no BuyModal",
   /fontSize: "10\.5px", color: T\.textFaint, lineHeight: 1\.4, marginTop: "10px" \}\}>\{DISCLAIMERS\.trade\}/.test(buy));
ok("estilo do disclaimer é 10.5px/T.textFaint/lineHeight 1.4/marginTop 10px no SellModal",
   /fontSize: "10\.5px", color: T\.textFaint, lineHeight: 1\.4, marginTop: "10px" \}\}>\{DISCLAIMERS\.trade\}/.test(sell));

// ------------------------------------------------- (c) tudo-ou-nada na UI
const FRASE_TUDO_OU_NADA = "Esta simulação executa por completo ou não executa — não há preenchimento parcial de ordem.";
const totalFrase = (app.match(/Esta simulação executa por completo ou não executa — não há preenchimento parcial de ordem\./g) || []).length;
ok("a frase de tudo-ou-nada aparece pelo menos 2x (Buy + Sell)", totalFrase >= 2);
ok("BuyModal contém a frase de tudo-ou-nada", buy.includes(FRASE_TUDO_OU_NADA));
ok("SellModal contém a frase de tudo-ou-nada", sell.includes(FRASE_TUDO_OU_NADA));

// nenhum badge/modal/coluna novo de fill parcial foi introduzido
ok("nenhuma ocorrência de \"parcialmente executada\" (fill parcial não foi implementado)",
   !/parcialmente executada/i.test(app));

// --------------------------------------------- (d) disclaimers.js intacto
ok("disclaimers.js preserva a string trade verbatim (FIX-C13 é só render, zero copy nova)",
   disclaimers.includes('trade:\n    "Operação SIMULADA (paper trading). Nenhuma ordem real é enviada a uma corretora."'));

// -------------------------------------------------------- (e) CLAUDE.md --
ok("CLAUDE.md declara a execução tudo-ou-nada", /tudo-ou-nada/.test(claudeMd));
ok("CLAUDE.md cita o achado C-14 na declaração de tudo-ou-nada", /C-14/.test(claudeMd));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
