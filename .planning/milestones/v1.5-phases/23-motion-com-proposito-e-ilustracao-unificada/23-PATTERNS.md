# Phase 23: Motion com propósito e ilustração unificada - Pattern Map

**Mapped:** 2026-09-06
**Files analyzed:** 3 (1 modified extensively — `web/src/App.jsx`; 1 modified — `web/src/pet/BorisIntro.jsx`; 1 new — flat Boris illustration component)
**Analogs found:** 3 / 3

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `web/src/App.jsx` — `GlobalStyle()` (new `@keyframes` for MOTION-01/02) | config/style (CSS-in-JS) | event-driven (render-triggered CSS animation) | `GlobalStyle()` itself, `b3spin`/`b3tt`/`b3shimmer` keyframes (lines 359-364) | exact |
| `web/src/App.jsx` — `AtivoCard` entry wrapper (MOTION-01) | component | event-driven (mount/re-render triggered) | `AtivoCard` outer `<div key={t} id="ativo-…">` (line 3438) + `b3-mode-switch` transient-class pattern (lines 7762-7764) | role-match (component) / exact (transient-class mechanism) |
| `web/src/App.jsx` — `BuyModal`/`confirmBuy`/`confirmSell` value pulse (MOTION-02) | component + event handler | request-response (order confirm) | `BuyModal` "Custo estimado" value block (line 7515-7518) + `sweeppulse` keyframe (line 7137) + `b3-mode-switch` transient-class timing (lines 7762-7764) | role-match |
| New Boris flat illustration component (ILUS-01) | component (SVG) | transform (pure render, no I/O) | `LogoMark` (lines 201-231, inline in `App.jsx`) vs. `web/src/pet/Boris.jsx` (separate file) | exact (visual vocabulary) / role-match (file placement) |
| `web/src/pet/BorisIntro.jsx` (swap `<Boris size={110}/>`) | component | transform | itself, current import line 27 (`import Boris from "./Boris.jsx"`) | exact |

## Pattern Assignments

### MOTION-01 — `@keyframes` for card entry (`web/src/App.jsx`, `GlobalStyle()`)

**Analog:** `GlobalStyle()`, existing keyframes block, `web/src/App.jsx:359-364`

```javascript
@keyframes b3spin{ to{ transform:rotate(360deg); } }
.b3 .spin{ animation:b3spin .8s linear infinite; }
@keyframes b3shimmer{ 0%{ background-position:-200px 0; } 100%{ background-position:200px 0; } }
.b3 .sk{ border-radius:6px; background:linear-gradient(90deg, ${T.bgPanel} 25%, ${T.borderSubtle} 37%, ${T.bgPanel} 63%); background-size:400px 100%; animation:b3shimmer 1.2s linear infinite; }
@keyframes b3tt{ from{ transform:translateX(0); } to{ transform:translateX(-50%); } }
.b3 .tt-track{ animation:b3tt 52s linear infinite; }
```

**Structural convention to mirror exactly:**
- Keyframe name prefixed `b3` (`b3spin`, `b3shimmer`, `b3tt`) — a new entry animation should follow suit, e.g. `b3cardin`.
- The class that uses the animation is scoped under `.b3 ` (the app root class), e.g. `.b3 .card-in{ animation:b3cardin .2s ease-out; }` — never a bare global class name, to stay inside the `.b3`-scoped cascade the reduced-motion rule already targets.
- One-shot (non-`infinite`) entry keyframes already exist as the model for MOTION-01: `boris-hop`/`boris-epop`/`boris-etilt` in `web/src/pet/Boris.jsx` (lines 85-93) are finite, single-play keyframes triggered by adding a class once (see MOTION-02 analog below) — same shape as what MOTION-01 needs (fade+translateY once on mount), just relocated to `GlobalStyle()` since `AtivoCard` renders many times in a grid and a per-instance `<style>` tag (see `sweeppulse` pattern) would duplicate needlessly.

