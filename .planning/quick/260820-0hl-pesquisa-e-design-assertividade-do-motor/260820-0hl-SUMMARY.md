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

## Addendum (2026-08-20, pós-publicação) — classificação de regime

A pedido do Alex, aprofundei a análise sobre a classificação de regime
(`regime.py:classificar()`, tese do ADR-009) com mais uma consulta read-only
em produção. Achado: a segmentação por regime tem **N=0 hoje, não N baixo**
— `regime` só passou a ser gravado em 2026-08-11 (qa/44), os 269 registros
anteriores nunca tiveram o campo, e nenhum dos 123 registros com `regime`
ainda cruzou os 10 pregões (~14 dias corridos) para resolver. Primeira leva
resolve a partir de ~2026-08-25. Também corrigi uma afirmação da pesquisa
original: `confianca` não é constante em produção (era 100% `moderada` só em
dev) — em prod tem `moderada` 326, `baixa` 39, `alta` 4, `None` 23.
Atualizado em `docs/adr/015-*.md` (seção "Achado adicional — classificação
de regime").

## Próximo passo

Documento pronto para leitura/aprovação do Alex. Nenhuma implementação deve
começar antes de decisão explícita sobre a Alternativa 1 (e 2, se aprovada).
