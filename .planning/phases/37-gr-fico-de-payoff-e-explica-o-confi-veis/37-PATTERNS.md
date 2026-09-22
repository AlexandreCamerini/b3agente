# Phase 37: Gráfico de Payoff e Explicação Confiáveis - Pattern Map

**Mapped:** 2026-09-21
**Files analyzed:** 11 (2 backend modify, 1 backend analog-only, 6 frontend modify/new, 1 copy, plus test files)
**Analogs found:** 11 / 11

---

## CRITICAL ARCHITECTURE FINDING (read before planning)

UI-SPEC.md §0 flags an "open gap, not solved by this document": which backend
route actually wires `dominio_da_curva()`/`segmentos_da_curva()` (Fase 36,
`server/app/opcoes_payoff.py`) into what `PayoffChart.jsx` receives. This
pattern-mapping pass resolves it concretely, and the answer changes the shape
of the backend plan:

**`PayoffChart.jsx`'s 3 consumers use TWO unrelated data paths, not one:**

| Consumer | Route / call chain | Data shape at the point `estrutura` is built |
|---|---|---|
| `CuradoriaEstruturas.jsx` (`payoffPrimeiro`, line 152/291) | Local motor: `opcoes_curadoria.py` → `opcoes_motor.avaliar()` → `opcoes_payoff.perfil_da_estrutura()` (`server/app/opcoes_curadoria.py:253/330/393/494`) | **PT-keyed**, exactly the `perfil` dict `dominio_da_curva()`/`segmentos_da_curva()` already accept as input (`pernas`, `curva`, `ganho_maximo`, `ganho_ilimitado`, …) — zero adapter needed to call these functions here. Reaches `PayoffChart` only via `estruturaParaPayoff.js` (PT→EN, one-way, arithmetic-forbidden). |
| `SecaoAnalisar.jsx` (line 390) | `POST /api/options/mcp/proposta` (`options_mcp_api.py:2200`, handler `proposta()`) ← MCP tool `propose_option_setups` directly, **no `evaluate_option_structure` call, no local motor at all** | **EN-keyed already**, external mydata service schema (`dados.get("setups")`) |
| `SecaoComparar.jsx` (line 221) | `POST /api/options/mcp/possibilidades` (`options_mcp_api.py:2273`, handler `possibilidades()`) ← MCP tools `propose_option_setups` + `evaluate_option_structure`, filtered through `CHAVES_DA_ESTRUTURA` allowlist (line 281, applied at line 2404) | Same EN-keyed external-service schema as above |

**Consequence for this phase:** D-09 puts the two NEW blocks (EXPL-01/02/03,
CHART-05) exclusively on `SecaoAnalisar`/`SecaoComparar` — i.e. exclusively on
the **MCP path**, never the local-motor path. `dominio_da_curva()`/
`segmentos_da_curva()` cannot be called AS-IS on the MCP-sourced dict — its
top-level keys are EN (`max_gain`, `unlimited_gain`, `payoff`) where the two
functions expect PT (`ganho_maximo`, `ganho_ilimitado`, `curva`).

**Verified against real fixtures — the data needed for a straightforward
adapter is present, contrary to an initial read of the outbound-request
shape.** `_pernas_para_avaliar()` (`options_mcp_api.py:1454-1475`) builds a
STRIPPED-DOWN outbound request to `evaluate_option_structure`
(`{contract, side, quantity}` only — that's what's SENT). But the RESPONSE
the tool echoes back is richer: `server/tests/fixtures/mcp_evaluate_petr4.json`
(the offline fixture `test_options_mcp_api.py` replays for `evaluate_option_structure`)
shows `legs` in the response carrying `strike`, `kind` (`CALL`/`PUT`), `side`,
`quantity`, `premium`, `delta`, `expiration` — full per-leg data, not opaque
contract codes. Likewise `propose_option_setups`'s own `setups[].legs`
(`test_options_mcp_api.py:154-159`, `_setup()` fixture) already carries
`strike`/`kind`/`premium`/`delta` too. And `payoff` in both fixtures is a
list of `{underlying, result}` points — the exact EN-renamed twin of
`perfil["curva"]`'s `{preco_objeto, resultado}` points that
`segmentos_da_curva()` consumes.

**This means the practical resolution is a small EN→PT field-rename adapter
— the INVERSE of `estruturaParaPayoff.js`'s existing PT→EN pattern, applied
only to the handful of fields `dominio_da_curva()`/`segmentos_da_curva()`
need** (`legs[].strike`/`kind` → `pernas[].strike`/`tipo`, `max_gain` →
`ganho_maximo`, `unlimited_gain` → `ganho_ilimitado`, `payoff` → `curva`,
etc.), followed by calling the two Fase-36 functions **verbatim, unchanged**
— not a reimplementation of their algorithm against curve break-points (the
weaker alternative considered and now deprioritized). This keeps the
"cálculo determinístico numa fonte só" guarantee intact: the arithmetic
stays in `opcoes_payoff.py`; the new code in `options_mcp_api.py` only
renames keys, same discipline `estruturaParaPayoff.js` already models on the
frontend, and same "compute once, attach to envelope" placement as
`_em_reais`/`_razao_ganho_perda` (see Pattern Assignments below). The
planner still owns the concrete shape of this adapter (where it lives,
whether inline or a named helper) — this pattern map narrows it to "small
rename, call existing functions," not "new algorithm."

