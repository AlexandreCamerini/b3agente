---
phase: 43
slug: refinamento-copy-por-modo-kpiblock-e-ritmo
status: draft
shadcn_initialized: false
preset: none
created: 2026-09-27
---

# Phase 43 — UI Design Contract

> Contrato visual/interação para a linha de elegibilidade e a "Leitura da IA"
> do `AtivoCard` (`web/src/App.jsx:3521`, Watchlist e Radar) e para o
> espaçamento interno dos blocos que a Fase 42 já ordenou. Verificado por
> `gsd-ui-checker`; fonte de verdade para `gsd-planner`/`gsd-executor`.
> Escopo travado por `43-CONTEXT.md` (D-01..D-18) — não reabre decisões.
> Reusa a estrutura do `42-UI-SPEC.md` (mesmo card, mesma convenção de
> tabela/ban-list/citação de linha).
>
> Linhas citadas medidas em 2026-09-27, no estado do repo pós-Fase 42
> (commit `671b4db`).

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none — sem shadcn/Tailwind/component lib; design system é o conjunto de tokens `T.x` (CSS vars) já existente em `PALETTE`/`MODE_OPERADOR` (inalterado nesta fase) |
| Preset | not applicable |
| Component library | none — React puro, estilo inline |
| Icon library | none — glifos Unicode inline (`✓`, `↗`, `↘`) já em uso; nenhuma lib nova |
| Font | inalterado — Nunito (`SANS`) corpo/label, Fredoka 600 (`DISPLAY`) manchete/números de destaque |

Nenhuma decisão de Design System nova nesta fase — RITMO-01/HIER-03/CHIP-03
não tocam tooling, só espaçamento e conteúdo dentro do que a Fase 42 já
definiu.

---

## Spacing Scale (RITMO-01)

Constante nomeada única em `web/src/App.jsx`, ao lado de `DIR_STYLE`/
`REC_STYLE` (mesmo bloco de constantes de apresentação):

```js
// RITMO-01 (Fase 43): escala 4/8pt do qa/AUDITORIA-Design-System-v1.md §3.2.
// Card inteiro (D-14): usa SP em vez de string solta. Regra de arredondamento
// (D-15/D-16): cada valor herdado vira o degrau MAIS PRÓXIMO; empate (diff
// igual para os dois lados) arredonda para CIMA (não aperta o layout
// existente). Exceção só como constante nomeada, comentada, na lista fechada
// abaixo — o guardião aceita só essas.
const SP = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32 };
```

Escopo do guardião (D-14, literal): gap/padding/margin dentro de `SinalChip`
(os dois pesos), `LinhaContexto`, `PlanoOperacionalBloco`, `HistoricoPill`, e
os espaços ENTRE os blocos 1-5 do `AtivoCard` (manchete → timing → plano →
contexto → elegibilidade — a régua da lista de HIER-02). **Fora do
escopo**: bloco 0 (identidade/preço/posição, acima da manchete — pré-
existente, não tocado por HIER-02/RITMO-01), bloco 6 (cauda — CTAs/opções),
`FundamentoTabela` (fora do `AtivoCard`, renderizada dentro de
`AnalysisView`), `TimingBadge`/`PlanRuler` internos (não estão na lista
D-14; só o `marginTop` que separa o `TimingBadge` do bloco anterior entra,
porque é "espaço ENTRE blocos"). `font-size`/`raio`/`line-height` inalterados
(D-14) — só `margin`/`padding`/`gap`.

### Mapeamento valor herdado → degrau (D-15)

