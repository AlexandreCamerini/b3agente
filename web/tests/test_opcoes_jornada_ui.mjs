// Fase 35, plano 35-01 (2026-09-21) — guardião da jornada guiada do
// workspace da sub-aba "Setups" da aba Opções.
//
// Defeito que este arquivo fecha: (1) o portão de leitura paga ("Ler no
// serviço de opções") e o carril de pills (Analisar/Comparar/Setups salvos)
// não nomeavam etapa nenhuma — o usuário não via em que ponto da jornada
// estava nem o que faltava (JORN-01); (2) o convite de leitura paga
// aparecia incondicionalmente acima do carril MESMO quando a pill ativa era
// "Setups salvos", que nunca leu `temLeitura` — um portão sem porta
// bloqueando quem só queria ver/criar um setup salvo (JORN-03).
//
// Regra que este guardião trava, não só descreve: rótulo de progresso NUNCA
// vira disparador de chamada paga (NAV-05, §3.3 do ADR-027) e NUNCA numera
// Analisar/Comparar entre si como se fossem passos 2/3 de uma sequência que
// o produto não tem (princípio 5 do CLAUDE.md — não inventar número).
//
// Cada bloco abaixo nomeia o defeito que reprova:
//
//  1. **D-02, o gate por pill** — o convite de leitura paga tem de conter
//     `abaWorkspace !== "setups"`, exatamente 1x, e o ramo 4 da Fase 34 não
//     pode ter ganhado um quarto `abaWorkspace === "..."` por acidente.
//  2. **D-01, o rótulo do estágio 1** — a fatia de `blocoLeituraDoServico`
//     tem de conter `cp.opcoesPasso1de2` e o separador " · ".
//  3. **D-06, o metadado "leitura já feita"** — existe um ramo `temLeitura ?`
//     com `cp.opcoesLeituraJaFeita` dentro, e essa fatia NUNCA usa
//     `T.positive`/`T.negative` (par reservado a direção financeira) nem
//     celebração (emoji, "Pronto", "Parabéns") — é metadado, não festa.
//  4. **D-08, o rótulo do estágio 2 e a transição** — `cp.opcoesEscolhaTitulo`
//     e `cp.opcoesPasso2de2` aparecem 1x cada, ANTES de `{workspacePillRow}`
//     no arquivo (o rótulo do estágio precede o carril que ele nomeia); a
//     linha de transição usa o estilo `AJUDA` já existente, nenhum estilo
//     novo.
//  5. **Princípio 5 — nunca inventar uma 3ª etapa**: nenhuma forma "Passo 2
//     de 3"/"Passo 3 de 3"/`de 3"`/"etapa 3" pode aparecer em
//     `OpcoesScreen.jsx` nem nos valores das 7 chaves novas de `copy.js`.
//     Analisar e Comparar nunca são numeradas entre si.
//  6. **NAV-05 — trocar de aba/ver o rótulo não pode pagar**: a fatia do
//     Kicker do estágio 2 até `{workspacePillRow}` não contém nenhum
//     disparador de chamada paga.
//  7. **Anti-inércia do guardião da Fase 34** — `test_opcoes_hub_workspace_
//     ui.mjs` fatia `workspaceTopo` de `<WorkspaceHeader` até o PRIMEIRO
//     `);`; um `);` intermediário introduzido por esta fase truncaria essa
//     fatia e deixaria aquele guardião medindo um pedaço vazio sem reprovar.
//     Esta asserção recalcula a MESMA fatia e exige que ela ainda contenha
//     `{workspacePillRow}` — se um `);` novo cortasse antes, esta asserção
//     reprova primeiro.
//  8. **Paridade de copy** — as 7 chaves novas existem em `COPY.estudo` e
//     `COPY.operador`, nenhuma vazia, valor idêntico nos dois modos (decisão
//     registrada no plano 35-01: são metadado de progresso, categoria já
//     neutra no arquivo).
//  9. **`SecaoSetups.jsx` intocada** — JORN-03 é paridade ESTRUTURAL pelo
//     Kicker compartilhado acima do carril, não tratamento novo dentro da
//     seção; o arquivo não pode ganhar nenhuma das 7 chaves novas nem
//     referência a `temLeitura`.
//
// ---- Plano 35-02 (2026-09-21) — hierarquia visual dos 3 CTAs + marca de
// resultado. Blocos 10-18 abaixo, acrescentados ao guardião do 35-01:
//
// 10. **Varredura de tokens por DIRETÓRIO** — para cada .jsx de
//     web/src/opcoes/, todo `T.<nome>` referenciado no CÓDIGO (sem
//     comentário) tem de estar no array TOKENS do PRÓPRIO arquivo — token
//     fora do array vira `undefined` calado. Este é o bloco que teria pego
//     o T.bgPanel de SecaoVigias.jsx em 2026-09-20 (undefined desde a Fase
//     33, 33-01, achado só pela varredura desta fase).
// 11. **Fronteira D-04 (exatamente 3 CTAs)** — BOTAO_PRIMARIO só existe em
//     OpcoesScreen.jsx/SecaoAnalisar.jsx/SecaoComparar.jsx, 1 declaração +
//     1 uso em cada (2 ocorrências exatas do IDENTIFICADOR, não substring —
//     CUSTO_NO_BOTAO_PRIMARIO também contém a string "BOTAO_PRIMARIO", por
//     isso a contagem usa fronteira de identificador, não grep ingênuo).
// 12. **Os 3 usos são os 3 botões certos** — a fatia de <button> que contém
//     cp.opcoesLerNoServico/opcoesMontarEstrutura/opcoesVerPossibilidades
//     usa BOTAO_PRIMARIO; a prova pelo avesso, os botões de
//     opcoesVerCadeia/opcoesVerOperaveis (exploração opcional) NÃO usam.
// 13. **Identidade das cópias locais** — o preço da duplicação aceita
//     (35-CONTEXT.md, decisao_do_planner): as N cópias de cada uma das 4
//     constantes, normalizadas por espaço, têm de ser IDÊNTICAS entre
//     arquivos — divergência nomeia os arquivos que diferem.
// 14. **Cópia morta proibida** — nenhum arquivo declara uma das 4
//     constantes sem usá-la (contagem de ocorrências do identificador ≥ 2
//     sempre que a declaração existe).
// 15. **D-07, o par proibido** — nenhum dos 3 arquivos com BOTAO_PRIMARIO
//     contém, no CÓDIGO (sem comentário), #fff/#ffffff/"white"/color-mix(.
//     35-UI-SPEC.md mediu que os dois valores originalmente propostos
//     reprovam AA (branco literal: 2,90:1 Dark·Estudo, 2,10:1
//     Dark·Operador; color-mix(#fff 72%): 2,20:1-3,38:1 em todo tema
//     medido). O único valor permitido é T.onAccent.
// 16. **D-05** — o corpo de desabilitadoPrimario contém 0.55 e
//     cursor: "not-allowed", e NÃO contém display. Nos botões com estado
//     desabilitado, o spread é desabilitadoPrimario(, nunca desabilitado(.
// 17. **D-06, regra de cor e gate da marca** — as fatias de MARCA_RESULTADO
//     não contêm T.positive/T.negative; cada render é gateado por uma
//     condição que contém .length e NÃO contém .erro nem .carregando.
// 18. **JORN-03 parity, prova negativa estrutural** — SecaoSetups.jsx e
//     WorkspaceHeader.jsx continuam sem BOTAO_PRIMARIO, sem T.accent e sem
//     T.onAccent (a paridade das 3 pills é o Kicker compartilhado do plano
//     35-01, não botão novo dentro delas).
//
// Roda sem build: `node web/tests/test_opcoes_jornada_ui.mjs`.
import { readFileSync, readdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");

const opcoesScreenBruto = readFileSync(join(dirOpcoes, "OpcoesScreen.jsx"), "utf8");
const secaoSetupsBruto = readFileSync(join(dirOpcoes, "SecaoSetups.jsx"), "utf8");
const secaoAnalisarBruto = readFileSync(join(dirOpcoes, "SecaoAnalisar.jsx"), "utf8");
const secaoCompararBruto = readFileSync(join(dirOpcoes, "SecaoComparar.jsx"), "utf8");
const workspaceHeaderBruto = readFileSync(join(dirOpcoes, "WorkspaceHeader.jsx"), "utf8");

// Sem comentários: este plano ACRESCENTA comentários que citam `abaWorkspace`,
// `temLeitura` e nomes de chave para EXPLICAR as decisões (D-01/D-02/D-06/
// D-08) — contá-los junto do código faria o guardião se auto-invalidar.
// Mesmo padrão de `test_opcoes_hub_workspace_ui.mjs`/`test_opcoes_subabas_ui.mjs`.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

const opcoesScreen = semComentario(opcoesScreenBruto);
const secaoAnalisar = semComentario(secaoAnalisarBruto);
const secaoComparar = semComentario(secaoCompararBruto);
const secaoSetups = semComentario(secaoSetupsBruto);
const workspaceHeader = semComentario(workspaceHeaderBruto);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 0) parse mudo: um arquivo vazio faria toda negativa abaixo passar de
// graça, sem medir nada de verdade -------------------------------------------
ok("OpcoesScreen.jsx foi lido e tem corpo (>200 caracteres)",
   opcoesScreenBruto.length > 200);