Whichever exact shape the planner gives it, the wiring point in code is the
**same pattern already used for `emReais`/`razaoGanhoPerda`**: compute once
server-side, attach to the envelope, verbatim to the front — see
`_em_reais`/`_razao_ganho_perda` pattern below (§ Pattern Assignments,
`options_mcp_api.py`).

**Spot value (also flagged as unresolved by UI-SPEC §0) — resolved:** both
`proposta()` (line 2254) and `possibilidades()` (line 2330) envelopes already
carry `"precoObjeto": dados.get("underlying_price")` — the same live quote
the MCP `propose_option_setups` call returns. This is the `spot` argument
`dominio_da_curva(perfil, spot)` expects; no second fetch is needed for the
spot value itself (CHART-05's "hoje" block is a *separate* new fetch,
`get_option_chain`, for mark-to-market premium — not for spot).

**`estruturaParaPayoff.js` is NOT on the call path for the two files that
need the new props.** It stays relevant only as the "regex-forbids-arithmetic
guardian test" pattern to imitate — both for its own future extension (if
`CuradoriaEstruturas.jsx` ever gets the new blocks) and as the structural
template for the NEW EN→PT adapter this phase likely needs in
`options_mcp_api.py` (rename-only, zero arithmetic, same discipline).

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `server/app/options_mcp_api.py` (`proposta`, `possibilidades` handlers) | route/service (FastAPI) | request-response, external-service passthrough | itself — `_em_reais`/`_razao_ganho_perda`/`CHAVES_DA_ESTRUTURA` (compute-once-attach-verbatim pattern already in this file) | exact |
| `server/app/opcoes_payoff.py` | service (pure calc) | transform | itself — `dominio_da_curva`/`segmentos_da_curva` already exist (Fase 36); no new backend module needed, only new call sites (via a small EN→PT adapter in `options_mcp_api.py`) | exact (analog = itself) |
| `web/src/opcoes/PayoffChart.jsx` | component (SVG) | request-response (props in, render out) | itself — extending existing component, not creating new | exact |
| `web/src/opcoes/estruturaParaPayoff.js` | utility/adapter | transform (pure, PT→EN) | itself — extending with new keys, same zero-arithmetic discipline; also the structural TEMPLATE for the new EN→PT backend adapter (see Critical Architecture Finding) | exact |
| `web/src/opcoes/uiOpcoes.jsx` | component (shared UI primitives) | request-response | itself — `RazaoGanhoPerda`/`ErroDoMcp`/`Kicker`/`Aviso` already here | exact |
| `web/src/opcoes/ExplicacaoPayoff.jsx` (NEW) | component (pure, template text) | transform | `web/src/finance.js` / `web/src/plan.js` (pure functions, no I/O) for the "pure function" discipline; `uiOpcoes.jsx`'s `RazaoGanhoPerda` for the "reads a `cp`-driven template, renders prose in an `Aviso` box" shape | role-match (calc purity) + exact (visual/prop shape) |
| `web/src/opcoes/CuradoriaEstruturas.jsx` | component | request-response | itself — single-line copy-key rename only | exact |
| `web/src/opcoes/SecaoAnalisar.jsx` | component | request-response | itself — extending existing `PayoffChart`/`RazaoGanhoPerda` call site | exact |
| `web/src/opcoes/SecaoComparar.jsx` | component | request-response | itself — extending existing `PayoffChart`/`RazaoGanhoPerda` call site | exact |
| `web/src/copy.js` | config (i18n/vocabulary) | CRUD (key-value) | itself — existing `cp.opcoes*` Estudo/Operador key pairs | exact |
| `server/tests/test_opcoes_payoff.py` | test | — | itself — existing `dominio_da_curva`/`segmentos_da_curva` test blocks (golden case already there) | exact |
| `server/tests/test_options_mcp_api.py` | test | — | itself — existing `proposta`/`possibilidades` route tests, plus `server/tests/fixtures/mcp_evaluate_petr4.json` for the response shape a new EN→PT adapter test should assert against | exact |
| `web/tests/test_estrutura_para_payoff.mjs` | test (guardian, static regex) | — | itself | exact |
| `web/tests/test_payoff_responsivo.mjs` | test (SVG geometry) | — | itself | exact |
| new `web/tests/test_explicacao_payoff.mjs` (proposed) | test | — | `web/tests/test_estrutura_para_payoff.mjs` (pure-function, plain input/output assertions, no DOM/build) | role-match |

---

## Pattern Assignments

