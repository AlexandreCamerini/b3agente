# MEDIÇÃO — rate-limit do mydata (cvm-financas) contra 60/min · 2.000/dia

**Data:** 2026-08-27 (projeção) · **2026-08-28T01:57:52Z** (amostra ao vivo,
anexada por fora do ciclo GSD da fase 9 — ver §4/§5) · **Status: COMPLETO** —
projeção offline e amostra ao vivo, as duas fechadas. Princípio 4 do
`CLAUDE.md` do repo se aplica à própria medição: nenhum número deste
documento é inventado — os da amostra ao vivo vieram de 10 chamadas reais
contra `mydata.acamerini.app` com a chave de produção `f00b4554`.

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

**Rodada em 2026-08-28T01:57:52Z**, pelo Alex, no shell local, com
`MYDATA_TOKEN` exportado (chave de produção, prefixo `f00b4554`; valor
completo nunca aparece neste documento nem em nenhum arquivo do repo).
Comando:

```
server/.venv/bin/python scripts/medir-mydata.py --fases vivo --vivo --amostra 5 --saida /tmp/medicao-mydata-vivo.json
```

5 tickers × 2 rotas = 10 chamadas reais contra `mydata.acamerini.app`. Todas
com `erro: null` (nenhuma falha, nenhum retry):

| Ticker | Rota | Latência | Linhas | Preço presente | Quota restante |
|---|---|---|---|---|---|
| PETR4 | cotacoes | 565ms | 5 | sim | 59 |
| PETR4 | opcoes/vencimentos | 1490ms | 27 | n/a | 58 |
| PETR3 | cotacoes | 451ms | 5 | sim | 57 |
| PETR3 | opcoes/vencimentos | 700ms | 4 | n/a | 56 |
| VALE3 | cotacoes | 459ms | 5 | sim | 55 |
| VALE3 | opcoes/vencimentos | 782ms | 24 | n/a | 54 |
| ITUB4 | cotacoes | 514ms | 5 | sim | 53 |
| ITUB4 | opcoes/vencimentos | 1180ms | 26 | n/a | 52 |
| BBDC4 | cotacoes | 395ms | 5 | sim | 59 |
| BBDC4 | opcoes/vencimentos | 968ms | 24 | n/a | 58 |

`quotaLimite` = 60 em toda chamada, confere com o contrato. `precosPresentes`
é `n/a` (não `null`-erro) nas rotas de `vencimentos`: esse endpoint não
devolve preço, é o formato esperado do payload, não o sintoma de chave sem
escopo.

**Achado — chave escopada corretamente.** `precosPresentes=true` nas 5
chamadas de `cotacoes` — confirma que a chave `f00b4554` carrega `fonte:b3`
de fato (o script tem uma guarda dedicada para o sintoma inverso, "200 com
`dados` mas sem `preco_fechamento`" — descrito no `contrato-consumidor.md`
do cvm-financas como o defeito da chave anterior `dadbd4b0` — e ela NÃO
disparou: `achadoEscopoChave: null` no JSON bruto). Item 3 do TODO fecha
aqui: **a chave de produção autentica de fato e devolve dado real das duas
rotas.**

**Achado colateral — a janela de cota é por minuto-relógio, não rolante a
partir da primeira chamada.** `X-Quota-Restante` caiu de forma monotônica
59→58→57→56→55→54→53→52 nas primeiras 8 chamadas (~6,5s), e então **subiu**
para 59 na 9ª (BBDC4/cotacoes) — só possível se a janela de contagem tiver
resetado no meio da amostra. As 10 chamadas levaram ~7,5s no total, bem
abaixo de 60s; o reset só se explica por uma janela alinhada ao minuto-
relógio (ex.: `HH:MM:00`), não por uma janela rolante de 60s contada a
partir da primeira chamada do cliente. Isso é uma vantagem, não um risco
adicional: janela fixa por minuto-relógio significa que uma rajada correndo
perto do fim de um minuto ganha "cota nova" mais cedo do que uma janela
rolante daria — não muda o veredito do §6 (o teto continua 60/min), mas é
relevante para quem for desenhar o `intervaloMinimoSeguro` com precisão de
borda de janela.

## 5. Reconciliação previsão × verdade

**Fechada.** `X-Quota-Restante` antes da amostra: não capturado (primeira
chamada do processo, sem estado prévio local) → depois: **58**.
`chamadasFeitas` (contador local do script): **10**. O JSON bruto
(`reconciliacao.quotaDepois`) confere exatamente com a última linha da
tabela do §4 (BBDC4/opcoes/vencimentos, restante=58) — a previsão local do
`mydata_budget.py` bateria com a verdade do hub SE tivesse rodado nesta
mesma janela (o teste não instrumentou `mydata_budget` em paralelo; ver
"Plano de ação" no §8 para o gap de instrumentação ao vivo, se algum dia for
necessário).

## 6. Veredito

**VEREDITO FINAL (projeção + amostra ao vivo, as duas fechadas): NÃO CABE
no pico por minuto.** A projeção offline mede 148 de 60/min projetado nos
cenários frio+morno — não por causa do volume diário (548 de 2.000/dia,
folga confortável de 72,6%). A chave suporta o VOLUME; não suporta a mesma
VELOCIDADE de rajada que o `scanner.py` usa hoje para Yahoo/brapi
(`MIN_FETCH_GAP_S`=0,15s permite até ~400 chamadas/min, 6,7× acima do teto
do mydata).

