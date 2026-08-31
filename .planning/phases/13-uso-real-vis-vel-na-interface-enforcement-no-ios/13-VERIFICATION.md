---
phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios
verified: 2026-08-30T23:00:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 13: Uso real visível na interface + enforcement no iOS Verification Report

**Phase Goal:** Usuário no plano gratuito vê o número real de uso/limite —
ativos na watchlist e análises de IA no mês — antes de esbarrar no limite,
tanto no web quanto no app iOS nativo, nunca estimado ou escondido; e no app
iOS nativo, o mesmo limite de 10 ativos que já vale no web/PWA desde a Fase
12 passa a valer de verdade (CAP-12).

**Verified:** 2026-08-30
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (9 Success Criteria from ROADMAP.md)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Usuário free vê "ativos: X/10" com contagem real, visível sem abrir modal | ✓ VERIFIED | `App.jsx:3452` — `<QuotaSeg quota={wlQuota} count={(data.watchlist \|\| []).length} prefix="  ·  ativos: " />` no subtítulo da `MercadoScreen`. Guardião `test_fase13_contadores_ui.mjs` passa (18/18 asserções). |
| 2 | Usuário free vê "análises deste mês: X/30" com `monthUsed` real de `/api/ai/quota` | ✓ VERIFIED | `App.jsx:5036`, dentro de `AtividadeIAScreen`, lendo `store.aiQuota()` em try/catch independente de `aiActivity`. |
| 3 | Se o backend não confirmar o número, mostra estado de erro/indisponível — nunca número inventado | ✓ VERIFIED | `QuotaSeg` (`App.jsx:374-382`): `quota === null \|\| count == null` renderiza `—` em texto normal; nenhum fallback numérico ou cache. Rastreado a `refreshWlQuota`'s `catch { setWlQuota(null) }` (nunca mantém valor antigo). |
| 4 | `deviceStore` e `serverStore` expõem o mesmo par de números via métodos espelhados (paridade) | ✓ VERIFIED | `watchlistQuota()` presente e idêntico em nome nos dois stores (`persistence.js`). `node web/tests/test_fase3_paridade_stores_generica.mjs` → 0 assimetrias (63 métodos em cada lado); `test_api_parity.mjs` → 6/6 passam. Executado nesta verificação, não só lido. |
| 5 | Usuário pro não vê limite fabricado (nem "X/10" nem "ilimitado") | ✓ VERIFIED | `QuotaSeg`: `quota.limit == null` → `return null` (segmento inteiro omitido). Guardião assere ausência literal de "ilimitado" no corpo do helper. |
| 6 | Usuário free no iOS com 10 ativos não consegue adicionar o 11º — gate ANTES do `write()`, usando `max_watchlist` real, nunca hardcoded | ✓ VERIFIED (com ressalva, ver Anti-Patterns) | `persistence.js:893`: `canAddTicker(doc.watchlist.length, {..., maxWatchlist: quota.limit})` — CR-01 (bug crítico achado no code review pós-fase: o gate comparava contra `quota.count`, contagem SERVER-side estruturalmente desconectada do device local-first) está corrigido no commit `101335e`. **Mutation-testado nesta verificação**: revertendo a linha para `canAddTicker(quota.count, ...)`, o guardião `test_fase13_watchlist_quota_ios.mjs` falha (1 FALHA, exit 1); com o código atual, passa (exit 0). Código restaurado ao original após o teste, `git diff` vazio. |
| 7 | `web/src/plan.js` perde a frase de CTA "Faça upgrade para adicionar mais." | ✓ VERIFIED | `grep -c "Faça upgrade" web/src/plan.js` → 0. `canAddTicker` reason agora é fato+motivo ("Você atingiu o limite de N ativos do plano X."). |
| 8 | Resíduos "BolsIA" limpos em `mydata_budget.py`/`MEDICAO-Mydata-2026-08-27.md`, sem tocar arquivos históricos protegidos | ✓ VERIFIED | `grep -n "BolsIA" server/app/mydata_budget.py docs/MEDICAO-Mydata-2026-08-27.md` → 0 ocorrências (exit 1). `RELEASES.md`/`qa/*` continuam com "BolsIA" intacto (registro histórico preservado, guardrail respeitado). `BOLSAI_API_KEY` (identificador do provedor externo) intocado. |
| 9 | Checkpoint humano: Alex confirma/corrige o nome do app no App Store Connect | ✓ VERIFIED | `13-04-SUMMARY.md`: veredito registrado — nome encontrado era "B3 Ai Agent" (não "BolsIA" como hipotetizado), corrigido pelo Alex diretamente no portal para "Boris+". Item inerentemente não verificável por código; tratado o veredito da SUMMARY como fonte de verdade, conforme instrução da tarefa. |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `server/app/main.py` (`GET /api/watchlist/quota`) | Endpoint read-only `{count, limit, planId}` lendo `plan.py` | ✓ VERIFIED | Rota existe, autenticada por `current_scope`, sem `10` hardcoded. |
| `server/tests/test_fase13_watchlist_quota.py` | Guardião de contrato (free/anônimo/pro) | ✓ VERIFIED | 4/4 testes passam (`pytest -q` executado nesta verificação). |
| `web/src/api.js` (`watchlistQuota`) | Wrapper HTTP | ✓ VERIFIED | `req("GET", "/api/watchlist/quota")` presente. |
| `web/src/persistence.js` (`watchlistQuota`, gate fail-closed) | Paridade + gate em `addWatchlistTicker`/`putWatchlist` | ✓ VERIFIED | Ambos gates presentes, fail-closed confirmado (catch → throw), fonte de contagem local confirmada por mutation test. |
| `web/src/plan.js` (`canGrowWatchlistTo`) | Espelho de `can_grow_watchlist_to` (operador `>`) | ✓ VERIFIED | Função existe, semântica de massa correta. |
| `web/src/App.jsx` (`QuotaSeg` + 3 call sites) | Helper de 5 estados nos 3 pontos do UI-SPEC | ✓ VERIFIED | 1 definição, 3 usos, todos os tokens de estilo corretos (MONO/700/T.warn, sem T.negative/positive). |
| `web/tests/test_fase13_watchlist_quota_ios.mjs` | Guardião estático de ordem + fonte de contagem | ✓ VERIFIED, com gap de simetria | Pina `addWatchlistTicker` explicitamente; **não pina** a mesma checagem para `putWatchlist`/`canGrowWatchlistTo` (ver Anti-Patterns). |
| `web/tests/test_fase13_contadores_ui.mjs` | Guardião dos 5 estados/tipografia | ✓ VERIFIED | 18/18 asserções passam. |
| `web/src/version.js` / `server/web_dist` | Publicação com `BUILD_ID` novo | ✓ VERIFIED | `BUILD_ID = "F10-20260830-02"` presente em `version.js` e propagado ao bundle publicado (`server/web_dist/assets/index-Cs5oE6Ep.js`). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `main.py::watchlist_quota` | `plan.py::PLAN_FREE/PLAN_PRO` | `_plano_do_escopo(scope).get("max_watchlist")` | ✓ WIRED | Confirmado por leitura de código + teste de contrato. |
| `deviceStore.addWatchlistTicker` | `api.js::watchlistQuota` | chamada antes do `write()` | ✓ WIRED | Confirmado por guardião estático + mutation test. |
| `deviceStore.putWatchlist` | `plan.js::canGrowWatchlistTo` | checagem de crescimento em massa | ✓ WIRED (funcionalmente correto, guardião incompleto) | Código correto (`final.length`), mas guardião não pina a fonte do argumento como faz para `addWatchlistTicker`. |
| `App()::wlQuota` | `MercadoScreen`/`CatalogModal`/`AtividadeIAScreen` | `<QuotaSeg quota={...}>` | ✓ WIRED | 3 usos confirmados, cada um com numerador correto (`data.watchlist.length` vs `catalogSel.length`). |

