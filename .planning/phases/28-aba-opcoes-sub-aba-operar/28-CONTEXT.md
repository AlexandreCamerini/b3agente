# Fase 28 — Sub-aba "Operar" e extração de `PropostaLastreada` · CONTEXT

> Consolidado por Claude a partir do pedido do Alex de 2026-09-13 (prompt de
> execução para levar TODA a operação de opções — hoje espalhada entre o card
> do ativo em Watchlist/Radar e a aba Opções — para dentro da aba, em duas
> sub-abas). **Este CONTEXT substitui a rodada de `/gsd-discuss-phase`
> assistida por subagente**: o pedido já veio com decisões e guardrails
> explícitos, e a leitura de código abaixo foi feita diretamente (grep/Read),
> sem despachar `gsd-assumptions-analyzer`/`gsd-advisor-researcher` — critério
> de orçamento do próprio pedido ("prefira leitura direta a despachar um
> agente de exploração para redescobrir o que este prompt já aponta"). Onde
> uma decisão de produto não estava no pedido original, ela foi FECHADA como
> premissa de trabalho (reversível, declarada, corrigível a custo baixo) na
> seção "Decisões assumidas" abaixo — não presumir nada além do que está
> escrito ali.

## Por que esta fase existe (motivação, não sintoma isolado)

O pedido maior do Alex (trazer toda operação de opções para a aba, com duas
sub-abas "Setups"/"Operar", payoff sempre numérico, sem duplicar código, e
depois — em fase futura — curadoria de IA sobre as 4 melhores estruturas) é
grande demais para uma fase só. Esta é a **fundação**: sem ela, as fases
seguintes (opção a descoberto com flag, curadoria de IA) não têm onde morar,
porque a sub-aba "Operar" ainda não existe.

## O que já existe e o que este pedido está pedindo para MOVER, não recriar

Verificado por leitura direta em 2026-09-13, arquivo:linha:

1. **O card de proposta lastreada já existe e já funciona.**
   `PropostaLastreada` (`App.jsx:3314-3424`) renderiza venda coberta, put de
   proteção e collar — manchete do motor determinístico, payoff **numérico**
   (ganho máximo/perda máxima/breakevens, `App.jsx:3361-3392`), CTA de
   abrir/fechar (`App.jsx:3402-3419`). É usado em DOIS pontos: dentro do
   `AtivoCard` (Watchlist/Radar, `App.jsx:3799`) e dentro de
   `OportunidadesOpcoes` (tira "Oportunidades de opções" em Posições, Fase 18,
   `App.jsx:4416`). **Payoff numérico (pedido #4 do Alex) já é verdade hoje**
   — não é feature nova, é o que este componente já faz.
2. **A aba Opções (`OpcoesScreen.jsx`) não importa nada de `App.jsx`, de
   propósito** (ADR-027, Decisão 3 — isolamento do núcleo). É por isso que
   "trazer as operações para dentro da aba, sem duplicar código" **não** é
   copiar/colar: exige extrair `PropostaLastreada` (+ os dois componentes que
   ela usa, `FonteDoDadoProposta` e `ChipDaProposta`, `App.jsx:3272-3305`)
   para um módulo em `web/src/opcoes/` que os DOIS lados importam — nem
   `App.jsx` importa de `OpcoesScreen.jsx`, nem o contrário. Mesma técnica das
   Emendas 1 e 2 do ADR-027, aplicada a componente de UI em vez de dado.
   **Isto exige Emenda 3 ao ADR-027**, registrada nesta fase.
3. **Existe uma SEGUNDA implementação de payoff numérico**, independente da
   de `PropostaLastreada`: `PayoffChart.jsx` (`web/src/opcoes/PayoffChart.jsx`),
   usado no caminho MCP (`/possibilidades`) dentro da própria
   `OpcoesScreen.jsx`. As duas mostram ganho máximo/perda máxima/breakevens,
   nenhuma reusa a outra. Esta fase NÃO unifica as duas (são fontes de dado
   diferentes — motor interno × serviço MCP, mesma distinção que a Emenda 2
   já aceitou por escrito para a leitura técnica) — só evita que a extração
   crie uma TERCEIRA.
4. **A aba Opções hoje é uma tela linear, sem sub-abas.** `OpcoesScreen.jsx`
   (`export default function OpcoesScreen`, `:270`) é uma cascata única:
   lista de posições → bloco "Seus vigias" → escolher ativo → leitura interna
   → leitura do serviço → cadeia/possibilidades → criar setup. As duas
   sub-abas do pedido ("Setups"/"Operar") são uma mudança estrutural real, não
   cosmética — e é também a resposta mais direta ao pedido #5 (a aba está
   confusa, informação demais): dividir a tela em dois modos de uso
   (monitorar × decidir/executar) é simplificação de verdade, não polimento.
5. **`ctx.data.positions` já é a fonte de universo da aba** (Fase 27, D3) —
   a sub-aba "Operar" reusa a MESMA fonte, sem chamada nova.

## Decisões herdadas do pedido (não re-litigar)

- **Universo de "Operar" = carteira**, mesma régua da Fase 27 (D3) — nunca
  watchlist.
- **Guardrail não-negociável**: nada nesta fase aproxima a IA de calcular ou
  escolher estrutura. A manchete de cada proposta continua vindo do motor
  determinístico (`opcoes_lastreadas.propor()`/`opcoes_motor.avaliar()`) —
  princípio 5 do `CLAUDE.md`, já em produção em `PropostaLastreada`. Esta fase
  não muda o motor, só onde o resultado dele é renderizado.
- **Lastro obrigatório por padrão é invariante.** Nada nesta fase abre
  caminho de operação a descoberto — isso é a Fase 29, com o flag opt-in
  ainda por construir (não existe hoje em lugar nenhum do código, confirmado
  por grep vazio em `naked`/`a_descoberto`/`permitirNaked`).
- **Fora de escopo, explícito**: opção a seco (Fase 29), curadoria de IA das
  4 melhores estruturas (Fase 30), polish de UX pós-uso real (Fase 31).

## Decisões assumidas (premissa declarada, não confirmada em texto pelo Alex)

Nenhuma das três é irreversível — trocar import de componente, nome de aba
ou gesto de navegação não têm custo de deploy ou de dado. Por isso, seguindo
o protocolo do CLAUDE.md ("não pare por ambiguidade secundária: assuma o
razoável, declare a premissa e siga"), as três ficam FECHADAS como premissa
de trabalho para o plano de execução. Se alguma estiver errada, corrigir
custa uma linha de plano, não uma rodada de `/gsd-plan-phase`.

### D1 — O card de proposta em Watchlist/Radar SOME; a tira em Posições FICA

Hoje `PropostaLastreada` aparece em TRÊS lugares depois da extração ser só
"mudar de onde o componente é importado": `AtivoCard` (Watchlist/Radar,
`App.jsx:3799`), `OportunidadesOpcoes` em Posições (`App.jsx:4416`) e a nova
sub-aba Operar. Manter os três seria a duplicação de EXPERIÊNCIA que o
pedido #3 pede para reduzir (o código deixa de duplicar, a navegação continua
duplicada).

**Decisão: o card dentro de `AtivoCard` (Watchlist/Radar) é removido — a
proposta lastreada de um ativo passa a viver só na sub-aba Operar.** A tira
`OportunidadesOpcoes` em Posições **permanece intocada** — motivo de produto
diferente, não é a mesma dúvida: ela é descoberta de proposta ativa sem abrir
a aba Opções (Fase 18/NAV-01), aponta para a POSIÇÃO, não para a aba, e não
duplica renderização — hoje ela deliberadamente NÃO usa `PropostaLastreada`
(`App.jsx:4426-4427`, comentário do próprio código: "NÃO renderiza o
componente PropostaLastreada de propósito"). Nada nesta fase muda isso.

### D2 — Corte da sub-aba "Setups": tudo que a Fase 27 já entrega, sem redução

**Decisão: "Setups" = a `OpcoesScreen` de hoje, inteira** (lista de
posições, bloco "Seus vigias", leitura interna/técnica, cadeia/possibilidades
do serviço, criar/desativar setup) — nada sai dela nesta fase. "Operar" é
**aditiva**, não um recorte da primeira: reusa a mesma lista de posições e a
mesma leitura técnica (é a mesma decisão de já ter os dois, custo zero,
disponíveis para quem vai decidir), e acrescenta a proposta lastreada
(abrir/fechar venda coberta/put/collar) que hoje só existe fora da aba.
Motivo de não recortar: leitura técnica e cadeia são a evidência que
sustenta a decisão de operar — tirá-las de "Operar" forçaria ida e volta
entre as duas sub-abas para decidir uma coisa só.

### D3 — Dentro de "Operar": lista → clique → proposta (mesmo gesto de "Setups")

**Decisão: (a) lista de posições → clicar numa → ver a proposta lastreada
daquela posição** — mesmo gesto que "Setups" já usa para vigias/leitura
técnica (Fase 27, D3), em vez de uma tira no topo estilo
`OportunidadesOpcoes`. Consistência de gesto dentro da mesma aba pesa mais
que a conveniência de ver tudo de uma vez — que já existe em Posições
(D1 acima) e não precisa ser reinventada aqui.

## Guardrails (herdados, não re-litigar)

- **Brand Book v2** travado por `web/tests/test_brand_book_v2_tokens.mjs` —
  nenhuma cor, escala de tipo ou token novo.
- **Paridade obrigatória** `deviceStore` ↔ `serverStore` em
  `web/src/persistence.js` — nenhum método novo é esperado nesta fase (a
  extração é só de componente React, não de chamada de API), mas se algo
  novo entrar, paridade nos DOIS.
- **Princípio 5 do CLAUDE.md**: manchete, payoff e execução continuam
  determinísticos — a IA não entra nesta fase em lugar nenhum.
- **ADR-027 §3.3**: custo de MCP só em clique explícito. A extração não move
  nenhuma chamada de `useEffect` — só move componente de apresentação.
- **Guardiões de teste não se apagam** — reversão deliberada atualiza com
  nota datada.
- **Suíte canônica**: `bash scripts/executar.sh --testes`, fora do sandbox.
  Front editado → `npx vite build` antes de declarar ok.
- **Publicação**: fora de escopo desta fase (fica testada, não vai ao ar sem
  passo humano separado — lição de `fase-sem-plano-de-publicacao-front`).
