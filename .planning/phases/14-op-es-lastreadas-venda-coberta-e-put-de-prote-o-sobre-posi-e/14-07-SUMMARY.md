---
phase: 14-opcoes-lastreadas
plan: 07
subsystem: ui
tags: [options, covered-call, protective-put, portfolio, react, frontend, copy]

# Dependency graph
requires:
  - phase: 14-opcoes-lastreadas
    plan: "05"
    provides: "finance.js qtyLivre (fonte única) e portfolioMetrics(...optionPositions, optionQuotes) — assinatura estendida usada aqui"
  - phase: 14-opcoes-lastreadas
    plan: "06"
    provides: "PropostaLastreada/myOptionPositionsLegado no AtivoCard — este plano fecha o laço do lado da Carteira, sem tocar o card de proposta"
provides:
  - "TravaPill (web/src/App.jsx): badge de trava de lastro, renderizado no card de posição da CarteiraScreen e no AtivoCard (hero, ao lado do PosPill)"
  - "SellModal/A.openSell limitados a qtyLivre(pos) — nunca pos.qty; livre === 0 desabilita o confirmar; aviso explicativo quando há trava"
  - "AvisoLiquidacao + eventoLiquidacaoRecente: banner de estado (sem CTA) quando uma CALL coberta foi liquidada por vencimento"
  - "Patrimônio Total com as pernas lastreadas: as 7 chamadas de portfolioMetrics em App.jsx passam data.optionPositions; linha discriminando m.opcoesVal na Carteira"
  - "copy.js: badgeTravada/avisoTravaNaVenda/avisoLiquidacaoForcada/linhaPatrimonioOpcoes nos dois modos"
  - "web/tests/test_carteira_lastro_ui.mjs: guardião de UI (28 asserções)"
