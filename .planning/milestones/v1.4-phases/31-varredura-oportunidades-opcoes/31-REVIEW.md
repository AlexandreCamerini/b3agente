---
phase: 31-varredura-oportunidades-opcoes
reviewed: 2026-09-14T00:00:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - server/app/opcoes_curadoria.py
  - server/app/skill_ref.py
  - server/tests/test_opcoes_curadoria.py
  - server/app/main.py
  - server/app/options_provider_mydata.py
  - server/tests/test_opcoes_curadoria_rota.py
  - server/tests/test_options_provider_mydata.py
  - web/src/opcoes/PayoffChart.jsx
  - web/tests/test_payoff_responsivo.mjs
  - web/src/opcoes/estruturaParaPayoff.js
  - web/tests/test_estrutura_para_payoff.mjs
  - web/src/copy.js
  - web/src/App.jsx
  - web/tests/test_curadoria_ui.mjs
findings:
  critical: 0
  warning: 3
  info: 1
  total: 4
status: issues_found
---

# Phase 31: Code Review Report

**Reviewed:** 2026-09-14
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Reviewed the four plans of Phase 31 (deterministic 4-structure curation engine
in `opcoes_curadoria.py`, the `mydata` chain provider's date-based expiration
fix + expiration-list cache, the responsive `PayoffChart`, and the Posições
"4 melhores oportunidades" block in `App.jsx`). This is disciplined, heavily
self-documented code: every hard invariant named in the task (deterministic
ranking never touched by the LLM, `exigir_ranking()` as a structural gate
before narration, manchete rendered verbatim with a static guardian banning
composition/truncation, the D-05 `permitirOpcaoADescoberto` gate re-checked
server-side in both routes and independently at `store.buy_option` execution
time, "null never 0.0" honored end-to-end through the JS adapter) is actually
enforced in code, not just asserted in a docstring, and each is backed by a
targeted regression test (`test_opcoes_curadoria_rota.py`,
`test_curadoria_ui.mjs`, `test_estrutura_para_payoff.mjs`). I traced the
ranking math, the collar/put/naked-call branches, the mydata vencimento
selection + budget-gate interaction, and the two routes' handling of a
client-supplied `config` body, and did not find a violation of the CVM
manchete guardrail, the D-05 opt-in gate, or the "never fabricate on
failure" principle.

What I did find is a set of three related front-end gaps: a fetch-failure
state the component receives but never renders (so a real network/store
failure is indistinguishable on screen from "no eligible structures"), an
explanatory copy string that exists, is tested for parity, but is never
wired into the render (the one nuance a user most needs — negative premium
in the "4 best" ranking is by design, not a bug), and a data hook that never
revalidates after mount, unlike its sibling hook one screen element above it.
None of these touch a financial number or the CVM/D-05 guardrails; all are
quality/UX defects that should be fixed before shipping this screen to
production users who are meant to trust "as 4 melhores" as current.

## Warnings

### WR-01: `erro` (fetch failure) state is captured but never rendered — a real failure looks identical to "no eligible structures"

**File:** `web/src/App.jsx:4560-4608` (state) and `web/src/App.jsx:4197-4310` (`CuradoriaEstruturas` render)

**Issue:** `useCuradoria()` sets `erro=true` when `store.opcoesCuradoria()` rejects (`.catch(() => { if (aliveRef.current) setErro(true); })`, line 4582), and this `erro` value is threaded all the way down as the `erro` prop into `CuradoriaEstruturas` (destructured at line 4197: `{ top, meta, carregando, erro, narrativa, ... }`). The prop is never read anywhere inside the component body. The empty-state branch fires purely on `top.length === 0 && !carregando` (line 4275), so a genuine network/store failure renders the exact same box and copy as a successful-but-empty response: `cp.curadoriaVazio` = *"Nenhuma estrutura elegível nos vencimentos varridos — por isso não há nada para ranquear agora."* That sentence asserts a fact (the varredura ran and found nothing) that is false when the fetch itself failed. This sits in tension with CLAUDE.md principle 4 ("se a fonte de dados falhar... mostre o estado correto") — the state shown is not the correct one for a fetch failure.

`test_curadoria_ui.mjs` has no assertion touching `erro`/error-state rendering, so nothing currently guards this gap.

**Fix:** Either wire a distinct branch (`top.length === 0 && !carregando && erro && <...texto de falha.../>`) with its own copy key (mirroring the `erroNarrativa` "cota"/"erro" split already used lower in the same component), or — if silent best-effort degradation to the empty state is the deliberate product choice (as it is in the sibling `useOpcoesPropostas`, which also swallows errors) — remove the dead `erro` state/prop plumbing so a future reader doesn't assume it's wired in. Either fix removes the current worst outcome: a misleading factual claim on data-source failure.

### WR-02: `curadoriaRazaoAjuda` copy exists, is guardian-tested, but is never rendered — the one explanation for D-06 (negative premium ranking low) never reaches the user

**File:** `web/src/copy.js:624` (estudo), `web/src/copy.js:1137` (operador); render site `web/src/App.jsx:4253` (`CuradoriaEstruturas`)

