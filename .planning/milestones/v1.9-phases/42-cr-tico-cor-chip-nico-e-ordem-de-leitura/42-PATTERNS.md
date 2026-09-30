# Phase 42: Crítico — cor, chip único e ordem de leitura - Pattern Map

**Mapped:** 2026-09-26
**Files analyzed:** 4 (todos MODIFICADOS — fase não cria arquivo novo)
**Analogs found:** 4 / 4 (todos internos ao próprio `App.jsx`/`copy.js` — não há componente externo a copiar; esta fase EXTRAI um componente novo `SinalChip` de código já existente no mesmo arquivo)

Nota de escopo: esta fase não introduz nenhum arquivo novo de produção. Todo
trabalho é refactor/edição em 2 arquivos (`web/src/App.jsx`, `web/src/copy.js`)
e atualização de guardiões em `web/tests/*.mjs`. Por isso os "analogs" abaixo
são as próprias implementações atuais dentro do mesmo arquivo — o padrão a
copiar é o código que está sendo substituído/consolidado, não um arquivo de
outro domínio.

---

## File Classification

| Arquivo | Papel | Fluxo de dado | Ação nesta fase |
|---|---|---|---|
| `web/src/App.jsx` | component (React, UI) | request-response (render puro a partir de `vm`/`radarVm`, sem I/O) | Extrair `SinalChip` (substitui `chip()`×2, `FundamentoChip`, `RegimeChip`, pill de confiança, `HISTORICO_PILL_STYLE`); reordenar `AtivoCard`; mover `ring` para dentro de `SinalChip peso="primario"`; recolorir `ConfluenceRing` |
| `web/src/copy.js` | provider (dicionário de texto) | CRUD (leitura de chave por modo) | Adicionar strings novas (marca de alinhamento, rótulo do anel, disclaimer de fundamento) em `COPY.estudo`/`COPY.operador` |
| `web/tests/test_historico_ui.mjs` | test (guardião grep-estático) | transform (lê texto do App.jsx, testa regex) | Atualizar expectativa de cor (D-04): `HISTORICO_PILL_STYLE.elegivel`/`inelegivel` deixam de usar `T.positive`/`T.negative` |
| `web/tests/test_radar_leitura_rapida.mjs` | test (guardião grep-estático) | transform | Atualizar P3b: pill "confiança X" sai, vira parte do rótulo do anel dentro de `SinalChip peso="primario"` |
| `web/tests/test_radar_regime_chip.mjs` | test (guardião grep-estático) | transform | Migrar asserções de `RegimeChip`/`FundamentoChip` para `SinalChip peso="contexto"`, preservando "indefinido nunca vira chip" |
| (novo, opcional) `web/tests/test_sinal_chip_ui.mjs` | test (guardião grep-estático) | transform | Guardião NOVO para o contrato do `SinalChip` (ban list de cor, D-14/D-15) |

---

## Pattern Assignments

### `SinalChip` (peso="contexto") — substitui `chip()`, `FundamentoChip`, `RegimeChip`, pill de confiança

**Analogs (todos em `web/src/App.jsx`):**
- `chip()` interno do `AtivoCard`, `App.jsx:3370-3374` (watchlist, com `explicavel`/`SUBLINHADO`)
- `chip()` interno da lista da Watchlist, `App.jsx:3952-3954` (duplicata mais simples, sem `explicavel`)
- `FundamentoChip`, `App.jsx:1372-1381`
- `RegimeChip`, `App.jsx:1389-1404`
- pill de confiança do Radar, `App.jsx:6896`

**Padrão de visual a preservar (chip base, `App.jsx:3370-3374`):**
```jsx
const chip = (label, value, col, explicavel) => (
  <span style={{ fontSize: "11px", padding: "4px 10px", borderRadius: "999px", background: T.bgBase, color: T.textSecondary, fontWeight: 700 }}>
    <span style={explicavel ? SUBLINHADO : undefined}>{label}</span> <b style={{ fontWeight: 800, color: col || T.textPrimary }}>{value}</b>
  </span>
);
```
UI-SPEC pede radius 7px (herdado de `FundamentoChip`/`RegimeChip`, não 999px do
`chip()` legado) — usar o padrão de borda de `FundamentoChip`, não o de `chip()`:

```jsx
// App.jsx:1373-1380 — FundamentoChip (padrão de borda+cor a copiar)
const SCORE_COLOR = { A: "positive", B: "accent", C: "negative" };
function FundamentoChip({ f }) {
  if (!f || !f.score) return null;
  const c = T[SCORE_COLOR[f.score] || "textFaint"];
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "5px", padding: "4px 9px", borderRadius: "7px", fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", border: `1px solid ${c}`, color: c }}>
      FUNDAMENTO <b style={{ fontFamily: MONO, fontSize: "11px" }}>{f.score}</b>
    </span>
  );
}
```
**Mudança obrigatória (D-06):** remover `T[SCORE_COLOR[...]]`/`T[REGIME_STYLE...]`
como fonte de `color`/`border` — trocar por `T.textPrimary` (valor) fixo,
`T.textFaint` (label), borda `1px solid T.borderSubtle` (não mais cor
semântica). `SCORE_COLOR`/`REGIME_STYLE` são removidos como dirigentes de cor
(podem sobreviver só se algo mais os usar; se não, apagar — checar).

**Guarda de ausência a preservar (D-16), padrão de `RegimeChip` (`App.jsx:1394-1396`):**
```jsx
function RegimeChip({ regime }) {
  if (!regime || !regime.regime || regime.regime === "indefinido") return null;
  ...
  {regime.confiavel === false && <span style={{ fontWeight: 400, opacity: 0.75 }}>·SMA50</span>}
```
`SinalChip` precisa reproduzir literalmente essas 2 guardas: sem `score`/sem
`regime` válido → não renderiza; base degradada (`·SMA50`) permanece como
sufixo textual dentro de `value`/`ariaLabel` (D-16).

**aria-label obrigatório (D-15)** — padrão a copiar de `HistoricoPill`:
```jsx
// App.jsx:6617
<span role="img" aria-label={ariaLabel} style={pillStyle}>{rotulo}</span>
```

**Estado `inelegivel` (variante de cor dentro de `contexto`):**
```jsx
// App.jsx:6577-6583 — HISTORICO_PILL_STYLE atual (a REVISAR: D-03/D-04)
const HISTORICO_PILL_STYLE = {
  elegivel: [T.positive, T.positiveTint10],      // MUDA: para T.textPrimary + borda, glifo ✓
  inelegivel: [T.negative, T.negativeTint10],    // MUDA: para T.warn + T.warnTint10 (D-03)
  insuficiente: [T.textFaint, T.bgBase],         // mantém
  nunca_medido: [T.textFaint, T.bgBase],         // mantém
  aposentado: [T.textMuted, T.bgCard],           // mantém (borda tracejada)
};
```
Novo token a declarar em `PALETTE.dark`/`PALETTE.light` (junto a `warn:`,
`App.jsx:127` e `:162`):
```js
warnTint10: "rgba(251,191,36,0.10)",   // dark
warnTint10: "rgba(161,98,7,0.04)",     // light
```

---

### `SinalChip` (peso="primario") — substitui o bloco da manchete + `ring` embutido

**Analog:** bloco da manchete do `AtivoCard`, `App.jsx:3558-3562` (pixel-equivalente, UI-SPEC exige):
```jsx
{decM ? (
  <div style={{ marginTop: "11px", background: decBg, borderRadius: "9px", padding: "9px 11px" }}>
    <div style={{ fontSize: "10px", letterSpacing: "0.04em", color: decColor }}>
      {operador ? "DECISÃO DA MESA" : "PLANO EDUCACIONAL"}{pos ? " · você está comprado" : ""}
    </div>
    <div style={{ fontSize: "17px", fontWeight: 800, color: decColor }}>{decM}</div>
  </div>
) : contexto !== "radar" && (
  <div style={{ marginTop: "11px", background: T.bgBase, borderRadius: "9px", padding: "9px 11px", border: `1px solid ${T.borderFaint}` }}>
    <div style={{ fontSize: "10px", letterSpacing: "0.04em", color: T.textFaint }}>{operador ? "DECISÃO DA MESA" : "PLANO EDUCACIONAL"}</div>
    <div style={{ fontSize: "12.5px", color: T.textMuted, marginTop: "2px" }}>Sem leitura do motor para este ativo agora — toque em ↻ reordenar para varrer de novo.</div>
  </div>
)}
```
**Resolução de cor interna (nunca prop livre) — reusar `REC_STYLE`:**
```js
// App.jsx:1286-1304
const REC_STYLE = {
  "COMPRAR": [T.positive, T.positiveTint10],
  "VENDER": [T.negative, T.negativeTint10],
  "AGUARDAR CONFIRMAÇÃO": [T.accent, T.accentTint10],
  "NÃO OPERAR": [T.textMuted, T.bgBase],
  ...
};
```
`decColor`/`decBg` já chegam calculados no `vm` (watchlist: `App.jsx:3951`;
radar: `App.jsx:6876`) — o componente pode continuar recebendo `[decColor,
decBg]` OU recalcular via `REC_STYLE[decision]` internamente (UI-SPEC pede a
segunda forma — "resolve internamente" — para não vazar cor livre pelo
`vm`). Escolha de implementação: mover o lookup de `REC_STYLE` para dentro do
`SinalChip`, chamador passa só `decision` (string).

