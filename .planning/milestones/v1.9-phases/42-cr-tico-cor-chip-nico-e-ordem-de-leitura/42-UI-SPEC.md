---
phase: 42
slug: cr-tico-cor-chip-nico-e-ordem-de-leitura
status: approved
reviewed_at: 2026-09-26
shadcn_initialized: false
preset: none
created: 2026-09-26
---

# Phase 42 — UI Design Contract

> Contrato visual/interação para `AtivoCard` (`web/src/App.jsx:3368`) e o
> cabeçalho do Radar que o reaproveita (`App.jsx:~6869-6960`). Verificado por
> `gsd-ui-checker`; fonte de verdade para `gsd-planner`/`gsd-executor`.
> Escopo travado por `42-CONTEXT.md` (D-01..D-16) — não reabre decisões.
>
> **Revisão 2026-09-26** (achados do checker): (1) tipografia reduzida a 2
> pesos novos declarados, com tabela de exceções herdadas citando `App.jsx`;
> (2) `SinalChip peso="primario"` deixa de ser contrato sem call site — passa
> a ser o bloco da manchete do `AtivoCard`, com 2 usos reais (watchlist e
> radar, mesmo componente); (3) `warnTint10` do tema claro recalculado com
> a tensão entre piso de alpha (≥4%) e meta de contraste (≥4,7:1) exposta
> explicitamente, não escondida atrás de um número só.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none — sem shadcn/Tailwind/component lib; design system é o conjunto de tokens `T.x` (CSS vars) já existente em `PALETTE`/`MODE_OPERADOR` |
| Preset | not applicable |
| Component library | none — React puro, estilo inline, sem Radix/base-ui |
| Icon library | none — glifos Unicode inline (`✓`, `↗`, `↘`, `▲`, `▼`, `⏱`) e SVG à mão (`TierDot`, `ConfluenceRing`); nenhuma lib nova entra nesta fase |
| Font | Corpo/label: Nunito (`SANS`, `App.jsx:303`). Manchete/números de destaque: Fredoka 600 (`DISPLAY`, `App.jsx:305`) |

---

## Spacing Scale

Escala global 4/8pt (RITMO-01, Fase 43) **não** é migrada nesta fase — o card
mantém seus valores herdados (10px/10.5px/11px/11.5px/12px/12.5px/17px) fora
dos elementos NOVOS. Os elementos novos desta fase (`SinalChip`, rótulo do
anel, marcas de alinhamento, linha de elegibilidade) usam a escala abaixo
para não aumentar a dívida que a Fase 43 vai herdar. O bloco da manchete
(agora `SinalChip peso="primario"`) preserva seu padding herdado — ver
"Inherited exceptions" na seção Typography.

| Token | Value | Usage nesta fase |
|-------|-------|-------------------|
| xs | 4px | gap interno do `SinalChip` (label↔valor), gap glifo↔texto nas marcas de alinhamento |
| sm | 8px | padding horizontal do `SinalChip` peso `contexto`; gap entre chips na linha de contexto |
| md | 16px | não usado nesta fase (blocos herdados seguem com seus próprios `marginTop`) |
| — | 44px | exceção: alvo de toque mínimo do `SetorAlvo` que envolve o anel de confluência (ver Acessibilidade) — obrigatório por acessibilidade, não é múltiplo de 4/8 por design, é o piso de toque padrão |

Exceptions: `ConfluenceRing` mede 36px visualmente (D-08, fixo); o alvo de
toque do `SetorAlvo` que o envolve é 44×44px via padding invisível (ver
seção Acessibilidade) — o visual não muda, só a área clicável. Padding do
`SinalChip peso="primario"` (9px 11px) é herdado — ver Typography.

---

## Typography

**Pesos novos declarados nesta fase: apenas 2 — 400 (regular) e 700
(bold).** Nenhum elemento NOVO usa um terceiro peso.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Chip contexto (label + valor) | 11px | 700 | 1.3 |
| Marca de alinhamento / linha de contexto | 12px | 400 | 1.4 |
| Rótulo do anel (confluência·tier·lado·setup) | 12px | 700 | 1.3 |

