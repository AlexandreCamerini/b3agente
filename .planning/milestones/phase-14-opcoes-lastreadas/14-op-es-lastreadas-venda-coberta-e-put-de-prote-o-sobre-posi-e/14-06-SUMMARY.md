---
phase: 14-opcoes-lastreadas
plan: 06
subsystem: ui
tags: [options, covered-call, protective-put, react, frontend, copy]

# Dependency graph
requires:
  - phase: 14-opcoes-lastreadas
    plan: "03"
    provides: "GET /api/options/proposta/{ticker}, POST /api/options/lastreada/abrir|fechar (403 Estudo, 502 degradado prontos)"
  - phase: 14-opcoes-lastreadas
    plan: "05"
    provides: "store.optionsProposta/optionsAbrirLastreada/optionsFecharLastreada paritários nos dois stores"
provides:
  - "PropostaLastreada (web/src/App.jsx): card de proposta pronta (venda coberta/put de proteção) dentro do AtivoCard, acima da cadeia expansível"
  - "copy.js: eyebrow/CTA/confirmação das operações lastreadas nos dois modos (Estudo sem vocabulário de ordem)"
  - "A.abrirLastreada/A.fecharLastreada — ações wiring store→UI com flash de sucesso/erro"
  - "myOptionPositionsLegado: filtro que impede a cadeia legada (OpcoesCamada/OpcaoContrato) de expor posições com lastro"
  - "web/tests/test_opcoes_proposta_ui.mjs: guardião de UI (21 asserções)"
