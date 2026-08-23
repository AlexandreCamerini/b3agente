---
phase: 05-corre-o-m-dio-c-digo-gate-admin
plan: 03
subsystem: testing
tags: [skill, prompt-parity, catalog.js, deviceStore, guardian-test, defaults.py]

# Dependency graph
requires: []
provides:
  - "web/src/catalog.js com SKILL_TEXT_ESTUDO/SKILL_TEXT_OPERADOR byte-idênticos a defaults.py"
  - "LEGACY_SKILL_TEXTS (lista de migração) exportado de catalog.js"
  - "Guardião Python test_a8ii_paridade_defaults_skill_com_catalog_js"
  - "Migração de default legado no deviceStore/ensure() (persistence.js)"
  - "Guardião .mjs test_fase5_skill_migracao_legado.mjs"
affects: [FIX-C22, camada-de-entendimento, deviceStore, catalog.js]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guardião de paridade byte-exata via extração de template literal por regex (mesmo padrão de carteiraStopAlvo*), estendido para tolerar backtick escapado (\\`) dentro do literal"
    - "Migração de default legado no aparelho espelhando _eh_default_antigo do servidor: default antigo sobe, edição do usuário é intocável"

key-files:
  created:
    - web/tests/test_fase5_skill_migracao_legado.mjs
  modified:
    - web/src/catalog.js
    - server/tests/test_auditoria_prompts.py
    - web/src/persistence.js

key-decisions:
  - "Texto canônico gerado executando o servidor real (python -c com defaults.default_skill_text()/default_skill_text_operador()), não transcrito à mão — elimina risco de erro de transcrição em texto acentuado"
  - "O Contrato de saída contém um backtick literal (`corpo`) — escapado como \\` no template literal de catalog.js; a regex do guardião Python foi desenhada para tratar \\` como par escapado e desescapar antes de comparar, em vez de simplificar o texto para evitar o backtick"
  - "Migração de legado implementada dentro de ensure() no deviceStore (persistence.js), não como método novo — preserva paridade de MÉTODO com serverStore (guardrail CLAUDE.md), pois nenhuma função pública nova foi criada"
  - "Guardião .mjs exercita o código real (seed de localStorage por escopo + store._setDeviceScope(), sem mock de fetch) em vez de inspeção estática, porque ensure()/store são plenamente importáveis e exercitáveis em Node (mesmo padrão de test_carteira_nativa_sincroniza.mjs)"

patterns-established:
  - "Quando um literal de template JS precisa conter o caractere de fechamento do próprio literal, escapar e ajustar a regex do guardião para tolerar o escape — não simplificar/alterar o texto canônico para 'facilitar' o teste"

requirements-completed: [FIX-C22]

# Metrics
duration: ~50min
completed: 2026-08-23
---

# Phase 5 Plan 3: Paridade byte-exata da skill (FIX-C22) Summary

**`catalog.js` reconciliado byte a byte com `defaults.py` (11 princípios, acentuação, Contrato de saída) e travado por guardião Python + migração automática de aparelhos com texto legado, sem tocar em edição do usuário.**

## Performance

- **Duration:** ~50 min
- **Completed:** 2026-08-23
- **Tasks:** 2/2
- **Files modified:** 3 (+ 1 criado)

## Accomplishments

- A divergência REAL encontrada na auditoria (`catalog.js` carregava uma
  geração de texto anterior — sem acentos, sem os 11 princípios, sem
  Contrato de saída — enquanto o servidor já compunha da fonte canônica
  `skill_ref`) foi RECONCILIADA, não só detectada: o app iPhone hoje manda a
  MESMA persona que a web no corpo de `/api/technical/analyze`.
- Guardião de paridade byte-exata (`test_a8ii_paridade_defaults_skill_com_catalog_js`)
  no mesmo padrão do par `carteiraStopAlvo*` já protegido — prova negativa
  executada (1 caractere corrompido faz o teste falhar; revertido e
  confirmado verde de novo, round-trip sem diff no arquivo).
- Aparelhos que já têm o texto legado gravado sobem automaticamente para o
  canônico na próxima leitura do doc (`ensure()`); texto que o usuário
  editou manualmente (qualquer string fora de `LEGACY_SKILL_TEXTS`)
  permanece intocado — mesmo contrato de `_eh_default_antigo` do servidor.

## Task Commits

1. **Task 1: Reconciliar os literais de skill em catalog.js com o servidor** - `e980cb6` (fix)
2. **Task 2: Guardião de paridade byte-exata + migração do legado no aparelho** - `5b22ed2` (feat)

_Nenhum deviation exigiu commit adicional fora dos dois commits de task._

## Files Created/Modified

- `web/src/catalog.js` - `SKILL_TEXT_ESTUDO`/`SKILL_TEXT_OPERADOR` (constantes de template literal, byte-idênticas ao stdout do Python); `defaultSkillText()`/`defaultSkillTextOperador()` viraram wrappers finos; `LEGACY_SKILL_TEXTS` exportado com os dois textos de geração anterior
- `server/tests/test_auditoria_prompts.py` - novo guardião `test_a8ii_paridade_defaults_skill_com_catalog_js`, extraindo o literal via regex que tolera backtick escapado e desescapando antes de comparar
- `web/src/persistence.js` - `ensure()` (deviceStore) ganha upgrade de default legado para `doc.skill.text`/`doc.skillOperador.text` contra `LEGACY_SKILL_TEXTS`; import de `LEGACY_SKILL_TEXTS` acrescentado
- `web/tests/test_fase5_skill_migracao_legado.mjs` (novo) - guardião que exercita `deviceStore` real via seed de `localStorage` + `_setDeviceScope()`, cobrindo migração de legado, preservação de edição e doc novo já nascendo canônico, nos dois modos (Estudo/Operador)

## Decisions Made

- Gerar o texto canônico executando `defaults.default_skill_text()`/
  `default_skill_text_operador()` no interpretador real do servidor (não
  transcrever à mão) — elimina risco de erro de acentuação/pontuação em
  texto com `⇒`, `≥`, `—` etc. Verificado byte a byte via `node -e` contra o
  JSON gerado pelo Python antes de commitar.
- O Contrato de saída (`_CONTRATO_SAIDA` em `defaults.py`) contém um
  backtick literal em `` `corpo` `` — presente nos DOIS textos (Estudo e
  Operador), 2 ocorrências cada. Escapado como `\`` no template literal de
  `catalog.js`; a regex do guardião Python (`` `((?:\\.|[^`\\])*)` ``) trata
  o par escapado sem fechar o literal prematuramente, e desescapa
  (`.replace("\\`", "`").replace("\\\\", "\\")`) antes da comparação byte a
  byte. Registrado no comentário do arquivo e no docstring do teste, como o
  plano pedia explicitamente para o caso de haver backtick no texto.
- Migração de legado implementada só dentro de `ensure()` no `deviceStore`
  (não um método novo exportado) — confirma explicitamente que a paridade de
  MÉTODO entre `deviceStore`/`serverStore` (guardrail CLAUDE.md) NÃO é
  violada, porque nenhuma função pública nova foi criada; a migração roda
  como efeito colateral do carregamento do doc, igual ao backfill de
  `skillOperador` que já morava ali.
- Guardião `.mjs` exercita o código de produção real em vez de inspeção
  estática — `deviceStore`/`ensure()`/`store._setDeviceScope()` já são
  plenamente importáveis e testáveis em Node com `localStorage` mockado
  (mesmo padrão comprovado em `test_carteira_nativa_sincroniza.mjs`), então
  a ressalva do plano ("se `ensureShape` não for exercitável, usar inspeção
  estática") não se aplicou — o teste comprova o comportamento real, não só
  a existência do código.

## Deviations from Plan

None - plan executado exatamente como especificado, incluindo o tratamento
explícito do backtick no Contrato de saída que o próprio plano antecipava
como possibilidade a verificar.

## Issues Encountered

- `web/node_modules` ausente no worktree novo (achado C-24 do REPORT-01,
  documentado como pré-requisito operacional em `05-CONTEXT.md`) — resolvido
  com `npm install` em `web/` antes de `npx vite build`/`scripts/executar.sh --testes`,
  como o próprio C-24 já previa.
- `server/.venv` não existe no worktree (git-worktree não replica venvs
  locais) — contornado apontando o Python do clone principal
  (`/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python3`) com
  `cwd` no `server/` do worktree, garantindo que o código importado é o do
  worktree e não o do clone principal.
- Primeira tentativa de comentário no cabeçalho de `catalog.js` citou o
  padrão `${...}` literalmente para explicar "zero interpolação" — isso por
  si só fez `grep -c '\${' web/src/catalog.js` subir de 0 para 1 (falso
  positivo: o critério de aceite mede a string, não se é código real).
  Reescrito para descrever a regra sem usar a sequência `${` no comentário;
  grep voltou a 0.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Next Phase Readiness

- FIX-C22 fechado: paridade travada e divergência real reconciliada, não só
  detectada.
- `bash scripts/executar.sh --testes` passa (1326 testes backend, +1 do
  guardião novo; suíte web 100% OK, incluindo os 2 arquivos novos/alterados
  deste plano) e `cd web && npx vite build` conclui sem erro.
- Sem bloqueios para os demais planos da Wave 1 (05-01, 05-02, 05-04, 05-05)
  — nenhum arquivo deste plano (`catalog.js`, `persistence.js`,
  `test_auditoria_prompts.py`, o `.mjs` novo) é compartilhado com os outros
  planos da wave.

---
*Phase: 05-corre-o-m-dio-c-digo-gate-admin*
*Completed: 2026-08-23*

## Self-Check: PASSED

All created/modified files found on disk; both task commits (`e980cb6`,
`5b22ed2`) verified present in git log.
