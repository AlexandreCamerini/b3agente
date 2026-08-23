---
phase: 02-realismo-de-mercado
plan: 07
subsystem: testing / qa
tags: [end-to-end, ordens-pendentes, MERC-01, MERC-02, MERC-03, MERC-04, human-verify]

requires:
  - phase: 02-realismo-de-mercado (plano 03)
    provides: "hook de execução automática de ordens pendentes dentro de scheduler_loop (agent.py), status_snapshot()[\"ordensPendentes\"]"
  - phase: 02-realismo-de-mercado (plano 06)
    provides: "MarketStatusBadge (login + Topbar), BuyModal/SellModal com pill PENDENTE, seção Pendentes no HistoricoScreen, cancelamento em dois passos"
provides:
  - "qa/48-fase2-verificacao-e2e-ordens-pendentes.md: exercício ponta-a-ponta contra servidor uvicorn real (não TestClient), banco SQLite descartável — market/status público, buy pendente, cancelamento, execução forçada da passada do scheduler, fluxo de venda pendente, conta do caixa fechando em todos os passos"
  - "Aprovação humana registrada do badge de status de mercado e da seção Pendentes (web); iPhone/TestFlight declarado como limitação conhecida, não omitida"
  - "MERC-01 fechado no REQUIREMENTS.md (era o único dos 4 ainda pendente — dependia desta verificação humana)"
affects: [testflight-verification, ios-deviceStore, ordens-pendentes-ios]

tech-stack:
  added: []
  patterns:
    - "Exercício ao vivo de fase inteira: servidor real + banco descartável + curl, nunca TestClient — modelo reusável para futuras verificações de fase (qa/48 como referência de formato)"
    - "Forçar uma passada do scheduler fora do pregão real: scheduler_loop(once=True) num processo Python separado, mesmo B3_DB_PATH (WAL garante visibilidade entre processos), com monkeypatch documentado do gate de horário — alternativa a POST /api/agent/run-now quando este não cobre o subsistema testado (run-now só roda run_cycle_for por usuário, nunca pending_orders)"

key-files:
  created:
    - qa/48-fase2-verificacao-e2e-ordens-pendentes.md
    - .planning/phases/02-realismo-de-mercado/02-07-SUMMARY.md
  modified:
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Execução forçada da ordem pendente rodou num processo Python separado do servidor uvicorn (mesmo arquivo SQLite, WAL) em vez de esperar o pregão real abrir (madrugada no momento do exercício) — documentado explicitamente no relatório como método e como limitação (o contador ultimoCiclo, que é memória do PROCESSO do servidor, não reflete a passada forçada externamente; o contador total, que É lido do banco, reflete corretamente)"
  - "Dois achados investigados a fundo e confirmados como comportamento esperado, não bugs: (1) escopos:2 em /api/agent/status vem de um bucket anônimo legado (user_id=None) que store.ensure_defaults(_conn) grava no BOOT do servidor (main.py:51), confirmado rodando o servidor contra um banco 100% virgem antes de qualquer requisição além de /api/health; (2) POST /api/sell com qty=40 pendente virou ordem de qty=100 porque pending_orders.criar_venda normaliza para lote de 100, a MESMA normalização que store.sell (venda imediata) já usa"
  - "Alex aprovou os passos 1-6 e 8 do roteiro visual (web). Passo 7 (repetir no iPhone via TestFlight) fica como limitação conhecida DECLARADA — ele confirmou explicitamente que não vai testar agora, não é uma omissão silenciosa (atende ao critério de aceite do próprio plano, que permite essa declaração)"

patterns-established:
  - "qa/NN-slug.md como formato padrão de relatório de verificação ao vivo: data real, comandos exatos, saída crua/recortada, tabela de conservação de caixa, seção de limitações conhecidas separada de defeitos"

requirements-completed: [MERC-01, MERC-02, MERC-03, MERC-04]

duration: "~35min de trabalho ativo (Task 1: setup + exercício + relatório + commit); Task 2 pausou em checkpoint humano até a resposta do Alex chegar de forma assíncrona"
completed: 2026-08-19
---

# Phase 2 Plan 07: Verificação Ponta-a-Ponta da Fase (Realismo de Mercado) Summary

Servidor `uvicorn` real (não `TestClient`) contra banco SQLite descartável, exercitado via
`curl`: status de mercado público, ordem pendente com caixa reservado e conservado,
cancelamento com devolução exata, execução forçada da passada do scheduler transformando
pendente em posição + linha de histórico, fluxo de venda pendente — fechando a Fase 2
(MERC-01..04) com evidência ao vivo em vez de só suíte verde, e aprovação humana do badge
de status de mercado e da seção Pendentes no web (iPhone/TestFlight declarado como
limitação conhecida).

## Performance

- **Duration:** ~35 min de trabalho ativo (Task 1 completa: leitura de contexto, self-heal
  do worktree, setup do exercício, execução das 4 rotas reais, escrita do relatório,
  commit). Task 2 é um checkpoint humano — pausou a execução até a resposta assíncrona do
  Alex, que não conta como tempo de trabalho do executor.
- **Completed:** 2026-08-19
- **Tasks:** 2/2
- **Files modified:** 1 novo (`qa/48-fase2-verificacao-e2e-ordens-pendentes.md`), 1
  atualizado (`.planning/REQUIREMENTS.md`)

## Accomplishments