**Reduced-motion gate — do NOT touch, only rely on it (already covers new keyframes):**
```javascript
// web/src/App.jsx:384-385
@media (prefers-reduced-motion: reduce){ .b3, .b3 *, .b3 *::before, .b3 *::after, .b3-mode-switch, .b3-mode-switch *{ transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; } }
@media (prefers-reduced-motion: reduce){ .b3 .tt-track,.b3 .spin{ animation:none !important; } }
```
The first rule already zeroes `animation-duration` for any descendant of `.b3` (line 384) — a plain `animation:b3cardin .2s ease-out` on a card inside `.b3` falls under it automatically. No second `@media` block needed (CONTEXT.md is explicit: do not reopen this rule).

**Anti-pattern flagged by CONTEXT.md, present elsewhere in the file — do not copy for this phase:**
```javascript
// web/src/App.jsx:1443 — JS-level media query snapshot, used to swap `transition: "none"` vs a real transition inline
const REDUCE_MOTION = typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
```
This exists in the codebase (used at line 1637 for the bottom-sheet drag transition) but is a second, JS-driven reduced-motion mechanism. CONTEXT.md for Phase 23 explicitly says MOTION-01/02 must fall under the *existing* CSS media-query rule and must NOT introduce a JS-timed alternative — do not extend `REDUCE_MOTION` to the new card/pulse animations; use plain `animation`/`transition` CSS only.

---

### MOTION-01 — Applying the entry class in `AtivoCard` (`web/src/App.jsx`, ~line 3438, and its two call sites)

**Analog 1 — the wrapper to attach the class to:** `web/src/App.jsx:3436-3438`
```javascript
return (
            // id: alvo do scroll quando o usuário chega por um toque no push.
            <div key={t} id={"ativo-" + t} style={{ ...card, padding: "14px 15px" }}>
```
This is the single outer element for both Watchlist (`contexto="watchlist"`, call site `web/src/App.jsx:3896`) and Radar/Mesa (`contexto="radar"`, call site `web/src/App.jsx:6855-6913`) — one conditional `className`/inline `animation` here covers both screens without touching either `.map()` call site's JSX structure, only the data passed in `vm` (a boolean flag such as `vm.isNovo`).

**Analog 2 — transient one-shot class lifecycle (add class, remove after animation duration via `setTimeout`):** `web/src/App.jsx:7762-7765`
```javascript
if (html.classList.contains("b3-mode-operador") !== (appMode === "operador")) {
  html.classList.add("b3-mode-switch");
  setTimeout(() => html.classList.remove("b3-mode-switch"), 450);
}
```
This is the closest existing "flag a transient visual state imperatively, then clear it" pattern in the codebase. For MOTION-01 the natural adaptation is declarative instead of imperative (React re-render, not direct DOM manipulation): compute `isNovo` once per card from a `useRef`-held `Set`/`Map` of tickers already rendered in this list (per CONTEXT.md "Claude's Discretion"), and apply the animation only on the render where `isNovo` is true — since `key={t}` keeps the DOM node stable across price-only re-renders, the animation (triggered by class/style presence, not by remount) naturally won't replay on every re-render once the ticker is marked "seen" in the ref.

**No direct analog for the ref-based "seen set" itself** — no existing `useRef(new Set(...))`/`useRef(new Map(...))` pattern was found elsewhere in `web/src/App.jsx`. This is genuinely new territory; implement per CONTEXT.md's discretion note, not by force-fitting an existing hook.

---

### MOTION-02 — Value pulse on order confirmation (`web/src/App.jsx`, `BuyModal`/`SellModal` + `confirmBuy`/`confirmSell`)

**Analog 1 — the exact value node to pulse (buy side):** `web/src/App.jsx:7515-7518`
```javascript
<div style={{ display: "flex", justifyContent: "space-between", marginTop: "16px", padding: "12px 13px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "9px", fontFamily: MONO }}>
  <span style={{ color: T.textMuted, fontSize: "13px" }}>Custo estimado</span>
  <span style={{ fontWeight: 700, fontSize: "15px" }}>{money(cost)}</span>
</div>
```
The `<span>{money(cost)}</span>` is the "valor exibido" CONTEXT.md refers to for MOTION-02. `SellModal` (`web/src/App.jsx:7539+`) mirrors this with its own total/valor block — same treatment applies there.

