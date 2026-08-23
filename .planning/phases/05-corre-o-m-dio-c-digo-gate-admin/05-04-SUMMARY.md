---
phase: 05-corre-o-m-dio-c-digo-gate-admin
plan: 04
subsystem: testing
tags: [bash, npm, ci, adr, testing-strategy]

# Dependency graph
requires: []
provides:
  - "scripts/executar.sh --testes resolve web/node_modules sozinho em checkout/worktree novo"
  - "Falha de teste web imprime a causa (últimas ~20 linhas) em vez de [X] mudo"
  - "docs/adr/018-cobertura-e2e.md — decisão datada sobre não adotar E2E agora, com 4 gatilhos objetivos de reavaliação"
affects: [testing, ci, worktree-onboarding]

# Tech tracking
tech-stack:
  added: []
  patterns: [npm ci com fallback npm install, captura de saída em arquivo temp em vez de /dev/null]

key-files:
  created:
    - docs/adr/018-cobertura-e2e.md
  modified:
    - scripts/executar.sh
    - .planning/codebase/TESTING.md

key-decisions:
  - "FIX-C24: scripts/executar.sh --testes agora checa web/node_modules e instala sozinho (npm ci, fallback npm install), com die() acionável na falha de instalação"
  - "FIX-C24: falha de um teste web agora imprime as últimas ~20 linhas da saída real em vez de um [X] mudo (>/dev/null 2>&1 removido)"
  - "FIX-C27: decisão de NÃO adotar E2E/browser automation agora — Playwright na PWA não cobriria os 3 defeitos caros já registrados no projeto (todos do lado nativo/Capacitor); device harness (XCUITest/Maestro) cobriria, mas custo de infra desproporcional ao estágio atual (um dev, pré-receita)"
  - "FIX-C27: reforça o controle já em uso (guardiões estáticos + checkpoint humano bloqueante nas Fases 7/8 + checklist TESTFLIGHT.md) em vez de abrir infraestrutura de teste nova"

patterns-established:
  - "Pré-requisito de suíte resolvido pelo próprio script (mesmo padrão de scripts/test.sh para o venv em worktree), não documentado como passo manual"

requirements-completed: [FIX-C24, FIX-C27]

# Metrics
duration: ~35min
completed: 2026-08-23
---

# Phase 05 Plan 04: Suíte canônica auto-suficiente + decisão de cobertura E2E Summary

**`scripts/executar.sh --testes` resolve `web/node_modules` sozinho e mostra a causa real de falha web; ADR-018 decide não adotar E2E agora, com 4 gatilhos objetivos de reavaliação.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-08-23T17:41:02Z
- **Tasks:** 2 completed
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments

- FIX-C24 fechado: checkout/worktree novo roda `bash scripts/executar.sh --testes` de ponta a ponta sem passo manual — o script checa `web/node_modules`, instala com `npm ci` (fallback `npm install`) se ausente, e aborta com mensagem acionável se a instalação falhar.
- Falha num teste web deixou de ser um `[X]` mudo: a saída (últimas ~20 linhas) é capturada em arquivo temporário e impressa só no caso de falha; sucesso continua silencioso.
- FIX-C27 fechado: `docs/adr/018-cobertura-e2e.md` registra avaliação com inventário medido (105 arquivos `server/tests/*.py`, 95 `web/tests/*.mjs`), mapeia os 8 passos da Experiência Principal contra a cobertura atual, avalia 3 opções (Playwright/PWA, device harness, não adotar) e decide não adotar agora — com a assimetria decisiva documentada: os 3 defeitos caros já registrados no projeto (sync stop/alvo, orçamento, link Operador) são todos do lado nativo, superfície que Playwright-na-PWA não alcançaria.

## Task Commits

Each task was committed atomically:

1. **Task 1: executar.sh resolve node_modules e para de engolir o erro (FIX-C24)** - `a354ff6` (fix)
2. **Task 2: ADR-018 — avaliação de cobertura E2E (FIX-C27)** - `3b39b84` (docs)

_Nenhuma task TDD neste plano._

## Files Created/Modified

- `scripts/executar.sh` - bloco `--testes`: checa/instala `web/node_modules` antes do laço de testes web; captura saída em arquivo temp e imprime as últimas ~20 linhas só na falha
- `docs/adr/018-cobertura-e2e.md` - avaliação de cobertura E2E, decisão de não adotar agora, 4 gatilhos de reavaliação
- `.planning/codebase/TESTING.md` - nota sobre o comportamento novo de `executar.sh --testes` na seção "Canonical Test Suite"; ponteiro ao ADR-018 na seção "Test Types"

## Decisions Made

- **FIX-C24** — `npm ci` é preferido sobre `npm install` quando `web/package-lock.json` existe (instalação determinística a partir do lockfile versionado), com fallback só se `npm ci` falhar. Nenhuma dependência nova instalada — `web/package.json`/`package-lock.json` ficam inalterados (confirmado via `git diff --name-only`).
- **FIX-C27** — decisão explícita de NÃO adotar Playwright/device-harness agora. Ver seção "Decisão" do ADR-018 para a justificativa completa e a distinção entre "não decidido nunca fazer E2E" e "não é o próximo investimento de teste com melhor retorno hoje".

## Deviations from Plan

None - plan executado exatamente como escrito. As duas tasks seguiram a `<action>` do plano sem necessidade de fix automático (Rule 1-3) ou decisão arquitetural (Rule 4).

## Issues Encountered

Nenhum problema técnico. A prova ao vivo do gap C-24 (mover `web/node_modules`, rodar a suíte, confirmar reinstalação + exit 0) e a prova de que a saída de falha aparece (quebrar temporariamente um `.mjs` com `throw` no topo do arquivo, confirmar texto do erro sob o `[X]`, reverter) foram executadas conforme os critérios de aceite do plano — ambas passaram na primeira tentativa depois de ajustar o teste de falha (a primeira tentativa apendou o `throw` depois de um `process.exit()` já existente no arquivo copiado, que mascarou o erro; corrigido escrevendo um arquivo `.mjs` com `throw` na primeira linha).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Suíte canônica agora é auto-suficiente em qualquer checkout/worktree novo (fecha um gap que já havia mordido as Fases 4, 6, 7 e 8 desta mesma sessão de trabalho). ADR-018 fica como referência para qualquer replanejamento futuro de infraestrutura de teste — os 4 gatilhos de reavaliação (terceiro defeito de regressão financeira, segundo desenvolvedor, cobrança real ligada, checklist manual virando gargalo) são o critério objetivo para reabrir a decisão. Sem blockers para os outros planos da Fase 5 (05-01, 05-02, 05-03, 05-05), que não têm dependência técnica deste plano.

---
*Phase: 05-corre-o-m-dio-c-digo-gate-admin*
*Completed: 2026-08-23*