| Local (citação) | Propriedade | Valor herdado | Degrau `SP` | Novo valor |
|---|---|---|---|---|
| `SinalChip` primário, container (`App.jsx:1393`) | `marginTop` | `11px` | `SP[3]` | `12px` |
| `SinalChip` primário, header (`:1394`) | `gap` | `8px` | `SP[2]` | `8px` (sem mudança) |
| `SinalChip` primário, rótulo do anel (`:1411`) | `marginTop` | `4px` | `SP[1]` | `4px` (sem mudança) |
| `SinalChip` contexto (`:1427`) | `gap` | `4px` | `SP[1]` | `4px` (sem mudança) |
| `SinalChip` contexto (`:1427`) | `padding` vertical | `4px` | `SP[1]` | `4px` (sem mudança) |
| `SinalChip` contexto (`:1427`) | `padding` horizontal | `8px` | `SP[2]` | `8px` (sem mudança) |
| `LinhaContexto` (`:1458`) | `gap` | `8px` | `SP[2]` | `8px` (sem mudança) |
| `LinhaContexto` (`:1458`) | `marginTop` | `11px` | `SP[3]` | `12px` |
| `PlanoOperacionalBloco`, caixa (`:1508`) | `marginTop` | `10px` | `SP[3]` (empate 8/12 → arredonda p/ cima) | `12px` |
| `PlanoOperacionalBloco`, caixa (`:1508`) | `padding` | `11px 12px` | `SP[3]`/`SP[3]` | `12px 12px` |
| `PlanoOperacionalBloco`, linha (`:1515`) | `padding` | `3px 0` | `SP[1]`/`0` | `4px 0` |
| `PlanoOperacionalBloco`, sizing (`:1520`) | `marginTop` | `4px` | `SP[1]` | `4px` (sem mudança) |
| `PlanoOperacionalBloco`, sizing (`:1520`) | `paddingTop` | `7px` | `SP[2]` | `8px` |
| `PlanoOperacionalBloco`, aviso (`:1525`) | `marginTop` | `5px` | `SP[1]` | `4px` |
| `PlanoOperacionalBloco`, motivo operador (`:1529`) | `marginTop` | `9px` | `SP[2]` | `8px` |
| `PlanoOperacionalBloco`, motivo estudo (`:1532`) | `marginTop` | `9px` | `SP[2]` | `8px` |
| `HistoricoPill`, wrapper (`:6777`) | `gap` | `6px` (empate 4/8 → arredonda p/ cima) | `SP[2]` | `8px` |
| `TimingBadge`, gap manchete→timing (`:3358`, o `marginTop` do `SetorAlvo` que envolve o badge) | `marginTop` | `9px` | `SP[2]` | `8px` |
| Elegibilidade, gap plano/contexto→elegibilidade (`:3772`) | `marginTop` | `8px` | `SP[2]` | `8px` (já conforme — sem mudança) |

Todo valor da tabela usa `SP[N]` no código (ex.: `marginTop: SP[3]`), nunca
o número literal — string solta tipo `"12px"` nesses pontos é falha de
guardião. Pontos fora da tabela e fora do escopo do parágrafo acima (padding
do `TimingBadge` em si, header de identidade/preço, `PlanRuler`,
`FundamentoTabela`) continuam com o valor literal herdado — não mexer, para
não abrir escopo de outra tela/bloco nesta fase (D-14 é só o card, blocos
1-5).

### Exceções ópticas (lista fechada, D-16)

Só estas duas — o guardião aceita exatamente esta lista, nenhuma outra
constante `SP_OPTICO_*` nova sem passar por discuss-phase de novo:

| Constante | Valor | Local | Justificativa |
|---|---|---|---|
| `SP_OPTICO_CHIP_PRIMARIO` | `{ v: 9, h: 11 }` (padding `9px 11px`) | `SinalChip` peso `primario`, `App.jsx:3559` | Herdado do `42-UI-SPEC.md` ("developer-approved — matches existing pattern — 2026-09-26"); a Fase 42 já travou este padding como pixel-equivalente ao bloco antigo da manchete — reabrir agora quebraria uma decisão de fase fechada sem novo achado visual. |
| `SP_OPTICO_ANEL` | `36` (diâmetro do `ConfluenceRing`) | `SinalChip` peso `primario`, prop `ring` | Idem — já registrado como exceção fixa no `42-UI-SPEC.md` ("elemento gráfico/SVG, não espaçamento"); RITMO-01 não reabre. |

Guardião novo (`web/tests/test_ritmo_sp.mjs`, nome sugerido): varre o corpo
de `SinalChip`/`LinhaContexto`/`PlanoOperacionalBloco`/`HistoricoPill` e o
trecho do `AtivoCard` entre a manchete e a linha de elegibilidade — falha em
qualquer `px` solto de `margin`/`padding`/`gap` que não seja `SP[N]`,
`SP_OPTICO_CHIP_PRIMARIO`, `SP_OPTICO_ANEL`, ou um dos dois valores
explicitamente fora de escopo (`0`, e o `4px`/`8px` que já eram exatos antes
da tabela, listados só para documentar que não mudam).

---

## Typography

Nenhum tamanho, peso ou line-height novo nesta fase (D-14: fora do escopo
de RITMO-01; CHIP-03 reusa o `SinalChip peso="contexto"` já declarado no
`42-UI-SPEC.md` — 11px/700/1.3, sem peso novo). A tabela do `42-UI-SPEC.md`
segue valendo sem alteração.