**Analog 2 — existing transient/pulsing keyframe syntax to mirror (shape, not duration/semantics):** `web/src/App.jsx:7137`
```javascript
<style>{`@keyframes sweepspin{to{transform:rotate(360deg)}}@keyframes sweeppulse{0%,100%{opacity:1}50%{opacity:0.45}}`}</style>
```
`sweeppulse` is `infinite` (loading state, not a one-shot confirmation pulse) — do not copy the `infinite` semantics, only the terse inline-`<style>` `@keyframes` syntax as one option. Given `GlobalStyle()` is the established home for `.b3`-scoped keyframes (see MOTION-01 above), prefer adding the new one-shot pulse keyframe (e.g. `b3pulse{ 0%{transform:scale(1)} 50%{transform:scale(1.08)} 100%{transform:scale(1)} }`, non-`infinite`) to `GlobalStyle()` instead of a component-local `<style>` tag, for consistency with where MOTION-01's keyframe lands.

**Analog 3 — order confirm handlers, where to key the "just confirmed, not yet closed" transient state:** `web/src/App.jsx:8222-8250` (`confirmBuy`) and `8165-8184` (`confirmSell`)
```javascript
confirmBuy: async () => {
  const bm = buyModal; if (!bm) return;
  try {
    const s = await store.buy(bm.t, bm.qty, bm.meta || undefined); // FASE 2 (2.4): setup de entrada
    setData(s); setBuyModal(null);
    track("trade_simulated", { side: "buy", ticker: bm.t, instrument: "equity", pendente: !!s.pendente }); // qa/47 (Fase 2)
    if (s.pendente) {
      flash(cp.toastOrdemPendente(bm.qty, bm.t));
    } else {
      flash(cp.toastCompra(bm.qty, bm.t)); // FASE 8B (B1): voz do modo
      setStopAlvoFor(bm.t);
      A.runStopAlvoFor(bm.t);
    }
  }
  catch (e) {
    try { setData(await store.getState()); } catch { /* refresh best-effort */ }
    flash("Compra: " + (e.message || e));
  }
},
```
Key structural facts the planner needs: (1) the motor call (`store.buy`/`store.sell`) already fully resolves success/rejection before any UI feedback runs — the guardrail from CLAUDE.md ("tudo-ou-nada… não há preenchimento parcial") is already enforced upstream, so the pulse only needs to trigger in the success branch (`!s.pendente` / no `catch`), never in `catch` (rejected) — exactly as CONTEXT.md specifies. (2) `setBuyModal(null)` currently closes the modal in the SAME tick the success path runs — since MOTION-02 wants the pulse to play ON the modal's value BEFORE the modal disappears, the modal close needs a short delay (~120ms, matching the pulse duration) instead of being synchronous with `store.buy`'s resolution, OR the pulse needs to be replayed on the value as displayed in the toast/next screen. This sequencing decision is for PLAN.md, not this file — flagging it because the current handler shape (`setData(s); setBuyModal(null);` back-to-back, synchronous) is the literal obstacle a naive implementation will hit.

**Error path — confirmed no-pulse case, same file:** the `catch` blocks at `8244-8249` (buy) and `8176-8183` (sell) are the existing "rejected order" paths — no visual success signal is emitted there today (only `flash("Compra: " + …)`/`flash("Venda: " + …)`), which already matches CONTEXT.md's requirement that rejected orders never pulse. No new branching needed to satisfy this — just don't add the pulse trigger to these branches.

---

### ILUS-01 — Flat Boris illustration component

