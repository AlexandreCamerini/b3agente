# ADR-001: Fonte de dados intraday e onde esse dado vive

**Status:** **Aceito** — atraso medido em 31/07 (15,0 min constantes); regra do "dobro do atraso" corrigida.
Risco aberto: lacuna de 3h no feed em 31/07 (§ Decisão 2, "O achado que NÃO era o esperado")
**Data:** 2026-07-31
**Decisor:** Alex
**Base empírica:** [`docs/MEDICAO-Yahoo-Intraday-2026-07-30.md`](../MEDICAO-Yahoo-Intraday-2026-07-30.md) — nada aqui é estimativa quando existe medição.

---

## Contexto

A F1 do checkout (timing de entrada) exige dado intraday, que o produto nunca
buscou: `yahoo.py` sempre chamou `/v8/finance/chart/` com `interval: "1d"`.
A Fase 1 mediu o terreno. O que ela fixou:

- O Yahoo **entrega** intraday para `.SA` (1m até 7d; 5m/15m até 1mo; 60m até 2y)
  e **aguenta** o volume: 1.300 requisições em 17 s de IP residencial, e do IP de
  produção (`sfo`) 266 requisições com p50 de **50 ms** e zero não-200 — o IP de
  datacenter é **3,5× mais rápido**, não penalizado.
- Custo de infraestrutura do intraday: **~US$ 1/mês**. Não é o custo relevante.
- **Nenhuma fonte gratuita** entrega intraday de B3. A única paga barata e
  confirmada é a brapi Pro (R$ 116,66/mês), que usaria 1,7% da cota.

Restrições já decididas pelo Alex, que este ADR trata como dadas:

| Decisão | Valor | Impacto aqui |
|---|---|---|
| Orçamento de dado intraday | **US$ 0** | elimina brapi Pro e EODHD como fonte primária |
| Enquadramento do timing | **só no Operador, vocabulário descritivo** | limita o que o dado pode afirmar (§ Consequências) |

E duas descobertas no código que este ADR precisa endereçar, medidas em 30/07:

1. **O caminho atual colapsa intraday.** `get_history` monta `date` como
   `%Y-%m-%d` (`gmtime`) e `merge_candles` indexa por essa string: 617 velas de
   `15m × 1mo` viram **22 chaves**. Passar intraday pelo caminho de hoje descarta
   96% dos candles em silêncio.
2. **O `snapshotId` não conhece o intervalo.** `_snapshot_id(ticker, period, fp)`
   e `_SNAP_CACHE[(ticker, period)]` — o intervalo não entra na identidade. Um
   snapshot diário e um intraday do mesmo ativo e período disputam a mesma
   entrada de cache, e o `snapshotId` não distingue de qual timeframe veio. É
   exatamente a "contradição entre camadas" que o masstest existe para pegar.

---

## Decisão 1 — Provedor: Yahoo primário, atrás de uma interface

**Yahoo Finance como fonte primária, acessada por uma interface de provedor**
(`CandleProvider`), com brapi Pro registrada como plano B **documentado e não
implementado**.

O orçamento de US$ 0 decide a fonte. O que ele **não** decide é o acoplamento: o
Yahoo é gratuito, sem contrato, sem SLA, e seus termos de uso vedam uso
comercial e redistribuição. A medição diz que ele sustenta; nada diz que
continuará permitindo. A interface é o que transforma "trocar de fonte" em
configuração em vez de refatoração — e custa pouco, porque
`options_provider_yahoo.py` já estabeleceu essa postura no módulo de opções
depois do incidente do 401.

**Gatilho declarado para acionar o plano B** (sem isso, "temos um plano B" é
conversa): taxa de **FALHA** no fetch intraday acima de **2% em uma janela de 3
pregões**, observada pela instrumentação da Decisão 5. Nesse ponto a decisão
volta para o Alex com número, não com impressão.

**FALHA = não-200 _ou_ 200 com série vazia.** A definição original só contava
não-200 e teria dormido durante o incidente de 31/07, em que 360 requisições
consecutivas voltaram 200 com zero velas (§ Decisão 2). Corrigido no mesmo dia,
com regressão.

### Opções consideradas

