---
phase: 22-componentes-compartilhados-trilho-cones-mascote
plan: 01
subsystem: ui
tags: [react, jsx, scroll-snap, inline-style, guardian-test]

# Dependency graph
requires:
  - phase: 20-fundacao-estrutural-e-tipografica
    provides: shell/GlobalStyle/tokens que os componentes compartilhados desta fase consomem
  - phase: 21-duplicacao-removida-e-portfolio-consolidado
    provides: App.jsx pós-consolidação (CapitalCurve única, card 2x2), base sobre a qual este plano opera
provides:
  - "carouselTrackStyle/carouselItemStyle como constantes de módulo compartilhadas por todo trilho horizontal do app"
  - "os 4 trilhos horizontais (HERO-CARROSSEL, filtro MODELO DE ANÁLISE, tira OportunidadesOpcoes, linha de candidatos de PropostaDaPosicao) roteados pelo mesmo mecanismo de scroll-snap"
  - "guardião estático único da Fase 22 (test_fase22_componentes_compartilhados.mjs), Seção A completa, com Seções B/C/D reservadas para os planos 22-02/22-03"
affects: [22-02, 22-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "carouselTrackStyle(extra)/carouselItemStyle(align): helper de módulo em vez de repetir overflowX/scrollSnapType em cada call site — extra é mesclado por último para overrides pontuais"
    - "taxonomia de scroll-snap dividida: scrollSnapType universal (x proximity) em todos os trilhos, mas flex 0 0 84% (peek dominante) exclusivo do HERO-CARROSSEL"

key-files:
  created:
    - web/tests/test_fase22_componentes_compartilhados.mjs
  modified:
    - web/src/App.jsx

key-decisions:
  - "scrollSnapType universal (x proximity + scrollSnapAlign start) nos 3 trilhos que rolavam solto, SEM aplicar o flex 0 0 84% do HERO — copiar o peek-width literalmente regrediria o filtro de 8 chips (TECH_MODELS) e a comparação lado a lado de N candidatos (Fase 19, MULTI-01/02), decisão já travada no 22-UI-SPEC.md"
  - "HERO-CARROSSEL também passa a usar o helper (via override 'x mandatory'/'center' no call site), decisão do planner registrada no 22-01-PLAN.md — comportamento computado idêntico ao anterior, mas agora overflowX: auto existe em 1 único lugar do arquivo"
  - "scrollbarWidth: none NÃO removido dos 2 sites que já tinham (OportunidadesOpcoes/PropostaDaPosicao) e NÃO adicionado aos outros 2 — mudança visual fora de escopo, registrada explicitamente no plano como não-mudança deliberada"

patterns-established:
  - "Guardião único por fase, estendido por planos subsequentes: test_fase22_componentes_compartilhados.mjs nasce com Seção A (SYS-01) e cabeçalho já nomeia Seções B/C/D como responsabilidade dos planos 22-02/22-03 no MESMO arquivo, não um arquivo novo"

requirements-completed: [SYS-01]

# Metrics
duration: 8min (commit-to-commit; total session time longer — inclui carregamento de contexto/leitura de 7 arquivos de planejamento antes da Task 1)
completed: 2026-09-06
---

# Phase 22 Plan 01: Trilho horizontal único (SYS-01) Summary

**Helper de módulo `carouselTrackStyle`/`carouselItemStyle` unifica os 4 trilhos horizontais de `App.jsx` — `overflowX: "auto"` passa a existir em um único lugar, travado por guardião estático novo.**

## Performance

- **Duration:** ~8 min commit-a-commit (23:37:50 → 23:45:28, base commit → último commit de task); tempo total de sessão é maior — inclui carregamento de contexto e leitura dos 7 arquivos de planejamento antes de escrever a Task 1, não capturado pelo intervalo entre commits
- **Started:** 2026-09-05T23:37:50-03:00
- **Completed:** 2026-09-05T23:45:28-03:00
- **Tasks:** 2 completed
- **Files modified:** 1 (`web/src/App.jsx`), 1 criado (`web/tests/test_fase22_componentes_compartilhados.mjs`)

## Accomplishments

- 4 trilhos horizontais do app (home/setups, filtro de modelo de análise,
  tira de oportunidades de opções, linha de candidatos multi-opção) agora
  passam pelo mesmo mecanismo de rolagem, definido em um único lugar do
  arquivo.
- Os 3 trilhos que hoje rolavam solto (sem assentar em item ao parar) ganham
  `scrollSnapType: "x proximity"` + `scrollSnapAlign: "start"`, sem regredir
  a visibilidade de 8 chips do filtro nem a comparação lado a lado dos
  candidatos de opção (Fase 19).
- Guardião estático novo (`test_fase22_componentes_compartilhados.mjs`)
  trava a regra central: `overflowX: "auto"` só pode existir dentro da
  definição do helper — um trilho futuro que redefina inline quebra o
  guardião.

## Task Commits

Executado como plano `tdd="true"` em nível de plano (Task 1 = RED, Task 2 = GREEN):

1. **Task 1: Guardião da Fase 22, Seção A (SYS-01), escrito antes da mudança (RED)** - `dc03a20` (test)
2. **Task 2: Helper compartilhado e os 4 trilhos roteados por ele (GREEN)** - `fdc8a9b` (feat)

**Plan metadata:** commit desta entrega (SUMMARY.md) segue nesta mesma sessão.

## Files Created/Modified

- `web/tests/test_fase22_componentes_compartilhados.mjs` - guardião estático único da Fase 22; Seção A (SYS-01) completa, cabeçalho reserva Seções B/C/D para os planos 22-02/22-03
- `web/src/App.jsx` - `carouselTrackStyle`/`carouselItemStyle` como constantes de módulo (ao lado de `card`/`kicker`); os 4 trilhos (HERO-CARROSSEL, TECH_MODELS, OportunidadesOpcoes, PropostaDaPosicao/CandidatoOpcao) roteados pelo helper

## Decisions Made

- Ver `key-decisions` no frontmatter. Nenhuma decisão foi tomada fora do que
  já estava travado em `22-UI-SPEC.md`/`22-PATTERNS.md` — este plano seguiu
  a taxonomia de carrossel já aprovada (snap universal, peek-width exclusivo
  do HERO) e a decisão do planner de rotear o HERO pelo helper também.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comentário do helper colidia com a própria asserção regex do guardião**
- **Found during:** Task 2 (implementação do helper `carouselTrackStyle`)
- **Issue:** O comentário explicativo acima da definição do helper continha
  a string literal `overflowX: "auto"` (para explicar a regra em prosa),
  fazendo a contagem `(app.match(/overflowX: "auto"/g) || []).length === 1`
  do guardião contar 2 ocorrências (a do comentário + a da definição real)
  em vez de 1.
- **Fix:** Reescrito o comentário para descrever a regra sem repetir a
  string literal exata (`overflowX solto (fora deste helper)` em vez de
  `` `overflowX: "auto"` ``).
- **Files modified:** `web/src/App.jsx`
- **Verification:** `node web/tests/test_fase22_componentes_compartilhados.mjs` volta a sair com código 0 e a asserção da contagem única passa.
- **Committed in:** `fdc8a9b` (parte do commit da Task 2, o comentário nunca chegou a ser commitado na forma incorreta)

---

**Total deviations:** 1 auto-fixed (1 bug, Rule 1)
**Impact on plan:** Nenhum — erro introduzido e corrigido dentro da própria Task 2, antes do commit. Sem impacto no escopo ou no comportamento entregue.

## Verification Notes (post-hoc, added after advisor review)

- **Dentes do guardião confirmados por teste adversarial:** depois de editar
  o comentário do helper (ver Deviations), injetou-se temporariamente um
  segundo `overflowX: "auto"` real (fora de comentário) em `App.jsx` e
  confirmou-se que o guardião falha exatamente na asserção central ("aparece
  exatamente 1×"). O arquivo foi restaurado ao estado do commit `fdc8a9b`
  logo em seguida (`git status --short` voltou vazio, guardião voltou a sair
  com código 0) — nenhuma mudança residual desse teste ficou no código.
- **`git push`:** nenhum `git push` foi executado nesta sessão (critério de
  aceite explícito da Task 2) — confirmado por revisão do histórico de
  comandos, não apenas por ausência de menção.

## Issues Encountered

- `web/node_modules` estava ausente no worktree (checkout novo). Resolvido
  automaticamente por `bash scripts/executar.sh --testes`, que detecta a
  ausência e roda `npm ci`/`npm install` sozinho (comportamento documentado
  desde a Fase 5, FIX-C24) — nenhuma ação manual necessária.
- `npx vite build` isolado falhou uma vez por permissão de sandbox no cache
  do npm (`EPERM` em `~/.npm/_cacache`); a suíte canônica completa (que
  inclui o mesmo `npm install`) rodou sem sandbox restrito e resolveu o
  `node_modules`, e o `npx vite build` subsequente rodou limpo (código 0).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- SYS-01 está satisfeito no código e travado por guardião: todo trilho
  horizontal do app rola pelo mesmo mecanismo, assenta em item, e nenhum
  perdeu densidade de conteúdo.
- `test_fase22_componentes_compartilhados.mjs` está pronto para receber as
  Seções B (SYS-02, ícones), C (SYS-02, Radar + tier dot + varredura de
  emoji zero) e D (SYS-03, sombra do PetFab) dos planos 22-02/22-03, no
  MESMO arquivo — cabeçalho já documenta essa expectativa.
- Nenhum push para `origin` foi feito nesta sessão (execução em worktree
  isolado); publicação do front (`scripts/bump.sh` + `publicar-web.sh`) fica
  para quando a Fase 22 inteira fechar, seguindo a regra já registrada em
  PROJECT.md ("Fase sem plano de publicação front").

## Orchestrator Live Re-Verification

Executada via MCP do navegador contra o dev server (merge desta branch):

1. **Watchlist ("Modelo de análise")** — trilho com `scroll-snap-type: x`
   (proximity implícito por spec quando a força não é declarada) e
   `overflow-x:auto`. ✓
2. **Acompanhar (HERO-CARROSSEL)** — mantém `scroll-snap-type: x mandatory`
   intacto, sem regressão do peek de 84%. ✓

---
*Phase: 22-componentes-compartilhados-trilho-cones-mascote*
*Completed: 2026-09-06*

## Self-Check: PASSED

- FOUND: web/tests/test_fase22_componentes_compartilhados.mjs
- FOUND: web/src/App.jsx
- FOUND: .planning/phases/22-componentes-compartilhados-trilho-cones-mascote/22-01-SUMMARY.md
- FOUND: commit dc03a20 (Task 1)
- FOUND: commit fdc8a9b (Task 2)
