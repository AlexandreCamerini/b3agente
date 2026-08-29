---
phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa
plan: 03
subsystem: api
tags: [mydata, options, iv, greeks, adr-004, provider-seletor, tdd]

# Dependency graph
requires: ["09-01"]
provides:
  - "server/app/mydata_client.py: get_vencimentos()/get_options_chain() sobre /v1/opcoes — endpoint dedicado de vencimentos (sem paginação) + cadeia paginada por proximo_cursor, ambos devolvendo linhas cruas de gold_opcoes"
  - "server/app/options_provider_mydata.py: adaptador do contrato ADR-004 (providerStatus/calls/puts/expirations) alimentado por gold_opcoes, com IV/gregas/preço teórico prontos do hub, sem fallback ao Yahoo (D-04)"
  - "server/app/options_provider.py: seletor de provedor de opções por env B3_OPTIONS_PROVIDER (default yahoo, espelho de candle_provider.provider_name())"
affects: [09-04-medicao-rate-limit, 09-06-checkpoint-virada-de-provedor]

# Tech tracking
tech-stack:
  added: []   # nenhuma dependência nova
  patterns:
    - "Seletor por env em miniatura (options_provider.py), mesmo padrão de candle_provider.provider_name()/get_provider() — alavanca de rollback manual, nunca fallback automático em runtime"
    - "Campos aditivos: contrato antigo preservado 1:1, gregas/IV/proveniência entram como chaves NOVAS no mesmo dict, nunca substituindo as antigas"

key-files:
  created:
    - server/app/options_provider_mydata.py
    - server/app/options_provider.py
    - server/tests/test_options_provider_mydata.py
    - server/tests/test_options_provider.py
  modified:
    - server/app/mydata_client.py
    - server/app/options_api.py
    - server/app/main.py
    - server/app/agent.py
    - server/tests/test_mydata_client.py

key-decisions:
  - "Arquivo de teste do seletor: test_options_provider.py dedicado (não em test_options_provider_mydata.py) — o plano deixava a escolha a critério do executor; um arquivo por módulo mantém a mesma convenção 1:1 já usada no repo (test_options_provider_yahoo.py ↔ options_provider_yahoo.py)"
  - "Teste do caso B3_OPTIONS_PROVIDER=banana: pytest.raises(ValueError, match='banana') real, em vez do comando shell condicional (if hasattr(...)) sugerido como alternativa nos critérios de aceite — a alternativa 'OU um teste equivalente' do próprio plano cobre essa escolha"
  - "agent.py:501 (comentário citando options_provider_yahoo.get_options em produção) corrigido para citar options_provider.get_options — Rule 1 (comentário desatualizado depois da troca de import em main.py), fora da lista de <files> do plano mas necessário para o grep de aceite 'nenhum options_provider_yahoo fora dos arquivos esperados' passar"

requirements-completed: []

# Metrics
duration: ~9min (implementação; tempo de leitura/orientação não contado)
completed: 2026-08-27
---

# Phase 9 Plan 03: Opções/IV migradas para o mydata (atrás do contrato ADR-004) Summary

**Cadeia de opções, IV e gregas passam a vir do mydata via `options_provider_mydata.py`, atrás do MESMO contrato `providerStatus`/`calls`/`puts`/`expirations` do ADR-004, com degradação direta sem fallback ao Yahoo (D-04) e provedor selecionável por env — default de produção continua `yahoo`.**

## Performance

- **Duration:** ~9 min (do primeiro commit RED ao commit de verificação do contrato)
- **Tasks:** 3/3 completos
- **Files modified:** 9 (4 novos, 5 existentes)

## Accomplishments

