// Fase 34, plano 34-01 (2026-09-20) — guardião do split hub/workspace da
// sub-aba "Setups" da aba Opções.
//
// Este arquivo nasce com só a metade "fundação" da fase (34-01): o
// componente `WorkspaceHeader.jsx` e as 4 chaves de copy novas. O split de
// `OpcoesScreen.jsx` em si (hub × workspace) entra nos planos 34-02/34-03,
// que ACRESCENTAM asserções a ESTE MESMO arquivo — não criam um terceiro
// guardião.
//
// Cada item abaixo nomeia o defeito que ele reprova. Nenhum é decorativo:
//
//  1. **`WorkspaceHeader.jsx` sem export default** — o 34-02 importa o
//     componente por nome; sem export correto, o import quebra em silêncio
//     se o guardião não travar a forma exata.
//  2. **`WorkspaceHeader.jsx` deixando de ser props-only** (hook, `ctx.`/
//     `store.`, import de `App.jsx`) — o orquestrador é o único dono de
//     estado compartilhado (REORG-03/04 da Fase 33); um componente de seção
//     que passa a ler estado por conta própria quebra esse invariante em
//     silêncio.
//  3. **`WorkspaceHeader.jsx` renderizando `.manchete`** — o guardrail CVM
//     (CLAUDE.md princípio 5) exige que só o motor determinístico decida a
//     manchete; a allowlist `RENDERIZADORES_DE_MANCHETE` de
//     `test_opcoes_subabas_ui.mjs` não muda nesta fase, e este componente não
//     entra nela.
//  4. **Botão de voltar perdendo o alvo de toque de 44px ou o rótulo de
//     copy** — regressão silenciosa de acessibilidade/i18n.
//  5. **`WorkspaceHeader.jsx` usando cor de destaque (accent)** — o botão é
//     navegação, não a ação primária da tela (Color do UI-SPEC reserva
//     accent só para a pill ativa).
//  6. **Alguma das 4 chaves novas de copy faltando ou vazia num dos dois
//     modos** — quebraria em produção só no modo que não foi aberto à mão.
//  7. **`SecaoSetups.jsx` perdendo `cp.opcoesSetupsTitulo`/
//     `cp.opcoesCriarTitulo`** — guarda contra o "não renomear" do UI-SPEC;
//     a asserção nasce aqui porque é o 34-03 que mexe no arredor dela.
//
// 2026-09-20, Fase 34 (34-02) — ACRESCENTA 6 asserções sobre o split em si
// (`OpcoesScreen.jsx`), agora que ele existe:
//
//  8. **Um aviso crítico (carregando/erro) ficando PRESO dentro de um ramo
//     de modo** — os dois têm de continuar acima da partição por `ticker`
//     dos ramos 3/4, senão um MCP fora do ar vira invisível num dos dois
//     modos (NAV-06).
//  9. **Ramo 1 ou 2 duplicado** (uma cópia por modo) — dobraria o aviso, ou
//     pior, deixaria uma cópia desatualizada.
//  10. **`seletor` vazando para dentro do workspace** — criaria um SEGUNDO
//      caminho de volta ao hub, competindo com o botão do `WorkspaceHeader`
//      (contradiz NAV-03).
//  11. **`WorkspaceHeader` perdendo o `onVoltar` ligado a `escolherTicker`**
//      — abriria espaço para um segundo caminho de reset, divergente do de
//      D-03.
//  12. **Um segundo caminho de volta ao hub** (histórico, breadcrumb,
//      `setTicker("")` solto fora de `escolherTicker`) — o único botão de
//      volta é a exigência literal de NAV-03.
//  13. **A adjacência de D-04/NAV-04 quebrando** — a frase-ponte (dentro de
//      `SecaoDescobrir`) tem de continuar imediatamente seguida por
//      `SecaoVigias` no ramo do hub, sem gate condicional entre os dois.
//
// Roda sem build: `node web/tests/test_opcoes_hub_workspace_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");

