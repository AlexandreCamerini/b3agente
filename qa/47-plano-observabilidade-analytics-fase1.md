# qa/47 — Plano: Fase 1 de Observabilidade + Analytics de Comportamento

**Data:** 2026-08-13 · **Status:** plano aprovado para implementação da Fase 1
(infra de backend) · **Pedido por:** Alex, reconciliando dois streams — a
auditoria já fechada de observabilidade/governança (`qa/46` + ADR-011) e uma
especificação de analytics de comportamento do usuário que **não pôde ser
recuperada** (colada em turno anterior, perdida na compactação da conversa e
não localizável em nenhum arquivo do repo). Este documento não re-decide nada
do `qa/46` — só resolve as 5 lacunas que a reconciliação deixou em aberto.

**Premissa declarada (por falta da spec original)**: em vez de instrumentar
os "12 eventos" nomeados na spec perdida (nomes desconhecidos), o schema
desta fase é **genérico** — aceita qualquer `event` (string livre,
namespaced pelo cliente) + `properties` (JSON). Isso não é uma escolha de
conveniência: é a única forma de construir a infra de ingest sem inventar
nomes de evento que a spec original talvez não usasse. A instrumentação real
das telas (Etapa 2 da spec original, fora de escopo aqui de qualquer forma)
fica bloqueada até a spec ser reescrita ou recolada.

---

## Decisão 1 — SQLAlchemy vs. sqlite3 puro

**sqlite3 puro**, mesmo padrão de `server/app/db.py` (`conn.execute`,
`CREATE TABLE IF NOT EXISTS`, migração aditiva via `ALTER TABLE` + `except
OperationalError: pass`). Trade-off: perde schema declarativo/migração
tipada do SQLAlchemy, mas ganha consistência total com o resto do backend —
zero dependência nova, zero segunda forma de falar com SQLite no mesmo
processo, reaproveita o padrão `_ThreadLocalConnection` já validado para
concorrência (WAL + busy_timeout) em vez de introduzir um pool de conexões
paralelo.

## Decisão 2 — Caminho real de `analytics.db`

**Arquivo separado, mesmo diretório do banco principal**: derivado de
`Path(db.default_db_path()).parent / "analytics.db"` — ou seja, se
`B3_DB_PATH=/data/b3_agente.db`, o analytics fica em `/data/analytics.db`,
dentro do MESMO volume persistente do Railway. Nunca `./analytics.db`
(relativo ao cwd do processo — seria apagado a cada redeploy).

Por que arquivo separado (e não tabelas novas dentro de `b3_agente.db`):
isolamento de um dataset aditivo, potencialmente alto-volume e sujeito a
purga periódica, do arquivo que guarda estado transacional (posições,
sessões, saldo simulado) — o job de rollup+purga do analytics não deve
competir pelo WAL/lock do banco que atende toda rota autenticada do app.
Custo: uma segunda instância de `_ThreadLocalConnection` (mesma classe,
zero abstração nova) e dois arquivos `.db` no volume em vez de um.

Módulo novo `server/app/analytics.py` replica só o necessário de
`db.py` (`connect`/`shared`/`init_db`) apontando pra esse segundo caminho —
não reabre `db.py` para generalizar multi-arquivo.

## Decisão 3 — Onde este dado aparece pro Alex nesta fase

**Sem dashboard.** Um endpoint de leitura, `GET /api/analytics/summary`,
atrás do mesmo `_is_obs_admin` que já guarda `/api/obs/*` (`main.py:382`) —
JSON cru, sem tela nova. Consulta manual também possível via
`sqlite3 analytics.db` direto no volume (mesmo padrão que já se usa hoje
para depurar `b3_agente.db`).

## Decisão 4 — Onde entra no mapa de telas do `qa/46`

**Nova sexta área, "Comportamento do Usuário"**, ao lado de "Ações
Automáticas & Eficiência" — não dentro de "Visão Geral". Motivo: a própria
Decisão 3 do `qa/46` já separa por cadência — Visão Geral é polling leve
(15s, status operacional), enquanto isto é dado de auditoria/drill-down sob
demanda, mesmo tier de "Processos"/"Dados". Misturar quebraria essa divisão
que o `qa/46` já fixou. Implementação da tela em si segue fora de escopo
(pertence ao projeto da aplicação separada, ADR-011 Decisão 1 — não nasce
nesta rodada).

## Decisão 5 — Ordem de execução (mesclando os dois streams)

1. **`qa/46` Fase 1** (wiring — expor campos já computados: heartbeat,
   radarDiario, avaliacaoAnalises, protecaoSemOperador, breakdown brapi/IA)
   — zero schema novo, risco mínimo, pode andar em paralelo a isto.
