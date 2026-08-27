---
phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa
plan: 01
subsystem: api
tags: [httpx, mydata, cotahist, b3, rate-limit, cursor-pagination, tdd]

# Dependency graph
requires: []
provides:
  - "server/app/mydata_client.py: cliente HTTP async do hub mydata.acamerini.app (auth X-API-Key, retry curto em 5xx, sem retry em 429/401, paginação por proximo_cursor com teto anti-loop, get_history() no contrato CandleProvider)"
  - "server/app/mydata_budget.py: orçamento local 60/min · 2.000/dia (janela do minuto só memória, janela do dia persistida no kv), sem fatias, sem gate de pregão, pacer async aguarda_vaga()"
  - "26 guardiões offline em server/tests/test_mydata_client.py + 11 em server/tests/test_mydata_budget.py"
affects: [09-02-candles, 09-03-opcoes, 09-05-checkpoint-b3-historical]

# Tech tracking
tech-stack:
  added: []   # nenhuma dependência nova — httpx já está em requirements.txt
  patterns:
    - "Cliente HTTP async com fetch_json injetável para teste offline (mesma forma de brapi.py)"
    - "Paginação por cursor com teto anti-loop (PAGINAS_MAX) — primeiro precedente desse padrão no repo"
    - "Orçamento com duas janelas independentes (minuto em memória + dia persistido no kv) — primeiro precedente de janela por minuto no repo"

key-files:
  created:
    - server/app/mydata_client.py
    - server/app/mydata_budget.py
    - server/tests/test_mydata_client.py
    - server/tests/test_mydata_budget.py
  modified: []

key-decisions:
  - "PAGINAS_MAX=8 (planejado, não alterado): com limite=2000 registros/página, cobre até 16.000 linhas de gold_cotacoes por chamada — folga generosa sobre o maior range (RANGE_DIAS['max']=3700 dias corridos ≈ 2.500 pregões, bem abaixo de 16.000)"
  - "MARGEM=0.9 em mydata_budget: teto útil = 90% da cota real, para o contador local nunca deixar a chamada real bater no 429 do hub antes de o contador local perceber"
  - "Janela do minuto é fixa em memória (chave 'AAAA-MM-DD HH:MM'), não deslizante nem persistida — decisão do plano, não precisa sobreviver a deploy"
  - "get_history usa 'de' sem 'ate' (busca tudo desde a janela até hoje) — o endpoint já ordena ASC e o cliente não precisa fixar o fim da janela"

requirements-completed: []

# Metrics
duration: ~35min
completed: 2026-08-27
---

# Phase 9 Plan 01: Cliente mydata + orçamento de cota Summary

**Cliente HTTP async do hub mydata.acamerini.app (auth X-API-Key, paginação por cursor, mapeamento COTAHIST→candle) e orçamento local de 60/min·2.000/dia com duas janelas independentes — nenhuma fiação em candle_provider/options_api ainda, só a fronteira nova e seus 37 guardiões offline.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-08-27T21:55:00Z (aprox.)
- **Completed:** 2026-08-27T22:31:00Z
- **Tasks:** 3/3 completos
- **Files modified:** 4 (todos novos, nenhum arquivo existente tocado)

## Accomplishments
- Cliente `mydata_client.py`: autentica por `X-API-Key` (nunca `Authorization`/Bearer), valida `MYDATA_URL` contra esquema não-TLS fora de localhost (T-09-02), captura `X-Quota-Limite`/`X-Quota-Restante` de toda resposta em `LAST_QUOTA`, nunca faz retry em 429/401/403 (retry queimaria cota), tenta 5xx duas vezes, e percorre `proximo_cursor` com teto de 8 páginas contra loop infinito.
- `get_history()` recusa qualquer `interval != "1d"` ANTES de tocar a rede (o COTAHIST não publica intraday — ADR-001 intocada) e mapeia `gold_cotacoes`→candle preservando `volume = quantidade_negociada` (papéis), nunca o notional em reais.
- `mydata_budget.py`: duas janelas independentes (minuto fixo em memória, dia persistido no `kv` sobrevivendo a restart), sem fatias (cota combinada candles+opções), deliberadamente sem gate de horário de pregão (dado é EOD), com `snapshot()` expondo a cota real do header ao lado da previsão local.
- 37 guardiões novos (26 + 11), todos offline — nenhum teste toca rede.

## Task Commits

Cada task seguiu RED→GREEN (TDD):

1. **Task 1: Cliente HTTP — auth, retry, cota, paginação**
   - `8228210` (test) — 15 guardiões offline, RED confirmado (ImportError)
   - `3ebfbac` (feat) — implementação, GREEN (15/15), inclui correção de um bug na própria asserção de teste (Rule 1)
2. **Task 2: get_history — recusa de intraday, mapeamento gold_cotacoes**
   - `253f42d` (test) — 11 guardiões adicionais, RED confirmado (AttributeError)
   - `e8a7fc9` (feat) — implementação, GREEN (26/26)
