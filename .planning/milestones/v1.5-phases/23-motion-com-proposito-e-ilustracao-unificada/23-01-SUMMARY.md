---
phase: 23-motion-com-proposito-e-ilustracao-unificada
plan: 01
subsystem: ui
tags: [react, css-keyframes, motion, accessibility, prefers-reduced-motion, watchlist, radar]

# Dependency graph
requires:
  - phase: 20-motion-fundacao-visual
    provides: "gate abrangente de prefers-reduced-motion em GlobalStyle() (MOTION-03), reusado verbatim sem @media novo"
provides:
  - "keyframe b3cardEnter + classe .b3 .card-enter (fade 0→1 + translateY 8px→0, 200ms ease-out) em GlobalStyle()"
  - "mecanismo de sessão de visualização (useRef(new Set()) por tela) para detectar ticker inédito em MercadoScreen e RadarScreen"
  - "prop isNovo no vm do AtivoCard, consumida como className condicional na raiz do card"
  - "guardião web/tests/test_fase23_motion.mjs (Seção A, MOTION-01) — arquivo será estendido pelo plano 23-03 com a Seção B (MOTION-02)"
affects: [23-02, 23-03, 23-04]

tech-stack:
  added: []
  patterns:
    - "Ref de sessão de visualização por tela (useRef(new Set())), commitado em useEffect sem array de dependências — nunca no corpo do render, por causa do React.StrictMode de main.jsx"
    - "Motion novo entra como animation CSS comum dentro de .b3 (nunca @media (prefers-reduced-motion) novo) para herdar o gate amplo da Fase 20 automaticamente"

key-files:
  created:
    - web/tests/test_fase23_motion.mjs
  modified:
    - web/src/App.jsx

key-decisions:
  - "Nome do mecanismo: vistosRef (useRef(new Set())) + isNovo(t), uma instância própria por tela (MercadoScreen e RadarScreen), nunca compartilhada — são listas diferentes"
  - "className aplicado via card-enter | undefined (nunca class=\"\") na raiz do AtivoCard, na mesma linha que id={\"ativo-\" + t}"
  - "Primeira pintura da lista anima TODOS os cards (conjunto de vistos começa vazio) — comportamento deliberado do 23-CONTEXT.md, não uma variação a implementar"

patterns-established:
  - "Guardião de motion único por fase (test_fase23_motion.mjs), organizado em seções (A=MOTION-01, B=MOTION-02 reservada para 23-03) para o próximo plano estender em vez de criar arquivo paralelo"

requirements-completed: [MOTION-01]

# Metrics
duration: ~45min
completed: 2026-09-06
---

# Phase 23 Plan 01: Entrada de card com transição (MOTION-01) Summary

**Card de setup inédito entra na Watchlist/Radar com fade + subida de 8px em 200ms (ease-out), via `@keyframes b3cardEnter` escopado em `.b3` — card já visto não re-anima, e o movimento herda o gate de `prefers-reduced-motion` da Fase 20 sem nenhum `@media` novo.**

## Performance

- **Duration:** ~45 min
- **Completed:** 2026-09-06T14:36:24Z
- **Tasks:** 2/2 completos
- **Files modified:** 2 (`web/src/App.jsx`, `web/tests/test_fase23_motion.mjs`)

## Accomplishments

- `@keyframes b3cardEnter` + `.b3 .card-enter{ animation:b3cardEnter 200ms ease-out; }` adicionados a `GlobalStyle()`, imediatamente após o bloco `b3tt`/`.tt-track` — mesma convenção de nome (`b3<algo>`) e mesmo escopo `.b3` dos keyframes existentes.
- `MercadoScreen` e `RadarScreen` ganharam, cada um, seu próprio `useRef(new Set())` de tickers já renderizados nesta montagem da lista, com o commit (`.add(`) feito dentro de `useEffect` sem array de dependências — nunca no corpo do render, prevenindo o bug de `React.StrictMode` (corpo roda 2x em dev) descrito no plano.
- `isNovo(t)`/`isNovo(r.ticker)` passado no `vm` dos dois call sites do `AtivoCard` (Watchlist `App.jsx:3912`, Radar `App.jsx:6939`); `AtivoCard` consome `isNovo` no destructuring e aplica `className={isNovo ? "card-enter" : undefined}` na raiz (`App.jsx:3443`).
- Nenhum `@media (prefers-reduced-motion: reduce)` novo — continuam existindo exatamente 2 blocos, travado tanto pelo guardião novo quanto pelo guardião da Fase 20 (`test_fase20_fundacao_visual.mjs`, rodado isolado após a mudança).
- Guardião `web/tests/test_fase23_motion.mjs` criado com 22 asserções (Seção A / MOTION-01), provado com dentes: falhou nas 11 asserções que exigiam código ainda não escrito (Task 1, RED) e passou em todas depois da implementação (Task 2, GREEN).
- Zero dependência de animação nova (`web/package.json` sem `framer-motion`/`react-spring`/`motion`/`gsap`/`animejs`/`react-transition-group`).

