// Quick 260915-j5l — Guardião de `executarCandidato.js`: despacho por tipo
// (call_coberta/put_protecao/collar/opcao_a_descoberto) para o método de
// store correto, com o corpo EXATO que cada rota real exige (ver bloco
// <interfaces> do plano, verificado contra server/app/main.py e
// server/app/opcoes_curadoria.py nesta sessão).
//
// Mesmo padrão "Node puro, sem DOM" de test_estrutura_para_payoff.mjs: import
// direto do módulo, contador `fails` + helper `ok`. `store` é um espião
// literal — nenhum fetch real, nenhum mock de rede.
import { corpoDoCandidato, executarCandidato } from "../src/opcoes/executarCandidato.js";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Deep-equal estrita (chave a chave, incluindo ausência) — sem depender de
// ordem de inserção.
function mesmoObjeto(a, b) {
  if (a === b) return true;
  if (typeof a !== "object" || typeof b !== "object" || a === null || b === null) return false;
  const ka = Object.keys(a).sort();
  const kb = Object.keys(b).sort();
  if (JSON.stringify(ka) !== JSON.stringify(kb)) return false;
  return ka.every((k) => mesmoObjeto(a[k], b[k]) || a[k] === b[k]);
}

// ---- fixtures — um candidato por tipo, campos reais de opcoes_curadoria.py
const callCoberta = {
  tipo: "call_coberta", ticker: "PETR4", contractSymbol: "PETRC123",
  expiration: "2026-10-16", contratos: 2, qtyAcoes: 200,
  premioUnitario: 1.5, premioTotal: 300, idCandidato: "id-call-1",
  liquidez: { faixa: "BOA", aviso: null },
  estrutura: { ganho_maximo: 300, perda_maxima: null, perda_ilimitada: false, breakevens: [30.5] },
};

const putProtecao = {
  tipo: "put_protecao", ticker: "PETR4", contractSymbol: "PETRP456",
  expiration: "2026-10-16", contratos: 2, qtyAcoes: 200,
  premioUnitario: 0.8, premioTotal: 160, idCandidato: "id-put-1",
  liquidez: { faixa: "BOA", aviso: null },
};

const collar = {
  tipo: "collar", ticker: "VALE3", contractSymbol: null,
  expiration: "2026-11-20", contratos: 1, qtyAcoes: 100,
  strikeCall: 70, strikePut: 60,
  pernasContratos: [
    { contractSymbol: "VALEC1", optionType: "call", lado: "venda", strike: 70, premioUnitario: 2.1 },
    { contractSymbol: "VALEP1", optionType: "put", lado: "compra", strike: 60, premioUnitario: 1.3 },
  ],
  premioUnitario: 0.8, premioTotal: 80, idCandidato: "id-collar-1",
  liquidez: { faixa: "REGULAR", aviso: null },
};

const descoberto = {
  tipo: "opcao_a_descoberto", ticker: "ITUB4", contractSymbol: "ITUBC789",
  expiration: "2026-10-16", contratos: 1, qtyAcoes: 100,
  premioUnitario: 0.5, premioTotal: 50, idCandidato: "id-desc-1",
  liquidez: { faixa: "DIFÍCIL", aviso: "Liquidez DIFÍCIL (score 40/100) — negociação rarefeita." },
};

// ---- store espião: registra {metodo, body}, nenhum fetch real -------------
function storeEspiao() {
  const chamadas = [];
  return {
    chamadas,
    optionsAbrirLastreada: (body) => { chamadas.push({ metodo: "optionsAbrirLastreada", body }); return Promise.resolve({ fake: "lastreada" }); },
    optionsAbrirCollar: (body) => { chamadas.push({ metodo: "optionsAbrirCollar", body }); return Promise.resolve({ fake: "collar" }); },
    // Quick 260915-ndt: método NOVO (chave nomeada aqui achada pelo
    // plan-checker — sem ela o espião não tem `store[metodo]` e o despacho
    // do collar vira TypeError síncrono, não uma asserção que falha).
    optionsCuradoriaAbrirCollar: (body) => { chamadas.push({ metodo: "optionsCuradoriaAbrirCollar", body }); return Promise.resolve({ fake: "collar-curado" }); },
    optionsBuy: (body) => { chamadas.push({ metodo: "optionsBuy", body }); return Promise.resolve({ fake: "buy" }); },
  };
}

