---
phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re
plan: 01
subsystem: data
tags: [yahoo-finance, backtest, replay-determinístico, python, pytest]

# Dependency graph
requires: []
provides:
  - "server/app/signal_replay.py — fonte única do replay determinístico (sinais_do_ticker/avaliar/agregar/replay), consumível pelo ledger (Plano 02), bootstrap (Plano 03) e hook diário (Plano 04)"
  - "yahoo.confere_granularidade — guard universal contra dado Yahoo degradado (1d/5d/1wk/1mo/3mo), chamado dentro de get_history"
  - "scripts/backtest_sinal.py como wrapper fino, sem nenhuma segunda implementação da barreira tripla"
affects: [07-02-ledger-de-sinais, 07-03-bootstrap, 07-04-hook-diario]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guard de granularidade na fronteira de fetch (get_history), não como utilitário opcional — nenhum caller novo pode esquecer de validar"
    - "Módulo de produção puro (sem I/O/rede/relógio) para lógica determinística que precisa ser reproduzível a partir de um script CLI"

key-files:
  created:
    - server/app/signal_replay.py
    - server/tests/test_yahoo_granularidade.py
    - server/tests/test_signal_replay.py
  modified:
    - server/app/yahoo.py
    - scripts/backtest_sinal.py

key-decisions:
  - "Guard de espaçamento ampliado além de scripts/backtest_sinal (só tinha 1d/1wk) para cobrir 5d/1mo/3mo — nenhum caller de yahoo.get_history nesses intervalos ficava protegido antes"
  - "Guard de meta.dataGranularity fora do intraday só recusa quando MAIS GROSSO que o pedido (ordem de granularidade), nunca por divergência de rótulo em granularidade igual/mais fina — evita falso positivo em fetch diário de produção"
  - "Testes de sinais_do_ticker/avaliar mockam setups.detect_setups/plano_do_resultado em vez de reengenhar uma série que dispare um setup real — a mecânica de detecção já é travada em test_setups.py; aqui o alvo é a orquestração e a barreira"

requirements-completed: [ADR17-B1-04, ADR17-B1-07]

# Metrics
duration: 28min
completed: 2026-08-21
---

# Phase 07 Plan 01: Guard de Granularidade + Replay Determinístico Summary

**Guard universal de granularidade do Yahoo (`yahoo.confere_granularidade`, todos os intervalos não-intraday) e promoção do replay determinístico/barreira tripla para `server/app/signal_replay.py`, com `scripts/backtest_sinal.py` reduzido a wrapper fino — fecha os dois pré-requisitos que o ledger, bootstrap e hook diário da Fase 7 dependem.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-08-21T07:32:35-03:00
- **Completed:** 2026-08-21T08:00:55-03:00
- **Tasks:** 3
- **Files modified:** 5 (2 criados de produção, 2 criados de teste, 1 modificado)

## Accomplishments
- `yahoo.get_history` agora recusa dado degradado (mensal rotulado como diário/semanal/etc.) em TODOS os intervalos não-intraday, comprovado ao vivo contra a API real do Yahoo (`B3_TESTE_REDE=1`) para `rng=15y/interval=1d` (passa) e `rng=max/interval=1d` (recusa) — exatamente o bug medido em 2026-08-20 no ADR-016.
- `server/app/signal_replay.py` criado: única implementação da barreira tripla (detecção + avaliação forward), com `dataResolucao` adicionado a todos os ramos de `avaliar()` e uma função `replay()` nova como ponto de entrada único.
- `scripts/backtest_sinal.py` reduzido de 358 para 199 linhas, sem nenhuma reimplementação da barreira; `scripts/backtest_placebo.py` continua importando `CACHE_DIR`/`HORIZONTE`/`avaliar` normalmente.

## Task Commits

Each task was committed atomically:

1. **Task 1: Guard de granularidade do Yahoo cobrindo todos os intervalos** - `92b3c85` (feat)
2. **Task 2: Promover o replay determinístico para server/app/signal_replay.py** - `86fe891` (feat)
3. **Task 3: scripts/backtest_sinal.py vira wrapper fino sobre signal_replay** - `5bf7fd0` (refactor)

**Plan metadata:** (este commit, docs)