ok("SecaoSetups.jsx foi lido e tem corpo (>200 caracteres)",
   secaoSetupsBruto.length > 200);

// ---- 1) D-02: gate por pill -------------------------------------------------
const ocorrenciasGateD02 = (opcoesScreen.match(/podePedirLeitura && abaWorkspace !== "setups"/g) || []).length;
ok("existe exatamente 1 ocorrência de `podePedirLeitura && abaWorkspace !== \"setups\"` (D-02)",
   ocorrenciasGateD02 === 1);
const comparacoesAbaWorkspace = opcoesScreen.match(/abaWorkspace === "(analisar|comparar|setups)"/g) || [];
ok("continuam existindo exatamente 3 comparações abaWorkspace === \"...\" no arquivo (o gate do ramo 4 da Fase 34 não ganhou um quarto ramo por acidente)",
   comparacoesAbaWorkspace.length === 3);

// ---- 2) D-01: rótulo do estágio 1, dentro de blocoLeituraDoServico ---------
const iBlocoLeituraInicio = opcoesScreen.indexOf("const blocoLeituraDoServico = (");
const iBlocoLeituraFim = iBlocoLeituraInicio >= 0
  ? opcoesScreen.indexOf(");", iBlocoLeituraInicio) : -1;
const blocoLeituraDoServicoSlice = (iBlocoLeituraInicio >= 0 && iBlocoLeituraFim > iBlocoLeituraInicio)
  ? opcoesScreen.slice(iBlocoLeituraInicio, iBlocoLeituraFim) : "";
