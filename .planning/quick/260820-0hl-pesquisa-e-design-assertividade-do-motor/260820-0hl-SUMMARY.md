---
status: complete
---

# Quick Task 260820-0hl — Sumário

**Status:** complete
**Entregável:** [docs/adr/015-assertividade-do-motor-de-recomendacao.md](../../../docs/adr/015-assertividade-do-motor-de-recomendacao.md)

## O que foi feito

1. Pesquisador (`gsd-phase-researcher`) extraiu dados reais de
   `analysis_outcomes` no banco local de dev, mapeou o pipeline
   determinístico ponta a ponta (arquivo:linha), pesquisou literatura de risk
   management (triple-barrier / López de Prado, expectância / Van Tharp,
   deflated Sharpe / Bailey), e confirmou via WebFetch que o ToS da
   TradingView proíbe nominalmente o uso pretendido — resultado em
   `260820-0hl-RESEARCH.md`.
2. A pesquisa achou algo mais grave que a pergunta original: a *medição* de
   eficiência da IA está quebrada (âncora errada, `n` inflado por
   duplicação), e o erro é otimista — o painel reportaria edge forte onde não
   há edge. Confirmado com o usuário antes de fechar o ADR: rodei um
   diagnóstico read-only via `railway ssh` contra o banco de produção
   (aprovação explícita solicitada e concedida) — confirmou os mesmos dois
   bugs em 100% dos 159 registros resolvidos de produção, com volume bem
   maior que o dataset de dev (392 registros vs. 57).
3. Escrevi `docs/adr/015-assertividade-do-motor-de-recomendacao.md`
   diretamente (não via `gsd-executor`) para preservar a precisão numérica —
   diagnóstico com números de dev e produção, 3 alternativas com trade-off
   (consertar instrumentação / + backtest com walk-forward / TradingView —
   rejeitada), recomendação explícita, e nota de que nenhuma alternativa
   toca o Princípio 5 do CLAUDE.md.

## Verificação

- Todas as citações arquivo:linha do ADR foram conferidas por leitura direta
  do código (`main.py:1313-1327`, `store.py:621` vs `store.py:704-715`), não
  apenas herdadas do relatório do pesquisador.
- Números de produção vêm de consulta read-only real (`sqlite3 mode=ro`),
  aprovada pelo usuário, sem escrita/deploy — reproduzível com os scripts em
  `/private/tmp/claude-501/.../scratchpad/medicao_prod_outcomes*.py` (fora do
  repo, não versionados).
- Nenhum arquivo de código de produção (`server/`, `web/`) foi alterado.

## Limitações conhecidas

- O placar de produção deduplicado (41 stop / 21+4 alvo entre 66 planos)
  ainda usa a âncora errada (close, não gatilho) — corrigir isso em escala
  de produção (66+ planos × candle real) é trabalho de implementação, fora
  do escopo desta pesquisa. O ADR sinaliza isso explicitamente.
- `confluencia` nunca foi gravada em nenhum outcome (dev ou prod) — a
  segmentação por faixa de confluência pedida no prompt original não pôde
  ser feita; o ADR documenta isso como gap de instrumentação (B4), não como
  dado inexistente por erro de busca.

## Próximo passo

Documento pronto para leitura/aprovação do Alex. Nenhuma implementação deve
começar antes de decisão explícita sobre a Alternativa 1 (e 2, se aprovada).
