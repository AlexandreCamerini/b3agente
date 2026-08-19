---
phase: 02-realismo-de-mercado
plan: 04
subsystem: front-end / camada de estado (web + iOS)
tags: [pending-orders, market-status, MERC-01, MERC-04, deviceStore, serverStore, parity-guardian]

requires:
  - phase: 02-realismo-de-mercado (plano 02)
    provides: "GET /api/market/status (público), DELETE /api/orders/pending/{id}, pendingOrders/caixaReservado em public_state"
provides:
  - "api.marketStatus() e api.cancelPendingOrder(id) no cliente HTTP"
  - "pendingOrders/caixaReservado espelhados nos DOIS stores (deviceStore e serverStore)"
  - "cancelPendingOrder e marketStatus com o mesmo contrato nos DOIS stores"
  - "portfolioMetrics(positions, quotes, cash, reservado) — patrimônio conta o caixa reservado"
  - "guardião de paridade estático (web/tests/test_ordens_pendentes_client.mjs)"
affects: [02-05, 02-06, 02-07]

tech-stack:
  added: []
  patterns:
    - "Guardião de paridade por inspeção estática (readFileSync + regex >= 2 ocorrências) — mesmo padrão de test_didatica_parity.mjs/test_deep_parity.mjs"
    - "marketStatus roda ANTES do login (D-08): delegação pura nos dois stores, sem ensure()/sync.hasSession()"
    - "cancelPendingOrder é chamada DIRETA (fora de sync.mutate/outbox) no serverStore, mesma decisão de buy/sell — evita devolver caixa duas vezes numa reaplicação offline"

key-files:
  created:
    - web/tests/test_ordens_pendentes_client.mjs
  modified:
    - web/src/api.js
    - web/src/persistence.js
    - web/src/finance.js
    - web/tests/test_finance.mjs

key-decisions:
  - "deviceStore.cancelPendingOrder SEM sessão levanta erro explícito ('Ordens pendentes exigem conta conectada.') em vez de implementar o motor de pendentes local — evita segunda fonte de verdade financeira em JS (princípio 5 do CLAUDE.md); login é obrigatório no produto de qualquer forma"
  - "portfolioMetrics ganhou 4º parâmetro OPCIONAL (reservado, default 0) em vez de mudar a assinatura dos 7 call sites existentes — retrocompatibilidade total, App.jsx fica fora do escopo deste plano"
  - "cost/openPnL/openPct/dayVal não mudam com o caixa reservado — reservado não é posição, não tem preço de marcação"

patterns-established:
  - "Campo/método novo em persistence.js precisa aparecer >= 2 vezes (uma por store) — guardião automático trava regressão"

requirements-completed: [MERC-01, MERC-04]

duration: ~35min
completed: 2026-08-18
---

# Phase 2 Plan 04: Ordens Pendentes e Status de Mercado no Front Summary

Leva `pendingOrders`, `caixaReservado` e o status público de mercado do backend
(plano 02-02) até `deviceStore`/`serverStore` — com guardião de paridade
estático que falha se um método/campo novo entrar em só um dos dois stores —
e faz `portfolioMetrics` (motor financeiro puro do front) contar o caixa
reservado como patrimônio, para que criar uma ordem pendente não faça
dinheiro "sumir" da tela.

## Performance

- **Duration:** ~35 min (inclui recuperação de worktree desatualizado via merge)
- **Started:** 2026-08-18T22:30Z (aprox.)
- **Completed:** 2026-08-19T01:57Z
- **Tasks:** 3/3
- **Files modified:** 4 (3 fonte + 1 teste existente estendido, + 1 teste novo)

## Accomplishments
- `api.marketStatus()`/`api.cancelPendingOrder(id)` no cliente HTTP, mesma
  trilha de tratamento de erro/resposta não-JSON do resto de `api.js`
- `pendingOrders`/`caixaReservado` chegam à tela nos DOIS stores, com
  `_adotarCarteiraDoServidor` adotando as duas chaves do payload do servidor
  (fecha a mesma classe de defeito do qa/audit-2026-08-08: ordem
  executada/cancelada pelo servidor com o app fechado nunca sumiria da tela)
- `marketStatus`/`cancelPendingOrder` existem nos DOIS stores com o mesmo
  contrato — App.jsx poderá consumir `store.marketStatus()` sem exceção ao
  guardrail de paridade
- `portfolioMetrics` soma o caixa reservado ao patrimônio, com
  retrocompatibilidade total para os 7 call sites atuais (App.jsx, fora de
  escopo deste plano — entra em plano posterior de UI)

## Task Commits

Todas as 3 tasks são `tdd="true"`, executadas em ciclo RED → GREEN:

1. **Task 1: api.marketStatus() e api.cancelPendingOrder()**
   - RED (junto com o guardião de paridade da Task 2): `349b66a` — test(02-04)
   - GREEN: `50c7e96` — feat(02-04)
2. **Task 2: pendingOrders/caixaReservado e cancelPendingOrder nos DOIS stores**
   - RED: (mesmo commit `349b66a` da Task 1 — o teste único cobre as duas)
   - GREEN: `5851d31` — feat(02-04)
3. **Task 3: portfolioMetrics conta o caixa reservado**
   - RED: `f8f088f` — test(02-04)
   - GREEN: `74c46ed` — feat(02-04)

Nenhum REFACTOR separado foi necessário em nenhuma task.

**Plan metadata:** commit ainda a fazer (`docs(02-04): complete plan`, após este SUMMARY)

## Files Created/Modified
- `web/tests/test_ordens_pendentes_client.mjs` — cliente HTTP (marketStatus/cancelPendingOrder) + guardião de paridade estático dos dois stores
- `web/src/api.js` — `marketStatus()` e `cancelPendingOrder(id)` no objeto `api`
- `web/src/persistence.js` — `pendingOrders`/`caixaReservado` em `pub()`, `_localSeed()`, `_adotarCarteiraDoServidor` e `resetPortfolio`; `marketStatus`/`cancelPendingOrder` nos dois stores
- `web/src/finance.js` — `portfolioMetrics` ganha o 4º parâmetro opcional `reservado`
- `web/tests/test_finance.mjs` — casos de conservação, retrocompatibilidade e defensiva contra `reservado` inválido

## Decisions Made
Ver `key-decisions` no frontmatter. Resumo: nenhuma decisão nova fora do que
o PLAN.md já especificava — as três (erro explícito sem sessão, 4º parâmetro
opcional, cost/openPnL intocados) são implementações diretas do `<behavior>`
de cada task, sem desvio de arquitetura.

## Deviations from Plan

None - plan executado exatamente como escrito. O único evento fora do fluxo
normal foi a recuperação de worktree desatualizado (merge de
`claude/gsd-revisao-aplicacao-b9b4ef` ANTES da Task 1, conforme instruído em
`<known_environment_gaps>` do prompt do executor) — não é um desvio de
implementação, é o próprio protocolo de recuperação sendo seguido.

## Issues Encountered

**Gap de ambiente pré-existente, não causado por este plano — mas com efeito
diferente do já documentado em 02-01/02-02:**

- **`web/node_modules` não provisionado neste worktree isolado** (mesma causa
  raiz já registrada nos SUMMARYs de 02-01 e 02-02 para outros arquivos):
  `for t in web/tests/*.mjs; do node "$t" ...; done` reporta os MESMOS 7
  arquivos falhando (`test_appmode_sincroniza_servidor.mjs`,
  `test_carteira_nativa_sincroniza.mjs`, `test_fase2_portfolio.mjs`,
  `test_notif_central.mjs`, `test_notify.mjs`,
  `test_oauth_repassa_name_e_code.mjs`, `test_pet_resumo_modo_web.mjs`), todos
  com `Cannot find package '@capacitor/core'`. Confirmado por comparação byte
  a byte com a lista do SUMMARY de 02-02: nenhum arquivo novo falhando, nenhum
  destes 7 foi tocado por este plano.
