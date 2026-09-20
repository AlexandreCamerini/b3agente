---
phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios
plan: 04
subsystem: ui
tags: [react, refactor, opcoes, guardian-tests, static-analysis]

# Dependency graph
requires:
  - phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios (plano 33-03)
    provides: "web/src/opcoes/SecaoSetups.jsx (job 5), padrão de varredura de diretório para o cruzamento de custo declarado (Secao*.jsx), precedente 'censo é piso, não teto'"
provides:
  - "web/src/opcoes/SecaoComparar.jsx — job 4 (comparação de vencimentos) extraído: custo declarado ANTES do disparo, alvo/stop, cascata de possibilidades por vencimento (PayoffChart/RazaoGanhoPerda/Cenarios)"
  - "Linha/RazaoGanhoPerda migrados para web/src/opcoes/uiOpcoes.jsx — job 3 (ainda em OpcoesScreen.jsx) e job 4 (SecaoComparar.jsx) usam a MESMA implementação"
  - "2 guardiões reapontados para a topologia nova (test_opcoes_analisar_ui.mjs itens 4/5/13) + 1 achado tardio fora do censo do plano (seção 9, alvo/stop) + 1 asserção corrigida em test_opcoes_custo_declarado.mjs (seção 7)"
  - "Asserção nova (Pitfall 6, test_opcoes_vigias_ui.mjs): nenhum Secao*.jsx pode declarar useState de ticker/tese/vencimento/lote — nascida da injeção 5 da prova negativa, nenhum dos 7 guardiões da fase cobria o caso; vale para os 5 componentes desta fase"
  - "Asserção do item 4 endurecida contra reescrita da fórmula de custo com Math.min(...) em vez do literal 2*N+1 — nascida da injeção 2 da prova negativa"
affects: [33-05-secao-analisar]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SecaoComparar.jsx: mesmo padrão props-in/callback-out dos irmãos desta fase — recebe ticker/tese/temTese/lote/loteOk/alvo/setAlvo/stop/setStop/vencimentos/consultados/chamadasPrevistas/possibilidades/verPossibilidades/custos/cp/palette, nenhum store.*/hook instanciado"
    - "loteNum/alvoNum/stopNum (forma numérica exigida pelo corpo de verPossibilidades) derivados LOCALMENTE em SecaoComparar.jsx a partir das strings cruas — mesmo um-liner de OpcoesScreen.jsx, formatação de UMA linha (espelho declarado local), não recálculo de negócio; a conta de custo propriamente dita (N_MAX_VENCIMENTOS/2*N+1) continua proibida no arquivo novo"
    - "Guardião de estado compartilhado entre jobs (Pitfall 6): varredura de diretório sobre Secao*.jsx proibindo useState ligado a ticker/tese/vencimento/lote — quarto precedente de D-02 nesta fase"
    - "Guardião de recálculo de custo endurecido para cobrir reescritas com Math.min(...), não só o literal 2*N+1 — achado real da prova negativa, não hipotético"

key-files:
  created:
    - web/src/opcoes/SecaoComparar.jsx
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/opcoes/uiOpcoes.jsx
    - web/tests/test_opcoes_analisar_ui.mjs
    - web/tests/test_opcoes_custo_declarado.mjs
    - web/tests/test_opcoes_vigias_ui.mjs

key-decisions:
  - "Linha/RazaoGanhoPerda migram para uiOpcoes.jsx (não ficam duplicados) porque job 3 (Analisar, que continua em OpcoesScreen.jsx até o 33-05) e job 4 (SecaoComparar.jsx) renderizam a MESMA razão ganho/perda — duas cópias divergiriam na primeira correção feita só numa delas. Cenarios, que só tinha o consumidor de job 4, foi direto para dentro de SecaoComparar.jsx, sem virar primitivo compartilhado."
  - "vencimentos.length e consultados.length substituem o N cru do orquestrador dentro de SecaoComparar.jsx — são a MESMA grandeza (consultados = vencimentos.slice(0, N) no orquestrador), evitando abrir uma prop extra só para carregar um número já implícito no tamanho do array. Não é recálculo: N_MAX_VENCIMENTOS/2*N+1 nunca aparecem no arquivo novo, e uma asserção trava isso."
  - "loteNum/alvoNum/stopNum (Option B, confirmada com o advisor): derivados localmente em SecaoComparar.jsx a partir dos props crus lote/alvo/stop, em vez de o orquestrador computá-los e descer prontos. Consistente com o texto literal do PLAN.md ('o que FICA no orquestrador e desce por prop: lote, alvo/setAlvo, stop/setStop' — a forma crua, não a derivada) e com a regra já registrada em uiOpcoes.jsx ('formatador de UMA linha pode ser espelho declarado local'). alvoNum/stopNum removidos de OpcoesScreen.jsx por terem ficado sem consumidor ali."
  - "Props seguidas literalmente da lista do PLAN.md (ticker, tese, temTese, lote, loteOk, alvo, setAlvo, stop, setStop, vencimentos, consultados, chamadasPrevistas, possibilidades, verPossibilidades, custos, cp, palette) mesmo onde ticker/custos/lote não são consumidos diretamente dentro do bloco movido — mantém o contrato do componente estável e consistente com os irmãos da fase, e custos preserva o padrão 'a seção nunca importa a tabela, só recebe o que precisar dela'."

