---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 09
subsystem: vocabulário do card de posição v6
tags: [skill_ref, copy.js, paridade, gap-closure, UAT]
requires: []
provides: [chaves CARTAO_POSICAO do card fechado (G-01..G-06)]
affects: [46-10, 46-11, 46-12]
key-files:
  modified:
    - server/app/skill_ref.py
    - web/src/copy.js
    - server/tests/test_skill_ref.py
    - web/tests/test_cartao_posicao_espelho.mjs
decisions:
  - "faixa_rot_be é a única chave nova não neutra (equilíbrio × BE)"
metrics:
  completed: 2026-10-01
---

# Phase 46 Plan 09: chaves de texto do card fechado v6 Summary

19 chaves novas em `CARTAO_POSICAO` (operador e educacional) espelhadas byte a byte em `COPY.*.cartaoPosicao`, mais o novo texto do cadeado ("Ações travadas pela call · saída após encerrar").

## Tarefas

| Task | Commit | Resultado |
|------|--------|-----------|
| 1 chaves em skill_ref.py + copy.js | 330359d2 | legendas, chip_total_suspenso, linha_acoes/opcoes/estrutura, motivos, chips, faixa_rot_*, faixa_leg_hoje; estado_travadas_todas atualizado |
| 2 guardiões estendidos | 47627c07 | NEUTRAS (mjs e py) + asserções datadas "46-UAT"; novo `test_cartao_posicao_uat_card_fechado` |

## Verificação
- `node web/tests/test_cartao_posicao_espelho.mjs`: verde
- `pytest tests/test_skill_ref.py tests/test_opcoes_collar_vocab.py`: 53 passed
- `npx vite build`: ok

## Deviations from Plan
Nenhuma. Observação: a lista do plano tem 19 chaves; 18 são neutras e `faixa_rot_be` difere por modo. Nenhuma asserção existente foi removida; o texto antigo de `estado_travadas_todas` não era travado por guardião.

## Known Stubs
Nenhum. As chaves ainda não são consumidas pelo JSX (46-10/11/12).

## Self-Check: PASSED
