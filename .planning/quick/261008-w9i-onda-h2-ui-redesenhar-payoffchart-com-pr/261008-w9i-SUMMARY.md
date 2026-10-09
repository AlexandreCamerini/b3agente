---
phase: quick-261008-w9i
plan: 01
status: complete
completed: 2026-10-08
commits:
  - 49418525 test(261008-w9i): guardião test_ui_onda_h2 (RED)
  - 4387f571 feat(261008-w9i): PayoffChart na linguagem da Onda H
  - 6bdbd2aa test(261008-w9i): reconcilia test_payoff_responsivo com a Onda H2
---

# Quick 261008-w9i: Onda H2 - PayoffChart na linguagem da Onda H

PayoffChart passa a usar viewBox = largura medida, plot de 244px, eixo Y de ate 3 ticks (H-D3), eixo X de 3 ticks a 12px, marcadores numerados no topo (strike, breakeven, spot) e legenda numerada fora do SVG. Zero numero financeiro novo.

## Arquivos
- `web/src/opcoes/PayoffChart.jsx`: desenho reescrito sobre `montarGeometria` + primitivas.
- `web/src/opcoes/PayoffPrimitivas.jsx`: `traco` opcional por marcador (default "3 3").
- `web/src/copy.js`: 4 chaves (`opcoesLegStrike`, `opcoesLegHoje`, `opcoesSerieTotal`, `opcoesSerieLeitura`) em estudo e operador.
- `web/tests/test_ui_onda_h2.mjs` (novo), `web/tests/test_payoff_responsivo.mjs` (reconciliado).

## Verificacao
- test_ui_onda_h2 RED na Task 1, GREEN na Task 2.
- Bateria da Task 3 (payoff_responsivo, ui_onda_h2/h/a/b/c1/e/f/g, chart_colors_theme_aware, ritmo_sp, cartao_v6_camadas, curadoria_ui, explicacao_payoff, estrutura_para_payoff, vocabulario_opcoes/espelho, copy_theme, todos test_opcoes_*): nenhuma falha. `npx vite build` ok.
- test_payoff_responsivo: 30 -> 33 asserções `ok(`; itens 1, 6 e 8 com NOTA 2026-10-08.
- `git diff main --stat`: so os 5 arquivos acima; App.jsx, 4 chamadores e server/ intocados.

## Deviations
Nenhuma. Decisoes H2-D1..D9 aplicadas como no plano.

## Para H3 (nao implementado)
P1 (area/hachura), P2 (curvas por perna), P3 (tabela alternativa), seta de ilimitado do GraficoAnatomia.
