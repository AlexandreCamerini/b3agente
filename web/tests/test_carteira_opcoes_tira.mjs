// Fase 18 (Plano 04) — Guardião estático da tira "Oportunidades de opções"
// (NAV-01) e do detalhe por posição (NAV-02) em CarteiraScreen.
//
// Este arquivo tranca a CLASSE de erros que a Fase 18 pode reintroduzir, não
// a instância — cada bloco abaixo defende uma regra que o autor de uma
// edição futura em App.jsx não tem por que conhecer de cor:
//
//   1. manchete do card vem SÓ do motor determinístico (guardrail CVM,
//      CLAUDE.md) — o front nunca compõe/concatena/trunca a frase;
//   2. a tira agregada tem estado vazio OBRIGATÓRIO (NAV-03) — ao contrário
//      do card individual, que cala por desenho quando não há proposta
//      (ADR-004, App.jsx:3484-3489/inversão documentada no 18-03-SUMMARY);
//   3. a tira só aparece com carteira NÃO-vazia — duas mensagens pra mesma
//      ausência (tira vazia + portfólio vazio) seria ruído;
//   4. a busca de gate/proposta em useOpcoesPropostas é BEST-EFFORT — cada
//      chamada de rede tem `.catch(` no próprio encadeamento, nunca deixa
//      exceção não tratada travar a tira;
//   5. uma busca por ticker, não duas — a Fase 18 reusa o mesmo hook nas
//      duas superfícies (tira + detalhe), fetch duplicado na mesma tela é
//      regressão de custo;
//   6. estrutura só existe sobre POSIÇÃO REAL — useOpcoesPropostas é
//      chamado com `data.positions.map(`, nunca watchlist/radar.
//
// Padrão "static source inspection" da casa (mesmo de
// test_opcoes_proposta_ui.mjs, test_carteira_lastro_ui.mjs,
// test_fase5_appmode_fonte_unica.mjs): readFileSync de App.jsx + import de
// COPY, sem build e sem DOM. Roda isolado: `node web/tests/test_carteira_opcoes_tira.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Filtra linhas de comentário ANTES de contar — mesma higiene de
// test_fase5_appmode_fonte_unica.mjs:38-42: uma asserção que CONTA
// ocorrências (não apenas testa presença) precisa ignorar linhas que
// começam com `//`, senão o próprio comentário explicativo deste arquivo
// (ou de App.jsx) infla a contagem e auto-invalida o guardião.
const linhasSemComentario = app.split("\n").filter((l) => !/^\s*\/\//.test(l));
const fonteSemComentario = linhasSemComentario.join("\n");

// ---- (1) Copy nos dois ramos ---------------------------------------------
const CHAVES = [
  "tiraOpcoesTitulo", "tiraOpcoesVerDetalhe", "tiraOpcoesCarregando",
  "tiraOpcoesSemCobertura", "tiraOpcoesSemSetup", "linhaPropostaNaPosicao",
];
ok("6 chaves da tira existem em COPY.estudo e COPY.operador",
  CHAVES.every((k) => k in COPY.estudo) && CHAVES.every((k) => k in COPY.operador));
ok("todas as 6 chaves são string literal (não função)",
  CHAVES.every((k) => typeof COPY.estudo[k] === "string") && CHAVES.every((k) => typeof COPY.operador[k] === "string"));
ok("tiraOpcoesSemCobertura difere entre Estudo e Operador (voz de professor x voz de mesa)",
  COPY.estudo.tiraOpcoesSemCobertura !== COPY.operador.tiraOpcoesSemCobertura);
ok("tiraOpcoesSemSetup difere entre Estudo e Operador",
  COPY.estudo.tiraOpcoesSemSetup !== COPY.operador.tiraOpcoesSemSetup);
ok("dentro de Estudo, SemCobertura e SemSetup são frases distintas (dois motivos de NAV-03, não duplicados)",
  COPY.estudo.tiraOpcoesSemCobertura !== COPY.estudo.tiraOpcoesSemSetup);
ok("dentro de Operador, SemCobertura e SemSetup são frases distintas",
  COPY.operador.tiraOpcoesSemCobertura !== COPY.operador.tiraOpcoesSemSetup);

// ---- Âncoras de função usadas pelas fatias abaixo ------------------------
const iOO = app.indexOf("function OportunidadesOpcoes");
const iPDP = app.indexOf("function PropostaDaPosicao");
const iHook = app.indexOf("function useOpcoesPropostas");
const iCarteira = app.indexOf("function CarteiraScreen(");
const iHistorico = app.indexOf("function HistoricoScreen(");
ok("as 5 âncoras de função da Fase 18 foram localizadas, na ordem esperada",
  iOO > -1 && iPDP > iOO && iHook > iPDP && iCarteira > iHook && iHistorico > iCarteira);

const fatiaOO = app.slice(iOO, iPDP);
const fatiaPDP = app.slice(iPDP, iHook);
const fatiaCarteira = app.slice(iCarteira, iHistorico);

// ---- (2) Guardrail CVM na tira --------------------------------------------
ok("OportunidadesOpcoes renderiza {pr.manchete} direto (sem composição)",
  /\{pr\.manchete\}/.test(fatiaOO));
ok("OportunidadesOpcoes NÃO usa template string envolvendo manchete",
  !/`[^`]*\$\{[^}]*manchete/.test(fatiaOO));
