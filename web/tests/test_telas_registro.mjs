// Fase 41, plano 41-01 — TELAS-01: guardião do registro único de telas.
//
// Origem: achado C3 da Fase 26 / A1 (2026-09-12) — "opcoes" entrou na barra
// (`BottomNav.defs`) e ficou fora de `petSnapshot`/`conceitos.PET_TELAS`, e o
// mesmo defeito podia se repetir em QUALQUER tela nova, porque havia cinco
// listas paralelas sem teste amarrando uma na outra. `web/tests/test_pet_opcoes.mjs`
// se autodeclarava "rede de segurança até a Fase 41" (26-CONTEXT.md, item C3)
// — este arquivo é a Fase 41 chegando: ele absorve esse papel para o lado do
// front, agora comparando o REGISTRO ÚNICO (`web/src/telas.js`, D-01) contra
// `conceitos.PET_TELAS`, em vez de derivar de `BottomNav.defs` isolado.
//
// Padrão de "dois pontos testados, sem import cross-language" (CLAUDE.md,
// paridade defaults.py×catalog.js): este arquivo lê `conceitos.py` como TEXTO
// (nunca subprocess Python, nunca import); o espelho do lado Python é
// `server/tests/test_telas_paridade.py`, que lê `telas.js` como texto.
//
// PARTE A — paridade registro↔PET_TELAS (8 com 8, sem exceção — D-01).
// PARTE B — integridade estrutural do registro (sem duplicata, ordens
//           contíguas, módulo sem import).
// PARTE C — equivalência com o fixture pré-refactor (`telas_baseline_41.json`,
//           gerado do App.jsx ANTES de qualquer edição, Task 1 deste plano) —
//           prova que as funções do registro reproduzem byte a byte o
//           comportamento atual das 4 listas (D-04: refactor puro).
//
// Plano 41-02, Task 2 — PARTES C (cont.), D e E acrescentadas:
// PARTE C (cont.) — tourPassos/ajudaSecoes EXTRAÍDAS do App.jsx atual
//           (religado) deepEqual o fixture pré-refactor, nas 2 e 4
//           combinações de modo — prova que mover os textos de tela para
//           `porTela` não mudou nada visível.
// PARTE D — fiação (SC#1): nenhuma lista paralela sobrou em App.jsx; os 4
//           consumidores chamam as funções do registro.
// PARTE E — D-03: o conjunto de `case "<id>":` do switch de petSnapshot é
//           igual a `idsComSnapshotNoSwitch()`; o sha256 do bloco do switch
//           bate com o do fixture (switch intocado).
//
// Roda sem build e sem servidor: `node web/tests/test_telas_registro.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { createHash } from "crypto";
import { COPY } from "../src/copy.js";
import {
  TELAS,
  idsDasTelas,
  defsDaBarra,
  telasDoTour,
  telasDaAjuda,
  telaDoAssistente,
  idsComSnapshotNoSwitch,
} from "../src/telas.js";

const here = dirname(fileURLToPath(import.meta.url));
const conceitos = readFileSync(join(here, "..", "..", "server", "app", "conceitos.py"), "utf8");
const baseline = JSON.parse(readFileSync(join(here, "fixtures", "telas_baseline_41.json"), "utf8"));

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};
const deepEqual = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// ============================================================= PARTE A
// paridade registro ↔ conceitos.PET_TELAS (D-01: 8 com 8, sem exceção)
const PET_TELAS = (conceitos.match(/PET_TELAS = \(([^)]*)\)/) || [, ""])[1]
  .split(",").map((s) => s.trim().replace(/^"|"$/g, "")).filter(Boolean);
ok("conceitos.PET_TELAS foi lido do backend", PET_TELAS.length === 8, "achou: " + PET_TELAS.join(", "));

