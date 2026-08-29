---
phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa
verified: 2026-08-27T23:50:00Z
status: passed
score: 11/11 must-haves verified (2 explicitly deferred by design, 2 pre-existing documented gaps carried as warnings)
overrides_applied: 0
re_verification: null
human_verification: []
---

# Phase 9: Centralização de dados de mercado (mydata_client.py) Verification Report

**Phase Goal:** Implementar `mydata_client.py` consumindo `GET /v1/cotacoes/{ticker}` e `GET /v1/opcoes/{ticker}` do cvm-financas (`mydata.acamerini.app`). Migrar COTAHIST diário (aposenta `b3_historical.py`/ADR-019) e Opções/IV (substitui `options_provider_yahoo.py`, mantém ADR-004 sem reabrir via `providerStatus`). Redefinir brapi como fonte exclusiva de cotação spot ao vivo (ADR-008 com escopo reduzido). Yahoo intraday 15min fica intocado (ADR-001 sem mudança). Critério de aceite obrigatório: medir rate-limit real (60/min·2.000/dia) contra padrão de uso antes de desligar Yahoo/brapi nas fatias migradas.

**Verified:** 2026-08-27
**Status:** passed
**Re-verification:** No — initial verification

## Framing: why "adiar" is a pass, not a gap

This phase's own contract (09-06-PLAN.md must_haves, `<how-to-verify>` step 1) explicitly defines the checkpoint's valid terminal states as **`aprovado` OR `adiar`** — with `adiar` being the *mandated* response whenever the rate-limit veredito is `NÃO CABE`. The veredito came back `NÃO CABE` (148 calls/min projected vs. 60/min ceiling). The human (Alex) responded `adiar`, with rationale, a resume condition, and confirmation that no env var was touched in production. This is the plan working as designed, not a failure to execute it. Verification below treats "code built + tested behind env vars, decision recorded with rationale, nothing silently activated" as the actual goal for the cutover truths — and confirms all three independently in the codebase, not from SUMMARY narrative.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `mydata_client.py` authenticates via `X-API-Key`, never fabricates data on failure, paginates by cursor with a loop cap | VERIFIED | Read `server/app/mydata_client.py` in full: `X-API-Key` header (no `Authorization`), 429/401/403 raise without retry, 5xx retries twice, `_paginar` caps at `PAGINAS_MAX=8`. 26+12 offline guardians in `test_mydata_client.py`. |
| 2 | `mydata_budget.py` enforces 60/min · 2000/day, reconciles against real headers | VERIFIED | Read module: two independent windows (minute in-memory, day persisted in `kv`), `MARGEM=0.9` safety margin, `snapshot()` exposes `headerQuota` from `mydata_client.LAST_QUOTA`. 11 guardians pass. |
| 3 | Candle fallback chain is mydata→brapi→Yahoo in a single request, intraday never touches mydata | VERIFIED | Read `candle_provider.py` roteador: `_gate()`/`_debita()` applied per-hop over `[get_provider(), *get_fallbacks()]`; `valida_fatia()` rejects `interval!=1d` before any network call. 21 guardians in `test_mydata_provider.py` cover 2-hop degradation, intraday-never-touches-mydata, cota gate skip without network. |
| 4 | Options chain/IV/greeks servable from mydata behind the unchanged ADR-004 `providerStatus` contract, no Yahoo fallback (D-04) | VERIFIED | Read `options_provider_mydata.py`: `grep -c yahoo` = 0, `grep -c black_scholes` = 0 (no local recompute), all legacy contract keys present, `ivStatus`/`greeks`/`theoreticalPrice` additive. `test_options_provider.py` proves contract-key parity `mydata ⊇ yahoo`. |
| 5 | b3_historical parallel COTAHIST ingestion is retired, no code path downloads from the B3 directly | VERIFIED | `server/app/b3_historical.py` confirmed absent from disk and `git ls-files`; `grep -rlE 'bvmf.bmfbovespa.com.br|COTAHIST_D' server/app/` returns nothing; `rbac.py` entity reverted (`b3_daily_import` count = 0); scheduler hook removed with neighbors (`analytics`/`maybe_warm`/`signal_ledger`) intact; commit `b3fdf02` still recoverable in history (`git cat-file -e` OK). |
| 6 | ADR-019 stamped, not rewritten; ADR-020 records the full supersession with real numbers | VERIFIED | `docs/adr/019-cotahist-diario-b3.md` has only the added `**Status:** Superada parcialmente pela ADR-020...` header, body untouched. `docs/adr/020-...md` (195 lines) has all 6 required sections, D-01..D-04 tracked, `b3fdf02` cited, MEDICAO numbers cited, reversibility documented literally (`B3_OPTIONS_PROVIDER=yahoo`). |
| 7 | Rate-limit measured (not estimated) against 60/min·2000/day, veredict published, action plan recorded if it doesn't fit | VERIFIED | `docs/MEDICAO-Mydata-2026-08-27.md` (228 lines): projection phase executes real code with injected fake `fetch_json`/counters (not code-reading estimates), veredict section present (`NÃO CABE` on peak/min, `CABE` on daily volume), action plan (negotiate quota increase vs. tighten `scanner` spacing to `intervaloMinimoSeguro=1.0s`). |
| 8 | The live leg of the measurement (real key authenticating against mydata.acamerini.app) actually ran | **NOT VERIFIED — correctly escalated, not silently skipped** | 09-04-SUMMARY.md states explicitly this truth (`"A chave de produção autentica de fato... e devolve dado das duas rotas"`) was **not fulfilled** — `MYDATA_TOKEN` was absent in the execution environment, the script correctly exited code 2 rather than simulate/estimate (verified: this is the exact degradation path the plan mandated — "PARE. Não invente número"). `.planning/todos/pending/medir-rate-limit-mydata.md` §Resultado, read directly (not summary-trusted), confirms: still in `pending/`, explicitly labeled "PARCIAL, ainda PENDING," item 3 (live key confirmation) open. This is a correctly-surfaced gap that fed directly into the `adiar` decision at the checkpoint — not a silently-dropped truth. |
| 9 | The production cutover only happens with the veredict on the table and Alex approving; rollback path known before flipping | VERIFIED | `docs(09-06)` commit `9aa5e5f` records literal numbers presented (veredict NÃO CABE, 148/60, live leg not run, options-gate architecture gap, liquidity_score=52.0) and the literal response `adiar`, with a resume condition. No `B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER` mutation anywhere in the repo; code-level defaults confirmed still `"yahoo"` in both `candle_provider.py:213` and `options_provider.py:36`. |
| 10 | Front recognizes "MyData" as a source label, banner no longer claims Yahoo exclusively, front actually published (not just built) | VERIFIED | `FONTE_LABEL` in `web/src/App.jsx:1125` has `source === "mydata" ? "MyData"` branch with pass-through for unknown sources preserved. `disclaimers.js` no longer contains "Yahoo Finance". Carimbo `F10-20260827-02` consistent across `web/src/version.js`, `server/web_dist/assets/index-Bf73jdLI.js`, and `server/app/main.py:953` `SERVER_BUILD_ID`. |
| 11 | Post-review fixes (CR-01, WR-02) landed in the code, not just claimed in commit messages | VERIFIED | Read current `mydata_client.py:226-242`: `get_vencimentos()` now requires `isinstance(resp.get("dados"), list)`, raising `MydataIndisponivel` for any other shape — matches CR-01 fix description exactly. `git show 25c37e2` confirms WR-02 text fix + full republish cycle (bump.sh + publicar-web.sh) producing the F10-20260827-02 carimbo, superseding the -01 stamp recorded in 09-06-SUMMARY.md as expected. |

