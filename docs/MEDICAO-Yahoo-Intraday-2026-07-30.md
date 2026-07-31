# Medição — Yahoo intraday para `.SA` (Fase 1 do CHECKOUT Intraday/Trailing/Web)

**Quando:** 2026-07-30, entre 18h17 e 18h30 (BRT ~20h20–20h33) — **pregão fechado**.
**Como:** `scripts/medir-yahoo-intraday.py`, script pontual que **não toca produção**
(não importa `main`, não abre banco, não usa `candle_cache`). Reusa só a camada de
sessão do cliente real (`server/app/yahoo.py`: cookie + crumb + UA + rotação de host).
**De onde:** IP residencial. **Não é o IP da Railway** — ver "Limites da medição".

Reproduzir:

```bash
server/.venv/bin/python scripts/medir-yahoo-intraday.py --fases matriz,latencia,rajada,spark,cobertura --saida /tmp/medicao.json
```

---

## 1. Intervalos e janela máxima real (PETR4.SA)

`range` pedido além do limite → **HTTP 422** (`Unprocessable Entity`), não degrada.
Exceção perigosa: `range=max`.

| Intervalo | Janela máxima aceita | Velas na janela máxima | Velas por pregão | Payload (janela útil) | Observação |
|---|---|---|---|---|---|
| `1m`  | **7d** (8 dias corridos) | 2.938 | 418 | 36,8 KB (`1d`) · 250 KB (`7d`) | `1mo`+ → 422 |
| `2m`  | **1mo** (29 dias) | 4.620 | 210 | 399 KB (`1mo`) | |
| `5m`  | **1mo** | 1.849 | 85 | 162 KB (`1mo`) · 37 KB (`5d`) | |
| `15m` | **1mo** | 617 | 29 | 56 KB (`1mo`) · 3,7 KB (`1d`) | |
| `30m` | **1mo** | 309 | 15 | 30 KB (`1mo`) | |
| `60m` / `1h` | **2y** | 3.490 | 8 | 344 KB (`2y`) | únicos intraday com histórico longo |
| `90m` | **1mo** | 111 | 6 | 12,5 KB | |
| `1d`  | `max` (26 anos) | 500 (`2y`) | 1 | 54 KB (`2y`) | o que o app usa hoje |

**Armadilha medida:** `range=max` **com qualquer intervalo intraday** devolve HTTP 200
com `dataGranularity: "1mo"` — 319 velas **mensais**, passo de 2.678.400 s. Não erra:
degrada em silêncio. Quem pedir `max` achando que pega "tudo" recebe dado mensal
rotulado como intraday.

**Cobertura da sessão:** `1m × 1d` traz 418 velas para um pregão de 10:00–17:00
(421 min). Último candle às **17:00 BRT** — sessão inteira, `includePrePost=false`
respeitado. `exchangeTimezoneName: America/Sao_Paulo`, `gmtoffset: -10800`;
timestamps em epoch UTC.

**Buracos:** em `1m`, ~2,5% das velas vêm com `close: null` (413 válidas de 418 em
PETR4) e há velas de volume zero. Em `15m`/`30m` isso praticamente some (1 vela).
Quanto menor o intervalo, mais o indicador vai precisar tolerar buraco — em ativo
de cauda o efeito é maior que em PETR4.

## 2. Cobertura do universo do Radar

| Requisição | Servidos | Sem dado |
|---|---|---|
| `15m × 5d` | **65 / 74** | ELET3, ELET6, JBSS3, EMBR3, CPLE6, CRFB3, NTCO3, MRFG3, BRFS3 |
| `1d × 1mo` | **65 / 74** | os mesmos 9 |

Os 9 dão **HTTP 404 em qualquer intervalo, inclusive `1d`**. Ou seja: **não é
limitação do intraday — é um buraco que já existe na produção de hoje.** Eletrobras,
Embraer, JBS, Copel, Carrefour BR, Natura, Marfrig e BRF simplesmente não entram no
Radar. `run_scan` captura a exceção por ativo (`scanner.py:308`) e devolve
`scanned: 65` + `errors: [...]` no payload — está exposto, mas ninguém olha.
**Achado colateral, fora do escopo da F1, que vale um item próprio.**

## 3. Latência (sequencial, 1 requisição por vez, 12 amostras, liquidez variada)

