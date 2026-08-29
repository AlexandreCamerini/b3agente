# Phase 12: Limites do plano gratuito ativos - Pattern Map

**Mapped:** 2026-08-29
**Files analyzed:** 3 (2 modified, 1 new test file recommended; RESEARCH.md skipped — small, well-understood activation of existing hooks)
**Analogs found:** 3 / 3

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|-----------------|----------------|
| `server/app/plan.py` (edit: `PLAN_FREE` limits + `can_add_ticker` copy) | config/service (pure hook, no I/O) | transform (in-memory limit check) | itself — pre-existing `can_analyze` in same file is the copy-pattern reference | exact (sibling function in same module) |
| `server/app/main.py` — `put_watchlist` (line 1041-1044) | route/controller | request-response (gate + CRUD write) | `server/app/main.py` — `watchlist_add` (line 1049-1080), same file, same resource | exact |
| `server/tests/test_XX_...py` (new — gate on `PUT /api/watchlist`) | test | request-response (TestClient) | `server/tests/test_fase3_gate_plano.py` (route-level gate tests, `can_add_ticker` spy pattern) + `server/tests/test_fase5_gate_mensal.py` (ledger/limit activation guardian pattern) | exact |

## Pattern Assignments

### `server/app/plan.py` (config/service, transform)

**Analog:** same file, `can_analyze` (lines 83-95) — already in the target "no CTA" copy style; `can_add_ticker` (lines 73-80) is the function being edited itself.

**Current state to change** (lines 29-40):
```python
PLAN_FREE = {
    "id": "free",
    "max_watchlist": None,        # futuro: ex. 10 ativos no gratuito
    "max_analyses_per_month": None,  # futuro: ex. 30 analises/mes no gratuito
    "byok_required": False,       # futuro: gratuito pode exigir BYOK
}
PLAN_PRO = {
    "id": "pro",
    "max_watchlist": None,
    "max_analyses_per_month": None,
    "byok_required": False,
}
```
D-01: set `PLAN_FREE["max_watchlist"] = 10`, `PLAN_FREE["max_analyses_per_month"] = 30`. `PLAN_PRO` stays `None`/`None` (unlimited). Update the misleading module docstring lines 1-25 and the `# futuro:` inline comments (limits are no longer hypothetical) — but do NOT touch the C-32/C-33 contract prose, it's still accurate and load-bearing for other modules' comments that reference it.

**Core pattern — gate function shape, already correct, just copy-edit** (lines 73-95):
```python
def can_add_ticker(current_count: int, plan: Optional[dict] = None) -> tuple:
    """HOOK: limite de tamanho da watchlist no tier gratuito.
    Retorna (permitido: bool, motivo: str|None)."""
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_watchlist")
    if limit is not None and current_count >= limit:
        return (False, f"O plano {plan['id']} permite ate {limit} ativos. Faca upgrade para adicionar mais.")
    return (True, None)


def can_analyze(used_this_month: int, plan: Optional[dict] = None) -> tuple:
    """HOOK: limite de analises/mes no tier gratuito. ..."""
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_analyses_per_month")
    if limit is not None and used_this_month >= limit:
        return (False, f"Voce atingiu o limite de {limit} analises/mes do plano {plan['id']}.")
    return (True, None)
```
D-05: change ONLY the f-string in `can_add_ticker` (line 79) to match `can_analyze`'s no-CTA pattern:
```python
return (False, f"Voce atingiu o limite de {limit} ativos do plano {plan['id']}.")
```
`can_analyze`'s message is already the target style — do not touch it, it's the reference.

---

### `server/app/main.py` — `put_watchlist` (route/controller, request-response)

**Analog:** `watchlist_add` in the same file (lines 1049-1080) — same resource, already implements the gate correctly for the sibling endpoint.

**Current state — the gap (no gate at all)** (lines 1041-1044):
```python
@app.put("/api/watchlist")
async def put_watchlist(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    store.set_watchlist(_conn, body.get("tickers") or [], user_id=scope)
    return store.public_state(_conn, user_id=scope)
```

**Gate pattern to copy from `watchlist_add`** (lines 1068-1072):
```python
    # GANCHO FREEMIUM (hoje sempre permite): limite de ativos do tier gratuito.
    allowed, reason = plan.can_add_ticker(len(store.get(_conn, "watchlist", user_id=scope)),
                                          plan=_plano_do_escopo(scope))
    if not allowed:
        raise HTTPException(402, reason)  # 402 Payment Required (fase futura)
```

