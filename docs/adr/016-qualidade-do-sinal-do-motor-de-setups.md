# ADR-016: Qualidade do sinal do motor de setups — diagnóstico e caminho

**Status:** Proposto — aguardando decisão. Nenhum código de produção foi alterado.
**Data:** 2026-08-20
**Gatilho:** observação do dono do produto de que os ativos com confluência 100%
para alta saíram majoritariamente por stop, com o usuário perdendo dinheiro.
**Companion:** ADR-015 (medição). Este ADR é sobre o **sinal**, não sobre o medidor.
**Harness:** `scripts/backtest_{sinal,analise,placebo,horizonte,comprado,periodo}.py`
— reexecutáveis, sem I/O de produção.

---

## Resumo para decisão

1. **O motor tem expectância negativa.** 32.095 sinais, 74 tickers, 3 anos:
   **−0,104R por operação** (IC95 [−0,114; −0,094], t = −19,7). Não é ruído de
   amostra pequena; é o resultado central com significância folgada.
2. **O motor perde para o acaso.** Entrada em dia sorteado com a mesma geometria
   rende **−0,016R**; entrada pelo setup rende **−0,104R**. Diferença −0,088R,
   t = −12,4. O setup não é neutro — ele **seleciona momentos piores que o
   aleatório**.
3. **A confluência não discrimina, e não tinha como.** 93,1% dos sinais têm
   confluência 100%, porque em 2 dos 13 setups esse é o único valor possível e em
   5 outros é um de dois. Expectância por faixa: 100% → −0,103R, 86% → −0,119R,
   71% → −0,094R. A variável que ordena o Radar não separa nada.
4. **Nenhum setup se salva individualmente.** O melhor é Setup 9.3 (alta) com
   +0,001R (t = +0,05) — zero. Nenhum passa nem o limiar de |t| = 2, quanto mais
   o limiar deflacionado de 2,4 exigido por testar 17 configurações.
5. **Nenhum sobrevive ao walk-forward.** Em 6 janelas consecutivas, nenhum setup
   é positivo em mais de 4, e os dois que chegam a 4/6 têm expectância ≈ 0.
6. **A observação do dono do produto estava certa e era conservadora.** Não é um
   subconjunto de sinais que falha: é o motor inteiro.

O ADR-015 concluiu que o medidor mente na direção otimista. Este ADR mede o que
o medidor deveria ter medido, e o resultado é pior do que a percepção que abriu
a investigação.

---

## Como foi medido

Replay determinístico do motor real, sem LLM e sem tocar `server/app/`:

| Parâmetro | Valor | Origem |
|---|---|---|
| Universo | 74 tickers | `scanner.DEFAULT_UNIVERSE` |
| Período dos sinais | 2023-07 → 2026-08 (~756 pregões) | 5 anos baixados, 252 de warmup |
| Janela do motor | 252 barras | `candles_mod.resolve_keep("1y")`, o que o Radar usa |
| Horizonte | 10 pregões | `analysis_outcomes.HORIZON_PREGOES` |
| Fonte | Yahoo diário, cacheado em disco | ADR-008 (não consumiu orçamento brapi) |
| Sinais gerados | 41.144 | planos COMPRAR/VENDER de `plano_do_resultado` |
| Sinais resolvidos | 32.095 | 9.049 não acionaram o gatilho |

Para cada pregão, o harness recomputa `detect_setups` + `plano_do_resultado`
sobre a janela que a produção teria visto naquele dia, e avalia as 10 barras
seguintes. Os indicadores são causais e alinhados ao array de candles, então
fatiar em `t` reproduz exatamente o estado do dia `t` — não há vazamento de
futuro.

**Metodologia de avaliação (herdada do ADR-015):** entrada ancorada no gatilho
(`plano["entrada"]`), nunca no close. Plano do tipo "a mercado" abre a barreira
na primeira barra, sem exigir toque — exigir toque jogaria o gap adverso para
fora do denominador, que é o viés que o ADR-015 documenta. Empate intrabar
resolve a favor do stop (mesma convenção de `_avaliar_entry` e `agent.py`).
Sinais que nunca acionaram o gatilho ficam fora do denominador: o trade não
existiu.

Medimos as duas barreiras: `alvo1` (1R — o que o produto mede hoje) e `alvo2`
(a projeção do setup, R:R ≥ 1,5 — o que o produto promete).

---

## Resultado

### 1. Expectância global

| Barreira | n | Expectância | IC95 | t | Acerto | Profit factor |
|---|---:|---:|---|---:|---:|---:|
| `alvo1` (1R) | 32.095 | **−0,104R** | [−0,114; −0,094] | −19,7 | 44,8% | 0,80 |
| `alvo2` (projeção) | 32.095 | **−0,094R** | [−0,107; −0,080] | −13,9 | 35,8% | 0,84 |

Com barreira 1:1, o ponto de equilíbrio é 50% de acerto. O motor entrega 44,8%.

### 2. O controle nulo — o achado que muda a conversa

Para separar "o setup escolhe mal" de "qualquer entrada com essa geometria
perde", geramos um placebo: mesmo ticker, mesma distância relativa de stop e
alvo, mesmo lado, entrada num dia sorteado do mesmo período (semente fixa 42).

| | n | Expectância | Acerto | t |
|---|---:|---:|---:|---:|
| Placebo (dia sorteado) | 41.105 | −0,016R | 49,1% | −3,3 |
| **Motor (setup)** | 32.095 | **−0,104R** | 44,8% | −19,7 |
| **Diferença** | | **−0,088R** | | **−12,4** |

O placebo fica praticamente no zero — os −0,016R são o custo da geometria
(empate intrabar a favor do stop, spread implícito no OHLC). O motor fica
0,088R abaixo disso, com t = −12,4.

**Leitura:** o sinal tem informação, mas com o sinal trocado. Os setups
implementados são de reversão e rompimento de curtíssimo prazo, e disparam
justamente depois de o preço já ter se movido. Entrar onde eles mandam é pior
do que entrar num dia qualquer.

### 3. A confluência

Distribuição dos 41.144 sinais:

| Confluência | Sinais | % |
|---:|---:|---:|
| 100% | 38.312 | **93,1%** |
| 86% | 2.690 | 6,5% |
| 71% | 141 | 0,3% |
| 57% | 1 | 0,0% |

Expectância por faixa (barreira `alvo1`): 100% → −0,103R · 86% → −0,119R ·
71% → −0,094R. Os intervalos de confiança se sobrepõem; não há gradiente.

Isso não é acaso — é consequência da implementação. `_confluencia()`
(`setups.py:68-71`) divide pelo peso total dos critérios do próprio setup, e
`_vale()` (`setups.py:504-506`) já exige que **todos** os critérios
`obrigatorio=True` estejam presentes para o setup existir. Como cada setup tem 3
critérios e a maioria é obrigatória, sobra pouco para variar:

