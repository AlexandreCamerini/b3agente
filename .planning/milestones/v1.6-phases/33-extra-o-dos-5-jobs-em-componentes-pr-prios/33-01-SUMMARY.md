---
phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios
plan: 01
subsystem: ui
tags: [react, refactor, opcoes, guardian-tests, static-analysis]

# Dependency graph
requires:
  - phase: 32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone
    provides: "OpcoesScreen.jsx com os 5 jobs numa rolagem única, padrão de extração ADR-027 Emenda 3 (OportunidadesOpcoes.jsx/CuradoriaEstruturas.jsx)"
provides:
  - "web/src/opcoes/SecaoVigias.jsx — job 2 (gerenciar vigias) extraído como componente props-in/callback-out"
  - "web/src/opcoes/uiOpcoes.jsx — módulo de primitivos compartilhados (Kicker/Aviso/ErroDoMcp/RecusaCobrada), base reusável para 33-02..33-05"
  - "6 guardiões reapontados para a fonte nova, sem afrouxar nenhuma garantia"
  - "1 guardião adicional (test_opcoes_custo_declarado.mjs) corrigido — achado ao rodar a suíte, fora do censo por palavra-chave"
affects: [33-02-secao-descobrir, 33-03-secao-setups, 33-04-secao-comparar, 33-05-secao-analisar]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "uiOpcoes.jsx: primitivos de UI compartilhados entre orquestrador e seções job-to-be-done, sem import de App.jsx nem OpcoesScreen.jsx (ADR-027 Emenda 3)"
    - "Secao*.jsx recebe tudo por prop (dado + callback), nunca chama useOpcoesMcp/store.* diretamente — só o orquestrador instancia o hook"

key-files:
  created:
    - web/src/opcoes/SecaoVigias.jsx
    - web/src/opcoes/uiOpcoes.jsx
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/tests/test_opcoes_vigias_ui.mjs
    - web/tests/test_opcoes_subabas_ui.mjs
    - web/tests/test_opcoes_analisar_ui.mjs
    - web/tests/test_opcoes_consolidacao_ui.mjs
    - web/tests/test_carteira_opcoes_tira.mjs
    - web/tests/test_curadoria_ui.mjs
    - web/tests/test_opcoes_custo_declarado.mjs

key-decisions:
  - "SecaoVigias.jsx recebe exatamente as 10 props literais do PLAN.md (vigias/vigiasVivos/atualizarVigias/listaDeVigias/temEstado/tickersEmCarteira/ticker/onIr/custos/cp) — listaDeVigias/temEstado/tickersEmCarteira continuam DERIVADOS em OpcoesScreen.jsx, nunca recalculados na seção"
  - "custos desce como prop genérica (custos={CUSTO_DA_ACAO}), nunca CUSTO_DA_ACAO importado dentro do componente novo — SecaoVigias.jsx não conhece a tabela, só a chave que usa"
  - "test_opcoes_custo_declarado.mjs entrou no escopo desta task como achado tardio: não bateu no grep de palavras-chave do censo (só cita 'listarVigias', não 'atualizarVigias'/'blocoVigias'/etc.), só apareceu ao rodar a suíte completa"

patterns-established:
  - "Guardião de arquivo migrado: ao mover um bloco/const para arquivo novo, reler o guardião ANTES de editar, trocar a FONTE lida (não só o texto buscado), manter a checagem `>= 0` antes de qualquer fatiamento, e nunca deletar/afrouxar a asserção original"

requirements-completed: [REORG-01, REORG-02, REORG-03, REORG-05]

duration: unknown (sessão interrompida por rate limit e retomada; PLAN_START_TIME não foi capturado no início real da execução)
completed: 2026-09-20
---

# Phase 33 Plan 01: Extração de SecaoVigias e uiOpcoes Summary

**Job 2 ("gerenciar vigias") extraído de OpcoesScreen.jsx para SecaoVigias.jsx, com uiOpcoes.jsx nascendo como módulo compartilhado de Kicker/Aviso/ErroDoMcp/RecusaCobrada — 6 guardiões reapontados para a fonte nova, mais 1 achado tardio corrigido, sem afrouxar nenhuma garantia.**

