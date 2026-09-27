---
phase: 39-reestrutura-o-de-navega-o-da-aba-op-es
plan: 03
subsystem: ui
tags: [react, opcoes, curadoria, aria, accessibility, tdd]

# Dependency graph
requires:
  - phase: 39-01
    provides: piso de probabilidade OTM (PISO_PROB_OTM=0.60), probOtm/volatilidadeFonte/premioAnualizado/posicaoNoRanking e meta.candidatosAvaliados/semProbabilidade/pisoProbOtm em server/app/opcoes_curadoria.py, consumidos por este plano
  - phase: 39-02
    provides: vocabulário de copy.js (curadoriaPosicaoRotulo, curadoriaVazioPiso, curadoriaVazioSemProb, curadoriaProbOtmRotulo, curadoriaPremioAnualizadoRotulo, curadoriaVolImplicita, curadoriaVolHistorica), contrato de props (infoBotao/abertoTicker) que este plano consome
provides:
  - CuradoriaEstruturas.jsx com cascata de 5 estados vazios (D-11), posição no ranking em vez de score bruto (D-14), painel inline com chance OTM estimada + fonte da volatilidade + prêmio anualizado (D-08/D-09), botão Executar com T.onAccent (correção AA obrigatória), slot infoBotao (D-13)
  - OportunidadesOpcoes.jsx com aria-expanded={abertoTicker === p.t} e slot infoBotao, pronta para o painel inline do Plano 04, sem mudança de comportamento para quem não passa as props novas
  - Guardião test_curadoria_ui.mjs estendido (bloco "Fase 39, NAV-01") com paridade do piso 60% contra server/app/opcoes_curadoria.py, provas de D-11/D-14/T-39-11 e as 2 asserções de OportunidadesOpcoes
