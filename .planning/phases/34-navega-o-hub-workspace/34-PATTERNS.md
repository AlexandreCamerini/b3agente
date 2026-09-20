# Phase 34: Navegação hub + workspace - Pattern Map

**Mapped:** 2026-09-20
**Files analyzed:** 4 (2 modified, 1 new component, 1 new/extended test) + 1 shared data file (copy.js)
**Analogs found:** 4 / 4

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|---------------|
| `web/src/opcoes/OpcoesScreen.jsx` (modified — split render into Hub/Workspace branches) | component (screen orchestrator) | request-response (renders from `ticker`/`subaba`/hook state, no new fetch) | itself — `subabas` pill-row block (lines 600-617) and `cabecalho` box (lines 411-467) as internal analogs for the two new pieces | exact (same file, same author conventions) |
| `web/src/opcoes/WorkspaceHeader.jsx` (NEW — D-05, ticker name + "Voltar") | component (small presentational, props-only) | request-response (pure render, one callback prop) | `web/src/opcoes/SecaoVigias.jsx` (whole-file pattern: VARKEY/TOKENS mirror + local `BOTAO` + props-only) | role-match (closest existing "small extracted job component" shape in this directory) |
| `web/src/opcoes/SecaoSetups.jsx` (modified — add `modo: "lista" \| "criar"` prop, gate the two existing blocks) | component (CRUD list + create) | CRUD | itself — the file already splits cleanly at the two `Kicker` blocks (list at line 56, create at line 193) | exact |
| `web/src/copy.js` (modified — add `cp.opcoesVoltarAoHub`, `cp.opcoesAbaAnalisar`, `cp.opcoesAbaComparar`, `cp.opcoesAbaCriarSetup` in BOTH `COPY.estudo` and `COPY.operador`) | config (i18n/vocab dictionary) | CRUD (dictionary entries) | existing sibling keys `opcoesSubabaSetups`/`opcoesSubabaOperar` (estudo: lines 383-384; operador: lines 1012-1013) | exact |
| `web/tests/test_opcoes_hub_workspace_ui.mjs` (NEW guardian test) | test | transform (static-source grep assertions, no runtime render) | `web/tests/test_opcoes_subabas_ui.mjs` (whole-file pattern: no-build source-slice + regex guardian) | exact |

## Pattern Assignments

### `web/src/opcoes/OpcoesScreen.jsx` (component, request-response)

**Analog:** itself (existing `subabas` and `cabecalho` blocks in the same file)

**Imports pattern** (already present, lines 60-82) — no new imports needed for the split itself, only `WorkspaceHeader`:
```javascript
import { Kicker, Aviso, ErroDoMcp, RecusaCobrada, Linha } from "./uiOpcoes.jsx";
import SecaoVigias from "./SecaoVigias.jsx";
import SecaoAnalisar from "./SecaoAnalisar.jsx";
import SecaoDescobrir from "./SecaoDescobrir.jsx";
import SecaoSetups from "./SecaoSetups.jsx";
import SecaoComparar from "./SecaoComparar.jsx";
// ADD:
import WorkspaceHeader from "./WorkspaceHeader.jsx";
```

**Core pill-row pattern to copy verbatim for the new 3-tab workspace row** (`subabas`, lines 600-617 — D-02 says "mesmo componente de pill já usado em Setups/Operar"):
```javascript
const subabas = (
  <div style={{ display: "flex", gap: "8px", margin: "10px 0 4px" }}>
    {[
      { id: "setups", rotulo: cp.opcoesSubabaSetups || "Setups" },
      { id: "operar", rotulo: cp.opcoesSubabaOperar || "Operar" },
    ].map((s) => (
      <button
        key={s.id}
        type="button"
        onClick={() => setSubaba(s.id)}
        aria-pressed={subaba === s.id}
        style={{ minHeight: "44px", padding: "8px 14px", borderRadius: "11px", border: `1px solid ${subaba === s.id ? T.accent : T.borderSubtle}`, background: subaba === s.id ? T.accentTint10 : T.bgPanel, color: subaba === s.id ? T.accent : T.textSecondary, fontWeight: 700, fontSize: "13px" }}
      >
        {s.rotulo}
      </button>
    ))}
  </div>
);
```
New `workspacePillRow` (3 tabs: Analisar/Comparar/Criar Setup, new local `useState` — same mechanism, NOT the existing `subaba` state which is the outer Setups/Operar switch) copies this block verbatim, only changing the tab array and the state variable name (e.g. `abaWorkspace`/`setAbaWorkspace`) and the `cp.*` keys (`cp.opcoesAbaAnalisar`, `cp.opcoesAbaComparar`, `cp.opcoesAbaCriarSetup`). Do not reuse the outer `subaba` state — that one already means "Setups vs Operar" and is orthogonal to the new workspace-internal tab.

