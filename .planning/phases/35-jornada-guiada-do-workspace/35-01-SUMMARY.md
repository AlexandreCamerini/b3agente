---
phase: 35-jornada-guiada-do-workspace
plan: 01
subsystem: ui
tags: [react, copy-vocabulary, opcoes, progressive-disclosure, accessibility]

# Dependency graph
requires:
  - phase: 34-navega-o-hub-workspace
    provides: "abaWorkspace (estado de navegação do workspace), workspacePillRow (carril de 3 pills), temLeitura/podePedirLeitura (estado da leitura paga)"
provides:
  - "Rótulos de estágio honestos (Passo 1 de 2 / Passo 2 de 2) no portão de leitura paga e no carril de pills"
  - "Linha de transição quando a leitura já foi feita ('Leitura concluída — escolha Analisar ou Comparar.')"
  - "Metadado 'leitura já feita' no lugar do convite quando temLeitura"
  - "Bug fix: convite de leitura paga não aparece mais com a pill 'Setups salvos' ativa"
  - "7 chaves novas de copy.js (nos dois modos, valor idêntico) — 2 consumidas nesta fase, 2 (opcoesEstruturaMontada/opcoesPossibilidadesVistas) reservadas para o plano 35-02"
  - "Guardião test_opcoes_jornada_ui.mjs (24 asserções + 3 provas negativas reais)"
affects: [35-02-hierarquia-visual-cta, 35-03-checkpoint-publicacao]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Kicker com sufixo de estágio via concatenação ' · ' (mesmo separador para D-01 e D-06 — uma convenção só)"
    - "Gate de render condicionado a abaWorkspace (estado já existente da Fase 34), sem estado novo"

key-files:
  created:
    - web/tests/test_opcoes_jornada_ui.mjs
  modified:
    - web/src/copy.js
    - web/src/opcoes/OpcoesScreen.jsx

key-decisions:
  - "D-06 (metadado 'leitura já feita') gateado só por temLeitura, SEM abaWorkspace — decisão literal do UI-SPEC/CONTEXT, registrada em comentário no código para não ser 'corrigida' por simetria visual numa fase futura"
  - "Comentário do gate D-02 evita repetir o literal `abaWorkspace === \"setups\"` para não inflar a contagem de comparações de igualdade que o guardião da Fase 34 mede (achado da própria execução, não do planejamento)"

requirements-completed: [JORN-01, JORN-03]

# Metrics
duration: ~25min
completed: 2026-09-21
---

# Phase 35 Plan 01: Rótulos de estágio e correção do gate por pill Summary

**Dois estágios nomeados (porta de leitura → carril de pills), linha de transição quando a leitura já foi feita, e bug fix que liberava a pill "Setups salvos" do portão de leitura paga que ela nunca precisou.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-09-21
- **Tasks:** 3/3
- **Files modified:** 2 (`web/src/copy.js`, `web/src/opcoes/OpcoesScreen.jsx`)
- **Files created:** 1 (`web/tests/test_opcoes_jornada_ui.mjs`)

## Accomplishments

- O bloco de convite de leitura paga anuncia "LEITURA DO ATIVO · Passo 1 de 2" e o carril de pills anuncia "O QUE FAZER · Passo 2 de 2" — dois estágios reais, nunca três; Analisar/Comparar continuam sem numeração entre si.
- Com a leitura já feita, uma linha de transição ("Leitura concluída — escolha Analisar ou Comparar.") aparece acima do carril, e o lugar do convite passa a mostrar "LEITURA DO ATIVO · leitura já feita" em vez de sumir sem deixar rastro.
- Bug corrigido: o convite de leitura paga não aparece mais quando a pill ativa é "Setups salvos" — seção que nunca leu `temLeitura` e estava sendo bloqueada por um portão sem porta.
- 7 chaves novas de copy nos dois modos (valor idêntico — metadado de progresso, categoria já neutra no arquivo).
- Guardião novo com 24 asserções e 3 provas negativas reais executadas e revertidas.

## Task Commits

1. **Task 1: 7 chaves de jornada em copy.js, nos dois modos** - `c3b4cf5` (feat)
2. **Task 2: rótulos de estágio, linha de transição, gate por pill e ramo "leitura já feita"** - `68d5982` (feat)
3. **Task 3: guardião da jornada (arquivo novo) + prova negativa real** - `2d713e0` (test)

## Files Created/Modified

- `web/src/copy.js` - 7 chaves novas (`opcoesPasso1de2`, `opcoesLeituraJaFeita`, `opcoesEscolhaTitulo`, `opcoesPasso2de2`, `opcoesLeituraConcluidaAjuda`, `opcoesEstruturaMontada`, `opcoesPossibilidadesVistas`) nos dois ramos `COPY.estudo`/`COPY.operador`, agrupadas por vizinhança semântica com comentário datado
- `web/src/opcoes/OpcoesScreen.jsx` - Kicker do convite ganha sufixo "· Passo 1 de 2"; gate `podePedirLeitura && abaWorkspace !== "setups"`; ramo novo `temLeitura ? (...)` com o metadado "leitura já feita"; Kicker "O QUE FAZER · Passo 2 de 2" sempre visível + linha de transição AJUDA
- `web/tests/test_opcoes_jornada_ui.mjs` (novo) - guardião da jornada: 24 asserções cobrindo D-01/D-02/D-06/D-08, princípio 5 (nunca numerar Analisar/Comparar), NAV-05, anti-inércia do guardião da Fase 34, paridade de copy e `SecaoSetups.jsx` intocada

