---
phase: 44-motor-estrutura-por-ativo
plan: 03
subsystem: api
tags: [options, estrutura, fastapi]
requires: [44-01, 44-02]
provides:
  - "GET /api/options/proposta/{ticker} com chave aditiva `estrutura`"
affects: [45-card]
key-files:
  modified: [server/app/main.py]
  created: [server/tests/test_estrutura_posicao_rota.py]
decisions:
  - "Estrutura calculada sobre todas as pernas do underlying, com cadeia buscada por vencimento distinto; get_quote só se nenhuma cadeia ok trouxer spot"
metrics:
  tasks: 2
  files: 2
completed: 2026-09-29
---

# Phase 44 Plan 03: estrutura na rota de proposta Summary

`options_proposta` devolve `estrutura` (via `estrutura_posicao.ler_estrutura`) sobre todas as optionPositions do ativo; try/except próprio faz falha virar `estrutura: None` (log via obslog) sem afetar proposta legada nem gerar 500.

## Tasks
1. Chave aditiva em main.py — 7235c00e
2. Testes de rota (7 testes: collar, sem pernas, degradado, perna fora da cadeia, chave em todos os ramos, falha do motor, zero get_quote) — commit `test(44-03)`

## Verificação
- `cd server && ./.venv/bin/python -m pytest -q tests/test_opcoes_lastreadas_rotas.py tests/test_opcoes_collar.py tests/test_opcoes_lastreadas_proposta.py` -> 105 passed
- `cd server && ./.venv/bin/python -m pytest -q tests/test_estrutura_posicao_rota.py tests/test_estrutura_posicao.py tests/test_opcoes_lastreadas_rotas.py` -> 73 passed
- Rotas `@app.get("/api/options/`: 4 antes e depois.

## Deviations from Plan
None - plano executado como escrito.

## Known Stubs
None.

## Self-Check: PASSED
