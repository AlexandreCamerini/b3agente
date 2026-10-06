// REANCORAGEM — Fase 48 (2026-10-05), caminho B: a aba Opções deixou de ter 3
// sub-abas fixas e passou a um fluxo em profundidade (hub -> objetivo ->
// escada -> confirmar, + "montar" = Montar do zero), num estado único `nav`
// (navOpcoes.js, NIVEIS). O texto original (Fase 39, 2026-09-24) segue
// abaixo, preservado como histórico; cada item reancorado ganha o sufixo
// "(reancorado 2026-10-05)" e troca a ÂNCORA, nunca a invariante: allowlist
// ABAS_OPCOES validando deep-link, one-shot em useEffect([]), SecaoVigias 1x
// dentro de VigiasSheet, SecaoComparar condicional dentro do Montar,
// isolamento ADR-027 e `.manchete` fora dos componentes (guardrail CVM) —
// agora também nos componentes novos do fluxo. Quem verifica o fluxo em
// runtime é test_opcoes_fluxo_render.mjs.
//
// Fase 39, plano 39-04 (2026-09-24) — guardião estrutural do NAV-01: a aba
// Opções tem exatamente 3 abas fixas de nível 1 (Oportunidades/Recomendadas/
// Montar), Vigias vira badge+sheet no cabeçalho, e a sub-aba "Operar"
// (Fase 28) deixa de existir. Substitui, para este invariante, os guardiões
// mais antigos que assumiam a estrutura de duas abas ortogonais (`subaba` ×
// `abaWorkspace`) — aqueles ficam VERMELHOS por desenho ao fim deste plano
// (ver 39-04-PLAN.md, `<repo_guardrail>`) e são reconciliados no Plano 39-05,
// não aqui.
//
// Cada item abaixo nomeia o defeito que ele reprova. Nenhum é decorativo:
//
//  1. **`ABAS_OPCOES` divergindo de `["oportunidades", "recomendadas",
//     "montar"]`, ou o `useState` de `abaOpcoes` aceitando um valor fora da
//     allowlist** (T-39-14) — um deep-link malformado (`ctx.opcoesAbaInicial`)
//     abriria uma aba que não existe na `abaBar`, ou pior, quebraria o
//     `.includes` silenciosamente. `limparOpcoesAbaInicial` fora de um
//     `useEffect(..., [])` reexecutaria o "consumo" do pedido one-shot a
//     cada render, quebrando o canal do Plano 39-02.
//  2. **Qualquer resquício de código (fora de comentário) dos dois estados
//     ortogonais dissolvidos** (`subaba`/`abaWorkspace`/`SubAbaOperar`/
//     `workspacePillRow`/`WorkspaceHeader`/`SecaoDescobrir`/`irParaOperar`) —
//     sobrevivência de qualquer um deles é sinal de dissolução incompleta
//     (SC#1/SC#3).
//  3. **`abaBar` perdendo uma das 3 pills, o alvo de toque de 44px, o
//     `aria-pressed` ou o `flexWrap: "wrap"`, ou passando a depender de
//     `ticker`** — D-01 exige a MESMA barra, sempre, com ou sem ativo
//     escolhido.
//  4. **`VigiasBadge` deixando de ser visível nas 3 abas** (renderizado
//     DEPOIS do primeiro ramo de aba, em vez de antes) — regressão de SC#2.
//     `SecaoVigias` fora do `VigiasSheet`, ou duplicado, quebraria "Vigias
//     abre por um badge... num sheet" (D-07).
//  5. **Um componente de aba vazando para o ramo errado** (ex.:
//     `AbaRecomendadas` renderizado dentro de "oportunidades") — cada aba
//     tem UM conjunto de componentes, e vazamento é a classe de bug que faz
//     duas abas mostrarem o mesmo conteúdo.
//  6. **`SecaoComparar` deixando de ser condicional a `compararAberto`, ou o
//     botão que alterna perdendo `aria-expanded`/o rótulo de copy** — D-06
//     exige expansão INLINE, não uma aba nova.
//  7. **O botão "saiba mais" fixo do topo voltando** (regressão de D-13) —
//     ele tem de morrer, substituído por `infoDaAba(` (esperado 3x, uma por
//     aba). `ANCORAS_KB.opcoes` some do arquivo — o ⓘ contextual perderia a
//     fonte do verbete.
//  8. **`cp.opcoesCustoFrescor`/`cp.opcoesLastroAjuda` voltando a ser
//     parágrafo fixo** em vez de morarem atrás de `<DetalheInfo` — regressão
//     de D-14 (bastidor atrás de ⓘ).
//  9. **`PropostaDoAtivo` perdendo `useAceiteLastreado(`/`<PropostaLastreada`/
//     `<CandidatoOpcao`, ou ganhando uma segunda fonte de dado** (`store.mcp`/
//     `store.options`) ou um `window.confirm` — a Emenda 3 do ADR-027 exige
//     fonte única (o fan-out de `useOpcoesPropostas`, custo zero).
//  10. **Isolamento ADR-027 quebrando em qualquer arquivo de
//      `web/src/opcoes/`** (import de App.jsx) — ou `CuradoriaEstruturas`
//      ganhando um segundo call site, ou `SecaoDescobrir.jsx`/
//      `WorkspaceHeader.jsx` ressuscitando, ou `.manchete` vazando para os
//      wrappers novos (guardrail CVM).
//  11. **Rótulo de navegação colidindo** (SC#4) — chaves antigas
//      (`opcoesSubaba*`/`opcoesAbaAnalisar`/`opcoesAbaComparar`/
//      `opcoesAbaSetupsSalvos`/`duasLeiturasIntro`) voltando a ser
//      referenciadas em OpcoesScreen.jsx, ou os 3 rótulos da `abaBar`
//      deixando de ser distintos entre si e do título "Setups" salvos.
//
// Roda sem build: `node web/tests/test_opcoes_nav_tres_abas_ui.mjs`.
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");

