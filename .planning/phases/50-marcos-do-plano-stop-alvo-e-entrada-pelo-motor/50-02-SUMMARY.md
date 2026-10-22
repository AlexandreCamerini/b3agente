---
phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor
plan: 02
subsystem: vocabulario
tags: [skill_ref, copy.js, espelho, adr-015, claude-md]
requires: []
provides:
  - skill_ref.MARCOS_PLANO + marcos_plano_txt (24 chaves, 2 modos)
  - copy.js COPY[modo].marcosPlano + marcosPlanoTxt
  - CARTAO_POSICAO: estado_plano_invalido, plano_invalido_detalhe, rr_plano; rr_atual relabelado
affects: [50-03..50-09]
key-files:
  created: [server/tests/test_marcos_vocabulario.py]
  modified: [server/app/skill_ref.py, web/src/copy.js, web/tests/test_vocabulario_espelho.mjs, web/tests/test_cartao_posicao_espelho.mjs, CLAUDE.md, docs/adr/015-assertividade-do-motor-de-recomendacao.md]
decisions:
  - rr_atual = "R:R restante (do preço atual)" nos dois modos (neutra); rr_plano = "R:R do plano (da entrada)"
  - chaves novas do card entram em NEUTRAS (idênticas nos dois modos)
metrics:
  tasks: 2
  completed: 2026-10-22
---

# Phase 50 Plan 02: Vocabulário dos marcos do motor Summary

Vocabulário completo da fase fixado (interface-first) em skill_ref ↔ copy.js com espelho byte a byte travado, mais nota datada da invariante D-12 no CLAUDE.md e adendo de quebra de série no ADR-015.

## Commits
- 27fe310f feat(50-02): vocabulario MARCOS_PLANO e chaves do card v6 espelhados
- 95c1fa9b feat(50-02): nota D-12 no CLAUDE.md e adendo de quebra de serie no ADR-015

## Verificação
- pytest tests/test_marcos_vocabulario.py + test_cartao_posicao.py + test_skill_ref.py: 73 passed
- node web/tests/test_vocabulario_espelho.mjs: todos passam (inclui MARCOS_PLANO)
- node web/tests/test_cartao_posicao_espelho.mjs: todos passam
- npx vite build: ok
- git diff CLAUDE.md/ADR-015: 0 linhas removidas

## Deviations from Plan

**1. [Rule 3 - Blocking] Parser do guardião não aceitava dígito em chave**
- `paresDoModo` em test_vocabulario_espelho.mjs usava `[a-zA-Z_]+`; chaves `origem_stop_piso_1atr` e `origem_alvo_projecao_2r` eram descartadas em silêncio no lado Python (4 falhas).
- Fix: regex passou a `[a-zA-Z0-9_]+`, com nota "Fase 50". Nenhuma verificação removida.

**2. Texto educacional de gestao_breakeven** foi suavizado para não sugerir perda máxima eliminada ("sai sem perda, descontados custos e eventual gap") — princípio 8.

**3. CLAUDE.md**: a nota D-12 entrou como linhas de continuação abaixo do bullet existente (diff só com adições), em vez de editar a última linha do bullet.

## Known Stubs
Nenhum. As chaves ainda não têm consumidores; os planos 03-09 as usam.

## Self-Check: PASSED
