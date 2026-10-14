---
phase: quick-261013-u7w
plan: 01
status: complete
note: Leva 1 (backend, Tarefas 1 e 2) e Leva 2 (Tarefas 3 e 4: iPhone, App.jsx BRT, admin, guardioes) concluidas.
---

# Quick 261013-u7w — Snapshot diario do patrimonio no servidor

## Leva 1 (backend)

### Commits (so codigo)
- 3a0be1d5 `feat(quick-261013-u7w): patrimonio_conta espelho de portfolioMetrics e regra fechamento x app no upsert de snapshot` (Tarefa 1)
- 0c5c704d `feat(quick-261013-u7w): job snapshot_diario grava o fechamento do patrimonio de cada conta no scheduler` (Tarefa 2)

TDD: os testes e fixtures da Tarefa 1 foram escritos antes e falharam (20 pytest + 12 asserts .mjs de convivencia) antes da implementacao. O .mjs de paridade do patrimonio passa desde o inicio por desenho (o front ja existe; o lado novo e o py).

### Arquivos
- Novos: `server/app/snapshot_diario.py`, `server/tests/test_snapshot_diario.py` (J1-J25 + zeragem do `erro`), `server/tests/test_patrimonio_conta_paridade.py`, `server/tests/test_snapshot_convivencia.py`, `server/tests/fixtures/patrimonio_conta_paridade.json`, `server/tests/fixtures/snapshot_convivencia_casos.json`, `web/tests/test_patrimonio_conta_paridade.mjs`, `web/tests/test_snapshot_convivencia.mjs`.
- Alterados: `server/app/store.py`, `server/app/agent.py`, `web/src/persistence.js` (so `upsertSnapshot`), `server/tests/test_agent.py`.
- `main.py` e `web/src/App.jsx` intocados.

### Verifies (cada teste separado)
Tarefa 1: test_patrimonio_conta_paridade.py 10 ok; test_snapshot_convivencia.py 10 ok; test_persistence.py 30 ok; test_retorno_acumulado_base.py 21 ok; test_patrimonio_opcao_avulsa.py 12 ok; test_conta_nova_nasce_limpa.py 4 ok; .mjs: test_patrimonio_conta_paridade, test_snapshot_convivencia, test_retorno_acumulado_base, test_patrimonio_opcao_avulsa todos ok. Exit 0.

Tarefa 2: test_snapshot_diario.py 37 ok; test_agent.py 41 ok; test_put_lifecycle_scheduler 8 ok; test_put_bridge_scheduler 6 ok; test_signal_ledger_scheduler 10 ok; test_ordens_pendentes_scheduler 10 ok; test_fase3_operador 17 ok; test_qa46_fase2_wiring 4 ok; test_pregao_calendario 35 ok; test_brapi_budget 22 ok; test_snapshot_convivencia 10 ok; test_patrimonio_conta_paridade 10 ok.
- test_fase3_kill_switch_duracao.py: 24 ok no orquestrador. As 4 falhas anotadas inicialmente (`asyncio.run(_alertar_kill_switch)` devolvendo 0) vinham do sandbox do executor, nao do codigo; nao sao pre-existentes nem regressao. (Reproduzem so dentro do sandbox do executor.)
- Nao rodados por instrucao: suite canonica, `cap copy ios`, `vite build` (web/src nao tocado alem de persistence.js, helper privado; build e da leva 2).

### Guardioes
| Guardiao | Asserção atual | Substituta | Nota |
|---|---|---|---|
| test_agent.py `_JOBS_MARCADOS` | 4 jobs | + `snapshotDiario` (13 chaves) | ADITIVA 2026-10-13 (quick 261013-u7w) |
| test_agent.py `_FORMA_MARCADORES` | 4 marcadores | + `snapshotDiario` | idem |
| test_agent.py `set(st) == {...}` | sem `snapshotDiario` | + `"snapshotDiario"` | idem |
| test_retorno_acumulado_base.py/.mjs (regex de `upsertSnapshot` e da chamada do `putSnapshot`) | inalterado | verde sem edicao | conferido |
| test_persistence.py, test_patrimonio_opcao_avulsa, test_conta_nova_nasce_limpa, test_pregao_calendario | inalterado | verdes sem edicao | conferido |

Nenhuma asserção apagada.

### Desvios
- Nenhum desvio de regra. Escolhas de detalhe: `LAST_RUN["tickers"]` e uma contagem (int), `tickersSemCotacao` e lista (max 20); `perdido` so e true se nenhuma rodada ocorreu no dia E havia contas pendentes (sem contas, nada foi perdido); `fonte` do ponto e o `source` das cotacoes da conta, concatenado com "+" se houver mais de uma.

