---
phase: 51-seu-dia-na-bolsa
plan: 10
subsystem: web-front (integração App.jsx)
tags: [card, streak, decision_day, vistos, push]
requires: ["51-06", "51-07", "51-08"]
provides: ["card no Acompanhar", "streak por decisão em BRT", "decision_day", "vistos do app", "toggle do fechamento", "toque no push de fechamento"]
key-files:
  modified:
    - web/src/App.jsx
    - web/src/notify.js
    - web/tests/test_analytics_instrumentacao.mjs
  created:
    - web/tests/test_dia_na_bolsa_ui.mjs
metrics:
  tasks: 3
  completed: 2026-11-18
---

# Phase 51 Plan 10: integração do card no App

Card montado no topo do Acompanhar (antes do `OperadorIACard`), streak de abertura trocado por dias de decisão em BRT, `decision_day`, vistos de Radar/watchlist/carteira, toggle do fechamento em Configurações e toque no push de fechamento abrindo o Acompanhar.

## Commits
- e56fecf3 — feat(51-10): tarefas 1 e 2 (mesmo arquivo, edições entrelaçadas: um commit só)
- 45e2d1a7 — test(51-10): guardião da integração + EVENTOS da fase
- (docs) este SUMMARY

## O que mudou
- `App`: estado `diaNaBolsa` (carregando/ok/erro) via `store.getDiaNaBolsa(appMode)`; recarrega ao ter `data`, ao trocar de modo e em `visibilitychange`; exposto em `ctx.diaNaBolsa`/`ctx.recarregarDiaNaBolsa`. Falha vira estado "erro" isolado.
- `EvolucaoScreen`: `<DiaNaBolsaCard>` antes do `<OperadorIACard>`; bloco "dias de consistência" substituído por `<FaixaDecisao>`.
- Streak por abertura (efeito UTC) removido; `config.streak` legado intocado. `A.registrarDecisao(origem)` (card|plano|stop) une `hojeBRT()` em `config.diasDecisao` e emite `decision_day {modo, origem}` 1x/dia; `setStop`/`setAlvo` chamam com "stop". Sem origem "não entrar".
- `radar_result_opened` leva `setup`; `registrarVistos([t], "radar")`; efeito diário (chave `b3-dnb-vistos-dia`) registra watchlist e carteira.
- Configurações: linha "Resumo do fechamento (17:15)" só no nativo, gravando por `store.decidirFechamento`.
- `notify.onPushTap`: aceita `kind === "fechamento"` exato sem ticker; App abre `evolucao` e recarrega o card.

## Verificação
Guardiões verdes: test_analytics_instrumentacao, test_dia_na_bolsa_ui (novo), _card, _push_prefs, _stores, test_vocabulario_espelho, test_api_parity, test_conceito_ui, test_telas_registro. `npx vite build` ok.

## Deviations from Plan
1. [Rule 1] Comentários que citavam o título do card em App.jsx quebravam `test_vocabulario_espelho` (anti-hardcode); reescritos sem o literal.
2. Tarefas 1 e 2 num único commit (mesmo arquivo).
3. `podeConvidar` = `isNative` + `notif.enabled` (mestre local de notificações); não há sinal de permissão do SO mais barato disponível no escopo do Acompanhar.
4. `onAbrirPlano`/`onAbrirAtivo` reusam `ctx.openAvaliar(ticker)` (navegação existente para o ativo).
5. Rótulo do toggle usa `diaNaBolsaTxt("estudo","config_rotulo")` (texto idêntico nos dois modos).

## Known Stubs
Nenhum.

## Threat Flags
Nenhum além do modelado (T-51-30/31/32 mitigados e travados por guardião).

## Self-Check: PASSED
