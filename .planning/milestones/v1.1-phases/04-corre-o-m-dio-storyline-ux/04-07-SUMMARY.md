---
phase: 04-corre-o-m-dio-storyline-ux
plan: 07
subsystem: ui
tags: [react, finance, copy, carteira, diversificacao, fix-c05]

# Dependency graph
requires:
  - phase: 04-corre-o-m-dio-storyline-ux (04-01)
    provides: "conceito + verbete 'diversificacao' (conceitos.py/kb.py), POST /api/conceito/diversificacao"
  - phase: 04-corre-o-m-dio-storyline-ux (04-06)
    provides: "App.jsx/finance.js estáveis nos mesmos componentes vizinhos (CarteiraScreen/CapitalCurve), sem overlap de arquivo com este plano"
provides:
  - "concentracaoMaxima(positions, quotes, patr) — maior posição em % do patrimônio, mesma família de portfolioMetrics"
  - "copy.js: chaves concentracaoTitulo/concentracaoCorpo/concentracaoLink nos dois modos"
  - "CarteiraScreen: card de aviso T.warn quando concentração > 50%, com link 'saiba mais' para o verbete diversificacao"
  - "A.abrirVerbete(cid, dados) — ação nova de drill-down comum, sem telemetria de coach_tip_shown/gestoUso"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ação de drill-down 'comum' separada das ações especializadas (openConceito via proativa, abrirSetor via sublinhado pontilhado) para não contaminar métricas de origem específica"

key-files:
  created:
    - web/tests/test_concentracao_carteira.mjs
  modified:
    - web/src/finance.js
    - web/src/copy.js
    - web/src/App.jsx
    - web/tests/test_finance.mjs

key-decisions:
  - "concentracaoMaxima é PURA e não aplica o limiar de 50% — só devolve o número (maior posição/valor/pct); quem decide o corte é a UI (LIMIAR_CONCENTRACAO em App.jsx). Mantém o limiar visível num lugar só e testável."
  - "Nova ação A.abrirVerbete em vez de reusar openConceito/abrirSetor: openConceito marca viaProativa+track('coach_tip_shown') (via do gatilho, one-shot); abrirSetor incrementa gestoUso (medição do sublinhado pontilhado). Um link comum de aviso não é nenhuma das duas — reusar contaminaria a medição existente."
  - "Link 'saiba mais' só renderiza quando ctx.didatica && ctx.didatica.ligada — com a camada desligada o backend devolveria null e a folha mostraria erro; o card de aviso em si continua aparecendo (é determinístico, independente da camada de conceitos)."

requirements-completed: [FIX-C05]

# Metrics
duration: ~35min
completed: 2026-08-22
---

# Phase 4 Plan 07: Aviso de concentração alta na Carteira Summary

**`concentracaoMaxima()` (aritmética pura, mesma família de `portfolioMetrics`) alimenta um card `T.warn` no `CarteiraScreen` que avisa — sem bloquear nada — quando um único ativo passa de 50% do patrimônio simulado, com "saiba mais" abrindo o verbete `diversificacao` (backend do Plano 04-01) ancorado no ticker e no percentual reais da carteira: fecha FIX-C05 e tira "diversificação" da lista de conceitos obrigatórios do CLAUDE.md com zero ocorrência no produto.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-08-22T02:37:09Z
- **Tasks:** 2/2 completed
- **Files modified:** 5 (3 arquivos-fonte, 1 teste existente ajustado, 1 teste novo)

## Accomplishments
- `concentracaoMaxima(positions, quotes, patr)` (`web/src/finance.js`) — percorre `positions` uma vez, usa o MESMO `markPrice` de `portfolioMetrics` (garante que o `pct` bata com o patrimônio exibido na tela), guard clauses para `patr <= 0`/`positions` vazio/nulo, `Number(qty) || 0` para nunca produzir `NaN`, empate de valor resolvido pela ordem de `positions` (determinístico, sem `sort`). Não aplica limiar — devolve só o número.
- `web/src/copy.js` ganha `concentracaoTitulo`/`concentracaoCorpo`/`concentracaoLink` nos DOIS modos (guardião de chaves espelhadas `test_copy_theme.mjs` continua verde); corpo verbatim do UI-SPEC — voz de professor no Estudo, voz de mesa no Operador, sem vocabulário de ordem de operação no ramo Estudo.
- `web/src/App.jsx`: `LIMIAR_CONCENTRACAO = 50` (constante nomeada, topo do módulo); card de aviso renderizado em `CarteiraScreen` entre o grid de KPIs e o ramo de portfólio vazio, só quando `conc.pct > LIMIAR_CONCENTRACAO` (50% exatos não dispara); gramática visual `T.warn` idêntica à caixa já estabelecida no `BuyModal`/`SellModal` (nunca `T.negative` — é aviso educacional, não erro); cabeçalho ícone-em-círculo reusado de "FATOS RELEVANTES" recolorido para `T.warn`; nova ação `A.abrirVerbete(cid, dados)` que abre a folha do conceito sem tocar em `track()`/`gestoUso`.
- Guardião novo `web/tests/test_concentracao_carteira.mjs` (19 asserções) trava: limiar e condição de render estrita; `T.warn` presente e `T.negative` ausente no bloco do card; rótulo único "CONCENTRAÇÃO ALTA"; `A.abrirVerbete` sem `track(`/`gestoUso`; chamada do link com `{ticker, pct}`; ausência de `disabled=` novo em todo `CarteiraScreen`; as 3 chaves de copy nos dois modos com texto IDÊNTICO byte a byte ao UI-SPEC; link condicionado a `ctx.didatica.ligada`.
- Suíte canônica completa (`bash scripts/executar.sh --testes`) verde: **1325 testes backend passed, 1 skipped** (pré-existente) + **95/95 `web/tests/*.mjs` OK** (94 anteriores + 1 novo). `npx vite build` conclui sem erro.

