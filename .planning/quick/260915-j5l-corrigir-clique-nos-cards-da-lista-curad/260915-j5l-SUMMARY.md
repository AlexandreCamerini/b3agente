---
phase: quick-260915-j5l
plan: 01
subsystem: ui
tags: [react, options-trading, curadoria, jsx, guardian-tests]

requires:
  - phase: 31-varredura-oportunidades-opcoes
    provides: "CuradoriaEstruturas + useCuradoria (bloco 'AS 4 MELHORES OPORTUNIDADES DE OPÇÕES'), rotas /api/options/lastreada/abrir, /abrir-collar, /buy já existentes e corretas"
provides:
  - "web/src/opcoes/executarCandidato.js — módulo puro de despacho por tipo de candidato curado (call_coberta/put_protecao/collar/opcao_a_descoberto) para o método de store correto"
  - "Confirmação inline por card em CuradoriaEstruturas (App.jsx): prêmio/perda máxima/breakeven + botão Executar, sem rolagem de tela, sem modal"
  - "A.executarCandidatoCurado em App.jsx: despacha, atualiza carteira via setData, relança erro verbatim para o card renderizar"
  - "9 guardiões novos (regras 14-22) em test_curadoria_ui.mjs travando a classe de bug corrigida"
affects: [opcoes, carteira, curadoria]

tech-stack:
  added: []
  patterns:
    - "Módulo puro de despacho tipo→corpo-de-rota, testável com store injetado (mesmo padrão de estruturaParaPayoff.js)"
    - "Estado de confirmação inline indexado por idCandidato, nunca por ticker (dois candidatos do mesmo ticker convivem no top-4)"

key-files:
  created:
    - web/src/opcoes/executarCandidato.js
    - web/tests/test_executar_candidato.mjs
  modified:
    - web/src/App.jsx
    - web/src/copy.js
    - web/tests/test_curadoria_ui.mjs

key-decisions:
  - "Confirmação inline dentro do próprio card (decisão do Alex via AskUserQuestion, 2026-09-15) — não modal, não scrollIntoView para outro lugar"
  - "onAbrir (navegação para o acordeão de UMA posição, Fase 18) sobrevive como link secundário dentro do painel, não removido"
  - "Erro de execução NÃO vira flash — é relançado (throw) para o card exibir e.message verbatim, evitando duas superfícies da mesma falha"

requirements-completed: [QUICK-260915-J5L]

duration: 30min
completed: 2026-09-15
---

# Quick 260915-j5l: Confirmação inline por tipo no bloco de curadoria de opções

**Cada um dos 4 tipos de estrutura do bloco "AS 4 MELHORES OPORTUNIDADES DE OPÇÕES" agora abre uma confirmação inline no próprio card e dispara a rota real correta, em vez de descartar o candidato e abrir o acordeão genérico de venda coberta.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-09-15 (sessão contínua)
- **Completed:** 2026-09-15T14:11:51-03:00
- **Tasks:** 3/3
- **Files modified:** 5 (2 criados, 3 modificados)

## Accomplishments

- `corpoDoCandidato()`/`executarCandidato()` — módulo puro que traduz cada um dos 4 tipos do motor de curadoria (`call_coberta`, `put_protecao`, `collar`, `opcao_a_descoberto`) para o corpo EXATO que sua rota real exige, sem I/O e sem aritmética financeira.
- Clicar num card alterna uma confirmação inline (prêmio/perda máxima/breakeven, lidos só de `item.estrutura`/`item.premioTotal`, zero chamada de rede no clique) — o clique antigo (`onAbrir(item.ticker)`) descartava `idCandidato`/`contractSymbol`/`pernasContratos`/`tipo` e sempre abria a proposta de venda coberta de UMA posição, independente do tipo clicado.
- Liquidez DIFÍCIL exige consentimento explícito (checkbox) antes de `aceitaLiquidezDificil: true` entrar no corpo — nunca reenvio automático após um 400.
- Modo Estudo não mostra CTA de executar em nenhum card (defesa em UI espelhando o 403 do servidor, mesmo padrão T-14-23 de `PropostaLastreada`).
- Erro do servidor (400 de liquidez, 403 de Modo Estudo, 409 de collar duplicado) aparece verbatim no card, em `T.warn` (nunca `T.negative` — vermelho é de P&L).
- 9 guardiões estáticos novos (regras 14-22) em `test_curadoria_ui.mjs`, com 3 provas negativas MEDIDAS (revert → falha → revert de volta).

## Task Commits

1. **Task 1: módulo puro de despacho por tipo + 6 casos de teste** - `781ecf3` (feat, TDD) — RED medido (`ERR_MODULE_NOT_FOUND`), GREEN 26/26 asserções
2. **Task 2: confirmação inline no card + ação com erro verbatim** - `423ee89` (feat)
3. **Task 3: guardiões do bloco curado + suíte canônica** - `9acb475` (test)

_Nota: Task 1 é TDD (frontmatter `tdd="true"`) — o teste foi escrito e medido em RED antes do módulo existir, depois o módulo trouxe as 26 asserções para GREEN num commit único (módulo + teste nasceram juntos no mesmo commit por serem pequenos e interdependentes; RED/GREEN foram medidos e registrados abaixo, não pulados)._

