// Fase 51 (D-13, plano 03) — guardião do opt-in `fechamento` FORA do sync do
// aparelho. Semântica invertida em relação a test_push_prefs_classes.mjs:
// radar/execucao/protecao são opt-out (`n.k !== false`); `fechamento` é opt-in
// e o consentimento só é gravado pela rota de convite / criação de conta.
// Se `_pushPrefsLocais` ou `syncPushPrefs` mandassem `fechamento`, todo sync
// do aparelho sobrescreveria a decisão do usuário com o default local.
//
// Roda sem build: `node web/tests/test_dia_na_bolsa_push_prefs.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const pushPy = readFileSync(join(here, "..", "..", "server", "app", "push.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

ok('push.py: `"fechamento": False` em PREFS_PADRAO', /"fechamento": False/.test(pushPy));
ok('push.py: `"fechamentoDecidido": False` em PREFS_PADRAO', /"fechamentoDecidido": False/.test(pushPy));
const bools = (pushPy.match(/^PREFS_BOOLS\s*=.*$/m) || [""])[0];
ok("PREFS_BOOLS localizado e sem `fechamento`", bools.length > 0 && !/fechamento/.test(bools));

const corpoLocais = (persistence.match(/function _pushPrefsLocais\(\) \{[\s\S]*?\n {2}\}\n/) || [""])[0];
ok("corpo de `_pushPrefsLocais` localizado", corpoLocais.length > 0);
ok("`_pushPrefsLocais` não menciona `fechamento`", !/fechamento/.test(corpoLocais));

const corpoSync = (persistence.match(/syncPushPrefs: async \(\) => \{[\s\S]*?\n {4}\},/) || [""])[0];
ok("corpo de `serverStore.syncPushPrefs` localizado", corpoSync.length > 0);
ok("`serverStore.syncPushPrefs` não menciona `fechamento`", !/fechamento/.test(corpoSync));

ok("nenhuma `fechamento: n.fechamento` em persistence.js", !/fechamento:\s*n\.fechamento/.test(persistence));

if (fails) { console.error(`${fails} falha(s)`); process.exit(1); }
console.log("OK");
