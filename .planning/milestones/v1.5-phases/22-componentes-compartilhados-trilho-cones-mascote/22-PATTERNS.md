# Phase 22: Componentes compartilhados (trilho, ícones, mascote) - Pattern Map

**Mapped:** 2026-09-05
**Files analyzed:** 1 (`web/src/App.jsx`, all changes are edits, no new files)
**Analogs found:** 5 / 5 (single-file phase — every "analog" is another region of the same file, already the canonical source per `22-CONTEXT.md`/`22-UI-SPEC.md`)

All line numbers below were re-verified by direct `grep`/`Read` against
`web/src/App.jsx` on 2026-09-05 (post Phase 20/21, matching `22-UI-SPEC.md`'s
own verification date) — no drift found. Re-verify again immediately before
editing, per this repo's own recurring-line-drift note in `21-UI-SPEC.md`.

This phase touches exactly one file (`web/src/App.jsx`, 9138 lines) and adds
zero new files/components at the module level (small in-file helpers only,
per `22-CONTEXT.md`'s Claude's Discretion). The generic "role/data-flow"
classification below is compressed to a single row set — the real structure
of this map is **per change-site (SYS-01 / SYS-02 / SYS-03), each pointing to
its own in-file analog.**

## File Classification

| Change site | Role | Data Flow | Closest Analog (same file) | Match Quality |
|---|---|---|---|---|
| 3 non-compliant trilhos (`3792`, `4001`+`4170`(CandidatoOpcao), `4133`) | component (horizontal scroll container) | request-response (render from already-fetched state) | HERO-CARROSSEL container+item, `App.jsx:1949`/`1951` | exact (same mechanism family, snap-only subset) |
| 9 live emoji→SVG sites (`2155`,`2156`,`3461`,`3703`,`3705`,`4535`,`5620`,`6757`,`6926`) + 2 `<option>` deletions (`5356`,`5357`) | component (inline icon glyph) | transform (glyph → SVG or plain text) | `NavIcon`, `App.jsx:898-912` | exact for the 8 stroke-icons; `tierOf`, `App.jsx:963-969`, is the analog for the one filled-circle icon (`6926`) |
| `PetFab` shadow (`App.jsx:2748-2755`) | component (fixed-position button, decorative shadow) | transform (hardcoded rgba → theme token) | `PALETTE.dark.scrim`/`PALETTE.light.scrim`, `App.jsx:80`/`106`, + `T` resolution mechanism `App.jsx:111-113` | exact (same token-pair convention, different key) |

---

## Pattern Assignments

### SYS-01 — Universal `scrollSnapType`, peek-width only on HERO-CARROSSEL

**Analog:** HERO-CARROSSEL, `App.jsx:1946-1967` (home setups carousel — already compliant, the reference pattern named in `22-CONTEXT.md`).

**Reference container (already correct — do not touch, copy the snap mechanism from here):**
```jsx
// App.jsx:1949
<div style={{ display: "flex", gap: "12px", overflowX: "auto", scrollSnapType: "x mandatory", margin: "0 -18px", padding: "2px 18px 6px", WebkitOverflowScrolling: "touch" }}>
```

**Reference item (already correct — this is the "84% peek" that must NOT be copied to the other 3 sites, per `22-UI-SPEC.md` Decision 1):**
```jsx
// App.jsx:1951
<button key={r.ticker} onClick={() => A.go("mercado")} style={{ ...card, scrollSnapAlign: "center", flex: "0 0 84%", maxWidth: "330px", borderLeft: `3px solid ${T.accent}`, padding: "15px 16px", textAlign: "left", cursor: "pointer" }}>
```

