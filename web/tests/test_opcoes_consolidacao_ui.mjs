// Fase 32 (32-03, 2026-09-15) — Guardião DEDICADO da consolidação das
// operações de opções na aba Opções. Reprova a volta dos dois blocos
// cross-carteira para Posições e a perda da frase-ponte obrigatória (D-05,
// histórica — ver nota datada abaixo).
//
// Contexto: os blocos "Oportunidades de opções" (motor COM gate) e "as 4
// melhores oportunidades de opções" (motor SEM gate) migraram de
// CarteiraScreen (App.jsx) para o topo da sub-aba Setups da aba Opções
// (OpcoesScreen.jsx) — D-04/D-07. Posições ganhou uma linha de chamada
// única, com contagem lida da MESMA fonte que alimenta a lista (D-03).
//
// 2026-09-24, Fase 39 (39-04/39-05, NAV-01) — RECONCILIAÇÃO. `SecaoDescobrir.jsx`
// (Fase 33-02) foi DELETADO — os dois blocos cross-carteira que ali
// conviviam NUMA MESMA TELA, separados pela frase-ponte, viram DUAS ABAS
// FIXAS IRMÃS e mutuamente exclusivas (Oportunidades/Recomendadas, D-01/D-02),
// cada uma com o próprio arquivo (`AbaOportunidades.jsx`/`AbaRecomendadas.jsx`)
// e o próprio `CarimboFrescor` (D-04b da Fase 33 preservado, sem mudança).
// Reversões (nota datada, nenhum `ok(` apagado sem substituto —
// T-39-19/T-39-20 do 39-05-PLAN.md):
//
//  · Item 1 (ordem `<SecaoDescobrir` < `<SecaoVigias`, e DENTRO dele
//    `duasLeiturasIntro` < `<OportunidadesOpcoes` < `<CuradoriaEstruturas`) —
//    REVERTIDO: os dois motores não dividem mais tela nenhuma, então "ordem
//    sequencial" deixa de fazer sentido — viram abas MUTUAMENTE EXCLUSIVAS.
//    Substituído pela checagem de exclusividade (item 1 novo).
//  · Item 2 (frase-ponte incondicional, D-05) — REVERTIDO: `duasLeiturasIntro`
//    sai de uso (Plano 39-02); a negação de hierarquia passa a morar em
//    `curadoriaSubtitulo` (checada com nota própria em
//    `test_opcoes_hub_workspace_ui.mjs`, item 5a — não duplicada aqui).
//    Substituído por uma prova negativa: nenhum dos dois arquivos novos
//    referencia `duasLeiturasIntro` (item 2 novo).
//  · Item 8 (D-06, nada entre a frase-ponte e os vigias) — re-ancorado: sem
//    frase-ponte nem bloco fixo de vigias, a varredura de sticky/input passa
//    a cobrir os dois arquivos novos inteiros (item 8 novo).
//  · Item 9 (onExecutar somado OpcoesScreen.jsx + SecaoDescobrir.jsx) —
//    re-ancorado (a), soma cai para 1 arquivo só: `SecaoDescobrir.jsx` não
//    existe mais, então a contagem é só sobre `OpcoesScreen.jsx`.
//  · Item 13 (fio de `concluido` via SecaoDescobrir.jsx) — re-ancorado (a):
//    `OpcoesScreen.jsx` passa `curadoria={ctx && ctx.curadoria}` direto para
//    `AbaRecomendadas.jsx`, que repassa a mesma expressão de sempre para
//    `CuradoriaEstruturas`.
//  · Item 14 (SecaoDescobrir.jsx sem .sort(/.reverse() — re-ancorado (a) para
//    os dois arquivos novos, `AbaOportunidades.jsx`/`AbaRecomendadas.jsx`.
//
// Itens 3-7, 10-12, 15 não referenciam `SecaoDescobrir.jsx` e não mudam de
// condição — re-executados sem alteração (a).
//
// Roda sem build: `node web/tests/test_opcoes_consolidacao_ui.mjs`.
import { readFileSync, readdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirSrc = join(here, "..", "src");
const dirOpcoes = join(dirSrc, "opcoes");

const app = readFileSync(join(dirSrc, "App.jsx"), "utf8");
const tela = readFileSync(join(dirOpcoes, "OpcoesScreen.jsx"), "utf8");
const curadoriaModulo = readFileSync(join(dirOpcoes, "CuradoriaEstruturas.jsx"), "utf8");
const executarCandidato = readFileSync(join(dirOpcoes, "executarCandidato.js"), "utf8");
// Fase 39 (39-04/39-05, 2026-09-24): `SecaoDescobrir.jsx` foi DELETADO — a
// frase-ponte + Bloco A + Bloco B que viviam nele viram DUAS ABAS próprias.
const abaOportunidadesModulo = readFileSync(join(dirOpcoes, "AbaOportunidades.jsx"), "utf8");
const abaRecomendadasModulo = readFileSync(join(dirOpcoes, "AbaRecomendadas.jsx"), "utf8");

// Remove comentários de bloco ({/* ... */} e /* ... */) ANTES de filtrar
// linhas `//` — mesmo padrão de test_opcoes_subabas_ui.mjs. Sem isto, um
// comentário explicativo que MENCIONA "scrollIntoView"/"posicao-" (para
// dizer que o padrão foi abandonado) faria este guardião reprovar por
// vacuidade — o próprio texto que documenta a ausência do defeito.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const appSC = semComentario(app);
const telaSC = semComentario(tela);
const curadoriaSC = semComentario(curadoriaModulo);
const abaOportunidadesSC = semComentario(abaOportunidadesModulo);
const abaRecomendadasSC = semComentario(abaRecomendadasModulo);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- (1) [reversão b] exclusividade mútua entre as duas abas cross-carteira
// (substitui a ordem sequencial de antes — os dois motores não dividem mais
// a mesma tela, D-01/D-02) ----------------------------------------------------
const iRamoOportunidades = telaSC.indexOf('abaOpcoes === "oportunidades" ? (');
const iRamoRecomendadas = telaSC.indexOf('abaOpcoes === "recomendadas" ? (');
ok("os dois ramos abaOpcoes === \"oportunidades\"/\"recomendadas\" foram localizados em OpcoesScreen.jsx",
  iRamoOportunidades > -1 && iRamoRecomendadas > -1);
const fimRamoOportunidades = iRamoRecomendadas > iRamoOportunidades ? iRamoRecomendadas : telaSC.length;
const corpoRamoOportunidades = telaSC.slice(iRamoOportunidades, fimRamoOportunidades);
ok("o ramo \"oportunidades\" contém <AbaOportunidades e NÃO contém <AbaRecomendadas (abas mutuamente exclusivas)",
  corpoRamoOportunidades.includes("<AbaOportunidades") && !corpoRamoOportunidades.includes("<AbaRecomendadas"));
const iFimRamoRecomendadas = telaSC.indexOf('abaOpcoes === "montar" ? (', iRamoRecomendadas);
const corpoRamoRecomendadas = (iFimRamoRecomendadas > iRamoRecomendadas)
  ? telaSC.slice(iRamoRecomendadas, iFimRamoRecomendadas) : "";
ok("o ramo \"recomendadas\" contém <AbaRecomendadas e NÃO contém <AbaOportunidades (abas mutuamente exclusivas)",
  corpoRamoRecomendadas.length > 0
  && corpoRamoRecomendadas.includes("<AbaRecomendadas") && !corpoRamoRecomendadas.includes("<AbaOportunidades"));

// ---- (2) [reversão b] frase-ponte dissolvida (D-05 histórico) --------------
// A negação de hierarquia entre os dois motores passa a morar em
// `curadoriaSubtitulo` — checado com nota própria em
// `test_opcoes_hub_workspace_ui.mjs` (item 5a), não duplicado aqui. Esta
// prova é NEGATIVA: nenhum dos dois arquivos novos pode ter ressuscitado a
// frase-ponte por engano (voltaria a acoplar as duas abas).
ok("AbaOportunidades.jsx NÃO referencia duasLeiturasIntro (frase-ponte dissolvida, D-05/39-02)",
  !abaOportunidadesSC.includes("duasLeiturasIntro"));
ok("AbaRecomendadas.jsx NÃO referencia duasLeiturasIntro (frase-ponte dissolvida, D-05/39-02)",
  !abaRecomendadasSC.includes("duasLeiturasIntro"));
ok("cada aba nova tem o próprio <CarimboFrescor (D-04b da Fase 33 preservado — carimbo por aba, não mais um só compartilhado)",
  /<CarimboFrescor/.test(abaOportunidadesSC) && /<CarimboFrescor/.test(abaRecomendadasSC));

// ---- (3) App.jsx não renderiza mais os dois blocos -------------------------
ok("App.jsx NÃO contém <OportunidadesOpcoes",
  !appSC.includes("<OportunidadesOpcoes"));
ok("App.jsx NÃO contém <CuradoriaEstruturas",
  !appSC.includes("<CuradoriaEstruturas"));

// ---- (4) <LinhaChamadaOpcoes aparece 1x em App.jsx (D-01) ------------------
ok("App.jsx contém <LinhaChamadaOpcoes exatamente 1x",
  (appSC.match(/<LinhaChamadaOpcoes/g) || []).length === 1);

// ---- (5) os 4 estados + contagem de origem única (D-03) --------------------
const iDefLinha = app.indexOf("function LinhaChamadaOpcoes");
const iDefCarteira = app.indexOf("function CarteiraScreen(");
const fatiaLinha = (iDefLinha > -1 && iDefCarteira > iDefLinha) ? app.slice(iDefLinha, iDefCarteira) : "";
ok("LinhaChamadaOpcoes foi localizada", fatiaLinha.length > 0);
ok("LinhaChamadaOpcoes referencia os 4 estados (Erro/Carregando/Vazia/Texto)",
  fatiaLinha.includes("linhaChamadaOpcoesErro") && fatiaLinha.includes("linhaChamadaOpcoesCarregando")
  && fatiaLinha.includes("linhaChamadaOpcoesVazia") && fatiaLinha.includes("linhaChamadaOpcoesTexto"));
ok("cp.linhaChamadaOpcoesTexto( é chamado exatamente 1x dentro de LinhaChamadaOpcoes",
  (fatiaLinha.match(/linhaChamadaOpcoesTexto\(/g) || []).length === 1);

// ---- (6) sem recálculo local de contagem -----------------------------------
ok("LinhaChamadaOpcoes NÃO usa .filter( no corpo",
  !fatiaLinha.includes(".filter("));
ok("LinhaChamadaOpcoes NÃO usa .reduce( no corpo",
  !fatiaLinha.includes(".reduce("));
ok("LinhaChamadaOpcoes NÃO referencia `positions` (a contagem vem pronta de curadoria.top.length)",
  !/\bpositions\b/.test(fatiaLinha));
ok("LinhaChamadaOpcoes lê curadoria.top.length (fonte única, D-03)",
  fatiaLinha.includes("curadoria.top.length") || /\btop\s*=\s*\(curadoria/.test(fatiaLinha));

// ---- (7) navegação para a aba Recomendadas (D-02) --------------------------
// Fase 39 (NAV-01): a linha de chamada conta itens da CURADORIA (aba
// Recomendadas) — reversão deliberada, guardião atualizado com nota, não
// apagado: a linha passa a levar direto a essa aba. O parâmetro de
// ctx.goOpcoes é id de ABA, nunca ticker/candidato — o invariante "sem
// deep-link de ticker/candidato" continua.
ok('App.jsx passa onIr={() => ctx.goOpcoes("recomendadas")} para LinhaChamadaOpcoes',
  appSC.includes('onIr={() => ctx.goOpcoes("recomendadas")}'));
ok('ctx.goOpcoes(aba) só usa o parâmetro para setOpcoesAbaInicial, guardado por typeof aba === "string", antes de navigate("opcoes") (sem parâmetro de ticker/candidato)',
  /goOpcoes:\s*\(aba\)\s*=>\s*\{\s*if\s*\(typeof aba === "string"\)\s*setOpcoesAbaInicial\(aba\);\s*navigate\("opcoes"\);\s*\}/.test(appSC));

// ---- (8) [re-ancorado] D-06: nada impede busca depois ----------------------
// Fase 39 (39-05, 2026-09-24): sem frase-ponte nem bloco fixo de vigias para
// medir "o trecho entre os dois", a varredura passa a cobrir os DOIS
// arquivos novos inteiros — a intenção (nada se intromete no fluxo das duas
// abas cross-carteira) é a mesma.
const duasAbasFonte = abaOportunidadesSC + "\n" + abaRecomendadasSC;
ok('nenhum position: "sticky"/"fixed" em AbaOportunidades.jsx/AbaRecomendadas.jsx',
  !/position:\s*["']?(sticky|fixed)/.test(duasAbasFonte));
ok("nenhum <input de busca/filtro em AbaOportunidades.jsx/AbaRecomendadas.jsx",
  !/<input/.test(duasAbasFonte));

// ---- (9) [re-ancorado a] regressão do collar curado ------------------------
// Fase 39 (39-05, 2026-09-24): `SecaoDescobrir.jsx` não existe mais — o fio
// só pode estar em `OpcoesScreen.jsx` (não soma mais dois arquivos).
const nOnExecutar =
  (telaSC.match(/onExecutar=\{\(cand, o\) => ctx\.A\.executarCandidatoCurado\(cand, o\)\}/g) || []).length;
ok("onExecutar liga a ctx.A.executarCandidatoCurado exatamente 1x em OpcoesScreen.jsx",
  nOnExecutar === 1);
ok("executarCandidato.js continua despachando para tipo === \"collar\" (optionsCuradoriaAbrirCollar)",
  /if\s*\(tipo === "collar"\)/.test(executarCandidato) && executarCandidato.includes("optionsCuradoriaAbrirCollar"));
ok("CuradoriaEstruturas.jsx NÃO chama store.<metodo>( dentro do componente",
  !/\bstore\.\w+\(/.test(curadoriaSC));
ok("CuradoriaEstruturas.jsx NÃO chama api.<metodo>( dentro do componente",
  !/\bapi\.\w+\(/.test(curadoriaSC));

// ---- (10) estado de erro do Bloco B ----------------------------------------
ok("CuradoriaEstruturas.jsx referencia cp.curadoriaErroBusca",
  curadoriaSC.includes("cp.curadoriaErroBusca"));
const iRamoVazio = curadoriaSC.indexOf("cp.curadoriaVazio");
const trechoAntesVazio = iRamoVazio > -1 ? curadoriaSC.slice(Math.max(0, iRamoVazio - 300), iRamoVazio) : "";
ok("o ramo que mostra cp.curadoriaVazio exige !erro (a tela não afirma \"nada elegível\" quando a busca falhou)",
  trechoAntesVazio.includes("!erro"));

// ---- (11) Pitfall 4: sem scrollIntoView / âncora "posicao-" ----------------
// Varredura de DIRETÓRIO (D-02 do 33-CONTEXT.md) — estende a proibição a
// qualquer arquivo da pasta, cobrindo AbaOportunidades.jsx/AbaRecomendadas.jsx
// automaticamente, sem precisar atualizar esta lista.
const arquivosOpcoesDirConsolidacao = readdirSync(dirOpcoes).filter((f) => f.endsWith(".jsx") || f.endsWith(".js"));
ok("achou pelo menos 15 arquivos em web/src/opcoes/ (sanidade da varredura, Pitfall 4)",
  arquivosOpcoesDirConsolidacao.length >= 15);
const comScrollIntoView = arquivosOpcoesDirConsolidacao.filter((f) => {
  const src = semComentario(readFileSync(join(dirOpcoes, f), "utf8"));
  return src.includes("scrollIntoView");
});
ok("nenhum arquivo de web/src/opcoes/ contém scrollIntoView"
  + (comScrollIntoView.length ? " (violam: " + comScrollIntoView.join(", ") + ")" : ""),
  comScrollIntoView.length === 0);
const comAncoraPosicao = arquivosOpcoesDirConsolidacao.filter((f) => {
  const src = semComentario(readFileSync(join(dirOpcoes, f), "utf8"));
  return src.includes("posicao-");
});
ok("nenhum arquivo de web/src/opcoes/ contém a âncora \"posicao-\""
  + (comAncoraPosicao.length ? " (violam: " + comAncoraPosicao.join(", ") + ")" : ""),
  comAncoraPosicao.length === 0);

// ---- (12) identificador pendurado em App.jsx --------------------------------
// Para cada nome, conta OCORRÊNCIAS fora da(s) linha(s) de DECLARAÇÃO
// (`const`/destructuring). Se há uso (contagem > 0), tem de haver pelo menos
// uma linha de declaração — senão é a classe de defeito que o plan-checker
// achou nesta fase (identificador livre em JSX, ReferenceError em render,
// que nem `vite build` nem guardião de string pegam).
function checaPenduradoOuDeclarado(nome, fonteLinhas) {
  const linhas = fonteLinhas.split("\n");
  const linhasDeclaracao = linhas.filter((l) =>
    new RegExp("\\b(const|let)\\b[^=]*\\b" + nome + "\\b").test(l)
    || new RegExp("\\{[^}]*:\\s*" + nome + "\\b").test(l) // destructuring com rename: { x: nome }
  );
  const totalOcorrencias = (fonteLinhas.match(new RegExp("\\b" + nome + "\\b", "g")) || []).length;
  const ocorrenciasForaDaDeclaracao = totalOcorrencias - linhasDeclaracao.reduce(
    (acc, l) => acc + (l.match(new RegExp("\\b" + nome + "\\b", "g")) || []).length, 0);
  return { usado: ocorrenciasForaDaDeclaracao > 0, declarado: linhasDeclaracao.length > 0 };
}
for (const nome of ["opcoesPorTicker", "opcoesCarregando", "opcoesFor"]) {
  const r = checaPenduradoOuDeclarado(nome, appSC);
  ok(`(identificador pendurado) ${nome}: se usado em App.jsx, também está declarado` +
     (r.usado && !r.declarado ? " — PENDURADO" : ""),
     !r.usado || r.declarado);
}

// ---- (13) [re-ancorado a] WR-01: nenhum dos dois consumidores afirma ------
//           "vazio" antes de a primeira busca terminar (32-REVIEW.md, quick
//           260916-cod)
const fatiaLinhaSC = semComentario(fatiaLinha);
ok("LinhaChamadaOpcoes (App.jsx) trata `!concluido` como carregando, na MESMA condição que `carregando` (ramo `carregando || !concluido`)",
  /\bcarregando\s*\|\|\s*!concluido\b/.test(fatiaLinhaSC));
const iCarregandoOuNaoConcluido = fatiaLinhaSC.indexOf("!concluido");
const iVazioLinhaChamada = fatiaLinhaSC.indexOf("top.length === 0");
ok("`!concluido` é checado ANTES do ramo de vazio (top.length === 0) dentro de LinhaChamadaOpcoes",
  iCarregandoOuNaoConcluido > -1 && iVazioLinhaChamada > -1 && iCarregandoOuNaoConcluido < iVazioLinhaChamada);

ok("CuradoriaEstruturas.jsx recebe `concluido` como prop (mesma fonte ctx.curadoria, D-03)",
  /function CuradoriaEstruturas\(\{[^}]*\bconcluido\b/.test(curadoriaSC));
ok("CuradoriaEstruturas.jsx combina `carregando || !concluido` (nunca só `carregando`) para decidir o ramo de vazio",
  /\bcarregando\s*\|\|\s*!concluido\b/.test(curadoriaSC));
const iNaoMedidoUsoCarregando = curadoriaSC.indexOf("top.length === 0 && naoMedido");
const iNaoMedidoUsoVazio = curadoriaSC.indexOf("top.length === 0 && !naoMedido && !erro");
ok("o ramo de vazio de CuradoriaEstruturas.jsx exige o estado combinado (naoMedido) resolvido, não só `!carregando`",
  iNaoMedidoUsoCarregando > -1 && iNaoMedidoUsoVazio > -1);

// Fase 39 (39-04/39-05, 2026-09-24): o fio de `concluido` passou a atravessar
// `AbaRecomendadas.jsx` em vez de `SecaoDescobrir.jsx` — `OpcoesScreen.jsx`
// passa `ctx.curadoria` INTEIRO (não `.concluido` avulso) para
// `AbaRecomendadas.jsx`, que repassa a mesma expressão de sempre
// (`!!(curadoria && curadoria.concluido)`) para `CuradoriaEstruturas` — a
// garantia WR-01 não muda, só onde o fio é lido.
ok("OpcoesScreen.jsx passa curadoria={ctx && ctx.curadoria} inteiro para AbaRecomendadas",
  /curadoria=\{ctx\s*&&\s*ctx\.curadoria\}/.test(telaSC));
ok("AbaRecomendadas.jsx repassa concluido={!!(curadoria && curadoria.concluido)} para CuradoriaEstruturas",
  /concluido=\{!!\(curadoria\s*&&\s*curadoria\.concluido\)\}/.test(abaRecomendadasSC));

// ---- (14) [re-ancorado a] REORG-07: curadoria.top/curadoria.meta são
// consumidos por REFERÊNCIA e por ÍNDICE — a seleção é do motor
// determinístico (opcoes_curadoria.rankear), nunca do front. Fase 39
// (39-05, 2026-09-24): a checagem agora cobre os dois arquivos novos
// (`AbaOportunidades.jsx` também tem acesso a `opcoesPorTicker`, o
// equivalente de "lista com posição de exibição" do lado do gate).
ok("AbaOportunidades.jsx NÃO usa .sort( no corpo",
  !abaOportunidadesSC.includes(".sort("));
ok("AbaOportunidades.jsx NÃO usa .reverse( no corpo",
  !abaOportunidadesSC.includes(".reverse("));
ok("AbaRecomendadas.jsx NÃO usa .sort( no corpo",
  !abaRecomendadasSC.includes(".sort("));
ok("AbaRecomendadas.jsx NÃO usa .reverse( no corpo",
  !abaRecomendadasSC.includes(".reverse("));

// ---- (15) princípios 3/4 do CLAUDE.md: carimbo de frescor derivado só do
// campo que a resposta já trouxe, NUNCA do relógio de quem está com a tela
// aberta — varredura de DIRETÓRIO, cobre os arquivos novos automaticamente.
const comRelogioDoCliente = arquivosOpcoesDirConsolidacao.filter((f) => {
  const src = semComentario(readFileSync(join(dirOpcoes, f), "utf8"));
  return /Date\.now\(\)|new Date\(/.test(src);
});
ok("nenhum arquivo de web/src/opcoes/ usa Date.now()/new Date( como fonte de carimbo"
  + (comRelogioDoCliente.length ? " (violam: " + comRelogioDoCliente.join(", ") + ")" : ""),
  comRelogioDoCliente.length === 0);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
