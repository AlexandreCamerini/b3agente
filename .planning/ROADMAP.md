# Roadmap: Boris+ (b3-agente)

## Milestones

- ✅ **v1.0 Revisão Geral** — Phase 1 (shipped 2026-08-18) — [detalhes](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Realismo de Mercado + Correções** — Phases 2-8 (shipped 2026-08-23) — [detalhes](milestones/v1.1-ROADMAP.md)
- 🚧 **v1.2 Camada de opções ancorada na carteira** — Phases 0, 10, 11 (in progress)

## Phases

<details>
<summary>✅ v1.0 Revisão Geral (Phase 1) — SHIPPED 2026-08-18</summary>

- [x] Phase 1: Auditoria Diagnóstica Consolidada (6/6 plans) — completed 2026-08-18

</details>

<details>
<summary>✅ v1.1 Realismo de Mercado + Correções (Phases 2-8) — SHIPPED 2026-08-23</summary>

- [x] Phase 2: Realismo de Mercado (7/7 plans) — completed 2026-08-19
- [x] Phase 3: Correção Crítico + Alto (6/6 plans) — completed 2026-08-19
- [x] Phase 4: Correção Médio — Storyline & UX (7/7 plans) — completed 2026-08-22
- [x] Phase 5: Correção Médio — Código, Gate & Admin (8/8 plans) — completed 2026-08-23
- [x] Phase 6: Instrumentação de Assertividade (ADR-015) (5/5 plans) — completed 2026-08-21
- [x] Phase 7: Seleção Dinâmica por Desempenho Histórico (ADR-017 Bloco 1) (6/6 plans) — completed 2026-08-21
- [x] Phase 8: Interface e IA da Seleção Dinâmica (ADR-017 Bloco 3/4) (5/5 plans) — completed 2026-08-21

Full phase details: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)

</details>

## Progress

| Phase | Milestone | Status | Completed |
|-------|-----------|--------|-----------|
| 1. Auditoria Diagnóstica Consolidada | v1.0 | Complete | 2026-08-18 |
| 2. Realismo de Mercado | v1.1 | Complete | 2026-08-19 |
| 3. Correção Crítico + Alto | v1.1 | Complete | 2026-08-19 |
| 4. Correção Médio — Storyline & UX | v1.1 | Complete | 2026-08-22 |
| 5. Correção Médio — Código, Gate & Admin | v1.1 | Complete | 2026-08-23 |
| 6. Instrumentação de Assertividade (ADR-015) | v1.1 | Complete | 2026-08-21 |
| 7. Seleção Dinâmica por Desempenho Histórico (ADR-017 Bloco 1) | v1.1 | Complete | 2026-08-21 |
| 8. Interface e IA da Seleção Dinâmica (ADR-017 Bloco 3/4) | v1.1 | Complete | 2026-08-21 |
| 0. Precondições | 2/2 | Complete   | 2026-08-28 |
| 10. Ponte gatilho→put | 1/3 | In Progress|  |
| 11. Ciclo de vida e monitoramento | v1.2 | Not started | - |

### Phase 9: Centralização de dados de mercado (mydata_client.py)

**Goal:** Implementar `mydata_client.py` consumindo `GET /v1/cotacoes/{ticker}` e `GET /v1/opcoes/{ticker}` do cvm-financas (`mydata.acamerini.app`). Migrar COTAHIST diário (aposenta `b3_historical.py`/ADR-019) e Opções/IV (substitui `options_provider_yahoo.py`, mantém ADR-004 sem reabrir via `providerStatus`). Redefinir brapi como fonte exclusiva de cotação spot ao vivo (ADR-008 com escopo reduzido). Yahoo intraday 15min fica intocado (ADR-001 sem mudança). Critério de aceite obrigatório: medir rate-limit real (60/min·2.000/dia) contra padrão de uso antes de desligar Yahoo/brapi nas fatias migradas — ver [.planning/todos/pending/medir-rate-limit-mydata.md](todos/pending/medir-rate-limit-mydata.md) e [.planning/notes/boris-pp-centralizacao-dados-mydata.md](notes/boris-pp-centralizacao-dados-mydata.md) para a decisão completa com evidência.
**Requirements**: TBD
**Depends on:** Phase 8
**Plans:** 6/6 plans complete