## Performance

- **Duration:** não medida com precisão (a sessão foi interrompida por rate limit no meio da Task 2/3 e retomada por handoff do orquestrador; o trabalho de código não foi perdido, confirmado por `git status` antes de retomar)
- **Tasks:** 3/3 completas
- **Files modified:** 2 criados + 8 modificados (7 planejados + 1 achado)

## Accomplishments

- `web/src/opcoes/SecaoVigias.jsx` criado: job 2 como componente próprio, props-in/callback-out, zero `store.*`/`useOpcoesMcp`/`useState` (confirmado por grep, REORG-03).
- `web/src/opcoes/uiOpcoes.jsx` criado: `Kicker`/`Aviso`/`ErroDoMcp`/`RecusaCobrada` movidos VERBATIM de `OpcoesScreen.jsx`, uma implementação só reusada pelas duas fontes e por todas as seções futuras (33-02..33-05).
- `OpcoesScreen.jsx` mais magro: `blocoVigias`, `CartaoDeVigia`, `Kicker`, `Aviso`, `ErroDoMcp`, `RecusaCobrada` saíram; `<SecaoVigias .../>` renderiza na mesma posição exata da árvore (depois de `{blocoCuradoria}`, antes de `{carteira.length > 0 ? seletor : null}`).
- 6 guardiões reapontados para a fonte nova (5 do CONTEXT.md + `test_curadoria_ui.mjs`, achado do censo do plano): `test_opcoes_vigias_ui.mjs`, `test_opcoes_subabas_ui.mjs`, `test_opcoes_analisar_ui.mjs`, `test_opcoes_consolidacao_ui.mjs`, `test_carteira_opcoes_tira.mjs`, `test_curadoria_ui.mjs`.
- 1 guardião adicional corrigido como achado TARDIO desta sessão: `test_opcoes_custo_declarado.mjs` — não apareceu no grep de palavras-chave do censo (`blocoVigias|CartaoDeVigia|opcoesVigiasTitulo|atualizarVigias|ErroDoMcp|RecusaCobrada|const BOTAO`), só quebrou ao rodar a suíte canônica completa, porque referencia `listarVigias` sem nenhuma dessas palavras-chave.
- 4 provas negativas reais executadas na Task 3, cada uma reprovando o guardião certo, revertida e reconfirmada verde.
- `App.jsx` intocado (`git diff --stat web/src/App.jsx` vazio) — REORG-04 preservado.

## Task Commits

1. **Task 1+2: Criar uiOpcoes.jsx/SecaoVigias.jsx, religar OpcoesScreen.jsx, reapontar os 6 guardiões** — `b72ab44` (refactor) — código e guardiões no MESMO commit, por decisão explícita do plano (Pitfall 3: guardião reescrito depois é guardião que passou um intervalo inerte).
2. **Fix intermediário (Rule 1 — bug de digitação)** — `dd954e2` (fix) — "não não" duplicado no header de proveniência de `SecaoVigias.jsx`, achado antes das provas negativas da Task 3. Sem efeito de runtime.
3. **Task 3: Provas negativas + baseline** — nenhum commit (task de verificação pura: cada defeito foi injetado, confirmado, e revertido com `git checkout --`; `git status` limpo ao final, nada para commitar).

**Plan metadata:** este arquivo (SUMMARY) + atualização de STATE.md/ROADMAP.md pelo orquestrador (fora do escopo deste executor, por guardrail do repositório).

## Files Created/Modified

