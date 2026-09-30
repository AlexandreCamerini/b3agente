# Phase 45: Card de Posição Estruturada - Pattern Map

**Mapped:** 2026-09-29
**Files analyzed:** 13 new/modified files
**Analogs found:** 12 / 13 (one new module for navigation one-shot)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `web/src/App.jsx` (~4499-4650 card section) | component | request-response | `web/src/App.jsx` TravaPill, AvisoLiquidacao, PlanRuler | exact (same file) |
| `web/src/copy.js` (new ESTRUTURA_CARD) | config/vocabulary | request-response | `web/src/copy.js` badgeTravada, collarPernasLinha (738, 729) | role-match |
| `server/app/skill_ref.py` (new ESTRUTURA_CARD) | config/vocabulary | request-response | `server/app/skill_ref.py` ESTRUTURA_POSICAO (745-808) | exact analog |
| `web/src/opcoes/OpcoesScreen.jsx` (abaInicialOpcoes init) | component | request-response | `web/src/opcoes/OpcoesScreen.jsx` lines 334-339 | exact |
| `web/src/opcoes/memoriaOpcoes.js` (add opcoesAbrirTicker) | utility/state | request-response | `web/src/opcoes/memoriaOpcoes.js` (entire file) | exact analog |
| `web/src/persistence.js` (verify optionsProposta) | service | request-response | `web/src/persistence.js` lines 277, 1340 | exact (already paritário) |
| `web/src/api.js` (verify structure endpoint) | service | request-response | `web/src/api.js` line 327 | exact |
| `web/tests/test_estrutura_card.mjs` | test | validation | `web/tests/test_vocabulario_opcoes.mjs` | role-match |
| `web/tests/test_estrutura_espelho.mjs` | test | validation | `web/tests/test_fase3_paridade_stores_generica.mjs` | role-match |
| `web/tests/test_ritmo_sp.mjs` (add CardPosicaoEstruturada check) | test | validation | `web/tests/test_ritmo_sp.mjs` (existing) | role-match |
| `server/tests/test_estrutura_card.py` | test | validation | `server/tests/test_estrutura_posicao.py` | role-match |
| `.planning/REQUIREMENTS.md` (update CARD-06) | documentation | documentation | `.planning/REQUIREMENTS.md` | same file |

---

## Pattern Assignments

### `web/src/App.jsx` — Card de Posição (component, request-response)

**Analog:** `web/src/App.jsx` lines 1171-1249 (PlanRuler, TravaPill, AvisoLiquidacao) + lines 4500-4650 (position card rendering pattern)

**Status/state component pattern** (lines 1217-1249 — TravaPill + AvisoLiquidacao):
```javascript
function TravaPill({ qty, cp }) {
  if (!qty) return null;
  return <span style={{ padding: "3px 9px", borderRadius: "999px", background: T.negativeTint10, color: T.negative, fontSize: "10.5px", fontWeight: 800, whiteSpace: "nowrap" }}>{cp.badgeTravada(qty)}</span>;
}

function AvisoLiquidacao({ evento, cp }) {
  if (!evento) return null;
  const valor = evento.price === 0 ? 0 : price(evento.price);
  const texto = cp.avisoLiquidacaoForcada(evento.underlying, valor);
  return (
    <div style={{ marginTop: "10px", padding: "10px 11px", borderRadius: "9px", background: T.bgBase, border: `1px solid ${T.negative}`, display: "flex", gap: "7px", alignItems: "flex-start" }}>
      <span aria-hidden style={{ color: T.negative, fontSize: "13px", lineHeight: 1 }}>⚠</span>
      <span style={{ fontSize: "11.5px", color: T.textSecondary, lineHeight: 1.5 }}>{texto}</span>
    </div>
  );
}
```

