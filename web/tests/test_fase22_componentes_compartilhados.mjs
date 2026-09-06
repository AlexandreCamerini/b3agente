// Guardião ÚNICO da Fase 22 (v1.5, Redesenho de UI) — componentes
// compartilhados (trilho, ícones, mascote).
//
// Seção A (SYS-01, plano 22-01): padrão único de rolagem horizontal. Os 4
// trilhos de App.jsx (HERO-CARROSSEL, filtro MODELO DE ANÁLISE, tira de
// OportunidadesOpcoes, linha de candidatos de PropostaDaPosicao) passam a
// chamar os helpers de módulo `carouselTrackStyle`/`carouselItemStyle` em
// vez de definir `overflowX`/scroll-snap inline cada um por conta própria.
//
// Este arquivo vai ser ESTENDIDO pelos planos 22-02 e 22-03 com:
//   Seção B (SYS-02, ícones SVG) — plano 22-02
//   Seção C (SYS-02, Radar + tier dot + varredura de emoji zero) — plano 22-02 ou 22-03
//   Seção D (SYS-03, sombra do PetFab) — plano 22-03
// O próximo agente que tratar SYS-02/SYS-03 deve ACRESCENTAR seções a este
// MESMO arquivo, não criar um arquivo paralelo.
//
// Roda sem build: `node web/tests/test_fase22_componentes_compartilhados.mjs`.
// Padrão da casa: regex sobre App.jsx lido com readFileSync — o módulo
// importa @capacitor/core e não é importável fora do build (ver
// test_fase21_dedup_consolidacao.mjs, test_fase3_c19_card_status.mjs).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// --- Seção A — SYS-01 (plano 22-01): padrão único de carrossel horizontal --

// Isolamento por marcador textual estável, padrão da casa (test_fase3_c19_
// card_status.mjs / test_fase21_dedup_consolidacao.mjs): do início do
// marcador até o próximo marcador do mesmo tipo. Aborta com mensagem
// explícita (nunca passa em silêncio) se o marcador sumir.

function isolarFuncao(nome) {
  const marcador = `function ${nome}(`;
  const inicio = app.indexOf(marcador);
  if (inicio < 0) {
    console.error(`FALHOU: ${marcador} não encontrado em App.jsx — guardião não pode isolar o componente`);
    process.exit(1);
  }
  const fim = app.indexOf("\nfunction ", inicio + 10);
  return app.slice(inicio, fim > inicio ? fim : undefined);
}

const evolucaoScreen = isolarFuncao("EvolucaoScreen");
const oportunidadesOpcoes = isolarFuncao("OportunidadesOpcoes");
const propostaDaPosicao = isolarFuncao("PropostaDaPosicao");
const candidatoOpcao = isolarFuncao("CandidatoOpcao");

// TECH_MODELS não vive dentro de uma função nomeada própria — isolar pelo
// próprio marcador do container + o `.map()` que segue, com um recorte
// generoso (algumas linhas antes e depois) para cobrir container e item.
const idxTechModels = app.indexOf("TECH_MODELS.map(");
if (idxTechModels < 0) {
  console.error("FALHOU: TECH_MODELS.map( não encontrado em App.jsx — guardião não pode isolar o filtro MODELO DE ANÁLISE");
  process.exit(1);
}
// A abertura do container fica na linha imediatamente anterior ao .map() —
// recuar até o início dessa linha (o `<div style={carouselTrackStyle...`).
const inicioContainerTechModels = app.lastIndexOf("\n", app.lastIndexOf("\n", idxTechModels) - 1) + 1;
const fimTechModels = app.indexOf("</div>", idxTechModels + "TECH_MODELS.map(".length);
const techModelsBloco = app.slice(inicioContainerTechModels, fimTechModels > 0 ? fimTechModels : idxTechModels + 800);

// --- 1. carouselTrackStyle existe -------------------------------------------

const idxTrackDef = app.indexOf("const carouselTrackStyle");
ok("existe `const carouselTrackStyle`", idxTrackDef >= 0);
if (idxTrackDef >= 0) {
  const fimTrackDef = app.indexOf("\nconst ", idxTrackDef + 10);
  const trackDefBloco = app.slice(idxTrackDef, fimTrackDef > idxTrackDef ? fimTrackDef : idxTrackDef + 400);
  ok("`carouselTrackStyle` contém `overflowX: \"auto\"`", trackDefBloco.includes('overflowX: "auto"'));
  ok("`carouselTrackStyle` contém `display: \"flex\"`", trackDefBloco.includes('display: "flex"'));
  ok("`carouselTrackStyle` contém `scrollSnapType: \"x proximity\"`", trackDefBloco.includes('scrollSnapType: "x proximity"'));
  ok("`carouselTrackStyle` contém `WebkitOverflowScrolling: \"touch\"`", trackDefBloco.includes('WebkitOverflowScrolling: "touch"'));
} else {
  ok("`carouselTrackStyle` contém `overflowX: \"auto\"`", false);
  ok("`carouselTrackStyle` contém `display: \"flex\"`", false);
  ok("`carouselTrackStyle` contém `scrollSnapType: \"x proximity\"`", false);
  ok("`carouselTrackStyle` contém `WebkitOverflowScrolling: \"touch\"`", false);
}

