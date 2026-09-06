---
phase: 22-componentes-compartilhados-trilho-cones-mascote
plan: 03
subsystem: ui
tags: [react, jsx, svg, palette, guardian-test]

# Dependency graph
requires:
  - phase: 22-componentes-compartilhados-trilho-cones-mascote
    provides: "Plano 22-02 (NavIcon generalizado, size/color, fallback active?T.accent:T.textMuted preservado) e o guardião único da Fase 22 (test_fase22_componentes_compartilhados.mjs) que este plano estende com as Seções C e D"
provides:
  - "SYS-02 fechado no código: zero emoji pictográfico do sistema operacional em App.jsx (varredura Unicode inteira dá zero)"
  - "📡 do Radar reusando a geometria `radar` já existente no NavIcon — nenhuma segunda antena desenhada"
  - "TierDot (SVG) + tierOf devolvendo id de tier (índice [0]); TIER_FILL com 4 literais hex, semanticamente separados de T.positive/T.negative/T.warn"
  - "Destructure morto [tierDot, tierLabel] removido da Watchlist"
  - "SYS-03 IMPLEMENTADO (não fechado): PALETTE.dark.shadowFab/PALETTE.light.shadowFab consumidos por T.shadowFab no PetFab; tema escuro idêntico a hoje, tema claro com valor de PARTIDA pendente de conferência visual"
  - "Seções C e D do guardião da Fase 22 (test_fase22_componentes_compartilhados.mjs), cobrindo Radar + varredura final de emoji e a sombra do PetFab por tema"
