// Quick 261006-dvf (2026-10-06): retorno acumulado com base errada (+10.193 %).
// Paridade: MESMO fixture lido por server/tests/test_retorno_acumulado_base.py.
// `budget` 10000 em todas as chamadas prova que o orçamento não é divisor.
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { resolverBaseSerie, equityCurve } from "../src/finance.js";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const r2 = (v) => (v == null ? null : Math.round(v * 100) / 100);

const fixture = JSON.parse(readFileSync(
  join(here, "..", "..", "server", "tests", "fixtures", "retorno_acumulado_casos.json"), "utf8"));
ok("fixture tem 11 casos", fixture.casos.length === 11);

for (const c of fixture.casos) {
  const antes = JSON.stringify(c.snapshots);
  const e = c.esperado;
  const r = resolverBaseSerie(c.snapshots);
  ok(`${c.nome}: leitura não muta a entrada`, JSON.stringify(c.snapshots) === antes);
  ok(`${c.nome}: origem`, r.origem === e.origem);
  ok(`${c.nome}: base`, r.base === e.base);
  ok(`${c.nome}: inicio`, r.inicio === e.inicio);
  ok(`${c.nome}: desde`, r.desde === e.desde);
  const ec = equityCurve(c.snapshots, 10000, c.fim, "2099-01-01");
  ok(`${c.nome}: retAcum`, r2(ec.retAcum) === e.retAcum);
  ok(`${c.nome}: baseOrigem`, ec.baseOrigem === e.origem);
  ok(`${c.nome}: datas paralelo a curve`, ec.datas.length === ec.curve.length);
  if (e.drawdown !== undefined) ok(`${c.nome}: drawdown ${e.drawdown}`, r2(ec.drawdown) === e.drawdown);
}
{
  const c = fixture.casos[0];
  const ec = equityCurve(c.snapshots, 10000, c.fim, "2099-01-01");
  ok("caso real: retAcum < 100 (nunca +10.193 %)", ec.retAcum < 100);
}
{
  const ec = equityCurve([], 10000, 10000, "2026-10-06");
  ok("sem_serie: retAcum null (não 0)", ec.retAcum === null);
}

// ---- 2026-10-06 (quick 261006-qre): curva completa — a janela mede, a exibição mostra tudo ----
for (const c of fixture.casos) {
  const e = c.esperado;
  const antes = JSON.stringify(c.snapshots);
  const ec = equityCurve(c.snapshots, 10000, c.fim, "2099-01-01");
  const serie = resolverBaseSerie(c.snapshots).serie;
  const k = e.inicio ?? 0;
  ok(`${c.nome}: qre leitura não muta`, JSON.stringify(c.snapshots) === antes);
  ok(`${c.nome}: qre inicioNaCurvaCompleta`, ec.inicioNaCurvaCompleta === k);
  ok(`${c.nome}: qre curvaCompleta.length`, ec.curvaCompleta.length === k + ec.curve.length);
  ok(`${c.nome}: qre datasCompleta paralelo`, ec.datasCompleta.length === ec.curvaCompleta.length);
  ok(`${c.nome}: qre cauda == curve`, JSON.stringify(ec.curvaCompleta.slice(k)) === JSON.stringify(ec.curve));
  ok(`${c.nome}: qre cauda datas == datas`, JSON.stringify(ec.datasCompleta.slice(k)) === JSON.stringify(ec.datas));
  ok(`${c.nome}: qre prefixo == patrimônios anteriores`,
    JSON.stringify(ec.curvaCompleta.slice(0, k)) === JSON.stringify(serie.slice(0, k).map((s) => s.patrimonio)));
  if (k === 0) {
    ok(`${c.nome}: qre inicio 0 => mesma referência`, ec.curvaCompleta === ec.curve && ec.datasCompleta === ec.datas);
  } else {
    ok(`${c.nome}: qre todos os snapshots + live`,
      ec.datasCompleta.filter((d) => d != null).length === serie.length + 1
      && ec.curvaCompleta.at(-1) === c.fim && ec.datasCompleta.at(-1) === "2099-01-01");
  }
}
{
  const snaps = [];
  for (let i = 1; i <= 30; i++) snaps.push({ data: `2026-07-${String(i).padStart(2, "0")}`, patrimonio: 10000 + i * 10 });
  snaps.push({ data: "2026-07-31", patrimonio: 10500, base: 10500 });
  const ec = equityCurve(snaps, 10000, 10600, "2026-08-01");
  ok("qre sintético: curvaCompleta >= 32", ec.curvaCompleta.length >= 32);
  ok("qre sintético: inicioNaCurvaCompleta 30", ec.inicioNaCurvaCompleta === 30);
  ok("qre sintético: days 31", ec.days === 31);
  ok("qre sintético: diasJanela 1", ec.diasJanela === 1);
  ok("qre sintético: retAcum só desde a âncora", r2(ec.retAcum) === r2(((10600 - 10500) / 10500) * 100));
  const mesmo = equityCurve(snaps, 10000, 10700, "2026-07-31");
  ok("qre sintético: live na mesma data substitui", mesmo.curvaCompleta.at(-1) === 10700 && mesmo.curvaCompleta.length === 31 + 1);
}
{
  const ec = equityCurve([], 10000, null, "2026-10-06");
  ok("qre vazio: curvaCompleta === curve", ec.curvaCompleta === ec.curve);
}