ok("OportunidadesOpcoes NÃO concatena manchete (regex `manchete...+`)",
  !/manchete[^}]*\+/.test(fatiaOO));
ok('OportunidadesOpcoes NÃO compõe "Vender " +',
  !/"Vender " \+/.test(fatiaOO));
const linhaMancheteOO = (fatiaOO.match(/^.*\{pr\.manchete\}.*$/m) || [""])[0];
ok("a linha que renderiza a manchete não usa T.accent",
  linhaMancheteOO.length > 0 && !linhaMancheteOO.includes("T.accent"));

// ---- (3) Estado vazio de NAV-03 presente e explícito ----------------------
ok("OportunidadesOpcoes referencia cp.tiraOpcoesSemCobertura",
  fatiaOO.includes("cp.tiraOpcoesSemCobertura"));
ok("OportunidadesOpcoes referencia cp.tiraOpcoesSemSetup",
  fatiaOO.includes("cp.tiraOpcoesSemSetup"));
ok("OportunidadesOpcoes referencia cp.tiraOpcoesCarregando",
  fatiaOO.includes("cp.tiraOpcoesCarregando"));
ok("o ramo de carregando é avaliado ANTES do ramo vazio (a tira não mente durante a busca)",
  fatiaOO.indexOf("cp.tiraOpcoesCarregando") < fatiaOO.indexOf("cp.tiraOpcoesSemCobertura"));

// ---- (4) Tira ausente com carteira vazia ----------------------------------
const iTag = app.indexOf("<OportunidadesOpcoes");
const iEmptyGuard = app.indexOf("{data.positions.length === 0 && (");
ok("<OportunidadesOpcoes aparece depois de function CarteiraScreen(",
  iTag > iCarteira);
ok("<OportunidadesOpcoes aparece antes da guarda de portfólio vazio",
  iTag > -1 && iEmptyGuard > -1 && iTag < iEmptyGuard);
const antesTag = app.slice(Math.max(0, iTag - 120), iTag);
ok("os 120 caracteres imediatamente anteriores a <OportunidadesOpcoes contêm data.positions.length > 0",
  antesTag.includes("data.positions.length > 0"));

