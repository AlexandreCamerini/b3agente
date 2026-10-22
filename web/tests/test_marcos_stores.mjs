// Fase 50 (plano 50-08) — stores: marcos() paritário, putPosition local validado, compra local
// com marcos do motor e gate do laço local (plano inválido não vende nem avisa stop/alvo).
// Roda sem build: `node web/tests/test_marcos_stores.mjs`.
import { MOTIVO_SEM_PRECO_VALIDAR } from "../src/finance.js";

globalThis.CapacitorCustomPlatform = { name: "ios" };
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => { mem.set(k, String(v)); },
  removeItem: (k) => { mem.delete(k); },
};
let fails = 0;
const ok = (name, cond, extra) => { console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || ""))); if (!cond) fails++; };

let quotePrice = 23.51;   // null => getQuotes falha
let marcosResp = { valido: true, stop: 18.95, alvo: 23.5, entrada: 20 };
let marcosFalha = false;
let mercadoAberto = true;
const chamadas = [];
globalThis.fetch = async (url, opts) => {
  const u = String(url);
  chamadas.push((opts && opts.method ? opts.method + " " : "GET ") + u);
  const res = (o) => ({ ok: true, status: 200, text: async () => JSON.stringify(o) });
  if (/\/api\/marcos\//.test(u)) {
    if (marcosFalha) throw new Error("rede");
    return res(marcosResp);
  }
  if (/\/api\/market\/status/.test(u)) return res({ aberto: mercadoAberto });
  if (/\/api\/quotes/.test(u)) {
    if (quotePrice === null) return { ok: false, status: 502, text: async () => "{}" };
    return res({ quotes: { PETR4: { price: quotePrice } } });
  }
  return res({});
};

const KEY = "b3-agente-state-v1";
let seq = 0;
async function novoStore(doc) {
  mem.clear();
  mem.set(KEY, JSON.stringify(doc));
  chamadas.length = 0;
  return (await import("../src/persistence.js?m" + (++seq))).store;
}
const lerDoc = () => JSON.parse(mem.get(KEY));
const base = (positions, extra = {}) => ({
  cash: 100000, positions, history: [], optionPositions: [],
  agent: { autonomous: true }, config: { appMode: "operador" }, ...extra,
});
const PM = () => ({ t: "PETR4", qty: 100, avg: 23.01, stop: null, alvo: null });
const erro = async (fn) => { try { await fn(); return null; } catch (e) { return e; } };

// ---- paridade de método ----
let st = await novoStore(base([PM()]));
ok("deviceStore.marcos existe", typeof st.marcos === "function");
marcosResp = { valido: true, stop: 1, alvo: 2 };
const r0 = await st.marcos("PETR4", { setup: "x" });
ok("deviceStore.marcos delega a POST /api/marcos/PETR4", chamadas.some((c) => /^POST .*\/api\/marcos\/PETR4/.test(c)) && r0.valido === true);

// ---- putPosition local: geometria do caso 23,01/23,51/23,36/21,58 ----
quotePrice = 23.51;
st = await novoStore(base([PM()]));
let e = await erro(() => st.putPosition("PETR4", { stop: 23.36, alvo: 21.58 }));
ok("putPosition recusa geometria impossível com o motivo do servidor",
   e && e.message === "Stop (R$ 23,36) precisa ficar abaixo do alvo (R$ 21,58).", e && e.message);
ok("putPosition recusado não grava", lerDoc().positions[0].stop === null && lerDoc().positions[0].alvo === null);

// sem preço
quotePrice = null;
st = await novoStore(base([PM()]));
e = await erro(() => st.putPosition("PETR4", { stop: 22 }));
ok("sem cotação: recusa com MOTIVO_SEM_PRECO_VALIDAR", e && e.message === MOTIVO_SEM_PRECO_VALIDAR, e && e.message);
ok("sem cotação: não grava", lerDoc().positions[0].stop === null);

// limpar e gestaoAuto não exigem preço
st = await novoStore(base([{ ...PM(), stop: 22, alvo: 26 }]));
e = await erro(() => st.putPosition("PETR4", { stop: null, alvo: null }));
ok("limpar stop/alvo sem preço grava", !e && lerDoc().positions[0].stop === null && lerDoc().positions[0].alvo === null, e && e.message);
e = await erro(() => st.putPosition("PETR4", { gestaoAuto: false }));
ok("só gestaoAuto grava sem preço", !e && lerDoc().positions[0].gestaoAuto === false, e && e.message);

