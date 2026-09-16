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
ad hoc mas internamente consistentes entre componentes irmãos (`9px`, `10px`,
`11px`, `14px`, `18px`...). Confirmado por leitura de `OportunidadesOpcoes`,
`CuradoriaEstruturas`, `PropostaDaPosicao`, `CandidatoOpcao`, `SubAbaOperar`.

| Token observado | Valor | Uso |
|-------|-------|-----|
| gap compacto | 4px–7px | espaço entre eyebrow e valor, entre chips |
| gap padrão | 8px–10px | espaço entre itens de carrossel, entre blocos internos |
| padding de card | 11px–14px | padding interno de card/tira |
| separação de seção | 14px | `marginBottom` entre blocos de nível de tela (`OportunidadesOpcoes`, `CuradoriaEstruturas`) |
| alvo de toque mínimo | 44px | `minHeight` de todo elemento clicável (botão, item de carrossel, linha de toggle) — não-negociável, já testado |

**Exceções desta fase:** nenhuma. Todo elemento novo reusa os valores já
listados acima — a linha de chamada em Posições usa `padding: "5px 0"` e
`minHeight: "44px"`, o mesmo padrão do toggle de `PropostaDaPosicao`
(`App.jsx:4480`).

---

## Typography

Valores literais medidos nos quatro blocos e em `SubAbaOperar`:

| Role | Size | Weight | Uso |
|------|------|--------|-----|
| Eyebrow/label | 9px–10.5px | 800, `letterSpacing: 0.03em–0.04em`, uppercase | Título de seção fixo ("OPORTUNIDADES DE OPÇÕES", chip de tipo) |
| Body pequeno | 10.5px–12px | 400–700 | Texto secundário, rótulo de linha, motivo de estado vazio |
| Body padrão | 12.5px–13px | 400–800 | Manchete do motor, texto de proposta, botões |
| Heading de tela | 22px | 800 | `<h1>{cp.tituloOpcoes}</h1>` — não muda nesta fase |

Line-height: `1.4`–`1.6` em texto corrido (subtítulo, disclaimer, motivo de
estado vazio); sem `line-height` declarado em labels curtos de uma linha.

**Esta fase não declara tamanho/peso novo.** A linha de chamada em Posições
usa o mesmo par (rótulo 11.5px/700 + ícone `T.accent`) do toggle de
`PropostaDaPosicao` que ela substitui em espírito.

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
3. Frase-ponte neutra (NOVA, obrigatória — ver abaixo)
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
decisão deste documento. Ver também `## Open Questions`.

---

## Os dois rótulos (D-05) — a entrega de copy mais importante desta fase

**Frase-ponte obrigatória**, acima dos dois blocos, nos dois modos (mesmo
texto — é constatação de fato, não voz de personagem):

> `duasLeiturasIntro`: "Duas leituras diferentes da sua carteira — nenhuma é
> mais certa que a outra: uma parte do que a leitura técnica confirma agora,
> a outra varre a cadeia inteira sem exigir essa confirmação."

Esta frase é **obrigatória, não estilística** — é o que impede a leitura
"um bloco é o correto, o outro é o alternativo/inferior" só pela ordem de
leitura (o Bloco A vem primeiro na tela).

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

### Requisito de arquitetura de dado (consequência do contrato acima, não op

cional)

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
caixa). Não recriar em `OpcoesScreen.jsx`; mover o componente.

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
- **Ordem de foco na aba cheia:** título → sub-abas → frase-ponte (D-05) →
  Bloco A → Bloco B → "Seus vigias" → seletor de ticker → cascata técnica.
  Segue a ordem visual (DOM order = tab order), sem `tabIndex` manual — é
  o padrão já usado em toda a tela (nenhum `tabIndex` customizado encontrado
  em `OpcoesScreen.jsx`/`App.jsx` nestes componentes).
- **D-06 (rolagem aceita, sem busca):** nenhum elemento desta fase usa
  posicionamento `sticky`/`fixed` que impeça inserir uma barra de busca no
  topo depois — os blocos são `<div>` em fluxo normal. Confirmado: não
  desenhar nada que bloqueie isso.
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
| Frase-ponte dos dois motores (D-05) | "Duas leituras diferentes da sua carteira — nenhuma é mais certa que a outra: uma parte do que a leitura técnica confirma agora, a outra varre a cadeia inteira sem exigir essa confirmação." |
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
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending

---

## Open Questions

1. **Fork de hierarquia (Leitura A × B, ver seção "Contrato de composição").**
   D-04/D-07 dizem "topo da aba Opções"; este contrato assume que isso
   significa "topo da sub-aba Setups" (Leitura A), pelo precedente de código
   de que todo conteúdo cross-carteira de hoje (vigias) já vive lá dentro.
   Se o Alex quis dizer "acima do alternador de sub-abas, nas duas"
   (Leitura B), a mudança é pequena mas muda a estrutura de render de
   `OpcoesScreen.jsx`. Recomenda-se confirmar antes de planejar.

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

4. **Frescor/carimbo de dado ausente nos dois blocos cross-carteira** — nem
   `OportunidadesOpcoes` nem `CuradoriaEstruturas` mostram "pregão"/"em
   dia"/"atrasado" hoje, ao contrário do bloco de leitura técnica por
   ticker. Não há requirement desta fase pedindo isso; registrado como
   lacuna pré-existente, não como pendência desta fase.

---

*Phase: 32-Consolidação das operações de opções na aba Opções*
*UI-SPEC gerado: 2026-09-15*
