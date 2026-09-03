# ADR-025: Collar e estrutura multiperna — cinco decisões da Fase 16

**Status:** Aceito
**Data:** 2026-09-02
**Decisor:** Alex (autonomia concedida em `16-CONTEXT.md` para a decisão de
produto da Decisão 3 abaixo; as demais são decisões de implementação do
planner/executor dentro do escopo já aprovado no kickoff da milestone).
**Base:** ROADMAP v1.4 Fase 16; `16-CONTEXT.md`; `16-01-SUMMARY.md`;
`16-03-SUMMARY.md`; ADR-024 (limite `rastrear()`/`avaliar()`); ADR-004
(contrato de cadeia de opções).

---

## Contexto

A Fase 15 entregou o motor comum de N-pernas (`opcoes_motor.rastrear()`/
`avaliar()`, `opcoes_payoff.perfil_da_estrutura()`) mas nenhum consumidor de
produto. A Fase 16 tinha três tarefas: migrar as duas propostas existentes
(venda coberta, put de proteção) do motor single-leg antigo para o motor
comum (LIB-01/LIB-02), adicionar collar como terceira composição de duas
pernas sobre a mesma posição (LIB-03), e ligar tudo isso na rota HTTP que o
cliente já consome sem quebrar o cliente publicado hoje (Plano 16-04, este
ADR). Cinco decisões concretas nasceram desse trabalho — cada uma com um
racional que só fica visível olhando o diff real, não a descrição do
requisito.

## Decisão 1 — Perna de lastro no payoff, a preço de spot

