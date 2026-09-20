---
phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios
plan: 02
subsystem: ui
tags: [react, refactor, opcoes, guardian-tests, static-analysis, princ-3-4]

# Dependency graph
requires:
  - phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios (plano 33-01)
    provides: "web/src/opcoes/uiOpcoes.jsx (primitivos compartilhados) e o padrão de extração/reapontamento de guardião por diretório, reusados aqui"
provides:
  - "web/src/opcoes/SecaoDescobrir.jsx — job 1 (descobrir oportunidades cross-carteira) extraído: frase-ponte (D-05) + Bloco A (OportunidadesOpcoes) + Bloco B (CuradoriaEstruturas), adjacentes, sem reescrever nenhum dos dois"
  - "D-04b implementado: carimbo de frescor (at/source) nos dois blocos cross-carteira, ramo FRONT-ONLY confirmado por medição direta do backend"
  - "REORG-06: guardrail CVM de manchete generalizado por varredura de diretório, com duas sanidades (contagem mínima + allowlist não envelhecida)"
  - "5 guardiões reapontados/generalizados para a topologia nova, sem afrouxar garantia; 2 asserções novas (REORG-07, princípios 3/4) nascidas de injeção real"
affects: [33-03-secao-setups, 33-04-secao-comparar, 33-05-secao-analisar]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SecaoDescobrir.jsx: componente WRAPPER FINO que compõe dois componentes já extraídos (OportunidadesOpcoes/CuradoriaEstruturas) sem reescrever nenhum — primeiro Secao*.jsx desta fase que compõe, em vez de só mover JSX próprio"
    - "Carimbo de frescor derivado de campo de resposta (at/source), nunca do relógio do cliente — chave comparável 'DD/MM/AAAA HH:mm' → 'AAAA-MM-DD HH:mm' por STRING (sem objeto Date) para achar o mais antigo entre N tickers"
    - "Guardrail CVM por varredura de diretório com allowlist NOMEADA + duas sanidades (contagem mínima do diretório; cada arquivo da allowlist contém .manchete de fato) — evita allowlist que envelhece em silêncio"

key-files:
  created:
    - web/src/opcoes/SecaoDescobrir.jsx
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/copy.js
    - web/tests/test_opcoes_subabas_ui.mjs
    - web/tests/test_opcoes_consolidacao_ui.mjs
    - web/tests/test_curadoria_ui.mjs
    - web/tests/test_carteira_opcoes_tira.mjs
    - web/tests/test_opcoes_mcp_aba_ui.mjs

key-decisions:
  - "D-04b resolvido no ramo FRONT-ONLY (Task 1): /api/options/curadoria (server/app/main.py:3456-3488, meta em 3443-3452) e /api/options/proposta/{ticker} (server/app/main.py:3238-3243) já devolvem at/source; useCuradoria (web/src/App.jsx:4184-4189) e useOpcoesPropostas (web/src/opcoes/useOpcoesPropostas.js:26-78) já preservam os dois até o cliente — zero linha de backend mudou, zero chamada de rede nova"
  - "Carimbo do Bloco A usa o `at` MAIS ANTIGO entre os tickers com proposta concreta (não o mais recente, que esconderia dado velho) e só mostra fonte quando é a MESMA em todos — implementado com laço `for` comum (Object.keys + índice), nunca `.sort(`/`.filter(`, para não disparar a regra REORG-07 nem introduzir reordenação real"
  - "Chave nova de copy (`opcoesConsultadoEmRotulo`) idêntica nos dois modos, mesmo padrão dos vizinhos `opcoesPregaoRotulo`/`opcoesFonteRotulo` (rótulo de dado, não juízo)"
  - "SecaoDescobrir.jsx recebe `curadoria` como o objeto `ctx.curadoria` INTEIRO (não campos desestruturados) — OpcoesScreen.jsx só passa a referência, SecaoDescobrir lê `.top`/`.meta`/`.carregando`/etc. internamente, preservando D-03 (uma fonte, duas leituras) com uma leitura a menos espalhada pelo orquestrador"
  - "3 dos 4 guardiões afetados (test_curadoria_ui.mjs, test_carteira_opcoes_tira.mjs) migraram de 'contagem fixa em OpcoesScreen.jsx' para varredura de DIRETÓRIO — mesma lição do 33-01: um call site que muda de arquivo pela segunda vez em duas fases não deveria exigir reescrita de guardião pela terceira"