### Behavioral Spot-Checks

Step 7b: executado via suíte pytest com `TestClient` real (equivalente funcional
a um `curl` contra servidor ao vivo, sem precisar subir `uvicorn` nesta sessão de
verificação): `cd server && ./.venv/bin/python -m pytest tests/test_fase13_watchlist_quota.py -q`
→ 4 passed. Cobre free logado (0 e N tickers), anônimo (200, `limit=10`) e pro
(`limit=None`). Nenhum servidor de dev foi iniciado nesta verificação (não
havia processo `uvicorn`/`vite` já rodando) — decisão consciente de não violar
a restrição de não iniciar serviços; a suíte de contrato já exercita o
handler real via `TestClient`, dando o mesmo sinal que um `curl` traria.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Endpoint de quota devolve contrato correto nos 3 cenários (free/anônimo/pro) | `pytest tests/test_fase13_watchlist_quota.py -q` | 4 passed | ✓ PASS |
| Gate fail-closed do iOS bloqueia com count local (CR-01) | mutation test (reverter `doc.watchlist.length`→`quota.count`) | guardião falha corretamente (exit 1) com o bug reintroduzido; passa (exit 0) com o fix | ✓ PASS |
| Suíte canônica completa | `bash scripts/executar.sh --testes` | 1741 passed, 1 skipped (pytest) + todos os `web/tests/*.mjs` OK | ✓ PASS |
| Build de produção do front | `cd web && npx vite build` | build concluído sem erro | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| CAP-06 | 13-01, 13-02, 13-03, 13-05 | Usuário vê número real de uso/limite | ✓ SATISFIED | Critérios 1-3, 5 verificados; 3 pontos de UI no ar. |
| CAP-12 | 13-01, 13-02, 13-05 | iOS nativo passa a checar `max_watchlist` real antes de gravar | ✓ SATISFIED | Critério 6 verificado com mutation test; publicado no web (TestFlight pendente — ver nota abaixo, não é falha da fase). |
| CAP-07 (mencionado nos frontmatters de 13-01/02, mas oficialmente rastreado como Phase 12 em REQUIREMENTS.md) | 13-02 | Sem CTA de upgrade urgente | ✓ SATISFIED (extensão consistente) | `plan.js` sem CTA (frontend mirror da correção já feita no backend na Fase 12). Não é requirement órfão: REQUIREMENTS.md já marca CAP-07 "Complete" desde a Fase 12; a Fase 13 apenas estendeu a mesma correção ao espelho do front, coerente com o próprio objetivo do plano 13-02. |

