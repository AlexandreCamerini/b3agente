// Guardião do bug relatado em 2026-08-09 DEPOIS do fix de debounce
// (test_config_debounce_flush.mjs): "recomeçar do zero" continuava voltando
// pra 10000, mas SÓ no iOS. Causa raiz diferente da primeira rodada:
//
//   No aparelho (deviceStore), config é local-first por DESENHO — o
//   servidor "não enxerga a config deste aparelho" (comentário original de
//   registerPushToken). Mas resetPortfolio(), quando logado, NÃO reseta
//   local: chama api.resetPortfolio(), que roda no SERVIDOR e lê
//   config.initialBudget de LÁ (store.py:reset_portfolio). Editar o
//   orçamento no iPhone só escrevia no doc local — nunca sincronizava com o
//   servidor — então o reset (logado) sempre usava o orçamento VELHO do
//   servidor, nunca o que a pessoa acabou de digitar no aparelho.
//
//   Mesma classe de bug que appMode/operadorTermo já tinham (qa/audit-
//   2026-08-08): campo editado só no aparelho, mas a ação que IMPORTA roda
//   no servidor. Fix: initialBudget entra no MESMO sync explícito que
//   appMode/operadorTermo já usam (`api.putConfig` quando `sync.hasSession()`).
//
// ATUALIZADO EM 2026-08-17 (reversão deliberada de FORMA, não de intenção).
// A intenção continua idêntica e continua travada aqui: editar o orçamento no
// aparelho TEM que chegar ao servidor. O que mudou é que o payload deixou de
// ser o trio fixo {appMode, operadorTermo, initialBudget} e passou a levar só
// o campo que o chamador mexeu.
//
// Por quê: mandar `appMode` de carona era um desliga-execução silencioso.
// Editar só o ORÇAMENTO com o aparelho em Estudo enviava `appMode:"estudo"`;
// o servidor lê isso como SAÍDA do Modo Operador e reescreve `agent.mode` de
// "executar" para "sinalizar" (store.py, migração silenciosa), e voltar para
// Operador não restaura. O Operador passava a só AVISAR, nunca executar —
// relatado em produção em 2026-08-17. A forma do payload agora é guardada por
// test_putconfig_so_o_que_mudou.mjs; este arquivo guarda o orçamento.
//
// Roda sem build: `node web/tests/test_device_budget_sync.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function bodyOf(src, anchor) {
  const at = src.indexOf(anchor);
  if (at < 0) return null;
  const open = src.indexOf("{", at + anchor.length);
  let depth = 0;
  for (let i = open; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) return src.slice(open, i + 1); }
  }
  return null;
}

const putConfigBody = bodyOf(src, "async putConfig(patch)");
ok("deviceStore.putConfig localizado", !!putConfigBody);

// --- 1) editar o orçamento entra no payload enviado ao servidor ------------
ok("initialBudget entra no payload quando o patch o traz",
   !!putConfigBody && /if \(typeof patch\.initialBudget === "number"\) enviar\.initialBudget = c\.initialBudget;/.test(putConfigBody));

// --- 2) o orçamento chega ao servidor -------------------------------------
ok("api.putConfig é chamado com o payload montado",
   !!putConfigBody && /await api\.putConfig\(enviar\);/.test(putConfigBody));

// --- 2b) e vai SOZINHO: appMode não pega carona (a regressão de 2026-08-17)
ok("editar só o orçamento NÃO arrasta appMode junto",
   !!putConfigBody && !/putConfig\(\{\s*appMode: c\.appMode, operadorTermo: c\.operadorTermo,\s*initialBudget: c\.initialBudget\s*\}\)/.test(putConfigBody));

// --- 3) o sync só dispara com o patch pendente já mesclado em `c` ----------
// (garante que manda o valor NOVO, não um c.initialBudget desatualizado —
// a atribuição de c.initialBudget já acontece antes deste bloco no código)
ok("atribuição de c.initialBudget vem ANTES do bloco de sync",
   putConfigBody.indexOf("c.initialBudget = Math.max") < putConfigBody.indexOf("const enviar = {}"));

console.log(fails ? `\n${fails} FALHA(S) NO SYNC DE ORÇAMENTO DO APARELHO` : "\nSYNC DE ORÇAMENTO (DEVICE → SERVIDOR) OK");
process.exit(fails ? 1 : 0);
