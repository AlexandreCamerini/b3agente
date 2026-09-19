# Phase 19: Motor multi-candidato - Pattern Map

**Mapped:** 2026-09-03
**Files analyzed:** 6 (2 backend modified, 1 backend route file with 2 routes touched, 1 frontend component modified, 2 test files extended + 2 new test files)
**Analogs found:** 6 / 6 — this phase is a pure extension of Phases 14/16/17/18 in the SAME feature area; every file being touched already has itself (an earlier revision) as the closest analog. No external/cross-feature analog search was needed.

**Special note on this phase:** unlike a typical new-feature phase, Phase 19 does not introduce new roles/files — it extends `propor()`, one route, and one React component that ALL already exist and were built across Phases 14→18 with a documented, consistent style (Portuguese comments carrying decision history, guard clauses, `None`-never-`0.0`, CVM manchete guardrail). The "analog" for each file IS the file itself, read at the exact line ranges CONTEXT.md already verified. This document exists to hand the planner concrete before/after code and the exact patterns to preserve, not to point at a different file to imitate.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `server/app/opcoes_lastreadas.py` (`propor()`, lines 158-336) | service (pure calculation, no I/O) | transform (plano+cadeia → candidatos list) | itself, `_propor_collar()` (lines 41-155) — same file, same module, already the multi-candidate-adjacent pattern | exact (self) |
| `server/app/main.py` (`POST /api/options/lastreada/abrir-collar`, lines 2506-2625) | route (FastAPI POST, request-response) | CRUD (validates + re-derives + executes) | itself (prior revision, Phase 17/ADR-026) — no other route in the codebase re-derives a proposal server-side before executing | exact (self) |
| `server/app/main.py` (`GET /api/options/proposta/{ticker}`, lines 2348-2440) | route (FastAPI GET, request-response) | transform (pass-through of `propor()`'s dict) | itself — confirmed NO CHANGE needed structurally, only needs to add `candidatos` key to the returned dict | exact (self), minimal-touch |
| `web/src/App.jsx` — `PropostaDaPosicao` (lines 3992-4060) | component (React, request-response + local mutation) | CRUD (renders proposal, dispatches accept) | `OportunidadesOpcoes` (lines 3919-3981, same file, Phase 18) for the card/scroll visual pattern; `PropostaLastreada` (lines 3023-~3140) for the payoff/CTA internals of a single candidate card | exact (sibling component, same phase family) |
| `server/tests/test_opcoes_lastreadas_proposta.py`, `server/tests/test_opcoes_collar.py` | test | transform (unit, pure function) | themselves — established fixture pattern (`_contrato`/`_cadeia`/`_posicao`, `_PLANO_VENDER`) reused verbatim | exact (self) |
| `server/tests/test_opcoes_collar_rota.py` | test | request-response (FastAPI TestClient) | itself — established fixture pattern (`_expiracao_fixa`, `_snapshot_sem_setup`, `_plano_vender`) for testing `abrir-collar` | exact (self) |

No files with zero analog. No new architectural role is introduced by this phase.

---

## Pattern Assignments

### `server/app/opcoes_lastreadas.py` — `propor()` (service, transform)

**Analog:** itself, `server/app/opcoes_lastreadas.py:158-336` (current) + `_propor_collar()` at `:41-155`.

**Current decision branch to change** (lines 198-212 — untouched shape, still 3-way branch on `decisao`/`lado`):
```python
plano = plano or {}
decisao = plano.get("decisao")
lado = plano.get("lado")
if decisao == "VENDER" or lado == "baixa":
    # Risco de queda sobre posição existente: proteger com PUT.
    tipo = "put_protecao"
elif decisao in ("AGUARDAR CONFIRMAÇÃO", "NÃO OPERAR") or lado == "neutro":
    # Sem alta a preservar: vender o upside gera prêmio.
    tipo = "call_coberta"
else:
    # decisao == "COMPRAR" ou lado == "alta": ...
    return {"proposta": None, "motivo": "sem_setup"}
```
This branch still decides which SINGLE `tipo` string enters the flow (it stays a scalar — `call_coberta`/`put_protecao`/early-return `sem_setup`). What must change is what happens AFTER, inside the `put_protecao` path.

**Current fallback-only collar call to replace** (lines 246-263 — this is the exact block CONTEXT.md says "needs to become try both independently"):
```python
if tipo == "put_protecao":
    contratos = min(contratos, int(cash // (100 * premio)) if premio > 0 else 0)
    if contratos < 1:
        # Julgamento de produto reversível (16-CONTEXT.md, decisão tomada
        # com autonomia concedida): o collar financia a proteção com o
        # prêmio da call vendida, então faz sentido oferecê-lo EXATAMENTE
        # onde a put pura já não cabe no caixa disponível — em vez de só
        # devolver "caixa insuficiente" sem alternativa. Reverter esta
        # regra no futuro é mexer só aqui (a condição `if multiperna`),
        # nunca no motor comum. `_propor_collar` devolvendo `None` (sem
        # call líquida acima do spot, ou débito que também não cabe no
        # caixa) cai no `caixa_insuficiente` de sempre, logo abaixo.
        if multiperna:
            colar = _propor_collar(
                underlying, chain, spot, contrato, posicao, cash, modo, hoje, dias, qty_livre_val)
            if colar is not None:
                return {"proposta": colar, "motivo": "collar"}
        return {"proposta": None, "motivo": "caixa_insuficiente"}
```
Per CONTEXT.md's MULTI-01 rule: when `multiperna=True` and `tipo == "put_protecao"`, the collar must be attempted UNCONDITIONALLY (not gated on `contratos < 1`), and the two outcomes (put_protecao dict if `contratos >= 1`, collar dict if `_propor_collar()` returns non-None) both get appended to a `candidatos` list, in that order (put_protecao first — see CONTEXT.md compatibility decision). `_propor_collar()` itself needs ZERO changes — it already takes `contrato_put` by parameter and returns `None`/a full dict, which is exactly the shape needed for a list append.

**Return-shape pattern to add** (new, aditivo — same style as how `estrutura`/`caixa`/`precoObjeto` were added in Phase 16 per CONTEXT.md's own framing):
```python
return {"proposta": <candidatos[0] or None>, "motivo": <candidatos[0]["tipo"] or negative-reason>, "candidatos": <list>}
```
This is NOT a new pattern to invent from scratch — it is the same "aditivo, campo novo, forma antiga preservada" discipline already used when `estrutura`/`caixa` were added to the single-candidate dict in Phase 16 (see docstring lines 164-173 of the current file, which explicitly narrates this kind of additive-capability history).

**Docstring/comment discipline to preserve** (this module's house style, present on every function in this file):
- Portuguese comments that narrate the WHY and cite the originating phase/plan (e.g. "Fase 16, Plano 03, LIB-03", "16-CONTEXT.md, decisão tomada com autonomia concedida") — new comments for the multi-candidate branch should cite "Fase 19, MULTI-01".
- Never invent a value — every early return has a named `motivo` string, never a silent `None`.
- `None` never `0.0` (see `opcoes_lastreadas.py:118-129` for the explicit rationale on why collar fields are `None`, not zero, when not applicable).

---

### `server/app/main.py` — `POST /api/options/lastreada/abrir-collar` (route, CRUD)

**Analog:** itself, `server/app/main.py:2506-2625` (current, Phase 17/ADR-026).

**Exact line that breaks and needs to change** (`main.py:2583`):
```python
if resultado.get("motivo") != "collar" or not resultado.get("proposta"):
    raise HTTPException(409, "O collar não está mais disponível — o servidor recalculou a "
                              "proposta e o resultado mudou.")
p = resultado["proposta"]
```
Must become a search inside `resultado["candidatos"]` for the entry with `tipo == "collar"`, e.g.:
```python
p = next((c for c in (resultado.get("candidatos") or []) if c.get("tipo") == "collar"), None)
if not p:
    raise HTTPException(409, "O collar não está mais disponível — o servidor recalculou a "
                              "proposta e o resultado mudou.")
```
Everything AFTER this point in the route (lines 2586-2625: contratos cross-check, `pernasContratos` cross-check, contract lookup in `chain`, `store.abrir_collar` call) is unchanged — it already operates on `p` as a local variable, agnostic to how `p` was obtained. This is the single point of change in this route; the surrounding "re-derive with `multiperna=True` fixed, never read from body" pattern (lines 2552-2581) is untouched and must stay untouched (ADR-026 Decision 2).

**Pattern to preserve — re-derivation discipline** (lines 2552-2559, comment already in the file, still applies verbatim):
```python
# RE-DERIVAÇÃO server-side (ADR-026, Decisão 2) — repete o pipeline do
# ramo B de `options_proposta` verbatim, com `multiperna=True` FIXO
# (nunca lido do corpo — ver guardião `test_rota_de_collar_nao_le_
# multiperna_do_corpo`).
```

---

### `server/app/main.py` — `POST /api/options/lastreada/abrir` (route, CRUD)

**Analog:** itself, `server/app/main.py:2443-2504`. **CONFIRMED NO CHANGE.** This route validates `contractSymbol` directly against the live chain (`chain.get("calls")`/`puts`, ~line 2478) and never calls `propor()`. Any `put_protecao`/`call_coberta` candidate the new multi-candidate UI offers already has its own `contractSymbol`, so this route accepts it unmodified. Included here only so the planner does not accidentally schedule a no-op task against it.

---

### `server/app/main.py` — `GET /api/options/proposta/{ticker}` (route, request-response)

**Analog:** itself, `server/app/main.py:2348-2440`.

**Current pass-through** (lines 2432-2440):
```python
return {
    "ticker": t, "providerStatus": provider_status, "modo": modo,
    "proposta": resultado["proposta"], "motivo": motivo, "motivoTexto": motivo_texto,
    "putSemLastro": put_sem_lastro_ids,
    "source": source, "at": now_str(),
}
```
Needs one additive key: `"candidatos": resultado.get("candidatos", [])`. Note this route has TWO branches producing `resultado` (the `pos_op_aberta` branch calling `opcoes_lastreadas.proposta_fechar()`, and the fresh-proposal branch calling `opcoes_lastreadas.propor()`). `proposta_fechar()` is a DIFFERENT function (line 339+ in `opcoes_lastreadas.py`, not touched by MULTI-01/02 per CONTEXT.md scope) and does not return a `candidatos` key — so `resultado.get("candidatos", [])` (not `resultado["candidatos"]`) is required to avoid a `KeyError` on the closing-a-position branch. This is the one place in the route layer where a defensive `.get()` with default matters more than the "never silently default" principle — it's a structural difference between two source functions, not a market-data failure being masked.

---

### `web/src/App.jsx` — `PropostaDaPosicao` (component, CRUD)

**Analog:** `OportunidadesOpcoes` (`web/src/App.jsx:3919-3981`) for the horizontal-scroll card pattern; `PropostaLastreada` (`web/src/App.jsx:3023-~3140`) for a single candidate's internal payoff/CTA layout; `PropostaDaPosicao` itself (`3992-4060`) for the position-scoped wiring (`onAbrirLastreada`/`onFecharLastreada`, `busy` state, `posAberta` lookup).

**Card/scroll pattern to reuse verbatim** (from `OportunidadesOpcoes`, `App.jsx:3938-3964` — per 19-UI-SPEC.md this is the ONLY visual pattern this phase may use, spacing/typography/color values are locked in the spec, not re-derived here):
```jsx
<div style={{ display: "flex", gap: "10px", overflowX: "auto", WebkitOverflowScrolling: "touch", scrollbarWidth: "none", paddingBottom: "2px" }}>
  {itens.map((p) => {
    const pr = propostas[p.t].proposta.proposta;
    const isCollar = pr.tipo === "collar";
    const isCall = pr.optionType === "call";
    const eyebrow = isCollar ? cp.eyebrowPropostaCollar : isCall ? cp.eyebrowPropostaCall : cp.eyebrowPropostaPut;
    const cor = isCall ? T.positive : T.negative;
    return (
      <button
        key={p.t}
        type="button"
        aria-label={p.t + " — " + cp.tiraOpcoesVerDetalhe}
        onClick={() => onAbrir(p.t)}
        style={{ flex: "0 0 auto", minWidth: "210px", minHeight: "44px", textAlign: "left", padding: "11px 12px", borderRadius: "11px", background: T.bgCard, border: `1px solid ${T.borderFaint}`, cursor: "pointer" }}
      >
        <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.accent }}>{eyebrow}</div>
        <div style={{ fontFamily: MONO, fontWeight: 800, fontSize: "13px", color: T.textPrimary, marginTop: "3px" }}>{p.t}</div>
        <div style={{ fontSize: "12.5px", fontWeight: 700, color: cor, marginTop: "4px", whiteSpace: "normal" }}>{pr.manchete}</div>
        <div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "6px" }}>{cp.tiraOpcoesVerDetalhe}</div>
      </button>
    );
  })}