**Layout com `ring` embutido (D-08), ponto de fusão com `ConfluenceRing`:**
```jsx
// App.jsx:6942-6949 — bloco atual do Radar (rodapé, a MOVER para dentro do SinalChip primario)
<div style={{ marginTop: "12px", display: "flex", alignItems: "center", gap: "13px" }}>
  <ConfluenceRing conf={r.confluencia} size={54} />
  <div style={{ minWidth: 0 }}>
    <div style={{ fontSize: "10.5px", color: T.textFaint, letterSpacing: "0.05em", fontWeight: 700 }}>CONFLUÊNCIA DO SETUP</div>
    <div style={{ fontSize: "12px", color: T.textMuted, marginTop: "3px", lineHeight: 1.4 }}>
      <TierDot tier={tierOf(r.confluencia)[0]} /> {tierOf(r.confluencia)[1]} · aderência ao padrão de estudo
    </div>
  </div>
</div>
```
Este bloco INTEIRO some do rodapé — o anel some daqui e reaparece 36px dentro
do `SinalChip peso="primario"`, ao lado do texto de decisão
(`display:flex; justify-content:space-between; align-items:center; gap:8px`,
por UI-SPEC).

---

### `ConfluenceRing` — cor do arco (D-08/D-09, TIER_FILL em vez de P.positive/P.accent)

**Analog:** `App.jsx:6553-6569` (função atual, a EDITAR, não substituir):
```jsx
function ConfluenceRing({ conf, size = 54, label = true }) {
  const P = usePalette();
  const c = Math.max(0, Math.min(100, Number(conf) || 0));
  const cx = size / 2;
  const r = cx - 4;
  const C = 2 * Math.PI * r;
  const off = C * (1 - c / 100);
  const col = c >= 75 ? P.positive : c >= 50 ? P.accent : P.textFaint;   // MUDA → TIER_FILL[tierOf(conf)[0]]
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ flex: "none" }} role="img" aria-label={`Confluência ${c}%`}>
      <circle cx={cx} cy={cx} r={r} fill="none" stroke={P.borderFaint} strokeWidth="4" />
      <circle cx={cx} cy={cx} r={r} fill="none" stroke={col} strokeWidth="4" strokeLinecap="round"
        strokeDasharray={C.toFixed(1)} strokeDashoffset={off.toFixed(1)} transform={`rotate(-90 ${cx} ${cx})`} />
      {label && <text x={cx} y={cx} textAnchor="middle" dominantBaseline="central" fontFamily={MONO} fontSize={Math.round(size * 0.26)} fontWeight="800" fill={P.textPrimary}>{c}%</text>}
    </svg>
  );
}
```
**Fonte da nova cor** — `TIER_FILL`/`tierOf`, já existentes e reutilizados sem
mudança de contrato (`App.jsx:1085-1098`):
```js
function tierOf(conf) {
  const c = Number(conf) || 0;
  if (c >= 75) return ["forte", "Forte"];
  if (c >= 50) return ["moderada", "Moderada"];
  if (c > 0) return ["neutra", "Neutra"];
  return ["fraca", "Fraca"];
}
const TIER_FILL = { forte: "#22c55e", moderada: "#f59e0b", neutra: "#9ca3af", fraca: "#ef4444" };
```
`col = TIER_FILL[tierOf(c)[0]]` substitui a linha atual. `aria-label` do SVG
também precisa ganhar tier+lado+setup (UI-SPEC, seção Acessibilidade) — a
composição do texto deve reusar a MESMA string do rótulo visível (nunca uma
segunda fonte), o que empurra a montagem do rótulo para uma função pura
compartilhada entre `aria-label` e o `<div>` de texto.

