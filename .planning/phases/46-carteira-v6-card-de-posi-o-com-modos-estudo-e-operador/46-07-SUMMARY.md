---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 07
subsystem: web/App.jsx (card aberto v6)
tags: [carteira, estudo, operador, simulador, payoff, kb]
requires: [46-01, 46-02, 46-03, 46-04, 46-06]
provides: [SimuladorEstudo, TermosTocaveis, PayoffOperador, GradeConta]
key-files:
  created: [web/tests/test_cartao_v6_camadas.mjs]
  modified: [web/src/App.jsx, web/tests/test_estrutura_para_payoff.mjs]
requirements-completed: [CART6-03, CART6-04]
completed: 2026-10-01
---

# Phase 46 Plan 07: camadas Estudo e Operador do card aberto

Estudo ganha simulador "e se?" por índice da grade do backend e termos tocáveis ancorados na KB; Operador ganha payoff no vencimento (SVG novo, sem texto) e grade 3x2 com a conta. Nenhum número é calculado no front.

## Entregue
- `SimuladorEstudo`: slider `min=0 step=1` sobre índices; preço/resultado/zona lidos de `pontoDoIndice`; chips Hoje/Equilíbrio/Teto/Alta forte via `indiceNomeado` (omitidos sem ponto); caixa de zona `role=status` com texto do backend, borda/glifo por `zonaVisual`; trilho com segmentos e rótulos sem colisão.
- `TermosTocaveis`: termo só vira botão com `verbeteDoCatalogo(ctx.kbCatalogo, kb)` válido; um por vez; painel com definição da KB, "No seu caso:" do backend (ou "aguardando o cálculo do app") e "Entendi" devolvendo o foco. Montado fora do flip, só no Estudo, com `e.didatica` ou `leituraPlano.didatica`.
- `PayoffOperador`: SVG `role=img` + `aria-label` do backend, zero `<text`, fundo vermelho/verde no BE, K e hoje tracejados, ◆ BE como overlay HTML; legenda abaixo. Único cálculo: funções de layout `xDoGrafico`/`yDoGrafico`.
- `GradeConta`: colunas por `colunasDaGrade` (ResizeObserver + escala de texto), células `aria-expanded`, conta `{formula, numeros}` ou `conta_sem_formula`; sem ⓘ/termos.
- Montagem em `data-area-cenario`; sem `cenarios` permanece a caixa `sem_cenario`.
- `PayoffChart.jsx` e `estruturaParaPayoff.js` intactos.

## Commits
- b0219073 feat(46-07): componentes e montagem em App.jsx
- 1c7b3759 test(46-07): `test_cartao_v6_camadas.mjs` novo; `test_estrutura_para_payoff.mjs` ampliado (nota Fase 46)

## Verificação
`npx vite build` ok. Verdes: cartao_v6_camadas, estrutura_para_payoff, payoff_responsivo, cartao_v6_aberto, cartao_v6_fechado, cartao_posicao_espelho, ritmo_sp, estrutura_card_contraste, copy_theme, fase22_componentes_compartilhados, hero_reconciliado, posicao_stop_alvo, estrutura_card_ui, carteira_lastro_ui. Nenhum guardião antigo precisou de ajuste.

## Deviations from Plan
- skill_ref.py / copy.js (listados em files_modified) não precisaram de edição: todas as chaves de copy já existiam (46-01).
- Commit de tarefas agrupado em um `feat` (App.jsx) + um `test`, pois as duas tarefas editam o mesmo arquivo em região contígua.

## Known Stubs
Nenhum. Caso `cenarios` exista sem `simulador` no Estudo (ou sem `payoff` no Operador), a área fica vazia; o backend entrega o bloco conforme o modo (46-03).

## Self-Check: PASSED