patterns-established:
  - "Quarto guardião de varredura de diretório nesta fase (após test_opcoes_subabas_ui.mjs, test_opcoes_analisar_ui.mjs seção 13/recálculo, test_opcoes_custo_declarado.mjs seção 8) — Pitfall 6 (estado compartilhado entre jobs) agora tem cobertura estática que vale para os 5 componentes Secao*.jsx da fase, não só para SecaoComparar.jsx."
  - "Prova negativa que reprova por acidente da REGEX, não da GARANTIA: a injeção 2 (Math.min em vez de 2*N+1) mostrou que uma asserção pode ter a garantia certa e a regex estreita demais — corrigido AMPLIANDO a regex antes de aceitar a prova, não afrouxando a garantia."

requirements-completed: [REORG-01, REORG-02, REORG-03, REORG-05]

duration: unknown (sessão contínua, sem interrupção de rate limit)
completed: 2026-09-20
---

# Phase 33 Plan 04: Extração de SecaoComparar Summary

**Job 4 ("comparar os vencimentos") extraído para SecaoComparar.jsx — custo declarado ANTES do disparo, alvo/stop e cascata de possibilidades por vencimento —, com Linha/RazaoGanhoPerda virando primitivos compartilhados em uiOpcoes.jsx, 2 guardiões reapontados mais 2 achados tardios (um de censo, um de cobertura de regex/estado), e uma asserção nova de Pitfall 6 válida para os 5 componentes da fase.**

## Performance

- **Duration:** não medida com precisão (sessão contínua, sem interrupções)
- **Tasks:** 3/3 completas
- **Files modified:** 1 criado + 5 modificados

## Accomplishments

- `web/src/opcoes/SecaoComparar.jsx` criado: job 4 como componente próprio, props-in/callback-out, zero `store.*`/`useOpcoesMcp`/`useState` de estado compartilhado (confirmado por grep e por guardião novo, REORG-03/Pitfall 6).
- `Linha`/`RazaoGanhoPerda` migrados VERBATIM de `OpcoesScreen.jsx` para `uiOpcoes.jsx` — job 3 (Analisar, que continua em `OpcoesScreen.jsx` até o 33-05) e job 4 usam a MESMA implementação, evitando duas cópias que divergiriam na primeira correção feita só numa delas. `Cenarios` (único consumidor era job 4) foi direto para dentro de `SecaoComparar.jsx`.
- `OpcoesScreen.jsx` mais magro: o bloco "COMPARAR OS VENCIMENTOS" (~90 linhas) saiu, junto com as definições locais de `Linha`/`RazaoGanhoPerda`/`Cenarios` e a derivação órfã `alvoNum`/`stopNum` (ficou sem consumidor ali); `<SecaoComparar .../>` renderiza na posição EXATA de hoje, dentro do MESMO ramo `temLeitura` do job 3, entre "O QUE DÁ PARA MONTAR" e `<SecaoSetups`.
- Custo declarado (`cp.opcoesCustoChamadas(chamadasPrevistas)`) continua aparecendo no fonte ANTES do disparo de `verPossibilidades(...)`; a conta (`N_MAX_VENCIMENTOS`/`2 * N + 1`) continua SÓ no orquestrador; uma asserção nova proíbe qualquer forma da fórmula (literal ou via `Math.min(`) dentro do arquivo novo.
- 2 guardiões reapontados (censo do plano): `test_opcoes_analisar_ui.mjs` itens 4/5/13 (ordem, cascata, razão ganho/perda) e `test_opcoes_custo_declarado.mjs` (conferido, não reescrito por reflexo — a seção 7 precisou de ajuste real, a seção 8 sobreviveu intacta por já cobrir `Secao*.jsx` via varredura de diretório desde o 33-03).
- 2 achados TARDIOS fora do censo literal do plano: (a) a seção 9 de `test_opcoes_analisar_ui.mjs` ("alvo e stop viajam NOMEADOS") ancorava em `OpcoesScreen.jsx` e quebraria silenciosamente — reapontada para `SecaoComparar.jsx`; (b) a injeção 5 da prova negativa (Pitfall 6) não reprovava em NENHUM dos 7 guardiões da fase — asserção nova criada em `test_opcoes_vigias_ui.mjs`, por varredura de diretório, valendo para os 5 componentes `Secao*.jsx`.
- 5 injeções negativas reais na Task 3: 3 já reprovavam com os guardiões existentes; 1 (recálculo com `Math.min`) exigiu ampliar a regex da asserção nova; 1 (useState de `tese`) exigiu a asserção nova de Pitfall 6 descrita acima. Todas revertidas e reconfirmadas verdes.
- `App.jsx` intocado (`git diff --stat web/src/App.jsx` vazio) — REORG-04 preservado.

