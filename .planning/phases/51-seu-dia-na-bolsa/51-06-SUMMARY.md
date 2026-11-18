---
phase: 51-seu-dia-na-bolsa
plan: 06
subsystem: front data layer / config
tags: [persistence, api, diasDecisao, paridade]
requires: ["51-03"]
provides:
  - api.diaNaBolsa / diaNaBolsaVistos / diaNaBolsaConvite
  - getDiaNaBolsa / registrarVistos / decidirFechamento nos dois stores
  - config.diasDecisao (união, regex, teto 60) no servidor e no aparelho
affects: [51-07, 51-08]
key-files:
  created:
    - server/tests/test_dia_na_bolsa_config.py
    - web/tests/test_dia_na_bolsa_stores.mjs
  modified:
    - server/app/store.py
    - server/app/defaults.py
    - web/src/catalog.js
    - web/src/api.js
    - web/src/persistence.js
decisions:
  - "diasDecisao: união ordenada, regex AAAA-MM-DD, teto 60 (DIAS_DECISAO_MAX) — mesma regra em store.set_config, deviceStore.putConfig e patch otimista do serverStore"
  - "streak legado intocado"
  - "fechamento fora de _pushPrefsLocais/syncPushPrefs; só decidirFechamento (rota de convite) o envia"
metrics:
  tasks: 2
  completed: 2026-11-18
---

# Phase 51 Plan 06: camada de dados do card e config.diasDecisao

Clientes HTTP das três rotas do card, três métodos novos com paridade `deviceStore` ↔ `serverStore`, e `config.diasDecisao` mesclado por união nos dois lados.

## Commits
- d5519b3c — feat(51-06): config.diasDecisao por uniao no servidor e nos defaults
- 652f853e — feat(51-06): api e metodos do card nos dois stores, diasDecisao por uniao no aparelho

## O que mudou
- `store.py`: `set_config` une `diasDecisao` (regex, ordenado, teto 60); migração `setdefault([])`. `defaults.py` e `catalog.js` ganham `diasDecisao: []` após `streak`.
- `api.js`: `diaNaBolsa(modo)`, `diaNaBolsaVistos`, `diaNaBolsaConvite` (timeout regular).
- `persistence.js`: helper `uniaoDiasDecisao` (usado no `deviceStore.putConfig` e no `optConfig` do serverStore, que antes substituiria); `_normalizarVistos` (maiúsculas, únicos, até 60); métodos nos dois stores. No deviceStore, sem sessão: `getDiaNaBolsa` devolve `{card:null, convite:false, fechamento:null, ultimas4Semanas:[]}` e as outras duas `null`, sem rede.
- `fechamento` não entra em `_pushPrefsLocais` nem em `syncPushPrefs`.

## Verificação
- pytest: `test_dia_na_bolsa_config` (5), `test_push_prefs_classes`, `test_conta_nova_nasce_limpa`, `test_auditoria_prompts`, `test_telas_paridade`, `test_put_bridge_sem_superficie`, `test_kb_ancoras`: 61 passam.
- `test_conta_nova_ios_nasce_limpa.mjs`, `test_dia_na_bolsa_stores.mjs`, `test_api_parity.mjs`, `test_dia_na_bolsa_push_prefs.mjs`: verdes.
- `npx vite build`: OK (ruído de certificado do sandbox no stderr, sem relação).

## Deviations from Plan
None - plano executado como escrito. Nota: `serverStore.optConfig` precisou da união explícita (previsto como "conferir" no plano).

## Self-Check: PASSED