(A revisão anterior desta tabela listava um terceiro peso, 600, para o
rótulo do anel — corrigido: o rótulo do anel usa 700, igual ao `SinalChip`.
O número `%` renderizado dentro do SVG do anel é um elemento SEPARADO,
pré-existente, listado abaixo como exceção herdada, não um terceiro peso da
UI nova.)

### Inherited exceptions (pré-existentes, não contam para o limite de pesos)

| Elemento | Tamanho/peso | Citação | Status |
|----------|--------------|---------|--------|
| Número `%` dentro do SVG do `ConfluenceRing` (`fontFamily={MONO} fontWeight="800"`) | `Math.round(size*0.26)`px / 800, mono | `web/src/App.jsx:6566` | developer-approved — matches existing pattern — 2026-09-26 |
| `SinalChip peso="primario"` — kicker ("DECISÃO DA MESA"/"PLANO EDUCACIONAL") | 10px / 400, `letterSpacing: 0.04em` | `web/src/App.jsx:3560` (bloco que o `SinalChip` substitui, visual pixel-equivalente) | developer-approved — matches existing pattern — 2026-09-26 |
| `SinalChip peso="primario"` — valor da decisão (`decM`) | 17px / 800 | `web/src/App.jsx:3561` (idem) | developer-approved — matches existing pattern — 2026-09-26 |

Estas 2 exceções (800 no anel, 800 no valor da manchete) são herdadas
byte-a-byte do código atual — a fase não introduz peso novo nelas, só
realoca o mesmo visual para dentro do componente `SinalChip`/`ConfluenceRing`.

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `T.bgBase` (dark `#10121a` / light `#f7f8fc`; Operador dark `#0a0c12` / light `#f2f6f4`) | fundo da tela |
| Secondary (30%) | `T.bgCard` (dark `#1b1f2e` / light `#ffffff`; Operador dark `#141926` / light `#ffffff`) | `AtivoCard`, chips com fundo (`bgBase` interno) |
| Accent (10%) | `T.accent` (dark `#2fa8a0`/`#d4af37` Operador; light `#1f7d76`/`#8a6c1c` Operador) | reservado a: gatilho "AGUARDAR CONFIRMAÇÃO" na manchete (`REC_STYLE`, agora dentro do `SinalChip peso="primario"`), toques/CTAs fora do card. **Nenhum `SinalChip` de contexto usa `T.accent` como cor de valor** |
| Destructive/Warn | `T.warn` (dark `#fbbf24` / light `#a16207`) | estado "sem vantagem estatística medida" (inelegível) — único uso de cor fora do par positive/negative dentro de chips de contexto |

Accent reserved for: manchete "AGUARDAR CONFIRMAÇÃO" (dentro do `SinalChip
peso="primario"`, cor resolvida internamente via `REC_STYLE`, nunca por prop
livre), elementos de navegação/CTA fora do `AtivoCard`. Nunca em `SinalChip`
peso `contexto`, nunca no arco do `ConfluenceRing`.

### Token novo: `warnTint10`

D-03 pede tint dedicado, sem hex solto. Contraste calculado (fórmula WCAG,
luminância relativa) do par texto `T.warn` sólido sobre o tint blendado com
`bgCard`, nas 4 combinações:

| Combo | `bgCard` | Alpha do tint | Cor blendada | Contraste texto×tint |
|-------|----------|----------------|---------------|------------------------|
| dark · estudo | `#1b1f2e` | 10% | `rgb(49,47,45)` | **7,98:1** — passa AA |
| dark · operador | `#141926` | 10% | `rgb(43,42,38)` | **8,64:1** — passa AA |
| light · estudo | `#ffffff` | 4% | `rgb(251,249,245)` | **4,68:1** — passa AA (mín. 4,5:1) |
| light · operador | `#ffffff` | 4% | `rgb(251,249,245)` | **4,68:1** — passa AA (mesmo `bgCard` do estudo) |

**Tensão exposta, não escondida:** o pedido de recontagem pedia ≥4,7:1 no
tema claro sem baixar o alpha do piso de 4% (abaixo disso o tint deixa de
ser perceptível como tint). Os dois alvos são mutuamente exclusivos neste
par de cores — a curva medida:

| Alpha | Contraste (light) |
|-------|---------------------|
| 4,0% | 4,68:1 |
| 3,8% | 4,69:1 |
| 3,6% | 4,70:1 (atinge a meta, mas fica abaixo do piso de 4%) |
| 3,0% | 4,74:1 |

**Decisão:** manter o piso de 4% (tint precisa continuar visível como tint,
não só como ruído de antialiasing) e aceitar 4,68:1 — 0,18 abaixo da meta de
4,7, mas 0,18 ACIMA do mínimo legal AA de 4,5:1 exigido pelo requisito
COR-01 original. `T.warn` (hex do texto) não muda, como pedido — só o alpha
do tint foi ajustado. Se o Alex preferir fechar exatamente em 4,7:1, a
alternativa registrada é aceitar alpha 3,6% (perceptibilidade reduzida) —
decisão de produto, não de acessibilidade (a meta legal de 4,5:1 já está
superada nas duas opções).

Valores declarados em `PALETTE` (sem hex solto no componente):

```js
// PALETTE.dark
warnTint10: "rgba(251,191,36,0.10)",   // #fbbf24 a 10% — 7,98:1 pior caso (estudo); 8,64:1 Operador
// PALETTE.light
warnTint10: "rgba(161,98,7,0.04)",     // #a16207 a 4% — 4,68:1 nas 2 combinações (mesmo bgCard)
```

`MODE_OPERADOR` **não precisa de override** de `warnTint10`: no dark os dois
`bgCard` do modo (estudo/operador) já passam com o mesmo alpha 10%; no light
os dois modos compartilham o mesmo `bgCard` (`#ffffff`), então o mesmo alpha
4% cobre ambos. Texto do chip inelegível continua `T.warn` sólido (já mede
4,92:1 contra `bgCard` branco e 7,98–8,64:1 contra os `bgCard` escuros —
muito acima do piso, independente do alpha do tint).

### Ban list (grep guardião)

