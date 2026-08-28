---
phase: 10-ponte-gatilho-put
plan: 03
subsystem: options
tags: [put, protecao, guardiao, adr-021, adr-017, put-03, testes]

# Dependency graph
requires:
  - phase: 10-ponte-gatilho-put (plano 01)
    provides: "put_suggestions/put_bridge.triar_put (persistência e triagem)"
  - phase: 10-ponte-gatilho-put (plano 02)
    provides: "put_bridge.run_diario/maybe_run pendurado no scheduler_loop"
provides:
  - "test_put_bridge_sem_superficie.py: guardião permanente de PUT-03 (leitura de fonte + comportamento — status_snapshot, app.routes, agregações do ADR-017)"
  - "ADR-021: registro permanente de onde a sugestão de put mora, garantias de long-only, seletor de acesso e disposição de WR-01"
  - "docs/OPERACAO-ponte-gatilho-put.md: runbook explicando por que a ponte fecha em sugestoes:0 em produção hoje"
affects: [11-ciclo-de-vida-e-monitoramento]

tech-stack:
  added: []
  patterns:
    - "Guardião de ausência (D-10-M): teste que LÊ O FONTE, não que inspeciona diff — sobrevive ao merge seguinte"
    - "Contagem com comentários filtrados (D-10-N) — sem isso o próprio comentário que explica a regra faz o teste passar/falhar sozinho"
    - "Prova dupla: leitura de fonte (grep estrutural) + comportamento real (status_snapshot, app.routes, agregações) — cobre a via de vazamento que nenhum grep de front-end pegaria"

key-files:
  created:
    - server/tests/test_put_bridge_sem_superficie.py
    - docs/adr/021-ponte-gatilho-put.md
    - docs/OPERACAO-ponte-gatilho-put.md
  modified: []

key-decisions:
  - "D-10-A a D-10-O herdadas dos Planos 01/02 (não reabertas) — registradas permanentemente no ADR-021 em vez de só em nota de planejamento"
  - "D-EXEC-10-03-01: acceptance criterion literal do diff origin/main..HEAD sobre mydata_budget.py/options_provider.py/options_provider_mydata.py não é vazio — mas por motivo alheio à Fase 10 (mudanças legítimas da Fase 0/OPTGATE-01, commit 72ce2dc, que origin/main nunca recebeu porque nenhuma fase deste milestone foi pushada). Diff escopado à Fase 10 (9a9d470..HEAD, fim da Fase 0) sobre os mesmos arquivos é vazio, confirmando que nenhum dos 3 planos da Fase 10 tocou os arquivos de gate de orçamento"

requirements-completed: [PUT-03]

duration: ~30min
completed: 2026-08-28
---

# Phase 10 Plan 03: Guardião de PUT-03 + ADR-021 + doc de operação Summary

**Um teste que lê o fonte (não um diff) prova, de forma permanente, que a ponte gatilho→put não alcança nenhuma rota HTTP, vocabulário, front, portal admin, telemetria do agente nem as agregações do Radar que o ADR-017 usa para ranquear setups — e o ADR-021 registra formalmente onde a sugestão mora, por que é long-only por construção, e a decisão pendente sobre WR-01 (race condition do gate de orçamento) que o Alex ainda precisa validar.**

## Performance

- **Duration:** ~30 min
- **Completed:** 2026-08-28
- **Tasks:** 2/2
- **Files modified:** 3 (0 modificados, 3 criados)

## Accomplishments

