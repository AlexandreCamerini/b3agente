---
phase: 03-corre-o-cr-tico-alto
plan: 05
subsystem: api
tags: [fastapi, rbac, adr-013, admin-portal, react, kill-switch]

# Dependency graph
requires:
  - phase: 03-02
    provides: "candle_provider.py e web-admin custos card (linha de base pós-fase-3 wave 1)"
  - phase: 03-04
    provides: "main.py com _gate_analise e o restante da linha de base pós-wave-2"
provides:
  - "timing_watch.kill_switch_on() com o mesmo padrão memória→DB→env de agent.kill_switch_on (ADR-013), generalizado em vez de duplicado às cegas"
  - "GET/PUT /api/admin/timing-watch/kill-switch, par RBAC-gated do kill-switch do agente, mesmas permissões execucao_automatica.ver/.controlar"
  - "/api/agent/status expõe timingWatchKillSwitch"
  - "TimingWatchKillSwitchBox + KPI 'PUSH DO GATILHO' no portal admin (aba Automação + Visão Geral)"
  - "guardiões: server/tests/test_fase3_timing_watch_kill.py (17 testes), web/tests/test_fase3_admin_timing_watch.mjs (26 asserções)"
affects: [fase-5-observabilidade, C-37-alerta-kill-switch-ligado-ha-N-horas]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "2º kill-switch clonado do padrão memória→DB→env já estabelecido por agent.kill_switch_on — mesma estrutura de globals (_DB_CONN/_DB_ENABLED/_KILL_MEM/_KILL_DB_CHECKED), mesmos docstrings de justificativa, generalizado por cópia deliberada em vez de abstração prematura"
    - "Par de rotas/componentes 'irmãos': UI e API do 2º interruptor ficam adjacentes ao 1º (mesma permissão, texto adjacente, renderização imediatamente após) — reduz a chance de alguém encontrar um sem o outro"

key-files:
  created:
    - server/tests/test_fase3_timing_watch_kill.py
    - web/tests/test_fase3_admin_timing_watch.mjs
  modified:
    - server/app/timing_watch.py
    - server/app/main.py
    - web-admin/src/api.js
    - web-admin/src/App.jsx
    - .planning/phases/03-corre-o-cr-tico-alto/deferred-items.md

key-decisions:
  - "Ampliação deliberada da tolerância da env B3_TIMING_PUSH_KILL: de == \"1\" estrito para (\"1\",\"true\",\"TRUE\",\"yes\") após .strip(), igualando o contrato de agent.kill_switch_on — instruído explicitamente pelo PLAN (não é deviation, é comportamento pedido), documentado em comentário no código e no docstring do módulo para não parecer acidental"
  - "Task 2's acceptance criterion sobre 'nenhuma permissão nova' foi verificado por AUSÊNCIA DE UMA TERCEIRA string de permissão distinta (o grupo execucao_automatica já tinha .ver e .controlar em HEAD antes desta plan) — a leitura literal do grep sugerido no PLAN ('devolve exatamente execucao_automatica.controlar') está desalinhada com o estado pré-existente do arquivo (linha 440 comentário, linha 1174 nav-tab perm já usavam .ver); documentado abaixo em Deviations"

patterns-established:
  - "Pattern 1: interruptor de emergência novo = clone estrutural do padrão existente (agent.kill_switch_on), nunca abstração genérica prematura — cada módulo mantém sua própria cópia dos 4 globals + 4 funções, testável isoladamente"

requirements-completed: [FIX-C35]

# Metrics
duration: ~55min
completed: 2026-08-19
---

# Phase 03 Plan 05: Kill-switch do push de gatilho (C-35) Summary

**`timing_watch.kill_switch_on()` ganha o mesmo padrão memória→DB→env do kill-switch do agente (ADR-013), com duas rotas admin RBAC-gated, campo em `/api/agent/status`, e o par `TimingWatchKillSwitchBox`/KPI "PUSH DO GATILHO" no portal — o 2º interruptor do sistema deixa de precisar de redeploy para ser revertido.**

## Performance

