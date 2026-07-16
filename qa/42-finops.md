# qa/42 — Análise de FinOps · BolsIA

Data: 16/07/2026 · read-only, zero patch · produção `b3agente-production.up.railway.app`
Método: leitura de código + `railway variables` (nomes, valores nunca lidos) + `railway status`.

---

## 1. Veredito: onde o dinheiro está hoje

**O projeto tem exatamente UM custo em dólar: o container Railway (RAM/CPU alocados × tempo)
+ o volume. Mais nada.**

| Vetor | Custo hoje | Evidência |
|---|---|---|
| **LLM** | **ZERO** | `B3_MANAGED_LLM_KEY` **ausente** do Railway → `managed_config()` retorna None (`managed.py:26-28`) → 100% BYOK: cada usuário paga a própria chave. |
| **Yahoo Finance** | ZERO | Sem contrato, sem chave. Gratuito, rate-limited. |
| **usebolsai.com** | ZERO | Free 200 req/dia (`fundamentals.py:9`); `WARM_MAX_POR_RUN = 60` (`fundamentals.py:310`) → ~60/dia. Margem 3×. |
| **brapi.dev** | ZERO | Free tier, complementar (DY + 4 tickers). |
| **APNs (push)** | ZERO | Apple não cobra. |
| **Railway** | **ÚNICO custo** | Container 24/7, 1 worker, + volume. Valor só no dashboard. |

**Custo marginal por usuário novo hoje ≈ ZERO.** Isso é uma posição de FinOps invejável, e é
consequência direta de duas decisões: BYOK e o scanner determinístico. `plan.py:20-24` confirma
a intenção — todos os limites `None`, "hoje TODOS ilimitados (sem cobranca)".

---

## 2. O patch pedido ("agente só no horário da bolsa") economiza ZERO

Três razões independentes, cada uma suficiente:

1. **Já existe.** `if not kill_switch_on() and in_market_hours()` (`agent.py:221`). Provado em
   qa/41: das 00:57 às 10:00 BRT, todas as passadas com `usuarios=0` e `duracaoS: 0.0`.
2. **O scheduler não gasta.** Confirmado por varredura: `grep -rn "llm\.|import llm"` em
   `agent.py`, `radar_daily.py`, `analysis_outcomes.py`, `fundamentals.py` → **zero hits**.
   O laço NUNCA chama LLM. O gasto de LLM é 100% dirigido por request de usuário. Ponto forte
   do desenho — não há gasto de fundo.
3. **O Railway cobra alocação, não uso.** Um laço que acorda 288×/dia e mede `duracaoS: 0.0`
   não move a fatura. Você paga o container existir, não ele pensar.

**Risco ativo:** a única forma de o container deixar de custar fora do pregão é ligar Serverless
— o que **reintroduz o H1 descartado em qa/41**. O container dormiria de madrugada e o radar das
08:48 (pré-abertura, FORA do gate de pregão de propósito, `radar_daily.py:27`) não rodaria, pois
nada geraria o request para acordá-lo. Quebra a varredura diária para economizar centavos.
**Não fazer.**

---

## 3. A única economia real disponível hoje: RAM

Railway cobra RAM × tempo. Com **1 worker** (`Procfile:1`, `railway.json:5` — sem `--workers`),
tudo abaixo é RAM que você paga 24/7:

| Consumidor | RAM estimada | Teto? | file:line |
|---|---|---|---|
| Conexões SQLite thread-local | **até ~80 MB** (40 threads × ~2 MB page cache) | ❌ nunca fecham | `db.py:42-70` |
| `_SNAP_CACHE` (snapshots + indicadores, até 504 barras) | **~15–40 MB** (~90 MB se os 5 períodos forem usados) | ⚠️ implícito | `technical_snapshot.py:32` |
| `_CACHE` candle L1 (600 candles × ~180 KB/símbolo) | **~13 MB** (74 tickers) → ~72 MB no teto B3 | ❌ chaves nunca saem | `candle_cache.py:33` |
| `_DEEP_CACHE` | cresce **por dia, para sempre** | ❌ | `scan_deep.py:18,100` |
| `_SCAN_CACHE` | ilimitado, **chave do cliente** | ❌ | `scanner.py:65,305` |

Só **2 de 10** caches globais têm teto real (`RUN_HISTORY` 12, `obslog._buffer` 1000).

