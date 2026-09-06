# Phase 21: Duplicação removida e Portfólio consolidado - Pattern Map

**Mapped:** 2026-09-05
**Files analyzed:** 2 (`web/src/App.jsx` edited in 4 places, `web/src/copy.js` edited in 1 place)
**Analogs found:** 4 / 4 — this phase edits a single-file monolith (same as Phase 20); every "analog" is a sibling block in the SAME file, already fully specified by `21-UI-SPEC.md` with line numbers verified live on 2026-09-05. This PATTERNS.md re-verifies those line numbers against the current tree (all match, zero drift) and packages the exact excerpts for the planner.

**Note on scope:** unlike a typical multi-file phase, there are no separate "role" files to search for (controller/service/model). All 4 changes are JSX edits inside `App.jsx` components plus one per-mode copy dictionary entry in `copy.js`. The "analog" for each change is the nearest existing sibling pattern already in production in the same file.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `web/src/App.jsx` — Portfólio route (`CarteiraScreen` call site, ~line 9027) | component (route composition) | request-response (render) | `EvolucaoScreen`'s single `<CapitalCurve>` call (line 2029) | exact — literal duplicate being removed |
| `web/src/App.jsx` — 4 separate `kpi()` cards (lines 4358-4363) | component (stat display) | transform (derived display values) | `EvolucaoScreen`'s "RESUMO DO DIA" 3-cell stat block (lines ~1976-1980, `kicker` + value pattern) | exact — spec explicitly names this as the byte-for-byte density reference |
| `web/src/App.jsx` — `AgenteScreen` redundant status card (lines 4765-4802) | component (status/removal + relocation) | request-response (render) | same file's functional hero card immediately below (lines ~4812-4833) — target of redundancy; "ENTRADA AUTOMÁTICA" card (lines 4970-4988) — target of relocation for `entradaAuto.regra`/`.contraste` | exact — both destinations are existing cards in the same screen |
| `web/src/App.jsx` — `CapitalCurve` component (lines 1723-1857) | component (chart + empty-state branching) | transform (data → render branch) | its own existing `!hasSeries` placeholder branch (lines 1850-1854) | exact — new `poucosDias` branch is a sibling of the existing zero-state branch, same component |
| `web/src/copy.js` — new `curvaPoucosDias` key | utility (per-mode copy dictionary entry) | transform (pure function → string) | `saudacao`/`resumoDia` inline arrow-function entries (lines 26-30, mirrored 246-250 in `COPY.operador`) | exact — spec explicitly names this as the pattern to mirror, not `entradaAutoTxt`'s wrapper-function style |

## Pattern Assignments

### 1. `App.jsx` Portfólio route — remove duplicate `<CapitalCurve>` (DEDUP-01)

**Analog:** the surviving instance in `EvolucaoScreen`, `App.jsx:2029` — confirms this is genuinely the LAST line of that component and needs zero change.

**Current state, verified live** (`App.jsx:9027`, single line):
```jsx
: (<><CapitalCurve ctx={ctx} /><CarteiraScreen ctx={ctx} /><div style={{ marginTop: "14px" }}><button onClick={() => setCarteiraView("historico")} style={{ width: "100%", minHeight: "48px", padding: "13px", borderRadius: "13px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "13.5px", display: "flex", alignItems: "center", justifyContent: "space-between" }}><span>Ver histórico de operações</span><span aria-hidden style={{ color: T.textFaint }}>›</span></button></div></>))}
```

**Target:**
```jsx
: (<><CarteiraScreen ctx={ctx} /><div style={{ marginTop: "14px" }}><button onClick={() => setCarteiraView("historico")} style={{ width: "100%", minHeight: "48px", padding: "13px", borderRadius: "13px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "13.5px", display: "flex", alignItems: "center", justifyContent: "space-between" }}><span>Ver histórico de operações</span><span aria-hidden style={{ color: T.textFaint }}>›</span></button></div></>))}
```

Only remove `<CapitalCurve ctx={ctx} />` from this one line; leave everything else on the line untouched. `EvolucaoScreen`'s call (`App.jsx:2029`) is NOT touched.

