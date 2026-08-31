---
phase: 14-opcoes-lastreadas
plan: 05
subsystem: ui
tags: [options, portfolio-engine, covered-call, protective-put, frontend, parity, ios-local-first]

# Dependency graph
requires:
  - phase: 14-opcoes-lastreadas
    plan: "01"
    provides: "store.qty_livre (server/app/store.py) — gêmeo backend da fonte única de quantidade vendável"
  - phase: 14-opcoes-lastreadas
    plan: "02"
    provides: "abrir_call_coberta/fechar_call_coberta/comprar_put_protecao + formato aditivo optionPositions (side/lastro)"
  - phase: 14-opcoes-lastreadas
    plan: "03"
    provides: "GET /api/options/proposta/{ticker}, POST /api/options/lastreada/abrir|fechar"
  - phase: 14-opcoes-lastreadas
    plan: "04"
    provides: "agent._avaliar_opcoes com ramo lastreado — referência espelhada no ciclo local do deviceStore"
provides:
  - "api.js: optionsProposta/optionsAbrirLastreada/optionsFecharLastreada"
  - "persistence.js: os três métodos nos DOIS stores (serverStore delega direto; deviceStore espelha a aritmética do backend quando sem sessão, adota o estado do servidor quando logado)"
  - "finance.js: qtyLivre(pos) — fonte única da quantidade vendável do front, gêmeo de store.qty_livre"
  - "finance.js: portfolioMetrics estendida (5º/6º argumentos opcionais) somando as pernas lastreadas no Patrimônio Total (D-6)"
