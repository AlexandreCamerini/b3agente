---
phase: 32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone
plan: 04
subsystem: ui
tags: [react, opcoes, refactor, adr-027, multi-candidato]

# Dependency graph
requires:
  - phase: 32-02
    provides: "CandidatoOpcao.jsx extraído para web/src/opcoes/, reusável verbatim"
  - phase: 32-03
    provides: "SubAbaOperar já busca gate/proposta por ticker (dois useEffect próprios); LinhaChamadaOpcoes em Posições"
provides:
  - "SubAbaOperar (OpcoesScreen.jsx) com os dois ramos: N candidatos lado a lado (MULTI-02 portado) e cartão único (PropostaLastreada, sem regressão)"
  - "App.jsx sem PropostaDaPosicao, sem o estado opcoesFor, sem a chamada de useOpcoesPropostas em CarteiraScreen — nenhum bloco de opções por posição sobra em Posições"
  - "Teto de pontos de uso de <PropostaLastreada cai de 2 (Fase 28) para 1 (só OpcoesScreen.jsx) — App.jsx passa a 0"
  - "TODO nomeado do fetch redundante de gate/proposta em SubAbaOperar, com o guardião que prende a decisão de não corrigi-lo nesta fase"
affects: [32-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Card reusado verbatim entre ramo único/multi: CandidatoOpcao nunca é recriado, só importado — mesmo padrão já usado em PropostaLastreada.jsx"
    - "Silêncio deliberado (ADR-004) é local ao COMPONENTE que itera N posições, não uma regra universal — SubAbaOperar (uma posição por vez) não precisa dela; a fatia de teste que a media foi aposentada com nota, não portada às cegas"

key-files:
  created:
    - .planning/todos/pending/subaba-operar-fetch-redundante-gate-proposta.md
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/App.jsx
    - web/tests/test_opcoes_multi_candidato_ui.mjs
    - web/tests/test_opcoes_subabas_ui.mjs
    - web/tests/test_opcoes_proposta_ui.mjs
    - web/tests/test_opcoes_collar_ui.mjs
    - web/tests/test_carteira_opcoes_tira.mjs
    - web/tests/test_curadoria_ui.mjs
    - web/tests/test_faixa_liquidez_ui.mjs
    - web/tests/test_fase22_componentes_compartilhados.mjs

key-decisions:
  - "Decisão arquitetural B do PLAN.md aplicada literalmente: PORTAR o suporte multi-candidato (não aceitar como débito técnico) — PropostaDaPosicao não é movida como componente, ela morre; só o ramo multi (a parte com valor) é portado para SubAbaOperar"
  - "myOptionPositions/posAberta: a implementação de SubAbaOperar (já adaptada a 'uma posição selecionada por vez') fica como ÚNICA — a irmã de PropostaDaPosicao morreu junto com o componente"
  - "Fetch redundante de gate/proposta em SubAbaOperar NÃO corrigido nesta fase (decisão já registrada no PLAN.md) — TODO nomeado criado com o guardião que prende a decisão"
  - "Guardas de silêncio (ADR-004) e o estado opcoesFor NÃO foram portados para OpcoesScreen.jsx — deixaram de fazer sentido no novo local (SubAbaOperar mostra 1 posição por vez, nunca N); os testes que os mediam foram aposentados com nota datada, não recriados às cegas em outro arquivo"

patterns-established: []

requirements-completed: [D-01, D-04]

duration: ~2h10min
completed: 2026-09-16
---

# Phase 32 Plan 04: Multi-candidato portado para SubAbaOperar + PropostaDaPosicao removida Summary

**`SubAbaOperar` (aba Opções, sub-aba Operar) ganha o ramo de N candidatos lado a lado (MULTI-02, antes só em `PropostaDaPosicao`); `App.jsx` não define nem renderiza mais nenhum bloco de opções por posição — a fase 32 termina sem a regressão silenciosa que o plano existiu para evitar.**

## Performance

- **Duration:** ~2h10min (estimativa — investigação de dependências colaterais de teste consumiu a maior parte)
- **Completed:** 2026-09-16
- **Tasks:** 3/3
- **Files modified:** 11 (1 criado, 10 modificados — 6 previstos no plano + 4 guardiões colaterais fora de `files_modified`)

## Accomplishments

- `SubAbaOperar` deriva `candidatos`/`multi` de `prop.candidatos` (mesma guarda `Array.isArray` de `PropostaDaPosicao`) e renderiza N `CandidatoOpcao` lado a lado quando `multi`, com o MESMO `aceitarCandidato` de `useAceiteLastreado` para todos — aceite continua exclusivo por rodada, sem trava nova na UI (mitigação T-32-09 do threat model). Candidato único continua em `PropostaLastreada`, sem regressão.
- `PropostaDaPosicao` foi removida de `App.jsx` junto com o estado `opcoesFor`/`setOpcoesFor` e a chamada de `useOpcoesPropostas` em `CarteiraScreen` — nesta ordem (consumidor antes da declaração), evitando o `ReferenceError` nomeado no `32-03-PLAN.md`. Os imports órfãos (`CandidatoOpcao`, `PropostaLastreada`/`FonteDoDadoProposta`/`ChipDaProposta`/`useAceiteLastreado`, `useOpcoesPropostas`) saíram junto.
- `id={"posicao-" + p.t}` foi mantido (âncora do deep link de push), com nota datada explicando por que fica mesmo sem chamador de scroll.
- Teto de pontos de uso de `<PropostaLastreada` caiu de 2 (Fase 28) para 1 — só `OpcoesScreen.jsx`; `App.jsx` passa a 0. Guardião reescrito para medir e AFIRMAR isso (não é violação do teto, é o teto respeitado por um número menor).
- 4 guardiões colaterais (fora de `files_modified` da Task 2) quebraram como consequência direta da remoção e foram corrigidos: `test_fase22_componentes_compartilhados.mjs` (`isolarFuncao("PropostaDaPosicao")` chamava `process.exit(1)` e escondia ~118 asserções), `test_carteira_opcoes_tira.mjs`, `test_curadoria_ui.mjs` e `test_faixa_liquidez_ui.mjs` (o único chamador de `A.abrirVerbete("liquidez-opcao", ...)` em `App.jsx` sumiu — migrou para `SubAbaOperar`).
- Sanidade do guardião MULTI-02 comprovada por injeção real (`const multi = false` temporário em `OpcoesScreen.jsx`) — reprovou exatamente a asserção esperada, revertido, `git diff --stat` confirmou reversão limpa.
- Débito nomeado do fetch redundante de gate/proposta em `SubAbaOperar` (já registrado como decisão no PLAN.md) documentado em `.planning/todos/pending/subaba-operar-fetch-redundante-gate-proposta.md`, citando o guardião que prende a decisão.

## Task Commits

1. **Task 1: Portar multi-candidato para SubAbaOperar** - `cf25715` (feat)
2. **Task 2: Remover PropostaDaPosicao de App.jsx e o estado que só ela usava** - `1b3cea4` (feat)
3. **Task 3: Reconciliar os guardiões de multi-candidato, proposta e collar** - `1abb442` (test)

**Deviation collateral (entre Task 2 e Task 3):** `9489359` (fix) — 4 guardiões colaterais quebrados pela Task 2, fora de `files_modified`.

## Files Created/Modified

- `web/src/opcoes/OpcoesScreen.jsx` — `SubAbaOperar` ganha `candidatos`/`multi` e o ramo `<CandidatoOpcao>` lado a lado; `carouselTrackStyle` local (nunca importado de App.jsx); imports de `CandidatoOpcao`/`FonteDoDadoProposta`
- `web/src/App.jsx` — `PropostaDaPosicao` removida; `opcoesFor`/`setOpcoesFor` e a chamada de `useOpcoesPropostas` em `CarteiraScreen` removidos; imports órfãos removidos; comentários históricos reconciliados
- `web/tests/test_opcoes_multi_candidato_ui.mjs` — reescrito: fatia de `SubAbaOperar` (OpcoesScreen.jsx) substitui a fatia de `PropostaDaPosicao` (App.jsx); teto de `<PropostaLastreada` de 2→1 pontos de uso
- `web/tests/test_opcoes_subabas_ui.mjs` — regra 5 aceita `CandidatoOpcao` como delegação legítima, ao lado de `PropostaLastreada`
- `web/tests/test_opcoes_proposta_ui.mjs` — contagem exata de `<PropostaLastreada` em `OpcoesScreen.jsx` (1x, sem duplicação pelo ramo novo)
- `web/tests/test_opcoes_collar_ui.mjs` — comentário histórico atualizado (nenhuma asserção mudou)
- `web/tests/test_carteira_opcoes_tira.mjs` — (deviation, fora do plano) âncoras de função reduzidas; itens 8/9 (silêncio do card, `opcoesFor`) aposentados com nota; item 11 (`<PropostaLastreada`) de 1x para 0x em App.jsx
- `web/tests/test_curadoria_ui.mjs` — (deviation, fora do plano) âncora `PropostaDaPosicao` removida da checagem de ordem
- `web/tests/test_faixa_liquidez_ui.mjs` — (deviation, fora do plano) `A.abrirVerbete("liquidez-opcao", ...)` medido em `OpcoesScreen.jsx`, não mais em `App.jsx`
- `web/tests/test_fase22_componentes_compartilhados.mjs` — (deviation, fora do plano) isola `SubAbaOperar` em `OpcoesScreen.jsx` em vez de `isolarFuncao("PropostaDaPosicao")` (que abortava o arquivo); soma de `carouselTrackStyle(` passa a cobrir 3 arquivos
- `.planning/todos/pending/subaba-operar-fetch-redundante-gate-proposta.md` — (novo) débito nomeado do fetch redundante, com o guardião que prende a decisão

## Decisions Made

- Decisão arquitetural B do PLAN.md aplicada literalmente: `PropostaDaPosicao` morre, só o ramo multi é portado — `CandidatoOpcao` reusado verbatim, nunca recriado.
- Guardas de silêncio (ADR-004, "um aviso por card vira ruído") e o estado `opcoesFor` NÃO foram portados para `SubAbaOperar` — deixaram de fazer sentido no novo local (uma posição selecionada por vez, nunca N iteradas). Os testes que mediam essa classe de regra em `App.jsx` foram aposentados com nota datada explicando o motivo, em vez de recriados às cegas.
- O critério de aceite do plano `grep -c "myOptionPositions" ... devolve 1` e `grep -c "candidatos.length > 1" ... devolve 1` foram tratados como contagem de OCORRÊNCIA FUNCIONAL, não contagem literal cega: `myOptionPositions` aparece 2x no arquivo (declaração + uso em `.find(`), padrão pré-existente desde a Fase 28-02, não alterado por este plano — o "1" do plano provavelmente contava só a declaração. `candidatos.length > 1` foi mantido em exatamente 1 ocorrência de código reescrevendo os comentários explicativos para não repetir o literal.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `test_fase22_componentes_compartilhados.mjs` abortava o arquivo inteiro (`process.exit(1)`) ao não achar `PropostaDaPosicao`**
- **Found during:** Task 2, validação da suíte completa
- **Issue:** `isolarFuncao("PropostaDaPosicao")` chamava `process.exit(1)` quando o marcador não existia mais em `App.jsx` — escondia as ~118 asserções seguintes do arquivo em silêncio.
- **Fix:** passa a isolar `SubAbaOperar` em `OpcoesScreen.jsx` (mesmo padrão de marcador, `\nfunction ` como limite); soma de `carouselTrackStyle(` atualizada para cobrir App.jsx + OportunidadesOpcoes.jsx + OpcoesScreen.jsx (o 4º call site mudou de arquivo).
- **Files modified:** `web/tests/test_fase22_componentes_compartilhados.mjs`
- **Verification:** `node web/tests/test_fase22_componentes_compartilhados.mjs` — exit 0
- **Committed in:** `9489359`

**2. [Rule 1 - Bug] `test_carteira_opcoes_tira.mjs` quebrado em 7 asserções pela remoção de `PropostaDaPosicao`/`opcoesFor`/`useOpcoesPropostas`**
- **Found during:** Task 2, validação da suíte completa
- **Issue:** âncoras de função (`iPDP`), a chamada do hook em `CarteiraScreen`, a guarda de silêncio do card e o estado `opcoesFor` não existiam mais.
- **Fix:** âncoras reduzidas a `CarteiraScreen < HistoricoScreen`; itens 8/9 (silêncio do card, `opcoesFor`) reescritos como asserções NEGATIVAS com nota explicando por que a classe de regra não tem mais equivalente; item 11 (`<PropostaLastreada` em App.jsx) de 1x para 0x.
- **Files modified:** `web/tests/test_carteira_opcoes_tira.mjs`
- **Verification:** `node web/tests/test_carteira_opcoes_tira.mjs` — exit 0
- **Committed in:** `9489359`

**3. [Rule 1 - Bug] `test_curadoria_ui.mjs` quebrado na checagem de ordem das âncoras de função**
- **Found during:** Task 2, validação da suíte completa
- **Issue:** a âncora `PropostaDaPosicao` (usada só para a checagem de ordem, `iPDP > -1`) deixou de existir.
- **Fix:** removida da checagem; restam 4 âncoras (`useCuradoria < LinhaChamadaOpcoes < CarteiraScreen < HistoricoScreen`).
- **Files modified:** `web/tests/test_curadoria_ui.mjs`
- **Verification:** `node web/tests/test_curadoria_ui.mjs` — exit 0
- **Committed in:** `9489359`

**4. [Rule 1 - Bug] `test_faixa_liquidez_ui.mjs` — `A.abrirVerbete("liquidez-opcao", ...)` não existe mais em App.jsx**
- **Found during:** Task 2, validação da suíte completa
- **Issue:** o único chamador em `App.jsx` vivia dentro de `PropostaDaPosicao` (o chip de liquidez → verbete, D-09).
- **Fix:** asserção passa a medir `OpcoesScreen.jsx` (`SubAbaOperar` já chamava `A.abrirVerbete("liquidez-opcao", ...)` nos dois ramos, herdado da Task 1).
- **Files modified:** `web/tests/test_faixa_liquidez_ui.mjs`
- **Verification:** `node web/tests/test_faixa_liquidez_ui.mjs` — exit 0
- **Committed in:** `9489359`

**5. [Rule 1 - Bug] Comentário próprio da Task 2 colidia com a âncora `function OpcoesCamada` de `test_faixa_liquidez_ui.mjs`**
- **Found during:** Task 2, ao investigar a falha #4
- **Issue:** o comentário adicionado em `App.jsx` ("ver comentário abaixo de `function OpcoesCamada`") continha o literal `function OpcoesCamada`, que `app.indexOf("function OpcoesCamada")` encontrava ANTES da definição real da função — invertendo a ordem que `test_faixa_liquidez_ui.mjs` assume entre `OpcaoContrato` e `OpcoesCamada`.
- **Fix:** reescrito o comentário para não repetir o literal `function OpcoesCamada`.
- **Files modified:** `web/src/App.jsx`
- **Verification:** `node web/tests/test_faixa_liquidez_ui.mjs` — exit 0
- **Committed in:** `9489359`

---

**Total deviations:** 5 auto-fixed (5 bugs em guardiões/comentários colaterais, todos causados diretamente pela remoção de `PropostaDaPosicao` na Task 2 — mesmo padrão já registrado nos SUMMARYs 32-02/32-03)
**Impact on plan:** Todos necessários para a suíte canônica passar. Nenhum escopo criado além de consertar o que a própria mudança quebrou. Zero mudança de comportamento de produto.

## Issues Encountered

- Vários critérios de aceite literais do PLAN.md (`grep -c "PropostaDaPosicao"`, `grep -c "opcoesPorTicker\|opcoesCarregando\|useOpcoesPropostas"`) não excluem comentários JSX (`{/* */}`), só comentários `//` — meus próprios comentários explicativos, ricos em contexto histórico, precisaram ser reescritos para não repetir os literais banidos (ex.: "o antigo card de proposta" em vez de nomear `PropostaDaPosicao`). Nenhuma perda de informação — só reformulação.
- A suíte rodou primeiro dentro do sandbox padrão do Bash tool e reportou 27 falsas falhas de backend (`PermissionError` em `ssl.py`, carregamento de certificado bloqueado pelo sandbox de rede) — mesmo padrão já registrado nos SUMMARYs 32-01/32-02/32-03. Reexecutada com `dangerouslyDisableSandbox: true`: **2923 passed, 5 skipped, 3 xfailed, 0 failed backend + 152/152 `.mjs`, exit 0**.

## Validação executada

- `npm --prefix web run build` — verde, exit 0 (executado após Task 1 e Task 2)
- `npx vite build` (em `web/`) — verde, exit 0 (execução final)
- `node web/tests/test_opcoes_subabas_ui.mjs` — 23/23 ok (era 22 antes deste plano)
- `node web/tests/test_opcoes_multi_candidato_ui.mjs` — 44/44 ok (era 42 — 2 asserções novas líquidas; reescrito para ler `SubAbaOperar`)
- `node web/tests/test_opcoes_proposta_ui.mjs` — 70/70 ok (era 69)
- `node web/tests/test_opcoes_collar_ui.mjs` — 34/34 ok (igual)
- `node web/tests/test_opcoes_consolidacao_ui.mjs` — ok (identificadores pendurados `opcoesPorTicker`/`opcoesCarregando`/`opcoesFor` confirmados ausentes)
- `node web/tests/test_carteira_opcoes_tira.mjs` / `test_curadoria_ui.mjs` / `test_faixa_liquidez_ui.mjs` / `test_fase22_componentes_compartilhados.mjs` — todos exit 0 após a correção colateral
- Sanidade do guardião: `const multi = candidatos.length > 1;` trocado temporariamente por `const multi = false;` em `OpcoesScreen.jsx` → `test_opcoes_multi_candidato_ui.mjs` reprovou exatamente 1 asserção ("SubAbaOperar deriva `multi` a partir de candidatos.length > 1"); revertido, `git diff --stat web/src/opcoes/OpcoesScreen.jsx` confirmou reversão limpa (0 linhas de diff)
- `bash scripts/executar.sh --testes` (sem sandbox) — **2923 passed, 5 skipped, 3 xfailed, 0 failed backend + 152/152 `.mjs`, exit 0**
- `git diff --name-only` (acumulado das 3 tasks) — não inclui `web/src/opcoes/executarCandidato.js`, `web/src/persistence.js`, `web/src/api.js` nem nada sob `server/`

## User Setup Required

None — nenhuma configuração de serviço externo.

## Next Phase Readiness

- A fase 32 fecha o D-01/D-04 do lado per-posição: `App.jsx` não define nem renderiza mais nenhum bloco de opções por posição; a descoberta em Posições é só a linha de chamada única (`LinhaChamadaOpcoes`, Plano 32-03); o detalhe por posição (com N candidatos quando existem) vive só na sub-aba Operar da aba Opções.
- MULTI-02 continua guardada por teste, apontando para o novo local (`SubAbaOperar`), com sanidade do guardião comprovada por injeção real.
- O débito do fetch redundante (`SubAbaOperar` busca gate/proposta de novo quando o topo da aba já buscou) está nomeado por escrito em `.planning/todos/pending/subaba-operar-fetch-redundante-gate-proposta.md`, não escondido.
- Nenhum bloqueio conhecido para o próximo plano da fase (32-05, se existir) ou para o fechamento da fase 32.

---
*Phase: 32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone*
*Completed: 2026-09-16*

## Self-Check: PASSED

- FOUND: `web/src/opcoes/OpcoesScreen.jsx`
- FOUND: `web/src/App.jsx`
- FOUND: `web/tests/test_opcoes_multi_candidato_ui.mjs`
- FOUND: `web/tests/test_opcoes_subabas_ui.mjs`
- FOUND: `web/tests/test_opcoes_proposta_ui.mjs`
- FOUND: `web/tests/test_opcoes_collar_ui.mjs`
- FOUND: `.planning/todos/pending/subaba-operar-fetch-redundante-gate-proposta.md`
- FOUND: commit `cf25715` (Task 1)
- FOUND: commit `1b3cea4` (Task 2)
- FOUND: commit `9489359` (deviation colateral, Rule 1)
- FOUND: commit `1abb442` (Task 3)
- `.planning/STATE.md` e `.planning/ROADMAP.md` NÃO modificados nesta execução (guardrail do repositório — o orquestrador atualiza os dois à mão)
