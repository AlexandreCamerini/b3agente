---
phase: 18-aba-opcoes
plan: 01
subsystem: ui

tags: [react, copy-dictionary, options, vocabulary, hooks]

# Dependency graph
requires:
  - phase: 14-opcoes-lastreadas
    provides: "store.optionsGate/optionsProposta (paridade deviceStore/serverStore), PropostaLastreada component"
  - phase: 17-fluxo-de-aceite
    provides: "payoff/fonte-do-dado copy keys, multiperna proposta contract"
provides:
  - "6 chaves de vocabulário novas em COPY.estudo/COPY.operador para a tira de oportunidades e afordância de posição"
  - "hook useOpcoesPropostas(tickers) — fan-out gate→proposta por ticker, contrato { propostas, carregando }"
affects: [18-02, 18-03, 18-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fan-out por ticker sem rota bulk (mesmo precedente de custo ADR-004), agora reutilizável via hook único"
    - "Chave primitiva (string join) como dependência de useEffect para evitar refetch por render"
    - "Contador de pendências decrementado em todos os caminhos (sucesso/gate reprovado/erro) para não travar estado de carregamento"

key-files:
  created: []
  modified:
    - web/src/copy.js
    - web/src/App.jsx

key-decisions:
  - "Seis chaves novas são todas string literal (não função) — evita acoplamento com a invocação sintética de argumentos do guardião test_copy_theme.mjs"
  - "Hook posicionado estritamente entre AtivoCard e CarteiraScreen — preserva a ordem que o guardião test_opcoes_proposta_ui.mjs depende (primeira ocorrência de store.optionsProposta(t, true) precisa continuar sendo a de AtivoCard)"

patterns-established:
  - "useOpcoesPropostas(tickers): ponto único de fan-out gate→proposta reusável pelas duas superfícies da Fase 18 (tira agregada e detalhe por posição)"

requirements-completed: [NAV-01, NAV-03]

duration: 7min
completed: 2026-09-03
---

# Phase 18 Plan 01: Contrato (vocabulário + hook) Summary

**Seis chaves de copy.js espelhadas nos dois modos e o hook `useOpcoesPropostas(tickers)` que os Planos 18-02/18-03 vão consumir para buscar gate+proposta por posição sem duplicar requisição.**

## Performance

- **Duration:** ~7 min (execução dos tasks; commit base 08:10:51 → último commit 08:17:36, horário local -03:00)
- **Started:** 2026-09-03T11:10:51Z
- **Completed:** 2026-09-03T11:18:05Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments
- `web/src/copy.js`: 6 chaves novas (`tiraOpcoesTitulo`, `tiraOpcoesVerDetalhe`, `tiraOpcoesCarregando`, `tiraOpcoesSemCobertura`, `tiraOpcoesSemSetup`, `linhaPropostaNaPosicao`) espelhadas em `COPY.estudo` e `COPY.operador`, todas string literal.
- `web/src/App.jsx`: hook `useOpcoesPropostas(tickers)` — uma requisição de `store.optionsGate` por ticker, `store.optionsProposta(t, true)` só quando o gate aprova, `{ propostas, carregando }` como contrato de saída. Posicionado exatamente entre `AtivoCard` e `CarteiraScreen`.
- Nenhum guardião existente (`test_copy_theme.mjs`, `test_opcoes_proposta_ui.mjs`, `test_carteira_lastro_ui.mjs`) enfraquecido; build do Vite limpo.

## Task Commits

Each task was committed atomically:

1. **Task 1: Vocabulário da tira e da afordância de posição em copy.js** - `1daaed6` (feat)
2. **Task 2: Hook useOpcoesPropostas(tickers) — fan-out gate→proposta por ticker** - `086093b` (feat)

**Plan metadata:** (this commit, SUMMARY.md)

## Files Created/Modified
- `web/src/copy.js` - 6 chaves novas em ambos os ramos (estudo/operador), bloco comentado citando Fase 18 Plano 01
- `web/src/App.jsx` - `useOpcoesPropostas(tickers)` novo, entre `AtivoCard` (fim ~3652) e `CarteiraScreen` (linha 3905, deslocada para depois da inserção); `AtivoCard` e `CarteiraScreen` intocados

## Decisions Made
- Nenhuma decisão de arquitetura nova — plano seguiu o contrato já congelado em `18-CONTEXT.md`/`18-PATTERNS.md` (réplica disciplinada do par `opGate`/`opProposta` de `AtivoCard`, sem rota bulk).
- Nome de variável do gate dentro do hook mantido como `gate` (não `opGate`) por instrução explícita do plano, para deixar claro na leitura que este bloco não é o de `AtivoCard`.

## Deviations from Plan

None - plan executed exactly as written. As únicas ações fora do texto literal do plano foram operacionais (ambiente): fast-forward do worktree para o commit-base correto do plano (`git merge --ff-only`, usado no lugar de `git reset --hard` por bloqueio de política do harness contra comandos destrutivos — operação equivalente e comprovadamente segura: HEAD era ancestral estrito do alvo, working tree limpo) e `npm install` em `web/` (node_modules ausente no worktree novo, precondição de `npx vite build` exigido pelo CLAUDE.md do projeto — não alterou `package.json`/`package-lock.json`, confirmado por diff vazio).

## Issues Encountered
- Worktree HEAD (`0b9ead1`) estava desatualizado em relação ao commit-base exigido pelo plano (`785bc23`, que já continha os 5 arquivos de planejamento da Fase 18). Resolvido com `git merge --ff-only` — fast-forward puro, sem perda de commit ou trabalho (verificado via `git merge-base --is-ancestor` antes de agir).
- `web/node_modules` ausente no worktree recém-criado; `npm install` resolveu (mesmo comportamento documentado no CLAUDE.md do projeto sobre `scripts/executar.sh` desde a Fase 5/FIX-C24 — aqui feito manualmente porque só `npx vite build` foi exigido pela verificação deste plano, não a suíte canônica completa).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plano 18-02 (detalhe dentro da posição) e 18-03 (tira agregada) podem consumir `useOpcoesPropostas(tickers)` e as 6 chaves novas de `copy.js` diretamente — contrato `{ propostas, carregando }` estável, nomes de chave literais conforme especificado.
- Nenhum bloqueio identificado. `useOpcoesPropostas` ainda não é chamado em lugar nenhum (esperado — consumo entra no 18-02), então não há superfície visível nova nesta entrega.

---
*Phase: 18-aba-opcoes*
*Completed: 2026-09-03*

## Self-Check: PASSED

- FOUND: web/src/copy.js
- FOUND: web/src/App.jsx
- FOUND: .planning/phases/18-aba-opcoes/18-01-SUMMARY.md
- FOUND commit: 1daaed6
- FOUND commit: 086093b
