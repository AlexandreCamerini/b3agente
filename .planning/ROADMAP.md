# Roadmap: Boris+ (b3-agente)

## Milestones

- ✅ **v1.0 Revisão Geral** — Phase 1 (shipped 2026-08-18) — [detalhes](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Realismo de Mercado + Correções** — Phases 2-8 (shipped 2026-08-23) — [detalhes](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Camada de opções ancorada na carteira** — Phases 0, 10, 11 (shipped 2026-08-28) — [detalhes](milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Cap comercial (plano gratuito)** — Phases 12-13 (shipped 2026-08-31) — [detalhes](milestones/v1.3-ROADMAP.md)
- ✅ **v1.5 Redesenho de UI — simplificação e acessibilidade** — Phases 20-23 (shipped 2026-09-06) — [detalhes](milestones/v1.5-ROADMAP.md)
- ✅ **v1.4 Opções v2** — Phases 15-19, 24-32 (shipped 2026-09-19) — [detalhes](milestones/v1.4-ROADMAP.md)
- ✅ **v1.6 Simplificação da aba Opções** — Phases 33-34 (shipped 2026-09-20) — [detalhes](milestones/v1.6-ROADMAP.md)
- ✅ **v1.7 Confiabilidade explicativa da aba Opções** — Phases 35-37 (shipped 2026-09-22) — [detalhes](milestones/v1.7-ROADMAP.md)
- ✅ **v1.8 Didática ampliada + continuidade da aba Opções** — Phases 38-41 (shipped 2026-09-25) — [detalhes](milestones/v1.8-ROADMAP.md)
- ✅ **v1.9 Jornada de Decisão** — Phases 42-43 (shipped 2026-09-27) — [detalhes](milestones/v1.9-ROADMAP.md)
- 🚧 **v2.0 Estruturas de opções na carteira** — Phases 44-47 (iniciada 2026-09-29)

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

<details>
<summary>✅ v1.7 Confiabilidade explicativa da aba Opções (Phases 35-37) — SHIPPED 2026-09-22</summary>

- [x] Phase 35: Jornada Guiada do Workspace (3/3 plans) — completed 2026-09-21
- [x] Phase 36: Motor de Payoff Genérico (2/2 plans) — completed 2026-09-21
- [x] Phase 37: Gráfico de Payoff e Explicação Confiáveis (5/5 plans) — completed 2026-09-22

Publicado em dois carimbos: `F10-20260921-01` (Fase 35) e `F10-20260922-01`
(Fase 37). Pendência não-bloqueante registrada: verificação visual em
produção com dado real do gráfico corrigido (checkpoint da Fase 37 fechou
com evidência automática, não visual — ver `STATE.md`).

Full phase details: [milestones/v1.7-ROADMAP.md](milestones/v1.7-ROADMAP.md)

</details>

<details>
<summary>✅ v1.8 Didática ampliada + continuidade da aba Opções (Phases 38-41) — SHIPPED 2026-09-25</summary>

- [x] Phase 38: KB Didática ampliada (6/6 plans) — completed 2026-09-23
- [x] Phase 39: Reestruturação de navegação da aba Opções (6/6 plans) — completed 2026-09-24
- [x] Phase 40: Continuidade da aba Opções (2/2 plans) — completed 2026-09-25
- [x] Phase 41: Consolidação de registros de tela (3/3 plans) — completed 2026-09-25

Publicado em quatro carimbos (`F10-20260923-01`, `F10-20260924-01`,
`F10-20260925-01`, `F10-20260925-02`), todas as fases com checkpoint humano
aprovado ao vivo. Achados de inconsistência da Fase 41 (D-04) registrados e
deliberadamente não corrigidos — ver `41-02-SUMMARY.md`.

Full phase details: [milestones/v1.8-ROADMAP.md](milestones/v1.8-ROADMAP.md)

</details>

<details>
<summary>✅ v1.9 Jornada de Decisão (Phases 42-43) — SHIPPED 2026-09-27</summary>

- [x] Phase 42: Crítico — cor, chip único e ordem de leitura (6/6 plans) — completed 2026-09-27
- [x] Phase 43: Refinamento — copy por modo, KpiBlock e ritmo (6/6 plans, incl. gap 43-06) — completed 2026-09-27

Publicado em dois carimbos: `F10-20260927-01` (Fase 42) e `F10-20260927-03`
(Fase 43 — o bump `-02` nunca foi ao ar). Ambas as fases fecharam com
checkpoint humano aprovado ao vivo pelo Alex. CHIP-03 teve premissa factual
corrigida durante a execução (KpiBlock/KpiCell eram código morto desde a
qa/49) — ver `v1.9-REQUIREMENTS.md`.

Full phase details: [milestones/v1.9-ROADMAP.md](milestones/v1.9-ROADMAP.md)

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
| 35. Jornada Guiada do Workspace | 3/3 | Complete (checkpoint humano aprovado ao vivo) | 2026-09-21 |
| 36. Motor de Payoff Genérico | 2/2 | Complete | 2026-09-21 |
| 37. Gráfico de Payoff e Explicação Confiáveis | 5/5 | Complete (checkpoint com ressalva — ver STATE.md) | 2026-09-22 |
| 38. KB Didática ampliada | 6/6 | Complete (publicado, checkpoint humano aprovado ao vivo) | 2026-09-23 |
| 39. Reestruturação de navegação da aba Opções | 6/6 | Complete (publicado `F10-20260924-01`, checkpoint humano aprovado ao vivo, override D-03 → "Destacadas") | 2026-09-24 |
| 40. Continuidade da aba Opções | 2/2 | Complete (publicado `F10-20260925-01`, checkpoint humano aprovado ao vivo, DP-1) | 2026-09-25 |
| 41. Consolidação de registros de tela | 3/3 | Complete (publicado `F10-20260925-02`, checkpoint humano aprovado ao vivo, achados D-04 não corrigidos) | 2026-09-25 |
| 42. Crítico — cor, chip único e ordem de leitura | 6/6 | Complete (publicado `F10-20260927-01`, checkpoint humano aprovado ao vivo, DP-1..DP-4) | 2026-09-27 |
| 43. Refinamento — copy por modo, KpiBlock e ritmo | 6/6 | Complete (publicado `F10-20260927-03`, checkpoint humano aprovado ao vivo, DP-1..DP-3, gap 43-06) | 2026-09-27 |

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
Simplificação da aba Opções (Phases 33-34) shipped em 2026-09-20 — ver
[milestones/v1.6-ROADMAP.md](milestones/v1.6-ROADMAP.md). v1.7
Confiabilidade explicativa da aba Opções (Phases 35-37) shipped em
2026-09-22 — ver [milestones/v1.7-ROADMAP.md](milestones/v1.7-ROADMAP.md).

v1.8 Didática ampliada + continuidade da aba Opções (Phases 38-41) shipped
em 2026-09-25 — ver [milestones/v1.8-ROADMAP.md](milestones/v1.8-ROADMAP.md).

v1.9 Jornada de Decisão (Phases 42-43) shipped em 2026-09-27 — ver
[milestones/v1.9-ROADMAP.md](milestones/v1.9-ROADMAP.md).

## v2.0 Estruturas de opções na carteira (Phases 44-47) — EM ANDAMENTO

Requirements: `.planning/REQUIREMENTS.md`. Mock: https://claude.ai/artifact/JEpy5VmkoddNTHyVYnYWZc

- [x] Phase 44: Motor — estrutura por ativo (ESTR-01..06)
- [x] Phase 45: Card de posição estruturada (CARD-01..06) — concluída em código 2026-09-30; validação em aparelho pendente (backend da Fase 44 ainda não em produção)
- [x] Phase 46: Carteira v6 — card de posição com modos Estudo e Operador (CART6-01..07) (completed 2026-10-02)
- [ ] Phase 46.1: Fechamento das ressalvas da 46 (G-07, G-08, AL-01, AL-02)
- [ ] Phase 47: Didática — expectativa matemática × taxa de acerto (DIDA-01..02)

### Phase 44: Motor — estrutura por ativo
**Goal:** o backend entrega, por ativo, todas as pernas e a leitura determinística da estrutura (resultado, faixa, estado, motivos), sem estimar nada.
**Requirements:** ESTR-01, ESTR-02, ESTR-03, ESTR-04, ESTR-05, ESTR-06
**Success criteria:**
1. Ativo com put + call abertas retorna as 2 pernas e classifica como collar (hoje só a primeira).
2. Resultado = P&L das ações + prêmio marcado a mercado; prêmio sem cotação devolve `null` e "incompleto", nunca 0.
3. Faixa no vencimento (piso/teto, perda/ganho máx.) bate com a conta pelos strikes em teste unitário; `null` quando indeterminável.
4. Estrutura aberta com gate de liquidez reprovado vira `aberta_sem_proposta` e não some; motivos distintos, frases só de `skill_ref.py` com paridade em `copy.js`.
**Modelo:** Sonnet executa/verifica; Opus só orquestra e planeja.

### Phase 45: Card de posição estruturada
**Goal:** o card de Posições mostra a estrutura inteira, com estados claros, sem aviso falso.
**Requirements:** CARD-01, CARD-02, CARD-03, CARD-04, CARD-05, CARD-06
**Depends on:** Phase 44
**Success criteria:**
1. UGPA3 (ações + put + call) mostra "collar", resultado total, régua de faixa e as 2 pernas visíveis.
2. Nenhum "sem stop" nem `R:R —` para estrutura protegida; piso/teto em texto do motor.
3. Os 5 estados renderizam; "Encerrar" bloqueado com motivo quando o prêmio está indisponível.
4. Estudo e Operador × claro/escuro passam contraste AA; `vite build` e guardiões verdes.
**UI hint:** yes (UI-SPEC a partir do mock)
**Plans:** 5 plans (4 ondas; App.jsx serializa as ondas 2-3)

Plans:
- [x] 45-01-PLAN.md — vocabulário ESTRUTURA_CARD (skill_ref.py↔copy.js), "collar" no lugar de "trava protetora", nota D-11 em CARD-06 (onda 1)
- [x] 45-02-PLAN.md — lógica pura do card (estruturaCard.js) + one-shot goOpcoes("oportunidades", {abrirTicker}) + verificação do destino do Encerrar (onda 1)
- [x] 45-03-PLAN.md — busca da estrutura, estados carregando/falha e CardPosicaoEstruturada (chips, resultado, estado, pernas, fonte, Encerrar) (onda 2)
- [x] 45-04-PLAN.md — régua de faixa, limites/contexto sem aviso falso, TravaPill em contorno, guardiões AA/SP (onda 3)
- [x] 45-05-PLAN.md — verificação final + checkpoint humano (4 combinações, M1, P4) (onda 4)

### Phase 46: Carteira v6 — card de posição com modos Estudo e Operador
**Goal:** o card de posição da Carteira segue o protótipo aprovado v6 — um visual e um estado no card fechado, flip Ação/Opções no aberto, e camada didática por modo (Estudo: simulador "e se?" e termos tocáveis; Operador: payoff e grade com a conta) — com todo cálculo no backend.
**Requirements:** CART6-01, CART6-02, CART6-03, CART6-04, CART6-05, CART6-06, CART6-07
**Depends on:** Phase 45
**Prototype:** `~/Downloads/Carteira Boris+ v6 (standalone).html`
**Decisão (Alex, 2026-09-30):** todo cálculo é do backend; o front só lê e posiciona (sem `optionsCalc` no cliente). Simulador usa grade de preços devolvida pelo backend.
**Plans:** 12/12 plans complete

Plans:
- [x] 46-01-PLAN.md — vocabulário v6 (CARTAO_POSICAO/CARTAO_DIDATICA skill_ref↔copy.js) + 6 verbetes KB (onda 1)
- [x] 46-02-PLAN.md — helpers puros do card (prioridade de estado, âncora/anti-colisão, flip reduzido, grade por índice) (onda 1)
- [x] 46-03-PLAN.md — motor puro cartao_posicao.py: leitura do plano, cenários/simulador/grade com conta, didática (onda 2)
- [x] 46-04-PLAN.md — fiação: estrutura.cenarios/didatica aditivos + POST /api/carteira/leitura + stores; pytest UGPA3/CXSE3/ITSA4 (onda 3)
- [x] 46-05-PLAN.md — card fechado v6 para toda posição (régua/faixa, um estado, Bóris explica, rodapé) (onda 4)
- [x] 46-06-PLAN.md — card aberto: seletor Ação|Opções, flip, faces, bloco BÓRIS IA e saída (onda 5)
- [x] 46-07-PLAN.md — camadas: Estudo (simulador + termos) e Operador (payoff SVG + grade com conta) (onda 6)
- [x] 46-08-PLAN.md — guardiões transversais (contraste/SP/higiene) + checkpoint do Alex (onda 7)
- [x] 46-09-PLAN.md — gap G-01..G-06: chaves novas do card fechado (skill_ref↔copy.js) + texto do cadeado (gap onda 1)
- [x] 46-10-PLAN.md — gap G-01..G-05: helpers puros (um estado, linhas rótulo/valor, chips, NBSP, fonte do valor) + CSS vars pendente/info e contraste (gap onda 1)
- [x] 46-11-PLAN.md — gap G-01..G-05: cabeçalho, linhas Ações/Opções/Estrutura, chips e um estado em CartaoPosicao + guardiões reancorados (gap onda 2)
- [x] 46-12-PLAN.md — gap G-06: faixa com rótulos ancorados e "● hoje" + checkpoint do Alex no iPhone (gap onda 3)

### Phase 46.1: Fechamento das ressalvas da Fase 46
**Goal:** corrigir o que o checkpoint do iPhone e o code review da 46 deixaram aberto, sem reabrir o desenho do card v6.
**Origem:** `46-UAT.md` (G-07, G-08), `46-REVIEW.md` (AL-01, AL-02; MD-01..06 candidatos), checkpoint do 46-12 (aprovado com ressalvas, 2026-10-02).
**Depends on:** Phase 46
**Escopo:**
1. G-07 — nome da empresa com fallback (catálogo/último conhecido); sem nome, só o ticker.
2. G-08 — "total suspenso" explica a causa por modo (skill_ref.py ↔ copy.js); default de `B3_OPTIONS_PROVIDER` não muda.
3. AL-01 — conta do Estudo para collar ignora o prêmio da put (número errado; cálculo é do backend, `cartao_posicao.py`).
4. AL-02 — `plano.status` ignorado: falha de `/api/carteira/leitura` mantém leitura antiga como atual (princípio 4 do produto).
5. Triagem de MD-01..06 (estado "Sem stop e alvo" com put; "sem teto" com cobertura parcial; preço sem fonte/horário; cabeçalho só com ações; idx do simulador) — incluir só o que o planner justificar.
**Fora de escopo:** aba Opções não executa a estrutura (não reproduzida); BX-01..07 (backlog).
**Plans:** 5 plans
- [ ] 46.1-01-PLAN.md — vocabulário 46.1 (skill_ref ↔ copy) + AL-01 equilíbrio do collar + MD-02 aria teto parcial + MD-03a nota de PM (onda 1)
- [ ] 46.1-02-PLAN.md — G-08 backend: causa da falta de prêmio por perna (`motivoSemCotacao`) + MD-03b corte das compras recentes (onda 1)
- [ ] 46.1-03-PLAN.md — helpers puros: G-07 nome com fallback, AL-02 situação da leitura, G-08 notas, MD-01, MD-05 (onda 1)
- [ ] 46.1-04-PLAN.md — fiação no App.jsx (hook com retry, CarteiraScreen, CartaoPosicao, LinhasResultadoV6) + guardiões (onda 2)
- [ ] 46.1-05-PLAN.md — checkpoint do Alex no iPhone (servidor local mydata): G-07, G-08, AL-02 (onda 3)

### Phase 47: Didática — expectativa matemática × taxa de acerto
**Goal:** o tema obrigatório do CLAUDE.md ganha verbete e o microtexto passa a abri-lo.
**Requirements:** DIDA-01, DIDA-02
**Success criteria:**
1. Verbete determinístico na KB, sem promessa de rentabilidade.
2. A cláusula tocável do microtexto abre o verbete (não `confluencia`); paridade `skill_ref.py`↔`copy.js` verde.
**Modelo:** Sonnet.