**Verification:** `grep -n "<CapitalCurve" web/src/App.jsx` returns exactly ONE match after the edit (line ~2029).

---

### 2. `App.jsx` Portfólio KPI cards — consolidate 4→1 (DEDUP-03)

**Analog:** `card` style object (`App.jsx:292`), `kicker` style object (`App.jsx:293`), `numBody`/`numMicro` constants (`App.jsx:257-258`), `MONO` constant (`App.jsx:236`) — all already defined module-level, reused via spread, not redefined.

**Current state, verified live** (`App.jsx:4358-4363`):
```jsx
<div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "12px", margin: "16px 0 18px" }}>
  {kpi("PATRIMÔNIO TOTAL", money(total), T.textPrimary)}
  {kpi("RESULTADO ABERTO", moneySigned(openPnL), openPnL >= 0 ? T.positive : T.negative, pct(openPct), openPnL >= 0 ? T.positive : T.negative)}
  {kpi("CAIXA DISPONÍVEL", money(data.cash), T.textMuted)}
  {kpi("EM POSIÇÕES", money(positionsValue), T.textMuted)}
</div>
```

**`kpi()` helper being removed** (`App.jsx:4340`, first line of a multi-line arrow function — the WHOLE function must go, confirmed by `grep -n "kpi("` returning ONLY the definition at 4340 plus the 4 call sites at 4359-4362, no other consumers anywhere in the file):
```jsx
const kpi = (label, value, color, sub, subColor) => (
  ...
);
```

**Target** (exact code, already fully specified by `21-UI-SPEC.md` Structural Contract):
```jsx
<div style={{ ...card, padding: "16px 18px", margin: "16px 0 18px" }}>
  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px 18px" }}>
    <div>
      <div style={kicker}>PATRIMÔNIO TOTAL</div>
      <div style={{ ...numBody, fontFamily: MONO, color: T.textPrimary }}>{money(total)}</div>
    </div>
    <div>
      <div style={kicker}>RESULTADO ABERTO</div>
      <div style={{ ...numBody, fontFamily: MONO, color: openPnL >= 0 ? T.positive : T.negative }}>{moneySigned(openPnL)}</div>
      <div style={{ ...numMicro, fontFamily: MONO, color: openPnL >= 0 ? T.positive : T.negative }}>{pct(openPct)}</div>
    </div>
    <div>
      <div style={kicker}>CAIXA DISPONÍVEL</div>
      <div style={{ ...numBody, fontFamily: MONO, color: T.textMuted }}>{money(data.cash)}</div>
    </div>
    <div>
      <div style={kicker}>EM POSIÇÕES</div>
      <div style={{ ...numBody, fontFamily: MONO, color: T.textMuted }}>{money(positionsValue)}</div>
    </div>
  </div>
</div>
```

**Style objects referenced** (module-level, do NOT redefine — verified at these lines):
```jsx
// App.jsx:236
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";
// App.jsx:257-258
const numBody = { fontSize: "18px", fontWeight: 700 };
const numMicro = { fontSize: "13px", fontWeight: 600 };
// App.jsx:292-293
const card = { background: T.bgCard, border: `1px solid ${T.borderSubtle}`, borderRadius: "12px" };
const kicker = { fontSize: "10px", color: T.textFaint, letterSpacing: "0.06em" };
```

**Verification:** `grep -n "kpi("` after the edit returns zero matches (helper fully removed, no orphan). Grid renders 4 cells inside 1 `card`-styled container.

---

### 3. `App.jsx` `AgenteScreen` — remove redundant status card, relocate 2 live pieces (DEDUP-02)

**Analog A (removal target's replacement, i.e. why it's redundant):** the functional hero card immediately below (`App.jsx:~4812-4833`, `OPERADOR NO SERVIDOR · 24×5` / `ATIVO`/`INATIVO` with real `Toggle`) already surfaces the same 3 facts (modo, servidor ligado/desligado, executar/sinalizar) actionably.

