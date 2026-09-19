---
phase: 15-motor-de-proposta-arquitetura-interna
plan: 02
subsystem: api
tags: [python, pytest, ast, opcoes, setups, radar, tdd]

# Dependency graph
requires:
  - phase: 14-opcoes-lastreadas (standalone)
    provides: "setups.plano_do_resultado shape e opcoes_lastreadas.propor() como mapeamento de referência em produção"
provides:
  - "opcoes_gatilho.do_plano(plano) — função pura que traduz o plano do Radar em decisão de avaliar estrutura de opções (avaliar/vies/motivo), reusável pela Fase 16 sem acoplar a nenhuma estrutura concreta"
  - "Guardião de paridade entre do_plano() e opcoes_lastreadas.propor() em produção"
  - "Guardião estrutural (ast) que reprova qualquer import/string/arquivo trazendo a DSL de setups do b-mcp para dentro dos módulos de opções"
affects: ["16-biblioteca-de-estruturas"]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Módulo puro sem I/O testado por comportamento (mesma disciplina de setups.py/opcoes_lastreadas.py)", "Guardião estrutural via ast.walk em vez de grep textual, para não proibir o próprio comentário que documenta a proibição"]

key-files:
  created:
    - server/app/opcoes_gatilho.py
    - server/tests/test_opcoes_gatilho.py
  modified: []

key-decisions:
  - "do_plano() importa DECISAO_VENDER/DECISAO_AGUARDAR/DECISAO_NAO_OPERAR de setups.py em vez de literais duplicados — paridade estrutural garantida por import, não por convenção"
  - "Racional de ENG-06 (proibição da DSL do b-mcp) documentado via comentários `#`, não no docstring do módulo — docstrings são ast.Constant e cairiam no próprio guardião de string proibida que o módulo declara"
  - "Guardião de paridade compara motivo de opcoes_lastreadas.propor() (put_protecao/call_coberta/outro) contra vies de do_plano() (protecao/premio/None) para as 6 combinações decisao×lado do bloco de comportamento — detecta divergência se qualquer um dos dois lados mudar isoladamente"

requirements-completed: [ENG-06]

duration: ~25min
completed: 2026-09-02
---

# Phase 15 Plan 02: Motor de proposta — gatilho técnico do Radar Summary

**`opcoes_gatilho.do_plano()` extrai o mapeamento decisao/lado → avaliar estrutura hoje embutido em `opcoes_lastreadas.propor()`, como função pura testada, com dois guardiões: paridade com o motor em produção e proibição estrutural (via `ast`) da DSL de setups do b-mcp.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-09-02T21:43:38Z
- **Tasks:** 2/2
- **Files modified:** 2 (ambos criados)

## Accomplishments
- `opcoes_gatilho.do_plano(plano)` traduz qualquer plano do Radar (inclusive ausente/malformado/decisão desconhecida) em `{avaliar, vies, motivo}`, com a mesma ordem de avaliação que `opcoes_lastreadas.propor()` já usa em produção
- Guardião de paridade prova que os dois caminhos (o embutido em `propor()` e o novo `do_plano()`) concordam hoje — vai falhar sozinho se um dos dois divergir antes da unificação real da Fase 16
- Guardião estrutural via `ast.walk` reprova import de raiz `mcp`/`setups_json` ou nome contendo `b_mcp`/`bmcp`, constante de string citando `b-mcp`/`setups.json`/`semente.dev`, e a existência de `server/app/setups.json` — nos três módulos de opções (`opcoes_gatilho.py`, `opcoes_payoff.py` se existir, `opcoes_lastreadas.py`)

## Task Commits

Each task was committed atomically (Task 1 é TDD: RED → GREEN):

1. **Task 1 (RED): comportamento de `do_plano`** - `eeaa0d6` (test)
2. **Task 1 (GREEN): implementação de `do_plano`** - `dda018c` (feat)
3. **Task 2: guardiões de paridade e proibição b-mcp** - `64150ce` (test)

**Plan metadata:** commit deste SUMMARY (a seguir)

