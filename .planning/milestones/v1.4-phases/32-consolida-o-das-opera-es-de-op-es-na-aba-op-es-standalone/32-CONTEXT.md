# Phase 32: Consolidação das operações de opções na aba Opções - Context

**Gathered:** 2026-09-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Concentrar na **aba Opções** o conteúdo de operação com opções que hoje está
espalhado entre Posições e Opções, e deixar Posições com **uma única linha de
chamada** apontando para lá.

Esta fase **move e unifica** — não constrói tela nova. O destino já existe: a
aba Opções já tem sub-abas "Setups" e "Operar" (`OpcoesScreen.jsx:309`,
`1297`), e a sub-aba Operar já recebe `carteira`/`posicaoSelecionada`.

**O que sai de Posições** (`CarteiraScreen`, `web/src/App.jsx`):
- `OportunidadesOpcoes` (tira agregada, proposta única por posição) — `App.jsx:4852`
- `CuradoriaEstruturas` (as 4 melhores, Fases 30/31) — `App.jsx:4856`
- `PropostaDaPosicao` (acordeão "Estrutura de opções possível nesta posição") — `App.jsx:5008`
- `PropostaLastreada` / `CandidatoOpcao` dentro dele — `App.jsx:4498`, `4492`

**O que entra em Posições:** uma linha de chamada com contagem, que navega
para a aba Opções.

**Fora de escopo:** unificar os dois motores de proposta (`propor()` vs
`opcoes_curadoria`) — ver D-05; qualquer mudança em rota de execução ou no
motor determinístico; busca/filtro na aba Opções (ver D-06).
</domain>

<decisions>
## Implementation Decisions

### O que sobra em Posições

- **D-01:** Posições perde os QUATRO blocos de opções listados no
  `<domain>`. Fica **uma única linha de chamada**, discreta, com contagem —
  no espírito de `"3 oportunidades de opções nas suas posições →"`. Decisão
  literal do Alex (2026-09-15): *"só uma linha de chamada"*.

- **D-02:** Clicar nessa linha leva à **aba Opções, na lista de
  oportunidades** — não a uma oportunidade específica. A primeira formulação
  do Alex mencionou cair "já na oportunidade apresentada", mas isso
  pressupunha cards clicáveis em Posições; com a linha única não há card de
  origem, então o destino é a lista. Registrado explicitamente porque é a
  diferença entre as duas leituras que foram desambiguadas na discussão.

- **D-03:** A contagem da linha tem de vir do mesmo dado que alimenta a
  lista curada — **nunca** um número calculado à parte no front. Número que
  diverge do que a aba mostra é pior que não ter número (princípio 4 do
  `CLAUDE.md`: não inventar valor).

