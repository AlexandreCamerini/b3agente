---
phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor
plan: 01
subsystem: motor-deterministico
tags: [setups, marcos, stop, alvo, rr, sizing, tdd]
requires: []
provides:
  - niveis_tecnicos, marcos_do_plano, marcos_da_posicao, validar_marcos, rr_da_entrada, revalidar_na_execucao, sizing_por_risco, MOTIVO_SEM_PRECO_VALIDAR (server/app/setups.py)
  - fixture compartilhada backend-front (server/tests/fixtures/marcos_casos.json)
affects: [plano_operacional (alta), plano_do_resultado, detect_setups, signal_replay (mede a regra nova sem mudar a chamada)]
key-files:
  created:
    - server/tests/test_marcos_plano.py
    - server/tests/fixtures/marcos_casos.json
  modified:
    - server/app/setups.py
    - server/tests/test_plano_operacional.py
    - server/tests/test_qa39.py
decisions:
  - "Resistencia dentro de 0,25xATR da entrada e ignorada (e o nivel rompido, nao teto)"
  - "marcos_da_posicao: sem suporte abaixo do preco, stop = preco - 1xATR (origem piso_1atr)"
  - "Constantes de motivo (MOTIVO_SEM_ATR, MOTIVO_SO_COMPRA, MOTIVO_PERSEGUICAO) exportadas em setups.py para reuso pelos planos seguintes"
metrics:
  tasks: 3
  tests: "33 em test_marcos_plano + 178 nos 9 arquivos tocados"
---

# Phase 50 Plan 01: Funcao unica de marcos Summary

Funcao pura e unica de marcos (stop com folga de 0,1xATR, alvo na primeira resistencia relevante ou entrada+2R, R:R canonico a partir da entrada, geometria, revalidacao na execucao e sizing por risco limitado por alocacao) em `server/app/setups.py`; o plano COMPRAR do Radar e do replay sai dela.

## Commits
- 06ed6905 test(50-01): RED marcos/geometria/R:R + fixture
- ae563887 feat(50-01): funcoes puras de marcos, geometria e R:R
- (test) RED revalidacao/sizing (fixture preenchida)
- 6f9d37cf feat(50-01): revalidacao na execucao e sizing por risco
- e6ee2e65 feat(50-01): plano do Radar (alta) sobre marcos_do_plano; detect_setups anexa niveis; guardioes com nota

## Comportamento
- `detect_setups` devolve `niveis` (atr/suportes/resistencias); `plano_do_resultado` repassa a `plano_operacional(setup, close, niveis=)`.
- Alta: COMPRAR com `alvo`, `origemStop`, `origemAlvo`, `atr`, `gatilho`, `invalidacao` (crus); `alvo2 = alvo`, `alvo1 = 1R`, `rr1 = 1.0`. Marcos invalidos -> NAO OPERAR com motivo do motor. Sem ATR -> NAO OPERAR (T-50-01).
- Baixa/neutro: byte a byte como antes (caso fixo travado em teste).
- `RR_MINIMO` reusado (nenhum literal 1.5 novo; contagem de `1.5` fora de comentarios inalterada: 1).

## Deviations from Plan
- [Rule 1] test_qa39::test_plano_rejeita_alvo_do_lado_errado: com `alvoSugerido` ignorado na alta (D-04), o resultado deixa de ser NAO OPERAR; o guardiao agora afirma `alvo2 > entrada > stop` por construcao (nota Fase 50). test_adr017/test_setups/test_setups_br ja passavam sem edicao.
- `test_perseguicao_de_preco_corta_pelo_rr_real` passava pelo motivo errado (sem ATR); agora usa `niveis` e checa "Teto proximo demais".

## Known Stubs
Nenhum.

## Self-Check: PASSED
