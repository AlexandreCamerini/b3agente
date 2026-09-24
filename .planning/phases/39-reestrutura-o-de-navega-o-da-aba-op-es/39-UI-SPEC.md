---
phase: 39
slug: reestrutura-o-de-navega-o-da-aba-op-es
status: draft
shadcn_initialized: false
preset: none
created: 2026-09-24
---

# Phase 39 — UI Design Contract

> Contrato visual e de interação para a reestruturação de navegação da aba
> Opções. Esta fase **não introduz** design system novo — reusa os tokens
> `T.*`/constantes de estilo já em produção em `web/src/opcoes/*.jsx`. O
> contrato aqui é sobre **composição, estado de navegação e copy** —
> continuação direta da linhagem `32-UI-SPEC.md` → `34-UI-SPEC.md` →
> `38-UI-SPEC.md`, mesma aba, mesmos tokens. Gerado por gsd-ui-researcher,
> verificado por gsd-ui-checker.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none — React 18 hand-rolled, sem shadcn, sem `components.json` |
| Preset | não aplicável |
| Component library | nenhuma — estilos inline (`style={{...}}`), tokens via CSS custom properties (`T` object, espelho declarado em cada arquivo de `web/src/opcoes/`) |
| Icon library | nenhuma — SVG inline hand-authored (24×24 viewBox, `stroke="currentColor"`, strokeWidth 2) onde precisar de ícone novo (badge de Vigias, ⓘ); glifos de texto (`ⓘ`, `→`, `✓`) onde já é o padrão |
| Font | herdada do shell do app (`App.jsx`), não tocada por esta fase |

**Por que nenhum gate de shadcn roda:** `components.json` ausente repo-wide;
convenção de token estabelecida há 30+ fases (`VARKEY`/`TOKENS`/`T` em cada
`web/src/opcoes/*.jsx`, lendo `var(--*)` injetado por `App.jsx`). Introduzir
shadcn agora seria mudança de arquitetura não pedida, contra
`CLAUDE.md` ("não reescreva a aplicação sem necessidade"). `Tool: none` é a
resposta certa, deliberada — mesma decisão de `32-UI-SPEC.md`/
`34-UI-SPEC.md`/`38-UI-SPEC.md`.

---

## Layout & Interaction Contract

Esta é a parte que sustenta o plano — resolve o que `39-CONTEXT.md` trava
(D-01..D-14) e o que deixa implícito (onde `SecaoSetups`/`SecaoComparar`
realmente moram dentro de "Montar", o destino do card de Oportunidades
depois que "Operar" some, onde o ⓘ entra fisicamente). Sem isso o
planner/executor teriam que re-derivar tudo lendo `OpcoesScreen.jsx` a frio —
exatamente o problema que `34-UI-SPEC.md` já resolveu uma vez para o
hub/workspace, e que esta fase reabre porque muda a forma de novo.

### Modelo de estado — de 2 estados ortogonais para 1

Hoje: `subaba` (`"setups"|"operar"`) × `abaWorkspace`
(`"analisar"|"comparar"|"setups"`), só a segunda sendo condicional a
`ticker`. **Novo: um único `useState`**, ex. `abaOpcoes`, com exatamente 3
valores fixos:

```js
const [abaOpcoes, setAbaOpcoes] = useState("oportunidades");
// "oportunidades" | "recomendadas" | "montar"
```

