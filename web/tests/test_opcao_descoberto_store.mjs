// FASE 29 (Plano 02) — Guardião: flag de opção a descoberto no deviceStore.
//
// O QUE ISTO PROTEGE: `deviceStore.optionsBuy` (`web/src/persistence.js`)
// tem um ramo LOCAL (iPhone sem sessão) que reimplementa `store.buy_option`
// inteiro em JavaScript — é a ÚNICA superfície de todo o app capaz de abrir
// uma posição de opção A SECO sem passar pelo gate do backend (29-01). Sem
// este guardião, três classes de regressão silenciosa passariam despercebido
// pela suíte canônica, porque nenhum outro teste executa este ramo:
//   1. alguém remove o `if (!doc.config.permitirOpcaoADescoberto)` do ramo
//      local — o gate do backend continua de pé, mas o iPhone offline abre
//      posição a seco de novo (T-29-06);
//   2. a mensagem de recusa diverge de `store.py` por uma letra — duas
//      redações da mesma regra, incidente clássico de fonte não-única
//      (T-29-08, mesma classe de `defaults.py`↔`catalog.js` do CLAUDE.md);
//   3. alguém "conserta" `optionsSell` pondo o mesmo gate nela — trancaria o
//      usuário dentro da própria posição se ele desligar o flag depois de
//      abrir (T-29-07, guardrail "Stop/alvo nunca são vetados").
//
// Cobre, nesta ordem: Grupo A (paridade da mensagem, byte a byte, lida dos
// dois arquivos do disco), Grupo B (forma do gate, source assertions
// fatiadas por marcador — números de linha envelhecem, marcadores não),
// Grupo C (comportamento do deviceStore com `api`/`fetch` mockados, SEM
// sessão) e Grupo D (sync device→servidor, COM sessão).
//
// Roda sem build: `node web/tests/test_opcao_descoberto_store.mjs` (de
// dentro de `web/`, ou com o caminho completo — o runner do
// `scripts/executar.sh` faz glob em `web/tests/*.mjs`).

import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const persistenciaSrc = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const storePySrc = readFileSync(join(here, "..", "..", "server", "app", "store.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// =========================================================== Grupo A =======
// Paridade byte a byte da mensagem única do gate. Falha EXPLÍCITA se o
// regex não conseguir extrair o literal de qualquer um dos dois arquivos —
// nunca passa por vacuidade (mesma disciplina de defaults.py↔catalog.js).
// `motivoEsperado` é hasteado para fora do bloco: os testes comportamentais
// do Grupo C reusam o MESMO valor já verificado, em vez de redigitar a
// string (redigitar aqui derrotaria o propósito do guardião).
let motivoEsperado = null;
{
  const mJs = persistenciaSrc.match(/const MOTIVO_DESCOBERTO_DESLIGADO = "((?:[^"\\]|\\.)*)";/);
  const mPy = storePySrc.match(/MOTIVO_DESCOBERTO_DESLIGADO = \(\s*"((?:[^"\\]|\\.)*)"\s*"((?:[^"\\]|\\.)*)"\s*\)/);
  if (!mJs) {
    console.error("FALHOU: não consegui extrair MOTIVO_DESCOBERTO_DESLIGADO de persistence.js — a constante mudou de forma, o guardião não pode passar sem conseguir lê-la");
    fails++;
  }
  if (!mPy) {
    console.error("FALHOU: não consegui extrair MOTIVO_DESCOBERTO_DESLIGADO de store.py — a constante mudou de forma, o guardião não pode passar sem conseguir lê-la");
    fails++;
  }
  if (mJs && mPy) {
    motivoEsperado = mJs[1];
    const valorPy = mPy[1] + mPy[2];
    ok("mensagem do gate é byte a byte igual em persistence.js e store.py", mJs[1] === valorPy);
  }
}