- `test_put_bridge_sem_superficie.py` materializa PUT-03 com 8 testes, nenhum em `skip` para os arquivos que importam de verdade (`main.py`, `skill_ref.py`, `web/src/`): leitura de fonte com comentários filtrados (`_sem_comentarios`, D-10-N) sobre `main.py`, `skill_ref.py`, TODOS os `.js`/`.jsx` de `web/src/` e `web-admin/src/`, `defaults.py`, `catalog.js` — mais 3 testes de comportamento real (`status_snapshot` não ganha chave com "put", nenhuma rota de `app.main.app.routes` tem "put" no path, e as duas agregações do ADR-017 — `agregar_cumulativo`/`agregar_janela` — continuam `porSetup == {}` mesmo depois de gravar 3 sugestões de put via `put_suggestions.registrar`).
- Prova de RED executada e documentada: um código sentinela (`_PUT_BRIDGE_SENTINELA = "put_suggestions"`, linha de código, não comentário — a filtragem de comentário não teria mascarado essa prova) adicionado temporariamente ao fim de `skill_ref.py` derrubou `test_skill_ref_nao_menciona_put_de_protecao` (1 failed, 7 passed); revertido com `git checkout -- server/app/skill_ref.py`, `git diff --stat` confirmado vazio, suíte de volta a 8/8.
- ADR-021 registra as 4 decisões que o Alex vai querer revisar de manhã: tabela própria (`put_suggestions`, não `signal_ledger` — D-10-A, com o argumento principal sobre `GROUP BY setup` mudar `expR`/ranking visível); garantias estruturais de long-only (`CHECK(option_type='put')`, ausência de coluna de margem/quantidade/lado, `estilo_exercicio`/`iv` `NOT NULL`); acesso só pelo seletor `options_provider` (a ponte nasce dormente com `B3_OPTIONS_PROVIDER=yahoo`, espelhando o mesmo padrão do gate OPTGATE-01); e a disposição explícita de WR-01 (herdado, mitigado por sequencialidade + `MAX_TICKERS_DIA=10`, correção estrutural — lock/fila — reservada para decisão do Alex, não resolvida nesta noite).
- `docs/OPERACAO-ponte-gatilho-put.md` documenta, em 6 seções numeradas (formato-irmão de `docs/OPERACAO-ledger-de-sinais.md`): o que a ponte faz e quando roda; as 2 env vars (`B3_PUT_BRIDGE_HHMM`/`B3_PUT_BRIDGE_OFF`, nenhuma definida em produção); por que `sugestoes: 0` em produção hoje é o desenho, não defeito; a query SQL + a linha de log `[put-bridge]` para inspecionar; os limites de consumo (2 requisições/ticker, teto de 10/dia); e o que explicitamente NÃO existe nesta fase (rota, push, UI, execução simulada, opção vendida).
- Suíte canônica validada 2x com resultado idêntico: `1595 passed, 1 skipped` (backend), `105 .mjs OK`, exit 0 nas duas rodadas — 8 testes a mais que o baseline do Plano 02 (`1587 passed`).
- Diff de superfície visível provado por comando, não por afirmação — ver Decisões Autônomas para a nuance do diff contra `origin/main` (D-EXEC-10-03-01).

## Task Commits

Each task was committed atomically:

1. **Task 1: Guardião de PUT-03** - `06edccc` (test)
2. **Task 2: ADR-021 + doc de operação + fechamento da suíte** - `c7a56f4` (docs)

## Files Created/Modified

- `server/tests/test_put_bridge_sem_superficie.py` — novo: 8 testes (leitura de fonte + comportamento), docstring de cabeçalho explicando por que apagá-lo/afrouxá-lo é reverter PUT-03, não limpar teste morto
- `docs/adr/021-ponte-gatilho-put.md` — novo: ADR no formato do ADR-020 (Status/Data/Decisor/Base/Contexto/4 Decisões/Consequências)
- `docs/OPERACAO-ponte-gatilho-put.md` — novo: runbook no formato de `docs/OPERACAO-ledger-de-sinais.md`, 6 seções numeradas

## Acceptance Criteria (verificadas literalmente do plano)

| Critério | Resultado |
|---|---|
| `pytest tests/test_put_bridge_sem_superficie.py -q` → exit 0, 8 testes, nenhum skip para main.py/skill_ref.py/web/src | PASSOU (8 passed) |
| Prova de RED: sentinela em skill_ref.py derruba o teste; revertido; diff vazio | PASSOU (1 failed com sentinela; `git diff --stat -- server/app/skill_ref.py` vazio depois do revert) |
| `git diff --stat -- web/ web-admin/ server/app/skill_ref.py server/app/main.py server/app/defaults.py` vazio ao fim da Task 1 | PASSOU |
| `bash scripts/executar.sh --testes` exit 0 nas DUAS execuções, contagem idêntica | PASSOU (1595 passed/1 skipped/105 mjs OK, ambas as rodadas) |
| `ls docs/adr/021-ponte-gatilho-put.md docs/OPERACAO-ponte-gatilho-put.md` lista os dois | PASSOU |
| `grep -c "WR-01" docs/adr/021-ponte-gatilho-put.md` ≥ 1 | PASSOU (2) |
| `grep -c "MAX_TICKERS_DIA" docs/adr/021-ponte-gatilho-put.md` ≥ 1 | PASSOU (1) |
| `git diff --stat -- docs/adr/020-*.md docs/OPERACAO-ledger-de-sinais.md` vazio (aditivo) | PASSOU |
| `git status -sb` mostra branch sem tracking remoto — nenhum push | PASSOU (`## worktree-agent-af8bbeb3f9f0d70ba`, sem branch `worktree-agent-*` no `git ls-remote --heads origin`) |
| `git diff --stat origin/main..HEAD -- ... mydata_budget.py options_provider.py options_provider_mydata.py` vazio | **DIVERGIU — ver D-EXEC-10-03-01 abaixo** |

