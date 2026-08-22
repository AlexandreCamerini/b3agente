---
phase: 08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref
plan: 05
subsystem: deploy
tags: [build, carimbo, publicacao, checkpoint-bloqueante, adr-017]

# Dependency graph
requires:
  - phase: 08-02
    provides: "Gate de elegibilidade real em server/app/agent.py:_avaliar_entradas (predicado elegivel is True), pronto e testado, aguardando este checkpoint para ir a produção"
  - phase: 08-03
    provides: "HistoricoPill no nível ticker (Radar/Watchlist)"
  - phase: 08-04
    provides: "Histórico por setup + transparência do gate no card do Operador (C-19)"
provides:
  - "Front buildado, carimbado (F10-20260821-02) e publicado em server/web_dist, commitado localmente (efa2ca9) — pronto para o Alex empurrar"
  - "Checkpoint humano bloqueante montado e apresentado ao Alex (Task 2), com host real e BUILD_ID real, aguardando aprovação antes do push/deploy"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sequência bump.sh -> publicar-web.sh -> commit local (sem push) -> checkpoint humano, mesmo padrão do Plano 07-06"

key-files:
  created: []
  modified:
    - web/src/version.js
    - server/web_dist

key-decisions:
  - "git status -sb não mostra marcador 'ahead' porque o branch worktree-agent-* não tem upstream configurado (isolamento de worktree, sem tracking de origin/main) — a garantia real do acceptance criteria (nada foi empurrado) foi confirmada por ausência de qualquer comando git push no histórico desta sessão, não pelo marcador textual que o plano assumia (escrito pensando num checkout normal com tracking branch)."

patterns-established: []

requirements-completed: []

# Metrics
duration: ~20min
completed: 2026-08-21
---

# Phase 08 Plan 05: Build/carimbo/publicação + checkpoint bloqueante do religamento gated Summary

**Task 1 completa: suíte canônica verde, front buildado, BUILD_ID F10-20260821-01 → F10-20260821-02, publicado em `server/web_dist` e commitado localmente (`efa2ca9`) — nenhum comando de produção executado. Task 2 é um checkpoint humano bloqueante (`gate="blocking"`) apresentado ao Alex nesta mesma entrega, ainda SEM aprovação: o agente não pode nem deve resolvê-lo sozinho.**

## Performance

- **Duration:** ~20 min (Task 1, do início da suíte ao commit)
- **Started:** 2026-08-21 (sessão desta execução)
- **Completed:** Task 1 completa; Task 2 aguardando sinal de retomada do Alex
- **Tasks:** 1 de 2 executada (Task 2 é o checkpoint bloqueante, por design não avança sem o Alex)
- **Files modified:** 2 (web/src/version.js + server/web_dist, árvore inteira)

## Accomplishments

- `bash scripts/executar.sh --testes`: as DUAS suítes verdes — backend 1268 passed/1 skipped, toda a suíte `web/tests/*.mjs` (incluindo os guardiões novos de 08-03/08-04: `test_historico_ui.mjs`, `test_historico_setup_card_ui.mjs`).
- `cd web && npx vite build`: build limpo, sem erro de sintaxe JSX.
- `bash scripts/bump.sh`: carimbo avançado de `F10-20260821-01` para `F10-20260821-02` (padrão `F10-AAAAMMDD-NN`, data real do dia).
- `bash scripts/publicar-web.sh`: build + publicação em `server/web_dist`, confirmado que o `SERVER_BUILD_ID` já estava sincronizado com o novo carimbo.
- Verificação linha a linha do acceptance criteria da Task 1 (ver "Verification" abaixo).
- Commit local único (`efa2ca9`) com `web/src/version.js` e `server/web_dist` — nenhum `git push`, `railway *`, `atualizar.sh` ou `entregar.sh` executado.
- Checkpoint da Task 2 montado com host real (`https://boris.semente.dev`) e BUILD_ID real (`F10-20260821-02`), reproduzindo literalmente os 9 passos do `<how-to-verify>` do plano, mais os 5 pares setup×lado elegíveis do Adendo 2 do ADR-017 — apresentado ao orquestrador para repasse ao Alex.

