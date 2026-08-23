---
phase: 05-corre-o-m-dio-c-digo-gate-admin
plan: 02
subsystem: api
tags: [fastapi, sqlite, metering, admin, finops, rbac]

# Dependency graph
requires:
  - phase: 03-corre-o-alta-gate-comercial
    provides: "arquitetura do gate de plano (_gate_analise, _plano_do_escopo, contrato de contagem em plan.py)"
  - phase: 03-corre-o-alta-gate-comercial
    provides: "audit.record e ADR-013 admin_config_get/set/delete (padrão de override + auditoria)"
provides:
  - "metering.py: ledger MENSAL por usuário (month_used/consume), registro próprio isolado do diário"
  - "metering.alerta_gasto: função pura de alerta preventivo de gasto de IA (desvio % vs média da janela)"
  - "/api/ai/quota expõe monthUsed/monthLimit em nível raiz"
  - "/api/obs/usage e /api/admin/summary expõem alertaGastoIA"
  - "/api/admin/config/ia aceita llmAlertaGastoPct/llmAlertaJanelaDias com validação e auditoria"
affects: [05-07-front-monthUsed-quota, web-admin-custos-alerta]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ledger em registro kv PRÓPRIO por janela temporal (dia/mês) — nunca compartilhar dict que zera em rollover diferente"
    - "Função pura de cálculo (sem conn/I/O) testável offline, separada da orquestração de rota"
    - "Degradação honesta: avaliavel/configurado distintos de acima — nunca inferir 'normal' da ausência de dado"

key-files:
  created:
    - server/tests/test_fase5_gate_mensal.py
    - server/tests/test_fase5_alerta_gasto_ia.py
  modified:
    - server/app/metering.py
    - server/app/main.py

key-decisions:
  - "Acumulado mensal vive em MONTH_SECTION separado do dict diário (SECTION) — evita que a virada de dia apague o mês, mesmo padrão defensivo de _load_global"
  - "can_add_ticker (main.py ~1013) já recebia contagem real antes desta fase — confirmado, nenhuma mudança necessária"
  - "alerta_gasto compara a MESMA grandeza do hard stop (análises gerenciadas/dia via ia_analises_gerenciadas_dia), não tokens — tokens seguem como sparkline separado"
  - "Nenhum limite comercial ativado: PLAN_FREE/PLAN_PRO continuam com max_analyses_per_month=None (ADR-010 permanece decisão de negócio pendente)"
  - "Validação numérica só nos 2 campos novos (llmAlertaGastoPct/llmAlertaJanelaDias) — não retro-valida llmDailyQuota/llmRatePerMin/llmGlobalDailyCap (fora de escopo)"

patterns-established:
  - "Guardião estático (regex no fonte sem comentários) fechando a CLASSE do erro (can_analyze(0 nunca mais volta), não só a instância"
  - "try/except degradando para motivo declarado ('série indisponível') em vez de derrubar a rota inteira quando um banco separado (analytics) falha"

requirements-completed: [FIX-C33, FIX-C38]

duration: ~25min
completed: 2026-08-23
---

# Phase 05 Plan 02: Contagem real do gate de plano + alerta preventivo de gasto de IA Summary

**Ledger mensal dedicado em `metering.py` substitui o `0` hardcoded no gate de análises (FIX-C33); nova função pura `alerta_gasto` compara o gasto de hoje contra a média da janela e alimenta `/api/obs/usage` com um alerta configurável pelo admin, complementar ao hard stop já existente (FIX-C38).**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-08-23T17:41:45Z
- **Tasks:** 3/3 completed
- **Files modified:** 4 (2 novos, 2 editados)

## Accomplishments
- `metering.month_used`/`consume` mantêm o único ledger mensal do app (registro `aiUsageMonth`, isolado do dict diário que zera a cada virada de dia); `_gate_analise` e `/api/ai/quota` passam a lê-lo em vez de um `0` fixo
- `metering.alerta_gasto` — função pura, sem I/O — calcula desvio percentual do gasto de hoje vs média da janela de dias passados, distinguindo "não configurado" de "não avaliável" de "acima do limiar" sem nunca inferir "dentro do normal" na ausência de dado (CLAUDE.md item 4)
- `/api/obs/usage` (consumido também por `/api/admin/summary`) expõe `alertaGastoIA`; `/api/admin/config/ia` ganha `llmAlertaGastoPct`/`llmAlertaJanelaDias` com validação numérica e auditoria, reusando o padrão ADR-013 já existente
- Nenhum limite comercial ativado; nenhuma rota nova criada; guardiões pré-existentes de `test_fase3_gate_plano.py` intactos

