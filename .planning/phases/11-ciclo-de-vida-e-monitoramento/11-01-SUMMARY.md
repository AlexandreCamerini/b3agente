---
phase: 11-ciclo-de-vida-e-monitoramento
plan: 01
subsystem: options
tags: [put, ciclo-de-vida, maquina-de-estado, adr-003, adr-005, long-only]

# Dependency graph
requires:
  - phase: 10-ponte-gatilho-put
    provides: "put_suggestions (tabela + módulo): registrar/listar/contar, estado inicial 'armada', CHECK(option_type='put')"
provides:
  - "put_suggestions.transicionar: única porta de escrita de estado, whitelist de campos por COLUNAS_CICLO, gate contra TRANSICOES"
  - "put_suggestions.registrar_pendencia/listar_abertas: rastro de limbo + varredura diária ordenada"
  - "put_lifecycle.py: máquina de decisão PURA (forma_adr003, resolver_spots, intrinseco, decidir) — zero rede, zero escrita, zero import de store"
affects: [11-ciclo-de-vida-e-monitoramento (planos 02/03)]

tech-stack:
  added: []
  patterns:
    - "11 colunas de ciclo de vida em put_suggestions, migração idempotente ALTER TABLE (precedente literal de candle_cache/users), CREATE TABLE + ALTER TABLE cobrem banco novo e banco migrado"
    - "transicionar() como porta única: SELECT estado → valida ESTADOS → valida TRANSICOES[atual] → filtra campos por whitelist → UPDATE com estado_em=_now_iso() → delta de total_changes (nunca rowcount)"
    - "decidir() é PURA: recebe linha+hoje+spots já resolvidos, nunca lê banco/rede — orquestração fica para o Plano 02"
    - "intrinseco() é wrapper fino sobre agent.intrinseco_opcao via import local (evita ciclo, já que agent.py importará este módulo no Plano 02) — PUTLIFE-03 por reuso literal, não cópia"

key-files:
  created:
    - server/app/put_lifecycle.py
    - server/tests/test_put_lifecycle_estados.py
    - server/tests/test_put_lifecycle_decisao.py
  modified:
    - server/app/db.py
    - server/app/put_suggestions.py

key-decisions:
  - "Nenhuma decisão autônoma exigida nesta execução — plano seguido literalmente, todos os guardiões de aceite (incluindo os greps de literal proibido em docstring) passaram na primeira tentativa, aplicando o padrão já documentado em D-EXEC-10-01-01/D-EXEC-10-02-01 desde o primeiro rascunho da docstring de put_lifecycle.py"

requirements-completed: [PUTLIFE-01, PUTLIFE-02, PUTLIFE-03]

duration: ~35min
completed: 2026-08-28
---

# Phase 11 Plan 01: Ciclo de vida da sugestão de put — colunas de estado + máquina de decisão PURA Summary

**`put_suggestions` ganha 11 colunas de ciclo de vida e `transicionar()` como única porta de escrita de estado (proveniência da Fase 10 comprovadamente imutável por essa porta), e `put_lifecycle.py` nasce como máquina de decisão pura que cobre as 5 transições do ROADMAP reusando literalmente `agent.intrinseco_opcao` — nenhuma chamada de rede, nenhum hook, nenhuma escrita na carteira real.**

## Performance

- **Duration:** ~35 min (leitura de contexto até o commit final de Task 2)
- **Completed:** 2026-08-28
- **Tasks:** 2/2
- **Files modified:** 5 (2 modificados, 3 criados)

## Accomplishments

