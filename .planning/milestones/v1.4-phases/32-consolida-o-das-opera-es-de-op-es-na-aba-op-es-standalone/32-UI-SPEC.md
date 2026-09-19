---
phase: 32
slug: consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone
status: draft
shadcn_initialized: false
preset: none
created: 2026-09-15
---

# Phase 32 — UI Design Contract

> Contrato visual e de interação para a consolidação das operações de opções
> na aba Opções. Esta fase **não cria** design system nem componentes visuais
> novos — move quatro blocos e um hook entre `web/src/App.jsx` e
> `web/src/opcoes/OpcoesScreen.jsx`. O contrato aqui é sobre **composição,
> hierarquia e copy**, não sobre tokens novos. Gerado por gsd-ui-researcher,
> verificado por gsd-ui-checker.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none — React 18 hand-rolled (sem shadcn, sem `components.json`, sem lib de componentes) |
| Preset | não aplicável |
| Component library | nenhuma — estilos inline (objeto JS → `style={{...}}`), tokens via CSS custom properties injetadas por `PALETTE`/`T` |
| Icon library | nenhuma — SVG inline (`<polyline>`, `<svg>`) e glifos de texto (`⚡`, `▾`/`▴`, `→`) |
| Font | herdada do sistema (nenhuma declaração de `font-family` custom vista nestes arquivos) |

Esta fase não introduz nenhum destes. Todo elemento novo (linha de chamada,
rótulos dos dois motores) usa os tokens `T.*` e os padrões visuais já
catalogados abaixo — nenhum valor novo de cor, espaçamento ou família
tipográfica.

---

## Spacing Scale

O projeto **não segue** uma escala estrita de múltiplos de 4/8 — usa valores
ad hoc mas internamente consistentes entre os componentes auditados nesta
fase (`OportunidadesOpcoes`, `CuradoriaEstruturas`, `PropostaDaPosicao`,
`CandidatoOpcao`, `SubAbaOperar`). Valores fora da grade de 4px, com
citação:

| Token observado | Valor | Citação | Uso |
|-------|-------|---------|-----|
| padding vertical mínimo | 5px | `App.jsx:4480` (`padding: "5px 0"`, toggle de `PropostaDaPosicao` — mesmo padrão reusado pela linha de chamada) | toggle/linha discreta |
| gap de ícone | 7px | `App.jsx:4481` (`gap: "7px"`) | espaço entre ícone e rótulo |
| padding/raio pequeno | 9px | `App.jsx:4479` (`paddingTop: "9px"`), `App.jsx:4168`/`4404` (`borderRadius: "9px"`) | topo de card, raio de caixa de estado vazio |
| padding composto | 10px–11px | `App.jsx:4146`/`4285`/`4541` (`padding: "11px 12px"`), `App.jsx:4168`/`4404` (`padding: "10px 11px"`), `App.jsx:4490` (`marginTop: "11px"`) | padding interno de item de carrossel |
| gap padrão | 8px–10px | `carouselTrackStyle({ gap: "10px" ... })` nos quatro blocos | espaço entre itens de carrossel |
| padding de painel expandido | 14px | `App.jsx:4310` (`padding: "14px"`) | painel de confirmação inline (Bloco B) |
| alvo de toque mínimo | 44px | `minHeight: "44px"` em todo elemento clicável (botão, item de carrossel, linha de toggle) — não-negociável, já testado | — |

**Exceção registrada:** `developer-approved — matches existing pattern —
2026-09-15`. O Alex aprovou explicitamente manter os valores ad hoc acima em
vez de normalizar para múltiplos de 4px nesta fase — normalizar a escala é
**débito nomeado para uma fase própria**, não escopo da Fase 32, que é uma
fase de mover/reusar componentes existentes, não de redesenhá-los.

Todo elemento NOVO desta fase (linha de chamada em Posições, frase-ponte,
rótulos dos dois blocos) reusa os valores já listados acima — a linha de
chamada usa `padding: "9px 2px"` e `minHeight: "44px"`, o mesmo padrão do
toggle de `PropostaDaPosicao` (`App.jsx:4480`) — nenhum valor novo fora
desta tabela.

---

## Typography

Valores literais medidos nos cinco componentes auditados:

| Role | Size | Weight | Uso |
|------|------|--------|-----|
| Eyebrow/label | 9px–10.5px | 800, `letterSpacing: 0.03em–0.04em`, uppercase | Título de seção fixo ("OPORTUNIDADES DE OPÇÕES", chip de tipo) |
| Body pequeno | 10.5px–12px | 400–700 | Texto secundário, rótulo de linha, motivo de estado vazio |
| Body padrão | 12.5px–13px | 400–800 | Manchete do motor, texto de proposta, botões |
| Heading de tela | 22px | 800 | `<h1>{cp.tituloOpcoes}</h1>` — não muda nesta fase |

**Exceção registrada:** `developer-approved — matches existing pattern —
2026-09-15`. A tabela declara três pesos (400/700/800), acima do teto padrão
de 2 pesos por fase — o Alex aprovou explicitamente manter os três,
confirmados por citação:

- **800** — `App.jsx:4127` (eyebrow `tiraOpcoesTitulo`), `App.jsx:4262`
  (eyebrow `curadoriaTitulo`), `App.jsx:4542` (eyebrow de `CandidatoOpcao`),
  `OpcoesScreen.jsx:688` (`<h1>` da aba).
