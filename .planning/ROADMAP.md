# Roadmap: Boris+ (b3-agente)

## Milestones

- ✅ **v1.0 Revisão Geral** — Phase 1 (shipped 2026-08-18) — [detalhes](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Realismo de Mercado + Correções** — Phases 2-8 (shipped 2026-08-23) — [detalhes](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Camada de opções ancorada na carteira** — Phases 0, 10, 11 (shipped 2026-08-28) — [detalhes](milestones/v1.2-ROADMAP.md)
- 🚧 **v1.3 Cap comercial (plano gratuito)** — Phases 12-13 (in progress)

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
| 12. Limites do plano gratuito ativos | 3/3 | Complete   | 2026-08-29 |
| 13. Uso real visível na interface + enforcement no iOS | 2/5 | In Progress|  |

### Phase 9: Centralização de dados de mercado (mydata_client.py) — standalone, fora de v1.0/v1.1/v1.2

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

---

### 🚧 v1.3 Cap comercial (plano gratuito) (In Progress)

**Milestone Goal:** ativar de verdade os limites do plano gratuito que o
ADR-010 já desenhou tecnicamente — `PLAN_FREE.max_watchlist=10` e
`PLAN_FREE.max_analyses_per_month=30` passam de `None` (ilimitado) para
números reais, os hooks `can_add_ticker`/`can_analyze` (`server/app/plan.py`)
passam a bloquear de verdade, e a UI mostra o número real de uso/limite.
Sem loja/IAP neste milestone; `PLAN_PRO` continua ilimitado.

**Achado de investigação (orienta as duas fases):** a fiação já existe.
`_gate_analise` (linha 453 de `server/app/main.py`) já chama
`plan.can_analyze(metering.month_used(_conn, scope), plan=plano)` e o
endpoint `/api/ai-quota` já devolve `monthUsed`/`monthLimit` reais
(`_plano_do_escopo(scope).get("max_analyses_per_month")`); o hook de
adicionar ticker (linha 1069) já chama
`plan.can_add_ticker(len(watchlist), plan=...)`. Não existe hoje nenhum
endpoint que exponha `max_watchlist`/contagem atual da watchlist para a UI —
essa exposição nova é escopo exclusivo da Fase 13, não da Fase 12.

**Decisões de arquitetura travadas neste milestone (não reabrir):**

1. Cap comercial (por conta) e cota física da brapi (por app inteiro) são
   camadas independentes — um usuário pago consome da mesma cota física, só
   sem limite comercial próprio (ADR-010, decisão 2)

2. Fonte de cotação (brapi/Yahoo) não é diferencial de plano — infraestrutura
   igual pra todo mundo (ADR-010, decisão 3)

3. Sem loja/IAP, sem validação de recibo, sem preço/moeda neste milestone —
   `PLAN_PRO` segue ilimitado por decisão, não por lacuna técnica

- [x] **Phase 12: Limites do plano gratuito ativos** - `PLAN_FREE` ganha números reais e os gates passam a recusar de verdade, com o resto do app intacto e a mensagem de recusa sem tom de upgrade urgente (completed 2026-08-29)
- [ ] **Phase 13: Uso real visível na interface + enforcement no iOS** - Usuário vê "ativos: X/10" e "análises deste mês: X/30" reais, nos dois stores (web e iOS), nunca estimado ou escondido; e o cap de 10 ativos passa a valer de verdade no app iOS nativo (CAP-12)

### Phase 12: Limites do plano gratuito ativos

**Goal**: Usuário no plano gratuito é bloqueado de verdade ao tentar
ultrapassar 10 ativos na watchlist ou 30 análises de IA no mês corrente,
usando a contagem real de `metering.py`; usuário no plano pago não sofre
nenhum dos dois limites; e nenhuma outra funcionalidade do app degrada
quando um limite é atingido.
**Depends on**: Nothing (primeira fase do milestone — a estrutura de gate já
existe em `plan.py`/`metering.py`/`main.py`, esta fase liga os números e
fecha a lacuna de copy, sem infraestrutura nova)
**Requirements**: CAP-01, CAP-02, CAP-03, CAP-04, CAP-05, CAP-07
**Success Criteria** (what must be TRUE):

  1. Usuário no plano free que já tem 10 ativos na watchlist não consegue
     adicionar um 11º — a ação é recusada (`POST` de adicionar ticker) com
     o motivo exato, não um erro genérico

  2. Usuário no plano free que já pediu 30 análises de IA no mês corrente
     não consegue pedir a 31ª — a ação é recusada com o motivo exato, e a
     contagem usada pelo gate é `metering.month_used` (ledger real, já
     wired em `_gate_analise`), nunca um contador paralelo — confirmado por
     teste que prova que zerar/ignorar o ledger muda o resultado do gate

  3. Usuário no plano pro consegue ultrapassar as duas marcas (11º ativo,
     31ª análise) no mesmo mês sem nenhuma recusa

  4. Depois de uma recusa por limite, o resto do app continua funcionando
     normalmente: comprar/vender ação, ver cotações, remover um ativo já
     existente da watchlist, pedir análise dentro da cota restante — nenhuma
     outra funcionalidade degrada

  5. A mensagem de recusa (watchlist e análise) declara só o fato e o
     motivo — o texto atual de `can_add_ticker`
     ("Faça upgrade para adicionar mais.") é revisado para tirar o tom de
     CTA/upgrade urgente, ficando conforme o princípio 8 do CLAUDE.md
**Plans**: 3 plans

Plans:
**Wave 1**

- [x] 12-01-PLAN.md — ativa `PLAN_FREE` (10 ativos / 30 análises-mês), tira o CTA da recusa de `can_add_ticker` e ATUALIZA (não apaga) os dois guardiões que travavam "nenhum limite comercial ativado"

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 12-02-PLAN.md — fecha o bypass do `PUT /api/watchlist` (gate que só bloqueia crescimento, D-03/D-04) + `store.normalize_watchlist` como fonte única do tamanho final + suíte de comportamento do cap de ativos
- [x] 12-03-PLAN.md — suíte de comportamento do cap mensal de análises (prova que o ledger de `metering` é quem decide) + registro da ativação no ADR-010

**Decisão do Alex (2026-08-29):** as lacunas abaixo foram dobradas no escopo
da Fase 13 (opção (a) de [.planning/todos/pending/cap-gratuito-lacunas-de-cobertura.md](todos/pending/cap-gratuito-lacunas-de-cobertura.md))
— o `deviceStore` do iOS grava a watchlist só no aparelho e não passa por
gate nenhum (CAP-01 não valia no app nativo), e `web/src/plan.js` ainda
carrega a copy com CTA (hoje inalcançável). Ver Fase 13 abaixo, que ganhou
CAP-12 e enforcement no cliente nativo além da visibilidade original.

**Revisão pós-fase**: code review encontrou 1 Critical + 3 Warning + 1 Info (ver [12-REVIEW.md](phases/12-limites-do-plano-gratuito-ativos/12-REVIEW.md)). Os 3 Warning foram corrigidos e **mergeados no main** via [PR #26](https://github.com/AlexandreCamerini/b3agente/pull/26); o Critical (CR-01, bypass do cap no iOS) é o mesmo item 1 da lacuna acima, endereçado como CAP-12 na Fase 13.

### Phase 13: Uso real visível na interface + enforcement no iOS

**Goal**: Usuário no plano gratuito vê o número real de uso/limite —
ativos na watchlist e análises de IA no mês — antes de esbarrar no limite,
tanto no web quanto no app iOS nativo, nunca estimado ou escondido; e no
app iOS nativo, o mesmo limite de 10 ativos que já vale no web/PWA desde a
Fase 12 passa a valer de verdade (CAP-12) — hoje o `deviceStore` grava
direto no aparelho sem checar nada.
**Depends on**: Phase 12 (os limites precisam estar realmente ativos e
contando certo antes de expor o número na tela; esta fase também precisa de
um endpoint novo expondo `max_watchlist`/contagem atual da watchlist, que
nenhum requirement da Fase 12 exige — só existe hoje para análises via
`/api/ai-quota`)
**Requirements**: CAP-06, CAP-12
**Success Criteria** (what must be TRUE):

  1. Usuário no plano free vê "ativos: X/10" com X = contagem real da
     watchlist, em algum ponto visível da UI (Watchlist ou Carteira)

  2. Usuário no plano free vê "análises deste mês: X/30" com X = `monthUsed`
     real de `/api/ai-quota`, em algum ponto visível da UI

  3. Se o backend não conseguir responder o número real, a tela mostra
     estado de erro/indisponível — nunca um número inventado ou estimado
     (princípio 4 do CLAUDE.md)

  4. `deviceStore` (iOS) e `serverStore` (web) expõem o mesmo par de
     números (watchlist count/limit, análises count/limit) através de
     métodos espelhados — paridade confirmada pelo guardião existente de
     paridade de stores

  5. Usuário no plano pro não vê um limite artificial fixo (nem "X/10", nem
     contagem que sugira teto) — exibição condicional ao plano, sem número
     fabricado

  6. Usuário free no app iOS que já tem 10 ativos na watchlist não consegue
     adicionar o 11º — `deviceStore.putWatchlist`/`addWatchlistTicker`
     passam a checar o limite ANTES de gravar no `localStorage`, usando o
     `max_watchlist` real vindo do endpoint novo (item 3), nunca um `10`
     hardcoded no front (contrariaria o contrato C-32/C-33 de fonte única)

  7. `web/src/plan.js` perde a frase com CTA ("Faça upgrade para adicionar
     mais.") — mesma correção do CAP-07 do backend, agora no espelho do
     front

  8. Os resíduos triviais do rename BolsIA→Boris+ que sobraram no código/
     docs internos são limpos (comentário em `server/app/mydata_budget.py`,
     doc `docs/MEDICAO-Mydata-2026-08-27.md`) — sem tocar arquivos
     históricos protegidos pelo guardrail do repo (`RELEASES.md`, `qa/`,
     `ESTADO-*`, `CHECKOUT-*`)

  9. Checkpoint humano: Alex confirma (e corrige, se preciso) o nome do
     app exibido no App Store Connect/TestFlight — fora do alcance do
     agente, é configuração no portal da Apple, não no repositório
**Plans**: 5 plans
Plans:
**Wave 1**

- [x] 13-01-PLAN.md — endpoint GET /api/watchlist/quota (fonte única de count/limit) + teste de contrato + limpeza dos resíduos BolsIA

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 13-02-PLAN.md — watchlistQuota() nos dois stores, gate fail-closed do deviceStore (CAP-12/CR-01) e plan.js sem CTA (CAP-07 do front)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 13-03-PLAN.md — 3 contadores na UI (Watchlist, CatalogModal, Atividade da IA) com os 5 estados do 13-UI-SPEC

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 13-04-PLAN.md — checkpoints humanos: contraste do T.warn no tema claro + nome do app no App Store Connect

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 13-05-PLAN.md — bump + publicação do front e sincronização do bundle iOS

**UI hint**: yes