## Task Commits

1. **Task 1 + Task 2: Criar SecaoComparar.jsx, migrar Linha/RazaoGanhoPerda/Cenarios, religar OpcoesScreen.jsx, reapontar os guardiões (+1 achado tardio)** — `3002958` (refactor) — código e guardiões no MESMO commit, por decisão explícita do plano.
2. **Task 3: Provas negativas + endurecimento de guardião (Math.min) + asserção nova (Pitfall 6) + baseline** — `7fe429b` (test).

**Plan metadata:** este arquivo (SUMMARY) + atualização de STATE.md/ROADMAP.md pelo orquestrador (fora do escopo deste executor, por guardrail do repositório).

## Files Created/Modified

- `web/src/opcoes/SecaoComparar.jsx` (novo) — job 4, caixa de comparação de vencimentos com custo declarado, alvo/stop e cascata de possibilidades.
- `web/src/opcoes/uiOpcoes.jsx` — ganha `Linha`/`RazaoGanhoPerda` (migrados de `OpcoesScreen.jsx`) e os tokens/helpers que eles exigem (`textPrimary`/`borderFaint`, `ehNum`/`fmt`, `AJUDA`).
- `web/src/opcoes/OpcoesScreen.jsx` — perde o bloco "COMPARAR OS VENCIMENTOS", as definições locais de `Linha`/`RazaoGanhoPerda`/`Cenarios` e a derivação órfã de `alvoNum`/`stopNum`; ganha o import de `SecaoComparar.jsx` e de `Linha`/`RazaoGanhoPerda` de `uiOpcoes.jsx`, e `<SecaoComparar .../>` na posição exata.
- `web/tests/test_opcoes_analisar_ui.mjs` — itens 4/5/13 reapontados para `SecaoComparar.jsx`/`uiOpcoes.jsx`; asserção nova contra `Math.min(` (item 4); seção 9 (achado tardio) reapontada para `SecaoComparar.jsx`.
- `web/tests/test_opcoes_custo_declarado.mjs` — seção 7, segunda asserção passa a ler `SecaoComparar.jsx` (onde o controle está), com nota datada explicando por que virou vácuo em `tela`.
- `web/tests/test_opcoes_vigias_ui.mjs` — seção 4d NOVA (Pitfall 6): varredura de diretório contra `useState` de `ticker`/`tese`/`vencimento`/`lote` em qualquer `Secao*.jsx`.

## Decisions Made