// ---- escrita no aparelho (upsertSnapshot é privada; persistence.js importa
// @capacitor/core, então extraímos o fonte da função e a rodamos isolada) ----
const pers = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const m = pers.match(/function upsertSnapshot\(list, snap, ctx\) \{[\s\S]*?\n\}\n/);
ok("persistence.js: upsertSnapshot(list, snap, ctx) existe", !!m);
if (m) {
  const up = new Function(m[0] + "; return upsertSnapshot;")();
  const a = up([], { data: "2026-08-01", patrimonio: 999999 }, { semOperacao: true, caixa: 10000 });
  ok("sem operação: base = caixa (não o patrimônio enviado)", a[0].base === 10000);
  const b = up([], { data: "2026-08-01", patrimonio: 10000 }, { semOperacao: false, caixa: 5 });
  ok("com operação e série vazia: base null", b[0].base === null);
  const c = up(a, { data: "2026-08-02", patrimonio: 10100 }, { semOperacao: false, caixa: 5 });
  ok("com operação: herda a base do registro anterior", c[1].base === 10000);
  const d = up([{ data: "2026-07-01", patrimonio: 1000000 }], { data: "2026-07-02", patrimonio: 1004000 }, { semOperacao: false, caixa: 1 });
  ok("série legada sem base + operação: base null (nunca initialBudget)", d[1].base === null);
}
ok("deviceStore.putSnapshot passa ctx {semOperacao, caixa}", /upsertSnapshot\(doc\.equitySnapshots \|\| \[\], snap, \{ semOperacao, caixa: doc\.cash \}\)/.test(pers));
ok("resetPortfolio zera equitySnapshots nos dois ramos", (pers.match(/doc\.equitySnapshots = \[\];/g) || []).length >= 2);

// ---- guardiões estáticos de App.jsx (2026-10-06, quick 261006-dvf) ----
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
ok("App.jsx: não existe mais ((patr - budget) / budget)", !/\(\(patr - budget\) \/ budget\)/.test(app));
ok("App.jsx: usa retornoAcumuladoTxt(", /retornoAcumuladoTxt\(/.test(app));
ok("App.jsx: contexto evolucao leva retornoAcumuladoOrigem", /retornoAcumuladoOrigem:\s*ec\.baseOrigem/.test(app));
ok("App.jsx: existe `ec.retAcum == null ?` (cor neutra para base indeterminada)", /ec\.retAcum == null \?/.test(app));
ok("App.jsx: não existe (ec.retAcum || 0)", !/\(ec\.retAcum \|\| 0\)/.test(app));

// ---- 2026-10-06 (quick 261006-qre): CapitalCurve desenha a curva completa ----
{
  const i0 = app.indexOf("function CapitalCurve(");
  const i1 = app.indexOf("\nfunction ", i0 + 10);
  const cc = app.slice(i0, i1);
  ok("qre CapitalCurve: ec.curvaCompleta.map", /ec\.curvaCompleta\.map/.test(cc));
  ok("qre CapitalCurve: ec.inicioNaCurvaCompleta", /ec\.inicioNaCurvaCompleta/.test(cc));
  ok("qre CapitalCurve: curvaEvolucaoTxt(", /curvaEvolucaoTxt\(/.test(cc));
  ok("qre CapitalCurve: Ibovespa segue na janela", /benchmarkSerie\(ibov\.candles, ec\.datas\)/.test(cc));
  const pa = cc.match(/<path d=\{pathAntes\}[^>]*>/);
  ok("qre CapitalCurve: pathAntes existe", !!pa);
  ok("qre CapitalCurve: pathAntes pontilhado distinto do Ibovespa + opacidade",
    !!pa && /strokeDasharray="1 3"/.test(pa[0]) && !/strokeDasharray="3 3"/.test(pa[0]) && /strokeOpacity/.test(pa[0]));
  ok("qre CapitalCurve: legenda condicional a k > 0", /hasSeries && k > 0 &&/.test(cc));
  ok("qre CapitalCurve: ibovPath desenhado em xAt(i + k)", /xAt\(i \+ k\)/.test(cc));
}

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\nTODOS PASSARAM");