Nenhum requirement órfão encontrado — CAP-06, CAP-07 e CAP-12 aparecem tanto
nos frontmatters dos planos quanto na tabela de rastreabilidade do
`REQUIREMENTS.md`, todos com evidência de implementação real.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `web/tests/test_fase13_watchlist_quota_ios.mjs` | 58-65 | Guardião pina explicitamente a fonte de contagem (`doc.watchlist.length` vs `quota.count`) só para `addWatchlistTicker`; a mesma checagem NÃO existe para `putWatchlist`/`canGrowWatchlistTo`. Confirmado nesta verificação por mutation test independente (reverter `canGrowWatchlistTo(final.length,...)` para `canGrowWatchlistTo(quota.count,...)` — o guardião continua passando, não captura a regressão). | ⚠️ WARNING | O código ATUAL está correto (`final.length`, contagem local) — critério de sucesso 6 não falha hoje. Mas o path de `putWatchlist` (troca em massa) pode reabrir o mesmo bypass do CR-01 no futuro sem que nenhum teste acuse. O próprio `13-REVIEW.md` (WR-01) já sinalizou isso como "implicitamente coberto pelo teste 4" e sugeriu uma asserção simétrica explícita, que não foi adicionada no commit de correção `101335e` (que só corrigiu/pinou o caso de `addWatchlistTicker`). |

Nenhum debt marker (`TBD`/`FIXME`/`XXX`) encontrado nos arquivos tocados pela fase. Nenhum placeholder, `console.log`-only, ou stub visual encontrado nos 3 pontos de UI.

### Human Verification Required

Nenhum item pendente. Os dois checkpoints humanos da fase (contraste do
`T.warn` no tema claro; nome do app no App Store Connect) já foram fechados
com veredito explícito do Alex, registrado em `13-04-SUMMARY.md` — tratado
como fonte de verdade para este item conforme instrução da tarefa.

### Gaps Summary

Nenhum gap bloqueante. Um achado de severidade WARNING (não bloqueante,
não é regressão de comportamento hoje): o guardião estático de
`test_fase13_watchlist_quota_ios.mjs` não pina a fonte do argumento passado a
`canGrowWatchlistTo` dentro de `putWatchlist` da mesma forma rigorosa que pina
`canAddTicker` dentro de `addWatchlistTicker`. Mutation-testado nesta
verificação: reverter `putWatchlist` para usar `quota.count` (o mesmo bug do
CR-01, na variante de troca em massa) NÃO derruba a suíte. Sugestão para um
follow-up leve (não bloqueia a fase): adicionar ao guardião existente uma
asserção simétrica, ex. `/canGrowWatchlistTo\(final\.length,/.test(putBody) && !/canGrowWatchlistTo\(quota\.count,/.test(putBody)`.

Sobre a pendência de TestFlight (documentada nominalmente em
`13-05-SUMMARY.md`): CAP-12 está implementado, testado e publicado no
`server/web_dist`, mas só chega ao usuário do iPhone após um build novo
distribuído manualmente pelo Alex via TestFlight — restrição inerente à
distribuição de app nativo (o bundle Capacitor é embutido no binário, sem
`server.url`), corretamente identificada e registrada pelos próprios planos
da fase, não uma falha de escopo desta verificação.

---

_Verified: 2026-08-30_
_Verifier: Claude (gsd-verifier)_