| | Yahoo | brapi Pro | EODHD | B3 UP2DATA |
|---|---|---|---|---|
| Custo/mês | **US$ 0** | R$ 116,66 | US$ 29,99 | milhares de R$ |
| Intraday `.SA` | sim, 1m–90m | sim, 1m–90m | sim, atraso 15 min | sim, oficial |
| Cota vs. volume do Radar | sem cota declarada | 1,7% de 500k | 6% de 100k/dia | n/a |
| Latência medida da produção | **50 ms** | não medida | não medida | n/a |
| Contrato / SLA | **nenhum** | sim | sim | sim |
| Termos permitem uso comercial | **não** | sim | sim | sim |
| Validado empiricamente | **sim, 1.566 requisições** | não | **não** — cobertura `.SA` não confirmada | não |

Twelve Data foi descartada por medição de terceiro: a BVMF é *EOD only* na
plataforma. Alpha Vantage não documenta intraday para `.SAO`.

**Trade-off central:** US$ 0 sem contrato e contra os termos de uso, versus
R$ 117/mês com contrato. Não é uma decisão técnica nem de custo — é de risco, e
o Alex a tomou. O papel deste ADR é garantir que ela seja **reversível barato**.

---

## Decisão 2 — Granularidade: **15m, sobre velas FECHADAS** · MEDIDA E CONFIRMADA

**Decisão do Alex em 31/07:** adotar `15m`, em vez de deixar a escolha pendurada
na medição. O produto é, nesta fase, um **modelo de treinamento** —
assertividade e verificabilidade valem mais que resolução.

**Medição de 31/07/2026, 13:04 BRT, pregão aberto, do IP de produção:**

| Intervalo | Lag do último negócio | Idade da barra utilizável |
|---|---|---|
| `1m` | **15,0 min** | 15–16 min |
| `5m` | **15,1 min** | 15–20 min |
| `15m` | **15,1 min** | 15–30 min |
| `30m` | **15,1 min** | 30–60 min |

Idêntico em PETR4, VALE3, BBDC4 e MGLU3, e estável em 15,0–15,2 min ao longo de
25 minutos de amostragem. **Não é jitter: é atraso deliberado e constante de 15
minutos**, a assinatura padrão de feed de bolsa não licenciado.

### A regra do "dobro do atraso" estava ERRADA — a medição a derrubou

A versão anterior deste ADR fixava: *a barra tem que durar no mínimo o dobro do
atraso*. Com 15 min de lag, isso exigiria `30m` e reprovaria os `15m`.

A regra está errada, e a tabela acima mostra por quê: **engrossar a barra piora a
informação**. A idade da barra utilizável é `atraso + duração da barra` — subir de
`15m` para `30m` leva a staleness de 15–30 min para 30–60 min. A regra empurraria
para a decisão pior.

O erro conceitual foi tratar o atraso como algo que a granularidade compensa. Não
compensa: **os 15 minutos são constantes e independem do intervalo escolhido.**

**Regra corrigida:** o atraso do feed não escolhe a granularidade — ele decide
**se timing é uma feature viável e o que o produto pode afirmar**. A granularidade
é escolhida por resolução e qualidade de série (ver "Por que 15m e não 5m").

### O que o produto pode e não pode dizer, com 15 min de atraso

- ❌ "a condição **está ocorrendo agora**" — falso por construção, sempre, por 15 min.
- ✅ "a condição ocorreu **na barra das 12:45, que fechou às 13:00**" — verdadeiro
  e auditável.

Para o horizonte swing do produto (Operador reavaliando a cada 5 min, Radar
diário), um gatilho com 15–30 min de idade é utilizável. Para day trade, não
seria — e o produto não é day trade.

**Obrigação de interface:** toda afirmação de timing carrega o carimbo da barra e
o horário de fechamento dela. Sem o carimbo, a frase insinua tempo real e vira
falsa. Isto é requisito, não enfeite.

### Por que 15m e não 5m

1. **Melhor relação entre frescor e ruído, dado o atraso medido.** Com 15 min de
   lag constante, `5m` entrega staleness de 15–20 min contra 15–30 min do `15m` —
   ganho marginal, ao custo de 3× mais velas e de uma série visivelmente mais
   suja. `1m` seria 14× o volume por 1 minuto de frescor.
2. **Série mais limpa.** Medido em PETR4: `1m` traz 2,5% de fechamentos nulos,
   `15m` traz **1 vela** em 617. E PETR4 é a ação mais líquida da bolsa — na
   cauda do universo (COGN3, AURE3, IGTI11) o buraco é maior. Indicador sobre
   série esburacada mente, e o Radar varre 65 ativos, não um.
3. **Casa com o horizonte real do produto.** O laço reavalia a cada 5 min e o
   Radar é diário: o horizonte é swing, não scalping. `1m`/`5m` só se pagariam
   num produto que executa na hora.
