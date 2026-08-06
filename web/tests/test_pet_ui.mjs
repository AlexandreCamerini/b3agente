// O PET — mascote do assistente (coruja) na UI.
//
// Os contratos que estes guardiões travam, e por quê:
//
//  1. O PET NUNCA ABRE SOZINHO. O único one-shot proativo do app é o do
//     gatilho; um segundo espontâneo viraria ruído e queimaria a confiança.
//  2. SÓ NA WATCHLIST DO ESTUDO. Operador não tem pet (mesmo isolamento da
//     via proativa) e o FAB some sob overlays.
//  3. O QUE O PET FALA É O QUE EXIBE — a lista `fala` do backend, sem
//     composição local (lei do vocabulário).
//  4. VOZ É CONFORTO, NUNCA DEPENDÊNCIA: sem speechSynthesis o botão explica
//     e o texto continua; fechar a folha CALA a voz (nada de coruja
//     fantasma falando atrás de outra tela).
//  5. A pergunta LLM do pet vai com `tela: "pet:mercado"` (allowlist no
//     backend) e o snapshot são os itens do resumo — dado, não instrução.
//  6. Paridade: `petResumo` nos DOIS stores.
//
// Roda sem build: `node web/tests/test_pet_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const apiSrc = readFileSync(join(here, "..", "src", "api.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------------------ o FAB
ok("o pet só existe na Watchlist do ESTUDO com a tela livre",
   /tab === "mercado" && appMode !== "operador" && didatica && didatica\.ligada && ctx\.overlayLivre && \(\s*\n\s*<PetFab/.test(app));
ok("o pet NUNCA abre sozinho (só o onOpen do FAB liga petOpen)",
   (app.match(/setPetOpen\(true\)/g) || []).length === 1);
ok("a folha do pet entra no portão de overlays (proativa adia sob o pet)",
   /overlayLivre: !tourOpen && !aboutOpen && !welcomeOpen && !welcomeAuthOpen && !conceitoAberto && !petOpen/.test(app));

// ------------------------------------------------------------- o conteúdo
ok("o resumo vem do backend e o pet exibe a MESMA lista `fala` que leria",
   /store\.petResumo\(\)/.test(app)
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
ok("a coruja anima: piscar periódico e boca ciclando enquanto fala",
   /CORUJA_BOCAS = \["😮", "😯", "🗣️", "😃"\]/.test(app)
   && /piscando \? "🙈" : "🦉"/.test(app)
   && /setInterval\(\(\) => setBoca\(\(b\) => b \+ 1\), 150\)/.test(app));

// ------------------------------------------------------------ LLM do pet
ok("a pergunta do pet vai com tela pet:mercado e snapshot = itens do resumo",
   /<AssistenteBox tela="pet:mercado" dados=\{\{ itens: \(r\.itens \|\| \[\]\) \}\} \/>/.test(app));
ok("a LLM continua opt-in atrás do resumo grátis (AssistenteBox, não chamada direta)",
   /didatica && didatica\.assistente && \(\s*\n\s*<AssistenteBox tela="pet:mercado"/.test(app));

// ------------------------------------------------------------- paridade
ok("petResumo existe nos DOIS stores (deviceStore manda o modo local-first)",
   /petResumo: \(modo\) => api\.petResumo\(modo\)/.test(persistence)
   && /async petResumo\(\) \{ ensure\(\); return api\.petResumo\(doc\.config\.appMode \|\| "estudo"\); \}/.test(persistence));
ok("api.petResumo chama GET /api/pet/resumo com o modo",
   /petResumo: \(modo\) => req\("GET", "\/api\/pet\/resumo\?modo="/.test(apiSrc));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
