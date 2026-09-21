---
phase: 35-jornada-guiada-do-workspace
plan: 03
subsystem: release
tags: [checkpoint-humano, publicacao, build-id, contraste-wcag, docs-fechamento]

# Dependency graph
requires:
  - phase: 35-jornada-guiada-do-workspace
    plan: 02
    provides: "Os 3 CTAs da jornada preenchidos com T.accent/T.onAccent, marca de resultado re-clicável, fold-in do bug T.bgPanel"
provides:
  - "Jornada Guiada do Workspace EM PRODUÇÃO (F10-20260921-01), aprovada por checkpoint humano ao vivo com as 8 leituras de contraste"
  - "REQUIREMENTS.md/ROADMAP.md/STATE.md fechados à mão, refletindo o estado real da Fase 35 (3/3 planos, JORN-01..03 Done)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - .planning/phases/35-jornada-guiada-do-workspace/35-03-SUMMARY.md
  modified:
    - server/app/main.py
    - server/web_dist/**
    - web/src/version.js
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md

key-decisions:
  - "Achado de ambiente registrado, não decidido como bug de produto: `bash scripts/executar.sh` sozinho trava neste host (lsof/ps travados, reproduzido 2x, com e sem sandbox) — contornado subindo backend/Vite diretamente. Nenhum script alterado."
  - "Publicação sem PR — confirmado via `gh pr list` (zero PRs abertas neste repo) que o pipeline deste projeto é push direto em v2/interacao-estrutural + origin/main, sem revisão de PR. Railway deploja a partir de main."

requirements-completed: [JORN-01, JORN-02, JORN-03]

# Metrics
duration: "~1h (checkpoint + aprovação + publicação)"
completed: 2026-09-21
---

# Phase 35 Plan 03: Checkpoint humano, publicação e fechamento de documentos Summary

**A jornada guiada do workspace foi aprovada ao vivo pelo Alex — incluindo as 8 leituras de contraste nas 4 combinações tema×modo que fechavam o risco aberto de D-07 — e publicada em produção sob o carimbo `F10-20260921-01`. Fase 35 e milestone v1.7 (3/3 requirements desta fase) formalmente fechados.**

## Performance

- **Duration:** ~1h (checkpoint + aprovação explícita + publicação + fechamento de docs)
- **Tasks:** 2
- **Files modified:** `server/app/main.py`, `server/web_dist/**`, `web/src/version.js` (Task 2); `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` (fechamento)

## Accomplishments

### Task 1 — checkpoint humano bloqueante

- Ambiente local subido (backend :8787 + Vite :5173) e evidência automática coletada ANTES de apresentar o roteiro ao Alex: `bash scripts/executar.sh --testes` (2923 pytest + 153/154 `.mjs`, baseline), `npx vite build` (verde), `test_brand_book_v2_tokens.mjs` (contraste `onAccent`×`accent` ≥ 4,5:1 computado nas 4 paletas), `test_opcoes_jornada_ui.mjs` (86 asserções verdes).
- **Achado de ambiente, não do produto**: `bash scripts/executar.sh` (sem argumentos) travou indefinidamente neste host — `lsof`/`ps` travados isoladamente, reproduzido 2x, com e sem sandbox. Contornado subindo `uvicorn`/`vite dev` diretamente. Nenhum script foi alterado; registrado como achado de ambiente para investigação futura, não bloqueou o checkpoint.
- Roteiro de 8 passos apresentado ao Alex na íntegra, numerado, com o passo 7 (as 8 leituras de contraste: rótulo + subtexto de custo × 4 combinações claro/escuro × Estudo/Operador) destacado como o item que fecha o risco aberto de D-07, e o passo 1 destacado como pedindo veredito sobre o fold-in do chip de vigia (mudança visual fora do workspace).
- **Aprovação do Alex obtida em duas rodadas de confirmação** — a primeira resposta ("os seis passos passados") não batia com a numeração real (8 passos) nem confirmava explicitamente as 8 leituras de contraste; pedido esclarecimento antes de aceitar. Resposta final: "Aprovado publicar" — tratada como a aprovação explícita que a Task 2 exige, só liberada depois dessa segunda rodada.

### Task 2 — publicação

- Merge de segurança com `origin/main` conferido (fetch + `merge-base --is-ancestor`) antes de qualquer carimbo.
- `bash scripts/bump.sh` → `web/src/version.js` `BUILD_ID = "F10-20260921-01"`.
- `bash scripts/publicar-web.sh` → `server/web_dist` regenerado (24 arquivos), `SERVER_BUILD_ID` sincronizado.
- Comentário do `SERVER_BUILD_ID` reescrito à mão com o resumo desta fase; entrega anterior (F10-20260920-01, Fases 33+34) rebaixada a "HISTORICO" com o texto preservado verbatim (guardrail: histórico não se reescreve).
- Suíte canônica repetida pós-bump: 2923 pytest + 0 failed, confirmado; `node web/tests/test_opcoes_jornada_ui.mjs` reconfirmado verde isoladamente.
- Commit `e9b819f`, push em `v2/interacao-estrutural` e `origin/main` — fast-forward confirmado (`HEAD == origin/main`).
- `/api/health` monitorado: serviu `F10-20260920-01` até 17:47:06, `F10-20260921-01` confirmado a partir de 17:47:36 (redeploy do Railway levou ~3-4min).
- Confirmado via `gh pr list` (zero PRs abertas neste repo) que a publicação não passa por PR — push direto é o pipeline real deste projeto.

## Task Commits

1. **Task 1 (checkpoint humano)** — sem commit próprio (verificação ao vivo + aprovação).
2. **Task 2: publicação** — `e9b819f` (feat)
3. **Fechamento de docs** — commit a seguir (docs)

## Files Created/Modified

- `server/app/main.py` — `SERVER_BUILD_ID` novo + comentário reescrito à mão, histórico preservado
- `server/web_dist/**` — 24 arquivos regenerados (hash de conteúdo)
- `web/src/version.js` — `BUILD_ID = "F10-20260921-01"`
- `.planning/REQUIREMENTS.md` — JORN-01..03 Done
- `.planning/ROADMAP.md` — checkbox Fase 35, item 35-03, Progress table
- `.planning/STATE.md` — Current Position reescrita, pendências declaradas

## Decisions Made

Ver `key-decisions` no frontmatter. Nenhuma decisão de arquitetura nova — Task 1/2 executaram o que os planos já travavam. Duas decisões operacionais desta sessão: (1) tratar a trava de `lsof`/`ps` como achado de ambiente, não reescrever scripts sem entender a causa raiz; (2) exigir clareza explícita do Alex antes de tratar uma resposta como aprovação de publicar (rejeitei "Fase testada" e "os seis passos passados" por não corresponderem ao que o checkpoint exige, só aceitei "Aprovado publicar").

## Deviations from Plan

**Nenhum desvio de escopo.** Diferença de processo, não de escopo: a aprovação exigiu duas rodadas de pedido de esclarecimento antes de ser aceita como o "aprovado — publicar" literal que o plano exige — registrado aqui porque é exatamente a disciplina que o `<resume-signal>` do plano pedia (não aceitar confirmação ambígua numa ação de publicação em produção).

## Issues Encountered

- Trava de `lsof`/`ps` neste host — documentada acima, contornada, não resolvida (fora do escopo desta fase investigar a causa raiz).
- `git fetch`/`gh pr list` falharam uma vez sob sandbox padrão ("failed to verify certificate"/"fatal: failed to store") — resolvido com `dangerouslyDisableSandbox: true`, mesma causa ambiental já documentada no projeto.

## User Setup Required

Nenhuma configuração de serviço externo necessária. Pendência já registrada (não desta fase): app iOS/TestFlight ainda não reflete esta entrega — rodar `scripts/distribuir-iphone.sh` quando o Alex decidir.

## Next Phase Readiness

- **Fase 35 e seus 3 requirements (JORN-01..03) fechados.** Milestone v1.7 segue com Fases 36 (Motor de Payoff Genérico) e 37 (Gráfico de Payoff e Explicação Confiáveis) pendentes.
- Próximo passo: `/gsd-discuss-phase 36`.
- Nenhum blocker conhecido para a Fase 36 — é fundacional (motor puro, sem dependência da 35).

---
*Phase: 35-jornada-guiada-do-workspace*
*Completed: 2026-09-21*

## Self-Check: PASSED

- FOUND: web/src/version.js (BUILD_ID F10-20260921-01)
- FOUND: server/app/main.py (SERVER_BUILD_ID F10-20260921-01, histórico preservado)
- FOUND: .planning/REQUIREMENTS.md (JORN-01..03 Done)
- FOUND: .planning/ROADMAP.md (checkbox Fase 35, item 35-03, Progress table)
- FOUND: .planning/STATE.md (Current Position reescrita)
- FOUND commit e9b819f
- CONFIRMED: https://boris.semente.dev/api/health respondendo F10-20260921-01