| Intervalo × range | p50 | p95 | Payload médio | Falhas |
|---|---|---|---|---|
| `1m × 1d`   | 175 ms | 274 ms | 36,4 KB | 0 |
| `5m × 5d`   | 179 ms | 204 ms | 37,2 KB | 0 |
| `15m × 5d`  | 173 ms | 201 ms | 13,6 KB | 0 |
| `60m × 1mo` | 179 ms | 200 ms | 16,1 KB | 0 |
| `1d × 1mo`  | 198 ms | 262 ms | 3,5 KB  | 0 |

A latência **não varia com a granularidade** — é custo de rede, não de payload.

## 4. Rajada — o universo do Radar de uma vez

`15m × 5d`, 74 ativos (os 9 do 404 contam como falha):

| Concorrência | Parede | Status | p50 | p95 | Tráfego |
|---|---|---|---|---|---|
| 4  | 5,5 s | 65×200, 9×404 | 274 ms | 469 ms | 0,87 MB |
| 8  | 2,7 s | 65×200, 9×404 | 271 ms | 467 ms | 0,87 MB |
| 16 | 1,5 s | 65×200, 9×404 | 272 ms | 585 ms | 0,87 MB |

`1m × 1d` (payload máximo por ativo), 65 ativos válidos:

| Concorrência | Parede | Status | p50 | p95 | Tráfego |
|---|---|---|---|---|---|
| 8  | 2,7 s | 65×200 | 276 ms | 459 ms | 2,32 MB |
| 16 | 1,5 s | 65×200 | 272 ms | 586 ms | 2,32 MB |

**Endurance:** 20 rodadas seguidas de 65 ativos a conc=16 →
**1.300 requisições em 17 s (74,7 req/s), zero não-200.** Nenhum 429/401/403.
A latência **caiu** ao longo do teste (p50 de 275 ms para ~100 ms) — CDN aquecendo,
não throttle. O `MIN_FETCH_GAP_S = 0.15` e `CONCURRENCY = 4` do scanner são
conservadores por ~40× em relação ao que o Yahoo aceitou aqui.

## 5. `/v7/finance/spark` — vários símbolos em uma requisição

| Lote | Status | Retorno |
|---|---|---|
| 10 | 200 | 10 símbolos, 36,7 KB, 287 ms |
| 15 | 200 | 15 símbolos, 47,8 KB, 280 ms |
| 20 | 200 | 20 símbolos, 62,6 KB, 285 ms |
| 25 / 40 / 74 | **400** | `Number of symbols needs to be less than or equal to 20` |

Teto rígido de **20 símbolos**. Devolve **só `close`** (sem OHLC, sem volume):
serve para gatilho de *preço cruzou nível*, **não** serve para ATR, corpo de candle,
volume ou qualquer coisa que a F2/F3 precise. 74 ativos = **4 requisições** em vez de
74 — redução de 18× no número de chamadas, para um subconjunto do dado.

## 6. Custo real no volume do Radar

Premissa: pregão 10:00–17:59 (o gate `in_market_hours` de `agent.py:65`), laço já
existente de 300 s → **96 rodadas/dia**, 22 pregões/mês, 65 ativos servidos.

| Cenário | Req/rodada | Req/mês | Tráfego/mês | Parede/rodada |
|---|---|---|---|---|
| `15m × 1d`, 1 req/ativo | 65 | **137.000** | 0,5 GB | 1,5–2,7 s |
| `1m × 1d`, 1 req/ativo | 65 | 137.000 | **4,9 GB** | 1,5–2,7 s |
| `15m`, via `spark` (só close) | 4 | **8.400** | 0,05 GB | < 1 s |

**Custo Railway incremental (preços de `railway.com/pricing`: egress US$ 0,05/GB;
CPU US$ 0,0000077/vCPU·s ≈ US$ 0,028/vCPU·h; RAM US$ 0,014/GB·h; volume
US$ 0,00000006/GB·s ≈ US$ 0,16/GB·mês):**

- **Rede: ~US$ 0.** O download do Yahoo é *ingress*; a Railway cobra *egress*, e o
  que sai são os GETs (bytes irrisórios).
- **CPU/RAM: < US$ 1/mês** (estimativa, não medição). A rodada gasta 1,5–2,7 s quase
  inteiramente em `await` de rede; o parse de 65×29 velas é trivial. No cenário `1m`
  o parse é ~14× maior (65×418 velas) e ainda assim marginal.
- **Volume: irrelevante.** 15m com retenção de 1 mês = 617 velas × 149 B × 65 ativos
  ≈ **6 MB** (≈ US$ 0,001/mês). 1m com 7 dias ≈ 27 MB.

