---
phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
plan: 02
subsystem: ui
tags: [design-system, spacing, ritmo, guardiao, hier-02]

# Dependency graph
requires:
  - phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura
    provides: "SinalChip peso=contexto/primario, LinhaContexto, PlanoOperacionalBloco, HistoricoPill, ordem de leitura do AtivoCard"
provides:
  - "const SP = {1:4,2:8,3:12,4:16,5:20,6:24,8:32} em web/src/App.jsx"
  - "SP_OPTICO_CHIP_PRIMARIO/SP_OPTICO_ANEL — lista fechada de exceções ópticas (D-16)"
  - "web/tests/test_ritmo_sp.mjs — guardião ban-list de px solto de espaçamento no card"
  - "área de toque >=44px do chip de fundamento tocável (D-18) sem regressão de layout"
affects: [43-03, 43-04, 43-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Constante de escala nomeada (SP[N]) + lista fechada de exceções ópticas comentadas, travadas por guardião grep-estático — primeiro precedente do tipo no repo"
    - "Padding + margem negativa simétrica (sinal oposto) para ampliar área de TOQUE sem alterar a caixa de LAYOUT — técnica genérica de CSS, sem analog anterior no código"

key-files:
  created:
    - web/tests/test_ritmo_sp.mjs
  modified:
    - web/src/App.jsx
    - web/tests/test_sinal_chip_ui.mjs

key-decisions:
  - "Caixa 'Sem leitura do motor' do AtivoCard (ponto fora da tabela do UI-SPEC, dentro do recorte D-14) migrada por Claude's Discretion: mesmo padding óptico da manchete (SP_OPTICO_CHIP_PRIMARIO), marginTop no degrau mais próximo (empate 8/12 → SP[3]), marginTop interno 2px→SP[1] (empate 0/4 → arredonda p/ cima) — registrado para o checkpoint 43-05"

patterns-established:
  - "Guardião ban-list de px solto (test_ritmo_sp.mjs): detector autotestado com strings sintéticas antes de varrer o código real — prova que o detector funciona antes da migração existir"

requirements-completed: [RITMO-01]

# Metrics
duration: ~40min
completed: 2026-09-27
---

# Phase 43 Plan 02: Escala 4/8pt (RITMO-01) + área de toque do fundamento (D-18) Summary

**Constante nomeada `SP` + duas exceções ópticas fechadas migram todo margin/padding/gap do `AtivoCard` (entre blocos e dentro deles) para a escala 4/8pt, com guardião novo autotestado que reprova qualquer px solto — inclui a correção do alvo de toque do chip de fundamento (D-18).**

## Performance

- **Duration:** ~40 min
- **Tasks:** 2 completadas (TDD RED→GREEN)
- **Files modified:** 2 (+ 1 criado)

## Accomplishments
- `const SP = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32 };` + `SP_OPTICO_CHIP_PRIMARIO`/`SP_OPTICO_ANEL` (lista fechada, D-16) em `web/src/App.jsx`, ao lado de `REC_STYLE`
- Migração completa da tabela D-15 do UI-SPEC: `SinalChip` (primário e contexto), `LinhaContexto`, `PlanoOperacionalBloco`, `HistoricoPill`, `TimingBadge` (só o `marginTop` de separação entre blocos), wrapper de elegibilidade e o recorte do `AtivoCard` entre a manchete e `anVencida`
- D-18: `SetorAlvo setorId="fundamento"` ganha `padding: ${SP[3]}px ${SP[2]}px` + `margin: -${SP[3]}px -${SP[2]}px` (simétrico, sinal oposto) — área de toque ampliada sem empurrar os chips vizinhos na `LinhaContexto` (`flex-wrap`/`gap` intocados)
- Guardião novo `web/tests/test_ritmo_sp.mjs` (RED→GREEN): detector de ban-list de `margin`/`padding`/`gap`/`rowGap`/`columnGap` px solto, autotestado com 5 strings de rejeição + 6 de aceitação ANTES de varrer o código real (prova que o detector funciona no RED)
- `test_sinal_chip_ui.mjs`: 2 asserções reconciliadas com nota "REVERSÃO DELIBERADA (2026-09-27, Fase 43, RITMO-01)" — mesmo contrato visual (anel 36px, chip `4px 8px`), agora expresso via `SP`/`SP_OPTICO_ANEL`
- Nenhuma outra tela migrada (D-15): `TimingBadge` interno (padding "8px 11px"), `PlanRuler`, `FundamentoTabela`, header de identidade/preço e cauda seguem com os valores herdados, fora do escopo D-14

## Task Commits

Each task was committed atomically (TDD RED→GREEN):

1. **Task 1 RED:** `8b49b6e` — test(43-02): guardião de ritmo 4/8pt (RED)
2. **Task 2 GREEN:** `259b23f` — feat(43-02): constante SP, migração do card e área de toque do fundamento (GREEN)

## Files Created/Modified
- `web/tests/test_ritmo_sp.mjs` (novo) — guardião ban-list de px solto de espaçamento, com autoteste do detector
- `web/src/App.jsx` — `const SP`, `SP_OPTICO_CHIP_PRIMARIO`, `SP_OPTICO_ANEL`; migração de `SinalChip`/`LinhaContexto`/`PlanoOperacionalBloco`/`HistoricoPill`/`TimingBadge`/`AtivoCard`; área de toque D-18
- `web/tests/test_sinal_chip_ui.mjs` — 2 asserções reconciliadas (size={36}→size={SP_OPTICO_ANEL}, padding "4px 8px"→`${SP[1]}px ${SP[2]}px`)

## Decisões autônomas

1. **[Claude's Discretion, Task 2.3] Caixa "Sem leitura do motor" (`AtivoCard`, estado sem decisão)** — ponto não listado na tabela "Mapeamento valor herdado → degrau" do UI-SPEC, mas dentro do recorte D-14 (mesma caixa visual da manchete, no branch em que `decM` é `null` e `contexto !== "radar"`). Migrado assim: `marginTop: SP[3]` (empate 8/12 → arredonda p/ cima, mesma regra da manchete real), `padding` óptico idêntico ao da manchete (`SP_OPTICO_CHIP_PRIMARIO`, porque é literalmente a mesma caixa visual em outro estado), `marginTop` do texto interno `"2px"` → `SP[1]` (empate 0/4 → arredonda p/ cima). Nenhuma mudança visual perceptível (2px→4px, 11px→12px, 9/11px preservados). Registrado aqui para o checkpoint humano do 43-05 confirmar.

Nenhuma outra decisão fora do que o `43-02-PLAN.md` especificava — a tabela D-15 do UI-SPEC foi seguida verbatim para todos os demais pontos.

## Deviations from Plan

None além da decisão autônoma documentada acima (que o próprio plano já antecipava como "Claude's Discretion" no Task 2, item 3).

## Issues Encountered

Nenhum. `npx cap copy ios` reportou `ERROR: failed to copy trust settings of system certificate-25291` repetidamente — ruído de keychain do sandbox (Capacitor tentando copiar certificados de confiança do sistema), não afeta a cópia dos assets web nem o resultado do comando (`copy ios` terminou com sucesso, `test_ios_assets.mjs` confirma paridade de chunks).

## Validação executada

- `node tests/test_ritmo_sp.mjs` — 0 falhas (autoteste do detector + 5 escopos zero-violação + pontos específicos do `<behavior>`)
- `node tests/test_sinal_chip_ui.mjs` — 0 falhas (44 asserções, contrato do `SinalChip`/`LinhaContexto`/`PlanoOperacionalBloco`/`AtivoCard` intacto)
- Loop completo `for t in tests/*.mjs` — 0 falhas em todos os arquivos (`TOTAL_FALHAS=0`)
- `npx vite build` — build limpo (warning de chunk >500kB pré-existente, fora do escopo desta fase)
- `npx cap copy ios` — copiado com sucesso; `test_ios_assets.mjs` confirma paridade de chunks dist↔ios após a cópia
- Backend pytest — não executado (plano front-only, confirmado pelo `sequential_execution` desta sessão)

## User Setup Required

None - nenhuma configuração externa necessária.

## Next Phase Readiness
- `SP`/`SP_OPTICO_CHIP_PRIMARIO`/`SP_OPTICO_ANEL` disponíveis para o 43-03/43-04 (`HistoricoPill` com `microtexto`, os 3 `SinalChip contexto` da `AnalysisView`) fiarem o próprio espaçamento novo neles — nenhuma constante nova de espaçamento deveria ser necessária.
- `test_ritmo_sp.mjs` já fiscaliza qualquer código novo que toque `SinalChip`/`LinhaContexto`/`PlanoOperacionalBloco`/`HistoricoPill`/o recorte do `AtivoCard` — planos seguintes que editarem esses componentes devem usar `SP[N]` desde o início (o guardião reprova px solto imediatamente).
- A decisão autônoma da caixa "Sem leitura do motor" (acima) precisa de confirmação do Alex no checkpoint 43-05 — não é um gap funcional, só um ponto fora da tabela original que precisou de julgamento no momento da implementação.

---
*Phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo*
*Completed: 2026-09-27*

## Self-Check: PASSED

- FOUND: web/tests/test_ritmo_sp.mjs
- FOUND: web/src/App.jsx
- FOUND: web/tests/test_sinal_chip_ui.mjs
- FOUND commit 8b49b6e (test RED)
- FOUND commit 259b23f (feat GREEN)