affects: [14-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TravaPill reusa a forma de PosPill (pílula 999px, 10.5px/800) com T.negative em vez de T.accent — mesmo padrão de badge, cor invertida por comunicar restrição"
    - "AvisoLiquidacao segue o padrão de banner informativo já usado por 'análise de outro momento' (borda tracejada/estado), adaptado com borda T.negative + texto T.textSecondary (nunca o texto inteiro em vermelho — CLAUDE.md, resultado sem manipulação visual)"
    - "eventoLiquidacaoRecente busca só nas ÚLTIMAS 30 entradas do histórico (não o array inteiro) — evita que um evento de liquidação antigo vire um aviso permanente na tela; Claude's Discretion per UI-SPEC (o contrato não define a janela de busca)"

key-files:
  created:
    - web/tests/test_carteira_lastro_ui.mjs
    - .planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/deferred-items.md
  modified:
    - web/src/App.jsx
    - web/src/copy.js

key-decisions:
  - "As chamadas de portfolioMetrics em App.jsx são SETE, não seis — a interface do plano (linhas 1640/1802/3659/7933/8106/8129) estava desatualizada; finance.js já documentava 'os 7 sites em App.jsx' desde o plano 14-05 (comentário no cabeçalho de portfolioMetrics). Todas as 7 foram atualizadas para passar data.optionPositions; a acceptance_criteria literal do plano ('retorna 6') foi superada pela contagem real — o guardião de Task 3 trava o valor real (7), não o número stale do plano."
  - "avisoLiquidacaoForcada(ticker, valor): `valor` é o valor intrínseco POR AÇÃO (h.price do histórico, já é essa grandeza no backend — server/app/store.py:fechar_call_coberta_vencida), não qty×price. Claude's Discretion explícita do UI-SPEC ('a fórmula exata de {valor} é Claude's Discretion')."
  - "AvisoLiquidacao e a 2ª TravaPill (a de 'card de posição da Carteira') foram colocados no card da CarteiraScreen (não no AtivoCard) — é literalmente a tela 'posição de ação' que o Task 2 descreve, e onde o Patrimônio Total já é discriminado; a 1ª TravaPill vai no AtivoCard (hero, ao lado do PosPill), como o plano pede explicitamente."
  - "linhaPatrimonioOpcoes só foi renderizada na CarteiraScreen, não na Evolução — a acceptance_criteria só exige 'opcoesVal aparece 1x ou mais' em App.jsx; a Carteira é onde a composição do patrimônio já é discriminada em KPIs (PATRIMÔNIO TOTAL / EM POSIÇÕES), a superfície mais direta para a ressalva de marcação."
  - "A.confirmSell (toast de venda) NÃO foi alterado — seu `total` interno continua comparando contra pos.qty (não livre): com trava ativa, vender o máximo livre nunca fecha a posição por completo (sobra a parte travada), então dizer 'venda total' seria uma imprecisão visual que o CLAUDE.md proíbe (resultado sem manipulação visual). O servidor (store.py:sell) já vende exatamente `qty_livre(pos)` quando chamado sem qty explícita — comportamento correto preservado, só o rótulo do toast fica mais conservador."

requirements-completed: []

# Metrics
duration: ~40min
completed: 2026-08-31
---

# Phase 14 Plan 07: Trava visível na Carteira, aviso de liquidação e patrimônio com pernas lastreadas Summary

**A trava de lastro que já existia no motor desde o plano 14-01 finalmente aparece na tela: badge nas duas superfícies, venda de ação limitada à quantidade LIVRE (importada de `finance.js`, nunca recalculada), aviso de liquidação forçada como estado do sistema (sem CTA), e o Patrimônio Total passando a contar as pernas de opção lastreadas nas 7 (não 6, como o plano assumia) chamadas de `portfolioMetrics` — com a ressalva de marcação pelo prêmio de abertura sempre dita, nunca omitida.**

## Performance

- **Duration:** ~40 min
- **Completed:** 2026-08-31T09:08:27-03:00
- **Tasks:** 3/3
- **Files modified:** 4 (2 modificados: `App.jsx`, `copy.js`; 2 criados: `test_carteira_lastro_ui.mjs`, `deferred-items.md`)

## Accomplishments

- `TravaPill` (novo componente, espelha `PosPill`): renderizado no card de posição da `CarteiraScreen` (junto do resumo cotas/PM) e no `AtivoCard` (hero, ao lado do `PosPill`), sempre que `qtyTravada > 0`. Texto vem de `cp.badgeTravada(qty)`.
- `SellModal`: `qtyLivre(pos)` importada de `finance.js` (fonte única, gêmea de `store.qty_livre`) vira o teto em TODOS os pontos que antes usavam `pos.qty` — cálculo de `qty`, `step`, botão "Vender tudo (N)", e a definição de "venda total" (agora = vender tudo o que está livre). `livre === 0` desabilita o botão de confirmar; linha explicativa (`cp.avisoTravaNaVenda`) aparece quando há trava. `A.openSell` monta `{t, qty: qtyLivre(pos)}`. Stop/alvo intocados — guardrail "proteção nunca é vetada" preservado e travado por teste.
- `AvisoLiquidacao` + `eventoLiquidacaoRecente`: banner de estado (sem botão) no card da posição de ação, derivado das últimas 30 entradas de `data.history` com `kind==="opcao"`, `motivo==="vencimento"`, `origem==="sistema"`, `acao==="fechar"`. Texto ITM/OTM verbatim do UI-SPEC, `T.negative` só no ícone/borda, texto em `T.textSecondary`.
- Patrimônio: as **7** chamadas de `portfolioMetrics` em `App.jsx` (não 6 — ver `key-decisions`) passam `data.optionPositions`; `optionQuotes` (6º arg) fica `undefined` por decisão do plano 14-05 (orçamento do mydata). Carteira ganha uma linha discriminando `m.opcoesVal` com a ressalva de marcação pelo prêmio de abertura (`cp.linhaPatrimonioOpcoes`).
- `copy.js`: `badgeTravada`/`avisoTravaNaVenda`/`avisoLiquidacaoForcada`/`linhaPatrimonioOpcoes` nos dois modos — Estudo evita "vender"/"comprar" (usa "recomprada", que não contém o infinitivo "comprar" como substring); `avisoLiquidacaoForcada`/`linhaPatrimonioOpcoes` são idênticos nos dois modos (system notice, não voz de professor/mesa).
- `web/tests/test_carteira_lastro_ui.mjs` (novo, 28 asserções): TravaPill em duas superfícies; fonte única de `qtyLivre` (import + duas asserções negativas contra subtração escrita à mão, inclusive `const livre = <subtração>`); `SellModal` sem `Math.min(pos.qty`; `A.openSell` via `qtyLivre(pos)`; stop/alvo nunca desabilitados por `qtyTravada`; as 7 chamadas de `portfolioMetrics` com `optionPositions`; `AvisoLiquidacao` sem `<button`; chaves de copy espelhadas e sem vocabulário de ordem no Estudo.
- Suíte canônica completa verde: `bash scripts/executar.sh --testes` — `1805 passed, 1 skipped` (pytest) + todos os `web/tests/*.mjs` `[OK]` (incluindo o novo guardião e os dois irmãos do plano 06); `cd web && npx vite build` verde.

## Task Commits

Each task was committed atomically:

1. **Task 1: Trava visível — badge na Carteira e venda limitada à quantidade livre** - `d4ad0a2` (feat)
2. **Task 2: Aviso de liquidação forçada e Patrimônio com as pernas lastreadas** - `1207cb6` (feat)
3. **Task 3: Guardião da Carteira lastreada** - `182a2fd` (test)

_Note: nenhuma task era TDD — plano `autonomous: true`, sem checkpoints._

## Files Created/Modified
- `web/src/App.jsx` - `TravaPill`, `AvisoLiquidacao`, `eventoLiquidacaoRecente`, `SellModal`/`A.openSell` via `qtyLivre`, 7 call sites de `portfolioMetrics`, linha de patrimônio de opções na `CarteiraScreen`
- `web/src/copy.js` - 4 chaves novas nos dois ramos (`badgeTravada`/`avisoTravaNaVenda`/`avisoLiquidacaoForcada`/`linhaPatrimonioOpcoes`)
- `web/tests/test_carteira_lastro_ui.mjs` - guardião novo (28 asserções)
- `.planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/deferred-items.md` - 2 falhas de pytest fora de escopo, registradas

## Decisions Made
Ver `key-decisions` no frontmatter — decisão central desta entrega é a correção do número de call sites de `portfolioMetrics` (7, não 6), já que o próprio `finance.js` (plano 14-05) documentava esse número desde antes deste plano ser escrito.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug no plano] Contagem de call sites de `portfolioMetrics` desatualizada (6 → 7)**
- **Found during:** Task 2, antes de editar o 1º call site.
- **Issue:** O plano (`<interfaces>` e `acceptance_criteria`) afirma "seis chamadas de portfolioMetrics (linhas 1640, 1802, 3659, 7933, 8106, 8129)" e pede `grep -c "portfolioMetrics(" web/src/App.jsx` == 6. A leitura do código mostrou 7 ocorrências reais; o próprio `finance.js` (comentário de cabeçalho de `portfolioMetrics`, escrito no plano 14-05) já dizia "os 7 sites em App.jsx continuam passando só 4" — a contagem correta é uma decisão herdada de um plano anterior, não uma descoberta nova; o 14-07-PLAN.md simplesmente não foi atualizado com esse número.
- **Fix:** Todas as 7 chamadas (incluindo a 7ª, dentro de `petSnapshot` caso `"evolucao"`, que o plano não listava) foram atualizadas para passar `data.optionPositions`. O guardião de Task 3 trava a contagem REAL (`chamadas.every(...)`), não um número fixo — não hardcoda "6" nem "7", então continua correto se um 8º call site aparecer no futuro.
- **Files modified:** `web/src/App.jsx` (linhas 8320/8330 — as duas ocorrências dentro de `petSnapshot` — além das 5 já esperadas pelo plano)
- **Verification:** `cd web && npx vite build` verde; `grep -c "portfolioMetrics([^)]*optionPositions" web/src/App.jsx` → 7; `bash scripts/executar.sh --testes` verde.
- **Committed in:** `1207cb6` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 Rule 1 — contagem desatualizada no plano, não um bug de código)
**Impact on plan:** Nenhum impacto arquitetural. O objetivo do plano ("Patrimônio Total exibido inclui as pernas lastreadas") é mais completo COM a correção — sem ela, o resumo do Boris (pet) na aba Carteira/Evolução mostraria um patrimônio sem as pernas de opção, inconsistente com a Carteira e a Evolução.

