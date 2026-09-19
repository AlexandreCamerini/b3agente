# Feature Research

**Domain:** Options-trading sub-screen information architecture (job-separation within an existing tab, no new capability)
**Researched:** 2026-09-19
**Confidence:** MEDIUM — IA principles are well-established (LOW risk of being wrong on "nested tabs >2 levels" and "screener ≠ symbol-detail ≠ saved-scan-management" as a pattern), but the specific mapping onto Boris+'s exact codebase (`web/src/opcoes/OpcoesScreen.jsx`) is my own reading of the source, not a cited external claim, so I'm flagging that split explicitly per finding.

## Context confirmed from source (not assumed)

Read directly from `web/src/opcoes/OpcoesScreen.jsx` before making any recommendation, per the quality gate:

- The app already has a working, non-router sub-tab mechanism: `subaba` is a plain `useState("setups")`, switched by a row of `<button aria-pressed=...>` — explicitly **not** `role="tab"` (comment at line ~757: "este app não usa ARIA de tab em lugar nenhum, ver BottomNav em App.jsx"). This is the load-bearing precedent: any new separation should reuse this exact mechanism, not invent a second one.
- `Opções` tab (level 1, bottom nav) → `subaba` Setups/Operar (level 2) → inside **Setups**, all 5 jobs currently render in one unconditional scroll (frase-ponte → Bloco A → Bloco B → vigias → seletor → LastroDoAtivo → LeituraInterna(free) → blocoLeituraDoServico(paid) → chain/estrutura/CriarSetup blocks gated by `ticker`/`painel`).
- Drill-down already exists as a **state gate**, not a route or a tab: `{ticker ? <LeituraInterna .../> : null}`, `{carteira.length > 0 ? seletor : null}`. Selecting a ticker via `seletor` is already, structurally, the "enter deep-work mode" trigger — it just doesn't currently hide the discovery/watcher blocks above it.
- `CriarSetup.jsx` (saved/automated setups) and `CartaoDeVigia` (watcher cards) are already separate components, just concatenated into the same scroll rather than separated into distinct destinations.

This confirms the codebase already has 90% of the *mechanism* needed (state-gated conditional rendering, an existing pill-row pattern) — the gap is purely in how blocks are grouped and sequenced, which matches the milestone's "reorganização, não funcionalidade nova" framing exactly.

## Feature Landscape

### Table Stakes (Users Expect These)

Patterns that table-stakes trading/screener tools (ThinkorSwim, Barchart, tastytrade, Unusual Whales) universally apply when discovery, single-instrument analysis, and saved-automation management coexist under one product area.

| Pattern | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Discovery lives on a **landing/hub view**, not mixed into a workspace | ThinkorSwim keeps Watchlist/Scanner as its own destination reachable from the bottom app menu, separate from the symbol-detail page (MEDIUM confidence, WebSearch-verified across ThinkorSwim + Barchart docs) | LOW | Fits directly: keep Bloco A + Bloco B (+ frase-ponte, unchanged) as the **default view of the "Setups" sub-tab when no ticker is selected** — this is already almost the natural order in the code, just needs the ticker-gated blocks moved out of the same scroll. |
| Selecting one instrument **switches the whole view** to a focused workspace, not just adds a section | ThinkorSwim's tap-to-search flow replaces the current screen content with the symbol page; it does not append the symbol page below the watchlist (MEDIUM confidence) | LOW–MEDIUM | Directly reuses the `ticker` state that already exists. Change is a rendering split (`ticker ? <TickerWorkspace/> : <DiscoveryHub/>`), not new state or new data. This IS the "progressive drill-down" pattern the question asks about, and it's the one that requires zero new mechanism in this app. |
| Saved automations/alerts are **managed in their own list**, decoupled from the scan results that inspired them | tastytrade's Watchlist Scanner and ThinkorSwim's "Hacker Scans" store saved scans/conditions as a separate persistent list, distinct from the live results table (MEDIUM confidence) | LOW | Maps directly onto `CriarSetup.jsx` + the saved-setups list (status/conditions/backtest/trigger history) — this should be its own hub section/card, not interleaved with Bloco A/B or with watcher cards. |
| Watchers/alerts get a **persistent, easily-reachable area** independent of the scan | Barchart and Unusual Whales keep alert management outside the screener's filter/result panel (MEDIUM confidence) | LOW | `blocoVigias` already exists as one block — the fix is purely where it sits (its own hub card) not whether it exists. |
| **Density differs by job, not uniformly**: dense compact rows for "scan many," roomier single-column sequential layout for "deep-work one" | Cross-checked across ThinkorSwim (scanner = dense table; symbol page = full-width sequential panels) and Barchart screener docs (MEDIUM confidence) | LOW | Milestone explicitly says card density is NOT being reduced — this pattern doesn't ask you to shrink Bloco A/B cards, only to give the single-ticker workspace (thesis→expiration→lot→build, plus vencimento comparison) its own full-width sequential layout instead of squeezing it into the same scroll as dense list cards. |

