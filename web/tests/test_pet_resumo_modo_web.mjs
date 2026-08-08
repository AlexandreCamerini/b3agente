// qa/audit-2026-08-08 (Fase 1, achado ao vivo) — no WEB, `petResumo` sempre
// mandava `?modo=estudo` explícito (default de `modo || "estudo"` em
// api.js), mesmo quando a conta estava em Modo Operador. `get_pet_resumo` no
// servidor dá PRECEDÊNCIA ao query param sobre `cfg.appMode` — então o
// vocabulário do resumo/perguntas do Boris no web nunca refletia Operador,
// silenciosamente, mesmo com a config do servidor correta. Só apareceu
// testando ao vivo: FAB some sob "MODO OPERADOR" no cabeçalho, mas as
// perguntas sugeridas continuavam as de Estudo.
//
// Este guardião prova o contrato NOVO, em runtime (não só regex de fonte):
// `store.petResumo(tela)` no store do WEB NUNCA manda `modo=` na URL — o
// servidor decide pela config do escopo, mesmo contrato já usado por
// `api.timing`.
//
// Roda sem build: `node web/tests/test_pet_resumo_modo_web.mjs`.

const chamadas = [];
globalThis.fetch = async (url) => {
  chamadas.push(String(url));
  return { ok: true, status: 200, text: async () => JSON.stringify({ ligada: true, modo: "operador", tela: "evolucao", perguntas: [] }) };
};

const { store, isNative } = await import("../src/persistence.js");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

ok("ambiente web detectado (serverStore em uso, não deviceStore)", isNative === false);

{
  chamadas.length = 0;
  await store.petResumo("evolucao");
  const chamada = chamadas.find((u) => /\/api\/pet\/resumo/.test(u));
  ok("store.petResumo(tela) chama GET /api/pet/resumo", !!chamada);
  ok("a URL NUNCA leva `modo=` — o servidor decide pela config do escopo (mesmo contrato de `timing`)",
     chamada && !/[?&]modo=/.test(chamada));
  ok("a URL leva a `tela` pedida", chamada && /[?&]tela=evolucao/.test(chamada));
}

console.log();
console.log(fails === 0 ? "TODOS OS TESTES DE MODO DO RESUMO (WEB) PASSARAM" : fails + " TESTE(S) FALHARAM");
process.exit(fails === 0 ? 0 : 1);
