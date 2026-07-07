// FASE 2 (Revisão Total) — Portfólio no DEVICE STORE (iOS/localStorage):
// venda TOTAL (comportamento original) e PARCIAL em lotes de 100 com preço
// médio preservado, e meta de ENTRADA (setup do STU) sanitizada e registrada
// na posição e no histórico — espelho exato de server/tests/test_fase2_portfolio.py,
// provando a invariante "mesma interface e mesma semântica nos DOIS stores".
// Roda sem device nem build: `node web/tests/test_fase2_portfolio.mjs`.

// ---- ambiente de aparelho simulado ANTES do import (Capacitor + localStorage) ----
// @capacitor/core sobrescreve isNativePlatform de um global pré-existente; o
// gancho oficial para simular plataforma é CapacitorCustomPlatform.
globalThis.CapacitorCustomPlatform = { name: "ios" };
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => { mem.set(k, String(v)); },
  removeItem: (k) => { mem.delete(k); },
};
// cotações mockadas (deviceStore.priceOf usa api.getQuotes)
globalThis.fetch = async () => ({
  ok: true,
  status: 200,
  text: async () => JSON.stringify({ quotes: { WEGE3: { price: 40.0, change: 1.2 }, RADL3: { price: 20.0, change: 0.5 } } }),
});

const { store, isNative } = await import("../src/persistence.js");
// nativo exige base absoluta; o caminho canônico é a config do doc (o boot do
// deviceStore aplica doc.config.serverUrl por cima de qualquer setApiBase).
await store.putConfig({ serverUrl: "http://mock.local" });

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

ok("ambiente nativo detectado (deviceStore em uso)", isNative === true);

const META = { setup: "Setup 9.2 (alta)", lado: "alta", veredito: "Estudar alta", snapshotId: "abc12345", gatilho: 38.5, invalidacao: 36.9, confluencia: 86, malicioso: "x".repeat(500) };

// 1) compra com meta em ticker FORA do seed demo: posição nova ganha
// setupEntrada sanitizado + abertaEm; histórico ganha setup/snapshotId
let aposCompra;
{
  aposCompra = await store.buy("WEGE3", 200, META); // 200×R$40 cabe no caixa demo
  const pos = aposCompra.positions.find((p) => p.t === "WEGE3");
  ok("buy registra setupEntrada na posição", pos && pos.setupEntrada && pos.setupEntrada.setup === "Setup 9.2 (alta)");
  ok("meta sanitizada descarta campo desconhecido", pos && !("malicioso" in (pos.setupEntrada || {})));
  ok("posição nova ganha abertaEm", !!(pos && pos.abertaEm));
  const h = aposCompra.history[0];
  ok("histórico COMPRA carrega setup + snapshotId", h.type === "COMPRA" && h.setup === "Setup 9.2 (alta)" && h.snapshotId === "abc12345");
}

// 2) venda PARCIAL: lote de 100, avg preservado, pnl proporcional
{
  // pub() do deviceStore devolve referências vivas do doc — snapshotar ANTES
  const antes = aposCompra.positions.find((p) => p.t === "WEGE3");
  const qtyAntes = antes.qty, avgAntes = antes.avg;
  const s = await store.sell("WEGE3", 130); // arredonda para 100
  const pos = s.positions.find((p) => p.t === "WEGE3");
  ok("parcial reduz qty em lote (200→100)", pos && pos.qty === qtyAntes - 100);
  ok("parcial preserva o preço médio", pos && pos.avg === avgAntes);
  const h = s.history[0];
  ok("histórico VENDA parcial com qty=100 e pnl", h.type === "VENDA" && h.qty === 100 && typeof h.pnl === "number");
}

// 3) venda TOTAL sem qty (comportamento original preservado)
{
  const s = await store.sell("WEGE3");
  ok("venda total remove a posição", !s.positions.find((p) => p.t === "WEGE3"));
  ok("histórico VENDA total registrado", s.history[0].type === "VENDA" && s.history[0].t === "WEGE3");
}

// 4) compra SEM meta preserva o shape original (sem chaves novas)
{
  const s = await store.buy("RADL3", 100);
  const pos = s.positions.find((p) => p.t === "RADL3");
  ok("buy sem meta não cria setupEntrada", pos && !("setupEntrada" in pos));
  ok("histórico sem meta não cria setup", !("setup" in s.history[0]));
}

// 5) persistência: doc sobrevive no localStorage (reimport = reabrir o app)
{
  const raw = [...mem.keys()].find((k) => k.startsWith("b3"));
  ok("doc persistido no localStorage do aparelho", !!raw && mem.get(raw).includes("RADL3"));
}

console.log();
console.log(fails === 0 ? "TODOS OS TESTES DO PORTFÓLIO F2 (DEVICE) PASSARAM" : fails + " TESTE(S) FALHARAM");
process.exit(fails === 0 ? 0 : 1);