- **Duration:** ~55 min (inclui recuperação de worktree via merge fast-forward)
- **Completed:** 2026-08-19
- **Tasks:** 3/3
- **Files modified:** 4 (`server/app/timing_watch.py`, `server/app/main.py`, `web-admin/src/api.js`, `web-admin/src/App.jsx`) + 2 criados (`server/tests/test_fase3_timing_watch_kill.py`, `web/tests/test_fase3_admin_timing_watch.mjs`)

## Accomplishments

- `timing_watch.kill_switch_on()` deixou de ler SÓ a env `B3_TIMING_PUSH_KILL` — agora segue memória → DB (`admin_config`, chave `timingWatchKillSwitch`) → env AO VIVO → default (desligado), com `configure_db`, `reset_kill_switch_cache` e `set_kill_switch` espelhando byte a byte o padrão já estabelecido por `agent.kill_switch_on` (ADR-013), incluindo os dois achados de revisão já corrigidos lá (try/except na leitura do DB; `_KILL_DB_CHECKED` para não bater no SQLite a cada tick do scheduler).
- Duas rotas novas — `GET`/`PUT /api/admin/timing-watch/kill-switch` — são o par RBAC-gated irmão das rotas do kill-switch do agente: mesmas permissões (`execucao_automatica.ver`/`.controlar`, nenhuma criada), inseridas imediatamente após o par existente, com auditoria de transição em `admin_audit_log` (`entity="timing_watch_kill_switch"`).
- `/api/agent/status` agora expõe `timingWatchKillSwitch`, fora de `agent.status_snapshot()` de propósito (subsistemas separados, sem acoplamento).
- O portal admin ganhou `TimingWatchKillSwitchBox` — clone estrutural exato de `KillSwitchBox`, mesmo botão/confirm/fallback de permissão, texto literal do Copywriting Contract — renderizado imediatamente após o box do agente em Automação (par casado), e um KPI "PUSH DO GATILHO" irmão do "KILL-SWITCH" em Visão Geral.
- Dois guardiões novos: 17 testes backend (`test_fase3_timing_watch_kill.py`, unidade + rota HTTP) e 26 asserções estruturais no front (`test_fase3_admin_timing_watch.mjs`).
- Suíte canônica inteira (`bash scripts/executar.sh --testes`) verde: 1076 testes de backend + todos os `.mjs` do front, zero falha nova.

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: `timing_watch.kill_switch_on` ganha o padrão memória→DB→env** - `f557c98` (feat) — 10 testes de unidade
2. **Task 2: Rotas admin do kill-switch do push + campo no `/api/agent/status`** - `af479fd` (feat) — 7 testes de rota somados aos 10 da Task 1 (17 no arquivo)
3. **Task 3: `TimingWatchKillSwitchBox` e KPI "PUSH DO GATILHO" no portal admin** - `c2c5e4e` (feat) — guardião `.mjs` novo, 26 asserções

_Merge de recuperação do worktree (`claude/gsd-revisao-aplicacao-b9b4ef`, fast-forward, zero conflitos) feito antes da Task 1 — obrigatório pelo `known_environment_gaps` do prompt, não é parte do escopo do plano._

## Files Created/Modified

- `server/app/timing_watch.py` — `configure_db`, `reset_kill_switch_cache`, `set_kill_switch`, `kill_switch_on` reescrito (padrão memória→DB→env); docstring do módulo atualizado
- `server/app/main.py` — import de `timing_watch`; `timing_watch.configure_db(_conn)` no bootstrap; par de rotas `GET`/`PUT /api/admin/timing-watch/kill-switch`; campo `timingWatchKillSwitch` em `/api/agent/status`
- `web-admin/src/api.js` — `timingWatchKillSwitchGet`/`timingWatchKillSwitchPut`
- `web-admin/src/App.jsx` — `TimingWatchKillSwitchBox` (novo), KPI "PUSH DO GATILHO" em `VisaoGeral`, renderização em `Automacao` logo após `KillSwitchBox`
- `server/tests/test_fase3_timing_watch_kill.py` — 17 testes (10 unidade + 7 rota)
- `web/tests/test_fase3_admin_timing_watch.mjs` — guardião estático, 26 asserções
- `.planning/phases/03-corre-o-cr-tico-alto/deferred-items.md` — nota de verificação (gap de `node_modules` pré-existente, confirmado não-bloqueante nesta plan)