Nasce em `"oportunidades"` (é a leitura mais barata — motor COM gate,
zero fetch novo no mount, mesmo padrão de custo-zero que `hubTopo` já
seguia). `ticker` continua existindo como estado PRÓPRIO — mas deixa de
governar QUAL CONJUNTO DE ABAS aparece (isso era o par `subaba`/
`abaWorkspace`); ele governa só o CONTEÚDO INTERNO da aba "Montar" (ver
abaixo). As 3 abas de nível 1 são **sempre clicáveis, sempre as mesmas 3**,
com ou sem ticker escolhido — isto é o que D-01 exige literalmente ("sem
segunda camada de abas dependente de estado intermediário").

### Estrutura de topo (substitui `subabas`/`workspacePillRow`/`cabecalho` fixo)

```
OpcoesScreen
  cabeçalho de tela
    <h1>Opções</h1> ................................ inalterado
    VigiasBadge (ícone + contador) .................. NOVO, D-07 — abre sheet
  <p subtituloOpcoes> ............................... inalterado (não é bastidor, é descrição do produto)
  abaBar (3 pills fixas) ............................. NOVO — substitui `subabas` + `workspacePillRow`
    "Oportunidades" | "Recomendadas" | "Montar"
  ── conteúdo da aba ativa ──
    abaOpcoes === "oportunidades" → <AbaOportunidades/>
    abaOpcoes === "recomendadas"  → <AbaRecomendadas/>
    abaOpcoes === "montar"        → <AbaMontar/>
  <VigiasSheet/> (renderiza condicionalmente, ver D-07 abaixo)
  <ConceitoSheet/> local (já existe, Fase 38 — reaproveitada, ver ⓘ abaixo)
```

`abaBar` reusa **verbatim** a régua visual de `subabas`/`seletor`/
`workspacePillRow` (`OpcoesScreen.jsx:657-701`): `minHeight: "44px"`,
`padding: "8px 14px"`, `borderRadius: "11px"`, `border`/`background`/`color`
por `T.accent`/`T.accentTint10` quando ativa, `T.borderSubtle`/`T.bgPanel`/
`T.textSecondary` quando inativa, `fontWeight: 700`, `fontSize: "13px"`,
`aria-pressed`. **Nenhum valor novo de espaçamento/raio/tipografia** — só o
array de 3 itens muda e o `onClick` grava `abaOpcoes` em vez de `subaba`/
`abaWorkspace`.

### `cabecalho` (caixa de Pregão/Fonte/frescor) — deixa de ser fixo no topo

Hoje `cabecalho` (`OpcoesScreen.jsx:464-520`) é ticker-scoped (lê
`leitura`/`status`, que só fazem sentido com um ativo escolhido) mas
renderiza **acima** da condicional hub/workspace, sempre visível mesmo sem
ticker — hoje isso já é estranho (mostra "Pregão: —" com a aba vazia).
Com o novo modelo, **Oportunidades e Recomendadas são cross-carteira, não
ticker-scoped** — não têm frescor de UM ativo para mostrar. `cabecalho`
passa a renderizar **só dentro de "Montar", e só quando um ticker está
selecionado** (mesma condição que `LastroDoAtivo`/`LeituraInterna` já usam
hoje dentro do workspace). Isto não é regressão: hoje, sem ticker, o
`cabecalho` já mostrava só travessões — a informação real só existe com
ticker escolhido.

### D-14 aplicado ao `cabecalho`: o parágrafo de mecânica de cache vira ⓘ

`cp.opcoesCustoFrescor` (`OpcoesScreen.jsx:516-518`, copy.js:138/914) — "Abrir
esta aba consulta o frescor do dado no serviço: consome até 1 chamada da sua
cota do dia..." — é exatamente o "texto de bastidor" que D-14 tira do fluxo
principal. **Não é removido** (é informação real sobre custo, princípio 3 do
CLAUDE.md exige transparência de fonte/custo) — mas some do parágrafo fixo e
vira conteúdo do ⓘ da aba Montar (ver seção ⓘ abaixo). O chip de frescor em
si (`chip`, `frescor.warning` quando bloqueia) **continua inline** — isso é
estado do dado, não mecânica de bastidor; D-14 mira em "cache/cota/lastro/
score bruto", não em "o dado está atrasado".

`cp.opcoesLoteAjuda` ("1 contrato = 100 ações...") **fica inline**, colado
ao campo Lote dentro de `AbaMontar` — não é bastidor, é a explicação
mínima necessária para preencher o próprio campo ao lado dela; escondê-la
atrás de ⓘ pioraria a tarefa (a pessoa precisaria abrir uma folha para saber
o que digitar no campo que está olhando). Esta é uma linha que este UI-SPEC
traça deliberadamente — nem todo texto explicativo é "bastidor" no sentido
de D-14; bastidor é o que **antecede o conteúdo sem ajudar a decisão
imediata** (cache, cota, mecânica interna do motor). Ajuda de campo
contextual não entra nessa categoria.

### Vigias — ícone/badge no cabeçalho (D-07)

**Localização:** linha do `<h1>Opções</h1>`, alinhado à direita
(`display: flex, justifyContent: space-between, alignItems: center`).
Visível nas 3 abas, sempre — não é parte do conteúdo de nenhuma aba.

**Contrato de dado do contador (não é só escolha de ícone — isto é
contrato de dado, precisa ser declarado):** o número no badge é
`listaDeVigias.length`, a MESMA variável já derivada em
`OpcoesScreen.jsx:543-546` (prioriza `vigiasVivos.dados.vigias` quando
existe — superset com estado do dia — e cai para `vigias.dados.vigias`,
o índice de custo zero, quando o estado ainda não foi pedido). **Nenhuma
segunda fonte de contagem** — reusa a variável existente, não recalcula.
Quando `vigias.dados` ainda não respondeu (mount), o badge mostra o ícone
sem número (nunca "0" antes de medir — princípio 4 do CLAUDE.md, mesma
disciplina de `linhaChamadaOpcoes*` em `32-UI-SPEC.md`).

**Estilo do botão:** reusa o padrão de botão neutro compacto —
`minHeight: "44px"`, `padding: "8px 10px"`, `borderRadius: "11px"`,
`border: 1px solid T.borderSubtle`, `background: T.bgPanel`,
`color: T.textSecondary` — mesma geometria de `BOTAO` (`OpcoesScreen.jsx:
140-144`), só compacto o bastante para caber ícone+número numa pastilha ao
lado do `<h1>`. O número, quando > 0, usa `T.accent`/`fontWeight: 700` (é a
única leitura acionável do badge — sinaliza "há vigias armados a checar");
o ícone usa `T.textSecondary` em repouso.

**Ícone exato — Claude's Discretion (39-CONTEXT.md), recomendação não
travada:** um olho ou um sino, 24×24 stroke, mesma convenção de
`38-UI-SPEC.md` §"Icon library" (SVG hand-authored, `stroke="currentColor"`
strokeWidth 2). Recomenda-se 👁 (olho) sobre 🔔 (sino) porque "vigia" no
vocabulário do produto já é "observar", não "notificar" — mas o planner
decide dentro do design system existente, sem travar aqui.

**Sheet:** ao clicar, abre um bottom sheet **local** (módulo próprio de
`web/src/opcoes/`, isolamento ADR-027 intacto — nenhum import de `App.jsx`)
reusando o shell já estabelecido em `entendimento.jsx`
(`ConceitoSheet`, `App.jsx`-espelho local desde a Fase 38):

```
position: fixed, inset: 0, zIndex: 86, background: T.scrim,
display: flex, alignItems: flex-end, justifyContent: center
  → painel: maxWidth 520px, background: T.bgPanel,
    borderRadius: "18px 18px 0 0",
    padding: "16px 18px calc(18px + env(safe-area-inset-bottom))",
    maxHeight: "82vh", overflowY: "auto"
```

`zIndex: 86` é o MESMO valor que `ConceitoSheet` já usa (acima de todos os
outros overlays do app, `entendimento.jsx:201-206`) — não inventar um novo
número de z-index; os dois nunca abrem ao mesmo tempo (fechar um ao abrir o
outro é comportamento aceitável, não travado aqui como requisito, mas
citado para o planner não deixar os dois empilharem por acidente).

**Conteúdo do sheet:** reusa `SecaoVigias.jsx` **inteiro**, sem reescrita —
mesmos props (`vigias`, `vigiasVivos`, `atualizarVigias`, `listaDeVigias`,
`temEstado`, `tickersEmCarteira`, `ticker`, `onIr`, `custos`, `cp`). O botão
de fechar do sheet e o clique fora (scrim) fecham; `onIr` (clicar num vigia)
fecha o sheet E navega — `escolherTicker(t)` + `setAbaOpcoes("montar")`
(mesma razão de D-02/D-03 abaixo: qualquer navegação que leve a "trabalhar
com este ticker" agora aponta para Montar, não mais para uma sub-aba
"Operar" que deixou de existir).

### As 3 abas — composição interna

#### 1. "Oportunidades" (D-02) — `OportunidadesOpcoes.jsx`, motor COM gate

Conteúdo: exatamente o componente `OportunidadesOpcoes.jsx` hoje, sem
alterações de layout — eyebrow (`tiraOpcoesTitulo`) + subtítulo
(`tiraOpcoesSubtitulo`) + carrossel de cards (`flex: "0 0 210px"`, manchete
colorida por polaridade, `→` "ver detalhe") + 3 variantes de vazio já
existentes (`tiraOpcoesSemSetup`/`tiraOpcoesSemMercado`/
`tiraOpcoesSemCobertura`) + carregando. **Nenhuma dessas três variantes de
vazio é substituída por uma genérica** — mesma regra já travada em
`32-UI-SPEC.md`.

Acima do carrossel: ⓘ contextual (ver seção ⓘ abaixo) — substitui o
"saiba mais" fixo que hoje vive no topo da tela inteira.

**Destino do clique num card — fork resolvido nesta seção, ver abaixo.**

#### 2. "Recomendadas" (D-03) — `CuradoriaEstruturas.jsx`, motor SEM gate

Conteúdo: exatamente o componente `CuradoriaEstruturas.jsx` hoje —
eyebrow + subtítulo + resumo de varredura + carrossel (`flex: "0 0 220px"`)
+ painel de confirmação inline (`abertoId`, `handleExecutar`, checkbox de
liquidez DIFÍCIL, botão Executar) + payoff do nº 1 + narração por IA.
**Este é o padrão de execução inline que D-05 cita como referência** — já
está pronto, D-05 não pede reescrevê-lo, só que a sub-aba "Operar" pare de
existir como caminho paralelo.

Duas correções obrigatórias, não opcionais, ambas travadas por decisão do
`39-CONTEXT.md` (D-08/D-09/D-14), detalhadas nas seções próprias abaixo:
piso de admissão (D-08/D-11) e posição-no-ranking em vez de score bruto
(D-14).

#### 3. "Montar" (D-04) — `SecaoAnalisar.jsx` + sub-ações

```
AbaMontar (abaOpcoes === "montar")
  seletor de ticker (chip row, MESMO componente `seletor` de hoje)
  !ticker → Aviso "Escolha um ativo para montar uma estrutura"
             (reusa `cp.opcoesEscolherAtivo`, mesmo texto de hoje)
  ticker →
    cabecalho (Pregão/Fonte/frescor) — só aqui, ver seção acima
    LastroDoAtivo
    LeituraInterna
    blocoLeituraDoServico (convite pago, quando aplicável)
    SecaoAnalisar (tese/vencimento/lote → Montar estrutura → payoff →
                    ExecutarProposta — já inclui execução, quick 260923-ndy)
    link "ver outros vencimentos" (NOVO rótulo, D-06) → expande SecaoComparar
      inline, MESMO container, sem navegação/nova aba
    seção "Setups salvos" (SecaoSetups.jsx inteiro — lista + criação,
      D-03: nome "Setups" preservado) — abaixo, sempre visível quando há
      leitura (mesma condição de hoje)
```

**Resolução do gap que `39-CONTEXT.md` deixa implícito — onde
`SecaoSetups.jsx` mora agora.** D-01 a D-07 mapeiam Oportunidades/
Recomendadas/Montar/Vigias, mas nunca dizem onde vai o antigo 3º item do
`workspacePillRow` ("Setups salvos", hoje pill própria dentro do
workspace). D-01 proíbe segunda camada de abas — então "Setups salvos" NÃO
pode voltar a ser uma pill. A leitura mais consistente com D-04 (Montar =
"o usuário monta sua própria estrutura", texto verbatim do Alex em
`<specifics>`) é: **gerenciar/criar setups salvos é parte do MESMO job**
("montar e acompanhar o que já montei para este ativo") — a seção desce,
sem gate de aba, dentro de `AbaMontar`, abaixo do link de "ver outros
vencimentos". Isto é o mesmo raciocínio que resolveu o D-01 amendment de
`34-UI-SPEC.md` (SecaoSetups migra inteira, sem partição) — aplicado de
novo aqui porque a forma da navegação mudou outra vez. **Flag para
planner/plan-checker confirmar**, mesmo tratamento que `34-UI-SPEC.md` deu
ao seu próprio D-01 amendment (proposta com citação, não decisão
silenciosa).

`SecaoComparar` (D-06) — sub-ação, não aba. Renderiza **inline**, abaixo do
link "ver outros vencimentos", no MESMO container de `AbaMontar` — nunca em
sheet/modal/nova aba (D-06 diz "link... depois de montar uma estrutura",
não "abre uma tela nova"). Continua reusando a MESMA `tese`/`lote` de
`SecaoAnalisar` somente-leitura (já é assim hoje,
`SecaoComparar.jsx:24-25`) — nenhuma mudança de contrato de prop.

O link em si (`cp.opcoesVerOutrosVencimentos`, chave NOVA — ver Copywriting
Contract) reusa o estilo de link secundário já estabelecido (`T.accent`,
`fontWeight: 700`, sem sublinhado, `background: transparent` — mesmo
padrão do link "saiba mais"/"ver posição" já em produção,
`CuradoriaEstruturas.jsx:275-281`). Alterna expandido/recolhido
(`aria-expanded`), mesma mecânica de `abertoId` que `CuradoriaEstruturas`
já usa para seu próprio painel — mas aqui é um `useState` boolean local de
`AbaMontar`, não um id (só existe UM painel de comparação por vez, para o
ticker ativo).

### Fork não resolvido pelo `39-CONTEXT.md`, resolvido aqui com recomendação — destino do card de "Oportunidades"

**O problema:** hoje, clicar num card de `OportunidadesOpcoes` chama
`onAbrir(ticker)` → `irParaOperar` (`OpcoesScreen.jsx:363`) →
`escolherTicker(t); setSubaba("operar")`. A sub-aba "Operar" é exatamente
o que D-05 dissolve. Sem novo destino declarado, o clique no card de
Oportunidades **não tem para onde ir** — regressão silenciosa se ninguém
decidir.

**Duas leituras possíveis:**

- **Leitura A (recomendada, adotada neste contrato):** o clique navega para
  `AbaMontar` com o ticker já selecionado —
  `escolherTicker(t); setAbaOpcoes("montar")` — MESMO padrão de
  `irParaVigia`/`irParaOperar` já em produção, só trocando o destino de
  `setSubaba("operar")` para `setAbaOpcoes("montar")`. A pessoa chega em
  Montar com o ativo já escolhido, `SecaoAnalisar` mostra a leitura técnica
  e o formulário de montagem — que já inclui `ExecutarProposta` (quick
  260923-ndy). **Vantagem:** zero motor novo, zero componente novo — reusa
  o fluxo de execução que Montar já tem, ponta a ponta. **Custo aceito:** a
  proposta PRÉ-CALCULADA pelo motor com gate (`opcoes_lastreadas.propor()`,
  que hoje `SubAbaOperar`/`PropostaLastreada` mostravam pronta — prêmio,
  strike e vencimento já escolhidos pelo motor) deixa de aparecer
  pré-preenchida; a pessoa monta manualmente em `SecaoAnalisar`
  (tese/vencimento/lote). Isto é uma perda de conveniência real, não
  cosmética — nomeada aqui, não escondida.
- **Leitura B (alternativa, não adotada, registrada para decisão do
  Alex/planner):** o card de Oportunidades GANHA o mesmo padrão de
  execução inline que `CuradoriaEstruturas.jsx` já tem — `handleExecutar`
  portado para `OportunidadesOpcoes.jsx`, mostrando a proposta pronta do
  motor com gate (que já existe em `opcoesPorTicker[p.t].proposta`, a MESMA
  entrada que `entrada`/`prop` liam dentro de `SubAbaOperar` antes de ela
  ser dissolvida — o dado já chega até este componente hoje, só não é
  usado para executar). **Vantagem:** preserva a conveniência do motor com
  gate (proposta pronta, sem re-digitar tese/vencimento). **Custo:**
  duplica o padrão de execução inline em DOIS arquivos
  (`OportunidadesOpcoes.jsx` E `CuradoriaEstruturas.jsx`) em vez de um só —
  mais superfície para o checklist `PROIBIDAS`/guardrail CVM cobrir, e
  tecnicamente vai além do texto literal de NAV-01 SC#3 ("a ação de
  executar... aparece inline no card da aba **Recomendadas**" — SC#3 não
  proíbe Oportunidades também ter, mas também não pede).

