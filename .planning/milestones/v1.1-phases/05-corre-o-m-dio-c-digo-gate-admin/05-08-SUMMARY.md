---
phase: 05-corre-o-m-dio-c-digo-gate-admin
plan: 08
subsystem: release
tags: [bump, publicacao, web-dist, admin-dist, checkpoint, deploy]

# Dependency graph
requires:
  - phase: 05-corre-o-m-dio-c-digo-gate-admin
    provides: "05-01..05-07 — todas as correções Médio de código/gate/admin da fase, commitadas na main local"
provides:
  - "server/web_dist publicado com BUILD_ID F10-20260823-01 (toggle disabled real FIX-C23, fonte única appMode FIX-C21, gate mensal real + confirmação FIX-C33/C34 no front)"
  - "server/admin_dist publicado (alerta de gasto de IA FIX-C38, regra de acesso explícita da Auditoria FIX-C39)"
  - "server/app/main.py com SERVER_BUILD_ID sincronizado ao carimbo novo"
affects: [deploy, checkpoint-humano-fase-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Publicação por script único (bump.sh -> publicar-web.sh -> publicar-admin.sh), nunca edição manual de server/web_dist ou server/admin_dist"

key-files:
  created: []
  modified:
    - web/src/version.js
    - server/web_dist
    - server/admin_dist
    - server/app/main.py

key-decisions:
  - "git push NÃO executado por este agente — worktree isolado não tem origin/main alcançável de forma segura sem repetir o padrão de merge do orquestrador (mesmo padrão usado nos 05-01..05-07: 'merge: executor worktree'). Verificação técnica feita (origin/main é ancestor do HEAD deste worktree, fast-forward seguro), mas a execução do push fica para o orquestrador, após o merge deste commit na main local, seguindo o handoff que rodou identicamente nas 7 waves anteriores da fase."
  - "Suíte canônica completa (bash scripts/executar.sh --testes) rodada e verde ANTES de qualquer bump/build, conforme <action> do plano — 1365 passed, 1 skipped (backend) + suíte web completa (todas as .mjs OK, incluindo os 6 guardiões test_fase5_*.mjs de 05-01/05-05/05-06/05-07)"

requirements-completed: [FIX-C21, FIX-C22, FIX-C23, FIX-C33, FIX-C34, FIX-C38, FIX-C39]

# Metrics
duration: ~25min
completed: 2026-08-23
---

# Phase 05 Plan 08: Publicação do front (app consumidor + portal admin) + checkpoint humano Summary

**BUILD_ID F10-20260822-01 → F10-20260823-01; `server/web_dist` e `server/admin_dist` republicados com todas as correções de front da Fase 5; commit local feito (`caf714b`); `git push` para origin/main deliberadamente NÃO executado por este agente — fica para o orquestrador, seguindo o mesmo padrão de merge usado nas 7 waves anteriores da fase.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-08-23
- **Tasks:** 1/2 (Task 1 completa; Task 2 é checkpoint humano bloqueante, retornado ao orquestrador sem resolução)
- **Files modified:** 4 (web/src/version.js, server/web_dist, server/admin_dist, server/app/main.py)

## Accomplishments

- Suíte canônica (`bash scripts/executar.sh --testes`) rodada ANTES de qualquer build: 1365 testes backend passed (1 skipped) + suíte web completa (todos os `.mjs` OK), exit 0.
- `bash scripts/bump.sh`: BUILD_ID avançado de `F10-20260822-01` para `F10-20260823-01`.
- `bash scripts/publicar-web.sh`: build + publicação em `server/web_dist` — confirmado que o BUILD_ID novo aparece dentro do bundle (`grep -rl "F10-20260823-01" server/web_dist/assets/*.js` bate em `index-Qg13QRIR.js`), e que `server/app/main.py` teve `SERVER_BUILD_ID` sincronizado automaticamente pelo script.
- `bash scripts/publicar-admin.sh`: build + publicação em `server/admin_dist` (hash de `EditorTexto-*.js` e `index-*.js` mudou, prova de republicação exigida pelo próprio script, já que o portal não carrega BUILD_ID).
- Diff revisado antes do commit: as 30 mudanças em `server/web_dist`/`server/admin_dist` são inteiramente saída de build (renames/creates/deletes de assets com hash, `index.html`, `sw.js`) — nenhuma edição manual. `git diff --stat` de `web/package.json`/`web/package-lock.json`/`web-admin/package.json`/`web-admin/package-lock.json` veio vazio (nenhuma dependência nova).
- Commit único local: `caf714b`.

## Task Commits

1. **Task 1: Bump, build e publicação das duas árvores de front** - `caf714b` (chore)

## Files Created/Modified

- `web/src/version.js` — `BUILD_ID` de `F10-20260822-01` para `F10-20260823-01`
- `server/web_dist` — árvore inteira republicada (assets com hash novo, `index.html`, `sw.js`) via `scripts/publicar-web.sh`
- `server/admin_dist` — árvore inteira republicada via `scripts/publicar-admin.sh`
- `server/app/main.py` — `SERVER_BUILD_ID` sincronizado ao carimbo novo pelo próprio `publicar-web.sh` (passo 3/3)

## Decisions Made

- **`git push` NÃO executado por este agente.** O passo 7 da `<action>` do plano (`git push`) foi verificado tecnicamente possível de forma segura — `git merge-base --is-ancestor <origin/main> HEAD` confirmou que o HEAD deste worktree (`caf714b`) contém `origin/main` (`a788571...`) como ancestral, ou seja, um push direto de `HEAD:main` seria fast-forward, sem risco de divergência. MAS: as 7 waves anteriores desta fase (05-01 a 05-07) landaram na `main` local do repositório SEMPRE via commit de merge explícito do orquestrador (`merge: executor worktree (05-0N, ...)`), nunca por push direto de dentro de um worktree isolado. Pular esse handoff agora seria a primeira exceção ao padrão em 7 execuções, deixaria a `main` local do orquestrador (hoje em `9e59eeea`, um commit atrás deste HEAD) desatualizada em relação a `origin/main` depois do push, e é exatamente o tipo de divergência que os guardrails de git destrutivo deste ambiente existem para prevenir. **O push fica para o orquestrador**, depois de mesclar este branch (`worktree-agent-abda4153555dc814c`, commit `caf714b`) na sua `main` local — só então o `git push` do passo 7 do plano deve rodar.
- **Consequência para o checkpoint da Task 2:** como o push ainda não aconteceu, o `curl https://boris.semente.dev/api/health` do roteiro de verificação AINDA NÃO vai devolver `SERVER_BUILD_ID = "F10-20260823-01"` — vai devolver o carimbo anterior, até o orquestrador mesclar e empurrar. A mensagem de checkpoint devolvida ao orquestrador registra isso explicitamente, para não passar a falsa impressão de que a entrega já está no ar.

## Deviations from Plan

### Auto-fixed Issues

Nenhum — plano executado como escrito para os passos 1-6 da Task 1 (suíte, bump, publicar-web, publicar-admin, revisão de diff, commit).

### Desvio registrado (não Rule 1-4, decisão de segurança operacional)

**1. Passo 7 da Task 1 (`git push`) NÃO executado pelo agente — delegado ao orquestrador**
- **Encontrado durante:** Task 1, passo 7
- **Motivo:** este agente roda num worktree isolado, numa branch própria (`worktree-agent-abda4153555dc814c`), não em `main`. As 7 waves anteriores da mesma fase sempre landaram na `main` local via commit de merge do orquestrador antes de qualquer push a `origin`. Um `git push` direto deste worktree para `origin main` seria tecnicamente seguro (fast-forward verificado), mas quebraria esse padrão pela primeira vez na fase e deixaria a `main` local do orquestrador desatualizada em relação a `origin`.
- **Ação:** trabalho de Task 1 completo e commitado localmente (`caf714b`); `git push` explicitamente deixado para o orquestrador, depois do merge deste branch na `main` local — mesma sequência que fechou 05-01 a 05-07.
- **Arquivos:** nenhum (decisão de processo, não de código)
- **Commit:** N/A (é a AUSÊNCIA de uma ação, documentada aqui e no handoff ao orquestrador)

## Issues Encountered

Nenhum problema técnico. `web/node_modules`/`web-admin/node_modules` ausentes no worktree novo (gap C-24, recorrente e já resolvido automaticamente por `scripts/executar.sh --testes` desde o Plano 05-04 para `web/`; `web-admin/` resolvido pelo próprio `npm ci` dentro de `publicar-admin.sh`).

## User Setup Required

Resolvido — ver "Task 2: resolução" abaixo.

### Task 2 — Checkpoint: resolução (2026-08-23)

Orquestrador mesclou `worktree-agent-abda4153555dc814c` (`caf714b`) na `main`
local (`merge: executor worktree (05-08, task 1 — build/carimbo/publicação
web+web-admin)`) e deu `git push` (`a788571..1fe3e46`). Deploy confirmado:
`curl https://boris.semente.dev/api/health` devolveu `SERVER_BUILD_ID =
"F10-20260823-01"` na 3ª tentativa de polling.

**Alex aprovou** ("aprovdo", confirmando o roteiro de 7 passos sem
divergência reportada item a item). Checkpoint fecha a Fase 05 em produção:
- FIX-C23 (toggle desabilitado real fora do Operador) e FIX-C38 (alerta de
  gasto de IA no portal admin) — únicos 2 achados com pixel — confirmados.
- Demais 9 achados (C21, C22, C24, C25, C26, C27, C33, C34, C39) — teste,
  guardião, migração e documentação, sem superfície visual própria a
  verificar além do que já roda na suíte canônica.

Nenhuma divergência registrada. Fase 05 concluída.

## Next Phase Readiness

- Task 1 completa: as duas árvores de front (`server/web_dist`, `server/admin_dist`) estão publicadas e commitadas localmente com o carimbo `F10-20260823-01`.
- Task 2 é um checkpoint humano bloqueante (`gate="blocking"`) — retornado ao orquestrador sem resolução, incluindo a ressalva de que o push/deploy ainda não aconteceu.
- Esta é a última wave/plano da Fase 5. Depois do merge + push + aprovação do checkpoint pelo Alex, a fase fecha.

---
*Phase: 05-corre-o-m-dio-c-digo-gate-admin*
*Completed: 2026-08-23*

## Self-Check: PASSED

- FOUND: .planning/phases/05-corre-o-m-dio-c-digo-gate-admin/05-08-SUMMARY.md
- FOUND commit: caf714b (Task 1)
- FOUND commit: 72cdc7e (SUMMARY)
- CONFIRMED: BUILD_ID F10-20260823-01 in web/src/version.js
- CONFIRMED: BUILD_ID F10-20260823-01 present in server/web_dist/assets bundle