**Current state to delete, verified live** (`App.jsx:4765-4790`, comment + outer div + status spans + old link position):
```jsx
{/* C-19 (REPORT-01) · D-02 revisado (03-CONTEXT.md): card de status
    único, PRIMEIRO elemento da tela, ANTES de qualquer controle — os
    3 interruptores que decidem se uma ordem dispara: Modo do app,
    Operador no servidor, Executar/sinalizar. Absorve a tira parcial
    que vivia aqui e mostrava só 1 dos 3 (qa/audit-2026-08-07 itens
    3+4, causa raiz registrada de "não me deixa selecionar Executar")
    — card ÚNICO, não duas tiras. Read-only: nenhum badge altera
    estado; a troca acontece só pelo link "Trocar modo →" (Perfil).
    Cada badge lê a MESMA fonte canônica que o card-herói logo abaixo
    usa — nunca contradiz o herói. */}
<div style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "10px 14px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", flexWrap: "wrap" }}>
    <div style={{ display: "flex", alignItems: "center", gap: "14px", flexWrap: "wrap" }}>
      <span style={{ fontSize: "11px", fontWeight: 400, color: T.textSecondary }}>
        Modo do app: <b style={{ color: operador ? T.positive : T.textFaint }}>{operador ? "📈 Operador" : "🎓 Estudo"}</b>
      </span>
      <span style={{ fontSize: "11px", fontWeight: 400, color: T.textSecondary }}>
        Operador no servidor: <b style={{ color: (ag.serverEnabled && logged) ? T.positive : T.textFaint }}>{(ag.serverEnabled && logged) ? "Ligado" : "Desligado"}</b>
      </span>
      <span style={{ fontSize: "11px", fontWeight: 400, color: T.textSecondary }}>
        Executar/sinalizar: <b style={{ color: modoEfetivo === "executar" ? T.positive : T.textFaint }}>{modoEfetivo === "executar" ? "Executar" : "Apenas sinalizar"}</b>
      </span>
    </div>
    <button onClick={() => A.go("perfil")} style={{ background: "transparent", border: "none", padding: 0, color: T.accent, fontWeight: 800, fontSize: "11.5px", textDecoration: "underline", flex: "none" }}>
      Trocar modo →
    </button>
  </div>
```
followed by the `entradaAuto` transparency block and closing div (`App.jsx:4791-4802`):
```jsx
  {/* ADR-017 Bloco 4 (Plano 08-02): a entrada automática deixou de ser
      suspensão cega e virou gate por elegibilidade medida — esta linha
      é a transparência exigida pelo 08-UI-SPEC (aditiva, read-only,
      nenhum toggle novo). O número do contraste é referência FIXA de
      backtest (ADR-016/017), nunca cálculo vivo — os dois números
      moram na MESMA string de copy.js, nunca separados. */}
  <div>
    <div style={{ fontSize: "11px", color: T.textMuted, lineHeight: 1.45 }}>{ctx.cp.entradaAuto.regra}</div>
    <div style={{ fontSize: "11px", color: T.textFaint, lineHeight: 1.45, marginTop: "2px" }}>{ctx.cp.entradaAuto.contraste}</div>
  </div>
</div>
```

**Three separate fates for this deleted block's content:**

1. The comment (4765-4774) + 3 status `<span>` lines (4776-4787) + outer `<div>` chrome (4775, 4791-4802 closing) → **delete entirely**, no replacement needed (redundant with hero card).

2. The `Trocar modo →` `<button>` (4788-4790) → **relocate verbatim** to a new standalone position: after the intro `<p>` closing tag (`App.jsx:~4810`) and before the hero-card comment (`App.jsx:~4812`). Reuse the exact JSX below, only removing the now-unneeded `flex:"none"` (it was flex-item-specific to the row layout being deleted):
```jsx
<button onClick={() => A.go("perfil")} style={{ background: "transparent", border: "none", padding: "8px 0 0", color: T.accent, fontWeight: 800, fontSize: "11.5px", textDecoration: "underline" }}>
  Trocar modo →
</button>
```

