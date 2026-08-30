# Boris+ Opções — Modelos do MVP

## Escopo implementado

O módulo de opções implementa uma primeira fundação quantitativa e educacional:

- cadeia de opções via Yahoo Finance, quando disponível
- vencimentos
- calls e puts
- strike, bid, ask, último preço, volume, open interest e IV
- volatilidade histórica de 21 e 63 pregões
- Black-Scholes-Merton educacional
- gregos: delta, gamma, theta, vega e rho
- valor intrínseco e valor extrínseco
- breakeven
- score de liquidez
- score educacional

## Modelos considerados

### Black-Scholes-Merton

Usado como referência para preço teórico e gregos. Limitação: não resolve perfeitamente opções americanas, exercício antecipado, dividendos e eventos corporativos. No app, é uma aproximação educacional.

### Volatilidade histórica versus implícita

O backend calcula HV 21 e HV 63 com retornos logarítmicos anualizados. A IV vem da cadeia de opções do provedor quando disponível.

### Liquidez

O score de liquidez considera volume, open interest e spread bid/ask. Contratos sem mercado, sem OI ou com spread aberto são penalizados.

### Score educacional

Composição atual:

- tendência do ativo objeto: 25%
- liquidez: 20%
- volatilidade: 20%
- gregos: 15%
- prazo: 10%
- probabilidade ITM: 10%

O score não é sinal operacional.

## Próximas evoluções

- provider especializado para B3
- IV Rank e IV Percentile com série histórica de IV
- árvore binomial para exercício antecipado
- payoff visual
- simulação de compra de call/put
- travas e estratégias estruturadas