affects: [22-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tier vira SVG decorativo (aria-hidden) com paleta literal PRÓPRIA (TIER_FILL), deliberadamente fora de T.* — a única introdução de cor nova da fase, documentada e travada por guardião (asserção C8)"
    - "rgba literal por tema, mesma convenção de `scrim` (App.jsx:80/108): nova chave `shadowFab` em PALETTE.dark/light, publicada automaticamente como T.shadowFab pelo mecanismo VARKEY/T existente — zero plumbing novo"
    - "Reuso de geometria de ícone entre concept e call site: 📡 do Radar consome o id `radar` já existente no NavIcon, em vez de desenhar uma segunda antena"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_fase22_componentes_compartilhados.mjs

key-decisions:
  - "Cores literais do TierDot (#22c55e/#f59e0b/#9ca3af/#ef4444) fora de T.* — decisão do planner (22-UI-SPEC.md Decisão 2), replicada em comentário no código para o próximo agente não 'consertar' isso para T.positive/T.negative"
  - "shadowFab do tema claro (rgba(15,20,28,0.22)) é valor de PARTIDA aprovado (22-UI-SPEC.md Decisão 3), não calibração final — a conferência visual ao vivo nos dois temas fica para a Task 2 do plano 22-04"
  - "Guardião próprio (C12) exigia regex mais preciso que o texto do plano sugeria — corrigido dentro da mesma task, ver Deviations"

patterns-established:
  - "Regex de guardião que precisa distinguir 'texto cru' de 'valor de atributo JSX' deve ancorar no `>` que precede um children literal — sem essa âncora, o padrão bate também no uso correto em `prop={...}`"

requirements-completed: [SYS-02, SYS-03]

# Metrics
duration: ~11min (commit-a-commit, 00:34:54 → 00:45:16 -03:00)
completed: 2026-09-06
---

# Phase 22 Plan 03: Radar SVG + sombra do PetFab por tema (SYS-02/SYS-03) Summary

**Últimos três sites de emoji do Radar (ícone de varredura, ponto de tier, destructure morto) trocados por SVG/id de tier, fechando a varredura Unicode de SYS-02 em zero; sombra do PetFab sai de `rgba` fixo e vira `T.shadowFab` por tema — implementado com o tema escuro idêntico a hoje e o claro como valor de partida, calibragem visual PENDENTE para o plano 22-04.**

## Performance

- **Duration:** ~11 min commit-a-commit (00:34:54 → 00:45:16, -03:00)
- **Started:** 2026-09-06T00:34:54-03:00
- **Completed:** 2026-09-06T00:45:16-03:00
- **Tasks:** 3 completed
- **Files modified:** 2 (`web/src/App.jsx`, `web/tests/test_fase22_componentes_compartilhados.mjs`)

## Accomplishments

- Guardião da Fase 22 ganhou as Seções C (Radar + varredura Unicode final) e D (sombra do PetFab por tema), escritas e confirmadas RED antes de qualquer edição em `App.jsx` (25 asserções falhando, saída literal registrada abaixo).
- 📡 do Radar (Site A) virou `<NavIcon id="radar" size={13} color="currentColor" />`, reusando a geometria já existente — nenhuma segunda antena desenhada; os dois braços irmãos `↻` do mesmo ternário ficaram intactos.
- `tierOf` (Site B) devolve id de tier em minúsculas no índice [0] (`"forte"/"moderada"/"neutra"/"fraca"`), preservando os 4 limiares e os 4 rótulos do índice [1] intocados — `test_radar_leitura_rapida.mjs` continua verde. Novo `TierDot`/`TIER_FILL` com 4 cores literais aprovadas, deliberadamente fora de `T.positive`/`T.negative`/`T.warn` (comentário no código documenta o porquê).
- Destructure morto `const [tierDot, tierLabel] = tierOf(...)` (Site C) removido da Watchlist — confirmado por grep antes da deleção que ambos os nomes eram mortos; `const anVencida =` (linha vizinha, protegida por outro guardião) ficou intocada.
- Varredura Unicode pictográfica (`[\u{1F300}-\u{1FAFF}]`) e `⚪` sobre `App.jsx` dão zero — SYS-02 fechado no código.
- `PALETTE.dark.shadowFab`/`PALETTE.light.shadowFab` adicionados seguindo a convenção literal de `scrim`; `PetFab` consome `T.shadowFab` via template literal no lugar do `rgba(0,0,0,0.45)` hardcoded. Tema escuro idêntico ao valor de hoje; tema claro com valor de PARTIDA aprovado.
- Suíte canônica completa verde nas duas suítes: pytest `2021 passed, 1 skipped`; `web/tests/*.mjs` com as quatro seções do guardião da Fase 22 verdes e nenhuma outra falha. `npx vite build` conclui com código 0.

## Task Commits

Executado como plano `tdd="true"` na Task 1 (RED) e Tasks 2/3 (GREEN, um requirement por task):

1. **Task 1: Guardião da Fase 22, Seções C e D, escritas antes da mudança (RED)** - `fe0c402` (test)
2. **Task 2: Radar — ícone de varredura, ponto de tier e o destructure morto (GREEN, SYS-02)** - `fdf3e54` (feat)
3. **Task 3: Sombra do PetFab por tema — token shadowFab (GREEN, SYS-03)** - `b3a2dc1` (feat)

**Plan metadata:** commit desta entrega (SUMMARY.md) segue nesta mesma sessão.

## Saída literal do RED (Task 1, antes de editar App.jsx)

```
FALHOU varredura Unicode pictográfica em App.jsx dá zero (encontrados: ["🟢","🟡","🔴","📡"])
FALHOU `⚪` não aparece mais em App.jsx
FALHOU recorte de RadarScreen contém `<NavIcon id="radar"`
FALHOU existe `function TierDot`
FALHOU `TierDot` contém `<circle`
FALHOU `TierDot` contém `fill`
FALHOU `TierDot` contém `aria-hidden`
FALHOU existe `const TIER_FILL`
FALHOU recorte de TIER_FILL contém #22c55e
FALHOU recorte de TIER_FILL contém #f59e0b
FALHOU recorte de TIER_FILL contém #9ca3af
FALHOU recorte de TIER_FILL contém #ef4444
FALHOU `tierOf` devolve o id `"forte"`
FALHOU `tierOf` devolve o id `"moderada"`
FALHOU `tierOf` devolve o id `"neutra"`
FALHOU `tierOf` devolve o id `"fraca"`
FALHOU `<TierDot tier=` aparece na renderização do Radar
FALHOU o índice [0] de `tierOf` não é mais renderizado como texto cru
FALHOU `tierDot` (destructure morto da Watchlist) saiu de App.jsx
FALHOU `PALETTE.dark` contém `shadowFab:`
FALHOU `PALETTE.light` contém `shadowFab:`
FALHOU `shadowFab` do tema escuro é exatamente "rgba(0,0,0,0.45)" (o tema escuro não muda de aparência)
FALHOU `shadowFab` do tema claro é DIFERENTE do valor do tema escuro
FALHOU `PetFab` usa `T.shadowFab` dentro de um `drop-shadow(`
FALHOU `PetFab` não contém mais `rgba(0,0,0,0.45)` inline

25 asserção(ões) falharam.
```

Todas as 25 falhas correspondem exatamente às asserções que a Task 1 previu como RED (itens 1, 2, 6, 7, 9, 12, 13, 14, 17, 18 do plano). As asserções que deveriam permanecer verdes (3, 4, 10, 11, 19, 20) passaram nesta mesma execução.

## Files Created/Modified

- `web/src/App.jsx` - 📡 do Radar reusa `<NavIcon id="radar">`; `tierOf` devolve id de tier (índice [0]); `TierDot`/`TIER_FILL` novos; destructure morto removido; `PALETTE.dark/light.shadowFab` adicionados; `PetFab` consome `T.shadowFab`
- `web/tests/test_fase22_componentes_compartilhados.mjs` - Seções C (13 grupos de asserção — varredura final, Radar, TierDot/TIER_FILL, compatibilidade com `test_radar_leitura_rapida.mjs`, código morto) e D (7 grupos — `shadowFab` nos dois temas, compatibilidade com `test_pet_ui.mjs`) acrescentadas

## Decisions Made

Ver `key-decisions` no frontmatter. Nenhuma decisão de produto foi tomada fora do que já estava travado em `22-UI-SPEC.md`/`22-CONTEXT.md` (cores literais do tier, valor de partida do `shadowFab` claro). A única decisão tomada durante a execução foi técnica/de guardião — ver Deviations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Regex da asserção C12 do próprio guardião (escrito na Task 1) batia também no uso correto que a Task 2 introduziria**

- **Found during:** Task 2, ao rodar o guardião depois da edição do `App.jsx`.
- **Issue:** O texto do plano (`22-03-PLAN.md`, item 12 da Task 1) especifica literalmente o regex `!/\{tierOf\([^)]*\)\[0\]\}/.test(app)` para garantir que o índice `[0]` de `tierOf` não seja mais renderizado como texto cru. Mas a implementação correta que o próprio plano prescreve na Task 2 (`<TierDot tier={tierOf(r.confluencia)[0]} />`) contém literalmente a substring `{tierOf(r.confluencia)[0]}` dentro do valor do atributo `tier=` — o regex sem âncora de contexto barra tanto o padrão antigo (texto cru, o que se queria proibir) quanto o padrão novo correto (valor de atributo JSX, o que a própria task pede para existir). Rodar o guardião após a Task 2 confirmou a falha: `FALHOU o índice [0] de tierOf não é mais renderizado como texto cru`, mesmo com o código certo.
- **Fix:** Regex ajustado para `!/>\{tierOf\([^)]*\)\[0\]\}/.test(app)` — a âncora `>` isola especificamente o caso de "filho de JSX diretamente após o fechamento de uma tag" (o padrão antigo, `<div style={...}>{tierOf(...)[0]} ...`), sem colidir com `tier={tierOf(...)[0]}` (precedido por `tier=`, não por `>`). A intenção original do guardião (proibir a renderização como texto cru em qualquer lugar) foi preservada — só o mecanismo de detecção ficou mais preciso.
- **Files modified:** `web/tests/test_fase22_componentes_compartilhados.mjs`
- **Verification:** Reexecução do guardião confirma a asserção C12 verde com o código da Task 2, e continuaria vermelha se alguém reintroduzisse `{tierOf(...)[0]}` como filho direto de uma tag (testado mentalmente contra o código antigo, que tinha exatamente `>{tierOf(r.confluencia)[0]} {tierOf(r.confluencia)[1]}...`).
- **Committed in:** `fdf3e54` (Task 2 commit — a versão com falso positivo nunca foi commitada isoladamente, o fix entrou junto com a implementação de Site B).

---

**Total deviations:** 1 auto-fixed (1 bug, Rule 1) — descoberto e corrigido ainda dentro da Task 2, antes do commit, seguindo o mesmo padrão do plano 22-02 (bugs de guardião auto-escrito encontrados ao rodar contra a implementação real).
**Impact on plan:** Nenhum no comportamento de produto entregue — o desvio foi só na precisão do regex do próprio guardião desta fase. A intenção documentada no `22-03-PLAN.md` (índice [0] nunca mais como texto cru) foi mantida e verificada empiricamente (RED→GREEN).

## Issues Encountered

- `npx vite build` isolado falhou primeiro com `EPERM`/cache root-owned do npm (mesmo padrão dos planos 22-01/22-02), depois com `ERR_MODULE_NOT_FOUND` por `web/node_modules` ausente no worktree — resolvido rodando a suíte canônica completa (`bash scripts/executar.sh --testes`, sandbox desabilitado só para este comando), que detecta e resolve `node_modules` sozinha. Depois disso, `npx vite build` isolado também passou a funcionar (código 0, warning de chunk grande pré-existente e fora de escopo).
- Nenhum outro guardião quebrou fora da Seção D reservada à Task 3 — confirmado que `test_radar_leitura_rapida.mjs`, `test_radar.mjs`, `test_pet_ui.mjs`, `test_watchlist_anvencida_guard.mjs` e `test_fase4_radar_deepmodal.mjs` seguem verdes durante e depois de todas as três tasks, como a varredura do plano previu (nenhum guardião quebrado, só adições).

## SYS-03 — Status explícito: IMPLEMENTADO, calibragem visual PENDENTE

**SYS-03 não está fechado.** O código está completo (`PALETTE.dark.shadowFab`/`PALETTE.light.shadowFab` existem, `PetFab` consome `T.shadowFab`, o tema escuro é byte a byte igual ao valor de hoje), mas o valor do tema claro é um **ponto de partida aprovado**, não uma calibração final:

- **Arquivo:** `web/src/App.jsx`
- **Linha:** 108 (`shadowFab: "rgba(15,20,28,0.22)"`, dentro de `PALETTE.light`)
- **Valor a conferir:** `0.22` de opacidade — precisa de uma checagem visual ao vivo nos DOIS temas (dark e light), confirmando que o halo separa a silhueta da coruja do card atrás sem virar um "disco"/badge chapado ao redor da arte (o PNG já tem transparência e contorno próprios).
- **Onde a conferência acontece:** Task 2 do plano `22-04` (per decisão do planner, `22-UI-SPEC.md` Decisão 3 / `22-03-PLAN.md` `<decisao_do_planner_shadowfab>`).
- **Ambiente deste executor não tem browser/computer-use MCP** — a verificação visual ao vivo não pôde ser feita nesta sessão; ela permanece explicitamente como pendência, não como "feito".

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- SYS-02 está satisfeito no código E travado por guardião: `App.jsx` tem zero emoji pictográfico do sistema operacional (varredura Unicode completa), o 📡 do Radar reusa a geometria `radar` já existente, o tier tem paleta própria e justificada, e o destructure morto saiu.
- `test_fase22_componentes_compartilhados.mjs` tem as quatro seções (A/B/C/D) completas e verdes — o guardião único da Fase 22 está fechado, nenhuma seção reservada para planos futuros.
- SYS-03 está implementado no código, mas explicitamente **não fechado**: a calibragem visual do `shadowFab` claro (linha 108) fica para o plano `22-04`, que já nasce sabendo o arquivo/linha/valor exatos a verificar.
- Nenhum `git push` para `origin` foi executado nesta sessão (execução em worktree isolado); publicação do front fica para quando a Fase 22 inteira fechar, seguindo a regra já registrada em `PROJECT.md` ("Fase sem plano de publicação front").
- Suíte canônica (`bash scripts/executar.sh --testes`) verde nas duas suítes ao final da Task 3: pytest `2021 passed, 1 skipped`; todos os `web/tests/*.mjs` OK.

---
*Phase: 22-componentes-compartilhados-trilho-cones-mascote*
*Completed: 2026-09-06*
