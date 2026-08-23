---
phase: 03-corre-o-cr-tico-alto
plan: 02
subsystem: api
tags: [fastapi, candle-provider, error-handling, observability, react, admin-portal]

requires:
  - phase: 03-corre-o-cr-tico-alto
    provides: "REPORT-01 achados C-12/C-36 e as interfaces já corretas (get_quotes plural, snapshot(), validation_outcome) que este plano alinha/expõe"
provides:
  - "candle_provider.get_quote (singular) trata falha do provedor no mesmo padrão de get_quotes (plural) — nunca propaga exceção crua"
  - "web-admin: card 'Orçamento brapi (ADR-008)' mostra vazios, taxa de falha e alerta do provedor primário, separados de erros"
affects: [candle_provider, main-buy-sell-routes, watchlist, admin-observability]

tech-stack:
  added: []
  patterns:
    - "try/except por chamada externa na fronteira do provedor: QuoteUnavailable relançada intacta (contrato 503), qualquer outra Exception vira payload {price:None, error: genérico fixo}, nunca str(e) na resposta"
    - "leitura defensiva de métricas no front admin: `?? '—'` e `typeof === 'number'` antes de formatar, nunca renderiza 0.0% como estado inventado"

key-files:
  created:
    - server/tests/test_fase3_get_quote_erro_limpo.py
    - web/tests/test_fase3_custos_falha_brapi.mjs
  modified:
    - server/app/candle_provider.py
    - web-admin/src/App.jsx

key-decisions:
  - "Regra 3 (blocking) aplicada em Task 2: web-admin e web careciam de node_modules neste worktree isolado; symlink temporário para o node_modules já instalado no clone principal (lockfiles idênticos, confirmado por diff) só para rodar `npx vite build` e as suítes .mjs — removido antes de cada commit, não fica no working tree final."
  - "Teste de rota (Task 1, item d) usa TestClient + B3_DB_PATH temporário + reimport de app.main, padrão já estabelecido em test_ciclo_imediato_apos_carteira.py."
  - "O guardião do painel admin (Task 2) mira a EXPRESSÃO de código que somaria erros+vazios (`candles.erros + ... candles.vazios`), não o texto do rótulo — o Copywriting Contract exige que o rótulo da taxa de falha CITE 'erros + vazios' em prosa, o que não é fusão no código."

patterns-established:
  - "Fronteira de provedor externo: toda chamada a `yahoo.get_quote`/similar na função pública precisa do par except QuoteUnavailable: raise / except Exception: payload genérico — não é opcional, é o contrato desde get_quotes."

requirements-completed: [FIX-C12, FIX-C36]

duration: 9min
completed: 2026-08-18
---

# Phase 3 Plan 02: get_quote sem vazamento + painel de custos com vazios/taxa de falha Summary

**`candle_provider.get_quote` (singular) alinhado ao try/except já usado por `get_quotes` (plural) — erro de provedor vira `price: None` genérico em vez de HTTP 500 com URL/`crumb` vazando; painel admin "Orçamento brapi" ganha 3 linhas (vazios, taxa de falha, alerta) separadas de `erros`.**

## Performance

- **Duration:** 9 min (20:23 → 20:31, commits) + leitura/verificação prévia
- **Started:** 2026-08-18T23:15:00Z (aprox., leitura de contexto)
- **Completed:** 2026-08-18T23:32:00Z
- **Tasks:** 2/2
- **Files modified:** 4 (2 criados, 2 modificados)

## Accomplishments
- `POST /api/buy`/`POST /api/sell` com ticker inexistente agora devolvem 502 `"Sem cotacao para X"` de forma confiável — o crash cru do Yahoo (URL + `crumb`) que gerava HTTP 500 em produção (C-12) não pode mais escapar de `get_quote`.
- `QuoteUnavailable` continua sendo relançada intacta nos dois ramos (brapi-com-fallback e provedor-não-brapi) — o contrato de 503 dos chamadores não regrediu.
- O card "Orçamento brapi (ADR-008)" do portal admin agora mostra `vazios` (200 sem vela), `taxaFalha` e `alerta` do provedor primário — o incidente de 31/07/2026 (HTTP 200, zero velas, 2h de pregão) deixaria de ler "Erros: 0" (C-36).

## Task Commits

1. **Task 1: get_quote (singular) devolve preço nulo em vez de propagar exceção crua do provedor** - `05161ef` (fix)
2. **Task 2: Painel de custos do portal admin passa a mostrar vazios, taxa de falha e alerta do provedor** - `e0e88dd` (feat)

**Plan metadata:** (commit de fechamento feito pelo orquestrador após merge — este executor não grava STATE.md/ROADMAP.md)