**1 worker é a decisão certa e deve ser mantida** — não por RAM, mas porque `scheduler_loop` sobe
no `@app.on_event("startup")` (`main.py:1103`): com N workers, **N schedulers em paralelo** →
N× Yahoo, radar concorrente, corrida de escrita no SQLite. Aumentar workers quebraria o produto,
não só a fatura.

---

## 4. Bomba-relógio: o dia em que `B3_MANAGED_LLM_KEY` for ligada

Hoje tudo abaixo é inofensivo (BYOK: o usuário paga). No instante em que a IA gerenciada for
ligada, o custo passa de **fixo** para **variável e sem teto** — com cinco defeitos ativos:

**4.1 `/api/scan/deep` fura a quota E o rate limit** — o mais grave.
`_ai_apply_managed` roda `check` **1× por request** (`main.py:638`), mas `_consume_ai()` roda
**1× por ticker** (`main.py:658`), e `run_deep` faz `asyncio.gather` de até `MAX_TOP_N = 10`
(`scan_deep.py:16,105`).
- Usuário com `count=19`, `quota=20`: check passa → dispara **10 chamadas** → termina em **29**.
- Rate limit 6/min registra **1 timestamp** para um burst de 10 → teto real **60 chamadas de
  LLM/min/usuário** ≈ **~420k tokens de input/minuto**.

**4.2 Zero teto global de gasto.** `metering` só escopa por `user_id` (`metering.py:27`). Nada
agrega. Sem kill-switch de custo, sem orçamento. N usuários = N × 20+/dia, ilimitado.

**4.3 O caminho que VOCÊ paga é o mais caro** (bug de custo real).
`_ai_apply_managed` recria a config sem `candlePeriod` (`managed.py:27-38`, `main.py:242`), e logo
depois o código lê `candlePeriod` da config **já substituída** (`main.py:719`, `:819`, `:882`) →
`normalize_period(None)` → `DEFAULT_PERIOD = "1y"` (`candles.py:30`). **Todo usuário de IA
gerenciada sempre manda 252 candles (~2.911 tok) mesmo tendo escolhido `1mo` (~411 tok).**
~7× mais input, na sua chave. `/api/scan/deep` não sofre disso (usa `body["period"]`).

**4.4 Zero prompt caching.** Nenhum `cache_control` (`llm.py:185`); `system` é `str`, não blocos —
nem seria possível marcar sem refatorar. Input domina output em 3–6×: o deep manda **~7,1k tok**
(1y) a **~12,9k tok** (2y) por ticker para no máximo 2,2k de saída.

**4.5 Sem cache de resposta em N2/N3.** Só o deep tem (`scan_deep.py:18`), e em memória. O mesmo
usuário pedindo o mesmo ticker 5× paga 5× ~7k tok — com `snapshotId` idêntico e `temperature=0.2`.
O `snapshotId` já existe e é a chave natural.

**4.6 Sem telemetria de tokens.** Nenhum caller lê `usage` da resposta. **Não dá para medir custo
real hoje** — é por isso que este relatório não traz números em dólar.

**Pior caso, um único POST:** topN=10 × 2y = **~129k tok in / ~22k tok out**, consumindo 1 slot
de rate limit.

---

## 5. Disponibilidade que vira custo (e ameaça o Operador)

**`_SCAN_CACHE` — OOM dirigido por endpoint sem autenticação.**
`scanner.py:226` monta a chave como `período + "|" + ",".join(tickers)`, e os tickers vêm do query
param `?tickers=` (`main.py:596`). O TTL só é checado na **leitura** (`scanner.py:229`) — nada
purga. `?tickers=PETR4,VALE3` e `?tickers=VALE3,PETR4` são **duas chaves** (ordem preservada):
N tickers → N! permutações, ~150 KB cada. `/api/scan` **não exige auth** (`main.py:588`,
`current_scope` → None sem token).

Cadeia: request anônimo → RAM enche → OOM → restart → `restartPolicyMaxRetries: 3`
(`railway.json`) → **após 3 OOMs o serviço fica fora do ar** → o Operador para de proteger.

Isto é a mesma classe de risco da §9 de qa/41: *proteção que depende de um container derrubável
por um GET anônimo não protege.* Registrar como risco de produto, não só de infra.

---

## 6. Desperdício de CPU: event loop bloqueado (CPU paga, parada)