3. **Task 3: mydata_budget — cota 60/min · 2.000/dia**
   - `3f8164b` (test) — 11 guardiões, RED confirmado (ImportError)
   - `566eeed` (feat) — implementação, GREEN (11/11), inclui ajuste de um teste com limiar exato (Rule 1) e remoção de referência literal a `em_pregao` no docstring (guardião do plano exige ausência)

## Files Created/Modified
- `server/app/mydata_client.py` (217 linhas) - cliente async: `base_url`, `tem_token`, `_fetch_json`, `_paginar`, `valida_fatia`, `get_history`, exceções `MydataIndisponivel`/`MydataForaDaFatia`, `LAST_QUOTA`
- `server/app/mydata_budget.py` (188 linhas) - `configure_db`, `quota_min`/`quota_dia`, `pode_gastar`/`debita`, `degradado`, `aguarda_vaga`, `snapshot`, `reset`
- `server/tests/test_mydata_client.py` (332 linhas) - 26 guardiões offline
- `server/tests/test_mydata_budget.py` (142 linhas) - 11 guardiões offline

## Decisions Made
- **PAGINAS_MAX = 8** — valor planejado, mantido sem alteração. Com `LIMITE_MAX=2000` por página, o teto cobre até 16.000 linhas por chamada de `get_history`; o maior range suportado (`"max": 3700` dias corridos) equivale a bem menos que 2.500 pregões, então o teto nunca é alcançado em uso normal — só protege contra um servidor que nunca zera `proximo_cursor`.
- **MARGEM = 0.9** em `mydata_budget` (não estava explicitamente fixado no plano como valor final, mas é o valor prescrito na `<action>` da Task 3) — teto útil local fica em 90% da cota real, dando folga para o contador local nunca deixar uma chamada real estourar o 429 do hub antes de o contador perceber.
- Nenhum campo de `gold_cotacoes` divergiu do mapeamento planejado: `dt_pregao→date`, `preco_abertura→open`, `preco_maximo→high`, `preco_minimo→low`, `preco_fechamento→close`, `quantidade_negociada→volume`. `volume_financeiro`, `hv21`, `hv63`, `preco_medio` e `proveniencia` foram deliberadamente deixados de fora do payload (fora do contrato fechado de `CandleProvider`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Asserção de teste verificava o lugar errado**
- **Found during:** Task 1, verificação GREEN de `test_401_nao_faz_retry_e_cita_chave_invalida`
- **Issue:** a asserção `"tok-errado" not in str(_FakeAsyncClient._CHAMADAS)` falhava porque o registro de chamadas HTTP legitimamente contém o header enviado (é o que foi de fato transmitido) — o teste deveria checar a MENSAGEM DA EXCEÇÃO levantada, não o log da chamada de rede.
- **Fix:** trocado para `assert "tok-errado" not in str(exc.value)`, capturando a exceção via `pytest.raises(...) as exc`.
- **Files modified:** `server/tests/test_mydata_client.py`
- **Verification:** `pytest tests/test_mydata_client.py -q` → 15/15 passam
- **Committed in:** `3ebfbac` (Task 1 feat commit)

**2. [Rule 1 - Bug] Limiar de teste caía exatamente na borda do `degradado()`**
- **Found during:** Task 3, verificação GREEN de `test_degradado_passa_de_80_por_cento_do_teto_util`
- **Issue:** com `quota_dia=100` (teto útil 90), `90 * 0.8 = 72.0` exato; `int(72.0) == 72` bate no limiar via `>=` em vez de ficar estritamente abaixo dele — a comparação `False` esperada na verdade avaliava `True`.
- **Fix:** trocado `quase = int(90 * 0.8)` por `quase = int(limiar) - 1`, garantindo valor estritamente abaixo do limiar antes do débito que cruza os 80%.
- **Files modified:** `server/tests/test_mydata_budget.py`
- **Verification:** `pytest tests/test_mydata_budget.py -q` → 11/11 passam
- **Committed in:** `566eeed` (Task 3 feat commit)

**3. [Rule 1 - Bug/guardião] Literal `em_pregao` sobrando no docstring**
- **Found during:** Task 3, verificação dos critérios de aceite (`grep -c 'em_pregao' server/app/mydata_budget.py` deve dar 0)
- **Issue:** o docstring do topo do módulo citava `brapi_budget.em_pregao()` por nome ao explicar a ausência deliberada do gate de pregão — o próprio critério de aceite do plano proíbe essa string literal no arquivo (para impedir que alguém "copie o que falta" depois).
- **Fix:** reescrita a frase sem citar o nome da função.
- **Files modified:** `server/app/mydata_budget.py`
- **Verification:** `grep -c 'em_pregao' server/app/mydata_budget.py` → 0
- **Committed in:** `566eeed` (Task 3 feat commit)

**4. [Processo — não é Rule 1/2/3] Task 2 escrita em conjunto com Task 1 antes da separação de commits**
- **Found during:** Task 1
- **Issue:** ao implementar, escrevi `valida_fatia`/`get_history`/`RANGE_DIAS` (conteúdo da Task 2) no mesmo arquivo antes de commitar a Task 1 isoladamente. Isso teria misturado os dois escopos num commit só.
- **Fix:** revertido o arquivo para conter só o conteúdo da Task 1 antes do commit `3ebfbac`; o conteúdo da Task 2 foi reintroduzido depois, no ciclo RED (`253f42d`) → GREEN (`e8a7fc9`) próprio dela. O código final é idêntico ao que teria sido escrito task-a-task; só a ordem de escrita mudou, não o resultado.
- **Files modified:** `server/app/mydata_client.py`
- **Verification:** `git diff --stat 0d33b58..HEAD` mostra só os 4 arquivos do plano; `git log` mostra 6 commits (test/feat × 3 tasks) na ordem correta.
- **Committed in:** n/a (correção de processo antes de qualquer commit)

---

**Total deviations:** 3 auto-fixes de teste (Rule 1) + 1 nota de processo. Nenhum desvio de escopo, nenhuma dependência nova, nenhum arquivo fora dos 4 do plano.
**Impact on plan:** Todos os ajustes foram correções em asserções de teste ou em texto de comentário — a implementação de produção não mudou de forma nenhuma por causa deles.

## Issues Encountered
- O worktree não tem seu próprio `.venv` (não é rastreado pelo git); os testes foram rodados apontando para `/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python` (o mesmo venv que `scripts/test.sh` já resolve automaticamente via `git rev-parse --git-common-dir` ao detectar execução em worktree). Nenhum impacto no resultado — confirmado rodando `bash scripts/executar.sh --testes` a partir da raiz do worktree, que passou (1454 passed, 1 skipped no backend; todas as suítes web/tests/*.mjs OK).
- HEAD do worktree, ao ser criado, estava um commit ATRÁS do `base_commit` esperado pelo protocolo de execução (`0d33b58...`); corrigido com `git reset --hard` para o commit correto antes de qualquer edição, conforme instruído no `worktree_branch_check`. Working tree estava limpo no momento, sem perda de trabalho.

## Estado dos diffs não commitados de `b3_historical` (pré-condição do plano)

O plano assumia (na sua seção `<assumptions>`, escrita no momento do planejamento) que `server/app/b3_historical.py`, `server/tests/test_b3_historical.py` e `docs/adr/019-cotahist-diario-b3.md` estariam **untracked**, e que `agent.py`/`db.py`/`main.py`/`rbac.py` teriam diffs não commitados ligando esse módulo. **No estado deste worktree, isso já não é verdade**: esses arquivos estão COMMITADOS na branch base (commit `b3fdf02 feat(b3-historical): acervo diário oficial COTAHIST da B3 (ADR-019)`, presente no histórico antes do início deste plano). Não há nenhum diff pendente relacionado a `b3_historical` neste worktree — `git status --short` está limpo desde o início da execução.

Isto NÃO muda o resultado deste plano: nenhuma linha de `b3_historical.py`, `agent.py`, `db.py`, `main.py` ou `rbac.py` foi tocada (confirmado por `git diff --stat 0d33b58..HEAD`, que lista apenas os 4 arquivos novos deste plano). A decisão sobre o que fazer com `b3_historical.py` (aposentar via remoção, uma vez que `MydataProvider` cubra a fatia diária) continua sendo o checkpoint humano bloqueante do Plano 09-05 — só que agora sobre código já commitado, não sobre um diff pendente. Vale atualizar essa premissa no Plano 09-05 antes de abrir o checkpoint.

## User Setup Required

None neste plano — `MYDATA_TOKEN`/`MYDATA_URL` são consumidos apenas em runtime (nenhuma chamada real acontece até os Planos 09-02/09-03 ligarem o cliente em `candle_provider`/`options_api`). O `user_setup` do frontmatter do plano documenta a origem da chave de produção para quando essa fiação acontecer.

## Next Phase Readiness
- `mydata_client.get_history()` está pronto para ser chamado por um `MydataProvider` em `candle_provider.py` (Plano 09-02) com o mesmo contrato que `BrapiProvider`/`YahooProvider` já respeitam.
- `mydata_budget.pode_gastar()`/`debita()`/`aguarda_vaga()` estão prontos para o pacer do consumidor em lote do Plano 09-02.
- Nenhum bloqueio conhecido. O único ponto a revisitar no Plano 09-05: a premissa de "diffs não commitados de b3_historical" mudou para "código commitado" (ver seção acima) — ajustar o texto do checkpoint quando esse plano for escrito/executado.

---
*Phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa*
*Completed: 2026-08-27*