## Decisions Made

- D-06 mantido literal ao UI-SPEC: o metadado "leitura já feita" é gateado só por `temLeitura`, não por `abaWorkspace` — mesmo continuando visível na pill "Setups salvos" (é contexto do ticker, compartilhado pelas três pills; D-02 remove só a AÇÃO paga daquela pill, não o contexto). Registrado em comentário no código para não ser "corrigido" por simetria visual numa fase futura sem decisão explícita.
- Ao escrever o comentário do gate D-02, evitei repetir o literal `abaWorkspace === "setups"` (usei "desigualdade contra a pill 'setups'" em prosa) — escrever o literal exato dentro de um comentário inflaria a contagem bruta de `abaWorkspace === "..."` que o guardião da Fase 34 mede via `grep`, quase quebrando a Task 2 pelo próprio comentário explicativo. Achado durante a execução, corrigido antes do commit.

## Deviations from Plan

None - plan executado como escrito, com um ajuste de redação de comentário (ver "Decisions Made" acima) feito durante a Task 2, antes do commit, para não conflitar com o próprio guardião que o comentário citava.

## Issues Encountered

- **Sandbox mentiu na primeira rodada da suíte canônica**: `bash scripts/executar.sh --testes` dentro do sandbox padrão reportou 27 falhas em pytest (todas de módulos que fazem chamada de rede real — `test_benchmark_ibov`, `test_yahoo_*`, `test_texto_vazio`, etc.), incompatível com a baseline documentada (2923 passed / 0 failed). Re-executado com `dangerouslyDisableSandbox: true` (mesma causa raiz já registrada na memória do projeto — "sandbox mente") e o resultado bateu exatamente com a baseline: **2923 passed, 5 skipped, 3 xfailed, 0 failed** + todos os `.mjs` verdes exceto a falha ambiental pré-existente `test_ios_assets.mjs` (`web/ios/` gitignored, `CLAUDE.md:236`), incluindo o arquivo novo (`test_opcoes_jornada_ui.mjs`) passando.

## User Setup Required

None - no external service configuration required.

## Self-Check Evidence

- `grep -c` das 7 chaves em `copy.js`: 14 (7×2 ramos) — confirmado
- `node` script de paridade estudo/operador: "ok 7/7 iguais nos dois modos"
- Gate D-02: `grep -c` retorna 1; `abaWorkspace === "..."` continua 3 ocorrências
- `cd web && npx vite build`: verde (2 rodadas, Task 2 e Task 3)
- `git diff web/src/App.jsx`: vazio
- 3 provas negativas reais executadas por injeção (`git checkout -- web/src/opcoes/OpcoesScreen.jsx` após cada uma, `git diff --stat` vazio confirmado):
  - (a) reverter gate D-02 para `podePedirLeitura ?` → asserção "existe exatamente 1 ocorrência de `podePedirLeitura && abaWorkspace !== \"setups\"`" reprovou, exit 1
  - (b) trocar `cp.opcoesPasso2de2` por literal `"Passo 2 de 3"` → 3 asserções reprovaram (contagem de `opcoesPasso2de2`, ordem antes de `{workspacePillRow}`, e a regra de "nunca numerar uma 3ª etapa"), exit 1
  - (c) inserir `abrirLeitura()` dentro do ternário `temLeitura ?` da linha de transição → asserção NAV-05 reprovou, exit 1

## Next Phase Readiness

- Plano 35-02 pode consumir `opcoesEstruturaMontada`/`opcoesPossibilidadesVistas` (já existentes em `copy.js`, nos dois modos) sem tocar `copy.js` de novo.
- `OpcoesScreen.jsx` está pronto para a extensão de `BOTAO_PRIMARIO` do plano 35-02 (D-03/D-04/D-05) — nenhuma sobreposição de linha com o que este plano editou (`blocoLeituraDoServico`'s Kicker mudou, o botão dentro dele não).
- Nenhum blocker conhecido para o plano 35-02.

---
*Phase: 35-jornada-guiada-do-workspace*
*Completed: 2026-09-21*

## Self-Check: PASSED

- FOUND: web/src/copy.js (modificado, 7 chaves confirmadas nos dois modos)
- FOUND: web/src/opcoes/OpcoesScreen.jsx (modificado, 4 edições confirmadas)
- FOUND: web/tests/test_opcoes_jornada_ui.mjs (criado, 24 asserções, todas passando)
- FOUND commit c3b4cf5 (git log --oneline --all)
- FOUND commit 68d5982 (git log --oneline --all)
- FOUND commit 2d713e0 (git log --oneline --all)
