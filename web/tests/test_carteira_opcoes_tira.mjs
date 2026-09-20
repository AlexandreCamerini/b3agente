// Fase 18 (Plano 04) — Guardião estático da tira "Oportunidades de opções"
// (NAV-01) e do detalhe por posição (NAV-02) em CarteiraScreen.
//
// 2026-09-15, Fase 32 (32-02): `OportunidadesOpcoes` saiu de App.jsx para
// web/src/opcoes/OportunidadesOpcoes.jsx (ADR-027 Emenda 3). A âncora de
// DEFINIÇÃO passa a apontar para o módulo; as âncoras de USO (call site em
// CarteiraScreen) continuam em App.jsx até o Plano 32-03.
//
// 2026-09-15, Fase 32 (32-03): o bloco cross-carteira mudou de TELA — de
// `CarteiraScreen` (`App.jsx`) para o topo da sub-aba Setups
// (`OpcoesScreen.jsx`, D-04/D-07). As âncoras de USO passam a apontar para
// lá; `App.jsx` não renderiza mais `<OportunidadesOpcoes` — Posições passa
// a ter uma linha de chamada (`LinhaChamadaOpcoes`) no lugar. A DEFINIÇÃO
// de `useOpcoesPropostas` também saiu de App.jsx (para
// ./opcoes/useOpcoesPropostas.js) — a chamada em CarteiraScreen sobrevive
// (PropostaDaPosicao ainda a consome, até o Plano 32-04), e OpcoesScreen.jsx
// ganha uma segunda chamada, sobre o mesmo universo (a carteira).
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
// ATUALIZADO 2026-09-13 (Fase 28, 28-01): PropostaLastreada saiu de App.jsx
// para web/src/opcoes/PropostaLastreada.jsx.
const modulo = readFileSync(join(here, "..", "src", "opcoes", "PropostaLastreada.jsx"), "utf8");
// ATUALIZADO 2026-09-15 (Fase 32, 32-02): OportunidadesOpcoes saiu de
// App.jsx para web/src/opcoes/OportunidadesOpcoes.jsx (ADR-027 Emenda 3). A
// âncora de DEFINIÇÃO passa a apontar para o módulo; as âncoras de USO
// (`<OportunidadesOpcoes`, `useOpcoesPropostas`, `CarteiraScreen`) continuam
// em App.jsx até o Plano 32-03.
const moduloOO = readFileSync(join(here, "..", "src", "opcoes", "OportunidadesOpcoes.jsx"), "utf8");
// Fase 32 (32-03): o call site (`<OportunidadesOpcoes`) mudou de tela, e a
// DEFINIÇÃO de useOpcoesPropostas saiu para seu próprio módulo.
const telaOpcoes = readFileSync(join(here, "..", "src", "opcoes", "OpcoesScreen.jsx"), "utf8");
const telaOpcoesSemComentario = telaOpcoes.split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const moduloUOP = readFileSync(join(here, "..", "src", "opcoes", "useOpcoesPropostas.js"), "utf8");
const moduloUOPSemComentario = moduloUOP.split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

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
// ATUALIZADO 2026-09-08 (quick 260908-ldg, G10): `tiraOpcoesSemMercado`
// entra na lista — terceiro caso do estado vazio (D-07), com as MESMAS
// asserções de distinção dos dois anteriores.
// ATUALIZADO 2026-09-15, Fase 32 (32-01): a tira ganhou `tiraOpcoesSubtitulo`
// porque os dois blocos cross-carteira passam a conviver na mesma tela e o
// título sozinho não diz mais qual motor é qual (D-05) — de 7 para 8 chaves.
const CHAVES = [
  "tiraOpcoesTitulo", "tiraOpcoesSubtitulo", "tiraOpcoesVerDetalhe", "tiraOpcoesCarregando",
  "tiraOpcoesSemCobertura", "tiraOpcoesSemSetup", "tiraOpcoesSemMercado", "linhaPropostaNaPosicao",
];
ok("8 chaves da tira existem em COPY.estudo e COPY.operador",
  CHAVES.every((k) => k in COPY.estudo) && CHAVES.every((k) => k in COPY.operador));
