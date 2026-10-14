// Quick 261013-vai (2026-10-14) — Guardião do portão de pregão no ciclo LOCAL do iPhone.
//
// O QUE PROTEGE: deviceStore.cycle() é o espelho de agent._run_cycle_inner. Antes desta quick
// ele executava stop/alvo (ação e opção) a qualquer hora e liquidava vencimento com a data UTC
// (um dia antes entre 21:00 e 24:00 BRT). Aqui: mercado fechado ou status indeterminado NÃO
// executa ordem; vencimento (calendário) roda nos dois casos, com data BRT e sem liquidar antes
// da abertura do próprio dia; aviso deduplicado por `acao:`/`opcao:` no Diário local; opção só
// ganha o aviso GENÉRICO (D2-emenda), sem nenhuma leitura de prêmio. Mais os guardiões
// estáticos do App.jsx (setInterval, A.cycle, A.* de opções; stop/alvo nunca vetados).
//
// Roda sem build: `node web/tests/test_execucao_fora_pregao.mjs`.

import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

globalThis.CapacitorCustomPlatform = { name: "ios" };
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => { mem.set(k, String(v)); },
  removeItem: (k) => { mem.delete(k); },
};

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- fetch stub configurável ------------------------------------------------
let statusResp = { aberto: true, abertura: "10:00" }; // objeto | "erro500" | "lanca"
let preco = 37.5;
let spotCadeia = 37.5;
const chamadas = [];
globalThis.fetch = async (url, opts) => {
  const u = String(url);
  chamadas.push(u);
  if (/\/api\/market\/status/.test(u)) {
    if (statusResp === "lanca") throw new Error("rede");
    if (statusResp === "erro500") return { ok: false, status: 500, text: async () => "{}" };
    return { ok: true, status: 200, text: async () => JSON.stringify(statusResp) };
  }
  if (/\/api\/options\/chain\//.test(u)) {
    return { ok: true, status: 200, text: async () => JSON.stringify({ providerStatus: "ok", underlyingPrice: spotCadeia, calls: [], puts: [] }) };
  }
  if (/\/api\/quotes/.test(u)) {
    return { ok: true, status: 200, text: async () => JSON.stringify({ quotes: { PETR4: { price: preco, change: 0 } } }) };
  }
  return { ok: true, status: 200, text: async () => "{}" };
};

const copy = await import("../src/copy.js");
const evo = await import("../src/evolucaoPosicao.js");
const KEY = "b3-agente-state-v1";
let seq = 0;
async function novoStore(docParcial) {
  mem.clear();
  mem.set(KEY, JSON.stringify(docParcial));
  chamadas.length = 0;
  const mod = await import("../src/persistence.js?c" + (++seq));
  return mod.store;
}
const lerDoc = () => JSON.parse(mem.get(KEY));
const posPetr = (extra) => ({ t: "PETR4", qty: 100, avg: 40, stop: 38, alvo: 45, abertaEm: "2026-10-01", ...(extra || {}) });
const base = (extra) => ({
  cash: 6000, positions: [posPetr()], history: [], optionPositions: [],
  agent: { autonomous: true }, config: { appMode: "operador" }, ...(extra || {}),
});
const txt = (modo, chave, v) => copy.execucaoForaPregaoTxt(modo, chave, v);
const vendas = (d) => (d.history || []).filter((h) => h.type === "VENDA");

// Date fake: instante fixo para os casos de calendário.
const RealDate = Date;
function fixarRelogio(iso) {
  const alvo = new RealDate(iso).getTime();
  globalThis.Date = class extends RealDate {
    constructor(...a) { if (a.length === 0) super(alvo); else super(...a); }
    static now() { return alvo; }
  };
}
const soltarRelogio = () => { globalThis.Date = RealDate; };

