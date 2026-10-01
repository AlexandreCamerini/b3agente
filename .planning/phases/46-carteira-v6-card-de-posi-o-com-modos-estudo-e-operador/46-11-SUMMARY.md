---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 11
subsystem: web/card-posicao
tags: [gap-closure, G-01, G-02, G-03, G-04, G-05]
requires: ["46-09", "46-10"]
provides: [LinhasResultadoV6, ChipsMetaV6, IconeCadeado, CartaoPosicao cabeçalho nowrap]
key-files:
  modified:
    - web/src/App.jsx
    - web/tests/test_cartao_v6_fechado.mjs
    - web/tests/test_estrutura_card_ui.mjs
    - web/tests/test_cartao_v6_transversal.mjs
    - web/tests/test_ritmo_sp.mjs
requirements: [CART6-01, CART6-07]
metrics:
  completed: 2026-10-01
---

# Phase 46 Plan 11: card fechado (G-01..G-05) Summary

Card fechado com número ou "—" + chip "total suspenso", linhas rótulo/valor com hairline, chips pill da meta, um único estado (cadeado) e valor do cabeçalho que nunca quebra (nowrap, NBSP, redução determinística de fonte).

## Commits
- feat: cabeçalho, LinhasResultadoV6, ChipsMetaV6, IconeCadeado, LinhaEstadoV6 de estado único (App.jsx; hash no git log, "feat(46-11)")
- test: reancoragem dos guardiões e travas nowrap/NBSP/pior caso ("test(46-11)")

## O que mudou
- `CartaoPosicao` consome `linhasResultadoV6`, `rsSinalNbsp`, `fonteValorCabecalho`; removidos "Parcial", linha mono "indisp.", `meta` e `metaVence`. `pctDoCapital` reutilizado (sem aritmética nova).
- `TIPO_CARD` + `valor/legenda/chip` (21/11/11.5 px). Cores só via `--cv-pendente-*`/`--cv-info-*` e `T.*`.
- Guardiões reancorados com asserção equivalente e nota "46-UAT (2026-10-01)": WR-06 (chip genérico agora em `chipsMetaV6` + `<ChipsMetaV6`), "Parcial" (agora `res.cabecalho.suspenso` + `chip_total_suspenso`), total via `rsSinalNbsp` (sem `moneySigned`), escala tipográfica do transversal (valor/legenda/chip, `fonteValorCabecalho`, ternários 400/700 e corpo/rótulo), ritmo_sp (+LinhasResultadoV6, ChipsMetaV6; IconeCadeado < 200 chars fica fora). test_cartao_v6_fechado: 11 asserções novas (flex/nowrap/minWidth/overflowWrap/letterSpacing/NBSP/pior caso 14px/extras).
- Contagem de `ok(`: test_estrutura_card_ui 73 -> 73; test_cartao_v6_fechado 30 -> 41.

## Verificação
- 15 guardiões da lista: GUARDIOES_OK. `npx vite build`: ok.

## Deviations from Plan
None - plan executed as written. (Os dois commits de tarefa foram feitos; Task 1 deixou 2 guardiões vermelhos até o commit da Task 2, como previsto no plano.)

## Known Stubs
None.

## Self-Check: PASSED
