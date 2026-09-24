# Phase 39: Reestruturação de navegação da aba Opções - Pattern Map

**Mapped:** 2026-09-24
**Files analyzed:** 14 (frontend 11, backend 3) — 12 no mapeamento original + 2 wrappers novos do Plano 39-04 (`AbaOportunidades.jsx`/`AbaRecomendadas.jsx`) acrescentados na revisão do checker
**Analogs found:** 14 / 14 (all files being modified are their own best analog — this phase restructures existing components in place; the only genuinely new surface, `VigiasBadge`/`VigiasSheet`, has a direct analog in the existing `ConceitoSheet`/`saiba mais` pattern)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `web/src/opcoes/OpcoesScreen.jsx` | controller/orchestrator (React, no import from `App.jsx`, ADR-027) | request-response (state → conditional render) | itself, prior fases (28/34) that introduced `subaba`/`abaWorkspace` | exact (same file, replacing its own pattern) |
| `web/src/opcoes/OportunidadesOpcoes.jsx` | component (presentational, cross-position carousel) | CRUD-read / request-response | `CuradoriaEstruturas.jsx` (sibling cross-position block) | exact |
| `web/src/opcoes/AbaOportunidades.jsx` (new, Plano 39-04) | component (thin tab wrapper: frescor stamp + cross-position carousel, no data hook) | request-response (props in → render; no fetch, no sort/filter) | `web/src/opcoes/SecaoDescobrir.jsx` (Fase 33) — the file it is partitioned out of: `chaveComparavel` + `frescorAgregadoOportunidades` (`SecaoDescobrir.jsx:59-113`) move VERBATIM, then `<CarimboFrescor>` + `<OportunidadesOpcoes>` | exact — same code, split by motor (motor COM gate); `SecaoDescobrir.jsx` is deleted after the split |
| `web/src/opcoes/AbaRecomendadas.jsx` (new, Plano 39-04) | component (thin tab wrapper: frescor stamp + curadoria block with inline execution) | request-response (props in → render; `curadoria.top/meta` by reference, no reordering — REORG-07) | `web/src/opcoes/SecaoDescobrir.jsx` (Fase 33) — the `CuradoriaEstruturas` prop mapping (`SecaoDescobrir.jsx:152-168`) moves VERBATIM, plus `infoBotao` | exact — same code, split by motor (motor SEM gate); becomes the only mount point of `<CuradoriaEstruturas` in `web/src/opcoes/` |
| `web/src/opcoes/CuradoriaEstruturas.jsx` | component (presentational + inline execution) | CRUD (read ranking, write execution) | itself — is the canonical execution-inline pattern D-05 says to reuse | exact |
| `web/src/opcoes/SecaoAnalisar.jsx` | component (form + payoff + execute) | CRUD (write structure, execute) | `ExecutarProposta.jsx` (already embedded inside it) | exact — unchanged internally, only its mount point moves |
| `web/src/opcoes/SecaoComparar.jsx` | component (read-only comparison, sub-action) | request-response (read) | `SecaoAnalisar.jsx` (shares `tese`/`lote` contract) | exact — unchanged props, only becomes inline/collapsible instead of a pill-routed screen |
| `web/src/opcoes/SecaoSetups.jsx` | component (list + create, CRUD) | CRUD | itself — unchanged; only its parent slot changes | exact |
| `web/src/opcoes/SecaoVigias.jsx` | component (list + poll-refresh) | CRUD-read + action | itself — unchanged; new consumer is a sheet instead of hub-always-visible block | exact |
| `VigiasBadge` + `VigiasSheet` (new, likely inline in `OpcoesScreen.jsx` or a new small module in `web/src/opcoes/`) | component (icon button + bottom sheet) | request-response (open/close, no fetch) | `ConceitoSheet` (`web/src/entendimento.jsx:180-206`) for the sheet shell; `BOTAO` const (`OpcoesScreen.jsx:140-144`) for the badge button | role-match (sheet shell exact; badge is a compact `BOTAO` variant) |
| ⓘ contextual per tab (reuses existing `ConceitoSheet`/`verbeteAberto`) | component (icon button opening existing sheet) | request-response | `OpcoesScreen.jsx:793-798` (current fixed "saiba mais" link) | exact — same mechanism, 3 mount points instead of 1 |
| `web/src/copy.js` | config/i18n dictionary | CRUD (static key-value) | itself — add/retire keys per Copywriting Contract | exact |
| `server/app/opcoes_curadoria.py` (`rankear`, `candidatos_da_posicao`) | service (pure calculation, no I/O) | transform/batch | itself — extend `razao`-based sort with admission floor + new sort key | exact |
| `server/app/options_quant.py` (`black_scholes`) | utility (pure math) | transform | itself — already implemented, only needs a new call site | exact (no change needed to this file, just consumed) |

