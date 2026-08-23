---
phase: 02-realismo-de-mercado
plan: 05
subsystem: front-end / UI (web + iOS, mesmo bundle)
tags: [market-status, MERC-01, MarketStatusBadge, WelcomeAuthScreen, Topbar, portfolioMetrics, copy.js]

requires:
  - phase: 02-realismo-de-mercado (plano 04)
    provides: "store.marketStatus()/store.cancelPendingOrder(id) nos dois stores; portfolioMetrics(positions, quotes, cash, reservado) com 4º parâmetro opcional; pendingOrders/caixaReservado em public_state"
provides:
  - "MarketStatusBadge: componente único (3 estados: aberto/fechado/indisponível), renderizado pré-login (WelcomeAuthScreen) e pós-login (Topbar)"
  - "Estado único `mercado` no root de App(), alimentado por store.marketStatus() (rota pública, roda antes de qualquer login), exposto em ctx.mercado"
  - "copy.js: mercadoAberto/mercadoFechado(abertura)/mercadoIndisponivel nos dois modos (estudo/operador), simétricos e sem invenção de horário"
  - "Os 7 call sites de portfolioMetrics em App.jsx passam data.caixaReservado — patrimônio da Topbar não encolhe ao criar uma ordem pendente"
affects: [02-06, 02-07]

tech-stack:
  added: []
  patterns:
    - "Inspeção estática de App.jsx (readFileSync + regex/funcBody por balanceamento de chaves) para guardiões que não podem importar o arquivo (single-file, sem exports internos) — mesma técnica de test_copy_theme.mjs/test_brand_book_v2_tokens.mjs"
    - "color-mix(in srgb, <cor> 14%, transparent) para o halo do dot do badge — reusa padrão já existente em App.jsx (linha ~1254), evita precisar de um token *Tint por estado que não existe para T.warn"
    - "Nome de variável local ESPECÍFICO em closures de efeito (onVisibleMercado, não onVisible genérico) quando outro guardião do arquivo faz match posicional por nome de variável — ver Deviations"

key-files:
  created:
    - web/tests/test_status_mercado_ui.mjs
  modified:
    - web/src/copy.js
    - web/src/App.jsx

key-decisions:
  - "mercadoFechado(abertura) no ramo estudo acrescenta uma frase didática fixa (\"a B3 só negocia em horário de pregão, em dias úteis\") sem citar o horário de fechamento (16:55) — o payload de /api/market/status não passa esse dado para a função (assinatura de 1 argumento, conforme PLAN.md), e citar um horário fixo não vindo do dado violaria CLAUDE.md princípio 4; o ramo operador fica seco, só \"abre {HH:MM}\""
  - "Halo do dot do badge usa color-mix() em vez de um token *Tint dedicado — T.warnTint não existe no sistema de tokens (só positiveTint/negativeTint/accentTint), e criar um token novo estava fora do escopo deste plano; color-mix() já é um padrão estabelecido no arquivo"
  - "portfolioMetrics recebe data.caixaReservado || 0 (não `data && data.caixaReservado`) nos 7 call sites — todos os 7 já desreferenciam data.cash na mesma linha sem guard adicional, então data já está garantido non-null nesse ponto; || 0 cobre só o campo estar ausente (ex.: conta antes deste dado existir no payload)"

patterns-established:
  - "Badge de status client-side reusa cores SÓ semânticas (T.positive/T.negative/T.warn), nunca T.accent, quando precisa renderizar idêntico em contexto sem modo (pré-login) — documentado inline no componente"

requirements-completed: [MERC-01]

duration: ~45min
completed: 2026-08-18
---

# Phase 2 Plan 05: Status Real de Mercado na UI (Badge Pré/Pós-Login) Summary

Um único componente `MarketStatusBadge` (3 estados: aberto/fechado/indisponível,
cores só semânticas, nunca `T.accent`) alimentado por um único estado `mercado`
no root de `App()` — consultado via `store.marketStatus()` (rota pública, roda
ANTES do login) — agora aparece na tela de entrada (`WelcomeAuthScreen`) e no
Topbar pós-login, nos dois modos. Os 7 pontos de cálculo de patrimônio
(`portfolioMetrics`) passam a contar `data.caixaReservado`, para que criar uma
ordem pendente (plano 02-04) nunca faça o patrimônio da Topbar encolher.

