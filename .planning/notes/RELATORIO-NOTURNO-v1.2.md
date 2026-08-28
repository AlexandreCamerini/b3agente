---
title: Relatório noturno — Milestone v1.2 (Camada de opções ancorada na carteira)
date: 2026-08-28
context: Execução desassistida overnight, iniciada por pedido explícito do
  Alex com CONTRATO DE AUTONOMIA (sem perguntas, decisões registradas,
  guardrails invioláveis, hard-stops definidos). Config `auto_advance`/
  `skip_discuss` ligados para a duração da execução, revertidos para
  `false` no último commit desta sessão.
---

# Relatório noturno — Milestone v1.2

**Resumo em uma linha:** as 3 fases planejadas (0, 10, 11) rodaram de ponta
a ponta — planejamento, execução, code review, correção pós-review e
verificação de objetivo, cada uma independente — sem nenhum blocker. 76
commits locais, nenhum push. Milestone está código-completo e testado, mas
**não foi marcado como Shipped**: dois itens seguem esperando seu sign-off.

## O que foi feito

### Fase 0 — Precondições
- `ledger_tickers.py`: os 9 tickers com 404 no bootstrap do ledger de sinais
  resolvidos com evidência real — `MRFG3→MBRF3` e `EMBR3→EMBJ3` (renomeação
  confirmada por série de preço contínua de 2 anos), `BRFS3`/`JBSS3`/
  `CRFB3`/`NTCO3`/`CPLE6` excluídos (fusão/deslistagem), `ELET3`/`ELET6`
  deixados `INDETERMINADO` (sem evidência, documentado honestamente, não
  escondido). Varredura real dos 74 tickers do universo fechou com 0 erros.
- `options_provider_mydata.py`: gate de orçamento (`_gate`/`_debita`)
  adicionado, espelhando `candle_provider.py` — refusal HARD (nunca
  soft-pass, porque o caminho de opções só tem 1 elo).
- **Code review: 1 Crítico corrigido** — `signal_ledger_bootstrap.executar()`
  usava o ticker cru (não-normalizado) como chave do ledger; um input tipo
  `--tickers MRFG3.SA` quebraria a idempotência de rerun e infllaria o `n`
  agregado do setup. Corrigido, guardião adicionado.

### Fase 10 — Ponte gatilho→put
- Tabela nova `put_suggestions` (não `signal_ledger` — isolada por desenho
  para não poluir a ponderação do ADR-017), long-only por `CHECK
  (option_type = 'put')`.
- `put_bridge.py`: hook diário no `scheduler_loop` (mesmo padrão de
  `signal_ledger_job`) cruza gatilho de setup × `positions` do usuário,
  seleciona a put de proteção candidata com dados REAIS do hub
  (`estilo_exercicio`/strike/IV nunca assumidos), grava com proveniência.
  Processamento sequencial por ticker (mitiga a race condition WR-01 da
  Fase 9/0, herdada e não resolvida — ver "Itens pendentes" abaixo).
- **Ships dormente em produção por desenho:** `B3_OPTIONS_PROVIDER=yahoo`
  (default, intocado) não expõe `estilo_exercicio`, então a triagem sempre
  zera até a virada da Fase 9 acontecer. Documentado em `docs/adr/021`.
- **Code review: 2 Warnings corrigidos** — WR-01: ticker malformado em
  `positions` de UM usuário abortava `run_diario` para TODOS os usuários do
  dia (contradizendo o próprio isolamento por linha que a função afirmava
  ter). WR-02: strike não-positivo não era rejeitado. Ambos corrigidos com
  guardiões.

### Fase 11 — Ciclo de vida e monitoramento (última fase)
- Máquina de 5 estados (`armada`/`expirada_sem_uso`/`executada_simulada`/
  `monitorada`/`fechada`) inteira em 11 colunas novas de `put_suggestions`.
- **Decisão de arquitetura importante, com evidência dura:** o texto literal
  do ROADMAP ("reusa optionPositions", "dentro da segunda passada") foi
  reinterpretado deliberadamente. Ler literalmente significaria chamar
  `store.buy_option()` — que grava na coleção `optionPositions` e deduz
  `cash` REAIS, ambos já renderizados pela UI existente. Isso violaria
  "nada visível ao usuário" tão explícito no seu pedido. Evidência:
  `store.py:10` (`SECTIONS` inclui `optionPositions`/`cash`/`history`, logo
  são superfície visível por definição) e `agent.py:531` (`_avaliar_opcoes`
  sai cedo se `optionPositions` estiver vazio — pendurar ali seria
  literalmente inerte). Registrado como ADR-022. Verificado
  independentemente pelo plan-checker E pelo verifier, com teste
  comportamental dedicado que monta uma carteira real via `db.kv_set`
  direto e prova JSON byte-idêntico antes/depois de um ciclo completo.
- `intrinseco()` delega para `agent.intrinseco_opcao` real (não reimplementa
  a fórmula do ADR-005).
