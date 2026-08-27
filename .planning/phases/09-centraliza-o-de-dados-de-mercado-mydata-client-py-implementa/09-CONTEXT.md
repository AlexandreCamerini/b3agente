# Phase 9: Centralização de dados de mercado (mydata_client.py) - Context

**Gathered:** 2026-08-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Implementar `mydata_client.py`, um cliente pro hub de dados `mydata.acamerini.app`
(`~/dev/cvm-financas`), e migrar duas fatias de dado de mercado que hoje o
Boris mantém em pipeline próprio: COTAHIST diário (`b3_historical.py`/ADR-019)
e Opções/IV (`options_provider_yahoo.py`). Redefine o papel de brapi (fica
exclusiva de cotação spot ao vivo) e não toca em Yahoo intraday (ADR-001
intocada — limite estrutural do COTAHIST, que só publica após o fechamento
do pregão).

</domain>

<decisions>
## Implementation Decisions

### Camada de integração
- **D-01:** `mydata_client.py` implementa a mesma interface `CandleProvider`
  que `BrapiProvider`/`YahooProvider` já implementam em `candle_provider.py`
  — `MydataProvider`, roteado pela fatia diária. Reusa o cache L2 existente
  (`candle_cache.py`) e todos os call sites atuais (setups, indicadores,
  agente) sem mudar nada neles.
- **D-02:** Opções seguem o mesmo padrão — `MydataOptionsProvider` atrás da
  mesma interface que `options_provider_yahoo.py` já expõe hoje
  (`providerStatus`). `options_api.py` continua chamando o mesmo contrato;
  ADR-004 não precisa ser reaberta, só a implementação por trás muda.

### Degradação quando mydata cai
- **D-03:** Se `GET /v1/cotacoes/{ticker}` falhar no refresh diário, o
  `candle_provider` cai pra próximo da cadeia (brapi, depois Yahoo) — mesmo
  padrão de fallback que já existe entre brapi→Yahoo hoje. O candle daquele
  dia vem de outra fonte, registrado com o `src` de proveniência
  (`candle_cache.py` já grava isso por registro) — prioriza disponibilidade
  sobre pureza de proveniência única.
- **D-04:** Opções NÃO seguem o mesmo padrão de fallback — se o endpoint de
  opções do mydata falhar, vai direto pra `providerStatus="degraded"` (ADR-004
  já bloqueia compra e mostra aviso nesse estado), sem tentar Yahoo como
  fallback. Motivo: Yahoo (401/403/429 frequentes) é exatamente a fonte
  instável que esta migração elimina — reintroduzi-la como fallback ativo
  anularia o ganho. `options_provider_yahoo.py` fica como código histórico,
  não caminho ativo.

### Folded Todos
- **Medir rate-limit real do mydata antes de trocar fontes em produção**
  (`.planning/todos/pending/medir-rate-limit-mydata.md`) — vira critério de
  aceite formal desta fase: antes de desligar Yahoo/brapi nas fatias
  migradas em produção, medir o volume real de chamadas (universo de
  tickers, cadência do refresh diário, chamadas de opções por ciclo) contra
  o limite da chave (60/min·2.000/dia), e confirmar se `provento_b3` já teve
  a primeira carga completa do lado do cvm-financas (se for usar essa
  classe também — hoje fora do escopo das duas fatias migradas).

### Claude's Discretion
- Nome exato do env var de credencial (`MYDATA_URL`/`MYDATA_TOKEN`, seguindo
  o padrão `BRAPI_TOKEN`/`BOLSAI_API_KEY` já usado no repo — provider-name
  prefix, não `B3_*`).
- Se o `MydataBudget` (rastreio de rate-limit, mesmo padrão memória→DB→env
  de `brapi_budget.py`) entra nesta fase junto com a implementação ou fica
  pra depois de medir o número real — decidir durante o planejamento com
  base no resultado do critério de aceite acima.
- Mecânica exata do job de refresh diário (batch 1×/dia após o fechamento
  vs. pass-through com TTL) — não discutido explicitamente; planejador
  decide com base no padrão já estabelecido em ADR-019/`b3_historical.py`
  (scheduler existente, sem cron externo).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Decisão e evidência desta migração
- `.planning/notes/boris-pp-centralizacao-dados-mydata.md` — decisão completa
  com evidência (arquivo:linha) de por que COTAHIST/Opções migram e
  Indicadores/Setups/Calendário/Job diário não