</div>
```
Adapt: instead of `onAbrir(p.t)` navigating to a ticker's detail, each candidate item's click (or its own CTA button, per 19-UI-SPEC.md interaction decision) fires `onAbrirLastreada`/`onAbrirCollar`-equivalent parametrized by THAT candidate — see below.

**Current single-candidate accept wiring to parametrize** (`App.jsx:4015-4037`, `PropostaDaPosicao`'s own `onAbrirLastreada`):
```jsx
const onAbrirLastreada = async () => {
  if (!r || !r.proposta) return;
  const p = r.proposta;
  if (p.tipo === "collar") {
    if (!window.confirm(cp.confirmAbrirCollar(p.contratos, t, p.qtyAcoes))) return;
    setBusy(true);
    try {
      await A.abrirCollar({
        underlying: t,
        pernasContratos: (p.pernasContratos || []).map((perna) => ({ contractSymbol: perna.contractSymbol, lado: perna.lado })),
        contratos: p.contratos,
        expiration: p.expiration,
      });
    } finally { setBusy(false); }
    return;
  }
  if (p.optionType === "call" && !window.confirm(cp.confirmAbrirCoberta(p.contratos, t, p.qtyAcoes))) return;
  setBusy(true);
  try { await A.abrirLastreada({ underlying: t, contractSymbol: p.contractSymbol, expiration: p.expiration, contratos: p.contratos }); }
  finally { setBusy(false); }
};
```
This function closes over `r.proposta` (the single candidate). The N-candidate version needs the SAME body with `p` taken as a parameter (the clicked candidate from `r.candidatos`) instead of `r.proposta` — per CONTEXT.md MULTI-02, no new store function, same `A.abrirLastreada`/`A.abrirCollar`, same `busy` boolean shared across all candidates in this position (per 19-UI-SPEC.md Interaction Decision 1 — do NOT add per-candidate busy state).

**Guard clause to preserve exactly** (`App.jsx:4003`):
```jsx
if (!r || !r.proposta) return null;
```
Per 19-UI-SPEC.md, when `r.candidatos.length <= 1` behavior must be visually identical to today — this guard and the existing single-card render path (delegating to `PropostaLastreada`) stay the primary path; the N-candidate row is an ADDITIONAL branch gated on `r.candidatos && r.candidatos.length > 1`, not a replacement of the existing render.

**Copy functions to reuse, never invent new ones** (from `web/src/copy.js`, confirmed by 19-UI-SPEC.md Copywriting Contract): `cp.ctaPutProtecao`, `cp.ctaVendaCoberta`, `cp.ctaCollarCredito`, `cp.ctaCollarDebito`, `cp.eyebrowPropostaPut`, `cp.eyebrowPropostaCollar`, `cp.confirmAbrirCoberta`, `cp.confirmAbrirCollar`, `cp.linhaPropostaNaPosicao` (unchanged, no pluralization).

**Manchete guardrail to preserve** (comment at `App.jsx:3957-3959`, applies identically to each new candidate card):
```jsx
{/* manchete do motor, verbatim — guardrail CVM (CLAUDE.md);
    nunca truncada com reticências: cortar reescreveria a
    afirmação do motor. */}
