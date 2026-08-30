---
phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios
reviewed: 2026-08-30T23:54:41Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - docs/MEDICAO-Mydata-2026-08-27.md
  - server/app/main.py
  - server/app/mydata_budget.py
  - server/tests/test_fase13_watchlist_quota.py
  - web/src/App.jsx
  - web/src/api.js
  - web/src/persistence.js
  - web/src/plan.js
  - web/src/version.js
  - web/tests/test_fase13_contadores_ui.mjs
  - web/tests/test_fase13_watchlist_quota_ios.mjs
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-08-30T23:54:41Z
**Depth:** standard
**Files Reviewed:** 11 (scoped to Phase 13's actual diff: `GET /api/watchlist/quota`, `watchlistQuota()` in both stores, the deviceStore fail-closed gate, `QuotaSeg` + its 3 call sites, `plan.js` CTA removal, and the two textual cleanups — not the large pre-existing surface of `App.jsx`/`persistence.js`/`main.py`)
**Status:** issues_found

## Summary

Reviewed the code Phase 13 actually added or changed, cross-referencing each plan's SUMMARY.md against the real diff (`git show` on the task commits) rather than trusting the SUMMARY's own claims.

`GET /api/watchlist/quota` (server/app/main.py:1277-1295) is a clean, correctly-scoped read-only endpoint; its contract test (`test_fase13_watchlist_quota.py`) locks the 3-field shape against `plan.py`, not literals. The BolsIA→Boris+ text cleanup is exact and doesn't touch the protected `BOLSAI_API_KEY`/`bolsai` provider identifier. `QuotaSeg` (App.jsx:374-382) and its 3 call sites correctly source `limit`/`planId` from the live endpoint and `count` from local state, never mixing the two — the UI layer (13-03) is sound.

The enforcement layer (13-02) has one real bug: `deviceStore.addWatchlistTicker`'s fail-closed gate (persistence.js:885) feeds the *server's* watchlist count into the local cap check, not the device's own count. Because iOS watchlist state is documented and architected as local-only (persistence.js:1-14, never pushed to the server for a logged-in or anonymous device), that server count is a structurally unrelated number — the gate that this phase exists to close (CR-01, 12-REVIEW.md) doesn't actually enforce anything in the most common "quick add one ticker" flow. The sibling method `putWatchlist` gets this right (compares local `final.length`), which makes the asymmetry easy to miss in review and easy to prove as a bug rather than a design choice.

## Critical Issues

### CR-01: `addWatchlistTicker` fail-closed gate compares against the wrong watchlist — CAP-12 does not actually enforce the cap on iOS

**File:** `web/src/persistence.js:873-886`
**Issue:**
```js
if (!doc.watchlist.includes(info.t)) {
  let quota;
  try {
    quota = await api.watchlistQuota();
  } catch {
    throw new Error("Não foi possível confirmar o limite do plano agora. Tente de novo.");
  }
  if (!quota || typeof quota.count !== "number") {
    throw new Error("Não foi possível confirmar o limite do plano agora. Tente de novo.");
  }
  const r = canAddTicker(quota.count, { id: quota.planId || "free", maxWatchlist: quota.limit });
  if (!r.ok) throw new Error(r.reason);
}
```
`quota.count` comes from `GET /api/watchlist/quota`, which returns `len(store.get(_conn, "watchlist", user_id=scope))` — the **server-side** watchlist for that scope (`server/app/main.py:1293-1295`). Per the file's own header comment (`persistence.js:5-6`, "watchlist... ficam no PRÓPRIO APARELHO (localStorage do WKWebView)") and confirmed by tracing every call site of `api.putWatchlist`/`api.addWatchlistTicker`: **the deviceStore never writes the device's watchlist to the server.** `_agendarSyncPrefs()` (called after every local watchlist write) only calls `POST /api/push/register-token`, which persists push *preferences* (`push.set_prefs`), not `store.watchlist` (`server/app/main.py:2879-2905`).

Consequences:
- **Logged-in iOS user, account only ever used on the phone:** server-side `watchlist` for that account stays frozen at whatever it was at registration (6 default tickers, `defaults.default_state()`) or whatever the user last did on the web app with the same account. `quota.count` will almost never approach the real device count, so `canAddTicker(quota.count, ...)` keeps returning `{ ok: true }` long after the device has exceeded the 10-ticker cap.
- **Anonymous iOS device:** `api.watchlistQuota()` is sent without an Authorization header, so it hits the server's single shared anonymous bucket (`user_id=None`, "balde anônimo") — a count with zero relationship to any specific device's local list.

The sibling method one block above, `putWatchlist` (persistence.js:800-829), does this correctly: it gates on `final.length` (the **local**, device-computed size) against `quota.limit`, using the endpoint only for the plan's numeric ceiling, never for the current count. `addWatchlistTicker` should do the same.

This directly undermines the phase's own stated deliverable — 13-02-SUMMARY.md claims "CR-01 (12-REVIEW.md) fechado: iOS nativo agora respeita `max_watchlist` real antes de gravar, com fail-closed comprovado por guardião estático" — but the guardian test only checks call *ordering* and that the `catch` throws (see WR-01 below), never which count value reaches `canAddTicker`. The bypass this phase was built to close is still open for the single-ticker "quick add" path, which is the primary way tickers get added in the app (App.jsx:7145, 7375, 7791, 8013 all route through `addWatchlistTicker`).

**Fix:**
```js
const r = canAddTicker(doc.watchlist.length, { id: quota.planId || "free", maxWatchlist: quota.limit });
```
`doc.watchlist.length` at this point is exactly "how many tickers exist before this addition" — the contract `canAddTicker`'s own doc comment in `plan.js:20-24` requires. Only `quota.limit`/`quota.planId` (genuinely server-authoritative plan properties, unaffected by the local/server watchlist split) should come from the network call.

## Warnings

### WR-01: Guardian test never asserts which count value feeds `canAddTicker`, so the CR-01 finding above shipped undetected

**File:** `web/tests/test_fase13_watchlist_quota_ios.mjs:48-56`
**Issue:** The new guardian test for the iOS gate checks three things for `addWatchlistTicker`: that `watchlistQuota()` is called, that it's called before `write()`, and that it's called before the `doc.watchlist = [...doc.watchlist` push. It never inspects *what* is passed into `canAddTicker(...)` as the count argument — so a call passing `quota.count` (wrong, server-side) and a call passing `doc.watchlist.length` (correct, local) are indistinguishable to this guardian. This is exactly the class of regression the test was written to prevent (per its own header comment about CR-01), but the assertion set stops one step short of the actual enforcement logic.
**Fix:** Add an assertion pinning the count source, e.g.:
```js
ok(
  "addWatchlistTicker: canAddTicker recebe doc.watchlist.length (contagem LOCAL), não quota.count",
  !!addBody && /canAddTicker\(\s*doc\.watchlist\.length\s*,/.test(addBody)
);
```
and the mass-add equivalent already implicitly covered by the `final.length > (doc.watchlist || []).length` check in test 4, but consider a parallel explicit assertion that `canGrowWatchlistTo` is called with `final.length` (not `quota.count`) to lock the correct pattern symmetrically.

---

## Status de correção (2026-08-30)

- **CR-01**: corrigido em `101335e` — `canAddTicker(quota.count, ...)` →
  `canAddTicker(doc.watchlist.length, ...)`. Só `limit`/`planId` continuam
  vindo do servidor.
- **WR-01**: corrigido no mesmo commit — nova asserção em
  `test_fase13_watchlist_quota_ios.mjs` pinando o argumento exato de
  `canAddTicker`; mutação manual confirmada (reverter pra `quota.count`
  derruba o teste com 1 FALHA).
- Suíte canônica (`bash scripts/executar.sh --testes`) e `npx vite build`
  verdes após o fix.

_Reviewed: 2026-08-30T23:54:41Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
