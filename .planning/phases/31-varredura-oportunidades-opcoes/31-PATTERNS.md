# Phase 31: Varredura de oportunidades de opções - Pattern Map

**Mapped:** 2026-09-14
**Files analyzed:** 7 (5 backend, 2 frontend)
**Analogs found:** 7 / 7 (all are direct extensions of existing files — this phase modifies canonical_refs files in place, it does not create new modules)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `server/app/opcoes_curadoria.py` (extend `candidatos_da_posicao`, `rankear`) | service (pure/deterministic) | transform (batch scan over N vencimentos × 4 estruturas) | itself, Fase 30 version (this IS the file to extend — see below) | exact (self) |
| `server/app/main.py` — `_curadoria_top()` / `GET /api/options/curadoria` | route/controller | request-response, orchestrates batch I/O | itself (`_curadoria_top`, lines 3287-3353) | exact (self) |
| `server/app/options_provider_mydata.py` — `get_options()` / `_primeiro_vencimento_futuro` | service (I/O, external HTTP) | request-response (budgeted network call per vencimento) | itself — needs a "N vencimentos" variant of the existing "1 vencimento" flow | exact (self), needs a sibling function, not a rewrite |
| `server/app/curadoria_narrativa.py` | service (AI narration layer) | request-response (LLM call over pre-ranked list) | itself — no structural change expected, only consumes a longer/richer `top` | exact (self), likely untouched logic |
| `server/app/store.py` — new discovery-time gate for `permitirOpcaoADescoberto` | middleware/guard (config read, not route middleware) | CRUD (config read) | `server/app/store.py:825` (`buy_option`'s execution-time gate) | role-match (same flag, different call site — execution vs. discovery) |
| `web/src/opcoes/PayoffChart.jsx` | component | transform (SVG render from a payoff struct) | itself — responsiveness fix, not a new component | exact (self) |
| `web/src/App.jsx` — `CuradoriaEstruturas` / `useCuradoria` (Posições screen) | component + hook | request-response (fetch top-N, render cards) | itself, `CuradoriaEstruturas` (4179-4249) / `useCuradoria` (4498-4547) — extend, likely don't replace | exact (self) |

## Pattern Assignments

### `server/app/opcoes_curadoria.py` — extend from 1 estrutura × 1 vencimento to 4 estruturas × 2 vencimentos

**Analog:** the file itself, Fase 30 shape (298 lines total, read in full).

**Current signature to extend** (lines 54-63):
```python
def candidatos_da_posicao(
    underlying: str,
    chain: Any,
    spot: Any,
    posicao: Any,
    modo: str,
    hoje: Any,
    *,
    n: int = STRIKES_POR_POSICAO,
) -> list[dict[str, Any]]:
```
Only produces `tipo: "call_coberta"` candidates (lines 108-178), via `opcoes_motor.rastrear()` + `opcoes_motor.avaliar()` with a fixed leg pair (`perna_de_acao` + `perna_de_contrato(..., "venda", ...)`).

**Gate order to replicate for new structures** (lines 91-100, "Portas fechadas, na ordem"):
```python
if not isinstance(chain, dict) or chain.get("providerStatus") != "ok":
    return []
if not isinstance(posicao, dict) or store.qty_livre(posicao) < 100:
    return []
if not isinstance(spot, (int, float)) or isinstance(spot, bool) or spot <= 0:
    return []

dias = _dias_ate(chain.get("expiration"), hoje)
if dias is None or not (_PRAZO_MIN_DIAS <= dias <= _PRAZO_MAX_DIAS):
    return []
```
This is the template gate chain. Every new estrutura (put de proteção, collar, opção a descoberto) should follow the same "return `[]` on any closed door, never raise, never `None`" contract — this is a hard house convention across `opcoes_lastreadas.py`/`opcoes_motor.py`/this file (stated explicitly in the module docstring, lines 64-67).

**Per-estrutura leg assembly pattern** (lines 119-131, the loop body) — copy this shape per new estrutura, swapping `pernas`:
```python
for contrato in selecionados:
    try:
        pernas = [
            opcoes_motor.perna_de_acao(underlying, spot, quantidade=1),
            opcoes_motor.perna_de_contrato(contrato, "venda", quantidade=1),
        ]
        estrutura = opcoes_motor.avaliar(pernas)
    except ValueError:
        continue  # one bad contract must not sink the whole scan
```
For put de proteção: `perna_de_acao(..., "compra", ...)` + `perna_de_contrato(put, "compra", ...)`. For collar: action leg + short call + long put (3 legs — `opcoes_motor.avaliar` already accepts N legs, no engine change needed, confirmed in `opcoes_motor.py` docstring "N pernas"). For opção a descoberto: `perna_de_contrato(contrato, "venda", ...)` alone, no action leg — this is the one that needs the D-05 gate (see below), because it has no lastro requirement (`qty_livre >= 100` check above stops applying the same way; naked calls are the one structure not gated by owning shares).

**D-06 ranking formula — do not fork by estrutura, use one `rankear()`** (lines 187-206):
```python
def rankear(candidatos: list[dict[str, Any]], *, topo: int = TOPO) -> list[dict[str, Any]]:
    ordenados = sorted(candidatos, key=lambda c: (-c["razao"], -c["premioUnitario"], c.get("contractSymbol") or ""))
    cortados = ordenados[:topo]
    return [{**c, "posicaoNoRanking": i} for i, c in enumerate(cortados, start=1)]
```
D-06 says use the SAME `razao = premio_unitario / perda_maxima` for all 4 estruturas — this function needs zero changes if every new estrutura's dict carries a `razao` key computed the same way as the existing `call_coberta` block (lines 133-144):
```python
perda_maxima = estrutura.get("perda_maxima")
if not isinstance(perda_maxima, (int, float)) or isinstance(perda_maxima, bool) or perda_maxima <= 0:
    continue
premio = float(contrato.get("lastPrice") or 0)
premio_unitario = round(premio, 2)
razao = round(premio_unitario / perda_maxima, 6)
```
Watch D-06's known caveat: put/collar structurally have low `perda_maxima` (protection lowers max loss by design) and can produce negative `premio_unitario` (net debit) — the `perda_maxima <= 0` guard above still applies, but a **negative premium** is not currently rejected by this gate (only `perda_maxima <= 0` is checked, not `premio_unitario`). Confirm with the plan whether negative-premium put/collar candidates should be silently excluded or explicitly ranked low — CONTEXT.md D-06 says "aceito" (accept low ranking), which implies premio negativo should NOT be filtered out, just ranked naturally low/negative by the same formula. Don't add a new filter that CONTEXT.md didn't ask for.

**exigir_ranking() — no changes needed** (lines 209-239): it validates structural shape (`posicaoNoRanking`, monotonic `razao`), not estrutura type. It will keep working unmodified once `rankear()` receives a mixed-type pool.

**Naked-option D-05 gate — the concrete gap to close.** `candidatos_da_posicao` today receives no `cfg`/`scope`, only `modo: str`. The naked-structure branch needs a `permitirOpcaoADescoberto` read modeled on the EXECUTION-time gate at `server/app/store.py:825` (inside `buy_option`, `store.py:815-828`):
```python
cfg = get(conn, "config", user_id=user_id) or {}
if not cfg.get("permitirOpcaoADescoberto"):
    registrar_rejeicao(conn, "COMPRA", cid, qty, price, MOTIVO_DESCOBERTO_DESLIGADO,
                        user_id=user_id, origem=origem)
    raise ValueError(MOTIVO_DESCOBERTO_DESLIGADO)
```
The discovery-time version in `opcoes_curadoria.py` must NOT raise or register a rejection (this is a display filter, not an order attempt) — it should simply skip generating naked candidates when the flag is off, mirroring the "closed door returns `[]`" contract used everywhere else in this file, not the raise-based contract used in `store.py`'s execution path. Concretely: the new/extended `candidatos_da_posicao` (or a sibling function for the unlastreada case) needs a `permitir_a_descoberto: bool` parameter, and the caller (`_curadoria_top` in `main.py`) needs to read `cfg.get("permitirOpcaoADescoberto")` the same way `main.py:3370` already reads `cfg = store.get(_conn, "config", user_id=scope)` for `modo` — this cfg read already exists in `_curadoria_top`'s caller, it just isn't threaded through to the estrutura-generation layer yet.

---

### `server/app/main.py` — `_curadoria_top()` extension for N vencimentos × 4 estruturas

**Analog:** itself, `_curadoria_top` (lines 3287-3353) and `options_curadoria` route (3356-3380).

**Current per-position single-vencimento fetch** (lines 3314-3344):
```python
for posicao in elegiveis:
    t = posicao.get("t")
    if not t:
        continue
    try:
        chain = await options_provider.get_options(t)
    except Exception:
        degradados.append(t)
        continue

    if chain.get("providerStatus") != "ok":
        degradados.append(t)
        continue
    ...
    pool.extend(opcoes_curadoria.candidatos_da_posicao(t, chain, spot, posicao, modo, hoje))
```
D-01 requires this to become "up to 2 vencimentos per position" — that means: (1) fetch `mydata_client.get_vencimentos(t)` once (cheap, per D-03), pick the 2 nearest future dates; (2) call `options_provider.get_options(t, expiration=venc)` once PER vencimento (up to 2× `get_options_chain` calls), feeding each resulting chain through `candidatos_da_posicao`/its extended siblings, and extending the same `pool` list. The `degradados`/`avaliadas`/`ignoradas` meta bookkeeping (lines 3346-3352) needs to stay position-scoped, not vencimento-scoped — a position with 1-of-2 vencimentos degraded should probably still count as "avaliada" since some candidates came through; this is a concrete open question for the plan (declare `degradados` semantics: per-position or per-(position,vencimento)).

**`options_curadoria` route wrapper — no change expected** (3356-3380): it already delegates everything to `_curadoria_top`, tolerates `Exception` best-effort, and returns `{"top": ..., **meta}`. This should keep working unmodified once `_curadoria_top`'s internals change, same reuse relationship `curadoria_narrativa` route (3383-3429) already has — it recomputes via the SAME `_curadoria_top` so the narrated list always matches the displayed list (documented at 3388-3395). Nothing here needs a second code path for "N vencimentos" — one call site, extended in place.

---

### `server/app/options_provider_mydata.py` — sibling for "2 nearest vencimentos" (D-01/D-03)

**Analog:** itself, `get_options()` (lines 222-334) + `_primeiro_vencimento_futuro()` (183-203).

**Current 1-vencimento selection** (183-203):
```python
def _primeiro_vencimento_futuro(venc: list, hoje: dt.date) -> Optional[str]:
    candidatos: list[tuple[dt.date, str]] = []
    for v in venc:
        raw = v.get("dt_vencimento")
        try:
            d = dt.date.fromisoformat(raw)
        except (TypeError, ValueError):
            continue
        if d > hoje:
            candidatos.append((d, raw))
    if not candidatos:
        return None
    candidatos.sort(key=lambda item: item[0])
    return candidatos[0][1]
```
D-01 needs a `_dois_vencimentos_futuros` (or equivalent) that returns `candidatos[:2]` instead of `candidatos[0]` — trivial extension of the same sorted-list pattern, same malformed-item tolerance (`try/except (TypeError, ValueError): continue`).

**Cost/budget contract to preserve** (documented inline, 206-219 and D-03 in CONTEXT.md): `_debita()`/`mydata_budget.reservar()` is the atomic commit point, called once per network call — `get_vencimentos` (1 call, cheap, already returns the full list) then `get_options_chain` (1 call PER vencimento fetched, expensive). The existing `get_options()` already does `_debita()` before the `get_vencimentos` call (line 248) and a SECOND `_debita()` before `get_options_chain` (line 290) — for 2 vencimentos, this becomes 1 (`get_vencimentos`) + 2 (`get_options_chain` × 2) = 3 debits instead of today's 2. Any new "2 vencimentos" entry point must call `_debita()` explicitly once per `get_options_chain` call, exactly like the existing single-vencimento path — reuse `_debita`/`_gate` as-is, do not add a parallel budget mechanism (CLAUDE.md guardrail: `brapi_budget`-style memory→DB→env pattern is the house convention, mirrored here by `mydata_budget`).

**Degradation-per-vencimento pattern to reuse** (lines 269-288, `_empty_payload(...)` calls): every failure mode (vencimento not in list, no future vencimento, out of budget) returns a structured payload with `providerStatus != "ok"` and a PT-BR `error`/warning string rather than raising — the N-vencimento caller in `main.py` should treat each vencimento's fetch independently with this same shape, so 1 failed vencimento doesn't kill the other.

---

### `server/app/curadoria_narrativa.py` — likely untouched, confirm no structural coupling

**Analog:** itself (89 lines, read in full).

`narrar()` (lines 42-89) only consumes `top: list[dict]` via `opcoes_curadoria.exigir_ranking(top)` (line 45) and serializes fields generically in `narrativa_user()` (`opcoes_curadoria.py:269-298`) — `tipo`, `ticker`, `strike`, `premioUnitario`, etc. are read via `.get()`, not type-specific formatting. **Risk to flag for the plan:** `narrativa_user()` (opcoes_curadoria.py:280-295) hardcodes phrasing implying a "venda coberta" framing in places (e.g., no explicit `tipo`-branching in the per-item line template) — check whether the line template needs a `tipo`-aware branch once put/collar/naked structures with different economics (net debit vs. credit, `ganho_maximo`/`perda_maxima` meaning differently per estrutura) start flowing through. This module itself should NOT need changes to its LLM-calling scaffolding (`llm.resolve_key`, `llm.collect_usage`, `ai_activity.registrar_uso` — all generic), only `opcoes_curadoria.narrativa_user()`'s per-item line template is the actual touch point, and it lives in the other file.

---

### `server/app/store.py` — D-05 discovery-time gate, reference only (Fase 29 invariant, do not modify)

**Analog:** `server/app/store.py:815-828` (inside `buy_option`, the naked-call execution path).

```python
cfg = get(conn, "config", user_id=user_id) or {}
if not cfg.get("permitirOpcaoADescoberto"):
    registrar_rejeicao(conn, "COMPRA", cid, qty, price, MOTIVO_DESCOBERTO_DESLIGADO,
                        user_id=user_id, origem=origem)
    raise ValueError(MOTIVO_DESCOBERTO_DESLIGADO)
```
CONTEXT.md D-05 and canonical_refs are explicit: **this file does not change**. It is cited only as the pattern for HOW to read the flag (`cfg.get("permitirOpcaoADescoberto")`, config defaults to `False` per `store.py:102`'s backfill comment). The new read belongs in `opcoes_curadoria.py`/`main.py`'s discovery path (see above), structured as a silent skip, not a raise+rejection-log — those two behaviors (execution rejection vs. discovery filtering) are deliberately different and should not be unified into one function.

---

### `web/src/opcoes/PayoffChart.jsx` — responsiveness fix, not a rewrite (D-07/D-08)

**Analog:** itself (305 lines, read in full).

The component already uses the scale-safe pattern: `viewBox="0 0 320 180"` + `preserveAspectRatio="xMidYMid meet"` + `width: "100%", height: "auto"` (lines 228-233), which is the correct SVG responsive idiom — it is NOT true that this file has no responsive behavior at all. **The concrete gap for D-07 is legibility at small rendered width, not scaling failure**: all internal text is sized in SVG user-space units tied to the fixed 320×180 viewBox (`fontSize="9.5"` for breakeven labels, line 266; `fontSize="11"` for the unlimited-side arrows, lines 290/293; `fontSize="9.5"` for cenário labels, line 280) — when the SVG's rendered width drops below ~320 CSS px (likely on a 375px-wide screen once outer page margins + the `caixa()` wrapper's `padding: "12px"`, line 194, are subtracted), these labels shrink proportionally and can become illegible. There is no media query or minimum-font clamp anywhere in this file today.

**Call sites to check for actual rendered width** (both currently unconstrained by any fixed-width wrapper, both inside `display: grid, gap: 10px` blocks — `OpcoesScreen.jsx:922` and `OpcoesScreen.jsx:1100`):
```jsx
<PayoffChart estrutura={proposta.dados.estruturas[0]} emReais={proposta.dados.emReais} cp={cp} palette={palette} />
```
No 375px-specific test exists today — confirmed via grep on `web/tests/test_curadoria_ui.mjs` (0 hits for "375"/"viewport"/"resize"). This is a real gap, not a pre-existing pattern to copy: whatever fix ships (larger minimum font-size floor in SVG user-space, a `vector-effect="non-scaling-stroke"`-style approach for text, or clamping the viewBox aspect differently for narrow containers) is new work within this file, scoped by D-07/D-08 to "make legible at 375px, no overlay, no interactivity, still 1 estrutura at a time." The `cabecalho` block above the SVG (lines 164-190) is regular DOM text (`fontSize: "13px"`, `"11.5px"`, `"11px"` as CSS, not SVG units) and already reflows normally — that part is not the concern; the SVG text sizing is.

---

### `web/src/App.jsx` — `CuradoriaEstruturas` / `useCuradoria` extension point (Posições screen)

**Analog:** itself, `CuradoriaEstruturas` (4179-4249) and `useCuradoria` (4498-4547).

**Current card list rendering** (4187-4207) — carousel of `top` items, each a `call_coberta` structure, keyed by `contractSymbol`:
```jsx
{top.length > 0 && (
  <div style={carouselTrackStyle({ gap: "10px", scrollbarWidth: "none", paddingBottom: "2px" })}>
    {top.map((item) => (
      <button key={item.contractSymbol} type="button" ... onClick={() => onAbrir(item.ticker)}>
        <div>{item.posicaoNoRanking}. {item.ticker}</div>
        <div>{item.manchete}</div>
        <div>{cp.curadoriaRazaoRotulo}: {item.razao != null ? item.razao.toFixed(2) : "—"}</div>
        <div>{money(item.premioTotal)} · {item.diasParaVencimento}d · {item.liquidez && item.liquidez.faixa}</div>
      </button>
    ))}
  </div>
)}
```
This already renders generically off `item.manchete`/`item.razao`/`item.premioTotal`/`item.diasParaVencimento`/`item.liquidez` — if the extended backend candidates for put/collar/naked keep the same field shape (which `opcoes_curadoria.py`'s per-item dict construction, lines 150-178, already guarantees via `skill_ref.opcoes_lastreadas_txt` for `manchete`/`didatica`), **this card list likely needs zero changes** beyond a possible `item.tipo`-based icon/badge if the plan wants visual differentiation between the 4 estrutura types. `contractSymbol` as the React key may collide for multi-leg estruturas (collar has 2 option legs, no single `contractSymbol`) — flag this for the plan: the key needs to become something like `item.tipo + "-" + (item.contractSymbol || item.ticker + item.expiration)`, mirroring the existing multi-candidate key pattern already used elsewhere in this file at `key={c.tipo + "-" + (c.contractSymbol || "collar")}` (line 4303, inside `PropostaDaPosicao`'s multi-candidate branch) — this is a directly reusable precedent for exactly this collision.

**`useCuradoria()` fetch/state shape** (4498-4547) — no-param fetch on mount, separate opt-in `narrar()` call, `aliveRef` guard against unmounted-state writes:
```jsx
useEffect(() => {
  aliveRef.current = true;
  setCarregando(true);
  store.opcoesCuradoria()
    .then((r) => { if (!aliveRef.current) return; setTop((r && r.top) || []); setMeta(r || null); })
    .catch(() => { if (aliveRef.current) setErro(true); })
    .finally(() => { if (aliveRef.current) setCarregando(false); });
  return () => { aliveRef.current = false; };
}, []);
```
No new hook needed — the backend route contract (`GET /api/options/curadoria` returns `{top, meta...}`) does not change shape for this phase (more items in `top`, same envelope), so this hook can stay as-is. `store.opcoesCuradoria()` (client call, `web/src/persistence.js:279-280,1342-1348`) is a thin passthrough to `api.opcoesCuradoria()` and also needs no change.

## Shared Patterns

### Closed-door contract (pure functions never raise, always return `[]`/`None`)
**Source:** `server/app/opcoes_curadoria.py` (module docstring + every gate in `candidatos_da_posicao`), `server/app/opcoes_motor.py:52-67` (`rastrear`'s docstring: "nunca `None` e nunca uma exceção").
**Apply to:** every new estrutura-generation branch added inside `candidatos_da_posicao` or its siblings — put/collar/naked candidates all follow the same "closed door → skip, never raise" discipline as venda coberta today.

### Determinism guardrail (`exigir_ranking` / princípio 5)
**Source:** `server/app/opcoes_curadoria.py:209-239` (`exigir_ranking`), reinforced by `server/app/curadoria_narrativa.py:44-50` (first line of `narrar()` body calls `exigir_ranking(top)` before touching the LLM).
**Apply to:** any new code path that produces a `top` list for narration must go through `rankear()`/`exigir_ranking()` unchanged — no new bypass for the 4-estrutura case.

### Network-cost declaration discipline (D-01/D-03)
**Source:** `server/app/options_provider_mydata.py:206-219` (comment on `_debita`), `server/app/main.py:3319-3325` (comment on `_curadoria_top`'s single-call-per-position guarantee).
**Apply to:** the plan's task description for the N-vencimento fetch must explicitly state the new call count (up to 3 mydata calls per elegible position: 1 `get_vencimentos` + up to 2 `get_options_chain`) against the measured budget in `docs/MEDICAO-Mydata-2026-08-27.md`, exactly as D-03 in CONTEXT.md requires.

### Config-flag read pattern (`permitirOpcaoADescoberto`)
**Source:** `server/app/store.py:102` (default `False` on backfill), `server/app/store.py:319-328` (write-side accept-only-with-terms gate), `server/app/store.py:825` (execution-time read).
**Apply to:** the new discovery-time read in `opcoes_curadoria.py`/`main.py` — same `cfg.get("permitirOpcaoADescoberto")` boolean read, but silent-skip semantics instead of raise+reject semantics (see the dedicated section above).

## No Analog Found

None — every file in scope for this phase is an in-place extension of an existing, already-read file. There is no genuinely new module, route, or component being introduced.

## Metadata

**Analog search scope:** `server/app/opcoes_curadoria.py`, `server/app/curadoria_narrativa.py`, `server/app/opcoes_motor.py`, `server/app/options_provider_mydata.py`, `server/app/store.py`, `server/app/main.py` (curadoria routes), `web/src/opcoes/PayoffChart.jsx`, `web/src/opcoes/OpcoesScreen.jsx` (call sites), `web/src/App.jsx` (`CuradoriaEstruturas`/`useCuradoria`/`PropostaDaPosicao`), `web/src/persistence.js` (client wrappers), `server/tests/test_opcoes_curadoria*.py`, `web/tests/test_curadoria_ui.mjs`
**Files scanned:** 12 read in full or targeted ranges; 2 grep sweeps (call-site discovery, 375px test coverage)
**Pattern extraction date:** 2026-09-14
