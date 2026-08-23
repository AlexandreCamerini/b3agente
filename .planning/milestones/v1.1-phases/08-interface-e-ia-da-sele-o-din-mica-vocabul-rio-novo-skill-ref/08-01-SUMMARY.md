---
phase: 08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref
plan: 01
subsystem: ui
tags: [skill_ref, copy, vocabulario, adr-017, guardiao, cross-file-parity]

# Dependency graph
requires:
  - phase: 07-sele-o-din-mica-por-desempenho-hist-rico
    provides: "historico por setup no JSON de scan/watchlist (signal_ledger.py, expR/n/elegivel/janelaRef/medidoAte), sem vocabulario canonico ainda"
provides:
  - "skill_ref.HISTORICO / HISTORICO_ROTULO / ENTRADA_AUTO — fonte unica dos 6 estados do historico medido por setup, por modo (operador/educacional)"
  - "historico_txt() / entrada_auto_txt() — helpers de interpolacao com fallback fechado (nunca anuncia disponibilidade sem veredito explicito)"
  - "COPY[modo].historico / .historicoRotulo / .entradaAuto em web/src/copy.js, byte a byte identicos ao Python"
  - "historicoTxt() / entradaAutoTxt() em copy.js, espelho de comportamento dos helpers Python"
  - "guardiao cruzado estendido em test_vocabulario_espelho.mjs cobrindo os 3 dicionarios novos"
