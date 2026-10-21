// Quick 261021-spd — deviceStore.cycle(): COM conta delega ao servidor (POST /api/cycle, zero
// venda local); SEM conta o laço legado tolera lastro de CALL coberta (aviso, não exceção).
// Roda sem build: `node web/tests/test_ciclo_iphone_delega_servidor.mjs`.
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

let cycleResp = "ok"; // "ok" | "erro500" | "lanca"
const chamadas = [];
const estadoServidor = {
  positions: [{ t: "VALE3", qty: 10, avg: 60, stop: 50 }],
  optionPositions: [], cash: 9999, history: [{ type: "VENDA", t: "PETR4", qty: 100 }],
  agent: { events: [{ time: "21/10 11:00", kind: "buy", t: "PETR4", text: "Proteção simulada: PETR4 vendido (stop atingido) a R$ 37.50." }], mode: "executar" },
  quotes: { VALE3: { price: 61 } }, mercadoFechado: true, mensagem: "Pregão fechado.",
};
globalThis.fetch = async (url, opts) => {
  const u = String(url);
  chamadas.push((opts && opts.method ? opts.method + " " : "GET ") + u);
  if (/\/api\/cycle/.test(u)) {
    if (cycleResp === "lanca") throw new Error("rede");
    if (cycleResp === "erro500") return { ok: false, status: 500, text: async () => "{}" };
    return { ok: true, status: 200, text: async () => JSON.stringify(estadoServidor) };
  }
  if (/\/api\/market\/status/.test(u)) return { ok: true, status: 200, text: async () => JSON.stringify({ aberto: true }) };
  if (/\/api\/quotes/.test(u)) {
    return { ok: true, status: 200, text: async () => JSON.stringify({ quotes: { PETR4: { price: 37.5 }, VALE3: { price: 57 } } }) };
  }
  if (/\/api\/options\/chain\//.test(u)) return { ok: true, status: 200, text: async () => JSON.stringify({ providerStatus: "ok", underlyingPrice: 37.5, calls: [], puts: [] }) };
  return { ok: true, status: 200, text: async () => "{}" };
};

const KEY = "b3-agente-state-v1";
let seq = 0;
async function novoStore(doc, comToken) {
  mem.clear();
  mem.set(KEY, JSON.stringify(doc));
  if (comToken) mem.set("b3-auth-token-v1", "tok");
  chamadas.length = 0;
  return (await import("../src/persistence.js?c" + (++seq))).store;
}
const lerDoc = () => JSON.parse(mem.get(KEY));
const base = (positions) => ({
  cash: 6000, positions, history: [], optionPositions: [],
  agent: { autonomous: true }, config: { appMode: "operador" },
});
const A = { t: "PETR4", qty: 100, qtyTravada: 100, avg: 40, stop: 38, alvo: 45 };
const B = { t: "VALE3", qty: 50, avg: 60, stop: 58, alvo: 70 };

// ---- COM conta ----
cycleResp = "ok";
let st = await novoStore(base([A, B]), true);
let out = await st.cycle();
ok("logado: POST /api/cycle chamado", chamadas.some((c) => /^POST .*\/api\/cycle/.test(c)));
ok("logado: nenhuma venda/status/quotes/chain local", !chamadas.some((c) => /\/api\/(sell|market\/status|quotes|options\/chain)/.test(c)));
ok("logado: carteira do servidor adotada", out.positions.length === 1 && out.positions[0].t === "VALE3" && out.cash === 9999);
ok("logado: eventos do servidor", out.agent.events.length === 1 && /PETR4 vendido/.test(out.agent.events[0].text));
ok("logado: quotes/mercadoFechado/mensagem repassados", out.quotes.VALE3.price === 61 && out.mercadoFechado === true && out.mensagem === "Pregão fechado.");
ok("logado: doc local reflete o servidor", lerDoc().positions.length === 1 && lerDoc().cash === 9999);

// W2 da revisão (quick 261021-spd): outro ciclo da conta já rodava — a flag e a frase chegam à UI.
const _ef = { mercadoFechado: estadoServidor.mercadoFechado, mensagem: estadoServidor.mensagem };
delete estadoServidor.mercadoFechado;
estadoServidor.cicloEmAndamento = true;
estadoServidor.mensagem = "Já havia um ciclo do Operador em andamento nesta conta — nada novo foi executado agora.";
st = await novoStore(base([A, B]), true);
out = await st.cycle();
ok("logado: cicloEmAndamento + mensagem repassados", out.cicloEmAndamento === true && /em andamento/.test(out.mensagem) && !out.mercadoFechado);
delete estadoServidor.cicloEmAndamento;
Object.assign(estadoServidor, _ef);

for (const modo of ["erro500", "lanca"]) {
  cycleResp = modo;
  st = await novoStore(base([A, B]), true);
  let erro = null;
  try { await st.cycle(); } catch (e) { erro = e; }
  ok(`logado + /api/cycle ${modo}: rejeita`, !!erro);
  ok(`logado + /api/cycle ${modo}: sem fallback local (nada vendido)`,
    !chamadas.some((c) => /\/api\/sell/.test(c)) && lerDoc().positions.length === 2 && lerDoc().history.length === 0);
}

// ---- SEM conta ----
cycleResp = "ok";
st = await novoStore(base([A, B]), false);
out = null; let lancou = false;
try { out = await st.cycle(); } catch { lancou = true; }
ok("sem conta: 100% travada não lança", !lancou && out);
const d = lerDoc();
const evs = d.agent.events;
const lastro = evs.filter((e) => e.kind === "warn" && e.t === "PETR4" && /lastro/.test(e.text));
ok("sem conta: 1 aviso de lastro para A, sem 'vendido'", lastro.length === 1 && !/vendido/.test(lastro[0].text));
ok("sem conta: B vendida com evento", d.positions.every((p) => p.t !== "VALE3") && evs.some((e) => e.kind === "buy" && /VALE3 vendido/.test(e.text)));
ok("sem conta: A continua na carteira", d.positions.some((p) => p.t === "PETR4" && p.qty === 100));
ok("sem conta: ciclo chegou ao fim (opções avaliadas / eventos gravados)", Array.isArray(d.agent.events) && d.agent.events.length >= 2);
ok("sem conta: nenhuma rejeição local de A", !(d.history || []).some((h) => h.t === "PETR4"));
// 2º ciclo no mesmo dia: não repete o aviso
await st.cycle();
ok("sem conta: aviso 1x por dia", lerDoc().agent.events.filter((e) => e.t === "PETR4" && /lastro/.test(e.text)).length === 1);

// venda local que lança por outro motivo
st = await novoStore(base([B]), false);
const orig = st.sell;
st.sell = async () => { throw new Error("falha simulada"); };
try { await st.cycle(); } catch { ok("sem conta: erro de venda não derruba o ciclo", false); }
const ev2 = lerDoc().agent.events;
ok("sem conta: erro de venda vira warn com a mensagem, sem 'vendido'",
  ev2.some((e) => e.kind === "warn" && /falha simulada/.test(e.text)) && !ev2.some((e) => /vendido/.test(e.text)));
st.sell = orig;

// ---- estático ----
const src = readFileSync(join(here, "../src/persistence.js"), "utf8");
const i = src.indexOf("async cycle() {\n      ensure();\n      // Quick 261021-spd");
const j = src.indexOf("return out;", i);
const ramo = src.slice(i, j);
ok("estático: ramo logado usa api.cycle() e não chama this.sell(", i > 0 && /hasSession\(\)[\s\S]{0,400}api\.cycle\(\)/.test(ramo) && !/this\.sell\(/.test(ramo));

process.exit(fails ? 1 : 0);
