---
phase: quick-261006-qre
plan: 01
subsystem: web/finance + CapitalCurve
tags: [evolucao, curva, regressao-261006-dvf]
requires: [261006-dvf]
provides: [equityCurve.curvaCompleta, CURVA_EVOLUCAO]
key-files:
  modified:
    - web/src/finance.js
    - web/src/App.jsx
    - web/src/copy.js
    - server/app/skill_ref.py
    - web/tests/test_retorno_acumulado_base.mjs
    - web/tests/test_vocabulario_espelho.mjs
    - server/tests/test_retorno_acumulado_base.py
metrics:
  completed: 2026-10-06
---

# Quick 261006-qre: curva da Evolução não pode ser recortada

A janela do retorno (retAcum, drawdown, base, benchmark) segue medida só desde `inicio`; a exibição agora mostra a série inteira, com o trecho anterior pontilhado e legenda de uma linha.

## Commits
- c0bd06d6 — fix: equityCurve expõe `curvaCompleta`, `datasCompleta`, `inicioNaCurvaCompleta`, `diasJanela`; `days` = série inteira (limiar `hasSeries` não some com janela reiniciada). Mesma referência de `curve`/`datas` quando k === 0.
- dfa7e314 — fix: CapitalCurve desenha `ec.curvaCompleta`; trecho 0..k pontilhado `1 3` + opacidade 0.45 (distinto do `3 3` do Ibovespa), marcador vertical em k, legenda só com k > 0 e `baseDesde` válida; Ibovespa continua em `ec.datas`, desenhado em `xAt(i + k)`. Legenda via `skill_ref.CURVA_EVOLUCAO` ↔ `COPY.*.curvaEvolucao` (byte a byte, guardião de vocabulário atualizado).

## Verificação
- Verdes: test_retorno_acumulado_base, test_finance, test_numeros_fundamentados, test_c09_drawdown_alerta, test_fase21_dedup_consolidacao, test_benchmark_curva, test_chart_colors_theme_aware, test_vocabulario_espelho, test_telas_registro; pytest test_retorno_acumulado_base.py + test_skill_ref.py (69 passed); `npx vite build` ok; `npx cap copy ios` ok.
- `git diff` vazio em `web/src/persistence.js` e `server/tests/fixtures/`. Bloco `switch (petTela)` intocado.
- Suíte canônica completa NÃO rodada (a cargo do orquestrador).

## Deviations from Plan
Nenhuma de lógica. Nota: com k === 0 a área usa `L${xAt(0).toFixed(1)}` = `L0.0` em vez de `L0` literal (geometria idêntica).

## Known Stubs
Nenhum.

## Self-Check: PASSED