- **700** — `App.jsx:4153` (manchete de `OportunidadesOpcoes`),
  `App.jsx:4480` (toggle de `PropostaDaPosicao`), `App.jsx:4551` (manchete
  de `CandidatoOpcao`).
- **400** (implícito, sem `fontWeight` declarado — peso padrão do
  navegador) — `App.jsx:4263` (`curadoriaSubtitulo`),
  `OpcoesScreen.jsx:689` (`subtituloOpcoes`).

Reduzir para 2 pesos exigiria reescrever o peso visual de eyebrow OU de
manchete em componentes que esta fase **move, não redesenha** — isso
contradiria a premissa da fase (consolidação de composição, não
redesign visual) e foi explicitamente rejeitado pelo Alex. Nenhum peso
quarto (ex.: 600, 900) é introduzido; os três already-in-use permanecem os
únicos em uso.

Line-height: `1.4`–`1.6` em texto corrido (subtítulo, disclaimer, motivo de
estado vazio); sem `line-height` declarado em labels curtos de uma linha.

**Esta fase não declara tamanho/peso novo além dos três já auditados.** A
linha de chamada em Posições usa o mesmo par (rótulo 13px/700 + ícone
`T.accent`) do toggle de `PropostaDaPosicao` que ela substitui em espírito.

---

## Color

Sistema de dois eixos independentes (tema × modo), já implementado — ver
`PALETTE` em `web/src/App.jsx`. Nenhum hex novo nesta fase.

| Role | Token | Valor (dark) | Uso |
|------|-------|---------------|-----|
| Dominante (60%) | `T.bgBase` | `#10121a` | Fundo da tela |
| Secundária (30%) | `T.bgPanel` / `T.bgCard` | `#161927` / `#1b1f2e` | Cards, painéis, itens de carrossel |
| Acento (10%) | `T.accent` | `#2fa8a0` (Estudo) / dourado `#d4af37` (Operador — `MODE_OPERADOR`) | Eyebrow de proposta, borda/realce de item selecionado, CTA primário, ícone da linha de chamada |
| Positivo/Negativo | `T.positive` / `T.negative` | `#34d399` / `#f26d6d` | Polaridade CALL/PUT na manchete — **nunca** `T.accent` na manchete (regra já travada em comentário de código) |
| Aviso/degradado | `T.warn` | `#fbbf24` | Falha técnica declarada (liquidez não confirmada, erro de execução, **erro de busca desta fase**) |

**Atenção de marca:** `BRAND.amber` (`#f2a93b`) é a cor da marca (splash,
ícone) e é **distinta** de `T.warn` (`#fbbf24`, token de estado já em
produção desde qa/34) — os dois só coincidem na família de matiz. Esta fase
não usa `BRAND.amber` em nenhum bloco de conteúdo; todo aviso de estado usa
`T.warn`, como já é o padrão.

Accent reservado para: eyebrow de tipo de proposta (`CALL COBERTA`/`PUT`/
`COLLAR`), borda e fundo de item selecionado no seletor de ticker e nas
sub-abas, CTA primário de execução, link secundário ("ver posição"), e o
ícone/seta da linha de chamada nova em Posições. **Nunca** na manchete do
motor (guardrail CVM) e nunca como cor de aviso/erro.

Destructive: `T.negative` (`#f26d6d`) — reservado a polaridade PUT/venda e
P&L negativo. Esta fase não introduz ação destrutiva nova (fechar posição de
opção usa o fluxo de confirmação já existente em `useAceiteLastreado`,
intocado).

---

## Contrato de composição — a aba Opções (o núcleo desta fase)

### Ordem vertical decidida (sub-aba "Setups", que é a que abre por padrão)

```
1. <h1>Opções</h1> + subtítulo                         [existente, intocado]
2. Alternador de sub-abas "Setups" / "Operar"           [existente, intocado]
   ── dentro da sub-aba "Setups" ──
3. Frase-ponte neutra (NOVA, obrigatória, SEMPRE visível — ver abaixo)
4. Bloco A — OportunidadesOpcoes (motor COM gate)       [movido, D-07]
5. Bloco B — CuradoriaEstruturas (motor SEM gate)       [movido, D-04]
6. "Seus vigias" (cabeçalho + lista)                    [existente, intocado]
7. Seletor de ticker                                    [existente, intocado]
8. Leitura técnica interna + convite de leitura do serviço (cascata)  [existente, intocado]
   ── dentro da sub-aba "Operar" ──
9. Seletor de ticker (reusado)                          [existente, intocado]
10. Proposta lastreada da posição selecionada — com suporte a N candidatos [PropostaDaPosicao migrado, ver seção própria]
```

**Justificativa da posição 3–5 (acima de "Seus vigias"):** D-02 fixa que
clicar na linha de chamada de Posições leva "à aba Opções, na lista de
oportunidades" — não a qualquer outro conteúdo da aba. Como `OpcoesScreen`
desmonta e remonta a cada troca de aba (`{tab === "opcoes" && <OpcoesScreen/>}`,
`App.jsx:9775`), ela sempre abre com `subaba="setups"` e `ticker=""` — ou
seja, o que estiver **no topo do conteúdo da sub-aba Setups** é literalmente
o que a pessoa vê ao navegar pela linha de chamada. Colocar os dois blocos
cross-carteira ANTES de "Seus vigias" é o que cumpre D-02 ao pé da letra:
"a lista de oportunidades" é a primeira coisa na tela, não a segunda.

