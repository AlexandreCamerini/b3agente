// Fase 39 (39-02, NAV-01) — guardião dos primitivos compartilhados da
// reestruturação de navegação da aba Opções: `CarimboFrescor`/`DetalheInfo`/
// `BotaoSaibaMais` (uiOpcoes.jsx) e `VigiasBadge`/`VigiasSheet`
// (VigiasSheet.jsx), mais o canal one-shot `ctx.goOpcoes(aba)` de App.jsx
// (Task 3 deste plano).
//
// Este é um plano "interface-first" (39-02-PLAN.md): os Planos 03/04
// constroem CONTRA estes contratos, sem ninguém precisar caçar nada no
// código. O que este arquivo tranca, e por que cada regra existe:
//
//  1. os 5 exports existem, nos módulos certos;
//  2. VigiasSheet.jsx não importa App.jsx nem chama store./fetch( — isolamento
//     ADR-027 (Emenda 3) — módulo terceiro de web/src/opcoes/;
//  3. o shell do sheet reusa a MESMA geometria de ConceitoSheet
//     (entendimento.jsx): zIndex 86, 82vh, safe-area-inset-bottom — nenhum
//     valor novo inventado;
//  4. role="dialog"/aria-modal presentes (acessibilidade de overlay modal);
//  5. o número do VigiasBadge só aparece com `medido && n > 0` (princípio 4
//     do CLAUDE.md: nunca "0" antes de medir);
//  6. T.accent (a única cor "acionável" do badge) aparece SÓ no número, nunca
//     no botão inteiro em repouso;
//  7. nenhum T.<token> usado em VigiasSheet.jsx/uiOpcoes.jsx fica de fora do
//     próprio array TOKENS do arquivo (token fora do array vira `undefined`
//     calado — defeito real já pego na Fase 35, SecaoVigias.jsx);
//  8. DetalheInfo/BotaoSaibaMais têm aria-expanded/aria-label e minHeight
//     "44px" (alvo de toque mínimo, não-negociável no app inteiro);
//  9. BotaoSaibaMais devolve null sem onClick (nunca um botão morto na tela);
//  10. as chaves novas da Task 1 (copy.js) existem nos dois modos;
//  11. ctx (App.jsx) expõe `opcoesAbaInicial`/`limparOpcoesAbaInicial`
//      (Task 3 — canal one-shot da linha de chamada de Posições).
//
// Roda sem build e sem servidor: `node web/tests/test_opcoes_nav_primitivos_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirSrc = join(here, "..", "src");
const dirOpcoes = join(dirSrc, "opcoes");

const uiOpcoes = readFileSync(join(dirOpcoes, "uiOpcoes.jsx"), "utf8");
const vigiasSheet = readFileSync(join(dirOpcoes, "VigiasSheet.jsx"), "utf8");
const app = readFileSync(join(dirSrc, "App.jsx"), "utf8");