ok("todas as 8 chaves são string literal (não função)",
  CHAVES.every((k) => typeof COPY.estudo[k] === "string") && CHAVES.every((k) => typeof COPY.operador[k] === "string"));
ok("tiraOpcoesSemCobertura difere entre Estudo e Operador (voz de professor x voz de mesa)",
  COPY.estudo.tiraOpcoesSemCobertura !== COPY.operador.tiraOpcoesSemCobertura);
ok("tiraOpcoesSemSetup difere entre Estudo e Operador",
  COPY.estudo.tiraOpcoesSemSetup !== COPY.operador.tiraOpcoesSemSetup);
ok("tiraOpcoesSemMercado difere entre Estudo e Operador",
  COPY.estudo.tiraOpcoesSemMercado !== COPY.operador.tiraOpcoesSemMercado);
ok("dentro de Estudo, SemCobertura e SemSetup são frases distintas (dois motivos de NAV-03, não duplicados)",
  COPY.estudo.tiraOpcoesSemCobertura !== COPY.estudo.tiraOpcoesSemSetup);
ok("dentro de Operador, SemCobertura e SemSetup são frases distintas",
  COPY.operador.tiraOpcoesSemCobertura !== COPY.operador.tiraOpcoesSemSetup);
ok("dentro de Estudo, SemMercado ≠ SemCobertura e SemMercado ≠ SemSetup",
  COPY.estudo.tiraOpcoesSemMercado !== COPY.estudo.tiraOpcoesSemCobertura &&
  COPY.estudo.tiraOpcoesSemMercado !== COPY.estudo.tiraOpcoesSemSetup);
ok("dentro de Operador, SemMercado ≠ SemCobertura e SemMercado ≠ SemSetup",
  COPY.operador.tiraOpcoesSemMercado !== COPY.operador.tiraOpcoesSemCobertura &&
  COPY.operador.tiraOpcoesSemMercado !== COPY.operador.tiraOpcoesSemSetup);

// ---- Âncoras de função usadas pelas fatias abaixo ------------------------
// ATUALIZADO 2026-09-15 (Fase 32, 32-02): `OportunidadesOpcoes` saiu de
// App.jsx — restam PropostaDaPosicao < useOpcoesPropostas < CarteiraScreen <
// HistoricoScreen (4 âncoras, não mais 5).
// ATUALIZADO 2026-09-15 (Fase 32, 32-03): a DEFINIÇÃO de `useOpcoesPropostas`
// também saiu de App.jsx (para ./opcoes/useOpcoesPropostas.js) — só a
// CHAMADA sobrevive dentro de CarteiraScreen. Restam PropostaDaPosicao <
// CarteiraScreen < HistoricoScreen (3 âncoras).
// ATUALIZADO 2026-09-16 (Fase 32, 32-04, deviation Rule 1): `PropostaDaPosicao`
// foi REMOVIDA de App.jsx — o card de proposta por posição (com o ramo
// multi-candidato) foi portado para `SubAbaOperar`
// (web/src/opcoes/OpcoesScreen.jsx, D-04). Restam CarteiraScreen <
// HistoricoScreen (2 âncoras). As asserções que mediam `fatiaPDP` (silêncio
// deliberado do card, estado `opcoesFor`) saíram — o que elas guardavam
// agora é guardado por `test_opcoes_multi_candidato_ui.mjs` e
// `test_opcoes_subabas_ui.mjs`, sobre o novo local.
const iCarteira = app.indexOf("function CarteiraScreen(");
const iHistorico = app.indexOf("function HistoricoScreen(");
ok("(Fase 32/32-04) as 2 âncoras de função restantes em App.jsx foram localizadas, na ordem esperada",
  iCarteira > -1 && iHistorico > iCarteira);