**Conclusão de custo: o dado intraday do Yahoo custa ~US$ 1/mês de infraestrutura.**
O custo relevante desta frente **não é o dado** — é (a) IA, se o timing disparar mais
chamadas de LLM, e (b) o risco de bloqueio, que não tem preço porque não tem contrato.

### O número que escolhe a política de retenção (escrita em SQLite)

`candle_cache` guarda a série **inteira como um blob JSON por chave** e **regrava o
blob todo** a cada atualização (`_db_put`). Medido no formato do app: **149 B/vela**.

| Política | Blob por ativo | Escrita/dia (65 ativos × 96 rodadas) |
|---|---|---|
| `15m`, retenção 1 dia (29 velas) | 4,2 KB | **26 MB/dia** |
| `15m`, retenção 1 mês (617 velas) | 90 KB | **561 MB/dia** |
| `5m`, retenção 1 mês (1.821 velas) | 265 KB | **1,65 GB/dia** |
| `1m`, retenção 7 dias (2.865 velas) | 414 KB | **2,58 GB/dia** |

Não é custo de dinheiro (o volume é barato) — é **desgaste e latência de escrita no
volume único da Railway**, com WAL por cima. Escolher `5m` com retenção de um mês no
desenho de hoje significa 1,65 GB/dia de reescrita para adicionar 65×78 velas.

### Bloqueador medido no caminho atual

`yahoo.get_history` monta cada vela com `date = strftime("%Y-%m-%d", gmtime(t))` e
`candle_cache.merge_candles` indexa **por essa data**. Medido:

| Requisição | Velas recebidas | Chaves após o merge | Colapso |
|---|---|---|---|
| `15m × 1mo` | 617 | 22 | **sim** |
| `5m × 1mo` | 1.821 | 22 | **sim** |
| `1m × 7d` | 2.865 | 7 | **sim** |
| `1d × 2y` | 500 | 500 | não |

Passar intraday pelo caminho de hoje **descarta 96% dos candles em silêncio** e
ainda usa `gmtime` (UTC) num timestamp de bolsa em BRT. A chave do cache já segmenta
por intervalo (`símbolo@intervalo`) — isso está certo —, mas a chave **da vela**
precisa virar o timestamp completo. É mudança de contrato do `merge_candles`, com
teste próprio, antes de qualquer outra coisa da F1.

## 7. Alternativas — o que sobra depois do custo real

| Fonte | Intraday `.SA`? | Custo | No volume do Radar | Veredito |
|---|---|---|---|---|
| **Yahoo `/v8/chart`** (atual) | Sim, 1m–90m | **US$ 0** | 137k req/mês, folga de ~40× na taxa | **Sustenta.** Sem contrato, sem SLA; ToS veda uso comercial/redistribuição |
| **brapi Free** | **Não** (só `1d`) | R$ 0 · 15k req/mês · 1 ticker/req | 137k req/mês = **9× a cota** | Não serve (nem por intraday, nem por cota) |
| **brapi Startup** | **Não** (só `1d`) | R$ 99,99/mês (anual) | — | Não serve |
| **brapi Pro** | **Sim** (1m–90m), delay ~5 min | **R$ 116,66/mês** (anual) / R$ 166,66 (mensal) · 500k req/mês · 20 tickers/req | 4 req/rodada → **8,4k/mês = 1,7% da cota** | **Fallback viável.** Sobra folga até para laço de 1 min |
| **Twelve Data** | **Não** — BVMF é *EOD only* | — | — | Descartado |
| **EODHD "EOD+Intraday Extended"** | Sim (1m/5m/1h), 15 min de atraso | US$ 29,99/mês · 100k chamadas/dia | 6,2k/dia = 6% da cota | Candidato **não validado** — cobertura intraday de `.SA` exige trial |
| **Alpha Vantage** | Não documentado para `.SAO` | — | — | Não validado; a doc de intraday só exemplifica mercados US/EU/Ásia |
| **bolsai** (já usada em fundamentos) | **Não sei** — site bloqueou o fetch (403) | chave já existe no Railway | — | **Vale uma pergunta ao fornecedor** antes do ADR: se tiver intraday, é a de menor atrito |
| **B3 UP2DATA / vendors licenciados** | Sim, oficial | milhares de R$/mês + contrato de redistribuição | — | Só se o produto virar sinal operacional de verdade |

