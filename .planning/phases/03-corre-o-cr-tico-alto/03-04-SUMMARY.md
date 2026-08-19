---
phase: 03-corre-o-cr-tico-alto
plan: 04
subsystem: api
tags: [fastapi, gating-comercial, plan, metering, adr-013, adr-010]

# Dependency graph
requires:
  - phase: 03-01
    provides: "main.py com _degradado_spot e o restante da linha de base pós-fase-2/3-01 (correções críticas de fonte de dado)"
provides:
  - "current_plan(user) deixa de ser código órfão — os 3 call sites de gate resolvem o plano REAL da conta logada"
  - "_plano_do_escopo(scope): helper fail-closed (falha de banco/ausência de sessão degrada pro plano MENOS privilegiado)"
  - "_gate_analise(scope, config, custo): ponto ÚNICO de decisão de gate de análise por requisição (plano + metering, precedência explícita)"
  - "plan.py com contrato escrito: metering.py é o contador único de uso de IA; can_analyze nunca mantém contagem própria"
  - "guardião de backend server/tests/test_fase3_gate_plano.py (12 testes)"
affects: [fase-5-adr-010-ativacao-comercial, C-33-contagem-mensal-real]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ponto único de decisão de gate por requisição (_gate_analise) em vez de dois mecanismos independentes coexistindo na mesma chamada"
    - "Helper fail-closed com try/except -> fallback menos privilegiado (nunca escala privilégio em falha)"

key-files:
  created:
    - server/tests/test_fase3_gate_plano.py
    - .planning/phases/03-corre-o-cr-tico-alto/deferred-items.md
  modified:
    - server/app/main.py
    - server/app/plan.py

key-decisions:
  - "D-03 (03-CONTEXT.md): corrigir só a ARQUITETURA do gating, sem ativar limite comercial — PLAN_FREE/PLAN_PRO seguem com todos os limites None"
  - "_gate_analise substitui o par (plan.can_analyze + raise 402) + _ai_apply_managed nas 2 rotas de análise, preservando a ordem de captura do appMode ANTES do managed (FASE 8B)"

patterns-established:
  - "Pattern 1: gate comercial sempre resolvido server-side via _plano_do_escopo(scope) a partir do Bearer token — nunca de um campo do corpo da requisição"
  - "Pattern 2: contrato de contagem escrito no docstring do módulo (plan.py) para travar por texto que metering é o contador único, mesmo antes do limite ser ativado"

requirements-completed: [FIX-C31, FIX-C32]

# Metrics
duration: ~30min
completed: 2026-08-18
---

# Phase 03 Plan 04: Gating comercial (C-31/C-32) Summary

**`current_plan(user)` deixa de ser código órfão nos 3 call sites de gate, e um único `_gate_analise` substitui os dois mecanismos de contagem (plan + metering) que coexistiam na mesma requisição — zero limite comercial ativado.**

## Performance

- **Duration:** ~30 min (inclui recuperação de worktree desatualizado via merge)
- **Completed:** 2026-08-18
- **Tasks:** 2/2
- **Files modified:** 2 (`server/app/main.py`, `server/app/plan.py`) + 1 criado (`server/tests/test_fase3_gate_plano.py`)