**Card iteration pattern** (lines 4500-4650 — how to modify card rendering):
```javascript
{data.positions.map((p) => {
  const q = byQ(p.t);
  const cur = markPrice(q, p);
  return (
    <div key={p.t} id={"posicao-" + p.t} style={{ ...card, padding: "14px 15px" }}>
      {/* Header: ticker, qty, chips */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px", flexWrap: "wrap" }}>
        <div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: "16px" }}>{p.t}</span>
            <span style={{ color: T.textFaint, fontFamily: MONO, fontSize: "12px" }}>{p.qty} cotas · PM R$ {price(p.avg)}</span>
            {/* Add chips here: estrutura chip, vencimento chip, TravaPill */}
          </div>
        </div>
        <div style={{ textAlign: "right", fontFamily: MONO }}>
          <div style={{ fontSize: "16px", fontWeight: 600, color }}>{moneySigned(pnl)}</div>
        </div>
      </div>
      {/* AvisoLiquidacao — keep existing */}
      <AvisoLiquidacao evento={eventoLiquidacaoRecente(data.history, p.t)} cp={cp} />
      {/* Replace PlanRuler with new structure ruler when estrutura is loaded */}
      {/* List pernas, buttons, links — per UI-SPEC layout */}
    </div>
  );
})}
```

**Structure loading pattern** (new, store.optionsProposta integration):
```javascript
// At component mount, fetch structure for each ticker with optionPositions:
const estruturaMap = useRef({});
const loadEstrutura = async (t) => {
  if (estruturaMap.current[t]) return;
  try {
    const resposta = await store.optionsProposta(t, true);
    estruturaMap.current[t] = resposta.estrutura || null;
  } catch (e) {
    estruturaMap.current[t] = null; // falha
  }
};

// On mount/when positions change, trigger loads:
const tickers = new Set(data.optionPositions?.map(o => o.underlying) || []);
useEffect(() => {
  tickers.forEach(t => loadEstrutura(t));
}, [/* deps */]);

// In card render:
const estrutura = estruturaMap.current[p.t];
if (estrutura) {
  // Render CardPosicaoEstruturada with estrutura
} else if (data.optionPositions?.some(o => o.underlying === p.t)) {
  // Card is loading/failed — show current card + aviso
}
```

---

### `web/src/copy.js` — ESTRUTURA_CARD vocabulary (config, request-response)

**Analog:** `web/src/copy.js` lines 729-739 (collarPernasLinha, badgeTravada pattern, eyebrowPropostaCollar)

**Dictionary structure pattern** (lines 728-739):
```javascript
eyebrowPropostaCollar: "ESTUDO · TRAVA PROTETORA",  // Estudo mode
collarPernasLinha: (n, ticker, strikeCall, strikePut) => `${n}× TRAVA ${ticker} · call ${strikeCall} / put ${strikePut}`,
ctaCollarDebito: () => "Ver como este collar funcionaria",
badgeTravada: (qty) => `${qty} travada(s) · lastro da call coberta`,
avisoTravaNaVenda: (qty) => `${qty} ação(ões) está(ão) travada(s) como lastro de uma call coberta…`,
```

**New ESTRUTURA_CARD keys per UI-SPEC §Copywriting Contract** (lines 193-210):

Structure: identical to `ESTRUTURA_POSICAO` structure in skill_ref.py — same two-mode format.

```javascript
// In COPY.estudo block (lines 19-700):
chip_estrutura: "ESTUDO · {nome}",
chip_estrutura_generica: "ESTUDO · OPÇÕES",
lendo: "Lendo a estrutura de opções desta posição…",
indisponivel: "Não foi possível ler a estrutura de opções agora. As pernas abertas continuam na sua carteira, e nenhum valor é estimado no lugar.",
badge_travada_collar: (qty) => `${qty} travada(s) · lastro da call do collar`,
aviso_sem_stop: "Esta posição não tem stop definido. Defina em Editar stop/alvo ou peça a sugestão da IA.",

// Neutral keys (same in both modes) — add to COPY object globally:
estruturaResultadoRotulo: "Resultado da estrutura",
estruturaAcoesRotulo: "Ações",
estruturaOpcoesRotulo: "Opções",
estruturaFaixaTitulo: "FAIXA NO VENCIMENTO",
estruturaPernasTitulo: "PERNAS",
btnEncerrarEstrutura: "Encerrar estrutura…",
btnAtualizarEstrutura: "Atualizar",
fonteEstruturaLinha: (fonte, quando) => `Opções lidas de ${fonte} em ${quando}`,
fonteEstruturaSemDado: "Fonte das opções não declarada.",
```

