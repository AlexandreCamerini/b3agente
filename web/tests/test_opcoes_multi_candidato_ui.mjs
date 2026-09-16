// Fase 19 (Plano 03, MULTI-02) — Guardião estático do ramo de N candidatos
// dentro do detalhe da posição em Posições (`CandidatoOpcao` +
// `PropostaDaPosicao`).
//
// 2026-09-15, Fase 32 (32-02): `CandidatoOpcao` saiu de App.jsx para
// web/src/opcoes/CandidatoOpcao.jsx (ADR-027 Emenda 3). A âncora de
// DEFINIÇÃO passa a apontar para o módulo; `PropostaDaPosicao` e a âncora de
// USO (`<CandidatoOpcao`, dentro de PropostaDaPosicao) continuam em App.jsx.
//
// Este arquivo tranca a CLASSE de erros que um edito futuro poderia
// reintroduzir, não a instância — cada bloco abaixo defende uma regra que o
// autor de uma edição futura em App.jsx não tem por que conhecer de cor:
//
//   1. `CandidatoOpcao` existe e cai na fatia certa do arquivo (entre
//      PropostaDaPosicao e useOpcoesPropostas) — o mesmo lugar que
//      test_carteira_opcoes_tira.mjs já inspeciona;
//   2. a manchete de cada candidato vem SÓ do motor determinístico
//      (guardrail CVM, CLAUDE.md) — nunca concatenada;
//   3. a cor da manchete nunca usa T.accent (regra de polaridade já em
//      produção desde a Fase 14/18);
//   4. campo não aplicável nunca vira "R$ 0,00" (regra null-nunca-zero
//      aplicada à UI, `typeof v === "number"` antes de multiplicar);
//   5. breakeven é preço do ativo, nunca valor de lote (não multiplica por
//      qtyAcoes);
//   6. Modo Estudo nunca ganha botão de executar (defesa em UI, T-14-23);
//   7. o busy compartilhado da posição desabilita TODOS os candidatos
//      irmãos (19-UI-SPEC.md, Decisão de Interação 1);
//   8. o ramo de N candidatos só existe quando há mais de um, e o ramo de
//      um candidato só continua caindo no card de hoje (PropostaLastreada);
//   9. `<PropostaLastreada` continua em exatamente 2 pontos de uso — repete
//      o guardião da Fase 18 aqui de propósito: é a regra que impede o ramo
//      multi de virar um terceiro ponto de uso;
//   10. os candidatos compartilham um único caminho de aceite
//       (`aceitarCandidato`), não um handler por componente;
//   11. nenhuma chave de copy nova — toda `cp.X` referenciada dentro de
//       CandidatoOpcao já existe em COPY.estudo e COPY.operador;
//   12. nenhuma composição de frase proibida no fonte inteiro (guardiões
//       globais da Fase 14, repetidos aqui por precaução).
//
// Padrão "static source inspection" da casa (mesmo de
// test_carteira_opcoes_tira.mjs, test_opcoes_collar_ui.mjs,
// test_opcoes_proposta_ui.mjs): readFileSync de App.jsx + import de COPY,
// sem build e sem DOM. Roda isolado: `node web/tests/test_opcoes_multi_candidato_ui.mjs`.
import { readFileSync, readdirSync, statSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
// ATUALIZADO 2026-09-13 (Fase 28, 28-01): `aceitarCandidato` saiu de App.jsx
// (PropostaDaPosicao) e virou `useAceiteLastreado`, em
// web/src/opcoes/PropostaLastreada.jsx.
const modulo = readFileSync(join(here, "..", "src", "opcoes", "PropostaLastreada.jsx"), "utf8");
// ATUALIZADO 2026-09-15 (Fase 32, 32-02): `CandidatoOpcao` saiu de App.jsx
// para web/src/opcoes/CandidatoOpcao.jsx (ADR-027 Emenda 3). A âncora de
// DEFINIÇÃO passa a apontar para o módulo; PropostaDaPosicao (o chamador) e
// a âncora de USO continuam em App.jsx.
const moduloCO = readFileSync(join(here, "..", "src", "opcoes", "CandidatoOpcao.jsx"), "utf8");

let fails = 0;
const ok = (name, cond, detail) => { console.log((cond ? "ok " : "FALHOU ") + name + (detail !== undefined ? ` (${detail})` : "")); if (!cond) fails++; };

// Filtra linhas de comentário ANTES de contar — mesma higiene de
// test_carteira_opcoes_tira.mjs:39-45: uma asserção que CONTA ocorrências
// (não apenas testa presença) precisa ignorar linhas que começam com `//`,
// senão o próprio comentário explicativo (deste arquivo ou de App.jsx)
// infla a contagem e auto-invalida o guardião.
const linhasSemComentario = app.split("\n").filter((l) => !/^\s*\/\//.test(l));
const fonteSemComentario = linhasSemComentario.join("\n");

// ---- (1) CandidatoOpcao é importado por App.jsx e não reimplementado -----
// ATUALIZADO 2026-09-15 (Fase 32, 32-02): "CandidatoOpcao está ENTRE
// PropostaDaPosicao e useOpcoesPropostas" perdeu o sentido — o componente
// saiu de App.jsx. Regra equivalente em espírito: CandidatoOpcao é
// IMPORTADO por App.jsx e não é reimplementado em nenhum outro .jsx de
// web/src/ (contagem de `function CandidatoOpcao`/`export default function
// CandidatoOpcao` no diretório inteiro igual a 1).
// ATUALIZADO 2026-09-15 (Fase 32, 32-03, deviation — Rule 1, guardião
// colateral fora de files_modified): a DEFINIÇÃO de `useOpcoesPropostas`
// também saiu de App.jsx (para ./opcoes/useOpcoesPropostas.js) — a âncora
// `function useOpcoesPropostas` não existe mais no arquivo, e usá-la como
// fim de fatia produzia `iHook === -1` e `fatiaPDP === ""` (mudo, não
// vazio-e-correto), fazendo as regras que dependem de `fatiaPDP` passarem
// por vacuidade ou falharem por ausência de conteúdo. A próxima função
// declarada em App.jsx depois de PropostaDaPosicao passou a ser
// `useCuradoria` (32-02) — usada como novo limite.
const iPDP = app.indexOf("function PropostaDaPosicao");
const iHookCur = app.indexOf("function useCuradoria");
ok("function PropostaDaPosicao localizada", iPDP > -1);
ok("function CandidatoOpcao localizada (no módulo)", moduloCO.includes("export default function CandidatoOpcao"));
ok("(Fase 32/32-03) function useOpcoesPropostas NÃO existe mais em App.jsx (definição saiu para o módulo)",
  !fonteSemComentario.includes("function useOpcoesPropostas"));
ok("(Fase 32/32-03) function useCuradoria localizada (novo limite de fatia de PropostaDaPosicao)", iHookCur > -1);
ok("App.jsx importa CandidatoOpcao de ./opcoes/CandidatoOpcao.jsx",
  /from\s+"\.\/opcoes\/CandidatoOpcao\.jsx"/.test(app));
ok("App.jsx NÃO define mais function CandidatoOpcao",
  !fonteSemComentario.includes("function CandidatoOpcao"));
ok("CandidatoOpcao.jsx NÃO importa App.jsx (seria ciclo)",
  !/from\s+"[^"]*App\.jsx"/.test(moduloCO));

const fatiaPDP = iPDP > -1 && iHookCur > iPDP ? app.slice(iPDP, iHookCur) : "";
ok("(Fase 32/32-03) fatiaPDP não é vazia (parse mudo — sem isto, as regras abaixo passariam por vacuidade)",
  fatiaPDP.length > 100);
// A "fatia" de CandidatoOpcao agora É o módulo inteiro (sem comentários,
// mesma higiene do resto do arquivo) — substitui o antigo
// `app.slice(iCO, iHook)`.
const fatiaCO = moduloCO.split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

// ---- (2) Guardrail CVM: manchete verbatim, nunca concatenada ---------------
ok("CandidatoOpcao renderiza {p.manchete} direto (sem composição)",
  /\{p\.manchete\}/.test(fatiaCO));
ok('CandidatoOpcao NÃO concatena manchete (regex "p.manchete ... +")',
  !/p\.manchete[^}]*\+/.test(fatiaCO));
ok('CandidatoOpcao NÃO concatena manchete (regex "+ ... p.manchete")',
  !/\+[^{]*p\.manchete/.test(fatiaCO));

// ---- (3) Cor da manchete nunca T.accent ------------------------------------
const linhaMancheteCO = (fatiaCO.match(/^.*\{p\.manchete\}.*$/m) || [""])[0];
ok("a linha que renderiza {p.manchete} tem conteúdo (parse mudo)", linhaMancheteCO.length > 0);
ok("a linha que renderiza {p.manchete} NÃO usa T.accent",
  linhaMancheteCO.length > 0 && !linhaMancheteCO.includes("T.accent"));
ok("CandidatoOpcao usa T.positive/T.negative para a cor da manchete",
  /const cor = isCall \? T\.positive : T\.negative;/.test(fatiaCO));

// ---- (4) Null-nunca-zero: helper antes de multiplicar por qtyAcoes ---------
ok('CandidatoOpcao tem o helper `typeof v === "number"` antes de multiplicar por qtyAcoes',
  /typeof v === "number"/.test(fatiaCO));
ok("CandidatoOpcao NÃO multiplica est.ganho_maximo diretamente (sem o helper)",
  !/est\.ganho_maximo \*/.test(fatiaCO));
ok("CandidatoOpcao NÃO multiplica est.perda_maxima diretamente (sem o helper)",
  !/est\.perda_maxima \*/.test(fatiaCO));

// ---- (5) Breakeven é preço do ativo, não valor de lote ---------------------
const linhaBreakeven = (fatiaCO.match(/^.*breakevens.*$/m) || [""])[0];
ok("linha que renderiza breakevens localizada em CandidatoOpcao", linhaBreakeven.length > 0);
ok("a linha que renderiza breakevens NÃO contém qtyAcoes",
  linhaBreakeven.length > 0 && !linhaBreakeven.includes("qtyAcoes"));

// ---- (6) Modo Estudo nunca ganha botão de executar -------------------------
ok("CandidatoOpcao condiciona o botão de CTA a `operador`",
  /\{operador && \(/.test(fatiaCO));
ok("CandidatoOpcao condiciona a frase didática a `!operador`",
  /\{!operador && \(/.test(fatiaCO));
ok("o botão de CTA vem DEPOIS da guarda `{operador && (` (não antes)",
  fatiaCO.indexOf("{operador && (") < fatiaCO.indexOf("<button"));

// ---- (7) Busy compartilhado desabilita todos os candidatos irmãos ---------
ok("CandidatoOpcao usa disabled={busy || degradado} no CTA",
  /disabled=\{busy \|\| degradado\}/.test(fatiaCO));

// ---- (8) Ramo multi só existe com mais de um candidato ---------------------
ok("PropostaDaPosicao deriva `multi` a partir de candidatos.length > 1",
  /candidatos\.length > 1/.test(fatiaPDP));
ok("PropostaDaPosicao continua renderizando PropostaLastreada no ramo de candidato único",
  /<PropostaLastreada/.test(fatiaPDP));

// ---- (9) <PropostaLastreada em exatamente 2 pontos de uso (Fase 18, reafirmado) ----
// ATUALIZADO 2026-09-13 (Fase 28, 28-03): o segundo ponto de uso não é mais
// AtivoCard/Watchlist — foi removido (28-CONTEXT D1). O teto de 2 continua
// sendo a regra (um terceiro ponto é a duplicação de EXPERIÊNCIA que a Fase
// 28 existiu para fechar), só que os dois pontos agora moram em ARQUIVOS
// diferentes: App.jsx (PropostaDaPosicao) e OpcoesScreen.jsx (SubAbaOperar).
// Varre web/src/**/*.jsx e afirma que SÓ esses dois arquivos têm a tag.
function listarJsxRecursivo(dir) {
  const out = [];
  for (const nome of readdirSync(dir)) {
    const caminho = join(dir, nome);
    const st = statSync(caminho);
    if (st.isDirectory()) out.push(...listarJsxRecursivo(caminho));
    else if (nome.endsWith(".jsx")) out.push(caminho);
  }
  return out;
}

const srcDir = join(here, "..", "src");
const todosJsx = listarJsxRecursivo(srcDir);
const contagemPorArquivo = todosJsx.map((caminho) => {
  const conteudo = readFileSync(caminho, "utf8");
  const semComentario = conteudo.split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
  return { caminho, n: (semComentario.match(/<PropostaLastreada/g) || []).length };
}).filter((r) => r.n > 0);

const appJsxPath = join(here, "..", "src", "App.jsx");
const opcoesScreenPath = join(here, "..", "src", "opcoes", "OpcoesScreen.jsx");
ok("<PropostaLastreada aparece exatamente 1x em App.jsx (PropostaDaPosicao)",
  (fonteSemComentario.match(/<PropostaLastreada/g) || []).length === 1,
  String((fonteSemComentario.match(/<PropostaLastreada/g) || []).length));
const opcoesScreenSemComentario = readFileSync(opcoesScreenPath, "utf8").split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
ok("<PropostaLastreada aparece exatamente 1x em OpcoesScreen.jsx (SubAbaOperar)",
  (opcoesScreenSemComentario.match(/<PropostaLastreada/g) || []).length === 1,
  String((opcoesScreenSemComentario.match(/<PropostaLastreada/g) || []).length));
const outrosComTag = contagemPorArquivo.filter((r) => r.caminho !== appJsxPath && r.caminho !== opcoesScreenPath);
ok("nenhum outro .jsx de web/src/ usa <PropostaLastreada (teto de 2 pontos de uso, Fase 28 D1)",
  outrosComTag.length === 0, outrosComTag.map((r) => r.caminho + ":" + r.n).join(", "));
ok("total de pontos de uso de <PropostaLastreada em web/src/**/*.jsx é 2 (App.jsx + OpcoesScreen.jsx)",
  contagemPorArquivo.reduce((acc, r) => acc + r.n, 0) === 2,
  String(contagemPorArquivo.reduce((acc, r) => acc + r.n, 0)));

// ---- (1, continuação) `function CandidatoOpcao` existe em exatamente 1
// arquivo de web/src/**/*.jsx (Fase 32, 32-02: o módulo, nenhuma
// reimplementação em outro lugar) --------------------------------------
const contagemDefCandidatoOpcao = todosJsx.map((caminho) => {
  const conteudo = readFileSync(caminho, "utf8");
  const semComentario = conteudo.split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
  return { caminho, n: (semComentario.match(/function CandidatoOpcao/g) || []).length };
}).filter((r) => r.n > 0);
ok("(Fase 32) function CandidatoOpcao existe em exatamente 1 arquivo de web/src/**/*.jsx",
  contagemDefCandidatoOpcao.length === 1 && contagemDefCandidatoOpcao[0].caminho.endsWith(join("opcoes", "CandidatoOpcao.jsx")),
  contagemDefCandidatoOpcao.map((r) => r.caminho + ":" + r.n).join(", "));

// ---- (10) Caminho de aceite único, compartilhado pelos candidatos ----------
ok("CandidatoOpcao é renderizado com onAceitar={aceitarCandidato} (o MESMO handler para todos os candidatos)",
  /onAceitar=\{aceitarCandidato\}/.test(fatiaPDP));
// ATUALIZADO 2026-09-13 (Fase 28, 28-01): `aceitarCandidato` deixou de ser
// declarado LOCALMENTE em PropostaDaPosicao — agora vem do hook
// `useAceiteLastreado`, importado do módulo. O invariante ("handler único,
// compartilhado por todos os candidatos") passa a ser medido em três partes:
// (a) PropostaDaPosicao consome o hook; (b) a implementação é única, no
// módulo; (c) App.jsx não voltou a ter uma implementação própria.
ok("PropostaDaPosicao consome o hook useAceiteLastreado({ A, cp, ticker: t })",
  /useAceiteLastreado\(\{ A, cp, ticker: t \}\)/.test(fatiaPDP));
ok("o módulo declara `const aceitarCandidato = async (p) =>` exatamente 1× (implementação única)",
  (modulo.match(/const aceitarCandidato = async \(p\) => \{/g) || []).length === 1);
ok("App.jsx NÃO declara mais `const aceitarCandidato = async (p) =>` (a implementação está fora)",
  !/const aceitarCandidato = async \(p\) => \{/.test(app));

// ---- (11) Nenhuma chave de copy nova ---------------------------------------
const chavesCp = new Set();
const reCp = /\bcp\.([A-Za-z0-9_]+)/g;
let mCp;
while ((mCp = reCp.exec(fatiaCO))) chavesCp.add(mCp[1]);
ok("pelo menos uma chave cp.X referenciada em CandidatoOpcao (sanity)", chavesCp.size > 0, String(chavesCp.size));
let todasExistem = true;
for (const k of chavesCp) {
  if (!(k in COPY.estudo) || !(k in COPY.operador)) { todasExistem = false; break; }
}
ok("toda cp.X referenciada em CandidatoOpcao existe em COPY.estudo e COPY.operador (nenhuma chave nova)",
  todasExistem, [...chavesCp].join(", "));

// ---- (12) Composição de frase proibida (guardiões globais da Fase 14) -----
ok('fonte inteiro NÃO compõe "Vender " + (manchete/didática do motor)',
  !/"Vender " \+/.test(fonteSemComentario));
ok('fonte inteiro NÃO contém "Se você tivesse" (didática do motor, nunca duplicada em copy.js/App.jsx)',
  !fonteSemComentario.includes("Se você tivesse"));
// ATUALIZADO 2026-09-13 (Fase 28, 28-01): as mesmas duas proibições, agora
// também sobre o módulo extraído — a proibição segue o código.
ok('módulo NÃO compõe "Vender " + (manchete/didática do motor)',
  !/"Vender " \+/.test(modulo));
ok('módulo NÃO contém "Se você tivesse" (didática do motor, nunca duplicada)',
  !modulo.includes("Se você tivesse"));
// ATUALIZADO 2026-09-15 (Fase 32, 32-02): as mesmas duas proibições, agora
// também sobre CandidatoOpcao.jsx — a proibição segue o código onde quer
// que ele more.
ok('CandidatoOpcao.jsx NÃO compõe "Vender " + (manchete/didática do motor)',
  !/"Vender " \+/.test(moduloCO));
ok('CandidatoOpcao.jsx NÃO contém "Se você tivesse" (didática do motor, nunca duplicada)',
  !moduloCO.includes("Se você tivesse"));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
