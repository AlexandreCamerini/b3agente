---
phase: 06-instrumentacao-assertividade-adr015
plan: 04
subsystem: database
tags: [python, fastapi, sqlite, store, agent, adr-015, adr15-04, taxa-stop-alvo]

# Dependency graph
requires: []
provides:
  - "store.sell() com parâmetro motivo, mesmo contrato de sell_option() (ADR-005)"
  - "Call site automático de agent.py (venda por stop/alvo) grava motivo real no history"
  - "Taxa stop×alvo de carteira de AÇÃO agora computável a partir do history"
affects: [06-03-consolidacao-adr015]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "motivo (POR QUE vendeu) x origem (QUEM disparou) como eixos independentes — replicado de sell_option/ADR-005 para sell/ação"

key-files:
  created: []
  modified:
    - server/app/store.py
    - server/app/agent.py
    - server/tests/test_fase2_portfolio.py
    - server/tests/test_agent.py

key-decisions:
  - "Testes novos foram para server/tests/test_fase2_portfolio.py, não test_persistence.py como o plano citava — é onde os testes reais de compra/venda de ação já vivem (test_sell_total_comportamento_original etc.), seguindo CLAUDE.md ('um arquivo por feature, não por módulo')"
  - "motivo não é espelhado em web/src/persistence.js (deviceStore) — precedente ADR-012/origem: o campo pertence ao motor server-side, não à carteira local do iOS"

patterns-established:
  - "Vendas automáticas (stop/alvo) derivam motivo do MESMO booleano que decide o texto do Diário, sem reusar a variável do texto — evita que o vocabulário longo (Diário) e o vocabulário curto (campo estruturado) fiquem acoplados"

requirements-completed: [ADR15-04]

duration: ~35min
completed: 2026-08-21
---

# Phase 6 Plan 04: store.sell() ganha motivo, paridade com sell_option() Summary

**`sell()` de ação passa a gravar `motivo` ('manual'|'stop'|'alvo'|'vencimento'), mesmo contrato de `sell_option()` desde o ADR-005; o único call site automático em `agent.py` passa o motivo real derivado de `breach_stop`/`hit_alvo`.**

## Performance

- **Duration:** ~35 min
- **Tasks:** 3/3 completos
- **Files modified:** 4 (2 código, 2 teste)

## Accomplishments
- `store.sell()` tem paridade de assinatura com `store.sell_option()`: `(..., motivo: str = "manual", origem: str = "manual")`
- Venda automática do Operador (stop rompido / alvo atingido) grava `motivo` estruturado no `history`, não só o texto do Diário
- Aritmética de PnL/caixa/posição parcial intocada — mudança puramente de instrumentação
- Suíte canônica completa (`bash scripts/executar.sh --testes`) verde: 1117 testes pytest + 87 suítes `.mjs`

## Task Commits

Cada task foi commitada atomicamente (TDD RED→GREEN nas tasks 1 e 2):

1. **Task 1: store.sell() aceita e persiste `motivo`**
   - `33534ef` test(06-04): venda de ação passa motivo, contrato paridade com sell_option (RED)
   - `c2c2989` feat(06-04): sell() aceita motivo, paridade de contrato com sell_option (GREEN)
2. **Task 2: ciclo automático do Operador passa o motivo real**
   - `7757c6a` test(06-04): ciclo automático grava motivo real (stop/alvo) no histórico (RED)
   - `83b8b69` feat(06-04): call site automático de store.sell passa motivo real (GREEN)
3. **Task 3: verificação canônica + registro da divergência do ROADMAP** — sem commit de código (só verificação + este SUMMARY)

**Plan metadata:** (commit deste SUMMARY, a seguir)

## Files Created/Modified
- `server/app/store.py` — `sell()` ganha `motivo: str = "manual"` antes de `origem`; `"motivo": motivo` no dict do `history`; docstring estendida com o contrato motivo×origem e a nota de compatibilidade retroativa
- `server/app/agent.py` — call site de `store.sell` (linha 861) passa `motivo="stop" if breach_stop else "alvo"`; comentário ganha `ADR15-04` ao lado de `ADR-012 (Fase 3)`
- `server/tests/test_fase2_portfolio.py` — 4 testes novos: default `manual`, eixos independentes motivo/origem, parcial preserva avg/pnl com motivo, venda sem posição continua `None`
- `server/tests/test_agent.py` — 2 testes novos ao lado de `test_executa_venda_no_stop_e_registra_log`: venda por stop grava `motivo='stop'`, venda por alvo grava `motivo='alvo'`