ok("a fatia de blocoLeituraDoServico (const até o fechamento) foi localizada",
   blocoLeituraDoServicoSlice.length > 0);
ok("D-01: a fatia de blocoLeituraDoServico contém cp.opcoesPasso1de2 e o separador \" · \"",
   blocoLeituraDoServicoSlice.length > 0
   && /cp\.opcoesPasso1de2\b/.test(blocoLeituraDoServicoSlice)
   && blocoLeituraDoServicoSlice.includes(" · "));

// ---- 3) D-06: metadado "leitura já feita" -----------------------------------
// Isola o ramo `temLeitura ? (` (com parêntese — a forma do metadado, D-06)
// da linha de transição `temLeitura ? <div ...` (sem parêntese, D-08): as
// duas ternárias sobre `temLeitura` têm formas de abertura DIFERENTES no
// arquivo, então buscar pelo marcador com parêntese não ambiguía.
const iLeituraJaFeitaUso = opcoesScreen.indexOf("cp.opcoesLeituraJaFeita");
const iD06Inicio = iLeituraJaFeitaUso >= 0
  ? opcoesScreen.lastIndexOf("temLeitura ? (", iLeituraJaFeitaUso) : -1;
const iD06Fim = iD06Inicio >= 0 ? opcoesScreen.indexOf(": null}", iD06Inicio) : -1;
const blocoD06 = (iD06Inicio >= 0 && iD06Fim > iD06Inicio)
  ? opcoesScreen.slice(iD06Inicio, iD06Fim + ": null}".length) : "";
ok("existe um ramo temLeitura ? (...) contendo cp.opcoesLeituraJaFeita (D-06)",
   blocoD06.length > 0 && /cp\.opcoesLeituraJaFeita\b/.test(blocoD06));
ok("D-06: o ramo de \"leitura já feita\" NÃO usa T.positive/T.negative (par reservado a direção financeira)",
   blocoD06.length > 0 && !/T\.positive\b/.test(blocoD06) && !/T\.negative\b/.test(blocoD06));
ok("D-06: o ramo de \"leitura já feita\" não celebra (sem emoji de festa, \"Pronto\" ou \"Parabéns\")",
   blocoD06.length > 0 && !/🎉|✅|Pronto!|Parabéns/i.test(blocoD06));

// ---- 4) D-08: rótulo do estágio 2 + transição, na ordem certa --------------
const iEscolhaTitulo = opcoesScreen.indexOf("cp.opcoesEscolhaTitulo");
const iPasso2de2 = opcoesScreen.indexOf("cp.opcoesPasso2de2");
const iWorkspacePillRowUso = opcoesScreen.indexOf("{workspacePillRow}");
ok("cp.opcoesEscolhaTitulo aparece exatamente 1x",
   (opcoesScreen.match(/cp\.opcoesEscolhaTitulo\b/g) || []).length === 1);
