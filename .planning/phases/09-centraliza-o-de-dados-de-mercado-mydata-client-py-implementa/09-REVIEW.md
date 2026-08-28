---
phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa
reviewed: 2026-08-27T00:00:00Z
depth: standard
files_reviewed: 22
files_reviewed_list:
  - docs/MEDICAO-Mydata-2026-08-27.md
  - docs/adr/019-cotahist-diario-b3.md
  - docs/adr/020-centralizacao-de-dados-no-mydata.md
  - scripts/medir-mydata.py
  - server/app/agent.py
  - server/app/candle_provider.py
  - server/app/db.py
  - server/app/main.py
  - server/app/mydata_budget.py
  - server/app/mydata_client.py
  - server/app/options_api.py
  - server/app/options_provider.py
  - server/app/options_provider_mydata.py
  - server/app/rbac.py
  - server/tests/test_candle_provider.py
  - server/tests/test_mydata_budget.py
  - server/tests/test_mydata_client.py
  - server/tests/test_mydata_provider.py
  - server/tests/test_options_provider.py
  - server/tests/test_options_provider_mydata.py
  - web/src/App.jsx
  - web/src/disclaimers.js
  - web/src/version.js
findings:
  critical: 1
  warning: 2
  info: 1
  total: 4
status: issues_found
---

# Phase 9: Code Review Report

**Reviewed:** 2026-08-27
**Depth:** standard
**Files Reviewed:** 22
**Status:** issues_found

## Summary

Phase 9 adds `mydata_client.py` (HTTP client for the `mydata.acamerini.app` hub),
`mydata_budget.py` (60/min · 2000/day rate accounting), wires a new
`MydataProvider` into the existing `candle_provider` fallback chain
(mydata→brapi→Yahoo), adds `options_provider_mydata.py`/`options_provider.py`
as a D-04-compliant options adapter/selector, and retires the parallel
`b3_historical.py` COTAHIST ingestion module in favor of the hub. The removal
commit (`ce1c207`) is clean — additive-only DB changes, no `DROP TABLE`, RBAC
entity reverted correctly, module + tests `git rm`'d with the historical
commit preserved for recovery, matching the commit message's own claims. Test
coverage for `mydata_client`/`mydata_budget`/the candle-chain gate/the
options adapter is thorough and offline (fake `fetch_json`/`httpx.AsyncClient`
injection throughout, no live network in tests). Credential handling is
correct: `X-API-Key` header only, never logged, `base_url()` refuses non-TLS
except localhost, 401/403 messages never include the token value (verified by
a dedicated guardian test).

Documentation quality is unusually high for this phase — ADR-020 and
`docs/MEDICAO-Mydata-2026-08-27.md` proactively document the exact gap named
in this review's brief (options path has no rate-budget gate) and an
independently-discovered pico/min capacity shortfall (148 of 60/min
projected), and the checkpoint commit (`9aa5e5f`) confirms neither
`B3_CANDLE_PROVIDER` nor `B3_OPTIONS_PROVIDER` was flipped to `mydata` in
production — both stay at their safe defaults (`yahoo`/`brapi`) pending those
fixes. That said, one fresh, config-independent logic bug was found in
`mydata_client.get_vencimentos()` that silently converts a subset of real API
errors into a false "no data" result — a direct violation of CLAUDE.md
principle 4 (never invent/mask a failed data fetch as a legitimate empty
state). One user-facing/comment provenance inaccuracy was also found in the
front-end text added this phase.

## Critical Issues

### CR-01: `mydata_client.get_vencimentos()` silently converts real API errors into "no options published"

**File:** `server/app/mydata_client.py:226-242` (root cause in `_fetch_json`, lines 78-128)

**Issue:** `_fetch_json()` only special-cases HTTP `429`, `401`/`403`, and `>=500`
(lines 98, 112, 118). Every other status code — including client errors like
`400`/`404`/`422` that a REST API commonly returns for a malformed ticker,
bad `pregao` date, or validation failure — falls through to
`try: return r.json()` (lines 123-127) and is returned as if it were a
successful payload, with no signal that the request actually failed.

Two of the three call sites are protected from this by a downstream
structural check: `_paginar()` (used by `get_history()` and
`get_options_chain()`) requires `isinstance(resp.get("dados"), list)` and
raises `MydataIndisponivel("resposta inesperada")` if that shape is missing
(line 147-148) — an error envelope like `{"erro": {...}}` (the shape used by
the 429/401/403 paths, confirmed in `test_429_nao_faz_retry_...`/
`test_401_nao_faz_retry_...`) fails that check and correctly raises.

