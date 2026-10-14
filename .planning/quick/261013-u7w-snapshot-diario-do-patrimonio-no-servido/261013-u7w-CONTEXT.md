# Quick Task 261013-u7w: Snapshot diário do patrimônio no servidor — Context

**Gathered:** 2026-10-13
**Status:** Ready for planning
**Origem:** follow-up da 261013-svo (STATE.md). Hoje `equitySnapshots` só ganha ponto quando o app abre (web: POST /api/snapshot; iOS: só no aparelho). Objetivo: o servidor grava o ponto de fechamento de cada conta em todo pregão, e web e iPhone passam a enxergar esses pontos.

<domain>
## Task Boundary
1. Job diário no servidor que grava o snapshot de fechamento de todas as contas em dia de pregão.
2. Função única de patrimônio no servidor, espelho de `portfolioMetrics` (finance.js:123), com fixture de paridade.
3. Regra de convivência app × servidor no mesmo dia (servidor e os dois stores).
4. iPhone (deviceStore) passa a adotar os pontos do servidor (união por data).
5. Correção: o app grava a data do snapshot em UTC (`new Date().toISOString().slice(0,10)`, App.jsx ~10458 e ~11114) — passa a usar a data BRT.
6. Visibilidade no portal admin (status do job).

FORA de escopo: upload dos pontos antigos que só existem no aparelho iOS para o servidor (follow-up); horário por cotação em /api/quotes; marcação histórica de opções; série intradiária.
</domain>

<decisions>
## Implementation Decisions (LOCKED — Alex, 2026-10-13)

### D1. Quando e com que cotação
- Job em `server/app/snapshot_diario.py` (novo), pendurado no `agent.scheduler_loop` (agent.py ~1182; jobs diários ~1256-1315) com `try` próprio, FORA do gate de pregão intraday. Roda em dia de pregão (`pregao.is_trading_day()`, calendário B3 com feriados) a partir de **17:05 BRT** (horário configurável por env, default 17:05), UMA vez por dia (dedupe por kv tipo `snapshotDiarioLastRun` + `db.marcar_job`, padrão radar_daily.py:68-94 — sobrevive a reinício).
- Cotação: UM lote único com os tickers distintos de todas as contas, via o getter exclusivo do agente (`candle_provider.get_quotes_exclusive`, brapi, sem misturar fonte), dentro da janela de orçamento da brapi (até 17:15, `brapi_budget`). Custo = tickers distintos/dia.
- Posições usadas = as do momento do job (são as do fechamento; o motor não executa ordem após 16:55).
- Kill-switch do agente: o job NÃO é bloqueado por ele (não executa ordem, só mede) — decisão do orquestrador, registrada no comentário.
- Iteração de contas: todas as contas com carteira no kv (varrer `u:%:cash`/`positions`, não `list_users` com limit 500); lotes curtos com `await asyncio.sleep(0)` entre contas (SQLite síncrono no event loop). Contas sem nenhuma posição: o planner decide se grava (curva plana real) — preferir gravar, é dado verdadeiro.

### D2. Sem cotação → não grava
- Se QUALQUER ativo aberto da conta (ação, ou opção que exija cotação pela regra de `valor_opcoes`) ficar sem cotação válida, a conta NÃO ganha ponto naquele dia; registrar no log do job (obslog + contagem no status). Nunca usar preço médio silencioso no ponto do servidor (princípio 4) — divergência deliberada do `markPrice` do front, documentada.
- Opções seguem a regra atual de `store.valor_opcoes` (store.py:632; pernas pelo prêmio de abertura quando não há cotação de contrato — é a regra vigente do patrimônio, já sinalizada na UI) — isso NÃO conta como "sem cotação" (mesmo comportamento do patrimônio exibido hoje).

### D3. Patrimônio no servidor = espelho do front
- Função pura nova `patrimonio_conta(...)` em `server/app/store.py` (ou módulo), espelho 1:1 de `portfolioMetrics` (caixa + reservado + posições a preço + opções via `valor_opcoes`), com fixture de paridade NOVA servidor ↔ front (padrão `server/tests/fixtures/patrimonio_opcoes_paridade.json`), testada dos dois lados.
- Snapshot gravado pelo `store.upsert_snapshot` (store.py:1543), reaproveitando regra de `base`, cap 400 e upsert por `data`. Campos NOVOS no registro: `origem` ("fechamento" | "app"), `fonte` (ex.: "brapi") e `hora` (BRT, HH:MM) — princípio 3. Registros antigos sem os campos continuam válidos (tratados como "app").

