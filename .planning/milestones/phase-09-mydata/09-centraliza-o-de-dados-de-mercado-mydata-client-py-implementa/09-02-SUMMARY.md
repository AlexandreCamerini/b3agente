---
phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa
plan: 02
subsystem: api
tags: [candle-provider, mydata, fallback-chain, routing, tdd]

# Dependency graph
requires:
  - "server/app/mydata_client.py + server/app/mydata_budget.py (Plano 09-01): get_history/valida_fatia, pode_gastar/debita/snapshot"
provides:
  - "server/app/candle_provider.py: MydataProvider registrado em _PROVEDORES; cadeia de fallback de N saltos (fallback_names()/get_fallbacks()/set_fallbacks()); roteador get_history() percorrendo [primario, *fallbacks] com gate por elo (_gate/_debita); snapshot() com 'fallbacks' e 'orcamentoMydata'"
  - "server/tests/test_mydata_provider.py: 21 guardiões cobrindo registro, cadeia de fallback e roteador (dois saltos, intraday nunca toca mydata, gate de cota/plano por elo, comportamento pré-existente intacto)"
affects: [09-04-medicao-rate-limit, 09-05-checkpoint-b3-historical, 09-06-checkpoint-virada-producao]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate por elo com dois tipos de recusa (dura=PLANO/FATIA relança exceção no último elo; mole=ORÇAMENTO/COTA serve sem debitar no último elo) — generaliza para N elos a regra de 1 salto que já existia para brapi"
    - "Cadeia de provedores memoizada por lista de nomes (get_fallbacks compara nomes instanciados com fallback_names() a cada chamada), preservando a injeção de teste single-provider (set_fallback) e multi-provider (set_fallbacks)"

key-files:
  created:
    - server/tests/test_mydata_provider.py
  modified:
    - server/app/candle_provider.py
    - server/tests/test_candle_provider.py

key-decisions:
  - "_gate() devolve (motivo, erro) em vez do Optional[str] literal do plano — necessário para distinguir recusa DURA (PLANO/FATIA, relança a exceção original no último elo) de recusa MOLE (ORÇAMENTO/COTA, serve sem debitar no último elo). Achado por Rule 1 durante a Task 2: o guardião existente test_sem_backup_orcamento_nao_vira_sem_dado (que a acceptance criteria exige continuar verde SEM edição) só passa com essa distinção — sem ela, orçamento esgotado no primário sem backup vira RuntimeError em vez de servir mesmo assim"
  - "fallback_name()/get_fallback() continuam sendo wrappers PUROS de env (primeiro nome/provedor de fallback_names()/get_fallbacks()), não refletem cadeia injetada via set_fallbacks() quando chamados isoladamente — mesmo contrato que o código original já tinha (nunca refletiam o provedor injetado via set_fallback() antes desta Fase)"
  - "Configuração de produção INTOCADA: B3_CANDLE_PROVIDER default continua 'yahoo' (confirmado por teste + grep); a virada para mydata é decisão do checkpoint do Plano 09-06"

requirements-completed: []

# Metrics
duration: ~30min
completed: 2026-08-27
---

# Phase 9 Plan 02: Roteador de candles com MydataProvider + cadeia mydata→brapi→Yahoo Summary

**`MydataProvider` registrado em `candle_provider._PROVEDORES` e o fallback de um salto só virou cadeia de N elos (`fallback_names()`/`get_fallbacks()`), com o roteador `get_history()` reescrito para aplicar gate de fatia/plano/cota por elo — mydata→brapi→Yahoo degrada na mesma requisição, intraday nunca toca o mydata, e nenhum call site de candle mudou.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-08-27T22:19:00Z (aprox., logo após o merge da wave 1)
- **Completed:** 2026-08-27T22:49:00Z
- **Tasks:** 2/2 completos
- **Files modified:** 3 (1 novo, 2 editados)