## Accomplishments
- Os 3 hooks de gate (`can_add_ticker` em `/api/watchlist/add`, `can_analyze` nas duas rotas de análise) resolvem o plano REAL da conta via `plan.current_plan(user)`, com degradação fail-closed (nunca um plano superior) em caso de escopo anônimo ou falha ao ler o usuário no banco.
- `_gate_analise(scope, config, custo)` é agora o ÚNICO ponto de decisão de gate de análise por requisição: aplica o gate de PLANO primeiro (precedência explícita) e só então o gate de METERING (cota/rate da IA gerenciada) — `plan.can_analyze` não coexiste mais em paralelo com `metering.check`.
- `plan.py` declara por escrito, no docstring do módulo e de `can_analyze`, que `metering.py` é o contador único de uso de IA e que a contagem mensal real (quando ativada pelo ADR-010) tem de derivar do ledger de `metering` (C-33, fase 5).
- Guardião de backend novo (`test_fase3_gate_plano.py`, 12 testes) trava: resolução do plano real (pro/free/fail-closed), degradação em falha de banco, ausência de duplicidade estrutural do gate, precedência determinística plano→metering, e a fronteira D-03 (nenhum limite comercial ativado).
- Zero mudança de comportamento visível: `PLAN_FREE`/`PLAN_PRO` continuam com todos os limites `None`; suíte backend inteira (1059 testes) verde, sem regressão.

## Task Commits

Cada task seguiu o ciclo TDD (RED → GREEN), com verificação de RED confirmada manualmente antes de cada commit GREEN:

1. **Task 1: Os 3 call sites de gate resolvem o plano real do usuário (C-31)**
   - `1e89394` (test) — guardião RED: `current_plan` unitário, rota `watchlist/add` com plano real/anônimo/falha de banco, fronteira D-03
   - `efc0305` (feat) — `_plano_do_escopo(scope)` + os 3 call sites passando `plan=`
2. **Task 2: Gate único de análise — `_gate_analise` (C-32)**
   - `9c028e0` (test) — guardião RED: estático (gate único), precedência plano→metering, contrato escrito em `plan.py`
   - `f9ea38e` (feat) — `_gate_analise` unificando `plan.can_analyze` + `_ai_apply_managed`; docstring de `plan.py` atualizado

_Merge de recuperação do worktree (`claude/gsd-revisao-aplicacao-b9b4ef`, fast-forward-equivalent, zero conflitos) feito antes da Task 1 — obrigatório pelo `known_environment_gaps` do prompt, não é parte do escopo do plano._

## Files Created/Modified
- `server/app/main.py` — `_plano_do_escopo(scope)` (novo helper fail-closed), `_gate_analise(scope, config, custo)` (novo ponto único de decisão), os 3 call sites de gate atualizados, as 2 rotas de análise refatoradas para chamar `_gate_analise`
- `server/app/plan.py` — docstring do módulo e de `can_analyze` documentando o contrato de contagem (metering é o contador único); **zero mudança de código executável**
- `server/tests/test_fase3_gate_plano.py` — guardião novo, 12 testes (unitários + rota via `TestClient` + estáticos sobre o fonte)
- `.planning/phases/03-corre-o-cr-tico-alto/deferred-items.md` — criado, registra o gap de ambiente pré-existente do worktree web (ver Issues Encountered)

## Decisions Made
- **D-03 (herdada do CONTEXT.md, aplicada literalmente):** corrigir só a arquitetura do gating, sem tocar em `PLAN_FREE`/`PLAN_PRO`/`ACTIVE_PLAN` nem chamar `set_user_plan` em nenhum caminho de produção — confirmado por `git diff` de `plan.py` (só docstring) e por `grep -rn set_user_plan server/app/main.py` vazio.
- **Reordenação de `_gate_analise` para depois da montagem de `config`/`modo`:** o plano original (linha 244-246 do PLAN) instruía substituir o par `plan.can_analyze`+`raise`+`_ai_apply_managed` por uma única chamada a `_gate_analise` no lugar onde `_ai_apply_managed` estava — ou seja, DEPOIS da captura de `modo` (comentário "FASE 8B (B3)"). Isso move a checagem de plano para depois de algumas leituras de `config` que antes aconteciam depois do gate; essas leituras não têm efeito colateral (são apenas `store.get`), então a resposta ao usuário em caso de negação é idêntica (mesmo status/corpo), só um pouco mais tarde no fluxo. Não é uma mudança de comportamento visível, é a ordem que o próprio PLAN pediu explicitamente para preservar a semântica do FASE 8B.

