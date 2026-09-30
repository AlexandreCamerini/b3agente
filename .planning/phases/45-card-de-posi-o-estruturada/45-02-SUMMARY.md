---
phase: 45-card-de-posi-o-estruturada
plan: 02
subsystem: web-front
tags: [card-posicao, estrutura, navegacao, opcoes, guardioes]
requires: []
provides:
  - "web/src/estruturaCard.js: decisao de exibicao pura do card estruturado (12 funcoes)"
  - "abrirTickerOpcoes + ctx.goOpcoes(aba, { abrirTicker }) one-shot Carteira -> Opcoes > Oportunidades"
affects: [45-03, 45-05]
tech-stack:
  added: []
  patterns: ["modulo puro sem React/I-O", "one-shot com inicializador lazy (sem useEffect pos-paint)"]
key-files:
  created:
    - web/src/estruturaCard.js
    - web/tests/test_estrutura_card_logica.mjs
    - web/tests/test_opcoes_abrir_ticker.mjs
  modified:
    - web/src/opcoes/memoriaOpcoes.js
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/App.jsx
    - web/tests/test_opcoes_consolidacao_ui.mjs
    - web/tests/test_opcoes_continuidade_ui.mjs
key-decisions:
  - "Ticker do one-shot e gravado independente do if de aba e validado contra a carteira no destino (UI-SPEC vence o esboco do PATTERNS, P10)"
  - "executarComTeto declarada como function normal retornando Promise (acceptance conta `^export function`)"
requirements-completed: [CARD-02, CARD-04, CARD-05, CARD-06]
completed: 2026-09-29
---

# Phase 45 Plan 02: Logica pura do card estruturado + one-shot Encerrar Summary

Modulo puro `estruturaCard.js` (estado de leitura, aviso sem stop, R:R, pill travada, chip de vencimento, regua 8%-92%, assinatura de recarga, pool com teto 3) coberto por 62 asserts Node, mais o canal `goOpcoes("oportunidades", { abrirTicker })` que abre Oportunidades com o painel do ticker ja aberto uma unica vez.

## Tarefas e commits

| Task | Commit | Resultado |
|------|--------|-----------|
| 1 estruturaCard.js + guardiao de logica | 2a4b3771 | 12 exports, 62 "ok", sem import de React/store/api/App, sem timers |
| 2 one-shot abrirTicker | 7020dbef | App.jsx +11/-2 linhas (limite 20); OpcoesScreen lazy init + useEffect([]) proprio |
| 3 P5 (so leitura) | (neste SUMMARY) | ver abaixo; `git diff --stat server/` vazio |

## Desvios do plano

Nenhum de regra 1-4. Ajustes de guardiao previstos no plano, ambos com nota "Reversao deliberada Fase 45":
- `test_opcoes_consolidacao_ui.mjs`: regex de `goOpcoes` atualizado para `(aba, opts)` + bloco condicional de abrirTicker (asserção de `onIr={() => ctx.goOpcoes("recomendadas")}` intacta).
- `test_opcoes_continuidade_ui.mjs` (nao listado no plano, mesma causa): o regex do import de `memoriaOpcoes.js` exigia exatamente 3 nomes; agora exige os 3 + `abrirTickerOpcoes`. Nenhuma asserção removida.

## P5 — destino do Encerrar

1. Quais pernas `pos_op_aberta` seleciona: a PRIMEIRA de `optionPositions` do underlying que tenha `lastro` (`server/app/main.py:3189-3190`). Put de protecao isolada TEM `lastro` (`server/app/store.py:1157`, `lastro={"t","qty"}`), logo e selecionada e `proposta_fechar` a trata como `put_protecao` (`server/app/opcoes_lastreadas.py`, ramo `tipo = ... else "put_protecao"`, ~l.452).
2. Collar, 2a perna: o collar grava a call primeiro e a put depois (`store.py:1273-1290`); ambas com `lastro`. `pos_op_aberta` pega so a primeira (a call), entao a proposta de fechamento em Oportunidades cobre so a CALL. A put do collar NAO tem caminho de fechamento nessa proposta (limitacao conhecida). `PropostaDoAtivo` ainda casa `posAberta` por `contractSymbol` da proposta (`OpcoesScreen.jsx:1119-1121`), reforcando que so ha CTA "fechar" para a perna proposta.
3. Rota de fechar aceita `contractSymbol` de PUT: sim. `main.py:4143-4224` localiza a posicao por `id` (qualquer perna), busca a cadeia em `calls` + `puts` (l.4154-4156) e, para `side == "comprada"`, chama `store.sell_option` (l.4217-4224). O gargalo e a UI/proposta (item 2), nao a rota.
4. Estudo: a rota devolve 403 "Modo Estudo nao executa ordens" (`main.py:4146-4148`); a UI renderiza a proposta condicional do Estudo sem executar (`PropostaLastreada.jsx:166` e `:252`), sem quebrar.

Conclusao: o card promete so navegar (copy `encerrarAria`) e nenhuma copy muda. Limitacao conhecida para o checkpoint 45-05: em collar, o painel de Oportunidades so oferece fechar a CALL; a PUT do collar so fecha por chamada direta a rota. Fechar 2 pernas / execucao nova segue Deferred (sem atomicidade).

## Guardioes executados (todos verdes)

test_estrutura_card_logica, test_opcoes_abrir_ticker, test_opcoes_consolidacao_ui, test_opcoes_continuidade_ui, test_opcoes_nav_primitivos_ui, test_opcoes_nav_tres_abas_ui, test_opcoes_universo_carteira; `cd web && npx vite build` ok. Suite canonica e `cap copy ios` nao rodadas (orquestrador, 1x por onda).

## Known Stubs

Nenhum. `estruturaCard.js` ainda nao e consumido por nenhum componente (o card entra em 45-03), por desenho do plano.

## Threat Flags

Nenhum. T-45-04 (ticker validado contra a carteira) e T-45-05 (`_resetScopeState` limpa `opcoesAbrirTicker`) mitigados e travados em `test_opcoes_abrir_ticker.mjs`.

## Self-Check: PASSED
Arquivos criados presentes; commits 2a4b3771 e 7020dbef existem; STATE.md/ROADMAP.md intocados.