patterns-established:
  - "Comentário de proveniência em arquivo `Secao*.jsx` evita citar literalmente 'App.jsx'/'store.'/'api.'/nomes de hook — mesmo cuidado do 33-01, necessário porque scripts de verificação ad hoc fazem substring matching cru sobre o arquivo inteiro, sem diferenciar prosa de código"
  - "Ao mover um JSX comment (`{/* ... */}`) que cita o nome de uma tag JSX nova para perto do call site, checar se algum guardião usa uma versão FRACA de remoção de comentário (só linhas `//`, não blocos `/* */`) — um comentário mencionando `<TagNova` pode inflar contagens 'exatamente 1x' nesses guardiões mais antigos"

requirements-completed: [REORG-01, REORG-02, REORG-03, REORG-04, REORG-05, REORG-06, REORG-07]

duration: unknown (sessão contínua, sem interrupção de rate limit; PLAN_START_TIME não capturado no início real desta execução)
completed: 2026-09-20
---

# Phase 33 Plan 02: Extração de SecaoDescobrir + carimbo de frescor (D-04b) Summary

**Job 1 ("descobrir oportunidades cross-carteira") extraído para SecaoDescobrir.jsx — frase-ponte + Bloco A + Bloco B compostos sem reescrita —, guardrail CVM de manchete generalizado por varredura de diretório (REORG-06), e carimbo de frescor front-only nos dois blocos (D-04b) derivado só de `at`/`source` da resposta.**

## Performance

- **Duration:** não medida com precisão (PLAN_START_TIME não capturado no início real; sessão sem interrupções)
- **Tasks:** 4/4 completas
- **Files modified:** 1 criado + 6 modificados

## Accomplishments

- `web/src/opcoes/SecaoDescobrir.jsx` criado: compõe `<OportunidadesOpcoes>` (Bloco A) e `<CuradoriaEstruturas>` (Bloco B) com a frase-ponte (`cp.duasLeiturasIntro`, D-05) incondicional imediatamente acima do Bloco B — mesmas props que os dois componentes já recebiam, zero reescrita de conteúdo (confirmado por grep: nenhum `store.`/`api.`/hook instanciado/`.manchete` dentro do arquivo novo).
- D-04b implementado: um carimbo de frescor por bloco (motores/respostas diferentes, nunca um carimbo compartilhado), derivado de `at`/`source` — Bloco B lê `curadoria.meta.at`/`.source`; Bloco A calcula o `at` mais antigo entre os tickers com proposta concreta e só mostra fonte quando é a mesma em todos. Campo ausente cai no vocabulário `cp.opcoesFrescorNaoMedido` já existente. Zero chamada de rede nova, zero `Date.now()`.
- `OpcoesScreen.jsx` mais magro: `fraseDuasLeituras`/`blocoOportunidades`/`blocoCuradoria` saíram (junto com os imports de `OportunidadesOpcoes.jsx`/`CuradoriaEstruturas.jsx`); `<SecaoDescobrir ... />` renderiza na mesma posição exata (imediatamente antes de `<SecaoVigias`), passando `curadoria={ctx && ctx.curadoria}` inteiro.
- REORG-06: guardrail CVM de manchete generalizado em `test_opcoes_subabas_ui.mjs` — varredura de `web/src/opcoes/` inteiro, allowlist nomeada de 4 renderizadores (`PropostaLastreada.jsx`, `CandidatoOpcao.jsx`, `CuradoriaEstruturas.jsx`, `OportunidadesOpcoes.jsx`), com as duas sanidades obrigatórias (≥15 arquivos no diretório; cada arquivo da allowlist contém `.manchete` de fato).
- 5 guardiões reapontados/estendidos: `test_opcoes_subabas_ui.mjs` (regra nova REORG-06), `test_opcoes_consolidacao_ui.mjs` (ordem, frase-ponte, D-06, onExecutar 1x, Pitfall 4 por diretório, WR-01, REORG-07, princípios 3/4), `test_curadoria_ui.mjs` e `test_carteira_opcoes_tira.mjs` (call sites de `CuradoriaEstruturas`/`OportunidadesOpcoes` migrados para varredura de diretório), `test_opcoes_mcp_aba_ui.mjs` (chave nova na lista `CHAVES`).
- 5 injeções negativas reais na Task 4, cada uma reprovando o guardião certo (2 delas — REORG-07 e princípios 3/4 — não tinham guardião algum antes; a asserção foi criada, confirmada reprovando, e só então revertida).