4. **Custo.** 29 velas/pregão/ativo contra 85 do `5m` e 418 do `1m`.

29 pontos de decisão por pregão são poucos para day trade e suficientes para o
que este produto faz.

### Sobre velas FECHADAS — a parte que importa mais que a granularidade

**Nenhum gatilho pode ser lido na vela em formação.** Ela muda até fechar: às
11:32 a barra das 11:30 ainda tem 13 minutos de mudança pela frente, e uma
condição vista ali pode simplesmente deixar de existir às 11:45.

Isso não é hipotético neste código: o `candle_cache` **revalida a última vela por
contrato** (`merge_candles`: "fresco vence"), então a última vela da série é
sempre a que ainda está se formando. Com o laço de 5 min e velas de 15m, cada
barra seria lida três vezes antes de existir de verdade.

Para um modelo de treinamento a diferença é entre uma afirmação verificável e
uma que não é:

- ✅ "a condição ocorreu na barra das 11:30, que fechou às 11:45"
- ❌ "a condição está ocorrendo agora"

**Consequência de implementação:** no intraday, o STU calcula sobre a série
**menos a última vela**, e o carimbo (`snapshotAt`) é o da última barra fechada.
O diário fica como está — lá a "vela em formação" é o pregão do dia, e o produto
já é explícito sobre isso.

### O achado que NÃO era o esperado — e que ameaça a Decisão 1, não a 2

A medição de 31/07 revelou algo mais grave que o atraso, e por acaso: **o feed de
B3 do Yahoo passou as primeiras 3 horas do pregão sem publicar absolutamente
nada.**

Cronologia medida (360 amostras de 2 em 2 min, 3 ativos, 2 intervalos):

| Hora BRT | Estado |
|---|---|
| 10:00 | abertura da B3 (dia de pregão normal, [calendário oficial](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-participantes-e-traders/calendario-de-negociacao/feriados/) confere) |
| 10:08 → 12:10 | **zero velas**, em 360 amostras. `regularMarketTime` congelado em `30/07 17:05:39` — o MESMO segundo, sempre |
| 13:02 | primeira vela do dia aparece, começando às **12:45** |
| 13:28 | série continua começando em 12:45 — **a manhã não foi preenchida** |

Discriminante decisivo, no mesmo instante e pelo mesmo endpoint:

| Símbolo | Velas hoje | Lag |
|---|---|---|
| AAPL | 22 | **0 min** |
| VALE (ADR em NY) | 22 | **0 min** |
| PETR4.SA | 0 | 1.147 min |
| ^BVSP | 0 | 1.135 min |

O Yahoo estava **saudável e em tempo real** para os EUA enquanto não entregava
nada de B3. Não é feriado, não é bloqueio, não é rate limit, não é o IP da
Railway: é o feed de B3 sumindo em silêncio, com HTTP 200 e
`marketState: REGULAR`.

**Consequências:**

1. **~2h45 de pregão sumiram da série** e não retornaram. Indicador calculado
   sobre série com buraco de três horas mente, e o produto não teria como saber.
2. **A instrumentação da Decisão 5 era cega para isto** — contava falha como
   não-200, e aqui todos os 360 retornos foram 200. Corrigido no mesmo dia:
   resposta vazia agora conta como falha (`vazios`, `taxaFalha`), com regressão
   que reproduz este pregão.
3. **O risco da Decisão 1 deixou de ser teórico.** "Sem contrato, sem SLA" saiu
   do papel no segundo dia de observação. Em 30/07 o mesmo pedido devolveu 617
   velas de `15m`; em 31/07, nada por 3 horas.

**Um pregão não faz padrão** — por isso a Decisão 1 NÃO muda aqui. Mas fica o
gatilho explícito: **se a lacuna se repetir em outro pregão, a Decisão 1 volta à
mesa**, e a brapi Pro (R$ 116,66/mês) deixa de ser plano B teórico. O orçamento
de US$ 0 foi aprovado com a informação de que o Yahoo funcionava; essa
informação mudou.

---

## Decisão 3 — Cobertura: o universo inteiro, global, não por usuário

**Os 65 ativos que o Yahoo serve, varridos uma vez por ciclo, no laço global.**
Não por posição aberta, não por watchlist.

O argumento não é custo de dado — é **como o custo escala**. Uma varredura
global de 65 ativos custa 65 requisições por ciclo, **independente do número de
usuários**: 0,45 s de parede, medido da produção. Uma varredura por posição
aberta ou por watchlist custa O(usuários × ativos) e cresce com o sucesso do
produto. O `radar_daily` já armazena globalmente (kv sem `user_id`) pela mesma
razão.

