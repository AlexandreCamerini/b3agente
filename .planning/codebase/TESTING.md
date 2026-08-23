# Testing Patterns

**Analysis Date:** 2026-08-18

## Canonical Test Suite

**There are TWO suites, and both must run.** The canonical command is:

```bash
bash scripts/executar.sh --testes
```

This runs, in order:
1. `bash scripts/test.sh` — backend pytest suite (`server/tests/*.py`, 84 files, ~911 `def test_*` functions).
2. Every `web/tests/*.mjs` file (74 files) run individually with plain `node`, from inside `web/`.

`scripts/test.sh` alone is **only the backend half** — running it in isolation and declaring the work validated is explicitly called out as insufficient in the project's own `CLAUDE.md`. Always use `bash scripts/executar.sh --testes` (or `bash executar.sh --testes` from repo root) for real validation.

**Checkout/worktree novo (FIX-C24, 2026-08-23):** `bash scripts/executar.sh --testes` agora resolve o pré-requisito de `web/node_modules` sozinho — se ausente, roda `npm ci` (ou `npm install` se não houver lockfile ou o `npm ci` falhar) em `web/` antes do laço de testes, e aborta com mensagem acionável se a instalação falhar. Não é mais necessário rodar `npm install` manualmente antes da suíte canônica num checkout/worktree novo. Além disso, uma falha num `.mjs` da suíte web agora imprime as últimas ~20 linhas da saída do teste (antes era um `[X]` mudo, com a causa engolida por `>/dev/null 2>&1`). Ver `docs/adr/018-cobertura-e2e.md` para a avaliação companheira de cobertura E2E (FIX-C27).

**Front-end edits require an additional build check** the test suites do not catch (JS syntax errors are not caught by grep/static read):

```bash
npx vite build   # from web/
```

## Backend Test Framework

**Runner:** pytest ≥ 8.0 (`server/requirements.txt`), config at `server/pytest.ini`:
```ini
[pytest]
pythonpath = .
testpaths = tests
```
No coverage plugin configured (no `pytest-cov` in requirements) — coverage is not measured or enforced numerically.

**Venv location:** the venv lives in the **main clone**, not necessarily in a worktree. `scripts/test.sh` resolves this via `git rev-parse --git-common-dir` and falls back through candidate python paths; if pytest truly isn't importable anywhere, it falls back to a bespoke **offline mini-runner** that executes any `tests/test_*.py` file containing an `if __name__ == "__main__":` block directly with `python3`, skipping files whose only failure is a missing dependency. This offline fallback is intentionally **partial coverage** — never treat an offline run as equivalent to the full pytest run before a deploy.

**Run commands:**
```bash
cd server && ./.venv/bin/python -m pytest -q     # full suite
cd server && ./.venv/bin/python -m pytest -q tests/test_persistence.py   # single file
bash scripts/test.sh                              # portable entrypoint (resolves venv location)
```

## Backend Test File Organization

**Location:** flat directory, `server/tests/*.py`, one file per feature/bugfix/ADR, not one-per-source-module. Filenames reference the originating work: `test_qa39.py`, `test_qa42_finops.py`, `test_adr013_rbac.py`, `test_auditoria_prompts.py`.

**No `conftest.py`** exists — no shared pytest fixtures. Each test file is self-contained and defines its own local helpers (`_fresh_db()`, `_client()`, `_spy()`).

**Structure — isolated SQLite per test:**
```python
def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_test_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)
    return conn, path

def test_config_persiste_apos_reinicio():
    conn, path = _fresh_db()
    store.set_config(conn, {...})
    conn.close()          # simulates server shutdown
    conn2 = db.connect(path)   # reopens same file = simulates restart
    cfg = store.get(conn2, "config")
    assert cfg["provider"] == "openai"
```
Never depends on shared fixtures or a persistent test DB — every test creates and tears down its own temp SQLite file. Reuse this pattern for any new persistence test.

