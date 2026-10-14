// Quick 261013-u7w (2026-10-13): regra D4 (fechamento nao e sobrescrito por app)
// no espelho do deviceStore. MESMA fixture lida por
// server/tests/test_snapshot_convivencia.py (store.upsert_snapshot).
// persistence.js importa @capacitor/core: extraimos o fonte de upsertSnapshot
// pelo mesmo regex do guardiao test_retorno_acumulado_base.mjs e rodamos isolado.
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const fixture = JSON.parse(readFileSync(
  join(here, "..", "..", "server", "tests", "fixtures", "snapshot_convivencia_casos.json"), "utf8"));
ok("fixture tem 7 casos", fixture.casos.length === 7);

const pers = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const m = pers.match(/function upsertSnapshot\(list, snap, ctx\) \{[\s\S]*?\n\}\n/);
ok("persistence.js: upsertSnapshot(list, snap, ctx) existe", !!m);
if (m) {
  const up = new Function(m[0] + "; return upsertSnapshot;")();
  for (const c of fixture.casos) {
    let lista = JSON.parse(JSON.stringify(c.inicial));
    for (const p of c.passos) {
      lista = up(lista, { data: p.data, patrimonio: p.patrimonio }, { semOperacao: true, caixa: 0, origem: p.origem });
    }
    const got = lista.map((s) => [s.data, s.patrimonio, s.origem]);
    const want = c.final.map((s) => [s.data, s.patrimonio, s.origem]);
    ok(c.nome, JSON.stringify(got) === JSON.stringify(want));
  }
  // C2 devolve a lista intacta (mesma referencia: nada foi gravado)
  const base = up([], { data: "2026-10-13", patrimonio: 200 }, { semOperacao: true, caixa: 0, origem: "fechamento" });
  const ign = up(base, { data: "2026-10-13", patrimonio: 1 }, { semOperacao: true, caixa: 0, origem: "app" });
  ok("app ignorado devolve a lista intacta", ign === base);
  // origem desconhecida vira app; fonte/hora
  const o = up([], { data: "2026-10-13", patrimonio: 1 }, { semOperacao: true, caixa: 0, origem: "qualquer" });
  ok("origem desconhecida vira app", o[0].origem === "app" && o[0].fonte === null);
  ok("hora default HH:MM", /^\d{2}:\d{2}$/.test(o[0].hora));
  const f = up([], { data: "2026-10-13", patrimonio: 1 }, { semOperacao: true, caixa: 0, origem: "fechamento", fonte: "brapi", hora: "17:06" });
  ok("fonte e hora do ctx", f[0].fonte === "brapi" && f[0].hora === "17:06" && f[0].origem === "fechamento");
  // o corpo do snap nao define origem
  const forj = up([], { data: "2026-10-13", patrimonio: 1, origem: "fechamento" }, { semOperacao: true, caixa: 0 });
  ok("corpo do snap nao forja fechamento", forj[0].origem === "app");
}
ok("deviceStore.putSnapshot chama upsertSnapshot sem origem", /upsertSnapshot\(doc\.equitySnapshots \|\| \[\], snap, \{ semOperacao, caixa: doc\.cash \}\)/.test(pers));

process.exit(fails ? 1 : 0);
