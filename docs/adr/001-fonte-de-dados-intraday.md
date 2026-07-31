# ADR-001: Fonte de dados intraday e onde esse dado vive

**Status:** Proposto — uma variável aberta (§ Decisão 2)
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
conversa): taxa de não-200 no fetch intraday acima de **2% em uma janela de 3
pregões**, observada pela instrumentação da Decisão 5. Nesse ponto a decisão
volta para o Alex com número, não com impressão.

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

## Decisão 2 — Granularidade: regra, não número (ABERTA até 11h BRT de 31/07)

A granularidade não pode ser escolhida por gosto: ela é **função do atraso do
feed**, que ainda não foi medido (a medição de 30/07 caiu com o pregão fechado;
rotina agendada para 31/07 às 11h BRT).

**Regra que este ADR fixa:** a duração da barra precisa ser **no mínimo o dobro
do atraso mediano do feed**.

O raciocínio: o produto só pode falar em "a condição ocorreu" se a barra em que
ela ocorreu já for conhecida. Se o atraso for maior que a duração da barra, o
sistema está permanentemente mais de uma barra atrás do mercado, e a afirmação
é falsa por construção. O fator 2 é a margem para o jitter da rede (p95 medido:
97 ms — irrelevante) e para o tempo de ciclo do laço.

| Atraso mediano medido | Granularidade | O que o produto pode dizer |
|---|---|---|
| ≤ 2,5 min | **5m** | "a condição ocorreu às 11:35" |
| ≤ 7,5 min | **15m** | "a condição ocorreu na barra das 11:30" |
| > 7,5 min | **30m ou 60m** | timing sai do produto; o dado vira contexto, não gatilho |

**Preferência declarada, a ser confirmada pela medição: 5m.** Justificativa
independente do atraso: 1m custa 14× mais em parse e armazenamento (418 velas/dia
contra 85) e traz **2,5% de fechamentos nulos** contra praticamente zero em
15m — buraco que a metodologia teria de tolerar sem ganhar resolução que os
setups do `skill_ref` explorem. E 15m dá só 29 pontos de decisão por pregão.

**Este ADR não é aceitável enquanto esta seção estiver aberta.** Se o atraso vier
acima de 7,5 min, a F1 muda de natureza — deixa de ser "timing" e vira "contexto
intradiário", e o vocabulário do Operador precisa ser revisto antes de qualquer
implementação.

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
- Se o atraso vier acima de 7,5 min → Decisão 2 muda e a F1 muda de natureza.
- Se a taxa de não-200 passar de 2% em 3 pregões → Decisão 1 aciona o plano B.
- Se a F3 exigir histórico intraday → Decisão 4 volta à mesa.

---

## Action items

1. [ ] **Fechar a Decisão 2** com a medição de atraso das 11h BRT de 31/07
       (rotina `trig_01Gj96hZAqj9ExHur6WEUyP7`). Sem isso o ADR não é aceito.
2. [ ] `merge_candles` chaveado por timestamp completo, no fuso da bolsa, com
       teste que prove que 617 velas de `15m × 1mo` continuam 617.
3. [ ] Intervalo na identidade do snapshot (`_snapshot_id` e `_SNAP_CACHE`), com
       teste de colisão diário × intraday.
4. [ ] `candle_cache` aceita modo sem L2 (intraday memória-apenas), preservando o
       write-through do diário.
5. [ ] Interface `CandleProvider` com o Yahoo como implementação única; brapi Pro
       documentada, não implementada.
6. [ ] Instrumentar o fetch intraday em `/api/obs/usage` (requisições, não-200,
       latência) — é o gatilho da Decisão 1.
7. [ ] Passada intraday no `scheduler_loop`, global, dentro de `in_market_hours()`,
       sem tocar o caminho do Radar diário.
8. [ ] `scripts/masstest-agentes.py` com 0 violações antes e depois.
9. [ ] Item separado, fora deste ADR: os 9 ativos que o Yahoo não serve.
