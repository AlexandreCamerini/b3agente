---
phase: 51-seu-dia-na-bolsa
plan: 03
subsystem: push / radar
tags: [push, consentimento, radar, arquivo-diario]
requires: ["51-00"]
provides:
  - push.quer_fechamento / decidir_fechamento / estado_fechamento / reservar_engajamento
  - radar_daily.get_arquivo / arquivo_ate (radarDailyArquivo:<data>)
affects: [51-05, 51-07]
key-files:
  created:
    - server/tests/test_dia_na_bolsa_push.py
    - web/tests/test_dia_na_bolsa_push_prefs.mjs
  modified:
    - server/app/push.py
    - server/app/auth.py
    - server/app/radar_daily.py
    - server/tests/test_radar_daily.py
    - web/tests/test_push_prefs_classes.mjs
decisions:
  - "fechamento/fechamentoDecidido nascem False, fora de PREFS_BOOLS; set_prefs descarta; só decidir_fechamento grava (desvio deliberado do texto de D-13)"
  - "teto de engajamento fail-closed no Radar; pref radar segue fail-open"
metrics:
  tasks: 2
  completed: 2026-11-18
---

# Phase 51 Plan 03: consentimento do fechamento, teto de engajamento e arquivo do Radar

Preferência opt-in `fechamento` (conta antiga não recebe sem decidir, conta nova nasce ligada), contador de 2 pushes de engajamento por dia compartilhado com o Radar 08:45, e arquivo diário do Radar com retenção de 45 dias.

## Commits
- 4132fcc4 — feat(51-03): pref fechamento opt-in, decidir_fechamento e teto de engajamento
- 0d5f0a10 — feat(51-03): arquivo diario do Radar com retencao e teto de engajamento no push

## O que mudou
- `push.py`: `fechamento`/`fechamentoDecidido` em `PREFS_PADRAO` (False), fora de `PREFS_BOOLS`; `set_prefs` descarta as duas chaves (cobre `register-token`); `quer_fechamento` fail-closed; `decidir_fechamento`; `estado_fechamento`; `reservar_engajamento` (`TETO_ENGAJAMENTO_DIA = 2`, kv `pushEngajamento` por escopo). `CLASSE_POR_TAG` intocado.
- `auth.py`: `decidir_fechamento(..., True)` após os dois `insert_user`, em try/except que nunca derruba a criação de conta.
- `radar_daily.py`: `store_result` grava também `radarDailyArquivo:<data BRT>` (`linhas` operáveis, `universo`, `dataBase` = pregão anterior), poda de 45 dias, `get_arquivo`, `arquivo_ate`. `run_daily` reserva o teto antes do `notify_push` (fail-closed). `_key`, `get_stored`, `esta_vencida` e o payload de `radarDaily:<period>` intocados.
- Guardiões: `test_dia_na_bolsa_push.py` (9 casos), `test_dia_na_bolsa_push_prefs.mjs` (aparelho nunca manda `fechamento`), 5 casos novos em `test_radar_daily.py`; `test_push_prefs_classes.mjs` só ganhou comentário.

## Verificação
- `pytest tests/test_dia_na_bolsa_push.py tests/test_push_prefs_classes.py tests/test_radar_daily.py`: verde (31 + 19).
- `node web/tests/test_dia_na_bolsa_push_prefs.mjs` e `test_push_prefs_classes.mjs`: verdes.
- `tests/test_push_registro_evento.py`: 26 passam; 3 falham (`test_gatilho_*`) com `PermissionError` em `ssl.create_default_context(cafile=certifi.where())` ao criar o cliente httpx — leitura de certificado bloqueada pelo sandbox, sem relação com este plano (não toca `agent.py`/gatilho). Não verificado fora do sandbox.

## Deviations from Plan
None funcional. Nota: o ponto de criação OAuth é o segundo `insert_user` em `upsert_oauth_user` (só conta nova); o caminho de login existente não regrava consentimento.

## Self-Check: PASSED