| Setup | Pesos (\* = obrigatório) | Valores alcançáveis |
|---|---|---|
| Setup 9.3, Ponto Contínuo | 3\*, 2\*, 3\* | **[100]** — constante |
| 9.2, IFR2, PFR, Inside Bar, 9.4 LW | 3\*, 3\*, 1 | [86, 100] |
| Reversão / Compressão | — | [71, 100] / [75, 100] |
| Pullback | 3\*, 3, 2 | [62, 75, 100] |
| Rompimento, 9.1, 123 | 4\*, …, 1 | 4 valores |

Em 8 dos 13 setups, "confluência 100%" significa apenas que o critério opcional
de peso 1 (de 7) também bateu. E `regime.ranquear()` (`regime.py:212-262`) usa
`−confluência` como critério de ordenação do Radar — o produto ordena o que
mostra ao usuário por uma variável que é quase constante.

### 4. Por setup

Barreira `alvo1`, ordenado por n:

| Setup | n | Expectância | IC95 | t | Acerto |
|---|---:|---:|---|---:|---:|
| Setup 9.2 (baixa) | 4.531 | −0,197R | [−0,23; −0,17] | −13,9 | 40,3% |
| Setup 9.2 (alta) | 4.083 | −0,148R | [−0,18; −0,12] | −9,8 | 42,5% |
| Setup 9.3 (baixa) | 4.011 | −0,072R | [−0,10; −0,04] | −4,9 | 46,2% |
| Setup 9.3 (alta) | 3.647 | **+0,001R** | [−0,03; +0,03] | +0,05 | 49,9% |
| Máx/Mín LW 9.4 (baixa) | 3.008 | −0,126R | [−0,16; −0,09] | −7,3 | 43,9% |
| 123 de topo (baixa) | 2.476 | −0,131R | [−0,17; −0,10] | −7,4 | 44,3% |
| Máx/Mín LW 9.4 (alta) | 2.116 | −0,122R | [−0,16; −0,08] | −5,9 | 43,4% |
| 123 de fundo (alta) | 2.027 | −0,082R | [−0,12; −0,04] | −4,1 | 45,6% |
| Setup 9.1 (baixa) | 1.260 | −0,015R | [−0,07; +0,04] | −0,6 | 49,8% |
| Setup 9.1 (alta) | 1.144 | −0,030R | [−0,08; +0,03] | −1,1 | 48,4% |
| IFR2 (alta) | 696 | −0,049R | [−0,12; +0,02] | −1,3 | 47,4% |
| PFR (baixa) | 684 | −0,117R | [−0,19; −0,04] | −3,2 | 44,2% |
| Ponto Contínuo (alta) | 565 | −0,230R | [−0,31; −0,15] | −5,8 | 38,4% |
| PFR (alta) | 557 | **+0,031R** | [−0,05; +0,11] | +0,8 | 51,9% |
| Inside Bar (baixa) | 475 | −0,059R | [−0,14; +0,02] | −1,4 | 48,0% |
| Inside Bar (alta) | 415 | −0,074R | [−0,17; +0,02] | −1,6 | 46,0% |
| Ponto Contínuo (baixa) | 400 | −0,209R | [−0,30; −0,12] | −4,5 | 39,8% |

Dois setups têm expectância nominalmente positiva (9.3 alta, PFR alta) e nenhum
dos dois é estatisticamente distinguível de zero. Testamos 17 configurações — o
limiar prudente de |t| sobe para ≈ 2,4 (Bailey & López de Prado, *The Deflated
Sharpe Ratio*, 2014). Nenhum chega perto.

### 5. Walk-forward — 6 janelas consecutivas

Nenhum setup é consistentemente positivo. Os únicos com 4 janelas positivas de 6
(Setup 9.1 baixa, PFR alta) têm expectância global ≈ 0 e n modesto. Os de maior
volume são positivos em 0/6, 1/6 ou 2/6:

| Setup | Janelas positivas |
|---|---|
| 123 de topo (baixa), PFR (baixa), Ponto Contínuo (alta) | **0/6** |
| Setup 9.2 (alta), Setup 9.2 (baixa), 9.4 LW (alta), 9.4 LW (baixa), 123 de fundo (alta), Setup 9.1 (alta), Inside Bar (baixa) | 1/6 |
| Setup 9.3 (alta), Setup 9.3 (baixa) | 2/6 |
| IFR2 (alta) | 3/6 |
| Setup 9.1 (baixa), PFR (alta) | 4/6 |

### 6. Por regime — a tese do ADR-009 não se sustenta como está

| Regime | n | Expectância | t |
|---|---:|---:|---:|
| Lateral | 20.000 | −0,098R | −14,7 |
| Tendência de alta | 6.664 | −0,077R | −6,6 |
| Tendência de baixa | 5.431 | −0,157R | −12,4 |

Nenhum regime salva o motor. O ADR-009 promoveu regime a eixo primário de
seleção com a tese de que o setup certo no regime certo funcionaria; das 49
células setup × regime, nenhuma é positiva com significância. A célula menos
ruim é Setup 9.3 (baixa) em tendência de alta: +0,067R com t = +1,41 e n = 399 —
não passa o corte.

Operações vendidas são consistentemente piores (−0,124R contra −0,081R nas
compradas), o que é coerente com o viés de alta estrutural do período medido.

---

## O que isso significa

O produto ensina o usuário a operar com um motor que, medido sobre 3 anos de
mercado real, **destrói capital simulado a −0,104R por operação e perde para
sortear um dia no calendário**. O Core Value declarado no PROJECT.md — "o
usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona"
— não sobrevive a um motor cujo sinal é pior que aleatório: o usuário aprende um
raciocínio que não se sustenta.

Nada disso viola o Princípio 5 nem o guardrail CVM — os cálculos sempre foram
determinísticos. O problema é que a regra determinística escolhida não tem
vantagem.

**Contexto honesto, para não superinterpretar:** a família de price action de
curto prazo (9.x, IFR2, PFR, 123, inside bar, Larry Williams) é reconhecidamente
a de evidência empírica mais fraca — o próprio docstring de `regime.py` já
registra isso. Este resultado é consistente com o que a literatura de sistemas
sistemáticos prevê para checklists de indicadores derivados do mesmo preço, e
não é uma surpresa metodológica; é a primeira vez que o projeto o mediu.

---

## O que a evidência externa diz

Pesquisa completa em
`.planning/prompts/pesquisa-externa-qualidade-do-sinal.md`, com cada achado
rotulado como evidência quantitativa publicada, prática difundida ou opinião.
Quatro pontos mudam decisões deste ADR:

**1. Existe um mecanismo conhecido para o colapso da confluência.** Indicadores
técnicos derivados da mesma série de preço são fortemente colineares — um
diagnóstico de 39 indicadores encontrou VIF > 5 em todos exceto quatro. Um
checklist cujos itens nascem do mesmo cálculo não produz cinco confirmações
independentes; produz a mesma informação cinco vezes. Isso explica por que a
confluência do Boris+ colapsou em 1–2 valores por setup: não é um bug de pesos,
é a consequência esperada de agregar itens correlatos. **Implicação:** redesenhar
a confluência só ajuda se os fatores novos forem de conceitos comprovadamente
não-correlatos (estrutura × momentum × volume × volatilidade). Mais critérios do
mesmo tipo reproduzem o problema.

**2. O resultado é consistente com a única evidência acadêmica forte sobre o
mercado-alvo.** Chen & Metghalchi testaram combinações de regras técnicas
populares no Bovespa entre 1996 e 2011 (~15 anos) e não encontraram superação
sobre buy-and-hold; as regras que pareciam lucrativas perdiam a vantagem ao
contabilizar o juro do período fora do mercado. O backtest deste ADR chega ao
mesmo lugar por caminho independente. Isso eleva o ônus da prova para qualquer
proposta futura.

**3. O atalho óbvio já foi testado e não funciona.** A correção intuitiva para
setup de reversão com expectância ruim é "filtrar por tendência de prazo maior".
A QuantBrasil rodou exatamente isso no IFR2 (LREN3, 2015–2020, filtros de
MMA50/MMA200/EMA80): as operações caíram de 160 para 100 e o retorno por
operação não melhorou de forma significativa — só houve leve redução de
drawdown. **Implicação direta:** adicionar filtro de média como remédio de
primeira linha tem evidência contrária, não a favor. Se for testado, que seja
com essa expectativa.

**4. A única evidência quantitativa favorável a um setup do produto está em
outro timeframe.** Pellin (EnANPAD 2022) mediu o Setup 9.1 em 4 ações do
Ibovespa entre 2012 e 2021 e reportou 67% de acerto e relação lucro/prejuízo
5,34 — mas em **gráfico semanal**, com 12–14 operações por ativo, sem custos e
somando retornos aritmeticamente. O Boris+ roda o 9.1 em barra **diária**, e
este backtest o mediu em ≈ 0 (−0,015R vendido, −0,030R comprado) com n = 2.404.
Os dois resultados não se contradizem: são horizontes diferentes. **É a pista
mais concreta desta pesquisa** — o horizonte de 10 pregões pode ser curto demais
para a família que o produto implementa, e isso é testável no harness sem
inventar nada.

Fora dos 13 setups atuais, o que tem mais lastro acadêmico é rompimento de canal
(Donchian) e momentum de série temporal — em horizonte de semanas a meses, não
de dias — e pairs trading, que tem paper específico sobre o mercado brasileiro.
Nenhum deles é substituto direto de um setup de 1–5 dias.

---

## Alternativas

### Alternativa A — Parar de apresentar o sinal como operável (mínima, imediata)

Manter os setups como material didático e remover a moldura de recomendação:
`plano_do_resultado` deixa de emitir COMPRAR/VENDER como manchete padrão, o
Radar para de ordenar por confluência, e o card passa a apresentar o setup como
"padrão gráfico identificado — sem vantagem estatística medida", com o número
deste ADR visível.

- **Ganha:** o produto para de ensinar como operável algo medido como pior que o
  acaso. É a única alternativa que endereça o dano ao usuário hoje.
- **Paga:** o Modo Operador perde o gatilho automático; o Radar perde o critério
  de ordenação; a proposta de valor "treine decisões" fica mais fraca até haver
  substituto.
- **Custo:** baixo. Mexe em `setups.plano_do_resultado`, `regime.ranquear` e na
  camada de copy — não exige motor novo.
- **Risco:** nenhum guardrail tocado. Reversível.

### Alternativa B — Reconstruir a seleção sobre o que o backtest mostrar que funciona

Usar o harness como bancada: testar filtros e sinais candidatos com o mesmo
protocolo (walk-forward + deflação), e só promover a produção o que sobreviver.
O harness já existe e roda o universo inteiro em minutos.

Fila de teste, ordenada por razão entre lastro e custo — as três primeiras saem
direto da medição e da pesquisa deste ADR:

1. **Horizonte.** O 9.1 tem evidência favorável em barra semanal (Pellin 2022) e
   mede ≈ 0 em barra diária aqui. Rodar os 13 setups em horizontes de 20, 40 e 60
   pregões antes de concluir que a família não presta — pode ser o produto medindo
   no timeframe errado, não o setup sendo inútil.
2. **Ordenação do Radar.** Comparar, em walk-forward, o retorno dos top-N
   ordenados por confluência × ordenação aleatória dentro do subconjunto já
   filtrado × score de fatores não-correlatos. O controle nulo deste ADR já dá
   metade da resposta; falta isolar o efeito da ordenação.
3. ~~**Só comprado.**~~ **Testado e descartado como remédio autônomo** — ver
   Adendo 2. O lado comprado perde de segurar o mesmo papel por 1,49 pontos
   percentuais por operação (t = −32,6). O que parecia edge era beta de um
   período de alta.
4. ~~**Momentum relativo cross-sectional.**~~ **Testado — ver Adendo 4.**
   Direção certa em 6 de 6 configurações, mas o excesso sobre o mercado não
   atinge significância (t = +0,6 a +1,1) e é o candidato mais exposto ao viés de
   sobrevivência do universo. Não provado, não promissor.
5. **Rompimento de canal (Donchian)** e **pairs trading** — famílias novas, a
   segunda com paper específico sobre o mercado brasileiro.

Com expectativa calibrada: filtro de média móvel como remédio de primeira linha
tem evidência **contrária** (QuantBrasil no IFR2), então entra na fila como
teste, não como correção presumida.

- **Ganha:** é o único caminho que pode produzir sinal com vantagem real, e
  produz evidência antes de cada mudança em vez de depois.
- **Paga:** semanas de trabalho, sem garantia de achar edge. Precisa de
  disciplina anti-sobreajuste — com 74 tickers e 3 anos dá para "descobrir"
  qualquer coisa se testar o suficiente.
- **Custo:** alto.
- **Risco:** o risco real é psicológico — encontrar um número bonito na
  centésima tentativa e acreditar nele. Mitigação: walk-forward obrigatório,
  contagem de configurações testadas registrada, e teste out-of-sample num
  período reservado.

### Alternativa C — Reconstruir só a confluência

Redesenhar `_confluencia()` para discriminar de fato (mais critérios opcionais,
pesos que separem, ou score contínuo), mantendo os setups.

- **Ganha:** endereça a variável que o dono do produto apontou; mudança contida
  em uma função pura.
- **Paga:** **não resolve o problema medido.** A confluência não discrimina
  porque é quase constante, mas os setups são negativos em todas as faixas —
  refinar o ranking de um conjunto uniformemente ruim reordena o ruim.
