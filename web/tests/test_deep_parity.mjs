// FASE 2 (2.1) — contrato do cliente do deep (N1) e paridade dos stores.
// Roda sem device nem build: `node web/tests/test_deep_parity.mjs`.
import assert from "node:assert";
import { readFileSync } from "node:fs";
import { api, setNativeMode, setApiBase } from "../src/api.js";

let passed = 0;
const ok = (name) => { console.log("ok", name); passed++; };

// 1) scanDeepEstimate monta GET com period/topN/tickers na query.
await (async () => {
  setNativeMode(false);
  setApiBase("http://127.0.0.1:8787");
  let captured = null;
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (url, opts) => {
    captured = { url: String(url), method: (opts && opts.method) || "GET" };
    return { ok: true, status: 200, headers: { get: () => "application/json" }, json: async () => ({ topN: 2, chamadas: 1 }), text: async () => JSON.stringify({ topN: 2, chamadas: 1 }) };
  };
  try {
    const r = await api.scanDeepEstimate("6mo", 2, "PETR4,VALE3");
    assert.equal(captured.method, "GET");
    assert.ok(captured.url.includes("/api/scan/deep/estimate"), "rota do estimate");
    assert.ok(captured.url.includes("period=6mo") && captured.url.includes("topN=2") && captured.url.includes("tickers=PETR4%2CVALE3"));
    assert.equal(r.chamadas, 1);
  } finally { globalThis.fetch = realFetch; }
  ok("estimate: GET com period/topN/tickers");
})();

// 2) scanDeep é POST em /api/scan/deep com o body JSON.
await (async () => {
  let captured = null;
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (url, opts) => {
    captured = { url: String(url), method: opts.method, body: JSON.parse(opts.body) };
    return { ok: true, status: 200, headers: { get: () => "application/json" }, json: async () => ({ results: [] }), text: async () => JSON.stringify({ results: [] }) };
  };
  try {
    await api.scanDeep({ period: "1y", topN: 3, tickers: "PETR4" });
    assert.equal(captured.method, "POST");
    assert.ok(captured.url.includes("/api/scan/deep"));
    assert.deepEqual(captured.body, { period: "1y", topN: 3, tickers: "PETR4" });
  } finally { globalThis.fetch = realFetch; }
  ok("deep: POST /api/scan/deep com body");
})();

// 3) PARIDADE dos stores (invariante do projeto): serverStore e deviceStore
// expõem a MESMA interface. Verificação estática no fonte (persistence.js
// importa @capacitor/core, que não existe fora do build — por isso o grep).
await (async () => {
  const src = readFileSync(new URL("../src/persistence.js", import.meta.url), "utf8");
  for (const m of ["scanDeep", "scanDeepEstimate"]) {
    const hits = (src.match(new RegExp("\\b" + m + "\\s*[:(]", "g")) || []).length;
    assert.ok(hits >= 2, m + " deve existir nos DOIS stores (achado " + hits + "x)");
  }
  ok("paridade: scanDeep/scanDeepEstimate nos dois stores");
})();

console.log("\n" + passed + " testes ok — contrato do deep e paridade preservada");