**Ordem entre Bloco A e Bloco B:** Bloco A (`OportunidadesOpcoes`, motor COM
gate) primeiro, Bloco B (`CuradoriaEstruturas`, motor SEM gate) em seguida —
mantém a continuidade de nome/posição que a Fase 18 já estabeleceu
("Oportunidades de opções" era o título original desse bloco) e evita que a
lista de 4 sem gate pareça "a lista principal, com a outra como rodapé".

### Contrato mensurável de densidade (Blocos A e B, viewport de referência 375×667px)

Números verificáveis, derivados de constantes já no código — não
julgamento subjetivo. Constantes-fonte:

- Largura útil de conteúdo: `375px − (18px × 2)` de padding horizontal do
  wrapper de tela (`App.jsx:9768`, `padding: "24px 18px 34px"`) = **339px**.
- Gap entre itens de carrossel: `10px` (`carouselTrackStyle({ gap: "10px" })`
  nos quatro blocos).
- Largura de cartão: `210px` fixo em Bloco A (`App.jsx:4146`,
  `flex: "0 0 210px"`) e em `CandidatoOpcao`/Operar (`App.jsx:4541`);
  `220px` fixo em Bloco B (`App.jsx:4285`, `flex: "0 0 220px"`).

| Bloco | Cartões visíveis em 339px antes do 1º scroll horizontal | Altura de referência do cartão | Altura do bloco completo (cabeçalho + 1 linha de carrossel) |
|---|---|---|---|
| **Bloco A** — `OportunidadesOpcoes`, cartão 210px | 1 cartão inteiro + ≈61% do segundo (`339 − 210 = 129px` de sobra; `129/210 ≈ 0,61`) → **≈1,6 cartão visível** | **≈96px** com manchete de 1 linha, até **≈112px** com manchete de 2 linhas — variável por desenho (padding 11px×2 + eyebrow 10px + ticker 13px + manchete 12.5px×1–2 linhas + rodapé 10.5px, cada linha com seu `marginTop`; não fixar `max-height`/`overflow:hidden` aqui — cortaria a manchete, que é protegida pelo guardrail CVM) | eyebrow de seção (10px+8px margem) + subtítulo novo (11.5px+8px margem) + 1 linha de carrossel (96–112px) ≈ **≈140px–156px** |
| **Bloco B** — `CuradoriaEstruturas`, cartão 220px | 1 cartão inteiro + ≈54% do segundo (`339 − 220 = 119px`; `119/220 ≈ 0,54`) → **≈1,5 cartão visível** | **≈104px** com manchete de 1 linha, até **≈120px** com manchete de 2 linhas (mesma ressalva de não fixar altura rígida) | eyebrow (10px+4px) + subtítulo (11.5px+8px) + linha de resumo de varredura (10.5px+8px, quando presente) + 1 linha de carrossel (104–120px) ≈ **≈150px–175px** |
| **Sub-aba Operar** — `CandidatoOpcao`, cartão 210px (quando `multi`) | mesma métrica do Bloco A: **≈1,6 cartão visível** | mesma faixa do Bloco A (**≈96px–112px**) — componente reusado verbatim | não se aplica (não é bloco fixo de topo; renderiza sob demanda por posição selecionada) |

**Primeira dobra em 375×667px, em ordem** (chrome fixo do app medido a
partir dos componentes citados: friso `3px` (`App.jsx:9760`) + `Ticker`
`38px` fixo (`App.jsx:879`) + `Topbar` **≈76px estimado** por soma de
padding `10px×2` + wordmark `27px` + linha de modo `≈14px` (`App.jsx:931`
em diante — altura não fixada em CSS, valor é estimativa por composição de
conteúdo, não medição em dispositivo) + `BottomNav` **≈64px estimado**
(`minHeight: "54px"` + padding `5px×2`, `App.jsx:1025-1031`, sem contar
`safe-area-inset-bottom` variável por aparelho) → chrome fixo total
**≈181px**; altura de conteúdo rolável disponível ≈ `667 − 181 = 486px`,
menos `24px` de padding-top do wrapper de conteúdo ≈ **≈462px antes do
primeiro scroll vertical**):

1. `<h1>Opções</h1>` + subtítulo ≈ 63px
2. Alternador de sub-abas ≈ 58px
3. Frase-ponte (D-05, 2–3 linhas em 339px) ≈ 72px
4. Bloco A completo ≈ 140–156px
5. Bloco B — cabeçalho sempre visível; o carrossel de cartões do Bloco B
   tende a ficar **na borda ou logo abaixo da dobra** na soma acumulada
   (`63+58+72+148+~160 ≈ 501px`, acima dos ≈462px disponíveis)

**Conclusão verificável:** em iPhone SE/8 (375×667, o viewport mais
restritivo de uso comum), a frase-ponte e o Bloco A completo cabem antes do
primeiro scroll; o cabeçalho do Bloco B é tipicamente a última coisa visível
na dobra, com seu carrossel de cartões e "Seus vigias" abaixo dela — sem
violar D-06 (rolagem aceita) e sem exigir sticky/fixed em nenhum destes
blocos. Números de chrome (Topbar/BottomNav) são estimativa por composição
de código, não medição em dispositivo físico — o executor deve confirmar a
ordem qualitativa (Bloco A na dobra, Bloco B na borda) no checkpoint ao vivo,
não recalcular os pixels.

