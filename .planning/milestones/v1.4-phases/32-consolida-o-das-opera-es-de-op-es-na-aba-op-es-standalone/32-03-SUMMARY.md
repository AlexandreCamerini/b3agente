---
phase: 32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone
plan: 03
subsystem: ui
tags: [react, opcoes, refactor, adr-027, consolidacao]

# Dependency graph
requires:
  - phase: 32-01
    provides: "9 chaves novas de copy (duasLeiturasIntro, tiraOpcoesSubtitulo, curadoriaErroBusca*, linhaChamadaOpcoes*) nos dois modos"
  - phase: 32-02
    provides: "OportunidadesOpcoes.jsx/CuradoriaEstruturas.jsx/CandidatoOpcao.jsx extraídos para web/src/opcoes/; useCuradoria sobe para App() com ctx.curadoria/ctx.goOpcoes"
provides:
  - "Os dois blocos cross-carteira (OportunidadesOpcoes/CuradoriaEstruturas) migrados para o topo da sub-aba Setups da aba Opções, com frase-ponte obrigatória (D-05) entre eles"
  - "LinhaChamadaOpcoes: linha única em Posições com os 4 estados (erro/carregando/vazia/n), contagem exclusiva de ctx.curadoria.top.length (D-03)"
  - "useOpcoesPropostas.js: hook extraído para módulo, consumido por CarteiraScreen e OpcoesScreen.jsx (dois chamadores, mesma função)"
  - "CuradoriaEstruturas.jsx passa a exibir o estado de erro de busca (precedência sobre 'vazio'), corrigindo violação do princípio 4 do CLAUDE.md"
  - "Guardião novo test_opcoes_consolidacao_ui.mjs (32 asserções) travando a consolidação"
