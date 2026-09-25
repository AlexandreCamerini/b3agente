---
title: SubAbaOperar busca gate/proposta duas vezes quando o ticker já foi consultado no topo da aba Opções
date: 2026-09-16
priority: low
resolved: 2026-09-20
resolution: "Resolvido pelo fold-in D-04a do Plano 33-05 (Fase 33, 2026-09-20), ANTES da Fase 39 existir: SubAbaOperar passou a ler opcoesPorTicker[ticker] (o fan-out único de useOpcoesPropostas, já calculado no topo de OpcoesScreen.jsx) em vez de rodar os dois useEffect próprios — a busca duplicada de store.optionsGate/store.optionsProposta caiu de 1 para 0 nesse componente, com nota datada no próprio código (OpcoesScreen.jsx, comentário citando este arquivo). A Fase 39 (39-04, D-01) renomeou SubAbaOperar para PropostaDoAtivo e moveu o painel para dentro do card de Oportunidades (Leitura B', DR-1 aprovada pelo Alex no 39-06) sem tocar essa fonte de dado — confirmado por leitura direta de PropostaDoAtivo em web/src/opcoes/OpcoesScreen.jsx: `const entrada = opcoesPorTicker[ticker] || null;`. Movido para resolved/ só agora, no fechamento da Fase 39 (39-06), porque é quando o registro do TODO foi auditado — a correção em si já estava em produção há mais de uma fase."

# Fetch redundante de gate/proposta em SubAbaOperar

Achado durante a execução do Plano 32-04 (`32-04-PLAN.md`, decisão
arquitetural B — "Fetch redundante de gate/proposta: NÃO é resolvido nesta
fase").

## O que é

`SubAbaOperar` (`web/src/opcoes/OpcoesScreen.jsx`) tem dois `useEffect`
próprios que chamam `store.optionsGate(ticker)` e
`store.optionsProposta(ticker, true)` sempre que o ticker selecionado muda.
No topo da mesma aba, a sub-aba Setups já chama `useOpcoesPropostas(store,
carteira.map(...))` — um hook de fan-out que busca gate+proposta para TODAS
as posições da carteira, incluindo o mesmo ticker que `SubAbaOperar` acabou
de consultar de novo.

Se o usuário visitou a sub-aba Setups antes de ir para Operar (o fluxo mais
comum, já que a aba sempre abre em Setups), o dado do ticker selecionado em
Operar já está em `opcoesPorTicker[ticker]` — mas `SubAbaOperar` não lê essa
fonte, refaz a busca.

## Por que ficou fora do Plano 32-04

Decisão declarada no `32-04-PLAN.md`: trocar a fonte de dado da sub-aba no
mesmo plano que muda o layout dela (portar o ramo multi-candidato) misturaria
duas classes de defeito. O `32-UI-SPEC.md` também registra isso como
opcional: "Não é exigido por este contrato de UI corrigir isso nesta fase".

## Guardião que prende a decisão

`web/tests/test_opcoes_subabas_ui.mjs`, regra 3: `store.optionsGate(`/
`store.optionsProposta(` aparecem exatamente 1x cada em `OpcoesScreen.jsx`
(a chamada de `SubAbaOperar`, não uma segunda busca duplicada dentro do
próprio arquivo). Essa regra NÃO impede a otimização proposta abaixo — ela
impede uma TERCEIRA busca aparecer no mesmo arquivo. Se a correção subir
`opcoesPorTicker` para `SubAbaOperar` reusar, a contagem de chamadas cai
para 0 nesse componente (a busca vira zero — os dois `useEffect` somem) e o
guardião precisa de nota datada explicando a queda de 1 para 0.

## O que fazer

1. Subir `opcoesPorTicker`/`opcoesCarregando` (o resultado de
   `useOpcoesPropostas`, já calculado no topo de `OpcoesScreen.jsx`) até
   `SubAbaOperar` via prop, em vez dos dois `useEffect` locais.
2. Se `opcoesPorTicker[ticker]` já tiver `gate`/`proposta` prontos, usar
   direto — sem chamada de rede nova. Só cair no fetch local quando o
   ticker selecionado em Operar não tiver sido varrido no topo (ex.: posição
   nova, ainda não coberta pelo fan-out).
3. Atualizar `web/tests/test_opcoes_subabas_ui.mjs` regra 3 com nota datada
   quando a contagem mudar.

## Contexto relacionado

- `32-04-PLAN.md` — decisão arquitetural B, seção "Fetch redundante de
  gate/proposta: NÃO é resolvido nesta fase".
- `32-UI-SPEC.md` — seção "Duplicações a resolver na mudança", subitem
  "Fetch de gate/proposta redundante".
- `web/src/opcoes/useOpcoesPropostas.js` — o hook de fan-out cuja saída já
  cobre o mesmo dado.