```

---

## Shared Patterns

### Backend: additive dict-field discipline (never break old consumers)
**Source:** `server/app/opcoes_lastreadas.py:158-178` (docstring narrating the `multiperna` param's own additive-parameter precedent from Phase 16).
**Apply to:** `propor()`'s new `candidatos` key, `GET /api/options/proposta/{ticker}`'s response dict.
Pattern: new capability = new dict key with a safe default for old readers; NEVER change the meaning or type of an existing key. `proposta` stays `candidatos[0]` or `None`; `motivo` stays the primary candidate's `tipo` or the negative-reason string — old consumers (`AtivoCard`, `PropostaLastreada`, `GET /api/options/proposta/{ticker}`'s old shape, `POST .../abrir`) need zero changes.

### Backend: `None` never `0.0` (repo-wide house rule)
**Source:** `server/app/opcoes_lastreadas.py:118-129` (collar fields explicitly `None` when not applicable, with rationale comment); reinforced by `server/tests/test_m3_format_pede_null_nunca_zero` (guardian cited in CLAUDE.md's Return Values convention).
**Apply to:** any new field on a `candidatos[i]` dict that doesn't apply to that candidate's type.

### Backend: named `motivo` strings, no silent failure
**Source:** every early return in `opcoes_lastreadas.propor()` (`degradado`, `sem_lastro`, `sem_setup`, `sem_vencimento_elegivel`, `sem_contrato_liquido`, `caixa_insuficiente`).
**Apply to:** empty-`candidatos` case (both structures fail) must still produce `motivo="caixa_insuficiente"` (or whichever applies) exactly as today — MULTI-01 does not add a new negative-motivo vocabulary entry, it reuses the existing one for the "zero candidatos fit" case.

### Backend: route-layer defense-in-depth re-validation (ORDER_LOCK)
**Source:** `store.abrir_call_coberta`/`store.comprar_put_protecao`/`store.abrir_collar` (referenced throughout `main.py` and `opcoes_lastreadas.py` comments) — validate lastro/caixa AGAIN under `ORDER_LOCK` at execution time, never trusting what a displayed proposal claimed.
**Apply to:** MULTI-02's "accepting one candidate must reject the sibling" requirement — CONTEXT.md is explicit this needs NO new guard code, only a NEW TEST proving the existing lock-time validation already produces the rejection. Do not add a new lock/flag; write the test against the existing `ValueError` path.

### Frontend: manchete verbatim, never `T.accent` on headline
**Source:** `App.jsx:3038` (`PropostaLastreada`) and `App.jsx:3944-3946` (`OportunidadesOpcoes`) — both carry the identical comment "nunca T.accent na linha da manchete", polarity signaled by `T.positive`/`T.negative` only.
**Apply to:** every candidate card in the new N-candidate row.

### Frontend: single shared `busy` boolean per position, not per candidate
**Source:** `PropostaDaPosicao`, `App.jsx:3996` (`const [busy, setBusy] = useState(false);`), confirmed in 19-UI-SPEC.md Interaction Decision 1 as the correct behavior to keep (falls out of existing code structure — do not add per-candidate state).
**Apply to:** all candidate CTA buttons within one `PropostaDaPosicao` instance.

### Frontend: flash/toast error surfacing, no new inline card message
**Source:** `App.jsx:8076` (`flash("Abrir operação lastreada: " + e.message)`), `App.jsx:8088` (`flash("Montar collar: " + e.message)`).
**Apply to:** the stale-sibling-rejected-on-accept case (19-UI-SPEC.md Interaction Decision 1) — reuse this exact mechanism, do not build a new inline "no longer available" message.

---

## Tests — Pattern Assignments

### Backend: `server/tests/test_opcoes_collar.py`

**Analog:** itself, existing fixtures `_contrato`/`_cadeia`/`_posicao`/`_PLANO_VENDER` (lines 30-49), and the existing multiperna-gate tests (lines 61-101).

**⚠ Guardian requiring an explicit update, not silent breakage** — per CLAUDE.md's repo guardrail ("Guardiões de teste não se apagam — reversão deliberada atualiza o guardião com nota"), this exact test WILL fail once MULTI-01 ships and needs a documented update, not a delete-and-forget:
```python
def test_propor_multiperna_true_com_caixa_folgado_mantem_put_protecao():
    """O collar não rouba o caso em que a put isolada cabe no caixa."""
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(), 100000, "operador", _HOJE, multiperna=True)
    assert r["motivo"] == "put_protecao"
