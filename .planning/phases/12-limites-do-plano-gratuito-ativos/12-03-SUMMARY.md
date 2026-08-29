---
phase: 12-limites-do-plano-gratuito-ativos
plan: 03
subsystem: testing
tags: [pytest, fastapi, plan, metering, adr]

requires:
  - phase: 12-01
    provides: PLAN_FREE.max_analyses_per_month=30 já ativado
provides:
  - Guardião de comportamento do cap mensal de análises (10 testes)
  - ADR-010 registrando a ativação técnica v1.3
affects: [Fase 13 (uso real visível na interface)]

tech-stack:
  added: []
  patterns:
    - "Isolamento B3_DB_PATH temporário + reimport de app.main (mesmo padrão de test_fase3_gate_plano.py/test_fase5_gate_mensal.py/test_fase12_cap_watchlist.py)"
    - "Ledger sempre semeado via metering.consume, nunca kv_set direto"
    - "Prova de que o ledger decide: espião no call site + monkeypatch que zera month_used"

key-files:
  created:
    - server/tests/test_fase12_cap_analises.py
  modified:
    - docs/adr/010-planos-e-cap-gratuito.md

key-decisions:
  - "Regressão do plano de execução original (executor em worktree isolado travou 8h sem nenhum commit, killado pelo orquestrador) — Task 1/2 executadas inline, sem subagente"
  - "/api/buy no teste de não-regressão precisou de pregao.in_market_hours forçado True (padrão já usado em test_ciclo_imediato_apos_carteira.py) para exercitar a execução imediata, não a ordem pendente"
  - "positions é lista de dicts, não dict por ticker — corrigido no primeiro rodar dos testes (a suposição errada foi pega pela própria suíte, não passou despercebida)"

patterns-established:
  - "grep -c \"402\" no arquivo de teste tem de dar 0 — nem docstring pode citar o código HTTP interno que as rotas de análise nunca devolvem (mesma disciplina de test_fase5_gate_mensal.py)"

requirements-completed: [CAP-02, CAP-03, CAP-04, CAP-05]

duration: ~50min (inline, após kill do executor travado)
completed: 2026-08-29
---

# Phase 12: Limites do plano gratuito ativos — Plan 03 Summary

**Suíte de comportamento (10 testes) provando que o cap mensal de 30 análises nega de verdade nas duas rotas via o ledger real, mais registro da ativação técnica v1.3 no ADR-010**

## Performance

- **Duration:** ~50min de execução real (após o kill do executor em worktree que travou 8h sem progresso)
- **Tasks:** 2/2
- **Files modified:** 2 (1 criado, 1 editado)

## Accomplishments
- `test_fase12_cap_analises.py`: 10 testes cobrindo CAP-02 (negação nas duas rotas, mensagem exata), CAP-03 (prova por espião + prova por zerar o ledger — critério de sucesso 2 do ROADMAP), CAP-04 (conta pro nunca negada, unitário + rota), CAP-05 (estado/cotações/compra/segunda análise continuam funcionando após a recusa), mais `/api/ai/quota` (monthLimit=30 real) e D-06 (cap anônimo nunca dispara)
- ADR-010 atualizado: Status sai de "Proposto" pra "Parcialmente aceito", seção nova registra os números ativados, o que fechou do item 5 original, o bypass do PUT fechado pelo 12-02, a grandfather clause, a copy sem CTA e a consequência aceita do BYOK (cap protege custo do app, não volume de uso de conta BYOK)

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Suíte de comportamento do cap mensal de análises** - `42ea67e` (test)
2. **Task 2: Registrar a ativação no ADR-010** - `45942c8` (docs)

## Files Created/Modified
- `server/tests/test_fase12_cap_analises.py` - 10 testes de comportamento do cap mensal (277 linhas)
- `docs/adr/010-planos-e-cap-gratuito.md` - Status atualizado + seção "Atualização — ativação técnica (v1.3, Fase 12, 2026-08-29)" apensada ao final

## Decisions Made
- Executor original (subagente em worktree isolado) travou por 8h sem nenhum commit — morto pelo orquestrador após confirmação do usuário; Tasks 1 e 2 refeitas inline, na main working tree, sem subagente. A worktree travada (`agent-ad49e9209b2372c3a`) não tinha nenhum commit — removida sem perda de trabalho.
- `/api/buy` no teste de não-regressão (caso g) precisou de `pregao.in_market_hours` forçado `True` — sem isso o teste ficaria sujeito ao relógio real da máquina (às vezes mercado fechado → ordem pendente em vez de execução imediata, tornando a asserção de posição flaky). Mesmo padrão já usado em `test_ciclo_imediato_apos_carteira.py`.
- Contrato de `/api/buy` (`positions` é lista, não dict por ticker) foi verificado por leitura de `store.py` só depois que a primeira tentativa (assumindo dict) falhou — corrigido antes de prosseguir, sem inventar contrato daí em diante.

## Deviations from Plan

None nas tasks em si — plano executado como escrito. A única deviation é de PROCESSO (documentada acima): execução inline em vez de subagente isolado, por causa do stall do executor original.

## Issues Encountered
- Executor original travado 8h sem commits (worktree `agent-ad49e9209b2372c3a`, plano 12-03) — matado pelo orquestrador, worktree removida (nada commitado, nada perdido). Ver histórico da sessão para o diagnóstico completo (harness reportava `running`, worktree parada exatamente no commit-base).
- Primeira versão do teste `test_g_apos_recusa_mensal_resto_do_app_continua_respondendo` assumiu `positions` como dict — TypeError na primeira rodada, corrigido lendo `store.py` (positions é lista de dicts com chave `t`).
- Acceptance criterion `grep -c "402"` retornando 0 exigiu reescrever 3 trechos de docstring/comentário que citavam o código HTTP interno por extenso — trocados por descrição sem o número literal, sem perder a explicação da armadilha do FIX-C01.

## User Setup Required

None - nenhuma configuração de serviço externo necessária.

## Next Phase Readiness

CAP-02/03/04/05/07 (Fase 12 inteira) fechados — junto com 12-01/12-02, todos os requirements da Fase 12 estão cobertos. Pronto para a Fase 13 (exibir os números reais na interface), que depende do endpoint novo de `max_watchlist`/contagem de watchlist que ainda não existe (só `/api/ai/quota` expõe o par de análises hoje).

---
*Phase: 12-limites-do-plano-gratuito-ativos*
*Completed: 2026-08-29*