**Shared helper to introduce** (name is implementer's discretion per `22-CONTEXT.md`; shape approved in `22-UI-SPEC.md`):
```js
// Place near other small style helpers (e.g. alongside `card`, wherever that constant is defined).
const carouselTrackStyle = (extra) => ({
  display: "flex",
  overflowX: "auto",
  scrollSnapType: "x proximity",
  WebkitOverflowScrolling: "touch",
  ...extra,
});
const carouselItemStyle = (align = "start") => ({ scrollSnapAlign: align });
```
Note: HERO-CARROSSEL itself keeps `scrollSnapType:"x mandatory"` + `scrollSnapAlign:"center"` (it is the single-focus sub-variant, explicitly excluded from the universal-`proximity` rule — see `22-UI-SPEC.md` Decision 1, item 3). Whether to also route HERO-CARROSSEL's own style through the helper (passing `"x mandatory"`/`"center"` as override) or leave it untouched is a planner call; the UI-SPEC says "unchanged," so leaving the literal inline style at `1949`/`1951` as-is is the safer reading.

**Site 1 — `TECH_MODELS` filter rail (Watchlist), container only, item is inline in the same `.map()`:**
```jsx
// BEFORE — App.jsx:3792-3798
<div style={{ display: "flex", gap: "8px", overflowX: "auto", WebkitOverflowScrolling: "touch", paddingBottom: "2px" }}>
  {TECH_MODELS.map(([id, label, sub]) => (
    <button key={id} onClick={() => setAnalysisModel(id)} style={{ minWidth: "118px", minHeight: "48px", padding: "8px 10px", borderRadius: "12px", border: `1px solid ${analysisModel === id ? T.accent : T.borderSubtle}`, background: analysisModel === id ? T.accentTint : T.bgBase, color: analysisModel === id ? T.accent : T.textSecondary, textAlign: "left", fontWeight: 800 }}>
      <span style={{ display: "block", fontSize: "12px" }}>{label}</span>
      <span style={{ display: "block", fontSize: "10px", color: T.textFaint, fontWeight: 600, marginTop: "2px" }}>{sub}</span>
    </button>
  ))}
</div>

// AFTER (shape) — add scrollSnapType to container, scrollSnapAlign to the item's style object
<div style={carouselTrackStyle({ gap: "8px", paddingBottom: "2px" })}>
  {TECH_MODELS.map(([id, label, sub]) => (
    <button key={id} onClick={() => setAnalysisModel(id)} style={{ ...carouselItemStyle("start"), minWidth: "118px", minHeight: "48px", padding: "8px 10px", borderRadius: "12px", border: `1px solid ${analysisModel === id ? T.accent : T.borderSubtle}`, background: analysisModel === id ? T.accentTint : T.bgBase, color: analysisModel === id ? T.accent : T.textSecondary, textAlign: "left", fontWeight: 800 }}>
      ...
```
No `minWidth`/`flex` change — width stays `118px` per Decision 1 (chip rail must stay scannable, not one-at-a-time).

**Site 2 — `OportunidadesOpcoes` strip (Posições), item inline in same `.map()`:**
```jsx
// BEFORE — App.jsx:4001, item at 4011-4017
<div style={{ display: "flex", gap: "10px", overflowX: "auto", WebkitOverflowScrolling: "touch", scrollbarWidth: "none", paddingBottom: "2px" }}>
  {itens.map((p) => {
    ...
    return (
      <button
        key={p.t}
        type="button"
        aria-label={p.t + " — " + cp.tiraOpcoesVerDetalhe}
        onClick={() => onAbrir(p.t)}
        style={{ flex: "0 0 auto", minWidth: "210px", minHeight: "44px", textAlign: "left", padding: "11px 12px", borderRadius: "11px", background: T.bgCard, border: `1px solid ${T.borderFaint}`, cursor: "pointer" }}
      >
```
Add `scrollSnapType:"x proximity"` to the container style and `scrollSnapAlign:"start"` into the button's style object; no width/flex change (already narrower than viewport, per `22-UI-SPEC.md`'s "peek already present by construction" analysis). Per the "minor cleanup" note in `22-UI-SPEC.md`, this site's `scrollbarWidth:"none"` may optionally be removed for scrollbar-treatment consistency with the other 3 trilhos — low priority, skip if risky.

