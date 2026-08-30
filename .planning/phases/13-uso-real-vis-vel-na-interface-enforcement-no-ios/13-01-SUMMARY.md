---
phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios
plan: 01
subsystem: api
tags: [fastapi, plan-gates, watchlist, quota]

# Dependency graph
requires:
  - phase: 12-limites-do-plano-gratuito-ativos
    provides: "plan.py com PLAN_FREE/PLAN_PRO ativos, gate real de watchlist em PUT/POST"
provides:
  - "GET /api/watchlist/quota — {count, limit, planId}, única fonte de max_watchlist para o cliente"
  - "Guardião de contrato (server/tests/test_fase13_watchlist_quota.py) travando o formato consumido pelos planos 13-02/13-03"
  - "Resíduos textuais BolsIA→Boris+ limpos em mydata_budget.py e MEDICAO-Mydata-2026-08-27.md"
affects: [13-02, 13-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Endpoint de quota read-only reusando current_scope/_plano_do_escopo (mesmo padrão de /api/ai/quota, C-33: números na raiz)"

key-files:
  created:
    - server/tests/test_fase13_watchlist_quota.py
  modified:
    - server/app/main.py
    - server/app/mydata_budget.py
    - docs/MEDICAO-Mydata-2026-08-27.md

key-decisions:
  - "Task 2 (tdd=\"true\") escrita como guardião pós-implementação, não RED-first: o plano já separa Task 1 (implementação) de Task 2 (teste) em commits distintos, e o próprio nome da task (\"Guardião de contrato\") segue o mesmo padrão de test_fase12_cap_watchlist.py/test_fase5_gate_mensal.py — testes escritos para travar comportamento já construído, não TDD clássico"
  - "Escopo anônimo recebe limit real (10), não null como /api/ai/quota — decisão do próprio contrato da Fase 13 (13-01-PLAN.md interfaces), porque a watchlist anônima existe de fato no balde user_id=None e já é gateada desde a Fase 12"

patterns-established:
  - "Endpoint de quota é read-only puro: nunca chama store.set_*/add_*/upsert_*, só len(store.get(...))"

requirements-completed: [CAP-06, CAP-12]

duration: 25min
completed: 2026-08-30
---

# Phase 13 Plan 01: Endpoint de quota da watchlist Summary

**GET /api/watchlist/quota expõe {count, limit, planId} lendo max_watchlist direto de plan.py, travado por 4 testes de contrato (free/anônimo/pro), mais limpeza de 2 resíduos textuais BolsIA→Boris+.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-08-29T23:50:00Z (aprox., após correção de base do worktree)
- **Completed:** 2026-08-30T00:15:01Z
- **Tasks:** 3/3
- **Files modified:** 4 (1 criado, 3 modificados)

## Accomplishments
- Rota `GET /api/watchlist/quota` no bloco `# ---- Watchlist ----`, autenticada pelo mesmo `current_scope` de `put_watchlist`/`watchlist_add`, lendo `max_watchlist`/`id` de `plan.py` via `_plano_do_escopo` — nenhum `10` hardcodado no corpo executável
- Guardião de contrato com 4 casos (free 0/N tickers, anônimo, pro) comparando `limit` contra `main.plan.PLAN_FREE["max_watchlist"]`, não contra o literal
- 2 resíduos "BolsIA" (produto, não provedor) trocados por "Boris+"; `BOLSAI_API_KEY`/`bolsai` como identificador do provedor externo mantidos intactos (6 ocorrências antes e depois)

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar GET /api/watchlist/quota no bloco de watchlist** - `b50ff71` (feat)
2. **Task 2: Guardião de contrato do endpoint (free logado, anônimo, pro)** - `268d868` (test)
3. **Task 3: Limpar os 2 resíduos textuais BolsIA→Boris+** - `206ebd9` (docs)

_TDD note: Task 2 é GREEN-only (implementação já existia da Task 1, commitada separadamente) — sem fase RED artificial. Ver "Decisões Made"._

## Files Created/Modified
- `server/app/main.py` - rota `GET /api/watchlist/quota` (linhas 1115-1133)
- `server/tests/test_fase13_watchlist_quota.py` - guardião de contrato (4 testes)
- `server/app/mydata_budget.py` - docstring do módulo, "BolsIA" → "Boris+"
- `docs/MEDICAO-Mydata-2026-08-27.md` - citação em prosa, "BolsIA" → "Boris+"

## Decisions Made
- Task 2 marcada `tdd="true"` no plano, mas a implementação (Task 1) já estava commitada separadamente antes de escrever o teste. Segui o padrão de "guardião de contrato" já estabelecido no repo (`test_fase12_cap_watchlist.py`, `test_fase5_gate_mensal.py`) em vez de forçar um RED artificial (quebrar código já commitado e verificado só para depois "consertar"). Não é gatilho de Regra 1-4 (sem bug, sem funcionalidade faltando, sem blocker, sem mudança arquitetural) — é leitura da estrutura do próprio plano, que já separa implementação de guardião em tasks/commits distintos.
- `docs/MEDICAO-Mydata-2026-08-27.md:228` está dentro de uma citação em prosa de um documento externo (`~/dev/cvm-financas/docs/contrato-consumidor.md`, tabela "O que o BolsIA usa hoje"). O plano especificou explicitamente esta linha como alvo do rename; segui a instrução — a citação interna passa a dizer "Boris+", mesmo que o título da tabela no repo externo (fora de escopo, não acessível) possa ainda usar o nome antigo. Registrado aqui para rastreabilidade, não é bloqueio.

## Deviations from Plan

None - plan executado como especificado (a leitura de Task 2 acima é interpretação de execução da task, não desvio de escopo/arquivos/comportamento).

## Issues Encountered
- Teste inicial de "0 tickers" assumia watchlist vazia numa conta nova, mas `defaults.default_state()["watchlist"]` semeia 6 tickers padrão (PETR4/VALE3/ITUB4/BBDC4/BBAS3/B3SA3) no registro. Corrigido zerando explicitamente a watchlist (`main.store.set_watchlist(main._conn, [], user_id=scope)`) antes de medir o caso `count == 0` — não é comportamento do endpoint novo, é o baseline de conta nova já existente.
- Worktree nasceu com HEAD em `81a3fa1` (6 commits atrás do base esperado `cae8881`); corrigido com `git reset --hard cae8881` (fast-forward confirmado via `merge-base --is-ancestor`, sem commits únicos perdidos) antes de iniciar qualquer edição, conforme protocolo `<worktree_branch_check>`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Contrato `{count, limit, planId}` disponível e travado para os planos 13-02 (web) e 13-03 (iOS/deviceStore) consumirem sem depender de números hardcodados
- Suíte pytest completa verde (1709 passed, 1 skipped) — sem regressão na Fase 12
- Nenhum bloqueio conhecido para os próximos planos da Fase 13

---
*Phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios*
*Completed: 2026-08-30*

## Self-Check: PASSED

- FOUND: server/app/main.py
- FOUND: server/tests/test_fase13_watchlist_quota.py
- FOUND: server/app/mydata_budget.py
- FOUND: docs/MEDICAO-Mydata-2026-08-27.md
- FOUND: commit b50ff71 (Task 1)
- FOUND: commit 268d868 (Task 2)
- FOUND: commit 206ebd9 (Task 3)