- `mydata_client.py`: `get_vencimentos()` chama o endpoint dedicado `/v1/opcoes/{ticker}/vencimentos` (sem paginação — o endpoint não devolve `proximo_cursor`), devolve `[]` sem levantar quando o papel não tem pregão publicado; `get_options_chain()` pagina `/v1/opcoes/{ticker}` por `proximo_cursor` e devolve linhas cruas de `gold_opcoes`, sem remapear nenhum campo (separação cliente-fala-hub / adaptador-fala-Boris preservada).
- `options_provider_mydata.py`: adaptador completo do contrato ADR-004 — mapeia `contrato→contractSymbol`, `premio→lastPrice`, `melhor_oferta_compra/venda→bid/ask`, `quantidade_negociada→volume`; `openInterest` sempre `None` (sem fonte no COTAHIST); IV nula é dado legítimo, rotulada em `ivStatus` (`situacao_sigma` cru); gregas e preço teórico entram como campos ADITIVOS (`greeks`, `theoreticalPrice`, `riskFreeRate`, `exerciseStyle`) sem remover nenhuma chave antiga; cache de módulo 300s/60s idêntico ao provider anterior; qualquer falha (vencimentos vazio, `MydataIndisponivel`) degrada direto — nenhum ramo importa ou chama o provedor Yahoo.
- `options_provider.py`: seletor mínimo por `B3_OPTIONS_PROVIDER` (default `"yahoo"`, espelho de `candle_provider.provider_name()`), nome desconhecido levanta `ValueError` citando as opções válidas. Documentado como alavanca de rollback manual, não fallback automático.
- 8 call sites trocados (`options_api.py:10`; `main.py:30,46,1211,1216,1226,2103,2138,2626,2656,2776,2844`) — nenhuma chamada mudou de assinatura. Os dois literais `"yfinance"` em `main.py` (status técnico da IA) viraram `options_provider.provider_name()`, corrigindo um rótulo de fonte que já estava desatualizado antes desta migração.
- 71 guardiões novos (7 + 19 + 26 + 12 + 7 novos entre os arquivos), todos offline.

## Task Commits

Cada task de código seguiu RED→GREEN (TDD); Task 3 (troca de call sites, sem `tdd="true"`) foi feita direto com verificação de suíte completa.

1. **Task 1: mydata_client — get_vencimentos e get_options_chain**
   - `ae5bf77` (test) — 12 guardiões novos, RED confirmado (`AttributeError`)
   - `4ef5610` (feat) — implementação, GREEN (38/38 no arquivo)
2. **Task 2: options_provider_mydata — adaptador do contrato ADR-004**
   - `2afe20d` (test) — 26 guardiões novos, RED confirmado (`ImportError`)
   - `1654619` (feat) — implementação, GREEN (26/26 nos dois arquivos de opções); 1 ajuste de conteúdo do docstring durante GREEN (ver Deviations)
3. **Task 3: options_provider + troca dos 8 call sites**
   - `d517755` (feat) — seletor + troca de import/call sites em `options_api.py`/`main.py` + correção de comentário em `agent.py`; suíte completa 1497 passed, 1 skipped; `bash scripts/executar.sh --testes` verde (backend + web)
   - `29a2497` (test) — teste de paridade de contrato (chaves de topo mydata ⊇ yahoo, aditivos declarados) exigido pela seção `<verification>` do plano; suíte completa 1498 passed, 1 skipped

## Files Created/Modified

- `server/app/mydata_client.py` (+48 linhas) — `get_vencimentos`, `get_options_chain`
- `server/app/options_provider_mydata.py` (175 linhas, novo) — `_empty_payload`, `_clean_contract`, `get_options`, `MYDATA_OPTIONS_WARNING`
- `server/app/options_provider.py` (42 linhas, novo) — `provider_name()`, `get_options()`, `_PROVEDORES`
- `server/app/options_api.py` (1 linha) — import trocado para `.options_provider`
- `server/app/main.py` (11 linhas em 8 pontos) — import + 6 call sites + 2 literais `"yfinance"`
- `server/app/agent.py` (1 comentário) — referência desatualizada corrigida (Rule 1)
- `server/tests/test_mydata_client.py` (+121 linhas) — 12 guardiões de vencimentos/cadeia
- `server/tests/test_options_provider_mydata.py` (312 linhas, novo) — 26 guardiões do adaptador
- `server/tests/test_options_provider.py` (91 linhas, novo) — 7 guardiões do seletor + paridade de contrato