Toda estrutura avaliada por `opcoes_motor.avaliar(pernas)` inclui a perna
ACAO (`opcoes_motor.perna_de_acao(underlying, spot, quantidade=1)`), ao
preço CORRENTE do papel (`spot`), nunca ao preço médio da posição
(`server/app/opcoes_lastreadas.py`, comentário em `propor()`: "A perna ACAO
entra SEMPRE no cálculo de risco").

**Alternativas descartadas:**
- **Sem a perna ACAO no payoff:** uma venda coberta apareceria como perda
  ilimitada — `perfil_da_estrutura` vê só a call vendida (inclinação -1) e
  classifica o risco errado para um produto que existe para ensinar risco
  corretamente.
- **Perna ACAO ao preço MÉDIO da posição:** o ganho máximo absorveria o
  lucro não realizado da posição já aberta, e a MESMA proposta de opção
  pareceria melhor ou pior dependendo de quando o usuário comprou a ação —
  informação que não tem nada a ver com a estrutura sendo montada agora.

**Consequência:** `estrutura["custo_liquido"]` inclui o preço da ação (numa
venda coberta, spot - prêmio ≈ valor da ação menos o prêmio recebido) — por
isso existe o campo `caixa`, calculado separadamente com `avaliar()` chamado
SÓ sobre a(s) perna(s) de opção. `caixa` responde "quanto dinheiro muda de
mãos hoje"; `estrutura` responde "qual o perfil de risco completo".
Misturar as duas perguntas num único número teria sido o bug mais fácil de
introduzir aqui.

## Decisão 2 — Régua única de seleção

`opcoes_lastreadas.propor()` não escolhe mais contrato por conta própria:
delega inteiramente a `opcoes_motor.rastrear(cadeia, filtros)`, a mesma
função que qualquer composição futura vai usar. As funções locais
`_escolher_contrato`/`_candidato_valido`/`_LIQUIDEZ_MINIMA` que existiam
desde a Fase 14 foram apagadas (16-01-SUMMARY.md), não mantidas como
wrapper fino — a segunda opção teria deixado duas implementações da mesma
régua no arquivo, exatamente o que esta migração existe para eliminar.

**Alternativa descartada:** manter `_escolher_contrato` como wrapper fino
sobre `rastrear()`. Rejeitada porque o corpo da função já era idêntico ao
de `rastrear()` — um wrapper sem lógica própria é só um nome a mais para
manter sincronizado.

**Consequência conhecida e aceita:** o desempate de strike EMPATADO mudou.
`max(candidatos, key=strike)` (implementação anterior) devolvia o PRIMEIRO
strike máximo na ordem da cadeia; `rastrear(criterio="max")` ordena
ascendente e devolve o ÚLTIMO empatado (`list(reversed(sorted))[:n]`,
`opcoes_motor.py`). Documentado em comentário no código e travado por teste
(`test_propor_put_empate_de_strike_devolve_ultimo_da_ordem`,
16-01-SUMMARY.md). Cadeia real da B3 não repete strike no mesmo tipo e
vencimento — divergência sem efeito prático em produção, mas testada por
disciplina, não por necessidade observada.

## Decisão 3 — Quando o collar é oferecido

**Decisão de PRODUTO, tomada com autonomia concedida nesta milestone,
marcada como reversível** (`16-CONTEXT.md`, seção "LIB-03"): o collar é
oferecido exatamente quando `decisao == VENDER` (a leitura técnica já pede
proteção) **e** a put de proteção isolada seria rejeitada por
`caixa_insuficiente` (`contratos < 1` após o corte por caixa disponível,
`opcoes_lastreadas.py`, ramo `put_protecao`).

**Racional:** o collar financia a proteção com o prêmio da call vendida —
faz sentido oferecê-lo exatamente onde a put pura já não cabe no caixa
disponível, em vez de só devolver "caixa insuficiente" sem alternativa
nenhuma.

**Gatilho alternativo descartado:** oferecer o collar sempre que
`decisao == VENDER`, independente de a put isolada caber no caixa —
descartado porque, quando a put isolada já cabe, o collar não tem
vantagem clara sobre ela (o collar troca upside da ação por proteção mais
barata; sem a restrição de caixa, não há razão de produto para forçar essa
troca no usuário). Restringir a oferta ao caso em que a alternativa mais
simples (put isolada) já falhou mantém o motor oferecendo a estrutura mais
simples que resolve o problema, escalando para a mais complexa só quando
necessário.

**O que faria revisitar a regra:** uso real na Fase 17/18 mostrando que o
gatilho por `caixa_insuficiente` não captura os casos que fariam sentido
para o usuário (por exemplo, usuários que prefeririam collar mesmo com
caixa suficiente para a put isolada, por razões de custo de oportunidade).
Reverter é mexer só na condição `if multiperna` dentro do ramo
`put_protecao` de `propor()` — nunca no motor comum (`opcoes_motor`/
`opcoes_payoff`), que continua agnóstico a quando cada estrutura é
oferecida.

## Decisão 4 — O collar não tem contrato único

No dict de proposta devolvido por `_propor_collar`, os campos
`contractSymbol`, `optionType`, `strike`, `premioUnitario` e `premioTotal`
são explicitamente `None`. As duas pernas nomeadas vivem em
`pernasContratos` (lista de 2 dicts, cada um com seu próprio
`contractSymbol`/`optionType`/`strike`/`lado`/`premioUnitario`), e o
dinheiro que muda de mãos hoje vive em `caixa`.

**Alternativa descartada:** preencher `contractSymbol`/`strike`/
`premioTotal` com o valor de UMA das duas pernas (por exemplo, a call
vendida, espelhando o formato de `call_coberta`). Descartada porque
qualquer consumidor que case proposta com posição por `contractSymbol`
único — que é exatamente o que o cliente publicado hoje faz
(`web/src/App.jsx:3216-3217`, `myOptionPositions.find(p => p.id ===
opProposta.proposta.contractSymbol)`) — trataria uma estrutura de DUAS
pernas como se fosse uma operação de UMA perna. Isso não é uma
simplificação inofensiva: é uma estrutura de dados mentindo sobre sua
própria forma para o único consumidor que existe.

**Aplicação da regra "null nunca 0.0":** este é um caso de ESTRUTURA (o
campo não se aplica a este tipo de proposta), não de DADO FALTANTE (o
campo se aplica mas o valor não pôde ser calculado) — a mesma disciplina do
resto do repositório (`server/app/db.py`, campos nullable), estendida a um
caso novo: quando um campo não faz sentido para o tipo de proposta, `None`
é o valor correto, e o dado real mora em outro lugar do dict
(`pernasContratos`/`caixa`), nunca escondido atrás de um valor sentinela
como `0.0`.

## Decisão 5 — Negociação de capacidade `multiperna` + trava de execução

Duas peças, uma decisão: `GET /api/options/proposta/{ticker}` ganhou o
parâmetro de query tipado `multiperna: bool = False`
(`server/app/main.py`, Plano 16-04), repassado a
`opcoes_lastreadas.propor(..., multiperna=multiperna)`; e
`POST /api/options/lastreada/abrir` ganhou uma trava de servidor que
recusa com 400 nomeado ("Estrutura de mais de uma perna não é executada
por esta rota.") qualquer corpo com `tipo == "collar"` OU
`pernasContratos`/`pernas` de mais de um item.

**Por que o cliente publicado não recebe estrutura de duas pernas sem
pedir:** `PropostaLastreada` (`web/src/App.jsx:3010-3065`) e o casamento
proposta-posição por `contractSymbol` único (`App.jsx:3216-3217`) são o
ÚNICO consumidor real desta rota hoje. Esse componente lê `p.optionType`
para decidir `isCall` (chip visual) e `p.contratos`/`p.strike`/
`p.premioTotal` para montar o texto do botão de CTA. Com
`contractSymbol`/`optionType` nulos (Decisão 4), o componente não quebra
com exceção — mas o botão "Abrir" que ele renderiza chamaria
`POST /api/options/lastreada/abrir` com um corpo que representa DUAS pernas
como se fosse UMA, porque o componente nunca foi desenhado para renderizar
`pernasContratos`. Sem a negociação de capacidade, o gatilho de
`caixa_insuficiente` (Decisão 3) faria o collar aparecer para TODO usuário
nesse cenário, silenciosamente — não é um bug hipotético, é o comportamento
garantido do gatilho já implementado.

**Por que a trava é do servidor, não só da UI:** mesma disciplina do 403 de
Modo Estudo (T-14-23, `options_lastreada_abrir`) — a UI pode ter bug, pode
ser modificada por um cliente que não é o app publicado, ou pode
simplesmente não ter sido atualizada ainda para a capacidade nova. Confiar
só na UI para nunca postar um corpo de duas pernas é a mesma classe de erro
que motivou o 403 explícito de Modo Estudo em vez de confiar só no botão
escondido. `T-16-13` no threat model do Plano 16-04 formaliza isso como
elevação de privilégio mitigada.

**Alternativa descartada:** não adicionar o parâmetro `multiperna` e
simplesmente NUNCA propor collar até a Fase 17 estar pronta. Descartada
porque o motor de collar (`_propor_collar`, Plano 16-03) já estava completo
e testado — atrasar sua exposição pela rota até a Fase 17 teria adiado
LIB-03 sem necessidade técnica real, só para evitar desenhar a negociação
de capacidade que este ADR documenta. A negociação de capacidade é mais
barata que segurar a feature inteira.

**O que a Fase 17 precisa fazer para ligar:** (1) declarar a capacidade
passando `multiperna=1`/`true` na chamada de `GET
/api/options/proposta/{ticker}` a partir de um cliente que sabe renderizar
`pernasContratos`; (2) desenhar um caminho de execução de N pernas sobre
`server/app/store.py` (hoje só existem `abrir_call_coberta` e
`comprar_put_protecao`, uma perna cada) e então relaxar ou substituir a
trava de `options_lastreada_abrir` para aceitar corpos de collar
legítimos vindos de um cliente que declarou a capacidade.

**Explícito:** `multiperna` NÃO é uma feature flag de entrega parcial. O
collar está COMPLETO no motor (`opcoes_lastreadas.propor`) e ACESSÍVEL pela
rota (`GET /api/options/proposta/{ticker}?multiperna=1`) desde este plano —
o parâmetro descreve exclusivamente o que o CLIENTE sabe renderizar e
executar, não o que o SERVIDOR sabe calcular.

## Limitação conhecida — guarda por autoidentificação, não re-derivação

A trava de `options_lastreada_abrir` confia nos campos `tipo`/
`pernasContratos` que o próprio corpo da requisição declara — ela NÃO
re-deriva a partir da cadeia de opções se o `contractSymbol` postado faz
parte de uma estrutura de N pernas que o servidor já propôs. Isso é
aceitável no escopo desta fase porque nenhum código de front deste
repositório monta ou envia um corpo de múltiplas pernas — o único caminho
que produz um corpo assim é um cliente escrito deliberadamente para tentar,
e a trava (Decisão 5) já recusa esse corpo antes de qualquer escrita,
independente do `tipo` declarado ser honesto. Torna-se um item de
hardening real a partir do momento em que a Fase 17 construir um cliente
que negocia `multiperna=1` de verdade — nesse ponto, a rota de abertura
precisa decidir de forma mais robusta (por exemplo, re-consultando a
proposta original ou validando o conjunto de `contractSymbol`s contra uma
estrutura conhecida) em vez de confiar apenas no que o cliente afirma sobre
sua própria requisição.

> **Nota (2026-09-03, Plano 17-03):** esta limitação foi fechada pelo
> ADR-026 — `POST /api/options/lastreada/abrir-collar` re-deriva a proposta
> no servidor (`opcoes_lastreadas.propor(..., multiperna=True)`) a cada
> aceite e cruza os `contractSymbol`/`lado` submetidos contra essa proposta
> fresca, em vez de confiar no que o corpo declara.

## Consequências

**Fica mais fácil:**
- A Fase 17 recebe collar, venda coberta e put de proteção no MESMO
  vocabulário de proposta (`estrutura`/`caixa`/`precoObjeto`/
  `pernasContratos`), pronto para exibir sem reconstrução.
- O cliente publicado hoje não precisa de NENHUMA mudança para continuar
  funcionando exatamente como antes — a negociação de capacidade é
  aditiva por desenho.

**Fica mais difícil / o que se paga:**
- A guarda de execução (Decisão 5, limitação acima) é mais fraca do que
  seria uma re-derivação server-side — aceito conscientemente para esta
  fase, não esquecido.
- `propor()` cresceu um parâmetro somente-nomeado e um desvio condicional
  interno (`_propor_collar`) em vez de virar um dispatcher de três funções
  — mais simples de ler hoje, mas se uma quarta estrutura for adicionada no
  futuro, vale reavaliar se o desvio condicional ainda é a forma certa ou
  se o dispatcher passa a valer o custo.

**A revisitar:**
- Decisão 3 (quando propor collar) explicitamente marcada como reversível
  a partir de uso real nas Fases 17/18.
- A limitação de guarda por autoidentificação (acima) precisa virar
  hardening real no momento em que a Fase 17 ligar um cliente de verdade.

---
*Fase: 16-biblioteca-de-estruturas*
*ADR: 025*
