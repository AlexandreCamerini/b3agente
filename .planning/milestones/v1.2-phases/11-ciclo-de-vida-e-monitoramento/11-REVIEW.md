---
phase: 11-ciclo-de-vida-e-monitoramento
reviewed: 2026-08-28T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - docs/OPERACAO-ciclo-de-vida-put.md
  - docs/adr/022-ciclo-de-vida-da-sugestao-de-put.md
  - server/app/agent.py
  - server/app/db.py
  - server/app/put_lifecycle.py
  - server/app/put_suggestions.py
  - server/tests/test_put_lifecycle_decisao.py
  - server/tests/test_put_lifecycle_diario.py
  - server/tests/test_put_lifecycle_estados.py
  - server/tests/test_put_lifecycle_scheduler.py
  - server/tests/test_put_lifecycle_sem_carteira.py
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-08-28
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Independently re-verified the two claims flagged as high-risk in the review brief, both hold up:

1. **`put_lifecycle.py` never touches the real wallet.** Grepped and read the full file: no import of `store`, no reference to `buy_option`/`sell_option`/`close_option_vencida`/`set_option_position`/`optionPositions`, and the only writes are through `put_suggestions.transicionar`/`registrar_pendencia` (new columns on `put_suggestions`) plus one global `db.kv_set` for the scheduler marker. `test_put_lifecycle_sem_carteira.py::test_b1_carteira_intocada_em_ciclo_completo` seeds `cash`/`positions`/`history`/`optionPositions` via direct `db.kv_set` (bypassing `store.py` entirely) and asserts byte-identical JSON after a full 4-round lifecycle sweep — ran it locally, passes. This is a real guarantee, not just a same-named test file.
2. **`intrinseco()` genuinely delegates to `agent.intrinseco_opcao`.** `put_lifecycle.py:115-116` does a local import (`from .agent import intrinseco_opcao`) and returns its result directly — no parallel `max(0, strike - spot)` formula exists in `put_lifecycle.py`.
3. **The D-EXEC-11-02-01 autonomous decision (hook moved outside the kill-switch/`is_trading_day` gate) is correctly implemented and the reasoning holds.** Confirmed by indentation analysis of `agent.py`: the `put_lifecycle.maybe_run` call (lines 1210-1214) sits at the same indent level as the `if radar_fetch is not None and not kill_switch_on() and pregao.is_trading_day():` block (line 1171), i.e. it is a **sibling**, not nested inside it — it runs regardless of kill-switch/trading-day state. Critically, it has its **own** `try/except` (1210-1213), which is what actually matters: the per-user stop/alvo cycle (lines 1355-1412, the "real" critical path) lives further down inside the *same* outer `try` (opened at line 1165, `except` at line 1413) that also wraps the put-lifecycle call. Without its own inner try/except, an exception raised inside `put_lifecycle.maybe_run` would propagate to the outer `except` at line 1413 and skip the per-user stop/alvo pass entirely for that tick. The inner try/except is what prevents that. `test_excecao_do_hook_nao_impede_ponte_nem_vizinhos`/`test_excecao_do_hook_nao_derruba_a_passada` in `test_put_lifecycle_scheduler.py` exercise exactly this and pass.

**Unguarded-type scan (the class of bug from Phase 0's CR-01 / Phase 10's WR-01):** checked every field `put_lifecycle.py` reads off a `put_suggestions` row (`ticker`, `strike`, `vencimento`, `contrato`, `premio`, `precoEntrada`, `estado`) against how it's produced. `ticker` is `TEXT NOT NULL` and passed through `normalize_ticker()` at insert (`put_suggestions.registrar`), and `candle_cache._key` degrades gracefully (`symbol or ""`) even if that guarantee were ever violated. `vencimento` is `TEXT NOT NULL`; `_vencida()` still re-validates with `isinstance(..., str)` before comparing (redundant but harmless). `strike`/`premio` are read through `_numero_positivo()` before any arithmetic, which rejects non-numeric/bool/non-positive values outright (SQLite is dynamically typed per column regardless of the declared `REAL`, so this guard is doing real work, not just satisfying a linter). `contrato` is only used as an opaque dict value in `forma_adr003` (dead code path today — see below), never compared/parsed. No equivalent of the Phase 0/10 crash-on-malformed-row bug was found; every row-level failure mode in `run_diario` is caught per-row (`test_excecao_em_uma_linha_nao_aborta_as_demais` covers this) rather than crashing the whole sweep.

