---
phase: 04-corre-o-m-dio-storyline-ux
plan: 05
subsystem: ui
tags: [react, disclaimers, transparency, portfolio, history, ai-labeling]

# Dependency graph
requires:
  - phase: 04-03
    provides: "textFaint WCAG AA corrigido, acordeão acessível, nudge de prontidão — App.jsx estável para novas edições nos mesmos componentes vizinhos"
provides:
  - "DISCLAIMERS.trade renderizado em BuyModal/SellModal, acima do botão de confirmar (defeito de renderização fechado)"
  - "declaração tudo-ou-nada nos dois modais + CLAUDE.md (Modelo de simulação)"
  - "AiNote com prop source (ia|deterministico) — explicação sem IA nunca rotulada como conteúdo de IA"
  - "AnalysisView consumindo an.fonte/an.iaIndisponivel/an.semDados do contrato de backend (04-04)"
  - "HistoricoScreen mostrando ordem rejeitada (pill neutra + badge REJEITADA + motivo), sem zero fabricado"
  - "deviceStore com paridade completa: rejeição local espelhando store.py.registrar_rejeicao"
affects: [04-06, 04-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "helper privado dentro de deviceStore() que NÃO chama write() (mesmo padrão de _sellOptionLocal) — o chamador grava depois de invocar, um único ponto de persistência por operação; evita falso-positivo no guardião genérico de paridade (test_fase3_paridade_stores_generica.mjs), que escaneia todo o corpo de deviceStore() por indentação e capturaria um write() bare como 'método novo só no device'"

key-files:
  created:
    - web/tests/test_disclaimer_trade_modal.mjs
    - web/tests/test_fonte_explicacao.mjs
    - web/tests/test_historico_rejeitada.mjs
  modified:
    - web/src/App.jsx
    - web/src/persistence.js
    - CLAUDE.md

key-decisions:
  - "_registrarRejeicaoLocal não chama write() internamente — segue o precedente já existente de _sellOptionLocal (write() é responsabilidade do chamador), evitando um falso-positivo no guardião de paridade genérico que interpretou um write() solto em profundidade de 4 espaços como um 'método novo' do deviceStore"
  - "motivo da rejeição local usa a MESMA string do Error lançado (não uma frase nova) — consistência garantida por construção (uma única const motivo usada nos dois lugares), já que a frase exata usada pelo backend em main.py está sendo decidida no Plano 04-04, executado em paralelo neste mesmo wave"

patterns-established:
  - "guardião estático localiza blocos de função por par de índices (`function X(` até o próximo `function Y(`/`export default function`) e escaneia com regex/substring dentro da fatia — mesmo padrão de test_prontidao_operador.mjs (04-03), aplicado três vezes neste plano"

requirements-completed: [FIX-C13, FIX-C14, FIX-C01, FIX-C02]

# Metrics
duration: ~25min
completed: 2026-08-22
---

# Phase 4 Plan 5: Transparência no ponto de decisão + rótulo de fonte + rastro de rejeição Summary

**Disclaimer de operação simulada e declaração tudo-ou-nada plugados nos dois modais de trade, AiNote deixa de afirmar "conteúdo de IA" sobre texto determinístico, e uma ordem rejeitada agora aparece no histórico com pill neutra + motivo, na web e no app nativo.**

## Performance

- **Duration:** ~25min
- **Started:** 2026-08-21T22:58:00Z (aprox.)
- **Completed:** 2026-08-21T23:12:00Z (aprox.)
- **Tasks:** 3/3 completas
- **Files modified:** 6 (3 fonte, 3 testes novos)

## Accomplishments
- FIX-C13/FIX-C14: `DISCLAIMERS.trade` (já existia em `disclaimers.js`, nunca renderizado) agora aparece nos dois modais, acima do botão de confirmar — defeito de renderização puro, zero copy nova. A nota secundária de ambos ganhou uma 2ª sentença declarando execução tudo-ou-nada; `CLAUDE.md` (Modelo de simulação) registra a decisão citando C-14/ROADMAP v1.1. Nenhum código de fill parcial foi escrito.
- FIX-C01 (front): `AiNote` ganhou `source` ("ia" default | "deterministico"), com copy exata do UI-SPEC para o caso sem IA. `AnalysisView` deriva `source` de `an.fonte`, mostra a nota "IA indisponível agora..." quando `an.iaIndisponivel`, e a frase mandatória do CLAUDE.md quando `an.semDados` (ou corpo vazio no caminho determinístico) — sempre pelo mesmo `<Markdown>`, nunca um contêiner degradado. `deviceStore.analyze` persiste `fonte`/`iaIndisponivel`/`verbetes`/`semDados` (o ramo `reaproveitada` já preservava via spread).
- FIX-C02 (front): `HistoricoScreen` mostra ordem rejeitada com pill neutra (`T.textFaint`/`T.bgPanel`, nunca `T.negative`) + badge `REJEITADA` (`T.warn`), `—` em RESULTADO/PREÇO em vez de zero fabricado, e sub-linha `Rejeitada: {motivo}` no mesmo padrão do `ultimoErro` das pendentes. `confirmBuy`/`confirmSell` fazem refresh best-effort (`store.getState()`) no `catch`, antes do `flash`. `deviceStore` ganhou `_registrarRejeicaoLocal` (espelho de `store.py.registrar_rejeicao`, `CAP_REJEICOES_LOCAL = 100`), chamado antes de cada `throw` do ramo local de `buy`/`sell`; entradas de sucesso locais agora gravam `status: "executada"`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Disclaimer de operação simulada e declaração tudo-ou-nada nos modais (FIX-C13, FIX-C14)** - `e46ee60` (feat)
2. **Task 2: AnalysisView e AiNote cientes da fonte da explicação (FIX-C01, front)** - `14de8bd` (feat)
3. **Task 3: Ordem rejeitada visível no histórico, nos dois stores (FIX-C02, front)** - `148bea1` (feat)

_Nenhuma task era TDD — sem commits test→feat separados._

## Files Created/Modified
- `web/src/App.jsx` — `DISCLAIMERS.trade` + frase tudo-ou-nada em `BuyModal`/`SellModal`; `AiNote` com prop `source`; `AnalysisView` consumindo `an.fonte`/`an.iaIndisponivel`/`an.semDados`; `HistoricoScreen` com pill/badge/sub-linha de rejeição; refresh no `catch` de `confirmBuy`/`confirmSell`
- `web/src/persistence.js` — `deviceStore.analyze` persiste `fonte`/`iaIndisponivel`/`verbetes`/`semDados`; novo helper `_registrarRejeicaoLocal` + `CAP_REJEICOES_LOCAL`; `buy`/`sell` locais gravam rejeição antes do throw e `status: "executada"` no sucesso
- `CLAUDE.md` — item novo na lista "O sistema mantém" (Modelo de simulação) declarando execução tudo-ou-nada, citando C-14/ROADMAP v1.1
- `web/tests/test_disclaimer_trade_modal.mjs` (novo) — guardião estático de FIX-C13/C14
- `web/tests/test_fonte_explicacao.mjs` (novo) — guardião estático de FIX-C01 (front)
- `web/tests/test_historico_rejeitada.mjs` (novo) — guardião estático de FIX-C02 (front)

## Decisions Made

- **`_registrarRejeicaoLocal` não chama `write()` internamente.** A primeira versão chamava `write()` dentro do helper, mas isso quebrou `test_fase3_paridade_stores_generica.mjs`: o guardião genérico de paridade escaneia TODO o corpo de `deviceStore()` (a partir do primeiro `return {` que encontra — que por acidente é o de `pub()`, não o do objeto retornado de fato) procurando linhas com indentação de exatamente 4 espaços que pareçam `nome(`. Um `write();` solto a essa profundidade foi capturado como "método novo só no deviceStore". A correção seguiu o precedente já existente de `_sellOptionLocal` (linha ~390 do arquivo): o helper NÃO persiste sozinho, o chamador (`buy`/`sell`) chama `write()` explicitamente logo após invocar o helper e antes do `throw`. Comportamento observável idêntico ao pedido pelo plano ("chama write() e SÓ ENTÃO lança o erro"), só a divisão de responsabilidade mudou.
- **`motivo` da rejeição local usa a mesma string do `Error` lançado**, via uma única `const motivo` reaproveitada nos dois lugares — garante consistência por construção. O plano pedia "mesma frase do backend", mas a frase exata que `main.py` vai usar em `/api/buy`/`/api/sell` está sendo decidida no Plano 04-04 (rodando em paralelo, worktree separado, sem merge ainda neste ponto) — não havia como ler o valor real. Ficou documentado aqui para o caso de a Fase 4 precisar de um ajuste de string fina após o merge dos dois planos.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Falso-positivo no guardião de paridade genérico causado por `write()` solto**
- **Found during:** Task 3 (implementação de `_registrarRejeicaoLocal`)
- **Issue:** a implementação literal do plano (helper chamando `write()` internamente) fazia `test_fase3_paridade_stores_generica.mjs` reportar `write` como método existente só no `deviceStore` — falso-positivo do próprio guardião (ele varre por indentação, não por AST real), mas ainda assim quebrava a suíte canônica
- **Fix:** helper não persiste sozinho; `buy()`/`sell()` chamam `write()` explicitamente após `_registrarRejeicaoLocal(...)` e antes do `throw` — mesmo padrão já usado por `_sellOptionLocal`
- **Files modified:** web/src/persistence.js
- **Verification:** `test_fase3_paridade_stores_generica.mjs` volta a reportar server=60/device=60, todas as 5 checagens OK; suíte canônica completa (1300 pytest + 92 web/tests) verde
- **Committed in:** 148bea1 (Task 3 commit)

---

**Total deviations:** 1 auto-fixado (1 bug).
**Impact on plan:** O auto-fix não mudou nenhum comportamento observável do usuário (rejeição continua gravada e persistida antes do throw); só reorganizou QUEM chama `write()`, seguindo um padrão já estabelecido no mesmo arquivo. Nenhum scope creep.

## Issues Encountered

- Este worktree não tinha `web/node_modules` instalado (mesmo achado do 04-03 — worktrees não compartilham `node_modules` do clone principal); rodei `npm ci` em `web/` antes do primeiro `npx vite build`. Não afeta o clone principal nem outros worktrees.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Os 4 requirements (FIX-C13, FIX-C14, FIX-C01, FIX-C02) estão fechados e testados no lado front; suíte canônica completa (`bash scripts/executar.sh --testes`) verde: 1300 passed / 1 skipped (pytest) + 92/92 web/tests OK, incluindo os 3 novos guardiões deste plano.
- Este plano rodou em paralelo com o Plano 04-04 (backend: fallback determinístico FIX-C01, wiring de `registrar_rejeicao` em `/api/buy`/`/api/sell`), em worktrees separados sem overlap de arquivos. Depois do merge dos dois, vale conferir ao vivo que `an.fonte`/`an.iaIndisponivel`/`h.status`/`h.motivo` realmente chegam do jeito que este plano assume (o contrato foi lido do 04-04-PLAN.md, não verificado contra código já mesclado).
- Nenhum bloqueio para os planos seguintes da Fase 4 (04-06, 04-07) — este plano não tocou `server/`, e as mudanças em `App.jsx`/`persistence.js` são isoladas aos componentes/métodos citados acima.

---
*Phase: 04-corre-o-m-dio-storyline-ux*
*Completed: 2026-08-22*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/src/persistence.js
- FOUND: CLAUDE.md
- FOUND: web/tests/test_disclaimer_trade_modal.mjs
- FOUND: web/tests/test_fonte_explicacao.mjs
- FOUND: web/tests/test_historico_rejeitada.mjs
- FOUND commit: e46ee60
- FOUND commit: 14de8bd
- FOUND commit: 148bea1
