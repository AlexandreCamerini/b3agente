// Testes de PARIDADE web x iOS do cliente HTTP (Etapa 4).
// Travam o bloqueador 2: no nativo, base ausente deve falhar cedo e claro;
// e qualquer resposta NÃO-JSON deve virar erro tratado (nunca quebrar no parse).
// Roda sem device nem build: `node web/tests/test_api_parity.mjs`.
import assert from "node:assert";
import { api, setNativeMode, setApiBase, getApiBase, testServer } from "../src/api.js";

let passed = 0;
const ok = (name) => { console.log("ok", name); passed++; };

// 1) NATIVO sem base configurada => falha cedo, com mensagem acionável.
await (async () => {
  setNativeMode(true);
  setApiBase(""); // sem servidor
  await assert.rejects(
    () => api.getState(),
    (e) => /Endereço do servidor não configurado/.test(e.message),
    "deveria falhar cedo no nativo sem base",
  );
  ok("nativo sem base falha cedo e claro");
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

// 5) testServer com base vazia no nativo => mensagem pedindo o endereço (não quebra).
await (async () => {
  setNativeMode(true);
  setApiBase("");
  const r = await testServer("");
  assert.strictEqual(r.ok, false);
  assert.ok(/Informe o endereço/.test(r.message));
  ok("testServer sem base devolve aviso tratado");
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