- **Custo:** médio.
- **Risco:** cria a aparência de correção sem mudar o resultado do usuário. É a
  alternativa mais fácil de aprovar e a menos útil.

---

## Recomendação

**A imediatamente, B em seguida. C só dentro de B, se o backtest mostrar que
vale.**

A separação importa: A é sobre parar o dano em produção e não depende de
descobrir nada; B é sobre construir substituto e pode não dar certo. Tratá-las
como uma coisa só significa deixar o usuário operando um sinal pior que o acaso
enquanto a pesquisa acontece.

C isolada é a armadilha deste ADR: é a resposta literal à pergunta que originou
a investigação ("revisar a confluência") e é a que menos muda o resultado do
usuário.

**Nenhuma das três toca o Princípio 5 nem o guardrail CVM.** Todas mudam *quais*
regras determinísticas o motor usa; nenhuma move decisão para julgamento da IA.
Se em algum momento a proposta for deixar a IA escolher setup, ordenar o Radar ou
decidir entrada, isso é mudança de natureza e exige aprovação separada e
explícita — não entra por dentro de uma dessas alternativas.

---

## Adendo (2026-08-20) — teste de horizonte: hipótese eliminada, e o lado vendido aparece

Rodamos o item 1 da fila da Alternativa B. Duas variantes, porque "horizonte
maior" é ambíguo: alongar só a janela de avaliação não é a mesma coisa que
operar em barra semanal — a segunda muda a própria detecção do setup, e é o que
Pellin fez.

### Variante 1 — mesmos setups diários, horizonte de avaliação maior

| Horizonte | n | Expectância | t | Acerto | Não acionados |
|---:|---:|---:|---:|---:|---:|
| 10 pregões (produto) | 32.095 | −0,104R | −19,7 | 44,8% | 9.049 |
| 20 pregões | 34.439 | −0,110R | −20,9 | 44,5% | 6.667 |
| 40 pregões | 36.347 | −0,114R | −22,1 | 44,3% | 4.723 |
| 60 pregões | 37.059 | −0,113R | −21,9 | 44,4% | 3.948 |

**Hipótese eliminada.** A expectância não melhora — piora de leve e estabiliza.
Nenhum dos 17 pares setup × lado melhora com significância em nenhum horizonte;
os únicos que se movem na direção certa (IFR2 alta: −0,049 → −0,027; Inside Bar
alta: −0,074 → −0,024) continuam negativos e não significativos. Dar mais tempo
ao trade não resolve: o problema não é o alvo não dar tempo de chegar, é a
entrada ser ruim.

### Variante 2 — barra semanal (o análogo direto do Pellin)

> **CORREÇÃO (2026-08-20, mesma data).** A primeira execução desta variante usou
> `range=max`, e o Yahoo devolveu HTTP 200 com velas **MENSAIS** — 320 barras a
> partir de 2000-02-01 — tanto para `interval=1wk` quanto para `1d`. O guard de
> granularidade de `yahoo.get_history` só cobre intervalos intraday, então a
> degradação passou silenciosa. Os números publicados abaixo são da reexecução
> com `range=10y`, que o Yahoo honra em barra semanal de verdade.
> `scripts/backtest_sinal.py` ganhou `_confere_granularidade()`, que recusa a
> série quando o espaçamento mediano entre barras não bate com o intervalo
> pedido — o mesmo tipo de defesa que o ADR-001 já exigia para intraday.

Motor rodado sobre candles semanais reais (`range=10y`), janela de 252 barras
semanais (o que `resolve_keep("1y", "1wk")` daria), horizonte de 10 semanas.

| Recorte | n | Expectância | IC95 | t | Acerto |
|---|---:|---:|---|---:|---:|
| **Geral semanal** | 9.671 | **−0,167R** | — | — | 41,9% |
| Comprado | 4.633 | −0,146R | [−0,17; −0,12] | −10,5 | 42,6% |
| Vendido | 5.038 | −0,187R | [−0,21; −0,16] | −14,3 | 41,2% |
| **IFR2 (alta)** | 263 | **+0,164R** | [+0,05; +0,28] | **+2,79** | 58,2% |
| Setup 9.1 (alta) — *o setup do Pellin* | 552 | −0,070R | [−0,15; +0,01] | −1,72 | 46,2% |
| Setup 9.3 (alta) | 1.152 | −0,096R | [−0,15; −0,04] | −3,39 | 45,1% |
| Setup 9.2 (baixa) | 1.530 | −0,313R | [−0,36; −0,27] | −13,2 | 34,8% |

**Hipótese não confirmada.** O agregado semanal é *pior* que o diário (−0,167R
contra −0,104R), e os dois lados são claramente negativos.

Sobre o **Setup 9.1**, que motivou o teste: com dado semanal real e n = 552, ele
fica em −0,070R (t = −1,72). O resultado do Pellin **não se reproduz** — nem a
magnitude (67% de acerto contra 46,2%) nem a direção. As diferenças de método
que podem explicar: ele usou 4 ativos contra 74, período 2012–2021 contra
2016–2026, e excluiu custos e aluguel de ação.

**O IFR2 (alta) é a exceção que sobrevive.** +0,164R com n = 263 e t = +2,79 —
acima do limiar deflacionado de |t| ≈ 2,4 para 17 configurações. É o único
recorte de toda a investigação que passa por esse crivo. Ver o Adendo 2 para a
ressalva que o qualifica.

### O achado que os dois testes produziram sem que fosse a pergunta

O lado vendido é pior nos dois intervalos:

| Lado | Semanal | Diário (h=10) |
|---|---|---|
| Comprado | −0,146R (t = −10,5) | −0,081R |
| Vendido | −0,187R (t = −14,3) | −0,124R |

Os dois são claramente negativos. Isso motivou o teste do Adendo 2, que eliminou
"só comprado" como remédio.

Ressalva honesta antes de tratar isso como conclusão: o período medido
(2021–2026 no semanal, 2023–2026 no diário) tem viés de alta estrutural, e
"vender é ruim" é o resultado esperado de um mercado que subiu. O teste que
separa "o lado vendido é ruim" de "o período foi de alta" é medir o lado vendido
num período de baixa — está fora do que estes dados cobrem.

### Ressalvas destes testes

- O semanal tem n = 956 contra 32.095 do diário: 33× menos amostra, intervalos de
  confiança muito mais largos.
- CPLE6 e EMBR3 devolveram 404 no Yahoo em intervalo semanal e ficaram fora.
- A janela de 252 barras semanais faz "máxima do período" olhar 5 anos para trás
  — fiel ao que `resolve_keep` daria, mas mais longo do que um operador semanal
  usaria na prática. Janela semanal mais curta é variante não testada.
