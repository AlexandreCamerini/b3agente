# Roadmap: Boris+ (b3-agente)

## Milestones

- ✅ **v1.0 Revisão Geral** — Phase 1 (shipped 2026-08-18) — [detalhes](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Realismo de Mercado + Correções** — Phases 2-8 (shipped 2026-08-23) — [detalhes](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Camada de opções ancorada na carteira** — Phases 0, 10, 11 (shipped 2026-08-28) — [detalhes](milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Cap comercial (plano gratuito)** — Phases 12-13 (shipped 2026-08-31) — [detalhes](milestones/v1.3-ROADMAP.md)
- 🚧 **v1.4 Opções v2** — Phases 15-18 (in progress)

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

<details>
<summary>✅ v1.2 Camada de opções ancorada na carteira (Phases 0, 10, 11) — SHIPPED 2026-08-28</summary>

- [x] Phase 0: Precondições (2/2 plans) — completed 2026-08-28
- [x] Phase 10: Ponte gatilho→put (3/3 plans) — completed 2026-08-28
- [x] Phase 11: Ciclo de vida e monitoramento (3/3 plans) — completed 2026-08-28

Numeração de fase não-sequencial deliberada (Fase 0 = precondição midstream;
Fase 10 = continuação lógica da Fase 9, standalone; sem renumeração
contígua). Execução autônoma noturna sob contrato de autonomia — ver
`.planning/notes/RELATORIO-NOTURNO-v1.2.md` e
`.planning/notes/decisoes-autonomas-v1.2.md`.

Full phase details: [milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)

</details>

<details>
<summary>✅ v1.3 Cap comercial (plano gratuito) (Phases 12-13) — SHIPPED 2026-08-31</summary>

- [x] Phase 12: Limites do plano gratuito ativos (3/3 plans) — completed 2026-08-29
- [x] Phase 13: Uso real visível na interface + enforcement no iOS (5/5 plans) — completed 2026-08-31

Achado próprio do code review pós-Fase 13: gate fail-closed do iOS (CAP-12)
comparava a contagem do servidor em vez da do aparelho — corrigido e
mutation-tested antes de fechar a fase (`101335e`). CAP-12 vale para builds
novos; instalações já ativas no TestFlight só recebem o fix num build novo
distribuído pelo Alex (pendência nomeada em `13-05-SUMMARY.md`).

Full phase details: [milestones/v1.3-ROADMAP.md](milestones/v1.3-ROADMAP.md)

</details>

### 🚧 v1.4 Opções v2 (In Progress)

**Milestone Goal:** nova experiência de Opções no Boris+ que propõe setups
(venda coberta, put de proteção, collar) a partir da análise técnica sobre
posições reais da carteira, com aceite manual do usuário — independente do
MCP externo (b-mcp) até ele ficar pronto.

Numeração de fase continua a partir da última fase standalone (14, Opções
lastreadas). Fases desta milestone: 15-18.

#### Phase 15: Motor de proposta (arquitetura interna)
**Goal**: O motor determinístico de proposta de estruturas de opções existe
internamente — seleção de contrato, cálculo de payoff N-pernas, limite
interno `rastrear()`/`avaliar()` e gatilho técnico — pronto para as
estruturas da Fase 16 se apoiarem nele. Sem UI, sem chamada de rede ao
b-mcp.
**Depends on**: Phase 14 (opções lastreadas, motor single-leg em produção)
**Requirements**: ENG-01, ENG-02, ENG-03, ENG-04, ENG-05, ENG-06
**Success Criteria** (what must be TRUE):
  1. `rastrear()` (screening de cadeia) e `avaliar()` (avaliação de
     estrutura) existem como funções de limite interno no vocabulário do
     contrato ADR-004/`mydata_client.py` (prêmio/strike/delta/tipo) —
     trocáveis por chamadas reais ao b-mcp no futuro por troca de corpo de
     função, sem redesenho.
  2. A seleção de contrato usada por `avaliar()` aplica
     `liquidity_score >= 40` + strike extremo — a mesma régua já em
     produção em `server/app/opcoes_lastreadas.py` — nunca o critério por
     delta do `estruturas.py` do b-mcp.
  3. O payoff calculado por `avaliar()` (custo líquido, ganho/perda
     máximos, breakevens, delta somado) usa aritmética portada e testada de
     `calculos.py` do b-mcp, adaptada dentro do repo do Boris.
  4. Nenhuma chamada de rede sai do motor para o processo/serviço b-mcp —
     toda leitura de dado passa por `mydata_client.py` existente, e
     qualquer chamada nova ao hub mydata feita pelo motor passa pelo lock
     já existente (`mydata_budget.reservar()`), nunca um canal paralelo.
  5. O gatilho que aciona `avaliar()` é o motor de setups já em produção do
     Boris (Radar/`setups.py`/`indicators.py`, server-side) — nenhuma DSL
     de setups técnicos do b-mcp é portada ou depende dele.
**Plans**: 4 plans (3 waves)
- [x] 15-01-PLAN.md — aritmética pura de payoff de N pernas portada de `calculos.py` (ENG-02)
- [x] 15-02-PLAN.md — gatilho técnico reusando o plano do Radar + proibição da DSL do b-mcp (ENG-06)
- [x] 15-03-PLAN.md — limite interno `rastrear()`/`avaliar()` + adaptadores ADR-004 → perna (ENG-01, ENG-04)
- [x] 15-04-PLAN.md — guardiões de fronteira (sem rede ao b-mcp, canal único com orçamento) + ADR-024 (ENG-03, ENG-04, ENG-05)

#### Phase 16: Biblioteca de estruturas
**Goal**: Venda coberta e put de proteção deixam de nascer de motores
single-leg isolados (Fase 14) e passam a ser geradas pelo motor comum de N
pernas da Fase 15; collar existe como nova composição das mesmas duas
pernas — prova de que o motor compõe N pernas de verdade, não só 1.
**Depends on**: Phase 15
**Requirements**: LIB-01, LIB-02, LIB-03
**Success Criteria** (what must be TRUE):
  1. Usuário com posição comprada real recebe proposta de venda coberta
     (LIB-01) gerada pelo motor de N pernas da Fase 15 — não mais pelo
     motor single-leg isolado de `opcoes_lastreadas.py`.
  2. Usuário com posição comprada real recebe proposta de put de proteção
     (LIB-02) gerada pelo mesmo motor de N pernas — mesma fonte de seleção
     e payoff que a venda coberta, não uma implementação paralela.
  3. Usuário com posição comprada real recebe proposta de collar (LIB-03)
     combinando as duas pernas (call vendida + put comprada) num único
     payoff consolidado (custo líquido, ganho/perda máximos, breakevens,
     delta somado).
**Plans**: 4 plans

Plans:
- [x] 16-01-PLAN.md — venda coberta e put de proteção pelo motor comum: seleção por `rastrear()` + payoff/caixa aditivos (LIB-01, LIB-02)
- [x] 16-02-PLAN.md — vocabulário canônico do collar nos dois modos + guardião CVM (LIB-03)
- [x] 16-03-PLAN.md — composição do collar: 3 pernas numa avaliação, gatilho de oferta e guardiões (LIB-03)
- [x] 16-04-PLAN.md — collar na rota por negociação de capacidade, trava de execução de meia estrutura e ADR-025 (LIB-01, LIB-02, LIB-03)

#### Phase 17: Fluxo de aceite
**Goal**: Usuário vê os dados completos de uma proposta — via o mecanismo
de card de proposta já em produção desde a Fase 14 (AtivoCard), antes de
existir a aba dedicada — e decide aceitar ou recusar explicitamente; ao
aceitar, a execução usa o mesmo motor de ordens de opções lastreadas da
Fase 14 (`store.py`), sem nenhuma automação nova; toda proposta declara
fonte e horário do dado usado.
**Depends on**: Phase 16
**Requirements**: FLOW-01, FLOW-02, FLOW-03, FLOW-04
**Success Criteria** (what must be TRUE):
  1. Usuário visualiza estrutura, pernas, prêmio, breakeven e ganho/perda
     máximos da proposta antes de decidir.
  2. Usuário aceita ou recusa a proposta com uma ação explícita — nenhuma
     execução dispara sozinha.
  3. Ao aceitar, a ordem é executada pelo mesmo motor de opções lastreadas
     da Fase 14 (`store.py`) — nenhum caminho de execução novo.
  4. Toda proposta exibida mostra a fonte e o horário do dado usado
     (frescor) — nunca dado silenciosamente desatualizado.
**Plans**: TBD
**UI hint**: yes

#### Phase 18: Aba Opções
**Goal**: Usuário acessa uma aba própria "Opções" na barra de navegação
inferior (Candidato A) que mostra só propostas com cobertura real e
comunica estado vazio claramente — a casa definitiva para o fluxo que já
funciona desde a Fase 17.
**Depends on**: Phase 17
**Requirements**: NAV-01, NAV-02, NAV-03
**Success Criteria** (what must be TRUE):
  1. Usuário encontra e abre a aba "Opções" na barra de navegação inferior.
  2. A aba mostra somente propostas sobre tickers com posição real na
     carteira do usuário — nunca uma estrutura sobre ticker sem cobertura.
  3. Quando não há proposta disponível (sem cobertura elegível, ou
     cobertura elegível mas sem setup técnico ativo hoje), a aba comunica
     esse estado vazio claramente, com o motivo.
**Plans**: TBD
**UI hint**: yes

Fora de escopo desta milestone (decidido no kickoff): plano comercial da
feature, DSL de setups técnicos do b-mcp, integração MCP real (Estratégia
C) — ver `.planning/REQUIREMENTS.md` Out of Scope / Future Requirements.

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
| 9. Centralização de dados de mercado (mydata_client.py) | standalone | Complete | 2026-08-27 |
| 0. Precondições | v1.2 | Complete | 2026-08-28 |
| 10. Ponte gatilho→put | v1.2 | Complete | 2026-08-28 |
| 11. Ciclo de vida e monitoramento | v1.2 | Complete | 2026-08-28 |
| 12. Limites do plano gratuito ativos | v1.3 | Complete | 2026-08-29 |
| 13. Uso real visível na interface + enforcement no iOS | v1.3 | Complete | 2026-08-31 |
| 14. Opções lastreadas — venda coberta e put de proteção | standalone | Complete (em produção) | 2026-08-31 |
| 15. Motor de proposta (arquitetura interna) | 4/4 | Complete   | 2026-09-02 |
| 16. Biblioteca de estruturas | 4/4 | Complete   | 2026-09-03 |
| 17. Fluxo de aceite | v1.4 | Not started | - |
| 18. Aba Opções | v1.4 | Not started | - |

### Phase 9: Centralização de dados de mercado (mydata_client.py) — standalone, fora de v1.0/v1.1/v1.2/v1.3

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

**Status pós-checkpoint:** virada de produção `adiada` — `B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER` seguem em `brapi`/`yahoo`. Perna ao vivo da medição rodou em 2026-08-28 (chave confirmada autenticando), mas o pico/min (148 projetado vs. 60/min) segue sem mitigação. Ver `docs/MEDICAO-Mydata-2026-08-27.md` e `.planning/todos/pending/medir-rate-limit-mydata.md`.

### Phase 14: Opções lastreadas — venda coberta e put de proteção sobre posições da carteira — standalone, CONCLUÍDA e em produção (2026-08-31)

**Goal:** Redesenhar a mecânica de opções do zero para só permitir operações lastreadas por posição real da carteira: venda de CALL coberta (com lote-lastro travado enquanto a call estiver aberta, nunca simula atribuição/exercício — call sempre fecha antes do vencimento) e compra de PUT de proteção, ambas guiadas pela análise técnica do próprio ativo-lastro. UI vira proposta pronta (estilo card de decisão) + cadeia expansível. Estudo explica sem executar, Operador executa. Entra no Patrimônio Total/P&L da Carteira. Não reaproveita put_bridge/put_lifecycle (ADR-021, decisão de sombra) nem setOptionStop/setOptionAlvo (código morto hoje). **Atualização 2026-08-31:** WR-01 resolvido (lock, PR #28) e `B3_OPTIONS_PROVIDER=mydata` virou produção de verdade — verificado ao vivo (`providerStatus: "ok"`, cadeia real com Greeks). `B3_CANDLE_PROVIDER` continua `brapi` (ADR-008 intacto, decisão explícita do Alex). Decisões completas: [.planning/notes/opcoes-mecanica-lastreada-decisoes.md](notes/opcoes-mecanica-lastreada-decisoes.md). Fechamento: [docs/adr/023-opcoes-lastreadas.md](../docs/adr/023-opcoes-lastreadas.md) (Nota aditiva 2026-08-31).
**Requirements**: TBD
**Depends on:** Phase 13
**Plans:** 8/8 plans complete + fix WR-01 pós-fase (PR #28)

Plans:
**Wave 1**

- [x] 14-01-PLAN.md — Provedor de opções mock + trava de lastro no motor (`qtyTravada`, `qty_livre`, guardas de venda)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 14-02-PLAN.md — Operações lastreadas no motor: abrir/fechar CALL coberta e comprar PUT de proteção

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 14-03-PLAN.md — Motor de proposta determinística, vocabulário por modo e as três rotas HTTP
- [x] 14-04-PLAN.md — Liquidação forçada no vencimento (sem atribuição) e ramo lastreado no ciclo do agente

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 14-05-PLAN.md — Paridade dos dois stores do front + Patrimônio Total com as pernas lastreadas

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 14-06-PLAN.md — Card de proposta no AtivoCard, cadeia expansível e split Estudo × Operador

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 14-07-PLAN.md — Carteira: badge de trava, venda limitada ao livre, aviso de liquidação, patrimônio

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 14-08-PLAN.md — ADR-023, verificação ponta a ponta com o mock, publicação e checkpoint humano

---

Milestone em andamento: v1.4 Opções v2 (Phases 15-18). Próximo passo:
`/gsd:plan-phase 15`.
