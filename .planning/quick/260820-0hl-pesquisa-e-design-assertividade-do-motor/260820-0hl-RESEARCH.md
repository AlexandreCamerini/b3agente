# Pesquisa — Assertividade do motor de trading do Boris+

**Data:** 2026-08-20
**Domínio:** motor determinístico de setups/plano operacional + loop de autoavaliação (`analysis_outcomes`)
**Confiança global:** ALTA no diagnóstico de código e de metodologia · **BAIXA** em qualquer conclusão sobre a qualidade preditiva do motor (amostra insuficiente — ver §1)
**Escopo:** pesquisa. Nada foi implementado, nenhum arquivo do produto foi alterado.

---

## TL;DR para decisão

1. **A pergunta "o motor stopa mais do que alveja?" não pode ser respondida hoje com os dados do produto.** A base local tem 57 registros que colapsam em **11 planos distintos**, dos quais 8 têm desfecho. [VERIFIED: consulta SQL em `server/data/b3_agente.db`]
2. **Mas a medição está quebrada de um jeito que fabrica stops.** O `analysis_outcomes` avalia um trade que o motor **nunca propôs**: ele ancora o preço de referência no *close* do dia da análise e ignora o **gatilho de entrada**. Reavaliando os mesmos 11 planos com o gatilho correto, o placar muda de **5 stop × 3 alvo** para **3 stop × 3 alvo + 3 que nunca acionaram**. [VERIFIED: reexecução com candles reais do Yahoo]
3. **E o painel "Eficiência da IA" reporta um número falso na direção oposta.** Nos mesmos dados, a metodologia atual produz **expectância +2,56R com n=44**; a metodologia correta produz **0,00R com n=6**. O painel diria "amostra suficiente, edge forte" onde não há edge nenhum. [VERIFIED: cálculo reproduzível]
4. **`n` está inflado por duplicação.** Um mesmo plano determinístico foi gravado até **24 vezes em 48 minutos**. `MIN_N=10` é atingido por 1 observação real. [VERIFIED]
5. **Para ação (não opção), o motivo do fechamento não é persistido.** `store.sell()` não tem parâmetro `motivo` — só `origem`. Não existe forma de calcular taxa stop×alvo a partir do histórico de trades. [VERIFIED: `server/app/store.py:621`]
6. **TradingView está fora.** Não há API pública de dados e o ToS proíbe explicitamente scraping **e** uso non-display (incluindo "algorithmic decision-making" e "risk management programs"). [CITED: tradingview.com/policies §3]

---

## 1. Dados reais de outcomes (`analysis_outcomes`)

### 1.1 O que existe no banco

Banco consultado: `server/data/b3_agente.db` (caminho default de `db.default_db_path()`, `server/app/db.py:25-36`).

```
942 chaves kv · 71 escopos de usuário
analysisOutcomes: 1 chave, escopo ANÔNIMO (user_id=None) · 57 registros · 27.684 bytes
analysisOutcomesLastRun: "2026-08-16"
```

| Campo | Distribuição |
|---|---|
| `resultado` | **`pendente`: 57 · resolvidos: 0** |
| Período | 2026-08-03 → 2026-08-15 |
| `tipo` | `n1`: 57 (nenhum N2) |
| `modo` | `estudo`: 45 · `operador`: 12 |
| `modelo` | `anthropic:claude-haiku-4-5`: 57 |
| `confianca` | `moderada`: 57 (nenhuma variação → calibração impossível) |
| `regime` | `None`: 50 · `tendencia_alta`: 7 (qa/44 é recente; 88% dos registros são pré-B) |
| Tickers | 6 (FLRY3, GOAU4, RECV3, SANB11, TIMS3, UGPA3) |

O cache admin confirma o mesmo estado: `analytics.db → admin_cache['ia_eficiencia']` = `{"totalAnalises": 57, "avaliadas": 0, "pendentes": 57, "taxaAcerto": null, ...}`. [VERIFIED]

**Trades reais:** 71 escopos com `history`; **1 escopo não-vazio, 3 eventos, todos `COMPRA`, nenhuma venda**. `automacao_resumo` no cache admin: `{"totalOrdens": 3, "porOrigem": {"desconhecida": {...}}}`. Cobertura de correlação análise↔ordem: **0,0%**. [VERIFIED]

> **Portanto: não há uma única operação fechada por stop ou por alvo no histórico de carteira.** A taxa perguntada não existe nos dados de trade.

### 1.2 Duplicação — `n` é ficção

Os 57 registros correspondem a **13 combinações (ticker, setup, stop, alvo)** e a **11 planos distintos por dia**:

| Ticker | Setup | Registros | Janela |
|---|---|---:|---|
| TIMS3 | Setup 9.2 (baixa) | **24** | 2026-08-05 15:15 → 16:03 (48 min) |
| GOAU4 | Rompimento com volume (alta) | 9 | 08-03 22:43 → 08-04 05:27 |
| GOAU4 | Pullback à média (alta) | 5 | 08-15 00:22 (mesmo minuto) |
| TIMS3 | Inside Bar (baixa) | 4 | — |
| RECV3 | Máx/Mín LW 9.4 (alta) | 4 | mesmo minuto |
| FLRY3 | Setup 9.3 (alta) | 4 | 2 min |
| SANB11 | Máx/Mín LW 9.4 (baixa) | 3 | mesmo minuto |
| UGPA3 | IFR2 (alta) | 2 | mesmo minuto |
| TIMS3 | Reversão de sobrevenda | 1 | — |
| FLRY3 | Setup 9.2 (alta) | 1 | — |

