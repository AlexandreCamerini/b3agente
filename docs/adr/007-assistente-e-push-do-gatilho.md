# ADR-007: O assistente recebe snapshot, e o push do gatilho é opt-in server-side

**Status:** Aceito
**Data:** 2026-08-05
**Base:** ADR-006, `CHECKOUT-Didatica-Estudo-otimizado.md`, revisão sênior.

Duas features distintas num ADR só porque compartilham a mesma decisão de
fundo: **o que sai do app sem o usuário pedir precisa de uma fonte de verdade
que o servidor consiga ler.**

---

## Parte 1 — O assistente recebe um snapshot, não a tela

### Contexto

A camada determinística (ADR-006) responde *"o que é isto"*. Falta *"por que
isto está assim, no meu caso"* — pergunta livre, que só uma LLM responde.

### Decisão

**1. Snapshot estruturado, nunca a tela.** O front envia o view-model que já
usou para renderizar. Nada de raspar DOM. Assim o que chega é dado auditável, e
o modelo não tem como confundir texto de tela com instrução.

**2. Conteúdo de tela é DADO, não instrução.** Nome de ativo, texto de análise
anterior da LLM e campo editável pelo usuário entram como **valores** de um
JSON, depois do rótulo `Snapshot (dados exibidos agora):` e antes de
`Pergunta da pessoa:`. O prefixo declara isso explicitamente. Guardião:
`test_snapshot_entra_como_dado_e_o_prefixo_declara_isso`.

**3. Montagem cache-aware.** Prefixo estável (regras + princípios + glossário
canônico + disclaimer) primeiro; volátil (snapshot + pergunta) depois. Nada
variável no prefixo — timestamp, id ou número de ativo o invalidariam em
silêncio.

**4. Exige conta — por motivo técnico, não comercial.** `ai_activity` grava com
`user_id=scope`, e `scope=None` é **um balde compartilhado por todos os
anônimos**: um teto por escopo ali deixaria um usuário esgotar a cota de todos.
Quem não tem conta continua com a camada determinística, que é completa e não
gasta nada.

**5. `config` no corpo.** No aparelho o modelo e a chave são locais e o
servidor não os tem. Omitir isso é o que produziu *"Nenhum modelo de IA
configurado"* em produção no `scanDeep` (qa/29).

**6. Teto por escopo por dia** (`B3_ASSISTENTE_TETO_BRL`, padrão R$ 1,00),
lido do mesmo registro do painel de IA. Ao atingir, a mensagem aponta a camada
grátis em vez de só negar.

### Medição de cache — critério de aceite cumprido, e o que ela revelou

Duas perguntas seguidas na mesma tela, `claude-opus-5`, chamada real
(2026-08-05):

| | tokens novos | `cache_creation` | `cache_read` |
|---|---|---|---|
| 1ª pergunta | 109 | **4.118** | 0 |
| 2ª pergunta | 112 | 0 | **4.118** |

O prefixo é escrito uma vez e lido a 10% do preço nas seguintes. É o critério
de aceite da Fase 4, cumprido.

**A descoberta:** o prefixo tem **4.118 tokens reais**, não os ~3.038 que
`llm._system_cacheavel` estima. A heurística usa `_CHARS_POR_TOKEN = 3.2`; o
texto real deste prefixo dá **2,36 chars/token** (português com muito termo
técnico e pontuação). A estimativa erra 26% **para baixo**.

Consequência: `claude-haiku-4-5` exige 4.096 tokens e o prefixo real (4.118)
**passaria** — mas o código acha que tem 3.038 e recusa cachear. No modelo
padrão do app, portanto, cada pergunta paga o prefixo inteiro: **R$ 0,018**,
medido.

**Decisão: não mexer em `_CHARS_POR_TOKEN`.** A margem é de 0,5% (4.118 contra
4.096) — qualquer edição no texto do glossário derruba o prefixo abaixo do
mínimo, e a constante é global: mudá-la altera o comportamento de cache do
Radar N1 e de todo o resto por causa de um caso. Subestimar é a direção segura
do erro (nunca se paga uma escrita inútil). Se um dia valer a pena cachear em
haiku, o caminho é medir por chamador, não afrouxar a heurística de todos.

| Modelo | Mín. | Prefixo real 4.118 passa? | O código deixa cachear? |
|---|---|---|---|
| `claude-haiku-4-5` (padrão) | 4.096 | sim, por 22 tokens | **não** (estima 3.038) |
| `claude-sonnet-5` | 1.024 | sim | sim |
| `claude-opus-5` | 512 | sim | sim — **verificado acima** |

Com o teto de R$ 1,00/dia, haiku dá ~55 perguntas por usuário por dia. A
resposta viaja com `prefixoCacheavel` para a promessa seguir verificável.
**Inflar o prefixo até o mínimo não é opção**: pagar tokens para destravar
desconto é a otimização que alguém vai propor lendo só a tabela.