## Task Commits

1. **Task 1: Descoberta do frescor (D-04b)** — sem commit (task de medição pura; achado registrado abaixo e no código/comentários do Task 2).
2. **Task 2 + Task 3: Criar SecaoDescobrir.jsx, generalizar guardrail CVM, reapontar 4 guardiões, carimbar frescor** — `20d1818` (feat) — código e guardiões no MESMO commit, por decisão explícita do plano.
3. **Task 4: Provas negativas + baseline** — `032efcb` (test) — as 3 primeiras injeções não deixaram rastro (revertidas, nada para commitar); as injeções 4 e 5 exigiram asserção NOVA (nenhum guardião existente pegava REORG-07/princípios 3-4), commitadas separadamente do código de produção.

**Plan metadata:** este arquivo (SUMMARY) + atualização de STATE.md/ROADMAP.md pelo orquestrador (fora do escopo deste executor, por guardrail do repositório).

## Files Created/Modified

- `web/src/opcoes/SecaoDescobrir.jsx` (novo) — job 1, wrapper fino sobre os dois blocos + carimbo de frescor.
- `web/src/opcoes/OpcoesScreen.jsx` — perde `fraseDuasLeituras`/`blocoOportunidades`/`blocoCuradoria` e os dois imports; ganha `<SecaoDescobrir .../>` passando `curadoria={ctx.curadoria}` inteiro.
- `web/src/copy.js` — chave nova `opcoesConsultadoEmRotulo` nos dois modos (estudo/operador).
- `web/tests/test_opcoes_subabas_ui.mjs` — nova seção (12): guardrail CVM por diretório com allowlist + 2 sanidades.
- `web/tests/test_opcoes_consolidacao_ui.mjs` — regras 1/2/8/9/11/13 reapontadas para a topologia nova; regras 14/15 novas (REORG-07, princípios 3/4).
- `web/tests/test_curadoria_ui.mjs` — call site de `<CuradoriaEstruturas` migrado para varredura de diretório (era contagem fixa em `OpcoesScreen.jsx`); leitura `.top`/`.meta` migrada para `SecaoDescobrir.jsx`; import migrado.
- `web/tests/test_carteira_opcoes_tira.mjs` — item 4: call site de `<OportunidadesOpcoes` migrado para varredura de diretório; par de ordem `{blocoOportunidades}`→`<SecaoVigias` virou `<SecaoDescobrir`→`<SecaoVigias`.
- `web/tests/test_opcoes_mcp_aba_ui.mjs` — `opcoesConsultadoEmRotulo` acrescentada à lista `CHAVES` de paridade entre modos.

## Decisions Made

Ver `key-decisions` no frontmatter. Resumo: D-04b fechado FRONT-ONLY (medição real, sem tocar backend); freshness do Bloco A é o `at` mais antigo do conjunto exibido, com laço `for` comum (não `.sort(`/`.filter(`) para respeitar a letra e o espírito de REORG-07; `curadoria` desce como objeto inteiro para preservar D-03 com um ponto de leitura a menos no orquestrador.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comentário JSX inflava contagem "exatamente 1x" em dois guardiões com remoção de comentário fraca**
- **Found during:** Task 3, ao escrever as novas asserções de `test_curadoria_ui.mjs`/`test_carteira_opcoes_tira.mjs`
- **Issue:** o comentário `{/* ... `<SecaoDescobrir`, um componente só. */}` inserido em `OpcoesScreen.jsx` continha o literal `<SecaoDescobrir` dentro de um bloco `{/* */}`. Dois guardiões (`test_curadoria_ui.mjs`, `test_carteira_opcoes_tira.mjs`) usam uma função `semComentario` que só remove linhas `//`, NÃO blocos `/* */` — o literal no comentário contaria como uma segunda ocorrência da tag em asserções de "exatamente 1x".
- **Fix:** reescrito o comentário para citar "o componente SecaoDescobrir" sem o prefixo `<`, eliminando o falso positivo sem perder a explicação.
- **Files modified:** `web/src/opcoes/OpcoesScreen.jsx`
- **Verification:** `grep -n "<SecaoDescobrir" web/src/opcoes/OpcoesScreen.jsx` confirma exatamente 1 ocorrência (a renderização real); os dois guardiões passam com a contagem correta.
- **Committed in:** `20d1818` (mesmo commit da Task 2/3, achado antes do commit)