Plans:
**Wave 1**

- [x] 09-01-PLAN.md — mydata_client.py (auth X-API-Key, paginação por cursor, mapeamento COTAHIST→candle) + mydata_budget.py (60/min · 2.000/dia)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 09-02-PLAN.md — MydataProvider na fatia diária + fallback vira cadeia mydata→brapi→Yahoo com gate de fatia/cota por elo
- [x] 09-03-PLAN.md — options_provider_mydata (IV e gregas do hub) + seletor options_provider + troca dos 8 call sites

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 09-04-PLAN.md — medição obrigatória do rate-limit real contra 60/min · 2.000/dia, com veredito publicado

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 09-05-PLAN.md — aposentadoria da ingestão paralela de COTAHIST (checkpoint de decisão) + ADR-020

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 09-06-PLAN.md — rótulos de fonte no front + bump/publicar-web + checkpoint da virada de produção

---

### 🚧 v1.2 Camada de opções ancorada na carteira (In Progress)

**Milestone Goal:** quando um gatilho de setup dispara sobre um ticker que o
usuário já tem em carteira, o app arma uma sugestão de put de proteção sobre
essa posição, registra, monitora e mede — sem mostrar nada ao usuário neste
milestone (medição interna antes de expor qualquer superfície).

**Numeração de fase não-sequencial (deliberada, não renumerar):** Fase 0
(precondição midstream, não início cronológico), Fase 10 (continuação lógica
direta da Fase 9, standalone/já shippada fora deste milestone), Fase 11.
Fases 1-8 pertencem a v1.0/v1.1 e a própria Fase 9 já está documentada acima.

**Decisões de arquitetura travadas neste milestone (não reabrir):**
1. **EOD de ponta a ponta.** Gatilho fecha no fechamento do pregão, estrutura
   é proposta sobre o preço de fechamento, monitoramento é diário — nenhuma
   fase deste milestone lê ou depende de preço de opção ao vivo/intraday.
2. **Só put de proteção COMPRADA sobre posição existente.** `optionPositions`
   é long-only; short/margem/atribuição ficam explicitamente fora de escopo
   em qualquer fase — uma perna, comprada, sem margem, sem atribuição
   (exercício entrega uma ação que o usuário já possui).

- [x] **Phase 0: Precondições** - Fecha os 9 tickers 404 do bootstrap do ledger (ADR-017) e o gate de orçamento do provedor de opções mydata (achado WR-01 da Fase 9) (completed 2026-08-28)
- [ ] **Phase 10: Ponte gatilho→put** - Hook no `scheduler_loop` seleciona série de put candidata via hub mydata e grava a sugestão no ledger com proveniência — nada visível
- [ ] **Phase 11: Ciclo de vida e monitoramento** - Estados armada→expirada/executada→monitorada→fechada, reusando `optionPositions` e ADR-003/004/005 inteiros

### Phase 0: Precondições

**Goal**: O ledger de sinais fecha sem 404 residual e o provedor de opções
mydata respeita um teto de taxa de requisições — destravando a ponderação do
ADR-017 (calculada sobre o ledger completo) e fechando o achado WR-01 do
09-REVIEW.md antes de qualquer estrutura de opções nova consumir a mesma
chave mydata.
**Depends on**: Nothing (precondition gate — investiga um gap pré-existente
do bootstrap do ledger, aberto desde a Fase 7/v1.1, e fecha o achado WR-01 do
09-REVIEW.md; não é dependência técnica do código já shippado da Fase 9,
que está completo e mergeado)
**Requirements**: LEDGER-01, OPTGATE-01
**Success Criteria** (what must be TRUE):
  1. O bootstrap do ledger de sinais roda sobre os 74 tickers do universo
     sem nenhum erro 404 residual — os 9 tickers (ELET3, BRFS3, ELET6,
     JBSS3, CRFB3, NTCO3, CPLE6, MRFG3, EMBR3) resolvidos por correção de
     símbolo (renomeação) ou excluídos com razão documentada (deslistagem)
  2. `options_provider_mydata.py`/`options_provider.py` respeitam um teto de
     requisições ao mydata, aplicando o mesmo padrão `_gate`/`_debita` que
     `candle_provider.py` já usa — um burst de requisições de opções não
     estoura o orçamento compartilhado (60/min · 2.000/dia)
  3. Teste automatizado novo cobre o caminho de estouro de orçamento em
     `options_provider` (equivalente ao que `test_candle_provider.py` já
     cobre para candle)
  4. Suíte canônica (`bash scripts/executar.sh --testes`) verde após as
     duas mudanças
