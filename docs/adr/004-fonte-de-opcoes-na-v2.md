# ADR-004: Fonte de opções na v2 — o que o app pode simular com dado degradado

**Status:** Aceito
**Data:** 2026-08-04
**Decisor:** Alex
**Base:** [`docs/v2-opcoes-proposta.md`](../v2-opcoes-proposta.md) §4, memória
`opcoes-b3-fonte-de-dados`, [`OPTIONS-GUARDRAILS.md`](../../OPTIONS-GUARDRAILS.md).

---

## Contexto

`server/app/options_provider_yahoo.py` é hoje a única fonte de cadeia de
opções — endpoint não-oficial do Yahoo, que falha com frequência para B3
(401/403/429) e, quando falha, retorna `providerStatus: "degraded"` com um
`warning` explícito, nunca inventa dado (postura já estabelecida no módulo
depois do incidente do 401).

Em 2026-08-04, ficou decidido (memória `opcoes-b3-fonte-de-dados`, relayed
para a sessão do MyData) que o MyData aceita brapi como fonte de opções de
terceiro, nunca como origem — mas **nada disso está implementado em nenhum
dos dois lados**: sem chave gerada, sem cliente `mydata_client.py` no
b3-agente. A v2 não pode depender de uma integração que não existe.

**A pergunta que o checkout anterior não fez**, levantada nesta rodada: o
produto pode **simular execução** — registrar uma compra em
`optionPositions` — a um preço que o próprio sistema rotula como
`providerStatus: "degraded"`? Ler uma cadeia degradada pra *mostrar* é
honesto (o usuário vê o warning); preencher `avg` de uma posição simulada
com esse número vira P&L falso no histórico de um usuário real, sem que ele
tenha sido avisado no momento da decisão que importa — a de comprar.

---

## Decisão

**Ler é permitido sempre; simular execução (comprar) é bloqueado quando
`providerStatus != "ok"`.**

A camada de opções no card (§2 da proposta) pode exibir uma cadeia
degradada — é o mesmo padrão que o Estudo/Radar já usam para outros dados
intermitentes: mostrar com o aviso, nunca esconder. Mas o botão de comprar
(escopo já travado: só compra a seco de call/put) fica desabilitado com uma
mensagem descritiva ("cotação de opções indisponível no momento — tente
novamente") quando o payload do provider vier com `providerStatus:
"degraded"`. O `avg` de uma posição simulada só é preenchido com preço que o
próprio sistema classificou como confiável no momento da compra.

**Gatilho declarado para acionar o MyData/brapi como fonte primária** (sem
isso, "trocar de fonte depois" é conversa, não plano): taxa de
`providerStatus: "degraded"` acima de **20% das aberturas da cadeia em uma
semana corrida**, medida pela mesma instrumentação de uso que já existe para
IA (`/api/obs/usage`, ADR-001 Decisão 5) — este ADR estende esse contador
para o fetch de opções. Acima do gatilho, a decisão volta ao Alex com
número, não com impressão, e a prioridade do cliente MyData sobe.

**Por que 20% e não outro número:** é o mesmo espírito do gatilho de 2% do
ADR-001 (Decisão 1), escalado pela natureza mais frágil do endpoint de
opções (que já falha "com frequência" por descrição própria do módulo,
diferente do endpoint de cotação/candle que sustentou 1.566 requisições sem
erro). Um piso mais baixo dispararia o alarme quase sempre; este ADR não tem
medição própria como o ADR-001 teve — é estimativa consciente, a revisitar
com instrumentação real.

### Opções consideradas

| | Bloquear compra em degradado (escolhida) | Permitir sempre, só avisar | Esperar o MyData antes de lançar v2 |
|---|---|---|---|
| Risco de P&L falso no histórico | Eliminado no momento da compra | Existe — usuário decide sob aviso, mas o histórico fica sujo | Eliminado |
| Data de entrega da v2 | Não bloqueada pelo MyData | Não bloqueada | Bloqueada por um item fora deste repo, sem ETA |
| Consistência com `OPTIONS-GUARDRAILS.md` | Direta — "nunca inventar cadeia" se estende a "nunca simular execução sobre cadeia inventada/não confiável" | Tensiona a guardrail | Direta |

Esperar o MyData foi descartada porque a implementação vive em outro
projeto, sem cronograma sob controle deste — travar a v2 nisso reabriria a
mesma dependência cruzada que a Fase 0 do checkout já mapeou como risco.

---

## Consequências

**Fica mais fácil**
- Trocar Yahoo por MyData/brapi quando existir: é configuração no provider,
  não mudança na regra de bloqueio (que olha `providerStatus`, não a fonte).
- O histórico de operações de opção nunca carrega preço que o próprio
  sistema não confiava.

**Fica mais difícil**
- Em dias de degradação alta do Yahoo para B3, a camada de opções vira só
  leitura — usuário pode se frustrar sem entender por quê. Mitigado pela
  mensagem descritiva, não por esconder o botão sem explicação.
- Nenhuma automação hoje conta "aberturas da cadeia por semana" — o gatilho
  de 20% exige a extensão de `/api/obs/usage` (action item 2) antes de ser
  verificável.

**A revisitar**
- Quando `mydata_client.py` existir, este ADR volta para decidir se o
  Yahoo vira fallback do MyData ou é desligado.
- Se o gatilho de 20% disparar antes do MyData estar pronto, a prioridade
  daquele lado sobe — comunicar via `send_message`, como já feito uma vez
  nesta sessão.

## Action items

1. [ ] Compra de opção verifica `providerStatus == "ok"` antes de
   `buy_option`; resposta 4xx descritiva se degradado.
2. [ ] Estender `/api/obs/usage` com contador de aberturas de cadeia
   degradadas vs. ok (mesmo padrão do contador de IA).
3. [ ] UI: mensagem no botão de comprar quando degradado (não é erro
   genérico — nomeia a causa, como o resto do produto já faz).
