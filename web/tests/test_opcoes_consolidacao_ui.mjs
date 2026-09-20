// Fase 32 (32-03, 2026-09-15) — Guardião DEDICADO da consolidação das
// operações de opções na aba Opções. Reprova a volta dos dois blocos
// cross-carteira para Posições e a perda da frase-ponte obrigatória (D-05).
//
// Contexto: os blocos "Oportunidades de opções" (motor COM gate) e "as 4
// melhores oportunidades de opções" (motor SEM gate) migraram de
// CarteiraScreen (App.jsx) para o topo da sub-aba Setups da aba Opções
// (OpcoesScreen.jsx) — D-04/D-07. Posições ganhou uma linha de chamada
// única, com contagem lida da MESMA fonte que alimenta a lista (D-03).
//
// Cada regra abaixo defende um requisito específico do 32-UI-SPEC.md/
// 32-03-PLAN.md, por leitura estática de source (sem build, sem DOM):
//
//  1. ordem no ramo `setups`: <SecaoDescobrir < <SecaoVigias em
//     OpcoesScreen.jsx (Fase 33/33-02: fraseDuasLeituras/blocoOportunidades/
//     blocoCuradoria saíram — os três viraram um componente só,
//     SecaoDescobrir.jsx), e DENTRO de SecaoDescobrir.jsx a ordem interna
//     duasLeiturasIntro < <OportunidadesOpcoes < <CuradoriaEstruturas
//     (Fase 33/33-01 já tinha trocado {blocoVigias} por <SecaoVigias);
//  2. a frase-ponte (D-05) é incondicional — nunca colapsável;
//  3. App.jsx não contém <OportunidadesOpcoes nem <CuradoriaEstruturas;
//  4. App.jsx contém <LinhaChamadaOpcoes exatamente 1x (D-01);
//  5. LinhaChamadaOpcoes referencia os 4 estados e chama
//     linhaChamadaOpcoesTexto( exatamente 1x (D-03, origem única da contagem);
//  6. LinhaChamadaOpcoes não recalcula contagem (sem .filter(/.reduce(/positions);
//  7. navegação (D-02): onIr resolve para ctx.goOpcoes, que é navigate("opcoes"),
//     sem parâmetro de ticker/candidato (sem deep-link);
//  8. D-06: nenhum sticky/fixed nem <input de busca entre a frase-ponte e os
//     vigias (Fase 33/33-02: medido sobre SecaoDescobrir.jsx inteiro + o
//     trecho de OpcoesScreen.jsx entre <SecaoDescobrir e <SecaoVigias);
//  9. regressão do collar curado: onExecutar liga a ctx.A.executarCandidatoCurado
//     exatamente 1x, somando OpcoesScreen.jsx + SecaoDescobrir.jsx (Fase
//     33/33-02: o fio pode ficar em qualquer um dos dois, nunca nos dois);
//     executarCandidato.js continua despachando optionsCuradoriaAbrirCollar
//     para tipo === "collar"; nenhum store./api. dentro de
//     CuradoriaEstruturas.jsx;
//  10. estado de erro do Bloco B: CuradoriaEstruturas.jsx referencia
//      cp.curadoriaErroBusca e o ramo de cp.curadoriaVazio exige !erro;
//  11. Pitfall 4: nenhum arquivo de web/src/opcoes/ contém scrollIntoView
//      nem a âncora "posicao-" (Fase 33/33-02: varredura de diretório,
//      cobre SecaoDescobrir.jsx e qualquer seção nova automaticamente);
//  12. identificador pendurado em App.jsx: opcoesPorTicker/opcoesCarregando/
//      opcoesFor só podem ser USADOS se também DECLARADOS — a classe de
//      defeito que este plano quase criou (ver 32-03-PLAN.md, achado do
//      plan-checker) e que nem `vite build` nem os outros guardiões de
//      string pegam.
//  13. WR-01 (32-REVIEW.md, quick 260916-cod, 2026-09-16): nem
//      LinhaChamadaOpcoes (App.jsx) nem CuradoriaEstruturas.jsx podem
//      afirmar "vazio" antes de a primeira busca de useCuradoria terminar —
//      os dois têm de tratar `!concluido` como "ainda carregando", na
//      MESMA condição que já trata `carregando`, e ANTES do ramo de vazio.
//      Fase 33 (33-02): OpcoesScreen.jsx passa `ctx.curadoria` INTEIRO para
//      SecaoDescobrir.jsx, que é quem agora repassa `concluido` para
//      CuradoriaEstruturas (mesma fonte, D-03).
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
// Fase 33 (33-02): a frase-ponte + Bloco A + Bloco B migraram para este
// arquivo novo — várias regras abaixo passam a medir ELE, não mais
// OpcoesScreen.jsx, para o que se moveu.
const secaoDescobrirModulo = readFileSync(join(dirOpcoes, "SecaoDescobrir.jsx"), "utf8");

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
const secaoDescobrirSC = semComentario(secaoDescobrirModulo);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- (1) ordem no ramo setups ---------------------------------------------
// 2026-09-20, Fase 33 (33-02): `{fraseDuasLeituras}`/`{blocoOportunidades}`/
// `{blocoCuradoria}` saíram de OpcoesScreen.jsx — os três viraram
// `<SecaoDescobrir` (componente único, SecaoDescobrir.jsx). A garantia de
// ORDEM se divide em duas, nenhuma mais fraca que a original: (a) em
// OpcoesScreen.jsx, `<SecaoDescobrir` vem antes de `<SecaoVigias`; (b)
// DENTRO de SecaoDescobrir.jsx, a frase-ponte (duasLeiturasIntro) vem antes
// do Bloco A (<OportunidadesOpcoes), que vem antes do Bloco B
// (<CuradoriaEstruturas) — mesma sequência de sempre, só em arquivo próprio.
const iSecaoDescobrirTela = telaSC.indexOf("<SecaoDescobrir");
const iVigias = telaSC.indexOf("<SecaoVigias");
ok("<SecaoDescobrir e <SecaoVigias foram localizados em OpcoesScreen.jsx",
  iSecaoDescobrirTela > -1 && iVigias > -1);
