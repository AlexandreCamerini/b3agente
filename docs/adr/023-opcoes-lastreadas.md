# ADR-023: Opções lastreadas — venda coberta e put de proteção sobre posição real

**Status:** Aceito
**Data:** 2026-08-31
**Decisor:** Alex (via `/gsd-explore`, decisões registradas em
`.planning/notes/opcoes-mecanica-lastreada-decisoes.md`)
**Base:** ROADMAP Fase 14 (standalone, sem milestone ativo); `14-CONTEXT.md`;
ADR-003/004/005 (motor de opções long-only pré-existente); ADR-020/ADR-021/
ADR-022 (dados de opções e o mecanismo de sombra que esta fase substitui).

---

## Contexto

O motor de opções do Boris+ era, até esta fase, exclusivamente long-only e
desvinculado da carteira de ações (`store.py buy_option`/`sell_option`,
componente `OpcoesCamada` em `App.jsx`): comprar CALL ou PUT a seco, sem
nenhum lastro. `sell_option` só sabe "vender pra fechar" — não existe
"vender pra abrir" (lançar/escrever uma opção), então venda coberta não
tinha nenhuma fundação no código antes desta fase. Em paralelo, um
mecanismo de sombra completamente diferente já existia (`put_bridge.py`/
`put_lifecycle.py`, ADR-021/ADR-022): uma sugestão de put vinculada a um
gatilho técnico, mas deliberadamente incapaz de virar posição real
(sem campo de quantidade, nunca aparece pro usuário).

A exploração `/gsd-explore` de 2026-08-30 fechou um pivô de escopo: em vez
de "compra especulativa de qualquer contrato líquido", a mecânica nova
restringe-se a duas operações, **ambas lastreadas por uma posição real do
ativo-objeto já na carteira do usuário**: venda de CALL coberta (gera
prêmio, trava o upside) e compra de PUT de proteção (paga prêmio, protege o
downside). O motor de sugestão de put existente e `setOptionStop`/
`setOptionAlvo` (código morto, sem UI que os invoque) não foram reaproveitados
como base — este é um redesenho do zero (D-1 da exploração).

## Decisão 1 — escopo restrito a duas operações lastreadas, sem exercício/atribuição simulados

Só existem duas operações novas, ambas exigindo posição real do ativo-lastro
no momento da abertura: venda de CALL coberta (`store.abrir_call_coberta`) e
compra de PUT de proteção (`store.comprar_put_protecao`). Nenhuma perna
especulativa desvinculada de uma posição existente. Nenhuma estrutura fora
dessas duas (travas, straddles etc.) faz parte do escopo.

O motor **nunca simula exercício/atribuição**: uma CALL coberta que vence
ITM sem ter sido recomprada manualmente não resulta, em nenhuma hipótese, em
venda das ações-lastro pelo strike. O produto assume que o usuário sempre
fecha (recompra) a call antes do vencimento — esse é o caminho normal. A
liquidação forçada abaixo é a exceção que cobre quem não fecha a tempo.

## Decisão 2 — fórmula de liquidação forçada no vencimento (D-2 da exploração, especificada no Plano 14-04)

Quando uma CALL coberta lastreada chega ao vencimento sem ter sido fechada à
mão, `store.liquidar_lastreada_vencida` roda uma **recompra sintética ao
valor intrínseco** — nunca uma venda das ações-lastro pelo strike:

- `intrinseco = max(0.0, spot_no_vencimento − strike)` — a MESMA aritmética
  que `agent.intrinseco_opcao` já usa para call; `store.py` não pode
  importar `agent.py` (dependência corre no sentido inverso), então a
  fórmula é copiada verbatim, com os dois lados travados por teste
  (`test_agent_options.py` + `test_opcoes_lastreadas_vencimento.py`) para
  nunca divergir.
- Débito de caixa: `cash -= qty × intrinseco` (o vendedor da call paga a
  diferença entre o preço de mercado no vencimento e o strike, exatamente
  como uma recompra real custaria).
- Resultado realizado: `pnl = round((avg − intrinseco) × qty, 2)` — o MESMO
  caminho de código nos dois desfechos possíveis, sem ramo especial: fora do
  dinheiro (`intrinseco = 0.0`), débito zero e `pnl == avg × qty` (o prêmio
  integral fica com quem vendeu); dentro do dinheiro, o débito reduz o
  ganho na proporção exata do quanto a call terminou ITM.
