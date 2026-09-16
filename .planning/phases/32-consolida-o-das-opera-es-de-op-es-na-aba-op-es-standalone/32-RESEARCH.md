# Phase 32: Consolidação das operações de opções na aba Opções - Research

**Researched:** 2026-09-15
**Domain:** Refatoração de UI React (mover 4 componentes + 1 hook entre `web/src/App.jsx` e `web/src/opcoes/OpcoesScreen.jsx`, sem novo backend, sem nova lib)
**Confidence:** MEDIUM-HIGH — código lido diretamente (arquivo+linha citados abaixo), não inferido. As áreas de confiança MEDIUM são decisões de arquitetura que o CONTEXT.md delega ao planner (ver Open Questions) e a extensão real do impacto sobre os ~90 testes que fazem `readFileSync(App.jsx)` sem depender da localização dos 4 blocos.

## Summary

Esta é uma fase de arqueologia de código, não de pesquisa de biblioteca. Os quatro
blocos que saem de `CarteiraScreen` (`OportunidadesOpcoes`, `CuradoriaEstruturas`,
`PropostaDaPosicao`, `CandidatoOpcao`) e o hook `useCuradoria()` são componentes
React puros — recebem tudo por prop, não têm acoplamento de import a `App.jsx`
que impeça a mudança de arquivo. O obstáculo real não é técnico-de-produto, é
**dois problemas de dado compartilhado** e **uma dúzia de guardiões estáticos**
que travam a localização exata desses blocos dentro de `App.jsx` por
`indexOf("function X")` — mover sem atualizar esses testes quebra a suíte
inteira, não por regressão de comportamento, mas porque os testes deixam de
achar as âncoras.

Os dois problemas de dado: (1) a contagem da nova linha de chamada em Posições
(D-03) precisa vir do MESMO dado que alimenta a lista curada em Opções —
`useCuradoria()` hoje só é chamado uma vez, dentro de `CarteiraScreen`; se a
lista se muda para `OpcoesScreen`, alguém precisa decidir onde a busca
realmente acontece sem duplicar a chamada de rede (que consome orçamento do
mydata, não é grátis) nem sem quebrar o caso "abriu app, nunca visitou
Posições/Opções, zero chamada disparada" que vale hoje. (2) `SubAbaOperar`
(destino de `PropostaDaPosicao`/`CandidatoOpcao` por D-04) já faz sua PRÓPRIA
busca de gate/proposta por ticker, redundante com o que `useOpcoesPropostas`
já busca para `CarteiraScreen` — e essa tela HOJE só suporta candidato único
(`PropostaLastreada`), nunca múltiplos candidatos (`CandidatoOpcao`), então
o "destino já existe, não precisa de props novas" do CONTEXT.md está
parcialmente correto: a casca está pronta, a lógica multi-candidato não.

**Primary recommendation:** tratar isto como uma fase de EXTRAÇÃO PARA MÓDULO
COMPARTILHADO, não de "recortar-colar" — os quatro blocos e `useCuradoria`
devem sair de `App.jsx` para um módulo terceiro (padrão já estabelecido em
`web/src/opcoes/PropostaLastreada.jsx`, ADR-027 Emenda 3), e o fetch de
curadoria deve subir para o nível onde `ctx` já é construído uma vez (a
função `App()`, não `CarteiraScreen`), com o efeito ainda gatilhado por
visita a uma das duas telas — não por boot do app. Cada guardião estático
listado abaixo precisa de reescrita explícita (não é ajuste de 1 linha).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Renderização dos 4 blocos de opções | Frontend (React, client) | — | Componentes puros, sem I/O próprio (recebem dado por prop) |
| Busca de gate/proposta por posição (`useOpcoesPropostas`) | Frontend (client, efeito) | API/Backend (`/api/options/gate`, `/api/options/proposta`) | Fetch client-side já existe; rotas já existem, custo zero de MCP |
| Busca da lista curada (`useCuradoria`) | Frontend (client, efeito) | API/Backend (`/api/options/curadoria`) | Idem; ATENÇÃO: a varredura por trás desta rota consome orçamento do `mydata_budget` (não é "custo zero" em todos os sentidos — ver Common Pitfalls) |
| Execução do candidato (abrir lastreada/collar/a descoberto) | API/Backend (`store.py`, rotas `/api/options/*`) | Frontend (`executarCandidato.js`, despacho puro) | Cálculo determinístico é sempre do backend (princípio 5 CLAUDE.md); front só traduz candidato → corpo da rota |
| Navegação entre abas (Posições → Opções) | Frontend (client, estado local `tab`) | — | `navigate(t)` é troca de estado React (`setTab`), não roteamento de URL |
| Vocabulário por modo (linha de chamada nova) | Frontend (`copy.js`) | — | Texto nunca composto no componente; chave nova entra nos dois modos |

## User Constraints (from CONTEXT.md)

<user_constraints>

### Locked Decisions

- **D-01:** Posições perde os QUATRO blocos de opções (`OportunidadesOpcoes`,
  `CuradoriaEstruturas`, `PropostaDaPosicao`, `PropostaLastreada`/`CandidatoOpcao`
  dentro dele). Fica **uma única linha de chamada**, discreta, com contagem —
  no espírito de `"3 oportunidades de opções nas suas posições →"`.
- **D-02:** Clicar na linha leva à **aba Opções, na lista de oportunidades**
  — não a uma oportunidade específica (sem card de origem em Posições, não há
  o que deep-linkar).
- **D-03:** A contagem da linha tem de vir do MESMO dado que alimenta a lista
  curada — nunca um número calculado à parte no front (princípio 4 do
  CLAUDE.md: não inventar valor).
- **D-04 — Onde os blocos aterrissam:** a lista curada (`CuradoriaEstruturas`)
  vai para o topo da aba Opções, fora do seletor de ticker, junto dos vigias
  (precedente Fase 27 D4, aprovado). Os blocos **por posição**
  (`PropostaDaPosicao`, `PropostaLastreada`) vão para a sub-aba **"Operar"**.