**2. [Rule 2 - Missing Critical] Duas asserções que a Task 4 exige criar, porque nenhum guardião existente cobria REORG-07/princípios 3-4 na topologia nova**
- **Found during:** Task 4, injeções 4 e 5
- **Issue:** um `.sort()` sobre `curadoria.top` e uma troca do carimbo por `new Date().toLocaleTimeString()` passavam despercebidos por TODOS os 5 guardiões tocados nesta fase — nenhum tinha regra genérica contra reordenação/relógio do cliente em `SecaoDescobrir.jsx`.
- **Fix:** duas asserções novas em `test_opcoes_consolidacao_ui.mjs` (seções 14 e 15): proíbe `.sort(`/`.reverse(` em `SecaoDescobrir.jsx` (mesmo precedente de `CuradoriaEstruturas.jsx`) e `Date.now()`/`new Date(` em todo `web/src/opcoes/` (varredura de diretório, cobre seções futuras automaticamente).
- **Files modified:** `web/tests/test_opcoes_consolidacao_ui.mjs`
- **Verification:** cada asserção nova, com o defeito injetado, reprovou nomeando exatamente o arquivo; revertido o defeito, guardião voltou a passar (log completo abaixo).
- **Committed in:** `032efcb` (commit dedicado, code + guardião juntos por serem parte da mesma prova negativa)

---

**Total deviations:** 2 auto-fixed (1 Rule 1 — bug de falso-positivo por remoção de comentário fraca; 1 Rule 2 — asserções ausentes que a própria Task 4 do plano mandava criar)
**Impact on plan:** nenhum afrouxamento de garantia; ambos os achados são exatamente o tipo de coisa que a disciplina "censo é piso, suíte completa é quem prova" (33-01) e "injeção real, não descrita" (33-02) existem para pegar.

## Issues Encountered

- `test_ios_assets.mjs` falha na suíte canônica com `ENOENT` para `web/ios/App/App/Assets.xcassets/...` — gap documentado no `CLAUDE.md` do repositório (`web/ios/` gitignored, nasce ausente em worktree novo). Pré-existente, sem relação com `web/src/opcoes/`, fora do escopo desta task. Não corrigido — idêntico à baseline herdada do 33-01.

## Task 1 — Descoberta do frescor (D-04b), respostas com `arquivo:linha`

1. **`GET /api/options/curadoria`** (`server/app/main.py:3456-3488`) devolve `{"top":..., "modo":..., "fonte": "deterministico", "at": now_str(), **meta}` — `at` no nível raiz (linha 3486) e `meta` (construído em `_curadoria_top`, `server/app/main.py:3443-3452`) inclui `"source": source` (derivado em `server/app/main.py:3424-3425`), espalhado para o nível raiz da resposta pelo `**meta`. `useCuradoria` (`web/src/App.jsx:4184-4189`) faz `setMeta(r || null)` com `r` sendo a resposta INTEIRA — logo `ctx.curadoria.meta.at` e `ctx.curadoria.meta.source` chegam ao cliente.

2. **`GET /api/options/proposta/{ticker}`** (`server/app/main.py:3155-3251`) devolve, no bloco de retorno (`server/app/main.py:3238-3243`), `"source": source, "at": now_str()` no nível raiz do objeto. `useOpcoesPropostas` (`web/src/opcoes/useOpcoesPropostas.js:26-78`, especificamente linhas 59-66) guarda `{ gate, proposta }` por ticker, onde `proposta` é a resposta inteira da rota — logo `opcoesPorTicker[t].proposta.at`/`.source` chegam ao cliente, mas SÓ quando `gate.liquida` é verdadeiro e a chamada resolve (senão `proposta: null`, sem `at`/`source`).