- Os quatro horizontes diários compartilham os mesmos sinais de entrada, então
  não são amostras independentes — a comparação entre eles é válida, somar as
  significâncias não é.

**Reprodução:**

```
python3 scripts/backtest_sinal.py --anos 3 --horizonte 40 --saida /tmp/h40.json
python3 scripts/backtest_sinal.py --anos 5 --intervalo 1wk --rng max --saida /tmp/sem.json
python3 scripts/backtest_horizonte.py /tmp/linhas-h{10,20,40,60}.json
```

---

## Adendo 2 (2026-08-20) — teste "só comprado": o que parecia edge era o mercado subindo

O adendo anterior mostrou que o lado comprado é muito menos ruim que o vendido
(−0,081R contra −0,124R no diário) e promoveu "só comprado" a item 1 da fila.
Este teste responde se isso é sinal ou beta.

A comparação é **pareada**: para cada sinal comprado, o retorno do trade (entra
no gatilho, sai no stop, no alvo ou no fim do prazo) contra o retorno de ter
comprado **o mesmo papel, no mesmo dia, e segurado pelo mesmo prazo**. Mesmo
ativo, mesma janela, mesmo período — o que sobra da diferença é o que o setup
adiciona. Um terceiro braço entra a mercado num dia sorteado com a mesma
geometria.

### Diário — 15.241 operações compradas

| Braço | Retorno médio/operação | t | Operações positivas |
|---|---:|---:|---:|
| **Setup (entra no gatilho)** | **−0,186%** | −7,1 | 45,8% |
| **Segurar a ação o mesmo prazo** | **+1,307%** | +25,2 | 58,8% |
| Placebo (dia sorteado) | −0,020% | −0,8 | 49,6% |

| Comparação pareada | Diferença | t | Setup vence em |
|---|---:|---:|---:|
| Setup − Segurar | **−1,493%** | **−32,6** | 34,6% dos casos |
| Setup − Placebo | −0,166% | −4,4 | 47,3% dos casos |

### Semanal — 4.625 operações compradas

| Braço | Retorno médio/operação | t |
|---|---:|---:|
| Setup | −0,914% | −8,5 |
| **Segurar a ação o mesmo prazo** | **+2,337%** | +11,7 |
| Placebo (dia sorteado) | +0,913% | +8,5 |

Setup − Segurar: **−3,251%**, t = −18,2, vence em 36,7% dos casos.
Setup − Placebo: −1,827%, t = −12,1.

### Leitura

**"Só comprado" não é solução.** O lado comprado parecia aceitável em R porque R
é normalizado pelo risco e esconde o custo de oportunidade. Em retorno absoluto,
o setup comprado entrega ≈ 0 enquanto simplesmente segurar o mesmo papel pelo
mesmo prazo entregou +1,3% (diário) e +4,2% (semanal). A diferença é de 32
desvios-padrão no diário — não é ruído nem artefato de período.

Em todos os setups menos um, comprar pelo sinal é pior do que comprar e esperar:

| Setup (comprado, diário) | Setup % | Segurar % | Diferença | t |
|---|---:|---:|---:|---:|
| Setup 9.2 (alta) | −0,319 | +1,696 | −2,015 | −22,0 |
| 123 de fundo (alta) | −0,193 | +2,691 | −2,884 | −23,3 |
| Máx/Mín LW 9.4 (alta) | −0,296 | +1,468 | −1,764 | −14,6 |
| Ponto Contínuo (alta) | −0,514 | +1,006 | −1,520 | −6,6 |
| Inside Bar (alta) | −0,128 | +1,368 | −1,496 | −6,2 |
| Setup 9.3 (alta) | −0,004 | +0,745 | −0,749 | −8,3 |
| PFR (alta) | +0,165 | +0,996 | −0,831 | −3,4 |
| Setup 9.1 (alta) | −0,052 | +0,442 | −0,493 | −2,9 |
| **IFR2 (alta)** | **−0,271** | **−0,670** | **+0,399** | **+2,2** |

**A exceção do IFR2 merece leitura cuidadosa, e não é o que parece.** É o único
setup que bate o benchmark, em ambos os intervalos (diário +0,399%, t = +2,2,
n = 695; semanal +7,738%, t = +2,0, n = 40). Mas ele bate porque **segurar é
ainda pior**: o IFR2 dispara em papéis que continuam caindo (hold = −0,670%), e
a saída no alvo captura o repique antes da queda seguir. O mecanismo é
coerente com o que o setup se propõe a fazer — reversão à média com saída
disciplinada — e é o único achado genuinamente interessante de toda a
investigação.

Ainda assim, **não é um produto**: o retorno do próprio setup continua negativo
(−0,271% no diário). O IFR2 é uma forma menos ruim de ficar exposto a papéis que
estão caindo, não uma estratégia com expectativa positiva. Com t = +2,2 contra
um limiar deflacionado de ≈ 2,1 para 9 configurações, sobrevive por margem
estreita — é candidato a investigação, não a decisão.

### Efeito de custos

As comparações pareadas são **invariantes a custo**: setup e benchmark pagam um
round-trip cada, então o custo se cancela na diferença. O que o custo muda é o
nível absoluto — a 0,2% de round-trip (emolumentos + slippage conservador), o
setup diário vai de −0,186% para −0,386% por operação.

O efeito de carteira é pior que isso e não está medido aqui: no mesmo período, a
estratégia de setup faz dezenas de round-trips enquanto segurar faz um. Contar
custo por operação subestima a diferença acumulada a favor de segurar.

### Consequência para as alternativas

Isto **rebaixa "só comprado" de item 1 para fora da fila** como remédio
autônomo, e reforça a Alternativa A: um produto que ensina a entrar por esses
sinais está ensinando algo pior do que comprar e esperar — no lado comprado,
que era o menos ruim, e num período em que o mercado subiu.

O item que sobe na fila é o IFR2 isolado (mecanismo de reversão com saída
disciplinada), e mesmo ele como pergunta de pesquisa, não como feature.

**Reprodução:**

```
python3 scripts/backtest_comprado.py /tmp/linhas-h10.json --intervalo 1d
python3 scripts/backtest_comprado.py /tmp/linhas-semanal.json --intervalo 1wk
```

---

## Adendo 3 (2026-08-20) — 15 anos e regime de mercado: o confound está resolvido

A limitação mais séria dos adendos anteriores era o período: 2023–2026 foi de
alta, e num mercado que sobe "vender é ruim" e "segurar bate o setup" são o
resultado esperado. Um sistema de trading justifica sua existência **justamente
quando segurar é ruim** — isso nunca tinha sido testado.

Reexecução com `range=15y`: **2011-08 → 2026-08, 125.938 sinais resolvidos**.

### O agregado não se move

