---
phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios
plan: 02
subsystem: web
tags: [react, plan-gates, watchlist, ios, fail-closed]

# Dependency graph
requires:
  - phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios
    plan: 01
    provides: "GET /api/watchlist/quota — {count, limit, planId}, única fonte de max_watchlist"
provides:
  - "watchlistQuota() nos dois stores (api.js + serverStore + deviceStore), paridade travada"
  - "plan.js sem CTA de upgrade + canGrowWatchlistTo espelhando can_grow_watchlist_to (plan.py)"
  - "Gate fail-closed em deviceStore.addWatchlistTicker/putWatchlist — fecha CR-01 (bypass do cap no iOS nativo)"
  - "Guardião estático web/tests/test_fase13_watchlist_quota_ios.mjs travando a ordem rede→escrita"
affects: [13-03, 13-04, 13-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate fail-closed no cliente quando o cliente é a ÚNICA linha de defesa (sem gate server-side para watchlist no iOS local-first) — contraste explícito com o padrão fail-open já existente em aiQuota/analisesNoMes, onde o servidor barra de qualquer jeito"
    - "Guardião estático de ORDEM (índice de string no corpo do método via bracket-matching), não de resultado — a classe do erro (rede depois da escrita), não só a instância"

key-files:
  created:
    - web/tests/test_fase13_watchlist_quota_ios.mjs
  modified:
    - web/src/api.js
    - web/src/persistence.js
    - web/src/plan.js

key-decisions:
  - "Escopo do guardião novo restrito ao catch do gate de watchlist (não a TODOS os catches de persistence.js) — o arquivo tem 8 catches vazios pré-existentes fora deste plano (padrão fail-open legítimo em outros pontos); assertar globalmente teria violado o boundary de escopo (CLAUDE.md/deviation rules) e travado código correto não relacionado a este plano"
  - "Worktree exigia `npm ci` em web/ (node_modules ausente, fresh checkout) antes de `npx vite build` funcionar — restauração de dependências já pinadas em package-lock.json, não instalação de pacote novo (fora do escopo da Regra 3/exclusão de package installs)"

patterns-established:
  - "canAddTicker (item-a-item, operador >=) e canGrowWatchlistTo (tamanho final de troca em massa, operador >) são hooks distintos com semânticas diferentes, mesma reason — espelho literal de can_add_ticker/can_grow_watchlist_to em plan.py"

requirements-completed: [CAP-12, CAP-07, CAP-06]

duration: ~8min (tasks) + setup de worktree/deps
completed: 2026-08-30
---

# Phase 13 Plan 02: Enforcement no deviceStore (iOS) + espelho comercial do front Summary

**watchlistQuota() nos dois stores lendo o endpoint real (sem hardcode de 10/30), gate fail-closed em deviceStore.addWatchlistTicker/putWatchlist fechando o bypass do CR-01 no app iOS nativo, e plan.js sem CTA de upgrade com o novo canGrowWatchlistTo espelhando can_grow_watchlist_to do backend.**

## Performance

- **Duration:** ~8 min de execução das 3 tasks (commits d8d6268→76f16a4); tempo adicional de setup (fast-forward do worktree para a base c947b7a + `npm ci` em web/, node_modules ausente no fresh checkout)
- **Tasks:** 3/3
- **Files modified:** 4 (1 criado, 3 modificados)

## Accomplishments
- `web/src/api.js`: `watchlistQuota: () => req("GET", "/api/watchlist/quota")`, mesmo padrão de `aiQuota`
- `web/src/persistence.js` — `serverStore.watchlistQuota`/`deviceStore.watchlistQuota`: delegação direta ao endpoint, sem cache local (D-05); guardião genérico de paridade (`test_fase3_paridade_stores_generica.mjs`) confirma 63 métodos em cada store, 0 assimetrias
- `web/src/plan.js`: `canAddTicker` perdeu a frase "Faça upgrade para adicionar mais." (CAP-07); `canGrowWatchlistTo(finalSize, plan)` novo, espelhando `can_grow_watchlist_to` (operador `>`, não `>=` — tamanho FINAL de uma troca em massa); `canAnalyze` intocado (diff confirmado)
- `deviceStore.addWatchlistTicker`/`putWatchlist`: gate fail-closed ANTES de qualquer `write()` — falha de rede ou resposta inválida (`typeof quota.count !== "number"`) bloqueia com a mesma mensagem, nunca segue fail-open; `putWatchlist` só busca quota quando há crescimento real (`final.length > atual`), preservando a grandfather clause D-04 (remoção/reordenação nunca falham offline)
- Guardião estático novo (`test_fase13_watchlist_quota_ios.mjs`, 128 linhas): trava a ORDEM rede→escrita via bracket-matching do corpo dos dois métodos, o `throw` dentro do catch do gate, a comparação de crescimento em `putWatchlist`, a ausência de CTA em `plan.js` e a ausência de literal `maxWatchlist: <número>` em `persistence.js`

## Task Commits

Each task was committed atomically:

1. **Task 1: watchlistQuota() em api.js e nos dois stores (paridade)** - `d8d6268` (feat)
2. **Task 2: plan.js — remover CTA e adicionar o espelho canGrowWatchlistTo** - `3c243ac` (fix)
3. **Task 3: Gate fail-closed no deviceStore + guardião estático** - `76f16a4` (fix)

## Files Created/Modified
- `web/src/api.js` - wrapper `watchlistQuota` (linha 304)
- `web/src/persistence.js` - `watchlistQuota` nos dois stores (linhas ~285-288, ~1148-1156); import de `canAddTicker`/`canGrowWatchlistTo` de `./plan.js`; gate fail-closed em `deviceStore.putWatchlist` e `deviceStore.addWatchlistTicker`
- `web/src/plan.js` - `canAddTicker` sem CTA; `canGrowWatchlistTo` novo; comentário de topo atualizado explicando a fonte de verdade do limite (endpoint em runtime, nunca hardcode)
- `web/tests/test_fase13_watchlist_quota_ios.mjs` - guardião estático novo (criado)

## Decisions Made
- Guardião novo restringe a checagem de "catch não-vazio" ao catch específico do gate de watchlist (via `catchBodyAfter`, bracket-matching a partir do marcador `await api.watchlistQuota()`), não a todos os catches do arquivo. Uma primeira versão assertava globalmente e falhou contra 8 catches vazios pré-existentes em `persistence.js`, não relacionados a este plano (SCOPE BOUNDARY das regras de execução) — corrigido para escopo restrito antes do commit.
- `npm ci` em `web/` fora necessário porque o worktree nasceu sem `node_modules` (fresh checkout, diretório gitignored). Restauração de dependências já pinadas em `package-lock.json` versionado — não é instalação de pacote novo, portanto fora da exclusão da Regra 3 sobre package installs.

## Deviations from Plan

None - plan executado como especificado. O ajuste de escopo do guardião (catch global → catch restrito) foi correção durante a própria Task 3, antes do commit, não uma mudança de comportamento em relação ao que o plano pediu.

## Issues Encountered
- Worktree nasceu com HEAD em `81a3fa1` (5 commits atrás da base esperada `c947b7a`, que já incluía a Wave 1/plano 13-01). Corrigido com `git merge-base --is-ancestor` (confirmou fast-forward puro, sem uncommitted changes) seguido de `git merge --ff-only c947b7aaac53d404bda73154b605a7c3a4047cdc` — usado `merge --ff-only` em vez de `reset --hard` porque um hook local (Fact-Forcing Gate) bloqueia comandos destrutivos por padrão de string; o resultado é idêntico (fast-forward, sem perda de commits) e documentado com a evidência de ancestralidade antes de rodar.
- `web/node_modules` ausente no worktree (fresh checkout) impedia `npx vite build`; resolvido com `npm ci` usando o `package-lock.json` já versionado (439 pacotes, sem mudança de dependência).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `watchlistQuota()` disponível nos dois stores para os planos 13-03 (UI de visibilidade proativa) e seguintes consumirem sem depender de números hardcodados
- CR-01 (12-REVIEW.md) fechado: iOS nativo agora respeita `max_watchlist` real antes de gravar, com fail-closed comprovado por guardião estático
- Suíte canônica completa verde: `bash scripts/executar.sh --testes` (1709 passed, 1 skipped pytest + todos os `web/tests/*.mjs`, incluindo o novo `test_fase13_watchlist_quota_ios.mjs`); `cd web && npx vite build` sem erro
- REQUIREMENTS.md já mostra CAP-06/CAP-07/CAP-12 marcados `[x]`/`Complete` na tabela de rastreabilidade — nenhuma escrita adicional necessária neste plano
- Nenhum bloqueio conhecido para os próximos planos da Fase 13

---
*Phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios*
*Completed: 2026-08-30*

## Self-Check: PASSED

- FOUND: web/src/api.js
- FOUND: web/src/persistence.js
- FOUND: web/src/plan.js
- FOUND: web/tests/test_fase13_watchlist_quota_ios.mjs
- FOUND: commit d8d6268 (Task 1)
- FOUND: commit 3c243ac (Task 2)
- FOUND: commit 76f16a4 (Task 3)