**Issue:** `curadoriaRazaoAjuda` was added in this phase specifically to explain D-06 ("Prêmio negativo significa que montar a estrutura custa dinheiro (é uma proteção) — por isso ela pode aparecer embaixo na mesma régua, sem que isso seja um defeito do ranking."). `test_curadoria_ui.mjs` asserts the key exists in both `COPY.estudo`/`COPY.operador` (parity check, lines 101-112) and is non-promotional, but no assertion checks that it is actually *displayed*. Grepping `App.jsx` confirms `cp.curadoriaRazaoAjuda` is never referenced — only `cp.curadoriaRazaoRotulo` is used, at line 4253 (`{cp.curadoriaRazaoRotulo}: {item.razao...}`). Compare the sibling screen: `cp.opcoesRazaoAjuda` (the near-identical string for `OpcoesScreen`) *is* rendered, at `web/src/opcoes/OpcoesScreen.jsx:98`. This strongly suggests the wiring for `curadoriaRazaoAjuda` was planned (it's even called out by name in the copy.js comment block explaining the 7 new keys of this phase, line 613) but the render call site was never added.

**Impact:** Because put_protecao/collar-de-débito/opcao_a_descoberto candidates can legitimately show a negative "razão" near the bottom of the "4 melhores oportunidades" ranking (by design, D-06), a user has no on-screen explanation for why a structure that "costs money" appears in a list titled "AS 4 MELHORES OPORTUNIDADES DE OPÇÕES" — reads as a ranking bug to anyone not aware of the doctrine documented in code comments.

**Fix:** Render `cp.curadoriaRazaoAjuda` next to (or below) the razão line in `CuradoriaEstruturas`, mirroring how `OpcoesScreen.jsx:98` renders `cp.opcoesRazaoAjuda`, e.g.:
```jsx
<div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "6px" }}>{cp.curadoriaRazaoRotulo}: {item.razao != null ? item.razao.toFixed(2) : "—"}</div>
{cp.curadoriaRazaoAjuda && (
  <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "2px", lineHeight: 1.4 }}>{cp.curadoriaRazaoAjuda}</div>
)}
```

### WR-03: `useCuradoria()` never revalidates after mount — the "4 melhores" list and its payoff chart can silently go stale while the tab stays open

**File:** `web/src/App.jsx:4571-4585` (`useCuradoria`'s `useEffect`)

**Issue:** The `useEffect` that fetches `/api/options/curadoria` has an empty dependency array (`}, []);`, line 4585) — it fires exactly once per mount of `CarteiraScreen` and never again. Compare its sibling one line above in the same screen, `useOpcoesPropostas(data.positions.map((p) => p.t))` (line 4627), whose effect depends on the joined ticker string (`chave`, line 4511) and therefore re-fetches whenever the set of position tickers changes. `CuradoriaEstruturas` is rendered inside `CarteiraScreen`, which stays mounted for as long as the user stays on the "carteira" tab (`{tab === "carteira" && (...)}`, `App.jsx:9630`) — it does not unmount on every data refresh, only on tab switch. Positions can change while this tab is open without a tab switch: the autonomous Operador (`agent.py` scheduler, stop/alvo execution) runs server-side and can free or lock `qtyLivre` on a position at any time, and `data` (portfolio state) is generally kept live by polling elsewhere in the app. When that happens, the previously-fetched `top`/`meta` (and the payoff chart drawn from `top[0].estrutura`) keep describing a portfolio state that may no longer exist — e.g., a `call_coberta` candidate sized against shares that a stop/alvo cycle has since sold, or a newly-eligible position (just crossed the 100-share free-lot threshold) that never gets picked up until the user leaves and re-enters the tab.

This is not a violation of any hard invariant (the numbers shown were correct *at fetch time*, and the route itself is best-effort/degrade-safe), but it is a real staleness gap with no user-visible cue, in a screen whose entire premise is "here is what the deterministic motor thinks is currently the best" — and it's inconsistent with the precedent set one hook above it in the same file.

**Fix:** Either add `data.positions.map((p) => p.qtyTravada + ":" + p.t).join(",")` (or an equivalent primitive summarizing lot-freedom, matching the `chave` pattern of `useOpcoesPropostas`) as an effect dependency so the block revalidates when the portfolio actually changes, or add a lightweight "atualizado às HH:MM — toque para atualizar" affordance so staleness is at least visible instead of silent.

## Info

### IN-01: Vencimento-cache key format duplicated in two places (`options_provider_mydata.py`)

**File:** `server/app/options_provider_mydata.py:248` (inside `_vencimentos`) and `server/app/options_provider_mydata.py:282` (pre-filter in `get_options`)

**Issue:** The cache key `f"{t}@{hoje_efetivo.isoformat()}"` for `_venc_cache` is constructed independently at two call sites instead of through one shared helper. Both currently agree, and the test suite (`test_duas_cadeias_mesmo_ticker_mesmo_dia_custam_3_requisicoes_nao_4` et al.) would catch a drift in practice — but if either literal is edited in isolation during a future change, the pre-filter in `get_options` silently stops matching the cache populated by `_vencimentos`, degrading the `_gate(1)` fast path back to the pessimistic `_gate(2)` without any test failure pointing at the actual cause (both remain individually "correct" against the same wrong assumption).

**Fix:** Factor a small `_venc_cache_key(t, hoje_efetivo)` helper and use it at both sites.

---

_Reviewed: 2026-09-14_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
