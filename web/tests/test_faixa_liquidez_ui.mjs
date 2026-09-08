// Quick 260908-ldg (2026-09-08) — Task 3: gate de liquidez em três faixas no
// FRONT — paridade JS×Python da escala, consentimento explícito nos DOIS
// handlers de aceite, régua no ramo OFFLINE do deviceStore, ausência das
// strings do motor em web/src, e o chip de liquidez abrindo o verbete.
//
// Roda sem build: `node web/tests/test_faixa_liquidez_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { faixaDeLiquidez, FAIXA_NEGOCIAVEL_MIN, FAIXA_DIFICIL_MIN } from "../src/finance.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const financeJs = readFileSync(join(here, "..", "src", "finance.js"), "utf8");
const optionsQuantPy = readFileSync(join(here, "..", "..", "server", "app", "options_quant.py"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => { console.log((cond ? "ok " : "FALHOU ") + name + (extra ? ` (${extra})` : "")); if (!cond) fails++; };

function extrairBalanceado(src, openIdx) {
  let depth = 0, i = openIdx, inStr = null;
  for (; i < src.length; i++) {
    const c = src[i];
    if (inStr) {
      if (c === "\\") { i++; continue; }
      if (c === inStr) inStr = null;
      continue;
    }
    if (c === '"' || c === "'" || c === "`") { inStr = c; continue; }
    if (c === "(" || c === "{" || c === "[") depth++;
    else if (c === ")" || c === "}" || c === "]") { depth--; if (depth === 0) return src.slice(openIdx, i + 1); }
  }
  return src.slice(openIdx);
}

// ---------------------------------------------------------------------------
// 1) faixaDeLiquidez — comportamento (espelho de options_quant.faixa_de_liquidez)
// ---------------------------------------------------------------------------
ok("faixaDeLiquidez(66.5) === NEGOCIÁVEL", faixaDeLiquidez(66.5) === "NEGOCIÁVEL");
ok("faixaDeLiquidez(55) === NEGOCIÁVEL (fronteira)", faixaDeLiquidez(55) === "NEGOCIÁVEL");
ok("faixaDeLiquidez(46) === DIFÍCIL", faixaDeLiquidez(46) === "DIFÍCIL");
ok("faixaDeLiquidez(30) === DIFÍCIL (fronteira)", faixaDeLiquidez(30) === "DIFÍCIL");
ok("faixaDeLiquidez(29.6) === SEM MERCADO", faixaDeLiquidez(29.6) === "SEM MERCADO");
ok("faixaDeLiquidez(null) === SEM MERCADO", faixaDeLiquidez(null) === "SEM MERCADO");
ok("faixaDeLiquidez(undefined) === SEM MERCADO", faixaDeLiquidez(undefined) === "SEM MERCADO");
ok("faixaDeLiquidez(-1) === SEM MERCADO", faixaDeLiquidez(-1) === "SEM MERCADO");
ok("faixaDeLiquidez(NaN) === SEM MERCADO", faixaDeLiquidez(NaN) === "SEM MERCADO");
ok("faixaDeLiquidez('lixo') === SEM MERCADO (tipo errado nunca lança)", faixaDeLiquidez("lixo") === "SEM MERCADO");

// ---------------------------------------------------------------------------
// 2) Paridade byte-a-byte dos limiares — lê os DOIS arquivos-fonte
// ---------------------------------------------------------------------------
ok("finance.js exporta FAIXA_NEGOCIAVEL_MIN = 55", FAIXA_NEGOCIAVEL_MIN === 55);
ok("finance.js exporta FAIXA_DIFICIL_MIN = 30", FAIXA_DIFICIL_MIN === 30);
ok("options_quant.py declara LIQUIDEZ_NEGOCIAVEL = 55", /LIQUIDEZ_NEGOCIAVEL\s*=\s*55\b/.test(optionsQuantPy));
ok("options_quant.py declara LIQUIDEZ_DIFICIL = 30", /LIQUIDEZ_DIFICIL\s*=\s*30\b/.test(optionsQuantPy));
ok("options_quant.py declara FAIXA_NEGOCIAVEL = \"NEGOCIÁVEL\"", /FAIXA_NEGOCIAVEL\s*=\s*"NEGOCIÁVEL"/.test(optionsQuantPy));
ok("options_quant.py declara FAIXA_DIFICIL = \"DIFÍCIL\"", /FAIXA_DIFICIL\s*=\s*"DIFÍCIL"/.test(optionsQuantPy));
ok("options_quant.py declara FAIXA_SEM_MERCADO = \"SEM MERCADO\"", /FAIXA_SEM_MERCADO\s*=\s*"SEM MERCADO"/.test(optionsQuantPy));
ok("finance.js documenta o espelho (comentário aponta para options_quant.faixa_de_liquidez)",
  financeJs.includes("options_quant.faixa_de_liquidez"));

// ---------------------------------------------------------------------------
// 3) OpcaoContrato — literais 55/30 saíram do componente (usa faixaDeLiquidez)
// ---------------------------------------------------------------------------
(() => {
  const iOC = app.indexOf("function OpcaoContrato");
  const iFonteDoDado = app.indexOf("function FonteDoDadoProposta");
  ok("OpcaoContrato localizado antes de FonteDoDadoProposta", iOC > -1 && iFonteDoDado > iOC);
  const fatia = iOC > -1 && iFonteDoDado > iOC ? app.slice(iOC, iFonteDoDado) : "";
  ok("OpcaoContrato usa faixaDeLiquidez(", fatia.includes("faixaDeLiquidez("));
  ok("OpcaoContrato NÃO tem mais o literal >= 55 inline", !/liq\.score[\s\S]{0,10}>=\s*55/.test(fatia));
  ok("OpcaoContrato NÃO tem mais o literal >= 30 inline", !/liq\.score[\s\S]{0,10}>=\s*30/.test(fatia));
})();
ok("App.jsx importa faixaDeLiquidez de finance.js",
  /import \{[^}]*faixaDeLiquidez[^}]*\} from ".\/finance\.js"/.test(app));

