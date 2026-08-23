---
phase: 05-corre-o-m-dio-c-digo-gate-admin
plan: 01
subsystem: testing
tags: [pytest, fastapi-testclient, store.py, guardian-test, buy-sell]

# Dependency graph
requires: []
provides:
  - "Guardião HTTP dos 4 caminhos de rejeição de /api/buy e /api/sell que não tinham teste de rota (FIX-C25)"
  - "Tabela de inventário auditada (9 caminhos reais, não os ~3 do achado original) apontando onde cada um é coberto"
  - "Guardião da reponderação de preço médio na recompra após venda parcial (FIX-C26), avg=35.00 travado, 33.75 explicitamente rejeitado"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Isolamento de TestClient por banco temporário + reimport de app.main (mesmo padrão de test_rotas_fase4.py FIX-C02)"
    - "Motor determinístico testado direto via store.buy/store.sell sem TestClient quando o teste não é sobre a rota HTTP"

key-files:
  created:
    - server/tests/test_fase5_rejeicao_rotas.py
    - server/tests/test_fase5_recompra_reponderacao.py
  modified: []

key-decisions:
  - "Inventário real de caminhos de rejeição é 9 (5 buy + 4 sell), não os ~7 aproximados no objetivo do plano — a diferença é o achado original não separar os dois ramos dentro/fora de pregão de /api/buy, nem os dois sub-casos de 'Quantidade inválida' em /api/sell. Documentado explicitamente no docstring do arquivo, sem reabrir o achado."
  - "Exemplo do 05-CONTEXT.md (buy(100@30) → sell(qty=40) → buy(60@40)) corrigido para buy(1000@30) → sell(qty=400) → buy(600@40) — a normalização de lote de 100 em store.py invalida os números originais, exatamente como o plano já alertava para verificar."

requirements-completed: [FIX-C25, FIX-C26]

# Metrics
duration: ~20min
completed: 2026-08-23
---

# Phase 05 Plan 01: Guardiões de rota de rejeição e reponderação de preço médio Summary

**Dois arquivos de teste novos travam 4 caminhos de rejeição HTTP descobertos em /api/buy e /api/sell (FIX-C25) e a reponderação de preço médio na recompra após venda parcial com avg=35.00 travado contra o valor errado 33.75 (FIX-C26) — zero mudança em server/app/.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-08-23T17:37:38Z
- **Tasks:** 2/2
- **Files modified:** 2 (ambos novos)

## Accomplishments
- Inventário auditado (não copiado do achado): 9 caminhos de rejeição HTTP reais em `/api/buy`/`/api/sell`, com tabela no docstring apontando arquivo de cobertura pra cada um — 5 já cobertos (4 pela Fase 4/FIX-C02, 1 por `test_ordens_pendentes_rotas.py` de uma fase anterior de MERC-02/03), 4 descobertos e agora fechados neste plano
- `store.buy`/`store.sell` reponderação de preço médio travada em nível de motor: `buy(1000@30) → sell(qty=400) parcial → buy(600@40)` resulta em `avg=35.00`, com asserção explícita que `avg != 33.75` (o valor que sairia se a reponderação usasse as 1000 cotas originais em vez das 600 remanescentes)
- Regra de normalização de lote de 100 documentada em teste — `sell(qty=40)` sobre uma posição de 100 vende a posição INTEIRA, não 40 (é essa regra que invalidava o exemplo original do 05-CONTEXT.md)

## Task Commits

Each task was committed atomically:

1. **Task 1: Guardião de rota dos caminhos de rejeição (FIX-C25)** - `7ae48c3` (test)
2. **Task 2: Guardião da reponderação na recompra após venda parcial (FIX-C26)** - `6a112da` (test)

_TDD não se aplica — plano de teste-guardião puro, sem código de produção a implementar._

## Files Created/Modified
- `server/tests/test_fase5_rejeicao_rotas.py` - 5 testes: ticker curto em `/api/buy` (400, novo), anônimo não grava (T-05-03), `/api/sell` sem cotação (502, novo), `/api/sell` qty não-inteiro (400, novo), `/api/sell` qty=0 (400, novo, regressão F10-20260819) — docstring com a tabela de inventário completa dos 9 caminhos
- `server/tests/test_fase5_recompra_reponderacao.py` - 4 testes: reponderação `avg=35.00`/rejeita `33.75`, PnL realizado proporcional + caixa final bate com a soma das 3 operações, histórico com 3 entradas executadas, normalização de lote (`sell(qty=40)` sobre 100 vende o total)

## Decisions Made
- Tabela de inventário construída por auditoria literal contra `main.py:1800-1960` em vez de aceitar a contagem aproximada ("7") do objetivo do plano — resultado real são 9 branches HTTP distintas. Não é uma reabertura do achado C-25 (que falava em "3 caminhos" na auditoria original de 2026-08-18): é a mesma correção estrutural que o plano já pedia ("Confirmar o inventário antes"), só que o número final ficou mais preciso que a estimativa do objetivo. Documentado no próprio docstring do arquivo para a próxima auditoria não reabrir sem saber onde olhar.
- Sequência de teste de FIX-C26 escalada ×10 em relação ao exemplo do 05-CONTEXT.md, exatamente como o próprio `05-01-PLAN.md` já instruía fazer (a conta original não roda no motor real por causa da normalização de lote de 100).

## Deviations from Plan

None - plan executado exatamente como especificado. A única diferença do plano é a contagem final do inventário (9 vs. a aproximação de 7 no objetivo), que é um refinamento de precisão da própria tarefa de auditoria pedida pelo plano, não uma mudança de escopo, bug ou achado de arquitetura — coberto acima em "Decisions Made", não como deviation de código.

## Issues Encountered
None - os dois arquivos passaram na primeira execução de `bash scripts/test.sh` (1334 passed, 1 skipped — os 4 anteriores já eram esperados: `test_fase5_recompra_reponderacao.py` roda depois no mesmo diretório e a suíte inteira sempre teve 1 skip pré-existente não relacionado a este plano).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- FIX-C25 e FIX-C26 fechados: nenhum bloqueio para os demais planos da Wave 1 (05-02..05-05), que tocam código de produção (`web/src/App.jsx`, `web-admin/src/App.jsx`, `server/app/main.py` em rotas diferentes) — sem overlap de arquivo com este plano.
- Nenhum código de produção foi tocado; a suíte canônica completa (`bash scripts/executar.sh --testes`) ainda precisa rodar no fechamento da fase (este plano só validou `bash scripts/test.sh`, conforme o `<verify>` do próprio plano).

---
*Phase: 05-corre-o-m-dio-c-digo-gate-admin*
*Completed: 2026-08-23*

## Self-Check: PASSED

- FOUND: server/tests/test_fase5_rejeicao_rotas.py
- FOUND: server/tests/test_fase5_recompra_reponderacao.py
- FOUND commit: 7ae48c3
- FOUND commit: 6a112da
