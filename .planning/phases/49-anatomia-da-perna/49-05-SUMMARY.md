---
phase: 49-anatomia-da-perna
plan: 05
subsystem: api-opcoes
tags: [anatomia, rota, refactor, custo-zero]
requires: [49-03]
provides: [GET /api/options/anatomia/{ticker}, _estrutura_do_ativo]
affects: [49-06]
key-files:
  modified:
    - server/app/main.py
  created:
    - server/tests/test_opcoes_anatomia_rota.py
decisions:
  - "Estrutura cotada vem do mesmo helper nas duas rotas; anatomia independe do gate de liquidez"
metrics:
  tasks: 2
  files: 3
completed: 2026-10-06
---

# Phase 49 Plan 05: Rota da anatomia Summary

Rota grátis `GET /api/options/anatomia/{ticker}` (custoMcp 0, sem cap, fora de `/mcp/`) devolve anatomia por perna + estrutura cotada, com posições e preço médio lidos só do escopo do token. O bloco de estrutura de `options_proposta` foi extraído para `_estrutura_do_ativo` (retorna `(estrutura, spot, source)`), sem mudança de resposta.

## Commits
- e8ce8c6f feat(49-05): extrai _estrutura_do_ativo
- 8bcfbf17 feat(49-05): rota options_anatomia + testes
- (fix) docstring da rota sem citar o cap, para o teste por source passar

## Verificação
- Proposta/estrutura (test_estrutura_posicao_rota, _v6, test_opcoes_lastreadas_rotas/_proposta): 88 passed sem alteração.
- test_opcoes_anatomia_rota + test_anatomia_perna + test_opcoes_escada_rotas + test_mcp_guardioes: verdes (129 passed na última rodada).
- Cobertos: ok com ações a 30,00, excluir ACOES/perna, 400 (id inválido, >20, ticker curto), sem_pernas, cadeia degradada (Hoje None com motivo), erro do motor vira estado "erro" (nunca 500), isolamento entre contas, ausência de _cap_check e /mcp/.
- Não rodei suíte canônica nem vite (só server).

## Deviations from Plan
Nenhuma de lógica. Nota: o commit da rota saiu antes do ajuste de docstring (o teste de source-grep pegava "_cap_check" no próprio docstring); corrigido em commit seguinte.

## Known Stubs
None.

## Self-Check: PASSED