ok("cp.opcoesPasso2de2 aparece exatamente 1x",
   (opcoesScreen.match(/cp\.opcoesPasso2de2\b/g) || []).length === 1);
ok("{workspacePillRow} foi localizado (sanidade da ordem abaixo)",
   iWorkspacePillRowUso >= 0);
ok("D-08: cp.opcoesEscolhaTitulo e cp.opcoesPasso2de2 aparecem ANTES de {workspacePillRow} (o rótulo do estágio precede o carril que ele nomeia)",
   iEscolhaTitulo >= 0 && iPasso2de2 >= 0 && iWorkspacePillRowUso >= 0
   && iEscolhaTitulo < iWorkspacePillRowUso && iPasso2de2 < iWorkspacePillRowUso);
ok("cp.opcoesLeituraConcluidaAjuda aparece exatamente 1x",
   (opcoesScreen.match(/cp\.opcoesLeituraConcluidaAjuda\b/g) || []).length === 1);
ok("D-08: a linha de transição está dentro de um ternário sobre temLeitura e usa o estilo AJUDA já existente (nenhum estilo novo)",
   /temLeitura \? <div style=\{AJUDA\}>\{cp\.opcoesLeituraConcluidaAjuda/.test(opcoesScreen));

// ---- 5) Princípio 5: nunca inventar uma 3ª etapa ----------------------------
const FORMAS_PROIBIDAS = /Passo 2 de 3|Passo 3 de 3|de 3"|etapa 3/i;
ok("OpcoesScreen.jsx não contém nenhuma forma que numere uma 3ª etapa (Analisar/Comparar nunca são numeradas entre si)",
   !FORMAS_PROIBIDAS.test(opcoesScreenBruto));
const CHAVES_NOVAS = [
  "opcoesPasso1de2", "opcoesPasso2de2", "opcoesEscolhaTitulo",
  "opcoesLeituraJaFeita", "opcoesLeituraConcluidaAjuda",
  "opcoesEstruturaMontada", "opcoesPossibilidadesVistas",
];
const valoresDasChavesNovas = CHAVES_NOVAS.flatMap((k) => [COPY.estudo[k], COPY.operador[k]]);
ok("nenhum valor das 7 chaves novas de copy.js numera uma 3ª etapa",
   valoresDasChavesNovas.every((v) => typeof v === "string" && !FORMAS_PROIBIDAS.test(v)));

// ---- 6) NAV-05: rótulo de progresso não pode virar disparador de chamada ---
const DISPARADORES_PROIBIDOS = /abrirLeitura|abrirCadeia|abrirOperaveis|montarProposta|verPossibilidades|atualizarVigias|compilarSetup|confirmarSetup/;
const iInicioEstagio2 = opcoesScreen.indexOf("<Kicker>{(cp.opcoesEscolhaTitulo");
const trechoEstagio2AtePillRow = (iInicioEstagio2 >= 0 && iWorkspacePillRowUso > iInicioEstagio2)
  ? opcoesScreen.slice(iInicioEstagio2, iWorkspacePillRowUso) : "";
ok("a fatia do Kicker do estágio 2 até {workspacePillRow} foi localizada",
   trechoEstagio2AtePillRow.length > 0);
ok("NAV-05: a fatia do estágio 2 (Kicker até o carril) não contém nenhum disparador de chamada paga",
   trechoEstagio2AtePillRow.length > 0 && !DISPARADORES_PROIBIDOS.test(trechoEstagio2AtePillRow));

// ---- 7) Anti-inércia do guardião da Fase 34 --------------------------------
// Recalcula a MESMA fatia que test_opcoes_hub_workspace_ui.mjs usa
// (`<WorkspaceHeader` até o PRIMEIRO `);`). Se uma edição futura introduzir
// um `);` intermediário dentro de `workspaceTopo`, aquele guardião passaria
// a medir uma fatia truncada SEM reprovar (asserção inerte) — esta asserção
// reprova antes disso acontecer.
const iWorkspaceHeaderUso = opcoesScreen.indexOf("<WorkspaceHeader");
const iFimWorkspaceTopo = iWorkspaceHeaderUso >= 0
  ? opcoesScreen.indexOf(");", iWorkspaceHeaderUso) : -1;
const corpoWorkspaceTopo = (iWorkspaceHeaderUso >= 0 && iFimWorkspaceTopo > iWorkspaceHeaderUso)
  ? opcoesScreen.slice(iWorkspaceHeaderUso, iFimWorkspaceTopo) : "";
ok("o corpo de workspaceTopo (de <WorkspaceHeader até o primeiro `);`) foi localizado",
   corpoWorkspaceTopo.length > 0);
ok("anti-inércia (Fase 34): a fatia de workspaceTopo ainda contém {workspacePillRow} — nenhum `);` novo truncou a fatia que test_opcoes_hub_workspace_ui.mjs mede",
   corpoWorkspaceTopo.length > 0 && corpoWorkspaceTopo.includes("{workspacePillRow}"));

// ---- 8) Paridade de copy: as 7 chaves, idênticas nos dois modos ------------
const chavesFaltandoOuVazias = CHAVES_NOVAS.filter((k) => !COPY.estudo[k] || !COPY.operador[k]);
ok("as 7 chaves novas existem em COPY.estudo e COPY.operador, nenhuma vazia"
   + (chavesFaltandoOuVazias.length ? " (faltando/vazia: " + chavesFaltandoOuVazias.join(", ") + ")" : ""),
   chavesFaltandoOuVazias.length === 0);
// Fase 39 (39-02-PLAN.md, NAV-01, D-01/D-06): reversão deliberada, não
// apagamento — `opcoesLeituraConcluidaAjuda` ganhou voz por modo porque a
// pill row Analisar/Comparar que justificava o tratamento neutro do plano
// 35-01 deixou de existir (D-01 dissolve as duas abas; D-06 move "Comparar"
// para um link dentro de Montar). As outras 6 chaves continuam idênticas.
const CHAVES_AINDA_IDENTICAS = CHAVES_NOVAS.filter((k) => k !== "opcoesLeituraConcluidaAjuda");
const chavesDivergentes = CHAVES_AINDA_IDENTICAS.filter((k) => COPY.estudo[k] !== COPY.operador[k]);
ok("as 6 chaves restantes têm valor IDÊNTICO nos dois modos (decisão do plano 35-01: metadado de progresso, categoria já neutra)"
   + (chavesDivergentes.length ? " (divergentes: " + chavesDivergentes.join(", ") + ")" : ""),
   chavesDivergentes.length === 0);
ok("opcoesLeituraConcluidaAjuda DIFERE entre Estudo e Operador (Fase 39, NAV-01: ganhou voz por modo, reversão deliberada de 35-01)",
   COPY.estudo.opcoesLeituraConcluidaAjuda !== COPY.operador.opcoesLeituraConcluidaAjuda);

// ---- 9) SecaoSetups.jsx intocada -------------------------------------------
ok("SecaoSetups.jsx não ganhou nenhuma das 7 chaves novas de copy (JORN-03 é paridade estrutural pelo Kicker compartilhado, não tratamento novo dentro da seção)",
   CHAVES_NOVAS.every((k) => !new RegExp("\\b" + k + "\\b").test(secaoSetupsBruto)));
ok("SecaoSetups.jsx não ganhou referência a temLeitura",
   !/\btemLeitura\b/.test(secaoSetupsBruto));

// ============================================================================
// Plano 35-02 (2026-09-21) — hierarquia visual dos 3 CTAs + marca de
// resultado. Blocos 10-18.
// ============================================================================

// Ocorrência EXATA de um identificador — nunca substring: CUSTO_NO_BOTAO_
// PRIMARIO também contém a string "BOTAO_PRIMARIO", e um grep ingênuo (ou
// um .split ingênuo) contaria os dois juntos. Fronteira: nem letra, nem
// dígito, nem `_` dos dois lados.
const idExato = (nome) => new RegExp("(?<![A-Za-z0-9_])" + nome + "(?![A-Za-z0-9_])", "g");
const contarIdExato = (fonte, nome) => (fonte.match(idExato(nome)) || []).length;

// ---- 10) Varredura de tokens por DIRETÓRIO (fecha a classe inteira) --------
const arquivosOpcoesJsx = readdirSync(dirOpcoes).filter((f) => f.endsWith(".jsx"));
ok("sanidade: a varredura por diretório achou pelo menos 8 arquivos .jsx em web/src/opcoes/",
   arquivosOpcoesJsx.length >= 8);

let arquivosComTokens = 0;
let arquivosComReferenciaT = 0;
const violacoesDeToken = [];
for (const nomeArquivo of arquivosOpcoesJsx) {
  const bruto = readFileSync(join(dirOpcoes, nomeArquivo), "utf8");
  const fonte = semComentario(bruto);
  const mTokens = fonte.match(/const TOKENS = \[([\s\S]*?)\]/);
  if (!mTokens) continue;
  arquivosComTokens++;
  const declarados = [...mTokens[1].matchAll(/"([A-Za-z0-9]+)"/g)].map((m) => m[1]);
  const referenciados = [...new Set(
    [...fonte.matchAll(/\bT\.([A-Za-z0-9]+)\b/g)].map((m) => m[1])
  )];
  if (referenciados.length) arquivosComReferenciaT++;
  const faltando = referenciados.filter((t) => !declarados.includes(t));
  if (faltando.length) violacoesDeToken.push(nomeArquivo + ": " + faltando.join(", "));
}
ok("sanidade: pelo menos 8 arquivos declaram um array TOKENS",
   arquivosComTokens >= 8);
ok("sanidade: pelo menos 8 arquivos com TOKENS têm ao menos 1 referência T.<nome> (senão a asserção seguinte passaria por vácuo)",
   arquivosComReferenciaT >= 8);
ok("nenhum arquivo de web/src/opcoes/ referencia T.<token> fora do próprio array TOKENS (bloco que teria pego T.bgPanel em SecaoVigias.jsx, undefined desde 2026-09-20/Fase 33)"
   + (violacoesDeToken.length ? " — violações: " + violacoesDeToken.join(" | ") : ""),
   violacoesDeToken.length === 0);

// ---- 11) Fronteira D-04: exatamente 3 arquivos com BOTAO_PRIMARIO ----------
const ARQUIVOS_COM_CTA_PRIMARIO = ["OpcoesScreen.jsx", "SecaoAnalisar.jsx", "SecaoComparar.jsx"];
const arquivosComBotaoPrimario = [];
for (const nomeArquivo of arquivosOpcoesJsx) {
  const bruto = readFileSync(join(dirOpcoes, nomeArquivo), "utf8");
  if (contarIdExato(bruto, "BOTAO_PRIMARIO") > 0) arquivosComBotaoPrimario.push(nomeArquivo);
}
ok("BOTAO_PRIMARIO existe SOMENTE nos 3 arquivos da allowlist (D-04)"
   + " — achados: " + JSON.stringify(arquivosComBotaoPrimario.sort()),
   JSON.stringify(arquivosComBotaoPrimario.sort()) === JSON.stringify([...ARQUIVOS_COM_CTA_PRIMARIO].sort()));
for (const nomeArquivo of ARQUIVOS_COM_CTA_PRIMARIO) {
  const bruto = readFileSync(join(dirOpcoes, nomeArquivo), "utf8");
  const n = contarIdExato(bruto, "BOTAO_PRIMARIO");
  ok(nomeArquivo + ": BOTAO_PRIMARIO tem exatamente 2 ocorrências do identificador (1 declaração + 1 uso)",
     n === 2);
}

// ---- 12) Os 3 usos são os 3 botões certos ----------------------------------
const fatiaDoBotao = (fonteSemComentario, marcador) => {
  const iMarcador = fonteSemComentario.indexOf(marcador);
  if (iMarcador < 0) return "";
  const iInicio = fonteSemComentario.lastIndexOf("<button", iMarcador);
  const iFim = fonteSemComentario.indexOf("</button>", iMarcador);
  if (iInicio < 0 || iFim < 0) return "";
  return fonteSemComentario.slice(iInicio, iFim + "</button>".length);
};
const botaoLeitura = fatiaDoBotao(opcoesScreen, "cp.opcoesLerNoServico");
const botaoMontar = fatiaDoBotao(secaoAnalisar, "cp.opcoesMontarEstrutura");
const botaoVerPossibilidades = fatiaDoBotao(secaoComparar, "cp.opcoesVerPossibilidades");
ok("os 3 botões-alvo foram localizados (sanidade antes das asserções seguintes)",
   botaoLeitura.length > 0 && botaoMontar.length > 0 && botaoVerPossibilidades.length > 0);
ok("o botão de cp.opcoesLerNoServico usa BOTAO_PRIMARIO", /BOTAO_PRIMARIO/.test(botaoLeitura));
ok("o botão de cp.opcoesMontarEstrutura usa BOTAO_PRIMARIO", /BOTAO_PRIMARIO/.test(botaoMontar));
ok("o botão de cp.opcoesVerPossibilidades usa BOTAO_PRIMARIO", /BOTAO_PRIMARIO/.test(botaoVerPossibilidades));
// Prova pelo avesso: exploração opcional continua neutra.
const botaoVerCadeia = fatiaDoBotao(secaoAnalisar, "cp.opcoesVerCadeia");
const botaoVerOperaveis = fatiaDoBotao(secaoAnalisar, "cp.opcoesVerOperaveis");
ok("os 2 botões de exploração opcional foram localizados (sanidade)",
   botaoVerCadeia.length > 0 && botaoVerOperaveis.length > 0);
ok("o botão de cp.opcoesVerCadeia NÃO usa BOTAO_PRIMARIO (exploração opcional, D-04)",
   !/BOTAO_PRIMARIO/.test(botaoVerCadeia));
ok("o botão de cp.opcoesVerOperaveis NÃO usa BOTAO_PRIMARIO (exploração opcional, D-04)",
   !/BOTAO_PRIMARIO/.test(botaoVerOperaveis));

// ---- 13) Identidade das cópias locais (preço da duplicação aceita) --------
const normaliza = (s) => s.replace(/\s+/g, " ").trim();
const extrairConstObjeto = (fonte, nome) => {
  const m = fonte.match(new RegExp("const " + nome + " = \\{[\\s\\S]*?\\n\\};"));
  return m ? normaliza(m[0]) : null;
};
const extrairConstLinha = (fonte, nome) => {
  const m = fonte.match(new RegExp("const " + nome + " = [^\\n]*;"));
  return m ? normaliza(m[0]) : null;
};
function verificarIdentidade(nome, extrator, arquivos) {
  const corpos = {};
  for (const nomeArquivo of arquivos) {
    const bruto = readFileSync(join(dirOpcoes, nomeArquivo), "utf8");
    const corpo = extrator(semComentario(bruto), nome);
    if (corpo) corpos[nomeArquivo] = corpo;
  }
  const arquivosComDecl = Object.keys(corpos);
  ok(nome + ": encontrado em " + arquivos.length + " arquivo(s) esperado(s)",
     arquivosComDecl.length === arquivos.length);
  const valoresUnicos = [...new Set(Object.values(corpos))];
  const divergentes = valoresUnicos.length > 1 ? arquivosComDecl.join(", ") : "";
  ok(nome + ": as " + arquivos.length + " cópias locais são byte a byte idênticas (normalizado por espaço)"
     + (divergentes ? " — DIVERGEM em: " + divergentes : ""),
     valoresUnicos.length <= 1);
}
verificarIdentidade("BOTAO_PRIMARIO", extrairConstObjeto, ARQUIVOS_COM_CTA_PRIMARIO);
verificarIdentidade("CUSTO_NO_BOTAO_PRIMARIO", extrairConstObjeto, ["OpcoesScreen.jsx", "SecaoAnalisar.jsx"]);
verificarIdentidade("desabilitadoPrimario", extrairConstLinha, ["SecaoAnalisar.jsx", "SecaoComparar.jsx"]);
verificarIdentidade("MARCA_RESULTADO", extrairConstObjeto, ["SecaoAnalisar.jsx", "SecaoComparar.jsx"]);

// ---- 14) Cópia morta proibida ----------------------------------------------
// Fonte SEM COMENTÁRIO: um comentário explicando por que uma constante NÃO
// é declarada num arquivo (ex.: "NÃO declarar CUSTO_NO_BOTAO_PRIMARIO aqui")
// cita o nome literal sem ser uma declaração real — contar o comentário
// junto do código faria esta asserção reprovar por um texto explicativo,
// não por cópia morta de verdade.
const CONSTANTES_NOVAS = ["BOTAO_PRIMARIO", "CUSTO_NO_BOTAO_PRIMARIO", "desabilitadoPrimario", "MARCA_RESULTADO"];
for (const nomeArquivo of arquivosOpcoesJsx) {
  const bruto = readFileSync(join(dirOpcoes, nomeArquivo), "utf8");
  const fonte = semComentario(bruto);
  for (const nomeConst of CONSTANTES_NOVAS) {
    const n = contarIdExato(fonte, nomeConst);
    if (n === 0) continue; // constante não declarada aqui — fora de escopo deste arquivo
    ok(nomeArquivo + ": " + nomeConst + " declarada e USADA (≥ 2 ocorrências, nunca cópia morta)",
       n >= 2);
  }
}

// ---- 15) D-07, o par proibido -----------------------------------------------
const PROIBIDO_SOBRE_ACCENT = /#fff\b|#ffffff\b|"white"|color-mix\(/i;
for (const nomeArquivo of ARQUIVOS_COM_CTA_PRIMARIO) {
  const bruto = readFileSync(join(dirOpcoes, nomeArquivo), "utf8");
  const fonte = semComentario(bruto);
  ok(nomeArquivo + ": nenhum #fff/#ffffff/\"white\"/color-mix( no CÓDIGO (D-07 — 35-UI-SPEC.md mediu que ambos reprovam AA; T.onAccent é o único valor permitido sobre preenchimento de accent)",
     !PROIBIDO_SOBRE_ACCENT.test(fonte));
}

// ---- 16) D-05 ---------------------------------------------------------------
const corpoDesabilitadoPrimario = extrairConstLinha(secaoAnalisar, "desabilitadoPrimario") || "";
ok("desabilitadoPrimario contém 0.55 e cursor: \"not-allowed\", e NÃO contém display (D-05, nunca some)",
   corpoDesabilitadoPrimario.includes("0.55")
   && corpoDesabilitadoPrimario.includes('cursor: "not-allowed"')
   && !corpoDesabilitadoPrimario.includes("display"));
ok("SecaoAnalisar.jsx: o botão de Montar estrutura usa desabilitadoPrimario(, nunca desabilitado(",
   botaoMontar.includes("desabilitadoPrimario(") && contarIdExato(botaoMontar, "desabilitado") === 0);
ok("SecaoComparar.jsx: o botão de Ver possibilidades usa desabilitadoPrimario(, nunca desabilitado(",
   botaoVerPossibilidades.includes("desabilitadoPrimario(") && contarIdExato(botaoVerPossibilidades, "desabilitado") === 0);

// ---- 17) D-06, regra de cor e gate da marca --------------------------------
const fatiaMarcaResultado = (fonteSemComentario, marcador) => {
  const iMarcador = fonteSemComentario.indexOf(marcador);
  if (iMarcador < 0) return "";
  const iInicio = fonteSemComentario.lastIndexOf("{", fonteSemComentario.lastIndexOf("?", iMarcador));
  const iFim = fonteSemComentario.indexOf(": null}", iMarcador);
  if (iInicio < 0 || iFim < 0) return "";
  return fonteSemComentario.slice(iInicio, iFim + ": null}".length);
};
const marcaAnalisar = fatiaMarcaResultado(secaoAnalisar, "cp.opcoesEstruturaMontada");
const marcaComparar = fatiaMarcaResultado(secaoComparar, "cp.opcoesPossibilidadesVistas");
ok("as 2 fatias de MARCA_RESULTADO foram localizadas (sanidade)",
   marcaAnalisar.length > 0 && marcaComparar.length > 0);
ok("MARCA_RESULTADO (Analisar): não usa T.positive/T.negative (par reservado a direção financeira)",
   !/T\.positive\b/.test(marcaAnalisar) && !/T\.negative\b/.test(marcaAnalisar));
ok("MARCA_RESULTADO (Comparar): não usa T.positive/T.negative",
   !/T\.positive\b/.test(marcaComparar) && !/T\.negative\b/.test(marcaComparar));
ok("MARCA_RESULTADO (Analisar): o gate contém .length e NÃO contém .erro nem .carregando",
   marcaAnalisar.includes(".length") && !marcaAnalisar.includes(".erro") && !marcaAnalisar.includes(".carregando"));
ok("MARCA_RESULTADO (Comparar): o gate contém .length e NÃO contém .erro nem .carregando",
   marcaComparar.includes(".length") && !marcaComparar.includes(".erro") && !marcaComparar.includes(".carregando"));

// ---- 18) JORN-03 parity, prova negativa estrutural -------------------------
ok("SecaoSetups.jsx continua sem BOTAO_PRIMARIO/T.accent/T.onAccent (paridade é o Kicker compartilhado do 35-01, não botão novo aqui)",
   !/BOTAO_PRIMARIO/.test(secaoSetups) && !/T\.accent\b/.test(secaoSetups) && !/T\.onAccent\b/.test(secaoSetups));
ok("WorkspaceHeader.jsx continua sem BOTAO_PRIMARIO/T.accent/T.onAccent",
   !/BOTAO_PRIMARIO/.test(workspaceHeader) && !/T\.accent\b/.test(workspaceHeader) && !/T\.onAccent\b/.test(workspaceHeader));

if (fails > 0) {
  console.log(`\n${fails} falha(s).`);
  process.exit(1);
}
console.log("\ntodos os testes passaram");
