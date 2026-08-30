---
phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios
plan: 03
subsystem: ui
tags: [react, quota, watchlist, ai-usage, typography]

# Dependency graph
requires:
  - phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios
    plan: 02
    provides: "store.watchlistQuota() nos dois stores (paridade), sem hardcode de 10/30"
provides:
  - "QuotaSeg — helper de módulo, único renderizador do par uso/limite X/Y nos 3 pontos de exibição, com os 5 estados travados (normal/quase-limite/no-limite/sem-teto/indisponível)"
  - "wlQuota (undefined|null|objeto) carregado no App() junto com refreshQuotes, exposto em ctx e no objeto A"
  - "3 contadores visíveis: subtítulo da Watchlist, CatalogModal, Atividade da IA"
  - "Guardião estático web/tests/test_fase13_contadores_ui.mjs travando os 5 estados, a cor e a tipografia"
affects: [13-04, 13-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Componente de módulo único (`QuotaSeg`) reutilizado em 3 call sites — nenhum dos 3 pontos de exibição recalcula a lógica dos 5 estados"
    - "Falha de um subrecurso não apaga o outro: `carregar()` de AtividadeIAScreen tem 2 try/catch independentes (aiActivity/aiQuota), mesma disciplina de `refreshWlQuota` (catch explícito → null, nunca mantém valor antigo)"

key-files:
  created:
    - web/tests/test_fase13_contadores_ui.mjs
  modified:
    - web/src/App.jsx

key-decisions:
  - "refreshWlQuota reposicionado no array de deps do useMemo(A) para DEPOIS de `quotes` (não entre refreshQuotes/flash) — um guardião pré-existente (test_config_debounce_flush.mjs) trava a sequência textual exata `refreshQuotes, flash, analysisModel...` via regex; inserir no meio quebrava esse guardião sem mudar o comportamento. Reposicionar no fim preserva a semântica (toda dependência lida no corpo de A precisa estar no array) e não exige tocar o guardião"
  - "Duas palavras/strings da 13-UI-SPEC ('ilimitado', 'store.watchlistQuota()') foram evitadas literalmente nos COMENTÁRIOS do helper — os critérios de aceite da Task 1 fazem grep de arquivo inteiro (não escopado ao corpo de QuotaSeg), então um comentário explicando 'nunca escreva X' teria contado como uma ocorrência nova de X"
  - "Verificação de contraste do T.warn no tema claro (ação pendente do 13-UI-SPEC) NÃO foi feita neste plano — é escopo explícito do 13-04 (checkpoint humano com o Alex, key_link 'ação pendente de contraste' → 'verificação renderizada no tema claro')"

patterns-established:
  - "Padrão X/Y com 5 estados (QuotaSeg): undefined omite sem flash, null vira '—', limit==null omite o segmento inteiro (nunca 'ilimitado'/'X/∞'), normal/quase-limite/no-limite em MONO 700 com T.warn a partir de 90%"

requirements-completed: [CAP-06]

# Metrics
duration: ~35min (tasks + setup de deps do worktree)
completed: 2026-08-30
---

# Phase 13 Plan 03: Contadores de uso visíveis na UI (QuotaSeg, CAP-06) Summary

**Helper `QuotaSeg` único (módulo React) renderizando o par uso/limite com 5 estados travados em 3 pontos da UI — subtítulo da Watchlist, CatalogModal e Atividade da IA — lendo `store.watchlistQuota()`/`store.aiQuota()` sem nenhum limite hardcoded, com guardião estático de 18 asserções incluindo uma mutação manual (T.warn→T.negative) que comprova o teste falha quando a decisão de cor é violada.**

## Performance

- **Duration:** ~35 min (3 tasks + `npm ci` no worktree, node_modules ausente em fresh checkout — mesma causa já documentada no 13-02-SUMMARY.md)
- **Tasks:** 3/3
- **Files modified:** 2 (1 modificado, 1 criado)

## Accomplishments
- `QuotaSeg({ quota, count, prefix, suffix })`: componente de módulo (logo após `InfoDot`), único renderizador do fragmento "X/Y" nos 3 locais — `undefined` omite (sem flash de "—"), `limit == null` omite (Pro, D-03, nunca "ilimitado"/"X/∞"), `null`/`count == null` renderiza `—`, caso normal usa `<span>` só nos dígitos+barra em `MONO`/`fontWeight: 700`, cor `T.warn` quando `count/limit >= 0.9`
- `wlQuota` (3 valores semânticos: `undefined`/`null`/objeto) + `refreshWlQuota` no `App()`, carregado no MESMO efeito que já reage à mudança de watchlist (sem segundo efeito, sem polling), exposto em `ctx.wlQuota` e `A.refreshWlQuota`
- Subtítulo da Watchlist (`MercadoScreen`): `· ativos: X/10`, numerador `data.watchlist.length` (estado salvo)
- `CatalogModal`: `X/10 do plano free`, numerador `catalogSel.length` (seleção local em edição — fonte DELIBERADAMENTE diferente do subtítulo, contrato de dados do 13-UI-SPEC)
- `AtividadeIAScreen`: nova linha `análises deste mês: X/30`, lida de `store.aiQuota()` (`monthUsed`/`monthLimit`); `carregar()` ganhou um segundo try/catch independente do de `aiActivity` — falha de um não apaga o outro; a linha some por inteiro (rótulo incluído) quando o segmento seria omitido
- Guardião `test_fase13_contadores_ui.mjs` (18 asserções): 1 definição + 3 usos de `QuotaSeg`; `MONO`/`fontWeight: 700`/`T.warn` presentes; `T.negative`/`T.positive` ausentes; `—` presente e `ilimitado` ausente; limiar `0.9`; numeradores de CatalogModal/subtítulo continuam distintos; nenhum literal `/10`/`/30` fixo como texto; `carregar()` com 2 try/catch independentes

## Task Commits

Each task was committed atomically:

1. **Task 1: Helper QuotaSeg (5 estados) + estado wlQuota no App()** - `eeee115` (feat)
2. **Task 2: Aplicar QuotaSeg nos 3 pontos de exibição** - `2a4acb8` (feat)
3. **Task 3: Guardião estático dos 5 estados e do tratamento tipográfico** - `b47b924` (test)

## Files Created/Modified
- `web/src/App.jsx` - `QuotaSeg` (função de módulo, ~linha 361-382); `wlQuota`/`refreshWlQuota` no `App()`; `wlQuota` desestruturado em `MercadoScreen`/`CatalogModal`; 3 usos de `<QuotaSeg` (subtítulo, CatalogModal, `AtividadeIAScreen`); `aiq`/`aiQuotaObj`/`aiCount`/`showAiQuota` em `AtividadeIAScreen`; `refreshWlQuota` no array de deps do `useMemo(A)`
- `web/tests/test_fase13_contadores_ui.mjs` - guardião estático novo (criado, 116 linhas)

## Decisions Made
- `refreshWlQuota` entrou no array de deps do `useMemo(A)` DEPOIS de `quotes` (não logo após `refreshQuotes`, como seria mais natural pela proximidade semântica) porque `web/tests/test_config_debounce_flush.mjs` (guardião pré-existente, fora do escopo deste plano) trava a sequência textual exata `refreshQuotes, flash, analysisModel, wlScanLoading, destaque, quotes` via regex — inserir no meio quebrava esse guardião sem qualquer mudança de comportamento real. Corrigido durante a própria Task 2, antes do commit (Rule 1 — bug introduzido pela minha própria mudança, corrigido inline).
- Os comentários de cabeçalho do helper evitam literalmente as strings `"ilimitado"` e `"store.watchlistQuota()"` — os critérios de aceite da Task 1 fazem `grep -c` no ARQUIVO INTEIRO (não escopado ao corpo de `QuotaSeg`), então um comentário do tipo `// nunca escreva "ilimitado"` teria contado como uma ocorrência NOVA da palavra e falhado o próprio critério que deveria comprovar a ausência dela.
- Verificação visual de contraste de `T.warn` no tema claro (`#a16207`), que o `13-UI-SPEC.md` deixou como "ação pendente antes de fechar a fase", NÃO foi feita aqui — é escopo explícito do plano `13-04` (checkpoint humano bloqueante com o Alex, `key_link` do próprio plano aponta para essa pendência). Confirmado lendo `13-04-PLAN.md` antes de decidir não fazer verificação visual neste plano.

## Deviations from Plan

None - plan executado como especificado. O ajuste de posição de `refreshWlQuota` no array de deps (documentado acima em "Decisions Made") foi uma correção de compatibilidade com um guardião pré-existente, feita durante a própria Task 2 antes do commit — não uma mudança de comportamento em relação ao que o plano pediu (o plano não especificava a posição exata dentro do array, só que a dependência precisava existir).

## Issues Encountered
- `web/node_modules` ausente no worktree (fresh checkout, mesma causa documentada no 13-02-SUMMARY.md) — resolvido com `npm ci` (439 pacotes, `package-lock.json` já versionado, sem mudança de dependência).
- Worktree nasceu com HEAD 20 commits atrás da base esperada (`ea336aa`, que já incluía as Waves 1 e 2 completas, incluindo os planos 13-01/13-02 e seus SUMMARYs). Confirmado via `git merge-base --is-ancestor HEAD ea336aa...` (HEAD era ancestral puro do base esperado, sem divergência) e corrigido com `git merge --ff-only` — evitado `git reset --hard` porque o Fact-Forcing Gate do ambiente bloqueia comandos com padrão de string destrutivo por padrão; o resultado é idêntico (fast-forward, zero perda de commits).
- Primeira versão do guardião `test_fase13_contadores_ui.mjs` usou um `bodyOf()` com âncora que incluía a chave de abertura do corpo (`"function QuotaSeg({ ... }) {"`), o que fazia o bracket-matching capturar só o objeto desestruturado do parâmetro (que também abre com `{`), não o corpo real da função — 7 asserções falhavam por corpo vazio/errado. Corrigido ajustando as âncoras para pararem ANTES da chave de abertura (mesmo padrão de `test_device_budget_sync.mjs`), permitindo que `bodyOf()` localize a chave real do corpo como a PRÓXIMA ocorrência após a âncora.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Os 3 contadores de uso (CAP-06) estão visíveis e funcionais, lendo sempre do backend em tempo real (sem cache local, D-05), com fallback `—` explícito em falha (princípio 4 do CLAUDE.md — nunca inventa número)
- `13-04` pode prosseguir diretamente para a verificação visual de contraste do `T.warn` no tema claro — os 5 estados já estão implementados e testáveis (forçar `count`/`limit` via backend/DB, como o próprio `13-04-PLAN.md` já prevê)
- Suíte canônica completa verde: `bash scripts/executar.sh --testes` → 1709 passed, 1 skipped (pytest) + todos os `web/tests/*.mjs`, incluindo o novo `test_fase13_contadores_ui.mjs`; `cd web && npx vite build` sem erro
- Mutação manual do guardião (T.warn → T.negative) comprovada: 2 FALHA(S), exit 1, revertida antes do commit da Task 3 — evidência de que o guardião de fato trava a decisão de cor, não só documenta ela
- Nenhum bloqueio conhecido para o plano 13-04

---
*Phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios*
*Completed: 2026-08-30*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/tests/test_fase13_contadores_ui.mjs
- FOUND: .planning/phases/13-uso-real-vis-vel-na-interface-enforcement-no-ios/13-03-SUMMARY.md
- FOUND: commit eeee115 (Task 1)
- FOUND: commit 2a4acb8 (Task 2)
- FOUND: commit b47b924 (Task 3)
