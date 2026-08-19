# Deferred Items — Phase 03 (Correção Crítico + Alto)

## 03-04

- **Web test suite environment gap (out of scope, pre-existing — same as
  phase 02).** `bash scripts/executar.sh --testes` reports 7 failing
  `web/tests/*.mjs` files: `test_appmode_sincroniza_servidor.mjs`,
  `test_carteira_nativa_sincroniza.mjs`, `test_fase2_portfolio.mjs`,
  `test_notif_central.mjs`, `test_notify.mjs`,
  `test_oauth_repassa_name_e_code.mjs`, `test_pet_resumo_modo_web.mjs`. All 7
  fail with the identical root cause: `Error [ERR_MODULE_NOT_FOUND]: Cannot
  find package '@capacitor/core' imported from .../web/src/persistence.js` —
  `web/node_modules` does not exist at all in this worktree checkout
  (`ls web/node_modules` → no such file or directory), even though the
  package is declared in `web/package.json`. This is a worktree-provisioning
  gap (`npm install` was never run for `web/` in this isolated worktree), not
  a code regression — plan 03-04 touched ONLY `server/app/main.py`,
  `server/app/plan.py`, and `server/tests/test_fase3_gate_plano.py`, no
  `web/` file. Per the package-manager-install exclusion (Rule 3), this
  executor does not run `npm install` unilaterally. Backend suite
  (`cd server && ./.venv/bin/python -m pytest -q`) is fully green: 1059
  passed. Flag for the orchestrator/human: run `npm install` inside `web/`
  in this worktree (or verify CI/merge target has it installed) before
  treating the canonical suite as fully green.

## 03-05