**Required shape for `put_watchlist` per D-03/D-04** — this is NOT a direct copy-paste of the snippet above; the semantics differ (`watchlist_add` grows by exactly 1, `put_watchlist` receives an arbitrary final list and must only gate GROWTH, never shrink/reorder):
```python
@app.put("/api/watchlist")
async def put_watchlist(body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    novos = body.get("tickers") or []
    atual = store.get(_conn, "watchlist", user_id=scope)
    if len(novos) > len(atual):  # D-03: só bloqueia CRESCIMENTO, nunca remoção/reordenação
        allowed, reason = plan.can_add_ticker(len(novos) - 1, plan=_plano_do_escopo(scope))
        if not allowed:
            raise HTTPException(402, reason)
    store.set_watchlist(_conn, novos, user_id=scope)
    return store.public_state(_conn, user_id=scope)
```
**Recommendation (resolved, not a fork for the planner):** reuse `plan.can_add_ticker(len(novos) - 1, plan=_plano_do_escopo(scope))` exactly as in the code block above — do not write a separate inline `len(novos) > limit` check. Proof of equivalence: given the growth guard `len(novos) > len(atual)` already gated entry into this branch, `can_add_ticker` denies iff `current_count >= limit`, i.e. iff `(len(novos) - 1) >= limit`, i.e. iff `len(novos) > limit` — exactly "final size vs. limit" per D-03's own wording ("comparar o tamanho FINAL contra o limite, não incremento a incremento"), not an approximation. Boundary check: `atual=9, novos=10, limit=10` → `can_add_ticker(9, ...)` → `9 >= 10` false → allowed (final size 10 is exactly at the limit, correct). `atual=15 (grandfathered), novos=16, limit=10` → `can_add_ticker(15, ...)` → `15 >= 10` true → denied (growth from an already-over state is still growth, correctly blocked per D-03). Reusing `can_add_ticker` also keeps the refusal string defined in exactly one place (`plan.py`), consistent with the C-32/C-33 single-source-of-truth contract cited in Shared Patterns below — the inline alternative would duplicate the D-05 message string in `main.py` too, which is strictly worse, not cleaner.

**Imports already present in `main.py`** (no new imports needed — `plan`, `store`, `HTTPException`, `Optional`, `Depends`, `Body`, `current_scope`, `_plano_do_escopo` are already imported/defined at module level, used by `watchlist_add` and `_gate_analise`).

---

### `server/tests/test_XX_gate_watchlist_put.py` (new, test, request-response)

