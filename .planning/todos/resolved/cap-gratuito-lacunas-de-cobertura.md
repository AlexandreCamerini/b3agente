---
title: Cap do gratuito — duas lacunas de cobertura achadas no planejamento da Fase 12
date: 2026-08-29
priority: high
resolved: 2026-08-29
resolution: "Alex escolheu a opção (a) para os dois itens — dobrados no escopo da Fase 13. Ver ROADMAP.md §Phase 13 (goal/success criteria expandidos, requirement CAP-12 novo) e REQUIREMENTS.md."
---

# Cap do gratuito: o que a Fase 12 (backend) deliberadamente NÃO cobre

Achados do planejamento da Fase 12 (v1.3). Nenhum dos dois estava no
`12-CONTEXT.md` — o scout não os viu. Ambos precisam de decisão do Alex; nenhum
foi implementado.

## 1. iOS não passa pelo gate de watchlist — CAP-01 não vale no app nativo

`web/src/persistence.js` tem dois stores. No `deviceStore` (iOS, local-first)
`putWatchlist` e `addWatchlistTicker` gravam direto no `localStorage`: nunca
chamam `PUT /api/watchlist` nem `POST /api/watchlist/add`. Só as preferências de
push sobem (`_agendarSyncPrefs`). Ou seja: depois da Fase 12, o limite de 10
ativos vale no web/PWA e **não vale no iPhone** — o usuário do app nativo passa
de 10 sem nenhuma recusa.

Por que ficou fora da Fase 12:

- A fase é backend-only por fronteira travada no `12-CONTEXT.md`.
- Enforcement no `deviceStore` exige o valor do limite no cliente. Ou o front
  hardcoda `10` (segunda fonte de verdade, contraria o contrato C-32/C-33), ou
  lê de um endpoint que exponha `max_watchlist` — endpoint que **ainda não
  existe** e que o ROADMAP atribui explicitamente à Fase 13
  ("essa exposição nova é escopo exclusivo da Fase 13, não da Fase 12").

Opções:

- **(a)** dobrar na Fase 13, que já vai criar o endpoint e já vai publicar o
  front (`bump.sh` + `publicar-web.sh`) — custo marginal quase zero;
- **(b)** fase 12.1 dedicada só ao enforcement no `deviceStore`;
- **(c)** aceitar como limitação conhecida do milestone e registrar no ADR-010.

Recomendação: **(a)**. Requer ampliar o escopo da Fase 13 de "visibilidade"
para "visibilidade + enforcement no cliente nativo", o que é mudança de
requisito (CAP-01 passa a ter uma parte na Fase 13) — por isso não foi feito
sem confirmação.

## 2. `web/src/plan.js` — espelho do front ainda tem a copy com CTA (CAP-07)

`web/src/plan.js` espelha `server/app/plan.py`. A `canAddTicker` de lá ainda
devolve `"O plano ${plan.id} permite até ${plan.maxWatchlist} ativos. Faça
upgrade para adicionar mais."` — exatamente a frase que a Fase 12 removeu do
backend por CAP-07 / princípio 8 do CLAUDE.md.

Hoje a frase é **inalcançável**: `PLAN_FREE.maxWatchlist` no front continua
`null` (decisão deliberada — o front não conhece o plano real da conta, o gate
autoritativo é o do servidor), e um guardião existente
(`web/tests/test_fase5_gate_mensal_front.mjs`, caso (e)) trava
`maxAnalysesPerMonth: null` nos dois planos. Então nenhum usuário vê esse texto
hoje.

Por que ficou fora da Fase 12: qualquer edição em `web/src/` obriga
`npx vite build` + `scripts/bump.sh` + `publicar-web.sh` (guardrail do
CLAUDE.md); um ciclo de publicação inteiro para trocar uma string morta não se
paga. A Fase 13 vai publicar de qualquer jeito.

Ação sugerida: dobrar na Fase 13 junto com o item 1 — trocar a string e decidir
ali se o espelho do front passa a receber os números reais (e, se passar,
condicionar ao plano real da conta, senão uma conta **pro** leva bloqueio
fantasma no cliente e CAP-04 quebra na UI).