const opcoesScreenBruto = readFileSync(join(dirOpcoes, "OpcoesScreen.jsx"), "utf8");
const abaOportunidadesBruto = readFileSync(join(dirOpcoes, "AbaOportunidades.jsx"), "utf8");
const abaRecomendadasBruto = readFileSync(join(dirOpcoes, "AbaRecomendadas.jsx"), "utf8");
const navOpcoesBruto = readFileSync(join(dirOpcoes, "navOpcoes.js"), "utf8");

// Sem comentários: os próprios doc-comments desta fase citam os termos
// dissolvidos ao explicar a decisão (histórico não se reescreve) — contá-los
// faria o guardião se auto-invalidar (mesmo padrão de
// test_opcoes_hub_workspace_ui.mjs/test_opcoes_subabas_ui.mjs).
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

const opcoesScreen = semComentario(opcoesScreenBruto);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 0) parse mudo -----------------------------------------------------
ok("OpcoesScreen.jsx foi lido e tem corpo (>1000 caracteres)",
   opcoesScreenBruto.length > 1000);

// ---- 1) ABAS_OPCOES, fallback de allowlist e one-shot -------------------
ok("ABAS_OPCOES é exatamente [\"oportunidades\", \"recomendadas\", \"montar\"]",
   /const ABAS_OPCOES = \["oportunidades", "recomendadas", "montar"\];/.test(opcoesScreenBruto));
// REVERSÃO DELIBERADA (2026-09-25, Fase 40, ESTADO-01): o inicializador
// passou a chamar `abaInicialOpcoes(ABAS_OPCOES, ...)`. REANCORAGEM
// (2026-10-05, Fase 48): quem chama é `estadoInicialOpcoes` (navOpcoes.js),
// que delega a `abaInicialOpcoes`/`abrirTickerOpcoes`/`tickerInicialOpcoes`
// (allowlist T-39-14/T-48-36 preservada, coberta por
// test_opcoes_continuidade_ui.mjs e test_opcoes_nav_profundidade.mjs).
// NOTA 2026-10-06 (quick 261006-axi): o quarto campo passou de `carteira` para `carteira: universo` (carteira + ativo só com perna); a regex aceita os dois.
ok("nav nasce validado por estadoInicialOpcoes({ abas: ABAS_OPCOES, abaInicial: ctx.opcoesAbaInicial, ..., memoria: ctx.opcoesMemoria }) (D-03, T-39-14) (reancorado 2026-10-05)",
   /useState\(\(\) => estadoInicialOpcoes\(\{\s*abas: ABAS_OPCOES,\s*abaInicial: ctx && ctx\.opcoesAbaInicial,\s*abrirTicker: ctx && ctx\.opcoesAbrirTicker,\s*memoria: ctx && ctx\.opcoesMemoria,\s*carteira(?:: universo)?,\s*\}\)\)/.test(opcoesScreenBruto));