---

## Pattern Assignments

### `web/src/opcoes/OpcoesScreen.jsx` — navigation state model

**Analog:** itself, current `subaba`/`abaWorkspace` pair (to be replaced by a single `abaOpcoes` state)

**Current state declarations** (lines 285-297):
```javascript
const [ticker, setTicker] = useState("");
const [subaba, setSubaba] = useState("setups");
const [abaWorkspace, setAbaWorkspace] = useState("analisar");
```
→ Replace `subaba`+`abaWorkspace` with the UI-SPEC's single state (UI-SPEC line 61):
```javascript
const [abaOpcoes, setAbaOpcoes] = useState("oportunidades");
// "oportunidades" | "recomendadas" | "montar"
```
`ticker`/`escolherTicker` (lines 285, 344-347) stay untouched — they now govern only content inside "Montar", not which tab-set renders.

**Navigation helper pattern** (lines 354, 363) — `irParaVigia`/`irParaOperar` show the established guard-against-toggle-close idiom:
```javascript
const irParaVigia = (t) => { if (t && t !== ticker) escolherTicker(t); };
const irParaOperar = (t) => { if (t && t !== ticker) escolherTicker(t); setSubaba("operar"); };
```
New destinations copy this exact shape, only swapping the second statement:
```javascript
// D-05/D-07/Leitura A do fork: qualquer navegação que leve a "trabalhar com
// este ticker" agora aponta para Montar.
const irParaMontar = (t) => { if (t && t !== ticker) escolherTicker(t); setAbaOpcoes("montar"); };
```
Used by: Vigias sheet `onIr`, and by `OportunidadesOpcoes`'s `onAbrir` (replacing `irParaOperar`, UI-SPEC "Fork... Leitura A").

**Pill-row visual pattern to copy verbatim** (lines 657-701, `subabas`/`workspacePillRow`) — this is the literal template for the new 3-item `abaBar`:
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
New `abaBar` (UI-SPEC lines 92-99) is this same block with the 3-item array (`opcoesAbaOportunidades`/`opcoesAbaRecomendadas`/`opcoesAbaMontar`) and `setAbaOpcoes` in place of `setSubaba`/`setAbaWorkspace`. **No new style value** — copy the object literal byte-for-byte, change only the data array and the state setter/getter names.

**`cabecalho` relocation** (lines 464-520) — content and styling untouched, only its mount point moves from "always visible above hub/workspace split" to "only inside AbaMontar, only when ticker is set" (same guard already used for `LastroDoAtivo`/`LeituraInterna` at lines 744-745).

**D-14 relocation of `cp.opcoesCustoFrescor`** (line 516-518) — the paragraph:
```javascript
<div style={{ marginTop: "8px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.5 }}>
  {cp.opcoesCustoFrescor || ""}
</div>
```
moves out of the fixed `cabecalho` render and becomes body content of the Montar-tab ⓘ sheet (`ConceitoSheet` content prop or equivalent) — same string, same key, different container.

**Existing "saiba mais" mechanism to replicate 3×** (lines 793-798):
```javascript
{ctx && ctx.didatica && ctx.didatica.ligada && verbeteDoCatalogo(ctx.kbCatalogo, ANCORAS_KB.opcoes) && (
  <button type="button" onClick={() => setVerbeteAberto({ cid: ANCORAS_KB.opcoes, trilha: [] })} style={{ background: "transparent", border: "none", padding: 0, marginTop: "6px", color: T.accent, fontWeight: 700, fontSize: "12px", textDecoration: "none" }}>{cp.saibaMais || "saiba mais"}</button>
)}
```
Move this button (unchanged `verbeteAberto`/`ANCORAS_KB.opcoes` wiring — UI-SPEC recommends `mkt-opcao` for all 3 tabs, not diversified) inside each of the 3 tab bodies, next to that tab's own eyebrow/kicker instead of the screen-level `<h1>`.