**Site 3 — `PropostaDaPosicao` N-candidate row: container is inline, but the ITEM lives in a separate component (`CandidatoOpcao`), not the same `.map()` block:**
```jsx
// Container — App.jsx:4133
<div style={{ marginTop: "11px", display: "flex", gap: "10px", overflowX: "auto", WebkitOverflowScrolling: "touch", scrollbarWidth: "none", paddingBottom: "2px" }}>
  {candidatos.map((c) => (
    <CandidatoOpcao key={c.tipo + "-" + (c.contractSymbol || "collar")} p={c} r={r} cp={cp} operador={operador} busy={busy} onAceitar={aceitarCandidato} />
  ))}
</div>

// Item style is INSIDE the CandidatoOpcao component definition — App.jsx:4156-4170
function CandidatoOpcao({ p, r, cp, operador, busy, onAceitar }) {
  ...
  return (
    <div style={{ flex: "0 0 auto", minWidth: "210px", minHeight: "44px", padding: "11px 12px", borderRadius: "11px", background: T.bgCard, border: `1px solid ${T.borderFaint}` }}>
```
**Important for the planner:** the `scrollSnapAlign:"start"` for this site must be added inside `CandidatoOpcao`'s own returned `<div>` style at line 4170, NOT at the `.map()` call site (4134) — the item markup is not inline here, unlike sites 1 and 2. Same optional `scrollbarWidth:"none"` cleanup note applies to the container at 4133.

**Verification (from `22-UI-SPEC.md`, copy verbatim into the plan):**
- `grep -n "scrollSnapType" web/src/App.jsx` → 4 matches after (was 1).
- `grep -n "flex: \"0 0 84%\"" web/src/App.jsx` → still exactly 1 match (HERO-CARROSSEL only). More than 1 means the peek-width mistake was made.

---

### SYS-02 — Emoji → SVG (NavIcon contract), and two deletions

**Analog:** `NavIcon`, `App.jsx:898-912` (full component, already read in full — nothing else to fetch from it):
```jsx
function NavIcon({ id, active }) {
  const c = active ? T.accent : T.textMuted;
  const p = { fill: "none", stroke: c, strokeWidth: 1.9, strokeLinecap: "round", strokeLinejoin: "round" };
  const paths = {
    evolucao: <><polyline points="3 17 9 11 13 15 21 7" {...p} /><polyline points="16 7 21 7 21 12" {...p} /></>,
    mercado: <><line x1="6" y1="20" x2="6" y2="13" {...p} /><line x1="12" y1="20" x2="12" y2="5" {...p} /><line x1="18" y1="20" x2="18" y2="10" {...p} /></>,
    radar: <><circle cx="12" cy="12" r="8.5" {...p} /><circle cx="12" cy="12" r="4.2" {...p} /><line x1="12" y1="12" x2="18" y2="6" {...p} /><circle cx="12" cy="12" r="1.2" fill={c} stroke="none" /></>,
    carteira: <><rect x="3" y="6" width="18" height="13" rx="2.5" {...p} /><path d="M3 9h13a2 2 0 0 1 2 2v0" {...p} /><circle cx="17" cy="13" r="1.3" fill={c} stroke="none" /></>,
    opcoes: <><path d="M4 17c4-9 12-9 16 0" {...p} /><path d="M6 12h12" {...p} /><circle cx="8" cy="12" r="1.3" fill={c} stroke="none" /><circle cx="16" cy="12" r="1.3" fill={c} stroke="none" /></>,
    perfil: <><circle cx="12" cy="8.5" r="3.4" {...p} /><path d="M5.5 19a6.5 6.5 0 0 1 13 0" {...p} /></>,
    agente: <><rect x="5" y="7" width="14" height="11" rx="2.5" {...p} /><line x1="12" y1="4" x2="12" y2="7" {...p} /><circle cx="12" cy="3.4" r="1" fill={c} stroke="none" /><circle cx="9.2" cy="11.5" r="1.1" fill={c} stroke="none" /><circle cx="14.8" cy="11.5" r="1.1" fill={c} stroke="none" /><path d="M9.5 15h5" {...p} /></>,
  };
  return <svg width="23" height="23" viewBox="0 0 24 24" aria-hidden>{paths[id]}</svg>;
}
```
**Pattern to copy:** `viewBox="0 0 24 24"`, shared stroke-props object `p` (`fill:"none", stroke:c, strokeWidth:1.9, strokeLinecap:"round", strokeLinejoin:"round"`), a lookup object keyed by icon id, `aria-hidden` on the outer `<svg>`, occasional `fill={c} stroke="none"` on small `<circle>` accent dots within an otherwise-stroked icon (see `radar`/`carteira`/`opcoes`/`agente` for that mixed idiom — useful precedent for the new "sparkle"/"checkmark"/"broadcast" icons in this phase, all of which mix a stroke shape with small solid accent dots per `22-UI-SPEC.md`'s icon descriptions).

New icon component/registry should follow the same shape — either extend `NavIcon`'s own `paths` map with new ids (if reused inside `BottomNav`-adjacent contexts) or, more likely given these are one-off inline icons scattered across unrelated components, a small sibling function (name at Claude's Discretion, e.g. `Glyph({ id })` or per-icon components `IconGraduationCap`/`IconChart`/`IconSparkle`/`IconCheck`/`IconBroadcast`) using the identical `p` stroke-props convention. **Recommendation: reuse `NavIcon`'s existing `radar` path (`App.jsx:904`) for the `6757` broadcast/scan icon** instead of drawing a new one — `22-UI-SPEC.md` flags this explicitly ("already solves this exact radar/scan concept").