3. The `entradaAuto.regra`/`.contraste` two-line block (4798-4801) → **relocate verbatim** into the existing "ENTRADA AUTOMÁTICA" card, inserted right after that card's own intro `<p>` closes (`App.jsx:4977`) and before its `Toggle` row (`App.jsx:4979`):
```jsx
{/* App.jsx:4970-4988, ENTRADA AUTOMÁTICA card — insertion point verified live */}
<div style={{ marginTop: "16px", ...card, padding: "16px 17px" }}>
  <div style={{ fontSize: "10.5px", fontWeight: 800, letterSpacing: "0.06em", color: T.textFaint }}>ENTRADA AUTOMÁTICA</div>
  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "14px", marginTop: "8px" }}>
    <div>
      <div style={{ fontWeight: 700, fontSize: "15px" }}>{ag.entradaAuto && operador ? "Entrar automaticamente" : "Apenas avisar"}</div>
      <p style={{ margin: "4px 0 0", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "440px" }}>
        Quando o gatilho de entrada dispara para um plano de COMPRA da watchlist, decide se a mesa compra sozinha (lote redondo, dentro do teto abaixo) ou só avisa, como hoje.
      </p>
      {/* INSERT HERE, right after </p> and before the Toggle row: */}
      <div>
        <div style={{ fontSize: "11px", color: T.textMuted, lineHeight: 1.45 }}>{ctx.cp.entradaAuto.regra}</div>
        <div style={{ fontSize: "11px", color: T.textFaint, lineHeight: 1.45, marginTop: "2px" }}>{ctx.cp.entradaAuto.contraste}</div>
      </div>
    </div>
    <Toggle on={!!ag.entradaAuto && operador} disabled={!operador} onClick={() => operador && putAg({ entradaAuto: !ag.entradaAuto })} label="Entrar automaticamente" />
  </div>
  ...
```
Note the div ordering: `entradaAuto.regra`/`.contraste` currently sits as a SIBLING to the `<div>` wrapping the title+description (see the deleted block, where it was a sibling of the flex row, not nested inside the text `<div>`), and the target card's `Toggle` sits in a flex row alongside the text `<div>`. The planner should decide whether to nest the transparency lines inside the same text `<div>` (after its `<p>`) or as a new sibling block placed after the whole flex row closes but still "before" the allocation slider section — either reading satisfies "diretamente sob o parágrafo de introdução... antes do Toggle" from the spec; nesting inside the text `<div>` (shown above) keeps it visually grouped under the description text within the same flex column, which matches the existing text-block's own margin/line-height conventions without new wrapper divs.

**Verification (from `21-UI-SPEC.md`, already-specified acceptance checks):**
- `grep -n "entradaAuto.regra\|entradaAuto.contraste" web/src/App.jsx` → exactly one match each (relocated, not duplicated/deleted).
- `grep -n "Trocar modo →" web/src/App.jsx` → exactly ONE match (relocated link). Do not confuse with the separate, untouched `"Trocar para Modo Operador →"` string at `App.jsx:4854` (different string, different guard `{!operador && (...)}`).

---

### 4. `App.jsx` `CapitalCurve` — add "poucos dias" placeholder branch (FIX-03)

**Analog:** the component's own existing zero-points placeholder (`App.jsx:1850-1854`) — the new branch is a sibling `else-if`, same wrapper style, same conditional position in the ternary.

**Current state, verified live:**

Destructure (`App.jsx:1729`):
```jsx
const { data, quotes } = ctx;
```
→ becomes:
```jsx
const { data, quotes, cp } = ctx;
```

Threshold flag (`App.jsx:1736`):
```jsx
const hasSeries = ec.days >= 1;          // mostra a curva a partir do 1º dia (baseline = orçamento)
```
→ becomes (add a second flag, keep `hasSeries` semantics but raise its threshold to 3 per spec — verify exact wording the planner chooses matches `ec.days >= 3`):
```jsx
const hasSeries = ec.days >= 3;
const poucosDias = ec.days >= 1 && ec.days < 3;
```

