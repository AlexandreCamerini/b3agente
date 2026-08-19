---
phase: 02-realismo-de-mercado
plan: 06
subsystem: front-end / UI (web + iOS, mesmo bundle)
tags: [ordens-pendentes, MERC-02, MERC-03, MERC-04, BuyModal, SellModal, HistoricoScreen, copy.js]

requires:
  - phase: 02-realismo-de-mercado (plano 05)
    provides: "ctx.mercado ({aberto, diaDePregao, abertura, fechamento, agoraBRT, afterMarket} | null | {erro:true}) — fonte única de status de mercado no root de App(); MarketStatusBadge"
  - phase: 02-realismo-de-mercado (plano 04)
    provides: "data.pendingOrders/data.caixaReservado em public_state; store.cancelPendingOrder(id) nos dois stores; POST /api/buy|/api/sell devolvem {pendente:true, order, priceUsed:null, precoReferencia} com mercado fechado"
provides:
  - "BuyModal/SellModal: pill PENDENTE + disclaimer trocado quando ctx.mercado.aberto === false; aviso de status indisponível com retry (ctx.recarregarMercado) quando ctx.mercado.erro, sem bloquear o Confirmar"
  - "confirmBuy/confirmSell ramificam por `pendente` da resposta: toast de ordem pendente, sem abrir stop/alvo para uma posição que ainda não existe"
  - "HistoricoScreen: seção 'Pendentes' acima da tabela de operações (data.pendingOrders), só quando length > 0, com o total reservado (data.caixaReservado) e a linha de ultimoErro quando a ordem tentou executar e falhou"
  - "Cancelamento de ordem pendente em dois passos (ícone ✕ 40px → 'Manter ordem'/'Confirmar cancelamento'), A.cancelPendingOrder adota o public_state devolvido pelo servidor"
  - "Toast na abertura do app para ordem pendente auto-cancelada (agentLog tag=='pendente-cancelada'), com o texto do motor determinístico"
  - "copy.js: ordemPendentePill/ordemPendenteAvisoCompra/ordemPendenteAvisoVenda/mercadoStatusFalhouNaOrdem/toastOrdemPendente/toastOrdemPendenteCancelada nos dois modos"
affects: [02-07]

tech-stack:
  added: []
  patterns:
    - "ctx.recarregarMercado: função de retry exposta no ctx do root, reusando a MESMA função async do efeito de boot via useRef (consultarMercadoRef) — nunca uma segunda rota/consulta de status"
    - "Inspeção estática de App.jsx isolando o corpo de uma função top-level pelo balanceamento de chaves a partir de ') {' (não do primeiro '{' da desestruturação de props) — funcBody() em test_ordens_pendentes_ui.mjs, reusável por guardiões futuros que testem componentes com `({ ctx })` como assinatura"

key-files:
  created:
    - web/tests/test_ordens_pendentes_ui.mjs
  modified:
    - web/src/copy.js
    - web/src/App.jsx
    - web/src/persistence.js
    - web/tests/test_analytics_instrumentacao.mjs

key-decisions:
  - "deviceStore.buy/sell (persistence.js) passou a propagar `r.pendente` pra fora do método (out.pendente = !!(r && r.pendente)) — bug pré-existente descoberto durante a Task 1 (Rule 1): sem isto, o app nativo/iOS nunca saberia que uma ordem virou pendente, e confirmBuy tomaria o ramo de execução imediata, abrindo o modal de stop/alvo para uma posição que não existe. serverStore já funcionava (devolve a resposta crua da API, que já inclui `pendente`)."
  - "Tasks 2 e 3 do plano foram commitadas JUNTAS num único commit: a coluna de ação da seção Pendentes (Task 2) já nasce chamando A.cancelPendingOrder (Task 3) — a UI e a ação são a mesma peça de código, escrita de uma vez; separar os hunks produziria um commit intermediário funcionalmente quebrado (UI referenciando uma ação que ainda não existiria naquele ponto da história)."
  - "toastOrdemPendente(qty, t) é genérico (não menciona 'compra'/'venda') de propósito — é reusado tanto por confirmBuy quanto por confirmSell quando a ordem vira pendente, evitando duas chaves de copy quase idênticas."
  - "O título da seção usa texto sentence-case 'Pendentes' (não 'PENDENTES' all-caps) — o tratamento visual de kicker (10px MONO, letterSpacing, peso 700) já comunica hierarquia sem precisar de caixa alta; UI-SPEC não exige caixa alta literal, só o tratamento de kicker."
  - "Guardião test_analytics_instrumentacao.mjs (qa/47) foi atualizado com nota — não apagado — para aceitar a propriedade `pendente` nova no evento trade_simulated de ação (buyOption/sellOption ficam com o shape exato de antes, não passam por ordem pendente). Segue o guardrail do CLAUDE.md: 'guardiões de teste não se apagam — reversão deliberada atualiza o guardião com nota.'"

