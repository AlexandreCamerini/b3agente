---
phase: 05-corre-o-m-dio-c-digo-gate-admin
plan: 07
subsystem: ui
tags: [react, persistence, gate, plan-js, guardian-test, deviceStore, serverStore]

# Dependency graph
requires:
  - phase: 05-corre-o-m-dio-c-digo-gate-admin
    provides: "Plano 05-02 — contrato monthUsed/monthLimit em nível raiz de GET /api/ai/quota"
  - phase: 03-corre-o-alta-gate-comercial
    provides: "FIX-C30 — qualificador de degradado no TechnicalModal, Copywriting Contract (não expor orçamento/cota/limite ao usuário final)"
provides:
  - "web/src/persistence.js: analisesNoMes() nos dois stores (serverStore e deviceStore), mesmo contrato, lendo monthUsed do ledger do servidor"
  - "web/src/App.jsx: A.analyze usa a contagem real do mês (falha-aberta documentada) em vez de canAnalyze(0) hardcoded"
  - "web/tests/test_fase5_gate_mensal_front.mjs — guardião estático do hardcode + paridade de método"
  - "web/tests/test_fase5_c34_orcamento_nao_vaza.mjs — guardião de CONFIRMAÇÃO de FIX-C34 (não feature nova)"
affects: [FIX-C33, FIX-C34, web/src/App.jsx, web/src/persistence.js]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Falha-aberta documentada no call site: pré-check de UX do cliente não é o gate autoritativo — o servidor decide na mesma requisição"
    - "Guardião de vizinhança textual (janela de N caracteres em torno de uma string âncora) para provar ausência de vazamento de informação, não só presença de comportamento"

key-files:
  created:
    - web/tests/test_fase5_gate_mensal_front.mjs
    - web/tests/test_fase5_c34_orcamento_nao_vaza.mjs
  modified:
    - web/src/persistence.js
    - web/src/App.jsx

key-decisions:
  - "analisesNoMes() nos dois stores NÃO mantém contador próprio — lê o MESMO endpoint (api.aiQuota()) que já expõe monthUsed, seguindo o contrato de plan.py de que a contagem tem de vir do ledger de metering, nunca de um segundo contador paralelo"
  - "Falha-aberta explícita: erro/null na leitura de analisesNoMes() faz A.analyze seguir com usedThisMonth=0, comentado no código como aceitável porque o gate AUTORITATIVO (_gate_analise, servidor) roda na mesma requisição de análise — bloquear a análise por uma leitura de cota que não respondeu seria pior UX que o pré-check falhar aberto"
  - "canAddTicker (linha ~7618) não foi tocado — já recebia (data.watchlist || []).length antes da fase; essa metade de FIX-C33 já estava correta, confirmado e registrado em guardião"
  - "FIX-C34 fechado por CONFIRMAÇÃO, não por feature nova — nenhuma UI de medidor de orçamento construída; o Success Criteria 4 do ROADMAP (pré-datava a entrega de FIX-C30) foi formalmente superado pelo Copywriting Contract da Fase 3, registro escrito no cabeçalho do guardião novo"
  - "Nenhum limite comercial ativado — plan.js segue com maxAnalysesPerMonth: null nos dois planos (ADR-010 continua decisão de negócio pendente do Alex), travado por guardião"

patterns-established:
  - "Guardião estático fechando a CLASSE do erro (canAnalyze(0 nunca mais volta), não só a instância — mesmo padrão dos guardiões anteriores da fase (test_fase5_appmode_fonte_unica.mjs, test_fase3_fonte_technicals.mjs)"

requirements-completed: [FIX-C33, FIX-C34]

# Metrics
duration: ~45min
completed: 2026-08-23
---

# Phase 05 Plan 07: Gate mensal real no front + confirmação de FIX-C34 Summary

**`analisesNoMes()` nos dois stores lê `monthUsed` do ledger do servidor (mesmo endpoint de `aiQuota()`, sem contador paralelo no aparelho); `A.analyze` substitui `canAnalyze(0)` hardcoded por essa contagem real com falha-aberta documentada; FIX-C34 fechado por confirmação (sem UI nova) de que o Copywriting Contract da Fase 3 segue sem vazar orçamento/cota/limite ao usuário final.**

## Performance

- **Duration:** ~45 min
- **Completed:** 2026-08-23T18:18:55Z
- **Tasks:** 2/2 completed
- **Files modified:** 2 (persistence.js, App.jsx) + 2 criados (guardiões .mjs)

## Accomplishments
- `serverStore.analisesNoMes()` e `deviceStore.analisesNoMes()` (mesmo contrato: `async () => Promise<number|null>`) leem `monthUsed` de `api.aiQuota()` — mesmo endpoint que o Plano 05-02 já preparou no backend, sem contador local paralelo no aparelho (comentário explícito no código citando o contrato de `plan.py`)
- `A.analyze` em `App.jsx` troca `canAnalyze(0) // FUTURO: passar contagem do mês` por uma leitura real com `try/catch` — erro ou `null` degrada para `0`, documentado como aceitável porque `_gate_analise` no servidor é o gate autoritativo, não este pré-check de UX
- `canAddTicker` (linha ~7618) confirmado intocado — já passava `(data.watchlist || []).length` antes da fase, essa metade de FIX-C33 já estava correta
- FIX-C34 fechado por CONFIRMAÇÃO: nenhuma UI de medidor de orçamento construída (decisão já tomada no 05-CONTEXT.md, verificada contra `03-01-SUMMARY.md`); guardião novo prova que o qualificador de degradado continua sem mencionar orçamento/cota/limite/% na vizinhança textual, e que os números de orçamento em `FonteDadosScreen` continuam admin-only (`adminDenied`)
- 2 guardiões novos, ambos com prova negativa executada e revertida (mutação temporária confirmada quebrando o teste, revertida via `mv`/patch inverso, `git diff --stat` vazio depois)

