---
phase: 00-precondi-es
reviewed: 2026-08-28T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md
  - docs/OPERACAO-ledger-de-sinais.md
  - docs/adr/020-centralizacao-de-dados-no-mydata.md
  - scripts/diagnostico-tickers-ledger.py
  - server/app/ledger_tickers.py
  - server/app/options_provider.py
  - server/app/options_provider_mydata.py
  - server/app/signal_ledger_bootstrap.py
  - server/tests/test_agent_options.py
  - server/tests/test_ledger_tickers.py
  - server/tests/test_options_provider.py
  - server/tests/test_options_provider_mydata.py
  - server/tests/test_signal_ledger_bootstrap.py
findings:
  critical: 1
  warning: 1
  info: 1
  total: 3
status: issues_found
---

# Phase 0: Code Review Report — LEDGER-01 + OPTGATE-01 (v1.2)

**Reviewed:** 2026-08-28
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Two independent unattended overnight deliveries were reviewed.

**LEDGER-01** (`ledger_tickers.py` + retry in `signal_ledger_bootstrap.py`) is
well-evidenced: the alias/exclusion map cites a dated, reproducible diagnosis
per entry, `resolver()` correctly separates "symbol fetched from Yahoo" from
"key written to the ledger" (verified by
`test_executar_ticker_com_alias_busca_pelo_alias_mas_grava_sob_ticker_do_universo`),
and exclusion is enforced in the single code path that iterates the universe
(`executar()`), not bypassed by any parallel path — `scanner.DEFAULT_UNIVERSE`
itself is untouched, exactly as the module docstring commits to. However, I
found and reproduced a real gap: `signal_ledger_bootstrap.py`'s own `--tickers`
CLI parsing does not fully normalize its input before that value becomes the
**ledger write key**, while `scanner.get_universe()`'s equivalent override path
does. This silently fragments the ledger's `(ticker, ...)` key for any ticker
supplied with a `.SA` suffix, stray case, or similar — see CR-01. Concretely
reproduced below; the default/production invocation path (`scanner.get_universe()`
with no override) is unaffected, but the documented debug workflow
(`--tickers PETR4,VALE3 ...`) is a plausible vector, and the diagnosis document
this very fix is built on is full of `.SA`-suffixed symbols an operator could
copy-paste.

**OPTGATE-01** (`options_provider_mydata.py` gate) correctly implements the
documented hard-refusal-not-soft design: the gate is checked once before the
first network call reserving capacity for both calls in the chain
(`get_vencimentos` + `get_options_chain`), `_debita()` sits immediately before
each of the two network calls (no call site bypasses it — verified there are
no other callers of `mydata_client.get_vencimentos`/`get_options_chain` in the
codebase), a cota refusal never touches the network and is never cached (A-07,
tested), and `agent.py`'s `_avaliar_opcoes`/`_option_quotes` degrade cleanly on
a gate refusal (`providerStatus != "ok"` → skip, no exception, no tight retry
loop — confirmed by `test_ciclo_com_orcamento_estourado_nao_trava_nem_executa`).
This correctly diverges from `candle_provider`'s soft-refusal-on-last-link
pattern, as intended (not flagged as a bug per the task brief). The one gap
worth naming is a pre-existing, now-duplicated architectural pattern: the
budget check-then-debit sequence in `mydata_budget.py` has no locking, so
concurrent HTTP requests hitting different tickers could both pass `_gate(2)`
before either debits, jointly overspending the shared quota — see WR-01.

## Critical Issues

### CR-01: `signal_ledger_bootstrap.py` writes the ledger key from un-normalized input, silently fragmenting a ticker's historical series

