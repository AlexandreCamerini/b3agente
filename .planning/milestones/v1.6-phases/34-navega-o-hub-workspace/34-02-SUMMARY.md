---
phase: 34-navega-o-hub-workspace
plan: 02
subsystem: ui
tags: [react, jsx, opcoes, hub-workspace-split, guardian-test]

# Dependency graph
requires:
  - phase: 34-navega-o-hub-workspace
    plan: 01
    provides: "WorkspaceHeader.jsx (props-only) + 4 chaves de copy (opcoesVoltarAoHub/opcoesAbaAnalisar/opcoesAbaComparar/opcoesAbaSetupsSalvos) + test_opcoes_hub_workspace_ui.mjs (fundação)"
provides:
  - "OpcoesScreen.jsx com dois modos de renderização sobre `ticker` (hub sem ticker × workspace com ticker) — hubTopo/workspaceTopo, ramo 3 da cascata particionado por modo, ramo 4 intocado"
  - "6 asserções novas em test_opcoes_hub_workspace_ui.mjs cobrindo ordem da cascata, seletor confinado ao hub, onVoltar ligado a escolherTicker, ausência de segundo caminho de volta, adjacência D-04"
  - "Censo dos 21 guardiões que leem OpcoesScreen.jsx — nenhum ficou inerte"