## Files Created/Modified
- `server/app/candle_provider.py` - `get_quote` (singular) envolve as duas chamadas a `yahoo.get_quote` em try/except; `QuoteUnavailable` relançada, qualquer outra exceção vira `{"t", "price": None, "change": 0, "error": "sem cotação (falha do provedor de dados)"}`, detalhe logado via `print("[candle_provider] ...")`
- `server/tests/test_fase3_get_quote_erro_limpo.py` - guardião novo: 5 testes (ramo yahoo puro, ramo brapi-com-fallback, contrato QuoteUnavailable preservado, rota `/api/buy` via TestClient devolvendo 502 limpo, `validation_outcome` classificando como `not_found`)
- `web-admin/src/App.jsx` - 3 `Kv` novas no card "Orçamento brapi (ADR-008)", logo após "Erros (janela 3 dias)": "Respostas vazias (200 sem vela, janela 3 dias)", "Taxa de falha (erros + vazios / requisições, 3 dias)", "Alerta do provedor primário" — leitura defensiva (`?? "—"`, `typeof === "number"`)
- `web/tests/test_fase3_custos_falha_brapi.mjs` - guardião estático novo: rótulos literais, leitura dos 4 campos do payload, ausência de fusão `erros`+`vazios` no código, coexistência com a linha antiga, tons `negative`/`positive`

## Decisions Made
- Nenhuma alteração em `server/app/main.py`, `server/app/yahoo.py` ou `server/app/tickers.py` — confirmado pelo diff (a mensagem `"Sem cotacao para " + t` já existia; só passou a ser alcançada).
- Ver `key-decisions` no frontmatter para o racional do symlink temporário de `node_modules` e do ajuste de regex do guardião de front.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Ajuste da regex do guardião front — falso positivo no próprio rótulo literal exigido**
- **Found during:** Task 2 (escrita do guardião `test_fase3_custos_falha_brapi.mjs`)
- **Issue:** A regex sugerida no plano (`erros\s*\+\s*.*vazios`) para travar "vazios nunca somado a erros" batia também no rótulo LITERAL exigido pelo Copywriting Contract ("Taxa de falha (erros + vazios / requisições, 3 dias)"), que precisa citar "erros + vazios" em prosa — falso positivo, o teste falhava mesmo com o código correto.
- **Fix:** Regex reescrita para mirar a expressão de código (`candles\.erros\s*\+\s*[^;\n]*candles\.vazios` e o inverso) em vez de proximidade textual solta — continua travando fusão real dos dois contadores, sem reagir ao rótulo em prosa.
- **Files modified:** web/tests/test_fase3_custos_falha_brapi.mjs
- **Verification:** `node web/tests/test_fase3_custos_falha_brapi.mjs` → "TODOS OS TESTES PASSARAM"
- **Committed in:** e0e88dd (Task 2 commit)

**2. [Rule 3 - Blocking] node_modules ausente no worktree isolado (web/ e web-admin/)**
- **Found during:** Task 2 (verificação `npx vite build`) e verificação da suíte canônica
- **Issue:** Este worktree (`.claude/worktrees/agent-aab3fd05d5776cc4a`) não tinha `node_modules` instalado em `web/` nem `web-admin/` — `npx vite build` e os testes `.mjs` falhavam com `ERR_MODULE_NOT_FOUND`, não por erro no código.
- **Fix:** `diff` confirmou que `package-lock.json` de `web/` e `web-admin/` é BYTE-IDÊNTICO ao do clone principal; criado symlink temporário para o `node_modules` já instalado lá, só para rodar build/testes, removido antes de cada `git add`/commit (não entra no histórico nem fica no working tree final).
- **Files modified:** nenhum arquivo versionado (symlinks removidos)
- **Verification:** `cd web-admin && npx vite build` → build OK; `bash scripts/executar.sh --testes` → RC=0, zero `[X]`
- **Committed in:** não aplicável (nenhuma mudança versionada)

---

**Total deviations:** 2 auto-fixed (ambas Rule 3 — bloqueios de ambiente/teste, sem mudança de escopo)
**Impact on plan:** Nenhum impacto no código de produção. Um ajuste de regex do guardião (mais preciso, mesma garantia) e um workaround de ambiente de verificação (sem artefato versionado).

## Issues Encountered
- Primeira versão de `test_get_quote_unavailable_continua_relancada` (Task 1) fez chamada de rede real ao Yahoo por engano: sem `B3_CANDLE_FALLBACK` explícito, `fallback_name()` assume `"yahoo"` como backup implícito (ADR-008) mesmo com `BRAPI_TOKEN` ausente — corrigido setando `B3_CANDLE_FALLBACK=""` explicitamente no teste para desligar o backup e exercitar o caminho "nenhum backup configurado" que o teste pretendia cobrir. Sem impacto no código de produção, só na fixture do teste.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- C-12 e C-36 fechados; próximos planos da fase 3 (03-01, 03-03..03-06) não dependem destes arquivos (`server/app/candle_provider.py`, `web-admin/src/App.jsx` não aparecem nos `files_modified` dos planos irmãos conhecidos).
- Verificação humana pendente (fica para `/gsd:verify-phase`, conforme a seção `<verification>` do plano): com o servidor local no ar, `curl -X POST localhost:8787/api/buy -d '{"t":"XXXXX9","qty":10}'` deve devolver 502 com `Sem cotacao para XXXXX9` sem trecho de URL; a aba Custos do portal deve mostrar as três linhas novas.

---
*Phase: 03-corre-o-cr-tico-alto*
*Completed: 2026-08-18*

## Self-Check: PASSED

- FOUND: server/app/candle_provider.py
- FOUND: server/tests/test_fase3_get_quote_erro_limpo.py
- FOUND: web-admin/src/App.jsx
- FOUND: web/tests/test_fase3_custos_falha_brapi.mjs
- FOUND: 05161ef (fix, Task 1)
- FOUND: e0e88dd (feat, Task 2)