affects: [14-07, 14-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Card de proposta reusa a linguagem visual do hero (Display 17/800 para a manchete, Label 10/800 para o eyebrow) sem introduzir componente de design novo — mesmo T token object, mesmo inline style"
    - "Espaçamento 4/8/16/24 aplicado só aos elementos NOVOS desta fase (proposal card); OpcoesCamada/OpcaoContrato mantidos com a escala ad hoc pré-existente, sem retrofit"
    - "Filtro de exposição por capacidade: myOptionPositionsLegado exclui posições com `lastro` do prop passado a um componente que nunca foi adaptado para aquele shape — em vez de adaptar o componente reusado (proibido pelo UI-SPEC), filtra-se o que ele recebe"

key-files:
  created:
    - web/tests/test_opcoes_proposta_ui.mjs
  modified:
    - web/src/copy.js
    - web/src/App.jsx

key-decisions:
  - "PropostaLastreada renderiza null enquanto `r` (opProposta) ainda é null — silêncio, não esqueleto, porque a proposta é secundária ao card do ativo (UI-SPEC)."
  - "Estudo NUNCA recebe o botão de executar: o bloco <button> só existe sob `operador && (...)`; a defesa real continua sendo o 403 do servidor (T-14-23) — a UI é a segunda camada, não a única."
  - "onFechar sempre pede window.confirm (call OU put); onAbrir só pede confirmação para CALL coberta — a PUT de proteção não trava lastro algum, então a confirmação existiria só pelo ritual, sem fato novo a declarar (regra explícita do plano)."
  - "cp.ctaFecharLastreada usa o texto literal do plano ('Recomprar a call — R$ {custo}') mesmo sabendo que posAberta também pode casar com uma PUT — aceito como especificado; o comportamento financeiro (fecharLastreada aceita ambos os sides) é correto independente do texto do botão, é só um ponto de nuance de copy não coberto pelo UI-SPEC."
  - "REGRA 2 (achado durante Task 2, não no plano original): OpcaoContrato nunca foi adaptado para os campos `side`/`lastro` (Plano 02) — seu único botão de venda ('Vender posição') chama A.sellOption → store.sell_option, que credita caixa e NUNCA decrementa qtyTravada. Expor uma posição side='vendida' (CALL coberta) por esse caminho creditaria caixa quando deveria debitar (semântica invertida de fechamento) e estrangularia o lastro permanentemente — o usuário nunca mais conseguiria vender a ação travada. Corrigido filtrando myOptionPositionsLegado = myOptionPositions.filter(p => !p.lastro) antes de passar para OpcoesCamada; toda posição lastreada agora só se gerencia pelo card da proposta (onFechar → fecharLastreada, que passa pelas rotas/store corretos). Não é mudança arquitetural — é um filtro de uma linha no caller, sem tocar OpcoesCamada/OpcaoContrato (que o UI-SPEC proíbe explicitamente modificar)."

requirements-completed: []

# Metrics
duration: ~45min
completed: 2026-08-31
---

# Phase 14 Plan 06: Card de proposta lastreada (venda coberta / put de proteção) na UI Summary

**Componente `PropostaLastreada` no `AtivoCard`: manchete e didática vêm só do motor (`proposta.manchete`/`proposta.didatica`, guardrail CVM), CTA em Modo Operador com confirmação declarando a trava de lastro, texto condicional em Modo Estudo sem nenhum botão de executar, cadeia completa preservada 24px abaixo — e um bug real de integração achado e corrigido: a cadeia legada `OpcoesCamada`/`OpcaoContrato` teria corrompido caixa e travado lastro para sempre se uma posição lastreada vazasse para o botão "Vender posição" dela.**

## Performance

- **Duration:** ~45 min
- **Completed:** 2026-08-31T08:28:40-03:00
- **Tasks:** 3/3
- **Files modified:** 3 (1 criado: `test_opcoes_proposta_ui.mjs`; 2 modificados: `copy.js`, `App.jsx`)

## Accomplishments
- `copy.js`: `eyebrowPropostaCall`/`eyebrowPropostaPut`, `ctaVendaCoberta`/`ctaPutProtecao`, `ctaFecharLastreada`, `confirmAbrirCoberta`/`confirmFecharCoberta`, `verCadeiaCompleta`, `propostaIndisponivelDegradada`, `propostaVaziaTitulo` — chaves idênticas nos dois modos; ramo Estudo devolve texto condicional sem "vender"/"comprar" (guardião `test_copy_theme.mjs` continua verde).
- `PropostaLastreada` (novo componente, `App.jsx`, logo acima de `OpcoesCamada`): estado vazio (`propostaVaziaTitulo` + `motivoTexto`/`propostaIndisponivelDegradada` quando `motivo==="degradado"`), estado populado (eyebrow, manchete Display 17/800 colorida por `optionType` — `T.positive` CALL / `T.negative` PUT, NUNCA `T.accent` —, linha estrutural MONO do contrato, chips do motor, corpo didático em Estudo, CTA em Operador).
- `AtivoCard`: novo `useEffect` busca `store.optionsProposta(t)` só quando `opGate && opGate.liquida` é verdadeiro (D-8 — zero requisição extra sem gate de liquidez); `posAberta` casa a proposta atual com uma posição já aberta pelo `contractSymbol`; `onAbrirLastreada`/`onFecharLastreada` chamam `window.confirm` (trava declarada na abertura de CALL coberta; sempre confirmado no fechamento) antes de `A.abrirLastreada`/`A.fecharLastreada`.
- `A.abrirLastreada`/`A.fecharLastreada`: chamam o store, adotam o estado devolvido com `setData`, repassam mensagem de erro do servidor sem reescrever (403 Modo Estudo, 502 cadeia degradada já vêm prontos).
- `OpcoesCamada` ganha `rotuloFechado` (usa `cp.verCadeiaCompleta` quando existe proposta) — única mudança no componente reusado, conforme o UI-SPEC manda; `OpcaoContrato` inalterado.
- Removido o par morto `A.setOptionStop`/`A.setOptionAlvo` (D-1) — sem uso em nenhuma tela; `putOptionPosition` permanece em `persistence.js` (o agente ainda usa no ciclo do modelo antigo).
- **Achado e corrigido (Regra 2, não estava no plano):** `myOptionPositionsLegado` filtra fora qualquer posição com `lastro` antes de alimentar `OpcoesCamada` — sem isso, uma CALL coberta apareceria com o botão "Vender posição" da cadeia legada, que chama `store.sell_option` (credita caixa, nunca destrava `qtyTravada`) em vez de `fechar_call_coberta` (debita, destrava). Corrupção de caixa + lastro estrangulado permanentemente, sem nenhum teste do plano original cobrindo esse caminho.
- `web/tests/test_opcoes_proposta_ui.mjs` (novo, 21 asserções): chaves de copy espelhadas e sem vocabulário de ordem no Estudo; manchete/didática nunca compostas no front; split de modo (CTA só sob `operador`, didática só sob `!operador`); cadeia preservada e posicionada depois da proposta no JSX; gate de dormência; confirmação da trava nos dois sentidos (abrir/fechar); cor da manchete por polaridade sem `T.accent`; código morto removido.
- Suíte canônica completa verde: `bash scripts/executar.sh --testes` — `1805 passed, 1 skipped` (pytest) + `108/108` `web/tests/*.mjs` `[OK]`; `cd web && npx vite build` verde (2 execuções, antes e depois do guardião de Task 3).

## Task Commits

Each task was committed atomically:

1. **Task 1: Rótulos e confirmações das operações lastreadas em copy.js** - `323fba0` (feat)
2. **Task 2: Componente PropostaLastreada e fiação no AtivoCard** - `5323ffb` (feat)
3. **Task 3: Guardião de UI da proposta** - `2190200` (test)

_Note: nenhuma task era TDD — plano `autonomous: true`, sem checkpoints._

## Files Created/Modified
- `web/src/copy.js` - 10 chaves novas nos dois ramos (eyebrow/CTA/confirmação das operações lastreadas)
- `web/src/App.jsx` - componente `PropostaLastreada`, fiação no `AtivoCard` (estado/efeito/handlers), `A.abrirLastreada`/`A.fecharLastreada`, `rotuloFechado` em `OpcoesCamada`, remoção de `setOptionStop`/`setOptionAlvo`, filtro `myOptionPositionsLegado`
- `web/tests/test_opcoes_proposta_ui.mjs` - guardião novo (copy + UI estática, 21 asserções)

## Decisions Made
- Ver `key-decisions` no frontmatter — decisão central desta entrega é o achado de Regra 2 (filtro `myOptionPositionsLegado`), documentado ali com o raciocínio completo.
- `posAberta` casa pelo `contractSymbol` da proposta ATUAL contra as posições existentes — é um match de "a mesma leitura técnica ainda recomenda o contrato que você já tem", não uma consulta de posição independente; aceito como especificado no plano (não há busca de preço separada para uma posição já aberta que não bate mais com a proposta corrente).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Filtro que impede a cadeia legada de gerenciar posições lastreadas**
- **Found during:** Task 2 (fiação no AtivoCard) — antes de escrever o wiring de `myPositions` passado a `OpcoesCamada`.
- **Issue:** `OpcaoContrato` (reusado sem retrofit, conforme UI-SPEC manda) renderiza `pos ? <button onClick={onSell}>Vender posição</button>` para QUALQUER posição truthy, sem checar `side`/`lastro`. `onSell` chama `A.sellOption` → `store.optionsSell` → `POST /api/options/sell` → `store.sell_option`, que **credita** caixa e nunca toca `qtyTravada`. Para uma posição `side==="vendida"` (CALL coberta), fechar por esse caminho creditaria caixa quando deveria debitar (semântica de "vender para fechar" aplicada a uma posição que precisa "comprar para fechar") e o lastro travado no ativo-objeto nunca seria liberado — o usuário perderia a capacidade de vender aquelas ações permanentemente, sem erro visível.
- **Fix:** `myOptionPositionsLegado = myOptionPositions.filter((p) => !p.lastro)` — só posições SEM o campo `lastro` (modelo antigo, long-only) chegam a `OpcoesCamada`/`OpcaoContrato`. Toda posição lastreada (identificada pela presença de `lastro`, mesmo discriminador que o backend usa) só se gerencia pelo card da proposta, via `onFechar` → `A.fecharLastreada` → `POST /api/options/lastreada/fechar` → `fechar_call_coberta`/`sell_option` com a rota correta.
- **Files modified:** `web/src/App.jsx` (linha do filtro + comentário explicando o porquê, dentro de `AtivoCard`)
- **Verification:** `cd web && npx vite build` verde; `bash scripts/executar.sh --testes` verde (nenhum teste pré-existente cobria esse caminho — o guardião novo (`test_opcoes_proposta_ui.mjs`) não testa isso diretamente por não ter fixture de posição lastreada, mas a mudança não quebrou nenhum teste de paridade/carteira existente).
- **Committed in:** `5323ffb` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 Rule 2 — missing critical functionality)
**Impact on plan:** Correção de escopo estrito ao próprio plano (a fiação de `myPositions` já era tarefa da Task 2); não modifica `OpcoesCamada`/`OpcaoContrato` (proibido pelo UI-SPEC), não introduz componente novo, não é decisão arquitetural. Sem essa correção, a fase entregaria uma trava de lastro (o próprio objetivo da fase) que um caminho de UI não relacionado poderia corromper silenciosamente.

