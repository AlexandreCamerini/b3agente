---
phase: 08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref
plan: 04
subsystem: ui
tags: [react, historico-medido, adr-017, entrada-automatica, guardiao, radar, operador]

# Dependency graph
requires:
  - phase: 08-01
    provides: "COPY[modo].entradaAuto (regra/contraste/por_setup_disponivel/por_setup_bloqueado) + entradaAutoTxt() em web/src/copy.js, espelho byte a byte de server/app/skill_ref.py"
  - phase: 08-02
    provides: "Gate de elegibilidade real em server/app/agent.py:_avaliar_entradas (predicado `elegivel is True`) — a linha por setup precisa espelhar EXATAMENTE este predicado"
  - phase: 08-03
    provides: "HistoricoPill (web/src/App.jsx) + historicoEstado()/historicoDesatualizado() (web/src/finance.js) — reusados aqui no nível SETUP, nenhum componente/cálculo novo"
provides:
  - "HistoricoPill reusado no item de lista de setup (Ver critérios do setup), com números da janela visíveis (compacto=false) — fecha a lacuna do nível SETUP que só existia no nível TICKER (08-03)"
  - "Carimbo de tempo do dado por setup (medidoAte/calculadoEm), degradando cor+prefixo ⏱ quando desatualizado, sem nunca bloquear a leitura do número"
  - "Transparência do gate por setup em Modo Operador: entradaAutoTxt(modoJS, estadoGate, {setup, janelaRef}) nomeando o setup, condicionado a `operador &&` (Estudo não renderiza)"
  - "Linha agregada cp.entradaAuto.regra/.contraste no card de status único (C-19) do Operador — os dois números do backtest sempre juntos"
  - "web/tests/test_historico_setup_card_ui.mjs — guardião novo (nível setup + card C-19), sabotagem controlada validada em 4 cenários"
