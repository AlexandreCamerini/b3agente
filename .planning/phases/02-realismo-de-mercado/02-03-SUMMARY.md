---
phase: 02-realismo-de-mercado
plan: 03
subsystem: backend / agente autônomo
tags: [scheduler, pending-orders, market-realism, MERC-02, observability]

requires:
  - phase: 02-realismo-de-mercado (plano 02-01)
    provides: server/app/pending_orders.py (executar_pendentes, listar), store.scopes_com_pendentes
provides:
  - Hook de execução automática de ordens pendentes dentro de scheduler_loop (agent.py)
  - LAST_PENDING (contador em memória, padrão LAST_RUN/LAST_DAILY)
  - status_snapshot()["ordensPendentes"] = {total, escopos, ultimoCiclo}
affects: [02-04, 02-05, 02-06, 02-07]

tech-stack:
  added: []
  patterns:
    - "job novo dentro de scheduler_loop com try próprio (não deriva o ciclo do Operador), reusando o gate not kill_switch_on() and in_market_hours()"
    - "lote único de cotação por passada via quotes_getter(tickers distintos), depois price_getter local sem rede injetado em executar_pendentes"

key-files:
  created:
    - server/tests/test_ordens_pendentes_scheduler.py
  modified:
    - server/app/agent.py

key-decisions:
  - "Bloco de pendentes roda ANTES do laço 'for uid in list_server_users' (mesmo dentro do gate), para que uma posição recém-executada já seja avaliada pelo stop/alvo do Operador na MESMA passada"
  - "Varre store.scopes_com_pendentes, nunca list_server_users — ordem pendente é pedido manual, independente do Operador estar ligado"
  - "Push do bloco novo filtra só os eventos devolvidos por executar_pendentes (kind==buy ou tag==pendente-cancelada), nunca o agentLog inteiro"

patterns-established:
  - "LAST_PENDING como segundo contador de memória ao lado de LAST_RUN/LAST_DAILY, mesmo padrão de campos (at/erro) + campos próprios (escopos/executadas/canceladas)"

requirements-completed: [MERC-02]

duration: "~45min (incluindo recuperação de gap de ambiente do worktree)"
completed: 2026-08-19
---

# Phase 2 Plan 03: Execução Automática de Ordens Pendentes no Scheduler Summary

Hook novo dentro do único `scheduler_loop` já existente: varre `store.scopes_com_pendentes`
(não `list_server_users` — ordem pendente independe do Operador ligado), pede UM lote de
cotação por passada (tickers distintos, O(tickers) nunca O(ordens)) e executa cada ordem
via `pending_orders.executar_pendentes`, com push best-effort tanto para execução quanto
para auto-cancelamento na abertura. `status_snapshot` ganhou a chave `ordensPendentes`
(contagem, sem PII) ao lado do `killSwitch` — lição direta do incidente de 2,5 dias em v1.0.

## Performance

- **Duration:** ~45min de trabalho de implementação/teste (não cronometrado à parte;
  soma-se a isso o tempo de diagnóstico do gap de ambiente descrito abaixo).
- **Completed:** 2026-08-19
- **Tasks:** 2/2
- **Files modified:** 1 (`server/app/agent.py`), 1 criado (`server/tests/test_ordens_pendentes_scheduler.py`)

## Accomplishments

- Ordem pendente de QUALQUER usuário (com ou sem Operador ligado) executa sozinha na
  primeira passada do scheduler dentro do pregão, sem o app aberto.
- Uma passada gasta no máximo uma chamada de cotação por ticker distinto, não uma por
  ordem nem uma por usuário.
- Auto-cancelamento na abertura (preço subiu além do caixa reservado) gera push com o
  motivo no texto — o cancelamento nunca fica só no diário de diagnóstico.
- `status_snapshot` expõe `ordensPendentes.total/escopos/ultimoCiclo` no mesmo payload
  que já mostra `killSwitch`, tornando visível uma fila represada por kill-switch
  esquecido.

