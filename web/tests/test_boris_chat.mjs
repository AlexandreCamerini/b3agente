// F5 — chat multi-turno do Boris (histórico de verdade, não pergunta isolada).
//
// Os contratos que estes guardiões travam, e por quê:
//
//  1. `useBorisBrain.js` e `BorisChat.jsx` EXISTEM e são importados em
//     `App.jsx`, dentro de `PetSheet` — é ali que a conversa fica acessível.
//  2. `useBorisBrain` fala com `store.assistente` de VERDADE (não o
//     `{message,history,client}` do anexo original) e manda `historico`
//     junto — o corpo bate com `/api/assistente` real.
//  3. O HISTÓRICO tem teto (6 turnos) — mesmo N do backend
//     (`assistente.MAX_HISTORICO_TURNOS`), pra não divergir em silêncio.
//  4. A VOZ é dirigida pelo MESMO mecanismo do resumo: `falarTexto`/
//     `calarVoz` chegam por prop (não um segundo caminho de voz); o Boris
//     entra em "thinking" enquanto espera e volta a falar (`talk()/stop()`)
//     quando a resposta chega.
//  5. STT é MELHORIA PROGRESSIVA: só aparece se `SpeechRecognition` (ou o
//     prefixo `webkit`) existir — a ausência não quebra nada.
//  6. `AssistenteBox` (pergunta única, sem histórico) continua existindo e
//     sendo usada por `ConceitoSheet` sem mudança nenhuma.
//
// Roda sem build: `node web/tests/test_boris_chat.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const brainSrc = readFileSync(join(here, "..", "src", "pet", "useBorisBrain.js"), "utf8");
const chatSrc = readFileSync(join(here, "..", "src", "pet", "BorisChat.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// -------------------------------------------------------------- existência
ok("App.jsx importa BorisChat de ./pet/BorisChat.jsx",
   /import BorisChat from ["']\.\/pet\/BorisChat\.jsx["'];/.test(app));
ok("BorisChat.jsx importa useBorisBrain de ./useBorisBrain.js",
   /import \{ useBorisBrain \} from ["']\.\/useBorisBrain\.js["'];/.test(chatSrc));
ok("BorisChat é renderizado dentro de PetSheet, atrás do mesmo opt-in de didatica.assistente",
   /<BorisChat key=\{telaAtual\}/.test(app));

// ------------------------------------------------------- contrato real da API
ok("useBorisBrain fala com store.assistente (não um endpoint próprio inventado)",
   /store\.assistente\(\{ tela, snapshot: snapshot \|\| \{\}, pergunta, historico \}\)/.test(brainSrc));
ok("useBorisBrain importa `store` de ../persistence.js (o store de verdade, não um mock)",
   /import \{ store \} from ["']\.\.\/persistence\.js["'];/.test(brainSrc));
ok("useBorisBrain NÃO usa o protocolo do anexo ({message,history,client} -> {reply,react})",
   !/res\.reply/.test(brainSrc) && !/, client\b/.test(brainSrc) && !/message:/.test(brainSrc));

// ------------------------------------------------------------- teto de N=6
ok("useBorisBrain tem teto de turnos e manda só os últimos ao backend",
   /MAX_HISTORICO = 6/.test(brainSrc)
   && /mensagensRef\.current\s*\n?\s*\.slice\(-MAX_HISTORICO\)/.test(brainSrc));

// ----------------------------------------------------------------- a voz
ok("BorisChat recebe falarTexto/calarVoz por PROP (mesmo mecanismo do PetSheet, não um segundo caminho)",
   /function BorisChat\(\{ tela, snapshot, borisRef, falarTexto, calarVoz, onFechar \}\)/.test(chatSrc));
ok("BorisChat NÃO chama Boris.speak() diretamente (só talk()\\/stop() via falarTexto)",
   !/borisRef\.current\.speak\(/.test(chatSrc) && !/borisRef\.current\?\.speak\(/.test(chatSrc));
ok("Boris entra em 'thinking' antes de perguntar e falarTexto dirige talk()/stop() na resposta",
   /borisRef && borisRef\.current && borisRef\.current\.setState\("thinking"\)/.test(chatSrc)
   && /onStart: \(\) => borisRef && borisRef\.current && borisRef\.current\.talk\(\)/.test(chatSrc)
   && /onEnd: \(\) => borisRef && borisRef\.current && borisRef\.current\.stop\(\)/.test(chatSrc));
ok("fechar/desmontar o chat CALA a voz (mesma disciplina do resumo)",
   /useEffect\(\(\) => \(\) => \{ calarVoz && calarVoz\(\); \}, \[calarVoz\]\);/.test(chatSrc));
ok("App.jsx passa falarTexto/calarVoz (as MESMAS funções do módulo, não reescritas) pro BorisChat",
   /falarTexto=\{falarTexto\} calarVoz=\{calarVoz\}/.test(app));

// ---------------------------------------------------------------- STT opcional
ok("o mic só existe se SpeechRecognition (ou webkitSpeechRecognition) existir — ausência não quebra",
   /window\.SpeechRecognition \|\| window\.webkitSpeechRecognition/.test(chatSrc)
   && /stt\.suportado &&/.test(chatSrc));
ok("sem STT, nenhum código tenta usar a API (guarda antes de instanciar)",
   /if \(!SR \|\| ouvindo\) return;/.test(chatSrc));

// --------------------------------------------------- AssistenteBox intocada
ok("AssistenteBox (pergunta única, sem histórico) continua existindo tal qual, sem `historico` nenhum",
   /function AssistenteBox\(\{ cid, dados, setor, tela \}\)/.test(app)
   && !/AssistenteBox[\s\S]{0,400}historico/.test(app.slice(app.indexOf("function AssistenteBox"), app.indexOf("function AssistenteBox") + 2200)));
ok("ConceitoSheet continua chamando AssistenteBox sem tela (pergunta isolada por conceito)",
   /\{didatica && didatica\.assistente && <AssistenteBox cid=\{cid\} dados=\{dados\} setor=\{setor\} \/>\}/.test(app));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
