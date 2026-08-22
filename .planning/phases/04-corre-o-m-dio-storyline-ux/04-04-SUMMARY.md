---
phase: 04-corre-o-m-dio-storyline-ux
plan: 04
subsystem: api
tags: [python, fastapi, llm-fallback, order-rejection-trail, benchmark, ibovespa]

# Dependency graph
requires:
  - phase: 04-corre-o-m-dio-storyline-ux (04-01)
    provides: "explicacao_det.montar(ticker, snap, modo, quote) — compositor determinístico do Passo 7"
  - phase: 04-corre-o-m-dio-storyline-ux (04-02)
    provides: "store.registrar_rejeicao(), benchmark.serie_ibov() — motores do rastro de rejeição e da série do Ibovespa"
provides:
  - "POST /api/technical/analyze/{ticker} e POST /api/analyze/{ticker} devolvem 200 + fonte:\"deterministico\" (nunca 502) quando a IA está indisponível"
  - "POST /api/buy e POST /api/sell gravam toda rejeição de conta logada no histórico (status/motivo/price honestos) antes do erro voltar ao cliente"
  - "GET /api/benchmark/ibov — série diária do Ibovespa para o Passo 8 comparar com a carteira simulada"
affects: ["04-05-ui-explicacao-passo7", "04-06 (front, consumo dos 3 contratos fixados)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate 402 (_gate_analise) e falha de chamada de IA convergem no MESMO ponto de decisão (ia_indisponivel) — a rota nunca precisa saber POR QUE a IA faltou, só QUE faltou"
    - "Reuso por promptFp roda ANTES da checagem de ia_indisponivel — uma leitura de IA já paga é servida de graça mesmo com cota negada agora"
    - "Rejeição de ordem é escrita ANTES do HTTPException (não depois, não num handler de exceção) — o contrato de erro HTTP não muda, o registro é estritamente aditivo"

key-files:
  created:
    - server/tests/test_rotas_fase4.py
  modified:
    - server/app/main.py
    - server/tests/test_fase3_gate_plano.py

key-decisions:
  - "Reuso por promptFp tem precedência sobre ia_indisponivel: se existe análise cacheada com a MESMA pergunta, ela é devolvida (reaproveitada:true) mesmo quando o gate acabou de negar a cota. Racional: reaproveitar não custa nada, e esconder uma resposta de IA já paga atrás do fallback determinístico seria pior experiência sem ganho nenhum. Não estava descrito literalmente no PLAN.md; guardião dedicado em test_rotas_fase4.py."
  - "sell() passou a normalizar `t` via _normalize_ticker (era só .upper()) — fecha T-04-03 (o `t` gravado em qualquer registro precisa ser sempre o normalizado) e alinha com buy()/as rotas de análise, que já normalizavam. Mudança estritamente aditiva: tickers.normalize_ticker é superset de .upper() (também remove espaço/.SA/caractere fora de A-Z0-9), nenhum teste existente dependia do comportamento antigo."
  - "Guardiões de Fase 3 (test_fase3_gate_plano.py) que travavam 402 cru na negação do gate foram atualizados para 200+fallback — mesma precedência PLANO>METERING, contrato de resposta diferente por desenho explícito do CONTEXT.md desta fase. Nota no topo do arquivo documenta a reversão de contrato (guardrail CLAUDE.md: guardião não se apaga, se atualiza com nota)."

requirements-completed: [FIX-C01, FIX-C02, FIX-C03]

# Metrics
duration: ~30min
completed: 2026-08-21
---

# Phase 4 Plan 04: Fiação das rotas — fallback determinístico, rastro de rejeição, benchmark Ibovespa Summary

**As duas rotas de análise nunca mais devolvem 502 por falta de IA (fallback determinístico via `explicacao_det`), `/api/buy`/`/api/sell` gravam toda rejeição de conta logada no histórico antes do erro, e `GET /api/benchmark/ibov` expõe a série do Ibovespa — os 3 contratos de resposta fixados no PLAN.md, verificados também com o servidor real no ar (não só TestClient).**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-08-21T22:56:00-03:00 (aprox., logo após a leitura do plano)
- **Completed:** 2026-08-21T23:15:00-03:00
- **Tasks:** 3/3 completed
- **Files modified:** 3 (1 criado, 2 modificados)

## Accomplishments
- `POST /api/technical/analyze/{ticker}` e `POST /api/analyze/{ticker}` (legada) degradam para `explicacao_det.montar()` — 200 com `fonte:"deterministico"`, `iaIndisponivel:{code,mensagem}`, `verbetes`, `semDados` — tanto quando o gate de plano/cota nega (402) quanto quando a chamada de IA falha (`missing_key` etc.). O fallback é efêmero por desenho: não consome cota, não persiste (evita que o reuso por `promptFp` sirva o fallback pra sempre depois que a chave voltar), não alimenta `ai_activity`/`analysis_outcomes`. Caminho de IA bem-sucedido ganha `fonte:"ia"`/`iaIndisponivel:null` aditivos.
- `POST /api/buy` e `POST /api/sell` chamam `store.registrar_rejeicao()` em TODO ponto de rejeição de conta logada (ticker inválido, sem cotação, caixa/posição insuficiente, quantidade inválida — nos caminhos imediato E pendente) ANTES do `HTTPException` — contrato de erro HTTP inalterado, nenhum dinheiro se move, balde anônimo nunca registra (T-04-12).
- `GET /api/benchmark/ibov` (nova rota) expõe `benchmark.serie_ibov()` sem aceitar símbolo do cliente (T-04-04), degrada com a frase única `"Comparação com o Ibovespa indisponível agora."` quando o Yahoo falha, posicionada antes do `app.mount("/")` catch-all.
- Verificação AO VIVO (não só TestClient): servidor real subido contra o worktree, `GET /api/benchmark/ibov` devolveu a série real do Yahoo, `POST /api/buy` com caixa insuficiente devolveu 400 e o `GET /api/state` seguinte confirmou a entrada `status:"rejeitada"` com `motivo` e `cash` intocado, `POST /api/technical/analyze/PETR4` sem chave de IA devolveu 200 com `fonte:"deterministico"` e markdown real do compositor.
- 25 casos novos em `server/tests/test_rotas_fase4.py` cobrindo os 3 achados; suíte canônica completa verde (1324 testes backend + toda `web/tests/*.mjs`).

## Task Commits

Each task was committed atomically:

1. **Task 1: Fallback determinístico nas duas rotas de análise (FIX-C01)** - `7f8cf91` (feat)
2. **Task 2: Registro da tentativa rejeitada em /api/buy e /api/sell (FIX-C02)** - `27f2da2` (feat)
3. **Task 3: Rota GET /api/benchmark/ibov (FIX-C03)** - `03ff3c6` (feat)
4. **Follow-up: guardião do reuso vencendo o gate 402** - `66ad1fc` (test) — adicionado após revisão, cobre uma decisão de design tomada durante a Task 1 que não tinha teste dedicado (ver Deviations)

_Note: nenhuma tarefa era TDD; guardiões escritos junto do código na mesma tarefa/commit, exceto o follow-up acima._

## Files Created/Modified
- `server/app/main.py` - fallback determinístico nas 2 rotas de análise (FIX-C01); `store.registrar_rejeicao` nos 9 pontos de rejeição de `/api/buy`/`/api/sell` (FIX-C02), incluindo normalização de `t` em `sell()`; rota nova `GET /api/benchmark/ibov` (FIX-C03)
- `server/tests/test_rotas_fase4.py` (novo) - 25 testes: 12 de C-01 (fallback + gate 402 + reuso), 9 de C-02 (rastro de rejeição), 6 de C-03 (benchmark) — alguns casos se sobrepõem entre grupos temáticos
- `server/tests/test_fase3_gate_plano.py` - 2 guardiões de Fase 3 atualizados: a negação do gate de análise não estoura mais 402 cru, vira fallback determinístico (200); nota no topo do arquivo documenta a reversão de contrato

## Decisions Made
- Ver `key-decisions` no frontmatter (reuso vence gate 402; normalização de `t` em `sell()`; atualização dos guardiões de Fase 3).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `sell()` não normalizava `t` — só `.upper()`**
- **Found during:** Task 2
- **Issue:** O PLAN.md exige (T-04-03) que o `t` gravado em qualquer registro seja sempre o resultado de `_normalize_ticker`. `buy()` já normalizava; `sell()` fazia só `t = str(body.get("t","")).upper()`, deixando passar espaço/sufixo `.SA`/caractere fora de A-Z0-9 sem normalizar.
- **Fix:** `sell()` passou a chamar `_normalize_ticker` (que é superset de `.upper()` — também remove espaço, `.SA`, caracteres não-alfanuméricos), igualando o comportamento a `buy()` e às rotas de análise.
- **Files modified:** server/app/main.py
- **Verification:** suíte completa (`tests/test_ordens_pendentes_rotas.py`, `tests/test_ciclo_imediato_apos_carteira.py`) segue verde — nenhum teste existente usava ticker fora do formato já normalizado.
- **Committed in:** 27f2da2 (Task 2 commit)

**2. [Rule 1 - Bug/Test gap] Guardiões de Fase 3 assumiam 402 cru do gate de análise**
- **Found during:** Task 3 (ao rodar a suíte completa após as 3 tasks)
- **Issue:** `test_fase3_gate_plano.py` tinha 2 testes que esperavam `HTTPException(402, motivo)` propagando cru até o cliente quando `_gate_analise` nega — comportamento que a Task 1 deste mesmo plano mudou deliberadamente (é o próprio FIX-C01: gate negando vira fallback determinístico, não erro).
- **Fix:** Os 2 testes foram atualizados para esperar 200 + `fonte:"deterministico"` + `iaIndisponivel.mensagem` igual ao motivo antigo do `detail`. A PRECEDÊNCIA que os testes travam (plano decide antes de metering) continua idêntica — só o transporte da negação mudou. Nota explicativa adicionada no topo do arquivo, por guardrail do CLAUDE.md ("guardiões de teste não se apagam — reversão deliberada atualiza o guardião com nota").
- **Files modified:** server/tests/test_fase3_gate_plano.py
- **Verification:** suíte completa (1324 testes) verde após o ajuste.
- **Committed in:** 03ff3c6 (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (1 bug/T-04-03, 1 atualização de guardião pré-existente por mudança de contrato deliberada da própria Task 1)
**Impact on plan:** Ambos necessários para fechar exatamente o que o PLAN.md pediu (T-04-03) e para manter a suíte canônica verde sem apagar cobertura histórica. Nenhum scope creep.

## Issues Encountered
- Um comportamento de design tomado durante a Task 1 (o reuso por `promptFp` vencer uma negação de gate 402, servindo a análise cacheada em vez do fallback) não estava descrito literalmente no PLAN.md e inicialmente ficou sem teste dedicado — identificado em revisão antes de fechar o plano. Resolvido com um guardião novo (`test_gate_402_com_analise_cacheada_reaproveita_em_vez_de_cair_no_fallback`, commit `66ad1fc`) e documentado aqui.
- `web/node_modules` não estava instalado no worktree (esperado — gitignored). `npm install` rodado localmente no worktree (sem alterar `package.json`/lockfile) para poder rodar a suíte canônica completa (`bash scripts/executar.sh --testes`), já que este é o plano de consolidação que toca `main.py` — as 87 web/tests/*.mjs mais os 1324 testes backend passaram.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Os 3 contratos de resposta fixados no PLAN.md (`fonte`/`iaIndisponivel`/`verbetes`/`semDados` nas rotas de análise; `status`/`motivo` no histórico; `t`/`nome`/`fonte`/`candles`/`asOf` em `/api/benchmark/ibov`) estão implementados exatamente como especificado — os Planos 04-05/04-06 (UI) podem consumi-los sem ambiguidade.
- Nenhum arquivo de `web/` foi tocado (confirmado via `git diff --stat` contra a base da wave) — consistente com o `success_criteria` do plano.
- Verificação ao vivo (servidor real, não só TestClient) confirmou os 3 achados ponta a ponta com dado real do Yahoo — reduz risco de o `app.mount()`/startup do ASGI real divergir do comportamento observado só em teste.
- Sem bloqueios conhecidos para os Planos 04-05/04-06.

---
*Phase: 04-corre-o-m-dio-storyline-ux*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: server/app/main.py
- FOUND: server/tests/test_rotas_fase4.py
- FOUND: server/tests/test_fase3_gate_plano.py
- FOUND: .planning/phases/04-corre-o-m-dio-storyline-ux/04-04-SUMMARY.md
- FOUND: 7f8cf91 (Task 1 commit)
- FOUND: 27f2da2 (Task 2 commit)
- FOUND: 03ff3c6 (Task 3 commit)
- FOUND: 66ad1fc (follow-up guardião commit)