// =========================================================== Grupo B =======
// Forma do gate — fatiado por marcador (função test_fase3_paridade_..., o
// mesmo truque desta casa: números de linha envelhecem, marcadores não).
const iServerStore = persistenciaSrc.indexOf("function serverStore()");
const iDeviceStore = persistenciaSrc.indexOf("function deviceStore()");
const iBuy = persistenciaSrc.indexOf("async optionsBuy(body) {");
const iSell = persistenciaSrc.indexOf("async optionsSell(body) {");
const iPutOptionPosition = persistenciaSrc.indexOf("async putOptionPosition(");
if (
  iServerStore < 0 || iDeviceStore < 0 || iBuy < 0 || iSell < 0 || iPutOptionPosition < 0 ||
  !(iServerStore < iDeviceStore && iDeviceStore < iBuy && iBuy < iSell && iSell < iPutOptionPosition)
) {
  console.error("FALHOU: persistence.js foi reestruturado — marcadores de serverStore()/deviceStore()/optionsBuy/optionsSell/putOptionPosition não encontrados na ordem esperada");
  process.exit(1);
}
const serverStoreBody = persistenciaSrc.slice(iServerStore, iDeviceStore);
const optionsBuyBody = persistenciaSrc.slice(iBuy, iSell);
const optionsSellBody = persistenciaSrc.slice(iSell, iPutOptionPosition);

ok("optionsBuy (ramo local) referencia permitirOpcaoADescoberto", optionsBuyBody.includes("permitirOpcaoADescoberto"));

{
  const idxFlag = optionsBuyBody.indexOf("permitirOpcaoADescoberto");
  const idxChain = optionsBuyBody.indexOf("api.optionsChain");
  ok("gate roda ANTES do fetch da cadeia de opções (não queima requisição do provedor)", idxFlag >= 0 && idxChain >= 0 && idxFlag < idxChain);
}

ok("optionsSell NÃO referencia permitirOpcaoADescoberto — decisão SC-4/T-29-07, fechar nunca é vetado", !optionsSellBody.includes("permitirOpcaoADescoberto"));

ok("serverStore não tem nenhuma linha do flag — a mudança é toda do deviceStore, por desenho (optConfig já é genérico)",
  !serverStoreBody.includes("permitirOpcaoADescoberto") && !serverStoreBody.includes("descobertoTermo"));

ok("regra de aceite no putConfig está na forma negativa esperada (mesmo padrão de operadorTermo)",
  persistenciaSrc.includes('if (!(patch.permitirOpcaoADescoberto && !(c.descobertoTermo'));

// =========================================================== Grupo C+D =====
// Instância real do deviceStore, `api`/`fetch` mockados. Ambiente nativo
// (iPhone) simulado ANTES do import — mesmo padrão de
// test_appmode_sincroniza_servidor.mjs.
globalThis.CapacitorCustomPlatform = { name: "ios" };
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => { mem.set(k, String(v)); },
  removeItem: (k) => { mem.delete(k); },
};

const CONTRATO_TESTE = { contractSymbol: "TESTE29D001", optionType: "CALL", strike: 30, lastPrice: 1.5, impliedVolatility: 0.3 };
const CHAIN_OK = { providerStatus: "ok", expiration: "2026-12-18", calls: [CONTRATO_TESTE], puts: [] };

const chamadas = [];
globalThis.fetch = async (url, opts) => {
  const method = (opts && opts.method) || "GET";
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  chamadas.push({ url: String(url), method, body });
  if (/\/api\/options\/chain\//.test(url)) {
    return { ok: true, status: 200, text: async () => JSON.stringify(CHAIN_OK) };
  }
  if (/\/api\/config$/.test(url) && method === "PUT") {
    return { ok: true, status: 200, text: async () => JSON.stringify({ ok: true }) };
  }
  return { ok: true, status: 200, text: async () => JSON.stringify({}) };
};