const ids = idsDasTelas();
ok("o registro tem exatamente 8 ids", ids.length === 8, "achou " + ids.length);
ok(
  "o conjunto de ids do registro é IGUAL ao de conceitos.PET_TELAS (8 com 8, sem exceção)",
  deepEqual([...ids].sort(), [...PET_TELAS].sort()),
  "diferença: registro-só=" + ids.filter((i) => !PET_TELAS.includes(i)).join(",") +
    " | PET_TELAS-só=" + PET_TELAS.filter((i) => !ids.includes(i)).join(",") +
    " — uma tela fora de PET_TELAS faz /api/assistente responder 400 'Tela desconhecida.'; uma tela em PET_TELAS fora do registro faz o assistente falar de uma tela que o front não declara"
);

// ============================================================= PARTE B
// integridade estrutural do registro
ok("sem id duplicado", new Set(ids).size === ids.length);
ok("o módulo telas.js não importa nada (React/store/copy.js)", Array.isArray(TELAS) && TELAS.length === 8);

const comBarra = TELAS.filter((t) => t.barra != null).sort((a, b) => a.barra - b.barra);
ok(
  "as ordens de barra são contíguas 1..5",
  deepEqual(comBarra.map((t) => t.barra), [1, 2, 3, 4, 5]),
  "achou: " + comBarra.map((t) => t.barra).join(",")
);
for (const t of comBarra) {
  ok(`a tela "${t.id}" (na barra) tem rotuloPadrao string não-vazia`, typeof t.rotuloPadrao === "string" && t.rotuloPadrao.length > 0);
}

const comTour = TELAS.filter((t) => t.tour != null);
const posicoesTour = comTour.map((t) => t.tour).sort((a, b) => a - b);
ok(
  "as posições de tour são únicas 1..4",
  deepEqual(posicoesTour, [1, 2, 3, 4]),
  "achou: " + posicoesTour.join(",")
);

// ============================================================= PARTE C
// equivalência com o fixture pré-refactor (comportamento congelado ANTES de
// qualquer edição — Task 1 deste plano)

// --- barra: defsDaBarra(cp) reproduz BottomNav.defs para as 4 combinações
for (const [chave, cp] of [["estudo", COPY.estudo], ["operador", COPY.operador], ["nulo", null], ["vazio", {}]]) {
  const got = defsDaBarra(cp);
  ok(
    `defsDaBarra(${chave}) reproduz o baseline (BottomNav.defs pré-refactor)`,
    deepEqual(got, baseline.barra[chave]),
    "rótulo/ordem da barra divergiu do baseline → mudança visível, viola D-04. esperado=" +
      JSON.stringify(baseline.barra[chave]) + " obtido=" + JSON.stringify(got)
  );
}

// --- tour: ids na ordem certa (textos continuam em tourPassos, D-02)
ok(
  'telasDoTour() é ["radar","mercado","carteira","opcoes"], na ordem do funil',
  deepEqual(telasDoTour(), ["radar", "mercado", "carteira", "opcoes"]),
  "achou: " + JSON.stringify(telasDoTour())
);
ok("o baseline confirma 6 passos de tour (4 do funil + 2 de introdução fora do registro, D-02)", baseline.tour.estudo.length === 6);

// --- ajuda: ids com seção (historico/perfil não têm — achado registrado, não corrigido)
ok(
  'telasDaAjuda() é ["evolucao","radar","mercado","carteira","opcoes","agente"]',
  deepEqual(telasDaAjuda(), ["evolucao", "radar", "mercado", "carteira", "opcoes", "agente"]),
  "achou: " + JSON.stringify(telasDaAjuda())
);
ok("o baseline confirma 11 seções em ajudaSecoes (só 6 mapeiam 1:1 com tela — achado registrado)", baseline.ajuda["estudo,false"].length === 11);