## Files Created/Modified
- `server/app/yahoo.py` - `confere_granularidade()` público (tabela de espaçamento 1d/5d/1wk/1mo/3mo), guard de `meta.dataGranularity` generalizado por ordem de granularidade fora do intraday, chamado em `get_history` antes do `return`
- `server/app/signal_replay.py` - novo; `JANELA`/`HORIZONTE`/`sinais_do_ticker`/`avaliar`/`agregar`/`replay`, módulo puro (sem I/O)
- `scripts/backtest_sinal.py` - vira wrapper: cache em disco (`carregar`, agora usando `yahoo.confere_granularidade`), apresentação/CLI (`_tab`, `main`), reexportação de nomes de `signal_replay`
- `server/tests/test_yahoo_granularidade.py` - novo; 10 testes (espaçamento offline + meta.dataGranularity via mock de `_yfetch` + 1 teste ao vivo gated por `B3_TESTE_REDE`)
- `server/tests/test_signal_replay.py` - novo; 14 testes (sinais_do_ticker, as 4 resoluções da barreira + dataResolucao, agregar, replay)

## Decisions Made
- Tabela `_ESPACAMENTO` ampliada para `5d`/`1mo`/`3mo` além dos `1d`/`1wk` que só existiam no script — nenhum consumidor de `get_history` nesses intervalos tinha proteção antes deste plano.
- Guard de `meta.dataGranularity` fora do intraday usa ordem de granularidade (`_GRANULARIDADE_ORDEM`) e só recusa quando a granularidade devolvida é mais GROSSA que a pedida — decisão explícita do plano para não arriscar falso positivo em fetch diário de produção por variação de rótulo do Yahoo.
- Testes de `sinais_do_ticker` mockam `setups.detect_setups`/`plano_do_resultado` em vez de reengenhar uma série sintética que dispare um setup real com níveis operacionais (gatilho/invalidação) — a mecânica de detecção de setup já é travada em `test_setups.py`; validado empiricamente que setups sem `_mk()` (como "Rompimento com volume") não geram `gatilho`/`invalidacao` e portanto não viram plano, então uma série "óbvia" de rompimento não bastaria sem engenharia adicional dos setups FASE 1 (9.1/9.2/IFR2/etc.), que por sua vez exigem ≥200 candles para SMA200. Mockar as dependências mantém o teste focado na orquestração (chaves do sinal, filtragem por decisão, montagem do regime) sem duplicar cobertura.

## Deviations from Plan

None - plan executado exatamente como escrito. As duas mudanças "aditivas" em `avaliar` (dataResolucao, alvo_campo default) e a criação de `replay()` já estavam explicitamente especificadas no plano.

## Issues Encountered
- Primeira tentativa de engenhar uma série sintética de "Rompimento com volume (alta)" para testar `sinais_do_ticker` produzia veredito correto mas `plano_do_resultado` devolvia `NÃO OPERAR` ("Setup sem gatilho/invalidação numéricos") — descobri por inspeção direta (`detect_setups`/`plano_do_resultado` rodados manualmente) que esse setup específico não popula `gatilho`/`invalidacao` (não usa `_mk()`), só os setups "FASE 1" (9.1, 9.2, IFR2, PFR, etc.) têm níveis operacionais, e vários desses exigem SMA200 (≥200 candles). Resolvido mockando `setups.detect_setups`/`plano_do_resultado` para tornar o teste de orquestração determinístico e independente dessas particularidades — decisão registrada acima.
- Suíte web (`web/tests/*.mjs`) mostrou 7 falhas na primeira rodada por ausência de `web/node_modules` no worktree — comportamento já documentado em `PROJECT.md`/`STATE.md` como falso-positivo de ambiente, não regressão. Resolvido com `npm install` em `web/` (não gera diff versionado, `node_modules/` está no `.gitignore`); suíte completa (`bash scripts/executar.sh --testes`) ficou 100% verde depois.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `server/app/signal_replay.py` está pronto para o Plano 02 (ledger de sinais resolvidos) consumir via `replay()` como ponto de entrada único.
- `yahoo.confere_granularidade` está pronto para o Plano 03 (bootstrap 15 anos × 74 tickers) confiar sem re-verificação adicional — o guard já roda dentro de `get_history`.
- Nenhum bloqueio identificado para os Planos 02/03/04.

---
*Phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: server/app/yahoo.py, server/app/signal_replay.py, scripts/backtest_sinal.py, server/tests/test_yahoo_granularidade.py, server/tests/test_signal_replay.py
- FOUND commits: 92b3c85, 86fe891, 5bf7fd0
- `bash scripts/executar.sh --testes` (pytest + web/tests/*.mjs) verde; `B3_TESTE_REDE=1 bash scripts/test.sh` verde (1154 passed)
