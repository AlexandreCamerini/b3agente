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
// Roda sem build: `node web/tests/test_opcoes_jornada_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");

const opcoesScreenBruto = readFileSync(join(dirOpcoes, "OpcoesScreen.jsx"), "utf8");
const secaoSetupsBruto = readFileSync(join(dirOpcoes, "SecaoSetups.jsx"), "utf8");

// Sem comentários: este plano ACRESCENTA comentários que citam `abaWorkspace`,
// `temLeitura` e nomes de chave para EXPLICAR as decisões (D-01/D-02/D-06/
// D-08) — contá-los junto do código faria o guardião se auto-invalidar.
// Mesmo padrão de `test_opcoes_hub_workspace_ui.mjs`/`test_opcoes_subabas_ui.mjs`.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

const opcoesScreen = semComentario(opcoesScreenBruto);

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
const chavesDivergentes = CHAVES_NOVAS.filter((k) => COPY.estudo[k] !== COPY.operador[k]);
ok("as 7 chaves novas têm valor IDÊNTICO nos dois modos (decisão do plano 35-01: metadado de progresso, categoria já neutra)"
   + (chavesDivergentes.length ? " (divergentes: " + chavesDivergentes.join(", ") + ")" : ""),
   chavesDivergentes.length === 0);

// ---- 9) SecaoSetups.jsx intocada -------------------------------------------
ok("SecaoSetups.jsx não ganhou nenhuma das 7 chaves novas de copy (JORN-03 é paridade estrutural pelo Kicker compartilhado, não tratamento novo dentro da seção)",
   CHAVES_NOVAS.every((k) => !new RegExp("\\b" + k + "\\b").test(secaoSetupsBruto)));
ok("SecaoSetups.jsx não ganhou referência a temLeitura",
   !/\btemLeitura\b/.test(secaoSetupsBruto));

if (fails > 0) {
  console.log(`\n${fails} falha(s).`);
  process.exit(1);
}
console.log("\ntodos os testes passaram");
