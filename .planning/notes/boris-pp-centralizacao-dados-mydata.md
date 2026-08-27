---
title: Boris++ — decisão de centralização de dados via mydata (cvm-financas)
date: 2026-08-27
context: Sessão /gsd-explore sobre deduplicação Boris×mydata. Corrige e substitui
  a tabela de posse do prompt original, que comparou contra o repositório errado.
---

# Boris++ — centralização de dados via mydata (cvm-financas)

## Achado que motivou a revisão

O levantamento original (`~/dev/MCP/docs/boris-pp-00-mapa-de-realidade.md`)
comparou o Boris contra `~/dev/MCP/servers/mydata/` — a camada de ferramentas
MCP conversacionais (DSL, `create_setup`, 11 tools). Mas existe um **segundo
repositório também chamado "mydata"**: `~/dev/cvm-financas`, que é o hub de
dados real deployado em `mydata.acamerini.app` (confirmado em
`~/dev/cvm-financas/docs/deploy-railway.md`). O `fonte.py` (301 l.) que o mapa
original citou como "COTAHIST do mydata" não ingere nada — é só um cliente
HTTP fino que chama esse hub. A duplicação real de COTAHIST e Opções está no
hub, não no MCP, e o hub está mais maduro do que o Boris nessas duas frentes.

`~/dev/cvm-financas/docs/contrato-consumidor.md` já lista **BolsIA
(`b3-agente`)** — este repositório — como consumidor em produção (chave
`f00b4554`, emitida 2026-08-26, escopo `negociacao_b3`+`provento_b3`), com uma
pendência explícita já registrada do lado do hub: "implementar
`mydata_client.py` e desligar Yahoo/brapi/COTAHIST paralelo — a migração é do
lado de lá [b3-agente]". Não é proposta hipotética — é contrato já negociado,
com uma ponta esperando a outra.

## Tabela de decisão revisada

| Frente | Decisão original do prompt | Decisão revisada | Por quê |
|---|---|---|---|
| COTAHIST diário | Boris (ADR-019), descartar mydata | **Migra para `mydata_client.py`**, aposenta `b3_historical.py`/ADR-019 | cvm-financas ingere o mesmo arquivo oficial desde 31/07 (Postgres produção, 4,69 GB), servindo via `GET /v1/cotacoes/{ticker}`. ADR-019 foi implementada 25/08 — um dia antes do contrato ser ampliado. Mesma fonte oficial, duas capturas; a mais madura vence. |
| Opções / IV | Boris (003/4/5), exceto "solver IV + cross-val OBM" | **Migra para `mydata_client.py`**, substitui `options_provider_yahoo.py` | "OBM" não existe em lugar nenhum (busca zero em ambos os repos). O que existe é `bs_iv` (bisseção, `~/dev/cvm-financas/app/motor/nucleos.py:182-223`), testado (36 testes verdes), ligado a `GET /v1/opcoes/{ticker}` com dado real do COTAHIST oficial — objetivamente melhor que Yahoo não-oficial (ADR-004 já registra 401/403/429 frequentes). Baixo risco: ADR-004 já trata provider como trocável via `providerStatus`, não precisa reabrir a ADR. |
| Cotação spot ao vivo (pregão aberto) | Não estava separado do "diário/spot" | **brapi, exclusiva** — ADR-008 com escopo reduzido | COTAHIST só é publicado depois do fechamento do pregão (job do cvm-financas roda às 23:59/06:00 UTC). mydata **não pode nunca** servir preço vivo durante o pregão — é limitação estrutural da fonte, não lacuna de implementação. brapi perde a fatia de delta diário mas continua necessária pro spot. |
| Intraday 15min | Não estava em pauta | **Yahoo, intocado** — ADR-001 sem mudança | cvm-financas decidiu explicitamente (commit `aaa93e8`, 26/08 21:15, Alex) manter intraday fora de escopo: "o diário atende: IV, gregas e HV são calculados sobre fechamento... reabrir só com caso real de timing intradiário". A pendência #124 do contrato ("desligar Yahoo... paralelo") só pode valer pra fatia diário/spot — desligar Yahoo por completo quebraria ADR-001 (travada). |
| Indicadores técnicos | Boris, diff numérico obrigatório | Boris — **decidido nesta sessão**: tolerância (~1e-4 relativo) + equivalência de sinal (mesma vela dispara o mesmo setup), universo dos 15 anos/74 tickers do ADR-016, reusando `scripts/backtest_sinal.py` | cvm-financas não tem nenhuma camada de indicador (busca por sma/rsi/atr/adx/macd/etc. não retorna hit). Único cálculo derivado é HV21/HV63 e gregas BS. Divergência de sinal vira caso de teste nomeado, nunca é apagada. |
| Motor de setups | Boris (016/017), migra DSL do mydata como formato, nunca o motor | Boris — **decidido nesta sessão**: DSL do MCP (`~/dev/MCP/servers/mydata/setups.py`) vira formato de autoria só pra setup **candidato novo** (via compilador NL→DSL), sempre passa por `scripts/backtest_sinal.py` + ponderação ADR-017 antes de aparecer no Radar. Os 17 detectores já medidos (ADR-016/017) ficam como Python, intocados. | Reescrever os 17 setups pra DSL reintroduziria o mesmo risco de divergência silenciosa que motivou a decisão de Indicadores acima — o backtest histórico mediu o código antigo, não uma tradução. `contrato-consumidor.md:204-206` confirma: "o que continua do lado do BolsIA: limiares de liquidez, score educacional e backtest de regras de trailing — são juízo de produto, não fato de mercado." |
| Calendário B3 | Boris (`pregao.py`), descartar `FERIADOS_B3` | Sem mudança — Boris | cvm-financas não tem calendário/feriados próprio; irrelevante à decisão. |
| Job diário | Boris (`agent.py`), descartar `job_diario.py` do MCP | Sem mudança — Boris | Job do cvm-financas é interno (alimenta o próprio hub), não concorre com o `scheduler_loop` do Boris. Comparação original (contra `~/dev/MCP`) continua válida. |