ok("limparOpcoesAbaInicial é chamado dentro de um useEffect(..., [])",
   /useEffect\(\(\) => \{[\s\S]{0,200}limparOpcoesAbaInicial\(\)[\s\S]{0,80}\}, \[\]\);/.test(opcoesScreenBruto));
ok("os 5 níveis do fluxo (NIVEIS) existem em navOpcoes.js, na ordem hub, objetivo, escada, confirmar, montar (reancorado 2026-10-05)",
   /export const NIVEIS = \["hub", "objetivo", "escada", "confirmar", "montar"\];/.test(navOpcoesBruto));
ok("o estado antigo (abaOpcoes/setAbaOpcoes/oportunidadeAberta/setOportunidadeAberta/setTicker) não sobrevive em código (absorvido por `nav`) (reancorado 2026-10-05)",
   !/\b(abaOpcoes|setAbaOpcoes|oportunidadeAberta|setOportunidadeAberta|setTicker)\b/.test(opcoesScreen));

// ---- 2) resquício de código dos dois estados ortogonais dissolvidos -----
const TOKENS_DISSOLVIDOS = [
  "subaba", "abaWorkspace", "SubAbaOperar", "workspacePillRow",
  "WorkspaceHeader", "SecaoDescobrir", "irParaOperar",
];
for (const tk of TOKENS_DISSOLVIDOS) {
  ok("código sem comentário de OpcoesScreen.jsx não contém `" + tk + "`",
     !new RegExp("\\b" + tk + "\\b").test(opcoesScreen));
}

// ---- 3) (reancorado 2026-10-05) abaBar -> um ramo por NÍVEL ------------
// Antes: 3 pills fixas `abaBar`, fora de condicional de ticker (D-01). Agora:
// a barra deixa de existir e o fluxo tem UM ramo por nível; o contêiner dos
// níveis do hub à confirmação não depende de `ticker` para existir.
ok("a const abaBar NÃO existe mais (a barra de 3 sub-abas deixou de ser superfície) (reancorado 2026-10-05)",
   !/\babaBar\b/.test(opcoesScreen));
const iHub = opcoesScreen.indexOf('{nav.nivel === "hub" ? (');
const iObj = opcoesScreen.indexOf('{nav.nivel === "objetivo" ? (');
const iEsc = opcoesScreen.indexOf('{nav.nivel === "escada" ? (');
const iConf = opcoesScreen.indexOf('{nav.nivel === "confirmar" ? (');
const iMontar = opcoesScreen.indexOf('{nav.nivel === "montar" ? (');
const iDisclaimer = opcoesScreen.indexOf("cp.opcoesDisclaimer");
ok("os 5 ramos de nível foram localizados, na ordem hub → objetivo → escada → confirmar → montar (reancorado 2026-10-05)",
   iHub >= 0 && iObj > iHub && iEsc > iObj && iConf > iEsc && iMontar > iConf && iDisclaimer > iMontar);
const ramoHub = (iHub >= 0 && iObj > iHub) ? opcoesScreen.slice(iHub, iObj) : "";
const ramoObjetivo = (iObj >= 0 && iEsc > iObj) ? opcoesScreen.slice(iObj, iEsc) : "";
const ramoEscada = (iEsc >= 0 && iConf > iEsc) ? opcoesScreen.slice(iEsc, iConf) : "";
const ramoConfirmar = (iConf >= 0 && iMontar > iConf) ? opcoesScreen.slice(iConf, iMontar) : "";
const ramoMontar = (iMontar >= 0 && iDisclaimer > iMontar) ? opcoesScreen.slice(iMontar, iDisclaimer) : "";
ok("as 5 fatias de nível não estão vazias (parse mudo) (reancorado 2026-10-05)",
   [ramoHub, ramoObjetivo, ramoEscada, ramoConfirmar, ramoMontar].every((r) => r.length > 0));
const iSection = opcoesScreen.indexOf("<section");
const trechoAteHub = (iSection >= 0 && iHub > iSection) ? opcoesScreen.slice(iSection, iHub) : "";
ok("o trecho entre <section e o ramo do hub foi localizado e não depende de `ticker` (o hub é o nível raiz, não gateado por ativo) (reancorado 2026-10-05)",
   trechoAteHub.length > 0 && !/\bticker\b/.test(semComentario(trechoAteHub)));