Ver `key-decisions` no frontmatter. Resumo: `Linha`/`RazaoGanhoPerda` viram primitivos compartilhados (job 3 e job 4 usam a mesma implementação); `Cenarios` fica exclusivo de `SecaoComparar.jsx`; `N`/`consultados` viram `.length` no arquivo novo em vez de uma prop extra; `loteNum`/`alvoNum`/`stopNum` são derivados LOCALMENTE em `SecaoComparar.jsx` a partir dos props crus (Option B, confirmada com o advisor, consistente com o texto literal do plano e com a regra de "formatador de uma linha, espelho declarado local" já registrada em `uiOpcoes.jsx`); props seguem a lista literal do plano mesmo onde algum nome (ticker/custos) não é consumido diretamente no bloco movido, para manter o contrato do componente estável.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `test_opcoes_analisar_ui.mjs` seção 9 ("alvo e stop viajam NOMEADOS") fora do censo do plano**
- **Found during:** Task 1/2, ao mapear todas as referências de `alvoNum`/`stopNum`/`cp.opcoesAlvoRotulo`/`cp.opcoesStopRotulo` antes de mover o bloco (não apareceu nos itens 4/5/13 citados no PLAN.md)
- **Issue:** a seção 9 checava 4 asserções contra `tela` (`OpcoesScreen.jsx`): o corpo nomeado (`alvo: alvoNum`), os dois rótulos (`cp.opcoesAlvoRotulo`/`cp.opcoesStopRotulo`) e a declaração de `alvoNum`. As quatro coisas migraram inteiras para `SecaoComparar.jsx` com a extração — nenhuma sobrevive em `OpcoesScreen.jsx`.
- **Fix:** as 4 asserções passaram a ler `secaoComparar` em vez de `tela`. A garantia (alvo/stop nomeados, nunca número solto; rótulo próprio; preço ausente vira ausência) não afrouxou.
- **Files modified:** `web/tests/test_opcoes_analisar_ui.mjs`
- **Verification:** `node web/tests/test_opcoes_analisar_ui.mjs` — todos os testes passam; suíte canônica completa confirmou nenhum outro guardião afetado pelo mesmo padrão.
- **Committed in:** `3002958` (mesmo commit da Task 1/2, já que era um guardião afetado pela mesma extração)

**2. [Rule 1 - Bug] Asserção nova do item 4 (proibição de recálculo) reprovava regex estreita demais, não a garantia**
- **Found during:** Task 3, injeção 2 (recalcular `chamadasPrevistas` com `2 * Math.min(vencimentos.length, 6) + 1`)
- **Issue:** a asserção nova criada na Task 2 só buscava o literal `2 \* N \+ 1` e `N_MAX_VENCIMENTOS` — uma reescrita da MESMA fórmula com `Math.min(...)` e outro nome de variável não batia na regex, apesar de ser exatamente o defeito que a asserção deveria pegar (dupla fonte da mesma conta).
- **Fix:** a asserção passou a proibir também `Math\.min\(` dentro de `SecaoComparar.jsx`, alinhando com o que o verify script da Task 1 já checava (`N_MAX_VENCIMENTOS|2 \* N \+ 1|Math\.min\(`).
- **Files modified:** `web/tests/test_opcoes_analisar_ui.mjs`
- **Verification:** com a injeção presente, reprova nomeando a asserção certa; revertida a injeção, guardião volta a passar.
- **Committed in:** `7fe429b` (commit da Task 3, achado antes do commit)

**3. [Rule 2 - Missing Critical] Nenhum guardião cobria Pitfall 6 (estado compartilhado redeclarado em Secao*.jsx)**
- **Found during:** Task 3, injeção 5 (`const [tese, setTese] = useState("")` dentro de `SecaoComparar.jsx`)
- **Issue:** rodados os 7 guardiões tocados/lidos nesta fase antes de criar a asserção — nenhum reprovava. Sem cobertura, um `Secao*.jsx` futuro poderia redeclarar `ticker`/`tese`/`vencimento`/`lote` localmente sem que a suíte notasse, quebrando a sincronização entre jobs (ex.: a tese mudaria só dentro da seção, divergindo do que o job 3 mostra).
- **Fix:** asserção nova em `test_opcoes_vigias_ui.mjs` (seção 4d), por varredura de diretório sobre `Secao*.jsx`, proibindo `useState` ligado a `ticker`/`tese`/`vencimento`/`lote` — vale para os 5 componentes desta fase, não só `SecaoComparar.jsx`.
- **Files modified:** `web/tests/test_opcoes_vigias_ui.mjs`
- **Verification:** com a injeção presente, reprova nomeando `SecaoComparar.jsx`; revertida, guardião passa com os 5 `Secao*.jsx` intactos (sem falso-positivo).
- **Committed in:** `7fe429b` (commit da Task 3, achado antes do commit)

---

