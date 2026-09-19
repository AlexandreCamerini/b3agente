# Stack Research

**Domain:** Reorganizing a dense, multi-job React screen (existing "Opções" tab, sub-aba "Setups") into job-separated views — no router, no state library, no UI kit, by explicit standing decision.
**Researched:** 2026-09-19
**Confidence:** HIGH — every recommendation below is sourced to a specific file:line in THIS codebase (primary source, not training data or external ecosystem survey). This is not "what React apps generally do" research; it's "what this app already does, three times over, for this exact problem."

## Recommended Stack

### Core Technologies

No new technology. The three primitives needed already exist in `web/src/App.jsx` and `web/src/opcoes/*.jsx`, each already solving one of the five jobs' UI shape. The milestone requires composition of existing patterns, not a stack decision.

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| React 18 `useState` (already in use) | 18.3.1 (existing) | Local component state for "which job/section is active" | Already the app's only state mechanism (`CLAUDE.md`: "hand-rolled state in `web/src/App.jsx`"). `OpcoesScreen.jsx:339` already holds `const [subaba, setSubaba] = useState("setups")` for the existing 2-way Setups/Operar split — extending this to N sections is the same primitive, no new concept. |
| Segmented toggle-button group (house pattern, not a library) | n/a | Switching between job-sections (the "which job am I doing" navigation) | `OpcoesScreen.jsx:762-779` is the exact, working, tested implementation: array of `{id, rotulo}` mapped to `<button aria-pressed={active}>`, reusing `T.accent`/`T.accentTint10`/`T.bgPanel`/`T.borderSubtle`/`T.textSecondary` tokens, 44px tap target, radius 11px. The code comment is explicit and load-bearing: *"mesma afordância (`aria-pressed`, sem `role=\"tab\"` — este app não usa ARIA de tab em lugar nenhum, ver BottomNav em App.jsx)"* (`OpcoesScreen.jsx:760-761`). `BottomNav` (`App.jsx:1030-1062`) is the same pattern at the top-nav level (5 items, `aria-pressed`, no `role="tablist"`). **This is a deliberate, twice-applied house convention, not an oversight to "fix" by adding ARIA tabs.** |
| `aria-expanded` accordion (house pattern, not a library) | n/a | Progressive disclosure *within* a job-section (collapsing a candidate's detail, a chain row, a group of purchases) | At least 6 independent, working instances: `App.jsx:2604`, `App.jsx:3311`, `App.jsx:3382`, `App.jsx:3754`, `App.jsx:3843`, `App.jsx:4472`, `CuradoriaEstruturas.jsx:173`. Two idioms coexist: a plain `<button aria-expanded>` toggling a boolean/index in `useState`, and a `<div role="button" tabIndex={0} onKeyDown={... Enter/Space ...} aria-expanded>` for non-button elements that need keyboard parity (`App.jsx:3311`, `:3382`) — this second idiom is the direct implementation of the "acordeão por teclado" requirement already validated in `CLAUDE.md`'s FIX-C-16 history. Use this, not the toggle-button group, for disclosure *inside* a job, never for switching *between* jobs — they are semantically different and the codebase already keeps them distinct. |
| `carouselTrackStyle`/`carouselItemStyle` scroll-snap rail (house pattern, not a library) | n/a | Side-by-side comparison of multiple items of the same kind (job 4: comparing expirations; also multi-candidate structures) | Declared once, canonically, at `App.jsx:350-364` ("Fase 22 (SYS-01): padrão ÚNICO de rolagem horizontal do app"), reused verbatim in `opcoes/OpcoesScreen.jsx:74`, `opcoes/CuradoriaEstruturas.jsx:49-53`, `opcoes/OportunidadesOpcoes.jsx:37-41`, `opcoes/CandidatoOpcao.jsx:34-35`. `scrollSnapType: "x proximity"` (or `"x mandatory"` for the hero carousel), `align: "start"` for "navigate/compare" rails vs `"center"` reserved for the one dominant-card hero carousel. This is the correct primitive for job (4) "compare option expirations for a ticker" — do not build a new comparison widget; reuse this rail. |

### Supporting Libraries

None. Zero new npm packages are justified for this milestone — see "What NOT to Use" below for the explicit reasoning per candidate that might otherwise seem tempting.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `web/tests/*.mjs` (existing, Node-run, no framework) | Guardian tests for the new job-separated structure | Follow existing naming: one file per feature/bugfix (`web/tests/test_<feature>.mjs`), not one-per-module. Precedent for testing structural/ARIA properties by reading source statically: `test_opcoes_analisar_ui.mjs`, `test_api_parity.mjs`-style source-scanning guardians already exist for this exact screen family. |
| `npx vite build` | Syntax/type-safety net after any edit to `.jsx` | Mandatory per `CLAUDE.md`: "Front editado → `npx vite build` antes de declarar ok (grep e teste estático não pegam erro de sintaxe JS)." |
| `bash scripts/executar.sh --testes` | Canonical validation (both suites: pytest + `web/tests/*.mjs`) | `scripts/test.sh` alone is explicitly documented as "meia baseline" and does not count as validation for this repo. |

## Installation

```bash
# Nothing to install. This milestone adds zero npm dependencies.
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|--------------------------|
| Hand-rolled `subaba`-style `useState` + toggle-button group | A router (React Router, wouter, tiny hash-router) for URL-addressable job sections | Never for this milestone. The app has zero router anywhere, by design (`CLAUDE.md`: "no framework router/state library — hand-rolled state"); v1.5's own decision log explicitly closed "sem migração de stack" as a locked architecture decision. A router would also conflict with the existing `tab`/`setTab` prop-drilled navigation model used for the 5 top-level screens and the `subaba` pattern used one level down — introducing URL state for a THIRD level of navigation (job-section inside sub-aba inside aba) when neither of the outer two levels use URLs would be an inconsistent, unjustified architecture fork. |
| Native `role="tab"`/`role="tablist"`/`aria-selected` ARIA authoring pattern | Toggle-button group with `aria-pressed` | Only if a future accessibility audit specifically demands full ARIA tab semantics app-wide — but the codebase has an explicit, repeated decision NOT to do this ("este app não usa ARIA de tab em lugar nenhum"), and changing it here alone would fragment the navigation semantics between this one screen and `BottomNav`/the existing Setups↔Operar toggle. Not a call to make inside a UI-reorganization milestone whose own scope explicitly excludes new functionality/behavior changes. |
| CSS-only `<details>`/`<summary>` for progressive disclosure | The house `aria-expanded` + `useState` accordion pattern | `<details>` is used exactly once in the whole `web/src/` tree, in `main.jsx:33` (the top-level error boundary fallback, a one-off diagnostic UI, not a designed component). Every product-surface accordion in the app (App.jsx, CuradoriaEstruturas.jsx) uses the controlled `useState`+`aria-expanded` idiom instead, almost certainly because `<details>` styling is harder to make consistent with the token-driven inline-style system (`T.*`) and doesn't give the keyboard-Enter/Space idiom control needed to match existing focus/animation behavior (v1.5 Fase 23 added purposeful motion gated by `prefers-reduced-motion` — `<details>`'s native open/close has no hook for that gate). Stick with the house pattern for consistency. |
| A UI component library (Radix, Headless UI, Ariakit) for tabs/accordion primitives | n/a | Never. This app has never adopted a component library anywhere (`web/`, `web-admin/` are both plain React + inline styles + CSS custom properties, confirmed by `CLAUDE.md`'s "Frameworks" section listing only `lightweight-charts` and CodeMirror as UI deps beyond React itself). Reaching for Radix/Headless-UI here to get "proper" tab/accordion semantics would (a) contradict the twice-stated "sem role=tab" convention, (b) require re-theming through the library's own styling API instead of the existing `T.*` token object, (c) add a dependency for something 6+ existing call sites already do by hand with ~15 lines of JSX each. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|--------------|
| Any router (React Router, wouter, TanStack Router, even a minimal hash-router) | Zero router exists in this app by design; adding one for this milestone only, one screen deep, when the outer two navigation levels (`tab`, `subaba`) are both plain `useState`, creates an inconsistent architecture and touches a decision (`CLAUDE.md`, v1.5 lock: "Sem migração de stack") this milestone is explicitly not authorized to reopen. | `useState` for the active job-section id, lifted to the same component level `subaba` already lives at (`OpcoesScreen.jsx:339`), following the exact pattern already there. |
| A UI/component kit (Radix, Headless UI, Ariakit, MUI, Chakra, shadcn/Tailwind) | v1.5's own architecture decision log closed this explicitly: *"Sem migração de stack: estilo inline + tokens `var(--x)`, nada de Tailwind/shadcn."* Nothing about this milestone's scope (pure reorganization, no new capability) justifies reopening a locked decision. | The house token object `T` (CSS custom properties via `VARKEY`, `OpcoesScreen.jsx:59-61`) plus inline styles, exactly as every other screen does. |
| `role="tab"` / `role="tablist"` / `aria-selected` ARIA tab pattern | Explicitly rejected in the very file being reorganized: *"este app não usa ARIA de tab em lugar nenhum"* (`OpcoesScreen.jsx:760-761`). Introducing it here — even if "more correct" per WAI-ARIA authoring practices — would fragment navigation semantics from `BottomNav` and the existing Setups/Operar toggle, both `aria-pressed` button groups. | The existing `aria-pressed` segmented toggle-button group pattern (`OpcoesScreen.jsx:762-779`). |
| A state-management library (Zustand, Jotai, Redux, Context-based store) to coordinate the newly-split job-sections | The app deliberately has none (`CLAUDE.md`: "no framework router/state library"); the existing 2-way split (`SubAbaOperar`) already proves the coordination need is fully satisfiable by lifting shared state (`ticker`, `tese`, `vencimento`, `lote`, `alvo`, `stop`, `painel`) to the parent `OpcoesScreen()` function and passing it down as props — confirmed by inspection: every `useState` call in `OpcoesScreen.jsx` (lines 333, 339, 367-372, 1416-1417) already lives above the point where the screen branches into sub-views (line 789), so no state is trapped inside something that would need to survive an unmount. | Keep lifting shared state to whichever component becomes the new coordinator (either `OpcoesScreen()` itself, or a thin wrapper if the file is split further) — same as the existing `SubAbaOperar` extraction already does. |
| `<details>`/`<summary>` for the new job-separated accordions | Used exactly once in the app, as a one-off error-boundary fallback (`main.jsx:33`), never as a designed product-surface component; doesn't hook into the `prefers-reduced-motion` gate or the `T.*` token system the way the controlled pattern does. | The controlled `useState` + `aria-expanded` (+ `onKeyDown` Enter/Space when the trigger isn't a native `<button>`) pattern already used 6+ times. |

## Stack Patterns by Variant

**If splitting the 5 jobs into distinct navigable sections (jobs 1-2-3-4-5 as peers the user switches between):**
- Use the toggle-button-group pattern (`OpcoesScreen.jsx:762-779`), extended from 2 items to N.
- Because it's the exact primitive already proven for this screen's own Setups/Operar split, uses only existing tokens, and preserves the app's "no ARIA tab" convention.
- Watch the 44px-tap-target / label-width math on a 375px viewport with 5 labels instead of 2 — if labels don't fit one row, reuse the `carouselTrackStyle` horizontal-rail pattern (`App.jsx:350-364`) to make the toggle row itself horizontally scrollable, rather than wrapping to two rows or shrinking below the tap-target floor. This is a layout decision for the UI-spec step, not a new dependency.

**If a job is naturally a "manage a list of items, expand one for detail" shape (e.g., watchers/"vigias" management, saved-setups management):**
- Use the `aria-expanded` accordion pattern per list item, not a second-level toggle-button group.
- Because switching sections is a different interaction than expanding an item's detail, and the codebase already keeps these visually and semantically distinct (buttons with `aria-pressed` for navigation vs. `aria-expanded` rows for disclosure).

**If a job requires comparing multiple same-shaped items side by side (comparing expirations, comparing multi-candidate structures):**
- Use `carouselTrackStyle`/`carouselItemStyle` (`App.jsx:350-364`).
- Because it's the app's one canonical horizontal-comparison primitive (v1.5 Fase 22 deliberately unified 4 prior ad hoc implementations into this one), already used for the closely related "multi-candidato" comparison in this same `opcoes/` directory.

**If extracting each job's markup into its own file (recommended, mirrors existing precedent):**
- Follow the `SubAbaOperar` extraction precedent already in `OpcoesScreen.jsx` — job-specific JSX lives in its own component under `web/src/opcoes/`, receives shared state (ticker, selections, callbacks) as props from the coordinating screen, and must NOT import `App.jsx` (the isolation rule stated repeatedly in the file's comments, e.g. "Fase 27 (27-02): `finance.js` é módulo PURO — zero import de `App.jsx`", "módulos terceiros... nenhum import de App.jsx").
- Because this is the exact architectural move Fases 28/32 already made once for the Setups/Operar split, and the ADR-027 isolation constraint (no `opcoes/*` file imports `App.jsx`) is an existing, tested guardrail — any new extracted file must respect it or a guardian test will likely catch the violation (precedent: `test_opcoes_*` source-scanning guardians already exist for this family of constraint).

## Version Compatibility

Not applicable — no new packages, no version pins to add. All primitives are plain React 18 JSX/hooks already in production use in this exact React 18.3.1 codebase.

## Sources

- `/Users/acamerini/dev/borisv2/web/src/opcoes/OpcoesScreen.jsx` (read in full context around lines 1-80, 320-440, 740-860) — primary source for the existing `subaba` toggle pattern, its explicit "no ARIA tab" comment, and the fully-lifted `useState` call sites.
- `/Users/acamerini/dev/borisv2/web/src/App.jsx` (lines 1030-1062, 2604, 3311, 3382, 3754, 3843, 4472, 350-364) — primary source for `BottomNav`'s top-level `aria-pressed` nav, the 6+ `aria-expanded` accordion instances, and the canonical `carouselTrackStyle` rail.
- `/Users/acamerini/dev/borisv2/web/src/opcoes/CuradoriaEstruturas.jsx`, `OportunidadesOpcoes.jsx`, `CandidatoOpcao.jsx` — confirm the carousel-rail and accordion patterns are reused (not reinvented) within the `opcoes/` module family.
- `/Users/acamerini/dev/borisv2/web/src/main.jsx:33` — confirms `<details>` is a one-off, not a house pattern.
- `/Users/acamerini/dev/borisv2/CLAUDE.md` (repo root, Technology Stack / Conventions / Architecture sections) — confirms no router, no state library, no UI kit anywhere in `web/`; confirms `T` token / inline-style convention and the ADR-027-style module-isolation rule (`opcoes/*` must not import `App.jsx`).
- `/Users/acamerini/dev/borisv2/.planning/PROJECT.md` (Milestone v1.5 "Decisões de arquitetura travadas") — confirms the locked decision "Sem migração de stack: estilo inline + tokens `var(--x)`, nada de Tailwind/shadcn," directly precluding any UI-kit addition for this milestone.
- Confidence: HIGH throughout — every claim above is grounded in reading this exact codebase's source, not in general React ecosystem conventions or training-data assumptions about what "usually" gets added for tab/accordion UI.

---
*Stack research for: reorganizing the Opções tab's "Setups" sub-screen by job-to-be-done (Boris+ / b3-agente, milestone v1.6)*
*Researched: 2026-09-19*
