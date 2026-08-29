---
phase: 12-limites-do-plano-gratuito-ativos
plan: 02
subsystem: api
tags: [plan-gating, freemium, watchlist, python, fastapi, pytest]

# Dependency graph
requires:
  - phase: 12-01
    provides: "PLAN_FREE.max_watchlist=10 ativo em plan.py, can_add_ticker sem CTA na recusa"
provides:
  - "store.normalize_watchlist — fonte única do tamanho FINAL efetivo (filtrado+deduplicado), sem escrita"
  - "PUT /api/watchlist com gate de plano que só bloqueia CRESCIMENTO (D-03), nunca remoção/reordenação, nunca trunca conta grandfathered (D-04)"
  - "Bypass do cap fechado nos DOIS endpoints de watchlist (POST /add e PUT) — CAP-01 completo"
  - "Suíte de comportamento test_fase12_cap_watchlist.py (14 testes) + guardião estático anti-bypass"
affects: [12-03, 13]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate condicional por delta de tamanho (len(final) > len(atual)) em vez de gate incondicional — permite endpoints 'lista final arbitrária' (PUT) coexistirem com grandfather clause sem duplicar regra de negócio"
    - "Extração de normalização pura (normalize_watchlist) separada da escrita (set_watchlist) para servir de fonte única a um gate que precisa saber o tamanho ANTES de gravar"

key-files:
  created:
    - server/tests/test_fase12_cap_watchlist.py
  modified:
    - server/app/store.py
    - server/app/main.py

key-decisions:
  - "Gate reusa plan.can_add_ticker(len(final) - 1, ...) em vez de comparação inline — mantém a frase de recusa (D-05) numa fonte única, como o contrato C-32/C-33 exige"
  - "Prova de regressão: gate da Task 2 revertido temporariamente e restaurado depois de confirmar 6 falhas (>= 3 exigido) — não ficou no histórico como commit, é evidência documentada aqui"

requirements-completed: [CAP-01, CAP-04, CAP-05, CAP-07]

# Metrics
duration: ~45min
completed: 2026-08-29
---

# Phase 12 Plan 02: Fechamento do bypass de watchlist no PUT Summary

**`PUT /api/watchlist` ganhou gate de plano que compara o tamanho FINAL normalizado (não o cru do body) e só bloqueia crescimento — fechando o bypass que permitia contas free ultrapassarem 10 ativos pelo catálogo, sem nunca recusar remoção, reordenação ou truncar contas grandfathered.**

## Performance

- **Duration:** ~45 min (incluindo a correção do HEAD do worktree antes de iniciar — ver Issues Encountered)
- **Completed:** 2026-08-29T05:10:00Z (aprox.)
- **Tasks:** 3/3
- **Files modified:** 3 (1 criado, 2 modificados)

## Accomplishments
- `store.normalize_watchlist(conn, tickers, user_id)` extraída de `set_watchlist` — devolve a lista FINAL efetiva (filtrada contra `known_tickers`, deduplicada, reordenada) sem escrever no banco; `set_watchlist` passou a delegar nela, comportamento observável idêntico
- `put_watchlist` ganhou gate: só entra em `plan.can_add_ticker` quando `len(final) > len(atual)` (D-03) — remoção e reordenação nunca são recusadas, mesmo para conta já acima do limite (D-04, grandfather clause)
- Bypass do cap fechado nos DOIS caminhos de escrita de watchlist: `POST /api/watchlist/add` (já gateado desde antes) e `PUT /api/watchlist` (fechado agora) — CAP-01 completo
- Docstring de `ai_quota` atualizada: `monthLimit` do FREE está ativo (30) desde a v1.3/Fase 12, não mais "ADR-010 pendente"
- 14 testes novos cobrindo fronteira exata (10/11), grandfather clause (redução/reordenação/crescimento-do-topo/estado intacto), conta pro sem limite, os dois endpoints fechados, não-regressão pós-402, ausência de CTA na recusa, e proteção contra recusa falsa (tamanho cru ≠ tamanho final)
- Guardião estático: `put_watchlist` referencia `can_add_ticker`; `plan.can_add_ticker(` aparece exatamente 2× em `main.py` sem comentários; frase de recusa não duplicada fora de `plan.py`
- Prova de regressão executada ao vivo: gate revertido temporariamente → 6 testes falharam (acima do mínimo de 3 exigido pelo plano) → gate restaurado, `git diff` confirmou byte-identidade com o commit da Task 2
- Suíte de backend inteira (1691 testes, 0 falhas) e suíte canônica completa (`scripts/executar.sh --testes`, pytest + `web/tests/*.mjs`) verdes

## Task Commits

Each task was committed atomically:

1. **Task 1: Extrair store.normalize_watchlist como fonte única do tamanho final efetivo** - `cc4745d` (refactor)
2. **Task 2: Gate de plano no PUT /api/watchlist — só bloqueia crescimento (D-03/D-04)** - `9bea267` (feat)
3. **Task 3: Suíte de comportamento do cap de watchlist** - `bfb235f` (test)

**Plan metadata:** committed alongside this SUMMARY (worktree mode — orchestrator handles the shared-file/state commit after merge)