**Analogs:**
- `server/tests/test_fase3_gate_plano.py` — route-level gate test harness (TestClient, `_client()`/`_registra()`/`_auth()` helpers, `plan.can_add_ticker` spy pattern via `monkeypatch.setattr`).
- `server/tests/test_fase5_gate_mensal.py` — pattern for testing an activation of a previously-`None` limit (this phase is the `max_watchlist` analog of that file's `max_analyses_per_month` activation), including the static "no hardcoded bypass" guardian test style (`_main_source_sem_comentarios`).

**Isolation boilerplate to copy verbatim** (from `test_fase3_gate_plano.py` lines 42-76 — identical in `test_fase5_gate_mensal.py`):
```python
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import plan


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    from app import agent, brapi_budget, managed
    original = sys.modules.get("app.main")
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, env=None):
    d = tempfile.mkdtemp(prefix="b3_gate_watchlist_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    for k, v in (env or {}).items():
        monkeypatch.setenv(k, v)
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}
```

**Core pattern — route test hitting `PUT /api/watchlist` directly** (adapt from `watchlist_add` tests in `test_fase3_gate_plano.py` lines 124-147, and CONTEXT.md's own required coverage a/b/c):
```python
def test_put_watchlist_bloqueia_crescimento_alem_do_limite(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "cresce@teste.com")
    # popula 10 tickers (limite free) via store direto, sem passar pelo gate
    main.store.set_watchlist(main._conn, [f"T{i}4" for i in range(10)], user_id=payload["user"]["id"])

    r = c.put("/api/watchlist", json={"tickers": [f"T{i}4" for i in range(11)]},
              headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    assert "10 ativos" in r.json()["detail"]


def test_put_watchlist_nunca_bloqueia_reducao(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "reduz@teste.com")
    main.store.set_watchlist(main._conn, [f"T{i}4" for i in range(15)], user_id=payload["user"]["id"])  # já acima do limite (D-04)

    r = c.put("/api/watchlist", json={"tickers": [f"T{i}4" for i in range(15)][:5]},
              headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text  # reduzir nunca é bloqueado


def test_put_watchlist_nunca_bloqueia_reordenacao_mesmo_tamanho(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "reordena@teste.com")
    tickers = [f"T{i}4" for i in range(10)]
    main.store.set_watchlist(main._conn, tickers, user_id=payload["user"]["id"])

    r = c.put("/api/watchlist", json={"tickers": list(reversed(tickers))},
              headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text


def test_put_watchlist_usuario_ja_acima_do_limite_nao_perde_ativos_existentes(monkeypatch):
    """D-04 (grandfather clause): conta que já tinha >10 ativos antes do limite
    entrar em vigor continua vendo/operando a lista inteira — o gate só
    impede CRESCER além do limite, nunca remove nada em silêncio."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "legado@teste.com")
    tickers = [f"T{i}4" for i in range(15)]
    main.store.set_watchlist(main._conn, tickers, user_id=payload["user"]["id"])

    r = c.get("/api/state", headers=_auth(payload["token"]))  # confirme rota real de leitura de estado no store.py/main.py
    assert r.status_code == 200, r.text
    assert len(r.json()["watchlist"]) == 15  # nada foi truncado
```
(Planner/executor: confirm the exact route name for reading `public_state` — grep `store.public_state` call sites in `main.py` for the canonical read-back endpoint; `test_fase3_gate_plano.py`/`test_fase5_gate_mensal.py` don't need this because they only assert on write-route responses which already return `store.public_state(...)`.)

**Static guardian pattern (copy from `test_fase5_gate_mensal.py` lines 199-217)** — to prove the fix landed in the code, not just in a mocked test:
```python
def _main_source_sem_comentarios() -> str:
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    return "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))


def test_put_watchlist_chama_o_gate_de_plano():
    assert "def put_watchlist" in _main_source_sem_comentarios()
    # a função precisa referenciar max_watchlist/can_add_ticker/limit — não
    # mais só store.set_watchlist direto
```

**D-01 activation guardian (copy shape from `test_fase3_gate_plano.py`'s now-inverted `test_d03_nenhum_limite_comercial_ativado`, lines 182-186)** — this phase FLIPS that guardian; update it (per CLAUDE.md "guardiões de teste não se apagam — reversão deliberada atualiza o guardião com nota") rather than deleting it:
```python
def test_d01_limites_do_plano_free_ativos():
    """ATUALIZADO (Fase 12): reversão deliberada de test_fase3_gate_plano.py::
    test_d03_nenhum_limite_comercial_ativado — os dois limites do FREE agora
    estão ativos (ver 12-CONTEXT.md D-01). PLAN_PRO segue ilimitado."""
    assert plan.PLAN_FREE["max_watchlist"] == 10
    assert plan.PLAN_FREE["max_analyses_per_month"] == 30
    assert plan.PLAN_PRO["max_watchlist"] is None
    assert plan.PLAN_PRO["max_analyses_per_month"] is None
```
**Important**: `server/tests/test_fase3_gate_plano.py::test_d03_nenhum_limite_comercial_ativado` (lines 182-186) currently asserts `PLAN_FREE["max_watchlist"] is None` and `PLAN_FREE["max_analyses_per_month"] is None` — this WILL fail once D-01 lands. Per CLAUDE.md guardrail, do not silently delete it: update it in place with a comment noting the deliberate reversal (pointing at this phase), mirroring how `test_fase3_gate_plano.py` itself documents its own reversal of an earlier contract at the top of the file (lines 19-25, the FIX-C01 note).

## Shared Patterns

### Gate-then-write / gate-then-fetch on a route
**Source:** `server/app/main.py::watchlist_add` (lines 1068-1072), `server/app/main.py::_gate_analise` (lines 437-457)
**Apply to:** `put_watchlist`
Pattern: resolve the real plan via `_plano_do_escopo(scope)` (never assume `ACTIVE_PLAN`), call the pure hook function from `plan.py` with the count read from a single source of truth (never a parallel counter — contract C-32/C-33), and on denial raise `HTTPException(402, reason)` where `reason` is the hook's returned string verbatim.

### Route test isolation boilerplate
**Source:** `server/tests/test_fase3_gate_plano.py` lines 42-76 (identical in `test_fase5_gate_mensal.py`)
**Apply to:** any new test file hitting `main.app` via `TestClient`
Pattern: temp `B3_DB_PATH`, reimport `app.main` fresh per test (module-level globals like `_conn`, `managed` cache, kill-switch caches are process-global and must reset between tests), `_registra`/`_auth` helpers for a logged-in scope.

### No-CTA refusal copy
**Source:** `server/app/plan.py::can_analyze` (line 94) — already correct
**Apply to:** `server/app/plan.py::can_add_ticker` (line 79, needs the D-05 edit)
Pattern: `f"Voce atingiu o limite de {limit} <unidade> do plano {plan['id']}."` — fact + reason, no "Faça upgrade" / CTA language anywhere in the string.

## No Analog Found

None — this phase only touches two already-established modules (`plan.py`, `main.py`) with a directly analogous sibling endpoint (`watchlist_add`) and two directly analogous prior-phase test files (`test_fase3_gate_plano.py`, `test_fase5_gate_mensal.py`) that did the exact same kind of "flip a `None` limit to a real number + close a bypass" work for the neighboring `max_analyses_per_month` limit.

## Metadata

**Analog search scope:** `server/app/plan.py`, `server/app/main.py` (routes + `_gate_analise`/`_plano_do_escopo`), `server/tests/` (grepped for `plan`, `watchlist`, `can_analyze`, `can_add_ticker`, `_gate_analise`)
**Files scanned:** `server/app/plan.py`, `server/app/main.py` (targeted ranges: 100-135, 420-480, 1020-1150), `server/tests/test_fase3_gate_plano.py`, `server/tests/test_fase5_gate_mensal.py`, `server/tests/test_plano_operacional.py` (checked, not an analog — different "plano" domain, trading plan not commercial plan), `server/app/store.py` (grepped for `set_watchlist`/`get` signatures only)
**Pattern extraction date:** 2026-08-29