Como o intraday é global, ele **não** entra no gate `intervalMin` por usuário:
roda uma vez por passada do `scheduler_loop`, dentro do `in_market_hours()`, e
todo usuário lê o mesmo resultado.

**Nota sobre os 9 ausentes.** ELET3, ELET6, JBSS3, EMBR3, CPLE6, CRFB3, NTCO3,
MRFG3 e BRFS3 dão 404 no Yahoo em **qualquer** intervalo, inclusive `1d` — o
Radar já roda com 65 de 74 hoje. Não é consequência deste ADR e não deve ser
resolvido dentro dele, mas com uma fonte única de dados isso vira dívida
conhecida: **Eletrobras, Embraer, JBS, Copel, Carrefour, Natura, Marfrig e BRF
não existem no produto.** Item próprio.

---

## Decisão 4 — Onde o dado vive: L1 apenas, sem persistência

**O cache intraday é memória do processo. Sem write-through para o SQLite.**

Esta é a decisão que mais economiza, e ela vem direto da medição. O `candle_cache`
guarda a série inteira como **um blob JSON por chave** e **regrava o blob todo** a
cada atualização (149 B/vela, medidos). Com persistência, o intraday custaria:

| Política | Blob por ativo | Reescrita/dia (65 ativos × 96 rodadas) |
|---|---|---|
| `15m`, retenção 1 dia | 4,2 KB | 26 MB/dia |
| `15m`, retenção 1 mês | 90 KB | 561 MB/dia |
| **`5m`, retenção 1 mês** | **265 KB** | **1,65 GB/dia** |
| `1m`, retenção 7 dias | 414 KB | 2,58 GB/dia |

Nada disso é caro em dinheiro (volume custa ~US$ 0,16/GB-mês). É desgaste e
latência de escrita num volume único com WAL, para guardar dado que **não vale a
pena guardar**.

O L2 existe por uma razão específica, registrada no próprio módulo: evitar
rebaixar **2 anos** de candles diários do universo inteiro depois de cada
redeploy. Essa razão **não transfere** para o intraday, onde a janela cheia é
*uma* requisição barata. Medido: reidratar o intraday de todo o universo do zero
custa **0,45 s**. Persistir 1,65 GB/dia para poupar 0,45 s por redeploy é um mau
negócio com números em cima.

Consequências operacionais, todas aceitas:

- **Redeploy e restart perdem o intraday** e o refazem em 0,45 s.
- **Railway dormindo** (§6 do checkout) tem o mesmo efeito e o mesmo custo. O
  `scheduler_loop` já gera tráfego outbound a cada 300 s durante o pregão, então
  o cenário é raro dentro da janela que importa.
- **RAM:** 65 ativos × 600 velas ≈ 8 MB. Cabe folgado.
- Carga fria pede `5m × 1mo` (1.849 velas, 162 KB — cobre SMA200 e EMA72 com
  margem); as passadas seguintes pedem `5m × 1d` (85 velas, 37 KB).

**Correção obrigatória antes de qualquer coisa (bloqueador medido):** a chave da
vela em `merge_candles` precisa ser o **timestamp completo**, não `%Y-%m-%d`, e o
horário precisa vir no fuso da bolsa (`America/Sao_Paulo`, `gmtoffset -10800`),
não em `gmtime`. Sem isso o intraday perde 96% dos candles em silêncio. A chave
do *cache* (`símbolo@intervalo`) já está correta e não muda.

---

## Decisão 5 — Identidade e instrumentação

