---
phase: 260823-vu4-ajuste-de-ui-no-cabecalho-badge-mercado-
plan: 01
subsystem: ui

tags: [react, css, capacitor, ios, safe-area, layout]

# Dependency graph
requires: []
provides:
  - "MarketStatusBadge (web/src/App.jsx) trunca com ellipsis em vez de vazar/sobrepor layout vizinho, nos três pontos de render (Topbar, WelcomeAuthScreen, Home)"
  - "capacitor.config.ts com ios.contentInset: never — WKWebView edge-to-edge, sem faixa nativa fixa acima do cabeçalho"
  - "WelcomeAuthScreen com padding-top safe-area-aware (soma env(safe-area-inset-top) aos 18px existentes)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Flex item que precisa truncar com ellipsis: minWidth:0 no próprio item E no ancestral flex imediato (min-width:auto implícito do flex trava o encolhimento sem isso)"
    - "Container position:fixed+inset:0 não herda padding do shell ancestral — precisa somar env(safe-area-inset-*) ao próprio padding explicitamente"

key-files:
  created: []
  modified:
    - "web/src/App.jsx"
    - "web/capacitor.config.ts"

key-decisions:
  - "ios platform (web/ios/) estava ausente nesta worktree (diretório gerado, gitignorado) — rodei `npx cap add ios` antes do `cap sync ios` exigido pelo plano, para poder cumprir o critério de aceite sem pular a etapa; não altera nenhum arquivo versionado (web/ios/ continua fora do git)"
  - "web/node_modules ausente na worktree fresca — rodei `npm ci` (respeitando package-lock.json existente, nenhuma dependência nova) para poder rodar `npx vite build` conforme exigido pelo CLAUDE.md"

patterns-established: []

requirements-completed: [UI-BADGE-OVERFLOW, UI-DYNAMIC-ISLAND-GAP]

# Metrics
duration: 13min
completed: 2026-08-23
---

# Quick Task 260823-vu4: Ajuste de UI no cabeçalho (badge de mercado + Dynamic Island) Summary

**MarketStatusBadge trunca com ellipsis (minWidth:0 + textOverflow) e capacitor.config.ts vira edge-to-edge (contentInset: never) com WelcomeAuthScreen somando safe-area-inset-top ao próprio padding**

## Performance

- **Duration:** ~13 min
- **Started:** 2026-08-23T23:05:58-03:00 (base do plano)
- **Completed:** 2026-08-23T23:18:08-03:00
- **Tasks:** 2/2
- **Files modified:** 2 (`web/src/App.jsx`, `web/capacitor.config.ts`)

## Accomplishments
- `MarketStatusBadge` não vaza mais quando o texto do Modo Estudo é longo ("Mercado fechado — abre HH:MM (a B3 só negocia em horário de pregão, em dias úteis)") — encolhe e trunca com "…" no Topbar, no WelcomeAuthScreen e também no ponto de render da Home que o inventário do plano não listou (ver Deviations).
- `capacitor.config.ts` deixou de forçar o inset nativo automático do WKWebView (`contentInset: "always"`, pintado com a cor fixa `#0b0e14`) — agora é edge-to-edge (`"never"`), e o `paddingTop: env(safe-area-inset-top)` que o `shell` do App.jsx já tinha passa a fazer efeito de verdade, pintado com a cor de tema (`T.bgBase`).
- `WelcomeAuthScreen` (único container `position:fixed,inset:0` alterado, dos 12+ existentes no arquivo) agora soma a safe-area ao próprio `paddingTop`, evitando a regressão que o passo 1 introduziria (coruja/wordmark atrás da Dynamic Island).
- `cap sync ios` propagado e verificado: `web/ios/App/App/capacitor.config.json` gerado contém `"contentInset": "never"`.

## Task Commits

Each task was committed atomically:

1. **Task 1: truncar MarketStatusBadge** - `01cab95` (fix)
2. **Task 2: edge-to-edge no iOS + safe-area no WelcomeAuthScreen** - `94078a3` (fix)

_Nenhuma task era TDD; ambas são fix de layout/config, sem novo comportamento testável em unit test._

## Files Created/Modified
- `web/src/App.jsx` - `MarketStatusBadge` (linhas 758/760): `minWidth:0` no span externo e no span do label + `overflow:hidden, textOverflow:ellipsis` no label. `WelcomeAuthScreen` (linha 653): `padding:"18px"` trocado por `paddingTop:"calc(18px + env(safe-area-inset-top))"` + `paddingRight/Bottom/Left:"18px"`.
- `web/capacitor.config.ts` - `ios.contentInset`: `"always"` → `"never"`.

