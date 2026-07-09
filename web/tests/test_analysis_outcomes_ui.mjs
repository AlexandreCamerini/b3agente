// qa/30 (Fase A) — contrato do cliente da eficiência da IA + paridade dos
// stores + wiring na tela de Observabilidade. Roda sem device nem build:
// `node web/tests/test_analysis_outcomes_ui.mjs`.
import assert from "node:assert";
import { readFileSync } from "node:fs";
import { api, setNativeMode, setApiBase } from "../src/api.js";

let passed = 0;
const ok = (name) => { console.log("ok", name); passed++; };

// 1) analysisOutcomesStats é GET em /api/analysis-outcomes/stats (sem modo).
await (async () => {
  setNativeMode(false);
  setApiBase("http://127.0.0.1:8787");
  let captured = null;
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (url, opts) => {
    captured = { url: String(url), method: (opts && opts.method) || "GET" };
    return { ok: true, status: 200, headers: { get: () => "application/json" }, json: async () => ({ totalAnalises: 0 }), text: async () => JSON.stringify({ totalAnalises: 0 }) };
  };
  try {
    const r = await api.analysisOutcomesStats();
    assert.equal(captured.method, "GET");
    assert.ok(captured.url.includes("/api/analysis-outcomes/stats"), "rota das estatísticas");
    assert.ok(!captured.url.includes("modo="), "sem filtro de modo, não manda ?modo=");
    assert.equal(r.totalAnalises, 0);
  } finally { globalThis.fetch = realFetch; }
  ok("stats: GET /api/analysis-outcomes/stats sem filtro");
})();

// 2) com modo, vira query string ?modo=operador.
await (async () => {
  let captured = null;
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    captured = String(url);
    return { ok: true, status: 200, headers: { get: () => "application/json" }, json: async () => ({}), text: async () => "{}" };
  };
  try {
    await api.analysisOutcomesStats("operador");
    assert.ok(captured.includes("modo=operador"), "modo vira query string");
  } finally { globalThis.fetch = realFetch; }
  ok("stats: filtro de modo vira ?modo=");
})();

// 3) PARIDADE dos stores (invariante do projeto): serverStore e deviceStore
// expõem a MESMA interface. Verificação estática no fonte (persistence.js
// importa @capacitor/core, que não existe fora do build).
await (async () => {
  const src = readFileSync(new URL("../src/persistence.js", import.meta.url), "utf8");
  const hits = (src.match(/\banalysisOutcomesStats\s*[:(]/g) || []).length;
  assert.ok(hits >= 2, "analysisOutcomesStats deve existir nos DOIS stores (achado " + hits + "x)");
  ok("paridade: analysisOutcomesStats nos dois stores");
})();

// 4) A tela de Observabilidade carrega e exibe as estatísticas (wiring real,
// não só a API existir solta). Verificação estática no App.jsx.
await (async () => {
  const src = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  assert.ok(/store\.analysisOutcomesStats\(\)/.test(src), "ObservabilidadeScreen chama store.analysisOutcomesStats()");
  assert.ok(/EFICIÊNCIA DA IA/.test(src), "painel 'Eficiência da IA' está na tela");
  assert.ok(/efic\.taxaAcerto/.test(src) && /efic\.rMedio/.test(src), "exibe taxa de acerto e R médio");
  ok("wiring: ObservabilidadeScreen carrega e exibe a eficiência da IA");
})();

console.log("\n" + passed + " testes ok — contrato da eficiência da IA e paridade preservada");
