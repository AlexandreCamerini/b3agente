---
phase: 04-corre-o-m-dio-storyline-ux
plan: 02
subsystem: api
tags: [python, fastapi, sqlite, httpx, yahoo-finance, store, benchmark]

# Dependency graph
requires: []
provides:
  - "store.registrar_rejeicao() — motor determinístico do rastro de ordem rejeitada"
  - "status: executada|rejeitada em toda entrada de history (buy/sell + rejeicao)"
  - "server/app/benchmark.py — serie_ibov() com fechamentos diarios do Ibovespa"
affects: ["04-04 (fiação das rotas /api/buy, /api/sell, novo /api/benchmark)", "04-05/04-06 (UI que consome status/benchmark)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "registrar_rejeicao segue o mesmo contrato de campos de buy/sell (date/type/t/qty/price/pnl/status/motivo/origem), inserido em history[0] sem tocar cash/positions"
    - "Poda por status (CAP_REJEICOES=100) via varredura de índices, preservando execuções — mesmo espírito de push_events/set_analysis mas escopado só a rejeitadas"
    - "benchmark.py reusa yahoo._yfetch diretamente (não yahoo.get_history) para evitar a normalização .SA de catalog.yahoo_symbol em símbolos de índice"

key-files:
  created:
    - server/app/benchmark.py
    - server/tests/test_ordem_rejeitada.py
    - server/tests/test_benchmark_ibov.py
  modified:
    - server/app/store.py

key-decisions:
  - "status carimbado em buy()/sell() sem reescrever histórico legado — mesma regra já adotada quando origem/motivo entraram (histórico não se reescreve, CLAUDE.md)"
  - "registrar_rejeicao aceita price=None e preserva null (nunca 0.0), seguindo a convenção da casa (test_m3_format_pede_null_nunca_zero) por razão de produto (CLAUDE.md item 4)"
  - "benchmark.serie_ibov cacheia por range resolvido (TTL 900s), não por period bruto — evita múltiplas entradas de cache para aliases do mesmo range"

requirements-completed: [FIX-C02, FIX-C03]

duration: 45min
completed: 2026-08-22
---

# Phase 04 Plan 02: Motor determinístico — rastro de rejeição e benchmark Ibovespa Summary

**`store.registrar_rejeicao()` grava toda tentativa de ordem rejeitada no histórico sem mover dinheiro, e `server/app/benchmark.py` (novo) entrega fechamentos diários do Ibovespa via Yahoo com cache de 15 min — os dois pré-requisitos de estado para FIX-C02/FIX-C03, sem tocar nenhuma rota.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-08-22T00:55:00Z (aprox., primeira leitura do plano)
- **Completed:** 2026-08-22T01:42:25Z
- **Tasks:** 2/2
- **Files modified:** 4 (1 modificado, 3 criados)

## Accomplishments

- `store.buy()`/`store.sell()` carimbam `status: "executada"` em toda entrada nova de `history`, sem reescrever entradas legadas sem essa chave.
- `store.registrar_rejeicao()` grava o contrato completo de uma tentativa rejeitada (9 campos: date/type/t/qty/price/pnl/status/motivo/origem), truncando `motivo` em 200 chars, preservando `price=None` quando a rejeição foi por falta de cotação, e sem tocar `cash`/`positions`/`pendingOrders`.
- Poda `CAP_REJEICOES=100` mantém no máximo 100 entradas `status=="rejeitada"` (descarta as mais antigas), sem nunca descartar entradas executadas — mitigação de T-04-02.
- `server/app/benchmark.py` (novo) expõe `serie_ibov(period)`: símbolo `^BVSP` hardcoded (sem parâmetro de requisição, T-04-04), cache em memória TTL 900s por `range` resolvido, reusa `yahoo._yfetch` para herdar a mitigação de 429/cookie/crumb, recusa granularidade degradada e série vazia, converte toda falha em `BenchmarkIndisponivel` sem vazar detalhe do provedor (T-04-01).
- Dois guardiões novos: `test_ordem_rejeitada.py` (11 casos) e `test_benchmark_ibov.py` (6 casos, sem rede — `_yfetch` monkeypatchado).

## Task Commits

1. **Task 1: Rastro da ordem rejeitada no histórico (FIX-C02, motor)** - `cab68f7` (feat)
2. **Task 2: Série diária do Ibovespa (FIX-C03, motor)** - `13d5d6c` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `server/app/store.py` - `CAP_REJEICOES` constante, `status: "executada"` em `buy()`/`sell()`, nova `registrar_rejeicao()`
- `server/app/benchmark.py` (novo) - `SIMBOLO`, `TTL`, `_cache`, `BenchmarkIndisponivel`, `serie_ibov()`, `limpar_cache()`
- `server/tests/test_ordem_rejeitada.py` (novo) - 11 testes cobrindo contrato, tipo inválido, não-movimento de dinheiro, price=None, truncamento de motivo, poda (2 cenários), buy/sell carimbando status, histórico legado intocado
- `server/tests/test_benchmark_ibov.py` (novo) - 6 testes cobrindo payload feliz, close=None no meio, granularidade degradada, payload vazio, QuoteUnavailable sem vazamento de detalhe, cache TTL

## Decisions Made

- Nenhuma decisão nova fora do que já estava fechado no CONTEXT.md/PLAN.md — as duas decisões relevantes (status em toda tentativa; Ibovespa via Yahoo mesmo provedor) já vinham do C-02/C-03.
- Ajuste textual em `benchmark.py`: o comentário de topo originalmente citava `catalog.yahoo_symbol()` por extenso, o que fazia `grep -n "yahoo_symbol" server/app/benchmark.py` (critério de aceite da Task 2) retornar 1 linha em vez de zero. Reescrito para explicar a mesma razão sem repetir o nome literal da função — critério de aceite confirmado com grep vazio após o ajuste.

## Deviations from Plan

None - plan executed exactly as written (uma correção textual menor documentada acima em "Decisions Made", sem mudança de comportamento).

## Issues Encountered

- O worktree não tinha `.venv` próprio (não versionado, esperado — `server/.venv` é gitignored). Testes rodados apontando o interpretador do `.venv` do repo principal (`/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python`) contra o código do worktree — mesmo padrão que o binário standalone, sem instalar nada novo. Suíte completa (1284 passed, 1 skipped) confirma zero regressão.
- Suíte web (`web/tests/*.mjs`) não foi executada: este plano não toca nenhum arquivo em `web/` (escopo é só `server/app/store.py` + `server/app/benchmark.py` + testes backend, conforme `files_modified` do frontmatter), e o worktree não tem `web/node_modules` instalado (nota já registrada em `PROJECT.md`: isso causaria 7 falhas por ambiente, não por regressão). Suíte canônica completa fica para a wave de consolidação/plano de fiação (04-04), quando rotas web também mudarem.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Motor pronto para o Plano 04-04 (fiação de rotas): `/api/buy`/`/api/sell` podem chamar `store.registrar_rejeicao()` dentro do `store.ORDER_LOCK` já existente ao invés de só levantar `HTTPException`; uma rota nova (`/api/benchmark` ou equivalente) pode chamar `benchmark.serie_ibov()` diretamente.
- Contrato fixado no PLAN.md (`status`, `motivo`, `price`, `pnl` em history; `t`/`nome`/`fonte`/`candles`/`asOf` em `serie_ibov`) está implementado exatamente como especificado — nenhuma rota tocada neste plano, conforme success_criteria.
- Sem bloqueios conhecidos para os planos seguintes (04-04, 04-05, 04-06).

---
*Phase: 04-corre-o-m-dio-storyline-ux*
*Completed: 2026-08-22*

## Self-Check: PASSED

- FOUND: server/app/benchmark.py
- FOUND: server/tests/test_ordem_rejeitada.py
- FOUND: server/tests/test_benchmark_ibov.py
- FOUND: cab68f7 (Task 1 commit)
- FOUND: 13d5d6c (Task 2 commit)