## Decisions Made

- **Ampliação da tolerância da env `B3_TIMING_PUSH_KILL`** (`== "1"` → `("1","true","TRUE","yes")` após `.strip()`): instruída explicitamente pelo PLAN (Task 1, `<action>`), não é uma decisão autônoma do executor — documentada em comentário no código (`kill_switch_on` docstring) e no docstring do módulo, citando C-35, para não parecer uma mudança acidental de contrato.
- **Leitura do critério de aceite "nenhuma permissão nova" por AUSÊNCIA de terceira string, não pelo grep literal do PLAN.** O PLAN sugere `grep -o 'execucao_automatica\.[a-z]*' web-admin/src/App.jsx | sort -u` devolvendo exatamente `execucao_automatica.controlar` — mas `execucao_automatica.ver` já aparecia em `App.jsx` ANTES desta plan (linha 440, comentário do `KillSwitchBox` original; linha 1174, permissão da aba "Automação" no menu), então o grep sugerido nunca teria passado nem no HEAD anterior a esta plan. Verifiquei a intenção real do critério (nenhuma permissão NOVA introduzida) comparando o conjunto de strings distintas antes/depois da Task 3: `{"execucao_automatica.controlar", "execucao_automatica.ver"}` em ambos — nenhuma terceira string. Ver Deviations abaixo.

## Deviations from Plan

### Auto-fixed Issues

Nenhum desvio via Regras 1-3 (auto-fix de bug/funcionalidade/bloqueio) — o plano foi executado como escrito.

### Discrepância de critério de aceite (não é bug de código, é imprecisão do PLAN)

**1. Acceptance criterion da Task 3 ("nenhuma string de permissão nova") tinha um grep cujo resultado esperado já não batia com o HEAD anterior à Task 3**
- **Found during:** Task 3, verificação de acceptance criteria
- **Issue:** `grep -o 'execucao_automatica\.[a-z]*' web-admin/src/App.jsx | sort -u` no HEAD imediatamente anterior à Task 3 (commit `af479fd`) já devolvia `execucao_automatica.controlar` E `execucao_automatica.ver` (duas linhas), não uma. O texto do PLAN esperava "exatamente `execucao_automatica.controlar`" — criterio escrito sem levar em conta que `.ver` já existia no arquivo por outros motivos (comentário do `KillSwitchBox` original na linha 440, e a permissão da aba de navegação "Automação" na linha 1174).
- **Resolução:** Reinterpretei o objetivo real do critério — "nenhuma permissão NOVA introduzida" (o motivo declarado no `<action>` da Task 3) — e verifiquei por comparação de conjunto: `git show <HEAD-anterior>:web-admin/src/App.jsx | grep -o ... | sort -u` vs. o mesmo grep após minhas mudanças. Ambos retornam exatamente `{execucao_automatica.controlar, execucao_automatica.ver}` — nenhuma string nova. Não fiz nenhuma mudança de código por causa disso; é só uma nota de verificação para não deixar a discrepância entre "o que o PLAN pedia literalmente" e "o que o HEAD já tinha" sem registro.
- **Files modified:** nenhum (achado é sobre o critério de verificação, não sobre o código)
- **Verification:** `git show f557c98^:web-admin/src/App.jsx | grep -o 'execucao_automatica\.[a-z]*' | sort -u` e `grep -o 'execucao_automatica\.[a-z]*' web-admin/src/App.jsx | sort -u` (pós Task 3) devolvem o MESMO conjunto de 2 strings.
- **Committed in:** N/A (nenhum código alterado por este achado)

---

**Total deviations:** 0 auto-fixed via Regras 1-3; 1 nota de discrepância de critério de aceite (sem impacto de código)
**Impact on plan:** Nenhum sobre o comportamento entregue. O plano foi executado como escrito; a nota acima existe só para que verify-phase não trave tentando reproduzir um grep cujo resultado esperado já estava desatualizado antes da Task 3 começar.

## Issues Encountered

