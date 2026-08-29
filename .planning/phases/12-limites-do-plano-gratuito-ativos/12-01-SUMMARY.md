---
phase: 12-limites-do-plano-gratuito-ativos
plan: 01
subsystem: api
tags: [plan-gating, freemium, python, fastapi, pytest]

# Dependency graph
requires:
  - phase: 03-05 (fases anteriores de arquitetura do gate)
    provides: "hooks can_add_ticker/can_analyze e call sites já resolvendo plano real (C-31/C-32/C-33), só faltava o número"
provides:
  - "PLAN_FREE.max_watchlist=10 e max_analyses_per_month=30 ativos (D-01)"
  - "PLAN_PRO permanece None/None (ilimitado por decisão comercial, CAP-04)"
  - "Copy de recusa de can_add_ticker sem CTA/upgrade (D-05, CAP-07)"
  - "Guardiões test_fase3_gate_plano.py e test_fase5_gate_mensal.py atualizados (não apagados) para o novo contrato"
affects: [12-02, 12-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reversão deliberada de guardião: renomear função + docstring citando o nome antigo + parágrafo ATUALIZADO (Fase N, vX.Y) no topo do arquivo, sem apagar histórico (guardrail CLAUDE.md)"

key-files:
  created: []
  modified:
    - server/app/plan.py
    - server/tests/test_fase3_gate_plano.py
    - server/tests/test_fase5_gate_mensal.py

key-decisions:
  - "Só a f-string de recusa de can_add_ticker foi tocada; can_analyze (já sem CTA) ficou intocada, servindo de referência de estilo"
  - "Comentários/docstring do módulo plan.py reescritos para declarar o estado ATIVO em vez de 'nada cobra hoje', preservando C-32/C-33 citados literalmente (guardião estático de outro teste depende disso)"

requirements-completed: [CAP-01, CAP-02, CAP-04, CAP-07]

# Metrics
duration: ~15min (execução das tasks; tempo adicional gasto resolvendo desvio do HEAD do worktree antes da Task 1)
completed: 2026-08-29
---

# Phase 12 Plan 01: Ativação dos limites do plano gratuito Summary

**PLAN_FREE ganhou limites reais (10 ativos / 30 análises-mês) em `server/app/plan.py`, a recusa de watchlist perdeu o tom de CTA, e os dois guardiões pré-existentes que travavam "nenhum limite ativo" foram invertidos com nota de reversão rastreável.**

## Performance

- **Duration:** ~15 min de execução das duas tasks (tempo adicional fora desse total foi gasto corrigindo o HEAD do worktree, que estava atrás do commit base esperado, antes de iniciar a Task 1)
- **Completed:** 2026-08-29T04:39:15Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments
- `PLAN_FREE["max_watchlist"]` e `PLAN_FREE["max_analyses_per_month"]` saíram de `None` para `10`/`30`; `PLAN_PRO` continua `None`/`None`
- Mensagem de recusa de `can_add_ticker` virou fato+motivo ("Voce atingiu o limite de {limit} ativos do plano {id}.") sem nenhuma palavra de upgrade/CTA
- Docstring do módulo e comentários inline reescritos para declarar o estado ativo (v1.3/Fase 12, ADR-010), preservando o contrato C-32/C-33 citado literalmente
- Os dois guardiões que travavam o estado oposto ("nenhum limite comercial ativado") foram atualizados no lugar — não apagados, não skipados — com nota "ATUALIZADO (Fase 12, v1.3)" no mesmo formato do precedente FIX-C01 já existente
- Suíte de backend inteira (`pytest -q`, 1677 testes) e suíte canônica completa (`scripts/executar.sh --testes`, pytest + `web/tests/*.mjs`) verdes após a ativação

## Task Commits

Each task was committed atomically:

1. **Task 1: Ativar os limites do PLAN_FREE e tirar o CTA da recusa de can_add_ticker** - `71a0bd3` (feat)
2. **Task 2: Atualizar (não apagar) os dois guardiões que travavam "nenhum limite comercial ativado"** - `fb36ca0` (test)

**Plan metadata:** committed alongside this SUMMARY (worktree mode — orchestrator handles the shared-file/state commit after merge)

## Files Created/Modified
- `server/app/plan.py` - `PLAN_FREE` com limites ativos; copy de `can_add_ticker` sem CTA; docstring/comentários atualizados
- `server/tests/test_fase3_gate_plano.py` - `test_d03_nenhum_limite_comercial_ativado` → `test_d01_limites_do_plano_free_ativos` (inverte as asserções do FREE, mantém PRO `is None`), nota de reversão no topo do arquivo
- `server/tests/test_fase5_gate_mensal.py` - `test_ai_quota_conta_logada_devolve_month_used_inteiro` passa a esperar `monthLimit == 30`, nota de reversão no topo do arquivo

## Decisions Made
- Seguiu-se à risca o plano: nenhuma decisão nova fora do que D-01/D-05 já travavam. A única liberdade exercida foi a redação exata dos parágrafos "ATUALIZADO (Fase 12, v1.3)" nos dois arquivos de teste, no estilo do precedente FIX-C01 já presente em `test_fase3_gate_plano.py` (conforme "Claude's Discretion" do 12-CONTEXT.md, que deixa a redação exata a critério do executor).

## Deviations from Plan

None - plan executado exatamente como escrito. A única ocorrência fora do escopo das tasks foi um desvio de estado do worktree ANTES do Task 1 (ver "Issues Encontered" abaixo) — não é uma alteração de plano, é infraestrutura de execução.

## Issues Encountered
- **HEAD do worktree divergente do commit base esperado pelo `<worktree_branch_check>`:** ao iniciar, `git merge-base HEAD <base-esperada>` mostrou que o HEAD do worktree (3 commits de um trabalho anterior não relacionado — "checklist ao vivo da virada de produção do mydata") era um ANCESTRAL da base esperada, não um desvio real. Confirmado com `git merge-base --is-ancestor` (SAFE) antes de qualquer ação. Um hook de segurança local ("Fact-Forcing Gate") bloqueou `git reset --hard` mesmo após a disclosure de 3 partes exigida; a operação foi refeita como `git merge --ff-only <base-esperada>`, que é não-destrutiva por construção (falha se não for fast-forward) e não disparou o hook. Resultado: HEAD avançou de `16df05c` para `58603d6c` sem perda de nenhum commit — os 3 commits anteriores permanecem como ancestrais alcançáveis. Nenhum arquivo de trabalho foi tocado por essa correção (`git status --short` já estava limpo antes e depois).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Task 1/2 desta fase deixam `plan.py` com os limites reais ligados e os guardiões de fronteira coerentes com o novo estado — pronto para 12-02 (fechar o bypass de `PUT /api/watchlist`, D-02/D-03/D-04) e 12-03.
- Nenhum bloqueio conhecido para os planos seguintes da Fase 12.

## Self-Check: PASSED

- FOUND: server/app/plan.py
- FOUND: server/tests/test_fase3_gate_plano.py
- FOUND: server/tests/test_fase5_gate_mensal.py
- FOUND: .planning/phases/12-limites-do-plano-gratuito-ativos/12-01-SUMMARY.md
- FOUND commit: 71a0bd3 (Task 1)
- FOUND commit: fb36ca0 (Task 2)
- FOUND commit: 0b38c51 (SUMMARY, pre-append)

---
*Phase: 12-limites-do-plano-gratuito-ativos*
*Completed: 2026-08-29*