**Second analog — filled-dot pattern (for the ONE non-stroke icon, `6926` tier dot):** `tierOf`, `App.jsx:963-969`:
```jsx
function tierOf(conf) {
  const c = Number(conf) || 0;
  if (c >= 75) return ["🟢", "Forte"];
  if (c >= 50) return ["🟡", "Moderada"];
  if (c > 0) return ["⚪", "Neutra"];
  return ["🔴", "Fraca"];
}
```
Consumed at:
```jsx
// App.jsx:6926 (only live render site)
<div style={{ fontSize: "12px", color: T.textMuted, marginTop: "3px", lineHeight: 1.4 }}>{tierOf(r.confluencia)[0]} {tierOf(r.confluencia)[1]} · aderência ao padrão de estudo</div>
```
```jsx
// App.jsx:3818 — DEAD destructure, tierDot never rendered (grep "tierDot" hits only this line)
const [tierDot, tierLabel] = tierOf(sc && sc.confluencia);
```
**Pattern to copy for the new dot:** keep `tierOf`'s 4-branch threshold logic (`>=75`/`>=50`/`>0`/else) unchanged, but change its first tuple element from an emoji string to either (a) a small id string consumed by a new `<TierDot id=.../>` component rendering `<circle>` with `fill` from the 4-value literal-hex table (`#22c55e`/`#f59e0b`/`#9ca3af`/`#ef4444`, approved in `22-UI-SPEC.md` Decision 2 — NOT `T.positive`/`T.negative`/`T.warn`, deliberately, per `tierOf`'s own existing comment on reserving green/red for market signal), or (b) return the SVG element directly from `tierOf`. Either way, `aria-hidden` on the `<svg>`/`<circle>` — the adjacent text label (`"Forte"` etc.) already carries the accessible meaning. While touching this function, resolve the dead `tierDot` destructure at `3818` (wire it in or delete the unused variable — hygiene item, not a design requirement).

**Live stroke-icon replacement sites (8, all follow the same "before" idiom — emoji inline string next to visible text, all `aria-hidden` on the new SVG):**

