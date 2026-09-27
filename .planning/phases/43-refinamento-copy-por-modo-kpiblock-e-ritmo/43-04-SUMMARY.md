---
phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
plan: 04
subsystem: ui
tags: [copy, vocabulario, hier-03, historicopill, ativocard, setoralvo]

# Dependency graph
requires:
  - phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
    plan: 01
    provides: "reconciliacaoTxt/reconciliacaoPorQueImporta em web/src/copy.js"
  - phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
    plan: 03
    provides: "SP (escala 4/8pt) já migrado no card; test_ritmo_sp.mjs fiscalizando HistoricoPill"
provides:
  - "HistoricoPill com terceira forma mutuamente exclusiva `microtexto` (D-07/D-09), além de números crus e compacto"
  - "Call site do AtivoCard (Watchlist e Radar) passando microtexto/A/didatica/dados"
  - "Guardião Parte B em web/tests/test_reconciliacao_elegibilidade.mjs, fiando a fiação real no App.jsx"
affects: [43-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fronteira fato/clausula como DUAS strings prontas (reconciliacaoTxt + reconciliacaoPorQueImporta), nunca uma cortada no front — mesma regra didatica-boris já usada por HistoricoPill/entradaAuto"
    - "SetorAlvo reusado como wrapper de cláusula tocável dentro de um <span> de texto corrido (não só em torno de chip), mesmo componente do fundamento (D-18 do 43-02)"

key-files:
  created: []
  modified:
    - web/tests/test_reconciliacao_elegibilidade.mjs
    - web/src/App.jsx

key-decisions:
  - "Nenhuma - plano seguido como especificado (JSX de referência do 43-UI-SPEC.md, linhas 351-390/419-424, usado verbatim)"

patterns-established: []

requirements-completed: [HIER-03]

# Metrics
duration: ~20min
completed: 2026-09-27
---

# Phase 43 Plan 04: Microtexto de reconciliação HIER-03 na linha de elegibilidade Summary

**HistoricoPill ganha a forma `microtexto` — a linha de elegibilidade do AtivoCard troca números crus por uma frase por modo (`reconciliacaoTxt`), com cláusula tocável só no Estudo (`SetorAlvo setorId="analise"`) — listas por setup e modo compacto continuam com chip + números.**

## Performance

- **Duration:** ~20 min
- **Tasks:** 2 completadas (TDD RED→GREEN)
- **Files modified:** 2

## Accomplishments
- `web/tests/test_reconciliacao_elegibilidade.mjs`: Parte B nova (11 asserções) lendo `App.jsx` como texto — confirma import, assinatura de `HistoricoPill`, chamada exata de `reconciliacaoTxt`, gates `!microtexto`/`!operador`, `SUBLINHADO`, ordem do modificador `⏱`, call site único com `microtexto`, ausência de string literal da frase, e cor do span em `T.textSecondary`. Parte A (43-01) permanece intacta.
- `HistoricoPill` ganha `microtexto, A, didatica, dados` na assinatura; a terceira forma substitui os números crus por `reconciliacaoTxt(modoJS, estado, { n: nJanela, janela: janelaRef, expR: expRJanela })` — Estudo com a cláusula tocável "sinal técnico e histórico medido são coisas diferentes" (dentro de `SetorAlvo setorId="analise"`, sublinhada), Operador sem cláusula (`!operador` gate, D-12).
- Modificador `⏱ {refYmd}` inalterado, continua depois da frase (D-10). Bloco de números crus ganha o gate `!microtexto && !compacto && (...)` — inalterado no conteúdo, só no gate.
- Call site do `AtivoCard` (Watchlist e Radar, mesmo componente único) passa `microtexto A={A} didatica={didatica} dados={dadosDoCard}`. Cauda do Radar (`<HistoricoPill historico={s.historico} ...>`) intocada — continua sem `microtexto`.
- Nenhuma string da frase é literal no componente (SC#1): grep confirma zero ocorrência de "Critérios ok"/"O padrão bateu os critérios"/o texto de `reconciliacaoPorQueImporta` em `App.jsx`.

## Task Commits

Each task was committed atomically (TDD RED→GREEN):

1. **Task 1 RED:** `d06e4ca` — test(43-04): Parte B do guardiao de reconciliacao — fiacao no App.jsx (RED)
2. **Task 2 GREEN:** `32a5bae8` — feat(43-04): microtexto de reconciliacao por modo na linha de elegibilidade (GREEN)

## Files Created/Modified
- `web/tests/test_reconciliacao_elegibilidade.mjs` — Parte B (fiação no App.jsx): 11 asserções novas
- `web/src/App.jsx` — import de `reconciliacaoTxt`/`reconciliacaoPorQueImporta`; `HistoricoPill` com `microtexto`/`A`/`didatica`/`dados`; call site do `AtivoCard` atualizado

## Decisões autônomas

Nenhuma. O JSX de referência do `43-UI-SPEC.md` (linhas 351-390 para o corpo de `HistoricoPill`, 419-424 para a cláusula tocável) foi usado verbatim — a única adaptação foi a ordem/formatação de espaços para bater com o estilo real do arquivo (identação, quebras de linha), sem alterar nenhuma decisão de conteúdo, gate ou string.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

`npx cap copy ios` reportou `ERROR: failed to copy trust settings of system certificate-25291` repetidamente — mesmo ruído de keychain do sandbox já registrado nos `43-02-SUMMARY.md`/`43-03-SUMMARY.md`; não afeta a cópia dos assets web (`copy ios` terminou com sucesso, `test_ios_assets.mjs` confirma paridade de chunks dist↔ios). `for t in web/tests/*.mjs` redirecionado para `$TMPDIR` (não `/tmp`), evitando o EPERM de sandbox já conhecido dos planos anteriores.

## Validação executada

- `node tests/test_reconciliacao_elegibilidade.mjs` — 41/41 ok (30 Parte A + 11 Parte B)
- `node tests/test_historico_ui.mjs` — 0 falhas
- `node tests/test_historico_setup_card_ui.mjs` — 0 falhas
- `node tests/test_ritmo_sp.mjs` — 0 falhas (zero violação de margin/padding/gap em `HistoricoPill`, incluindo o span novo de microtexto)
- `node tests/test_vocabulario_espelho.mjs` — 0 falhas
- `node tests/test_sinal_chip_ui.mjs` — 0 falhas
- Loop completo `for t in web/tests/*.mjs` (171 arquivos) — `TOTAL_FALHAS=0`
- `npx vite build` — build limpo (warning de chunk >500kB pré-existente, fora do escopo desta fase)
- `npx cap copy ios` — copiado com sucesso; `test_ios_assets.mjs` confirma paridade de chunks dist↔ios após a cópia
- `git diff --stat -- server/` — vazio (plano front-only confirmado)
- Grep dos critérios de aceite do plano (contagens exatas 1/1/1/0) — todos conferem
- Backend pytest — não executado (plano front-only, confirmado pelo `sequential_execution` desta sessão)

## User Setup Required

None - nenhuma configuração externa necessária.

## Next Phase Readiness
- HIER-03 completo: microtexto de reconciliação por modo ligado na linha de elegibilidade, números do `signal_ledger` preservados nas listas por setup, nenhuma string solta no componente.
- Fase 43 fica pronta para o Plano 05 (checkpoint humano + publicação + fechamento de docs) — nenhum trabalho de produto pendente nos requirements HIER-03/CHIP-03/RITMO-01, todos completos entre 43-01..43-04.
- A decisão autônoma pendente de confirmação do Alex (caixa "Sem leitura do motor", registrada no `43-02-SUMMARY.md`) continua aguardando o checkpoint do 43-05 — não é gap funcional desta fase.

---
*Phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo*
*Completed: 2026-09-27*

## Self-Check: PASSED
