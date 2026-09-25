---
phase: 40-continuidade-da-aba-op-es
plan: 01
subsystem: ui
tags: [react, hooks, state-lifting, jsx, front-end]

requires:
  - phase: 39-reestrutura-o-de-navega-o-da-aba-op-es
    provides: "ABAS_OPCOES (3 abas fixas), ctx.opcoesAbaInicial/limparOpcoesAbaInicial (deep-link one-shot de aba), OpcoesScreen.jsx reescrita (39-04)"
provides:
  - "Módulo puro web/src/opcoes/memoriaOpcoes.js (abaInicialOpcoes/tickerInicialOpcoes/memoriaOpcoes)"
  - "Estado em sessão opcoesMemoria + escopoOpcoes em App.jsx, ctx.opcoesMemoria/ctx.lembrarOpcoes"
  - "Restauração silenciosa (sem flash) de ticker + aba ao voltar para a aba Opções, na mesma sessão"
  - "Isolamento por escopo de conta: _resetScopeState() limpa a memória e remonta OpcoesScreen (key={escopoOpcoes})"
affects: [40-continuidade-da-aba-op-es (plano 40-02, checkpoint humano + publicação)]

tech-stack:
  added: []
  patterns:
    - "Lógica pura extraída para módulo sem React/I/O (memoriaOpcoes.js), testada comportamentalmente em Node puro, seguindo a convenção de finance.js/plan.js"
    - "Estado lifted a App.jsx (nunca desmonta) + key de escopo no componente filho para forçar remount em troca de conta — extensão do padrão já existente de opcoesAbaInicial"

key-files:
  created:
    - web/src/opcoes/memoriaOpcoes.js
    - web/tests/test_opcoes_continuidade_ui.mjs
  modified:
    - web/src/App.jsx
    - web/src/opcoes/OpcoesScreen.jsx
    - web/tests/test_opcoes_nav_tres_abas_ui.mjs
    - web/tests/test_opcoes_universo_carteira.mjs
    - web/tests/test_operador_ia_subtela.mjs
    - web/tests/test_opcoes_hub_workspace_ui.mjs

key-decisions:
  - "Memória fica só em memória React de App.jsx (D-01) — nunca em deviceStore/serverStore/localStorage, para não acionar o guardrail de paridade obrigatória dos dois stores por um requirement que não pediu persistência entre reloads."
  - "Write-back contínuo via useEffect([ticker, abaOpcoes]) SEM cleanup — grava no mount e a cada mudança; nunca no unmount, para o _resetScopeState() não ser desfeito pelo desmonte da instância da conta anterior (cenário C)."
  - "Mecanismo de isolamento por escopo (cenário C2): key={escopoOpcoes} incrementada dentro de _resetScopeState() força remount de OpcoesScreen mesmo nos 3 call-sites que não trocam `tab` (login/register/oauth)."
  - "P-1 aplicado sem confirmação do Alex: deep-link sobrescreve só a aba; o ticker lembrado permanece. Fica como item DP-1 para o checkpoint humano do Plano 40-02."

patterns-established:
  - "Módulo puro em web/src/opcoes/ para regra de precedência/validação de estado de navegação, testável sem DOM/mocks"

requirements-completed: [ESTADO-01]

duration: ~110min
completed: 2026-09-25
---

# Phase 40 Plan 01: Continuidade da aba Opções (ESTADO-01) Summary

**Ticker e aba ativa da tela Opções sobrevivem à troca de aba principal na mesma sessão, via estado em memória em App.jsx (nunca nos stores), com precedência deep-link > memória > default e isolamento total por conta.**

## Performance

- **Duration:** ~110 min (2026-09-25T15:30 a 17:22, incluindo 2 rodadas da suíte canônica fora do sandbox, ~2min cada)
- **Started:** 2026-09-25T15:30:56-03:00
- **Completed:** 2026-09-25T17:22:21-03:00
- **Tasks:** 2/2 completas
- **Files modified:** 6 modificados + 2 criados

