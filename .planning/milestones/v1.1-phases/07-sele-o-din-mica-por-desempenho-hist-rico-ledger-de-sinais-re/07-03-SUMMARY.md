---
phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re
plan: 03
subsystem: data
tags: [bootstrap, cli, backtest, ledger, adr-017, railway]

# Dependency graph
requires:
  - "server/app/signal_replay.py — replay() (Plano 01)"
  - "server/app/signal_ledger.py — registrar_linhas/apagar_tudo/contar/agregar_cumulativo/agregar_janela (Plano 02)"
provides:
  - "server/app/signal_ledger_bootstrap.py — comando manual `python -m app.signal_ledger_bootstrap`, reexecutável, executável dentro do container do Railway (rootDirectory=/server)"
  - "docs/OPERACAO-ledger-de-sinais.md — runbook local e Railway, custo, quando reexecutar"
affects: [07-04-hook-diario, 07-05-detect-setups-regime-ranquear]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Comando operacional __main__ dentro de server/app/ (não scripts/) para sobreviver ao rootDirectory=/server do deploy — precedente já existia em obslog.py, reaplicado aqui como CLI argparse completa"
    - "Orquestração assíncrona com asyncio.Semaphore + asyncio.as_completed + progresso em stderr, mesmo padrão de scripts/backtest_sinal.py, sem cache em disco (container efêmero)"

key-files:
  created:
    - server/app/signal_ledger_bootstrap.py
    - server/tests/test_signal_ledger_bootstrap.py
    - docs/OPERACAO-ledger-de-sinais.md
  modified: []

key-decisions:
  - "carregar_candles não valida granularidade por conta própria — o guard já roda DENTRO de yahoo.get_history (Plano 01); duplicar a validação aqui seria a mesma reimplementação que o ADR-017 proíbe"
  - "dry-run nunca chama bootstrap_ticker (que grava): chama signal_replay.replay diretamente para contar linhas sem tocar signal_ledger.registrar_linhas nem as agregações finais — garante contar()==0 depois de um dry-run"
  - "--reset roda ANTES da varredura de tickers (apagar_tudo síncrono, sem I/O de rede) — nunca dentro do loop de execução, para não misturar limpeza com gravação incremental"

requirements-completed: [ADR17-B1-02]

# Metrics
duration: ~35min
completed: 2026-08-21
---

# Phase 07 Plan 03: Bootstrap do Ledger de Sinais Summary

**`server/app/signal_ledger_bootstrap.py` — comando manual `python -m app.signal_ledger_bootstrap` que roda o replay determinístico (15 anos × 74 tickers) e grava no ledger, reexecutável via UNIQUE do schema, sem replay próprio, com runbook completo para local e `railway ssh`.**

## Performance

- **Duration:** ~35 min
- **Tasks:** 2/2 completos
- **Files modified:** 3 (2 criados de produção/doc, 1 criado de teste)

## Accomplishments

- `signal_ledger_bootstrap.py`: `carregar_candles` (fetch sem cache em disco,
  guard de granularidade herdado de `yahoo.get_history`), `bootstrap_ticker`
  (síncrono, `signal_replay.replay` + `signal_ledger.registrar_linhas`, grava
  por ticker sem acumular os ~126k sinais em memória), `executar` (semáforo
  de concorrência + progresso em stderr, ticker com fetch quebrado entra em
  `erros` sem derrubar os demais) e `main()` com os 7 argumentos
  (`--anos/--rng/--tickers/--concorrencia/--reset/--dry-run/--db`).
- Idempotência comprovada por teste: `bootstrap_ticker` rodado duas vezes com
  os mesmos candles grava N linhas na primeira e 0 na segunda (UNIQUE do
  ledger, herdado do Plano 02).
- `main()` fecha a carga chamando `agregar_cumulativo`/`agregar_janela(ano
  anterior)` e imprime resumo legível (total no ledger, setups elegíveis,
  insuficientes, `medidoAte`) — `--dry-run` nunca chega nessas duas chamadas.
- `docs/OPERACAO-ledger-de-sinais.md`: runbook com os 7 pontos pedidos pelo
  plano — o que é (com a distinção retrospectivo/prospectivo do ADR-015),
  quando rodar (só 3 casos, não é cron), comando local e via `railway ssh`
  (com o aviso explícito de `/opt/venv/bin/python3`), custo (zero orçamento
  brapi — só Yahoo), como conferir sucesso, o que não fazer.

## Task Commits

Each task was committed atomically:

