---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 10
subsystem: web/card-posicao
tags: [gap-closure, G-01, G-02, G-03, G-04, G-05, puro, contraste]
requires: []
provides: [linhasResultadoV6, chipsMetaV6, rsNbsp, rsSinalNbsp, fonteValorCabecalho, pctCapitalTexto, LARGURA_VALOR_PIOR_CASO_PX, vars --cv-pendente-*/--cv-info-*]
affects: [web/src/estruturaCard.js, web/src/cartaoV6Cores.js]
key-files:
  modified:
    - web/src/estruturaCard.js
    - web/src/cartaoV6Cores.js
    - web/tests/test_cartao_v6_logica.mjs
    - web/tests/test_estrutura_card_contraste.mjs
requirements: [CART6-01, CART6-07]
metrics:
  completed: 2026-10-01
---

# Phase 46 Plan 10: Helpers puros e cores do card fechado Summary

Helpers puros (sem aritmética financeira) para o card fechado rótulo/valor, estadoPrincipalV6 reduzido a um único estado e CSS vars pendente/info com contraste travado nas 4 combinações tema x modo.

## Commits
- 8213f883: feat(46-10): helpers puros do card fechado
- 39a49c27: feat(46-10): CSS vars pendente/info e contraste

## O que mudou
- `estadoPrincipalV6`: sem `extras.push`; `extras` sempre `[]`. Travadas usam glifo `cadeado` (tom info). `extra_cotacao_indisponivel` só vira o estado quando nenhum outro ocupa a linha. Resultado parcial e prêmio indisponível passam a ser motivos na linha `Opções · contrato`.
- Novos: `linhasResultadoV6` (cabeçalho = mesma referência de `resultado.total` da linha Estrutura; null vira motivo, nunca 0), `chipsMetaV6`, `rsNbsp`, `rsSinalNbsp` (NBSP, U+2212), `pctCapitalTexto`, `fonteValorCabecalho` (21/18/16/14 px) e `LARGURA_VALOR_PIOR_CASO_PX = 178`.
- `varsCartaoV6` emite `--cv-pendente-bg/-texto` e `--cv-info-bg/-texto`.
- Guardiões: asserções antigas de `extras` reancoradas com nota "46-UAT"; casos novos; 6 funções novas no guardião estático de aritmética; pares `status pendente/info texto/bgCard` nas 4 combinações.

## Verificação
- test_cartao_v6_logica.mjs, test_estrutura_card_logica.mjs, test_estrutura_card_contraste.mjs: verdes.
- pytest tests/test_auditoria_prompts.py: 16 passed. `npx vite build`: ok.
- grep de razões com vírgula nos arquivos de cores/contraste: 0.

## Deviations from Plan
None - plan executed as written. Notas: o padding da tela/card não foi reconferido além do card (`SP[4]`, App.jsx:5606); constante 178 mantida. Caso de teste "cotação indisponível" usa `posicaoNoPlano: null` (com preço nulo o backend não emite posição).

## Known Stubs
None.

## Self-Check: PASSED