- `HISTORICO_PILL_STYLE` não referencia `T.positive` nem `T.negative` (D-04,
  critério de aceite #1 do ROADMAP).
- Nenhum `SinalChip` peso `contexto` usa `T.positive`/`T.negative` como cor
  de valor (D-05/D-06). Regime ALTA/BAIXA e Fundamento A/B/C perdem
  `SCORE_COLOR`/`REGIME_STYLE` como fonte de cor — valor vira texto forte
  neutro (`T.textPrimary`).
- Marcas de alinhamento ("a favor"/"contra") nunca usam `T.warn` (D-07) nem
  `T.positive`/`T.negative` — só `T.textSecondary`.
- Arco do `ConfluenceRing` não usa `T.positive`/`T.negative`/`T.accent`.
- `SinalChip peso="primario"` é o ÚNICO lugar do card novo que pode usar
  `T.positive`/`T.negative`/`T.accent` (via `REC_STYLE`, resolvido
  internamente) — nenhum outro `SinalChip` (`peso="contexto"`) herda essa
  permissão.

### `ConfluenceRing` — cor do arco (decisão desta fase)

Hoje: `col = c>=75 ? P.positive : c>=50 ? P.accent : P.textFaint` — colide
com D-05 (verde ao lado de uma manchete VENDER). **Decisão: reusar
`TIER_FILL`** (`App.jsx:1098`, já existe como "outro eixo semântico" e já é
decorativo/`aria-hidden` no precedente `TierDot`):

```js
TIER_FILL = { forte: "#22c55e", moderada: "#f59e0b", neutra: "#9ca3af", fraca: "#ef4444" }
```

Mapeamento: `tierOf(conf)` já devolve o id do tier (`forte`/`moderada`/
`neutra`/`fraca`) — o arco usa `TIER_FILL[tierOf(conf)[0]]` em vez de
`P.positive`/`P.accent`/`P.textFaint`. Justificativa: (1) mantém uma FONTE
ÚNICA de cor de tier no app (o mesmo mapeamento do `TierDot`, sem inventar
uma terceira paleta); (2) `TIER_FILL` já é literal/hex fora de `T.x` por
decisão de produto anterior ("reusar T.positive/negative/warn aqui
recolocaria o tier em cima do vocabulário de sinal de mercado" — comentário
em `App.jsx:1093-1097`), então herdar o mesmo racional para o arco é
consistente, não uma exceção nova; (3) evita qualquer leitura "verde = boa
notícia" ao lado de uma manchete VENDER. Nota: como D-10 esconde o anel sem
setup, o tier `fraca` (conf ≤ 0) não deve aparecer na prática — mantido no
mapeamento por completude/paridade com `TierDot`, não por expectativa de uso.

---

## Component Contract — `SinalChip`

Um único componente, dois pesos fixos, ambos com call site real nesta fase
(D-14/CHIP-01).

- `peso="contexto"` substitui `chip()` interno do `AtivoCard`
  (`App.jsx:3370`), `FundamentoChip` (`:1373`), `RegimeChip` (`:1394`) e o
  pill "confiança X" (`:6896`).
- `peso="primario"` substitui o BLOCO DA MANCHETE do `AtivoCard` — o `<div>`
  com kicker ("DECISÃO DA MESA"/"PLANO EDUCACIONAL") + valor da decisão
  (`decM`), hoje em `App.jsx:3558-3562`. Como o `AtivoCard` é o MESMO
  componente em `contexto="watchlist"` (`:3955`) e `contexto="radar"`
  (`:6891`), este é automaticamente 1 componente com 2 usos reais (D-08:
  "Igual em Watchlist e Radar"). O bloco de ausência ("Sem leitura do motor
  para este ativo agora...", `App.jsx:3567-3570`) **continua um `<div>`
  comum, não um `SinalChip`** — não há decisão a expressar quando não há
  leitura do motor.

```ts
type SinalChipProps =
  | {
      peso: "contexto";
      label: string;                 // "REGIME", "FUNDAMENTO" — maiúsculas, convenção herdada
      value: string;                 // "ALTA", "A", "100%"
      ariaLabel: string;             // sentença completa, obrigatório (D-15/CHIP-02)
      estado?: "elegivel" | "inelegivel" | "insuficiente" | "nunca_medido" | "aposentado";
      alinhamento?: "a_favor" | "contra" | null; // só com decisão direcional (D-01)
    }
  | {
      peso: "primario";
      decision: string;              // decM já resolvido por decisaoDoModo/recDoModo — motor, não IA
      kicker: string;                // "DECISÃO DA MESA" | "PLANO EDUCACIONAL" — resolvido pelo chamador (operador flag), passado pronto
      suffix?: string;               // " · você está comprado" quando pos existe (D-13 continua fora do chip, mas o texto entra aqui)
      ring?: { conf: number; lado?: "alta" | "baixa" | "neutro"; setup?: string } | null; // D-08/D-09/D-10
    };
```

O componente resolve `REC_STYLE[decision]` INTERNAMENTE para `peso="primario"`
— o chamador nunca passa cor livre (D-14). Isso preserva o guardrail
"manchete só do motor": o `SinalChip` não decide a cor, só traduz a decisão
já calculada (`decM`) para o par `[cor, fundo]` que `REC_STYLE` já define
hoje.

### Visual por `peso` (fixo, sem exceção por chamada)

| Peso | Tamanho/peso de fonte | Padding | Radius | Borda vs. fundo | Cor |
|------|------------------------|---------|--------|-------------------|-----|
| `contexto` | 11px / 700 | `4px 8px` (xs vertical, sm horizontal) | 7px (herdado de `FundamentoChip`/`RegimeChip`) | borda 1px sólida, sem fundo (herda o padrão atual) | `T.textPrimary` (valor) / `T.textFaint` (label) — **exceção única**: `estado="inelegivel"` usa `T.warn` texto + fundo `T.warnTint10` (sem borda) |
| `primario` | kicker 10px/400 (`letterSpacing:0.04em`, exceção herdada — ver Typography) + valor 17px/800 (exceção herdada — ver Typography) | `9px 11px` (herdado, `App.jsx:3559` — developer-approved — matches existing pattern — 2026-09-26) | 9px (herdado, mesma citação) | fundo sólido tintado (`REC_STYLE[decision][1]`), sem borda | `REC_STYLE[decision][0]` (kicker e valor usam a MESMA cor, como hoje) |

Visual de `primario` é **pixel-equivalente** ao bloco atual — a mudança é
estrutural (vira componente reutilizável com `ring` embutido, D-08), não
visual.

### Estados de elegibilidade (variante do `contexto`, não cor livre)

| Estado | Cor texto | Fundo | Borda | Glifo prefixo |
|--------|-----------|-------|-------|-----------------|
| `elegivel` | `T.textPrimary` | transparente | 1px `T.borderSubtle` | `✓ ` (decorativo, `aria-hidden`; leitor de tela usa `ariaLabel` completo) |
| `inelegivel` | `T.warn` | `T.warnTint10` | nenhuma | nenhum |
| `insuficiente` | `T.textFaint` | `T.bgBase` | nenhuma | nenhum |
| `nunca_medido` | `T.textFaint` | `T.bgBase` | nenhuma | nenhum |
| `aposentado` | `T.textMuted` | `T.bgCard` | 1px tracejada `T.borderDashed` | nenhum |

D-16 preservado: regime `indefinido` não vira chip; fundamento sem `score`
não vira chip; base degradada do regime (`·SMA50`) continua como sufixo
textual dentro do `value`/`ariaLabel`; `null` nunca vira `0`/string vazia —
o chip inteiro não renderiza.

### Marca de alinhamento (não é um `SinalChip`, é anexo textual)

Renderizada ao lado do chip de regime, mesmo peso tipográfico da linha de
contexto (12px/400, `T.textSecondary`), nunca como chip com borda:

- `a_favor`: `"↗ a favor da tendência"`
- `contra`: `"↘ contra a tendência"`
- Sem decisão direcional (AGUARDAR/NÃO OPERAR/sem leitura): não renderiza
  (D-01).

---

## `ConfluenceRing` — layout no bloco da manchete (D-08/D-09/D-10)

Renderizado DENTRO de `SinalChip peso="primario"` via a prop `ring`.

- Tamanho: 36px de diâmetro (D-08, fixo — exceção à escala 4/8pt, justificada
  por ser elemento gráfico/SVG, não espaçamento).
- Posição: à direita do texto COMPRAR/VENDER/AGUARDAR/NÃO OPERAR, mesma
  linha, `display:flex`, `justify-content: space-between`,
  `align-items: center`, `gap: 8px`.
- Arco: ver "Color" acima (`TIER_FILL[tierOf(conf)[0]]`).
- Rótulo (sempre visível ao lado/abaixo do anel, nunca só em `aria-label`):
  formato fixo `"{pct}% · {TierLabel} — padrão de {ladoTxt}: {setup}"`, ex.
  `"100% · Forte — padrão de venda: Reversão de sobrecompra"`. Peso 700
  (ver Typography) — nenhum terceiro peso aqui.
  - `{pct}` = `sc.confluencia`/`r.confluencia` (motor, sem arredondamento
    além do já existente).
  - `{TierLabel}` = `tierOf(conf)[1]` (rótulo travado por teste, não mudar).
  - `{ladoTxt}` = `"compra"` se `lado === "alta"`, `"venda"` se
    `lado === "baixa"`; lado NUNCA inferido do texto/nome do setup — vem do
    campo `lado` do motor (`plano.lado` no Radar, hoje disponível;
    **dependência de dado**: a Watchlist só mostra o lado se o campo chegar
    em `sc` — mesma postura de `gatilhoAlinhado`/D-01: se `sc.lado` não
    vier no payload, o rótulo omite a cláusula "padrão de X:" e mostra só
    `"{pct}% · {TierLabel} — {setup}"`; nunca recalcula lado no front).
  - `{setup}` = `melhorSetup`/`setup.nome` (motor, texto já existente).
- Truncamento mobile (320–375px): o rótulo é o elemento que quebra primeiro.
  Regra: `label` em `<div>` com `white-space: normal`, `font-size: 12px`,
  até 2 linhas (`-webkit-line-clamp: 2` com `overflow: hidden`); nunca
  trunca o `%`/tier (primeiras palavras), só a cauda "— padrão de X:
  {setup}" pode quebrar linha ou, se `{setup}` for muito longo, o texto do
  setup pode ser cortado com reticências CSS (`text-overflow: ellipsis` num
  `<span>` interno dedicado só ao nome do setup) — `%`, tier e "padrão de
  X" nunca são cortados.
- Regra de ausência (D-10): sem `melhorSetup`/confluência 0/sem leitura do
  motor → nem o anel nem o rótulo renderizam (`ring` prop = `null`). A
  manchete e `motivo` já dizem a ausência (nenhum texto substituto no lugar
  do anel).
- Decisão × setup sem operar: quando há setup mas a decisão é NÃO OPERAR
  (esticado/R:R baixo), o anel RENDERIZA normalmente com o rótulo de lado
  (Claude's Discretion resolvida — D-10 só suprime na ausência de setup, não
  na ausência de operação).

---

## Ordem de leitura (HIER-02) — layout mobile-first

Vale para os dois contextos (`watchlist`, `radar`; "4 contextos" do
ROADMAP é imprecisão corrigida no CONTEXT — só existem esses 2 call sites).

```
0. identidade + preço + resumo da posição (D-13, inalterado, já no topo)
1. MANCHETE = SinalChip peso="primario" (com ring embutido, D-08)
2. TimingBadge (colado, sem gap extra além do já herdado)
3. Plano operacional por modo (D-12), quando existir:
   - Operador: caixa entrada/stop/alvo/R:R/sizing (a régua PlanRuler SAI daqui)
   - Estudo: `motivo` determinístico + PlanRuler didática
   - Watchlist: só se o dado de plano já estiver no `vm` (sem plumbing novo)
4. UMA linha de contexto (peso contexto): SinalChip regime + marca de
   alinhamento + SinalChip fundamento (nesta ordem, gap 8px, flex-wrap)
5. Elegibilidade estatística (HistoricoPill reestilizado) — linha PRÓPRIA,
   abaixo da linha de contexto, nunca misturada nela
6. Cauda do contexto (inalterada): Watchlist = posição no risco/histórico/
   CTAs; Radar = aprofundar/monitorar/critérios
```

Nota de implementação: a ordem acima é sequencial mesmo quando um bloco
está ausente (ex. sem plano no Estudo sem `motivo`) — nenhum bloco herda a
posição de outro; ausência é espaço vazio, não realocação.

---

## Copywriting Contract

| Elemento | Copy | Fonte |
|----------|------|-------|
| Rótulo do anel (lado compra) | `"padrão de compra"` | novo — `web/src/copy.js`, comum aos 2 modos (fato do motor, não interpretação) |
| Rótulo do anel (lado venda) | `"padrão de venda"` | idem |
| Marca "a favor" | `"↗ a favor da tendência"` | novo — `copy.js`, comum aos 2 modos |
| Marca "contra" | `"↘ contra a tendência"` | idem |
| Fundamento — disclaimer de não-direção | `"fundamento indica qualidade da empresa, não direção"` | novo — `copy.js`, uma vez por card, ao final da linha de contexto, só quando o chip de fundamento está presente (evita repetir "não indica direção" dentro do próprio chip de 11px, que não cabe) |
| Elegível — glifo | `"✓ "` prefixado ao rótulo `historicoRotulo.elegivel` existente ("VANTAGEM MEDIDA") | glifo decorativo no componente (`aria-hidden`), TEXTO de `historicoRotulo` não muda — preserva o par `copy.js`/aria já testado |
| aria-label de `SinalChip` (regime) | segue o padrão do `HistoricoPill`: sentença completa, ex. `"Regime: alta, a favor da tendência"` / `"Regime: baixa, contra a tendência"` / `"Regime: alta"` (sem decisão direcional) | novo — compõe `regime.label` + `alinhamento` |
| aria-label de `SinalChip` (fundamento) | `"Fundamento: qualidade {score} (não indica direção)"` | novo |
| Kicker do `SinalChip peso="primario"` | inalterado — `"DECISÃO DA MESA"` (Operador) / `"PLANO EDUCACIONAL"` (Estudo) | existente, `App.jsx:3560` |
| Ausência de leitura do motor (herdado, bloco não-chip) | inalterado — `"Sem leitura do motor para este ativo agora — toque em ↻ reordenar para varrer de novo."` | existente |

Todas as strings NOVAS vivem em `web/src/copy.js` (`COPY.estudo`/
`COPY.operador`) — nenhuma string solta em `SinalChip`/`ConfluenceRing`/
`AtivoCard`. Como nenhuma delas depende de vocabulário determinístico do
backend (`skill_ref.py`) e não têm variação de tom por modo (são fatos do
motor: lado, alinhamento, definição de fundamento), **entram idênticas em
`COPY.estudo` e `COPY.operador`** — não há microtexto por modo nesta fase
(isso é HIER-03, Fase 43). O planner deve confirmar se replica a string nos
dois objetos ou cria uma chave compartilhada fora do split
`estudo`/`operador` (ambas as formas preservam o testável "sem string
solta"; decisão de implementação, não de design).

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | nenhum — projeto não usa shadcn | not applicable |
| third-party | nenhum | not applicable |

---

## Acessibilidade

- Todo `SinalChip` expõe `aria-label` descritivo (CHIP-02) — texto visual
  (`label`+`value`) NUNCA é a única informação; a marca de alinhamento
  entra no texto acessível mesmo quando visualmente é um elemento separado
  (D-15). Para `peso="primario"`, o `aria-label` combina kicker + decisão +
  (quando houver ring) o mesmo texto do rótulo do anel — uma leitura só,
  sem duas fontes.
- Glifos decorativos (`✓`, `↗`, `↘`, `%` dentro do SVG do anel) recebem
  `aria-hidden="true"` — o significado completo mora no `aria-label`/texto
  irmão, nunca só no glifo (mesmo padrão já usado por `TierDot`).
- `ConfluenceRing` mantém `role="img"` + `aria-label` (`"Confluência {c}%"`)
  — ao adotar o rótulo textual completo ao lado (D-09), o `aria-label` do
  SVG deve ser estendido para incluir tier+lado+setup (mesma informação do
  texto visível, não uma segunda fonte): `"Confluência {pct}%, {TierLabel},
  padrão de {ladoTxt}: {setup}"`.
- `SetorAlvo` que envolve o anel de confluência (herdando a âncora didática
  hoje na linha de chips, Claude's Discretion resolvida: o setor `analise`
  passa a envolver o `ConfluenceRing`, agora dentro do `SinalChip
  peso="primario"`): o componente `SetorAlvo` (`entendimento.jsx:87`) hoje
  NÃO garante alvo de toque mínimo — a área clicável é o `bounding box` dos
  `children` via `style` do chamador. Como o anel visual é 36px (< 44px
  mínimo recomendado), o chamador DEVE passar `style={{ minWidth: 44,
  minHeight: 44, display: "flex", alignItems: "center", justifyContent:
  "center" }}` ao `SetorAlvo` que envolve o anel — o visual do anel continua
  36px, centralizado; só a área de toque cresce via padding invisível. O
  botão só-leitor (`"O que é a confluência?"`, já existente em `SetorAlvo`)
  não muda.
- Setor `fundamento` continua ancorado no chip do fundamento (`SinalChip`
  com `estado`/`value` de fundamento), sem mudança de contrato de toque —
  já é um chip com padding suficiente (`padding: 4px 8px` + altura de linha
  ~11px + padding ≈ ~19px de altura visual; **abaixo de 44px** também, mas
  este É o comportamento HERDADO de `FundamentoChip` hoje — fora do escopo
  desta fase alterar; registrar como achado, não bloquear COR-01/HIER/CHIP).
- Contraste AA: ver seção Color — `warnTint10` calculado e aprovado (com a
  tensão de meta documentada) nas 4 combinações; demais cores de `SinalChip`
  (`T.textPrimary`/`T.textFaint`/`T.textSecondary` sobre `T.bgCard`) já são
  tokens existentes com AA auditado em `test_brand_book_v2_tokens.mjs` (não
  recalculado aqui — sem mudança de valor, só de onde são consumidos).

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
