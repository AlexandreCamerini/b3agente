---
phase: 02-realismo-de-mercado
plan: 01
subsystem: backend / motor de ordens
tags: [pending-orders, market-realism, MERC-02, MERC-03, MERC-04]
dependency-graph:
  requires: []
  provides:
    - server/app/pending_orders.py (criar_compra, criar_venda, cancelar, executar_pendentes, listar, caixa_reservado, qty_reservada)
    - store.ORDER_LOCK (trava única de processo)
    - kv section "pendingOrders" + public_state.caixaReservado
    - store.scopes_com_pendentes
  affects:
    - server/app/store.py
    - server/app/defaults.py
tech-stack:
  added: []
  patterns:
    - "trava única de processo (threading.RLock), definida no dono dos dados (store.py) e aliasada por quem também precisa dela"
    - "price_getter injetável (sync ou async, resolvido via inspect.isawaitable), no contrato de candle_provider.get_quote"
key-files:
  created:
    - server/app/pending_orders.py
    - server/tests/test_ordens_pendentes.py
  modified:
    - server/app/store.py
    - server/app/defaults.py
decisions:
  - "caixa_reservado vive em store.py (não em pending_orders.py) para public_state poder chamá-lo sem import circular; pending_orders.caixa_reservado delega para lá (fonte única)"
  - "kind:\"buy\" reusado para o evento de execução bem-sucedida tanto de compra quanto de venda pendente, seguindo o precedente já existente em agent.py (linha 716, onde store.sell também loga kind:\"buy\")"
metrics:
  duration: "~45min"
  completed: 2026-08-18
---

# Phase 2 Plan 01: Motor de Ordens Pendentes Summary

Motor determinístico de ordens pendentes (`server/app/pending_orders.py`) —
reserva de caixa/posição no momento do pedido, cancelamento com devolução
imediata, e execução ao preço do motor de cotações via `price_getter`
injetável, tudo protegido por uma trava única de processo compartilhada com
o caminho de ordem imediata.

## What Was Built

1. **`server/app/pending_orders.py`** (módulo novo): `criar_compra`/
   `criar_venda` reservam caixa/posição na hora do pedido (D-02/D-05/D-06),
   sem tocar `history`; `cancelar` devolve imediatamente (D-03), reponderando
   `avg` se o usuário recomprou o ticker no meio do caminho; `executar_pendentes`
   (async) aplica o preço vindo de um `price_getter` injetável — nunca a
   `precoReferencia` — reusando `store.buy`/`store.sell` para o débito real
   (D-01/D-05). Exceções de domínio nomeadas: `CaixaInsuficiente`,
   `PosicaoInsuficiente`, `OrdemNaoPendente` (padrão `brapi.ForaDoPlano`).

2. **`store.ORDER_LOCK`** (`threading.RLock()`, único no backend) — nasce em
   `store.py` porque é lá que `cash`/`positions` moram; `pending_orders.
   ORDER_LOCK` é um ALIAS do mesmo objeto (identidade verificada em teste),
   para o plano 02-02 (`/api/buy`/`/api/sell`) adquirir exatamente esta
   trava e não colidir com a execução de pendentes no scheduler.

3. **Auto-cancelamento na abertura**: se o preço de execução subir o
   suficiente para o caixa reservado + caixa livre não cobrir mais o custo,
   a ordem é cancelada automaticamente, o caixa reservado volta integralmente,
   e um evento `kind:"warn"`/`tag:"pendente-cancelada"` é gravado em
   `agentLog` — o scheduler (02-03) e o app (02-06) filtram por essa tag para
   avisar o usuário sem varrer todo `warn` do agente (T-02-36).

4. **Ligação ao estado** (`server/app/defaults.py`, `server/app/store.py`):
   `default_state()["pendingOrders"] = []`; `SECTIONS` (e portanto
   `USER_SECTIONS`, que herda automaticamente) ganham a seção; `public_state`
   expõe `pendingOrders` e `caixaReservado` (derivado); `scopes_com_pendentes`
   é o que o scheduler vai varrer.

## Verification

- `cd server && ./.venv/bin/python -m pytest -q tests/test_ordens_pendentes.py` — 26 testes (mínimo pedido: 8 na Task 1, 18 na Task 2).
- `cd server && ./.venv/bin/python -m pytest -q tests/test_ordens_pendentes.py tests/test_persistence.py` — 62 testes.
- `cd server && ./.venv/bin/python -m pytest -q tests/` (suíte backend inteira) — **1002 passed**.
- `bash scripts/executar.sh --testes` (suíte canônica) — **saiu com código
  de erro (7 falhas)**, NÃO zero: backend 1002 passed (todos verdes), mas
  67/74 arquivos `web/tests/*.mjs` OK e 7 falhando. As 7 falhas têm causa
  raiz idêntica e ambiental (`web/node_modules/@capacitor/*` ausente neste
  worktree), não uma regressão deste plano — que não tocou nenhum arquivo
  de `web/`. Ver "Known Issues" abaixo e `deferred-items.md`. O orquestrador
  NÃO deve tratar a suíte canônica como 100% verde sem antes rodar `npm
  install` em `web/` (ou confirmar que o ambiente de destino já a tem).