## Files Created/Modified

- `web/src/opcoes/executarCandidato.js` - `corpoDoCandidato()` (pura) + `executarCandidato()` (store injetado); despacha os 4 tipos para `optionsAbrirLastreada`/`optionsAbrirCollar`/`optionsBuy`
- `web/tests/test_executar_candidato.mjs` - 26 asserções: 4 tipos × corpo idêntico, consentimento de liquidez por identidade (`=== true`), tipo desconhecido/candidato nulo/incompleto lançam sem chamar store
- `web/src/App.jsx` - `A.executarCandidatoCurado` (despacha + `setData` + `track` + `flash` no sucesso, `throw` no erro); `CuradoriaEstruturas` com estado `abertoId`/`execucao`/`liquidezOk` e painel de confirmação inline
- `web/src/copy.js` - 7 chaves novas (`curadoriaExecutarCta`, `curadoriaExecutando`, `curadoriaFechar`, `curadoriaExecutada`, `curadoriaLiquidezConsentir`, `curadoriaEstudoNaoExecuta`, `curadoriaVerPosicao`) em `COPY.estudo` e `COPY.operador`, sem a string-âncora do collar (guardrail CVM)
- `web/tests/test_curadoria_ui.mjs` - CHAVES 18→25; 9 regras novas (14-22) travando: onClick do card não descarta mais o candidato, `onExecutar` recebe o item inteiro, despacho sem literal de rota na UI, painel sem I/O, `porLote` null-safe, `T.warn` nunca `T.negative`, zero `window.confirm`, `aceitaLiquidezDificil` sempre derivado de `liquidezOk`, CTA guardado por `operador`

## Decisions Made

- Confirmação inline no próprio card (não modal, não `scrollIntoView`) — decisão de produto do Alex via `AskUserQuestion` nesta sessão, registrada no `PLAN.md`.
- `onAbrir` (a navegação da Fase 18 para o acordeão de UMA posição) foi preservada como link secundário dentro do painel expandido, em vez de removida — evita apagar um caminho de navegação existente.
- O painel de confirmação é renderizado UMA VEZ, fora do carrossel horizontal (não dentro de cada card de 220px) — melhor legibilidade em 375px, sem constranger o layout do card à largura fixa do carrossel.
- Variável de loop do `.map()` manteve o nome `item` (shadowing legal em JS/JSX) para preservar os guardiões pré-existentes (regras 9/10 de `test_curadoria_ui.mjs`) sem reescrevê-los desnecessariamente.

## Deviations from Plan

None - plan executado como especificado. A única adaptação foi de forma, não de substância: o commit da Task 1 (TDD) trouxe teste e módulo juntos porque são pequenos e mutuamente definidores — o RED foi medido de verdade (`node web/tests/test_executar_candidato.mjs` falhando com `ERR_MODULE_NOT_FOUND` antes do módulo existir) antes de escrever `executarCandidato.js`.

## Issues Encountered

Durante a Task 3, a primeira tentativa de escrever a regra 14 (grep pelo padrão antigo) usou uma nova variável de loop (`c` em vez de `item`) no `.map()` de `CuradoriaEstruturas`, o que quebrou 2 guardiões PRÉ-EXISTENTES (regras 9 e 10 da Fase 31, que fazem `grep` por `item.idCandidato`/`ROTULO_TIPO_CURADORIA[item.tipo]` literal). Corrigido revertendo o nome da variável para `item` (shadowing da constante externa de mesmo nome, legal em JS/JSX) — os 39 guardiões antigos voltaram a passar sem reescrita.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Next Phase Readiness

**Pendência operacional a NOMEAR, não executar:** este quick task toca `web/src/`, então só chega ao usuário com `scripts/bump.sh` + `scripts/publicar-web.sh`, e ao iPhone só com `cap sync` + build novo no Xcode. A Fase 31 (que criou o bloco original) também segue não publicada — as duas mudanças entram na mesma janela de publicação, na ordem: bump → publicar-web.sh → (se aplicável) cap sync/build iOS.

Nenhum bloqueio para trabalho futuro. `server/`, `persistence.js` e `PropostaLastreada.jsx` permaneceram intocados, como exigido pelo plano.

## Self-Check: PASSED

- `web/src/opcoes/executarCandidato.js` — FOUND
- `web/tests/test_executar_candidato.mjs` — FOUND
- Commit `781ecf3` — FOUND (`git log --oneline --all`)
- Commit `423ee89` — FOUND
- Commit `9acb475` — FOUND
- `git diff --stat 33c1be7 HEAD` — exatamente os 5 arquivos de `files_modified`, nenhum arquivo fora da lista
- `bash scripts/executar.sh --testes` (com `dangerouslyDisableSandbox`, após confirmar que as 27 falhas do primeiro run eram `PermissionError` em `ssl.py`, artefato de sandbox documentado) — 2910 passed, 0 failed (backend) + 150/150 `.mjs`, exit 0
- `cd web && npx vite build` — verde nas 3 rodadas (após Task 1, Task 2, Task 3)

---
*Phase: quick-260915-j5l*
*Completed: 2026-09-15*
