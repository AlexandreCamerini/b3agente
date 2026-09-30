---
phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
plan: 06
subsystem: ui
tags: [copy, vocabulario, reconciliacao, skill_ref, python, javascript]

# Dependency graph
requires:
  - phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
    provides: reconciliacao_elegibilidade_txt/reconciliacaoTxt (43-04, HIER-03)
provides:
  - "queda determinística para a frase nunca_medido quando falta um dado exigido pelo microtexto de reconciliação, nos dois lados (skill_ref.py e copy.js)"
affects: [43-refinamento-copy-por-modo-kpiblock-e-ritmo]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Detecção de placeholder por frase: em vez de checar campos genéricos, a função inspeciona quais placeholders ({n}/{janela}/{expR}) a frase do estado escolhido realmente contém, e só cai em nunca_medido se um placeholder PRESENTE estiver sem valor."

key-files:
  created: []
  modified:
    - server/app/skill_ref.py
    - server/tests/test_skill_ref.py
    - web/src/copy.js
    - web/tests/test_reconciliacao_elegibilidade.mjs

key-decisions:
  - "Reversão deliberada da regra '?' (Fase 43 original) por decisão do Alex na DP-3 do checkpoint 43-05 (2026-09-27): ausência de dado no microtexto de reconciliação cai para a frase nunca_medido do modo, nunca mostra '?'."
  - "n=0 é tratado como valor presente (não cai), preservando o princípio 'nunca inventa nem esconde dado real' (CLAUDE.md item 4/5) — distinção crítica de n=None (ausência real)."
  - "Guardiões antigos da regra '?' não foram apagados: reescritos com nota de reversão deliberada datada, conforme regra da casa (guardiões nunca se apagam silenciosamente)."

requirements-completed: [HIER-03]

# Metrics
duration: 25min
completed: 2026-09-27
---

# Phase 43 Plan 06: Queda para nunca_medido no microtexto de reconciliação Summary

**Microtexto de reconciliação (skill_ref.py ↔ copy.js) cai para a frase `nunca_medido` do modo, em vez de mostrar "?", quando falta um dado exigido pelos placeholders da frase escolhida — n=0 continua sendo exibido como valor real.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- `reconciliacao_elegibilidade_txt` (skill_ref.py) e `reconciliacaoTxt` (copy.js) agora detectam, por frase, quais placeholders (`{n}`, `{janela}`, `{expR}`) estão presentes e caem em `nunca_medido` se qualquer um deles não tiver valor — em vez de interpolar `?`.
- `n = 0` continua distinto de `n = None`: é valor real, nunca dispara a queda.
- Guardiões antigos da regra `?` preservados com nota de reversão deliberada datada (2026-09-27, Fase 43, DP-3) em vez de apagados.
- Varredura de regressão em ambos os lados (modo × estado × combinações de ausência) garante que nenhum retorno contenha `"?"`.
- Paridade skill_ref.py ↔ copy.js mantida — guardião cruzado `test_vocabulario_espelho.mjs` continua verde sem alteração.

## Task Commits

Each task was committed atomically:

1. **Task 1: queda para nunca_medido em skill_ref.py (pytest RED → GREEN)** - `0274ed42` (feat)
2. **Task 2: espelho em copy.js + guardião JS** - `d4ba6ece` (feat)

_Ambas as tasks eram `tdd="true"`: RED confirmado antes de cada implementação (pytest e node respectivamente), GREEN confirmado depois; sem etapa de refactor separada — o corpo final já ficou limpo na primeira implementação._

## Files Created/Modified
- `server/app/skill_ref.py` - `reconciliacao_elegibilidade_txt` detecta placeholders da frase e cai em `nunca_medido` quando falta valor exigido; docstring atualizada citando a reversão e a DP-3.
- `server/tests/test_skill_ref.py` - guardião antigo (`test_reconciliacao_txt_ausente_vira_interrogacao_nunca_zero`) reescrito com nota de reversão deliberada e renomeado para `test_reconciliacao_txt_ausente_cai_para_nunca_medido_nunca_zero`; +2 testes novos (n=0 presente; varredura sem "?").
- `web/src/copy.js` - `reconciliacaoTxt` espelha a mesma regra de queda (placeholders da frase, `n == null` / `!janela` / `typeof expR !== "number"` como ausência).
- `web/tests/test_reconciliacao_elegibilidade.mjs` - asserções antigas da regra "?" trocadas por asserções da regra nova (com nota de reversão), mais varredura modo × estado × ausências.

## Decisions Made
- Ver `key-decisions` no frontmatter. Nenhuma decisão arquitetural (Rule 4) foi necessária — o plano já especificava a regra exata (placeholders por frase, `n=0` como valor presente).

## Deviations from Plan

None - plano executado exatamente como escrito. As duas tasks seguiram a ação descrita linha a linha (RED com os testes especificados, GREEN com a implementação especificada).

## Issues Encountered

- `bash scripts/executar.sh --testes` completo (pytest full + suíte web) não pôde ser rodado dentro do sandbox por restrição de rede (falha em testes que dependem de `httpx`/SSL/certificados, ex.: `test_yahoo_*`, `test_texto_vazio.py`) — comportamento já documentado pelo checkpoint 43-05 ("suíte canônica roda fora do sandbox"). Rodei em vez disso: `pytest tests/test_skill_ref.py` (31/31 verde, sem rede) e a suíte web `.mjs` completa (todos os arquivos, 0 falhas), além de `npx vite build` (exit 0) e `npx cap copy ios` (exit 0, ignorando os avisos inofensivos de "failed to copy trust settings of system certificate" que vêm do próprio `cap copy` no sandbox e não afetam o bundle copiado). A verificação de rede completa via `scripts/executar.sh --testes` fica pendente para quem rodar fora do sandbox, mas não é esperada nenhuma regressão porque as mudanças não tocam nenhum módulo de rede/dados de mercado.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Next Phase Readiness

O gap `43-06` estava bloqueando a Task 2 do `43-05` (bump/publicar). Com a regra `nunca_medido` implementada, testada e espelhada nos dois lados, o `43-05` pode retomar na Task 2 (bump + publicação pelo Alex) — não é ação deste executor.

---
*Phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo*
*Completed: 2026-09-27*

## Self-Check: PASSED

Todos os arquivos referenciados existem em disco e os dois commits de task (`0274ed42`, `d4ba6ece`) foram encontrados em `git log --oneline --all`.
