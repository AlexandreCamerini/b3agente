# Sumário — Refatoração para Opções

## O que foi implementado

Foi criada a base do módulo **B3 Agente Opções** sem reescrever a carteira atual de ações.

Entregas:

- backend de opções com provider Yahoo Finance
- endpoints para vencimentos, cadeia e análise educacional
- motor quantitativo stdlib-only
- cálculo de Black-Scholes, gregos, volatilidade histórica, breakeven, valor intrínseco/extrínseco
- score de liquidez
- score educacional
- nova aba `Opções` no app React
- extensão da interface de persistência web/iPhone
- testes automatizados do motor quantitativo
- documentação específica do módulo

## Decisão arquitetural

A opção foi por um módulo paralelo ao fluxo de ações. Isso reduz risco de regressão e prepara o produto para trocar o provider Yahoo por uma fonte mais robusta para B3 no futuro.

## Limitações conhecidas

- O Yahoo Finance pode não retornar cadeia de opções para ativos B3.
- A implementação atual não opera opções na carteira; é análise/estudo.
- Não há payoff visual ainda.
- Não há venda coberta, travas ou estratégias estruturadas.
- IV Rank/Percentile dependem de histórico de IV, ainda não implementado.

## Próximo passo recomendado

Validar o provider com ativos americanos e B3. Depois decidir se o MVP2 deve priorizar:

1. simulação de compra de call/put com payoff; ou
2. integração com fonte especializada para opções B3.

## Atualização — fix iOS LLM URL reaplicado na versão correta
- Base: ZIP enviado pelo usuário `b3-agente-mobile-technical-models-fix-pytest.zip`.
- Correção: normalização automática de API base para iOS/WebView.
- Resultado: domínio Railway sem protocolo passa a `https://`; IP local continua `http://`.
- Validação: backend `45 passed`; cliente HTTP/iOS `5 passed`.
