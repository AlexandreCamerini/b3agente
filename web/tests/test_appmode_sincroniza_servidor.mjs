// qa/audit-2026-08-08 — appMode/operadorTermo eram 100% locais no aparelho
// nativo, mesmo logado. Isso quebrava toda trava do servidor que depende de
// config.appMode: `store.set_agent` só grava entradaAuto=True (ou
// mode="executar") quando o SERVIDOR enxerga appMode="operador" — e ele
// nunca enxergava, porque nada sincronizava a troca de modo. Sintoma real do
// Alex: liga "Entrar automaticamente" em Modo Operador no iPhone, o toggle
// volta pra desligado sozinho (o servidor recusa e devolve entradaAuto:false,
// que o app adota de volta) — mesmo com a conta genuinamente em Operador.
//
// Este guardião prova o contrato NOVO: LOGADO, putConfig({appMode}) ou
// putConfig({operadorTermo}) chama PUT /api/config com esses dois campos —
// nunca a apiKey, que segue exclusiva do aparelho. SEM login, nada muda.
//
// Roda sem device nem build: `node web/tests/test_appmode_sincroniza_servidor.mjs`.

globalThis.CapacitorCustomPlatform = { name: "ios" };
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => { mem.set(k, String(v)); },
  removeItem: (k) => { mem.delete(k); },
};

const chamadas = [];
globalThis.fetch = async (url, opts) => {
  const method = (opts && opts.method) || "GET";
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  chamadas.push({ url: String(url), method, body });
  if (/\/api\/config$/.test(url) && method === "PUT") {
    return { ok: true, status: 200, text: async () => JSON.stringify({ ok: true }) };
  }
  return { ok: true, status: 200, text: async () => JSON.stringify({}) };
};

const { store, isNative } = await import("../src/persistence.js");
const sync = await import("../src/sync.js");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

ok("ambiente nativo detectado (deviceStore em uso)", isNative === true);

// ---- SEM sessão: appMode continua 100% local (comportamento preservado) ----
{
  chamadas.length = 0;
  await store.putConfig({ appMode: "operador" });
  const chamouConfig = chamadas.some((c) => /\/api\/config$/.test(c.url));
  ok("sem login, putConfig({appMode}) NÃO chama o servidor", !chamouConfig);
}

// ---- COM sessão: appMode/operadorTermo sincronizam com o servidor ---------
sync.saveToken("token-de-teste");
ok("sessão estabelecida (sync.hasSession)", sync.hasSession() === true);

{
  chamadas.length = 0;
  const termo = { aceitoEm: "2026-08-08T00:00:00.000Z", versao: "1" };
  await store.putConfig({ operadorTermo: termo, appMode: "operador" });
  const chamada = chamadas.find((c) => /\/api\/config$/.test(c.url) && c.method === "PUT");
  ok("logado, putConfig({appMode, operadorTermo}) CHAMA PUT /api/config", !!chamada);
  ok("o corpo leva appMode confirmado", chamada && chamada.body.appMode === "operador");
  ok("o corpo leva operadorTermo", chamada && chamada.body.operadorTermo && chamada.body.operadorTermo.versao === "1");
  ok("o corpo NUNCA leva apiKey — essa fica só no aparelho", chamada && !("apiKey" in chamada.body));
}

{
  // Troca de campo que NÃO é appMode/operadorTermo (ex.: tema) não deve
  // gerar chamada nenhuma — o sync é cirúrgico, só os dois campos que os
  // gates do servidor precisam.
  chamadas.length = 0;
  await store.putConfig({ theme: "dark" });
  const chamouConfig = chamadas.some((c) => /\/api\/config$/.test(c.url));
  ok("logado, putConfig({theme}) (sem appMode/operadorTermo) NÃO chama o servidor", !chamouConfig);
}

console.log();
console.log(fails === 0 ? "TODOS OS TESTES DE SYNC DE APPMODE PASSARAM" : fails + " TESTE(S) FALHARAM");
process.exit(fails === 0 ? 0 : 1);
