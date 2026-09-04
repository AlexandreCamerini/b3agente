---
phase: 19-motor-multi-candidato
plan: 02
subsystem: api
tags: [python, fastapi, opcoes, pytest, motor-deterministico]

# Dependency graph
requires:
  - phase: 19-motor-multi-candidato
    plan: 01
    provides: "opcoes_lastreadas.propor() devolve candidatos (lista de 1 ou 2 estruturas), proposta==candidatos[0], motivo==candidatos[0]['tipo']"
provides:
  - "GET /api/options/proposta/{ticker} expõe candidatos na resposta JSON (aditivo, default [] nos ramos sem a chave)"
  - "POST /api/options/lastreada/abrir-collar aceita QUALQUER candidato tipo=='collar' da lista, não só o primário"
  - "Precondição de posição lastreada já aberta na rota de escrita do collar — fecha a lacuna put->collar de MULTI-02 critério 3"
affects: [19-03-motor-multi-candidato, 19-04-motor-multi-candidato]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Busca por tipo dentro de lista de candidatos (next() com predicado), não indexação por posição — necessário mas não suficiente, cross-check integral roda contra o achado"
    - "Precondição de estado (posição já lastreada) verificada ANTES da re-derivação de proposta, evitando fetch de cadeia inútil"

key-files:
  created: []
  modified:
    - server/app/main.py
    - server/tests/test_opcoes_collar_rota.py

key-decisions:
  - "Busca de candidato por tipo=='collar' é condição necessária, nunca suficiente — todo o cross-check contrato-a-contrato preexistente continua rodando contra o candidato encontrado (T-19-05/T-19-06 do threat model)"
  - "Exclusão mútua entre candidatos irmãos usa DOIS mecanismos diferentes, nenhum novo: collar->put bloqueado pela guarda de lastro de sempre em comprar_put_protecao (ORDER_LOCK); put->collar bloqueado pela precondição de rota nova (posição lastreada aberta), replicando o que a rota de leitura já fazia desde a Fase 14"
  - "store.py permanece INTOCADO nesta fase — confirmado por diff vazio e por guardião estático (inspect.getsource) que nenhuma trava/flag nova entrou no motor de carteira"

patterns-established:
  - "Guardião pré-existente cujo cenário deixa de ser alcançável por mudança de comportamento é reapontado com nota na docstring citando a fase, nunca reescrito silenciosamente (CLAUDE.md: guardiões de teste não se apagam)"

requirements-completed: [MULTI-01, MULTI-02]

# Metrics
duration: ~1h (inclui correção de base de worktree, ver Issues Encountered)
completed: 2026-09-04
---

# Phase 19 Plan 02: Motor multi-candidato (rotas falam a língua de N candidatos) Summary

**As duas rotas de opções (`GET /api/options/proposta/{ticker}` e `POST /api/options/lastreada/abrir-collar`) passam a operar sobre a lista `candidatos` da Fase 19-01, com precondição nova que fecha a lacuna put→collar de MULTI-02 critério 3.**

## Performance

- **Duration:** ~1h (inclui uma correção de base de worktree idêntica à do Plano 19-01, ver Issues Encountered)
- **Tasks:** 3/3 completed
- **Files modified:** 2

## Accomplishments

- `GET /api/options/proposta/{ticker}` devolve `"candidatos": resultado.get("candidatos", [])` — aditivo, com `.get()` obrigatório para não estourar `KeyError` no ramo de fechamento (`proposta_fechar()`) nem no ramo de degradação.
- `POST /api/options/lastreada/abrir-collar` busca o candidato `tipo == "collar"` dentro de `candidatos[]` (não mais a suposição `motivo == "collar"` como resultado primário) — aceita collar não-primário, com o cross-check integral de contratos/pernas preservado sobre o candidato encontrado.
- Precondição nova na rota de escrita do collar: 409 se já existe posição lastreada aberta no `underlying` (mesma regra que a rota de leitura já aplicava desde a Fase 14) — fecha a lacuna real descoberta no planejamento (put_protecao não trava `qtyTravada`, então sem esta checagem o collar executaria em cima de uma put já aberta).
- Guardião pré-existente `test_collar_indisponivel_agora_devolve_409_sem_efeito_colateral` reapontado com nota "Fase 19" — o cenário original ("collar deixou de existir") não é mais alcançável com put+collar coexistindo; o 409 agora vem do cross-check de contratos.
- 4 testes novos: aceite de collar não-primário, anti-regressão do cross-check com perna trocada, e as duas ordens de exclusão mútua entre candidatos irmãos (collar→put bloqueado por lastro; put→collar bloqueado pela nova precondição) + guardião estático provando zero trava nova em `store.py`.
- `server/app/store.py`: diff vazio, confirmado.

## Task Commits