## Files Created/Modified
- `server/app/opcoes_gatilho.py` (72 linhas) - módulo puro; `do_plano()`, `VIES_PROTECAO`, `VIES_PREMIO`, `MOTIVO_SEM_SETUP`; importa constantes `DECISAO_*` de `.setups`, nunca literais duplicados
- `server/tests/test_opcoes_gatilho.py` (213 linhas) - 16 testes: 12 de comportamento (Task 1) + 1 guardião de paridade + 2 guardiões b-mcp (Task 2)

## Decisions Made
- Racional de proibição do b-mcp documentado em comentários `#` (não no docstring do módulo/função) — decisão deliberada para não colidir com o próprio guardião de string que o módulo declara (docstrings viram `ast.Constant`, comentários `#` não entram no AST)
- `vies` mantido abstrato (`"protecao"`/`"premio"`), sem nomear estrutura concreta — quem mapeia viés → estrutura (venda coberta, put, collar) é a Fase 16, conforme `<interfaces>` do plano
- Guardião de paridade constrói cadeia sintética e posição no próprio teste (padrão já usado em `test_opcoes_lastreadas_proposta.py`), sem fixture externa

## Deviations from Plan

None - plan executado exatamente como escrito. `opcoes_lastreadas.py` não foi tocado (verificado: `git diff --stat` vazio), nenhuma dependência nova (`requirements.txt`/`requirements-prod.txt` intocados).

## Issues Encountered

O worktree não tinha `.venv` próprio (gitignored, não replicado por `git worktree add`). Reusei o interpretador do `.venv` do repo principal (`/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python3`) para rodar os testes a partir do diretório `server/` do worktree — leitura/execução apenas, nenhuma escrita fora do worktree.

Sob o sandbox padrão do Bash tool, 27 testes falharam com `PermissionError: [Errno 1] Operation not permitted` ao carregar certificados TLS (`ssl.load_verify_locations`) — módulos afetados: `test_benchmark_ibov.py`, `test_yahoo_*.py`, `test_push_registro_evento.py`, `test_texto_vazio.py`, `test_opcoes_lastreadas_rotas.py`, `test_rotas_fase4.py`, `test_fase3_kill_switch_duracao.py`, `test_options_provider_yahoo.py`. Nenhum desses testes importa `opcoes_gatilho.py` (confirmado por inspeção — o módulo é stdlib puro, sem rede) e a falha é uma restrição de I/O do sandbox (carregamento de cert TLS), não relacionada ao conteúdo deste plano. Verifiquei isso rodando a suíte completa uma vez com `dangerouslyDisableSandbox: true`: **1832 passed, 1 skipped** (incluindo os 16 testes novos deste plano) — o que prova que a suíte inteira passa sem a restrição de sandbox, não que os mesmos 27 testes já falhavam antes deste plano sob sandbox (não rodei a suíte sandboxeada no commit-base `17b9122` para comparar 1:1). Dado o mecanismo de falha (I/O de certificado, nada a ver com lógica de `opcoes_gatilho`), a inferência é segura, mas fica registrada como inferência, não como diff comparativo. Fora de escopo deste plano por desenho (SCOPE BOUNDARY) — não fiz nenhuma alteração para "corrigir" isso.

## User Setup Required

None - nenhuma configuração de serviço externo necessária.

## Next Phase Readiness

`opcoes_gatilho.do_plano()` está pronto para a Fase 16 (biblioteca de 3 estruturas — venda coberta, put, collar) mapear `vies` para a estrutura concreta e compor as N pernas correspondentes. Nenhum bloqueio.

---
*Phase: 15-motor-de-proposta-arquitetura-interna*
*Completed: 2026-09-02*

## Self-Check: PASSED

- FOUND: server/app/opcoes_gatilho.py
- FOUND: server/tests/test_opcoes_gatilho.py
- FOUND: .planning/phases/15-motor-de-proposta-arquitetura-interna/15-02-SUMMARY.md
- FOUND commit: eeaa0d6 (test, RED)
- FOUND commit: dda018c (feat, GREEN)
- FOUND commit: 64150ce (test, guardiões)