| Role | Size | Weight | Line Height | Fonte |
|------|------|--------|-------------|-------|
| Chip contexto (label + valor) | 11px | 700 | 1.3 | herdado, `42-UI-SPEC.md` |
| Marca de alinhamento / linha de contexto / microtexto de reconciliação | 12px | 400 | 1.4 | herdado — o microtexto (HIER-03) usa o MESMO papel tipográfico da linha de contexto, não introduz um novo |

---

## Color

Nenhuma cor nova, nenhum token novo. Os 3 chips da "Leitura da IA" (CHIP-03)
são **neutros** — `SinalChip peso="contexto"` sem prop `estado`, que já cai
no ramo padrão (`T.textPrimary`/`T.textFaint`, borda `T.borderSubtle`, sem
fundo). `DIR_STYLE`/`SCALE_STYLE` (que coloriam direção/convicção/qualidade
com `T.positive`/`T.negative`/`T.accent`) são apagados junto com
`KpiBlock`/`KpiCell` — a cor de mercado deixa de tocar esses três valores em
QUALQUER lugar do app.

### Ban list (grep guardião, extensão do 42-UI-SPEC)

- Nenhum dos 3 chips de `AnalysisView` (direção/convicção/qualidade) usa
  `T.positive`/`T.negative`/`T.accent`/`T.warn` — nem via prop `estado`, nem
  via cor livre (D-02: "neutros, sem verde/vermelho").
- `DIR_STYLE` e `SCALE_STYLE` não existem mais em `web/src/App.jsx` (grep:
  zero ocorrência) — eram a única fonte de cor de mercado nesses três
  valores.
- O microtexto de reconciliação (HIER-03) não introduz cor nova: o chip de
  estado que o acompanha já é o `SinalChip` de elegibilidade existente
  (âmbar/neutro, aprovado na Fase 42) — o TEXTO ao lado é `T.textSecondary`
  (mesmo papel da linha de contexto), nunca colorido por estado.

---

## Component Contract — Leitura da IA (CHIP-03)

### `KpiBlock`/`KpiCell` apagados

`KpiBlock` (`App.jsx:1338-1367`), `KpiCell` (`:1327-1336`), `DIR_STYLE`
(`:1072-1076`) e `SCALE_STYLE` (`:1077-1080`) são removidos por inteiro —
código morto desde qa/49 (achado do scout, D-01), sem call site em produção.

**Guardiões a reconciliar (D-05), nunca apagar, nota datada "REVERSÃO
DELIBERADA — 2026-XX-XX, Fase 43, ID-CHIP-03":**

- `web/tests/test_decisao_modo.mjs` (linhas ~38-58) — testa hoje o rótulo
  mode-aware e o `rec` mapeado DENTRO de `KpiBlock`. Reescrever as
  asserções para o que substitui a única parte que sobrevive (o rótulo
  mode-aware da manchete "DECISÃO DA MESA"/"PLANO EDUCACIONAL" já é
  `SinalChip peso="primario"`, coberto por outro guardião da Fase 42 —
  `kicker`). A parte que NÃO sobrevive (mapa `rec`→cor de
  direção/convicção/qualidade) não tem substituto: nota datada explicando
  que a IA parou de recomendar cor nesses três valores por decisão de
  produto (D-03: "a recomendação da IA não vira chip").
- `web/tests/test_hero_reconciliado.mjs` (linha ~57) — a asserção "KpiBlock
  não é mais renderizado no card do ativo" continua VERDADEIRA depois da
  remoção (checa ausência, não presença) — sem edição necessária, só nota
  confirmando que a função nem existe mais no arquivo.
- Grep de `DIR_STYLE`/`SCALE_STYLE`/`KpiBlock`/`KpiCell` em qualquer outro
  `.mjs` antes de fechar a fase — nenhum encontrado na varredura desta
  pesquisa, mas o planner deve reconfirmar no momento da implementação
  (drift possível entre a pesquisa e a execução).

### Os 3 chips (novo local: `AnalysisView`)

Renderizados em `AnalysisView` (`App.jsx:1616`), entre o corpo da análise
(`Markdown`/`semDados`) e o bloco de "FATOS RELEVANTES" (antes da linha
`{Array.isArray(d.fatos) ...}`, `:1653`) — só quando `an.kpis` existe (D-04).
No caminho determinístico (`an.fonte === "deterministico"`, sem `kpis`), a
linha inteira é omitida — nunca placeholder, nunca "—" inventado.

