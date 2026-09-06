---
phase: 20-funda-o-estrutural-e-tipogr-fica
plan: 01
subsystem: ui
tags: [react, css, layout, overflow, responsive, web]

# Dependency graph
requires: []
provides:
  - ".b3-shell e <main> contidos horizontalmente em viewport estreito (FIX-01)"
  - "MarketStatusBadge trunca com reticência em vez de empurrar layout (FIX-02)"
  - "Constante CONTENT_MAX_WIDTH (720px) única para o teto de largura desktop (SYS-04)"
  - "Guardião estático web/tests/test_fase20_fundacao_visual.mjs travando as três correções"
affects: [20-02, 20-03, 20-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Contenção de largura: overflow-x:hidden na regra CSS de classe (GlobalStyle), não só no style inline do elemento"
    - "Ancestral flex com minWidth:0 não é suficiente para span filho display:inline-flex encolher — o próprio inline-flex também precisa de maxWidth:100%"
    - "Constante de largura compartilhada (CONTENT_MAX_WIDTH) junto ao bloco MONO/SANS/DISPLAY, referenciada por igualdade em vez de literal duplicado"

key-files:
  created:
    - web/tests/test_fase20_fundacao_visual.mjs
  modified:
    - web/src/App.jsx

key-decisions:
  - "FIX-02 real root cause diverge do UI-SPEC/CONTEXT: a medição ao vivo (feita pelo orquestrador antes desta execução, browser MCP indisponível para este subagent) apontou que os ancestrais já tinham minWidth:0 — o defeito estava no próprio span raiz do MarketStatusBadge (display:inline-flex sem maxWidth), não resolvido só por minWidth:0 no pai."
  - "Aplicado tanto o ajuste de ancestral (minWidth:0 no call site da home, que genuinamente faltava) quanto o maxWidth:100% dentro do próprio componente — o primeiro por ser decisão travada em 20-CONTEXT.md e consumido pelo guardião estático via grep de padrão, o segundo por ser o que efetivamente fecha o defeito."
  - "FIX-01 estendido para <main> além de .b3-shell — medição ao vivo mostrou main também vazando (scrollWidth 506 vs clientWidth 365 em 375px), não coberto pelo texto original do plano."

requirements-completed: [FIX-01, FIX-02, SYS-04]

duration: ~50min
completed: 2026-09-05
---

# Phase 20 Plan 01: Fundação estrutural — contenção horizontal e teto de largura Summary

**`.b3-shell`/`<main>` param de vazar lateralmente em mobile, o badge de status de mercado trunca com reticência em vez de empurrar o Topbar, e o conteúdo desktop passa a respeitar 720px via uma única constante `CONTENT_MAX_WIDTH` compartilhada com o `BottomNav`.**

## Performance

- **Duration:** ~50 min
- **Completed:** 2026-09-05
- **Tasks:** 3 (Task 1 medição já executada pelo orquestrador antes desta sessão; Task 2 e 3 executadas nesta sessão)
- **Files modified:** 2 (`web/src/App.jsx`, novo `web/tests/test_fase20_fundacao_visual.mjs`)

## Accomplishments
- FIX-01: `.b3-shell` (regra CSS de `GlobalStyle()`) e `<main>` (style inline) ganharam `overflow-x:hidden` — os dois vazavam de fato, não só o shell.
- FIX-02: fechado por DUAS metades — `minWidth:0` no call site da home (que genuinamente faltava) e `maxWidth:"100%"` no próprio span raiz `display:"inline-flex"` do `MarketStatusBadge` (a causa raiz real, medida ao vivo).
- SYS-04: nova constante `CONTENT_MAX_WIDTH = "720px"` substitui os dois literais independentes (`"720px"` do `BottomNav`, `"1060px"` do wrapper de conteúdo pós-login).
- Guardião estático novo (`web/tests/test_fase20_fundacao_visual.mjs`), 10 asserções, sensibilidade confirmada manualmente (revertendo `overflow-x:hidden` o teste falha).

## Task 1 — Medição ao vivo (executada pelo orquestrador antes desta sessão)

Esta task foi executada pelo orquestrador diretamente contra o dev server no mesmo commit-base, porque ferramentas MCP de navegador (`mcp__computer-use__*`, `mcp__claude-in-chrome__*`) não são herdadas por subagentes spawnados via Task (bug upstream anthropics/claude-code#13898). Os achados foram entregues a este executor como contexto e são registrados aqui como o resultado oficial da Task 1:

**Medições em 375×812 (Modo Estudo, conta local descartável):**
- `.b3-shell`: scrollWidth=504, clientWidth=375
- `<main>`: scrollWidth=506, clientWidth=365 (achado NOVO — não estava no texto original do plano, que só mencionava o shell)
- `document.documentElement`: scrollWidth=375, clientWidth=375 (ok)
- `document.body`: scrollWidth=375, clientWidth=375 (ok)

**Elementos com `scrollWidth>clientWidth` ou `right>377`:** só o marquee do ticker (`.tt-track`, trilho intencional) e as duas instâncias de `MarketStatusBadge` (Topbar e home) com seus ancestrais em fluxo normal. Nenhum outro ofensor.

**Causa raiz de FIX-02 (a leitura estática do UI-SPEC/PATTERNS estava incompleta):** todos os ancestrais do badge, nos dois call sites, já tinham `minWidth:0` (confirmado via `getComputedStyle` subindo 5-6 níveis). O defeito real: o span raiz do próprio `MarketStatusBadge` é `display:"inline-flex"` — uma caixa inline-level, que só encolhe abaixo do tamanho intrínseco quando um pai flex/grid impõe `flex-basis`; aqui o pai é um `<div>` de bloco comum, então o badge sempre renderizava na largura intrínseca do conteúdo (medida: 488px), ignorando os 149px (Topbar) / 329px (home) disponíveis — o `overflow:hidden`/`textOverflow:ellipsis` do span de texto interno nunca disparava, porque essas propriedades só truncam quando a própria caixa tem largura restrita. `maxWidth:"100%"` no span raiz fecha isso.

**Baseline em 1280×900:** `.b3-shell`/`<main>` sem overflow (scrollWidth===clientWidth); wrapper de conteúdo renderizava em 1060px — confirma o valor "antes" que o SYS-04 precisa encolher para 720px.

## Task Commits

Cada task ficou num commit atômico:

1. **Task 1: Medir ao vivo** — sem commit (medição executada pelo orquestrador antes desta sessão de execução; nenhum arquivo foi alterado nessa task, conforme critério de aceite do plano)
2. **Task 2: Aplicar contenção horizontal, truncamento e teto de 720px** — `7fee622` (fix)
3. **Task 3: Guardião estático novo + remedição ao vivo** — `3473c91` (test) — remedição ao vivo (Parte 2) NÃO executada, ver "Issues Encountered"

**Base do plano:** `e33566a` (docs: cria plano da Fase 20)

## Files Created/Modified
- `web/src/App.jsx` — `const CONTENT_MAX_WIDTH = "720px"` (perto de `MONO`/`SANS`/`DISPLAY`); `.b3-shell{...overflow-x:hidden;}`; `<main>` com `overflowX:"hidden"`; call site da home do `MarketStatusBadge` com `minWidth:0`; span raiz do `MarketStatusBadge` com `maxWidth:"100%"`; `BottomNav` e wrapper de conteúdo pós-login referenciando `CONTENT_MAX_WIDTH` em vez dos literais `"720px"`/`"1060px"`.
- `web/tests/test_fase20_fundacao_visual.mjs` — guardião novo, 10 asserções, padrão `readFileSync` + `ok()` + `process.exit(fails)` dos 114 testes `.mjs` existentes.

## Decisions Made
- Reconciliar o palpite do plano (`20-CONTEXT.md`/`20-UI-SPEC.md`: "a correção é só ancestral, não tocar em `MarketStatusBadge` por dentro") com a medição ao vivo que o supera: mantive a correção ancestral no call site da home (decisão travada em `20-CONTEXT.md`, também é o padrão que o guardião trava via grep) E adicionei `maxWidth:"100%"` dentro do próprio componente, que é o que efetivamente fecha o defeito segundo a medição.
- Estendi FIX-01 para `<main>` além de `.b3-shell`, porque a medição ao vivo mostrou os dois vazando — o texto original do plano só citava o shell como certeza e tratava `<main>` como condicional ("se a Task 1 apontou outro elemento").
- Guardião conta ocorrências após remover comentários de linha (`//...`) do texto de `App.jsx`, porque os próprios comentários que documentam esta fase mencionam os termos travados (`720px`, `1060px`, `CONTENT_MAX_WIDTH`) e inflariam a contagem crua.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] FIX-02 corrigido dentro de `MarketStatusBadge`, não só nos ancestrais**
- **Found during:** Task 2 (aplicação das correções), com base na medição ao vivo já feita na Task 1 pelo orquestrador
- **Issue:** O plano instruía explicitamente "não tocar em `MarketStatusBadge` por dentro" partindo do palpite de que 4/5 ancestrais já tinham `minWidth:0` e o 5º (Topbar `App.jsx:795`) seria a causa. A medição ao vivo confirmou que TODOS os ancestrais já tinham `minWidth:0` (inclusive o candidato `App.jsx:795`, que na leitura atual do código nem é ancestral direto do badge) — o defeito real estava no próprio span raiz `display:"inline-flex"` do componente, que não encolhe sem `maxWidth` próprio.
- **Fix:** Adicionado `maxWidth: "100%"` ao mesmo objeto de style do span raiz do `MarketStatusBadge` (`display:"inline-flex", alignItems:"center", gap:"6px", minWidth:0` → `..., maxWidth:"100%"`), com comentário explicando a decisão e citando a medição.
- **Files modified:** `web/src/App.jsx`
- **Verification:** `npx vite build` ok; guardião estático novo trava especificamente esta linha (`display: "inline-flex", ..., maxWidth: "100%"`) via regex.
- **Committed in:** `7fee622`

**2. [Rule 2 - Missing Critical] FIX-01 estendido a `<main>`**
- **Found during:** Task 2, a partir do achado de medição da Task 1
- **Issue:** O texto do plano descrevia `<main>` como um alvo condicional ("se a Task 1 apontou outro elemento") — a medição confirmou que `<main>` de fato vaza (506 vs 365), então a contenção nele é obrigatória, não opcional.
- **Fix:** `overflowX: "hidden"` adicionado ao style inline de `<main>` (que já tinha `overflowY:"auto"` — eixo vertical intocado).
- **Files modified:** `web/src/App.jsx`
- **Verification:** `npx vite build` ok; guardião novo trava o atributo.
- **Committed in:** `7fee622`

---

**Total deviations:** 2 auto-fixed (ambas Rule 1/2, decorrentes da medição ao vivo superando o palpite do UI-SPEC/CONTEXT — exatamente o cenário que o `<decisao_do_planner>` do próprio plano previu e autorizou: "a Task 2 corrige o que a medição apontar").
**Impact on plan:** Nenhum scope creep — as duas mudanças são estritamente necessárias para fechar FIX-01/FIX-02 conforme a evidência medida, dentro do mesmo arquivo e sem novo pacote.

## Issues Encountered

**Task 3 Parte 2 (remedição ao vivo em 375px/1280px/820px) NÃO foi executada por este subagent.** O plano exige repetir a medição ao vivo (browser) depois da correção, para confirmar `scrollWidth===clientWidth`, truncamento visível do badge com reticência, largura de 720px no wrapper em 1280px, e varredura de regressão em 820px (Acompanhar/Watchlist/Portfólio). Nenhuma ferramenta MCP de navegador está disponível para este subagent — confirmado empiricamente durante a execução: tentativas diretas de invocar `mcp__computer-use__screenshot` e `mcp__claude-in-chrome__navigate` retornaram `Error: No such tool available`. Esta é a mesma limitação de ambiente (subagentes spawnados via Task não herdam MCP tools do orquestrador — anthropics/claude-code#13898) que já havia bloqueado a Task 1 original, que por isso foi executada pelo orquestrador diretamente e entregue como contexto a este executor.

Diferente da Task 1, a Task 3 Parte 2 NÃO foi pré-executada pelo orquestrador e permanece pendente. Todo o resto de Task 3 (guardião estático — Parte 1 — e suíte canônica completa — Parte 3) foi executado e está verde.

**O que fica pendente para o orquestrador (ou uma nova sessão com acesso a browser MCP) fechar, sobre o commit `3473c91`:**
1. Confirmar em 375×812 que `.b3-shell.scrollWidth === .b3-shell.clientWidth` e `main.scrollWidth === main.clientWidth`.
2. Confirmar que o `<span>` de rótulo do badge (Topbar, Modo Estudo, frase longa) tem `scrollWidth > clientWidth` com `textOverflow: ellipsis` computado e reticência visível, sem empurrar o bloco de patrimônio para fora da tela.
3. Confirmar em 1280×900 que o wrapper de conteúdo mede exatamente 720px e está alinhado ao `BottomNav`.
4. Varrer 820×1000 (Acompanhar, Watchlist, Portfólio) e registrar se o teto de 720px (vindo de 1060px) introduziu alguma quebra visível — esperado que não, mas não confirmado ao vivo.

Nenhum destes itens foi aproximado ou estimado neste SUMMARY — ficam explicitamente em aberto, conforme o próprio `<decisao_do_planner>` do plano veta ("escrever a partir do palpite é o anti-padrão que este projeto já pagou caro").

## Orchestrator Live Re-Verification (Task 3, Parte 2 — fechada)

Executada pelo orquestrador via MCP do navegador (mesmo método da Task 1), dev
server subido no commit de merge (base `3473c91` + merge), conta local
existente, sem dados fabricados:

1. **375×812** — `.b3-shell`: scrollWidth=375=clientWidth. `<main>`:
   scrollWidth=365=clientWidth. Nenhum vazamento horizontal. ✓
2. **Truncamento do badge (Topbar, frase real "Mercado fechado — abre 10:00
   ...")** — span de texto: `scrollWidth=475` vs `clientWidth=136`,
   `computedTextOverflow: "ellipsis"`, `computedOverflow: "hidden"`.
   Confirmado visualmente: "Mercado fechado — ab…" com reticência visível,
   bloco de patrimônio intacto ao lado. ✓
3. **1280×900** — wrapper de conteúdo: 720px de largura, `left≈275`;
   `BottomNav`: 720px, `left≈280` (diferença de 5px é padding interno do nav,
   não desalinhamento). ✓
4. **820×1000, varredura de regressão** — Acompanhar, Watchlist/Monitoramento
   e Portfólio/Posições: `.b3-shell`/`<main>` sem vazamento nas três; únicos
   elementos com `scrollWidth>clientWidth` são o marquee do ticker
   (intencional), o carrossel "Modelo de análise" (padrão pré-existente, fora
   do escopo desta fase) e o mascote animado (`transform:scale`, decorativo,
   pré-existente). Nenhuma quebra visível introduzida pela redução de
   1060px→720px. ✓

**Os 4 itens do critério de aceite estão fechados por medição ao vivo, não
por leitura de código.** FIX-01, FIX-02 e SYS-04 confirmados.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Código fonte e guardião estático prontos, `npx vite build` limpo, suíte canônica completa verde (2021 pytest passed + 1 skipped; 115 testes `.mjs`, incluindo o novo guardião).
- Bloqueador residual: live re-verification da Task 3 Parte 2 (item acima) — recomendo que o orquestrador execute essa medição (do mesmo jeito que fez para a Task 1) antes de considerar FIX-02/SYS-04 100% fechados por evidência ao vivo, já que o critério de aceite do plano exige medição, não leitura de código.
- Fases 21/22/23 podem prosseguir editando `App.jsx` com a garantia do guardião novo contra regressão dos três defeitos.

---
*Phase: 20-funda-o-estrutural-e-tipogr-fica*
*Completed: 2026-09-05*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/tests/test_fase20_fundacao_visual.mjs
- FOUND: .planning/phases/20-funda-o-estrutural-e-tipogr-fica/20-01-SUMMARY.md
- FOUND commit: 7fee622 (fix — Task 2)
- FOUND commit: 3473c91 (test — Task 3)
- FOUND commit: e33566a (plan base)