// válido com preço
quotePrice = 23.51;
st = await novoStore(base([PM()]));
e = await erro(() => st.putPosition("PETR4", { stop: 22, alvo: 26 }));
ok("marcos válidos gravam", !e && lerDoc().positions[0].stop === 22 && lerDoc().positions[0].alvo === 26, e && e.message);

// ---- buy local com marcos ----
quotePrice = 20;
marcosResp = { valido: true, stop: 18.95, alvo: 23.5 };
st = await novoStore(base([]));
await st.buy("PETR4", 100, { setup: "Rompimento" });
let p = lerDoc().positions[0];
ok("buy com setup: nasce com marcos do motor", p && p.stop === 18.95 && p.alvo === 23.5 && p.stopInicial === 18.95 && p.gestaoAuto === true, JSON.stringify(p));

marcosResp = { valido: true, stop: 21, alvo: 23.5 }; // stop acima do preço 20
st = await novoStore(base([]));
let out = await st.buy("PETR4", 100, { setup: "Rompimento" });
p = lerDoc().positions[0];
ok("buy com marcos inválidos ao preço: nasce sem marcos + marcosMotivo",
   p && p.stop === null && p.alvo === null && /precisa ficar abaixo da cotação/.test(out.marcosMotivo || ""), JSON.stringify([p, out.marcosMotivo]));

marcosFalha = true;
st = await novoStore(base([]));
out = await st.buy("PETR4", 100, { setup: "Rompimento" });
p = lerDoc().positions[0];
ok("buy com /api/marcos fora do ar: compra segue sem marcos", p && p.qty === 100 && p.stop === null && p.alvo === null);
marcosFalha = false;

st = await novoStore(base([]));
chamadas.length = 0;
await st.buy("PETR4", 100);
ok("buy sem setup não consulta o motor", !chamadas.some((c) => /\/api\/marcos\//.test(c)) && lerDoc().positions[0].stop === null);

// ---- laço local: plano inválido ----
quotePrice = 23.51;
const inval = { t: "PETR4", qty: 100, avg: 23.01, stop: 23.36, alvo: 21.58 };
st = await novoStore(base([inval]));
out = await st.cycle();
let d = lerDoc();
ok("laço aberto: posição inválida não é vendida", d.positions.length === 1 && !d.history.some((h) => h.type === "VENDA"));
const avisos = d.agent.events.filter((x) => /inválido/i.test(x.text));
ok("laço aberto: 1 aviso plano inválido", avisos.length === 1, JSON.stringify(d.agent.events));
out = await st.cycle();
ok("laço aberto: aviso dedup no mesmo dia", lerDoc().agent.events.filter((x) => /inválido/i.test(x.text)).length === 1);

// Nota review WR-02 (2026-10-22, reversão deliberada do guardião da Fase 50): o plano é
// avaliado marco a marco. Alvo inválido (21,58 ≤ PM) nunca vende; o stop 23,36 é válido
// por si e VENDE ao romper — a posição não fica sem proteção por causa do alvo.
quotePrice = 21;
st = await novoStore(base([inval]));
await st.cycle();
ok("laço aberto: stop válido protege mesmo com alvo inválido (WR-02)", lerDoc().positions.length === 0);

// alvo inválido sozinho nunca vira 'alvo atingido'
quotePrice = 24.5;
st = await novoStore(base([{ t: "PETR4", qty: 100, avg: 25, stop: 22, alvo: 24 }]));
await st.cycle();
ok("laço aberto: alvo inválido (≤ PM) não dispara venda", lerDoc().positions.length === 1);

// posição válida segue vendendo no stop
st = await novoStore(base([{ t: "PETR4", qty: 100, avg: 23.01, stop: 22, alvo: 26 }]));
quotePrice = 21.5;
await st.cycle();
ok("laço aberto: posição válida no stop continua vendendo", lerDoc().positions.length === 0);

// fora do pregão
mercadoAberto = false;
quotePrice = 23.51;
st = await novoStore(base([inval]));
await st.cycle();
d = lerDoc();
ok("fora do pregão: posição inválida não gera aviso_diario", !d.agent.events.some((x) => /stop|alvo/i.test(x.text) && !/inválid/i.test(x.text)), JSON.stringify(d.agent.events));
mercadoAberto = true;

if (fails) { console.error("\n" + fails + " falha(s)"); process.exit(1); }
console.log("\ntodos os testes passaram");
