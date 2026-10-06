---
phase: 49-anatomia-da-perna
plan: 03
subsystem: motor-opcoes
tags: [anatomia, payoff, tdd, motor-puro]
requires: [49-01]
provides: [anatomia_perna.ler_anatomia, MAX_PONTOS_ANATOMIA, ACOES_ID]
affects: [49-04, 49-05, 49-06]
key-files:
  created:
    - server/app/anatomia_perna.py
    - server/tests/test_anatomia_perna.py
decisions:
  - "Grade independe de excluir (chip não move o slider)"
  - "Sem fórmula de payoff nova: tudo via opcoes_payoff"
metrics:
  tasks: 2
  files: 2
completed: 2026-10-06
---

# Phase 49 Plan 03: Motor puro da anatomia da perna Summary

`ler_anatomia` entrega por perna valor pago/recebido, pior caso, equilíbrio, prazo em dias corridos, pontos de payoff no vencimento e "Hoje" vindo da estrutura cotada, mais o total por ativo (pernas marcadas + ações só com preço médio do simulador) e o total "sem esta perna", tudo numa grade única de preços. Contrato de saída exatamente o do plano.

## Commits
- 9452c670 test(49-03): testes do motor (RED, falha por módulo ausente)
- 5edfbd1f feat(49-03): motor puro (GREEN)

## Verificação
- `pytest tests/test_anatomia_perna.py tests/test_estrutura_posicao.py tests/test_skill_ref.py`: 121 passed
- `pytest tests/test_opcoes_payoff*.py`: 65 passed
- Cenário ITUB4 conferido: total −277,00 em 48,00; sem a PUT −37,00; contribuição da PUT −240,00; com ações +800,00 → 523,00; identidade total = semEsta + contribuição em todo índice.
- Pureza: grep de httpx/db/relógio/anthropic = 0; `opcoes_payoff.` referenciado.
- Não rodei a suíte canônica nem vite (plano toca só server/app novo e teste novo).

## Deviations from Plan
None - plano executado como escrito.

## Known Stubs
None.

## Self-Check: PASSED
