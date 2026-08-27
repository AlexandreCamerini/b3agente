---
phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa
plan: 04
subsystem: infra
tags: [mydata, rate-limit, medicao, budget, scanner, radar-daily, options-provider]

# Dependency graph
requires:
  - phase: "09-01/09-02/09-03"
    provides: "mydata_client.py (Plano 09-01), candle_provider roteador+cadeia de fallback com MydataProvider (Plano 09-02), options_provider_mydata.py (Plano 09-03) — os módulos que este plano mede executando de verdade"
provides:
  - "scripts/medir-mydata.py: fase `projecao` (offline, ZERO rede, sempre executável) mede custo unitário real de candle/cadeia de opções com fetch_json fake contando chamadas, projeta 3 cenários sobre scanner.get_universe() e emite veredito CABE/NÃO CABE contra 60/min·2.000/dia; fase `vivo` (rede real, --vivo explícito) implementada por completo, ainda não executada"
  - "docs/MEDICAO-Mydata-2026-08-27.md: veredito da projeção (NÃO CABE no pico/min, CABE no volume/dia), achados de arquitetura (morno real vs. leitura literal do plano; opções sem gate de orçamento), plano de ação, status de provento_b3"
  - ".planning/todos/pending/medir-rate-limit-mydata.md: seção Resultado anexada, item 1 (mapear volume) resolvido, item 3 (chave autenticando de fato) segue pending"
affects: [09-06-checkpoint-virada-producao]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "fetch_json fake injetado no cliente real (não estimativa por leitura de código) para medir custo unitário de chamadas HTTP offline, mesmo padrão de mydata_provider tests"
    - "monkeypatch temporário de mydata_client._fetch_json (nome resolvido em tempo de chamada) para medir módulos que não expõem fetch_json injetável (options_provider_mydata.get_options)"

key-files:
  created:
    - scripts/medir-mydata.py
    - docs/MEDICAO-Mydata-2026-08-27.md
  modified:
    - .planning/todos/pending/medir-rate-limit-mydata.md

key-decisions:
  - "Cenário 'morno' relatado em DOIS números: o REAL (radar_daily.maybe_run, 1x/dia útil, verificado por leitura de código — 74 chamadas/dia) e o LEITURA LITERAL do texto do plano (cadência do scheduler_loop, 300s → 288 ciclos/dia → 21.312 chamadas/dia, NÃO observada no código). O texto do plano descrevia uma cadência que o código não implementa; corrigir isso em silêncio teria reproduzido exatamente a 'inferência de arquitetura' que este plano existe para eliminar (09-CONTEXT.md) — os dois números ficam visíveis, com o REAL usado no veredito"
  - "Pico chamadas/min do cenário de opções fica SEM número, não estimado: confirmado por leitura que options_provider_mydata.py/options_provider.py nunca chamam mydata_budget.pode_gastar/debita (só candle_provider.get_history tem gate, Plano 09-02) — não há teto de taxa no código, e não há dado de uso real para estimar concorrência. Reportar um número aqui seria inventar valor (princípio 4 do CLAUDE.md)"
  - "Token fake (`_FAKE_TOKEN_PROJECAO`, nunca impresso) setado/restaurado via try/finally em os.environ só para satisfazer o guard `if not _token()` do mydata_client durante a fase projecao — nenhuma chamada real acontece nesse escopo (fetch_json sempre fake)"

requirements-completed: []

# Metrics
duration: ~55min
completed: 2026-08-27
---

# Phase 9 Plan 04: Medição de rate-limit do mydata Summary

**VEREDITO DA PROJEÇÃO: NÃO CABE — pico projetado de 148 chamadas/min (frio+morno) contra o teto de 60/min da chave; volume diário CABE com folga (548 de 2.000/dia, 72,6% de folga); `intervaloMinimoSeguro` = 1,0s; perna ao vivo (autenticação real da chave `f00b4554`) BLOQUEADA — `MYDATA_TOKEN` ausente neste ambiente de execução.**

## Performance

