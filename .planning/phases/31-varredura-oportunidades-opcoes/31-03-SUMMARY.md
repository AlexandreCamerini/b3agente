---
phase: 31-varredura-oportunidades-opcoes
plan: 03
subsystem: ui
tags: [react, svg, responsive, payoff, opcoes, accessibility]

# Dependency graph
requires:
  - phase: 24-30 (aba-opcoes)
    provides: "PayoffChart.jsx já em produção no caminho MCP/lastreado, componente pronto a tornar responsivo"
provides:
  - "PayoffChart.jsx legível em 375px: piso de fontSize >= 11 (SVG user-space ~= CSS px na largura do cartão)"
  - "supressão determinística de rótulo sobreposto (breakeven por ordem em X, cenário por proximidade x/y) sem perder a marca visual nem a descrição acessível"
  - "contenção de largura no wrapper (minWidth:0/maxWidth:100%) para não estourar coluna grid estreita"
  - "guardião estático novo (web/tests/test_payoff_responsivo.mjs) trancando D-07 e o fence D-08"
affects: [31-04, futuras fases de polish/overlay do payoff]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "supressão de rótulo por IIFE dentro do JSX map: a marca visual (line/circle) é sempre desenhada, só o <text> é condicional — mesma disciplina de 'closed door retorna [], nunca esconde dado' aplicada a texto em vez de estrutura de dado"
    - "fontSize resolvido via constante nomeada (FONTE_MIN/FONTE_SETA) em vez de número mágico espalhado — precedente para qualquer ajuste futuro de tipografia SVG neste arquivo"

key-files:
  created:
    - web/tests/test_payoff_responsivo.mjs
  modified:
    - web/src/opcoes/PayoffChart.jsx

key-decisions:
  - "Fonte extraída via regex resolve tanto fontSize=\"N\" literal quanto fontSize={CONST} — o guardião não fica preso a um formato de código específico, só ao valor final resolvido"
  - "Ordenação por X só para breakevens (regra explícita do plano); cenários mantêm a ordem original do serviço, com supressão por proximidade x/y (52/14) em vez de por ordem — plano não pediu reordenar cenários"

patterns-established:
  - "Pattern: guardião estático de legibilidade tipográfica em SVG — extrai fontSize (literal ou constante), resolve o valor real, compara contra piso numérico"

requirements-completed: [SC-5, SC-7]

# Metrics
duration: ~20min
completed: 2026-09-14
---

# Phase 31 Plan 03: PayoffChart responsivo em 375px Summary

**`PayoffChart.jsx` ganha piso de tipografia (>=11 unidades/CSS px), geometria recalculada (viewBox 320×192, PAD_T=18/PAD_B=32) e supressão determinística de rótulo sobreposto — sem tocar em cálculo financeiro nem reabrir overlay/interatividade (D-08 intocado) — mais um guardião estático de 19 asserções que tranca a regressão.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-09-14T15:48:36Z
- **Tasks:** 2/2
- **Files modified:** 2 (1 modificado, 1 criado)

## Accomplishments
- Todo texto do SVG (`<text>`) passa a ter piso de 11 unidades user-space (`FONTE_MIN=11.5` para breakeven/cenário, `FONTE_SETA=14` para as setas de lado ilimitado) — antes `fontSize="9.5"`/`"11"`, que em ~315px de largura real (aparelho de 375px) renderizava abaixo de 10px CSS.
- Geometria recalculada para caber o texto maior sem cortar no eixo: `H` 180→192, `PAD_T` 14→18, `PAD_B` 26→32. `W` permanece 320 (não é sobre enquadramento, é sobre respiro vertical).
- Âncoras de texto recalculadas para o tamanho maior: limiar de breakeven 22→28 (dos dois lados), limiar de cenário `W-44`→`W-52`.
- Supressão determinística de rótulo sobreposto: breakevens ordenados por X, texto só desenhado quando a distância ao último rótulo desenhado é >= 44 unidades; cenários com texto suprimido quando um rótulo já desenhado fica a menos de 52 em X **e** 14 em Y. Em ambos os casos, a marca visual (linha tracejada / círculo) continua sendo desenhada **sempre** — só o texto redundante some, e o `aria-label`/`<title>` do SVG seguem listando todos os breakevens.
- Contenção de largura: `caixa()` ganhou `minWidth: 0, maxWidth: "100%"` (filho de grid tem `min-width: auto` por padrão e pode estourar a coluna em 375px); `<svg>` ganhou `maxWidth: "100%"` no style.
- Guardião novo (`web/tests/test_payoff_responsivo.mjs`, 19 asserções) trancando: piso de fontSize (resolvendo literal ou constante), responsividade do `<svg>` (sem largura/altura fixa), `minWidth:0`, fence D-08 (zero `useState`/`onClick`/`onPointer`/`onTouch`/`onMouse`, assinatura de 4 props), zero aritmética sobre `net_cost`/`max_gain`/`max_loss`, a `<line>` do breakeven nunca atrás da mesma guarda condicional que suprime o `<text>`, e `aria-label`/`<title>` continuando completos.

## Task Commits

Each task was committed atomically:

1. **Task 1: piso de legibilidade, geometria e não-sobreposição de rótulos** - `a18803c` (feat)
2. **Task 2: guardião estático da legibilidade e do fence D-08** - `34f12b5` (test)

