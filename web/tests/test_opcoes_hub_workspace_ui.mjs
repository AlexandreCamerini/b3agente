// REANCORAGEM — Fase 48 (2026-10-05), caminho B: o "hub" da aba Opções voltou a
// existir, mas é OUTRO hub — `HubOpcoes.jsx` (nível raiz do fluxo em
// profundidade, navOpcoes.js): cards da CARTEIRA + seção Atenção (vigias) +
// frescor + aviso de dinheiro virtual. As 3 abas fixas (`abaBar`) e o badge de
// Vigias do cabeçalho deixaram de existir; Vigias viram a seção Atenção do hub
// + "ver todos" abrindo o sheet existente. Itens 2, 5b, 7 e 8 trocam a âncora
// (sufixo "(reancorado 2026-10-05)"); 1, 3, 4, 5a, 6, 9 e 10 seguem como
// estavam. Invariantes mantidos: custo só em clique (o único disparador pago
// do hub é o "Atualizar" dos vigias, com custo declarado dentro do botão),
// universo = carteira, travessão em vez de zero. Texto original abaixo
// preservado.
//
// Fase 34, plano 34-01 (2026-09-20) — guardião do split hub/workspace da
// sub-aba "Setups" da aba Opções.
//
// Este arquivo nasceu com só a metade "fundação" da fase (34-01): o
// componente `WorkspaceHeader.jsx` e as 4 chaves de copy novas. O split de
// `OpcoesScreen.jsx` em si (hub × workspace) entrou nos planos 34-02/34-03,
// que ACRESCENTARAM asserções a ESTE MESMO arquivo — não um terceiro
// guardião. Histórico completo (itens originais 1-20, Fases 34-01/34-02/
// 34-03) preservado em `git log -p` deste arquivo — não reescrito aqui.
//
// 2026-09-24, Fase 39 (39-04/39-05, NAV-01) — RECONCILIAÇÃO. `WorkspaceHeader.jsx`
// foi DELETADO (zero consumidor restante) e o split hub×workspace inteiro foi
// dissolvido: os dois estados ortogonais `subaba` (Fase 28) e `abaWorkspace`
// (Fase 34) viram UM estado `abaOpcoes` com 3 valores fixos
// (Oportunidades/Recomendadas/Montar, D-01) — sempre os mesmos, com ou sem
// ticker escolhido. Não há mais "hub" nem "workspace": há 3 abas fixas, e a
// antiga sub-aba "Setups" (Fase 28/34) é hoje a aba "Montar".
//
// Reversões desta fase (nota datada, nenhum `ok(` apagado sem substituto —
// T-39-19/T-39-20 do 39-05-PLAN.md):
//
//  · Itens originais 1-5 (existência/forma de `WorkspaceHeader.jsx`: export
//    default, props-only, sem manchete, botão de voltar 44px+copy, sem
//    accent) — SEM SUBSTITUTO 1:1, porque o COMPONENTE em si desapareceu
//    (D-01/D-04: não há mais "voltar ao hub", só trocar de aba pela
//    `abaBar`). O invariante de FUNDO que sobrevive — um seletor de ativo
//    sempre visível, com afordância de alvo tátil — é re-ancorado no item 1
//    novo abaixo, sobre `seletor` (o mesmo widget de troca de ticker que já
//    existia dentro da sub-aba "Setups", agora único caminho de troca/
//    desseleção em Montar, D-04 do UI-SPEC).
//  · Item original 11 (`<WorkspaceHeader recebe onVoltar={() =>
//    escolherTicker(ticker)}`) — SEM SUBSTITUTO 1:1 pelo mesmo motivo; o
//    invariante de fundo ("um único caminho de reset, sem via alternativa")
//    é re-ancorado no item 2 novo abaixo, direto sobre `escolherTicker`.
//  · Item original 13 (adjacência D-04/NAV-04: frase-ponte `duasLeiturasIntro`
//    imediatamente seguida de `<SecaoVigias` dentro de `hubTopo`) — DUAS
//    reversões distintas da lista fechada do `<repo_guardrail>` do
//    39-05-PLAN.md: (a) a frase-ponte sai de uso (Plano 39-02) — a negação de
//    hierarquia entre os dois motores de opções passa a morar em
//    `curadoriaSubtitulo`, checado no item 5a novo; (b) "Seus vigias" deixa
//    de ser bloco fixo do hub e vira badge+sheet (D-07), checado no item 5b
//    novo.
//  · Itens originais 14-20 (pill row do workspace — `workspacePillRow` —
//    e o gate do ramo "4. DADOS" por ela): a pill row de 3 abas
//    (Analisar/Comparar/Setups salvos) é re-ancorada como `abaBar`, a régua
//    de NÍVEL 1 (Oportunidades/Recomendadas/Montar) — item 7 novo. O gate do
//    ramo "4. DADOS" É REVERTIDO de propósito (D-06): Analisar e Setups
//    salvos deixam de estar atrás de pill própria e passam a aparecer
//    SEMPRE que há dados (item 10 novo); só Comparar continua atrás de um
//    gate, agora `compararAberto` em vez de uma pill (item 9 novo).
//  · Item original 16 (`abaWorkspace`/`subaba` não se confundindo) fica sem
//    objeto: os dois estados foram fundidos num só (`abaOpcoes`), então a
//    classe de defeito "dois estados vazando um no outro" deixa de existir
//    por desenho — não há mais dois estados para confundir.
//
// Itens re-ancorados sem mudança de condição (nenhuma reversão, só forma):
//  · Itens originais 6/7 (paridade das 4 chaves de copy / SecaoSetups mantém
//    `cp.opcoesSetupsTitulo`/`cp.opcoesCriarTitulo`) — item 6 novo confirma
//    que as 4 chaves antigas NÃO foram apagadas (retiradas de uso, mas
//    preservadas pelo Copywriting Contract do 39-UI-SPEC.md — comentário
//    datado já presente em `copy.js`); item 3 novo reproduz o item 7
//    original, intocado.
//  · Itens originais 8/9 (avisos críticos carregando/erro não duplicados,
//    acima da partição por ticker) — item 4 novo, mesma fatia técnica
//    ({cabecalho}…cp.opcoesDisclaimer), agora dentro do ramo Montar (não há
//    mais partição por modo dentro dela: D-04 do 39-04-SUMMARY.md diz que a
//    cascata roda só dentro de Montar, nunca duplicada por hub/workspace).
//  · Item original 12 (setTicker(...) só na forma toggle de `escolherTicker`,
//    sem history/pushState/breadcrumb) — incorporado ao item 2 novo.
//  · Item original 15 (nenhum `useEffect` reage ao estado de navegação) —
//    item 8 novo, mesma checagem, dependência renomeada de `abaWorkspace`
//    para `abaOpcoes`.
//
// Roda sem build: `node web/tests/test_opcoes_hub_workspace_ui.mjs`.
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");

