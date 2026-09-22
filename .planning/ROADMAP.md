# Roadmap: Boris+ (b3-agente)

## Milestones

- ✅ **v1.0 Revisão Geral** — Phase 1 (shipped 2026-08-18) — [detalhes](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Realismo de Mercado + Correções** — Phases 2-8 (shipped 2026-08-23) — [detalhes](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Camada de opções ancorada na carteira** — Phases 0, 10, 11 (shipped 2026-08-28) — [detalhes](milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Cap comercial (plano gratuito)** — Phases 12-13 (shipped 2026-08-31) — [detalhes](milestones/v1.3-ROADMAP.md)
- ✅ **v1.5 Redesenho de UI — simplificação e acessibilidade** — Phases 20-23 (shipped 2026-09-06) — [detalhes](milestones/v1.5-ROADMAP.md)
- ✅ **v1.4 Opções v2** — Phases 15-19, 24-32 (shipped 2026-09-19) — [detalhes](milestones/v1.4-ROADMAP.md)
- ✅ **v1.6 Simplificação da aba Opções** — Phases 33-34 (shipped 2026-09-20) — [detalhes](milestones/v1.6-ROADMAP.md)
- 🚧 **v1.7 Confiabilidade explicativa da aba Opções** — Phases 35-37 (in progress)

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
mais concretos: jornada do workspace sem passos visíveis, e gráfico de
payoff (`PayoffChart.jsx`) matematicamente incorreto (screenshot de
produção, 2026-09-20).

- [x] Phase 35: Jornada Guiada do Workspace (3/3 plans) — completed 2026-09-21
- [x] Phase 36: Motor de Payoff Genérico (2/2 plans) — completed 2026-09-21
- [ ] Phase 37: Gráfico de Payoff e Explicação Confiáveis (0/5 plans)

**Phase Numbering:** continua a partir do fim do v1.6 (Phase 34) — Fases
35-37 definidas por `/gsd-roadmapper` a partir de `REQUIREMENTS.md` v1.7
(14 requirements: JORN-01..03, PAYOFF-01..03, CHART-01..05, EXPL-01..03).
Ordem de dependência: Fase 36 (motor de payoff, puro/determinístico) precisa
fechar antes da Fase 37 (gráfico SVG + explicação), que consome a forma de
saída do motor. Fase 35 (jornada do workspace, toca só navegação/copy de
`OpcoesScreen.jsx`) não depende de nenhuma das outras duas — sequenciada
primeiro por conveniência de execução (branch única, `workflow.use_worktrees=false`),
não por dependência técnica real.

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
| 37. Gráfico de Payoff e Explicação Confiáveis | 2/5 | Executing (wave 1/3) | - |

## Phase Details

### Phase 35: Jornada Guiada do Workspace

**Goal**: Usuário monta e analisa uma estrutura de opções dentro do
workspace (pills Analisar/Comparar/Setups salvos) vendo passos claros do
ticker escolhido até "ver possibilidades", sem se perder e sem precisar de
explicação externa.
**Depends on**: Nenhuma (independente de PAYOFF/CHART/EXPL — sequenciada
primeiro por conveniência de execução, não por dependência técnica)
**Requirements**: JORN-01, JORN-02, JORN-03
**Success Criteria** (what must be TRUE):
  1. Na pill Analisar, o usuário vê indicação visual de progresso/etapas do
     ticker escolhido até "ver possibilidades" (JORN-01)
  2. O botão "ver possibilidades" é visualmente proeminente e comunica seu
     propósito sem exigir explicação externa (JORN-02)
  3. As pills Comparar e Setups salvos exibem o mesmo padrão de clareza de
     passos que Analisar — paridade de tratamento entre as 3 (JORN-03)
  4. Em qualquer uma das 3 pills do componente `OpcoesScreen.jsx`, o usuário
     consegue dizer em qual etapa está e o que falta para avançar
**Plans**: 3 plans
- [x] 35-01-PLAN.md — vocabulário da jornada (7 chaves nos dois modos) + rótulos de estágio, gate por pill ativa e ramo "leitura já feita" em `OpcoesScreen.jsx` (D-01/D-02/D-06/D-08) — completo 2026-09-21 (guardião novo com 3 provas negativas reais; 2923 pytest + mjs verde; App.jsx intocado)
- [x] 35-02-PLAN.md — `BOTAO_PRIMARIO` nos 3 CTAs da jornada com `T.onAccent`, marca de resultado re-clicável e varredura de tokens do diretório (D-03/D-04/D-05/D-06/D-07) — completo 2026-09-21 (fold-in real do bug `T.bgPanel` em `SecaoVigias.jsx`; guardião com 70 asserções e 4 provas negativas; 2923 pytest + mjs verde; App.jsx intocado)
- [x] 35-03-PLAN.md — checkpoint humano ao vivo nos 4 pares tema × modo (fecha o risco aberto de D-07) + bump/publicação gated pela aprovação — completo 2026-09-21 (aprovado ao vivo, publicado F10-20260921-01, /api/health confirmado)
**UI hint**: yes

### Phase 36: Motor de Payoff Genérico

**Goal**: O motor de payoff calcula, de forma pura e determinística,
resultado/breakevens/ganho-perda máxima/domínio X-Y para qualquer combinação
de legs, sem lógica por nome de estratégia, cobrindo os casos-limite
especificados — base que a Fase 37 (gráfico + explicação) consome.
**Depends on**: Nenhuma (fase fundacional do motor; independente da Fase 35)
**Requirements**: PAYOFF-01, PAYOFF-02, PAYOFF-03
**Success Criteria** (what must be TRUE):
  1. Dado um conjunto de legs (`kind`/`side`/`strike`/`premium`/`qty`/`expiry`),
     o motor devolve resultado/breakevens/ganho-máx/perda-máx/domínio X-Y
     corretos, sem nenhum `switch`/`case` ou dicionário de texto por nome de
     estratégia (PAYOFF-01)
  2. Os casos-limite documentados (perna única, venda descoberta/ratio
     spread, travas de alta/baixa, borboleta/condor, straddle/strangle,
     covered call/collar, box, calendário/diagonal degradando com
     honestidade, lotes assimétricos, entrada degenerada) produzem resultado
     correto ou recusa com mensagem clara — nunca `NaN` (PAYOFF-02)
  3. O caso golden (trava de alta com calls, strikes 49,17/49,67, débito
     0,25, lote 100) é teste de regressão nomeado que trava breakeven 49,42,
     ganho/perda máx R$ 25,00, 3 segmentos, nenhum ilimitado (PAYOFF-03)
  4. Nenhum ponto do motor decide o cálculo a partir do nome da estratégia —
     auditável por leitura direta do módulo puro (sem chamada de IA, sem
     dependência nova de charting de terceiros)
**Plans**: 2 plans (2 ondas sequenciais — `server/app/opcoes_payoff.py` é
tocado pelos dois, sem paralelismo honesto). Achado da discussão: um motor
genérico já existe em produção (`opcoes_payoff.py`, Fase 15) — esta fase
ESTENDE, não recria (D-01).
- [x] 36-01-PLAN.md — `vencimento` por perna + degradação de calendário
  (D-03); recusa de entrada degenerada + correção do breakeven espúrio em
  S=0 (D-04); casos-limite de PAYOFF-02 em teste nomeado (D-07 parte 1) —
  completo 2026-09-21 (verificado de novo direto no código pelo orquestrador
  após o executor; 48 testes, 2943 pytest + 154/154 mjs, App/web intocados)
- [x] 36-02-PLAN.md — `dominio_da_curva()` (D-05); `segmentos_da_curva()`
  (D-06); caso golden como regressão nomeada + auditoria de PAYOFF-01 +
  suíte canônica — completo 2026-09-21 (verificado de novo direto no
  código; 65 testes, 2960 pytest + 154/154 mjs; nada publicado, backend
  puro sem consumidor ainda)

### Phase 37: Gráfico de Payoff e Explicação Confiáveis

**Goal**: O componente SVG de payoff (`PayoffChart.jsx`) e o texto
explicativo gerado a partir da curva calculada são matematicamente corretos,
coerentes entre si e com o motor da Fase 36 — vocabulário leigo, sem jargão
técnico banido e sem promover recomendação.
**Depends on**: Phase 36 (consome PAYOFF-01/02/03 — segmentos, breakevens e
domínio X-Y do motor de payoff)
**Requirements**: CHART-01, CHART-02, CHART-03, CHART-04, CHART-05, EXPL-01,
EXPL-02, EXPL-03
**Success Criteria** (what must be TRUE):
  1. O gráfico mostra a linha do zero tracejada rotulada "R$ 0", eixo
     vertical com escala visível, todo strike/breakeven marcado e rotulado,
     e o spot marcado "hoje {preço}" (CHART-01, CHART-02)
  2. Segmento de risco ilimitado termina em seta aberta na borda rotulada
     "sem teto"/"sem piso" — nunca desenha um platô falso onde o risco é
     ilimitado (CHART-03)
  3. O domínio X (min/max strike + margem especificada, spot sempre dentro)
     e o domínio Y (inclui zero, +15% do extremo finito) nunca cortam um
     platô real (CHART-04)
  4. O valor de marcação a mercado ("hoje · valor de mercado da estrutura")
     aparece separado e rotulado, distinto do resultado "no vencimento ·
     {data}" — corrige a regressão confirmada em produção por screenshot
     (CHART-05)
  5. O texto explicativo é derivado dos segmentos da curva calculada
     (segmento onde o spot está descrito primeiro), livre do vocabulário
     técnico banido, e a razão G/P impressa no texto é o mesmo número
     exibido em tela — corrige a regressão confirmada em produção
     ("1:1,00" exibido vs. "1:0,67" no texto) (EXPL-01, EXPL-02, EXPL-03)
**Plans**: 5 plans (3 ondas — mesmo arquivo força onda sequencial em
`options_mcp_api.py`/`copy.js`/`PayoffChart.jsx`; contrato de campo
camelCase fixado no planejamento habilita paralelismo dentro de cada onda)
- [x] 37-01-PLAN.md — adaptador EN→PT + `dominio`/`segmentos` no envelope de `proposta`/`possibilidades` (CHART-04) — completo 2026-09-21 (2968 pytest + 154/154 mjs)
- [x] 37-02-PLAN.md — `copy.js` (todas as chaves novas + D-04) + `formatarRazao()` extraído + `ExplicacaoPayoff.jsx` novo (EXPL-01/02/03) — completo 2026-09-21 (TDD RED→GREEN, npx vite build ok)
- [ ] 37-03-PLAN.md — busca de `valorHoje` via `get_option_chain`, gate do 1º candidato em `possibilidades()` (CHART-05 backend)
- [ ] 37-04-PLAN.md — `PayoffChart.jsx`: eixo Y, strike/spot no eixo, setas rotuladas, bloco Hoje/No vencimento (CHART-01/02/03 + CHART-05 frontend)
- [ ] 37-05-PLAN.md — wiring em `SecaoAnalisar.jsx`/`SecaoComparar.jsx` + checkpoint humano ao vivo (fecha CHART-01..05/EXPL-01..03 de ponta a ponta)
**UI hint**: yes

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
Confiabilidade explicativa da aba Opções (Phases 35-37) aberto em
2026-09-20 — Fase 35 (jornada do workspace, independente), Fase 36 (motor
de payoff genérico, fundacional) e Fase 37 (gráfico + explicação,
dependente da Fase 36).