## Performance

- **Duration:** ~45 min (leitura de contexto + recuperação de worktree
  desatualizado via merge + 3 tasks TDD)
- **Started:** 2026-08-18T22:40Z (aprox., leitura de contexto)
- **Completed:** 2026-08-18T23:24Z
- **Tasks:** 3/3
- **Files modified:** 2 fonte (`copy.js`, `App.jsx`) + 1 teste novo

## Accomplishments
- `copy.js`: `mercadoAberto`/`mercadoFechado(abertura)`/`mercadoIndisponivel`
  nos dois modos, simétricos (guardião de chaves de `test_copy_theme.mjs`
  continua passando), sem invenção de horário quando o payload não traz
  `abertura`
- `MarketStatusBadge`: componente único, 3 estados só, `T.positive`/
  `T.negative`/`T.warn`, NUNCA `T.accent` — precisa renderizar idêntico
  pré-login (sem contexto de modo) e nos dois modos pós-login
- Estado `mercado` no root: `null` = 1ª consulta em voo (nada afirmado),
  `{erro: true}` em falha de rede (sem `flash`, não é erro do usuário),
  reconsulta em `visibilitychange`/`focus` + intervalo de 60s, cleanup
  completo de listeners/timer
- Badge renderizado em `WelcomeAuthScreen` (abaixo do disclaimer, usa só
  `ctx.mercado`/`ctx.cp`, tela continua sem tocar `data`) e em `Topbar`
  (linha de modo, após o mesmo divisor "·" já usado ali)
- Os 7 call sites de `portfolioMetrics` em `App.jsx` passam
  `data.caixaReservado || 0` como 4º argumento
- Diagnóstico do Operador (`srv.pregaoAberto`) ganhou um comentário
  explicando por que coexiste de propósito com `ctx.mercado`/
  `MarketStatusBadge` (dados semanticamente diferentes: status do
  SERVIDOR — inclui kill-switch/heartbeat — vs. status público do pregão)

## Task Commits

Todas as 3 tasks são `tdd="true"`; RED e GREEN ficaram no mesmo commit por
task (o guardião novo cresceu incrementalmente junto com cada implementação,
não em ciclo RED→GREEN estritamente separado — ver nota abaixo):

1. **Task 1: Textos do badge em copy.js** — `598db33` (feat)
2. **Task 2: Estado único no root + MarketStatusBadge** — `763d07b` (feat)
3. **Task 3: Render pré/pós-login + portfolioMetrics com caixa reservado** — `602bff5` (feat)
4. **Correção de deviation (Rule 1)** — `5714ef3` (fix) — ver Deviations

**Plan metadata:** commit ainda a fazer (`docs(02-05): complete plan`, após este SUMMARY)

## Files Created/Modified
- `web/tests/test_status_mercado_ui.mjs` — guardião novo (cresce nas 3 tasks): simetria/invenção de horário em `copy.js`; inspeção estática de `App.jsx` (fonte única de `store.marketStatus(`, `MarketStatusBadge` sem `T.accent`, cleanup de listener/timer, badge nos dois pontos de render, `WelcomeAuthScreen` sem `ctx.data`, nenhuma chamada de `portfolioMetrics` com 3 argumentos, conservação de patrimônio)
- `web/src/copy.js` — 3 chaves novas por modo (`mercadoAberto`/`mercadoFechado`/`mercadoIndisponivel`)
- `web/src/App.jsx` — `MarketStatusBadge` (antes de `Topbar`), `useState(mercado)` + `useEffect` de boot/reconsulta no root, `ctx.mercado`, render em `WelcomeAuthScreen` e `Topbar` (prop `mercado`/`cp` nova), 7 call sites de `portfolioMetrics` com 4º argumento, comentário de coexistência em `srv.pregaoAberto`

