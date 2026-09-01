---
phase: quick-260901-2da
plan: 01
subsystem: api
tags: [mydata, config, backend]

requires: []
provides:
  - "BASE_DEFAULT de server/app/mydata_client.py aponta para o domínio canônico mydata.semente.dev"
  - "Todo de acompanhamento com o item 1 marcado como concluído"
affects: [opcoes-v2]

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - server/app/mydata_client.py
    - server/tests/test_mydata_client.py
    - .planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md

key-decisions:
  - "Domínio canônico do hub mydata é mydata.semente.dev, confirmado pelo Alex em 2026-09-01"
  - "mydata.acamerini.app é alias do MESMO serviço Railway (edge jfk1, x-hikari-trace jfk1.57w5 idêntico) — troca de baixo risco"
  - "Guardião de teste atualizado com nota, não apagado, conforme guardrail do repositório"

patterns-established: []

requirements-completed: [QT-260901-2da]

duration: 8min
completed: 2026-09-01
---

# Quick Task 260901-2da: Troca de domínio canônico no cliente mydata Summary

**BASE_DEFAULT de `mydata_client.py` migrado de `mydata.acamerini.app` para o domínio canônico `mydata.semente.dev`, com guardião de teste atualizado e todo de acompanhamento marcado como concluído.**

## Performance

- **Duration:** ~8 min
- **Tasks:** 2/2 completos
- **Files modified:** 3

## Accomplishments
- `BASE_DEFAULT` e docstring do módulo em `server/app/mydata_client.py` agora referenciam `https://mydata.semente.dev`, com comentário registrando a decisão e a razão (produção depende do default porque `MYDATA_URL` não é setada no Railway).
- Guardião `test_base_url_sem_env_usa_default` (e docstring do arquivo de teste) atualizados para o novo valor, com nota explicando que a mudança é deliberada, não drift.
- Todo `.planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` — seção "Ação decorrente do item 1" marcada `CONCLUÍDA 2026-09-01`, arquivo mantido em `pending/` porque o item 2 (acesso server-to-server ao b-mcp) segue aberto.

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Trocar o domínio canônico no cliente mydata e no guardião** - `c2f30bf` (fix)
2. **Task 2: Marcar a ação decorrente como concluída no todo de acompanhamento** - `7ba39de` (docs)

## Files Created/Modified
- `server/app/mydata_client.py` - `BASE_DEFAULT` e docstring apontam para `mydata.semente.dev`; comentário de decisão acima da constante.
- `server/tests/test_mydata_client.py` - guardião `test_base_url_sem_env_usa_default` e docstring do arquivo atualizados para o novo domínio, com nota de que a troca é deliberada.
- `.planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` - seção "Ação decorrente do item 1" marcada `CONCLUÍDA 2026-09-01`; item 2 e o restante do todo intocados.

## Decisions Made
- Nenhuma decisão nova além do que já estava no plano — Alex já havia confirmado o domínio canônico antes da execução; esta task só aplicou a troca no código.

## Deviations from Plan

Um único ajuste dentro do próprio Task 1, sem impacto de escopo: o comentário de decisão inicialmente escrito acima de `BASE_DEFAULT` citava literalmente o domínio antigo (`mydata.acamerini.app`) para explicar o porquê da troca, o que fazia o gate de verificação `grep -c "mydata.acamerini.app" server/app/mydata_client.py` retornar 1 em vez de 0 (contando o próprio comentário, não só o valor antigo do default). Reescrito para "o nome antigo" sem citar a string literal, preservando o mesmo conteúdo histórico exigido pela convenção de comentários do repo. Não é uma mudança de escopo — é o mesmo Task 1, mesmo commit (`c2f30bf`), apenas o texto do comentário ajustado para passar no próprio gate do plano.

**Total deviations:** 0 fora do escopo do Task 1 (auto-correção textual dentro da própria task, sem novo commit).
**Impact on plan:** Nenhum — diff final tem exatamente os 3 arquivos previstos, gates do plano todos verdes.

## Issues Encountered
- Ambiente do worktree não tinha `server/.venv` (não versionado em git, cada worktree o recria à parte). Usado o `.venv` do repo principal (`/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python3`) para rodar `pytest tests/test_mydata_client.py` a partir do diretório `server/` do worktree — sem instalar nada, sem tocar no worktree. Suíte: 40 passed.

## User Setup Required
None - no external service configuration required. Nenhuma variável de ambiente do Railway foi alterada; produção continua sem `MYDATA_URL` setada e passa a depender do novo default assim que este código for deployado.

## Next Phase Readiness
- Item 1 do todo `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` resolvido e aplicado no código.
- Item 2 (acesso server-to-server ao `b-mcp`) segue em aberto e continua bloqueando o planejamento de "Opções v2" — arquivo permanece em `.planning/todos/pending/`.
- Deploy: esta troca de código só terá efeito em produção após deploy do backend (`server/`); não há passo de deploy nesta quick task — fica para quando o backend for publicado.

---
*Phase: quick-260901-2da*
*Completed: 2026-09-01*

## Self-Check: PASSED

- FOUND: server/app/mydata_client.py
- FOUND: server/tests/test_mydata_client.py
- FOUND: .planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md
- FOUND: commit c2f30bf (Task 1)
- FOUND: commit 7ba39de (Task 2)