// ---- (1) call_coberta → optionsAbrirLastreada, corpo idêntico -------------
const r1 = corpoDoCandidato(callCoberta);
ok("call_coberta resolve metodo optionsAbrirLastreada", r1.metodo === "optionsAbrirLastreada");
ok("call_coberta: corpo idêntico (underlying/contractSymbol/expiration/contratos, SEM aceitaLiquidezDificil)",
  mesmoObjeto(r1.body, { underlying: "PETR4", contractSymbol: "PETRC123", expiration: "2026-10-16", contratos: 2 }));
ok("call_coberta: aceitaLiquidezDificil AUSENTE do corpo por padrão", !("aceitaLiquidezDificil" in r1.body));

// ---- (2) put_protecao → MESMA rota/corpo -----------------------------------
const r2 = corpoDoCandidato(putProtecao);
ok("put_protecao resolve metodo optionsAbrirLastreada (mesma rota da call)", r2.metodo === "optionsAbrirLastreada");
ok("put_protecao: corpo idêntico",
  mesmoObjeto(r2.body, { underlying: "PETR4", contractSymbol: "PETRP456", expiration: "2026-10-16", contratos: 2 }));

// ---- (3) collar → optionsCuradoriaAbrirCollar, 2 pernas SÓ contractSymbol+lado
// REVERSÃO DELIBERADA (2026-09-15, quick 260915-ndt): antes desta quick, o
// collar ia para `optionsAbrirCollar` (rota `/lastreada/abrir-collar`, que
// re-deriva por `opcoes_lastreadas.propor()` e 409ava todo collar curado
// quando a leitura técnica não endossava collar — o caso comum). Agora vai
// para `optionsCuradoriaAbrirCollar` (rota `/curadoria/abrir-collar`, que
// re-deriva pelo motor que gerou o card), com `idCandidato` no corpo no
// lugar de `expiration` (o id já carrega a expiração).
const r3 = corpoDoCandidato(collar);
ok("collar resolve metodo optionsCuradoriaAbrirCollar", r3.metodo === "optionsCuradoriaAbrirCollar");
ok("collar: exatamente 2 pernas", Array.isArray(r3.body.pernasContratos) && r3.body.pernasContratos.length === 2);
ok("collar: cada perna tem SOMENTE contractSymbol e lado (Object.keys === 2)",
  r3.body.pernasContratos.every((p) => Object.keys(p).length === 2 && "contractSymbol" in p && "lado" in p));
ok("collar: corpo idêntico (underlying/idCandidato/pernasContratos/contratos, SEM expiration/strike/prêmio)",
  mesmoObjeto(r3.body, {
    underlying: "VALE3",
    idCandidato: "id-collar-1",
    pernasContratos: [{ contractSymbol: "VALEC1", lado: "venda" }, { contractSymbol: "VALEP1", lado: "compra" }],
    contratos: 1,
  }));

// ---- (4) opcao_a_descoberto → optionsBuy, qty=qtyAcoes, SEM liquidez -------
const r4 = corpoDoCandidato(descoberto);
ok("opcao_a_descoberto resolve metodo optionsBuy", r4.metodo === "optionsBuy");
ok("opcao_a_descoberto: corpo idêntico (underlying/contractSymbol/expiration/qty)",
  mesmoObjeto(r4.body, { underlying: "ITUB4", contractSymbol: "ITUBC789", expiration: "2026-10-16", qty: 100 }));
ok("opcao_a_descoberto: qty === cand.qtyAcoes", r4.body.qty === descoberto.qtyAcoes);
ok("opcao_a_descoberto: aceitaLiquidezDificil NUNCA existe no corpo (a rota não aceita)",
  !("aceitaLiquidezDificil" in r4.body));

// ---- (5) aceitaLiquidezDificil: true entra SÓ em lastreada/collar ---------
const r5a = corpoDoCandidato(callCoberta, { aceitaLiquidezDificil: true });
ok("call_coberta com consentimento: aceitaLiquidezDificil === true (identidade)", r5a.body.aceitaLiquidezDificil === true);
const r5b = corpoDoCandidato(collar, { aceitaLiquidezDificil: true });
ok("collar com consentimento: aceitaLiquidezDificil === true (identidade)", r5b.body.aceitaLiquidezDificil === true);
ok("collar com consentimento: metodo continua optionsCuradoriaAbrirCollar", r5b.metodo === "optionsCuradoriaAbrirCollar");
const r5c = corpoDoCandidato(descoberto, { aceitaLiquidezDificil: true });
ok("opcao_a_descoberto com consentimento: aceitaLiquidezDificil AINDA AUSENTE (rota sem gate de liquidez)",
  !("aceitaLiquidezDificil" in r5c.body));
