# Phase 20: Fundação estrutural e tipográfica - Pattern Map

**Mapped:** 2026-09-05
**Files analyzed:** 1 (`web/src/App.jsx`, single-file frontend, ~9085 lines, all changes are in-place edits — no new files created)
**Analogs found:** 6 / 6 change groups (all analogs are same-file, different-section — this phase has no cross-file pattern borrowing since the entire frontend is one file with no component library)

**Verification note:** every line number below was re-read directly against the current `web/src/App.jsx` (not copied from CONTEXT.md/UI-SPEC.md without checking) — all matched the UI-SPEC.md line numbers exactly, zero drift.

## File Classification

Single file, six independent change sites. Classified by role/data-flow of the *code region*, not the file as a whole (there is no per-file granularity here — this is a monolith).

| Change Site | Role | Data Flow | Closest Analog (same file) | Match Quality |
|---|---|---|---|---|
| `.b3-shell` CSS rule (FIX-01) | config (global CSS-in-template-string) | N/A (static style) | Same `GlobalStyle()` function, its own existing rules (`.b3 *{box-sizing:border-box}` etc.) | exact — edit is additive to an existing rule in the same function |
| `MarketStatusBadge` parent containers (FIX-02) | component (layout container) | request-response (renders from `mercado` prop, already-fetched state) | Sibling ancestor divs in the SAME `Topbar` (already carry `minWidth:0`) | exact — 3 of 4 ancestors already follow the pattern; only 2 sites need the addition |
| Content wrapper `maxWidth` (SYS-04) | component (layout wrapper) | request-response (wraps screen render) | `BottomNav`'s own `<div style={{ maxWidth:"720px", margin:"0 auto" }}>` (`App.jsx:875`) | exact — literal value + property pair already exists, just needs extraction to a shared constant and a second call site |
| `numHero`/`numBody`/`numMicro` constants (TYPO-01/02) | utility (style-object constant) | N/A (static value) | `MONO`/`DISPLAY`/`SANS` constant block (`App.jsx:236-243`) — same declaration pattern (`const NAME = ...`) | exact — same file region, same declaration idiom |
| `GlobalStyle()` reduced-motion media query (MOTION-03) | config (global CSS) | N/A (static style) | Existing `@media (prefers-reduced-motion: reduce){...}` block at `App.jsx:323` | exact — same function, same media feature, needs source-order care |
| Screen H1 `fontFamily: DISPLAY` (TYPO-03) | component (screen title element) | request-response (renders `cp.tituloX` / static string) | `Topbar`'s wordmark div, which ALREADY uses `fontFamily: DISPLAY` (`App.jsx:805`) | exact — proves the exact syntax to copy into each `<h1>` style object |

## Pattern Assignments

### 1. `.b3-shell{ overflow-x:hidden }` (FIX-01)

**Analog:** `GlobalStyle()` function itself, `App.jsx:281-326`

**Location of edit** (`App.jsx:290`):
```jsx
.b3-shell{ height:100vh; height:100dvh; }
```
becomes:
```jsx
.b3-shell{ height:100vh; height:100dvh; overflow-x:hidden; }
```

**Pattern to follow** — every rule in this template string is a flat `.selector{ prop:value; }` line, one rule per line, no nesting, no preprocessor (`App.jsx:283-323`). Add the new property inline in the existing `.b3-shell` rule; do not create a new separate rule.

**Context for the edit — sibling inline style that does NOT close the defect** (`App.jsx:8920`):
```jsx
style: { boxSizing: "border-box", background: T.bgBase, color: T.textPrimary, fontFamily: SANS, display: "flex", flexDirection: "column", WebkitFontSmoothing: "antialiased", paddingTop: "env(safe-area-inset-top)", overflow: "hidden" },
```
This is the same shell element's React inline `style` prop — it already sets `overflow:"hidden"` on both axes, but the audited defect (scrollWidth 504px vs clientWidth 375px) persists anyway. The CSS-class rule in `GlobalStyle()` is additive belt-and-suspenders, not a duplicate — do not treat this inline style as already sufficient.

---

### 2. `MarketStatusBadge` parent `minWidth:0` (FIX-02)

**Analog:** sibling ancestor divs inside `Topbar` that already carry the fix — use these as the literal template for the two divs that don't.