- **Duration:** ~55 min
- **Tasks:** 2/2 executados — Task 1 completa e verificada; Task 2 completa PARCIALMENTE (ver Deviations/blocked)
- **Files modified:** 3 (2 novos, 1 editado)

## Os quatro números que o checkpoint do Plano 09-06 lê

1. **VEREDITO (só da projeção offline):** NÃO CABE, por causa do pico por minuto — não do volume diário.
2. **Pico chamadas/min projetado:** 148 (74 do cenário frio + 74 do cenário morno REAL), contra 60/min da chave. Volume chamadas/dia projetado: 548 (74 frio + 74 morno REAL + 400 opções), contra 2.000/dia.
3. **`intervaloMinimoSeguro`:** 1,0s de espaçamento mínimo entre chamadas reais ao mydata (hoje `scanner.MIN_FETCH_GAP_S`=0,15s, dimensionado para Yahoo/brapi — 6,7× mais folgado do que o teto do mydata permite).
4. **Perna ao vivo:** NÃO RODOU. `MYDATA_TOKEN` ausente neste ambiente — confirmado por `env | grep -i MYDATA` antes de começar. `scripts/medir-mydata.py --fases vivo --vivo` saiu com código 2, exatamente como o critério de aceite do Plano 09-04 exige (recusa explícita, nenhuma simulação, nenhuma chamada de rede feita). A chave de produção (`f00b4554`) **ainda não foi confirmada autenticando de fato** contra `mydata.acamerini.app`.

## Accomplishments

- `scripts/medir-mydata.py` — fase `projecao` executa o código REAL
  (`mydata_client.get_history`/`get_vencimentos`/`get_options_chain`, via
  `options_provider_mydata.get_options`) com `fetch_json` fake contando
  chamadas HTTP — não estima por leitura de código. Mede custo unitário
  (candle: 1 chamada sem paginação para `2y` e para `1mo`, confirmando o
  09-02-SUMMARY.md; opções: 2 chamadas por cadeia completa, confirmando o
  09-03-SUMMARY.md), projeta 3 cenários sobre `scanner.get_universe()`
  (74 ativos reais) e emite veredito explícito com `60/min`/`2.000/dia`
  literais no stdout.
- Fase `vivo` implementada por completo — amostra por ticker (status,
  latência, `X-Quota-Limite`/`X-Quota-Restante`, campos de preço), guarda de
  escopo de chave (200 com dados mas sem `preco_fechamento` = achado
  nomeado, não "sem dado"), reconciliação previsão×verdade — mas não
  executável neste ambiente (token ausente).
- Dois achados de arquitetura descobertos ao medir (não ao planejar):
  1. **Cenário morno do plano não bate com o código.** O texto do Plano
     09-04 descrevia a cadência do "morno" pela `interval_s` do
     `scheduler_loop` (300s → 288 ciclos/dia). Verificado por leitura: o
     único ponto que varre o universo INTEIRO em busca de candle é
     `radar_daily.maybe_run`, 1x por dia útil às 08:45 — não a cada tick do
     scheduler. O número REAL é 74 chamadas/dia, não 21.312. Os dois
     números aparecem no script e no documento, rotulados.
  2. **Opções não têm gate de orçamento no código.** Confirmado por leitura
     de `options_provider.py`/`options_provider_mydata.py`: nenhum dos dois
     chama `mydata_budget.pode_gastar()`/`debita()` — só `candle_provider.py`
     tem esse gate (Plano 09-02). O pico/min de opções fica sem teto
     nenhum no código atual.
- `docs/MEDICAO-Mydata-2026-08-27.md` — 9 seções (o que foi medido, custos
  unitários, projeção, amostra ao vivo, reconciliação, veredito, item 2 do
  TODO, plano de ação, pré-condição da virada), com o status de
  `provento_b3` conferido em `~/dev/cvm-financas/docs/contrato-consumidor.md`
  (rota construída, primeira carga de produção pendente do lado de lá).