**Causa raiz** (`server/app/scan_deep.py:19,52-62`): `_DEEP_CACHE` é **em memória** e a chave é `(ticker, period, snapshotId, modo, leitor_fp)`. Cada restart do processo, cada troca de modo Estudo↔Operador e cada perfil/modelo/keySource diferente gera um cache miss → `deep_call` roda → `analysis_outcomes.registrar` grava **de novo o mesmo plano determinístico**.

Isso **não é artefato de dev**. `compute_stats_all_users` (`analysis_outcomes.py:235-242`) concatena todos os escopos sem deduplicar. Em produção, N usuários com perfis diferentes analisando o mesmo ticker no mesmo dia geram N registros idênticos do mesmo plano. `MIN_N = 10` (`analysis_outcomes.py:34`) é ultrapassado por **uma** observação independente. [VERIFIED]

### 1.3 Resolução real — eu resolvi os 57 pendentes com candles de verdade

Rodei `analysis_outcomes._avaliar_entry` (a função pura de produção, sem alterá-la) contra candles diários reais do Yahoo (`app.yahoo.get_history`, `rng="3mo"`, último candle 2026-08-18).

**Resultado pela metodologia atual do app:**

```
{'stop': 12, 'prazo_incompleto': 45}
R médio: -1.0 | soma: -12.0 | n: 12
```

**12 stops, 0 alvos — 100% de stop.** Mas esses 12 registros são **3 planos distintos**, e um deles (SANB11) *nunca teve o gatilho acionado*. [VERIFIED]

**Estendendo para a janela parcial (todos os 11 planos, contando o primeiro toque em stop ou alvo mesmo antes de fechar os 10 pregões):**

| Ticker | Data | Lado | Setup | Pregões | Primeiro toque |
|---|---|---|---|---:|---|
| SANB11 | 08-03 | V | Máx/Mín LW 9.4 | 11 | **stop** (D+1) |
| GOAU4 | 08-03 | C | Rompimento c/ volume | 11 | **stop** (D+6) |
| GOAU4 | 08-04 | C | Rompimento c/ volume | 10 | **stop** (D+5) |
| TIMS3 | 08-05 | V | Setup 9.2 (baixa) | 9 | alvo (D+6) |
| TIMS3 | 08-06 | V | Inside Bar (baixa) | 8 | nada ainda |
| TIMS3 | 08-06 | C | Reversão de sobrevenda | 8 | **stop** (D+3) |
| RECV3 | 08-07 | C | Máx/Mín LW 9.4 | 7 | alvo (D+1) |
| FLRY3 | 08-10 | C | Setup 9.3 (alta) | 6 | nada ainda |
| FLRY3 | 08-10 | C | Setup 9.2 (alta) | 6 | **stop** (D+2) |
| UGPA3 | 08-11 | C | IFR2 (alta) | 5 | alvo (D+3) |
| GOAU4 | 08-15 | C | Pullback à média | 2 | nada ainda |

**Placar pela metodologia atual: 5 stop · 3 alvo · 3 indefinidos.** [VERIFIED]

### 1.4 Segmentação pedida (setup / confluência / R:R)

- **Por setup:** ver tabela acima. Todo setup tem n ∈ {1, 2}. **Nenhuma célula chega perto de `MIN_N=10`.** Não existe base para dizer "o setup X stopa mais que o Y".
- **Por faixa de confluência:** **impossível.** `analysis_outcomes.registrar` (`analysis_outcomes.py:60-100`) grava `setup` (nome) mas **não grava `confluencia`**. O campo não existe no registro nem no CSV de export (`to_csv`, `analysis_outcomes.py:248-251`). **Gap de instrumentação — bloqueia a pergunta.** [VERIFIED]
- **Por R:R proposto:** também não é gravado, mas é derivável dos campos existentes. Reconstruído abaixo — e é onde está o problema.

### 1.5 Limitação honesta

Este é o banco **local de desenvolvimento**. Produção roda no Railway com volume `/data` e `B3_DB_PATH=/data/b3_agente.db` (`GUIA-OPERACAO.md:51` — "Nunca remova esse volume"), então **os dados de produção persistem e podem ser maiores que estes**. Não consultei produção.

**Ação recomendada antes de fechar o ADR:** rodar a mesma extração contra o banco de produção via `railway ssh` usando `/opt/venv/bin/python3` (o `python3` do PATH não tem as libs — ver memória `railway-ssh-python`). Se o volume de produção também estiver na casa das dezenas, a conclusão de §1 vale para o produto inteiro.

---

## 2. Pipeline determinístico ponta a ponta

### 2.1 Mapa (arquivo:linha)

