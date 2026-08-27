---
phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa
plan: 05
subsystem: infra
tags: [adr, cotahist, b3-historical, rbac, scheduler, cleanup, checkpoint-decision]

# Dependency graph
requires:
  - phase: "09-01/09-02/09-03/09-04"
    provides: "mydata_client.py, MydataProvider/MydataOptionsProvider atrás dos contratos existentes, medição de rate-limit (docs/MEDICAO-Mydata-2026-08-27.md) — a fatia diária que este plano aposenta o código paralelo"
provides:
  - "b3_historical.py e sua fiação (hook do scheduler_loop, rotas admin /api/admin/b3/cotahist*, tabelas b3_daily_imports/b3_daily_quotes, entidade RBAC b3_daily_import) removidos do caminho de código ativo — commit b3fdf02 permanece recuperável no histórico"
  - "docs/adr/019-cotahist-diario-b3.md carimbada com status de supersessão parcial, corpo original intacto"
  - "docs/adr/020-centralizacao-de-dados-no-mydata.md: registro formal da supersessão/não-supersessão de ADR-001/004/008/019, decisões D-01 a D-04 rastreadas, números da medição do Plano 09-04, reversibilidade por env"
affects: [09-06-checkpoint-virada-producao]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - docs/adr/020-centralizacao-de-dados-no-mydata.md
  modified:
    - server/app/agent.py
    - server/app/main.py
    - server/app/db.py
    - server/app/rbac.py
    - docs/adr/019-cotahist-diario-b3.md

key-decisions:
  - "Alex escolheu 'remover' no checkpoint humano bloqueante da Task 1 — não 'congelar' nem 'desfazer-o-commit'. Decisão comunicada ao orquestrador antes desta execução (AskUserQuestion já resolvido); esta execução reconfirmou o estado do git/banco e prosseguiu direto para Task 2/3."
  - "git rm dos dois arquivos rastreados + fiação desfeita + carimbo do ADR-019, tudo em UM commit citando ADR-020 e b3fdf02 — NÃO git revert (que apagaria a própria ADR-019 do disco)."
  - "Tabelas b3_daily_imports/b3_daily_quotes NÃO foram tocadas no banco local (sem DROP TABLE) — só o CREATE TABLE saiu do init_db. Ficam órfãs e inertes no SQLite de desenvolvimento do Alex; limpeza é ação destrutiva separada, fora do escopo desta task."

requirements-completed: []

# Metrics
duration: ~25min
completed: 2026-08-27
---

# Phase 9 Plan 05: Aposentadoria do COTAHIST paralelo (ADR-020) Summary

**A ingestão paralela do COTAHIST (`b3_historical.py`, ADR-019) saiu do caminho de código ativo por decisão do Alex ("remover"), com o commit que a implementou (`b3fdf02`, não pushado) preservado no histórico; ADR-020 registra formalmente a supersessão parcial de ADR-001/004/008/019 com os números medidos no Plano 09-04.**

## Performance

- **Duration:** ~25 min (Task 2 + Task 3; Task 1 já resolvida pelo orquestrador antes desta execução)
- **Tasks:** 3/3 completos (Task 1 pré-resolvida "remover"; Task 2 e 3 executadas nesta sessão)
- **Files modified:** 6 (5 editados/removidos + 1 novo)

## Accomplishments

- Hook do `scheduler_loop` que baixava o COTAHIST direto de `bvmf.bmfbovespa.com.br` removido de `server/app/agent.py`, sem tocar nos hooks vizinhos (`analytics`, `automacao`, `obs-metricas`, `radar_daily`, `fundamentals.maybe_warm`, `signal_ledger_job` — confirmados intactos por grep).
- Import e as duas rotas admin (`GET`/`POST /api/admin/b3/cotahist*`) removidos de `server/app/main.py`.
- `CREATE TABLE`/`CREATE INDEX` de `b3_daily_imports`/`b3_daily_quotes` removidos de `server/app/db.py::init_db` — sem `DROP TABLE`, sem tocar em dado nenhum.
- `server/app/rbac.py::ENTIDADES_POR_PERMISSAO["fontes_dados.configurar"]` revertido para `{"brapi_spot_intervalo"}`.
- `server/app/b3_historical.py` e `server/tests/test_b3_historical.py` removidos via `git rm` (rastreados desde `b3fdf02`) — árvore limpa, saída registrada em commit, não em disco solto.
- `docs/adr/019-cotahist-diario-b3.md` carimbada com `**Status:** Superada parcialmente pela ADR-020 (2026-08-27)...` — só 2 linhas adicionadas, corpo original intacto (provado por `git diff b3fdf02`).
- `docs/adr/020-centralizacao-de-dados-no-mydata.md` escrita com as 6 seções exigidas (Contexto, Decisão, Status das ADRs anteriores, Consequências, Medição, Reversibilidade), decisões D-01 a D-04 rastreadas, tabela de status das 4 ADRs anteriores, números reais do `docs/MEDICAO-Mydata-2026-08-27.md`.

## Task Commits

1. **Task 1: Decisão do Alex sobre o destino do código do ADR-019** — resolvida pelo orquestrador ANTES desta execução (checkpoint humano bloqueante, `AskUserQuestion`). Resposta literal: **"remover"**. Nenhum commit — task é diagnóstico/apresentação puro, sem ação em disco.
2. **Task 2: Executar a decisão e desfiar o scheduler** — `ce1c207` (refactor) — fiação desfeita em `agent.py`/`main.py`/`db.py`/`rbac.py`, `git rm` dos dois arquivos de `b3_historical`, carimbo do ADR-019, tudo num commit só citando `ADR-020` e `b3fdf02`.
3. **Task 3: ADR-020 — o que foi superado, e o que deliberadamente não foi** — `6c71414` (docs) — `docs/adr/020-centralizacao-de-dados-no-mydata.md` criada.