## Task Commits

Each task was committed atomically (Task 1 seguiu TDD — RED/GREEN):

1. **Task 1 RED: casos falhando para concentracaoMaxima** - `1f2d5b0` (test)
2. **Task 1 GREEN: aritmética pura da concentração (finance.js)** - `6a28590` (feat)
3. **Task 2: aviso de concentração alta na Carteira, com link para o verbete** - `5670d48` (feat)

_Task 1 era `tdd="true"` — RED confirmado rodando `node tests/test_finance.mjs` antes da implementação (`SyntaxError: concentracaoMaxima não exportado`), commitado separado do GREEN. Task 2 não era TDD — guardião escrito junto do código no mesmo commit._

## Files Created/Modified
- `web/src/finance.js` — `concentracaoMaxima(positions, quotes, patr)` novo (aritmética pura, mesma família de `portfolioMetrics`)
- `web/src/copy.js` — 3 chaves novas (`concentracaoTitulo`/`concentracaoCorpo`/`concentracaoLink`) nos dois modos
- `web/src/App.jsx` — import de `concentracaoMaxima` (linha 15); `LIMIAR_CONCENTRACAO = 50` (constante nomeada, topo do módulo); `A.abrirVerbete` (ação nova, mesmo bloco de `openConceito`/`abrirSetor`); card de aviso em `CarteiraScreen`
- `web/tests/test_finance.mjs` — bloco novo (`concentracaoMaxima`): 7 casos (base do plano, vazio, patr<=0, tudo nulo, sem cotação/avg, qty inválido sem NaN, empate determinístico, consistência com `portfolioMetrics.posVal`)
- `web/tests/test_concentracao_carteira.mjs` (novo) — guardião estático do contrato visual/comportamental FIX-C05

## Decisions Made
Ver `key-decisions` no frontmatter (função pura sem limiar embutido; ação de drill-down nova em vez de reusar `openConceito`/`abrirSetor` para não contaminar telemetria existente; link condicionado à camada de conceitos ligada).

## Deviations from Plan

None - plan executed exactly as written. O guardião `test_concentracao_carteira.mjs` foi escrito pelo executor seguindo a especificação de casos do plano (não veio pronto); nenhum ajuste de código de produto foi necessário além do que o plano já descrevia. As linhas citadas no plano (`interfaces`) já estavam levemente desatualizadas em relação ao fonte vivo (ex.: `CarteiraScreen` em 3615/3620 em vez de 3493, `statusIndisponivel` do `BuyModal` já incluindo o texto tudo-ou-nada do FIX-C14 e `DISCLAIMERS.trade` do FIX-C13 — planos 04-02/04-03 já haviam sido executados) — o plano já avisava "re-grep obrigatório", e o re-grep confirmou os mesmos padrões estruturais citados (caixa `T.warn`, cabeçalho ícone-em-círculo, bloco de ações `openConceito`/`abrirSetor`), só com números de linha diferentes.

## Issues Encountered
- `web/node_modules` não estava instalado neste worktree (mesmo achado recorrente dos Planos 04-03 a 04-06 — worktrees não compartilham `node_modules` do clone principal). Rodei `npm ci` em `web/` antes do primeiro `npx vite build`; não afeta o clone principal nem outros worktrees (gitignored).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- FIX-C05 fechado ponta a ponta: backend (conceito/verbete `diversificacao`, Plano 04-01) + frontend (aritmética pura, copy nos dois modos, aviso na Carteira com drill-down, este plano). Suíte canônica completa verde (1325 pytest + 95 web/tests).
- **Este é o ÚLTIMO plano da Fase 4** (wave 4/4). Os 9 achados Médio STORY+UX do REPORT-01 (FIX-C01..C05, FIX-C13..C16) estão fechados pelos 7 planos da fase (04-01 a 04-07).
- Verificação AO VIVO recomendada pelo plano (carteira com posição acima de 50% mostra o card e "saiba mais" abre a folha do conceito com o ticker/percentual certos; carteira equilibrada não mostra nada) NÃO foi executada nesta sessão — o plano marca essa checagem como "recomendada", não bloqueante, e a suíte automatizada (incluindo o novo `test_concentracao_carteira.mjs`) cobre o contrato visual/comportamental por asserção estática. Fica como item de verificação manual opcional para quem revisar esta entrega com o servidor no ar.
- Nenhum arquivo de `server/` foi tocado por este plano (confirmado por `git status`/commits) — consistente com o escopo (front-only).
- Sem bloqueios conhecidos.

---
*Phase: 04-corre-o-m-dio-storyline-ux*
*Completed: 2026-08-22*

## Self-Check: PASSED

- FOUND: web/src/finance.js
- FOUND: web/src/copy.js
- FOUND: web/src/App.jsx
- FOUND: web/tests/test_finance.mjs
- FOUND: web/tests/test_concentracao_carteira.mjs
- FOUND: .planning/phases/04-corre-o-m-dio-storyline-ux/04-07-SUMMARY.md
- FOUND commit: 1f2d5b0 (Task 1 RED)
- FOUND commit: 6a28590 (Task 1 GREEN)
- FOUND commit: 5670d48 (Task 2)
