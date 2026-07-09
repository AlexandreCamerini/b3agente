// qa/28 — Guardião: o proxy do plugin nativo (LocalNotifications) nunca pode
// ser o valor "solto" de um return/await dentro deste módulo.
//
// BUG (qa/28): o objeto do plugin Capacitor responde a QUALQUER nome de
// método, inclusive "then" — se ele for retornado direto de uma async
// function (ou virar o valor resolvido de uma Promise), o motor JS o trata
// como "thenable" e chama .then() nele, virando uma chamada de bridge nativa
// para o método inexistente "then": "LocalNotifications.then() is not
// implemented on ios". Isso quebrava TODA chamada nativa de notify.js
// (Diagnóstico, Pedir permissão, agendar, cancelar) mesmo com o plugin
// corretamente linkado no binário — nenhum guardião de arquivo pega isso,
// porque é um bug de SEMÂNTICA de runtime, não de conteúdo estático.
// Contrato travado aqui: plugin() só pode devolver o proxy DENTRO de um
// objeto comum ({ p: ... }); todo call site precisa desestruturar ({ p }),
// nunca capturar o retorno bruto.
// Roda sem build: `node web/tests/test_notify_plugin_boxing.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "notify.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// plugin() deve sempre devolver um objeto boxed, nunca o proxy cru.
const pluginBody = (src.match(/async function plugin\(\)\s*\{[\s\S]*?\n\}/) || [""])[0];
ok("plugin() existe e foi localizado", pluginBody.length > 0);
ok("plugin() nunca faz 'return _plugin;' (proxy cru)", !/return\s+_plugin\s*;/.test(pluginBody));
ok("plugin() sempre devolve boxed '{ p: ... }'", (pluginBody.match(/return\s*\{\s*p\s*:/g) || []).length >= 2);

// nenhum call site pode capturar o retorno de plugin() sem desestruturar.
const callSitesCrus = (src.match(/const\s+p\s*=\s*await\s+plugin\(\)/g) || []);
ok("nenhum call site faz 'const p = await plugin()' sem desestruturar", callSitesCrus.length === 0);

const callSitesBoxed = (src.match(/const\s*\{\s*p\s*\}\s*=\s*await\s+plugin\(\)/g) || []);
ok("existem call sites usando a forma correta 'const { p } = await plugin()'", callSitesBoxed.length >= 5);

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