## Achados de produto registrados no plano (não corrigidos aqui)

**(a) `liquidity_score` sem `openInterest` — MEDIDO, não presumido.** Um contrato PETR4 realista (volume 5.000, spread 1,80/1,90 ≈ 5,41%, `openInterest=None`) mede `score=52.0` — passa do corte de 40 usado por `options_api.liquidity_gate`. O teto do score cai de 100 para 60 sem open interest (perde os até 40 pontos de `oi_score`); este caso específico ainda passa, mas contratos de volume mais baixo que hoje dependiam de open interest real para cruzar o corte podem deixar de passar. `options_quant.py` NÃO foi alterado (confirmado: `git diff --stat` não lista o arquivo) — acompanhar este número no checkpoint do Plano 09-06.

**(b) Custo de chamadas ao hub por cadeia completa.** 1 chamada a `/v1/opcoes/{ticker}/vencimentos` (sem paginação) + N chamadas a `/v1/opcoes/{ticker}` até `proximo_cursor` zerar. Com `LIMITE_MAX=2000` por página e cadeias de opções da B3 tipicamente na casa de dezenas a poucas centenas de contratos por vencimento, o caso normal é **2 chamadas por cadeia completa** (1 vencimentos + 1 página de cadeia). Múltiplas páginas só ocorreriam em vencimentos com >2.000 contratos, cenário não observado na B3. Este número entra na conta do Plano 09-04 (medição de rate-limit real).

**(c) Lista final de campos aditivos entregues além do contrato do ADR-004.** Por contrato: `ivStatus` (`situacao_sigma` cru — explica IV nula quando aplicável), `theoreticalPrice` (preço teórico do hub via Black-Scholes), `greeks` (`{delta, gamma, vega, theta, rho}`), `expiration` (eco do `dt_vencimento` da linha), `riskFreeRate`, `exerciseStyle`. No topo do payload: `pregao` (data do pregão que serviu a cadeia) e `provenance` (dict `{sha256, dt_captura, arquivo, arquivo_em}` da primeira linha, quando presente) — rastro até o arquivo oficial da B3 que o contrato do Yahoo nunca teve.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug/guardião] Docstring de `options_provider_mydata.py` citava `options_provider_yahoo.py` por nome**
- **Found during:** Task 2, verificação dos critérios de aceite (`grep -c 'options_provider_yahoo'`/`grep -c 'yahoo'` devem dar 0)
- **Issue:** o parágrafo de topo do módulo, ao explicar D-04, citava `options_provider_yahoo.py` e "Yahoo" por nome — os próprios critérios de aceite do plano proíbem essas strings literais no arquivo (para impedir reintrodução acidental de fallback).
- **Fix:** reescrita a explicação sem citar o nome do módulo nem "Yahoo" — fala de "o provedor anterior"/"aquele endpoint" mantendo o raciocínio de D-04 intacto.
- **Files modified:** `server/app/options_provider_mydata.py`
- **Verification:** `grep -c 'yahoo' server/app/options_provider_mydata.py` e `grep -c 'options_provider_yahoo' server/app/options_provider_mydata.py` → 0 nos dois
- **Committed in:** `1654619` (Task 2 feat commit)

**2. [Rule 1 - Bug/comentário] `agent.py:501` citava `options_provider_yahoo.get_options` como "em produção" depois da troca do import em `main.py`**
- **Found during:** Task 3, verificação do critério de aceite (`grep -rn 'options_provider_yahoo' server/app/ | grep -v ...` deve imprimir nada)
- **Issue:** `agent.py` não está na lista de `<files>` do plano, mas seu comentário sobre `option_quotes_getter` citava `options_provider_yahoo.get_options` por nome como o valor injetado "em produção" — agora factualmente incorreto, já que `main.py` passa `options_provider.get_options` (o seletor) em todos os 4 call sites de `option_quotes_getter=`.
- **Fix:** comentário atualizado para citar `options_provider.get_options` (o seletor), mantendo a explicação do padrão de injeção.
- **Files modified:** `server/app/agent.py`
- **Verification:** `grep -rn 'options_provider_yahoo' server/app/ | grep -v 'options_provider_yahoo.py:' | grep -v 'options_provider.py:' | grep -v '^server/app/candle_provider.py:7:'` → vazio
- **Committed in:** `d517755` (Task 3 feat commit)