```jsx
// 2155-2156 — Perfil, Modo seletor (two glyphs, one line each)
<button onClick={() => escolher("estudo")} style={segBtn(mode === "estudo")}>🎓 Estudo</button>
<button onClick={() => escolher("operador")} style={segBtn(mode === "operador")}>📈 Operador</button>
// AFTER shape: <button ...>{<IconGraduationCap aria-hidden />} Estudo</button>  (svg + space + existing text)
```
```jsx
// 3461 — Watchlist sparkline fallback (already aria-hidden today, carry forward)
{sc && Array.isArray(sc.spark) && sc.spark.length > 1 ? <Sparkline data={sc.spark} width={44} height={18} /> : <span aria-hidden style={{ fontSize: "14px" }}>📈</span>}
// Parent button already has aria-label="Abrir gráfico de velas" — no a11y change needed.
```
```jsx
// 3703/3705 — Watchlist action row (✨ appears twice on 3703's ternary, 📈 once on 3705)
{an.loading ? <><Spinner size={11} color={T.accent} /> analisando…</> : (hasAnalysis(an) ? "✨ Reanalisar" : "✨ " + cp.btnAnalise)}
</button>
<button onClick={() => A.openTech(t)} disabled={q.error} style={{ background: "transparent", border: "none", padding: "6px 0", color: T.textMuted, fontSize: "11.5px", fontWeight: 700 }}>📈 Indicadores</button>
// Note: string-concatenation idiom ("✨ " + cp.btnAnalise / "✨ Reanalisar") means the icon
// must move OUT of the string into JSX — button content becomes {<IconSparkle aria-hidden />}{hasAnalysis(an) ? " Reanalisar" : " " + cp.btnAnalise} (mind the leading-space adjustment once the emoji-plus-space literal is split into icon+text).
```
```jsx
// 4535 — Posições, Stop/alvo (IA) button (aria-label already exists on the button, no a11y change)
<button onClick={() => ctx.openStopAlvo(p.t)} aria-label={"Sugerir stop e alvo de " + p.t + " com IA"} style={{ ... }}>
  📈 Stop/alvo (IA)
</button>
```
```jsx
// 5620 — Perfil/config, plain-text checkmark inline in a <span>
<span style={{ fontSize: "11px", color: T.positive, fontWeight: 700 }}>chave configurada ✅ <span style={{ color: T.textFaint, fontWeight: 500 }}>{isNative ? "(neste aparelho)" : "(no servidor)"}</span></span>
```
```jsx
// 6757 — Radar, ternary embedded in template text (broadcast icon)
{res.scanOrigem === "revalidação"
  ? "↻ Releitura após o fechamento"
  : res.scanAuto ? "📡 Varredura automática de hoje" : "↻ Última varredura (manual)"} · {res.scanAtLabel}
// Note: the "↻" alternatives in the SAME ternary are OUT OF SCOPE (existing typographic
// glyph per Out-of-Scope Symbols in 22-UI-SPEC.md) — only the 📡 branch gets an SVG swap;
// the string-literal ternary must be restructured to JSX to mix icon+text conditionally.
```

**`<option>` deletion sites (no SVG possible — `<option>` is text-only):**
```jsx
// BEFORE — App.jsx:5356-5357
<option value="estudo">{(data.skill && data.skill.name) || "Mesa B3 - Educacional v1"} · 🎓 Estudo</option>
<option value="operador">{(data.skillOperador && data.skillOperador.name) || "Mesa B3 - Operador v1"} · 📈 Operador</option>

// AFTER — delete emoji + trailing space, keep everything else verbatim
<option value="estudo">{(data.skill && data.skill.name) || "Mesa B3 - Educacional v1"} · Estudo</option>
<option value="operador">{(data.skillOperador && data.skillOperador.name) || "Mesa B3 - Operador v1"} · Operador</option>
```

**Confirmed NOT present:** `🚀` does not exist anywhere in `web/src/*` (grep-confirmed) — do not search for it during execution.

---

### SYS-03 — PetFab shadow becomes theme-aware

**Analog:** `PALETTE.dark.scrim` / `PALETTE.light.scrim` (`App.jsx:80` / `106`) — the exact literal-rgba, per-theme token-pair convention to replicate for the new `shadowFab` key, plus the `T` resolution mechanism that makes any new `PALETTE.*` key automatically available as `T.*` with zero extra plumbing:

```js
// App.jsx:80 (PALETTE.dark)
scrim: "rgba(5,6,10,0.68)",
// App.jsx:106 (PALETTE.light)
scrim: "rgba(15,20,28,0.45)",
// App.jsx:111-113 — mechanism: every PALETTE.dark key becomes a T.<key> CSS-var reference automatically
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const T = Object.fromEntries(Object.keys(PALETTE.dark).map((k) => [k, `var(${VARKEY(k)})`]));
```
**Pattern to copy:** add a `shadowFab` key to both `PALETTE.dark` (alongside the existing `scrim` line, `~80`) and `PALETTE.light` (alongside `~106`) — no other change needed to the `T`/`VARKEY`/`themeVarBlock` machinery, it picks up any new `PALETTE.dark` key automatically. Approved starting values (`22-UI-SPEC.md` Decision 3):
```js
// PALETTE.dark: shadowFab: "rgba(0,0,0,0.45)",       // matches current hardcoded value — dark unchanged
// PALETTE.light: shadowFab: "rgba(15,20,28,0.22)",   // lighter than scrim's 0.45 — small drop-shadow, not full-screen overlay
```

