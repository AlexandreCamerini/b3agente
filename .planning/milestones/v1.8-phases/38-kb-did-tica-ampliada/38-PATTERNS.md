# Phase 38: KB Didática ampliada - Pattern Map

**Mapped:** 2026-09-23
**Files analyzed:** 9 (+2 likely new test files, flagged below)
**Analogs found:** 9 / 9

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `web/src/didatica.jsx` (NEW) | component (extracted shared module) | request-response | `web/src/opcoes/uiOpcoes.jsx` (extraction precedent, Fase 33) | exact — same "module terceiro" pattern, same repo, same kind of extraction |
| `web/src/App.jsx` — `TelaGlossario` (NEW screen) | component / screen | CRUD-ish read + client-side filter | `web/src/App.jsx` `AjudaScreen`/`ConfigScreen` (sub-screens opened from `PerfilHub` via `perfilView`) | exact — same navigation/mount pattern |
| `web/src/App.jsx` — boot fetch of `/api/kb/catalogo` | component (boot effect) | request-response, fetch-once | `web/src/App.jsx` boot fetch of `/api/conceitos` (`store.conceitos(modoApp)`, sets `didatica` state) | exact — same one-shot-on-boot fetch shape |
| `web/src/opcoes/OpcoesScreen.jsx` (MODIFIED) | component (isolated screen) | request-response | itself — existing import block + isolation comment (`OpcoesScreen.jsx:1-65`) | exact — file being extended, not replaced |
| `server/app/kb.py` — `formatar()`/verbete dicts (MODIFIED, add `titulo`) | service / data catalog | transform (pure, no I/O) | `server/app/conceitos.py` `CONCEITOS` dict (`titulo: {educacional, operador}` shape already there) | exact — the very shape being copied into `kb.py` |
| `server/app/main.py` — `GET /api/kb/catalogo` (NEW route) | route / controller | request-response | `server/app/main.py` `GET /api/kb/buscar` (`main.py:4595-4608`) | exact — same neighborhood, same auth/scope pattern, same module |
| `web/src/api.js` — `kbCatalogo` (NEW method) | service (API client) | request-response | `web/src/api.js` `kbBuscar` (`api.js:285`) | exact — same file, same req() wrapper convention |
| `web/src/persistence.js` — `kbCatalogo` (NEW method, both stores) | store / service | request-response | `web/src/persistence.js` `kbBuscar` in `serverStore`/`deviceStore` (`persistence.js:245`, `1188`) | exact — same file, same dual-store paridade convention |
| `server/tests/test_kb.py` (MODIFIED, add `titulo` assertion) | test | — | itself — existing `id`/`termos`/`texto` assertions (`test_kb.py:1-40`) | exact |
| `web/tests/test_conceito_ui.mjs` (MODIFIED, repoint regex source) | test (guardian) | — | itself — reads `App.jsx` via `readFileSync`, needs to also/instead read `didatica.jsx` | exact — same file, mechanical repoint |
| `web/tests/test_didatica_parity.mjs` (possible NEW sibling for kbCatalogo) | test | — | `web/tests/test_didatica_parity.mjs` (pointed-content parity guardian, cited by research) | role-match — not read directly, but research (HIGH confidence) confirms its shape mirrors `kbBuscar`/`conceito` parity checks |

## Pattern Assignments

### `web/src/didatica.jsx` (NEW module — component, request-response)

**Analog:** `web/src/opcoes/uiOpcoes.jsx` (extraction precedent) + the exact code being moved out of `web/src/App.jsx:2810-3013`

**Theme-token mirroring pattern** (copy verbatim shape, adjust `TOKENS` list to what `SetorAlvo`/`ConceitoSheet`/`AssistenteBox` actually use) — `web/src/opcoes/uiOpcoes.jsx:29-31`:
```javascript
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["textMuted", "borderSubtle", "negative", "bgPanel", "textSecondary", "textPrimary", "borderFaint"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));
```
Research's `Code Examples` section already lists the fuller token set actually needed for the three components being moved: `textFaint, borderSubtle, scrim, bgPanel, textPrimary, textSecondary, accent, accentTint10, negative, textMuted, bgBase`.

