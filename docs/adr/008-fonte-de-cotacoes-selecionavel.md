# ADR-008: brapi (plano gratuito) como fonte master; Yahoo como backup

**Status:** Aceito em direção (decisão do Alex, 11/08/2026: "brapi master, plano gratuito, Yahoo de backup, dividir as 15.000 requisições, só no período de funcionamento da bolsa"). **Fase 0 executada em 11/08 com token real** ([MEDICAO-Brapi-2026-08-11](../MEDICAO-Brapi-2026-08-11.md)) — gate aprovado com ressalva (delay do spot pendente de medição em pregão)
**Data:** 2026-08-11
**Decisor:** Alex
**Base empírica:** doc viva da brapi (`https://brapi.dev/docs` e `https://brapi.dev/pricing`, consultadas em 11/08/2026) + spike ao vivo contra `https://brapi.dev/api/quote/PETR4` no sandbox gratuito (11/08/2026, payloads reais abaixo). A cota de **15.000 req/mês do plano gratuito é premissa informada pelo Alex** — a página pública de pricing só exibe Startup e Pro; a Fase 0 confirma com o token real.

---

## Contexto

O ADR-001 (31/07/2026) fixou Yahoo como primário atrás da interface
`CandleProvider`, com brapi Pro como plano B não implementado, sob restrição de
orçamento US$ 0. A direção agora inverte **sem revogar o orçamento**: a brapi
entra como master no **plano gratuito** (R$ 0), e o Yahoo — gratuito, sem
contrato, com termos que vedam uso comercial — sai da posição de dependência
primária e vira reserva. O motivador: reduzir a exposição ao Yahoo (risco
regulatório/ToS e a lacuna de 3h registrada em 31/07) usando uma fonte
brasileira com contrato, dentro de uma cota finita que exige orçamento de
requisições.

## O que já está confirmado vs o que a Fase 0 precisa provar

**Confirmado (spike de 11/08, sandbox):**

| Fato | Evidência |
|---|---|
| `GET /api/quote/{TICKER}?range=&interval=`; auth `Authorization: Bearer` | 200 no sandbox; doc 11/08 |
| Ticker sem `.SA`; velas em `historicalDataPrice` com `date` em epoch **já no fuso da bolsa** (diário = meia-noite BRT; 15m em 10:15, 10:30… BRT) | `1786330800 → 2026-08-10 00:00 BRT`; série 15m 10:15→16:45 |
| Spot mapeável 1:1 ao contrato interno (`regularMarketPrice/PreviousClose/ChangePercent`, `longName`, `currency`) | payload real |
| Batch multi-ticker exige token | `PETR4,VALE3,WEGE3` → `MISSING_TOKEN` |
| Endpoint `/api/available` lista o universo sem token | 200 com lista de tickers |
| **Intraday 1m–90m é exclusivo do plano Pro** (nem o Startup pago tem) | pricing 11/08: Startup "apenas 1d"; Pro "1m…3mo" |

**Confirmado na Fase 0 com token real (11/08/2026, [medição](../MEDICAO-Brapi-2026-08-11.md)):**

- Cota **15.000** confirmada por header (`x-ratelimit-limit: 15000`); janela de
  reset não exposta nos headers — presumida mensal, confirmar no painel.
- **1 ticker por requisição** (`QUOTES_PER_REQUEST_EXCEEDED` ao enviar 3).
- **Só `1d`** de intervalo (`INVALID_INTERVAL` para 15m fora do sandbox).
- **Range máximo `3mo`** (`INVALID_RANGE` para 2y; permitidos: 1d/5d/1mo/3mo) —
  warmup `2y` e período default `1y` do app ficam **definitivamente no Yahoo**;
  a brapi free serve spot + delta diário de até 3mo.
- **Requisição recusada por plano DEBITA a cota** — validação client-side de
  intervalo/range antes de chamar é obrigatória; erro de plano é guarda de
  teste, não caminho normal.
- `close` ≠ `adjustedClose` em 25/62 velas do ITSA4 (3mo) — confirma a regra
  "fonte diferente = substituição, nunca merge".
- **Pendente:** atraso real do spot (medição feita fora de pregão; repetir
  amostragem de 1h em pregão — decide só o TTL da fatia de spot).

## Decisão

**brapi (plano gratuito) é a fonte master de candles diários e cotação spot.
Yahoo é o backup dessas duas superfícies e continua sendo a fonte do intraday**,
porque o plano gratuito não tem intraday — isso não é escolha, é restrição de
plano, e fica declarado. Toda chamada à brapi respeita um **orçamento de
requisições** com teto diário e janela restrita ao calendário/horário da B3.
Estourou o orçamento ou falhou → Yahoo assume o resto do dia, transparente, com
o payload etiquetado pela fonte que serviu.

### Orçamento das 15.000 requisições

Premissas: ~21 pregões/mês → **teto diário = 15.000 ÷ 21 ≈ 700 req/pregão**
(fora de pregão a brapi não é chamada — sábado, domingo, feriado B3 e
madrugada consomem zero). Hipótese conservadora de 1 ticker/req; universo ~65
ativos; cache spot é **compartilhado entre usuários** (o consumo escala com o
universo × TTL, não com o número de usuários).

| Fatia | Uso | Orçamento/dia | Mecânica |
|---|---|---|---|
| Spot on-demand | cards, watchlist, `/api/quotes` | **400** | cache compartilhado com TTL dinâmico: 5 min enquanto sobra orçamento, degradando para 15 min quando a fatia passa de 70% |
| Delta diário de candles | revalidação `1mo` por ticker | **150** | 1 passada pós-fechamento (~17:10 BRT) no universo ativo; warmup `FULL_RANGE` de ticker novo vai pro Yahoo se o gratuito limitar o range |
| Fundamentos | `fundamentals.py` já chama a brapi; com token passa a contar na cota | **30** | TTL de 7 dias já existente + throttle atual |
| Reserva | falha/retry, tickers fora do universo, folga | **~120** | — |

