---
phase: 05-corre-o-m-dio-c-digo-gate-admin
plan: 06
subsystem: ui
tags: [react, web-admin, finops, rbac, static-guardian]

# Dependency graph
requires:
  - phase: 05-corre-o-m-dio-c-digo-gate-admin
    provides: "Plano 05-02: contrato de backend pronto e testado — alertaGastoIA em /api/obs/usage, llmAlertaGastoPct/llmAlertaJanelaDias em /api/admin/config/ia"
provides:
  - "web-admin/src/App.jsx: linha de alerta preventivo de gasto de IA na aba Custos (4 estados: não configurado / sem base de comparação / acima do limiar / dentro do normal)"
  - "web-admin/src/App.jsx: 2 campos numéricos novos no formulário auditado de MudancaDeLLM (llmAlertaGastoPct, llmAlertaJanelaDias)"
  - "web-admin/src/App.jsx: sentinela PERM_ANY declarando explicitamente a regra de acesso da aba Auditoria, sem estreitar o acesso real"
  - "web/tests/test_fase5_alerta_gasto_admin.mjs e test_fase5_auditoria_perm.mjs: guardiões estáticos rodando na suíte canônica"
affects: [web-admin-portal-admin]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guardião estático (readFileSync do fonte de web-admin/, sem framework de teste novo) para telas de web-admin/ que não têm suíte própria — precedente de test_fase3_custos_falha_brapi.mjs reusado, não reinventado"
    - "Tom 'faint' em Kv para estados sem base suficiente para avaliar (não configurado, histórico insuficiente) — nunca cai no verde de 'positive', regra explícita do CLAUDE.md item 4"

key-files:
  created:
    - web/tests/test_fase5_alerta_gasto_admin.mjs
    - web/tests/test_fase5_auditoria_perm.mjs
  modified:
    - web-admin/src/App.jsx

key-decisions:
  - "Alerta preventivo NUNCA usa tom 'negative' — reservado ao hard stop de metering.py (sinal separado, já existente); fundir os dois numa severidade só é exatamente a regressão que o guardião trava"
  - "PERM_ANY = '*' é sentinela de leitura, não uma permissão real — a aba Auditoria continua acessível a qualquer permissão administrativa, mesma regra de sempre; o backend (require_any_admin_permission()) é quem realmente gateia, o filtro do front é conveniência"
  - "Guardiões novos vivem em web/tests/ (não em web-admin/), seguindo o precedente já estabelecido — web-admin/ não ganhou infraestrutura de teste nova, package.json permanece sem diff"

patterns-established:
  - "Comentário de código evita repetir literal exato de Copywriting Contract entre aspas quando o literal também é asserção de contagem exata em guardião — colisão descoberta e corrigida durante a própria execução deste plano (ver Deviations)"

requirements-completed: [FIX-C38, FIX-C39]

duration: ~20min
completed: 2026-08-23
---

# Phase 05 Plan 06: Alerta preventivo de gasto de IA + regra de acesso explícita da aba Auditoria (portal admin) Summary

**Aba Custos do web-admin passa a mostrar o alerta preventivo de gasto de IA (4 estados, tom âmbar no cruzamento do limiar) que o backend já calculava desde o Plano 05-02, e a aba Auditoria ganha declaração explícita de regra de acesso via sentinela `PERM_ANY`, sem alterar o acesso real.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-08-23T18:20Z
- **Tasks:** 3/3 completed
- **Files modified:** 3 (1 editado, 2 novos)

