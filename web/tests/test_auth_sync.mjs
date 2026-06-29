// FASE 2 — testes do cliente de auth + camada de sync (sem device, sem build).
// Roda: `node web/tests/test_auth_sync.mjs`.
//   1) o token vira header Authorization: Bearer em toda chamada do api.js;
//   2) escrita offline cai na fila (outbox) e é reaplicada no flush ao voltar.
import assert from "node:assert";
import { api, setNativeMode, setApiBase, setAuthToken, getAuthToken } from "../src/api.js";

// localStorage mínimo em memória (Node não tem) para a sync.js.
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => mem.set(k, String(v)),
  removeItem: (k) => mem.delete(k),
};
// controla "online" para os testes (navigator é read-only no Node 22)
let online = true;
Object.defineProperty(globalThis, "navigator", { configurable: true, get() { return { onLine: online }; } });

const sync = await import("../src/sync.js");

let passed = 0;
const ok = (n) => { console.log("ok", n); passed++; };

// 1) Authorization: Bearer presente quando há token; ausente quando não há.
await (async () => {
  setNativeMode(false);
  setApiBase("http://192.168.0.10:8787");
  let seenAuth = null;
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (url, opts) => {
    seenAuth = (opts.headers && opts.headers.Authorization) || null;
    return { ok: true, status: 200, text: async () => JSON.stringify({ ok: true }) };
  };
  try {
    setAuthToken("");
    await api.getState();
    assert.equal(seenAuth, null, "sem token => sem header");
    setAuthToken("TOKEN-123");
    assert.equal(getAuthToken(), "TOKEN-123");
    await api.getState();
    assert.equal(seenAuth, "Bearer TOKEN-123", "com token => Bearer no header");
    ok("token vira Authorization: Bearer (e ausência => sem header)");
  } finally { globalThis.fetch = realFetch; setAuthToken(""); }
})();

// 2) Escrita offline -> outbox; flush ao voltar online reaplica no servidor.
await (async () => {
  setApiBase("http://192.168.0.10:8787");
  mem.clear();
  // semente de cache para o patch otimista ter base
  sync.cacheSet({ config: { userName: "" }, profile: {}, watchlist: [] });

  const calls = [];
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (url, opts) => {
    calls.push({ url, method: opts.method, body: opts.body });
    return { ok: true, status: 200, text: async () => JSON.stringify({ config: { userName: "Z" } }) };
  };
  try {
    online = false;
    const optimistic = await sync.mutate("putConfig", [{ userName: "Offline" }], (cur) => ({ ...cur, config: { ...cur.config, userName: "Offline" } }));
    assert.equal(optimistic.config.userName, "Offline", "offline aplica patch otimista no cache");
    assert.equal(sync.outboxLen(), 1, "operação foi enfileirada");
    assert.equal(calls.length, 0, "nada foi enviado ao servidor offline");

    online = true;
    const remaining = await sync.flush();
    assert.equal(remaining, 0, "fila drenada ao reconectar");
    assert.ok(calls.length >= 1, "operação reaplicada no servidor");
    assert.ok(/\/api\/config$/.test(calls[0].url), "reaplicou PUT /api/config");
    ok("escrita offline enfileira e reaplica no flush (server = fonte da verdade)");
  } finally { globalThis.fetch = realFetch; online = true; }
})();

// 3) Leitura offline devolve o cache (sem crash).
await (async () => {
  mem.clear();
  sync.cacheSet({ config: { userName: "DoCache" }, watchlist: ["PETR4"] });
  online = false;
  const s = await sync.readState();
  assert.equal(s.config.userName, "DoCache", "offline lê do cache");
  online = true;
  ok("leitura offline cai no cache (boot sem crash)");
})();

console.log(`\n${passed} testes de auth+sync OK`);
