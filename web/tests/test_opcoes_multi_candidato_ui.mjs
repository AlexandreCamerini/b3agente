// Fase 19 (Plano 03, MULTI-02) — Guardião estático do ramo de N candidatos
// dentro do detalhe da posição em Posições (`CandidatoOpcao` +
// `PropostaDaPosicao`).
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
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond, detail) => { console.log((cond ? "ok " : "FALHOU ") + name + (detail !== undefined ? ` (${detail})` : "")); if (!cond) fails++; };

// Filtra linhas de comentário ANTES de contar — mesma higiene de
// test_carteira_opcoes_tira.mjs:39-45: uma asserção que CONTA ocorrências
// (não apenas testa presença) precisa ignorar linhas que começam com `//`,
// senão o próprio comentário explicativo (deste arquivo ou de App.jsx)
// infla a contagem e auto-invalida o guardião.
const linhasSemComentario = app.split("\n").filter((l) => !/^\s*\/\//.test(l));
const fonteSemComentario = linhasSemComentario.join("\n");

// ---- (1) CandidatoOpcao está na fatia certa --------------------------------
const iPDP = app.indexOf("function PropostaDaPosicao");
const iCO = app.indexOf("function CandidatoOpcao");
const iHook = app.indexOf("function useOpcoesPropostas");
ok("function PropostaDaPosicao localizada", iPDP > -1);
ok("function CandidatoOpcao localizada", iCO > -1);
ok("function useOpcoesPropostas localizada", iHook > -1);
ok("CandidatoOpcao está ENTRE PropostaDaPosicao e useOpcoesPropostas",
  iPDP > -1 && iCO > iPDP && iHook > iCO);

const fatiaPDP = iPDP > -1 && iHook > iPDP ? app.slice(iPDP, iHook) : "";
const fatiaCO = iCO > -1 && iHook > iCO ? app.slice(iCO, iHook) : "";

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
ok("<PropostaLastreada aparece exatamente 2x no fonte inteiro (o ramo multi não virou um 3º ponto de uso)",
  (fonteSemComentario.match(/<PropostaLastreada/g) || []).length === 2,
  String((fonteSemComentario.match(/<PropostaLastreada/g) || []).length));

// ---- (10) Caminho de aceite único, compartilhado pelos candidatos ----------
ok("CandidatoOpcao é renderizado com onAceitar={aceitarCandidato} (o MESMO handler para todos os candidatos)",
  /onAceitar=\{aceitarCandidato\}/.test(fatiaPDP));
ok("PropostaDaPosicao declara `const aceitarCandidato = async (p) =>` (handler único, parametrizado)",
  /const aceitarCandidato = async \(p\) => \{/.test(fatiaPDP));

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

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
