---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 08
subsystem: web/guardioes
tags: [contraste, a11y, ritmo-sp, guardiao]
requires: ["46-07"]
provides: ["guardiao de contraste dos pares v6", "guardiao transversal do card v6"]
affects: [web/src/App.jsx]
key-files:
  created: [web/tests/test_cartao_v6_transversal.mjs]
  modified: [web/tests/test_estrutura_card_contraste.mjs, web/tests/test_ritmo_sp.mjs, web/src/App.jsx]
decisions:
  - "Zonas positive/negative da faixa e do simulador sobem de opacidade 0.5 para 0.75 (medido 2.0-2.5:1 < 3:1); segmento medio 0.35 -> 0.5"
metrics:
  tasks: "1/2 (Task 2 = checkpoint humano PENDENTE)"
  completed: 2026-10-01
status: CHECKPOINT PENDENTE (validacao do Alex)
---

# Phase 46 Plan 08: Guardioes transversais + validacao humana Summary

Contraste dos pares novos do card v6 medido nas 4 combinacoes tema x modo, ritmo SP estendido aos 12 componentes v6 e guardiao transversal de higiene; validacao visual do Alex ainda PENDENTE.

## Tarefas

| Task | Nome | Commit | Arquivos |
| ---- | ---- | ------ | -------- |
| 1a | Contraste (pares de texto >= 4,5 e graficos >= 3,0) + ajuste de opacidade | 950bd03a | web/src/App.jsx, web/tests/test_estrutura_card_contraste.mjs |
| 1b | Ritmo SP nos componentes v6 + guardiao transversal | 2276538a | web/tests/test_ritmo_sp.mjs, web/tests/test_cartao_v6_transversal.mjs |
| 2 | Validacao do Alex nas 4 combinacoes | - | PENDENTE (checkpoint:human-verify) |

## Deviations from Plan

**1. [Rule 1 - Bug] Contraste de zona reprovado a 0.5**
- Medido sobre bgBase: negative@0.5 = 2.40/2.46 (escuro) e 2.16/2.14 (claro); positive@0.5 = 2.02 (claro). Minimos para 3:1: positive 0.47-0.75, negative 0.60-0.70.
- Fix (regra da UI-SPEC "se reprovar, subir opacidade"; nenhum texto mudou para cor de tom): `seg(...)` em FaixaVencimento e SimuladorEstudo 0.5 -> 0.75 e 0.35 -> 0.5 (gradacao preservada). Guardiao mede com `ALFA_ZONA = 0.75` e trava que o App usa 0.75.
- Os retangulos de fundo do PayoffOperador (opacity 0.12/0.10) sao tints de area sem informacao exclusiva (linha/legenda carregam o dado); nao medidos.

**2. Excecoes nomeadas no ritmo SP** (lista fechada, por componente, da UI-SPEC): `TermosTocaveis padding "0 2px"` (excecao c) e `GradeConta gap "1px"` (separador S5). Qualquer outro px solto segue reprovado.

## Verificacao (executor)

- node: contraste, ritmo_sp, cartao_v6_transversal, cartao_v6_{aberto,camadas,fechado,logica}, copy_theme, fase22_componentes_compartilhados, hero_reconciliado, posicao_stop_alvo, estrutura_card_ui, carteira_lastro_ui: todos rc=0.
- `npx vite build` rc=0. Nao rodei o loop completo de web/tests nem `cap copy ios` (escopo do orquestrador). `web_dist` nao foi republicado.

## Known Stubs

Nenhum.

## Checkpoint (Task 2) — PENDENTE

Aguardando "aprovado" do Alex (ou divergencias por combinacao/posicao/passo) conforme how-to-verify do plano (8 passos, 4 combinacoes, 320 px / texto 130 %). Nota: como a opacidade das zonas mudou, o `web_dist`/bundle precisa ser reconstruido antes da conferencia visual.