- `put_suggestions` ganha 11 colunas novas em `CREATE TABLE IF NOT EXISTS` (banco novo) E em migração idempotente `ALTER TABLE ... ADD COLUMN` por coluna com `try/except sqlite3.OperationalError` (banco migrado) — mesmo precedente literal de `candle_cache`/`users` em `db.py`. Índice `idx_put_suggestions_estado` novo para a varredura diária do Plano 02.
- `ESTADOS_ROTULO`/`ESTADOS`/`TERMINAIS`/`TRANSICOES`/`MOTIVOS_FECHAMENTO`/`COLUNAS_CICLO` nascem em `put_suggestions.py` — tokens DB-friendly (`expirada_sem_uso`, `executada_simulada`) com rótulo literal do ROADMAP preservado byte a byte em `ESTADOS_ROTULO` (`"expirada sem uso"`, `"executada (simulada)"`).
- `transicionar(conn, id, estado_novo, campos=None)` é a ÚNICA porta de escrita de estado: recusa (devolve 0) qualquer destino não declarado em `TRANSICOES`, incluindo estado inexistente, saída de terminal e `id` ausente — nunca levanta. Filtra `campos` por whitelist `COLUNAS_CICLO` ANTES do UPDATE, o que torna a proveniência da Fase 10 (`premio`/`fonte`/`prov_sha256`/`iv`/`estilo_exercicio`) estruturalmente inalcançável por essa porta — provado por teste dedicado tentando sobrescrever as 4 colunas junto de uma transição válida.
- `monitorada → monitorada` é permitida de propósito (remarcação diária) e atualiza `spot_marcacao`/`marcada_em` sem contar como transição de fato.
- `motivo_fechamento` só aceita o vocabulário do ADR-005 (`stop|alvo|vencimento|manual`); qualquer outro valor é descartado silenciosamente, o resto do UPDATE segue.
- `registrar_pendencia()` grava `pendente_desde` só se ainda `NULL` — a primeira data de pendência é a que vale, tornando limbo silencioso detectável (mitigação T-11-05).
- `listar_abertas()` reusa o mesmo `SELECT`/mapeamento camelCase de `listar()` via helper `_select_e_mapear` compartilhado — sem duplicar SQL, `_COLUNAS` continua sendo a fonte única.
- `put_lifecycle.py` nasce PURO: `forma_adr003()` produz o shape ADR-003 deliberadamente sem `qty` (estruturalmente incapaz de virar posição real); `resolver_spots()` resolve `spotAtual`/`spotLiquidacao` sobre uma lista de candles em qualquer ordem de entrada, pulando item malformado sem abortar; `intrinseco()` é wrapper fino que importa `agent.intrinseco_opcao` localmente (evita ciclo) — reuso literal, PUTLIFE-03 cumprido; `decidir()` cobre as 5 transições do ROADMAP na ordem exata de guardas do plano, nunca inventa preço (armada sem prêmio real fica `armada`), nunca levanta mesmo com `strike`/`premio`/`vencimento` malformados.
- Teste de alcançabilidade prova que os 5 estados de `ESTADOS` são todos alcançáveis por `decidir()`, e um segundo teste varre múltiplos casos confirmando que todo `estado_novo` devolvido é destino válido em `TRANSICOES[estado_atual]`.
- Put que expira fora do dinheiro (strike 30, liquidação 33): `preco_fechamento == 0.0`, `pnl_por_acao == -preco_entrada` — perda total do prêmio, exatamente o comportamento do ADR-005.

## Task Commits

Each task was committed atomically (RED then GREEN, TDD):

1. **Task 1: Colunas de ciclo de vida + transicionar() como única porta de escrita**
   - `03df6aa` (test) — 15 testes de comportamento, RED confirmado (todos os 15 falham por `AttributeError`/schema incompleto)
   - `78ec51e` (feat) — schema + `put_suggestions.py`, GREEN (24/24: 15 novos + 9 da Fase 10 inalterados)
2. **Task 2: put_lifecycle.py — máquina de decisão PURA**
   - `dc22a3a` (test) — 23 testes de comportamento, RED confirmado (`ImportError: app.put_lifecycle` não existe)
   - `8b53246` (feat) — `put_lifecycle.py`, GREEN (23/23)

## Files Created/Modified

- `server/app/db.py` — bloco `put_suggestions` de `init_db`: 11 colunas novas no `CREATE TABLE`, migração idempotente `ALTER TABLE` por coluna, índice `idx_put_suggestions_estado`
- `server/app/put_suggestions.py` — `ESTADOS_ROTULO`/`ESTADOS`/`TERMINAIS`/`TRANSICOES`/`MOTIVOS_FECHAMENTO`/`COLUNAS_CICLO`, 11 colunas em `_COLUNAS`, `transicionar()`, `registrar_pendencia()`, `listar_abertas()`, `_select_e_mapear()` (extraído de `listar()` para reuso)
- `server/app/put_lifecycle.py` — novo: `MOTIVO_VENCIMENTO`, `_numero_positivo()`, `forma_adr003()`, `resolver_spots()`, `intrinseco()`, `_vencida()`, `decidir()`
- `server/tests/test_put_lifecycle_estados.py` — novo: 15 testes (transições, imutabilidade de proveniência, migração idempotente)
- `server/tests/test_put_lifecycle_decisao.py` — novo: 23 testes (forma ADR-003, resolução de spots, intrínseco, decisão, alcançabilidade)

