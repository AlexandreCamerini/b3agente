// Quick 261006-dvg (2026-10-06) — conta nova no iOS nasce LIMPA (decisão do
// Alex; invariante "conta nova nasce limpa"). Revoga a "decisão B": o
// deviceStore não envia mais semente ao servidor e não copia o doc anônimo
// (b3-agente-state-v1) para o namespace novo. O doc anônimo fica intocado.
// Roda sem device: `node web/tests/test_conta_nova_ios_nasce_limpa.mjs`.
import { readFileSync } from "node:fs";

globalThis.CapacitorCustomPlatform = { name: "ios" };
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => { mem.set(k, String(v)); },
  removeItem: (k) => { mem.delete(k); },
};

const ANON = JSON.stringify({
  cash: 1000000,
  positions: [{ t: "VALE3", qty: 100, avg: 60 }],
  history: [{ type: "COMPRA", t: "VALE3", qty: 100, price: 60 }],
  equitySnapshots: [{ data: "2026-01-02", patrimonio: 1 }, { data: "2026-01-03", patrimonio: 2 }],
  watchlist: ["ZZZZ3"],
  config: { apiKey: "LOCALKEY", initialBudget: 10000 },
});
mem.set("b3-agente-state-v1", ANON);

const chamadas = [];
let respostaAuth = null;
let cashServidor = 7777;
const ESTADO_NOVO = { cash: 100000, positions: [], history: [], equitySnapshots: [], watchlist: ["PETR4"], config: { initialBudget: 100000, keyStored: false } };
const json = (o) => ({ ok: true, status: 200, text: async () => JSON.stringify(o) });
globalThis.fetch = async (url, opts) => {
  const method = (opts && opts.method) || "GET";
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  chamadas.push({ url: String(url), method, body });
  if (/\/api\/auth\/(register|login|oauth)$/.test(url)) return json(respostaAuth);
  if (/\/api\/state$/.test(url) && method === "GET") return json({ ...ESTADO_NOVO, cash: cashServidor, positions: [], history: [] });
  return json({});
};

const { auth, store } = await import("../src/persistence.js");
let fails = 0;
const ok = (n, c) => { console.log((c ? "ok " : "FALHOU ") + n); if (!c) fails++; };
const vazio = (a) => !a || a.length === 0;

// nova com estado
respostaAuth = { token: "t1", user: { id: "novo1" }, state: ESTADO_NOVO };
await auth.register({ email: "a@b.c", password: "senhaboa123" });
ok("register sem 'seed' no corpo", !("seed" in chamadas.find((c) => /auth\/register$/.test(c.url)).body));
{
  const s = await store.getState();
  ok("conta nova: positions vazio", vazio(s.positions));
  ok("conta nova: history vazio", vazio(s.history));
  ok("conta nova: equitySnapshots vazio", vazio(s.equitySnapshots));
  ok("conta nova: cash do servidor", s.cash === 100000 || s.cash === 7777);
  ok("conta nova: watchlist sem ZZZZ3", !(s.watchlist || []).includes("ZZZZ3"));
  ok("conta nova: sem LOCALKEY", !s.config || !s.config.apiKey);
  ok("conta nova: initialBudget 100000", s.config.initialBudget === 100000);
}

// nova sem state
await auth.logout();
respostaAuth = { token: "t2", user: { id: "novo2" } };
await auth.login({ email: "c@d.e", password: "senhaboa123" });
ok("login sem 'seed' no corpo", !("seed" in chamadas.filter((c) => /auth\/login$/.test(c.url)).pop().body));
{
  const s = await store.getState();
  ok("sem state: positions vazio", vazio(s.positions));
  ok("sem state: sem ZZZZ3", !(s.watchlist || []).includes("ZZZZ3"));
  ok("sem state: sem LOCALKEY", !s.config || !s.config.apiKey);
}

// oauth
await auth.logout();
respostaAuth = { token: "t3", user: { id: "novo3" }, state: ESTADO_NOVO };
await auth.oauth({ provider: "google", idToken: "x" });
ok("oauth sem 'seed' no corpo", !("seed" in chamadas.filter((c) => /auth\/oauth$/.test(c.url)).pop().body));

// existente
await auth.logout();
mem.set("b3-agente-state-v1::u:velho1", JSON.stringify({ cash: 5000, watchlist: ["ITUB4"], positions: [], history: [] }));
respostaAuth = { token: "t4", user: { id: "velho1" }, state: { ...ESTADO_NOVO, watchlist: ["OUTRA3"] } };
await auth.login({ email: "v@v.v", password: "senhaboa123" });
{
  const s = await store.getState();
  ok("existente: namespace local não sobrescrito (ITUB4)", (s.watchlist || []).includes("ITUB4") && !(s.watchlist || []).includes("OUTRA3"));
  ok("existente: cash adotado do servidor (7777)", s.cash === 7777);
}

await auth.logout();
ok("doc anônimo intocado byte a byte", mem.get("b3-agente-state-v1") === ANON);

// estático
{
  const src = readFileSync(new URL("../src/persistence.js", import.meta.url), "utf8");
  const code = src.split("\n").filter((l) => !l.trim().startsWith("//")).join("\n");
  ok("estático: sem _localSeed", !code.includes("_localSeed"));
  ok("estático: sem _seedBody", !code.includes("_seedBody"));
  ok("estático: sem body.seed", !code.includes("body.seed"));
  ok("estático: sem readKey(BASE_KEY)", !code.includes("readKey(BASE_KEY)"));
  ok("estático: _semearDoServidor nos dois stores", (code.match(/_semearDoServidor\s*(\(|:)/g) || []).length >= 2);
}

if (fails) { console.log(fails + " falha(s)"); process.exit(1); }
console.log("tudo ok");