1. **Task 1: Módulo de bootstrap com CLI executável dentro do container** - `e9f8f83` (feat)
2. **Task 2: Runbook do bootstrap (local e produção)** - `49edfbb` (docs)

## Files Created/Modified

- `server/app/signal_ledger_bootstrap.py` - novo; `carregar_candles`, `bootstrap_ticker`, `executar`, `main`, cabeçalho de módulo explicando por que é manual/pesado, por que vive em `server/app/`, por que é reexecutável, e por que reusa `signal_replay.replay`.
- `server/tests/test_signal_ledger_bootstrap.py` - novo; 8 testes (idempotência de `bootstrap_ticker`, total do ledger == soma por ticker, ticker com fetch quebrado entra em `erros`, `dry-run` não grava, `--reset` apaga antes da carga, `main()` grava as duas agregações, `dry-run` via CLI não grava agregações) — nenhum toca rede.
- `docs/OPERACAO-ledger-de-sinais.md` - novo; runbook operacional completo.
- `.planning/REQUIREMENTS.md` - `ADR17-B1-02` marcado `[x]`/`Complete` via `gsd-sdk query requirements.mark-complete`.

## Decisions Made

- `carregar_candles` não duplica a validação de granularidade — confia inteiramente no guard que já roda dentro de `yahoo.get_history` (Plano 01). Duplicar seria a mesma "segunda implementação" que o ADR-017 explicitamente proíbe para o replay.
- `dry-run` chama `signal_replay.replay` diretamente em vez de `bootstrap_ticker`, para nunca tocar `signal_ledger.registrar_linhas` — garante que `signal_ledger.contar(conn) == 0` depois de um dry-run, e que as agregações finais (`agregar_cumulativo`/`agregar_janela`) também não são chamadas nesse modo.
- `--reset` roda de forma síncrona antes de qualquer fetch de rede (evita misturar `apagar_tudo` com gravação incremental em andamento).
- Documento operacional evita qualquer linguagem de promessa de resultado (`grep -c "garantia\|promete lucro\|vai render"` == 0), conforme princípios 6/8 do `CLAUDE.md`.

## Deviations from Plan

None - plano executado exatamente como escrito. As duas tasks (módulo+testes, runbook) seguiram a estrutura, comportamento e critérios de aceite do `07-03-PLAN.md` sem ajuste de escopo ou arquitetura.

## Issues Encountered

Nenhum. Todos os greps de critério de aceite (linhas do módulo, ausência de `def sinais_do_ticker`/`def avaliar`/"barreira" fora de comentário, cobertura dos 7 argumentos, ausência de `scripts/`, presença de `agregar_cumulativo`/`agregar_janela`) passaram na primeira verificação, e a suíte completa ficou verde sem retrabalho.

## User Setup Required

None - nenhuma configuração de serviço externo. O comando em produção depende de `railway ssh` (acesso já existente do Alex ao serviço) e do `B3_DB_PATH` já configurado no ambiente Railway.

## Next Phase Readiness

- `server/app/signal_ledger_bootstrap.py` está pronto para ser executado manualmente (local ou via `railway ssh`) assim que o Plano 04 (hook diário) e o restante da fase estiverem prontos — não é bloqueante para os planos seguintes, mas é o comando que popula a amostra que `regime.ranquear()` (Plano 05) vai consumir.
- Nenhum bloqueio identificado para o Plano 04 (manutenção diária incremental) ou Plano 05 (`detect_setups`/`regime.ranquear`).
- `bash scripts/test.sh`: 1200 passed, 1 skipped. `bash scripts/executar.sh --testes`: pytest 100% verde; falhas em `web/tests/*.mjs` (7 arquivos: `test_appmode_sincroniza_servidor`, `test_carteira_nativa_sincroniza`, `test_fase2_portfolio`, `test_notif_central`, `test_notify`, `test_oauth_repassa_name_e_code`, `test_pet_resumo_modo_web`) são pré-existentes por ausência de `web/node_modules`/`@capacitor/core` neste worktree — mesmo padrão documentado em `07-01-SUMMARY.md`/`07-02-SUMMARY.md`; este plano é backend-only e não toca nenhum arquivo em `web/`.

---
*Phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: server/app/signal_ledger_bootstrap.py, server/tests/test_signal_ledger_bootstrap.py, docs/OPERACAO-ledger-de-sinais.md
- FOUND commits: e9f8f83, 49edfbb (confirmados em `git log --oneline`)
- `bash scripts/test.sh` verde (1200 passed, 1 skipped); `python3 -m app.signal_ledger_bootstrap --help` lista os 7 argumentos a partir de `server/`
