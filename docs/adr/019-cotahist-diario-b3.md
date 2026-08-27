# ADR-019: Acervo diário oficial COTAHIST da B3

**Status:** Accepted  
**Date:** 2026-08-25  
**Deciders:** Produto/engenharia Boris+

## Contexto

A página pública de cotações históricas da B3 oferece uma série diária do ano
corrente. A página referencia o arquivo `COTAHIST_DDDMMAAAA.ZIP`, que contém um
TXT de posições fixas com registros de header (`00`), cotações (`01`) e
trailer (`99`). O app já possui provedores de spot/intraday e cache de candles;
esse acervo precisa ser uma fonte histórica rastreável, sem substituir
silenciosamente os provedores de cotação nem depender de uma chamada por ticker.

## Decisão

Implementar `server/app/b3_historical.py` com:

- URL direta derivada da data: `https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_DDDMMAAAA.ZIP`;
- download HTTP com limite de tamanho, validação de ZIP, exatamente um TXT e
  decodificação Latin-1;
- validação de header/trailer, tamanho dos registros e coincidência da data;
- persistência SQLite em `b3_daily_imports` (status, horário, arquivo, SHA-256,
  quantidade e erro) e `b3_daily_quotes` (linhas normalizadas);
- reexecução idempotente por data: arquivo já importado não é baixado novamente;
  se a B3 publicar uma correção depois, a data pode ser reimportada atomically;
- job no scheduler existente, depois do horário configurável
  `B3_COTAHIST_DAILY_HHMM` (default `20:30` BRT), com retry espaçado e sem
  depender do kill-switch de execução de ordens;
- CLI para operação manual e rotas admin protegidas por
  `fontes_dados.configurar` para status, amostra e reimportação.

## Alternativas rejeitadas

### Consultar o HTML todos os dias e simular o fluxo do navegador

Rejeitado: a página precisa apenas para descoberta/uso humano; o arquivo diário
é um endereço estável e a simulação do popup/captcha adicionaria fragilidade.

### Usar Yahoo/brapi para reconstruir o arquivo

Rejeitado: isso perderia a proveniência oficial do COTAHIST e poderia misturar
prints ajustados, atrasados ou incompletos com o histórico da B3.

### Inserir o conteúdo diretamente no `candle_cache`

Rejeitado: o cache atual é uma série por ticker/provedor e tem regras próprias
de delta/fallback. O COTAHIST é um acervo de arquivo, com todas as linhas do
dia e hash da fonte; consumidores podem adotá-lo explicitamente depois.

## Consequências

- A ingestão diária exige apenas uma requisição e sobrevive a redeploy no mesmo
  volume SQLite.
- 404 é registrado como `not_available`, sem fabricar um dia de pregão e sem
  marcar o dado como atual.
- A tabela preserva o universo completo de linhas `01`; filtros por mercado e
  ativo ficam explícitos para os consumidores.
- A disponibilidade da URL/arquivo da B3 continua sendo uma dependência externa
  sem SLA; status e hash tornam a falha observável.

