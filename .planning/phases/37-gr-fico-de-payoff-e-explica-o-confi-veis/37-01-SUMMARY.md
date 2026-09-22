---
phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis
plan: 01
subsystem: api
tags: [fastapi, options-mcp, payoff, adapter, pytest]

# Dependency graph
requires:
  - phase: 36-motor-de-payoff-genrico
    provides: "opcoes_payoff.dominio_da_curva()/segmentos_da_curva() (D-05/D-06), em produção sem consumidor"
provides:
  - "_perfil_para_curva()/_dominio_e_segmentos() em options_mcp_api.py — adaptador EN->PT rename-only"
  - "dominio/segmentos no envelope JSON de POST /api/options/mcp/proposta e POST /api/options/mcp/possibilidades"
affects: [37-02, 37-04, 37-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Adaptador EN->PT rename-only (mesma disciplina de estruturaParaPayoff.js, sentido inverso) — guardado por regex estática sobre inspect.getsource()"
    - "Guarda de entrada degenerada no adaptador (pernas/curva vazias -> None,[]) em vez de deixar ValueError das funções da Fase 36 estourar"

key-files:
  created: []
  modified:
    - server/app/options_mcp_api.py
    - server/tests/test_options_mcp_api.py

key-decisions:
  - "dominio/segmentos seguem a MESMA regra de ambiguidade de emReais/razaoGanhoPerda: só existem com exatamente uma estrutura (proposta) ou por item avaliado (possibilidades) — nunca com duas estruturas na tela"
  - "possibilidades() reusa o dict `estrutura` já filtrado por CHAVES_DA_ESTRUTURA (não relê avaliacao bruto) para computar dominio/segmentos"

requirements-completed: [CHART-04]

# Metrics
duration: 27min
completed: 2026-09-21
---

# Phase 37 Plan 01: Adaptador EN->PT + domínio/segmentos do payoff via MCP Summary

**Adaptador rename-only (`_perfil_para_curva`/`_dominio_e_segmentos`) liga `POST /api/options/mcp/proposta` e `POST /api/options/mcp/possibilidades` a `opcoes_payoff.dominio_da_curva()`/`segmentos_da_curva()` (Fase 36), fechando CHART-04 — domínio X/Y do gráfico agora calculado no backend, nunca localmente pelo `PayoffChart.jsx`.**

## Performance

- **Duration:** 27 min (commits `9e6fd72` → `dbe5a6b`)
- **Started:** 2026-09-21T22:52:42-03:00 (aprox., primeiro commit de task)
- **Completed:** 2026-09-21T22:59:40-03:00
- **Tasks:** 2/2 completed
- **Files modified:** 2

## Accomplishments
- `_perfil_para_curva()` traduz `legs`/`max_gain`/`max_loss`/`unlimited_gain`/`unlimited_loss`/`payoff` (envelope EN do serviço MCP) para `pernas`/`ganho_maximo`/`perda_maxima`/`ganho_ilimitado`/`perda_ilimitada`/`curva` (formato PT que `opcoes_payoff.py` já aceita) — zero aritmética, confirmado por leitura e por guardião estático
- `_dominio_e_segmentos()` chama `dominio_da_curva()`/`segmentos_da_curva()` VERBATIM e devolve o resultado em camelCase (`xMin`/`xMax`/`yMin`/`yMax`/`margem`/`spot`/`ganhoIlimitado`/`perdaIlimitada`/`motivo` + `de`/`ate`/`inclinacao`/`ePlato` por segmento), com guarda própria para pernas/curva vazias (evita `ValueError` não tratada, T-37-01)
- `dominio`/`segmentos` anexados a `POST /api/options/mcp/proposta` (uma estrutura só) e a cada item de `POST /api/options/mcp/possibilidades` (uniforme nos 3 ramos: estrutura avaliada, sem estrutura, erro de tool)
- Caso golden da Fase 36 (trava de alta 49,17/49,67, débito 0,25) provado pela rota MCP com os MESMOS números do motor local (`margem=1.976`, `xMin=47.194`, `xMax=51.646`, `yMax=0.2875`, `yMin=-0.2875`, 3 segmentos com fronteira nos strikes, não no breakeven)

## Task Commits

Each task was committed atomically:

1. **Task 1: Adaptador EN→PT + wiring de dominio/segmentos em proposta()/possibilidades()** - `9e6fd72` (feat)
2. **Task 2: Testes do adaptador (pytest) + guardião estático de zero-aritmética** - `dbe5a6b` (test)

_Sem plano de metadata separado — SUMMARY é o commit final desta sessão de execução._

## Files Created/Modified
- `server/app/options_mcp_api.py` - `_perfil_para_curva()`/`_dominio_e_segmentos()` (import `opcoes_payoff` adicionado); `proposta()` e `possibilidades()` passam a anexar `dominio`/`segmentos` ao envelope de retorno
- `server/tests/test_options_mcp_api.py` - 8 testes novos: forma das 9 chaves de `dominio`/4 de cada `segmento`, regra de ambiguidade (proposta com 1×2 estruturas), caso golden número a número via rota MCP, forma uniforme `None`/`[]` nos ramos sem estrutura/erro de tool, guardião estático de zero-aritmética + sanidade da regex

## Decisions Made
- Regra de ambiguidade de `dominio`/`segmentos` em `proposta()` replica EXATAMENTE a de `emReais`/`razaoGanhoPerda` (só com uma estrutura) — nenhuma decisão nova, aplicação do padrão já existente no arquivo.
- `possibilidades()` computa `dominio`/`segmentos` a partir do dict `estrutura` já filtrado por `CHAVES_DA_ESTRUTURA` (não relê `avaliacao` bruto de novo) — evita uma segunda fonte de verdade para o mesmo dado dentro da mesma função.

## Deviations from Plan

None - plan executed exactly as written. As duas funções, o wiring nos dois endpoints e os testes seguiram a especificação linha a linha do `37-01-PLAN.md` (incluindo os nomes de campo, a régua de ambiguidade e a técnica de guardião estático).

## Issues Encountered

**Sandbox de execução mentiu em 27 testes durante a primeira rodada da suíte canônica completa** (`test_benchmark_ibov.py`, `test_fase3_kill_switch_duracao.py`, `test_yahoo_*`, etc. — todos fora do escopo deste plano, chamadas httpx mockadas). Reproduzido fora do sandbox (`dangerouslyDisableSandbox`): 2968 passed/5 skipped/3 xfailed/0 failed — confirma que as 27 falhas eram artefato do sandbox, não regressão real (mesmo padrão documentado em `worktree-test-setup.md`, "sandbox mente").

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `dominio`/`segmentos` já chegam prontos (camelCase, calculados pela Fase 36) em `POST /api/options/mcp/proposta` e `POST /api/options/mcp/possibilidades` — a Fase 37 Plano 04 (`PayoffChart.jsx`) pode consumir esses campos em vez de recalcular domínio localmente (o achado original de CHART-04).
- Nenhum bloqueio conhecido. Suíte canônica completa (fora do sandbox): 2968 pytest passed/5 skipped/3 xfailed + 154/154 `web/tests/*.mjs`, `npx vite build` não exigido (nenhum arquivo `web/src/` tocado neste plano).

---
*Phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis*
*Completed: 2026-09-21*

## Self-Check: PASSED

- FOUND: server/app/options_mcp_api.py
- FOUND: server/tests/test_options_mcp_api.py
- FOUND: .planning/phases/37-gr-fico-de-payoff-e-explica-o-confi-veis/37-01-SUMMARY.md
- FOUND commit: 9e6fd72 (Task 1)
- FOUND commit: dbe5a6b (Task 2)
- FOUND commit: b2e5512 (docs: summary)