### Fork não resolvido, registrado explicitamente (não decidido em silêncio)

O CONTEXT.md diz literalmente **"topo da aba Opções"** (D-04) e **"topo da
aba, ao lado da lista curada"** (D-07) — não "topo da sub-aba Setups". Há
duas leituras válidas:

- **Leitura A (recomendada acima, adotada neste contrato):** os blocos ficam
  DENTRO da sub-aba "Setups", acima de "Seus vigias" — seguindo o padrão de
  código já existente, em que TODO conteúdo cross-carteira de hoje (vigias)
  já vive dentro dessa sub-aba, não acima do alternador. Vantagem: zero
  mudança estrutural no componente de sub-abas; D-02 continua satisfeito
  porque a aba sempre abre em "Setups". Desvantagem: os blocos ficam
  invisíveis para quem está na sub-aba "Operar".
- **Leitura B (alternativa, não adotada, registrada para decisão do Alex):**
  os blocos ficam ACIMA do alternador de sub-abas, visíveis nas duas
  sub-abas. Vantagem: literal ao "topo da aba" (não da sub-aba); descoberta
  nunca desaparece ao trocar de sub-aba. Desvantagem: exige mexer na
  estrutura de render hoje condicionada a `subaba !== "setups"` (ver
  `OpcoesScreen.jsx:686-710`), e duplica a pergunta "o que abre primeiro" —
  hoje a aba abre em "Setups", então a diferença prática entre A e B só
  aparece se o usuário trocar manualmente para "Operar" e quiser ver os
  blocos cross-carteira sem voltar.

Este contrato assume a Leitura A. **Se o Alex revisar o CONTEXT.md e preferir
B, a mudança é de escopo pequeno** (mover o bloco de dentro do `return` da
sub-aba Setups para antes de `{subabas}`) — não invalida nenhuma outra
decisão deste documento, incluindo os números de densidade acima (a única
mudança seria os blocos aparecerem também quando `subaba === "operar"`).
Ver também `## Open Questions`.

---

## Os dois rótulos (D-05) — a entrega de copy mais importante desta fase

**Frase-ponte obrigatória, SEMPRE visível, NUNCA colapsável** — renderizada
acima dos dois blocos, nos dois modos (mesmo texto — é constatação de fato,
não voz de personagem). Não é um disclaimer opcional nem um texto que
esconde atrás de "saiba mais": ela é a mitigação do risco regulatório
central do D-05, então precisa estar sempre no DOM e sempre visível junto
dos dois blocos, sem toggle, sem acordeão, sem `aria-expanded` que permita
recolhê-la:

> `duasLeiturasIntro`: "Duas leituras diferentes da sua carteira — nenhuma é
> mais certa que a outra: uma parte do que a leitura técnica confirma agora,
> a outra varre a cadeia inteira sem exigir essa confirmação."

Esta frase é **obrigatória, não estilística** — é o que impede a leitura
"um bloco é o correto, o outro é o alternativo/inferior" só pela ordem de
leitura (o Bloco A vem primeiro na tela) e, especificamente, impede que
alguém que pule direto para "AS 4 MELHORES OPORTUNIDADES DE OPÇÕES" (Bloco
B, sem gate) leia esse título como veredito geral do app em vez de
"melhores dentro dos 4 candidatos do próprio bloco" — sem a frase-ponte
sempre visível, essa leitura errada é o comportamento padrão de quem
escaneia a tela.

### Bloco A — motor COM gate (`opcoes_lastreadas.propor()`, hoje `OportunidadesOpcoes`)

| Chave | Estudo | Operador |
|---|---|---|
| `tiraOpcoesTitulo` (renomear conteúdo, manter chave) | "OPORTUNIDADES CONFIRMADAS PELA LEITURA TÉCNICA" | "CONFIRMADAS PELA LEITURA TÉCNICA" |
| `tiraOpcoesSubtitulo` (chave NOVA) | "Só aparecem aqui as posições em que a leitura técnica do próprio ativo confirma a estrutura agora — o mesmo motor que decide o gatilho do Radar." | "Só entram aqui posições cuja leitura técnica confirma a estrutura agora — mesmo motor do gatilho do Radar." |

### Bloco B — motor SEM gate (`opcoes_curadoria`, hoje `CuradoriaEstruturas`)

| Chave | Estudo | Operador |
|---|---|---|
| `curadoriaTitulo` (existente, manter) | "AS 4 MELHORES OPORTUNIDADES DE OPÇÕES" | "AS 4 MELHORES OPORTUNIDADES DE OPÇÕES" |
| `curadoriaSubtitulo` (reescrever conteúdo, manter chave) | "As 4 melhores por prêmio ÷ perda máxima, entre todas as posições e vencimentos varridos — inclusive as que a leitura técnica ainda não confirma. A ordem é do motor; não muda com a explicação da IA." | "As 4 melhores por prêmio ÷ perda máxima, entre todas as posições e vencimentos varridos — inclusive as que a leitura técnica ainda não confirma. Ordem do motor; a IA não reordena." |

