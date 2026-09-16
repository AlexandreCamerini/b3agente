---
phase: 32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone
plan: 01
subsystem: ui
tags: [copy, vocabulario, opcoes, react, guardiao]

# Dependency graph
requires: []
provides:
  - "9 chaves novas de copy (duasLeiturasIntro, tiraOpcoesSubtitulo, curadoriaErroBusca, curadoriaErroBuscaCta, linhaChamadaOpcoesTexto/Vazia/Carregando/Erro/Aria) nos dois modos"
  - "3 conteúdos reescritos (tiraOpcoesTitulo, tiraOpcoesSubtitulo, curadoriaSubtitulo) que nomeiam os dois motores (D-05)"
  - "Guardião test_consolidacao_opcoes_copy.mjs cobrindo chaves que viverão fora de OpcoesScreen.jsx"
affects: [32-02, 32-03, 32-04, 32-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Frase-ponte/constatação de fato: texto idêntico nos dois modos quando não é voz de personagem (duasLeiturasIntro, linhaChamadaOpcoes*, curadoriaErroBusca)"
    - "Paridade de CONJUNTO por prefixo (Object.keys().filter(startsWith).sort()) em vez de lista fixa, para pegar chave nova esquecida num dos dois modos"

key-files:
  created:
    - web/tests/test_consolidacao_opcoes_copy.mjs
  modified:
    - web/src/copy.js
    - web/tests/test_carteira_opcoes_tira.mjs

key-decisions:
  - "linhaChamadaOpcoes* e duasLeiturasIntro/curadoriaErroBusca são texto idêntico nos dois modos — constatação de fato sobre dois motores determinísticos, não voz de personagem"
  - "curadoriaErroBusca corrige violação ativa do princípio 4 do CLAUDE.md (erro de busca caía no estado 'vazio')"

patterns-established:
  - "Guardião dedicado para chaves de copy consumidas fora do arquivo que o guardião-irmão varre (test_vocabulario_opcoes.mjs só cobre OpcoesScreen.jsx)"

requirements-completed: [D-01, D-03, D-05]

duration: ~20min (estimativa — PLAN_START_EPOCH não foi capturado no início desta execução)
completed: 2026-09-15
---

# Phase 32 Plan 01: Vocabulário novo da consolidação de opções Summary

**9 chaves novas + 3 conteúdos reescritos em `web/src/copy.js` (dois modos), com guardião novo cobrindo as chaves que os planos 32-02..32-04 vão consumir fora de `OpcoesScreen.jsx`.**

## Performance

- **Duration:** ~20min (estimativa)
- **Completed:** 2026-09-15
- **Tasks:** 2/2
- **Files modified:** 3 (1 criado, 2 modificados)

## Accomplishments

- As 9 chaves novas (`duasLeiturasIntro`, `tiraOpcoesSubtitulo`, `curadoriaErroBusca`, `curadoriaErroBuscaCta`, `linhaChamadaOpcoesTexto/Vazia/Carregando/Erro/Aria`) existem em `COPY.estudo` e `COPY.operador`, com os tipos corretos (7 string + 2 função).
- `tiraOpcoesTitulo` e `curadoriaSubtitulo` foram reescritos para NOMEAR o motor de cada bloco (D-05) — antes os dois blocos cross-carteira usavam títulos que não distinguiam "motor com gate" de "motor sem gate".
- A frase-ponte `duasLeiturasIntro` ("nenhuma é mais certa que a outra") existe, idêntica nos dois modos — mitigação do risco regulatório do D-05.
- `curadoriaErroBusca` corrige o achado do UI-SPEC: `useCuradoria().erro` existia mas nunca era exibido, e a busca falha caía no mesmo estado que "nada elegível" (violação do princípio 4 do CLAUDE.md).
- Guardião novo `test_consolidacao_opcoes_copy.mjs` (24 asserções) cobre as 9 chaves nos dois modos, checklist `PROIBIDAS`, e paridade de CONJUNTO por prefixo — sem esta lacuna, `linhaChamadaOpcoes*` (que os planos seguintes vão consumir em `App.jsx`) ficaria sem cobertura de paridade.

## Task Commits

1. **Task 1: Escrever as chaves novas e reescrever os três conteúdos nos dois modos** - `56c3f20` (feat)
2. **Task 2: Guardião das chaves que vivem fora de OpcoesScreen.jsx + ajuste de contagem na tira** - `f194879` (test)

_Nenhuma task exigiu commit adicional além dos dois acima._

## Files Created/Modified

- `web/src/copy.js` — 9 chaves novas + 3 conteúdos reescritos, em `COPY.estudo` e `COPY.operador`
- `web/tests/test_consolidacao_opcoes_copy.mjs` — guardião novo (24 asserções), criado
- `web/tests/test_carteira_opcoes_tira.mjs` — contagem da tira de 7 para 8 chaves (`tiraOpcoesSubtitulo` entrou), nota datada 2026-09-15; nenhuma regra removida (43 `ok(` antes e depois da edição)

## Decisions Made

- Nenhuma decisão de arquitetura nova nesta plano — texto literal do UI-SPEC/PLAN.md, sem interpretação. As únicas escolhas foram de POSICIONAMENTO dos comentários/chaves dentro do arquivo (ex.: `duasLeiturasIntro` e `linhaChamadaOpcoes*` ficaram agrupados perto de `tiraOpcoes*`, já que descrevem a mesma superfície de Posições), sem impacto em comportamento.

## Deviations from Plan

None - plan executado exatamente como escrito.

## Issues Encountered

- A suíte canônica (`bash scripts/executar.sh --testes`) rodou primeiro dentro do sandbox padrão do Bash tool e reportou 27 falhas de backend, todas `PermissionError: [Errno 1] Operation not permitted` em `ssl.py` (carregamento de certificado TLS bloqueado pelo sandbox de rede) — nenhuma delas em código tocado por este plano (que só mexeu em `web/`). Reexecutada com `dangerouslyDisableSandbox: true` (autorizado pelas instruções do ambiente para evidência clara de bloqueio de sandbox): **2923 passed, 5 skipped, 3 xfailed, 0 failed + 151/151 `.mjs`, exit 0**. Consistente com o padrão já registrado no MEMORY.md do usuário ("sandbox mente — falsas falhas").

## Validação executada

- `node web/tests/test_consolidacao_opcoes_copy.mjs` — passou (24/24)
- `node web/tests/test_carteira_opcoes_tira.mjs` — passou (43/43), sem regressão
- `node web/tests/test_curadoria_ui.mjs` — passou, sem regressão
- `node web/tests/test_vocabulario_opcoes.mjs` — passou, sem regressão
- `bash scripts/executar.sh --testes` (sem sandbox) — **2923 passed, 5 skipped, 3 xfailed, 0 failed backend + 151/151 `.mjs`, exit 0**
- `npx vite build` (em `web/`) — build verde, exit 0 (warning pré-existente de chunk >500kB, não relacionado a este plano)

## User Setup Required

None - nenhuma configuração de serviço externo.

## Next Phase Readiness

- O vocabulário que os planos 32-02 (extração de componentes), 32-03 (migração dos blocos cross-carteira) e 32-04 (multi-candidato em Operar) vão consumir já existe nos dois modos, testado e com guardião de paridade.
- `curadoriaErroBusca`/`curadoriaErroBuscaCta` estão prontos para o plano que reescrever `CuradoriaEstruturas` ler `useCuradoria().erro` e renderizar o estado (a correção de EXIBIÇÃO, não de captura de dado, é escopo do 32-0x que move o componente).
- Nenhum componente foi tocado nesta plano — `App.jsx`/`OpcoesScreen.jsx` continuam lendo as chaves antigas onde já liam; as chaves novas ficam disponíveis, mas sem consumidor ainda (esperado, por desenho do plano).
- Nenhum bloqueio conhecido para o 32-02.

---
*Phase: 32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone*
*Completed: 2026-09-15*

## Self-Check: PASSED

- FOUND: `web/tests/test_consolidacao_opcoes_copy.mjs`
- FOUND: `.planning/phases/32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone/32-01-SUMMARY.md`
- FOUND: commit `56c3f20` (Task 1)
- FOUND: commit `f194879` (Task 2)
- FOUND: commit `f1ea53d` (docs, este SUMMARY)
- `.planning/STATE.md` e `.planning/ROADMAP.md` não modificados nesta execução (confirmado por `git status --short`), conforme guardrail do repositório