## Accomplishments
- `Custos()` lê `data.alertaGastoIA` e renderiza os 4 estados no formato exato do Copywriting Contract (05-UI-SPEC.md), reusando o mesmo `Kv` do card "Uso de IA" — sem card novo, sem contêiner novo
- `Kv` ganhou o tom `"faint"` (uma linha no ternário existente) para os 2 estados sem base suficiente para avaliar
- `MudancaDeLLM` ganhou 2 campos numéricos (`llmAlertaGastoPct`, `llmAlertaJanelaDias`) no mesmo formulário auditado, mesma permissão `llm.configurar`, mesmo botão "Salvar (auditado)" — zero permissão nova
- Sentinela `const PERM_ANY = "*"` declara explicitamente a regra da aba Auditoria (qualquer permissão administrativa); filtro `visiveis` trata a sentinela como equivalente a `!v.perm`; nenhuma das outras 9 entradas mudou
- 2 guardiões estáticos novos em `web/tests/`, seguindo o precedente de `test_fase3_custos_falha_brapi.mjs` — `web-admin/` continua sem framework de teste próprio, `package.json` sem diff

## Task Commits

Each task was committed atomically:

1. **Task 1: Linha de alerta na aba Custos + 2 campos no formulário de IA (FIX-C38)** - `ebf9b24` (feat)
2. **Task 2: Regra de acesso explícita na aba Auditoria (FIX-C39)** - `a93fef5` (feat)
3. **[Rule 1 fix] Remoção de duplicação literal no comentário do Task 1** - `8e1fbc8` (fix) — ver Deviations
4. **Task 3: Guardiões estáticos do portal admin** - `f62e086` (test)

## Files Created/Modified
- `web-admin/src/App.jsx` — `Kv` ganha tom `"faint"`; `Custos()` ganha `alertaGasto` (cálculo do estado a partir de `data.alertaGastoIA`) e a linha `Kv` correspondente; `MudancaDeLLM` ganha 2 `campo(...)` novos + as 2 chaves no laço numérico de `salvar`; `PERM_ANY` declarado, entrada de auditoria e filtro `visiveis` atualizados
- `web/tests/test_fase5_alerta_gasto_admin.mjs` — guardião estático de FIX-C38 (20 asserções: literais de copy, leitura do payload, tons por estado, nunca `negative`, tom `faint` em `Kv`, campos numéricos no laço de `salvar`, nenhuma permissão nova em `MudancaDeLLM`)
- `web/tests/test_fase5_auditoria_perm.mjs` — guardião estático de FIX-C39 (29 asserções: `PERM_ANY` declarado, entrada de auditoria sem permissão real, filtro tratando a sentinela, as outras 9 entradas intactas)

## Decisions Made
- Tom `"faint"` (não `"negative"`) para "não configurado"/"sem base de comparação": um alerta desligado ou sem histórico não é "tudo certo" nem é "problema" — é um terceiro estado, consistente com CLAUDE.md item 4 (nunca inferir "normal" da ausência de dado, mas também nunca fabricar alarme onde não há dado suficiente para julgar).
- `PERM_ANY` como sentinela de string (`"*"`) em vez de, por exemplo, um booleano `permAny: true` — mantém o schema de `VIEWS` uniforme (toda entrada tem uma chave `perm` de mesmo tipo), e o filtro fica uma única expressão a mais no OR existente, sem branch novo.
- Guardiões novos ficam em `web/tests/`, não em `web-admin/` — decisão de escopo já fechada no `05-CONTEXT.md`/plano (T-05-SC do threat model): introduzir framework de teste no `web-admin/` seria mudança de infraestrutura fora do escopo de um achado Médio.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comentário do Task 1 duplicava literais de Copywriting Contract, quebrando a contagem exata do guardião**
- **Found during:** Task 3 (escrita do guardião `test_fase5_alerta_gasto_admin.mjs`)
- **Issue:** O comentário adicionado no Task 1 citava `"não configurado"`/`"sem base de comparação"` entre aspas dentro de um comentário de código, fazendo `appAdmin.split(str).length - 1` contar 2 ocorrências em vez de 1 para essas duas strings — o guardião do Task 3 precisa de contagem exata (o próprio plano alerta para não assumir 1 sem checar, mas o caso aqui era uma auto-colisão introduzida pelo comentário, não uma ocorrência pré-existente legítima como a de `"dentro do normal"`).
- **Fix:** Reescrito o comentário para descrever os dois estados sem repetir o texto exato entre aspas.
- **Files modified:** web-admin/src/App.jsx
- **Verification:** `grep -c` das 2 strings volta a 1 cada; `npx vite build` limpo; guardião do Task 3 passa com a contagem exata declarada.
- **Committed in:** `8e1fbc8`

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug de contagem em asserção de teste, causado pelo próprio código deste plano)
**Impact on plan:** Nenhum impacto de escopo — correção mecânica de um comentário, sem mudança de comportamento ou de contrato.

