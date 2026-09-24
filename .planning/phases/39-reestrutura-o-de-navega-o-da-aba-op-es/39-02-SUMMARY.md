---
phase: 39-reestrutura-o-de-navega-o-da-aba-op-es
plan: 02
subsystem: ui
tags: [react, copy.js, opcoes, navegacao, curadoria, vigias, adr-027]

# Dependency graph
requires:
  - phase: 39-01
    provides: piso de probabilidade OTM (D-08/D-09/D-11) e prêmio anualizado no backend (opcoes_curadoria.py), consumidos pelo vocabulário novo deste plano
provides:
  - Vocabulário completo da Fase 39 em copy.js (26 chaves novas/reescritas, Estudo+Operador): 3 abas fixas (Oportunidades/Recomendadas/Montar, D-01), Vigias sheet (D-07), ⓘ contextual por aba (D-13), rótulos de bastidor (D-14), piso/ordenação de Recomendadas (D-08/D-09/D-11)
  - Primitivos compartilhados em uiOpcoes.jsx — CarimboFrescor, DetalheInfo, BotaoSaibaMais — isolados de App.jsx (ADR-027)
  - VigiasSheet.jsx (novo) — VigiasBadge (ícone+contador) e VigiasSheet (shell bottom-sheet zIndex 86)
  - Canal one-shot ctx.goOpcoes(aba)/ctx.opcoesAbaInicial/ctx.limparOpcoesAbaInicial em App.jsx — a linha de chamada de Posições agora pede a aba "recomendadas"
