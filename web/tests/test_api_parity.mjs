// Testes de PARIDADE web x iOS do cliente HTTP (Etapa 4).
// Travam o bloqueador 2: no nativo, base ausente deve falhar cedo e claro;
// e qualquer resposta NÃO-JSON deve virar erro tratado (nunca quebrar no parse).
// Roda sem device nem build: `node web/tests/test_api_parity.mjs`.
import assert from "node:assert";
import { api, setNativeMode, setApiBase, getApiBase, testServer } from "../src/api.js";

let passed = 0;
const ok = (name) => { console.log("ok", name); passed++; };

// 1) NATIVO sem base configurada => usa a PRODUÇÃO embutida (FASE 6, fix 1).
// Contrato antigo (falhar cedo) foi substituído de propósito: o app deve
// funcionar de fábrica, sem o usuário digitar servidor. O guardião completo
// do novo contrato está em test_api_base.mjs.
await (async () => {
  setNativeMode(true);
  setApiBase(""); // sem override manual
  assert.strictEqual(getApiBase(), "https://boris.semente.dev");
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.ok(String(url).startsWith("https://boris.semente.dev/api/"), "deveria chamar a produção");
    return { ok: true, status: 200, text: async () => JSON.stringify({ okState: true }) };
  };
  try {
    const s = await api.getState();
    assert.ok(s && s.okState);
    ok("nativo sem base usa a produção embutida (app funciona de fábrica)");
  } finally {
    globalThis.fetch = realFetch;
  }
})();

// 2) Resposta NÃO-JSON (HTML do próprio app) => erro tratado, sem crash de parse.
await (async () => {
  setNativeMode(false);
  setApiBase("http://192.168.0.10:8787");
  const realFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    text: async () => "<!doctype html><html><body>app</body></html>",
  });
  try {
    await assert.rejects(
      () => api.getState(),
      (e) => /não veio em JSON|aponta para o app/.test(e.message),
      "resposta HTML deveria virar erro tratado",
    );
    ok("resposta nao-JSON vira erro tratado (sem crash de parse)");
  } finally {
    globalThis.fetch = realFetch;
  }
})();

// 3) Erro HTTP com corpo JSON => propaga `detail` legível.
await (async () => {
  setNativeMode(false);
  setApiBase("http://192.168.0.10:8787");
  const realFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 502,
    text: async () => JSON.stringify({ detail: "Backend fora do ar" }),
  });
  try {
    await assert.rejects(() => api.getState(), (e) => /Backend fora do ar/.test(e.message));
    ok("erro HTTP propaga detail legivel");
  } finally {
    globalThis.fetch = realFetch;
  }
})();

// 4) normalização da base: tolera host:porta e remove /api e barra final.
await (async () => {
  setNativeMode(false);
  setApiBase("192.168.0.12:8787/api/");
  assert.strictEqual(getApiBase(), "http://192.168.0.12:8787");
  setApiBase("b3-production-8fc0.up.railway.app/api/");
  assert.strictEqual(getApiBase(), "https://b3-production-8fc0.up.railway.app");
  ok("normaliza base (IP local em http; dominio publico em https; sem /api e barra final)");
})();

// 5) testServer com base vazia no nativo => testa a PRODUÇÃO embutida (FASE 6).
await (async () => {
  setNativeMode(true);
  setApiBase("");
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.ok(String(url).startsWith("https://boris.semente.dev/api/health"));
    return { ok: true, status: 200, text: async () => JSON.stringify({ ok: true }) };
  };
  try {
    const r = await testServer("");
    assert.strictEqual(r.ok, true);
    ok("testServer sem base testa a produção embutida");
  } finally {
    globalThis.fetch = realFetch;
    setNativeMode(false); setApiBase("");
  }
})();

// 6) Erro HTTP estruturado da IA => mensagem útil com ação, provedor/modelo e servidor.
await (async () => {
  setNativeMode(false);
  setApiBase("https://b3-production-8fc0.up.railway.app");
  const realFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 502,
    text: async () => JSON.stringify({ detail: { message: "Nenhuma chave de API disponível para a IA.", provider: "openai", model: "gpt-4o-mini", keySource: "manual", action: "Salve a chave no iPhone." } }),
  });
  try {
    await assert.rejects(
      () => api.analyzeTechnical("PETR4", { model: "completo" }),
      (e) => /Nenhuma chave/.test(e.message) && /provedor=openai/.test(e.message) && /Como corrigir: Salve a chave/.test(e.message),
    );
    ok("erro estruturado de IA vira diagnóstico acionável");
  } finally {
    globalThis.fetch = realFetch;
  }
})();

console.log(`\n${passed} testes de paridade do cliente HTTP: TODOS PASSARAM`);
