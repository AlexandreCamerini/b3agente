# Phase 36: Motor de Payoff Genérico - Pattern Map

**Mapped:** 2026-09-21
**Files analyzed:** 2 (both MODIFIED, none created — D-01 forbids a parallel motor)
**Analogs found:** all new functions have an analog in the SAME file — this phase
extends `opcoes_payoff.py`, so "closest analog" means "closest existing function
in this module," not a different module.

**Scope reminder (from CONTEXT.md D-01):** no new file is created. Every unit of
work below lands in `server/app/opcoes_payoff.py` (implementation) and
`server/tests/test_opcoes_payoff.py` (tests). Do not classify this phase as
file-to-file mapping — classify function-to-function within the same module.

## File Classification

| File | Role | Data Flow | Change type |
|------|------|-----------|-------------|
| `server/app/opcoes_payoff.py` | service (pure calculation module, no I/O) | transform (pernas in → dict out) | extend: new field, bugfix, 2 new functions |
| `server/tests/test_opcoes_payoff.py` | test | request-response (call function, assert dict/exception) | extend: new test cases per D-07 |

No controller/route/model files are touched. `opcoes_motor.py`,
`opcoes_lastreadas.py`, `opcoes_curadoria.py`, `options_mcp_api.py` are
consumers, read-only for this phase (verified below) — do not classify them as
files to modify unless a task explicitly needs to thread `vencimento` through
an adapter.

## Verified retrocompatibility (empirical, not assumed — for D-03)

Traced all 4 consumers named in CONTEXT.md's canonical_refs:

- `server/app/opcoes_motor.py:204` — `avaliar()` is a direct, zero-logic
  delegation to `perfil_da_estrutura(pernas)`. It does not read or set
  `vencimento` anywhere in the file.
- `server/app/opcoes_motor.py:127-186` — `perna_de_contrato()` and
  `perna_de_acao()` are the only two places that build a perna dict from
  scratch. Neither sets a `vencimento` key today (checked full dict literals
  at lines 157-165 and 178-186).
- `server/app/opcoes_lastreadas.py` — never calls `opcoes_payoff` directly;
  every call site (lines 94, 108, 253, 330, 393, 494) goes through
  `opcoes_motor.avaliar(pernas)`, where `pernas` is built by
  `opcoes_motor.perna_de_contrato`/`perna_de_acao` — same conclusion as above.
- `server/app/opcoes_curadoria.py` — **corrected after an initial mis-trace:
  this file DOES import and use `opcoes_motor` directly** (`from . import
  opcoes_motor, skill_ref, store` at line 44), the same adapter/delegation
  pattern as `opcoes_lastreadas.py` — `opcoes_motor.rastrear()` (lines 237,
  321), `opcoes_motor.perna_de_contrato()`/`perna_de_acao()` (lines 251-252,
  328-329, 389-392, 493), `opcoes_motor.avaliar()` (lines 103, 253, 330, 393,
  494). It is a transitive consumer of `opcoes_payoff.perfil_da_estrutura`
  through `opcoes_motor.avaliar`, exactly like `opcoes_lastreadas.py` — not a
  non-consumer as an earlier pass of this trace concluded. It builds pernas
  exclusively via the same two `opcoes_motor` adapters (never a bare dict
  literal), so it inherits the same conclusion: neither adapter sets
  `vencimento` today (already verified above), so this file requires zero
  changes for D-03's optional field to be safe. Verification command run to
  confirm cleanly: `grep -n "^from\|^import" server/app/opcoes_curadoria.py |
  grep "opcoes_motor\|opcoes_payoff"` → returns exactly the line-44 import.
- `server/app/options_mcp_api.py` — consumes the OUTPUT dict of
  `perfil_da_estrutura` (via `opcoes_motor.avaliar`) in `_em_reais()`
  (line 1289) and the `/possibilidades` route (~2276-2437). `_em_reais` reads
  `net_cost`/`max_gain`/`max_loss`/`scenarios` keys only — it does not read or
  write `vencimento`.