const workspaceHeaderBruto = readFileSync(join(dirOpcoes, "WorkspaceHeader.jsx"), "utf8");
const secaoSetupsBruto = readFileSync(join(dirOpcoes, "SecaoSetups.jsx"), "utf8");
const opcoesScreenBruto = readFileSync(join(dirOpcoes, "OpcoesScreen.jsx"), "utf8");

// Sem comentários: eles citam os mesmos termos ao explicar as decisões (o
// próprio doc-comment de WorkspaceHeader.jsx menciona "hook"/"manchete" ao
// explicar por que não os usa, e o de OpcoesScreen.jsx cita "seletor"/
// "carregando"/"breadcrumb" para EXPLICAR as decisões desta mesma fase), e
// contá-los faria o guardião se auto-invalidar (mesmo padrão de
// test_opcoes_subabas_ui.mjs).
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

const workspaceHeader = semComentario(workspaceHeaderBruto);
const opcoesScreen = semComentario(opcoesScreenBruto);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 0) parse mudo: um arquivo vazio faria toda negativa abaixo passar de
// graça, sem medir nada de verdade -------------------------------------------
ok("WorkspaceHeader.jsx foi lido e tem corpo (>200 caracteres)",
   workspaceHeaderBruto.length > 200);

// ---- 1) export default correto ----------------------------------------------
ok("WorkspaceHeader.jsx exporta `export default function WorkspaceHeader`",
   /export default function WorkspaceHeader/.test(workspaceHeaderBruto));

// ---- 2) props-only: zero hook, zero ctx./store., zero import de App.jsx ----
ok("WorkspaceHeader.jsx não usa useState/useEffect/useMemo/useRef",
   !/\buse(State|Effect|Memo|Ref)\b/.test(workspaceHeader));
ok("WorkspaceHeader.jsx não lê `ctx.` nem `store.`",
   !/\bctx\./.test(workspaceHeader) && !/\bstore\./.test(workspaceHeader));
ok("WorkspaceHeader.jsx não importa App.jsx",
   !/from\s+["'][^"']*App\.jsx["']/.test(workspaceHeaderBruto));

// ---- 3) sem manchete (guardrail CVM) ----------------------------------------
ok("WorkspaceHeader.jsx não renderiza `.manchete`",
   !/\.manchete\b/.test(workspaceHeader));

// ---- 4) botão de voltar: 44px + copy ----------------------------------------
ok("WorkspaceHeader.jsx declara `minHeight: \"44px\"` no botão de voltar",
   /minHeight:\s*"44px"/.test(workspaceHeader));
ok("WorkspaceHeader.jsx usa `cp.opcoesVoltarAoHub`",
   /cp\.opcoesVoltarAoHub/.test(workspaceHeader));

// ---- 5) sem cor de destaque (accent é só da pill ativa) ---------------------
ok("WorkspaceHeader.jsx não usa `T.accent`",
   !/T\.accent/.test(workspaceHeader));

// ---- 6) paridade de locale das 4 chaves novas -------------------------------
const CHAVES_NOVAS = [
  "opcoesVoltarAoHub", "opcoesAbaAnalisar", "opcoesAbaComparar", "opcoesAbaSetupsSalvos",
];
const chavesFaltando = CHAVES_NOVAS.filter(
  (k) => !COPY.estudo[k] || !COPY.operador[k]);
ok("as 4 chaves novas existem em COPY.estudo e COPY.operador, nenhuma vazia"
   + (chavesFaltando.length ? " (faltando/vazia: " + chavesFaltando.join(", ") + ")" : ""),
   chavesFaltando.length === 0);

// ---- 7) SecaoSetups.jsx intocada (regressão do "não renomear" do UI-SPEC) --
ok("SecaoSetups.jsx continua com `cp.opcoesSetupsTitulo`",
   /cp\.opcoesSetupsTitulo/.test(secaoSetupsBruto));
ok("SecaoSetups.jsx continua com `cp.opcoesCriarTitulo`",
   /cp\.opcoesCriarTitulo/.test(secaoSetupsBruto));

