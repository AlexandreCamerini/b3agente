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

// ===== qa/35 (P2): expectância + calibração + export CSV =====

// 5) analysisOutcomesCsv é GET em /export.csv e devolve TEXTO cru (não JSON).
await (async () => {
  let captured = null;
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (url, opts) => {
    captured = { url: String(url), method: (opts && opts.method) || "GET" };
    return { ok: true, status: 200, headers: { get: () => "text/csv" }, text: async () => "id,ticker\na1,PETR4\n" };
  };
  try {
    const csv = await api.analysisOutcomesCsv();
    assert.equal(captured.method, "GET");
    assert.ok(captured.url.includes("/api/analysis-outcomes/export.csv"), "rota do export");
    assert.ok(csv.startsWith("id,ticker"), "devolve o texto do CSV, sem parse JSON");
  } finally { globalThis.fetch = realFetch; }
  ok("qa/35: export CSV via GET /api/analysis-outcomes/export.csv (texto)");
})();

// 6) paridade dos stores para o CSV.
await (async () => {
  const src = readFileSync(new URL("../src/persistence.js", import.meta.url), "utf8");
  const hits = (src.match(/\banalysisOutcomesCsv\s*[:(]/g) || []).length;
  assert.ok(hits >= 2, "analysisOutcomesCsv nos DOIS stores (achado " + hits + "x)");
  ok("qa/35: paridade — analysisOutcomesCsv nos dois stores");
})();

// 7) a tela exibe as camadas aprovadas (a: expectância; c: calibração) e
// respeita a régua de amostra mínima (n insuficiente — nunca % enganosa).
await (async () => {
  const src = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  assert.ok(/EXPECTÂNCIA/.test(src) && /efic\.expectancia\b/.test(src), "camada (a): expectância na tela");
  assert.ok(/PROFIT FACTOR/.test(src) && /efic\.profitFactor/.test(src), "camada (a): profit factor na tela");
  assert.ok(/CALIBRAÇÃO DA CONFIANÇA/.test(src) && /efic\.porConfianca/.test(src), "camada (c): calibração na tela");
  assert.ok(/efic\.porDecisao/.test(src), "camada (c): recorte por decisão na tela");
  assert.ok(/n insuficiente/.test(src) && /insuficiente\b/.test(src), "régua de amostra mínima visível");
  // qa/35-fix: os cards aparecem já com totalAnalises>0 (mostrando "aguardando
  // o prazo"), NÃO só quando avaliadas>0 — senão somem inteiros por 10 pregões.
  const expBloco = src.slice(src.indexOf("qa/35 (P2a): EXPECTÂNCIA"), src.indexOf("qa/35 (P2): export CSV do registro bruto"));
  assert.ok(!/efic\.avaliadas > 0 &&/.test(expBloco), "expectância/calibração NÃO podem gate em avaliadas>0 (some por 10 pregões)");
  assert.ok((expBloco.match(/efic\.totalAnalises > 0 &&/g) || []).length >= 2, "expectância e calibração gate em totalAnalises>0");
  assert.ok(/Aguardando o prazo/.test(expBloco), "aviso de prazo enquanto avaliadas===0");
  assert.ok(/Exportar CSV/.test(src) && /store\.analysisOutcomesCsv\(\)/.test(src), "botão de export ligado no store");
  ok("qa/35: painel exibe expectância + calibração + export, com n mínimo");
})();

// 9) qa/37 (P2e): curva de R acumulado + drawdown no painel.
await (async () => {
  const src = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  assert.ok(/CURVA DE R ACUMULADO/.test(src) && /efic\.curvaR/.test(src), "card da curva de R na tela");
  assert.ok(/function RCurve\(/.test(src) && /<RCurve pts=\{efic\.curvaR\}/.test(src), "componente RCurve renderizado");
  assert.ok(/efic\.rAcumulado/.test(src) && /efic\.drawdownMax/.test(src), "R acumulado e drawdown exibidos");
  assert.ok(/Aguardando o prazo/.test(src), "estado vazio (aguardando 10 pregões) coberto");
  // usePalette (hex resolvido) no SVG, não var() cru — mesmo contrato do Sparkline
  assert.ok(/function RCurve[\s\S]{0,400}usePalette\(\)/.test(src), "RCurve usa usePalette (SVG theme-aware)");
  ok("qa/37: curva de R acumulado + drawdown no painel de eficiência");
})();

// 8) o servidor captura a confiança declarada nos DOIS registros (N1/N2) e o
// backend expõe o endpoint CSV — wiring estático no main.py.
await (async () => {
  const py = readFileSync(new URL("../../server/app/main.py", import.meta.url), "utf8");
  assert.ok(/confianca=res\.get\("confianca"\)/.test(py), "N1 registra a confiança declarada");
  assert.ok(/confianca=\(result\.get\("kpis"\) or \{\}\)\.get\("conviccao"\)/.test(py), "N2 registra a convicção dos kpis");
  assert.ok(/analysis-outcomes\/export\.csv/.test(py), "endpoint do export CSV existe");
  ok("qa/35: main.py captura confiança (N1+N2) e expõe o CSV");
})();

console.log("\n" + passed + " testes ok — contrato da eficiência da IA e paridade preservada");
