---
phase: 48-opcoes-caminho-b
plan: 10
subsystem: web-opcoes
tags: [opcoes, navegacao, fiacao, guardioes, ssr-smoke]
requires: [48-03, 48-05, 48-06, 48-07, 48-08, 48-09, 48-11]
provides:
  - OpcoesScreen.jsx religado no fluxo hub -> objetivo -> escada -> confirmar (+ montar)
  - test_opcoes_fluxo_render.mjs (guardião de contrato em runtime, SSR)
  - 5 guardiões de navegação reancorados (+ test_kb_ancoras)
key-files:
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/opcoes/useEscada.js
    - web/tests/test_opcoes_nav_tres_abas_ui.mjs
    - web/tests/test_opcoes_subabas_ui.mjs
    - web/tests/test_opcoes_jornada_ui.mjs
    - web/tests/test_opcoes_continuidade_ui.mjs
    - web/tests/test_opcoes_hub_workspace_ui.mjs
    - web/tests/test_kb_ancoras.mjs
  created:
    - web/tests/test_opcoes_fluxo_render.mjs
requirements-completed: [OPC-01, OPC-02, OPC-04, OPC-06, OPC-07, OPC-12]
metrics:
  tasks: 2 (+ 2 commits de contrato/correção)
  completed: 2026-10-05
---

# Phase 48 Plan 10: fiação do caminho B em OpcoesScreen Summary

A aba Opções agora é um fluxo em profundidade num estado único `nav` (navOpcoes.js): hub com cards da carteira, objetivo, escada (com matriz paga só em clique), confirmar e "Montar do zero" (o Montar antigo, intacto). Vigias saíram do badge do cabeçalho e viraram a seção Atenção do hub + "ver todos" no sheet existente.

## Commits
- 01320035 feat(48-10): religa OpcoesScreen no fluxo em profundidade
- f6546c47 test(48-10): guardião de contrato em runtime do fluxo (SSR)
- 65f33267 test(48-10): reancora os 5 guardiões de navegação (+ test_kb_ancoras)
- a9e5b085 fix(48-10): horário de reinício da cota chega à escada/matriz; fixtures com formato real do backend

## Entregue
- `nav` substitui `ticker`/`abaOpcoes`/`oportunidadeAberta`; `ABAS_OPCOES` segue allowlist de deep-link (T-48-36); one-shots em `useEffect([])`; write-back de memória `memoriaOpcoes(nav.ticker, montar|oportunidades)` sem cleanup.
- `useEscada` (1x) ativo nos níveis objetivo/escada/confirmar; `useTecnicoCarteira` só no hub; matriz só por `abrirMatriz` (handler de clique); nenhum `store.mcp*` novo na tela.
- Célula da matriz sem degrau selecionável: `lerCelula` (custo zero) e a leitura aparece no lugar do degrau, com CTA desabilitado (`execucao.executavel` false + motivo do backend).
- Confirmar: `onExecutar -> ctx.A.executarCandidatoCurado(cand, {aceitaLiquidezDificil, origem:"escada"})` (48-11 já despacha o toast); `onConcluido` volta ao hub.
- "Encerrar estrutura…" abre o objetivo do ativo com `PropostaDoAtivo` como `estruturaAberta`; `goOpcoes('montar')` abre Montar do zero.
- Foco no título ao trocar de nível; transição via `transicaoTela(reduzido())`.

## Contratos verificados contra o backend real (não só fixtures)
- `execucao` de `opcoes_escada` (tipo/contractSymbol/expiration/contratos/qtyAcoes/idCandidato/pernasContratos) casa com `executarCandidato.js`; `TIPO_DO_OBJETIVO` = put_protecao/call_coberta/collar (todos tratados).
- Células de `celulas_da_cadeia` trazem `id`, `pernas` (tipo/lado/strike/premio/contrato), `total`, `motivo` — formato aceito por `/escada/leitura`.
- `HubOpcoes` lê `pos.ticker`; a carteira traz `t` -> mapeado em `carteiraHub` (sem isso os cards renderizariam "undefined").