- **D-05 — Os dois motores lado a lado:** manter os dois (`opcoes_lastreadas.propor()`
  com gate técnico × `opcoes_curadoria` sem gate), com rótulos que expliquem
  a diferença — **não unificar** nesta fase. Um bloco é "o que a leitura
  técnica endossa agora", o outro é "o que existe de melhor na cadeia,
  endossado ou não".
- **D-06 — Rolagem da aba cheia:** aceita e adiada. Sem busca, sem filtro,
  sem acordeão novo nesta fase. O planner não pode desenhar nada que
  **impeça** busca depois.

### Claude's Discretion

D-04, D-05 e D-06 acima já foram decididos pelo Claude (o Alex delegou:
"decide o resto por mim") e estão registrados como decisões fechadas, não
como sugestões — mas o Alex pode revisar o CONTEXT.md antes de planejar se
quiser mudar.

### Deferred Ideas (OUT OF SCOPE)

- **Unificar os dois motores de proposta** (`opcoes_lastreadas.propor()` ×
  `opcoes_curadoria`) — fase própria, peso regulatório. Candidata mais forte
  a próxima fase depois da 32.
- **Busca/filtro na aba Opções** para carteiras grandes — herdado da Fase 27
  ("Em aberto #2"), adiado de novo.
- **Deep-link para uma oportunidade específica** — fora por D-01/D-02; volta
  a fazer sentido se Posições um dia voltar a exibir cards.
- Fora de escopo também: qualquer mudança em rota de execução ou no motor
  determinístico.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| D-01 | Posições perde os 4 blocos, fica com 1 linha de chamada com contagem | Ver "Mapa exato do que se move" — os 4 call sites em `App.jsx` estão identificados linha a linha; a linha nova precisa de novo `cp.*` (copy.js) e de uma fonte de contagem (ver D-03) |
| D-02 | Clique navega para a aba Opções, na lista — sem selecionar ticker | Ver "Navegação entre telas" — `navigate(t)` é só `setTab`; a aba já abre "na lista" por desenho (ticker nasce `""`), então D-02 não exige mecanismo novo, só chamar `navigate("opcoes")` a partir de Posições |
| D-03 | Contagem da linha vem do MESMO dado da lista curada | Ver "O hook useCuradoria()" — é o achado central desta pesquisa: hoje só existe UMA instância do hook, dentro de `CarteiraScreen`; UI em duas telas precisa de estado compartilhado, com tradeoff de custo explicitado |
| D-04 | Blocos aterrissam: curada no topo (fora do ticker), por-posição na sub-aba Operar | Ver "SubAbaOperar como destino" — a casca aceita o candidato único hoje; falta suporte a multi-candidato (`CandidatoOpcao`), gap real não coberto pelo CONTEXT.md |
| D-05 | Dois motores lado a lado, rotulados, sem unificar | Sem impacto técnico de research — é decisão de copy/rótulo; ver Open Questions sobre o destino de `OportunidadesOpcoes` (motor com gate) |
| D-06 | Rolagem aceita, não inventar busca | Sem impacto técnico — nenhum componente novo de busca/filtro deve ser criado |

</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Paridade `deviceStore` ↔ `serverStore`:** esta fase, pelo que a pesquisa
  encontrou, **não precisa** de método novo de store — `executarCandidato.js`
  já despacha para métodos existentes nos dois stores, e mover componentes de
  arquivo não adiciona campo novo de estado. Se o planner decidir criar um
  endpoint/campo novo para resolver D-03 (ex.: um contador dedicado), a
  paridade se aplica e precisa entrar no plano.
- **Manchete só do motor determinístico (guardrail CVM):** `item.manchete`
  (em `CuradoriaEstruturas`) e `pr.manchete` (em `OportunidadesOpcoes`) são
  renderizados verbatim hoje — a migração de arquivo NÃO pode introduzir
  composição de frase a partir de strike/prêmio/optionType. Os guardiões que
  travam isso (`test_curadoria_ui.mjs` regra 2, `test_carteira_opcoes_tira.mjs`)
  precisam ser recriados no novo local, não apenas movidos.
- **Guardiões de teste não se apagam:** ver seção "Guardiões de teste em
  risco" abaixo — TODOS os testes listados precisam de nota datada
  (2026-09-15/16, Fase 32) quando forem reescritos, nunca silenciosamente
  apagados.
- **Suíte canônica:** `bash scripts/executar.sh --testes` (pytest + `.mjs`).
  Front editado → `npx vite build` antes de declarar ok.
- **Skill `didatica-boris`:** texto novo de UI (a linha de chamada) entra nos
  DOIS modos (`COPY.estudo`/`COPY.operador`) em `copy.js`, nunca só um.
  `test_curadoria_ui.mjs` já demonstra o padrão de teste de paridade de
  CONJUNTO de chaves (`chavesCuradoriaDe`) que deve ser reaproveitado para a
  chave nova da linha de chamada.

## Standard Stack

Não aplicável — esta fase não introduz biblioteca nova. Stack já em uso:
React 18 (hooks, sem router), `web/src/copy.js` (vocabulário), `web/src/opcoes/*`
(módulos isolados de `App.jsx` por ADR-027).

## Package Legitimacy Audit

N/A — esta fase não instala pacote externo novo.

## Mapa exato do que se move

Confirmado por leitura direta (linhas podem ter se deslocado ligeiramente
desde o CONTEXT.md, conferidas em 2026-09-15):