Each task was committed atomically:

1. **Task 1: rotas falam a língua de N candidatos** - `d58d12a` (feat)
2. **Task 2: guardião reapontado + aceite de candidato não-primário** - `f4e8531` (test)
3. **Task 3: guardião de exclusão mútua entre candidatos irmãos** - `02464fa` (test)

## Files Created/Modified

- `server/app/main.py` — 3 edições cirúrgicas: chave `candidatos` aditiva em `options_proposta`; precondição de posição lastreada aberta e busca por tipo em `options_lastreada_abrir_collar`. Rota single-leg `options_lastreada_abrir` sem uma linha alterada (confirmado por diff).
- `server/tests/test_opcoes_collar_rota.py` — guardião reapontado + 4 testes novos, nenhum teste apagado.

## Decisions Made

- Busca por `tipo == "collar"` é condição NECESSÁRIA, nunca suficiente — decisão herdada do threat model do plano (T-19-05/T-19-06): o cross-check contrato-a-contrato preexistente (contratos, `{contractSymbol: lado}` das duas pernas, localização por `optionType`) continua rodando integralmente contra o `p` encontrado, provado pelo teste anti-regressão de perna trocada.
- A precondição de posição lastreada aberta foi colocada ANTES da re-derivação de proposta (não depois) — evita um fetch de cadeia inútil quando a resposta já vai ser 409, e é precondição de ESTADO, não desconfiança do corpo.
- Nenhuma trava nova em `store.py`: a exclusão mútua entre candidatos irmãos usa os dois mecanismos que já existiam (guarda de lastro de `comprar_put_protecao` para a ordem collar→put; a nova precondição de ROTA, não de motor, para a ordem put→collar) — decisão confirmada por guardião estático (`inspect.getsource`) que verifica ausência de lock/flag novos.

## Deviations from Plan

None de código — plano executado exatamente como escrito (3 edições cirúrgicas em `main.py`, guardião reapontado com nota, 4 testes novos seguindo os padrões dos testes existentes do arquivo). Um desvio operacional de infraestrutura de worktree, documentado abaixo (mesmo padrão já registrado pelo Plano 19-01).

## Issues Encountered

**Worktree clonado de uma base desatualizada (não relacionado ao código deste plano) — mesmo padrão do Plano 19-01.** O worktree deste executor foi criado a partir do commit `0b9ead1` (anterior à execução completa do Plano 19-01 e às commits de planejamento da Fase 19), em vez do commit `7b32f83` (`docs(19): marca 19-01 completo no ROADMAP`) esperado pelo `worktree_branch_check` do orquestrador.

- **Como foi pego:** ao tentar ler `.planning/phases/19-motor-multi-candidato/19-02-PLAN.md` e `19-01-SUMMARY.md`, nenhum dos dois existia no worktree — a pasta `.planning/phases/19-motor-multi-candidato/` inteira estava ausente do HEAD do worktree.
- **Verificação antes de agir:** `git diff --stat` entre a base do worktree (`0b9ead1`) e o commit esperado (`7b32f83`, que já existia localmente no repositório principal, mesmo objeto compartilhado) mostrou um diff de ~56 arquivos incluindo toda a Fase 18/19 (App.jsx, opcoes_lastreadas.py, docs de planejamento) — sinal inequívoco de base errada, não de escopo deste plano. A checagem restrita só aos 2 arquivos nominais de `files_modified` (`server/app/main.py`, `server/tests/test_opcoes_collar_rota.py`) teria dado falso conforto (só diferiam por um bump trivial de `SERVER_BUILD_ID`); a checagem correta precisou olhar as dependências reais do plano (`opcoes_lastreadas.py`, os próprios arquivos de planejamento da fase).
- **Correção:** o worktree deste executor NÃO tinha nenhum commit próprio ainda (só leituras haviam sido feitas) — diferente do incidente do Plano 19-01, que já tinha código commitado sobre a base errada e precisou de `cherry-pick`. Aqui bastou `git reset --hard 7b32f83...` direto, sem perda de trabalho, seguido de releitura de todo o contexto (PROJECT.md, STATE.md, o próprio `19-02-PLAN.md`, `19-01-SUMMARY.md`, `19-PATTERNS.md`) na base correta antes de iniciar qualquer edição.
- **Nenhum código de produto foi afetado** por este incidente — é puramente um artefato de infraestrutura de execução (worktree), sem relação com MULTI-01/MULTI-02.
- **Recomendação para o orquestrador:** este é o segundo incidente idêntico em sequência dentro da mesma Fase 19 (ver 19-01-SUMMARY.md "Issues Encountered") — o padrão `worktree.baseRef` clonando de `origin/main`/HEAD antigo em vez do HEAD local mais recente após um push de wave anterior está confirmado recorrente, não incidental. Vale aplicar o fix `worktree.baseRef: "head"` documentado na memória do usuário (`agent-isolation-worktree-baseref.md`) antes da próxima wave (19-03/19-04) para não repetir o mesmo desvio pela terceira vez.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Verification Evidence