affects: [32-04, 32-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hook cross-tela extraído para módulo terceiro (ADR-027 Emenda 3) com `store` por parâmetro — mesmo padrão de useOpcoesMcp(store, ticker)"
    - "Precedência de estado: erro > carregando > vazio > dados, sempre nesta ordem, em todo bloco que lê um resultado de busca best-effort"
    - "Linha de chamada discreta (sem card, sem borda) como substituto de bloco cross-carteira quando o destino é outra tela, nunca um resumo local"

key-files:
  created:
    - web/src/opcoes/useOpcoesPropostas.js
    - web/tests/test_opcoes_consolidacao_ui.mjs
  modified:
    - web/src/App.jsx
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/opcoes/OportunidadesOpcoes.jsx
    - web/src/opcoes/CuradoriaEstruturas.jsx
    - web/tests/test_curadoria_ui.mjs
    - web/tests/test_carteira_opcoes_tira.mjs
    - web/tests/test_opcoes_subabas_ui.mjs
    - web/tests/test_opcoes_multi_candidato_ui.mjs

key-decisions:
  - "opcoesPorTicker/opcoesCarregando/opcoesFor sobrevivem em CarteiraScreen (App.jsx) até o Plano 32-04 — PropostaDaPosicao ainda os consome; a armadilha de ReferenceError nomeada no PLAN.md foi evitada por desenho (a definição do hook sai, a chamada fica)"
  - "CarteiraScreen deixou de desestruturar ctx.curadoria (sem consumidor local depois da migração dos blocos) — passa o objeto inteiro como prop para LinhaChamadaOpcoes; OpcoesScreen.jsx lê o MESMO objeto via blocoCuradoria. Duas leituras, uma fonte (D-03)"
  - "id={'posicao-' + p.t} no card de posição NÃO foi removido (fora do escopo declarado da task) — fica órfão até alguém precisar dele de novo ou decidir removê-lo; não quebra nada"

patterns-established:
  - "Guardião dedicado por fase de consolidação (test_opcoes_consolidacao_ui.mjs), com teste de sanidade próprio (injeção de aria-expanded, revertida) provando que o guardião reprova o que ele diz reprovar"

requirements-completed: [D-01, D-02, D-03, D-04, D-05, D-06, D-07]

duration: ~1h50min
completed: 2026-09-16
---

# Phase 32 Plan 03: Migração dos blocos cross-carteira para a aba Opções + linha de chamada em Posições Summary

**Os dois blocos cross-carteira (motor COM gate / motor SEM gate) saem de Posições e passam a abrir no topo da sub-aba Setups da aba Opções, com a frase-ponte obrigatória entre eles (D-05); Posições fica com uma linha de chamada única cuja contagem vem exclusivamente de `ctx.curadoria.top.length` (D-03), e o estado de erro da curadoria deixa de se disfarçar de "nada elegível".**

## Performance

- **Duration:** ~1h50min (estimativa — PLAN_START_EPOCH não foi capturado no início desta execução)
- **Completed:** 2026-09-16
- **Tasks:** 3/3
- **Files modified:** 10 (2 criados, 8 modificados — 9 previstos no plano + 1 guardião colateral fora de `files_modified`)

## Accomplishments

- `useOpcoesPropostas` virou módulo (`web/src/opcoes/useOpcoesPropostas.js`), com `store` recebido por parâmetro (padrão de `useOpcoesMcp`) e guarda nova para `store` ausente — consumido agora por DOIS chamadores (`CarteiraScreen` e `OpcoesScreen.jsx`) sem reimplementação.
- A sub-aba Setups da aba Opções abre mostrando, nesta ordem: cabeçalho → frase-ponte (`duasLeiturasIntro`, sempre no DOM, nunca colapsável, D-05) → Bloco A (`OportunidadesOpcoes`, motor COM gate, com subtítulo novo `tiraOpcoesSubtitulo`) → Bloco B (`CuradoriaEstruturas`, motor SEM gate) → vigias → seletor.
- `CuradoriaEstruturas.jsx` passa a ler `erro` com precedência sobre o ramo vazio — a busca que falha não afirma mais "nenhuma estrutura elegível" (correção do achado do UI-SPEC, princípio 4 do CLAUDE.md), com botão "Tentar de novo" (`onRecarregar`) e recarga automática após execução bem-sucedida.
- `irParaOperar` (guarda igual a `irParaVigia`: `escolherTicker` é toggle) substitui o `abrirOpcoesDe`/`scrollIntoView` que dependia de um elemento `#posicao-<t>` que só existe em `CarteiraScreen` (Pitfall 4 do 32-RESEARCH.md) — "ver posição" agora navega para a sub-aba Operar dentro da própria aba Opções.
- `LinhaChamadaOpcoes` (novo componente em `App.jsx`) substitui os dois blocos em Posições: um único `<button>` com os 4 estados (erro/carregando/vazia/n≥1), nunca mostra número no estado de erro, contagem lida exclusivamente de `ctx.curadoria.top.length` — a mesma fonte que alimenta o Bloco B em Opções (D-03).
- Guardião novo `test_opcoes_consolidacao_ui.mjs` (32 asserções, teto mínimo do plano era 12) trava: ordem dos 4 blocos, frase-ponte incondicional, ausência dos dois blocos cross-carteira em `App.jsx`, origem única da contagem, navegação sem deep-link, D-06 (sem sticky/fixed/input), a cadeia de execução do collar curado intacta, o estado de erro do Bloco B, o Pitfall 4 (sem scrollIntoView/âncora "posicao-") e identificador pendurado em `App.jsx`. Sanidade do guardião comprovada por injeção real de `aria-expanded` na frase-ponte (reprovou, revertido).

## Task Commits

1. **Task 1: useOpcoesPropostas vira módulo e a aba Opções monta frase-ponte + Bloco A + Bloco B** - `a77d61c` (feat)
2. **Task 2: Posições perde os dois blocos e ganha a linha de chamada única** - `ec271f2` (feat)
3. **Task 3: Guardiões de âncora de USO + guardião novo da consolidação** - `3154df9` (test)

## Files Created/Modified

- `web/src/opcoes/useOpcoesPropostas.js` — hook extraído de `App.jsx`, `store` por parâmetro, guarda de `store` ausente
- `web/src/opcoes/OportunidadesOpcoes.jsx` — ganha subtítulo (`tiraOpcoesSubtitulo`, D-05)
- `web/src/opcoes/CuradoriaEstruturas.jsx` — lê `erro` com precedência sobre vazio; `onRecarregar` chamado após execução bem-sucedida e pelo CTA de erro
- `web/src/opcoes/OpcoesScreen.jsx` — monta `fraseDuasLeituras`/`blocoOportunidades`/`blocoCuradoria` no topo da sub-aba Setups; `irParaOperar` substitui o scroll
- `web/src/App.jsx` — `LinhaChamadaOpcoes` novo; `CarteiraScreen` perde os dois blocos e `abrirOpcoesDe`; chamada de `useOpcoesPropostas` sobrevive (consumida por `PropostaDaPosicao`, sai só no 32-04)
- `web/tests/test_curadoria_ui.mjs` — âncoras de USO migram para `OpcoesScreen.jsx`; regra de `CarteiraScreen` atualizada (não desestrutura mais `ctx.curadoria`)
- `web/tests/test_carteira_opcoes_tira.mjs` — idem para `OportunidadesOpcoes`; regra de scroll-to-id invertida (não existe mais)
- `web/tests/test_opcoes_subabas_ui.mjs` — regra de isolamento (nenhum módulo de `web/src/opcoes/` importa `App.jsx`) estendida por varredura de diretório
- `web/tests/test_opcoes_multi_candidato_ui.mjs` — (deviation, fora do plano) âncora `function useOpcoesPropostas` corrigida para `function useCuradoria`
- `web/tests/test_opcoes_consolidacao_ui.mjs` — (novo) guardião dedicado da consolidação, 32 asserções

## Decisions Made

- `CarteiraScreen` passou a passar `ctx.curadoria` inteiro como prop para `LinhaChamadaOpcoes`, em vez de desestruturar campo a campo (o consumidor local dos campos individuais — o painel `CuradoriaEstruturas` — migrou para `OpcoesScreen.jsx`). D-03 continua provado: as duas telas leem o MESMO objeto, nunca uma segunda instância do hook.
- `id={"posicao-" + p.t}` no card de posição em `CarteiraScreen` não foi removido — está fora do escopo literal desta task (o plano só mandava remover `abrirOpcoesDe`, não a âncora que ele consumia) e não tem custo de manutenção real ficando órfão.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `test_opcoes_multi_candidato_ui.mjs` quebrado pela remoção de `function useOpcoesPropostas` de `App.jsx`**
- **Found during:** Task 3, validação da suíte canônica completa (`bash scripts/executar.sh --testes`)
- **Issue:** `test_opcoes_multi_candidato_ui.mjs` (guardião da Fase 19/MULTI-02, fora dos `files_modified` deste plano) usava `app.indexOf("function useOpcoesPropostas")` como limite de fatia de `PropostaDaPosicao` (`fatiaPDP`). A Task 1 moveu a DEFINIÇÃO do hook para o módulo — a âncora passou a devolver `-1`, produzindo `fatiaPDP = ""` (vazio, não ausência de conteúdo) e mascarando 3 asserções por vacuidade (`PropostaDaPosicao continua renderizando PropostaLastreada...`, `CandidatoOpcao é renderizado com onAceitar=...`, `PropostaDaPosicao consome o hook useAceiteLastreado(...)`), além de uma 4ª que checava a âncora diretamente.
- **Fix:** limite de fatia trocado para `function useCuradoria` (a próxima função declarada em `App.jsx` depois de `PropostaDaPosicao`, desde a Fase 32-02); adicionada asserção de "parse mudo" (`fatiaPDP.length > 100`) para que uma regressão futura do mesmo tipo falhe explicitamente em vez de passar por vacuidade; adicionada asserção de que `function useOpcoesPropostas` NÃO existe mais em `App.jsx`.
- **Files modified:** `web/tests/test_opcoes_multi_candidato_ui.mjs`
- **Verification:** `node web/tests/test_opcoes_multi_candidato_ui.mjs` — 34/34 ok (era mascarado, agora mede de verdade)
- **Committed in:** `3154df9` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug em guardião colateral, causado diretamente pela extração da Task 1 — mesmo padrão já registrado no 32-02-SUMMARY para outros dois guardiões)
**Impact on plan:** Necessário para a suíte canônica passar; nenhum escopo criado além de consertar o que a própria mudança quebrou (e de fortalecer o guardião contra vacuidade futura). Zero mudança de comportamento de produto.

