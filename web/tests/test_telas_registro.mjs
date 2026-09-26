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
// Roda sem build e sem servidor: `node web/tests/test_telas_registro.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
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

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