ok("ordem em OpcoesScreen.jsx: <SecaoDescobrir < <SecaoVigias",
  iSecaoDescobrirTela > -1 && iVigias > -1 && iSecaoDescobrirTela < iVigias);

const iFraseSD = secaoDescobrirSC.indexOf("duasLeiturasIntro");
const iBlocoASD = secaoDescobrirSC.indexOf("<OportunidadesOpcoes");
const iBlocoBSD = secaoDescobrirSC.indexOf("<CuradoriaEstruturas");
ok("os 3 marcadores foram localizados em SecaoDescobrir.jsx",
  iFraseSD > -1 && iBlocoASD > -1 && iBlocoBSD > -1);
ok("ordem em SecaoDescobrir.jsx: duasLeiturasIntro < <OportunidadesOpcoes < <CuradoriaEstruturas",
  iFraseSD > -1 && iFraseSD < iBlocoASD && iBlocoASD < iBlocoBSD);

// ---- (2) frase-ponte incondicional (D-05) ---------------------------------
// 2026-09-20, Fase 33 (33-02): a medição passa a ser em SecaoDescobrir.jsx
// (onde a frase-ponte agora vive). A frase não pode estar dentro de uma
// condição — ela é sempre montada e sempre no DOM. Verificação: nenhum
// aria-expanded/onClick no trecho onde o parágrafo é montado, e o USO (a
// linha com `{cp.duasLeiturasIntro}`) não está precedido de `&&` nem de `?`
// na mesma linha (ternário/curto-circuito inline).
const iDeclFrase = secaoDescobrirSC.indexOf("cp.duasLeiturasIntro");
const iDeclBlocoA = secaoDescobrirSC.indexOf("<OportunidadesOpcoes");
const trechoDeclFrase = (iDeclFrase > -1 && iDeclBlocoA > iDeclFrase) ? secaoDescobrirSC.slice(Math.max(0, iDeclFrase - 300), iDeclBlocoA) : "";
ok("a montagem de cp.duasLeiturasIntro foi localizada em SecaoDescobrir.jsx", trechoDeclFrase.length > 0);
ok("o trecho da frase-ponte NÃO tem aria-expanded (nunca colapsável)",
  !trechoDeclFrase.includes("aria-expanded"));
ok("o trecho da frase-ponte NÃO tem onClick (não é toggle)",
  !trechoDeclFrase.includes("onClick"));
const linhaUsoFrase = (secaoDescobrirSC.match(/^.*\{cp\.duasLeiturasIntro\}.*$/m) || [""])[0];
ok("o USO de {cp.duasLeiturasIntro} na árvore não depende de carteira.length/ticker/subaba/carregando (mesma linha)",
  linhaUsoFrase.length > 0
  && !/carteira\.length|ticker\s*&&|ticker\s*\?|subaba\s*&&|subaba\s*\?|carregando\s*&&|carregando\s*\?/.test(linhaUsoFrase)
  && linhaUsoFrase.trim() === "{cp.duasLeiturasIntro}"); // linha isolada, nenhuma condição envolvendo o marcador

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