// ---- 8/9) split hub/workspace (34-02) ---------------------------------------
// Escopo PRIMEIRO, marcadores DEPOIS: `SubAbaOperar` (a OUTRA sub-aba, fora
// do escopo desta fase) tem o SEU PRÓPRIO `!ticker ? (`/`carregandoGate ? (`
// — procurar os marcadores no ARQUIVO INTEIRO acharia o de `SubAbaOperar`
// por acidente no dia em que o de "Setups" mudasse de forma, e o guardião
// passaria verde sem medir nada (guardião inerte). Por isso a fatia da
// sub-aba "Setups" (de {cabecalho} até {cp.opcoesDisclaimer}) é calculada
// ANTES, e todo marcador abaixo é procurado DENTRO dela.
const iInicioSubabaSetups = opcoesScreen.indexOf("{cabecalho}");
const iFimSubabaSetups = opcoesScreen.indexOf("cp.opcoesDisclaimer");
const subAbaSetupsCascata = (iInicioSubabaSetups >= 0 && iFimSubabaSetups > iInicioSubabaSetups)
  ? opcoesScreen.slice(iInicioSubabaSetups, iFimSubabaSetups) : "";
ok("a fatia da sub-aba Setups (cabecalho até disclaimer) foi localizada",
   subAbaSetupsCascata.length > 0);

// Ordem da cascata: carregando ? e erro ? (ramos 1-2, sempre acima) têm de
// vir ANTES do `!ticker ?` que particiona o CONTEÚDO dos ramos 3/4 — é o
// marcador ESPECÍFICO do particionamento por modo (o outro `ticker ?` da
// mesma fatia, `ticker ? workspaceTopo : hubTopo`, decide qual TOPO
// renderizar, não o conteúdo da cascata em si; por isso a busca é por
// "!ticker ?", não por "ticker ?" — o primeiro `ticker ?` da fatia aparece
// ANTES da cascata, de propósito, e pegaria a asserção na forma ingênua).
const iCarregandoCascata = subAbaSetupsCascata.indexOf("carregando ? (");
const iErroCascata = subAbaSetupsCascata.indexOf("erro ? (");
const iTickerRamos34 = subAbaSetupsCascata.indexOf("!ticker ? (");
ok("os três marcadores da cascata foram localizados dentro da sub-aba Setups",
   iCarregandoCascata >= 0 && iErroCascata >= 0 && iTickerRamos34 >= 0);
ok("carregando ? e erro ? (ramos 1-2) vêm ANTES do !ticker ? que particiona os ramos 3/4 (NAV-06)",
   iCarregandoCascata >= 0 && iErroCascata >= 0 && iTickerRamos34 >= 0
   && iCarregandoCascata < iTickerRamos34 && iErroCascata < iTickerRamos34);
ok("cp.opcoesCarregando aparece exatamente 1x dentro da sub-aba Setups (ramo 1 não duplicado por modo)",
   (subAbaSetupsCascata.match(/cp\.opcoesCarregando\b/g) || []).length === 1);
ok("cp.opcoesNaoConfigurado aparece exatamente 1x dentro da sub-aba Setups (ramo 2 não duplicado por modo)",
   (subAbaSetupsCascata.match(/cp\.opcoesNaoConfigurado\b/g) || []).length === 1);

// ---- 10) seletor só existe no hub, nunca dentro do workspace ---------------
// Fatia do corpo de `workspaceTopo`: de `<WorkspaceHeader` até o primeiro
// `);` seguinte (fecha o `const workspaceTopo = (...)`). O único outro uso
// de "seletor" no arquivo é a prop `seletor={seletor}` de `SubAbaOperar`,
// fora do ramo "setups" inteiro — por isso a checagem é por FATIA, não por
// contagem total no arquivo.
const iWorkspaceHeaderUso = opcoesScreen.indexOf("<WorkspaceHeader");
const iFimWorkspaceTopo = iWorkspaceHeaderUso >= 0
  ? opcoesScreen.indexOf(");", iWorkspaceHeaderUso) : -1;
