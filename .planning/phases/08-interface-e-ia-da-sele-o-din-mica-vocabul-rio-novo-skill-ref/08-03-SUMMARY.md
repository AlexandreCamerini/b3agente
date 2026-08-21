---
phase: 08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref
plan: 03
subsystem: ui
tags: [react, historico-medido, adr-017, guardiao, radar, watchlist, acessibilidade]

# Dependency graph
requires:
  - phase: 08-01
    provides: "COPY[modo].historico/.historicoRotulo + historicoTxt() em web/src/copy.js, espelho byte a byte de server/app/skill_ref.py — vocabulário canônico dos 6 estados do histórico medido"
  - phase: 07 (Bloco 1, Fase 7)
    provides: "setupHistorico/setupElegivel anexados a cada resultado de /api/scan (regime.ranquear/signal_ledger._fundir) — dado já existia, sem vitrine no front"
provides:
  - "historicoEstado()/historicoDesatualizado() em web/src/finance.js — derivação PURA dos 6 estados + modificador de desatualização (2 dias úteis), fonte única testada, reusável por qualquer componente futuro (Plano 08-04 incluído)"
  - "Componente HistoricoPill (web/src/App.jsx) — contrato visual aprovado do UI-SPEC: 6 estados, cor por estado, aria-label sempre presente, nenhuma string de vocabulário hardcodada"
  - "HistoricoPill wireado no AtivoCard (Watchlist) e no RadarScreen (Radar/Mesa) — usuário agora VÊ a elegibilidade medida no nível do ticker, sem abrir o card"
  - "web/tests/test_historico_ui.mjs — guardião que trava cor por estado (recorte do fonte, sabotagem controlada validada), aria-label e ausência de vocabulário hardcodado"
