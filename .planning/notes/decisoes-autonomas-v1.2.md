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