const secaoSetupsBruto = readFileSync(join(dirOpcoes, "SecaoSetups.jsx"), "utf8");
const opcoesScreenBruto = readFileSync(join(dirOpcoes, "OpcoesScreen.jsx"), "utf8");

// Sem comentários: o próprio doc-comment de OpcoesScreen.jsx cita
// "abaWorkspace"/"subaba"/"WorkspaceHeader"/"hubTopo" ao EXPLICAR a
// dissolução desta fase — contá-los faria o guardião se auto-invalidar
// (mesmo padrão de test_opcoes_subabas_ui.mjs).
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

const opcoesScreen = semComentario(opcoesScreenBruto);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 0) parse mudo: um arquivo vazio faria toda negativa abaixo passar de
// graça, sem medir nada de verdade -------------------------------------------
ok("OpcoesScreen.jsx foi lido e tem corpo (>200 caracteres)",
   opcoesScreenBruto.length > 200);
ok("WorkspaceHeader.jsx NÃO existe mais em web/src/opcoes/ (D-01/D-04: zero consumidor restante)",
   !existsSync(join(dirOpcoes, "WorkspaceHeader.jsx")));

// ---- 1) [re-ancora itens 1-5/10 originais, reversão b] o seletor de ativo é
// o único widget de troca em Montar, sempre com afordância -------------------
const iSeletorDef = opcoesScreen.indexOf("const seletor = (");
const iFimSeletor = iSeletorDef >= 0 ? opcoesScreen.indexOf(");", iSeletorDef) : -1;
const seletorSlice = (iSeletorDef >= 0 && iFimSeletor > iSeletorDef)
  ? opcoesScreen.slice(iSeletorDef, iFimSeletor) : "";