**Structure — FastAPI endpoint tests:**
```python
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def _app_main_isolado():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)

def _client(monkeypatch, admin_emails=None):
    monkeypatch.setenv("B3_ADMIN_EMAILS", admin_emails) if admin_emails else monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    d = tempfile.mkdtemp(prefix="b3_admin_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main
```
Route-level tests reimport `app.main` with `B3_DB_PATH` monkeypatched to a temp directory, so they never touch the real dev database, then restore `sys.modules["app.main"]` afterward. Use this pattern for any test exercising a route gated on env-driven state (admin allowlists, kill-switches).

## Mocking

**No mock library** (`unittest.mock`, `AsyncMock`, `MagicMock`) is used anywhere in `server/tests/`. The house pattern is:

1. **`monkeypatch`** (pytest builtin) — used in 33+ files, for env vars, module attributes, and swapping out functions:
```python
def _spy(seen):
    async def call(config, key, system, user, max_tokens):
        seen["system"] = system
        seen["user"] = user
        return '{"direcao":"Alta", ...}'
    return call

def test_a1_...(monkeypatch):
    monkeypatch.setattr(llm, "_call_llm", _spy(seen))
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
```
2. **Fake async callables passed as parameters** for network-bound functions, e.g. `brapi.get_history("PETR4", rng="1d", interval="15m", fetch_json=fake)` — the function under test accepts an injectable fetcher instead of importing `httpx` directly, making mocking a no-dependency plain function.

**What to mock:** the LLM call boundary (`_call_llm`) and any real network fetch (brapi/Yahoo). Never call a real external provider from a test.

**What NOT to mock:** the SQLite layer (use a real temp-file DB instead — see above), and pure calculation functions (call them directly with literal inputs).

## Async Testing

No `pytest-asyncio`/`anyio` plugin declared. Async code under test is driven synchronously with `asyncio.run(...)` inside an otherwise-sync `def test_...():` function (used 159 times):
```python
def test_a2_legado_declara_ausencia_do_pacote(monkeypatch):
    monkeypatch.setattr(llm, "_call_llm", _spy(seen))
    asyncio.run(llm.analyze({"appMode": modo}, {"text": skill_ref.PRINCIPIOS}, {}, {}, "PETR4", {}, {"candles": []}))
    assert "NÃO há pacote técnico pré-calculado" in seen["system"]
```

## Error Testing

`pytest.raises(...)` with a domain-specific exception and `match=` regex, e.g.:
```python
with pytest.raises(brapi.ForaDoPlano, match="15m"):
    asyncio.run(brapi.get_history("PETR4", rng="1d", interval="15m", fetch_json=fake))
assert fake.chamadas == []   # rejection must not burn network quota
```
Note the accompanying assertion on side-effect absence (no network call happened) — error tests in this codebase commonly assert both the exception AND that no unwanted side effect occurred.

## Web Test Framework

**Runner:** none — plain Node.js (`node web/tests/test_*.mjs`), no Jest/Vitest/Mocha. `node:assert` is used directly for assertion-style tests; many files use a hand-rolled boolean checker instead.

**Run commands:**
```bash
node web/tests/test_finance.mjs                       # single file
for t in web/tests/*.mjs; do node "$t" || echo "FALHOU: $t"; done   # all (what executar.sh --testes does)
```
No `npm test` script is defined in `web/package.json` — tests are invoked by path, not through package.json scripts.

## Web Test File Organization

**Location:** flat, `web/tests/test_<feature>.mjs`, 74 files. Same convention as backend: one file per feature/fix/ADR, not one-per-source-module.

**Two coexisting patterns**, both valid, pick whichever fits the test's shape:

**Pattern A — boolean checker (most common for pure-function/static-source tests):**
```javascript
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

ok("markPrice usa cotação > 0", markPrice({ price: 30 }, { avg: 25 }) === 30);
// ... more ok() calls ...

console.log("\n" + (fails === 0 ? "TODOS OS TESTES PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
```