**Reconciliation note** (D-11, copy changes):
Update existing keys in copy.js per UI-SPEC §Reconciliação de "trava protetora":
- `eyebrowPropostaCollar` Estudo (line 728): "ESTUDO · TRAVA PROTETORA" → "ESTUDO · COLLAR"
- `eyebrowPropostaCollar` Operador (line 1583): "PROPOSTA · TRAVA PROTETORA" → "PROPOSTA · COLLAR"
- `collarPernasLinha` (lines 729, 1584): "{n}× TRAVA {t}" → "{n}× COLLAR {t}"
- `ctaCollarDebito`/`ctaCollarCredito` Operador (lines 1585-1586): "Montar {n}× trava" → "Montar {n}× collar"
- `confirmAbrirCollar` Operador (line 1587): "Montar {n} trava(s) protetora(s)" → "Montar {n} collar(s)"

Update guardião `web/tests/test_opcoes_collar_ui.mjs` with note of deliberate reversal.

---

### `server/app/skill_ref.py` — ESTRUTURA_CARD vocabulary (config, request-response)

**Analog:** `server/app/skill_ref.py` lines 745-823 (ESTRUTURA_POSICAO dict + estrutura_posicao_txt function)

**Dictionary structure pattern** (lines 745-776 operador, 777-807 educacional):
```python
ESTRUTURA_POSICAO = {
    "operador": {
        "nome_call_coberta": "call coberta",
        "estado_vigente": "Vigente · vence {vencimento} ({dias} dia(s)).",
        "faixa_piso": "Piso R$ {piso} · perda máx. R$ {perdaMaxima}.",
        # ... 20+ more keys
    },
    "educacional": {
        "nome_call_coberta": "call coberta",
        "estado_vigente": "Estrutura vigente: faltam {dias} dia(s) para o vencimento de {vencimento}.",
        # ... educacional variants
    },
}

def estrutura_posicao_txt(modo: str, chave: str, **dados):
    """Frase canônica — interpolação com str.replace."""
    d = ESTRUTURA_POSICAO.get(modo if modo in ESTRUTURA_POSICAO else "educacional")
    frase = d.get(chave)
    if frase is None:
        return None
    for k, v in dados.items():
        frase = frase.replace("{" + str(k) + "}", str(v))
    return frase
```

**New ESTRUTURA_CARD dictionary** — distinct from ESTRUTURA_POSICAO per UI-SPEC §Copywriting Contract §Chaves de voz por modo:

Create new dict and function (same pattern):
```python
ESTRUTURA_CARD = {
    "operador": {
        "chip_estrutura": "ESTRUTURA · {nome}",
        "chip_estrutura_generica": "ESTRUTURA · OPÇÕES",
        "lendo": "Lendo a estrutura de opções…",
        "indisponivel": "Estrutura indisponível agora. Pernas abertas seguem na carteira — nada estimado.",
        "badge_travada_collar": "{qty} travada(s) · lastro da CALL do collar",
        "aviso_sem_stop": "Posição sem stop definido — defina em Editar stop/alvo ou peça a sugestão da IA.",
    },
    "educacional": {
        "chip_estrutura": "ESTUDO · {nome}",
        "chip_estrutura_generica": "ESTUDO · OPÇÕES",
        "lendo": "Lendo a estrutura de opções desta posição…",
        "indisponivel": "Não foi possível ler a estrutura de opções agora. As pernas abertas continuam na sua carteira, e nenhum valor é estimado no lugar.",
        "badge_travada_collar": "{qty} travada(s) · lastro da call do collar",
        "aviso_sem_stop": "Esta posição não tem stop definido. Defina em Editar stop/alvo ou peça a sugestão da IA.",
    },
}

def estrutura_card_txt(modo: str, chave: str, **dados):
    """Chaves de voz do card de estrutura — interpolação com str.replace."""
    d = ESTRUTURA_CARD.get(modo if modo in ESTRUTURA_CARD else "educacional")
    frase = d.get(chave)
    if frase is None:
        return None
    for k, v in dados.items():
        frase = frase.replace("{" + str(k) + "}", str(v))
    return frase
```

**Route integration** (server/app/main.py ~line 3273):
Existing `options_proposta` route already returns `estrutura` in payload — verify and document in pattern.

---

### `web/src/opcoes/OpcoesScreen.jsx` (component, request-response)

**Analog:** `web/src/opcoes/OpcoesScreen.jsx` lines 334-339 (abaInicialOpcoes initialization)

