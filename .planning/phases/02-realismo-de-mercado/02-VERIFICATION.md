---
phase: 02-realismo-de-mercado
verified: 2026-08-19T10:11:38Z
status: passed
score: 5/5 success criteria verified; 4/4 requirements (MERC-01..04) complete
overrides_applied: 0
---

# Phase 2: Realismo de Mercado — Verification Report

**Phase Goal:** Usuário vê o status real do pregão a qualquer momento (mesmo
antes de logar) e pode colocar ordens fora do horário sem perder controle
sobre elas — preço, caixa e cancelamento ficam claros enquanto a ordem
aguarda a abertura seguinte.

**Verified:** 2026-08-19T10:11:38Z
**Status:** passed
**Re-verification:** No — initial verification

## Method

This verification did not trust SUMMARY.md claims. For every load-bearing
claim, the actual source was read and, where possible, executed:

- Read all 7 PLAN.md/SUMMARY.md pairs (02-01..02-07) and 02-CONTEXT.md.
- Read `server/app/pending_orders.py` in full (312 lines) — confirmed
  `criar_compra`/`criar_venda`/`cancelar`/`executar_pendentes` implement
  D-01/D-02/D-05/D-06/D-07 exactly as specified, that execution always uses
  the price from `price_getter` (never `precoReferencia`), and that the
  quote is fetched outside `ORDER_LOCK`.
- Read the `/api/buy`, `/api/sell`, `/api/market/status`,
  `DELETE /api/orders/pending/{id}` handlers directly in `server/app/main.py`
  — confirmed `store.ORDER_LOCK` wraps the critical section of BOTH the
  immediate-order path and is the identical object aliased by
  `pending_orders.ORDER_LOCK`.
- Read `WelcomeAuthScreen`, `MarketStatusBadge`, `Topbar`, and
  `HistoricoScreen` directly in `web/src/App.jsx` — confirmed the badge
  renders pre-login (D-08) and post-login, and the "Pendentes" section /
  two-step cancel flow exist and are wired to `ctx.data.pendingOrders` and
  `A.cancelPendingOrder`.
- Read `_pet_resumo_evolucao` — confirmed `patrimonio = cash + reservado +
  pos_val`.
- Ran `grep -rn "RLock()" server/app/` myself — exactly 1 hit (`store.py`),
  confirming no second process lock was introduced anywhere in the backend.
- Ran the full canonical suite myself: `bash scripts/executar.sh --testes`
  → exit 0, **1100 backend tests passed**, **83/83 web `.mjs` files `[OK]`**.
- Ran `cd web && npx vite build` myself → exit 0, clean Vite/Rollup/PWA
  build (this had been a known blocker in earlier plans' worktrees; it is
  resolved in the current merged state).
- Read `qa/48-fase2-verificacao-e2e-ordens-pendentes.md` in full — it is a
  genuine live exercise against a real `uvicorn` process and disposable
  SQLite DB (not `TestClient`), with raw curl output and a cash-conservation
  table (`cash + caixaReservado` = 10000.0 at every step except execution,
  where it becomes position value, exactly as the plan anticipates).
- Confirmed via `git log --oneline` that all 7 plans (02-01..02-07) are
  actually merged into the current branch history (`c07373c` merge:
  plan 02-07 is HEAD), not just claimed in SUMMARY narrative.
- Cross-checked `.planning/REQUIREMENTS.md` — MERC-01..04 all marked
  `[x]`/`Complete`.

## Goal Achievement — Success Criteria (verbatim from ROADMAP.md)

