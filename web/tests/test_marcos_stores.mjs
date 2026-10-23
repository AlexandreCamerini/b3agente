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

// Review WR-03: edição manual do stop reancora o 1R (stopInicial); stop >= PM remove
quotePrice = 23.51;
st = await novoStore(base([{ ...PM(), stopInicial: 20 }]));
e = await erro(() => st.putPosition("PETR4", { stop: 22 }));
ok("WR-03: edição manual reancora stopInicial", !e && lerDoc().positions[0].stopInicial === 22, e && e.message);
e = await erro(() => st.putPosition("PETR4", { stop: 23.2 }));
ok("WR-03: stop >= PM remove stopInicial", !e && lerDoc().positions[0].stopInicial === undefined, e && e.message);

// Review WR-06: editar só o alvo não recusa por causa do stop antigo vs cotação defasada
quotePrice = 21;
st = await novoStore(base([{ ...PM(), stop: 22, alvo: 26 }]));
e = await erro(() => st.putPosition("PETR4", { alvo: 27 }));
ok("WR-06: só o alvo editado, stop gravado acima da cotação não recusa", !e && lerDoc().positions[0].alvo === 27, e && e.message);
e = await erro(() => st.putPosition("PETR4", { alvo: 21.5 }));
ok("WR-06: estrutura segue valendo (alvo < stop)", e && /abaixo do alvo/.test(e.message), e && e.message);

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

// Review WR-04: paridade com POST /api/buy (marcos, marcosMotivo, marcosTexto; revalida no preço executado)
quotePrice = 20;
marcosResp = { valido: true, stop: 18.95, alvo: 23.5, gatilho: 20, invalidacao: 19 };
st = await novoStore(base([]));
out = await st.buy("PETR4", 100, { setup: "Rompimento" });
ok("WR-04: compra com marcos devolve marcos + marcosTexto", out.marcos && out.marcos.stop === 18.95 && out.marcos.alvo === 23.5 && /18,95/.test(out.marcosTexto || "") && out.marcosMotivo === null, JSON.stringify([out.marcos, out.marcosTexto]));
// perseguição no preço executado: gatilho 20, invalidação 19, preço 20,6 (> 0,5R)
quotePrice = 20.6;
st = await novoStore(base([]));
out = await st.buy("PETR4", 100, { setup: "Rompimento" });
ok("WR-04: perseguição recusa os marcos (compra segue sem eles) com texto", lerDoc().positions[0].stop === null && /não persiga/.test(out.marcosMotivo || "") && !!out.marcosTexto, JSON.stringify([out.marcosMotivo, out.marcosTexto]));
// rede fora do ar: motivo explícito + texto
quotePrice = 20;
marcosFalha = true;
st = await novoStore(base([]));
out = await st.buy("PETR4", 100, { setup: "Rompimento" });
ok("WR-04: /api/marcos fora do ar devolve motivo e texto", /Sem dados técnicos/.test(out.marcosMotivo || "") && !!out.marcosTexto, JSON.stringify([out.marcosMotivo, out.marcosTexto]));
marcosFalha = false;
marcosResp = { valido: true, stop: 18.95, alvo: 23.5 };

st = await novoStore(base([]));
chamadas.length = 0;
await st.buy("PETR4", 100);
ok("buy sem setup não consulta o motor", !chamadas.some((c) => /\/api\/marcos\//.test(c)) && lerDoc().positions[0].stop === null);

// WR-03(c): somar lote sem marcos do motor reancora o 1R (paridade com store.buy)
st = await novoStore(base([{ t: "PETR4", qty: 100, avg: 20, stop: 19.5, alvo: 25, stopInicial: 19 }]));
quotePrice = 21;
await st.buy("PETR4", 100);
let pw = lerDoc().positions[0];
ok("WR-03(c): lote somado reancora stopInicial no stop vigente", pw.avg === 20.5 && pw.stopInicial === 19.5, JSON.stringify(pw));
st = await novoStore(base([{ t: "PETR4", qty: 100, avg: 20, stop: 20.6, alvo: 25, stopInicial: 19 }]));
await st.buy("PETR4", 100);
pw = lerDoc().positions[0];
ok("WR-03(c): stop >= novo PM remove stopInicial", pw.stopInicial === undefined, JSON.stringify(pw));
quotePrice = 23.51;

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
