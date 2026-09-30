---
phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura
plan: 02
subsystem: ui
tags: [react, color-tokens, wcag, confluence-ring, historico-pill]

# Dependency graph
requires: []
provides:
  - "PALETTE.dark/light.warnTint10 (token novo, sem hex solto fora de PALETTE)"
  - "HISTORICO_PILL_STYLE.inelegivel/elegivel fora do canal positive/negative (COR-01/D-03/D-04)"
  - "ConfluenceRing.col via TIER_FILL[tierOf(c)[0]] (COR-01/D-05)"
  - "web/tests/test_cor_confiabilidade.mjs: guardião com contraste AA calculado nas 4 combinações tema×modo"
affects: ["42-03", "42-04", "42-05", "42-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guardião grep-estático + contraste WCAG calculado a partir do texto de App.jsx (mesma fórmula de test_brand_book_v2_tokens.mjs), sem build/JSDOM"

key-files:
  created:
    - web/tests/test_cor_confiabilidade.mjs
  modified:
    - web/src/App.jsx
    - web/tests/test_historico_ui.mjs

key-decisions:
  - "Borda 1px solid T.borderSubtle no estado elegivel (não estava no <action> literal do plano, mas está no contrato do UI-SPEC §Estados de elegibilidade — implementado por completude de contrato, sem prop de cor livre)"

requirements-completed: [COR-01]

# Metrics
duration: ~40min
completed: 2026-09-27
---

# Phase 42 Plan 02: Crítico — cor do chip único de confiabilidade Summary

**Inelegível vira âmbar (T.warn/T.warnTint10) fora do canal de VENDER/prejuízo; elegível vira neutro com ✓; arco do ConfluenceRing usa TIER_FILL em vez de positive/accent — verde ao lado de VENDER deixa de existir.**

## Performance

- **Duration:** ~40 min
- **Started:** 2026-09-27 (após leitura de contexto)
- **Completed:** 2026-09-27
- **Tasks:** 2/2 completos
- **Files modified:** 3 (2 modificados, 1 criado)

## Accomplishments

- `warnTint10` declarado em `PALETTE.dark` (`rgba(251,191,36,0.10)`) e `PALETTE.light` (`rgba(161,98,7,0.04)`) — sem override em `MODE_OPERADOR`, conforme UI-SPEC (as 4 combinações passam com o mesmo alpha por tema).
- `HISTORICO_PILL_STYLE.inelegivel` → `[T.warn, T.warnTint10]`; `elegivel` → `[T.textPrimary, "transparent"]` + glifo `✓ ` decorativo (`aria-hidden`) no ramo elegível — texto acessível continua vindo de `historicoTxt`/`ariaLabel`, nunca do glifo.
- `ConfluenceRing.col` trocado de `c>=75 ? P.positive : c>=50 ? P.accent : P.textFaint` para `TIER_FILL[tierOf(c)[0]] || TIER_FILL.neutra` — arco fora do canal de direção de mercado.
- Guardião novo `test_cor_confiabilidade.mjs`: calcula contraste WCAG (luminância relativa, blend rgba sobre bgCard) nas 4 combinações tema×modo — resultado bate exatamente com o UI-SPEC: 7,98:1 / 8,64:1 / 4,68:1 / 4,68:1, todas ≥ AA 4,5:1.
- Guardião `test_historico_ui.mjs` reconciliado com nota "REVERSÃO DELIBERADA (2026-09-26, Fase 42, COR-01/D-03/D-04)" e novas asserções: ban list do objeto `HISTORICO_PILL_STYLE` (sem `T.positive`/`T.negative`, ROADMAP SC#1) e presença do glifo `✓` com `aria-hidden`.

## Task Commits

Each task was committed atomically:

1. **Task 1: token `warnTint10` + `HISTORICO_PILL_STYLE` (D-03/D-04) + guardião de histórico reconciliado** - `22d9e74` (feat)
2. **Task 2: arco do `ConfluenceRing` em `TIER_FILL` (D-05) + guardião COR-01 com contraste calculado** - `7868f95` (feat)

## Files Created/Modified

- `web/src/App.jsx` — `warnTint10` (2 temas), `HISTORICO_PILL_STYLE` revisado, `HistoricoPill` (borda elegível + glifo ✓), `ConfluenceRing.col` via `TIER_FILL`
- `web/tests/test_historico_ui.mjs` — §3 reescrito (novo contrato de cor + ban list + glifo), nota de reversão deliberada
- `web/tests/test_cor_confiabilidade.mjs` — guardião novo (criado)

## Validação

```
node web/tests/test_historico_ui.mjs              → TUDO OK (37 asserções)
node web/tests/test_historico_setup_card_ui.mjs   → todos os testes passaram
node web/tests/test_brand_book_v2_tokens.mjs       → todas as verificações passaram
node web/tests/test_mode_operador_light_palette.mjs → todos os testes passaram
node web/tests/test_cor_confiabilidade.mjs         → TUDO OK (28 asserções, 4 razões de contraste ≥4,5)
node web/tests/test_fase22_componentes_compartilhados.mjs → 0 FALHOU
cd web && npx vite build --logLevel error         → exit 0, build limpo
web/tests/*.mjs (suíte completa, 167 arquivos)     → 1 falha: test_ios_assets.mjs
```

`test_ios_assets.mjs` falha por drift de build local: `npx vite build` regenera `web/dist` com hashes novos que não batem com `web/ios/App/App/public` (bundle nativo local não resincronizado via `cap sync`). Ambos `web/dist/` e `web/ios/` são gitignored — artefato de ambiente, não regressão de código desta plan (mesmo achado documentado no 42-01-SUMMARY.md; nenhum arquivo iOS de produção foi tocado por este plano). Não corrigido (fora do escopo — corrigir exigiria `cap sync`, que não é regra deste repo rodar automaticamente).

Suíte pytest do backend não foi executada — este plano não toca nenhum arquivo `server/app/*.py` (confirmado: `files_modified` do frontmatter e o diff real cobrem só `web/src/App.jsx` e `web/tests/*.mjs`); motor intocado.

## Deviations from Plan

None. Diff confirmado (`git diff HEAD~2 -- web/src/App.jsx`) toca exatamente os 4 pontos previstos: as duas linhas `warnTint10` em `PALETTE`, a linha `col` do `ConfluenceRing`, o objeto `HISTORICO_PILL_STYLE` e a borda/glifo do `HistoricoPill`. Nenhum outro consumidor de `T.positive`/`T.negative` foi afetado.

## Decisões autônomas

Execução autorizada pelo Alex sem pausa para confirmação (autonomia concedida no prompt de execução). Decisões tomadas sem consulta:

1. **Borda `1px solid T.borderSubtle` no estado `elegivel`** — o `<action>` do plano (Task 1, item 5) já pedia essa borda explicitamente ("adicionar `if (estado === "elegivel") pillStyle.border = ...`"), e o UI-SPEC (§"Estados de elegibilidade") confirma o mesmo contrato. Sem risco — segue literalmente o plano e o contrato de design, registrado aqui só por completude da seção.
2. **Formato do fallback de `warnTint10` no guardião novo** (`test_cor_confiabilidade.mjs`, linha do loop de combos): escrevi `cores.warnTint10 || estudo[tema].warnTint10` para cobrir o caso hipotético de `MODE_OPERADOR` declarar um override futuro — hoje é sempre o valor do tema base (nenhum override existe), então o fallback nunca dispara na prática. Decisão de robustez do teste, não de comportamento do produto; documentado no próprio cabeçalho do arquivo de teste ("o teste não assume ausência, mede") conforme pedido pelo `<action>` da Task 2, item 2c.
3. **Não rodei `cap sync` nem toquei `web/dist`/`web/ios`** ao confirmar a falha conhecida de `test_ios_assets.mjs` — decisão consistente com o 42-01-SUMMARY.md (mesmo achado, mesma justificativa: artefato gitignored, fora do escopo de um plano que só toca cor/token).
4. **Rodei a suíte completa `web/tests/*.mjs` (167 arquivos)** além dos 2 arquivos exigidos pela `<verify>` explícita de cada task, para confirmar ausência de regressão antes de fechar o plano — mesma prática do executor anterior (42-01). Achei só a falha já conhecida de `test_ios_assets.mjs`.

## User Setup Required

None — nenhuma configuração externa necessária.

## Next Phase Readiness

- `warnTint10`, `HISTORICO_PILL_STYLE` revisado e `ConfluenceRing` recolorido estão prontos para os planos 42-03+ (extração do componente `SinalChip`, reposicionamento do anel dentro da manchete, reordenação do `AtivoCard`) consumirem sem retrabalho de cor.
- `TIER_FILL`/`tierOf` permanecem intocados (confirmado pelo próprio guardião novo) — nenhum plano futuro precisa reconciliar esse contrato.
- Nenhum bloqueio. Nota de ambiente (repetida do 42-01): se o próximo executor rodar `npx vite build`, considerar `cd web && npx cap sync ios` antes de rodar a suíte completa para não repetir a falha local de `test_ios_assets.mjs`.

---
*Phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura*
*Completed: 2026-09-27*

## Self-Check: PASSED

- `web/src/App.jsx` — FOUND (modificado, existe)
- `web/tests/test_historico_ui.mjs` — FOUND (modificado, existe)
- `web/tests/test_cor_confiabilidade.mjs` — FOUND (criado, existe)
- Commit `22d9e74` — FOUND em `git log --oneline --all`
- Commit `7868f95` — FOUND em `git log --oneline --all`
