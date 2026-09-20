---
phase: 34-navega-o-hub-workspace
plan: 03
subsystem: ui
tags: [react, jsx, opcoes, hub-workspace-split, pill-row, guardian-test, nav-05]

# Dependency graph
requires:
  - phase: 34-navega-o-hub-workspace
    plan: 02
    provides: "OpcoesScreen.jsx com hub/workspace particionado sobre `ticker` — hubTopo/workspaceTopo, ramo 3 da cascata particionado por modo, ramo 4 (DADOS) ainda intocado"
provides:
  - "workspacePillRow: pill row de 3 abas (Analisar/Comparar/Setups salvos, D-02) dentro do workspace, ÚLTIMO elemento acima da cascata"
  - "Ramo 4 (DADOS) gateado por abaWorkspace — os três jobs (SecaoAnalisar/SecaoComparar/SecaoSetups) renderizam um por vez, props e gate temLeitura intactos"
  - "7 asserções novas (14-20) em test_opcoes_hub_workspace_ui.mjs travando NAV-05 por guardião, com prova negativa dupla"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pill row interna do workspace copia VERBATIM a régua visual de `subabas` (mesmos tokens/métrica), com estado próprio (`abaWorkspace`) ortogonal a `subaba` — segundo nível de pill sobre o mesmo padrão, sem componente novo"
    - "Gate de conteúdo (abaWorkspace === id) combinado com gate de dado (temLeitura) via && — nenhum dos dois substitui o outro"
    - "Leitura paga pedida UMA vez, acima do gate de aba (workspaceTopo); trocar de aba é useState puro, nunca um novo useEffect/disparo"

key-files:
  created: []
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/tests/test_opcoes_hub_workspace_ui.mjs

key-decisions:
  - "D-01 amendment (já resolvida antes desta execução, herdada de 34-02): SecaoSetups migra INTEIRA (lista + criação) para a 3ª aba, sem prop `modo` — seguido literalmente, SecaoSetups.jsx permanece intocado"
  - "Comentário auto-invalidante evitado por disciplina: a primeira versão do comentário de `workspacePillRow` citava o literal `` `setAbaWorkspace` `` para EXPLICAR a decisão, o que fazia `grep -c \"setAbaWorkspace\"` (acceptance_criteria da Task 1) retornar 3 em vez de 2 — mesma classe de cuidado que 34-01/34-02 já registraram. Reescrito para descrever sem repetir o identificador literal."

requirements-completed: [NAV-02, NAV-05]

# Metrics
duration: 50min
completed: 2026-09-20
---

# Phase 34 Plan 03: Pill row de 3 abas do workspace + gate do ramo DADOS Summary

**`OpcoesScreen.jsx` ganha a pill row de 3 abas (Analisar/Comparar/Setups salvos) dentro do workspace e gateia o ramo "4. DADOS" por ela; a leitura paga continua pedida uma única vez, acima do gate — trocar de aba é `useState` puro, travado por guardião com prova negativa dupla.**

## Performance

- **Duration:** ~50 min
- **Tasks:** 3
- **Files modified:** 2 (`OpcoesScreen.jsx`, `test_opcoes_hub_workspace_ui.mjs`)

## Accomplishments