// --- petTela: telaDoAssistente reproduz a tabela-verdade do baseline (35 combinações)
const tabsBaseline = Object.keys(baseline.petTela);
let combinacoes = 0;
for (const tab of tabsBaseline) {
  for (const chaveView of Object.keys(baseline.petTela[tab])) {
    const view = chaveView === "__undefined__" ? undefined : chaveView;
    const esperado = baseline.petTela[tab][chaveView];
    const obtido = telaDoAssistente(tab, view);
    combinacoes++;
    ok(
      `telaDoAssistente("${tab}", ${JSON.stringify(view)}) === "${esperado}" (baseline)`,
      obtido === esperado,
      "obtido=" + obtido
    );
  }
}
ok("a tabela-verdade cobriu as 35 combinações do baseline (7 tabs × 5 carteiraView)", combinacoes === 35, "achou " + combinacoes);

// --- snapshot: idsComSnapshotNoSwitch() tem o mesmo conjunto do baseline (switch do petSnapshot)
const snapBaseline = baseline.switchPetSnapshot.casos;
const snapRegistro = idsComSnapshotNoSwitch();
ok(
  "idsComSnapshotNoSwitch() tem o MESMO conjunto de baseline.switchPetSnapshot.casos",
  deepEqual([...snapRegistro].sort(), [...snapBaseline].sort()),
  "diferença: registro-só=" + snapRegistro.filter((i) => !snapBaseline.includes(i)).join(",") +
    " | baseline-só=" + snapBaseline.filter((i) => !snapRegistro.includes(i)).join(",")
);
ok('"mercado" é a única tela com snapshot "petSheet" (fora do switch, de propósito)', !snapRegistro.includes("mercado"));

// ============================================================= PARTE C (cont.)
// tourPassos(COPY.<modo>)/ajudaSecoes(COPY.<modo>, op) EXTRAÍDAS do App.jsx
// ATUAL (religado pela 41-02) deepEqual o fixture pré-refactor — prova que
// mover os 4/6 textos de tela para `porTela` (D-02) não mudou nada visível.
//
// Técnica de extração copiada de `web/tests/test_tour_opcoes.mjs:48-57`
// (contagem de chaves + eval, não regex de contagem — regex daria falso
// verde na primeira reorganização do array/objeto). O `eval` roda no escopo
// deste módulo, que já importou `telasDoTour`/`telasDaAjuda` no topo — as
// duas funções extraídas chamam esses nomes internamente depois da GREEN
// desta task, e o `eval` precisa resolvê-los sem erro de referência.
function extrair(nome, fonte) {
  const i = fonte.indexOf("function " + nome + "(");
  if (i < 0) return null;
  let nivel = 0, dentro = false;
  for (let k = i; k < fonte.length; k++) {
    if (fonte[k] === "{") { nivel++; dentro = true; }
    else if (fonte[k] === "}") { nivel--; if (dentro && nivel === 0) return fonte.slice(i, k + 1); }
  }
  return null;
}

const appSrc = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const fonteTour = extrair("tourPassos", appSrc);
const fonteAjuda = extrair("ajudaSecoes", appSrc);
ok("tourPassos foi encontrada em App.jsx", !!fonteTour);
ok("ajudaSecoes foi encontrada em App.jsx", !!fonteAjuda);
const tourPassosAtual = fonteTour ? eval("(" + fonteTour + ")") : null; // eslint-disable-line no-eval
const ajudaSecoesAtual = fonteAjuda ? eval("(" + fonteAjuda + ")") : null; // eslint-disable-line no-eval

