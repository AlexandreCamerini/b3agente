---
phase: 49-anatomia-da-perna
plan: 02
subsystem: web-opcoes
tags: [opcoes, anatomia, stores, paridade, hook]
requires: []
provides:
  - api.opcoesAnatomia(t, q)
  - opcoesAnatomia nos dois stores (serverStore e deviceStore)
  - useAnatomia / chaveAnatomia / buscarAnatomia
affects: [49-06]
tech-stack:
  patterns: [delegação paritária de store, descarte de resposta velha por contador]
key-files:
  created:
    - web/src/opcoes/useAnatomia.js
    - web/tests/test_opcoes_anatomia_stores.mjs
  modified:
    - web/src/api.js
    - web/src/persistence.js
key-decisions:
  - "Os dois stores delegam a api.opcoesAnatomia; o aparelho não duplica cálculo"
  - "Modo entra na chave do hook (frase/condição vêm do servidor por modo)"
metrics:
  tasks: 2
  files: 4
  completed: 2026-10-06
---

# Phase 49 Plan 02: contrato de dados da anatomia no front

`GET /api/options/anatomia/{ticker}` (custo MCP 0) exposto por `api.opcoesAnatomia` e delegado pelos dois stores, mais o hook `useAnatomia` com chave primitiva, descarte de resposta velha e dado anterior preservado durante o recálculo.

## Commits
- 0defc6c4 feat(49-02): opcoesAnatomia em api.js e nos dois stores
- 27d50f9f feat(49-02): hook useAnatomia + guardião de paridade dos stores

## Verificação
- test_opcoes_anatomia_stores.mjs, test_fase3_paridade_stores_generica.mjs, test_opcoes_tecnico_stores.mjs, test_api_parity.mjs: verdes
- `npx vite build`: ok (o hook ainda não é importado por ninguém; será consumido no 49-06)

## Deviations from Plan
Task 2 (tdd): o guardião e o hook foram criados e commitados juntos, sem commit RED separado `test(...)`. Comportamento coberto pelo guardião, que passa.

## Known Stubs
Nenhum. A rota do backend nasce no 49-05; até lá a chamada retornaria erro 404 real (nada é inventado).

## Self-Check: PASSED