Guardas: contador persistido em SQLite por dia-calendário (sobrevive a
restart/deploy), **soft stop em 80%** da fatia (degrada TTL), **hard stop em
100%** do teto diário (brapi silencia, Yahoo assume até o próximo pregão).
`/api/status` expõe consumo por fatia. Janela: chamadas só em pregão
(10:00–17:15 BRT em dia útil B3), exceto a passada de delta pós-fechamento,
que faz parte do funcionamento da bolsa (leilão de fechamento) e roda uma vez.

### As decisões de projeto, fechadas

1. **Escopo por superfície** — diário+spot: brapi master / Yahoo backup;
   intraday 15m (Radar/STU/F1): Yahoo (restrição do plano gratuito, declarada
   na didática); fundamentos: como estão (brapi já é a fonte; o token entra na
   cota e no orçamento); opções: fora (ADR-004).
2. **Seleção em env** — `B3_CANDLE_PROVIDER=brapi` (master),
   `B3_CANDLE_FALLBACK=yahoo`, `BRAPI_TOKEN` por ambiente no Railway,
   `B3_BRAPI_COTA_MES=15000` (ajustável sem deploy se o plano mudar). Nada de
   escolha na UI.
3. **Cache com fonte no registro** — chave `(symbol, interval)` fica; entrada
   ganha `src` (fonte da última escrita, persistida no L2).
   **ERRATA (11/08, Fase 4):** no DIÁRIO o merge entre fontes é PERMITIDO —
   a inversão obriga warmup Yahoo (2y) + delta brapi (≤3mo) a conviverem na
   mesma série, e a validação ao vivo mostrou 21 pregões de PETR4 com
   open/close/volume IDÊNTICOS entre as fontes (o print bruto da B3 é o
   mesmo; o cliente brapi usa `close`, nunca `adjustedClose`). Pela mesma
   razão o `snapshotId` NÃO carrega a fonte: ele identifica o DADO, o dado
   diário é idêntico, e carimbar a origem invalidaria análises N1/N2 pagas a
   cada failover sem mudança real. A regra "substituição, nunca merge"
   sobrevive onde o risco existe: séries ajustadas (nunca usar
   `adjustedClose`) e intraday (fonte única por construção — Yahoo).
   Este `src` acumulado no L2 é também o **acervo próprio de histórico**
   pedido pelo Alex: o delta diário estende a série local dia a dia e ela
   sobrevive a deploy.
4. **Failover por requisição + por orçamento** — cai pro Yahoo em três
   situações: exceção, série vazia, ou orçamento esgotado. Retorno à brapi:
   automático no pregão seguinte (orçamento renova por dia).
5. **Divergência: quem serviu manda e se declara** — payload carrega `source`
   e idade; a didática declara origem e atraso; intraday declarado como Yahoo.
6. **Instrumentação por provedor + por fatia de orçamento** — `snapshot()`
   reporta taxa de falha por provedor e consumo por fatia; o gatilho de 2%/3
   dias do ADR-001 passa a vigiar o **novo primário (brapi)**; guardião
   atualizado com nota, nunca apagado.
7. **Cota**: orçamento acima; premissa de 15k confirmada na Fase 0.
8. **Segredo**: `BRAPI_TOKEN` só em env do servidor; sem token, o registry
   falha alto (mensagem atual do stub) e o app opera 100% Yahoo como hoje.
9. **Rollback**: `B3_CANDLE_PROVIDER=yahoo` + `B3_CANDLE_FALLBACK=""` devolve
   o comportamento de hoje — só env, sem build. O cache se auto-corrige pela
   regra 3.

## Alternativas descartadas

- **brapi Pro (R$ 116,66/mês) já:** resolveria intraday e batch, mas contraria
  o orçamento vigente; fica como upgrade natural se a cota gratuita apertar ou
  o Yahoo degradar de vez — o consumo por fatia no `/api/status` é exatamente
  o dado para essa decisão.
- **Intraday na brapi gratuita:** não existe no plano (pricing 11/08). Se a
  Fase 0 mostrar o contrário com token real, o orçamento é refeito — hoje
  seria planejar sobre um privilégio de sandbox.
- **Escolha de fonte na UI / cross-check de preço / chave de cache com
  provedor:** descartados pelos mesmos motivos da versão anterior deste ADR
  (usuário sem base para escolher; consumo dobrado sem histórico de
  divergência; L2 duplicado e failover frio).

## Consequências

- Custo: **R$ 0**. O orçamento do ADR-001 permanece válido.
- A dependência primária migra de uma fonte sem contrato (Yahoo) para uma
  fonte com contrato e cota — e o Yahoo continua indispensável (intraday +
  backup): não é remoção de dependência, é redução de exposição.
- Surge um subsistema novo e testável: o orçamento de requisições (contador
  persistido, fatias, janela de pregão) — `candle_provider.py` deixa de ser só
  fronteira e ganha política.
- O calendário B3 (dias úteis/feriados) passa a ser insumo do provedor — o
  app já tem noção de pregão (`intraday.py`, `candles.py:64`); reusar, não
  duplicar.
- Se o gratuito limitar range histórico, warmup de médias longas continua no
  Yahoo — mais um motivo para o backup nunca ser removido.