## Deviations from Plan
1. **[Rule 1 - Bug] `useEscada.lerCelula` não repassava `indice`/`precoObjeto`/`vencimentosExecutaveis`.** A rota aceita os três; sem `indice` caía no degrau 0 (rótulo errado). Editei `web/src/opcoes/useEscada.js` (fora de `files_modified`). Commit 01320035.
2. **[Rule 1 - Bug] Horário de reinício da cota vinha em `erro.detail.reinicia`, os componentes liam `erro.reinicia`/`cap.reinicia`** -> mostrariam "—". Normalizado em OpcoesScreen (`erroDaMatriz`/`matrizView` + `comparar.cap`), sem editar componentes. Commit a9e5b085.
3. **[Rule 3] `test_kb_ancoras.mjs` reancorado** (fora de `files_modified`, mas ancorava `infoDaAba(` 3x; agora 1x, só o ⓘ do Montar). Nota datada no arquivo.
4. **Arquivo novo `web/tests/test_opcoes_fluxo_render.mjs`** (não listado): SSR (react-dom/server + `_jsx_loader`) dos 5 componentes e da `OpcoesScreen` real com o formato do backend; cobre hub/objetivo/escada/matriz/confirmar, Montar via deep-link, "Encerrar estrutura…" (exige `PropostaDoAtivo` visível) e `abrirTicker` fora da carteira (cai no hub).
5. **`onConcluido` não recarrega propostas**: `useOpcoesPropostas` não tem reload e o hub deriva a estrutura aberta de `ctx.data.optionPositions` (atualizado por `setData` em `executarCandidatoCurado`). `nome` da estrutura no card do hub = símbolos das pernas abertas (nada inventado).
6. Removidos os imports de `AbaOportunidades`/`AbaRecomendadas`/`VigiasBadge` (arquivos permanecem em disco; os guardiões que os ancoram são do 48-12).

## Mudança de comportamento (dizer claramente)
Ao sair da aba e voltar, `estadoInicialOpcoes` só restaura o ticker lembrado quando a memória aponta para "montar". Objetivo/escada/confirmar NÃO são lembrados (voltam ao hub). Isso é mais estreito que a leitura do rótulo B7 reancorado ("ticker restaurado só se estiver na carteira") sugere.

## Guardiões reancorados (contagem de `ok(` antes -> depois)
| Guardião | antes | depois |
|---|---|---|
| test_opcoes_nav_tres_abas_ui | 39 | 41 |
| test_opcoes_subabas_ui | 30 | 32 |
| test_opcoes_jornada_ui | 54 | 61 |
| test_opcoes_continuidade_ui | 48 | 54 |
| test_opcoes_hub_workspace_ui | 41 | 43 |
Todos com bloco "REANCORAGEM — Fase 48 (2026-10-05)", asserções trocadas ganham o sufixo "(reancorado 2026-10-05)"; nenhum `ok(` removido sem substituto. Invariantes mantidas: custo só em clique, universo = carteira, travessão em vez de zero, manchete (`.manchete`) fora dos componentes novos, isolamento ADR-027 (agora cobre também os componentes novos).

## Verificação
- `npx vite build` (web): ok.
- Verdes: os 5 guardiões, test_opcoes_nav_profundidade, test_opcoes_custo_declarado, test_opcoes_fluxo_render, test_kb_ancoras, test_tour_opcoes, test_telas_registro, test_api_parity.
- Greps de aceite do Task 1: `estadoInicialOpcoes(` = 2 (>=1); `useEscada(` = 1; `setAbaOpcoes|setOportunidadeAberta` fora de comentário = 0; componentes novos = 5 (>=5); `<SecaoVigias` = 1; `<SecaoAnalisar` = 1; `executarCandidatoCurado(cand` = 2.
- Não rodados (fora do escopo): suíte canônica completa, `cap copy ios`.

## Guardiões vermelhos remanescentes (escopo do 48-12)
Todos só por texto de âncora; nenhuma invariante afrouxada.
- test_opcoes_universo_carteira (3): inicializador lazy do ticker (`tickerInicialOpcoes` em OpcoesScreen), existência de `setTicker` fora de efeito, toggle de `escolherTicker` (agora `setNav`). As asserções "universo = carteira" seguem verdes.
- test_opcoes_vigias_ui (4): `<VigiasBadge` renderizado / antes do seletor / sem depender de ticker; "navegar não é alternar (irParaMontar)". Neste último o comportamento é preservado (guarda `t !== n.ticker` em `irParaMontar`); só o texto da âncora mudou.
- test_opcoes_consolidacao_ui (4): ramos `abaOpcoes === "oportunidades"/"recomendadas"`, `<AbaOportunidades`/`<AbaRecomendadas` exclusivos, `curadoria={ctx && ctx.curadoria}` para AbaRecomendadas.
- test_curadoria_ui (2): `<VigiasBadge` antes do 1º ramo de aba; `curadoria={ctx.curadoria}` em AbaRecomendadas.
- test_carteira_opcoes_tira (1): `<VigiasBadge` usado antes do 1º ramo de aba.
- test_opcoes_abrir_ticker (2): import de `abrirTickerOpcoes` na tela e `oportunidadeAberta` com inicializador lazy (agora via `estadoInicialOpcoes`; o comportamento está coberto em test_opcoes_fluxo_render e test_opcoes_nav_profundidade).
- test_opcoes_abertas_e_motivos (1): `optionPositions=` passado ao `<AbaOportunidades`.

## Known Stubs
Nenhum. Literal "ver todos ›" do hub é herdado do 48-08.

## Self-Check: PASSED
- Arquivos criados/modificados existem; commits 01320035, f6546c47, 65f33267, a9e5b085 existem; STATE.md e ROADMAP.md intocados.
- Guardiões vermelhos acima são os explicitamente atribuídos ao 48-12 (não tornam o self-check FAILED).