**Analog for visual vocabulary (color/geometry to reuse verbatim):** `LogoMark`, `web/src/App.jsx:201-231`
```javascript
function LogoMark({ size = 32, radius }) {
  const r = radius != null ? radius : Math.round(size * 0.26);
  const rx = (r / size) * 64;
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" aria-hidden role="img" style={{ display: "block", flex: "none" }}>
      <rect x="0" y="0" width="64" height="64" rx={rx} fill="#161927" />
      {/* tufos de orelha */}
      <path d="M14 16 L22 27 L10 27 Z" fill="#2a3a6b" />
      <path d="M50 16 L42 27 L54 27 Z" fill="#2a3a6b" />
      {/* rosto */}
      <circle cx="32" cy="34" r="26" fill="#2a3a6b" />
      {/* óculos redondos */}
      <circle cx="22" cy="32" r="10" fill="none" stroke={BRAND.amber} strokeWidth="3.2" />
      <circle cx="42" cy="32" r="10" fill="none" stroke={BRAND.amber} strokeWidth="3.2" />
      <path d="M30 32 Q32 29 34 32" fill="none" stroke={BRAND.amber} strokeWidth="3.2" />
      <circle cx="22" cy="32" r="4" fill="#eef1f8" />
      <circle cx="42" cy="32" r="4" fill="#eef1f8" />
      {/* bico */}
      <path d="M32 42 L27.5 49 L36.5 49 Z" fill={BRAND.amber} />
      {/* selo "+" */}
      <circle cx="51" cy="50" r="10" fill="#161927" />
      <circle cx="51" cy="50" r="9" fill={BRAND.amber} />
      <path d="M51 45.5V54.5M46.5 50H55.5" stroke="#161927" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}
```
Exact hex/token vocabulary to reuse: body/face/ear-tufts `#2a3a6b` (fixed brand navy, never the mode accent), glasses/beak/seal `BRAND.amber` (`#f2a93b`, `web/src/App.jsx:41`), eye-white `#eef1f8`, background/seal-ring `#161927`. The "nunca recolorir os óculos fora do âmbar da marca" comment (line 202-206) is a locked brand rule ILUS-01 must also honor.

**File-placement analog — where new SVG components live, and the constraint that decides it:**
- `LogoMark` lives inline in `App.jsx` (no separate file) because it's small/static and consumed only from within `App.jsx`.
- `Boris` (the PNG-based mascot) lives in its own file, `web/src/pet/Boris.jsx`, and is imported BY `App.jsx` (`web/src/App.jsx:18`) and by `BorisIntro.jsx` (`web/src/pet/BorisIntro.jsx:27`, `import Boris from "./Boris.jsx"`).
- **Constraint that resolves the "Claude's Discretion" placement question:** `BorisIntro.jsx`'s own header comment (`web/src/pet/BorisIntro.jsx:23-25`) states explicitly why it can't import from `App.jsx`: *"importar T/card de App.jsx criaria import circular (App.jsx importa este arquivo)"* — confirmed by `web/src/App.jsx:18-21` importing `Boris`, `BorisChat`, `BorisIntro` all from `./pet/*.jsx`. Any new illustration component that `BorisIntro.jsx` needs to import directly must therefore live in `web/src/pet/` (a new file, e.g. `web/src/pet/BorisFlat.jsx`), NOT as a function added to `App.jsx` — importing an `App.jsx` export into `BorisIntro.jsx` would recreate the exact circular-import problem this codebase has already worked around once.
- Because the new component can't import `App.jsx`'s `BRAND` constant either (same circular-import reason), it must hardcode the brand hex values directly, exactly as `BorisIntro.jsx` already does for its own theme tokens (`web/src/pet/BorisIntro.jsx:29-32`, rebuilding `T` from CSS `var(--x)` strings instead of importing `T` from `App.jsx`). Concretely: hardcode `"#f2a93b"` (amber) and `"#2a3a6b"` (navy) as literals in the new SVG, mirroring `LogoMark`'s own literals for everything except the one BRAND lookup.

**Integration point — the swap itself:** `web/src/pet/BorisIntro.jsx:42`
```javascript
<Boris size={110} />
```
becomes a call to the new component (same call-site shape: a sized presentational element inside the existing centered flex column at lines 41-49). Import line 27 (`import Boris from "./Boris.jsx"`) is replaced/supplemented with an import of the new file.

---

## Shared Patterns

