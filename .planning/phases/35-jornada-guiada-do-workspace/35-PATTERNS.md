# Phase 35: Jornada Guiada do Workspace - Pattern Map

**Mapped:** 2026-09-21
**Files analyzed:** 5 (all modified, zero new files)
**Analogs found:** 5 / 5 — every pattern this phase needs already ships in the
same file tree; no external/new pattern required.

## File Classification

| Modified File | Role | Data Flow | Closest Analog | Match Quality |
|----------------|------|-----------|-----------------|---------------|
| `web/src/opcoes/OpcoesScreen.jsx` | component (orchestrator) | request-response (renders derived state, no new fetch) | itself — `workspacePillRow`/`subabas` pill-row pattern (lines 611-655), `blocoLeituraDoServico` button (540-563) | exact (self-analog, same file) |
| `web/src/opcoes/SecaoAnalisar.jsx` | component (job-to-be-done section) | request-response | `SecaoComparar.jsx` (sibling, same role/flow) + `OpcoesScreen.jsx`'s `blocoLeituraDoServico` button | exact |
| `web/src/opcoes/SecaoComparar.jsx` | component (job-to-be-done section) | request-response | `SecaoAnalisar.jsx` (sibling, same role/flow) | exact |
| `web/src/opcoes/uiOpcoes.jsx` | utility (shared style/component primitives module) | transform (pure style objects + small components) | itself — existing centralization precedent (`Kicker`, `Linha`, `RazaoGanhoPerda`, `ErroDoMcp`) | exact (self-analog) |
| `web/src/copy.js` | config (per-mode copy dictionary) | CRUD-like (static key/value declarations) | itself — existing `cp.opcoesX` key pairs across `COPY.estudo`/`COPY.operador` | exact (self-analog) |

**Cross-file precedent (not modified, cited by CONTEXT/UI-SPEC as the source pattern for `BOTAO_PRIMARIO`):**
- `web/src/opcoes/CuradoriaEstruturas.jsx:264-271` — solid-accent-fill button precedent (geometry + `opacity: 0.55` disabled state). **Do not copy its `color: "#fff"` literal** — UI-SPEC computed this fails AA contrast in 2 of 4 theme×mode combos; use `T.onAccent` instead (see below).
- `web/src/opcoes/PropostaLastreada.jsx:183` — the `T.positive`/`T.negative` "never reuse for UI success" rule, load-bearing for `MARCA_RESULTADO`'s color choice.

---

## Pattern Assignments

### `web/src/opcoes/OpcoesScreen.jsx` (component, request-response)

**Analog:** itself (existing `workspacePillRow`/`subabas` pill pattern + `blocoLeituraDoServico`)

