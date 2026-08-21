---
phase: 06-instrumentacao-assertividade-adr015
plan: 05
subsystem: testing
tags: [python, javascript, jsx, guardian-tests, adr-015, adr15-05, rr-minimo, skill_ref]

# Dependency graph
requires:
  - phase: 06-instrumentacao-assertividade-adr015 (06-04)
    provides: "agent.py com store.sell(motivo) — mesmo arquivo, sem colisão (06-04 toca a chamada de store.sell na linha ~861; este plano toca só a constante RR_MINIMO e o import, linhas ~30/445-446)"
provides:
  - "setups.RR_MINIMO e agent.RR_MINIMO leem de skill_ref.RR_MIN (deixaram de ser literais 1.5 soltos)"
  - "web/src/finance.js exporta RR_MIN/RR_MIN_TXT — fonte única do front"
  - "guardião cruzado Python (test_a8iii, server/tests/test_auditoria_prompts.py) — falha se qualquer um dos 2 motores ou dos 3 arquivos de front divergir do skill_ref.RR_MIN"
  - "guardião cruzado JS (web/tests/test_rr_min_fonte_unica.mjs) — cruza por VALOR com skill_ref.py, checa interpolação real em runtime e ausência de interpolação morta em JSX"
affects: [06-03-consolidacao-adr015]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "guardião cruzado por VALOR (não por grafia): quando o texto do lado B é COMPUTADO em runtime a partir de um literal do lado A (RR_MIN_TXT = f'{RR_MIN:g}'.replace('.',',')), o teste cruzado parseia só o literal fonte e DERIVA o texto esperado — nunca procura o texto computado como string literal (esse match falharia sempre)"
    - "anti-interpolação-morta em JSX: recortar o trecho do fonte, assertar ausência de '${' e simular a renderização (substituir a expressão pelo valor esperado e comparar a frase final) — pega o caso que nem grep nem build pegam"
    - "override de caminho por env var só para sabotagem controlada em sandbox (B3_SKILL_REF_PATH) — nunca para uso normal do runner"

key-files:
  created:
    - web/tests/test_rr_min_fonte_unica.mjs
  modified:
    - server/app/setups.py
    - server/app/agent.py
    - server/tests/test_auditoria_prompts.py
    - web/src/finance.js
    - web/src/copy.js
    - web/src/App.jsx
    - web/src/catalog.js
    - web/tests/test_alvo_dinamico_ui.mjs

key-decisions:
  - "catalog.js mantém os 3 literais de R:R (defaultSkillTextOperador + os 2 template literals de prompt) — interpolar quebraria test_a8ii_paridade_defaults_carteira_com_catalog_js, que compara o CÓDIGO-FONTE byte a byte com defaults.py. Amarrados à fonte única por teste cruzado (test_a8iii + test_rr_min_fonte_unica.mjs), não por import — decisão já registrada no plano (decision_note), confirmada na execução."
  - "comentários adicionados perto dos literais preservados foram escritos evitando a substring exata '1,5:1' (ex.: 'os R:R mínimo/ideal' em vez de citar o número) — senão os próprios comentários quebrariam o critério de aceite 'grep -c 1,5:1 catalog.js == 3', que conta ocorrências no arquivo inteiro, não só no código executável"

patterns-established:
  - "constante consolidada com comentário de 'não consolidar' ao lado da constante irmã que só coincide em valor (ALVO_ATR_MULT = 1.5 ao lado de RR_MINIMO = skill_ref.RR_MIN, ambas 1.5 mas semânticas diferentes) — evita que o próximo guardião ou o próximo editor amarre as duas por engano"

requirements-completed: [ADR15-05]

# Metrics
duration: ~50min
completed: 2026-08-21
---

# Phase 6 Plan 05: Fonte única do R:R mínimo (1,5:1) — dois motores Python + front — Summary

**`setups.RR_MINIMO` e `agent.RR_MINIMO` passam a ler de `skill_ref.RR_MIN`; `web/src/finance.js` exporta `RR_MIN`/`RR_MIN_TXT`; dois guardiões cruzados novos (Python `test_a8iii` e JS `test_rr_min_fonte_unica.mjs`) amarram os 2 motores + 3 arquivos de front + `skill_ref.py` — valor continua 1,5, nenhum comportamento de gate mudou.**

## Performance

- **Duration:** ~50 min
- **Tasks:** 3/3 completos
- **Files modified:** 9 (8 código/teste modificados, 1 teste novo)