- `.planning/todos/pending/medir-rate-limit-mydata.md` — seção `## Resultado
  (2026-08-27)` anexada ao final, texto original preservado
  (`grep -c 'Vira critério de aceite da fase'` = 1). Fica em `pending/`
  (não vai para `done/`): item 1 resolvido pela projeção, item 3 (chave
  autenticando de fato) segue pendente até a perna ao vivo rodar.
- `bash scripts/executar.sh --testes` verde: 1519 passed/1 skipped
  (backend) + todas as `web/tests/*.mjs` OK — confirma que nada de
  aplicação foi arrastado por este plano (só script novo + docs).

## Task Commits

1. **Task 1: scripts/medir-mydata.py — projeção offline do volume de chamadas** - `9180bd8` (feat)
2. **Task 2: Rodar a medição ao vivo e publicar o veredito** - `158e62f` (docs) — PARCIAL, ver Deviations

## Files Created/Modified

- `scripts/medir-mydata.py` (novo, 443 linhas) — fases `projecao`/`vivo`, contadores de chamadas fake, cálculo de pico/burst e `intervaloMinimoSeguro`, veredito
- `docs/MEDICAO-Mydata-2026-08-27.md` (novo) — números da projeção, achados, plano de ação, seção "Amostra ao vivo" e "Reconciliação" marcadas BLOQUEADO
- `.planning/todos/pending/medir-rate-limit-mydata.md` — seção `## Resultado` anexada, texto original intacto

## Decisions Made

Ver `key-decisions` no frontmatter — resumo: (1) cenário morno relatado em
dois números (real vs. leitura literal do plano) em vez de escolher um só
em silêncio; (2) pico de opções deixado sem número em vez de inventado; (3)
token fake local/nunca impresso para destravar a fase projeção sem
credencial real.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug/premissa técnica] Cenário "morno" do texto do plano descrevia uma cadência que o código não implementa**
- **Found during:** Task 1, ao implementar o cenário morno conforme `<action>` (ler `interval_s` do `scheduler_loop` e o piso de `_MIN_DELTA_INTERVAL`)
- **Issue:** seguir o texto literal do plano (288 ciclos/dia de varredura completa do universo) produziria um número (21.312 chamadas/dia) que não corresponde a nenhum caminho de código real — o único full-universe scan é `radar_daily.maybe_run`, 1x/dia útil
- **Fix:** o script calcula e reporta OS DOIS números (real, observado no código; e literal, rotulado como hipótese não observada), e usa o REAL na soma que fecha o veredito — evita tanto subestimar quanto inflar artificialmente o risco
- **Files modified:** `scripts/medir-mydata.py`, `docs/MEDICAO-Mydata-2026-08-27.md`
- **Verification:** leitura de `server/app/agent.py` (linha 1202 em diante) e `server/app/radar_daily.py` (`maybe_run`, gate `pregao.is_trading_day()`, `B3_RADAR_DAILY_HHMM`); confirmado com o `advisor` antes de implementar
- **Committed in:** `9180bd8` (Task 1), documentado em `158e62f` (Task 2)

---

**Total deviations:** 1 auto-fix de premissa técnica (Rule 1), descoberto ao medir, não ao planejar. Nenhum desvio de escopo, nenhuma dependência nova, nenhum arquivo fora dos 3 do plano.
**Impact on plan:** O ajuste torna o número do cenário morno FIEL ao código real, em vez de herdar uma premissa de arquitetura não verificada — exatamente o problema que este plano (e o TODO que ele fecha) existe para eliminar.

## BLOQUEIO — Task 2 não fecha o critério de aceite completo