- `abaWorkspace`/`setAbaWorkspace` (`useState("analisar")`) declarado junto de `subaba`, explicitamente ortogonal a ele — nenhum dos dois é reusado pelo outro.
- `workspacePillRow` criado copiando verbatim a régua visual de `subabas` (mesmos tokens/métrica de 44px/aria-pressed), com as 3 abas do D-02 (`cp.opcoesAbaAnalisar`/`cp.opcoesAbaComparar`/`cp.opcoesAbaSetupsSalvos`) e renderizado como ÚLTIMO elemento de `workspaceTopo`, acima da cascata — a posição estrutural que faz NAV-05 uma garantia de arquitetura, não uma promessa de comentário.
- Ramo 4 (DADOS) gateado: `SecaoAnalisar` por `abaWorkspace === "analisar"`, `SecaoComparar` por `abaWorkspace === "comparar" && temLeitura` (gate de dado preservado, só combinado com o de aba), `SecaoSetups` por `abaWorkspace === "setups"` — nenhuma prop acrescentada, removida ou renomeada nos três renders (confirmado por `git diff`, ver abaixo).
- Guardião estendido com 7 asserções novas (14-20) cobrindo o núcleo de NAV-05 (nenhum disparador de leitura na pill row, nenhum `useEffect` dependente de `abaWorkspace`), a distinção `abaWorkspace`×`subaba`, a forma da pill row (3 abas, chave de copy, alvo de toque), a sobrevivência do gate `temLeitura`, e a exclusividade mútua dos três renders do ramo 4.
- Duas provas negativas por injeção executadas e revertidas (ver seção própria abaixo).
- Suíte canônica confirmada EXATAMENTE na baseline da Fase 33/34-01/34-02: **2923 pytest passed / 0 failed / 5 skipped / 3 xfailed**; **152/153 `.mjs`** (única falha: `test_ios_assets.mjs`, ambiental, `web/ios/` gitignored). `npx vite build` verde nas 3 tasks.
- `App.jsx`: `git diff --stat` vazio — intocado, como em 34-01/34-02.

## Task Commits

Each task was committed atomically:

1. **Task 1: pill row de 3 abas do workspace** - `7180ae4` (feat)
2. **Task 2: gatear o ramo 4 (DADOS) por aba, preservando props e gates de hoje** - `c09fee7` (feat)
3. **Task 3: guardião de NAV-05 + suíte canônica verde** - `8924a49` (test)

**Plan metadata:** commit deste SUMMARY.md (a seguir)

## Files Created/Modified

- `web/src/opcoes/OpcoesScreen.jsx` — +85/-31 linhas líquidas (estado `abaWorkspace`, `workspacePillRow`, gate do ramo 4, comentários de decisão)
- `web/tests/test_opcoes_hub_workspace_ui.mjs` — +107 linhas (7 grupos de asserções novas + comentário de cabeçalho atualizado)

## Conferência NAV-05 — reabrir cadeia/operáveis depois de trocar de aba (Task 2, exigida pelo plano)

Lida a fonte de `SecaoAnalisar.jsx` e `useOpcoesMcp.js` antes de afirmar, como o plano exige:

- `cadeia`/`operaveis` (os trios `dados/carregando/erro` de `useChamadaSobDemanda`) vivem no **orquestrador** (`useOpcoesMcp`, chamado só em `OpcoesScreen.jsx`) e são passados por PROP para `SecaoAnalisar`. Trocar `abaWorkspace` desmonta `SecaoAnalisar`, mas NÃO desmonta o hook que o chama — os dados pagos permanecem no estado do orquestrador enquanto o `ticker` não mudar.
- `painel` (`"" | "cadeia" | "operaveis"`, o estado de QUAL painel está visualmente aberto) é `useState` LOCAL de `SecaoAnalisar.jsx`. Desmontar a seção (troca de aba) reseta `painel` para `""` — o painel fecha, mas isso é só o estado de exibição, não os dados.
- `abrirCadeia`/`abrirOperaveis` (`useOpcoesMcp.js:365-371`) chamam `dispararCadeia`/`dispararOperaveis` de `useChamadaSobDemanda`, e `useChamadaSobDemanda` (linhas 49-81) **não tem cache interno** — cada chamada a `disparar` sempre refaz o pedido. Isso é comportamento PRÉ-EXISTENTE do botão de toggle (`onClick={() => { const abrir = painel !== "cadeia"; setPainel(...); if (abrir) abrirCadeia(...); }}`, `SecaoAnalisar.jsx:364`), não algo introduzido por esta fase.
- Consequência medida: trocar de `abaWorkspace` para "analisar" NÃO chama `abrirCadeia`/`abrirOperaveis` automaticamente — `painel` volta a `""` (fechado), e reabrir a cadeia/os operáveis exige um CLIQUE explícito do usuário no botão de toggle, que é exatamente o "clique explícito com custo declarado" que o §3.3 do ADR-027 permite. Trocar de ABA em si (o gate `abaWorkspace`) — o que NAV-05 promete — não dispara nenhuma chamada: confirmado tanto por leitura do hook quanto pelas asserções 14/15 do guardião (nenhum disparador na pill row, nenhum `useEffect` dependente de `abaWorkspace`).
- Nenhum `abrirCadeia`/`abrirOperaveis` é chamado no MOUNT de `SecaoAnalisar` (procurado em `SecaoAnalisar.jsx` — o único `useEffect([ticker])` do arquivo só faz `setPainel("")`, não chama nenhuma das quatro funções de disparo). Portanto a condição de PARADA do plano ("se abrirCadeia/abrirOperaveis é chamado no mount") não se aplica — nada a reportar como bloqueio.