## Files Created/Modified

- `server/app/agent.py` — bloco `try/except` do hook `b3_historical.maybe_run` removido (8 linhas), hooks vizinhos intactos
- `server/app/main.py` — import `from . import b3_historical` e as 2 rotas admin removidas (~46 linhas)
- `server/app/db.py` — 2 `CREATE TABLE IF NOT EXISTS` + 2 `CREATE INDEX` removidos de `init_db`
- `server/app/rbac.py` — `fontes_dados.configurar` revertido para `{"brapi_spot_intervalo"}`
- `server/app/b3_historical.py` — removido (`git rm`)
- `server/tests/test_b3_historical.py` — removido (`git rm`)
- `docs/adr/019-cotahist-diario-b3.md` — cabeçalho de status acrescentado, corpo intacto
- `docs/adr/020-centralizacao-de-dados-no-mydata.md` — novo, 195 linhas

## Estado real encontrado na Task 1 (reconfirmado nesta execução) vs. esperado

- **`git status --short`:** limpo, exceto dois arquivos de sessão não relacionados a este plano (`.planning/cowork-sync-2026-08-27.md`, `.planning/notes/protocolo-cowork-code.md`) — fora de escopo, não tocados.
- **`git log --oneline origin/main..HEAD`:** confirmado — `b3fdf02` é **local, não pushado**. Bate com a premissa do plano.
- **`git show --stat b3fdf02`:** confirmado — 7 arquivos, o commit descrito na premissa do plano.
- **`git log b3fdf02..HEAD -- <7 arquivos>`:** UMA divergência da premissa "nada tocou esses arquivos depois de `b3fdf02`" — o commit `d517755` (trabalho já mergeado do Plano 09-03) tocou `server/app/main.py` e `server/app/agent.py` DEPOIS de `b3fdf02`, mas só para renomear referências de `options_provider_yahoo` para `options_provider` (troca de seletor da migração de opções) — regiões de código não relacionadas à fiação do `b3_historical`. Confirmado por `git show d517755 --stat` e leitura do diff antes de editar: não bloqueou nem complicou a remoção.
- **Contagem das tabelas no banco local:** a premissa do plano citava `b3_daily_imports`=1/`b3_daily_quotes`=16.846; o estado real encontrado (repassado pelo orquestrador) foi `b3_daily_imports`=2/`b3_daily_quotes`=33.621 — mais alto, porque a ingestão paralela rodou de novo entre a escrita da premissa e a execução. **As tabelas NÃO foram tocadas** por esta task (proibição explícita de `DROP TABLE`/mexer em banco) — ficam órfãs e inertes no SQLite de desenvolvimento do Alex.

## Decisions Made

Ver `key-decisions` no frontmatter. Resumo: Alex escolheu **remover** (não `congelar` nem `desfazer-o-commit`) no checkpoint bloqueante da Task 1, comunicado ao orquestrador antes desta execução via `AskUserQuestion`. A mecânica de execução seguiu literalmente a `<recommendation>` do plano: `git rm` explícito + fiação desfeita + carimbo, tudo num commit — nunca `git revert b3fdf02` (que apagaria a própria `docs/adr/019-cotahist-diario-b3.md` do disco, violando o guardrail "histórico não se reescreve").

## Deviations from Plan

None além da divergência já registrada acima (commit `d517755` tocando `agent.py`/`main.py` em região não relacionada) — sinalizada, avaliada como não-bloqueante, e a execução prosseguiu conforme o plano. Nenhum Rule 1/2/3 disparado: as edições de Task 2 seguiram exatamente a `<action>` do plano, e a Task 3 seguiu as 6 seções obrigatórias sem necessidade de correção.

## Issues Encountered

None. Suíte canônica (`bash scripts/executar.sh --testes`) verde: 1514 passed, 1 skipped (backend) + todas as `web/tests/*.mjs` OK, exit code 0. `cd server && python -c "from app import main"` importa sem erro.

## User Setup Required

None neste plano.

## Next Phase Readiness

- Nenhum caminho de código no servidor baixa COTAHIST da B3 por conta própria — confirmado por `grep -rlE 'bvmf.bmfbovespa.com.br|COTAHIST_D' server/app/` (vazio).
- `docs/adr/020-centralizacao-de-dados-no-mydata.md` está pronta como referência do checkpoint humano do Plano 09-06 (virada de `B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER` para `mydata`), incluindo os dois achados de arquitetura pendentes de mitigação antes da virada: pico/min do mydata (NÃO CABE, 148 de 60/min) e ausência de gate de orçamento na cadeia de opções.
- `b3fdf02` segue no histórico local, não pushado — a regra de processo desta fase (checkpoint humano bloqueante do Plano 09-06) continua segurando o push de TODA a fase até a aprovação final, garantindo que `b3fdf02` e o commit de remoção (`ce1c207`) viajem juntos.
- Nenhum bloqueio conhecido para o Plano 09-06.

## Self-Check: PASSED

- FOUND: docs/adr/020-centralizacao-de-dados-no-mydata.md
- FOUND: .planning/phases/09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa/09-05-SUMMARY.md
- MISSING (esperado — removido por decisão "remover"): server/app/b3_historical.py
- MISSING (esperado — removido por decisão "remover"): server/tests/test_b3_historical.py
- FOUND commits: ce1c207, 6c71414 (verified via `git log --oneline -3`)
- CONFIRMED: `git cat-file -e b3fdf02^{commit}` → OK (b3fdf02 continua no histórico)

---
*Phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa*
*Completed: 2026-08-27*