**`SubAbaOperar` dissolution** (lines 801-1044, definition at 1090-1222) — this whole component and its render branch are removed; its execution-inline responsibility is absorbed by `CuradoriaEstruturas.jsx`'s existing `handleExecutar` pattern (already in production, see below), per D-05.

---

### `web/src/opcoes/CuradoriaEstruturas.jsx` (component, CRUD — the reference execution-inline pattern)

**Analog:** itself (this file IS the pattern D-05 designates for reuse; no external analog needed)

**Imports** (lines 28-32):
```javascript
import { useState } from "react";
import PayoffChart from "./PayoffChart.jsx";
import { estruturaParaPayoff } from "./estruturaParaPayoff.js";
```

**Execution-inline core pattern** (lines 91-129) — `abertoId`/`execucao`/`liquidezOk` state + `handleExecutar`, the exact shape any new "execute a proposed structure" surface should copy:
```javascript
const [abertoId, setAbertoId] = useState(null);
const [execucao, setExecucao] = useState({}); // {[id]: {busy, erro, ok}}
const [liquidezOk, setLiquidezOk] = useState({}); // {[id]: true}
...
const handleExecutar = async () => {
  if (!item || !idAberto) return;
  setExecucao((s) => ({ ...s, [idAberto]: { busy: true, erro: null, ok: false } }));
  try {
    await onExecutar(item, { aceitaLiquidezDificil: !!liquidezOk[idAberto] });
    setExecucao((s) => ({ ...s, [idAberto]: { busy: false, erro: null, ok: true } }));
    if (onRecarregar) onRecarregar();
  } catch (e) {
    setExecucao((s) => ({ ...s, [idAberto]: { busy: false, erro: (e && e.message) || String(e), ok: false } }));
  }
};
```

**Error handling pattern** (lines 253-257, 306-319) — error is rendered as state (not thrown), verbatim `e.message`, no retry auto-trigger; distinct visual for "search failed" (`T.warn` block with retry CTA) vs. "search succeeded, nothing qualifies" (`T.textSecondary` block, no CTA) vs. "not yet measured" (folded into loading). This 3-way (soon 4-way, D-11) precedence cascade is the pattern to extend for the new `curadoriaVazioPiso` state:
```javascript
{top.length === 0 && naoMedido && ( /* loading */ )}
{top.length === 0 && !naoMedido && erro && ( /* T.warn block + retry button */ )}
{top.length === 0 && !naoMedido && !erro && ( /* T.textSecondary block, curadoriaVazio */ )}
```
New 4th state (D-11) inserts between the `erro` branch and the generic-vazio branch: `top.length === 0 && !naoMedido && !erro && pisoFiltrouTudo` → `curadoriaVazioPiso` (also `T.textSecondary`, not `T.warn` — UI-SPEC color rule).

**D-14 removal target** (line 194):
```javascript
<div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "6px" }}>{cp.curadoriaRazaoRotulo}: {cand.razao != null ? cand.razao.toFixed(2) : "—"}</div>
```
This line is deleted; `cand.posicaoNoRanking` already renders in the card eyebrow (line 184) and per UI-SPEC gets reinforced with a `"1ª de N"` phrase (new `curadoriaPosicaoRotulo` key) in the expanded panel where this line's space frees up.

**Color debt to fix as part of this phase** (line 268) — `color: "#fff"` literal on the Executar button must become `color: T.onAccent`:
```javascript
// current (line 268):
style={{ marginTop: "10px", minHeight: "44px", width: "100%", padding: "10px", borderRadius: "10px", border: "none", background: T.accent, color: "#fff", fontWeight: 700, fontSize: "13px", opacity: executarTravado ? 0.55 : 1, cursor: executarTravado ? "default" : "pointer" }}
```
Correct token already established elsewhere in the same directory — `OpcoesScreen.jsx:155-159` (`BOTAO_PRIMARIO`):
```javascript
const BOTAO_PRIMARIO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: "none", background: T.accent, color: T.onAccent,
  fontWeight: 700, fontSize: "13px",
};
```

---

### `web/src/opcoes/OportunidadesOpcoes.jsx` (component, request-response, cross-position)

**Analog:** `CuradoriaEstruturas.jsx` (sibling block, same directory, same "espelho declarado" token pattern)

**Imports / token mirror pattern** (lines 23-25, exact convention to preserve — this module cannot import from `App.jsx`, ADR-027 Emenda 3):
```javascript
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgCard", "borderFaint", "textPrimary", "textSecondary", "textMuted", "textFaint", "accent", "positive", "negative"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));
```