affects: [39-04, 39-05, 39-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED→GREEN aplicado à task de adaptação de componente (não só a features novas de backend) — 16 asserções falharam antes do GREEN, todas nas expectativas dependentes da implementação ainda não escrita"
    - "Reversão deliberada de guardião pré-existente com nota datada (mesmo padrão do 39-02 com opcoesLeituraConcluidaAjuda): item 24 de test_curadoria_ui.mjs passa de 'exatamente 1x' para '0x' quando D-14 remove o score bruto do card por completo"

key-files:
  created: []
  modified:
    - web/src/opcoes/CuradoriaEstruturas.jsx
    - web/src/opcoes/OportunidadesOpcoes.jsx
    - web/tests/test_curadoria_ui.mjs

key-decisions:
  - "A cascata de vazios (D-11) deriva avaliados/semProb/piso de meta SÓ quando typeof === 'number' — backend antigo/degradado sem esses campos cai no ramo genérico (cp.curadoriaVazio), nunca finge ter medido o piso ou a falta de dado (princípio 4 do CLAUDE.md)"
  - "pctFmt(v) é null-safe (typeof v === 'number' && isFinite(v)) e formata só EXIBIÇÃO — probOtm/premioAnualizado já vêm calculados do motor (server/app/opcoes_curadoria.py), o front nunca reconstrói a conta (princípio 5)"
  - "O guardião pré-existente que travava curadoriaRazaoRotulo em 'exatamente 1x' foi revertido com nota datada (2026-09-24, Fase 39/D-14), não apagado — mesmo guardrail de reversão deliberada aplicado no 39-02"

patterns-established:
  - "infoBotao || null como slot opcional de ⓘ contextual — mesmo padrão aplicado nos dois componentes desta task (CuradoriaEstruturas e OportunidadesOpcoes), consumido pelo Plano 04"

requirements-completed: [NAV-01]

# Metrics
duration: ~30min
completed: 2026-09-24
---

# Phase 39 Plan 03: Recomendadas com piso/posição/probOtm + Oportunidades com aria-expanded Summary

**CuradoriaEstruturas.jsx ganha D-11 (cascata de 5 estados vazios: não-medido/erro/sem-probabilidade/sem-piso/genérico), D-14 (posição no ranking substitui o score bruto "Pontuação de curadoria: 0.02"), o painel inline com chance estimada OTM + fonte da volatilidade + prêmio anualizado, e a correção obrigatória de contraste do botão Executar (T.onAccent, nunca "#fff"); OportunidadesOpcoes.jsx ganha aria-expanded e o slot infoBotao — ambos prontos para o painel inline do Plano 04, TDD RED→GREEN com 16 asserções falhando antes da implementação.**

## Performance

- **Duration:** ~30 min
- **Completed:** 2026-09-24T17:11:15Z
- **Tasks:** 2/2
- **Files modified:** 3 (CuradoriaEstruturas.jsx, OportunidadesOpcoes.jsx, test_curadoria_ui.mjs)

## Accomplishments

- `CuradoriaEstruturas.jsx`: cascata de 5 estados (naoMedido < erro < vazioSemProb < vazioPiso < vazioGenérico), cada um nomeando exatamente o motivo — nunca um genérico que esconde o piso de 60% de probabilidade OTM (D-11); a posição no ranking (`cp.curadoriaPosicaoRotulo(cand.posicaoNoRanking, top.length)`) substitui o score bruto no card (D-14); o painel inline mostra `cp.curadoriaProbOtmRotulo` + fonte da volatilidade (implícita/histórica de 21 pregões) e `cp.curadoriaPremioAnualizadoRotulo`, ambos formatados por `pctFmt` null-safe; o botão Executar usa `T.onAccent` em vez de `"#fff"` literal (correção AA obrigatória, mesma razão medida na Fase 35); slot `infoBotao` novo no eyebrow (D-13).
- `OportunidadesOpcoes.jsx`: `aria-expanded={abertoTicker === p.t}` no botão do card e slot `infoBotao` no eyebrow — props opcionais, zero mudança de comportamento para quem não as passa; `onClick={() => onAbrir(p.t)}` intocado (o toggle do painel inline é decisão do pai, Plano 04).
- `test_curadoria_ui.mjs`: bloco "(Fase 39, NAV-01)" com 27 asserções novas — paridade do piso 60% lido de `server/app/opcoes_curadoria.py` (mesmo padrão de `CUSTO_DA_ACAO`/`test_opcoes_custo_declarado.mjs`), chaves função/string novas sem promessa de lucro nem convite ao flag de opção a descoberto, D-14, T.onAccent, infoBotao, painel inline, cascata D-11, guardrail T-39-11 (sem comparação de `premioAnualizado`), e as 2 asserções de `OportunidadesOpcoes.jsx`.
- Handlers preservados byte a byte: `handleExecutar`, `abertoId`, consentimento de liquidez DIFÍCIL, gate `!operador`, payoff do nº 1, narração, `top.map(` na ordem recebida, `onAbrir(item.ticker)` como link secundário exatamente 1x.

## Task Commits

1. **Task 1 (RED): guardião D-11/D-14/onAccent da curadoria** - `fb1b527` (test)
2. **Task 1 (GREEN): Recomendadas com piso, posição no ranking e onAccent** - `f26b7a6` (feat)
3. **Task 2: OportunidadesOpcoes ganha aria-expanded + slot infoBotao** - `ec696f6` (feat)

**Plan metadata:** (a seguir, commit de docs)

## Files Created/Modified

- `web/src/opcoes/CuradoriaEstruturas.jsx` - cascata de 5 estados, posição no ranking, painel com probOtm/prêmio anualizado, T.onAccent, slot infoBotao
- `web/src/opcoes/OportunidadesOpcoes.jsx` - aria-expanded, slot infoBotao
- `web/tests/test_curadoria_ui.mjs` - bloco Fase 39 (27 asserções novas) + item 24 revertido com nota datada

## Decisions Made

- Ver `key-decisions` no frontmatter — cascata de vazios só deriva de campos NÚMEROS de `meta`, `pctFmt` é formatação de exibição pura (nunca recalcula), e o guardião pré-existente da razão bruta foi revertido com nota em vez de apagado.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Guardião pré-existente (item 24, Quick 260915-ndt) travava `curadoriaRazaoRotulo` em "exatamente 1x" — conflitava com D-14**
- **Found during:** Task 1 (RED)
- **Issue:** `test_curadoria_ui.mjs` tinha uma asserção histórica exigindo que `cp.curadoriaRazaoRotulo` aparecesse exatamente 1x no módulo (o card mostrando o score bruto). O Plano 39-03 (D-14) remove essa linha do card por completo, substituindo por `cp.curadoriaPosicaoRotulo`. Sem atualizar o guardião, a suíte ficaria permanentemente vermelha (0x vs "exatamente 1x" exigido).
- **Fix:** Assertion revertida com nota datada (2026-09-24, Fase 39/D-14): passa a exigir 0 ocorrências, comentário histórico preservado acima explicando o motivo da mudança (mesmo padrão do 39-02 com `opcoesLeituraConcluidaAjuda`).
- **Files modified:** `web/tests/test_curadoria_ui.mjs`
- **Verification:** `node web/tests/test_curadoria_ui.mjs` sai 0 depois do GREEN; item 25 (que compara `curadoriaPremioRotulo !== curadoriaRazaoRotulo` em copy.js, não no componente) continua intocado e válido.
- **Committed in:** `fb1b527` (Task 1, commit RED)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug em guardião pré-existente, consequência direta e esperada de D-14 pedido pelo próprio plano)
**Impact on plan:** Necessário para manter a suíte canônica verde; sem mudança de escopo além do que D-14 já pedia.