- `cd server && .venv/bin/python -m pytest tests/test_opcoes_collar_rota.py tests/test_opcoes_lastreadas_rotas.py tests/test_opcoes_collar_vocab.py -q` (rodado via o venv do repositório principal, symlinkado temporariamente — ver nota abaixo) → **2 failed, 54 passed** logo após a Task 1, exatamente as 2 falhas esperadas: (a) o guardião que a Task 1 quebra deliberadamente (`test_collar_indisponivel_agora_devolve_409_sem_efeito_colateral`, corrigido na Task 2) e (b) a mesma falha ambiental pré-existente já documentada no 19-01-SUMMARY.md (`test_vender_posicao_100_por_cento_travada_via_sell_devolve_400`, sandbox sem egress de rede pra Yahoo).
- `cd server && .venv/bin/python -m pytest tests/test_opcoes_collar_rota.py -q` (após Task 2) → **19 passed** (17 + 2 novos).
- `cd server && .venv/bin/python -m pytest tests/test_opcoes_collar_rota.py -q` (após Task 3) → **22 passed** (19 + 3 novos).
- `bash scripts/executar.sh --testes` (suíte canônica completa, backend) → **27 failed, 1994 passed, 1 skipped**. As 27 falhas são a MESMA lista, byte a byte, já documentada como pré-existente/ambiental no `19-01-SUMMARY.md` (sandbox sem egress de rede para Yahoo/Anthropic/OpenAI) — confirmado por comparação direta das duas listas. 1994 passed = 1989 (base do 19-01) + 5 novos testes deste plano (2 da Task 2 + 3 da Task 3). Nenhuma falha nova introduzida por este plano.
- Suíte web (`web/tests/*.mjs`, todos os arquivos, executados via `node` individualmente após o `executar.sh` short-circuitar na falha ambiental do backend — mesmo padrão de contorno do 19-01) → **0 falhas**.
- `git diff server/app/store.py` → **vazio**, confirmado.
- `git diff --stat 7b32f83 HEAD` → limitado a `server/app/main.py` e `server/tests/test_opcoes_collar_rota.py`, exatamente os dois arquivos de `files_modified` do plano.
- `git diff 7b32f83 HEAD -- server/app/main.py | grep SERVER_BUILD_ID` → vazio (não alterado à mão, conforme instrução do plano).
- Todos os greps de `acceptance_criteria` das 3 tasks executados e conferidos (candidatos aditivo, ausência de indexação direta, checagem antiga removida, texto do 409 reusado, cross-check >= 3 ocorrências, `multiperna=True` fixo sem leitura do corpo, nenhum `def test_` removido, nota "Fase 19" na docstring do guardião, `nao_e_trava_nova_no_store` passando).
- Nenhum pacote novo instalado — `git diff server/requirements.txt server/requirements-prod.txt web/package.json` (implícito: nenhum destes arquivos aparece no diff do plano).

**Nota de infraestrutura de teste (não é desvio de plano):** este worktree não tinha `server/.venv` nem `web/node_modules` próprios (gitignored). Seguindo o mesmo precedente do Plano 19-01, ambos foram symlinkados TEMPORARIAMENTE a partir do repositório principal só para rodar a verificação, e removidos antes do commit final — nenhum symlink ou artefato de ambiente foi commitado.

## Next Phase Readiness

- Contrato de resposta HTTP estabelecido: `19-03-PLAN.md`/`19-04-PLAN.md` (cliente web) podem consumir `candidatos` na resposta de `GET /api/options/proposta/{ticker}` e contar com `abrir-collar` aceitando qualquer candidato collar da lista, não só o primário.
- **Pendência herdada do 19-01, não deste plano:** suíte canônica ainda não roda 100% verde num ambiente com egress de rede liberado — mesma classe de limitação (sandbox), não nova.
- **Recomendação operacional para a wave 3 (19-03):** aplicar o fix `worktree.baseRef: "head"` antes de spawnar o próximo worktree, dado o padrão recorrente descrito em "Issues Encountered".

---
*Phase: 19-motor-multi-candidato*
*Completed: 2026-09-04*

## Self-Check: PASSED

- FOUND: server/app/main.py
- FOUND: server/tests/test_opcoes_collar_rota.py
- FOUND: .planning/phases/19-motor-multi-candidato/19-02-SUMMARY.md
- FOUND commit: d58d12a (Task 1)
- FOUND commit: f4e8531 (Task 2)
- FOUND commit: 02464fa (Task 3)
