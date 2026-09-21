# Roadmap: Boris+ (b3-agente)

## Milestones

- ✅ **v1.0 Revisão Geral** — Phase 1 (shipped 2026-08-18) — [detalhes](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Realismo de Mercado + Correções** — Phases 2-8 (shipped 2026-08-23) — [detalhes](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Camada de opções ancorada na carteira** — Phases 0, 10, 11 (shipped 2026-08-28) — [detalhes](milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Cap comercial (plano gratuito)** — Phases 12-13 (shipped 2026-08-31) — [detalhes](milestones/v1.3-ROADMAP.md)
- ✅ **v1.5 Redesenho de UI — simplificação e acessibilidade** — Phases 20-23 (shipped 2026-09-06) — [detalhes](milestones/v1.5-ROADMAP.md)
- ✅ **v1.4 Opções v2** — Phases 15-19, 24-32 (shipped 2026-09-19) — [detalhes](milestones/v1.4-ROADMAP.md)
- ✅ **v1.6 Simplificação da aba Opções** — Phases 33-34 (shipped 2026-09-20) — [detalhes](milestones/v1.6-ROADMAP.md)
- 🚧 **v1.7 Confiabilidade explicativa da aba Opções** — Phases TBD (in progress)

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

<details>
<summary>✅ v1.5 Redesenho de UI — simplificação e acessibilidade (Phases 20-23) — SHIPPED 2026-09-06</summary>

- [x] Phase 20: Fundação estrutural e tipográfica (4/4 plans) — completed 2026-09-05
- [x] Phase 21: Duplicação removida e Portfólio consolidado (4/4 plans) — completed 2026-09-06
- [x] Phase 22: Componentes compartilhados (trilho, ícones, mascote) (4/4 plans) — completed 2026-09-06
- [x] Phase 23: Motion com propósito e ilustração unificada (4/4 plans) — completed 2026-09-06

Nenhum requirement do v1.4 foi tocado por este milestone (invariante técnico
declarado no kickoff: só `web/src/`, sem alteração de motor/API/backend).
Débito técnico não-bloqueante e itens de verificação humana pendentes:
ver `.planning/milestones/v1.5-MILESTONE-AUDIT.md` e `20-HUMAN-UAT.md`.

Full phase details: [milestones/v1.5-ROADMAP.md](milestones/v1.5-ROADMAP.md)

</details>

<details>
<summary>✅ v1.4 Opções v2 (Phases 15-19, 24-32) — SHIPPED 2026-09-19</summary>

- [x] Phase 15: Motor de proposta (arquitetura interna) (4/4 plans) — completed 2026-09-02
- [x] Phase 16: Biblioteca de estruturas (4/4 plans) — completed 2026-09-03
- [x] Phase 17: Fluxo de aceite (6/6 plans, código) — completed 2026-09-03 (checkpoint humano adiado, não reprovado)
- [x] Phase 18: Seção de Opções em Posições (5/5 plans, código) — completed 2026-09-03 (checkpoint humano parcial)
- [x] Phase 19: Motor multi-candidato (4/4 plans, código) — completed 2026-09-04 (checkpoint humano pendente, ver ressalva)
- [x] Phase 24: Aba Opções sobre MCP — análise e criação de setups (12/13 plans) — completed 2026-09-12
- [x] Phase 25: Planos comerciais (6/6 plans) — completed 2026-09-12
- [~] Phase 26: Otimização de UX e da camada de IA (1/6 plans — só Fase A; B2/B3/C1/C2/C3 backlog) — completed (parcial) 2026-09-12
- [x] Phase 27: Aba Opções sobre a carteira (5/5 plans) — completed 2026-09-13
- [x] Phase 28: Sub-aba "Operar" e extração de `PropostaLastreada` (3/3 plans) — completed 2026-09-13
- [x] Phase 29: Opção a descoberto com flag opt-in (3/3 plans) — completed 2026-09-13
- [x] Phase 30: Curadoria de IA das 4 melhores estruturas (4/4 plans) — completed 2026-09-14
- [x] Phase 31: Varredura de oportunidades de opções (4/4 plans) — completed 2026-09-14
- [x] Phase 32: Consolidação das operações de opções na aba Opções (5/5 plans) — completed 2026-09-16

Numeração de fase não-contígua e deliberada: Fases 15-19 continuam a partir
da última fase standalone (14); Fases 24-32 nascem standalone cada uma,
pulando as Fases 20-23 (v1.5, executado em paralelo no mesmo branch sem
tocar o v1.4). Fase 26 está PARCIALMENTE completa (só "Fase A", 26-01) —
B2/B3/C1/C2/C3 nunca executados, carregados como backlog geral do produto
em `26-CONTEXT.md`, não como escopo shippado desta milestone. Checkpoints
humanos das Fases 17/18/19 (roteiro de `checkpoints-pendentes-fase-17-18-19.md`)
nunca fecharam individualmente ao vivo; o item de multi-candidato lado a
lado (Fase 19) segue sem confirmação em navegador real mesmo na verificação
da última fase da milestone (`32-VERIFICATION.md`, 2026-09-16). Detalhe
completo, decisões e tech debt: [milestones/v1.4-ROADMAP.md](milestones/v1.4-ROADMAP.md).

</details>

<details>
<summary>✅ v1.6 Simplificação da aba Opções (Phases 33-34) — SHIPPED 2026-09-20</summary>

- [x] Phase 33: Extração dos 5 jobs em componentes próprios (5/5 plans, verified 7/7) — completed 2026-09-20
- [x] Phase 34: Navegação hub + workspace (4/4 plans) — completed 2026-09-20

Full phase details: [milestones/v1.6-ROADMAP.md](milestones/v1.6-ROADMAP.md)

</details>

### 🚧 v1.7 Confiabilidade explicativa da aba Opções (In Progress)

**Milestone Goal:** corrigir a jornada de montar/analisar uma estrutura de
opções dentro do workspace e tornar o gráfico de payoff (e sua explicação)
matematicamente correto e genérico para qualquer estrutura — sem promover
recomendação.

**Origem:** pedido do Alex ao usar a navegação nova do v1.6 em produção
(2026-09-20) — a reorganização estrutural não tocou qualidade de explicação
por desenho (ver `PROJECT.md`, seção do milestone anterior); mapeia para
PERS-01 (`v1.6-REQUIREMENTS.md`), descoberto na prática como dois problemas
mais concretos.

**Phase Numbering:** continua a partir do fim do v1.6 (Phase 34) — fases
ainda não definidas, pendente de `/gsd-roadmapper` a partir de
`REQUIREMENTS.md` v1.7.

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
| 17. Fluxo de aceite | 6/6 | Complete (código; checkpoint humano adiado) | 2026-09-03 |
| 18. Aba Opções | 5/5 | Complete (código; checkpoint humano parcial) | 2026-09-03 |
| 19. Motor multi-candidato | 4/4 | Complete (código; checkpoint humano pendente) | 2026-09-04 |
| 20. Fundação estrutural e tipográfica | 4/4 | Complete    | 2026-09-05 |
| 21. Duplicação removida e Portfólio consolidado | 4/4 | Complete    | 2026-09-06 |
| 22. Componentes compartilhados (trilho, ícones, mascote) | 4/4 | Complete    | 2026-09-06 |
| 23. Motion com propósito e ilustração unificada | 4/4 | Complete    | 2026-09-06 |
| 24. Aba Opções sobre MCP — análise e criação de setups | 12/13 | Complete (24-05 nunca rodou como plano; publicado empacotado) | 2026-09-12 |
| 25. Planos comerciais — acesso por função e limites por plano | 6/6 | Complete | 2026-09-12 |
| 26. Otimização de UX e da camada de IA | 1/6 | Partial (só Fase A; B2/B3/C1/C2/C3 backlog) | 2026-09-12 |
| 27. Aba Opções sobre a carteira | 5/5 | Complete | 2026-09-13 |
| 28. Sub-aba "Operar" e extração de `PropostaLastreada` | 3/3 | Complete | 2026-09-13 |
| 29. Opção a descoberto com flag opt-in | 3/3 | Complete | 2026-09-13 |
| 30. Curadoria de IA das 4 melhores estruturas | 4/4 | Complete (30-04 sem SUMMARY — bookkeeping) | 2026-09-14 |
| 31. Varredura de oportunidades de opções | 4/4 | Complete | 2026-09-14 |
| 32. Consolidação das operações de opções na aba Opções | 5/5 | Complete | 2026-09-16 |
| 33. Extração dos 5 jobs em componentes próprios | 5/5 | Complete (verified, 7/7) | 2026-09-20 |
| 34. Navegação hub + workspace | 4/4 | Complete (verified, checkpoint humano aprovado ao vivo) | 2026-09-20 |

## Phase Details

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

v1.5 Redesenho de UI (Phases 20-23) shipped em 2026-09-06 — ver
[milestones/v1.5-ROADMAP.md](milestones/v1.5-ROADMAP.md). v1.4 Opções v2
(Phases 15-19, 24-32) shipped em 2026-09-19, com ressalvas documentadas —
ver [milestones/v1.4-ROADMAP.md](milestones/v1.4-ROADMAP.md). v1.6
Simplificação da aba Opções (Phases 33-34) aberto em 2026-09-19 — Fase 33
(extração) e Fase 34 (navegação hub/workspace, dependente de checkpoint
verde da Fase 33).