## Acceptance Criteria (verificadas literalmente do plano)

`BASE` (Task 1) = `f9b4e61b6ccda4bb4a749d69cff66b7b09ac1c53` (HEAD antes de qualquer edição desta task).
`BASE` (Task 2) = `78ec51ee51dc26584cb35b6030813537861b64c6` (HEAD antes de qualquer edição da Task 2, recapturado por instrução explícita do plano — as duas tasks editam arquivos disjuntos, então o resultado do diff é o mesmo com qualquer um dos dois BASEs, mas o comando literal usado por task usa o BASE certo daquela task).

### Task 1

| Critério | Resultado |
|---|---|
| `pytest tests/test_put_lifecycle_estados.py -q` → exit 0 | PASSOU (15 passed) |
| `pytest tests/test_put_suggestions.py -q` → exit 0, 9 passed, arquivo inalterado | PASSOU (9 passed); `git diff --stat -- server/tests/test_put_suggestions.py` vazio |
| `ESTADOS` ordenado == `['armada', 'executada_simulada', 'expirada_sem_uso', 'fechada', 'monitorada']` | PASSOU |
| `ESTADOS_ROTULO['expirada_sem_uso'], ESTADOS_ROTULO['executada_simulada']` == `expirada sem uso \| executada (simulada)` | PASSOU |
| `grep -c "ALTER TABLE put_suggestions ADD COLUMN" server/app/db.py` ≥ 1 | PASSOU (1 — laço sobre tupla, 1 linha de código cobre as 11 colunas) |
| `grep -c "CHECK (option_type = 'put')" server/app/db.py` == 1 | PASSOU |
| `grep -v '^#' put_suggestions.py \| grep -cE "buy_option\|sell_option\|close_option_vencida\|set_option_position\|optionPositions"` == 0 | PASSOU |
| `git diff --stat "$BASE" -- server/app/store.py server/app/agent.py server/app/main.py server/app/skill_ref.py server/app/defaults.py web/ web-admin/` → vazio | PASSOU |
| `pytest -q` → exit 0, ≥ baseline + novos | PASSOU (1612 passed, 1 skipped; baseline Fase 10 = 1597 + 15 novos) |

### Task 2

| Critério | Resultado |
|---|---|
| `pytest tests/test_put_lifecycle_decisao.py -q` → exit 0 | PASSOU (23 passed) |
| `'qty' in forma_adr003(...)` → `False` | PASSOU |
| `intrinseco({'strike':30.0}, 28.0), intrinseco({'strike':30.0}, 33.0)` → `2.0 0.0` | PASSOU |
| `grep -v '^#' put_lifecycle.py \| grep -c "intrinseco_opcao"` ≥ 1 | PASSOU (2) |
| `grep -v '^#' put_lifecycle.py \| grep -cE "buy_option\|sell_option\|close_option_vencida\|set_option_position\|optionPositions"` == 0 (docstring incluída) | PASSOU |
| `grep -v '^#' put_lifecycle.py \| grep -cE "^from \.store\|^from \. import store\|import store"` == 0 | PASSOU |
| `grep -v '^#' put_lifecycle.py \| grep -cE "httpx\|await \|asyncio"` == 0 | PASSOU |
| `grep -v '^#' put_lifecycle.py \| grep -cE "\bcall\b\|short\|vendida\|margem"` == 0 (docstring incluída) | PASSOU |
| `git diff --stat "$BASE" -- server/app/store.py server/app/agent.py server/app/main.py server/app/skill_ref.py web/ web-admin/` → vazio | PASSOU |
| `pytest -q` → exit 0, zero regressão | PASSOU (1635 passed, 1 skipped; baseline pós-Task-1 = 1612 + 23 novos) |

### Suíte canônica (contrato de autonomia, item 5 — 2 rodadas)

- `bash scripts/executar.sh --testes` rodada 1: `1635 passed, 1 skipped`, exit 0, 105 `.mjs` OK / 0 FAIL
- `bash scripts/executar.sh --testes` rodada 2: `1635 passed, 1 skipped`, exit 0, 105 `.mjs` OK / 0 FAIL
- Resultado idêntico nas duas rodadas. `git status --short` vazio depois de ambas (nenhum arquivo untracked/gerado deixado para trás).

## Decisões autônomas