## Task Commits

1. **Task 1: Guardião da Fase 23, Seção A (MOTION-01), escrito antes da mudança (RED)** - `1c5cee8` (test)
2. **Task 2: Entrada de card com fade + subida nas duas listas (GREEN)** - `304bcd4` (feat)

_Nenhum commit de metadados de plano separado — este SUMMARY é o registro final da execução (STATE.md/ROADMAP.md não são atualizados por esta task, conforme instrução do orquestrador)._

## Files Created/Modified

- `web/src/App.jsx` — keyframe/classe em `GlobalStyle()`; refs de vistos em `MercadoScreen`/`RadarScreen`; `isNovo` nos dois call sites e na raiz do `AtivoCard`.
- `web/tests/test_fase23_motion.mjs` — guardião novo (Seção A, MOTION-01); cabeçalho reserva a Seção B (MOTION-02, plano 23-03) para extensão no mesmo arquivo e aponta `test_boris_intro.mjs` como guardião de ILUS-01.

## Decisions Made

- Nomes escolhidos (discricionários pelo `23-CONTEXT.md`): `vistosRef` para o `useRef(new Set())`, `isNovo` para o predicado — usados de forma idêntica nas duas telas, sem compartilhar a instância.
- `className={isNovo ? "card-enter" : undefined}` em vez de string vazia — evita `class=""` supérfluo no DOM.
- Primeira pintura de cada tela anima todos os cards da lista (conjunto de vistos nasce vazio) — comportamento explicitamente travado pelo `23-CONTEXT.md`, não uma variação a decidir.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Guardião (Task 1) tinha um falso negativo na asserção 7 (commit em efeito), corrigido durante a Task 2**
- **Found during:** Task 2, ao rodar `node web/tests/test_fase23_motion.mjs` depois de implementar `RadarScreen` — a asserção de "MercadoScreen" passou, mas a de "RadarScreen" falhou mesmo com o código correto no lugar certo.
- **Issue:** A asserção usava `corpo.indexOf("return (")` para achar o primeiro `return (` da tela, mas essa string casa também com `return () => {` (retorno de função de limpeza de um `useEffect` qualquer, ex.: o polling de `scanProgress` em `RadarScreen`) — que aparece bem antes do `return (` de JSX de verdade e produzia um índice errado, fazendo a checagem `idxAdd < idxReturn` falhar mesmo com o `.add(` corretamente posicionado dentro do `useEffect` certo, antes do JSX.
- **Fix:** Trocado por uma regex (`/return \(\s*\n/`) que exige quebra de linha imediatamente após o parêntese — padrão que só o retorno de JSX (`return (\n    <div>`) satisfaz, distinguindo-o de `return () => {`.
- **Files modified:** `web/tests/test_fase23_motion.mjs` (parte do commit `304bcd4`, junto da Task 2 — não gerou commit próprio porque o guardião ainda não tinha sido "fechado" como correto até a Task 2 confirmar GREEN).
- **Verification:** `node web/tests/test_fase23_motion.mjs` passa nas 22 asserções, incluindo a de `RadarScreen` que motivou a correção; reconferido que a asserção equivalente de `MercadoScreen` continua correta com a nova regex.
- **Committed in:** `304bcd4`

**2. [Rule 3 - Blocking] `web/node_modules` ausente no worktree — instalado a partir do lockfile existente, sem pacote novo**
- **Found during:** Task 2, ao rodar `cd web && npx vite build` (passo obrigatório de validação do CLAUDE.md) — o worktree não tinha `node_modules` instalado (isolamento de worktree, não falta declarada no `package.json`).
- **Issue:** `vite`/`@vitejs/plugin-react`/`vite-plugin-pwa` não resolviam; build falhava antes de sequer compilar o código desta task.
- **Fix:** `cd web && npm install` — reinstala exatamente as dependências já pinadas em `web/package-lock.json` (nenhum nome de pacote novo, nenhuma versão alterada). Não se qualifica como "instalação de pacote referenciado pelo plano" (a exclusão de Rule 3 do protocolo é sobre nomes de pacote novos/possivelmente slopsquatted) — é restauração de um `node_modules` local a partir de um lockfile já commitado e confiável.
- **Files modified:** nenhum arquivo versionado (`node_modules/` é gitignored; `git status --porcelain` confirmado vazio após a instalação).
- **Verification:** `npx vite build` concluiu com código 0 depois da instalação; `git diff web/package.json web/package-lock.json` vazio.
- **Committed in:** N/A (não gerou mudança versionada).

---

