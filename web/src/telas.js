// Fase 41 (TELAS-01) — registro único da ESTRUTURA das 8 telas que o
// assistente (Boris) conhece. Sem React, sem I/O, sem store: só a
// declaração estática de id, posição na barra, posição no tour, presença na
// ajuda e origem do snapshot de cada tela — o mesmo contrato de módulo puro
// de `web/src/opcoes/memoriaOpcoes.js` (Fase 40).
//
// D-01: as 8 telas são exatamente as de `conceitos.PET_TELAS` — travado por
// dois pontos testados (`web/tests/test_telas_registro.mjs` aqui,
// `server/tests/test_telas_paridade.py` do lado Python), 8 com 8, sem
// exceção. Nenhum import cross-language: cada lado lê o fonte do outro como
// TEXTO (padrão `defaults.py`×`catalog.js`, CLAUDE.md).
//
// D-02: este registro guarda só ESTRUTURA. Os TEXTOS do tour e da ajuda
// continuam em `tourPassos`/`ajudaSecoes` (App.jsx) e em `copy.js` — o
// registro só diz QUAIS telas entram em cada um e em que ordem. Os 2 passos
// de introdução do tour (que não são tela nenhuma) ficam fora daqui, de
// propósito.
//
// D-03: o snapshot do assistente é calculado em runtime (hooks, dados de
// carteira/cotações) e por isso NÃO é dado estático — o switch de
// `petSnapshot` continua em App.jsx. O campo `snapshot` aqui só declara QUEM
// tem `case` próprio nesse switch ("switch") e quem não tem porque o
// snapshot vem de outro lugar ("petSheet" — o resumo de "mercado" vem de
// dentro do próprio PetSheet, nunca do switch, por desenho antigo da F4).
//
// `agente` e `historico` não são abas da barra nem tabs de `App.jsx` — são
// sub-telas de "carteira", selecionadas por `carteiraView`. `subtelaDe` +
// `carteiraView` capturam essa relação para `telaDoAssistente()` reproduzir
// a mesma ternária que `petTela` sempre computou.
//
// Zero mudança visível (D-04): os campos abaixo reproduzem byte a byte o
// comportamento congelado em `web/tests/fixtures/telas_baseline_41.json`
// (gerado do App.jsx ANTES desta consolidação). Qualquer inconsistência
// encontrada (ex. `historico`/`perfil` sem seção de ajuda, `agente` sem
// passo de tour) é um ACHADO REGISTRADO, não corrigido nesta fase.
//
// ------------------------------------------- Como adicionar uma tela nova
//
// Depois da 41-02 (religação completa dos 4 consumidores), o procedimento
// REAL é este — conferido contra o código religado, não uma versão
// aspiracional de "uma linha e pronto" (SC#4 é "a LISTA mora num ponto só e
// o resto é exigido por teste", não "zero trabalho"):
//
//  1. Uma entrada nova em `TELAS` (acima) — o ÚNICO ponto da LISTA no
//     front. Campos sempre presentes, `null` quando não se aplica (nunca
//     omitidos — os testes de paridade casam por forma estável).
//  2. Espelho em `server/app/conceitos.py:PET_TELAS` (backend) — a paridade
//     8-com-8 reprova NOS DOIS LADOS se faltar
//     (`web/tests/test_telas_registro.mjs` PARTE A,
//     `server/tests/test_telas_paridade.py`).
//  3. Conteúdo que DEPENDE da natureza da tela — cada um só é exigido
//     quando o campo correspondente pede, e cada um tem teste próprio que
//     reprova sem ele:
//       · `snapshot: "switch"` → precisa de um `case "<id>":` no switch de
//         `petSnapshot` (App.jsx) — sem ele, PARTE E de
//         `test_telas_registro.mjs` reprova (D-03). `snapshot: "petSheet"`
//         (só "mercado", por desenho da F4) dispensa o case.
//       · `tour` não-nulo → precisa de uma entrada em `porTela` dentro de
//         `tourPassos(cp)` (App.jsx) — sem ela, `telasDoTour().map((id) =>
//         porTela[id])` produz `undefined` na posição e a PARTE C
//         (equivalência com o fixture) reprova.
//       · `ajuda: true` → precisa de uma entrada em `porTela` dentro de
//         `ajudaSecoes(cp, operador)` (App.jsx) — mesma consequência
//         (`undefined` no array, PARTE C reprova).
//       · `barra` não-nulo → precisa de um path em `NavIcon.paths`
//         (App.jsx) — sem ele, o ícone da aba não renderiza (nenhum teste
//         estático trava isso hoje; é inspeção visual, achado registrado
//         abaixo).
//       · `rotuloCp` não-nulo → precisa da chave em `copy.js` nos DOIS
//         modos (Estudo/Operador) — guardrail do repositório (CLAUDE.md),
//         não teste local deste registro.
//     Além dos testes automáticos: o COMPONENTE da tela e o ramo de render
//     em `App.jsx` (`tab === "<id>" && <TelaScreen ... />`), e um ramo de
//     resumo em `server/app/main.py` (`_pet_resumo_<id>` + `elif aba ==
//     "<id>":`) se a tela precisar de resumo próprio para `/api/pet/resumo`
//     — nenhum dos dois tem teste estrutural genérico hoje (só os testes
//     específicos de cada feature, caso existam).
//
// Walkthrough de uma tela hipotética + contagem de arquivos: ver
// "Plano 41-02" no `41-02-SUMMARY.md`.

