---
phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re
plan: 02
subsystem: database
tags: [sqlite, backtest, adr-017, expectancia, ledger]

# Dependency graph
requires: []
provides:
  - "Tabela `signal_ledger` no banco PRINCIPAL (mesmo de radar_daily/kv), com UNIQUE(ticker, setup, lado, data_sinal) e dois índices"
  - "server/app/signal_ledger.py: registrar_linhas, apagar_tudo, contar, data_sinal_maxima, agregar_cumulativo, agregar_janela, historico_snapshot, reset_cache"
  - "Duas agregações SQL carimbadas (K_CUMULATIVO / K_JANELA) gravadas em kv global (user_id=None)"
  - "Provedor de histórico por setup com cache em processo (TTL 300s), pronto para detect_setups/regime.ranquear consumirem sem query por request"
affects: [07-03-bootstrap, 07-04-hook-diario, 07-05-detect-setups-regime-ranquear]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ledger append-only idempotente via INSERT OR IGNORE + UNIQUE + conn.total_changes (delta antes/depois) para contar linhas novas sem depender do rowcount de executemany"
    - "Duas agregações SQL (SUM/COUNT condicionais) sobre a mesma tabela, arredondamento em Python (não ROUND() do SQLite) para reproduzir byte a byte scripts/backtest_sinal.agregar"
    - "Cache em processo com TTL + try/except silencioso, no padrão de technical_snapshot._SNAP_CACHE, para dado informativo no caminho síncrono quente"

key-files:
  created:
    - server/app/signal_ledger.py
    - server/tests/test_signal_ledger.py
  modified:
    - server/app/db.py

key-decisions:
  - "Tabela signal_ledger vive no banco PRINCIPAL (mesmo de kv/radar_daily), não em admin_cache/analytics.db — o motor de decisão lê daqui por request, banco separado seria custo de I/O extra sem motivo."
  - "Arredondamento de acerto/expR/somaR feito em Python (round()), não via SQL ROUND(), para garantir paridade byte a byte com scripts/backtest_sinal.agregar (mesma fórmula, mesmo motor de arredondamento) — decisão validada com o advisor antes de implementar."
  - "MIN_N_JANELA=40 herdado literalmente de scripts/backtest_pesos.py:69; célula abaixo do piso nunca vira elegivel=False, sempre None + insuficiente=True."
  - "sem_gatilho fica fora do denominador de todas as estatísticas (n só conta status='resolvido'), evitando o viés que o ADR-015 já corrigiu em analysis_outcomes."

patterns-established:
  - "Um ledger, duas leituras: cumulativa (todo o histórico, atualizada a cada sinal) e por janela anual fechada (walk-forward, congelada) — nunca uma única agregação misturando as duas."

requirements-completed: [ADR17-B1-01]

duration: ~40min
completed: 2026-08-21
---

# Phase 07 Plan 02: Ledger de Sinais Resolvidos Summary

**Tabela `signal_ledger` no banco principal + `server/app/signal_ledger.py` com gravação idempotente, as duas agregações SQL carimbadas (cumulativa e por janela anual, piso `n≥40`) e um provedor de histórico com cache em processo (TTL 300s) que nunca propaga exceção de banco.**

## Performance

- **Duration:** ~40 min
- **Tasks:** 3/3 completos
- **Files modified:** 3 (1 criado: `signal_ledger.py`; 1 modificado: `db.py`; 1 teste criado: `test_signal_ledger.py`)

## Accomplishments
- Schema `signal_ledger` idempotente em `init_db`, com `UNIQUE(ticker, setup, lado, data_sinal)` impedindo amostra inflada por reexecução de bootstrap/hook e dois índices (`idx_signal_ledger_setup`, `idx_signal_ledger_ticker`) para as varreduras que os Planos 03-05 vão fazer.
- `registrar_linhas` idempotente (via `INSERT OR IGNORE` + delta de `conn.total_changes`), derivando `status`/`r`/`data_resolucao` corretamente a partir de `resultado` (sem_gatilho vira NULL nos dois campos).
- `agregar_cumulativo`/`agregar_janela`: as duas agregações SQL sobre o mesmo ledger, com precisão idêntica a `scripts/backtest_sinal.agregar` (acerto 1 casa, expR 3 casas, somaR 1 casa) e carimbo obrigatório (`medidoAte`/`calculadoEm`/`janelaRef`) gravado em kv global.
- Piso de amostra `MIN_N_JANELA=40` respeitado literalmente: célula insuficiente nunca vira `elegivel=False` — sempre `None` + `insuficiente=True`.
- `historico_snapshot`: funde as duas agregações por nome de setup, cache em processo com TTL 300s (custa zero query dentro do TTL) e `try/except` que devolve o cache anterior (ou `{}`) em vez de propagar — nunca derruba a tela do usuário por causa de um dado informativo.

## Task Commits

Cada task foi commitada em ciclo RED→GREEN (TDD):