affects: [08-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reuso de componente entre nível ticker (08-03) e nível setup (08-04) — mesmo HistoricoPill, sem duplicar contrato visual"
    - "Predicado da UI espelha literalmente o predicado do backend: estadoGate = historicoEstado(...) === 'elegivel' ? 'disponivel' : 'bloqueado', mesma semântica de `elegivel is True` em agent.py (08-02)"
    - "Card de status single-row vira coluna (flexDirection: column) para acomodar linha aditiva read-only, preservando os marcadores de recorte que os guardiões de regressão dependem"

key-files:
  created:
    - web/tests/test_historico_setup_card_ui.mjs
  modified:
    - web/src/App.jsx

key-decisions:
  - "Carimbo de tempo do item de setup é um elemento PRÓPRIO (\"Medido até {data}\"), distinto do indicador de dado velho já embutido no HistoricoPill (que só aparece quando desatualizado) — aqui aparece sempre que há data, degradando cor/prefixo só quando velho, conforme literal do plano"
  - "Predicado de disponibilidade da entrada automática por setup usa o MESMO historicoEstado() já testado em 08-03 (nenhuma reimplementação de estado) — estadoGate cai em 'bloqueado' para todo resultado != 'elegivel' (inelegivel/insuficiente/nunca_medido/aposentado), falha fechada, T-08-21 do threat model"
  - "Linha agregada do card C-19 (cp.entradaAuto.regra/.contraste) renderiza em AMBOS os modos (não condicionada a operador) — a aba 'Operador IA' é visível em Modo Estudo também (BottomNav não filtra por modo) e a frase já é mode-aware nos dois ramos de copy.js"
  - "Linha POR SETUP (entradaAutoTxt) SÓ em Modo Operador — não existe entrada automática em Estudo, anunciar disponibilidade ali seria falso (literal do plano)"

patterns-established:
  - "Guardião de UI recorta por marcador com abort explícito (nunca 0-asserção silenciosa) — padrão replicado de test_fase3_c19_card_status.mjs, agora também em test_historico_setup_card_ui.mjs"

requirements-completed: [ADR17-B34-03, ADR17-B34-04]

# Metrics
duration: ~25min
completed: 2026-08-21
---

# Phase 08 Plan 04: Histórico por setup + transparência do gate no card do Operador Summary

**`HistoricoPill` reusado no nível SETUP (não só ticker) dentro de "Ver critérios do setup", com carimbo de tempo e frase de disponibilidade da entrada automática por setup (`entradaAutoTxt`, mesmo predicado `elegivel is True` do 08-02); card de status único do Operador (C-19) ganha a linha agregada `cp.entradaAuto.regra/.contraste` — guardião novo com sabotagem controlada validada em 4 cenários.**

## Performance

- **Duration:** ~25 min (do primeiro commit ao commit deste SUMMARY)
- **Started:** 2026-08-21T19:26:18-03:00 (commit `ebfc88d`, Task 1)
- **Completed:** 2026-08-21T19:31:04-03:00 (commit `b58ed64`, Task 3)
- **Tasks:** 3
- **Files modified:** 1 (+ 1 criado)

## Accomplishments

- Item de lista de setup (`{isOpen && (r.setups || []).map(...)}` em `RadarScreen`) ganhou: `HistoricoPill` reusado do nível ticker (08-03) logo após `s.confluencia%` — âncora primária preservada, `compacto=false` para expor `expRJanela`/`nJanela`/`janelaRef`; carimbo de tempo do dado (`medidoAte`/`calculadoEm`) abaixo do cabeçalho, degradando cor/prefixo `⏱` só quando desatualizado, nunca bloqueando a leitura do número; e, em Modo Operador, uma linha de transparência do gate por setup (`entradaAutoTxt`) nomeando o setup e a janela de medição — condicionada a `operador &&`, portanto ausente em Modo Estudo.
- Setup aposentado continua na lista sem nenhum tratamento de "removido" (sem `line-through`, sem `opacity` reduzida) — `HistoricoPill` já entrega o rótulo + borda tracejada; o item não adiciona esmaecimento próprio (ADR-017 Decisão 1, registrado em comentário citando a decisão).
- `estadoGate` calculado com o MESMO `historicoEstado()` já testado em 08-03: só "elegivel" vira `"disponivel"`; qualquer outro resultado (`inelegivel`/`insuficiente`/`nunca_medido`/`aposentado`) cai em `"bloqueado"` — espelha literalmente o predicado `elegivel is True` de `_avaliar_entradas` (08-02); a tela nunca promete mais que o gate real permite.
- Card de status único do Operador (C-19, `AgenteScreen`) reestruturado de linha única para coluna, preservando os 3 badges existentes (Modo do app / Operador no servidor / Executar/sinalizar) e o único `onClick` (`A.go("perfil")`), com uma nova linha aditiva read-only: `cp.entradaAuto.regra` + `cp.entradaAuto.contraste`, os dois números do backtest sempre na mesma string vinda de `copy.js`.
- Guardião novo `web/tests/test_historico_setup_card_ui.mjs`: recorta o item de lista de setup e o bloco do card C-19 por marcador (abort explícito se sumir), 23 asserções cobrindo os 10 bullets do `<behavior>` da Task 3. Sabotagem controlada validada em 4 cenários no próprio `web/src/App.jsx` do worktree (nunca em cópia externa — restaurado via `git checkout -- web/src/App.jsx` logo após cada teste, sem sabotagem chegando a commit): remover `HistoricoPill` do item → guardião falha (2 asserções); remover `entradaAutoTxt` do item → guardião falha (2 asserções); remover 1 dos 3 badges do C-19 → guardião falha (1 asserção); renomear o marcador `"C-19 (REPORT-01)"` → guardião ABORTA com mensagem explícita, `exit 1`, nunca silencioso.
- `bash scripts/executar.sh --testes` verde nas DUAS suítes (1268 testes Python + toda a suíte `web/tests/*.mjs`, incluindo os 5 guardiões de regressão do `AgenteScreen` listados no plano). `cd web && npx vite build` sai 0.

## Task Commits

Each task was committed atomically:

1. **Task 1: Histórico por setup na lista de critérios do card** - `ebfc88d` (feat)
2. **Task 2: Linha de transparência do gate no card de status do Operador** - `e2acf8b` (feat)
3. **Task 3: Guardião dos 4 estados por setup e da transparência do gate** - `b58ed64` (test)

**Plan metadata:** (este commit de SUMMARY, feito pelo orquestrador junto com STATE.md/ROADMAP.md — este agente NÃO grava esses arquivos compartilhados)

_Nota: Task 3 tinha `tdd="true"`. A implementação de origem (Tasks 1/2) e o guardião nasceram em commits separados (comportamento primeiro, guardião depois), então houve GREEN→GREEN em vez de um RED→GREEN clássico dentro da própria Task 3 — não havia comportamento pré-existente quebrado a "corrigir" no guardião; ele trava o que as Tasks 1/2 acabaram de implementar. A sabotagem controlada (4 cenários, todos os 3 primeiros derrubando o guardião e o 4º abortando com mensagem) é a evidência empírica de que o guardião de fato falha quando deveria — substitui o RED clássico como prova de que o teste não é vazio. Ver "TDD Gate Compliance" abaixo._

## Files Created/Modified
- `web/src/App.jsx` - item de lista de setup ganha `HistoricoPill`/carimbo de tempo/`entradaAutoTxt` por setup (Task 1); card C-19 ganha `cp.entradaAuto.regra`/`.contraste` (Task 2); import de `entradaAutoTxt` de `copy.js` adicionado
- `web/tests/test_historico_setup_card_ui.mjs` - guardião novo (nível setup + card C-19), 23 asserções, sabotagem controlada validada

## Decisions Made
- Carimbo de tempo do item de setup é um elemento próprio ("Medido até {data}"), sempre desenhado quando há data (`medidoAte` ou prefixo de `calculadoEm`), degradando só cor/prefixo `⏱` quando desatualizado — distinto do indicador interno do `HistoricoPill` (que só aparece quando já está velho); literal do plano.
- Linha agregada do card C-19 (`cp.entradaAuto.regra`/`.contraste`) renderiza em AMBOS os modos, sem condicionar a `operador` — a aba "Operador IA" é visível em Modo Estudo também (`BottomNav` não filtra por aba), e a frase já é mode-aware nos dois ramos de `copy.js` ("No Modo Operador, a entrada automática..." no ramo Estudo).
- Linha POR SETUP (`entradaAutoTxt`) só em Modo Operador — não existe entrada automática em Estudo; anunciar disponibilidade ali seria falso (literal do plano).
- Reestruturação do card C-19 de linha única (`flex row`) para coluna (`flexDirection: column`) foi o mínimo necessário para acomodar a nova linha aditiva sem quebrar os marcadores de recorte (`C-19 (REPORT-01)` → wrapper do `<h1>`) que 5 guardiões de regressão dependem — os 3 badges e o único `onClick` permaneceram literalmente idênticos.

## Deviations from Plan

None - plan executado exatamente como escrito. Uma dependência de ambiente foi resolvida sem mudança de escopo (mesmo achado documentado em `PROJECT.md` e nos Planos 08-01/08-03):

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `npm install` em `web/` antes do `vite build`/testes**
- **Found during:** Task 1 (verificação `npx vite build`)
- **Issue:** Worktree nasce sem `web/node_modules`.
- **Fix:** `npm install` em `web/` (dependências normais do `package.json`, nenhum pacote novo adicionado).
- **Files modified:** nenhum arquivo versionado (`web/node_modules` é gitignored).
- **Verification:** `npx vite build` e `bash scripts/executar.sh --testes` passaram limpos depois.
- **Committed in:** N/A (artefato gitignored, sem commit necessário).

---

**Total deviations:** 1 auto-fixed (1 blocking, ambiente)
**Impact on plan:** Nenhum impacto de escopo — resolução de ambiente já esperada.

## Issues Encountered
None além do item de ambiente acima.

## TDD Gate Compliance

O frontmatter do plano é `type: execute` (não `type: tdd`), então o gate de plano inteiro (RED→GREEN→REFACTOR obrigatório) não se aplica. Task 3 tinha `tdd="true"` na tag de tarefa: o guardião novo foi escrito DEPOIS da implementação (Tasks 1/2), não antes — não houve um ciclo RED (teste falhando contra código ainda inexistente) clássico, porque o `<behavior>` da Task 3 é a especificação do que as Tasks 1/2 acabaram de construir. Em vez do RED clássico, a prova empírica de que o guardião não é vazio veio da sabotagem controlada explicitamente exigida pela acceptance criteria: 4 cenários de regressão aplicados diretamente em `web/src/App.jsx` dentro do próprio worktree (nunca em cópia externa, já que os testes de UI desta base leem o arquivo real por caminho relativo, sem override de path como o guardião cruzado de `skill_ref.py`/`copy.js` tem) — os 3 primeiros (remover `HistoricoPill`, remover `entradaAutoTxt`, remover 1 dos 3 badges do C-19) derrubaram o guardião com falhas específicas, e o 4º (renomear o marcador `"C-19 (REPORT-01)"`) abortou com mensagem explícita (`exit 1`), nunca "0 asserções, tudo ok". Cada sabotagem foi revertida com `git checkout -- web/src/App.jsx` imediatamente após a verificação, confirmado limpo (`git status --short`/`git diff --stat` vazios) antes de prosseguir para o próximo cenário — nenhuma sabotagem chegou a ser commitada.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Vitrine da elegibilidade medida agora completa nos 3 níveis: ticker (Radar/Watchlist, 08-03), setup (item de lista, 08-04) e agregado (card C-19, 08-04) — nenhuma lacuna de vitrine restante do Bloco 3/4 do ADR-017.
- Código do gate (08-02) e a vitrine (08-03/08-04) prontos e testados; NÃO foi deployado (nenhum `atualizar.sh`/`entregar.sh`/`railway`/`git push` executado neste plano, por escopo).
- O checkpoint humano bloqueante antes do deploy em produção do religamento de `entradaAuto` vive no Plano 08-05 desta mesma fase — não seguir sem aprovação explícita do Alex.

## Known Stubs

Nenhum. Todo o dado exibido (`s.historico`, `s.aposentado`, `s.confluencia`, `s.nome`) vem do payload real de `/api/scan` (já entregue desde a Fase 7/Bloco 1), e `cp.entradaAuto.regra`/`.contraste` vêm do vocabulário canônico do 08-01 — nenhum valor mockado ou placeholder aguardando fiação futura.

## Threat Flags

Nenhum achado fora do `<threat_model>` do plano. Os 6 itens do STRIDE Threat Register (T-08-15..T-08-19, T-08-21) foram mitigados conforme desenhado: contraste em string única de `copy.js` (T-08-15), setup aposentado sem esmaecimento (T-08-16), frase do card C-19 espelhando literalmente o predicado do 08-02 (T-08-17), marcadores de recorte preservados nos 5 guardiões de regressão (T-08-18), card C-19 permanece read-only sem controle novo (T-08-19), e `estadoGate` só "disponivel" quando `historicoEstado` devolve `"elegivel"` — mesmo predicado de `_avaliar_entradas`, falha fechada (T-08-21).

---
*Phase: 08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref*
*Completed: 2026-08-21*

## Self-Check: PASSED

All created/modified files verified present (`web/src/App.jsx`, `web/tests/test_historico_setup_card_ui.mjs`, este `SUMMARY.md`). All 3 task commits verified in `git log` (`ebfc88d`, `e2acf8b`, `b58ed64`).