## Decisões autônomas

### D-EXEC-10-03-01: o diff literal `origin/main..HEAD` sobre os arquivos de gate de orçamento não é vazio — por motivo alheio à Fase 10

**Contexto:** o critério de aceite da Task 2 pede `git diff --stat origin/main..HEAD -- web/ web-admin/ server/app/skill_ref.py server/app/main.py server/app/defaults.py server/app/mydata_budget.py server/app/options_provider.py server/app/options_provider_mydata.py` vazio, como "prova literal do Success Criteria 4 do ROADMAP". Rodando o comando literalmente:

```
 server/app/options_provider.py        |  7 ++++
 server/app/options_provider_mydata.py | 69 ++++++++++++++++++++++++++++++++++-
 2 files changed, 75 insertions(+), 1 deletion(-)
```

**Investigação:** `git log --oneline origin/main..HEAD -- server/app/options_provider.py server/app/options_provider_mydata.py` aponta para UM commit só: `72ce2dc feat(00-02): gate e débito de orçamento no adaptador de opções do mydata` — a implementação de OPTGATE-01, da **Fase 0**, já revisada e resumida em `.planning/phases/00-precondi-es/00-02-SUMMARY.md`, sem nenhuma relação com PUT-03 ou com qualquer um dos 3 planos da Fase 10. `mydata_budget.py` não aparece no diff (Fase 0 não o modificou; a Fase 10 também não).

A causa raiz: **nenhuma fase deste milestone foi pushada** para `origin` (constraint absoluto do contrato de autonomia, `git ls-remote --heads origin` confirma ausência de qualquer branch `worktree-agent-*` remota) — então `origin/main` continua no estado de antes da Fase 0 começar (tip real: `b207e41 docs(09-04)...`, Fase 9). O diff `origin/main..HEAD` necessariamente inclui TODOS os commits do milestone v1.2 até agora (Fase 0 inteira + Fase 10 inteira), não só os desta Task/Plano.

**Verificação adicional (não pedida pelo plano, mas necessária para fechar a dúvida):**

```
$ git diff --stat 9a9d470..HEAD -- web/ web-admin/ server/app/skill_ref.py \
    server/app/main.py server/app/defaults.py server/app/mydata_budget.py \
    server/app/options_provider.py server/app/options_provider_mydata.py
(saída vazia)
```

`9a9d470` é o commit de fechamento da Fase 0 (`docs(phase-00): evolve PROJECT.md after phase completion`). O diff escopado à Fase 10 inteira (Planos 01+02+03, que é o que PUT-03/Success Criteria 4 realmente precisam provar) sobre os MESMOS 8 caminhos é vazio — confirmando que nenhum plano da Fase 10 tocou qualquer um desses arquivos, inclusive os 3 de gate de orçamento que a Fase 0 legitimamente mudou antes da Fase 10 começar.

**Decisão:** tratar o resultado literal do comando do plano como a prova textual pedida (colada acima, sem omitir nem embelezar), e ACRESCENTAR a investigação/o diff escopado como evidência de que a divergência é inteiramente atribuível à Fase 0 (já revisada, fora do escopo de PUT-03), não a um vazamento desta fase. Não alterei o comando do critério de aceite nem escondi o resultado — documentei os dois lados.

**Por quê:** o contrato de autonomia proíbe relaxar uma prova estrutural para fazer um critério passar (mesma régua de D-EXEC-10-01-01/D-EXEC-10-02-01dos planos anteriores) — mas aqui o "critério" em si tem uma premissa implícita (que `origin/main` já conteria a Fase 0 no momento em que a Fase 10 rodasse) que não se sustenta sob o guardrail "nenhum `git push`" deste milestone inteiro. A alternativa correta não é forçar o comando a passar (impossível sem tocar `mydata_budget.py`/`options_provider*.py`, o que violaria "nenhuma superfície tocada fora do previsto") nem esconder a divergência — é mostrar os dois diffs lado a lado e deixar a evidência falar.