## Issues Encountered

- 2 falhas de `pytest` (`test_reuso_analise_n2.py`, `test_rotas_fase4.py`) apareceram numa das execuções da suíte completa, mas passam limpas quando rodadas isoladas (44/44) e numa reexecução completa posterior (1805 passed, 0 failed). Este plano não tocou nenhum arquivo em `server/` — confirmado por `git diff --stat HEAD~2 HEAD -- server/` vazio nos dois commits de código. Fora de escopo (SCOPE BOUNDARY); registrado em `deferred-items.md` para investigação futura (padrão de poluição de estado global entre arquivos de teste, não relacionado a opções lastreadas).
- `server/.venv` e `web/node_modules` ausentes neste worktree (mesmo padrão dos planos 14-01 a 14-06) — resolvido com symlinks temporários para o clone principal, removidos antes de cada commit (não aparecem em nenhum `git status`/commit deste plano).

## User Setup Required

None - nenhuma configuração de serviço externo necessária. A UI depende só do estado (`positions[].qtyTravada`, `optionPositions[].lastro`, `data.history`) já produzido pelos planos 14-01/14-02/14-05, e do card de proposta do plano 14-06 (não modificado aqui).

## Next Phase Readiness
- A trava de lastro, o aviso de liquidação e o patrimônio com pernas lastreadas estão completos e testados; o plano 14-08 (próximo da fase) pode assumir que a Carteira já reflete o estado real de qualquer posição lastreada.
- Publicação pendente: este plano NÃO inclui bump de `web/src/version.js`/`publicar-web.sh` — a fase segue atrás do flag `B3_OPTIONS_PROVIDER=mydata` (dormente em produção), mesmo padrão registrado no `14-06-SUMMARY.md`; confirmar com o Alex se a publicação espera a virada do provider ou se cada wave publica incrementalmente.
- Nenhum bloqueio conhecido para o plano 14-08.

---
*Phase: 14-opcoes-lastreadas*
*Completed: 2026-08-31*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/src/copy.js
- FOUND: web/tests/test_carteira_lastro_ui.mjs
- FOUND: .planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/deferred-items.md
- FOUND: .planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/14-07-SUMMARY.md
- FOUND commit d4ad0a2 (Task 1)
- FOUND commit 1207cb6 (Task 2)
- FOUND commit 182a2fd (Task 3)
