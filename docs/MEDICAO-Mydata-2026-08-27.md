# MEDIÇÃO — rate-limit do mydata (cvm-financas) contra 60/min · 2.000/dia

**Data:** 2026-08-27 · **Status: PARCIAL — perna ao vivo BLOQUEADA por
`MYDATA_TOKEN` ausente no ambiente de execução.** Este documento registra a
medição de **projeção offline** (100% completa, ZERO rede) e deixa a
**amostra ao vivo** explicitamente pendente. Princípio 4 do `CLAUDE.md` do
repo se aplica à própria medição: nenhum número da perna ao vivo abaixo é
inventado — as seções correspondentes dizem "BLOQUEADO", não um valor
chutado.

## 1. O que foi medido e como

- **Comando executado:** `python3 scripts/medir-mydata.py --fases projecao --saida /tmp/medicao-mydata-projecao.json`
  (a fase `vivo` foi tentada via `--fases projecao,vivo --vivo --amostra 5`,
  mas saiu com código 2 antes de tocar a rede — ver §4).
- **Ambiente:** worktree isolado da execução do Plano 09-04, sem
  `MYDATA_TOKEN` no shell (confirmado por `env | grep -i MYDATA` antes de
  começar — nenhuma variável presente).
- **Universo:** `scanner.get_universe()` real — **74 ativos**, origem
  `default (scanner.DEFAULT_UNIVERSE)` (nenhum `B3_SCAN_UNIVERSE` setado
  neste ambiente).
- **Método da projeção:** o script EXECUTA `mydata_client.get_history`/
  `get_vencimentos`/`get_options_chain` reais (via
  `options_provider_mydata.get_options`), com um `fetch_json` fake injetado
  que só CONTA chamadas HTTP — não lê o código-fonte e estima. Isso garante
  que a paginação, os ranges (`RANGE_DIAS`) e o fluxo de
  vencimentos+cadeia são o comportamento real do cliente, não uma suposição
  do medidor.

## 2. Custos unitários medidos

### Candle (`mydata_client.get_history`)

| Range | Sem paginação (1 página fake) | Com paginação (3 páginas fake) |
|---|---|---|
| carga cheia (`2y`) | **1** | 3 |
| delta (`1mo`) | **1** | 3 |

Confirma a estimativa do 09-02-SUMMARY.md (§Decisions Made): tanto `2y`
quanto `1mo` cabem em UMA página do mydata (`LIMITE_MAX=2000` registros;
`RANGE_DIAS["2y"]=790` dias corridos ≈ 564 pregões, `RANGE_DIAS["1mo"]=45`
dias corridos ≈ 32 pregões — ambos bem abaixo do teto de uma página). O
teto real de páginas por chamada lógica é `mydata_client.PAGINAS_MAX=8`; as
colunas "com paginação" acima usam 3 páginas fake só para expor o
comportamento caso um range maior (`max`) algum dia precise paginar — não é
o caminho normal medido.

### Cadeia de opções (`options_provider_mydata.get_options`)

| Sem paginação (1 página fake da cadeia) | Com paginação (3 páginas fake) |
|---|---|
| **2** (1 vencimentos + 1 cadeia) | 4 |

Confirma a estimativa do 09-03-SUMMARY.md (§Achados de produto, item b):
caso normal = 2 chamadas por cadeia completa (1 `/vencimentos` + 1 página de
`/opcoes/{ticker}`).

## 3. Projeção

Três cenários sobre o universo real (74 ativos), usando os custos unitários
**sem paginação** (o caminho real medido acima):

| Cenário | chamadas | pico chamadas/min |
|---|---|---|
| **frio** — redeploy do Railway, L2 vazio, carga cheia do universo inteiro de uma vez | 74 (evento único) | **74** |
| **morno REAL** — delta do universo inteiro, cadência OBSERVADA no código (`radar_daily.maybe_run`, 1x/dia útil, `B3_RADAR_DAILY_HHMM`=08:45) | 74/dia | **74** |
| **morno — leitura literal do plano** (NÃO observada no código; ver achado abaixo) | 21.312/dia | 74 |
| **opções** — `--cadeias-dia`=200 (default), custo/cadeia=2 | 400/dia | não limitado pelo código (achado de arquitetura, ver abaixo) |