// Identidade, não truthiness: um valor truthy que não é `true` estrito não entra.
const r5d = corpoDoCandidato(callCoberta, { aceitaLiquidezDificil: "sim" });
ok("call_coberta com aceitaLiquidezDificil truthy MAS não === true: chave ausente (identidade, não truthiness)",
  !("aceitaLiquidezDificil" in r5d.body));

// ---- (6) tipo desconhecido / candidato nulo → lança, store espião intocado
let lancouTipoDesconhecido = false;
try { corpoDoCandidato({ tipo: "estrangulamento", ticker: "X" }); } catch (e) { lancouTipoDesconhecido = e instanceof Error; }
ok("tipo desconhecido lança Error nomeado", lancouTipoDesconhecido);

let lancouNulo = false;
try { corpoDoCandidato(null); } catch (e) { lancouNulo = e instanceof Error; }
ok("candidato null lança Error", lancouNulo);

let lancouUndefined = false;
try { corpoDoCandidato(undefined); } catch (e) { lancouUndefined = e instanceof Error; }
ok("candidato undefined lança Error", lancouUndefined);

// candidato incompleto do próprio tipo (sem contractSymbol) também lança —
// nunca devolve corpo meia-boca (a action do plano proíbe explicitamente).
let lancouIncompleto = false;
try { corpoDoCandidato({ tipo: "call_coberta", ticker: "PETR4" }); } catch (e) { lancouIncompleto = e instanceof Error; }
ok("call_coberta sem contractSymbol lança Error (nunca corpo incompleto)", lancouIncompleto);

let lancouCollarIncompleto = false;
try { corpoDoCandidato({ tipo: "collar", ticker: "VALE3", contratos: 1, idCandidato: "x", pernasContratos: [{ contractSymbol: "A", lado: "venda" }] }); } catch (e) { lancouCollarIncompleto = e instanceof Error; }
ok("collar com só 1 perna lança Error (exige exatamente 2)", lancouCollarIncompleto);

// Caso NOVO (quick 260915-ndt): collar sem idCandidato lança ANTES de
// tocar store nenhum — idCandidato é a CHAVE de re-derivação server-side
// (ADR-026 D2), sem ela a rota nova não tem como recalcular a estrutura.
let lancouCollarSemIdCandidato = false;
const espiaoSemId = storeEspiao();
try {
  await executarCandidato(
    { tipo: "collar", ticker: "VALE3", contratos: 1, pernasContratos: collar.pernasContratos },
    { store: espiaoSemId },
  );
} catch (e) { lancouCollarSemIdCandidato = e instanceof Error; }
ok("collar sem idCandidato lança Error e NÃO chama store nenhum",
  lancouCollarSemIdCandidato && espiaoSemId.chamadas.length === 0);

// executarCandidato: despacha para o store espião correto e NUNCA chama
// store nenhum quando o tipo é inválido.
const espiao1 = storeEspiao();
await executarCandidato(callCoberta, { store: espiao1 });
ok("executarCandidato(call_coberta) chamou store.optionsAbrirLastreada exatamente 1x",
  espiao1.chamadas.length === 1 && espiao1.chamadas[0].metodo === "optionsAbrirLastreada");

const espiao2 = storeEspiao();
await executarCandidato(collar, { store: espiao2, aceitaLiquidezDificil: true });
ok("executarCandidato(collar, consentido) chamou store.optionsCuradoriaAbrirCollar com aceitaLiquidezDificil true",
  espiao2.chamadas.length === 1 && espiao2.chamadas[0].metodo === "optionsCuradoriaAbrirCollar"
  && espiao2.chamadas[0].body.aceitaLiquidezDificil === true);

const espiao3 = storeEspiao();
await executarCandidato(descoberto, { store: espiao3 });
ok("executarCandidato(opcao_a_descoberto) chamou store.optionsBuy exatamente 1x",
  espiao3.chamadas.length === 1 && espiao3.chamadas[0].metodo === "optionsBuy");

const espiaoInvalido = storeEspiao();
let lancouViaExecutar = false;
try { await executarCandidato({ tipo: "invalido" }, { store: espiaoInvalido }); } catch (e) { lancouViaExecutar = e instanceof Error; }
ok("executarCandidato com tipo inválido lança e NÃO chama store nenhum", lancouViaExecutar && espiaoInvalido.chamadas.length === 0);

const espiaoNulo = storeEspiao();
let lancouNuloViaExecutar = false;
try { await executarCandidato(null, { store: espiaoNulo }); } catch (e) { lancouNuloViaExecutar = e instanceof Error; }
ok("executarCandidato com candidato null lança e NÃO chama store nenhum", lancouNuloViaExecutar && espiaoNulo.chamadas.length === 0);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