affects: [39-03, 39-04, 39-05, 39-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Contratos de interface antes de qualquer rewiring — Planos 03/04 constroem contra copy.js/uiOpcoes.jsx/VigiasSheet.jsx/ctx.goOpcoes sem caçar nada no código"
    - "Canal one-shot de navegação (opcoesAbaInicial) — estado local do App, consumido e limpo pelo destino no mount, nunca persistência"

key-files:
  created:
    - web/src/opcoes/VigiasSheet.jsx
    - web/tests/test_opcoes_nav_primitivos_ui.mjs
  modified:
    - web/src/copy.js
    - web/src/opcoes/uiOpcoes.jsx
    - web/src/App.jsx
    - web/tests/test_consolidacao_opcoes_copy.mjs
    - web/tests/test_opcoes_consolidacao_ui.mjs
    - web/tests/test_opcoes_jornada_ui.mjs

key-decisions:
  - "opcoesLeituraConcluidaAjuda ganhou voz por modo (Estudo/Operador divergem) porque a pill row Analisar/Comparar que motivava o tratamento neutro do plano 35-01 deixou de existir (D-01/D-06) — guardião test_opcoes_jornada_ui.mjs atualizado com nota datada, não apagado"
  - "curadoriaTitulo/curadoriaSubtitulo reescritos: 'AS 4 PRIMEIRAS DO RANKING' substitui 'AS 4 MELHORES OPORTUNIDADES DE OPÇÕES' (colidia com o rótulo da aba vizinha 'Oportunidades', SC#4)"
  - "linhaChamadaOpcoes* passam a contar 'estruturas recomendadas', não 'oportunidades de opções' — a contagem é da curadoria (aba Recomendadas), e 'oportunidades' passaria a nomear o OUTRO motor"
  - "A linha de chamada de Posições passa a pedir ctx.goOpcoes('recomendadas') em vez de abrir a aba padrão — ela conta itens da curadoria, então abrir em Oportunidades (outro motor) quebraria a promessa da frase tocada"

patterns-established:
  - "ctx.goOpcoes(aba) com parâmetro opcional: sem argumento, comportamento idêntico ao de hoje; com string, grava pedido one-shot"

requirements-completed: [NAV-01]

# Metrics
duration: ~35min
completed: 2026-09-24
---

# Phase 39 Plan 02: Contratos de navegação — copy.js, primitivos, Vigias sheet, deep-link Summary

**26 chaves de copy novas/reescritas (Estudo+Operador) para as 3 abas fixas, o sheet de Vigias e o piso de probabilidade de Recomendadas, mais VigiasSheet.jsx e o canal one-shot `ctx.goOpcoes("recomendadas")` em App.jsx — nenhum rewiring de tela ainda, por desenho (interface-first).**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-09-24T16:59:29Z
- **Tasks:** 3/3
- **Files modified:** 4 (copy.js, uiOpcoes.jsx, App.jsx, +1 guardião pré-existente ajustado) + 2 criados (VigiasSheet.jsx, test_opcoes_nav_primitivos_ui.mjs) + 3 guardiões atualizados

## Accomplishments

- `copy.js` ganhou o vocabulário inteiro da Fase 39 nos dois modos: navegação das 3 abas (D-01), rótulos do sheet de Vigias (D-07), aria-label do ⓘ por aba (D-13), rótulos dos ⓘ de bastidor (D-14), piso de 60% de probabilidade OTM + prêmio anualizado em Recomendadas (D-08/D-09/D-11) — zero chave antiga deletada, zero palavra proibida.
- `uiOpcoes.jsx` ganhou 3 primitivos compartilhados (`CarimboFrescor` movido verbatim de `SecaoDescobrir.jsx`, `DetalheInfo`, `BotaoSaibaMais`) e o array `TOKENS` corrigido (faltavam `accent`/`textFaint`, que virariam `undefined` calado).
- `VigiasSheet.jsx` (novo): `VigiasBadge` (ícone de olho + contador, nunca "0" antes de medir) e `VigiasSheet` (shell reusando a mesma geometria de `ConceitoSheet`, zIndex 86) — zero import de `App.jsx`, zero fetch/`store.*` (ADR-027 intacto).
- `App.jsx`: canal one-shot `opcoesAbaInicial`/`limparOpcoesAbaInicial` + `ctx.goOpcoes(aba)` com parâmetro opcional; a linha de chamada de Posições passa a abrir direto na aba Recomendadas.

## Task Commits

1. **Task 1: copy.js — chaves novas e reescritas da Fase 39, nos dois modos** - `663455e` (feat)
2. **Task 2: primitivos compartilhados + VigiasSheet.jsx (badge e sheet)** - `1e1a5aa` (feat)
3. **Task 3: deep-link one-shot — linha de chamada de Posições abre Opções já em Recomendadas** - `077e0c3` (feat)

**Plan metadata:** (a seguir, commit de docs)

## Files Created/Modified

- `web/src/copy.js` - 26 chaves de copy novas/reescritas, Estudo+Operador
- `web/src/opcoes/uiOpcoes.jsx` - CarimboFrescor/DetalheInfo/BotaoSaibaMais + TOKENS corrigido
- `web/src/opcoes/VigiasSheet.jsx` - VigiasBadge + VigiasSheet (novo)
- `web/src/App.jsx` - opcoesAbaInicial/limparOpcoesAbaInicial + ctx.goOpcoes(aba) opcional
- `web/tests/test_consolidacao_opcoes_copy.mjs` - singular/plural atualizado para "estrutura(s) recomendada(s)"
- `web/tests/test_opcoes_consolidacao_ui.mjs` - itens 168-171 (D-02) atualizados para o novo destino/assinatura de goOpcoes
- `web/tests/test_opcoes_jornada_ui.mjs` - guardião de paridade de voz por modo atualizado (opcoesLeituraConcluidaAjuda excluída da lista "idêntica nos dois modos", com nota)
- `web/tests/test_opcoes_nav_primitivos_ui.mjs` - guardião novo (26 asserções): exports, isolamento ADR-027, geometria do sheet, acessibilidade, tokens declarados, chaves de copy, ctx one-shot

## Decisions Made

- `curadoriaSubtitulo` reescrito preserva as 3 funções regulatórias da frase-ponte da Fase 32 (nega hierarquia entre os dois motores, nomeia o critério de piso+ordenação, diz que a IA não reordena) — agora dentro da própria aba, já que Oportunidades/Recomendadas viraram abas separadas.
- Ícone do badge de Vigias: olho (não sino) — "vigia" no vocabulário do produto é observar, seguindo a recomendação não-travada do 39-UI-SPEC.md.
- `vid` do ⓘ por aba: reusa `mkt-opcao` (Fase 38, Alex-aprovado) — não diferenciado por aba nesta fase (recomendação do UI-SPEC, aberta ao planner, não travada).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Guardião pré-existente quebrado pela reescrita de `opcoesLeituraConcluidaAjuda`**
- **Found during:** Task 1 (varredura da suíte completa após a reescrita da chave)
- **Issue:** `test_opcoes_jornada_ui.mjs` (Fase 35) travava que 7 chaves — incluindo `opcoesLeituraConcluidaAjuda` — tinham valor IDÊNTICO nos dois modos ("metadado de progresso, categoria já neutra"). O Plano 39-02 pede explicitamente textos DIFERENTES por modo para essa chave (Estudo mais longo/professor, Operador curto/mesa), porque a pill row Analisar/Comparar que justificava o tratamento neutro deixou de existir (D-01/D-06).
- **Fix:** Guardião atualizado com nota datada (Fase 39, NAV-01) — excluída `opcoesLeituraConcluidaAjuda` da lista de "6 chaves ainda idênticas" e adicionada uma asserção positiva nova exigindo que ela DIVIRJA entre os modos. Nenhuma asserção foi apagada, todas as outras 6 chaves continuam exigidas como idênticas.
- **Files modified:** `web/tests/test_opcoes_jornada_ui.mjs`
- **Verification:** `node web/tests/test_opcoes_jornada_ui.mjs` volta a sair 0; suíte completa `web/tests/*.mjs` (157 arquivos) sem falha.
- **Committed in:** `663455e` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug em guardião pré-existente, consequência direta da reescrita de copy pedida pelo próprio plano)
**Impact on plan:** Necessário para manter a suíte canônica verde; sem mudança de escopo além do que o plano já pedia para `opcoesLeituraConcluidaAjuda`.

