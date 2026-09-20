---
phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios
plan: 03
subsystem: ui
tags: [react, refactor, opcoes, guardian-tests, static-analysis]

# Dependency graph
requires:
  - phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios (plano 33-02)
    provides: "web/src/opcoes/uiOpcoes.jsx (Kicker/Aviso/ErroDoMcp), padrão de header de proveniência e o precedente de varredura de diretório para guardião cujo call site muda de arquivo"
provides:
  - "web/src/opcoes/SecaoSetups.jsx — job 5 (gerenciar/criar setups salvos) extraído: listagem 'SETUPS GRAVADOS' + porta 'CRIAR UM SETUP', envolvendo CriarSetup.jsx/BotaoDesativar/SetupChart já existentes sem renomeá-los nem reescrevê-los"
  - "5 guardiões reapontados para a topologia nova (test_opcoes_vigias_ui, test_opcoes_criar_setup_ui, test_opcoes_custo_declarado, test_opcoes_analisar_ui) + 1 achado tardio (test_opcoes_mcp_aba_ui) fora do censo por palavra-chave do plano"
  - "Cruzamento de custo declarado migrado de lista fixa para varredura de diretório (Secao*.jsx), preservando a sanidade 'toda chave da tabela tem rótulo na tela'"
  - "Asserção nova (T-33-08): nenhum arquivo de web/src/opcoes/ expõe nomeNoServico fora da derivação da chave ou do key= do React — nascida da injeção 3 da prova negativa, nenhum guardião existente cobria o caso"
affects: [33-04-secao-comparar, 33-05-secao-analisar]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SecaoSetups.jsx: mesmo padrão props-in/callback-out de SecaoVigias.jsx — recebe ticker/setups/naoAvaliado/grafico/callbacks/podeCriarSetup/custos/cp/ctx/palette, nenhum store.*/hook instanciado"
    - "Cruzamento de custo declarado (test_opcoes_custo_declarado.mjs seção 8) migrado de lista de arquivos nomeados para readdirSync(dirOpcoes).filter(Secao*.jsx) — terceiro precedente de D-02 nesta fase, mesma lição do achado tardio do 33-01"
    - "Guardião de exposição de chave interna (T-33-08): permite só duas formas seguras (derivação `const chave = s.nomeNoServico || s.name;` e `key={...nomeNoServico...}` do React) e reprova qualquer outra ocorrência, por varredura de diretório inteiro"

key-files:
  created:
    - web/src/opcoes/SecaoSetups.jsx
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/tests/test_opcoes_vigias_ui.mjs
    - web/tests/test_opcoes_criar_setup_ui.mjs
    - web/tests/test_opcoes_custo_declarado.mjs
    - web/tests/test_opcoes_analisar_ui.mjs
    - web/tests/test_opcoes_mcp_aba_ui.mjs

key-decisions:
  - "SecaoSetups.jsx recebe ctx e palette (além das props listadas no PLAN.md) porque SetupChart.jsx — reusado verbatim para o gráfico de disparos — exige ctx.PriceChart e palette; sem elas o botão 'Disparos do setup' quebraria em runtime"
  - "O aviso 'nenhum setup gravado' do ramo VAZIO da cascata (OpcoesScreen.jsx) e o aviso interno de SecaoSetups.jsx usam a MESMA chave de copy (cp.opcoesSemSetups) de propósito — medem coisas diferentes (nenhuma leitura pedida vs. leitura sem setups), registrado em comentário datado para o próximo leitor não 'limpar' um dos dois como duplicata"
  - "custos desce como prop genérica para SecaoSetups (custos={CUSTO_DA_ACAO} em OpcoesScreen.jsx, custos={custos} repassado a CriarSetup/BotaoDesativar) — SecaoSetups nunca importa CUSTO_DA_ACAO, mesma regra do 33-01"

patterns-established:
  - "Achado tardio de guardião fora do censo por palavra-chave se repete pela terceira vez nesta fase (33-01: test_opcoes_custo_declarado.mjs; 33-02: nenhum, mas o padrão já estava estabelecido; 33-03: test_opcoes_mcp_aba_ui.mjs) — reforça que o censo do PLAN.md é PISO, a suíte canônica completa é quem prova"
  - "Guardião de negative-proof pode reprovar em caso legítimo pré-existente se a regex não distinguir contexto (achado ao escrever a asserção nova de T-33-08: key={...nomeNoServico...} do React é seguro, texto renderizado não é — corrigido antes de comitar, não depois)"

requirements-completed: [REORG-01, REORG-02, REORG-03, REORG-05]

