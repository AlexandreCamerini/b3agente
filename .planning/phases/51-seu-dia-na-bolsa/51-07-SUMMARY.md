---
phase: 51-seu-dia-na-bolsa
plan: 07
subsystem: server/rotas + push do Radar
tags: [dia-na-bolsa, rotas, consentimento, radar, push]
requires: ["51-03", "51-05"]
provides: ["GET /api/dia-na-bolsa", "POST /api/dia-na-bolsa/vistos", "POST /api/dia-na-bolsa/convite", "linha Ontem: no push do Radar 08:45"]
affects: ["51-08", "51-10"]
key-files:
  created:
    - server/tests/test_dia_na_bolsa_rotas.py
  modified:
    - server/app/main.py
    - server/app/radar_daily.py
    - server/tests/test_radar_daily.py
requirements: [ENG-01, ENG-06, ENG-09, ENG-10]
metrics:
  tasks: 2
  tests: 12 novos (10 rotas + 2 radar)
  completed: 2026-11-18
---

# Fase 51 Plano 07: Rotas do card e linha "Ontem:" no Radar Summary

Três rotas autenticadas (`require_user`, uid do token) para o card, o registro de vistos e o convite do push de fechamento, mais a linha do "e se" de ontem por usuário no push do Radar das 08:45, sem push novo.

## Commits
- `c729e796` feat(51-07): rotas do card, dos vistos e do convite do fechamento
- `9bd3fb50` feat(51-07): linha do e se de ontem no push do Radar 08:45

## O que mudou
- `main.py`: `GET /api/dia-na-bolsa?modo=` (modo diferente de "operador" vira estudo) chama `dia_na_bolsa.payload_para`; `POST /vistos` valida lista, teto 60 ("Lista de ativos grande demais.") e traduz `ValueError` de origem em 400 PT-BR, sem receber preço do corpo; `POST /convite` exige booleano e é o único call site de `push.decidir_fechamento` (D-13).
- `radar_daily.run_daily`: `corpo = push_body(payload)` segue único; dentro do laço por uid monta `corpo_uid` = corpo + " " + `PUSH_RADAR[chave]` com `{T}` substituído, via `dia_na_bolsa.e_se_de_ontem` em try/except próprio. `store.push_events` e `notify_push` usam `corpo_uid`. `push_body` intocado.
- Guardiões: `test_dia_na_bolsa_rotas.py` (401 sem login, chaves do payload, ordem por modo, isolamento A×B, validação de vistos, convite booleano/escopo, register-token não altera `estado_fechamento` nos dois sentidos, um único `decidir_fechamento(` em main.py) e 2 casos em `test_radar_daily.py` (alvo/stop por usuário, sem "e se" e falha = corpo antigo, rastro igual ao enviado).

## Verificação
- `pytest tests/test_dia_na_bolsa_rotas.py` -> 10 passed.
- `pytest tests/test_radar_daily.py tests/test_push_registro_evento.py` -> 28 passed, 3 failed: os `test_gatilho_*` com `PermissionError` de certificado no sandbox (preexistente, já registrado em 51-03/51-05, não toca este plano).
- Greps de aceite: `"/api/dia-na-bolsa` >= 3, `decidir_fechamento(` em main.py = 1, `e_se_de_ontem(` em radar_daily = 1, `corpo_ontem` = 2, assinatura de `push_body` = 1.
- Não rodados (regra de custo): suíte canônica, `vite build` (sem `web/src`), `cap copy ios`.

## Deviations from Plan
Nenhuma funcional. `GET` aceita qualquer valor de `modo` e normaliza para "operador" ou "estudo" ("educacional" cai em estudo, mesma ordem).

## Known Stubs
Nenhum.

## Threat Flags
Nenhum além do modelo: T-51-19 a T-51-22 mitigados e testados; T-51-23 aceito (teto 60).

## Self-Check: PASSED
- `server/tests/test_dia_na_bolsa_rotas.py` existe; commits c729e796 e 9bd3fb50 presentes; STATE.md e ROADMAP.md intocados.