**Direct vs. transitive, stated plainly (CONTEXT.md's "4 consumidores em
produção" doesn't make this distinction):** of the 4, only
`opcoes_motor.py:avaliar()` calls `perfil_da_estrutura` directly.
`opcoes_lastreadas.py`, `opcoes_curadoria.py`, and `options_mcp_api.py` are
all transitive — they only ever reach `opcoes_payoff` through
`opcoes_motor.avaliar`/`opcoes_motor`'s two perna-building adapters. This
doesn't change the retrocompatibility conclusion (still zero required
changes), but it does mean any FUTURE task that needs to inspect or set
`vencimento` from one of these 3 files has exactly one chokepoint to touch
(`opcoes_motor.py`'s adapters), not three separate call sites.

**Conclusion for the planner:** making `vencimento` an optional per-perna
field with default `None` is safe with ZERO changes required to any of the 4
consumers. A task to "thread vencimento through the adapters" is optional
scope, not a retrocompatibility requirement — only add it if a later phase
needs `opcoes_motor.perna_de_contrato` to populate it from the ADR-004
contract dict (it has an `expiration`-shaped field available if so; not
verified here since out of scope for D-03 itself).

## Function Classification (the real unit of work for this phase)

| New/changed unit | Role | Closest analog (same file) | Match quality |
|---|---|---|---|
| `vencimento` field on perna + `_validar_perna` extension (D-03) | validation | `_validar_perna()` lines 64-117 | exact — same function, additive field |
| Calendar-divergence guard in `perfil_da_estrutura` (D-03) | validation / early-return state | `resultado_no_vencimento`'s "sem pernas" guard, lines 151-152 (raise before doing work) + `_delta_total`'s "declare a reason for a degraded result" idiom, lines 260-276 | role-match |
| `_breakevens` fix — stop reporting spurious `S=0` (D-04.2) | core transform (bugfix in existing function) | the function itself, `_breakevens()` lines 232-257 — fix in place, do not rewrite the interpolation branch (lines 246-247) which is already correct | exact |
| Degenerate-entry rejection (D-04.1) | validation / guard clause | `_validar_perna`'s `ValueError` citation style (lines 64-117) generalized to whole-structure scope, placed like the early guard in `perfil_da_estrutura` lines 174-175 (`if not pernas: raise ValueError(...)`) | role-match |
| Domain X/Y function (D-05) | new pure function, transform | `perfil_da_estrutura()` lines 161-229 for shape/docstring convention; `ganho_ilimitado`/`perda_ilimitada` sign-classification idiom lines 202-211 for the "unbounded side signals instead of drawing a fake bound" logic | role-match |
| Segments function (D-06) | new pure function, transform | `_breakevens()` lines 232-257 for "walk the curve left to right, classify each stretch" shape; reuses `curva`, `breakevens`, `inclinacao_direita` as inputs — do not recompute | role-match |
| New pytest cases (D-07) | test | existing `test_opcoes_payoff.py` — Parte 2 block, lines 123-221 (naming convention `test_<function_or_concept>_<scenario>`) | exact |

## Guard ordering — D-03 vs D-04.1 (both fire at the same point in `perfil_da_estrutura`)

Both the calendar-divergence guard (D-03) and the degenerate-entry guard
(D-04.1) are placed after `normalizadas`/`custo` are computed and before
curve-building (see Analog B and D-04.1 below — same insertion point).
A structure CAN trigger both simultaneously (e.g., offsetting legs with zero
net cost but different `vencimento` values). CONTEXT.md does not state
precedence. Recommendation for the planner to lock down explicitly in the
plan (not left to the executor to improvise): check calendar-divergence
FIRST. Rationale — "vencimentos diferentes" is a structural fact about the
input itself (unrelated legs, arguably not one "estrutura" in the payoff
sense at all), while degeneracy is a fact about the computed result; a
malformed/ambiguous input should fail on the more fundamental defect before
the engine even asks whether the (not-yet-well-defined) result is degenerate.
This ordering choice needs a dedicated D-07 test (structure with both
divergent vencimento AND zero net cost/flat curve) asserting which message
comes back, so the choice is pinned by a guardian test, not left implicit.

## Pattern Assignments

### D-03 — `vencimento` field + calendar degradation

**Analog A — field addition + validation, `_validar_perna` (lines 64-117):**

Current signature and return dict end (lines 108-117):
```python
    return {
        "contrato": perna.get("contrato"),
        "tipo": tipo,
        "lado": lado,
        "sinal": 1.0 if lado == "compra" else -1.0,
        "strike": strike,
        "premio": premio,
        "quantidade": quantidade,
        "delta": _numero(perna.get("delta")),
    }
```
`vencimento` should be read the same way `delta` is read — optional,
passthrough, no validation failure on absence (`_numero(perna.get("delta"))`
returns `None` silently for missing/malformed input; follow that exact
permissiveness for `vencimento` since D-03 requires it to stay optional with
default `None`, not error on omission). Do NOT model it after `strike`/`premio`
(those raise `ValueError` when invalid) — a bad `vencimento` type is a
different failure class than a missing one; if validation is wanted, cite the
`_tipo`-style guard-clause pattern (lines 55-57, 70-73) with index+field in
the message, matching `_validar_perna`'s citation convention:
```python
raise ValueError(f"perna {i}: tipo precisa ser CALL, PUT ou ACAO, veio {perna.get('tipo')!r}")
```

**Analog B — early guard-clause-before-work, `perfil_da_estrutura` (lines 174-175) and `resultado_no_vencimento` (lines 151-152):**
```python
    if not pernas:
        raise ValueError("estrutura sem pernas: informe ao menos um contrato")
```
The divergent-vencimento check (D-03: "vencimentos DIVERGENTES → estado
explícito, nunca aproxima linearmente") belongs at this same point in
`perfil_da_estrutura` — after `normalizadas = [_validar_perna(...) ...]`
(line 177) but before the curve is built (line 184) — because building a
curve for mismatched-expiry legs is exactly the "aproxima linearmente"
D-03 forbids. Do not compute `custo`/`curva`/`breakevens` first and patch the
result after; short-circuit like the guard above. See "Guard ordering" note
above for how this interacts with D-04.1's guard at the same point.

**Analog C — declare-a-reason-for-a-degraded-result idiom, `_delta_total` (lines 260-276):**
```python
    if faltando:
        return {"valor": round(total, 4), "pernas_sem_delta": faltando,
                "motivo": "soma parcial: alguma perna não tem delta calculado"}
    return {"valor": round(total, 4), "pernas_sem_delta": 0, "motivo": None}
```
D-03's "estado explícito" for divergent vencimentos should follow this exact
shape (a `motivo`/reason string key sitting next to the degraded fields,
never a bare `None` with no explanation) rather than inventing a new error
schema. "Pernas com vencimento omitido (`None`) são tratadas como mesmo
vencimento implícito entre si" (CONTEXT D-03) — so the divergence check is:
group non-`None` vencimentos, and only trip if that set has more than one
distinct value; `None`-only or single-distinct-value structures behave exactly
as today (zero behavior change, verified by the golden-case run already done
in CONTEXT.md's D-01 discussion).

---

### D-04.1 — Degenerate-entry rejection

**Root cause traced concretely (not from CONTEXT.md's prose alone):**
Same leg bought and sold at identical strike/premium produces
`normalizadas` with `custo_liquido == 0` and, critically,
`inclinacao_direita == 0` too (the two opposite `sinal`s cancel in the sum at
`perfil_da_estrutura` lines 198-200) — meaning the curve is flat zero not just
at the evaluated breakpoints but for the ENTIRE right tail as well. That
`inclinacao_direita == 0` check is what distinguishes true degeneracy from
D-04.2's case 2 below (CALL comprada premio 0 has `inclinacao_direita == 1`,
i.e. real exposure past the strike).

**Where to add the guard:** same spot as Analog B above (after
`normalizadas`/`custo` are computed, lines 177-179, before curve-building at
line 184) — cheap to check (`custo == 0` from line 179, and
`inclinacao_direita` needs to be computed before this point instead of after,
i.e. this guard forces moving the `inclinacao_direita` computation earlier
than its current position at lines 198-200). Message should follow
`_validar_perna`'s directness (no hedging language), e.g. in the register of:
```python
raise ValueError("estrutura sem exposição: custo líquido e resultado são zero em qualquer preço — não há o que analisar")
```
(exact wording is Claude's Discretion per CONTEXT.md — this is illustrative,
matching the file's existing PT-BR tone.)

**Explicit non-example (must NOT be rejected):** box / resultado constante
NÃO-zero — same shape (flat curve, `inclinacao_direita == 0`) but
`custo_liquido != 0` in that case's classic construction OR the flat nonzero
value comes from the extremes, not from `custo==0`. The guard must check
`custo == 0 AND all(ponto["resultado"] == 0 for ponto in curva) AND
inclinacao_direita == 0` — all three, not fewer — otherwise a legitimate
locked-nonzero-result box gets wrongly rejected. D-07 requires a dedicated
test for this box case precisely so this three-part condition doesn't
regress toward two parts.

---

### D-04.2 — `_breakevens` bugfix (spurious `S=0`)

**Analog: the function itself, `_breakevens()` (lines 232-257) — fix in place:**
```python
    for anterior, atual in zip(curva, curva[1:]):
        y0, y1 = anterior["resultado"], atual["resultado"]
        x0, x1 = anterior["preco_objeto"], atual["preco_objeto"]
        if y0 == 0:
            pontos.append(x0)          # <-- BUG: fires unconditionally
        if (y0 < 0 < y1) or (y1 < 0 < y0):
            pontos.append(round(x0 + (x1 - x0) * (-y0) / (y1 - y0), 4))
```
The interpolation branch (last 2 lines) is already correct and is what
produces the golden case's `[49.42]` and the straddle's `[48.0, 52.0]` —
do not touch it. Only the `if y0 == 0:` line is the bug.

**Concrete repro traced by hand (for the planner to cite in the task, not
re-derive):**
- Degenerate case (rejected entirely by D-04.1's new guard, so `_breakevens`
  never even sees it post-fix): `curva = [(0.0, 0.0), (strike, 0.0)]`,
  `inclinacao_direita = 0`. Today (pre-fix, pre-guard):
  `breakevens = [0.0, strike]` — both spurious.
- Case 2, CALL comprada premio 0 (must survive as a valid, non-degenerate
  structure per CONTEXT.md): same `curva = [(0.0, 0.0), (strike, 0.0))]` shape
  but `inclinacao_direita = 1` (bought CALL, sinal +1, qty 1, counted in the
  `("CALL", "ACAO")` sum at lines 198-200). Today: `y0==0` at the first pair
  fires → `pontos = [0.0]`; then the tail check (`ultimo["resultado"]==0` →
  append `ultimo["preco_objeto"]`) adds `strike` → final
  `breakevens = [0.0, strike]`. **Correct answer per D-04.2: `[strike]`
  only** — `0.0` is not a real crossing, the curve is flat at zero from 0 to
  strike then rises; there is no sign change at `x0=0`.

**Structural fix direction (grounded, not final — algorithm choice is
implementation, but the SHAPE should follow an existing idiom in this file):**
the `ganho_ilimitado`/`perda_ilimitada` classify-by-sign idiom (lines 202-204,
`ganho_ilimitado = inclinacao_direita > 0`) is the file's established pattern
for "decide a boolean/state from the sign of a delta, not from a raw
comparison in isolation." Apply the same discipline here: `y0 == 0` alone is
not sufficient signal — the fix needs to look at whether a REAL sign change
happens around that zero point (compare the sign entering the zero point
against the sign leaving it, walking forward through the tail's
`inclinacao_direita` when `x0`/`x1` is the last segment). A zero point that
is approached AND left on the same side (both segments non-negative, or both
non-positive, i.e. the curve merely touches zero without crossing through it)
is not a breakeven; only a genuine sign change is. Write the exact
walk/compare logic as its own reviewable unit (mirrors `_delta_total`'s
separation of "compute" from "report/classify") rather than inline in the
existing loop, so the D-07 test cases (straddle/strangle, borboleta/condor
with a platô central, box) can each assert against it directly.

---

### D-05 — Domain X/Y function (new)

**Analog: `perfil_da_estrutura()` (lines 161-229) for shape; sign-classify idiom (lines 202-211) for the unbounded-side behavior.**

Function should be a new top-level function alongside `perfil_da_estrutura`,
same file (Claude's Discretion per CONTEXT.md on file location — CONTEXT
explicitly says "not mix rendering concepts into the pure financial
calculation function," meaning a SEPARATE function, still in this module, not
inlined into `perfil_da_estrutura`'s return dict).

Suggested signature mirrors `perfil_da_estrutura(pernas)`'s "take normalized
input, return a plain dict" shape — likely takes the ALREADY-COMPUTED profile
dict plus `spot` as input (avoid recomputing `normalizadas`/`curva` a second
time — this is exactly the "don't build a second aritmética" principle cited
throughout `opcoes_lastreadas.py`, e.g. line 88-93's comment about not
duplicating `custo_liquido - premio_put` by hand).

**Margin formula traced against the golden case (CONTEXT.md's numbers), so
the planner has verified arithmetic to cite:**
Golden case strikes `[49.17, 49.67]`, span `= 0.50`.
`0.12 * span = 0.06`. For `0.04 * spot` to matter (dominate the `max()`),
spot just needs to be a realistic equity price (tens of reais) — e.g. spot
`≈ 49.4`: `0.04 * 49.4 = 1.976`, so `margem = max(0.06, 1.976) = 1.976`
(the 4%-of-spot term dominates for any realistic spot on a sub-R$1 wide
spread — this is the expected common case, not an edge case, worth a
dedicated D-07 test with these exact numbers).
Domain X `= [49.17 - 1.976, 49.67 + 1.976] = [47.194, 51.646]`, and spot
`49.4` already falls inside it (no expansion needed for the golden case —
D-07 should add a SEPARATE test where spot falls outside, to exercise the
"expand the side that's missing" clause of D-05).
Single-strike case (e.g. CALL seca strike 40, no span): `margem = 0.10 * 40 =
4.0` → domain `[36.0, 44.0]`.

Y domain: "inclui zero sempre; estende 15% além do extremo finito." Golden
case per-unit `ganho_maximo = perda_maxima = 0.25` (both finite, neither
unlimited — matches `ganho_ilimitado=False, perda_ilimitada=False` from the
already-verified golden run in CONTEXT.md D-01): extreme `= 0.25`, `Y domain
≈ [-0.2875, 0.2875]` (0.25 × 1.15, rounded per the file's existing
`round(x, 4)` convention used everywhere, e.g. lines 122, 158, 206, 247, 255,
272, 276). For an unbounded side, D-05 says devolve the existing
`ganho_ilimitado`/`perda_ilimitada` booleans (already computed, do not
reinvent a schema) — the new function's job is only to say "don't draw a
false ceiling," i.e. `y_max = None` (following the file's `None`-has-a-reason
convention, module docstring lines 13-17) when `ganho_ilimitado` is `True`,
not `0.0` and not a made-up large number.

---

### D-06 — Segments function (new)

**Analog: `_breakevens()` (lines 232-257) for the "walk `curva` pairwise,
left to right" shape — reuse, don't recompute:**
```python
    for anterior, atual in zip(curva, curva[1:]):
        y0, y1 = anterior["resultado"], atual["resultado"]
        x0, x1 = anterior["preco_objeto"], atual["preco_objeto"]
        ...
```
The segments function walks the same `curva` list the same way, but instead
of looking for zero-crossings, classifies each `(x0,x1)` stretch's slope sign
(`"negativa"|"zero"|"positiva"` per D-06's proposed schema) directly from
`(y1 - y0)`. The final open-ended segment (`{"de": <last strike>, "ate":
None, ...}`) is the direct translation of the existing `inclinacao_direita`
tail-handling already in `_breakevens` (lines 252-255) and in
`perfil_da_estrutura`'s `ganho_ilimitado`/`perda_ilimitada` (lines 202-204) —
same signal, reformatted as a segment instead of a boolean/breakeven point.
There is no left-open tail (`S<0` is not a valid preço do objeto — validated
by `_numero`/the `s < 0` guard in `resultado_no_vencimento` line 154), so the
FIRST segment's `de` is always `0.0`, never `None` — asymmetric with `ate`,
matching the module's existing asymmetry (curve is only ever evaluated for
`S >= 0`, line 184's `avaliar = sorted({0.0, ...})`).

`e_plato` (is-a-plateau, per D-06's proposed schema) is `True` when
`inclinacao == "zero"` for that segment — likely redundant with `inclinacao`
as a field but CONTEXT.md's D-06 example dict includes both explicitly,
follow it as given (Claude's Discretion is only on FIELD NAMES per CONTEXT,
not on whether the field exists).

**IMPORTANT — CONTEXT.md's golden-case segment example does not match the
curve arithmetic; verified by hand and by direct Python computation, do not
copy it as a test fixture as-is.**
CONTEXT.md's `<specifics>` block gives:
```python
{"de": 0.0, "ate": 49.42, "inclinacao": "zero", "e_plato": True}
{"de": 49.42, "ate": 49.67, "inclinacao": "positiva", "e_plato": False}
{"de": 49.67, "ate": None, "inclinacao": "zero", "e_plato": True}
```
Recomputing the golden case's curve directly (bull call spread, long 49.17
call / short 49.67 call, custo 0.25 — verified by running
`resultado = max(S-49.17,0) - max(S-49.67,0) - 0.25` at S=0, 49.17, 49.42,
49.67):
```
S=0.00  -> -0.25   (flat: both legs OTM)
S=49.17 -> -0.25   (still flat: this is where the flat stretch ENDS)
S=49.42 ->  0.00   (breakeven — INSIDE the rising stretch, not a kink)
S=49.67 ->  0.25   (flat begins: this is where the rise ENDS)
```
The curve only bends at the strikes (49.17 and 49.67) — the slope is
uniformly positive across the WHOLE `[49.17, 49.67]` stretch, including the
sub-piece from 49.17 to 49.42. The breakeven at 49.42 is a zero-crossing
POINT, not a slope-change point. So the constant-slope segmentation that
matches `_breakevens`'s "walk curva pairwise" analog produces:
```python
{"de": 0.0, "ate": 49.17, "inclinacao": "zero", "e_plato": True}
{"de": 49.17, "ate": 49.67, "inclinacao": "positiva", "e_plato": False}
{"de": 49.67, "ate": None, "inclinacao": "zero", "e_plato": True}
```
— boundary `49.17`, not `49.42`. CONTEXT.md's own text frames its dict as
"formato proposto... ponto de partida pro planner" (a shape illustration),
unlike the breakeven/ganho-máximo numbers elsewhere in D-01 which are
explicitly marked "Verificado... por execução direta." This segment example
was not verified the same way, and the numeric boundary in it does not survive
verification.

Two ways this resolves — flag both to the planner rather than picking
silently:
1. **Segments are constant-slope curve stretches** (matches "Derivado de
   `curva`" in D-06's own text, and matches the `_breakevens`-style walk this
   PATTERNS.md points to as the analog) → boundaries are strikes only
   (49.17/49.67), and the corrected 3-segment dict above is right. Under this
   reading, `breakevens` inform NARRATION (which segment contains a sign
   change, for Fase 37 to phrase "vira positivo por volta de 49,42") but do
   NOT split the segment list itself.
2. **Segments also split at every breakeven** (matches D-06's literal text
   "Derivado de `curva` + `breakevens` + a cauda," which lists `breakevens`
   as a distinct input, not just narration) → the golden case would have 4
   segments (0→49.17 flat, 49.17→49.42 positive-but-still-negative-result,
   49.42→49.67 positive-and-positive-result, 49.67→None flat), not the 3
   CONTEXT.md's dict shows. This reading is consistent with D-06's stated
   inputs but produces a DIFFERENT boundary count than CONTEXT.md's example,
   which only ever shows 3.

Neither reading reproduces CONTEXT.md's literal dict (3 segments, but split
at 49.42 instead of 49.17). This is a genuine ambiguity in the locked
decision, not a pattern-mapping question — the planner should surface it as
an open point for the Alex to confirm (one-line question: "segmentos cortam
só nos strikes, ou também em cada breakeven?") before writing the D-06 task,
rather than the executor guessing during implementation. Whichever reading is
chosen, the analog and mechanics above (walk `curva`, classify slope sign,
merge in `breakevens` as extra cut points only if reading 2 is chosen) still
apply — only the boundary set changes.

---

### D-07 — New test cases

**Analog: `test_opcoes_payoff.py` Parte 2 block (lines 123-221), naming and shape convention:**
```python
def test_perfil_venda_coberta_ganho_limitado():
    r = m.perfil_da_estrutura([
        {"tipo": "ACAO", "lado": "compra", "premio": 30},
        {"tipo": "CALL", "lado": "venda", "strike": 32, "premio": 1.5},
    ])
    assert r["ganho_ilimitado"] is False
    assert r["perda_ilimitada"] is False
    assert r["ganho_maximo"] == 3.5
    assert r["breakevens"] == [28.5]
```
Naming: `test_<função_ou_conceito>_<cenário>`, all lowercase snake_case,
descriptive enough to read as a spec (matches every existing test name in the
file, e.g. `test_perfil_collar_travado_dos_dois_lados`,
`test_delta_total_perna_sem_delta_declara_soma_parcial`). For an exception
case, follow the `pytest.raises` + message-substring-assert idiom used
throughout Parte 1, e.g.:
```python
def test_resultado_no_vencimento_sem_pernas_recusa_citando_sem_pernas():
    with pytest.raises(ValueError) as exc:
        m.resultado_no_vencimento([], 10)
    assert "sem pernas" in str(exc.value)
```
Use this exact shape for the degenerate-entry-rejection test (D-04.1) and the
calendar-divergence test (D-03), asserting a specific substring of the
PT-BR message rather than the full string (matches the file's existing
tolerance for exact wording — none of the existing exception tests assert
full string equality).

Required new cases per D-07 (mapped to the closest existing test as a
template):
| New test | Template to copy from |
|---|---|
| Golden case, named explicitly (trava de alta 49,17/49,67) | `test_perfil_collar_travado_dos_dois_lados` (multi-field assert shape) |
| Straddle/strangle, 2 breakevens | same template + assert `len(r["breakevens"]) == 2` |
| Borboleta/condor, 2 breakevens + platô central | same, plus a segments-function assertion once D-06 exists |
| Box / resultado constante não-zero | new — assert `r["breakevens"] == []` (no crossing) and every `curva` point has the same nonzero `resultado` |
| Calendário/diagonal degradation | `pytest.raises`-style OR degraded-dict-style depending on D-03's final chosen shape (guard-clause raise vs. `motivo` field — see Analog B/C above) |
| Both D-03 and D-04.1 conditions at once | new — pins the guard-ordering decision above; assert which message/state wins |
| Entrada degenerada (recusa) | `test_resultado_no_vencimento_sem_pernas_recusa_citando_sem_pernas` template (`pytest.raises` + substring) |
| Lote/quantidades assimétricas entre pernas | `test_custo_liquido_venda_coberta`-style (differing `quantidade` per perna, assert `custo_liquido`) |
| Domínio X/Y — 3+ estruturas (unária ilimitada, travada 2 lados, 2+ breakevens) | new function, 3 separate test functions, one per structure shape |
| Segmentos — same 3 structures | new function; use the HAND-VERIFIED golden-case dict from this PATTERNS.md (boundary `49.17`, not CONTEXT.md's literal `49.42`) once the strike-vs-breakeven boundary question above is resolved with the Alex — do NOT copy CONTEXT.md's `<specifics>` dict verbatim, it does not match the curve arithmetic |

## Shared Patterns

### Error citation convention
**Source:** `_validar_perna()`, `server/app/opcoes_payoff.py` lines 64-117
**Apply to:** every new `ValueError` in this phase (D-03 divergent-vencimento
guard if implemented as a raise, D-04.1 degenerate-entry guard)
```python
raise ValueError(f"perna {i}: tipo precisa ser CALL, PUT ou ACAO, veio {perna.get('tipo')!r}")
```
Structure-level errors (not per-perna) drop the `perna {i}:` prefix and follow
`perfil_da_estrutura`'s existing structure-level guard instead:
```python
raise ValueError("estrutura sem pernas: informe ao menos um contrato")
```

### Null-has-a-reason convention
**Source:** module docstring lines 9-17, `_delta_total()` lines 260-276,
`ganho_maximo`/`perda_maxima` lines 206-211
**Apply to:** D-05's Y-domain unbounded side, D-03's divergent-vencimento
state, any new field that can legitimately be "unknown/not applicable" —
never substitute `0.0`, always accompany with either a boolean flag already
in the dict (`ganho_ilimitado`) or an explicit `motivo` string.

### Round to 4 decimals
**Source:** used consistently at lines 122, 158, 186-187, 206, 211, 247, 255,
272, 276 — `round(x, 4)` on every float that leaves the module.
**Apply to:** all new numeric outputs (domain bounds, segment boundaries,
margin calculation intermediate values that get returned).

### Pure module discipline
**Source:** module docstring lines 1-4 ("sem rede, sem banco, sem LLM, sem
leitura de relógio")
**Apply to:** the whole phase — no new function may import `httpx`, `db`,
`llm`, or read wall-clock time. `vencimento` is compared as opaque data
(equality/inequality between pernas), never resolved against "today" inside
this module — date arithmetic against the current date, if ever needed, is a
caller concern (matches how `opcoes_lastreadas.py`/`options_mcp_api.py`
already keep calendar/"days to expiry" logic outside `opcoes_payoff.py`, per
the module docstring's explicit note that `prazo_em_pregoes` was deliberately
NOT ported here).

## No Analog Found

None — every unit of work in this phase has a same-file analog. This is
expected: D-01 explicitly chose "extend the existing motor" specifically so
new code inherits every established convention rather than needing to invent
new ones.

## Metadata

**Analog search scope:** `server/app/opcoes_payoff.py` (full file, 277
lines — read whole, single pass), `server/tests/test_opcoes_payoff.py`
(full file, 222 lines — read whole, single pass), `server/app/opcoes_motor.py`
(targeted: lines 100-205), `server/app/opcoes_lastreadas.py` (targeted: lines
1-16, 70-119, 230-260, 320-395, 480-495 via grep-then-read), `server/app/
opcoes_curadoria.py` (grep-verified: imports `opcoes_motor` at line 44, uses
`rastrear`/`perna_de_contrato`/`perna_de_acao`/`avaliar` throughout — see
"Verified retrocompatibility" above for the corrected trace),
`server/app/options_mcp_api.py` (targeted: lines 1270-1323, plus grep across
full file for `vencimento`/`perfil_da_estrutura` occurrences).
**Files scanned:** 6
**Pattern extraction date:** 2026-09-21
