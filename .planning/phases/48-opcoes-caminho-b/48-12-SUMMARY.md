---
phase: 48-opcoes-caminho-b
plan: 12
subsystem: web-tests
tags: [opcoes, guardioes, reancoragem]
requires: [48-10]
key-files:
  modified:
    - web/tests/test_opcoes_universo_carteira.mjs
    - web/tests/test_opcoes_abrir_ticker.mjs
    - web/tests/test_opcoes_vigias_ui.mjs
    - web/tests/test_opcoes_consolidacao_ui.mjs
    - web/tests/test_curadoria_ui.mjs
    - web/tests/test_carteira_opcoes_tira.mjs
    - web/tests/test_opcoes_abertas_e_motivos.mjs
requirements-completed: [OPC-12]
metrics:
  tasks: 2
  completed: 2026-10-05
---

# Phase 48 Plan 12: reancoragem dos guardiões de Opções Summary

Os 7 guardiões que o 48-10 deixou vermelhos por texto de âncora voltaram a verde. Só o texto da âncora mudou; nenhuma invariante foi afrouxada e nenhum `ok(` foi removido sem substituto. Nenhum arquivo de `web/src` foi alterado, porque nenhuma invariante real estava quebrada. Todos os arquivos têm o bloco "REANCORAGEM — Fase 48 (2026-10-05)" no topo e o texto original preservado.

## Commits
- Task 1 (universo, deep-link, vigias): `test(48-12): reancora universo, deep-link e vigias ao fluxo do caminho B`
- Task 2 (curadoria, tira, abertas, consolidação): `test(48-12): reancora curadoria, tira da carteira e estruturas abertas ao fluxo do caminho B`

## Tabela de reancoragem
| Guardião | Âncora antiga | Âncora nova | ok( antes -> depois |
|---|---|---|---|
| test_opcoes_universo_carteira (3) | `useState(() => tickerInicialOpcoes(...))`; `setTicker(` fora de efeito; toggle `setTicker(t === ticker ? "" : t)` | `useState(() => estadoInicialOpcoes({... carteira}))` + `const ticker = nav.ticker`; `setNav(` fora de efeito; toggle `t === n.ticker ? {...n, ticker: ""}`. Extras: nenhum useEffect chama `setNav` com `carteira[0]`; watchlist proibida em HubOpcoes/ObjetivoAtivo/EscadaObjetivo; `navOpcoes.js` só usa `tickerInicialOpcoes(memoria, carteira)` | 37 -> 40 |
| test_opcoes_vigias_ui (4) | `<VigiasBadge` renderizado, antes do seletor, sem ticker; `irParaMontar` com `escolherTicker` | `<HubOpcoes` no ramo `nav.nivel === "hub"` (seção Atenção), antes do seletor do Montar e sem ticker; `custoAtualizar={CUSTO_DA_ACAO.listarVigias}` + `onVerTodosVigias` abre o sheet; `irParaMontar` via `setNav(irMontar(...abrirAtivo))` | 51 -> 52 |
| test_opcoes_abrir_ticker (2) | import de `abrirTickerOpcoes` na tela; `oportunidadeAberta` lazy | `estadoInicialOpcoes({abrirTicker, carteira})` na tela; `navOpcoes.js` importa `abrirTickerOpcoes`; comportamento (na carteira -> objetivo, fora -> hub); `PropostaDoAtivo` como `estruturaAberta` | 16 -> 19 |
| test_opcoes_consolidacao_ui (4) | ramos `abaOpcoes === "oportunidades"/"recomendadas"`, exclusividade das abas, `curadoria={ctx && ctx.curadoria}` | ramo hub localizado; 0 ramos de aba e 0 call sites `<AbaOportunidades`/`<AbaRecomendadas` na tela; exclusividade provada nos próprios arquivos de aba; sem `useCuradoria(` nem `curadoria.top/.meta` na tela | 43 -> 44 |
| test_curadoria_ui (2) | `<VigiasBadge` antes do 1º ramo de aba; `curadoria={ctx.curadoria}` | `<HubOpcoes` no ramo hub antes do Montar, sem ramo de aba; sem 2ª instância/leitura de curadoria na tela | 121 -> 121 |
| test_carteira_opcoes_tira (1) | `<VigiasBadge` antes do 1º ramo de aba | mesma âncora do hub | 51 -> 51 |
| test_opcoes_abertas_e_motivos (1) | `optionPositions=` em `<AbaOportunidades` | `ctx.data.optionPositions` -> `opcoesPorTicker` do HubOpcoes; `PropostaDoAtivo` como `estruturaAberta` do ObjetivoAtivo só com perna aberta (a asserção de AbaOportunidades.jsx segue intacta) | 34 -> 35 |

## Verificação
- Todos os `web/tests/test_opcoes_*.mjs`, test_curadoria_ui, test_carteira_opcoes_tira, test_kb_ancoras, test_telas_registro, test_tour_opcoes e test_api_parity estão verdes.
- A varredura de todo guardião que lê `OpcoesScreen` não deixou nenhum vermelho; nenhum arquivo fora dos 7 precisou de edição.
- `npx vite build` (web) passou.
- Não rodados, conforme o escopo: a suíte canônica completa e `cap copy ios`.

## Deviations from Plan
Nenhuma estrutural. Os arquivos do `files_modified` que não estavam vermelhos (test_opcoes_nav_primitivos_ui, test_kb_ancoras) não foram tocados.

## Pontos para o orquestrador
- `ctx.curadoria` não chega mais a `OpcoesScreen` (0 call sites de `AbaRecomendadas`/`CuradoriaEstruturas` na tela). Os guardiões foram reancorados para 0 call sites, como o plano permite. A UI-SPEC prevê "Destacadas" na escada, mas não há `destac*` em EscadaObjetivo, HubOpcoes ou ObjetivoAtivo. Vale conferir se isso é perda de função ou decisão consciente do 48-08/48-10. `LinhaChamadaOpcoes` na Carteira ainda usa a curadoria.
- Falso-verde do guardião de vigias: o hub só renderiza vigias no nível "hub"; no objetivo/escada eles ficam acessíveis só via voltar. Isso é consistente com o desenho do 48-10.

## Known Stubs
Nenhum.

## Self-Check: PASSED
- Os 7 arquivos existem e contêm "REANCORAGEM — Fase 48 (2026-10-05)".
- Os 2 commits existem.
- STATE.md e ROADMAP.md intocados.