- **Worktree em base desatualizada (esperado, coberto pelo `known_environment_gaps` do prompt).** `grep _gate_analise server/app/main.py` deu `HAS_DEP=false` no início da execução. Recuperado com `git merge claude/gsd-revisao-aplicacao-b9b4ef` — fast-forward limpo, zero conflitos, antes de qualquer commit da Task 1. Confirmado `HAS_DEP=true` após o merge.
- **cwd real do agente divergia dos caminhos apontados pelo prompt.** O prompt e o `known_environment_gaps` referenciavam caminhos absolutos sob `.claude/worktrees/peaceful-swanson-e9e462/`, mas o `cwd` real do ambiente de execução (ferramenta Bash/Edit) é `.claude/worktrees/agent-abf382d4a6c03e2fc/` (branch `worktree-agent-abf382d4a6c03e2fc`, distinto e correto para este agente). Confirmado via `diff` que os arquivos relevantes (`main.py`, `timing_watch.py`, `App.jsx`, `api.js`, o próprio `03-05-PLAN.md`) eram byte-idênticos entre os dois worktrees antes de qualquer edição — usei `peaceful-swanson-e9e462` só para LEITURA/orientação inicial (antes de descobrir a divergência) e fiz TODAS as edições/commits em `agent-abf382d4a6c03e2fc`, o worktree real desta sessão. Nenhuma edição foi perdida ou aplicada no lugar errado.
- **Gap de `web/node_modules` pré-existente (mesmo já documentado por 03-04), confirmado não-bloqueante.** `bash scripts/executar.sh --testes` sem `node_modules` reporta 7 falhas em `web/tests/*.mjs`, todas por `ERR_MODULE_NOT_FOUND: '@capacitor/core'` (import em `web/src/persistence.js`), arquivo que esta plan não toca. Confirmei que `package-lock.json` de `web/` e `web-admin/` são byte-idênticos ao clone principal e criei um symlink TEMPORÁRIO para o `node_modules` já instalado lá, só para rodar `npx vite build` e a suíte canônica completa — removido antes de cada `git add`/commit (`node_modules/` é gitignored, então nada vaza pro histórico de qualquer forma). Com o symlink: suíte canônica inteira verde, exit 0, zero `[X]` (as 7 falhas desaparecem). Nota adicionada em `.planning/phases/03-corre-o-cr-tico-alto/deferred-items.md` sob `## 03-05`, sem duplicar a entrada já existente de 03-04.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- C-35 fechado: o 2º kill-switch do sistema (push do gatilho) tem visibilidade e controle em runtime equivalentes ao kill-switch do agente — nenhum trabalho de fiação adicional necessário para esta frente.
- C-37 (fase 5, alerta "kill-switch ligado há N horas") pode se apoiar no `admin_audit_log` com `entity="timing_watch_kill_switch"` gravado por esta plan, seguindo o mesmo padrão já usado por `agent_kill_switch` — nenhuma mudança de schema necessária.
- Ação recomendada para o orquestrador/humano: rodar `npm install` em `web/` neste worktree (ou confirmar que o ambiente de merge/CI já tem `web/node_modules`) antes de tratar a suíte canônica como 100% verde sem intervenção manual — o gap está isolado, documentado e confirmado não-bloqueante nesta plan (ver Issues Encountered).

## Self-Check: PASSED

- FOUND: `server/app/timing_watch.py`
- FOUND: `server/app/main.py`
- FOUND: `web-admin/src/api.js`
- FOUND: `web-admin/src/App.jsx`
- FOUND: `server/tests/test_fase3_timing_watch_kill.py`
- FOUND: `web/tests/test_fase3_admin_timing_watch.mjs`
- FOUND: `.planning/phases/03-corre-o-cr-tico-alto/deferred-items.md`
- FOUND commit `f557c98` (feat: timing_watch kill-switch memória→DB→env, C-35)
- FOUND commit `af479fd` (feat: rotas admin + /api/agent/status, C-35)
- FOUND commit `c2c5e4e` (feat: TimingWatchKillSwitchBox + KPI, C-35)

---
*Phase: 03-corre-o-cr-tico-alto*
*Completed: 2026-08-19*