**O que a amostra ao vivo (§4) resolveu:** a chave de produção `f00b4554`
**está confirmada autenticando de fato** contra `mydata.acamerini.app`,
devolvendo dado real e corretamente escopado (`fonte:b3` ativo,
`precosPresentes=true`) das duas rotas medidas (`cotacoes` e
`opcoes/vencimentos`). Essa era a segunda das duas razões que motivaram o
`adiar` do checkpoint do Plano 09-06 — está fechada.

**O que NÃO mudou (na época em que este parágrafo foi escrito):** o pico por
minuto continuava acima do teto. A amostra ao vivo usou 10 chamadas em
~7,5s (bem abaixo de 60/min) — não é um teste de rajada equivalente ao
padrão real do scanner, então não contradiz nem confirma o número 148
projetado; só confirma que a chave funciona.

**Atualização (2026-08-28T17h): mitigação (b) do item 1 do §8 aplicada em
código.** `scanner.run_scan` agora usa `MIN_FETCH_GAP_S_MYDATA`=1,0s (o
`intervaloMinimoSeguro` calculado abaixo) quando `candle_provider.
provider_name() == "mydata"`, preservando `MIN_FETCH_GAP_S`=0,15s para
brapi/Yahoo (commit — ver `server/app/scanner.py`, testado por
`test_gap_sobe_para_mydata_quando_provider_e_mydata` e 2 guardiões
irmãos em `server/tests/test_scanner.py`). Isso torna **estruturalmente
impossível** o código enviar mais de 60 chamadas de candle/min quando
mydata está ativo — o espaçamento é aplicado ANTES de cada chamada real,
não depois; uma rajada de N chamadas agora leva `(N-1)×1,0s` para
completar em vez de estourar o teto. **Efeito no veredito:** a dimensão
"pico por minuto" do §6 passa a **CABE por desenho** para o caminho de
CANDLE (o gate cobre exatamente esse caminho); o veredito histórico acima
(NÃO CABE) permanece registrado como o estado medido ANTES desta mitigação
— não reescrito, carimbado. Item 3 do plano de ação (gate de orçamento nas
opções) também fechou nesse meio tempo (Fase 0 do milestone v1.2,
`OPTGATE-01`) — ver §8 atualizado.

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

1. ~~**Pico por minuto (achado principal, bloqueante para a virada)**~~ —
   **RESOLVIDO em código, 2026-08-28.** Opção (b) implementada:
   `scanner.run_scan` aplica `MIN_FETCH_GAP_S_MYDATA`=1,0s só quando
   `candle_provider.provider_name() == "mydata"`, preservando 0,15s para
   Yahoo/brapi (sem perda de performance nas outras fontes). Estruturalmente
   impossível estourar 60/min de candle enquanto essa checagem estiver no
   caminho. Ver atualização no §6.
2. **Volume diário:** CABE com folga confortável (72,6%) nos números REAIS
   medidos — nenhuma ação necessária aqui. Negociar aumento de cota com o
   lado cvm-financas não é preciso para o volume.
3. ~~**Opções sem teto de taxa (Achado 2, §3)**~~ — **RESOLVIDO em
   2026-08-28** (Fase 0 do milestone v1.2, `OPTGATE-01`):
   `options_provider_mydata.py` ganhou gate `_gate`/`_debita` espelhando
   `candle_provider.py`, com refusal HARD (nunca soft-pass). Ver
   `docs/adr/020-centralizacao-de-dados-no-mydata.md` e
   `.planning/milestones/v1.2-phases/00-precondi-es/00-02-SUMMARY.md`.
4. ~~**Perna ao vivo**~~ — **CONCLUÍDA em 2026-08-28T01:57:52Z.** Chave
   `f00b4554` confirmada autenticando de fato, escopo `fonte:b3` ativo
   (campos de preço presentes nas 5 amostras de `cotacoes`). Ver §4/§5/§6.

## 9. Pré-condição da virada

Este documento é o **pré-requisito declarado** do checkpoint do Plano
09-06. Sem `CABE` nas DUAS dimensões (volume diário E pico por minuto) —
ou sem a mitigação do item 1 do Plano de ação aplicada — **a virada de
`B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER` para `mydata` NÃO acontece**.

**Status atual (pós amostra ao vivo de 2026-08-28):** volume diário CABE;
chave confirmada autenticando de fato (item 4 do Plano de ação fechado);
**pico por minuto continua NÃO CABE** sem a mitigação do item 1 aplicada
(gate de espaçamento sensível ao provedor, ou elevar o espaçamento global).
Dos três itens que precisavam fechar antes da virada, dois fecharam — falta
só o pico por minuto. O checkpoint do Plano 09-06 foi resolvido como
`adiar` em 2026-08-27 (antes desta amostra ao vivo existir); com a chave
agora confirmada, o único bloqueio restante para reabrir esse checkpoint é
a mitigação do pico/min.