**Module isolation header comment pattern** — `web/src/opcoes/uiOpcoes.jsx:1-27` (adapt wording, same rule): declare explicitly that this module does not import `App.jsx` and is importable by both `App.jsx` and `OpcoesScreen.jsx`. Mirror the tone of the existing header, e.g.:
> "Este módulo não importa o núcleo do app... nem `OpcoesScreen.jsx`... Regra de duplicação aceita: token de tema... pode ser espelho declarado local."

**Components to move verbatim (with the one addition noted in Pattern Assignments below), current location `web/src/App.jsx:2818-3013`:**
- `CONCEITO_BLOCOS` (`App.jsx:2818-2824`)
- `SUBLINHADO` (`App.jsx:2842`)
- `SR_ONLY` (`App.jsx:2846`)
- `SetorAlvo` (`App.jsx:2848-2869`)
- `AssistenteBox` (`App.jsx:2876-2939`)
- `ConceitoSheet` (`App.jsx:2941-3013`)

**`ConceitoSheet` fetch pattern — must gain a `fonte` discriminator (Pattern 1 from RESEARCH.md), current code to modify** (`App.jsx:2941-2951`):
```jsx
function ConceitoSheet({ cid, dados, setor, onClose, onTrocar, didatica, voltar }) {
  const [c, setC] = useState(null);
  const [erro, setErro] = useState(false);
  useEffect(() => {
    let alive = true;
    setC(null); setErro(false);
    store.conceito(cid, { dados })
      .then((r) => { if (alive) setC(r); })
      .catch(() => { if (alive) setErro(true); });
    return () => { alive = false; };
  }, [cid, dados]);
  ...
```
New call-sites (KB-01 result rows, KB-02 fixed links) MUST pass an explicit `fonte="kb"` prop and resolve against the in-memory `kbCatalogo` array (not a new fetch) — default stays `"conceito"` so none of the 9 existing call-sites change behavior. See RESEARCH.md Pattern 1 for the exact `useEffect` branch to copy.

**"Veja também" lookup — must change source** (`App.jsx:2990-2992`):
```jsx
{c.veja.map((vid) => {
  const alvo = ((didatica.conceitos || []).find((x) => x && x.id === vid));
```
Change `didatica.conceitos` → the full `kb` catalog (superset) so `veja` targets that only exist in `kb.py` (74 of 83 verbetes) don't silently disappear. Guardian regex at `web/tests/test_conceito_ui.mjs:115-116` currently pins this exact line — must be updated in lockstep (see Shared Patterns below).

**Error/degradation copy — reuse verbatim** (`App.jsx:2968`):
```jsx
{erro && <p style={{ margin: 0, fontSize: "13px", color: T.textMuted }}>Não consegui carregar a explicação agora. O card continua válido.</p>}
```

---

### `web/src/App.jsx` — `TelaGlossario` (NEW screen, KB-01)

**Analog:** existing `perfilView` sub-screen pattern (`ProfileTile` → `onOpen(...)` → conditional render), `App.jsx:2473-2484` (tile) and `App.jsx:9305-9323` (routing switch).

**`ProfileTile` — reuse verbatim, `wide=false` grid-cell variant** (`App.jsx:2473-2484`):
```jsx
function ProfileTile({ icon, title, sub, onClick, wide }) {
  return (
    <button onClick={onClick} style={{ display: "flex", flexDirection: wide ? "row" : "column", alignItems: wide ? "center" : "flex-start", gap: wide ? "13px" : "9px", minHeight: wide ? "auto" : "98px", padding: "14px", borderRadius: "14px", border: `1px solid ${T.borderSubtle}`, background: T.bgCard, textAlign: "left", cursor: "pointer", boxShadow: "0 8px 24px -14px rgba(0,0,0,0.5)" }}>
      <span style={{ width: 34, height: 34, flex: "none", borderRadius: "10px", background: T.accentTint, color: T.accent, display: "flex", alignItems: "center", justifyContent: "center" }} aria-hidden>{icon}</span>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ display: "block", fontSize: "13.5px", fontWeight: 700, color: T.textPrimary }}>{title}</span>
        {sub ? <span style={{ display: "block", fontSize: "11.5px", color: T.textMuted, marginTop: "2px", lineHeight: 1.4 }}>{sub}</span> : null}
      </span>
      {wide ? <svg ...chevron.../> : null}
    </button>
  );
}
```
UI-SPEC already locks the new tile's copy: title `"Glossário"`, sub `"83 termos de indicadores, estruturas e mecânica da B3 — busque ou navegue por categoria"`, placed in the non-`wide` `hubGrid` alongside "IA & Boris"/"Notificações" (UI-SPEC section 1).