**Checklist regulatório aplicado às quatro strings acima e à frase-ponte**
(mesma lista `PROIBIDAS` de `test_curadoria_ui.mjs`): sem "garantido", "sem
risco", "certeza", "lucro garantido"; nenhuma das duas frases usa verbo de
recomendação ("compre", "prefira"); nenhuma diz "melhor" sobre a outra —
"melhores" em `curadoriaTitulo` qualifica os 4 candidatos ENTRE SI dentro do
próprio bloco B (prêmio ÷ perda máxima), não uma comparação com o bloco A.

---

## Linha de chamada em Posições (D-01/D-02/D-03)

### Onde fica

No topo do conteúdo de `CarteiraScreen`, exatamente onde os quatro blocos
hoje começam (`App.jsx:4852`) — antes da lista de posições. Substitui os
quatro blocos inteiros; nenhum outro conteúdo de opções permanece em
Posições.

### Estilo visual

Reusa o padrão de linha-toggle já em produção em `PropostaDaPosicao`
(`App.jsx:4480`) — não o padrão de card (`ProfileTile`/tira de carrossel),
que tem borda, sombra e fundo `bgCard`. É deliberadamente **mais discreto**
que qualquer bloco que ela substitui:

```
<button style={{
  display: "flex", width: "100%", alignItems: "center",
  justifyContent: "space-between", minHeight: "44px",
  padding: "9px 2px", background: "transparent", border: "none",
  borderBottom: `1px solid ${T.borderFaint}`, cursor: "pointer",
}}>
  <span style={{ display: "flex", alignItems: "center", gap: "8px",
                 fontSize: "13px", fontWeight: 700, color: T.textPrimary }}>
    <span style={{ color: T.accent }}>⚡</span> {texto}
  </span>
  <span style={{ color: T.textFaint }}>→</span>
</button>
```

Sem background de destaque, sem borda ao redor — só a linha divisória
inferior (`borderFaint`), igual às demais linhas de lista da tela.

### Copy e estados (chave nova: `linhaChamadaOpcoes*`)

| Estado | Estudo | Operador | Comportamento |
|---|---|---|---|
| `n >= 1` (função `linhaChamadaOpcoesTexto(n)`) | `n===1 ? "1 oportunidade de opções nas suas posições" : n + " oportunidades de opções nas suas posições"` | idêntico ao Estudo (é constatação de fato, não voz de personagem) | Linha ativa, ícone `⚡` em `T.accent`, cor de texto `T.textPrimary`, clicável, `onClick` → `navigate("opcoes")` |
| `n === 0` (`linhaChamadaOpcoesVazia`) | "Nenhuma oportunidade de opções agora" | idêntico | Linha **continua visível e clicável** (nunca desaparece — princípio 9 CLAUDE.md) mas com peso visual reduzido: `color: T.textFaint`, sem `fontWeight: 700` (usar 500/normal), ícone em `T.textFaint` em vez de `T.accent`. Clicar ainda leva à aba Opções, que explica o motivo (bloco B mostra `curadoriaVazio`) |
| `carregando` (`linhaChamadaOpcoesCarregando`) | "Verificando oportunidades de opções…" | idêntico | Cor `T.textFaint`, sem número, **sem ícone `⚡`** (evita prometer resultado antes de saber) — mas a linha continua clicável (navegar não depende do resultado) |
| `erro` (`linhaChamadaOpcoesErro`) — busca falhou, não é "zero" | "Não foi possível verificar agora — toque para ver na aba Opções" | idêntico | Cor `T.warn` (nunca `T.negative`, que é P&L; nunca a mesma cor do estado "zero", que é um resultado real e este não é), ícone em `T.warn`. **Nunca mostrar "0" nem qualquer contagem quando o estado é erro** — mostrar "0" aqui seria inventar valor (princípio 4 do CLAUDE.md) |