3. **Grep em `web/src/copy.js`** por "consultado"/"Consultado": nenhuma chave existente expressa "consultado em `<hora>`". As chaves de frescor vizinhas mais próximas são `opcoesPregaoRotulo`/`opcoesFonteRotulo`/`opcoesFrescorNaoMedido` (`web/src/copy.js:112-116` e `805-809`, idênticas nos dois modos). Chave nova necessária: `opcoesConsultadoEmRotulo`, adicionada nos DOIS ramos (`web/src/copy.js`, próximo às vizinhas de frescor).

**Ramo escolhido: FRONT-ONLY.** Nenhuma linha de backend mudou, nenhum consumo novo de `mydata_budget`, nenhuma chamada de rede nova — as duas rotas já devolviam `at`/`source` e os dois hooks já preservavam os dois campos até o cliente antes desta fase.

## Negative-Proof Log (Task 4)

Guardião que passa não prova que guarda. Cada defeito abaixo foi injetado À MÃO em `web/src/opcoes/SecaoDescobrir.jsx`, o guardião correspondente rodado sozinho, a saída real conferida, e o arquivo revertido com `git checkout --` (confirmado `git diff --stat`/`git status --porcelain` limpos depois de cada um).

**1. `.manchete` renderizado dentro de `SecaoDescobrir.jsx` (prova de REORG-06)**
- Injeção: `<div>{curadoria && curadoria.top && curadoria.top[0] && curadoria.top[0].manchete}</div>` logo após o carimbo do Bloco A.
- Comando: `node web/tests/test_opcoes_subabas_ui.mjs`
- Saída real: `FALHOU nenhum arquivo de web/src/opcoes/ FORA da allowlist renderiza manchete (REORG-06) (violam: SecaoDescobrir.jsx)` — nomeia o arquivo certo.
- Antes desta fase, o mesmo defeito passaria calado: o guardião só olhava `SubAbaOperar`.
- Revert: `git checkout -- web/src/opcoes/SecaoDescobrir.jsx`; guardião volta a passar (17 arquivos no diretório, allowlist intacta).

**2. Frase-ponte virou toggle colapsável (D-05)**
- Injeção: `<p onClick={() => {}} aria-expanded={false} ...>` no lugar do `<p>` incondicional da frase-ponte.
- Comando: `node web/tests/test_opcoes_consolidacao_ui.mjs`
- Saída real: `FALHOU o trecho da frase-ponte NÃO tem aria-expanded (nunca colapsável)` + `FALHOU o trecho da frase-ponte NÃO tem onClick (não é toggle)` — as duas asserções da regra 2 reprovam.
- Revert: `git checkout -- web/src/opcoes/SecaoDescobrir.jsx`; guardião volta a passar.

**3. Frase-ponte movida para DEPOIS do Bloco B (Pitfall 2: adjacência, não existência)**
- Injeção: reordenado o JSX para `Bloco A → Bloco B → frase-ponte` (a frase continua existindo, incondicional, mas não mais adjacente ao Bloco B na posição correta).
- Comando: `node web/tests/test_opcoes_consolidacao_ui.mjs`
- Saída real: `FALHOU ordem em SecaoDescobrir.jsx: duasLeiturasIntro < <OportunidadesOpcoes < <CuradoriaEstruturas` + `FALHOU a montagem de cp.duasLeiturasIntro foi localizada em SecaoDescobrir.jsx` (efeito colateral esperado: o cálculo do trecho de declaração depende da mesma ordem).
- Revert: `git checkout -- web/src/opcoes/SecaoDescobrir.jsx`; guardião volta a passar.

