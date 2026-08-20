# Pesquisa externa — qualidade de sinal em sistemas sistemáticos (foco B3)

> Insumo para ADR de produto. Ponto de partida (já verificado internamente, não
> re-testado aqui): a confluência do motor determinístico do Boris+ quase não
> varia — em 2 dos 13 setups só pode valer 100%; em 5 outros só 86% ou 100%.
> Entrou como critério de ordenação do Radar mas carrega pouca informação.
>
> Rótulo de evidência usado em todo o documento:
> **[QUANT]** = evidência quantitativa publicada (paper acadêmico, journal,
> ou backtest com metodologia auditável) · **[PRÁTICA]** = prática difundida
> entre operadores/casas, sem estudo rigoroso por trás · **[OPINIÃO]** =
> heurística ou afirmação de operador individual, sem backtest conhecido.
>
> Nada neste documento constitui promessa de rentabilidade ou recomendação de
> investimento. Todo item da Seção 3 é uma hipótese a testar, não um resultado.

---

## 1. Por que confluência de checklist falha como preditor

**Multicolinearidade entre indicadores derivados do mesmo preço [QUANT].**
Um diagnóstico de multicolinearidade em 39 indicadores técnicos encontrou VIF
(fator de inflação de variância) acima de 5 em todos exceto quatro (ADX, PSY,
VHF, VR) — ou seja, a esmagadora maioria dos indicadores técnicos populares
carrega informação redundante entre si, porque todos derivam da mesma série
de preço/volume por transformações correlatas (Shukla, "Multicollinearity of
Technical Indicators"; MDPI 2022, "A Correlation-Embedded Attention Module to
Mitigate Multicollinearity"). Um estudo cita que metade dos investidores de
varejo que usam múltiplos indicadores técnicos tem resultado ruim justamente
por empilhar indicadores colineares, não independentes.

**Ilusão de confirmação [PRÁTICA/OPINIÃO, mas amplamente reconhecida].**
A analogia central da literatura de trading: RSI, estocástico e MACD todos
sinalizando "sobrecomprado" ao mesmo tempo não são três confirmações
independentes — é a mesma informação de momentum repetida três vezes de
formas diferentes. Se cinco checklist-items nascem do mesmo cálculo de
variação de preço recente, "5 de 5" não é mais forte que "1 de 1"; é a
mesma fonte ouvida cinco vezes (SMC Tutors; InsiderFinance; MQL5 Traders'
Blog, ago/2026). A prescrição repetida na literatura de prática é usar
fatores de confluência que vêm de **conceitos de preço não-correlatos**
(estrutura vs. momentum vs. volume vs. volatilidade), não variações do
mesmo cálculo.

**Como isso explica o achado interno.** Os 13 setups do Boris+ são famílias
de price action clássicas (rompimento de estrutura, IFR2, PFR, 123, inside
bar) cujos checklists de confirmação tendem a testar o mesmo evento —
"o candle fechou na direção certa", "rompeu a mínima/máxima anterior" — sob
ângulos ligeiramente diferentes. Isso é consistente com o padrão descrito na
literatura: quando os itens do checklist não são estatisticamente
independentes, o percentual de confluência tende a colapsar num conjunto
pequeno de valores possíveis (comportamento binário/quase-binário), que é
exatamente o sintoma relatado (2 setups só 100%, 5 só 86%/100%).

**Consequência de design (não uma hipótese de backtest, é lógica estrutural):**
confluência-como-está não deveria ser usada como critério de *ranking*
contínuo. Ou ela é redesenhada para agregar fatores comprovadamente
não-correlatos (ver Seção 3), ou é removida do papel de ordenação do Radar e
mantida só como checklist educacional (mostrar o "porquê" do setup, papel
que o CLAUDE.md do projeto já atribui à IA — nunca susbtituir o motor
determinístico).

---

## 2. O que tem evidência em price action de curto prazo

| Fenômeno | Evidência | Tipo | Nota |
|---|---|---|---|
| Reversão de curto prazo (1 semana) | Lehmann (1990): comprar perdedores da semana anterior / vender vencedores gerou ~1,5%/semana bruto nos EUA | **[QUANT]** | Efeito clássico, mas explicado em parte por pressão de liquidez/custo de execução — o próprio paper de decomposição do NY Fed (Nagel et al.) atribui parte do retorno a "provisão de liquidez", não a padrão de preço puro |
| Reversão de curto prazo (1 mês) | Jegadeesh (1990): correlação serial negativa mensal, ~2%/mês extra 1934–1987 | **[QUANT]** | Horizonte mensal, mais longo que a maioria dos 13 setups do Boris+ (que operam em barras diárias/15min) |
| Padrões de candlestick (2–3 dias) | Resultado misto: Caginalp & Laurent (1998) e um teste out-of-sample em S&P500 1992–96 encontraram poder preditivo estatisticamente significativo em alguns padrões de 3 dias; um estudo em 29 ações do OMXS30 sueco (2007–2015) não encontrou poder preditivo nenhum; estudo no mercado chinês achou poder preditivo variável por padrão, caindo conforme aumenta o horizonte de previsão | **[QUANT], mas inconsistente entre mercados/períodos** | Não há consenso — "não existe até hoje evidência conclusiva a favor ou contra" é a conclusão mais honesta da literatura. Tratar qualquer padrão de candle isolado como fraco preditor por padrão |
| Momentum de série temporal (tendência, 3–12 meses) | Moskowitz, Ooi & Pedersen (2012): retorno passado de 12 meses prediz retorno futuro em 58 mercados futuros por 25+ anos; AQR replicou por quase 100 anos de dados | **[QUANT], robusto** | Horizonte mais longo que price action de curto prazo — é o fundamento acadêmico de trend-following, não de setups de 1 a 5 dias. Relevante como *filtro de regime* (Seção 3), não como setup em si |
| Análise técnica no Ibovespa especificamente | Chen & Metghalchi (CCSE, *Int'l Journal of Economics and Finance*): testaram combinações de indicadores populares no Bovespa, 1996–2011 (~14,8 anos); regras técnicas não superaram buy-and-hold; poucas que pareciam lucrativas perderam a vantagem ao contabilizar juro do período fora do mercado. Conclusão: suporte forte à eficiência de forma fraca no mercado brasileiro | **[QUANT]** | É a evidência mais diretamente aplicável ao universo do produto (ações B3). Resultado desfavorável a análise técnica genérica — eleva a régua de exigência para qualquer setup/filtro do Boris+ provar valor além do acaso |
| RSI-2 (Larry Connors) | Taxa de acerto de 75–79% relatada em múltiplos backtests de praticantes ao longo de 10+ anos | **[PRÁTICA]**, não **[QUANT]** | Amplamente citado mas sem publicação peer-reviewed encontrada — são backtests de blogs/livros de trader, metodologia não auditável publicamente. Taxa de acerto alta não implica expectância positiva (ver item 6) |
| Setup 9.1 (Larry Williams/Wolwacz) especificamente em ações B3 | Pellin (2022), *Análise Técnica no mercado financeiro: a eficácia do setup 9.1 de Larry Williams como estratégia de investimentos* — XLVI EnANPAD 2022. Backtest manual, gráfico semanal, 4 ativos do Ibovespa sorteados (ABEV3, CSNA3, PETR3, CPFE3), 2012–2021 (10 anos). Taxa de acerto agregada 67%, ganho médio 22%, perda média −4,12%, relação lucro/prejuízo 5,34. Retorno acumulado (soma aritmética simples dos % de cada trade, não capital composto) de 699,44% contra 134,98% do Buy-and-Hold e 79,18% do Ibovespa no período | **[QUANT]**, mas com limitações metodológicas relevantes | É a evidência quantitativa mais diretamente aplicável a um dos 13 setups do Boris+ (9.1) especificamente em ações B3. **Limitações que reduzem a confiança no número:** (a) só 12–14 operações por ativo em 10 anos — N pequeno, alta variância possível por sorte; (b) autor exclui explicitamente custo de operação, incluindo aluguel de ação para as vendas a descoberto (75% das operações de ABEV3 foram vendidas), o que tende a inflar o resultado real; (c) o "acumulado" é soma aritmética de retornos percentuais de trades não sobrepostos, não retorno composto sobre capital — infla a magnitude versus o que um investidor realmente capturaria; (d) só 4 ativos, um período, sem walk-forward nem correção por seleção múltipla. Direção do resultado (setup bate buy-and-hold) é sugestiva, magnitude não deve ser tomada literalmente |

**Leitura para o produto:** a única linha da tabela com evidência acadêmica
forte e diretamente sobre o mercado-alvo (ações B3) é desfavorável a preditividade
de análise técnica pura. Isso não invalida os 13 setups — eficiência de forma
fraca é sobre a média do mercado, não sobre cada subconjunto de ativos/regimes —
mas estabelece o ônus da prova: qualquer setup do Boris+ que alegue vantagem
precisa demonstrá-la em backtest out-of-sample com controle de seleção múltipla
(Seção 6), não assumi-la pela tradição da escola de price action.

---

## 3. Filtros que valem testar (hipóteses de backtest)

Cada item seguindo o formato pedido. "Ganho esperado" é qualitativo — nenhum
número de retorno é prometido.

Formato por linha: **Hipótese** | **Fonte** | **Tipo de evidência** | **Como
testar no backtest** | **Ganho esperado**. Ordenado por prioridade de
execução sugerida (a última linha é a de maior prioridade — liga direto ao
achado que motivou a pesquisa).

| # | Hipótese | Fonte | Tipo de evidência | Como testar no backtest | Ganho esperado |
|---|---|---|---|---|---|
| 1 | Setups de reversão/rompimento têm melhor expectância operados a favor do regime de prazo maior (ex.: preço acima da SMA200 para long) do que sem filtro. | Faber (2007), *A Quantitative Approach to Tactical Asset Allocation* — SMA de 10 meses reduziu drawdown mantendo retorno em alocação de classes de ativos, 1901–2012. | [QUANT], mas sobre *classes de ativos*, não setups diários de ações individuais — extrapolação, não transferência direta. | Rodar os 13 setups com e sem filtro de regime (ex.: SMA200 diária) sobre o mesmo universo B3 e período; comparar expectância (não só taxa de acerto) dentro/fora do filtro. | Redução de drawdown mais provável que ganho de retorno bruto — regime filter historicamente corta cauda ruim mais do que aumenta média. Ver linha 2: não é garantia automática, depende do setup. |
| 2 | Para o IFR2, filtro de tendência por médias móveis (MMA50/MMA200/EMA80) melhora o resultado versus IFR2 puro. | QuantBrasil, "Backtest da Estratégia de IFR2 Utilizando Médias Móveis Como Filtro" (LREN3, 2015–2020). | [QUANT] — metodologia e números publicados, mas ativo único, período curto (~6 anos), sem correção para múltiplos testes. | Replicar a mesma estrutura (com/sem filtro de MA) no universo real do Radar do Boris+, não só um ativo, antes de assumir que "filtro de tendência = sempre melhor". | **Resultado já obtido (não repetir cego):** filtro de MMA50 reduziu operações de 160→100 e retorno/operação caiu de 0,86%→0,69–1,08%; autor conclui que **não houve melhoria significativa**, apesar de leve queda de drawdown (9,49–11,31%). Achado mais importante da Frente B — contraria a intuição da linha 1. |
| 3 | Setups de rompimento (PFR, rompimento com volume, ponto contínuo) têm expectância melhor quando volume do candle de gatilho é ≥1,5× a média anterior, vs. sem filtro de volume. | Prática difundida entre traders de rompimento no Brasil (regra "-30% da média = evitar entrada"); estatística de "+8–12pp de acerto com confirmação 1,5×" citada em blog de squeeze breakout (QuantifiedStrategies). | [PRÁTICA] a regra em si; o número +8–12pp é [QUANT] de baixa confiabilidade — metodologia não auditável e não é sobre B3. | Medir expectância do PFR/rompimento-com-volume com e sem limiar de volume relativo no universo B3 real, antes de aceitar a magnitude citada. | Direção plausível (reduzir falsos rompimentos é lógica clássica de leitura de fita); magnitude desconhecida até teste próprio. |
| 4 | Dimensionar posição pelo ATR (volatility targeting) melhora Sharpe/drawdown da carteira simulada frente a tamanho fixo, mesmo sem mudar as entradas. | Literatura de risk parity/volatility targeting em trend-following (Concretum Group; prática difundida em CTAs); base teórica em Moskowitz, Ooi & Pedersen (2012). | [QUANT] no princípio geral (padrão em fundos sistemáticos), mas nenhuma fonte encontrada testa isso especificamente em ações B3 de varejo. | No motor de simulação existente, comparar tamanho fixo vs. tamanho ∝ 1/ATR sobre os mesmos sinais; medir Sharpe/drawdown da carteira, não do trade isolado. | Ganho mais provável em regularidade de risco (drawdown mais previsível) que em retorno absoluto — é o que a literatura consistentemente relata. |
| 5 | Aplicar piso de liquidez (volume financeiro médio diário) como filtro de elegibilidade do Radar reduz viés de slippage/custo não-modelado no backtest. | Prática difundida entre corretoras/educadores de day trade brasileiros — piso citado "~R$50 milhões/dia" para day trade líquido; para swing, referência solta "acima de R$1 milhão/dia". | [PRÁTICA] — nenhum estudo formal encontrado que valide o limiar específico; heurística de mercado, não resultado de pesquisa. | Comparar expectância dos 13 setups com e sem piso de liquidez no universo elegível; medir se ativos ilíquidos concentram os resultados extremos. | Não é sobre inflar retorno; é correção de viés de mensuração — ativo ilíquido no backtest tende a mostrar edge que não sobrevive à execução real. |
| 6 | Setups de reversão (IFR2, PFR, 123) têm expectância pior quando disparados na semana de vencimento de opções (3ª sexta do mês) ou perto do vencimento de futuros de índice (quarta mais próxima do dia 15), por pinning perto de strikes com grande OI. | Conceito de pinning/max pain difundido na literatura de opções; calendário de vencimento é fato documentado da B3. | [OPINIÃO/PRÁTICA] — nenhum estudo quantitativo B3-specific sobre magnitude do efeito em ações individuais foi encontrado. | Segmentar o backtest por "semana de vencimento" vs. resto do mês, para ativos com maior OI em opções (blue chips mais líquidas), e comparar expectância. | Desconhecido — hipótese exploratória, não extrapolação de resultado publicado. Pode não haver efeito mensurável fora de um pequeno grupo de papéis com opções líquidas. |
| 7 | A ordenação atual do Radar por confluência (que carrega pouca informação, Seção 1) tem desempenho indistinguível de ordenação aleatória dentro do subconjunto já filtrado por regime+gatilho; substituí-la por score de fatores não-correlatos (distância normalizada ao stop estrutural, inclinação do regime, ATR relativo) teria poder de ranking maior. | Síntese própria a partir da Seção 1 (multicolinearidade) + Seção 6 (deflação por seleção múltipla). | Dedução lógica a partir de evidência [QUANT] de outros contextos — não testada diretamente aqui. | Comparar, em walk-forward, o retorno médio dos top-N do Radar ordenados por (a) confluência atual, (b) aleatório dentro do subconjunto pré-filtrado, (c) score alternativo. Se (a) não vence (b) de forma estatisticamente significativa após deflação por nº de variantes, confluência não cumpre função de ranking. | **Maior prioridade de execução** — é o teste ligado diretamente à decisão de produto que motivou esta pesquisa. |

## 4. Setups ausentes que mereceriam teste

- **Rompimento de N dias / canal de Donchian (trend-following clássico).**
  [QUANT] — base acadêmica robusta (Moskowitz, Ooi & Pedersen 2012; "A
  Century of Evidence on Trend-Following Investing", AQR). É o setup de
  price action com *mais* evidência acadêmica de toda a pesquisa, mas em
  horizonte mais longo (semanas–meses) que a maioria dos 13 atuais — cabe
  melhor em um "Setup 14" de médio prazo do que como concorrente direto dos
  setups de 1–5 dias.

- **Pairs trading (par de ações correlacionadas, spread mean-reverting).**
  [QUANT] — há paper específico sobre o mercado brasileiro: "Evaluation of
  pairs-trading strategy at the Brazilian financial market" (*Journal of
  Derivatives & Hedge Funds*, Springer). Não é price-action single-asset como
  os 13 atuais — é uma família estrutural diferente (estatística/relativo
  valor) — mas tem evidência direta para B3 que nenhum dos 13 setups atuais
  possui.

- **VWAP / VWAP ancorado (leitura de abertura intraday).**
  [PRÁTICA] — citado por operadora profissional brasileira (Maria Silveira,
  via InfoMoney) como parte de como lê abertura de mercado combinando VWAP +
  liquidez + gaps. Nenhuma evidência quantitativa rigorosa encontrada, nem
  para B3 nem genérica — é prática de mesa, não resultado de pesquisa.

- **Opening Range Breakout (ORB).**
  [PRÁTICA, com números quantitativos de origem duvidosa] — estatísticas
  citadas (56% de acerto no OR de 15min, 65% no S&P) vêm de blogs de
  estratégia sobre mercado americano, sem relação com B3/mini-índice. Setup
  amplamente usado por day traders de futuros no Brasil (WIN/WDO), mas
  nenhuma fonte B3-specific com metodologia auditável foi encontrada — é
  candidato a teste próprio, não a importação de número alheio.

- **Cruzamento de médias móveis (golden/death cross) e estratégias de MA
  aplicadas a mercados emergentes/BRICS.**
  [QUANT, resultado misto] — há paper (*Financial Innovation*, Springer,
  "Examination of the profitability of technical analysis based on moving
  average strategies in BRICS") cujo abstract indica avaliação de MA em
  mercados BRICS incluindo Brasil; não foi possível recuperar o texto
  completo (paywall/redirect de autenticação) para extrair números
  específicos do Brasil — sinalizado como fonte a perseguir, não como
  evidência confirmada.

---

## 5. Especificidades da B3 que afetam o desenho

- **Leilão de abertura e fechamento fixam O/C, não negociação contínua.**
  O leilão de abertura ocorre nos 15 minutos antes do pregão regular; o de
  fechamento, nos 5 minutos finais — o preço de abertura/fechamento vem do
  cruzamento de ordens no leilão, não do primeiro/último negócio contínuo
  [fato documentado, B3/nelogica]. Qualquer setup que use O ou C como
  referência (9.1/9.2 tipicamente usam abertura) está, na prática, usando um
  preço formado por mecanismo de leilão — relevante para o motor de dados
  saber se está replicando isso corretamente.

- **Circuit breaker é por índice (Ibovespa), não por papel, e em 3 níveis.**
  Queda de 10% → pausa de 30 min; 15% (após reabertura) → pausa de 1h; 20%
  → suspensão por tempo indeterminado a critério da B3. Regra não se aplica
  nos últimos 45 minutos do pregão [B3/múltiplas fontes convergentes]. Evento
  raro mas categórico: qualquer backtest ou execução simulada que atravesse
  esses dias precisa tratar a lacuna de negociação como dado ausente, não
  como preço achatado — reforça o princípio já presente no CLAUDE.md do
  projeto ("não invente valores; mostre o estado correto").

- **Vencimento de opções (mensal, 3ª sexta) e semanal; futuros de índice/dólar
  (mensal, quarta mais próxima do dia 15).**
  Fato documentado (B3). O efeito de pinning/max pain sobre o papel
  subjacente é conceito difundido na literatura de opções, mas não há
  estudo quantitativo B3-specific encontrado nesta pesquisa que meça a
  magnitude em ações individuais — tratar como hipótese (Seção 3), não como
  efeito estabelecido.

- **Gap de abertura.**
  Fenômeno real e mencionado por praticantes B3 (ex.: PETR4/VALE3 como
  "terreno fértil" por liquidez), mas os números de probabilidade de
  fechamento de gap encontrados (ex.: "~70% fecham", "gaps <1% fecham 78,5%
  das vezes") vêm de fontes genéricas sem metodologia B3-specific auditável
  — **[PRÁTICA/OPINIÃO de baixa confiabilidade numérica]**. Não usar esses
  números no produto sem revalidação com dado real B3.

- **After-market B3.** Existe, mas não foi encontrada nesta pesquisa
  nenhuma fonte quantitativa sobre liquidez/spread comparados ao pregão
  regular — conhecimento geral de mercado (liquidez sensivelmente menor),
  não uma evidência citável. Se o produto usar dado de after-market para
  algum setup, tratar como lacuna de pesquisa a preencher, não como
  assumido.

---

## 6. Metodologia de validação

**Walk-forward analysis** — padrão-ouro citado na literatura desde Pardo
(1992), *Design, Testing and Optimization of Trading Systems*. Mecânica:
otimiza em uma janela in-sample, testa "cego" na janela seguinte
out-of-sample, desliza a janela e repete. Serve como checagem de robustez
contra overfitting de parâmetro — não prova que a estratégia é boa, prova
que ela não depende de ter visto o futuro durante o ajuste. **[QUANT/
metodológico, consenso amplo]**.

**Deflated Sharpe Ratio (DSR)** — Bailey & López de Prado (2014), *The
Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting
and Non-Normality* (SSRN 2460551). Corrige o Sharpe observado por: (a)
número de variantes/testes tentados antes de escolher a "vencedora", (b)
não-normalidade dos retornos (assimetria, caudas gordas), (c) tamanho da
amostra. O ponto central para este produto: **quando muitas variações são
testadas (13 setups × múltiplos filtros × múltiplos parâmetros), o melhor
resultado observado é inflado só pelo número de tentativas, mesmo que todas
as variantes fossem puro ruído** — é exatamente o risco de testar as
hipóteses da Seção 3 uma a uma sem registrar quantas foram tentadas.
**[QUANT, paper fundacional da área]**.

**Aplicação prática recomendada para o roadmap de teste:**
1. Registrar antecipadamente (antes de rodar) a lista de hipóteses a testar
   (a Seção 3 deste documento já serve como esse registro) — isso define N
   para a correção de seleção múltipla.
2. Rodar cada hipótese em walk-forward, não em otimização in-sample única.
3. Aplicar DSR sobre o melhor resultado antes de declarar qualquer filtro
   "vencedor" — um Sharpe aparentemente bom entre 10+ variantes testadas
   pode não sobreviver à deflação.
4. Nenhum resultado de backtest deste processo deve ser comunicado ao
   usuário final como promessa de rentabilidade (reforça princípio 6 e 8 do
   CLAUDE.md do projeto).

---

## 7. Contexto não-acionável

Achados relevantes para entendimento, mas que não viram uma hipótese de
backtest específica:

- **Eficiência de forma fraca do Ibovespa (Chen & Metghalchi, 1996–2011)**
  é um resultado de mercado agregado — não indica *qual* setup específico
  falha ou funciona, só eleva o ônus da prova geral. Não é testável
  diretamente; é um prior que deveria calibrar expectativa de magnitude de
  qualquer edge encontrado.
- **A analogia "5 pessoas repetindo a mesma fonte" sobre confluência** é
  explicativa, não operacionalizável por si — a operacionalização já está
  na hipótese de re-scoring do Radar (Seção 3, último item).
- **Teoria comportamental de overreaction como explicação da reversão de
  curto prazo** (Lehmann/Jegadeesh) — explica o *porquê*, mas o *teste* já
  está capturado como hipótese de reversão em si; a teoria não adiciona um
  filtro novo a testar.
- **"Squeeze com 40% de acerto pode ser lucrativo se ganho médio é 3x a
  perda média"** — é reafirmação do princípio expectância > taxa de acerto
  (já coberto na Seção 2/6), não uma hipótese nova.
- **Estatística "OR estreito precede dia de tendência 68% das vezes"** —
  número de fonte única (blog), sem desagregação de metodologia nem relação
  com B3; baixo o suficiente em confiabilidade para não virar hipótese até
  que uma fonte melhor apareça.
- **After-market B3 tem liquidez menor** — conhecimento geral de mercado
  sem fonte quantitativa encontrada; relevante como cautela operacional, não
  como hipótese de backtest.
- **Debate acadêmico sobre se sucesso de timing por SMA é estatisticamente
  "real" mesmo em mercado eficiente** (autocorrelação, clustering de
  volatilidade como explicação alternativa) — nuance importante para não
  superinterpretar um resultado positivo de filtro de regime, mas não é, em
  si, uma hipótese de teste adicional.

---

## 8. Fontes

| Fonte | O que sustenta |
|---|---|
| Shukla, "Multicollinearity of Technical Indicators" (MQL5/forextsd) | Evidência de VIF alto entre indicadores técnicos populares (Seção 1) |
| MDPI 2022, "A Correlation-Embedded Attention Module to Mitigate Multicollinearity" | Confirmação acadêmica recente do problema de multicolinearidade em indicadores (Seção 1) |
| SMC Tutors (Medium); InsiderFinance; MQL5 Traders' Blog (ago/2026) | Formulação de prática/opinião sobre ilusão de confirmação em confluência (Seção 1) |
| Lehmann (1990) | Reversão semanal de curto prazo, ~1,5%/semana bruto (Seção 2) |
| Jegadeesh (1990); jegadeesh-titman93.pdf | Reversão mensal de curto prazo, ~2%/mês 1934–1987 (Seção 2) |
| Caginalp & Laurent (1998); estudo S&P500 1992–96; estudo OMXS30 sueco 2007–2015; estudo mercado chinês | Evidência mista/inconsistente sobre padrões de candlestick (Seção 2) |
| Moskowitz, Ooi & Pedersen (2012), "Time Series Momentum" (SSRN 2089463); AQR "A Century of Evidence on Trend-Following Investing" | Base acadêmica de momentum/trend-following (Seção 2, Seção 3 filtro de regime, Seção 4 Donchian) |
| Chen & Metghalchi, "Weak-Form Market Efficiency: Evidence from the Brazilian Stock Market" (CCSE, *Int'l J. of Economics and Finance*) | Evidência direta sobre Bovespa 1996–2011: regras técnicas não batem buy-and-hold (Seção 2, Seção 7) |
| Pellin, A. (2022), "Análise Técnica no mercado financeiro: a eficácia do *setup* 9.1 de Larry Williams como estratégia de investimentos", XLVI EnANPAD (ANPAD, PDF completo lido) | Único estudo quantitativo B3-specific encontrado sobre um dos 13 setups do Boris+ especificamente; números e limitações metodológicas (custos excluídos, N pequeno, soma aritmética não composta) documentados na íntegra (Seção 2) |
| QuantifiedStrategies.com, "RSI 2 Strategy" e derivados | Backtests de praticante sobre RSI-2/IFR2, sem peer review (Seção 2) |
| Faber (2007), "A Quantitative Approach to Tactical Asset Allocation" (trendfollowing.com/whitepaper) | Evidência de filtro de regime via SMA de 10 meses (Seção 3) |
| QuantBrasil, "Backtest da Estratégia de IFR2 Utilizando Médias Móveis Como Filtro" | Resultado quantitativo específico: filtro de tendência não melhorou IFR2 em LREN3 2015–2020 (Seção 3, achado central) |
| Concretum Group, "Position Sizing in Trend-Following" | Comparação de volatility targeting/parity/pyramiding em trend-following (Seção 3) |
| Blogs de corretora/educador B3 (moneystart, borainvestir B3, Clear) | Heurísticas de liquidez mínima para day trade (Seção 3, Seção 5) |
| B3 (b3.com.br), Nelogica, blogs de corretora sobre leilão/circuit breaker | Fatos operacionais: mecânica de leilão de abertura/fechamento e circuit breaker em 3 níveis (Seção 5) |
| B3, calendário de vencimento de opções/futuros | Datas de vencimento mensal/semanal (Seção 5) |
| InfoMoney, entrevista com Maria Silveira | Prática profissional de leitura de abertura via VWAP+liquidez+gaps (Seção 4) |
| Bailey & López de Prado (2014), "The Deflated Sharpe Ratio" (SSRN 2460551) | Metodologia de correção por seleção múltipla e overfitting de backtest (Seção 6) |
| Pardo (1992), *Design, Testing and Optimization of Trading Systems*; Wikipedia "Walk forward optimization" | Metodologia de walk-forward como padrão de validação (Seção 6) |
| Springer, "Examination of the profitability of technical analysis based on moving average strategies in BRICS" | Citado mas não recuperado por completo (paywall) — sinalizado como fonte a perseguir, não confirmada (Seção 4) |
| Springer, "Evaluation of pairs-trading strategy at the Brazilian financial market" | Evidência específica de B3 para pairs trading como família ausente (Seção 4) |

---

**Limitações desta pesquisa:** buscas via WebSearch/WebFetch, sem acesso a
bases acadêmicas pagas (SSRN/ScienceDirect/Springer foram acessados só onde
havia versão aberta ou abstract público). Vários números citados por blogs
de trading (não acadêmicos) não puderam ser verificados quanto a metodologia
— foram rotulados como [PRÁTICA] ou [OPINIÃO] e sinalizados como não
confiáveis para uso direto no produto sem replicação própria.