### Differentiators (Fit This Specific Product, Not Generic Best Practice)

Patterns that go beyond minimum separation and specifically suit a **self-taught retail learner in a simulator**, not a professional terminal user — checked against Core Value (Modo Estudo teaches reasoning) and against "no new feature."

| Pattern | Value Proposition | Complexity | Fit check |
|---------|--------------------|------------|-----------|
| Job cards on the hub carry a **one-line job label** ("Descobrir oportunidades" / "Meus vigias" / "Meus setups automáticos") instead of relying on the visitor to infer the job from content shape | Retail learners scanning a long mixed screen don't have the vocabulary yet to separate "this is a scan result" from "this is my saved automation" — professionals infer this from familiarity with terminal conventions, beginners need the label | LOW | Pure copy/label work on top of existing `cp.*` vocabulary strings (`skill_ref.py`/`copy.js` pattern already used for mode-specific vocabulary) — no new data, no new component logic, fits "reorganização apenas." |
| Hub uses **stacked full-width sections in a fixed, predictable order** (discovery → vigias → setups salvos) rather than a grid of equal-weight cards a user must choose among | A grid of equal cards implies "pick one path," which fits a professional choosing a tool; a beginner benefits more from a fixed narrative order that matches the mental model "first see what's out there, then see what I'm watching, then see what I've automated" — this also happens to match the code's current natural order | LOW | Zero new interaction pattern — same vertical scroll shell as today, just partitioned. Cheapest option that still solves the stated problem. |
| Entering the single-ticker workspace shows a **lightweight "you are here" affordance** (e.g., a back-to-discovery action, or the ticker name persisted at the top) instead of a bare tab switch | Because this is a state toggle and not a real tab/route, without an explicit affordance the learner may not realize they left the discovery view — professionals are used to terminal-style navigation and don't need this, beginners lose orientation easily in single-page apps with no URL/back button | LOW–MEDIUM | Needs one small addition (a persistent header row + "Voltar" control) — still no router, no new data source, just one new small piece of UI state layered on the existing `ticker` gate. This is the one item here that is closest to "new," so flag it for explicit scope confirmation rather than assuming it's included for free. |

### Anti-Features (Look Like Best Practice, Wrong for This App/Milestone)

