---
phase: 17-fluxo-de-aceite
plan: 02
subsystem: api
tags: [fastapi, opcoes, proveniencia-de-dado, tdd]

# Dependency graph
requires:
  - phase: 14-opcoes-lastreadas
    provides: "GET /api/options/proposta/{ticker} (proposta determinística de venda coberta/put de proteção/collar)"
  - phase: 16-biblioteca-de-estruturas
    provides: "parâmetro multiperna, campos estrutura/caixa/precoObjeto na proposta"
provides:
  - "Campos `source` e `at` na resposta de GET /api/options/proposta/{ticker}, em TODOS os caminhos (proposta nova, fechamento, sem_lastro, degradado)"
  - "Guardião por inspect.getsource proibindo `source` chumbado na rota"
  - "Guardião parametrizado garantindo `at` bem formado em todos os caminhos de resposta"
affects: [17-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "source/at na resposta HTTP mirroring a convenção já usada por /api/quotes (at) e /api/technicals (source) — nenhum vocabulário novo"
    - "source nunca resetado no except: se a cadeia já foi lida, a fonte é conhecida e continua honesta mesmo com pipeline quebrado"

key-files:
  created: []
  modified:
    - server/app/main.py (options_proposta: captura source nos dois ramos, acrescenta source/at ao dict de retorno)
    - server/tests/test_opcoes_lastreadas_rotas.py (7 testes novos: 5 de comportamento + 2 guardiões)

key-decisions:
  - "source é capturado logo após cada chamada a options_provider.get_options() (ramo de fechamento e ramo de proposta nova), nunca um literal escrito na rota — evita repetir o defeito C-11/C-30 do REPORT-01"
  - "source NUNCA é resetado no except Exception: — se a cadeia já foi lida antes da exceção, a fonte é conhecida e declará-la é mais honesto que apagá-la (regra 'null nunca 0.0' aplicada a texto: None só quando genuinamente desconhecido)"
  - "at é o instante da montagem DA RESPOSTA (now_str(), mesma função de /api/quotes e technicals) — não o horário do pregão do dado; comentário no código evita essa leitura errada"

patterns-established:
  - "Guardião por inspect.getsource() para proibir literais de provedor hardcoded numa rota — reusável em qualquer rota futura que precise declarar proveniência"

requirements-completed: [FLOW-04]

# Metrics
duration: 25min
completed: 2026-09-02
---

# Phase 17 Plan 02: Fonte e horário na proposta de opções (FLOW-04) Summary

**GET /api/options/proposta/{ticker} agora declara `source` (da cadeia realmente usada, nunca literal) e `at` (now_str()) em todos os quatro caminhos de resposta — proposta completa, fechamento, ausência sem_lastro e degradado.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-09-02T23:00:00Z (aprox.)
- **Completed:** 2026-09-02T23:25:00Z (aprox.)
- **Tasks:** 2/2 completos
- **Files modified:** 2

## Accomplishments
- `options_proposta` (main.py) captura `source` da cadeia real (`chain.get("source")`/`chain_pos.get("source")`) nos dois ramos (fechamento e proposta nova) e nunca o reseta na exceção.
- Dict de retorno ganha `"source": source, "at": now_str()` — acréscimo puramente aditivo, nenhum campo pré-existente mudou de nome/tipo/valor.
- 7 testes novos: 5 cobrindo os caminhos de resposta (bem-sucedida, fechamento, sem_lastro, degradado, exceção no pipeline) + 2 guardiões (fonte nunca literal via `inspect.getsource`; `at` sempre bem formado, parametrizado sobre 3 cenários).

## Task Commits

Cada task foi commitada atomicamente (TDD: RED → GREEN na Task 1):

1. **Task 1 (RED): testes falhando source/at** - `53eca92` (test)
2. **Task 1 (GREEN): source e at na rota** - `3f47379` (feat)
3. **Task 2: guardiões (fonte nunca literal, at nunca falta)** - `8195edc` (test)

**Plan metadata:** commit final pendente (SUMMARY.md, feito pelo orquestrador após a wave)

_TDD: Task 1 seguiu RED→GREEN (`53eca92`→`3f47379`); Task 2 é guardião puro (sem GREEN separado, a implementação já existia)._

## Files Created/Modified
- `server/app/main.py` — `options_proposta`: variável `source` inicializada `None`, capturada nos dois ramos do `try`, nunca resetada no `except`, acrescentada ao dict de retorno junto de `at`.
- `server/tests/test_opcoes_lastreadas_rotas.py` — 7 testes novos (imports `inspect`/`re` acrescentados); nenhum teste existente alterado ou removido.

## Decisions Made
- `source` só pode vir de `chain.get("source")`/`chain_pos.get("source")` — nunca um literal na rota. Guardião por `inspect.getsource` fecha essa porta permanentemente (o repositório já teve esse defeito exato, C-11/C-30 do REPORT-01).
- `source` sobrevive à exceção (não é resetado no `except Exception:`) — decisão explícita do plano, implementada literalmente: "se a cadeia chegou a ser lida, a fonte é conhecida e declará-la é mais honesto que apagá-la".
- `at` reusa `now_str()` — mesma função e mesma semântica de `/api/quotes`/technicals (instante da resposta, não do pregão). Nenhum vocabulário novo criado, conforme o objective do plano.

## Deviations from Plan

None - plan executado exatamente como escrito. As duas tasks TDD seguiram RED→GREEN conforme especificado; os 7 testes batem com o `<behavior>`/`<action>` do plano.

## Issues Encountered

**Falhas pré-existentes de rede/sandbox, fora de escopo.** Ao rodar a suíte completa (`bash scripts/test.sh`, 1947 passed / 27 failed) e o arquivo do plano isoladamente (27 passed / 1 failed), a ÚNICA falha dentro de `test_opcoes_lastreadas_rotas.py` foi `test_vender_posicao_100_por_cento_travada_via_sell_devolve_400` — um teste PRÉ-EXISTENTE (não tocado por este plano) que chama `POST /api/sell`, não `options_proposta`. Falha com 502 em vez de 400 porque `candle_provider.get_quote` tenta rede real (Yahoo) e o sandbox bloqueia (`[Errno 1] Operation not permitted`). Confirmado que as outras 26 falhas da suíte completa compartilham a mesma causa raiz (chamadas HTTP externas reais: Yahoo, Anthropic/OpenAI, benchmark IBOV) — nenhuma toca `options_proposta`. Documentado em `deferred-items.md` (não corrigido, fora do escopo Rule 1/2/3 — falha em arquivo/rota não tocada por este plano). Recomendação registrada: rodar `bash scripts/executar.sh --testes` fora do sandbox antes do merge da fase.

**Suíte web não executada neste worktree.** `web/node_modules` ausente no worktree paralelo; plano é backend-only (`git status --porcelain web/` vazio, confirmado). Documentado em `deferred-items.md`.

## Verification Executed

- `cd server && .venv/bin/python -m pytest tests/test_opcoes_lastreadas_rotas.py -q` → **27 passed, 1 failed** (falha pré-existente/ambiental, ver acima).
- `cd server && .venv/bin/python -m pytest tests/test_opcoes_lastreadas_rotas.py -k "recusa" -q` → **2 passed** (trava 400 do Plano 16-04 intacta).
- `bash scripts/test.sh` (suíte backend completa) → **1947 passed, 27 failed** (todas as 27 são a mesma classe de falha de rede/sandbox, confirmado por inspeção individual).
- `grep -c '"at": now_str()' server/app/main.py` → 8 (aumentou em 1 em relação ao HEAD anterior).
- `grep -n 'source = chain' server/app/main.py` → 2 ocorrências dentro de `options_proposta`.
- `git diff server/app/main.py` (task 1) → só acréscimos no bloco de retorno, nenhuma linha removida.
- Injeção de falha manual: substituído `"source": source` por `"source": "yahoo"` na rota → `test_fonte_da_proposta_vem_da_cadeia_e_nunca_de_literal_na_rota` reprovou; `git checkout -- server/app/main.py` restaurou o verde.
- `git status --porcelain web/` → vazio (plano backend-only confirmado).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plano 17-04 (front) pode consumir `body.source` e `body.at` da resposta de `GET /api/options/proposta/{ticker}` — nomes de campo exatos: `source` (string ou `null`), `at` (string `"DD/MM/AAAA HH:MM"`, sempre presente, nunca `null`). Front já tem `FONTE_LABEL` pronto para renderizar esse par (`web/src/App.jsx:1185,1655`), conforme mapeado no `17-CONTEXT.md`.

Nenhum bloqueio para 17-03/17-04/17-05/17-06.

---
*Phase: 17-fluxo-de-aceite*
*Completed: 2026-09-02*

## Self-Check: PASSED

- FOUND: `.planning/phases/17-fluxo-de-aceite/17-02-SUMMARY.md`
- FOUND: `.planning/phases/17-fluxo-de-aceite/deferred-items.md`
- OK: `server/.venv` (worktree test symlink) removed before finishing
- FOUND commit `53eca92` (test: RED)
- FOUND commit `3f47379` (feat: GREEN)
- FOUND commit `8195edc` (test: guardiões)
- FOUND commit `21a5eb9` (docs: SUMMARY)
