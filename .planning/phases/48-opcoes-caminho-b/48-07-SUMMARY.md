---
phase: 48-opcoes-caminho-b
plan: 07
subsystem: opcoes-mcp
tags: [mcp, cap, escada-matriz, adr-027]
requires: [48-04]
provides:
  - "POST /api/options/mcp/escada-matriz (matriz vencimento x 3 degraus x 3 objetivos, custo 2N+1)"
affects: [48-08, 48-09]
key-files:
  modified: [server/app/options_mcp_api.py, server/tests/test_mcp_guardioes.py]
  created: [server/tests/test_options_mcp_escada_matriz.py]
requirements-completed: [OPC-06]
metrics:
  completed: 2026-10-05
---

# Phase 48 Plan 07: Rota paga da matriz "Comparar vencimentos" Summary

Rota nova `POST /api/options/mcp/escada-matriz` com o mesmo desenho de custo de `/possibilidades` (1 + 2xN, reserva em duas etapas), servindo os 3 objetivos numa consulta so; `/possibilidades` intocada.

## Commits
- 31b61136 feat(48-07): rota escada-matriz + 13 testes
- de7f0894 test(48-07): guardiao (iv) cobre escada-matriz e reserva em duas etapas

## Entregue
- Reserva 1 (`propose_option_setups {ticker}` descobre vencimentos) e depois `_cap_check(uid, 2 * len(escolhidos))`; por vencimento, `get_option_chain` PUT e CALL com `limit=LIMITE_MAX`. `chamadasPrevistas` = 2N+1 (1 se nao ha vencimento), igual ao gasto real (testado).
- Pedido de vencimento inexistente nao vira chamada; teto N_MAX_VENCIMENTOS=6 (13 chamadas).
- Itens com `total_negocios < OPERAVEIS_MIN_NEGOCIOS` descartados antes do seletor; degraus por `opcoes_escada.celulas_da_cadeia` (nenhum calculo financeiro novo).
- Erro de tool num vencimento: linha com 3 celulas vazias (`id`/`total` None) e `motivo` = mensagem do servico; os demais seguem. Erro de servico (McpErro/ValueError) encerra a rota com `_erro_http`, sem 200 parcial.
- Posicao e modo lidos do servidor (`store.get(_conn, "positions"/"config", user_id=uid)`); posicao no corpo e ignorada (T-48-26). Sem posicao: celulas vazias com motivo.
- Resposta: ticker, pregao, precoObjeto, fonte, at, frescor, vencimentosConsiderados, chamadasPrevistas, matriz{proteger,renda,collar}[{vencimento,celulas,motivo}], motivo, cap.
- Guardiao: teste explicito em `test_mcp_guardioes.py` (rota na lista descoberta; `_cap_check` chamado 2x). Apenas linhas adicionadas.

## Decisoes
- `store` e `opcoes_escada` importados direto em `options_mcp_api` (sem ciclo: store so depende de db/defaults/catalog); nao foi preciso novo parametro em `configure()`.
- spot = `underlying_price` de `propose_option_setups` (ja na 1a chamada); cai para o da cadeia so se ausente.

## Deviations from Plan
None - plano executado como escrito.

## Verificacao
- `pytest tests/test_options_mcp_escada_matriz.py tests/test_options_mcp_api.py tests/test_mcp_cap.py tests/test_adr013_cobertura_rotas.py tests/test_opcoes_escada_rotas.py`: 181 passed.
- `pytest tests/test_mcp_guardioes.py tests/test_opcoes_fronteira.py tests/test_options_mcp_escada_matriz.py`: 121 passed.
- `grep -c '@router.post("/escada-matriz")'` = 1; diff de `options_mcp_api.py` so remove a linha de import (ampliada); `possibilidades()` intocada.
- Suite canonica e vite build nao rodados (backend only; suite e do orquestrador).

## Known Stubs
Nenhum.

## Threat Flags
Nenhum (T-48-23..27 mitigados).

## Self-Check: PASSED
- Arquivos presentes; commits 31b61136 e o de task 2 existem; STATE.md/ROADMAP.md intocados.
