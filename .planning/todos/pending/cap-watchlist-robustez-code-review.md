---
title: 3 achados de robustez do code review da Fase 12 (gate de watchlist)
date: 2026-08-29
priority: medium
---

# Cap de watchlist: 3 achados WR do code review (12-REVIEW.md, commit 265f98b)

Achados do code review da Fase 12 (v1.3, "Cap comercial"), não bloqueantes —
`status: issues_found`, mas fora do escopo dos `must_haves` da fase. Nenhum
foi corrigido inline; um chip de sessão (`task_9c8a1930`) foi criado pra
disparar essa correção numa sessão separada, mas o registro durável fica
aqui pro GSD rastrear entre fases.

## WR-01 — check-then-act sem lock em PUT/POST de watchlist

`server/app/main.py`: `PUT /api/watchlist` e `POST /api/watchlist/add` leem
a watchlist atual, checam o limite e escrevem, sem nenhum lock — diferente
de `store.ORDER_LOCK`, que o codebase já usa pra `cash`/`positions`
exatamente pra evitar essa classe de bug. Adições concorrentes de um único
ticker podem perder update.

## WR-02 — aritmética frágil reusando `can_add_ticker`

`server/app/main.py:1054`: `plan.can_add_ticker(len(final) - 1, ...)` reusa
o parâmetro "contagem antes de UMA adição" pra codificar uma checagem de
tamanho final em massa (PUT). Correto hoje (verificado em 9 casos de
fronteira pelo próprio review), mas frágil — a semântica só funciona por
coincidência com a comparação `>=` atual. Considerar um hook explícito
(ex.: `pode_definir_watchlist(tamanho_final, tamanho_atual, plano)`) em vez
de reusar `can_add_ticker` com um valor sintético.

## WR-03 — sem validação de tipo no corpo do PUT

`PUT /api/watchlist`: `body.get("tickers") or []` não valida tipo — um
valor truthy não-lista (string, bool, dict) pode zerar a watchlist em
silêncio ou disparar um `TypeError` não tratado que vira 500 opaco pro
cliente. Adicionar validação (ex.: `HTTPException(400, ...)` se não for
lista) antes de processar.

## Por que não foi corrigido na Fase 12

Nenhum dos três estava nos `must_haves` dos planos 12-01/02/03 — são
achados de review pós-hoc, não requirements da fase. Corrigir agora seria
escopo não pedido pelo milestone v1.3.
