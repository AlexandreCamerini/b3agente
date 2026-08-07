// O PET — mascote do assistente (coruja) na UI.
//
// Os contratos que estes guardiões travam, e por quê:
//
//  1. O PET NUNCA ABRE SOZINHO. O único one-shot proativo do app é o do
//     gatilho; um segundo espontâneo viraria ruído e queimaria a confiança.
//  2. EM QUALQUER ABA DO ESTUDO (F4). Operador não tem pet (mesmo isolamento
//     da via proativa) e o FAB some sob overlays — só a restrição de aba
//     saiu; as outras duas condições continuam de pé.
//  3. O QUE O PET FALA É O QUE EXIBE — a lista `fala` do backend, sem
//     composição local (lei do vocabulário).
//  4. VOZ É CONFORTO, NUNCA DEPENDÊNCIA: sem speechSynthesis o botão explica
//     e o texto continua; fechar a folha CALA a voz (nada de coruja
//     fantasma falando atrás de outra tela).
//  5. A pergunta LLM do pet vai com `tela: "pet:<aba ativa>"` (allowlist no
//     backend) e o snapshot é o view-model que a tela já usa — dado, não
//     instrução. F4: as 7 abas do plano têm snapshot próprio.
//  6. Paridade: `petResumo` nos DOIS stores (agora recebendo `tela`).
//
// Roda sem build: `node web/tests/test_pet_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const apiSrc = readFileSync(join(here, "..", "src", "api.js"), "utf8");
const borisSrc = readFileSync(join(here, "..", "src", "pet", "Boris.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------------------ o FAB
ok("F4: o pet não depende mais da aba — só appMode/didática/overlay livre",
   /appMode !== "operador" && didatica && didatica\.ligada && ctx\.overlayLivre && \(\s*\n\s*<PetFab/.test(app));
ok("F4: a condição do FAB NÃO checa mais `tab === \"mercado\"`",
   !/tab === "mercado" && appMode !== "operador" && didatica && didatica\.ligada/.test(app));
ok("o pet NUNCA abre sozinho (só o onOpen do FAB liga petOpen)",
   (app.match(/setPetOpen\(true\)/g) || []).length === 1);
ok("a folha do pet entra no portão de overlays (proativa adia sob o pet)",
   /overlayLivre: !tourOpen && !aboutOpen && !welcomeOpen && !welcomeAuthOpen && !conceitoAberto && !petOpen/.test(app));

// ------------------------------------------------------------- o conteúdo
ok("o resumo vem do backend PARA A TELA ATIVA e o pet exibe a MESMA lista `fala` que leria",
   /store\.petResumo\(telaAtual\)/.test(app)
   && /\(r\.fala \|\| \[\]\)\.map\(/.test(app)
   && /falarTexto\(\(\(r && r\.fala\) \|\| \[\]\)\.join\(" "\)/.test(app));
ok("falha de rede degrada com honestidade (os cards continuam valendo)",
   /Não consegui montar o resumo agora\. Os cards continuam valendo\./.test(app));
ok("camada desligada tem mensagem própria (não é erro)",
   /r\.ligada === false/.test(app));

// ------------------------------------------------------------------ a voz
ok("a voz usa pt-BR e escolhe voz do sistema quando houver",
   /u\.lang = "pt-BR";/.test(app) && /\/\^pt\(-\|_\)BR\/i\.test\(v\.lang/.test(app));
ok("fechar a folha CALA a voz (scrim e desmontagem)",
   /onClick=\{\(\) => \{ calarVoz\(\); onClose\(\); \}\}/.test(app)
   && /return \(\) => \{ alive = false; calarVoz\(\); \};/.test(app));
ok("sem speechSynthesis o botão vira aviso e o TEXTO segue inteiro",
   /Voz indisponível neste aparelho — o texto acima continua valendo/.test(app));
ok("Safari: a utterance fica referenciada (GC não mata a fala no meio)",
   /const _vozViva = \{ u: null \};/.test(app) && /_vozViva\.u = u;/.test(app));

// --------------------------------------------------------------- o mascote
// F1: a coruja emoji (Coruja) saiu; Boris.jsx (CSS puro, animado) entrou no
// lugar. falarTexto/calarVoz continuam donas da voz — só passam a dirigir a
// boca do Boris pelos callbacks onStart/onEnd que já existiam.
ok("App.jsx importa Boris de ./pet/Boris.jsx",
   /import Boris from ["']\.\/pet\/Boris\.jsx["'];/.test(app));
ok("a folha do pet usa <Boris> por ref (não mais o emoji)",
   /<Boris ref=\{borisRef\} size=\{72\} \/>/.test(app));
ok("a coruja emoji (Coruja) NÃO existe mais como componente em App.jsx",
   !/function Coruja\(/.test(app) && !/CORUJA_BOCAS/.test(app));
ok("falarTexto dirige a boca do Boris: talk() ao começar, stop() ao terminar",
   /onStart: \(\) => \{ setFalando\(true\); borisRef\.current\?\.talk\(\); \}/.test(app)
   && /onEnd: \(\) => \{ setFalando\(false\); borisRef\.current\?\.stop\(\); \}/.test(app));

// ---------------------------------------------------------- Boris.jsx (F1)
ok("Boris.jsx importa o PNG como asset do Vite (nada de data-URI embutido)",
   /import owlSrc from ["']\.\.\/assets\/boris\.png["'];/.test(borisSrc)
   && /--owl['"], `url\("\$\{owlSrc\}"\)`/.test(borisSrc));
ok("Boris.jsx expõe a API por ref: speak/talk/stop/setMouth/setState/react/setVoice/setReduced",
   /useImperativeHandle\(ref, \(\)=>\(\{ speak, talk, stop, setMouth, setState, react, setVoice, setReduced,/.test(borisSrc));
ok("Boris.jsx preserva prefers-reduced-motion (CSS original)",
   /@media \(prefers-reduced-motion: reduce\)\{\.boris-stage \.owl-body,\.boris-stage \.breath\{animation:none!important\}\}/.test(borisSrc));
ok("Boris.jsx injeta o CSS uma vez só (idempotente)",
   /function injectCSS\(\)\{/.test(borisSrc)
   && /document\.getElementById\('boris-css'\)\) return;/.test(borisSrc));
ok("nenhum arquivo do pet (App.jsx, Boris.jsx) tem string literal data:image (o PNG virou asset)",
   !/data:image/.test(app) && !/data:image/.test(borisSrc));

// ------------------------------------------------------------ LLM do pet
ok("F4: a pergunta do pet interpola a TELA ATIVA (pet:<aba>), não mais fixa em pet:mercado",
   /tela=\{"pet:" \+ telaAtual\}/.test(app));
ok("F4: pet:mercado NÃO mudou de formato — snapshot continua `{ itens: (r.itens || []) }`",
   /dados=\{telaAtual === "mercado" \? \{ itens: \(r\.itens \|\| \[\]\) \} : \(snapshot \|\| \{\}\)\}/.test(app));
ok("a LLM continua opt-in atrás do resumo grátis (AssistenteBox/BorisChat, não chamada direta)",
   // F5: o gate `didatica.assistente` agora escolhe ENTRE o chat completo
   // (histórico) e a pergunta única — as duas formas continuam atrás do
   // mesmo opt-in, nenhuma delas dispara sozinha.
   /didatica && didatica\.assistente && \(\s*\n\s*chatAberto \? \(/.test(app)
   && /<AssistenteBox tela=\{"pet:" \+ telaAtual\}/.test(app));

// ---------------------------------------------------- F4: presença nas 7 abas
// A folha do pet passa a existir em toda aba; cada uma tem um `tela: "pet:<id>"`
// e um snapshot próprio. Não exige string literal por aba (o código usa
// variável — `petTela`/`telaAtual`) — confere que (a) o cálculo da aba ativa
// cobre as 7, e (b) cada uma tem um ramo de snapshot ou é a rota já coberta
// (mercado, tratada dentro do PetSheet a partir do resumo).
const ABAS_PET = ["mercado", "carteira", "evolucao", "radar", "agente", "historico", "perfil"];
ok("PetFab/PetSheet recebem a aba ativa calculada de tab+carteiraView (petTela)",
   /const petTela = tab === "carteira" \? \(carteiraView === "historico" \? "historico" : "carteira"\) : tab;/.test(app));
ok("PetSheet é chamado com a tela ativa e o snapshot por tela",
   /<PetSheet didatica=\{didatica\} tela=\{petTela\} snapshot=\{petSnapshot\}/.test(app));
for (const aba of ABAS_PET) {
  ok(`a aba "${aba}" está coberta pelo cálculo do pet (petTela e/ou petSnapshot)`,
     new RegExp(`["']${aba}["']`).test(app) && (aba === "mercado"
       // "mercado" não precisa de `case` no snapshot — é o default (o
       // snapshot dele vem do resumo, não de `ctx`, dentro do PetSheet).
       || new RegExp(`case "${aba}":`).test(app)));
}

// ------------------------------------------------------------- paridade
ok("petResumo existe nos DOIS stores, agora recebendo `tela`",
   /petResumo: \(tela\) => api\.petResumo\(undefined, tela\)/.test(persistence)
   && /async petResumo\(tela\) \{ ensure\(\); return api\.petResumo\(doc\.config\.appMode \|\| "estudo", tela\); \}/.test(persistence));
ok("api.petResumo chama GET /api/pet/resumo com o modo E a tela",
   /petResumo: \(modo, tela\) => req\("GET", "\/api\/pet\/resumo\?modo="/.test(apiSrc)
   && /&tela=" \+ encodeURIComponent\(tela \|\| "mercado"\)/.test(apiSrc));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
