# Requirements: Boris+ (b3-agente) — Milestone v1.2

**Defined:** 2026-08-28
**Core Value:** O usuário leigo sai do Modo Estudo entendendo de verdade como
o mercado funciona — e só então tem acesso a automações do Modo Operador.

## v1.2 Requirements

Requisitos deste milestone. Toda a camada é backend-only e invisível ao
usuário — o critério de aceite é medição interna, não UI.

### Precondições (Fase 0)

- [x] **LEDGER-01**: Os 9 tickers com 404 no bootstrap do ledger de sinais
  (ELET3, BRFS3, ELET6, JBSS3, CRFB3, NTCO3, CPLE6, MRFG3, EMBR3) são
  investigados (renomeação/deslistagem) e o ledger fecha sem erro 404
  residual — necessário porque a ponderação do ADR-017 é calculada sobre
  o ledger completo
- [x] **OPTGATE-01**: `options_provider_mydata.py`/`options_provider.py`
  respeitam um teto de taxa de requisições ao mydata, espelhando o padrão
  `_gate`/`_debita` que `candle_provider.py` já tem (fecha o achado WR-01
  do 09-REVIEW.md antes de qualquer estrutura de opções nova consumir a
  mesma chave)

### Ponte gatilho→put (Fase 10)

- [x] **PUT-01**: Quando um detector de setup dispara sobre um ticker
  presente em `positions` do usuário, o sistema seleciona automaticamente
  uma série de put candidata para proteção, usando `estilo_exercicio`,
  strike e IV reais devolvidos pelo hub mydata — nunca assumidos
  localmente
- [x] **PUT-02**: A sugestão de put selecionada é gravada no ledger de
  sinais com proveniência (fonte, `as_of`, e `sha256`/`dt_captura` quando
  disponíveis na resposta do hub)
- [x] **PUT-03**: Nenhuma superfície da sugestão de put fica visível ao
  usuário nesta fase — puramente backend/ledger, sem UI, sem push, sem
  card novo

### Ciclo de vida e monitoramento (Fase 11)

- [ ] **PUTLIFE-01**: Toda sugestão de put armada tem um estado rastreável
  ao longo do tempo: `armada` → `expirada sem uso` | `executada
  (simulada)` → `monitorada` → `fechada`
- [ ] **PUTLIFE-02**: A execução simulada de uma put reusa `optionPositions`
  e os contratos inteiros de ADR-003/004/005 — sem reimplementar preço
  médio, PnL ou proveniência de posição de opção
- [ ] **PUTLIFE-03**: O fechamento por expiração reusa o mecanismo já
  resolvido pelo ADR-005 — sem lógica de expiração paralela
- [ ] **PUTLIFE-04**: O ciclo de monitoramento diário de puts de proteção
  roda dentro da segunda passada já existente do `agent.py` para
  `optionPositions` — nenhum scheduler novo

## v2 Requirements (deferred)

Explicitamente fora do roadmap deste milestone, mas candidatos futuros
depois que as pré-condições listadas abaixo forem resolvidas.

### Exposição ao usuário

- **PUTUI-01**: Exibir a sugestão de put de proteção na UI do card do
  ativo (Modo Operador) — depende de: medição deste milestone confirmar
  qualidade/utilidade da sugestão antes de expor

## Out of Scope

Explicitamente excluído deste milestone. Documentado para prevenir scope
creep.

| Feature | Razão |
|---------|-------|
| DSL / criação de setup por linguagem natural | ADR-017 pondera setup por desempenho histórico medido; um setup recém-criado não tem histórico — exige resolver antes "como um setup novo ganha o direito de entrar no Radar" |
| Estruturas que lançam opção (call coberta, travas, spreads) | Exigem modelo de posição vendida, margem e atribuição; decisão já registrada de que essa mecânica precisa de um agente judge com poder de veto antes de publicar — não construído |
| Monitoramento intradiário de opção | Consequência direta da decisão de arquitetura "EOD de ponta a ponta" (não reaberta neste milestone) |
| Posição vendida/short em qualquer forma | Fora de escopo de produto (PROJECT.md), reafirmado como PROIBIDO no contrato deste milestone |
| Virar `B3_OPTIONS_PROVIDER` / mexer na virada de produção da Fase 9 | Fora de escopo — pertence ao checkpoint `adiar` da Fase 9, não a este milestone |

## Traceability

Preenchido pelo roadmapper na criação do roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| LEDGER-01 | Phase 0 | Complete |
| OPTGATE-01 | Phase 0 | Complete |
| PUT-01 | Phase 10 | Complete |
| PUT-02 | Phase 10 | Complete |
| PUT-03 | Phase 10 | Complete |
| PUTLIFE-01 | Phase 11 | Pending |
| PUTLIFE-02 | Phase 11 | Pending |
| PUTLIFE-03 | Phase 11 | Pending |
| PUTLIFE-04 | Phase 11 | Pending |