// ---- (7) navegação sem deep-link (D-02) ------------------------------------
ok("App.jsx passa onIr={ctx.goOpcoes} para LinhaChamadaOpcoes",
  appSC.includes("onIr={ctx.goOpcoes}"));
ok("ctx.goOpcoes é definido como navigate(\"opcoes\") em App.jsx (sem parâmetro de ticker/candidato)",
  /goOpcoes:\s*\(\)\s*=>\s*navigate\("opcoes"\)/.test(appSC));

// ---- (8) D-06: nada impede busca depois -------------------------------------
// 2026-09-20, Fase 33 (33-02): o trecho "entre a frase-ponte e os vigias"
// agora atravessa DOIS arquivos — a frase-ponte + Bloco A + Bloco B moraram
// em SecaoDescobrir.jsx inteiro, e o que falta entre ele e os vigias é o
// trecho de OpcoesScreen.jsx entre `<SecaoDescobrir` e `<SecaoVigias`. A
// intenção (nada se intromete entre a desambiguação e os vigias) é a MESMA;
// só a fonte lida mudou de forma (um arquivo inteiro + um trecho, em vez de
// um trecho só).
const trechoAteVigiasTela = (iSecaoDescobrirTela > -1 && iVigias > iSecaoDescobrirTela)
  ? telaSC.slice(iSecaoDescobrirTela, iVigias) : "";
ok("trecho entre <SecaoDescobrir e <SecaoVigias em OpcoesScreen.jsx foi localizado",
  trechoAteVigiasTela.length > 0);
const trechoAteVigias = secaoDescobrirSC + "\n" + trechoAteVigiasTela;
ok('nenhum position: "sticky"/"fixed" entre a frase-ponte e os vigias',
  !/position:\s*["']?(sticky|fixed)/.test(trechoAteVigias));
ok("nenhum <input de busca/filtro entre a frase-ponte e os vigias",
  !/<input/.test(trechoAteVigias));

// ---- (9) regressão do collar curado ----------------------------------------
// 2026-09-20, Fase 33 (33-02): o fio pode ficar no orquestrador
// (OpcoesScreen.jsx) e descer por prop, ou ir para a seção
// (SecaoDescobrir.jsx) — o que não pode é existir nos DOIS ao mesmo tempo.
// Soma das duas fontes, exigindo exatamente 1x no total.
const nOnExecutar =
  (telaSC.match(/onExecutar=\{\(cand, o\) => ctx\.A\.executarCandidatoCurado\(cand, o\)\}/g) || []).length +
  (secaoDescobrirSC.match(/onExecutar=\{\(cand, o\) => ctx\.A\.executarCandidatoCurado\(cand, o\)\}/g) || []).length;
ok("onExecutar liga a ctx.A.executarCandidatoCurado exatamente 1x, somando OpcoesScreen.jsx + SecaoDescobrir.jsx",
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
// 2026-09-20, Fase 33 (33-02): convertido para varredura de DIRETÓRIO (D-02
// do 33-CONTEXT.md) — estende a proibição a SecaoDescobrir.jsx e a qualquer
// arquivo novo das próximas 33-03/04/05 sem precisar lembrar de atualizar
// esta lista de novo.
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

// ---- (13) WR-01: nenhum dos dois consumidores afirma "vazio" antes de ------
//           a primeira busca terminar (32-REVIEW.md, quick 260916-cod)
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

// 2026-09-20, Fase 33 (33-02): o fio de `concluido` passou a atravessar TRÊS
// pontos — OpcoesScreen.jsx passa `ctx.curadoria` INTEIRO (não mais
// `.concluido` avulso) para SecaoDescobrir.jsx, que é quem agora repassa
// `concluido={!!(curadoria && curadoria.concluido)}` para CuradoriaEstruturas
// (mesma fonte, D-03) — a garantia WR-01 não muda, só onde o fio é lido.
ok("OpcoesScreen.jsx passa curadoria={ctx.curadoria} inteiro para SecaoDescobrir",
  /curadoria=\{ctx\s*&&\s*ctx\.curadoria\}/.test(telaSC));
ok("SecaoDescobrir.jsx repassa concluido={!!(curadoria && curadoria.concluido)} para CuradoriaEstruturas",
  /concluido=\{!!\(curadoria\s*&&\s*curadoria\.concluido\)\}/.test(secaoDescobrirSC));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
