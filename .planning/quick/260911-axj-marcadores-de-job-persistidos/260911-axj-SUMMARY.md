---
quick_id: 260911-axj
status: complete
commit: 13fc28e
branch: worktree-agent-a20132e672fc7f724
base: a2ec527108c188466c7a5eb63a5116fc39470fc5
files_modified: [server/app/db.py, server/app/agent.py, server/app/radar_daily.py, server/app/analysis_outcomes.py, server/app/fundamentals.py, server/app/intraday.py, server/tests/test_agent.py]
front_tocado: false
deploy_feito: false
---

# 260911-axj — Marcadores de job persistidos

`fix(260911-axj): marcadores de job sobrevivem ao reinicio do processo` — `13fc28e`
(7 arquivos, +385/-5; nenhum arquivo de `web/`, nenhuma deleção).

## O que mudou

| Camada | Mudança |
|---|---|
| `db.py` | `marcar_job(conn, nome, registro)` / `ler_job(conn, nome)` — helper único, chave `jobMarcador:<nome>`, escopo global (`user_id=None`). Nenhum dos dois levanta. |
| 4 módulos de job | `db.marcar_job(...)` no MESMO ponto onde já atualizavam o dict de memória. Persistência aditiva. |
| `agent.status_snapshot` | `_marcador_job()` lê o kv quando este processo não tem registro próprio, e devolve a origem do registro. |
| `agent.status_snapshot` | chave ADITIVA `jobs` (boot do processo + origem + janela de cada job). |

## Inventário: o que já persistia (pedido do plano)

Nenhum dos quatro persistia o registro **completo**. O que existia:

- `radar_daily` → `radarDailyLastRun`: **só a data**, e só na varredura automática (gate de `should_run`).
- `analysis_outcomes` → `analysisOutcomesLastRun`: **só a data** (gate FinOps de qa/42).
- `fundamentals` → `fundamentalsLastWarm`: **só a data** (gate FinOps de qa/42 — 60 req/run contra free tier de 200/dia).
- `intraday` → `intradayPass` (`CHAVE`): o caso mais próximo — persiste o **resultado** da passada, com `at`/`atLabel`/`ativos`/`comLacuna`. **Não reaproveitei**: a forma é outra (`erros` é lista, não contagem; não tem `duracaoS`) e esse payload é consumido pelo Radar intraday (`get_stored`). Mapear um no outro criaria uma segunda verdade divergente sobre a mesma passada — exatamente o defeito que o resto do repo evita. Custo de não reaproveitar: uma linha de kv por passada.

Os três gates de data **seguem intactos e separados do marcador**: gate é decisão do job (quem lê é o próprio job), marcador é observabilidade. Misturar os dois faria a tela decidir se o job roda.

## Desenho escolhido: helper único em `db.py` (não quatro pares, não em `agent.py`)

- **Helper único** porque quatro pares de `kv_set`/`kv_get` espalhados divergiriam no quinto job — e a evidência está no próprio repo: os três gates de data já divergem entre si em nome de chave e granularidade.
- **Em `db.py`, não em `agent.py`**: os quatro módulos já importam `db`, e `db` não importa nada do pacote. Helper em `agent.py` forçaria os quatro a importar `agent` no nível de módulo — ciclo de import (`agent` importa `store`/`skill_ref`, e já usa import local justamente para evitar isso).
- **Envelope `{emISO, registro}`** em vez do registro cru: carimbo de quando o marcador foi gravado, para diagnóstico, sem poluir o `registro` que vai ao snapshot.

### Regra de precedência (por que memória ganha da memória persistida)

O plano sugeriu "ler do banco, cair para a memória". Inverti, e a razão é o invariante de escrita: a gravação no kv é **best-effort** (pode ter falhado), enquanto o dict de memória é atualizado **sempre**. Com o banco vencendo, uma falha de escrita faria o painel mostrar uma data **mais antiga** do que a realidade — reintroduzindo o defeito por outro caminho. Ordem implementada:

1. memória registra execução (`date`/`at` preenchido) → `origem: "memoria"`;
2. senão, registro no kv → `origem: "kv"`;
3. senão → `origem: None`, e **só aí** "nunca rodou" é verdade.

Um `erro` que só a memória conhece (job falhou neste processo antes de registrar execução) prevalece sobre o persistido — a falha é deste processo. O registro do kv é **projetado** nas chaves do dict de memória: marcador gravado por outra versão do código (chave a mais, chave a menos) não vaza para o contrato da tela.

**Limite deliberado:** marcador só é gravado no caminho de SUCESSO. Gravar no caminho de erro sobrescreveria o registro de uma execução real anterior com `{date: None, erro: ...}` quando o job falha logo após um reinício — destruiria exatamente a informação que esta entrega adiciona.

## Provas

### 1. Reinício do processo (a prova central)

Script com reinício **real** (`importlib.reload` dos cinco módulos = estado de import, o que o deploy faz) + conexão **nova** ao mesmo arquivo de banco:

```
processo 1  radarDiario: {'date': '2026-09-11', 'atLabel': '11/09 08:08', 'duracaoS': 0.0, 'erro': None} origem: memoria
memória após reinício: {'date': None, 'atLabel': None, 'duracaoS': None, 'erro': None}
processo 2  radarDiario: {'date': '2026-09-11', 'atLabel': '11/09 08:08', 'duracaoS': 0.0, 'erro': None} origem: kv
OK — a data sobreviveu ao reinício do processo (antes: 'nunca rodou')
banco vazio radarDiario: {'date': None, 'atLabel': None, 'duracaoS': None, 'erro': None} origem: None
OK — sem registro em lugar nenhum, a tela ainda lê 'nunca rodou'
jobs.janelas: {'radarDiario': {'hhmm': '08:45', 'diaUtil': True}, 'intraday': {'pregao': True, 'gapMinS': 240}, 'avaliacaoAnalises': {'porDia': 1}, 'aquecimentoFundamentos': {'porDia': 1}}
```

Na suíte, `test_marcador_de_job_sobrevive_ao_reinicio_do_processo` cobre os **quatro** jobs (o script cobre um, com reinício real de módulo).

### 2. Falha de escrita não derruba o job (o invariante)

`test_falha_ao_gravar_o_marcador_nao_derruba_o_job`: espião substitui `db.kv_set` e **levanta** `sqlite3.OperationalError("database is locked")` para qualquer chave `jobMarcador:*` (as outras chaves passam). Rodando o job real (`radar_daily.run_daily`):

- `espiao["tentativas"] == 1` — tentou gravar;
- `r["results"] is not None` — **o job concluiu**;
- `LAST_DAILY["date"] == hoje` — a memória segue atualizada;
- `status_snapshot` continua servindo a data, com `origem: "memoria"`.

`test_falha_ao_ler_o_marcador_nao_derruba_o_snapshot`: espião levanta em `db.kv_get` para `jobMarcador:*` — o snapshot **não cai**, degrada para "sem registro". A observabilidade é a tela a que alguém recorre para diagnosticar; não pode ser a que quebra.

### 3. A forma do snapshot não muda

`test_status_snapshot_mantem_a_forma_que_o_portal_admin_le` compara o conjunto de chaves de topo contra a lista atual (16 chaves) + a aditiva `jobs`, e o conjunto de chaves de cada um dos quatro marcadores (`radarDiario`, `avaliacaoAnalises`, `aquecimentoFundamentos`, `intraday`) — o que `web-admin/src/App.jsx:118-130` lê. `test_marcador_persistido_por_outra_versao_nao_muda_a_forma_do_snapshot` prova a projeção. Os guardiões existentes continuam verdes sem alteração: `test_qa46_fase2_wiring` (igualdade com os dicts de memória) e `test_status_snapshot_nao_ganha_chave_nova`.

## Estado (c) — job que só roda em certa janela

Backend pronto, **front não tocado** (conforme o plano). A chave aditiva `jobs` entrega o que falta:

- `processoDesdeBRT` / `processoHaS` — quando ESTE processo subiu;
- `origem.<job>` — `"memoria"` | `"kv"` | `null` (os três estados);
- `janelas.<job>` — `radarDiario: {hhmm: "08:45", diaUtil: true}` (horário-alvo real, via `radar_daily.janela_hhmm()`, que valida o env), `intraday: {pregao: true, gapMinS: 240}`, os dois diários: `{porDia: 1}`.

Com isso a tela pode dizer "aguardando a próxima janela" quando `origem == null` **e** o processo subiu depois da janela de hoje.

### Pendência registrada

`web-admin/src/App.jsx:122-127` continua imprimindo `"nunca rodou"` quando o campo vem vazio. Depois de um reinício, a frase agora só aparece quando é verdade **ou** quando o job ainda não atingiu a janela do dia. Fechar o caso (c) por completo é edição de front (`Kv` dos quatro marcadores lendo `jobs.origem`/`jobs.janelas`), o que exige tarefa própria com `bump.sh` + `publicar-web.sh` — fora desta entrega.

## Suíte

`bash scripts/executar.sh --testes` — **EXIT=0**:

```
== Suítes do backend ==
2304 passed, 4 skipped, 450 warnings in 39.26s
== Suítes web ==
126 [OK], 0 [X]
```

(Primeira execução falhou em massa no web por sandbox — `Operation not permitted` ao criar os `.log` em mktemp; repetida com sandbox desabilitado, como prevê o plano. `test_ios_assets.mjs` passou neste worktree.)

Front não editado → sem `vite build` (nenhum arquivo de `web/` no diff).

## Não feito (por escopo)

Sem deploy, sem bump, sem `railway`, sem publicar. É deploy **só-backend** quando for a hora: bump manual de `SERVER_BUILD_ID` + `atualizar.sh --somente-deploy`.