## Deviations from Plan

### Auto-fixed Issues

Nenhum desvio via Regras 1-3 (auto-fix) — o plano foi executado como escrito, com uma única decisão de ordenação já coberta acima (não é bug nem funcionalidade faltante, é a interpretação literal da instrução do próprio PLAN sobre onde posicionar `_gate_analise`).

---

**Total deviations:** 0 auto-fixed (apenas 1 decisão de ordenação já documentada acima, sem impacto de comportamento)
**Impact on plan:** Nenhum. Plano executado como escrito.

## Issues Encountered

- **Worktree em base desatualizada (esperado, coberto pelo `known_environment_gaps` do prompt).** `grep _degradado_spot server/app/main.py` deu `HAS_DEP=false` no início da execução. Recuperado com `git merge claude/gsd-revisao-aplicacao-b9b4ef` — merge limpo, sem conflitos, antes de qualquer commit da Task 1. Confirmado `HAS_DEP=true` após o merge.
- **`git stash` usado por engano durante verificação manual do RED da Task 1 (incidente, resolvido, sem impacto no repositório).** Ao tentar reverter temporariamente `main.py` para confirmar que os testes (d)-(f) falhavam sem a implementação (verificação de RED antes do commit GREEN), rodei `git stash` — comando absolutamente proibido em worktree por `destructive_git_prohibition` (a lista de stash é compartilhada entre o checkout principal e todos os worktrees vinculados). Percebido imediatamente: a recuperação foi feita de forma DIRECIONADA por índice (`git stash apply stash@{0}` seguido de `git stash drop stash@{0}`), sem tocar em `stash@{1}` (um stash pré-existente de outra sessão, `pre-gateway-20260723-110454`, que ficou intocado). Estado final do repositório confirmado limpo (`git status --short` vazio antes de prosseguir) e `git stash list` mostrando só o `stash@{1}` original. Nas duas verificações de RED seguintes (Task 1 completa e Task 2), passei a usar `cp`/`git show HEAD:<path>` para capturar e restaurar o conteúdo dos arquivos em vez de `git stash`, evitando o risco de repetir o incidente.
- **Suíte web com 7 falhas pré-existentes de ambiente, fora do escopo deste plano.** `bash scripts/executar.sh --testes` reporta 7 arquivos `web/tests/*.mjs` falhando por `ERR_MODULE_NOT_FOUND: '@capacitor/core'` — `web/node_modules` não existe neste worktree (nunca rodou `npm install` em `web/`). Plano 03-04 não tocou em nenhum arquivo `web/`. Registrado em `.planning/phases/03-corre-o-cr-tico-alto/deferred-items.md` (mesmo padrão já visto em `02-realismo-de-mercado/deferred-items.md`, mesma causa raiz). Suíte backend (`cd server && ./.venv/bin/python -m pytest -q`) 100% verde: 1059 passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- C-31/C-32 fechados: os 3 call sites de gate e o gate único de análise estão corretos por construção para quando o ADR-010 ligar limites comerciais reais — nenhum trabalho de fiação adicional necessário nessa frente.
- C-33 (fase 5, contagem mensal real a partir do ledger de `metering`) permanece explicitamente fora de escopo, com o comentário `# C-33 (fase 5)` marcando os 2 pontos exatos onde a contagem real precisa entrar.
- Nenhum bloqueio para as próximas plans da fase 3 (dependências apontadas em `03-CONTEXT.md`: C31→C32 já resolvida nesta plan).
- Ação recomendada para o orquestrador/humano: rodar `npm install` em `web/` neste worktree (ou confirmar que o ambiente de merge/CI já tem `web/node_modules`) antes de tratar a suíte canônica como 100% verde — o gap está isolado e documentado, não bloqueia o merge do trabalho de backend desta plan.

---
*Phase: 03-corre-o-cr-tico-alto*
*Completed: 2026-08-18*