- **As ações do lastro nunca são tocadas** — nenhuma venda pelo strike,
  nenhuma entrega. Só a trava é destravada: `qtyTravada` da posição de ações
  volta a cair na quantidade liquidada (piso 0), com a posição de AÇÕES em
  si intocada em qualquer dos dois desfechos.
- A PUT de proteção comprada, quando vence, despacha para o caminho legado
  já existente (`close_option_vencida`) com `intrinseco = max(0.0, strike −
  spot)` — pode ser zero (perda total do prêmio, o resultado comum, não uma
  exceção). Nada a destravar: a PUT nunca prendeu lastro nenhum (só a CALL
  trava, ver Decisão 3).
- Histórico grava `motivo="vencimento"`, `origem="sistema"` — expiração é
  liquidação mecânica obrigatória, roda igual com o Operador ligado ou
  desligado, não é uma decisão do agente (mesma regra já valia para
  `close_option_vencida`, ADR-012/Fase 3).

## Decisão 3 — trava de lastro: campo novo, fonte única de leitura

Enquanto a CALL coberta está aberta, o lote de ações que a lastreia fica
bloqueado para venda livre. Implementado como campo novo na posição de ação,
`positions[].qtyTravada` (inteiro, ausente = `0` via `.get`, sem migração de
dado nenhuma — ver Decisão 5). `store.qty_livre(pos)` é a **ÚNICA** fonte da
aritmética `qty − qtyTravada` no backend — proibido recalcular essa
subtração em qualquer outro módulo (mesma disciplina de `caixa_reservado`).
No front, o mesmo dado precisa existir espelhado nos dois stores
(`deviceStore`/`serverStore`, `web/src/persistence.js` — paridade
obrigatória, guardrail do repositório) e a mesma fonte única é importada de
`web/src/finance.js`, nunca recalculada dentro de um componente.

A PUT de proteção **não trava ações** — protege, não reserva lastro para
entrega. O estado "sem lastro suficiente para propor uma operação nova"
(`motivo: "sem_lastro"` na rota `GET /api/options/proposta/{ticker}`) é
sempre **DERIVADO** na leitura (`store.qty_livre(posicao) < 100`), nunca
persistido como flag — o mesmo padrão já usado por `caixa_reservado`.

## Decisão 4 — Patrimônio Total passa a incluir as pernas lastreadas

Diferente do comportamento anterior a esta fase (`portfolioMetrics()` em
`finance.js` excluía `optionPositions` do Patrimônio Total/P&L agregado da
Carteira), a mecânica lastreada **entra** no cálculo: prêmio e P&L da
operação de opção passam a compor o total, com a ressalva de marcação pelo
prêmio de abertura sempre exibida (nunca omitida) na Carteira. Esta decisão
é filtrada por `lastro` presente — ver Decisão 5.

## Decisão 5 — NÃO-retroatividade: nenhuma migração de dado

A trava de lastro (Decisão 3) e a entrada no Patrimônio Total (Decisão 4)
valem **só** para posições de opção abertas por esta mecânica nova — nunca
para posições pré-existentes do modelo antigo (`buy_option`/`sell_option`,
long-only, sem lastro). Dois discriminadores no schema tornam essa
distinção estrutural, sem precisar de uma coluna de "versão" ou de qualquer
job de backfill:

- `optionPositions[].side` (`"vendida"` para CALL coberta, `"comprada"`
  para PUT de proteção lastreada) — chave **ausente** identifica uma posição
  do modelo antigo.
- `optionPositions[].lastro` (`{"t": <ticker>, "qty": <ações travadas ou
  protegidas>}`) — presença é o que define "posição desta fase";
  `liquidar_lastreada_vencida` recusa (`ValueError`) qualquer posição sem
  essa chave, e o caminho de vencimento legado (`close_option_vencida`,
  chamado direto pelo agente) continua servindo exatamente essas posições
  antigas.

Nenhuma posição existente foi reescrita, nenhum campo foi retroativamente
preenchido. Um usuário com uma posição de opção comprada antes desta fase
não ganha trava nenhuma nem entra no Patrimônio agregado por essa posição —
continua sob as regras antigas, sem alteração de comportamento.

## Decisão 6 — provedor `mock`: só desenvolvimento, default de produção inalterado

