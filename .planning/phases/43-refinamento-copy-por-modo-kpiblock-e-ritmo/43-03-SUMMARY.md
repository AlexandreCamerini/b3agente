---
phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
plan: 03
subsystem: ui
tags: [chip-03, kpiblock, analysisview, guardiao, fold-in]

# Dependency graph
requires:
  - phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
    plan: 01
    provides: "copy.js: sinal.leituraIa (rótulo, campos, aria) nos dois modos"
  - phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
    plan: 02
    provides: "const SP em web/src/App.jsx (escala 4/8pt)"
provides:
  - "AnalysisView({ an, operador }) com a linha 'Leitura da IA' (3 SinalChip peso=contexto neutros)"
  - "KpiBlock/KpiCell/DIR_STYLE/SCALE_STYLE/REC_PRO_MAP/recDoModo apagados de App.jsx"
  - "FundamentoTabela sem 'FUNDAMENTO' duplicado (D-17)"
  - "web/tests/test_leitura_ia_chips.mjs — guardião novo (CHIP-03/D-17)"
affects: [43-04, 43-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bloco condicional {an.kpis && (...)} na mesma posição estrutural dos outros blocos de AnalysisView (an.iaIndisponivel, d.fatos, an.fundamento) — nenhum wrapper novo de componente"
    - "Seta de direção como elemento aria-hidden SEPARADO do SinalChip (nunca dentro de value) — leitor de tela só ouve o ariaLabel completo"

key-files:
  created:
    - web/tests/test_leitura_ia_chips.mjs
  modified:
    - web/src/App.jsx
    - web/src/sinal.js
    - web/tests/test_decisao_modo.mjs
    - web/tests/test_sinal_chip_ui.mjs

key-decisions:
  - "Nenhuma - plano seguido como especificado (JSX de referência do 43-UI-SPEC.md usado verbatim, adaptado para copy.js/SP)"

patterns-established:
  - "Guardião de reconciliação datada aplicado a duas asserções mortas de test_decisao_modo.mjs (nunca apagadas, reescritas para testar a ausência/D-05)"

requirements-completed: [CHIP-03]

# Metrics
duration: ~35min
completed: 2026-09-27
---

# Phase 43 Plan 03: KpiBlock apagado, Leitura da IA em AnalysisView (CHIP-03) Summary

**KpiBlock/KpiCell (código morto desde qa/49) e seus órfãos (DIR_STYLE/SCALE_STYLE/REC_PRO_MAP/recDoModo) saem de App.jsx; direção/convicção/qualidade da IA voltam como 3 SinalChip peso="contexto" neutros dentro da Leitura da IA em AnalysisView, nunca no card — mais o fold-in D-17 (FUNDAMENTO duplicado).**

## Performance

- **Duration:** ~35 min
- **Tasks:** 2 completadas (TDD RED→GREEN)
- **Files modified:** 4 (+ 1 criado)

## Accomplishments
- `web/tests/test_leitura_ia_chips.mjs` (novo, 22 asserções): trava ausência de `KpiBlock`/`KpiCell`/`DIR_STYLE`/`SCALE_STYLE`/`recDoModo`/`REC_PRO_MAP` em `App.jsx`; os 3 `SinalChip peso="contexto"` neutros dentro de `AnalysisView` (direção com seta ↗/↘ `aria-hidden`, convicção, qualidade), na posição estrutural correta (depois de `<Markdown`, antes de `Array.isArray(d.fatos)`); ausência de `estado=`/cor de mercado/`kpis.recomendacao` no bloco; `operador` no escopo de `AnalysisView`; remoção do `label="FUNDAMENTO"` duplicado em `FundamentoTabela` (D-17)
- `App.jsx`: `KpiBlock`, `KpiCell`, `DIR_STYLE`, `SCALE_STYLE`, `REC_PRO_MAP`, `recDoModo` apagados por inteiro; comentário datado no topo do bloco de constantes de apresentação explicando a remoção sem citar os nomes banidos (o guardião exige grep == 0)
- `AnalysisView({ an, operador })`: deriva `leituraIa` de `copyFor(operador ? "operador" : "estudo").sinal.leituraIa`; bloco `{an.kpis && (an.kpis.direcao || an.kpis.conviccao || an.kpis.qualidade) && (...)}` com `marginTop: SP[4]`, título `leituraIa.rotulo`, e os 3 chips com `leituraIa.campos.*`/`leituraIa.aria(...)`; `kpis.recomendacao` nunca vira chip (D-03); caminho determinístico (sem `an.kpis`) omite a linha inteira sem placeholder (D-04)
- Call site do `AtivoCard`: `<AnalysisView an={an} operador={operador} />`
- D-17: `FundamentoTabela` perde `label="FUNDAMENTO"` do `SinalChip` — fica só `value={f.score}`; cabeçalho `>FUNDAMENTO<` continua único
- `sinal.js`: comentário atualizado (referência a `recDoModo`/`REC_PRO_MAP:App.jsx:1272-1285` trocada por texto sem os identificadores apagados)
- `test_decisao_modo.mjs`: 2 asserções reconciliadas com nota "REVERSÃO DELIBERADA (2026-09-27, Fase 43, CHIP-03...)" — nunca apagadas, reescritas para testar a AUSÊNCIA de `recDoModo`/`REC_PRO_MAP` e de `kpis.recomendacao` como decisão exibida
- `test_sinal_chip_ui.mjs`: contagem de call sites de `<SinalChip peso="contexto"` sobe de 4 para 7 (3 novos em `AnalysisView`), com nota datada; asserção nova confirma exatamente 3 nesse componente

## Task Commits

Each task was committed atomically (TDD RED→GREEN):

1. **Task 1 RED:** `df8558d` — test(43-03): guardião de leitura da IA (RED) + reconciliação de KpiBlock/contagem de chips
2. **Task 2 GREEN:** `4e5c31c` — feat(43-03): Leitura da IA em AnalysisView, KpiBlock/órfãos apagados, D-17 (GREEN)

## Files Created/Modified
- `web/tests/test_leitura_ia_chips.mjs` (novo) — guardião comportamental CHIP-03/D-17
- `web/src/App.jsx` — remoção de `KpiBlock`/`KpiCell`/`DIR_STYLE`/`SCALE_STYLE`/`REC_PRO_MAP`/`recDoModo`; `AnalysisView` ganha `operador` + bloco Leitura da IA; `FundamentoTabela` sem label duplicado; call site atualizado
- `web/src/sinal.js` — comentário de referência atualizado
- `web/tests/test_decisao_modo.mjs` — 2 asserções reconciliadas (REVERSÃO DELIBERADA)
- `web/tests/test_sinal_chip_ui.mjs` — contagem de call sites 4→7 + asserção nova

## Decisões autônomas

Nenhuma fora do que o `43-03-PLAN.md` especificava. O JSX de referência do `43-UI-SPEC.md` (linhas 196-222) foi usado como base, adaptado apenas para consumir `copyFor(...).sinal.leituraIa` (em vez de strings literais "DIREÇÃO"/"CONVICÇÃO"/"QUALIDADE"/aria-label hardcoded) e `SP[N]` (em vez de `"16px"`/`"4px"`/`"8px"` literais) — ambos já disponíveis dos planos 43-01/43-02, exatamente como o plano previa em "Next Phase Readiness".

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

`npx cap copy ios` reportou `ERROR: failed to copy trust settings of system certificate-25291` repetidamente — mesmo ruído de keychain do sandbox já registrado no `43-02-SUMMARY.md`; não afeta a cópia dos assets web (`copy ios` terminou com sucesso, `test_ios_assets.mjs` confirma paridade de chunks). `for t in tests/*.mjs` inicialmente reportou 171 "falhas" por um erro de sandbox ao escrever em `/tmp` (`operation not permitted`) — não é falha de teste; refeito redirecionando para `$TMPDIR` (correto para este ambiente), resultado real: 0 falhas.

## Validação executada

- `node tests/test_leitura_ia_chips.mjs` — 22/22 ok
- `node tests/test_decisao_modo.mjs` — 10/10 ok
- `node tests/test_sinal_chip_ui.mjs` — 48/48 ok
- `node tests/test_hero_reconciliado.mjs` — 12/12 ok
- `node tests/test_ritmo_sp.mjs` — 20/20 ok
- Loop completo `for t in web/tests/*.mjs` — 0 falhas em todos os arquivos (`TOTAL_FALHAS=0`)
- `npx vite build` — build limpo (warning de chunk >500kB pré-existente, fora do escopo desta fase)
- `npx cap copy ios` — copiado com sucesso; `test_ios_assets.mjs` confirma paridade de chunks dist↔ios após a cópia
- `git diff --stat -- server/` — vazio (plano front-only confirmado)
- Backend pytest — não executado (plano front-only, confirmado pelo `sequential_execution` desta sessão)

## User Setup Required

None - nenhuma configuração externa necessária.

## Next Phase Readiness
- `AnalysisView` com `operador` em escopo e Leitura da IA pronta para o 43-04/43-05 (HIER-03: microtexto de reconciliação em `HistoricoPill`) fiarem sem depender de vocabulário novo
- Guardião `test_leitura_ia_chips.mjs` já fiscaliza qualquer regressão futura em `KpiBlock`/`DIR_STYLE`/`SCALE_STYLE`/`REC_PRO_MAP`/`recDoModo` e na posição/contrato dos 3 chips
- Radar "Aprofundar com IA" (`scan_deep`): confirmado por grep que `server/app/scan_deep.py` não devolve `kpis` — nenhuma linha nova aparece ali por ora (Claude's Discretion do 43-CONTEXT.md: não inventar); revisitar se o payload mudar em fase futura

---
*Phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo*
*Completed: 2026-09-27*

## Self-Check: PASSED

