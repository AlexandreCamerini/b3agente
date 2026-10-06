---
phase: quick-261006-axi
plan: 01
subsystem: carteira / opcoes
tags: [opcoes, carteira, perna-avulsa, estados-completos]
requires: []
provides:
  - tickersComPernas inclui ativo só com perna; tickersSoComPernas; universoOpcoes
  - card "sem ações" na Carteira (CartaoPernaAvulsa) e no hub de Opções
affects: [web/src/estruturaCard.js, web/src/App.jsx, web/src/opcoes/OpcoesScreen.jsx, web/src/opcoes/HubOpcoes.jsx]
key-files:
  created: [web/tests/test_carteira_perna_avulsa.mjs]
  modified:
    - web/src/estruturaCard.js
    - web/src/App.jsx
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/opcoes/HubOpcoes.jsx
    - server/app/skill_ref.py
    - web/src/copy.js
    - web/tests/test_estrutura_card_logica.mjs
    - web/tests/test_opcoes_fluxo_render.mjs
    - web/tests/test_opcoes_universo_carteira.mjs
    - web/tests/test_opcoes_hub_workspace_ui.mjs
    - server/tests/test_opcoes_anatomia_rota.py
decisions:
  - "Universo do hub = posições de ações + pernas abertas (nunca watchlist); lastro/Montar seguem só em `carteira`"
  - "Backend não mudou: anatomia e sell já tratavam posicao ausente (provado por pytest)"
metrics:
  completed: 2026-10-06
  tasks: 3
---

# Quick 261006-axi: opção comprada sem ações do ativo some da Carteira e do hub

Causa: `tickersComPernas` partia de `positions` e o hub montava cards só de `ctx.data.positions`; ticker que só tem perna (PUT VALEV731W2 sem VALE3) caía fora das duas telas. Agora aparece como card "sem ações" nas duas, com a estrutura lida do motor e Encerrar, sem número de ação inventado.

## Commits

- 70a2a7a8 — Task 1: helpers puros (`tickersComPernas` ampliado, `tickersSoComPernas`, `universoOpcoes`) + pytest `test_perna_avulsa_sem_acoes` (anatomia ok, `acoes` None, sem marcador precoMedio; sell encerra a perna).
- 77925500 — Task 2: hub de Opções com universo = carteira + pernas; `card_subtitulo_sem_acoes` (sem "0 ações · 0 livres"); deep-link de Encerrar aceita o ticker avulso.
- 407611aa — Task 3: `CartaoPernaAvulsa` na Carteira (sem FaceAcao/ReguaPlano/EditorStopAlvo/BlocoBorisIA), "Portfólio vazio" só sem ações e sem avulsa; guardião novo.

## Textos novos (espelho skill_ref.py <-> copy.js, byte a byte, nos dois modos)

- `OPCOES_ESCADA.card_subtitulo_sem_acoes`: "sem ações deste ativo · opção sem lastro"
- `CARTAO_POSICAO.avulsa_sem_acoes`: "Sem ações deste ativo: só a opção está aberta."
- Mesmo texto nos dois modos (é fato, não voz); guardiões de espelho verdes.

## Deviations from Plan

- Backend: nenhuma mudança em `server/app` (o pytest passou direto).
- Guardiões reconciliados com nota datada (nenhuma asserção removida): `test_estrutura_card_logica.mjs` (expectativa de `tickersComPernas`), `test_opcoes_universo_carteira.mjs` (regex de `estadoInicialOpcoes` aceita `carteira: universo`; nota de cabeçalho; asserção nova `universo[0]`), `test_opcoes_hub_workspace_ui.mjs` (nota + asserção irmã de `universoOpcoes`).
- [Rule 1] Teste SSR novo ajustado: o termo "lastro" é span tocável (texto não contíguo no HTML) e "300 ações" casava `0 ações`; asserções corrigidas (só o teste, não o código).

## Achado fora do escopo: patrimônio (NÃO ALTERADO, decisão do Alex)

`portfolioMetrics` (web/src/finance.js:135) ignora perna sem `lastro` ("modelo antigo: fora do agregado", D-6, Fase 14), e `store.buy_option` (server/app/store.py:805) cria perna avulsa sem `lastro`. Efeito: a PUT do Alex debitou R$ 92 do caixa e não entra no patrimônio (patrimônio aparece R$ 92 menor). O guardião `web/tests/test_finance.mjs:141-143` trava esse comportamento. Mudar exige decisão de semântica de patrimônio + paridade com o equity do backend/benchmark. `finance.js`, `persistence.js` e `test_finance.mjs` sem diff.

## Verificação

- node: test_estrutura_card_logica, test_cartao_v6_logica, test_opcoes_{fluxo_render,universo_carteira,hub_workspace_ui,custo_declarado,escada_espelho,caminho_b_ui,anatomia_render,consolidacao_ui}, test_carteira_perna_avulsa, test_cartao_posicao_espelho, test_estrutura_card_ui, test_carteira_lastro_ui, test_cartao_v6_fechado: verdes.
- pytest: test_opcoes_anatomia_rota, test_estrutura_posicao, test_anatomia_perna, test_skill_ref: verdes.
- `npx vite build` e `npx cap copy ios`: ok. Suíte canônica completa NÃO rodada (orquestrador, fora do sandbox).

## Known Stubs

Nenhum. `qty: 0` é fato (zero ações); avg/stop/alvo `null`, nunca 0.

## Self-Check: PASSED

Commits 70a2a7a8, 77925500, 407611aa existem; test_carteira_perna_avulsa.mjs existe.