- `.planning/notes/mapa-realidade-mcp-desatualizado.md` — por que o mapa de
  realidade original comparou contra o repositório errado
- `.planning/todos/pending/medir-rate-limit-mydata.md` — critério de aceite
  de rate-limit (dobrado nesta fase, ver Decisions acima)

### ADRs do Boris afetadas (nenhuma reaberta — supersessão parcial vem numa ADR-020 futura)
- `docs/adr/001-fonte-de-dados-intraday.md` — Yahoo intraday 15min, INTOCADA
- `docs/adr/004-fonte-de-opcoes-na-v2.md` — contrato `providerStatus`, não
  reaberta, só a implementação por trás troca
- `docs/adr/008-fonte-de-cotacoes-selecionavel.md` — brapi master
  diário/spot, escopo reduzido a spot-only nesta fase
- `docs/adr/019-cotahist-diario-b3.md` — `b3_historical.py`, aposentada por
  esta fase na fatia diária

### Contrato do lado mydata (cvm-financas, fora deste repo)
- `~/dev/cvm-financas/docs/contrato-consumidor.md` — chave de produção
  `f00b4554`, escopo `negociacao_b3`+`provento_b3`, rate limit 60/min·2.000/dia
- `~/dev/cvm-financas/docs/deploy-railway.md` — confirma domínio
  `mydata.acamerini.app`
- `~/dev/cvm-financas/app/motor/nucleos.py:182-223` — `bs_iv`, solver de IV
  testado (36 testes verdes)
- `~/dev/cvm-financas/app/api/main.py:596-770` — `GET /v1/cotacoes/{ticker}`,
  `GET /v1/opcoes/{ticker}`, `GET /v1/opcoes/{ticker}/vencimentos`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `server/app/candle_provider.py` — interface `CandleProvider`,
  `BrapiProvider`/`YahooProvider` já implementam o contrato que
  `MydataProvider` precisa seguir; `get_history()` é o router único.
- `server/app/candle_cache.py` — cache L2 persistente em SQLite, já grava
  `src` (proveniência) por registro — reusar pra registrar candles vindos do
  mydata sem mudar schema.
- `server/app/brapi_budget.py` — padrão memória→DB→env pra orçamento de
  requisições, com soft/hard stop; modelo direto pro eventual `MydataBudget`.
- `server/app/options_provider_yahoo.py` — contrato `providerStatus` que
  `MydataOptionsProvider` precisa preencher; `options_api.py` já sabe
  bloquear compra quando degradado (ADR-004).
- `server/app/fundamentals.py` — padrão análogo já em produção: fonte
  primária (BolsAI) + fallback (brapi) + cache TTL em SQLite `kv`. Bom
  precedente de como estruturar client HTTP + auth + cache pra uma API
  externa nova.

### Established Patterns
- Nunca inventar dado quando a fonte falha — `HTTPException(502, ...)` em
  vez de simular preço (`main.py:1509`), princípio 4 do CLAUDE.md do repo,
  se aplica igual a qualquer falha de mydata.
- Secrets só em env do Railway, nunca no bundle — credencial mydata segue
  `BRAPI_TOKEN`/`BOLSAI_API_KEY` (provider-name, não `B3_*`).
- Scheduler interno sem cron externo (`agent.py:874` `scheduler_loop`) — é
  onde o refresh diário do mydata deve pendurar, mesmo padrão de
  `B3_COTAHIST_DAILY_HHMM` que ADR-019 já usa.

### Integration Points
- `server/app/candle_provider.py::get_history()` — ponto de entrada único
  pra registrar `MydataProvider` na cadeia diária.
- `server/app/options_api.py` — consumidor do contrato `providerStatus`,
  ponto de troca pra `MydataOptionsProvider`.
- `server/app/agent.py::scheduler_loop` — onde o job de refresh diário
  pendura, se for batch (ver Claude's Discretion acima).

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência específica além da decisão já documentada na nota de
centralização — a discussão desta sessão focou em como plugar o cliente novo
na arquitetura existente (interface, degradação), não em detalhes visuais ou
de produto.

</specifics>

<deferred>
## Deferred Ideas

Nenhuma — discussão ficou dentro do escopo da fase.

</deferred>

---

*Phase: 9-Centralização de dados de mercado (mydata_client.py)*
*Context gathered: 2026-08-27*
