---
phase: 14-opcoes-lastreadas
plan: 08
subsystem: web
tags: [options, covered-call, protective-put, radar, bugfix, vm-parity, guardian-test]

# IMPORTANT — scope note
# This SUMMARY covers a SECOND targeted bugfix found by the developer (Alex)
# during Task 2 (checkpoint:human-verify) of plan 14-08 — the live UI
# verification step, after the FIRST bug (proposta_fechar, backend,
# 14-08-TASK2-BUGFIX-SUMMARY.md) was already fixed and re-tested. It is NOT
# a new plan; it is a single atomic bugfix commit against the same phase,
# executed outside the plan's task structure per explicit executor
# instructions (STATE.md/ROADMAP.md are NOT updated by this executor — the
# orchestrator owns those writes).

# Dependency graph
requires:
  - phase: 14-opcoes-lastreadas
    plan: "06"
    provides: "PropostaLastreada — sub-componente de AtivoCard que lê cp.propostaVaziaTitulo/cp.badgeTravada/etc a partir de vm.cp, sem guarda de undefined"
  - phase: 14-opcoes-lastreadas
    plan: "08"
    provides: "achado ao vivo do bug (Task 2, checkpoint humano) — este commit é o fix"
provides:
  - "radarVm (RadarScreen, App.jsx ~6334) inclui cp — paridade com o vm da Watchlist (MercadoScreen, App.jsx ~3699)"
  - "guardião estrutural (web/tests/test_opcoes_proposta_ui.mjs) que mede paridade de campos de vm entre os dois call sites de AtivoCard, escopado ao bloco opGate.liquida (o único trecho da AtivoCard que roda incondicionalmente para as duas telas)"