**File:** `server/app/signal_ledger_bootstrap.py:153-158` (loop inside `executar()`), root cause at `server/app/signal_ledger_bootstrap.py:211` (`main()`'s `--tickers` parsing)

**Issue:** `ledger_tickers.resolver(ticker)` normalizes its **input** internally
(`tk = normalize_ticker(ticker)`) to look up `ALIASES`/`EXCLUIDOS`, and for
alias hits it correctly returns the clean, hardcoded alias symbol (e.g.
`"MBRF3"`) to fetch. But the *outer* loop in `executar()` keeps using the
caller-supplied, **un-normalized** `tk` as both the "excluded" report key and,
critically, as the argument passed to `bootstrap_ticker(conn, tk, ...)` →
`signal_replay.replay(tk, ...)` → the row's `ticker` column in
`signal_ledger` — i.e. the actual **ledger write key**.

`scanner.get_universe()` (the default, no-argument invocation path documented
in the runbook) already normalizes every ticker before returning it (both the
hardcoded `DEFAULT_UNIVERSE` list and the env/query override path), so the
default production bootstrap is not affected today. But `main()`'s own
`--tickers` CLI parsing only does `.strip().upper()` — it does **not** strip a
`.SA` suffix or otherwise call `tickers.normalize_ticker()`. This CLI flag is
explicitly documented as the supported debug workflow in
`docs/OPERACAO-ledger-de-sinais.md` §3 (`--tickers PETR4,VALE3 --anos 1
--dry-run`), and the diagnosis document this whole fix is built on
(`docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md`) is full of `.SA`-suffixed
symbols (`MBRF3.SA`, `EMBJ3.SA`, `CPLE3.SA`, ...) that an operator debugging a
specific ticker could plausibly copy-paste straight into `--tickers`.

Reproduced directly against the real module:

```
CLI-parsed tickers (main()): ['PETR4.SA', 'MRFG3.SA']
tk='PETR4.SA' -> simbolo='PETR4' razao=None
  write-key used by bootstrap_ticker/signal_replay.replay: 'PETR4.SA'  (NOT normalized)
tk='MRFG3.SA' -> simbolo='MBRF3' razao=None
  write-key used by bootstrap_ticker/signal_replay.replay: 'MRFG3.SA'  (NOT normalized)
```

The network fetch always goes to the right symbol (`MBRF3` for the alias
case), but a non-`--dry-run` run would write those rows under the ledger key
`"MRFG3.SA"` — a *different* key from the canonical `"MRFG3"` that every other
run (past and future, via the default path) writes under. This violates the
explicit invariant `ledger_tickers.py`'s own module docstring states as the
reason this whole map is safe to exist ("a chave do ledger nunca muda").

Verified mechanism (read `server/app/signal_ledger.py:134-182`,
`agregar_cumulativo`/`agregar_janela`): both aggregations `GROUP BY setup`
only — `ticker` is not part of the grouping key, so a dirty-keyed row still
counts toward its setup's aggregate `n`. The actual failure mode is therefore
not "the ticker's sub-sample gets split off" but **idempotency defeat**: the
`UNIQUE(ticker, setup, lado, data_sinal)` constraint no longer recognizes a
later clean rerun (default path, no `--tickers`) as a duplicate of the
earlier dirty-keyed rows, because `"MRFG3.SA"` and `"MRFG3"` are different
keys. The same underlying signals for that ticker get inserted twice — once
under each key — and both copies count toward the setup's `n` in
`agregar_cumulativo`/`agregar_janela`, inflating the apparent sample size
with non-independent evidence and skewing `expR`/`acerto` for that setup by
whatever bias that ticker's re-counted signals carry. This is exactly the
kind of silent measurement corruption this task asked to rule out — no
error, no warning is raised, and no current test catches it (existing tests
only exercise already-clean ticker strings like `"TESTOR3"`).

**Fix:** Normalize at the single shared entry point (`executar()`'s loop) so
the write key is canonical regardless of how the caller supplied it —
defends both the CLI path and any future caller:

```python
# server/app/signal_ledger_bootstrap.py
from . import db, ledger_tickers, scanner, signal_ledger, signal_replay, yahoo
from .tickers import normalize_ticker  # add

async def executar(conn, tickers: list, anos: float, rng: str,
                    concorrencia: int = 4, dry_run: bool = False) -> dict:
    ...
    tickers_ativos = []
    for tk_raw in tickers:
        tk = normalize_ticker(tk_raw)
        simbolo, razao = ledger_tickers.resolver(tk)
        if razao is not None:
            resumo["excluidos"].append({"ticker": tk, "razao": razao})
            continue
        tickers_ativos.append((tk, simbolo))
```

Add a regression test exercising a dirty `--tickers`-style input (e.g.
`"petr4.sa"` or `"MRFG3.SA"`) through `executar()` and asserting the row
lands under the normalized key (`"PETR4"` / `"MRFG3"`), not the raw one.

**Fixed post-review (commit `6e640dc`):** applied exactly the suggested fix —
`executar()` now normalizes `tk_bruto → tk` via `normalize_ticker()` before
calling `ledger_tickers.resolver()`, so the normalized value flows through
`tickers_ativos`, the ledger write key, and `resumo["erros"]`. Guardian test
added: `test_executar_ticker_bruto_nao_normalizado_grava_sob_chave_normalizada`
(input `"petr4.sa"` → asserts fetch and write both use `"PETR4"`). Canonical
suite green twice post-fix (1540 passed/1 skipped both runs).

## Warnings

### WR-01: Budget gate check-then-debit is not atomic under concurrency (duplicated pattern, no lock)

**File:** `server/app/options_provider_mydata.py:128-152` (`_gate`/`_debita`), `server/app/mydata_budget.py:120-134` (`pode_gastar`/`debita`)

**Issue:** `get_options()` calls `_gate(2)` once, then issues up to two
sequential `_debita()` calls (one per network call). `mydata_budget.pode_gastar()`
reads in-memory counters and `debita()` mutates them with no lock (`asyncio.Lock`
or otherwise) between the check and the mutation. Under FastAPI's threaded/async
concurrency, two simultaneous `/api/options` requests for different tickers (or
one HTTP request racing the agent's `scheduler_loop`) can both observe
`pode_gastar(2) == True` against the same remaining headroom before either has
debited, jointly overspending the 60/min or 2000/day cap that this gate exists
to enforce. This is not a new architectural pattern — `brapi_budget.py` and
`candle_provider._gate`/`_debita` have the same gap — but this change
duplicates the gap into a second consumer (options) without addressing it, and
the docstring's stated goal ("recusa DURA... o gate nunca protegeria nada" if
soft) is undercut by a TOCTOU window that lets concurrent callers each believe
they have headroom.

**Fix:** Not blocking for this phase given it mirrors an existing, accepted
codebase pattern, but worth a follow-up: wrap `pode_gastar()`+`debita()` in a
single `asyncio.Lock`-guarded "reserve" operation in `mydata_budget.py` (shared
by both `candle_provider` and `options_provider_mydata`), or accept the
current best-effort headroom as a soft budget with the hub's own 429 as the
hard backstop, and say so explicitly in the module docstring so a future
reader doesn't assume the local counter is authoritative under load.

## Info

### IN-01: Unreachable `raise ultimo_erro` in `carregar_candles`

**File:** `server/app/signal_ledger_bootstrap.py:101`

**Issue:** The `for` loop in `carregar_candles` always exits via an explicit
`return` (success) or `raise` (last attempt, or non-retryable exception) inside
the loop body — the trailing `raise ultimo_erro` after the loop can never
execute. It's already marked `# pragma: no cover — inalcançável`, so this is
purely a readability note, not a functional defect.

**Fix:** No action required; the existing comment already documents the
intent (satisfying "a function that always returns/raises" without relying on
an unreachable-code linter warning). Optional: replace with
`raise RuntimeError("carregar_candles: estado inalcançável") from ultimo_erro`
if a future refactor wants the dead branch to fail loudly instead of silently
if the loop's invariant is ever broken.

---

_Reviewed: 2026-08-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