### W4 — verificacao no codigo (nao corrigido; task separada)
`agent.run_cycle_for` (`server/app/agent.py:848-873`) e `_run_cycle_inner` (`agent.py:875-1031`, ate `_agent_rows` em :1032) NAO tem portao de pregao: nenhuma ocorrencia de `in_market_hours`/`is_trading_day` nesse intervalo (as ocorrencias no arquivo sao :291 alerta de kill-switch, :369/:379 definicao, :1219 heartbeat, :1258 jobs diarios, :1308 gate do laço — o gate do laço so protege a passada agendada). Caminhos que chamam o ciclo fora do laço, sem portao de pregao: `_disparar_ciclo_imediato` (`server/app/main.py:5258`, so checa `kill_switch_on`, nao o horario) e `POST /api/agent/run-now` (`main.py:5406`). Logo, stop/alvo podem executar depois das 16:55. As rotas de opcao (buy/sell/lastreada/collar/fechar) tambem nao tem portao (conforme as Premissas do PLAN). Consequencia: o ponto de fechamento e o patrimonio "na `hora` da gravacao", nao garantidamente a carteira de 16:55.

### Interfaces que a leva 2 consome
- **Registro de snapshot** (kv `equitySnapshots`, chave `u:{uid}:equitySnapshots`): `{data, patrimonio, caixa, posicoesValor, base, origem, fonte, hora}`. `origem` "fechamento" | "app" (legado sem `origem` = "app"); `fonte` str ("brapi", "yahoo", "brapi+yahoo") ou null; `hora` "HH:MM" BRT da gravacao. Vem em `public_state().equitySnapshots` (api.getState) sem mudanca de rota.
- **Regra de convivencia (D4)**: `store.upsert_snapshot(conn, snap, user_id=None, *, origem="app", fonte=None, hora=None)`; "app" nao sobrescreve "fechamento" da mesma data (devolve a lista atual); "fechamento" sobrescreve "app". O corpo do cliente nunca define origem/fonte/hora; `POST /api/snapshot` segue sem kwargs. Espelho em `persistence.js upsertSnapshot(list, snap, ctx)` com `ctx.origem/fonte/hora` (autocontido, ctx de `putSnapshot` inalterado byte a byte).
- **`store.patrimonio_conta(positions, quotes, cash, reservado=0, option_positions=None, option_quotes=None)`** -> `{patr, posVal, cash, reservado, opcoesVal, opcoesSemMarcacao, semCotacao}`; `store.scopes_com_carteira(conn)`.
- **`status_snapshot` (agent.py)**, chaves aditivas: top-level `snapshotDiario` com exatamente `date, atLabel, duracaoS, contas, gravadas, puladasSemCotacao, erros, perdidasNaJanela, perdido, tickers (int), tickersSemCotacao (lista), fonte, erro`; `jobs.origem.snapshotDiario` ("memoria" | "kv" | null); `jobs.janelas.snapshotDiario = {hhmm, ate: "17:15", diaUtil: true, intervaloOk}`. `LAST_RUN` em memoria tem as mesmas 13 chaves (`snapshot_diario.LAST_RUN`, `JOB_NOME = "snapshotDiario"`).
- Fixtures para a leva 2 reutilizar/paridade: `server/tests/fixtures/snapshot_convivencia_casos.json` (C1-C7). A mescla M1-M10 (`mesclarSnapshots`) e a Tarefa 3, ainda nao existe.
- Env: `B3_SNAPSHOT_DIARIO_HHMM` (default 17:05, valido em [16:55, 17:15)), `B3_SNAPSHOT_DIARIO_OFF`.

### Validacao local
`cd server && .venv/bin/python -m pytest tests/test_snapshot_diario.py -q`. Para simular: `asyncio.run(snapshot_diario.maybe_run(conn, getter, now))` num banco de copia, com `now` aware em BRT dentro de [17:05, 17:15) de dia de pregao e `getter` async `tickers -> {t: {price, source}}`.

## Leva 2 (front / iOS / admin)

### Commits (so codigo)
- 081cffb4 `feat(quick-261013-u7w): iPhone adota os pontos de fechamento do servidor, data BRT no App e linhas do job no admin` (Tarefa 3)
- 7813e356 `test(quick-261013-u7w): guardiao generico de paridade registra putSnapshot como coberto` (Tarefa 4)
- 7284784f `test(quick-261013-u7w): guardiao do switch do assistente aceita a troca datada para hojeBRT() com sha travado` (substituta de guardiao, ver abaixo)