// ---- H1 horaMinutoBRT -------------------------------------------------------
ok("H1 12:30Z = 09:30 BRT", evo.horaMinutoBRT(new RealDate("2026-10-16T12:30:00Z")) === "09:30");
ok("H1 01:00Z do dia 17 = 22:00 BRT do dia 16", evo.horaMinutoBRT(new RealDate("2026-10-17T01:00:00Z")) === "22:00"
  && evo.hojeBRT(new RealDate("2026-10-17T01:00:00Z")) === "2026-10-16");
ok("H1 meia-noite BRT = 00:00", evo.horaMinutoBRT(new RealDate("2026-10-16T03:00:00Z")) === "00:00");
ok("H1 relógio inválido -> null", evo.horaMinutoBRT(new RealDate("x")) === null);

// ---- C1 fechado -------------------------------------------------------------
{
  statusResp = { aberto: false, abertura: "10:00" };
  const store = await novoStore(base());
  const out = await store.cycle();
  const d = lerDoc();
  ok("C1 fechado: não vende (posição e caixa iguais, sem VENDA)", d.positions.length === 1 && d.cash === 6000 && vendas(d).length === 0);
  ok("C1 devolve mercadoFechado e a mensagem canônica", out.mercadoFechado === true && out.mensagem === txt("operador", "ciclo_fechado", { abertura: "10:00" }));
  ok("C1 quotes presentes (remarcação é leitura)", out.quotes && out.quotes.PETR4 && out.quotes.PETR4.price === 37.5);
  ok("C1 aviso do Diário = aviso_diario", d.agent.events[0].text === txt("operador", "aviso_diario", { ticker: "PETR4", motivo: "stop" }) && d.agent.events[0].kind === "warn");
  // C2 dedupe
  await store.cycle();
  const d2 = lerDoc();
  ok("C2 segundo ciclo no mesmo dia: nenhum aviso novo", d2.agent.events.filter((e) => /atingido/.test(e.text)).length === 1);
  ok("C2 chave acao:PETR4 e data BRT no doc", d2.agent.avisoForaPregao.chaves.includes("acao:PETR4") && d2.agent.avisoForaPregao.data === evo.hojeBRT());
}
// C2b: chave de opção pré-existente não suprime a da ação
{
  statusResp = { aberto: false, abertura: "10:00" };
  const store = await novoStore(base({ agent: { autonomous: true, avisoForaPregao: { data: evo.hojeBRT(), chaves: ["opcao:X"] } } }));
  await store.cycle();
  const d = lerDoc();
  ok("C2b opcao:X pré-existente não suprime acao:PETR4", d.agent.avisoForaPregao.chaves.includes("acao:PETR4") && d.agent.events.some((e) => /PETR4/.test(e.text)));
}
// modo Estudo usa o texto educacional
{
  statusResp = { aberto: false, abertura: "10:00" };
  const store = await novoStore(base({ config: { appMode: "estudo" } }));
  const out = await store.cycle();
  ok("modo Estudo: aviso e mensagem educacionais", lerDoc().agent.events[0].text === txt("estudo", "aviso_diario", { ticker: "PETR4", motivo: "stop" })
    && out.mensagem === txt("estudo", "ciclo_fechado", { abertura: "10:00" }));
}
// ---- C3 indeterminado -------------------------------------------------------
for (const modoErro of ["erro500", "lanca"]) {
  statusResp = modoErro;
  const store = await novoStore(base());
  const out = await store.cycle();
  const d = lerDoc();
  ok(`C3 status ${modoErro}: não vende`, d.positions.length === 1 && vendas(d).length === 0);
  ok(`C3 status ${modoErro}: mercadoFechado + status_indeterminado`, out.mercadoFechado === true && out.mensagem === txt("operador", "status_indeterminado"));
}
// ---- C4 aberto --------------------------------------------------------------
{
  statusResp = { aberto: true, abertura: "10:00" };
  const store = await novoStore(base());
  const out = await store.cycle();
  const d = lerDoc();
  ok("C4 aberto: vende como antes (Protecao automatica)", d.positions.length === 0 && vendas(d).length === 1 && /Protecao automatica/.test(d.agent.events[0].text));
  ok("C4 aberto: sem mercadoFechado", !out.mercadoFechado);
}
// ---- C5 / C9 opção não vencida, fechado ------------------------------------
const opcaoLegado = (extra) => ({ id: "PETRK99", underlying: "PETR4", expiration: "2099-01-01", optionType: "call", strike: 30, side: "comprada", qty: 100, avg: 1.0, stop: 1.0, alvo: null, ...(extra || {}) });
{
  statusResp = { aberto: false, abertura: "10:00" };
  const store = await novoStore(base({ positions: [], optionPositions: [opcaoLegado()] }));
  const out = await store.cycle();
  let d = lerDoc();
  ok("C5 opção com stop e mercado fechado: não vende", d.optionPositions.length === 1 && vendas(d).length === 0);
  ok("C9 aviso genérico aviso_opcao, chave opcao:<id>", d.agent.events.some((e) => e.text === txt("operador", "aviso_opcao", { contrato: "PETRK99" })) && d.agent.avisoForaPregao.chaves.includes("opcao:PETRK99"));
  ok("C9 aviso sem preço nem 'atingido'", !/R\$|atingido/.test(txt("operador", "aviso_opcao", { contrato: "PETRK99" })) && !/R\$|atingido/.test(txt("estudo", "aviso_opcao", { contrato: "PETRK99" })));
  ok("C9 nenhuma chamada a /api/options/* por causa do aviso", !chamadas.some((u) => /\/api\/options\//.test(u)));
  ok("C9 mensagem do ciclo presente", out.mercadoFechado === true);
  await store.cycle();
  d = lerDoc();
  ok("C9 segundo ciclo no mesmo dia: nenhum aviso novo", d.agent.events.filter((e) => /PETRK99/.test(e.text)).length === 1);
}
{
  statusResp = { aberto: false, abertura: "10:00" };
  const store = await novoStore(base({ positions: [], optionPositions: [opcaoLegado({ stop: null, alvo: null })] }));
  await store.cycle();
  ok("C9 opção sem stop/alvo: nenhum aviso", !lerDoc().agent.events.some((e) => /PETRK99/.test(e.text)));
}
// ---- C8 sem abertura --------------------------------------------------------
{
  statusResp = { aberto: false };
  const store = await novoStore(base());
  const out = await store.cycle();
  ok("C8 sem abertura: variante *_sem_hora e nenhum '?'", out.mensagem === txt("operador", "ciclo_fechado_sem_hora") && !out.mensagem.includes("?")
    && lerDoc().agent.events.every((e) => !e.text.includes("?")));
}
ok("C8 placeholder sem valor lança (nunca '?')", (() => { try { txt("operador", "botao_bloqueado", {}); return false; } catch { return true; } })());
// ---- C6 / C7 vencimento ----------------------------------------------------
const lastrada = () => ({ id: "PETRK30", underlying: "PETR4", expiration: "2026-10-16", optionType: "call", strike: 30, side: "vendida", qty: 100, avg: 1.0, lastro: { t: "PETR4" } });
const legadoVenc = () => opcaoLegado({ id: "PETRK31", expiration: "2026-10-16", strike: 30, stop: null });
for (const [rotulo, st] of [["fechado", { aberto: false, abertura: "10:00" }], ["indeterminado", "erro500"]]) {
  fixarRelogio("2026-10-17T15:00:00Z"); // sábado
  try {
    statusResp = st; spotCadeia = 37.5;
    const store = await novoStore(base({ positions: [posPetr({ stop: null, alvo: null, qtyTravada: 100 })], optionPositions: [lastrada()] }));
    await store.cycle();
    const d = lerDoc();
    ok(`C6 lastreada vencida, ${rotulo}, sábado: liquida pelo intrínseco do payload`, d.optionPositions.length === 0
      && d.history.some((h) => h.kind === "opcao" && h.price === 7.5 && h.motivo === "vencimento"));
    ok(`C6 lastreada, ${rotulo}: destrava qtyTravada`, d.positions[0].qtyTravada === 0);
    const store2 = await novoStore(base({ positions: [], optionPositions: [legadoVenc()] }));
    await store2.cycle();
    const d2 = lerDoc();
    ok(`C6 legado vencido, ${rotulo}, autônomo: liquida`, d2.optionPositions.length === 0 && d2.history.some((h) => h.motivo === "vencimento"));
    const store3 = await novoStore(base({ positions: [], agent: { autonomous: false }, optionPositions: [legadoVenc()] }));
    await store3.cycle();
    ok(`C6 legado vencido, ${rotulo}, sem autônomo: não liquida (regra de hoje)`, lerDoc().optionPositions.length === 1);
  } finally { soltarRelogio(); }
}
// C7: data BRT, não UTC
for (const [iso, rotulo, liquida] of [
  ["2026-10-16T01:00:00Z", "quinta 22:00 BRT (sexta 01:00 UTC)", false],
  ["2026-10-16T12:30:00Z", "sexta 09:30 BRT", false],
  ["2026-10-16T13:30:00Z", "sexta 10:30 BRT", true],
]) {
  fixarRelogio(iso);
  try {
    statusResp = { aberto: false, abertura: "10:00" }; spotCadeia = 37.5;
    const store = await novoStore(base({ positions: [posPetr({ stop: null, alvo: null, qtyTravada: 100 })], optionPositions: [lastrada()] }));
    await store.cycle();
    ok(`C7 ${rotulo}: ${liquida ? "liquida" : "NÃO liquida"}`, (lerDoc().optionPositions.length === 0) === liquida);
  } finally { soltarRelogio(); }
}

// ---- Estáticos do App.jsx ---------------------------------------------------
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persist = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
ok("S1 mercadoRef.current = mercado", app.includes("mercadoRef.current = mercado;"));
{
  const i = app.indexOf("setInterval(() => {", app.indexOf("cycleRef.current = A.cycle;"));
  const corte = app.slice(i, i + 400);
  ok("S2 setInterval do modo autônomo só chama o ciclo com o pregão confirmado aberto",
    /mercadoRef\.current && !mercadoRef\.current\.erro && mercadoRef\.current\.aberto\) cycleRef\.current\(\)/.test(corte));
}
{
  const i = app.indexOf("    cycle: async () => {");
  const corte = app.slice(i, i + 700);
  ok("S3 A.cycle usa s.mercadoFechado para escolher mensagem", /s\.mercadoFechado && s\.mensagem \? s\.mensagem : "Ciclo executado\."/.test(corte));
}
for (const nome of ["buyOption: async", "sellOption: async", "abrirLastreada: async", "abrirCollar: async", "executarCandidatoCurado: async", "fecharLastreada: async"]) {
  const i = app.indexOf("    " + nome);
  const fim = app.indexOf("store.options", i) > 0 ? i + 900 : i + 900;
  const corte = app.slice(i, fim);
  const iRef = corte.indexOf("mercadoRef.current");
  const iStore = Math.min(...["store.options", "executarCandidato("].map((s) => { const k = corte.indexOf(s); return k < 0 ? Infinity : k; }));
  ok(`S4 ${nome.split(":")[0]} checa mercadoRef.current antes da chamada ao store`, iRef >= 0 && iRef < iStore);
}
ok("S5 rodarAgora segue exibindo s.mensagem", /rodarAgora/.test(app) && /s\.mensagem/.test(app.slice(app.indexOf("rodarAgora"), app.indexOf("rodarAgora") + 2500)));
{
  const i = app.indexOf("    applyProposal: async");
  const corte = app.slice(i, i + 500);
  ok("S6 applyProposal (stop/alvo) NÃO referencia mercadoRef — nunca vetado", i > 0 && !corte.includes("mercadoRef"));
}
ok("S7 deviceStore.cycle consulta api.marketStatus() e usa hojeBRT (não UTC)", persist.includes("await api.marketStatus()") && !/const hoje = new Date\(\)\.toISOString\(\)/.test(persist));

if (fails) { console.error("\n" + fails + " falha(s)"); process.exit(1); }
console.log("\ntodos os testes passaram");
