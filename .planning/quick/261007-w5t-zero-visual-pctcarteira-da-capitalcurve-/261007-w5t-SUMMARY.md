---
phase: quick-261007-w5t
plan: 01
status: complete
completed: 2026-10-07
commits: [ef5e8262, 849e9a74, 85e9eb8f]
---

# Quick 261007-w5t: CapitalCurve sem zero inventado

`pctDesdeBase(curva, base)` em finance.js devolve null sem base > 0. CapitalCurve deixa de desenhar série plana em 0 % quando a base é indeterminada: sem linha, com "—" centralizado no gráfico e a frase existente de dados insuficientes (fraseRet).

## Commits
- ef5e8262 test: guardião novo (RED, unitário + estático no mesmo arquivo)
- 849e9a74 feat: pctDesdeBase
- 85e9eb8f fix: CapitalCurve religada, diffIbov exige retAcum != null, efeito do Ibovespa não dispara sem base, nota datada no guardião qre

## Deviations
- Override do orquestrador: drawdown e alerta DRAWDOWN ALTO inalterados (itens 11/12 no-op); o teste novo não assevera supressão.
- O arquivo de teste foi criado inteiro (unitário + estático) no commit RED único; a seção estática só passou no commit 3.

## Verificação
- `npx vite build` ok.
- Passam: test_capitalcurve_sem_base, test_retorno_acumulado_base (reconciliado com nota datada), test_benchmark_curva, test_fase21_dedup_consolidacao, test_c09_drawdown_alerta, test_chart_colors_theme_aware, test_numeros_fundamentados, test_vocabulario_espelho.
- Suíte completa, cap copy ios, push e publicação NÃO executados (conforme instrução).