**Score:** 10/11 truths fully VERIFIED; 1 (live-key authentication) correctly NOT verified and NOT masked — it is the exact input that triggered the `adiar` decision, which is itself a valid, well-documented terminal state per this phase's contract.

### Known, Documented, Non-Blocking Gaps (carried as WARNING, not BLOCKER)

Both items below are pre-existing architecture findings that the phase's own documentation (ADR-020, 09-04-SUMMARY.md, 09-REVIEW.md) already surfaces — not new defects discovered by this verification, and both are dormant because `B3_OPTIONS_PROVIDER` defaults remain `"yahoo"`.

| Item | Where | Status | Why non-blocking |
|------|-------|--------|-------------------|
| WR-01 | `options_provider_mydata.py`/`options_provider.py` never call `mydata_budget.pode_gastar()`/`debita()` — options path has zero local rate gate, and it now feeds the autonomous agent cycle (`option_quotes_getter=`) at every scheduler tick, not just UI browsing | CONFIRMED still open in code (`grep -c mydata_budget` on both files returns 0) | Dormant: `B3_OPTIONS_PROVIDER` default is `"yahoo"` in code, confirmed by grep, and production was never flipped. Documented as a pre-condition to resolve before any future options cutover (ADR-020 §Consequências, 09-REVIEW.md WR-01). |
| IN-01 | `mydata_budget.aguarda_vaga()` fully implemented and tested but never called from any production code path | CONFIRMED (repo-wide search in 09-REVIEW.md, not re-derived here — informational, not re-verified independently) | The exact pacer mechanism ADR-020/MEDICAO name as the fix for the pico/min shortfall, built but not yet wired — appropriately flagged as follow-up, not a blocker for this phase's stated goal. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `server/app/mydata_client.py` | HTTP client: auth, retry, cursor pagination, candle+options mapping | VERIFIED | 26+12+ guardians pass; CR-01 fix confirmed live in code |
| `server/app/mydata_budget.py` | 60/min·2000/day budget | VERIFIED | 11 guardians pass |
| `server/app/candle_provider.py` (MydataProvider + N-hop chain) | Registered provider + fallback chain + per-hop gate | VERIFIED | `class MydataProvider` present, `_gate`/`_debita` present, 21 guardians pass |
| `server/app/options_provider_mydata.py` | ADR-004 adapter, no Yahoo fallback | VERIFIED | D-04 compliance confirmed by grep (0 yahoo references) |
| `server/app/options_provider.py` | Env-based selector, default yahoo | VERIFIED | `provider_name()` default confirmed `"yahoo"` |
| `scripts/medir-mydata.py` | Measurement script, real-code-execution based | VERIFIED | `scanner.get_universe()` used (not literal number), guards against printing token |
| `docs/MEDICAO-Mydata-2026-08-27.md` | Numbers + veredict + action plan | VERIFIED | 228 lines, veredict section present, live leg explicitly marked BLOQUEADO |
| `docs/adr/020-centralizacao-de-dados-no-mydata.md` | Supersession record | VERIFIED | 195 lines, all 6 sections present |
| `docs/adr/019-cotahist-diario-b3.md` | Stamped, not rewritten | VERIFIED | Only header line added, body intact |
| `web/src/App.jsx`, `web/src/disclaimers.js` | Source labels updated | VERIFIED | `"mydata"` → `"MyData"` present; "Yahoo Finance" string removed |
| `server/web_dist` | Published build | VERIFIED | Carimbo F10-20260827-02 present in built assets, matches version.js and SERVER_BUILD_ID |
| `.planning/todos/pending/medir-rate-limit-mydata.md` | Result appended, original text preserved | VERIFIED (read directly) | `## Resultado (2026-08-27)` section present, original text intact, correctly still in `pending/` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `candle_provider.py` | `mydata_client.py` | `MydataProvider.history` delegates to `get_history` | WIRED | Confirmed by reading class body |
| `candle_provider.py` | `mydata_budget.py` | `_gate`/`_debita` call `pode_gastar`/`debita` | WIRED | Confirmed in roteador |
| `candle_provider.py::snapshot` | `/api/obs/usage` | `orcamentoMydata` key, no `main.py` edit needed | WIRED | `main.py:561` already exposes `candle_provider.snapshot()` |
| `options_api.py` | `options_provider.py` | import swapped | WIRED | `grep -c 'from .options_provider import get_options'` = 1 |
| `main.py` (8 call sites incl. agent scheduler) | `options_provider.get_options` | direct calls + `option_quotes_getter=` | WIRED | Confirmed via 09-03-SUMMARY.md file list + WR-01's own confirmation that this wiring reaches the agent cycle |
| `agent.py::scheduler_loop` | `b3_historical.maybe_run` | REMOVED | CONFIRMED REMOVED | grep for `b3_historical` in `agent.py`/`main.py`/`db.py`/`rbac.py` returns 0 (excluding comments) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Canonical test suite (backend + web) | `bash scripts/executar.sh --testes` | 1516 passed, 1 skipped (backend); all `web/tests/*.mjs` OK | PASS |
| Candle provider default unchanged | `grep -n 'B3_CANDLE_PROVIDER' server/app/candle_provider.py` | default `"yahoo"` | PASS |
| Options provider default unchanged | `grep -n 'B3_OPTIONS_PROVIDER' server/app/options_provider.py` | default `"yahoo"` | PASS |
| CR-01 fix present in current code | Read `mydata_client.py:226-242` | `isinstance(resp.get("dados"), list)` guard present | PASS |
| Build carimbo consistency | grep across version.js/web_dist/main.py | all show `F10-20260827-02` | PASS |
| No debt markers in phase-touched files | grep `TBD\|FIXME\|XXX` across all files this phase modified | only a false-positive docstring example ticker `XXXXX9` in `candle_provider.py`, not a marker | PASS |