Ran the phase's 5 test files locally (77 tests): all pass.

Two warnings below concern silent value-fabrication / missing-observability paths in `decidir()` — same family as the CLAUDE.md "never invent a value" principle, but neither one produces an incorrect financial/state result today; both are either an observability gap or a currently-unreachable defensive fallback.

## Warnings

### WR-01: An `armada` suggestion without a valid `premio` gets no observability trace while it waits for `vencimento`

**File:** `server/app/put_lifecycle.py:144-156` (`decidir`) and `server/app/put_lifecycle.py:273-288` (`run_diario`)

**Issue:** `premio` is **not** in `put_suggestions.CAMPOS_OBRIGATORIOS` (`put_suggestions.py:59-63`), and `put_bridge.py:132` sets it straight from `escolhido.get("lastPrice")` — a field that is legitimately absent for illiquid/untraded option contracts. So a row can land in the database as `armada` with `premio=None`.

When `decidir()` runs on such a row **before** its `vencimento` is reached:
```python
if estado_atual == "armada":
    if vencida:
        return "expirada_sem_uso", {}, "venceu sem execução"
    premio = linha.get("premio")
    if _numero_positivo(premio):
        ...
    return None, {}, "sem prêmio de entrada"   # <-- this branch
```
`run_diario`'s pendency branch only tracks two specific motives:
```python
elif motivo in ("sem preço de liquidação", "sem preço do ativo-objeto"):
    put_suggestions.registrar_pendencia(conn, linha["id"], hoje)
    pendentes += 1
```
`"sem prêmio de entrada"` is not one of them, so the row leaves **no trace**: `estado_em` stays `NULL` (it was never a `transicionar` target — `armada` is the row's initial state), `pendente_desde` stays `NULL`, and it doesn't count toward `avancos`/`pendentes`/`porEstado` in the daily summary.

Reproduced locally (3 consecutive daily sweeps over an `armada`/`premio=None` row, vencimento still weeks away):
```
2026-08-29 {'linhas': 1, 'avancos': 0, 'pendentes': 0, 'porEstado': {}, 'erros': []} estado=armada estadoEm=None pendenteDesde=None
2026-08-30 {'linhas': 1, 'avancos': 0, 'pendentes': 0, 'porEstado': {}, 'erros': []} estado=armada estadoEm=None pendenteDesde=None
2026-08-31 {'linhas': 1, 'avancos': 0, 'pendentes': 0, 'porEstado': {}, 'erros': []} estado=armada estadoEm=None pendenteDesde=None
```

Important nuance: this is **not** a correctness defect. The row's eventual outcome is correct either way — it self-resolves to `expirada_sem_uso` once `vencimento` passes (already covered by `test_armada_sem_execucao_ate_vencimento_vira_expirada_sem_uso`), and no `pnl_por_acao` is fabricated in the meantime. It's a genuinely-waiting contract with no last-trade print, not a sweep that's stuck — the sweep is behaving correctly, it's the *visibility* into that state that's missing. `test_put_lifecycle_sem_carteira.py::test_b3_nenhuma_linha_em_limbo_apos_rodada_mista` claims to prove "no line is in silent limbo," but never actually exercises this reachable state (`armada` + no `premio` + not yet vencida) — only the already-vencida case and rows already past `armada`.

**Consequence in production:** `docs/OPERACAO-ciclo-de-vida-put.md` §4's inspection query (`WHERE pendente_desde IS NOT NULL`) will report zero rows waiting on data even when one is — an operator debugging "why is `put_suggestions` not moving" would get a false "nothing pending" answer for this specific case.

**Fix — needs a product call, not just a one-line patch:** `pendente_desde`'s documented semantics are specifically "falta de preço confiável do **ativo-objeto**" (missing spot price for marking/liquidation), which is a different kind of gap than "the option contract itself has no captured last-trade price yet." Reusing the same column for both would blur that distinction in any future reporting built on it. Two legitimate options: (a) extend the `run_diario` pendency branch to also cover `"sem prêmio de entrada"`, reusing `pendente_desde` and accepting the slightly broader semantics, or (b) give this state its own signal (e.g. count it separately in the `run_diario` summary as `"semPremio"` without touching `pendente_desde`). Either way, add a `test_b3`-style case (`armada`, `premio=None`, `vencimento` in the future, several consecutive `run_diario` calls) asserting the chosen trace is present — right now the guardian test's claim and the code's actual coverage don't match for this state.

### WR-02: `decidir()` silently fabricates `preco_entrada = 0.0` when `precoEntrada` is missing/malformed, instead of treating it as unknown

**File:** `server/app/put_lifecycle.py:169-173`

**Issue:**
```python
preco_entrada = linha.get("precoEntrada")
try:
    preco_entrada_num = float(preco_entrada)
except (TypeError, ValueError):
    preco_entrada_num = 0.0
```
If `precoEntrada` is `None` or otherwise non-numeric on a row reaching `executada_simulada`/`monitorada`, this treats the entry price as `R$ 0,00` rather than surfacing "sem dado confiável" — the kind of value-fabrication CLAUDE.md's principle 4 forbids ("não invente valores... impeça operações dependentes de dados inválidos"). It would produce a silently-wrong (inflated) `pnl_por_acao`.

**Currently not reachable** via the automated path: the only producer of `executada_simulada` is `decidir()` itself (armada→executada_simulada), which always sets `preco_entrada` from a validated positive `premio` in the same `campos` dict, so a row can't legitimately reach this branch with a bad `precoEntrada` today — this is a dead defensive branch, not a live bug. It becomes live only if a future second entry path into `executada_simulada`/`monitorada` is added (e.g. a manual repair script, an admin tool, a schema back-fill of old Fase 10 rows) without also setting `preco_entrada`.

**Fix:** Treat a missing/invalid `precoEntrada` the same as missing spot data — return `(None, {}, "sem preço de entrada")` and let it fall into the pendency path (same motive-set extension as WR-01), rather than silently defaulting to `0.0`.

## Info

### IN-01: Runbook overstates trading-calendar awareness of the daily sweep

**File:** `docs/OPERACAO-ciclo-de-vida-put.md:9-12`, `server/app/put_lifecycle.py:233-245` (`should_run`)

**Issue:** The runbook says the sweep runs "uma vez por pregão útil" (once per trading day). In reality `should_run()` only checks `now.weekday() >= 5` (Sat/Sun) — unlike the neighboring `radar_fetch`-gated hooks, it does **not** call `pregao.is_trading_day()`, so it will also attempt to run on B3 holidays that fall on a weekday. This is a deliberate, well-tested choice (`test_put_lifecycle_scheduler.py::test_hook_roda_em_dia_sem_pregao`, and ADR-022 Decision 3 explains why it's safe: cache-only, self-correcting via `pendente_desde`), so this is not a functional bug — just imprecise wording in the ops doc that could mislead a future reader into assuming holiday-awareness that isn't there.

**Fix:** Tweak the runbook line to "roda em todo dia útil (segunda–sexta), incluindo feriados da B3 — não depende de `pregao.is_trading_day()`, ver ADR-022 Decisão 3" so it matches the actually-tested behavior.

---

_Reviewed: 2026-08-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