## Issues Encountered

- Acceptance criteria do Task 2 (`grep -c "tiraOpcoesSemSetup\|tiraOpcoesSemMercado\|tiraOpcoesSemCobertura" web/src/opcoes/OportunidadesOpcoes.jsx` == 3) não bate: `grep -c` conta LINHAS que casam, não ocorrências, e as 3 chaves vivem numa única linha ternária (`{algumLiquido ? cp.tiraOpcoesSemSetup : algumSemMercado ? cp.tiraOpcoesSemMercado : cp.tiraOpcoesSemCobertura}`) — o comando nunca poderia retornar 3, mesmo antes deste plano (confirmado com `git show` do commit anterior a esta task: já era 2). Não é uma regressão desta task nem uma remoção de variante — o invariante substantivo ("3 variantes distintas, nenhuma sumiu") está coberto por `test_carteira_opcoes_tira.mjs` (asserções de `tiraOpcoesSemCobertura`/`tiraOpcoesSemSetup`/`tiraOpcoesSemMercado`, todas presentes e distintas nos dois modos), que passou sem alteração. Erro de redação da acceptance criteria do plano, não do código — documentado, não corrigido silenciosamente.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `CuradoriaEstruturas.jsx` e `OportunidadesOpcoes.jsx` prontos para o Plano 04 (montagem das 3 abas fixas): ambos aceitam `infoBotao` (slot D-13), `OportunidadesOpcoes` aceita `abertoTicker` para o painel inline que o Plano 04 monta.
- Suíte canônica web (`web/tests/*.mjs`, 157 arquivos) e `npx vite build` (116 módulos) verdes, sem regressão. Backend não foi tocado por este plano (nenhum arquivo `server/app/*.py` no `files_modified`).
- TDD gate: commit `test(...)` (RED, `fb1b527`) seguido de `feat(...)` (GREEN, `f26b7a6`) confirmado no git log — gate de sequência cumprido.

---
*Phase: 39-reestrutura-o-de-navega-o-da-aba-op-es*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: `web/src/opcoes/CuradoriaEstruturas.jsx`
- FOUND: `web/src/opcoes/OportunidadesOpcoes.jsx`
- FOUND: `.planning/phases/39-reestrutura-o-de-navega-o-da-aba-op-es/39-03-SUMMARY.md`
- FOUND commit `fb1b527` (Task 1, RED)
- FOUND commit `f26b7a6` (Task 1, GREEN)
- FOUND commit `ec696f6` (Task 2)
- Suíte web completa fora do sandbox: 157/157 `.mjs`, 0 falhas; `npx vite build` limpo (116 módulos)
