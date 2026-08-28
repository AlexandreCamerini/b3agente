---
title: Decisões autônomas — Milestone v1.2 (Camada de opções ancorada na carteira)
date: 2026-08-28
context: Execução desassistida noturna sob CONTRATO DE AUTONOMIA do Alex.
  Toda decisão que normalmente viraria pergunta é registrada aqui, com
  alternativas descartadas e razão, para revisão de manhã. Viés de
  desempate: menor, reversível, mantém a feature invisível.
---

# Decisões autônomas — v1.2

Lista consolidada. Cada fase também registra suas decisões no próprio
DISCUSSION-LOG; esta lista é o resumo para leitura rápida de manhã.

## Setup do milestone (/gsd-new-milestone)

### D-AUTO-01: Pular `phases.clear --confirm` na inicialização do milestone
**Decisão:** não rodar o passo de limpeza/arquivamento de diretórios de fase
do workflow `new-milestone`.
**Por quê:** `init.new-milestone` reporta `phase_archive_path:
".planning/milestones/v1.1-phases"` — ou seja, o comando arquivaria o
único diretório de fase existente (`09-centraliza-o-de-dados-de-mercado-
mydata-client-py-implementa`) dentro da pasta de arquivo do milestone
v1.1. Isso é factualmente errado: a Fase 9 é standalone, executada DEPOIS
do v1.1 shipar, fora de qualquer milestone. Arquivá-la sob "v1.1-phases"
reescreveria a proveniência do histórico do projeto.
**Alternativas descartadas:** rodar `phases.clear` mesmo assim (rejeitada —
violaria "histórico não se reescreve"); arquivar manualmente a Fase 9 sob
um nome correto (rejeitada — fora do escopo desta tarefa, decisão de
organização do Alex, não peça de execução do milestone).
**Efeito:** `.planning/phases/09-...` permanece no lugar, intocado. Os
novos diretórios de fase (`00-*`, `10-*`, `11-*`) nascem ao lado dele.

### D-AUTO-02: Pular pesquisa de domínio (Step 8 do new-milestone)
**Decisão:** não spawnar os 4 pesquisadores paralelos antes de definir
requisitos.
**Por quê:** `research_enabled: false` no config (default do projeto) e o
escopo entregue pelo Alex já é pré-pesquisado em detalhe — cita arquivos
exatos (`agent.py::scheduler_loop`, `find_tradable_options` no MCP do
mydata), ADRs específicas (003/004/005/015/016/017/020), decisões de
arquitetura já fechadas (EOD, put comprada long-only) e razões de exclusão
de escopo. Pesquisa de mercado/stack não agregaria nada que não esteja já
decidido.
**Alternativas descartadas:** rodar pesquisa mesmo assim "por padrão" —
rejeitada, gastaria tempo/tokens de uma noite finita sem mudar nenhuma
decisão já travada pelo Alex.

### D-AUTO-04: Roadmap aprovado sem apresentar para confirmação
**Decisão:** aprovar o roadmap gerado pelo `gsd-roadmapper` (3 fases, 9/9
requirements cobertos) sem parar em `AskUserQuestion`.
**Por quê:** o contrato de autonomia proíbe perguntas; o roadmapper formalizou
exatamente o escopo que o Alex já ditou linha a linha (fases, requirements,
guardrails, decisões travadas) — não há decisão de produto nova para
confirmar, só verificação de fidelidade ao pedido, que foi feita por leitura
do arquivo antes de commitar.
**Efeito:** `.planning/ROADMAP.md`/`STATE.md`/`config.json` commitados em
`3020441`.

### D-AUTO-03: Numeração de fase não-sequencial (0, 10, 11) honrada literalmente
**Decisão:** instruir o roadmapper a criar as fases com os números exatos
que o Alex especificou (Fase 0, Fase 10, Fase 11), não a numeração
contígua padrão do workflow (que continuaria de onde a Fase 9 parou, ex.:
10, 11, 12).
**Por quê:** o Alex nomeou explicitamente "Fase 0" (precondições) e "Fase
10"/"Fase 11" no pedido — Fase 10 é deliberadamente a continuação direta
do número da Fase 9 (a "ponte" lógica), e Fase 0 sinaliza precondição
midstream, não o início cronológico do produto. Seguir a numeração padrão
do workflow renomearia a intenção do Alex sem necessidade.
**Efeito:** diretórios `00-precondicoes-...`, `10-ponte-gatilho-put-...`,
`11-ciclo-de-vida-e-monitoramento-...`.

## Execução da Fase 0, Plano 02 (`/gsd:execute-phase`)

### D-EXEC-00-02-01: Fixtures autouse de `test_options_provider_mydata.py` e
`test_options_provider.py` resetam `mydata_budget` em TODO teste do
arquivo, não só nos novos

**Decisão:** estender a fixture `autouse=True` já existente em cada arquivo
(`_cache_limpo`/`_sem_env`) para também chamar `mydata_budget.reset()` antes
e depois de CADA teste do arquivo — não só nos 8 testes novos que exercitam
o gate de orçamento diretamente.

**Por quê:** a partir desta entrega (OPTGATE-01), `options_provider_mydata.
get_options` sempre consulta `mydata_budget.pode_gastar()` de verdade
quando não mockada. Os ~25 testes pré-existentes desses dois arquivos
chamam `get_options`/`p.get_options` sem mockar o orçamento; sem reset,
ficariam reféns de estado global acumulado entre arquivos/ordem de
execução do pytest (mesmo processo, módulo `mydata_budget` com estado em
memória). A suíte completa passou mesmo sem essa mudança (testado), mas
depender de "a cota dar por acaso" é frágil e contraria o padrão que
`test_mydata_budget.py`/`test_mydata_provider.py` já estabelecem (ambos já
resetam o orçamento em fixture autouse).

**Alternativas descartadas:** resetar `mydata_budget` só nos 8 testes novos
do gate, deixando os pré-existentes expostos à cota real — rejeitada
porque tornaria "a suíte canônica fica verde" não-determinístico: passa
hoje, pode falhar amanhã se outro arquivo de teste crescer o número de
débitos antes deste no processo do pytest.

**Efeito:** nenhuma mudança de comportamento de produção; só isolamento de
teste, dentro dos arquivos que o próprio `00-02-PLAN.md` já lista como
`files_modified` da Task 2. Detalhe completo em
`.planning/phases/00-precondi-es/00-02-SUMMARY.md`.