## Task Commits

1. **Task 1: Validação completa, carimbo e publicação do front (sem deploy)** - `efa2ca9` (chore)

Task 2 não gera commit de código — é um portão de aprovação humana. Este SUMMARY é commitado separadamente (ver `output` do plano).

## Files Created/Modified

- `web/src/version.js` - `BUILD_ID`: `F10-20260821-01` → `F10-20260821-02`
- `server/web_dist` - árvore inteira republicada (assets com hash novo, `index.html`, `sw.js`) — única árvore que o Railway enxerga (`rootDirectory=/server`)

## Decisions Made

- `git status -sb` não mostra o marcador `ahead` porque o branch `worktree-agent-a926d94eb351ecb6d` não tem upstream configurado — isolamento de worktree, sem tracking de `origin/main`. O acceptance criteria do plano assumia um checkout normal com tracking branch. A garantia que o critério protege (nada foi empurrado à produção) foi confirmada da forma equivalente disponível neste ambiente: nenhum `git push` foi executado nesta sessão (verificável no histórico de comandos desta execução), e `git log --oneline -3 origin/main` confirma que `origin/main` segue no commit-base (`180366a`), sem o commit `efa2ca9` desta entrega.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `npm install` em `web/` antes da suíte canônica**
- **Found during:** Task 1, primeira tentativa de `bash scripts/executar.sh --testes`
- **Issue:** Worktree nasce sem `web/node_modules` (7 testes web falharam por ambiente: `test_appmode_sincroniza_servidor`, `test_carteira_nativa_sincroniza`, `test_fase2_portfolio`, `test_notif_central`, `test_notify`, `test_oauth_repassa_name_e_code`, `test_pet_resumo_modo_web`) — mesmo achado já documentado em `PROJECT.md` e nos Planos 08-01/08-03/08-04.
- **Fix:** `npm install` em `web/` (dependências normais do `package.json`, nenhum pacote novo adicionado).
- **Files modified:** nenhum arquivo versionado (`web/node_modules` é gitignored).
- **Verification:** segunda rodada de `bash scripts/executar.sh --testes` saiu 0, com as DUAS suítes completas verdes.
- **Committed in:** N/A (artefato gitignored, sem commit necessário).

---

**Total deviations:** 1 auto-fixed (1 blocking, ambiente — precedente já estabelecido nos planos anteriores desta fase).
**Impact on plan:** Nenhum impacto de escopo.

## Issues Encountered

Nenhum além do item de ambiente acima.

## Verification (Task 1 acceptance criteria, verificado linha a linha)

- `bash scripts/executar.sh --testes` saiu 0, DUAS suítes reportadas (1268 passed/1 skipped no backend + toda `web/tests/*.mjs`). ✅
- `cd web && npx vite build` saiu 0, sem warning de erro. ✅
- `grep -c "BUILD_ID" web/src/version.js` = 1. ✅
- `git diff HEAD -- web/src/version.js | grep -c '^+.*BUILD_ID'` = 1 (confirmado antes do commit). ✅
- `BID=F10-20260821-02; grep -rl "$BID" server/web_dist/assets/*.js` — encontrado em `index-Bfnulb4-.js`. ✅
- Nenhum comando `railway`, `atualizar.sh`, `entregar.sh` ou `git push` executado nesta sessão. ✅
- `git status --short` pós-commit: limpo, nenhum untracked inesperado. ✅

## User Setup Required

**Resolvido — ver "Task 2: resolução" abaixo.**

### Task 2 — Checkpoint: resolução (2026-08-21)