// ---------------------------------------------------------------------------
// 4) Ordem dos dois confirms nos DOIS handlers de aceite (mesmo padrão de
//    test_opcoes_proposta_ui.mjs/test_opcoes_collar_ui.mjs — reafirmado aqui
//    como o guardião CENTRAL desta quick, autocontido).
// ---------------------------------------------------------------------------
(() => {
  const idxs = [];
  const reOnAbrir = /const onAbrirLastreada = async \(\) => \{/g;
  const reAceitar = /const aceitarCandidato = async \(p\) => \{/g;
  let m;
  while ((m = reOnAbrir.exec(app))) idxs.push(m.index);
  while ((m = reAceitar.exec(app))) idxs.push(m.index);
  idxs.sort((a, b) => a - b);
  ok("existem exatamente 2 handlers de aceite", idxs.length === 2, String(idxs.length));

  idxs.forEach((iInicio, n) => {
    const iFim = app.indexOf("const onFecharLastreada", iInicio);
    const handler = iFim > iInicio ? app.slice(iInicio, iFim) : "";
    ok(`handler #${n + 1}: liq = p.liquidez || {} declarado`, /const liq = p\.liquidez \|\| \{\};/.test(handler));
    ok(`handler #${n + 1}: liq.faixa === "DIFÍCIL" checado`, handler.includes('liq.faixa === "DIFÍCIL"'));
    ok(`handler #${n + 1}: motor mudo (sem aviso) aborta sem inventar texto`, /if \(!liq\.aviso\)/.test(handler));
    ok(`handler #${n + 1}: window.confirm(liq.aviso) presente`, handler.includes("window.confirm(liq.aviso)"));
    ok(`handler #${n + 1}: aceitaLiquidezDificil setado para true só após confirmar`,
      /aceitaLiquidezDificil = true;/.test(handler));

    const iLiq = handler.indexOf("window.confirm(liq.aviso)");
    const iCollarConfirm = handler.indexOf("window.confirm(cp.confirmAbrirCollar(");
    const iCobertaConfirm = handler.indexOf("window.confirm(cp.confirmAbrirCoberta(");
    if (iCollarConfirm > -1) {
      ok(`handler #${n + 1}: confirm de liquidez vem ANTES do confirm do collar`, iLiq > -1 && iLiq < iCollarConfirm);
    }
    if (iCobertaConfirm > -1) {
      ok(`handler #${n + 1}: confirm de liquidez vem ANTES do confirm da venda coberta`, iLiq > -1 && iLiq < iCobertaConfirm);
    }

    // Corpo enviado carrega aceitaLiquidezDificil — nos dois caminhos
    // (abrirCollar e abrirLastreada) deste MESMO handler.
    const iAbrirCollarCall = handler.indexOf("A.abrirCollar(");
    const iAbrirLastreadaCall = handler.indexOf("A.abrirLastreada(");
    if (iAbrirCollarCall > -1) {
      const corpo = extrairBalanceado(handler, iAbrirCollarCall + "A.abrirCollar".length);
      ok(`handler #${n + 1}: corpo de A.abrirCollar( carrega aceitaLiquidezDificil`, corpo.includes("aceitaLiquidezDificil"));
    }
    if (iAbrirLastreadaCall > -1) {
      const corpo = extrairBalanceado(handler, iAbrirLastreadaCall + "A.abrirLastreada".length);
      ok(`handler #${n + 1}: corpo de A.abrirLastreada( carrega aceitaLiquidezDificil`, corpo.includes("aceitaLiquidezDificil"));
    }
  });
})();

// ---------------------------------------------------------------------------
// 5) Chip de liquidez → verbete (D-09): abrirVerbete("liquidez-opcao", ...)
// ---------------------------------------------------------------------------
ok('App.jsx chama A.abrirVerbete("liquidez-opcao", ...)', /abrirVerbete\("liquidez-opcao"/.test(app));
ok("ChipDaProposta existe e trata k === \"liquidez\" como botão", /function ChipDaProposta/.test(app) && /c\.k === "liquidez"/.test(app));
ok("o botão de liquidez tem aria-label acessível", app.includes('aria-label="O que é liquidez de opção?"'));
ok("PropostaLastreada e CandidatoOpcao usam <ChipDaProposta (não mais <span cru para os chips)",
  (app.match(/<ChipDaProposta /g) || []).length === 2);

// ---------------------------------------------------------------------------
// 6) Ramo OFFLINE do deviceStore.optionsAbrirLastreada aplica a MESMA régua
// ---------------------------------------------------------------------------
(() => {
  const iMetodo = persistence.indexOf("async optionsAbrirLastreada(body)");
  const iProximoMetodo = persistence.indexOf("async optionsFecharLastreada(body)");
  ok("optionsAbrirLastreada localizado em persistence.js", iMetodo > -1 && iProximoMetodo > iMetodo);
  const fatia = iMetodo > -1 && iProximoMetodo > iMetodo ? persistence.slice(iMetodo, iProximoMetodo) : "";

  ok("ramo offline lê contrato.liquidity (não reimplementa liquidity_score)", fatia.includes("contrato.liquidity"));
  ok("ramo offline usa faixaDeLiquidez importado de finance.js", fatia.includes("faixaDeLiquidez("));
  ok("ramo offline NÃO reimplementa a fórmula (sem Math.log10 dentro do método)", !/Math\.log10/.test(fatia));
  ok('liquidity ausente/sem score vira erro nomeado ("medir a liquidez")', /não foi possível medir a liquidez/i.test(fatia));
  ok("SEM MERCADO sempre registra rejeição local e lança erro", /liqFaixa === "SEM MERCADO"[\s\S]{0,300}_registrarRejeicaoLocal/.test(fatia));
  ok("DIFÍCIL sem aceitaLiquidezDificil registra rejeição e lança erro",
    /liqFaixa === "DIFÍCIL" && body\.aceitaLiquidezDificil !== true/.test(fatia));

  // Ordem: a régua de liquidez vem ANTES de qualquer escrita em `doc.` —
  // localiza a primeira atribuição a `doc.` depois do início do método.
  const iPrimeiraEscritaDoc = fatia.search(/doc\.\w+\s*=/);
  const iChecagemSemMercado = fatia.indexOf('liqFaixa === "SEM MERCADO"');
  ok("régua de liquidez vem ANTES de qualquer escrita em doc.*",
    iChecagemSemMercado > -1 && (iPrimeiraEscritaDoc === -1 || iChecagemSemMercado < iPrimeiraEscritaDoc));
})();
ok("persistence.js importa faixaDeLiquidez de finance.js",
  /import \{[^}]*faixaDeLiquidez[^}]*\} from ".\/finance\.js"/.test(persistence));

// ---------------------------------------------------------------------------
// 7) Ausência das strings do motor em web/src (o front nunca compõe o aviso)
// ---------------------------------------------------------------------------
ok('App.jsx NÃO contém "sem livro publicado"', !app.includes("sem livro publicado"));
ok('App.jsx NÃO contém "unidades negociadas hoje"', !app.includes("unidades negociadas hoje"));
ok('App.jsx NÃO contém "poderia não ser atendida"', !app.includes("poderia não ser atendida"));
ok('persistence.js pode conter as mensagens do SERVIDOR (espelho, Task 2c) mas não o vocabulário do consentimento didático',
  !persistence.includes("unidades negociadas hoje") && !persistence.includes("sem livro publicado"));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
