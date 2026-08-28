# ADR-021: Ponte gatilho→put — onde a sugestão mora

**Status:** Aceito
**Data:** 2026-08-28
**Decisor:** Alex (executado sob contrato de autonomia noturna)
**Base:** ROADMAP v1.2 Fase 10; requisitos PUT-01/PUT-02/PUT-03; achado
WR-01 do `09-REVIEW.md`.

---

## Contexto

A Fase 10 constrói a ponte entre um sinal de setup (gatilho de baixa
detectado pelo motor determinístico) e uma sugestão de put de proteção
sobre um ticker que o usuário já tem em carteira: um detector EOD roda
dentro do `scheduler_loop` já existente, cruza o Radar diário armazenado com
as carteiras de todos os usuários, seleciona UM contrato de put candidata a
partir de uma cadeia real do provedor de opções ativo e grava a sugestão com
proveniência. Duas decisões de arquitetura do milestone já estavam travadas
antes desta fase começar e este ADR as documenta em vez de reabri-las: (1)
o ciclo é **EOD de ponta a ponta** — sem preço de opção ao vivo, sem
segunda passada intraday; (2) só existe **put COMPRADA, long-only** — uma
perna, sem margem, sem atribuição, sem qualquer forma de opção vendida ou a
descoberto.

## Decisão 1 — tabela própria `put_suggestions`, não o `signal_ledger`

A sugestão de put é gravada numa tabela SEPARADA (`put_suggestions`,
`server/app/put_suggestions.py`), não no `signal_ledger` que já existe para
sinais de ação (ADR-017).

Os 3 argumentos (D-10-A do Plano 01):

1. **`agregar_cumulativo()` é `GROUP BY setup` sobre a tabela inteira.**
   `signal_ledger.agregar_cumulativo`/`agregar_janela` somam `r` e contam
   `n` por `setup`, sem nenhuma coluna discriminadora de "isto é uma linha
   de ação, isto é uma linha de opção". Uma linha de put gravada ali mudaria
   `expR` — o número exato que `regime.ranquear()` consome como peso para
   ordenar setups no Radar **VISÍVEL**. É o principal argumento: o vazamento
   não aconteceria por nenhuma rota, nenhum texto, nenhum componente de
   front — aconteceria por um número que já é lido no cálculo do ranking, um
   caminho que nenhum grep de front-end pegaria.
2. **Contratos de dado divergentes.** `signal_ledger` é indexado por
   `(ticker, setup, lado, data_sinal)` e mede desfecho de UM sinal de ação
   (`alvo`/`stop`/`expirou`/`sem_gatilho`). Uma sugestão de put carrega
   campos que não têm equivalente ali: `contrato`, `strike`, `vencimento`,
   `estilo_exercicio`, `iv`, `delta`, `premio` — forçar os dois num mesmo
   schema exigiria colunas nulas na maioria das linhas de cada tipo.
3. **Ciclo de vida diferente.** `signal_ledger` é write-once/replay
   (backtest, ADR-016/017); `put_suggestions` nasce em `armada` e vai
   evoluir (`expirada sem uso` → `executada (simulada)` → `monitorada` →
   `fechada`, Fase 11/PUTLIFE-01) — um ciclo de vida próprio, incompatível
   com a tabela de backtest.

**Alternativa descartada:** acrescentar uma coluna `tipo` ao `signal_ledger`
e filtrar `WHERE tipo = 'acao'` nas duas agregações. Rejeitada porque
depende de disciplina de manutenção futura — qualquer query nova sobre
`signal_ledger` (e existem várias, ver `signal_ledger_bootstrap.py`,
`signal_ledger_job.py`) precisaria lembrar do filtro para sempre, e um
único `SELECT` esquecido reabriria exatamente o vazamento que esta decisão
existe para fechar. Tabela separada torna o vazamento estruturalmente
impossível em vez de disciplinarmente evitável.

## Decisão 2 — garantias estruturais de long-only

