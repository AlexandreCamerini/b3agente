---
phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor
verified: 2026-10-22
status: passed
score: 8/8 success criteria verified
gaps: []
---

# Fase 50 — Verificação

Goal: stop/alvo/entrada saem de UMA função determinística do motor, geometria validada; IA só explica; entrada automática nasce com stop e alvo.

Método: leitura do código (não dos SUMMARYs) + testes direcionados (`pytest tests/test_marcos_*.py` = 138 passed; `test_marcos_espelho/stores/ui.mjs` e `test_api_parity.mjs` rc=0). Suíte canônica já verde (não reexecutada). Checkpoint 50-10 aprovado pelo Alex.

## Truths (Success Criteria)

| # | Truth | Status | Evidência |
|---|-------|--------|-----------|
| 1 | PUT /api/position 23,01/23,51/23,36/21,58 -> 400 PT-BR; deviceStore recusa com a mesma frase | VERIFIED | `main.py` rota PUT (~3105-3160): `HTTPException(400, motivo_preco)` + preço obrigatório (`MOTIVO_SEM_PRECO_VALIDAR`); `setups.validar_marcos` (setups.py:801); espelho `finance.validarMarcos` (finance.js:463) usado em `persistence.js:2020-2022`; regressão em `test_marcos_gravacao_store.py:26`, paridade por fixture |
| 2 | Legado inválido não é vendido (servidor e laço local); card/Diário "plano inválido" | VERIFIED | `agent.marcos_efetivos` (agent.py:982) e uso em :1002/:1193; `skill_ref.marcos_plano_txt(... "plano_invalido_diario")`; `cartao_posicao.py:233`; laço local `persistence.js:2303` + `finance.marcosEfetivos`; `test_marcos_agente.py`, `test_marcos_stores.mjs` |
| 3 | Posição por entrada automática / compra manual de setup / ordem pendente nasce com marcos de `marcos_do_plano` (ou sem marcos + motivo) | VERIFIED | agent.py:826 (revalidação), store.py:891-920 (`buy` com marcos), main.py:2914 (`/api/buy`), pending_orders.py:316 (eventos `compra_com_marcos`/`compra_sem_marcos`); `test_marcos_gravacao_store.py`, `test_marcos_pendentes.py` |
| 4 | Sizing por risco, lote 100 p/ baixo, limitado por allocPct; sem compra se R:R<1,5 no preço executado | VERIFIED | `setups.sizing_por_risco` (setups.py:836), `revalidar_na_execucao` (setups.py:819), agent.py:850; espelho `sizingPlano` com `limitadoPor` (finance.js) |
| 5 | Nenhuma rota de IA devolve stop/alvo da LLM; modal mostra marcos do motor, IA explica | VERIFIED | `main.py:_proposal_do_motor` (2406), `POST /api/marcos/{ticker}` (3167), N2 `registrar(... stop/alvo=None)` (main.py ~2549); `test_marcos_ia.py` (FORMAT sem stop/alvo, `parse_rich` ignora); `StopAlvoModal` App.jsx:4169 usa `store.marcos`; `localProposal` removida (App.jsx:393) |
| 6 | Gestão: breakeven a 1R e trailing 2xATR monotônico, desligável | VERIFIED | agent.py:461-499 (`GESTAO_BREAKEVEN_R`, `ATR_MULT_DEFAULT=2.0`, `gestaoAuto is not False`); toggle App.jsx:4203/10473; alvo dinâmico opt-in medido com `stopInicial` (agent.py:532-559, fix CR-01) |
| 7 | Opções lastreadas ancoradas em alvo/stop válidos, declaram fallback ao spot | VERIFIED | `opcoes_lastreadas.py:89-93` (invalida ambos se geometria inválida); `test_marcos_opcoes.py` |
| 8 | Paridade por `marcos_casos.json`; defaults.py<->catalog.js; suíte verde | VERIFIED | `server/tests/fixtures/marcos_casos.json` existe; `test_marcos_espelho.mjs` e `test_api_parity.mjs` rc=0; suíte canônica rc=0 (informado pelo orquestrador) |

## Cobertura de requisitos

| Req | Status | Código / teste |
|-----|--------|----------------|
| MARC-01, 02, 03 | OK | `setups.marcos_do_plano` (setups.py:734); `plano_operacional` alta delega (setups.py:903); `test_marcos_plano.py` |
| MARC-04 | OK | fontes antigas removidas: `riskPlanReference`/`localProposal` sem uso em `web/src`/`server/app` (restam só comentários); `alvoSugerido` permanece apenas no ramo "baixa" de `plano_operacional` (setups.py:947), que o produto (long-only) não grava |
| MARC-05 | OK | `rr` canônico vs `rrPlano` no card (`cartao_posicao.py`), `test_marcos_ui.mjs` |
| MARC-06, 07, 08 | OK | agent.py:826-850; `test_marcos_agente.py` |
| MARC-09 | OK | store.py:899, pending_orders.py:316, main.py:2914 |
| MARC-10 | OK | `test_marcos_ia.py`; N2 sem número próprio |
| MARC-11 | OK | store.py:642, main.py PUT, `persistence.js:2020-2022` |
| MARC-12 | OK | CLAUDE.md:130-133 (nota D-11/D-12); guardião `test_marcos_stores.mjs` atualizado com nota (review WR-02) |
| MARC-13 | OK | agent.py:982-1002, :1193; persistence.js:2303 |
| MARC-14, 15 | OK | agent.py:461-559 |
| MARC-16 | OK | opcoes_lastreadas.py:89-93; `test_marcos_opcoes.py` (put_bridge/top-4 diferidos, D-19, conforme escopo) |
| MARC-17 | OK | `docs/adr/015*.md:341` Adendo Fase 50; N2 deixa de gravar números (main.py ~2549) |
| MARC-18 | OK | modal com Aplicar habilitado e recusa exibida (`onRecusa`, App.jsx:10473); `test_marcos_ui.mjs`; aprovado no checkpoint 50-10 |
| MARC-19 | OK | `ALVO 2:1`/`riskPlanReference` ausentes da exibição e do contexto da IA (grep) |

Órfãos: nenhum.

## Anti-padrões
Nenhum TBD/FIXME/XXX introduzido nos arquivos checados. Achados do review IN-01, IN-05, IN-06 e item (c) de WR-03 (lote somado mantém `stopInicial`) foram conscientemente não tratados (fora de escopo, informativos) — WARNING informativo, não bloqueia.

## Observações (não bloqueantes)
- Produção segue em build anterior (auto-deploy Railway parado desde 15/10); validação com conta real só após publicar (já registrado em 50-10-SUMMARY).
- Resolução do review (CR-01, WR-01..06) conferida em código: `marcos_efetivos`, `marcos_da_posicao(avg=)`, `revalidarNaExecucao` presentes.

## Itens humanos
Nenhum pendente (checkpoint 50-10 aprovado pelo Alex).