| Etapa | Onde | O que faz |
|---|---|---|
| **Detecção de setup** | `setups.py:483-523` `detect_setups()` | Avalia 23 detectores (7 clássicos + 16 BR) |
| **Pontuação de confluência** | `setups.py:68-71` `_confluencia()` | `round(100 * Σpeso_ok / Σpeso)` — percentual **ponderado de checklist** |
| **Critério + peso** | `setups.py:61-65` `_crit()` | `obrigatorio=True` = critério que define o setup |
| **Corte de confluência** | `setups.py:480` `MIN_CONFLUENCIA = 50` | + `setups.py:501-506`: todos os obrigatórios têm de estar `ok` |
| **Gatilho / invalidação / alvo do setup** | `setups.py:214-220` `_mk()` | Cada detector define `gatilho`, `invalidacao`, `alvoSugerido` |
| **Projeção de alvo do setup** | `setups.py:204-211` `_alvo_rr()` | **2× o risco** a partir do gatilho; fallback 2×ATR |
| **Seleção do universo (Radar)** | `regime.py:212-262` `ranquear()` | Ordena por (tier de regime, momentum relativo percentil, gatilho alinhado, −confluência) |
| **Classificação de regime** | `regime.py` `classificar()` | SMA200/ADX14/DI±/SMA50 → `tendencia_alta \| tendencia_baixa \| lateral \| indefinido` |
| **Plano operacional** | `setups.py:575-654` `plano_operacional()` | Entrada, stop, alvo1, alvo2, rr1, rr2, riscoPorAcao |
| **Seleção do plano** | `setups.py:657-676` `plano_do_resultado()` | Lado dominante + preferência por setup com níveis executáveis |
| **Sizing** | `web/src/finance.js:107-121` `sizingPlano()` | Fixed-fractional, `pct` default 1%, teto 5%, lote de 100 |
| **Timing intraday** | `timing.py`, `timing_watch.py` | Tríade temporal (plano diário × barra 15m fechada × estado armado/gatilho/esticado) |
| **Execução simulada (saída)** | `agent.py:821-856` | `breach_stop` / `hit_alvo` / trailing / alvo dinâmico |
| **Trailing stop** | `agent.py:366-428` | 3 modos (pct / atr / estrutura), invariante: **stop só sobe** |
| **Alvo dinâmico** | `agent.py:444-478` | `MAX_ALVO_EXTENSOES=2`, `ALVO_ATR_MULT=1.5`, `RR_MINIMO=1.5` |
| **Registro para autoavaliação** | `main.py:1311-1327` (N1), `main.py:1416-1432` (N2) | Grava a análise em `analysisOutcomes` |
| **Resolução do outcome** | `analysis_outcomes.py:289-325` `_avaliar_entry()` | Barreira tripla: stop / alvo / 10 pregões |

### 2.2 Geometria do plano — `plano_operacional`

```
risco       = |gatilho − stop|                                    setups.py:597
entrada     = gatilho  (ou close, se já rompido dentro da zona)   setups.py:602-612
zona de perseguição: excedente > 0,5 × risco  ⇒  NÃO OPERAR       setups.py:560, 608-610
risco_real  = |entrada − stop|                                    setups.py:617
alvo1       = entrada ± risco_real          ← EXATAMENTE 1R       setups.py:623
alvo2       = alvoSugerido (2R do gatilho) ou fallback 2×risco    setups.py:614-616
rr2 < RR_MINIMO (1,5) ⇒ NÃO OPERAR                                setups.py:635-637
```

Guardas de coerência que já existem e são boas (`setups.py:599-600, 618-632`, todas comentadas como achados de qa/39): stop do lado certo do gatilho, alvo do lado do lucro, risco não-nulo, alvo > 0. Nada a reclamar aqui.

### 2.3 Regra de R:R — onde ela mora hoje

Existem **três constantes Python independentes** com o valor 1.5:

| Constante | Arquivo:linha | Aplicada em |
|---|---|---|
| `skill_ref.RR_MIN = 1.5` | `skill_ref.py:30` | prompts da LLM (`skill_ref.py:45,107`), `llm.py:1093,1135`, `kb.py:928,933`, `conceitos.py:359` |
| `setups.RR_MINIMO = 1.5` | `setups.py:559` | gate do plano determinístico (`setups.py:635`) |
| `agent.RR_MINIMO = 1.5` | `agent.py:446` | trava da extensão de alvo dinâmico (`agent.py:475`) |

E **sete literais "1,5" hardcoded no front**, fora de qualquer constante:
`web/src/copy.js:134`, `web/src/copy.js:147`, `web/src/catalog.js:45`, `web/src/catalog.js:100`, `web/src/catalog.js:147`, `web/src/App.jsx:4009`, `web/src/App.jsx:4347`.

O único teste que trava o valor é `server/tests/test_auditoria_prompts.py:167-172`, e ele **só verifica `skill_ref`** — não verifica `setups.RR_MINIMO` nem `agent.RR_MINIMO`, nem os literais do front. [VERIFIED]

**Contexto histórico:** o comentário em `conceitos.py:354-356` diz textualmente *"o R:R mínimo já viveu como '1,5' em quatro lugares e a auditoria de 2026-07 existiu para matar essa classe de divergência"*. A auditoria resolveu **o texto didático** (que passou a ler de `skill_ref`); **os dois motores e o front continuam com o valor duplicado**. Mudar o limiar hoje exige editar 10 lugares. [VERIFIED]

### 2.4 O defeito central — a medição avalia um trade que o motor nunca propôs

`main.py:1313-1325` grava:

```python
stop  = plano.get("stop")     # invalidação do setup — ancorada no candle do GATILHO
alvo  = plano.get("alvo1")    # 1R a partir da ENTRADA
preco = snap.get("close")     # ← preço de fechamento do dia da análise
```

`plano["entrada"]` — que **existe** e é o gatilho — **não é gravado**.

`_avaliar_entry` (`analysis_outcomes.py:289-325`) então usa `precoNaAnalise` como preço de entrada e mede `risco = abs(preco0 - stop)`. Três problemas encadeados:

**(a) O gatilho é ignorado.** Se o setup está *armado* (gatilho ainda não rompido — condição explícita de vários detectores: `setups.py:377, 459`), o close fica **entre** o gatilho e a invalidação. A avaliação simula uma entrada num preço que o plano não autoriza, com o stop colado. Medindo as distâncias reais dos 13 planos:

| Ticker | Setup | dist. ao STOP | dist. ao ALVO | razão |
|---|---|---:|---:|---:|
| SANB11 | Máx/Mín LW 9.4 (baixa) | **0,59%** | 4,39% | 7,5× |
| RECV3 | Máx/Mín LW 9.4 (alta) | **0,60%** | 2,58% | 4,3× |
| TIMS3 | Setup 9.2 (baixa) | **0,79%** | 3,54% | 4,5× |
| TIMS3 | Setup 9.2 (baixa) | **0,85%** | 3,49% | 4,1× |
| TIMS3 | Setup 9.2 (baixa) | **0,90%** | 3,44% | 3,8× |
| TIMS3 | Setup 9.2 (baixa) | **0,95%** | 3,39% | 3,6× |
| TIMS3 | Reversão de sobrevenda | 1,85% | 3,33% | 1,8× |
| FLRY3 | Setup 9.2 (alta) | 1,93% | 4,92% | 2,6× |
| GOAU4 | Pullback à média | 3,37% | 5,00% | 1,5× |
| UGPA3 | IFR2 (a mercado) | 4,07% | 4,07% | 1,0× |
| TIMS3 | Inside Bar (baixa) | 4,55% | 5,83% | 1,3× |
| GOAU4 | Rompimento c/ volume | 4,64% | 5,18% | 1,1× |
| FLRY3 | Setup 9.3 (alta) | 9,60% | 17,84% | 1,9× |

Mediana: stop a **1,85%**, alvo a **4,07%**. Mas **6 de 13 planos têm o stop a menos de 1% do preço de referência**, com o alvo 3,4–4,4% longe. Num papel da B3 com ATR diário típico de 1,5–2,5%, uma barreira de 0,6% em 10 pregões é atingida quase com certeza. **Esses stops não medem o motor; medem o ruído entre o close e o gatilho.** [VERIFIED: cálculo sobre os registros reais]

**(b) O alvo medido é o `alvo1` (1R), não o `alvo2` que passa pelo gate de R:R.** O produto promete R:R ≥ 1,5:1 no alvo final e mede a eficiência contra uma barreira de 1:1. `rMultiple` em sucesso fica limitado ao que a âncora deixar; em stop dá **exatamente −1,0** sempre. A assimetria que o motor foi desenhado para explorar **não entra na estatística**.

**(c) Empate intrabar sempre vira stop.** `analysis_outcomes.py:306` (`if bateu_stop: ... break` antes de `bateu_alvo`) e `agent.py:821-822` (`breach_stop` avaliado antes de `hit_alvo`). O comentário chama de *"cenário conservador"* — e é conservador, corretamente. Mas com candles **diários**, um candle cujo `low ≤ stop` **e** `high ≥ alvo` sempre é contado como stop. Com barreiras próximas (§a), isso acontece com frequência não-desprezível e é **viés estrutural negativo**, não medição. [VERIFIED]

### 2.5 Prova numérica do impacto

Reexecutei os mesmos 11 planos com uma regra corrigida: **só entra se o gatilho for tocado**; a partir daí, stop = invalidação, alvo = alvo1 (1R do gatilho).

| Ticker | Data | close | entrada (gatilho) | stop | alvo1 | Desfecho corrigido |
|---|---|---:|---:|---:|---:|---|
| SANB11 | 08-03 | 28,93 | 28,38 | 29,10 | 27,66 | **nunca acionou** |
| GOAU4 | 08-03 | 11,20 | 11,23 | 10,68 | 11,78 | stop 08-11 |
| GOAU4 | 08-04 | 11,20 | 11,23 | 10,68 | 11,78 | stop 08-11 |
| TIMS3 | 08-05 | 18,93 | 18,67 | 19,08 | 18,26 | alvo 08-13 |
| TIMS3 | 08-06 | 18,70 | 18,58 | 19,55 | 17,61 | aberta |
| TIMS3 | 08-06 | 18,90 | 19,04 | 18,55 | 19,53 | **nunca acionou** |
| RECV3 | 08-07 | 10,07 | 10,17 | 10,01 | 10,33 | alvo 08-10 |
| FLRY3 | 08-10 | 18,95 | 19,73 | 17,13 | 22,33 | **nunca acionou** |
| FLRY3 | 08-10 | 18,69 | 18,97 | 18,33 | 19,61 | stop 08-12 |
| UGPA3 | 08-11 | 30,99 | 30,99 (a mercado) | 29,73 | 32,25 | alvo 08-14 |
| GOAU4 | 08-15 | 10,99 | 11,08 | 10,62 | 11,54 | aberta |

**Comparação direta:**

| Metodologia | n | Soma R | Expectância | Placar |
|---|---:|---:|---:|---|
| App, contando 1 voto por plano | 8 | +4,80 | **+0,60R** | 5 stop · 3 alvo |
| **App, como o painel realmente conta (com duplicatas)** | **44** | **+112,60** | **+2,56R** | — |
| **Corrigida (entrada no gatilho, R do plano)** | **6** | **0,00** | **0,00R** | **3 stop · 3 alvo** |

R individuais — app: `[-1,0 ×5, +1,0, +4,33, +4,47]` · corrigida: `[-1,0 ×3, +1,0 ×3]`.

**Leitura:** o painel "Eficiência da IA" hoje reportaria **n=44, expectância +2,56R** — acima do `MIN_N=10`, portanto sem o rótulo "n insuficiente", e num patamar que a literatura chama de edge excepcional. A realidade nos mesmos dados é **n=6, expectância 0,00R**. O sinal do erro é **positivo**: a métrica é otimista, não pessimista. [VERIFIED — reproduzível]

> Note a tensão: a **taxa de stop** é inflada pela âncora errada (§2.4a), enquanto a **expectância** é inflada pelo `rMultiple` normalizado por um risco falso (§2.4b) e pela duplicação (§1.2). Os dois erros não se cancelam — corrompem métricas diferentes em direções diferentes.

### 2.6 Motivo de fechamento não persistido (ação)