duration: unknown (sessão contínua, sem interrupção de rate limit)
completed: 2026-09-20
---

# Phase 33 Plan 03: Extração de SecaoSetups Summary

**Job 5 ("gerenciar/criar setups salvos") extraído para SecaoSetups.jsx — listagem + porta de criação envolvendo CriarSetup.jsx verbatim —, 5 guardiões reapontados mais 1 achado tardio fora do censo, cruzamento de custo virado varredura de diretório, e uma asserção nova (T-33-08) nascida de injeção real que nenhum guardião cobria.**

## Performance

- **Duration:** não medida com precisão (PLAN_START_TIME não capturado no início real desta execução; sessão contínua sem interrupções)
- **Tasks:** 3/3 completas
- **Files modified:** 1 criado + 6 modificados (5 planejados + 1 achado tardio)

## Accomplishments

- `web/src/opcoes/SecaoSetups.jsx` criado: job 5 como componente próprio, props-in/callback-out, zero `store.*`/`useOpcoesMcp`/checagem de permissão reimplementada (confirmado por grep, REORG-03). Envolve `CriarSetup.jsx`/`BotaoDesativar`/`SetupChart.jsx` já existentes sem renomeá-los nem reescrevê-los (D-01).
- Regra de chave do armazém (`const chave = s.nomeNoServico || s.name;`, Fase 27) migrada verbatim — `abrirGrafico(chave)`, `grafico.setup === chave`, `nome={chave}`/`nomeVisivel={s.name}` no `<BotaoDesativar>` intactos.
- `OpcoesScreen.jsx` mais magro: o bloco "SETUPS GRAVADOS" + "CRIAR UM SETUP" (153 linhas) saiu, junto com os imports de `SetupChart.jsx`/`CriarSetup.jsx`/`BotaoDesativar`; `<SecaoSetups .../>` renderiza na posição EXATA de hoje, dentro do ramo "4. DADOS" da cascata, logo depois de "COMPARAR OS VENCIMENTOS".
- 5 guardiões reapontados: `test_opcoes_vigias_ui.mjs` (seção 4b, regra de chave), `test_opcoes_criar_setup_ui.mjs` (gate visual `podeCriarSetup` migrado para a prop dentro de SecaoSetups.jsx), `test_opcoes_custo_declarado.mjs` (cruzamento de custo virou varredura de diretório sobre `Secao*.jsx`), `test_opcoes_analisar_ui.mjs` (marcador de ordem `iSetups` migrado de `cp.opcoesSetupsTitulo` para `<SecaoSetups`).
- 1 guardião adicional corrigido como achado TARDIO: `test_opcoes_mcp_aba_ui.mjs` — não apareceu no grep de palavras-chave do censo (`opcoesSetupsTitulo|opcoesCriarTitulo|CriarSetup|BotaoDesativar|abrirGrafico|nomeNoServico|podeCriarSetup|CUSTO_DA_ACAO`), só quebrou ao rodar a suíte canônica: 4 asserções liam texto que migrou de arquivo (aria-label do botão de gráfico, `cp.opcoesNaoAvaliado`, o motivo verbatim de `setupsNaoAvaliados`, "sem avaliação hoje").
- 5 injeções negativas reais na Task 3, cada uma reprovando o guardião certo, revertida e reconfirmada verde. A injeção 3 (nomeNoServico renderizado) não tinha guardião algum cobrindo o caso — asserção nova criada, e o primeiro rascunho dela reprovava um uso LEGÍTIMO pré-existente (`key={...nomeNoServico...}` em SecaoVigias.jsx), corrigido antes de comitar.
- `App.jsx` intocado (`git diff --stat web/src/App.jsx` vazio) — REORG-04 preservado.

## Task Commits

1. **Task 1 + Task 2: Criar SecaoSetups.jsx, religar OpcoesScreen.jsx, reapontar os 5 guardiões (+1 achado tardio)** — `3729144` (refactor) — código e guardiões no MESMO commit, por decisão explícita do plano.
2. **Task 3: Provas negativas + baseline** — `84203f1` (test) — as 4 primeiras injeções não deixaram rastro (revertidas, nada para commitar); a injeção 3 exigiu asserção NOVA (nenhum guardião cobria T-33-08), commitada separadamente do código de produção.

**Plan metadata:** este arquivo (SUMMARY) + atualização de STATE.md/ROADMAP.md pelo orquestrador (fora do escopo deste executor, por guardrail do repositório).

## Files Created/Modified

