---
phase: 19-motor-multi-candidato
plan: 01
subsystem: api
tags: [python, fastapi, opcoes, pytest, motor-deterministico]

# Dependency graph
requires:
  - phase: 16-biblioteca-de-estruturas
    provides: "_propor_collar() como composição N-pernas do motor comum (opcoes_motor.avaliar), parâmetro multiperna somente-nomeado"
provides:
  - "opcoes_lastreadas.propor() devolve `candidatos` (lista de 1 ou 2 estruturas) nos retornos positivos, aditivo, sem quebrar consumidor existente"
  - "Contrato de interface para 19-02 (rota) e 19-03/19-04 (front): candidatos[0] == proposta, ordem [put_protecao, collar], negativos sem a chave"
affects: [19-02-motor-multi-candidato, 19-03-motor-multi-candidato, 19-04-motor-multi-candidato]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Campo aditivo em dict de retorno determinístico: nova chave com default seguro pro consumidor antigo (`resultado.get('candidatos', [])`), nunca muda tipo/sentido de chave existente"
    - "Tentativa incondicional de estrutura alternativa dentro do mesmo branch, decisão de QUAL retornar feita só no ponto de saída (evita duplicar a chamada em dois returns)"

key-files:
  created: []
  modified:
    - server/app/opcoes_lastreadas.py
    - server/tests/test_opcoes_collar.py

key-decisions:
  - "Collar deixa de ser fallback do caixa insuficiente e passa a ser tentado sempre que multiperna=True e a leitura é de proteção, incondicional a contratos<1 — permite coexistência quando os dois cabem"
  - "candidatos[0] é sempre o objeto proposta (identity, não cópia) e motivo é sempre candidatos[0]['tipo'] — nunca recalculado à parte, para que UI e motivo nunca divirjam"
  - "Retornos negativos permanecem dict de 2 campos, sem candidatos — compat. com ~15 guardiões de igualdade exata de dict já existentes"

patterns-established:
  - "Guardião pré-existente ameaçado por mudança de comportamento é re-verificado com nota na docstring, nunca reescrito silenciosamente (CLAUDE.md: 'guardiões de teste não se apagam')"

requirements-completed: [MULTI-01]

# Metrics
duration: ~45min
completed: 2026-09-04
---

# Phase 19 Plan 01: Motor multi-candidato (propor() com lista de candidatos) Summary

**`opcoes_lastreadas.propor()` devolve `candidatos` (put_protecao + collar coexistindo, ordem travada) nos retornos positivos, aditivo e byte-compatível com o consumidor de hoje.**

> **Critério de sucesso NÃO atingido:** dos 4 itens em `<success_criteria>` do
> plano, "Suíte canônica verde" **não** foi satisfeito literalmente —
> `bash scripts/executar.sh --testes` saiu com código 1 (27 failed) em vez de
> 0. As 27 falhas são pré-existentes e ambientais (sandbox sem egress de rede
> pra Yahoo/Anthropic/OpenAI), não causadas por este plano — evidência
> completa em "Verification Evidence"/"Issues Encountered" abaixo. Não
> reescrevo o critério como satisfeito: fica registrado como não atingido,
> com a justificativa anexa, para o orquestrador/reviewer decidir.

## Performance

- **Duration:** ~45 min (inclui uma correção de base de worktree, ver Issues Encountered)
- **Tasks:** 2/2 completed
- **Files modified:** 2

## Accomplishments
- `propor()` monta `candidatos = [proposta]` (+ `colar` quando não `None`) em todo retorno positivo; `proposta`/`motivo` continuam derivados de `candidatos[0]`, nunca recalculados à parte.
- Collar deixou de ser só fallback do caixa insuficiente: agora é tentado sempre que `multiperna=True` e a leitura é `put_protecao`, incondicional a `contratos < 1` — put e collar coexistem quando os dois cabem.
- 6 testes novos provam coexistência (com identidade de objeto `is`), a negociação de capacidade de `multiperna=False` continua intocada, candidato único em `call_coberta`, collar sozinho quando a put não cabe, ausência deliberada da chave `candidatos` em 3 portas fechadas, e manchete própria por candidato (guardrail CVM).
- Guardião pré-existente (`test_propor_multiperna_true_com_caixa_folgado_mantem_put_protecao`) re-verificado e anotado, sem alteração de asserção.

## Task Commits

Each task was committed atomically:

1. **Task 1: propor() monta a lista de candidatos** - `1754fcb` (feat)
2. **Task 2: guardiões de coexistência, ordem e não-regressão** - `505cd23` (test)

_Nota: os hashes acima são o resultado FINAL após a correção de base descrita em "Issues Encountered" — os commits originais (`6a79055`, `4c64d89`) foram cherry-picked para a base correta e substituídos por estes; o commit intermediário de sincronização de docs (`918d7e0`) tornou-se redundante depois da correção e foi descartado (a base correta já contém os arquivos de planejamento nativamente)._