## Accomplishments
- `MydataProvider` (nome `"mydata"`) delega a `mydata_client.get_history` — mesma forma de duas linhas de `BrapiProvider`, cobrindo só a fatia diária (ADR-001 intocada, intraday continua do Yahoo).
- `_fallback` singular virou `_fallbacks` (lista): `fallback_names()` calcula a cadeia por env (`B3_CANDLE_FALLBACK`) ou default por primário (`mydata`→`["brapi","yahoo"]`, `brapi`→`["yahoo"]`, `yahoo`→`[]`), filtrando o próprio primário e nomes desconhecidos, sem levantar.
- `set_fallbacks(ps)` novo, para os testes injetarem a cadeia inteira; `set_fallback(p)` (singular) continua funcionando para injeção de um provedor só.
- Roteador `get_history()` reescrito como passada única sobre `[get_provider(), *get_fallbacks()]`: `_gate()` decide sem rede/sem debitar se o elo serve agora, `_debita()` debita o orçamento certo (brapi→fatia `delta`, mydata→cota combinada) imediatamente antes da chamada instrumentada (`_chama`, que continua sendo a única fronteira de instrumentação — não migrou para dentro de nenhum provedor).
- `snapshot()` ganha `"fallbacks"` (lista, aditivo) e `"orcamentoMydata"` (espelhando `"orcamentoBrapi"`, presente quando mydata está no primário ou em qualquer elo do fallback) — torna o consumo do mydata observável em `/api/obs/usage` sem tocar em `main.py`.
- 21 guardiões novos em `server/tests/test_mydata_provider.py` cobrindo: registro de 3 provedores, cadeia de fallback (defaults por primário, override por env, filtro de nome inválido/próprio primário, injeção single/multi), e o roteador (mydata sadio, falha cai na brapi sem tocar Yahoo, dois saltos mydata+brapi→Yahoo, três falhas relançam o último erro, série vazia tenta o próximo, intraday nunca toca o mydata, gate de cota do mydata pula sem tocar rede, brapi como FALLBACK pulada sem rede por plano/orçamento, comportamento pré-existente do primário brapi intacto).

## Task Commits

Cada task seguiu RED→GREEN (TDD):

1. **Task 1: MydataProvider no registro + cadeia de fallback de N saltos**
   - `dfe9018` (test) — 10 guardiões offline, RED confirmado (`AttributeError: set_fallbacks`)
   - `e496af2` (feat) — implementação, GREEN (39/39 em `test_mydata_provider.py` + `test_candle_provider.py`)
2. **Task 2: roteador com gate por provedor e degradação mydata→brapi→Yahoo**
   - `e27221c` (test) — 11 guardiões adicionais, RED confirmado (8 falhas: router ainda no salto único antigo)
   - `9ffb313` (feat) — implementação, GREEN (70/70 em `test_mydata_provider.py` + `test_candle_provider.py` + `test_candle_cache.py`)

## Files Created/Modified
- `server/app/candle_provider.py` — `MydataProvider`, cadeia de fallback (`fallback_names`/`get_fallbacks`/`set_fallbacks`), `_gate`/`_debita`, roteador `get_history()` reescrito, `snapshot()` com `fallbacks`/`orcamentoMydata`
- `server/tests/test_mydata_provider.py` (novo, 312 linhas) — 21 guardiões offline
- `server/tests/test_candle_provider.py` — `_limpa()` ganha `cp.set_fallbacks([])` (única linha editada, conforme acceptance criteria)