- Todos os greps de `acceptance_criteria` do PLAN.md confirmados manualmente
  (símbolos exatos, `ORDER_LOCK` único, alias por identidade, `with ORDER_LOCK`
  ≥ 2 ocorrências, zero escrita em `history`, `origem="pendente"` nas duas
  chamadas, `precoReferencia` nunca como argumento de execução, cotação obtida
  fora do lock, tags `pendente-cancelada`/`pendente-executada` presentes).
- Nenhum arquivo de front foi tocado — `npx vite build` não se aplica a este
  plano.

## Deviations from Plan

### TDD sequencing note (not a Rule 1-4 deviation, process note)

Task 1 e Task 2 têm `tdd="true"`. O módulo `pending_orders.py` nasceu numa
única passada de escrita cobrindo TODAS as funções do plano (Task 1 +
Task 2), então o ciclo RED→GREEN estrito só pôde ser aplicado à Task 1 (commit
`b8f5f7f` RED, `16ba419` GREEN — verificado: `ImportError` antes, 13 testes
passando depois). A Task 2 (`cancelar`/`executar_pendentes`) já estava
implementada dentro do GREEN da Task 1; o commit `7d21fa4` da Task 2 é
guardião puro (tests-only, todos os 26 testes do arquivo passam ao final),
não um RED→GREEN novo. Nenhum código de produção ficou sem teste — os 26
testes cobrem integralmente o `<behavior>` de ambas as tasks — mas a
sequência de commits não segue literalmente "RED falha, GREEN implementa" na
Task 2. Documentado aqui em vez de reescrever a história do módulo.

### Nenhum outro desvio

O restante da execução seguiu o plano à risca: nomes de função, formato do
registro, mensagens de erro em PT-BR idênticas às rotas atuais, semântica de
`_restaurar_posicao` como inverso exato da reserva, e a arquitetura de trava
única exatamente como especificado.

## Known Issues (not blocking this plan)

- **Web test suite environment gap.** `bash scripts/executar.sh --testes`
  reporta 7 arquivos `web/tests/*.mjs` falhando (`test_appmode_sincroniza_
  servidor.mjs`, `test_carteira_nativa_sincroniza.mjs`, `test_fase2_
  portfolio.mjs`, `test_notif_central.mjs`, `test_notify.mjs`, `test_oauth_
  repassa_name_e_code.mjs`, `test_pet_resumo_modo_web.mjs`), todos com a
  MESMA causa raiz: `Cannot find package '@capacitor/core'` — `web/
  node_modules/@capacitor/*` não está instalado neste worktree isolado
  (`web/package.json` declara a dependência, mas `npm install` nunca rodou
  para `web/` aqui). Este plano não tocou nenhum arquivo de `web/` — é um gap
  de provisionamento do worktree, não uma regressão de código. Por política
  (exclusão de instalação de pacote do Rule 3), este executor não roda `npm
  install` unilateralmente. Sinalizado para o orquestrador/humano: rodar
  `npm install` dentro de `web/` neste worktree (ou confirmar que o
  merge/branch de destino já tem os `node_modules` instalados) antes de
  tratar a suíte canônica como 100% verde. Detalhe em
  `.planning/phases/02-realismo-de-mercado/deferred-items.md`.

## Known Stubs

Nenhum. Este plano é backend puro, sem UI — não há dado renderizado
vazio/placeholder a rastrear.

## Threat Flags

Nenhum achado fora do `<threat_model>` do plano. Toda a superfície nova
(reserva de caixa/posição, trava de processo, execução com preço injetável,
auto-cancelamento) já estava mapeada no STRIDE register do PLAN.md (T-02-01
a T-02-06, T-02-36) e implementada conforme a mitigação descrita lá.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 (RED) | `b8f5f7f` | test(02-01): guardioes do ciclo de vida de ordens pendentes (RED) |
| 1 (GREEN) | `16ba419` | feat(02-01): motor de ordens pendentes — modelo, trava e criacao com reserva (GREEN) |
| 2 | `7d21fa4` | test(02-01): guardioes de cancelamento e execucao de ordens pendentes |
| 3 | `125be17` | feat(02-01): liga pendingOrders ao estado (defaults, SECTIONS, public_state, scopes) |

## Self-Check: PASSED

- FOUND: server/app/pending_orders.py (312 lines, min_lines required: 150)
- FOUND: server/tests/test_ordens_pendentes.py
- FOUND: commit b8f5f7f
- FOUND: commit 16ba419
- FOUND: commit 7d21fa4
- FOUND: commit 125be17