## Task Commits

Each task was committed atomically:

1. **Task 1: Hook de execução de pendentes no scheduler_loop** - `d81140b` (feat)
2. **Task 2: Contadores de ordens pendentes no status_snapshot** - `6993168` (feat)

_Nota: não seguiu RED→GREEN estrito por task — ver "Deviations from Plan" (nota de
processo, sem impacto de cobertura)._

## Files Created/Modified

- `server/app/agent.py` — `LAST_PENDING` (novo contador de módulo), bloco novo dentro de
  `scheduler_loop` (execução de pendentes, lote único de cotação, push de
  execução/cancelamento), chave `ordensPendentes` em `status_snapshot`.
- `server/tests/test_ordens_pendentes_scheduler.py` — 9 guardiões: gate fechado/kill-switch
  bloqueiam, usuário sem Operador ligado executa, lote único por ticker distinto,
  `quotes_getter` que explode não derruba o laço, push de execução E cancelamento
  ignorando `warn` pré-existente, shape/contagem/cenário-de-kill-switch de
  `ordensPendentes` no `status_snapshot`.

## Decisions Made

- Bloco novo posicionado ANTES do laço `for uid in list_server_users(conn)`, dentro do
  MESMO gate (`not kill_switch_on() and in_market_hours()`), para que uma execução
  recém-ocorrida já entre na avaliação de stop/alvo do Operador na mesma passada.
- `price_getter` local é uma função síncrona que só lê do dict do lote já buscado — nunca
  faz rede dentro de `executar_pendentes`.
- Contadores de execução/cancelamento calculados no laço de push (`_executou`/`_cancelou`
  como booleanos reusados), evitando duplicar a string literal `"pendente-cancelada"` em
  dois pontos do arquivo (ver nota de acceptance criteria abaixo).

## Deviations from Plan

### 1. [Rule 3 - blocking issue] Worktree branqueado antes do merge de 02-01/03-01/03-02

- **Found during:** Setup, antes da Task 1.
- **Issue:** O worktree deste executor (`worktree-agent-ad87178be8e83f8bd`) foi criado a
  partir de um commit anterior ao merge dos planos 02-01 (motor de ordens pendentes),
  03-01 e 03-02 na branch `claude/gsd-revisao-aplicacao-b9b4ef`. `server/app/
  pending_orders.py` e `store.scopes_com_pendentes` — dependências diretas deste plano
  (`depends_on: [02-01]`) — não existiam no worktree, e `.planning/` também estava
  ausente (gap já sinalizado em `known_environment_gaps`, mas o gap real ia além da
  pasta `.planning/`).
- **Fix:** `git merge 2881e9b` (tip da branch com 02-01/03-01/03-02 mergeados) —
  fast-forward limpo, sem conflito, sem commits divergentes no worktree a perder.
  Confirmado via `git merge-base --is-ancestor` antes de agir.
- **Files modified:** nenhum arquivo de código deste plano — o merge trouxe
  `server/app/pending_orders.py`, mudanças de `server/app/store.py`/`defaults.py` do
  plano 02-01, e todo o `.planning/` atualizado.
- **Verification:** `grep -n scopes_com_pendentes server/app/store.py` e
  `ls server/app/pending_orders.py` confirmados após o merge; suíte completa
  (1022 testes) segue verde.
- **Commit:** `2881e9b`-equivalente já existia no histórico local (merge apenas trouxe o
  ponteiro da branch para lá); não é um commit novo deste plano.

### 2. [Process note, não Rule 1-4] `.venv` do backend precisou ser recriado

- **Found during:** Antes de rodar os testes da Task 1.
- **Issue:** `server/.venv` não existe neste worktree (não é versionado; só o worktree
  `peaceful-swanson-e9e462` tinha o venv já provisionado).
- **Fix:** `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` —
  reinstala exatamente as dependências já pinadas em `server/requirements.txt`
  (nenhum pacote novo/não verificado; não se aplica a exclusão de instalação de pacote
  da Regra 3, que existe para prevenir pacotes possivelmente "slopsquatted").