## Issues Encountered
- `server/.venv` e `web/node_modules` ausentes neste worktree (mesmo padrão documentado nos planos 14-01 a 14-05) — resolvido com symlinks temporários para o clone principal (`ln -s`), usados só para rodar a suíte canônica e o `vite build`; removidos antes de cada commit (não aparecem em nenhum `git status`/commit deste plano).
- Nenhum teste automatizado exercita o cenário exato que o achado de Regra 2 corrige (uma posição `side==="vendida"` renderizada dentro de `OpcoesCamada`) — o guardião novo trava o FILTRO (`myOptionPositionsLegado` existe e exclui `lastro`) por leitura estática, mas não simula o fluxo completo de runtime. Registrado aqui para visibilidade; um teste de integração dedicado a esse caminho fica como item potencial para um plano futuro de hardening, não bloqueante para esta entrega.

## User Setup Required

None - nenhuma configuração de serviço externo necessária. A UI depende só das rotas/stores já prontos dos planos 14-03/14-05 (dormentes em produção até `B3_OPTIONS_PROVIDER=mydata`, per 14-CONTEXT.md).

## Next Phase Readiness
- O card de proposta está completo e fiado; próximos planos da fase (14-07/14-08) podem construir em cima sem retrabalho de UI base.
- `myOptionPositionsLegado` é o padrão a seguir se outro componente legado precisar coexistir com o shape lastreado no futuro — documentado no `key-decisions`.
- Publicação pendente: este plano NÃO inclui bump de `web/src/version.js`/`publicar-web.sh` — a fase ainda está atrás do flag `B3_OPTIONS_PROVIDER=mydata` (dormente em produção), então o padrão "fase sem plano de publicação front" não se aplica aqui da mesma forma; confirmar com o Alex se a publicação do build web deve esperar o plano de virada do provider ou se cada wave publica incrementalmente.
- Nenhum bloqueio conhecido para os próximos planos da fase.

---
*Phase: 14-opcoes-lastreadas*
*Completed: 2026-08-31*

## Self-Check: PASSED

- FOUND: web/src/copy.js
- FOUND: web/src/App.jsx
- FOUND: web/tests/test_opcoes_proposta_ui.mjs
- FOUND: .planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/14-06-SUMMARY.md
- FOUND commit 323fba0 (Task 1)
- FOUND commit 5323ffb (Task 2)
- FOUND commit 2190200 (Task 3)