affects: ["34-03"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Particionamento hub/workspace via `ticker ? workspaceTopo : hubTopo`, único novo read de estado (nenhum estado/chamada/rota nova) — reorganização pura sobre o `ticker` já existente"
    - "Guarda-de-modo movida para FORA do bloco, não removida: os dois `ticker ? ... : null` (LastroDoAtivo/LeituraInterna) e o `!semTicker &&` (aviso opcoesSemSetups) somem DENTRO dos fragmentos de modo porque a guarda subiu de nível — documentado em comentário em cada ponto"
    - "Guardião de fatia (não de arquivo inteiro): buscas por marcador (`!ticker ? (`, `carregando ? (`, `erro ? (`) escopadas à fatia da sub-aba \"Setups\" (`{cabecalho}` até `cp.opcoesDisclaimer`) para não colidir com marcadores homônimos de `SubAbaOperar` — achado por injeção real durante a escrita do guardião (ver Issues)"

key-files:
  created: []
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/tests/test_opcoes_hub_workspace_ui.mjs

key-decisions:
  - "D-01 amendment já resolvida na v1.0 do plano (SecaoSetups NÃO entra no hub, migra inteira para o workspace no 34-03) — nada a decidir nesta execução, só seguir o `<interfaces>` do plano"
  - "Ramo 3 (VAZIO): removida a guarda redundante `!semTicker &&` do aviso `opcoesSemSetups` (ela vira sempre-verdadeira dentro do branch `ticker`) — guarda subiu de nível para o `!ticker ? ... : ...` externo, não foi removida sem substituto; a guarda de `semTicker` no LADO HUB do ternário (`carteira.length === 0 ? ... : semTicker ? ...`) foi mantida literalmente, por não ser redundante ali (é ela quem decide entre os dois avisos do hub)"
  - "Guardião novo: toda busca de marcador da cascata (carregando/erro/!ticker) escopada à fatia 'sub-aba Setups', não ao arquivo inteiro — SubAbaOperar tem seus próprios `!ticker ? (`/`carregandoGate` homônimos que tornariam o guardião inerte se buscado no arquivo inteiro (achado por injeção real, ver Issues)"

requirements-completed: [NAV-01, NAV-02, NAV-03, NAV-04, NAV-06]

# Metrics
duration: 45min
completed: 2026-09-20
---

# Phase 34 Plan 02: Particiona OpcoesScreen.jsx em hub × workspace Summary

**`OpcoesScreen.jsx` troca a rolagem única da sub-aba Setups por dois modos de renderização sobre `ticker` (hub sem ticker × workspace com ticker); zero estado/chamada/rota nova.**

## Performance

- **Duration:** 45 min
- **Tasks:** 3
- **Files modified:** 2 (`OpcoesScreen.jsx`, `test_opcoes_hub_workspace_ui.mjs`)

## Accomplishments

- `hubTopo` (SecaoDescobrir + SecaoVigias + seletor, D-04) e `workspaceTopo` (WorkspaceHeader + LastroDoAtivo + LeituraInterna + convite pago) criados como fragmentos JSX, escolhidos por `ticker ? workspaceTopo : hubTopo` — a única leitura de estado nova no arquivo inteiro.
- Cabeçalho e os ramos 1-2 da cascata (carregando/erro) permanecem ÚNICOS, acima da partição — NAV-06 preservado byte a byte (um MCP fora do ar continua visível nos dois modos).
- Ramo 3 (VAZIO COM MOTIVO) particionado por modo: hub vê carteira-vazia/escolher-ativo; workspace vê sem-candles/sem-setups. `nadaParaMostrar` (o gatilho do ramo) não mudou uma vírgula. Ramo 4 (DADOS) ficou intocado, como o plano previa (já é 100% workspace).
- `test_opcoes_hub_workspace_ui.mjs` ganhou 6 grupos de asserções novas (13 checagens) sobre o split; censo dos 21 guardiões que leem `OpcoesScreen.jsx` concluído — nenhum ficou inerte ou precisou de reaponte além do próprio arquivo novo.
- Suíte canônica (pytest + `.mjs`) confirmada na baseline exata da Fase 33/34-01: **2923 pytest passed / 0 failed / 5 skipped / 3 xfailed**; **152/153 `.mjs`** (única falha: `test_ios_assets.mjs`, ambiental, `web/ios/` gitignored). `npx vite build` verde nas 3 tasks.
- `App.jsx`: `git diff --stat` vazio em todas as 3 tasks — intocado.

## Task Commits

Each task was committed atomically:

1. **Task 1: particionar o bloco ACIMA da cascata em hubTopo × workspaceTopo** - `0bf14de` (feat)
2. **Task 2: particionar os ramos 3/4 da cascata por modo** - `5d686ef` (feat)
3. **Task 3: censo dos guardiões + extensão do guardião novo + suíte canônica** - `96174ae` (test)

**Plan metadata:** commit deste SUMMARY.md (a seguir)

## Files Created/Modified

- `web/src/opcoes/OpcoesScreen.jsx` — +126/-88 linhas líquidas (import de `WorkspaceHeader`, `hubTopo`/`workspaceTopo`, partição do ramo 3, comentários de decisão)
- `web/tests/test_opcoes_hub_workspace_ui.mjs` — +109/-2 linhas (6 grupos de asserções novas sobre o split)

## Censo dos 21 guardiões que leem `OpcoesScreen.jsx`

Comando: `grep -ln "OpcoesScreen.jsx" web/tests/*.mjs`. Veredito por arquivo:

| Arquivo | Veredito |
|---|---|
| `test_benchmark_curva.mjs` | não afetado (comentário só cita o arquivo) |
| `test_consolidacao_opcoes_copy.mjs` | não afetado (varre chaves `cp.*`, não posição) |
| `test_carteira_opcoes_tira.mjs` | não afetado (âncoras de import/uso, não posição de render) |
| `test_curadoria_ui.mjs` | não afetado (âncoras de uso do Bloco B, fora do escopo do split) |
| `test_faixa_liquidez_ui.mjs` | não afetado (verbete de liquidez em `SubAbaOperar`) |
| `test_fase22_componentes_compartilhados.mjs` | não afetado (isolamento de função em `SubAbaOperar`) |
| `test_opcoes_consolidacao_ui.mjs` | não afetado — ordem `<SecaoDescobrir` < `<SecaoVigias` e adjacência (sem sticky/input) continuam verdadeiras dentro de `hubTopo`; verificado passando |
| `test_opcoes_custo_declarado.mjs` | não afetado (tabela `CUSTO_DA_ACAO`, não tocada) |
| `test_opcoes_leitura_interna_ui.mjs` | não afetado (estrutura interna de `LeituraInterna`/`ReguaRegime`, não a posição no split) |
| `test_opcao_descoberto_ui.mjs` | não afetado (flag `permitirOpcaoADescoberto`, ausência de menção) |
| `test_opcoes_mcp_aba_ui.mjs` | não afetado (isolamento de import entre módulos) |
| `test_opcoes_analisar_ui.mjs` | não afetado (job 3, extraído para `SecaoAnalisar.jsx` na Fase 33) |
| `test_opcoes_collar_ui.mjs` | não afetado (sub-aba Operar) |
| `test_opcoes_proposta_ui.mjs` | não afetado (sub-aba Operar) |
| `test_opcoes_subabas_ui.mjs` | não afetado — checagem #11 é presença (`tela.includes(nome)`), não posição; `LastroDoAtivo`/`LeituraInterna`/`seletor`/`<SecaoVigias`/`cabecalho`/`blocoLeituraDoServico` continuam todos referenciados no arquivo, só migraram para dentro de `hubTopo`/`workspaceTopo` |
| `test_opcoes_universo_carteira.mjs` | não afetado — ordem `cp.opcoesCarteiraVazia` < `cp.opcoesEscolherAtivo` preservada dentro do ramo hub; verificado passando |
| `test_opcoes_criar_setup_ui.mjs` | não afetado (porta de criação em `SecaoSetups.jsx`, fora do escopo) |
| `test_opcoes_vigias_ui.mjs` | não afetado — `<SecaoVigias` antes de `carteira.length > 0 ? seletor` (D4), literal preservado dentro de `hubTopo`; verificado passando |
| `test_opcoes_hub_workspace_ui.mjs` | **reapontado** — 6 grupos de asserções novas acrescentadas (este plano) |
| `test_opcoes_multi_candidato_ui.mjs` | não afetado (ramo multi-candidato em `SubAbaOperar`) |
| `test_operador_ia_subtela.mjs` | não afetado (import/render de `<OpcoesScreen>` em `App.jsx`) |
| `test_vocabulario_opcoes.mjs` | não afetado (paridade `cp.tituloOpcoes`/`cp.subtituloOpcoes`) |

Nenhum guardião ficaria inerte: a varredura por padrões de risco (`LastroDoAtivo`, `LeituraInterna`, `ticker ? <`, `indexOf` posicional sobre `seletor`/`cabecalho`) não encontrou nenhuma outra dependência de posição fora dos 4 arquivos já listados como "não afetado (verificado passando)" acima, e a suíte completa confirmou 0 regressões.

## Provas Negativas por Injeção (mínimo 2 exigido, 3 executadas)

1. **`seletor` vazando para `workspaceTopo`**: injetado `{seletor}` no fim do fragmento de `workspaceTopo`. Resultado: `FALHOU` a asserção "`seletor` NÃO aparece dentro do corpo de workspaceTopo" — 1 falha. Revertido com `git checkout -- web/src/opcoes/OpcoesScreen.jsx`; guardião voltou a 100% verde.
2. **Inversão do gate do ramo 3** (`{!ticker ? (` → `{ticker ? (`, simulando o defeito que a acceptance_criteria da Task 2 pedia para provar: `cp.opcoesEscolherAtivo` passaria a renderizar com ticker escolhido): `FALHOU` em 2 asserções ("os três marcadores da cascata foram localizados dentro da sub-aba Setups" e "carregando ? e erro ? vêm ANTES do !ticker ?"). Revertido; guardião voltou a 100% verde. Esta prova cobre tanto a acceptance_criteria da Task 2 quanto a exigência de prova negativa da Task 3.
3. Combinado com o achado abaixo (guardião inerte por busca não-escopada), a primeira versão da prova #2 **passou por engano** (o guardião achou o `!ticker ? (` homônimo de `SubAbaOperar` em vez de reprovar) — corrigido antes de aceitar qualquer prova como válida (ver Issues).

## Decisions Made

Ver `key-decisions` no frontmatter. Resumo: nenhuma decisão de arquitetura nova — D-01 (SecaoSetups fica fora do hub) já estava resolvida e registrada em `34-CONTEXT.md`/`34-UI-SPEC.md`/`34-PATTERNS.md` antes desta execução; as únicas escolhas de implementação foram onde remover guardas redundantes (documentado inline) e como escopar o guardião novo para não colidir com `SubAbaOperar`.

## Deviations from Plan

**Nenhum desvio de escopo.** Um ajuste de qualidade dentro da Task 3 (não uma mudança de plano): a primeira versão das asserções 8/9 (ordem da cascata) buscava os marcadores (`carregando ? (`, `erro ? (`, `!ticker ? (`) no arquivo inteiro. Achado por injeção real durante a escrita da prova negativa #2 (ver Issues): `SubAbaOperar` (a sub-aba "Operar", fora do escopo desta fase) tem marcadores homônimos próprios (`!ticker ? (` na linha ~999, para "Escolha uma posição para ver a proposta"), o que fazia o guardião passar mesmo com o gate do ramo 3 de "Setups" invertido — guardião inerte por vacuidade de escopo. Corrigido calculando a fatia da sub-aba "Setups" (`{cabecalho}` até `cp.opcoesDisclaimer`) ANTES de buscar qualquer marcador, e reescaneando só dentro dela. Reexecutada a prova negativa após a correção: reprovou como esperado.

## Issues Encountered

**Guardião inerte por escopo (achado por injeção real, Task 3):** ver `Deviations from Plan` acima — o defeito foi pego pela própria disciplina de prova negativa exigida pelo plano (a primeira tentativa de "quebrar de propósito" não quebrou nada, o que é o sinal de alarme certo), não por revisão estática. Corrigido antes de aceitar a Task 3 como concluída.

**Comentário auto-invalidante (Task 1):** a primeira versão do comentário acima de `hubTopo` citava literalmente `` `ticker ? workspaceTopo : hubTopo` `` para EXPLICAR a decisão, o que fazia `grep -c "ticker ? workspaceTopo : hubTopo"` (acceptance_criteria da Task 1, grep sobre o arquivo COM comentário) retornar 2 em vez de 1. Reescrito para descrever o ternário sem repetir o literal exato. Mesma classe de cuidado que o 34-01-SUMMARY já registrou para `WorkspaceHeader.jsx`.

Nenhum outro problema. Sandbox local bloqueia certificados TLS/rede para o pytest (achado pré-existente, ver memória `worktree-test-setup.md`) — a primeira rodada da suíte canônica reportou 27 falhas de pytest sob sandbox (`PermissionError`/timeout de rede), todas desaparecendo com o bypass de sandbox (2923 passed / 0 failed, total idêntico); a suíte `.mjs` roda igual com ou sem bypass. Toda validação final foi feita com o bypass, conforme a nota de `<validation>` do plano.

## User Setup Required

None - nenhuma configuração de serviço externo necessária.

## Next Phase Readiness

- `hubTopo`/`workspaceTopo` estão prontos para o 34-03 acrescentar a pill row de 3 abas (Analisar/Comparar/Setups salvos) DENTRO de `workspaceTopo`, e mover `SecaoSetups` inteira para dentro dela (D-01 amendment, D-02).
- `test_opcoes_hub_workspace_ui.mjs` está pronto para receber as asserções do 34-03 (pill row, `aria-pressed`, `SecaoSetups` byte-idêntica) — mesmo arquivo, sem criar um terceiro guardião.
- `SecaoSetups.jsx` continua intocada (ramo 4 da cascata não mudou nesta plano) — confirmado por `cp.opcoesSetupsTitulo`/`cp.opcoesCriarTitulo` ainda presentes, checagem 7 do guardião.
- `App.jsx` continua fora do diff da fase inteira (34-01 e 34-02) — confirmado por `git diff --stat web/src/App.jsx` vazio nas 3 tasks desta plano.

---
*Phase: 34-navega-o-hub-workspace*
*Completed: 2026-09-20*

## Self-Check: PASSED

- FOUND: web/src/opcoes/OpcoesScreen.jsx
- FOUND: web/tests/test_opcoes_hub_workspace_ui.mjs
- FOUND: .planning/phases/34-navega-o-hub-workspace/34-02-SUMMARY.md
- FOUND commit: 0bf14de
- FOUND commit: 5d686ef
- FOUND commit: 96174ae
