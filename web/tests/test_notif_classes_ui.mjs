// Quick task 260824-kc2 — Guardião: os controles por CLASSE do push do
// servidor, na central de Notificações (Perfil → Notificações).
//
// O INVARIANTE que este arquivo existe para travar: `rowPushClasse` NÃO pode
// ser gated por `nf.enabled`. São DOIS MESTRES —
//   `nf.enabled`      → notificações LOCAIS do front (stop/alvo/agente/variação);
//   token registrado  → push do SERVIDOR (o ato explícito é `onAtivarPush`).
// Gatear a linha do push pelo mestre local conflaciona os dois: quem registrou
// push e nunca ligou o interruptor local pararia de receber execução e
// proteção — avisos que essa pessoa RECEBE hoje, porque até 2026-08-24 os call
// sites do servidor não consultavam preferência nenhuma.
//
// Padrão source-grep (mesmo de `test_notif_central.mjs` e `test_notif_pregao
// .mjs`): lê `App.jsx` como texto, recorta por âncoras, roda regex. Sem render,
// sem build. FALHA RUIDOSAMENTE se uma âncora sumir — chunk vazio é teste mudo.
//
// Roda sem build: `node web/tests/test_notif_classes_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const conta = (s, re) => (s.match(re) || []).length;

// Asserção de AUSÊNCIA roda sobre o CÓDIGO, nunca sobre a prosa: o comentário
// que explica o helper cita `nf.enabled` de propósito (é nele que a decisão
// fica registrada), e sem isto o guardião acusaria a própria explicação — foi
// exatamente o que aconteceu em `test_notif_pregao.mjs`. A negativa `[^:]`
// preserva `https://`; só o comentário de linha cai.
const semComentarios = (s) => s.split("\n")
  .map((l) => l.replace(/(^|[^:])\/\/.*$/, "$1"))
  .join("\n");
const appCode = semComentarios(app);

function chunk(src, de, ate, rotulo) {
  const i = src.indexOf(de);
  const j = i >= 0 ? src.indexOf(ate, i + de.length) : -1;
  ok(`âncora do chunk ${rotulo} existe`, i >= 0 && j > i);
  return i >= 0 && j > i ? src.slice(i, j) : "";
}

// ---- 1) o helper existe e é usado nas três classes --------------------------
ok("rowPushClasse é definido", /const rowPushClasse = \(key, label, desc\) =>/.test(appCode));
for (const k of ["radar", "execucao", "protecao"]) {
  ok(`rowPushClasse("${k}" é chamado uma vez`,
     conta(appCode, new RegExp(`rowPushClasse\\("${k}"`, "g")) === 1);
}

// ---- 2) O INVARIANTE: o corpo do helper não conhece o mestre local ---------
const corpoHelper = chunk(appCode, "const rowPushClasse = (key, label, desc) =>", "\n  );", "rowPushClasse");
ok("o corpo de rowPushClasse NÃO cita `nf.enabled` (os dois mestres não se misturam)",
   corpoHelper.length > 0 && !/nf\.enabled/.test(corpoHelper));
ok("estado ligado é `!== false` (ausente = LIGADO, casa com push.PREFS_PADRAO)",
   /on=\{nf\[key\] !== false\}/.test(corpoHelper));
ok("não usa `=== true` (isso é a semântica do opt-in, que aqui seria regressão)",
   !/nf\[key\] === true/.test(corpoHelper));
ok("o clique escreve a classe pelo A.setNotif, sem gate",
   /onClick=\{\(\) => A\.setNotif\(\{ \[key\]: !\(nf\[key\] !== false\) \}\)\}/.test(corpoHelper));

// ---- 3) acessibilidade (princípio 10) --------------------------------------
// `Toggle` já emite role="switch" + aria-checked + aria-label={label}; o que o
// helper precisa garantir é PASSAR o rótulo.
ok("o Toggle das três linhas recebe `label`", /label=\{label\} \/>/.test(corpoHelper));
ok("Toggle continua emitindo aria-label a partir do label",
   /aria-label=\{label\}/.test(appCode));

// ---- 4) estados completos (princípio 9) ------------------------------------
ok("o estado \"nenhum aparelho com push ativo\" está explicado",
   /nenhum aparelho tiver o push ativo, nada é enviado/.test(app));
ok("o bloco de classes é gated por `logged` (preferência é da CONTA)",
   /\{logged && \([\s\S]{0,900}rowPushClasse\("radar"/.test(app));

// ---- 5) sem regressão da classe antiga -------------------------------------
ok("rowOptIn(\"gatilho\" continua existindo", conta(appCode, /rowOptIn\("gatilho"/g) === 1);
ok("rowOptIn continua com exatamente 2 ocorrências (definição + 1 uso)",
   conta(appCode, /rowOptIn/g) === 2);
const corpoOptIn = chunk(appCode, "const rowOptIn = (key, label, desc) =>", "\n  );", "rowOptIn");
ok("rowOptIn continua GATED pelo mestre local (a exceção histórica não regride)",
   corpoOptIn.length > 0 && /nf\.enabled && nf\[key\] === true/.test(corpoOptIn));

// ---- 6) A.setNotif não ganhou prompt novo ----------------------------------
// Ele pede permissão do SISTEMA só quando `patch.enabled === true`, então os
// controles novos não disparam prompt nenhum — coerente, já que push do
// servidor e permissão local são coisas diferentes.
ok("A.setNotif continua pedindo permissão só no mestre local",
   /patch\.enabled === true/.test(appCode));

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