- `bash scripts/executar.sh --testes`: 1100 testes de backend + 82/82 arquivos
  `web/tests/*.mjs`, exit 0 — as DUAS suítes, não substituto.
- `cd web && npx vite build`: exit 0, pipeline completo (sem substituto de `esbuild`).
- Ciclo completo de ordem pendente exercitado contra servidor real: `GET /api/market/status`
  (público, 6 chaves, bate com horário real), `POST /api/buy` pendente (caixa reservado e
  conservado), `DELETE /api/orders/pending/{id}` (devolução exata), execução forçada da
  passada do scheduler (posição criada, `history` com `origem: "pendente"`,
  `pendingOrders` esvaziado, `/api/agent/status.ordensPendentes.total` correto), fluxo de
  venda pendente (reserva de quantidade na criação, devolução com mesmo `avg` no
  cancelamento).
- Conta do caixa fechando em TODOS os passos (tabela consolidada no relatório) — patrimônio
  conservado em 10000,0 do início ao fim.
- Dois achados investigados a fundo (não deixados como "estranho, mas não bug" sem
  verificação) e confirmados como comportamento esperado — ver `key-decisions`.
- Aprovação humana do Alex: passos 1-6 e 8 do roteiro visual (badge pré-login, badge no
  Topbar, pill PENDENTE nos modais, seção Pendentes no Histórico, cancelamento em dois
  passos, ausência de linguagem de promessa/número inconsistente) — **"aprovado"**. Passo 7
  (iPhone/TestFlight) declarado como limitação conhecida, confirmado explicitamente pelo
  Alex que não seria testado agora (não é omissão).

## Task Commits

1. **Task 1: Exercício ponta-a-ponta contra servidor real + suíte canônica** - `fa37a56`
   (docs)
2. **Task 2: Verificação visual do Alex** - checkpoint humano, sem alteração de código
   (nenhum commit de código — só o registro no SUMMARY, conforme a própria instrução da
   task: "Não editar código nesta task")

**Plan metadata:** `docs(02-07): complete plan` (este commit, junto com este SUMMARY) +
`docs(02-07): mark MERC-01..04 complete in REQUIREMENTS.md` (commit seguinte)

## Files Created/Modified

- `qa/48-fase2-verificacao-e2e-ordens-pendentes.md` — relatório do exercício ao vivo:
  suíte canônica, build, setup do banco descartável, as 5 rotas reais exercitadas com
  saída crua, tabela de conservação de caixa, achados investigados, limitações conhecidas.
- `.planning/REQUIREMENTS.md` — `MERC-01` marcado completo (era o único dos 4 requirements
  desta fase ainda pendente; dependia da verificação humana desta task).
- `.planning/phases/02-realismo-de-mercado/02-07-SUMMARY.md` — este arquivo.

## Decisions Made

Ver `key-decisions` no frontmatter. Resumo: (1) execução forçada da ordem pendente via
`scheduler_loop(once=True)` num processo separado com monkeypatch documentado do gate de
horário (madrugada no momento do exercício, fora do pregão real) — limitação conhecida do
método registrada no relatório, não afeta a validade do estado persistido (mesmo banco,
WAL); (2) dois comportamentos "estranhos à primeira vista" foram investigados até a causa
raiz no código-fonte (não deixados como suposição) e confirmados como esperados, não bugs;
(3) checkpoint da Task 2 aprovado pelo Alex com o passo 7 (iPhone) declarado como limitação
conhecida — conforme o próprio critério de aceite do plano permite.

## Deviations from Plan

None - plan executado exatamente como escrito. As duas investigações adicionais
(`escopos:2` e normalização de lote na venda pendente) não são desvios do plano — são
exatamente o que o `<action>` da Task 1 já pedia ("registrar... o que passou, o que não
passou, limitações conhecidas"), aprofundadas por rigor antes de declarar "não é bug" no
relatório (verificação retroativa contra banco virgem, sem redo de nenhum passo já feito).

## Issues Encountered

None. Nenhum defeito encontrado no exercício ponta-a-ponta nem na verificação humana.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Next Phase Readiness

- **Fase 2 (Realismo de Mercado) completa**: MERC-01, MERC-02, MERC-03, MERC-04 todos
  fechados no REQUIREMENTS.md, os 7 planos da fase (02-01..02-07) com SUMMARY.
- Limitação conhecida carregada para o futuro: verificação nativa (iPhone/TestFlight) do
  fluxo de ordem pendente (`deviceStore`) ainda não foi feita ao vivo — o Alex confirmou
  que não testaria agora. Recomendado como primeiro item de verificação humana da próxima
  vez que houver uma build de TestFlight nova, já que "defeitos de sync já apareceram só
  ali antes" (texto do próprio roteiro do plano).
- Nenhum bloqueio de código conhecido. Suíte canônica completa e build do front verdes no
  estado final commitado.

---
*Phase: 02-realismo-de-mercado*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: qa/48-fase2-verificacao-e2e-ordens-pendentes.md
- FOUND: .planning/phases/02-realismo-de-mercado/02-07-SUMMARY.md
- FOUND commit: fa37a56 (docs, Task 1 — exercício ponta-a-ponta)
- Acceptance criteria da Task 1: re-verificadas (ver seção "Veredito" e tabela do
  relatório) — todas PASS.
- Acceptance criteria da Task 2: 8 passos percorridos e registrados; passo 7 declarado
  como limitação conhecida (não omitido); resposta do Alex registrada literalmente
  ("aprovado", com a ressalva do passo 7).
