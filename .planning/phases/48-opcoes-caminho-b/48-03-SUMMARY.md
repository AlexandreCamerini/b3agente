---
phase: 48-opcoes-caminho-b
plan: 03
subsystem: web-opcoes
tags: [opcoes, navegacao, hook, stores, custo-declarado]
requires: []
provides:
  - web/src/opcoes/navOpcoes.js (máquina de navegação pura)
  - web/src/opcoes/useEscada.js (hook de dados do caminho B)
  - opcoesEscada / opcoesEscadaLeitura / mcpEscadaMatriz (api.js + serverStore + deviceStore)
affects: [48-08, 48-09, 48-10]
key-files:
  created:
    - web/src/opcoes/navOpcoes.js
    - web/src/opcoes/useEscada.js
    - web/tests/test_opcoes_nav_profundidade.mjs
  modified:
    - web/src/api.js
    - web/src/persistence.js
    - web/tests/test_opcoes_custo_declarado.mjs
decisions:
  - "abrirTicker tem precedência sobre abaInicial no estado inicial; abas válidas diferentes de montar caem no hub"
metrics:
  tasks: 2
  completed: 2026-10-05
---

# Phase 48 Plan 03: fundação de front do caminho B Summary

Estado único de navegação em profundidade (puro), hook `useEscada` com a matriz paga só em clique e três métodos de cliente com paridade nos dois stores.

## Commits
- 734ec69f feat(48-03): navOpcoes.js + guardião test_opcoes_nav_profundidade.mjs
- 0cf47f83 feat(48-03): useEscada + 3 métodos de cliente nos dois stores + guardião de custo estendido

## Entregue
- `navOpcoes.js`: 12 exports (NIVEIS, OBJETIVOS e 10 funções); sem React/store/fetch; deep-links `opcoesAbrirTicker` e `opcoesAbaInicial` ("montar") preservados; valor fora da allowlist cai no hub.
- `useEscada.js`: escada por efeito (primitivas, custo 0), `verMatriz` única chamada paga, só por clique; descarta resposta de ticker antigo; erro verbatim.
- `api.js` + `persistence.js`: 3 métodos nos dois stores (deviceStore com `ensure()`).
- Guardião de custo: bloco 11 (reprova `mcpEscadaMatriz` em `useEffect`, exige em `verMatriz`, só `store.mcp*` permitido é a matriz, sem literal de custo). Nada removido.

## Deviations from Plan
- O critério `grep -c ... persistence.js == 2` conta linhas: o resultado é 3 (serverStore numa linha, deviceStore em duas: assinatura e delegação). Existe exatamente um método por store; intenção atendida.
- Usei também `abaInicialOpcoes` (já existente em memoriaOpcoes.js) em `navOpcoes.js`.

## Verificação
Verdes: test_opcoes_nav_profundidade, test_opcoes_custo_declarado, test_api_parity, test_fase3_paridade_stores_generica, test_opcoes_tecnico_stores; `npx vite build` ok. Suíte completa não rodada (escopo da onda: orquestrador).

## Known Stubs
Nenhum. As rotas backend (48-06/48-07) ainda não existem; o hook só as chama quando `ativo`, e nenhum componente o consome ainda.

## Self-Check: PASSED