**Current initialization pattern** (lines 323-339):
```javascript
const [ticker, setTicker] = useState(() => tickerInicialOpcoes(ctx && ctx.opcoesMemoria, carteira));

// deep-link one-shot (`ctx.opcoesAbaInicial`, Plano 39-02), validado contra
// ABAS_OPCOES — fallback = "oportunidades" (mesmo default se a chave sair)
const [abaOpcoes, setAbaOpcoes] = useState(() => abaInicialOpcoes(ABAS_OPCOES, ctx && ctx.opcoesAbaInicial, ctx && ctx.opcoesMemoria));

useEffect(() => {
  if (ctx && ctx.opcoesAbaInicial && ctx.limparOpcoesAbaInicial) ctx.limparOpcoesAbaInicial();
}, [ctx]);
```

**Modified initialization pattern** (add abrirTicker one-shot — D-05 navigation):
```javascript
// New state for one-shot ticker from "Encerrar estrutura…" button
const [oportunidadeAberta, setOportunidadeAberta] = useState(() => {
  if (ctx?.opcoesAbrirTicker && Array.isArray(carteira) && carteira.some(p => p.t === ctx.opcoesAbrirTicker)) {
    return ctx.opcoesAbrirTicker;
  }
  return null;
});

// Clean up the one-shot on mount
useEffect(() => {
  if (ctx?.opcoesAbrirTicker && ctx?.limparOpcoesAbrirTicker) {
    ctx.limparOpcoesAbrirTicker();
  }
}, [ctx]);

// In render: if oportunidadeAberta is set, show PropostaDoAtivo for that ticker
// (existing pattern from Fase 39 initialization logic)
```

---

### `web/src/opcoes/memoriaOpcoes.js` — add opcoesAbrirTicker state (utility, request-response)

**Analog:** `web/src/opcoes/memoriaOpcoes.js` (entire file, lines 1-35)

**Full file pattern** (existing, shows pattern):
```javascript
export function abaInicialOpcoes(abas, abaInicial, memoria) {
  if (!Array.isArray(abas)) return "oportunidades";
  if (abas.includes(abaInicial)) return abaInicial;
  if (memoria && abas.includes(memoria.aba)) return memoria.aba;
  return "oportunidades";
}

export function tickerInicialOpcoes(memoria, carteira) {
  if (!memoria || typeof memoria.ticker !== "string" || memoria.ticker === "") return "";
  if (!Array.isArray(carteira)) return "";
  return carteira.some((p) => p && p.t === memoria.ticker) ? memoria.ticker : "";
}

export function memoriaOpcoes(ticker, aba) {
  if (ticker === "" && aba === "oportunidades") return null;
  return { ticker, aba };
}
```

**New one-shot function** (add to same file, follows validation pattern):
```javascript
// D-05: one-shot ticker for "Encerrar estrutura…" navigation
// Called by ctx.goOpcoes("oportunidades", { abrirTicker: t })
// Cleaned by ctx.limparOpcoesAbrirTicker()
// Returns ticker if it exists in carteira, null otherwise
export function abrirTickerOpcoes(ticker, carteira) {
  if (!ticker || typeof ticker !== "string") return null;
  if (!Array.isArray(carteira)) return null;
  return carteira.some((p) => p && p.t === ticker) ? ticker : null;
}
```

---

### `web/src/persistence.js` — verify optionsProposta parity (service, request-response)

**Analog:** `web/src/persistence.js` lines 277, 1340 (existing optionsProposta implementations in both stores)

**Current pattern** (already exists, no changes needed):
```javascript
// serverStore (line 277)
optionsProposta: (t, multiperna) => api.optionsProposta(t, multiperna),

// deviceStore (line 1340) — same signature
optionsProposta: (t, multiperna) => api.optionsProposta(t, multiperna),
```

**Verification:** Both stores already delegate to `api.optionsProposta` with same contract — structure is in `resposta.estrutura`. No modification needed; document in pattern.

---

### `web/src/api.js` — verify structure endpoint (service, request-response)

**Analog:** `web/src/api.js` line 327 (existing API integration)

**Pattern:** Existing `api.optionsProposta(t, multiperna)` already delivers `estrutura` in response payload. Verify route returns:
- `estrutura` (object with nome, nomeTexto, pernas[], acoes, resultado, faixa, estado, estadoTexto, descoberta, abertaSemProposta, encerrar, stopTexto, incompleto)
- `source` (cadeia da proposta — brapi/yahoo/mydata)
- `at` (instante de montagem)

From Fase 44 backend contract (CONTEXT.md).

---

### `web/tests/test_estrutura_card.mjs` — new test (test, validation)