**O intervalo entra na identidade do snapshot.** `_snapshot_id(ticker, period,
interval, fp)` e `_SNAP_CACHE[(ticker, period, interval)]`. Hoje o intervalo não
entra em nenhum dos dois: um snapshot diário e um intraday do mesmo ativo
disputam a mesma entrada, e o `snapshotId` que amarra N1/N2/N3 não diz de qual
timeframe veio. Sem esta correção, o critério de aceite da F1 ("dado intraday
chega ao STU com `snapshotId` próprio") é impossível de satisfazer.

**O fetch intraday é instrumentado como a IA já é.** Contador de requisições,
de não-200 e de latência, expostos em `/api/obs/usage` ao lado do uso de IA. É o
que torna o gatilho da Decisão 1 verificável, e é o que o §7 do checkout pede
("custo cresce em silêncio").

---

## Consequências

**Fica mais fácil**
- Trocar de provedor: vira configuração, não refatoração.
- Prever o custo: o intraday é O(1) em usuários e ~US$ 1/mês em infraestrutura.
- Subir a concorrência: conc=16 foi medida sem um único erro e é 3,4× mais rápida
  que a conc=4 de hoje. `CONCURRENCY` e `MIN_FETCH_GAP_S` do scanner são
  conservadores por ~40×.

**Fica mais difícil**
- Backtest intraday: sem persistência, não há série histórica intraday para
  reprocessar. **Aceito conscientemente** — se a F3 (alvo dinâmico) precisar de
  histórico intraday para validação, este ADR precisa ser revisitado, e a saída
  é uma tabela append-only por vela, não o blob de hoje.
- Depender do Yahoo sem contrato continua sendo o risco não mitigado. A interface
  reduz o custo de sair; não reduz a chance de precisar sair.

**O que o dado NÃO pode dizer** (decisão do Alex, registrada aqui porque
restringe o desenho): o timing aparece **só no Modo Operador**, em vocabulário
descritivo — "a condição de rompimento ocorreu às 11:32" —, nunca em verbo de
ordem. O Estudo continua sem eixo de tempo. O `test_guardrail_imperativo`
continua valendo para os dois modos.

**A revisitar**
- Se a LACUNA de 31/07 se repetir em outro pregão → a Decisão 1 (fonte única
  gratuita) volta à mesa, não a Decisão 2.
- Se a taxa de não-200 passar de 2% em 3 pregões → Decisão 1 aciona o plano B.
- Se a F3 exigir histórico intraday → Decisão 4 volta à mesa.

---

## Action items

1. [x] ~~Validar a Decisão 2 com a medição de atraso~~ — FEITO em 31/07:
       15,0 min constantes. `15m` confirmado; a regra do "dobro do atraso" foi
       corrigida (engrossar a barra piorava a informação).
1c.[ ] **Carimbo da barra na interface** — toda afirmação de timing mostra a
       barra e o horário de fechamento dela. Sem isso a frase insinua tempo
       real e vira falsa. Requisito da Decisão 2.
1d.[x] ~~Detectar lacuna na série intraday~~ — FEITO: `candles.detectar_lacunas`
       (início tardio, buracos no meio, cobertura), ligado ao `dataQuality` do
       STU. Série furada derruba `tetoConfianca` para "baixa". Validado contra a
       série real de 31/07 (cobertura 0,45, 11 velas faltando) e contra a de
       30/07 (cobertura 1,0, sem lacuna).
1b.[x] ~~STU intraday calcula sobre velas FECHADAS~~ — FEITO (`bd3d2db`). — descartar a última vela
       (a que o `merge_candles` revalida) e carimbar `snapshotAt` com a última
       barra fechada. Teste: gatilho não pode mudar entre duas leituras da mesma
       barra em formação.
2. [x] ~~`merge_candles` chaveado por timestamp completo~~ — FEITO (`0425617`):, no fuso da bolsa, com
       teste que prove que 617 velas de `15m × 1mo` continuam 617.
3. [x] ~~Intervalo na identidade do snapshot~~ — FEITO (`0425617`): (`_snapshot_id` e `_SNAP_CACHE`), com
       teste de colisão diário × intraday.
4. [x] ~~`candle_cache` sem L2 no intraday~~ — FEITO (`0425617`): (intraday memória-apenas), preservando o
       write-through do diário.
5. [x] ~~Interface `CandleProvider`~~ — FEITO (`ce840d7`): com o Yahoo como implementação única; brapi Pro
       documentada, não implementada.
6. [x] ~~Instrumentar o fetch intraday~~ — FEITO (`ce840d7` + `39f2910`): em `/api/obs/usage` (requisições, não-200,
       latência) — é o gatilho da Decisão 1.
7. [x] ~~Passada intraday no `scheduler_loop`~~ — FEITO: `app/intraday.py`,
       global, 15m canônico, dentro de `in_market_hours()`, gap mínimo de 240 s,
       kill switch próprio (`B3_INTRADAY_OFF`) e endpoint `/api/intraday` que
       serve o ARMAZENADO (varrer sob demanda viraria custo O(requisições)).
       Validado com dado real: 5 ativos em 1,83 s, asOf na barra fechada,
       lacuna detectada (cobertura 0,5 no pregão quebrado de 31/07).
8. [x] ~~`scripts/masstest-agentes.py` com 0 violações~~ — conferido a cada entrega: antes e depois.
9. [ ] Item separado, fora deste ADR: os 9 ativos que o Yahoo não serve.