## Decisions Made
- **`_gate()` com retorno `(motivo, erro)` em vez do `Optional[str]` literal da `<action>` do plano** — a Task 2 especificava `_gate` devolvendo só uma string de motivo. Ao implementar literalmente, o guardião pré-existente `test_sem_backup_orcamento_nao_vira_sem_dado` (que a acceptance criteria exige continuar verde SEM edição) quebrava: com primário `brapi` sem fallback e sem orçamento, o código original **serve mesmo assim, sem debitar** (proteção de cota não pode virar "sem dado" quando não há alternativa); mas para `ForaDoPlano` sem fallback, o código original **relança a exceção**, não serve. Essas duas recusas têm efeito diferente no último elo da cadeia — resolvido com `_gate` devolvendo também a exceção original (`erro`) quando a recusa é de PLANO/FATIA, para o roteador relançar especificamente nesse caso, e servir sem debitar nos casos de ORÇAMENTO/COTA. Rule 1 (bug encontrado ao rodar a suíte, não ao planejar).
- **Estimativa de chamadas ao mydata por carga cheia (`rng="2y"`) e delta (`rng="1mo"`)**: com `LIMITE_MAX=2000` registros/página em `mydata_client._paginar`, e `RANGE_DIAS["2y"]=790` dias corridos (≈564 pregões úteis) / `RANGE_DIAS["1mo"]=45` dias corridos (≈32 pregões úteis), **ambos os ranges cabem em UMA página — 1 requisição HTTP ao mydata por chamada de `get_history()`**, tanto para carga cheia quanto para delta. Só o range `"max"` (3700 dias corridos, ≈2643 pregões) ultrapassaria o teto de uma página e paginaria (2 requisições, dentro do teto `PAGINAS_MAX=8`). Número de partida para o Plano 09-04 dimensionar quantos tickers/dia cabem nos 60/min·2.000/dia de cota.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `_gate()` precisou distinguir recusa dura (PLANO/FATIA) de recusa mole (ORÇAMENTO/COTA)**
- **Found during:** Task 2, ao rodar `test_sem_backup_orcamento_nao_vira_sem_dado` (guardião pré-existente, não editado) contra a primeira implementação literal de `_gate` retornando só `Optional[str]`
- **Issue:** com `_gate` retornando só motivo, o roteador não tinha como saber se o último elo recusado por ORÇAMENTO deveria servir mesmo assim (comportamento documentado: "proteção de cota não pode virar 'sem dado' quando não há alternativa") ou se um último elo recusado por PLANO deveria relançar a exceção original (comportamento documentado: "falha alto"). A primeira versão levantava `RuntimeError` genérico nos dois casos, quebrando o guardião de orçamento
- **Fix:** `_gate(p, rng, interval)` passou a devolver `(motivo, erro)` — `erro` só preenchido para recusa de PLANO/FATIA (a exceção original `brapi.ForaDoPlano`/`mydata_client.MydataForaDaFatia`). O roteador relança `erro` quando o último elo é recusa dura, e segue sem debitar quando é recusa mole (`_MOTIVOS_ORCAMENTO = {"sem orçamento", "sem cota"}`)
- **Files modified:** `server/app/candle_provider.py`
- **Verification:** `pytest tests/test_mydata_provider.py tests/test_candle_provider.py tests/test_candle_cache.py -q` → 70/70 passam, incluindo os 15 guardiões pré-existentes de roteamento sem nenhuma edição
- **Committed in:** `9ffb313` (Task 2 feat commit)

---

**Total deviations:** 1 auto-fix de comportamento (Rule 1), descoberto pela suíte de teste existente, não pela minha própria suíte nova. Nenhum desvio de escopo, nenhuma dependência nova, nenhum arquivo fora dos 3 do plano.
**Impact on plan:** A assinatura interna de `_gate` (tupla em vez de string) diverge do texto literal da `<action>`, mas o contrato PÚBLICO do plano (comportamento observável, `grep -c 'def _gate'` == 1, testes de aceite) é cumprido integralmente.

## Issues Encountered
- HEAD do worktree, ao ser criado, estava um commit ATRÁS do `base_commit` esperado pelo protocolo de execução (mesma situação relatada no 09-01-SUMMARY.md — o worktree clona de `origin/main`, não do HEAD local mais recente); corrigido com `git reset --hard` para o commit correto (`41105d2`) antes de qualquer edição, working tree limpo, sem perda de trabalho.

## User Setup Required

None neste plano. `MYDATA_TOKEN`/`MYDATA_URL` continuam sendo consumidos só em runtime quando `B3_CANDLE_PROVIDER=mydata` for de fato configurado — e isso NÃO acontece neste plano (default de produção continua `yahoo`, confirmado por teste e grep).

## Next Phase Readiness
- `candle_provider.get_history()` já suporta a cadeia `mydata→brapi→Yahoo` completa, pronta para o Plano 09-04 medir rate-limit real (mesmo com `B3_CANDLE_PROVIDER` ainda apontando para `yahoo` em produção) e para o checkpoint do Plano 09-06 decidir a virada.
- `snapshot()["orcamentoMydata"]` já aparece em `/api/obs/usage` assim que qualquer ambiente setar `B3_CANDLE_PROVIDER=mydata` ou `B3_CANDLE_FALLBACK` incluindo `mydata` — nenhuma mudança em `main.py` necessária.
- Estimativa de 1 requisição/chamada ao mydata (tanto para `2y` quanto `1mo`) está pronta para o Plano 09-04 dimensionar quantos tickers cabem na janela de 60/min·2.000/dia.
- Nenhum bloqueio conhecido.

## Self-Check: PASSED

- FOUND: server/app/candle_provider.py
- FOUND: server/tests/test_mydata_provider.py
- FOUND: server/tests/test_candle_provider.py
- FOUND: .planning/phases/09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa/09-02-SUMMARY.md
- FOUND commits: dfe9018, e496af2, e27221c, 9ffb313 (verified via `git log --oneline -6`)

---
*Phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa*
*Completed: 2026-08-27*