- `web/src/opcoes/SecaoSetups.jsx` (novo) — job 5, listagem de setups + porta de criação.
- `web/src/opcoes/OpcoesScreen.jsx` — perde o bloco "SETUPS GRAVADOS"/"CRIAR UM SETUP" e os imports de `SetupChart.jsx`/`CriarSetup.jsx`; ganha `<SecaoSetups .../>` e nota datada explicando por que os dois avisos "nenhum setup" (VAZIO da cascata vs. interno da seção) usam a mesma chave de copy sem serem duplicata.
- `web/tests/test_opcoes_vigias_ui.mjs` — seção 4b reapontada para `SecaoSetups.jsx`; seção 4c NOVA (T-33-08, varredura de diretório contra `nomeNoServico` fora da derivação/key).
- `web/tests/test_opcoes_criar_setup_ui.mjs` — item 1, gate visual (`<CriarSetup`/`<BotaoDesativar` condicionados a `podeCriarSetup`) migrado para ler `SecaoSetups.jsx`; a derivação da permissão continua medida em `OpcoesScreen.jsx`.
- `web/tests/test_opcoes_custo_declarado.mjs` — seção 8, `linhasDeCusto` migrado de lista fixa (`tela`/`criar`/`vigias`) para varredura de `Secao*.jsx` via `readdirSync`.
- `web/tests/test_opcoes_analisar_ui.mjs` — seção 5, `iSetups` migrado de `cp.opcoesSetupsTitulo` para `<SecaoSetups`.
- `web/tests/test_opcoes_mcp_aba_ui.mjs` — achado tardio: `SecaoSetups.jsx` entrou na leitura (`brutos`); 4 asserções (aria-label, `opcoesNaoAvaliado`, motivo verbatim, "sem avaliação hoje") reapontadas para o arquivo novo.

## Decisions Made

Ver `key-decisions` no frontmatter. Resumo: `SecaoSetups` recebe `ctx`/`palette` além das props do PLAN.md (necessário para `SetupChart`); os dois avisos "nenhum setup" convivem de propósito com a mesma chave de copy, documentado para não serem "limpos" como duplicata; `custos` desce genérico, nunca `CUSTO_DA_ACAO` importado dentro da seção.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `test_opcoes_mcp_aba_ui.mjs` quebrado por migração de arquivo, fora do censo do plano**
- **Found during:** Task 2, ao rodar `bash scripts/executar.sh --testes` pela primeira vez após o commit do refactor
- **Issue:** o guardião lia só `OpcoesScreen.jsx` (entre outros) para 4 asserções: existência de `aria-label=` (o único da tela era o do botão "Disparos do setup"), `cp.opcoesNaoAvaliado`/`cp.opcoesSemSetups`/`cp.opcoesDisclaimer` no dicionário de estado, o motivo de `setupsNaoAvaliados` repassado verbatim, e o texto "sem avaliação hoje". As quatro coisas migraram para `SecaoSetups.jsx` com a extração. O grep de palavras-chave do censo do plano não pegou este arquivo (ele não cita nenhuma das 8 palavras-chave listadas na task).
- **Fix:** `SecaoSetups.jsx` entrou na leitura (`brutos`/`fontes`) do guardião; as 4 asserções passaram a checar `telaSetups` (aria-label e aria-pressed viraram `||` entre os dois arquivos, já que o de `aria-pressed` no seletor de tese continua em `OpcoesScreen.jsx`). Nenhuma asserção foi afrouxada — a garantia é a mesma, só o arquivo lido mudou.
- **Files modified:** `web/tests/test_opcoes_mcp_aba_ui.mjs`
- **Verification:** `node web/tests/test_opcoes_mcp_aba_ui.mjs` — todos os testes passam; suíte canônica completa confirmou nenhum outro guardião afetado pelo mesmo padrão.
- **Committed in:** `3729144` (mesmo commit da Task 2, já que era um guardião afetado pela mesma extração)

**2. [Rule 1 - Bug] Primeiro rascunho da asserção T-33-08 reprovava um uso legítimo pré-existente**
- **Found during:** Task 3, injeção 3 (exibir `s.nomeNoServico` na tela)
- **Issue:** a primeira versão da asserção nova ("nenhum arquivo de `web/src/opcoes/` expõe `nomeNoServico` fora da derivação da chave") reprovava `SecaoVigias.jsx` além do arquivo injetado — `SecaoVigias.jsx:149` usa `v.nomeNoServico` dentro de um `key={...}` do React (reconciliação interna, nunca pintado na tela), um uso seguro que a regex não distinguia de texto renderizado.
- **Fix:** a asserção passou a permitir DUAS formas seguras — a derivação da chave (`const chave = s.nomeNoServico || s.name;`) e o `key={...nomeNoServico...}` do React — antes de checar se sobra alguma ocorrência. Confirmado que só o arquivo com a injeção real reprova depois do ajuste.
- **Files modified:** `web/tests/test_opcoes_vigias_ui.mjs`
- **Verification:** com a injeção presente, reprova nomeando só `SecaoSetups.jsx`; revertida a injeção, guardião passa com `SecaoVigias.jsx` e `SecaoSetups.jsx` intactos.
- **Committed in:** `84203f1` (commit da Task 3, achado antes do commit)