## Decisions Made
- Arquivo de teste real dos casos de `sell()` de ação diverge do citado no plano (`test_persistence.py`): os testes de compra/venda vivem em `test_fase2_portfolio.py` (ver `test_sell_total_comportamento_original`, `test_sell_parcial_reduz_qty_e_preserva_preco_medio`). Coloquei os 4 casos novos lá, ao lado dos existentes — é o "estilo dos testes vizinhos" que o `read_first` do plano pedia, só que num arquivo diferente do citado. `pytest tests/test_persistence.py -q` (critério de aceite literal do plano) continua passando (30 testes, nenhum quebrado) porque a mudança não toca nada daquele arquivo.
- Não espelhar `motivo` em `web/src/persistence.js` (deviceStore): mesmo precedente de `origem` (ADR-012) — o campo é do motor server-side; a venda local do iOS (`deviceStore`, linha ~1075) já não carrega `origem` e não precisa carregar `motivo`.

## Deviations from Plan

### Auto-fixed Issues

Nenhuma — plano executado como escrito, à exceção da localização do arquivo de teste (documentada acima em "Decisions Made", não é uma correção de bug/funcionalidade faltante, é uma correção de referência de arquivo dentro do escopo já previsto pela task).

---

**Total deviations:** 0 auto-fixed
**Impact on plan:** Nenhum. A única discrepância (arquivo de teste) foi resolvida seguindo a intenção explícita do `read_first` ("colocar os novos ao lado" dos testes de compra/venda existentes) em vez do nome de arquivo citado, que não correspondia ao repo real.

## Issues Encountered
- Worktree nasceu sem `server/.venv` próprio (só existe no repo principal) e sem `web/node_modules` — usei o `.venv` do repo principal (mesmo Python/deps) e rodei `npm install` em `web/` antes da suíte canônica, como o achado já documentado em `PROJECT.md` ("Achado da auditoria: rodar num worktree/checkout novo sem `web/node_modules` instalado faz 7 testes web falharem por ambiente").

## Emenda pendente no ROADMAP — critério 4

O critério 4 da Phase 6 no `.planning/ROADMAP.md` hoje diz que **"os 3 call sites automáticos em `agent.py` passam o motivo real"**. Verificado por grep: existe **1 único** call site automático de `store.sell` em `agent.py` — o de opções (`store.sell_option`) já passava `motivo` desde o ADR-005, antes desta fase.

Evidência (saída do grep, colada literalmente):

```
$ grep -n "store.sell(" server/app/agent.py | grep -v sell_option
861:        store.sell(conn, pos["t"], price, user_id=scope, motivo="stop" if breach_stop else "alvo",
```

O call site da linha ~580 (`_avaliar_opcoes`) é `store.sell_option(conn, pos["id"], price, user_id=scope, motivo=motivo, origem="automatico")` — já passa `motivo` desde o ADR-005, não é um call site novo desta fase.

**Texto de substituição literal a aplicar no critério 4:**

> 4. `store.sell()` aceita `motivo` com o mesmo contrato de `sell_option()` (`'manual'|'stop'|'alvo'|'vencimento'`); o ÚNICO call site automático de `store.sell` em `agent.py` (linha ~852) passa o motivo real (`breach_stop`/`hit_alvo`) — os demais call sites (`pending_orders.py`, rota `/api/sell`) são vendas pedidas pelo usuário e ficam no default `'manual'`. [ADR15-04]

Decisão de não espelhar `motivo` no `deviceStore`, com precedente: registrado acima em "Decisions Made" (ADR-012/`origem` é o precedente — campo do motor server-side, `deviceStore` já não carrega `origem` e continua sem carregar `motivo`).

Quem edita `.planning/ROADMAP.md` é o Plano 03 (Task 3) — este plano só registra a evidência para a emenda, não escreve no arquivo (duas plans da mesma wave não escrevem no mesmo arquivo).

## User Setup Required

None - nenhuma configuração de serviço externo necessária.

## Next Phase Readiness
- Taxa stop×alvo de carteira de AÇÃO agora é computável a partir do `history` (campo `motivo` estruturado), pré-requisito de dado para qualquer plano de Phase 6 que meça essa taxa (ex.: 06-03 consolidação)
- Divergência do critério 4 do ROADMAP documentada com evidência, pronta para o Plano 03 aplicar a emenda
- Nenhum bloqueio conhecido

---
*Phase: 06-instrumentacao-assertividade-adr015*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: .planning/phases/06-instrumentacao-assertividade-adr015/06-04-SUMMARY.md
- FOUND: 33534ef (test RED, Task 1)
- FOUND: c2c2989 (feat GREEN, Task 1)
- FOUND: 7757c6a (test RED, Task 2)
- FOUND: 83b8b69 (feat GREEN, Task 2)