`_conn = db.shared()` é `sqlite3` **síncrono** e é chamado direto de rotas `async def`.
Pior caso: `_enrich_fundamentos` (`main.py:554`) é **síncrona**, chamada de dentro do
`async def scan` (`main.py:596`), e faz `fundamentals.get_cached` para **cada um dos 74
resultados** → **74 leituras SQLite bloqueantes no event loop**, congelando todo o resto.
Com 1 worker, não há outro processo para atender enquanto o loop está parado.

A disciplina existe no repo (`main.py:580`, `:762` e `fundamentals.py:358` usam `asyncio.to_thread`
corretamente) — só não foi aplicada aqui. Também: `list_server_users` (`agent.py:183`) faz full
table scan (`kv` só tem PK, `db.py:106`).

---

## 7. Rede: amplificação sob rate-limit

- Volume/dia ≈ `74 (radar) + 32×U (agente) + U×T (outcomes)`. Com U=10, T=5: **~450/dia**;
  **até ~1.800** se o Yahoo devolver 429/401.
- `yahoo._yfetch` (`yahoo.py:73`): `retries=3` → 4 tentativas; em 401 refaz sessão (+3 requests) →
  **até ~16 requests HTTP por fetch lógico**.
- `get_quotes` (`yahoo.py:157-163`): batch falha → fallback 1-por-ticker, cada um com 4 tentativas.
  Um 429 num batch de 10 → **até 40 requests**, exatamente quando o Yahoo pede para parar.
- `analysis_outcomes` (`analysis_outcomes.py:295`) usa `yahoo.get_history` cru, **sem cache e sem
  dedup entre usuários**: 50 usuários com PETR4 → **50 downloads idênticos** de 6 meses.
  O(U×T) onde deveria ser O(T).
- **Gates diários em memória** → todo redeploy re-executa o job: `analysis_outcomes.LAST_EVAL`
  (`analysis_outcomes.py:53`) e `fundamentals.LAST_WARM` (`fundamentals.py:302`). `radar_daily`
  persiste no kv e acertou (`radar_daily.py:82`); os outros dois copiaram o padrão pela metade.
  10 deploys/dia = 10× a rede desses jobs — e o warm da bolsai (60/run) × 4 deploys **estoura o
  free tier de 200/dia**.

---

## 8. Storage: cresce para sempre, nunca encolhe

- **`history` sem cap nenhum** (`store.py:331,356`) — todos os vizinhos têm: events 50, analyses
  40, equitySnapshots 400, agentLog 200, analysisOutcomes 500+180d. Omissão evidente.
  ~0,5–1 KB/usuário/dia, monotônico.
- **`candle_cache` sem TTL e sem poda** (`candle_cache.py:70`) — `_MAX=600` limita candles POR
  LINHA, não o nº de linhas. Nenhum `DELETE FROM candle_cache` no repo. Cada símbolo já carregado
  fica no volume para sempre, inclusive deslistados e erros de digitação. ~54 KB/símbolo →
  ~4 MB (universo) → ~21 MB (teto B3).
- **Zero VACUUM** (só `journal_mode=WAL`, `db.py:33`) → arquivo é high-water-mark, nunca encolhe.
  Agrava: `kv_set` reescreve o blob JSON inteiro a cada mutação (`db.py:138`); o radar reescreve
  ~4 MB/dia.

**Volume não é gargalo de custo hoje** (ordem de MB), mas são três vetores monotônicos sem
contramedida e sem meio de recuperar espaço.

---

## 9. Recomendações priorizadas

**Fazer agora (custo/risco real hoje):**
1. **Autenticar ou capar `/api/scan`** — OOM anônimo derruba o Operador (§5). É o único item que
   hoje ameaça produto e fatura ao mesmo tempo. Teto no `_SCAN_CACHE` + chave normalizada
   (`sorted(uni)`) mata as N! permutações.
2. **`_enrich_fundamentos` → `asyncio.to_thread`** (§6) — 74 leituras bloqueantes por Radar.
3. **Persistir os gates diários** de `analysis_outcomes` e `fundamentals` no kv, copiando
   `radar_daily.last_run_date` (§7) — hoje cada deploy paga o job de novo e ameaça o free tier
   da bolsai.

**Fazer ANTES de ligar `B3_MANAGED_LLM_KEY` (bloqueadores):**
4. **Mover `_consume_ai` para dentro do gate, ou re-checar no loop** do `/api/scan/deep` (§4.1).
5. **Teto global de gasto** + telemetria de `usage` (§4.2, §4.6) — hoje é impossível medir.
6. **Preservar `candlePeriod` na config gerenciada** (§4.3) — 7× de input na sua chave.
7. Cache de resposta por `snapshotId` em N2/N3 (§4.5).