2. **Analytics Fase 1 — esta rodada** (ingest + rollup + purga + leitura
   admin) — schema novo mas isolado (arquivo próprio), não toca fluxo
   existente.
3. **`qa/46` Fase 2** (navegador de tabelas + campo `origem` em `history` +
   contadores hoje ausentes) — mexe em `history`, estrutura compartilhada
   com o ledger financeiro real da simulação; maior raio de impacto, vem
   depois da infra de analytics estar validada em produção.
4. **Client SDK + instrumentação dos eventos reais + funil completo** —
   bloqueado até a especificação original ser recuperada ou reescrita; não
   há nomes de evento confiáveis para instrumentar hoje.
5. **Aplicação separada de observabilidade** (ADR-011 Decisão 1) — maior
   entrega, consome os endpoints de leitura dos dois streams; por último.

---

## O que nasce na Etapa 2 (implementação desta rodada)

- `server/app/analytics.py`: conexão própria (Decisão 2), schema:
  - `analytics_events(id, user_id, event, properties_json, client_ts,
    ingested_at, day)` — dado bruto, purgado após 90 dias.
  - `analytics_daily(day, event, count, distinct_users, PRIMARY
    KEY(day, event))` — rollup que sobrevive à purga do bruto (preserva
    contagem histórica; `distinct_users` além de 90 dias vira soma de
    diários, não distinct exato entre dias — limitação documentada, não
    escondida).
- `POST /api/analytics/events` (`require_user`, mesmo padrão de auth das
  outras rotas autenticadas): batch `{"events": [{"event": str,
  "properties": dict, "ts": float|null}, ...]}`.
  - Validação: rejeita (400) qualquer `properties` cuja CHAVE bata num
    denylist case-insensitive (`email`, `cpf`, `senha`, `password`, `token`,
    `saldoReal`, `valorReal`, `cartao`) — não filtra silenciosamente, loga
    via `obslog` como achado a revisar (guardrail do escopo proibido).
  - Rate limit: reusa `metering.check`/`consume` (não cria `rate_limit.py`)
    — requer um parâmetro `section` novo em `metering.py` (hoje hardcoded
    em `SECTION="aiUsage"`), para não misturar o balde de cota de IA
    gerenciada com o de eventos. Estado do rate-limit fica no `kv` do banco
    PRINCIPAL (`db.py`), não no `analytics.db` — é contador efêmero, não
    dado de produto. Excedente → 429 (não 402: aqui não é "cota paga", é
    proteção contra flood).
- Job diário `analytics.maybe_run(conn_analytics)`, mesmo padrão de
  `radar_daily.should_run`/`LAST_*` — chamado no `scheduler_loop`
  (`agent.py`) num hook próprio, **não** condicionado ao kill-switch do
  agente (esse é sobre execução de ordens, não sobre rollup de analytics) —
  só ao próprio `B3_ANALYTICS_OFF`. Faz: (a) agrega o dia anterior em
  `analytics_daily`; (b) purga `analytics_events` com `day` > 90 dias atrás.
- `GET /api/analytics/summary` (`_is_obs_admin`, mesmo portão de
  `/api/obs/*`): 3 blocos, direto de `analytics_events` (dado bruto,
  precisão total dentro da janela de retenção de 90 dias):
  1. **Adoção por feature** — contagem e usuários distintos por `event`,
     no intervalo pedido (default 30 dias).
  2. **Funil** — recebe lista ordenada de eventos via query param (default
     de 2 passos, `onboarding_completed` → `trade_simulated`, os únicos
     nomes que a própria especificação perdida menciona explicitamente no
     prompt de reconciliação); conta quantos usuários completam cada passo
     em sequência temporal.
  3. **Shown vs. dismissed** — agrupa por convenção de sufixo (`*_shown` /
     `*_dismissed`), casa pelo prefixo comum, mostra os dois lados.

## Fora desta rodada (confirmado pelo escopo proibido)

Client SDK (`src/lib/analytics.ts`), instrumentação de tela, rota de
exclusão sob pedido, política de privacidade, app de observabilidade,
qualquer mudança em `plan.py`, merge/publish/bump de carimbo.

## Verificação

- `bash scripts/executar.sh --testes` sem regressão.
- Teste novo (`server/tests` ou equivalente): ingest aceita lote válido;
  rejeita batch com chave sensível (400); estoura rate limit de
  `metering` (429); rollup agrega um dia sintético corretamente; purga
  remove só `day` > 90 dias atrás (fixture com timestamp controlado).
- Teste apontando `B3_DB_PATH` pra um tmpdir confirma `b3_agente.db` e
  `analytics.db` lado a lado nesse tmpdir, não em `cwd`.
