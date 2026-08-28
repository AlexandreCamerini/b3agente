---
phase: 10-ponte-gatilho-put
reviewed: 2026-08-28T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - docs/OPERACAO-ponte-gatilho-put.md
  - docs/adr/021-ponte-gatilho-put.md
  - server/app/agent.py
  - server/app/db.py
  - server/app/put_bridge.py
  - server/app/put_suggestions.py
  - server/tests/test_put_bridge_diario.py
  - server/tests/test_put_bridge_scheduler.py
  - server/tests/test_put_bridge_sem_superficie.py
  - server/tests/test_put_bridge_triagem.py
  - server/tests/test_put_suggestions.py
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-08-28
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Reviewed the ponte gatilho→put (`put_bridge.py`/`put_suggestions.py`), its
scheduler hook in `agent.py`, the new `put_suggestions` table in `db.py`,
the ADR/runbook pair, and all five test files. The three deliberate,
pre-documented facts named in the review brief were independently verified
against the merged code, not taken on faith:

- **(a) Dormant in production.** Confirmed by reading `options_provider_yahoo.py`
  directly: `_clean_contract` never emits an `exerciseStyle` key. With
  `B3_OPTIONS_PROVIDER=yahoo` (untouched default), every put contract fails
  `triar_put`'s `estilo_exercicio` guard (`put_bridge.py:90-93`) and the daily
  run genuinely closes with `(None, "nenhuma put elegível")` — no crash, no
  fabricated `exerciseStyle`, matches `docs/OPERACAO-ponte-gatilho-put.md` §3.
- **(b) WR-01 mitigation (sequential-only).** Confirmed `put_bridge.py` has
  zero occurrences of `asyncio.gather`/`create_task`/`ensure_future`
  (`grep` verified) and zero occurrences of `options_provider_mydata` (the
  guardian's own check). `run_diario` awaits `options_provider.get_options`
  inside a plain `for` loop (`put_bridge.py:301-328`), and
  `test_consulta_e_sequencial_nunca_concorrente` proves reentrancy never
  exceeds 1 even with a real `await` inside the fake provider. The
  `_gate()`→`_debita()` window inside `options_provider_mydata.get_options`
  genuinely has no `await` between them (verified by reading
  `options_provider_mydata.py:142-174`), so Phase 10 does not widen WR-01's
  race window, only adds a third caller to the existing one — as claimed.
- **(c) `MAX_TICKERS_DIA=10`** is enforced and covered by
  `test_teto_diario_de_tickers`.

Also verified directly, per the review brief's specific asks:

- **Idempotency:** `put_suggestions` has `UNIQUE(user_id, ticker,
  data_pregao)` (`db.py:339`) and `registrar()` uses `INSERT OR IGNORE`
  (`put_suggestions.py:85-90`), returning `0` on a duplicate key — confirmed
  by `test_regravar_mesma_chave_nao_duplica` and
  `test_rodar_duas_vezes_no_mesmo_dia_nao_duplica`. Reruns cannot duplicate
  rows.
- **Hook isolation at the scheduler boundary:** `maybe_run` has its own
  `try/except Exception` (`put_bridge.py:346-365`) and `scheduler_loop` wraps
  the call in a *second*, independent `try/except`
  (`agent.py:1202-1206`) — the documented "two belts" pattern shared with
  `signal_ledger_job`. `test_excecao_do_hook_nao_derruba_a_passada` and
  `test_maybe_run_nunca_propaga_excecao` both exercise this with a real
  `RuntimeError` and confirm the scheduler's heartbeat still ticks. No
  exception from this hook reaches `scheduler_loop` unhandled.
- **Per-user scoping of `positions`:** `carteiras_por_ticker` scans
  `kv WHERE key LIKE 'u:%:positions'`, which (a) matches the `u:<id>:positions`
  format `db._scoped` produces, and (b) structurally excludes the anonymous
  bucket (bare `positions`, no `u:` prefix) — confirmed by
  `test_balde_anonimo_e_ignorado`. Each `put_suggestions` row is written
  per-`uid` inside the `for uid in carteiras[ticker]` loop
  (`put_bridge.py:311-325`), so one user's suggestion cannot leak into
  another's — confirmed by `test_dois_usuarios_mesmo_ticker_mesmo_dia...`
  (2 users, 1 chain fetch, 2 rows) and `test_usuarios_diferentes_mesmo_ticker_mesmo_dia_coexistem`.

Two WARNING-level gaps were found during this pass, both in
`put_bridge.py`; details below. No BLOCKER-level issues were found — the
long-only structural guarantees (`CHECK(option_type='put')`, absence of any
quantity/margin/side column) and the `signal_ledger` isolation (D-10-A) hold
under direct testing (`test_option_type_call_e_rejeitado_pelo_check`,
`test_agregacoes_do_adr017_nao_enxergam_sugestao_de_put`,
`test_nao_toca_signal_ledger`).

**Post-review:** both WR-01 and WR-02 were fixed in commit `465f13d` (see
findings below for what changed).

## Warnings

### WR-01: `carteiras_por_ticker` can abort the entire daily run for every user, contradicting its own documented per-line isolation

**File:** `server/app/put_bridge.py:228-251`

**Issue:** The function's docstring promises the same isolation contract as
`agent._agent_rows` — "`json.loads` com try/except POR LINHA (linha ruim é
pulada, nunca aborta)". That promise holds for the JSON-decode step
(`try: positions = json.loads(value) except (ValueError, TypeError):
continue`, line 237-240) but **not** for what happens next. For each
position dict `p` in a user's `positions` list:

```python
t = p.get("t")
if not t:
    continue
out.setdefault(normalize_ticker(t), set()).add(uid)
```

`normalize_ticker` (`server/app/tickers.py:13-18`) does
`re.sub(r"\s+", "", (s or "").upper())`. If `t` is truthy but not a string
(e.g. an `int`, `list`, or `dict` — malformed/legacy data, a migration bug,
or manual DB tampering), `(s or "").upper()` raises `AttributeError`
(int/list/dict have no `.upper()`), and that exception propagates out of
`carteiras_por_ticker`, out of `run_diario` (the call at line 282 sits
*before* the per-ticker `try/except` at lines 301-328, so it is not
protected by it), and is only caught by `maybe_run`'s outer `try/except`
(`put_bridge.py:346-365`).

Net effect, precisely stated: this **does not** escape to `scheduler_loop`
— the outer hook-isolation boundary the review brief asked about holds,
confirmed by the existing double try/except and by
`test_excecao_do_hook_nao_derruba_a_passada`'s pattern applying here too.
But the *inner* isolation the function's own docstring claims does not
hold: one malformed `t` field in **any single user's** `positions` blob
aborts `run_diario()` for **every** user that day — not just the offending
one. The intersection-then-loop design (gatilho ∩ carteira, then per-ticker
try/except) means a healthy user's chain lookup never even gets attempted
if an unrelated user's row poisons the upstream scan. This is a cross-user
blast-radius bug relative to what the code claims about itself, even though
it degrades gracefully (silently skips the whole day, logs nothing beyond
`LAST_RUN["erro"]`) rather than crashing the process.

**Fix:** Push the same per-item defensiveness one level deeper, mirroring
the try/except already used for the JSON decode:

```python
for p in positions:
    if not isinstance(p, dict):
        continue
    t = p.get("t")
    if not isinstance(t, str) or not t:
        continue
    out.setdefault(normalize_ticker(t), set()).add(uid)
```

This makes a single malformed row inert instead of fatal to the whole scan,
matching the isolation level the docstring already promises.

### WR-02: `triar_put` validates strike type but not positivity, unlike `spot`/`iv`

**File:** `server/app/put_bridge.py:81-83`

**Issue:** `_numero_positivo()` (line 46-47) is defined and applied
consistently to `spot` (line 63) and to `iv` (line 86) — both must be a
real, positive number or the payload/contract is rejected. `strike` gets a
weaker check:

```python
strike = contrato.get("strike")
if not isinstance(strike, (int, float)) or isinstance(strike, bool) or strike > spot:
    continue  # proteção é abaixo do preço atual — sem contador dedicado
```

This validates type and the "below spot" business rule, but not
positivity. A contract with `strike == 0` or `strike < 0` passes this guard
(it is `<= spot` for any positive spot) and continues into the eligibility
pool. If IV/estilo/liquidez checks also pass for that same malformed
contract — plausible if it's a genuinely bad row from the source rather
than a hand-crafted adversarial one — it becomes a candidate in the sort at
line 112-119, and would win if it happens to be the only (or closest-ranked)
eligible contract that day. This is a data-integrity gap contingent on a
malformed upstream payload (mydata/Yahoo would have to emit a strike ≤ 0),
not a demonstrated defect with real data today — no test in
`test_put_bridge_triagem.py` exercises a zero/negative strike, so the gap
is unexercised in either direction.

**Fix:** Reuse the existing helper instead of the weaker ad hoc check:

```python
strike = contrato.get("strike")
if not _numero_positivo(strike) or strike > spot:
    continue  # proteção é abaixo do preço atual — sem contador dedicado
```

**Fixed post-review (commit `465f13d`):** both WR-01 and WR-02 applied exactly
as suggested. WR-01: `carteiras_por_ticker` now checks `isinstance(t, str)`
before calling `normalize_ticker(t)`, so a malformed position entry is
skipped per-line instead of raising and aborting `run_diario` for every
user. WR-02: `triar_put`'s strike check now reuses `_numero_positivo()`.
Guardian tests added: `test_posicao_com_ticker_malformado_nao_aborta_carteiras_por_ticker`
(mixed malformed/valid positions across two users, confirms isolation) and
`test_strike_zero_ou_negativo_e_pulado`. Canonical suite green twice post-fix
(1597 passed/1 skipped both runs).

## Info

### IN-01: `db._now_iso()` accessed as a "private" (underscore-prefixed) cross-module attribute

**File:** `server/app/put_suggestions.py:78`

**Issue:** `candidato["criado_em"] = db._now_iso()` reaches into another
module's underscore-prefixed name. This matches existing precedent in the
codebase (`signal_ledger.py`, `audit.py`, `rbac.py` all do the same), so it
is not a new pattern introduced by this phase — flagged for visibility
only, not as a regression.

**Fix:** None required; consistent with established convention. If this is
ever revisited codebase-wide, promoting `_now_iso` to a public
`db.now_iso()` would remove the underscore-crossing but is out of scope for
this phase.

---

_Reviewed: 2026-08-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