### `server/app/options_mcp_api.py` — `proposta()`/`possibilidades()` handlers

**Analog:** itself (`_em_reais`, `_razao_ganho_perda`, `CHAVES_DA_ESTRUTURA` verbatim-copy)

**Compute-once-attach-verbatim pattern** (`options_mcp_api.py:1289-1323`, `_em_reais`):
```python
def _em_reais(dados: dict, lote: int) -> dict:
    dados = dados if isinstance(dados, dict) else {}
    ...
    return {
        "lote": lote,
        "custoLiquido": _vezes_lote(dados.get("net_cost"), lote),
        "ganhoMaximo": _vezes_lote(dados.get("max_gain"), lote),
        "perdaMaxima": _vezes_lote(dados.get("max_loss"), lote),
        "cenarios": cenarios,
        "unidade": "reais para o lote informado (lote = número de ações)",
    }
```
New `valor_hoje`/domain/segments fields follow the exact same shape: a
private `_algo(dados: dict, ...) -> dict` helper, called once per structure,
attached to the response envelope at the same level as `emReais`/
`razaoGanhoPerda` — never inline in the route body.

**EN→PT adapter needed for `dominio_da_curva`/`segmentos_da_curva`** — new
helper, structurally mirroring `estruturaParaPayoff.js`'s rename-only
discipline but in the opposite direction, e.g.:
```python
def _perfil_para_dominio(avaliacao: dict) -> dict:
    """Traduz o envelope EN do serviço MCP para o formato PT que
    `opcoes_payoff.dominio_da_curva`/`segmentos_da_curva` esperam.
    Zero aritmética: só renomeia chave — mesma disciplina de
    `estruturaParaPayoff.js`, sentido inverso."""
    legs = avaliacao.get("legs") or []
    return {
        "pernas": [{"strike": p.get("strike"), "tipo": p.get("kind")} for p in legs
                   if isinstance(p, dict)],
        "ganho_maximo": avaliacao.get("max_gain"),
        "perda_maxima": avaliacao.get("max_loss"),
        "ganho_ilimitado": avaliacao.get("unlimited_gain"),
        "perda_ilimitada": avaliacao.get("unlimited_loss"),
        "curva": [{"preco_objeto": pt.get("underlying"), "resultado": pt.get("result")}
                  for pt in (avaliacao.get("payoff") or []) if isinstance(pt, dict)],
        "vencimentos": {"divergentes": False},  # já resolvido pelo próprio serviço
    }
```
(Exact shape/placement is the planner's call — this sketch exists to prove
the adapter is small and rename-only, evidenced by
`server/tests/fixtures/mcp_evaluate_petr4.json` having `strike`/`kind` on
every leg and `payoff` as `{underlying, result}` points.) Once adapted,
`dominio_da_curva(perfil_adaptado, spot=dados.get("underlying_price"))` and
`segmentos_da_curva(perfil_adaptado)` are called **verbatim, unmodified**.

