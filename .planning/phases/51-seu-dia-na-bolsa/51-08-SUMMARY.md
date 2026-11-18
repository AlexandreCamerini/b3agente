---
phase: 51-seu-dia-na-bolsa
plan: 08
subsystem: web-front
tags: [card, react, analytics, ui-spec]
requires: ["51-02", "51-05", "51-06"]
provides: ["DiaNaBolsaCard", "FaixaDecisao", "diaNaBolsaLogica"]
affects: ["51-10 (integração em App.jsx)"]
key-files:
  created:
    - web/src/diaNaBolsa.jsx
    - web/src/diaNaBolsaLogica.js
    - web/tests/test_dia_na_bolsa_card.mjs
  modified: []
metrics:
  completed: 2026-11-18
---

# Phase 51 Plan 08: Card "Seu dia na bolsa" (front) Summary

Componente `DiaNaBolsaCard` + `FaixaDecisao` com lógica pura separada e guardião; todo texto vem de `diaNaBolsaTxt` e do payload, chips de alvo e stop compartilham um único estilo neutro.

## Commits
- `113cc5ed` feat(51-08): lógica pura (familiasNaOrdem, linhasVisiveis, chaveExploracao, contarDiasDecisao, textoDecisao4Sem, faixaDots) + testes
- `22bc9dbf` feat(51-08): componente — `diaNaBolsa.jsx` + guardião estendido com regras visuais por leitura de fonte

## Contrato para 51-10
Props conforme `<interfaces>` do plano. Tokens chegam por `ui = {T, MONO, DISPLAY, SUBLINHADO}` (App.jsx não exporta `T`; `SUBLINHADO` é exportado de `entendimento.jsx`, mas o componente o lê de `ui` para ficar sem dependência de ciclo). `FaixaDecisao` recebe `diasDecisao` (ISO) e `ultimas4Semanas` do payload; a janela vem do servidor (sem `toISOString`).

## Verificação
- `node web/tests/test_dia_na_bolsa_card.mjs`: ok
- `node web/tests/test_vocabulario_espelho.mjs`: ok
- esbuild do `.jsx` (sintaxe): ok; `npx vite build`: ok

## Deviations from Plan
1. [Rule 3] O plano manda reusar a string "Simulação educacional com dinheiro virtual. Não é recomendação." de `disclaimers.js`, mas ela não existe lá. Usei `DISCLAIMERS.short` ("Simulador educacional · cotações reais · dinheiro simulado."), a linha curta de rodapé canônica do arquivo; não criei texto novo. Se o Alex quiser a frase do UI-SPEC literal, adicionar a chave em `disclaimers.js` (e trocar a referência no card).
2. `textoDecisao4Sem(mode, x, txt)` recebe `txt` injetado para manter a lógica pura livre de `copy.js`; o guardião passa `diaNaBolsaTxt`.
3. `faixaDots`: dia com decisão num dia sem pregão aparece como "decisao" (a decisão vence); sem decisão e sem pregão é "sem_pregao".

## Decisões de implementação (interpretação do payload 51-05)
- O número de carteira × IBOV usa marcadores no template (`f2_carteira_ibov`) para destacar os dois números em MONO 18/700 sem compor frase fora do copy; `ibovPct` nulo mostra `—` + `f2_ibov_indisponivel`.
- Termo sublinhado da família 3 só aparece se `conceito.rotulo` ocorre na frase do template; o botão sr-only "O que é {rotulo}?" e a ação `ver_conceito` sempre existem quando há rótulo.
- Botão de retry lê `erro_tentar` ("Tentar novamente") do copy.

## Known Stubs
Nenhum.

## Threat Flags
Nenhum (sem `dangerouslySetInnerHTML`; props de `track` só com modo/card/tipo/família/familias, guardado por teste).

## Self-Check: PASSED