```
This currently asserts the collar is NOT offered when the put alone fits in cash. MULTI-01 makes both coexist when both fit AND a liquid call exists above spot — but this fixture has NO calls in the chain (`_cadeia(puts=puts)`, no `calls=`), so `_propor_collar()` still returns `None` (no liquid call found) and `r["motivo"] == "put_protecao"` remains TRUE even after the change — this specific guardian likely does NOT need to change, but the planner/executor MUST verify this explicitly (add a comment noting it was re-verified post-MULTI-01, per the guardian-update convention) rather than assuming it silently still passes.

**New test needed (coexistence)** — closest analog is `test_propor_multiperna_true_oferece_collar_quando_put_nao_cabe` (lines 69-76), inverted to a chain where BOTH structures fit:
```python
def test_propor_multiperna_true_com_caixa_e_call_liquida_ambos_coexistem():
    """MULTI-01: quando put E collar cabem, os DOIS aparecem em candidatos,
    put_protecao primeiro (índice 0, compat. com consumidor antigo de .proposta)."""
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(), 100000, "operador", _HOJE, multiperna=True)
    assert [c["tipo"] for c in r["candidatos"]] == ["put_protecao", "collar"]
    assert r["proposta"]["tipo"] == "put_protecao"  # backward-compat: index 0
    assert r["motivo"] == "put_protecao"