affects: [14-08-task-2-checkpoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guardião estrutural por parsing estático de App.jsx (mesmo estilo de test_wiring_deps.mjs e test_vocabulario_espelho.mjs): extrai nomes de campos por regex/balanceamento de chaves em vez de listar campos à mão, para pegar a PRÓXIMA ocorrência da mesma classe de bug sem precisar saber o nome do campo de antemão."

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_opcoes_proposta_ui.mjs

key-decisions:
  - "O fix em si é de UM campo só (cp: ctx.cp, na verdade cp em shorthand — já estava em escopo em RadarScreen por const { data, cp } = ctx;) — MercadoScreen não foi tocado (já estava correto)."
  - "O guardião NÃO mede paridade nos 32 campos inteiros do destructuring de vm em AtivoCard — só nos campos efetivamente LIDOS dentro do bloco opGate.liquida (que embala PropostaLastreada/OpcoesCamada), porque investigação confirmou que os outros 11 campos ausentes em radarVm (an fora do bloco de anVencida, rrPos, diasPos, pctCapPos, os, buyMeta, expanded, opsOpen, opsSpark, onToggleOps) são legitimamente watchlist-only por desenho: só são lidos dentro da cauda `{!opOpen && (children || (<>...</>))}`, e o Radar SEMPRE passa children, então esse ramo nunca avalia lá. Medir paridade nesses 11 campos deixaria a suíte permanentemente vermelha sem nenhum bug real — falso positivo, não regressão."
  - "Verificação empírica de que o guardião pega a regressão: revertido manualmente o campo cp de radarVm, rodado o teste isolado (FALHOU no assert de paridade), restaurado o fix, teste voltou a passar. Documentado no teste."
  - "Extensão do arquivo test_opcoes_proposta_ui.mjs (já existente, já cobre o contrato cp/PropostaLastreada) em vez de arquivo novo — é o teste mais relacionado ao bug (checado antes, junto com test_radar.mjs, conforme instrução da task)."

requirements-completed: []

# Metrics
duration: ~50min
completed: 2026-08-31
---

# Phase 14 Plan 08 (Task 2 bugfix #2): radarVm sem cp derrubava todo card do Radar

**`radarVm` (RadarScreen) não incluía `cp` — `AtivoCard`/`PropostaLastreada` lê `cp.propostaVaziaTitulo` sem guarda, e todo card do Radar quebrava com `undefined is not an object (evaluating 'cp2.propostaVaziaTitulo')`; fix de um campo + guardião estrutural que mede paridade de vm entre Watchlist e Radar no único trecho de AtivoCard que roda incondicionalmente para as duas telas.**

## Performance

- **Duration:** ~50min
- **Completed:** 2026-08-31
- **Tasks:** 1 (bugfix atômico, fora da estrutura de tasks do plano — ver nota de escopo no topo)
- **Files modified:** 2 (1 código, 1 teste — guardião estrutural novo dentro de arquivo existente)

## Accomplishments

- **Bug reproduzido e confirmado por leitura de código**: `AtivoCard` (`web/src/App.jsx`, função em ~3119) desestrutura `cp` de `vm` (linha 3120) e repassa incondicionalmente para `<PropostaLastreada cp={cp} .../>` sempre que `opGate && opGate.liquida` (linha 3397-3417) — sem checar `cp` truthy antes. `PropostaLastreada` (Plano 14-06) lê `cp.propostaVaziaTitulo`/`cp.badgeTravada`/etc dentro dessa árvore. `AtivoCard` é COMPARTILHADO entre `MercadoScreen` (Watchlist, ~3699) e `RadarScreen` (Radar, ~6334) — comentário no próprio código confirma a intenção ("o mesmo card serve Watchlist e Radar"). O `vm` da Watchlist ganhou `cp` no Plano 14-06; `radarVm` nunca ganhou. Resultado: todo card do Radar renderizava com `cp === undefined`, e o primeiro acesso `cp.algumaCoisa` dentro de `PropostaLastreada` derrubava o componente — exatamente o erro reportado ao vivo pelo Alex ("a mesa continua sem funcionar", `undefined is not an object (evaluating 'cp2.propostaVaziaTitulo')`).
- **Fix**: adicionado `cp` (shorthand — já estava em escopo em `RadarScreen` via `const { data, cp } = ctx;`, linha 6106) ao literal de `radarVm` (linha 6334), no mesmo padrão que `MercadoScreen` já usa (`cp` desestruturado de `ctx`, repassado como shorthand no `vm`). `MercadoScreen` não foi tocado.
- **Guardião estrutural novo** (`web/tests/test_opcoes_proposta_ui.mjs`): parseia estaticamente (sem build) o destructuring de `vm` em `AtivoCard`, localiza o bloco `{opGate && opGate.liquida && (...)}` (único trecho que renderiza incondicionalmente para as DUAS telas — a "cauda" watchlist-only vive atrás de `!opOpen && (children || (<>...))`, sempre pulada em Radar porque a tela sempre passa `children`), extrai os campos de `vm` efetivamente lidos ali (`t`, `q`, `cur`, `decColor`, `operador`, `cp`) e verifica paridade contra as chaves dos dois objetos-literais que constroem `vm` (`MercadoScreen`'s watchlist `vm` e `RadarScreen`'s `radarVm`), também extraídas por parsing estrutural (balanceamento de `{}/()/[]`, não regex ingênua — necessário porque `radarVm` tem um objeto aninhado, `sc: {...}`). Não é uma lista fixa de nomes de campo: se amanhã um campo novo entrar no destructuring de `vm` e for lido dentro desse bloco em qualquer um dos dois call sites, o guardião pega automaticamente.
- **Por que não medir os 32 campos inteiros do destructuring**: investigação (ver key-decisions) confirmou que 11 campos ausentes em `radarVm` (`an` fora do bloco de `anVencida`, `rrPos`, `diasPos`, `pctCapPos`, `os`, `buyMeta`, `expanded`, `opsOpen`, `opsSpark`, `onToggleOps`) NUNCA são lidos em Radar — são watchlist-only por desenho, protegidos pelo curto-circuito `children ||`. Um guardião de paridade total nesses 32 campos ficaria permanentemente vermelho sem nenhum bug real. O escopo no bloco `opGate.liquida` é o que captura precisamente a classe do bug relatado sem produzir falso positivo.
- **Verificação empírica do guardião**: revertido manualmente `cp` de `radarVm` (`sed` temporário), rodado `node web/tests/test_opcoes_proposta_ui.mjs` isolado — o assert de paridade do Radar FALHOU corretamente (`FALHOU todo campo de vm lido no bloco opGate.liquida está no radarVm ... — faltando: cp`); restaurado o arquivo, teste voltou a passar. Confirma que o guardião realmente detecta esta classe de regressão, não só documenta.

## Task Commits

1. **Fix: cp em radarVm + guardião estrutural de paridade** - `ac9e1c6` (fix)
2. **Este SUMMARY** - (a seguir, docs)

## Files Created/Modified

- `web/src/App.jsx` - `radarVm` (linha 6334) ganha o campo `cp` (shorthand, já em escopo via `const { data, cp } = ctx;` em `RadarScreen`)
- `web/tests/test_opcoes_proposta_ui.mjs` - novo bloco de guardião estrutural (paridade de campos de `vm` lidos no bloco `opGate.liquida` de `AtivoCard`, entre `MercadoScreen`'s watchlist `vm` e `RadarScreen`'s `radarVm`)

## Decisions Made

Ver `key-decisions` no frontmatter — resumo: fix mínimo de um campo (`cp`), `MercadoScreen` intocado; guardião escopado ao bloco `opGate.liquida` (não ao destructuring inteiro de 32 campos) porque os outros 11 campos ausentes em `radarVm` são intencionalmente watchlist-only (dead code em Radar via o curto-circuito `children`); guardião extraído por parsing estrutural (balanceamento de chaves), não hardcode de nomes de campo — verificado empiricamente que detecta a regressão revertendo o fix e vendo o teste falhar.

## Deviations from Plan

Este NÃO é um plano formal (é o segundo bugfix do mesmo checkpoint), então "Deviations from Plan" não se aplica no sentido usual. Nenhum auto-fix de Rule 1-3 fora do escopo do próprio bug relatado; nenhuma mudança de arquitetura (Rule 4) foi necessária — o fix é estritamente o campo faltante especificado pela task.

**Total deviations:** 0.
**Impact on plan:** Nenhum além da correção do bug relatado — Radar volta a renderizar o card de opções lastreadas sem crash.

## Issues Encountered

- **Conflito entre a especificação literal do guardião pedido pela task ("todo identificador desestruturado de `vm` deve estar em ambos os call sites") e o estado real do código**: uma implementação literal dessa regra (paridade nos 32 campos) falharia hoje por 11 lacunas pré-existentes e por desenho (não bugs). Resolvido escopando o guardião ao bloco `opGate.liquida` — o único trecho de `AtivoCard` que de fato roda incondicionalmente para as duas telas e onde o bug real (`cp`) se manifestou — documentado extensivamente em comentário no próprio teste. Ver key-decisions.
- **`server/.venv` ausente neste worktree** (mesmo padrão de bugfixes anteriores da Fase 14 — worktrees não copiam diretórios não versionados); não impactou este fix (é 100% frontend), mas `bash scripts/executar.sh --testes` resolve isso automaticamente via `scripts/test.sh` (mesmo padrão do bugfix anterior).
- Nenhum bloqueio de teste, nenhuma dependência nova instalada.

## User Setup Required

None — nenhuma configuração de serviço externo necessária. Fix é puramente de código de cliente (`web/src/App.jsx`), sem novo env var, sem nova rota, sem mudança de schema.

## Next Phase Readiness

- **O fix resolve o segundo achado da Task 2 (checkpoint humano) do plano 14-08.** A sessão orquestradora com canal ao vivo com o Alex deve re-verificar o cenário específico (abrir a aba Radar/Mesa com um ativo elegível para opções — `opGate.liquida` true — e confirmar que o card renderiza sem crash e mostra a proposta) antes de considerar a Task 2 aprovada.
- **Publicação de front NÃO foi feita nesta correção** — `web/src/App.jsx` foi tocado, mas nem `scripts/bump.sh` nem `publicar-web.sh` foram rodados (fora de escopo desta task por instrução explícita — orquestrador decide quando publicar). `npx vite build` foi rodado apenas para validação (mandatório por CLAUDE.md), não gerou mudanças versionadas (`web/dist` é gitignored).
- **`bash scripts/executar.sh --testes` verde**: 1814 passed, 1 skipped (backend, sem regressão — nenhum arquivo Python tocado), 110/110 `.mjs` (web, incluindo o guardião novo).
- **`npx vite build` verde**: 89 módulos transformados, build completo sem erro (só o warning pré-existente de chunk size, não relacionado a esta mudança).
- STATE.md e ROADMAP.md NÃO foram atualizados por este executor — por instrução explícita, o orquestrador que fizer o merge deste worktree é quem faz essas escritas.

---
*Phase: 14-opcoes-lastreadas*
*Bugfix completed: 2026-08-31*
