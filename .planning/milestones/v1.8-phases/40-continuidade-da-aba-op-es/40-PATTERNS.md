# Phase 40: Continuidade da aba Opções - Pattern Map

**Mapped:** 2026-09-25
**Files analyzed:** 3 (2 modified, 1 new test)
**Analogs found:** 3 / 3 (all in-repo, no external pattern needed)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|-----------------|---------------|
| `web/src/App.jsx` (add `opcoesMemoria` state + ctx wiring + `_resetScopeState` entry) | provider (lifted state / context root) | event-driven (state lifted to survive child unmount, written by child callbacks) | `web/src/App.jsx:7675` + `App.jsx:8973-8979` (`opcoesAbaInicial` lifted-state pattern) | exact — same file, same technique, same author decision (D-01 says "literally copy this shape") |
| `web/src/opcoes/OpcoesScreen.jsx` (lazy `useState` initializers for `ticker`/`abaOpcoes` reading `ctx.opcoesMemoria`, write-back on change, precedence gate) | component (screen, reads/writes lifted ctx state) | request-response / local UI state (no I/O) | `web/src/opcoes/OpcoesScreen.jsx:311-324` (existing `abaOpcoes` lazy-init + one-shot consume pattern) | exact — same component, same hook shape |
| `web/tests/test_40_opcoes_continuidade_ui.mjs` (new, name suggested — planner may rename `40-*`/`test_opcoes_continuidade_ui.mjs` to match existing convention) | test (static/structural guardian, no DOM/build) | transform (regex/string assertions over raw source) | `web/tests/test_opcoes_nav_tres_abas_ui.mjs` (whole file — technique, structure, `semComentario` helper) | exact — same technique family as every `*_ui.mjs` guardian in `web/tests/` |

## Pattern Assignments

### `web/src/App.jsx` (provider, event-driven lifted state)

**Analog:** same file, `opcoesAbaInicial` pattern (lines 7672-7675, 8969-8979) — this is the pattern D-01 explicitly says to copy, not invent.

**Declaration pattern** (`App.jsx:7672-7675`):
```javascript
// Fase 39 (NAV-01): pedido one-shot de aba inicial da tela Opções —
// consumido e limpo pelo OpcoesScreen no mount; não é persistência (isso é
// a Fase 40, ESTADO-01).
const [opcoesAbaInicial, setOpcoesAbaInicial] = useState(null);
```
New state follows the same shape, declared near it (same "Opções lifted state" cluster):
```javascript
// Fase 40 (ESTADO-01, D-01): memória em sessão do ticker + aba ativa da aba
// Opções — sobrevive ao unmount/remount de OpcoesScreen (App.jsx:9279) mas
// NÃO entra em deviceStore/serverStore (evita o guardrail de paridade dos
// dois stores por um requirement que não pediu persistência entre reloads).
const [opcoesMemoria, setOpcoesMemoria] = useState(null); // { ticker, aba } | null
```

**ctx wiring pattern** (`App.jsx:8969-8979`):
```javascript
// Fase 32 (32-02), D-03: PONTO ÚNICO de entrada na aba Opções a partir de
// outra tela — mesma razão registrada em goAgente acima. `navigate` já
// zera carteiraView/perfilView, então este destino chega sempre limpo.
// Fase 39 (NAV-01): `aba` é opcional — sem argumento, comportamento
// idêntico ao de hoje. Com string, grava em `opcoesAbaInicial` o pedido
// one-shot que o OpcoesScreen (Plano 04) consome no mount; a validação
// contra as 3 abas válidas é do próprio OpcoesScreen, que ignora valor
// desconhecido.
goOpcoes: (aba) => { if (typeof aba === "string") setOpcoesAbaInicial(aba); navigate("opcoes"); },
opcoesAbaInicial,
limparOpcoesAbaInicial: () => setOpcoesAbaInicial(null),
```
New ctx keys, same shape — a value plus a single setter callback that `OpcoesScreen` calls on change (NOT a "clear" one-shot like `limparOpcoesAbaInicial`, since this state is written continuously, not consumed-once):
```javascript
opcoesMemoria,
// Fase 40 (ESTADO-01): OpcoesScreen chama isto a cada mudança de
// ticker/abaOpcoes (ver OpcoesScreen.jsx) — grava { ticker, aba } em
// memória no pai que nunca desmonta. Espelha a forma de
// setOpcoesAbaInicial/limparOpcoesAbaInicial acima, mas grava em toda
// mudança em vez de consumir uma vez.
setOpcoesMemoria: (m) => setOpcoesMemoria(m),
```