| Período | n | Expectância | t | Acerto | PF |
|---|---:|---:|---:|---:|---:|
| 3 anos (2023–2026) | 32.095 | −0,104R | −19,7 | 44,8% | 0,80 |
| **15 anos (2011–2026)** | **125.938** | **−0,105R** | **−39,6** | 44,6% | 0,79 |

Quintuplicar o período e quadruplicar a amostra move a expectância em 0,001R.

### Por regime, classificado pelo índice

Anos rotulados pelo retorno do BOVA11 (ETF do Ibovespa) — não pelo retorno dos
dias de sinal. Essa distinção importa: os setups são majoritariamente de
reversão e disparam depois de queda, então a janela seguinte a um sinal tem
drift positivo por construção. Classificar o ano por ela rotularia quase todo
ano como "mercado a favor" — foi o que aconteceu na primeira tentativa, e o
bucket de mercado adverso saiu vazio.

| | Mercado a favor | Mercado contra |
|---|---:|---:|
| Anos | 2012, 2016–2020, 2022, 2023, 2025, 2026 | 2013, 2014, 2015, 2021, 2024 |
| n | 82.835 | 43.103 |
| **Motor (todos)** | **−0,091R** (t = −27,7) | **−0,132R** (t = −29,3) |
| Motor comprado | −0,041R (t = −9,3) | −0,186R (t = −27,6) |
| Motor vendido | −0,156R (t = −31,8) | −0,089R (t = −14,7) |
| Setup comprado | −0,030%/op | −0,526%/op |
| Segurar a ação | +2,304%/op | +0,903%/op |
| Diferença | −2,334 p.p. (t = −77,4) | −1,429 p.p. (t = −33,7) |

**O confound está resolvido, e o resultado piora.** Em mercado adverso o motor
não melhora — vai de −0,091R para **−0,132R**. O lado vendido, que deveria ser
onde um sistema ganha em queda, melhora de −0,156R para −0,089R e **continua
negativo**: nem quando o mercado cai o motor consegue ganhar dinheiro vendendo.
E o lado comprado piora bastante (−0,041R → −0,186R).

Também em anos adversos, segurar a ação continua batendo o setup comprado
(−1,429 p.p., t = −33,7).

> Nota sobre "segurar" ser positivo mesmo em anos de baixa do índice: o
> benchmark mede janelas de 10 pregões que começam num dia de sinal, e os setups
> disparam após queda. Não é o retorno anual do índice, e não deveria ser lido
> como tal. O que ele mede — e é o que importa aqui — é o custo de oportunidade
> de operar o setup em vez de manter a posição naquelas mesmas janelas.

**Conclusão:** os achados do ADR-016 não são artefato do período de alta. O motor
é negativo em 15 anos, nos dois regimes, nos dois lados, com t entre −15 e −40.
A recomendação (Alternativa A imediata) fica mais forte, não mais fraca.

### Correção de integridade de dado descoberta neste adendo

A primeira tentativa usou `range=max` e o Yahoo devolveu HTTP 200 com velas
**mensais** — 320 barras a partir de 2000-02-01 — tanto para `interval=1d`
quanto para `1wk`. O guard de `yahoo.get_history` só cobre intervalos intraday,
então diário e semanal passam batido.

Isso invalidou o teste de barra semanal do Adendo 1, que rodou em barra mensal.
Os números daquele adendo foram **corrigidos** com a reexecução em `range=10y`.
O que mudou de conclusão:

- Semanal geral: −0,197R (n=956, mensal) → **−0,167R (n=9.671, semanal real)**.
- Lado comprado semanal: −0,042R "indistinguível de zero" → **−0,146R
  (t = −10,5)**. A afirmação de que o comprado era neutro no semanal **estava
  errada** e vinha do dado contaminado.
- Setup 9.1 (alta), o do Pellin: +0,094R (n=61) → **−0,070R (n=552, t = −1,72)**.
  O resultado dele **não se reproduz** em barra semanal real.
- IFR2 (alta): +0,315R (n=40, t=+2,17, não sobrevivia à deflação) → **+0,164R
  (n=263, t=+2,79)** — com amostra 6× maior e agora **acima** do limiar
  deflacionado de 2,4. É o único recorte de toda a investigação que passa nesse
  crivo.

`scripts/backtest_sinal.py` ganhou `_confere_granularidade()`, que recusa a série
quando o espaçamento mediano entre barras não bate com o intervalo pedido.
Ranges que o Yahoo honra: `15y`/`1d`, `10y`/`1wk`. `max` degrada para mensal.

### O que isso faz com o IFR2

O IFR2 (alta) agora é o único candidato que sobrevive a todos os crivos
aplicados: positivo em barra semanal (+0,164R, t = +2,79, n = 263), acima do
limiar deflacionado, e no diário é o único setup que bate o benchmark de segurar
(+0,399 p.p., t = +2,2, n = 695).

A ressalva do Adendo 2 continua valendo e é o que impede tratá-lo como feature:
no diário ele bate o benchmark porque **segurar é ainda pior** (−0,670%), e o
retorno próprio dele permanece negativo (−0,271%). No semanal, porém, a
expectância própria é positiva. Os dois fatos juntos sustentam uma hipótese
específica e testável: **o IFR2 pode ter edge real em horizonte semanal e não em
diário** — que é exatamente o tipo de dependência de timeframe que a literatura
de reversão à média prevê. Isso é a primeira coisa a investigar na Alternativa B,
e agora com uma pergunta precisa em vez de uma varredura.

**Reprodução:**

```
python3 scripts/backtest_sinal.py --anos 15 --rng 15y --saida /tmp/longo.json
python3 scripts/backtest_periodo.py /tmp/longo.json --rng 15y
python3 scripts/backtest_sinal.py --anos 8 --rng 10y --intervalo 1wk --saida /tmp/sem.json
```

---

## Adendo 4 (2026-08-20) — momentum relativo: direção certa, sem significância

O candidato com maior lastro acadêmico da pesquisa externa, e que o ADR-009 já
implementou dentro de `regime.ranquear()` como critério de ordenação — nunca
medido como sinal.

Natureza diferente dos setups: não é trade com stop e alvo, é carteira. Ranqueia
o universo por momentum de formação 12-1 (12 meses pulando o mês mais recente, o
pulo padrão da literatura para não capturar reversão de curto prazo), compra a
cesta do topo, rebalanceia. Comparação contra o universo equal-weight.

**165 períodos mensais, 2012-08 → 2026-07, 65 tickers:**

| Carteira | Retorno médio | t | Sharpe a.a. |
|---|---:|---:|---:|
| **Topo de momentum** | **+1,128%** | +2,21 | **+0,60** |
| Universo equal-weight (mercado) | +0,881% | +1,80 | +0,49 |
| Fundo de momentum (o pior) | +0,457% | +0,55 | +0,15 |

A ordenação sai **na direção correta** — topo > mercado > fundo. Mas o que
interessa ao produto é o excesso sobre o mercado, e ele não tem significância:
**+0,246 p.p./mês, t = +0,76**.