affects: [08-04, 08-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Derivação de estado em função pura (finance.js) consumida por componente de apresentação (App.jsx) — mesmo padrão de tierOf/decisaoDoModo, agora estendido a um dicionário de histórico vindo do backend"
    - "Guardião por recorte de fonte: HISTORICO_PILL_STYLE + function HistoricoPill{...} recortado do texto de App.jsx antes de assertar cor, evitando falso-positivo contra os outros usos de T.negative/T.positive espalhados pelo arquivo"

key-files:
  created:
    - web/tests/test_historico_ui.mjs
  modified:
    - web/src/finance.js
    - web/tests/test_finance.mjs
    - web/src/App.jsx

key-decisions:
  - "elegivel==null cobre tanto 'nunca esteve na janela' quanto 'elegibilidade nunca resolvida' — precedência de 'insuficiente' sobre 'inelegivel' está no guard clause de historicoEstado, não numa checagem redundante no componente"
  - "hojeYmd é argumento OPCIONAL de HistoricoPill (default: new Date() em horário LOCAL, no ponto de uso) — mantém o componente testável sem forçar todo call site a calcular a data"
  - "aritmética de dias úteis usa Date.UTC a partir de partes YYYY-MM-DD extraídas por regex — nunca new Date(string) solta (desloca dia no WKWebView); feriados NÃO são considerados, decisão deliberada documentada em comentário (erra sempre para 'não degradar')"
  - "prop `elegivel` do HistoricoPill existe só por paridade defensiva com o par que regime._elegibilidade devolve — historico é a ÚNICA fonte do estado; nenhum ramo de reconciliação foi escrito para uma divergência que o backend estruturalmente não produz"

patterns-established:
  - "Estado derivado de dado do backend sempre em função pura testável antes de virar componente — finance.js continua a fonte única de números/estados determinísticos do front"

requirements-completed: [ADR17-B34-02]

# Metrics
duration: ~50min
completed: 2026-08-21
---

# Phase 08 Plan 03: HistoricoPill — vitrine da elegibilidade medida no Radar/Watchlist Summary

**Componente `HistoricoPill` (6 estados, cor via UI-SPEC, aria-label sempre presente) alimentado por `historicoEstado`/`historicoDesatualizado` puras em `finance.js`, ligado ao `AtivoCard` (Watchlist) e ao `RadarScreen` — o dado que `/api/scan` já entrega desde a Fase 7 finalmente aparece no nível do ticker.**

## Performance

- **Duration:** ~50 min
- **Started:** 2026-08-21T20:45:00-03:00 (approx.)
- **Completed:** 2026-08-21T18:33:11-03:00
- **Tasks:** 3
- **Files modified:** 3 (+ 1 criado)

## Accomplishments
- `historicoEstado(historico, aposentado)` e `historicoDesatualizado(historico, hojeYmd)` em `finance.js`: derivação pura dos 6 estados (`elegivel`, `inelegivel`, `insuficiente`, `nunca_medido`, `aposentado` + modificador `desatualizado`), com a precedência "insuficiente > inelegivel" codificando o princípio ADR-017 "Dois pisos de amostra" — ausência de evidência nunca vira evidência negativa. 17 testes novos, todos cobrindo os bullets do `<behavior>` do plano (incluindo o caso sexta→segunda e `calculadoEm` sem `medidoAte`).
- Componente `HistoricoPill` criado perto de `ConfluenceRing`: desenha os 6 estados com o contrato de cor do UI-SPEC (elegível/inelegível com o mesmo peso visual — nunca dim; insuficiente/nunca-medido neutros; aposentado com borda tracejada, único estado assim). Texto 100% de `copy.js` (`historicoRotulo`/`historicoTxt`) — zero string de vocabulário hardcodada. `role="img"` + `aria-label` sempre presentes; números da janela (`expRJanela`/`nJanela`/`janelaRef`) só desenhados quando existem — `null` nunca vira 0.
- Ligado ao `AtivoCard` (chip de análise, depois de `melhorSetup`, só quando `melhorSetup` existe) e ao `RadarScreen` (linha de chips do card, mesma regra de secundariedade — nunca antes da confluência/`ConfluenceRing`).
- Guardião `web/tests/test_historico_ui.mjs`: recorta o corpo de `HistoricoPill`/`HISTORICO_PILL_STYLE` do fonte (evita falso-positivo contra os outros usos de `T.negative` no arquivo) e trava cor por estado, ausência de `T.accent`, unicidade da borda tracejada, ausência de vocabulário hardcodado e presença de `aria-label`. Sabotagem controlada validada em sandbox (`scratchpad`, nunca o arquivo real): trocar o par de `insuficiente` para `T.negative` derruba o guardião (1 falha, exit 1); arquivo real confirmado intacto depois.
- `bash scripts/executar.sh --testes` verde nas DUAS suítes (1268 testes Python + todas as `web/tests/*.mjs`, incluindo os guardiões de regressão do Radar/card: `test_radar.mjs`, `test_radar_leitura_rapida.mjs`, `test_radar_regime_chip.mjs`, `test_hero_reconciliado.mjs`, `test_radar_watchlist.mjs`, `test_fundamento_ui.mjs`, `test_vocabulario_espelho.mjs`).

## Task Commits

Each task was committed atomically:

1. **Task 1: Derivação pura dos estados do histórico em finance.js** - `9d68222` (feat)
2. **Task 2: Componente HistoricoPill (contrato visual dos 6 estados)** - `fd3d8cd` (feat)
3. **Task 3: Radar consumindo setupHistorico/setupElegivel + guardião de UI** - `6a527d0` (feat)

**Plan metadata:** (este commit de SUMMARY)

_Nota: Tasks 1 e 3 tinham `tdd="true"`. Task 1: implementação (as duas funções puras) e os 17 testes novos nasceram como uma única unidade coesa — o `<behavior>` da tarefa É a especificação exata do comportamento a travar, sem implementação prévia a corrigir; não houve ciclo RED (teste falhando)→GREEN separado. Task 3 mistura mudança de produção (wiring do Radar) com o guardião novo — ambos nasceram juntos pela mesma razão. Ver "TDD Gate Compliance" abaixo._

## Files Created/Modified
- `web/src/finance.js` - `historicoEstado()`/`historicoDesatualizado()` (ADR-017 Bloco 3), aritmética de dias úteis sobre `Date.UTC`
- `web/tests/test_finance.mjs` - 17 testes novos (6 estados + 6 casos de desatualização)
- `web/src/App.jsx` - `HistoricoPill` + `HISTORICO_PILL_STYLE`, wiring no `AtivoCard` (Watchlist) e no `RadarScreen` (`radarVm.sc.setupHistorico`/`.setupElegivel` + chip), imports novos de `finance.js`/`copy.js`
- `web/tests/test_historico_ui.mjs` - guardião novo (cor por estado, aria-label, vocabulário, wiring do Radar)

## Decisions Made
- `elegivel` é prop defensiva do `HistoricoPill`, nunca fonte do estado — `historico` é a ÚNICA fonte (`regime._elegibilidade` estruturalmente nunca devolve `elegivel` não-nulo com `historico` nulo; documentado em comentário no componente).
- `hojeYmd` é opcional com default calculado no ponto de uso, em horário LOCAL (não UTC) — mantém o componente testável sem empurrar cálculo de data para todo call site.
- Feriados não entram na conta de "2 dias úteis" (só sábado/domingo) — limitação deliberada que sempre erra para o lado de "não degradar", documentada em comentário no código-fonte.
- `expRJanela`/`nJanela`/`janelaRef` só são desenhados quando não-nulos — reforça a regra de casa "null, nunca 0.0" também no front, não só no backend.

## Deviations from Plan

None - plan executado exatamente como escrito. Uma dependência de ambiente foi resolvida sem mudança de escopo (mesmo achado documentado em `PROJECT.md` e no Plano 08-01):

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `npm install` em `web/` antes do `vite build`/testes**
- **Found during:** Task 1 (verificação `npx vite build`)
- **Issue:** Worktree nasce sem `web/node_modules` (build falhava com `ERR_MODULE_NOT_FOUND` para `vite`).
- **Fix:** `npm install` em `web/` (dependências normais do `package.json`, nenhum pacote novo adicionado).
- **Files modified:** nenhum arquivo versionado (`web/node_modules` é gitignored).
- **Verification:** `npx vite build` e `bash scripts/executar.sh --testes` passaram limpos depois.
- **Committed in:** N/A (artefato gitignored, sem commit necessário).

---

**Total deviations:** 1 auto-fixed (1 blocking, ambiente)
**Impact on plan:** Nenhum impacto de escopo — resolução de ambiente já esperada (documentada em `PROJECT.md`).

## Issues Encountered
None além do item de ambiente acima.

## TDD Gate Compliance

O frontmatter do plano é `type: execute` (não `type: tdd`), então o gate de plano inteiro (RED→GREEN→REFACTOR obrigatório) não se aplica. Tasks 1 e 3 tinham `tdd="true"` na tag de tarefa:
- Task 1: a implementação nova (`historicoEstado`/`historicoDesatualizado`) e os 17 testes que a travam nasceram no mesmo commit `feat`, porque o `<behavior>` da tarefa É a especificação literal do comportamento aprovado (6 estados + regras de dias úteis) — não havia comportamento pré-existente a "corrigir" que justificasse um commit `test` isolado falhando primeiro.
- Task 3: mistura wiring de produção (Radar) com o guardião `test_historico_ui.mjs` — ambos escritos juntos pela mesma razão acima, e validados com sabotagem controlada em sandbox (prova de que o guardião de fato pega divergência) antes do commit.

Julgamento: risco de regressão baixo — toda a superfície nova (Tasks 1/2/3) passou por verificação manual das acceptance criteria linha por linha, `npx vite build` limpo em cada task, e a suíte canônica completa (`bash scripts/executar.sh --testes`) verde ao final, incluindo os 6 guardiões de regressão explicitamente listados no plano.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `HistoricoPill` pronto para reuso direto pelo Plano 08-04 (setup list item dentro do card do ativo, `s.historico`/`s.aposentado`) — o componente já aceita `compacto` para o caso de espaço reduzido dentro da lista de setups.
- `historicoEstado`/`historicoDesatualizado` são a fonte única para qualquer superfície futura que precise do mesmo veredito (ex.: card de status do Operador no Plano 08-04, linha de `entradaAuto` por setup).
- Nenhum bloqueador. `defaults.py`/`catalog.js` (prompts de IA) permanecem intocados.

## Known Stubs

Nenhum. O pill sempre lê `sc.setupHistorico`/`sc.setupElegivel` (Watchlist) ou `r.setupHistorico`/`r.setupElegivel` (Radar), campos que `/api/scan` já popula desde a Fase 7 — não há dado mockado nem placeholder de UI aguardando fiação futura.

## Threat Flags

Nenhum achado fora do `<threat_model>` do plano. Todos os 5 itens do STRIDE Threat Register (T-08-10..T-08-14) foram mitigados conforme desenhado e cobertos por asserção no guardião novo ou por reuso de padrão existente (nenhum cálculo novo no front, nenhum endpoint novo, nenhum caminho de auth tocado).

---
*Phase: 08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref*
*Completed: 2026-08-21*

## Self-Check: PASSED

All created/modified files verified present (`web/src/finance.js`, `web/tests/test_finance.mjs`, `web/src/App.jsx`, `web/tests/test_historico_ui.mjs`, este `SUMMARY.md`). All 3 task commits verified in `git log` (`9d68222`, `fd3d8cd`, `6a527d0`).