```jsx
{an.kpis && (
  <div style={{ marginTop: SP[4] }}>
    <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.05em", color: T.textFaint, marginBottom: SP[1] }}>
      LEITURA DA IA
    </div>
    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: SP[2] }}>
      {an.kpis.direcao && (
        <>
          {an.kpis.direcao === "Alta" && <span aria-hidden="true" style={{ fontSize: "12px", color: T.textSecondary }}>↗</span>}
          {an.kpis.direcao === "Baixa" && <span aria-hidden="true" style={{ fontSize: "12px", color: T.textSecondary }}>↘</span>}
          <SinalChip peso="contexto" label="DIREÇÃO" value={an.kpis.direcao}
            ariaLabel={`Direção da leitura da IA: ${an.kpis.direcao}`} />
        </>
      )}
      {an.kpis.conviccao && (
        <SinalChip peso="contexto" label="CONVICÇÃO" value={an.kpis.conviccao}
          ariaLabel={`Convicção da leitura da IA: ${an.kpis.conviccao}`} />
      )}
      {an.kpis.qualidade && (
        <SinalChip peso="contexto" label="QUALIDADE" value={an.kpis.qualidade}
          ariaLabel={`Qualidade da leitura da IA: ${an.kpis.qualidade}`} />
      )}
    </div>
  </div>
)}
```

- `an.kpis.recomendacao` **não aparece** aqui (D-03) — só direção/convicção/
  qualidade.
- Nenhum `estado`/cor por chip — os três são o ramo neutro padrão do
  `SinalChip peso="contexto"` (sem prop `estado`).
- Seta (↗/↘) é elemento `aria-hidden` SEPARADO do chip, antes dele — não vai
  dentro de `value` (evita o leitor de tela ler o glifo Unicode como um
  segundo texto confuso; a leitura completa mora só no `ariaLabel`).
  `Lateral` não recebe seta (sem direção definida).
- Rótulo da linha ("LEITURA DA IA") é string nova em `copy.js`
  (`COPY.estudo`/`COPY.operador`, idêntica nos dois — é rótulo de seção, não
  interpretação por modo).
- `an.kpis.recomendacao` continua existindo no payload (usado por
  `Markdown`/`AiNote` em outros pontos de `AnalysisView`) — só não vira
  chip.
