---
phase: quick/260907-vwl
plan: 01
subsystem: ui
tags: [react, jsx, design-tokens, ordens-pendentes]

# Dependency graph
requires:
  - phase: Fase 2 (02-02/02-04/02-05, MERC-02..04)
    provides: ctx.mercado (fonte única de abertura/fechamento), copy.js ordemPendenteAvisoCompra/Venda, pill PENDENTE
provides:
  - Bloco visual destacado (T.warn 14%) para o aviso de ordem pendente em BuyModal e SellModal
  - Des-concatenação entre o aviso de pendente e a frase de execução tudo-ou-nada
  - Guardião estendido que trava a simetria e a des-concatenação nos dois ramos
affects: [ui, ordens-pendentes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bloco condicional de estado (T.warn color-mix a 14%) reusado do pill PENDENTE existente, em vez de introduzir novo token visual"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_ordens_pendentes_ui.mjs

deviations-summary: "1 auto-fixed (Rule 1 — bug no próprio guardião novo, achado durante autoverificação)"

key-decisions:
  - "Reusar a linguagem visual do pill PENDENTE (color-mix T.warn 14%) em vez de criar um novo token de cor — consistência com o vocabulário visual já existente no mesmo componente"
  - "Preservar 100% do texto/estilo do ramo mercado-aberto — a mudança é isolada ao ramo fechado===true, sem tocar copy.js"

requirements-completed: [VWL-01]

# Metrics
duration: 11min
completed: 2026-09-07
---

# Quick Task 260907-vwl: Reforçar aviso visual de ordem pendente Summary

**Aviso de ordem pendente sai do slot `T.textFaint` 11px concatenado e ganha bloco próprio com fundo `color-mix(T.warn, 14%)` e texto `T.warn`, simétrico em BuyModal e SellModal.**

## Performance

- **Duration:** ~20 min (23:01 → ~23:21, incluindo o ciclo de autoverificação que achou e corrigiu o guardião)
- **Started:** 2026-09-07T23:01:10-03:00
- **Completed (tasks do plano):** 2026-09-07T23:11:43-03:00
- **Tasks:** 2/2 completos (+ 1 correção pós-verificação no próprio guardião novo)
- **Files modified:** 2

## Accomplishments
- `BuyModal`/`SellModal` renderizam, quando `fechado === true`, um bloco próprio com fundo `color-mix(in srgb, T.warn 14%, transparent)` e texto `T.warn` contendo só o aviso de pendente — não mais diluído em letra miúda
- A frase de execução tudo-ou-nada ("Esta simulação executa por completo ou não executa...") saiu da concatenação e ficou isolada no `div` `T.textFaint` 11px de sempre, presente nos dois estados (aberto/fechado)
- Ramo `fechado === false` (mercado aberto) permanece byte-idêntico ao comportamento anterior — mesma string, mesmo slot, mesmo estilo
- Guardião `test_ordens_pendentes_ui.mjs` estendido com 6 novos asserts que travam a simetria COMPRA/VENDA e impedem a volta silenciosa ao slot apagado ou à concatenação

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Destacar o aviso de pendente nos dois modais (COMPRA e VENDA)** - `9f971ec` (feat)
2. **Task 2: Estender o guardião de ordens pendentes e rodar a suíte canônica** - `77888bf` (test)
3. **Correção pós-verificação: assert estrutural em vez de janela de caracteres** - `d78a0a5` (fix — Rule 1, achado durante autoverificação, ver Deviations abaixo)

**Plan metadata:** commit de docs (SUMMARY/STATE) fica a cargo do orquestrador, não incluído aqui.

## Files Created/Modified
- `web/src/App.jsx` - `BuyModal` (~linha 7605) e `SellModal` (~linha 7712 após a edição) ganham bloco condicional `{fechado && <div ...>}` com o aviso destacado; o `div` `T.textFaint` de sempre passou a alternar só entre a frase de aberto+tudo-ou-nada e só a frase de tudo-ou-nada
- `web/tests/test_ordens_pendentes_ui.mjs` - bloco novo de asserts (SellModal usa T.warn; aviso dentro de janela com `color-mix(...T.warn)`; aviso não aparece mais na mesma expressão que "preenchimento parcial de ordem"; frase de tudo-ou-nada presente nos dois componentes)

## Decisions Made
- Reusar a linguagem visual do pill "PENDENTE" (já existente, `color-mix` T.warn 14%) em vez de introduzir um novo token/cor — zero cor literal nova, guardião de tema (`test_chart_colors_theme_aware.mjs`) intocado
- `web/src/copy.js` não editado — nenhum texto novo inventado, só mudança de slot visual da mesma string

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Assert de des-concatenação do guardião novo usava janela de caracteres frágil**
- **Found during:** Autoverificação pós-Task 2 (sugerida pelo advisor antes de declarar a tarefa concluída) — revertendo temporariamente `App.jsx` para o padrão antigo (concatenado) e confirmando que os 4 asserts novos realmente ficam vermelhos, 1 deles passou (falso negativo) no padrão antigo do SellModal.
- **Issue:** O assert original comparava `corpo.slice(i, i + 220).includes("preenchimento parcial de ordem")` — uma janela fixa de 220 caracteres a partir da chamada de `ordemPendenteAviso(Compra|Venda)`. A distância real até a frase variava por ramo: 183 no BuyModal antigo, 222 no SellModal antigo (a variante de venda tem um trecho a mais, "Registro vai para o histórico do ativo."), e ~207 no código novo (correto) de ambos os modais. Uma janela fixa não conseguia diferenciar de forma confiável "mesma expressão concatenada" de "elementos irmãos" — o caso do SellModal antigo (222 > 220) escapava silenciosamente da detecção.
- **Fix:** Trocado o critério de distância por um critério estrutural: existe um `</div>` fechando o bloco do aviso ANTES da frase de tudo-ou-nada aparecer. Verificado com o mesmo procedimento (reversão temporária do `App.jsx` para o padrão antigo, sem tocar em nenhum commit) que agora os 4 asserts (2 por modal) ficam corretamente vermelhos no padrão antigo e verdes no código atual.
- **Files modified:** `web/tests/test_ordens_pendentes_ui.mjs`
- **Verification:** `node web/tests/test_ordens_pendentes_ui.mjs` (verde no código atual, 4 falhas confirmadas ao reverter temporariamente `App.jsx` — reversão nunca commitada, `git diff --stat web/src/App.jsx` vazio depois de restaurado); `bash scripts/executar.sh --testes` verde depois da correção (2030 passed + 1 skipped, todos os `web/tests/*.mjs` OK)
- **Committed in:** `d78a0a5`

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug no próprio guardião novo, não no código de produção)
**Impact on plan:** Nenhum impacto no comportamento entregue pela Task 1 — o bug estava só na precisão do guardião da Task 2, corrigido antes de declarar a tarefa concluída. Sem scope creep: a correção ficou restrita ao mesmo arquivo e ao mesmo par de asserts que a Task 2 introduziu.