**Achado 1 (Rule 1 — premissa do plano não bateu com o código, corrigida
antes de fechar o número):** o texto do Plano 09-04 descreve a cadência do
cenário morno como "a cadência real do scheduler (`interval_s` do
`scheduler_loop`)" — 300s, o que daria 288 ciclos/dia e 21.312 chamadas/dia
se o universo inteiro fosse re-buscado a cada tick. Isso NÃO é o que o
código faz: o único ponto que varre o universo INTEIRO em busca de candle
(`scanner.run_scan`) é `radar_daily.maybe_run` (`server/app/radar_daily.py`),
gated por `pregao.is_trading_day()`, rodando **1x por dia útil** às
`B3_RADAR_DAILY_HHMM` (default 08:45) — não a cada passada do
`scheduler_loop` (300s). O `scheduler_loop` a cada 300s toca candle de
POSIÇÃO/pendência do usuário (conjunto pequeno, via `quotes_getter` — spot
brapi/Yahoo, não `mydata_client`) e a passada intraday GLOBAL (Yahoo, ADR-001
intocada) — nenhum dos dois bate a rota de candle diário do mydata. O
número REAL de chamadas/dia do cenário morno é **74/dia** (1 varredura ×
74 ativos × 1 chamada/ativo), não 21.312. Reportamos os dois números na
tabela acima para que quem lê este documento no checkpoint do Plano 09-06
veja a diferença explicitamente, em vez de herdar em silêncio uma premissa
de arquitetura não verificada — exatamente o erro que este plano existe
para eliminar (09-CONTEXT.md).

**Achado 2 (arquitetura — não corrigido neste plano, fora de escopo):**
`options_provider_mydata.py`/`options_provider.py` NUNCA chamam
`mydata_budget.pode_gastar()`/`debita()` (confirmado por leitura de
`server/app/options_provider.py` e `server/app/options_provider_mydata.py`
— só `candle_provider.get_history()` tem gate por elo, implementado no
Plano 09-02). **A cadeia de opções não tem NENHUM teto de taxa no código.**
O pico/min real depende só da concorrência de usuários abrindo cadeias
distintas simultaneamente — algo que este script não mede porque não há
dado de uso real do produto ainda. Reportar um número de pico aqui seria
inventar valor (princípio 4 do `CLAUDE.md`); o campo fica nomeado como
achado, não estimado.

**Soma dos três (frio + morno REAL + opções), chamadas/dia:** 74 + 74 + 400
= **548** de 2.000/dia → **CABE** (72,6% de folga).

**Soma do pico/min (frio + morno; opções sem número, ver Achado 2):**
74 + 74 = **148** de 60/min → **NÃO CABE** (147% acima do teto do minuto).

**`intervaloMinimoSeguro`:** **1,0s** de espaçamento mínimo entre chamadas
reais ao mydata para manter o pico de qualquer janela de 60s dentro da cota
do minuto. Hoje `scanner.MIN_FETCH_GAP_S`=0,15s — um gate GLOBAL (serializa
TODAS as chamadas reais via `gate_lock`, independente do semáforo de
concorrência de 4), dimensionado para Yahoo/brapi, não para o teto mais
apertado do mydata (60/min é 6,7× mais restritivo que a folga que
`MIN_FETCH_GAP_S` permite hoje — até 400 chamadas/min de capacidade teórica).

## 4. Amostra ao vivo

**BLOQUEADO.** `MYDATA_TOKEN` ausente no ambiente de execução deste plano.
Comando tentado:

```
python3 scripts/medir-mydata.py --fases projecao,vivo --vivo --amostra 5 --saida /tmp/medicao-mydata.json
```

Saída da fase `vivo`:

```
ERRO: MYDATA_TOKEN ausente no ambiente. A perna ao vivo não roda sem a chave
de produção (prefixo público f00b4554; exporte a chave completa só no shell
local — nunca commitar).
```

Código de saída: **2** (comportamento correto e verificado — a fase `vivo`
recusa terminantemente em vez de simular ou estimar; ver critério de
aceite do Plano 09-04, Task 1). Nenhuma chamada de rede foi feita, nenhuma
cota foi gasta.

**Para completar esta seção:** rodar localmente, com `MYDATA_TOKEN`
exportado no shell (nunca commitado):

```
server/.venv/bin/python scripts/medir-mydata.py --fases vivo --vivo --amostra 5 --saida /tmp/medicao-mydata-vivo.json
```

e anexar aqui a tabela por ticker (status, latência, `X-Quota-Limite`,
`X-Quota-Restante`, linhas devolvidas, campos de preço presentes) que o
script já imprime automaticamente.

## 5. Reconciliação previsão × verdade

**BLOQUEADO** — depende da amostra ao vivo (§4). O script já implementa a
reconciliação (`X-Quota-Restante` antes/depois da amostra vs. número de
chamadas feitas, impresso ao final da fase `vivo`); só falta rodá-la com a
chave real.

## 6. Veredito