## Task Commits

Each task was committed atomically:

1. **Task 1: Ledger mensal em metering.py + gate com contagem real (FIX-C33)** - `c46f533` (feat)
2. **Task 2: Função pura de alerta preventivo de gasto de IA (FIX-C38, cálculo)** - `e86d22b` (feat)
3. **Task 3: Ligar o alerta ao payload de Custos e ao formulário de config (FIX-C38, fios)** - `e7393e5` (feat)

_Nenhuma task usou TDD formal (RED/GREEN) — os 3 arquivos de teste foram escritos junto com a implementação de cada task, cobrindo o `<behavior>` do plano antes do commit._

## Files Created/Modified
- `server/app/metering.py` - `MONTH_SECTION`/`_month`/`_load_month`/`month_used` (ledger mensal); `consume`/`snapshot` estendidos; `alerta_gasto`/`ALERTA_JANELA_PADRAO` (alerta preventivo, função pura)
- `server/app/main.py` - `_gate_analise` usa `metering.month_used`; `/api/ai/quota` expõe `monthUsed`/`monthLimit`; `_CONFIG_IA_CAMPOS` + validação + `_usage_snapshot()` ligam o alerta preventivo
- `server/tests/test_fase5_gate_mensal.py` - 12 testes: ledger mensal (rollover dia/mês, isolamento por escopo, snapshot) + call site do gate (espião) + guardião estático
- `server/tests/test_fase5_alerta_gasto_ia.py` - 18 testes: 11 unitários puros de `alerta_gasto` (Task 2) + 7 de rota (`GET /api/obs/usage`, `PUT /api/admin/config/ia`) (Task 3)

## Decisions Made
- Registro mensal em kv **separado** do diário (`MONTH_SECTION` != `SECTION`) — se compartilhassem o dict, a virada de dia (que `_load` zera sempre) apagaria o acumulado do mês junto. Espelha o padrão defensivo já usado em `_load_global`.
- `alerta_gasto` recebe `hoje` como parâmetro com default `_today()` (UTC, mesma âncora do resto de `metering.py`) — não reconciliado com o fuso BRT usado por `analytics.serie_metrica`/`agent.py` para rotular o campo `day` da série. Na prática, o rollup diário roda 1x/dia e a comparação de string `day == hoje` tolera a janela estreita de divergência (00h–03h UTC = véspera em BRT); não há teste cobrindo esse caso de borda especificamente porque o plano não pediu reconciliação de fuso nesta fase.
- Validação dos 2 campos novos do admin (`llmAlertaGastoPct`/`llmAlertaJanelaDias`) converte para `float`/`int` e persiste o valor JÁ convertido (não o bruto do body) — garante que `metering.alerta_gasto` sempre recebe tipos numéricos reais, nunca strings.

## Deviations from Plan

None - plan executado exatamente como especificado. Os 3 `<acceptance_criteria>` de cada task foram verificados por grep antes do commit (ver comandos no corpo da sessão) e todos bateram.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required. O admin configura o novo alerta pelo formulário já existente (`PUT /api/admin/config/ia`), sem infraestrutura nova.

## Next Phase Readiness
- Backend de FIX-C33/FIX-C38 completo e testado (1355 testes passando na suíte canônica de backend, incluindo os 30 novos deste plano).
- **Pendência explícita para o front** (fora do escopo deste plano, conforme `<interfaces>`): o Plano 05-07 (ou equivalente) precisa consumir `monthUsed`/`monthLimit` de `/api/ai/quota` no `web/src/App.jsx` — o espelho front do call site hardcoded (`App.jsx:6627` na auditoria original) continua sem tocar até esse plano rodar.
- **Pendência explícita para o portal admin** (`web-admin/`): a aba Custos ainda não lê `alertaGastoIA` de `/api/obs/usage` nem expõe o formulário para `llmAlertaGastoPct`/`llmAlertaJanelaDias` — o contrato do backend está pronto e testado, mas a UI do painel não foi tocada neste plano (fora do `files_modified` declarado no frontmatter).
- Nenhum bloqueio para os demais planos da Fase 5 (05-01, 05-03, 05-04, 05-05) — sem overlap de arquivo.

---
*Phase: 05-corre-o-m-dio-c-digo-gate-admin*
*Completed: 2026-08-23*
