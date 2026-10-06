---
phase: quick-261006-bwv
plan: 01
subsystem: patrimonio / opcoes
tags: [patrimonio, opcoes, paridade, guardiao]
key-files:
  created:
    - server/tests/fixtures/patrimonio_opcoes_paridade.json
    - server/tests/test_patrimonio_opcao_avulsa.py
    - web/tests/test_patrimonio_opcao_avulsa.mjs
  modified:
    - server/app/store.py
    - server/app/main.py
    - web/src/finance.js
    - web/src/App.jsx
    - web/src/copy.js
    - web/tests/test_finance.mjs
decisions:
  - "Perna sem cotacao viva carrega pelo custo de entrada (avg), contada em opcoesSemMarcacao/sem_marcacao e sempre sinalizada; nunca 0."
  - "Perna sem side = comprada (modelo buy_option)."
metrics:
  completed: 2026-10-06
---

# Quick 261006-bwv: patrimonio conta opcao comprada sem lastro

A perna avulsa (`buy_option`, ex.: PUT VALEV731W2 100 x R$ 0,92) passa a entrar no patrimonio na Carteira, na Evolucao e no `pet:evolucao`, com paridade front x backend por fixture unica de 7 casos e sinalizacao "premio de abertura — sem cotacao ao vivo".

## Commits
- 3acf6558 — backend: `store.valor_opcoes` pura, `_pet_resumo_evolucao` soma opcoes (e avisa), fixture A-G, pytest.
- 18b73560 — front: `portfolioMetrics` sem filtro de lastro, `opcoesSemMarcacao` no retorno, guardiao D-6 de `test_finance.mjs` reconciliado (nota 2026-10-06, bloco preservado), teste Node de paridade.
- a1e3f079 — UI: linha `cp.linhaPatrimonioOpcoes` com `m.opcoesSemMarcacao > 0` na Carteira e no CapitalCurve; copy estudo "opcoes em aberto".

## Verificacao
- pytest: test_patrimonio_opcao_avulsa + test_ordens_pendentes_rotas + test_opcao_descoberto_gate = 49 passed.
- Node: test_patrimonio_opcao_avulsa, test_finance, test_carteira_lastro_ui, test_status_mercado_ui, test_carteira_perna_avulsa verdes; contagem de 7 `portfolioMetrics(` em App.jsx preservada.
- `npx vite build` ok; `npx cap copy ios` ok (rodado de `web/`; da raiz o npx tenta buscar pacote e e bloqueado pelo sandbox).
- Historico: `upsert_snapshot`, `buy_option`, `sell_option` nao tocados; teste prova equitySnapshots byte-identicos.

## Deviations from Plan
Nenhuma de escopo. Detalhes: helper `_num` de `valor_opcoes` converte string numerica como `Number(x)||0` (paridade); `portfolioMetrics` tambem exige `Number.isFinite` para cotacao viva (paridade com `math.isfinite`).

## Limitacoes
- Valor das opcoes usa o premio de abertura (sem cotacao de contrato) na Carteira, na Evolucao e no Boris; dito na tela.
- `web_dist`/`ios_dist` nao republicados (bump/publicar-web ficam com o orquestrador).
- Suite canonica completa nao rodada (conforme restricao).

## Known Stubs
Nenhum.

## Self-Check: PASSED