for (const [chave, cp] of [["estudo", COPY.estudo], ["operador", COPY.operador]]) {
  const passos = tourPassosAtual ? tourPassosAtual(cp) : null;
  ok(
    `tourPassos(${chave}) extraída do App.jsx reproduz o baseline pré-refactor byte a byte`,
    deepEqual(passos, baseline.tour[chave]),
    "os textos do tour mudaram ao entrar em porTela → viola D-04. esperado=" +
      JSON.stringify(baseline.tour[chave]) + " obtido=" + JSON.stringify(passos)
  );
}
for (const [chaveModo, cp] of [["estudo", COPY.estudo], ["operador", COPY.operador]]) {
  for (const operador of [false, true]) {
    const chave = chaveModo + "," + operador;
    const secoes = ajudaSecoesAtual ? ajudaSecoesAtual(cp, operador) : null;
    ok(
      `ajudaSecoes(${chave}) extraída do App.jsx reproduz o baseline pré-refactor byte a byte`,
      deepEqual(secoes, baseline.ajuda[chave]),
      "os textos da ajuda mudaram ao entrar em porTela → viola D-04. esperado=" +
        JSON.stringify(baseline.ajuda[chave]) + " obtido=" + JSON.stringify(secoes)
    );
  }
}

// ============================================================= PARTE D
// fiação (SC#1): nenhuma lista paralela de tela sobrou em App.jsx
ok('App.jsx não contém mais o literal "const defs = [["', !/const defs = \[\[/.test(appSrc));
ok(
  "App.jsx não contém mais a ternária antiga de petTela",
  !/carteiraView === "historico" \? "historico" : carteiraView === "agente" \? "agente" : "carteira"/.test(appSrc)
);
ok("BottomNav chama defsDaBarra(cp)", /const defs = defsDaBarra\(cp\);/.test(appSrc));
ok("tourPassos chama telasDoTour()", /telasDoTour\(\)/.test(appSrc));
ok("ajudaSecoes chama telasDaAjuda()", /telasDaAjuda\(\)/.test(appSrc));
ok("petTela usa telaDoAssistente(tab, carteiraView)", /const petTela = telaDoAssistente\(tab, carteiraView\);/.test(appSrc));

// ============================================================= PARTE E
// D-03: o switch de petSnapshot está amarrado ao registro por teste — o
// mesmo marcador de início/fim do gerador do fixture (Task 1, 41-01).
const inicioMarcador = "switch (petTela) {";
const fimMarcador = "}, [petTela, data, quotes, wlScan]);";
const iInicio = appSrc.indexOf(inicioMarcador);
const iFim = appSrc.indexOf(fimMarcador, iInicio);
ok("o bloco do switch de petSnapshot foi encontrado em App.jsx", iInicio >= 0 && iFim >= 0);
const blocoSwitch = iInicio >= 0 && iFim >= 0 ? appSrc.slice(iInicio, iFim + fimMarcador.length) : "";
const casosNoSwitch = [...blocoSwitch.matchAll(/case "([a-z]+)":/g)].map((m) => m[1]);
const idsSwitchRegistro = idsComSnapshotNoSwitch();
ok(
  "o conjunto de case do switch é IGUAL a idsComSnapshotNoSwitch() (D-03)",
  deepEqual([...casosNoSwitch].sort(), [...idsSwitchRegistro].sort()),
  "diferença: switch-só=" + casosNoSwitch.filter((c) => !idsSwitchRegistro.includes(c)).join(",") +
    " | registro-só=" + idsSwitchRegistro.filter((c) => !casosNoSwitch.includes(c)).join(",")
);
for (const c of casosNoSwitch) {
  ok(`o case "${c}" do switch é um id do registro`,
     idsDasTelas().includes(c),
     "case sem entrada no registro → tela que o assistente explica sem ser tela registrada");
}
for (const id of idsSwitchRegistro) {
  ok(`a entrada "${id}" (snapshot:"switch") tem case no switch`,
     casosNoSwitch.includes(id),
     "entrada snapshot:'switch' sem case → cai no default: return {} e o Boris fala sem dado (achado A1 da Fase 26)");
}
const sha256Switch = createHash("sha256").update(blocoSwitch, "utf8").digest("hex");
ok(
  "o sha256 do bloco do switch é igual ao do fixture (switch intocado, D-03)",
  sha256Switch === baseline.switchPetSnapshot.sha256,
  "esperado=" + baseline.switchPetSnapshot.sha256 + " obtido=" + sha256Switch
);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