---

**Total deviations:** 2 auto-fixed (1 Rule 3 — guardião bloqueado por migração de arquivo não coberta pelo censo textual do plano; 1 Rule 1 — falso-positivo na própria asserção nova, corrigido antes de comitar)
**Impact on plan:** nenhum afrouxamento de garantia; ambos os achados reforçam a disciplina "censo é piso, suíte completa é quem prova" (33-01) e "injeção real, não descrita, inclusive contra a própria asserção nova" (33-02/33-03).

## Issues Encountered

- `test_ios_assets.mjs` falha na suíte canônica com `ENOENT` para `web/ios/App/App/Assets.xcassets/...` — gap documentado no `CLAUDE.md` do repositório (`web/ios/` gitignored, nasce ausente em worktree novo). Pré-existente, sem relação com `web/src/opcoes/`, fora do escopo desta task. Não corrigido — idêntico à baseline herdada do 33-01/33-02.

## Negative-Proof Log (Task 3)

Guardião que passa não prova que guarda. Cada defeito abaixo foi injetado À MÃO em `web/src/opcoes/SecaoSetups.jsx`, o guardião correspondente rodado sozinho, a saída real conferida, e o arquivo revertido com `git checkout --` (confirmado `git status --porcelain`/`git diff --stat` limpos depois de cada um).

**1. `abrirGrafico(chave)` trocado por `abrirGrafico(s.name)`**
- Injeção: `onClick={() => (aberto ? fecharGrafico() : abrirGrafico(s.name))}`.
- Comando: `node web/tests/test_opcoes_vigias_ui.mjs`
- Saída real: `FALHOU o gráfico é aberto pela chave do ARMAZÉM, não pelo nome da pessoa` — é exatamente o defeito que produziu 422 `setup_desconhecido` em produção no 27-02.
- Revert: `git checkout -- web/src/opcoes/SecaoSetups.jsx`; guardião volta a passar.

**2. `nome={chave}` trocado por `nome={s.name}` no `<BotaoDesativar>`**
- Injeção: `nome={s.name}` no lugar de `nome={chave}`.
- Comando: `node web/tests/test_opcoes_vigias_ui.mjs`
- Saída real: `FALHOU desativar viaja com a chave do armazém e exibe o nome da pessoa`.
- Revert: `git checkout -- web/src/opcoes/SecaoSetups.jsx`; guardião volta a passar.

**3. `{s.nomeNoServico}` exibido na tela (o hash da conta como rótulo)**
- Injeção: `<div>...{s.nomeNoServico}{"registro: " + txt(s.status)}</div>`.
- Rodados TODOS os 7 guardiões tocados/lidos nesta fase (`test_opcoes_vigias_ui.mjs`, `test_opcoes_custo_declarado.mjs`, `test_opcoes_criar_setup_ui.mjs`, `test_opcoes_analisar_ui.mjs`, `test_opcoes_mcp_aba_ui.mjs`, `test_opcoes_subabas_ui.mjs`, `test_opcoes_consolidacao_ui.mjs`) ANTES de criar a asserção — nenhum reprovou (confirma o achado exigido pelo passo 3 da task: "se nenhum guardião reprovar, criar a asserção").
- Asserção nova criada em `test_opcoes_vigias_ui.mjs` (seção 4c, T-33-08): varredura de diretório proibindo `nomeNoServico` fora da derivação da chave ou do `key=` do React.
- Comando: `node web/tests/test_opcoes_vigias_ui.mjs`
- Saída real (primeiro rascunho, ANTES do ajuste do falso-positivo): `FALHOU nenhum arquivo de web/src/opcoes/ expõe nomeNoServico fora da derivação da chave (violam: SecaoSetups.jsx, SecaoVigias.jsx)` — pegou o defeito real E um uso legítimo (`key=`) que a regex ainda não distinguia; corrigida a asserção (permitir `key={...nomeNoServico...}`), a saída ficou: `FALHOU nenhum arquivo de web/src/opcoes/ expõe nomeNoServico fora da derivação da chave (violam: SecaoSetups.jsx)`.
- Revert: `git checkout -- web/src/opcoes/SecaoSetups.jsx`; guardião (já com a asserção corrigida) volta a passar.

