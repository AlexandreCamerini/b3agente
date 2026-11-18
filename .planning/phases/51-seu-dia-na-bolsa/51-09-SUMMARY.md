---
phase: 51-seu-dia-na-bolsa
plan: 09
subsystem: analytics-backend-admin
tags: [analytics, wau, rbac, admin-portal]
requires: ["51-05", "51-07"]
provides: ["analytics.wau", "analytics.engajamento_fechamento", "GET /api/analytics/engajamento", "painel Engajamento do fechamento"]
key-files:
  created:
    - server/tests/test_dia_na_bolsa_analytics.py
  modified:
    - server/app/analytics.py
    - server/app/agent.py
    - server/app/main.py
    - web-admin/src/App.jsx
    - web-admin/src/api.js
metrics:
  completed: 2026-11-18
---

# Phase 51 Plan 09: Engajamento do card (analytics + portal) Summary

WAU exato e exploração do card por família e modo calculados sobre o bruto de analytics, `wau_7d` persistido diariamente, rota RBAC `observabilidade.ver` e painel no portal sem meta nem tone (ENG-12, D-19/D-20).

## Commits
- `62ccc2b6` feat(51-09): `wau()`, `engajamento_fechamento()`, `wau_7d` em `METRICAS_CONHECIDAS`, gancho no `agent._maybe_registrar_metricas_diarias`, rota `GET /api/analytics/engajamento` (dias limitado a 7..90, cache de 10 min em `admin_cache`) + 8 testes
- `114a06c7` feat(51-09): `analyticsEngajamento` + `EngajamentoFechamento` dentro de `Comportamento()`, abaixo do funil

## Verificação
- `pytest tests/test_dia_na_bolsa_analytics.py tests/test_analytics.py`: 42 passed
- `npx vite build` em web-admin: ok; trecho novo sem `tone=`, `T.positive`, `T.negative` nem "30%"

## Decisões de implementação
- Unidade "card" = (user_id, properties.card). "Explorou" só conta cards também vistos (garante pct <= 100). Família: lista `familias` do shown cruzada com `familia` do explored, por modo.
- `operacoesPorAtivo` = total de `trade_simulated` no período ÷ média do WAU semanal (semanas com atividade); `null` se não houver WAU.
- Semana = segunda-feira (BRT). A janela do WAU é de 7 dias corridos, hoje incluído.
- Nenhum user_id nem ticker sai na resposta (T-51-28); teste cobre ausência de "meta/alvo/tone".

## Deviations from Plan
1. Os rótulos dos KPIs usam o período do seletor (`EXPLORAÇÃO DO CARD (30 DIAS)`) em vez de "4 SEM" fixo, porque a seção reutiliza o seletor 7/30/90 do plano ("mesmo seletor de período"). Rótulo literal "(4 SEM)" exigiria janela fixa de 28 dias.
2. Adicionei um `Card` pequeno com mediana/média/usuários de dias de decisão (o UI-SPEC pede a média num `Kv`).
3. O estado vazio é renderizado fora do `Estado` para não duplicar com "Nenhum dado neste filtro."

## Known Stubs
Nenhum. Os eventos `daily_card_*` e `decision_day` só chegam com a integração do 51-10; até lá o painel mostra o estado vazio.

## Threat Flags
Nenhum além do registro (T-51-27 RBAC testado com 403; T-51-29 `dias` limitado + cache).

## Self-Check: PASSED
