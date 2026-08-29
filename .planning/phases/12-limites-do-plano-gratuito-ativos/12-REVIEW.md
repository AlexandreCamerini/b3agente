---
phase: 12-limites-do-plano-gratuito-ativos
reviewed: 2026-08-29T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - docs/adr/010-planos-e-cap-gratuito.md
  - server/app/main.py
  - server/app/plan.py
  - server/app/store.py
  - server/tests/test_fase12_cap_analises.py
  - server/tests/test_fase12_cap_watchlist.py
  - server/tests/test_fase3_gate_plano.py
  - server/tests/test_fase5_gate_mensal.py
findings:
  critical: 1
  warning: 3
  info: 1
  total: 5
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-08-29
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the technical activation of the two free-tier commercial caps
(`PLAN_FREE.max_watchlist=10`, `PLAN_FREE.max_analyses_per_month=30`) and the
new gate added to `PUT /api/watchlist`. The in-scope diff itself is solid:
the boundary arithmetic in `can_add_ticker`/`can_analyze` was traced by hand
against fresh accounts, exactly-at-limit accounts, and grandfathered (>10)
accounts, and it holds in every case; the growth-only semantics (D-03), the
grandfather clause (D-04), the "final normalized size, not raw body size"
comparison (CAP-05), the single decision point for plan-vs-metering
precedence (C-32), and the "ledger is the only counter" contract (C-33) all
match what the two new/updated guardian test files assert, and I traced the
actual git diffs (`71a0bd3`, `cc4745d`, `9bea267`) to confirm nothing beyond
what's documented changed. `test_fase3_gate_plano.py`/`test_fase5_gate_mensal.py`
were correctly updated in place (not deleted) with explicit "reversão
deliberada" notes, per the repo's own guardrail.

However, tracing the client side of this feature (required to judge whether
the cap is actually enforced, not just whether the server-side hook fires)
surfaced a significant gap: the native iOS app's local-first watchlist writes
(`web/src/persistence.js::deviceStore`) never call the two endpoints this
phase gated. The cap this phase claims to activate does not apply to the iOS
app at all. This is flagged below as Critical despite `web/src/persistence.js`
being outside the file list provided for this review, because it directly
contradicts the phase's own stated deliverable ("bypass fechado nesta fase")
and the repository's own parity guardrail; the reviewer's job is to report
what's provable, not to stay silent because the offending file wasn't in the
diff list. Three further Warnings and one Info item cover concurrency safety,
call-site clarity, and input validation in the reviewed files.

## Critical Issues

### CR-01: Watchlist cap is fully bypassed on the native iOS app (deviceStore never calls the gated endpoints)