ok("a fatia de `seletor` (const seletor até o fechamento) foi localizada",
   seletorSlice.length > 0);
ok("`seletor` usa `aria-pressed` (afordância de estado, substitui o botão de voltar do WorkspaceHeader)",
   /aria-pressed=/.test(seletorSlice));
ok("`seletor` declara `minHeight: \"44px\"` (alvo tátil mínimo)",
   /minHeight:\s*"44px"/.test(seletorSlice));
ok("`seletor` é renderizado sem gate de `ticker` — só de `carteira.length > 0` (D-04: sempre visível em Montar)",
   /carteira\.length > 0 \? seletor : null/.test(opcoesScreen));

// ---- 2) [re-ancora itens 11/12 originais, reversão b + a] escolherTicker é
// o ÚNICO caminho de reset/troca — nenhum segundo caminho de navegação -------
const iEscolherTickerDef = opcoesScreen.indexOf("const escolherTicker = (t) => {");
const iFimEscolherTicker = iEscolherTickerDef >= 0 ? opcoesScreen.indexOf("};", iEscolherTickerDef) : -1;
const escolherTickerSlice = (iEscolherTickerDef >= 0 && iFimEscolherTicker > iEscolherTickerDef)
  ? opcoesScreen.slice(iEscolherTickerDef, iFimEscolherTicker) : "";
ok("a fatia de `escolherTicker` foi localizada", escolherTickerSlice.length > 0);
// REANCORAGEM (2026-10-05): o toggle agora age sobre `nav` (setNav) e o reset
// de tese/vencimento/alvo/stop/compararAberto mora num useEffect([nav.ticker]),
// que cobre TAMBÉM a troca de ativo feita pelo hub (não só pelo seletor).
ok("`escolherTicker` faz o toggle de `nav.ticker` (`t === n.ticker ? { ...n, ticker: \"\" } : { ...n, ticker: t, ... }`) (reancorado 2026-10-05)",
   /setNav\(\(n\) => \(t === n\.ticker\s*\? \{ \.\.\.n, ticker: "" \}\s*: \{ \.\.\.n, ticker: t, objetivo: null, vencimento: null, degrauId: null \}\)\)/.test(escolherTickerSlice));
ok("trocar de ativo (qualquer caminho) fecha `compararAberto`: useEffect([nav.ticker]) chama setCompararAberto(false) (D-06) (reancorado 2026-10-05)",
   /useEffect\(\(\) => \{[^}]*setCompararAberto\(false\);[^}]*\}, \[nav\.ticker\]\);/.test(opcoesScreen));
