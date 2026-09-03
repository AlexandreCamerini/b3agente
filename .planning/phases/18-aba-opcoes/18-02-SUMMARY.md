---
phase: 18-aba-opcoes
plan: 02
subsystem: ui

tags: [react, options, portfolio, ui-component]

# Dependency graph
requires:
  - phase: 18-aba-opcoes
    plan: "18-01"
    provides: "hook useOpcoesPropostas(tickers), chave cp.linhaPropostaNaPosicao"
  - phase: 14-opcoes-lastreadas
    provides: "PropostaLastreada component, A.abrirLastreada/abrirCollar/fecharLastreada"
provides:
  - "componente PropostaDaPosicao — detalhe completo (payoff/chips/aceite/encerramento) escopado a uma posição"
  - "CarteiraScreen renderizando o SEGUNDO ponto de PropostaLastreada no app (AtivoCard continua o primeiro)"
  - "âncora id={posicao-TICKER} nos cards de posição, alvo de scroll para o Plano 18-03"
affects: [18-03, 18-04, 18-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Estado local por posição (busy escopado ao componente, não levantado) para não travar botão de uma posição ao aceitar outra"
    - "Guardião generalizado: asserção de contagem global 'window.confirm aparece 1x' virou 'aparece 1x POR handler', suportando múltiplos pontos de entrada legítimos"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_opcoes_collar_ui.mjs

key-decisions:
  - "Guardião test_opcoes_collar_ui.mjs generalizado (não enfraquecido): a asserção antiga só previa 1 handler onAbrirLastreada no arquivo inteiro; a Fase 18 introduziu um segundo ponto de entrada legítimo (PropostaDaPosicao), então a verificação 'confirm antes de executar' passou a rodar por handler, mantendo a garantia original em AMBOS os pontos"
  - "PropostaDaPosicao não recebe posAberta/onAbrir/onFechar prontos de fora — replica o padrão de AtivoCard (App.jsx:3266-3330) internamente, escopado a `t`, porque o closure de AtivoCard não é reusável fora dele (myOptionPositions/opProposta são locais)"

patterns-established:
  - "Guardião de contagem global vira guardião 'por instância' quando um componente ganha um segundo ponto de renderização legítimo — preserva a invariante de segurança sem impedir reuso arquitetural"

requirements-completed: [NAV-02]

duration: ~35min
completed: 2026-09-03
---

# Phase 18 Plan 02: Detalhe de opções dentro da posição Summary

**`PropostaDaPosicao` — SEGUNDO ponto de renderização de `PropostaLastreada` no app, dentro de cada card de posição em `CarteiraScreen`, com aceite/encerramento de venda coberta/put/collar funcionando ali, sem tocar `AtivoCard`.**

## Performance

- **Duration:** ~35 min (leitura de contexto + 2 tasks + suíte canônica completa)
- **Started:** 2026-09-03T11:20:00Z (aprox., após correção de base do worktree)
- **Completed:** 2026-09-03T11:30:18Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- `PropostaDaPosicao({ t, r, cp, operador, A, data, aberto, onToggle })` criado entre `AtivoCard` e `useOpcoesPropostas` — guarda de silêncio (`!r || !r.proposta` → `null`, sem caixa vazia por posição, mesmo raciocínio do ADR-004 documentado em `App.jsx:3484-3489`), linha colapsada com `cp.linhaPropostaNaPosicao`, e réplica fiel (escopada a `t`) de `posAberta`/`onAbrirLastreada`/`onFecharLastreada` do padrão de `AtivoCard`.
- `CarteiraScreen` estendido em 4 pontos cirúrgicos: `operador` entrou na desestruturação de `ctx`; estado `opcoesFor` (mesma forma de `histFor`/`editFor`); chamada de `useOpcoesPropostas(data.positions.map(p => p.t))` com os nomes exatos `opcoesPorTicker`/`opcoesCarregando` que o Plano 18-03 vai consumir; `id={"posicao-" + p.t}` no card da posição (âncora de scroll); `<PropostaDaPosicao>` renderizado dentro do laço, após a linha de links de rodapé.
- `AtivoCard` intocado (confirmado por `git diff` — nenhuma linha do componente original mudou).
- Guardião `test_opcoes_collar_ui.mjs` generalizado: a asserção "`window.confirm(cp.confirmAbrirCollar(` aparece exatamente 1x" (contagem global) virou "exatamente 1x por handler `onAbrirLastreada`" — a Fase 18 introduziu um segundo handler legítimo, e a nova asserção confirma a confirmação-antes-da-execução em AMBOS (T-18-06), não só no original.
- Build limpo (`npx vite build`), suíte canônica completa verde (`bash scripts/executar.sh --testes`: 2010 passed/1 skipped no backend, todos os `web/tests/*.mjs` OK — incluindo os 6 guardiões explicitamente listados no `<verify>` do plano).

## Task Commits

Each task was committed atomically:

1. **Task 1: Componente PropostaDaPosicao — detalhe + aceite escopados a uma posição** - `9fe5bef` (feat)
2. **Task 2: CarteiraScreen consome o hook e renderiza o detalhe por posição** - `6edb046` (feat)

**Plan metadata:** (this commit, SUMMARY.md)

## Files Created/Modified

- `web/src/App.jsx` — `PropostaDaPosicao` novo (entre `AtivoCard` e `useOpcoesPropostas`); `CarteiraScreen` estendido (desestruturação `operador`, estado `opcoesFor`, chamada do hook, `id` de âncora, render de `PropostaDaPosicao` no laço). `AtivoCard` intocado.
- `web/tests/test_opcoes_collar_ui.mjs` — asserção de contagem generalizada de global para por-handler (ver Deviations).

## Decisions Made

- Nenhuma decisão de arquitetura nova — plano seguiu o contrato já congelado em `18-CONTEXT.md`/`18-PATTERNS.md`/`18-01-SUMMARY.md` (réplica disciplinada do padrão de `AtivoCard`, sem endpoint bulk, sem tocar a assinatura de `PropostaLastreada`).
- Bug de ordem de hooks corrigido durante a implementação: o primeiro rascunho de `PropostaDaPosicao` declarava `useState(false)` DEPOIS do `if (!r || !r.proposta) return null;` — violação das Rules of Hooks (early return condicional antes de um Hook). Corrigido movendo `const [busy, setBusy] = useState(false);` para antes da guarda, na mesma edição, antes de qualquer commit ou execução de teste (Rule 1 — bug próprio, corrigido antes de virar defeito observável).

## Deviations from Plan

**1. [Rule 3 — bloqueio] Guardião `test_opcoes_collar_ui.mjs` generalizado de contagem global para contagem por-handler**
- **Encontrado durante:** verificação da Task 1 (`node tests/test_opcoes_collar_ui.mjs` falhando: "window.confirm(cp.confirmAbrirCollar( aparece exatamente 1 vez" — 2 encontrados).
- **Causa:** o guardião original (Fase 17) assumia UM único handler `onAbrirLastreada` no arquivo inteiro. A Fase 18 (Plano 02) introduz, por desenho explícito do plano (Task 1, item 6), uma RÉPLICA legítima desse handler dentro de `PropostaDaPosicao` — segundo ponto de entrada para o mesmo fluxo de aceite de collar, cada um com seu próprio `window.confirm` antes de `A.abrirCollar(`.
- **Fix:** a asserção de contagem global virou uma varredura de TODOS os handlers `onAbrirLastreada` no arquivo (via regex), com a checagem "confirm antes de exec" repetida por handler — preserva a garantia original (T-18-06: nunca falta confirmação antes de travar lastro) em AMBOS os pontos, em vez de só permitir 1.
- **Arquivo modificado:** `web/tests/test_opcoes_collar_ui.mjs`.
- **Commit:** `9fe5bef` (junto com a Task 1, já que o guardião faz parte da verificação da própria task).
- **Nota (regra do repositório "guardiões não se apagam"):** isto não é uma reversão — nenhuma asserção foi removida ou enfraquecida; a cobertura foi ESTENDIDA de 1 ponto de checagem para 2, cada um mantendo a mesma régua original.

Fora isso, plano executado exatamente como escrito.

## Issues Encountered

- Ambiente novo do worktree: `web/node_modules` ausente (worktree recém-criado a partir do merge da Fase 18); `npm install` necessário antes de `npx vite build` — mesmo padrão já documentado no `18-01-SUMMARY.md` e no `CLAUDE.md` do projeto (o próprio `scripts/executar.sh --testes` resolve isso sozinho desde a Fase 5/FIX-C24, usado na verificação final deste plano).
- `bash scripts/executar.sh --testes` rodado dentro do sandbox padrão falhou em 27 testes de backend, todos com `PermissionError: [Errno 1] Operation not permitted` na carga de certificados SSL (`ssl.py:717`, `context.load_verify_locations`) — artefato do sandbox bloqueando acesso a certificados do sistema, não relacionado a nenhuma mudança deste plano (nenhum desses testes toca `App.jsx`/`copy.js`/`CarteiraScreen`). Confirmado reexecutando a suíte completa fora do sandbox: 2010 passed/1 skipped, 0 falhas.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plano 18-03 (tira agregada "Oportunidades de opções") pode consumir diretamente `opcoesPorTicker`/`opcoesCarregando` (nomes já fixados nesta entrega) e a âncora `id={"posicao-" + p.t}` já existe em todo card de posição para o clique-rola-até funcionar sem mudança adicional em `CarteiraScreen`.
- `opcoesFor`/`setOpcoesFor` (estado de CarteiraScreen) está pronto para o Plano 18-03 escrever nele a partir da tira — não precisa de nova prop, é estado local do mesmo componente.
- Nenhum bloqueio identificado.

---
*Phase: 18-aba-opcoes*
*Completed: 2026-09-03*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/tests/test_opcoes_collar_ui.mjs
- FOUND: .planning/phases/18-aba-opcoes/18-02-SUMMARY.md
- FOUND commit: 9fe5bef
- FOUND commit: 6edb046