export const TELAS = Object.freeze([
  Object.freeze({
    id: "evolucao",
    barra: 1,
    rotuloCp: null,
    rotuloPadrao: "Acompanhar",
    tour: null,
    ajuda: true,
    snapshot: "switch",
    subtelaDe: null,
    carteiraView: null,
  }),
  Object.freeze({
    id: "radar",
    barra: 2,
    rotuloCp: "tabRadar",
    rotuloPadrao: "Radar",
    tour: 1,
    ajuda: true,
    snapshot: "switch",
    subtelaDe: null,
    carteiraView: null,
  }),
  Object.freeze({
    id: "mercado",
    barra: 3,
    rotuloCp: "tituloWatchlist",
    rotuloPadrao: "Watchlist",
    tour: 2,
    ajuda: true,
    // "mercado" NÃO tem `case` no switch de petSnapshot, de propósito: o
    // snapshot dele vem do resumo dentro do PetSheet (regra da F4).
    snapshot: "petSheet",
    subtelaDe: null,
    carteiraView: null,
  }),
  Object.freeze({
    id: "carteira",
    barra: 4,
    rotuloCp: "tituloPortfolio",
    rotuloPadrao: "Portfólio",
    tour: 3,
    ajuda: true,
    snapshot: "switch",
    subtelaDe: null,
    carteiraView: null,
  }),
  Object.freeze({
    id: "opcoes",
    barra: 5,
    rotuloCp: "tabOpcoes",
    rotuloPadrao: "Opções",
    tour: 4,
    ajuda: true,
    snapshot: "switch",
    subtelaDe: null,
    carteiraView: null,
  }),
  Object.freeze({
    id: "agente",
    barra: null,
    rotuloCp: null,
    rotuloPadrao: null,
    tour: null,
    ajuda: true,
    snapshot: "switch",
    subtelaDe: "carteira",
    carteiraView: "agente",
  }),
  Object.freeze({
    id: "historico",
    barra: null,
    rotuloCp: null,
    rotuloPadrao: null,
    tour: null,
    // Achado registrado (não corrigido, D-04): `ajudaSecoes` não tem seção
    // própria para `historico`.
    ajuda: false,
    snapshot: "switch",
    subtelaDe: "carteira",
    carteiraView: "historico",
  }),
  Object.freeze({
    id: "perfil",
    barra: null,
    rotuloCp: null,
    rotuloPadrao: null,
    tour: null,
    // Achado registrado (não corrigido, D-04): `ajudaSecoes` não tem seção
    // própria para `perfil`.
    ajuda: false,
    snapshot: "switch",
    subtelaDe: null,
    carteiraView: null,
  }),
]);

// ------------------------------------------------------------- leitura pura

export function idsDasTelas() {
  return TELAS.map((t) => t.id);
}

// Reproduz `BottomNav.defs`: rótulo por modo via `cp.*` com fallback literal
// — `(cp && cp.X) || "literal"`. `evolucao` não tem `rotuloCp` e por isso
// ignora `cp` (mesma semântica de sempre: o item nunca variou por modo).
export function defsDaBarra(cp) {
  return TELAS.filter((t) => t.barra != null)
    .sort((a, b) => a.barra - b.barra)
    .map((t) => {
      const doCp = t.rotuloCp && cp && cp[t.rotuloCp];
      return [t.id, doCp || t.rotuloPadrao];
    });
}

export function telasDoTour() {
  return TELAS.filter((t) => t.tour != null)
    .sort((a, b) => a.tour - b.tour)
    .map((t) => t.id);
}

export function telasDaAjuda() {
  return TELAS.filter((t) => t.ajuda === true).map((t) => t.id);
}

// Reproduz a ternária de `petTela`:
//   tab === "carteira"
//     ? (carteiraView === "historico" ? "historico" : carteiraView === "agente" ? "agente" : "carteira")
//     : tab
// Qualquer `tab` fora de "carteira" (inclusive valor desconhecido) volta
// inalterado — mesma semântica de sempre.
export function telaDoAssistente(tab, carteiraView) {
  if (tab !== "carteira") return tab;
  const sub = TELAS.find((t) => t.subtelaDe === "carteira" && t.carteiraView === carteiraView);
  return sub ? sub.id : "carteira";
}

export function idsComSnapshotNoSwitch() {
  return TELAS.filter((t) => t.snapshot === "switch").map((t) => t.id);
}
