---
phase: 48-opcoes-caminho-b
plan: 13
subsystem: web-a11y
tags: [opcoes, acessibilidade, guardiao, contraste]
requires: [48-12]
key-files:
  created:
    - web/tests/test_opcoes_caminho_b_ui.mjs
  modified:
    - web/src/entendimento.jsx
    - web/tests/test_entendimento_modulo.mjs
    - web/src/opcoes/ObjetivoAtivo.jsx
    - web/src/opcoes/GraficoResultado.jsx
requirements-completed: [OPC-13, OPC-05, OPC-12]
metrics:
  tasks: 2
  completed: 2026-10-05
---

# Phase 48 Plan 13: acessibilidade do caminho B e guardião transversal Summary

`ConceitoSheet` virou diálogo acessível e um guardião novo (162 asserções `ok`) trava reduced-motion, alvos de toque, radiogroup, gráfico com alternativa em tabela, termos sr-only, ausência de "Watchlist", ausente nunca vira zero, estados obrigatórios, aviso de dinheiro virtual e contraste AA nos 4 pares tema x modo.

## Commits
- Task 1 `8d4b2935`: `feat(48-13): ConceitoSheet acessivel (aria-modal, Esc, foco devolvido)`
- Task 2: `test(48-13): guardiao transversal do caminho B (a11y, estados, contraste)` (inclui as 2 correções de componente abaixo)

## Task 1
`aria-modal="true"` na raiz; `useEffect` guarda `document.activeElement`, foca o painel da folha (`tabIndex -1`; o título carrega assíncrono, por isso o foco vai ao painel e não ao h2) e devolve o foco no cleanup se o elemento ainda está no documento; `keydown` Esc chama `onClose`, listener removido no cleanup (T-48-47). Props e visual inalterados. 3 asserções acrescentadas a `test_entendimento_modulo.mjs` (nenhuma removida).

## Task 2
Guardião `web/tests/test_opcoes_caminho_b_ui.mjs`, com prova negativa no cabeçalho e exercitada em memória. Cobre os 10 itens do plano. Contraste lido do `PALETTE`/`MODE_OPERADOR` de App.jsx (os componentes usam os tokens globais `T`, não `cartaoV6Cores`).

## Deviations from Plan

**1. [Rule 1 - AA] Dois textos em cor de aviso reprovavam no tema claro**
- `ObjetivoAtivo.jsx`: motivo do objetivo indisponível usava `T.warn` sobre bgPanel (4,32:1 claro/estudo, 4,23 operador). Agora `T.textPrimary`; o texto do motivo já carrega o aviso.
- `GraficoResultado.jsx`: rótulo "(perde)" usava `T.negative` (4,40:1 sobre bgBase no claro/operador). Agora `T.textPrimary` + peso 700; o rótulo textual permanece.
- Diff restrito a `web/src/opcoes/`, sem cor nova.

**2. [Interpretação] Escopo do contraste de texto**
Os tokens globais `positive`/`negative`/`warn` medem 4,1 a 4,5:1 sobre bgPanel/bgBase no tema claro (dívida legada do PALETTE, já registrada em `test_estrutura_card_contraste.mjs`; mexer no token viola "Zero cor nova"). Em vez de afrouxar o limite, o guardião: (a) exige >= 4,5 para textPrimary/Secondary/Muted, accent (bgBase e chip sobre tint), warn do selo "atrasado" (bgBase) e onAccent/accent (CTA); (b) trava por regex que `positive`/`negative` nunca são `color:` de texto e que `warn` só é texto no HubOpcoes; (c) exige >= 3,0 de accent/positive/negative/warn como gráfico/borda sobre bgPanel e bgBase; (d) imprime as medidas abaixo de 4,5 como linhas `info`. O preenchimento do gráfico usa `fillOpacity` 0,2 (tinta decorativa; a informação vai pela linha accent, marcadores rotulados, legenda e tabela); por isso mede-se o token cheio >= 3, não o composto a 0,75 como no card v6.

**3. Exceção declarada no item 2 (alvos)**
`<input type="checkbox">` de ConfirmarEstrutura tem `minHeight: 20px`, mas fica dentro de `<label>` com o texto; o guardião exige o `<label>` e dispensa só esse input.

**4. Item 8, "parcial"**
`copy.js` tem as chaves legadas `estado_travadas_parcial`/`extra_resultado_parcial` (não são fill parcial). O guardião proíbe "parcial" nos 7 componentes e chaves de fill parcial (`ordem_parcial`, `fill_parcial`, `parcialmente`) em `opcoesEscada`.

## Verificação
- `node web/tests/test_opcoes_caminho_b_ui.mjs`: OK, 162 `ok(`.
- `test_entendimento_modulo.mjs`, `test_setor_toque.mjs`, todos `test_opcoes_*.mjs` e `test_estrutura_card_contraste.mjs`: verdes.
- `npx vite build` (web): passou.
- Não rodados, conforme o escopo: suíte canônica e `cap copy ios`.

## Known Stubs
Nenhum.

## Self-Check: PASSED
- Arquivos criados/modificados existem; commit 8d4b2935 e o commit da Task 2 existem.
- STATE.md e ROADMAP.md intocados.