| Bloco | Definição | Call site em `CarteiraScreen` | Depende de |
|-------|-----------|-------------------------------|------------|
| `OportunidadesOpcoes` | `App.jsx:4101-4174` | `App.jsx:4852` | props: `propostas` (de `useOpcoesPropostas`), `carregando`, `positions`, `cp`, `onAbrir` (= `abrirOpcoesDe`) |
| `CuradoriaEstruturas` | `App.jsx:4198-4438` | `App.jsx:4856-4870` | props: `top`/`meta`/`carregando`/`erro`/`narrativa`/`narrando`/`erroNarrativa` (de `useCuradoria()`), `onNarrar`, `cp`, `onAbrir`, `onExecutar` (= `ctx.A.executarCandidatoCurado`), `operador`, `palette` (= `ctx.palette`) |
| `PropostaDaPosicao` | `App.jsx:4449-4503` | `App.jsx:5008-5011`, dentro do `.map` de `data.positions` | props: `t`, `r` (= `(opcoesPorTicker[p.t]\|\|{}).proposta`), `cp`, `operador`, `A` (= `ctx.A`), `data` (= `ctx.data`), `aberto`/`onToggle` (estado local `opcoesFor`) |
| `CandidatoOpcao` | `App.jsx:4513-~4600` | dentro de `PropostaDaPosicao` (linha 4492), quando `candidatos.length > 1` | props: `p`, `r`, `cp`, `operador`, `busy`, `onAceitar`, `onVerbeteLiquidez` |
| `useCuradoria()` (hook) | `App.jsx:4687-4736` | chamado 1x em `CarteiraScreen` (`App.jsx:4762`) | `store.opcoesCuradoria()`, `store.opcoesCuradoriaNarrativa()` |
| `ROTULO_TIPO_CURADORIA` (mapa módulo) | `App.jsx:4191-4196` | usado só dentro de `CuradoriaEstruturas` | nenhum estado — constante pura, mapeia tipo→chave de copy |