**Verbatim-allowlist-copy pattern** (`options_mcp_api.py:281-285`, `2404-2409`):
```python
CHAVES_DA_ESTRUTURA = (
    "kind", "name", "legs", "net_cost", "flow", "max_gain", "max_loss",
    "unlimited_gain", "unlimited_loss", "breakevens", "net_delta",
    "payoff", "scenarios", "sessions_to_nearest_expiry", "note",
)
...
estrutura = {c: avaliacao.get(c) for c in CHAVES_DA_ESTRUTURA}
```
The new `dominio`/`segmentos` fields (output of the adapter above, EN-cased
to match `PayoffChart`'s prop contract per UI-SPEC §0) get merged into the
envelope the same way `emReais`/`razaoGanhoPerda` are (line 2265-2267,
2416-2419) — a **sibling key, not inside `CHAVES_DA_ESTRUTURA`**, matching
how `razaoGanhoPerda` is deliberately kept OUT of `emReais`'s dict (F-01,
comment at line 1283-1288: "breakeven é PREÇO, não dinheiro... campo fica
FORA de `emReais`").

**Existing `get_option_chain` call pattern for CHART-05's new fetch**
(`options_mcp_api.py:2084`, inside the `/cadeia/{ticker}` route):
```python
with _cap_check(uid, 1) as cap:
    rota = "/api/options/mcp/cadeia/{ticker}"
    try:
        dados, cache = await _chamada_com_cap(cap, "get_option_chain", args)
    except (mcp_client.McpErro, ValueError) as e:
        obslog.log("mcp", "cadeia falhou", level="warn", rota=rota, uid=uid,
                   ticker=alvo, erro=type(e).__name__, detalhe=str(e))
        raise _erro_http(e)
```
The new "valor hoje" fetch (D-01) reuses `_chamada_com_cap(cap, "get_option_chain", args)` inside the existing `with _cap_check(...)` reservation
pattern — same cost/cap discipline as every other MCP call in this file.
Per D-01, the backend then sums current premium × side × quantity per leg —
same "lote multiplica fora" discipline as `_vezes_lote`/`_em_reais` (never a
second implementation of that arithmetic).

**Error handling pattern** (`options_mcp_api.py:1131-1185`, `_chamada_com_cap`,
and every route's `try/except (mcp_client.McpErro, ValueError)` → `raise
_erro_http(e)`): the new "hoje" fetch failing must NOT fail the whole route —
per D-01/CONTEXT.md, only the "hoje" block degrades. This means the new fetch
needs its OWN try/except **inside** the route (not the route-level
`except` that aborts everything), catching `mcp_client.McpErro` and turning
it into an inline `{"erro": {...}}` value on the `valorHoje` field rather than
raising — a narrower-scoped variant of the existing pattern, not a copy of
the outer one.

---

### `server/app/opcoes_payoff.py`

**Analog:** itself — `dominio_da_curva()` (line 297-386) and `segmentos_da_curva()` (line 389-446) already exist, Fase 36, fully tested (`server/tests/test_opcoes_payoff.py:511-749`, golden case at line 671). No new backend calculation module or algorithm is needed for EITHER data path — see Critical Architecture Finding: the MCP path just needs a small EN→PT rename adapter in `options_mcp_api.py`, then calls these two functions verbatim.

**Null-never-zero pattern** (`opcoes_payoff.py:371-374`):
```python
# Nunca `0.0` no lugar de "sem teto" (docstring do módulo, linhas 13-17):
# lado ilimitado sinaliza `None`, quem desenha a seta é a Fase 37.
y_max = None if ganho_ilimitado else round(max(perfil["ganho_maximo"], 0.0) * 1.15, 4)
y_min = None if perda_ilimitada else round(-max(perfil["perda_maxima"], 0.0) * 1.15, 4)
```

**`motivo` non-null-on-degradation pattern** (`opcoes_payoff.py:312-320`, divergent-expirations branch): the adapter feeding these functions from the MCP path should set `"vencimentos": {"divergentes": False, ...}` confidently (the external service already resolves a single evaluated structure, so this branch shouldn't fire) but must not silently swallow a `None`/missing field — pass `None` through untouched rather than defaulting to a number, exactly as `_vezes_lote` already does (`options_mcp_api.py:1274-1280`).

---

### `web/src/opcoes/PayoffChart.jsx`

**Analog:** itself (extend, do not recreate)

**New optional props, fallback-safe pattern** — model on the EXISTING optional-prop pattern already in the file (`PayoffChart.jsx:185`, `emReais ? (...) : null`):
```jsx
{emReais ? (
  <div style={{ ... }}>
    {(c.opcoesEmReaisRotulo || "em reais") + ": custo " + moeda(emReais.custoLiquido) + ...}
  </div>
) : null}
```
`dominio`/`segmentos`/`valorHoje` follow the same null-safe optional-chain
style; `dominio` additionally needs a **fallback to the existing local
`useMemo` domain calc** (`PayoffChart.jsx:100-160`) when `dominio.xMin`/etc
are null — UI-SPEC §0 states this explicitly and it is what keeps
`CuradoriaEstruturas.jsx` unbroken without any wiring work there.

**Token/geometry constants to extend, not replace** (`PayoffChart.jsx:31-48`):
```jsx
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "textFaint", "accent", "accentTint10", "negative", "scrim"];
const W = 320, H = 192;
const PAD_E = 10, PAD_D = 10, PAD_T = 18, PAD_B = 32;
const FONTE_MIN = 11.5;
```
UI-SPEC §1.1 requires `PAD_E: 10 → 48`. Zero new tokens (UI-SPEC Color
section is explicit: reuse only what's in `TOKENS` already).

**Collision-suppression pattern to REUSE for strike marks (CHART-02)**
(`PayoffChart.jsx:284-301`, breakeven rendering — this is the algorithm
UI-SPEC §1.2 says to merge strikes into, not duplicate):
```jsx
{(() => {
  const ordenadas = [...marcas].sort((a, b) => sx(a) - sx(b));
  let ultimoX = -Infinity;
  return ordenadas.map((b, i) => {
    const x = sx(b);
    const mostrarTexto = x - ultimoX >= 44;
    if (mostrarTexto) ultimoX = x;
    const ancora = x < 28 ? "start" : x > W - 28 ? "end" : "middle";
    return (
      <g key={"be-" + i}>
        <line x1={x} y1={PAD_T} x2={x} y2={H - PAD_B} stroke={T.textMuted} strokeWidth="1" strokeDasharray="2 4" />
        {mostrarTexto ? (
          <text x={x} y={H - PAD_B + 12} textAnchor={ancora} fontSize={FONTE_MIN} fill={T.textMuted}>{fmt(b)}</text>
        ) : null}
      </g>
    );
  });
})()}
```
The principle stated in the file's own comment (line 281-283, quoted
verbatim in UI-SPEC §1.2): "a LINHA... é SEMPRE desenhada — é dado, não
decoração — só o TEXTO se suprime."

**Collision-suppression pattern to REUSE for spot mark (CHART-02)**
(`PayoffChart.jsx:307-328`, `cenarios` rendering — the "top-anchored, 52×14
box" algorithm UI-SPEC §1.3 says spot joins, with spot given priority):
```jsx
{(() => {
  const desenhados = [];
  return cenarios.map((s, i) => {
    const x = sx(s.underlying);
    const y = ehNum(s.result) ? sy(s.result) : yZero;
    const colide = desenhados.some((p) => Math.abs(x - p.x) < 52 && Math.abs(y - p.y) < 14);
    const mostrarTexto = !colide;
    if (mostrarTexto) desenhados.push({ x, y });
    ...
  });
})()}
```

**`descricao`/`<title>` accessibility string pattern** (`PayoffChart.jsx:231-242`) — hardcoded PT text, NOT routed through `cp` (an existing, already-accepted inconsistency this file keeps for new additions per UI-SPEC §1.2):
```jsx
const descricao = "Curva de resultado no vencimento de " + nome
  + (vencimento ? ", vencimento " + vencimento : "")
  + ", por preço do ativo entre " + fmt(x0) + " e " + fmt(x1) + " reais. "
  ...
```

**"hoje" block placement pattern** — model on the existing `caixa()`/`cabecalho` structure (`PayoffChart.jsx:176-216`); the new "No vencimento"/"Hoje" `Kicker` pair (UI-SPEC §2) wraps the EXISTING `cabecalho` content unchanged, importing `Kicker` from `uiOpcoes.jsx` (not yet imported in this file today — new import line).

---

### `web/src/opcoes/estruturaParaPayoff.js`

**Analog:** itself — pure PT→EN renaming, zero arithmetic, guarded by regex; also the structural template for the NEW EN→PT backend adapter (see Critical Architecture Finding)

**Existing structure** (full file, 41 lines):
```js
export function estruturaParaPayoff(estrutura, nome) {
  if (!estrutura || typeof estrutura !== "object") return null;
  const curva = estrutura.curva;
  if (!Array.isArray(curva) || curva.length < 2) return null;

  return {
    name: nome,
    legs: Array.isArray(estrutura.pernas) ? estrutura.pernas : [],
    payoff: curva.map((ponto) => ({
      underlying: ponto.preco_objeto,
      result: ponto.resultado,
    })),
    breakevens: Array.isArray(estrutura.breakevens) ? estrutura.breakevens : [],
    net_cost: estrutura.custo_liquido,
    max_gain: estrutura.ganho_maximo,
    max_loss: estrutura.perda_maxima,
    unlimited_gain: estrutura.ganho_ilimitado,
    unlimited_loss: estrutura.perda_ilimitada,
  };
}
```
If `CuradoriaEstruturas.jsx`'s `estruturaParaPayoff` call site is ever given
`dominio`/`segmentos` (out of scope this phase per D-09, but the adapter
itself may still gain the mapping capability), the new keys are added the
same way — renamed 1:1 (`x_min → xMin`, etc.), never computed.

**Guardian test to extend** (`web/tests/test_estrutura_para_payoff.mjs:107-133`, regex over the file's own source):
```js
const ARITMETICA_FINANCEIRA = new RegExp(...);
ok("nenhuma aritmética sobre os campos financeiros no fonte do adaptador (exibe/renomeia, não calcula)", ...);
```
Any new key added here must pass this same static-source regex check — no
`*`/`+`/`-`/`/` applied to the new fields either. If the new backend EN→PT
adapter (`options_mcp_api.py`) is written as a standalone Python function,
consider the same style of static/regex guardian test on the Python side —
`server/tests/test_options_mcp_api.py` doesn't have one today, but the
precedent (`test_m3_format_pede_null_nunca_zero`-style guardians already
exist elsewhere in the backend test suite) supports adding one.

---

### `web/src/opcoes/uiOpcoes.jsx`

**Analog:** itself — `RazaoGanhoPerda`, `Kicker`, `Aviso`, `ErroDoMcp` already live here; this is the single shared-primitives module for `web/src/opcoes/`

**`RazaoGanhoPerda` — the exact function `formatarRazao()` must be extracted from** (`uiOpcoes.jsx:75-93`):
```jsx
export function RazaoGanhoPerda({ razao, cp }) {
  if (!razao) return null;
  const rotulo = cp.opcoesRazaoRotulo || "Razão ganho/perda";
  return (
    <div>
      {ehNum(razao.valor) ? (
        <Linha rotulo={rotulo} valor={"1 : " + fmt(razao.valor)} />
      ) : (
        <div style={{ padding: "7px 0", borderBottom: `1px solid ${T.borderFaint}` }}>
          <div style={{ fontSize: "12.5px", color: T.textSecondary }}>{rotulo}</div>
          <div style={{ fontSize: "12.5px", color: T.textPrimary, marginTop: "3px", whiteSpace: "pre-wrap", lineHeight: 1.45 }}>
            {razao.motivo || "—"}
          </div>
        </div>
      )}
      <div style={AJUDA}>{cp.opcoesRazaoAjuda || ""}</div>
    </div>
  );
}
```
Per UI-SPEC §3 / CONTEXT.md D-05: extract the `"1 : " + fmt(razao.valor)`
formatting (currently inline) into `export function formatarRazao(razao) {
return ehNum(razao?.valor) ? "1 : " + fmt(razao.valor) : razao?.motivo ||
"—"; }` (or equivalent), then have BOTH `RazaoGanhoPerda` and the new
`ExplicacaoPayoff` call it — this closes D-05/EXPL-03 by construction (one
formatter, not two).

**Local token-mirror + `fmt`/`ehNum` pattern** (`uiOpcoes.jsx:29-35`), to
reuse verbatim if `ExplicacaoPayoff` lands in a NEW file rather than here:
```jsx
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["textMuted", "borderSubtle", "negative", "bgPanel", "textSecondary", "textPrimary", "borderFaint"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));
const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v, casas = 2) => (ehNum(v) ? v.toFixed(casas).replace(".", ",") : "—");
```

**`Aviso`/`Kicker` components** (`uiOpcoes.jsx:37-51`) — reused verbatim by
`ExplicacaoPayoff`, no restyling:
```jsx
export function Kicker({ children }) {
  return (
    <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: ".08em", color: T.textMuted, margin: "18px 0 8px" }}>
      {children}
    </div>
  );
}
export function Aviso({ children, tom }) {
  return (
    <div style={{ border: `1px solid ${tom === "forte" ? T.negative : T.borderSubtle}`, borderRadius: "12px", padding: "12px", background: T.bgPanel, color: T.textSecondary, fontSize: "12.5px", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
      {children}
    </div>
  );
}
```

**`ErroDoMcp` cascade** (`uiOpcoes.jsx:103-128`) — reused verbatim for the
"hoje" block's error state (CHART-05):
```jsx
export function ErroDoMcp({ erro, cp }) {
  if (!erro) return null;
  const c = cp || {};
  if (erro.code === "mcp_nao_configurado") {
    return <Aviso>{c.opcoesNaoConfigurado || "Serviço de opções não configurado."}</Aviso>;
  }
  if (erro.code === "mcp_cota" || erro.code === "mcp_teto_servico") { ... }
  if (erro.code === "mcp_indisponivel") { ... }
  return (<><Aviso tom="forte">{erro.message}</Aviso><RecusaCobrada erro={erro} cp={cp} /></>);
}
```

---

### `web/src/opcoes/ExplicacaoPayoff.jsx` (NEW)

**Analog:** `web/src/finance.js`/`web/src/plan.js` for the "pure function, no I/O, unit-testable in isolation" discipline; `uiOpcoes.jsx`'s `RazaoGanhoPerda` for the concrete rendered shape (reads props + `cp`, returns `null` on missing data, wraps output in `Aviso`).

**Purity pattern to follow** (`web/src/finance.js` — small single-purpose
functions, no side effects, called by the component layer rather than doing
I/O themselves — same discipline `CLAUDE.md`'s Function Design convention
names explicitly): `ExplicacaoPayoff` must walk `segmentos` (prop, already
fetched by the caller) and `razao` (prop, reusing `formatarRazao()` from
`uiOpcoes.jsx` per D-05) into a `\n`-joined string — zero `fetch`, zero
`useEffect`, zero state.

**Rendering shape to follow** (mirrors `RazaoGanhoPerda`'s guard-clause +
`Aviso` wrap):
```jsx
import { Kicker, Aviso, formatarRazao } from "./uiOpcoes.jsx";

export default function ExplicacaoPayoff({ segmentos, spot, razao, cp }) {
  if (!Array.isArray(segmentos) || !segmentos.length) return null;
  const c = cp || {};
  const texto = montarTexto(segmentos, spot, razao, c); // pure helper, unit-testable alone
  return (
    <div>
      <Kicker>{c.opcoesComoLerTitulo || "Como ler esta estrutura"}</Kicker>
      <Aviso>{texto}</Aviso>
    </div>
  );
}
```
Template-sentence table is fully specified in UI-SPEC §3 (11 template
variants keyed by segment-position × inclinação); each variant becomes a
`cp.*` key per the Copywriting Contract table, consumed the same way
`RazaoGanhoPerda`/`ErroDoMcp` already consume `cp.*` (fallback string
literal when the key is absent, e.g. `c.opcoesExplicSpotPositiva || "Hoje, com..."`).

**Guard against re-deriving `razao`** (D-05/EXPL-03, the exact bug this phase fixes) — the pure helper receives `razao` as a prop and calls `formatarRazao(razao)` (from `uiOpcoes.jsx`), never reformats `razao.valor` inline a second time.

---

### `web/src/opcoes/CuradoriaEstruturas.jsx`

**Analog:** itself — single-line copy-key content change, no structural change

**Site to change** (`CuradoriaEstruturas.jsx:194`):
```jsx
<div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "6px" }}>{cp.curadoriaRazaoRotulo}: {cand.razao != null ? cand.razao.toFixed(2) : "—"}</div>
```
D-04 changes ONLY the string `cp.curadoriaRazaoRotulo` resolves to (in
`copy.js:712` Estudo, `copy.js:1300` Operador — see below) — this JSX line
itself, and the `cand.razao` field name, are unchanged (UI-SPEC §4 confirms
explicitly: "`cand.razao`... não é renomeado por este documento").

**Payoff chart call site, unchanged this phase** (`CuradoriaEstruturas.jsx:288-293`):
```jsx
{payoffPrimeiro && (
  <div style={{ marginTop: "10px" }}>
    <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.textFaint, marginBottom: "4px" }}>{cp.curadoriaPayoffRotulo}</div>
    <PayoffChart estrutura={payoffPrimeiro} emReais={null} cp={cp} palette={palette} />
  </div>
)}
```
No `dominio`/`segmentos`/`valorHoje` props added here per D-09 — CHART-01..04
fixes arrive automatically via `PayoffChart.jsx`'s own fallback local domain
calc, requiring zero edits at this call site.

---

### `web/src/opcoes/SecaoAnalisar.jsx` / `web/src/opcoes/SecaoComparar.jsx`

**Analog:** each other + `uiOpcoes.jsx`'s established grid/stacking convention

**Existing render site to extend** (`SecaoAnalisar.jsx:389-397`):
```jsx
<PayoffChart
  estrutura={proposta.dados.estruturas[0]}
  emReais={proposta.dados.emReais}
  cp={cp}
  palette={palette}
