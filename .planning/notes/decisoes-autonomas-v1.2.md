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

## ⚠ Item para decisão sua de manhã (não é hard-stop, mas pede seu julgamento)

**WR-01 — gate de orçamento com race condition check-then-debit, agora em
DOIS consumidores.** `mydata_budget.pode_gastar()`/`.debita()` não são
atômicos: duas chamadas concorrentes podem ambas passar `pode_gastar()`
antes de qualquer uma debitar, estourando a cota. Padrão pré-existente
(compartilhado com `candle_provider`/`brapi_budget`, achado já conhecido da
Fase 9), e o Plano 00-02 o duplicou para `options_provider_mydata.py` sem
resolver — decisão correta do executor (não era escopo do achado original,
corrigir seria scope creep numa noite autônoma). A Fase 10 (ponte
gatilho→put) vai chamar esse mesmo gate a partir de um hook novo no
scheduler — um TERCEIRO consumidor concorrente em potencial. Não bloqueei a
execução da Fase 10 por isso (não está na lista de PARADA DURA do contrato,
e o gate segue funcionalmente correto para chamada isolada), mas é o tipo
de decisão de arquitetura (lock? fila? aceitar o risco de estouro
ocasional?) que prefiro que você valide antes de eu considerar resolvido.

## Log cronológico

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

## Execução da Fase 0, Plano 01 (LEDGER-01 — diagnóstico dos 9 tickers 404)

### D-EXEC-00-01-01: Estender a investigação além das 3 sondas literais do script de diagnóstico

**Decisão:** além das 3 sondas descritas no `<action>` da Task 1 do
`00-01-PLAN.md` (sonda primária, sonda de alias por raiz do ticker, sonda
de contraprova via `candle_provider`), o executor rodou uma verificação
suplementar contra o Yahoo real: metadado de `/v7/finance/quote` (distingue
"código nunca existiu para o Yahoo" de "código existe mas está inativo") e
`/v1/finance/search` por NOME da empresa, não só pela raiz do ticker.
**Por quê:** a sonda de alias por raiz só encontra renomeação quando o
DÍGITO final muda, não quando a RAIZ inteira muda (ex.: `EMBR` → `EMBJ`,
Embraer). Rodando só o script literal, `MRFG3` e `EMBR3` — que tinham
renomeação real, confirmável e evidenciável por série de preço contínua de
2 anos — teriam ficado `INDETERMINADO` por limitação de busca, não por
ausência real de dado.
**Alternativa descartada:** marcar os 9 como `INDETERMINADO` sempre que a
sonda de alias por raiz não encontrasse candidato — mais fiel à letra do
`<action>`, mas deixaria 2 renomeações reais sem fechar sem necessidade.
**Efeito:** `server/app/ledger_tickers.py` nasce com 2 `ALIASES`
(`MRFG3→MBRF3`, `EMBR3→EMBJ3`) e 5 `EXCLUIR` em vez de 7 tickers a mais em
`INDETERMINADO`. Reversível: um diagnóstico futuro pode reclassificar
qualquer entrada trocando só o dicionário. Ver
`docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md` seção 5 e
`.planning/phases/00-precondi-es/00-01-SUMMARY.md`.

### D-EXEC-00-01-02: BRFS3 classificado `EXCLUIR`, não `INDETERMINADO`

**Decisão:** BRFS3 recebeu veredito `EXCLUIR` (fusão com Marfrig em "MBRF
Global Foods Company S.A.") apesar de não haver uma sucessora de BRF
encontrada sob nenhum código — a evidência é circunstancial (nome da
entidade combinada + ausência total de registro de BRFS3 no Yahoo), não uma
sucessora direta testada com série de preço própria.
**Por quê:** `BRFS3.SA` está VAZIO no quote do Yahoo (nem stub inativo,
diferente de CRFB3/JBSS3/NTCO3) e `MBRF3.SA` confirma uma fusão real
Marfrig+BRF pelo nome, mas a série de MBRF3 tem patamar de preço de
Marfrig, não de BRF — evidência (não prova definitiva) de que BRF foi
incorporada via troca de ações. `EXCLUIR` e `INDETERMINADO` têm efeito
IDÊNTICO em `ledger_tickers.EXCLUIDOS` (ambos removem o ticker do
bootstrap) — a diferença é só o rótulo de documentação.
**Alternativa descartada:** `INDETERMINADO` — mais conservador, mas
esconderia a evidência real encontrada atrás de um rótulo que sugere
"nenhuma pista". Optou-se pela opção que preserva mais informação no texto
sem mudar o efeito prático no bootstrap (critério de reversibilidade do
contrato de autonomia).
**Efeito:** `BRFS3` entra em `EXCLUIDOS` com razão citando a fusão, não com
o prefixo `não resolvido em 2026-08-28:`. Ver
`docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md` veredito BRFS3 e
`.planning/phases/00-precondi-es/00-01-SUMMARY.md`.

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

## Execução da Fase 10, Plano 01 (persistência e triagem da put de proteção)

### D-EXEC-10-01-01: docstring de `put_bridge.py` reescrita para não conter o literal `"calls"`

**Decisão:** troquei, na docstring de módulo de `server/app/put_bridge.py`, a
frase que citava literalmente `payload["calls"]` por "a perna de opção de
compra do payload" — mesmo conteúdo semântico, sem o literal.

**Por quê:** o critério de aceite da Task 2 do `10-01-PLAN.md` exige `grep -v
'^#' server/app/put_bridge.py | grep -c "calls"` == 0, como prova estrutural
de que a triagem nunca lê a perna de call (mais rígida que "a função não
lê o campo" — sobrevive a uma futura edição que reintroduza leitura de
`calls` sem aparecer no diff da lógica). `grep -v '^#'` só filtra linhas que
COMEÇAM com `#`; não filtra texto dentro de uma docstring de módulo (string,
não comentário `#`). O primeiro rascunho da docstring citava
`payload["calls"]` para explicar o escopo e o guardião falhava mesmo com a
implementação correta.

**Alternativa descartada:** relaxar o critério de aceite (remover o
`grep -c calls` da verificação) — rejeitada porque o critério vem do plano
assinado; afrouxar uma prova estrutural para acomodar um texto explicativo é
o tipo de atalho que o contrato de autonomia proíbe.

**Efeito:** um parágrafo da docstring de `server/app/put_bridge.py`. Nenhuma
mudança de comportamento — `triar_put` já nunca lia `payload.get("calls")`
antes do ajuste. Ver `.planning/phases/10-ponte-gatilho-put/10-01-SUMMARY.md`.