- **Diferente de 02-01/02-02: este plano toca `web/src/*.js` diretamente**,
  e tanto o PLAN.md quanto `CLAUDE.md` marcam `npx vite build` como
  MANDATÓRIO exatamente para este caso ("grep e teste estático não pegam erro
  de sintaxe JS"). `npx vite build` falhou não no bundle do app, mas ao
  carregar o PRÓPRIO `vite.config.js` (`Cannot find package 'vite'` /
  `@vitejs/plugin-react` / `vite-plugin-pwa`) — evidência de que
  `web/node_modules` está, de fato, vazio (confirmado: 1 entrada só) neste
  worktree, não um problema no código editado.
  - **Verificação substituta aplicada:** `node --check web/src/persistence.js`,
    `node --check web/src/finance.js` e `node --check web/src/api.js` — os
    três passam. `node --check` faz parse sem resolver imports, então
    contorna o gap de `@capacitor/core`/`vite` e confirma que os TRÊS
    arquivos editados são JS sintaticamente válido.
  - **O que continua sem confirmação:** o build real do bundler (resolução de
    módulo, tree-shaking, plugins Vite/PWA) não rodou. `node --check` prova
    ausência de erro de sintaxe, não ausência de erro de build/resolução.
  - **Por que não corrigido aqui:** `npm install`/`npm ci` para provisionar
    `web/node_modules` está fora do escopo deste plano (Regra 3, exclusão de
    instalação de pacote) e, ao contrário do `server/.venv`, não há mecanismo
    equivalente de "venv compartilhado do clone principal" para
    `node_modules` em `scripts/*.sh` (confirmado por grep — `scripts/test.sh`
    tem lógica de `git rev-parse --git-common-dir` para Python; não existe
    equivalente para `npm`/`node_modules`). Symlink ou install unilateral
    correriam risco de estado divergente no worktree compartilhado sem
    necessidade clara.
  - **Sinalização ao orquestrador:** este gap agora bloqueia a verificação
    MANDATÓRIA de build de front em qualquer plano futuro desta fase que
    toque `web/`. Recomenda-se provisionar `web/node_modules` no
    worktree/ambiente de execução ANTES do próximo plano que edite `web/src/`.

**Suíte canônica (`bash scripts/executar.sh --testes`) — rodada de verdade,
não substituída pela metade backend:**

- Comando executado literalmente: `bash scripts/executar.sh --testes`.
- **Saída: `EXIT_CANONICAL=1`.** Isto é ESPERADO neste worktree, não uma
  regressão deste plano — `executar.sh --testes` seta `RC=1` se QUALQUER
  `web/tests/*.mjs` falhar, e os MESMOS 7 arquivos do gap de `@capacitor/core`
  acima falham aqui também (confirmado linha a linha na saída: mesma lista
  exata — `test_appmode_sincroniza_servidor.mjs`,
  `test_carteira_nativa_sincroniza.mjs`, `test_fase2_portfolio.mjs`,
  `test_notif_central.mjs`, `test_notify.mjs`,
  `test_oauth_repassa_name_e_code.mjs`, `test_pet_resumo_modo_web.mjs`).
- Backend: **1047 passed** (suíte inteira, sem falha).
- Web: 74/81 arquivos `[OK]`, incluindo os dois relevantes a este plano —
  `test_ordens_pendentes_client.mjs` (novo) e `test_finance.mjs` (estendido)
  — ambos `[OK]`. Os 7 `[X]` são exatamente os já listados acima.
- **Conclusão explícita:** quem rodar `bash scripts/executar.sh --testes`
  neste worktree verá exit 1 — isto é o gap de ambiente pré-existente
  (`web/node_modules` vazio), não uma quebra introduzida por este plano.
  Nenhum arquivo tocado por este plano está entre os 7 que falham.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Next Phase Readiness

- `store.marketStatus()`/`store.cancelPendingOrder(id)` prontos para consumo
  por App.jsx (badge na tela de entrada D-08, tela de Histórico D-09) —
  fica para plano de UI subsequente (02-05/06/07), fora do escopo deste
  plano (`files_modified` não incluía `App.jsx`).
- `portfolioMetrics` está pronto para receber o 4º argumento, mas os 7 call
  sites em `App.jsx` ainda não foram atualizados para passar `caixaReservado`
  — é trabalho de UI, não deste plano de camada de estado.
- **Bloqueio a monitorar:** build real (`npx vite build`) segue não verificado
  neste worktree por gap de ambiente (`web/node_modules` vazio) — ver "Issues
  Encountered". Recomenda-se rodar `npx vite build` assim que o ambiente for
  provisionado, antes de considerar a Fase 2 pronta para merge/deploy.

---
*Phase: 02-realismo-de-mercado*
*Completed: 2026-08-18*

## Self-Check: PASSED

- FOUND: web/tests/test_ordens_pendentes_client.mjs
- FOUND: web/src/api.js
- FOUND: web/src/persistence.js
- FOUND: web/src/finance.js
- FOUND: web/tests/test_finance.mjs
- FOUND: .planning/phases/02-realismo-de-mercado/02-04-SUMMARY.md
- FOUND commit: 349b66a (test RED, Tasks 1+2)
- FOUND commit: 50c7e96 (feat GREEN, Task 1)
- FOUND commit: 5851d31 (feat GREEN, Task 2)
- FOUND commit: f8f088f (test RED, Task 3)
- FOUND commit: 74c46ed (feat GREEN, Task 3)

## TDD Gate Compliance

Todas as 3 tasks têm `tdd="true"`. Task 1 e Task 2 compartilham um único
arquivo de teste (`test_ordens_pendentes_client.mjs`) construído em UM ciclo
RED→GREEN→GREEN (um commit RED cobrindo as duas tasks, dois commits GREEN
separados — um por task, cada um tornando verde só a fatia correspondente).
Task 3 seguiu RED→GREEN isolado em `test_finance.mjs`. Nenhum REFACTOR
separado foi necessário. Gate sequence íntegro nas 5 commits listadas acima.