**Change required (fork resolution, Leitura A):** the sole call site to touch is the `onAbrir` prop consumer at `OpcoesScreen.jsx:640` (`onAbrir={irParaOperar}`) — swap to `onAbrir={irParaMontar}` (new helper above). `OportunidadesOpcoes.jsx` itself needs **zero internal changes** under Leitura A (its `onClick={() => onAbrir(p.t)}` at line 104 is untouched; only what the parent passes as `onAbrir` changes).

**3-variant empty state (preserve exactly, do not collapse to generic)** (lines 128-132):
```javascript
{itens.length === 0 && !carregando && (
  <div style={{ padding: "10px 11px", borderRadius: "9px", background: T.bgCard, border: `1px solid ${T.borderFaint}`, fontSize: "12px", color: T.textSecondary, lineHeight: 1.5 }}>
    {algumLiquido ? cp.tiraOpcoesSemSetup : algumSemMercado ? cp.tiraOpcoesSemMercado : cp.tiraOpcoesSemCobertura}
  </div>
)}
```

---

### `web/src/opcoes/entendimento.jsx` — sheet shell pattern for `VigiasSheet`

**Analog:** `ConceitoSheet` (lines 180-206)

**Sheet shell to copy for `VigiasSheet`** (`entendimento.jsx:206`, exact zIndex/positioning UI-SPEC mandates reusing verbatim):
```javascript
style={{ position: "fixed", inset: 0, zIndex: 86, background: T.scrim, display: "flex", alignItems: "flex-end", justifyContent: "center" }}
```
Panel geometry (UI-SPEC lines 176-182, cites this same file): `maxWidth: 520px`, `background: T.bgPanel`, `borderRadius: "18px 18px 0 0"`, `padding: "16px 18px calc(18px + env(safe-area-inset-bottom))"`, `maxHeight: "82vh", overflowY: "auto"`. `VigiasSheet` wraps `SecaoVigias` unmodified inside this shell — no new fetch, no new state beyond open/close boolean.

---

### `server/app/opcoes_curadoria.py` (service, pure transform — ranking)

**Analog:** itself — `rankear()` (lines 552-580) and `candidatos_da_posicao()` (lines 163-310) are both extended, not replaced.

**Current sort key** (lines 575-578):
```python
ordenados = sorted(candidatos, key=lambda c: (
    -c["razao"], -(c.get("premioUnitario") or 0.0),
    c.get("contractSymbol") or "", c.get("idCandidato") or "",
))
```
D-09 replaces `-c["razao"]` as primary key with `-c["premioAnualizado"]` (new field, `(premio/spot) × (365/dias)`), computed alongside `razao` in `candidatos_da_posicao` (same spot where `razao = round(premio_unitario / perda_maxima, 6)` is computed today, line 274/344/405/508) — `razao` itself is NOT removed from the dict (D-14 only stops *displaying* it in the frontend; `exigir_ranking()` at line 583 still validates on a numeric `razao`-shaped field, confirm which key it asserts before renaming/removing anything).