**Dado de `lado` para o rótulo (D-09):** vem do motor, nunca inferido:
```
server/app/regime.py:209   lado = (melhor.get("lado") or "").lower()
server/app/setups.py:707   "lado": lado,     (plano_operacional)
server/app/setups.py:576   veredito = "Estudar alta" if melhor["lado"] == "alta" else "Estudar baixa"
```
No payload do Radar hoje `plano.lado` está disponível (ver `server/app/setups.py:707`,
`plano_operacional`); o planner deve confirmar se `radarVm.sc` (`App.jsx:6889`)
precisa ganhar o campo `lado` (hoje ausente do subconjunto `sc: {...}` do
Radar) — se sim, adicionar só o campo, nunca `r` inteiro (guardrail já
documentado em `App.jsx:6883-6888`). Para a Watchlist, `sc.lado` só existe se
o payload de scan já entregar — se não vier, a cláusula "padrão de X:" é
omitida (nunca recalculada no front, D-01/D-09).

---

### Marca de alinhamento — não é um `SinalChip`, é texto anexo (D-07)

**Fonte do dado, motor (não recalcular no front):**
```
server/app/regime.py:193   def _gatilho_alinhado(...)
server/app/regime.py:293   r["gatilhoAlinhado"] = _gatilho_alinhado(r, r["regime"])
```
**Uso atual no Radar (texto simples, já existe, só reposicionar/reformular):**
```jsx
// App.jsx:6903
{r.melhorSetup && <span style={{ fontSize: "11.5px", color: T.textMuted }}>{r.melhorSetup}{critTot > 0 ? ` · ${critOk}/${critTot} critérios` : ""}{r.gatilhoAlinhado ? " · alinhado ao regime" : ""}</span>}
```
Nova forma (D-07, texto 12px/400 `T.textSecondary`, glifo `↗`/`↘` sem cor):
```jsx
{alinhamento && (
  <span style={{ fontSize: "12px", color: T.textSecondary, lineHeight: 1.4 }}>
    <span aria-hidden>{alinhamento === "a_favor" ? "↗" : "↘"}</span>{" "}
    {alinhamento === "a_favor" ? COPY_ALINHAMENTO.a_favor : COPY_ALINHAMENTO.contra}
  </span>
)}
```
Watchlist: verificar se `sc.gatilhoAlinhado` chega no payload de scan
(mesma checagem defensiva de `sc.lado` acima) — se não vier, a marca não
renderiza (D-01), nunca recalcula.

---

### Copy novo (`web/src/copy.js`) — padrão de par `historico`/`historicoRotulo` a seguir

**Analog:** `web/src/copy.js:585-599` (bloco `historico`/`historicoRotulo` dentro de `COPY.estudo`) + espelho em `:1351` (`COPY.operador`), consumidos por `copyFor()`/`historicoTxt()` (`copy.js:1561-1574`).

Como as strings novas desta fase (marca de alinhamento, rótulo do anel,
disclaimer de fundamento) são "fatos do motor" sem variação por modo
(confirmado no UI-SPEC, seção Copywriting Contract), o padrão mais próximo a
copiar é o de `glossarioSub`/`concentracaoLink` (`copy.js:612-624`) — chaves
que hoje já vivem IDÊNTICAS nos dois blocos `estudo`/`operador`, não o padrão
`historico` (que tem prosa diferenciada por modo). Ex.:
```js
// dentro de COPY.estudo (e repetir idêntico em COPY.operador)
alinhamentoAFavor: "↗ a favor da tendência",
alinhamentoContra: "↘ contra a tendência",
fundamentoDisclaimer: "fundamento indica qualidade da empresa, não direção",
ladoAnelCompra: "padrão de compra",
ladoAnelVenda: "padrão de venda",
```
Nenhuma string solta em `SinalChip`/`ConfluenceRing`/`AtivoCard` (guardrail
explícito do UI-SPEC).

---

## Shared Patterns

### Guardião de teste (grep estático sobre texto do App.jsx)
**Source:** `web/tests/test_radar_regime_chip.mjs` (padrão mais enxuto) e
`web/tests/test_historico_ui.mjs` (padrão de recorte + iteração sobre `COPY`).
**Apply to:** qualquer teste novo/atualizado desta fase.

