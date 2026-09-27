---
phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura
plan: 01
subsystem: ui
tags: [react, copy, pure-functions, sinal, aria]

# Dependency graph
requires: []
provides:
  - "Bloco `sinal` idêntico em COPY.estudo/COPY.operador (marca de alinhamento, lado do anel, disclaimer de fundamento, aria-labels)"
  - "web/src/sinal.js: camada pura (ladoDoMotor, decisaoDirecional, alinhamentoDoMotor, regimeRotulo, rotuloAnel, ariaRegime, ariaFundamento, ariaManchete)"
  - "web/tests/test_sinal_helpers.mjs: guardião unitário cobrindo D-01/D-09/D-10/D-16 e o caso UGPA3"
affects: ["42-02", "42-03", "42-04", "42-05", "42-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Módulo puro sem JSX/DOM consumindo copyFor() de copy.js (mesmo padrão de finance.js), testável por entrada/saída"
    - "Campo ausente/fora do domínio -> null explícito, nunca inferido/recalculado no front (D-01/D-09/D-16)"

key-files:
  created:
    - web/src/sinal.js
    - web/tests/test_sinal_helpers.mjs
  modified:
    - web/src/copy.js

key-decisions:
  - "ladoDoMotor(null) precisa retornar null sem lançar — troquei destructuring com default param por leitura defensiva (motor || {}), já que o teste chama a função com null explícito e default param não cobre esse caso"

patterns-established:
  - "Funções puras de apresentação (sinal.js) separadas do componente que vai consumi-las (SinalChip, plano 42-02+) — aria-label e texto visível saem da MESMA função"

requirements-completed: [HIER-01, CHIP-02]

# Metrics
duration: ~35min
completed: 2026-09-27
---

# Phase 42 Plan 01: Camada pura de apresentação do sinal Summary

**`web/src/sinal.js` + bloco `sinal` em `copy.js`: funções puras que traduzem lado/alinhamento/tier do motor em texto e aria-label, sem tocar componente ou motor.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-09-27T03:55:00Z (aprox.)
- **Completed:** 2026-09-27T04:33:53Z
- **Tasks:** 2/2 completos
- **Files modified:** 3 (1 modificado, 2 criados)

## Accomplishments
- Bloco `sinal` adicionado idêntico em `COPY.estudo`/`COPY.operador` (paridade de chaves preservada, `test_copy_theme.mjs` verde)
- `web/src/sinal.js` criado: 8 funções puras exportadas, zero import de App.jsx/React, zero inferência de lado a partir do nome do setup
- Guardião `test_sinal_helpers.mjs` (RED → GREEN) cobrindo todos os casos de borda do plano, incluindo o cenário UGPA3 (VENDER + tendência de alta + gatilho desalinhado + confluência 100 → "padrão de venda" + "contra a tendência")
- Motor (`server/app/*`) intocado — confirmado por `git diff --stat -- server/app` vazio

## Task Commits

Each task was committed atomically:

1. **Task 1: bloco `sinal` em COPY.estudo e COPY.operador** - `2076079` (feat)
2. **Task 2: `web/src/sinal.js` (funções puras) + guardião unitário** - `451427d` (test, RED) → `c08b319` (feat, GREEN)

**Plan metadata:** (este commit) — docs: complete plan

_TDD: Task 2 seguiu RED (test_sinal_helpers.mjs importando módulo inexistente, confirmado como falha) → GREEN (sinal.js implementado, guardião verde)._

## Files Created/Modified
- `web/src/copy.js` - bloco `sinal` (alinhamento, anelLado, fundamentoNaoDirecao, degradadoSufixo/Aria, ariaRegime, ariaFundamento, ariaAnel, ariaManchete) idêntico nos dois modos
- `web/src/sinal.js` - camada pura: `ladoDoMotor`, `decisaoDirecional`, `DECISOES_DIRECIONAIS`, `alinhamentoDoMotor`, `regimeRotulo`, `REGIME_ROTULO`, `rotuloAnel`, `ariaRegime`, `ariaFundamento`, `ariaManchete`
- `web/tests/test_sinal_helpers.mjs` - guardião unitário (43 asserções, incluindo paridade estudo/operador e o caso UGPA3)

## Decisions Made
- `ladoDoMotor(null)` deveria devolver `null` sem lançar (caso do behavior spec). Default param `({ setup, plano } = {})` não cobre chamada explícita com `null` (JS só aplica o default em `undefined`). Troquei para `ladoDoMotor(motor) { const { setup, plano } = motor || {}; ... }` — mesma semântica pública, implementação mais defensiva. Decisão autônoma menor, sem impacto de escopo (Rule 1 — bug de runtime descoberto no próprio guardião do plano).

## Deviations from Plan

None além da decisão acima (Rule 1, já documentada). Nenhuma arquitetura nova, nenhum arquivo fora do `files_modified` declarado no frontmatter do plano.

## Issues Encountered

- Rodei `npx vite build` (exigido pela validação do CLAUDE.md para front editado) e isso regenerou `web/dist` com novos hashes de chunk. O guardião `web/tests/test_ios_assets.mjs` comparou esses hashes contra `web/ios/App/App/public` (bundle nativo local, não resincronizado via `cap sync`) e falhou. **Ambos `web/dist/` e `web/ios/` são gitignored** (`.gitignore:15` e `:19`) — são artefatos de build locais, não versionados; a falha é drift de ambiente de build local, não uma regressão introduzida por este plano (nenhum código de produção do iOS foi tocado; `sinal.js`/`copy.js` não afetam o bundle nativo). Rodar `cap sync` resolveria localmente, mas está fora do escopo deste plano (só toca copy/UI pura) — registrado aqui para o executor da próxima wave não se assustar se rodar `npx vite build` de novo sem `cap sync`.
- Todos os demais 165 testes de `web/tests/*.mjs` passaram (`node "$t"` individual, sem regressão).

## Decisões autônomas

Execução autorizada pelo Alex sem pausa para confirmação (autonomia concedida no prompt de execução). Decisões tomadas sem consulta:

1. **`ladoDoMotor(null)` via `motor || {}` em vez de default param** — comportamento exigido pelo `<behavior>` do plano (`(null) → null`), mas a implementação literal sugerida no `<action>` (`{ setup, plano } = {}`) lança `TypeError` para chamada explícita com `null`. Corrigido para não quebrar o contrato descrito. Risco: nenhum — mesma assinatura pública, mesmo comportamento para todos os outros casos testados.
2. **Não roteei o `deferred-items.md`** — nenhum item ficou fora de escopo nesta wave; não havia nada a deferir.
3. **Rodei a suíte completa `web/tests/*.mjs` (166 arquivos) além do exigido pela validação do plano** (que pedia só os dois testes tocados) para confirmar ausência de regressão antes de fechar o plano — achei a falha de `test_ios_assets.mjs`, que documentei em "Issues Encountered" como drift de build local (arquivos gitignored), não regressão de código. Não revertida nem corrigida (fora do escopo do plano — não pedia rodar `cap sync`), só registrada.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `web/src/sinal.js` e o bloco `sinal` de `copy.js` estão prontos para os planos 42-02+ (extração do componente `SinalChip`, reposicionamento do `ConfluenceRing`, reordenação do `AtivoCard`) consumirem — nenhuma mudança de contrato esperada, as funções já cobrem todos os casos de borda descritos no CONTEXT/UI-SPEC.
- Nenhum bloqueio. Nota de ambiente: se o próximo executor rodar `npx vite build`, considerar `cd web && npx cap sync ios` antes de rodar a suíte completa para não repetir a falha local de `test_ios_assets.mjs` (não é regra deste repo tocar isso automaticamente — é observação de ambiente).

---
*Phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura*
*Completed: 2026-09-27*

## Self-Check: PASSED

Todos os arquivos declarados (`web/src/sinal.js`, `web/tests/test_sinal_helpers.mjs`, `web/src/copy.js`, este SUMMARY) existem em disco; todos os 3 hashes de commit (`2076079`, `451427d`, `c08b319`) confirmados em `git log --oneline --all`.