const chamadasDeChain = () => chamadas.filter((c) => /\/api\/options\/chain\//.test(c.url)).length;

const { store, isNative } = await import("../src/persistence.js");
const sync = await import("../src/sync.js");

ok("ambiente nativo detectado (deviceStore em uso)", isNative === true);

// ---- Grupo C.1 — default do doc novo ---------------------------------------
{
  const s = await store.getState();
  ok("default: permitirOpcaoADescoberto nasce false", s.config.permitirOpcaoADescoberto === false);
  ok("default: descobertoTermo nasce null", s.config.descobertoTermo === null);
}

// ---- Grupo C.2 — gate: sem sessão, flag desligado --------------------------
{
  chamadas.length = 0;
  const antes = await store.getState();
  let erro = null;
  try {
    await store.optionsBuy({ underlying: "PETR4", contractSymbol: CONTRATO_TESTE.contractSymbol, expiration: CHAIN_OK.expiration, qty: 100 });
  } catch (e) { erro = e; }
  ok("compra a seco com flag desligado É RECUSADA (lança Error)", erro instanceof Error);
  ok("a mensagem da recusa é exatamente a constante do gate (mesmo valor verificado no Grupo A)",
    !!motivoEsperado && !!erro && erro.message === motivoEsperado);
  const depois = await store.getState();
  ok("optionPositions inalterado após a recusa", JSON.stringify(depois.optionPositions) === JSON.stringify(antes.optionPositions));
  ok("cash inalterado após a recusa", depois.cash === antes.cash);
  ok("history[0] registrou a rejeição (COMPRA, status rejeitada, price null)",
    depois.history[0] && depois.history[0].status === "rejeitada" && depois.history[0].type === "COMPRA" && depois.history[0].price === null);
  ok("api.optionsChain NÃO foi chamado — o gate não queima requisição do provedor", chamadasDeChain() === 0);
}

// ---- Grupo C.3 — putConfig: regra de aceite --------------------------------
{
  await store.putConfig({ permitirOpcaoADescoberto: true });
  const s = await store.getState();
  ok("ligar SEM termo aceito não liga (silencioso, igual operadorTermo)", s.config.permitirOpcaoADescoberto === false);
}
{
  const termo = { aceitoEm: "2026-09-13T00:00:00.000Z", versao: "1.0" };
  await store.putConfig({ descobertoTermo: termo, permitirOpcaoADescoberto: true });
  const s = await store.getState();
  ok("ligar COM termo no MESMO patch liga de verdade", s.config.permitirOpcaoADescoberto === true);
  ok("descobertoTermo foi gravado com os limites certos", s.config.descobertoTermo && s.config.descobertoTermo.versao === "1.0" && s.config.descobertoTermo.aceitoEm === termo.aceitoEm);
}
{
  await store.putConfig({ permitirOpcaoADescoberto: false });
  const s = await store.getState();
  ok("desligar é sempre livre", s.config.permitirOpcaoADescoberto === false);
  ok("desligar NÃO apaga descobertoTermo (religar não pede releitura)", s.config.descobertoTermo && s.config.descobertoTermo.versao === "1.0");
}

// ---- Grupo C.4 — gate: sem sessão, flag ligado (compra deve executar) -----
{
  await store.putConfig({ permitirOpcaoADescoberto: true }); // termo já aceito acima — religa sem reenviar
  const antes = await store.getState();
  ok("religar sem reenviar termo funciona (termo já aceito)", antes.config.permitirOpcaoADescoberto === true);
  chamadas.length = 0;
  const r = await store.optionsBuy({ underlying: "PETR4", contractSymbol: CONTRATO_TESTE.contractSymbol, expiration: CHAIN_OK.expiration, qty: 100 });
  ok("com o flag ligado, a compra a seco EXECUTA (posição criada)", Array.isArray(r.optionPositions) && r.optionPositions.some((p) => p.id === CONTRATO_TESTE.contractSymbol));
  ok("caixa foi debitado pelo prêmio", r.cash < antes.cash);
}

// ---- Grupo C.5 — SC-4: desligar DEPOIS de aberta não impede fechar ---------
{
  await store.putConfig({ permitirOpcaoADescoberto: false });
  const antes = await store.getState();
  ok("flag desligado, posição a seco continua aberta", antes.optionPositions.some((p) => p.id === CONTRATO_TESTE.contractSymbol));
  chamadas.length = 0;
  const r = await store.optionsSell({ contractSymbol: CONTRATO_TESTE.contractSymbol });
  ok("com o flag DESLIGADO, optionsSell EXECUTA (fechar nunca é vetado)", !r.optionPositions.some((p) => p.id === CONTRATO_TESTE.contractSymbol));
  ok("caixa foi creditado pela venda", r.cash > antes.cash);
}

// ---- Grupo C.6 — doc com lixo é saneado (fail-closed) ----------------------
{
  store._setDeviceScope("guardiao-lixo-29-02");
  // Doc RAW com lixo — escrito direto na chave escopada, sem passar por
  // nenhum putConfig (simula doc antigo/corrompido lido do disco).
  await store.getState(); // materializa o doc default no escopo novo
  const rawKey = "b3-agente-state-v1::u:guardiao-lixo-29-02";
  const raw = JSON.parse(mem.get(rawKey));
  raw.config.permitirOpcaoADescoberto = "true"; // string, não booleano — lixo clássico
  raw.config.descobertoTermo = "nao-e-objeto"; // string, não {aceitoEm, versao}
  mem.set(rawKey, JSON.stringify(raw));
  // Força novo load: o deviceStore só recarrega quando `_setDeviceScope`
  // recebe um id DIFERENTE do atual — usa um escopo intermediário para
  // forçar o `doc = null` antes de voltar ao escopo com o lixo.
  store._setDeviceScope("guardiao-lixo-intermediario-29-02");
  store._setDeviceScope("guardiao-lixo-29-02");
  const s = await store.getState();
  ok("doc com permitirOpcaoADescoberto='true' (string) é saneado para false", s.config.permitirOpcaoADescoberto === false);
  ok("doc com descobertoTermo não-objeto é saneado para null", s.config.descobertoTermo === null);
  store._setDeviceScope(null); // volta ao escopo anônimo para o resto do arquivo
}

// =========================================================== Grupo D =======
// Sync device→servidor (com sessão).
sync.saveToken("token-de-teste-29-02");
ok("sessão estabelecida (sync.hasSession)", sync.hasSession() === true);

{
  chamadas.length = 0;
  const termo = { aceitoEm: "2026-09-13T01:00:00.000Z", versao: "1.0" };
  await store.putConfig({ descobertoTermo: termo, permitirOpcaoADescoberto: true });
  const chamada = chamadas.find((c) => /\/api\/config$/.test(c.url) && c.method === "PUT");
  ok("logado, putConfig({descobertoTermo, permitirOpcaoADescoberto}) chama PUT /api/config com AMBOS os campos",
    !!chamada && chamada.body.permitirOpcaoADescoberto === true && chamada.body.descobertoTermo && chamada.body.descobertoTermo.versao === "1.0");
}

{
  // Termo já presente localmente (do teste anterior); ligar de novo SEM
  // reenviar o termo no patch ainda tem que mandar o termo de carona —
  // senão o servidor recusa ligar (regra espelhada de appMode/operadorTermo).
  await store.putConfig({ permitirOpcaoADescoberto: false });
  chamadas.length = 0;
  await store.putConfig({ permitirOpcaoADescoberto: true });
  const chamada = chamadas.find((c) => /\/api\/config$/.test(c.url) && c.method === "PUT");
  ok("ligar sem reenviar o termo manda o termo DE CARONA (senão o servidor recusa ligar)",
    !!chamada && chamada.body.permitirOpcaoADescoberto === true && chamada.body.descobertoTermo && chamada.body.descobertoTermo.versao === "1.0");
}

{
  chamadas.length = 0;
  await store.putConfig({ theme: "dark" });
  const chamouConfig = chamadas.some((c) => /\/api\/config$/.test(c.url));
  ok("logado, putConfig({theme}) NÃO leva nenhum dos dois campos (disciplina 'sem carona')", !chamouConfig);
}

console.log();
console.log(fails === 0 ? "TODOS OS TESTES DO GATE DE OPÇÃO A DESCOBERTO PASSARAM" : fails + " TESTE(S) FALHARAM");
process.exit(fails === 0 ? 0 : 1);
