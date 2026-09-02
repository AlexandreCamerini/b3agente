# Phase 14: Opções lastreadas — venda coberta e put de proteção — Context

**Gathered:** 2026-08-30
**Status:** Ready for planning
**Source:** `/gsd-explore` (exploração Socrática sobre funcionalidades de opções, incluindo UI/UX) — decisões completas em `.planning/notes/opcoes-mecanica-lastreada-decisoes.md`

<domain>
## Phase Boundary

Redesenhar a mecânica de opções do Boris+ do zero para só permitir duas
operações, ambas **lastreadas por posição real de ação já existente na
carteira do usuário**: venda de CALL coberta e compra de PUT de proteção.
Nenhuma perna especulativa/descoberta desvinculada de uma posição real.
Setups e propostas de operação vêm da análise técnica do próprio
ativo-lastro (motor determinístico já existente), não de varredura livre
de qualquer ticker líquido.

Fora do escopo: qualquer estrutura de opção que não seja essas duas
(travas, straddles, etc.), simulação de exercício/atribuição, e mudança de
fonte de dados de mercado (nenhuma ADR de dado é reaberta).

</domain>

<decisions>
## Implementation Decisions

### Escopo da mecânica
- Só CALL coberta (venda) e PUT de proteção (compra), ambas exigindo
  posição real do ativo-lastro na carteira no momento da abertura.
- O motor escolhe o contrato com base na análise técnica do ativo-lastro
  (mesmo motor determinístico que já gera setups/decisão de ação).

### Redesenho, não reaproveitamento
- **Não aproveitar** `put_bridge.py`/`put_lifecycle.py`/`put_suggestions`
  (ADR-021/022) como base — aquilo é uma simulação-sombra deliberada
  (nunca vira posição real, nunca aparece pro usuário, sem campo de
  quantidade). A decisão de mantê-la sombra não é herdada aqui.
- **Não aproveitar** `setOptionStop`/`setOptionAlvo` existentes
  (`App.jsx:7512-13` + backend `set_option_position`) como estão — são
  código morto hoje (nenhuma UI os invoca). O redesenho os substitui pelo
  fluxo novo, não os "conserta" isoladamente.
- `store.py buy_option/sell_option` (long-only, sem lastro, "vender pra
  fechar" apenas) precisa de mecânica nova: "vender pra abrir" (lançar
  CALL coberta) não existe hoje — é greenfield.

### Atribuição/exercício
- **Nunca simular atribuição.** CALL coberta vencendo ITM nunca resulta em
  venda das ações-lastro pelo strike. Produto assume que o usuário sempre
  fecha (recompra) a call antes do vencimento.