Render branch (`App.jsx:1836-1854`, current 2-way ternary):
```jsx
{hasSeries ? (
  <>
    <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
      {stat("RETORNO ACUMULADO", pct(retAcum), retAcum >= 0 ? T.positive : T.negative)}
      {stat("DRAWDOWN (DESDE O PICO)", "-" + dd.toFixed(1) + "%", T.negative)}
      {stat("DIAS REGISTRADOS", String(ec.days))}
      {diffIbov != null && stat("VS. IBOVESPA", pct(diffIbov), diffIbov >= 0 ? T.positive : T.negative)}
    </div>
    {(ibovErro || (ibov && !temIbov)) && (
      <div style={{ fontSize: "11px", color: T.textFaint, marginTop: "8px", lineHeight: 1.4 }}>
        Comparação com o Ibovespa indisponível agora.
      </div>
    )}
  </>
) : (
  <div style={{ fontSize: "11.5px", color: T.textFaint, marginTop: "10px", lineHeight: 1.5 }}>
    Sua curva começa amanhã. Volte para vê-la crescer — cada dia que você abrir o app vira um ponto aqui.
  </div>
)}
```
→ becomes a 3-way ternary, new branch inserted between the two existing ones, reusing the exact same wrapper style object as the existing zero-state placeholder:
```jsx
{hasSeries ? (
  <>{/* unchanged block above */}</>
) : poucosDias ? (
  <div style={{ fontSize: "11.5px", color: T.textFaint, marginTop: "10px", lineHeight: 1.5 }}>
    {cp.curvaPoucosDias(ec.days)}
  </div>
) : (
  <div style={{ fontSize: "11.5px", color: T.textFaint, marginTop: "10px", lineHeight: 1.5 }}>
    Sua curva começa amanhã. Volte para vê-la crescer — cada dia que você abrir o app vira um ponto aqui.
  </div>
)}
```

**SVG placeholder (`App.jsx:1816-1834`) — no change needed.** Both `poucosDias` and `!hasSeries` fall into the `hasSeries === false` branch of the SVG's own ternary (`App.jsx:1825-1833`), so the dashed "no-data-yet" squiggle already renders for both — do not touch the SVG block.

**`ibov` fetch `useEffect` (`App.jsx:1750-1758`) — no change needed.** Already keys off `hasSeries`, so raising `hasSeries`'s threshold to 3 automatically delays the Ibovespa fetch until day 3, which is the correct side effect.

**Verification:** with `ec.days === 1` or `2`, the component renders `cp.curvaPoucosDias(ec.days)` text, no SVG curve, no Ibovespa fetch. With `ec.days === 0`, unchanged zero-state copy. With `ec.days >= 3`, unchanged curve rendering.

---

### 5. `copy.js` — new `curvaPoucosDias` key (both modes)

