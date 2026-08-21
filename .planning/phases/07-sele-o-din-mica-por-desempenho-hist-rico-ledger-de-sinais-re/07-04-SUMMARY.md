---
phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re
plan: 04
subsystem: data
tags: [sqlite, backtest, adr-017, ledger, scheduler-hook, python, pytest]

# Dependency graph
requires:
  - "server/app/signal_replay.py (Plano 01) — replay() como ponto de entrada único"
  - "server/app/signal_ledger.py (Plano 02) — registrar_linhas, data_sinal_maxima, agregar_cumulativo, agregar_janela"
provides:
  - "candle_cache.peek() — leitura de candles JÁ buscados, ZERO rede, fonte única do hook diário"
  - "server/app/signal_ledger_job.py: should_run/maybe_run/run_incremental/maybe_fechar_janela — hook completo e testado, ainda NÃO pendurado no scheduler_loop"
affects: [07-06-fiacao-do-hook-no-scheduler-loop]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cursor incremental DERIVADO do próprio dado (data_sinal_maxima), nunca uma chave kv paralela — sobrevive a --reset do bootstrap sem reconciliação"
    - "try/except cobrindo dois passos consecutivos (replay + registrar_linhas) quando qualquer um dos dois pode falhar por-item num laço em lote — não escopar o try só no primeiro passo"
    - "Gate diário replicado estruturalmente de radar_daily.should_run/maybe_run (dia útil + horário + last_date != hoje, persistido em kv, LAST_RUN em memória, try/except que nunca propaga)"
    - "asyncio.to_thread para tirar trabalho CPU-bound do laço único do agente sem criar segundo scheduler"

key-files:
  created:
    - server/app/signal_ledger_job.py
    - server/tests/test_signal_ledger_job.py
  modified:
    - server/app/candle_cache.py

key-decisions:
  - "try/except do run_incremental cobre replay() E registrar_linhas() no MESMO bloco (achado do plan-checker, 07-04 warning) — escopar só no replay deixaria uma falha de registrar_linhas (ex. IntegrityError fora do UNIQUE esperado) propagar pro laço externo e abortar o dia inteiro pros tickers restantes"
  - "maybe_fechar_janela(conn, now) chama pregao.is_trading_day(now.date()) — não pregao.is_trading_day() sem argumento. Passar o `now` simulado explicitamente evita que testes com `now` fixo fiquem dependentes do relógio de parede real na hora de rodar a suíte (achado do advisor antes da Task 3)"
  - "HHMM_DEFAULT do ledger é 09:15, 30 min depois do Radar diário (08:45) — de propósito, para o hook ler candles que o Radar já buscou minutos antes"
  - "signalLedgerLastRun só é gravado no caminho de SUCESSO de maybe_run — falha permite retentativa no próximo tick do laço em vez de travar até amanhã"

requirements-completed: []

# Metrics
duration: ~35min
completed: 2026-08-21
---

# Phase 07 Plan 04: Manutenção Diária do Ledger (Hook Incremental) Summary

**`candle_cache.peek()` (leitura sem rede) + `server/app/signal_ledger_job.py` completo: avanço incremental do ledger com cursor derivado do próprio dado, gate diário no padrão de `radar_daily`, e fechamento de janela anual alinhado ao calendário da B3 — hook pronto e testado, ainda não pendurado no `scheduler_loop` (isso é o Plano 06).**

## Performance

- **Duration:** ~35 min
- **Tasks:** 3/3 completos
- **Files modified:** 3 (1 criado: `signal_ledger_job.py`; 1 modificado: `candle_cache.py`; 1 teste criado/expandido: `test_signal_ledger_job.py`)

## Accomplishments

- `candle_cache.peek(symbol, interval)`: leitura síncrona sem nenhum ramo de fetch, reidrata do L2 quando o L1 está frio (mesmo caminho de `load`), `[]` em intraday (L2 desligado por ADR-001) ou quando não há nada em cache — a única fonte de dado do hook diário, garantindo zero requisição extra de brapi (ADR-008).
- `run_incremental(conn, universo=None)`: para cada ticker, lê `candle_cache.peek`, deriva o cursor de `signal_ledger.data_sinal_maxima` (nunca uma chave kv paralela), reprocessa só os dias novos (`DIAS_RECUPERACAO=60` na primeira vez, senão dias após a última data + `MARGEM_REPROCESSO=3`), grava via `signal_replay.replay` + `signal_ledger.registrar_linhas` dentro do MESMO `try/except` — isola erro por ticker sem abortar o lote. Regrava a agregação cumulativa e invalida o cache do provedor de histórico só quando gravou linha nova.
- `should_run`/`enabled`/`last_run_date`: cópia estrutural do gate de `radar_daily` (dia útil + horário `B3_LEDGER_DAILY_HHMM` default 09:15 + ainda não rodou hoje), com kill-switch próprio `B3_LEDGER_DAILY_OFF`.
- `maybe_fechar_janela(conn, now)`: fecha `signal_ledger.agregar_janela` do ANO ANTERIOR (nunca o corrente — evita o vazamento de futuro que `backtest_pesos.py` foi escrito para prevenir), alinhado a `pregao.is_trading_day(now.date())`, marcador em kv (`signalLedgerJanelaFechada`) impede regravação na mesma virada.
- `maybe_run(conn)`: assíncrono, roda `run_incremental` via `asyncio.to_thread` (tira o trabalho CPU-bound do laço único do agente), `try/except` no padrão de `radar_daily.maybe_run` que nunca propaga, grava `signalLedgerLastRun` só no caminho de sucesso, telemetria em `LAST_RUN` no formato de `radar_daily.LAST_DAILY`.