- Radar "Aprofundar com IA" (`scan_deep`, Claude's Discretion): se o payload
  trouxer `kpis`, aplica a MESMA linha (mesmo componente); se não trouxer,
  omite — nunca inventa.

---

## Microtexto de reconciliação (HIER-03)

### Fonte de dado e vocabulário

Novo dict em `server/app/skill_ref.py`, mesma seção do `HISTORICO`/
`HISTORICO_ROTULO` (~l.355-410), mesmo padrão de função espelhada:

```python
# --- Reconciliação sinal técnico × histórico medido (HIER-03) --------------
# O padrão bateu os critérios (sinal técnico, setups.py) e o histórico medido
# (signal_ledger, ADR-017 Bloco 1) são DUAS perguntas diferentes — este
# vocabulário é a frase que conecta as duas sem fundi-las num veredito só
# (guardrail ADR-017: decisão × elegibilidade nunca em síntese). `n`/`janela`
# nunca são omitidos nem inventados (D-08); Estudo explica o "por que
# importa" (duas orações), Operador é fato curto com os três números.
RECONCILIACAO_ELEGIBILIDADE = {
    "operador": {
        "elegivel": "Critérios ok · vantagem medida (n={n}, {janela}, {expR})",
        "inelegivel": "Critérios ok · sem vantagem medida (n={n}, {janela}, {expR})",
        "insuficiente": "Critérios ok · amostra insuficiente (n={n} — pouco para medir)",
        "nunca_medido": "Critérios ok · sem histórico medido",
        "aposentado": "Padrão identificado · sem vantagem medida em 15 anos (ADR-016)",
    },
    "educacional": {
        "elegivel": "O padrão bateu os critérios, e em {n} ocorrências na janela {janela} houve vantagem medida.",
        "inelegivel": "O padrão bateu os critérios, mas em {n} ocorrências na janela {janela} não houve vantagem medida.",
        "insuficiente": "O padrão bateu os critérios; só {n} ocorrências — pouco para medir.",
        "nunca_medido": "O padrão bateu os critérios; ainda sem histórico medido.",
        "aposentado": "Padrão identificado; sem vantagem medida em 15 anos (ADR-016).",
    },
}

# Cláusula "por que importa" (D-11): só o Modo Estudo a exibe, e é TOCÁVEL
# no front (abre setorId="analise" → conceito "confluencia", existente —
# nenhum conceito novo). String FIXA, sem interpolação — por isso não é uma
# função, é o mesmo padrão de `PRINCIPIOS`/frase única do módulo. O front
# nunca compõe esta frase a partir de outra coisa; ela vem pronta de aqui,
# como QUALQUER texto desta camada (regra da casa, didatica-boris/SKILL.md).
RECONCILIACAO_POR_QUE_IMPORTA = "sinal técnico e histórico medido são coisas diferentes"


def reconciliacao_elegibilidade_txt(modo: str, estado: str, n=None, janela: str = "", exp_r=None) -> str:
    """Frase de reconciliação por modo/estado — só o FATO (sem a cláusula
    "por que importa", que o front busca separado, ver
    RECONCILIACAO_POR_QUE_IMPORTA, e só anexa no Estudo). `n` nunca vira 0
    quando é None — cai no placeholder "?" como o resto da casa
    (historico_txt)."""
    d = RECONCILIACAO_ELEGIBILIDADE.get(modo if modo in RECONCILIACAO_ELEGIBILIDADE else "educacional",
                                         RECONCILIACAO_ELEGIBILIDADE["educacional"])
    frase = d.get(estado) or d["nunca_medido"]
    exp_txt = "" if exp_r is None else (("+" if exp_r >= 0 else "−") + f"{abs(exp_r):.3f}".replace(".", ",") + "R")
    return (frase
            .replace("{n}", str(n) if n is not None else "?")
            .replace("{janela}", janela or "?")
            .replace("{expR}", exp_txt or "?"))
```

Espelho em `web/src/copy.js`, ao lado de `historicoTxt`:

```js
// Espelho de skill_ref.reconciliacao_elegibilidade_txt (Fase 43, HIER-03) —
// só o FATO. A cláusula "por que importa" é exportada separada (constante
// fixa, sem interpolação), espelho de RECONCILIACAO_POR_QUE_IMPORTA.
export function reconciliacaoTxt(mode, estado, vals) {
  const d = copyFor(mode).reconciliacaoElegibilidade;
  const frase = d[estado] || d.nunca_medido;
  const n = vals && vals.n;
  const expR = vals && typeof vals.expR === "number" ? vals.expR : null;
  const expTxt = expR == null ? "" : (expR >= 0 ? "+" : "−") + Math.abs(expR).toFixed(3).replace(".", ",") + "R";
  return frase
    .replace("{n}", n != null ? String(n) : "?")
    .replace("{janela}", (vals && vals.janela) || "?")
    .replace("{expR}", expTxt || "?");
}

// Fixa, sem interpolação, só Estudo (D-11/D-12) — HistoricoPill anexa isto
// como cláusula TOCÁVEL, nunca a compõe/parafraseia.
export const reconciliacaoPorQueImporta = "sinal técnico e histórico medido são coisas diferentes";
```

`web/src/copy.js` ganha o objeto `reconciliacaoElegibilidade` dentro de
`COPY.estudo`/`COPY.operador`, com as mesmas 5 chaves × 2 modos do dict
Python acima — agora só o FATO, sem a cláusula (paridade coberta pelo
guardião cruzado existente — mesmo padrão de `historico`/`entradaAuto`).
`reconciliacaoPorQueImporta` é export solto (não dentro de `COPY.estudo`/
`COPY.operador`) porque não varia por modo nem por estado — é usada só pelo
call site do Estudo.

### Onde renderiza (D-09)

**Só na linha de elegibilidade do `AtivoCard`** (`App.jsx:3771-3775`,
Watchlist e Radar) — o `HistoricoPill` chamado DAQUI ganha uma nova prop
booleana, ex. `microtexto`, que substitui os números crus pela frase:

```jsx
<HistoricoPill historico={sc.setupHistorico} elegivel={sc.setupElegivel}
  operador={operador} microtexto A={A} didatica={didatica} dados={dadosDoCard} />
```

As listas por setup (cauda do Radar, lista do Operador IA,
`App.jsx:~7095`) e o modo `compacto` continuam chamando `HistoricoPill` SEM
`microtexto`/`A`/`didatica`/`dados` — mantêm chip + números crus, porque ali
o usuário compara setups lado a lado (D-09). `HistoricoPill` passa a ter
três formas mutuamente exclusivas de exibir o dado além do chip: números
crus (default), compacto (só chip), microtexto (frase por modo).

```jsx
function HistoricoPill({ historico, elegivel, aposentado, operador, hojeYmd, compacto, microtexto, A, didatica, dados }) {
  // ...estado/modoJS/cp/rotulo/hoje/refYmd/velho/ariaLabel iguais...
  const expRJanela = /* igual */;
  const nJanela = /* igual */;
  const janelaRef = /* igual */;
  // reconciliacaoTxt devolve SÓ o fato (D-08) — a cláusula "por que importa"
  // é uma string SEPARADA (reconciliacaoPorQueImporta), nunca concatenada
  // no backend/copy.js: o front precisa da fronteira entre as duas para
  // tornar só a segunda tocável (D-11). Compor a fronteira aqui (split de
  // string) violaria "o front não compõe vocabulário" (didatica-boris) —
  // por isso são DUAS strings prontas, não uma cortada.
  const fato = microtexto
    ? reconciliacaoTxt(modoJS, estado, { n: nJanela, janela: janelaRef, expR: expRJanela })
    : null;
  return (
    <span style={{ display: "inline-flex", alignItems: microtexto ? "flex-start" : "center", gap: SP[2], flexWrap: "wrap" }}>
      <SinalChip peso="contexto" estado={estado} value={rotulo} ariaLabel={ariaLabel} />
      {microtexto && fato && (
        <span style={{ fontSize: "12px", fontWeight: 400, lineHeight: 1.4, color: T.textSecondary, flex: "1 1 auto", minWidth: "0" }}>
          {fato}
          {/* D-12: Operador não recebe a cláusula — fato curto basta */}
          {!operador && (
            <>
              {" — "}
              <SetorAlvo setorId="analise" rotulo="a confluência" A={A} didatica={didatica} dados={dados} style={{ display: "inline" }}>
                <span style={SUBLINHADO}>{reconciliacaoPorQueImporta}</span>
              </SetorAlvo>
            </>
          )}
        </span>
      )}
      {!microtexto && !compacto && (expRJanela != null || nJanela != null || janelaRef) && (
        /* números crus — bloco existente, inalterado */
      )}
      {velho && refYmd && (
        <span style={{ fontSize: "11px", fontWeight: 400, lineHeight: 1.4, color: T.textDim }}>⏱ {refYmd}</span>
      )}
    </span>
  );
}
```

- D-10 preservado: o modificador `desatualizado` (⏱ `{medidoAte}`) continua
  depois da frase, sem mudança.
- `expR` sai da linha no Estudo (D-07) porque a frase Estudo não interpola
  `{expR}` (o template `educacional` acima não tem esse placeholder) — mas
  continua no `ariaLabel` (já vem de `historicoTxt`, que não muda). No
  Operador o `expR` volta DENTRO da frase (`{expR}` no template `operador`).
- `n`/`janela` nunca são omitidos (D-08): se `nJanela`/`janelaRef` forem
  `null` (estado `nunca_medido`, por exemplo), o template daquele estado
  simplesmente não usa `{n}`/`{janela}` — nenhum placeholder "?" aparece na
  tela porque o texto do estado já foi escrito para não precisar deles.

### Tom por modo (D-11/D-12) — oração tocável do Estudo

A cláusula "por que importa" (`reconciliacaoPorQueImporta`/
`RECONCILIACAO_POR_QUE_IMPORTA`, string FIXA e SEPARADA do fato — ver
"Fonte de dado e vocabulário" acima) é **tocável** e abre um conceito já
existente na camada de entendimento — **nenhum conceito novo é criado**
(regra da casa, D-11). O verbete mais próximo já existe:
`CONCEITOS["confluencia"]` (`server/app/conceitos.py:242`), cujo campo
`naoAcontece` já diz "Confluência NÃO é probabilidade de dar certo... e nada
além disso" — a MESMA distinção entre sinal técnico e chance/vantagem
estatística, só que hoje ancorada só no setor `analise` (o anel/manchete).
O bloco `HistoricoPill` (seção anterior) já mostra o mecanismo exato: o fato
(`reconciliacaoTxt`) e a cláusula são DUAS strings prontas, nunca uma
cortada no front — só a segunda entra no `SetorAlvo`:

```jsx
{" — "}
<SetorAlvo setorId="analise" rotulo="a confluência" A={A} didatica={didatica} dados={dados} style={{ display: "inline" }}>
  <span style={SUBLINHADO}>{reconciliacaoPorQueImporta}</span>
</SetorAlvo>
```

- Não cria `setorId` novo, não edita `conceitos.py` — a distinção que a
  frase nova ensina JÁ está no verbete `confluencia`; a cláusula tocável só
  aponta pra lá com um termo-âncora diferente do que já existe ao lado do
  anel (dois pontos de entrada para o mesmo conceito, prática já usada por
  `SETORES` — ex. "timing"/"barra" são dois setores aninhados pro mesmo
  card).
- O Operador **não** tem cláusula tocável (D-12: fato curto, sem "por que
  importa" — a mesa já sabe) — o `!operador` no JSX acima é o gate.
- `HistoricoPill` recebe `A`/`didatica`/`dados` como novas props opcionais,
  só passadas pelo call site do `AtivoCard` (Estudo E Operador — o Operador
  simplesmente não usa, porque `!operador` esconde o `SetorAlvo`). Os call
  sites de lista/compacto não passam nada disso, então a cláusula tocável
  nunca aparece fora do `AtivoCard`.

---

## Fold-ins (pendências da Fase 42)

### D-17 — "FUNDAMENTO" duplicado

`FundamentoTabela` (`App.jsx:1558-1593`): o `SinalChip` da linha 1576 perde
a prop `label` — fica só `<SinalChip peso="contexto" value={f.score}
ariaLabel={ariaFundamento(f.score, "estudo")} />`. O cabeçalho
`<span>FUNDAMENTO</span>` (linha 1572) continua igual. `ariaLabel` não
muda — o texto acessível já dizia "Fundamento: qualidade..." mesmo sem o
`label` visual redundante.

### D-18 — alvo de toque do chip de fundamento < 44px

`LinhaContexto` (`App.jsx:1473`): o `SetorAlvo setorId="fundamento"` que
envolve o `SinalChip` de fundamento ganha uma camada de toque invisível
maior que o visual, sem alterar layout dos irmãos na linha (`flex-wrap`,
`gap: SP[2]`) — técnica de padding + margem negativa equivalente (não
`minWidth`/`minHeight` direto no `SetorAlvo`, que empurraria os chips
vizinhos, diferente do caso do anel na Fase 42 que está sozinho numa linha
`space-between`):

```jsx
<SetorAlvo setorId="fundamento" rotulo="o fundamento" A={A} didatica={didatica} dados={dados}
  style={{ display: "inline-flex", padding: "10px 6px", margin: "-10px -6px" }}>
  <SinalChip peso="contexto" label="FUNDAMENTO" value={score} explicavel ariaLabel={ariaFundamento(score, modo)} />
</SetorAlvo>
```

- Chip visual não muda de tamanho (padding compensado por margem negativa
  igual e de sinal oposto — a caixa de LAYOUT do `SetorAlvo` volta ao
  tamanho original; só a caixa de TOQUE, antes do cancelamento de margem,
  fica maior).
- Executor confirma no devtools (bounding box computado) que o resultado
  chega a ≥44×44px para o valor típico (score é sempre 1 caractere — "A"/
  "B"/"C"); se a fonte/padding herdados renderizarem uma caixa menor que o
  esperado, ajustar os dois números (padding/margin) juntos, sempre
  simétricos e de sinal oposto — nunca só um dos dois (quebraria o
  cancelamento de layout).
- Mesmo padrão pode ser aplicado a qualquer outro alvo <44px encontrado
  durante a implementação desta fase (achado, não obrigação — só o chip de
  fundamento está na pendência nomeada da Fase 42).

---

## Copywriting Contract

| Elemento | Copy | Fonte |
|----------|------|-------|
| Rótulo da seção de chips da IA | `"LEITURA DA IA"` | novo — `copy.js`, comum aos 2 modos (rótulo de seção, não interpretação) |
| Chip direção (valor) | `an.kpis.direcao` cru (`"Alta"`/`"Baixa"`/`"Lateral"`) | motor/IA, sem tradução — já vem em pt-BR |
| aria-label chip direção | `"Direção da leitura da IA: {valor}"` | novo |
| aria-label chip convicção | `"Convicção da leitura da IA: {valor}"` | novo |
| aria-label chip qualidade | `"Qualidade da leitura da IA: {valor}"` | novo |
| Microtexto — Operador, elegível | `"Critérios ok · vantagem medida (n={n}, {janela}, {expR})"` | novo — `skill_ref.py`/`copy.js` |
| Microtexto — Operador, inelegível | `"Critérios ok · sem vantagem medida (n={n}, {janela}, {expR})"` | idem (exemplo aprovado no 43-CONTEXT) |
| Microtexto — Operador, insuficiente | `"Critérios ok · amostra insuficiente (n={n} — pouco para medir)"` | idem |
| Microtexto — Operador, nunca medido | `"Critérios ok · sem histórico medido"` | idem |
| Microtexto — Operador, aposentado | `"Padrão identificado · sem vantagem medida em 15 anos (ADR-016)"` | idem |
| Microtexto — Estudo, elegível (fato) | `"O padrão bateu os critérios, e em {n} ocorrências na janela {janela} houve vantagem medida."` | novo — `skill_ref.py`/`copy.js` |
| Microtexto — Estudo, inelegível (fato) | `"O padrão bateu os critérios, mas em {n} ocorrências na janela {janela} não houve vantagem medida."` | idem (exemplo aprovado no 43-CONTEXT, sem a cláusula que virou string própria) |
| Microtexto — Estudo, insuficiente (fato) | `"O padrão bateu os critérios; só {n} ocorrências — pouco para medir."` | idem |
| Microtexto — Estudo, nunca medido (fato) | `"O padrão bateu os critérios; ainda sem histórico medido."` | idem |
| Microtexto — Estudo, aposentado (fato) | `"Padrão identificado; sem vantagem medida em 15 anos (ADR-016)."` | idem |
| Cláusula tocável (Estudo, anexada após o fato com `" — "`, string SEPARADA — `reconciliacaoPorQueImporta`) | `"sinal técnico e histórico medido são coisas diferentes"` — abre `setorId="analise"` (concept `confluencia`, existente) | reuso — nenhum conceito novo (D-11); nunca concatenada no backend, sempre renderizada como elemento tocável distinto |

Todas as strings novas vivem em `server/app/skill_ref.py`
(`RECONCILIACAO_ELEGIBILIDADE`) + espelho em `web/src/copy.js`
(`COPY.estudo/operador.reconciliacaoElegibilidade`) para o microtexto, e em
`web/src/copy.js` puro para o rótulo "LEITURA DA IA" e os 3 aria-labels
(fatos do motor/IA, sem variação por modo, mesmo padrão do
`42-UI-SPEC.md` para os textos comuns). Nenhuma string solta em
`AnalysisView`/`HistoricoPill`.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | nenhum — projeto não usa shadcn | not applicable |
| third-party | nenhum | not applicable |

---

## Acessibilidade

- Os 3 chips da "Leitura da IA" seguem o contrato de `SinalChip` já
  auditado na Fase 42 (`aria-label` obrigatório, glifo decorativo
  `aria-hidden`). A seta ↗/↘ é elemento separado `aria-hidden`, nunca dentro
  do texto lido — a informação de direção mora só no `ariaLabel` do chip.
- O microtexto de reconciliação SUBSTITUI o texto acessível anterior (que já
  vinha de `historicoTxt`, preservado no `ariaLabel` do chip de estado) —
  ninguém perde informação: quem usa leitor de tela ouve o `ariaLabel` do
  `SinalChip` (frase completa do estado) e, se sighted, lê também a frase
  visível ao lado (mesma informação, formas diferentes — não duas fontes
  conflitantes, porque o `ariaLabel` de `historicoTxt` e a frase de
  `reconciliacaoTxt` descrevem o MESMO estado, só com granularidade
  diferente: uma é a base "elegível/inelegível/...", a outra reconcilia com
  o "bateu os critérios").
- Cláusula tocável do Estudo (D-11): usa o mesmo padrão de `SetorAlvo` já
  testado (`SUBLINHADO` + toque simples + botão sr-only "O que é a
  confluência?" — herdado do setor `analise`, sem botão novo).
- D-18 (fundamento <44px): ver seção "Fold-ins" — corrigido por área de
  toque, não por tamanho visual, sem regressão de layout dos chips vizinhos
  na `LinhaContexto`.
- Nenhuma cor nova nem contraste novo a recalcular nesta fase (ver seção
  Color) — os tokens já auditados na Fase 42 (`warnTint10`, `textPrimary`,
  `textFaint`, `textSecondary`) continuam sendo os únicos usados.

---

## Checkpoint humano (SC#4)

Roteiro mínimo para o checkpoint ao vivo do Alex, nos dois modos:

1. Abrir a Watchlist, localizar o card de UGPA3 (ou equivalente com setup +
   histórico medido) — em Estudo, ler a linha de elegibilidade e confirmar
   que a frase de reconciliação aparece (não os números crus) e que a
   cláusula final é tocável (abre o conceito de confluência).
2. Trocar para Operador no mesmo card — confirmar a frase curta com
   `n`/janela/`expR` (quando `elegivel`/`inelegivel`) e SEM a cláusula
   tocável.
3. Abrir a leitura da IA (Watchlist, análise expandida) e confirmar os 3
   chips neutros (direção com seta, convicção, qualidade) sob o rótulo
   "Leitura da IA" — nenhuma cor de mercado neles, nenhuma recomendação
   duplicada.
4. Olhar o card inteiro e confirmar visualmente que o ritmo entre os blocos
   ficou mais regular (sem exigir medição em px do Alex — é leitura de "não
   parece mais espremido/desalinhado", não um teste de régua).
5. Confirmar em <3s o veredito × contexto, como nos checkpoints anteriores
   (SC#4 do ROADMAP).

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
