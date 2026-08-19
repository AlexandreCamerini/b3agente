---
phase: 03-corre-o-cr-tico-alto
plan: 03
subsystem: ui
tags: [react, guardian-tests, state-parity, persistence, appmode]

# Dependency graph
requires:
  - phase: 03-corre-o-cr-tico-alto
    provides: "03-01: propagação de source real / degradado em /api/technicals (App.jsx FONTE_LABEL) — área do código disjunta desta plan, sem conflito"
provides:
  - "Guardião genérico e exaustivo de paridade deviceStore x serverStore (web/tests/test_fase3_paridade_stores_generica.mjs) — C-20 fechado"
  - "Card de status único no topo de AgenteScreen ('Operador IA'), 3 badges read-only (Modo do app, Operador no servidor, Executar/sinalizar) + link para o Perfil — C-19 fechado"
affects: ["05-*: C-21 (migração dos 8 pontos de leitura redundante de appMode) depende deste card não ter mexido nesses pontos de leitura"]

tech-stack:
  added: []
  patterns:
    - "Guardião estático genérico sobre persistence.js: extrai nomes de método via regex ancorada em indentação de 4 espaços a partir do `return {` de cada store (não do início da função), filtrando palavras reservadas do JS, com allowlist explícita (nome -> justificativa) para assimetrias intencionais"
    - "Isolamento de bloco JSX por marcador de comentário estável + indexOf, mesmo padrão dos guardiões pontuais já existentes (test_auditoria_status_strip.mjs, test_agente_modo_estudo_ui.mjs)"

key-files:
  created:
    - web/tests/test_fase3_paridade_stores_generica.mjs
    - web/tests/test_fase3_c19_card_status.mjs
  modified:
    - web/src/App.jsx
    - web/tests/test_auditoria_status_strip.mjs

key-decisions:
  - "Dependência 03-01 verificada por grep(FONTE_LABEL) deu falso positivo (string já existia no commit-base, antes de 03-01) — descoberto DEPOIS de Task 1/Task 2 já commitadas nesta worktree; verificação por diff de commit confirmou que a área tocada por 03-01 (AboutModal/TechnicalModal/FonteDadosScreen/CatalogModal em App.jsx) é disjunta da área tocada por esta plan (AgenteScreen, persistence.js) — merge de claude/gsd-revisao-aplicacao-b9b4ef executado a posteriori, sem conflitos, suíte completa re-executada e verde depois do merge"
  - "Cor do badge 'Modo do app' mudou de T.accent/T.textPrimary (tira antiga) para T.positive/T.textFaint (mudança deliberada, prevista no 03-UI-SPEC Dimensão 3 — accent fica reservado ao Toggle do card-herói e ao link)"
  - "Janela do regex de test_auditoria_status_strip.mjs alargada de 400 para 800 caracteres (com nota datada no próprio teste) porque os 2 badges novos aumentaram a distância até A.go(\"perfil\"); nenhuma assertiva foi removida (house rule preservada)"

patterns-established:
  - "Guardião de paridade genérico complementa (não substitui) os guardiões pontuais existentes — mesma convenção usada nos dois guardiões desta plan"

requirements-completed: [FIX-C20, FIX-C19]

duration: ~50min
completed: 2026-08-19
---

# Phase 3 Plan 3: Guardião genérico de paridade dos stores + card de status único (C-20, C-19) Summary

**Guardião estático que compara os 58 métodos de `deviceStore()`/`serverStore()` e falha em qualquer assimetria não declarada, e um card de 3 badges read-only no topo de "Operador IA" mostrando Modo do app · Operador no servidor · Executar/sinalizar, cada um lido da mesma fonte canônica que o card-herói.**

## Performance

- **Duration:** ~50 min
- **Started:** 2026-08-18T22:00Z (aprox.)
- **Completed:** 2026-08-19T01:41:46Z
- **Tasks:** 2/2
- **Files modified:** 4 (2 criados, 2 modificados)

## Accomplishments
- Guardião genérico de paridade `deviceStore()` × `serverStore()` — extrai estaticamente os nomes de método dos dois blocos (58 de cada lado hoje), com allowlist explícita e justificada para a única assimetria conhecida (`_setDeviceScope`); sensibilidade comprovada manualmente (método fictício inserido só num lado derruba o teste, nomeando o método)
- Card de status único, primeiro elemento de `AgenteScreen`, absorvendo a tira parcial que só mostrava 1 dos 3 interruptores; cada badge lê a mesma variável já derivada e usada pelo card-herói (`ctx.operador`, `ag.serverEnabled && logged`, `modoEfetivo`) — nunca contradiz o herói
- Novo guardião estático `test_fase3_c19_card_status.mjs` com 7 assertivas (posição, rótulos, fonte canônica de cada badge, ausência de `config.appMode`, read-only, sem accent nos badges, tira única); sensibilidade comprovada (trocar badge 3 para `ag.mode` cru derruba o teste)
- Guardião existente `test_auditoria_status_strip.mjs` preservado sem remoção de assertiva (janela de regex alargada com nota datada)
- Descoberta e correção de uma worktree em base desatualizada (merge limpo, sem conflitos, após confirmar que as áreas de código eram disjuntas)

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Guardião genérico exaustivo de paridade deviceStore × serverStore (C-20)** - `e48eff5` (test)
2. **Task 2: Card de status único no topo de "Operador IA" (C-19)** - `56022ed` (feat)
3. **Merge de recuperação de base (ver Deviations)** - `ea9db24` (merge, sem conteúdo próprio desta plan)