**Screen-routing switch pattern to extend** (`App.jsx:9305-9323`, `perfilView` ternary chain) — add a `perfilView === "glossario"` branch following the exact same `BackHeader` + screen-component shape as the `"ajuda"` branch immediately above it:
```jsx
: perfilView === "ajuda"
  ? (<><BackHeader title="Como funciona" onBack={() => setPerfilView("hub")} /><AjudaScreen ctx={ctx} /></>)
  : <PerfilHub ctx={ctx} onOpen={setPerfilView} />)}
```

**Boot fetch pattern to replicate for `GET /api/kb/catalogo`** — mirror the existing `/api/conceitos` boot fetch (referenced by research at `App.jsx:8048-8049`, `store.conceitos(modoApp)`, setting `didatica` state; degrades via `setDidatica({ ligada: false, conceitos: [] })` on failure — same guardian-checked degrade-not-crash shape pinned at `test_conceito_ui.mjs:172-173`). Wire the new catalog into `ctx.kbCatalogo` (per RESEARCH.md Pattern 3) so it is available to both `App.jsx`-internal call-sites (glossary screen, KB-02 links inside `App.jsx`) and passed through to `OpcoesScreen.jsx` without a second fetch.

**`A.abrirVerbete` — reuse as the single "saiba mais" entry point, unchanged** (`App.jsx:8619-8624`):
```jsx
// Plano 04-07 (FIX-C05): link comum "saiba mais" para um conceito, sem
// marcar telemetria — nem `openConceito` ... nem `abrirSetor` ...
// servem aqui; usar qualquer uma contaminaria uma métrica que não é desta interação.
abrirVerbete: (cid, dados) => setConceitoAberto({ cid, dados: dados || null, trilha: [] }),
```
KB-01's search-result rows and KB-02's 3 in-`App.jsx` anchors (Acompanhar/Radar/Watchlist) should call this unchanged — only the value of `cid` and (new) an explicit `fonte: "kb"` need threading through `conceitoAberto`/`ConceitoSheet`.

---

### 4 "saiba mais" anchors (KB-02) — `EvolucaoScreen`/`RadarScreen`/`MercadoScreen`/`OpcoesScreen.jsx`

**Analog:** the one existing precedent, Portfólio's concentration-alert link (`App.jsx:4356-4359`):
```jsx
{ctx.didatica && ctx.didatica.ligada && (
  <button type="button" onClick={() => A.abrirVerbete("diversificacao", { ticker: conc.t, pct: pctArred })}
    style={{ background: "transparent", border: "none", padding: 0, marginTop: "6px", color: T.accent, fontWeight: 700, fontSize: "12px", textDecoration: "none" }}>
    {cp.concentracaoLink}
  </button>
)}
```
Copy the exact button style block for all 4 new anchors (UI-SPEC section 3 confirms: same treatment, string `"saiba mais"` reused verbatim from `copy.js:565,1232`). Fixed `vid` per D-07 — UI-SPEC's proposed table (pending Alex approval per D-08):

| Tab | Proposed `vid` | Família |
|-----|-----------------|---------|
| Acompanhar (`evolucao`) | `mkt-carteira-simulada` | `mercado_b3` |
| Radar | `confluencia` | `setups` |
| Watchlist (`mercado`) | `ind-rsi` | `indicadores` |
| Opções | `mkt-opcao` | `mercado_b3` |

For the 3 tabs living inside `App.jsx` (Acompanhar/Radar/Watchlist): call `A.abrirVerbete(vidFixo, null)` directly — no new state needed, reuses the global `<ConceitoSheet>` overlay already mounted at `App.jsx:9366-9375`, just needs `fonte="kb"` threaded in.