**Box pattern to copy for `WorkspaceHeader`'s container** (`cabecalho`, lines 411-412 — UI-SPEC mandates reusing this exact box):
```javascript
<div style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "14px", padding: "12px 14px", background: T.bgPanel }}>
```

**Button pattern to copy for the "Voltar" button** (`BOTAO` constant, lines 122-126 — UI-SPEC mandates reusing this exact style, neutral not accent):
```javascript
const BOTAO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, fontWeight: 700, fontSize: "13px",
};
```

**Toggle/reset pattern for "Voltar" button's onClick** (D-03: leaving workspace resets tese/vencimento/alvo/stop — this is exactly what the existing toggle branch of `escolherTicker` already does when re-clicking the same ticker chip, lines 291-294):
```javascript
const escolherTicker = (t) => {
  setTicker(t === ticker ? "" : t);
  setTese(""); setVencimento(""); setAlvo(""); setStop("");
};
```
"Voltar" should call `escolherTicker(ticker)` (or an equivalent `() => escolherTicker(ticker)`) rather than inventing a second reset path — `t === ticker` is true when called with the current ticker, so it clears `ticker` and resets the four fields in one existing function. Do not write a second, parallel reset.

**Render-order and conditional-split target** (current structure to restructure, lines 619-868): today everything from `{cabecalho}` through the closing `</>` at line 864 is a single flat sequence inside `subaba !== "setups" ? <SubAbaOperar/> : (<>...</>)`. The hub/workspace split happens INSIDE the `else` branch (the `subaba === "setups"` case), per the Layout Contract:
```
{cabecalho}                          ← stays above the split (both modes)
{carregando ? ... : erro ? ... :     ← branches 1–2 stay above the split
  ticker ? (
    <>
      <WorkspaceHeader ticker={ticker} onVoltar={() => escolherTicker(ticker)} cp={cp} />
      {ticker ? <LastroDoAtivo .../> : null}
      {ticker ? <LeituraInterna .../> : null}
      {podePedirLeitura ? blocoLeituraDoServico : null}
      {workspacePillRow}
      {/* branch 3b / 4 content, ticker-scoped, tab-gated */}
    </>
  ) : (
    <>
      {secaoDescobrir}
      <SecaoVigias .../>
      {carteira.length > 0 ? seletor : null}
      {/* branch 3a content */}
      <SecaoSetups modo="lista" .../>
    </>
  )
}
```
`seletor` (lines 554-567) moves inside the hub-only branch and is NOT rendered once `ticker` is truthy (UI-SPEC's explicit resolution of the toggle-vs-back-button ambiguity — do not duplicate it into the workspace).

**Error handling pattern** (already correct, do not alter): `escolherErroOpcoes`/`erro.code` branching (lines 691-716) stays exactly where it is, above the split — untouched by this phase.

---

### `web/src/opcoes/WorkspaceHeader.jsx` (NEW component, request-response)

**Analog:** `web/src/opcoes/SecaoVigias.jsx` (whole-file shape)

**Imports + token-mirror pattern** (lines 11-18 of `SecaoVigias.jsx`, copy this shape, trimming `TOKENS` to only what's used):
```javascript
import { Kicker } from "./uiOpcoes.jsx"; // only if a Kicker-style label is used; otherwise plain <div>

const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["borderSubtle", "bgPanel", "textPrimary", "textSecondary"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));
```
Zero import of `App.jsx` — same ADR-027 Decisão 3 isolation every file in this directory declares in its header comment. Follow the same doc-comment convention (a `/** ... */` block at top explaining phase/plan number and why the component exists, matching `SecaoVigias.jsx` lines 1-10 and `SecaoSetups.jsx` lines 1-25).

**Local button-style mirror** (`BOTAO`, `SecaoVigias.jsx` lines 26-30 — reuse verbatim per Spacing Scale contract, this is the "Voltar" button style):
```javascript
const BOTAO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, fontWeight: 700, fontSize: "13px",
};
```

**Props-only contract** (core pattern — every `Secao*.jsx` in this directory receives all data by prop and calls zero hooks/stores directly; `SecaoVigias.jsx` line 52 signature is the template):
```javascript
export default function WorkspaceHeader({ ticker, onVoltar, cp }) {
  const c = cp || {};
  return (
    <div style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "14px", padding: "12px 14px", background: T.bgPanel, marginBottom: "10px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px" }}>
        <span style={{ fontSize: "15px", fontWeight: 800, color: T.textPrimary }}>{ticker}</span>
        <button type="button" onClick={onVoltar} style={BOTAO}>
          {c.opcoesVoltarAoHub || "Voltar"}
        </button>
      </div>
    </div>
  );
}
```
Typography values (15px/800 for ticker name, 13px/700 for the button label) are exact values from UI-SPEC's Typography section — do not substitute the screen `h1` size (22px/800) or any other heading scale.

---

### `web/src/opcoes/SecaoSetups.jsx` (component, CRUD)

**Analog:** itself

**Current structure to partition** (full file already read — 210 lines):
- Lines 48-56: function signature + `Kicker` "SETUPS GRAVADOS" (list section start)
- Lines 58-184: the entire list render (naoAvaliado banner, empty state, `listaSetups.map(...)` cards with grafico/BotaoDesativar)
- Lines 186-207: `Kicker` "CRIAR UM SETUP" + `<CriarSetup .../>` (create section, gated by `podeCriarSetup`)

**Core pattern — add `modo` prop, gate each existing block, do not duplicate the file** (per UI-SPEC's explicit, non-binding-but-recommended shape):
```javascript
export default function SecaoSetups({
  ticker, setups, naoAvaliado, grafico, abrirGrafico, fecharGrafico,
  setupNovo, compilarSetup, confirmarSetup, desativarSetup,
  podeCriarSetup, custos, cp, ctx, palette,
  modo, // NEW: "lista" | "criar"
}) {
  const listaSetups = Array.isArray(setups) ? setups : [];
  return (
    <>
      {modo === "lista" ? (
        <>
          <Kicker>{cp.opcoesSetupsTitulo || "SETUPS GRAVADOS"}</Kicker>
          {/* ...existing lines 58-184, unchanged... */}
        </>
      ) : null}

      {modo === "criar" && podeCriarSetup ? (
        <>
          <Kicker>{cp.opcoesCriarTitulo || "CRIAR UM SETUP"}</Kicker>
          <CriarSetup ticker={ticker} estado={setupNovo} onCompilar={compilarSetup} onConfirmar={confirmarSetup} custos={custos} cp={cp} />
        </>
      ) : null}
    </>
  );
}
```
Do not rename the internal `Kicker` copy keys (`cp.opcoesSetupsTitulo`, `cp.opcoesCriarTitulo`) — UI-SPEC explicitly forbids this ("do not duplicate the file or rename the internal Kicker copy"). Caller in `OpcoesScreen.jsx` passes `modo="lista"` in the hub branch and `modo="criar"` in the workspace branch (inside the new 3rd pill-row tab), each time omitting the props only relevant to the other mode is NOT required — pass everything as today, `modo` is purely a render gate, not a prop-surface reduction.

**Error/empty-state pattern (unchanged, do not touch):** `naoAvaliado` banner (lines 58-65) and the `listaSetups.length === 0` empty-state (`cp.opcoesSemSetups`, line 68) stay exactly as-is — they belong to `modo === "lista"` and are not reachable from `modo === "criar"`.

---

### `web/src/copy.js` (config, dictionary)

**Analog:** existing sibling entries in both locale branches

**Pattern** (estudo branch, insert near lines 383-384; operador branch, insert near lines 1012-1013 — same key set, different copy per mode, mirroring how `opcoesSubabaSetups`/`opcoesSubabaOperar` already differ in tone between estudo/operador):
```javascript
// COPY.estudo
opcoesVoltarAoHub: "Voltar",
opcoesAbaAnalisar: "Analisar",
opcoesAbaComparar: "Comparar",
opcoesAbaCriarSetup: "Criar Setup",

// COPY.operador — same or terser tone, following the existing estudo/operador
// divergence pattern seen in opcoesSubabaOperar ("Operação" vs "Operar")
opcoesVoltarAoHub: "Voltar",
opcoesAbaAnalisar: "Analisar",
opcoesAbaComparar: "Comparar",
opcoesAbaCriarSetup: "Criar Setup",
```
**Mandatory parity rule** (this is what `test_opcoes_subabas_ui.mjs`'s check #9 enforces and the new guardian test below must repeat): every `cp.X` key referenced from any file in `web/src/opcoes/` MUST exist in BOTH `COPY.estudo` and `COPY.operador` — a key present in only one locale passes silently until the untested mode is opened live and throws.

---

### `web/tests/test_opcoes_hub_workspace_ui.mjs` (NEW guardian test)

**Analog:** `web/tests/test_opcoes_subabas_ui.mjs` (whole-file pattern — no-build, static-source-slice regex guardian)

**Imports + source-loading pattern** (lines 51-64):
```javascript
import { readFileSync, readdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");

const tela = readFileSync(join(dirOpcoes, "OpcoesScreen.jsx"), "utf8");
const secaoSetups = readFileSync(join(dirOpcoes, "SecaoSetups.jsx"), "utf8");
const workspaceHeader = readFileSync(join(dirOpcoes, "WorkspaceHeader.jsx"), "utf8");
```

**Comment-stripping pattern** (lines 69-73, needed because assertions grep for terms also used in explanatory comments):
```javascript
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
```

**Assertion style** (`ok(name, cond)` helper, lines 75-76):
```javascript
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
```

**Concrete guardian assertions this new test file should encode** (derived directly from `34-CONTEXT.md` D-01..D-05 and the UI-SPEC Layout Contract — each is a defect this phase could silently reintroduce):
1. `cabecalho` and the `carregando`/`erro` cascade branches render ABOVE `ticker ? ... : ...` — i.e. the literal `ticker ?` conditional text appears in the source AFTER `carregando ?`/`erro ?` (line-index comparison, same technique as check #11's `tela.includes(nome)` but with `indexOf` ordering).
2. `seletor` is referenced inside the hub branch only, never inside a block that also references `<WorkspaceHeader` (slice-based, same technique as check #1's `subAba` slice in the analog).
3. `<SecaoSetups modo="lista"` appears exactly once and `<SecaoSetups modo="criar"` appears exactly once in `OpcoesScreen.jsx` (regression guard for D-01's split).
4. Every `cp.X` referenced in `WorkspaceHeader.jsx` and the new pill-row block exists in both `COPY.estudo` and `COPY.operador` (same technique as check #9).
5. The new pill-row button markup contains `aria-pressed=` and `minHeight: "44px"` (same technique as check #10).
6. `SecaoSetups.jsx` still contains both `cp.opcoesSetupsTitulo` and `cp.opcoesCriarTitulo` unchanged (guards against the UI-SPEC's explicit "do not rename" instruction).
7. No manchete-rendering leak: `WorkspaceHeader.jsx` is NOT added to `RENDERIZADORES_DE_MANCHETE` and does not match `/\.manchete\b/` — reuse check #12's `arquivosOpcoesDir` scan technique from the analog (it is directory-wide already, so this file is automatically covered if the analog test itself is re-run; the new test file only needs its own targeted assertion if it duplicates the scan rather than relying on the existing one).

**Exit pattern** (lines 275-279, copy verbatim):
```javascript
if (fails > 0) {
  console.log(`\n${fails} falha(s).`);
  process.exit(1);
}
console.log("\ntodos os testes passaram");
```

Register the new file in `scripts/executar.sh --testes`'s `.mjs` collection the same way every other `test_*.mjs` under `web/tests/` already is (glob-based — check `scripts/executar.sh` for how the JS suite is invoked; if it's a `for f in web/tests/test_*.mjs` glob, no registration step is needed).

---

## Shared Patterns

### Token-mirror declaration (CSS custom properties)
**Source:** `web/src/opcoes/SecaoVigias.jsx` lines 13-18, `web/src/opcoes/SecaoSetups.jsx` lines 30-35, `web/src/opcoes/OpcoesScreen.jsx` lines 84-89
**Apply to:** `WorkspaceHeader.jsx` (new file) — every file in `web/src/opcoes/` re-declares its own `VARKEY`/`TOKENS`/`T` trio locally rather than importing from `App.jsx`, by design (ADR-027 Decisão 3, two-way isolation — enforced by `test_opcoes_subabas_ui.mjs` check #1's directory-wide `App.jsx` import scan). Do not import `T` from `OpcoesScreen.jsx` either — declare the small subset of tokens actually used, same as every existing sibling.
```javascript
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = [/* only the keys this file uses */];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));
```

### Props-only components, zero direct hook/store access
**Source:** `web/src/opcoes/SecaoSetups.jsx` lines 8-10 (doc comment), `web/src/opcoes/SecaoVigias.jsx` lines 6-9
**Apply to:** `WorkspaceHeader.jsx` and the modified `OpcoesScreen.jsx` split — only `OpcoesScreen.jsx` calls `useOpcoesMcp`/`useOpcoesPropostas` (REORG-03/04 invariant, restated in `34-CONTEXT.md`'s Integration Points). `WorkspaceHeader` receives `ticker`/`onVoltar`/`cp` and nothing else; it must not read `ctx` or any store directly.

### 44px touch target + `aria-pressed` on any new interactive control
**Source:** `web/src/opcoes/OpcoesScreen.jsx` lines 122-126 (`BOTAO`), lines 554-567 (`seletor`), lines 600-617 (`subabas`)
**Apply to:** `WorkspaceHeader`'s "Voltar" button and the new 3-tab workspace pill row — both MUST use `minHeight: "44px"` and, for the pill row specifically, `aria-pressed={ativo === tab.id}` (checked by the analog test's check #10 pattern, and should be re-checked by the new guardian test's assertion 5 above).

### `.manchete` guardrail (CVM) — directory-wide allowlist scan
**Source:** `web/tests/test_opcoes_subabas_ui.mjs` lines 244-273 (`RENDERIZADORES_DE_MANCHETE` allowlist + scan)
**Apply to:** all new/modified files in this phase. Per UI-SPEC's own confirmation, none of the 4 allowlisted manchete-renderers are touched or relocated by this phase, so no allowlist change is needed — but `WorkspaceHeader.jsx` (new file) and the modified `OpcoesScreen.jsx`/`SecaoSetups.jsx` must continue to score 0 matches on `/\.manchete\b/` when the existing directory-wide scan test re-runs (no code change required if the guidance above — WorkspaceHeader renders only `ticker`/copy — is followed).

### Locale-parity for every new `cp.X` key
**Source:** `web/src/copy.js` (two top-level branches `COPY.estudo` / `COPY.operador`), enforced by `web/tests/test_opcoes_subabas_ui.mjs` lines 203-212 (check #9)
**Apply to:** `opcoesVoltarAoHub`, `opcoesAbaAnalisar`, `opcoesAbaComparar`, `opcoesAbaCriarSetup` — each MUST be added to both `COPY.estudo` and `COPY.operador` in the same commit, or the existing guardian test (which already scans `OpcoesScreen.jsx`'s `cp.X` references against both locales) will start failing the moment `OpcoesScreen.jsx` references the new keys, and any new guardian test for `WorkspaceHeader.jsx` should apply the identical check to that file too.

## No Analog Found

None — every file in scope has a strong existing analog in the same directory (`web/src/opcoes/`) or test directory (`web/tests/`), since this phase is an explicit "reorganização pura" over already-established Fase 33 component conventions, not new architecture.

## Metadata

**Analog search scope:** `web/src/opcoes/*.jsx`, `web/src/copy.js`, `web/tests/test_opcoes_*.mjs`
**Files scanned:** `OpcoesScreen.jsx` (full, 868 of 1268 lines read — remainder is `SubAbaOperar`, out of this phase's scope), `SecaoSetups.jsx` (full, 210 lines), `SecaoVigias.jsx` (partial, structural header read), `test_opcoes_subabas_ui.mjs` (full, 279 lines), `copy.js` (targeted grep for existing sibling keys)
**Pattern extraction date:** 2026-09-20
