// qa/29 (B-model) — Guardião: deviceStore.scanDeep() (persistence.js) tem que
// mandar `config` (doc.config, com o BYOK/modelo configurado no aparelho)
// pro servidor, exatamente como analyze() e analyzeStopAlvo() já fazem.
//
// BUG: scanDeep era a ÚNICA chamada de IA que esquecia de mandar `config` —
// só repassava `appMode`. Sem login (scope=None do lado do servidor) e sem
// BYOK no corpo, `_ai_apply_managed` (server/app/main.py) não tem gerenciada
// disponível e devolve a config vazia recebida; `llm.py` explode com
// "Nenhum modelo de IA configurado." (code="missing_model"). Sintoma na UI:
// clicar em "Plano da mesa (IA)" (botão do Radar) "não acha o modelo LLM".
//
// Fix: `config: doc.config` entra no body ANTES do spread de `body`, igual
// ao padrão de analyze()/analyzeStopAlvo(). Este guardião tranca isso via
// checagem estática do fonte (persistence.js importa @capacitor/core, que
// não existe fora do build — mesma convenção usada pelos outros guardiões
// deste projeto para varrer trechos do App.jsx/persistence.js sem build).
// Roda sem build: `node web/tests/test_scandeep_config.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Extrai o corpo do método "async scanDeep(body) { ... }," dentro do objeto
// literal do deviceStore (delimitado pela vírgula de fechamento do método
// seguinte, "},\n    async scanDeepEstimate").
const m = /async scanDeep\(body\)\s*\{[\s\S]*?\n\s*\},/.exec(src);
ok("scanDeep: método localizado em persistence.js", !!m);
const body = m ? m[0] : "";

ok("scanDeep: manda config: doc.config pro servidor (BYOK/modelo do aparelho)",
  /config:\s*doc\.config/.test(body));

ok("scanDeep: config vem ANTES do spread do body (não pode ser sobrescrito por ...(body || {}))",
  (() => {
    const iConfig = body.indexOf("config:");
    const iSpread = body.indexOf("...(body");
    return iConfig >= 0 && iSpread >= 0 && iConfig < iSpread;
  })());

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
