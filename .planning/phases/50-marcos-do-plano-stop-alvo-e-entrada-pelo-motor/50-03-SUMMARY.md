---
phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor
plan: 03
subsystem: motor-da-carteira
tags: [store, set_position, buy, pending_orders, marcos, tdd]
requires: [50-01, 50-02]
provides:
  - store.set_position(..., preco_ref=None, gestao_auto=None) validado por setups.validar_marcos
  - store.buy(..., marcos=None) com stopInicial/gestaoAuto/marcosOrigem
  - pending_orders.criar_compra(..., marcos=None) + revalidacao em executar_pendentes
affects: [50-04, 50-05, 50-08]
key-files:
  created: [server/tests/test_marcos_gravacao_store.py, server/tests/test_marcos_pendentes.py]
  modified: [server/app/store.py, server/app/pending_orders.py]
metrics:
  tasks: 2
  completed: 2026-10-22
---

# Phase 50 Plan 03: Gravacao dos marcos no motor da carteira Summary

set_position recusa geometria impossivel (ValueError PT-BR, kv intacto), buy cria posicao com marcos do motor e gestao padrao ligada, lote somado preserva marco valido do usuario, e a ordem pendente de compra carrega marcos do motor revalidados ao preco executado.

## Commits
- 0db9f4f7 feat(50-03): set_position valida geometria e buy grava marcos do motor
- e070ec5a feat(50-03): ordem pendente carrega e revalida os marcos do motor

## Comportamento
- set_position mescla has_stop/has_alvo com os valores atuais e valida antes de mutar; `preco_ref=None` valida so estrutura (stop<alvo, alvo>PM). Caso real PM 23,01 / stop 23,36 / alvo 21,58 recusado.
- buy(marcos): posicao nova com stop/alvo/stopInicial/gestaoAuto=True/marcosOrigem="motor"; marcos invalidos levantam ValueError antes de tocar caixa. Lote somado: mantem stop/alvo validos existentes; sem marcos aplica os do motor. Normalizacao de qty (lote de 100) intacta.
- criar_compra grava `order["marcos"]` apenas do parametro (nunca de `meta`). executar_pendentes revalida (geometria, perseguicao D-03, R:R); invalido executa SEM marcos com evento warn `compra_sem_marcos` + motivo; valido grava e emite info `compra_com_marcos`. Evento original preservado byte a byte.

## Testes
- test_marcos_gravacao_store.py: 10 passed; test_marcos_pendentes.py: 5 passed
- 48 passed (gravacao_store + execucao_fora_pregao_rotas + ciclo_imediato + fase3_operador); 146 passed (marcos_pendentes + test_agent* + ordens_pendentes*); 94 passed nos pendentes/push_payload.

## Deviations from Plan
- [Rule 1 - ajuste de teste] O caso "executar a 22,0" do plano, com gatilho/invalidacao presentes, dispara a regra de perseguicao (D-03) antes do R:R. O teste usa marcos sem gatilho/invalidacao para isolar o corte por R:R; "nao persiga" tem caso proprio (20,25).
- Import `setups` em store.py e modulo (sem ciclo: verificado import de app.main).
- Lote somado: "sem marcos" = nem stop nem alvo validos preexistentes; marco parcial valido do usuario tambem e preservado.

## Known Stubs
Nenhum.

## Self-Check: PASSED
