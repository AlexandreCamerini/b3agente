---
phase: 45-card-de-posi-o-estruturada
plan: 03
subsystem: web-front
tags: [card-posicao, estrutura, hook, guardioes]
requires: [45-01, 45-02]
provides:
  - "useEstruturasPosicao (busca por ativo com pernas, token monotonico global)"
  - "CardPosicaoEstruturada (sem regua/limites: ancora para 45-04)"
  - "TAM_TOTAL_ESTRUTURA, ctx.escopoSeq, ctx.goHistoricoOperacoes, TravaPill({texto})"
affects: [45-04, 45-05]
key-files:
  created:
    - web/tests/test_estrutura_card_ui.mjs
  modified:
    - web/src/App.jsx
key-decisions:
  - "Task 1 e Task 2 tocam o mesmo arquivo de forma entrelacada (componente + hook + branching): um commit feat unico e um commit test separado para o guardiao"
  - "Botoes Stop/alvo (IA) e Registrar saida do card estruturado usam 11.5px/700 (escala fechada do plano) em vez de 12.5px/800 do card atual; cores e handlers herdados"
requirements-completed: [CARD-01, CARD-03, CARD-04, CARD-05, CARD-06]
completed: 2026-09-29
---

# Phase 45 Plan 03: Card de posicao estruturada ligado a Posicoes

Hook `useEstruturasPosicao` (uma chamada `store.optionsProposta(t, true)` por ativo com pernas, teto 3, sem polling, last-response-wins com token monotonico nunca zerado) e `CardPosicaoEstruturada` (header, chips, pill, estado, resultado M1/M3, pernas, fonte + Atualizar, Encerrar que so navega) com branching em `CarteiraScreen`.

## Commits

| Task | Commit | Resultado |
|------|--------|-----------|
| 1+2 componente, hook, branching, ctx | fb372fa4 | vite build ok |
| 2 guardiao test_estrutura_card_ui.mjs | d3542aaf | 41 asserts ok |

## Exceção deliberada ao D-02

Ativo sem opcao continua com o card atual, com uma unica mudanca visivel: `R:R atual` so renderiza com stop E alvo (`mostraRR(p)`, W-001). Antes o legado mostrava "R:R atual —" sem stop/alvo. Ressalva: com stop e alvo definidos mas `cur <= p.stop` o legado ainda mostra "—" (formula existente, fora do escopo).

## Guardioes realmente executados (saida 0 conferida)

node: test_estrutura_card_ui, test_estrutura_card_logica, test_hero_reconciliado, test_setor_toque, test_carteira_lastro_ui, test_ritmo_sp, test_api_parity, test_estrutura_card_espelho, test_estrutura_espelho.
pytest: server/tests/test_opcoes_collar_vocab.py + server/tests/test_skill_ref.py (47 passed).
`cd web && npx vite build`: exit 0.
NAO rodados (orquestrador): suite completa, `npx cap copy ios`.
`git diff` em persistence.js, api.js e server/: vazio.

## Deviations from Plan

None - plano executado como escrito. Notas de implementacao:
- Chip de vencimento com `dias` nulo mostra `cp.chipVence(ddmm, "—")` ("vence DD/MM · — dia(s)"); caso raro (motor sem diasParaVencimento).
- `aceita()` do hook tambem exige `pedidasRef.current[t] === assinatura` (descarta resposta de ticker removido/assinatura superada), alem do token.
- Falha apos `Atualizar` em leitura previamente ok vira "falha" (descarta a estrutura anterior), conforme o plano.
- `TravaPill` mantem o estilo atual (contorno AA e do 45-04).

## Known Stubs

Nenhum. A ancora `45-04: régua de faixa + bloco de limites (M2)` e ponto de insercao deliberado do proximo plano.

## Self-Check: PASSED

Arquivos: test_estrutura_card_ui.mjs e App.jsx presentes; commits fb372fa4 e d3542aaf no git log. STATE.md e ROADMAP.md intocados.