- `web/src/opcoes/SecaoVigias.jsx` (novo) — job 2, componente próprio.
- `web/src/opcoes/uiOpcoes.jsx` (novo) — primitivos compartilhados.
- `web/src/opcoes/OpcoesScreen.jsx` — perde `blocoVigias`/`CartaoDeVigia`/`Kicker`/`Aviso`/`ErroDoMcp`/`RecusaCobrada`, ganha os dois imports novos e `<SecaoVigias .../>`.
- `web/tests/test_opcoes_vigias_ui.mjs` — guardião mais afetado (o dono do bloco), reapontado seção a seção com nota datada.
- `web/tests/test_opcoes_subabas_ui.mjs` — regra 11 (`blocoVigias` → `<SecaoVigias`).
- `web/tests/test_opcoes_analisar_ui.mjs` — allowlist `ARQUIVOS` virou varredura de diretório (`readdirSync`, sanity `>= 14`); `ErroDoMcp`/`RecusaCobrada` passam a ser lidos de `uiOpcoes.jsx`.
- `web/tests/test_opcoes_consolidacao_ui.mjs` — regras 1/8, marcador `{blocoVigias}` → `<SecaoVigias`.
- `web/tests/test_carteira_opcoes_tira.mjs` — item 4, mesmo marcador.
- `web/tests/test_curadoria_ui.mjs` — mesmo marcador, terceira ocorrência.
- `web/tests/test_opcoes_custo_declarado.mjs` — achado tardio: lê `SecaoVigias.jsx` além de `OpcoesScreen.jsx`/`CriarSetup.jsx`; `declara()` ganhou a terceira forma `custos.<chave>`, ao lado de `CUSTO_DA_ACAO.<chave>` e do literal entre aspas.

## Decisions Made

- **Props exatas de `SecaoVigias`**: seguidas literalmente do texto da Task 1 do PLAN.md (10 props nomeadas), não da lista um pouco diferente sugerida em `33-PATTERNS.md` (que era orientação de planejamento, mais genérica) — o PLAN.md é a fonte de maior precisão para o executor.
- **`custos` como prop genérica**: `SecaoVigias.jsx` nunca importa `CUSTO_DA_ACAO` — recebe o valor resolvido (`custos={CUSTO_DA_ACAO}`) e lê `custos.listarVigias` dentro do botão. Preserva REORG-03 (seção não lê tabela/estado do orquestrador diretamente) e ainda garante fonte única do número.
- **Comentários evitando texto que o guardião trataria como código real**: os headers de proveniência descrevem a regra de isolamento ("não importa o núcleo do app") em vez de citar `App.jsx` literalmente, porque o verify script do Task 1 e o guardião de diretório fazem `grep`/regex cru sobre substring, sem diferenciar prosa de import de verdade quando o texto NÃO está dentro de um comentário reconhecido pelo `semComentario` do arquivo de teste correspondente (caso do verify script ad-hoc da Task 1, que lê o arquivo bruto). Onde o guardião real já usa `semComentario` (ex.: `test_opcoes_vigias_ui.mjs`), a menção em comentário é segura e foi mantida.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] "não não" duplicado no header de `SecaoVigias.jsx`**
- **Found during:** revisão antes da Task 3 (prova negativa)
- **Issue:** uma reescrita de comentário durante a Task 1 deixou "Recebe TUDO por prop; não\nnão lê o estado bruto..." — palavra duplicada, sem efeito de runtime, mas comentário incorreto.
- **Fix:** removida a duplicação, texto corrigido para "Recebe TUDO por prop; não lê o estado bruto...".
- **Files modified:** `web/src/opcoes/SecaoVigias.jsx`
- **Commit:** `dd954e2`