**Total deviations:** 3 auto-fixed (1 Rule 3 — guardião bloqueado por migração de arquivo não coberta pelo censo textual do plano; 1 Rule 1 — regex estreita demais numa asserção recém-criada; 1 Rule 2 — lacuna real de cobertura para Pitfall 6, achada só por injeção real)
**Impact on plan:** nenhum afrouxamento de garantia; os três achados reforçam a disciplina já estabelecida nesta fase ("censo é piso, suíte completa é quem prova" — 33-01; "injeção real, não descrita, inclusive contra a própria asserção nova" — 33-02/33-03).

## Issues Encountered

- `test_ios_assets.mjs` falha na suíte canônica com `ENOENT` para `web/ios/App/App/Assets.xcassets/...` — gap documentado no `CLAUDE.md` do repositório (`web/ios/` gitignored, nasce ausente em worktree novo). Pré-existente, sem relação com `web/src/opcoes/`, fora do escopo desta task. Não corrigido — idêntico à baseline herdada do 33-01/33-02/33-03.

## Negative-Proof Log (Task 3)

Guardião que passa não prova que guarda. Cada defeito abaixo foi injetado À MÃO em `web/src/opcoes/SecaoComparar.jsx`, o guardião correspondente rodado sozinho, a saída real conferida, e o arquivo revertido com `git checkout --` (confirmado `git status --porcelain`/`git diff --stat` limpos depois de cada um).

**1. Custo movido para DEPOIS do disparo**
- Injeção: o `<div>` que declara `cp.opcoesCustoChamadas(chamadasPrevistas)` foi removido do lugar original e recolado logo depois do `<button onClick={() => verPossibilidades(...)}>`.
- Comando: `node web/tests/test_opcoes_analisar_ui.mjs`
- Saída real: `FALHOU o custo aparece no fonte ANTES do disparo (aviso, não recibo)`.
- Revert: `git checkout -- web/src/opcoes/SecaoComparar.jsx`; guardião volta a passar.

**2. Recalcular `chamadasPrevistas` dentro da seção, com fórmula reescrita**
- Injeção: `const n = 2 * Math.min(vencimentos.length, 6) + 1;` colado dentro do componente.
- Comando: `node web/tests/test_opcoes_analisar_ui.mjs`
- Saída real (ANTES do ajuste da asserção): `todos os testes passaram` — a asserção nova só buscava o literal `2 * N + 1`, e a reescrita com `Math.min` não batia. Corrigida a regex (ver Deviations item 2), a saída ficou: `FALHOU SecaoComparar.jsx não recalcula o teto nem a fórmula do custo (uma conta só)`.
- Revert: `git checkout -- web/src/opcoes/SecaoComparar.jsx`; guardião (já com a regex corrigida) volta a passar.

**3. Cascata invertida — vazio ANTES de carregando**
- Injeção: o ramo `possibilidades.dados && !(...).length` (vazio com motivo) movido para o INÍCIO da cadeia ternária, antes de `possibilidades.carregando`.
- Comando: `node web/tests/test_opcoes_analisar_ui.mjs`
- Saída real: `FALHOU Possibilidades: ordem carregando → erro → vazio com motivo → dados`.
- Revert: `git checkout -- web/src/opcoes/SecaoComparar.jsx`; guardião volta a passar.

**4. `<ErroDoMcp>` substituído por texto que raspa `.message`**
- Injeção: `<ErroDoMcp erro={possibilidades.erro} cp={cp} />` trocado por `<Aviso tom="forte">{possibilidades.erro.message}</Aviso>`.
- Comando: `node web/tests/test_opcoes_analisar_ui.mjs`
- Saída real: `` FALHOU Possibilidades: o erro é escolhido pelo `code` (ErroDoMcp), não raspando a mensagem ``.
- Revert: `git checkout -- web/src/opcoes/SecaoComparar.jsx`; guardião volta a passar.

**5. `const [tese, setTese] = useState("")` declarado dentro da seção (Pitfall 6)**
- Injeção: `import { useState } from "react";` + `const [tese, setTese] = useState("");` dentro do componente, sombreando o prop `tese`.
- Rodados TODOS os 7 guardiões tocados/lidos nesta fase (`test_opcoes_vigias_ui.mjs`, `test_opcoes_custo_declarado.mjs`, `test_opcoes_criar_setup_ui.mjs`, `test_opcoes_analisar_ui.mjs`, `test_opcoes_mcp_aba_ui.mjs`, `test_opcoes_subabas_ui.mjs`, `test_opcoes_consolidacao_ui.mjs`) ANTES de criar a asserção — nenhum reprovou.
- Asserção nova criada em `test_opcoes_vigias_ui.mjs` (seção 4d): varredura de diretório proibindo `useState` ligado a `ticker`/`tese`/`vencimento`/`lote` em qualquer `Secao*.jsx`.
- Comando: `node web/tests/test_opcoes_vigias_ui.mjs`
- Saída real: `FALHOU nenhum Secao*.jsx redeclara ticker/tese/vencimento/lote como estado local (Pitfall 6) (violam: SecaoComparar.jsx)` — nomeia o arquivo certo, sem falso-positivo contra os outros 4 `Secao*.jsx`.
- Revert: `git checkout -- web/src/opcoes/SecaoComparar.jsx`; guardião (já com a asserção nova) volta a passar.