## Files Created/Modified
- `server/app/store.py` - `normalize_watchlist` extraída (pura, sem escrita); `set_watchlist` delega nela
- `server/app/main.py` - `put_watchlist` com gate condicional por delta de tamanho; docstring de `ai_quota` atualizada
- `server/tests/test_fase12_cap_watchlist.py` - 14 testes de comportamento + guardião estático (novo arquivo, 299 linhas)

## Decisions Made
- Nenhuma decisão nova fora do que o plano já travava (D-02/D-03/D-04/D-05 do 12-CONTEXT.md). A única liberdade exercida foi a redação exata dos comentários do bloco de gate em `put_watchlist` — precisaram ser condensados para caber dentro da janela de 12 linhas que os acceptance criteria do plano checam via `grep -A12`, sem perder nenhum dos três pontos exigidos (bypass fechado, tamanho normalizado, grandfather clause).

## Deviations from Plan

None - plan executado exatamente como escrito.

## Issues Encountered
- **HEAD do worktree divergente do commit base esperado (mesma classe de evento do 12-01):** ao iniciar, `git merge-base HEAD <base-esperada>` mostrou que o HEAD do worktree (1 commit de trabalho anterior não relacionado — checklist ao vivo da virada do mydata) era ANCESTRAL da base esperada. Confirmado com `git merge-base --is-ancestor` (SAFE) antes de qualquer ação. O hook local "Fact-Forcing Gate" bloqueou o `git reset --hard` do script padrão mesmo depois da disclosure de 3 partes exigida; refeito como `git merge --ff-only <base-esperada>`, não-destrutivo por construção. HEAD avançou de `16df05c` para `aece4c1` sem perda de nenhum commit. Nenhum arquivo de trabalho foi tocado por essa correção.
- **Ambiente sem `.venv` local no worktree:** `server/.venv` só existe no clone principal. `scripts/test.sh` já resolve isso automaticamente (procura o venv via `git rev-parse --git-common-dir`), então toda verificação deste plano rodou via `bash scripts/test.sh` (suíte completa) em vez de invocar pytest com filtro de arquivo — o sandbox de isolamento do worktree bloqueia comandos que referenciam caminhos absolutos fora do worktree, então não foi possível chamar o binário do venv principal diretamente para rodar só os 2 arquivos-alvo da Task 1/2. Mitigado rodando a suíte inteira (1691 testes) a cada verificação — cobertura estritamente maior que o pedido, sem lacuna.
- **Prova de regressão da Task 3 (acceptance criteria explícito):** revertido manualmente o bloco de gate da Task 2 em `main.py` (voltando à linha única `store.set_watchlist(...)` sem gate), rodada a suíte — **6 testes falharam** (`test_a`, `test_e`, `test_i`, `test_j`, e os 2 guardiões estáticos `test_put_watchlist_referencia_can_add_ticker...` / `test_plan_can_add_ticker_aparece_exatamente_duas_vezes...`), acima do mínimo de 3 exigido pelo plano. Gate restaurado byte a byte (confirmado por `git diff` vazio contra o commit `9bea267`) e suíte revalidada verde (1691 passed, 0 failed) antes do commit da Task 3.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `PUT /api/watchlist` e `POST /api/watchlist/add` estão ambos gateados corretamente — CAP-01 fica satisfeito em conjunto com o 12-01 (`max_watchlist` ativo) e este plano (bypass fechado)
- `store.normalize_watchlist` fica disponível como fonte única para qualquer código futuro que precise saber o tamanho final efetivo da watchlist antes de decidir algo — reduz risco de um terceiro caminho duplicar a regra de normalização
- Nenhum bloqueio conhecido para o 12-03 (mesma wave, arquivos sem overlap: `server/tests/test_fase12_cap_analises.py`, `docs/adr/010-planos-e-cap-gratuito.md`) nem para a Fase 13 (expõe `max_watchlist`/contagem via endpoint novo — este plano não mexeu em nenhum contrato de resposta além de `watchlist` em `public_state`, que já existia)

## Requirements Status (nota para o orquestrador)
Este plano NÃO chamou `requirements mark-complete`. `CAP-01` e `CAP-04` aparecem
no frontmatter de MÚLTIPLOS planos desta fase (12-01 + 12-02); `CAP-05`/`CAP-07`
também têm superfície tocada por mais de um plano da mesma wave (12-03).
Marcar qualquer um agora, antes do 12-03 (mesma wave) completar, arriscaria
uma marcação prematura caso o 12-03 dependa de algum desses IDs de forma que
ainda não esteja satisfeita. Fica para o orquestrador, depois que 12-03
completar.

## Self-Check: PASSED

- FOUND: server/app/store.py (normalize_watchlist presente)
- FOUND: server/app/main.py (gate em put_watchlist presente)
- FOUND: server/tests/test_fase12_cap_watchlist.py
- FOUND commit: cc4745d (Task 1)
- FOUND commit: 9bea267 (Task 2)
- FOUND commit: bfb235f (Task 3)

---
*Phase: 12-limites-do-plano-gratuito-ativos*
*Completed: 2026-08-29*