affects: [14-06, 14-07, 14-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fonte única de aritmética entre camadas do front: qtyLivre vive só em finance.js, importada por persistence.js — mesmo padrão já usado por RR_MIN/RR_MIN_TXT (guardião estático de fonte única, não runtime)"
    - "Extensão ADITIVA de assinatura: portfolioMetrics ganha 2 parâmetros opcionais no final — todo call site antigo (7 em App.jsx, chamadas com 3/4 args nos testes) continua produzindo o mesmo resultado, sem migração"
    - "Abrir/fechar de operação lastreada são chamada DIRETA nos dois stores, nunca sync.mutate/outbox — mesma decisão já registrada para buy/sell/cancelPendingOrder (reaplicar de fila offline devolveria caixa duas vezes)"

key-files:
  created:
    - web/tests/test_opcoes_lastreadas_stores.mjs
  modified:
    - web/src/api.js
    - web/src/persistence.js
    - web/src/finance.js
    - web/tests/test_finance.mjs

key-decisions:
  - "qtyLivre(pos) definida em finance.js exatamente como store.qty_livre (server/app/store.py): max(0, qty - qtyTravada), defensiva a pos nulo. persistence.js IMPORTA, nunca reimplementa a subtração — negativa testada por regex no guardião novo."
  - "deviceStore.optionsAbrirLastreada determina CALL coberta vs PUT de proteção pelo optionType do contrato na cadeia (mesma lógica da rota HTTP em main.py) — o corpo da chamada não carrega um campo 'tipo' explícito, o front replica a mesma inferência do backend."
  - "Ciclo local (deviceStore.cycle) trata posição com lastro como liquidação MECÂNICA obrigatória no vencimento — ao contrário do ramo legado (gated por doc.agent.autonomous), o ramo lastreado sempre liquida e sai com continue, espelhando agent._avaliar_opcoes (Plano 04: 'roda igual com o Operador ligado ou desligado')."
  - "portfolioMetrics: só posições de opção com lastro entram no Patrimônio Total — filtro não-retroativo (D-6/14-CONTEXT.md, discricionariedade fechada como 'não migra dado antigo'). Put comprada soma como ativo; call vendida entra como passivo de recompra negativo em posVal, sem tocar cost (prêmio já está em cash)."
  - "Marcação das pernas lastreadas no Patrimônio Total usa o prêmio de ABERTURA por padrão (optionQuotes vazio) — a tela de Carteira não dispara uma chamada de cadeia por posição nesta fase, para não gastar orçamento do mydata (ADR-020) numa tela que já está sob o mesmo bloqueio de produção."

requirements-completed: []

# Metrics
duration: ~35min
completed: 2026-08-31
---

# Phase 14 Plan 05: Camada de dados do front — cliente HTTP, paridade dos dois stores e Patrimônio Total lastreado Summary

**Os três métodos novos de opções lastreadas (proposta/abrir/fechar) simétricos em `serverStore`×`deviceStore`, `qtyLivre(pos)` como fonte única de quantidade vendável no front (gêmeo de `store.qty_livre`), e `portfolioMetrics` somando a perna lastreada (put=ativo, call vendida=passivo) sem quebrar nenhum dos 7 call sites existentes em `App.jsx`.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-08-31T10:40:38Z
- **Tasks:** 3/3
- **Files modified:** 5 (1 criado: `test_opcoes_lastreadas_stores.mjs`; 4 modificados: `api.js`, `persistence.js`, `finance.js`, `test_finance.mjs`)

## Accomplishments
- `api.js`: `optionsProposta` (GET, timeout 30s — mesmo motivo de `optionsChain`/`optionsGate`, a rota busca cadeia+candles), `optionsAbrirLastreada`/`optionsFecharLastreada` (POST, timeout padrão).
- `persistence.js` `serverStore`: delegação direta das três chamadas, com comentário explícito de por que são chamada DIRETA (nunca fila otimista).
- `persistence.js` `deviceStore`: `optionsProposta` sempre delega (dado de mercado nunca se duplica no aparelho); `optionsAbrirLastreada`/`optionsFecharLastreada` adotam o estado do servidor quando logado e espelham a aritmética de `store.py.abrir_call_coberta`/`comprar_put_protecao`/`fechar_call_coberta` quando sem sessão (mesma ordem de validação: cadeia → contrato → prêmio → lastro → caixa).
- `deviceStore.sell` (ramo local): a venda agora é limitada por `qtyLivre(pos)`, não `pos.qty` — ação travada como lastro de uma CALL coberta não sai mais pelo caminho local do iPhone; `livre == 0` vira rejeição registrada, sem tocar caixa.
- `deviceStore.cycle` (ramo local): posição com `lastro` ganha ramo próprio ANTES do bloco legado de stop/alvo — vencimento liquida pela regra nova (call vendida: recompra sintética pelo intrínseco + destrava; put comprada: reusa `_sellOptionLocal`), não vencida sai com `continue` sem avaliar stop/alvo.
- `finance.js`: `qtyLivre(pos)` — fonte única da quantidade vendável no front, MESMO nome e semântica de `store.qty_livre`; `persistence.js` importa, nunca reimplementa.
- `finance.js`: `portfolioMetrics(positions, quotes, cash, reservado, optionPositions, optionQuotes)` — extensão aditiva com 2 parâmetros opcionais; devolve `opcoesVal`/`opcoesPnL` novos no objeto de retorno. Só posições com `lastro` entram; put soma como ativo, call vendida entra como passivo de recompra; `posVal` de ação continua contando a posição inteira (travada ou não).
- `web/tests/test_opcoes_lastreadas_stores.mjs` (novo): guardião estático — paridade dos 3 métodos nos dois stores, ramo local de abertura (crédito + débito + escrita de `qtyTravada`), fonte única de `qtyLivre` (import, ≥2 usos, negativa contra subtração crua e contra helper privado `_qtyLivre`), ordem do ramo `lastro` no ciclo (antes do stop/alvo legado), e ausência de `sync.mutate` nos três métodos.
- `web/tests/test_finance.mjs`: compatibilidade de 4 argumentos, put/call com sinal correto de `opcoesVal`/`opcoesPnL`, posição sem `lastro` fora do agregado, marcação sem `optionQuotes` cai no `avg`, `posVal` de ação conta a posição inteira mesmo travada, e bateria unitária de `qtyLivre` (espelho de `test_lastro_trava.py` do backend).
- Suíte canônica completa verde: `bash scripts/executar.sh --testes` — `1805 passed, 1 skipped` (pytest) + `108/108` `web/tests/*.mjs` `[OK]` (nenhum arquivo `.jsx` tocado neste plano, confirmado por `git diff --name-only | grep -c jsx` = 0).

## Task Commits

Each task was committed atomically:

1. **Task 1: Cliente HTTP e delegação do serverStore** - `3277810` (feat)
2. **Task 2: qtyLivre em finance.js e deviceStore — espelho local da mecânica lastreada e da trava** - `cd65e0a` (feat)
3. **Task 3: Patrimônio Total inclui as pernas lastreadas** - `39c5fbf` (feat)

_Note: nenhuma task era TDD — plano `autonomous: true`, sem checkpoints._

## Files Created/Modified
- `web/src/api.js` - 3 chamadas novas (`optionsProposta`/`optionsAbrirLastreada`/`optionsFecharLastreada`)
- `web/src/persistence.js` - 3 métodos novos nos DOIS stores; `qtyLivre` importada de `finance.js`; trava de venda local usa `qtyLivre`; ciclo local ganha ramo `lastro`
- `web/src/finance.js` - `qtyLivre(pos)` (fonte única) + `portfolioMetrics` estendida (aditivo)
- `web/tests/test_opcoes_lastreadas_stores.mjs` - guardião novo (paridade + fonte única + ordem do ciclo)
- `web/tests/test_finance.mjs` - testes de `qtyLivre` e das pernas lastreadas em `portfolioMetrics`

## Decisions Made
- `qtyLivre` segue exatamente o padrão de fonte única já estabelecido por `RR_MIN`/`RR_MIN_TXT` neste mesmo arquivo — comentário no cabeçalho cita o precedente explicitamente, para a regra ficar visível como padrão da casa.
- `deviceStore.optionsAbrirLastreada` infere CALL coberta vs. PUT de proteção pelo `optionType` do contrato na cadeia (não há campo `tipo` no corpo da chamada) — mesma inferência que a rota HTTP faz em `main.py`.
- Liquidação por vencimento do ramo `lastro` no ciclo local NÃO é condicionada a `doc.agent.autonomous` (diferente do ramo legado logo abaixo) — é mecânica obrigatória, espelhando a decisão já tomada em `agent._avaliar_opcoes` (Plano 04).
- `portfolioMetrics` não busca cotação ao vivo por posição de opção na tela de Carteira — decisão explícita registrada em comentário (orçamento do mydata, ADR-020); a perna é marcada pelo prêmio de abertura até um plano futuro decidir buscar isso.

## Deviations from Plan

None - plano executado exatamente como especificado. As três tasks seguiram a ordem de validação, os nomes de campo e a assinatura descritos no `<action>` de cada task; nenhum ajuste de Rule 1/2/3/4 foi necessário.

## Issues Encountered
- `server/.venv` e `web/node_modules` ausentes neste worktree (mesmo padrão já documentado nos planos 14-01 a 14-04) — resolvido com symlinks temporários para o clone principal, usados só para rodar os testes incrementais e a suíte canônica completa; removidos antes de cada commit (não aparecem em nenhum `git status`/commit deste plano).

## User Setup Required

None - nenhuma configuração de serviço externo necessária. A camada de dados depende só das rotas já criadas no Plano 03 (dormentes em produção até a virada do `B3_OPTIONS_PROVIDER=mydata`, per 14-CONTEXT.md).

## Next Phase Readiness
- `store.optionsProposta/optionsAbrirLastreada/optionsFecharLastreada` estão prontos para os próximos planos (14-06/14-07, UI) chamarem via `store.*`, com paridade garantida nos dois stores.
- `qtyLivre` está pronta para `App.jsx` importar (mencionado no `must_haves` do plano) — nenhum consumidor de UI foi tocado neste plano, por desenho.
- `portfolioMetrics` já devolve `opcoesVal`/`opcoesPnL` para a UI discriminar a perna lastreada do Patrimônio Total sem recalcular nada.
- Nenhum bloqueio conhecido para os próximos planos da fase.

---
*Phase: 14-opcoes-lastreadas*
*Completed: 2026-08-31*

## Self-Check: PASSED

- FOUND: web/src/api.js
- FOUND: web/src/persistence.js
- FOUND: web/src/finance.js
- FOUND: web/tests/test_opcoes_lastreadas_stores.mjs
- FOUND: web/tests/test_finance.mjs
- FOUND: .planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/14-05-SUMMARY.md
- FOUND commit 3277810 (Task 1)
- FOUND commit cd65e0a (Task 2)
- FOUND commit 39c5fbf (Task 3)