**Não fazer:**
- ❌ Serverless / dormir o container fora do pregão — reintroduz o H1 (§2).
- ❌ Cortar/gatear o laço do agente — já gateado, custo 0.0s, zero LLM (§2).
- ❌ Aumentar `--workers` — N schedulers em paralelo quebram o produto (§3).

**Não medido:** valor em dólar (sem telemetria de tokens e sem acesso a billing pela CLI);
limites de RAM/CPU do container e tamanho do volume (só no dashboard); nº real de usuários.

---

## 10. Aplicado (16/07/2026) — 6 dos 7 itens

Suíte: **291 passed** (baseline era 274+1 falha pré-existente). Endpoints exercitados de verdade
com TestClient (não só funções isoladas).

| # | Item | Onde | Estado |
|---|---|---|---|
| 1 | `_SCAN_CACHE`: teto (`SCAN_CACHE_MAX=16`) + chave com tickers **ordenados** | `scanner.py:65-90` | ✅ |
| 2 | `_enrich_fundamentos` async via `to_thread` (+ `radar_daily.get_stored`/`store_result`) | `main.py:573-578,605-615` | ✅ |
| 3 | Gates diários **persistidos** no kv (padrão `radar_daily`) | `analysis_outcomes.py`, `fundamentals.py` | ✅ |
| 4 | Cota reserva `custo=n` no `/api/scan/deep` | `metering.py:check`, `main.py:_ai_apply_managed` | ✅ |
| 5 | Teto **global** de gasto (`B3_MANAGED_GLOBAL_DAILY_CAP`, default None) + telemetria de tokens + `GET /api/obs/usage` | `metering.py`, `managed.py`, `llm.py`, `main.py` | ✅ |
| 6 | `candlePeriod` preservado na config gerenciada | `main.py:_ai_apply_managed` | ✅ |
| 7 | Cache de resposta N2/N3 por `snapshotId` | — | ❌ **não aplicado** |

**Decisões de projeto tomadas no caminho (ficam registradas):**

- **`/api/scan` NÃO foi autenticado.** É público por design (`current_scope` → None sem token:
  "rotas de dados funcionam sem login"); exigir auth quebraria o app para deslogado e mexeria em
  `web/src/` (proibido). O teto + a chave normalizada **matam o vetor de OOM** sem tocar no
  contrato — as N! permutações viram 1 entrada. Autenticar continua sendo defesa em profundidade
  desejável, mas é decisão de produto.
- **O `custo` entra na COTA, não no rate limit.** Reservar 10 slots num teto de 6/min bloquearia
  todo `/api/scan/deep`. O rate existe para impedir martelar (1 por request); quem protege o
  bolso é a cota. `custo=1` (default) é matematicamente idêntico ao comportamento anterior.
- **Teto global default = None (ilimitado).** Aditivo: sem a env, produção não muda.
- **Bug de teste pré-existente corrigido:** `test_scheduler_alimenta_historico_de_passadas`
  falhava na suíte completa **já no `main`** (274 passed + 1 failed, verificado com `git stash`).
  `LAST_USER_RUN` é global do módulo e `test_agent.py` roda o mesmo scheduler com o mesmo uid →
  o resultado dependia da ORDEM da suíte. `clear()` nos dois. Não é bug de produção (lá cada boot
  começa com o dict vazio).

### Item 7 — por que NÃO foi aplicado

`analyze_structured(config, skill, profile, account, ticker, context, modo)`: a resposta depende
da **skill** (editável pelo usuário), do **profile** e do **account**. Cachear por
`(ticker, snapshotId, modo)` — o padrão do `_DEEP_CACHE` atual — **vazaria análise personalizada
entre usuários**. Uma chave correta precisa incluir o `scope` + um hash de
`(skill, profile, account, model)`, e isso é decisão de design, não fix mecânico.

Além disso, o ganho hoje é do **usuário** (BYOK), não do dono: com a IA gerenciada desligada, este
item não economiza um centavo seu. Fica como pendência com a chave a definir.

**Achado adjacente (novo, não corrigido):** o `_DEEP_CACHE` existente (`scan_deep.py:37`) já tem
chave `(ticker, period, snapshotId, modo)` **sem `profile`**, e `analyze_deep` **recebe** profile.
Dois usuários com perfis diferentes podem compartilhar a mesma resposta. Vale investigar em frente
própria — é privacidade, não custo.