## Issues Encountered

- A acceptance criteria do Task 3 (`grep -c "opcoesAbaInicial" web/src/App.jsx >= 3`) inicialmente batia só 2 (a linha do `useState` e a linha `opcoesAbaInicial,` no ctx — `grep -c` conta LINHAS, não ocorrências, e "setOpcoesAbaInicial" não bate por diferença de maiúscula/minúscula). Resolvido citando o identificador por extenso num comentário adjacente, sem mudar comportamento.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Todos os contratos que os Planos 03/04 consomem existem, testados, sem import de `App.jsx`: `copy.js` (vocabulário completo), `uiOpcoes.jsx` (3 primitivos), `VigiasSheet.jsx` (badge+sheet), `ctx.goOpcoes(aba)`/`ctx.opcoesAbaInicial`/`ctx.limparOpcoesAbaInicial` (App.jsx).
- Nenhum rewiring de tela ainda — `OpcoesScreen.jsx`, `SecaoDescobrir.jsx`, `CuradoriaEstruturas.jsx` continuam intocados por este plano (isso é o Plano 03/04, por desenho "interface-first"). `SecaoDescobrir.jsx` mantém sua própria cópia local de `CarimboFrescor` até o Plano 04 deletar o arquivo.
- Suíte canônica web (`web/tests/*.mjs`, 157 arquivos) e `npx vite build` (116 módulos) verdes, sem regressão. Backend não foi tocado por este plano (nenhum arquivo `server/app/*.py` no `files_modified`).

---
*Phase: 39-reestrutura-o-de-navega-o-da-aba-op-es*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: `.planning/phases/39-reestrutura-o-de-navega-o-da-aba-op-es/39-02-SUMMARY.md`
- FOUND: `web/src/opcoes/VigiasSheet.jsx`, `web/tests/test_opcoes_nav_primitivos_ui.mjs`
- FOUND commit `663455e` (Task 1)
- FOUND commit `1e1a5aa` (Task 2)
- FOUND commit `077e0c3` (Task 3)
- Backend sanity (fora do escopo deste plano, nada tocado em `server/`): 640 passed, 1 skipped, 0 failed (`-k "opcoes or curadoria"`)