**D-08 admission floor** — new filter step before `rankear()` is called (candidate-list comprehension pattern, matching the existing perda_maxima guard at lines 265-266):
```python
if not isinstance(perda_maxima, (int, float)) or isinstance(perda_maxima, bool) or perda_maxima <= 0:
    continue
```
Same shape for the new floor: compute `prob_itm` via `options_quant.black_scholes(...)` (imported fresh into this module — not currently imported here), `prob_otm = 1 - prob_itm`, `continue` when `prob_otm < 0.60`. **D-12 scope guard: this filter belongs only in the code path that feeds Recomendadas (`opcoes_curadoria.py`), never in `opcoes_lastreadas.py`** (Oportunidades' motor).

**`black_scholes` call-site pattern to copy** (`server/app/options_api.py:93-105`, `_enrich_contract`):
```python
bs = black_scholes(kind, spot, strike, years_to_expiration(days), 0.105, float(iv or hv21 or 0), 0.0) if strike > 0 else None
...
prob_itm = bs.prob_itm if bs else None
```
Same call shape applies in `opcoes_curadoria.py`: `option_type`, `spot`, `strike`, `years_to_expiration(dias)`, rate (hardcoded `0.105` per existing precedent — CONTEXT.md explicitly defers replacing this with real Selic/CDI, D-08 only requires *some* rate), `vol` (iv-or-hv21 fallback, same null-safety), `dividend_yield=0.0`. **Missing IV/vol → `black_scholes` returns `None` → `prob_itm` is `None` → treat as "cannot compute floor" (exclude candidate, do not silently admit) — principle 4 of CLAUDE.md, never fabricate a passing probability.**

**`exigir_ranking()` validation pattern** (lines 583-613) — any new field added to the ranked dict (`premioAnualizado`) does not need a new guardian function; the existing structural check (posição sequencial 1..N, razão monotonic) stays as-is unless the sort key itself changes identity (if `premioAnualizado` becomes the field checked for monotonicity, `exigir_ranking` needs updating in lockstep — flag for plan-checker per its docstring's own precedent of "reversão deliberada atualiza o guardião com nota").

---

## Shared Patterns

### Tab pill row (navigation)
**Source:** `web/src/opcoes/OpcoesScreen.jsx:657-701` (`subabas`, `workspacePillRow`)
**Apply to:** the new `abaBar` (3-item) — copy geometry verbatim (44px minHeight, 8px/14px padding, 11px radius, `T.accent`/`T.accentTint10` active vs `T.borderSubtle`/`T.bgPanel`/`T.textSecondary` inactive, 700 weight, 13px, `aria-pressed`), only the data array and state hook change.

### Execution-inline (propose → confirm → execute)
**Source:** `web/src/opcoes/CuradoriaEstruturas.jsx:91-129, 206-283` (`handleExecutar`, `abertoId`, liquidity DIFÍCIL checkbox, inline confirmation panel)
**Apply to:** the dissolved `SubAbaOperar`'s executor role — now absorbed entirely by Recomendadas' existing implementation; no new file needed for D-05. If Leitura B of the Oportunidades fork is adopted instead of Leitura A, this same block is the one to port into `OportunidadesOpcoes.jsx`.

### Bottom sheet (icon → sheet, zero new fetch)
**Source:** `web/src/entendimento.jsx:180-206` (`ConceitoSheet`)
**Apply to:** `VigiasSheet` (wraps `SecaoVigias.jsx` unmodified) and the 3 per-tab ⓘ buttons (all reuse `ConceitoSheet` itself, just repositioned — not a new sheet type).

### Token-mirror convention (ADR-027 Emenda 3 isolation)
**Source:** every file in `web/src/opcoes/*.jsx` (e.g. `OportunidadesOpcoes.jsx:23-25`, `SecaoVigias.jsx:16-22`, `CuradoriaEstruturas.jsx:34-36`)
```javascript
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = [ /* only the tokens this file needs */ ];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));
```
**Apply to:** any new module created in `web/src/opcoes/` (e.g. a standalone `VigiasBadge.jsx` if not kept inline) — never import `T`/tokens from `App.jsx`.

### Error/empty-state precedence cascade
**Source:** `CuradoriaEstruturas.jsx:298-328` (loading → error → empty), `OportunidadesOpcoes.jsx:123-132` (loading → 3-variant empty)
**Apply to:** the new 4-state cascade in Recomendadas (D-11): carregando → erro → vazio-por-piso → vazio-sem-candidato.

### Pure-calculation module discipline (no I/O, no clock read)
**Source:** `server/app/opcoes_curadoria.py` module docstring (lines 1-38) — "sem rede, sem banco, sem LLM, sem leitura de relógio interna (`hoje` entra por argumento)"
**Apply to:** any admission-floor calculation added here — `black_scholes` call must receive all inputs as arguments (spot/strike/days/iv/hv21 already flow through `candidatos_da_posicao`'s existing parameters), no new external call from this module.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `VigiasBadge` (icon+counter button in the `<h1>` row) | component | request-response | No existing compact icon+counter pill in `web/src/opcoes/` — closest precedent is `BOTAO` (`OpcoesScreen.jsx:140-144`) used at full width; this is the first instance of that geometry used compact, inline, beside a heading. Low risk: it's a straightforward composition of existing tokens, not a new pattern. |

---

## Metadata

**Analog search scope:** `web/src/opcoes/*.jsx`, `web/src/entendimento.jsx`, `web/src/glossario.js`, `web/src/copy.js`, `server/app/opcoes_curadoria.py`, `server/app/options_quant.py`, `server/app/options_api.py`
**Files scanned:** 24 (`web/src/opcoes/` directory listing) + 4 backend modules + copy.js/glossario.js
**Pattern extraction date:** 2026-09-24
