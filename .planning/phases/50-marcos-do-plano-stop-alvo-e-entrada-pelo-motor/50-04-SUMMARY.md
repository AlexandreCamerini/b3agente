---
phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor
plan: 04
subsystem: rotas-de-marcos
tags: [main, marcos_servico, put-position, api-buy, api-marcos]
requires: [50-01, 50-02, 50-03]
provides:
  - server/app/marcos_servico.py (snapshot_canonico, marcos_de_setup, marcos_para_posicao)
  - POST /api/marcos/{ticker} (gratuita, sem IA, anonimo permitido)
  - PUT /api/position com 400 PT-BR (D-11) e gestaoAuto (D-14)
  - POST /api/buy com marcos/marcosMotivo/marcosTexto (imediata e pendente)
affects: [50-05, 50-08]
key-files:
  created: [server/app/marcos_servico.py, server/tests/test_marcos_rotas.py]
  modified: [server/app/main.py, server/tests/test_adr013_rbac.py, server/tests/test_ciclo_imediato_apos_carteira.py, server/tests/test_execucao_fora_pregao_rotas.py]
metrics:
  tasks: 2
  completed: 2026-10-22
---

# Phase 50 Plan 04: Rotas de marcos Summary

PUT /api/position recusa a geometria do iPhone (PM 23,01 / stop 23,36 / alvo 21,58) com 400 em PT-BR, compra manual a partir de setup nasce com marcos calculados no servidor a partir do snapshot, e o front ganha a rota gratuita POST /api/marcos/{ticker}.

## Commits
- feat(50-04) rotas de marcos (Tasks 1 e 2 num commit unico: as duas mexem em hunks adjacentes de main.py e dividir exigiria patch interativo)

## Comportamento
- PUT: preco de referencia = cotacao, senao close do snapshot, senao 400 `MOTIVO_SEM_PRECO_VALIDAR` (sem gravar). Limpar marcos e PUT so de gestaoAuto nao precisam de preco. `ValueError` do store vira 400.
- /api/marcos: ticker validado antes do I/O, sem snapshot -> 502, nenhuma chamada LLM/cota.
- /api/buy: snapshot e revalidacao ANTES do ORDER_LOCK; marcos so do setup DO SNAPSHOT (gatilho/invalidacao forjados no meta ignorados, teste cobre); R:R<1,5, perseguicao >0,5R ou sem snapshot executam SEM marcos com `marcosMotivo` (Esclarecimento da D-06). Ramo fechado: `order["marcos"]` com gatilho/invalidacao do snapshot para a revalidacao na abertura. Resposta ganha `marcos`, `marcosMotivo`, `marcosTexto` (via `skill_ref.marcos_plano_txt`).

## Testes
- test_marcos_rotas.py: 17 passed
- Conjunto (marcos_rotas + adr013_rbac + ciclo_imediato + execucao_fora_pregao + todos os arquivos com /api/buy): 216 passed, 2 failed -> 1 corrigido (preco do teste de posicao); sobrou `test_rotas_fase4::test_benchmark_ibov_cache...` com `PermissionError: Operation not permitted` (rede do sandbox, ruido de ambiente, nao relacionado).

## Deviations from Plan
- Tasks 1 e 2 num unico commit (ver acima).
- Guardiao do adr013 usa `c, _m` (precisa do `main` para o monkeypatch); nenhum `def test_` removido.
- Resposta do /api/buy tambem traz `marcosTexto` (previsto no plano) so quando ha setup no meta.

## Known Stubs
Nenhum.

## Self-Check: PASSED
