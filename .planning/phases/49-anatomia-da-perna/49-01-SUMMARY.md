---
phase: 49-anatomia-da-perna
plan: 01
subsystem: vocabulario-opcoes
tags: [skill_ref, copy, paridade, opcoes]
requires: []
provides: [anat_* em OPCOES_ESCADA (64 chaves x 2 modos), espelho em copy.js, guardião de paridade Fase 49]
affects: [49-03, 49-04, 49-06]
key-files:
  modified:
    - server/app/skill_ref.py
    - web/src/copy.js
    - web/tests/test_opcoes_escada_espelho.mjs
decisions:
  - "Chaves pernas_* preservadas (fallback do 48-16)"
metrics:
  tasks: 2
  files: 3
completed: 2026-10-06
---

# Phase 49 Plan 01: Vocabulário da anatomia da perna Summary

64 chaves `anat_*` em `skill_ref.OPCOES_ESCADA` (educacional e operador), espelhadas byte a byte em `COPY.estudo/operador.opcoesEscada`, travadas pelo guardião de paridade estendido.

## Commits
- 003341b8 feat(49-01): vocabulário anat_* + espelho copy.js
- 686deb89 test(49-01): guardião de paridade — bloco Fase 49

## Verificação
- `grep -c '"anat_' skill_ref.py` = 128; `copy.js` = 128
- `node web/tests/test_opcoes_escada_espelho.mjs` e `test_opcoes_caminho_b_ui.mjs` verdes; `pytest tests/test_skill_ref.py` 48 passed
- `opcoes_escada_txt('educacional','anat_frase_call_compra', ...)` interpola sem "{" residual
- Prova negativa: alterar uma letra de `anat_erro` só em skill_ref.py fez o guardião sair 1; revertido, volta a sair 0. (Plano pedia alterar em copy.js; a divergência é simétrica, alterei no .py.)
- `npx vite build` verde.

## Deviations from Plan
None - plano executado como escrito (exceto o lado da prova negativa, acima).

## Self-Check: PASSED