## Accomplishments
- `setups.RR_MINIMO` e `agent.RR_MINIMO` deixaram de ser literais `1.5` soltos — leem `skill_ref.RR_MIN` em runtime, com `import` explícito (`from . import skill_ref`)
- `agent.ALVO_ATR_MULT` (multiplicador de ATR, também `1.5` por coincidência) permanece constante independente, com comentário explícito de "não consolidar" — guardião novo assere isso
- `web/src/finance.js` ganhou `RR_MIN`/`RR_MIN_TXT`, espelho declarado de `skill_ref.py`
- `copy.js` (2 sites) e o `hint:` de `carteiraStopAlvoOperador` em `App.jsx` passaram de string com aspas duplas (`${}` inerte) para crase com interpolação real
- O parágrafo do alvo dinâmico em `App.jsx` (texto JSX cru) passou a usar a expressão `{RR_MIN_TXT}:1` — forma correta nesse contexto, sem cifrão
- `catalog.js` manteve os 3 literais de prompt espelhado, com comentário explicando por que ficam literais (paridade byte-a-byte com `defaults.py`)
- Dois guardiões cruzados novos: `test_a8iii_rr_min_fonte_unica_nos_dois_motores_e_no_front` (Python, lê o código-fonte de `setups.py`/`agent.py`/`finance.js`/`copy.js`/`App.jsx`/`catalog.js`) e `web/tests/test_rr_min_fonte_unica.mjs` (JS, cruza por VALOR com `skill_ref.py`)
- `test_alvo_dinamico_ui.mjs` atualizado (não removido) para exigir a nova forma interpolada, com nota
- Ambas as sabotagens controladas exigidas no aceite passaram: interpolação morta em JSX e divergência de valor via sandbox (`B3_SKILL_REF_PATH`), sem nunca mutar `server/app/skill_ref.py`
- Suíte canônica completa (`bash scripts/executar.sh --testes`): 1122 testes pytest + 87 suítes `.mjs`, todas verdes; `npx vite build` verde

## Task Commits

Cada task foi commitada em RED→GREEN (TDD):

1. **Task 1: os dois motores Python importam o R:R de skill_ref + guardião cruzado**
   - `ba39a67` test(06-05): guardião cruzado RR_MINIMO nos dois motores + front (RED)
   - `9022723` feat(06-05): setups e agent importam RR_MINIMO de skill_ref (GREEN)
2. **Task 2: fonte única do R:R no front + guardião JS cruzado**
   - `d234b6f` test(06-05): guardião cruzado JS do R:R mínimo front×backend (RED)
   - `0d81959` feat(06-05): fonte única do R:R mínimo no front, sintaxe correta por site (GREEN)
3. **Task 3: verificação canônica + build** — sem commit de código (só verificação + este SUMMARY)

**Plan metadata:** (commit deste SUMMARY, a seguir)

## Files Created/Modified
- `server/app/setups.py` — `+from . import skill_ref`; `RR_MINIMO = skill_ref.RR_MIN` (era `1.5` literal); gate de R:R (linha ~654) intocado
- `server/app/agent.py` — `+skill_ref` no import existente (`from . import db, skill_ref, store`); `RR_MINIMO = skill_ref.RR_MIN`; `ALVO_ATR_MULT = 1.5` preservado com comentário de "não consolidar"
- `server/tests/test_auditoria_prompts.py` — `test_a8iii_rr_min_fonte_unica_nos_dois_motores_e_no_front`: assere valor + leitura de código-fonte dos 2 motores Python e dos 3 arquivos de front (via regex `(\d,\d):1`)
- `web/src/finance.js` — `export const RR_MIN = 1.5` e `export const RR_MIN_TXT = "1,5"`, com comentário de espelho de `skill_ref.py`
- `web/src/copy.js` — `+import { RR_MIN_TXT } from "./finance.js"`; `subtituloRadar` e `comoAnalisaCorpo` do ramo `operador` convertidos para crase com `${RR_MIN_TXT}:1`
- `web/src/App.jsx` — `+RR_MIN_TXT` no import de `finance.js`; parágrafo do alvo dinâmico usa `{RR_MIN_TXT}:1` (expressão JSX); `hint:` de `carteiraStopAlvoOperador` convertido para crase
- `web/src/catalog.js` — 3 comentários novos explicando por que os literais de R:R ficam literais (sem tocar no texto dos template literals nem em `defaultSkillTextOperador`)
- `web/tests/test_alvo_dinamico_ui.mjs` — linha 37 atualizada para exigir `/R:R recalculado continuar ≥ \{RR_MIN_TXT\}:1/`, com nota ADR-015 no comentário
- `web/tests/test_rr_min_fonte_unica.mjs` (novo) — guardião cruzado front×backend por valor, anti-interpolação-morta em JSX, caminhos por `import.meta.url`, override por `B3_SKILL_REF_PATH`

