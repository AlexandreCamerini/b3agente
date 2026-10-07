---
phase: 47-didatica-expectativa-matematica-x-taxa-de-acerto
plan: 02
subsystem: didatica
tags: [skill_ref, copy, HistoricoPill, DIDA-02]
requires: [47-01]
provides:
  - skill_ref.RECONCILIACAO_POR_QUE_IMPORTA_ROTULO + espelho copy.reconciliacaoPorQueImportaRotulo
  - HistoricoPill abre setorId="expectativa" com dadosExpectativa
key-files:
  modified:
    - server/app/skill_ref.py
    - web/src/copy.js
    - web/src/App.jsx
    - server/tests/test_skill_ref.py
    - web/tests/test_reconciliacao_elegibilidade.mjs
metrics:
  tasks: 2
  completed: 2026-10-07
---

# Phase 47 Plan 02: destino do toque da cláusula -> expectativa-matematica Summary

A cláusula tocável do microtexto de reconciliação (Estudo) agora abre o conceito expectativa-matematica com n, janela, expR e estado do histórico do card; a frase não mudou.

## Commits
- b818ce94 feat(47-02): rótulo da cláusula tocável em skill_ref com espelho em copy.js
- c11dcddd feat(47-02): HistoricoPill abre expectativa-matematica com os números do caso

## Detalhes
- Rótulo "a expectativa matemática" nasce em skill_ref.py (nota de reversão datada 2026-10-06) e é espelhado byte a byte em copy.js; VoiceOver lê "O que é a expectativa matemática?".
- `dadosExpectativa` sobrepõe `estado` (histórico) ao do timing só nessa folha; null não vira 0.
- Guardião reconciliado com nota datada (gate `!operador &&` agora antes de `setorId="expectativa"`); asserções novas: sem `setorId="analise"` em HistoricoPill, `setorId="analise"` preservado no arquivo, sem literal do rótulo no App.jsx, paridade do rótulo, cadeia SETORES/CONCEITOS/kb.
- `rotulo="a confluência"` em App.jsx: antes 2, depois 1.

## Verificação
- pytest test_skill_ref + test_conceitos: 72 passed.
- node: test_reconciliacao_elegibilidade, test_setor_toque, test_conceito_ui, test_historico_ui, test_vocabulario_espelho, test_telas_registro: exit 0.
- `npx vite build` ok; `npx cap copy ios` executado (sem mudanças rastreadas).

## Deviations from Plan
Um ajuste: a regex da asserção de `dadosExpectativa` foi corrigida (o `{}` em `dados || {}` quebrava `[^}]*`) — erro do teste, não do código.

## Known Stubs
None.

## Self-Check: PASSED
