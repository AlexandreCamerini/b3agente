---
phase: 39-reestrutura-o-de-navega-o-da-aba-op-es
plan: 04
subsystem: ui
tags: [react, opcoes, navegacao, vigias, adr-027, guardian-test]

# Dependency graph
requires:
  - phase: 39-02
    provides: copy.js (26 chaves), primitivos uiOpcoes.jsx (CarimboFrescor/DetalheInfo/BotaoSaibaMais), VigiasSheet.jsx (VigiasBadge/VigiasSheet), canal one-shot ctx.opcoesAbaInicial/ctx.limparOpcoesAbaInicial/ctx.goOpcoes(aba)
  - phase: 39-03
    provides: CuradoriaEstruturas.jsx com infoBotao/cascata D-11/D-14; OportunidadesOpcoes.jsx com aria-expanded/abertoTicker/infoBotao
provides:
  - OpcoesScreen.jsx reescrito em torno de UM estado (abaOpcoes, 3 valores fixos) substituindo os dois estados ortogonais subaba/abaWorkspace
  - AbaOportunidades.jsx/AbaRecomendadas.jsx (novos) — partição de SecaoDescobrir.jsx (Fase 33), cada aba com o próprio carimbo de frescor
  - PropostaDoAtivo (renomeia/enxuga SubAbaOperar) — painel inline abaixo do carrossel de Oportunidades, sub-aba "Operar" dissolvida (Leitura B')
  - VigiasBadge+VigiasSheet no cabeçalho (visível nas 3 abas) envolvendo SecaoVigias, substituindo o bloco fixo do hub
  - Bastidor (custo/cota, mecânica de lastro) atrás de DetalheInfo (D-14); "saiba mais" fixo do topo substituído por BotaoSaibaMais por aba (D-13)
  - Link inline "Ver outros vencimentos" (compararAberto) expandindo SecaoComparar dentro de Montar (D-06); SecaoSetups migrado para dentro de Montar (fork 2)
  - SecaoDescobrir.jsx e WorkspaceHeader.jsx removidos (zero consumidores restantes)
  - test_opcoes_nav_tres_abas_ui.mjs — guardião novo do NAV-01 (43 asserções), com prova negativa executada
affects: [39-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Estado único de navegação com allowlist validada no inicializador do useState + consumo one-shot num useEffect(..., []) — mesmo padrão que 39-02 estabeleceu no lado do App.jsx, agora do lado consumidor"
    - "Bastidor (custo/mecânica) atrás de disclosure (DetalheInfo) em vez de parágrafo fixo — aplicado a 2 pontos nesta fase (custo do rodapé, mecânica de lastro)"

key-files:
  created:
    - web/src/opcoes/AbaOportunidades.jsx
    - web/src/opcoes/AbaRecomendadas.jsx
    - web/tests/test_opcoes_nav_tres_abas_ui.mjs
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
  deleted:
    - web/src/opcoes/SecaoDescobrir.jsx
    - web/src/opcoes/WorkspaceHeader.jsx

key-decisions:
  - "Fork 1 (Leitura B'): o card de Oportunidades expande um painel inline reusando PropostaLastreada/CandidatoOpcao/useAceiteLastreado verbatim (a sub-aba Operar dissolvida não perde caminho de execução) — decisão já travada no PLAN.md antes da execução, não uma escolha do executor"
  - "Fork 2: SecaoSetups migra para dentro de Montar, abaixo do link de Comparar, sem pill própria — decisão já travada no PLAN.md"
  - "Cascata carregando/erro/vazio/dados só é renderizada dentro da aba Montar (antes rodava para hub e workspace); Oportunidades/Recomendadas não dependem mais dela — consequência direta de D-04, não uma escolha nova"

patterns-established:
  - "Guardião estrutural por fatiamento de ramo (abaOpcoes === \"x\") em vez de por regex solto — usado nas asserções 5/6 do guardião novo para garantir que cada componente só vive no ramo da sua aba"

requirements-completed: [NAV-01]

# Metrics
duration: ~45min
completed: 2026-09-24
---

# Phase 39 Plan 04: Reescrita da navegação — 3 abas fixas, Vigias em sheet, Operar dissolvida Summary

**OpcoesScreen.jsx reescrito em torno de um estado único `abaOpcoes` (3 valores fixos: Oportunidades/Recomendadas/Montar) substituindo os dois estados ortogonais `subaba`/`abaWorkspace`; Vigias sai do hub fixo e vira badge+sheet visível nas 3 abas; a sub-aba "Operar" é dissolvida num painel inline dentro de Oportunidades; bastidor de custo/lastro vai atrás de ⓘ; guardião novo trava o invariante com 43 asserções e prova negativa executada.**

## Performance

- **Duration:** ~45 min
- **Completed:** 2026-09-24T14:36:15-03:00
- **Tasks:** 3/3
- **Files modified:** 1 (OpcoesScreen.jsx) + 2 criados (AbaOportunidades.jsx, AbaRecomendadas.jsx) + 1 guardião criado (test_opcoes_nav_tres_abas_ui.mjs) + 2 deletados (SecaoDescobrir.jsx, WorkspaceHeader.jsx)

## Accomplishments

- `AbaOportunidades.jsx`/`AbaRecomendadas.jsx` (novos): partição de `SecaoDescobrir.jsx` (Fase 33-02) em duas abas independentes — cada uma com seu próprio `CarimboFrescor` (D-04b preservado), sem a frase-ponte `duasLeiturasIntro` (a negação de hierarquia entre os dois motores agora mora em `curadoriaSubtitulo`, Plano 39-02).
- `OpcoesScreen.jsx` reescrito: `ABAS_OPCOES = ["oportunidades", "recomendadas", "montar"]` + `abaOpcoes` validado contra a allowlist no próprio inicializador do `useState` (T-39-14) + consumo one-shot de `ctx.opcoesAbaInicial` num `useEffect(..., [])`; `abaBar` (3 pills fixas, fora de qualquer condicional de `ticker`, D-01); `VigiasBadge` no cabeçalho abrindo `VigiasSheet` com `SecaoVigias` dentro (D-07, SC#2); `PropostaDoAtivo` (renomeia/enxuga `SubAbaOperar`) como painel inline do card de Oportunidades tocado (Leitura B', SC#3); custo/cota (`cp.opcoesCustoFrescor`) e mecânica de lastro (`cp.opcoesLastroAjuda`) atrás de `DetalheInfo` (D-14); "saiba mais" fixo do topo removido, substituído por `infoDaAba(` — 3 chamadas, uma por aba (D-13); "Ver outros vencimentos" vira link inline com `aria-expanded` expandindo `SecaoComparar` dentro de Montar (D-06); `SecaoSetups` migra para dentro de Montar, abaixo do link de Comparar (fork 2).
- `test_opcoes_nav_tres_abas_ui.mjs` (novo): 43 asserções cobrindo os 11 grupos do plano — allowlist/one-shot, ausência de código dos dois estados dissolvidos, geometria da `abaBar`, visibilidade do badge de Vigias, isolamento por ramo de aba, expansão inline de Comparar, ausência do "saiba mais" fixo, bastidor atrás de ⓘ, fonte única de `PropostaDoAtivo`, isolamento ADR-027 e paridade de rótulo (SC#4). Prova negativa executada de verdade (não só descrita): reintroduzir `const [subaba, setSubaba] = useState("setups")` faz o guardião falhar nomeando exatamente o item 2; revertido, volta a passar 43/43.
- `SecaoDescobrir.jsx`/`WorkspaceHeader.jsx` deletados — confirmado por grep que o único consumidor de cada um era `OpcoesScreen.jsx` (menções restantes em outros arquivos são comentários históricos, não imports).

## Task Commits

1. **Task 1: wrappers AbaOportunidades.jsx / AbaRecomendadas.jsx** - `f7ab754` (feat)
2. **Task 2: OpcoesScreen.jsx — estado único, abaBar, badge de Vigias, 3 ramos, PropostaDoAtivo, Montar** - `4b24d6c` (feat)
3. **Task 3: guardião estrutural novo do NAV-01** - `7bba7b7` (test)

**Plan metadata:** (a seguir, commit de docs)

## Files Created/Modified

- `web/src/opcoes/AbaOportunidades.jsx` (novo) - aba 1, motor COM gate de liquidez, carimbo próprio
- `web/src/opcoes/AbaRecomendadas.jsx` (novo) - aba 2, motor SEM gate, execução inline via CuradoriaEstruturas
- `web/src/opcoes/OpcoesScreen.jsx` - reescrito: estado único abaOpcoes, abaBar, VigiasBadge/VigiasSheet, PropostaDoAtivo, Montar consolidado
- `web/src/opcoes/SecaoDescobrir.jsx` (deletado) - dissolvido em AbaOportunidades.jsx/AbaRecomendadas.jsx
- `web/src/opcoes/WorkspaceHeader.jsx` (deletado) - sem consumidor (não há mais "voltar ao hub")
- `web/tests/test_opcoes_nav_tres_abas_ui.mjs` (novo) - guardião estrutural do NAV-01, 43 asserções

## Decisions Made

Ver `key-decisions` no frontmatter. Os dois forks abertos pelo UI-SPEC (destino do card de Oportunidades e local de SecaoSetups) já vinham resolvidos e travados no próprio `39-04-PLAN.md` (`<objective>`), não decididos por este executor — a execução seguiu a Leitura B' e o fork 2 literalmente. A única decisão de implementação genuína do executor foi onde a cascata carregando/erro/vazio/dados passa a viver: só dentro da aba Montar (antes cobria hub+workspace), consequência direta e não-ambígua de D-04 (Oportunidades/Recomendadas não fazem leitura de ticker).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comentário JSX com `*/}` órfão quebrando o build**
- **Found during:** Task 2 (primeira tentativa de `npx vite build`)
- **Issue:** Um bloco de comentário `/* ... */` dentro de um ternário JSX (não um comentário `{/* */}` de filho JSX) acabou com um `}` sobrando no fim (`*/}`), produzindo `Unexpected "}"` no esbuild — erro de sintaxe puro, não uma questão de conteúdo do comentário.
- **Fix:** Removido o `}` órfão, comentário voltou a ser um `/* ... */` plano dentro da expressão.
- **Files modified:** `web/src/opcoes/OpcoesScreen.jsx`
- **Verification:** `npx vite build` (117 módulos, sem erro)
- **Committed in:** `4b24d6c` (Task 2 commit — corrigido antes do commit, não é um commit separado)

**2. [Rule 1 - Bug] Três comentários `{/* ... */}` multi-linha citando identificadores dissolvidos em linhas de continuação sem prefixo `*`**
- **Found during:** Task 2 (verificação da acceptance criteria "fora de comentário, OpcoesScreen.jsx não contém setSubaba/abaWorkspace/SubAbaOperar/workspacePillRow/WorkspaceHeader/SecaoDescobrir/irParaOperar")
- **Issue:** A regra do próprio plano para filtrar comentário (`^\s*//\|^\s*\*\|{/\*`) só reconhece linhas que COMEÇAM com `//`, `*` ou `{/*` — três blocos de comentário JSX multi-linha desta reescrita tinham linhas de continuação em texto plano (sem prefixo `*`) que citavam `SecaoDescobrir.jsx`/`WorkspaceHeader`/`workspacePillRow` ao explicar a decisão (histórico, não código), disparando um falso positivo na verificação.
- **Fix:** Reformatados os 3 blocos para prefixo `*` por linha (estilo já usado no header `/** */` do arquivo) e reescrita levemente a prosa para não repetir o nome do arquivo deletado numa segunda menção (a primeira, no comentário do import, é suficiente e já passa no filtro).
- **Files modified:** `web/src/opcoes/OpcoesScreen.jsx`
- **Verification:** `grep -v "^\s*//\|^\s*\*\|{/\*" ... | grep -n "..."` sai vazio; `npx vite build` continua verde.
- **Committed in:** `4b24d6c` (Task 2 commit)

**3. [Rule 1 - Bug] `grep -c "onIr={irParaVigia}"` contava 2 por causa de uma menção em comentário**
- **Found during:** Task 2 (acceptance criteria `grep -c "onIr={irParaVigia}" == 1`)
- **Issue:** Um comentário citava literalmente `` `onIr={irParaVigia}` `` ao explicar por que o nome da função foi mantido — o `grep -c` (que conta por padrão, sem distinguir comentário) contava a menção em prosa e o uso real como prop, batendo 2 em vez de 1.
- **Fix:** Reescrito o comentário para descrever a mesma decisão sem repetir a forma `onIr={irParaVigia}` literal (fala da prop `onIr` de `SecaoVigias` apontando pra função, sem colar a sintaxe JSX completa).
- **Files modified:** `web/src/opcoes/OpcoesScreen.jsx`
- **Verification:** `grep -c "onIr={irParaVigia}"` volta a 1.
- **Committed in:** `4b24d6c` (Task 2 commit)

**4. [Rule 1 - Bug] Falso positivo do guardião novo em `.manchete` dentro de comentário de proveniência**
- **Found during:** Task 3 (primeira execução de `test_opcoes_nav_tres_abas_ui.mjs`)
- **Issue:** O header de `AbaOportunidades.jsx` explica, em prosa, que o componente é "sem `.manchete` próprio" — o guardião checava `.manchete` no arquivo BRUTO (com comentários), então achava o próprio texto explicativo e reprovava um componente que na verdade não renderiza manchete nenhuma.
- **Fix:** A asserção passou a rodar `semComentario()` (o mesmo helper que o próprio arquivo já usa para as outras checagens) antes de checar `.manchete`.
- **Files modified:** `web/tests/test_opcoes_nav_tres_abas_ui.mjs`
- **Verification:** `node web/tests/test_opcoes_nav_tres_abas_ui.mjs` sai 0, 43/43 `ok`.
- **Committed in:** `7bba7b7` (Task 3 commit — corrigido antes do commit)

---

**Total deviations:** 4 auto-fixed (Rule 1 — todos bugs de sintaxe/verificação descobertos ao rodar o próprio build/guardião do plano, nenhum é mudança de escopo ou de comportamento).
**Impact on plan:** Nenhum. Os quatro são correções mecânicas (sintaxe JS, precisão de regex de guardião) sem efeito no comportamento da tela ou no conteúdo semântico dos comentários preservados.

## Issues Encountered

- `grep -c` conta LINHAS que casam, não ocorrências — mesmo gotcha já documentado nos SUMMARYs de 39-02/39-03. Todas as acceptance criteria deste plano que usam `grep -c` foram verificadas com `grep -n` ao lado para confirmar que a contagem correspondia a usos reais, não a um acidente de linha compartilhada.
- Nenhum bloqueio, nenhuma pergunta de arquitetura (Rule 4) — os dois forks do UI-SPEC já vinham travados no próprio PLAN.md, e a implementação seguiu literal.

## User Setup Required

None - no external service configuration required.

## Known Stubs

Nenhum stub novo introduzido. `PropostaDoAtivo`/`AbaOportunidades`/`AbaRecomendadas` recebem dado real via `ctx`/hooks já existentes (`useOpcoesPropostas`, `ctx.curadoria`) — nenhum componente novo recebe prop vazia/mock fixa.

## Threat Flags

Nenhuma superfície nova fora do `<threat_model>` do plano — todos os 5 threat IDs (T-39-14 a T-39-18) correspondem 1:1 a mudanças efetivamente feitas (allowlist de `abaOpcoes`, ausência de disparo pago em troca de aba/sheet, aceite lastreado inalterado, isolamento ADR-027, allowlist de manchete inalterada).

## Guardiões vermelhos (insumo para o Plano 39-05)

Executado `for t in web/tests/*.mjs; do node "$t" >/dev/null 2>&1 || echo "$t"; done` sobre os 163 arquivos da suíte web. 10 ficaram vermelhos — todos consequência direta e esperada da dissolução de `subaba`/`abaWorkspace`/`SubAbaOperar`/`SecaoDescobrir.jsx`/`WorkspaceHeader.jsx` e da migração de Vigias para sheet (ver `<repo_guardrail>` do 39-04-PLAN.md, que declara esta lista como esperada). Nenhum outro arquivo da suíte quebrou.

| Arquivo | Motivo (1 linha) |
|---|---|
| `test_carteira_opcoes_tira.mjs` | Checa ordem `<SecaoDescobrir` antes de `<SecaoVigias` em OpcoesScreen.jsx — os dois não existem mais nessa forma. |
| `test_curadoria_ui.mjs` | Lê `SecaoDescobrir.jsx` diretamente do disco (`readFileSync`) para localizar o call site de `CuradoriaEstruturas` — arquivo deletado (ENOENT). |
| `test_fase22_componentes_compartilhados.mjs` | Procura `function SubAbaOperar(` em OpcoesScreen.jsx para isolar o componente — renomeado para `PropostaDoAtivo` com assinatura diferente. |
| `test_kb_ancoras.mjs` | Espera o bloco do link "saiba mais" fixo do topo (`color: T.accent, fontWeight: 700, fontSize: "12px"` solto no return) — removido por D-13, virou `infoDaAba(` por aba. |
| `test_opcoes_consolidacao_ui.mjs` | Lê `SecaoDescobrir.jsx` diretamente do disco — arquivo deletado (ENOENT). |
| `test_opcoes_hub_workspace_ui.mjs` | Lê `WorkspaceHeader.jsx` diretamente do disco e testa o split hub×workspace (`hubTopo`/`workspaceTopo`) — ambos dissolvidos por D-01/D-04. |
| `test_opcoes_jornada_ui.mjs` | Lê `WorkspaceHeader.jsx` diretamente do disco (paridade de voz por modo do texto de transição do workspace) — arquivo deletado (ENOENT). |
| `test_opcoes_multi_candidato_ui.mjs` | Testa o ramo multi-candidato dentro de `SubAbaOperar` por nome — hoje vive em `PropostaDoAtivo`, mesma lógica, nome/assinatura diferentes. |
| `test_opcoes_subabas_ui.mjs` | Testa a fatia de `SubAbaOperar` (uso de PropostaLastreada/CandidatoOpcao/useAceiteLastreado, modo por `ctx.operador`) por nome — mesma lógica agora em `PropostaDoAtivo`. |
| `test_opcoes_vigias_ui.mjs` | Espera "bloco de vigias renderizado antes do seletor" (D4, hub fixo) e o padrão textual exato de `irParaVigia` — Vigias agora é sheet (não bloco fixo no fluxo) e `irParaVigia` ganhou uma linha a mais (fechar o sheet antes de navegar). |

Todos os 10 testam uma FORMA de código (nome de função, presença de arquivo, ordem de bloco fixo) que a própria Fase 39 pede para mudar — nenhum aponta uma regressão de comportamento real. O Plano 39-05 deve, para cada um: (a) confirmar se o invariante de fundo que o teste protegia ainda é verdade sob a nova forma (ex.: `PropostaDoAtivo` ainda usa `PropostaLastreada`/`CandidatoOpcao`/`useAceiteLastreado` — confirmado por `test_opcoes_nav_tres_abas_ui.mjs` item 9), e (b) atualizar ou aposentar o guardião com nota datada (nunca apagar sem nota, mesmo padrão de 39-02/39-03).

## Next Phase Readiness

- `OpcoesScreen.jsx` reescrito e verde (`npx vite build`, 117 módulos); guardião novo (`test_opcoes_nav_tres_abas_ui.mjs`, 43/43) trava o invariante de 3 abas fixas para o resto da fase.
- 10 guardiões antigos vermelhos, listados acima com motivo — é o insumo direto que o Plano 39-05 (reconciliação de guardiões) precisa para não precisar rodar a suíte inteira e diagnosticar do zero.
- Nenhuma capacidade de execução perdida: aceite/fechamento lastreado alcançável via painel de Oportunidades (`PropostaDoAtivo`), execução curada inline em Recomendadas (`CuradoriaEstruturas`, inalterada desde o Plano 39-03), execução manual em Montar (`SecaoAnalisar`, inalterada).
- Backend não foi tocado por este plano (nenhum arquivo `server/app/*.py` em `files_modified`).

---
*Phase: 39-reestrutura-o-de-navega-o-da-aba-op-es*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: `web/src/opcoes/AbaOportunidades.jsx`
- FOUND: `web/src/opcoes/AbaRecomendadas.jsx`
- FOUND: `web/tests/test_opcoes_nav_tres_abas_ui.mjs`
- FOUND: `.planning/phases/39-reestrutura-o-de-navega-o-da-aba-op-es/39-04-SUMMARY.md`
- FOUND commit `f7ab754` (Task 1)
- FOUND commit `4b24d6c` (Task 2)
- FOUND commit `7bba7b7` (Task 3)
- CONFIRMED DELETED: `web/src/opcoes/SecaoDescobrir.jsx`, `web/src/opcoes/WorkspaceHeader.jsx`
- `npx vite build`: verde (117 módulos)
- `node web/tests/test_opcoes_nav_tres_abas_ui.mjs`: 43/43 ok
- Suíte web completa (163 arquivos): 153 verdes, 10 vermelhos (listados acima, todos esperados)