**2. [Rule 3 - Blocking] `test_opcoes_custo_declarado.mjs` quebrado por migração de arquivo, fora do censo do plano**
- **Found during:** Task 2, ao rodar `bash scripts/executar.sh --testes` pela primeira vez após o commit do refactor
- **Issue:** o guardião lia só `OpcoesScreen.jsx`/`CriarSetup.jsx` procurando a linha que declara o custo de `listarVigias` via `CUSTO_DA_ACAO.listarVigias` ou o literal `"listarVigias"` entre aspas. A extração moveu essa linha para `SecaoVigias.jsx`, onde ela lê `custos.listarVigias` (prop, não constante) — nenhuma das duas formas antigas batia. O grep de palavras-chave do censo do plano (`blocoVigias|CartaoDeVigia|opcoesVigiasTitulo|atualizarVigias|ErroDoMcp|RecusaCobrada|const BOTAO`) não pegou este arquivo porque ele só cita `listarVigias`, nenhuma das outras strings.
- **Fix:** o guardião passou a ler também `SecaoVigias.jsx`, e a função `declara(chave)` ganhou uma terceira forma aceita (`custos.<chave>`), ao lado das duas que já existiam (`CUSTO_DA_ACAO.<chave>` e o literal entre aspas). A garantia não afrouxou: ainda exige que ALGUMA das três formas aponte para a chave nomeada, nunca um número solto.
- **Files modified:** `web/tests/test_opcoes_custo_declarado.mjs`
- **Verification:** `node web/tests/test_opcoes_custo_declarado.mjs` — todos os testes passam; suíte canônica completa confirmou nenhum outro guardião afetado pelo mesmo padrão.
- **Committed in:** `b72ab44` (mesmo commit da Task 2, já que era um guardião afetado pela mesma extração)

---

**Total deviations:** 2 auto-fixed (1 Rule 1 — bug de digitação em comentário; 1 Rule 3 — guardião bloqueado por migração de arquivo não coberta pelo censo textual do plano)
**Impact on plan:** nenhum afrouxamento de garantia; o achado do `test_opcoes_custo_declarado.mjs` reforça a lição do próprio Pitfall 3 (censo por palavra-chave é piso, não teto — a suíte completa é quem prova).

## Issues Encountered

- A sessão foi interrompida por rate limit no meio da Task 2 (logo depois de rodar `bash scripts/executar.sh --testes` a primeira vez). O orquestrador confirmou por `git status` que nenhum trabalho de código tinha sido perdido (7 arquivos modificados + 2 novos, nenhum commit ainda) e pediu para continuar exatamente do ponto — o que foi feito sem refazer a extração.
- Dois avisos de lint pré-existentes foram checados e confirmados FORA do escopo desta task (Scope Boundary): `test_opcoes_consolidacao_ui.mjs:52` (`import { COPY }` não lido — nenhuma linha desta task toca essa área do arquivo) e `test_curadoria_ui.mjs:174-175` (`fatiaHookCurComComentario`/`fatiaCarteiraComComentario` não lidas — idem). Confirmado por `git diff --unified=0` que nenhuma dessas linhas foi tocada pelos meus edits. Não corrigidos aqui.
- `web/tests/test_ios_assets.mjs` falha na suíte canônica com `ENOENT` para `web/ios/App/App/Assets.xcassets/...` — é o gap documentado no `CLAUDE.md` do repositório ("Clone/worktree novo e build iOS": `web/ios/` é gitignored e nasce ausente). Pré-existente, sem relação com `web/src/opcoes/`, fora do escopo desta task (Scope Boundary). Não corrigido.

## Negative-Proof Log (Task 3)

Guardião que passa não prova que guarda. Cada defeito abaixo foi injetado À MÃO, o guardião correspondente rodado sozinho, a saída real conferida, e o arquivo revertido com `git checkout --` (confirmado `git status`/`git diff --stat` limpos depois de cada um).

**1. Import de `App.jsx` em `SecaoVigias.jsx` (varredura de diretório, ADR-027 Emenda 3)**
- Comando de injeção: adicionado `import { T } from "../App.jsx";` logo após o import de `uiOpcoes.jsx`.
- Comando: `node web/tests/test_opcoes_subabas_ui.mjs`
- Saída real: `FALHOU nenhum arquivo de web/src/opcoes/ importa App.jsx (violam: SecaoVigias.jsx)` — nomeia o arquivo certo.
- Revert: `git checkout -- web/src/opcoes/SecaoVigias.jsx`; confirmado `node web/tests/test_opcoes_subabas_ui.mjs` volta a exit 0.

