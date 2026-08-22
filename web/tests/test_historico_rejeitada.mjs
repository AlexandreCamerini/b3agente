// FIX-C02 (REPORT-01, lado front) — guardião da ordem rejeitada visível no
// histórico, nos DOIS stores.
//
// Contrato:
//  (a) pill neutra + badge REJEITADA com T.warn, T.negative AUSENTE no ramo
//      rejeitado;
//  (b) — em RESULTADO e em PREÇO quando h.price == null;
//  (c) sub-linha "Rejeitada: " com T.warn;
//  (d) refresh no catch de confirmBuy/confirmSell, ANTES do flash;
//  (e) paridade: deviceStore grava status: "rejeitada" antes de cada throw
//      do ramo local, e status: "executada" no sucesso.
// Roda sem build: `node web/tests/test_historico_rejeitada.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------- localizar blocos
const iHistorico = app.indexOf("function HistoricoScreen(");
const iBuyModal = app.indexOf("function BuyModal(");
ok("HistoricoScreen localizado antes de BuyModal", iHistorico >= 0 && iBuyModal > iHistorico);
const historico = iHistorico >= 0 && iBuyModal > iHistorico ? app.slice(iHistorico, iBuyModal) : "";

const iMap = historico.indexOf("data.history.map(");
const iMapEnd = historico.indexOf("\n          })}", iMap);
const linhaHistorico = iMap >= 0 && iMapEnd > iMap ? historico.slice(iMap, iMapEnd) : "";
ok("bloco data.history.map localizado", linhaHistorico.length > 0);

// -------------------------------------------------------- (a) pill + badge
ok("HistoricoScreen contém h.status === \"rejeitada\" (condição SEMPRE ===, nunca !== \"executada\")",
   linhaHistorico.includes('h.status === "rejeitada"') && !linhaHistorico.includes('h.status !== "executada"'));
ok("badge literal REJEITADA presente", linhaHistorico.includes("REJEITADA"));
ok("badge REJEITADA usa T.warn (mesma forma do ordemPendentePill)",
   /\{rejeitada && <span style=\{\{ padding: "3px 9px", borderRadius: "999px", fontSize: "10\.5px", fontWeight: 800, color: T\.warn, background: "color-mix\(in srgb, " \+ T\.warn \+ " 14%, transparent\)" \}\}>REJEITADA<\/span>\}/.test(linhaHistorico));
// T.negative segue existindo no bloco para o ramo EXECUTADO (venda vermelha,
// PnL negativo) — o que a pill/resultado NUNCA podem fazer é usar T.negative
// especificamente quando rejeitada === true.
ok("nenhum ramo condicionado a `rejeitada` resolve para T.negative (pill neutra, não afirma execução)",
   !/rejeitada \? T\.negative/.test(linhaHistorico));
ok("T.textFaint e T.warn aparecem no bloco (pill neutra + badge)",
   /T\.textFaint/.test(linhaHistorico) && /T\.warn/.test(linhaHistorico));

// --------------------------------------------------- (b) traço no lugar de zero
ok("RESULTADO usa rejeitada ? \"—\" (nenhuma chamada de moneySigned nesse ramo)",
   /color: rejeitada \? T\.textFaint : \(h\.pnl == null \? T\.textFaint : h\.pnl >= 0 \? T\.positive : T\.negative\) \}\}>\{rejeitada \? "—" : \(h\.pnl == null \? "—" : moneySigned\(h\.pnl\)\)\}/.test(linhaHistorico));
ok("PREÇO usa \"—\" quando h.price == null",
   /\{h\.price == null \? "—" : "R\$ " \+ price\(h\.price\)\}/.test(linhaHistorico));