**Varredura de 6 configurações, todas reportadas (não a melhor):**

| Cesta | Manutenção | Excesso sobre o mercado | t |
|---:|---:|---:|---:|
| 5 | 1 mês | +0,255 p.p. | +0,59 |
| 10 | 1 mês | +0,246 p.p. | +0,76 |
| 15 | 1 mês | +0,284 p.p. | +1,11 |
| 5 | 3 meses | +1,120 p.p. | +0,92 |
| 10 | 3 meses | +0,631 p.p. | +0,70 |
| 15 | 3 meses | +0,659 p.p. | +0,93 |

Positivo em 6 de 6, com Sharpe superior ao mercado em 6 de 6. Nenhuma atinge
|t| = 2. As configurações compartilham quase todo o dado, então a consistência de
sinal **não** é evidência independente — mas também não é o padrão que ruído puro
costuma produzir.

### A ressalva que impede tratar isso como promissor

**O viés de sobrevivência atinge o momentum muito mais que os setups.**
`DEFAULT_UNIVERSE` é a lista de líquidas de *hoje*. Uma estratégia que compra
vencedores dos últimos 12 meses, dentro de um universo pré-selecionado por ter
sobrevivido e permanecido líquido, sofre dupla seleção. Parte ou todo o
+0,25 p.p./mês pode ser artefato disso.

Nos setups esse viés era secundário — eles eram negativos *apesar* de o universo
favorecê-los. Aqui ele é a explicação alternativa mais provável para o resultado.
Testar de verdade exige composição histórica do índice (point-in-time), que não
temos.

### Onde isso deixa o momentum

Categoricamente diferente dos setups, e vale registrar a diferença:

| | Resultado | Leitura |
|---|---|---|
| 13 setups de price action | Negativo, t = −20 a −40 | **Refutado** |
| Momentum relativo | Positivo, t = +0,6 a +1,1 | **Não provado** — nem confirmado nem refutado |

"Não provado" não é "promissor". Com o viés de sobrevivência por cima, o
resultado honesto é: momentum não entrega edge demonstrável neste universo e
neste método, e a evidência que existe não separa efeito real de artefato de
seleção.

**Reprodução:**

```
python3 scripts/backtest_momentum.py --rng 15y --cesta 10 --manutencao 21
```

---

## Adendo 5 (2026-08-20) — o Modo Operador de verdade: pior que o Modo Estudo

**Lacuna que este adendo fecha, e ela era real:** tudo até aqui mediu stop fixo +
alvo1 fixo (1R) — a mecânica do Modo **Estudo**. O Modo Operador tem trailing
stop (`agent.py:366-428`, ATR 2× por padrão, stop só sobe) e alvo dinâmico com
até 2 extensões de 1,5× ATR (`agent.py:444-478`). A afirmação "o motor perde
dinheiro" estava medida sobre a máquina errada.

Réplica fiel da ordem de checagem de `agent.py:804-836`: trailing primeiro, stop
depois (contra `low`, empate a favor do stop), alvo por último (contra `high`),
e com `alvoDinamico` ligado o alvo batido tenta estender antes de fechar. Teto de
60 barras — o Operador não tem prazo fixo, e o trailing precisa de espaço.

| Braço | n | Expectância | t | Acerto | Ganho médio | Perda média |
|---|---:|---:|---:|---:|---:|---:|
| **A · fixo** (stop + alvo 1R) — o que se mediu antes | 34.587 | **−0,115R** | −21,6 | 44,3% | +1,00R | −1,00R |
| **B · trailing ATR 2×**, sem alvo | 34.587 | −0,160R | −17,8 | 25,3% | **+1,99R** | −0,89R |
| **C · trailing + alvo dinâmico** (config real do Operador) | 34.587 | **−0,167R** | −22,3 | 25,3% | +1,96R | −0,89R |
| **D · 50% em 1R + trailing no resto** | 34.587 | −0,142R | −22,6 | 37,0% | +1,09R | −0,92R |

### A hipótese da assimetria estava mecanicamente certa e mesmo assim falhou

O raciocínio que motivou o teste: com `alvo1 = entrada ± risco`, o alvo é
exatamente 1R, e numa barreira simétrica a expectância é ≈ 2p − 1. Com p = 44,3%
isso dá −0,114R **por aritmética**, independente da qualidade do sinal. A saída
proposta era assimetria: cortar em 1R, deixar o vencedor correr.

**A assimetria materializou exatamente como previsto** — o trailing dobrou o
ganho médio (+1,00R → +1,99R) e ainda reduziu a perda média (−1,00R → −0,89R).
Razão de payoff de 2,2:1, que é território profissional.

**E a expectância piorou**, porque a taxa de acerto caiu de 44,3% para 25,3%:

- A: 0,443 × 1,00 − 0,557 × 1,00 = **−0,114R**
- B: 0,253 × 1,99 − 0,747 × 0,89 = **−0,162R**

O trailing devolve o movimento antes de ele virar ganho, e faz isso com
frequência suficiente para engolir todo o benefício do payoff. Não é falha de
calibração do multiplicador — é o que acontece quando se aplica gestão de saída
sofisticada sobre uma entrada sem informação.

### O Operador real é o pior dos quatro

A configuração que o produto de fato executa (C) entrega **−0,167R**, contra
−0,115R do plano de Estudo. O alvo dinâmico piora um pouco o trailing puro: ele
estende a posição justamente nos casos que estavam indo bem, e devolve.

Isso vale para **todos os 17 pares setup × lado sem exceção** — nenhum melhora
sob a mecânica do Operador. Até PFR (alta), que era o único nominalmente positivo
no braço fixo (+0,009R), fica negativo em B, C e D.

### O que isso ensina, e é a lição profissional de sempre

**Gestão de risco não cria edge — ela limita estrago.** Trailing, alvo dinâmico,
parcial: todos fazem exatamente o que prometem na distribuição de resultados
(payoff sobe, perda média cai) e nenhum transforma expectância negativa em
positiva. Não se gerencia a saída de uma entrada ruim até ela virar boa.

**Consequência para a decisão:** o argumento de que "o Operador precisa ser
medido antes de mexer nele" está atendido, e o resultado **fortalece** a urgência
em vez de aliviá-la. O Modo Operador não é o Modo Estudo com proteção melhor —
ele executa automaticamente, com dinheiro simulado do usuário, a pior das quatro
mecânicas medidas.

### O que este adendo NÃO testou

- **Regime como gate de ativação** (volatilidade corrente decide qual família
  opera). Continua sendo a leitura séria de "levar em conta dados atuais", e não
  foi medida aqui.