## Files Created/Modified
- `server/app/opcoes_lastreadas.py` - `propor()` monta `candidatos`; `_propor_collar()` intocada (zero linhas alteradas)
- `server/tests/test_opcoes_collar.py` - 6 testes novos (Fase 19, MULTI-01) + nota de re-verificação num guardião existente

## Decisions Made
- Collar tentado incondicionalmente dentro do branch `put_protecao` (antes do `if contratos < 1`), decisão de retorno feita só no ponto de saída — evita duplicar a chamada a `_propor_collar` em dois `return`s diferentes.
- `candidatos[0] is proposta` (identidade de objeto, não cópia) é a asserção que torna "o card exibido é o que o usuário aceita" verificável por teste, não só uma convenção verbal (ver Threat Register T-19-01 do plano).

## Deviations from Plan

None de código — plano executado exatamente como escrito (edição cirúrgica em `propor()`, `_propor_collar()` sem uma linha tocada, 6 testes + 1 nota de re-verificação, docstring atualizada). Um desvio operacional de infraestrutura de worktree, documentado abaixo.

## Issues Encountered

**Worktree clonado de uma base desatualizada (não relacionado ao código deste plano).** O worktree deste executor foi criado a partir do commit `0b9ead1` (anterior à execução completa da Fase 18 e às commits de planejamento da Fase 19), em vez do commit `a4ae7a84` esperado pelo `worktree_branch_check` do orquestrador — o mesmo padrão já registrado em `agent-isolation-worktree-baseref.md` (memória do usuário). A checagem mandatória de branch no início da execução comparou os hashes incorretamente na primeira leitura (confundi o merge-base retornado com o commit-alvo) e concluiu, errado, que a base já estava correta.

- **Como foi pego:** ao tentar ler `.planning/phases/19-motor-multi-candidato/19-01-PLAN.md`, o arquivo não existia no worktree — os commits de planejamento da Fase 19 (`728bbc4`..`79a1d9b`) não estavam alcançáveis a partir do HEAD do worktree. Recuperei o conteúdo do plano via `git checkout 79a1d9b -- .planning/phases/19-motor-multi-candidato/` (os commits existem no object store compartilhado do repositório principal, mesmo sem estar na história do branch do worktree) e prossegui a execução.
- **Consequência:** as Tasks 1 e 2 foram implementadas e commitadas sobre a base desatualizada. Um `git diff --stat` contra o `a4ae7a84` esperado, feito ao preparar este SUMMARY, revelou um diff enorme e alheio (App.jsx, copy.js, web_dist, planos da Fase 18 inteiros) — sinal de que a base estava errada, não de que o código deste plano tocou esses arquivos.
- **Correção:** confirmei via `git diff 0b9ead1 a4ae7a84 -- server/app/opcoes_lastreadas.py server/tests/test_opcoes_collar.py server/tests/test_opcoes_lastreadas_proposta.py server/tests/test_opcoes_gatilho.py` que os 4 arquivos relevantes eram byte-idênticos entre as duas bases (a Fase 18 não tocou o motor de opções lastreadas). Isso tornou seguro: `git reset --hard a4ae7a84...` (a correção que o próprio `worktree_branch_check` já mandava, preservando os 3 commits originais como objetos nomeados) seguido de `git cherry-pick` dos dois commits de código (Task 1 e Task 2; o commit de sincronização de docs foi descartado por redundância — a base correta já traz `19-CONTEXT.md`/`19-UI-SPEC.md`/etc. nativamente). Os dois cherry-picks aplicaram limpo, sem conflito.
- **Re-verificação pós-correção:** toda a verificação (greps de aceite, indentação do `_propor_collar(`, suíte alvo, suíte canônica completa, suíte web) foi refeita do zero na base corrigida — os números reportados neste SUMMARY (87 passed na suíte alvo, 1989 passed na suíte backend completa, 112 passed na suíte web) são da base correta, não da base errada.
- **Nenhum código de produto foi afetado** por este incidente — é puramente um artefato de infraestrutura de execução (worktree), sem relação com MULTI-01.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Verification Evidence

- `cd server && .venv/bin/python -m pytest tests/test_opcoes_collar.py tests/test_opcoes_lastreadas_proposta.py tests/test_opcoes_gatilho.py -q` → **87 passed** (33 em `test_opcoes_collar.py`, incluindo os 6 novos).
- `bash scripts/executar.sh --testes` (suíte canônica completa) → **1989 passed, 1 skipped, 27 failed**. As 27 falhas são **pré-existentes e ambientais**, não causadas por este plano — todas são `PermissionError: [Errno 1] Operation not permitted` ao tentar rede real (Yahoo/Anthropic/OpenAI) a partir do sandbox de execução deste worktree (sem egress liberado para esses hosts). Confirmado por: (1) nenhum dos 8 arquivos de teste que falham importa `opcoes_lastreadas`; (2) a única falha em arquivo relacionado (`test_opcoes_lastreadas_rotas.py::test_vender_posicao_100_por_cento_travada_via_sell_devolve_400`) falha dentro de `store.sell` tentando `get_quote` via Yahoo — nada a ver com a chave `candidatos`; os outros 27 testes de `test_opcoes_lastreadas_rotas.py` passam limpos quando esse único teste é deselecionado. Lista completa das 27 falhas registrada abaixo, exatamente como pedido pela Task 2 ("reportar o nome do teste, o motivo da quebra e a decisão proposta"), decisão proposta: **nenhuma ação** — ambiente do worktree não tem egress de rede; suíte deve ser reexecutada num ambiente com rede antes do fechamento definitivo da fase (mesma limitação, não nova).
- Suíte web (`web/tests/*.mjs`, 112 arquivos, executados via `node` com `web/node_modules` disponibilizado temporariamente por symlink pro clone principal — removido antes de commitar) → **0 falhas**.
- `git diff --stat a4ae7a84 HEAD` limitado a `server/app/opcoes_lastreadas.py` e `server/tests/test_opcoes_collar.py` (confirmado na base corrigida).
- `git diff a4ae7a84 HEAD -- server/app/skill_ref.py` → vazio.
- `_propor_collar(` chamada no mesmo nível de indentação de `if contratos < 1:` (não aninhada) — confirmado via `sed`.