- **Same `web/node_modules` gap, verified non-blocking (temporary symlink,
  not committed).** Confirmed the 7 failures listed above are 100%
  attributable to the missing `web/node_modules` (same
  `ERR_MODULE_NOT_FOUND: '@capacitor/core'`) and not a code regression:
  `web-admin/package-lock.json` and `web/package-lock.json` are byte-identical
  to the main clone's (`diff` confirmed), so a temporary symlink to the main
  clone's already-installed `node_modules` (`ln -s
  /Users/acamerini/dev/bolsia/b3-agente/web/node_modules
  <worktree>/web/node_modules`, same for `web-admin/`) was created ONLY to
  run `npx vite build` (web-admin) and `bash scripts/executar.sh --testes`,
  then removed before every `git add`/commit — `node_modules/` is gitignored
  either way, so nothing leaks into history or the working tree. With the
  symlink in place: `bash scripts/executar.sh --testes` → exit 0, zero
  `[X]`, all 7 previously-failing files pass. Same remediation precedent as
  03-02's SUMMARY (symlink pattern) and 03-04's deferred-items.md entry
  above (pre-existing gap). Flag for the orchestrator/human still stands:
  run `npm install` inside `web/` in this worktree for a permanent fix.

## 03-06

- **Pre-existing test-isolation gap: `candle_cache._DB_CONN` is a
  process-global, lazily-resolved, per-thread-cached connection that can
  leak synthetic test fixture data into the REAL worktree SQLite DB
  (`server/data/b3_agente.db`) when the full pytest suite runs — NOT caused
  by this plan's new file (`server/tests/test_fase3_kill_switch_duracao.py`)
  and NOT fixed here (architectural, spans ~10 pre-existing test files,
  out of scope of this plan's file list).

  **What happened:** during the Task 3 human-verify checkpoint, the
  developer hit a broken `PriceChart` (`date: "2026-01-01+125"`, an invalid
  format) when opening the technical panel live. This is the EXACT date
  formula used by `_mk_candles()` in
  `server/tests/test_fase3_proveniencia_technicals.py` (`f"2026-01-01+{i}"`,
  same OHLC formula) — a pre-existing plan-03 test file (not touched by this
  plan), whose tests `test_a_snapshot_propaga_source_do_candle_cache` and
  `test_b_snapshot_nao_inventa_source_quando_ausente` call
  `technical_snapshot.get()` DIRECTLY (no HTTP layer, no
  `monkeypatch.setenv("B3_DB_PATH", ...)`, no fresh `app.main` import) —
  unlike this same file's OTHER tests (`test_c`..`test_f`), which correctly
  isolate via a `_client(monkeypatch)` helper.

  **Root cause (code-level, confirmed by reading, not just correlation):**
  `server/app/main.py:50-55` does, at MODULE IMPORT time,
  `_conn = db.shared()` (a `_ThreadLocalConnection` constructed with
  `db_path=None` — i.e. it defers path resolution to the FIRST query on
  EACH thread, reading `B3_DB_PATH`/the real default path AT THAT MOMENT,
  not at construction) followed by `candle_cache.configure_db(_conn)`,
  which stores this SAME lazy connection object in the module-global
  `candle_cache._DB_CONN`. `candle_cache.reset()` (called by this and other
  tests' `_isolado` fixtures) only clears the L1 memory dict (`_CACHE`) —
  it does NOT touch `_DB_CONN`/`_DB_ENABLED`. There is no `conftest.py` in
  `server/tests/` setting `B3_DB_PATH` at the session level. At least 10
  pre-existing test files import `app.main` at MODULE level (collection
  time, before any monkeypatch runs) with no `B3_DB_PATH` override at all:
  `test_admin_portal.py`, `test_pet.py`, `test_assistente.py`,
  `test_setores.py`, `test_didatica_rotas.py`, `test_pet_todas_telas.py`,
  `test_pet_perguntas_sugeridas.py`, `test_politica_privacidade.py`,
  `test_adr013_cobertura_rotas.py`, `test_assistente_kb.py`. Whichever
  thread first resolves `candle_cache._DB_CONN`'s connection while
  `B3_DB_PATH` happens to be unset (the ambient state for a bare `pytest -q`
  run, since nothing sets it session-wide) permanently binds that thread's
  cached connection to the REAL default DB path
  (`<server>/data/b3_agente.db`) for the rest of the pytest session — so
  when `test_a`/`test_b` later call `technical_snapshot.get()` on that same
  thread, the synthetic `_mk_candles()` rows get persisted to L2
  (`candle_cache` table) in the REAL worktree database, not a temp one.

  **Confirmed NOT the new file added by this plan:** this plan's
  `test_fase3_kill_switch_duracao.py` never touches `candle_cache` or
  `app.main`'s shared connection. Task 1 tests use `db.connect(tempdir)`
  directly (`_fresh_db()`/`_admin_conn()` helpers), bypassing `app.main`
  entirely. Task 2 route tests follow the SAME safe pattern already
  established by `test_fase3_timing_watch_kill.py`
  (`monkeypatch.setenv("B3_DB_PATH", ...)` BEFORE
  `sys.modules.pop("app.main", None)` + fresh `importlib.import_module`),
  which forces a brand-new, correctly-isolated connection object every
  time. The contamination is fully explained by running the PRE-EXISTING
  full suite (`cd server && ./.venv/bin/python -m pytest -q`, required by
  this plan's own acceptance criteria and run twice during this plan's
  execution) against this worktree's ambient (unset) `B3_DB_PATH`.

  **Remediation applied (data only, not code):** the developer (via the
  orchestrator) manually corrected the 15 contaminated `candle_cache` rows'
  `date` fields directly in the worktree's SQLite DB — a data-repair, not a
  code change, and the DB file is gitignored (`server/data/`, confirmed via
  `git check-ignore`), so nothing leaked into version control.

  **Not fixed here (scope boundary):** fixing this properly (e.g., a
  session-scoped `conftest.py` autouse fixture that sets `B3_DB_PATH` to a
  temp path before ANY test collection/import, or making
  `candle_cache.reset()` also clear `_DB_CONN`/`_DB_ENABLED`) touches
  ~10 pre-existing test files and test infrastructure, none of which are in
  plan 03-06's file list (`server/app/db.py`, `server/app/agent.py`,
  `server/app/main.py`, `web-admin/src/App.jsx`,
  `server/tests/test_fase3_kill_switch_duracao.py`,
  `web/tests/test_fase3_admin_duracao.mjs`). Flag for the orchestrator/
  human: this can bite ANY future worktree that runs the full backend
  suite locally without an isolated `B3_DB_PATH` — worth a dedicated fix
  (likely a `server/tests/conftest.py` session-scoped autouse fixture)
  in a future phase, independent of any specific feature plan.