### D4. Convivência no mesmo dia (servidor e os dois stores)
- Um ponto `origem:"fechamento"` NÃO é sobrescrito por um ponto `origem:"app"` da mesma `data` (o app grava valor intraday ao abrir). O inverso vale (fechamento sobrescreve app). Regra no `store.upsert_snapshot` E no espelho do iOS (`upsertSnapshot`, persistence.js:82-104), com guardião de paridade.
- A exibição continua substituindo o ponto de HOJE pelo patrimônio ao vivo (finance.js:309-316) — sem mudança.

### D5. iPhone adota os pontos do servidor
- `deviceStore` passa a mesclar `equitySnapshots` do servidor (em `_adotarCarteiraDoServidor`/`getState`, persistence.js:709-744): UNIÃO por `data`; mesma data → vence `origem:"fechamento"`; datas só no aparelho permanecem; ordenação por data e cap 400 iguais ao servidor. Mesma regra num helper puro testado, compartilhado ou espelhado. `resetPortfolio` segue zerando os dois lados.
- `serverStore` (web) já lê do servidor; garantir que não reintroduz o ponto intraday por cima do fechamento (via D4).

### D6. Data em BRT no app
- O app passa a gravar `data` do snapshot em BRT (mesma convenção `America/Sao_Paulo` do helper `hojeBRT` em `web/src/evolucaoPosicao.js`), nos pontos onde hoje usa `toISOString().slice(0,10)` para snapshot/curva. Guardião.

### D7. Admin
- O job aparece em `agent.status_snapshot` (bloco jobs/janelas, agent.py ~1556-1618) com última execução, contas gravadas, contas puladas por falta de cotação e tickers sem cotação; e numa linha do portal admin (`web-admin/src/App.jsx` ~101-129).

### Claude's Discretion
- Nomes, estrutura do módulo, env do horário, formato do log. Guardiões: tudo que for alterado ganha substituta com nota `2026-10-13 (quick 261013-u7w)`; nada apagado. Paridade deviceStore ↔ serverStore obrigatória (test_fase3_paridade_stores_generica).
</decisions>

<specifics>
## Inventário (Explore, 2026-10-13) — pontos-chave
- scheduler_loop agent.py:1182 (startup main.py:5468-5490); jobs diários com `pregao.is_trading_day()` agent.py:1256-1315; heartbeat 1209-1218; kill_switch_on agent.py:192.
- pregao.py: FECHAMENTO (16,55), feriados(), is_trading_day (:106); guardião test_pregao_calendario.py.
- brapi_budget: janela 10:00-17:15 (:90-93), `reservar("spot")`; get_quotes_exclusive candle_provider.py:631 (falha → price None).
- upsert_snapshot store.py:1543-1583 (base, cap 400, upsert por data); valor_opcoes store.py:632; caixa_reservado :611; resolver_base_serie :1486; deviceStore upsertSnapshot persistence.js:82-104, putSnapshot :1036-1044 (só local), _adotarCarteiraDoServidor :709-721, getState :735-744, semeadura :1753-1770.
- App grava snapshot App.jsx ~10459-10473 (data UTC ~10458, ~11114). equityCurve finance.js:291/309-316.
- Guardiões ligados: test_retorno_acumulado_base (py e mjs), test_patrimonio_opcao_avulsa, test_persistence.py, test_conta_nova_nasce_limpa.py, test_capitalcurve_sem_base, test_benchmark_curva, test_fase3_paridade_stores_generica, test_conta_nova_ios_nasce_limpa, test_migracao_carteira_demo, test_numeros_fundamentados.
- SQLite thread-local + WAL (db.py:38-80); 1 réplica (Procfile); volume /data em produção (STAGING.md).
- App.jsx ~164k tokens: NUNCA ler inteiro. Sem dependências novas, sem worktree, sem publicar/push. Executor roda guardiões tocados + testes novos + pytest dos módulos tocados + `npx vite build`; suíte canônica e `cap copy ios` com o orquestrador.
</specifics>

<canonical_refs>
- ./CLAUDE.md (princípios 3, 4, 5; paridade dos stores; guardiões não se apagam)
- docs/adr/001, docs/adr/008 (fontes e orçamento brapi)
- .planning/quick/261013-svo-painel-de-evolucao-da-carteira/261013-svo-SUMMARY.md
</canonical_refs>