Nenhuma injeção foi vácua no final: a 1/3/4 reprovaram de primeira; a 2 e a 5 exigiram correção de guardião ANTES de aceitar a prova (regex estreita e cobertura ausente, respectivamente) — ambas corrigidas e reconfirmadas antes do commit.

## Baseline da suíte canônica (saída deste plano, entrada do 33-05)

Rodado fora do sandbox padrão (`dangerouslyDisableSandbox: true`) porque o sandbox interno reprova `pytest` com `PermissionError` de SSL ao carregar `certifi` — achado conhecido e documentado (memória do projeto: "sandbox mente"), não uma falha real.

- **pytest:** 2923 passed, 5 skipped, 3 xfailed, 0 failed — idêntico à baseline herdada do 33-01/33-02/33-03.
- **`.mjs`:** 151 OK + 1 falha pré-existente (`test_ios_assets.mjs`, `ENOENT` por `web/ios/` ausente neste worktree — gap documentado no CLAUDE.md, fora do escopo) = 152 arquivos, mesma contagem da baseline do 33-03.
- **`npx vite build`:** verde nas três rodadas (após a Task 1/2, durante as reversões da Task 3, e após o commit final).

Estes números (2923 pytest / 152 `.mjs`, 1 falha ambiental conhecida e não-regressiva) são a baseline de entrada declarada para o plano 33-05.

## Verificação manual (Pitfall 7)

Conferido à mão no fonte: a frase "os N primeiros de X" (vencimentos truncados) continua visível sem clique extra — está no mesmo `<div>` que "Vencimentos consultados: ...", dentro do ramo `consultados.length !== 0` de `SecaoComparar.jsx`, exatamente como em `OpcoesScreen.jsx` antes da extração. Reorganizar não reduziu informação.

## Next Phase Readiness

- Padrão de extração props-in/callback-out (SecaoVigias → SecaoDescobrir → SecaoSetups → SecaoComparar) reusável para `SecaoAnalisar` (33-05), inclusive o padrão de mover primitivo compartilhado (`Linha`/`RazaoGanhoPerda`) para `uiOpcoes.jsx` quando dois jobs precisam da mesma implementação.
- Guardião de Pitfall 6 (`test_opcoes_vigias_ui.mjs`, seção 4d) já cobre `SecaoAnalisar.jsx` automaticamente quando ele nascer — nenhuma edição nova necessária ali.
- `App.jsx` intocado (`git diff --stat web/src/App.jsx` vazio, confirmado antes de cada commit) — REORG-04 preservado.
- Achado de processo a carregar adiante: além do censo textual do PLAN.md ser piso e não teto (quarta vez nesta fase), uma asserção NOVA recém-criada também pode ter regex estreita demais para a garantia que pretende — a prova negativa precisa confirmar que a REGEX pega reescritas plausíveis do defeito, não só a forma literal descrita no plano.
- Nenhum bloqueio conhecido para o 33-05 (`SecaoAnalisar`), o mais entrelaçado com `SubAbaOperar` e com o fold-in D-04a (fetch redundante de gate/proposta).

## Self-Check: PASSED

- `web/src/opcoes/SecaoComparar.jsx` — FOUND
- `web/src/opcoes/uiOpcoes.jsx` (modificado, `Linha`/`RazaoGanhoPerda` exportados) — FOUND
- `web/src/opcoes/OpcoesScreen.jsx` (modificado, `<SecaoComparar` presente) — FOUND
- Commit `3002958` (refactor: SecaoComparar + guardiões) — FOUND in `git log`
- Commit `7fe429b` (test: prova negativa + asserções novas) — FOUND in `git log`

---
*Phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios*
*Plan: 04*
*Completed: 2026-09-20*
