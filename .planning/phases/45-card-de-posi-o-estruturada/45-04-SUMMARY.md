---
phase: 45-card-de-posi-o-estruturada
plan: 04
subsystem: web-front
tags: [card-posicao, regua, contraste, guardioes]
requires: [45-02, 45-03]
provides:
  - "ReguaFaixa (faixa no vencimento: piso/teto/PM/hoje + stop/alvo)"
  - "Bloco de limites, Stop/Alvo, contexto e aviso sem stop no CardPosicaoEstruturada"
  - "TravaPill com prop opt-in contorno"
  - "test_estrutura_card_contraste.mjs; test_estrutura_card_ui e test_ritmo_sp estendidos"
key-files:
  created:
    - web/tests/test_estrutura_card_contraste.mjs
  modified:
    - web/src/App.jsx
    - web/tests/test_estrutura_card_ui.mjs
    - web/tests/test_ritmo_sp.mjs
requirements-completed: [CARD-02, CARD-05, CARD-06]
completed: 2026-09-29
---

# Phase 45 Plan 04: Régua de faixa, limites e contorno da pill

`ReguaFaixa` (top-level, antes de `CardPosicaoEstruturada`, fora das fatias dos guardiões) desenha a régua de 2px sem gradiente, com marcadores de forma distinta, pontas abertas ("sem piso"/"sem teto") e `role="img"` com `cp.estruturaFaixaAria`. O card ganhou caixa de limites neutra (`T.bgBase`, sem cor semântica), linha Stop/Alvo, contexto (dias, % do capital, R:R só com stop e alvo, setup de entrada) e aviso sem stop via `mostraAvisoSemStop(p, "estruturada", e)`. "definir stop e alvo" nunca é desabilitado. `TravaPill` recebeu `contorno` (default false, legado byte a byte).

## Commits

| Task | Commit | Resultado |
|------|--------|-----------|
| 1 (+ TravaPill opt-in) | 0072b619 | vite build ok |
| 2 guardiões | 2606cce0 | UI estendido, contraste novo, ritmo SP estendido |

## Deviations from Plan

**1. [Rule 3] TravaPill implementada no commit da Task 1.** As chamadas com `contorno` ficaram no mesmo commit do card (arquivo entrelaçado); a Task 2 só acrescentou os guardiões.

**2. Reversão deliberada em `test_estrutura_card_ui.mjs`.** A asserção "âncora do 45-04 presente" (do 45-03) virou "âncora consumida e `<ReguaFaixa …/>` renderizada", com nota no arquivo. Nenhuma outra asserção removida.

**3. Guardião de contraste:** o escuro declara `positive/negative` como `BRAND.green/red`; o teste resolve via objeto `BRAND` (sem afrouxar limiar). `test_ritmo_sp.mjs`: só adições (0 linhas removidas).

## Dívida conhecida

`TravaPill` legado (AtivoCard e card atual) segue com `negative` sobre `negativeTint10` fora de AA no claro. Razão medida nas 4 combinações (informativa, não assertada): dark·estudo 4.90, dark·operador 5.28, light·estudo 4.18, light·operador 4.18. O contorno do card novo mede >= 4.79 (light) e >= 5.60 (dark). Estender o contorno ao legado fica como pergunta do checkpoint 45-05.

## Guardiões realmente executados (exit 0 conferido)

node: test_estrutura_card_ui, test_estrutura_card_logica, test_estrutura_card_contraste, test_ritmo_sp, test_carteira_lastro_ui (sem diff), test_opcoes_consolidacao_ui, test_concentracao_carteira, test_carteira_opcoes_tira, test_hero_reconciliado, test_setor_toque, test_opcoes_continuidade_ui, test_opcoes_abrir_ticker, test_estrutura_card_espelho, test_cor_confiabilidade: todos 0.
pytest: `server/tests/test_opcoes_collar_vocab.py` 11 passed.
`cd web && npx vite build`: exit 0.
Não rodados (orquestrador): suíte completa, `npx cap copy ios`.

## Known Stubs

Nenhum.

## Self-Check: PASSED

Arquivos presentes; commits 0072b619 e 2606cce0 no git log; STATE.md e ROADMAP.md intocados.
