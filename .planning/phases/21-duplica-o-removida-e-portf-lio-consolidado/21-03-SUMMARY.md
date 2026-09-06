---
phase: 21-duplica-o-removida-e-portf-lio-consolidado
plan: 03
subsystem: ui
tags: [react, jsx, testing, tdd, capital-curve, guardian-tests]

# Dependency graph
requires:
  - phase: 21-duplica-o-removida-e-portf-lio-consolidado
    plan: 02
    provides: "test_fase21_dedup_consolidacao.mjs existente como guardião único da fase, para estender em vez de duplicar"
provides:
  - "CapitalCurve com limiar ec.days >= 3 (era >= 1) — a curva só é desenhada quando há 3+ snapshots de patrimônio"
  - "Flag poucosDias (ec.days >= 1 && ec.days < 3) com terceiro ramo de placeholder, entre o de curva e o de zero dias"
  - "Chave curvaPoucosDias(dias) em COPY.estudo e COPY.operador, texto idêntico nos dois modos"
  - "Guardião FIX-03 (Seções A/B/C) somado ao mesmo arquivo de DEDUP-01/03, incluindo prova unitária real de equityCurve com 1/2 snapshots"
affects: [21-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guardião de teste .mjs com seção que importa módulo puro de verdade (finance.js/copy.js via await import) ao lado de seções que só fazem grep sobre App.jsx lido como texto — os dois estilos convivem no mesmo arquivo quando o alvo é uma função pura testável isoladamente"
    - "Gate sobre ec.days (contagem de snapshots persistidos), nunca sobre curve.length (que varia ±1 conforme o último snapshot seja de hoje ou de ontem) — mesma disciplina que 'DIAS REGISTRADOS' já expõe ao usuário"

key-files:
  created: []
  modified:
    - web/src/copy.js
    - web/src/App.jsx
    - web/tests/test_fase21_dedup_consolidacao.mjs

key-decisions:
  - "TDD RED/GREEN literal: Task 1 estendeu o guardião e confirmou 16 falhas pelas razões exatas esperadas (limiar novo ausente, poucosDias inexistente, cp não desestruturado, chave de copy ausente nos dois modos) antes de qualquer edição em App.jsx/copy.js; Task 2 tornou as 39 asserções verdes."
  - "Texto de curvaPoucosDias idêntico em Estudo e Operador — é afirmação factual sobre disponibilidade de dado (quantos snapshots existem), não enquadramento de decisão, que é onde os dois modos divergem em tom no resto do arquivo."
  - "Assertion 6 do guardião (limiar antigo ausente) checa a string exata 'ec.days >= 1;' com o ';' — sem o ponto-e-vírgula a substring apareceria também dentro de 'ec.days >= 1 && ec.days < 3' (a definição de poucosDias) e geraria falso negativo."

patterns-established:
  - "Terceiro ramo de placeholder inserido ENTRE hasSeries e o estado zero (hasSeries ? ... : poucosDias ? ... : ...), reusando literalmente o mesmo objeto de estilo do placeholder de zero dias — nunca um componente novo para uma variação de texto dentro da mesma família visual."

requirements-completed: [FIX-03]

# Metrics
duration: ~20min
completed: 2026-09-05
---

# Phase 21 Plan 03: Placeholder de "poucos dias" em CapitalCurve (FIX-03) Summary

**Limiar de exibição da curva de patrimônio sobe de `ec.days >= 1` para `ec.days >= 3`; com 1-2 dias registrados, um placeholder textual (`cp.curvaPoucosDias`, nos dois modos) substitui a reta de escala degenerada que antes era desenhada.**

## Performance

- **Duration:** ~20 min (dois commits de task, 22:04–22:09, mais leitura de contexto e a suíte canônica completa)
- **Started:** 2026-09-05 (após reset do worktree para o HEAD do plano 21-02)
- **Completed:** 2026-09-05
- **Tasks:** 2
- **Files modified:** 3 (1 guardião de teste estendido, 2 arquivos de produto)

## Accomplishments
- Provado com `equityCurve` real (não só grep) que 1 snapshot datado de hoje colapsa a curva para exatamente 2 pontos (`curve.length === 2`) — a escala degenerada que motivou o achado ao vivo original; o sub-caso "1 snapshot de ontem" também coberto (`curve.length === 3`, ramo de anexar), confirmando que o gate uniforme em `ec.days` cobre os dois sub-casos sem caso especial.
- `CapitalCurve` (`web/src/App.jsx`) ganhou o limiar novo (`ec.days >= 3`) e o flag `poucosDias` (`ec.days >= 1 && ec.days < 3`), com um terceiro ramo de placeholder entre a curva real e o estado de zero dias — mesmo objeto de estilo (`fontSize: "11.5px", color: T.textFaint, marginTop: "10px", lineHeight: 1.5`) reusado nos dois placeholders.
- `curvaPoucosDias(dias)` entrou em `COPY.estudo` e `COPY.operador` (`web/src/copy.js`), texto idêntico nos dois modos, pluralização real (1 dia × 2 dias) e sempre mencionando o 3º dia — casando com o limiar do código.
- Nada do que devia sobreviver mudou: o texto do estado zero ("Sua curva começa amanhã...") segue byte a byte igual; a guarda do fetch do Ibovespa (`if (!hasSeries) return`) segue com a expressão literal travada por `test_benchmark_curva.mjs`; o rabisco tracejado do SVG (`M0,72 C60,66...`) segue intocado — as duas asserções desse guardião irmão continuam verdes, confirmando a premissa do plano.
- Guardião único da fase (`web/tests/test_fase21_dedup_consolidacao.mjs`) ESTENDIDO (não duplicado): 39 chamadas `ok(` (eram 17), somando as três seções de FIX-03 (prova unitária de `equityCurve`, grep sobre o corpo isolado de `CapitalCurve`, paridade da chave de copy) às 17 de DEDUP-01/03 do plano 21-01.
- Suíte canônica verde de ponta a ponta: `bash scripts/executar.sh --testes` → `2021 passed, 1 skipped` (pytest) + todos os `web/tests/*.mjs` `[OK]` (incluindo `test_fase21_dedup_consolidacao.mjs`, `test_copy_theme.mjs` e `test_benchmark_curva.mjs` isolados). `npx vite build` verde.

## Task Commits

Each task was committed atomically:

1. **Task 1: Guardião de FIX-03 escrito antes da mudança (RED)** - `0366da4` (test)
2. **Task 2: Limiar de 3 dias, terceiro ramo de placeholder e a chave nos dois modos (GREEN)** - `c29ec1f` (feat)

**Plan metadata:** (este commit, criado a seguir)

## TDD Gate Compliance

Plano com `tdd="true"` na Task 1. Gate sequence verificado no `git log`:
1. `test(21-03): ...` (RED) — `0366da4` — confirmado
2. `feat(21-03): ...` (GREEN) — `c29ec1f` — confirmado, após o RED
3. REFACTOR — não necessário; nenhum commit de `refactor(21-03)` (código ficou limpo já na primeira passada GREEN, sem duplicação a extrair).

Gate RED/GREEN íntegro.

## Files Created/Modified
- `web/tests/test_fase21_dedup_consolidacao.mjs` - Estendido com a seção FIX-03: Seção A (importa `equityCurve` de `finance.js` via `await import`, 6 asserções de comportamento real com 0/1/1(ontem)/2 snapshots), Seção B (isola o corpo de `CapitalCurve` pelo padrão `indexOf` já usado no arquivo para os outros dois componentes, 8 asserções de grep sobre limiar/flag/chamada/desestruturação/não-regressão), Seção C (importa `COPY` de `copy.js`, 10 asserções de paridade e conteúdo pluralizado). Cabeçalho do arquivo atualizado para refletir as 3 seções (DEDUP-01/03 + FIX-03).
- `web/src/copy.js` - `curvaPoucosDias: (dias) => ...` adicionado em `COPY.estudo` (linha ~31) e `COPY.operador` (linha ~253), mesmo padrão inline de `saudacao`/`resumoDia`, texto idêntico nos dois modos.
- `web/src/App.jsx` - `CapitalCurve`: `const { data, quotes, cp } = ctx;` (era sem `cp`); `hasSeries = ec.days >= 3` (era `>= 1`) com comentário datado explicando a escala degenerada; novo `const poucosDias = ec.days >= 1 && ec.days < 3;`; terceiro ramo `poucosDias ? <div>{cp.curvaPoucosDias(ec.days)}</div> : ...` inserido entre o ramo de curva e o de zero dias, mesmo objeto de estilo do placeholder de zero.

## Decisions Made
- Nenhuma decisão de produto nova — `21-CONTEXT.md`/`21-UI-SPEC.md`/`21-03-PLAN.md` já traziam o JSX-alvo, o texto de copy e o limiar exatos, literais. As únicas decisões foram de execução/teste:
  - Checar o limiar antigo ausente via a string exata `"ec.days >= 1;"` (com `;`) em vez de `"ec.days >= 1"`, para não colidir com a substring que aparece dentro de `poucosDias = ec.days >= 1 && ec.days < 3`.
  - `curvaPoucosDias` chamado com `try/catch` dentro do guardião (helper `callSafe`) para que a Seção C falhe assertion-por-assertion durante o RED (função ainda não existe) sem abortar o script inteiro com uma exceção não tratada.

## Deviations from Plan

None - plan executado exatamente como escrito. A varredura de planejamento sobre os dois guardiões irmãos (`test_benchmark_curva.mjs` linhas 79/84) estava correta: as duas asserções sobreviveram sem qualquer edição, confirmando que subir o limiar não quebrou a guarda do Ibovespa nem o rabisco tracejado.

## Issues Encountered

- **Setup do ambiente (não é deviation de código):** o worktree, resetado para o HEAD do plano 21-02, não tinha `web/node_modules` materializado — `npx vite build` falhava com `ERR_MODULE_NOT_FOUND`. Restaurado via `npm install` dentro de `web/` com o sandbox do Bash desabilitado (mesmo padrão documentado nos dois planos anteriores desta fase); `git diff --stat web/package.json web/package-lock.json` vazio antes e depois.
- **`mktemp -d` bloqueado pelo sandbox durante `bash scripts/executar.sh --testes`:** o script usa `TMPDIR_TESTES="$(mktemp -d)"` para os logs por-teste; `mktemp` tentou criar em `/var/folders/...` (fora da allowlist de escrita do sandbox), falhou com "Operation not permitted", e a variável ficou vazia — os logs por-teste caíam em caminhos absolutos a partir de `/` (ex.: `/test_x.mjs.log`), mas os testes em si RODARAM e passaram (o `[OK]`/`[X]` por linha não depende do log). Rodei a suíte completa uma segunda vez com o sandbox do Bash desabilitado para eliminar a fonte de ruído e confirmar `RC=0` de ponta a ponta: `2021 passed, 1 skipped` + todos os `.mjs` `[OK]`, sem nenhum `[X]`. Não é deviation de código — o próprio script já tem fallback de robustez (não trava a suíte por falha de log), só o ambiente do sandbox interferiu na criação do diretório de log.

## Orchestrator Live Re-Verification

**Não realizada neste subagente** — ambiente sem ferramentas de browser/computer-use vinculadas (limitação conhecida, confirmada em todos os planos anteriores desta fase e sessão). Pelo enquadramento do próprio plano, o núcleo de FIX-03 (limiar `ec.days`, escala degenerada) é provado por teste unitário real da função pura `equityCurve` — não depende de verificação visual ao vivo para estar correto. Um único ponto cosmético fica pendente de confirmação visual pelo orquestrador/Alex:
1. Abrir uma conta com 1 ou 2 dias de patrimônio registrados (ou simular via `equitySnapshots` curto) e confirmar visualmente que a área do gráfico mostra o texto novo ("Só 1/2 dia(s) registrado(s) ainda — a curva aparece a partir do 3º dia") em vez de uma linha reta, com a mesma família visual/tipográfica do placeholder de zero dias — sem quebra de layout em viewport estreito (375px).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Suíte canônica verde (`bash scripts/executar.sh --testes`: `2021 passed, 1 skipped` no pytest + todos os `web/tests/*.mjs`, incluindo os três guardiões relevantes desta task — `test_fase21_dedup_consolidacao.mjs`, `test_copy_theme.mjs`, `test_benchmark_curva.mjs`) e `npx vite build` verde. Nenhuma dependência nova, nenhum push feito.
- `git diff --stat` do plano inteiro lista exatamente os 3 arquivos esperados (`web/src/App.jsx`, `web/src/copy.js`, `web/tests/test_fase21_dedup_consolidacao.mjs`); `web/package.json`/`web/package-lock.json` sem diff.
- Requisito FIX-03 (critério 4 do ROADMAP da Fase 21: numa conta nova, logo depois da primeira operação, a área do gráfico mostra um placeholder que diz que ainda faltam dados, e a curva só é desenhada quando há forma de verdade para desenhar) satisfeito no código e na suíte estática/unitária; falta só a confirmação visual cosmética listada acima.
- Nenhum bump/publicação de front foi feito neste plano (fora de escopo) — publicar o front da Fase 21 fica para quando a fase inteira (ou o milestone v1.5) fechar, seguindo o guardrail do repositório sobre `scripts/bump.sh` antes de `publicar-web.sh`.
- Próximo plano da fase (21-04) pode seguir sem bloqueio desta entrega.

---
*Phase: 21-duplica-o-removida-e-portf-lio-consolidado*
*Completed: 2026-09-05*

## Self-Check: PASSED

- FOUND: web/tests/test_fase21_dedup_consolidacao.mjs
- FOUND: web/src/copy.js
- FOUND: web/src/App.jsx
- FOUND: .planning/phases/21-duplica-o-removida-e-portf-lio-consolidado/21-03-SUMMARY.md
- FOUND commit: 0366da4 (test)
- FOUND commit: c29ec1f (feat)