const chamadasSetTicker = opcoesScreen.match(/\bsetTicker\(/g) || [];
ok("nenhum `setTicker(` sobrevive em código: a troca de ativo só passa por `nav` (sem segundo caminho de reset) (reancorado 2026-10-05)",
   chamadasSetTicker.length === 0);
ok("nenhum history/pushState/breadcrumb em OpcoesScreen.jsx (sem histórico de navegação paralelo)",
   !/\bhistory\b/i.test(opcoesScreen) && !/pushState/.test(opcoesScreen) && !/breadcrumb/i.test(opcoesScreen));

// ---- 3) [item 7 original, sem mudança] SecaoSetups.jsx intocada (regressão
// do "não renomear" do UI-SPEC) -----------------------------------------------
ok("SecaoSetups.jsx continua com `cp.opcoesSetupsTitulo`",
   /cp\.opcoesSetupsTitulo/.test(secaoSetupsBruto));
ok("SecaoSetups.jsx continua com `cp.opcoesCriarTitulo`",
   /cp\.opcoesCriarTitulo/.test(secaoSetupsBruto));

// ---- 4) [itens 8/9 originais, re-ancorados sem mudança de condição] cascata
// carregando/erro únicos e em ordem, agora dentro do ramo Montar -------------
// Mesma técnica de fatiamento de sempre: de `{cabecalho}` (só existe dentro
// de Montar) até `cp.opcoesDisclaimer` (primeiro marcador depois do fim de
// TODAS as 3 abas — Oportunidades/Recomendadas não têm cascata própria desde
// o Plano 39-04, D-04).
const iInicioMontar = opcoesScreen.indexOf("{cabecalho}");
const iFimMontar = opcoesScreen.indexOf("cp.opcoesDisclaimer");
const montarSlice = (iInicioMontar >= 0 && iFimMontar > iInicioMontar)
  ? opcoesScreen.slice(iInicioMontar, iFimMontar) : "";
ok("a fatia da aba Montar ({cabecalho} até o disclaimer) foi localizada",
   montarSlice.length > 0);
const iCarregandoCascata = montarSlice.indexOf("carregando ? (");
const iErroCascata = montarSlice.indexOf("erro ? (");
const iVazioCascata = montarSlice.indexOf("nadaParaMostrar ? (");
ok("os três marcadores da cascata (carregando/erro/vazio) foram localizados dentro da aba Montar",
   iCarregandoCascata >= 0 && iErroCascata >= 0 && iVazioCascata >= 0);
ok("carregando ? e erro ? (ramos 1-2) vêm ANTES de nadaParaMostrar ? (ramo 3) — prioridade de estado crítico preservada",
   iCarregandoCascata >= 0 && iErroCascata >= 0 && iVazioCascata >= 0
   && iCarregandoCascata < iVazioCascata && iErroCascata < iVazioCascata);
ok("cp.opcoesCarregando aparece exatamente 1x dentro da aba Montar (ramo 1 não duplicado)",
   (montarSlice.match(/cp\.opcoesCarregando\b/g) || []).length === 1);
ok("cp.opcoesNaoConfigurado aparece exatamente 1x dentro da aba Montar (ramo 2 não duplicado)",
   (montarSlice.match(/cp\.opcoesNaoConfigurado\b/g) || []).length === 1);

// ---- 5) [item 13 original, reversão b — DUAS decisões distintas] ------------
// 5a) a frase-ponte `duasLeiturasIntro` sai de uso (Plano 39-02); a negação
// de hierarquia entre Oportunidades e Recomendadas passa a morar em
// `curadoriaSubtitulo`, nos dois modos (fork 3 do 39-02-PLAN.md).
const subtituloEstudo = (COPY.estudo.curadoriaSubtitulo || "").toLowerCase();
const subtituloOperador = (COPY.operador.curadoriaSubtitulo || "").toLowerCase();
ok("COPY.estudo.curadoriaSubtitulo nega hierarquia (contém \"não\"/\"promessa\"/\"oportunidades\")"
   + " — Fase 39 (39-02, D-05, fork 3, 2026-09-24): substitui a frase-ponte duasLeiturasIntro",
   subtituloEstudo.includes("não") && subtituloEstudo.includes("promessa") && subtituloEstudo.includes("oportunidades"));
ok("COPY.operador.curadoriaSubtitulo nega hierarquia (contém \"não\"/\"promessa\"/\"oportunidades\")"
   + " — mesma nota datada acima",
   subtituloOperador.includes("não") && subtituloOperador.includes("promessa") && subtituloOperador.includes("oportunidades"));
// 5b) "Seus vigias" deixa de ser bloco fixo do hub — vira badge no
// cabeçalho + sheet local (D-07). Fase 39 (39-02/39-04, 2026-09-24).
// REANCORAGEM (2026-10-05, Fase 48): o badge do cabeçalho some; o caminho até
// o sheet é o "ver todos ›" da seção Atenção do HubOpcoes (onVerTodosVigias).
const iHubUso = opcoesScreen.indexOf("<HubOpcoes");
const iVigiasSheet = opcoesScreen.indexOf("<VigiasSheet");
const iSecaoVigiasDentroSheet = iVigiasSheet >= 0 ? opcoesScreen.indexOf("<SecaoVigias", iVigiasSheet) : -1;
ok("`<HubOpcoes` (com onVerTodosVigias) aparece ANTES de `<VigiasSheet`, que envolve `<SecaoVigias` (sheet segue destino de 'ver todos') (reancorado 2026-10-05)",
   iHubUso >= 0 && /onVerTodosVigias=/.test(opcoesScreen) && iVigiasSheet > iHubUso && iSecaoVigiasDentroSheet > iVigiasSheet);
ok("`<VigiasBadge` não existe mais — Vigias não é superfície de mesmo nível do hub (reancorado 2026-10-05)",
   !/<VigiasBadge/.test(opcoesScreen));
ok("OpcoesScreen.jsx não importa mais WorkspaceHeader.jsx (import removido junto com o arquivo)",
   !/from\s+["'][^"']*WorkspaceHeader\.jsx["']/.test(opcoesScreenBruto));

// ---- 6) [itens 6 original, re-ancorado — reversão parcial] as 4 chaves
// antigas de WorkspaceHeader/pill row NÃO foram apagadas — retiradas de uso
// pelo Copywriting Contract do 39-UI-SPEC.md (decisão já registrada em
// copy.js), continuam existindo e não-vazias nos dois modos. Apagá-las sem
// uma decisão D-XX nova reabriria a pergunta que o 39-02 já fechou. --------
const CHAVES_RETIRADAS_DE_USO = [
  "opcoesVoltarAoHub", "opcoesAbaAnalisar", "opcoesAbaComparar", "opcoesAbaSetupsSalvos",
];
const chavesFaltando = CHAVES_RETIRADAS_DE_USO.filter(
  (k) => !COPY.estudo[k] || !COPY.operador[k]);
ok("as 4 chaves retiradas de uso (Fase 34) continuam existindo e não-vazias em COPY.estudo/operador"
   + " (não apagadas sem decisão nova — Copywriting Contract, 39-UI-SPEC.md)"
   + (chavesFaltando.length ? " (faltando/vazia: " + chavesFaltando.join(", ") + ")" : ""),
   chavesFaltando.length === 0);

// ---- 7) (reancorado 2026-10-05) hub novo: cards da carteira + Atenção ------
// Antes: `abaBar` com 3 abas fixas (itens 14/17/18 originais). Agora: o nível
// raiz é o HubOpcoes. Mesmas invariantes de fundo: sem disparador pago além
// do declarado, com afordância/alvo tátil, sem gate por ativo escolhido.
const hubBruto = readFileSync(join(dirOpcoes, "HubOpcoes.jsx"), "utf8");
const hub = semComentario(hubBruto);
const iHubAbre = opcoesScreen.indexOf("<HubOpcoes");
const iHubFecha = iHubAbre >= 0 ? opcoesScreen.indexOf("/>", iHubAbre) : -1;
const hubSlice = (iHubAbre >= 0 && iHubFecha > iHubAbre) ? opcoesScreen.slice(iHubAbre, iHubFecha) : "";
ok("a fatia de `<HubOpcoes ... />` foi localizada", hubSlice.length > 0);
const DISPARADORES_PROIBIDOS = /abrirLeitura|abrirCadeia|abrirOperaveis|montarProposta|verPossibilidades|verMatriz|compilarSetup|confirmarSetup/;
ok("o hub não dispara nenhuma leitura paga fora do 'Atualizar' dos vigias (NAV-05, §3.3 do ADR-027) (reancorado 2026-10-05)",
   hubSlice.length > 0 && !DISPARADORES_PROIBIDOS.test(hubSlice));
ok("o único disparador pago do hub (onAtualizarVigias) declara o custo (custoAtualizar={CUSTO_DA_ACAO.listarVigias}) (reancorado 2026-10-05)",
   /onAtualizarVigias=\{atualizarVigias\}/.test(hubSlice) && /custoAtualizar=\{CUSTO_DA_ACAO\.listarVigias\}/.test(hubSlice));
ok("o hub recebe a CARTEIRA (carteiraHub, de ctx.data.positions), não a watchlist (universo = carteira) (reancorado 2026-10-05)",
   /carteira=\{carteiraHub\}/.test(hubSlice) && !/watchlist/i.test(hubSlice));
ok("HubOpcoes: cards como role=\"button\" com minHeight 64 e teclado (Enter/Espaço) (reancorado 2026-10-05)",
   /role="button"/.test(hub) && /minHeight: 64/.test(hub) && /e\.key === "Enter" \|\| e\.key === " "/.test(hub));
ok("HubOpcoes: a seção Atenção só aparece com vigia (`vigias.length > 0`) e 'ver todos ›' é opcional (onVerTodosVigias) (reancorado 2026-10-05)",
   /vigias\.length > 0 && \(/.test(hub) && /onVerTodosVigias && \(/.test(hub));
ok("HubOpcoes: carteira vazia tem motivo e caminho (hub_vazio_*, onIrCarteira) — vazio nunca é silêncio (reancorado 2026-10-05)",
   /hub_vazio_titulo/.test(hub) && /hub_vazio_cta/.test(hub) && /onClick=\{onIrCarteira\}/.test(hub));
ok("HubOpcoes não menciona Watchlist (reancorado 2026-10-05)", !/watchlist/i.test(hubBruto));
ok("o hub é renderizado SEM gate de ticker: o ramo hub é `{nav.nivel === \"hub\" ? (` (reancorado 2026-10-05)",
   /\{nav\.nivel === "hub" \? \(\s*<HubOpcoes/.test(opcoesScreen));

// ---- 8) [item 15 original, re-ancorado — dependência renomeada] nenhum
// useEffect reage ao estado de navegação (NAV-05) -----------------------------
// REVERSÃO DELIBERADA (2026-09-25, Fase 40, ESTADO-01): passou a existir UM
// useEffect com `abaOpcoes` nas deps — o write-back da memória em sessão
// (`ctx.lembrarOpcoes(memoriaOpcoes(ticker, abaOpcoes))`, ver
// OpcoesScreen.jsx e test_opcoes_continuidade_ui.mjs). A intenção original de
// NAV-05 SEGUE de pé: trocar de aba não pode disparar CHAMADA nenhuma
// (rota/serviço) — o write-back só grava um eco local em memória no
// `App.jsx`, sem tocar `store.*`/rota nenhuma. A exceção é NOMEADA (só essa
// linha exata passa); qualquer OUTRO useEffect com `abaOpcoes` nas deps
// continua reprovado, preservando o guardião.
// REANCORAGEM (2026-10-05, Fase 48): o estado de navegação é `nav` — nenhum
// useEffect com `nav.nivel`/`nav.ticker` nas deps pode disparar CHAMADA
// (store.*/rota). Efeitos permitidos nomeados: write-back da memória, foco no
// título e reset de campos locais (todos sem I/O). Os fetches do fluxo vivem
// nos hooks (useEscada/useTecnicoCarteira), fora deste arquivo.
const blocosDeEfeito = opcoesScreen.split("useEffect(").slice(1);
const efeitoDeNavComIO = blocosDeEfeito.some((bloco) => {
  const fimDeps = bloco.indexOf("]);");
  const trecho = fimDeps >= 0 ? bloco.slice(0, fimDeps + 3) : bloco;
  if (!/\bnav\.(nivel|ticker)\b/.test(trecho.slice(trecho.lastIndexOf("}, ["))) ) return false;
  return /\bstore\./.test(trecho) || /\bmcp[A-Z]/.test(trecho) || /\boptions[A-Z]/.test(trecho) || /\bfetch\(/.test(trecho);
});
ok("nenhum useEffect do arquivo lista nav.nivel/nav.ticker nas dependências e dispara CHAMADA (NAV-05) — só write-back, foco e reset local (sem I/O) (reancorado 2026-10-05)",
   !efeitoDeNavComIO && blocosDeEfeito.some((b) => /nav\.nivel/.test(b)));
ok("a escada e a matriz só são buscadas por hooks dedicados: OpcoesScreen não chama store.opcoesEscada*/mcpEscadaMatriz direto (reancorado 2026-10-05)",
   !/store\.opcoesEscada|store\.mcpEscadaMatriz/.test(opcoesScreen));

// ---- 9) [itens 19/20 originais, reversão b — D-06] SecaoComparar atrás de
// `compararAberto`, não mais de uma pill própria ------------------------------
const iSecaoCompararUso = opcoesScreen.indexOf("<SecaoComparar");
const iTemLeituraGate = opcoesScreen.lastIndexOf("temLeitura ? (", iSecaoCompararUso >= 0 ? iSecaoCompararUso : undefined);
const iCompararAbertoGate = iTemLeituraGate >= 0
  ? opcoesScreen.indexOf("compararAberto ? (", iTemLeituraGate) : -1;
ok("<SecaoComparar continua condicionado a `temLeitura` (sem leitura não há de onde a tese sair)",
   iSecaoCompararUso >= 0 && iTemLeituraGate >= 0 && iTemLeituraGate < iSecaoCompararUso
   && iSecaoCompararUso - iTemLeituraGate < 800);
ok("<SecaoComparar também é condicionado a `compararAberto` (D-06: link inline substitui a pill própria)",
   iCompararAbertoGate >= 0 && iCompararAbertoGate < iSecaoCompararUso
   && iSecaoCompararUso - iCompararAbertoGate < 400);
ok("o link de Comparar usa `aria-expanded={compararAberto}` (afordância de disclosure, substitui a pill ativa)",
   /aria-expanded=\{compararAberto\}/.test(opcoesScreen));
ok("`compararAberto` nasce `false` (useState(false)) — o painel não abre sozinho ao entrar em Montar",
   /const \[compararAberto, setCompararAberto\] = useState\(false\)/.test(opcoesScreen));
ok("os dois rótulos do toggle (mostrar/ocultar) existem como chave de copy, nenhum literal solto",
   /cp\.opcoesVerOutrosVencimentos/.test(opcoesScreen) && /cp\.opcoesOcultarOutrosVencimentos/.test(opcoesScreen));

// ---- 10) [itens 19/20 originais, reversão b — D-06, contrapartida] Analisar
// e Setups salvos deixam de estar atrás de pill/gate — SEMPRE visíveis
// quando a cascata chega no ramo "4. DADOS" -----------------------------------
ok("não sobra nenhuma comparação `abaWorkspace === \"...\"` no arquivo (o gate por pill do ramo 4 foi dissolvido, D-06)",
   !/abaWorkspace\s*===/.test(opcoesScreen));
const iSecaoAnalisarUso = opcoesScreen.indexOf("<SecaoAnalisar");
const iSecaoSetupsUso = opcoesScreen.indexOf("<SecaoSetups", iSecaoAnalisarUso >= 0 ? iSecaoAnalisarUso : 0);
ok("<SecaoAnalisar e <SecaoSetups aparecem exatamente 1x cada no arquivo, sem pill/gate de aba própria",
   (opcoesScreen.match(/<SecaoAnalisar/g) || []).length === 1
   && (opcoesScreen.match(/<SecaoSetups/g) || []).length === 1
   && iSecaoAnalisarUso >= 0 && iSecaoSetupsUso > iSecaoAnalisarUso);

if (fails > 0) {
  console.log(`\n${fails} falha(s).`);
  process.exit(1);
}
console.log("\ntodos os testes passaram");