**Analog:** `web/tests/test_vocabulario_opcoes.mjs` (lines 1-95, shows guardião pattern for mode-based vocabulary)

**Test pattern** (new file, follows `test_*.mjs` naming):
```javascript
// Fase 45: guardrail de card de estrutura — estado, navegação, parity
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

// Verify ESTRUTURA_CARD keys exist in both modes
for (const [modo, bloco] of [["estudo", COPY.estudo], ["operador", COPY.operador]]) {
  ok(`COPY.${modo}.chip_estrutura exists`, typeof bloco.chip_estrutura === "string");
  ok(`COPY.${modo}.lendo exists`, typeof bloco.lendo === "string");
  ok(`COPY.${modo}.indisponivel exists`, typeof bloco.indisponivel === "string");
  ok(`COPY.${modo}.aviso_sem_stop exists`, typeof bloco.aviso_sem_stop === "string");
}

// Verify pill uses "collar" not "trava protetora" for D-11
const collar = COPY.operador.badge_travada_collar || "";
ok("pill rejeita âncora 'trava protetora'", !/trava\s+protetora/i.test(collar));

// Verify Estudo rejeita "comprar"/"vender" infinitive
ok("Estudo aviso_sem_stop rejeita 'comprar'/'vender' infinitive", 
   !/\bcompra\b|\bvenda\b/.test(COPY.estudo.aviso_sem_stop));

// Verify estruturaResultadoRotulo neutral
ok("estruturaResultadoRotulo same in both modes", 
   COPY.estudo.estruturaResultadoRotulo === COPY.operador.estruturaResultadoRotulo);

if (fails > 0) process.exit(1);
```

---

### `web/tests/test_estrutura_espelho.mjs` — new parity test (test, validation)

**Analog:** `web/tests/test_fase3_paridade_stores_generica.mjs` (lines 1-100, shows parity extraction and validation pattern)

**Test pattern** (new file):
```javascript
// Fase 45: guardrail de parity ESTRUTURA_CARD: skill_ref.py ↔ copy.js
// Extract ESTRUTURA_CARD from both files and verify byte-for-byte equality of keys
import { readFileSync } from "fs";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond) => {
  console.log((cond ? "ok " : "FALHOU ") + name);
  if (!cond) fails++;
};

// Read skill_ref.py and extract ESTRUTURA_CARD keys
const skillRef = readFileSync(join(here, "..", "..", "server", "app", "skill_ref.py"), "utf8");
const skillMatch = skillRef.match(/ESTRUTURA_CARD\s*=\s*\{([^}]+)\}/s);
const skillKeys = skillMatch ? Object.keys(JSON.parse("{" + skillMatch[1] + "}")) : [];

// Read copy.js via Node import + validate keys
const { COPY } = await import("../src/copy.js");
const copyEstuKeys = Object.keys(COPY.estudo).filter(k => k.startsWith("chip_") || k.startsWith("lendo") || k.startsWith("indisponivel") || k.startsWith("badge_") || k.startsWith("aviso_"));
const copyOpKeys = Object.keys(COPY.operador).filter(k => k.startsWith("chip_") || k.startsWith("lendo") || k.startsWith("indisponivel") || k.startsWith("badge_") || k.startsWith("aviso_"));

ok("ESTRUTURA_CARD keys in skill_ref.py == copy.js Estudo", skillKeys.every(k => copyEstuKeys.includes(k)));
ok("ESTRUTURA_CARD keys in skill_ref.py == copy.js Operador", skillKeys.every(k => copyOpKeys.includes(k)));

if (fails > 0) process.exit(1);
```

---

### `web/tests/test_ritmo_sp.mjs` — add CardPosicaoEstruturada spacing check (test, validation)

**Analog:** `web/tests/test_ritmo_sp.mjs` (existing, checks component spacing tokens)

