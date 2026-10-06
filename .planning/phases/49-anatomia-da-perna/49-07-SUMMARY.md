---
phase: 49-anatomia-da-perna
plan: 07
subsystem: front-opcoes
tags: [anatomia, fiacao, ordem-da-tela]
requires: [49-05, 49-06]
provides: [fiação store/didática em PernasAbertas, ordem posição → pernas → objetivos]
key-files:
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/opcoes/ObjetivoAtivo.jsx
    - web/tests/test_opcoes_fluxo_render.mjs
decisions:
  - "Com pernas, o h2 vira 'Sua posição em {ticker}' e a pergunta dos objetivos desce para um h3 (anat_objetivos_titulo) após pernas e estrutura; sem pernas, tela do 48 intacta"
metrics:
  tasks: 2
  files: 3
  completed: 2026-10-06
---

# Phase 49 Plan 07: Fiação final Summary

`OpcoesScreen` passa `store`, `didatica`, `kbCatalogo` e `onAbrirVerbete={abrirVerbeteLocal}` às duas montagens de `PernasAbertas` (objetivo e Montar) e corrige a fonte da estrutura para `opcoesPorTicker[x].proposta.estrutura` (antes sempre null). `ObjetivoAtivo` lê posição → pernas → objetivos quando há pernas.

## Commits
- feat(49-07): ObjetivoAtivo posição → pernas → objetivos
- feat(49-07): OpcoesScreen fiação + blocos novos do guardião de fluxo

## Verificação
- Todos os guardiões que leem OpcoesScreen/ObjetivoAtivo/PernasAbertas/AnatomiaPerna/PosicaoTotal, mais anatomia_render, escada_espelho e consolidacao_ui: verdes. `npx vite build` verde. App.jsx sem diff.
- Guardião test_opcoes_fluxo_render: blocos novos datados "Fase 49 (2026-10-06)"; nenhuma asserção apagada (2 montagens, regex do LastroDoAtivo, "Montar com ITUB4", 3 Encerrar intactos).
- Não rodei suíte canônica nem `cap copy ios` (conforme restrição).

## Deviations from Plan
Os dois commits dividem o guardião de fluxo: o commit da Task 1 cobre só ObjetivoAtivo; os blocos de teste de ambas as tarefas entraram no commit da Task 2.

## Known Stubs
Nenhum. A pendência do 49-06 (fiação) está resolvida.

## Self-Check: PASSED
