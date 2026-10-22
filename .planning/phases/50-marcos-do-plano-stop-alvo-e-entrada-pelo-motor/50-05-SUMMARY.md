---
phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor
plan: 05
subsystem: agente-operador-server
tags: [agent, timing, marcos, sizing, gestao]
requires: ["50-01", "50-02", "50-03"]
provides:
  - nivel_gestao (breakeven a 1R + trailing 2xATR, so sobe)
  - gate de plano invalido no ciclo e no aviso fora do pregao
  - entrada automatica com marcos do plano, R:R do preco executado e sizing por risco
key-files:
  modified:
    - server/app/agent.py
    - server/app/timing.py
    - server/tests/test_marcos_agente.py
    - server/tests/test_agent.py
    - server/tests/test_entrada_automatica.py
    - server/tests/test_entrada_automatica_suspensa_adr017.py
    - server/tests/test_push_payload.py
    - server/tests/test_timing.py
metrics:
  tasks: 2
  completed: 2026-10-22
requirements: [MARC-06, MARC-07, MARC-08, MARC-13, MARC-14, MARC-15]
---

# Phase 50 Plan 05: Operador server-side e os marcos do plano

Ciclo do agente nunca vende por geometria inválida, gerencia o stop por breakeven a 1R + trailing 2xATR (só sobe) e a entrada automática nasce com stop/alvo do motor, dimensionada por risco e recusada quando o R:R ao preço executado cai abaixo de 1,5.

## Commits
- ed221bb5 feat(50-05): gate de plano invalido, gestao breakeven/trailing e alvo dinamico do stop gerido (Task 1)
- d8e1b77e feat(50-05): entrada automatica com marcos do plano, R:R do preco executado e sizing por risco (Task 2)

## O que mudou
- `agent.py`: `GESTAO_BREAKEVEN_R`, `_gestao_ligada`, `nivel_gestao` (puro, retorna `(nivel, chave_txt)`); `_aviso_diario` genérico (kv por dia) e `_avisar_plano_invalido` (kv `avisoPlanoInvalido`); gate `validar_marcos(..., avg=)` antes de qualquer trailing/venda no laço e em `_avisar_fora_pregao`; `_avaliar_entradas` revalida com `setups.revalidar_na_execucao`, dimensiona com `setups.sizing_por_risco` e compra com `marcos={"stop","alvo"}`; evento `buy` byte a byte igual + info `entrada_marcos_gravados`.
- `timing.py`: base do timing expõe `alvo` (= alvo2), `alvo1`, `gatilho`, `invalidacao`.
- Quick 261021-spd intacto (pré-check `qty_livre`, `_avisar_lastro_travado`, cicloEmAndamento não tocados).
- Custo registrado: a gestão padrão faz o ciclo buscar 1 snapshot por posição com stop (cache L2 do provedor) quando há `snapshot_getter`.

## Testes
`pytest` dos arquivos tocados + `test_push_*`: 196 passed (test_marcos_agente 20, test_entrada_automatica, test_entrada_automatica_suspensa_adr017, test_timing, test_timing_watch, test_agent, test_agent_lastro_ciclo, test_agent_modo_estudo, test_execucao_fora_pregao, test_push_payload, test_push_registro_evento). `test_push_registro_evento` falha só dentro do sandbox (ssl PermissionError); passa com sandbox desligado. Sem `vite build` (não tocou `web/src`).

## Deviations from Plan

1. **[Rule 1 - integração] Gestão e trailing global convivem pelo MAIOR nível.** O plano diz "usar nivel_gestao em vez da regra global". Isso quebraria o guardião `test_trailing_sobe_o_stop_e_nunca_desce` (posição legada com stop passa a ter gestão ligada por D-14) e enfraqueceria quem escolheu trailing percentual/ATR/estrutura. Os dois candidatos passam pela mesma comparação única `novo > pos["stop"]` e vale o maior.
2. **[Rule 1] Subida de stop usa `preco_ref=None` (não `price`).** Com alvo dinâmico, o stop sobe no mesmo tick em que o preço já bateu o alvo; `validar_marcos(preco=price)` recusaria por "alvo abaixo da cotação". `stop < price` é garantido no chamador (`novo < price`); estrutura (stop<alvo, alvo>PM) segue validada. A extensão de alvo passa `preco_ref=price`; ValueError vira warn e o fluxo de saída segue.
3. **Guardião `test_alvo_dinamico_estende_duas_vezes_e_fecha_na_terceira`** recebeu `gestaoAuto: False` com nota Fase 50. Interação real D-14/D-15 (a registrar para verificação): com a gestão ligada o stop vai a 1R/2xATR antes do alvo; `_rr(avg, stop, novo_alvo)` com stop >= PM devolve None (breakeven) ou R:R < 1,5 (trailing a 2xATR vs. extensão de 1,5xATR) — na prática a extensão do alvo dinâmico raramente ocorre em posição gerida. Regra de D-15 não alterada, conforme o plano.
4. **`test_entrada_automatica_suspensa_adr017.py` precisou de alteração** (plano dizia "SEM alteração"). Os testes positivos desse arquivo semeiam plano sem `alvo` e `initialBudget` default (10000): pela regra D-08 (sem alvo = recusa) e D-07 (risco sobre o capital da config) a entrada deixa de ocorrer. Fixture ganhou `alvo`/`alvo2`/`alvo1` e `initialBudget=100000`, com nota; asserções do gate ADR-017 intactas. Mesma atualização com nota em `test_entrada_automatica.py` e `test_push_payload.py` (não listado no plano; regressão direta).
5. Aviso de sizing: `"Entrada automática em {ticker}: <aviso de sizing_por_risco> Sem execução, aviso mantido."` (prefixo "Entrada automática" mantido; "não cobre 1 lote" preservado nos dois casos).
6. Incidente de processo: rodei `git stash` por engano durante a verificação (proibido neste repo). Lista de stash estava vazia antes, havia apenas a minha entrada; `git stash pop` imediato restaurou tudo, árvore e stash conferidos. Sem perda.

## Known Stubs
Nenhum.

## Threat Flags
Nenhum novo. T-50-17..21 mitigados (gate de geometria, revalidação na execução, dedupe diário em kv, monotonicidade única, try/except ValueError).

## Self-Check: PASSED
Commits ed221bb5 e d8e1b77e existem; arquivos modificados presentes; nenhuma deleção.