**Guardrails** (aplicam a esta fase e a todo o milestone v1.2):
  - Nenhum deploy, nenhum `git push` para origin, nenhuma mudança de env
    var de produção em qualquer ponto deste milestone
  - `B3_OPTIONS_PROVIDER` nunca é alterado — o gate de orçamento fechado
    aqui é pré-requisito de uma virada futura, não a virada em si (o
    checkpoint `adiar` da Fase 9 continua fora de escopo)
  - Nenhuma superfície visível ao usuário introduzida em nenhuma fase
  - Nenhum suporte a opção vendida/short introduzido em qualquer forma
**Plans**: 2 plans (1 wave — os dois rodam em paralelo, zero sobreposição de arquivo)
- [x] 00-01-PLAN.md — LEDGER-01: diagnóstico dos 9 tickers 404, mapa de resolução (`server/app/ledger_tickers.py`) consumido pelo bootstrap, varredura dos 74 tickers sem 404 residual
- [x] 00-02-PLAN.md — OPTGATE-01: gate `_gate`/`_debita` de `mydata_budget` em `options_provider_mydata.py`, com prova de bloqueio/degradação e de que o ciclo do agente não trava (fecha WR-01)
**Nota (não-bloqueante, não trava o milestone)**: os itens de backlog
pré-existentes que dependem do Alex ligar uma feature ao vivo num pregão
real (verificação do `entradaAuto` do checkpoint 08-05; os 2 human-checks da
Fase 3, ver `03-VERIFICATION.md`) permanecem bloqueados por dependência
humana e **não são resolvidos por esta fase** — seguem rastreados em
STATE.md/PROJECT.md "Active", sem gate sobre este milestone.

### Phase 10: Ponte gatilho→put

**Goal**: Quando um detector de setup dispara sobre um ticker presente em
`positions` do usuário, o sistema seleciona automaticamente uma série de put
candidata para proteção — estrutura proposta sobre o fechamento do pregão
(decisão travada: EOD de ponta a ponta, sem preço de opção ao vivo) — e
grava a sugestão no ledger com proveniência. Puramente backend, nenhuma
superfície visível.
**Depends on**: Phase 0 (ledger sem 404 residual e gate de orçamento das
opções fechado antes de qualquer seleção de série rodar de forma autônoma
dentro do `scheduler_loop`)
**Requirements**: PUT-01, PUT-02, PUT-03
**Success Criteria** (what must be TRUE):
  1. Um hook novo dentro do `scheduler_loop` de `agent.py` (mesmo padrão
     try/except dos hooks existentes — `radar_daily`, `signal_ledger_job`
     etc. — sem scheduler novo) dispara quando um detector de setup aciona
     sobre um ticker presente em `positions` do usuário
  2. A série candidata de put é selecionada usando `estilo_exercicio`,
     strike e IV reais devolvidos pelo hub mydata — nunca assumidos
     localmente — no mesmo modelo de `find_tradable_options` do portal
     mydata (`~/dev/MCP/servers/mydata/server.py`)
  3. A sugestão selecionada é gravada no ledger de sinais com proveniência
     (fonte, `as_of`, `sha256`/`dt_captura` quando disponíveis na resposta
     do hub)
  4. Nenhuma rota HTTP nova, push, card ou texto expõe a sugestão de put —
     grep no diff confirma zero alteração em `App.jsx`/`persistence.js`/
     `copy.js`/`skill_ref.py` (vocabulário visível ao usuário)
  5. Suíte canônica (`bash scripts/executar.sh --testes`) verde
