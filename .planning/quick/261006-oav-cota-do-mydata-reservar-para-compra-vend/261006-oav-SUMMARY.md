---
phase: quick-261006-oav
plan: 01
subsystem: opcoes / mydata_budget
tags: [cota, mydata, prioridade, gate, obslog]
requires: []
provides:
  - classes de prioridade (usuario/fundo/descoberta) em mydata_budget via ContextVar
  - registrar_recusa com limite de taxa (obslog cat "cota")
  - reuso cross-key da cadeia em cache + lidoEm/cotacaoLidaEm/cotacaoIdadeS/pregao
  - semaforo (2) e fatia de descoberta (21/min) no gate de liquidez
  - fila de concorrencia + dedupe/TTL do gate no front (filaGate.js)
affects: [server/app/mydata_budget.py, server/app/options_provider_mydata.py, server/app/main.py, server/app/options_api.py, web/src/api.js]
key-files:
  created:
    - web/src/filaGate.js
    - server/tests/test_mydata_budget_prioridade.py
    - server/tests/test_opcoes_cota_reserva_rotas.py
    - server/tests/test_gate_concorrencia.py
    - web/tests/test_fila_gate.mjs
  modified:
    - server/app/mydata_budget.py
    - server/app/options_provider_mydata.py
    - server/app/main.py
    - server/app/options_api.py
    - web/src/api.js
    - server/tests/test_mydata_budget.py
    - server/tests/test_options_provider.py
decisions:
  - Classe de prioridade por ContextVar (sem kwarg novo nos chamadores; lambdas monkeypatchados seguem validos)
  - Reserva do usuario 10/min e 150/dia como FATIA do teto util (54/1.800); fundo 44/1.650; descoberta <=21/min
  - Fila do gate em api.js para nao mexer nos contadores de store.optionsGate( nem na paridade dos stores
metrics:
  tasks: 4
  completed: 2026-10-06
---

# Quick 261006-oav: cota do MyData (reserva, rajada, log)

Reserva de cota para compra/venda de opcoes, limite da rajada de gates (backend e front) e log com limite de taxa da recusa por cota, sem aumentar o teto total (54/min, 1.800/dia).

## Commits

- b0c0e4c7 Task 1: mydata_budget com classes de prioridade e registrar_recusa
- b08bca91 Task 2: rotas de execucao com contexto usuario, _sem_cota, reuso cross-key, idade da cotacao
- 43a86b62 Task 3: semaforo (2) e classe descoberta no liquidity_gate
- 4652acfb Task 4: filaGate.js + api.optionsGate via criarGateCacheado

## Verificacao

- pytest: test_mydata_budget*, test_options_provider*, test_mydata_provider, test_agent_options, test_opcoes_fronteira, test_brapi_budget, test_opcoes_cota_reserva_rotas, test_gate_concorrencia, test_gate_liquidez_rotas, test_opcao_descoberto_gate, test_fase5_rejeicao_rotas, test_opcoes_lastreadas_rotas, test_opcoes_collar_rota, test_opcoes_curadoria_rota, test_adr013_cobertura_rotas, test_mcp_guardioes: todos verdes.
- web: test_fila_gate, test_carteira_opcoes_tira, test_opcoes_subabas_ui, test_api_parity, test_opcoes_custo_declarado verdes; `npx vite build` ok; `npx cap copy ios` ok.
- Suite canonica completa NAO rodada (orquestrador).
- Invariantes: options_provider.py, App.jsx, persistence.js, opcoes/, skill_ref.py, copy.js sem diff; sem import de mydata_client em main.py/options_api.py; mensagem do 502 sem diff.

## Deviations from Plan

### Auto-fixed / reconciliacoes de guardioes (nota datada 2026-10-06, asserção preservada)

1. [Rule 1] test_mydata_budget.py: janela do minuto envolvida em `contexto("usuario")` (plano previa).
2. [Rule 1] test_mydata_budget.py::test_reservar_sob_corrida: ContextVar nao cruza ThreadPoolExecutor, entao `reservar(..., prioridade="usuario")` explicito (mede o teto total, como antes).
3. [Rule 1] test_options_provider.py::test_payload_ok_mydata_contem_todas_as_chaves...: conjunto de aditivos permitidos ganhou `lidoEm`; asserção de subconjunto mantida.

Nenhuma outra. Ajuste do checker aplicado: `pregao` das respostas de buy/sell vem de `chain.get("pregao")`, `None` explicito quando ausente (testado).

## Known Stubs

Nenhum.

## Fora do escopo (conforme plano)

IntersectionObserver nos AtivoCards e exibicao de `cotacaoIdadeS` na UI.

## Self-Check: PASSED

Arquivos criados presentes; commits b0c0e4c7, b08bca91, 43a86b62, 4652acfb existem.
