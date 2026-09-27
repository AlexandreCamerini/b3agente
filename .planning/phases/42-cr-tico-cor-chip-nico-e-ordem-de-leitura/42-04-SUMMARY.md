---
phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura
plan: 04
subsystem: ui
tags: [react, ativo-card, ordem-de-leitura, sinal-chip, confluence-ring, guardiao]

# Dependency graph
requires: ["42-01", "42-02", "42-03"]
provides:
  - "AtivoCard (Watchlist e Radar, mesmo componente) religado na ordem: identidade+preço → resumo da posição → manchete (SinalChip primario com anel) → TimingBadge → plano por modo → linha de contexto → elegibilidade → cauda"
  - "Manchete do AtivoCard é <SinalChip peso=\"primario\" decision={decM}> com ring={anel} (confluência·tier·lado·setup) — decM continua vindo só do motor (decisaoDoModo)"
  - "Chips da IA (kp.direcao/conviccao/qualidade) removidos do AtivoCard e do vm da Watchlist (D-02)"
  - "MercadoScreen (Watchlist) sem kp/chip() legado no vm"
affects: ["42-05", "42-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Derivação de sinal 100% no corpo do AtivoCard (s0Card/anel/alinhamento/fundamentoCard), lendo só sc/decM/fscore — nenhum recálculo de dado do motor, tudo repassado via sinal.js (42-01/42-03)"
    - "envolverAnel(no, papel) como render-prop: o SetorAlvo que dá o alvo de toque de 44px só envolve o SVG do anel (papel==='anel'), o rótulo textual usa o mesmo setor sem o constraint de tamanho"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_hero_reconciliado.mjs
    - web/tests/test_setor_toque.mjs
    - web/tests/test_sinal_chip_ui.mjs

key-decisions:
  - "fundamentoCard prioriza sc.fundamento (overlay determinístico do scan, anexado por _enrich_fundamentos_sync em ambos /api/scan — Watchlist e Radar) e cai para {score: fscore} (fundamento da análise da IA) só na ausência — confirmado por leitura do backend (scanner.py:346, regime.py:284, main.py:2172) antes de implementar, não assumido"
  - "anVencida movido para DEPOIS da elegibilidade (fim da sequência, antes da cauda) — o plano pedia isso explicitamente (HIER-01/D-11: TimingBadge colado à manchete, sem bloco entre eles)"
  - "elegibilidade (HistoricoPill) só renderiza com sc.melhorSetup presente, igual à postura antiga — sinal secundário, nunca antes da confluência/anel"

requirements-completed: [HIER-01, HIER-02, CHIP-01, CHIP-02]

# Metrics
duration: ~70min
completed: 2026-09-27
---

# Phase 42 Plan 04: AtivoCard religado na ordem de leitura (HIER-01/HIER-02) Summary

**AtivoCard (Watchlist + Radar, mesmo componente) agora renderiza manchete-com-anel → timing → plano → contexto → elegibilidade nos dois contextos, sem nenhum dado da IA no card — `chip()`/`kp` saíram do corpo do componente e do vm da Watchlist.**

## Performance

- **Duration:** ~70 min
- **Started:** 2026-09-27
- **Completed:** 2026-09-27
- **Tasks:** 2/2 completos
- **Files modified:** 4

## Accomplishments

- Import de `sinal.js` ampliado com `rotuloAnel`, `ladoDoMotor`, `alinhamentoDoMotor`.
- `AtivoCard`: destructuring sem `kp`; `const chip = ...` legado removido; 5 variáveis derivadas logo após o destructuring (`modoCard`, `s0Card`, `anel`, `alinhamento`, `fundamentoCard`), todas guardadas por `sc ?`, sem recálculo de dado do motor.
- Espinha de opções (card recolhido): removido o `<span>` de `kp.direcao`/`kp.conviccao` (D-02); ticker/preço/stop/alvo/veredito ficam.
- Manchete: `decM ? (<div>...)` virou `<SinalChip peso="primario" decision={decM} kicker={...} sufixo={...} ring={anel} operador={operador} envolverAnel={...} />`; o ramo de ausência ("Sem leitura do motor...") ficou byte-idêntico. O anel é envolvido por `SetorAlvo setorId="analise"` com alvo de toque 44×44px só no SVG (`papel==="anel"`).
- Sequência pós-manchete, IDÊNTICA para Watchlist e Radar (é o mesmo componente): `<TimingBadge>` → `<PlanoOperacionalBloco>` → `<LinhaContexto>` → elegibilidade (`<HistoricoPill>` em `<div>` própria, só com `sc.melhorSetup`) → `{anVencida && (...)}` (movido para o fim, antes da cauda).
- Removida inteiramente a antiga linha de chips (`SetorAlvo setorId="analise"` com `chip("direção"...)`, `chip("confluência"...)`, `chip("fundamento"...)`, `sc.melhorSetup` solto, `HistoricoPill` na posição antiga).
- `MercadoScreen` (Watchlist): removidos `const kp = an.kpis || {};` e o `const chip = (label, value, col) => (...)` código morto; vm sem `kp`.
- Guardiões reconciliados com nota "REVERSÃO DELIBERADA (2026-09-26, Fase 42, ...)": `test_hero_reconciliado.mjs` (manchete via `SinalChip`, anel em vez de chip de confluência, fundamento em `LinhaContexto`, prova negativa de `kp.` no corpo de `AtivoCard`) e `test_setor_toque.mjs` (sublinhado no `ring.cabeca` + `setorId="analise"`/`envolverAnel=` + `label="FUNDAMENTO"`).
- `test_sinal_chip_ui.mjs` ganhou a Parte C: ordem estritamente crescente `{pos && (` < manchete < timing < plano < contexto < elegibilidade < `anVencida`, mais asserções de `alinhamentoDoMotor`/`ladoDoMotor`/`tierOf`, ausência de `kp.`/`DIR_STYLE` e alvo de toque 44px.

## Task Commits

1. **Task 1: AtivoCard na ordem de leitura (manchete+anel, timing, plano, contexto, elegibilidade) e fora da IA** — `ffc25ae` (feat)
2. **Task 2: vm da Watchlist sem IA + guardiões reconciliados (hero, setor_toque) e guardião de ordem** — `fde9dc5` (feat)

**Plan metadata:** (este commit, a seguir) — docs: complete plan

## Files Created/Modified

- `web/src/App.jsx` — import de `sinal.js` ampliado; `AtivoCard` religado (derivação de sinal + JSX na nova ordem); `MercadoScreen` sem `kp`/`chip()` legado
- `web/tests/test_hero_reconciliado.mjs` — reancorado para `SinalChip`/anel/`LinhaContexto`, nota de reversão deliberada
- `web/tests/test_setor_toque.mjs` — reancorado para `ring.cabeca`/`envolverAnel`/`LinhaContexto`, nota de reversão deliberada
- `web/tests/test_sinal_chip_ui.mjs` — Parte C (ordem e fiação do `AtivoCard`)

## Validação

```
node web/tests/test_sinal_chip_ui.mjs              → TUDO OK (42 asserções, incl. Parte C nova)
node web/tests/test_decisao_modo.mjs               → todos os testes passaram
node web/tests/test_timing_ui.mjs                  → todos os testes passaram
node web/tests/test_conceito_ui.mjs                → todos os testes passaram
node web/tests/test_hero_reconciliado.mjs          → todos os testes passaram
node web/tests/test_setor_toque.mjs                → todos os testes passaram
web/tests/*.mjs (suíte completa, ~168 arquivos)     → 1 falha conhecida: test_ios_assets.mjs (ambiental)
cd web && npx vite build --logLevel error          → exit 0, build limpo
```

Acceptance criteria (greps literais do plano) confirmados:
- `grep -c '<SinalChip peso="primario" decision={decM}' web/src/App.jsx` → 1
- corpo de `AtivoCard` sem `kp.`/`const chip =` → 0 ocorrências
- corpo de `AtivoCard` com `envolverAnel=` → 1 ocorrência
- `MercadoScreen` sem `const kp =`/`const chip =` → 0 ocorrências
- nota "REVERSÃO DELIBERADA (2026-09-26, Fase 42" presente nos dois guardiões (`test_hero_reconciliado.mjs`, `test_setor_toque.mjs`)

`test_ios_assets.mjs` falha pelo mesmo motivo documentado em 42-01/42-02/42-03-SUMMARY.md: `npx vite build` regenera `web/dist` com hashes novos que não batem com o bundle nativo local (`web/ios/`, gitignored, não resincronizado via `cap sync`). Artefato de ambiente, nenhum arquivo iOS de produção tocado.

Suíte pytest do backend não foi executada — este plano é front-only (`files_modified` do frontmatter e o diff real cobrem só `web/src/App.jsx` e `web/tests/*.mjs`); motor intocado (nenhum arquivo `server/app/*.py` tocado, confirmado por `git diff --stat -- server/app` vazio).

## Deviations from Plan

Nenhuma. O `<action>` de cada task foi seguido literalmente: nomes de variáveis derivadas (`modoCard`, `s0Card`, `anel`, `alinhamento`, `fundamentoCard`), assinatura exata do `SinalChip`/`envolverAnel`, ordem exigida pelos guardiões novos/reconciliados. A verificação de que `sc.fundamento` chega no payload de `/api/scan` (tanto Watchlist quanto Radar, via `_enrich_fundamentos_sync` em `server/app/main.py:2172`) e que `sc.regime`/`sc.gatilhoAlinhado` vêm de `regime.ranquear()` (chamado dentro de `scanner.run_scan`, `scanner.py:358`) foi feita por leitura do backend antes de implementar — confirma a premissa do CONTEXT/interfaces do plano ("na Watchlist esses campos já chegam em `sc`"), sem exigir mudança de plumbing.

## Decisões autônomas

Execução autorizada pelo Alex sem pausa para confirmação (autonomia concedida no prompt de execução). Decisões tomadas sem consulta:

1. **`decBg` continua destructurado no `vm` do `AtivoCard` mesmo sem uso direto no corpo do componente após a migração da manchete para `SinalChip`** (que resolve cor internamente via `REC_STYLE[decision]`). Não removi porque (a) `decBg` continua sendo produzido e usado por quem monta o `vm` (`MercadoScreen`/Radar) para outros fins potenciais e (b) o `<action>` da Task 1 não pedia a remoção da variável do destructuring, só do `chip()` e do `kp`. Risco: nenhum — variável não usada não quebra build (`npx vite build` limpo) nem os guardiões. Fica como nota para o 42-05/06, que já vai tocar o `vm` do Radar.
2. **`radarVm.sc`/`radarVm.kp: {}` (Radar, `App.jsx` ~7073) não foram tocados** — o plano é explícito que o Radar "ainda passa `sc` enxuto e mantém seus próprios chips/plano/anel nos children" até o 42-05 (ação item 7 da Task 1). Confirmei que o card do Radar hoje pode mostrar fundamento/elegibilidade duplicados nesse intervalo (a `sc` do Radar tem `spark/confluencia/melhorSetup/setupHistorico/setupElegivel`, mas não `regime/gatilhoAlinhado/plano/setups/close`, então `s0Card`/`alinhamento`/parte da cláusula de lado do anel ficam `null` lá até o 42-05 religar o `radarVm`), exatamente como o plano previu — nada publicado antes do 42-06, então não é regressão visível em produção.
3. **Rodei a suíte completa `web/tests/*.mjs` (não só os arquivos exigidos pela `<verify>` de cada task)** — mesma prática dos executores anteriores desta fase (42-01/42-02/42-03), para confirmar ausência de regressão. Achei só a falha ambiental já conhecida.
4. **Escolhi `<div style={{ marginTop: "8px" }}>` para envolver o `HistoricoPill` na nova posição** (elegibilidade em linha própria) — o `<action>` do plano já especificava esse espaçamento (`marginTop: "8px"`) literalmente; segui à risca, sem inventar valor.

## User Setup Required

None — nenhuma configuração externa necessária.

## Next Phase Readiness

- `AtivoCard` está religado nos dois contextos (Watchlist já usa `sc` completo do payload; Radar ainda com `sc` enxuto — o 42-05 religa o `radarVm`/`RadarScreen` para completar a paridade e remover os children duplicados do Radar).
- `SinalChip`, `LinhaContexto`, `PlanoOperacionalBloco` (definidos no 42-03) agora têm call site real e travado por guardião — nenhum componente ficou "definido mas não fiado".
- Nenhum bloqueio. Nota de ambiente (repetida de 42-01/02/03): se o próximo executor rodar `npx vite build`, considerar `cd web && npx cap sync ios` antes da suíte completa para não repetir a falha local de `test_ios_assets.mjs`.

---
*Phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura*
*Completed: 2026-09-27*

## Self-Check: PASSED

- `web/src/App.jsx` — FOUND (modificado, existe)
- `web/tests/test_hero_reconciliado.mjs` — FOUND (modificado, existe)
- `web/tests/test_setor_toque.mjs` — FOUND (modificado, existe)
- `web/tests/test_sinal_chip_ui.mjs` — FOUND (modificado, existe)
- Commit `ffc25ae` — FOUND em `git log --oneline --all`
- Commit `fde9dc5` — FOUND em `git log --oneline --all`
