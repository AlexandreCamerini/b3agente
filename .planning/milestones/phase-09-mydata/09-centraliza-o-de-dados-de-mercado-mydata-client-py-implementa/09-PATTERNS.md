# Phase 9: Centralização de dados de mercado (mydata_client.py) - Pattern Map

**Mapped:** 2026-08-27
**Files analyzed:** 8 (new + modified)
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `server/app/mydata_client.py` (NEW) | service (HTTP client) | request-response | `server/app/brapi.py` (async client shape) + `server/app/fundamentals.py` (auth header, cache TTL) | role-match (blend of two) |
| `server/app/candle_provider.py` (MODIFIED — add `MydataProvider`) | provider adapter | request-response | `BrapiProvider`/`YahooProvider` classes, same file lines 163-187 | exact |
| `server/app/options_provider_mydata.py` (NEW, name at planner's discretion) | provider adapter | request-response | `server/app/options_provider_yahoo.py` (full file) | exact |
| `server/app/options_api.py` (MODIFIED — swap import) | route/consumer | request-response | same file, lines 10, 100, 112, 146 (existing call sites) | exact |
| `server/app/mydata_budget.py` (NEW, conditional — see Claude's Discretion in CONTEXT.md) | service (rate-limit tracker) | CRUD (counter) | `server/app/brapi_budget.py` | exact |
| `server/app/agent.py::scheduler_loop` (MODIFIED — daily refresh hook) | scheduler hook | batch/event-driven | same file lines 1163-1170 (`b3_historical.maybe_run` hook) | exact |
| `server/tests/test_mydata_client.py` (NEW) | test | request-response | `server/tests/test_b3_historical.py` + `brapi.py`'s `fetch_json` injection idiom | role-match |
| Env var config (`MYDATA_URL`/`MYDATA_TOKEN`, cross-cutting) | config | n/a | `BRAPI_TOKEN` (`brapi.py:54-55`) / `BOLSAI_API_KEY` (`fundamentals.py:55-58`) | exact |

## Pattern Assignments

### `server/app/mydata_client.py` (NEW — service, request-response)

**Primary analog:** `server/app/brapi.py` (async httpx client shape, retry, error types)
**Secondary analog:** `server/app/fundamentals.py` (auth header style, TTL cache via `db.kv_get`/`kv_set`)

**CRITICAL — auth header is `X-API-Key`, NOT Bearer.** Verified against the actual mydata source
(`~/dev/cvm-financas/app/api/main.py:137`, `exigir_chave` reads
`x_api_key: str | None = Header(default=None, alias="X-API-Key")`) and the mydata test fixture
(`~/dev/cvm-financas/tests/test_api_opcoes.py:44`, `c.headers.update({"X-API-Key": emitida.chave_completa})`).
So `mydata_client.py` must follow `fundamentals.py`'s header pattern, not `brapi.py`'s Bearer pattern.

**Imports pattern** (`brapi.py` lines 15-22, adapt module names):
```python
import asyncio
import os
import time

import httpx

from .tickers import normalize_ticker
```

**Env/token pattern** (`fundamentals.py` lines 55-58 — `X-API-Key` precedent):
```python
def _bolsai_key() -> Optional[str]:
    """Chave da bolsai via env (Railway). Ausente → cai no brapi."""
    k = (os.environ.get("BOLSAI_API_KEY") or "").strip()
    return k or None
```
Apply the same shape for `MYDATA_TOKEN` (and `MYDATA_URL` for the base, default
`https://mydata.acamerini.app`, per `docs/deploy-railway.md` referenced in CONTEXT.md).

**HTTP fetch with header auth + timeout** (`fundamentals.py` lines 312-318 — closest existing
X-API-Key example; adapt to `async with httpx.AsyncClient`):
```python
def _fetch_bolsai_raw(ticker: str, api_key: str) -> dict:
    """I/O da bolsai (fonte primária). Header X-API-Key obrigatório."""
    r = httpx.get(BOLSAI_BASE + ticker.upper(),
                  headers={"X-API-Key": api_key, "User-Agent": "Boris+/qa36"},
                  timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()
```

**Retry + rate-limit header capture pattern** (`brapi.py` lines 83-105 — reuse the retry loop shape,
swap `Authorization: Bearer` for `X-API-Key`):
```python
async def _fetch_json(symbol: str, params: dict) -> dict:
    """GET com Bearer e retry curto (2 tentativas em timeout/5xx)."""
    headers = {"Authorization": "Bearer " + _token()}
    last = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
                r = await client.get(BASE + symbol, params=params, headers=headers)
            for h in ("x-ratelimit-limit", "x-ratelimit-remaining"):
                if h in r.headers:
                    LAST_RATELIMIT[h] = r.headers[h]
            if r.status_code >= 500:
                last = BrapiIndisponivel(f"brapi HTTP {r.status_code}")
            else:
                try:
                    return r.json()
                except ValueError:
                    raise BrapiIndisponivel(f"brapi HTTP {r.status_code} com corpo não-JSON")
        except httpx.HTTPError as e:
            last = BrapiIndisponivel(f"brapi inacessível: {e!r}")
        await asyncio.sleep(0.4 * (attempt + 1))
    raise last
```
mydata does NOT surface `x-ratelimit-*` headers in the endpoints read (`main.py:596-770` uses `ETag`/
`Cache-Control` instead, not rate-limit headers) — the retry/error-wrapping shape transfers, the
rate-limit-header capture block does not. A `MydataIndisponivel(RuntimeError)` exception class,
mirroring `BrapiIndisponivel`, is the right shape for transient failures.

**Error handling / custom exception classes** (`brapi.py` lines 43-51):
```python
class BrapiIndisponivel(RuntimeError):
    """Falha transitória ou resposta imprestável — quem chama decide degradar."""

class ForaDoPlano(ValueError):
    """Pedido que o plano contratado não cobre..."""
```
mydata has no "fora do plano" concept in the endpoints read (no distinct free-tier range/interval
restriction like brapi's `PLAN_INTERVALS`/`PLAN_RANGES`) — only `MydataIndisponivel` is needed, not
a `ForaDoPlano` equivalent.

**429/quota-exceeded shape — CONFIRMED** (`~/dev/cvm-financas/app/api/main.py:139-163`, the
`exigir_chave` dependency that gates every route):
```python
quota = auth.consumir_quota(sink, chave)
response.headers["X-Quota-Limite"] = str(quota["limite"])
response.headers["X-Quota-Restante"] = str(quota["restante"])
if not quota["ok"]:
    raise HTTPException(
        status_code=429,
        detail={"codigo": "quota_excedida",
                "mensagem": f"Quota por {quota['janela']} esgotada."},
        headers={"Retry-After": "60" if quota["janela"] == "minuto" else "3600"},
    )
```
So `mydata_client.py` gets `X-Quota-Limite`/`X-Quota-Restante` on EVERY response (not just on
429 — same style as brapi's `x-ratelimit-*` capture at `brapi.py:91-93`, reuse that capture idiom)
and a `Retry-After` header on 429 distinguishing minute- vs. day-window exhaustion via
`detail.codigo == "quota_excedida"` + `detail.mensagem`. This is exactly what a `MydataBudget`
(if built) should reconcile against, mirroring how `brapi_budget.snapshot()` exposes
`headerRateLimit` (`brapi_budget.py:184-185`) as "verdade > previsão" alongside the local counter.

**Field mapping — `GET /v1/cotacoes/{ticker}` → candle dict.** Confirmed against
`~/dev/cvm-financas/app/seed_fontes.py:908-923` (the `gold_cotacoes` view definition) and
`~/dev/cvm-financas/tests/test_api_opcoes.py:146-150` (live field names in the JSON response):
```
mydata field (gold_cotacoes)   → CandleProvider candle dict field
dt_pregao                      → date          ("AAAA-MM-DD", already ISO)
preco_abertura                 → open
preco_maximo                   → high
preco_minimo                   → low
preco_fechamento                → close
quantidade_negociada            → volume        (share count — matches brapi.py's `v.get("volume")`
                                                  convention, NOT volume_financeiro which is R$ notional)
(no currency field)             → currency: "BRL" (hardcoded default, same as brapi.py/yahoo.py)
hv21, hv63                     → available but NOT part of the CandleProvider contract — extra
                                  fields the planner may choose to surface elsewhere (e.g. skip
                                  local HV recompute in options_api.py's `_technical_context`)
```
Response envelope is `{"dados": [...], "proximo_cursor": ...}` with cursor pagination (`limite` up
to 2000 pregões) — NOT a flat list like brapi/Yahoo. `mydata_client.py`'s candle-history function
needs to walk `proximo_cursor` until exhausted or until the requested range is covered — no existing
Boris module does cursor pagination; closest structural precedent is `b3_historical.py`'s
`import_daily`/`get_status` idempotent-fetch loop shape (page-until-done), not cursor pagination
itself. **No analog for cursor-walking exists in this repo — flag as new pattern for the planner.**

**Field mapping — `GET /v1/opcoes/{ticker}` → options contract.** Confirmed against
`~/dev/cvm-financas/app/seed_fontes.py:924-971` (`gold_opcoes` view) and
`~/dev/cvm-financas/tests/test_api_opcoes.py:51-71` (live field names):
```
mydata field (gold_opcoes)      → options_provider_yahoo.py contract field
contrato                        → contractSymbol
tipo ("CALL"/"PUT", uppercase)  → optionType ("call"/"put", lowercase — needs .lower())
strike                          → strike
premio                          → lastPrice
melhor_oferta_compra            → bid
melhor_oferta_venda             → ask
quantidade_negociada             → volume
volatilidade_implicita          → impliedVolatility  (nullable — ~10% of contracts, per
                                                        contrato-consumidor.md item 4; treat as
                                                        legitimate null, NOT an error)
preco_teorico                   → (no current field — BSM already computed server-side by mydata;
                                    options_api.py's own `black_scholes()`/`_enrich_contract()`
                                    recomputes this locally today — planner must decide whether to
                                    keep double computation or trust mydata's `preco_teorico`)
delta, gamma, vega, theta, rho  → (no current field — Yahoo path has NO greeks; options_quant.py's
                                    black_scholes() computes them locally. mydata provides them
                                    pre-computed. Planner decision: consume mydata's greeks directly
                                    vs. keep local BSM recompute for parity with old contract shape)
preco_objeto                    → underlyingPrice (top-level, not per-contract)
dt_vencimento                   → expiration (top-level, echo of query param or resolved default)
n/a                             → openInterest — **NO ANALOG / NO SOURCE FIELD.** B3's COTAHIST does
                                    not publish open interest; gold_opcoes has no equivalent column.
                                    `liquidity_score()` (options_quant.py) takes openInterest as an
                                    input — MydataOptionsProvider will have to pass 0/None, which
                                    degrades liquidity scoring vs. today. Flag for planner/product.
n/a (isin present, not currency) → currency — not in gold_opcoes; default "BRL" same as candles.
proveniencia.{sha256,dt_captura, → NOT part of options_provider_yahoo.py's contract today. New,
  arquivo,arquivo_em}              free upside (data provenance) — planner may want to surface
                                    this in `providerStatus`/`source` metadata since ADR-004's
                                    contract doesn't currently carry it.
```
Response envelope: `{"dados": [...], "proximo_cursor": ...}`, filterable server-side by
`vencimento`, `pregao`, `tipo` query params — unlike Yahoo's single nested payload with
`expirationDates`/`options[0]`. **Expirations list comes from a SEPARATE endpoint**
(`GET /v1/opcoes/{ticker}/vencimentos`, returns `[{dt_vencimento, contratos, com_sigma,
vence_no_pregao, menor_strike, maior_strike}]`) — `options_api.py`'s `/expirations/{ticker}` route
(line 94-103) must call this second endpoint, not derive expirations from the chain response like
Yahoo does today.

---

### `server/app/candle_provider.py` (MODIFIED — add `MydataProvider`)

**Analog:** `BrapiProvider`/`YahooProvider`, same file (lines 163-187)

**Exact shape to copy** (lines 174-187):
```python
class BrapiProvider(CandleProvider):
    """Era o plano B do ADR-001; implementado como fonte MASTER de diário/spot
    pelo ADR-008..."""

    nome = "brapi"

    async def history(self, ticker: str, rng: str, interval: str = "1d") -> dict:
        return await brapi.get_history(ticker, rng=rng, interval=interval)
```
`MydataProvider` follows identically: `nome = "mydata"`, `history()` delegates to
`mydata_client.get_history(ticker, rng=rng, interval=interval)`. Register in `_PROVEDORES` dict
(line 189: `_PROVEDORES = {"yahoo": YahooProvider, "brapi": BrapiProvider}`) as
`"mydata": MydataProvider`. `B3_CANDLE_PROVIDER=mydata` then activates it via the existing
`provider_name()`/`get_provider()` machinery (lines 193-207) — zero other call sites change
(this is D-01's entire point: `get_history()` at line 271 stays the single entry point).

**Fallback chain wiring** (D-03 — falls back to brapi, then Yahoo, on failure): the existing
`get_history()` router (lines 271-322) already does this generically via `get_provider()` +
`get_fallback()` — no new branching logic needed, only `fallback_name()` (line 221-228) needs its
default-chain assumption revisited if the planner wants `mydata → brapi → yahoo` as a two-hop
fallback (today `get_fallback()` only supports ONE fallback provider, not a chain). **Flag for
planner:** current `_fallback`/`fallback_name()` design is single-hop; a two-hop chain
(mydata→brapi→yahoo) requires either extending this mechanism or accepting single-hop
(mydata→brapi, no further Yahoo fallback) as scope for this phase.

---

### `server/app/options_provider_mydata.py` (NEW — provider adapter, request-response)

**Analog:** `server/app/options_provider_yahoo.py` (full file, 143 lines)

**Contract shape to preserve exactly** (lines 45-59, `_empty_payload`):
```python
def _empty_payload(ticker: str, symbol: str, expiration: Optional[str], warning: str, error: Optional[str] = None) -> dict:
    payload = {
        "ticker": ticker,
        "symbol": symbol,
        "expirations": [],
        "expiration": expiration,
        "calls": [],
        "puts": [],
        "source": "yahoo",
        "providerStatus": "degraded",
        "warning": warning,
    }
    if error:
        payload["providerError"] = error
    return payload
```
`MydataOptionsProvider`'s degraded-payload function is identical except `"source": "mydata"`. Per
D-04, **no fallback to Yahoo on failure** — any mydata error goes straight to this degraded shape
(the function above already does exactly that; no new branching needed, just point it at mydata
instead of Yahoo).

**Contract mapping function** (lines 62-86, `_clean_contract` — reuse this shape, feed it mydata's
`gold_opcoes` fields per the mapping table above instead of Yahoo's `optionChain` raw dict):
```python
def _clean_contract(raw: dict, option_type: str, spot: Optional[float]) -> dict:
    strike = raw.get("strike")
    last = raw.get("lastPrice")
    ...
    dist = None
    if isinstance(spot, (int, float)) and spot > 0 and isinstance(strike, (int, float)):
        dist = round((float(strike) - float(spot)) / float(spot) * 100, 2)
    return {"contractSymbol": ..., "optionType": option_type, "strike": strike, ...}
```

**Cache pattern** (lines 21-23, module-level TTL dict — same shape, cache key can reuse mydata's
own `pregao`/`vencimento` filters):
```python
_OPTIONS_TTL = 300
_ERROR_TTL = 60
_cache: dict[str, tuple[float, dict]] = {}
```

**providerStatus consumer contract** — unchanged; `options_api.py`'s `liquidity_gate()` (lines
136-156) already branches on `data.get("providerStatus") != "ok"` — this is the ADR-004 guardrail
CONTEXT.md says stays untouched.

---

### `server/app/options_api.py` (MODIFIED — swap import)

**Analog:** same file, current import + call sites

**Current** (line 10):
```python
from .options_provider_yahoo import get_options
```
**Target:** `from .options_provider_mydata import get_options` (or, if the planner wants
provider-selectability like candles have via `candle_provider.get_provider()`, a thin router
function — but D-02/D-04 read as "swap the implementation behind the same contract," which argues
for the simpler direct-import swap, NOT the class-based `_PROVEDORES` registry that
`candle_provider.py` uses for candles). Call sites at lines 100 (`expirations`), 112 (`chain`), 146
(`liquidity_gate`) need NO changes — they call `get_options(t, expiration)` exactly as today.

---

### `server/app/mydata_budget.py` (NEW, conditional — CONTEXT.md leaves in/out-of-scope to planner)

**Analog:** `server/app/brapi_budget.py` (full file, 301 lines)

**Memory→DB→env pattern to replicate** (lines 40-43, `configure_db`):
```python
def configure_db(conn=None, enabled: bool = True) -> None:
    global _DB_CONN, _DB_ENABLED
    _DB_CONN = conn
    _DB_ENABLED = bool(enabled and conn is not None)
```

**Persisted counter with soft/hard stop** (lines 139-167, `pode_gastar`/`debita`/`degradado`):
```python
def pode_gastar(fatia: str, now: Optional[datetime] = None) -> bool:
    """True se a chamada à brapi está autorizada agora, para esta fatia."""
    if not em_pregao(now):
        return False
    _carrega(_hoje(now))
    if _estado["total"] >= teto_dia():          # hard stop do dia
        return False
    ...
```
mydata's quota is flat (`60/min · 2.000/dia`, per `contrato-consumidor.md` line 63) — NO fatias
(slices) like brapi's spot/delta/fundamentos split, since mydata serves one client
(`mydata_client.py`) for two data types (candles + options) with a single combined quota. The
per-minute limit (`60/min`) has NO analog in `brapi_budget.py`, which only tracks a DAILY teto —
**this is a new pattern the planner must design** (a sliding-window or fixed-window per-minute
counter), not a direct copy. The daily-teto half (`2.000/dia`) copies directly from
`brapi_budget.py`'s `teto_dia()`/`_estado["total"]` shape.

**Persistence via SQLite `kv`** (lines 106-135, `_carrega`/`_persiste` — reuse verbatim shape, new
kv key prefix e.g. `"mydataBudget:" + dia`):
```python
def _persiste() -> None:
    if not _DB_ENABLED:
        return
    try:
        _DB_CONN.execute(
            "INSERT INTO kv(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (_kv_key(_estado["dia"]), json.dumps({"fatias": _estado["fatias"], "total": _estado["total"]})))
        _DB_CONN.commit()
    except Exception:  # noqa: BLE001
        pass
```

**Per CONTEXT.md's Claude's Discretion:** whether this file is even built in this phase (vs.
deferred until the rate-limit measurement TODO is closed) is an open planning decision, not a
pattern-mapping one — the pattern above is ready either way.

---

### `server/app/agent.py::scheduler_loop` (MODIFIED — daily refresh hook)

**Analog:** same file, lines 1163-1170 (the `b3_historical.maybe_run` hook) + `b3_historical.py`'s
own gate functions (lines 406-446)

**Hook wiring pattern to copy** (`agent.py` lines 1163-1170):
```python
try:
    # Acervo histórico oficial: independente do kill-switch de ordens
    # e do Radar. O job tem gate próprio e retry espaçado, portanto um
    # 404 da B3 em feriado/atraso não vira loop agressivo.
    from . import b3_historical  # import local: sem ciclo
    await b3_historical.maybe_run(conn)
except Exception as e:  # noqa: BLE001 — dado histórico não derruba ordens
    print(f"[b3-cotahist] hook do scheduler falhou: {e}")
```
`mydata_client.maybe_run(conn)` (or a new hook module) follows the exact same try/except-isolated,
import-local shape — critical invariant: a mydata refresh failure must NEVER derail the
buy/sell/stop/target cycle running in the same loop iteration (same reasoning as
`b3_historical`/`fundamentals`/`analytics` hooks already isolated here).

**Gate/retry pattern to copy** (`b3_historical.py` lines 388-434, `_hhmm`/`_retry_minutes`/
`should_run`):
```python
def should_run(conn, now: Optional[datetime] = None) -> bool:
    """Gate puro do job: só depois do fechamento, em dia de pregão e com retry."""
    from . import pregao
    now = now or datetime.now(BRT)
    if not enabled() or not pregao.is_trading_day(now.date()):
        return False
    hour, minute = _hhmm()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now < target:
        return False
    ...
```
This is the CONTEXT.md-referenced precedent ("planejador decide com base no padrão já estabelecido
em ADR-019/`b3_historical.py`") for "batch 1×/dia after close" — env var naming should follow
`B3_COTAHIST_DAILY_HHMM`/`B3_COTAHIST_RETRY_MIN` → e.g. `B3_MYDATA_DAILY_HHMM`. Note mydata's
COTAHIST ingestion already runs server-side at `mydata.acamerini.app` on its own schedule — Boris's
job here is a REFRESH/FETCH job (pull already-published data), not a re-ingestion job, so the
"404 = not yet published" semantics of `B3DailyNotAvailable` may not transfer 1:1 (mydata's
`/v1/cotacoes/{ticker}` for a date not yet ingested there would need its own not-yet-available
handling — verify against mydata's actual publish timing before copying `HHMM_DEFAULT = "20:30"`).

**What gets removed/replaced:** per CONTEXT.md ("`b3_historical.py`, aposentada por esta fase na
fatia diária"), the `b3_historical.maybe_run(conn)` call at `agent.py:1167-1168` is the removal
target once `MydataProvider` covers the daily slice — `b3_historical.py` itself is source code
(not `qa/`/`ESTADO-*`/`CHECKOUT-*`/RELEASES), so the "history is never rewritten" guardrail in
CLAUDE.md does not block deleting or deprecating it; only the historical DOCS (ADR-019 itself) stay
frozen as a record of the decision at the time.

---

### `server/tests/test_mydata_client.py` (NEW)

**Analog:** `server/tests/test_b3_historical.py` (fixture-injection idiom) + `brapi.py`'s
`fetch_json` injectable parameter (used for offline testing without network)

**Injectable I/O pattern** (`brapi.py` line 108-109, signature shape):
```python
async def get_history(ticker: str, rng: str = "1mo", interval: str = "1d",
                      *, fetch_json=None) -> dict:
```
`mydata_client.get_history`/`get_options` should take the same `fetch_json=None` (or
`fetch=None`) injectable kwarg so tests build fixture JSON payloads (shaped like the
`{"dados": [...], "proximo_cursor": ...}` envelope) without hitting the network — same idiom
`test_b3_historical.py` uses with `fetch_bytes=fetch` (lines 74-79).

**Test file naming convention:** `server/tests/test_<feature>.py`, functions
`def test_<description_in_snake_case>():` — confirmed by every analog read
(`test_b3_historical.py`, `test_brapi_budget.py`, `test_candle_provider.py`,
`test_options_provider_yahoo.py`, `test_fundamentals.py` all exist and follow this).

---

## Shared Patterns

### Secrets via env, never in bundle
**Source:** `brapi.py:54-55` (`BRAPI_TOKEN`), `fundamentals.py:55-58` (`BOLSAI_API_KEY`)
**Apply to:** `mydata_client.py` (`MYDATA_TOKEN`), any new config surface
```python
def _token() -> str:
    return (os.environ.get("BRAPI_TOKEN") or "").strip()
```
Provider-name prefix (not `B3_*`), matching CONTEXT.md's Claude's Discretion note.

### Never fabricate data on source failure
**Source:** CLAUDE.md principle 4, enforced pattern at `main.py:1509` (`HTTPException(502, ...)`
instead of a synthetic price)
**Apply to:** every mydata call site — a mydata outage must surface as a real error/degraded state
(candles fall back per D-03's existing chain machinery; options go straight to `providerStatus:
"degraded"` per D-04), never a guessed value.

### Provenance metadata is additive upside, not required parity
**Source:** mydata's `proveniencia.{sha256,dt_captura,arquivo,arquivo_em}` on every row
(`~/dev/cvm-financas/tests/test_api_opcoes.py:75-83`)
**Apply to:** `mydata_client.py`/`MydataProvider`/`MydataOptionsProvider` — `candle_cache.py`
already has a `src` field per record (line 92-99, `_db_get` selects `src` from `candle_cache`
table) that mydata's richer provenance can feed without a schema change; consider whether to also
carry `sha256`/`dt_captura` through `source` metadata for the options path, where ADR-004's
contract doesn't currently have a slot for it.

### Scheduler hooks are try/except-isolated, imported locally
**Source:** `agent.py:1148-1201` (every hook in `scheduler_loop` — analytics, automacao, metrics,
`b3_historical`, `fundamentals.maybe_warm`, `signal_ledger_job`)
**Apply to:** the mydata daily refresh hook — copy the exact `try: ... except Exception as e: #
noqa: BLE001 ... print(f"[mydata] hook do scheduler falhou: {e}")` shape, no exceptions.

## No Analog Found

| File/Concern | Role | Data Flow | Reason |
|---|---|---|---|
| Cursor-based pagination walk (`proximo_cursor`) for `/v1/cotacoes` and `/v1/opcoes` | client I/O | batch | No existing Boris module paginates a cursor-based API — brapi/Yahoo/bolsai are all single-shot fetches. Nearest structural cousin is `b3_historical.py`'s idempotent-fetch-per-day loop, but that is date-keyed, not cursor-keyed. New pattern; not a copy job. |
| Per-minute rate limit (`60/min`) tracking | service | CRUD (counter) | `brapi_budget.py` only tracks a DAILY teto, no sliding/fixed per-minute window. mydata's quota has both a per-minute AND per-day cap — the per-minute half needs new design. |
| `openInterest` field for options | data field | n/a | B3's COTAHIST does not publish open interest; `gold_opcoes` has no equivalent column. `options_quant.liquidity_score()` will receive 0/None where Yahoo used to (rarely) have real OI — a product-level tradeoff, not a code pattern gap. |

## Metadata

**Analog search scope:** `server/app/` (candle_provider.py, candle_cache.py, brapi.py,
brapi_budget.py, options_provider_yahoo.py, options_api.py, fundamentals.py, b3_historical.py,
agent.py), `server/tests/` (test_b3_historical.py, directory listing), plus the out-of-repo mydata
source (`~/dev/cvm-financas/docs/contrato-consumidor.md`, `~/dev/cvm-financas/app/api/main.py`
lines 1-100 + 596-770, `~/dev/cvm-financas/app/seed_fontes.py` lines 880-971 for view definitions,
`~/dev/cvm-financas/tests/test_api_opcoes.py` for live field names).
**Files scanned:** 9 in-repo + 4 out-of-repo (cvm-financas)
**Pattern extraction date:** 2026-08-27