/>
<RazaoGanhoPerda razao={proposta.dados.razaoGanhoPerda} cp={cp} />
<Pernas pernas={proposta.dados.estruturas[0].legs} cp={cp} />
```
New props (`dominio`, `segmentos`, `valorHoje`) and `<ExplicacaoPayoff/>`
slot in here, matching UI-SPEC §3's concrete diff:
```jsx
<PayoffChart estrutura={...} emReais={...} dominio={...} segmentos={...} valorHoje={...} cp={cp} palette={palette} />
<RazaoGanhoPerda razao={...} cp={cp} />
<ExplicacaoPayoff segmentos={...} spot={dominio && dominio.spot} razao={...} cp={cp} />
```

**Existing render site to extend** (`SecaoComparar.jsx:206-227`, the `gap: "10px"` grid UI-SPEC §Spacing cites directly):
```jsx
<div style={{ display: "grid", gap: "10px" }}>
  {possibilidades.dados.possibilidades.map((item) => (
    <div key={item.vencimento}>
      {item.erro ? ( <Aviso tom="forte">...</Aviso> )
       : !item.estrutura ? ( <Aviso>...</Aviso> )
       : ( <>
             <PayoffChart estrutura={item.estrutura} emReais={item.emReais} cp={cp} palette={palette} />
             <RazaoGanhoPerda razao={item.razaoGanhoPerda} cp={cp} />
             <Cenarios emReais={item.emReais} cp={cp} />
           </> )}
    </div>
  ))}