**Imports pattern** (lines 20-87, no new imports needed for D-01/D-02/D-08 — only `Kicker`/`AJUDA` already imported):
```jsx
import { Kicker, Aviso, ErroDoMcp, RecusaCobrada, Linha } from "./uiOpcoes.jsx";
```
If `BOTAO_PRIMARIO`/`desabilitadoPrimario` are centralized in `uiOpcoes.jsx` (planner's discretion call, see Shared Patterns below), add them to this same import line rather than declaring a second local copy.

**TOKENS array — must add `onAccent`** (lines 92-94):
```jsx
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "textFaint", "accent", "accentTint10", "negative", "scrim"];
```
Add `"onAccent"` to this array — `T.onAccent` resolves to `var(--on-accent)` automatically via the existing `VARKEY`/`Object.fromEntries` machinery (lines 91, 94), zero new logic needed.

**Existing BOTAO geometry to mirror exactly for `BOTAO_PRIMARIO`** (lines 127-131):
```jsx
const BOTAO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, fontWeight: 700, fontSize: "13px",
};
```
Corrected `BOTAO_PRIMARIO` (per UI-SPEC contrast correction — use `T.onAccent`, never literal `#fff`):
```jsx
const BOTAO_PRIMARIO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: "none", background: T.accent, color: T.onAccent,
  fontWeight: 700, fontSize: "13px",
};
const desabilitadoPrimario = (cond) => (cond ? { opacity: 0.55, cursor: "not-allowed" } : null);
```

**Existing `CUSTO_NO_BOTAO` to mirror for `CUSTO_NO_BOTAO_PRIMARIO`** (lines 142-145):
```jsx
const CUSTO_NO_BOTAO = {
  display: "block", fontSize: "11px", fontWeight: 600,
  color: T.textMuted, marginTop: "3px",
};
```
Corrected variant (UI-SPEC resolution — opaque `T.onAccent`, not `color-mix` alpha, which fails contrast in every theme×mode combo tested):
```jsx
const CUSTO_NO_BOTAO_PRIMARIO = {
  display: "block", fontSize: "11px", fontWeight: 600,
  color: T.onAccent, marginTop: "3px",
};
```

**Core "invite button" pattern to restyle** (lines 540-563, `blocoLeituraDoServico`):
```jsx
const blocoLeituraDoServico = (
  <div style={{ marginTop: "14px" }}>
    <Kicker>{cp.opcoesLeituraTitulo || "LEITURA DO ATIVO"}</Kicker>
    <div style={CAIXA}>
      <div style={{ fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.5 }}>
        {cp.opcoesLeituraConvite || ""}
      </div>
      <button
        onClick={abrirLeitura}
        style={{ ...BOTAO, width: "100%", marginTop: "12px" }}
      >
        <span style={{ display: "block" }}>{cp.opcoesLerNoServico || "Ler no serviço de opções"}</span>
        <span style={CUSTO_NO_BOTAO}>
          {(cp.opcoesCustoChamadas || ((n) => String(n)))(CUSTO_DA_ACAO.leitura)}
        </span>
      </button>
    </div>
  </div>
);
```
Change: swap `BOTAO` → `BOTAO_PRIMARIO` and `CUSTO_NO_BOTAO` → `CUSTO_NO_BOTAO_PRIMARIO` in this one button only (D-04 — exactly 3 buttons app-wide get this treatment).

**Kicker suffix pattern** (D-01/D-08, `Kicker` accepts `children` as-is, no component change — `uiOpcoes.jsx:37-43`):
```jsx
<Kicker>{(cp.opcoesLeituraTitulo || "LEITURA DO ATIVO") + " · " + (cp.opcoesPasso1de2 || "Passo 1 de 2")}</Kicker>
```

**Pill-row Kicker + transition-line pattern to insert above `workspacePillRow`** (replaces line 705's bare `{workspacePillRow}`, UI-SPEC exact contract):
```jsx
<Kicker>{(cp.opcoesEscolhaTitulo || "O QUE FAZER") + " · " + (cp.opcoesPasso2de2 || "Passo 2 de 2")}</Kicker>
{temLeitura ? <div style={AJUDA}>{cp.opcoesLeituraConcluidaAjuda || "Leitura concluída — escolha Analisar ou Comparar."}</div> : null}
{workspacePillRow}
```
`AJUDA` already declared at line 151, reused verbatim — no new style object.

**D-02 gate fix** (line 700, one-token change using existing `abaWorkspace` state declared at line 260):
```jsx
// before:
{podePedirLeitura ? blocoLeituraDoServico : null}
// after:
{podePedirLeitura && abaWorkspace !== "setups" ? blocoLeituraDoServico : null}
```

**D-06 "leitura já feita" new branch** (new code, inserted where `blocoLeituraDoServico`'s slot goes empty today once `temLeitura`):
```jsx
{temLeitura ? (
  <div style={{ marginTop: "14px" }}>
    <Kicker>{(cp.opcoesLeituraTitulo || "LEITURA DO ATIVO") + " · " + (cp.opcoesLeituraJaFeita || "leitura já feita")}</Kicker>
  </div>
) : null}
```

**Error handling pattern (unchanged, reused as-is):** `ErroDoMcp`/`RecusaCobrada` cascade — this phase touches nothing in the carregando→erro→vazio→dados cascade, only what sits above/around it (per UI-SPEC "Copywriting Contract" table). No new error-handling code needed in this file.

---

### `web/src/opcoes/SecaoAnalisar.jsx` (component, request-response)

**Analog:** `SecaoComparar.jsx` (sibling — same role, same job-to-be-done extraction pattern, same `desabilitado`/`BOTAO`/`CUSTO_NO_BOTAO` conventions)

**TOKENS array — must add `onAccent`** (lines 42-43):
```jsx
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "accent", "accentTint10"];
```
Add `"onAccent"`.

**Core button to restyle — "Montar estrutura"** (lines 320-329):
```jsx
<button
  onClick={() => montarProposta({ direction: tese, expiration: vencimento || undefined, lote: loteNum })}
  disabled={!temTese || !loteOk}
  style={{ ...BOTAO, width: "100%", marginTop: "12px", ...desabilitado(!temTese || !loteOk) }}
>
  <span style={{ display: "block" }}>{cp.opcoesMontarEstrutura || "Montar estrutura"}</span>
  <span style={CUSTO_NO_BOTAO}>
    {(cp.opcoesCustoChamadas || ((n) => String(n)))(custos.proposta)}
  </span>
</button>
```
Change: `BOTAO` → `BOTAO_PRIMARIO`, `desabilitado(...)` → `desabilitadoPrimario(...)`, `CUSTO_NO_BOTAO` → `CUSTO_NO_BOTAO_PRIMARIO`. Where `BOTAO_PRIMARIO`/`desabilitadoPrimario`/`CUSTO_NO_BOTAO_PRIMARIO` are DECLARED (locally here, or imported from `uiOpcoes.jsx`) is the centralization decision — see Shared Patterns.

**`MARCA_RESULTADO` placement** (after line 329's button, before the existing `carregando → erro → vazio → dados` cascade at lines 331-332):
```jsx
{proposta.dados && (proposta.dados.estruturas || []).length ? (
  <div style={MARCA_RESULTADO}>
    <span>✓</span>
    <span>{cp.opcoesEstruturaMontada || "Estrutura montada"}</span>
  </div>
) : null}
```
`MARCA_RESULTADO` style (new constant, from UI-SPEC, uses `T.textMuted` — **never** `T.positive`/`T.negative`, per `PropostaLastreada.jsx:183`'s rule):
```jsx
const MARCA_RESULTADO = {
  display: "flex", alignItems: "center", gap: "5px",
  fontSize: "11px", color: T.textMuted, marginTop: "6px",
};
```

**Disabled-button precedent already in this file** (`desabilitado`, declared near `BOTAO`/`CAMPO` block, mirrors `SecaoComparar.jsx:76`):
```jsx
const desabilitado = (cond) => (cond ? { opacity: 0.45, cursor: "not-allowed" } : null);
```
`desabilitadoPrimario` is the same shape at `0.55` instead of `0.45` (D-05) — copy this one-liner's structure, not its value.

---

### `web/src/opcoes/SecaoComparar.jsx` (component, request-response)

**Analog:** `SecaoAnalisar.jsx` (sibling)

**TOKENS array — must add BOTH `accent` and `onAccent`** (line 47, this file has neither today):
```jsx
const TOKENS = ["textSecondary", "textMuted", "borderSubtle", "bgPanel", "bgBase", "textPrimary"];
```
Becomes: `[..., "accent", "onAccent"]`.

**Core button to restyle — "Ver possibilidades"** (lines 152-161):
```jsx
<button
  onClick={() => verPossibilidades({
    direction: tese, lote: loteNum, alvo: alvoNum, stop: stopNum,
    expirations: consultados,
  })}
  disabled={!temTese || !loteOk}
  style={{ ...BOTAO, width: "100%", marginTop: "12px", ...desabilitado(!temTese || !loteOk) }}
>
  {cp.opcoesVerPossibilidades || "Ver possibilidades"}
</button>
```
**Important divergence from `SecaoAnalisar.jsx`'s button:** this button has NO `CUSTO_NO_BOTAO` second line today (cost is declared as a separate line at 128-130, *before* the button, not inside it) — the UI-SPEC's `CUSTO_NO_BOTAO_PRIMARIO` correction does not apply here; only swap `BOTAO` → `BOTAO_PRIMARIO` and `desabilitado(...)` → `desabilitadoPrimario(...)`. Do not add a cost subtext inside this button — that would be new scope not in CONTEXT/UI-SPEC.

**`MARCA_RESULTADO` placement** (after line 161's button, before the `possibilidades` cascade at lines 165-166):
```jsx
{possibilidades.dados && (possibilidades.dados.possibilidades || []).length ? (
  <div style={MARCA_RESULTADO}>
    <span>✓</span>
    <span>{cp.opcoesPossibilidadesVistas || "Possibilidades carregadas"}</span>
  </div>
) : null}
```

**Existing `desabilitado` in this file** (line 76, identical shape to `SecaoAnalisar.jsx`'s):
```jsx
const desabilitado = (cond) => (cond ? { opacity: 0.45, cursor: "not-allowed" } : null);
```

---

### `web/src/opcoes/uiOpcoes.jsx` (utility, transform — candidate for centralization)

**Analog:** itself — this module already IS the centralization precedent for exactly this kind of decision (`Kicker`/`Linha`/`RazaoGanhoPerda`/`ErroDoMcp` all migrated here because 2+ files rendered identical logic).

**Existing centralization pattern** (module docstring, lines 1-28, and each export's own "why it moved here" comment, e.g. lines 24-27, 53-55, 65-68):
```jsx
/**
 * Regra de duplicação aceita neste diretório: token de tema, constante de
 * estilo e formatador de UMA linha podem ser espelho declarado local em cada
 * arquivo de `web/src/opcoes/` (mesmo padrão de `OportunidadesOpcoes.jsx`/
 * `CuradoriaEstruturas.jsx`) — mas qualquer coisa com RAMIFICAÇÃO de lógica
 * (como os `if (erro.code === ...)` abaixo) vive numa fonte só, aqui.
 */
```
**Decision guidance for the planner (per CONTEXT.md's "Claude's Discretion"):** `BOTAO_PRIMARIO`/`CUSTO_NO_BOTAO_PRIMARIO`/`desabilitadoPrimario`/`MARCA_RESULTADO` are pure style *objects and one-line helpers* with **zero branching logic** — by this module's own stated rule ("token de tema, constante de estilo... podem ser espelho declarado local"), they are NOT required to centralize here. `BOTAO`/`CAIXA`/`CAMPO`/`AJUDA` remain duplicated per-file today (confirmed: `OpcoesScreen.jsx:127-151`, `SecaoAnalisar.jsx` and `SecaoComparar.jsx` each declare their own copies) — that is the established precedent this phase's new constants should follow **unless** the planner has a concrete reason to break it (e.g., if `MARCA_RESULTADO` is later reused by a 3rd file, matching `Linha`'s migration trigger). Centralizing here now would be introducing the first exception to an explicit, documented local rule without the 2+-consumer trigger the rule itself uses to decide.

**If centralized anyway**, the export shape to match (`Kicker`, lines 37-43 — plain function component/const, no HOC):
```jsx
export function Kicker({ children }) {
  return (
    <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: ".08em", color: T.textMuted, margin: "18px 0 8px" }}>
      {children}
    </div>
  );
}
```
Local `TOKENS`/`T` mirror here (lines 29-31) would also need `onAccent` and `accent` added if any new constant references them.

---

### `web/src/copy.js` (config, per-mode static declarations)

**Analog:** itself — existing `cp.opcoesX` key pairs, several of which already diverge in tone between `COPY.estudo` and `COPY.operador` (e.g. `opcoesMontarEstrutura`: "Montar a estrutura" vs "Montar estrutura"; `opcoesVerPossibilidades`: "Comparar os vencimentos" vs "Ver possibilidades"; `opcoesAbaSetupsSalvos`: "Setups salvos" vs "Setups").

**Declaration pattern — `COPY.estudo` block** (e.g. lines 103-110, plain string keys inline in the object, comments above a key explain WHY when non-obvious):
```jsx
opcoesLeituraTitulo: "LEITURA DO ATIVO",
// Fase 27 (27-05) — a leitura do SERVIÇO virou clique. As duas chaves
// abaixo são o convite...
opcoesLerNoServico: "Ler no serviço de opções",
```

**Declaration pattern — `COPY.operador` block** (e.g. lines 816-820, same keys, terser "voz de mesa" tone, comment cross-references the estudo-branch comment instead of repeating the rationale):
```jsx
opcoesLeituraTitulo: "LEITURA DO ATIVO",
// Fase 27 (27-05) — MESMA substância do ramo estudo, em voz de mesa: o que
// o serviço acrescenta ao que o motor interno já entregou de graça.
opcoesLerNoServico: "Puxar a leitura do serviço",
```

**New keys required (per UI-SPEC's Copywriting Contract table) — insertion points and exact defaults:**

| Key | Insertion point (estudo) | Insertion point (operador) | Default text |
|-----|---------------------------|------------------------------|---------------|
| `cp.opcoesPasso1de2` | near `opcoesLeituraTitulo` (~line 103) | near `opcoesLeituraTitulo` (~line 816) | `"Passo 1 de 2"` |
| `cp.opcoesEscolhaTitulo` | near `opcoesAbaAnalisar` block (~line 392-394) | near `opcoesAbaAnalisar` block (~line 1031-1033) | `"O QUE FAZER"` |
| `cp.opcoesPasso2de2` | same area | same area | `"Passo 2 de 2"` |
| `cp.opcoesLeituraConcluidaAjuda` | same area (used by `AJUDA` transition line) | same area | `"Leitura concluída — escolha Analisar ou Comparar."` (D-08 exact wording, locked content) |
| `cp.opcoesLeituraJaFeita` | near `opcoesLeituraTitulo` | near `opcoesLeituraTitulo` | `"leitura já feita"` |
| `cp.opcoesEstruturaMontada` | near `opcoesMontarEstrutura` (~line 273) | near `opcoesMontarEstrutura` (~line 926) | `"Estrutura montada"` |
| `cp.opcoesPossibilidadesVistas` | near `opcoesVerPossibilidades` (~line 274) | near `opcoesVerPossibilidades` (~line 927) | `"Possibilidades carregadas"` |

**Per UI-SPEC's own analysis:** none of these 7 strings reference execution or money, so a single shared string per key (identical in both `COPY.estudo`/`COPY.operador`) is the defensible default — diverge only with a concrete reason. This differs from the `opcoesMontarEstrutura`-style keys (which DO diverge) only because those describe an action/CTA in mesa-vs-professor voice; these new keys are progress/metadata labels, a category that stays neutral elsewhere in this file (e.g. `opcoesPregaoRotulo`, `opcoesFonteRotulo`, `opcoesConsultadoEmRotulo` are identical across both branches).

**All-caps Kicker convention to match** (existing precedent, `opcoesLeituraTitulo: "LEITURA DO ATIVO"`, `opcoesSetupsTitulo: "SETUPS GRAVADOS"`): `cp.opcoesEscolhaTitulo` must be `"O QUE FAZER"` (all-caps), not title-case — this is already the exact value UI-SPEC specifies, flagged here only to confirm it matches file convention, not a new rule.

---

## Shared Patterns

### Contrast-safe text-on-accent-fill token
**Source:** app-wide `T.onAccent` token, resolved via the `VARKEY`/`TOKENS`/`T` local-mirror pattern already declared in every file in `web/src/opcoes/*.jsx` (e.g. `OpcoesScreen.jsx:91-94`).
**Apply to:** `BOTAO_PRIMARIO.color` and `CUSTO_NO_BOTAO_PRIMARIO.color` in all 3 files that get a `BOTAO_PRIMARIO` button.
```jsx
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = [/* ...existing keys..., */ "onAccent"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));
```
**Do not** use a literal `#fff` or `color-mix(...)` — both were computed by the UI-SPEC (WCAG contrast ratios against real hex values in `App.jsx:95-213`) to fail AA in multiple theme×mode combinations. `T.onAccent` is the only value that passes in all 4 (4.94:1–8.09:1).

### Solid-accent-fill button geometry (mirrors `BOTAO` exactly, per D-03)
**Source:** `OpcoesScreen.jsx:127-131` (`BOTAO`), corrected against `CuradoriaEstruturas.jsx:264-271`'s precedent (same geometry, minus its uncommented `color:"#fff"` oversight).
**Apply to:** exactly 3 buttons — `OpcoesScreen.jsx` "Ler no serviço de opções", `SecaoAnalisar.jsx` "Montar estrutura", `SecaoComparar.jsx` "Ver possibilidades". Nowhere else (D-04).
```jsx
const BOTAO_PRIMARIO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: "none", background: T.accent, color: T.onAccent,
  fontWeight: 700, fontSize: "13px",
};
const desabilitadoPrimario = (cond) => (cond ? { opacity: 0.55, cursor: "not-allowed" } : null);
```

### Never-disappearing disabled button
**Source:** existing rule stated inline in both `SecaoAnalisar.jsx` and `SecaoComparar.jsx` next to their `desabilitado` helpers ("Botão desabilitado FICA VISÍVEL, em vez de sumir").
**Apply to:** `BOTAO_PRIMARIO` in all 3 buttons — never `display: none`, only `opacity`/`cursor` change via `desabilitadoPrimario`.

### Financial-direction color reservation
**Source:** `PropostaLastreada.jsx:183`, `const cor = isCall ? T.positive : T.negative; // NUNCA T.accent — mesma regra da manchete do ativo`.
**Apply to:** `MARCA_RESULTADO` — must use `T.textMuted`, never `T.positive`/`T.negative`, since those are reserved for buy/sell direction, not UI "success" states.

### `cp.*` fallback-string convention
**Source:** every existing copy consumption site in this file tree, e.g. `OpcoesScreen.jsx:542`: `{cp.opcoesLeituraTitulo || "LEITURA DO ATIVO"}`.
**Apply to:** every new copy usage in `OpcoesScreen.jsx`/`SecaoAnalisar.jsx`/`SecaoComparar.jsx` — always `cp.newKey || "default PT-BR string"`, never a bare `cp.newKey` reference, so the UI degrades gracefully if a key is momentarily missing (matches this file's own resilience convention, not a new one).

---

## No Analog Found

None. Every construct this phase needs (solid-fill button, opacity-based disabled state, Kicker suffix concatenation, muted metadata line, per-mode copy key with optional divergence, TOKENS-array extension) has at least one direct precedent already in `web/src/opcoes/*.jsx` or `web/src/copy.js`.

## Metadata

**Analog search scope:** `web/src/opcoes/*.jsx` (all 9 files in the directory), `web/src/copy.js`.
**Files scanned:** `OpcoesScreen.jsx`, `SecaoAnalisar.jsx`, `SecaoComparar.jsx`, `uiOpcoes.jsx`, `SecaoSetups.jsx` (confirmed unaffected — no `temLeitura` dependency, per D-02's own citation), `WorkspaceHeader.jsx` (confirmed unaffected, stays `BOTAO`), `CuradoriaEstruturas.jsx` (precedent, not modified), `PropostaLastreada.jsx` (precedent, not modified), `copy.js`.
**Pattern extraction date:** 2026-09-21