- Se o usuário não fechar manualmente e a call vencer ITM: precisa de uma
  regra determinística de liquidação em dinheiro equivalente ao valor
  intrínseco, sem tocar a posição de ações. **Fórmula exata fica a
  critério do planejamento** (Claude's Discretion) — não foi especificada
  na exploração.
- CALL coberta OTM no vencimento: expira sem valor, prêmio integral fica
  com quem vendeu, posição fecha normalmente.

### Trava de lastro
- Enquanto a CALL coberta estiver aberta, o lote de ações que a lastreia
  fica **bloqueado para venda** na tela de Carteira — não pode ser vendido
  livremente enquanto a call não for fechada.
- Implica campo novo de quantidade travada/reservada na posição de ação,
  distinto da quantidade livre. Mexe em `store.py`, `web/src/finance.js`, e
  precisa entrar nos DOIS stores do front (`deviceStore`/`serverStore`,
  paridade obrigatória — guardrail do repo).

### UX
- Formato: **proposta pronta + cadeia expansível**, os dois convivem. O
  motor escolhe 1 contrato com base no técnico + lastro disponível e
  propõe pronto ("vender N calls strike Y por Z prêmio"), no mesmo estilo
  de linguagem de decisão que o card de ação já usa (manchete única,
  guardrail CVM: manchete só do motor determinístico). A cadeia completa
  continua disponível, expansível, pra quem quiser escolher manualmente
  outro strike/vencimento — não substitui `OpcoesCamada`, evolui ela.

### Modo
- **Estudo:** explica a proposta como conteúdo didático (ex.: "se você
  tivesse vendido esta call coberta..."), sem CTA de executar.
- **Operador:** mesma proposta ganha os CTAs reais (vender CALL / comprar
  PUT), execução simulada de verdade.

### Patrimônio
- Posições de opção lastreada **entram** no Patrimônio Total e P&L
  agregado da Carteira (`portfolioMetrics()` em `web/src/finance.js`).
  Hoje `optionPositions` é excluído desse cálculo — isso muda para a
  mecânica nova (aplica-se às posições lastreadas desta fase; decisão não
  necessariamente retroativa a outras posições de opção pré-existentes,
  ver Claude's Discretion).

### Fonte de dados — SEM MUDANÇA DE ADR
- mydata confirmado como única fonte de opções B3 (ADR-004/ADR-020
  intactos, não reabertos).
- Ação diário/spot continua brapi master (ADR-008 intacto).
- Intraday continua Yahoo primário (ADR-001 intacto) — cogitado inverter
  para brapi primário durante a exploração, revertido explicitamente
  porque exigiria brapi Pro paga (R$116,66/mês) contra o orçamento US$0
  travado no ADR-001. Nenhuma mudança de fonte de dados faz parte desta
  fase.

### Timing / dormência
- Fase entra no roadmap agora (Fase 14, standalone, sem milestone ativo),
  construída estruturalmente pronta e testável contra payload
  mock/degradado.
- Execução real só libera quando a virada de produção
  `B3_OPTIONS_PROVIDER=mydata` acontecer — bloqueada hoje por dois motivos
  medidos (não achismo, ver ADR-020 §Medição): pico de requisições/min
  projetado (148 vs. teto 60/min, mitigação de espaçamento já feita em
  código 2026-08-28, falta confirmar perna ao vivo) e WR-01 (race
  condition em `mydata_budget`, decisão de arquitetura pendente — ver
  `.planning/todos/pending/decidir-wr01-mydata-budget.md`).
- Enquanto a cadeia real não responde, toda a fase deve ser testável contra
  payload mock/degradado — não há ambiente real pra validar contra até a
  virada acontecer.

### Claude's Discretion
- Fórmula exata de liquidação forçada de CALL coberta ITM não fechada
  manualmente no vencimento (valor intrínseco, quem paga o quê).
- Se a trava de lastro (D-3) e a inclusão no Patrimônio Total (D-6) se
  aplicam retroativamente a posições de opção pré-existentes (não
  lastreadas, do modelo antigo) ou só às novas posições lastreadas desta
  fase — nenhuma migração de dado foi discutida na exploração.
- Nome/rótulo exato da nova operação na UI (ex.: "venda coberta" vs. outro
  termo em PT-BR consistente com o vocabulário do produto).
- Detalhe de como o gate de liquidez (`opGate.liquida`) e o payload
  mock/degradado de teste vão simular a fase antes da virada de produção.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contexto de opções e fonte de dados
- `docs/adr/004-fonte-de-opcoes-na-v2.md` — contrato `providerStatus`, bloqueio de compra em `degraded` (NÃO reabrir)
- `docs/adr/020-centralizacao-de-dados-no-mydata.md` — mydata único provedor de opções, medição de cota/pico, status das ADRs anteriores
- `docs/adr/021-ponte-gatilho-put.md` e `docs/adr/022-ciclo-de-vida-da-sugestao-de-put.md` — mecanismo de sombra que esta fase NÃO reaproveita (ler para entender o que evitar repetir)
- `docs/adr/001-*.md` (intraday Yahoo) e `docs/adr/008-*.md` (brapi master diário/spot) — intactos, não mexer

### Código existente relevante
- `server/app/store.py` — `buy_option`/`sell_option`/`set_option_position` (motor atual, long-only, sem lastro)
- `server/app/options_api.py`, `server/app/options_provider.py`, `server/app/options_provider_mydata.py` — camada de dados de opções
- `web/src/App.jsx` — `OpcoesCamada` (componente atual da camada de opções no card), `myOptionPositions`, `setOptionStop`/`setOptionAlvo` (código morto a substituir)
- `web/src/finance.js` — `portfolioMetrics()` (exclui `optionPositions` hoje — muda nesta fase)
- `web/src/persistence.js` — `deviceStore`/`serverStore` (paridade obrigatória para qualquer método/campo novo)

### Nota da exploração
- `.planning/notes/opcoes-mecanica-lastreada-decisoes.md` — decisões completas com o porquê, produzidas em `/gsd-explore`

</canonical_refs>

<specifics>
## Specific Ideas

- Linguagem de decisão da proposta deve seguir o mesmo padrão do card de
  ação (Hero reconciliado v11: manchete única do motor determinístico +
  análise em chips) — não inventar um padrão visual novo.
- `docs/OPERACAO-ciclo-de-vida-put.md` e `docs/OPERACAO-ponte-gatilho-put.md`
  documentam o funcionamento operacional do mecanismo de sombra — útil como
  referência de "o que evitar", não como base a estender.

</specifics>

<deferred>
## Deferred Ideas

- Proventos via mydata (escopo `provento_b3` já liberado na chave de
  produção, nenhum consumidor no código) — mencionado na exploração, fora
  do escopo desta fase.
- Resolução definitiva do WR-01 (race condition em `mydata_budget`) — é
  pré-requisito da virada de produção, mas a decisão de arquitetura em si
  (lock/fila/aceitar risco) é tratada em todo separado, não nesta fase.

</deferred>

---

*Phase: 14-opcoes-lastreadas*
*Context gathered: 2026-08-30 via /gsd-explore (equivalente a discuss-phase)*