patterns-established: []

requirements-completed: [MERC-02, MERC-03, MERC-04]

duration: ~65min
completed: 2026-08-19
---

# Phase 2 Plan 06: Ordem Pendente na Interface (Modais, Histórico, Cancelamento) Summary

BuyModal/SellModal agora avisam ANTES da confirmação que uma ordem com o
mercado fechado fica pendente e reserva o caixa/posição na hora
(pill PENDENTE + disclaimer trocado, lendo `ctx.mercado` — mesma fonte única
do badge do plano 02-05); a ordem pendente aparece numa seção "Pendentes" no
topo do Histórico com o valor reservado e cancela em dois passos, com o
caixa/posição voltando na hora, a partir do estado que o SERVIDOR devolve
(nunca um palpite local).

## Performance

- **Duration:** ~65 min (leitura de contexto + self-heal de worktree
  desatualizado + 3 tasks TDD + 1 deviation de paridade de stores)
- **Started:** 2026-08-18T23:40Z (aprox., leitura de contexto)
- **Completed:** 2026-08-19T02:57Z
- **Tasks:** 3/3
- **Files modified:** 4 fonte/teste existentes (`copy.js`, `App.jsx`,
  `persistence.js`, `test_analytics_instrumentacao.mjs`) + 1 teste novo

## Accomplishments
- `copy.js`: 6 chaves novas por modo (`ordemPendentePill`,
  `ordemPendenteAvisoCompra(abertura)`, `ordemPendenteAvisoVenda(abertura)`,
  `mercadoStatusFalhouNaOrdem`, `toastOrdemPendente(qty, t)`,
  `toastOrdemPendenteCancelada`), simétricas (`test_copy_theme.mjs` continua
  verde), sem invenção de horário quando `abertura` não vem no payload
- `BuyModal`/`SellModal`: `fechado`/`statusIndisponivel` derivados de
  `ctx.mercado` (nunca uma segunda consulta); pill PENDENTE + disclaimer
  trocado quando fechado; aviso + botão "↻ Tentar de novo"
  (`ctx.recarregarMercado`) quando o status falhou — Confirmar continua
  habilitado, nunca presume aberto/fechado (CLAUDE.md princípio 4);
  validação de caixa insuficiente e rótulo do CTA (`confirmarCompra`/
  `confirmarVenda`) inalterados
- `confirmBuy`/`confirmSell`: ramificam por `s.pendente`/`st.pendente` —
  toast de ordem pendente em vez do toast de execução; `confirmBuy` PULA
  `setStopAlvoFor`/`A.runStopAlvoFor` quando pendente (não há posição para
  proteger ainda); `track("trade_simulated", ...)` ganha `pendente: bool`
- `HistoricoScreen`: seção "Pendentes" (mesmo tratamento visual da tabela:
  10px MONO kicker no cabeçalho, 13px MONO no dado) acima da tabela de
  operações, SÓ quando `data.pendingOrders.length > 0` (sem estado vazio
  próprio); subtítulo com `money(data.caixaReservado)`; pill sempre `T.warn`
  (nunca `T.positive`/`T.negative` — T-02-31); linha de `ultimoErro`
  visível quando a ordem tentou executar e falhou (princípio 4)