### O que a verificação ao vivo pegou

A primeira resposta real, em Modo Estudo, disse *"é o **sinal** de que chegou a
**hora de agir**"* sobre uma condição atingida. Não há verbo de ordem na frase,
então o guardrail de imperativo não pegaria — e é exatamente a confusão que a
camada inteira existe para desfazer. O prefixo ganhou uma seção proibindo
"sinal de compra", "sinal de entrada", "hora de agir" e equivalentes, com
guardião próprio.

---

## Parte 2 — O push do gatilho

### Contexto

Faz sentido avisar quando a condição de um plano é atingida. Mas um push é a
única coisa do app que **interrompe a pessoa fora do app, sem o contexto da
tela** — num produto de mercado, a superfície mais perigosa que existe.

### A descoberta que redesenhou a feature

O desenho inicial lia consentimento, modo e universo de `config.notif` /
`config.appMode` / `watchlist`. **Não funciona:** no aparelho,
`deviceStore.putConfig` grava em `localStorage` e **nunca chama a API**
(`web/src/persistence.js`). O servidor não enxerga nada disso de quem está no
iPhone — que é exatamente a audiência do APNs.

Consequências do desenho original, se tivesse ido a produção: o interruptor
desligado não desligaria nada; o vocabulário seria o do modo errado; e o app
avisaria sobre ativos que a pessoa removeu da watchlist.

### Decisão

**1. A fonte de verdade é `kv:pushPrefs`, alimentada pelo registro do token** —
o único caminho que sempre chega ao servidor nos dois stores. O aparelho anexa
`{prefs:{gatilho}, modo, universo}` a cada registro, e o `deviceStore` dispara
o sync sozinho (debounce) quando watchlist, posições, `notif` ou `appMode`
mudam: a UI não precisa lembrar do que ela não precisa saber.

**2. Opt-in.** Classe nova de alerta nasce desligada. `notif.gatilho` tem
variante própria de interruptor (`rowOptIn`), porque a variante comum trata
ausente como ligado — correto para avisos sobre a **sua** carteira, errado
para o único aviso disparado por evento de **mercado**.

**3. O carimbo vai no TÍTULO.** ADR-001 exige que toda afirmação de timing
carregue a hora da barra. No iOS o título é a única parte garantida na tela de
bloqueio — o corpo trunca. Carimbo no corpo é carimbo que some.

**4. Vocabulário de ESTUDO nos dois modos.** Canal interruptivo, fora do app,
sem o contexto da tela, não é lugar para a linguagem mais assertiva. Quem está
no Operador tem o app; o push é o menor denominador comum.

**5. A frase vem de `skill_ref.timing_txt`.** Redação nova faria a pessoa ler
um texto na notificação e outro no card — e ela é justamente quem não sabe se
são a mesma coisa.

**6. `esticado` não notifica.** Entre a barra fechar e o push chegar correm
~15 min de atraso do feed mais o intervalo do laço. Se nesse tempo o preço
esticou, avisar seria convocar a pessoa para uma entrada que o próprio app
desaconselha (Princípio 8).

**7. Teto duplo e agregação.** Um ativo oscilando em torno da entrada faz
`armado → gatilho → armado → gatilho` em barras consecutivas, cada uma com
`asOf` diferente — passaria pelo dedupe legitimamente. Daí o teto por
**(usuário, ticker, dia)** além do teto por usuário/dia (6). E vários ativos
cruzando na abertura viram **uma** mensagem, não N banners.

**8. Silencioso.** `priority 5`, sem som. Uma mesa não aprova alerta de mercado
em prioridade máxima com som num simulador.

**9. O push tem DESTINO.** O payload carrega `{"t": TICKER}` fora do `aps`; o
app escuta `pushNotificationActionPerformed`, **valida o ticker contra o
formato da B3** (conteúdo de notificação é dado, não instrução), garante o
ativo na watchlist, navega e rola até o card. Sem isso o toque abriria a aba
inicial sem nada sobre o ativo — interrupção sem destino é a pior categoria de
push que existe.

**10. Vaga consumida mesmo sem entrega.** `avisados` é gravado antes do envio.
Se o APNs falhar, aquele ativo não volta a notificar no dia, e o Diário
registra a **não entrega** com o motivo traduzido (`explain_reason`). É
deliberado: preferimos perder um aviso a produzir tempestade de retry num
canal interruptivo.

**11. Kill-switch próprio** (`B3_TIMING_PUSH_KILL=1`), independente da
didática e do assistente.

### Consequências

O vigia roda no laço que já existe (sem segundo scheduler), com fan-out
concorrente e um cliente HTTP compartilhado — `send_to_user` abre conexão por
chamada e espera até 10 s por token, o que em série travaria a passada
intraday e o ciclo de todos os usuários. O gancho tem `try` próprio pelo mesmo
motivo: o componente mais novo não pode derrubar o mais crítico.
