# Coding Conventions

**Analysis Date:** 2026-08-18

## Project Shape

Monorepo with three independent packages, no shared build tooling:

- `server/` — Python 3 / FastAPI backend (`server/app/*.py`), SQLite persistence.
- `web/` — Vite + React (JSX) frontend, wrapped by Capacitor for iOS (`web/src/*.js`, `*.jsx`).
- `web-admin/` — separate Vite + React admin portal, own `package.json` (`web-admin/src/`).

There is no monolithic "src/" — always specify which package (`server/app/…`, `web/src/…`, `web-admin/src/…`) when referencing a file.

## Naming Patterns

**Python (`server/app/*.py`):**
- Modules: `snake_case.py`, one module per domain concept (`brapi_budget.py`, `candle_cache.py`, `technical_snapshot.py`).
- Functions/variables: `snake_case`. Private/module-internal helpers prefixed `_` (`_eh_default_antigo`, `_call_llm`, `_spy`).
- Portuguese identifiers are common for domain concepts (`ensure_defaults`, `_eh_default_antigo`, `default_llm_prompts_ativo`) — do not force English renames; match the existing mix.
- Constants: `UPPER_SNAKE_CASE` (`SECTIONS`, `LEGACY_PROMPT_SHA256`, `FORMAT_PRO`).

**JavaScript/JSX (`web/src/*.js(x)`, `web-admin/src/*.jsx`):**
- Files: `camelCase.js`/`PascalCase.jsx` for React components (e.g. `web/src/pet/Boris.jsx`, `web-admin/src/EditorTexto.jsx`); plain modules lowercase (`persistence.js`, `catalog.js`, `finance.js`).
- Functions/variables: `camelCase`. Exported pure functions read as verbs (`portfolioMetrics`, `sizingPlano`, `dayReturnPct`).
- React components: `PascalCase` (`PetFab`, `BorisChat`, `SetorAlvo`).
- Constants: `UPPER_SNAKE_CASE` for module-level fixed values (`PROD_BASE`, `TIMEOUT_MS`, `CATALOG_TICKERS`).

**Test files:**
- Backend: `server/tests/test_<feature>.py`, functions `def test_<description_in_snake_case>():`.
- Web: `web/tests/test_<feature>.mjs` — one file per feature/bugfix, not one-per-module.

## Code Style

**Formatting:** No formatter configured (no `.prettierrc`, no `black`/`ruff` config found in `server/` or `web/`). Match surrounding style manually — the codebase favors dense, single-line conditionals and inline comments over vertical whitespace.

**Linting:** No ESLint/Biome config present in `web/package.json` or `web-admin/package.json`, and no `ruff`/`flake8`/`pylint` config in `server/`. There is no automated lint gate — correctness is enforced entirely through the test suites (see TESTING.md). Do not assume CI will catch style issues; the tests are the actual gate.

**Line length / density:** Functions frequently pack logic + comment on one line, especially in `server/app/store.py`, `web/src/api.js`, `web/src/finance.js`. This is intentional house style, not a code smell to "clean up" mid-task.

## Comments — carry decision history, not restatement

Comments in this codebase document **why**, referencing the phase/fix/ADR that motivated the code, not what the code does. Examples:

```python
# ADR-013: kill-switch do agente ganha override em runtime (admin), mesmo
# padrão memória→DB→env da brapi acima — sem isto o toggle admin nunca
# checaria o SQLite.
agent_mod.configure_db(_conn)
```

```javascript
// FASE 6 (fix 1): URL de PRODUÇÃO embutida como padrão do app NATIVO. Antes,
// sem VITE_API_BASE no build, o iPhone nascia sem endereço — login e tudo o
// mais falhava até o usuário digitar o servidor...
export const PROD_BASE = "https://boris.semente.dev";
```

**When adding code:** if a change fixes a bug, works around a platform quirk (iOS WebView, Railway, SQLite threading), or encodes a product/ADR decision, write a comment explaining the *reason*, tagged with the phase/fix id (`F10-YYYYMMDD-NN`) or ADR number if one exists. A comment that only restates the next line is not the house style and should be omitted instead.

All comments and identifiers-with-meaning are in **PT-BR**. Do not switch to English mid-file.

## Error Handling

**Backend (FastAPI, `server/app/main.py`):**
- Domain errors → `raise HTTPException(status_code, message)`, with the message as user-facing PT-BR text (`raise HTTPException(401, "Faça login para continuar.")`).
- A global handler catches anything unhandled and normalizes it to JSON instead of an opaque 500:

```python
@app.exception_handler(Exception)
async def _unhandled_exception(request: Request, exc: Exception):
    obslog.log("err", f"{request.method} {request.url.path}: {type(exc).__name__}: {exc}", level="error")
    return JSONResponse(status_code=500, content={"detail": type(exc).__name__ + ": " + (str(exc) or "erro interno")})
```
- Custom exception classes exist for domain-specific rejections (e.g. `brapi.ForaDoPlano` in `server/app/brapi.py`, tested via `pytest.raises(brapi.ForaDoPlano, match="15m")`). Prefer a named exception over a generic `ValueError` when the caller needs to branch on the failure reason.
- Never invent/estimate a value on failure — return the real error state. This is a product-level invariant from `CLAUDE.md` (item 4), not just a style preference: market-data failures must surface as errors, not fabricated numbers.

**Frontend (`web/src/api.js`):**
- All HTTP responses are read as text first (`readBody`), never `.json()` directly — the iOS WKWebView can throw a raw, unhelpful parse error on non-JSON bodies. `readBody` strips BOM/code-fences before attempting `JSON.parse`.
- `enrichErrorMessage(status, data, path)` turns a raw HTTP error into a structured, actionable message (provider/model/keySource/action/hint), consumed by the UI as `e.message`. When adding a new API-error path, populate `detail.action`/`detail.hint` server-side so the client message stays actionable instead of falling back to `"HTTP 502"`.
- Timeouts are explicit and different per call class: `TIMEOUT_MS = 15000` for regular calls, `TIMEOUT_LLM = 90000` for AI/analysis calls. Use the LLM timeout constant for any new LLM-backed endpoint, not the default.

## Async Patterns

**Backend:** the app is `async def` end-to-end in `main.py`; blocking I/O (SQLite, some HTTP libs) must not run directly on the event loop — see the memory note "Verificar endpoint + async": exercise the real endpoint and confirm no synchronous I/O landed on the loop. When adding a new async route that touches the DB or an external API, verify with a live request, not just a unit test with mocks.

**Frontend:** async/await throughout `web/src/api.js` and `persistence.js`; fetches use `fetchWithTimeout` wrapping `AbortController` so every network call is bounded.

## Module Design

**Python:** one file per domain concern under `server/app/`; `main.py` explicitly imports each module with an inline comment naming the phase/ADR that introduced it:

```python
from . import brapi_budget  # ADR-008: orçamento de requisições da brapi (Fase 2)
from . import candle_cache  # Objetivo 5: cache de candles (delta + revalida último)
```
Follow this pattern for new modules — the import comment is load-bearing documentation, not decoration.

**JavaScript:** named exports only (`export function foo() {}`), no default exports observed in `web/src/*.js`. Imports use explicit relative paths with extensions (`./catalog.js`, `./pet/Boris.jsx`) — no path aliases (`@/`) configured in `web/vite.config.js`.

**Two-store parity (invariant, not a suggestion):** `web/src/persistence.js` exports `deviceStore` (iOS/native, local-first, writes to `localStorage`) and `serverStore` (web, talks to the backend). **Any new field or method added to one MUST be added to the other with the same signature** — this is enforced by guardian tests (see TESTING.md) and documented in `.claude/skills/didatica-boris/SKILL.md`. A mismatch is a silent data-loss bug (e.g. push preferences never reaching the server from iOS), not a lint warning.

**Server/client default parity:** `server/app/defaults.py` (Python) and `web/src/catalog.js` (JS) must contain **byte-identical** copies of the LLM prompt text templates (`carteiraStopAlvo`, `carteiraStopAlvoOperador`, etc.), because the native app assembles state without ever calling the server. This is enforced byte-for-byte by `server/tests/test_auditoria_prompts.py::test_a8ii_paridade_defaults_carteira_com_catalog_js`. Any edit to a prompt template in one file requires the identical edit in the other, in the same commit.

## Function Design

- Small, single-purpose functions preferred, especially in the pure-logic modules (`web/src/finance.js`, `server/app/indicators.py`) — these are unit-tested directly with known inputs/outputs.
- Pure functions (no I/O, no side effects) are deliberately separated from I/O/orchestration code so they can be tested without mocking (`finance.js`, `plan.js`, most of `indicators.py`). When adding new calculation logic, keep it pure and put I/O in the caller.
- Guard clauses over nested conditionals for early-return validation (`if (!risco || risco <= 0 || !entrada || !cap) return null;`).

## Return Values

- Backend: JSON-serializable dicts; nullable numeric fields use `null` explicitly, never `0.0` as a stand-in for "unknown" — this is a house rule enforced by a guardian test (`test_m3_format_pede_null_nunca_zero`, asserting the LLM prompt format text says `"use null (nunca 0.0"`).
- Frontend calculation functions return small result objects (`{ curve, series, days, retAcum, drawdown, base, end }`) rather than tuples/arrays, so callers destructure by name.

---

*Convention analysis: 2026-08-18*