```python
# server/app/store.py:621
def sell(conn, t, price, user_id=None, qty=None, origem: str = "manual"):

# server/app/store.py:704 — opção TEM motivo
def sell_option(conn, contract_id, price, user_id=None, qty=None,
                motivo: str = "manual", origem: str = "manual"):
```

`agent.py:838` calcula `motivo = "stop atingido" if breach_stop else "alvo atingido"` e usa **só no texto do evento do Diário** (`agent.py:856`). A chamada de venda em `agent.py:852` é `store.sell(conn, pos["t"], price, user_id=scope, origem="automatico")` — **sem `motivo`**.

O docstring de `sell_option` (`store.py:706-715`) explicita a distinção correta entre `origem` (quem disparou) e `motivo` (por quê). **Ação nunca recebeu esse tratamento.** Consequência prática: mesmo que o produto acumule mil trades fechados pelo Operador, a taxa stop×alvo **não é computável a partir do histórico** — só por parsing de string em texto livre do Diário. [VERIFIED]

### 2.7 Outras lacunas de instrumentação

- **`confluencia` não é gravada no outcome** (`analysis_outcomes.py:77-93`). A segmentação "confluência alta acerta mais?" — que é a pergunta comercial do produto — **não tem dado**.
- **`rr2` / `entrada` / `alvo2` não são gravados.** Sem eles não dá para separar "plano bom que não acionou" de "plano ruim".
- **`confianca` é constante** (`moderada` em 57/57). A calibração declarada×real de qa/35 P2c está estruturalmente vazia.
- **`regime` só existe em 7/57 registros** (qa/44 é recente). A segmentação por regime do ADR-009 leva meses para ter massa crítica no ritmo atual.
- **Escopo anônimo:** todos os 57 registros estão em `user_id=None`. `current_scope` (`main.py:98-107`) devolve `None` silenciosamente para token ausente **ou expirado**. Análise feita com sessão expirada cai no balde anônimo e some do painel do próprio usuário (`main.py:2329-2333` lê por escopo). [VERIFIED]
- **Não existe backtest.** `grep -rn backtest server/app` retorna só a flag de metadado `backtestavel: True` em `setups.py:190,219`. Não há motor de replay histórico. Toda a validação do produto depende do loop forward de 10 pregões — que, no ritmo atual (~13 planos em 12 dias), leva **anos** para atingir os 200+ trades que a literatura pede.

---

## 3. Práticas de risk management (literatura)

### 3.1 Taxa de acerto × R:R — a assimetria é desenho, não defeito

O produto **deve** stopar mais do que alveja se o R:R for assimétrico. Estratégias trend-following operam com **30–40% de acerto** e sobrevivem porque o R:R realizado compensa. [CITED: journalplus.co, traderssecondbrain.com]

Expectância = `(P_win × R_win) − (P_loss × R_loss)`. Com 35% de acerto e 3:1: `(0,35×3) − (0,65×1) = +0,40R`. [CITED: traderssecondbrain.com]

Benchmark de Van Tharp amplamente citado: **+0,5R é edge forte; acima de +0,3R sobre 200+ trades é operável; abaixo de +0,1R você empata depois de custos e slippage.** [CITED: traderssecondbrain.com] `[ASSUMED]` quanto à atribuição exata a Tharp — a fonte é secundária; se o número entrar no ADR como referência, confirmar em *Trade Your Way to Financial Freedom*.

> **Implicação direta para o Boris+:** a pergunta "stopa demais?" está mal formulada. A pergunta certa é **"a expectância em R é positiva?"** — e o CLAUDE.md do repo já lista "diferença entre taxa de acerto e rentabilidade" como conceito obrigatório da camada educacional. O produto ensina isso e mede errado.

### 3.2 Triple-barrier — o método já está certo, a implementação não

`_avaliar_entry` é exatamente o **triple-barrier method** de Marcos López de Prado (*Advances in Financial Machine Learning*, 2018, cap. 3): barreira superior (alvo), inferior (stop), vertical (tempo — aqui `HORIZON_PREGOES = 10`). Boa escolha de arquitetura. [CITED: López de Prado 2018, via quantstrategy.io e paperswithbacktest.com]

Dois pontos da literatura que o código viola:

1. **A barreira precisa ser ancorada no evento de entrada, não numa observação arbitrária.** O método existe justamente para capturar path dependency a partir do ponto em que a posição é aberta. Ancorar no close de um dia em que a posição não foi aberta descaracteriza o rótulo. [CITED]
2. **Ambiguidade OHLC.** Com candles diários não se sabe a ordem intrabar. A convenção conservadora (stop primeiro) é defensável, mas **precisa ser reportada**: quantos rótulos foram decididos por empate. Hoje isso é invisível. Mitigação padrão: usar barra intraday para desempatar. **O Boris+ já tem passada de 15min** (`intraday.py`, `timing_watch.py`) — o insumo existe e não é usado na avaliação. [CITED + VERIFIED no código]

### 3.3 Position sizing — o que já está certo

`sizingPlano` (`web/src/finance.js:107-121`) implementa **fixed-fractional**: risco = `capital × pct/100`, quantidade = `risco_financeiro / risco_por_ação`, default 1%, teto 5%, arredondado para lote de 100. Isso **é** a prática padrão. [CITED: fixed-fractional / "regra do 1%"]

Detalhe importante: o sizing usa `p.entrada` (o gatilho) — **o front usa o gatilho corretamente**. Só o `analysis_outcomes` o ignora. Isso confirma que o defeito de §2.4 é **localizado no módulo de medição**, não no motor.

