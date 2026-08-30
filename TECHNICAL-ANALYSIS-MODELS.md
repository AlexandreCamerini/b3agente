# Boris+ — Modelos de análise técnica para LLM

A aplicação agora separa cálculo de interpretação:

1. Backend baixa dados no yfinance.
2. Backend limpa candles e calcula indicadores.
3. Backend compacta até 120 candles diários para a LLM.
4. LLM interpreta o pacote conforme o modelo escolhido.
5. UI mobile mostra a leitura educacional.

## Modelos disponíveis

- Completo
- Tendência
- Price Action
- Momentum
- Volume
- Volatilidade
- Suporte e resistência
- Swing trade educacional
- Opções

## Dados enviados à LLM

- ticker e fonte
- cotação atual quando disponível
- até 120 candles OHLCV diários
- variação 21, 63 e 252 pregões
- EMA9, EMA21, SMA20, SMA50
- RSI14, MACD, estocástico
- volume atual, volume médio 21, volume relativo, OBV
- ATR14, ATR percentual, volatilidade histórica 21/63
- suportes e resistências recentes
- referência educacional de stop/alvo por níveis e ATR
- status de opções no yfinance quando o modelo for `opcoes` ou `completo`

## Guardrail

A LLM não deve emitir ordem operacional. O campo visual é “Plano educacional”, não recomendação real. Valores aceitos:

- Estudar alta
- Estudar baixa
- Monitorar
- Aguardar
- Não operar
- Reduzir risco

Nada disso representa recomendação de investimento.
