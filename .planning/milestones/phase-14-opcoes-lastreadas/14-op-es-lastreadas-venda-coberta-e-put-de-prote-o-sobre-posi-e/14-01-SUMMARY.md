---
phase: 14-opcoes-lastreadas
plan: 01
subsystem: api
tags: [options, portfolio-engine, pytest, options-provider, position-lock]

# Dependency graph
requires: []
provides:
  - "options_provider_mock.py — cadeia de opções sintética determinística, roteável via B3_OPTIONS_PROVIDER=mock, com caminho degradado via B3_OPTIONS_MOCK_STATUS=degraded"
  - "store.qty_livre(pos) — fonte única backend da quantidade vendável de uma posição de ação (qty - qtyTravada)"
  - "store.sell guarda de trava — venda recusada (com rejeição registrada) quando a posição está 100% travada, limitada ao livre quando parcial"
  - "pending_orders.criar_venda guarda de reserva — nunca reserva a parte travada de uma posição"
affects: [14-02, 14-03, 14-04, 14-05, 14-06, 14-07, 14-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Provider mock determinístico sem I/O (mesmo contrato de payload do provider Yahoo/mydata), seguindo o padrão de seletor por env já estabelecido em options_provider.py"
    - "Campo qtyTravada em position (ação) com leitura via .get (default 0), sem migração/backfill — trava vale só para o modelo lastreado novo"
    - "Fonte única de aritmética entre camadas (mesmo padrão de RR_MIN/caixa_reservado): store.qty_livre no backend, qtyLivre em web/src/finance.js no front (a implementar no plano 14-05)"

key-files:
  created:
    - server/app/options_provider_mock.py
    - server/tests/test_options_provider_mock.py
    - server/tests/test_lastro_trava.py
  modified:
    - server/app/options_provider.py
    - server/app/store.py
    - server/app/pending_orders.py

key-decisions:
  - "Volume/openInterest do mock fixados em 500/2000 (constantes MOCK_VOLUME/MOCK_OPEN_INTEREST) — suficientes para liquidity_score >= 40 em qualquer strike gerado, sem precisar calibrar por contrato"
  - "symbol do payload mock é o próprio ticker em maiúsculas (sem sufixo .SA de yahoo_symbol) — mock não reusa formatação específica do provider Yahoo, evita acoplamento desnecessário"
  - "criar_venda devolve a mensagem específica de lastro quando o motivo da insuficiência é 100% trava (disponivel<=0 e qtyTravada>0), preservando a mensagem genérica de posição insuficiente nos demais casos"

requirements-completed: []

# Metrics
duration: ~35min
completed: 2026-08-31
---

# Phase 14 Plan 01: Fundação do motor lastreado Summary

**Provider de opções mock determinístico (sem rede) + trava de lastro no motor de carteira (`qty_livre`, guardas em `sell`/`criar_venda`) — as duas peças que toda a Fase 14 pressupõe.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-08-31T03:03:17Z
- **Tasks:** 2/2
- **Files modified:** 5 (3 criados, 2 modificados)

## Accomplishments
- Cadeia de opções sintética 100% determinística (`options_provider_mock.py`), roteável por `B3_OPTIONS_PROVIDER=mock` sem tocar o default de produção (`yahoo`), com caminho degradado (`B3_OPTIONS_MOCK_STATUS=degraded`) que exercita o bloqueio do ADR-004 sem depender do Yahoo falhar de verdade.
- Trava de lastro implementada no motor: `qty_livre(pos)` como fonte única da quantidade vendável do backend; venda imediata (`store.sell`) e venda pendente (`pending_orders.criar_venda`) nunca tocam a parte travada — a imediata registra rejeição com motivo legível em PT-BR, a pendente levanta `PosicaoInsuficiente`.
- Suíte canônica inteira verde: `1758 passed, 1 skipped` (pytest) + todas as `web/tests/*.mjs` `[OK]` — nenhum arquivo web foi tocado neste plano (backend-only), então não havia necessidade de `npx vite build`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Provedor de opções mock (payload sintético determinístico)** - `ad4d249` (feat)
2. **Task 2: Trava de lastro no motor — qtyTravada, qty_livre e guardas de venda** - `ef807b5` (feat)

_Note: nenhuma task era TDD — plano `autonomous: true`, sem checkpoints._

## Files Created/Modified
- `server/app/options_provider_mock.py` - cadeia sintética determinística: spot fixo por ticker (PETR4/VALE3/ITUB4 + default 30.00), 3 vencimentos (terceiras sextas), 9 strikes de call/put, caminho degradado via env
- `server/app/options_provider.py` - registra `"mock"` em `_PROVEDORES`; docstring documenta o propósito (dev/teste enquanto mydata não vira produção); default `"yahoo"` intacto
- `server/tests/test_options_provider_mock.py` - contrato completo, determinismo entre chamadas, gate de liquidez, caminho degradado, roteamento por env, default inalterado
- `server/app/store.py` - `qty_livre(pos)` (fonte única backend); `sell()` recusa/limita venda pela parte livre, nunca remove posição travada por venda total
- `server/app/pending_orders.py` - `criar_venda` calcula `disponivel` via `store.qty_livre`, nunca `pos["qty"]` cru; mensagem específica de lastro quando 100% travado
- `server/tests/test_lastro_trava.py` - guardião: `qty_livre` isolada, venda parcial/total travada, rejeição registrada sem mover caixa, reserva pendente respeitando a trava, guardião de fonte única (regex varrendo `server/app/*.py` exceto `store.py`)

## Decisions Made
- Volume/openInterest do mock fixados (500/2000) em vez de variar por strike — decisão de simplicidade: o `acceptance_criteria` do plano só exige `score >= 40` em qualquer contrato, e valores fixos generosos garantem isso sem lógica extra de calibração.
- `symbol` do payload mock não reusa `catalog.yahoo_symbol` (que adicionaria sufixo `.SA`) — o mock é uma fonte própria, não uma imitação byte a byte do formato Yahoo; nenhum consumidor no código depende do formato exato desse campo.
- Na guarda de `criar_venda`, quando a insuficiência é 100% travamento a mensagem devolvida é a mesma frase de lastro usada em `store.sell` (consistência de UX entre os dois caminhos de venda); nos demais casos de posição insuficiente (sem trava envolvida) a mensagem genérica original é preservada.

## Deviations from Plan

None - plan executed exactly as written. Todos os campos, funções, mensagens e critérios do plano (`options_provider_mock.py`, `_PROVEDORES["mock"]`, `qty_livre`, guardas em `sell`/`criar_venda`, testes) foram implementados conforme especificado em `<action>`.

## Issues Encountered
- O worktree foi criado a partir da tip do checkout principal em vez da branch de feature que contém os documentos de planejamento da Fase 14 — corrigido com `git reset --hard` (fast-forward confirmado via `git merge-base --is-ancestor`, sem perda de trabalho: working tree estava limpo) antes de começar a executar o plano.
- Não havia `.venv` dentro do worktree (padrão do repo — `scripts/test.sh` já documenta isso e resolve via `git rev-parse --git-common-dir`); os testes foram rodados apontando direto para `/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python` (o venv do clone principal), o mesmo caminho que `scripts/executar.sh --testes` usa internamente.

## User Setup Required

None - no external service configuration required. `B3_OPTIONS_PROVIDER=mock` é opcional e só para desenvolvimento/teste local; nenhuma env nova é obrigatória em produção.

## Next Phase Readiness
- `options_provider_mock.py` está pronto para os planos seguintes da Fase 14 exercitarem a mecânica lastreada ponta a ponta sem depender da virada de produção do mydata.
- `store.qty_livre` está pronto para o plano 14-02 (abridor de CALL coberta) escrever `qtyTravada` na posição, e para o plano 14-05 espelhar `qtyLivre` em `web/src/finance.js` (paridade front×backend, mesmo padrão de `RR_MIN`).
- Nenhum bloqueio conhecido para os próximos planos da fase.

---
*Phase: 14-opcoes-lastreadas*
*Completed: 2026-08-31*

## Self-Check: PASSED

- FOUND: server/app/options_provider_mock.py
- FOUND: server/tests/test_lastro_trava.py
- FOUND: server/tests/test_options_provider_mock.py
- FOUND commit ad4d249 (Task 1)
- FOUND commit ef807b5 (Task 2)
