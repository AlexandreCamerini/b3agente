---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 12
subsystem: web/card-posicao
tags: [gap-closure, G-06]
requires: ["46-11"]
provides: [FaixaVencimento com rótulos ancorados e legenda hoje]
key-files:
  modified:
    - web/src/App.jsx
    - web/tests/test_cartao_v6_fechado.mjs
requirements: [CART6-01, CART6-02, CART6-03, CART6-04, CART6-05, CART6-06, CART6-07]
metrics:
  completed: 2026-10-01
---

# Phase 46 Plan 12: faixa ancorada (G-06) Summary

Status: Task 1 concluída; Task 2 (checkpoint humano no iPhone) PENDENTE.

`FaixaVencimento` recebe `leitura={leituraPlano}`; "hoje" usa `leitura.preco` (nunca marcação) e entra no domínio da régua. O grid de 3 colunas saiu: "◆ equilíbrio R$ x" e "teto R$ x" são posicionados pelo x do marcador (`rotulosSemColisao` + `ancoraRotulo`, padrão do SimuladorEstudo) e valores usam `rsNbsp`. Legenda "● hoje R$ x" com notas "· sem piso" / "· sem teto". Segmentos/ALFA, role="img" e aria-label intactos.

## Commits
- 690a09aa feat(46-12): FaixaVencimento ancorada
- e2064aa3 test(46-12): 5 asserções G-06 em test_cartao_v6_fechado (nota "46-UAT (2026-10-01, G-06)")

## Verificação
- `npx vite build` ok; 14 guardiões (lista do plano + test_sinal_chip_ui) verdes. Nenhuma reancoragem necessária em test_estrutura_card_ui.

## Deviations from Plan
Adicionado `rsNbsp` ao import de estruturaCard.js (ainda não importado no App.jsx). Nada além disso.

## Known Stubs
None.

## Checkpoint
Task 2 (human-verify) PENDENTE: aprovação do Alex no iPhone, G-01..G-06 + passos do 46-08.