ok("(Fase 32/32-03) function useOpcoesPropostas NÃO existe mais em App.jsx (definição saiu para o módulo)",
  !/function useOpcoesPropostas/.test(app.split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n")));
ok("(Fase 32/32-04) function PropostaDaPosicao NÃO existe mais em App.jsx (o card de proposta por posição migrou para SubAbaOperar)",
  !/function PropostaDaPosicao/.test(app.split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n")));

// A "fatia" de OportunidadesOpcoes agora É o módulo inteiro — substitui o
// antigo `app.slice(iOO, iPDP)`.
const fatiaOO = moduloOO;
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
ok("OportunidadesOpcoes referencia cp.tiraOpcoesSemMercado (quick 260908-ldg, D-07)",
  fatiaOO.includes("cp.tiraOpcoesSemMercado"));
ok("OportunidadesOpcoes referencia cp.tiraOpcoesCarregando",
  fatiaOO.includes("cp.tiraOpcoesCarregando"));
ok("o ramo de carregando é avaliado ANTES do ramo vazio (a tira não mente durante a busca)",
  fatiaOO.indexOf("cp.tiraOpcoesCarregando") < fatiaOO.indexOf("cp.tiraOpcoesSemCobertura"));

// ---- (4, Fase 32/32-03) Tira migrou para OpcoesScreen.jsx -----------------
// O call site (`<OportunidadesOpcoes`) e sua guarda de carteira vazia
// pertenciam a CarteiraScreen; agora o bloco vive no topo da sub-aba Setups
// de OpcoesScreen.jsx, e Posições fica com a linha de chamada (D-01).
ok("(Fase 32/32-03) <OportunidadesOpcoes aparece exatamente 1x no fonte de OpcoesScreen.jsx",
  (telaOpcoesSemComentario.match(/<OportunidadesOpcoes/g) || []).length === 1);
ok("(Fase 32/32-03) <OportunidadesOpcoes aparece 0x em App.jsx (call site saiu de CarteiraScreen)",
  (fonteSemComentario.match(/<OportunidadesOpcoes/g) || []).length === 0);
// 2026-09-19, Fase 33 (33-01): `{blocoVigias}` virou `<SecaoVigias` (o
// bloco migrou para componente próprio, D-01 do 33-CONTEXT.md) — o marcador
// muda de forma, a relação de ordem que este guardião prova é a mesma.
const iUsoOOTela = telaOpcoesSemComentario.indexOf("{blocoOportunidades}");
const iUsoVigiasTela = telaOpcoesSemComentario.indexOf("<SecaoVigias");
ok("(Fase 32/32-03) {blocoOportunidades} é usado antes de <SecaoVigias em OpcoesScreen.jsx",
  iUsoOOTela > -1 && iUsoVigiasTela > iUsoOOTela);
ok("(Fase 32/32-03) App.jsx contém <LinhaChamadaOpcoes exatamente 1x (D-01: substitui os dois blocos em Posições)",
  (fonteSemComentario.match(/<LinhaChamadaOpcoes/g) || []).length === 1);

// ---- (5) Estrutura só sobre posição real -----------------------------------
// ATUALIZADO (Fase 32/32-03): store passou a ser o 1º argumento (a DEFINIÇÃO
// saiu para o módulo) — dois chamadores agora, ambos sobre posição real:
// CarteiraScreen (data.positions) e OpcoesScreen.jsx (carteira, que é
// ctx.data.positions filtrado).
// ATUALIZADO 2026-09-16 (Fase 32, 32-04, deviation Rule 1): a chamada em
// CarteiraScreen foi REMOVIDA junto com `PropostaDaPosicao` (o único
// consumidor) — resta 1 chamador (OpcoesScreen.jsx). A asserção de
// CarteiraScreen vira negativa: a chamada não existe mais em App.jsx.
ok("(Fase 32/32-04) useOpcoesPropostas( NÃO aparece mais em App.jsx (o único chamador, CarteiraScreen, foi removido junto com PropostaDaPosicao)",
  !/useOpcoesPropostas\(/.test(fonteSemComentario));
ok("(Fase 32/32-03) useOpcoesPropostas( dentro de OpcoesScreen.jsx recebe (store, carteira.map( como argumentos",
  /useOpcoesPropostas\(store, carteira\.map\(/.test(telaOpcoesSemComentario));
const linhaHookCallTela = (telaOpcoesSemComentario.match(/^.*useOpcoesPropostas\(.*$/m) || [""])[0];
ok("(Fase 32/32-03) a chamada de useOpcoesPropostas em OpcoesScreen.jsx não menciona watchlist nem radar",
  linhaHookCallTela.length > 0 && !/watchlist|radar/i.test(linhaHookCallTela));

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
// ATUALIZADO (Fase 32/32-03): o corpo do hook não vive mais dentro de
// App.jsx — a fatia agora É o módulo inteiro (useOpcoesPropostas.js), mesmo
// padrão de fatiaOO acima (a "fatia" de um componente/hook extraído passa a
// ser o arquivo inteiro, não um slice de App.jsx).
const fatiaHookSemComentario = moduloUOPSemComentario;
const rGate = encadeamentoTemCatch(fatiaHookSemComentario, "store.optionsGate(");
const rProp = encadeamentoTemCatch(fatiaHookSemComentario, "store.optionsProposta(");
ok("store.optionsGate( encontrado no corpo de useOpcoesPropostas (módulo)", rGate.achou);
ok("o encadeamento de store.optionsGate( contém .catch(", rGate.temCatch);
ok("store.optionsProposta( encontrado no corpo de useOpcoesPropostas (módulo)", rProp.achou);
ok("o encadeamento de store.optionsProposta( contém .catch(", rProp.temCatch);

// ---- (7) Uma busca por ticker, não duas ------------------------------------
// ATUALIZADO (Fase 32/32-03): a DEFINIÇÃO do hook saiu de App.jsx — a
// contagem de 2x (AtivoCard + hook) no MESMO arquivo não se aplica mais.
// Agora: App.jsx tem só a chamada de AtivoCard (1x); o hook (a busca de
// verdade) mora sozinho no módulo (1x) — dois CHAMADORES do hook
// (CarteiraScreen + OpcoesScreen.jsx) continuam sendo UMA busca cada, via
// import da MESMA função, nunca uma reimplementação.
ok("(Fase 32/32-03) store.optionsGate( aparece exatamente 1x em App.jsx (só AtivoCard — a busca do hook saiu daqui)",
  (fonteSemComentario.match(/store\.optionsGate\(/g) || []).length === 1);
ok("(Fase 32/32-03) store.optionsProposta( aparece exatamente 1x em App.jsx (só AtivoCard)",
  (fonteSemComentario.match(/store\.optionsProposta\(/g) || []).length === 1);
ok("(Fase 32/32-03) store.optionsGate( aparece exatamente 1x em useOpcoesPropostas.js (não uma 3ª busca duplicada)",
  (moduloUOPSemComentario.match(/store\.optionsGate\(/g) || []).length === 1);
ok("(Fase 32/32-03) store.optionsProposta( aparece exatamente 1x em useOpcoesPropostas.js",
  (moduloUOPSemComentario.match(/store\.optionsProposta\(/g) || []).length === 1);
ok("(Fase 32/32-03) OpcoesScreen.jsx importa useOpcoesPropostas (não reimplementa o fan-out)",
  /from\s+"\.\/useOpcoesPropostas\.js"/.test(telaOpcoes));

// ---- (8, Fase 32/32-04) Silêncio deliberado do card individual — APOSENTADO
// `PropostaDaPosicao` (o card com a guarda `if (!r || !r.proposta) return
// null`, ADR-004) foi removida de App.jsx nesta fase. A guarda não foi
// PORTADA para `SubAbaOperar` porque deixou de fazer sentido no novo local:
// a sub-aba Operar mostra UMA posição selecionada por vez (nunca itera N
// posições), então o raciocínio original — "um aviso por card, repetido
// posição a posição, vira ruído" — não se aplica; lá, ausência de proposta
// já cai numa das cascatas existentes (`gate === null`/`!gate.liquida`),
// não em silêncio. Sem asserção equivalente aqui — não há mais o que medir
// nesta classe de regra em App.jsx.
ok("(Fase 32/32-04) function PropostaDaPosicao NÃO existe mais em App.jsx (redundante com a âncora acima, reafirmado aqui por ser o contexto histórico desta seção)",
  !/function PropostaDaPosicao/.test(fonteSemComentario));

// ---- (9, Fase 32/32-04) Estado por ticker no padrão da casa — APOSENTADO
// `opcoesFor`/`setOpcoesFor` (o estado "qual posição tem o detalhe aberto")
// foi removido de CarteiraScreen junto com `PropostaDaPosicao`, seu único
// consumidor. `histFor`/`editFor` continuam de pé — são de OUTRAS
// affordances do card de posição (histórico de análises, edição de
// stop/alvo), não tocadas por esta fase.
ok("(Fase 32/32-04) opcoesFor NÃO aparece mais em CarteiraScreen (estado removido junto com PropostaDaPosicao)",
  !/opcoesFor/.test(fatiaCarteira));
ok("histFor === p.t segue presente (padrão copiado, não substituído)",
  /histFor === p\.t/.test(fatiaCarteira));
ok("editFor === p.t segue presente",
  /editFor === p\.t/.test(fatiaCarteira));

// ---- (10, Fase 32/32-03) scroll-to-id aposentado, substituído por navegação
// A âncora `id={"posicao-" + p.t}` continua no card de posição (não é
// exigida por nenhum consumidor novo, mas removê-la é fora de escopo deste
// plano — não é usada por nada que quebre se ficar). `abrirOpcoesDe`
// (o scroll-to-id que a alimentava) foi REMOVIDO: o Pitfall 4 do
// 32-RESEARCH.md é exatamente isto — o elemento `#posicao-<t>` só existe
// em CarteiraScreen, então "ver posição" a partir da aba Opções não pode
// depender de scrollIntoView. A navegação de Posições para a aba Opções
// agora é `ctx.goOpcoes` (ver test_curadoria_ui.mjs/
// test_opcoes_consolidacao_ui.mjs).
ok('id={"posicao-" + p.t} presente no card de posição',
  app.includes('id={"posicao-" + p.t}'));
ok("(Fase 32/32-03) abrirOpcoesDe NÃO existe mais em App.jsx (scroll-to-id sem chamador nesta tela)",
  !fonteSemComentario.includes("abrirOpcoesDe"));
ok("(Fase 32/32-03) getElementById(\"posicao-\" + t) seguido de scrollIntoView( NÃO aparece mais em App.jsx",
  !/getElementById\("posicao-" \+ t\)[\s\S]{0,120}scrollIntoView\(/.test(app));

// ---- (11) Assinatura de PropostaLastreada ---------------------------
// ATUALIZADO 2026-09-08 (quick 260908-ldg): ganhou `onVerbeteLiquidez`
// (D-09) — guardião de igualdade exata continua, agora com o campo novo.
// ATUALIZADO 2026-09-13 (Fase 28, 28-01): a definição saiu de App.jsx para
// o módulo — a fonte da asserção muda, a exigência de assinatura exata não.
ok("assinatura de PropostaLastreada é { r, operador, cp, busy, onAbrir, onFechar, posAberta, onVerbeteLiquidez }",
  /function PropostaLastreada\(\{ r, operador, cp, busy, onAbrir, onFechar, posAberta, onVerbeteLiquidez \}\)/.test(modulo));
// ATUALIZADO 2026-09-13 (Fase 28, 28-03): o ponto de uso de AtivoCard foi
// REMOVIDO (28-CONTEXT D1) — Watchlist/Radar deixaram de abrir/fechar
// operação lastreada. Restava 1x em App.jsx (PropostaDaPosicao).
// ATUALIZADO 2026-09-16 (Fase 32, 32-04, deviation Rule 1): `PropostaDaPosicao`
// também foi removida — App.jsx não renderiza mais `<PropostaLastreada`
// nenhuma vez. O único ponto de uso restante (OpcoesScreen.jsx, sub-aba
// Operar) é medido cross-arquivo por test_opcoes_multi_candidato_ui.mjs
// item (9), não repetido aqui.
ok("(Fase 32/32-04) <PropostaLastreada aparece 0x no fonte de App.jsx (PropostaDaPosicao removida — único ponto de uso restante é OpcoesScreen.jsx)",
  (fonteSemComentario.match(/<PropostaLastreada/g) || []).length === 0);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
