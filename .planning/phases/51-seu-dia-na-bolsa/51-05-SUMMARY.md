---
phase: 51-seu-dia-na-bolsa
plan: 05
subsystem: server/job de fechamento
tags: [dia-na-bolsa, job, push, vistos, yahoo, scheduler]
requires: ["51-01", "51-02", "51-03", "51-04"]
provides: ["dia_na_bolsa.registrar_vistos", "dia_na_bolsa.maybe_run", "dia_na_bolsa.payload_para", "dia_na_bolsa.e_se_de_ontem", "candle_cache.peek_meta", "evento de ajuste de stop com marcoMotor"]
affects: ["51-07", "51-08", "51-11"]
key-files:
  created:
    - server/app/dia_na_bolsa.py
    - server/tests/test_dia_na_bolsa_job.py
  modified:
    - server/app/candle_cache.py
    - server/app/agent.py
    - server/tests/test_agent.py
requirements: [ENG-01, ENG-02, ENG-03, ENG-04, ENG-06, ENG-08, ENG-09]
metrics:
  tasks: 3
  tests: 35 novos (34 no job + 1 em test_agent)
  completed: 2026-11-18
---

# Fase 51 Plano 05: Job de fechamento "Seu dia na bolsa" Summary

Módulo `dia_na_bolsa.py`: registro de vistos por conta com preços do motor, job idempotente (gate `is_trading_day`, 17:20 a 20:00 BRT) que monta o card das três famílias por conta com candles cache-first + Yahoo sob teto diário, push de fechamento com consentimento fail-closed, `payload_para`, `e_se_de_ontem` e hook no `scheduler_loop`. Zero chamada de LLM e zero de brapi no job.

## Commits
- `b940f714` feat(51-05): registro de vistos com precos do motor (+ `candle_cache.peek_meta`)
- `de4a0557` feat(51-05): job de fechamento, card por conta e payload
- `c97aa8e4` feat(51-05): push de fechamento, e_se_de_ontem, hook no scheduler e marcoMotor

## Declarações (N3)
- (a) Origem das barras do cache L2: o provedor que o populou via `candle_provider`, que pode ser brapi nas requisições dos usuários; o job `dia_na_bolsa` faz zero chamada brapi (grep de código filtrando comentários = 0).
- (b) O Radar já usa `yahoo.get_history` como busca de produção (`scanner.run_scan`); o fallback do job não introduz fonte nova.
- (c) Teste representativo J14 (teto `B3_DIA_NA_BOLSA_MAX_YAHOO=5`, 2 vistos + 2 posições + IBOV + 3 watchlist + 70 do universo, cache vazio): `yahooChamadas=5`, `cacheHits=0`, `semDado=73` (3 da watchlist + 70 do universo). Buscados nesta ordem: VIS1, VIS2, POS1, POS2 e IBOV. J13: com barra finalizada no L2 e >= 253 barras, `cacheHits=1` e zero chamada Yahoo para o ticker.
- (d) Emendas do CONTEXT: D-06/P-B (carteira × IBOV sozinha não gera card; família 2 só conta com >= 1 evento do motor) e D-12/P-A (cache-first, Yahoo fallback, teto 120, prioridade vistos > posições > IBOV > watchlist > universo; zero brapi), confirmadas pelo Alex em 2026-11-18, reversíveis (teto por env; revisão em `.planning/engajamento/DECISIONS.md`).

## Decisões de implementação
- Horário-alvo 17:20 (`B3_DIA_NA_BOLSA_HHMM`), depois do snapshot (17:05-17:15) e do atraso do Yahoo; espera o `snapshotDiarioLastRun` até 17:40, depois segue sem ele.
- W5: conta cujo visto aberto, posição ou o IBOV não tem a barra de hoje fica pendente (sem card parcial, fora de `K_FEITAS`); passadas com >= 10 min de intervalo; `K_LAST_RUN` só quando nada pendente ou na passada final (primeiro tick >= 20:00 do mesmo dia), que gera os cards com o que houver (faltante fora, IBOV null).
- Memo por dia em `_MEMO` + contador `diaNaBolsaYahooDia` no kv (sobrevive a reinício): o teto vale somando as passadas; busca repetida de série já obtida não acontece.
- Card guardado independente de modo (chave + variante + vals); `payload_para` aplica ordem por modo, chamada da 1ª família e o rótulo do conceito no vocabulário do modo.
- `{R}` em 1 casa decimal com sinal; `{pct}` do fato raro sem sinal (direção em `{direcao}`), conforme convenções de 51-02. `placar.semDado` conta vistos sem dado hoje (N6).
- `expirou`/`sem_gatilho` entram na linha do dia em que o visto resolve pela primeira vez.

## Deviations from Plan
**1. [Rule 1 - Teste] Fixtures e feriado.** 12/10/2026 é feriado no `pregao` (não é pregão), então os vistos de teste usam dataBase 09/10. Séries sintéticas foram desenhadas para nenhuma regra de raridade disparar por acidente.
**2. [Rule 2] `registrar_vistos` recusa uid vazio** (ValueError), para nunca gravar no balde anônimo (T-51-12).
**3.** Teste do `marcoMotor` foi acrescentado em `server/tests/test_agent.py` (arquivo fora da lista `files_modified`, só adição; guardiões de trailing intactos).

## Notas para as próximas ondas
- Conta sem watchlist gravada cai na watchlist padrão (`defaults`), então entra na coleta (prioridade 4). Os testes gravam `watchlist: []` explicitamente.
- Amplitude só dispara com >= 30 ativos com barra de hoje no universo do arquivo do Radar (73); com teto 120 e cache frio o universo pode ficar parcial (vai para `semDado` e a regra devolve None, nunca estima).
- 51-07 consome `payload_para(conn, uid, modo, agora)` e `e_se_de_ontem(conn, uid, hoje)`; `registrar_vistos(conn, uid, tickers, origem, agora)` levanta ValueError para origem inválida, lista > 60 ou uid vazio.

## Verificação
- `pytest tests/test_dia_na_bolsa_job.py tests/test_snapshot_diario.py tests/test_agent.py tests/test_dia_na_bolsa_push.py tests/test_dia_na_bolsa_regras.py tests/test_radar_daily.py tests/test_candle_cache.py` -> 183 passed.
- `tests/test_push_registro_evento.py`: 7 passam; 3 `test_gatilho_*` falham com `PermissionError` de certificado (sandbox, preexistente, já registrado em 51-03).
- Greps de aceite: `dia_na_bolsa.maybe_run` em agent.py = 1; `"marcoMotor"` = 1; `is_holiday(` = 0; brapi/llm em código = 0; `def peek_meta` = 1.
- Não rodados (regra de custo): suíte canônica, `vite build` (sem `web/src`), `cap copy ios`.

## Known Stubs
Nenhum.

## Threat Flags
Nenhum além do modelo: T-51-11 (regex, teto 60, origem allowlist, preço nunca do cliente), T-51-12 (isolamento por escopo testado), T-51-13 (semáforo 4, timeout, teto, K_FEITAS), T-51-14 (fail-closed + teto + pushEnviado), T-51-15 (J11: brapi/llm proibidos).

## Self-Check: PASSED
- `server/app/dia_na_bolsa.py`, `server/tests/test_dia_na_bolsa_job.py` existem; commits b940f714, de4a0557, c97aa8e4 presentes; STATE.md e ROADMAP.md intocados.