`put_suggestions` tem três camadas de defesa contra qualquer representação
de posição vendida, nenhuma delas opcional:

- `CHECK (option_type = 'put')` no schema (`server/app/db.py`, bloco
  `put_suggestions`) — uma linha com `option_type='call'` levanta
  `sqlite3.IntegrityError` na gravação, provado por teste com SQL bruto
  (`10-01-SUMMARY.md`).
- **Ausência estrutural** de qualquer coluna de quantidade, margem, garantia
  ou lado da operação (comprado/vendido) — a tabela não tem onde gravar uma
  posição vendida mesmo que alguém tentasse.
- `estilo_exercicio` e `iv` são `NOT NULL`, e `registrar()`
  (`put_suggestions.py`) filtra `CAMPOS_OBRIGATORIOS` **antes** de tentar o
  INSERT — um contrato sem proveniência mínima real nunca chega a gravar
  linha, nunca é completado por default.

Declaração explícita: não existe caminho de código nesta fase que possa
produzir uma posição vendida. Se algum dia existir, esse caminho terá que
derrubar o `CHECK` primeiro — que é exatamente o ponto de ter o `CHECK`: a
barreira não depende de nenhum código de aplicação continuar correto, só do
schema.

## Decisão 3 — acesso pelo seletor `options_provider`, e a ponte nasce dormente

`put_bridge.run_diario` chama exclusivamente `options_provider.get_options()`
— o seletor por env já estabelecido pelo ADR-020 (D-02), nunca
`options_provider_mydata`/`options_provider_yahoo` diretamente (D-10-I do
Plano 02, guardião estático `grep -c "options_provider_mydata"` == 0 sobre
`put_bridge.py`). A consequência é aceita explicitamente: com
`B3_OPTIONS_PROVIDER=yahoo` — o default de produção, que este milestone
**não muda** — o contrato do Yahoo não publica `exerciseStyle`;
`triar_put()` pula todo contrato sem esse campo (`puladosSemEstilo`) e a
rodada diária fecha em `"nenhuma put elegível"` para todo ticker. A ponte
nasce **dormente** em produção, por desenho, não por defeito.

Isso espelha o mesmo padrão do gate de orçamento OPTGATE-01 (Fase 0/Plano
02, nota aditiva ao ADR-020): o gate fecha um achado de segurança
independentemente de a virada de `B3_OPTIONS_PROVIDER=mydata` já ter
acontecido ou não — ele é pré-condição para quando essa decisão for
retomada, não a decisão em si. Aqui, a ponte inteira é construída e testada
de ponta a ponta, pronta para produzir sugestões reais no dia em que o
seletor apontar para `mydata` (decisão de negócio/arquitetura fora do
escopo de v1.2, ver `.planning/notes/decisoes-autonomas-v1.2.md` e o item
"Retomar virada de produção do mydata" em `STATE.md`).

## Decisão 4 — WR-01 (check-then-debit não-atômico): herdado, com mitigação, e reservado para decisão do Alex

`mydata_budget.pode_gastar()`/`.debita()` não são atômicos: duas chamadas
concorrentes podem ambas passar `pode_gastar()` antes de qualquer uma
debitar, estourando a cota compartilhada (60/min · 2.000/dia). Este é um
achado **pré-existente** (mesmo padrão em `candle_provider`/`brapi_budget`,
já conhecido da Fase 9/09-REVIEW.md), que o Plano 00-02 duplicou para
`options_provider_mydata.py` (OPTGATE-01) sem resolver — corrigir a atomicidade
ali estava fora do escopo daquele achado. A Fase 10 chama o mesmo gate a
partir de um hook novo no `scheduler_loop` (`put_bridge.maybe_run`) — um
**terceiro** consumidor concorrente em potencial.

Análise da janela real (D-10-H do Plano 02): a distância entre `_gate` (que
chama `pode_gastar()`) e o primeiro `_debita()` dentro de
`options_provider_mydata.get_options` não contém nenhum `await` — logo não
intercala com outra coroutine no laço de eventos de thread única do
FastAPI/uvicorn. A ponte em si não abre uma janela de corrida nova; ela
apenas soma um consumidor a mais na mesma janela pré-existente (a que já
existe entre o hook do radar/ledger e uma eventual chamada HTTP simultânea
de usuário).