1. **Task 1: Schema da tabela signal_ledger** — `1dd13b9` (test, RED) → `58ecbfb` (feat, GREEN)
2. **Task 2: Gravação idempotente e as duas agregações SQL** — `4fcc6f1` (test, RED) → `335299d` (feat, GREEN)
3. **Task 3: Provedor de histórico com cache em processo** — `480d194` (test, RED) → `ab8a6dd` (feat, GREEN)

_Nenhuma task precisou de commit de REFACTOR — nenhuma limpeza pós-GREEN foi necessária além do que já entrou no commit GREEN._

## Files Created/Modified
- `server/app/db.py` — schema `signal_ledger` dentro de `init_db` (tabela + 2 índices + comentário-decisão).
- `server/app/signal_ledger.py` (novo) — `MIN_N_JANELA`, `K_CUMULATIVO`, `K_JANELA`, `registrar_linhas`, `apagar_tudo`, `contar`, `data_sinal_maxima`, `agregar_cumulativo`, `agregar_janela`, `TTL_HISTORICO_S`, `_HIST_CACHE`, `reset_cache`, `historico_snapshot`.
- `server/tests/test_signal_ledger.py` (novo) — 27 testes cobrindo schema, idempotência, as duas agregações, piso de amostra e o cache do provedor de histórico.

## Decisions Made
- Arredondamento das agregações feito em **Python** (`round()`), não `ROUND()` do SQLite — ponto levantado explicitamente pelo advisor antes da implementação: o SQL só soma/conta (`SUM`/`COUNT` condicionais), o arredondamento final usa a mesma função que `scripts/backtest_sinal.agregar` usa, eliminando risco de divergência de borda (`.5`) entre os dois motores de arredondamento. Critério de reprodutibilidade do ADR-017 (o bootstrap tem que reproduzir o número exato que a produção mostra).
- `signal_ledger.py` não importa `signal_replay`/`backtest_sinal` — recebe o formato de linha já pronto (dict) e só grava/agrega. Mantém o sentido de dependência scripts→app (o Plano 01, que promove as funções de replay, é paralelo/independente desta plan, `wave: 1`, `depends_on: []`).

## Deviations from Plan

None - plano executado exatamente como escrito. As três tasks TDD (RED→GREEN) seguiram os comportamentos e critérios de aceite do `07-02-PLAN.md` sem necessidade de ajuste de escopo, arquitetura ou correção de bug.

## Issues Encountered
- Primeira versão do teste de `historico_snapshot` (ramo "setup só na cumulativa") assumia que um setup registrado antes de `agregar_cumulativo()` mas fora do ano agregado por `agregar_janela()` ficaria ausente da janela — só que `agregar_janela` varre o ledger inteiro filtrando por ano, então um sinal datado DENTRO do ano agregado aparece nas duas leituras mesmo que só tenha sido "pensado" para a cumulativa. Corrigido movendo a data do sinal de teste (`S_CUM`) para 2024, fora do filtro de `agregar_janela(conn, 2025)` — sem qualquer mudança de código de produção, só ajuste de fixture de teste. Achado durante a Task 3, resolvido antes do commit GREEN.

## User Setup Required
None - nenhuma configuração de serviço externo. Módulo é stdlib `sqlite3` puro, sem pacote novo.

## Next Phase Readiness
- Interface pronta para os Planos 03 (bootstrap), 04 (hook diário) e 05 (`detect_setups`/`regime.ranquear`) consumirem exatamente como especificado no bloco `<interfaces>` do plano: `registrar_linhas` aceita o formato de `signal_replay.replay()` (Plano 01), `historico_snapshot` devolve o dict por setup que os Planos 05 anexam/consomem.
- `bash scripts/test.sh` verde: 1170 passed. `bash scripts/executar.sh --testes` (suíte canônica): pytest 100% verde; 6 falhas pré-existentes em `web/tests/*.mjs` por `@capacitor/core` ausente (`web/node_modules` não instalado neste worktree) — fora do escopo deste plano (backend-only, nenhum arquivo em `web/` tocado). Detalhado em `deferred-items.md`.
- Verificações do bloco `<verification>` do plano conferidas: `grep -rn "signal_ledger" server/app/analytics.py` vazio (ledger não vazou para o banco do portal admin); a única ocorrência de `0.0` perto de `expr`/`acerto` é o literal `100.0` da fórmula de percentual (idêntico a `scripts/backtest_sinal.agregar`) e um comentário documentando a regra — nenhum `0.0` usado como valor de "desconhecido" (todos os casos de n=0 usam `None` explicitamente).

---
*Phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: server/app/db.py, server/app/signal_ledger.py, server/tests/test_signal_ledger.py
- FOUND: .planning/phases/07-.../07-02-SUMMARY.md, .planning/phases/07-.../deferred-items.md
- FOUND commits: 1dd13b9, 58ecbfb, 4fcc6f1, 335299d, 480d194, ab8a6dd (todos em `git log --oneline`)