- **D-07:** `OportunidadesOpcoes` (o motor **COM** gate técnico,
  `opcoes_lastreadas.propor()`) vai para o **topo da aba Opções, ao lado da
  lista curada**, fora do seletor de ticker — não é deletada nem empurrada
  para dentro de Operar. `useOpcoesPropostas` move junto. Decisão do Alex
  (2026-09-15), tomada em resposta à Open Question #1 da `32-RESEARCH.md`:
  o `<domain>` listava `OportunidadesOpcoes` entre os quatro blocos que saem
  de Posições, mas o D-04 não lhe dava destino. Esta é a leitura que cumpre
  o D-05 ao pé da letra — os dois motores cross-posição ficam visíveis lado
  a lado, com rótulos que expliquem a diferença ("o que a leitura técnica
  endossa agora" × "o melhor da cadeia, endossado ou não"). Consequência
  aceita: o topo da aba passa a ter dois blocos cross-carteira mais os
  vigias, o que agrava a rolagem já registrada em D-06.

### Claude's Discretion

O Alex delegou explicitamente as três áreas restantes (2026-09-15: *"decide
o resto por mim"*), com estas recomendações fundamentadas já registradas.
São **decisões**, não sugestões — o planner pode executá-las; o Alex revisa
este arquivo antes de planejar se quiser mudar.

- **D-04 — Onde os blocos aterrissam:** a lista curada (`CuradoriaEstruturas`)
  vai para o **topo da aba Opções, fora do seletor de ticker**, junto dos
  vigias. Razão: a Fase 27 (D4) já aprovou exatamente esse padrão — *"Vigias
  antes da carteira. A lista de setups fica no topo, fora de qualquer
  ticker"*. Já existe precedente aprovado para um bloco de carteira inteira
  nessa tela; a curadoria é o mesmo formato (cross-posição) e não deve
  inventar um lugar novo. Os blocos **por posição** (`PropostaDaPosicao`,
  `PropostaLastreada`) vão para a sub-aba **"Operar"**, que já é a tela
  per-posição e já recebe os dados de que precisam.

- **D-05 — Os dois motores lado a lado:** manter os dois, **com rótulos que
  expliquem a diferença** — não unificar nesta fase. Razão: unificar os
  motores é mudança de produto com consequência regulatória (qual leitura
  vale, o que a tela afirma), não reorganização de tela; misturar isso com
  uma fase de consolidação de UI é como um bug vira dois. A contradição que
  hoje está escondida em telas separadas (e que causou o 409 da quick
  `260915-ndt`) passa a ficar visível lado a lado — isso é **ganho**, não
  defeito: expõe uma inconsistência real que o produto vai ter de resolver
  numa fase própria. O planner deve deixar claro na tela que um bloco é "o
  que a leitura técnica endossa agora" e o outro é "o que existe de melhor
  na cadeia, endossado ou não".

- **D-06 — Rolagem da aba cheia:** aceita e adiada. Sem busca, sem filtro,
  sem acordeão novo nesta fase. Razão: a Fase 27 já registrou isto como "Em
  aberto #2" (*"a aba não tem busca... acima de ~8 posições isso vira
  rolagem longa. Sem decisão; não inventar busca nesta fase, mas não
  desenhar nada que a impeça depois"*) — a mesma regra vale aqui. O planner
  não pode desenhar nada que **impeça** busca depois.

### Decisões delegadas que o PLAN.md tem de declarar por escrito

A `32-RESEARCH.md` levantou duas escolhas de arquitetura que caem sob a
delegação acima, mas que **não podem ser tomadas em silêncio dentro de uma
task de "mover o componente"** — cada uma vira uma decisão explícita e
justificada no PLAN.md:

- **Onde mora o fetch de `useCuradoria()`** (Open Question #2). Hoje dispara
  1× por mount de `CarteiraScreen`. Passa a ser lido por Posições (contagem,
  D-03) e por Opções (lista, D-04). Subir para `App()` sem gatilho
  condicional muda o timing para "todo boot do app" — e essa rota consome
  orçamento do `mydata_budget` (Fase 31 D1). O tradeoff de custo tem de
  estar escrito.
- **Suporte multi-candidato em `SubAbaOperar`** (Open Question #3). A
  pesquisa achou que `SubAbaOperar` (`OpcoesScreen.jsx:1297`) nunca lê
  `prop.candidatos` — sempre renderiza `PropostaLastreada` única. A casca
  (props) está pronta; a lógica não. Mover `PropostaDaPosicao` para lá sem
  portar essa lógica **regride MULTI-02 em silêncio**. O plano declara: ou
  porta o suporte (recomendado), ou nomeia a lacuna como débito com
  guardião.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Decisões de UI da aba Opções (precedente direto, não re-litigar)
- `.planning/phases/27-aba-opcoes-sobre-a-carteira/27-CONTEXT.md` §D3 — universo
  da aba = `positions` (carteira), não watchlist. Os dois lugares já falam dos
  mesmos ativos; é o que torna a consolidação barata.
- `.planning/phases/27-aba-opcoes-sobre-a-carteira/27-CONTEXT.md` §D4 —
  protótipo de UX **aprovado sem ressalvas**, fixa "vigias antes da carteira"
  (bloco de carteira inteira no topo, fora de qualquer ticker), régua de
  regime, custo declarado por controle, lastro livre no cartão. É o
  precedente que D-04 aplica.
- `.planning/phases/27-aba-opcoes-sobre-a-carteira/27-CONTEXT.md` §"Em aberto
  #2" — rolagem longa acima de ~8 posições, sem busca. Base de D-06.

### O que se move
- `.planning/phases/30-curadoria-ia-melhores-estruturas/` — origem da lista curada.
- `.planning/phases/31-varredura-oportunidades-opcoes/31-CONTEXT.md` — decisões
  D1-D9 da varredura (4 estruturas, 2 vencimentos, gate do a descoberto,
  fórmula única de ranking). A consolidação **não** pode alterar nenhuma.
- `.planning/quick/260915-j5l-corrigir-clique-nos-cards-da-lista-curad/260915-j5l-PLAN.md`
  — confirmação inline no card (o comportamento de clique que existe hoje).
- `.planning/quick/260915-ndt-re-derivar-execucao-de-candidato-curado-/260915-ndt-PLAN.md`
  — rota `POST /api/options/curadoria/abrir-collar` e o despacho por tipo em
  `executarCandidato.js`. **Precisa continuar funcionando de onde quer que o
  card passe a viver** — é a regressão mais provável desta fase.

### Guardrails do repositório
- `./CLAUDE.md` — princípios 1-11, paridade obrigatória `defaults.py` ↔
  `catalog.js` e `deviceStore` ↔ `serverStore`, manchete só do motor
  determinístico (CVM), guardiões de teste não se apagam.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `OpcoesScreen.jsx:1297` `SubAbaOperar` — já recebe `carteira`, `ticker`,
  `posicaoSelecionada`, `tecnico`, `cp`, `ctx`, `seletor`. É o destino
  natural dos blocos por posição (D-04); não precisa de props novas óbvias.
- `OpcoesScreen.jsx:667-692` — o componente de sub-abas já existe e é
  genérico o bastante para uma terceira, se o planner concluir que precisa
  (D-04 recomenda NÃO precisar).
- `web/src/opcoes/executarCandidato.js` — despacho por tipo já isolado num
  módulo puro; mover o card de tela **não** deve exigir tocá-lo.
- `CuradoriaEstruturas` (`App.jsx:4198`) — componente já autocontido, recebe
  tudo por prop (`top`, `meta`, `carregando`, `erro`, `onExecutar`,
  `operador`, `cp`, `palette`). Mover = mudar o call site, não reescrever.

### Established Patterns
- Bloco cross-carteira no topo da aba, fora do seletor de ticker — precedente
  aprovado na Fase 27 (vigias). D-04 segue ele.
- Vocabulário por modo vem de `copy.js` / `skill_ref.py`, nunca composto no
  componente. Texto novo (a linha de chamada) entra nos DOIS modos.
- Guardiões estáticos em `web/tests/*.mjs` inspecionam o source — mover um
  componente entre arquivos costuma quebrar guardião que referencia o arquivo
  de origem. Conferir `test_curadoria_ui.mjs`, `test_opcoes_collar_ui.mjs`,
  `test_opcoes_analisar_ui.mjs`.

### Integration Points
- `App.jsx` `CarteiraScreen` (~4852-5008) — de onde os quatro blocos saem.
- `App.jsx` → `OpcoesScreen` — como a aba recebe props hoje; a linha de
  chamada de Posições precisa de um jeito de navegar para lá (e, por D-02,
  só até a lista, sem selecionar oportunidade).
- `useCuradoria()` (`App.jsx:4687`) — o hook que alimenta a lista. Se a lista
  muda de tela, o hook muda de lugar junto; a contagem da linha de chamada
  (D-03) tem de sair **desse mesmo** dado.

</code_context>

<specifics>
## Specific Ideas

- Formulação do Alex para a linha de chamada, a ser refinada pelo texto final:
  algo como `"3 oportunidades de opções nas suas posições →"`. O importante é
  ter **contagem real** (D-03) e ser uma linha, não um card.
- Motivação declarada, em duas falas (2026-09-15): *"eu gostaria de deixar
  todo conteúdo em relação a opções na aba opções"* e *"Acho que as telas
  estão ficando muito poluídas"*. O critério de sucesso subjetivo é Posições
  ficar visivelmente mais limpa.

</specifics>

<deferred>
## Deferred Ideas

- **Unificar os dois motores de proposta** (`opcoes_lastreadas.propor()` com
  gate técnico × `opcoes_curadoria` sem gate) — fase própria. É decisão de
  produto com peso regulatório, não reorganização de tela. Esta fase só os
  coloca lado a lado com rótulos honestos (D-05). **Esta é a candidata mais
  forte a próxima fase depois da 32.**
- **Busca/filtro na aba Opções** para carteiras grandes — herdado como "Em
  aberto #2" da Fase 27, adiado de novo aqui (D-06).
- **Deep-link para uma oportunidade específica** — a primeira formulação do
  Alex pedia cair "já na oportunidade apresentada". Ficou fora por D-01/D-02
  (sem card de origem em Posições não há o que deep-linkar), mas volta a
  fazer sentido se um dia Posições voltar a exibir cards.

### Reviewed Todos (not folded)
- `medir-rate-limit-mydata.md` ("Medir rate-limit real do mydata antes de
  trocar fontes em produção") — deu match por palavra-chave (`real`,
  `mydata`, `produção`), mas é sobre fonte de dados, não sobre UI. Não
  incorporado.
- `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` ("Acompanhar aprovação
  do serviço MCP autenticado") — match por `mcp`/`opções`; é acompanhamento
  externo, sem relação com consolidação de tela. Não incorporado.

</deferred>

---

*Phase: 32-Consolidação das operações de opções na aba Opções*
*Context gathered: 2026-09-15*