**Plan metadata:** (este commit) `docs(03-03): complete plan`

## Files Created/Modified
- `web/tests/test_fase3_paridade_stores_generica.mjs` - Guardião genérico de paridade dos stores (C-20)
- `web/src/App.jsx` - Card de status único em `AgenteScreen` (C-19), substitui a tira parcial anterior
- `web/tests/test_fase3_c19_card_status.mjs` - Guardião estático do card C-19
- `web/tests/test_auditoria_status_strip.mjs` - Janela do regex de link alargada (400→800 chars), nota datada, nenhuma assertiva removida

## Decisions Made
- Ver `key-decisions` no frontmatter — cor dos badges (Dimensão 3 do UI-SPEC), janela de regex do guardião existente, e a descoberta/correção da worktree em base desatualizada.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Worktree branchada de uma base desatualizada, faltando toda a árvore `.planning/` e a plan 03-01**
- **Found during:** Após Task 2, ao tentar localizar `.planning/` para escrever este SUMMARY.md
- **Issue:** O check inicial `grep -q "FONTE_LABEL" web/src/App.jsx` (prescrito no prompt de execução) deu falso positivo — a string `FONTE_LABEL` já existia no commit-base desta worktree (`403432f`), independente da plan 03-01. Investigação por `git merge-base --is-ancestor` confirmou que o merge commit real de 03-01 (`271fbcc`) NÃO era ancestral do HEAD desta worktree, e que `.planning/` inteiro estava ausente (nunca commitado nesta linha de história)
- **Fix:** Antes de mesclar, verifiquei por `git diff <base> <alvo> -- web/src/App.jsx web/src/persistence.js` que a área tocada pelas plans 03-01/02-02 (AboutModal, TechnicalModal, FonteDadosScreen, CatalogModal em App.jsx; nenhum arquivo em persistence.js) era disjunta da área tocada por esta plan (AgenteScreen em App.jsx; persistence.js inteiro). Com essa confirmação, executei `git merge claude/gsd-revisao-aplicacao-b9b4ef --no-edit`, que completou sem NENHUM conflito
- **Verificação:** Suíte canônica completa (`bash scripts/executar.sh --testes`) reexecutada depois do merge — 1047 testes de backend + todos os `web/tests/*.mjs` (incluindo os 2 guardiões novos desta plan) verdes; `npx vite build` também reexecutado com sucesso
- **Files modified:** nenhum arquivo de conteúdo (merge trouxe `.planning/`, plans 02-02/03-01 e seus testes/artefatos, sem tocar nos arquivos desta plan)
- **Committed in:** `ea9db24` (merge commit, separado dos 2 commits de task)

---

**Total deviations:** 1 auto-fixed (1 blocking — Rule 3)
**Impact on plan:** Nenhum impacto no conteúdo entregue pela plan; a correção só restaurou o histórico de base correto da worktree, permitindo que este SUMMARY.md exista no lugar certo. As 2 tasks foram implementadas e verificadas ANTES da descoberta do problema, e permaneceram intactas (nenhum conflito, nenhuma reescrita) depois do merge.

## Issues Encountered
- O check de dependência prescrito no prompt de execução (`grep -q "FONTE_LABEL" web/src/App.jsx`) não é um proxy confiável para "03-01 está merged nesta worktree" quando a string de busca já existia antes da mudança que o check pretende detectar — ver deviation acima. Recomendação para plans futuras com o mesmo padrão de recovery: usar `git merge-base --is-ancestor <hash-do-merge-commit-real> HEAD`, não grep de string, quando o hash do merge commit da dependência for conhecido.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- C-19 e C-20 fechados; card de status único no ar, guardião genérico de paridade travando qualquer assimetria futura entre os stores
- C-21 (migração dos 8 pontos de leitura redundante de `appMode`) permanece intocado, como determinado por D-02 revisado — fica para a fase 5
- Verificação humana pendente (`<human-check>` do plano): abrir a tela "Operador IA" e confirmar visualmente que o card aparece no topo com os 3 estados corretos, e que trocar Modo do app / Operador no servidor move os badges na mesma direção do card-herói — não executável neste ambiente (sem browser interativo), delegar ao Alex antes do deploy

---
*Phase: 03-corre-o-cr-tico-alto*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: web/tests/test_fase3_paridade_stores_generica.mjs
- FOUND: web/tests/test_fase3_c19_card_status.mjs
- FOUND: web/src/App.jsx
- FOUND: web/tests/test_auditoria_status_strip.mjs
- FOUND: .planning/phases/03-corre-o-cr-tico-alto/03-03-SUMMARY.md
- FOUND commit: e48eff5 (test 03-03 Task 1)
- FOUND commit: 56022ed (feat 03-03 Task 2)
- FOUND commit: ea9db24 (merge recovery)