Refinamento da literatura que o produto ainda não tem: **volatility targeting** — stop em múltiplo de ATR e sizing que encolhe automaticamente em pico de volatilidade, com o cap fixed-fractional agindo como teto (usar o menor dos dois). O `agent.py` já tem trailing por ATR (`ATR_MULT_DEFAULT`, `agent.py:414-419`) e alvo dinâmico por ATR — o insumo existe. [CITED: quantstrategy.io, medium/Ildi Veliu]

### 3.4 Filtros de regime — já implementado, subaproveitado

`regime.py` já inverte o eixo de seleção (ADR-009): regime primeiro, momentum relativo cross-sectional depois, setup de price action rebaixado a **gatilho de timing** dentro de um ativo já selecionado (`regime.py:188-209, 212-262`). O próprio docstring diz que o roster 9.x/IFR2/PFR/123/inside bar/LW é *"a família de price action de curto prazo — a de evidência acadêmica mais fraca"*. Isso está alinhado com a literatura.

**Mas:** o campo `regime` só existe em 7/57 outcomes, e `porSetupRegime` (`analysis_outcomes.py:216`) — a métrica que responderia *"este setup tem expectância positiva em tendência mas negativa em lateral?"* — não tem massa para nada. A tese do ADR-009 está **implementada e não validada**.

### 3.5 Validação — o que a literatura exige e o produto não tem

| Prática | Fonte | Status no Boris+ |
|---|---|---|
| **Walk-forward analysis** (reotimização em janelas rolantes) | padrão da indústria [CITED: arxiv 2512.12924] | **ausente** — não há backtest |
| **Deflated Sharpe Ratio** (corrige seleção múltipla, comprimento da amostra, não-normalidade) | Bailey & López de Prado, 2014 [CITED: SSRN 2460551] | ausente |
| **Probability of Backtest Overfitting / CSCV** | Bailey et al., 2017 [CITED] | ausente |
| Expectância + profit factor | Tharp / prática comum | **existe** (`compute_stats`) mas sobre dados corrompidos |
| Curva de R acumulado + drawdown em R | prática comum | **existe** (`analysis_outcomes.py:186-198`) |
| Amostra mínima 200+ trades | [CITED] | **n real = 6–11** |

**Alerta da literatura diretamente aplicável:** Bailey & López de Prado demonstram que alta performance simulada é trivialmente alcançável testando poucas configurações, e que **a probabilidade de selecionar uma estratégia sobreajustada cresce rapidamente com o número de tentativas**. O Boris+ tem **23 detectores** rodando simultaneamente e ranqueia pelo melhor. Isso é seleção múltipla por construção. Qualquer taxa de acerto agregada precisa ser deflacionada pelo número de tentativas — hoje não é. [CITED]

---

## 4. TradingView — viabilidade e risco de ToS

**Confirmado, dupla fonte.**

1. **Não existe API pública de dados de mercado.** TradingView não oferece API pública para preços, dados históricos, valores de indicador ou execução. As integrações reais são webhooks de alerta (saída, não entrada de dados) e o Charting Library sob licença comercial. [CITED: financialtechwiz.com, pineify.app, h2tfunding.com]

2. **Scraping é proibido explicitamente.** ToS §3, *"Ownership of information; license to use TradingView; redistribution of data; non-display usage"*: os usuários são proibidos de empregar qualquer método automatizado de coleta — *"scripts, APIs, screen scraping, data mining, robots, or other data gathering and extraction tools, regardless of their intended purposes"*. [CITED: tradingview.com/policies §3]

3. **Uso non-display é ainda mais restrito — e é exatamente o que o Boris+ faria.** Verbatim do §3:

   > *"The content and market data provided on the TradingView platform, including but not limited to charts, alerts, webhooks, and any other forms of information, are licensed for exclusive display-only use."*

   > *"Such prohibited uses include, but are not limited to, any form of automated trading, automated order generation, **price referencing**, order verification, **algorithmic decision-making**, algorithmic trading, smart order routing, **using data in operations control or risk management programs**, or any machine-driven processes that do not involve the direct, human-readable display of such data."*

   > *"Such prohibited cases also include **creating products or services based on TradingView content**, any processing of TradingView's content..."*

   [CITED: tradingview.com/policies §3, obtido via WebFetch em 2026-08-20]

**Avaliação de risco para este produto — severidade ALTA:**

- O Boris+ é um produto comercializável (CLAUDE.md: "funções básicas grátis... escalando para planos pagos"). "Creating products or services based on TradingView content" é vedação nominal.
- O uso pretendido é *price referencing* + *algorithmic decision-making* + *risk management program* — as três expressões literais da cláusula proibitiva.
- TradingView bane contas por atividade automatizada detectada. [CITED: tradingview.com/support/solutions/43000674726]
- Os dados de terceiros no TradingView vêm de Data Providers com restrições próprias; a violação escala para o exchange/vendor, não só para o TradingView.
- Serviços de scraping de terceiros (Apify etc.) **não transferem o risco** — o ToS proíbe nominalmente "utilization of any third-party products, tools, or services designed to facilitate or enable such non-display usage".

**Recomendação: descartar TradingView como fonte de dados.** A arquitetura atual (brapi master gratuita com orçamento de 15k/mês + Yahoo backup/intraday, ADR-001/ADR-008) já é a decisão travada do repo e não deve ser re-litigada por esta pesquisa. Se faltar cobertura de dado, o caminho é discutir brapi paga ou outra fonte licenciada — não TradingView.

*Se o interesse no TradingView for a **UI de gráfico** e não o dado:* o Charting Library / Advanced Charts é licenciável separadamente e é caminho legítimo — mas é outra discussão (front), não fonte de dados, e não resolve nada de assertividade do motor.

---