</div>
```
Per D-02: `valorHoje` (and the `get_option_chain` fetch that produces it) is
attempted ONLY for `possibilidades.dados.possibilidades[0]` (the first item
in the already-ranked list) — the `.map()` index (`i === 0`) is the natural
gate; the other N-1 items never receive the `valorHoje` prop at all (absent,
not degraded — UI-SPEC §2's "caller-level decision" note).

---

### `web/src/copy.js`

**Analog:** itself — existing `cp.opcoes*` Estudo/Operador paired-key convention

**Estudo block excerpt** (`copy.js:176, 317, 322, 327, 329`):
```js
opcoesCarregando: "Consultando o serviço de opções…",
...
opcoesBreakevenRotulo: "Preço de empate (breakeven)",
...
opcoesRazaoRotulo: "Razão ganho/perda",
...
opcoesPorAcaoRotulo: "por ação",
opcoesGanhoIlimitado: "sem teto",
```

**Operador block excerpt** (`copy.js:889, 977, 981, 986, 988`) — same keys, terser wording:
```js
opcoesCarregando: "Consultando o serviço de opções…",
...
opcoesBreakevenRotulo: "Breakeven",
...
opcoesRazaoRotulo: "Razão G/P",
...
opcoesPorAcaoRotulo: "por ação",
opcoesGanhoIlimitado: "sem teto",
```

**`curadoriaRazaoRotulo` (D-04 rename target) — exact locations confirmed:**
```js
// copy.js:712 (Estudo block)
curadoriaRazaoRotulo: "prêmio sobre perda máxima",
// copy.js:1300 (Operador block)
curadoriaRazaoRotulo: "prêmio / perda máxima",
```
New value per UI-SPEC §4: Estudo → `"Pontuação de curadoria (ordena a lista
— não é o resultado da estrutura)"`; Operador → `"Pontuação de curadoria"`.