| # | Success Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Usuário não-logado vê o status real do mercado, calculado por `pregao.py`, na tela de entrada | ✓ VERIFIED | `GET /api/market/status` (`server/app/main.py:874`) has no `current_scope`/`require_user` param, computes `aberto`/`diaDePregao` directly from `pregao.in_market_hours()`/`pregao.is_trading_day()`, and is in `_GATE_ALLOWLIST_PREFIXES` (`main.py:323`). `WelcomeAuthScreen` renders `<MarketStatusBadge mercado={ctx.mercado} cp={ctx.cp} />` (`App.jsx:658`) below the disclaimer, before the auth form, reading only `ctx.mercado`/`ctx.cp` (never `ctx.data`). Live-exercised in qa/48 §4: real curl without `Authorization` returned the 6 expected keys, `aberto:false` matching real clock time. |
| 2 | Ordem fora do horário fica "pendente" (não rejeitada, não executa ao preço do momento) | ✓ VERIFIED | `/api/buy`/`/api/sell` branch on `pregao.in_market_hours()` (`main.py:1639`, `:1688`); when false and `scope` exists, call `pending_orders.criar_compra`/`criar_venda`, returning `pendente: True`, `priceUsed: None`. Live-exercised in qa/48 §6: `POST /api/buy` with market closed returned `pendente: true`, `priceUsed: null`, `history` unchanged. |
| 3 | Caixa da ordem pendente reservado/indisponível ao pedido, debitado do saldo real só na execução | ✓ VERIFIED | `pending_orders.criar_compra` debits `cash` immediately inside `ORDER_LOCK` (`pending_orders.py:103-129`); `store.public_state` exposes `caixaReservado` as a derived sum (`store.py:545,832`). `_pet_resumo_evolucao` (main.py:1988-2017) sums `cash + reservado + pos_val` so the assistant's stated net worth doesn't shrink. Live-exercised in qa/48 §6/§10: `cash 5740.0 + caixaReservado 4260.0 = 10000.0` at creation. |
| 4 | Ordem pendente executa automaticamente ao preço de abertura do pregão seguinte | ✓ VERIFIED | `agent.scheduler_loop` (agent.py:1134) calls `store.scopes_com_pendentes` (not `list_server_users`) inside the `not kill_switch_on() and in_market_hours()` gate, batches one quote fetch per distinct ticker, and calls `pending_orders.executar_pendentes` per scope. `executar_pendentes` (pending_orders.py:211-312) applies the injected `price_getter` result via `store.buy`/`store.sell`, never `precoReferencia`. Live-exercised in qa/48 §8: forced scheduler pass turned the pending order into a `PETR4 100@42.6` position with `history` entry `origem: "pendente"`. |
| 5 | Usuário pode cancelar uma ordem pendente a qualquer momento, liberando o caixa reservado | ✓ VERIFIED | `DELETE /api/orders/pending/{order_id}` (main.py:1727) calls `pending_orders.cancelar`, scoped to the caller's `user_id` (IDOR-safe, 404 on other-account/nonexistent id). Front: `HistoricoScreen` (App.jsx:3693-3792) renders a two-step inline confirmation ("Manter ordem" / "Confirmar cancelamento") gated by local `confirmando` state, calling `A.cancelPendingOrder` → `store.cancelPendingOrder` → adopts server `public_state`. Live-exercised in qa/48 §7: `cash` returned to exactly `10000.0`, `caixaReservado` to `0`. |

**Score:** 5/5 success criteria verified.

## Requirements Coverage

| Requirement | Source Plan(s) | Status | Evidence |
|---|---|---|---|
| MERC-01 | 02-02, 02-04, 02-05, 02-07 | ✓ SATISFIED | Public route + pre/post-login badge, live-exercised and human-approved (qa/48, 02-07 checkpoint) |
| MERC-02 | 02-01, 02-02, 02-03, 02-06 | ✓ SATISFIED | Pending-order engine, route branch, scheduler auto-execution, UI disclosure |
| MERC-03 | 02-01, 02-02, 02-04, 02-05, 02-06 | ✓ SATISFIED | Cash/position reservation at request time, exposed in `public_state`/`pet:evolucao`/UI |
| MERC-04 | 02-01, 02-02, 02-04, 02-06 | ✓ SATISFIED | Scoped DELETE route, immediate refund, two-step UI confirmation |

`.planning/REQUIREMENTS.md` marks all four `[x]`/`Complete`, consistent with code evidence above — no orphaned or contradicted requirements found.

## Key Artifacts (Level 1-3: exists, substantive, wired)

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `server/app/pending_orders.py` | Deterministic pending-order engine | ✓ VERIFIED | 312 lines, read in full; `criar_compra`/`criar_venda`/`cancelar`/`executar_pendentes` all present and substantive, no stubs |
| `server/app/store.py` (`ORDER_LOCK`, `caixa_reservado`, `scopes_com_pendentes`, `SECTIONS`) | Single process lock + derived reserved-cash sum + scope discovery | ✓ VERIFIED | `ORDER_LOCK = threading.RLock()` at line 25, only RLock in `server/app/` (`grep -rn "RLock()" server/app/` = 1 hit); `caixa_reservado` at line 545; `pendingOrders` in `SECTIONS`/`USER_SECTIONS` |
| `server/app/main.py` (`/api/market/status`, buy/sell pending branch, DELETE route) | Public status route + pending order routes + shared lock | ✓ VERIFIED | Read directly; `with store.ORDER_LOCK:` at lines 1646 and 1693 wraps checkout+debit in both immediate paths; quote fetch is outside the lock in both handlers |
| `server/app/agent.py` (scheduler hook, `ordensPendentes` counters) | Auto-execution + observability | ✓ VERIFIED | `scopes_com_pendentes`/`executar_pendentes` wired inside `scheduler_loop`; `ordensPendentes` key present in `status_snapshot` |
| `web/src/api.js`, `web/src/persistence.js` (both stores) | HTTP client + dual-store parity | ✓ VERIFIED | `test_ordens_pendentes_client.mjs` guardian asserts `hits >= 2` (both stores) for `cancelPendingOrder`/`marketStatus`/`pendingOrders`/`caixaReservado`; passes in canonical suite |
| `web/src/finance.js` (`portfolioMetrics`) | Reserved-cash-aware net worth | ✓ VERIFIED | 4th optional `reservado` param, `patr = c + r + posVal`, backward-compatible with 3-arg call sites |
| `web/src/App.jsx` (`MarketStatusBadge`, `WelcomeAuthScreen`, `Topbar`, `HistoricoScreen`) | Pre/post-login badge, pending section, two-step cancel | ✓ VERIFIED | Read directly; badge rendered at both call sites (lines 658, 777); Pendentes section conditional on `length > 0`, `T.warn`-only pill, cash-conservation copy |
| `qa/48-fase2-verificacao-e2e-ordens-pendentes.md` | Live E2E exercise record | ✓ VERIFIED | Genuine curl output against real uvicorn + disposable SQLite, not TestClient; cash-conservation table checked |