- Cancelamento: botão só-ícone ✕ 40px (`aria-label="Cancelar ordem
  pendente de {ticker}"`) → confirmação inline em dois passos ("Manter
  ordem" / "Confirmar cancelamento", estilo de `Excluir conta`); um
  `confirmando` por vez; botão de confirmar desabilitado enquanto a
  chamada está em voo; `A.cancelPendingOrder` adota o `public_state`
  DEVOLVIDO pelo servidor (`setData(s)`), erro vira `flash`, nunca finge
  sucesso local
- `agentSummaryDone`: passa a também filtrar `agentLog` por
  `tag === "pendente-cancelada"` e disparar `flash(e.text)` +
  `notify.send("Boris+", e.text)` com o texto ÍNTEGRO do motor
  determinístico (`pending_orders.py`), disparado por ÚLTIMO (depois do
  resumo de ações do agente) — sem isto o auto-cancelamento na abertura só
  aparecia no Diário do Operador (tela de diagnóstico)

## Task Commits

Todas as 3 tasks são `tdd="true"`; RED e GREEN ficaram no mesmo commit por
task (mesmo padrão documentado em 02-05: o guardião cresceu junto com a
implementação, não em ciclo RED→GREEN estritamente separado):

1. **Task 1: BuyModal/SellModal com estado "mercado fechado"** — `84cde02`
   (feat) — inclui a correção de paridade de stores (deviation Rule 1) e a
   atualização do guardião de analytics, ambas causadas por esta task
2. **Task 2 + Task 3: Seção "Pendentes" + cancelamento em dois passos** —
   `7b4b6f6` (feat) — commitadas juntas (ver `key-decisions`)

**Plan metadata:** commit ainda a fazer (`docs(02-06): complete plan`, após
este SUMMARY)

## Files Created/Modified
- `web/tests/test_ordens_pendentes_ui.mjs` — guardião novo (padrão A +
  inspeção estática de `App.jsx`, mesma técnica de
  `test_agente_modo_estudo_ui.mjs`/`test_status_mercado_ui.mjs`): simetria
  das 6 chaves novas de `copy.js`, ausência de invenção de horário,
  `BuyModal`/`SellModal` lendo `ctx.mercado`, `confirmBuy`/`confirmSell`
  ramificando por `pendente`, paridade de stores (a correção da deviation),
  seção Pendentes (render condicional, ausência de `T.positive`/
  `T.negative` no pill, linha de `ultimoErro`), filtro do toast de
  auto-cancelamento por `tag`, cancelamento em dois passos (aria-label,
  40px, os dois textos, `confirmando`, `enviando`)
- `web/src/copy.js` — 6 chaves novas por modo
- `web/src/App.jsx` — `BuyModal`/`SellModal` (pill + disclaimer + aviso de
  status indisponível), `consultarMercadoRef`/`ctx.recarregarMercado`,
  `confirmBuy`/`confirmSell` (ramo pendente), `HistoricoScreen` (seção
  Pendentes + confirmação de cancelamento), `A.cancelPendingOrder`,
  `agentSummaryDone` (toast de auto-cancelamento)
- `web/src/persistence.js` — `deviceStore.buy`/`sell` propagam
  `r.pendente` pra fora (deviation Rule 1)
- `web/tests/test_analytics_instrumentacao.mjs` — guardião atualizado com
  nota para aceitar `pendente: bool` no evento `trade_simulated` de ação

## Decisions Made
Ver `key-decisions` no frontmatter. Resumo: (1) `deviceStore.buy/sell`
ganhou a propagação de `r.pendente` — bug de paridade pré-existente,
descoberto e corrigido porque bloqueava a Task 1 no app nativo/iOS; (2)
Tasks 2+3 commitadas juntas por dependência funcional direta (UI chama a
ação na mesma peça de código); (3) `toastOrdemPendente` é genérico
(compra/venda) de propósito, para não duplicar quase-a-mesma-frase em
`copy.js`; (4) título "Pendentes" em sentence-case, não all-caps — o
tratamento de kicker já comunica hierarquia; (5) guardião de analytics
atualizado com nota, não apagado (CLAUDE.md).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] deviceStore.buy/sell não propagava `r.pendente` pra fora**
- **Found during:** Task 1 (implementação de `confirmBuy`/`confirmSell`
  ramificando por `s.pendente`/`st.pendente`)