## Task Commits

Each task was committed atomically:

1. **Task 1: analisesNoMes() nos DOIS stores + call site do gate (FIX-C33 front)** - `213bf24` (fix)
2. **Task 2: Guardião do gate no front + confirmação de FIX-C34** - `610e7af` (test)

_Nenhuma task usou TDD formal (RED/GREEN) — os testes da Task 2 foram escritos após a implementação da Task 1, cobrindo o comportamento já implementado, no mesmo padrão dos guardiões estáticos anteriores da fase._

## Files Created/Modified
- `web/src/persistence.js` - `analisesNoMes()` acrescentado ao `serverStore` (linha ~228, arrow property) e ao `deviceStore` (linha ~1029, método shorthand com `ensure()`), ambos delegando para `api.aiQuota().monthUsed`
- `web/src/App.jsx` - `A.analyze` (linha ~7159): leitura real de `store.analisesNoMes()` com falha-aberta comentada, substitui `canAnalyze(0)`; comentário morto "FUTURO: passar contagem do mês" removido
- `web/tests/test_fase5_gate_mensal_front.mjs` (novo) - 6 asserções: hardcode `canAnalyze(0` ausente (sem comentários), `canAnalyze` chamado com identificador, comentário morto ausente, `analisesNoMes` com exatamente 2 definições em `persistence.js`, `maxAnalysesPerMonth: null` 2x em `plan.js`, `canAddTicker` intocado
- `web/tests/test_fase5_c34_orcamento_nao_vaza.mjs` (novo) - 10 asserções: qualificador de degradado 1x/condicionado/T.warn (duplicando as invariantes de `test_fase3_fonte_technicals.mjs` de propósito), vizinhança de ±200 chars sem orçamento/cota/limite/%, números de orçamento vindos de `admin.usoIA`, seção gateada por `adminDenied`; cabeçalho registra a supersessão do Success Criteria 4 do ROADMAP

## Decisions Made
- Ver `key-decisions` no frontmatter — resumo: sem contador paralelo no aparelho, falha-aberta documentada no pré-check, `canAddTicker` confirmado (não tocado), FIX-C34 fechado por confirmação (sem UI nova, supersessão do ROADMAP registrada), nenhum limite comercial ativado.

## Deviations from Plan

None - plan executado exatamente como especificado. Os `<acceptance_criteria>` de cada task foram verificados por grep e pela suíte canônica completa antes de cada commit.

## Issues Encountered

- `web/node_modules` ausente no worktree novo (mesmo gap C-24 já documentado, recorrente em toda fase que usa worktree) — resolvido com `npm install` em `web/` antes de `npx vite build`/`bash scripts/executar.sh --testes`.
- `server/.venv` ausente no worktree (git-worktree não replica venvs locais) — não exigiu intervenção manual: `scripts/test.sh` já resolve automaticamente o venv do clone principal via `git rev-parse --git-common-dir` (mesmo mecanismo documentado na Issue do Plano 05-05, já corrigido antes desta execução).
- Worktree nasceu com `HEAD` ancestral do commit base esperado (`1beded5db...`) em vez de nele — corrigido com `git reset --hard` (fast-forward seguro, confirmado sem commits divergentes antes de aplicar) na etapa de verificação inicial do executor, antes de qualquer edição.

## User Setup Required

None - nenhuma configuração de serviço externo necessária.

## Next Phase Readiness
- FIX-C33 (front) e FIX-C34 fechados, prontos para o merge da Wave 2 da Fase 5.
- `bash scripts/executar.sh --testes` passa (1365 testes backend + 1 skip + suíte web completa, incluindo os 2 guardiões novos deste plano) e `cd web && npx vite build` conclui sem erro.
- Nenhum bloqueio para o plano irmão da Wave 2 (05-06) — sem overlap de arquivo declarado (05-06 não toca `persistence.js`/`App.jsx`/os 2 `.mjs` novos deste plano).
- FIX-C33 (backend, Plano 05-02) e FIX-C33 (front, este plano) agora fecham a lacuna estrutural completa: quando o número comercial do ADR-010 for populado, o gate funciona corretamente desde o primeiro dia, nos dois lados.

---
*Phase: 05-corre-o-m-dio-c-digo-gate-admin*
*Completed: 2026-08-23*

## Self-Check: PASSED

- FOUND: web/src/persistence.js
- FOUND: web/src/App.jsx
- FOUND: web/tests/test_fase5_gate_mensal_front.mjs
- FOUND: web/tests/test_fase5_c34_orcamento_nao_vaza.mjs
- FOUND: .planning/phases/05-corre-o-m-dio-c-digo-gate-admin/05-07-SUMMARY.md
- FOUND commit: 213bf24 (Task 1)
- FOUND commit: 610e7af (Task 2)