```js
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
const here = dirname(fileURLToPath(import.meta.url));
const appSrc = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
// ... regex sobre `appSrc` (ou sobre um `recorte` explícito por índice de string) ...
console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
```
Regra do repositório: nunca assertar contra o arquivo inteiro quando o token
testado (`T.negative`, `T.positive`) aparece em dezenas de outros lugares —
sempre recortar por âncora de string (`appSrc.indexOf("...")`) antes de rodar
regex, como em `test_historico_ui.mjs` linhas 22-24.

Descoberta de teste: `scripts/executar.sh:33` faz `for t in web/tests/*.mjs`
— um arquivo novo `test_sinal_chip_ui.mjs` é pego automaticamente, sem
registro manual em lista alguma.

### Tokens de tema (nunca hex solto fora de `PALETTE`)
**Source:** `web/src/App.jsx:105-164` (`PALETTE.dark`/`PALETTE.light`), padrão de comentário-decisão em cada entrada nova (ex. `warn: "#fbbf24", // qa/34: ...`).
**Apply to:** declaração de `warnTint10` nos dois temas (D-03), qualquer cor nova.
```js
// PALETTE.dark
warnTint10: "rgba(251,191,36,0.10)",   // Fase 42 (COR-01/D-03): tint do estado inelegível — 7,98–8,64:1 AA
// PALETTE.light
warnTint10: "rgba(161,98,7,0.04)",     // Fase 42 (COR-01/D-03): alpha 4% — 4,68:1 AA (ver 42-UI-SPEC.md)
```
`MODE_OPERADOR` (`App.jsx:175-227`) não precisa de override para
`warnTint10` (confirmado no UI-SPEC) — só declarar nos 2 temas base.

### Guardrail "manchete só do motor" (REC_STYLE resolvido internamente)
**Source:** `App.jsx:1286-1304` (`REC_STYLE`) + `App.jsx:1272-1273` (`decisaoDoModo`).
**Apply to:** `SinalChip peso="primario"` — nenhuma prop de cor livre; o
componente resolve `REC_STYLE[decision]` internamente, replicando o padrão já
usado em 3 call sites (`App.jsx:3951`, `App.jsx:3922`, `App.jsx:6876`).

### `SetorAlvo` (âncora didática) — alvo de toque mínimo 44px sem mudar visual
**Source:** `web/src/entendimento.jsx:87` (componente `SetorAlvo`, não copiado aqui na íntegra — o achado do UI-SPEC é que ele NÃO garante 44px sozinho).
**Apply to:** o `SetorAlvo setorId="analise"` que hoje envolve a linha de
chips (`App.jsx:3603-3605`) passa a envolver o `ConfluenceRing` (36px) dentro
do `SinalChip primario` — o chamador deve passar
`style={{ minWidth: 44, minHeight: 44, display: "flex", alignItems: "center", justifyContent: "center" }}`
ao `SetorAlvo`, sem alterar o componente em si.

---

## No Analog Found

Nenhum arquivo desta fase carece de analog — todo o trabalho é
refactor/consolidação dentro de `web/src/App.jsx`/`web/src/copy.js` e seus
testes de guardião em `web/tests/`. Não há componente de outro domínio do
código a copiar.

---

## Metadata

**Analog search scope:** `web/src/App.jsx` (função `AtivoCard`, `RadarScreen`,
`ConfluenceRing`, `HistoricoPill`, `FundamentoChip`, `RegimeChip`, `REC_STYLE`,
`PALETTE`), `web/src/copy.js` (`COPY.estudo`/`COPY.operador`,
`copyFor`/`historicoTxt`), `web/tests/test_historico_ui.mjs`,
`web/tests/test_radar_regime_chip.mjs`, `web/tests/test_radar_leitura_rapida.mjs`,
`server/app/regime.py` (`_gatilho_alinhado`, `ranquear`), `server/app/setups.py`
(`detect_setups`, `plano_operacional`), `scripts/executar.sh` (descoberta de
teste `web/tests/*.mjs`).
**Files scanned:** ~12 (leituras diretas + greps direcionados, sem carregar
`App.jsx` inteiro — arquivo tem ~7600 linhas, lido só por trechos não
sobrepostos).
**Pattern extraction date:** 2026-09-26