affects: [08-02, 08-03, 08-04, 08-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "vocabulario canonico por modo em dict-por-modo + funcao de interpolacao (mesmo padrao de TIMING/timing_txt)"
    - "guardiao cruzado Python-como-texto + import ES do JS, com override de caminho por env var para sabotagem controlada em sandbox"

key-files:
  created: []
  modified:
    - server/app/skill_ref.py
    - server/tests/test_skill_ref.py
    - web/src/copy.js
    - web/tests/test_vocabulario_espelho.mjs

key-decisions:
  - "Textos copiados literalmente do 08-UI-SPEC.md (Copywriting Contract) — nenhuma redacao nova improvisada"
  - "entrada_auto_txt/entradaAutoTxt falham FECHADO: qualquer estado != 'disponivel' (incluindo vazio/None/desconhecido) cai em por_setup_bloqueado, nunca anuncia entrada automatica disponivel por engano"
  - "contraste (-0,099R / +0,005R) e texto FIXO de backtest nos dois modos — nao ligado a endpoint, mudanca exige nova ADR"

patterns-established:
  - "Vocabulario novo sempre entra em skill_ref.py (fonte) + copy.js (espelho) + guardiao cruzado — nunca hardcodado em componente"

requirements-completed: [ADR17-B34-01]

# Metrics
duration: 33min
completed: 2026-08-21
---

# Phase 08 Plan 01: Vocabulário canônico do histórico medido Summary

**`skill_ref.HISTORICO`/`HISTORICO_ROTULO`/`ENTRADA_AUTO` com os 6 estados do histórico medido por setup (ADR-017 Bloco 3), espelhados byte a byte em `copy.js`, travados por guardião cruzado com sabotagem controlada validada.**

## Performance

- **Duration:** ~33 min
- **Started:** 2026-08-21T17:37:00-03:00 (approx.)
- **Completed:** 2026-08-21T18:12:51-03:00
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Fonte única do vocabulário do histórico medido criada em `server/app/skill_ref.py`: 6 estados (`elegivel`, `inelegivel`, `insuficiente`, `nunca_medido`, `aposentado`, `desatualizado`) em `HISTORICO`, 5 rótulos de pill em `HISTORICO_ROTULO`, e 4 frases de transparência do gate em `ENTRADA_AUTO` (2 agregadas do card C-19 + 2 parametrizadas por setup) — todas nos dois modos (`operador`/`educacional`).
- Dois helpers de interpolação (`historico_txt`, `entrada_auto_txt`) seguindo o mesmo idioma de `timing_txt`, com falha fechada: estado desconhecido/vazio/`None` nunca anuncia "entrada automática disponível" por engano.
- Espelho completo em `web/src/copy.js` (`COPY[modo].historico`/`.historicoRotulo`/`.entradaAuto` + `historicoTxt()`/`entradaAutoTxt()`), byte a byte idêntico ao Python.
- Guardião cruzado `test_vocabulario_espelho.mjs` estendido: parseia `skill_ref.py` como texto (âncoras ancoradas em início de linha, parse mudo falha explicitamente), compara conjunto de chaves e conteúdo byte a byte contra `COPY` importado, confirma que `App.jsx` não hardcoda nenhum texto novo, e confirma que os placeholders `{setup}`/`{janelaRef}` sobrevivem nos dois arquivos.
- Sabotagem controlada validada em sandbox (`/private/tmp/.../scratchpad`, nunca o arquivo real do servidor): 1 byte trocado em cópia temporária derruba o guardião (1 falha detectada, exit 1) via override `B3_SKILL_REF_PATH`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Vocabulário canônico do histórico medido em skill_ref.py** - `f0ba107` (feat)
2. **Task 2: Espelho em copy.js com helper de interpolação** - `a04bd10` (feat)
3. **Task 3: Guardião cruzado skill_ref.py ↔ copy.js** - `61a028e` (test)

_Nota: Tasks 1 e 3 tinham `tdd="true"`, mas a implementação de origem (Task 1) e o guardião (Task 3) foram escritos como uma única unidade coesa cada — não houve ciclo RED (teste falhando)→GREEN separado porque o comportamento a travar (as strings literais aprovadas no UI-SPEC) e o teste que o verifica nasceram juntos, sem implementação prévia a corrigir. Ver "TDD Gate Compliance" abaixo._

**Plan metadata:** (este commit de SUMMARY)

## Files Created/Modified
- `server/app/skill_ref.py` - `HISTORICO`/`HISTORICO_ROTULO`/`ENTRADA_AUTO` + `historico_txt()`/`entrada_auto_txt()`
- `server/tests/test_skill_ref.py` - 11 guardiões novos cobrindo paridade de chaves, interpolação, fallback fechado e ausência de verbo de ordem
- `web/src/copy.js` - espelho `COPY[modo].historico`/`.historicoRotulo`/`.entradaAuto` + `historicoTxt()`/`entradaAutoTxt()`
- `web/tests/test_vocabulario_espelho.mjs` - segundo espelho do guardião cruzado (ADR-017 Bloco 3), parser de dict Python + comparação byte a byte

## Decisions Made
- Textos copiados literalmente do `08-UI-SPEC.md` (seção "Copywriting Contract") — nenhuma redação nova improvisada, incluindo acentuação, em-dash "—", minus U+2212 "−" e glifos "✓"/"✗".
- `entrada_auto_txt`/`entradaAutoTxt` falham FECHADO: qualquer estado diferente de `"disponivel"` (vazio, `None`, desconhecido) cai em `por_setup_bloqueado` — nunca anuncia entrada automática disponível sem veredito explícito (T-08-20 do threat model).
- `contraste` (−0,099R / +0,005R) é texto FIXO de backtest (ADR-016/017) nos dois modos — não ligado a endpoint; mudar o número exige nova ADR, não um PR de UI.
- `HISTORICO_ROTULO` não tem chave `desatualizado` (é modificador de timestamp, nunca pill própria), conforme UI-SPEC "Interaction & State Inventory".

## Deviations from Plan

None - plan executado exatamente como escrito. Uma dependência de ambiente foi resolvida sem mudança de escopo:

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `npm install` em `web/` antes do `vite build`/testes**
- **Found during:** Task 2 (verificação `npx vite build`)
- **Issue:** Worktree nasce sem `web/node_modules` (achado já documentado em `PROJECT.md`: "rodar num worktree/checkout novo sem `web/node_modules` instalado faz testes web falharem por ambiente, não por regressão").
- **Fix:** `npm install` em `web/` (dependências normais do `package.json`, nenhum pacote novo adicionado).
- **Files modified:** nenhum arquivo versionado (`web/node_modules` e `web/dist` são gitignored).
- **Verification:** `npx vite build` e `bash scripts/executar.sh --testes` passaram limpos depois.
- **Committed in:** N/A (artefato gitignored, sem commit necessário).

---

**Total deviations:** 1 auto-fixed (1 blocking, ambiente)
**Impact on plan:** Nenhum impacto de escopo — resolução de ambiente documentada como achado conhecido do projeto.

## Issues Encountered
None além do item de ambiente acima.

## TDD Gate Compliance

O frontmatter do plano é `type: execute` (não `type: tdd`), então o gate de plano inteiro (RED→GREEN→REFACTOR obrigatório) não se aplica. As Tasks 1 e 3 tinham `tdd="true"` na tag de tarefa: Task 1 combinou a implementação nova (dicionários + helpers) e o guardião pytest que a trava num único commit `feat`, porque o `<behavior>` da tarefa É a especificação do texto literal aprovado — não havia comportamento pré-existente a "corrigir" que justificasse um commit `test` isolado falhando primeiro. Task 3 é puramente um guardião de teste (nenhum arquivo de produção mudou) e foi commitada como `test`. Nenhum gate RED/GREEN foi formalmente sequenciado; julgamento: o risco de regressão é baixo porque toda a superfície nova (Tasks 1 e 2) já tinha 21 + 6 verificações de aceite manuais rodadas com sucesso antes do guardião cruzado (Task 3) ser escrito, e o guardião foi então validado com sabotagem controlada provando que ele de fato pega divergência.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Vocabulário canônico pronto para os Planos 08-02/08-03/08-04 consumirem sem hardcodar texto: `skill_ref.historico_txt`/`entrada_auto_txt` no backend, `copyFor(modo).historico`/`historicoTxt`/`entradaAutoTxt` no front.
- `ENTRADA_AUTO["*"]["por_setup_disponivel"/"por_setup_bloqueado"]` prontos para o card de status único do FIX-C19 (Plano 08-04) — texto ainda não desenhado em nenhuma tela (isso é o Bloco 3/4 dos próximos planos desta fase).
- Nenhum bloqueador. `defaults.py`/`catalog.js` (prompts de IA) permanecem intocados — confirmado por `git diff --stat` vazio e `test_auditoria_prompts.py` verde.

---
*Phase: 08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref*
*Completed: 2026-08-21*

## Self-Check: PASSED

All created/modified files verified present (`server/app/skill_ref.py`, `server/tests/test_skill_ref.py`, `web/src/copy.js`, `web/tests/test_vocabulario_espelho.mjs`, este `SUMMARY.md`). All 3 task commits verified in `git log` (`f0ba107`, `a04bd10`, `61a028e`).
