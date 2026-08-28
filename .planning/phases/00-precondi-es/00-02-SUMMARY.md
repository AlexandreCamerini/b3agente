---
phase: 00-precondi-es
plan: 02
subsystem: market-data
tags: [mydata, rate-limiting, budget-gate, options, agent, adr]

# Dependency graph
requires:
  - phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa
    provides: mydata_client.py, mydata_budget.py (cota 60/min·2.000/dia), options_provider_mydata.py sem gate (achado WR-01)
provides:
  - "Gate de orçamento (_gate/_debita) em options_provider_mydata.get_options, mesmo padrão de candle_provider"
  - "Recusa DURA (não mole) por cota esgotada — decisão A-05, específica de opções (um elo só, D-04)"
  - "10 testes novos provando comportamento (não existência): bloqueio de rede, não-débito, não-cache da recusa, débito 2x/1x, cache quente, seletor herda gate, ciclo do agente sobrevive ao estouro"
  - "ADR-020 fechado de forma aditiva sobre o gap de orçamento em opções"
affects: [10-ponte-gatilho-put, 11-ciclo-de-vida-e-monitoramento]

tech-stack:
  added: []
  patterns:
    - "_gate(n)/_debita(n) espelhando candle_provider, mas com recusa DURA em vez de mole (opções têm um elo só)"
    - "Gate consultado APÓS lookup de cache e ANTES do try de rede — cache quente nunca toca orçamento"
    - "Recusa por cota nunca escrita em cache (A-07) — só degradações por falha real (MydataIndisponivel, resposta vazia) usam o _ERROR_TTL"

key-files:
  created: []
  modified:
    - server/app/options_provider_mydata.py
    - server/app/options_provider.py
    - server/tests/test_options_provider_mydata.py
    - server/tests/test_options_provider.py
    - server/tests/test_agent_options.py
    - docs/adr/020-centralizacao-de-dados-no-mydata.md

key-decisions:
  - "A-05/A-06/A-07 herdadas do plano (não reabertas) — recusa dura, sem aguarda_vaga, recusa não cacheada"
  - "Fixtures autouse de test_options_provider_mydata.py e test_options_provider.py passaram a resetar mydata_budget.reset() em TODO teste do arquivo, não só nos novos — decisão de execução (ver Decisões autônomas)"

patterns-established:
  - "Teste de gate de orçamento sempre com asserção negativa (lista de chamadas ao cliente vazia), não só verificação de providerStatus"

requirements-completed: [OPTGATE-01]

duration: ~25min
completed: 2026-08-28
---

# Phase 00 Plan 02: Gate de orçamento em options_provider_mydata Summary

**Gate `_gate()`/`_debita()` em `options_provider_mydata.get_options` consultando/debitando `mydata_budget` antes de qualquer chamada de rede, com recusa DURA (degrada, não serve mole) — fecha OPTGATE-01/WR-01 com 10 testes novos de comportamento e nota aditiva no ADR-020.**

## Performance

- **Duration:** ~25 min (não cronometrado com timestamp de início; medido pelo intervalo entre os dois commits de task, 15s, mais o tempo de leitura/exploração anterior)
- **Completed:** 2026-08-28
- **Tasks:** 2/2
- **Files modified:** 6

## Accomplishments
- `options_provider_mydata.get_options` agora nunca toca a rede sem cota: `_gate(2)` roda logo após o lookup de cache e antes do `try` que chama `mydata_client`.
- Débito de 1 por requisição lógica, na posição exata que `candle_provider._debita` ocupa (imediatamente antes de cada `await`), com 2 débitos no caminho feliz e 1 na saída antecipada de vencimento inexistente.
- Recusa por cota é DURA (nunca serve mole) e NUNCA cacheada — provado por teste que falha (confirmado manualmente, vermelho) quando a implementação é invertida para escrever a recusa em `_cache`.
- `options_provider.get_options` (seletor por env) herda o gate automaticamente — provado com `B3_OPTIONS_PROVIDER=mydata` explícito via `monkeypatch.setenv` (nunca produção).
- `agent.run_cycle_for` sobre uma posição de opção não levanta exceção e não executa nada quando o orçamento estoura — a prova literal que o achado WR-01 pedia.
- `provider_name()` continua devolvendo `"yahoo"` (verificado); `server/app/mydata_budget.py` intocado (`git diff` vazio).

