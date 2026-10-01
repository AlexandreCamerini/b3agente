---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 02
subsystem: web-ui-logic
tags: [carteira-v6, estruturaCard, puro, tdd]
requires: []
provides:
  - "10 helpers puros em web/src/estruturaCard.js (ancoraRotulo, rotulosSemColisao, flipDuracaoMs, prefereMovimentoReduzido, faceInicial, estadoPrincipalV6, pontoDoIndice, indiceNomeado, zonaVisual, colunasDaGrade)"
affects: [46-05, 46-06, 46-07]
tech-stack:
  added: []
  patterns: ["helper puro devolve chave de CARTAO_POSICAO + vals; UI resolve o texto", "guardião estático anti-aritmética em campo financeiro"]
key-files:
  created: [web/tests/test_cartao_v6_logica.mjs]
  modified: [web/src/estruturaCard.js]
key-decisions:
  - "estadoPrincipalV6: risco do motor (vencida/exercício provável) > travadas > sem plano/incompleto > enum posicaoNoPlano > dentro (só sem estrutura)"
  - "prefereMovimentoReduzido lê matchMedia na hora; sem cache"
  - "colunasDaGrade com entrada inválida cai em 2 colunas"
requirements-completed: [CART6-01, CART6-02, CART6-03, CART6-04]
duration: ~10min
completed: 2026-10-01
---

# Phase 46 Plan 02: Helpers puros do card v6 Summary

10 funções puras (sem React/I/O) em `web/src/estruturaCard.js` com prioridade de estado D-13, âncora/anti-colisão de rótulos, flip com movimento reduzido, leitura da grade do simulador por índice, zona visual e colunas da grade; 92 asserções verdes.

## Commits
- 239dcea6 test(46-02): RED (módulo sem as funções)
- b0393716 feat(46-02): GREEN (helpers em estruturaCard.js)

## Verificação
- `node web/tests/test_cartao_v6_logica.mjs`: 92 ok, exit 0
- `node web/tests/test_estrutura_card_logica.mjs`: exit 0 (intocado)
- `npx vite build` em web/: ok
- grep: 10 exports; 0 ocorrências de REDUCE_MOTION; `qtyLivre` importado de `./finance.js`

## Deviations from Plan
Nenhuma de regra. Notas: pontoDoIndice com índice não finito (NaN) devolve null (spec cobria só não inteiro); estadoPrincipalV6 sem `p` não gera principal de plano. O guardião estático ignora comentários ao varrer o corpo das funções.

## Known Stubs
Nenhum.

## Threat Flags
Nenhum. T-46-04 e T-46-05 mitigados (guardião estático; clamp/null sem exceção).

## Self-Check: PASSED
