---
phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor
plan: 08
subsystem: front-data-layer
tags: [marcos, stop, alvo, finance, persistence, parity, deviceStore]
requires: [50-01, 50-02, 50-04]
provides:
  - validarMarcos, rrDaEntrada, MOTIVO_SEM_PRECO_VALIDAR, sizingPlano(plano, capital, pct, {caixa, allocPct}) (web/src/finance.js)
  - api.marcos e store.marcos nos dois stores
key-files:
  created:
    - web/tests/test_marcos_espelho.mjs
    - web/tests/test_marcos_stores.mjs
  modified:
    - web/src/finance.js
    - web/src/api.js
    - web/src/persistence.js
    - web/tests/test_finance.mjs
requirements: [MARC-07, MARC-09, MARC-11, MARC-13]
metrics:
  tasks: 2
  tests: "test_marcos_espelho 18 ok; test_marcos_stores 19 ok; test_finance e guardioes de paridade/ciclo/posicao verdes"
---

# Phase 50 Plan 08: Espelho dos marcos no front Summary

finance.js espelha `validar_marcos`, `rr_da_entrada` e o sizing com teto de alocacao (travado pela mesma fixture `marcos_casos.json` do pytest), e os dois stores ganham `marcos()` paritario; o iPhone sem conta recusa geometria impossivel, compra com marcos do motor e nao vende por marco invalido.

## Commits
- 749a3b63 feat(50-08): finance.js espelha validarMarcos, rrDaEntrada e sizing com teto de alocacao
- c1e379c1 feat(50-08): stores com marcos() paritario, putPosition local validado e gate do laco local

## Comportamento
- `numBR` interno sem Intl (milhar ".", decimal ","); todos os 9 casos de geometria, 3 de R:R e 6 de sizing da fixture passam, inclusive o texto de `MOTIVO_SEM_PRECO_VALIDAR`.
- `sizingPlano` sem o 4o argumento: comportamento anterior (so ganha o campo `limitadoPor`); `test_modo_operador` intacto.
- `deviceStore.putPosition` sem conta: gravar stop/alvo nao nulo busca cotacao via `api.getQuotes`; sem preco lanca `MOTIVO_SEM_PRECO_VALIDAR`; geometria invalida lanca o motivo e nao grava. Limpar marcos e `gestaoAuto` nao exigem preco. Com sessao segue delegando (400 do servidor sobe).
- `deviceStore.buy` sem conta com `meta.setup`: chama `api.marcos`; aplica so se `valido` e `validarMarcos(stop, alvo, preco, preco) === null`; nunca sobrescreve marco valido ao somar lote; falha/invalido -> sem marcos e `marcosMotivo` na resposta.
- `deviceStore.cycle` sem conta: gate `validarMarcos(stop, alvo, undefined, avg)` antes de breach/hit no laco aberto (1 aviso `plano_invalido_diario` por dia em `doc.agent.avisoPlanoInvalido`, via `marcosPlanoTxt`) e no aviso fora do pregao (pula, sem `aviso_diario`). Quick 261021-spd intacto (logado delega a /api/cycle; guardiao verde).

## Decisions
- Preco de referencia do `putPosition` local vem sempre de `api.getQuotes` (nao ha cache de cotacao no doc); falha => recusa. Mais conservador que o plano ("cotacao ja conhecida"), alinhado com D-11.
- Breakeven/trailing NAO entram no laco local (Operador legado sem conta, sem ATR; D-14 e server-side).
- Validacao exige preco apenas quando o corpo grava marco NAO nulo; a validacao estrutural (stop<alvo, alvo>PM) roda em qualquer escrita de stop/alvo, como `store.set_position`.

## Deviations from Plan
None - plano executado como escrito. Guardioes de paridade (`test_fase3_paridade_stores_generica`, `test_api_parity`) derivam metodos do fonte, entao `marcos` entrou nos dois sem edicao; nenhum guardiao apagado ou afrouxado.

## Known Stubs
Nenhum.

## Verification
- `node web/tests/test_marcos_espelho.mjs` (18 ok), `test_marcos_stores.mjs` (19 ok), `test_finance.mjs`, `test_modo_operador.mjs`, `test_fase3_paridade_stores_generica.mjs`, `test_api_parity.mjs`, `test_posicao_stop_alvo.mjs`, `test_ciclo_iphone_delega_servidor.mjs`, `test_deep_parity.mjs`, `test_carteira_leitura_paridade.mjs`: todos exit 0.
- `cd web && npx vite build`: ok.

## Self-Check: PASSED
