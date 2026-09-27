---
phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
plan: 01
subsystem: ui
tags: [copy, vocabulario, skill_ref, i18n-modo, hier-03, chip-03]

# Dependency graph
requires:
  - phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura
    provides: "SinalChip peso=contexto/primario, ordem de leitura do AtivoCard, sinal.js"
provides:
  - "RECONCILIACAO_ELEGIBILIDADE + reconciliacao_elegibilidade_txt em server/app/skill_ref.py (HIER-03)"
  - "COPY.estudo/operador.reconciliacaoElegibilidade + reconciliacaoTxt + reconciliacaoPorQueImporta em web/src/copy.js"
  - "sinal.leituraIa (rótulo, campos, aria) nos dois modos de copy.js (CHIP-03)"
  - "guardião cruzado skill_ref.py ↔ copy.js estendido para RECONCILIACAO_ELEGIBILIDADE"
  - "guardião comportamental novo web/tests/test_reconciliacao_elegibilidade.mjs"
affects: [43-03, 43-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Vocabulário por modo/estado em skill_ref.py com fallback duplo (modo→educacional, estado→nunca_medido), espelhado byte a byte em copy.js — mesmo padrão de HISTORICO/historico_txt"
    - "expR formatado com sinal explícito (+ ou U+2212), 3 casas, vírgula; ausência (None/null) vira '?', nunca '0' — regra da casa"

key-files:
  created:
    - web/tests/test_reconciliacao_elegibilidade.mjs
  modified:
    - server/app/skill_ref.py
    - server/tests/test_skill_ref.py
    - web/src/copy.js
    - web/tests/test_vocabulario_espelho.mjs

key-decisions:
  - "Nenhuma - plano seguido como especificado (código já travado no 43-UI-SPEC.md, verbatim)"

patterns-established:
  - "sinal.leituraIa: objeto idêntico nos dois modos (rótulo de seção, não interpretação) dentro de COPY.*.sinal — precedente para futuros rótulos comuns aos dois modos"

requirements-completed: [HIER-03, CHIP-03]

# Metrics
duration: ~25min
completed: 2026-09-27
---

# Phase 43 Plan 01: Vocabulário de reconciliação HIER-03 + rótulos CHIP-03 Summary

**Dict `RECONCILIACAO_ELEGIBILIDADE` + função espelhada em `skill_ref.py`↔`copy.js` para o microtexto "sinal técnico × histórico medido", mais os rótulos "LEITURA DA IA"/DIREÇÃO/CONVICÇÃO/QUALIDADE em `copy.js` — sem tocar `App.jsx`.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2 completadas (ambas TDD RED→GREEN)
- **Files modified:** 4 (+ 1 criado)

## Accomplishments
- `RECONCILIACAO_ELEGIBILIDADE`, `RECONCILIACAO_POR_QUE_IMPORTA` e `reconciliacao_elegibilidade_txt(modo, estado, n, janela, exp_r)` em `server/app/skill_ref.py`, com 8 testes novos (29 total no arquivo, todos verdes)
- Espelho em `web/src/copy.js`: `COPY.estudo/operador.reconciliacaoElegibilidade`, `reconciliacaoTxt(mode, estado, vals)`, `reconciliacaoPorQueImporta` (export solto), e `sinal.leituraIa` nos dois modos
- Guardião cruzado (`test_vocabulario_espelho.mjs`) estendido com `RECONCILIACAO_ELEGIBILIDADE` — paridade byte a byte confirmada
- Guardião comportamental novo (`test_reconciliacao_elegibilidade.mjs`) cobrindo formatação de expR (sinal U+2212, 3 casas), fallback de modo/estado, e os rótulos/aria da Leitura da IA
- `App.jsx` intocado (confirmado por grep: `reconciliacao|leituraIa` = 0 ocorrências)

## Task Commits

Each task was committed atomically (TDD RED→GREEN):

1. **Task 1 RED:** `a870222` — test(43-01): guardiões RED para reconciliação sinal técnico × histórico medido
2. **Task 1 GREEN:** `faa2606` — feat(43-01): RECONCILIACAO_ELEGIBILIDADE e reconciliacao_elegibilidade_txt em skill_ref.py
3. **Task 2 RED:** `6ee34b6` — test(43-01): guardiões RED do espelho JS de reconciliação e Leitura da IA
4. **Task 2 GREEN:** `239ebad` — feat(43-01): reconciliacaoTxt, reconciliacaoPorQueImporta e sinal.leituraIa em copy.js

**Plan metadata:** (este commit, docs de fechamento do plano)

## Files Created/Modified
- `server/app/skill_ref.py` - dict `RECONCILIACAO_ELEGIBILIDADE`, constante `RECONCILIACAO_POR_QUE_IMPORTA`, função `reconciliacao_elegibilidade_txt`
- `server/tests/test_skill_ref.py` - 8 testes novos (chaves espelhadas, interpolação, sinal negativo, fallback, ban-list, cláusula fixa)
- `web/src/copy.js` - `reconciliacaoElegibilidade` nos dois modos, `sinal.leituraIa` nos dois modos, `reconciliacaoTxt`, `reconciliacaoPorQueImporta`
- `web/tests/test_vocabulario_espelho.mjs` - `RECONCILIACAO_ELEGIBILIDADE` entra em `DICTS`/`CHAVE_JS`/`CHAVES_ESPERADAS`
- `web/tests/test_reconciliacao_elegibilidade.mjs` (novo) - guardião comportamental de `reconciliacaoTxt`/`reconciliacaoPorQueImporta`/`sinal.leituraIa`

## Decisões autônomas

Nenhuma. Todo o texto e código foi implementado verbatim conforme já travado no `43-UI-SPEC.md` (linhas 252-322 para o backend, 304-330 para o espelho JS) e no `43-PATTERNS.md`; nenhuma ambiguidade exigiu decisão do executor fora do que o plano especificava.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Suíte canônica completa (pytest fora do sandbox, `.mjs` completos) não foi rodada nesta sessão — fora do escopo deste plano isolado; os comandos de `<verify>`/`<verification>` especificados no 43-01-PLAN.md rodaram todos verdes (pytest de `test_skill_ref.py`, os dois guardiões `.mjs` do plano, e `test_historico_ui.mjs` como smoke adicional). O ambiente sandbox não apresentou o erro de rede/SSL conhecido porque nenhum teste desta suíte específica depende de rede.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `reconciliacaoTxt`/`reconciliacaoPorQueImporta`/`sinal.leituraIa` prontos para o 43-03/43-04 fiarem em `HistoricoPill`/`AnalysisView` — nenhum vocabulário novo precisa ser criado nesses planos, só consumido
- Guardião cruzado já cobre o dict novo; qualquer edição futura em `RECONCILIACAO_ELEGIBILIDADE` sem espelho em `copy.js` quebra `test_vocabulario_espelho.mjs`

---
*Phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo*
*Completed: 2026-09-27*

## Self-Check: PASSED