## 5. Achados que bloqueiam ou informam o design

Ordenados por impacto na decisão.

### B1 — BLOQUEIA · A pergunta não é respondível com os dados atuais
n real = 6 a 11 planos distintos, contra 200+ recomendados pela literatura. **Qualquer número de "taxa de stop" no ADR precisa vir com o rótulo "amostra insuficiente".** O `MIN_N=10` do produto é, ele próprio, baixo demais para expectância — mas o problema imediato é que nem esse limiar é atingido de verdade (é atingido por duplicação).
*Evidência:* §1.1, §1.2. *Confiança:* ALTA.

### B2 — BLOQUEIA · A medição de eficiência está incorreta e é otimista
`main.py:1317-1318` grava `preco = close` e `alvo = alvo1`, e não grava `entrada`. Resultado medido: **+2,56R / n=44** contra a realidade **0,00R / n=6**. Nenhuma decisão de produto deve ser tomada sobre o painel "Eficiência da IA" no estado atual.
*Correção mínima (3 linhas):* gravar `entrada=plano["entrada"]`, `alvo2`, `rr2` e `confluencia` no registro; em `_avaliar_entry`, exigir toque no gatilho antes de abrir a barreira, e usar `entrada` como `preco0`. **Retrocompatibilidade:** registros antigos sem `entrada` precisam ser marcados como não-comparáveis, não convertidos — inferir `entrada` de `(alvo1+stop)/2` funciona matematicamente mas mistura duas metodologias no mesmo agregado.
*Evidência:* §2.4, §2.5. *Confiança:* ALTA.

### B3 — BLOQUEIA · `n` inflado por duplicação
Até 24 registros do mesmo plano. `compute_stats_all_users` concatena escopos sem deduplicar. **Deduplicar por `(ticker, setup, entrada, stop, alvo, dia)` antes de agregar** — ou usar `snapshotId`, que já está no registro e é a chave natural (`main.py:1318`). Sem isso, `MIN_N` não protege de nada.
*Evidência:* §1.2. *Confiança:* ALTA.

### B4 — BLOQUEIA a pergunta comercial · `confluencia` não é gravada
"Confluência alta acerta mais?" é a hipótese central do produto e **não há dado para testá-la**. Um campo. Adicionar em `registrar()` e em `to_csv()`.
*Evidência:* §2.7. *Confiança:* ALTA.

### B5 — BLOQUEIA a métrica de carteira · `store.sell()` sem `motivo`
Trades de **ação** fechados pelo Operador não registram stop×alvo. Opções registram (`store.py:704`). Paridade óbvia e barata. Sem isso, mesmo com volume de trades, a taxa perguntada continua incomputável.
*Evidência:* §2.6. *Confiança:* ALTA.

### I1 — INFORMA · O R:R 1,5 está em 3 constantes + 7 literais
`skill_ref.RR_MIN`, `setups.RR_MINIMO`, `agent.RR_MINIMO` + literais em `copy.js`, `catalog.js`, `App.jsx`. O teste guardião só cobre `skill_ref`. Se o ADR propuser mexer no limiar (ex.: 2:1 para reduzir stops), **hoje são 10 edições e o teste não pega a divergência**. Consolidar em `skill_ref.RR_MIN` e adicionar um guardião cruzado é pré-requisito de qualquer mudança de limiar.
*Evidência:* §2.3. *Confiança:* ALTA.

### I2 — INFORMA · Empate intrabar sempre vira stop, e isso é invisível
`analysis_outcomes.py:306` e `agent.py:821-822`. A convenção conservadora está certa; o problema é não reportar a frequência. **Instrumentar:** contar `resultado="ambiguo_stop"` quando o mesmo candle toca as duas barreiras. A passada de 15min já existe (`intraday.py`, `timing_watch.py`) e poderia desempatar.
*Evidência:* §2.4c, §3.2. *Confiança:* ALTA no código, MÉDIA no impacto quantitativo (não medido — nenhum empate ocorreu nos 11 planos desta amostra).

### I3 — INFORMA · Não existe backtest; validar só forward leva anos
~13 planos em 12 dias. Para 200 observações independentes: anos. **Um replay histórico do motor determinístico é barato** — `detect_setups`, `plano_do_resultado`, `_avaliar_entry` são todos puros e sem I/O, e `candle_cache.py` já persiste candles. Um backtest de 2–3 anos × 60 tickers gera milhares de observações sem gastar 1 token de LLM nem 1 requisição do orçamento brapi. **É a maior alavanca de assertividade disponível.**
*Ressalva obrigatória (Bailey/López de Prado):* 23 detectores + escolha do melhor = seleção múltipla. Backtest sem walk-forward e sem deflação vai produzir um número bonito e falso. O backtest precisa nascer com walk-forward embutido.
*Evidência:* §2.7, §3.5. *Confiança:* ALTA.

### I4 — INFORMA · ADR-009 implementado e não validado
`regime.py` já rebaixou a confluência a desempate e promoveu regime + momentum relativo. Mas `regime` está em 7/57 registros e `porSetupRegime` está vazio. A tese certa não tem evidência. O backtest de I3 validaria I4 de graça.
*Evidência:* §3.4, §1.1. *Confiança:* ALTA.

### I5 — INFORMA · Análise com sessão expirada vaza para o balde anônimo
`current_scope` devolve `None` silenciosamente para token expirado (`main.py:98-107`). Os 57 registros deste banco estão todos em `user_id=None`. O usuário perde a própria estatística sem aviso. Efeito colateral: `compute_stats_all_users` recolhe esses registros e os mistura no agregado admin, mas o painel individual não.
*Evidência:* §2.7. *Confiança:* ALTA (código) / MÉDIA (se o padrão se repete em produção — não verificado).