const corpoWorkspaceTopo = (iWorkspaceHeaderUso >= 0 && iFimWorkspaceTopo > iWorkspaceHeaderUso)
  ? opcoesScreen.slice(iWorkspaceHeaderUso, iFimWorkspaceTopo) : "";
ok("o corpo de workspaceTopo (de <WorkspaceHeader até o fechamento do const) foi localizado",
   corpoWorkspaceTopo.length > 0);
ok("`seletor` NÃO aparece dentro do corpo de workspaceTopo (NAV-03: um único caminho de volta)",
   corpoWorkspaceTopo.length > 0 && !/seletor/.test(corpoWorkspaceTopo));

// ---- 11) <WorkspaceHeader recebe onVoltar={() => escolherTicker(ticker)} --
ok("<WorkspaceHeader recebe onVoltar={() => escolherTicker(ticker)} (D-03: sem segundo caminho de reset)",
   /<WorkspaceHeader[\s\S]{0,200}onVoltar=\{\(\) => escolherTicker\(ticker\)\}/.test(opcoesScreen));

// ---- 12) um único caminho de volta ao hub (NAV-03) -------------------------
// Toda chamada a `setTicker(` no arquivo tem de ser a forma exata do toggle
// de `escolherTicker` — um `setTicker("")` solto em outro lugar seria um
// SEGUNDO caminho de reset/volta, divergente do de D-03.
const chamadasSetTicker = opcoesScreen.match(/setTicker\([^)]*\)/g) || [];
ok("existe pelo menos uma chamada a setTicker (sanidade da asserção seguinte)",
   chamadasSetTicker.length >= 1);
ok("toda chamada a setTicker é o toggle exato de escolherTicker (nenhum setTicker(\"\") solto)",
   chamadasSetTicker.every((c) => c === 'setTicker(t === ticker ? "" : t)'));
ok("nenhum history/pushState/breadcrumb em OpcoesScreen.jsx (NAV-03: sem histórico de navegação)",
   !/\bhistory\b/i.test(opcoesScreen) && !/pushState/.test(opcoesScreen) && !/breadcrumb/i.test(opcoesScreen));

// ---- 13) adjacência D-04/NAV-04 no ramo do hub -----------------------------
const iHubTopoDef = opcoesScreen.indexOf("const hubTopo = (");
const iSecaoDescobrirUsoHub = iHubTopoDef >= 0 ? opcoesScreen.indexOf("{secaoDescobrir}", iHubTopoDef) : -1;
const iSecaoVigiasUsoHub = iHubTopoDef >= 0 ? opcoesScreen.indexOf("<SecaoVigias", iHubTopoDef) : -1;
ok("{secaoDescobrir} e <SecaoVigias foram localizados dentro de hubTopo",
   iSecaoDescobrirUsoHub >= 0 && iSecaoVigiasUsoHub >= 0);
ok("{secaoDescobrir} vem ANTES de <SecaoVigias dentro de hubTopo (D-04)",
   iSecaoDescobrirUsoHub >= 0 && iSecaoVigiasUsoHub >= 0 && iSecaoDescobrirUsoHub < iSecaoVigiasUsoHub);
const trechoEntreDescobrirEVigiasHub = (iSecaoDescobrirUsoHub >= 0 && iSecaoVigiasUsoHub > iSecaoDescobrirUsoHub)
  ? opcoesScreen.slice(iSecaoDescobrirUsoHub, iSecaoVigiasUsoHub) : "";
ok("nenhum gate condicional (?/:) entre {secaoDescobrir} e <SecaoVigias dentro de hubTopo",
   trechoEntreDescobrirEVigiasHub.length > 0
   && !/\?/.test(trechoEntreDescobrirEVigiasHub) && !/&&/.test(trechoEntreDescobrirEVigiasHub));

if (fails > 0) {
  console.log(`\n${fails} falha(s).`);
  process.exit(1);
}
console.log("\ntodos os testes passaram");
