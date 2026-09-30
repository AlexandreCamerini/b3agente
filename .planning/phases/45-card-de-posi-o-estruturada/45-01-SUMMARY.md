---
phase: 45-card-de-posi-o-estruturada
plan: 01
subsystem: vocabulário (skill_ref.py <-> copy.js)
tags: [copy, paridade, collar, guardiao]
requires: []
provides:
  - skill_ref.ESTRUTURA_CARD + estrutura_card_txt
  - COPY[modo].estruturaCard + estruturaCardTxt + chaves neutras do card
affects: [45-02, 45-03, 45-04]
key-files:
  created:
    - server/tests/test_estrutura_card_vocab.py
    - web/tests/test_estrutura_card_espelho.mjs
  modified:
    - server/app/skill_ref.py
    - web/src/copy.js
    - web/tests/test_opcoes_collar_ui.mjs
    - .planning/REQUIREMENTS.md
decisions:
  - "Manchete collar de OPCOES_LASTREADAS não tocada (P1, guardrail CVM); âncora trocada só nas chaves visíveis do copy.js"
  - "CARD-06 anotado com reversão deliberada D-11, sem marcar como concluído"
metrics:
  tasks: 2
  completed: 2026-09-29
---

# Phase 45 Plan 01: Vocabulário do card estruturado Summary

ESTRUTURA_CARD (6 chaves x 2 modos) em skill_ref.py espelhado byte a byte em COPY[modo].estruturaCard, com rótulos neutros idênticos nos dois modos e a âncora "trava protetora" removida das chaves de collar visíveis do copy.js.

## Commits
- f8d23119 feat(45-01): ESTRUTURA_CARD + estrutura_card_txt, teste py, nota CARD-06
- bf261052 feat(45-01): espelho estruturaCard, neutras, collar sem âncora, guardiões

## Inventário das chaves "collar" (copy.js)
Já usavam "collar" e NÃO mudaram: Estudo `ctaCollarDebito`/`ctaCollarCredito`/`confirmAbrirCollar` (vazio por paridade), `tiraOpcoesMotivo.caixa_insuficiente` (Estudo e Operador), Operador `tiraOpcoesSemSetup`, `estruturaPosicao.nome_collar` e `nome_fora_da_biblioteca`, `curadoriaTipoCollar` (ambos).
Mudaram (âncora "TRAVA PROTETORA"/"trava(s) protetora(s)"/"× TRAVA"/"× trava" -> collar):
- Estudo: `eyebrowPropostaCollar` ("ESTUDO · COLLAR"), `collarPernasLinha` ("× COLLAR").
- Operador: `eyebrowPropostaCollar` ("PROPOSTA · COLLAR"), `collarPernasLinha`, `ctaCollarDebito`, `ctaCollarCredito`, `confirmAbrirCollar` ("Montar N collar(s) de T — trava Q ação(ões) ...").
`badgeTravada` e `avisoTravaNaVenda` inalterados.

## Guardiões
- pytest (test_estrutura_card_vocab, test_skill_ref, test_opcoes_collar_vocab, test_estrutura_posicao): 105 passed.
- node: test_estrutura_card_espelho, test_estrutura_espelho, test_opcoes_collar_ui, test_faixa_liquidez_ui, test_vocabulario_opcoes, test_vocabulario_espelho: todos exit 0. Extras: test_opcoes_proposta_ui, test_api_parity: exit 0.
- Sabotagem `B3_SKILL_REF_PATH=/dev/null`: exit 1 (esperado).
- grep de âncoras em linhas não-comentadas de copy.js: vazio. `npx vite build`: ok.
- `git diff` de test_opcoes_collar_ui.mjs só adiciona linhas.

## Deviations from Plan
None - plano executado como escrito. Nota: o comentário-cabeçalho de ESTRUTURA_POSICAO foi reescrito (só comentário) conforme o plano; OPCOES_LASTREADAS e o corpo de ESTRUTURA_POSICAO intocados.

## Known Stubs
Nenhum. As chaves neutras ainda não são consumidas por App.jsx (consumo nos planos 45-03/45-04).

## Self-Check: PASSED
Arquivos e commits f8d23119, bf261052 verificados. STATE.md e ROADMAP.md intocados.