## Issues Encountered
None. `web/node_modules` e `web-admin/node_modules` estavam ausentes no worktree novo (C-24, gap já documentado em `05-CONTEXT.md` e recorrente em fases anteriores) — resolvido com `npm install` em ambos antes de rodar qualquer verificação; `git diff` de `package.json`/`package-lock.json` de ambos os projetos ficou vazio depois do install (nenhuma dependência nova).

## Provas negativas (Task 3, acceptance criteria)

Ambas executadas ao vivo e revertidas antes do commit — sem diff residual:

1. **FIX-C38:** trocado `tone: "warn"` → `tone: "negative"` no estado `acima` de `Custos()`. Resultado: `node web/tests/test_fase5_alerta_gasto_admin.mjs` falhou em 2 asserções (`estado "acima" usa tom "warn"` e `NUNCA usa tom "negative"...`), exit code 1. Revertido via backup do sed (`.bak`), confirmado `git diff --stat` vazio e suíte voltando a passar.
2. **FIX-C39:** trocado `perm: PERM_ANY` → `perm: "observabilidade.ver"` na entrada `id: "auditoria"`. Resultado: `node web/tests/test_fase5_auditoria_perm.mjs` falhou em 2 asserções (`entrada de auditoria carrega perm: PERM_ANY` e `entrada de auditoria NÃO cita a permissão real "observabilidade.ver"`), exit code 1. Revertido via `git checkout -- web-admin/src/App.jsx`, confirmado `git diff --stat` vazio e suíte voltando a passar.

## User Setup Required

None — nenhuma configuração de serviço externo. O admin usa o formulário já existente (`PUT /api/admin/config/ia`, backend pronto desde o Plano 05-02) para configurar limiar e janela do alerta; nenhuma infraestrutura nova em `web-admin/`.

## Next Phase Readiness
- FIX-C38 e FIX-C39 completos ponta a ponta (backend do Plano 05-02 + front deste plano).
- `bash scripts/executar.sh --testes` passa completo: 1365 backend (1 skipped) + toda a suíte web, incluindo os 2 guardiões novos e mais 2 guardiões `test_fase5_*` já presentes de outros planos da Fase 5 (`test_fase5_appmode_fonte_unica.mjs`, `test_fase5_skill_migracao_legado.mjs`) que rodaram no mesmo checkout sem conflito.
- `cd web-admin && npx vite build` limpo, `git diff web-admin/package.json` vazio.
- Sem overlap de arquivo com o plano paralelo 05-07 (rodando em worktree separado na mesma wave) — único arquivo de produto tocado (`web-admin/src/App.jsx`) é exclusivo deste plano no escopo da Fase 5.
- Verificação visual do portal (aba Custos com os 4 estados, formulário com os 2 campos novos) ainda não foi feita ao vivo — pendente de checkpoint humano/smoke test do Alex, mesmo padrão já registrado como pendência em outras fases recentes.

---
*Phase: 05-corre-o-m-dio-c-digo-gate-admin*
*Completed: 2026-08-23*

## Self-Check: PASSED

All created/modified files verified present (`web-admin/src/App.jsx`,
`web/tests/test_fase5_alerta_gasto_admin.mjs`,
`web/tests/test_fase5_auditoria_perm.mjs`, this SUMMARY). All 5 commits
(`ebf9b24`, `a93fef5`, `8e1fbc8`, `f62e086`, `3df220a`) verified present in
`git log`.