For `OpcoesScreen.jsx` — **must NOT** use `ctx.A.abrirVerbete` per the locked decision (module-import requirement, not just functional coverage — see RESEARCH.md Pattern 3, Opção B). Instead:
```jsx
// web/src/opcoes/OpcoesScreen.jsx — new import + local state, same isolation
// pattern already used for uiOpcoes.jsx/finance.js imports (OpcoesScreen.jsx:20-65)
import { ConceitoSheet } from "../didatica.jsx";
const [verbeteAberto, setVerbeteAberto] = useState(null); // {cid, dados}
<button onClick={() => setVerbeteAberto({ cid: "mkt-opcao", dados: null })}
  style={{ background: "transparent", border: "none", padding: 0, marginTop: "6px", color: T.accent, fontWeight: 700, fontSize: "12px", textDecoration: "none" }}>
  saiba mais
</button>
{verbeteAberto && (
  <ConceitoSheet cid={verbeteAberto.cid} dados={verbeteAberto.dados} fonte="kb"
    kbCatalogo={ctx.kbCatalogo}
    onClose={() => setVerbeteAberto(null)}
    onTrocar={(vid) => setVerbeteAberto((v) => ({ ...v, cid: vid }))}
    didatica={ctx.didatica} voltar={null} />
)}
```
`ctx.kbCatalogo` travels through the existing `ctx` object (already the established data channel across the isolation boundary — `ctx` is built in `App.jsx` and passed as `<OpcoesScreen ctx={ctx} />`, `App.jsx:9299`), never via a new import.

---

### `server/app/kb.py` — add `titulo` to verbete format (MODIFIED)

**Analog:** `server/app/conceitos.py` `CONCEITOS` dict, which already has the exact target shape (`conceitos.py:74-76`):
```python
CONCEITOS = {
    "gatilho": {
        "titulo": {"educacional": "A condição de estudo (o "gatilho")",
                   "operador": "O gatilho de entrada"},
        "campos": (...),
        "naoAcontece": [...],
```

**Current `_de_conceito()` to extend** (`kb.py:94-112`) — copy `c["titulo"]` through (it already exists on the source dict, zero new authoring for the 9 `_de_conceito()`-derived entries):
```python
def _de_conceito(cid: str) -> dict:
    c = conceitos.CONCEITOS[cid]
    texto = {}
    for modo in ("educacional", "operador"):
        m = conceitos.montar(cid, modo, None, resumido=False)
        ...
    termos = {cid, c["titulo"]["educacional"], c["titulo"]["operador"]}
    return {
        "id": cid,
        "termos": tuple(sorted(t for t in termos if t)),
        "familia": _FAMILIA_DO_CONCEITO[cid],
        "texto": texto,
        "veja": list(c.get("veja") or []),
        # ADD: "titulo": c["titulo"],
    }
```

**Current `formatar()` to extend** (`kb.py:1618-1628`) — add `titulo` resolution, same mode-collapse pattern already used for `texto`:
```python
def formatar(v: dict, modo: str) -> dict:
    voc = "operador" if modo == "operador" else "educacional"
    return {
        "id": v["id"],
        "familia": v.get("familia"),
        "texto": v["texto"].get(voc) or v["texto"].get("educacional") or "",
        "veja": list(v.get("veja") or []),
        # ADD: "titulo": v["titulo"].get(voc) or v["titulo"].get("educacional") or "",
    }
```

**Volume warning (Pitfall 6 from RESEARCH.md):** the ~74 native verbetes (`_INDICADORES`, `_ESTRUTURA`, `_FAMILIAS`, `_MODELOS`/`_modelo_verbete`, `_SETUPS`, `_PLANO_RISCO_EXTRA`, `_FUNDAMENTOS_EXTRA`, `_MERCADO_B3`, `_KPIS` — see `kb.py:167-1522` for the literal-list pattern each of these follows, e.g. `_INDICADORES` starting at `kb.py:167`) need a NEW `titulo: {educacional, operador}` dict authored by hand (~148 strings), following the same vocabulary rule documented in the module docstring (`kb.py:32-34`) and enforced by `.claude/skills/didatica-boris/SKILL.md`. Treat as a content task, separate from the code task above.

---

### `server/app/main.py` — `GET /api/kb/catalogo` (NEW route)

**Analog:** `GET /api/kb/buscar`, same file, same neighborhood (`main.py:4595-4608`):
```python
@app.get("/api/kb/buscar")
async def get_kb_buscar(q: str = "", modo: Optional[str] = None,
                        scope: Optional[str] = Depends(current_scope)):
    """Busca pública na base de conhecimento — sem custo, sem conta.
    ...
    """
    from . import kb
    cfg = store.get(_conn, "config", user_id=scope) or {}
    voc = "operador" if (modo or cfg.get("appMode")) == "operador" else "educacional"
    achados = kb.buscar(q, limite=5)
    return {"query": q, "resultados": [kb.formatar(v, voc) for v in achados]}
```