**Analog:** `saudacao`/`resumoDia` inline arrow-function pattern (`copy.js:26-30` for `COPY.estudo`, mirrored `copy.js:246-250` for `COPY.operador`) — plain per-mode function, NOT the `entradaAutoTxt`-style external wrapper (`copy.js:449`, which branches on extra `estado`/`vals` params this text doesn't need).

**Imports pattern** (`copy.js:15-16`, module-level, no new import needed for this key):
```js
import { DISCLAIMERS } from "./disclaimers.js";
import { RR_MIN_TXT } from "./finance.js"; // ADR-015 (06-05): fonte única do R:R mínimo
```

**Core pattern to copy** (`copy.js:26-30`, `COPY.estudo`):
```js
saudacao: (nome) => (nome ? `Vamos estudar o mercado hoje, ${nome}?` : "Vamos estudar o mercado hoje?"),
resumoDia: (nSetups, nGatilhos) =>
  nSetups > 0
    ? `Há ${nSetups} setup(s) para estudar na sua watchlist — bora entender o porquê de cada um?`
    : "Mercado sem setups claros na sua watchlist — bom dia para revisar os conceitos.",
```

**New key to add, identical in both `COPY.estudo` and `COPY.operador`** (per `21-UI-SPEC.md` Copywriting Contract — same tone both modes, factual not decision-framing text):
```js
curvaPoucosDias: (dias) =>
  dias === 1
    ? "Só 1 dia registrado ainda — a curva aparece a partir do 3º dia."
    : "Só 2 dias registrados ainda — a curva aparece a partir do 3º dia.",
```

**Guardian constraint** (`copy.js` header comment, line 12, and enforced by `web/tests/test_copy_theme.mjs:27`):
```js
const e = Object.keys(COPY.estudo).sort(), o = Object.keys(COPY.operador).sort();
```
This test asserts the key SETS of `COPY.estudo`/`COPY.operador` match — `curvaPoucosDias` MUST be added to both dictionaries in the same commit or `test_copy_theme.mjs` fails. This is the single most important shared-pattern constraint for this phase's `copy.js` edit.

---

## Shared Patterns

### Inline style objects, never CSS-in-JS or classNames
**Source:** whole file convention, confirmed at `card` (`App.jsx:292`), `kicker` (`App.jsx:293`), `numBody`/`numMicro`/`numHero` (`App.jsx:256-258`), `MONO` (`App.jsx:236`)
**Apply to:** all 4 `App.jsx` change sites. Always spread shared objects (`{...card, padding: "..."}`), never redefine inline. This project has zero CSS Modules/Tailwind (confirmed in `21-UI-SPEC.md` Design System table and `CLAUDE.md`'s frontend conventions).

### Per-mode copy dictionary, never hardcoded strings
**Source:** `copy.js:11-14` (file header convention), enforced by `web/tests/test_copy_theme.mjs`
**Apply to:** change #4 (`CapitalCurve`'s new placeholder text) and change #5 (`copy.js`). Any user-facing string that could plausibly differ or that is added net-new to a screen already served by `cp.*` must go through `copy.js`, added to BOTH `COPY.estudo` and `COPY.operador` with identical key names (content can differ or be identical, but the key must exist in both — guardian test enforces the key-set, not the values).

### Comments carry decision history — don't delete code without its comment
**Source:** `App.jsx:4765-4774` (the `C-19 (REPORT-01) · D-02 revisado` comment being removed alongside its code in change #3), general convention stated in `CLAUDE.md` ("Comments — carry decision history, not restatement")
**Apply to:** change #3 specifically — the spec is explicit that deleting the 3-line status block without its explanatory comment block would leave a stale description of removed code. When removing this pattern's source block, remove the comment with it; when relocating code (the `Trocar modo →` button, the `entradaAuto` transparency lines), the comments that describe the DESTINATION context (e.g. the `ADR-017 Bloco 4` comment at `App.jsx:4791-4796`) should travel WITH the relocated code if still accurate, since it documents the `entradaAuto.regra`/`.contraste` content itself, not the removed card's layout.

### `ctx.cp` is already the resolved per-mode dictionary
**Source:** `App.jsx:8760` (ctx object construction, confirmed by spec), `App.jsx:7712` (`copyFor(appMode)` resolution, confirmed by spec)
**Apply to:** change #4 — `CapitalCurve` just needs to destructure `cp` from `ctx`; no `copyFor()` call needed inside the component, it's already resolved upstream.

## No Analog Found

None. All 4 `App.jsx` change sites and the 1 `copy.js` change site have exact, already-verified analogs within the same files — this is a pure removal/consolidation phase inside a single-file monolith with byte-exact reference patterns already identified by `21-UI-SPEC.md`.

## Metadata

**Analog search scope:** `web/src/App.jsx` (single file, ~9000+ lines), `web/src/copy.js`, `web/tests/test_copy_theme.mjs` (guardian test reference only, not modified)
**Files scanned:** 3 (`App.jsx`, `copy.js`, `test_copy_theme.mjs`)
**Pattern extraction date:** 2026-09-05
**Line-number verification:** every line number cited above was re-verified live via `grep -n`/`Read` against the current working tree on 2026-09-05, matching `21-UI-SPEC.md`'s own live-verified numbers exactly (zero drift found between spec authoring and this pattern-mapping pass).
