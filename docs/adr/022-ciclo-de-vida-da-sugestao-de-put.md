# ADR-022: Ciclo de vida da sugestão de put — a simulação mora na sugestão, não na carteira

**Status:** Aceito
**Data:** 2026-08-28
**Decisor:** Alex (executado sob contrato de autonomia noturna)
**Base:** ROADMAP v1.2 Fase 11; requisitos PUTLIFE-01/PUTLIFE-02/PUTLIFE-03/
PUTLIFE-04; ADR-021 (Fase 10); ADR-003/ADR-004/ADR-005 (motor de opções da
carteira real).

---

## Contexto

A Fase 10 deixou a sugestão de put presa no estado `armada`, sem ciclo de
vida: a linha nascia gravada em `put_suggestions` e nunca mais avançava. O
ROADMAP v1.2 pedia, para a Fase 11, que o ciclo de vida **reusasse**
`optionPositions` e os contratos já estabelecidos por ADR-003 (coleção
própria de posição de opção), ADR-004 (nunca marcar posição sobre dado não
confiável) e ADR-005 (liquidação por vencimento pelo valor intrínseco,
inclusive zero). As duas decisões de arquitetura travadas do milestone
continuam valendo e este ADR não as reabre: (1) EOD de ponta a ponta — sem
preço de opção ao vivo, sem segunda passada intraday; (2) só put COMPRADA,
long-only — sem margem, sem atribuição, sem qualquer forma de opção vendida.

## Decisão 1 — a simulação vive nas colunas da própria tabela de sugestões, não na carteira do usuário

`put_suggestions` ganhou 11 colunas de ciclo de vida (`estado`, `estado_em`,
`executada_em`, `preco_entrada`, `spot_marcacao`, `intrinseco_marcacao`,
`marcada_em`, `fechada_em`, `preco_fechamento`, `motivo_fechamento`,
`pnl_por_acao`, `pendente_desde`) em vez de a Fase 11 chamar
`store.buy_option`/`store.sell_option` para materializar a sugestão como uma
posição real em `optionPositions`. PUTLIFE-02 (a garantia de que o ciclo de
vida nunca toca a carteira real) é o coração deste ADR, sustentado por duas
evidências duras, com caminho e linha:

- **(a)** `server/app/store.py:10` — `SECTIONS = ["config", ..., "cash",
  "positions", "history", ..., "optionPositions", "pendingOrders"]`. As três
  seções que compõem a carteira visível do usuário (`cash`, `positions`,
  `history`) e `optionPositions` estão todas na lista de seções exportadas
  para o front. Uma "sugestão invisível" que virasse posição real ali
  contradiria o objetivo de topo do milestone ("sem mostrar nada ao usuário
  neste milestone") — o vazamento não precisaria de rota nova, só de uma
  chamada a uma função que já escreve numa seção já exportada.
- **(b)** `server/app/agent.py:531` — `_avaliar_opcoes` (a segunda passada do
  `scheduler_loop` que avalia posições de opção reais) começa com
  `opts = store.get(conn, "optionPositions", user_id=scope) or []` seguido de
  `if not opts or option_quotes_getter is None: return executed`. Pendurar o
  ciclo de vida literalmente nesse caminho (como uma leitura ingênua do
  ROADMAP poderia sugerir) faria o monitoramento nunca rodar sem que o
  usuário já tivesse uma posição de opção REAL comprada — a leitura literal
  não é só arriscada, é tecnicamente inerte.

O que "reusar os ADR-003/004/005" passou a significar em concreto, sem tocar
a carteira: `put_lifecycle.forma_adr003()` produz o shape ADR-003
deliberadamente **sem** a chave `qty` — estruturalmente incapaz de virar uma
posição real, porque as funções de compra/venda de opção do motor dependem
dela para operar; ADR-004 (nunca marcar sobre dado não confiável) vira a
regra de que `run_diario` só marca `spot_marcacao`/`intrinseco_marcacao`
quando `candle_cache.peek` devolve um candle real, senão grava
`pendente_desde` e tenta de novo no próximo dia; ADR-005 (intrínseco na
liquidação, inclusive zero) vira `put_lifecycle.intrinseco()`, wrapper fino
sobre `agent.intrinseco_opcao` — a MESMA função pura que a carteira real usa
— reusada por import local, nunca copiada, e o vocabulário de motivo
(`MOTIVO_VENCIMENTO = "vencimento"`) é o literal do ADR-005, verbatim.

**Alternativa descartada:** chamar `store.buy_option`/`store.sell_option`/
`store.close_option_vencida` diretamente quando a sugestão "executasse".
Rejeitada pelas duas evidências acima — criaria uma posição de opção real,
visível na carteira e no patrimônio do usuário, o que é exatamente a
superfície que este milestone existe para não expor antes da medição
interna confirmar que a ponte produz sugestões de qualidade.

## Decisão 2 — as 5 transições e o gatilho da execução simulada

Os tokens de coluna (`armada`, `expirada_sem_uso`, `executada_simulada`,
`monitorada`, `fechada`) são DB-friendly (sem espaço/parêntese, fonte de bug
previsível em query — A-11-04 do `11-01-PLAN.md`); o rótulo literal do
ROADMAP fica preservado byte a byte em `ESTADOS_ROTULO`: `expirada sem uso` e
`executada (simulada)` são o texto que o produto usa para descrever o
estado, os tokens são só a representação interna de coluna.

Tabela de transições declaradas (`put_suggestions.TRANSICOES`), a única
porta de escrita de estado (`transicionar()`) recusa (devolve `0`) qualquer
destino fora desta tabela:

| Origem | Destinos válidos | Condição |
|---|---|---|
| `armada` | `expirada_sem_uso` | vencimento chegou sem prêmio real de entrada |
| `armada` | `executada_simulada` | vencimento não chegou E `premio` é um número positivo |
| `executada_simulada` | `monitorada` | remarcação diária com spot real do ativo-objeto |
| `executada_simulada` | `fechada` | vencimento chegou, com spot de liquidação real |
| `monitorada` | `monitorada` | remarcação diária (mesma fase, não é transição de fato) |
| `monitorada` | `fechada` | vencimento chegou, com spot de liquidação real |
| `expirada_sem_uso` | — | terminal, nenhum destino declarado |
| `fechada` | — | terminal, nenhum destino declarado |

A regra de que toda sugestão `armada` com prêmio real EXECUTA — sem nenhum
filtro adicional de qualidade — é deliberada (A-11-03 do `11-01-PLAN.md`):
a razão é medição. Este milestone quer a amostra máxima de sugestões
executadas antes de decidir se algum filtro de qualidade vale a pena; impor
um filtro agora seria inventar uma regra de produto sem origem em nenhum
artefato do ROADMAP, e reduziria artificialmente o tamanho da amostra que a
Fase 11 existe para gerar.

`pnl_por_acao` é **por ação**, nunca multiplicado por lote — porque
`put_suggestions` não tem (nem ganha) coluna de quantidade. Essa ausência
não é um descuido: é uma das garantias estruturais de long-only do ADR-021,
Decisão 2, preservada intacta por esta fase — a tabela continua sem onde
gravar margem, lado ou tamanho de posição.

## Decisão 3 — o monitoramento roda no gate diário do laço existente, não dentro da segunda passada por usuário

`put_lifecycle.maybe_run` é chamado a partir de `server/app/agent.py`, no
`scheduler_loop`, num nível de indentação irmão do `if radar_fetch...` (D-
EXEC-11-02-01) — **fora** de qualquer gate de pregão/kill-switch, e fora da
segunda passada por usuário (`_avaliar_opcoes`) que avalia posição de opção
real. Três razões (A-11-06 do `11-02-PLAN.md`):

1. **Pendurar dentro de `_avaliar_opcoes` seria inerte** — a evidência (b) da
   Decisão 1: sem uma posição real de opção, essa passada nunca roda para o
   usuário, e a sugestão nunca é carteira real.
2. **Acoplar ao kill-switch distorceria a medição.** O kill-switch existe
   para parar EXECUÇÃO de ordem real; o ciclo de vida da sugestão é medição
   interna, nunca ordem. O precedente do incidente de kill-switch ligado por
   2,5 dias (`.planning/notes/incidente-kill-switch.md`) mostra o custo de
   deixar QUALQUER coisa —- inclusive medição sem risco — refém do mesmo
   portão que trava execução real.
3. **Código novo não pertence ao caminho mais crítico do agente** (o que
   decide comprar/vender de verdade). Isolar o hook do ciclo de vida do
   caminho de execução real reduz a superfície de uma falha ali derrubar
   algo que importa.

A parte vinculante do critério do ROADMAP — "nenhum scheduler novo, nenhum
cron externo" — é cumprida literalmente: `put_lifecycle.maybe_run` é só mais
uma chamada dentro do `scheduler_loop` que já existe, com gate diário PRÓPRIO
(`should_run`: dia útil + horário + 1x/dia via marcador kv), no mesmo molde
estrutural de `put_bridge.maybe_run`/`signal_ledger_job.maybe_run`.

## Decisão 4 — custo de rede zero e o que acontece quando falta preço

`run_diario` só lê preço via `candle_cache.peek(ticker, "1d")` — o cache que
o Radar diário já pagou, nunca uma chamada de rede nova. Consequência
aceita: um ticker fora do universo que o Radar já varre fica sem candle no
cache, e a linha nunca acha `spotAtual`/`spotLiquidacao` — `decidir()` nunca
inventa um valor (princípio 4 do CLAUDE.md do repositório); o chamador grava
`pendente_desde` e tenta de novo no próximo dia útil, sem exceção, sem
travar as demais linhas (isolamento por linha, `try/except` dentro do laço
de `run_diario`).

Com `B3_OPTIONS_PROVIDER=yahoo` (default de produção, **não alterado** por
este milestone), a ponte da Fase 10 segue dormente (ADR-021, Decisão 3) —
sem `exerciseStyle` real do Yahoo, `put_bridge` nunca grava uma linha
`armada` com proveniência completa, `put_suggestions` fica vazia, e
`run_diario` sempre devolve `{"linhas": 0, ...}`. **O ciclo de vida nasce
sem nenhuma linha para varrer em produção — por desenho, não por defeito**,
exatamente como o ADR-021 documentou para a ponte que o alimenta. Todo
requisito desta fase (PUTLIFE-01 a PUTLIFE-04) é provado por teste
automatizado (`server/tests/test_put_lifecycle_sem_carteira.py` e os
guardiões dos Planos 01/02), não por dado de produção, até o dia em que o
seletor `B3_OPTIONS_PROVIDER` apontar para `mydata`.

## Consequências

**Fica mais fácil:**
- Adicionar um novo motivo de fechamento (`MOTIVOS_FECHAMENTO` já reserva
  `stop`/`alvo`/`manual`, vocabulário do ADR-005) sem tocar em nenhuma linha
  de código do motor de carteira real.
- Auditar "nenhuma posição real foi criada por esta fase" com um único teste
  de comportamento (`test_put_lifecycle_sem_carteira.py`), em vez de revisão
  de código contínua a cada PR futuro que toque `put_lifecycle.py`.
- Ligar a medição em produção no dia em que `B3_OPTIONS_PROVIDER=mydata` for
  aprovado — nenhum código muda, a ponte e o ciclo de vida já estão prontos
  ponta a ponta.

**Fica mais difícil:**
- Simular efeito de patrimônio/PnL agregado da put de proteção junto do
  resto da carteira — o `pnl_por_acao` da sugestão vive só em
  `put_suggestions`, nunca soma ao patrimônio real exibido ao usuário
  (decisão deliberada, ver Decisão 1).
- Medir o efeito real do ciclo de vida em produção enquanto a ponte
  permanecer dormente (Decisão 4) — sem sugestões `armada` chegando, não há
  amostra para calibrar nada.

**A revisitar:**
- (a) O item (a) do ADR-021 ("alargar o lado do gatilho quando a Fase 11
  tiver dado real para calibrar o que vale a pena sugerir") agora tem
  instrumento — a máquina de decisão e o histórico de estados existem — mas
  ainda não tem dado, porque a ponte que alimenta `put_suggestions` segue
  dormente com `B3_OPTIONS_PROVIDER=yahoo`.
- (b) Expor a medição (relatório, consulta no portal admin, ou qualquer
  superfície) é decisão do Alex, fora do roadmap de v1.2 — mesma nota que o
  ADR-021 já registrou para a ponte (item (c) das suas "A revisitar").
- (c) WR-01 (o gate de orçamento `mydata_budget.pode_gastar()`/`.debita()`
  não é atômico, check-then-debit) segue pendente de decisão do Alex —
  repetido aqui por visibilidade, sem ser resolvido nesta fase.
  `put_lifecycle.run_diario` não abre um consumidor novo desse gate (só lê
  `candle_cache.peek`, sem chamar `options_provider`/`mydata_budget`), então
  o risco residual documentado no ADR-021 Decisão 4 não cresce com esta
  fase.