**Veredito.** Tecnicamente, **o Yahoo sustenta o Radar intraday com folga** — 1.300
requisições em 17 s sem um único 429, contra as 65 requisições a cada 5 min que o
produto precisa. E **do IP de produção é ainda melhor**: 65 ativos em 0,45 s, p50 de
50 ms, zero erro (§8). Nenhuma alternativa gratuita entrega intraday de B3: a única
paga barata e confirmada é a **brapi Pro a R$ 116,66/mês**, que no volume do Radar
usa 1,7% da cota. Então a decisão do ADR **não é técnica nem de custo, é de risco**:
US$ 0 sem contrato e contra os termos de uso, versus R$ 117/mês com contrato.
Com o orçamento de US$ 0 aprovado, o desenho que preserva a saída é **Yahoo primário
+ provedor plugável** — a mesma postura que `options_provider_yahoo.py` adotou depois
do 401. Trocar de fonte precisa ser configuração, não refatoração.

## 8. O IP da Railway — medido de dentro do container

Executado em 2026-07-31 00:28Z (21:28 BRT, **pregão fechado**) via
`scripts/medir-yahoo-na-railway.sh`, que injeta `scripts/medicao_railway_payload.py`
por `railway ssh`. Sem deploy, sem arquivo no container, sem escrita em `/data`.
Escalonado, com **teto de 300 requisições** e **abort no primeiro 429/401/403**.
Saída bruta em `docs/evidencia-railway-bloqueio-20260730.txt`.

**IP de saída: `152.55.177.38` · região `sfo` · cookie e crumb obtidos normalmente
pela sessão do cliente real (`app.yahoo`).**

| Degrau | Carga | Resultado |
|---|---|---|
| 1 | 1 requisição (`15m × 1d`) | 200, 29 velas, **50 ms** |
| 2 | 5 sequenciais | p50 **50 ms**, máx 64 ms |
| 3 | 65 ativos, conc=4 (a de hoje) | **65/65** em **0,89 s** · p95 82 ms |
| 4 | 65 ativos, conc=8 | **65/65** em **0,45 s** · p95 97 ms |
| 4 | 65 ativos, conc=16 | **65/65** em **0,26 s** · p95 79 ms |
| 5 | mais 1 rodada a conc=8 | **65/65** em **0,42 s** |

**266 requisições, zero não-200, 19 s.** Nenhum 429, 401 ou 403 — o mecanismo de
abort nunca disparou. `/api/health` respondeu 200 logo depois (`F9-20260728-07`).

**O IP de datacenter não é penalizado — é 3,5× mais rápido.** p50 de **50 ms** contra
173 ms do IP residencial, e a rodada completa do universo cai de 2,7 s para **0,45 s**.
A hipótese que motivava o teste está descartada: o `sfo` da Railway está perto da
infraestrutura do Yahoo, e o custo de rede que dominava a medição local some.

Consequências diretas para o ADR:

- O laço intraday de 5 min consome **0,45 s** de parede por rodada, 0,15% do intervalo.
- `CONCURRENCY = 4` e `MIN_FETCH_GAP_S = 0.15` do scanner podem subir com folga —
  conc=16 não produziu um único erro e foi 3,4× mais rápido que conc=4.
- A cicatriz do `README_FIX_YAHOO_401.md` era do endpoint `/v7/finance/options` **sem
  sessão**, não do IP. Com cookie+crumb, o `/v8/chart` passa limpo daqui.

**O que este teste NÃO prova:** o sustentado. O teto de 300 requisições gastou-se nos
degraus, sobrando **uma** rodada extra — o equivalente a ~4 rodadas do laço, não a um
pregão inteiro. As 1.300 requisições de endurance foram do IP residencial. Antes de
subir a concorrência em produção, vale uma execução longa observada pelo
`/api/obs/usage`, não uma rajada sintética.

## 9. O que ainda falta antes do ADR

1. **Atraso do feed** — o número decisivo, e o único que ainda não existe. A medição
   de 30/07 foi com pregão fechado: sei que o último candle é o das 17:00, não sei
   **quanto tempo depois do fato** ele aparece. Um feed com 15 min de atraso não
   sustenta "a condição de entrada ocorreu agora" em 5m. Agendado para **31/07,
   entre 10h e 17h BRT**:
   ```bash
   bash scripts/medir-yahoo-na-railway.sh atraso
   ```
   (15 requisições; o script avisa se estiver fora do pregão.)
2. **bolsai tem intraday?** Uma pergunta ao fornecedor decide se a alternativa paga
   já está contratada. Com orçamento de US$ 0 aprovado, isso importa menos como
   plano A e mais como plano B documentado.