```

### Backend: `server/tests/test_opcoes_collar_rota.py`

**Analog:** itself — `test_collar_aceito_com_proposta_fresca_executa_as_duas_pernas` (line 192) for the happy-path fixture wiring (`_expiracao_fixa`, `_snapshot_sem_setup`, `_plano_vender` fixtures at the top of the file, not read in full here but referenced by every test in this file per the grep above).

**New test needed** — per CONTEXT.md: "um teste que prova `abrir-collar` aceitando um collar que NÃO é o candidato primário da lista." Follow the same TestClient POST pattern as `test_collar_aceito_com_proposta_fresca_executa_as_duas_pernas`, but arrange the fixture chain so `candidatos[0]` is `put_protecao` and `candidatos[1]` is `collar`, then POST the collar's `pernasContratos`/`contratos` and assert 200 (not 409) — proving the `abrir-collar` route's fixed line 2583 check now searches `candidatos` by `tipo == "collar"` instead of assuming `motivo == "collar"`.

### Backend: sibling-rejection test (MULTI-02 criterion 3)

**Analog:** none exists yet for this exact scenario (accept-one-then-try-accept-other), but the mechanism it tests (`ORDER_LOCK`-guarded re-validation) is exercised indirectly by existing store-level tests in `server/tests/test_opcoes_lastreadas_store.py`/`test_opcoes_collar_execucao.py` (files not read in full — grep-confirmed to exist, same test-file-per-feature convention). New test: accept candidate A (put_protecao) via `POST /api/options/lastreada/abrir`, then attempt to accept candidate B (collar) on the SAME position via `POST /api/options/lastreada/abrir-collar`, assert the second call fails with the store's existing `ValueError`-derived message (400/409, whichever the affected leg's guard already raises) — no new guard code, per CONTEXT.md's explicit instruction.

### Frontend: `web/tests/*.mjs`

**Analog:** `web/tests/test_opcoes_collar_ui.mjs` (static-source-grep style, `readFileSync` + regex/balanced-brace extraction against `App.jsx`, `persistence.js`, `api.js` — NOT a rendering test, this codebase has no component test runner). New assertions for Phase 19 should follow the identical style: `ok(name, condition)` helper, `extrairBalanceado` for locating a function body, regex checks that both `A.abrirLastreada` and `A.abrirCollar` calls exist within the N-candidate render path, and that no candidate's manchete is composed (still reads `pr.manchete`/`p.manchete` verbatim, never string-concatenated). Must run via `node web/tests/test_opcoes_multi_candidato_ui.mjs` (new file, following the one-file-per-feature convention) and be included in `scripts/executar.sh --testes`'s discovery (confirm the script auto-discovers `web/tests/*.mjs` — no registration list to update, per the existing pattern of `test_opcoes_collar_ui.mjs` needing no separate wiring).

---

## No Analog Found

None. This phase extends existing, actively-maintained files within the same feature family (Phases 14/16/17/18); no new architectural surface is introduced.

---

## Metadata

**Analog search scope:** `server/app/opcoes_lastreadas.py`, `server/app/main.py` (options routes section, ~lines 2340-2630), `web/src/App.jsx` (options proposal component cluster, ~lines 3000-4130, and the `A.*` action dispatch object, ~lines 8060-8098), `server/tests/test_opcoes_*.py` (11 files), `web/tests/test_opcoes_*.mjs` (4 files).
**Files scanned:** ~10 (targeted, non-overlapping reads at CONTEXT.md-verified line ranges plus the immediately-adjacent code needed for full context, e.g. the tail of `abrir-collar` at 2596-2625 and `PropostaLastreada`'s CTA branch at 3111-~3140).
**Pattern extraction date:** 2026-09-03