- **Issue:** `web/src/persistence.js` — `deviceStore.buy(t, qty, meta)` e
  `deviceStore.sell(t, qty)`, no ramo COM sessão (`sync.hasSession()`),
  chamam `api.buy`/`api.sell`, adotam a carteira devolvida via
  `_adotarCarteiraDoServidor(r)` (que já cobre `pendingOrders`/
  `caixaReservado` desde o plano 02-04/02-05) e devolvem `out = pub()` com
  só `out.priceUsed = r && r.priceUsed`. O flag `r.pendente` da RESPOSTA
  (não persistido no `doc`, então `pub()` sozinho não o carrega) nunca
  chegava até o chamador. No app nativo/iOS, `confirmBuy` tomaria o ramo
  de execução imediata mesmo com o mercado fechado, chamando
  `setStopAlvoFor`/`A.runStopAlvoFor` para uma posição que ainda não
  existe — contradizendo diretamente um dos `must_haves.truths` do
  frontmatter deste plano ("Confirmar uma ordem pendente NÃO abre o fluxo
  de stop/alvo"). `serverStore` (web) já funcionava, porque devolve a
  resposta crua da API (que já inclui `pendente`) sem essa camada de
  adoção seletiva.
- **Fix:** `out.pendente = !!(r && r.pendente);` acrescentado logo após
  `out.priceUsed = r && r.priceUsed;` nos dois métodos, mesmo padrão já
  usado para `priceUsed`.
- **Files modified:** `web/src/persistence.js`
- **Verification:** `web/tests/test_ordens_pendentes_ui.mjs` trava a
  presença de `out.pendente = !!(r && r.pendente);` dentro do corpo de
  `buy`/`sell` de `persistence.js`; suíte canônica completa (`bash
  scripts/executar.sh --testes`) sai 0, incluindo `test_ordens_pendentes_client.mjs`
  e `test_api_parity.mjs` (nenhum dos dois cobria este campo antes —
  confirmado por leitura antes da correção).
- **Committed in:** `84cde02` (Task 1)

**2. [Guardião atualizado com nota] test_analytics_instrumentacao.mjs — shape do evento trade_simulated**
- **Found during:** Task 1 (`track("trade_simulated", ...)` ganhou a
  propriedade `pendente: bool` em `confirmBuy`/`confirmSell`, por
  instrução explícita do próprio plano: "Manter o
  `track("trade_simulated", ...)` mas acrescentar `pendente: true` às
  propriedades")
- **Issue:** o guardião pré-existente `test_analytics_instrumentacao.mjs`
  (qa/47) trava o shape EXATO do objeto de propriedades via regex —
  `\{ side: "buy", ticker: bm\.t, instrument: "equity" \}` sem a
  propriedade nova, quebrando com a mudança pedida pelo plano.
- **Fix:** as duas regexes de compra/venda de AÇÃO foram atualizadas para
  incluir `, pendente: !!s\.pendente`/`, pendente: !!st\.pendente`, com
  comentário explicando o motivo (mudança deliberada, não regressão). As
  regexes de compra/venda de OPÇÃO (`buyOption`/`sellOption`) ficaram
  intocadas — essas rotas não passam por ordem pendente.
- **Files modified:** `web/tests/test_analytics_instrumentacao.mjs`
- **Verification:** `node web/tests/test_analytics_instrumentacao.mjs`
  sai 0 (estava falhando com o shape antigo, confirmado antes da correção).
- **Committed in:** `84cde02` (Task 1)

---

**Total deviations:** 2 (1 auto-fixed — Rule 1 bug de paridade; 1 guardião
atualizado com nota, exigido pela própria instrução do plano)
**Impact on plan:** A correção de paridade é necessária para que o plano
funcione de verdade no app nativo/iOS (mesmo bundle do web) — sem ela, um
dos `must_haves.truths` do próprio plano ficaria falso nessa plataforma. A
atualização do guardião de analytics é consequência direta e esperada de
uma instrução explícita do plano, não uma descoberta incidental. Nenhum
scope creep: nenhuma funcionalidade fora do pedido foi adicionada.

## Issues Encountered

**1. Worktree nascido de base desatualizada (mesmo padrão de 02-01..02-05)**
- `grep -q "ctx.mercado" web/src/App.jsx && grep -q "cancelPendingOrder"
  web/src/persistence.js` retornou `STALE` no boot deste agente — a
  branch local estava em `403432f` (topo de `main`/identities), sem
  nenhum commit divergente próprio. `git merge
  claude/gsd-revisao-aplicacao-b9b4ef` rodou limpo (fast-forward-like,
  zero conflitos, `403432f` já era ancestral direto de `0270975`), trazendo
  `.planning/` inteiro e o trabalho dos planos 02-01..02-05 e da fase 3.

**2. `web/node_modules` não provisionado — resolvido por symlink, confirmado completo desta vez**
- Lockfile (`web/package-lock.json`) byte-idêntico ao da origem
  (`peaceful-swanson-e9e462/web/`), confirmado por `diff`. Symlink criado
  (`web/node_modules → .../peaceful-swanson-e9e462/web/node_modules`),
  usado só para rodar `npx vite build` e a suíte canônica completa, e
  removido antes de cada commit (não é rastreado pelo git — `node_modules/`
  está no `.gitignore` — mas symlinks não batem no padrão `node_modules/`
  com barra final, então apareciam como `??` no `git status`; removidos
  antes de cada `git commit` para manter o worktree limpo).
- **Diferente de 02-05**: desta vez o `node_modules` compartilhado JÁ
  incluía `@capacitor/browser` (instalado por um passo de workflow
  autorizado antes deste plano, conforme o SUMMARY de 02-05 recomendava).
  `npx vite build` rodou de verdade (pipeline completo do Vite/Rollup,
  não o substituto de `esbuild` usado em 02-05) e saiu 0 em TODAS as
  verificações, antes e depois de cada task.

**Suíte canônica (`bash scripts/executar.sh --testes`) — rodada de verdade, no estado final commitado:**
- Comando executado literalmente: `bash scripts/executar.sh --testes`.
- **Saída: exit 0.** Web: 82/82 arquivos `[OK]` — incluindo
  `test_ordens_pendentes_ui.mjs` (novo), `test_copy_theme.mjs`,
  `test_analytics_instrumentacao.mjs` (guardião atualizado),
  `test_ordens_pendentes_client.mjs`, `test_api_parity.mjs`,
  `test_status_mercado_ui.mjs`. Backend: 1076 passed.
- `cd web && npx vite build` — exit 0, pipeline completo (Vite 6.4.3 +
  plugin PWA), sem substituto.

## Known Precision Gaps (acceptance_criteria do plano, não funcionais)

Duas checagens `grep` literais do `<acceptance_criteria>` do plano não
batem por razões de sintaxe/naming que são inerentes ao próprio plano, não
bugs de implementação — documentado aqui para não serem re-litigadas como
"critério falhando" numa verificação futura:

1. **`grep -n 'aria-label="Cancelar ordem pendente de' web/src/App.jsx`
   não retorna linha.** O `aria-label` PRECISA variar por ticker (linha por
   linha da seção Pendentes), o que em JSX exige
   `aria-label={"Cancelar ordem pendente de " + o.t}` — o caractere logo
   após `aria-label=` é `{` (abertura de expressão), nunca `"` (string
   literal), então o grep literal do plano (que assume `aria-label="` sem
   o `{`) não pode bater com NENHUMA implementação que de fato interpola o
   ticker por linha, em JSX válido. Verificado funcionalmente por
   `web/tests/test_ordens_pendentes_ui.mjs` (regex `"Cancelar ordem
   pendente de " + o.t` presente no corpo de `HistoricoScreen`, mais o
   `40px` do botão gatilho) e visualmente pelo `npx vite build` limpo.
2. **`grep -c "toastOrdemPendente" web/src/copy.js` retorna 4, não 2.**
   As duas chaves do plano são `toastOrdemPendente` e
   `toastOrdemPendenteCancelada` — a segunda contém a primeira como
   substring, então um grep sem word-boundary conta as 2 ocorrências de
   `toastOrdemPendenteCancelada` (1 por modo) junto com as 2 de
   `toastOrdemPendente` (1 por modo) = 4. `mercadoStatusFalhouNaOrdem`
   (sem colisão de substring) bate exatamente em 2, confirmando que a
   implementação está correta — é só a superposição de nomes das DUAS
   chaves pedidas pelo próprio plano. `web/tests/test_ordens_pendentes_ui.mjs`
   usa `/toastOrdemPendente\b/g` (boundary-aware) e confirma 2/modo
   corretamente.

Nenhum dos dois indica um problema de implementação: o comportamento real
(aria-label por ticker; as 6 chaves de copy simétricas e presentes) foi
verificado com métodos mais precisos que a checagem literal do plano.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Next Phase Readiness

- MERC-02, MERC-03, MERC-04 completos do ponto de vista da interface: o
  ciclo de ordem pendente (avisar antes → mostrar no histórico → cancelar
  em dois passos → avisar se auto-cancelada) está fechado nos dois modos
  (Estudo/Operador) e nas duas plataformas (web/serverStore,
  iOS/deviceStore — paridade corrigida nesta plano).
- Plano 02-07 (verificação end-to-end da Fase 2, última wave) pode assumir
  que toda a superfície de UI de ordens pendentes existe: `ctx.mercado`,
  `MarketStatusBadge`, seção Pendentes, cancelamento, toast de
  auto-cancelamento.
- Nenhum bloqueio conhecido. `npx vite build` e a suíte canônica completa
  rodaram de verdade (não substituto) em todas as verificações deste plano.

---
*Phase: 02-realismo-de-mercado*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: web/tests/test_ordens_pendentes_ui.mjs
- FOUND: web/src/copy.js
- FOUND: web/src/App.jsx
- FOUND: web/src/persistence.js
- FOUND: web/tests/test_analytics_instrumentacao.mjs
- FOUND: .planning/phases/02-realismo-de-mercado/02-06-SUMMARY.md
- FOUND commit: 84cde02 (feat, Task 1 + deviation + guardian update)
- FOUND commit: 7b4b6f6 (feat, Task 2 + Task 3)