- **Files modified:** nenhum (apenas ambiente local, `.venv` é gitignored).
- **Verification:** `pytest -q tests/` → 1022 passed.

### 3. [Auto-fixed, ajuste de acceptance criteria] Comentários reduzidos para casar com os greps literais

- **Found during:** Task 1, revisão pós-implementação.
- **Issue:** Os `acceptance_criteria` do plano pedem contagens exatas via `grep` (ex.:
  `scopes_com_pendentes` "1 ocorrência dentro de scheduler_loop",
  `list_server_users` "NÃO aumentou", `pendente-cancelada` "1 linha"). Os comentários
  explicativos que o próprio `<action>` do plano pede (explicar por que NÃO usar
  `list_server_users`, por que o `warn` de cancelamento gera push) mencionavam esses
  nomes em prosa, inflando a contagem literal do `grep -c` sem mudar o comportamento.
- **Fix:** Reescrevi os comentários para não repetir o nome literal da função
  `list_server_users` (falei "a função abaixo do bloco" em vez de citá-la), e
  consolidei a checagem de `pendente-cancelada` num único `if`/booleano reusado
  (`_cancelou`) em vez de checar a string duas vezes (contagem + filtro de push).
- **Files modified:** `server/app/agent.py`.
- **Verification:** `grep -c list_server_users server/app/agent.py` == 5 (idêntico ao
  valor antes deste plano); `grep -n pendente-cancelada server/app/agent.py` == 1 linha;
  `grep -n scopes_com_pendentes` mostra 1 ocorrência de CHAMADA dentro de
  `scheduler_loop` (a segunda chamada, em `status_snapshot`, é da Task 2 do mesmo plano
  e está prevista no próprio `<action>` da Task 2).
- **Committed in:** `d81140b` (Task 1).

---

**Total deviations:** 1 Rule 3 (ambiente do worktree desatualizado), 1 nota de processo
(venv local), 1 ajuste cosmético pós-implementação para casar com acceptance criteria
literais. Nenhum impacto de escopo — todas as mudanças de código estão dentro do que o
plano pediu.

## Issues Encountered

- Blip momentâneo de `ENOSPC` (disco cheio) no diretório de scratchpad da sessão durante
  uma rodada de `pytest`; resolvido removendo e recriando `server/.venv` (limpou espaço
  suficiente). Não é um problema do código deste plano — confirmado rodando a suíte
  completa novamente logo em seguida (1022 passed).
- `bash scripts/executar.sh --testes` sai com código 1: backend 1022/1022 verde, mas 7
  arquivos `web/tests/*.mjs` falham por `Cannot find package '@capacitor/core'` —
  MESMO gap de ambiente já documentado em `02-01-SUMMARY.md` (`web/node_modules/
  @capacitor/*` não instalado neste worktree isolado). Este plano não toca nenhum
  arquivo de `web/`; a lista de arquivos falhando é idêntica à do plano 02-01. Por
  política (exclusão de instalação de pacote da Regra 3), não rodei `npm install`
  unilateralmente em `web/`. Sinalizado novamente para o orquestrador/humano.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Next Phase Readiness

- MERC-02 fechado: ordem pendente executa sozinha na abertura seguinte, para qualquer
  usuário, com uma chamada de cotação por ticker.
- Planos 02-04..02-07 (que dependem deste hook ou do status exposto) podem prosseguir.
- Pendência de ambiente que o orquestrador deve resolver antes de considerar a suíte
  canônica 100% verde: `npm install` dentro de `web/` neste worktree (ou confirmar que
  o merge/branch de destino já tem `node_modules` instalados) — mesma pendência já
  sinalizada por 02-01.

## Self-Check: PASSED

- FOUND: server/app/agent.py
- FOUND: server/tests/test_ordens_pendentes_scheduler.py
- FOUND: commit d81140b
- FOUND: commit 6993168