**Update pattern:** Add `CardPosicaoEstruturada` to component list scanned for `SP[*]` usage:
```javascript
// Lines in test that scan components — add CardPosicaoEstruturada name to the list
const componentFunctions = ["SinalChip", "LinhaContexto", "PlanoOperacionalBloco", "CardPosicaoEstruturada"];
for (const comp of componentFunctions) {
  const regex = new RegExp(`function ${comp}\\({|const ${comp}\\s*=`, 'g');
  if (!regex.test(appCode)) {
    console.log(`FALHOU: ${comp} não encontrado em App.jsx`);
    fails++;
  }
}
```

---

### `server/tests/test_estrutura_card.py` — new backend test (test, validation)

**Analog:** `server/tests/test_estrutura_posicao.py` (existing backend test pattern)

**Test pattern** (new file):
```python
# Fase 45: testes da função estrutura_card_txt — interpolação e fallback
import pytest
from app.skill_ref import estrutura_card_txt

def test_estrutura_card_txt_operador():
    """Verifica interpolação e modo."""
    txt = estrutura_card_txt("operador", "chip_estrutura", nome="COLLAR")
    assert txt == "ESTRUTURA · COLLAR"

def test_estrutura_card_txt_educacional():
    """Verifica modo fallback."""
    txt = estrutura_card_txt("educacional", "chip_estrutura", nome="COLLAR")
    assert txt == "ESTUDO · COLLAR"

def test_estrutura_card_txt_fallback_unknown_mode():
    """Unknown mode → educacional."""
    txt = estrutura_card_txt("unknown_mode", "chip_estrutura", nome="TEST")
    assert txt == "ESTUDO · TEST"

def test_estrutura_card_txt_missing_key():
    """Chave desconhecida → None."""
    txt = estrutura_card_txt("operador", "key_that_does_not_exist")
    assert txt is None

def test_estrutura_card_badge_travada():
    """Badge travada só com collar (D-11)."""
    txt = estrutura_card_txt("operador", "badge_travada_collar", qty="500")
    assert "500 travada(s)" in txt
    assert "collar" in txt.lower()
```

---

## Shared Patterns

### Navigation One-Shot Pattern (D-05 "Encerrar estrutura…")

**Source:** `web/src/App.jsx:9127` (`goOpcoes` implementation) + `web/src/opcoes/memoriaOpcoes.js` (validation)

**Pattern:**
```javascript
// In App.jsx context (ctx), add:
const [opcoesAbrirTicker, setOpcoesAbrirTicker] = useState(null);

ctx.goOpcoes = (aba, opts) => {
  if (typeof aba === "string") {
    setOpcoesAbaInicial(aba);
    if (opts?.abrirTicker) setOpcoesAbrirTicker(opts.abrirTicker);
  }
  navigate("opcoes");
};

ctx.limparOpcoesAbrirTicker = () => setOpcoesAbrirTicker(null);
ctx.opcoesAbrirTicker = opcoesAbrirTicker;
```

**Call from card:**
```javascript
<button onClick={() => ctx.goOpcoes("oportunidades", { abrirTicker: p.t })}>
  {cp.btnEncerrarEstrutura}
</button>
```

**Validate in destination** (OpcoesScreen.jsx):
```javascript
const [oportunidadeAberta, setOportunidadeAberta] = useState(() => 
  abrirTickerOpcoes(ctx?.opcoesAbrirTicker, carteira)
);
```

---

### Vocabulary Parity Pattern (skill_ref.py ↔ copy.js)

**Source:** `server/app/skill_ref.py:745` (ESTRUTURA_POSICAO) + `web/src/copy.js:728` (badgeTravada, etc.)

**Pattern:**
1. Define dict in skill_ref.py with "operador" and "educacional" keys
2. Mirror ENTIRE dict structure byte-for-byte in copy.js (same keys, same order preferred)
3. Create test that reads both files from disk and compares key sets
4. Never split same key across files (all mode-specific copy in copy.js, all backend-facing in skill_ref.py)

**Guardrail test signature:**
```javascript
const skillRefKeys = new Set(Object.keys(SKILL_REF.ESTRUTURA_CARD.operador));
const copyEstuKeys = new Set(Object.keys(COPY.estudo).filter(k => ESTRUTURA_CARD_KEYS.has(k)));
ok("ESTRUTURA_CARD parity", skillRefKeys.size === copyEstuKeys.size && [...skillRefKeys].every(k => copyEstuKeys.has(k)));
```

---

### Component Loading State Pattern (D-03 carregando/indisponivel)

**Source:** `web/src/App.jsx:4531` (AvisoLiquidacao) + UI-SPEC §Estados

**Pattern for loading/error states:**
```javascript
const estrutura = estruturaMap.current[p.t];
const isLoading = (optionPositions includes p.t) && !estrutura; // não tentamos ainda
const isFailed = (optionPositions includes p.t) && estrutura === null; // tentamos e falhou

if (isLoading) {
  return <div role="status" aria-live="polite">{cp.lendo}</div>;
}
if (isFailed) {
  return <div role="status">{cp.indisponivel} <button onClick={() => loadEstrutura(p.t)}>{cp.btnAtualizarEstrutura}</button></div>;
}
if (estrutura) {
  // Render estrutura
  return <CardPosicaoEstruturada estrutura={estrutura} p={p} cp={cp} ctx={ctx} />;
}

// No structure — show current card
return <CardPosicaoAtual p={p} ... />;
```

---

### Font/Source Pattern (principle 3 — declare source and timestamp)

**Source:** `web/src/opcoes/PropostaLastreada.jsx:56-62` (FonteDoDadoProposta)

**Pattern:**
```javascript
export function FonteDoDadoProposta({ r, cp }) {
  return (
    <div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "10px" }}>
      {r.source ? cp.fontePropostaLinha(FONTE_LABEL(r.source), r.at || "—") : cp.fontePropostaSemDado}
    </div>
  );
}
```

**For CardPosicaoEstruturada:**
```javascript
const estrutura = estruturaMap.current[p.t]; // { estrutura, source, at }
const fonte = estrutura?.source;
const quando = estrutura?.at; // "dd/mm/aaaa hh:mm" from Intl.DateTimeFormat

<div style={sourceLineStyle}>
  {fonte ? cp.fonteEstruturaLinha(FONTE_LABEL(fonte), quando) : cp.fonteEstruturaSemDado}
  <button onClick={() => loadEstrutura(p.t)}>{cp.btnAtualizarEstrutura}</button>
</div>
```

---

### Disabled Button with aria-describedby Pattern (D-06 "Encerrar bloqueado")

**Source:** `web/src/opcoes/PropostaLastreada.jsx:69-79` (ChipDaProposta accessibility)

**Pattern:**
```javascript
const estrutura = estruturaMap.current[p.t];
const encerrar = estrutura?.encerrar || {};
const isDisabled = !encerrar.permitido;
const motivo = encerrar.texto;

<button 
  onClick={!isDisabled ? () => ctx.goOpcoes("oportunidades", { abrirTicker: p.t }) : undefined}
  disabled={isDisabled}
  aria-disabled={isDisabled}
  aria-describedby={isDisabled ? "motivo-encerrar-" + p.t : undefined}
  style={buttonStyle}
>
  {cp.btnEncerrarEstrutura}
</button>

{isDisabled && (
  <div id={"motivo-encerrar-" + p.t} style={{ fontSize: "11px", color: T.textMuted, marginTop: "4px" }}>
    {motivo}
  </div>
)}
```

---

## No Analog Found

None — all patterns exist in codebase or are direct extensions of existing patterns.

---

## Metadata

**Analog search scope:** 
- `web/src/App.jsx` (TravaPill, AvisoLiquidacao, PlanRuler, position card rendering)
- `web/src/copy.js` (vocabulary dictionary structure, mode-based copy)
- `web/src/opcoes/` (navigation, state management, one-shot patterns)
- `web/src/persistence.js` (store method parity)
- `web/src/api.js` (API integration)
- `server/app/skill_ref.py` (vocabulary dictionary pattern)
- `server/app/main.py` (route verification)
- `web/tests/` (test guardião patterns)

**Files scanned:** 47 (web components, services, tests; server modules)

**Pattern extraction date:** 2026-09-29

---

## Final Notes for Planner

### Critical Integration Points

1. **Structure loading must NOT block card render** — D-03 shows current card + aviso while loading
2. **optionsProposta already paritário** — no new route needed (D-01), use existing contract
3. **One-shot navigation** — ctx.goOpcoes signature extends to accept options object (backward compatible)
4. **Copy reconciliation** — D-11 changes to existing keys (eyebrowPropostaCollar, collarPernasLinha, ctaCollarDebito/Credito, confirmAbrirCollar, badgeTravada) must update guardiões with deliberate reversal notes
5. **Test guardiões do NOT get deleted** — add reversal note if changing behavior

### Risk Areas

- **Cota brapi impact** — structure loading calls optionsProposta which calculates proposta; monitor 15k/mês budget (D-04 recarga discreta)
- **Paridade stores** — ESTRUTURA_CARD keys must exist in BOTH copy.js Estudo AND Operador (test catches)
- **Avatar/markup synchronization** — Fase 44 backend output contract must be verified (estrutura shape from `ler_estrutura`)