**4. Custo do botão de gráfico trocado por literal `2`**
- Injeção: `(cp.opcoesCustoChamadas || ((n) => String(n)))(2)` nos DOIS lugares (aria-label e `<span>` visível) — a primeira tentativa trocou só o `<span>` e o guardião NÃO reprovou (a asserção é "ALGUMA linha declara o custo", e a do aria-label ainda apontava para `custos.grafico`), confirmando que a garantia real é "a chave `grafico` tem pelo menos uma declaração correta em algum lugar do arquivo" — coerente com a letra do guardião, não um bug dele.
- Comando: `node web/tests/test_opcoes_custo_declarado.mjs`
- Saída real (com as DUAS ocorrências trocadas): `FALHOU o controle de grafico declara o custo com cp.opcoesCustoChamadas`.
- Revert: `git checkout -- web/src/opcoes/SecaoSetups.jsx`; guardião volta a passar.

**5. `<CriarSetup>` renderizado fora do gate `podeCriarSetup`**
- Injeção: removido o `{podeCriarSetup ? (...) : null}` ao redor do bloco "CRIAR UM SETUP", deixando `<CriarSetup>` incondicional.
- Comando: `node web/tests/test_opcoes_criar_setup_ui.mjs`
- Saída real: `FALHOU a montagem de <CriarSetup é condicionada a \`podeCriarSetup\``.
- Revert: `git checkout -- web/src/opcoes/SecaoSetups.jsx`; guardião volta a passar.

Nenhuma injeção foi vácua — as 5 reprovaram nomeando exatamente a asserção esperada; a injeção 3 produziu asserção nova por não haver guardião algum cobrindo o defeito antes, e o primeiro rascunho dessa asserção nova foi corrigido por reprovar um caso legítimo (achado antes de comitar, não depois).

## Baseline da suíte canônica (saída deste plano, entrada do 33-04)

Rodado fora do sandbox padrão (`dangerouslyDisableSandbox: true`) porque o sandbox interno reprova `pytest` com `PermissionError` de SSL ao carregar `certifi` — achado conhecido e documentado (memória do projeto: "sandbox mente"), não uma falha real.

- **pytest:** 2923 passed, 5 skipped, 3 xfailed, 0 failed — idêntico à baseline herdada do 33-01/33-02.
- **`.mjs`:** 151 OK + 1 falha pré-existente (`test_ios_assets.mjs`, `ENOENT` por `web/ios/` ausente neste worktree — gap documentado no CLAUDE.md, fora do escopo) = 152 arquivos, mesma contagem da baseline do 33-02.
- **`npx vite build`:** verde nas duas rodadas (após a Task 1/2 e após a Task 3/commit final).

Estes números (2923 pytest / 152 `.mjs`, 1 falha ambiental conhecida e não-regressiva) são a baseline de entrada declarada para o plano 33-04.

## Next Phase Readiness

- Padrão de extração props-in/callback-out (SecaoVigias → SecaoDescobrir → SecaoSetups) reusável para `SecaoComparar`/`SecaoAnalisar` (33-04/33-05).
- Padrão de varredura de diretório para cruzamento de custo declarado (`readdirSync` filtrando `Secao*.jsx`) está pronto para cobrir `SecaoComparar.jsx`/`SecaoAnalisar.jsx` automaticamente quando eles nascerem, sem exigir edição nova do guardião.
- `App.jsx` intocado (`git diff --stat web/src/App.jsx` vazio, confirmado antes de cada commit) — REORG-04 preservado.
- Achado de processo a carregar adiante: o censo textual por palavra-chave do PLAN.md é confiavelmente incompleto (terceira vez nesta fase que a suíte completa encontra um guardião fora dele) — planos 33-04/33-05 devem continuar tratando o censo como piso, não teto.
- Nenhum bloqueio conhecido para o 33-04 (`SecaoComparar`).

## Self-Check: PASSED

- `web/src/opcoes/SecaoSetups.jsx` — FOUND
- `web/src/opcoes/OpcoesScreen.jsx` (modificado, `<SecaoSetups` presente) — FOUND
- Commit `3729144` (refactor: SecaoSetups + 5 guardiões + achado tardio) — FOUND in `git log`
- Commit `84203f1` (test: T-33-08) — FOUND in `git log`

---
*Phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios*
*Plan: 03*
*Completed: 2026-09-20*