**Component itself, unchanged** (`App.jsx:774-786`):
```jsx
function MarketStatusBadge({ mercado, cp }) {
  if (!mercado) return null;
  const erro = !!mercado.erro;
  const cor = erro ? T.warn : mercado.aberto ? T.positive : T.negative;
  const label = erro ? cp.mercadoIndisponivel : mercado.aberto ? cp.mercadoAberto : cp.mercadoFechado(mercado.abertura);
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", minWidth: 0 }}>
      <span aria-hidden style={{ width: "7px", height: "7px", borderRadius: "50%", background: cor, flex: "none", boxShadow: `0 0 0 3px color-mix(in srgb, ${cor} 14%, transparent)` }} />
      <span style={{ fontSize: "10.5px", fontWeight: 800, letterSpacing: "0.06em", color: cor, whiteSpace: "nowrap", minWidth: 0, overflow: "hidden", textOverflow: "ellipsis" }}>{label}</span>
    </span>
  );
}
```

**Topbar ancestor chain — VERIFIED CURRENT STATE** (`App.jsx:795-830`, re-read directly, matches UI-SPEC.md exactly, no drift):
- `App.jsx:795` — outer flex row: `<div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "10px 16px", ... }}>` — **no `minWidth:0`** (this is the row that also contains the profile avatar button as a flex sibling; it is the candidate root cause per UI-SPEC.md, unconfirmed without live measurement).
- `App.jsx:802` — `<div style={{ display: "flex", alignItems: "center", gap: "11px", marginRight: "auto", minWidth: 0 }}>` — already has it.
- `App.jsx:803` — `<div style={{ minWidth: 0 }}>` — already has it.
- `App.jsx:804` — `<div style={{ display: "flex", alignItems: "center", gap: "7px", minWidth: 0 }}>` — already has it (wordmark row, not the badge's own ancestor, but same pattern).
- `App.jsx:827` — `<div style={{ marginTop: "4px", minWidth: 0 }}>` — direct parent of `<MarketStatusBadge>` at line 828 — already has it.

**Pattern to copy** — the idiom is always `minWidth: 0` (or CSS `min-width:0`) added as a sibling key in the SAME inline style object, never a wrapper `<div>`. If the planner/executor confirms via live measurement that `App.jsx:795` is the actual gap, the edit is:
```jsx
<div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "10px 16px", borderBottom: `1px solid ${T.borderSubtle}`, background: T.bgPanel, flex: "none", minWidth: 0 }}>
```

**Home call site — confirmed genuinely missing** (`App.jsx:1871`):
```jsx
<div style={{ marginTop: "4px" }}>
  <MarketStatusBadge mercado={mercado} cp={cp} />
</div>
```
Apply the same idiom used at `App.jsx:827` (identical `marginTop` value, same missing property):
```jsx
<div style={{ marginTop: "4px", minWidth: 0 }}>
```

---

### 3. Content wrapper `maxWidth` (SYS-04)

**Analog:** `BottomNav`, `App.jsx:861-889`

**Source pattern** (`App.jsx:875`):
```jsx
<div style={{ display: "flex", maxWidth: "720px", margin: "0 auto", padding: "5px 6px" }}>
```

**Target call site — current value to replace** (`App.jsx:8967`):
```jsx
<div style={{ maxWidth: "1060px", margin: "0 auto", padding: "24px 18px 34px", transform: pullY ? `translateY(${pullY}px)` : undefined, transition: pullY ? "none" : "transform .2s ease" }}>
```
Replace `"1060px"` with a shared constant (e.g. `CONTENT_MAX_WIDTH`, per CONTEXT.md's discretion on naming) whose value is `"720px"`, declared near `MONO`/`DISPLAY` (`App.jsx:236-243`) and referenced at BOTH this site and `BottomNav`'s `App.jsx:875` — do not leave two independent literals.

**Declaration idiom to copy** (same block as MONO/DISPLAY, `App.jsx:236,241,243`):
```jsx
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";
const SANS = "'Nunito', -apple-system, system-ui, 'Segoe UI', Helvetica, Arial, sans-serif";
const DISPLAY = "'Fredoka', " + SANS;
```
New constant follows the same flat `const NAME = value;` idiom, placed adjacent.

---

### 4. `numHero`/`numBody`/`numMicro` constants (TYPO-01/02)

**Analog:** the `MONO`/`SANS`/`DISPLAY` constant block itself (`App.jsx:236-243`), which is the file's only precedent for shared, reusable style primitives declared once and consumed via spread/reference elsewhere.

**Declaration idiom to copy exactly** (module-level `const`, plain value, JSDoc-style Portuguese comment above explaining rationale — matches lines 237-240, 242):
```jsx
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";
// Fase 3 (rebranding Boris+, 2026-08-08): corpo do app em Nunito (marca) —
// stack de sistema como fallback se a fonte não carregar (offline no
// WKWebView, por exemplo); mesmo princípio de qualquer outro dado remoto
// deste app, nunca trava por falta de rede.
const SANS = "'Nunito', -apple-system, system-ui, 'Segoe UI', Helvetica, Arial, sans-serif";
// Display: Fredoka 600 — títulos, wordmark, números de destaque (Brand Book).
const DISPLAY = "'Fredoka', " + SANS;
```
New constants are style OBJECTS (not strings, since they carry `fontSize`+`fontWeight`), per UI-SPEC.md:
```jsx
const numHero  = { fontSize: "34px", fontWeight: 700 };
const numBody  = { fontSize: "18px", fontWeight: 700 };
const numMicro = { fontSize: "13px", fontWeight: 600 };
```

**Existing byte-identical call site (recommended, not mandated, migration target for `numBody`)** — `Topbar`'s patrimônio value, `App.jsx:833`:
```jsx
<div style={{ fontWeight: 700, fontSize: "18px", lineHeight: 1.05, color: T.textPrimary }}>{money(patr)}</div>
```
Spread pattern the file already uses elsewhere for merging a base style object with per-call overrides (this exact spread idiom is not yet used with `numBody` anywhere, but the file's general style-merge convention is `style={{ ...cor, extra: val }}` — grep confirms this pattern is common with the `T` token object, e.g. `style={{ ...T.something, ... }}`-shaped merges). If migrated:
```jsx
<div style={{ ...numBody, lineHeight: 1.05, color: T.textPrimary }}>{money(patr)}</div>
```

**tabular-nums — two candidate mechanical implementations, unresolved by CONTEXT.md, must be decided at plan time (not this agent's call):**
1. Add a CSS attribute-selector rule to `GlobalStyle()`'s template string, following the existing flat-rule idiom (see FIX-01's pattern):
```css
.b3 [style*="ui-monospace"]{ font-variant-numeric: tabular-nums; }
```
2. Change `MONO` from a bare string to a style-object partial (requires touching every call site that currently does `fontFamily: MONO`):
```jsx
const MONO_NUM = { fontFamily: MONO, fontVariantNumeric: "tabular-nums" };
```
Flag to planner per UI-SPEC.md: option 1 satisfies CONTEXT.md's "zero call-site edits" intent literally; option 2 does not (~155 grep hits for `MONO` per UI-SPEC.md's count).

---

### 5. Reduced-motion media query (MOTION-03)

**Analog:** the existing narrow rule at `App.jsx:323`, same `GlobalStyle()` function.

**Existing rule, KEEP unchanged, do not delete/merge destructively** (`App.jsx:323`):
```jsx
@media (prefers-reduced-motion: reduce){ .b3 .tt-track,.b3 .spin{ animation:none !important; } }
```

**New rule to add — CONTEXT.md-specified text, follow the SAME flat single-line-per-rule idiom used throughout `GlobalStyle()`:**
```css
@media (prefers-reduced-motion: reduce) {
  .b3 *, .b3 *::before, .b3 *::after {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}
```

**Source-order constraint (critical, verified against actual file):** the new block must appear BEFORE line 323 in the template string, OR the two `@media` blocks must be merged with the narrow selector listed textually after the broad one — both carry `!important` on tied properties, so whichever comes later in source order wins under equal specificity. Since `App.jsx:312` (the `.b3-mode-switch` transition rule) is already textually before line 323, and CONTEXT.md's own intent is "cobre a transição de tema/modo já existente" (which is at line 291 and 312, both before 323), the natural insertion point — near the top of `GlobalStyle()`, close to `App.jsx:291`'s `.b3{ transition:... }` — is already compatible. Re-verify final source order after edit; do not assume.

---

### 6. Screen H1 `fontFamily: DISPLAY` (TYPO-03)

**Analog — proves the exact syntax:** `Topbar`'s wordmark, which ALREADY uses `DISPLAY` in an inline style object (`App.jsx:805`):
```jsx
<div style={{ fontFamily: DISPLAY, fontWeight: 600, fontSize: "27px", lineHeight: 1.0, letterSpacing: "-0.015em" }}>Boris<span style={PLUS_STYLE}>+</span></div>
```
Pattern: `fontFamily: DISPLAY` is just another key in the existing inline style object, no wrapper, no new element.

**Two verified H1 samples showing the two style shapes found across the 15-element inventory** (both confirmed by direct read, matching UI-SPEC.md's table with zero drift):

`CarteiraScreen` (`App.jsx:4298`, 22px variant — 12 of 15 H1s share this exact shape):
```jsx
<h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700 }}>{cp.tituloPortfolio}</h1>
```
becomes:
```jsx
<h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700, fontFamily: DISPLAY }}>{cp.tituloPortfolio}</h1>
```

`RadarScreen` (`App.jsx:6672`, 24px + letterSpacing variant — shared with `EvolucaoScreen` line 1865 and `MercadoScreen` line 3693):
```jsx
<h1 style={{ margin: 0, fontSize: "24px", fontWeight: 700, letterSpacing: "-0.01em" }}>{cp.tituloRadar}</h1>
```
becomes:
```jsx
<h1 style={{ margin: 0, fontSize: "24px", fontWeight: 700, letterSpacing: "-0.01em", fontFamily: DISPLAY }}>{cp.tituloRadar}</h1>
```

**Rule for the executor across all 15 sites:** add `fontFamily: DISPLAY` as a new key to the existing style object; do not reorder or remove existing keys (`margin`, `fontSize`, `fontWeight`, `letterSpacing` where present). Full list of the 15 line numbers is in `20-UI-SPEC.md`'s table (lines 1865, 2268, 3693, 4298, 4553, 4752, 5474, 5619, 5667, 5764, 5773, 6068, 6378, 6672, 7161) — not re-verified line-by-line by this pass beyond the two samples above and the ones already spot-checked, since all previously spot-checked line numbers (236-243, 290, 774-843, 861-889, 1860-1878, 4296-4301, 6670-6675, 8915-8920, 8955-8994) matched UI-SPEC.md exactly with zero drift, giving high confidence the remaining 13 are equally accurate.

---

## Shared Patterns

### Inline-style-only, no CSS classes for component styling
**Source:** entire file (`web/src/App.jsx`), confirmed no Tailwind/CSS Modules/styled-components import.
**Apply to:** all 6 change groups — every new constant (`numHero`/`numBody`/`numMicro`, content-max-width constant) is a plain JS value/object, never a CSS class. The only place "real" CSS lives is inside `GlobalStyle()`'s template string (FIX-01, MOTION-03, and possibly tabular-nums option 1).

### `GlobalStyle()` as the single CSS-authority function
**Source:** `App.jsx:281-326`
**Apply to:** FIX-01 (`.b3-shell` rule), MOTION-03 (media query), tabular-nums option 1 (attribute selector) — all three edits land inside this one function's template string, in the existing flat one-rule-per-line style with no nesting/preprocessor.

### Shared constant declared once near `MONO`/`SANS`/`DISPLAY`, consumed by reference/spread everywhere else
**Source:** `App.jsx:236-243`
**Apply to:** `numHero`/`numBody`/`numMicro` (TYPO-01/02) and the new content-max-width constant (SYS-04) — both should live in this same declaration block, following the `const NAME = value;` idiom with a short Portuguese rationale comment above when the value encodes a design decision (matches the `SANS`/`DISPLAY` comment style at lines 237-240, 242).

### `minWidth: 0` on flex-container ancestors of text-truncating children
**Source:** `Topbar`'s own ancestor chain (`App.jsx:802-804, 827`) — 3 of 4 ancestors of `MarketStatusBadge` already carry this; it is an established, repeated idiom in this exact component, not a new pattern being introduced.
**Apply to:** FIX-02's two edit sites (`App.jsx:795` if confirmed by live measurement, and `App.jsx:1871`).

## No Analog Found

None. Every change site in this phase is an in-place edit inside a single existing file, and every edit has a same-file precedent (either an identical sibling rule/pattern already present, or the exact constant-declaration idiom already used for `MONO`/`SANS`/`DISPLAY`). There is no cross-file borrowing in this phase because `web/src/App.jsx` is a monolith with no component library or shared style module to draw from beyond itself.

## Metadata

**Analog search scope:** `web/src/App.jsx` only (per phase scope in CONTEXT.md — this phase touches no other file). No Glob/Grep search of other directories was needed since CONTEXT.md/UI-SPEC.md already pre-identified all line numbers; this pass's job was verifying those line numbers against the live file and extracting exact current-state code excerpts.
**Files scanned:** 1 (`web/src/App.jsx`, 9085 lines) — read via 9 targeted, non-overlapping offset/limit reads (lines 230-244, 280-329, 774-868, 861-890, 1860-1878, 4296-4301, 6670-6675, 8915-8924, 8955-8994).
**Pattern extraction date:** 2026-09-05