// ---- (5) Estrutura só sobre posição real -----------------------------------
ok("useOpcoesPropostas( dentro de CarteiraScreen recebe data.positions.map( como argumento",
  /useOpcoesPropostas\(data\.positions\.map\(/.test(fatiaCarteira));
const linhaHookCall = (fatiaCarteira.match(/^.*useOpcoesPropostas\(.*$/m) || [""])[0];
ok("a chamada de useOpcoesPropostas não menciona watchlist nem radar",
  linhaHookCall.length > 0 && !/watchlist|radar/i.test(linhaHookCall));

// ---- (6) Best-effort preservado --------------------------------------------
// Em vez de uma janela fixa de caracteres (que quebra em falso quando uma
// chamada aninhada — aqui, store.optionsProposta dentro do .then de
// store.optionsGate — empurra o `.catch(` correspondente pra mais longe do
// que uma distância arbitrária cobriria), caminha o encadeamento real de
// .then/.catch/.finally por balanceamento de parênteses a partir de cada
// chamada e confirma que um `.catch(` aparece nesse encadeamento. Isso mede
// a mesma garantia (nenhuma chamada de rede sem tratamento de erro) sem
// depender de contagem de caracteres do texto-fonte.
function encadeamentoTemCatch(src, chamada) {
  const i = src.indexOf(chamada);
  if (i === -1) return { achou: false, temCatch: false };
  let depth = 0, j = i;
  for (; j < src.length; j++) {
    if (src[j] === "(") depth++;
    else if (src[j] === ")") { depth--; if (depth === 0) { j++; break; } }
  }
  let k = j, temCatch = false;
  while (true) {
    while (k < src.length && /\s/.test(src[k])) k++;
    if (src[k] !== ".") break;
    const m = src.slice(k).match(/^\.(then|catch|finally)\(/);
    if (!m) break;
    if (m[1] === "catch") temCatch = true;
    let d = 0, p = k + m[0].length - 1;
    for (; p < src.length; p++) {
      if (src[p] === "(") d++;
      else if (src[p] === ")") { d--; if (d === 0) { p++; break; } }
    }
    k = p;
  }
  return { achou: true, temCatch };
}
const fatiaHookSemComentario = fonteSemComentario.slice(
  fonteSemComentario.indexOf("function useOpcoesPropostas"),
  fonteSemComentario.indexOf("function CarteiraScreen(")
);
const rGate = encadeamentoTemCatch(fatiaHookSemComentario, "store.optionsGate(");
const rProp = encadeamentoTemCatch(fatiaHookSemComentario, "store.optionsProposta(");
ok("store.optionsGate( encontrado no corpo de useOpcoesPropostas", rGate.achou);
ok("o encadeamento de store.optionsGate( contém .catch(", rGate.temCatch);
ok("store.optionsProposta( encontrado no corpo de useOpcoesPropostas", rProp.achou);
ok("o encadeamento de store.optionsProposta( contém .catch(", rProp.temCatch);

// ---- (7) Uma busca por ticker, não duas ------------------------------------
ok("store.optionsGate( aparece exatamente 2x no fonte (AtivoCard + hook — não uma 3ª busca duplicada)",
  (fonteSemComentario.match(/store\.optionsGate\(/g) || []).length === 2);
ok("store.optionsProposta( aparece exatamente 2x no fonte (AtivoCard + hook)",
  (fonteSemComentario.match(/store\.optionsProposta\(/g) || []).length === 2);

// ---- (8) Silêncio deliberado do card individual ----------------------------
ok("PropostaDaPosicao tem guarda de retorno null quando não há proposta",
  /if \(!r \|\| !r\.proposta\) return null;/.test(fatiaPDP));
ok("PropostaDaPosicao NÃO referencia cp.tiraOpcoesSemCobertura (o vazio agregado não vaza pro card)",
  !fatiaPDP.includes("cp.tiraOpcoesSemCobertura"));
ok("PropostaDaPosicao NÃO referencia cp.tiraOpcoesSemSetup",
  !fatiaPDP.includes("cp.tiraOpcoesSemSetup"));

// ---- (9) Estado por ticker no padrão da casa --------------------------------
ok("CarteiraScreen declara const [opcoesFor, setOpcoesFor] = useState(null);",
  /const \[opcoesFor, setOpcoesFor\] = useState\(null\);/.test(fatiaCarteira));
ok("o laço de posições lê opcoesFor === p.t",
  /opcoesFor === p\.t/.test(fatiaCarteira));
ok("histFor === p.t segue presente (padrão copiado, não substituído)",
  /histFor === p\.t/.test(fatiaCarteira));
ok("editFor === p.t segue presente",
  /editFor === p\.t/.test(fatiaCarteira));

// ---- (10) Âncora de scroll ligada --------------------------------------------
ok('id={"posicao-" + p.t} presente no card de posição',
  app.includes('id={"posicao-" + p.t}'));
ok('getElementById("posicao-" + t) seguido de scrollIntoView( presente',
  /getElementById\("posicao-" \+ t\)[\s\S]{0,120}scrollIntoView\(/.test(app));
ok("abrirOpcoesDe chama setOpcoesFor(",
  /const abrirOpcoesDe = \(t\) => \{\s*setOpcoesFor\(/.test(fatiaCarteira));

// ---- (11) Assinatura de PropostaLastreada intocada ---------------------------
ok("assinatura de PropostaLastreada permanece { r, operador, cp, busy, onAbrir, onFechar, posAberta }",
  /function PropostaLastreada\(\{ r, operador, cp, busy, onAbrir, onFechar, posAberta \}\)/.test(app));
ok("<PropostaLastreada aparece 2x no fonte (AtivoCard + PropostaDaPosicao — a Fase 18 ADICIONOU um ponto, não moveu o existente)",
  (fonteSemComentario.match(/<PropostaLastreada/g) || []).length === 2);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