Nenhuma decisão autônoma foi necessária nesta execução. O plano foi seguido literalmente task a task; todos os 19 critérios de aceite (9 da Task 1 + 10 da Task 2) passaram na primeira tentativa, incluindo os 4 guardiões de grep contra literal proibido em docstring (`optionPositions`/`buy_option`/`sell_option`/`close_option_vencida`/`set_option_position` e `call`/`short`/`vendida`/`margem`) — a armadilha documentada em D-EXEC-10-01-01/D-EXEC-10-02-01 (grep filtra só linha iniciada em `#`, não prosa de docstring) foi aplicada desde o primeiro rascunho da docstring de `put_lifecycle.py`, sem precisar de reescrita corretiva.

Nada foi acrescentado a `.planning/notes/decisoes-autonomas-v1.2.md` (nenhuma entrada nova, por não haver decisão a registrar).

## Deviations from Plan

Nenhum desvio de Regra 1/2/3/4. Comportamento, schema e nomes de função exatamente como especificado no `11-01-PLAN.md`.

---

**Total deviations:** 0.
**Impact on plan:** Nenhum.

## Verificações adicionais pós-implementação

- Confirmação manual de que `decidir()` nunca lê banco/rede — recebe `linha`/`hoje`/`spots` já resolvidos, toda I/O fica para o Plano 02 (hook do `scheduler_loop`), consistente com o contrato de pureza da Task 2.
- `resolver_spots()` foi testado deliberadamente com candles fora de ordem cronológica e com item malformado misturado (`"nao é dict"`, dict sem `date`, `close` string, `close` negativo) para provar que a busca por extremos (maior data ≤ hoje / menor data ≥ vencimento) é robusta à ordem de entrada da lista, não só ao primeiro/último item — o `<behavior>` do plano não exige isso explicitamente, mas é a leitura mais defensiva de "candle malformado é pulado por item, nunca aborta a resolução".
- `transicionar()` e `decidir()` produzem, juntos, o par (porta de escrita + máquina de decisão) que o Plano 02 vai conectar via hook diário — nenhuma das duas funções chama a outra diretamente nesta task, por desenho (a orquestração explícita é escopo do Plano 02).

## Issues Encountered

Nenhum. `server/.venv` não existe dentro do worktree (mesmo achado já registrado em `10-01-SUMMARY.md`/`00-01-SUMMARY.md`) — usado o Python do `.venv` do clone principal (`/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python`) para todos os comandos `pytest`/`python -c`; `scripts/executar.sh` resolve isso sozinho.

## User Setup Required

None. Nenhuma variável de ambiente tocada, `B3_OPTIONS_PROVIDER` nunca lido nem alterado neste plano (módulo puro, sem rede). Nenhum git push, nenhum deploy.

## Next Phase Readiness

- `put_suggestions.transicionar`/`registrar_pendencia`/`listar_abertas` e `put_lifecycle.decidir`/`resolver_spots`/`intrinseco`/`forma_adr003` estão prontos para o Plano 02 pendurar o hook diário (mesmo padrão de `put_bridge.maybe_run`/`run_diario`) que: varre `listar_abertas()`, resolve candles reais via `candle_cache.peek`, chama `decidir()` por linha e aplica o resultado via `transicionar()`/`registrar_pendencia()`.
- Nenhuma rota HTTP, nenhum export para front, nenhuma superfície visível — T-11 threat register segue sem exposição ativa porque não há hook ainda rodando; o Plano 03 (formal, como no PUT-03/10-03) prova isso por guardião automatizado.
- Suíte canônica validada 2x (exigência do contrato de autonomia): ambas `1635 passed, 1 skipped`, exit 0, 105 `.mjs` OK / 0 falhas, 0 arquivos untracked.

---
*Phase: 11-ciclo-de-vida-e-monitoramento*
*Completed: 2026-08-28*

## Self-Check: PASSED

- FOUND: `.planning/phases/11-ciclo-de-vida-e-monitoramento/11-01-SUMMARY.md`
- FOUND: `server/app/put_lifecycle.py`
- FOUND: `server/app/put_suggestions.py`
- FOUND: `server/app/db.py`
- FOUND: `server/tests/test_put_lifecycle_estados.py`
- FOUND: `server/tests/test_put_lifecycle_decisao.py`
- FOUND: commit `03df6aa` (Task 1 RED)
- FOUND: commit `78ec51e` (Task 1 GREEN)
- FOUND: commit `dc22a3a` (Task 2 RED)
- FOUND: commit `8b53246` (Task 2 GREEN)
