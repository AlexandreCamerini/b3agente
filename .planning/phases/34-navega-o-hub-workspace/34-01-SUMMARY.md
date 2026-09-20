---
phase: 34-navega-o-hub-workspace
plan: 01
subsystem: ui
tags: [react, jsx, opcoes, copy-dictionary, guardian-test]

# Dependency graph
requires:
  - phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios
    provides: "SecaoVigias.jsx/SecaoSetups.jsx (5 componentes Secao*.jsx job-to-be-done) e o padrão VARKEY/TOKENS/T de espelho declarado que este plano segue"
provides:
  - "WorkspaceHeader.jsx — componente props-only (ticker/onVoltar/cp) que o 34-02 vai importar e chamar dentro do branch `ticker ? Workspace : Hub` de OpcoesScreen.jsx"
  - "4 chaves de copy novas (opcoesVoltarAoHub, opcoesAbaAnalisar, opcoesAbaComparar, opcoesAbaSetupsSalvos) em COPY.estudo e COPY.operador"
  - "web/tests/test_opcoes_hub_workspace_ui.mjs — guardião novo da fase 34, parte 1 (header + paridade de copy); 34-02/34-03 ACRESCENTAM asserções a este mesmo arquivo"
affects: ["34-02", "34-03"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Componente de seção props-only com espelho declarado VARKEY/TOKENS/T local (zero import de App.jsx) — mesmo padrão de SecaoVigias.jsx, aplicado a WorkspaceHeader.jsx"
    - "Guardião de guarda dupla: acceptance_criteria do PLAN.md roda grep sobre o arquivo BRUTO (com comentário); o guardião .mjs usa `semComentario` antes de grepar os mesmos termos, porque o doc-comment do componente cita literalmente os termos proibidos (useState, .manchete, T.accent) ao explicar por que não os usa"

key-files:
  created:
    - web/src/opcoes/WorkspaceHeader.jsx
    - web/tests/test_opcoes_hub_workspace_ui.mjs
  modified:
    - web/src/copy.js

key-decisions:
  - "opcoesAbaSetupsSalvos diverge de tom entre modos por decisão do PATTERNS.md/UI-SPEC: 'Setups salvos' no Estudo (nome completo do artefato migrado, D-01 amendment), 'Setups' no Operador (tom terso, mesmo padrão de opcoesSubabaOperar 'Operação'×'Operar')"
  - "Botão de voltar usa `(cp && cp.opcoesVoltarAoHub) || \"Voltar\"` em vez de desestruturar `cp` num alias local — a acceptance_criteria do plano exige o literal `cp.opcoesVoltarAoHub` no código-fonte, não um alias `c.opcoesVoltarAoHub`"
  - "Comentários de WorkspaceHeader.jsx evitam citar literalmente 'T.accent'/'useState' — a acceptance_criteria da Task 2 faz grep sobre o arquivo COM comentários (diferente do guardião .mjs, que usa semComentario), então uma explicação textual desses termos no doc-comment quebraria a própria checagem"

requirements-completed: [NAV-03]

# Metrics
duration: 28min
completed: 2026-09-20
---

# Phase 34 Plan 01: Fundação do split hub/workspace Summary

**Header fixo do workspace (`WorkspaceHeader.jsx`, D-05/NAV-03) + 4 chaves de copy novas nos dois modos + guardião novo, sem tocar `OpcoesScreen.jsx`**

## Performance

- **Duration:** 28 min
- **Started:** 2026-09-20T18:30:52-03:00
- **Completed:** 2026-09-20T18:58:42-03:00
- **Tasks:** 3
- **Files modified:** 3 (1 modificado, 2 novos)

## Accomplishments
- `WorkspaceHeader.jsx` criado: props-only (`ticker`/`onVoltar`/`cp`), zero hook, zero import de `App.jsx`, reusa o box exato do `cabecalho` e o estilo `BOTAO` de `OpcoesScreen.jsx` (padding/radius/44px verbatim), sem `T.accent` (navegação, não ação primária) e sem `.manchete`.
- 4 chaves de copy (`opcoesVoltarAoHub`, `opcoesAbaAnalisar`, `opcoesAbaComparar`, `opcoesAbaSetupsSalvos`) inseridas em `COPY.estudo` E `COPY.operador`, na mesma vizinhança de `opcoesSubabaOperar` — só adições, nenhuma chave existente renomeada/reordenada.
- Guardião novo (`test_opcoes_hub_workspace_ui.mjs`) com 12 asserções e prova negativa por injeção registrada abaixo; suíte canônica inteira (pytest + `.mjs`) rodada e confirmada na baseline exata da Fase 33.

## Task Commits

Each task was committed atomically:

1. **Task 1: 4 chaves de copy novas, nos DOIS modos** - `7af698d` (feat)
2. **Task 2: WorkspaceHeader.jsx — header fixo do workspace (D-05)** - `d0a7815` (feat)
3. **Task 3: guardião novo (parte 1) + suíte canônica verde** - `e943735` (test)

**Plan metadata:** commit deste SUMMARY.md (a seguir)

## Files Created/Modified
- `web/src/copy.js` - +21 linhas (4 chaves × 2 modos + comentários), 0 remoções
- `web/src/opcoes/WorkspaceHeader.jsx` - novo componente props-only (43 linhas)
- `web/tests/test_opcoes_hub_workspace_ui.mjs` - novo guardião (112 linhas)

## Decisions Made
- Ver `key-decisions` no frontmatter — nenhuma decisão de arquitetura nova; todas são detalhes de implementação dentro do escopo já fechado pelo `34-CONTEXT.md`/`34-UI-SPEC.md`/`34-PATTERNS.md`.

## Deviations from Plan

None — plano executado exatamente como escrito. As únicas escolhas feitas foram as documentadas em `key-decisions` acima, todas resolvendo ambiguidade menor de forma explícita já autorizada pelo próprio plano (interfaces/acceptance_criteria), não desvio de escopo.

## Issues Encountered

**Prova negativa por injeção (exigida pela Task 3 acceptance_criteria):** injetei temporariamente `const [x, setX] = useState("")` em `WorkspaceHeader.jsx`, rodei `node web/tests/test_opcoes_hub_workspace_ui.mjs` e confirmei reprovação (`FALHOU WorkspaceHeader.jsx não usa useState/useEffect/useMemo/useRef`, saída 1, 1 falha). Revertido com `git checkout -- web/src/opcoes/WorkspaceHeader.jsx` (arquivo já estava commitado no Task 2, então o checkout restaurou o estado exato do commit `d0a7815`). Reexecutei o guardião após reverter: 12/12 ok, saída 0.

Nenhum outro problema — sandbox local bloqueia certificados TLS (achado pré-existente, ver memória `worktree-test-setup.md`); toda suíte de teste e `npx vite build` rodaram com o bypass de sandbox, confirmado necessário e sem outro efeito colateral.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `WorkspaceHeader.jsx` está pronto para ser importado por `OpcoesScreen.jsx` no plano 34-02, com o contrato de props já fixado na seção `<interfaces>` do `34-01-PLAN.md` (`WorkspaceHeader({ ticker, onVoltar, cp })`, `onVoltar` = `() => escolherTicker(ticker)`).
- As 4 chaves de copy já existem nos dois modos — 34-02/34-03 podem referenciá-las livremente sem risco de quebrar a checagem de paridade.
- `test_opcoes_hub_workspace_ui.mjs` existe e está verde; 34-02/34-03 devem ACRESCENTAR asserções a este mesmo arquivo (split hub/workspace em si), não criar um terceiro guardião.
- Suíte canônica confirmada na baseline exata esperada: 2923 pytest passed / 0 failed / 5 skipped / 3 xfailed; 152/153 `.mjs` (única falha: `test_ios_assets.mjs`, ambiental, `web/ios/` gitignored). `npx vite build` verde.
- `OpcoesScreen.jsx` permanece intocado, exatamente como o plano pretendia (verificado por `git diff --stat` mostrando só os 3 arquivos esperados).

---
*Phase: 34-navega-o-hub-workspace*
*Completed: 2026-09-20*

## Self-Check: PASSED

- FOUND: web/src/opcoes/WorkspaceHeader.jsx
- FOUND: web/tests/test_opcoes_hub_workspace_ui.mjs
- FOUND: .planning/phases/34-navega-o-hub-workspace/34-01-SUMMARY.md
- FOUND commit: 7af698d
- FOUND commit: d0a7815
- FOUND commit: e943735