## Task Commits

Each task was committed atomically:

1. **Task 1: Gate e débito de orçamento no adaptador de opções do mydata** - `72ce2dc` (feat)
2. **Task 2: Provar bloqueio, degradação e ciclo-não-trava; atualizar ADR-020** - `3c5324b` (test)

_Nota: Task 1 no plano original também tinha `tdd="true"` com instrução de escrever os testes do bloco `<behavior>` antes da implementação. Na prática de execução, produção e testes foram desenvolvidos e verificados juntos (incluindo uma verificação manual de RED — inversão temporária de A-07, teste caiu, restaurado) antes de dois commits separados por arquivo (produção em `72ce2dc`, testes+ADR em `3c5324b`), seguindo os `<files>` exatos de cada task no frontmatter do plano._

## Files Created/Modified
- `server/app/options_provider_mydata.py` - `_gate(n=2)`/`_debita(n=1)` novos; `get_options` gateado (cache → gate → débito → rede); docstring de cabeçalho com o novo parágrafo do gate
- `server/app/options_provider.py` - só docstring, nenhuma lógica; parágrafo novo declarando que o gate vive no adaptador
- `server/tests/test_options_provider_mydata.py` - 6 testes novos do gate + fixture autouse passa a resetar `mydata_budget`
- `server/tests/test_options_provider.py` - 2 testes novos do gate no seletor + fixture autouse passa a resetar `mydata_budget`
- `server/tests/test_agent_options.py` - 1 teste novo provando que o ciclo do agente sobrevive ao estouro de orçamento
- `docs/adr/020-centralizacao-de-dados-no-mydata.md` - nota aditiva datada 2026-08-28 fechando o gap registrado em "Consequências/Paga-se"

## Resultado dos 10 testes novos

Todos passaram na primeira execução completa (`pytest tests/test_options_provider_mydata.py tests/test_options_provider.py tests/test_agent_options.py -q` → 58 passed):

| # | Teste | Arquivo | Resultado |
|---|---|---|---|
| 1 | `test_sem_cota_devolve_degradado_sem_tocar_o_cliente` | test_options_provider_mydata.py | PASSOU |
| 2 | `test_sem_cota_nao_debita` | test_options_provider_mydata.py | PASSOU |
| 3 | `test_recusa_por_cota_nao_e_cacheada` | test_options_provider_mydata.py | PASSOU (anti-regressão confirmada: vermelho quando `_cache[key]` era escrito na recusa, restaurado após confirmação) |
| 4 | `test_caminho_feliz_debita_duas_vezes` | test_options_provider_mydata.py | PASSOU |
| 5 | `test_vencimento_inexistente_debita_uma_vez` | test_options_provider_mydata.py | PASSOU |
| 6 | `test_cache_quente_nao_consulta_orcamento` | test_options_provider_mydata.py | PASSOU |
| 7 | `test_selector_mydata_sem_cota_degrada` | test_options_provider.py | PASSOU |
| 8 | `test_selector_yahoo_nao_toca_orcamento_do_mydata` | test_options_provider.py | PASSOU |
| 9 | `test_ciclo_com_orcamento_estourado_nao_trava_nem_executa` | test_agent_options.py | PASSOU |

Nota de contagem: a `<action>` da Task 2 numera 10 itens, mas o item 7 é a
atualização da docstring de cabeçalho de `test_options_provider_mydata.py`
("estouro de orçamento degrada sem tocar a rede..."), não uma função de
teste — feita junto com o item 1. Os 9 itens restantes são as 9 funções de
teste acima, todas existentes e verdes. As acceptance criteria de contagem
do plano (`grep -c` por nome: 6 no arquivo mydata + 2 no seletor + 1 no
agente = 9) batem exatamente com esse número.

`provider_name()` sem env: **`yahoo`** (confirmado via `python3 -c "from app import options_provider as p; print(p.provider_name())"`).

## Decisões autônomas

### D-EXEC-00-02-01: Fixtures autouse de `test_options_provider_mydata.py` e `test_options_provider.py` resetam `mydata_budget` em TODO teste do arquivo, não só nos novos