// --- 2. carouselItemStyle existe ---------------------------------------------

const idxItemDef = app.indexOf("const carouselItemStyle");
ok("existe `const carouselItemStyle`", idxItemDef >= 0);
if (idxItemDef >= 0) {
  const fimItemDef = app.indexOf("\nconst ", idxItemDef + 10);
  const itemDefBloco = app.slice(idxItemDef, fimItemDef > idxItemDef ? fimItemDef : idxItemDef + 200);
  ok("`carouselItemStyle` contém `scrollSnapAlign`", itemDefBloco.includes("scrollSnapAlign"));
} else {
  ok("`carouselItemStyle` contém `scrollSnapAlign`", false);
}

// --- 3. Asserção central: overflowX: "auto" só pode existir 1x (no helper) --

const totalOverflowXAuto = (app.match(/overflowX: "auto"/g) || []).length;
ok(
  "`overflowX: \"auto\"` aparece exatamente 1× em App.jsx (trilho horizontal novo deve usar carouselTrackStyle(), não redefinir overflowX inline)",
  totalOverflowXAuto === 1
);

// --- 4. Os 4 call sites de carouselTrackStyle( -------------------------------
// A definição é `const carouselTrackStyle = (extra) => ({...})` — o nome
// seguido de parêntese sem espaço não ocorre nessa forma, então a definição
// não entra na contagem de chamadas.

const totalTrackCalls = (app.match(/carouselTrackStyle\(/g) || []).length;
ok("os 4 containers de trilho chamam `carouselTrackStyle(` (limiar >= 4, definição não conta)", totalTrackCalls >= 4);

// --- 5. Os 4 itens de carouselItemStyle( -------------------------------------
// Mesma razão do item 4: `const carouselItemStyle = (align = "start") => ...`
// não casa com o padrão `nome(`.

const totalItemCalls = (app.match(/carouselItemStyle\(/g) || []).length;
ok("os 4 itens chamam `carouselItemStyle(` (limiar >= 4, definição não conta)", totalItemCalls >= 4);

// --- 6. Presença nomeada de cada um dos 4 call sites -------------------------

ok("recorte de TECH_MODELS.map( chama `carouselTrackStyle(`", techModelsBloco.includes("carouselTrackStyle("));
ok("função OportunidadesOpcoes chama `carouselTrackStyle(`", oportunidadesOpcoes.includes("carouselTrackStyle("));
ok("função PropostaDaPosicao chama `carouselTrackStyle(`", propostaDaPosicao.includes("carouselTrackStyle("));
ok("função EvolucaoScreen (HERO-CARROSSEL) chama `carouselTrackStyle(`", evolucaoScreen.includes("carouselTrackStyle("));

// --- 7. Taxonomia preservada (Decisão 1 do 22-UI-SPEC): peek de 84% só HERO -

const totalPeek84 = (app.match(/flex: "0 0 84%"/g) || []).length;
ok(
  "`flex: \"0 0 84%\"` aparece exatamente 1× (peek de 84% é do HERO-CARROSSEL apenas — chips de filtro e candidatos de opção precisam ficar comparáveis lado a lado)",
  totalPeek84 === 1
);

// --- 8. Sub-variante de foco único é só do HERO ------------------------------

const totalMandatory = (app.match(/"x mandatory"/g) || []).length;
ok('"x mandatory" aparece exatamente 1× (override exclusivo do HERO-CARROSSEL)', totalMandatory === 1);

const totalCenterAlign = (app.match(/scrollSnapAlign: "center"/g) || []).length + (app.match(/carouselItemStyle\("center"\)/g) || []).length;
ok('`scrollSnapAlign: "center"` (ou `carouselItemStyle("center")`) aparece exatamente 1× (o HERO)', totalCenterAlign === 1);

// --- 9. <main> mantém overflowX: "hidden" (FIX-01, Fase 20, fora de escopo) -

ok('`<main>` mantém `overflowX: "hidden"` (FIX-01, Fase 20, fora do escopo do helper)', /<main[^>]*overflowX: "hidden"/.test(app));

if (fails > 0) {
  console.error(`\n${fails} asserção(ões) falharam.`);
}
process.exit(fails);
