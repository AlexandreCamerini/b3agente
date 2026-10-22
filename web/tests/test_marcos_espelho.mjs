// ESPELHO DOS MARCOS (Fase 50, plano 50-08) — finance.js x setups.py pela MESMA
// fixture do pytest (server/tests/fixtures/marcos_casos.json).
// Roda sem build: `node web/tests/test_marcos_espelho.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { validarMarcos, marcosEfetivos, rrDaEntrada, sizingPlano, MOTIVO_SEM_PRECO_VALIDAR } from "../src/finance.js";

const here = dirname(fileURLToPath(import.meta.url));
const fx = JSON.parse(readFileSync(join(here, "..", "..", "server", "tests", "fixtures", "marcos_casos.json"), "utf8"));

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};

for (const c of fx.geometria) {
  const e = c.entrada;
  const got = e.constante === "MOTIVO_SEM_PRECO_VALIDAR"
    ? MOTIVO_SEM_PRECO_VALIDAR
    : validarMarcos(e.stop, e.alvo, e.preco, e.avg);
  ok("geometria: " + c.nome, got === c.esperado.motivo, JSON.stringify(got));
}

for (const c of fx.rr) {
  const got = rrDaEntrada(c.entrada.entrada, c.entrada.stop, c.entrada.alvo);
  const exp = c.esperado.rr;
  ok("rr: " + c.nome, exp === null ? got === null : got !== null && Math.abs(got - exp) < 1e-9, String(got));
}

for (const c of fx.sizing) {
  const e = c.entrada, x = c.esperado;
  const plano = { decisao: "COMPRAR", entrada: e.entrada, riscoPorAcao: e.entrada - e.stop };
  const opts = e.caixa != null ? { caixa: e.caixa, allocPct: e.alloc_pct } : undefined;
  const got = sizingPlano(plano, e.capital, e.pct, opts);
  let good = got !== null && got.qtd === x.qtd;
  if ("pct" in x) good = good && got.pct === x.pct;
  if ("limitadoPor" in x) good = good && got.limitadoPor === x.limitadoPor;
  if ("valorAprox" in x) good = good && got.valorAprox === x.valorAprox;
  if ("riscoFinanceiro" in x) good = good && got.riscoFinanceiro === x.riscoFinanceiro;
  if ("aviso" in x) good = good && got.aviso === x.aviso;
  if (x.avisoContem) good = good && x.avisoContem.every((t) => (got.aviso || "").includes(t));
  ok("sizing: " + c.nome, good, JSON.stringify(got));
}

// Review WR-02 — marco por marco (espelho de agent.marcos_efetivos)
{
  const origem = marcosEfetivos({ avg: 23.01, stop: 23.36, alvo: 21.58 });
  ok("marcos_efetivos: caso-origem mantém o stop e anula só o alvo", origem.stopVale && !origem.alvoVale && !!origem.motivo, JSON.stringify(origem));
  const valido = marcosEfetivos({ avg: 20, stop: 19, alvo: 25 });
  ok("marcos_efetivos: plano íntegro", valido.stopVale && valido.alvoVale && valido.motivo === null, JSON.stringify(valido));
  const stopRuim = marcosEfetivos({ avg: 20, stop: 0, alvo: 25 });
  ok("marcos_efetivos: stop não positivo é suprimido, alvo segue", !stopRuim.stopVale && stopRuim.alvoVale && !!stopRuim.motivo, JSON.stringify(stopRuim));
}

if (fails) { console.log("\n" + fails + " falha(s)"); process.exit(1); }
console.log("\nTodos os casos do espelho de marcos passaram.");