// ------------------------------------------------------- (c) sub-linha ----
ok('sub-linha "Rejeitada: " presente', linhaHistorico.includes("Rejeitada: "));
ok("sub-linha usa T.warn, fontSize 11px, mesma posição/estilo do ultimoErro",
   /\{rejeitada && h\.motivo && \(\s*<div style=\{\{ padding: "0 15px 9px", fontSize: "11px", color: T\.warn, lineHeight: 1\.4 \}\}>/.test(linhaHistorico));

// entrada legada (sem status) cai no ramo executado — não é rejeitada, então
// a sub-linha/badge não aparecem para ela (rejeitada é false quando
// h.status é undefined).
ok("entrada sem status (legada) resulta em rejeitada=false (=== \"rejeitada\", não truthy check solto)",
   linhaHistorico.includes('const rejeitada = h.status === "rejeitada";'));

// -------------------------------------------------- (d) refresh no catch --
const iConfirmSell = app.indexOf("confirmSell: async () => {");
const iConfirmBuy = app.indexOf("confirmBuy: async () => {");
const confirmSellBlock = app.slice(iConfirmSell, iConfirmSell + 1200);
const confirmBuyBlock = app.slice(iConfirmBuy, iConfirmBuy + 1700);

ok("confirmSell: catch chama store.getState() ANTES do flash",
   (() => {
     const iCatch = confirmSellBlock.indexOf("} catch (e) {");
     if (iCatch < 0) return false;
     const bloco = confirmSellBlock.slice(iCatch);
     const iGetState = bloco.indexOf("store.getState()");
     const iFlash = bloco.indexOf('flash("Venda: "');
     return iGetState >= 0 && iFlash > iGetState;
   })());
ok("confirmBuy: catch chama store.getState() ANTES do flash",
   (() => {
     const iCatch = confirmBuyBlock.indexOf("catch (e) {");
     if (iCatch < 0) return false;
     const bloco = confirmBuyBlock.slice(iCatch);
     const iGetState = bloco.indexOf("store.getState()");
     const iFlash = bloco.indexOf('flash("Compra: "');
     return iGetState >= 0 && iFlash > iGetState;
   })());

// --------------------------------------------------- (e) paridade deviceStore
ok("deviceStore._registrarRejeicaoLocal existe e grava status: \"rejeitada\"",
   /function _registrarRejeicaoLocal\(tipo, t, qty, price, motivo\) \{[\s\S]*?status: "rejeitada"/.test(persistence));
ok("buy() local: _registrarRejeicaoLocal → write() → throw, nesta ordem (\"Caixa insuficiente.\")",
   (() => {
     const i = persistence.indexOf('if (qty * price > doc.cash) {');
     if (i < 0) return false;
     const bloco = persistence.slice(i, i + 500);
     const iReg = bloco.indexOf("_registrarRejeicaoLocal(");
     const iWrite = bloco.indexOf("write();");
     const iThrow = bloco.indexOf("throw new Error(motivo);");
     return iReg >= 0 && iWrite > iReg && iThrow > iWrite;
   })());
ok("sell() local: _registrarRejeicaoLocal → write() → throw, nesta ordem (\"Sem posicao em\")",
   (() => {
     const i = persistence.indexOf("if (!pos) {");
     if (i < 0) return false;
     const bloco = persistence.slice(i, i + 500);
     const iReg = bloco.indexOf("_registrarRejeicaoLocal(");
     const iWrite = bloco.indexOf("write();");
     const iThrow = bloco.indexOf("throw new Error(motivo);");
     return iReg >= 0 && iWrite > iReg && iThrow > iWrite;
   })());
ok("entrada de sucesso da COMPRA local grava status: \"executada\"",
   /type: "COMPRA", t, qty, price: \+price\.toFixed\(2\), pnl: null, status: "executada" \}/.test(persistence));
ok("entrada de sucesso da VENDA local grava status: \"executada\"",
   /type: "VENDA", t, qty: sold, price: \+price\.toFixed\(2\), pnl, status: "executada" \}/.test(persistence));
ok("CAP_REJEICOES_LOCAL = 100 espelha store.py.CAP_REJEICOES",
   /const CAP_REJEICOES_LOCAL = 100;/.test(persistence));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
