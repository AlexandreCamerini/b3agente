---
phase: 51-seu-dia-na-bolsa
plan: 01
subsystem: server/regras-puras
tags: [tdd, puro, dia-na-bolsa, raridade, analysis_outcomes]
requires: ["51-00"]
provides: ["server/app/dia_na_bolsa_regras.py"]
affects: ["51-04", "51-05"]
tech-stack:
  added: []
  patterns: ["núcleo puro sem I/O", "None nunca 0", "variante por sha256"]
key-files:
  created:
    - server/app/dia_na_bolsa_regras.py
    - server/tests/test_dia_na_bolsa_regras.py
  modified: []
requirements: [ENG-02, ENG-03, ENG-04]
metrics:
  completed: 2026-11-18
  tasks: 2
  tests: 21
---

# Fase 51 Plano 01: Núcleo puro do card "Seu dia na bolsa" Summary

Módulo puro (sem I/O) com desfecho do "e se" sobre `analysis_outcomes._avaliar_entry`, placar semanal, família 2 a partir dos eventos do motor, cinco regras de raridade (p95 do IBOV, 2×ATR, gap, extremo de 52 semanas, amplitude), seleção do fato, ordem por modo e variante sha256.

## Commits
- `23f91a4e` test(51-01): guardião (21 testes)
- `9237ede2` feat(51-01): módulo `dia_na_bolsa_regras.py`

## Decisões
- `estado_do_visto` chama `_avaliar_entry` com `prazoPregoes = min(decorridos, 10)` sobre candles <= hoje; stop/alvo valem em qualquer dia, `expirou_*`/`sem_gatilho` só com 10 pregões (antes disso: `aberto`). `decorridos == 0` devolve aberto explícito (evita o `or HORIZON` do `_avaliar_entry` transformar prazo 0 em 10).
- Critério do IBOV raro = limiar `statistics.quantiles(n=100, method="inclusive")[94]` de |retorno| dos 252 anteriores (>= limiar); `percentil` reportado = fração estritamente menor. Pode sair ligeiramente < 0.95 no limite; o critério de decisão é o limiar, não o percentil reportado.
- `regra_extremo_52s`: percentil = 1.0 por definição (todo novo extremo supera 100% dos 252 anteriores). Empata com outros fatos de percentil ~1; desempate fica por usuário > mercado > ticker. Se a calibração (51-04) quiser outra hierarquia, ajustar aqui.
- `regra_amplitude`: percentil calculado sobre a amplitude histórica do próprio universo passado (None sem histórico); exige `AMPLITUDE_MIN_ATIVOS` ativos também nos dias de referência.
- Travados (D-07): `IBOV_PERCENTIL = 0.95`, `ATR_MULT_ATIVO = 2.0`. Calibráveis (D-08): `AMPLITUDE_MIN`, `AMPLITUDE_MIN_ATIVOS`, `GAP_MIN_ATR`.
- Reconhece o evento `marcoMotor` (criado em 51-05); `text` nunca é lido.

## Deviations from Plan
**1. [Processo - TDD] RED sintético.** O módulo foi escrito antes do primeiro run dos testes; para manter a sequência de gates no git, o commit `test(...)` foi feito sem o módulo (sem import, falharia) e o `feat(...)` depois. Os dois tasks foram cobertos por um único par RED/GREEN (arquivos idênticos nos dois tasks). Um bug de helper de teste (`**{int: ...}`) foi corrigido antes do commit.

Nenhuma outra: sem mudança de escopo, sem pacote novo.

## Verificação
- `cd server && ./.venv/bin/python -m pytest -q tests/test_dia_na_bolsa_regras.py` -> 21 passed.
- Greps de aceite: `_avaliar_entry(` = 1; `bateu_stop|bateu_alvo` = 0; `random` = 0; imports de db/rede = 0; `hash(` = 0; constantes e ids de conceito presentes (verificado também em teste).
- Não rodadas (fora do escopo do plano): suíte canônica, `npx vite build` (sem `web/src` tocado).

## Known Stubs
Nenhum.

## Threat Flags
Nenhum (módulo puro, sem superfície nova). T-51-01: preços de entrada/stop/alvo só entram via registro montado no servidor (51-05).

## Self-Check: PASSED
- server/app/dia_na_bolsa_regras.py, server/tests/test_dia_na_bolsa_regras.py existem; commits 23f91a4e e 9237ede2 presentes; STATE.md e ROADMAP.md intocados.
