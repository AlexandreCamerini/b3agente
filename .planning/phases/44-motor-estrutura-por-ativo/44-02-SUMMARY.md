---
phase: 44-motor-estrutura-por-ativo
plan: 02
subsystem: motor-opcoes
tags: [opcoes, estrutura, motor-puro, tdd]
requires: [44-01]
provides: ["estrutura_posicao.ler_estrutura (contrato consumido pelo Plano 03 e pela Fase 45)"]
affects: []
key-files:
  created:
    - server/app/estrutura_posicao.py
    - server/tests/test_estrutura_posicao.py
  modified: []
decisions:
  - "Estado em dias corridos; exercicio_provavel = ITM estrito (B3 exerce ITM automaticamente)"
  - "encerrar exige lastPrice numérico > 0, igual ao preço que options_lastreada_fechar executa"
  - "liquidity_score recebe volume/OI/bid/ask saneados por _num (lixo vira ausente)"
metrics:
  tasks: 2
  files: 2
  completed: 2026-09-29
---

# Phase 44 Plan 02: Motor de estrutura por ativo Summary

`ler_estrutura` puro: lê todas as pernas do underlying, classifica (call coberta, put de proteção, collar), marca prêmio (ask/bid/last, nunca mid), soma resultado com "incompleto" explícito, calcula faixa via `opcoes_payoff.perfil_da_estrutura`, estado ESTR-04, eixo `abertaSemProposta` e `encerrar`. Todas as frases vêm de `skill_ref`.

## Tasks

| Task | Commits |
|------|---------|
| 1 pernas/classificação/marcação/resultado | 85b84db9 (RED), 0e349a5d (GREEN) |
| 2 faixa/descoberta/estado/encerrar/eixo | RED commit `test(44-02): add failing tests for faixa...`, GREEN `feat(44-02): faixa, descoberta, estado...` |

## Verificação

`cd server && ./.venv/bin/python -m pytest -q tests/test_estrutura_posicao.py tests/test_opcoes_payoff.py tests/test_skill_ref.py` → 139 passed. Caso UGPA3: piso 38, teto 42, perda 1400, ganho 2600, breakeven 39.4, total 100.00.
Greps de pureza (sem httpx/sqlite3/relógio/mid) limpos; a única correspondência do grep de frases é docstring. Sem web/src tocado, sem vite build.

## Deviations from Plan

None - plan executed as written. Nota: `liquidez` por perna alimenta o eixo sem_mercado; perna sem contrato na cadeia tem `liquidez` None e não dispara sem_mercado (cai em premio_indisponivel via estado/motivo da rota).

## Known Stubs

None.

## Self-Check: PASSED
