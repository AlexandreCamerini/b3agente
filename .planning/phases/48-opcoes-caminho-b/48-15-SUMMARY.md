---
phase: 48-opcoes-caminho-b
plan: 15
subsystem: opcoes-escada
tags: [gap-closure, G-01, G-02, skill_ref, paridade, fastapi]
requires: ["48-06", "48-13", "48-14"]
provides:
  - "opcoes_escada.motivo_sem_candidato (puro)"
  - "GET /api/options/escada: motivoChave real, dica por objetivo, objetivosMotivo"
  - "vocabulário pernas_* e sem_vencimento_elegivel em OPCOES_ESCADA + copy.js (usado pelo 48-16)"
affects: [server/app/main.py, server/app/opcoes_escada.py, server/app/skill_ref.py, web/src/copy.js]
key-files:
  modified:
    - server/app/skill_ref.py
    - web/src/copy.js
    - web/tests/test_opcoes_escada_espelho.mjs
    - server/app/opcoes_escada.py
    - server/tests/test_opcoes_escada.py
    - server/app/main.py
    - server/tests/test_opcoes_escada_rotas.py
decisions:
  - "Piso de 15 dias e VENCIMENTOS_POR_POSICAO=2 intactos; só o motivo deixa de mentir"
  - "Janela importada de opcoes_lastreadas (sem segundo corte)"
metrics:
  tasks: 3
  completed: 2026-10-05
---

# Phase 48 Plan 15: G-01 motivo real de vencimento + vocabulário G-02 Summary

Rota da escada distingue `sem_vencimento_elegivel` (nenhum vencimento lido em 15–60 dias, cita as datas DD/MM lidas e a janela, com dica) de `sem_estrutura`; 18 chaves novas nos dois modos já espelhadas para a seção "Suas pernas abertas" do 48-16.

## Commits
- 7ba9d81c feat: vocabulário G-01/G-02 em skill_ref.OPCOES_ESCADA + espelho copy.js + guardião de paridade
- 9ca9dd50 test (RED): motivo_sem_candidato
- 9447eee7 feat (GREEN): motivo_sem_candidato; `objetivos()` ganha `dica: None`
- abbdc3ce feat: rota com motivoChave/dica/objetivosMotivo + 3 guardiões de rota

## Verificação
- pytest test_opcoes_escada_rotas + test_opcoes_escada + test_opcoes_curadoria_rota + test_skill_ref: 132 passed
- node web/tests/test_opcoes_escada_espelho.mjs: verde
- vite build não rodado (nenhum arquivo de web/src além de copy.js, dado puro; sem mudança de lógica JS)

## Deviations from Plan
- [Rule 3] Teste de pernas compradas: `store.set_config` não aceita `permitirOpcaoADescoberto` (allowlist), então a fixture grava a flag via `db.kv_set` só para poder comprar perna avulsa.
- Nota: `sem_vencimento_elegivel` em OPCOES_ESCADA é namespace próprio; não colide com a homônima da Fase 44 em OPCOES_LASTREADAS (comentário no código).

## Known Stubs
Nenhum. Chaves `pernas_*` ainda sem consumidor de UI (entregue no 48-16, por desenho).

## Self-Check: PASSED
