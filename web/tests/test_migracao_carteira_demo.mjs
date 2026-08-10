// Espelho de `store.migrar_carteira_demo` para o doc LOCAL do aparelho (iOS).
// Corrigir o estado padrão só valeu para instalações novas; no iOS o doc é
// local-first, então quem já tinha o app seguia com R$ 23.600 em ações NUNCA
// PAGAS e +236% de retorno acumulado na abertura.
import { limparCarteiraDemo } from "../src/migrate.js";
let fails = 0;
const ok = (n, c) => { console.log((c ? "ok " : "FALHOU ") + n); if (!c) fails++; };

const demo = () => ({
  config: { initialBudget: 10000 },
  cash: 10000,                       // INTACTO: ninguém pagou
  positions: [
    { t: "PETR4", qty: 300, avg: 36.8 },
    { t: "ITUB4", qty: 200, avg: 31.1 },
    { t: "VALE3", qty: 100, avg: 63.4 },
  ],
  history: [
    { date: "18/06/2026 11:02", type: "COMPRA", t: "PETR4", qty: 300, price: 36.8 },
    { date: "17/06/2026 10:12", type: "COMPRA", t: "ITUB4", qty: 200, price: 31.1 },
    { date: "12/06/2026 09:58", type: "COMPRA", t: "VALE3", qty: 100, price: 63.4 },
  ],
  equitySnapshots: [{ data: "2026-08-01", patrimonio: 37908 }],
});

{
  const d = limparCarteiraDemo(demo());
  ok("remove as posições de fábrica", d.positions.length === 0);
  ok("remove as compras fabricadas", d.history.length === 0);
  ok("zera a série medida sobre o patrimônio inflado", d.equitySnapshots.length === 0);
}
{ // idempotente
  const d = limparCarteiraDemo(limparCarteiraDemo(demo()));
  ok("idempotente", d.positions.length === 0);
}
{ // caixa mexido = a pessoa operou de verdade
  const doc = demo(); doc.cash = 4200;
  ok("NÃO toca carteira real (caixa debitado)", limparCarteiraDemo(doc).positions.length === 3);
}
{ // mesma ação, quantidade diferente
  const doc = demo(); doc.positions[0].qty = 400;
  ok("NÃO toca quem só parece com a demo", limparCarteiraDemo(doc).positions.length === 3);
}
{ // operação real no histórico sobrevive
  const doc = demo();
  const minha = { date: "01/08/2026 10:00", type: "VENDA", t: "PETR4", qty: 100, price: 40 };
  doc.history = [minha, ...doc.history];
  const d = limparCarteiraDemo(doc);
  ok("preserva operação real no histórico", d.history.length === 1 && d.history[0].type === "VENDA");
}
{ // doc degradado não estoura
  ok("doc vazio não estoura", !!limparCarteiraDemo({}) && !!limparCarteiraDemo(null));
}

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
