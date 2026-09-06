---
phase: 21-duplica-o-removida-e-portf-lio-consolidado
plan: 01
subsystem: ui
tags: [react, jsx, portfolio, dedup, design-system]

# Dependency graph
requires:
  - phase: 20-funda-o-estrutural-e-tipogr-fica
    provides: "constantes de módulo numBody/numMicro/card/kicker/MONO (Fase 20, escala numérica nomeada) sem consumidor real de produção fora do Topbar"
provides:
  - "CapitalCurve existe em exatamente uma tela do app (EvolucaoScreen/Acompanhar)"
  - "Portfólio com card consolidado 2x2 substituindo os 4 cards kpi() empilhados"
  - "numBody/numMicro ganham primeiro consumidor real de produção no card de Portfólio"
  - "Guardião estático web/tests/test_fase21_dedup_consolidacao.mjs travando DEDUP-01 e DEDUP-03, extensível pelos próximos planos da Fase 21 (DEDUP-02, FIX-03)"
affects: [21-02, 21-03, 21-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guardião estático por regex sobre App.jsx com isolamento de corpo de componente (indexOf('function Xxx(') até próximo '\\nfunction '), mesmo padrão de test_fase3_c19_card_status.mjs e test_fase20_fundacao_visual.mjs"

key-files:
  created:
    - web/tests/test_fase21_dedup_consolidacao.mjs
  modified:
    - web/src/App.jsx

key-decisions:
  - "Guardião único por fase (não por plano): comentário de cabeçalho instrui os próximos planos (DEDUP-02, FIX-03) a ESTENDER este mesmo arquivo em vez de criar um segundo guardião paralelo para a mesma tela"
  - "Ordem das 4 células do card consolidado preservada (Patrimônio total, Resultado aberto, Caixa disponível, Em posições) — grid 2x2 já corresponde à ordem de leitura esquerda-direita/cima-baixo, sem necessidade de reordenar"

patterns-established:
  - "numBody/numMicro consumidos via spread ({...numBody, fontFamily: MONO, color}) em vez de redefinição inline de fontSize/fontWeight"

requirements-completed: [DEDUP-01, DEDUP-03]

# Metrics
duration: 35min
completed: 2026-09-06
---

# Phase 21 Plan 01: Duplicação removida e Portfólio consolidado Summary

**Remove a segunda chamada de `<CapitalCurve>` do Portfólio (permanece só em Acompanhar) e substitui os 4 cards `kpi()` empilhados por um único card 2×2 consumindo `numBody`/`numMicro` da Fase 20.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-09-06T00:00:00Z (aprox.)
- **Completed:** 2026-09-06T00:35:00Z (aprox.)
- **Tasks:** 2 (Task 1 TDD RED, Task 2 GREEN)
- **Files modified:** 2 (1 criado, 1 editado)

## Accomplishments
- A curva de patrimônio (`<CapitalCurve>`) agora existe em exatamente uma tela (`EvolucaoScreen`/Acompanhar); a rota Portfólio não a repete mais.
- Os 4 cards de KPI do Portfólio (Patrimônio total, Resultado aberto, Caixa disponível, Em posições) viraram um único card denso em grid 2×2, no padrão visual de "RESUMO DO DIA".
- `numBody`/`numMicro` (Fase 20) ganharam seu primeiro consumidor de produção fora do Topbar.
- Guardião estático novo (`test_fase21_dedup_consolidacao.mjs`) trava as duas mudanças e está desenhado para ser estendido pelos próximos planos da Fase 21 (DEDUP-02, FIX-03) em vez de duplicado.

## Task Commits

Each task was committed atomically:

1. **Task 1: Guardião de DEDUP-01/DEDUP-03 escrito antes da mudança (RED)** - `da9eaef` (test)
2. **Task 2: Remover a CapitalCurve duplicada e consolidar os 4 cards em 1 (GREEN)** - `a44aaa2` (feat)

**Plan metadata:** (este commit, criado a seguir)

## TDD Gate Compliance

Task 1 (`tdd="true"`) seguiu o ciclo RED/GREEN corretamente:
- RED: `da9eaef` — guardião criado, rodado contra `App.jsx` não editado, 11/17 asserções falharam pelas razões esperadas (contagem de `<CapitalCurve`, `kpi(`, `...numBody`, `...numMicro`, grid 2×2, literais de valor, remoção do grid antigo); as 3 asserções sobre "o que não muda" passaram (sobrevivente dentro de `EvolucaoScreen`; `CarteiraScreen` sem `CapitalCurve`) — confirmado que o guardião tem dentes, não é no-op.
- GREEN: `a44aaa2` — após as duas edições em `App.jsx`, todas as 17 asserções passam.

## Files Created/Modified
- `web/tests/test_fase21_dedup_consolidacao.mjs` - guardião estático novo (17 asserções) travando DEDUP-01 (CapitalCurve única) e DEDUP-03 (card consolidado 2×2), com cabeçalho instruindo extensão futura em vez de duplicação
- `web/src/App.jsx` - remove `<CapitalCurve ctx={ctx} />` da rota Portfólio (linha ~9027); remove o helper `kpi()` e as 4 chamadas (linhas ~4340-4362); substitui pelo card consolidado em grid 2×2 reusando `card`/`kicker`/`numBody`/`numMicro`/`MONO` via spread

## Decisions Made
- Nenhuma decisão nova de produto necessária — todas as decisões (qual instância de `CapitalCurve` sai, formato do card consolidado, ordem das células) já vinham fechadas em `21-CONTEXT.md` e `21-UI-SPEC.md` (Structural Contract), com o JSX alvo literal. A execução seguiu o texto do `21-UI-SPEC.md` byte a byte.

## Deviations from Plan

None - plan executado exatamente como escrito. As duas edições em `App.jsx` seguiram literalmente o JSX alvo do `21-UI-SPEC.md` (Structural Contract, DEDUP-01 e DEDUP-03).

## Issues Encountered

- **Setup do ambiente (não é deviation de código):** o worktree não tinha `web/node_modules` instalado (`npx vite build` falhava com `ERR_MODULE_NOT_FOUND` para `vite`/`@vitejs/plugin-react`/`vite-plugin-pwa`). Rodei `npm install` dentro de `web/` para restaurar as dependências já declaradas em `package.json`/`package-lock.json` — isto NÃO adicionou nem alterou nenhuma dependência (`git diff --stat web/package.json web/package-lock.json` vazio antes e depois), apenas materializou `node_modules` a partir do lockfile existente. Não se enquadra na exclusão de Rule 3 (instalar pacote referenciado no plano) porque nenhum pacote novo foi introduzido.
- Comandos que escrevem fora do worktree (npm cache, `git status --porcelain` redirecionado por `scripts/executar.sh` para `/*.log` na raiz do filesystem) dispararam `EPERM`/"Operation not permitted" do sandbox padrão da ferramenta Bash; refeitos com `dangerouslyDisableSandbox: true` conforme a política do ambiente (evidência clara de restrição de sandbox, não bug de código).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Portfólio e Acompanhar verificados via suíte canônica (`bash scripts/executar.sh --testes`: 2021 passed, 1 skipped no pytest + todos os `web/tests/*.mjs` OK, incluindo o guardião novo) e `npx vite build` verde. Nenhuma dependência nova, nenhum push feito.
- **Verificação visual ao vivo NÃO realizada** — este ambiente de subagente não tem ferramentas de browser/computer-use vinculadas (limitação conhecida, confirmada nas 4 fases do Phase 20). O orquestrador/Alex deve abrir a rota Portfólio (dev local ou build publicado) e confirmar visualmente: (a) nenhuma curva de patrimônio duplicada aparece ao navegar Acompanhar → Portfólio na mesma sessão; (b) o card consolidado 2×2 renderiza as 4 células sem quebra de layout em viewport estreito (375px, guardrail herdado da Fase 20 FIX-01).
- O guardião `test_fase21_dedup_consolidacao.mjs` está pronto para ser ESTENDIDO (não duplicado) pelos planos seguintes da Fase 21: DEDUP-02 (card de status do Operador IA) e FIX-03 (placeholder "poucos dias" da própria `CapitalCurve`), conforme o comentário de cabeçalho do arquivo.
- Nenhum bump/publicação de front foi feito neste plano (fora de escopo da Task 2, que só pede build local verde) — publicar o front da Fase 21 fica para quando a fase inteira (ou o milestone v1.5) fechar, seguindo o guardrail do repositório sobre `scripts/bump.sh` antes de `publicar-web.sh`.

---
*Phase: 21-duplica-o-removida-e-portf-lio-consolidado*
*Completed: 2026-09-06*

## Self-Check: PASSED

- FOUND: web/tests/test_fase21_dedup_consolidacao.mjs
- FOUND: .planning/phases/21-duplica-o-removida-e-portf-lio-consolidado/21-01-SUMMARY.md
- FOUND commit: da9eaef (test)
- FOUND commit: a44aaa2 (feat)
