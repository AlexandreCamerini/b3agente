// F6 — apresentação do Boris (`BorisIntro`), mostrada UMA ÚNICA VEZ, na
// primeira vez que a pessoa chega na aba inicial (Mercado/Watchlist) depois
// do gate de login/onboarding (`WelcomeAuthScreen`/`OnboardingModal`, que
// continuam INTOCADOS — a intro é uma tela DIFERENTE, mostrada DEPOIS deles).
//
// Os contratos que este guardião trava, e por quê:
//
//  1. ORDEM DO CONTEÚDO é regra (decisão D8 do plano): "o que o Boris não
//     faz" vem antes de "o que ele sabe", que vem antes de "como chamá-lo".
//  2. `borisIntroVisto` entra nos MESMOS 3 lugares que `onboarded` (o campo
//     de "já visto" mais próximo por forma: default + allowlist do servidor
//     + allowlist do aparelho) — server/app/defaults.py, server/app/store.py
//     e web/src/persistence.js.
//  3. A intro só é montada sob o MESMO portão de overlay que outras folhas
//     (tour, welcome, conceito, pet) respeitam — não abre em cima de nenhuma.
//  4. "Conversar agora" liga o MESMO estado que o `PetFab` liga (nenhum chat
//     duplicado); "Depois" só fecha (grava visto, não abre nada).
//  5. A intro NUNCA reaparece sozinha depois de `borisIntroVisto=true` — só
//     uma chamada literal liga `borisIntroOpen`, guardada por ref + flag.
//
// Roda sem build: `node web/tests/test_boris_intro.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const introSrc = readFileSync(join(here, "..", "src", "pet", "BorisIntro.jsx"), "utf8");
const defaultsPy = readFileSync(join(here, "..", "..", "server", "app", "defaults.py"), "utf8");
const storePy = readFileSync(join(here, "..", "..", "server", "app", "store.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------------- a montagem
ok("App.jsx importa BorisIntro de ./pet/BorisIntro.jsx",
   /import BorisIntro from ["']\.\/pet\/BorisIntro\.jsx["'];/.test(app));
ok("BorisIntro.jsx importa Boris (mesmo componente animado da F1)",
   /import Boris from ["']\.\/Boris\.jsx["'];/.test(introSrc));
ok("BorisIntro é renderizado sob `borisIntroOpen`",
   /\{borisIntroOpen && \(\s*\n\s*<BorisIntro/.test(app));

// --------------------------------------------------------- 1) a ordem — D8
// Só o CORPO do componente (depois de "export default function") conta —
// o docstring do topo cita as três ideias fora de ordem, como prosa.
const introBody = introSrc.slice(introSrc.indexOf("export default function"));
{
  const naoFaz = introBody.indexOf("não recomenda");
  const oQueSabe = introBody.indexOf("indicadores, estrutura de preço, modelos, setups");
  const comoChamar = introBody.indexOf("coruja flutuante");
  ok("BorisIntro.jsx tem os três blocos de conteúdo",
     naoFaz >= 0 && oQueSabe >= 0 && comoChamar >= 0);
  ok("ORDEM: 'o que não faz' vem ANTES de 'o que ele sabe'", naoFaz < oQueSabe);
  ok("ORDEM: 'o que ele sabe' vem ANTES de 'como chamá-lo'", oQueSabe < comoChamar);
}
ok("'o que não faz' cita carteira simulada e nenhuma ordem à corretora",
   /não envia ordem<\/b> para\s*\n\s*corretora nenhuma/.test(introSrc)
   && /a carteira é <b>simulada<\/b>/.test(introSrc));
ok("nenhuma promessa de resultado (mesmo registro de skill_ref.DISCLAIMER)",
   /recomendação de investimento nem promessa de resultado/.test(introSrc));

// ---------------------------------------------------- 2) os botões e o gate
ok("BorisIntro recebe onConversar/onDepois (sem estado de chat próprio)",
   /export default function BorisIntro\(\{ onConversar, onDepois \}\)/.test(introSrc));
ok("'Conversar agora' existe e chama onConversar",
   /onClick=\{onConversar\}[\s\S]{0,220}Conversar agora/.test(introSrc));
ok("'Depois' existe e chama onDepois",
   /onClick=\{onDepois\}[\s\S]{0,220}Depois/.test(introSrc));
ok("'Conversar agora' liga a MESMA função que o PetFab (abrirPet) — não duplica o chat",
   /<PetFab onOpen=\{abrirPet\} \/>/.test(app)
   && /onConversar=\{\(\) => \{ ctx\.marcarBorisIntroVisto\(\); abrirPet\(\); \}\}/.test(app));
ok("'Depois' só fecha e grava visto — nenhuma chamada de abertura no handler",
   /onDepois=\{\(\) => ctx\.marcarBorisIntroVisto\(\)\}/.test(app));
ok("abrirPet é a fonte ÚNICA que liga petOpen (invariante do FAB, F4, preservado)",
   (app.match(/setPetOpen\(true\)/g) || []).length === 1
   && /const abrirPet = \(\) => setPetOpen\(true\);/.test(app));
ok("marcarBorisIntroVisto fecha a intro E grava borisIntroVisto:true (device+server)",
   /marcarBorisIntroVisto: async \(\) => \{\s*\n\s*setBorisIntroOpen\(false\);/.test(app)
   && /config: \{ \.\.\.d\.config, borisIntroVisto: true \}/.test(app)
   && /store\.putConfig\(\{ borisIntroVisto: true \}\)/.test(app));

// --------------------------------------------------- 3) o portão de overlay
ok("overlayLivre passa a incluir !borisIntroOpen (mesmo portão das outras folhas)",
   /overlayLivre: !tourOpen && !aboutOpen && !welcomeOpen && !welcomeAuthOpen && !conceitoAberto && !petOpen && !borisIntroOpen,/.test(app));
ok("o efeito que decide mostrar a intro espera o MESMO conjunto de overlays fechar",
   /if \(tourOpen \|\| aboutOpen \|\| welcomeOpen \|\| welcomeAuthOpen \|\| conceitoAberto \|\| petOpen\) return;/.test(app));
ok("só monta na aba inicial (Mercado/Watchlist)",
   /if \(tab !== "mercado"\) return;/.test(app));
ok("só monta com a camada de entendimento ligada (didatica.ligada)",
   /if \(!\(didatica && didatica\.ligada\)\) return;/.test(app));

// ------------------------------------------- 4) nunca reaparece sozinha
ok("guardada por ref (decide 1x por boot, nunca reavalia)",
   /const borisIntroShownRef = useRef\(false\)/.test(app)
   && /if \(borisIntroShownRef\.current \|\| !data \|\| !data\.config\) return;/.test(app)
   && /borisIntroShownRef\.current = true;/.test(app));
ok("só abre se borisIntroVisto ainda for falso/ausente",
   /if \(!data\.config\.borisIntroVisto\) setBorisIntroOpen\(true\);/.test(app));
ok("nenhuma outra chamada liga borisIntroOpen além do efeito 1x (nunca abre 'sozinha' 2x)",
   (app.match(/setBorisIntroOpen\(true\)/g) || []).length === 1);

// ------------------------------------ 5) borisIntroVisto nos 3 lugares
ok("1/3 — server/app/defaults.py declara o default (mesmo padrão de onboarded)",
   /"borisIntroVisto": False,/.test(defaultsPy));
ok("2/3 — server/app/store.py aceita o campo em set_config (mesmo padrão de tourSeen)",
   /if "borisIntroVisto" in patch:/.test(storePy)
   && /cfg\["borisIntroVisto"\] = bool\(patch\["borisIntroVisto"\]\)/.test(storePy));
ok("3/3 — web/src/persistence.js (deviceStore.putConfig) aceita o campo (mesmo padrão de tourSeen)",
   /if \("borisIntroVisto" in patch\) c\.borisIntroVisto = !!patch\.borisIntroVisto;/.test(persistence));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