**`_resetScopeState` pattern — MANDATORY inclusion** (`App.jsx:8900-8906`):
```javascript
// FASE 8 (A3): fonte única do reset de estados derivados na TROCA de escopo
// (login/logout/exclusão) — evita vazar análises/cotações entre contas.
const _resetScopeState = () => {
  setAnalysis({}); setExpanded({}); setQuotes({}); setWlScan(null); setDestaque({ stage: "idle" });
  _proativoDono.t = null;   // conta nova recomeça elegível à via proativa
  notifRef.current = {};
};
```
D-04/SC#4 requires adding `setOpcoesMemoria(null);` to this exact function body — this is the ONLY place that needs a new line for the reset requirement; all 5 call sites (`login` `App.jsx:9032`, `register` `9041`, `oauth` `9052`, `logout` `9068`, `deleteAccount` `9079`) get the fix for free by calling `_resetScopeState()`, which they already do. Per UI-SPEC scenario C2, `_resetScopeState()` alone is not sufficient for the 3 call sites that don't change `tab` (login/register/oauth) while `OpcoesScreen` may still be mounted — planner must also address remount/revalidation of the already-mounted screen (UI-SPEC suggests a scope `key` on `<OpcoesScreen>` or revalidating `ticker` against `positions` outside the mount initializer).