Todos os quatro componentes de UI são **puros por prop** — nenhum deles
importa nada de `App.jsx` internamente (são funções declaradas DENTRO de
`App.jsx`, mas não referenciam variáveis de módulo privadas de `App.jsx` além
de helpers genéricos já replicados em outros módulos de `web/src/opcoes/`:
`T` (tokens de tema via CSS var), `MONO`, `money`/`price`, `carouselTrackStyle`/
`carouselItemStyle`, `PayoffChart` (import já existe em ambos os arquivos).
Isso é o que torna a extração viável sem redesenho — mesma conclusão do
CONTEXT.md, confirmada por leitura.

## O hook `useCuradoria()` (achado central)

`useCuradoria()` (`App.jsx:4687-4736`) é chamado **exatamente 1 vez** hoje,
dentro de `CarteiraScreen` (`App.jsx:4762`). Ele dispara `store.opcoesCuradoria()`
em um `useEffect` com `[]` de dependência — ou seja, dispara **ao montar
`CarteiraScreen`**, que só monta quando `tab === "carteira"`
(`App.jsx:9776-9780`). Hoje, se o usuário nunca visita a aba Posições, essa
chamada nunca acontece.

Isto choca com D-03 ("a contagem da linha de Posições tem que vir do mesmo
dado que a lista curada"): se `CuradoriaEstruturas`/`useCuradoria` se mudam
inteiramente para `OpcoesScreen`, `CarteiraScreen` deixa de ter acesso a
`top`/`meta` para montar a contagem, a menos que:

- **(a)** o hook suba para o componente `App()` (`App.jsx`, onde `ctx` é
  construído uma única vez, `App.jsx:9434` em diante, e passado idêntico para
  `<CarteiraScreen ctx={ctx}/>` e `<OpcoesScreen ctx={ctx}/>`, `App.jsx:9775-9780`).
  Isso resolve o compartilhamento de dado (D-03) SEM duplicar a chamada de
  rede — mas muda o TIMING do disparo: se o `useEffect` mantiver `[]` como
  dependência e o hook morar em `App()`, a chamada passa a disparar **em todo
  boot do app**, mesmo que o usuário nunca abra Posições nem Opções. Isso é
  uma mudança de comportamento real, não cosmética: `store.opcoesCuradoria()`
  aciona `_curadoria_top`/`_curadoria_scan_posicao` no backend, que varre
  cadeias de opção via `mydata_client` (orçamento `mydata_budget`, ADR-008) —
  "custo ZERO de IA e ZERO de serviço MCP" (comentário do backend,
  `server/app/main.py:3458-3459`) refere-se ao serviço MCP externo
  (`mcp.semente.dev`) e ao LLM, **não** ao orçamento do provedor de dados de
  mercado. A Fase 31 (D1) fixou um teto de 2 vencimentos por posição elegível
  exatamente por causa desse custo. Lifting ingênuo para `App()` aumenta a
  frequência de consumo desse orçamento para todo usuário que abre o app,
  independente de visitar as telas que mostram o resultado.
- **(b)** `CarteiraScreen` continua com seu próprio fetch (ou uma versão
  "leve"/cacheada) só para a contagem, e `OpcoesScreen` faz o fetch completo
  para a lista. Isso viola D-03 na letra ("nunca um número calculado à parte")
  se forem duas chamadas de rede independentes que podem divergir por
  timing (uma responde antes da outra, contagens diferentes por um instante)
  — mas seria tecnicamente "o mesmo dado" se ambas chamarem a mesma rota
  determinística. O risco aqui é sutil: não é o VALOR que diverge (a rota é
  determinística), é a POSSIBILIDADE de dois fetches redundantes gastarem o
  orçamento em dobro por sessão.

**Recomendação de pesquisa (não decisão travada):** opção (a) com um ajuste —
gatilhar o efeito por uma flag "visitou Posições ou Opções pelo menos uma vez
nesta sessão" em vez de `[]` puro, para preservar o comportamento atual de
"zero chamada para quem nunca abre nenhuma das duas telas" enquanto ainda
compartilha o mesmo estado entre as duas. Isto não está no CONTEXT.md e
**deve ser uma decisão explícita do planner**, não inferida em silêncio — ver
Open Questions.

## Navegação entre telas

`App()` mantém `const [tab, setTab] = useState("evolucao")`
(`App.jsx:8228`) e `const navigate = (t) => { setCarteiraView("main"); setPerfilView("hub"); setTab(t); }`
(`App.jsx:8231`). Trocar de aba é só `setTab`/`navigate(t)` — não existe
roteador de URL, não existe estado de "âncora" ou "seção" dentro do destino.
`OpcoesScreen` é montada com `{tab === "opcoes" && <OpcoesScreen ctx={ctx} />}`
(`App.jsx:9775`).

Boa notícia para D-02: `OpcoesScreen` **já abre "na lista"** por desenho —
`ticker` nasce `""` (`OpcoesScreen.jsx:303`, comentário explícito: "a aba não
abre vazia; ela abre sem ATIVO ESCOLHIDO... É o desenho aprovado: a aba abre
na lista, e entrar num ativo é um toque"). Ou seja, **não é preciso construir
nenhum mecanismo de navegação com destino/âncora** — `navigate("opcoes")` a
partir da nova linha de chamada em Posições já cumpre D-02 literalmente,
porque a aba Opções sempre abre mostrando a lista (vigias + o que quer que
vá para o topo por D-04), nunca um ticker pré-selecionado.

Ressalva: `abrirOpcoesDe(t)` (`App.jsx:4769-4776`), usado hoje pelos cliques
DENTRO de `OportunidadesOpcoes`/`CuradoriaEstruturas` para abrir o detalhe de
UMA posição em Posições (`setOpcoesFor(t)` + `scrollIntoView`), deixa de fazer
sentido para esses dois componentes quando eles saem de `CarteiraScreen` — o
scroll-to-id (`#posicao-`+t) só existe dentro de `CarteiraScreen`. Se
`CuradoriaEstruturas` se muda para `OpcoesScreen`, o botão "ver posição"
dentro do painel inline (`cp.curadoriaVerPosicao`, que hoje chama
`onAbrir(item.ticker)` → `abrirOpcoesDe`) precisa de um destino novo: dentro
da própria aba Opções, ir para a sub-aba Operar com aquele ticker selecionado
(equivalente a `escolherTicker(item.ticker)` + `setSubaba("operar")` em
`OpcoesScreen.jsx`), não mais um scroll em Posições. Isto é uma mudança de
comportamento pequena mas real que o planner precisa desenhar explicitamente.

## `SubAbaOperar` como destino (D-04) — gap encontrado

`SubAbaOperar` (`OpcoesScreen.jsx:1297-1396`) já recebe `carteira`, `ticker`,
`posicaoSelecionada`, `tecnico`, `cp`, `ctx`, `seletor` — confirma o CONTEXT.md.
Mas a leitura do corpo revela três coisas que o CONTEXT.md não menciona:

1. **Fetch próprio, redundante por desenho.** `SubAbaOperar` faz sua PRÓPRIA
   busca (`OpcoesScreen.jsx:1323-1337`, dois `useEffect` em cascata chamando
   `store.optionsGate(ticker)` e `store.optionsProposta(ticker, true)`) —
   ela **não reaproveita** `opcoesPorTicker` de `useOpcoesPropostas` (que é
   exclusivo de `CarteiraScreen` hoje). Isso já é intencional e testado:
   `test_opcoes_subabas_ui.mjs` regra 3 (linhas ~97-100) afirma
   `store.optionsGate(` e `store.optionsProposta(` aparecem **exatamente 1×**
   em `OpcoesScreen.jsx` inteiro — ou seja, o design atual está deliberadamente
   isolado (nenhuma busca duplicada DENTRO do arquivo), mas continua sendo uma
   segunda chamada de rede em relação ao que `CarteiraScreen` já buscou para
   o mesmo ticker, se a pessoa olhou a posição em Posições e depois foi para
   Operar. Mover `PropostaDaPosicao` para dentro de `OpcoesScreen` é o momento
   natural para resolver essa duplicação (reusar `opcoesPorTicker[ticker]` em
   vez de o fetch local), mas **não é exigido pelo CONTEXT.md** — é uma
   melhoria oportunista que o planner pode ou não decidir fazer.

2. **Suporte a multi-candidato está AUSENTE.** `SubAbaOperar` sempre renderiza
   `<PropostaLastreada r={prop} .../>` (linha 1379) — nunca lê `prop.candidatos`
   nem decide `multi = candidatos.length > 1` como `PropostaDaPosicao` faz
   hoje em `App.jsx:4468-4469`. A rota `/api/options/proposta/{ticker}` SEMPRE
   devolve `candidatos` (confirmado em `server/app/main.py:3253`,
   `"candidatos": resultado.get("candidatos", [])`), então o dado já chega —
   só não é usado. `test_opcoes_subabas_ui.mjs` regra 5/6 (linhas ~116-124)
   trava justamente que `SubAbaOperar` "não reimplementa o card" e "delega a
   PropostaLastreada" — essas regras precisarão de ATUALIZAÇÃO (não remoção)
   para permitir o ramo `CandidatoOpcao`/multi quando `PropostaDaPosicao`
   entrar de fato. **Sem essa atualização de lógica, mover só o JSX de
   `PropostaDaPosicao` para `SubAbaOperar` seria uma regressão silenciosa de
   MULTI-02** (carteira com posição de 2+ candidatos perderia a visão lado a
   lado que tem hoje em Posições).

3. **`posAberta` é replicado, não compartilhado.** `SubAbaOperar` recalcula
   `myOptionPositions`/`posAberta` localmente (linhas 1342-1345) com a MESMA
   lógica que `PropostaDaPosicao` calcula em `App.jsx:4473-4476` — duas
   implementações da mesma fórmula. Isso já existe hoje (não é introduzido
   por esta fase), mas se `PropostaDaPosicao` se move para dentro de
   `SubAbaOperar`, as duas versões colidem — o planner precisa escolher UMA.

## Cadeia de execução do collar curado (regressão mais provável)

Rastreada ponta a ponta:

1. Clique no card de `CuradoriaEstruturas` → `setAbertoId` (toggle inline,
   sem `onAbrir`) → painel expandido renderiza botão "executar" quando
   `operador` é true.
2. Botão chama `handleExecutar` (local a `CuradoriaEstruturas`,
   `App.jsx:4218-4232`) → `onExecutar(item, { aceitaLiquidezDificil })`.
3. `onExecutar` é injetado pelo call site como
   `(cand, o) => A.executarCandidatoCurado(cand, o)` (`App.jsx:4867`), onde
   `A` vem de `ctx.A` (o objeto de ações construído 1x em `App()`,
   `App.jsx:8667` em diante).
4. `A.executarCandidatoCurado` (`App.jsx:8949-8955`) chama
   `executarCandidato(cand, { store, aceitaLiquidezDificil })` —
   `executarCandidato` é importado de `web/src/opcoes/executarCandidato.js`,
   **um módulo puro sem estado, sem closure sobre `App.jsx`**: recebe `store`
   por parâmetro, devolve `{metodo, body}` e chama `store[metodo](body)`.
5. Para `tipo === "collar"`, o método resolvido é `optionsCuradoriaAbrirCollar`
   → `POST /api/options/curadoria/abrir-collar` (rota nova da quick
   `260915-ndt`, re-deriva pelo motor `opcoes_curadoria` via `idCandidato`).

**Achado importante: esta cadeia NÃO tem nenhuma dependência de ONDE
`CuradoriaEstruturas` é renderizada.** `ctx.A` já é passado idêntico para
`CarteiraScreen` e `OpcoesScreen` (ambos recebem `ctx={ctx}` da árvore de
`App()`). Mover `CuradoriaEstruturas` para `OpcoesScreen.jsx` e trocar o call
site de `onExecutar={(cand,o)=>A.executarCandidatoCurado(cand,o)}` para
`onExecutar={(cand,o)=>ctx.A.executarCandidatoCurado(cand,o)}` é a ÚNICA
mudança necessária nesta cadeia — `executarCandidato.js`, `persistence.js`,
`api.js` e a rota do backend continuam intocados. Isto reduz materialmente o
risco que o CONTEXT.md marcou como "a regressão mais provável desta fase": o
risco real está nos testes estáticos que verificam a cadeia por posição no
arquivo (`test_curadoria_ui.mjs` regras 14-25), não na cadeia em si.

## Guardiões de teste em risco

Confirmado por leitura completa ou por grep dirigido às âncoras estruturais.
Cada um destes precisa de **reescrita com nota datada**, não exclusão:

| Arquivo | O que trava hoje | Por que quebra com a mudança | Ação necessária |
|---|---|---|---|
| `web/tests/test_curadoria_ui.mjs` | 26 regras (chaves de copy, ordem de âncoras `function OportunidadesOpcoes < CuradoriaEstruturas < PropostaDaPosicao < useOpcoesPropostas < useCuradoria < CarteiraScreen < HistoricoScreen`, fatiamento de `App.jsx` por `indexOf` para isolar o corpo de `CuradoriaEstruturas`/`useCuradoria`/`CarteiraScreen`) | Se `CuradoriaEstruturas`/`useCuradoria` saem de `App.jsx`, `app.indexOf("function CuradoriaEstruturas")` devolve `-1`; `fatiaCuradoria`/`fatiaHookCur` viram fatias vazias ou lixo, e ~20 das 26 regras passam a testar string vazia (falso positivo silencioso) em vez de reprovar de verdade | Reescrever apontando para o novo arquivo (`OpcoesScreen.jsx` ou módulo novo); refazer o fatiamento por âncoras do novo local; preservar as 26 regras semanticamente (é a suíte mais densa desta feature) |
| `web/tests/test_carteira_opcoes_tira.mjs` | Âncoras `function OportunidadesOpcoes < PropostaDaPosicao < useOpcoesPropostas < CarteiraScreen < HistoricoScreen` dentro de `App.jsx`; asserções sobre `<OportunidadesOpcoes` aparecer depois de `function CarteiraScreen(` e antes da guarda de portfólio vazio | Mesma classe de quebra — todas as âncoras somem de `App.jsx` se o componente se move | Reescrever para o novo arquivo; a regra "PropostaDaPosicao NÃO referencia cp.tiraOpcoesSemCobertura" (isolamento de vazio agregado vs. vazio de card) precisa sobreviver à mudança |
| `web/tests/test_opcoes_multi_candidato_ui.mjs` | `CandidatoOpcao` precisa estar "ENTRE PropostaDaPosicao e useOpcoesPropostas" em `App.jsx`; ~15 regras sobre manchete verbatim, `typeof v === "number"`, `disabled={busy \|\| degradado}` | Âncoras quebram do mesmo jeito; e a regra 118-120 ("PropostaDaPosicao deriva multi de candidatos.length > 1", "continua renderizando PropostaLastreada no ramo único") precisa ser reconciliada com o gap real encontrado nesta pesquisa (SubAbaOperar não suporta multi hoje) | Reescrever apontando pro novo local; se o plano decidir NÃO portar suporte multi para `SubAbaOperar` nesta fase, este teste precisa de uma decisão explícita de escopo (regressão aceita ou tarefa obrigatória) |
| `web/tests/test_opcoes_collar_ui.mjs` | Handler de aceite já migrado para `PropostaLastreada.jsx` (Fase 28) — impacto PARCIAL: a parte 2 (varredura de `useEffect(` em `App.jsx` por `abrirCollar`) continua válida mesmo com a mudança, porque nenhum dos 4 blocos tem `useEffect` chamando `abrirCollar` diretamente | Baixo risco de quebra funcional; MAS a alusão "PropostaDaPosicao (detalhe dentro do card de Posições)" nos comentários fica desatualizada e deveria ganhar nota | Nota datada nos comentários; conferir se a contagem de handlers (hoje "exatamente 1") continua correta após a mudança |
| `web/tests/test_opcoes_proposta_ui.mjs` | Já testa `<PropostaLastreada` em `OpcoesScreen.jsx` (linha 98-100) — parcialmente preparado para este tipo de mudança | Baixo risco direto; mas se `PropostaDaPosicao` migrar e passar a envolver `<PropostaLastreada` DENTRO de `SubAbaOperar` num ramo condicional novo (single vs. multi), a asserção de "aparece 1x" pode precisar de ajuste | Conferir contagem de `<PropostaLastreada` em `OpcoesScreen.jsx` após a mudança |
| `web/tests/test_opcoes_subabas_ui.mjs` | Regra 3: `store.optionsGate(`/`store.optionsProposta(` aparecem EXATAMENTE 1× em `OpcoesScreen.jsx`; regra 5/6: `SubAbaOperar` "não reimplementa o card", "delega a PropostaLastreada", nunca chama `A.abrirLastreada`/`A.abrirCollar`/`A.fecharLastreada` direto | Se o plano decidir reusar `opcoesPorTicker` (de `useOpcoesPropostas` movido/lifted) em vez do fetch local de `SubAbaOperar`, a contagem de `store.optionsGate(`/`optionsProposta(` em `OpcoesScreen.jsx` muda (pode cair para 0 se o fetch subir para `App()`, ou continuar 1 se ficar em `OpcoesScreen`); se `CandidatoOpcao` entrar em `SubAbaOperar`, a regra "delega a PropostaLastreada" precisa aceitar também `<CandidatoOpcao` | Decidir a arquitetura de fetch ANTES de reescrever este teste — ele é o guardião que efetivamente força a decisão de "sem busca duplicada" |
| `web/tests/test_wiring_deps.mjs` | Guardião do wiring de dependências do objeto `A` em `App.jsx` (Fase 4) | Risco baixo/indireto — só quebra se `A.executarCandidatoCurado` ou outras entradas de `A` usadas pelos blocos móveis mudarem de assinatura | Conferir após a mudança; não requer reescrita a priori |
| `web/tests/test_vocabulario_opcoes.mjs` | Testa que toda `cp.X` referenciada em `OpcoesScreen.jsx` existe em `COPY.estudo`/`COPY.operador` | Deve **ajudar**, não quebrar — qualquer chave nova (ex.: a linha de chamada, se render dentro de `OpcoesScreen`) precisa satisfazer este teste automaticamente. Testar que a chave da NOVA linha de chamada (que fica em `CarteiraScreen`/`App.jsx`, não em `OpcoesScreen.jsx`) tem cobertura equivalente — hoje este arquivo só varre `OpcoesScreen.jsx` | Se a linha de chamada ficar em `App.jsx` (não em `OpcoesScreen.jsx`), este teste não a cobre — precisa de um teste irmão ou extensão de escopo |

**~90 arquivos adicionais `web/tests/*.mjs` fazem `readFileSync(App.jsx)`**
para guardar recortes NÃO relacionados a estes 4 blocos (paridade de
vocabulário geral, `test_wiring_deps.mjs`, testes de outras telas/features
inteiramente diferentes — Radar, Watchlist, Admin, etc.). Eles não têm
acoplamento estrutural à localização dos 4 blocos e devem passar inalterados;
a forma de verificar isso é rodar a suíte canônica completa
(`bash scripts/executar.sh --testes`), não auditar cada um manualmente.

## Texto de UI por modo (`copy.js`)

Confirmado: `COPY.estudo` (bloco em torno de `web/src/copy.js:585-620`) e
`COPY.operador` (bloco em torno de `web/src/copy.js:1140-1160`) já têm pares
simétricos para `tiraOpcoesTitulo`, `linhaPropostaNaPosicao`, `curadoriaTitulo`
e as demais chaves `curadoria*`/`tiraOpcoes*`. `test_curadoria_ui.mjs` já
demonstra o padrão de teste de PARIDADE DE CONJUNTO (não só lista fixa) via
`chavesCuradoriaDe(copy)` — filtra por prefixo e compara `JSON.stringify` dos
dois modos. A chave nova da linha de chamada em Posições (D-01) deve seguir
o mesmo padrão: nome com prefixo reconhecível (ex.: `linhaChamadaOpcoes*`),
presente nos dois modos, sem palavra de promessa/garantia (mesma lista
`PROIBIDAS` já usada em `test_curadoria_ui.mjs`: "garantido", "lucro
garantido", "sem risco", "certeza").

## Common Pitfalls

### Pitfall 1: mover o JSX sem mover o teste na mesma tarefa
**O que dá errado:** o componente funciona visualmente, a suíte "passa" porque
os testes quebrados falham de um jeito que parece não-relacionado (índice
`-1`, fatia vazia), e o defeito só aparece quando alguém lê o resultado linha
a linha.
**Como evitar:** cada task que move um bloco deve ter, no mesmo plano, a
task irmã de reescrever o(s) guardião(ões) daquele bloco especificamente —
listados na tabela acima.

### Pitfall 2: `useCuradoria()` subindo de tier sem gatilho condicional
**O que dá errado:** lifting ingênuo do hook para `App()` com `useEffect(…, [])`
transforma "busca só quando alguém abre Posições ou Opções" em "busca em todo
boot do app" — consumo adicional de orçamento do `mydata_budget` (Fase 31 D1)
para 100% dos usuários, mesmo os que nunca visitam essas duas telas.
**Como evitar:** gatilhar o efeito por uma flag de "primeira visita" a
qualquer uma das duas telas, não por mount de `App()`.

### Pitfall 3: `SubAbaOperar` ganhar `PropostaDaPosicao` sem suporte a multi-candidato
**O que dá errado:** carteiras com posição de 2+ candidatos (venda coberta E
put de proteção, por exemplo) perdem a visão lado a lado que têm hoje em
Posições — regressão silenciosa de MULTI-02, sem nenhum teste acusando,
porque `test_opcoes_subabas_ui.mjs` hoje testa exatamente o comportamento
single-candidate como CORRETO.
**Como evitar:** portar a lógica `multi = candidatos.length > 1` +
`CandidatoOpcao` para `SubAbaOperar` como parte explícita do plano, não como
efeito colateral de mover só o componente-pai.

### Pitfall 4: `abrirOpcoesDe`/scroll-to-id sobrevivendo fora de contexto
**O que dá errado:** o botão "ver posição" dentro do painel inline de
`CuradoriaEstruturas` (`cp.curadoriaVerPosicao`) chama `onAbrir(item.ticker)`
hoje ligado a `abrirOpcoesDe` (que faz `setOpcoesFor` + `scrollIntoView` num
elemento `#posicao-`+t que só existe em `CarteiraScreen`). Se o componente se
move sem trocar esse handler, o clique não faz nada (elemento não existe na
nova tela) ou lança erro silencioso (`if (!el) return;` engole o caso).
**Como evitar:** trocar o destino desse botão para `escolherTicker(item.ticker)`
+ `setSubaba("operar")` dentro de `OpcoesScreen`.

### Pitfall 5: duas implementações de `posAberta`/`myOptionPositions` colidindo
**O que dá errado:** `PropostaDaPosicao` (App.jsx) e `SubAbaOperar`
(OpcoesScreen.jsx) calculam a mesma coisa de formas ligeiramente diferentes
hoje (ambas corretas, mas duas fontes). Movidas para o mesmo arquivo, uma
das duas fica morta ou as duas competem no mesmo componente.
**Como evitar:** escolher uma implementação (recomendação: a de
`SubAbaOperar`, já adaptada ao formato "uma posição selecionada por vez" que
a sub-aba usa) e apagar a outra explicitamente, com nota.

## Don't Hand-Roll

| Problema | Não construir | Usar em vez disso | Por quê |
|---|---|---|---|
| Compartilhar `top`/`meta` da curadoria entre duas telas | Um segundo fetch independente em `OpcoesScreen` que "deveria" bater com o de Posições | Estado único, subido a `App()` (onde `ctx` já nasce compartilhado) e passado por prop/`ctx` às duas telas | Duas fontes da "mesma" verdade divergem na primeira race condition; `ctx` já é o padrão do repo para isso |
| Executar candidato de dentro do componente movido | `store.<metodo>(` ou `api.<metodo>(` direto dentro de `CuradoriaEstruturas`/`PropostaDaPosicao` no novo arquivo | `ctx.A.executarCandidatoCurado`/`ctx.A.abrirCollar`/`useAceiteLastreado` — já existem e já são a fonte única testada | `executarCandidato.js` e `useAceiteLastreado` já encapsulam a tradução candidato→corpo de rota; reimplementar seria a segunda cópia que o CLAUDE.md proíbe |
| Nova navegação com "âncora" para abrir Opções já numa oportunidade | Sistema de deep-link/query-param para pré-selecionar candidato | Nada — D-02 já decidiu que não há deep-link; `navigate("opcoes")` simples resolve, porque a aba já abre na lista por desenho | Construir mecanismo para um requisito que foi explicitamente descartado (D-02) seria trabalho fora de escopo |

## Runtime State Inventory

Não aplicável no sentido do gatilho padrão (rename/rebrand/migração de dado)
— esta fase move componentes de UI entre arquivos do MESMO app rodando, sem
renomear coleção, chave de kv, variável de ambiente ou serviço externo.
Verificação explícita, por categoria:

| Categoria | Achado |
|---|---|
| Dado armazenado | Nenhuma tabela/coleção/kv muda de nome ou de dono — os componentes movidos são puramente de apresentação, o dado vem das MESMAS rotas (`/api/options/curadoria`, `/api/options/proposta/*`, `/api/options/gate`) |
| Configuração de serviço vivo | Nenhuma — nenhuma integração externa (Railway, n8n, etc.) referencia nome de componente React |
| Estado registrado no SO | Nenhum |
| Segredos/env vars | Nenhum |
| Artefato de build | `server/web_dist` precisa ser regenerado e publicado (`scripts/bump.sh` + `publicar-web.sh`) depois do merge — mesma disciplina de toda fase que toca `web/src/` (ver Fase "sem plano de publicação front" na memória do projeto) — mas isso é publicação, não migração de estado |

## Environment Availability

Não aplicável — nenhuma dependência externa nova. Todas as rotas
(`/api/options/curadoria`, `/api/options/proposta/{ticker}`, `/api/options/gate`,
`/api/options/curadoria/abrir-collar`) já estão em produção desde as Fases
28/30/31 e a quick `260915-ndt`.

## Validation Architecture

Seção omitida — `.planning/config.json` tem `workflow.nyquist_validation: false`
explícito.

## Security Domain

`security_enforcement` não está declarado em `.planning/config.json` (default
= habilitado), mas esta fase não introduz superfície nova de autenticação,
autorização ou validação de input: nenhuma rota nova, nenhum campo novo
aceito do cliente. Os gates existentes (403 de Modo Estudo, RBAC, gate de
liquidez, `permitirOpcaoADescoberto`) permanecem no backend, inalterados —
mover onde o card aparece na UI não muda quem pode executar o quê. Categorias
ASVS aplicáveis: nenhuma nova; V5 (validação de input) continua coberta pelas
rotas já existentes e não testadas por esta fase.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `OportunidadesOpcoes`/`useOpcoesPropostas` não têm destino explícito em D-04 e podem precisar subir junto com `CuradoriaEstruturas` para o topo da aba (por analogia ao mandato D-05 de manter os dois motores visíveis lado a lado) | Open Questions #1 | Se o planner assumir silenciosamente que `OportunidadesOpcoes` simplesmente desaparece, D-05 ("os dois motores lado a lado, rotulados") fica sem um dos dois lados — o motor com gate técnico (`opcoes_lastreadas.propor()`) perderia toda superfície cross-posição visível |
| A2 | Subir `useCuradoria()` para `App()` com o efeito ainda gatilhado por "visita a Posições ou Opções" (não por boot) é a forma de resolver D-03 sem aumentar consumo do orçamento do mydata | Common Pitfalls #2, seção "O hook useCuradoria()" | Se o planner não decidir isso explicitamente, o caminho mais óbvio (mover `[]` como está para `App()`) aumenta silenciosamente o consumo de orçamento em produção |
| A3 | `SubAbaOperar` precisa ganhar suporte a `candidatos`/multi-candidato como parte desta fase, não como débito técnico aceito | Common Pitfalls #3 | Se aceito como débito técnico sem registro explícito, é uma regressão de MULTI-02 sem nenhum teste acusando — porque o teste atual (`test_opcoes_subabas_ui.mjs`) valida o comportamento single-candidate como CORRETO |

## Open Questions

1. **Qual é o destino de `OportunidadesOpcoes` (e do hook `useOpcoesPropostas`
   que a alimenta)?**
   - O que sabemos: o CONTEXT.md lista `OportunidadesOpcoes` entre os 4 blocos
     que SAEM de Posições (`<domain>`), mas D-04 (onde os blocos aterrissam)
     só nomeia explicitamente `CuradoriaEstruturas` (→ topo da aba) e
     `PropostaDaPosicao`/`PropostaLastreada` (→ sub-aba Operar).
     `OportunidadesOpcoes` não aparece em nenhum dos dois grupos.
   - O que não está claro: `OportunidadesOpcoes` representa o motor COM gate
     técnico (`opcoes_lastreadas.propor()`), enquanto `CuradoriaEstruturas`
     representa o motor SEM gate (`opcoes_curadoria`) — são exatamente os
     "dois motores lado a lado" que D-05 manda manter visíveis com rótulos
     que expliquem a diferença. Se `OportunidadesOpcoes` simplesmente for
     removida (não movida), D-05 fica com um motor só visível, o que
     contradiz a razão declarada de D-05 ("a contradição que hoje está
     escondida em telas separadas... passa a ficar visível lado a lado —
     isso é GANHO"). Mas também é possível que a intenção seja essa mesma
     remoção, e que `CuradoriaEstruturas` (que já cobre as 4 estruturas desde
     a Fase 31, incluindo call_coberta) simplesmente absorva o papel que
     `OportunidadesOpcoes` cumpria, deixando o "motor com gate" representado
     só dentro da sub-aba Operar (por posição, não cross-posição).
   - Recomendação: **o planner deve levar esta pergunta explicitamente ao
     Alex ou registrar a decisão com justificativa no PLAN.md**, em vez de
     escolher em silêncio — as duas leituras têm consequência de produto
     (visibilidade do motor com gate) e consequência técnica (se
     `useOpcoesPropostas` precisa mover/ser lifted junto, ou pode ser
     deletado com o componente).

2. **Onde exatamente o fetch de `useCuradoria()` deve morar após a mudança?**
   - O que sabemos: hoje mora em `CarteiraScreen`, dispara 1x por mount dessa
     tela. Precisa ser lido por Posições (para a contagem, D-03) e por
     Opções (para a lista completa, D-04).
   - O que não está claro: se deve subir para `App()` com gatilho condicional
     (ver Common Pitfalls #2), ficar em `OpcoesScreen` com Posições fazendo
     uma segunda leitura mais barata, ou alguma terceira forma (ex.: um
     contexto React dedicado).
   - Recomendação: decisão de arquitetura explícita no PLAN.md, com o
     tradeoff de custo (orçamento mydata) documentado — não uma escolha
     implícita dentro da task de "mover o componente".

3. **`SubAbaOperar` ganha suporte a multi-candidato nesta fase, ou isso é
   descoberto como fora de escopo?**
   - O que sabemos: o suporte não existe hoje (achado desta pesquisa); a
     casca (props) está pronta, a lógica não.
   - O que não está claro: se o CONTEXT.md considerou isso ao dizer "não
     precisa de props novas óbvias" — a frase é sobre PROPS, não sobre
     LÓGICA INTERNA, então tecnicamente não contradiz o achado, mas pode ter
     sido lida como "está pronto" por quem planejar rápido.
   - Recomendação: o plano deve declarar explicitamente se porta o suporte
     multi (recomendado, para não regredir MULTI-02) ou aceita a lacuna como
     débito técnico nomeado.

## Sources

### Primary (leitura direta do código, HIGH confidence)
- `web/src/App.jsx` (linhas citadas ao longo do documento) — componentes,
  hook, call sites, wiring de `ctx`/`A`, navegação (`tab`/`navigate`)
- `web/src/opcoes/OpcoesScreen.jsx` — `SubAbaOperar`, sub-abas, seletor,
  estrutura de render da aba
- `web/src/opcoes/PropostaLastreada.jsx` — módulo compartilhado (ADR-027
  Emenda 3), padrão de extração já aplicado
- `web/src/opcoes/executarCandidato.js` — despacho puro candidato→rota
- `server/app/main.py` (rotas `/api/options/curadoria`,
  `/api/options/proposta/{ticker}`, `/api/options/curadoria/abrir-collar`)
- `web/src/copy.js` — vocabulário por modo (`COPY.estudo`/`COPY.operador`)
- `web/tests/test_curadoria_ui.mjs`, `test_carteira_opcoes_tira.mjs`,
  `test_opcoes_multi_candidato_ui.mjs`, `test_opcoes_collar_ui.mjs`,
  `test_opcoes_proposta_ui.mjs`, `test_opcoes_subabas_ui.mjs`,
  `test_wiring_deps.mjs`, `test_vocabulario_opcoes.mjs` — leitura completa ou
  grep dirigido a cada assertiva estrutural relevante

### Secondary (contexto do projeto, MEDIUM confidence)
- `.planning/phases/32-.../32-CONTEXT.md` e `32-DISCUSSION-LOG.md`
- `.planning/phases/27-aba-opcoes-sobre-a-carteira/27-CONTEXT.md` (precedente
  D4 citado por D-04)
- `.planning/phases/31-varredura-oportunidades-opcoes/31-CONTEXT.md` (teto de
  vencimentos, custo de `mydata_budget`)
- `.planning/STATE.md` (histórico das Fases 27-31, quicks `260915-j5l`/`260915-ndt`)
- `./CLAUDE.md` (guardrails do repositório)

## Metadata

**Confidence breakdown:**
- Mapa de código (o que se move, de onde, para onde) — HIGH: lido linha a
  linha, não inferido.
- Guardiões de teste em risco — HIGH para os 6 arquivos citados
  (lidos/grepados diretamente); MEDIUM para a alegação de que os ~90
  restantes não são afetados (verificado por amostragem + raciocínio
  estrutural, não por leitura individual de cada um).
- Arquitetura de dado compartilhado (`useCuradoria`) — MEDIUM: o problema é
  real e a evidência é sólida (código lido), mas a solução recomendada é uma
  hipótese de design, não uma decisão travada — daí o Open Question.
- Gap de multi-candidato em `SubAbaOperar` — HIGH: confirmado por ausência
  literal de `candidatos`/`multi` no corpo do componente.

**Research date:** 2026-09-15
**Valid until:** próxima alteração de `App.jsx`/`OpcoesScreen.jsx` nesta área
(o CONTEXT.md já registra volatilidade alta — 2 quick tasks no mesmo dia
tocaram exatamente estes componentes). Recomenda-se replanejar se qualquer
quick task nova tocar `CuradoriaEstruturas`/`PropostaDaPosicao`/`SubAbaOperar`
antes da execução desta fase.