## Data-Flow Trace (Level 4)

`ctx.mercado` (App.jsx root state) → `store.marketStatus()` → `api.marketStatus()` → `GET /api/market/status` → `pregao.in_market_hours()`/`is_trading_day()`. No hardcoded/static fallback found; failure path sets `{erro: true}` and renders the "indisponível" (`T.warn`) state, never fabricating "aberto"/"fechado" — confirmed by reading `MarketStatusBadge` (`if (!mercado) return null`) and the copy guardian tests (`mercadoFechado()` without argument never contains a fabricated time).

`data.pendingOrders`/`data.caixaReservado` → `store.public_state` (backend, real KV read) → `_adotarCarteiraDoServidor` (deviceStore) / raw passthrough (serverStore) → `HistoricoScreen`. Confirmed flowing with real numbers in qa/48 (not empty arrays/zeros by default — populated when a pending order genuinely exists).

Status: ✓ FLOWING (both traces).

## Anti-Patterns Scan

Searched `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` across all phase-modified files (`pending_orders.py`, `store.py`, `main.py`, `agent.py`, `defaults.py`, `api.js`, `persistence.js`, `finance.js`, `App.jsx`, `copy.js`). No genuine debt markers found — all `TODO`-looking hits are the Portuguese word "TODOS"/"TODO" (all/every), not markers. No blockers.

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Backend unit suite for this phase | `pytest tests/test_ordens_pendentes*.py` | 66 passed | ✓ PASS |
| Full canonical suite | `bash scripts/executar.sh --testes` | 1100 backend passed, 83/83 web `[OK]`, exit 0 | ✓ PASS |
| Front build | `cd web && npx vite build` | exit 0, clean PWA build | ✓ PASS |
| Single process lock invariant | `grep -rn "RLock()" server/app/` | 1 hit (`store.py`) | ✓ PASS |
| Live E2E cash conservation | qa/48 §10 table | `cash + caixaReservado` = 10000.0 at every non-execution step | ✓ PASS |

## Human Verification

**None required to reach `passed`.** Phase 02-07's own plan included a blocking `checkpoint:human-verify` task (Task 2) that already ran: Alexandre walked an 8-step visual roteiro against the real running app and responded **"aprovado"** for steps 1-6 and 8 (pre-login badge, Topbar badge, PENDENTE pill in modals, Pendentes section, two-step cancel, absence of promissory/inconsistent language).

### Residual known limitation (informational, non-blocking)

**Item:** Step 7 of the 02-07 roteiro — repeating the visual verification on iPhone/TestFlight (`deviceStore` code path) — was **not performed live**.

**Why this is not a gap:** The 02-07 PLAN.md explicitly permits declaring this step as a known limitation rather than a silent omission, and Alexandre explicitly confirmed (recorded in 02-07-SUMMARY.md) that he would not test it now — this is a plan-permitted, developer-acknowledged deferral, not an unperformed verification task that this report is surfacing for the first time. Static coverage exists: `deviceStore`/`serverStore` parity is enforced by `test_ordens_pendentes_client.mjs`'s automated guardian (`hits >= 2` per method/field), and a real parity bug was found and fixed during 02-06 (`deviceStore.buy`/`sell` not propagating `r.pendente`) — evidence the guardian is effective, not just decorative.

**Recommendation:** Next TestFlight build should exercise the pending-order flow on-device first, per 02-07-SUMMARY's own "Next Phase Readiness" note — this is carried forward as a backlog item, not a phase-blocking gap.

## Gaps Summary

None. All 5 ROADMAP success criteria verified directly against source code and a genuine live exercise (not SUMMARY narrative alone). All 4 requirements (MERC-01..04) satisfied and marked complete in REQUIREMENTS.md. The single-lock concurrency invariant (`store.ORDER_LOCK` shared by the immediate-order path and the pending-order engine/scheduler) — flagged as a real risk during planning (02-01/02-02) — was independently confirmed present and correctly scoped in the merged code, not just asserted in a SUMMARY. Canonical test suite (1100 backend + 83 web) and `npx vite build` both pass cleanly when run directly by this verifier. No debt markers, no stubs, no orphaned requirements, no unresolved must-haves.

---

_Verified: 2026-08-19T10:11:38Z_
_Verifier: Claude (gsd-verifier)_