- Hook diário roda mesmo com kill-switch ligado — é medição, nunca execução
  de ordem (decisão do executor, documentada, verificada).
- **Code review: 0 Crítico, 2 Warnings NÃO corrigidos** (deliberado — ver
  "Itens pendentes" abaixo).
- **Fase fechou como `human_needed`** (9/9 verdades verificadas, zero
  blocker) — dois dos success criteria do ROADMAP divergem do texto literal
  por desenho (ver acima), e os 2 Warnings viram itens de UAT. Persistido em
  `11-HUMAN-UAT.md`, status `pending`. Fase e milestone foram fechados
  mecanicamente esta noite (toda evidência técnica aponta na mesma direção,
  zero blocker), MAS o UAT continua genuinamente pendente da sua revisão —
  não foi marcado como aprovado por mim.

## Números

- **76 commits locais**, nenhum `git push` em nenhum momento.
- **Suíte canônica** (`bash scripts/executar.sh --testes`) verde em TODA
  validação de fase/wave — rodada 2x consecutivas com resultado idêntico
  cada vez, conforme exigido pelo contrato.
- **3 code reviews**, **3 verificações de objetivo**, todas independentes.
- **3 achados Crítico/Warning corrigidos** com guardião de teste (Fase 0
  CR-01, Fase 10 WR-01/WR-02) + **2 Warnings deixados documentados sem
  correção** (Fase 11 WR-01/WR-02, baixo impacto).

## Decisões autônomas — lista completa

Ver `.planning/notes/decisoes-autonomas-v1.2.md` para o detalhe de cada uma
(alternativas descartadas, razão, efeito). Resumo:

- D-AUTO-01..04: setup do milestone (pular archive da Fase 9, pular
  pesquisa, numeração 0/10/11 literal, aprovar roadmap sem perguntar)
- D-EXEC-00-01-01/02: extensão da investigação de tickers além do script
  literal; BRFS3 classificado EXCLUIR em vez de INDETERMINADO
- D-EXEC-00-02-01: fixtures de teste resetam orçamento em todo teste do
  arquivo (isolamento, não produção)
- D-EXEC-10-01-01, D-EXEC-10-02-01/02, D-EXEC-10-03-01: ajustes de
  formatação/documentação para satisfazer guardiões de grep sem mascarar
  literal proibido em docstring
- D-EXEC-11-02-01: hook do ciclo de vida movido para FORA do gate de
  kill-switch — é medição, nunca execução de ordem (a decisão mais
  substantiva desta fase, com evidência dura, verificada 2x)

## Itens pendentes para você decidir

1. **UAT da Fase 11** (`11-HUMAN-UAT.md`) — 3 itens, nenhum bloqueia
   correção, todos pedem seu sign-off explícito antes do milestone virar
   "Shipped":
   - Aceitar a leitura por CONTRATOS do ADR-022 (recomendo aceitar — a
     evidência é forte e foi verificada duas vezes de forma independente)
   - WR-01 (Fase 11): observabilidade de sugestão sem prêmio — aceitar como
     está, ou investir numa das duas correções sugeridas no REVIEW
   - WR-02 (Fase 11): fallback morto — deixar documentado ou endurecer

2. **WR-01 da Fase 0/9** (não resolvido, herdado por Fase 10): a race
   condition check-then-debit em `mydata_budget` agora tem potencialmente
   3 consumidores concorrentes (candle, opções manuais, ponte gatilho→put).
   Decisão de arquitetura (lock? fila? aceitar o risco?) que prefiro que
   você valide.

3. **Rodar `/gsd:complete-milestone`** quando você validar os itens acima —
   isso arquiva `.planning/phases/00-*`, `10-*`, `11-*` para
   `.planning/milestones/v1.2-phases/` e marca v1.2 como Shipped em
   `MILESTONES.md`. Deliberadamente NÃO fiz isso esta noite — é a cerimônia
   de fechamento, faz mais sentido com você no controle.

4. **A camada inteira está dormente em produção** até a virada da Fase 9
   (`B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER=mydata`) acontecer — sem isso,
   `estilo_exercicio` nunca vem do Yahoo e a ponte nunca produz uma
   sugestão real. Isso já estava adiado antes desta madrugada (checkpoint
   da Fase 9); v1.2 não reabre essa decisão, só depende dela para gerar
   dado de medição de verdade.

## O que NÃO foi feito (fora de escopo, por desenho)

- Nenhum deploy, nenhum push, nenhuma variável de produção alterada.
- `B3_OPTIONS_PROVIDER` nunca tocado fora de escopo de teste.
- Nenhuma superfície visível ao usuário em nenhuma das 3 fases (verificado
  por grep + teste dedicado em cada fase).
- Nenhum suporte a opção vendida/short em qualquer forma.
- DSL de setup, estruturas que lançam opção, monitoramento intradiário —
  todos fora de escopo do milestone, como já decidido antes de começar.

## Config revertido

`workflow.auto_advance` e `workflow.skip_discuss` voltam para `false` no
commit que acompanha este relatório — a execução desassistida termina aqui.