## Issues Encountered

- Dois comentários pré-existentes (não escritos nesta task) mencionavam em prosa os literais `T.negative` (em `CuradoriaEstruturas.jsx`, dentro de um bloco JSX `{/* ... */}`, não filtrado pela higiene `^\s*\/\//` de `test_curadoria_ui.mjs`) e `scrollIntoView`/`"posicao-"` (idem) — o guardião novo (`test_opcoes_consolidacao_ui.mjs`) inicialmente reprovava por causa deles. Corrigido reescrevendo o próprio comentário adicionado nesta task (evitando o literal proibido) e estendendo `semComentario()` do guardião novo para remover blocos `{/* ... */}` também, não só linhas `//` — mesmo padrão já usado em `test_opcoes_subabas_ui.mjs`.
- Durante a investigação de um dos itens acima, um `git stash push -u` foi executado por engano (violação do protocolo do ambiente, que proíbe `git stash` em qualquer forma neste worktree por causa da pilha compartilhada entre sessões). Recuperado imediatamente e corretamente: a entrada foi identificada pelo SHA exato (`git stash list --format='%H %gs'`), restaurada com `git stash apply <sha>` (nunca `pop`), conferida por `git status --short` e pelo conteúdo dos arquivos, e só então descartada com `git stash drop stash@{0}` — sem tocar na outra entrada da pilha (de uma sessão diferente, tag `pre-gateway-20260723-110454`). Nenhum trabalho foi perdido; nenhum comando destrutivo adicional foi executado. Registrado aqui por transparência, não porque tenha causado dano.
- A suíte rodou primeiro dentro do sandbox padrão do Bash tool e reportou 27 falsas falhas de backend (`PermissionError` em `ssl.py`, carregamento de certificado bloqueado pelo sandbox de rede) — nenhuma delas em código tocado por este plano (que só mexeu em `web/`). Mesmo padrão já registrado nos SUMMARYs de 32-01/32-02. Reexecutada com `dangerouslyDisableSandbox: true`: **2923 passed, 5 skipped, 3 xfailed, 0 failed + 152/152 `.mjs`, exit 0**.