## Accomplishments
- Módulo puro `memoriaOpcoes.js` com as 3 funções de precedência/validação (deep-link > memória > default; ticker validado contra a carteira; normalização do estado default para `null`), cobertas por 19 asserções comportamentais.
- Fiação completa em `App.jsx`/`OpcoesScreen.jsx`: estado `opcoesMemoria`/`escopoOpcoes`, inicializadores lazy sem salto (D-05), write-back contínuo sem cleanup, limpeza + remount no `_resetScopeState()` (D-04/SC#4, cenário C2).
- 3 guardiões antigos reconciliados com nota datada (allowlist, inicializador de ticker, key de escopo no render) + **1 quarto guardião descoberto durante a execução** (`test_opcoes_hub_workspace_ui.mjs`, regra NAV-05) também reconciliado com exceção nomeada.
- Prova negativa das 3 mitigações críticas (T-40-01/T-40-02): removendo cada peça isoladamente, o guardião novo reprova nomeadamente a asserção correspondente; revertido e confirmado verde.

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: módulo puro memoriaOpcoes.js + guardião ESTADO-01 (comportamental verde, estrutural vermelho)** - `22a249b` (test)
2. **Task 2: fiação App.jsx + OpcoesScreen.jsx, guardiões antigos reconciliados, prova negativa, build e suíte canônica** - `f192eb2` (feat)

**Plan metadata:** (este commit, docs, feito a seguir)

## Files Created/Modified
- `web/src/opcoes/memoriaOpcoes.js` - módulo puro: `abaInicialOpcoes`, `tickerInicialOpcoes`, `memoriaOpcoes` (precedência D-03, validação T-39-14/P-2, normalização C2)
- `web/tests/test_opcoes_continuidade_ui.mjs` - guardião novo ESTADO-01: 19 asserções comportamentais + 29 estruturais (48 `ok(` no total)
- `web/src/App.jsx` - estado `opcoesMemoria`/`escopoOpcoes`; ctx expõe `opcoesMemoria`/`lembrarOpcoes`; `_resetScopeState()` limpa a memória e incrementa o escopo; render usa `key={escopoOpcoes}`
- `web/src/opcoes/OpcoesScreen.jsx` - import de `memoriaOpcoes.js`; inicializadores lazy de `ticker`/`abaOpcoes` lendo a memória; `useEffect([ticker, abaOpcoes])` de write-back sem cleanup; comentário desatualizado sobre `mcpLeitura` corrigido (texto da época preservado, com nota)
- `web/tests/test_opcoes_nav_tres_abas_ui.mjs` - regra da allowlist reconciliada (nota 2026-09-25, Fase 40)
- `web/tests/test_opcoes_universo_carteira.mjs` - inicializador de ticker reconciliado + nova asserção anti-`carteira[0]` (nota 2026-09-25, Fase 40)
- `web/tests/test_operador_ia_subtela.mjs` - render com `key={escopoOpcoes}` reconciliado (nota 2026-09-25, Fase 40)
- `web/tests/test_opcoes_hub_workspace_ui.mjs` - exceção nomeada na regra NAV-05 para o write-back sem I/O (nota 2026-09-25, Fase 40) — **guardião não listado no plano, descoberto durante a Task 2**

## Decisions Made
- D-01/D-02/D-03/D-04/D-05 do CONTEXT.md implementadas literalmente como especificado; nenhuma decisão nova tomada pelo executor além da reconciliação do 4º guardião (ver Issues Encountered).
- Nome da chave de ctx: `lembrarOpcoes` (não `setOpcoesMemoria`), conforme design_decisions §5 do plano — evita confundir com o setter React.
- Mecanismo de C2: `key` de escopo (design_decisions §4 do plano), não revalidação fora do mount.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Guardião não listado (`test_opcoes_hub_workspace_ui.mjs`, regra NAV-05) quebrou com o write-back novo**
- **Found during:** Task 2, ao rodar a suíte canônica completa (o plano listava só 3 guardiões a reconciliar; a suíte completa revelou um 4º)
- **Issue:** a regra NAV-05 ("nenhum useEffect lista `abaOpcoes` nas dependências: trocar de aba nunca dispara chamada") reprovava estruturalmente o novo `useEffect([ticker, abaOpcoes])` de write-back, mesmo ele não fazendo nenhuma chamada de rede/rota — só grava eco local em `ctx`.
- **Fix:** adicionada exceção NOMEADA (regex exata do write-back de memória) à asserção, com nota datada explicando que a intenção original de NAV-05 (nenhuma chamada disparada pela troca de aba) continua de pé — o teste passou a checar isso, não a mera presença da dependência.
- **Files modified:** `web/tests/test_opcoes_hub_workspace_ui.mjs`
- **Verification:** `node web/tests/test_opcoes_hub_workspace_ui.mjs` volta a passar; qualquer OUTRO `useEffect` com `abaOpcoes` nas deps continua reprovado.
- **Committed in:** `f192eb2` (parte do commit da Task 2)

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking, guardião não listado no plano).
**Impact on plan:** Necessário para a suíte canônica passar sem regressão; escopo estritamente do mesmo tipo de reconciliação já previsto pelo plano para os outros 3 guardiões, só que descoberto tarde. Sem scope creep — nenhuma funcionalidade nova, só a asserção do guardião ajustada.