**4. `.sort()` sobre `curadoria.top` antes de repassar ao Bloco B (REORG-07)**
- Injeção: `top={((curadoria && curadoria.top) || []).slice().sort((a, b) => (b.razao || 0) - (a.razao || 0))}`.
- Rodados TODOS os guardiões tocados nesta fase (`test_opcoes_consolidacao_ui.mjs`, `test_curadoria_ui.mjs`, `test_opcoes_subabas_ui.mjs`, `test_carteira_opcoes_tira.mjs`) ANTES de criar a asserção — nenhum reprovou (confirma o achado exigido pelo passo 4 da task: "se nenhum guardião reprovar, criar a asserção").
- Asserção nova criada em `test_opcoes_consolidacao_ui.mjs` (seção 14): `SecaoDescobrir.jsx NÃO usa .sort(/.reverse( no corpo`.
- Comando: `node web/tests/test_opcoes_consolidacao_ui.mjs`
- Saída real (com a asserção já criada e o defeito ainda presente): `FALHOU SecaoDescobrir.jsx NÃO usa .sort( no corpo`.
- Revert: `git checkout -- web/src/opcoes/SecaoDescobrir.jsx`; guardião (já com a asserção nova) volta a passar.

**5. Carimbo trocado por `new Date().toLocaleTimeString()` (princípios 3/4)**
- Injeção: substituído `at` por `new Date().toLocaleTimeString()` na montagem do texto de `CarimboFrescor`.
- Rodados TODOS os guardiões tocados nesta fase ANTES de criar a asserção — nenhum reprovou.
- Asserção nova criada em `test_opcoes_consolidacao_ui.mjs` (seção 15): varredura de diretório proibindo `Date.now()`/`new Date(` em qualquer arquivo de `web/src/opcoes/`.
- Comando: `node web/tests/test_opcoes_consolidacao_ui.mjs`
- Saída real: `FALHOU nenhum arquivo de web/src/opcoes/ usa Date.now()/new Date( como fonte de carimbo (violam: SecaoDescobrir.jsx)`.
- Revert: `git checkout -- web/src/opcoes/SecaoDescobrir.jsx`; guardião (já com a asserção nova) volta a passar.

Nenhuma injeção foi vácua — as 5 reprovaram nomeando exatamente a asserção esperada; as injeções 4 e 5 produziram asserção nova por não haver guardião algum cobrindo o defeito antes.

## Baseline da suíte canônica (saída deste plano, entrada do 33-03)

Rodado fora do sandbox padrão (`dangerouslyDisableSandbox: true`) porque o sandbox interno reprova `pytest` com `PermissionError` de SSL ao carregar `certifi` — achado conhecido e documentado (memória do projeto: "sandbox mente"), não uma falha real.

- **pytest:** 2923 passed, 5 skipped, 3 xfailed, 0 failed — idêntico à baseline herdada do 33-01.
- **`.mjs`:** 151 OK + 1 falha pré-existente (`test_ios_assets.mjs`, `ENOENT` por `web/ios/` ausente neste worktree — gap documentado no CLAUDE.md, fora do escopo) = 152 arquivos, mesma contagem da baseline do 33-01.
- **`npx vite build`:** verde nas duas rodadas (após a Task 2 e após a Task 4/commit final).

Estes números (2923 pytest / 152 `.mjs`, 1 falha ambiental conhecida e não-regressiva) são a baseline de entrada declarada para o plano 33-03.

## Next Phase Readiness

- Padrão de wrapper fino (compor dois componentes já extraídos, sem reescrever) demonstrado pela primeira vez nesta fase — reusável se `SecaoSetups`/`SecaoComparar`/`SecaoAnalisar` precisarem compor mais de um sub-componente.
- Padrão de varredura de diretório para call site que muda de arquivo (aplicado a `<CuradoriaEstruturas`/`<OportunidadesOpcoes`) está pronto para ser reaplicado se algum desses dois componentes migrar de arquivo de novo numa fase futura.
- `App.jsx` intocado (`git diff --stat web/src/App.jsx` vazio, confirmado antes do commit) — REORG-04 preservado.
- Nenhum bloqueio conhecido para o 33-03 (`SecaoSetups`).

## Self-Check: PASSED

- `web/src/opcoes/SecaoDescobrir.jsx` — FOUND
- `web/src/opcoes/OpcoesScreen.jsx` (modificado) — FOUND
- Commit `20d1818` (feat: SecaoDescobrir + guardrail CVM + guardiões) — FOUND in `git log`
- Commit `032efcb` (test: REORG-07 + princípios 3/4) — FOUND in `git log`

---
*Phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios*
*Plan: 02*
*Completed: 2026-09-20*
