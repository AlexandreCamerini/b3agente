---
phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor
plan: 07
subsystem: ia-n2-n3
tags: [llm, prompts, marcos, guardrails]
requires: [50-04]
provides: [ia-explica-marcos-do-motor]
affects: [llm.py, kpi.py, technical_models.py, technical_snapshot.py, defaults.py, catalog.js, main.py]
key-files:
  modified:
    - server/app/llm.py
    - server/app/kpi.py
    - server/app/technical_models.py
    - server/app/technical_snapshot.py
    - server/app/defaults.py
    - web/src/catalog.js
    - server/app/main.py
  created:
    - server/tests/test_marcos_ia.py
decisions:
  - "IA N2/N3 nao produz nem devolve numero gravavel (D-10); proposal das rotas = marcos do motor, sempre"
  - "riskPlanReference removido do contexto (D-18), sem manter como insumo interno"
  - "Hashes dos defaults anteriores de carteiraStopAlvo/Operador entraram em LEGACY_PROMPT_SHA256"
metrics:
  tasks: 4
  completed: 2026-10-22
---

# Phase 50 Plan 07: IA N2/N3 explica os marcos do motor

A IA deixa de propor e de receber numeros concorrentes: FORMAT, parsers, contexto tecnico e prompts mudaram, e as rotas N2/N3 sempre devolvem como `proposal` o stop/alvo do motor (`marcos_servico.marcos_para_posicao`), com `marcos`, `proposalOrigem: "motor"` e (N3) `iaExplica`.

## Commits
- d14a393c Task 1: FORMAT/FORMAT_PRO e parsers sem numero gravavel (D-10)
- 986b59a8 Task 2: contexto tecnico sem riskPlanReference/alvoSugerido (D-18)
- 82ceae9b Task 3: prompts N3, hashes legados, paridade catalog.js
- db5afd54 Task 4: rotas N2/N3 injetam e devolvem marcos do motor

## O que mudou
- `llm.FORMAT`/`FORMAT_PRO`: sem stopSugerido/alvoSugerido; pedem explicar MARCOS DO MOTOR e "Não há dados suficientes para concluir." sem marcos. `parse_carteira` devolve `proposal: None`, `riscos`, `quandoRevisar`, `numerosIaDescartados` (stop/alvo/cenarios/precoAtual da IA so marcam o descarte). `analyze_carteira`: sem fallback que promovia `parse_rich().proposal`; extensao `cenarios` numerica trocada por `modelosUtilizados` + regra de explicar `marcosMotor`. `kpi.parse_rich`: proposal sempre `{None, None}`.
- `technical_models`: sem `riskPlanReference` (contexto e 3 visoes por modelo). `_compact_setups`: sem `alvoSugerido`.
- `defaults.py`/`catalog.js`: prompts N3 explicam marcos, array por ativo `ativo/operar/explicacao/riscos/quandoRevisar`; texto de skill sem stopSugerido; hashes dos defaults anteriores em `LEGACY_PROMPT_SHA256`.
- `main.py`: helpers `_preco_ref_marcos`/`_proposal_do_motor`; N3 com `tech_context["marcosMotor"]` (sem `referencias`); N2 (`/api/technical/analyze`) com `context["marcosMotor"]`, `analysis_outcomes.registrar(stop=None, alvo=None)`, `operavel` por `marcos["valido"]`; `/api/analyze` legado devolve proposal do motor (nao injeta pacote na IA: rota so envia candles).

## Guardioes atualizados (nota "Fase 50", nenhum `def test_` apagado)
test_kpi, test_qa40, test_llm_errors, test_qa39 (parse_carteira_recomputa_rr agora trava descarte), test_auditoria_prompts (a8ii contrato, m3), test_snapshot_consistency, test_technical_models, test_pipeline_n2_n3 (3 parse_carteira), test_carteira_stopalvo_502. Guardioes que leem `alvoSugerido` de `setups._mk` (test_plano_operacional, test_qa39 setups, test_adr017_setups_aposentados, test_setups_br) ficam fora: `_mk` segue produzindo a chave; nenhum le o snapshot compactado nem o contexto da IA. Nenhum teste em web/tests le a chave.

## Testes
- `test_marcos_ia.py` novo: 11 testes (FORMAT, parsers, contexto, prompts/hash, rotas N2/N3 com LLM falsa 1.0/999.0, sem snapshot -> None).
- pytest (marcos_ia, pipeline_n2_n3, carteira_stopalvo_502, analysis_outcomes, auditoria_prompts, marcos_rotas, snapshot_consistency): 125 passed. Tasks 1-2: 56 e 53 passed.
- `npx vite build` ok; `web/tests/test_copy_theme.mjs` e `test_rr_min_fonte_unica.mjs` ok.

## Deviations from Plan
- [Rule 1] `test_qa39.py::test_parse_carteira_recomputa_rr`, `test_pipeline_n2_n3.py` (3 testes) e `test_carteira_stopalvo_502.py` esperavam numero no parser; o plano dizia que test_qa39 nao precisava de edicao, mas o teste de R:R recomputado depende de `cenarios`. Atualizados com nota Fase 50 / D-10.
- `test_m3_format_pede_null_nunca_zero` e `test_a8ii_prompts_de_carteira_compoem_do_canonico` atualizados (m3 ja na Task 1 para manter o verify verde).
- Teste de rota N3 usa marcos validos fixos (monkeypatch): a serie sintetica faz o motor real recusar por R:R baixo; o ramo de recusa fica coberto pelo motor real nos demais testes.

## Known Stubs
Nenhum.

## Self-Check: PASSED
