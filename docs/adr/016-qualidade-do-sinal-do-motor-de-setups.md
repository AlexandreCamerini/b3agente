# ADR-016: Qualidade do sinal do motor de setups — diagnóstico e caminho

**Status:** Proposto — aguardando decisão. Nenhum código de produção foi alterado.
**Data:** 2026-08-20
**Gatilho:** observação do dono do produto de que os ativos com confluência 100%
para alta saíram majoritariamente por stop, com o usuário perdendo dinheiro.
**Companion:** ADR-015 (medição). Este ADR é sobre o **sinal**, não sobre o medidor.
**Harness:** `scripts/backtest_sinal.py`, `scripts/backtest_analise.py`,
`scripts/backtest_placebo.py` — reexecutáveis, sem I/O de produção.

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
4. **Momentum relativo cross-sectional** — o ADR-009 já o implementou em
   `regime.ranquear` mas nunca o isolou como sinal. É a família com mais lastro
   acadêmico de toda a pesquisa.
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

Motor rodado sobre candles semanais, janela de 252 barras semanais (o que
`resolve_keep("1y", "1wk")` daria), horizonte de 10 semanas, ~5 anos de sinais.

| Recorte | n | Expectância | IC95 | t | Acerto |
|---|---:|---:|---|---:|---:|
| **Geral semanal** | 956 | **−0,197R** | [−0,26; −0,14] | −6,5 | 40,9% |
| IFR2 (alta) | 40 | +0,315R | [+0,03; +0,60] | +2,17 | 65,0% |
| Setup 9.1 (alta) — *o setup do Pellin* | 61 | +0,094R | [−0,15; +0,34] | +0,74 | 55,7% |
| Setup 9.3 (alta) | 126 | +0,051R | [−0,12; +0,22] | +0,58 | 53,2% |
| Setup 9.2 (baixa) | 150 | −0,515R | [−0,65; −0,38] | −7,69 | 24,7% |

**Hipótese não confirmada.** O agregado semanal é *pior* que o diário. Um único
setup fica nominalmente significativo — IFR2 (alta), t = +2,17 — e não sobrevive
à correção por seleção múltipla: com 16 configurações testadas o limiar prudente
é |t| ≈ 2,35. Com n = 40, é indício, não resultado.

Sobre o Setup 9.1 especificamente, que motivou o teste: a **direção** do Pellin
se confirma (positivo, 55,7% de acerto no lado comprado), a **magnitude** não
(ele reportou 67% e relação lucro/prejuízo 5,34). Com n = 61 e t = +0,74, o
resultado é compatível tanto com "há um efeito pequeno" quanto com "não há
efeito". Não é base para decisão. Vale registrar que o n de Pellin (12–14
operações por ativo × 4 ativos) é da mesma ordem do nosso — o problema de
amostra é dos dois lados, e ele ainda excluiu custos e aluguel de ação.

### O achado que os dois testes produziram sem que fosse a pergunta

O lado vendido é o que destrói o resultado, e a separação é muito mais nítida na
barra semanal:

| Lado | Semanal | Diário (h=10) |
|---|---|---|
| Comprado | **−0,042R** (t = −0,95 — indistinguível de zero) | −0,081R |
| Vendido | **−0,356R** (t = −8,94) | −0,124R |

No semanal, o lado comprado é estatisticamente indistinguível de zero e o
vendido carrega praticamente todo o prejuízo. O padrão se repete em todos os
horizontes diários e em todos os regimes. Isso **promove "só comprado" de item 3
para item 1 da fila da Alternativa B** — é a mudança de maior efeito medido por
menor esforço, e não depende de descobrir sinal novo.

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
(−0,042R contra −0,356R no semanal) e promoveu "só comprado" a item 1 da fila.
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

### Semanal — 480 operações compradas

| Braço | Retorno médio/operação | t |
|---|---:|---:|
| Setup | −0,249% | −0,4 |
| **Segurar a ação o mesmo prazo** | **+4,177%** | +4,2 |
| Placebo (dia sorteado) | +1,957% | +3,3 |

Setup − Segurar: **−4,426%**, t = −5,05, vence em 36,0% dos casos.

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

## Limitações

- **Período único.** 2023-07 a 2026-08 — um regime de mercado. O sinal do
  resultado (negativo, t ≈ −20) é robusto o bastante para não depender disso, mas
  a magnitude sim.
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