**Render call site to modify for a scope-remount key (if that's the chosen C2 mechanism)** (`App.jsx:9279`):
```javascript
{tab === "opcoes" && <OpcoesScreen ctx={ctx} />}
```

---

### `web/src/opcoes/OpcoesScreen.jsx` (component, local state initializers)

**Analog:** same file, existing `abaOpcoes` lazy-init + one-shot consume (lines 311-324).

**Imports pattern** (`OpcoesScreen.jsx:31`, already present, no new import needed for state logic):
```javascript
import { useState, useEffect } from "react";
```

**Existing state + precedence pattern to extend** (`OpcoesScreen.jsx:284, 311-324`):
```javascript
const ABAS_OPCOES = ["oportunidades", "recomendadas", "montar"];

export default function OpcoesScreen({ ctx }) {
  ...
  const [ticker, setTicker] = useState("");
  const [abaOpcoes, setAbaOpcoes] = useState(() => (ctx && ABAS_OPCOES.includes(ctx.opcoesAbaInicial)) ? ctx.opcoesAbaInicial : "oportunidades");
  useEffect(() => {
    if (ctx && ctx.opcoesAbaInicial && ctx.limparOpcoesAbaInicial) ctx.limparOpcoesAbaInicial();
  }, []);
```

**Required shape of the new code** (per D-03 precedence + UI-SPEC "Ordem de precedência"):
1. `ticker` initializer must add `opcoesMemoria.ticker` as fallback #1 when `opcoesAbaInicial` deep-link doesn't touch ticker (P-1) — but MUST validate against `carteira`/`ctx.data.positions` (P-2), never accept blindly (cenário E: sold-out ticker falls back to `""`).
2. `abaOpcoes` initializer must check `ctx.opcoesAbaInicial` FIRST (unchanged precedence, D-03 "sempre vence"), THEN `ctx.opcoesMemoria && ABAS_OPCOES.includes(ctx.opcoesMemoria.aba)`, THEN default `"oportunidades"` — same `useState(() => ...)` lazy form, no `useEffect` (UI-SPEC "Sem salto perceptível" forbids the render-then-effect pattern explicitly).
3. Restoring the ticker must NOT go through `escolherTicker` (`OpcoesScreen.jsx:383-387`, shown below) because it is a toggle and it resets `tese`/`vencimento`/`alvo`/`stop`/`compararAberto` — it is for the click handler, not for initial value:
```javascript
const escolherTicker = (t) => {
  setTicker(t === ticker ? "" : t);
  setTese(""); setVencimento(""); setAlvo(""); setStop("");
  setCompararAberto(false);
};
```
4. Write-back: every place that changes `ticker` (`escolherTicker`, `irParaMontar`) or `abaOpcoes` (`setAbaOpcoes(a.id)` at the tab-bar click, `irParaMontar`'s `setAbaOpcoes("montar")`) needs the corresponding call to `ctx.setOpcoesMemoria({ ticker, aba: abaOpcoes })` (post-update values) OR a single `useEffect([ticker, abaOpcoes])` that syncs to ctx on every change — UI-SPEC leaves the exact wiring to the planner but explicitly forbids relying only on unmount-cleanup (cenário C: scope change with tab open must not let the outgoing unmount re-write the previous account's state after `_resetScopeState()` already cleared it).

**One-shot consume — keep the existing form, do not touch** (`OpcoesScreen.jsx:322-324`):
```javascript
useEffect(() => {
  if (ctx && ctx.opcoesAbaInicial && ctx.limparOpcoesAbaInicial) ctx.limparOpcoesAbaInicial();
}, []);
```

---

### `web/tests/test_40_opcoes_continuidade_ui.mjs` (new guardian, static source-assertions)

**Analog:** `web/tests/test_opcoes_nav_tres_abas_ui.mjs` (full file, 262 lines) — same "read raw source, strip comments, regex-assert structure" technique used across every `*_ui.mjs` guardian in `web/tests/`.

**Imports/setup pattern** (lines 62-68):
```javascript
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");

const opcoesScreenBruto = readFileSync(join(dirOpcoes, "OpcoesScreen.jsx"), "utf8");
```
For this phase, also read `App.jsx` raw source the same way:
```javascript
const appBruto = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
```

**Comment-stripping helper — reuse verbatim** (lines 74-82), needed because doc-comments in this very file (and in App.jsx/OpcoesScreen.jsx) will mention the tokens being asserted:
```javascript
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

const opcoesScreen = semComentario(opcoesScreenBruto);
```

**Assertion style — `ok()` counter + line/index slicing** (lines 84-97, 109-126):
```javascript
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

ok("OpcoesScreen.jsx foi lido e tem corpo (>1000 caracteres)",
   opcoesScreenBruto.length > 1000);

ok("abaOpcoes nasce validado contra ABAS_OPCOES.includes(ctx.opcoesAbaInicial), senão \"oportunidades\"",
   /useState\(\(\) => \(ctx && ABAS_OPCOES\.includes\(ctx\.opcoesAbaInicial\)\) \? ctx\.opcoesAbaInicial : "oportunidades"\)/.test(opcoesScreenBruto));
```

**Slicing between two source markers to isolate a function body — reuse for isolating the new `useState` initializers and the "no useEffect writing ticker/abaOpcoes from memory" check** (pattern from lines 110-114, 202-216):
```javascript
const iAbaBarConst = opcoesScreen.indexOf("const abaBar = (");
const iAbaBarFimConst = iAbaBarConst >= 0 ? opcoesScreen.indexOf("\n  );", iAbaBarConst) : -1;
const corpoAbaBar = (iAbaBarConst >= 0 && iAbaBarFimConst > iAbaBarConst)
  ? opcoesScreen.slice(iAbaBarConst, iAbaBarFimConst) : "";
```
For this phase's D-05 acceptance criterion ("no `useEffect` feeds `setAbaOpcoes`/`setTicker` from memory" — UI-SPEC line ~140-143), the new guardian should isolate every `useEffect(` block in `opcoesScreen` and assert none of them contain `setTicker(` or `setAbaOpcoes(` sourced from `opcoesMemoria`/`ctx.opcoesMemoria`, e.g.:
```javascript
const blocosUseEffect = opcoesScreen.match(/useEffect\(\(\) => \{[\s\S]*?\}, \[[^\]]*\]\);/g) || [];
ok("nenhum useEffect grava ticker/abaOpcoes a partir de opcoesMemoria (D-05: sem salto pós-paint)",
   blocosUseEffect.every((b) => !(/opcoesMemoria/.test(b) && (/setTicker\(/.test(b) || /setAbaOpcoes\(/.test(b)))));
```

**Exit code / summary pattern — reuse verbatim** (lines 258-261):
```javascript
console.log(fails === 0 ? "TODOS OS " + "TESTES PASSARAM" : fails + " FALHA(S)");
if (fails > 0) {
  process.exit(1);
}
```

**Additional assertions this guardian must include** (derived from UI-SPEC cenários, not from an analog — no existing test covers scope-reset of Opções state):
- `_resetScopeState` body (isolate via `const iReset = appBruto.indexOf("const _resetScopeState = ()")` then slice to the closing `};`) contains a call that clears `opcoesMemoria` (e.g. `setOpcoesMemoria(null)`).
- `opcoesMemoria` (or the chosen name) is declared with `useState` in `App.jsx`, NOT read/written through `store.*`/`deviceStore`/`serverStore` (grep both raw files for the chosen state name near `store.` calls — must be absent, confirming D-01's "stays out of persistence" decision).
- Ticker restoration path in `OpcoesScreen.jsx` does not call `escolherTicker(` inside the initial `useState(() => ...)` (regex the initializer body specifically, not the whole file, since `escolherTicker` legitimately exists elsewhere for clicks).

## Shared Patterns

### Lifted one-shot vs. continuous state in App.jsx → ctx → OpcoesScreen
**Source:** `App.jsx:7672-7675` + `8969-8979`, consumed by `OpcoesScreen.jsx:311-324`
**Apply to:** both `App.jsx` and `OpcoesScreen.jsx` changes.
The existing `opcoesAbaInicial` mechanism is "write once from a deep-link, read once at mount, clear immediately" (one-shot). The new `opcoesMemoria` mechanism is "write on every change, read once at mount, never auto-clear except on scope reset" (continuous echo). Do not merge the two mechanisms or reuse `limparOpcoesAbaInicial`'s one-shot-clear shape for the new state — they have different lifecycles by design (D-03 requires the deep-link to always win over memory, which only works if they stay independent state slots).

### Scope-reset invariant (`_resetScopeState`)
**Source:** `App.jsx:8900-8906`, called at `App.jsx:9032, 9041, 9052, 9068, 9079`
**Apply to:** `App.jsx` (add the clear line) — this is the SC#4/D-04 guardrail; the planner must not introduce a second, parallel reset path.

### Static structural guardian technique (no DOM, no build, no bundler)
**Source:** every `web/tests/*_ui.mjs` file, exemplified by `web/tests/test_opcoes_nav_tres_abas_ui.mjs`
**Apply to:** the new test file — run via `node web/tests/test_40_opcoes_continuidade_ui.mjs`, wired into `scripts/executar.sh --testes` automatically (it globs `web/tests/*.mjs`, no manual registration needed — confirm by checking `scripts/executar.sh` if in doubt, not assumed here since it's out of this pattern-mapping scope).

## No Analog Found

None — all three files have a strong, exact-match analog already in the same source files (App.jsx's own `opcoesAbaInicial` pattern, OpcoesScreen.jsx's own lazy-init pattern, and the `web/tests/*_ui.mjs` family for the guardian). This phase is explicitly designed by D-01 to copy existing in-file patterns rather than introduce new mechanisms.

## Metadata

**Analog search scope:** `web/src/App.jsx`, `web/src/opcoes/OpcoesScreen.jsx`, `web/tests/*opcoes*.mjs` (24 files listed, 1 read in full as representative analog)
**Files scanned:** 2 source files (targeted grep + offset reads) + 1 test file (full read) + 24 test filenames (listed only)
**Pattern extraction date:** 2026-09-25