**New route — copy this shape exactly** (proposal already validated in RESEARCH.md Pattern 2):
```python
@app.get("/api/kb/catalogo")
async def get_kb_catalogo(modo: Optional[str] = None,
                          scope: Optional[str] = Depends(current_scope)):
    """Catálogo completo da KB (83 verbetes), formatado no modo do escopo.
    Público, sem custo, sem conta — mesma filosofia de GET /api/kb/buscar."""
    from . import kb
    cfg = store.get(_conn, "config", user_id=scope) or {}
    voc = "operador" if (modo or cfg.get("appMode")) == "operador" else "educacional"
    return {"modo": voc, "verbetes": [kb.formatar(v, voc) for v in kb.catalogo()]}
```
No auth pattern to copy beyond `Depends(current_scope)` — same as the analog, `scope` is optional and only used to read `appMode` from config.

**Error-handling pattern:** none needed — `kb.catalogo()` is pure/in-memory, cannot fail in a way that needs a `try/except` (matches the analog, which also has none).

---

### `web/src/api.js` — `kbCatalogo` (NEW method)

**Analog:** `kbBuscar`, same file (`api.js:283-285`):
```javascript
// Base de conhecimento (Fase F3): busca pública, custo zero, sem conta —
// mesma camada que /api/assistente já consulta primeiro por dentro.
kbBuscar: (q, modo) => req("GET", "/api/kb/buscar?q=" + encodeURIComponent(q || "") + (modo ? "&modo=" + encodeURIComponent(modo) : ""), undefined, 15000),
```
New method, same `req()` wrapper, same 15000ms timeout convention:
```javascript
kbCatalogo: (modo) => req("GET", "/api/kb/catalogo" + (modo ? "?modo=" + encodeURIComponent(modo) : ""), undefined, 15000),
```

---

### `web/src/persistence.js` — `kbCatalogo` (NEW method, BOTH stores — paridade obrigatória)

**Analog:** `kbBuscar` in both stores (`persistence.js:245`, `persistence.js:1188`):
```javascript
// serverStore (persistence.js:245):
kbBuscar: (q, modo) => api.kbBuscar(q, modo),
// deviceStore (persistence.js:1188):
async kbBuscar(q, modo) { ensure(); return api.kbBuscar(q, modo || doc.config.appMode || "estudo"); },
```
New methods, same file, same split:
```javascript
// serverStore:
kbCatalogo: (modo) => api.kbCatalogo(modo),
// deviceStore:
async kbCatalogo(modo) { ensure(); return api.kbCatalogo(modo || doc.config.appMode || "estudo"); },
```
**Paridade guardian:** `web/tests/test_fase3_paridade_stores_generica.mjs` already scans both blocks by method name — no separate paridade-of-name test needed, but a content-shape test (same pattern as `web/tests/test_didatica_parity.mjs`) is recommended per RESEARCH.md.

---

## Shared Patterns

### Theme-token mirroring (frontend, all new/moved components)
**Source:** `web/src/opcoes/uiOpcoes.jsx:29-31`
**Apply to:** `web/src/didatica.jsx` (new module), any new inline styles in `TelaGlossario`/`OpcoesScreen.jsx` additions.
```javascript
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = [/* only the keys actually used */];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));
```
Do NOT import a central `T` — repo convention is a local mirror per module (explicit anti-pattern in RESEARCH.md).