**Total deviations:** 2 auto-fixed (1 bug de guardião — Rule 1, 1 bloqueio de ambiente — Rule 3, sem instalação de pacote novo)
**Impact on plan:** Nenhum dos dois altera o escopo ou o comportamento entregue — um corrige um falso negativo no próprio guardião novo, o outro só restaura dependências já pinadas para permitir a validação obrigatória. Sem scope creep.

## Issues Encountered

Nenhum além dos dois deviations acima (já documentados como Rule 1 / Rule 3).

## User Setup Required

None - no external service configuration required.

## Pendente de verificação ao vivo (orquestrador)

Confirmado no `<environment_limitation_known_upfront>` do plano: subagentes executores não herdam ferramentas MCP de navegador (`mcp__computer-use__*`, `mcp__claude-in-chrome__*`) — bug upstream anthropics/claude-code#13898, mesmo precedente das Fases 20/21/22. Tudo o que é automatizável foi automatizado (guardião estático, `vite build`, suíte canônica completa). O que só existe ao vivo, PENDENTE, roteiro para o orquestrador:

1. **Watchlist — entrada real:** recarregar a aba Watchlist e observar se os cards entram com fade+subida (não com salto/pop abrupto). Depois adicionar um ticker novo à watchlist e confirmar que **só o card novo** anima — os já existentes não voltam a animar.
2. **Watchlist — não re-anima em atualização:** com a lista já pintada, esperar um tick de preço (ou alternar o filtro de direção e voltar) e confirmar que os cards já vistos **não re-animam** (a régua/manchete pode mudar de valor, mas o card não deve "piscar" fade+subida de novo).
3. **Radar — entrada real:** rodar uma varredura e observar a entrada dos cards; rodar uma segunda varredura (mesmo universo) e confirmar que só ticker que não estava na varredura anterior anima.
4. **Troca de aba:** sair da Watchlist/Radar e voltar — os cards animam de novo (comportamento DELIBERADO, per `<mecanismo_de_visto>`: a tela desmonta ao trocar de aba, o `useRef` zera). Confirmar que isso lê como transição de tela normal, não como bug de "esqueceu quem já vi".
5. **`prefers-reduced-motion` ligado no SO:** nenhum card deve animar; o estado final (opacidade 1, posição natural) deve aparecer direto, sem atraso perceptível. **Limitação de ferramenta já registrada em `20-HUMAN-UAT.md`** — nenhuma ferramenta deste ambiente expõe `Emulation.setEmulatedMedia` via CDP para alternar o media feature. Este item entra no MESMO `20-HUMAN-UAT.md` pendente; não foi criado documento de pendência novo, conforme decisão explícita do `23-CONTEXT.md`.

Item não medido é item ABERTO, não aproximado — nenhum dos cinco itens acima foi declarado verificado neste plano.

## Next Phase Readiness

- `web/tests/test_fase23_motion.mjs` está pronto para ser ESTENDIDO pelo plano 23-03 com a Seção B (MOTION-02, pulso da confirmação de ordem) — cabeçalho e separador de seção já deixados no arquivo.
- Nenhum bloqueio para os planos 23-02 (ILUS-01) ou 23-04 (publicação) — este plano não toca `web/src/pet/` nem `web/tests/test_boris_intro.mjs`.
- Suíte canônica (`bash scripts/executar.sh --testes`) verde: 2021 testes de backend passaram (1 skipped) + 100% dos `web/tests/*.mjs` (incluindo o guardião novo e o da Fase 20, isolado).

---
*Phase: 23-motion-com-proposito-e-ilustracao-unificada*
*Plan: 01*
*Completed: 2026-09-06*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/tests/test_fase23_motion.mjs
- FOUND: .planning/phases/23-motion-com-proposito-e-ilustracao-unificada/23-01-SUMMARY.md
- FOUND commit: 1c5cee8 (Task 1)
- FOUND commit: 304bcd4 (Task 2)

## Orchestrator Live Re-Verification

Servidores dev (`web`:5174 + `api`:8787) iniciados após o merge de 23-01+23-02. Confirmado via `getComputedStyle` em DOM real, tela Radar/Mesa recém-montada (conta de teste, sem forçar dado): **65 cards** com classe `.card-enter` presentes, todos com `animationName: "b3cardEnter"` e `animationDuration: "0.2s"` — bate exatamente com o alvo (~200ms). Comportamento "reseta ao trocar de tela" confirmado por desenho (o `Set` de vistos vive em `useRef` inicializado por mount, não por app inteiro) — não é regressão, é o comportamento especificado no `23-CONTEXT.md`.

Item de `prefers-reduced-motion` comportamental real permanece na mesma pendência já registrada em `20-HUMAN-UAT.md` (nenhuma ferramenta disponível expõe `Emulation.setEmulatedMedia`) — a prova estática (guardião confirma exatamente 2 blocos `@media` inalterados) segue sendo a evidência válida até essa medição acontecer.

Servidores parados ao final (`preview_stop`).