**Alternativa descartada:** reescrever o critério de aceite para excluir os 3 arquivos de gate de orçamento da lista, "corrigindo" o plano — rejeitada porque o plano foi assinado com essa lista literal (herdada do padrão que os Planos 01/02 já usavam para os MESMOS arquivos, sempre comparando contra o INÍCIO daquele plano específico, nunca contra `origin/main` congelado); reescrever o texto do plano depois de já ter sido executado é o tipo de ajuste que deveria vir do Alex, não do executor.

**Efeito:** nenhuma mudança de código ou de arquivo além dos 3 já documentados nesta Task. Apenas uma seção adicional de evidência nesta SUMMARY. Replicado em `.planning/notes/decisoes-autonomas-v1.2.md`.

## Deviations from Plan

Nenhum desvio de Regra 1/2/3/4. A única decisão autônoma (D-EXEC-10-03-01) é uma clarificação de evidência sobre um critério de aceite cuja premissa (origin/main já conter a Fase 0) não se sustentava sob o guardrail de "nenhum push" — não uma correção de bug nem uma mudança de escopo.

---

**Total deviations:** 0 bugs/gaps auto-corrigidos; 1 decisão autônoma de evidência/interpretação de critério (D-EXEC-10-03-01).
**Impact on plan:** Nenhum. Escopo e comportamento exatamente como especificado; a divergência documentada é sobre uma ferramenta de verificação (comando de diff), não sobre o produto.

## Issues Encountered

- Worktree HEAD estava em `475e0ab` (Fase 9, não continha nenhum commit da Fase 0/Fase 10) — corrigido pelo próprio `<worktree_branch_check>` do harness (`git reset --hard 7c1c25c...`) antes de qualquer leitura/edição, mesmo padrão registrado nos SUMMARYs de 10-01 e 10-02.

## User Setup Required

None. Nenhuma variável de ambiente tocada; `B3_OPTIONS_PROVIDER` nunca lido nem alterado neste plano (Task 1 é só teste; Task 2 é só documentação). Nenhum `git push`, nenhum deploy.

## Next Phase Readiness

- PUT-03 tem prova permanente e automatizada — a Fase 11 (ciclo de vida e monitoramento) pode mexer em `put_suggestions`/`put_bridge` com a garantia de que qualquer vazamento acidental para rota/vocabulário/front/admin/telemetria/ranking do Radar quebra a suíte canônica antes de chegar a revisão humana.
- ADR-021 é o registro permanente que sobrevive ao diretório `.planning/` — a decisão pendente sobre WR-01 (lock/fila/aceitar risco) está documentada em dois lugares (ADR-021 §Decisão 4 e `.planning/notes/decisoes-autonomas-v1.2.md`) para o Alex validar quando quiser, sem bloquear nenhum trabalho futuro.
- `docs/OPERACAO-ponte-gatilho-put.md` está pronto para quem for ler o log de produção e ver `sugestoes: 0` sem contexto — a resposta está a um `grep` de distância.
- Fase 10 (v1.2) está COMPLETA — os 3 planos (01/02/03) entregaram PUT-01/PUT-02/PUT-03. Requirements marcados no `REQUIREMENTS.md` fica a cargo do orquestrador (fora do escopo deste plano, que não toca STATE.md/ROADMAP.md por instrução explícita).
- Pendência não bloqueante herdada (repetida aqui por visibilidade): WR-01 — três consumidores concorrentes em potencial de `mydata_budget` agora (candle_provider, options_provider_mydata, put_bridge), decisão de arquitetura (lock/fila/aceitar risco) pendente do Alex, ver `.planning/notes/decisoes-autonomas-v1.2.md`.

---
*Phase: 10-ponte-gatilho-put*
*Completed: 2026-08-28*

## Self-Check: PASSED

- FOUND: `server/tests/test_put_bridge_sem_superficie.py`
- FOUND: `docs/adr/021-ponte-gatilho-put.md`
- FOUND: `docs/OPERACAO-ponte-gatilho-put.md`
- FOUND: `.planning/phases/10-ponte-gatilho-put/10-03-SUMMARY.md`
- FOUND: commit `06edccc` (Task 1)
- FOUND: commit `c7a56f4` (Task 2)
