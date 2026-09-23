---
phase: 38-kb-did-tica-ampliada
plan: 02
subsystem: ui
tags: [react, extraction, refactor, frontend, guardian-tests]

# Dependency graph
requires: []
provides:
  - "web/src/entendimento.jsx: módulo terceiro com AiNote, SUBLINHADO, SetorAlvo, AssistenteBox, ConceitoSheet (+ CONCEITO_BLOCOS/SR_ONLY privados), importável tanto por App.jsx quanto por web/src/opcoes/OpcoesScreen.jsx sem ciclo (ADR-027)"
  - "web/tests/test_entendimento_modulo.mjs: guardião de isolamento/tokens/ausência para a extração"
  - "6 guardiões pré-existentes reapontados para o código movido, contrato preservado byte a byte"
affects: [38-05, "opcoes/OpcoesScreen.jsx", "web/src/App.jsx"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Token de tema T local espelhado (VARKEY/TOKENS, mesmo padrão de web/src/opcoes/uiOpcoes.jsx da Fase 33) em módulo fora de App.jsx"

key-files:
  created:
    - web/src/entendimento.jsx
    - web/tests/test_entendimento_modulo.mjs
  modified:
    - web/src/App.jsx
    - web/tests/test_conceito_ui.mjs
    - web/tests/test_setor_toque.mjs
    - web/tests/test_boris_chat.mjs
    - web/tests/test_fonte_explicacao.mjs
    - web/tests/test_numeros_fundamentados.mjs
    - web/tests/test_perfil_reorg.mjs

key-decisions:
  - "Extração verbatim, zero mudança de comportamento — nenhum call-site em App.jsx alterado"
  - "AssistenteBox exportado do módulo novo mas NÃO importado de volta em App.jsx (único consumidor é ConceitoSheet, que já mora em entendimento.jsx)"
  - "Achado próprio (T-38-07): guardião de zIndex 86 em test_conceito_ui.mjs passava por coincidência contra o PetSheet (outro overlay, mesmo zIndex/estilo) depois da extração — reapontado para medir o componente real (ConceitoSheet em entendimento.jsx) em vez de deixar o falso positivo silencioso"
  - "test_perfil_reorg.mjs: marcador de fim do PerfilHub trocado de \"function SetorAlvo(\" (símbolo que migrou) para a próxima declaração de topo real (TIMING_STYLE), com prova de parse-não-mudo (hubGroup presente, nenhum outro function de topo na fatia)"

patterns-established:
  - "Regra de reapontamento de guardião pós-extração: comentário datado 'Fase 38 (38-02, 2026-09-23): <símbolo> migrou para web/src/entendimento.jsx' em cada asserção reapontada"

requirements-completed: [KB-02]

# Metrics
duration: ~30min
completed: 2026-09-23
---

# Phase 38 Plan 02: Extração da camada de entendimento Summary

**`SetorAlvo`/`ConceitoSheet`/`AssistenteBox`/`AiNote`/`SUBLINHADO` movidos verbatim de `App.jsx` para `web/src/entendimento.jsx`, um módulo terceiro sem ciclo com `opcoes/OpcoesScreen.jsx` (ADR-027), com os 6 guardiões pré-existentes reapontados e um guardião novo de isolamento/tokens.**

## Performance

- **Duration:** ~30 min
- **Completed:** 2026-09-23T12:14:16Z
- **Tasks:** 2/2
- **Files modified:** 8 (1 criado + 1 criado em teste + 6 testes reapontados + App.jsx)

## Accomplishments
- `web/src/entendimento.jsx` criado com os 7 símbolos (5 exportados, 2 privados), token de tema `T` local espelhado com os 12 tokens realmente usados pelo bloco movido
- `App.jsx` importa `AiNote`, `SUBLINHADO`, `SetorAlvo`, `ConceitoSheet` do módulo novo; zero call-site alterado; zero mudança de comportamento
- Os 6 guardiões que liam o código por regex sobre `App.jsx` (`test_conceito_ui.mjs`, `test_setor_toque.mjs`, `test_boris_chat.mjs`, `test_fonte_explicacao.mjs`, `test_numeros_fundamentados.mjs`, `test_perfil_reorg.mjs`) reapontados — 21 asserções, contrato intacto, nenhum `ok(` removido sem substituição
- Guardião novo `test_entendimento_modulo.mjs`: exports, isolamento de import, tokens `T.*` vs array `TOKENS` (com prova negativa por injeção), ausência dos 7 símbolos em `App.jsx`, isolamento preservado em `opcoes/OpcoesScreen.jsx`
- Achado real da própria extração corrigido: `zIndex: 86` de `ConceitoSheet` coincidia textualmente com o `zIndex: 86` do `PetSheet` (outro overlay, não movido) — o guardião de "folha acima de todos os overlays" passaria medindo o componente errado; reapontado para `entendimento.jsx`

## Task Commits

Each task was committed atomically:

1. **Task 1: criar web/src/entendimento.jsx e fazer App.jsx importar dele** - `bbab82e` (refactor)
2. **Task 2: reapontar os 6 guardiões + guardião novo da extração** - `5f47f18` (test)

_Nenhum commit de metadados de plano separado nesta execução — SUMMARY commitado pelo orquestrador ao final da onda, per guardrail do repositório (gsd-sdk state.* não é chamado)._

## Files Created/Modified
- `web/src/entendimento.jsx` - módulo novo: AiNote, SUBLINHADO, SetorAlvo, AssistenteBox, ConceitoSheet (+ CONCEITO_BLOCOS/SR_ONLY privados), T local espelhado
- `web/src/App.jsx` - remove os 7 símbolos, importa os 4 usados de `./entendimento.jsx`
- `web/tests/test_conceito_ui.mjs` - 9 asserções reapontadas (inclui o achado do zIndex 86 coincidente)
- `web/tests/test_setor_toque.mjs` - fatia `setorAlvo` passa a vir de `entendimento.jsx`; 2 asserções divididas entre `app`/`ent`
- `web/tests/test_boris_chat.mjs` - 2 asserções de AssistenteBox reapontadas
- `web/tests/test_fonte_explicacao.mjs` - localização de `AiNote`, contagens de não-duplicação (1x em `ent`/0x em `app`), busca de `<AiNote />` "fora de AnalysisView"
- `web/tests/test_numeros_fundamentados.mjs` - 1 asserção de `AssistenteBox`/Markdown reapontada
- `web/tests/test_perfil_reorg.mjs` - marcador de fim do PerfilHub trocado + prova de parse-não-mudo nova
- `web/tests/test_entendimento_modulo.mjs` (novo) - guardião da extração: exports, isolamento, tokens (com prova negativa), ausência em App.jsx

## Decisions Made
- Extração 100% verbatim — nenhuma linha de lógica, prop, string ou estilo mudou; qualquer mudança de comportamento é do 38-03 (fora de escopo deste plano)
- `AssistenteBox` fica exportado mas sem novo import em `App.jsx` — o único consumidor (`ConceitoSheet`) já mora no mesmo módulo
- Guardião de zIndex 86 reapontado mesmo tendo "passado" contra `App.jsx` por engano — a coincidência com o `PetSheet` tornaria o guardião um falso positivo silencioso (risco T-38-07 do threat model do plano), corrigido antes de declarar a task pronta

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comentário de cabeçalho do módulo novo continha o literal "T.x", disparando falso positivo no próprio guardião de tokens**
- **Found during:** Task 2, ao escrever `test_entendimento_modulo.mjs`
- **Issue:** O comentário de cabeçalho de `entendimento.jsx` (escrito na Task 1) usava a frase "nenhum uso de `T.x` muda de valor" como prosa solta — o regex `\bT\.[a-zA-Z0-9]+` do guardião novo capturou esse `T.x` como se fosse um uso real de token, acusando `x` como token faltante no array `TOKENS`
- **Fix:** Reescrita a frase do comentário para não conter o padrão `T.` seguido de identificador (usa "nenhum uso de um token muda de valor")
- **Files modified:** web/src/entendimento.jsx
- **Verification:** `node tests/test_entendimento_modulo.mjs` passou 12/12; `npx vite build` reconfirmado verde após a edição
- **Committed in:** `5f47f18` (parte do commit da Task 2, junto do guardião que revelou o problema)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Correção trivial de comentário, sem efeito em comportamento de runtime. Não houve scope creep.

## Issues Encountered
- Guardião pré-existente `test_conceito_ui.mjs` continha uma asserção que "passava" mesmo depois da extração, mas medindo o componente ERRADO (`PetSheet` em vez de `ConceitoSheet`, ambos com `zIndex: 86`) — não era uma falha visível no loop `for t in tests/*.mjs`, só apareceu ao inspecionar por que a asserção não estava na lista de `FALHOU`. Resolvido reapontando para `entendimento.jsx` com comentário explicando o achado (ver Key Decisions).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `web/src/opcoes/OpcoesScreen.jsx` já pode importar `SetorAlvo`/`ConceitoSheet` de `./entendimento.jsx` no plano 38-05 (D-08), sem ciclo — pré-condição do ROADMAP SC#4 satisfeita
- Suíte canônica confirmada fora do sandbox: **2987 pytest passed / 5 skipped / 3 xfailed / 0 failed** + **156/157 `.mjs`** (única falha: `test_ios_assets.mjs`, ambiental conhecida — `web/ios/` gitignored, `CLAUDE.md:236`). Os mesmos 27 testes de backend que envolvem chamada de rede (Yahoo/Anthropic/OpenAI/benchmark Ibovespa) falharam sob o sandbox padrão (permissão de rede) e passaram limpo ao rodar com o sandbox desabilitado — mesmo padrão documentado no memory do projeto ("sandbox mente"), não regressão desta fase
- `npx vite build` verde nas duas rodadas (após Task 1 e após a correção de comentário na Task 2)
- Nenhum bloqueio para o próximo plano da onda seguinte

---
*Phase: 38-kb-did-tica-ampliada*
*Completed: 2026-09-23*

## Self-Check: PASSED
- FOUND: web/src/entendimento.jsx
- FOUND: web/tests/test_entendimento_modulo.mjs
- FOUND: .planning/phases/38-kb-did-tica-ampliada/38-02-SUMMARY.md
- FOUND commit: bbab82e (Task 1)
- FOUND commit: 5f47f18 (Task 2)
