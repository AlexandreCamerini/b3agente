---
phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor
plan: 09
subsystem: web-ui
tags: [marcos, stop-alvo, modal, d-17, d-18]
requires: [50-06, 50-07, 50-08]
provides: ["StopAlvoModal sobre store.marcos", "estado plano invalido no card", "regua/bloco do plano pelo motor"]
key-files:
  modified:
    - web/src/App.jsx
    - web/src/estruturaCard.js
    - web/tests/test_marcos_ui.mjs
    - web/tests/test_estrutura_card_logica.mjs
    - web/tests/test_carteira_lastro_ui.mjs
    - web/tests/test_execucao_fora_pregao.mjs
    - web/tests/test_cartao_v6_aberto.mjs
    - web/tests/test_cartao_posicao_enxuto.mjs
    - web/tests/test_modo_operador.mjs
    - web/tests/test_copy_theme.mjs
metrics:
  tasks: 3
  completed: 2026-10-22
---

# Phase 50 Plan 09: UI dos marcos do motor Summary

Modal de stop/alvo, card e bloco do plano passam a exibir e aplicar só os marcos do motor (store.marcos), com Aplicar sempre habilitado e a recusa do motor visível no próprio modal.

## Commits
- 50684d80 feat(50-09): StopAlvoModal sobre os marcos do motor, Aplicar sempre habilitado e recusa no modal
- 69438035 feat(50-09): toggle de gestao, estado plano invalido no card e rotulos de R:R
- 28ed3d1a feat(50-09): bloco do plano e regua do Estudo sobre o plano do motor, guardioes com nota D-12

## O que mudou
- localProposal e cenários por perfil removidos; modal busca `store.marcos` ao abrir, mostra stop/alvo/R:R do plano com a frase de origem (`origem_*`); falha de rede mostra "—" + motivo, nunca número estimado.
- IA só explica (explicacao/riscos/quandoRevisar). `applyStopAlvoFor(t, stop, alvo, onRecusa)` não fecha o modal em erro; mensagem do motor em `role="alert"` com `modal_recusa_titulo`. Marcos inválidos no cliente também só mostram o motivo (sem PUT).
- Toggle de gestão automática (checkbox 22px/label 44px, `gestaoAuto !== false`) via `A.setGestaoAuto`.
- estruturaCard: `estado_plano_invalido` (leitura fresca) vence falta stop/alvo; card v6 mostra `textoInvalido` + botão Redefinir (abre o modal) e linhas `rr_atual`/`rr_plano`; AtivoCard usa o rótulo `rr_atual`; compra exibe `marcosTexto`.
- PlanoOperacionalBloco: linhas via `bloco_stop/alvo/breakeven/rr`; régua do Estudo lê `planoMotor` (stop/entrada/alvo numéricos), legenda `regua_alvo`; sem `alvoSugerido`/"ALVO 2:1"/"Alvo 1 (parcial".
- Guardiões da invariante anotados "Fase 50 / D-12".

## Testes
Todos saem 0: test_marcos_ui (21 ok), test_estrutura_card_logica (101), test_decisao_modo (10), test_posicao_stop_alvo (9), test_rr_min_fonte_unica (21), test_cartao_v6_logica (138), test_trailing_dinamico_ui (25), test_alvo_dinamico_ui (8), test_carteira_lastro_ui (29), test_execucao_fora_pregao (50), test_cartao_v6_aberto (36), test_cartao_posicao_enxuto (48), test_plano_ui (90), test_modo_operador (23), test_sinal_chip_ui (46), test_radar_leitura_rapida (10), test_copy_theme; pytest test_adr013_rbac 26 passed; `npx vite build` ok.

## Deviations from Plan
1. [Rule 3] test_modo_operador.mjs e test_copy_theme.mjs travavam os textos antigos ("Stop (invalidação do setup)", `ctx.cp.notaStopAlvo`); asserções trocadas por `"bloco_stop"` / `"modal_ia_explica"` com nota "Fase 50", nenhum `ok(` apagado.
2. [Rule 1] `plano={operador && sc ? sc.plano : null}` é travado por dois guardiões (test_modo_operador, test_radar_leitura_rapida); em vez de mudá-lo, novo prop `planoMotor` alimenta só a régua do Estudo.
3. Legenda da régua usa "STOP"/"ENTRADA" literais (a frase `bloco_stop` é longa demais para legenda); só o alvo vem do vocabulário (`regua_alvo`). Caption "PLANO DO SETUP (didático)" mantido (guardião test_sinal_chip_ui). test_plano_ui.mjs não precisou de mudança (trata de plano comercial, não do plano do setup).
4. Textos fixos fora do vocabulário (sem chave existente): "Redefinir", "CALCULANDO…", "CÁLCULO DO MOTOR", e mensagens de marcos ainda calculando/indisponíveis no modal.

## Deferred
- `notaStopAlvo` ("Sugestão por perfil…") permanece em copy.js/skill_ref sem uso na tela; remover exigiria mexer na paridade Python.

## Known Stubs
Nenhum.

## Self-Check: PASSED