## Decisions Made
- Nenhuma mudança em `web/src/copy.js` nem na lógica de `label`/`cor` do badge — fix é puramente CSS, conforme escopo do plano.
- `Topbar`/`Ticker`/`shell` não tocados — o fix do `contentInset` propaga sozinho via CSS `env()` que já existia no `shell`.
- Nenhum outro container `position:fixed,inset:0` do arquivo (modais/scrims centralizados) foi alterado — fora de escopo, não reproduziam o defeito.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `npm ci` em `web/` antes do build**
- **Found during:** Task 1, verificação (`npx vite build`)
- **Issue:** Worktree fresca sem `web/node_modules` instalado — `vite build` falhava com `ERR_MODULE_NOT_FOUND` já na leitura do `vite.config.js` (nem chegava a compilar o código-fonte).
- **Fix:** `npm ci` (respeita `package-lock.json` existente, nenhuma dependência nova adicionada ao `package.json`) — não se enquadra na exclusão de "package manager installs não auto-fixáveis" porque não é instalação de pacote novo/não verificado, é reidratação de deps já travadas em lockfile.
- **Files modified:** nenhum arquivo versionado (`web/node_modules` é gitignorado).
- **Verificação:** `npx vite build` passou a rodar e retornou exit 0.
- **Committed in:** N/A (node_modules não é versionado, nada a commitar).

**2. [Rule 3 - Blocking] `npx cap add ios` antes do `cap sync ios`**
- **Found during:** Task 2, execução do passo 3 (`cap sync ios`)
- **Issue:** `web/ios/` (plataforma nativa Capacitor) não existia nesta worktree — é diretório gerado, listado em `.gitignore` (`web/ios/`), então cada worktree/checkout novo nasce sem ele. `cap sync ios` falhava com `[error] ios platform has not been added yet.`
- **Fix:** `npx cap add ios` (usa `@capacitor/ios`, já declarado em `devDependencies` e instalado via `npm ci` — nenhuma dependência nova, apenas scaffolding do projeto Xcode local a partir de pacote já presente). Depois rodei `cap sync ios` normalmente, como o plano exige.
- **Files modified:** nenhum arquivo versionado (`web/ios/` é gitignorado).
- **Verificação:** `cap sync ios` rodou sem erro; `web/ios/App/App/capacitor.config.json` gerado confirma `"contentInset": "never"`.
- **Committed in:** N/A (diretório gerado, não versionado).

---

**Total deviations:** 2 auto-fixed (ambas Rule 3 - blocking, ambientais — nenhuma mudança de código além do especificado no plano).
**Impact on plan:** Nenhum impacto no escopo do fix; ambas as ações eram pré-requisito puramente ambiental (dependências e scaffolding local) para poder rodar as verificações que o próprio plano exige. Nenhum scope creep.

## Issues Encountered
- O inventário de call sites do plano (`MarketStatusBadge` usado em "exatamente 2 pontos": Topbar e WelcomeAuthScreen) estava incompleto — há um terceiro ponto de render na Home (linha ~1808, dentro do resumo do dia). Isso não afetou o fix: como o componente é único e reusado, a mesma correção de CSS beneficia os três pontos igualmente, e nenhum call site foi tocado (o critério "nenhum call site alterado" continua válido). Reportando para o Alex/orquestrador como nota de precisão do plano, não como bug.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Código pronto e `npx vite build` verde nas duas tasks; `cap sync ios` propagado com a config nova confirmada no projeto nativo gerado. **Verificação manual obrigatória, fora do alcance deste executor** (sem acesso a simulador/dispositivo — declarado explicitamente no plano como requisito de fechamento, não opcional): rebuildar no iOS Simulator (iPhone 17 Pro, Dynamic Island, UDID `8D9E194B-7F8B-40C5-9747-FEF21618612C`) e confirmar por screenshot:
(a) o badge "Mercado fechado — abre HH:MM (...)" no Topbar não colide mais com o bloco de patrimônio, trunca com "…" se necessário;
(b) o mesmo badge na tela de login não sangra para fora do card;
(c) não existe mais faixa de cor nativa fixa acima do cabeçalho — a área ao redor da Dynamic Island é pintada com a cor de tema do app, coerente com claro/escuro;
(d) a bottom nav e a área do home indicator NÃO regrediram depois de `contentInset: "never"` (config é global nas 4 bordas do WKWebView, não só o topo) — sem gap novo, sem conteúdo colado no home indicator.

Nenhum blocker de código. Bloqueio é só de verificação visual (requer o Alex/orquestrador com acesso ao simulador).

---
*Phase: 260823-vu4-ajuste-de-ui-no-cabecalho-badge-mercado-*
*Completed: 2026-08-23*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/capacitor.config.ts
- FOUND: .planning/quick/260823-vu4-ajuste-de-ui-no-cabecalho-badge-mercado-/260823-vu4-SUMMARY.md
- FOUND commit: 01cab95 (Task 1)
- FOUND commit: 94078a3 (Task 2)