| Pattern | Why It Looks Appealing | Why It's Wrong Here | Alternative |
|---------|------------------------|----------------------|-------------|
| Full router-based IA (distinct URLs/routes per job, like a real trading platform's `/scan`, `/symbol/:ticker`, `/alerts`) | This is literally how ThinkorSwim/Barchart/TradingView structure the same 3-way split at a page level | App is explicitly no-router, hand-rolled state (`isNative ? deviceStore() : serverStore()`, `useState` navigation throughout); adopting routes here is an architecture change, not a reorg — directly violates "nenhuma funcionalidade nova" and the existing precedent that this app deliberately doesn't use tab/route ARIA semantics | Reuse the existing `useState` + conditional-render mechanism (see Table Stakes row 2) — a state-gated hub/workspace toggle achieves the same separation without new infrastructure. |
| A **third-level nested tab row** inside "Setups" (i.e., add sub-sub-tabs: Descobrir / Vigias / Analisar / Comparar / Setups) mirroring the existing Setups/Operar pill row one level down | Reuses the exact pill-row component already in the codebase, looks consistent | UX research is consistent that **nested tabs beyond two levels harm orientation and tab/content-relationship tracking** (LogRocket, UX Planet, Design Monks — MEDIUM confidence, multiple sources agree). This app is already at 2 levels (bottom nav → Setups/Operar); a 3rd tab level for 5 jobs is exactly the anti-pattern the sources warn against, and with 5 items a pill row also stops fitting on a 375px mobile viewport (this app's tested breakpoint per v1.5 milestone) | Progressive disclosure via a hub view + drill-down state (as in Table Stakes), not more tabs. Accordions were also suggested by UX sources as a nested-tab alternative, but a hub-with-sections fits this app's existing vertical-scroll shell better than accordion collapse/expand chrome, which would be new interaction surface. |
| Bloomberg-terminal-style simultaneous multi-pane layout (discovery list + chain + watchlist all visible in adjacent panels at once) | This is what professional desktop options terminals do for "deep work on many things without losing context" | Wrong audience and wrong surface: Boris+ is mobile-first PWA/Capacitor for a self-taught retail learner (Core Value: "aprendeu o raciocínio," not power-user multitasking); multi-pane simultaneous layout also directly increases the density this milestone says NOT to touch, and requires new responsive-layout work the milestone doesn't ask for | Sequential, one-job-at-a-time views (hub → workspace), consistent with the existing single-column mobile shell. |
| A universal "jump to anything" search/command bar across the 5 jobs (TradingView-style omnisearch) | Feels powerful, matches what pro tools ship | New feature (search infra, ranking, keyboard/tap target design) — explicitly out of scope ("nenhuma funcionalidade nova"); also solves a discovery problem this app doesn't have yet (5 jobs, not 50 tools) | The existing ticker `seletor` (already built) is the only "jump to a specific thing" affordance this milestone needs; it just needs to trigger the hub→workspace transition described above. |
| Continuous/streaming auto-refresh across the discovery hub, to feel more "terminal-grade real-time" | Professional screeners refresh live | App's data-staleness discipline (CLAUDE.md principle 3: always show source/timestamp/staleness, never silently refresh into false freshness) and MCP budget/quota model (ADR-008, `brapi_budget`) make unmanaged auto-refresh a cost and correctness risk unrelated to this milestone's IA goal | Keep existing manual-fetch/quota-gated model; this reorg doesn't touch data-fetching behavior at all. |
| Drag-and-drop personalizable hub layout (reorder/hide job cards) | Natural "differentiator" instinct once you have a card-based hub | Explicitly deferred: PROJECT.md records "reorganizar primeiro, personalizar depois" and scopes personalization/progressive-disclosure/adaptive-challenge to Fases 2–4, not this milestone | Fixed, non-personalized section order now (see Differentiators row 2); leave the hook for personalization to a later milestone without pre-building it. |

## Feature Dependencies

```
Hub/workspace state split (ticker ? Workspace : Hub)
    └──requires──> existing `ticker` useState (ALREADY PRESENT — zero new state)
    └──requires──> moving (not rewriting) blocoOportunidades/blocoCuradoria/blocoVigias/CriarSetup
                    into hub-only render path, and seletor/LeituraInterna/blocoLeituraDoServico/
                    chain+vencimento blocks into workspace-only render path

"You are here" affordance in workspace ──enhances──> Hub/workspace state split
    (optional layer; without it the split still works, just with weaker orientation cues)

Hub section labels (cp.* vocabulary strings) ──enhances──> Hub/workspace state split
    (copy-only addition, no logic dependency)

Third-level nested tabs ──conflicts──> existing 2-level nav (bottom nav + Setups/Operar)
    (this is why it's an anti-feature here, not merely non-essential)

Personalizable/reorderable hub ──conflicts──> this milestone's decided scope
    (PROJECT.md: "reorganizar primeiro, personalizar depois" — do not build the hook now)
```

### Dependency Notes

- **Hub/workspace split requires only the existing `ticker` state:** this is the single most important finding for scoping the roadmap — the entire reorg can be implemented as a rendering reshuffle inside `OpcoesScreen.jsx`, with no new state, no new data fetch, no new component contract. That keeps it squarely inside "reorganização, não funcionalidade nova."
- **"You are here" affordance enhances but doesn't gate the split:** it can ship in the same phase cheaply or be deferred one phase without blocking the core separation — call this out explicitly to whoever plans phases, since it's the one item in this research with the highest chance of scope-creeping into "new feature" territory if over-built (e.g., don't build a breadcrumb history stack; a single back-to-hub action is enough).
- **Third-level nested tabs conflicts with existing nav depth:** flagging this as a hard "don't" for the roadmap, not a soft preference — it's the one candidate pattern a naive read of "add sub-tabs for job separation" would produce, and it's the one the cited UX sources most directly warn against for exactly this app's situation (2 levels already, mobile viewport, 5 candidate sub-items).

## MVP Definition

### Launch With (v1 — this milestone, v1.6)

- [ ] Hub view (default state of "Setups" sub-tab, no ticker selected) containing, in fixed order: frase-ponte (unchanged) → Bloco A → Bloco B → vigias section → setups salvos (list + "Criar um setup") — why essential: this alone eliminates the 5-jobs-in-one-scroll problem for 3 of the 5 jobs (discovery ×2 + watchers + automations) using zero new mechanism.
- [ ] Workspace view (ticker selected) containing: seletor/LastroDoAtivo → LeituraInterna (free) → blocoLeituraDoServico (paid) → chain/estrutura (manual analysis, job 3) → vencimento comparison (job 4) — why essential: separates the two remaining jobs (manual single-ticker analysis + vencimento comparison) from discovery/watchers/automations, matching the milestone's explicit list.
- [ ] Section labels using existing `cp.*` vocabulary pattern so each hub section names its job — why essential: without a label, grouping alone doesn't solve "which job am I looking at," per the Differentiators finding.

### Add After Validation (v1.x)

- [ ] "You are here" / back-to-hub affordance in the workspace view — trigger for adding: if live use (or a lightweight test) shows people getting stuck in the ticker workspace without noticing they left discovery.
- [ ] Comparação de vencimentos as its own explicitly labeled block within the workspace (rather than just adjacent to the chain analysis) — trigger for adding: if this milestone's execution finds job 3 and job 4 are still visually blurring together inside the workspace view itself.

### Future Consideration (v2+, already decided out-of-scope in PROJECT.md)

- [ ] Progressive disclosure of the frase-ponte (Fase 2) — defer until the reorg above ships and is validated live.
- [ ] Learner progress model scoped to option concepts (Fase 3) — defer, separate milestone.
- [ ] Personalized challenge by observed pattern (Fase 4) — defer; explicit regulatory-risk flag already recorded in PROJECT.md (soaring too close to "recommendation").
- [ ] Personalizable/reorderable hub layout — defer per PROJECT.md's explicit sequencing decision ("reorganizar primeiro, personalizar depois").

## Feature Prioritization Matrix

| Pattern | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Hub/workspace split via existing `ticker` state | HIGH | LOW | P1 |
| Section labels for each hub job | HIGH | LOW | P1 |
| Saved-setups list as its own hub section (decoupled from discovery scroll) | HIGH | LOW | P1 |
| Watchers as its own hub section | MEDIUM–HIGH | LOW | P1 |
| "You are here"/back-to-hub affordance | MEDIUM | LOW–MEDIUM | P2 |
| Explicit vencimento-comparison sub-block label inside workspace | MEDIUM | LOW | P2 |
| Third-level nested tabs | — (anti-feature) | MEDIUM | Do not build |
| Router-based IA | — (anti-feature) | HIGH | Do not build |
| Personalizable hub layout | LOW (now) | MEDIUM | P3 / explicitly deferred |

## Competitor Feature Analysis

| Job separation aspect | ThinkorSwim (mobile) | Barchart / tastytrade | Boris+ v1.6 approach |
|---|---|---|---|
| Discovery (screener/scanner) | Separate "Scanner" tool from bottom "More" menu, dense filter+results table | Dedicated Options Screener page with filter sidebar + results table | Hub view, Bloco A + Bloco B, density unchanged (per milestone constraint) |
| Single-instrument deep dive | Tap magnifying glass → full symbol detail page replaces current screen | Symbol page reached by clicking a screener row | Selecting a ticker (`seletor`) swaps hub for a workspace view — reuses existing state, no router |
| Saved automations/alerts | "Hacker Scans" presets + saved scans, stored separately from live results | tastytrade Watchlist Scanner presets, separate from live scan | `CriarSetup`/setups-salvos as its own hub section, not interleaved with Bloco A/B |
| Watchlist/alerts management | Dedicated "Watchlist" bottom-menu destination | Watchlist decoupled from screener filters | `blocoVigias` as its own hub section |

## Sources

- [thinkorswim mobile Getting Started (Schwab)](https://toslc.thinkorswim.com/center/howToTos/thinkManual/Getting-Started) — bottom app menu (Watchlist/Trade/Positions/More), magnifying-glass symbol search flow, MEDIUM confidence (official docs)
- [Scanning for Stocks with the Stock Hacker Tool — Schwab](https://www.schwab.com/learn/story/scanning-stocks-with-stock-hacker-tool) — scanner filter/column/results structure, preset saved-scan categories, MEDIUM confidence (official)
- [Barchart Options Screener](https://www.barchart.com/options/options-screener) — filter-driven screener separate from watchlist/alerts, MEDIUM confidence
- [7 Best Options Screeners of 2026 — DayTradingz](https://daytradingz.com/best-options-screener/) and [ChartingLens roundup](https://chartinglens.com/blog/best-options-trading-tools-scanners) — cross-tool pattern confirmation (screener vs. chain analysis vs. alerts as distinct destinations), LOW–MEDIUM confidence (aggregator content, used only for pattern corroboration, not as sole source)
- [Tabs for Mobile UX Design — UX Planet](https://uxplanet.org/tabs-for-mobile-ux-design-d4cc4d9410d1) — nested-tabs-harm-orientation finding, MEDIUM confidence
- [Tabbed navigation in UX — LogRocket](https://blog.logrocket.com/ux-design/tabs-ux-best-practices/) — "stick to two levels of tab depth" guidance, MEDIUM confidence, corroborates UX Planet independently
- [Nested Tab UI Examples — Design Monks](https://www.designmonks.co/blog/nested-tab-ui) — accordion/progressive-disclosure as the standard alternative to a third tab level, MEDIUM confidence
- `web/src/opcoes/OpcoesScreen.jsx` (this repo) — read directly to confirm the existing sub-tab mechanism, state-gated drill-down precedent, and current block order; HIGH confidence (primary source, not inferred)
- `.planning/PROJECT.md` (this repo) — Milestone v1.6 scope, out-of-scope decisions (Fases 2–4), "reorganizar primeiro, personalizar depois"; HIGH confidence (primary source)

---
*Feature research for: Boris+ Opções tab "Setups" sub-screen reorganization (Milestone v1.6)*
*Researched: 2026-09-19*
