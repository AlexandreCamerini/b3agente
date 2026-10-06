---
phase: 48-opcoes-caminho-b
plan: 11
subsystem: ajuda-tour
tags: [App.jsx, AJUDA.md, tour, toast, guardioes]
requires: ["48-01"]
key-files:
  modified: [web/src/App.jsx, docs/AJUDA.md, web/tests/test_tour_opcoes.mjs, web/tests/test_telas_registro.mjs, web/tests/fixtures/telas_baseline_41.json]
requirements-completed: [OPC-11, OPC-12, OPC-07]
metrics:
  completed: 2026-10-05
---

# Phase 48 Plan 11: Ajuda/tour sem Watchlist e toast do caminho B Summary

Ajuda e tour da aba Opções passam a falar da Carteira (via `cp.opcoesAjudaEstuda` / `cp.opcoesTourPasso`), docs/AJUDA.md espelha, e executar pela escada mostra "Ordem simulada registrada. Nenhuma ordem real foi enviada.".

## Commits
- af7944bb feat(48-11): Ajuda, tour e toast do caminho B
- 7e371e07 test(48-11): reancora guardiões de tour/telas

## Entregue
- `ajudaSecoes.opcoes`: 1º parágrafo = `cp.opcoesAjudaEstuda`; 2º mantido (fim de pregão, travessão nunca zero); 3º reescrito (abrir ativo/escada não gasta consultas; "Comparar vencimentos" diz antes o custo; "Nenhuma ordem sai desta aba").
- `tourPassos.opcoes`: texto = `cp.opcoesTourPasso`; título "4 · Estude estruturas em ..." preservado.
- `executarCandidatoCurado`: `origem === "escada"` usa `cp.opcoesEscada.toast_executada` (fallback `curadoriaExecutada`) e track `escada_`.
- `test_tour_opcoes.mjs`: 5 asserções novas por modo/espelho (sem Watchlist/Monitoramento/"da sua lista"; Carteira; fim de pregão; travessão). Nenhum `ok(` removido.
- `test_telas_registro.mjs`: +1 asserção datada (opcoes segue no tour, por último).

## Deviations from Plan
**1. [Rule 3 - Bloqueio] `test_telas_registro` ficou vermelho (6 falhas)** — o fixture `telas_baseline_41.json` congelava o texto antigo do passo 4 do tour e da seção Opções da Ajuda (comparação byte a byte). Contrário ao esperado pelo plano ("âncora preservada"): id/ordem preservados, mas o texto congelado mudou por desenho. Fix: atualizei SÓ o passo/seção de Opções no fixture (script verificou que qualquer outra diferença abortaria), com nota datada em `_origem.reancoragem_fase48` (guardião não se apaga; reversão deliberada atualiza com nota). Os 6 entradas atualizadas; resto do fixture intacto.

## Verificação
- `npx vite build`: ok.
- `test_tour_opcoes`, `test_telas_registro`, `test_pet_opcoes`, `test_opcoes_escada_espelho`, `test_vocabulario_opcoes`: verdes.
- Greps de aceite: `escolhido na sua " + tWl` = 0; "um ativo da sua lista" = 0; seção Opções do AJUDA.md sem "Watchlist" e com "Nenhuma ordem sai desta aba".
- Suíte canônica não rodada (orquestrador, por onda).

## Known Stubs
Nenhum. A origem `"escada"` ainda precisa ser passada pelo chamador da escada (planos de UI da fase); aqui só o despacho foi preparado.

## Self-Check: PASSED
- Commits af7944bb e 7e371e07 existem; arquivos modificados presentes; STATE.md/ROADMAP.md intocados.