**Current call site (before), `App.jsx:2746-2758` (`PetFab`, full component read in one pass):**
```jsx
function PetFab({ onOpen }) {
  return (
    <button onClick={onOpen} aria-label="Abrir o assistente Boris+"
      style={{ position: "fixed", right: "14px", bottom: "92px", zIndex: 60, width: "54px", height: "54px", borderRadius: 0, border: "none", background: "transparent", padding: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div aria-hidden style={{ lineHeight: 0, filter: "drop-shadow(0 3px 6px rgba(0,0,0,0.45))" }}>
        <Boris size={40} />
      </div>
    </button>
  );
}
```
**After (only the `filter` value changes):**
```jsx
<div aria-hidden style={{ lineHeight: 0, filter: `drop-shadow(0 3px 6px ${T.shadowFab})` }}>
```
No other line in `PetFab` changes — `position:"fixed", right:"14px", bottom:"92px"` stays as-is (SYS-03 is shadow-only, per `22-CONTEXT.md`).

**Verification:** human visual check in both dark and light theme, on any screen where a card sits directly behind the FAB's fixed position — halo must separate the owl silhouette from the card without producing a visible disc/badge shape. Flag as a human-check step in the plan (same category as Phase 20/21 visual-calibration steps) — not unit-testable.

---

## Shared Patterns

### Theme tokens (`T.*` / `PALETTE`)
**Source:** `App.jsx:61-172` (`PALETTE`), `App.jsx:111-113` (`T`/`VARKEY` mechanism)
**Apply to:** SYS-03 (new `shadowFab` key). SYS-02's tier-dot fill is the one approved exception that does NOT go through `T.*` (literal hex, see rationale above) — do not "fix" that by routing it through a token; that would reintroduce the collision `tierOf`'s own comment warns against.

### Inline-SVG icon contract (`NavIcon`)
**Source:** `App.jsx:898-912`
**Apply to:** all SYS-02 stroke-icon sites (8 of the 9 live sites; the 9th, tier-dot, is a filled `<circle>` variant of the same file's `tierOf`, not `NavIcon` itself).

### No external icon/UI dependency
**Source:** confirmed absent from `package.json` (per `22-UI-SPEC.md`'s Design System table — no shadcn, no Tailwind, no icon lib).
**Apply to:** SYS-02 — every new icon must be hand-written inline SVG, never `lucide-react`/`react-icons`/etc.

---

## No Analog Found

None — every change site in this phase has a same-file analog already identified above (this is an intra-file unification phase, not new-pattern introduction).

## Metadata

**Analog search scope:** `web/src/App.jsx` only (single-file phase; confirmed by `22-CONTEXT.md`'s Established Patterns: "100% inline style, sem CSS Modules/Tailwind" and zero new files named in `22-UI-SPEC.md`'s Design System table).
**Files scanned:** 1 (`web/src/App.jsx`, 9138 lines) — read via targeted non-overlapping `Read`/`grep` ranges: lines 55-180 (PALETTE/T), 898-937 (NavIcon/BottomNav), 960-971 (tierOf), 1940-1969 (HERO-CARROSSEL), 2736-2765 (PetFab), 3780-3819 (TECH_MODELS), 3995-4019/4128-4142/4156-4186 (options trilhos + CandidatoOpcao), plus single-line `sed` excerpts for all 11 emoji call sites and `grep -n` for `scrollSnapType`/`overflowX`/emoji-Unicode-range/`tierDot`/`scrim`/`NavIcon`/`PetFab`/`CandidatoOpcao`.
**Pattern extraction date:** 2026-09-05