**VEREDITO DA PROJEÇÃO (offline): NÃO CABE**, por causa do PICO por minuto
(148 de 60/min projetado nos cenários frio+morno) — não por causa do volume
diário (548 de 2.000/dia, folga confortável de 72,6%). A chave suporta o
VOLUME; não suporta a mesma VELOCIDADE de rajada que o `scanner.py` usa
hoje para Yahoo/brapi (`MIN_FETCH_GAP_S`=0,15s permite até ~400
chamadas/min, 6,7× acima do teto do mydata).

Este veredito é só da perna de PROJEÇÃO. A chave de produção (`f00b4554`)
**ainda não foi confirmada autenticando de fato** contra
`mydata.acamerini.app` nem devolvendo dado real das duas rotas — isso exige
a amostra ao vivo (§4), bloqueada nesta execução. O veredito final e
completo do critério de aceite da fase só fecha depois da perna ao vivo
rodar.

## 7. Item 2 do TODO — status de `provento_b3`

Fora das duas fatias migradas nesta fase (só COTAHIST diário e opções) —
entra como linha de status, não bloqueio. Conferido em
`~/dev/cvm-financas/docs/contrato-consumidor.md` (linha 151, tabela "O que
o BolsIA usa hoje"): a classe `provento_b3` está **"construída em
26/08/2026 — rota de consumo via gold_proventos; falta só a primeira carga
de produção"**. Ou seja: o endpoint e o escopo da chave já existem
(`f00b4554` inclui `provento_b3` desde 26/08/2026, linha 63 do mesmo
documento), mas o hub ainda não fez a primeira carga de produção dos dados
de proventos — não usar essa classe até essa carga ser confirmada do lado
do cvm-financas, mesmo depois que este plano/fase migrar candle e opções.

## 8. Plano de ação

O veredito é misto — CABE no volume diário, NÃO CABE no pico por minuto —
então a ação recomendada também é mista, e nenhuma das duas depende de
negociar aumento de cota:

1. **Pico por minuto (achado principal, bloqueante para a virada):** antes
   de virar `B3_CANDLE_PROVIDER=mydata` em produção, o gate de espaçamento
   entre chamadas reais precisa respeitar o teto do mydata
   especificamente — hoje `scanner.MIN_FETCH_GAP_S`=0,15s é compartilhado
   por todos os provedores e foi dimensionado para Yahoo/brapi. Duas saídas
   possíveis (decisão do Plano 09-06, não deste plano): (a) elevar o
   espaçamento GLOBAL para o `intervaloMinimoSeguro` calculado (1,0s) — mas
   isso deixaria Yahoo/brapi mais lentos também, sem necessidade; ou (b)
   tornar o gate de espaçamento SENSÍVEL ao provedor ativo (só aplicar
   1,0s quando o provedor da chamada for `mydata`), preservando 0,15s para
   Yahoo/brapi. A opção (b) é a que preserva o ganho de performance das
   outras fontes.
2. **Volume diário:** CABE com folga confortável (72,6%) nos números REAIS
   medidos — nenhuma ação necessária aqui. Negociar aumento de cota com o
   lado cvm-financas não é preciso para o volume.
3. **Opções sem teto de taxa (Achado 2, §3):** antes de virar
   `B3_OPTIONS_PROVIDER=mydata` em produção, considerar adicionar um gate de
   orçamento em `options_provider_mydata.py`/`options_provider.py`,
   espelhando o `_gate`/`_debita` que `candle_provider.py` já tem (Plano
   09-02) — hoje não existe NENHUM limite de taxa no caminho de opções, e
   o TTL de 300s só reduz repetição do MESMO ticker, não protege contra
   muitos tickers distintos abertos ao mesmo tempo.
4. **Perna ao vivo (bloqueio desta execução):** rodar
   `scripts/medir-mydata.py --fases vivo --vivo` localmente com
   `MYDATA_TOKEN` exportado, confirmar autenticação real e escopo
   `fonte:b3` (campos de preço presentes), e atualizar as §4/§5/§6 deste
   documento com os números reais antes do checkpoint do Plano 09-06.

## 9. Pré-condição da virada

Este documento é o **pré-requisito declarado** do checkpoint do Plano
09-06. Sem `CABE` nas DUAS dimensões (volume diário E pico por minuto) —
ou sem a mitigação do item 1 do Plano de ação aplicada — **a virada de
`B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER` para `mydata` NÃO acontece**.
Hoje: volume diário CABE; pico por minuto NÃO CABE sem a mitigação do item
1; a perna ao vivo (autenticação real, escopo `fonte:b3`) está BLOQUEADA
pendente de `MYDATA_TOKEN` neste ambiente. Os três precisam fechar antes do
Plano 09-06 aprovar a virada.