**2. Custo do botão trocado de `custos.listarVigias` para `2` literal**
- Comando de injeção: `{(c.opcoesCustoChamadas || ((n) => String(n)))(2)}` no lugar de `(custos.listarVigias)`.
- Comandos: `node web/tests/test_opcoes_vigias_ui.mjs` e `node web/tests/test_opcoes_custo_declarado.mjs`
- Saída real (vigias): `FALHOU o custo é lido pela PROP custos.listarVigias, nunca um literal`
- Saída real (custo declarado): `FALHOU o controle de listarVigias declara o custo com cp.opcoesCustoChamadas`
- Revert: `git checkout -- web/src/opcoes/SecaoVigias.jsx`; ambos os guardiões voltam a exit 0.

**3. Texto de estado ausente trocado de `"—"` para `"não armado"`**
- Comando de injeção: `{c.opcoesVigiasSemEstado || "não armado"}` no lugar de `"—"`.
- Comando: `node web/tests/test_opcoes_vigias_ui.mjs`
- Saída real: `FALHOU nem OpcoesScreen.jsx nem SecaoVigias.jsx carregam "não armado" como default do bloco`
- Revert: `git checkout -- web/src/opcoes/SecaoVigias.jsx`; guardião volta a exit 0.

**4. Ordem de render invertida — `<SecaoVigias` movido para DEPOIS do seletor**
- Comando de injeção: em `OpcoesScreen.jsx`, `{carteira.length > 0 ? seletor : null}` passou a vir ANTES de `<SecaoVigias .../>` (troca de posição das duas tags).
- Comando: `node web/tests/test_opcoes_vigias_ui.mjs`
- Saída real: `FALHOU o bloco de vigias é RENDERIZADO antes do seletor (D4: vigias antes da carteira)`
- Revert: `git checkout -- web/src/opcoes/OpcoesScreen.jsx`; guardião volta a exit 0.

Nenhuma injeção foi vácua — as 4 reprovaram nomeando exatamente a asserção esperada.

## Baseline da suíte canônica (entrada do plano 33-02)

Rodado fora do sandbox padrão (`dangerouslyDisableSandbox: true`) porque o sandbox interno reprova `pytest` com `PermissionError` de SSL ao carregar `certifi` — achado conhecido e documentado (memória do projeto: "sandbox mente"), não uma falha real.

- **pytest:** 2923 passed, 5 skipped, 3 xfailed, 0 failed — idêntico à baseline herdada da Fase 32.
- **`.mjs`:** 151 OK + 1 falha pré-existente (`test_ios_assets.mjs`, `ENOENT` por `web/ios/` ausente neste worktree — gap documentado no CLAUDE.md, fora do escopo) = 152 arquivos, mesma contagem da baseline da Fase 32.
- **`npx vite build`:** verde nas duas rodadas (antes e depois do commit).

Estes números (2923 pytest / 152 `.mjs`, 1 falha ambiental conhecida e não-regressiva) são a baseline de entrada declarada para o plano 33-02.

## Next Phase Readiness

- `uiOpcoes.jsx` está pronto para ser reusado por `SecaoDescobrir`/`SecaoSetups`/`SecaoComparar`/`SecaoAnalisar` (33-02..33-05) sem duplicar `ErroDoMcp`/`RecusaCobrada`.
- O padrão de reescrita de guardião (reler antes de editar, trocar a fonte lida mantendo a asserção `>= 0` antes do fatiamento, nunca afrouxar) está demonstrado neste plano e pode ser mirrorado nos 4 planos seguintes.
- Nenhum bloqueio conhecido. `App.jsx` intocado, `curadoriaAtiva` fora de escopo preservado (REORG-04).

## Self-Check: PASSED

- `web/src/opcoes/SecaoVigias.jsx` — FOUND
- `web/src/opcoes/uiOpcoes.jsx` — FOUND
- `.planning/phases/33-extra-o-dos-5-jobs-em-componentes-pr-prios/33-01-SUMMARY.md` — FOUND
- Commit `b72ab44` (refactor: extração + guardiões) — FOUND in `git log`
- Commit `dd954e2` (fix: typo no header) — FOUND in `git log`

---
*Phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios*
*Plan: 01*
*Completed: 2026-09-20*