## Decisions Made
Ver `key-decisions` no frontmatter. Resumo: (1) o texto didático de
`mercadoFechado` no ramo Estudo evita citar um horário de fechamento que a
função não recebe como argumento — sem isso seria uma invenção de dado
(CLAUDE.md princípio 4); (2) o halo do dot usa `color-mix()` por não existir
token `T.warnTint`; (3) `data.caixaReservado || 0` (sem guard de `data`) nos
7 call sites porque `data.cash` já é desreferenciado sem guard na mesma
linha em todos eles.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Colisão de nome de variável quebrou um guardião existente**
- **Found during:** verificação final (`bash scripts/executar.sh --testes`), depois da Task 3
- **Issue:** o novo `useEffect` de status de mercado (Task 2) declarou `const onVisible = () => {...}` para o listener de `visibilitychange`. Mais abaixo no mesmo arquivo, `test_config_debounce_flush.mjs` já tinha um guardião que faz *match posicional* pelo primeiro `const onVisible = () => {...}` seguido de `document.addEventListener("visibilitychange", onVisible)` no arquivo inteiro — meu novo efeito, por vir ANTES no arquivo, passou a "roubar" esse match do efeito de flush do debounce de config (bug antigo já documentado em `orcamento-bug-e-config-boris`), fazendo `test_config_debounce_flush.mjs` falhar por engano.
- **Fix:** renomeado o listener do efeito de mercado para `onVisibleMercado` (nome específico), com comentário explicando o motivo — evita colisão sem tocar no guardião pré-existente (fora de escopo deste plano).
- **Files modified:** `web/src/App.jsx`
- **Verification:** `bash scripts/executar.sh --testes` volta a sair 0 (1059 backend + 81/81 web, incluindo `test_config_debounce_flush.mjs` e `test_status_mercado_ui.mjs`).
- **Committed in:** `5714ef3`

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug introduzido pela própria Task 2, corrigido antes da entrega)
**Impact on plan:** Nenhum scope creep — correção pontual de uma colisão de nome que meu próprio código causou. Nenhum guardião pré-existente foi alterado.

## Issues Encountered

**1. Worktree nascido de base desatualizada (mesmo padrão já documentado em 02-01..02-04)**
- `grep -q "cancelPendingOrder" web/src/api.js` retornou `false` no boot deste
  agente — confirmado sem commits locais divergentes, `git merge
  claude/gsd-revisao-aplicacao-b9b4ef` rodou limpo (zero conflitos), trazendo
  `.planning/` inteiro (que não existia neste worktree) e o trabalho dos
  planos 02-01..02-04 e da fase 3.

**2. `web/node_modules` não provisionado — MAS com uma causa mais específica que os planos anteriores documentaram**
- Symlink para `web/node_modules` de `.../peaceful-swanson-e9e462/web/`
  (lockfiles byte-idênticos, confirmado por `diff`) resolveu a maior parte do
  ambiente — `test_brand_book_v2_tokens.mjs`, `test_copy_theme.mjs`,
  `test_finance.mjs` e toda a suíte `bash scripts/executar.sh --testes`
  rodaram de verdade (81/81 web, 1059/1059 backend).