### Falhas pré-existentes (ambientais, sandbox sem rede) — não corrigidas, fora de escopo

```
tests/test_benchmark_ibov.py::test_payload_feliz_devolve_contrato
tests/test_benchmark_ibov.py::test_close_none_no_meio_e_pulado
tests/test_benchmark_ibov.py::test_granularidade_degradada_levanta_indisponivel
tests/test_benchmark_ibov.py::test_payload_vazio_levanta_indisponivel
tests/test_benchmark_ibov.py::test_quote_unavailable_do_provedor_nao_vaza_detalhe
tests/test_benchmark_ibov.py::test_cache_ttl_evita_segunda_chamada
tests/test_fase3_kill_switch_duracao.py::test_duracao_conhecida_titulo_contem_horas
tests/test_fase3_kill_switch_duracao.py::test_duracao_nao_rastreavel_corpo_diz_variavel_de_ambiente_nunca_0h
tests/test_fase3_kill_switch_duracao.py::test_dedupe_duas_execucoes_seguidas_um_fan_out
tests/test_fase3_kill_switch_duracao.py::test_reset_liga_alerta_desliga_liga_de_novo_alerta_de_novo
tests/test_opcoes_lastreadas_rotas.py::test_vender_posicao_100_por_cento_travada_via_sell_devolve_400
tests/test_options_provider_yahoo.py::test_options_provider_degrades_instead_of_raising_on_yahoo_401
tests/test_push_registro_evento.py::test_gatilho_de_um_ativo_registra_evento_com_o_ticker
tests/test_push_registro_evento.py::test_gatilho_agregado_nao_elege_um_ticker
tests/test_push_registro_evento.py::test_gatilho_sem_entrega_registra_o_evento_assim_mesmo
tests/test_rotas_fase4.py::test_benchmark_ibov_cache_evita_segunda_chamada_ao_provedor
tests/test_texto_vazio.py::test_anthropic_200_sem_texto_levanta_diagnostico
tests/test_texto_vazio.py::test_anthropic_modelo_que_raciocina_tem_teto_alto_e_sem_temperature
tests/test_texto_vazio.py::test_anthropic_modelo_rapido_envia_temperature
tests/test_texto_vazio.py::test_openai_200_sem_conteudo_levanta_diagnostico
tests/test_yahoo_granularidade.py::test_meta_mais_grossa_que_pedido_e_recusada
tests/test_yahoo_granularidade.py::test_meta_igual_ao_pedido_nao_e_recusada
tests/test_yahoo_granularidade.py::test_meta_mais_fina_que_pedido_nao_e_recusada
tests/test_yahoo_intraday.py::test_get_history_intraday_nao_colapsa_a_serie
tests/test_yahoo_intraday.py::test_get_history_diario_inalterado
tests/test_yahoo_intraday.py::test_granularidade_divergente_e_recusada
tests/test_yahoo_intraday.py::test_60m_e_1h_sao_o_mesmo_intervalo
```

## Next Phase Readiness

- Contrato de retorno de `propor()` estabelecido e testado: `19-02-PLAN.md` (rota `POST /api/options/lastreada/abrir-collar` + `GET /api/options/proposta/{ticker}`) pode consumir `candidatos` diretamente, conforme mapeado em `19-PATTERNS.md`.
- **Pendência explícita:** critério de sucesso "suíte canônica verde" não atingido literalmente nesta execução — reexecutar `bash scripts/executar.sh --testes` num ambiente com egress de rede liberado antes de considerar a Fase 19 fechada de verdade (mesma classe de limitação já registrada para a Fase 17, não nova deste plano).

---
*Phase: 19-motor-multi-candidato*
*Completed: 2026-09-04*

## Self-Check: PASSED

- FOUND: server/app/opcoes_lastreadas.py
- FOUND: server/tests/test_opcoes_collar.py
- FOUND: .planning/phases/19-motor-multi-candidato/19-01-SUMMARY.md
- FOUND commit: 1754fcb (Task 1)
- FOUND commit: 505cd23 (Task 2)