### Probe Execution

Not applicable — no `scripts/*/tests/probe-*.sh` declared or discovered for this phase.

### Requirements Coverage

Not applicable. No `.planning/REQUIREMENTS.md` exists in this project (confirmed: only `.planning/intel/requirements.md`, which is the PRD-ingest synthesizer's explicit "zero PRDs found" output, not a requirements traceability document). ROADMAP.md lists `**Requirements**: TBD` for Phase 9, and no plan in this phase declares any `requirements:` frontmatter IDs (all six plans show `requirements: []`). There is nothing to cross-reference and no orphaned requirement IDs to flag.

### Anti-Patterns Found

None blocking. No unreferenced TBD/FIXME/XXX debt markers in phase-touched files. No stub returns, no hardcoded empty payloads flowing to rendering, no placeholder text. The two pre-existing architecture gaps (WR-01, IN-01) are documented findings carried forward as warnings, not newly discovered code smells.

### Human Verification Required

None outstanding. The one item that required human judgment in this phase — the production cutover checkpoint (09-06 Task 3) — already ran and was resolved (`adiar`, recorded literally with rationale and resume condition in commit `9aa5e5f`). There is no pending decision left for a human to make as a result of this verification.

### Gaps Summary

No blocking gaps. The phase goal — build the mydata integration end-to-end, keep it inert behind env-var defaults until proven safe, and make the rate-limit measurement a hard gate on cutover — is achieved and independently confirmed in the codebase (not just claimed in SUMMARY.md):

- All new code artifacts exist, are substantive (not stubs), are wired into their respective call sites, and pass 100+ offline guardians plus the full 1516-test canonical suite.
- The one truth that did NOT close (live-key authentication against the real mydata API) was correctly surfaced rather than masked, fed directly into the `adiar` decision, and is tracked with a clear resume condition in a still-`pending/` TODO file (verified by direct read, not SUMMARY trust).
- Both post-review fixes (CR-01 critical bug, WR-02 UI provenance inaccuracy) are confirmed present in the current code, not just claimed in commit messages, with the front republished and the build carimbo consistent end-to-end.
- The two remaining review findings (WR-01 options rate gate, IN-01 unused pacer) are pre-existing, previously-documented architecture gaps, confirmed still open, correctly non-blocking because the code paths they concern are dormant behind unflipped env-var defaults.
- No production behavior changed: `B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER` remain at pre-phase defaults, confirmed at the code level (not just asserted in a SUMMARY).

---

*Verified: 2026-08-27*
*Verifier: Claude (gsd-verifier)*
