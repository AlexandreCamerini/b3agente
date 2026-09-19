# Phase 18: Seção de Opções em Posições - Pattern Map

**Mapped:** 2026-09-03
**Files analyzed:** 3 (all modifications to existing files — no new files/routes expected per CONTEXT.md)
**Analogs found:** 3 / 3

No RESEARCH.md exists for this phase (config-disabled — this is pure UI reuse
of an already-shipped backend, decided in CONTEXT.md). All analogs below come
from `web/src/App.jsx`, which is the single-file frontend (~7600+ lines) —
new components live inline in the same file per project convention (CONTEXT.md
"Claude's Discretion": no file-split this phase).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `web/src/App.jsx` — new component `OportunidadesOpcoes` (or equivalent name), likely placed just above `CarteiraScreen` (~line 3905) or as a nested block inside it | component | request-response (fan-out N `optionsGate`/`optionsProposta` calls, one per `data.positions` ticker, aggregate render) | `AtivoCard`'s opGate/opProposta `useEffect` pair, `web/src/App.jsx:3213-3234` | exact (same gate→proposta two-step fetch, same best-effort silence-on-error) |
| `web/src/App.jsx` — `CarteiraScreen` function body, `web/src/App.jsx:3905-4148` (modified: render strip above KPI grid or above position list; render `<PropostaLastreada>` inside the `data.positions.map` loop, ~3991-4145) | component | CRUD-adjacent (reads `ctx.data.positions`, no new writes) | itself (same function, extend in place) — for the "toggle-by-ticker" click-to-focus mechanic, `histFor`/`editFor` state pattern in the same function is the closest existing analog | exact |
| `web/src/App.jsx` — optional extracted hook `useOpcoesProposta(t)` (Claude's Discretion in CONTEXT.md — extract vs. duplicate) | hook | request-response | `AtivoCard`'s inline `useEffect` pair, `web/src/App.jsx:3213-3234` | exact (this IS the logic being extracted) |
| `web/src/copy.js` — new keys for strip title, item summary, two empty-state variants (no eligible coverage vs. eligible-but-no-active-setup) | config (i18n/vocab dict) | CRUD (plain object literal, dual `estudo`/`operador` branches) | existing proposal-related keys, `web/src/copy.js:164-190` (estudo) and `:350-375` (operador); backend `skill_ref.OPCOES_LASTREADAS["sem_setup"]` for one of the two empty-state texts (see below — verified, not guessed) | exact for structure; partial reuse for the "eligible but no setup" empty-state text |
| `web/tests/test_carteira_opcoes_tira.mjs` (suggested name; planner may choose differently) | test | transform (static regex assertions over file text, no DOM/build) | `web/tests/test_opcoes_proposta_ui.mjs` (whole file) and `web/tests/test_carteira_lastro_ui.mjs` (whole file) | exact |

**No new backend files.** `server/app/main.py:2348-2422` (`GET /api/options/proposta/{ticker}`), `web/src/api.js:278` (`optionsGate`), `web/src/persistence.js:1130` (`store.optionsGate`/`optionsProposta`) are consumed as-is — CONTEXT.md is explicit: no bulk route, no new store method, both stores (`deviceStore`/`serverStore`) already have parity from Phase 14.

## Pattern Assignments

### New component: `OportunidadesOpcoes` (strip, NAV-01/NAV-03)

**Analog:** `AtivoCard`'s gate→proposta fetch pair, `web/src/App.jsx:3213-3234`

**Fetch pattern to replicate per ticker** (`web/src/App.jsx:3213-3234`):
```javascript
const [opOpen, setOpOpen] = useState(false);
const [opGate, setOpGate] = useState(null);
...
const [opProposta, setOpProposta] = useState(null);
const [opPropostaBusy, setOpPropostaBusy] = useState(false);

useEffect(() => {
  let alive = true;
  setOpGate(null);
  store.optionsGate(t).then((r) => { if (alive) setOpGate(r); }).catch(() => { /* gate é best-effort: sem ele, a linha só não aparece */ });
  return () => { alive = false; };
}, [t]);

// Fase 14 (Plano 06, D-8): a fase inteira fica dormente sem gate de
// liquidez — nenhuma requisição extra de proposta é feita além do que o
// gate já dispara. `opGate && opGate.liquida` é primitivo (boolean) na
// dependência: não recria o efeito a cada re-render do objeto do gate.
useEffect(() => {
  let alive = true;
  setOpProposta(null);
  if (opGate && opGate.liquida) {
    store.optionsProposta(t, true).then((r) => { if (alive) setOpProposta(r); }).catch(() => { /* best-effort, igual optionsGate */ });
  }
  return () => { alive = false; };
}, [t, opGate && opGate.liquida]);
```

**What to change for the strip vs. AtivoCard's single-ticker use:**
- This effect pair runs currently ONCE per `AtivoCard` instance (one ticker). The strip needs to run it **once per position ticker** (`ctx.data.positions`). Do NOT write a new fetch loop from scratch — either (a) extract this exact pair into `useOpcoesProposta(t)` and call it once per ticker inside a small per-item subcomponent that the strip `.map()`s over (preferred — keeps the `alive`-flag cleanup and the `[t, opGate && opGate.liquida]` dependency-boolean-primitive discipline intact), or (b) duplicate the pair per CONTEXT.md's explicit discretion. Either way, preserve the `.catch(() => {/* best-effort */})` — errors must never surface as a broken tile, only as absence (same silence contract AtivoCard uses for the gate).
- `data.positions.length` in this codebase is small (educational simulator) — CONTEXT.md explicitly green-lights N parallel per-ticker calls, same ADR-004 cost precedent ("1 chamada leve por card, best-effort") extended to N cards.

**Item truthy condition** (mirrors `web/src/App.jsx:3490`):
```javascript
{opGate && opGate.liquida && (
  <>
    <PropostaLastreada ... />
```
For the strip, an item only renders when `opGate.liquida && opProposta && opProposta.proposta` — i.e., gate passed AND a concrete proposal came back (not the "sem proposta" branch of `PropostaLastreada`, `web/src/App.jsx:3025-3035`).

**Manchete/headline reuse (CVM guardrail — do not violate):** the strip's item summary text MUST reuse `p.manchete` (`opProposta.proposta.manchete`) verbatim, the same field `PropostaLastreada` renders directly at `web/src/App.jsx:3059` (`{p.manchete}`). Never compose a new headline string in the strip component. See the guardian assertions in `test_opcoes_proposta_ui.mjs:58-60` (`ok("p.manchete é renderizado direto (sem composição)", ...)`, `ok("front não compõe a manchete...")`) — a Phase 18 test should add the equivalent assertion for the new strip component.

**Analytics event** — follow the existing `track()` call-site pattern, e.g. `web/src/App.jsx:3912` (`useEffect(() => { track("portfolio_view"); }, []);`) and `:3240` (`track("options_chain_view", { ticker: t, contexto });`). A new event name (e.g. `options_opportunities_view` or similar) should follow this exact `useEffect(() => { track(...) }, [])`-on-mount shape if the planner decides tracking is in scope (not explicitly required by CONTEXT.md, but consistent with every other screen).

---

### `CarteiraScreen` modification (NAV-01, NAV-02, NAV-03)

**Analog:** itself, `web/src/App.jsx:3905-4148` — extend in place, do not rewrite.

**Where the strip mounts** — immediately after the KPI grid / concentration warning and before the `data.positions.length === 0` empty-state block (`web/src/App.jsx:3974-3980`), because NAV-03 requires the strip to be entirely absent (not just empty-styled) when there are zero positions — this ordering makes that a natural early-return, matching the existing empty-state guard already at line 3974.

**Where `PropostaLastreada` gets added inside the position loop** — inside `data.positions.map((p) => {...})` (`web/src/App.jsx:3983-4145`), after the `AvisoLiquidacao`/`PlanRuler` block (~4006-4019) and likely near the "duas ações-bloco" CTA row (~4084-4091), following the same `operador`/`cp`/`busy` prop contract `PropostaLastreada` already has at `web/src/App.jsx:3492-3495`:
```javascript
<PropostaLastreada
  r={opProposta} operador={operador} cp={cp} busy={opPropostaBusy}
  onAbrir={onAbrirLastreada} onFechar={onFecharLastreada} posAberta={posAberta}
/>
```
`operador` for `CarteiraScreen` comes from `ctx.operador` (set at `web/src/App.jsx:8310`, `operador: appMode === "operador"`) — same source `AtivoCard` uses via its `vm`, just destructured differently. `cp` likewise comes from `ctx.cp` (already destructured at `web/src/App.jsx:3911`, `const { data, quotes, analysis, A, goMercado, cp } = ctx;`).

**`onAbrir`/`onFechar`/`posAberta` are NOT copy-pasteable as-is** — `onAbrirLastreada`/`onFecharLastreada` (`web/src/App.jsx:3292-3330`) and `posAberta` (`web/src/App.jsx:3289-3291`) currently live inside `AtivoCard`'s closure over its own `opProposta`/`t`/`myOptionPositions`. Inside `CarteiraScreen`'s position-loop, each `p` (position) needs its own copy of this logic scoped to `p.t` and that position's own `opProposta` fetch result (from the extracted hook or duplicated effect). Do not try to reuse `AtivoCard`'s closures directly — replicate the pattern per position, same shape:
```javascript
const posAberta = (opProposta && opProposta.proposta)
  ? myOptionPositions.find((pp) => pp.id === opProposta.proposta.contractSymbol) || null
  : null;
```
(swap `myOptionPositions` for the equivalent filtered list scoped to `p.t` inside `CarteiraScreen`, mirroring `web/src/App.jsx:3266-3275`).

**Click-to-focus mechanic (NAV-02, "clique no item rola/expande até o card")** — CONTEXT.md flags this as Claude's Discretion (`scrollIntoView` + `ref`, vs. expand a local `focusedTicker` state). The closest existing analog for "keyed-by-ticker toggle state that expands a specific position's card" is the `histFor`/`editFor` pattern already in `CarteiraScreen` itself:
```javascript
const [histFor, setHistFor] = useState(null);
const [editFor, setEditFor] = useState(null);
...
{histFor === p.t && ( ... )}
```
(`web/src/App.jsx:3907-3909`, `:4099`, `:4117`). If the planner chooses the "expand" route over `scrollIntoView`, this is the pattern to copy — a third sibling state (e.g. `focusedTicker`) toggled by the strip's `onClick`, read inside the position loop the same way `histFor`/`editFor` are read. Note: the codebase has **no existing `scrollIntoView`/`useRef`-per-list-item pattern** (checked via grep — only chart/gesture refs exist), so if the planner picks scroll-to-card instead, there is no in-repo analog to copy from; it would be new code, not a reuse.

---

### `web/src/copy.js` — new vocabulary keys (NAV-01, NAV-03)

**Analog:** existing proposal-related key block, `web/src/copy.js:160-190` (estudo) mirrored at `:346-376` (operador).

**Pattern to copy** — identical keys in both `COPY.estudo` and `COPY.operador` (guardian-enforced, see Testing section below), values differing only in voice (professor vs. mesa):
```javascript
// estudo (web/src/copy.js ~164-190)
eyebrowPropostaCall: "ESTUDO · VENDA COBERTA",
eyebrowPropostaPut: "ESTUDO · PUT DE PROTEÇÃO",
...
verCadeiaCompleta: "ver cadeia completa",
propostaIndisponivelDegradada: "Proposta indisponível — cotação de opções degradada.",
propostaVaziaTitulo: "Sem proposta agora",
...
fontePropostaLinha: (fonte, quando) => `Fonte: ${fonte} · ${quando}`,
fontePropostaSemDado: "Fonte do dado não declarada.",
```
New keys needed (naming is Claude's Discretion, values must not touch the guardrail-protected `manchete`/`didatica` fields):
- Strip title/eyebrow (e.g. `tiraOpcoesTitulo`).
- Per-item summary line (structure type + reused `manchete` — do not create a new headline string, only surrounding label text, e.g. an eyebrow like `cp.eyebrowPropostaCall`/`Put`/`Collar` already provide the structure-type label — reuse those three keys rather than inventing new ones).

**NAV-03 empty-state — CONTEXT.md's exact instruction was checked against the backend, with two different, VERIFIED outcomes per variant** (not a guess — grepped `server/app/skill_ref.py` and `server/app/options_api.py` directly):

1. **"Cobertura elegível mas sem setup técnico ativo hoje"** (gate passed for at least one position, but no proposal came back) — **a reusable equivalent EXISTS**: `server/app/skill_ref.py:515-551`, dict `OPCOES_LASTREADAS["operador"]["sem_setup"]` / `OPCOES_LASTREADAS["educacional"]["sem_setup"]`:
   ```python
   "sem_setup": "A leitura técnica de {ticker} não indica venda coberta nem put de proteção agora. A cadeia completa continua disponível abaixo.",
   ```
   This text is already delivered to the client PER TICKER as `motivoTexto` in the `GET /api/options/proposta/{ticker}` response (`server/app/main.py:2430-2434`: `motivo_texto = skill_ref.opcoes_lastreadas_txt(modo, motivo, ticker=t)` → `"motivoTexto": motivo_texto`), and is already rendered client-side in `PropostaLastreada`'s empty branch at `web/src/App.jsx:3030` (`r.motivo === "degradado" ? cp.propostaIndisponivelDegradada : r.motivoTexto`). **Caveat:** this text is per-ticker, singular ("a leitura técnica de {ticker}..."), while the strip's empty state is an aggregate across ALL positions — it cannot be concatenated N times without reading like a wall of near-duplicate sentences. Use it as the tone/wording SOURCE for a new aggregate copy.js key (same "a leitura técnica não indica [nenhuma] estrutura agora" register), not as a literal multi-ticker loop of `motivoTexto`.
   
2. **"Sem cobertura elegível"** (positions exist, but none pass the liquidity gate — `opGate.liquida === false` for all) — **NO reusable text exists**, verified negative: `server/app/options_api.py:135-156` (`GET /api/options/gate/{ticker}`) returns only `{"ticker": t, "liquida": bool, "providerStatus": str}` — no reason/message field at all, degraded or not. There is nothing in `skill_ref.py`, `conceitos.py`, or `mercado_ref.py` describing "sem contrato líquido" as user-facing copy (the closest hit, `OpcoesCamada`'s own inline empty-state strings at `web/src/App.jsx:3163`/`:3166` — "Cotação de opções indisponível no momento..." / "Nenhum contrato retornado para este vencimento." — are hardcoded in the component, not in `copy.js`/`skill_ref.py`, and describe the CHAIN view's empty state, not the gate's). Per CONTEXT.md's own fallback clause ("senão, texto novo em `web/src/copy.js`"), this variant is new copy — write it in `copy.js`, dual-mode, following the same header convention as `vazioPortfolio`/`vazioWatchlist` (`web/src/copy.js:59-60`).

**Convention reminder from the file header** (`web/src/copy.js:11-14`): "chaves idênticas nos dois modos (guardião compara os conjuntos); funções para textos com variáveis: saudacao(nome), resumoDia(n, g); vocabulário de ordem (comprar/vender) PROIBIDO no ramo estudo (guardião)." Any new key with a CTA-like verb must avoid "comprar"/"vender" in the `estudo` branch, same rule already enforced for `ctaVendaCoberta`/`ctaPutProtecao` (see `test_opcoes_proposta_ui.mjs:31-34`).

---

### Test file — `web/tests/test_carteira_opcoes_tira.mjs` (suggested)

**Analog:** `web/tests/test_opcoes_proposta_ui.mjs` (whole file, especially lines 1-27, 47-97) and `web/tests/test_carteira_lastro_ui.mjs` (whole file, especially lines 1-26).

**Structure to copy** — static text-based guardian, no build/DOM required:
```javascript
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ... assertions ...

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
```

**Assertions this guardian must include** (derived directly from CONTEXT.md's non-negotiable rules):
1. New copy keys exist in BOTH `COPY.estudo` and `COPY.operador` (same shape as `test_opcoes_proposta_ui.mjs:19-29`, `CHAVES_LASTREADAS.every((k) => k in COPY.estudo) && ...`).
2. The strip's item summary never composes a new headline — reuses `p.manchete`/`proposta.manchete` directly, same negative-assertion style as `test_opcoes_proposta_ui.mjs:58-60` (`!/"Vender " \+/.test(app)`, `!app.includes("Se você tivesse")`).
3. The strip is absent when `data.positions.length === 0` (NAV-03 second half) — assert the strip's render condition is guarded consistently with (or nested inside) the `data.positions.length === 0` check, e.g. locate the strip JSX and confirm it appears in source AFTER the positions-array is known non-empty, mirroring how `test_opcoes_proposta_ui.mjs:140-234` locates blocks by string index and slices between anchors to verify structural placement (not just presence).
4. `store.optionsGate`/`optionsProposta` calls from the new strip/hook remain wrapped in `.catch()` (best-effort) — same shape as `test_opcoes_proposta_ui.mjs:80-84` (`store.optionsProposta só dispara sob condição de opGate`).
5. If a `focusedTicker`-style state is added (click-to-focus), assert the position loop reads it the same way `histFor`/`editFor` are read (`{focusedTicker === p.t && ...}` or equivalent), analogous in spirit to the `TravaPill` "defined once, rendered ≥2 surfaces" check in `test_carteira_lastro_ui.mjs:24-26`.

**Do not delete/weaken existing guardians** — `test_opcoes_proposta_ui.mjs` and `test_carteira_lastro_ui.mjs` both assert things about `CarteiraScreen`/`AtivoCard`/`PropostaLastreada` that must keep passing unmodified; Phase 18 only ADDS a new render site for `PropostaLastreada`, it does not change the component's signature or existing call sites in `AtivoCard`.

## Shared Patterns

### Best-effort fetch, silent on error
**Source:** `web/src/App.jsx:3213-3234` (AtivoCard opGate/opProposta effects)
**Apply to:** the new strip component and/or extracted `useOpcoesProposta(t)` hook — every `store.optionsGate`/`optionsProposta` call site added in this phase must `.catch(() => {/* best-effort */})`, never surface a fetch error as a broken UI state. This is the same discipline already documented inline at `web/src/App.jsx:3216` and `:3231`.

### CVM headline guardrail — manchete only from the engine
**Source:** `web/src/App.jsx:3059` (`{p.manchete}`), enforced by `test_opcoes_proposta_ui.mjs:58-60`
**Apply to:** any text shown in the strip's per-item summary — must render `proposta.manchete` verbatim, never compose a new sentence from raw fields (strike, tipo, etc.) client-side. This is a project-level invariant (CLAUDE.md: "Manchete do card vem SÓ do motor determinístico").

### Dual-mode copy (`estudo` professor voice / `operador` mesa voice)
**Source:** `web/src/copy.js:11-14` (file header convention) + `:164-190`/`:350-375` (existing proposal keys)
**Apply to:** every new string surfaced by the strip and the empty-state messages — no hardcoded text in `App.jsx`, identical key sets in both branches, no order vocabulary ("comprar"/"vender") in the `estudo` branch.

### Reused backend reason-text for "no setup today" (verified — see copy.js section above)
**Source:** `server/app/skill_ref.py:533/546` (`OPCOES_LASTREADAS[modo]["sem_setup"]`), already surfaced client-side as `r.motivoTexto` at `web/src/App.jsx:3030`
**Apply to:** the wording/register of the strip's "cobertura elegível mas sem setup técnico" empty-state variant. Do not literally loop `motivoTexto` per ticker into the strip (it's a singular, per-ticker sentence) — write ONE new aggregate copy.js key that matches its tone ("a leitura técnica não indica [nenhuma] estrutura agora"), so the strip and the per-ticker card never contradict each other in register or claim.

### Keyed-by-ticker local UI state (expand/focus one item in a list)
**Source:** `web/src/App.jsx:3907-3909` (`histFor`/`editFor` in `CarteiraScreen`)
**Apply to:** NAV-02's "click item → open detail in the matching position card," if the planner picks the expand-state approach over `scrollIntoView` (no scroll-to-ref pattern exists elsewhere in the codebase to copy from — this would be genuinely new code, not a reuse, if chosen instead).

### `ctx` prop threading (`operador`, `cp`, `data`, `A`)
**Source:** `web/src/App.jsx:3911` (`const { data, quotes, analysis, A, goMercado, cp } = ctx;`) and `:8310` (`operador: appMode === "operador"`)
**Apply to:** the new strip component, if implemented as a sibling function receiving `ctx` the same way every other screen-level component does (`CarteiraScreen({ ctx })`, `HistoricoScreen({ ctx })`) — do not invent a different prop-passing convention.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| Click-to-scroll (`scrollIntoView` + `ref`-per-position) implementation, if chosen over the expand-state approach | interaction/utility | event-driven | No existing `scrollIntoView` or per-list-item `ref` pattern anywhere in `web/src/App.jsx` (verified via grep — only chart/gesture-related `useRef` calls exist). If the planner selects this UI mechanic, it is new code with no in-repo precedent to copy; recommend defaulting to the `histFor`/`editFor`-style expand pattern instead, which IS an exact analog. |
| "Sem cobertura elegível" (NAV-03 variant 2 — gate fails for all positions) reason text | config (copy) | n/a | Verified negative: `server/app/options_api.py:135-156` (gate endpoint) returns no reason/message field, and no equivalent phrase exists in `skill_ref.py`/`conceitos.py`/`mercado_ref.py`. New copy required — see copy.js section above for the exact grep evidence. |

## Metadata

**Analog search scope:** `web/src/App.jsx` (full-text grep + targeted reads of lines 1-35, 2990-3520, 3905-4150), `web/src/copy.js` (lines 1-390, targeted), `web/tests/*.mjs` (directory listing + full reads of `test_opcoes_proposta_ui.mjs`, `test_carteira_lastro_ui.mjs`), `server/app/skill_ref.py` (grep + targeted read of lines 495-565, `OPCOES_LASTREADAS` dict and `opcoes_lastreadas_txt`), `server/app/options_api.py` (targeted read of lines 130-160, `/gate/{ticker}` route), `server/app/main.py` (grep for `motivoTexto` wiring), `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`.
**Files scanned:** 8 read in full/targeted (App.jsx, copy.js, 2 test files, skill_ref.py, options_api.py, main.py excerpt, REQUIREMENTS.md/ROADMAP.md excerpts), plus directory listing of `web/tests/`.
**Pattern extraction date:** 2026-09-03
