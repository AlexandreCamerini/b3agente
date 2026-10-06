---
phase: 48-opcoes-caminho-b
plan: 06
subsystem: opcoes-rotas
tags: [escada, rotas, custo-zero]
requires: [48-04]
provides:
  - "GET /api/options/escada/{ticker}?objetivo=&vencimento="
  - "POST /api/options/escada/leitura"
affects: [48-07, 48-08, 48-09]
key-files:
  modified: [server/app/main.py]
  created: [server/tests/test_opcoes_escada_rotas.py]
requirements-completed: [OPC-02, OPC-03, OPC-13]
metrics:
  completed: 2026-10-05
---

# Phase 48 Plan 06: Rotas da escada Summary

Duas rotas grátis (custo MCP 0) sobre o motor `opcoes_escada`: escada por ativo/objetivo/vencimento montada na MESMA varredura `_curadoria_scan_posicao` que a execução do collar re-deriva, e leitura pura de uma célula da matriz.

## Commits
- 8c02a632 feat(48-06): as duas rotas + testes (as duas tasks num único commit, pois ambas editam main.py e o mesmo arquivo de teste)

## Entregue
- GET: sem `objetivo` devolve disponibilidade dos 3 objetivos (motivo quando inviável), vencimentos montáveis `{iso, texto DD/MM, dias}` e `comparar` (`chamadasPrevistas = 2N+1`, N = min(vencimentos futuros da 1ª cadeia, N_MAX_VENCIMENTOS); `restamHoje` do `_cap_bloco`). Com `objetivo`: até 3 degraus do vencimento mais próximo montável (ou `?vencimento=` varrido), `id` = `execucao.idCandidato`, `degrausAusentes` com texto do motor.
- Estados: `sem_posicao` (texto do motor), `degradado` (200, `providerStatus: degraded`, texto `erro_fonte`, nenhum número), vencimento não varrido -> degraus `[]` + `sem_estrutura`.
- POST: validação estrita (1-2 pernas, tipo/lado em allowlist, strike/prêmio numéricos > 0, bool rejeitado, vencimento ISO), `execucao.executavel=false` com motivo `matriz_so_comparacao`; sem provedor; `precoObjeto` do corpo ou `None`.
- 22 testes novos; `test_opcoes_curadoria_rota.py` sem edição, verde (48 passed no par). Também verdes: test_opcoes_fronteira, test_mcp_guardioes, test_adr013_cobertura_rotas, test_adr013_rbac, test_mcp_cap, test_put_bridge_sem_superficie, test_didatica_rotas.

## Decisões / premissas
- Objetivo com lastro ok mas sem NENHUM candidato varrido do tipo (ex.: cadeia sem puts) vira `disponivel=false` com `motivoChave="sem_estrutura"` na rota (extensão sobre `opcoes_escada.objetivos`, que só olha lastro) — evita escada vazia numa opção apresentada como disponível.
- `vencimentos` é filtrado pelo tipo do objetivo quando `objetivo` é dado.
- Degradação parcial (vencimento extra falhou, 1ª cadeia ok) mantém `estado: ok`; só falha da 1ª cadeia degrada.
- `vencimento` malformado e `objetivo` fora da allowlist -> 400; `indice` do POST fora de 0..2 cai em 0.
- `pregao` vem de `chain["pregao"]` (mydata) ou `None`.

## Deviations from Plan
None - plano executado como escrito (além das premissas acima).

## Known Stubs
Nenhum.

## Threat Flags
Nenhum (T-48-18..22 mitigados; custo 0 provado por teste que arma `_chamada_com_cap` para falhar).

## Self-Check: PASSED
- main.py contém 1 ocorrência de cada decorador de rota; teste criado; commit 8c02a632 existe; STATE.md/ROADMAP.md intocados. Suíte canônica e vite build não rodados (backend only; é do orquestrador).
