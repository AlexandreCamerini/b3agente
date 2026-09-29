---
phase: 44-motor-estrutura-por-ativo
plan: 01
subsystem: vocabulario-opcoes
tags: [skill_ref, copy.js, paridade, opcoes, estrutura]
requires: []
provides:
  - skill_ref.ESTRUTURA_POSICAO (26 chaves x 2 modos) + estrutura_posicao_txt
  - 5 motivos novos em OPCOES_LASTREADAS
  - COPY[modo].estruturaPosicao / opcoesLastreadasMotivo
  - proposta_fechar com motivos contrato_fora_da_cadeia / premio_indisponivel
affects: [44-02, 44-03, 45]
key-files:
  created:
    - web/tests/test_estrutura_espelho.mjs
  modified:
    - server/app/skill_ref.py
    - server/app/opcoes_lastreadas.py
    - web/src/copy.js
    - server/tests/test_skill_ref.py
    - server/tests/test_guardrail_imperativo.py
    - server/tests/test_opcoes_lastreadas_proposta.py
key-decisions:
  - "sem_contrato_liquido/sem_vencimento_elegivel deixam de ser alias de sem_setup (D-06); so tendencia_de_alta segue alias"
  - "proposta_fechar distingue degradado / contrato_fora_da_cadeia / premio_indisponivel (D-07); lastPrice bool recusado"
  - "tiraOpcoesMotivo e collar (trava protetora) intocados: reconciliacao e da Fase 45"
requirements-completed: [ESTR-05, ESTR-06]
completed: 2026-09-29
---

# Phase 44 Plan 01: Contrato de vocabulario da estrutura por ativo

Frases da leitura de estrutura nascem em `skill_ref.ESTRUTURA_POSICAO`, espelhadas byte a byte em `copy.js` com guardiao; motivos de ausencia e de fechamento impossivel agora sao distinguiveis.

## Commits
- f54f2d25 feat(44-01): ESTRUTURA_POSICAO e motivos distintos em skill_ref (Task 1)
- e8d2e6d8 feat(44-01): proposta_fechar com motivos distinguiveis (Task 3)
- a36d345f feat(44-01): espelho estruturaPosicao/opcoesLastreadasMotivo em copy.js + guardiao (Task 2)

## Verificacao
- `cd server && ./.venv/bin/python -m pytest -q tests/test_skill_ref.py tests/test_guardrail_imperativo.py tests/test_opcoes_lastreadas_proposta.py tests/test_opcoes_collar_vocab.py tests/test_faixas_liquidez.py tests/test_opcoes_collar.py tests/test_opcoes_lastreadas_rotas.py tests/test_fuso_dias_ate_vencimento.py` -> 189 passed
- `cd web && node tests/test_estrutura_espelho.mjs` -> todos passaram; `test_vocabulario_espelho.mjs`, `test_opcoes_abertas_e_motivos.mjs`, `test_opcoes_collar_ui.mjs` -> verdes; `npx vite build` -> ok
- Sabotagem controlada: copia do .py em $TMPDIR com "ja" no lugar de "já" em estado_vencida, `B3_SKILL_REF_PATH=<copia>` -> 1 falha, exit 1 (copia nao commitada)

## Deviations from Plan
- Intercalacao de commits: o guardiao de alias (D-06) vive em test_opcoes_lastreadas_proposta.py, que pertence tambem a Task 3; ele foi commitado junto com a Task 3. O commit da Task 1 sozinho deixa esse teste desatualizado (verde so a partir do commit da Task 3).
- Nenhuma outra: plano executado como escrito.

## Known Stubs
Nenhum.

## Self-Check: PASSED
