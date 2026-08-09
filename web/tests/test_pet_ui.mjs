// O PET — mascote do assistente (coruja) na UI.
//
// Os contratos que estes guardiões travam, e por quê:
//
//  1. O PET NUNCA ABRE SOZINHO. O único one-shot proativo do app é o do
//     gatilho; um segundo espontâneo viraria ruído e queimaria a confiança.
//  2. EM QUALQUER ABA, EM QUALQUER MODO DE TRABALHO (Fase 1 da auditoria de
//     UX, 2026-08-08: o Boris passou a existir em Modo Operador também — o
//     vocabulário já variava por modo em assistente.py/_pet_resumo_*, só
//     faltava o FAB aparecer lá). O FAB continua sumindo sob overlays.
//  3. A FOLHA ABRE DIRETO NO CHAT — o resumo automático (parágrafo lido
//     antes de qualquer interação) saiu; no lugar, `r.perguntas` (vindo do
//     MESMO /api/pet/resumo, campo novo) vira sugestões clicáveis no estado
//     vazio da conversa (ver test_boris_chat.mjs para o contrato dentro do
//     BorisChat).
//  4. VOZ É CONFORTO, NUNCA DEPENDÊNCIA: fechar a folha CALA a voz (nada de
//     coruja fantasma falando atrás de outra tela) — a leitura em voz alta
//     agora é por RESPOSTA do chat (mecanismo já existente em BorisChat),
//     não mais um botão dedicado sobre o resumo.
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
const vozSrc = readFileSync(join(here, "..", "src", "pet", "vozBoris.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------------------ o FAB
ok("Fase 1: o FAB NÃO exclui mais o Modo Operador — só didática/overlay livre (+ F10-20260809: fabVisivel, o 3º controle da tela do Boris)",
   /didatica && didatica\.ligada && ctx\.overlayLivre && data\.config\.fabVisivel !== false && \(\s*\n\s*<PetFab/.test(app));
ok("fabVisivel é opt-OUT (default visível) — preserva a Fase 1 em vez de revertê-la",
   /ctx\.overlayLivre && data\.config\.fabVisivel !== false/.test(app));
ok("o gate do FAB não checa mais `appMode` nenhum",
   !/appMode !== "operador" && didatica && didatica\.ligada && ctx\.overlayLivre/.test(app));
ok("F4: a condição do FAB NÃO checa mais `tab === \"mercado\"`",
   !/tab === "mercado" && didatica && didatica\.ligada && ctx\.overlayLivre/.test(app));
ok("o pet NUNCA abre sozinho (só o onOpen do FAB liga petOpen)",
   (app.match(/setPetOpen\(true\)/g) || []).length === 1);
ok("a folha do pet entra no portão de overlays (proativa adia sob o pet)",
   /overlayLivre: !tourOpen && !aboutOpen && !welcomeOpen && !welcomeAuthOpen && !conceitoAberto && !petOpen/.test(app));

// ------------------------------------------------------------- o conteúdo
ok("Fase 1: a folha busca o resumo da TELA ATIVA (perguntas + itens), sem mais renderizar `fala` como texto",
   /store\.petResumo\(telaAtual\)/.test(app)
   && !/\(r\.fala \|\| \[\]\)\.map\(/.test(app));
ok("falha de rede degrada com honestidade (os cards continuam valendo)",
   /Não consegui preparar o contexto desta tela agora\. Os cards continuam valendo\./.test(app));
ok("camada desligada tem mensagem própria (não é erro)",
   /r\.ligada === false/.test(app));

// ------------------------------------------------------------------ a voz
// A voz mora em ./pet/vozBoris.js (web usa speechSynthesis; nativo usa o
// plugin de TTS) — App.jsx só importa `falarTexto`/`calarVoz`, não define.
ok("App.jsx NÃO define mais falarTexto/calarVoz — importa de ./pet/vozBoris.js",
   /import \{ falarTexto, calarVoz(, setVozConfig, listarVozes)? \} from ["']\.\/pet\/vozBoris\.js["'];/.test(app)
   && !/^function falarTexto\(/m.test(app) && !/^function calarVoz\(/m.test(app));
ok("vozBoris: web usa pt-BR e escolhe voz do sistema quando houver",
   /u\.lang = "pt-BR";/.test(vozSrc) && /\/\^pt\(-\|_\)BR\/i\.test\(v\.lang/.test(vozSrc));
ok("fechar a folha CALA a voz (scrim e desmontagem)",
   /onClick=\{\(\) => \{ calarVoz\(\); onClose\(\); \}\}/.test(app)
   && /return \(\) => \{ alive = false; calarVoz\(\); \};/.test(app));
ok("Fase 1: a folha não tem mais um botão dedicado de 'ouvir' sobre o resumo (voz agora é por resposta do chat)",
   !/Ouvir esta explicação/.test(app) && !/Voz indisponível neste aparelho/.test(app));
ok("vozBoris: Safari — a utterance fica referenciada (GC não mata a fala no meio)",
   /const _vozViva = \{ u: null \};/.test(vozSrc) && /_vozViva\.u = u;/.test(vozSrc));

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
// Fase 1: o `ouvir`/`falando` dedicado ao resumo saiu de App.jsx junto com o
// parágrafo que ele lia — falarTexto→talk()/stop() agora só existe dentro de
// BorisChat.jsx (por RESPOSTA do chat), já travado em test_boris_chat.mjs.
ok("App.jsx NÃO tem mais o handler `ouvir` do resumo (voz virou responsabilidade só do BorisChat)",
   !/const ouvir = \(\) => \{/.test(app));
// 2026-08-08 (decisão do Alex): o FAB deixou de ser avatar circular recortado
// na cabeça e passou a mostrar o Bóris INTEIRO, SEM BOLHA. O que este guardião
// tranca agora: continua sendo <Boris> (nunca o emoji solto), não voltou a ter
// chrome de bolha (fundo/borda/raio) e a área de toque segue nos 54px que o
// iOS exige — a figura encolhe, o alvo não.
ok("o FAB do pet mostra o Boris INTEIRO e sem bolha, com alvo de toque de 54px",
   /function PetFab\(/.test(app)
   && (() => {
     const m = app.match(/function PetFab\([\s\S]*?\n\}\n/);
     if (!m) return false;
     const fab = m[0];
     const semEmoji = !/<span aria-hidden>🦉<\/span>/.test(fab);
     // ANIMADO de propósito (decisão do Alex): nada de `reduced` aqui — o FAB
     // pisca e respira. O `reduced` fica só no Boris do título.
     const temBoris = /<Boris size=\{40\} \/>/.test(fab) && !/<Boris[^>]*reduced/.test(fab);
     const semBolha = /background: "transparent"/.test(fab) && /border: "none"/.test(fab)
       && !/borderRadius: "50%"/.test(fab) && !/overflow: "hidden"/.test(fab);
     const semRecorte = !/scale\(1\.24\)/.test(fab) && !/translateY\(-14px\)/.test(fab);
     const alvo = /width: "54px", height: "54px"/.test(fab);
     return semEmoji && temBoris && semBolha && semRecorte && alvo;
   })());
// O cabeçalho passou por três formas em 08/08/2026: símbolo estático →
// Bóris inteiro → SEM ÍCONE, com o nome maior no lugar. Quem carrega a marca
// ali é o wordmark. Este guardião tranca a forma final: nenhum <Boris> no
// Topbar (o único da tela principal é o do FAB) e o nome em 27px.
ok("o título do app não tem ícone — a marca é o nome, maior",
   (() => {
     const m = app.match(/function Topbar\([\s\S]*?\n\}\n/);
     if (!m) return false;
     const topbar = m[0];
     return !/<Boris\b/.test(topbar) && !/<LogoMark\b/.test(topbar)
       && /fontSize: "27px"[^}]*\}\}>Boris<span style=\{PLUS_STYLE\}>\+<\/span>/.test(topbar);
   })());

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
   /snapshot=\{telaAtual === "mercado" \? \{ itens: \(r\.itens \|\| \[\]\) \} : \(snapshot \|\| \{\}\)\}/.test(app));
ok("Fase 1: `perguntas` do resumo vira `sugestoes` do chat (chips contextuais no lugar do resumo)",
   /sugestoes=\{r\.perguntas \|\| \[\]\}/.test(app));
ok("a LLM continua opt-in atrás da didática grátis (BorisChat, não chamada direta) — só o chat existe agora, sem AssistenteBox nem toggle de resumo",
   /didatica && didatica\.assistente \? \(/.test(app)
   && /<BorisChat key=\{telaAtual\}/.test(app)
   && !/chatAberto/.test(app));

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
ok("Fase 1: api.petResumo manda `tela` sempre, mas `modo` SÓ quando fornecido (web omite de propósito e deixa o servidor decidir pela config do escopo — mesmo contrato de `timing`)",
   /petResumo: \(modo, tela\) => req\("GET", "\/api\/pet\/resumo\?tela=" \+ encodeURIComponent\(tela \|\| "mercado"\) \+ \(modo \? "&modo=" \+ encodeURIComponent\(modo\) : ""\)/.test(apiSrc));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
