---
phase: 49-anatomia-da-perna
plan: 04
subsystem: front-opcoes
tags: [anatomia, svg, a11y, encerrar, ssr-guardiao]
requires: [49-01, 49-03]
provides: [GraficoAnatomia, AnatomiaPerna]
affects: [49-05, 49-06]
key-files:
  created:
    - web/src/opcoes/GraficoAnatomia.jsx
    - web/src/opcoes/AnatomiaPerna.jsx
    - web/tests/test_opcoes_anatomia_render.mjs
  modified:
    - web/tests/test_opcoes_caminho_b_ui.mjs
decisions:
  - "GraficoAnatomia é genérico (perna compacta e total): texto só por props, sem import de copy.js"
  - "Perda = hachura 45 graus + sinal; ganho liso; nenhuma cor de texto positive/negative/warn"
metrics:
  tasks: 2
  files: 4
completed: 2026-10-06
---

# Phase 49 Plan 04: GraficoAnatomia + AnatomiaPerna Summary

Card por perna que só renderiza o contrato do motor (frase, condição, prazo em dias, Pior caso, Equilíbrio tocável via `opc-equilibrio`, Hoje ou chip "Sem cotação" com motivo), curva SVG com hachura de perda, tabela alternativa e Encerrar em 2 passos que informa o que se sabe e o que não se sabe, vetado apenas por `encerrar.permitido === false`.

## Commits
- a8c8d684 feat(49-04): GraficoAnatomia
- (RED) test(49-04): guardião SSR da anatomia da perna
- 2f70d832 feat(49-04): AnatomiaPerna + registro de ambos em NOMES do guardião do caminho B

## Verificação
- `test_opcoes_anatomia_render.mjs`: 36 ok, saída 0 (RED confirmado antes: módulo ausente).
- `test_opcoes_caminho_b_ui.mjs` OK com os dois componentes em NOMES (reduced-motion, alvo 44, sem `?? 0`, contraste AA).
- As 11 varreduras por diretório + `test_opcoes_fluxo_render` + `test_opcoes_escada_espelho`: verdes.
- `npx vite build` verde. Greps de aceite: palavras proibidas 0, `opc-equilibrio` 1, cor de texto positive/negative/warn 0.
- Não rodei a suíte canônica nem `cap copy ios` (conforme restrição).

## Deviations from Plan
Menor: no guardião SSR, as asserções "nunca 0,00" usam `R$ 0,00` (e não `0,00`), porque a tabela de preços tem "50,00", que contém "0,00". Mesma intenção, sem falso positivo.

## Known Stubs
None. Os componentes ainda não estão montados em tela; a fiação é dos planos seguintes (49-05/06).

## Self-Check: PASSED