### `.b3`-scoped keyframes live in `GlobalStyle()`, not per-component `<style>` tags
**Source:** `web/src/App.jsx:313-388` (`GlobalStyle()`)
**Apply to:** both MOTION-01's card-entry keyframe and MOTION-02's pulse keyframe — add both to the existing keyframes block (lines 359-364), following the `b3<name>` naming convention, so both automatically fall under the single `prefers-reduced-motion` rule at line 384 without any new `@media` block.

### Reduced-motion gate — reuse, never re-litigate
**Source:** `web/src/App.jsx:384-385`
**Apply to:** MOTION-01 and MOTION-02 both — any `animation`/`transition` property on an element inside `.b3` is already covered. Do not add a second `@media (prefers-reduced-motion: reduce)` block and do not extend the JS-level `REDUCE_MOTION` constant (`web/src/App.jsx:1443`) to these two motions.

### Transient one-shot visual state = class/flag set, then cleared after a fixed duration
**Source:** `web/src/App.jsx:7762-7765` (`b3-mode-switch`, imperative DOM version) and `web/src/pet/Boris.jsx:181` (`emote()`, React-class-toggle version: `el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); …setTimeout(()=>el.classList.remove(cls),dur)`)
**Apply to:** MOTION-02's pulse trigger (flag "just confirmed" for ~120ms, matching the animation duration, before allowing the modal-close/success-state transition to proceed) and, if the planner chooses a class-toggle implementation over a pure-CSS-on-mount approach, MOTION-01's card entry as well.

### Brand-locked color vocabulary — hardcode hex when the constant isn't importable, never introduce a new hex outside `BRAND`/`PALETTE`
**Source:** `web/src/App.jsx:40-44` (`BRAND`), `LogoMark` (lines 201-231)
**Apply to:** ILUS-01 — glasses/beak/seal always `#f2a93b` (or `BRAND.amber` if the new file can import it; it cannot, per the circular-import analysis above, so hardcode the literal), body/face always `#2a3a6b`, independent of theme/mode.

## No Analog Found

| File/Concern | Role | Data Flow | Reason |
|---|---|---|---|
| "Seen tickers this session" ref (MOTION-01 novelty detection) | state/utility | event-driven | No existing `useRef(new Set(...))`/`useRef(new Map(...))` pattern in `web/src/App.jsx` to copy structure from — this is genuinely new; CONTEXT.md leaves the exact mechanism to Claude's discretion. |
| Automated test for MOTION-01/MOTION-02 (CSS animation presence/reduced-motion behavior) | test | n/a | No existing `web/tests/*.mjs` guardian tests CSS keyframe/animation properties or `prefers-reduced-motion` behavior (all existing tests are static-source-regex guardians, e.g. `web/tests/test_boris_intro.mjs`, or functional/data-flow tests) — expect this phase's verification to rely on `20-HUMAN-UAT.md` (per CONTEXT.md) rather than a new automated guardian, same tooling limitation already documented there (no CDP `Emulation.setEmulatedMedia`). |

**Test-file analog that DOES exist and will need updating:** `web/tests/test_boris_intro.mjs` (113 lines) is a static-source guardian that regex-asserts `App.jsx importa BorisIntro de ./pet/BorisIntro.jsx` and `BorisIntro.jsx importa Boris (mesmo componente animado da F1)` — i.e. it literally asserts `import Boris from ["']\.\/Boris\.jsx["'];` against `BorisIntro.jsx`'s source. ILUS-01 changing that import line WILL break this guardian; the planner must update the regex/assertion in the same PLAN.md step that swaps the import, per this repo's "guardiões de teste não se apagam" rule (update with a note, don't delete).

## Metadata

**Analog search scope:** `web/src/App.jsx` (single-file React app, ~9000+ lines), `web/src/pet/*.jsx`, `web/tests/test_boris_intro.mjs`
**Files scanned:** `web/src/App.jsx`, `web/src/pet/Boris.jsx`, `web/src/pet/BorisIntro.jsx`, `web/tests/test_boris_intro.mjs`, `web/tests/` directory listing
**Pattern extraction date:** 2026-09-06