## Task Commits

Each task was committed atomically:

1. **Task 1: candle_cache.peek — ler o cache de candles sem tocar na rede** - `5d14298` (feat)
2. **Task 2: Avanço incremental do ledger (cursor derivado do próprio ledger)** - `be70f04` (feat)
3. **Task 3: Gate diário, fechamento de janela anual e maybe_run assíncrono** - `7448f5a` (feat)

**Plan metadata:** (este commit, docs)

## Files Created/Modified

- `server/app/candle_cache.py` - `peek(symbol, interval="1d")` novo: leitura L1/L2 sem fetch.
- `server/app/signal_ledger_job.py` (novo, 227 linhas) - `DIAS_RECUPERACAO`, `MARGEM_REPROCESSO`, `run_incremental`, `HHMM_DEFAULT`, `LAST_RUN`, `_hhmm`, `enabled`, `should_run`, `last_run_date`, `maybe_fechar_janela`, `maybe_run`.
- `server/tests/test_signal_ledger_job.py` (novo) - 24 testes cobrindo `peek` (5), `run_incremental` (7), gate/janela/`maybe_run` (12).

## Decisions Made

- try/except de `run_incremental` cobre `replay()` **e** `registrar_linhas()` no mesmo bloco — achado explícito do plan-checker (07-04, warning) já corrigido na versão do plano lida no início da execução; validado com um teste dedicado que faz `registrar_linhas` levantar (não `replay`) para um ticker específico e prova que o outro ticker do lote segue gravando normalmente.
- `maybe_fechar_janela` chama `pregao.is_trading_day(now.date())` passando o `now` simulado explicitamente, em vez de `pregao.is_trading_day()` sem argumento (que cairia no relógio de parede real). Achado do advisor antes de implementar a Task 3: sem essa consistência, um teste com `now` fixo ficaria dependente do dia real em que a suíte roda.
- `HHMM_DEFAULT = "09:15"`, 30 minutos depois do Radar diário (`radar_daily.HHMM_DEFAULT = "08:45"`) — dependência de ordem documentada em comentário: o hook lê do cache que o Radar acabou de preencher.
- Testes de `run_incremental`/`maybe_run` monkeypatcham `signal_replay.replay`/`signal_ledger.registrar_linhas`/`agregar_cumulativo` em vez de engenhar séries sintéticas que disparem setups reais — mesma decisão já tomada e documentada no Plano 01 (setups sem `_mk()` não geram plano operável; setups com níveis operacionais exigem SMA200/≥200 candles). O foco aqui é a orquestração do job (cursor, isolamento de erro, gate), não a mecânica de detecção de setup, já coberta em `test_setups.py`/`test_signal_replay.py`.

## Deviations from Plan

None - plano executado exatamente como escrito, incluindo a correção do plan-checker (try/except cobrindo replay+registrar_linhas) já presente na versão do PLAN.md lida no início da execução.

## Issues Encountered

- `web/tests/*.mjs` mostrou 6 falhas na primeira rodada de `bash scripts/executar.sh --testes` por ausência de `web/node_modules` neste worktree fresco — mesmo falso-positivo de ambiente já documentado no 07-01-SUMMARY (não regressão, este plano é backend-only e não tocou `web/`). Resolvido com `npm install` em `web/` (gitignored, sem diff versionado); suíte completa ficou 100% verde depois (backend 1216 passed, 1 skipped; JS todas OK).

## User Setup Required

None - nenhuma configuração de serviço externo. `signal_ledger_job.py` só depende de módulos já existentes no repo.

## Requirements Note

`ADR17-B1-03` (frontmatter deste plano) é **parcialmente** satisfeito por este plano: o job (gate + avanço incremental + fechamento de janela + `maybe_run` assíncrono) está completo e testado, mas o texto do requisito inclui "pendurada no `scheduler_loop`" — essa fiação é explicitamente Escopo do Plano 06 (`07-06-PLAN.md`, que também lista `ADR17-B1-03` no frontmatter, junto com `ADR17-B1`/`ADR17-B1-05`). Por isso **não marquei `ADR17-B1-03` como completo em REQUIREMENTS.md** — fica `Pending` até o Plano 06 pendurar o hook e fechar o requisito por completo, evitando marcar como pronto algo que ainda não está no ar.

## Next Phase Readiness

- `server/app/signal_ledger_job.py` está pronto para o Plano 06 pendurar `maybe_run(conn)` no `scheduler_loop` (mesmo bloco de `radar_daily.maybe_run`/`analysis_outcomes.maybe_run`, `agent.py` ~1074-1087) — a interface já expõe exatamente o que o bloco `<interfaces>` do 07-04-PLAN.md prometia: `HHMM_DEFAULT`, `LAST_RUN`, `enabled()`, `should_run()`, `last_run_date()`, `run_incremental()`, `maybe_fechar_janela()`, `maybe_run()`.
- `grep -rn "signal_ledger_job" server/app/agent.py` confirmado vazio — a fiação não vazou para este plano por engano.
- Nenhum bloqueio identificado para o Plano 06.

---
*Phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: server/app/candle_cache.py, server/app/signal_ledger_job.py, server/tests/test_signal_ledger_job.py
- FOUND commits: 5d14298, be70f04, 7448f5a (todos em `git log --oneline`)
- `bash scripts/executar.sh --testes` (pytest 1216 passed/1 skipped + web/tests/*.mjs) verde após `npm install` em `web/`
