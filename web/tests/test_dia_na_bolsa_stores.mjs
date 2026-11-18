// Fase 51-06 — paridade deviceStore <-> serverStore dos métodos do card
// "Seu dia na bolsa", diasDecisao por união e consentimento fora do sync de prefs.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const dir = path.dirname(fileURLToPath(import.meta.url));
const pers = fs.readFileSync(path.join(dir, "../src/persistence.js"), "utf8");
const api = fs.readFileSync(path.join(dir, "../src/api.js"), "utf8");
let falhas = 0;
const ok = (c, m) => { if (c) console.log("ok " + m); else { console.error("FALHA " + m); falhas++; } };

for (const nome of ["getDiaNaBolsa", "registrarVistos", "decidirFechamento"]) {
  const n = (pers.match(new RegExp(`^\\s*(async\\s+)?${nome}\\s*(\\(|:)`, "gm")) || []).length;
  ok(n === 2, `${nome} definido nos dois stores (achou ${n})`);
}
ok(/Array\.isArray\(patch\.diasDecisao\)\) c\.diasDecisao = uniaoDiasDecisao\(/.test(pers), "deviceStore.putConfig une diasDecisao");
ok(/k === "diasDecisao"/.test(pers), "patch otimista do serverStore une diasDecisao");
ok(/\\d\{4\}-\\d\{2\}-\\d\{2\}/.test(pers) && /DIAS_DECISAO_MAX = 60/.test(pers), "regex AAAA-MM-DD e teto 60");
for (const rota of ["/api/dia-na-bolsa\"", "/api/dia-na-bolsa/vistos", "/api/dia-na-bolsa/convite"]) {
  ok(api.includes(rota) || api.includes(rota.replace(/"$/, "")), `api.js contém ${rota}`);
}
const m = pers.match(/function _pushPrefsLocais\(\)[\s\S]*?\n  }\n/);
ok(!!m, "_pushPrefsLocais localizada");
ok(m && !/fechamento/.test(m[0]), "_pushPrefsLocais não carrega fechamento");
const s = pers.match(/syncPushPrefs: async \(\) => \{[\s\S]*?\n    \},/);
ok(!s || !/fechamento/.test(s[0]), "serverStore.syncPushPrefs não carrega fechamento");
if (falhas) process.exit(1);
console.log("tudo ok");