### Arquivos
- Novo: `web/tests/test_snapshot_diario_front.mjs` (M1-M10 + estaticos).
- Alterados: `web/src/persistence.js` (`mesclarSnapshots` privada e autocontida; usada em `_adotarCarteiraDoServidor`; sem metodo novo nos stores), `web/src/App.jsx` (`hojeBRT()` nos 4 pontos; streak intocado), `web-admin/src/App.jsx` (5 linhas `Kv` do snapshot de fechamento), `web/tests/test_fase3_paridade_stores_generica.mjs`, `web/tests/test_telas_registro.mjs`.

### Guardioes alterados
| Guardiao | Asserção antiga | Substituta | Nota |
|---|---|---|---|
| test_fase3_paridade_stores_generica.mjs (comentario) | `putSnapshot` na lista "sem teste de comportamento" | `putSnapshot` removido da lista, nota de cobertura (D4) | 2026-10-13 (quick 261013-u7w); nenhuma assertiva removida; contagem de metodos inalterada |
| test_telas_registro.mjs PARTE E | sha256 do bloco `switch (petTela)` === fixture (switch intocado) | (1) sha do bloco com `hojeBRT()` revertido para a expressao UTC === sha do fixture; (2) sha do bloco atual === `SHA_SWITCH_2026_10_13` | 2026-10-13 (quick 261013-u7w); o `case "evolucao"` fica dentro do bloco e a troca UTC->BRT e intencional; sha anterior conferido em 0c5c704d |

### Resultado
- Verifies das Tarefas 3 e 4: todos os .mjs listados verdes (cada um isolado); `npx vite build` ok em `web/` e `web-admin/`.
- Loop completo de `web/tests/*.mjs`, um por vez: unica falha restante `test_ios_assets.mjs` (bundle iOS desatualizado: faltam chunks do dist em `ios_dist`; resolve com `cap copy`, do orquestrador). `test_telas_registro.mjs` falhava pela troca intencional e foi corrigido (acima).
- No sandbox do executor, test_fase3_kill_switch_duracao.py segue com 4 falhas (ver nota da leva 1: efeito do sandbox).

### Desvios
- [Rule 1/guardiao] `test_telas_registro.mjs` quebrou pela mudanca intencional do `hoje` dentro do switch do `petSnapshot`; substituta datada em vez de reverter a mudanca (o PLAN manda BRT nesse ponto). Fora isso, nenhum.

### Nao verificado em runtime
- Adocao dos pontos do servidor no iPhone real (so a funcao pura e a presenca da chamada foram testadas; `getState` logado nao foi exercitado).
- Render das linhas no portal admin com dados reais do job (so build e checagem estatica).
- Data BRT do snapshot no app depois das 21:00 BRT (so estatico; `hojeBRT` ja tinha teste proprio).
- Execucao real do job as 17:05 em producao e consumo do orcamento brapi.

### Follow-ups
- Upload de pontos que so existem no iOS (aparelho nao envia seus `equitySnapshots` ao servidor; a mescla e so servidor -> aparelho).
- Reset feito em outro aparelho: o iPhone mantem pontos locais antigos e a mescla (uniao por data) os traz de volta/polui a serie no iPhone.
- Pontos antigos gravados com data UTC continuam com o dia possivelmente trocado (sem migracao).
- Task separada: stop/alvo e rotas de opcoes sem portao de pregao (W4), que podem alterar a carteira depois de 16:55.

## Self-Check: PASSED
Commits 3a0be1d5 e 0c5c704d existem; arquivos listados existem; `grep` confirma 1 ocorrencia de `snapshot_diario.maybe_run` em agent.py (:1305, fora do bloco do kill-switch) e a linha da rota `upsert_snapshot(...)` em main.py intocada.

## Verificação do orquestrador (2026-10-13)
- Gate entre levas: verifies da leva 1 re-rodados pelo orquestrador fora do sandbox — tudo verde, inclusive test_fase3_kill_switch_duracao (24 ok; as 4 falhas do executor eram do sandbox dele).
- Suíte canônica após a leva 2 (com cap copy): rc=0, pytest 3551 passed + todos os .mjs.
- Teste de fumaça do job numa CÓPIA consistente (sqlite backup) do banco local de dev, relógio 17:06, getter falso (VALE3 sem cotação de propósito): 52.642 contas, 49.763 gravadas (origem fechamento, fonte brapi, hora 17:06), 2.879 puladas sem cotação, 0 erros; tick seguinte só retenta as pendentes.
- Achado no fumaça e corrigido (): `_gravar_feita` regravava a lista inteira a cada conta (O(n^2)); passou a gravar em lotes de 200 + no fim (upsert idempotente). Tempo: 26 s no 1º tick, 0,8 s no seguinte. Teste novo `test_feitas_persistido_em_lote_e_no_fim`.
- Não verificado em runtime: execução real às 17:05 em produção (precisa de B3_AGENT_INTERVAL_S ≤ 300), adoção dos pontos num iPhone logado, admin com dados reais.
