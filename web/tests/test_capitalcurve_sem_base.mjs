// 2026-10-07 (quick 261007-w5t): sem base determinável, a curva da Evolução não
// vira série plana em 0 — null nunca vira 0 (CLAUDE.md princípios 4/5; achado da 261006-qre).
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const fin = await import(join(here, "..", "src", "finance.js"));
const { equityCurve, pctDesdeBase } = fin;

console.log("---- unitário: pctDesdeBase / equityCurve sem base ----");
const temFn = typeof pctDesdeBase === "function";
ok("pctDesdeBase exportada", temFn);
if (temFn) {
  ok("base válida: [0, 10]", JSON.stringify(pctDesdeBase([10000, 11000], 10000)) === JSON.stringify([0, 10]));
  ok("base null -> null", pctDesdeBase([10000, 10500], null) === null);
  for (const [nome, b] of [["0", 0], ["-5", -5], ["NaN", NaN], ["undefined", undefined], ["string", "10000"]]) {
    ok(`base ${nome} -> null`, pctDesdeBase([10000, 10500], b) === null);
  }
  for (const [nome, c] of [["null", null], ["undefined", undefined], ["objeto", {}]]) {
    ok(`curva ${nome} -> null`, pctDesdeBase(c, 10000) === null);
  }
  const r = pctDesdeBase([10000, NaN, null, 11000], 10000);
  ok("elemento não finito -> null naquela posição, demais calculados",
    Array.isArray(r) && r[0] === 0 && r[1] === null && r[2] === null && r[3] === 10);

  // inconsistente
  const inc = equityCurve([
    { data: "2026-09-01", patrimonio: 10000, base: 10000 },
    { data: "2026-09-02", patrimonio: 12000, base: 11000 },
    { data: "2026-09-03", patrimonio: 12100, base: 11000 },
  ], 10000, 12200, "2026-09-04");
  ok("inconsistente: origem/base/days/retAcum",
    inc.baseOrigem === "inconsistente" && inc.base === null && inc.days === 3 && inc.retAcum === null);
  ok("inconsistente: pctDesdeBase === null (não série de zeros)", pctDesdeBase(inc.curvaCompleta, inc.base) === null);

  // sem_serie
  const ss = equityCurve([
    { data: "2026-09-01", patrimonio: 0 },
    { data: "2026-09-02", patrimonio: 100 },
    { data: "2026-09-03", patrimonio: 200 },
  ], 10000, 200, "2026-09-03");
  ok("sem_serie: origem/base/days", ss.baseOrigem === "sem_serie" && ss.base === null && ss.days === 3);
  ok("sem_serie: pctDesdeBase === null", pctDesdeBase(ss.curvaCompleta, ss.base) === null);

  // caminho feliz
  const pr = equityCurve([
    { data: "2026-09-01", patrimonio: 10000 },
    { data: "2026-09-02", patrimonio: 10500 },
    { data: "2026-09-03", patrimonio: 10200 },
  ], 10000, 10300, "2026-09-04");
  const p = pctDesdeBase(pr.curvaCompleta, pr.base);
  ok("primeiro_registro: base 10000", pr.base === 10000);
  ok("primeiro_registro: mesmo length, [0]===0, último ≈ 3",
    Array.isArray(p) && p.length === pr.curvaCompleta.length && p[0] === 0 && Math.abs(p[p.length - 1] - 3) < 1e-9);
  ok("primeiro_registro: idêntico ao cálculo antigo",
    JSON.stringify(p) === JSON.stringify(pr.curvaCompleta.map((v) => ((v - pr.base) / pr.base) * 100)));
}

console.log("---- estático: corpo de CapitalCurve ----");
{
  const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
  const i0 = app.indexOf("function CapitalCurve(");
  const i1 = app.indexOf("\nfunction ", i0 + 10);
  const cc = app.slice(i0, i1);
  ok("corpo isolado", i0 > 0 && i1 > i0);
  ok("usa pctDesdeBase(ec.curvaCompleta, ec.base)", /pctDesdeBase\(ec\.curvaCompleta, ec\.base\)/.test(cc));
  const linhaPct = cc.split("\n").find((l) => /const pctCarteira =/.test(l)) || "";
  ok("linha pctCarteira existe e usa o helper", linhaPct !== "" && linhaPct.includes("pctDesdeBase(ec.curvaCompleta, ec.base)"));
  ok("linha pctCarteira sem `: 0)` / `|| 0` / `?? 0`",
    !/:\s*0\s*\)|\|\|\s*0\b|\?\?\s*0\b/.test(linhaPct.split("//")[0]));
  ok("const desenhaCurva = hasSeries && temBase", /const desenhaCurva = hasSeries && temBase/.test(cc));
  ok("path sob if (desenhaCurva) {", /if \(desenhaCurva\) \{/.test(cc));
  ok("SVG: desenhaCurva ? ... : hasSeries ? null : placeholder", /desenhaCurva\s*\?/.test(cc) && /hasSeries \? null :/.test(cc));
  ok("overlay '—' sob hasSeries && !temBase &&", /hasSeries && !temBase &&/.test(cc));
  ok("diffIbov exige retAcum != null", /temIbov && retAcum != null && bm\.retAcum != null/.test(cc));
  ok("efeito Ibovespa: !hasSeries e !temBase, deps com temBase",
    /if \(!hasSeries\) return/.test(cc) && /if \(!temBase\) return/.test(cc) && /\[period, hasSeries, temBase\]/.test(cc));
  ok("fraseRet segue renderizado", /\{fraseRet && \(/.test(cc));

  const { COPY } = await import(join(here, "..", "src", "copy.js"));
  for (const modo of ["estudo", "operador"]) {
    for (const est of ["inconsistente", "sem_serie"]) {
      const t = (((COPY[modo] || {}).retornoAcumulado || {})[est]) || "";
      ok(`COPY.${modo}.retornoAcumulado.${est} começa com "Não há dados suficientes para concluir."`,
        t.startsWith("Não há dados suficientes para concluir."));
    }
  }
}

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\nTODOS PASSARAM");
