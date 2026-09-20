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
//  1. ordem no ramo `setups`: fraseDuasLeituras < blocoOportunidades <
//     blocoCuradoria < <SecaoVigias (Fase 33/33-01: o marcador migrou de
//     const para tag JSX — o bloco virou componente próprio);
//  2. a frase-ponte (D-05) é incondicional — nunca colapsável;
//  3. App.jsx não contém <OportunidadesOpcoes nem <CuradoriaEstruturas;
//  4. App.jsx contém <LinhaChamadaOpcoes exatamente 1x (D-01);
//  5. LinhaChamadaOpcoes referencia os 4 estados e chama
//     linhaChamadaOpcoesTexto( exatamente 1x (D-03, origem única da contagem);
//  6. LinhaChamadaOpcoes não recalcula contagem (sem .filter(/.reduce(/positions);
//  7. navegação (D-02): onIr resolve para ctx.goOpcoes, que é navigate("opcoes"),
//     sem parâmetro de ticker/candidato (sem deep-link);
//  8. D-06: nenhum sticky/fixed nem <input de busca entre a frase-ponte e os
//     vigias;
//  9. regressão do collar curado: onExecutar liga a ctx.A.executarCandidatoCurado
//     exatamente 1x; executarCandidato.js continua despachando
//     optionsCuradoriaAbrirCollar para tipo === "collar"; nenhum store./api.
//     dentro de CuradoriaEstruturas.jsx;
//  10. estado de erro do Bloco B: CuradoriaEstruturas.jsx referencia
//      cp.curadoriaErroBusca e o ramo de cp.curadoriaVazio exige !erro;
//  11. Pitfall 4: nem CuradoriaEstruturas.jsx nem OpcoesScreen.jsx contêm
//      scrollIntoView nem a âncora "posicao-";
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
//      OpcoesScreen.jsx precisa repassar `concluido` de ctx.curadoria para
//      CuradoriaEstruturas (mesma fonte, D-03).
//
// Roda sem build: `node web/tests/test_opcoes_consolidacao_ui.mjs`.
import { readFileSync } from "fs";
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

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- (1) ordem no ramo setups ---------------------------------------------
// 2026-09-19, Fase 33 (33-01): `{blocoVigias}` virou `<SecaoVigias` — o
// bloco migrou para componente próprio (D-01 do 33-CONTEXT.md). O marcador
// muda de forma (const → tag JSX); a relação de ORDEM que este guardião
// prova é a mesma.
const iFrase = telaSC.indexOf("{fraseDuasLeituras}");
const iBlocoA = telaSC.indexOf("{blocoOportunidades}");
const iBlocoB = telaSC.indexOf("{blocoCuradoria}");
const iVigias = telaSC.indexOf("<SecaoVigias");
ok("os 4 marcadores foram localizados em OpcoesScreen.jsx",
  iFrase > -1 && iBlocoA > -1 && iBlocoB > -1 && iVigias > -1);
ok("ordem: {fraseDuasLeituras} < {blocoOportunidades} < {blocoCuradoria} < <SecaoVigias",
  iFrase < iBlocoA && iBlocoA < iBlocoB && iBlocoB < iVigias);

// ---- (2) frase-ponte incondicional (D-05) ---------------------------------
// A CONST fraseDuasLeituras (onde ela é declarada) não pode estar dentro de
// uma condição — ela é sempre montada e sempre no DOM. Verificação: nenhum
// aria-expanded/onClick no trecho da declaração, e o USO ({fraseDuasLeituras})
// não está precedido de `&&` nem de `?` na mesma linha (ternário/curto-
// circuito inline).
const iDeclFrase = telaSC.indexOf("const fraseDuasLeituras");
const iDeclBlocoA = telaSC.indexOf("const blocoOportunidades");
const trechoDeclFrase = (iDeclFrase > -1 && iDeclBlocoA > iDeclFrase) ? telaSC.slice(iDeclFrase, iDeclBlocoA) : "";
ok("a declaração de fraseDuasLeituras foi localizada", trechoDeclFrase.length > 0);
ok("fraseDuasLeituras NÃO tem aria-expanded (nunca colapsável)",
  !trechoDeclFrase.includes("aria-expanded"));
ok("fraseDuasLeituras NÃO tem onClick (não é toggle)",
  !trechoDeclFrase.includes("onClick"));
const linhaUsoFrase = (telaSC.match(/^.*\{fraseDuasLeituras\}.*$/m) || [""])[0];
ok("o USO de {fraseDuasLeituras} na árvore não depende de carteira.length/ticker/subaba/carregando (mesma linha)",
  linhaUsoFrase.length > 0
  && !/carteira\.length|ticker\s*&&|ticker\s*\?|subaba\s*&&|subaba\s*\?|carregando\s*&&|carregando\s*\?/.test(linhaUsoFrase)
  && linhaUsoFrase.trim() === "{fraseDuasLeituras}"); // linha isolada, nenhuma condição envolvendo o marcador

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
const trechoAteVigias = (iFrase > -1 && iVigias > iFrase) ? telaSC.slice(iFrase, iVigias) : "";
ok("trecho entre a frase-ponte e os vigias foi localizado", trechoAteVigias.length > 0);
ok('nenhum position: "sticky"/"fixed" entre a frase-ponte e os vigias',
  !/position:\s*["']?(sticky|fixed)/.test(trechoAteVigias));
ok("nenhum <input de busca/filtro entre a frase-ponte e os vigias",
  !/<input/.test(trechoAteVigias));

// ---- (9) regressão do collar curado ----------------------------------------
ok("OpcoesScreen.jsx liga onExecutar a ctx.A.executarCandidatoCurado exatamente 1x",
  (telaSC.match(/onExecutar=\{\(cand, o\) => ctx\.A\.executarCandidatoCurado\(cand, o\)\}/g) || []).length === 1);
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
ok("CuradoriaEstruturas.jsx NÃO contém scrollIntoView",
  !curadoriaSC.includes("scrollIntoView"));
ok("CuradoriaEstruturas.jsx NÃO contém a âncora \"posicao-\"",
  !curadoriaSC.includes("posicao-"));
ok("OpcoesScreen.jsx NÃO contém scrollIntoView",
  !telaSC.includes("scrollIntoView"));
ok("OpcoesScreen.jsx NÃO contém a âncora \"posicao-\"",
  !telaSC.includes("posicao-"));

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

ok("OpcoesScreen.jsx repassa concluido={...ctx.curadoria.concluido} para CuradoriaEstruturas",
  /concluido=\{!!\(ctx\s*&&\s*ctx\.curadoria\s*&&\s*ctx\.curadoria\.concluido\)\}/.test(telaSC));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