// ---- 4) Vigias: seção Atenção do hub + "ver todos" abre o sheet ---------
ok("<VigiasBadge não existe mais; Vigias saem do cabeçalho (reancorado 2026-10-05)",
   !/<VigiasBadge/.test(opcoesScreen));
ok("o hub recebe onVerTodosVigias que abre o sheet (setVigiasAberto(true)) — Vigias alcançáveis a partir do hub, nível raiz (reancorado 2026-10-05)",
   /onVerTodosVigias=\{\(\) => \{[^}]*setVigiasAberto\(true\)/.test(ramoHub));
ok("<SecaoVigias aparece exatamente 1x no arquivo",
   (opcoesScreen.match(/<SecaoVigias/g) || []).length === 1);
const iVigiasSheetAbre = opcoesScreen.indexOf("<VigiasSheet");
const iVigiasSheetFecha = opcoesScreen.indexOf("</VigiasSheet>");
const iSecaoVigiasUso = opcoesScreen.indexOf("<SecaoVigias");
ok("<SecaoVigias está DENTRO de <VigiasSheet>...</VigiasSheet> (D-07: conteúdo do sheet)",
   iVigiasSheetAbre >= 0 && iVigiasSheetFecha > iVigiasSheetAbre
   && iSecaoVigiasUso > iVigiasSheetAbre && iSecaoVigiasUso < iVigiasSheetFecha);

// ---- 5) (reancorado 2026-10-05) cada componente só no ramo do SEU nível --
ok("<HubOpcoes só no ramo hub; <ObjetivoAtivo só no ramo objetivo; <EscadaObjetivo e <MatrizVencimentos só no ramo escada; <ConfirmarEstrutura só no ramo confirmar (reancorado 2026-10-05)",
   /<HubOpcoes/.test(ramoHub) && /<ObjetivoAtivo/.test(ramoObjetivo)
   && /<EscadaObjetivo/.test(ramoEscada) && /<MatrizVencimentos/.test(ramoEscada)
   && /<ConfirmarEstrutura/.test(ramoConfirmar)
   && (opcoesScreen.match(/<HubOpcoes/g) || []).length === 1
   && (opcoesScreen.match(/<ObjetivoAtivo/g) || []).length === 1
   && (opcoesScreen.match(/<EscadaObjetivo/g) || []).length === 1
   && (opcoesScreen.match(/<MatrizVencimentos/g) || []).length === 1
   && (opcoesScreen.match(/<ConfirmarEstrutura/g) || []).length === 1);
ok("<PropostaDoAtivo (estrutura aberta) só aparece dentro do ramo objetivo, como `estruturaAberta` (reancorado 2026-10-05)",
   /<PropostaDoAtivo/.test(ramoObjetivo)
   && !/<PropostaDoAtivo/.test(ramoHub) && !/<PropostaDoAtivo/.test(ramoEscada)
   && !/<PropostaDoAtivo/.test(ramoConfirmar) && !/<PropostaDoAtivo/.test(ramoMontar));
ok("<AbaOportunidades e <AbaRecomendadas não são mais montadas em OpcoesScreen (Oportunidades = cards do hub; Destacadas = escada) (reancorado 2026-10-05)",
   !/<AbaOportunidades/.test(opcoesScreen) && !/<AbaRecomendadas/.test(opcoesScreen));
ok("<SecaoAnalisar, <SecaoComparar, <SecaoSetups e {cabecalho} só aparecem dentro do ramo Montar",
   /<SecaoAnalisar/.test(ramoMontar) && /<SecaoComparar/.test(ramoMontar) && /<SecaoSetups/.test(ramoMontar) && /\{cabecalho\}/.test(ramoMontar)
   && [ramoHub, ramoObjetivo, ramoEscada, ramoConfirmar].every((r) =>
     !/<SecaoAnalisar/.test(r) && !/<SecaoComparar/.test(r) && !/<SecaoSetups/.test(r) && !/\{cabecalho\}/.test(r)));
ok("o ramo Montar tem '‹ voltar' (voltar(n)) e o hub/objetivo levam a ele via irMontar (Montar do zero alcançável) (reancorado 2026-10-05)",
   /setNav\(\(n\) => voltar\(n\)\)/.test(ramoMontar) && /irMontar\(n\)/.test(ramoObjetivo));

// ---- 6) SecaoComparar guardado por compararAberto (D-06) ----------------
ok("<SecaoComparar só é renderizado sob `compararAberto ? ... : null`",
   /compararAberto \? \(\s*<SecaoComparar/.test(ramoMontar));
ok("o botão que alterna Comparar tem aria-expanded={compararAberto} e usa cp.opcoesVerOutrosVencimentos",
   /aria-expanded=\{compararAberto\}/.test(ramoMontar) && /cp\.opcoesVerOutrosVencimentos/.test(ramoMontar));

// ---- 7) sem "saiba mais" fixo; infoDaAba( no Montar; ANCORAS_KB.opcoes vivo
ok("nenhum botão \"saiba mais\" fixo (cp.saibaMais) em OpcoesScreen (D-13: vira ⓘ) (reancorado 2026-10-05)",
   !/cp\.saibaMais/.test(opcoesScreen));
ok("infoDaAba( aparece exatamente 1x — só o ⓘ do Montar sobrou; as outras duas abas deixaram de existir (reancorado 2026-10-05)",
   (opcoesScreen.match(/infoDaAba\(/g) || []).length === 1 && /infoDaAba\(/.test(ramoMontar));
ok("ANCORAS_KB.opcoes segue referenciado (fonte do verbete do ⓘ)",
   /ANCORAS_KB\.opcoes/.test(opcoesScreen));

// ---- 8) bastidor atrás de ⓘ (D-14) --------------------------------------
const iCabecalhoConst = opcoesScreen.indexOf("const cabecalho = (");
const iCabecalhoFimConst = iCabecalhoConst >= 0 ? opcoesScreen.indexOf("\n  );", iCabecalhoConst) : -1;
const corpoCabecalho = (iCabecalhoConst >= 0 && iCabecalhoFimConst > iCabecalhoConst)
  ? opcoesScreen.slice(iCabecalhoConst, iCabecalhoFimConst) : "";
ok("a const cabecalho foi localizada", corpoCabecalho.length > 0);
ok("cp.opcoesCustoFrescor NÃO aparece dentro do literal de `cabecalho`",
   corpoCabecalho.length > 0 && !/cp\.opcoesCustoFrescor/.test(corpoCabecalho));
ok("cp.opcoesCustoFrescor aparece dentro de <DetalheInfo",
   /<DetalheInfo[\s\S]{0,120}cp\.opcoesCustoFrescor/.test(opcoesScreen));
ok("cp.opcoesLastroAjuda aparece dentro de <DetalheInfo (D-14: mecânica de lastro atrás de ⓘ)",
   /<DetalheInfo[\s\S]{0,160}opcoesLastroAjuda/.test(opcoesScreen));

// ---- 9) PropostaDoAtivo: fonte única, sem store.mcp/store.options -------
const iPropostaDoAtivoFn = opcoesScreen.indexOf("function PropostaDoAtivo(");
ok("function PropostaDoAtivo foi localizada", iPropostaDoAtivoFn >= 0);
// Fim do componente: próxima declaração de função/const de módulo depois
// dele (LastroDoAtivo, a próxima função do arquivo).
const iFimPropostaDoAtivo = iPropostaDoAtivoFn >= 0
  ? opcoesScreen.indexOf("\nfunction LastroDoAtivo", iPropostaDoAtivoFn) : -1;
const corpoPropostaDoAtivo = (iPropostaDoAtivoFn >= 0 && iFimPropostaDoAtivo > iPropostaDoAtivoFn)
  ? opcoesScreen.slice(iPropostaDoAtivoFn, iFimPropostaDoAtivo) : "";
ok("o corpo de PropostaDoAtivo (até a próxima função do arquivo) foi localizado",
   corpoPropostaDoAtivo.length > 0);
ok("PropostaDoAtivo usa useAceiteLastreado(, <PropostaLastreada e <CandidatoOpcao",
   corpoPropostaDoAtivo.length > 0
   && /useAceiteLastreado\(/.test(corpoPropostaDoAtivo)
   && /<PropostaLastreada/.test(corpoPropostaDoAtivo)
   && /<CandidatoOpcao/.test(corpoPropostaDoAtivo));
ok("PropostaDoAtivo não contém store.mcp/store.options/window.confirm (fonte única: opcoesPorTicker)",
   corpoPropostaDoAtivo.length > 0
   && !/store\.mcp/.test(corpoPropostaDoAtivo)
   && !/store\.options/.test(corpoPropostaDoAtivo)
   && !/window\.confirm/.test(corpoPropostaDoAtivo));

// ---- 10) isolamento ADR-027 + call site único de CuradoriaEstruturas ----
ok("nenhum arquivo de web/src/opcoes/ importa App.jsx (OpcoesScreen/AbaOportunidades/AbaRecomendadas)",
   !/from\s+["'][^"']*App\.jsx["']/.test(opcoesScreenBruto)
   && !/from\s+["'][^"']*App\.jsx["']/.test(abaOportunidadesBruto)
   && !/from\s+["'][^"']*App\.jsx["']/.test(abaRecomendadasBruto));
// REANCORAGEM (2026-10-05): o isolamento e a regra CVM valem também para os
// componentes novos do caminho B (48-08/48-09) — nenhum importa App.jsx e
// nenhum renderiza a manchete do card.
const NOVOS = ["HubOpcoes.jsx", "ObjetivoAtivo.jsx", "EscadaObjetivo.jsx", "ConfirmarEstrutura.jsx",
  "MatrizVencimentos.jsx", "GraficoResultado.jsx", "TermoOpcoes.jsx", "useEscada.js", "useTecnicoCarteira.js",
  "navOpcoes.js", "fluxoEstilo.js"];
const novosBrutos = NOVOS.map((f) => readFileSync(join(dirOpcoes, f), "utf8"));
ok("nenhum componente/hook novo do fluxo importa App.jsx (isolamento ADR-027) (reancorado 2026-10-05)",
   novosBrutos.every((t) => !/from\s+["'][^"']*App\.jsx["']/.test(t)));
ok("nenhum componente/hook novo do fluxo renderiza `.manchete` (guardrail CVM) (reancorado 2026-10-05)",
   novosBrutos.every((t) => !/\.manchete\b/.test(semComentario(t))));
ok("<CuradoriaEstruturas aparece exatamente 1x em AbaRecomendadas.jsx",
   (abaRecomendadasBruto.match(/<CuradoriaEstruturas/g) || []).length === 1);
ok("SecaoDescobrir.jsx e WorkspaceHeader.jsx não existem mais",
   !existsSync(join(dirOpcoes, "SecaoDescobrir.jsx")) && !existsSync(join(dirOpcoes, "WorkspaceHeader.jsx")));
// Comentários citam ".manchete" ao explicar a decisão (guardrail CVM) — sem
// tirar comentário, o guardião acharia o próprio texto explicativo e se
// auto-invalidaria (mesmo padrão de semComentario acima).
ok("AbaOportunidades.jsx e AbaRecomendadas.jsx não renderizam `.manchete` (guardrail CVM)",
   !/\.manchete\b/.test(semComentario(abaOportunidadesBruto)) && !/\.manchete\b/.test(semComentario(abaRecomendadasBruto)));

// ---- 11) paridade de rótulo — SC#4 --------------------------------------
const CHAVES_APOSENTADAS = [
  "opcoesSubabaSetups", "opcoesSubabaOperar", "opcoesAbaAnalisar",
  "opcoesAbaComparar", "opcoesAbaSetupsSalvos", "duasLeiturasIntro",
];
const chavesReferenciadas = CHAVES_APOSENTADAS.filter(
  (k) => new RegExp("cp\\." + k + "\\b").test(opcoesScreen));
ok("nenhuma chave aposentada (opcoesSubaba*/opcoesAbaAnalisar/opcoesAbaComparar/opcoesAbaSetupsSalvos/duasLeiturasIntro) é referenciada em OpcoesScreen.jsx"
   + (chavesReferenciadas.length ? " (encontradas: " + chavesReferenciadas.join(", ") + ")" : ""),
   chavesReferenciadas.length === 0);

for (const modo of ["estudo", "operador"]) {
  const c = COPY[modo];
  const rotulos = [c.opcoesAbaOportunidades, c.opcoesAbaRecomendadas, c.opcoesAbaMontar];
  const distintosEntreSi = new Set(rotulos).size === 3;
  const distintoDeSetups = !rotulos.includes(c.opcoesSetupsTitulo);
  ok("modo " + modo + ": os 3 rótulos da abaBar são distintos entre si e de cp.opcoesSetupsTitulo (SC#4)",
     distintosEntreSi && distintoDeSetups);
}

console.log(fails === 0 ? "TODOS OS " + "TESTES PASSARAM" : fails + " FALHA(S)");
if (fails > 0) {
  process.exit(1);
}