**Limite honesto da cobertura do guardião:** as asserções 14/15 (Task 3) leem só `OpcoesScreen.jsx` — a superfície que este plano modifica. Elas travam um disparador ou `useEffect([abaWorkspace])` introduzido NA PILL ROW ou em qualquer outro ponto de `OpcoesScreen.jsx`, mas não são uma checagem de runtime dos três componentes `Secao*.jsx` em si: uma mudança futura DENTRO de `SecaoAnalisar.jsx` que passasse a chamar `abrirCadeia` num `useEffect` de mount (em vez do clique atual) não seria pega por este guardião, porque `SecaoAnalisar.jsx` não está no escopo de leitura desta suíte nem nos `files_modified` deste plano. A conferência acima (leitura direta do fonte) é o que garante o estado ATUAL; o guardião protege a REGRESSÃO na superfície que este plano toca (`OpcoesScreen.jsx`), não uma garantia permanente sobre os três componentes de seção.

## Provas Negativas por Injeção (mínimo 2 exigido, 2 executadas)

1. **Disparador de leitura no `onClick` da pill**: substituído `onClick={() => setAbaWorkspace(a.id)}` por `onClick={() => { abrirLeitura(); setAbaWorkspace(a.id); }}`. Resultado: `FALHOU` a asserção 14 ("workspacePillRow não contém nenhum disparador de leitura paga"), como esperado — e, colateralmente, as asserções 18 (`minHeight`/`aria-pressed`) também falharam porque o `();` injetado por `abrirLeitura()` continha a substring `");"`, cortando cedo a fatia calculada por `indexOf(");", ...)`. Efeito colateral esperado do método de fatiamento por texto (mesma classe de achado que 34-02 já documentou), não um defeito do guardião: o disparador ainda foi pego pela asserção certa. Revertido com `git checkout -- web/src/opcoes/OpcoesScreen.jsx`; guardião voltou a 100% verde (37/37).
2. **`abaWorkspace` nas dependências de um `useEffect` novo**: injetado `useEffect(() => { atualizarVigias(); }, [abaWorkspace]);` logo antes de `const workspacePillRow = (`. Resultado: `FALHOU` exatamente 1 asserção ("nenhum useEffect do arquivo lista abaWorkspace nas dependências"), nenhuma outra — sinal de que o guardião mede especificamente o que promete, sem falso-positivo cruzado. Revertido com `git checkout -- web/src/opcoes/OpcoesScreen.jsx`; guardião voltou a 100% verde.

## Decisions Made

Ver `key-decisions` no frontmatter. Nenhuma decisão de arquitetura nova nesta execução — D-01/D-02 já estavam resolvidas em `34-CONTEXT.md`/`34-UI-SPEC.md`/`34-PATTERNS.md` antes desta plano; a única escolha de implementação foi reescrever um comentário que citava `setAbaWorkspace` literalmente e se auto-invalidava contra a própria acceptance_criteria (mesma classe de cuidado que 34-01/34-02 registraram para outros identificadores).

**Achado de orientação, não desta execução — confirmado intencional:** `web/src/copy.js` tem `opcoesAbaSetupsSalvos: "Setups salvos"` em `COPY.estudo` (linha ~394) mas `opcoesAbaSetupsSalvos: "Setups"` em `COPY.operador` (linha ~1033) — divergência criada no 34-01, não neste plano. O comentário que acompanha a chave no `COPY.operador` (linhas 1026-1029) diz explicitamente que é a MESMA divergência de tom de `opcoesSubabaOperar`/`opcoesSubabaSetups` (Operador é mais terso que Estudo por convenção já estabelecida na Fase 28). Tratado como intencional, não um defeito a corrigir nesta execução — a asserção 6 do guardião (herdada do 34-01) só verifica que a chave existe e não é vazia nos dois modos, por desenho: ela não força um valor idêntico entre locales, porque a divergência de tom É o padrão em toda a paridade `estudo`/`operador` deste arquivo.