Este contrato assume a **Leitura A** por ser a menor mudança de
superfície e a que casa literalmente com o texto de NAV-01 SC#3 (execução
inline é requisito só de Recomendadas). **Se o Alex preferir preservar a
proposta pronta do motor com gate, a Leitura B é a mudança certa** — não
invalida nenhuma outra decisão deste documento (é troca local de
`onAbrir` em `OportunidadesOpcoes.jsx` + um `handleExecutar` portado, sem
tocar Recomendadas/Montar/Vigias). **Flag para checkpoint do planner.**

### ⓘ contextual por aba (D-13) — substitui o "saiba mais" fixo do topo

Hoje: um único link "saiba mais" no topo da tela inteira
(`OpcoesScreen.jsx:796-798`), ligado a `ANCORAS_KB.opcoes` = `"mkt-opcao"`
(fixado na Fase 38, D-08, aprovado pelo Alex). D-13 exige: sai do topo
global, vira ⓘ **dentro de cada uma das 3 abas**.

**Mecanismo (reuso, zero componente novo):** cada aba renderiza o mesmo
botão que hoje existe no topo (`ConceitoSheet` local, `verbeteAberto`
state) — só reposicionado, um por aba, ao lado do eyebrow/kicker daquela
aba (`tiraOpcoesTitulo` em Oportunidades, `curadoriaTitulo` em
Recomendadas, `cp.opcoesAnalisarTitulo`/"O QUE DÁ PARA MONTAR" em Montar).
Estilo: ícone `ⓘ` (glifo de texto, sem SVG novo — mesma economia do padrão
já citado em `qa/AUDITORIA-Design-System-v1.md` §5/§10, "ícone ⓘ no
header → abre sheet"), `color: T.accent`, `fontSize: "13px"`, alvo de
toque 44px (área de toque maior que o glifo visível, `padding` suficiente
— mesmo cuidado de acessibilidade que `38-UI-SPEC.md` já documentou para o
"×" de limpar busca).

**`vid` por aba — Claude's Discretion (39-CONTEXT.md não trava),
recomendação:** reusar `ANCORAS_KB.opcoes = "mkt-opcao"` nas 3 abas,
**sem diferenciar por aba nesta fase**. Justificativa: `mkt-opcao` foi
Alex-aprovado na Fase 38 (D-08) como o verbete fundacional desta aba
inteira — reabrir essa escolha por aba é trabalho de curadoria de
conteúdo (qual verbete cada aba merece) fora do escopo de NAV-01, que é
sobre estrutura de navegação, não sobre o catálogo da KB. Diferenciar por
aba (ex.: Recomendadas → verbete sobre ranking/probabilidade quando um
existir; Montar → verbete sobre montagem de estrutura) é melhoria futura
válida, não bloqueante aqui — **não travado, aberto ao planner**.

### D-08/D-09/D-11 — piso de admissão e ordenação em Recomendadas (impacto de UI)

Este UI-SPEC não prescreve o cálculo (`black_scholes`/`prob_itm`,
`opcoes_curadoria.py` — território de backend/planner), só o CONTRATO
VISUAL do resultado:

- **D-11 (lista vazia por piso):** quando o piso de 60% de probabilidade
  OTM filtra TODOS os candidatos, `CuradoriaEstruturas` precisa de um
  ESTADO PRÓPRIO — não o `cp.curadoriaVazio` genérico atual ("nenhuma
  estrutura elegível... por isso não há nada para ranquear agora"), que
  não nomeia O MOTIVO específico (o piso, não "nada existe"). Chave nova
  (`curadoriaVazioPiso`, ver Copywriting Contract) com precedência sobre o
  vazio genérico — mesma disciplina de precedência já estabelecida entre
  `erro`/`naoMedido`/vazio em `CuradoriaEstruturas.jsx:298-328`: **4
  estados agora, não 3** (carregando → erro → vazio-por-piso → vazio-sem-
  candidato-nenhum). O backend precisa expor QUAL dos dois vazios é (zero
  candidatos varridos vs. candidatos varridos mas nenhum passou no piso)
  — contrato de dado que o plano declara, este UI-SPEC só exige que os
  dois textos existam e sejam distintos (princípio 4 do CLAUDE.md: nunca
  dizer "não há oportunidade" quando na verdade "há candidatos, mas nenhum
  passou no piso de segurança que você pediu").
- **D-08/D-09 (ordenação nova):** nenhuma mudança visual no CARROSSEL em
  si — os cards continuam na mesma forma (`flex: "0 0 220px"`, eyebrow +
  manchete + linha de resumo). O que muda é o CONTEÚDO da linha de resumo
  (ver D-14 abaixo, posição no ranking em vez de score bruto) e o
  `curadoriaSubtitulo`, que precisa passar a mencionar o piso de 60% —
  ver Copywriting Contract.

### D-14 — score bruto vira posição no ranking

`CuradoriaEstruturas.jsx:194` hoje renderiza:
`{cp.curadoriaRazaoRotulo}: {cand.razao.toFixed(2)}` — "Pontuação de
curadoria (ordena a lista — não é o resultado da estrutura): 0.02". Este é
o "score bruto" que D-14 nomeia explicitamente. **Esta linha é removida**
do painel de confirmação inline — não substituída por outro número técnico
no mesmo lugar.

A posição no ranking **já é exibida** no eyebrow do card
(`cand.posicaoNoRanking + ". " + cand.ticker`, linha 184) — D-14 pede que
ESSA seja a única forma de comunicar ordem, então nenhuma adição é
estritamente necessária ali. Recomenda-se reforçar no painel expandido
(onde a linha removida deixa um espaço) com uma frase curta que nomeia o
total, não só a posição: `"1ª de 4"` / `"3ª de 4"`, usando
`cand.posicaoNoRanking` + `top.length` (ambos já disponíveis no
componente, nenhuma prop nova) — chave nova `curadoriaPosicaoRotulo`, ver
Copywriting Contract. `curadoriaRazaoRotulo` (a chave de copy) fica **não
usada por este componente** após a mudança — não precisa ser deletada de
`copy.js` (pode servir outro consumidor no futuro), mas o guardião que
hoje talvez a valide neste arquivo específico deixa de encontrá-la aqui.

### Frase de enquadramento de Recomendadas — risco regulatório herdado, não resolvido por decisão explícita do CONTEXT.md

`32-UI-SPEC.md` (D-05 da Fase 32, ainda vigente em espírito) exigiu uma
frase-ponte SEMPRE visível entre os Blocos A e B ("nenhuma é mais certa
que a outra") precisamente para impedir que "AS 4 MELHORES OPORTUNIDADES
DE OPÇÕES" (motor sem gate) fosse lido como veredito geral do app.
**Com Oportunidades e Recomendadas virando abas SEPARADAS (não mais blocos
adjacentes na mesma tela), essa frase-ponte física deixa de fazer
sentido como estava** — ninguém vê as duas ao mesmo tempo para ler a
ponte entre elas. O risco que ela mitigava (ler "as 4 melhores" como
verdade universal, não como resultado de UM motor entre dois) **continua
existindo, só que agora precisa ser resolvido DENTRO de cada aba, não
entre elas**.

Isto não está decidido em `39-CONTEXT.md` (D-01 a D-14 não mencionam a
frase-ponte). **Não resolvido silenciosamente aqui** — mas o contrato
exige, como consequência de CLAUDE.md princípio 6 (a IA não promete
rentabilidade, não veste recomendação como certeza) e princípio 9 (nenhum
estado escondido): `curadoriaSubtitulo` (o subtítulo da aba Recomendadas)
precisa continuar fazendo o trabalho que a frase-ponte fazia — nomear que
é UM critério de ordenação entre outros, não veredito. A revisão de copy
do D-08/D-09 (ordenação nova) É a oportunidade natural de reescrever essa
frase preservando a função regulatória — ver Copywriting Contract,
`curadoriaSubtitulo` novo. **Flag para plan-checker**: confirmar que a
frase nova, ao ser escrita no plano, ainda cumpre essa função (checklist
`PROIBIDAS` de `test_curadoria_ui.mjs` continua a régua).

### Mobile 375px

Nenhum primitivo de layout novo além do `VigiasBadge`/sheet e do `ⓘ` —
ambos reusam geometria já testada em produção (botão 44px, sheet com
`maxHeight: 82vh` e `safe-area-inset-bottom`, já em uso desde a Fase 38).
A `abaBar` de 3 pills reusa a mesma régua de `subabas`/`seletor`
(min-height 44px, padding 8/14) que já renderiza corretamente em 375px há
30+ fases — 3 pills em vez de 2 cabem na mesma largura útil (339px, ver
`32-UI-SPEC.md` §"Contrato mensurável de densidade") porque os rótulos
("Oportunidades"/"Recomendadas"/"Montar") são comparáveis em comprimento
aos atuais ("Setups"/"Operar"/"Analisar"/"Comparar"/"Setups salvos"); se
o executor medir que "Oportunidades"+"Recomendadas"+"Montar" não cabem
numa linha só em 375px, a `abaBar` já usa `flexWrap` implícito? **Não —
`subabas`/`workspacePillRow` hoje NÃO têm `flexWrap: "wrap"`** (só
`gap`/`display: flex`). Isto é uma checagem obrigatória do executor, não
resolvida por medição aqui (seria estimativa sem medir a fonte real): se
as 3 pills não couberem numa linha em 375px, a correção mínima é
`flexWrap: "wrap"` na `abaBar` (nenhum valor de espaçamento novo, só a
propriedade de quebra) — nunca abreviar os rótulos para caber (rótulo
abreviado sem sentido reintroduz a ambiguidade que esta fase resolve).

---

## Spacing Scale

Reuso integral dos valores já em produção em `web/src/opcoes/*.jsx` — esta
fase não introduz escala nova. Citados por já estarem fora da grade
padrão de 4/8px (mesma ressalva de `32-UI-SPEC.md`/`34-UI-SPEC.md`):

| Token | Valor | Uso | Citação |
|-------|-------|-----|---------|
| alvo de toque mínimo | 44px | TODO elemento clicável novo (pills da `abaBar`, `VigiasBadge`, ⓘ, link "ver outros vencimentos") | `OpcoesScreen.jsx:140` (`BOTAO`), não-negociável em todo o app |
| padding de pill | 8px 14px | `abaBar` (3 pills) | `OpcoesScreen.jsx:658-673` (`subabas`), `683-701` (`workspacePillRow`) — mesma régua, array trocado |
| padding de caixa | 12px 14px | `cabecalho` (agora só dentro de Montar), `CAIXA` | `OpcoesScreen.jsx:184-187`, `464` |
| raio de caixa/botão | 11px–14px | pills (11px), caixas/cabecalho (12-14px) | `OpcoesScreen.jsx:141`, `184`, `465` |
| padding de sheet | 16px 18px + safe-area | `VigiasSheet` (novo, reuso do shell de `ConceitoSheet`) | `entendimento.jsx:208` |
| gap entre pills/chips | 8px | `abaBar`, `seletor` | `OpcoesScreen.jsx:612`, `658`, `684` |

**Exceção herdada, já aprovada em fases anteriores desta mesma aba**
(`developer-approved — matches existing pattern — 2026-09-15/20`, ver
`32-UI-SPEC.md`/`34-UI-SPEC.md`): esta árvore de arquivos não segue grade
estrita de 4px (10px/12px/14px convivem). Nenhum valor NOVO fora desse
conjunto já aprovado é introduzido por esta fase — `VigiasBadge` e o ⓘ
reusam padding/raio já citados acima, não inventam um terceiro.

---

## Typography

Nenhum tamanho/peso novo além dos já catalogados em `32-UI-SPEC.md`
(exceção de 3 pesos — 400/700/800 — já aprovada,
`developer-approved — matches existing pattern — 2026-09-15`):

| Role | Size | Weight | Uso |
|------|------|--------|-----|
| `<h1>Opções</h1>` | 22px | 800 | inalterado |
| Eyebrow de seção (título de aba) | 10px | 800, letterSpacing 0.04em, uppercase | `tiraOpcoesTitulo`/`curadoriaTitulo`, agora também eyebrow interno de "Montar" |
| Label de pill (`abaBar`) | 13px | 700 | 3 rótulos novos, mesma métrica de `subabas` |
| `VigiasBadge` — contador | 12px–13px | 700 | número, quando > 0 |
| ⓘ (glifo) | 13px | 400 (glifo, não texto customizado) | reuso do padrão "saiba mais"/ⓘ já citado |
| Body de card (manchete) | 12.5px | 700 | inalterado, `CuradoriaEstruturas`/`OportunidadesOpcoes` |
| Link secundário ("ver outros vencimentos") | 11.5px–12px | 700 | mesma métrica de "ver posição"/"saiba mais" (`CuradoriaEstruturas.jsx:278`) |

Line-height: 1.4–1.6 em texto corrido (subtítulos, avisos), sem
`line-height` declarado em labels curtas de uma linha — igual às fases
anteriores desta aba.

---

## Color

Sem hex novo — sistema de dois eixos (tema × modo) já implementado,
tokens `T.*` lidos de `var(--*)`.

| Role | Token | Uso |
|------|-------|-----|
| Dominante (60%) | `T.bgBase` | fundo da tela |
| Secundária (30%) | `T.bgPanel` / `T.bgCard` | caixas, cards, sheet do Vigias |
| Acento (10%) | `T.accent` / `T.accentTint10` | pill ativa da `abaBar`, número do `VigiasBadge` quando > 0, ⓘ, link "ver outros vencimentos", CTA de execução (Montar/Recomendadas) |
| Positivo/Negativo | `T.positive` / `T.negative` | polaridade CALL/PUT na manchete — nunca `T.accent` ali (guardrail já travado) |
| Aviso | `T.warn` | erro de busca, vazio-por-piso (D-11) quando comunicado como estado de atenção — **decisão de cor**: vazio-por-piso NÃO é erro (a busca funcionou, só que ninguém passou no piso) — usar `T.textSecondary` (mesmo tom do vazio genérico hoje), não `T.warn`. `T.warn` fica reservado a falha de busca de verdade (`erro === true`), preservando a distinção que `32-UI-SPEC.md` já travou |

**Accent reservado para:** pill ativa da `abaBar` (border+background tint+
texto — mesmo padrão de `subabas`/`seletor`), número do contador do
`VigiasBadge` quando `> 0`, o glifo ⓘ nas 3 abas, o link "ver outros
vencimentos", botões de execução (`handleExecutar` em Recomendadas,
`montarProposta`/`ExecutarProposta` em Montar). **Nunca** na manchete do
motor (guardrail CVM, inalterado) e nunca no ícone do `VigiasBadge` em
repouso (só o número, quando há algo a reportar).

**Débito de cor pré-existente, tocado por esta fase — correção
obrigatória, não opcional:** `CuradoriaEstruturas.jsx:268`
(botão "Executar", o mesmo botão que D-05 cita como o padrão de referência
inteiro desta fase) usa `color: "#fff"` **literal**, não `T.onAccent`. A
Fase 35 (`35-UI-SPEC.md`) já mediu e travou que `#fff` reprova AA em
Dark·Estudo (2,90:1) e Dark·Operador (2,10:1) contra o preenchimento de
`T.accent`, e estabeleceu `T.onAccent` como o token correto — mas
`CuradoriaEstruturas.jsx` foi escrito na Fase 32, antes dessa correção, e
nunca foi revisitado. Como esta fase é EXATAMENTE a que promove este botão
a "o padrão de execução da aba inteira" (D-05, reusado também em
Oportunidades se a Leitura B do fork acima for adotada), **o `#fff`
literal deve ser trocado por `T.onAccent` como parte desta fase** — não é
mudança de escopo, é a mesma linha que já vai ser tocada para acrescentar
`onRecarregar` e a lógica de D-08/D-11.

---

## Copywriting Contract

| Elemento | Copy | Status |
|---|---|---|
| Título da aba "Oportunidades" | `opcoesAbaOportunidades`: "Oportunidades" (Estudo e Operador) | NOVA chave |
| Título da aba "Recomendadas" | `opcoesAbaRecomendadas`: "Recomendadas" (Estudo e Operador) | NOVA chave |
| Título da aba "Montar" | `opcoesAbaMontar`: "Montar" (Estudo e Operador) | NOVA chave |
| `VigiasBadge` — aria-label | `opcoesVigiasAbrirSheet`: função `(n) => n > 0 ? n + " vigias — abrir" : "Vigias — abrir"` | NOVA chave, sem número inventado antes de medir |
| Link "ver outros vencimentos" (D-06) | `opcoesVerOutrosVencimentos`: "Ver outros vencimentos" (Estudo) / idêntico (Operador — é navegação, não voz de personagem) | NOVA chave |
| ⓘ por aba — aria-label | reusa `cp.saibaMais` ("saiba mais") como texto visível do botão ⓘ, com `aria-label` explícito por aba (ex.: `"O que é uma opção — Oportunidades"`) para leitor de tela não repetir "saiba mais" 3× sem contexto | reuso de chave existente + `aria-label` composto no plano |
| Vazio de Recomendadas por piso (D-11) | `curadoriaVazioPiso`: "Nenhum candidato com pelo menos 60% de chance de ficar OTM no vencimento hoje. Isto não significa que não há oportunidade — significa que nenhuma passou no piso de segurança desta lista." | NOVA chave, precedência sobre `curadoriaVazio` genérico |
| Posição no ranking (D-14, substitui score bruto) | `curadoriaPosicaoRotulo`: função `(pos, total) => pos + "ª de " + total` | NOVA chave, dado 100% já disponível (`posicaoNoRanking`, `top.length`) |
| `curadoriaSubtitulo` (D-08/D-09, preserva função regulatória) | Reescrever para nomear o piso + a ordenação nova, preservando "ordem do motor, IA não reordena" — ex.: "Candidatos com pelo menos 60% de chance de ficar OTM, ordenados por prêmio anualizado — entre um critério possível de ordenar, não uma promessa de resultado. Ordem do motor; a IA não reordena." | REESCRITA obrigatória, conteúdo exato é território do plano (checklist `PROIBIDAS` de `test_curadoria_ui.mjs` se aplica) |
| `opcoesCustoFrescor` (D-14, cache/cota) | Sem mudança de texto — só de LOCAL: sai do parágrafo fixo, vira conteúdo do ⓘ da aba Montar | RELOCADA, não reescrita |
| `opcoesLoteAjuda` | Sem mudança — fica inline, ver justificativa na seção Layout | INALTERADA |
| Chaves retiradas de uso nesta aba (não deletadas de `copy.js` — só sem consumidor nesta tela após a mudança) | `opcoesSubabaSetups`, `opcoesSubabaOperar` (nomeavam o alternador Setups/Operar, agora dissolvido); `opcoesAbaAnalisar`, `opcoesAbaComparar`, `opcoesAbaSetupsSalvos` (nomeavam a pill row de 3 abas dentro do workspace, agora dissolvida) | RETIRADAS — não usar em código novo; **isto também resolve, por remoção, a colisão de rótulo "Setups" × "Setups salvos" citada em NAV-01 e em `copy.js:1133/1143`** (o modo Operador tinha `opcoesSubabaSetups: "Setups"` E `opcoesAbaSetupsSalvos: "Setups"` na MESMA tela — ambas as chaves saem de uso, a colisão desaparece com elas, não precisa de renome |
| Destructive confirmation | Não aplicável — nenhuma ação destrutiva nova nesta fase (desativar setup já existente, fluxo intocado) | — |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|--------------|
| shadcn official | não aplicável — projeto não usa shadcn | não aplicável |
| terceiros | nenhum | não aplicável |

---

## Estados completos (princípio 9 do CLAUDE.md) — resumo por aba

| Aba | Carregando | Vazio | Erro | Nota |
|---|---|---|---|---|
| Oportunidades | `tiraOpcoesCarregando` (existente) | 3 variantes existentes (`tiraOpcoesSemSetup`/`SemMercado`/`SemCobertura`) — preservadas | não rastreado hoje (gap pré-existente, herdado de `32-UI-SPEC.md` Open Question #3 — fora de escopo desta fase) | — |
| Recomendadas | `curadoriaCarregando` (existente) | **2 variantes agora**: `curadoriaVazio` (nenhum candidato varrido) × `curadoriaVazioPiso` (varreu, nenhum passou no piso) — NOVA distinção, D-11 | `curadoriaErroBusca` (existente, Fase 32) | precedência: erro > vazio-piso > vazio-genérico > dados |
| Montar | `cp.opcoesCarregando` (existente, por sub-bloco: leitura/cadeia/operáveis/proposta) | `cp.opcoesEscolherAtivo` (sem ticker) | `ErroDoMcp`/`RecusaCobrada` (existente) | inalterado — esta fase só move ONDE a aba aparece, não os estados internos de `SecaoAnalisar` |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS — inclui a correção obrigatória `#fff`→`T.onAccent` em `CuradoriaEstruturas.jsx:268`
- [ ] Dimension 4 Typography: PASS — exceção `developer-approved — matches existing pattern` (3 pesos) herdada de `32-UI-SPEC.md`
- [ ] Dimension 5 Spacing: PASS — exceção `developer-approved — matches existing pattern` herdada de `32-UI-SPEC.md`/`34-UI-SPEC.md`
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending

---

## Open Questions

1. **Fork do destino do card de Oportunidades** (Leitura A × B, ver seção
   própria acima) — este contrato assume Leitura A (navega para Montar,
   monta manualmente). Se o Alex preferir preservar a proposta pronta do
   motor com gate, a Leitura B troca só `OportunidadesOpcoes.jsx`, sem
   invalidar o resto deste documento. **Flag para checkpoint do
   planner/Alex antes de codar.**
2. **Local de `SecaoSetups` dentro de "Montar"** — proposto aqui (seção
   sem gate de aba, abaixo do link de comparação), seguindo o mesmo padrão
   de resolução do D-01 amendment em `34-UI-SPEC.md`. Não travado por
   nenhuma decisão explícita do `39-CONTEXT.md` — **flag para
   plan-checker confirmar antes de fechar o plano**.
3. **`vid` do ⓘ diferenciado por aba** — este contrato recomenda reusar
   `mkt-opcao` nas 3 abas (mesmo verbete Alex-aprovado na Fase 38).
   Diferenciar por aba é melhoria futura válida, não bloqueante.
4. **Frase de enquadramento regulatório de Recomendadas** (a sucessora da
   frase-ponte da Fase 32) — este contrato exige que `curadoriaSubtitulo`
   cumpra essa função, mas não escreve o texto final (território do
   plano, sob o checklist `PROIBIDAS` já existente). **Flag para
   plan-checker.**
5. **`abaBar` em 375px sem `flexWrap`** — hoje `subabas`/`workspacePillRow`
   não têm `flexWrap: "wrap"`. Se 3 rótulos não couberem numa linha em
   375px, adicionar `flexWrap: "wrap"` é a correção mínima — não medido
   aqui (seria estimativa), **checagem obrigatória do executor** antes de
   fechar a task da `abaBar`.
6. **Erro de busca não rastreado em Oportunidades** — herdado de
   `32-UI-SPEC.md` Open Question #3, ainda não resolvido, ainda fora de
   escopo desta fase (não é requisito de NAV-01).

---

*Phase: 39-Reestruturação de navegação da aba Opções*
*UI-SPEC gerado: 2026-09-24*