**Guardrails** (aplicam a esta fase e a todo o milestone v1.2):
  - Nenhum deploy, nenhum `git push` para origin, nenhuma mudança de env
    var de produção
  - `B3_OPTIONS_PROVIDER` nunca é alterado
  - Nenhuma superfície visível ao usuário introduzida
  - Nenhum suporte a opção vendida/short introduzido em qualquer forma —
    só put comprada, uma perna, sem margem, sem atribuição
**Plans**: 3 plans (3 waves — cada plano depende do anterior; sem paralelismo,
o Plano 02 consome os módulos do 01 e o 03 prova a ausência de superfície do
conjunto)

Plans:
**Wave 1**

- [x] 10-01-PLAN.md — tabela `put_suggestions` (long-only por CHECK, estilo de
  exercício e IV NOT NULL) + `put_suggestions.py` + triagem determinística
  `put_bridge.triar_put` (função pura, offline)

**Wave 2** *(blocked on Wave 1)*

- [ ] 10-02-PLAN.md — `put_bridge.run_diario`/`maybe_run`: cruzamento
  gatilho EOD × carteira, consulta sequencial à cadeia (teto de 10 tickers/dia),
  gravação com proveniência, e o hook no `scheduler_loop` após
  `signal_ledger_job`

**Wave 3** *(blocked on Wave 2)*

- [ ] 10-03-PLAN.md — guardião automatizado de PUT-03 (fonte + comportamento +
  agregações do ADR-017) + ADR-021 (onde a sugestão mora, long-only estrutural,
  disposição de WR-01) + doc de operação + fechamento da suíte canônica

### Phase 11: Ciclo de vida e monitoramento

**Goal**: Toda sugestão de put armada tem um estado rastreável ao longo do
tempo (`armada` → `expirada sem uso` | `executada (simulada)` →
`monitorada` → `fechada`). Execução simulada e fechamento por expiração
reusam integralmente `optionPositions` e os contratos de ADR-003/004/005;
monitoramento é diário (decisão travada: EOD de ponta a ponta, sem preço de
opção ao vivo) e roda dentro da segunda passada já existente do `agent.py`.
**Depends on**: Phase 10 (precisa de sugestões gravadas no ledger para ter
o que monitorar)
**Requirements**: PUTLIFE-01, PUTLIFE-02, PUTLIFE-03, PUTLIFE-04
**Success Criteria** (what must be TRUE):
  1. Toda sugestão de put no ledger carrega um campo de estado que
     transiciona apenas pelos 5 estados definidos (`armada`, `expirada sem
     uso`, `executada (simulada)`, `monitorada`, `fechada`), sem estado
     inválido ou inatingível
  2. A execução simulada de uma put usa `optionPositions` e os contratos de
     ADR-003/004/005 sem nenhuma função paralela de cálculo de preço médio,
     PnL ou proveniência de posição de opção
  3. O fechamento por expiração de uma put de proteção reusa o mecanismo já
     resolvido pelo ADR-005 (`motivo: "vencimento"`) — sem lógica de
     expiração paralela
  4. O monitoramento diário de puts de proteção roda dentro da segunda
     passada já existente do `agent.py` para `optionPositions` (linha
     ~527, `_avaliar_opcoes`/equivalente) — nenhum scheduler novo, nenhum
     cron externo
  5. Nenhuma superfície visível ao usuário introduzida — grep no diff
     confirma zero alteração em front-end
**Guardrails** (aplicam a esta fase e a todo o milestone v1.2):
  - Nenhum deploy, nenhum `git push` para origin, nenhuma mudança de env
    var de produção
  - `B3_OPTIONS_PROVIDER` nunca é alterado
  - Nenhuma superfície visível ao usuário introduzida
  - Nenhum suporte a opção vendida/short introduzido em qualquer forma
**Plans**: TBD