## Deviations from Plan

**Nenhum desvio de escopo nas 3 tasks do plano.** Um ajuste de qualidade dentro da Task 1 (não uma mudança de plano): a primeira versão do comentário acima de `workspacePillRow` citava literalmente `` `setAbaWorkspace` `` para explicar por que o `onClick` não dispara leitura, o que fazia `grep -c "setAbaWorkspace"` (acceptance_criteria da Task 1) contar 3 ocorrências (declaração + comentário + `onClick`) em vez das 2 esperadas (declaração + `onClick`). Reescrito para descrever a regra sem repetir o identificador exato — mesmo padrão de cuidado que 34-01 (`WorkspaceHeader.jsx`) e 34-02 (`hubTopo`) já haviam registrado para comentários auto-invalidantes.

**Um 4º commit fora das 3 tasks do plano, e por quê:** depois de escrever a primeira versão deste SUMMARY e ANTES de reportar conclusão, a revisão do advisor apontou duas lacunas de documentação — o limite de cobertura do guardião (asserções 14/15 leem só `OpcoesScreen.jsx`, não os três `Secao*.jsx`) e a divergência `estudo`/`operador` pré-existente de `opcoesAbaSetupsSalvos` (criada no 34-01, não corrigida nem investigada por esta execução até então). Nenhuma das duas exigiu mudança de código — só uma seção nova neste próprio SUMMARY (commit `f65785f`, tipo `docs`). Registrado aqui pela mesma disciplina de honestidade que o resto do documento pede: é um desvio do "3 commits, um por task" declarado no plano, não um "nenhum desvio".

## Issues Encountered

Nenhum problema de execução. Sandbox local bloqueia certificados TLS/rede para o pytest (achado pré-existente, documentado em `worktree-test-setup.md` e no SUMMARY do 34-02) — a primeira rodada da suíte canônica sob sandbox reportou 27 falhas de pytest (`PermissionError: [Errno 1] Operation not permitted` ao carregar certificados TLS), todas desaparecendo com o bypass de sandbox (2923 passed / 0 failed, contagem idêntica ao 34-02). A suíte `.mjs` roda igual com ou sem bypass. Toda validação final foi feita com o bypass, conforme a nota de `<validation>` do plano.

## User Setup Required

None — nenhuma configuração de serviço externo necessária.

## Next Phase Readiness

- Fase 34 fecha com este plano: os 3 planos da fase (34-01 fundação, 34-02 split hub/workspace, 34-03 pill row + gate) estão completos, com `App.jsx` fora do diff da fase inteira e a suíte canônica na baseline exata da Fase 33 em todos os 9 checkpoints de task medidos ao longo dos 3 planos.
- `SecaoSetups.jsx` continua intocada (confirmado por `cp.opcoesSetupsTitulo`/`cp.opcoesCriarTitulo` ainda presentes, asserções 11/12 do guardião) — nenhuma prop `modo` foi introduzida, fiel ao D-01 amendment.
- NAV-05 está travado por guardião com prova negativa dupla, não por comentário/promessa — qualquer regressão futura que reintroduza um disparador na pill row ou um `useEffect` dependente de `abaWorkspace` reprova a suíte antes de chegar a produção.
- Nenhum item de escopo desta fase ficou pendente para uma Fase 35: os itens deferidos (backlog B2, personalização, deep-link) já estavam registrados como fora de escopo em `34-CONTEXT.md` antes desta execução.

---
*Phase: 34-navega-o-hub-workspace*
*Completed: 2026-09-20*

## Self-Check: PASSED

- FOUND: web/src/opcoes/OpcoesScreen.jsx
- FOUND: web/tests/test_opcoes_hub_workspace_ui.mjs
- FOUND: .planning/phases/34-navega-o-hub-workspace/34-03-SUMMARY.md
- FOUND commit: 7180ae4
- FOUND commit: c09fee7
- FOUND commit: 8924a49