## Issues Encountered
- O acceptance criterion literal `grep -c "setOpcoesMemoria(null); setEscopoOpcoes((n) => n + 1);" web/src/App.jsx == 1` exige as duas chamadas na MESMA linha — o primeiro rascunho as separou em duas linhas (mais legível, mas fora do literal exigido). Ajustado para uma linha só, conforme a ação do plano especifica literalmente.
- Nenhum outro problema; TDD RED/GREEN saiu exatamente como o plano previu (Parte A verde desde a Task 1, Parte B vermelha até a Task 2).

## Limitação declarada (não corrigida nesta fase, per design_decisions §7 do plano)
No nativo, `login` roda `_resetScopeState()` antes de `await loadState()`; entre os dois, `ctx.data.positions` ainda é a carteira anterior, e o seletor de chips (dado de carteira, não da memória desta fase) pode aparecer por um instante. É comportamento pré-existente de TODAS as telas que leem `ctx.data`, não do estado lembrado desta fase — a memória já é `null` e o ticker nasce `""` nesse momento. Não corrigido aqui, por decisão do plano.

## Nota factual sobre C2 (design_decisions §4 do plano)
No código atual, `login`/`register`/`oauth` só são acionáveis via `AuthModal` (aberto por `ctx.openAuth`, tile do Perfil) e o portão de login pós-logout — `logout`/`deleteAccount` já levam `tab` para `"evolucao"`. A key de escopo (`escopoOpcoes`) fecha o cenário C2 por construção (remonta a tela sempre que `_resetScopeState()` roda), independentemente de existir hoje um caminho real que autentique com Opções montada.

## User Setup Required
None - nenhuma configuração de serviço externo necessária.

## Next Phase Readiness
- ESTADO-01 implementado, testado (comportamental + estrutural + prova negativa) e sem regressão na suíte canônica.
- Pendente para o Plano 40-02: checkpoint humano de verificação visual (sair/voltar 3× em 375px sem piscar, cenários A–G ao vivo no aparelho/browser) e publicação (`scripts/bump.sh` + `publicar-web.sh`), conforme o guardrail de "fase sem plano de publicação front" do MEMORY.md.
- Item DP-1 (P-1: deep-link preserva o ticker lembrado) fica para o Alex confirmar/rejeitar no checkpoint do Plano 40-02.

---
*Phase: 40-continuidade-da-aba-op-es*
*Completed: 2026-09-25*

## Self-Check: PASSED
- FOUND: web/src/opcoes/memoriaOpcoes.js
- FOUND: web/tests/test_opcoes_continuidade_ui.mjs
- FOUND: .planning/phases/40-continuidade-da-aba-op-es/40-01-SUMMARY.md
- FOUND commit: 22a249b
- FOUND commit: f192eb2