Duas mitigações concretas, aplicadas nesta fase:

1. **Consulta sequencial, nunca concorrente.** `run_diario` percorre os
   tickers elegíveis num `for`/`await` simples — PROIBIDO qualquer fan-out
   concorrente (`asyncio.gather`/`create_task`) dentro da ponte. Provado por
   teste de reentrância (`test_consulta_e_sequencial_nunca_concorrente`,
   `10-02-SUMMARY.md`): um contador de chamadas simultâneas nunca passa de
   1, mesmo com um `await` real dentro do fake — não é só ausência de
   `gather` no grep, é comportamento provado.
2. **Teto duro `MAX_TICKERS_DIA=10`.** No pior caso, a ponte soma no máximo
   10 chamadas/dia ao consumo total do gate (≤20 requisições, contando as 2
   requisições/ticker de `find_tradable_options`) — 1% do orçamento diário
   de 2.000, e a rodada roda 1x/dia útil, fora do horário de pico do radar
   (09:30, depois do Radar 08:45 e do ledger 09:15).

**O que NÃO foi feito, e por quê:** nenhum lock/CAS foi introduzido em
`mydata_budget`. Corrigir a atomicidade do gate é uma mudança de padrão
compartilhado — o mesmo módulo é consumido por `candle_provider.py` e
`options_provider_mydata.py` fora desta fase, e uma correção de
concorrência ali afetaria consumidores que este plano não testou nem tinha
escopo para revalidar. Registrado explicitamente como item de decisão do
Alex, não como pendência escondida — ver a nota "⚠ Item para decisão sua de
manhã" no topo de `.planning/notes/decisoes-autonomas-v1.2.md`: a escolha
entre lock, fila, ou aceitar o risco residual de estouro ocasional é uma
decisão de arquitetura que o contrato de autonomia desta fase não autoriza
a resolver sozinha.

## Consequências

**Fica mais fácil:**
- Adicionar um novo detector de gatilho (`LADO_GATILHO`) sem tocar em
  `signal_ledger` nem no ranking do Radar — a superfície de gravação de put
  é isolada por desenho.
- Auditar o long-only estruturalmente, sem depender de revisão de código
  contínua — o `CHECK` do schema é a garantia, não um teste que alguém
  precisa lembrar de rodar.
- Ligar a ponte em produção no dia em que `B3_OPTIONS_PROVIDER=mydata` for
  aprovado — nenhum código muda, só o valor do seletor de env.

**Fica mais difícil:**
- Consultar sugestão de put e sinal de ação numa única query — são duas
  tabelas, dois módulos; qualquer relatório futuro que precise dos dois
  precisa fazer o join explicitamente (decisão deliberada, ver Decisão 1).
- Medir o efeito real da ponte em produção enquanto ela permanecer dormente
  (Decisão 3) — sem `exerciseStyle` do Yahoo, `puladosSemEstilo` é o único
  sinal observável, e ele vive só em `LAST_RUN` (memória), não em nenhuma
  superfície (D-10-L, ver `docs/OPERACAO-ponte-gatilho-put.md` §4).

**A revisitar:**
- (a) Alargar `LADO_GATILHO` para cobrir outros lados/setups de gatilho,
  quando a Fase 11 (ciclo de vida) tiver dado real para calibrar o que vale
  a pena sugerir.
- (b) Tornar `mydata_budget` atômico (lock ou fila) — decisão de
  arquitetura pendente do Alex (Decisão 4), agora com três consumidores
  concorrentes em potencial em vez de um.
- (c) Expor a sugestão na UI — é PUTUI-01, fora do roadmap de v1.2, e
  depende da medição interna deste milestone confirmar que a ponte produz
  sugestões de qualidade suficiente antes de virar superfície visível.
