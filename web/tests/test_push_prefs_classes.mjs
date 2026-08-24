// Quick task 260824-kc2 — preferência de push POR CLASSE, nos DOIS stores.
//
// Fecha o item 6 do brief de notificações: `serverStore.syncPushPrefs` existia
// e NUNCA era chamado, então no web logado ajustar push não gravava preferência
// nenhuma. Agora os dois clientes escrevem — cada um o que lhe cabe.
//
// DOIS INVARIANTES, um teste próprio para cada:
//
//  1. DOIS MESTRES, não um. `config.notif.enabled` é o mestre das notificações
//     LOCAIS do front; o mestre do push do SERVIDOR é o token registrado (ato
//     explícito e separado, `onAtivarPush`). As três classes refinam o SEGUNDO,
//     por isso são opt-out puro. Aplicar a conjunção `n.enabled && n.execucao`
//     desligaria execução e proteção para todo usuário que registrou push e
//     nunca ligou o interruptor local — gente que RECEBE esses avisos hoje.
//
//  2. NINGUÉM PERDE O `gatilho`. O web não escreve essa chave. Não é uma janela
//     estreita: é estrutural — não há ordem de eventos nem "primeiro toque no
//     aparelho" que a reabra, e um grep de AUSÊNCIA prova. Se o `gatilho`
//     voltasse ao corpo do web, ele seria derivado do `config.notif` DO
//     SERVIDOR, que para um usuário device-first é o default — e o default não
//     é ausência de chave: `defaults.py` grava `enabled: False` e
//     `gatilho: False` EXPLÍCITOS, e `set_prefs` grava por chave. Sintoma: o
//     iPhone com gatilho ligado, uma visita ao app no navegador, e o aviso
//     some. Em silêncio.
//
// REGRA DE FORMA (custou um guardião vácuo no quick task irmão): asserção que
// precisa ficar VERMELHA quando UM dos dois stores é mutado tem que ser por
// CONTAGEM (`=== 2`), nunca por booleano — na forma booleana, mutar um lado só
// continua verde.
//
// Roda sem build: `node web/tests/test_push_prefs_classes.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const storePy = readFileSync(join(here, "..", "..", "server", "app", "store.py"), "utf8");
const defaultsPy = readFileSync(join(here, "..", "..", "server", "app", "defaults.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const conta = (src, re) => (src.match(re) || []).length;

const CLASSES = ["radar", "execucao", "protecao"];

// ------------------------------------------- INVARIANTE 1: os dois mestres
// CONTAGEM, não booleano: `=== 2` é o que fica vermelho quando alguém muta só
// o deviceStore ou só o serverStore.
for (const k of CLASSES) {
  ok(`\`${k}\` na forma opt-out nos DOIS stores (deviceStore + serverStore)`,
     conta(persistence, new RegExp(`${k}: n\\.${k} !== false`, "g")) === 2);
  ok(`\`${k}\` NÃO é conjunção com o mestre local \`n.enabled\``,
     !new RegExp(`${k}: !!\\(n\\.enabled`).test(persistence));
}

// ------------------------------------------- INVARIANTE 2: o gatilho intocado
ok("a conjunção do `gatilho` existe UMA vez só (deviceStore; o web não a escreve)",
   conta(persistence, /gatilho: !!\(n\.enabled && n\.gatilho\)/g) === 1);

const corpoSyncWeb = (persistence.match(/syncPushPrefs: async \(\) => \{[\s\S]*?\n {4}\},/) || [""])[0];
ok("o corpo do `syncPushPrefs` do serverStore foi localizado", corpoSyncWeb.length > 0);
// Esta AUSÊNCIA é o fechamento da janela de clobber, não uma omissão. Quem
// vier "completar" o corpo tem que ler isto antes.
ok("o corpo do syncPushPrefs do web não menciona `gatilho`", !/gatilho/.test(corpoSyncWeb));
ok("o corpo do syncPushPrefs do web não menciona `modo`", !/modo/.test(corpoSyncWeb));
ok("o corpo do syncPushPrefs do web não menciona `universo`", !/universo/.test(corpoSyncWeb));
ok("o corpo do syncPushPrefs do web manda as TRÊS classes",
   CLASSES.every((k) => new RegExp(`${k}: n\\.${k} !== false`).test(corpoSyncWeb)));

// ----------------------------------- allowlist: é UMA paridade, não duas
// Chave ausente da allowlist é descartada em SILÊNCIO no putConfig — o modo de
// falha que já queimou o `agent.*` e o `initialBudget`. Os dois lados, sempre,
// e na MESMA ordem: as duas listas são a mesma coisa escrita em duas línguas.
ok("as 3 classes na allowlist do deviceStore.putConfig (literal, na ordem)",
   /for \(const k of \["enabled", "stop", "alvo", "agente", "variacao", "gatilho", "radar", "execucao", "protecao"\]\)/.test(persistence));
ok("as 3 classes na allowlist do store.set_config (literal, na mesma ordem)",
   /for k in \("enabled", "stop", "alvo", "agente", "variacao", "gatilho",\s*\n\s*"radar", "execucao", "protecao"\):/.test(storePy));

// ------------------------------------- `notif` sobe device→servidor, sem carona
ok("`notif` entra no payload condicionado a `patch.notif`",
   /if \(patch\.notif && typeof patch\.notif === "object"\) \{[\s\S]*?enviar\.notif = nEnviar;/.test(persistence));
ok("`notif` é montado CHAVE A CHAVE, nunca o objeto inteiro",
   /for \(const k of Object\.keys\(patch\.notif\)\) if \(k in c\.notif\) nEnviar\[k\] = c\.notif\[k\];/.test(persistence)
   && !/enviar\.notif = c\.notif/.test(persistence));

// ------------------------------------- o STORE do web dispara o sync sozinho
ok("serverStore.putConfig agenda o sync quando o patch toca `notif`",
   /putConfig: \(patch\) => \{[\s\S]*?if \(patch && patch\.notif && typeof patch\.notif === "object"\)[\s\S]*?_agendarSyncPrefsWeb\(\)/.test(persistence));
ok("o agendador do web tem debounce próprio (timer de closure + clearTimeout)",
   /let _prefsTimerWeb = null;[\s\S]*?clearTimeout\(_prefsTimerWeb\)/.test(persistence));
// O nome NÃO pode casar com `_agendarSyncPrefs();`: o guardião de paridade
// (`test_didatica_parity.mjs`) conta os disparos do deviceStore, e essa
// contagem não pode ser inflada por código do outro store.
ok("o agendador do web não infla a contagem de disparos do deviceStore",
   conta(persistence, /_agendarSyncPrefs\(\);/g) === 7);

// ------------------------------------------- default do servidor: LIGADAS
ok("as 3 classes nascem LIGADAS no default de config.notif (defaults.py)",
   /"radar": True, "execucao": True, "protecao": True/.test(defaultsPy));

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