Every new key from UI-SPEC's Copywriting Contract table (`opcoesEixoZeroRotulo`,
`opcoesEixoVerticalLoteAjuda`, `opcoesNoVencimentoTitulo`, `opcoesHojeTitulo`,
`opcoesHojeCarregando`, `opcoesHojeAjuda`, `opcoesPerdaIlimitadaCurta`,
`opcoesHojePrefixoEixo`, `opcoesComoLerTitulo`, and the 11 explanation-template
keys) needs a pair — one entry in the Estudo block (~lines 170-330), one in
the Operador block (~lines 880-990) — following this exact same
key-name-identical/wording-different pattern.

---

## Shared Patterns

### MCP error cascade (applies to CHART-05's "hoje" block and any new MCP call)
**Source:** `web/src/opcoes/uiOpcoes.jsx:103-128` (`ErroDoMcp`), `server/app/options_mcp_api.py:1131-1185` (`_chamada_com_cap`)
**Apply to:** the new "valor hoje" fetch (backend: catch+attach, don't abort route; frontend: reuse `<ErroDoMcp/>` verbatim inside the "Hoje" block)

### Null-never-zero / motivo-on-degradation
**Source:** `server/app/opcoes_payoff.py:13-17` (module docstring), `371-374` (`y_max`/`y_min`), `312-320` (`dominio_da_curva` divergent-expirations branch)
**Apply to:** every new backend field this phase introduces (domain bounds, segments, valor_hoje) — `None` on missing/degraded, never `0.0`, and a non-null `motivo` string explaining why whenever degraded.

### Compute-once-in-backend, render-verbatim-in-front (D-24.2 lineage)
**Source:** `server/app/options_mcp_api.py:1289-1323` (`_em_reais`), `web/src/opcoes/estruturaParaPayoff.js` (whole file, zero-arithmetic guardian), `web/src/opcoes/PayoffChart.jsx:10-14` (module docstring)
**Apply to:** ALL new numeric fields (valor_hoje, domain bounds) — no arithmetic in `PayoffChart.jsx`, `estruturaParaPayoff.js`, or `ExplicacaoPayoff.jsx`; every number arrives pre-computed. The new backend EN→PT adapter (`options_mcp_api.py`) is rename-only for the same reason — the actual domain/segment arithmetic stays inside `opcoes_payoff.py`'s existing, already-tested functions.

### Single-formatter-for-a-shared-number (D-05/EXPL-03 fix)
**Source:** `web/src/opcoes/uiOpcoes.jsx:75-93` (`RazaoGanhoPerda`, formatting to extract as `formatarRazao()`)
**Apply to:** `ExplicacaoPayoff.jsx` — must import and call the same `formatarRazao()`, never re-render `razao.valor` independently.

### Collision-suppression for SVG marks ("line always drawn, only text suppressed")
**Source:** `web/src/opcoes/PayoffChart.jsx:284-301` (breakevens), `303-328` (cenarios)
**Apply to:** new strike marks (merge into breakeven's sorted 44px-gap pass) and spot mark (join cenarios' 52×14 collision list, with priority).

### Optional-prop, absent-vs-degraded distinction
**Source:** `web/src/opcoes/PayoffChart.jsx:185` (`emReais ? (...) : null`)
**Apply to:** `valorHoje` prop everywhere — `undefined`/`null` (not attempted, D-02's 2nd+ candidates) renders NOTHING; `{ carregando: true }`/`{ erro }`/`{ dados }` (attempted) renders a state.

---

## No Analog Found

None. Every file in scope has an exact or role-matching in-repo analog — this
phase is explicitly an extension of existing, recently-built (Fase 30-36)
`web/src/opcoes/`/`server/app/opcoes_*`/`options_mcp_api.py` machinery, not
new architecture. The one open question is not "which pattern to copy" but
the exact shape/placement of the small EN→PT rename adapter in
`options_mcp_api.py` described in the Critical Architecture Finding above —
a scoping decision for the plan, not a missing pattern (the pattern itself —
rename-only translation, modeled on `estruturaParaPayoff.js` — is well
established in this codebase).

---

## Metadata

**Analog search scope:** `server/app/opcoes_payoff.py`, `server/app/opcoes_motor.py`, `server/app/opcoes_curadoria.py`, `server/app/options_mcp_api.py`, `web/src/opcoes/*.jsx`, `web/src/opcoes/*.js`, `web/src/copy.js`, `web/src/finance.js`, `web/src/plan.js`, `server/tests/test_opcoes_payoff.py`, `server/tests/test_options_mcp_api.py`, `server/tests/fixtures/mcp_evaluate_petr4.json`, `web/tests/test_estrutura_para_payoff.mjs`
**Files scanned:** ~16 (full or targeted reads), plus grep sweeps across `server/app/*.py` and `web/src/opcoes/*.{js,jsx}`
**Pattern extraction date:** 2026-09-21