- **Sizing por volatilidade e gestão de carteira** (risco igual por posição, teto
  de exposição bruta, limite de correlação). Vale registrar a aritmética: com
  expectância negativa por operação, sizing melhor **reduz a velocidade da perda
  e o drawdown, não a inverte**. É defesa contra ruína, não fonte de retorno.

**Reprodução:**

```
python3 scripts/backtest_operador.py /tmp/linhas-h10.json --rng 5y
```

---

## Adendo 6 (2026-08-20) — gate de regime e volatilidade: o espaço de soluções por regra se esgota

Última hipótese viva: cada família só funciona no ambiente para o qual foi
desenhada, e o produto dispara todas em todo lugar. `regime.classificar()` deixa
de ser desempate de ordenação (ADR-009) e vira **porta** — sinal desalinhado é
descartado, não rebaixado. Mais uma dimensão nunca medida: volatilidade corrente
(ATR14/close no percentil da própria história do ativo), que é o insumo mais
"atual" que o snapshot carrega.

Base: 125.938 sinais, 15 anos, braço de saída fixo — o mais favorável, já que o
Adendo 5 mostrou que a mecânica do Operador piora todos os 17 pares.

| Recorte | n | Expectância | t | Acerto |
|---|---:|---:|---:|---:|
| Todos os sinais (o produto hoje) | 125.938 | −0,105R | −39,6 | 44,6% |
| **Reversão em lateral** | 22.679 | **−0,051R** | −8,3 | 47,4% |
| Reversão em volatilidade alta | 12.144 | −0,055R | −6,7 | 46,8% |
| Reversão em lateral + vol. alta | 7.634 | −0,050R | −4,8 | 47,2% |
| **Continuação alinhada à tendência** | 26.845 | **−0,128R** | −22,0 | 43,4% |
| Continuação alinhada + vol. baixa/média | 18.110 | −0,119R | −16,7 | 43,8% |

**O gate completo corta 60,7% dos sinais e o que sobra continua em −0,093R**
(t = −22,0), contra −0,113R do que foi barrado. A separação existe — 0,021R — e é
informação real, mas de magnitude irrelevante frente ao buraco.

Dois achados dentro disso merecem registro:

**A literatura acerta a direção.** Reversão em mercado lateral é o melhor recorte
famíliar × regime de toda a investigação: −0,051R, metade do dano da base, com
47,4% de acerto. É exatamente onde a teoria de reversão à média diz que ela deve
funcionar. Só não é suficiente para cruzar o zero.

**A tese do ADR-009 é refutada com mais força.** Continuação **alinhada** à
tendência é **pior** que a base (−0,128R contra −0,105R). Alinhar o setup de
continuação com o regime, que é o coração do ADR-009, piora o resultado em vez de
melhorá-lo.

### Volatilidade não carrega informação nenhuma

| Volatilidade | n | Expectância | t |
|---|---:|---:|---:|
| Baixa | 41.509 | −0,113R | −24,1 |
| Média | 41.539 | −0,100R | −21,6 |
| Alta | 42.890 | −0,103R | −22,8 |

Nulo limpo. A leitura mais literal de "levar em conta dados atuais" não separa
nada.

### Nenhuma célula sobrevive

24 células família × regime × volatilidade com n ≥ 200. A melhor é
`reversão · indefinido · alta`: +0,066R com n = 342 e **t = +1,37** — abaixo até
do limiar solto de 2, quanto mais do deflacionado de 2,5 para 24 tentativas. E
"indefinido" é a categoria degenerada do classificador (sem SMA200 confiável),
não um regime de mercado.

### O que este adendo encerra

Todo mecanismo que um operador profissional acionaria foi medido:

| Mecanismo | Resultado |
|---|---|
| Sinal de entrada | Refutado (15 anos, dois regimes, perde do acaso) |
| Gestão de saída (trailing, alvo dinâmico, parcial) | Refutado — payoff sobe, acerto cai mais |
| Horizonte (10/20/40/60) | Refutado |
| Timeframe (semanal) | Refutado, exceto IFR2 |
| Restrição de lado (só comprado) | Refutado — perde de segurar |
| Gate de regime | Refutado — melhor combinação em −0,051R |
| Filtro de volatilidade | Nulo |
| Momentum relativo | Não provado, viés de sobrevivência |

**Sobra o IFR2 semanal** (+0,164R, n = 263, t = +2,79) — e note que ele é
reversão à média, coerente com o único recorte que a literatura acertou aqui.

O espaço de soluções por engenharia de regra sobre este conjunto de sinais está
esgotado. Não é falta de sofisticação na implementação: é ausência de sinal para
gerenciar.

**Reprodução:**

```
python3 scripts/backtest_gate.py /tmp/linhas-longo.json --rng 15y
```

---

## Limitações

- ~~**Período único.**~~ **Resolvido no Adendo 3**: reexecução sobre 2011–2026
  (125.938 sinais) dá −0,105R contra os −0,104R de 3 anos, e o motor é negativo
  tanto nos anos de alta quanto nos de baixa do índice — pior nos de baixa.
- **Viés de sobrevivência.** `DEFAULT_UNIVERSE` é a lista de líquidas de hoje;
  empresas que saíram do índice no período não estão. Isso favorece o motor, não
  o contrário — o resultado real tende a ser pior.
- **Custos não modelados.** Sem corretagem, emolumentos, spread explícito ou
  slippage. Todos empurram a expectância para baixo.
- **10 pregões é o horizonte do produto**, não necessariamente o dos setups.
  Alguns podem funcionar em horizonte maior — não foi testado. É hipótese
  aberta para a Alternativa B.
- **17 configurações testadas** na tabela por setup, 49 na tabela setup ×
  regime. Nenhuma sobreviveu ao limiar deflacionado — o problema aqui é ausência
  de edge, não sobreajuste. Se alguma tivesse passado, precisaria de validação
  out-of-sample antes de virar decisão.
- **O placebo entra a mercado**, enquanto parte dos sinais reais espera gatilho.
  Os 9.049 sinais que nunca acionaram ficam fora do denominador do motor e não
  têm equivalente no placebo. Isso é conservador para o motor: o recorte do
  placebo é o pior caso para ele.

## Referência cruzada

- `docs/adr/015-assertividade-do-motor-de-recomendacao.md` — a medição estava
  quebrada e otimista; este ADR mede o que ela deveria ter medido.
- `docs/adr/009-eixo-de-selecao.md` — regime como eixo primário. A tese não se
  sustenta como implementada: nenhuma célula setup × regime é positiva.
- `.planning/phases/06-instrumentacao-assertividade-adr015/` — Phase 6 conserta a
  instrumentação. Continua valendo: sem medidor confiável não há como acompanhar
  o efeito de nenhuma mudança deste ADR.
- `scripts/backtest_sinal.py` · `scripts/backtest_analise.py` ·
  `scripts/backtest_placebo.py` — o harness. Todo número deste documento sai
  deles e é reprodutível.
