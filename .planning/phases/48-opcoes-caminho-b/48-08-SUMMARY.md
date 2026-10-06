---
phase: 48-opcoes-caminho-b
plan: 08
subsystem: frontend-opcoes
tags: [opcoes, hub, objetivo, confirmar, termos, acessibilidade]
requires: [48-01, 48-03]
provides:
  - web/src/opcoes/fluxoEstilo.js (T, alvos, foco, reduced-motion)
  - web/src/opcoes/TermoOpcoes.jsx (default + marcarTermos)
  - web/src/opcoes/HubOpcoes.jsx, useTecnicoCarteira.js
  - web/src/opcoes/ObjetivoAtivo.jsx, ConfirmarEstrutura.jsx
affects: [48-10]
key-files:
  created:
    - web/src/opcoes/fluxoEstilo.js
    - web/src/opcoes/TermoOpcoes.jsx
    - web/src/opcoes/HubOpcoes.jsx
    - web/src/opcoes/useTecnicoCarteira.js
    - web/src/opcoes/ObjetivoAtivo.jsx
    - web/src/opcoes/ConfirmarEstrutura.jsx
requirements-completed: [OPC-01, OPC-02, OPC-07, OPC-13]
metrics:
  completed: 2026-10-05
---

# Phase 48 Plan 08: Telas 1, 2 e 4 do caminho B Summary

Componentes isolados do hub, da escolha de objetivo e da confirmação, mais termo clicável inline e estilos do fluxo; nenhum arquivo existente editado (fiação é do 48-10).

## Commits
- f97ea143 feat(48-08): fluxoEstilo e TermoOpcoes
- 635c16d3 feat(48-08): HubOpcoes e useTecnicoCarteira
- 23b9e959 feat(48-08): ObjetivoAtivo e ConfirmarEstrutura

## Entregue
- fluxoEstilo: tokens via var(--...) (sem hex, sem token novo), ALVO_MIN 44, CTA_MIN 48, FOCO, TIPO (12/14/16/24), transicoes que viram {} em reduced-motion, DISPLAY (espelho de App.jsx:313).
- TermoOpcoes: `marcarTermos` pura (1a ocorrência, case-sensitive); termo com setor -> `A.abrirSetor` (toque + sr-only "O que é X?"); com kb -> `onAbrirVerbete` só se didática ligada e verbete no catálogo; sem registro -> texto comum. SUBLINHADO importado, não redefinido.
- HubOpcoes: título, frescor (selo de pregão fechado via `mercado_fechado`), aviso virtual, Atenção só com vigia (custo declarado antes do clique), cards da carteira (role=button, minHeight 64, Enter/Espaço), estados vazio/erro de fonte/carregando.
- useTecnicoCarteira: 1 pedido por ticker por montagem, chave primitiva, erro isolado por ticker.
- ObjetivoAtivo: ordem do backend, `aria-disabled` com motivo escrito, "Montar do zero" 44px, estados carregando/erro/sem_posicao.
- ConfirmarEstrutura: sem botão no Estudo; Operador usa `onExecutar(cand, {aceitaLiquidezDificil: ===true, origem:"escada"})` com cand copiado de `degrau.execucao`; "Ordem rejeitada: motivo" verbatim; checkbox de consentimento para recusa de liquidez DIFÍCIL.

## Deviations from Plan
Nenhuma de regra. Premissas: (1) prêmio por perna lido de `degrau.porAcao.premioPago/premioRecebido` (formato do 48-04); (2) `termos` do degrau é mapa de setores, não lista; o nome da estrutura recebe TermoOpcoes só se `degrau.termos` for array (senão texto simples); (3) props opcionais extras: `carregando` (hub), `onIrCarteira` (objetivo).

## Known Stubs
Literal "ver todos ›" no hub (OPCOES_ESCADA não tem chave para isso). Sem outros.

## Verificação
- `node web/tests/test_setor_toque.mjs`: verde. `npx vite build`: ok. Parse esbuild dos 3 JSX ok.
- Greps de aceitação: sem hex, sem "watchlist", sem aritmética financeira em ConfirmarEstrutura, sem `store.mcp` no hook.
- Componentes ainda não importados (48-10); build não os exercita além do parse.

## Self-Check: PASSED
- 6 arquivos existem; commits f97ea143, 635c16d3 e 23b9e959 existem; STATE.md/ROADMAP.md intocados.