**Pattern B — `node:assert` + async IIFEs (used when mocking `fetch` / testing async flows):**
```javascript
import assert from "node:assert";
let passed = 0;
const ok = (name) => { console.log("ok", name); passed++; };

await (async () => {
  setNativeMode(true);
  setApiBase("");
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (url) => { ...; return { ok: true, status: 200, text: async () => JSON.stringify({...}) }; };
  try {
    const s = await api.getState();
    assert.ok(s && s.okState);
    ok("nativo sem base usa a produção embutida");
  } finally {
    globalThis.fetch = realFetch;   // always restore
  }
})();

console.log(`\n${passed} testes ... TODOS PASSARAM`);
```
Exit code convention: every file must exit non-zero on failure (`process.exit(fails === 0 ? 0 : 1)` for Pattern A; assert throws naturally abort the process for Pattern B) — `scripts/executar.sh --testes` relies on the node process exit code to detect failure.

## Mocking (Web)

**`globalThis.fetch` swap-and-restore** is the only mocking mechanism used — no `sinon`/`nock`/MSW. Always capture `realFetch` before overriding and restore it in a `finally` block, even on the happy path, or subsequent tests in the same process leak the mock.

**Static source inspection** is a first-class test technique here, not a fallback: several guardian tests `readFileSync` a source file and regex-match against its literal text rather than importing and executing it. This is used specifically when the code under test imports something unavailable outside a native build (e.g. `persistence.js` imports `@capacitor/core`):
```javascript
const src = readFileSync(new URL("../src/persistence.js", import.meta.url), "utf8");
const hits = (src.match(new RegExp("\\b" + m + "\\s*[:(]", "g")) || []).length;
assert.ok(hits >= 2, m + " deve existir nos DOIS stores");
```
Use this pattern for any new test that needs to assert something about native-only code paths.

## Guardian Tests — Regression Locks

A recurring, explicitly-named pattern across ~78 files (backend + web): a **"guardião"** (guardian) is a test written specifically to lock a bug fix or an invariant so it cannot silently regress. Guardian tests carry a comment block explaining the incident/finding that motivated them, e.g.:

```javascript
// O achado que originou estes guardiões (revisão do supervisor, 2026-08-05):
// no aparelho, `deviceStore.putConfig` grava em localStorage e NUNCA chama a
// API... A correção: o único caminho que SEMPRE chega ao servidor... passa a
// carregar consentimento + modo + universo. Estes testes travam isso.
```

**House rule:** guardian tests are never deleted to make a change easier. A deliberate reversal updates the guardian's assertion **with an updated comment explaining why**, not a silent removal (see `CLAUDE.md`: "Guardiões de teste não se apagam — reversão deliberada atualiza o guardião com nota"). When implementing a fix for a real bug, write the guardian test alongside it in the same change.

### Named parity guardians (project-critical, cross-file invariants)

**1. Server/client prompt-text byte parity** — `server/app/defaults.py` (Python) vs `web/src/catalog.js` (JS):
- Guardian: `server/tests/test_auditoria_prompts.py::test_a8ii_paridade_defaults_carteira_com_catalog_js`
- What it checks: extracts the `carteiraStopAlvo`/`carteiraStopAlvoOperador` template literals out of `catalog.js` with regex and asserts `==` (byte-exact) against `defaults.default_llm_prompts()` from the Python side.
- Why: the native (iOS) client assembles its own default state without calling the server, so both languages must carry an identical copy of the prompt text. A single differing byte is a silent divergence bug.
- Secondary coverage: `web/tests/test_copy_theme.mjs` also asserts both files contain matching marker strings (`carteiraStopAlvoOperador`, `defaultSkillTextOperador` / `default_skill_text_operador`).