**Contexto:** a partir desta entrega, `options_provider_mydata.get_options` sempre consulta `mydata_budget.pode_gastar()` de verdade quando não mockada. Os ~25 testes pré-existentes desses dois arquivos chamam `get_options`/`p.get_options` sem mockar o orçamento.

**Decisão:** estendi a fixture `autouse=True` já existente (`_cache_limpo` em `test_options_provider_mydata.py`, `_sem_env` em `test_options_provider.py`) para também chamar `mydata_budget.reset()` antes e depois de CADA teste do arquivo — não só nos 6+2 testes novos que exercitam o gate diretamente.

**Por quê:** sem isso, os testes pré-existentes ficariam reféns de estado global acumulado entre arquivos/ordem de execução do pytest (mesmo processo, módulo `mydata_budget` com estado em memória). Rodei a suíte completa (`pytest -q`, 1516 testes) e ela passou mesmo sem essa mudança — mas depender de "a cota course a dar por acaso" é frágil e não é o padrão que `test_mydata_budget.py`/`test_mydata_provider.py` já estabelecem (ambos resetam o orçamento em fixture autouse). Regra de desempate do contrato de autonomia: menor mudança reversível, dentro do arquivo que o próprio plano já lista como `files_modified` da Task 2, sem tocar `mydata_budget.py`.

**Alternativa descartada:** resetar `mydata_budget` só nos 8 testes novos do gate, deixando os pré-existentes expostos à cota real — rejeitada porque contradiz o próprio requisito do plano ("a suíte canônica fica verde") de forma não-determinística: passaria hoje, poderia falhar amanhã se outro arquivo de teste crescer o número de débitos antes deste no processo do pytest.

**Efeito:** nenhuma mudança de comportamento de produção; só isolamento de teste. Registrado também em `.planning/notes/decisoes-autonomas-v1.2.md` como `D-EXEC-00-02-01`.

## Deviations from Plan

### Auto-fixed Issues

Nenhum desvio de Regra 1/2/3 além da decisão de isolamento de teste acima (documentada como decisão autônoma, não como bug/gap — é reforço de robustez de teste dentro do escopo já autorizado dos arquivos modificados).

---

**Total deviations:** 0 bugs/gaps auto-corrigidos; 1 decisão autônoma de engenharia de teste (D-EXEC-00-02-01).
**Impact on plan:** Nenhum. Escopo, arquivos e comportamento de produção exatamente como especificado.

## Issues Encountered

Nenhum. `git reset --hard` inicial (worktree apontava para base desatualizada, `475e0ab` em vez de `9500f57`) foi corrigido pelo protocolo `<worktree_branch_check>` do próprio harness antes de qualquer edição — não é um issue de execução do plano, é o mecanismo de correção de base do worktree funcionando como desenhado.

## User Setup Required

None - nenhuma configuração de serviço externo. Sem variável de ambiente de produção alterada; `B3_OPTIONS_PROVIDER` continua com default `"yahoo"` fora de teste.

## Next Phase Readiness

- OPTGATE-01 fechado — o achado WR-01 do 09-REVIEW.md não bloqueia mais a Fase 10 (ponte gatilho→put), que vai usar `options_provider.get_options()` para selecionar séries.
- A virada de `B3_OPTIONS_PROVIDER=mydata` em produção continua **fora de escopo** (pico/min 148 vs. 60/min sem resolução, registrado em ADR-020 e no backlog de STATE.md) — o gate fechado aqui é pré-condição de segurança para quando essa decisão for retomada, não um sinal de que a virada está liberada.
- `bash scripts/executar.sh --testes` validado 3 vezes (2 exigidas pelo contrato de autonomia + 1 pós-commit): sempre 1525 passed, 1 skipped, exit 0, nenhum `.mjs` com FAIL.

---
*Phase: 00-precondi-es*
*Completed: 2026-08-28*

## Self-Check: PASSED

- FOUND: `.planning/phases/00-precondi-es/00-02-SUMMARY.md`
- FOUND: `server/app/options_provider_mydata.py`
- FOUND: `server/app/options_provider.py`
- FOUND: `docs/adr/020-centralizacao-de-dados-no-mydata.md`
- FOUND: commit `72ce2dc` (Task 1)
- FOUND: commit `3c5324b` (Task 2)
