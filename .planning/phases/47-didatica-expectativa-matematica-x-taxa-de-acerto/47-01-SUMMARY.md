---
phase: 47-didatica-expectativa-matematica-x-taxa-de-acerto
plan: 01
subsystem: didatica
tags: [conceitos, kb, setores, DIDA-01]
requires: []
provides:
  - conceitos.TEXTO_EXPECTATIVA (fonte única, dois modos)
  - CONCEITOS["expectativa-matematica"] ancorado em n/janela/expR/estado
  - SETORES["expectativa"] (destino do toque no plano 47-02)
  - verbete KB expectativa-matematica (família plano_risco)
affects: [47-02]
key-files:
  modified:
    - server/app/conceitos.py
    - server/app/kb.py
    - server/tests/test_setores.py
    - server/tests/test_kb_catalogo.py
  created:
    - server/tests/test_conceito_expectativa.py
decisions:
  - "Ilustração (40%/3R/1R = +0,6R; 70%/1R/4R = −0,5R) gerada de _ILUSTRACAO_EXPECTATIVA, rotulada como ilustração"
  - "Conceito fora de kb._FAMILIA_DO_CONCEITO; verbete KB manual com texto = conceitos.TEXTO_EXPECTATIVA (identidade)"
metrics:
  tasks: 2
  completed: 2026-10-07
---

# Phase 47 Plan 01: conceito + verbete KB + setor `expectativa` Summary

Expectativa matemática × taxa de acerto como texto determinístico: constante `TEXTO_EXPECTATIVA` (Estudo/Operador) reusada pelo conceito (com n, janela, expR e estado do histórico medido) e pelo verbete KB, mais o setor `expectativa` na allowlist do assistente.

## Commits
- 54ed9f0a feat(47-01): conceito expectativa-matematica + TEXTO_EXPECTATIVA + setor expectativa
- c2a28ecb feat(47-01): verbete KB expectativa-matematica com o mesmo texto do conceito

## Detalhes
- Formatadores novos `expR` (sinal +/−U+2212, 3 casas, só número não-bool) e `n` (milhar pt-BR). `ROTULOS` continua antes da constante (espelho de vocabulário verde).
- Estados insuficiente/nunca_medido usam a frase fixa "Não há dados suficientes para concluir." sem placeholder.
- Contagens do catálogo KB reconciliadas com nota datada: 93 -> 94 e 84 -> 85.

## Verificação
- pytest: test_conceito_expectativa, test_setores, test_conceitos, test_conceitos_opcoes_escada, test_guardrail_imperativo (69 passed); test_kb_catalogo, test_kb, test_kb_ancoras (45 passed com o novo); recorte `-k "kb or conceito or assistente or didatica or guardrail or glossario or setores or pet"` 301 passed, 1 xfailed.
- `node web/tests/test_vocabulario_espelho.mjs` ok. Front não tocado (sem vite build). Suíte canônica fica com o orquestrador.

## Deviations from Plan
None - plano executado como escrito (ajustes do checker aplicados: grep de `"texto": conceitos.TEXTO_EXPECTATIVA` = 1; test_vocabulario_espelho no verify).

## Known Stubs
None.

## Self-Check: PASSED
