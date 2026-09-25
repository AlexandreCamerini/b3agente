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
// passou a chamar `abaInicialOpcoes(ABAS_OPCOES, ctx.opcoesAbaInicial,
// ctx.opcoesMemoria)` em vez de inline `.includes`. A allowlist T-39-14
// continua valendo — só que aplicada DENTRO da função pura
// `web/src/opcoes/memoriaOpcoes.js`, coberta comportamentalmente por
// `test_opcoes_continuidade_ui.mjs` (cenários de deep-link/aba inválida).
ok("abaOpcoes nasce validado por abaInicialOpcoes(ABAS_OPCOES, ctx.opcoesAbaInicial, ctx.opcoesMemoria) (D-03, T-39-14)",
   /useState\(\(\) => abaInicialOpcoes\(ABAS_OPCOES, ctx && ctx\.opcoesAbaInicial, ctx && ctx\.opcoesMemoria\)\)/.test(opcoesScreenBruto));
ok("limparOpcoesAbaInicial é chamado dentro de um useEffect(..., [])",
   /useEffect\(\(\) => \{[\s\S]{0,200}limparOpcoesAbaInicial\(\)[\s\S]{0,80}\}, \[\]\);/.test(opcoesScreenBruto));

// ---- 2) resquício de código dos dois estados ortogonais dissolvidos -----
const TOKENS_DISSOLVIDOS = [
  "subaba", "abaWorkspace", "SubAbaOperar", "workspacePillRow",
  "WorkspaceHeader", "SecaoDescobrir", "irParaOperar",
];
for (const tk of TOKENS_DISSOLVIDOS) {
  ok("código sem comentário de OpcoesScreen.jsx não contém `" + tk + "`",
     !new RegExp("\\b" + tk + "\\b").test(opcoesScreen));
}

// ---- 3) abaBar: 3 pills fixas, fora de condicional de ticker ------------
const iAbaBarConst = opcoesScreen.indexOf("const abaBar = (");
const iAbaBarFimConst = iAbaBarConst >= 0 ? opcoesScreen.indexOf("\n  );", iAbaBarConst) : -1;
const corpoAbaBar = (iAbaBarConst >= 0 && iAbaBarFimConst > iAbaBarConst)
  ? opcoesScreen.slice(iAbaBarConst, iAbaBarFimConst) : "";
ok("a const abaBar foi localizada", corpoAbaBar.length > 0);
ok("abaBar referencia cp.opcoesAbaOportunidades/opcoesAbaRecomendadas/opcoesAbaMontar",
   /cp\.opcoesAbaOportunidades/.test(corpoAbaBar) && /cp\.opcoesAbaRecomendadas/.test(corpoAbaBar) && /cp\.opcoesAbaMontar/.test(corpoAbaBar));
ok("abaBar declara aria-pressed, minHeight: \"44px\" e flexWrap: \"wrap\"",
   /aria-pressed=\{abaOpcoes === a\.id\}/.test(corpoAbaBar) && /minHeight:\s*"44px"/.test(corpoAbaBar) && /flexWrap:\s*"wrap"/.test(corpoAbaBar));
ok("{abaBar} aparece exatamente 1x no arquivo",
   (opcoesScreen.match(/\{abaBar\}/g) || []).length === 1);
const iSection = opcoesScreen.indexOf("<section>");
const iAbaBarUso = opcoesScreen.indexOf("{abaBar}");
const trechoAteAbaBar = (iSection >= 0 && iAbaBarUso > iSection) ? opcoesScreen.slice(iSection, iAbaBarUso) : "";
ok("o trecho entre <section> e {abaBar} foi localizado", trechoAteAbaBar.length > 0);
ok("o trecho entre <section> e {abaBar} não depende de `ticker` (D-01: abaBar não é gateada por ativo escolhido)",
   trechoAteAbaBar.length > 0 && !/\bticker\b/.test(trechoAteAbaBar));

// ---- 4) VigiasBadge visível nas 3 abas; SecaoVigias só dentro do sheet --
const iVigiasBadgeUso = opcoesScreen.indexOf("<VigiasBadge");
const iPrimeiraAba = opcoesScreen.indexOf('abaOpcoes === "');
ok("<VigiasBadge e o primeiro ramo `abaOpcoes === \"` foram localizados",
   iVigiasBadgeUso >= 0 && iPrimeiraAba >= 0);
ok("<VigiasBadge aparece ANTES do primeiro ramo de aba (visível nas 3 abas, SC#2)",
   iVigiasBadgeUso >= 0 && iPrimeiraAba >= 0 && iVigiasBadgeUso < iPrimeiraAba);
ok("<SecaoVigias aparece exatamente 1x no arquivo",
   (opcoesScreen.match(/<SecaoVigias/g) || []).length === 1);
