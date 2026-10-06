---
phase: 48-opcoes-caminho-b
plan: 09
subsystem: frontend-opcoes
tags: [opcoes, escada, grafico, matriz, acessibilidade]
requires: [48-01, 48-03, 48-08]
provides:
  - web/src/opcoes/GraficoResultado.jsx
  - web/src/opcoes/EscadaObjetivo.jsx
  - web/src/opcoes/MatrizVencimentos.jsx
affects: [48-10]
key-files:
  created:
    - web/src/opcoes/GraficoResultado.jsx
    - web/src/opcoes/EscadaObjetivo.jsx
    - web/src/opcoes/MatrizVencimentos.jsx
requirements-completed: [OPC-04, OPC-05, OPC-06, OPC-13]
metrics:
  completed: 2026-10-05
---

# Phase 48 Plan 09: Tela 3 (escada, gráfico, matriz) Summary

Três componentes isolados da tela 3; nenhum arquivo existente editado (fiação é do 48-10).

## Commits
- aacae129 feat(48-09): GraficoResultado
- 5bed03ed feat(48-09): EscadaObjetivo
- 590614db feat(48-09): MatrizVencimentos

## Entregue
- GraficoResultado: R$ total por padrão + alternância "Por ação" (aria-pressed, 44px); SVG 340x214 responsivo com `role="img"` e `aria-label` do backend; linha tracejada (só ações) e cheia (estrutura); preenchimento pos/neg com a mesma opacidade 0.2; preço médio pontilhado; marcadores r=9 aria-hidden (ausente não desenha); legenda 1-5 com TermoOpcoes, sinal "−" e "(perde)"; ausências explicadas; "E se…?" por índice da grade (range 44px); `<details>` com tabela; sem `transition`; sem subtração/módulo de resultado no front; sem gráfico mostra o motivo na mesma proporção do SVG.
- EscadaObjetivo: voltar, cabeçalho secao_<objetivo> + acao_a, chips de vencimento (3 colunas, 48px), radiogroup roving com setas/Enter/Espaço, barras com `fracao` do backend, degraus ausentes com aria-disabled fora do radiogroup, nota_sem_piso na renda, estados carregando/erro (role=alert)/sem estrutura, botão Comparar com `dados.comparar.rotulo` antes do clique (some ao abrir, vira `renderMatriz()`), cota esgotada, frase de risco aria-live, CTA 48px desabilitado sem `execucao.executavel === true`.
- MatrizVencimentos: grid 3 colunas flexíveis, células 52px aria-pressed, "—" + motivo (aria-disabled), estados carregando/erro/cota, rodapé de frescor com a fonte da própria matriz; sem chamada de rede.

## Deviations from Plan
Nenhuma de regra. Premissas: (1) `colunas[].sinal` do backend é "negativo"/"positivo" (não "neg"/"pos"); (2) id do degrau = `degrau.id ?? degrau.nome`; (3) o backend não envia `execucao.motivo`: o motivo do CTA desabilitado usa `execucao.motivo` se existir, senão `motivoSemGrafico`, senão dado_insuficiente; (4) quando renova a cota: `comparar.cap.reinicia` / `matriz.dados.cap.reinicia`, senão "—" (nada inventado); (5) frescor da matriz: "em dia" só se `frescor.medido === true && bloqueia !== true`, senão "fim de pregão".

## Known Stubs
Nenhum. Componentes ainda não importados (48-10).

## Verificação
- `npx vite build` (web): ok. Parse esbuild dos 3 JSX: ok (build não exercita arquivos não importados).
- Greps de aceitação: role="img", type="range" ==1, `<details` ==1, transition ==0, sem subtração/Math.abs, radiogroup/radio/aria-checked, ArrowUp/Down, comparar.rotulo, sem `2*N+1` literal, sem `store.` na matriz, aria-live: todos conforme.
- Suíte de web/tests não rodada (escopo do executor).

## Self-Check: PASSED
- 3 arquivos existem; commits aacae129, 5bed03ed, 590614db existem; STATE.md/ROADMAP.md intocados.