**File:** `web/src/persistence.js:791-798` (`deviceStore.putWatchlist`), `web/src/persistence.js:799-835` (`deviceStore.addWatchlistTicker`) — cross-referenced against `server/app/main.py:1043-1094` (this phase's gate)
**Not in the file list supplied for this review** — flagged anyway because it falsifies the phase's stated deliverable; see rationale below.

**Issue:** ADR-010's Fase 12 update (`docs/adr/010-planos-e-cap-gratuito.md:125-129`) states: *"Bypass fechado nesta fase: `PUT /api/watchlist` gravava a lista final inteira sem passar por nenhum gate ... Passou a checar o limite."* That claim is only true for the web client (`serverStore`, which is a thin wrapper around the HTTP API). The iOS app uses `deviceStore` (`persistence.js:308` onward, selected at `persistence.js:1435` via `isNative`), which is local-first for watchlist state (per the module's own header comment, `persistence.js:6-22`, and `CLAUDE.md`'s "Camada de estado do front" section).

`deviceStore.putWatchlist` (`persistence.js:791-798`) writes directly to `doc.watchlist` in `localStorage` and only schedules `_agendarSyncPrefs()` (`persistence.js:587-593`), which fires `api.pushRegisterToken("", _pushPrefsLocais())` — a push-notification-preferences sync, not a watchlist upload. `deviceStore.addWatchlistTicker` (`persistence.js:799-835`) does the same: it calls `api.validateTicker`/`api.getQuotes` only to confirm the ticker *exists* on the exchange, then writes to `doc.watchlist` locally with no call to any endpoint that could apply `plan.can_add_ticker`. There is no `api.putWatchlist` call anywhere in the file (confirmed by grep) — the watchlist tickers never round-trip to the server at all.

Contrast this with the *other* cap this same phase activates: `max_analyses_per_month`. That one is correctly enforced cross-platform, because AI analyses always require a real server call (`POST /api/analyze`, `POST /api/technical/analyze`), so `_gate_analise` runs regardless of which store the client uses — and `deviceStore.analisesNoMes()` (`persistence.js:1148-1152`) even documents this explicitly ("o aparelho NÃO mantém contador próprio ... lê o MESMO monthUsed do ledger do servidor"). No equivalent exists for the watchlist cap; there was no reason it *couldn't* — `deviceStore` already makes network exceptions for server-authoritative state elsewhere in the same file (buy/sell/putPosition delegate straight to `api.*`, see `persistence.js:256` and `1316`+).

This also violates the repository's own stated invariant (`CLAUDE.md`, "Paridade obrigatória": *"deviceStore ↔ serverStore em web/src/persistence.js (método/campo novo entra nos DOIS)"*) — the watchlist cap is new business behavior for `putWatchlist`/`addWatchlistTicker` that entered only one of the two stores.

Practical effect: an iOS user can add an unbounded number of watchlist tickers, completely undermining the free-tier cap this phase is supposed to deliver. Since the product is explicitly "Web/PWA + app iOS nativo (mesmo bundle via Capacitor)" and the iOS TestFlight/App Store surface is a primary distribution channel, this is not a minor edge case.

**Fix:** Either (a) make `deviceStore.putWatchlist`/`addWatchlistTicker` call the server (`api.putWatchlist`/`api.validateTicker` result) as the source of truth for the final list the same way `analisesNoMes()` already does for the analyses cap, and adopt the server's response/rejection instead of writing local state unconditionally, or (b) if network-optional local-first behavior is intentional for the watchlist domain, port `plan.can_add_ticker`'s boundary check into `deviceStore` itself (reading `max_watchlist` from a cached `/api/ai/quota`-like endpoint, mirroring the existing `analisesNoMes()` pattern) so the cap is at least approximately enforced offline. Whichever direction is chosen, add a `deviceStore` counterpart test to `test_fase12_cap_watchlist.py`'s web-only coverage, or an equivalent `web/tests/*.mjs` case, so this doesn't silently regress again.

## Warnings

### WR-01: Read-modify-write race on watchlist mutation endpoints (no lock, unlike cash/positions)

**File:** `server/app/main.py:1043-1058` (`PUT /api/watchlist`), `server/app/main.py:1063-1094` (`POST /api/watchlist/add`)
**Issue:** Both endpoints read the current watchlist, decide via `plan.can_add_ticker`, then write — classic check-then-act. `store.py` documents (`store.py:12-24`) that exactly this class of bug ("lost update / double-spend") is why `store.ORDER_LOCK` exists for `cash`/`positions`, guarding `/api/buy` and `/api/sell` (`main.py:1902`, `main.py:2000`). No equivalent lock guards the watchlist read-modify-write. For `PUT /api/watchlist` this can't push a user's stored list *above* the plan cap (it's a full-replace write, so the race just picks a winner, not a union), but for `POST /api/watchlist/add` two concurrent adds of different tickers can silently lose one of the two additions (last writer's `wl + [t]` overwrites the other), independent of the plan gate.
**Fix:** Reuse `store.ORDER_LOCK` (or a dedicated watchlist lock) around the read-check-write sequence in both endpoints, the same pattern already established for buy/sell:
```python
with store.ORDER_LOCK:
    novos = body.get("tickers") or []
    final = store.normalize_watchlist(_conn, novos, user_id=scope)
    atual = store.get(_conn, "watchlist", user_id=scope)
    if len(final) > len(atual):
        allowed, reason = plan.can_add_ticker(len(final) - 1, plan=_plano_do_escopo(scope))
        if not allowed:
            raise HTTPException(402, reason)
    store.set_watchlist(_conn, novos, user_id=scope)
```

### WR-02: `can_add_ticker(len(final) - 1, ...)` reuses single-item semantics for a bulk endpoint via an unexplained "-1"

**File:** `server/app/main.py:1054`
**Issue:** `plan.can_add_ticker(current_count, plan)` is documented (`plan.py:75-82`) as "how many items exist *before* this one addition." `PUT /api/watchlist` is a bulk replace, not a single addition, so `len(final) - 1` is passed purely to make the `current_count >= limit` comparison land on "block iff `final size > limit`" — it has no meaning as an actual pre-add count when the bulk delta is >1 item. The current call is correct (verified against 9 boundary/grandfather test cases), but it's correct by arithmetic coincidence, not by the function's stated contract; a future change to `can_add_ticker`'s comparison operator (e.g. `>` instead of `>=`, or a rewrite that also validates `current_count` is non-negative or sane) would silently break this call site without touching it.
**Fix:** Give `plan.py` a second, honestly-named hook for the bulk case, e.g.:
```python
def can_grow_watchlist_to(final_size: int, plan=None) -> tuple:
    """Bulk-replace variant of can_add_ticker: block iff the FINAL size
    exceeds the plan limit. Used by PUT /api/watchlist, which replaces the
    whole list rather than adding one item at a time."""
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_watchlist")
    if limit is not None and final_size > limit:
        return (False, f"Voce atingiu o limite de {limit} ativos do plano {plan['id']}.")
    return (True, None)
```
and call it as `plan.can_grow_watchlist_to(len(final), plan=_plano_do_escopo(scope))`. Note the two static guardian tests in `test_fase12_cap_watchlist.py` (`test_plan_can_add_ticker_aparece_exatamente_duas_vezes_no_main`, `test_put_watchlist_referencia_can_add_ticker_nao_e_mais_set_watchlist_puro`) would need to be updated to reference the new hook name if this is adopted.

### WR-03: No type validation on `body.get("tickers")` before it reaches `normalize_watchlist`

**File:** `server/app/main.py:1050` (`novos = body.get("tickers") or []`), `server/app/store.py:417-443` (`normalize_watchlist`)
**Issue:** `body.get("tickers") or []` only guards against `None`/missing/empty — any other truthy non-list value (a string, a dict, a bool) passes through unchanged into `normalize_watchlist`, which does `for t in tickers`. A JSON string body like `{"tickers": "PETR4"}` iterates per-character (each 1-char "ticker" fails the catalog membership check, so `final` silently becomes `[]`, wiping the watchlist to empty with a 200 response and no error). A non-iterable truthy value (e.g. `{"tickers": true}`) raises an uncaught `TypeError` inside `normalize_watchlist`, which is caught only by the blanket 500 handler (`main.py:88-93`), returning an opaque `"TypeError: 'bool' object is not iterable"` to the client instead of a clean 400. This predates Phase 12 (the same coercion existed in the old direct `store.set_watchlist` call), but this phase turned this exact code path into the enforcement point for a paid-tier gate, which raises the bar for input hygiene here.
**Fix:** Validate the shape before normalizing:
```python
novos = body.get("tickers")
if novos is not None and not isinstance(novos, list):
    raise HTTPException(400, "tickers deve ser uma lista de codigos.")
novos = novos or []
```

## Info

### IN-01: `normalize_watchlist` filters against uppercase catalog but doesn't normalize case before matching, producing inconsistent internal ordering (harmless to cap correctness)

**File:** `server/app/store.py:417-443`
**Issue:** `chosen = [t for t in tickers if (t or "").upper() in allowed]` keeps `t` in its original case, but the first pass that preserves catalog ordering (`for t in ordered: if t in chosen ...`) does a case-sensitive comparison against `ordered` (always uppercase). A lowercase or mixed-case input ticker that IS valid will fail this first-pass match and fall through to the second "defensive" loop, which does uppercase it before adding. The resulting *set* and *count* are unaffected (confirmed: this cannot change `len(final)`, so it doesn't affect the Phase 12 cap check), but the resulting *order* silently differs from what a same-ticker-different-case request would otherwise produce, which is a minor footgun for any future code that assumes catalog order is stable regardless of input casing. Pre-existing (unchanged by the `cc4745d` extraction, confirmed via diff), not introduced by this phase.
**Fix:** Normalize case once, up front: `chosen = sorted({(t or "").upper() for t in tickers if (t or "").upper() in allowed}, key=ordered.index)` or equivalent, so a single canonical uppercase form flows through both passes.

---

_Reviewed: 2026-08-29_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