## Ressalvas — não tratar como resolvido

- **Rate limit não medido.** A chave de produção do BolsIA é 60/min·2.000/dia.
  O padrão natural de integração (COTAHIST é EOD → refresh em lote 1×/dia,
  cache local, mesmo padrão que ADR-019 já usava) sugere folga generosa, mas
  isso é inferência de arquitetura, não medição. Vira critério de aceite da
  fase de implementação — ver todo "Medir rate-limit real do mydata antes de
  trocar em produção".
- **`provento_b3` ainda não teve a primeira carga de produção completa**
  (`docs/contrato-consumidor.md:151` do cvm-financas, verificado 2026-08-27).
  Schema e rota testados com 84 eventos de 4 companhias, mas não é dado real
  completo ainda. Fora do escopo desta decisão (proventos não estavam nas seis
  frentes originais), mas relevante se aparecer depois.
- **Hub multi-app tem exatamente UM consumidor hoje.** A tabela
  `Consumidores integrados` do contrato só lista BolsIA (três gerações de
  chave). O hub é arquitetado pra multi-tenant (`docs/contrato-consumidor.md`:
  "cada consumidor tem repositório e ciclo de vida independente... a direção
  da dependência é assimétrica"), mas na prática ainda não tem um segundo
  cliente. Responde a pergunta em aberto do prompt original — o hub multi-app
  já existe como projeto separado e não precisa nascer de "extrair daqui" —
  mas com essa ressalva, não como premissa já provada em escala.
- **`mydata_client.py` não existe em nenhum dos dois repositórios** (nem
  arquivo, nem branch, nem em `git log --all`). Terreno limpo — quem
  implementa é o Boris.

## Próximo passo formal

Esta nota é insumo pra uma ADR-020 (ou renumeração equivalente) que documente
formalmente a supersessão parcial de ADR-001 (sem mudança), ADR-004 (provider
trocado, ADR não reaberta), ADR-008 (escopo reduzido a spot) e ADR-019
(aposentada). Histórico não se reescreve — as ADRs antigas ficam como estão,
uma nova ADR referencia e supera o que se aplica.