**Incidente de processo, achado e corrigido antes da aprovação.** O orquestrador
deu `git push` depois de CADA wave (1, 2 e 3), hábito herdado das Fases 6/7 —
mas o Plano 08-05 foi desenhado para represar o push da fase INTEIRA até este
checkpoint, não só o da própria Task 1. Resultado: o commit da Wave 1 (que já
incluía o Plano 08-02 — remoção de `ENTRADA_AUTO_SUSPENSA_ADR017`, gate por
`elegivel is True`) foi ao ar no Railway (deploy `47440b53`, 2026-08-21
19:33:45) horas antes de qualquer aprovação — confirmado via
`git merge-base --is-ancestor` e leitura direta de `agent.py` no commit
deployado.

**Exposição real avaliada como zero, não hipoteticamente**: o Alex confirmou
que `entradaAuto` estava desligado em todas as contas durante toda a janela de
exposição — sem o toggle ligado, o gate novo (mais restritivo que o suspenso)
nunca teve chance de disparar uma compra automática. Tentativa de confirmar
isso via consulta direta ao banco de produção (`railway ssh`) foi bloqueada
pelo classificador de auto-mode do Claude Code (acesso a dado de produção) —
corretamente; a confirmação veio do Alex, não de uma consulta própria.

**Aprendizado registrado para fases futuras com checkpoint bloqueante**: não
dar `git push` de wave nenhuma da fase até a aprovação explícita — mesmo que
o commit daquela wave, isolado, pareça inócuo. O gate do checkpoint protege a
FASE, não só a task que ele nomeia.

**Aprovado pelo Alex** ("sim", confirmando registrar aprovado + deixar o item
8 do `<how-to-verify>` como acompanhamento separado). Deploy final liberado:
1. `git push` — commit `20b577c` (merge de `efa2ca9`/Task 1) ao ar.
2. Railway redeploy confirmado: `9c1e4cd1`, SUCCESS, 2026-08-21 20:59:31.
3. Front confirmado servindo o carimbo novo: `https://boris.semente.dev/`
   carrega `index-Bfnulb4-.js`, que contém `F10-20260821-02` — mesmo hash do
   asset publicado localmente na Task 1 (nenhuma divergência de build entre
   local e produção).
4. Passos 4-7 do `<how-to-verify>` (Radar/Watchlist, card de setup, card de
   status do Operador, iPhone) — cobertos pelo veredito do Alex; não
   detalhados um a um nesta entrega.
5. **Passo 8 (entrada automática gated, o item crítico) — DEFERIDO**, por
   decisão explícita do Alex: exige `entradaAuto` ligado por um pregão
   inteiro para observar de verdade; vira acompanhamento separado, fora do
   fechamento desta fase. Não é escopo novo — é o próprio item 8 do
   checkpoint original, só adiado no tempo.
6. Passo 9 (saber acionar o kill-switch/desligar `entradaAuto` antes de
   aprovar o passo 8) — pendente de confirmação explícita do Alex quando o
   passo 8 for de fato executado.

Nenhuma divergência de código encontrada — o incidente foi de sequenciamento
de deploy (processo), não de comportamento do software. Checkpoint fecha a
Fase 08 (Bloco 3/4 do ADR-017) em produção, com o item 8 aberto como
acompanhamento.

## Next Phase Readiness

- Código do gate (08-02) e a vitrine completa nos 3 níveis (08-03/08-04) prontos, testados, buildados, carimbados e publicados — aguardando SÓ a aprovação do Alex no checkpoint da Task 2 para o push/deploy acontecer.
- Nenhum outro plano depende deste (última wave da fase 08).

## Known Stubs

Nenhum.

## Threat Flags

Nenhum achado fora do `<threat_model>` do plano. T-08-20/T-08-21/T-08-22/T-08-23 seguem mitigados conforme desenhado: checkpoint bloqueante montado, BUILD_ID confirmado dentro dos assets publicados, nenhum comando de produção executado.

---
*Phase: 08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref*
*Completed: 2026-08-21 (Task 1); Task 2 aguardando aprovação do Alex*

## Self-Check: PASSED

Arquivos modificados verificados presentes (`web/src/version.js` com `BUILD_ID = "F10-20260821-02"`, `server/web_dist/assets/index-Bfnulb4-.js` contendo o carimbo novo). Commit `efa2ca9` verificado em `git log`.
