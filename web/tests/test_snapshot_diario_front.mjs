// Quick 261013-u7w (2026-10-13): mesclarSnapshots (D5), data BRT no App e linhas do admin.
// persistence.js importa @capacitor/core: extraimos o fonte por regex e rodamos via new Function.
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const rd = (...p) => readFileSync(join(here, ...p), "utf8");

const pers = rd("..", "src", "persistence.js");
const m = pers.match(/function mesclarSnapshots\(local, servidor\) \{[\s\S]*?\n\}\n/);
ok("mesclarSnapshots(local, servidor) existe", !!m);
if (m) {
  const mescla = new Function(m[0] + "; return mesclarSnapshots;")();
  const S = (data, origem, patrimonio = 1) => ({ data, origem, patrimonio });
  const J = JSON.stringify;
  ok("M1 vazio + servidor", J(mescla([], [S("d1", "fechamento")])) === J([S("d1", "fechamento")]));
  ok("M2 app local x fechamento servidor", J(mescla([S("d1", "app", 5)], [S("d1", "fechamento", 9)])) === J([S("d1", "fechamento", 9)]));
  ok("M3 fechamento local x app servidor", J(mescla([S("d1", "fechamento", 5)], [S("d1", "app", 9)])) === J([S("d1", "fechamento", 5)]));
  ok("M4 empate app: servidor vence", J(mescla([S("d1", "app", 5)], [S("d1", "app", 9)])) === J([S("d1", "app", 9)]));
  ok("M5 empate fechamento: servidor vence", J(mescla([S("d1", "fechamento", 5)], [S("d1", "fechamento", 9)])) === J([S("d1", "fechamento", 9)]));
  ok("M6 data so no aparelho permanece", J(mescla([S("d0", "app")], [S("d1", "fechamento")])) === J([S("d0", "app"), S("d1", "fechamento")]));
  const r7 = mescla([null, 3, { patrimonio: 1 }, { data: 5 }, S("d1", "app")], ["x", { data: null }, undefined, S("d2", "fechamento")]);
  ok("M7 invalidos descartados", J(r7) === J([S("d1", "app"), S("d2", "fechamento")]));
  const dia = (i) => "2025-" + String(1 + Math.floor(i / 28)).padStart(2, "0") + "-" + String(1 + (i % 28)).padStart(2, "0");
  const loc = Array.from({ length: 200 }, (_, i) => S(dia(i), "app"));
  const srv = Array.from({ length: 210 }, (_, i) => S(dia(i + 195), "fechamento"));
  const r8 = mescla(loc, srv);
  ok("M8 cap 400 mantem as ultimas", r8.length === 400 && r8[399].data === dia(404) && r8[0].data === dia(5));
  ok("M9 servidor undefined/null => copia ordenada do local",
    J(mescla([S("d2", "app"), S("d1", "app")], undefined)) === J([S("d1", "app"), S("d2", "app")])
    && J(mescla([S("d2", "app"), S("d1", "app")], null)) === J([S("d1", "app"), S("d2", "app")]));
  const l10 = [S("d2", "app"), S("d1", "app")], s10 = [S("d1", "fechamento")];
  const l10c = J(l10), s10c = J(s10);
  const r10 = mescla(l10, s10);
  ok("M10 entradas nao mutadas", J(l10) === l10c && J(s10) === s10c && r10 !== l10 && r10 !== s10);
}

ok("estatico: _adotarCarteiraDoServidor usa mesclarSnapshots(doc.equitySnapshots", /mesclarSnapshots\(doc\.equitySnapshots/.test(pers));
ok("estatico: mesclarSnapshots nao e chave de store", !/^\s*mesclarSnapshots\s*[:(]/m.test(pers.replace(/function mesclarSnapshots\(/, "")));
ok("estatico: resetPortfolio zera equitySnapshots nos dois ramos", (pers.match(/doc\.equitySnapshots = \[\];/g) || []).length >= 2);

const app = rd("..", "src", "App.jsx");
ok("App: ymd = hojeBRT() antes do putSnapshot", /const ymd = hojeBRT\(\);\s*\n\s*const m = portfolioMetrics[^\n]*\n\s*store\.putSnapshot\(\{ data: ymd/.test(app));
ok("App: todayYmd = hojeBRT()", app.includes("const todayYmd = hojeBRT();"));
ok("App: hoje = hojeBRT() no contexto evolucao", /const hoje = hojeBRT\(\);\s*\n\s*const ec = equityCurve/.test(app));
ok("App: equityCurve(...) com hojeBRT() no 4o argumento", /equityCurve\(data\.equitySnapshots, [^\n]*m\.patr, hojeBRT\(\)\)/.test(app));
ok("App: nenhuma equityCurve( com toISOString no argumento", !/equityCurve\([^\n]*toISOString/.test(app));
ok("App: streak segue com toISOString", app.includes("const ymd = (d) => d.toISOString()"));

const adm = rd("..", "..", "web-admin", "src", "App.jsx");
ok("admin: linhas leem data.snapshotDiario", adm.includes("data.snapshotDiario?.atLabel") && adm.includes("data.snapshotDiario?.perdidasNaJanela") && adm.includes("data.snapshotDiario?.perdido"));

process.exit(fails ? 1 : 0);