### Degrade-not-crash on fetch failure
**Source:** `App.jsx:2968` (`ConceitoSheet` error paragraph) and the boot-fetch degrade for `didatica` (`setDidatica({ ligada: false, conceitos: [] })`, guarded by `test_conceito_ui.mjs:172-173`)
**Apply to:** `TelaGlossario`'s catalog fetch (UI-SPEC mandates: *"Não consegui carregar o glossário agora. Toque para tentar de novo."* — retry action, never a fabricated/partial list, per CLAUDE.md princípio 4) and `ConceitoSheet`'s `fonte="kb"` branch (if the `cid` isn't found in the in-memory catalog, treat like the existing `erro` state, do not silently render nothing).

### Dual-store paridade (backend-agnostic client data)
**Source:** `web/src/persistence.js` — every method exists in BOTH `serverStore()` and `deviceStore()` with the same name/contract; `web/tests/test_fase3_paridade_stores_generica.mjs` enforces this generically by name.
**Apply to:** `kbCatalogo` (new). Non-negotiable per `CLAUDE.md` guardrail ("Paridade dos dois stores... método novo entra nos DOIS").

### `A.abrirVerbete` as the single "saiba mais" entry point (no new navigation mechanism)
**Source:** `App.jsx:8619-8624`
**Apply to:** all `App.jsx`-internal KB-02 anchors and KB-01 result-row taps. `OpcoesScreen.jsx` mirrors the SHAPE (own local `verbeteAberto` state + own `ConceitoSheet` instance) but does not call `A.abrirVerbete` directly (isolation boundary, RESEARCH.md Pattern 3 Opção B).

### Guardian test repointing after component extraction
**Source:** `web/tests/test_conceito_ui.mjs:26-27` (reads `App.jsx` via `readFileSync`, then runs ~30 regex assertions against it — full file already read above)
**Apply to:** every assertion in this file that targets `SetorAlvo`/`ConceitoSheet`/`AssistenteBox`/`SUBLINHADO`/`SR_ONLY`/`CONCEITO_BLOCOS` source text must be repointed to read `web/src/didatica.jsx` instead of (or in addition to) `App.jsx`. This is documented in the project's own `STATE.md` as a repeat failure mode across Fases 32/33/34 — do not treat as optional cleanup, it is required for the phase's test suite to pass. Concretely, at minimum these assertions move:
- line 37: `/function ConceitoSheet\(/` + `/store\.conceito\(cid, \{ dados \}\)/` — the second regex ALSO needs updating for the `fonte` discriminator (RESEARCH.md Pattern 1) or it will assert the OLD unconditional call.
- lines 55-56: `/function SetorAlvo\(\{ setorId, dados, rotulo, A, didatica/`
- line 60: `/ConceitoDot/` absence + `/const SUBLINHADO = /`
- lines 115-116: `/\(didatica\.conceitos \|\| \[\]\)\.find\(\(x\) => x && x\.id === vid\)/` — MUST change to assert the new kb-catalog-backed lookup, not the old `didatica.conceitos`-only one (Pitfall 2, RESEARCH.md).
Everything else in the file (proativa/eleição/push/acessibilidade assertions) stays pointed at `App.jsx` since that logic is NOT moving.

### `titulo` field addition — content vs. code split
**Source:** RESEARCH.md Pitfall 6, `.claude/skills/didatica-boris/SKILL.md`, `server/tests/test_kb.py` `EXPRESSOES_PROIBIDAS` guardian pattern (file header, lines 1-16, read above)
**Apply to:** any plan task touching `kb.py`'s `titulo` field. Split into (a) structural code change (`_de_conceito`/`formatar`, small, mechanical) and (b) content authoring (~148 short strings across ~74 verbetes × 2 modes, reviewed against the vocabulary skill and the existing `EXPRESSOES_PROIBIDAS` list before merge).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `web/tests/test_didatica_parity.mjs` (possible NEW content-parity assertion for `kbCatalogo`) | test | — | Not read directly this pass (RESEARCH.md cites it at HIGH confidence, lines 1-45, as the existing pointed-content parity pattern for `kbBuscar`/`conceito`) — planner should read it directly before writing the new assertion, since this pattern-mapper did not re-read a range already covered by research's citation |

## Metadata

**Analog search scope:** `web/src/`, `web/src/opcoes/`, `server/app/`, `web/tests/`, `server/tests/` — guided entirely by explicit file:line references already gathered in `38-RESEARCH.md` (HIGH confidence, direct code reads) and `38-UI-SPEC.md`.
**Files scanned (read directly this pass):** `web/src/App.jsx` (targeted ranges: 2460-2489, 2810-3019, 4340-4370, 8600-8654, 8960-9014, 9270-9385), `server/app/kb.py` (1-170, 1520-1669), `server/app/conceitos.py` (1-85), `server/app/main.py` (4186-4225, 4580-4614), `web/src/opcoes/OpcoesScreen.jsx` (1-65), `web/src/opcoes/uiOpcoes.jsx` (1-40), `web/src/api.js` (275-294), `web/src/persistence.js` (225-259, 1180-1194), `web/tests/test_conceito_ui.mjs` (full, 183 lines), `server/tests/test_kb.py` (1-40), `.planning/phases/38-kb-did-tica-ampliada/38-UI-SPEC.md` (full, 158 lines).
**Pattern extraction date:** 2026-09-23