**3. [Processo — não é Rule 1/2/3] Worktree nasceu um commit atrás do `base_commit` esperado**
- **Found during:** início da execução, `worktree_branch_check`
- **Issue:** HEAD do worktree estava em `4919558` (mesmo padrão relatado no 09-01-SUMMARY.md para o worktree daquele plano), atrás do `base_commit` `41105d2c...` esperado pelo protocolo de execução.
- **Fix:** `git reset --hard 41105d2c2a3f29365886730da111d1add956a6ac`, conforme instruído no `worktree_branch_check`. Working tree limpo no momento do reset, sem perda de trabalho. Confirmado depois que os 8 commits do Plano 09-01 (incluindo o merge) estavam presentes no histórico pós-reset.
- **Committed in:** n/a (correção de ambiente antes de qualquer edição)

---

**Total deviations:** 2 auto-fixes de comentário/docstring (Rule 1) + 1 nota de processo (ambiente do worktree). Nenhum desvio de escopo, nenhuma dependência nova, nenhum arquivo fora dos 9 do plano + `agent.py` (justificado pela Deviation 2).
**Impact on plan:** Nenhum ajuste mudou comportamento de produção — todos foram correções de texto (comentário/docstring) ou de ambiente. A implementação funcional é exatamente a desenhada no plano.

## Escopo negativo confirmado

- `options_provider_yahoo.py` NÃO foi apagado nem alterado (`git diff --stat` não lista o arquivo) — fica como código histórico/alavanca de rollback via `B3_OPTIONS_PROVIDER=yahoo` (que é, aliás, o default atual).
- `options_quant.py` NÃO foi alterado (`git diff --stat` não lista o arquivo) — o achado de `liquidity_score` sem `openInterest` foi medido e documentado, não corrigido.
- `docs/adr/004-fonte-de-opcoes-na-v2.md` NÃO foi reaberta (`git diff --stat` não lista o arquivo).
- Nenhum default de produção foi virado: `python -c "from app import options_provider as p; print(p.provider_name())"` sem env imprime `yahoo`.

## User Setup Required

None neste plano — `MYDATA_TOKEN`/`MYDATA_URL` continuam consumidos apenas em runtime quando `B3_OPTIONS_PROVIDER=mydata` for setado manualmente (nenhuma chamada real acontece nos testes, todos offline). O `B3_OPTIONS_PROVIDER` de produção continua sem essa variável definida, portanto o Railway segue servindo opções pelo Yahoo até o checkpoint do Plano 09-06.

## Next Phase Readiness

- `options_provider_mydata.get_options()` está pronto para ser ativado em produção só com `B3_OPTIONS_PROVIDER=mydata` no Railway — nenhum código adicional necessário.
- O Plano 09-04 (medição de rate-limit real) tem os dois números que precisava desta fase: custo de chamadas por cadeia completa (2, caso normal) e o achado de `liquidity_score` (52.0 medido, corte 40).
- O Plano 09-06 (checkpoint humano de virada de provedor) tem o achado de `openInterest`/`liquidity_score` para incluir na decisão.
- Nenhum bloqueio conhecido.

## Self-Check: PASSED

- FOUND: server/app/mydata_client.py
- FOUND: server/app/options_provider_mydata.py
- FOUND: server/app/options_provider.py
- FOUND: server/tests/test_options_provider_mydata.py
- FOUND: server/tests/test_options_provider.py
- FOUND: .planning/phases/09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa/09-03-SUMMARY.md
- FOUND commits: ae5bf77, 4ef5610, 2afe20d, 1654619, d517755, 29a2497, a123fa7 (verified via `git log --oneline --all`)