As únicas ações operacionais fora do texto literal do plano (não deviations de código): instalar `web/node_modules` num worktree novo, ausente por ser gitignored — pré-requisito mecânico para rodar `npx vite build` e a suíte web.

## Issues Encountered
- Worktree novo nasceu sem `web/node_modules` (gitignored) — `npm install` em `web/` resolvido antes de rodar `npx vite build`/suíte web, sem impacto no código do plano.
- `npx vite build --root web` (comando exato do plano) falha porque o `npx` resolve um Vite global (v8) em vez do Vite 6 local do projeto, que não aceita `--root` como flag (só como argumento posicional `build [root]`). Rodado como `cd web && npx vite build` (equivalente funcional, usa o Vite 6.4.3 local) — build passou sem erro de sintaxe JSX.
- `bash scripts/executar.sh --testes` usa `mktemp -d` sem `-t`/prefixo, que tentou escrever fora do diretório de trabalho — rodado com sandbox de shell desabilitado para esta chamada específica (restrição de ambiente de execução, não do projeto).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Mudança é 100% cliente/apresentação — nenhuma dependência nova, nenhuma migração de dado
- **Publicação não faz parte desta quick task** (fora de escopo por decisão explícita do plano): levar a produção exige `scripts/bump.sh` seguido de `scripts/publicar-web.sh` — nunca editar `server/web_dist` direto
- Suíte canônica (`bash scripts/executar.sh --testes`) verde: 2030 passed + 1 skipped (pytest), todos os `web/tests/*.mjs` OK, incluindo o guardião estendido

## Self-Check: PASSED

- FOUND: web/src/App.jsx (bloco `fechado &&` presente em BuyModal e SellModal)
- FOUND: web/tests/test_ordens_pendentes_ui.mjs (asserts novos presentes, versão estrutural)
- FOUND: commit 9f971ec
- FOUND: commit 77888bf
- FOUND: commit d78a0a5
- CONFIRMED (autoverificação extra, sugerida pelo advisor): os 4 asserts novos de des-concatenação/color-mix vão VERMELHO quando `App.jsx` é revertido (em memória, nunca commitado) para o padrão antigo — não passam de forma vácua

---
*Phase: quick/260907-vwl*
*Completed: 2026-09-07*