**2. `deviceStore` / `serverStore` method-and-signature parity** — both defined in `web/src/persistence.js`:
- Guardians: `web/tests/test_didatica_parity.mjs`, `web/tests/test_deep_parity.mjs`, plus parity assertions embedded in `test_admin_ui.mjs`, `test_modo_operador.mjs`, `test_appmode_sincroniza_servidor.mjs`, `test_device_budget_sync.mjs`, `test_putconfig_so_o_que_mudou.mjs`, `test_carteira_nativa_sincroniza.mjs`, and others (20 files reference both stores).
- What it checks: for each method name, regex-counts occurrences in `persistence.js` and asserts `>= 2` (once per store), e.g.:
```javascript
for (const m of ["scanDeep", "scanDeepEstimate"]) {
  const hits = (src.match(new RegExp("\\b" + m + "\\s*[:(]", "g")) || []).length;
  assert.ok(hits >= 2, m + " deve existir nos DOIS stores");
}
```
- For methods where argument shape matters (not just name), the guardian checks the exact signature text on both sides, e.g. `syncPushPrefs` must appear as `async syncPushPrefs() { ensure();` in `deviceStore` AND `syncPushPrefs: async () => {` in `serverStore` — a name-only match would miss an accidental required-argument mismatch.
- Why: `deviceStore` (native/local-first) and `serverStore` (web) must expose the identical interface; a field/method added to only one is a silent data-loss bug (documented incident: push preferences never reaching the server from iOS because only `serverStore` synced `notif`/`appMode`/`watchlist`).

**When adding a field or method to either store, add it to both in the same change**, and add or extend a parity guardian if one doesn't already cover that surface.

### Other notable guardians

- `web/tests/test_editor_texto_byte_exato.mjs` — locks the admin prompt editor (`web-admin/src/EditorTexto.jsx`) to never transform user text (no `.trim()`/`.replace()`/`.normalize()`, no WYSIWYG/AST round-trip editor), because `server/app/store.py` decides prompt migration by SHA-256 of the saved text — any silent normalization breaks that hash comparison.
- `server/tests/test_m3_format_pede_null_nunca_zero` — locks that the LLM prompt format explicitly requires `null` (never `0.0`) for unknown stop/target values.
- `server/tests/test_setores.py` + `web/tests/test_setor_toque.mjs` — lock the tap-to-explain vocabulary/gesture contract described in `.claude/skills/didatica-boris/SKILL.md`.

## Coverage

No coverage tool or numeric threshold is configured or enforced. Coverage is achieved through breadth (911 backend + ~1500+ web assertions across 74 files) and through the guardian-test discipline: **every observed regression gets a permanent test**, rather than coverage being measured top-down.

## Test Types

**Unit tests:** the majority — pure calculation functions (`finance.js`, `indicators.py`, `technical_models.py`), persistence round-trips, prompt-construction logic.

**Integration tests:** FastAPI `TestClient` tests exercising real routes against a temp SQLite DB (`test_admin_summary.py`, `test_auth.py`, `test_gate_cadastro.py`).

**Contract/parity tests:** static-source comparison tests (see Guardian Tests above) — a category specific to this codebase's dual-client architecture (Python server + JS web + JS-in-native).

**E2E tests:** not present. There is no browser automation (Playwright/Cypress) or device-level test harness in the repo; iOS-specific behavior is verified manually via TestFlight (see `TESTFLIGHT.md`) and the memory note that some UI bugs "só a verificação ao vivo pegou" (only live verification catches them) — do not assume a passing unit/integration test proves the mobile UI behaves correctly. See `docs/adr/018-cobertura-e2e.md` (2026-08-23, FIX-C27) for the dated decision on why E2E is not being adopted now, with objective re-evaluation triggers.

**Manual/adjacent tooling:** `scripts/masstest-agentes.py` (deterministic, free) and `scripts/masstest-agentes-llm.py` (LLM-backed, BYOK) run larger simulated-agent scenarios outside the pytest/node suites — not part of the canonical gate, used for broader behavioral spot-checks.

---

*Testing analysis: 2026-08-18*