## Validação executada

- `npm --prefix web run build` — verde, exit 0 (executado após cada task)
- `npx vite build` (em `web/`) — verde, exit 0 (execução final)
- `node web/tests/test_curadoria_ui.mjs` — 81/81 ok (era 76 antes deste plano — herdado do 32-02)
- `node web/tests/test_carteira_opcoes_tira.mjs` — 50/50 ok (era 43 antes deste plano)
- `node web/tests/test_opcoes_subabas_ui.mjs` — sem regressão, regra de isolamento estendida
- `node web/tests/test_opcoes_multi_candidato_ui.mjs` — 34/34 ok (corrigido, ver Deviations)
- `node web/tests/test_opcoes_consolidacao_ui.mjs` — 32/32 ok (guardião novo)
- `node web/tests/test_opcoes_consolidacao_ui.mjs` com `aria-expanded` injetado na frase-ponte — reprovou (sanidade do guardião confirmada), revertido, `git diff --stat` confirmou reversão limpa
- `bash scripts/executar.sh --testes` (sem sandbox) — **2923 passed, 5 skipped, 3 xfailed, 0 failed backend + 152/152 `.mjs`, exit 0**
- `ls web/tests/*.mjs | wc -l` — 152 (era 151 no início deste plano; +1 guardião novo, nenhum arquivo deletado)
- `git diff --name-only` (acumulado das 3 tasks) — não lista `web/src/opcoes/executarCandidato.js`, `web/src/persistence.js`, `web/src/api.js` nem nada sob `server/`

## User Setup Required

None — nenhuma configuração de serviço externo.

## Next Phase Readiness

- A cadeia de dados que o Plano 32-04 precisa já está pronta: `opcoesPorTicker`/`opcoesFor` continuam declarados em `CarteiraScreen` (consumidos só por `PropostaDaPosicao` agora) — o 32-04 remove essa CHAMADA junto com o último consumidor, ao portar multi-candidato para `SubAbaOperar` e aposentar `PropostaDaPosicao`.
- `id={"posicao-" + p.t}` ficou órfão em `CarteiraScreen` (nenhum chamador consome mais) — não bloqueia o 32-04; decisão de remover ou não fica para quem tocar esse trecho depois.
- `test_opcoes_multi_candidato_ui.mjs` precisará de outra rodada de edição no 32-04 (quando `PropostaDaPosicao` morrer de vez) — já está com a âncora correta (`function useCuradoria`) e sem vacuidade, então a próxima edição parte de uma base medindo de verdade.
- Nenhum bloqueio conhecido para o 32-04.

---
*Phase: 32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone*
*Completed: 2026-09-16*

## Self-Check: PASSED

- FOUND: `web/src/opcoes/useOpcoesPropostas.js`
- FOUND: `web/tests/test_opcoes_consolidacao_ui.mjs`
- FOUND: `.planning/phases/32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone/32-03-SUMMARY.md`
- FOUND: commit `a77d61c` (Task 1)
- FOUND: commit `ec271f2` (Task 2)
- FOUND: commit `3154df9` (Task 3)
- `.planning/STATE.md` e `.planning/ROADMAP.md` não modificados nesta execução (guardrail do repositório — o orquestrador atualiza os dois à mão)
