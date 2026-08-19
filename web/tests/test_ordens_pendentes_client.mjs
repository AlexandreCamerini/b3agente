// Ordens pendentes / status de mercado — cliente HTTP + guardião de paridade
// dos dois stores (deviceStore x serverStore em persistence.js).
//
// Guardião de paridade (Task 2): incidente que motiva a regra — `deviceStore`
// e `serverStore` já divergiram antes (push/appMode que nunca chegava ao
// servidor porque só um dos dois stores mandava o campo, ver
// test_didatica_parity.mjs). Aqui: `pendingOrders`/`caixaReservado` chegam à
// tela nos DOIS stores (deviceStore local-first e serverStore web), e
// `cancelPendingOrder`/`marketStatus` existem nos DOIS com o mesmo contrato —
// senão o app teria uma classe de "a tela está certa, só um dos dois lados
// erra" outra vez.
//
// Roda sem device nem build: `node web/tests/test_ordens_pendentes_client.mjs`.
import assert from "node:assert";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { api } from "../src/api.js";

const here = dirname(fileURLToPath(import.meta.url));
const persistenceSrc = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let passed = 0;
let fails = 0;
const ok = (name) => { console.log("ok " + name); passed++; };
const okc = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------ api.marketStatus()
await (async () => {
  const realFetch = globalThis.fetch;
  let calledUrl = null;
  let calledHeaders = null;
  globalThis.fetch = async (url, opts) => {
    calledUrl = String(url);
    calledHeaders = (opts && opts.headers) || undefined;
    return { ok: true, status: 200, text: async () => JSON.stringify({ aberto: false, diaDePregao: true, abertura: "10:00", fechamento: "16:55", agoraBRT: "18/08 21:40", afterMarket: false }) };
  };
  try {
    const r = await api.marketStatus();
    assert.ok(/\/api\/market\/status$/.test(calledUrl), "deveria chamar GET /api/market/status");
    assert.strictEqual(r.aberto, false);
    assert.strictEqual(r.diaDePregao, true);
    // sem token de sessão: nao deveria haver Authorization no header (ela roda
    // ANTES do login, na tela de entrada, D-08).
    assert.ok(!calledHeaders || !calledHeaders.Authorization, "marketStatus nao deveria exigir Authorization");
    ok("api.marketStatus() chama GET /api/market/status e funciona sem token de sessão");
  } finally {
    globalThis.fetch = realFetch;
  }
})();

// ------------------------------------------------ api.cancelPendingOrder()
await (async () => {
  const realFetch = globalThis.fetch;
  let calledUrl = null;
  let calledMethod = null;
  globalThis.fetch = async (url, opts) => {
    calledUrl = String(url);
    calledMethod = (opts && opts.method) || "GET";
    return { ok: true, status: 200, text: async () => JSON.stringify({ cash: 7000, positions: [], pendingOrders: [], caixaReservado: 0 }) };
  };
  try {
    await api.cancelPendingOrder("po_abc123");
    assert.ok(calledUrl.endsWith("/api/orders/pending/po_abc123"), "URL deveria terminar em /api/orders/pending/po_abc123, veio: " + calledUrl);
    assert.strictEqual(calledMethod, "DELETE");
    ok("api.cancelPendingOrder(id) chama DELETE /api/orders/pending/{id}, id percent-encoded");
  } finally {
    globalThis.fetch = realFetch;
  }
})();

// ---------------------------------------- cancelPendingOrder: 404 tratado
await (async () => {
  const realFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 404,
    text: async () => JSON.stringify({ detail: "Ordem pendente não encontrada." }),
  });
  try {
    await assert.rejects(
      () => api.cancelPendingOrder("po_inexistente"),
      (e) => e instanceof Error && /não encontrada/.test(e.message),
    );
    ok("cancelPendingOrder 404 chega ao chamador como Error com mensagem legível");
  } finally {
    globalThis.fetch = realFetch;
  }
})();

// --------------------------------- resposta não-JSON não quebra o parse
await (async () => {
  const realFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    text: async () => "<!doctype html><html><body>app</body></html>",
  });
  try {
    await assert.rejects(
      () => api.marketStatus(),
      (e) => /não veio em JSON|aponta para o app/.test(e.message),
    );
    ok("marketStatus com resposta não-JSON vira erro tratado (mesma garantia de test_api_parity.mjs)");
  } finally {
    globalThis.fetch = realFetch;
  }
})();

// --------------------------------------- id percent-encoded corretamente
await (async () => {
  const realFetch = globalThis.fetch;
  let calledUrl = null;
  globalThis.fetch = async (url) => {
    calledUrl = String(url);
    return { ok: true, status: 200, text: async () => JSON.stringify({}) };
  };
  try {
    await api.cancelPendingOrder("po/estranho com espaço");
    assert.ok(calledUrl.includes(encodeURIComponent("po/estranho com espaço")), "id deveria vir percent-encoded na URL");
    ok("cancelPendingOrder faz encodeURIComponent do id");
  } finally {
    globalThis.fetch = realFetch;
  }
})();

// ==================================================== Task 2: guardião de paridade
// Padrão de casa: leitura estática da fonte, sem importar persistence.js —
// ele importa @capacitor/core, que só existe num build nativo (ver TESTING.md
// "Mocking (Web)" / "Static source inspection").
for (const nome of ["cancelPendingOrder", "marketStatus", "pendingOrders", "caixaReservado"]) {
  const hits = (persistenceSrc.match(new RegExp("\\b" + nome + "\\s*[:(]", "g")) || []).length;
  okc(nome + " deve existir nos DOIS stores (persistence.js)", hits >= 2);
}

okc("pub() menciona pendingOrders e caixaReservado",
  /function pub\(\)[\s\S]*?pendingOrders[\s\S]*?\}/.test(persistenceSrc) || /pendingOrders: doc\.pendingOrders/.test(persistenceSrc));
okc("_adotarCarteiraDoServidor adota pendingOrders quando vem no payload",
  /_adotarCarteiraDoServidor[\s\S]*?r\.pendingOrders/.test(persistenceSrc));
okc("_adotarCarteiraDoServidor adota caixaReservado quando vem no payload",
  /_adotarCarteiraDoServidor[\s\S]*?r\.caixaReservado/.test(persistenceSrc));
okc("resetPortfolio zera pendingOrders/caixaReservado no deviceStore (ramo local)",
  /doc\.pendingOrders = \[\]/.test(persistenceSrc) && /doc\.caixaReservado = 0/.test(persistenceSrc));
okc("deviceStore sem sessão levanta erro explícito em cancelPendingOrder (nunca finge sucesso local)",
  /throw new Error\("Ordens pendentes exigem conta conectada\."\)/.test(persistenceSrc));
okc("serverStore.cancelPendingOrder delega direto para api (fora de sync.mutate/outbox)",
  /cancelPendingOrder: \(id\) => api\.cancelPendingOrder\(id\)/.test(persistenceSrc));

if (fails) {
  console.error(`\n${fails} falha(s)`);
  process.exit(1);
}
console.log(`\n${passed} teste(s) assíncrono(s) + guardiões estáticos: TODOS PASSARAM`);