Per o `<action>` da Task 2 e a `<credential_note>` desta execução:
`MYDATA_TOKEN` está ausente neste ambiente (confirmado por `env | grep -i
MYDATA` antes de começar — nenhuma variável presente). Seguindo o caminho de
degradação DOCUMENTADO pelo próprio plano ("Se MYDATA_TOKEN não estiver no
ambiente: PARE. Não invente número, não rode só a projeção e declare o
critério fechado."):

- A fase `projecao` rodou por completo e o resultado foi publicado
  (`docs/MEDICAO-Mydata-2026-08-27.md`).
- A fase `vivo` foi tentada (`--fases projecao,vivo --vivo --amostra 5`) e
  saiu com código 2, recusando corretamente em vez de simular.
- **Os seguintes itens do critério de aceite da Task 2 NÃO estão fechados:**
  autenticação real da chave `f00b4554` contra `mydata.acamerini.app`;
  confirmação do escopo `fonte:b3` (campos de preço presentes); amostra ao
  vivo por ticker; reconciliação previsão×verdade com `X-Quota-Restante`
  real.
- **Os seguintes itens do `must_haves.truths` do plano NÃO estão
  cumpridos:** "A chave de produção autentica de fato... e devolve dado das
  duas rotas".

**Ação necessária do usuário:** exportar `MYDATA_TOKEN` (prefixo público
`f00b4554`; chave completa nunca commitada) no shell local e rodar:

```
server/.venv/bin/python scripts/medir-mydata.py --fases vivo --vivo --amostra 5 --saida /tmp/medicao-mydata-vivo.json
```

e completar as seções "Amostra ao vivo"/"Reconciliação previsão × verdade"
de `docs/MEDICAO-Mydata-2026-08-27.md` com os números reais antes do
checkpoint do Plano 09-06 — que **não pode aprovar a virada de
`B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER` para `mydata`** sem essa
confirmação, e sem resolver o achado do pico/min (item 1 do "Plano de ação"
do documento).

## Issues Encountered

- Worktree nasceu um commit ATRÁS do `base_commit` esperado (padrão já
  relatado nos SUMMARYs 09-01/09-02/09-03) — corrigido com `git reset
  --hard` para `2fab2897f1ea1880c195e1a29dea9306824b13c1` antes de qualquer
  edição, working tree limpo, sem perda de trabalho.

## User Setup Required

**Sim — MYDATA_TOKEN precisa ser exportado localmente para completar este
plano.** Ver seção "BLOQUEIO" acima e a `user_setup` do frontmatter do
Plano 09-04:
- `service: mydata (cvm-financas)`
- `env_vars: MYDATA_TOKEN` — "Chave de prefixo f00b4554 (produção).
  Exportar no shell local só para rodar a medição; nunca commitar."

## Next Phase Readiness

- `scripts/medir-mydata.py` está pronto e reexecutável — rodar `--fases
  vivo --vivo` localmente com o token é a ÚNICA ação pendente para fechar
  o critério de aceite completo desta fase.
- O achado do pico/min (NÃO CABE, 148 de 60/min) precisa de uma decisão
  arquitetural antes da virada (Plano 09-06): tornar `scanner.py`'s
  espaçamento entre chamadas SENSÍVEL ao provedor ativo, em vez de um
  `MIN_FETCH_GAP_S` global — decisão fora do escopo deste plano de medição.
- O achado de opções sem gate de orçamento (arquitetura, não corrigido)
  também precisa entrar na pauta do Plano 09-06 antes de virar
  `B3_OPTIONS_PROVIDER=mydata`.
- `provento_b3` confirmado fora do escopo das duas fatias migradas nesta
  fase — não usar essa classe até a primeira carga de produção ser
  confirmada do lado cvm-financas, mesmo depois da virada de candle/opções.
- **Bloqueio conhecido:** perna ao vivo pendente de `MYDATA_TOKEN` — ver
  seção BLOQUEIO acima.

## Self-Check: PASSED

- FOUND: scripts/medir-mydata.py
- FOUND: docs/MEDICAO-Mydata-2026-08-27.md
- FOUND: .planning/todos/pending/medir-rate-limit-mydata.md (seção Resultado presente)
- FOUND: .planning/phases/09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa/09-04-SUMMARY.md
- FOUND commits: 9180bd8, 158e62f (verified via `git log --oneline -3`)

---
*Phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa*
*Completed: 2026-08-27 (PARCIAL — perna ao vivo bloqueada pendente de MYDATA_TOKEN)*