`B3_OPTIONS_PROVIDER` ganha um terceiro valor, `"mock"` (além de
`"yahoo"`/`"mydata"`), servido por `options_provider_mock.py` — determinístico
por desenho (sem I/O de rede, sem cache, sem relógio interno; a mesma
entrada sempre devolve o mesmo payload byte a byte), com um segundo
interruptor, `B3_OPTIONS_MOCK_STATUS=degraded`, que simula cadeia
indisponível sem precisar derrubar nenhum serviço externo de verdade. Existe
exclusivamente para tornar a fase inteira testável ponta a ponta sem
depender da cadeia real da B3 responder — nunca é escolha do cliente, só
variável de ambiente do servidor. **O default de produção continua
`"yahoo"`**, inalterado por esta fase (mesmo valor que `options_provider.py`
já usava antes do Plano 14-01).

## Decisão 7 — dormência: sem flag nova, o gate de liquidez já existente é o interruptor

A fase inteira nasce **dormente em produção**, pelo mesmo padrão que
ADR-021 já documentou para a ponte gatilho→put: nenhuma flag de feature
nova controla se a mecânica "está ligada" — o comportamento é inteiramente
uma função de qual provedor de opções está ativo. Com `B3_OPTIONS_PROVIDER=
yahoo` (produção, hoje), `GET /api/options/gate/{ticker}` devolve
`liquida: false` e `GET /api/options/proposta/{ticker}` devolve
`{"proposta": null, "motivo": "degradado"}` para qualquer ticker — nenhuma
superfície nova aparece na tela, nenhuma proposta é oferecida, nenhum botão
de operação lastreada fica habilitado. A fase desperta, sem nenhum deploy de
código, no dia em que `B3_OPTIONS_PROVIDER=mydata` virar produção (bloqueado
hoje pelos dois motivos medidos e registrados em ADR-020 §Medição: pico de
requisições/minuto acima do teto da chave, e WR-01 — race condition
check-then-debit em `mydata_budget`, decisão de arquitetura pendente do
Alex, `.planning/todos/pending/decidir-wr01-mydata-budget.md`).

## O que NÃO foi reaberto

Esta fase não reabre nenhuma das seguintes decisões — elas permanecem
exatamente como documentado nos ADRs originais:

- **ADR-001** (fonte de dados intraday) — Yahoo continua primário do
  intraday; nenhuma mudança de fonte.
- **ADR-004** (fonte de opções na v2) — o contrato `providerStatus` e o
  bloqueio de execução em `degraded` continuam valendo, sem alteração.
- **ADR-008** (fonte de cotações selecionável) — brapi continua master de
  diário/spot.
- **ADR-020** (centralização de dados no mydata) — mydata segue como única
  fonte confirmada de opções B3; a virada de produção continua bloqueada
  pelos mesmos dois motivos medidos, não resolvidos por esta fase.
- **ADR-021** (ponte gatilho→put) e **ADR-022** (ciclo de vida da sugestão
  de put) — o mecanismo de sombra que os dois documentam (`put_bridge.py`/
  `put_lifecycle.py`, tabela `put_suggestions`) não é a base desta fase; os
  dois ADRs continuam descrevendo exatamente o comportamento do código deles,
  sem nenhuma mudança.

## Consequências

**Fica mais fácil:**
- Auditar "nenhuma operação lastreada aparece sem a cadeia real responder"
  com um único par de leituras (`gate`/`proposta` contra o provedor
  default), sem precisar de uma flag de feature separada para desligar.
- Ligar a mecânica em produção no dia da virada do mydata — nenhum código
  muda, só o valor de `B3_OPTIONS_PROVIDER`.
- Testar a fase inteira localmente contra o provedor `mock`, incluindo o
  caminho degradado, sem depender de rede nem de credencial de nenhum
  provedor real.

**Fica mais difícil:**
- Um usuário com posição de opção antiga (pré-fase) não ganha trava nem
  entra no Patrimônio agregado por essa posição — se o produto decidir
  estender essas garantias retroativamente no futuro, isso exigirá uma
  migração de dado que esta fase deliberadamente não fez.
- Medir o efeito real da mecânica em produção enquanto a fase permanecer
  dormente — sem cadeia real respondendo, não há amostra para calibrar a
  qualidade das propostas até a virada do mydata acontecer.

**A revisitar:**
- Quando `B3_OPTIONS_PROVIDER=mydata` virar produção, confirmar que o gate
  de liquidez (`options_api.liquidity_gate`) e a proposta se comportam da
  mesma forma testada aqui contra o payload determinístico do `mock`.
- Decisão de retroatividade (Decisão 5) pode ser revisitada se o produto
  quiser estender trava/Patrimônio a posições de opção antigas — hoje é uma
  decisão explícita de não fazer, não um esquecimento.