// Remove comentários de bloco e de linha antes de varrer — mesmo padrão de
// test_opcoes_vigias_ui.mjs/test_opcoes_consolidacao_ui.mjs.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const uiOpcoesSC = semComentario(uiOpcoes);
const vigiasSheetSC = semComentario(vigiasSheet);
const appSC = semComentario(app);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- (1) os 5 exports existem, nos módulos certos --------------------------
ok("uiOpcoes.jsx exporta CarimboFrescor/DetalheInfo/BotaoSaibaMais (3x)",
  (uiOpcoesSC.match(/export function CarimboFrescor\(|export function DetalheInfo\(|export function BotaoSaibaMais\(/g) || []).length === 3);
ok("VigiasSheet.jsx exporta VigiasBadge/VigiasSheet (2x)",
  (vigiasSheetSC.match(/export function VigiasBadge\(|export function VigiasSheet\(/g) || []).length === 2);

// ---- (2) isolamento ADR-027: sem import de App.jsx, sem store./fetch( -----
ok("VigiasSheet.jsx não importa App.jsx (fora de comentário)",
  !vigiasSheetSC.includes("App.jsx"));
ok("VigiasSheet.jsx não chama store.<metodo>( (sem rede/estado global)",
  !/\bstore\.\w+\(/.test(vigiasSheetSC));
ok("VigiasSheet.jsx não chama fetch(",
  !vigiasSheetSC.includes("fetch("));

// ---- (3) mesma geometria de ConceitoSheet (entendimento.jsx) ---------------
ok("VigiasSheet.jsx usa zIndex: 86 (mesmo valor de ConceitoSheet, nenhum z-index novo)",
  vigiasSheetSC.includes("zIndex: 86"));
ok("VigiasSheet.jsx usa maxHeight: \"82vh\"",
  vigiasSheetSC.includes("82vh"));
ok("VigiasSheet.jsx usa env(safe-area-inset-bottom)",
  vigiasSheetSC.includes("safe-area-inset-bottom"));

// ---- (4) acessibilidade de overlay modal -----------------------------------
ok('VigiasSheet.jsx usa role="dialog"',
  vigiasSheetSC.includes('role="dialog"'));
ok('VigiasSheet.jsx usa aria-modal="true"',
  vigiasSheetSC.includes('aria-modal="true"'));

// ---- (5) número do badge só com medido && n > 0 ----------------------------
ok("VigiasBadge só renderiza o número sob `medido && n > 0`",
  /\{medido\s*&&\s*n\s*>\s*0\s*&&/.test(vigiasSheetSC));

// ---- (6) T.accent só no número do badge, nunca no botão em repouso --------
const iDefVigiasBadge = vigiasSheetSC.indexOf("export function VigiasBadge");
const iDefVigiasSheet = vigiasSheetSC.indexOf("export function VigiasSheet");
const corpoVigiasBadge = (iDefVigiasBadge > -1 && iDefVigiasSheet > iDefVigiasBadge)
  ? vigiasSheetSC.slice(iDefVigiasBadge, iDefVigiasSheet) : "";
ok("o corpo de VigiasBadge foi localizado", corpoVigiasBadge.length > 0);
const iBotaoAbre = corpoVigiasBadge.indexOf("<button");
const iSpanNumero = corpoVigiasBadge.indexOf("<span");
const estiloDoBotao = (iBotaoAbre > -1 && iSpanNumero > iBotaoAbre) ? corpoVigiasBadge.slice(iBotaoAbre, iSpanNumero) : "";
ok("o estilo do <button> do VigiasBadge (antes do <span> do número) NÃO usa T.accent",
  estiloDoBotao.length > 0 && !estiloDoBotao.includes("T.accent"));
ok("T.accent aparece no VigiasBadge (só no número, dentro do <span>)",
  corpoVigiasBadge.includes("T.accent"));

// ---- (7) todo T.<token> usado está declarado no próprio array TOKENS ------
function tokensForaDoArray(fonteSemComentario) {
  const mArray = fonteSemComentario.match(/const TOKENS = \[([^\]]*)\]/);
  const declarados = mArray ? Array.from(mArray[1].matchAll(/"(\w+)"/g)).map((m) => m[1]) : [];
  const usados = Array.from(fonteSemComentario.matchAll(/\bT\.(\w+)/g)).map((m) => m[1]);
  return usados.filter((t) => !declarados.includes(t));
}
const foraUi = tokensForaDoArray(uiOpcoesSC);
const foraVigias = tokensForaDoArray(vigiasSheetSC);
ok("todo T.<token> usado em uiOpcoes.jsx está no array TOKENS do arquivo"
  + (foraUi.length ? " (fora do array: " + foraUi.join(", ") + ")" : ""),
  foraUi.length === 0);
ok("todo T.<token> usado em VigiasSheet.jsx está no array TOKENS do arquivo"
  + (foraVigias.length ? " (fora do array: " + foraVigias.join(", ") + ")" : ""),
  foraVigias.length === 0);

// ---- (8) DetalheInfo/BotaoSaibaMais: aria-*/minHeight 44px ------------------
const iDefDetalheInfo = uiOpcoesSC.indexOf("export function DetalheInfo");
const iDefBotaoSaibaMais = uiOpcoesSC.indexOf("export function BotaoSaibaMais");
const corpoDetalheInfo = (iDefDetalheInfo > -1 && iDefBotaoSaibaMais > iDefDetalheInfo)
  ? uiOpcoesSC.slice(iDefDetalheInfo, iDefBotaoSaibaMais) : "";
ok("o corpo de DetalheInfo foi localizado", corpoDetalheInfo.length > 0);
ok("DetalheInfo tem aria-expanded", corpoDetalheInfo.includes("aria-expanded"));
ok("DetalheInfo tem minHeight: \"44px\"", corpoDetalheInfo.includes('minHeight: "44px"'));
const corpoBotaoSaibaMais = iDefBotaoSaibaMais > -1 ? uiOpcoesSC.slice(iDefBotaoSaibaMais) : "";
ok("BotaoSaibaMais tem aria-label", corpoBotaoSaibaMais.includes("aria-label"));
ok("BotaoSaibaMais tem minHeight: \"44px\"", corpoBotaoSaibaMais.includes('minHeight: "44px"'));

// ---- (9) BotaoSaibaMais devolve null sem onClick ---------------------------
ok("BotaoSaibaMais devolve null quando !onClick",
  /if\s*\(!onClick\)\s*return null;/.test(corpoBotaoSaibaMais));

// ---- (10) as chaves novas da Task 1 (copy.js) existem nos dois modos ------
const CHAVES_NAVEGACAO = [
  "opcoesAbaOportunidades", "opcoesAbaRecomendadas", "opcoesAbaMontar",
  "opcoesVerOutrosVencimentos", "opcoesOcultarOutrosVencimentos",
  "opcoesVigiasSheetTitulo", "opcoesVigiasFechar", "opcoesVigiasAbrirSheet",
  "opcoesSaibaMaisAria",
];
const CHAVES_COM_VOZ = [
  "opcoesMontarTitulo", "opcoesMontarNoAtivo",
  "opcoesCustoFrescorRotulo", "opcoesLastroAjudaRotulo",
];
const CHAVES_RECOMENDADAS = [
  "curadoriaPosicaoRotulo", "curadoriaVazioPiso", "curadoriaVazioSemProb",
  "curadoriaProbOtmRotulo", "curadoriaPremioAnualizadoRotulo",
  "curadoriaVolImplicita", "curadoriaVolHistorica",
];
const TODAS_AS_CHAVES = [...CHAVES_NAVEGACAO, ...CHAVES_COM_VOZ, ...CHAVES_RECOMENDADAS];
ok("as " + TODAS_AS_CHAVES.length + " chaves novas da Task 1 existem em COPY.estudo",
  TODAS_AS_CHAVES.every((k) => k in COPY.estudo));
ok("as " + TODAS_AS_CHAVES.length + " chaves novas da Task 1 existem em COPY.operador",
  TODAS_AS_CHAVES.every((k) => k in COPY.operador));

// ---- (11) ctx (App.jsx) expõe opcoesAbaInicial/limparOpcoesAbaInicial ------
// (Task 3 deste plano — canal one-shot da linha de chamada de Posições).
ok("App.jsx declara o estado opcoesAbaInicial (useState)",
  /const \[opcoesAbaInicial, setOpcoesAbaInicial\] = useState\(null\);/.test(appSC));
ok("ctx expõe opcoesAbaInicial",
  /\bopcoesAbaInicial,/.test(appSC));
ok("ctx expõe limparOpcoesAbaInicial",
  /limparOpcoesAbaInicial:\s*\(\)\s*=>\s*setOpcoesAbaInicial\(null\)/.test(appSC));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