**Plan metadata:** (this commit, docs: complete plan)

## Files Created/Modified
- `web/src/opcoes/PayoffChart.jsx` - piso de tipografia, geometria, supressão de rótulo sobreposto, contenção de largura no wrapper/SVG
- `web/tests/test_payoff_responsivo.mjs` - guardião estático novo (19 asserções + 5 sanidades embutidas)

## Decisions Made
- Nenhuma decisão de produto nova nesta execução — seguiu as decisões já travadas em `31-CONTEXT.md` (D-07/D-08). A única escolha de implementação livre foi resolver `fontSize` tanto por literal quanto por constante nomeada no guardião, para não travar o teste num formato de código específico caso um ajuste futuro renomeie/reorganize as constantes.

## Deviations from Plan

None - plan executado exatamente como escrito. As cinco edições cirúrgicas (a-e) da Task 1 e as sete asserções (1-7) da Task 2, descritas no `31-03-PLAN.md`, foram implementadas sem necessidade de correção de bug, funcionalidade faltante ou bloqueio.

## Issues Encountered

A primeira versão do guardião localizava o bloco de breakevens procurando o texto do COMENTÁRIO `"3. breakevens"` no fonte já sem comentários (`semComentario`) — como o próprio comentário é removido por esse helper, a busca falhava (3 asserções FALHOU). Corrigido trocando os marcadores para trechos de CÓDIGO (`"[...marcas].sort"` até `"cenarios.map((s, i)"`), que sobrevivem à remoção de comentários. Corrigido antes do commit da Task 2 — não é deviation de produto, é acerto do próprio teste durante a escrita (RED→GREEN normal de TDD informal, sem task `tdd="true"` declarada no plano).

## User Setup Required

None - no external service configuration required.

## Verification Evidence

- `cd web && npx vite build` — verde, `✓ built in 988ms` (rodado após Task 1 e novamente após a prova negativa/reversão da Task 2).
- `node web/tests/test_payoff_responsivo.mjs` — 19/19 `ok`, exit 0.
- **Prova negativa real** (baixar `FONTE_MIN` de `11.5` para `9.5`):
  ```
  $ sed -i.bak 's/const FONTE_MIN = 11.5;/const FONTE_MIN = 9.5;/' web/src/opcoes/PayoffChart.jsx
  $ node web/tests/test_payoff_responsivo.mjs; echo "EXIT=$?"
  ...
  FALHOU toda fontSize de <text> no SVG tem piso >= 11 (D-07, legibilidade em 375px)
  ...
  1 FALHA(S)
  EXIT=1
  $ git checkout -- web/src/opcoes/PayoffChart.jsx && rm -f web/src/opcoes/PayoffChart.jsx.bak
  $ git diff --stat web/src/opcoes/PayoffChart.jsx   # vazio
  $ node web/tests/test_payoff_responsivo.mjs; echo "EXIT=$?"   # 19/19 ok, EXIT=0
  ```
  Só a regra do piso caiu — as outras 18 continuaram `ok`, confirmando que o guardião mede exatamente a regra pretendida, sem falso positivo cruzado.
- `node web/tests/test_opcoes_analisar_ui.mjs` (guardião irmão da F3) — continua verde, exit 0, sem regressão nas asserções antigas sobre `PayoffChart`.
- Contagem de `.mjs`: **147 → 148** (arquivo novo, `ls web/tests/*.mjs | wc -l`).
- Suíte canônica completa, `bash scripts/executar.sh --testes`: **2899 passed, 5 skipped, 3 xfailed, 0 failed** (backend) + **148/148 `.mjs` OK**, exit 0.
  - **Nota de ambiente:** a primeira tentativa rodou dentro do sandbox padrão e reportou 27 falhas de backend — todas `PermissionError: [Errno 1] Operation not permitted` em `ssl.py:717` (`context.load_verify_locations`), i.e. o sandbox bloqueando I/O de certificado TLS necessário para os testes de rede mockados/HTTP. Confirmado como artefato de ambiente (não relacionado a este plano, que só tocou `web/src/opcoes/` e `web/tests/`) reexecutando com `dangerouslyDisableSandbox: true` — suíte inteira ficou verde. Consistente com a nota já registrada em `MEMORY.md`: "sandbox mente (26 falsas)".

## Next Phase Readiness

`PayoffChart.jsx` está pronto para os planos seguintes da Fase 31 (31-02 rota+cache de vencimentos, 31-04 bloco de Posições) reutilizá-lo sem nenhuma mudança de contrato de props — os dois call sites em `OpcoesScreen.jsx` (linhas ~922 e ~1100) não precisaram de alteração. Overlay de múltiplos candidatos e interatividade (D-08) seguem explicitamente fora de escopo, candidatos a uma fase de polish futura conforme `31-CONTEXT.md`.

Nenhum push a `origin`, nenhum bump, nenhuma publicação — mesmo padrão do resto da Fase 31 em execução.

---
*Phase: 31-varredura-oportunidades-opcoes*
*Completed: 2026-09-14*

## Self-Check: PASSED

- FOUND: `web/src/opcoes/PayoffChart.jsx`
- FOUND: `web/tests/test_payoff_responsivo.mjs`
- FOUND: `.planning/phases/31-varredura-oportunidades-opcoes/31-03-SUMMARY.md`
- FOUND: commit `a18803c`
- FOUND: commit `34f12b5`
