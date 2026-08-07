// A CARTEIRA no app nativo (iPhone) era 100% local — buy/sell/putPosition só
// escreviam no localStorage do aparelho, NUNCA chamavam o servidor. Resultado
// real, confirmado em 2026-08-07: o Alex configurava stop numa posição pelo
// iPhone, e o Operador no servidor (que roda com o app FECHADO, lendo só o
// banco do servidor) nunca via esse stop — "não vendeu" porque, do ponto de
// vista do servidor, a posição nunca teve proteção nenhuma.
//
// Este guardião prova o contrato NOVO: LOGADO, buy/sell/putPosition passam a
// mão pro servidor (ele calcula preço e executa) e o doc local adota a
// resposta CONFIRMADA — nunca um cálculo local à parte que pode divergir.
// SEM login, nada muda (ver test_fase2_portfolio.mjs, que continua verde).
//
// Roda sem device nem build: `node web/tests/test_carteira_nativa_sincroniza.mjs`.

globalThis.CapacitorCustomPlatform = { name: "ios" };
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => { mem.set(k, String(v)); },
  removeItem: (k) => { mem.delete(k); },
};

// Mock de fetch CIENTE da rota: cada endpoint devolve um "estado do servidor"
// só com o que o teste precisa conferir — o bastante para provar que o doc
// local passou a refletir a RESPOSTA do servidor, não uma conta própria.
const chamadas = [];
globalThis.fetch = async (url, opts) => {
  const method = (opts && opts.method) || "GET";
  chamadas.push({ url: String(url), method });
  const body = { ok: true, status: 200 };
  if (/\/api\/buy$/.test(url) && method === "POST") {
    return { ...body, text: async () => JSON.stringify({
      positions: [{ t: "WEGE3", qty: 200, avg: 40.0, stop: null, alvo: null, abertaEm: "2026-08-07" }],
      cash: 2000.0, history: [{ date: "2026-08-07", type: "COMPRA", t: "WEGE3", qty: 200, price: 40.0, pnl: null }],
      priceUsed: 40.0,
    }) };
  }
  if (/\/api\/sell$/.test(url) && method === "POST") {
    return { ...body, text: async () => JSON.stringify({
      positions: [], cash: 10000.0,
      history: [{ date: "2026-08-07", type: "VENDA", t: "WEGE3", qty: 200, price: 41.0, pnl: 200 }],
      priceUsed: 41.0,
    }) };
  }
  if (/\/api\/position\/PETR4$/.test(url) && method === "PUT") {
    return { ...body, text: async () => JSON.stringify({
      positions: [{ t: "PETR4", qty: 300, avg: 36.8, stop: 39.5, alvo: null }],
      cash: 10000.0, history: [],
    }) };
  }
  // getState (boot) e afins: resposta genérica — inclui cotação de RADL3 só
  // para o cenário SEM sessão (buy local ainda precisa de preço).
  return { ...body, text: async () => JSON.stringify({ quotes: { RADL3: { price: 20.0, change: 0.5 } } }) };
};

const { store, isNative } = await import("../src/persistence.js");
const sync = await import("../src/sync.js");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

ok("ambiente nativo detectado (deviceStore em uso)", isNative === true);

// ---- SEM sessão: nenhuma chamada de rede pra carteira (comportamento local preservado) ----
{
  chamadas.length = 0;
  await store.putConfig({ serverUrl: "http://mock.local" });
  const antes = chamadas.length;
  await store.buy("RADL3", 100);
  const depois = chamadas.filter((c) => /\/api\/(buy|sell|position)/.test(c.url));
  ok("sem login, buy NÃO chama o servidor (continua local)", depois.length === 0);
}

// ---- COM sessão: buy/sell/putPosition passam pelo servidor -----------------
sync.saveToken("token-de-teste");
ok("sessão estabelecida (sync.hasSession)", sync.hasSession() === true);

{
  chamadas.length = 0;
  const r = await store.buy("WEGE3", 200);
  const chamouBuy = chamadas.some((c) => /\/api\/buy$/.test(c.url) && c.method === "POST");
  ok("logado, buy CHAMA /api/buy", chamouBuy);
  ok("o doc local adota as POSIÇÕES que o servidor confirmou (não um cálculo local)",
     r.positions.length === 1 && r.positions[0].t === "WEGE3" && r.positions[0].qty === 200);
  ok("o doc local adota o CAIXA que o servidor confirmou", r.cash === 2000.0);
  ok("priceUsed vem do servidor", r.priceUsed === 40.0);
}

{
  chamadas.length = 0;
  const r = await store.sell("WEGE3", 200);
  const chamouSell = chamadas.some((c) => /\/api\/sell$/.test(c.url) && c.method === "POST");
  ok("logado, sell CHAMA /api/sell", chamouSell);
  ok("posição fechada some do doc local (espelhando o servidor)", r.positions.length === 0);
  ok("caixa pós-venda vem do servidor", r.cash === 10000.0);
}

{
  // Uma posição PETR4 precisa existir no doc local pro putPosition ter algo
  // pra mostrar antes/depois — a chamada em si não depende disso (vai direto
  // pro servidor), mas simula o cenário real do Alex.
  chamadas.length = 0;
  const r = await store.putPosition("PETR4", { stop: "39.5" });
  const chamouPut = chamadas.some((c) => /\/api\/position\/PETR4$/.test(c.url) && c.method === "PUT");
  ok("logado, putPosition CHAMA PUT /api/position/PETR4", chamouPut);
  ok("o stop confirmado pelo servidor entra no doc local — o bug real que motivou este teste",
     r.positions.find((p) => p.t === "PETR4") && r.positions.find((p) => p.t === "PETR4").stop === 39.5);
}

console.log();
console.log(fails === 0 ? "TODOS OS TESTES DA CARTEIRA NATIVA SINCRONIZADA PASSARAM" : fails + " TESTE(S) FALHARAM");
process.exit(fails === 0 ? 0 : 1);