## Decisions Made
- `catalog.js` mantém os 3 literais de R:R — decisão já explícita no plano (`decision_note`), confirmada e documentada em comentário no código. Interpolar ali quebraria `test_a8ii_paridade_defaults_carteira_com_catalog_js` (paridade byte-a-byte com `defaults.py`).
- Os comentários adicionados nas linhas de `catalog.js` evitam a substring literal `"1,5:1"` (usam "os R:R mínimo/ideal" em vez de citar o número) — na primeira tentativa os próprios comentários fizeram `grep -c "1,5:1" catalog.js` subir de 3 para 6, quebrando o critério de aceite explícito da Task 2. Corrigido reescrevendo os comentários sem o literal.
- Linhas reais de `setups.py`/`agent.py` divergem levemente das citadas no `read_first` do plano (ex.: `RR_MINIMO` em `setups.py` está na linha 578, não 559) — drift esperado de arquivo vivo; localizado por `grep`, sem impacto na tarefa.

## Deviations from Plan

None - plano executado exatamente como escrito. O ajuste de wording nos comentários de `catalog.js` (ver "Decisions Made") foi uma correção dentro da própria Task 2, não uma mudança de escopo — o comentário SEMPRE foi para explicar a decisão de não interpolar; só a redação teve que evitar o literal que ela mesma descreve.

## Issues Encountered
- Worktree nasceu sem `server/.venv` próprio e sem `web/node_modules` (mesmo achado documentado em `06-04-SUMMARY.md` e em `PROJECT.md`) — `scripts/test.sh` já resolve isso sozinho (deriva o `.venv` do clone principal via `git rev-parse --git-common-dir`); rodei `npm install` em `web/` antes da suíte canônica.
- `ugrep` (grep instalado neste ambiente) trata `$` como âncora de fim de linha mesmo no meio do padrão em alguns casos, dando falso-negativo em `grep -c '${RR_MIN_TXT}:1' arquivo` sem escapar o `$` — não é um problema do código, é uma particularidade do binário `grep` local; confirmado com `\$` escapado e com os testes automatizados (`node tests/test_rr_min_fonte_unica.mjs`), que fazem a checagem real via string match em runtime, não via grep de shell.

## Sabotagens Controladas (Task 2, exigidas no aceite)

**Sabotagem 1 — JSX (rodada e desfeita):** troquei a expressão JSX `{RR_MIN_TXT}:1` do parágrafo do alvo dinâmico em `App.jsx` por `${RR_MIN_TXT}:1` (interpolação de string, inerte em texto JSX cru). `node tests/test_rr_min_fonte_unica.mjs` falhou em 2 checagens (`trecho NÃO contém '${'` e a renderização simulada). Revertido via `cp` do backup antes da sabotagem; `git diff web/src/App.jsx` confirmado limpo (só as 3 mudanças pretendidas da Task 2).

**Sabotagem 2 — backend, em sandbox (nunca tocou o arquivo real):** copiei `server/app/skill_ref.py` para um diretório temporário fora do worktree, troquei `RR_MIN = 1.5` por `RR_MIN = 2.0` SÓ NA CÓPIA, e rodei `B3_SKILL_REF_PATH=<cópia> node tests/test_rr_min_fonte_unica.mjs`. Falhou em 2 checagens (número do front 1.5 ≠ número do backend 2; texto derivado "2" ≠ RR_MIN_TXT do front "1,5"). `git diff server/app/skill_ref.py` confirmado vazio antes e depois — o arquivo real nunca foi mutado.

## User Setup Required

None - nenhuma configuração de serviço externo necessária.

## Next Phase Readiness
- `ADR15-05` (fonte única do R:R mínimo) concluído: 2 motores Python + front amarrados a `skill_ref.RR_MIN` por dois guardiões cruzados que falham na divergência
- Nenhum comportamento de gate mudou — valor continua `1.5`/`"1,5"` em todos os pontos
- `git diff --stat` desde antes deste plano confirma exatamente os 9 arquivos de `files_modified`; `server/app/skill_ref.py` não aparece (nunca foi tocado, nem pela sabotagem controlada)
- Nenhum bloqueio conhecido para o Plano 03 (consolidação da Phase 6)

---
*Phase: 06-instrumentacao-assertividade-adr015*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: web/tests/test_rr_min_fonte_unica.mjs
- FOUND: web/src/finance.js
- FOUND: .planning/phases/06-instrumentacao-assertividade-adr015/06-05-SUMMARY.md
- FOUND: ba39a67 (test RED, Task 1)
- FOUND: 9022723 (feat GREEN, Task 1)
- FOUND: d234b6f (test RED, Task 2)
- FOUND: 0d81959 (feat GREEN, Task 2)