### I6 — INFORMA · Duas invariantes do CLAUDE.md permanecem intactas
Nada nesta pesquisa aponta para mover cálculo para a IA. Todos os defeitos estão em **código determinístico medindo código determinístico**. O Princípio 5 (cálculo por regra, nunca pela IA) e o guardrail CVM (manchete só do motor) **não são tocados** por nenhuma das correções propostas. Registrar isso explicitamente no ADR evita que a discussão derrape.

### I7 — INFORMA · Limitação desta pesquisa
Dados de §1 vêm do **banco local de desenvolvimento**. Produção tem volume Railway persistente (`GUIA-OPERACAO.md:51`) e pode ter mais massa. **Antes de fechar o ADR, repetir a extração em produção** (`railway ssh` + `/opt/venv/bin/python3`). Se produção também tiver dezenas de registros, §1 vale para o produto; se tiver milhares, os números de §2.5 continuam válidos como diagnóstico de metodologia, mas o placar stop×alvo precisa ser recalculado sobre a base maior.

---

## Ordem de execução sugerida (para o ADR decidir)

| # | Ação | Custo | Desbloqueia |
|---|---|---|---|
| 0 | Extrair outcomes de **produção** e refazer §1 | minutos | confiança em tudo |
| 1 | Gravar `entrada`, `alvo2`, `rr2`, `confluencia` no outcome (B2, B4) | pequeno | medição correta daqui pra frente |
| 2 | `_avaliar_entry` exige toque no gatilho; `preco0 = entrada` (B2) | pequeno | fim do stop fantasma |
| 3 | Deduplicar por `snapshotId` antes de agregar (B3) | pequeno | `MIN_N` volta a significar algo |
| 4 | `store.sell(..., motivo=)` com paridade a `sell_option` (B5) | pequeno | taxa stop×alvo de carteira |
| 5 | Consolidar `RR_MIN` numa constante + guardião cruzado (I1) | pequeno | poder mexer no limiar depois |
| 6 | Backtest determinístico com walk-forward (I3) | grande | validar o motor e o ADR-009 de fato |

Itens 1–5 são correções de instrumentação: **não mudam o motor, mudam o que se sabe sobre ele.** Nenhum deles deve ser confundido com "melhorar a assertividade" — eles são pré-condição para saber se a assertividade precisa melhorar.

---

## Fontes

**Código deste repositório (VERIFIED — todas as afirmações citam arquivo:linha)**
`server/app/analysis_outcomes.py`, `setups.py`, `agent.py`, `regime.py`, `store.py`, `main.py`, `db.py`, `scan_deep.py`, `skill_ref.py`, `conceitos.py`, `web/src/finance.js`, `web/src/copy.js`, `web/src/catalog.js`, `web/src/App.jsx`, `server/tests/test_auditoria_prompts.py`, `GUIA-OPERACAO.md`, `docs/adr/009-eixo-de-selecao.md`.

**Dados (VERIFIED — reproduzível)**
`server/data/b3_agente.db` (kv `analysisOutcomes`, `history`), `server/data/analytics.db` (`admin_cache`), candles diários via `app.yahoo.get_history(rng="3mo")` — último candle 2026-08-18.

**Literatura (CITED)**
- Bailey, D. & López de Prado, M. — *The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality* — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 · https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf
- López de Prado, M. — *Advances in Financial Machine Learning* (2018), cap. 3, triple-barrier method — via https://quantstrategy.io/blog/the-triple-barrier-method-revolutionizing-how-we-label/ e https://paperswithbacktest.com/course/triple-barrier-method
- Walk-forward validation framework — https://arxiv.org/pdf/2512.12924
- Expectância / win rate × R:R — https://traderssecondbrain.com/guides/expectancy-formula-traders · https://journalplus.co/learn/guides/win-rate-vs-risk-reward/
- Position sizing fixed-fractional / ATR / volatility targeting — https://quantstrategy.io/blog/using-atr-to-adjust-position-size-volatility-based-risk/ · https://medium.com/@ildiveliu/risk-before-returns-position-sizing-frameworks-fixed-fractional-atr-based-kelly-lite-4513f770a82a

**TradingView (CITED)**
- Terms of Service §3 — https://www.tradingview.com/policies/ (verbatim obtido 2026-08-20)
- Ban por atividade automatizada — https://www.tradingview.com/support/solutions/43000674726-why-is-my-account-banned-due-to-suspicious-activity/
- Ausência de API pública de dados — https://www.financialtechwiz.com/post/tradingview-api/ · https://pineify.app/resources/blog/does-tradingview-have-an-api-comprehensive-guide-to-tradingviews-api-offerings

---

## Log de premissas (`[ASSUMED]`)

| # | Afirmação | Seção | Risco se errada |
|---|---|---|---|
| A1 | Benchmark "+0,5R forte / +0,3R operável / 200+ trades" atribuído a Van Tharp | §3.1 | Baixo — fonte secundária; se entrar no ADR como número, confirmar no livro original |
| A2 | ATR diário típico de 1,5–2,5% para large caps da B3 (usado para argumentar que stop de 0,6% é ruído) | §2.4a | Baixo — o argumento não depende do número exato; as distâncias medidas em §2.4a são VERIFIED |
| A3 | O padrão de duplicação observado no banco local se repete em produção com múltiplos usuários | §1.2 | Médio — o mecanismo de código é VERIFIED (`scan_deep.py:19,52-62`); a magnitude em produção não foi medida |

**Nenhuma recomendação deste documento depende de A1–A3.** Os achados que bloqueiam (B1–B5) são todos VERIFIED em código e dados.