**Fonte da contagem (D-03, não-negociável):** `n` vem exatamente de
`useCuradoria().top.length` — o MESMO estado que alimenta o Bloco B em
Opções, nunca uma segunda chamada. Consequência aceita e documentada: como
`opcoes_curadoria` sempre devolve no máximo 4 candidatos (é literalmente "as
4 melhores"), `n` está sempre entre 0 e 4, mesmo que exista uma quinta
oportunidade elegível não mostrada. Isto é herdado da Fase 30/31, não um
efeito colateral desta fase — mas a fase 32 é o primeiro lugar em que esse
teto vira um NÚMERO visível fora da aba Opções, então registra-se aqui: a
linha nunca deve ser lida como "o total de oportunidades da carteira", só
como "quantas aparecem na lista".

### Requisito de arquitetura de dado (consequência do contrato acima, não opcional)

Para que Posições e Opções mostrem sempre o MESMO número sem duas buscas
independentes (a divergência por race condition que D-03 proíbe), o estado
de `useCuradoria()` — `top`, `meta`, `carregando`, `erro` — precisa ser
**uma única fonte compartilhada** entre as duas telas, não duas instâncias
do hook. Isto é decisão de arquitetura (Open Question #2 do
`32-RESEARCH.md`), não puramente visual, mas o contrato de UI exige o
resultado: **um resultado, duas leituras**. A forma recomendada pela
pesquisa (subir o hook a `App()` com gatilho condicional por "visitou
Posições ou Opções", não por boot do app) preserva tanto D-03 quanto o
comportamento de custo de hoje (zero chamada para quem nunca visita nenhuma
das duas telas) — mas a escolha do mecanismo exato cabe ao plano.

---

## Correção de estado obrigatória: `erro` do Bloco B (achado desta pesquisa)

`useCuradoria()` (`App.jsx:4687-4736`) já rastreia `erro` (setado quando
`store.opcoesCuradoria()` rejeita — falha de rede, backend fora, etc.), mas
`CuradoriaEstruturas` **nunca lê essa prop hoje** — quando `erro === true`,
o componente cai no ramo `top.length === 0 && !carregando`, que mostra
`cp.curadoriaVazio` ("Nenhuma estrutura elegível... por isso não há nada
para ranquear agora"). Isso é uma violação ativa do princípio 4 do
CLAUDE.md: a tela afirma "nada é elegível" quando a causa real é "não
consultei com sucesso". Como esta fase já mexe neste componente e neste
hook (movendo os dois de arquivo), **a correção entra no escopo**, não é
opcional:

| Estado | Copy nova (`curadoriaErroBusca`) | Comportamento |
|---|---|---|
| `erro === true` (precedência sobre `top.length === 0`) | Estudo: "Não foi possível varrer sua carteira agora. Isto não significa que não há oportunidade — significa que a busca falhou. Toque para tentar de novo." / Operador: mesmo texto | Cor `T.warn`, com botão "Tentar de novo" que rechama o fetch (reusa o mesmo `useEffect`, sem UI nova de retry — um botão simples que reexecuta a busca) |

Mesma correção se propaga à linha de chamada em Posições (estado `erro`
acima) — as duas leem a mesma fonte, então devem ficar consistentes por
construção, não por coincidência de copy.

---

## Sub-aba "Operar" — suporte a multi-candidato (D-04, Open Question #3)

**Decisão registrada (recomendação adotada por este contrato):** portar o
suporte a N candidatos para dentro de `SubAbaOperar`, não aceitar como
débito técnico. Justificativa: aceitar a lacuna regride MULTI-02 em
silêncio — carteira com 2+ candidatos elegíveis (ex.: venda coberta E put de
proteção na mesma posição) perde a visão lado a lado que tem HOJE em
Posições, sem nenhum teste acusando (o guardião atual valida o comportamento
single-candidate como correto). Não portar é uma regressão visível na
primeira posição real com 2 candidatos.

### Contrato de layout

Reusar **verbatim** `CandidatoOpcao` (`App.jsx:4513-4600`) — já é puro por
prop, já tem o contrato visual completo (eyebrow por tipo, manchete
colorida por polaridade, chips, caixa de payoff com ganho/perda/breakeven/
caixa). Não recriar em `OpcoesScreen.jsx`; mover o componente. Métricas de
densidade: ver tabela "Contrato mensurável de densidade" acima (linha
"Sub-aba Operar").

- `SubAbaOperar` decide `multi = candidatos.length > 1` com a MESMA regra de
  `PropostaDaPosicao` hoje (`App.jsx:4469`).
- Quando `multi`: renderizar os N `CandidatoOpcao` em linha horizontal
  (`carouselTrackStyle`), largura fixa `flex: "0 0 210px"` cada — o mesmo
  padrão de largura comparável já documentado no comentário de
  `CandidatoOpcao` (dois candidatos disputam a MESMA decisão; largura
  diferente daria peso visual diferente, violação do princípio 9).
- Quando não `multi`: continua renderizando `<PropostaLastreada>` sozinha —
  comportamento de hoje, sem regressão para posições de candidato único.
- **Aceite continua exclusivo por rodada** (MULTI-02, critério 3): aceitar
  um candidato não deixa outro executável na mesma posição — reusa
  `useAceiteLastreado`/`aceitarCandidato`, sem novo mecanismo de trava (já
  garantido pelo motor, não pela UI).

### Duplicações a resolver na mudança (não introduzidas por ela, mas expostas por ela)

- **`posAberta`/`myOptionPositions`:** duas implementações hoje (uma em
  `PropostaDaPosicao`, outra já em `SubAbaOperar`). Ao mover
  `PropostaDaPosicao` para dentro de `SubAbaOperar`, manter a implementação
  **de `SubAbaOperar`** (já adaptada ao formato "uma posição selecionada
  por vez") e apagar a outra com nota — não deixar as duas competindo no
  mesmo componente.
- **Fetch de gate/proposta redundante:** `SubAbaOperar` já busca
  `store.optionsGate`/`store.optionsProposta` sozinha; se o ticker acabou
  de ser consultado em Posições/no topo da aba (`useOpcoesPropostas`), isso
  é uma segunda ida à rede pelo mesmo dado. **Não é exigido por este
  contrato de UI corrigir isso nesta fase** (é otimização, não regra
  visual) — mas se o plano decidir subir `useOpcoesPropostas` junto com
  `useCuradoria` para resolver a fonte de dado compartilhada acima, reusar
  `opcoesPorTicker[ticker]` em vez do fetch local é a consequência natural,
  e deve vir acompanhada da atualização do guardião
  `test_opcoes_subabas_ui.mjs` regra 3 (contagem de `store.optionsGate(`/
  `optionsProposta(` em `OpcoesScreen.jsx`).

### Navegação de dentro do painel curado até a posição (Pitfall 4 da pesquisa)

O botão "ver posição" dentro do painel inline do Bloco B
(`cp.curadoriaVerPosicao`, hoje ligado a `onAbrir(item.ticker)` →
`abrirOpcoesDe`, que faz `scrollIntoView` num elemento que só existe em
`CarteiraScreen`) precisa de destino novo dentro da própria aba Opções:

```
onAbrir={(t) => { escolherTicker(t); setSubaba("operar"); }}
```

Isto substitui o scroll por navegação real dentro da aba — sem essa troca,
o clique não faz nada (elemento inexistente) na nova localização.

---

## Estados completos por bloco (princípio 9 do CLAUDE.md)

| Bloco | Carregando | Vazio | Erro de busca | Mercado fechado | Dado atrasado | Sem orçamento (mydata_budget) |
|---|---|---|---|---|---|---|
| Bloco A (`OportunidadesOpcoes`) | `cp.tiraOpcoesCarregando` (existente) | Três variantes já existentes por motivo (`tiraOpcoesSemSetup`/`tiraOpcoesSemMercado`/`tiraOpcoesSemCobertura`) — **preservar as três**, não substituir por uma genérica | Não rastreado hoje no hook `useOpcoesPropostas` (best-effort, silencioso) — **fora de escopo desta fase corrigir** (não é um dos 4 blocos com hook próprio rastreando `erro`; ver Open Questions) | Não se aplica — dado é o mesmo já exibido em Posições/Watchlist, sem gate de pregão aberto | Não exibido neste bloco hoje (nenhum carimbo de frescor na tira) — gap pré-existente, não introduzido aqui, registrado em Open Questions | `_curadoria_scan_posicao`/gate são best-effort por posição — posição sem orçamento simplesmente não aparece na lista, sem aviso dedicado (mesmo padrão de "vazio" que já existe) |
| Bloco B (`CuradoriaEstruturas`) | `cp.curadoriaCarregando` (existente) | `cp.curadoriaVazio` (existente) | **NOVO, obrigatório**: `curadoriaErroBusca` — ver seção "Correção de estado obrigatória" acima | Idem Bloco A | Idem Bloco A (gap pré-existente) | Idem Bloco A — best-effort por posição, sem aviso dedicado a "esta posição foi pulada por orçamento" |
| Linha de chamada (Posições) | `linhaChamadaOpcoesCarregando` (novo) | `linhaChamadaOpcoesVazia` (novo) | `linhaChamadaOpcoesErro` (novo) | Não se aplica | Não se aplica | Herdado do Bloco B (mesma fonte, D-03) |
| Sub-aba Operar (proposta por posição) | Estados já existentes de `PropostaLastreada`/`useAceiteLastreado` — intocados | `PropostaDaPosicao` já retorna `null` se `!r.proposta` (guarda de silêncio documentada — um aviso por posição repetido vira ruído, decisão já registrada em `App.jsx:4457-4461`) — **preservar**, não converter em bloco vazio visível | `PropostaLastreada`/`ChipDaProposta` já tratam degradação (`r.providerStatus !== "ok"`) — intocado | `propostaIndisponivelDegradada` já cobre proposta indisponível por cotação degradada — intocado | Frescor já exibido dentro de `FonteDoDadoProposta`/chips — intocado (FLOW-04, Fase 17) | Não se aplica no nível da proposta única (orçamento é consumido na varredura cross-posição, não na proposta de uma posição já selecionada) |

**Nota sobre "mercado fechado" e "dado atrasado" nos dois blocos
cross-carteira:** nenhum dos dois hoje carimba frescor/pregão na tira (só a
manchete do motor e o payoff). Isto é uma lacuna pré-existente (não
introduzida por esta fase) que a pesquisa não encontrou nenhum requirement
pedindo — registrada como Open Question, não inventada como requisito novo
desta fase.

---

## Navegação e acessibilidade

- **Linha de chamada → aba Opções:** `onClick={() => navigate("opcoes")}` —
  mecanismo já existente (`App.jsx:8231`), zero código de roteamento novo.
  `aria-label` explícito: `linhaChamadaOpcoesTexto(n) + " — abrir aba Opções"`
  (não deixar o leitor de tela anunciar só "→").
- **Alvo de toque:** 44px mínimo na linha inteira (não só no ícone/seta) —
  já é o padrão do projeto, reforçado aqui.
- **Ordem de foco na aba cheia:** título → sub-abas → frase-ponte (D-05,
  sempre presente no DOM, nunca colapsada) → Bloco A → Bloco B → "Seus
  vigias" → seletor de ticker → cascata técnica. Segue a ordem visual (DOM
  order = tab order), sem `tabIndex` manual — é o padrão já usado em toda a
  tela (nenhum `tabIndex` customizado encontrado em `OpcoesScreen.jsx`/
  `App.jsx` nestes componentes).
- **D-06 (rolagem aceita, sem busca):** nenhum elemento desta fase usa
  posicionamento `sticky`/`fixed` que impeça inserir uma barra de busca no
  topo depois — os blocos são `<div>` em fluxo normal. Confirmado pelo
  contrato de densidade acima: mesmo com Bloco A completo + início do Bloco
  B na primeira dobra, nada exige `sticky` para isso funcionar.
- **Item de carrossel horizontal (Blocos A/B):** já usa `carouselTrackStyle`
  (scroll horizontal, `scrollbarWidth: none`) — mantém acessibilidade por
  teclado/swipe já testada em produção; nenhuma mudança de padrão de
  interação aqui.

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA (execução de candidato) | Já existente: `curadoriaExecutarCta` / CTA de `PropostaLastreada` — intocados |
| Linha de chamada (n≥1) | "N oportunidade(s) de opções nas suas posições" + seta `→`, ícone `⚡` em `T.accent` |
| Linha de chamada (vazio) | "Nenhuma oportunidade de opções agora" — visível, clicável, peso reduzido |
| Linha de chamada (erro) | "Não foi possível verificar agora — toque para ver na aba Opções" — `T.warn` |
| Frase-ponte dos dois motores (D-05) | "Duas leituras diferentes da sua carteira — nenhuma é mais certa que a outra: uma parte do que a leitura técnica confirma agora, a outra varre a cadeia inteira sem exigir essa confirmação." — sempre visível, nunca colapsável |
| Bloco A — título | "OPORTUNIDADES CONFIRMADAS PELA LEITURA TÉCNICA" |
| Bloco B — título | "AS 4 MELHORES OPORTUNIDADES DE OPÇÕES" (mantido) |
| Erro de busca do Bloco B | "Não foi possível varrer sua carteira agora. Isto não significa que não há oportunidade — significa que a busca falhou. Toque para tentar de novo." |
| Destructive confirmation | Nenhuma ação destrutiva nova — fechar posição de opção usa `window.confirm` já existente em `useAceiteLastreado`, intocado |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|--------------|
| shadcn official | não aplicável — projeto não usa shadcn | não aplicável |
| terceiros | nenhum | não aplicável |

---

## Guardrails de não-regressão (referência à pesquisa, não repetida aqui)

Os seis arquivos de guardião listados em `32-RESEARCH.md` §"Guardiões de
teste em risco" (`test_curadoria_ui.mjs`, `test_carteira_opcoes_tira.mjs`,
`test_opcoes_multi_candidato_ui.mjs`, `test_opcoes_collar_ui.mjs`,
`test_opcoes_proposta_ui.mjs`, `test_opcoes_subabas_ui.mjs`) precisam de
reescrita com nota datada — **não exclusão** — quando os blocos mudarem de
arquivo. O checklist `PROIBIDAS` de palavras de promessa/garantia já usado
em `test_curadoria_ui.mjs` deve ser estendido às strings novas desta fase
(frase-ponte, títulos do Bloco A, linha de chamada).

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS — exceção `developer-approved — matches existing pattern — 2026-09-15` registrada
- [ ] Dimension 5 Spacing: PASS — exceção `developer-approved — matches existing pattern — 2026-09-15` registrada
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending

---

## Open Questions

1. ~~**Fork de hierarquia (Leitura A × B, ver seção "Contrato de composição").**~~
   **RESOLVIDA (2026-09-15, Alex): Leitura A.** "Topo da aba Opções" em
   D-04/D-07 significa **topo da sub-aba Setups** — onde os vigias já vivem.
   Os dois blocos cross-carteira NÃO aparecem em Operar. Razão dada na
   escolha: segue o precedente de código, e quem está em Operar está focado
   numa posição — não precisa do cross-carteira empurrando o conteúdo
   per-posição para baixo (o que agravaria a rolagem que o D-06 já aceitou).
   A estrutura de render de `OpcoesScreen.jsx` não muda.

2. **Arquitetura do fetch compartilhado de `useCuradoria()`** (Open Question
   #2 do `32-RESEARCH.md`) — este UI-SPEC exige o RESULTADO (uma fonte, duas
   leituras, D-03), não prescreve o mecanismo. Cabe ao `PLAN.md` declarar
   por escrito, como o CONTEXT.md já exige.

3. **`erro` de `useOpcoesPropostas` (Bloco A) não é rastreado hoje** — ao
   contrário de `useCuradoria()` (Bloco B), o hook do Bloco A não guarda
   estado de erro de busca (é best-effort silencioso desde a Fase 18). Esta
   fase corrige o `erro` do Bloco B (já rastreado, só não exibido) porque é
   uma correção de exibição, não de captura de dado nova. Adicionar rastreio
   de erro ao Bloco A seria mudança de hook mais profunda — registrado aqui
   como candidato a fase/quick task futura, não incluído no escopo desta.

4. ~~**Frescor/carimbo de dado ausente nos dois blocos cross-carteira**~~ —
   **RESOLVIDA (2026-09-15, Alex): fora de escopo, vira quick task.** Nem
   `OportunidadesOpcoes` nem `CuradoriaEstruturas` mostram "pregão"/"em
   dia"/"atrasado" hoje, ao contrário do bloco de leitura técnica por
   ticker — o que é lacuna de princípio 3 do `CLAUDE.md`. A Fase 32 não
   criou o problema, mas promove os dois blocos ao topo da aba e o torna
   mais visível. Decisão: manter a fase no que ela é (mover e unificar) e
   registrar a lacuna como TODO nomeado
   (`.planning/todos/pending/carimbo-frescor-blocos-cross-carteira.md`).
   A fase já carrega uma correção de princípio — o `erro` da curadoria que
   hoje se disfarça de estado vazio.

---

*Phase: 32-Consolidação das operações de opções na aba Opções*
*UI-SPEC gerado: 2026-09-15*