`get_vencimentos()` does **not** go through `_paginar()` — it does its own,
weaker check:
```python
resp = await fetch(f"/v1/opcoes/{symbol}/vencimentos", params)
if not isinstance(resp, dict):
    raise MydataIndisponivel(...)
return resp.get("dados") or []
```
An error envelope `{"erro": {"codigo": ..., "mensagem": ...}}` **is** a
`dict`, so it passes the `isinstance` check; `.get("dados")` on it is `None`,
and `or []` silently converts that into an empty list. This list then flows
straight into `options_provider_mydata.get_options()`:
```python
venc = await mydata_client.get_vencimentos(t)
if not venc:
    payload = _empty_payload(
        ticker, expiration,
        "Nenhum pregão publicado com opções para este ativo no "
        "acervo oficial da B3.")
    ...
    return payload
```
The end user is told "no options published for this asset in the B3 official
archive" when the actual cause was an HTTP-level failure (bad request,
validation error, or any future status code the hub adds that isn't
429/401/403/5xx) — no `providerError` is set, so there is no way to
distinguish this from the legitimate "this stock genuinely has no options"
case. This directly contradicts CLAUDE.md principle 4 ("Se a fonte de dados
falhar... não invente valores. Mostre o estado correto") and the module's
own stated intent ("ausência de negócio, não erro" is only true for the
*real* `{"dados": []}` 200 response, not for a masked error).

No test in `test_mydata_client.py` exercises a non-JSON-error, non-401/403/429,
non-5xx status code for `get_vencimentos()` — the gap in behavior has a
matching gap in test coverage.

**Fix:** Give `get_vencimentos()` the same structural guard `_paginar()`
already has (reject any envelope without a `dados` key present, rather than
defaulting a missing key to `[]`), or better, make `_fetch_json()` validate
`200 <= r.status_code < 300` explicitly and raise `MydataIndisponivel` for
anything else before attempting to interpret the body as a success payload:
```python
if not (200 <= r.status_code < 300):
    corpo = None
    try:
        corpo = r.json()
    except ValueError:
        corpo = None
    erro = (corpo or {}).get("erro") if isinstance(corpo, dict) else None
    detalhe = f": {erro}" if erro else ""
    raise MydataIndisponivel(f"mydata HTTP {r.status_code}{detalhe}")
```
placed once, centrally, before the current `try: return r.json()` — this
closes the gap for every current and future call site, not just
`get_vencimentos()`.

## Warnings

### WR-01: Options path (`options_provider_mydata.py`/`options_provider.py`) has no rate-budget gate — and it now feeds the autonomous agent cycle, not just the UI

**File:** `server/app/options_provider_mydata.py` (whole file), `server/app/options_provider.py:39-46`

**Issue:** Already identified in this phase's own documentation
(`docs/MEDICAO-Mydata-2026-08-27.md` §3 "Achado 2" and ADR-020 §Consequências,
"Paga-se") — confirmed correct by reading the code: neither
`options_provider_mydata.get_options()` nor `options_provider.py` ever calls
`mydata_budget.pode_gastar()`/`debita()`. Only `candle_provider.get_history()`
(via `_gate`/`_debita`, Plano 09-02) has a budget gate. Unlike the candle
path, a burst of options requests (many distinct tickers/expirations opened
concurrently) has **zero** local rate limiting against the shared
60/min · 2000/day production key.

This gap is currently dormant: `B3_OPTIONS_PROVIDER` defaults to `"yahoo"`,
and the checkpoint commit (`9aa5e5f`) confirms production has not been
switched to `mydata` for either candles or options, pending exactly this
fix (and the related pico/min capacity shortfall). It is correctly *not* a
BLOCKER on that basis.

What is new in this review's severity assessment: `server/app/main.py`
(commit `d517755`) wired `options_provider.get_options` into
`agent_mod.run_cycle_for(..., option_quotes_getter=options_provider.get_options)`
at every call site — `cycle()`, `agent_run_now()`, `_disparar_ciclo_imediato()`,
and `_start_agent_scheduler()`. This means that once `B3_OPTIONS_PROVIDER=mydata`
is activated, the ungated option-quote fetch runs automatically on
**every scheduler tick, for every user with an open option position**, with
no human interaction and no per-request throttle — not just when a user
happens to browse the options chain screen. The 300s in-module cache
(`_OPTIONS_TTL`) only dedupes repeated fetches of the *same*
`(ticker, expiration)` pair; it does nothing to bound the number of
*distinct* pairs fetched in a burst across all users' positions on a single
agent cycle. This raises the real blast radius of the already-known gap
beyond what the existing docs describe (which frame it mostly in terms of
"usuários abrindo cadeias distintas" in the UI).

**Fix:** Before flipping `B3_OPTIONS_PROVIDER=mydata` in production (already
tracked as a pre-condition in ADR-020 §Medição/Plano de ação, item 3), add the
same `_gate`/`_debita` pattern `candle_provider.py` uses, applied per distinct
`(ticker, expiration)` fetch in `options_provider_mydata.get_options()`, and
make sure the agent's scheduler path degrades to `providerStatus="degraded"`
(already the D-04 behavior on `MydataIndisponivel`) rather than blocking the
cycle when the budget is exhausted.

### WR-02: Front-end comment and user-facing copy misstate that spot-quote lookups route through mydata

**File:** `web/src/App.jsx:3115-3118`, `web/src/App.jsx:6621-6623`

**Issue:** Two places added in this phase's front-end commit (`c90b102`)
describe `candle_provider.get_quote()` as routing "mydata→brapi→Yahoo em
cadeia":
```jsx
// ADR-008/ADR-020: princípio #3 do CLAUDE.md — dado de
// mercado exibe a FONTE. `source` vem em todo payload
// de candle_provider (mydata→brapi→Yahoo em cadeia);
// sem isso a tela nunca dizia de onde o preço veio.
{!q.error && q.change != null && q.source && (
  <div ...>{FONTE_LABEL(q.source)}</div>
)}
```
and, in `CatalogModal`:
```jsx
// consulta candle_provider.get_quote, hoje mydata→brapi→Yahoo em
// cadeia (ADR-008/ADR-020), não mais só Yahoo.
<div ...>Adicionar outro ativo da B3 — digite o código; a existência é
  confirmada no provedor de cotações (mydata/brapi/Yahoo).</div>
```
This is factually wrong for `get_quote()`/`get_quotes()`: reading
`server/app/candle_provider.py:490-556`, the spot-quote functions only ever
route between `"brapi"` and `"yahoo"` (`if provider_name() == "brapi": ...
else: yahoo...`) — `mydata` never appears in that code path; only
`get_history()` (the candle/period path) routes through the
mydata→brapi→Yahoo chain. The comment at `App.jsx:3115-3118` is also
attached to the wrong branch: it precedes the `q.change != null` block (the
*live spot* quote, sourced only from brapi/yahoo), while the block that
actually is candle-derived (`q.changePeriodo`, lines 3110-3113, "no período ·
fechamento") sits just above it, undocumented.

The `CatalogModal` text is user-facing and describes data provenance
(CLAUDE.md principle 3: "Dados de mercado exibem fonte... horário da última
atualização") — telling the user that ticker existence is confirmed against
mydata when it never is misrepresents where that check actually happens.

**Fix:** Correct both comments to say the live-quote path is brapi→Yahoo only
(unchanged by this phase), and reserve "mydata→brapi→Yahoo em cadeia" language
for text that actually describes `get_history()`. In `CatalogModal`, change
"confirmada no provedor de cotações (mydata/brapi/Yahoo)" to
"(brapi/Yahoo)" or drop the parenthetical enumeration entirely.

## Info

### IN-01: `mydata_budget.aguarda_vaga()` is fully implemented and tested but never called from production code

**File:** `server/app/mydata_budget.py:147-164`

**Issue:** `aguarda_vaga()` is a documented async pacer ("Pacer assíncrono
para o consumidor em lote (Plano 09-02)") with two dedicated unit tests
(`test_mydata_budget.py:114-122`), but a repo-wide search shows it is never
imported or called from any non-test module — `candle_provider.py` uses the
synchronous `pode_gastar()`/`debita()` pair instead, and there is no batch
consumer wired to it. This isn't wrong by itself, but it is exactly the kind
of mechanism that `docs/MEDICAO-Mydata-2026-08-27.md` §8 (Plano de ação,
item 1) says is still missing before the pico/min capacity shortfall (148 of
60/min projected) can be resolved — the pacer exists, but nothing calls it.

**Fix:** Either wire `aguarda_vaga()` into the scanner's provider-sensitive
throttle (the mitigation ADR-020/MEDICAO already names as the path forward),
or, if the intended mitigation ends up being a different mechanism, remove
`aguarda_vaga()` to avoid carrying tested-but-unused surface area.

---

_Reviewed: 2026-08-27_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
