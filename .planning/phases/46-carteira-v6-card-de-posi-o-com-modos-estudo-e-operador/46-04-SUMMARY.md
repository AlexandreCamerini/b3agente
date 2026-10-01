---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 04
subsystem: fiação backend do card v6
tags: [estrutura_posicao, carteira_leitura, paridade_stores, cartao_posicao]
requires: ["46-03"]
provides:
  - "estrutura.cenarios / estrutura.didatica (chaves aditivas de GET /api/options/proposta/{t})"
  - "POST /api/carteira/leitura"
  - "carteiraLeitura em serverStore e deviceStore"
affects: [46-05]
key-files:
  modified:
    - server/app/estrutura_posicao.py
    - server/app/main.py
    - web/src/api.js
    - web/src/persistence.js
  created:
    - server/tests/test_estrutura_posicao_v6.py
    - server/tests/test_carteira_leitura_rota.py
    - web/tests/test_carteira_leitura_paridade.mjs
decisions:
  - "ler_estrutura recebe modo 'estudo' (cfg.appMode) mas o motor do card fala 'educacional': mapeamento explícito em estrutura_posicao (operador -> operador, resto -> educacional)"
  - "_faixa devolve 6 elementos (entrada do payoff no fim); única chamada ajustada"
metrics:
  tasks: 2
  completed: 2026-10-01
---

# Phase 46 Plan 04: Fiação do card v6 Summary

`ler_estrutura` ganhou `cenarios` e `didatica` de forma aditiva (falha isolada em try/except, caem para None) e a rota pura `POST /api/carteira/leitura` devolve a leitura do plano de cada posição, com `carteiraLeitura` nos dois stores.

## Tarefas

| # | Tarefa | Commit |
|---|--------|--------|
| 1 | estrutura com cenarios/didatica + pytest UGPA3/CXSE3/ITSA4 | ac5998e6 |
| 2 | rota /api/carteira/leitura + api.js + stores + testes | 3231c4e0 |

## Verificação

- `pytest tests/test_estrutura_posicao_v6.py test_estrutura_posicao.py test_estrutura_posicao_rota.py test_opcoes_collar_rota.py`: 87 ok (testes das Fases 44/45 sem edição).
- `pytest tests/test_carteira_leitura_rota.py`: 12 ok.
- UGPA3 BE 38,01 / +4.240 / −38.010; CXSE3 BE 19,81 / +1.210 / −19.810; ITSA4 sintético `cenarios: null` + "aguardando o cálculo do app".
- `test_carteira_leitura_paridade.mjs`, `test_fase3_paridade_stores_generica.mjs` (server=86/device=86), `test_api_parity.mjs`: ok. `npx vite build`: ok.

## Deviations from Plan

**1. [Rule 1 - Bug] Modo "estudo" não é "educacional"**
- **Found during:** Task 1
- **Issue:** `ler_estrutura` é chamada com `cfg.appMode` ("estudo"); `cartao_posicao` só gera simulador/didática quando `modo == "educacional"`, então o Estudo ficaria sem cenários didáticos.
- **Fix:** mapeamento `operador`/resto->`educacional` antes de chamar o motor do card; teste dedicado.
- **Files:** server/app/estrutura_posicao.py

Teste TDD em commit único por tarefa (teste + implementação juntos), não RED/GREEN separados.

## Known Stubs

Nenhum.

## Self-Check: PASSED
