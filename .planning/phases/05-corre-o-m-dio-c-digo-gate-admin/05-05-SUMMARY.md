---
phase: 05-corre-o-m-dio-c-digo-gate-admin
plan: 05
subsystem: ui
tags: [react, jsx, static-guardian, accessibility, appMode]

# Dependency graph
requires:
  - phase: 04-corre-o-alta-story-ux
    provides: App.jsx na forma pós-Fase 4 (8181 linhas, ctx.operador já existente desde 2026-08-07)
provides:
  - "Fonte única de 'estamos em Modo Operador?' em App.jsx — ctx.operador (fora de App()) / appMode (dentro de App()) sem recomputação residual"
  - "Guardião estático que fecha a classe do erro de recomputação de appMode (test_fase5_appmode_fonte_unica.mjs)"
  - "Toggle mestre 'Entrada automática' com atributo HTML disabled real e feedback visual (opacity/cursor) no padrão dos irmãos gateados"
affects: [web/src/App.jsx, web/tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guardião estático (readFileSync + regex sobre o fonte, sem build/DOM) para travar classes de erro de recomputação de estado em App.jsx"
    - "Prova negativa executada e revertida como parte da verificação do guardião (mutação temporária → confirma FALHA → reverte → confirma PASSA)"

key-files:
  created:
    - web/tests/test_fase5_appmode_fonte_unica.mjs
  modified:
    - web/src/App.jsx
    - web/tests/test_entrada_automatica_ui.mjs
    - web/tests/test_agente_modo_estudo_ui.mjs
    - web/tests/test_decisao_modo.mjs
    - web/tests/test_modo_operador.mjs

key-decisions:
  - "3 guardiões pré-existentes com asserts hard-coded na expressão LITERAL antiga de leitura de appMode foram atualizados (não apagados) para a expressão nova, com nota datada FIX-C21 — a migração mecânica do plano quebrou esses asserts por design, não por regressão"
  - "Prova negativa de C-21 e C-23 executada por mutação temporária do fonte real (não simulação), revertida via Edit e confirmada byte-idêntica ao estado pré-mutação via diff"

requirements-completed: [FIX-C21, FIX-C23]

# Metrics
duration: ~30min
completed: 2026-08-23
---

# Phase 05 Plan 05: Fonte única de appMode + Toggle disabled Summary

**Migração mecânica de 7+3 leituras redundantes de `appMode` para a fonte única `ctx.operador`/`appMode`, e atributo HTML `disabled` real no Toggle mestre de Entrada automática, ambos travados por guardião estático.**

## Performance

- **Duration:** ~30 min
- **Completed:** 2026-08-23T17:46:22Z
- **Tasks:** 3/3 completos
- **Files modified:** 6 (1 App.jsx, 1 novo teste, 4 testes estendidos/corrigidos)

## Accomplishments
- FIX-C21: as 10 leituras redundantes de `appMode` que o REPORT-01 mapeou (re-grepadas em 2026-08-23, tabela do plano confirmada linha a linha) foram migradas para a fonte única — 7 componentes fora de `App()` leem `ctx.operador`, 3 pontos dentro de `App()` leem a variável local `appMode`, e a própria montagem de `ctx.operador` parou de recomputar e passou a derivar de `appMode`
- FIX-C23: `Toggle` ganhou a prop `disabled`, aplicada como atributo HTML real no `<button>` (não só cosmético), com o mesmo padrão numérico de esmaecimento dos 2 irmãos gateados já corretos (`opacity: 0.6` / `cursor: not-allowed`), zero mudança de cor e zero cópia nova
- Guardião novo (`test_fase5_appmode_fonte_unica.mjs`) fecha a CLASSE do erro de C-21 — testado com prova negativa real (reintroduzir a leitura independente quebra o teste, reverter volta a passar)
- Guardião existente (`test_entrada_automatica_ui.mjs`) estendido só-adição com a seção FIX-C23 — testado com prova negativa real (remover `disabled={disabled}` quebra o teste, reverter volta a passar)
- 3 guardiões pré-existentes que travavam a expressão literal ANTIGA de `appMode` foram atualizados para a expressão nova, preservando a garantia original de cada um

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Migrar as leituras de appMode para a fonte única (FIX-C21)** - `1f3eab2` (fix)
2. **Task 2: Toggle com disabled real no gate de Entrada automática (FIX-C23)** - `179ea1d` (fix)
3. **Task 3: Guardiões — classe do erro de appMode e estado disabled do Toggle** - `dcda6ab` (test, inclui os 3 guardiões pré-existentes corrigidos como parte da mesma verificação)

## Files Created/Modified
- `web/src/App.jsx` — 7 leituras fora de `App()` migradas para `ctx.operador` (linhas ~1767, 1979, 2199, 3376, 4540, 5996, 6196), 3 pontos dentro de `App()` migrados para a variável local `appMode` (modoApp, `runStopAlvoFor`, snapshot `perfil`), montagem de `ctx.operador` deixou de recomputar (`operador: appMode === "operador"`), comentário da montagem atualizado para tempo presente citando FIX-C21; `Toggle` ganhou prop `disabled` (atributo HTML real + opacity/cursor), call site de "Entrar automaticamente" ganhou `disabled={!operador}` mantendo o guard `operador &&` no `onClick`
- `web/tests/test_fase5_appmode_fonte_unica.mjs` (novo) — guardião estático de FIX-C21, filtra comentários antes de contar `.appMode`, assert de 1 única leitura (a derivação), `ctx.operador` >= 7x, escritas preservadas
- `web/tests/test_entrada_automatica_ui.mjs` — estendido só-adição com a seção FIX-C23 (assinatura/atributo/opacity/cursor do Toggle, call site, linha de cor intocada)
- `web/tests/test_agente_modo_estudo_ui.mjs`, `web/tests/test_decisao_modo.mjs`, `web/tests/test_modo_operador.mjs` — asserts que citavam a expressão literal antiga de leitura de `appMode` atualizados para a expressão nova (nota datada FIX-C21), garantia original preservada

## Decisions Made
- Manter a migração 100% mecânica: cada substituição foi conferida linha a linha contra a tabela `<interfaces>` do plano antes de aplicar, incluindo os casos de equivalência lógica não-óbvia (fallback `|| "estudo"` da linha 7018 e `(data.config || {})` da 7430, ambos já cobertos pela variável `appMode`, que sempre resolve para `"operador"`/`"estudo"`)
- Os 3 guardiões pré-existentes com asserts na expressão literal antiga foram ATUALIZADOS, não apagados nem ignorados — CLAUDE.md é explícito ("guardiões de teste não se apagam — reversão deliberada atualiza o guardião com nota"); cada assert manteve a garantia original (ex.: "a flag operador está em escopo", "o plano só existe no modo operador"), só a expressão regex mudou

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Regex do guardião novo tinha falso positivo por proximidade**
- **Found during:** Task 3 (escrita da seção FIX-C23 do guardião estendido)
- **Issue:** A asserção "Toggle NÃO referencia T.accent condicionado a disabled" usava uma regex de proximidade (`disabled[\s\S]{0,40}T\.accent`) que capturava qualquer ocorrência de `disabled` a até 40 caracteres de `T.accent` em QUALQUER lugar da função `Toggle` — inclusive combinações não-relacionadas (ex.: o atributo `disabled={disabled}` do `<button>` estando a poucas dezenas de caracteres do `border: on ? T.accent : ...` da linha de cor, que não depende de `disabled`). Isso fazia o guardião falhar mesmo com a implementação correta.
- **Fix:** Substituída por uma extração precisa da linha `const s = {...}` (a única fonte de bg/border/knob/color) via regex `/const s = \{[^}]*\};/`, seguida de um assert de que essa linha específica não contém a palavra `disabled` — testa exatamente o invariante do contrato (cor 100% baseada em `on`, nunca em `disabled`), sem falso positivo de proximidade.
- **Files modified:** web/tests/test_entrada_automatica_ui.mjs
- **Verification:** Guardião passa com a implementação real; a extração isolada de `const s = {...}` foi conferida manualmente contra o fonte
- **Committed in:** dcda6ab (Task 3 commit)

**2. [Rule 1 - Bug] 3 guardiões pré-existentes quebravam com a migração mecânica de FIX-C21**
- **Found during:** Task 3 (primeira execução da suíte canônica completa, com cwd correto — ver Issues Encontrados abaixo)
- **Issue:** `test_agente_modo_estudo_ui.mjs`, `test_decisao_modo.mjs` e `test_modo_operador.mjs` (guardiões de fases anteriores, F7.1/qa-40) tinham asserts com a expressão LITERAL antiga de leitura de `appMode` hard-coded em regex (ex.: `operador: !!\(data && data\.config && data\.config\.appMode === "operador"\),`). A migração da Task 1 (mandada pelo plano, linha a linha contra a tabela `<interfaces>`) mudou essas expressões de propósito — os 5 asserts falhando eram consequência ESPERADA da mudança arquitetural deliberada, não uma regressão introduzida por engano.
- **Fix:** Cada assert foi atualizado para a expressão nova (`ctx.operador` / `appMode === "operador"`), preservando a garantia original de cada teste (ex.: "as duas telas têm a flag operador em escopo", "plano só no modo operador", "disclaimer da persona no modo operador"), com comentário datado citando FIX-C21 (2026-08-23) explicando a mudança — conforme o guardrail do CLAUDE.md ("guardiões de teste não se apagam — reversão deliberada atualiza o guardião com nota").
- **Files modified:** web/tests/test_agente_modo_estudo_ui.mjs, web/tests/test_decisao_modo.mjs, web/tests/test_modo_operador.mjs
- **Verification:** `bash scripts/executar.sh --testes` completo (1325 testes backend + 96 suítes web) passa 100% depois da correção
- **Committed in:** dcda6ab (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 - bug)
**Impact on plan:** Ambos os fixes eram necessários para a suíte canônica passar de verdade contra o código real; nenhum scope creep — os 3 guardiões corrigidos continuam testando exatamente o que testavam antes, só com a expressão de código atualizada.

## Issues Encountered

**cwd-drift no worktree durante verificação (não afetou os commits, só a sequência de comandos de build/teste).** As duas primeiras rodadas de `npx vite build` e `bash scripts/executar.sh --testes` foram executadas com `cd /Users/acamerini/dev/bolsia/b3-agente` / `cd /Users/acamerini/dev/bolsia/b3-agente/web` — caminho do REPOSITÓRIO PRINCIPAL, não do worktree (`/Users/acamerini/dev/bolsia/b3-agente/.claude/worktrees/agent-ab0406df7a52353e9`). Essas rodadas validaram o código do repo principal (não editado), não as mudanças reais — o build "passou" e a suíte "passou" mas sem checar nada do trabalho feito. Identificado ao notar que a saída de um `node tests/test_entrada_automatica_ui.mjs` não mostrava os asserts novos que eu tinha acabado de escrever. Causa raiz adicional: `web/node_modules` estava ausente no worktree (achado C-24 do REPORT-01 recorrente — confirmado outra vez). Resolvido com `npm install` em `web/` do worktree e refazendo toda a verificação (build + suíte completa + as duas provas negativas) usando o caminho absoluto correto do worktree. Nenhum commit foi afetado — `git add`/`git commit` sem `cd` explícito sempre operaram no worktree correto (cwd default do ambiente), então os 2 primeiros commits (Task 1 e Task 2) já estavam corretos antes da correção; só a sequência de verificação precisou ser refeita. Importante: o CONTEÚDO dos commits 1f3eab2 (Task 1) e 179ea1d (Task 2) só foi de fato validado pela suíte canônica completa DEPOIS da correção de cwd, na investigação da Task 3 (é essa mesma rodada, com cwd correto, que expôs os 3 guardiões pré-existentes quebrados pela migração — ver deviation 2 abaixo) — os builds/testes "verdes" anteriores a essa rodada não atestavam nada sobre o código real editado.

## User Setup Required

None - nenhuma configuração de serviço externo necessária.

## Next Phase Readiness
- FIX-C21 e FIX-C23 fechados, prontos para o merge da wave 1 da Fase 5
- Nenhum bloqueio para os outros planos da fase (05-01 a 05-04, 05-06 a 05-08) — este plano não tocou nenhum arquivo compartilhado além dos testes/App.jsx já listados, sem overlap declarado com os demais planos da wave
- Observação operacional (não é blocker, mas vale registrar para o orquestrador): qualquer worktree novo desta fase que rode a suíte web precisa de `npm install` em `web/` antes — `web/node_modules` não vem populado no checkout do worktree (mesmo padrão já documentado em C-24)

---
*Phase: 05-corre-o-m-dio-c-digo-gate-admin*
*Completed: 2026-08-23*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/tests/test_fase5_appmode_fonte_unica.mjs
- FOUND: web/tests/test_entrada_automatica_ui.mjs
- FOUND: .planning/phases/05-corre-o-m-dio-c-digo-gate-admin/05-05-SUMMARY.md
- FOUND commit: 1f3eab2 (Task 1)
- FOUND commit: 179ea1d (Task 2)
- FOUND commit: dcda6ab (Task 3)
