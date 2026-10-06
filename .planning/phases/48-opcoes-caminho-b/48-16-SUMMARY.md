---
phase: 48-opcoes-caminho-b
plan: 16
subsystem: opcoes-front
tags: [gap-closure, G-01, G-02, react, ssr-guardian]
requires: ["48-15", "48-10", "48-13"]
provides:
  - "ObjetivoAtivo: frase única de indisponibilidade (objetivosMotivo) + slot pernasAbertas"
  - "PernasAbertas.jsx: lista de pernas abertas com encerrar por perna (A.sellOption, confirmação em 2 passos)"
  - "Fiação no nível objetivo e no Montar de OpcoesScreen"
affects: [web/src/opcoes/ObjetivoAtivo.jsx, web/src/opcoes/PernasAbertas.jsx, web/src/opcoes/OpcoesScreen.jsx, web/tests/test_opcoes_fluxo_render.mjs]
key-files:
  created:
    - web/src/opcoes/PernasAbertas.jsx
  modified:
    - web/src/opcoes/ObjetivoAtivo.jsx
    - web/src/opcoes/OpcoesScreen.jsx
    - web/tests/test_opcoes_fluxo_render.mjs
decisions:
  - "Único veto do botão Encerrar é encerrar.permitido === false do motor; sem leitura de frescor/executavel/gate (guardião estático trava)"
  - "Perna com lastro e perna vendida não ganham sellOption (T-48-57)"
  - "Guardião do Montar é estático (ticker do Montar só nasce por efeito, SSR não roda efeitos)"
metrics:
  tasks: 3
  completed: 2026-10-05
---

# Phase 48 Plan 16: G-01/G-02 front Summary

Tela de objetivo diz a causa real uma vez (com dica) em vez de 3 repetições, e toda perna aberta do ativo aparece em "Suas pernas abertas" com resultado só do motor e Encerrar por perna sem lastro, no objetivo e no Montar.

## Commits
- b55cb05e feat: ObjetivoAtivo frase única + slot de pernas (G-01)
- 6405aeb2 feat: PernasAbertas (G-02), guardião SSR RED->GREEN no mesmo arquivo de teste
- 7d9ed55e feat: fiação em OpcoesScreen + guardião do caminho Carteira

## Verificação
- node web/tests/test_opcoes_fluxo_render.mjs: OK (todos os asserts novos)
- laço dos guardiões que leem OpcoesScreen/ObjetivoAtivo/readdirSync (test_opcoes*.mjs, test_carteira_opcoes_tira.mjs): verde
- npx vite build: ok; App.jsx intocado; "Montar com {t}" (PropostaDoAtivo) intocado
- Não rodados por restrição: suíte canônica e cap copy ios (orquestrador)

## Deviations from Plan
Nenhuma de lógica. O RED da Task 2 foi confirmado (módulo ausente) mas commitado junto do GREEN, pois o guardião é um único arquivo e o plano não pede commit separado de teste.

## Known Stubs
Nenhum.

## Self-Check: PASSED