- **`npx vite build` continua falhando, mas por um motivo NOVO e mais
  preciso que "node_modules vazio" (02-04 documentou o caso genérico)**: o
  `node_modules` compartilhado em `peaceful-swanson-e9e462/web/` está, ele
  mesmo, DESSINCRONIZADO do seu próprio `package.json`/`package-lock.json`
  — falta `@capacitor/browser` (adicionado pelo commit `02b2aa1`, ADR-014
  admin no mobile), que `App.jsx` já importa desde aquele commit (fora do
  escopo deste plano). `npx vite build` falha em
  `[vite-plugin-pwa:build] Rollup failed to resolve import
  "@capacitor/browser"` — não é um erro introduzido por este plano.
  - **Verificação substituta aplicada (mais forte que `node --check` dos
    planos anteriores):** `App.jsx` contém JSX, então `node --check` não
    consegue nem parsear o arquivo (`ERR_UNKNOWN_FILE_EXTENSION`/JSX
    inválido para o parser puro do Node). Em vez disso, usei
    `node_modules/.bin/esbuild src/App.jsx --bundle --packages=external
    --loader:.png=dataurl --format=esm` — isso RESOLVE e empacota todos os
    imports RELATIVOS locais (`./copy.js`, `./finance.js`, `./persistence.js`
    etc.), tratando só os pacotes de `node_modules` como externos. Rodou
    limpo (0 erros) tanto ANTES quanto DEPOIS da Task 3, confirmando: (a)
    JSX sintaticamente válido; (b) todo o grafo de módulos locais que este
    plano toca resolve corretamente; (c) o `import "@capacitor/browser"`
    (não tocado por este plano) seria tratado como externo em qualquer caso,
    então esta checagem não o mascarou — ele já era um import válido de
    pacote antes deste plano.
  - **O que continua sem confirmação:** o pipeline COMPLETO do Vite/Rollup
    (tree-shaking real, plugin PWA, geração do bundle final) não rodou —
    exige `@capacitor/browser` fisicamente instalado.
  - **Por que não corrigido aqui:** `npm install`/`npm ci` em
    `web/node_modules` — mesmo scoped só a este worktree — é uma instalação
    de pacote via gerenciador, explicitamente excluída de auto-fix (Regra 3
    do executor), independentemente de o pacote já estar pinado no
    lockfile. Confirmado com o advisor antes de prosseguir.
  - **Sinalização ao orquestrador, com a causa exata desta vez:** para
    desbloquear `npx vite build` de verdade em planos futuros que tocam
    `web/`, é preciso rodar `npm install`/`npm ci` UMA VEZ em
    `.../peaceful-swanson-e9e462/web/` (o `node_modules` compartilhado por
    todos os worktrees via symlink) — por um humano ou por um passo de
    workflow autorizado a instalar pacotes, não por este executor.
- **Consequência direta no critério de sucesso deste plano:** o critério
  "`npx vite build` genuinely run... and passing" **NÃO foi atingido**, não
  por falha de implementação deste plano, mas por um gap de ambiente
  pré-existente e fora de escopo (dependência de um commit anterior nunca
  instalada no `node_modules` compartilhado). A verificação substituta
  (esbuild bundle de todos os imports locais + suíte canônica completa
  passando 100%) é a evidência disponível de que o código está correto.

**Suíte canônica (`bash scripts/executar.sh --testes`) — rodada de verdade:**
- Comando executado literalmente: `bash scripts/executar.sh --testes`.
- **Saída: exit 0.** Backend: 1059 passed (suíte inteira). Web: 81/81
  arquivos `[OK]` — incluindo `test_status_mercado_ui.mjs` (novo),
  `test_copy_theme.mjs`, `test_finance.mjs`, `test_brand_book_v2_tokens.mjs`
  e `test_config_debounce_flush.mjs` (o guardião afetado pela Deviation
  acima, confirmado verde após a correção).

## User Setup Required

None - nenhuma configuração de serviço externo.

## Next Phase Readiness

- `ctx.mercado`/`MarketStatusBadge` prontos para reuso por outras telas
  desta fase (ex.: `BuyModal`/`SellModal` no plano 02-06, que precisam do
  mesmo `pregaoAberto` para decidir ordem imediata × pendente — UI-SPEC já
  documenta essa dependência).
- **Bloqueio a monitorar (herdado, causa agora mais específica):** `npx vite
  build` real segue não verificado neste worktree — falta `@capacitor/browser`
  no `node_modules` compartilhado (`peaceful-swanson-e9e462/web/`), não
  relacionado a este plano. Recomenda-se `npm install`/`npm ci` nesse
  diretório ANTES do próximo plano desta fase que edite `web/src/`.

---
*Phase: 02-realismo-de-mercado*
*Completed: 2026-08-18*

## Self-Check: PASSED

- FOUND: web/tests/test_status_mercado_ui.mjs
- FOUND: web/src/copy.js
- FOUND: web/src/App.jsx
- FOUND: .planning/phases/02-realismo-de-mercado/02-05-SUMMARY.md
- FOUND commit: 598db33 (feat, Task 1)
- FOUND commit: 763d07b (feat, Task 2)
- FOUND commit: 602bff5 (feat, Task 3)
- FOUND commit: 5714ef3 (fix, Rule 1 deviation)