const iVigiasSheetAbre = opcoesScreen.indexOf("<VigiasSheet");
const iVigiasSheetFecha = opcoesScreen.indexOf("</VigiasSheet>");
const iSecaoVigiasUso = opcoesScreen.indexOf("<SecaoVigias");
ok("<SecaoVigias está DENTRO de <VigiasSheet>...</VigiasSheet> (D-07: conteúdo do sheet)",
   iVigiasSheetAbre >= 0 && iVigiasSheetFecha > iVigiasSheetAbre
   && iSecaoVigiasUso > iVigiasSheetAbre && iSecaoVigiasUso < iVigiasSheetFecha);

// ---- 5) cada componente só no ramo da SUA aba --------------------------
// Fatiamento pelos 3 ramos `abaOpcoes === "..."`, na ordem em que aparecem.
const iOport = opcoesScreen.indexOf('abaOpcoes === "oportunidades"');
const iRecom = opcoesScreen.indexOf('abaOpcoes === "recomendadas"');
const iMontar = opcoesScreen.indexOf('abaOpcoes === "montar"');
ok("os 3 ramos de aba foram localizados, na ordem Oportunidades → Recomendadas → Montar",
   iOport >= 0 && iRecom > iOport && iMontar > iRecom);
const ramoOportunidades = (iOport >= 0 && iRecom > iOport) ? opcoesScreen.slice(iOport, iRecom) : "";
const ramoRecomendadas = (iRecom >= 0 && iMontar > iRecom) ? opcoesScreen.slice(iRecom, iMontar) : "";
// Fim do ramo Montar: até o `<p>` do disclaimer, primeiro elemento comum a
// todas as abas (rodapé global) que vem logo depois do bloco de Montar.
const iDisclaimer = opcoesScreen.indexOf("cp.opcoesDisclaimer");
const ramoMontar = (iMontar >= 0 && iDisclaimer > iMontar) ? opcoesScreen.slice(iMontar, iDisclaimer) : "";
ok("as 3 fatias de aba não estão vazias (parse mudo)",
   ramoOportunidades.length > 0 && ramoRecomendadas.length > 0 && ramoMontar.length > 0);

ok("<AbaOportunidades e <PropostaDoAtivo só aparecem dentro do ramo Oportunidades",
   /<AbaOportunidades/.test(ramoOportunidades) && /<PropostaDoAtivo/.test(ramoOportunidades)
   && !/<AbaOportunidades/.test(ramoRecomendadas) && !/<PropostaDoAtivo/.test(ramoRecomendadas)
   && !/<AbaOportunidades/.test(ramoMontar) && !/<PropostaDoAtivo/.test(ramoMontar));
ok("<AbaRecomendadas só aparece dentro do ramo Recomendadas",
   /<AbaRecomendadas/.test(ramoRecomendadas)
   && !/<AbaRecomendadas/.test(ramoOportunidades) && !/<AbaRecomendadas/.test(ramoMontar));
ok("<SecaoAnalisar, <SecaoComparar, <SecaoSetups e {cabecalho} só aparecem dentro do ramo Montar",
   /<SecaoAnalisar/.test(ramoMontar) && /<SecaoComparar/.test(ramoMontar) && /<SecaoSetups/.test(ramoMontar) && /\{cabecalho\}/.test(ramoMontar)
   && !/<SecaoAnalisar/.test(ramoOportunidades) && !/<SecaoComparar/.test(ramoOportunidades) && !/<SecaoSetups/.test(ramoOportunidades) && !/\{cabecalho\}/.test(ramoOportunidades)
   && !/<SecaoAnalisar/.test(ramoRecomendadas) && !/<SecaoComparar/.test(ramoRecomendadas) && !/<SecaoSetups/.test(ramoRecomendadas) && !/\{cabecalho\}/.test(ramoRecomendadas));

// ---- 6) SecaoComparar guardado por compararAberto (D-06) ----------------
ok("<SecaoComparar só é renderizado sob `compararAberto ? ... : null`",
   /compararAberto \? \(\s*<SecaoComparar/.test(ramoMontar));
ok("o botão que alterna Comparar tem aria-expanded={compararAberto} e usa cp.opcoesVerOutrosVencimentos",
   /aria-expanded=\{compararAberto\}/.test(ramoMontar) && /cp\.opcoesVerOutrosVencimentos/.test(ramoMontar));

// ---- 7) sem "saiba mais" fixo; infoDaAba( 3x; ANCORAS_KB.opcoes vivo ----
const iH1Fecha = opcoesScreen.indexOf("</h1>");
const trechoAteAbaBarDoH1 = (iH1Fecha >= 0 && iAbaBarUso > iH1Fecha) ? opcoesScreen.slice(iH1Fecha, iAbaBarUso) : "";
ok("nenhum botão \"saiba mais\" solto entre </h1> e {abaBar} (D-13: vira ⓘ por aba)",
   trechoAteAbaBarDoH1.length > 0 && !/cp\.saibaMais/.test(trechoAteAbaBarDoH1));
ok("infoDaAba( aparece exatamente 3x (uma por aba, D-13)",
   (opcoesScreen.match(/infoDaAba\(/g) || []).length === 3);
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
