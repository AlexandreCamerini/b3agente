# Roadmap: Boris+ (b3-agente)

## Milestones

- ✅ **v1.0 Revisão Geral** — Phase 1 (shipped 2026-08-18) — [detalhes](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Realismo de Mercado + Correções** — Phases 2-8 (shipped 2026-08-23) — [detalhes](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Camada de opções ancorada na carteira** — Phases 0, 10, 11 (shipped 2026-08-28) — [detalhes](milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Cap comercial (plano gratuito)** — Phases 12-13 (shipped 2026-08-31) — [detalhes](milestones/v1.3-ROADMAP.md)
- 🚧 **v1.4 Opções v2** — Phases 15-19 (in progress)
- ✅ **v1.5 Redesenho de UI — simplificação e acessibilidade** — Phases 20-23 (shipped 2026-09-06) — [detalhes](milestones/v1.5-ROADMAP.md)

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
**Plans**: 6 plans (4 waves)

Plans:
- [x] 17-01-PLAN.md — `store.abrir_collar`: execução de 2 pernas tudo-ou-nada numa única aquisição de ORDER_LOCK (FLOW-03)
- [x] 17-02-PLAN.md — rota de proposta declara fonte e horário do dado (FLOW-04)
- [x] 17-03-PLAN.md — `POST /api/options/lastreada/abrir-collar` com re-derivação server-side da proposta + ADR-026 (FLOW-02, FLOW-03)
- [x] 17-04-PLAN.md — payoff completo e frescor no card de proposta (FLOW-01, FLOW-04)
- [x] 17-05-PLAN.md — cliente declara multiperna, renderiza as 2 pernas e aceita explicitamente (FLOW-02, FLOW-03)
- [ ] 17-06-PLAN.md — publicação do front (bump + publicar-web) e verificação humana do fluxo
**UI hint**: yes

#### Phase 18: Seção de Opções em Posições
**Goal**: Usuário descobre propostas de opções sem aba nova — uma tira
"Oportunidades de opções" agregando todas as propostas ativas no topo de
Posições/Portfólio, mais o detalhe completo dentro de cada posição
específica. Decisão revista em 03/09 (mockup + navigation-specialist):
a barra inferior real já tem 5 abas (não 4, como presumido em 01/09), e
Opções só existe sobre posição real — nunca destino primário sem carteira
construída. Candidato A (aba própria) descartado; ver
`.planning/notes/opcoes-v2-b-mcp-exploracao.md` seção "Navegação" pro
histórico completo (preservado, não reescrito).
**Depends on**: Phase 17
**Requirements**: NAV-01, NAV-02, NAV-03
**Success Criteria** (what must be TRUE):
  1. Usuário vê, no topo de Posições, um resumo horizontal de todas as
     propostas de opções ativas no momento (múltiplos tickers de uma vez).
  2. Cada item do resumo abre o detalhe completo dentro da posição
     correspondente — nunca uma estrutura sobre ticker sem cobertura real.
  3. Quando não há nenhuma proposta ativa, o resumo comunica esse estado
     vazio claramente, com o motivo — nunca desaparece silenciosamente.
**Plans**: 5 plans
Plans:
- [x] 18-01-PLAN.md — vocabulário da tira em copy.js + hook `useOpcoesPropostas` (uma busca gate→proposta por ticker)
- [x] 18-02-PLAN.md — NAV-02: `PropostaDaPosicao` e detalhe completo dentro do card de posição, com aceite/encerramento
- [x] 18-03-PLAN.md — NAV-01/NAV-03: tira `OportunidadesOpcoes` no topo de Posições, com estados vazios explícitos
- [x] 18-04-PLAN.md — guardião estático da fase + suíte canônica completa verde
- [ ] 18-05-PLAN.md — bump + publicação do front e checkpoint humano ao vivo
**UI hint**: yes

#### Phase 19: Motor multi-candidato
**Goal**: O motor de proposta deixa de escolher UMA estrutura por posição
(regra fixa de `plano.decisao` em `opcoes_lastreadas.propor()`, fechada na
Fase 15/ENG-01) e passa a avaliar e devolver uma LISTA de candidatos
(venda coberta, put de proteção, collar) sempre que mais de um fizer
sentido pra mesma posição — usuário escolhe qual aceitar, em vez do motor
decidir sozinho. Não reabre nem reescreve ENG-01..06 (Fase 15 permanece
verificada como estava) — é extensão aditiva sobre o mesmo motor
`opcoes_motor.rastrear()`/`avaliar()`.
**Depends on**: Phase 18 (checkpoint humano de Task 2 do 18-05 segue
ABERTO em 2026-09-03 — verificado ao vivo no iPhone só parcialmente,
faltando o Radar disparar um setup ativo sobre alguma posição real; ver
`.planning/STATE.md` Blockers/Concerns. Planejar esta fase agora é seguro
— não executa nem publica nada — mas executá-la herdaria o mesmo risco já
nomeado pra Fase 17→18: publicar 19 empurraria pro ar, no mesmo bundle,
fluxo ainda não confirmado ao vivo. Decisão explícita do Alex: planejar
mesmo assim.)
**Requirements**: MULTI-01, MULTI-02
**Success Criteria** (what must be TRUE):
  1. Para uma posição comprada real onde mais de uma estrutura (venda
     coberta, put de proteção, collar) faz sentido pela análise técnica
     atual, o motor (`opcoes_lastreadas.propor()`/`opcoes_motor.avaliar()`)
     devolve TODOS os candidatos elegíveis, não mais um único escolhido por
     `plano.decisao` (MULTI-01).
  2. O detalhe da posição em Posições mostra os N candidatos lado a lado,
     no mesmo padrão visual da tira "Oportunidades" da Fase 18 — cada um
     com sua própria manchete verbatim do motor, payoff e CTA de aceite
     (MULTI-02).
  3. Usuário aceita exatamente um candidato por avaliação — aceitar um não
     deixa disponível a execução de outro candidato concorrente sobre a
     MESMA posição na mesma rodada (MULTI-02).
  4. Quando só uma estrutura é elegível (caso de hoje), o comportamento
     observável não muda — nenhuma regressão visual/funcional pra
     posições com um candidato só.
**Plans**: 4 plans

Plans:
**Wave 1**

- [x] 19-01-PLAN.md — `propor()` devolve lista de candidatos (aditivo; put_protecao antes de collar; negativos inalterados)

**Wave 2** *(blocked on Wave 1)*

- [x] 19-02-PLAN.md — `candidatos` na rota de proposta; `abrir-collar` busca o candidato por tipo com cross-check integral; exclusão mútua entre candidatos irmãos provada nas duas ordens

**Wave 3** *(blocked on Wave 2)*

- [x] 19-03-PLAN.md — `CandidatoOpcao` + ramo de N candidatos em `PropostaDaPosicao`; guardiões estáticos novos e guardião de collar atualizado com nota

**Wave 4** *(blocked on Wave 3)*

- [ ] 19-04-PLAN.md — bump + publicação (front e `SERVER_BUILD_ID`) e checkpoint humano bloqueante com o roteiro de 10 passos

**UI hint**: yes

Fora de escopo desta milestone (decidido no kickoff): plano comercial da
feature, DSL de setups técnicos do b-mcp, integração MCP real (Estratégia
C) — ver `.planning/REQUIREMENTS.md` Out of Scope / Future Requirements.

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

#### Phase 24: Aba Opções sobre MCP — análise e criação de setups — standalone
**Goal**: As Fases 3 e 5 do `docs/PLANO-aba-opcoes.md`. A aba Opções deixa de
só LER o serviço `mcp.semente.dev` (Fases 1 e 2, entregues como quick tasks em
2026-09-09/10 e já em produção) e passa a (a) mostrar cadeia, catálogo,
proposta montada e possibilidades por vencimento, com custo/ganho/perda em
reais para o lote em ações, e (b) criar setups técnicos a partir de uma
descrição em português, com ensaio antes de gravar e permissão de verdade.
**Depends on**: Fases 1 e 2 do PLANO (em produção). A **Fase 4 do PLANO
(veredito por prompt) fica FORA desta fase** — decisão do Alex em 2026-09-11
("faz a 3 primeiro e a 5 em seguida"): montar setup sem ver cadeia e
vencimentos na tela é montar no escuro. A fiação de LLM que a Fase 4 usaria
nasce no plano 24-03, pronta para reuso.
**Requirements**: PLANO Fases 3 e 5 (aceite literal em `docs/PLANO-aba-opcoes.md` §4)
**Success Criteria** (what must be TRUE):
  1. Para um ticker com cadeia aberta, a aba mostra por vencimento a
     estrutura montada com custo, ganho e perda em REAIS para o lote em
     ações, ±1σ, alvo/stop quando informados, breakevens e razão ganho/perda.
  2. Breakeven nunca é multiplicado pelo lote, e campo ausente do serviço
     nunca vira 0 — nem no backend, nem na tela.
  3. A UI mostra "2×N+1 chamadas" ANTES de disparar `/possibilidades`, com
     N ≤ 6.
  4. A matemática de payoff do Boris (`opcoes_payoff.perfil_da_estrutura`) e a
     do serviço (`evaluate_option_structure`) batem campo a campo sobre
     fixture gravada, com a variante viva pronta para o smoke de staging.
  5. Uma descrição em português vira setup declarativo validado pelo próprio
     serviço, com dry-run (`disparos`, `disparos_por_100`, `retorno_apos_disparo`
     d+5/d+10) visto antes de gravar, e `problems` voltando item a item.
  6. Sem `opcoes.criar_setup` a seção não existe **e** a rota responde 403;
     o guardião ENG-06 continua verde (nenhuma DSL copiada para dentro do app).
  7. Nenhuma rota nova escapa de `require_user` + `_cap_check`, e nada cai no
     handler 500.
**Plans**: 5 plans

Plans:

**Wave 1**

- [x] 24-01-PLAN.md — backend da Fase 3: `/cadeia`, `/operaveis`, `/proposta`, `/possibilidades`, helper de lote e paridade `opcoes_payoff` × MCP

**Wave 2** *(blocked on Wave 1; os dois planos tocam árvores disjuntas e rodam em paralelo)*

- [x] 24-02-PLAN.md — front da Fase 3: `PayoffChart.jsx`, seções "Analisar" e "Possibilidades", dois stores, dois modos de copy
- [x] 24-03-PLAN.md — backend da Fase 5: `list_tools`, compilador NL→DSL montado em runtime, `/setups/compilar|confirmar|desativar`, RBAC e auditoria

**Wave 3** *(blocked on Wave 2)*

- [x] 24-04-PLAN.md — front da Fase 5: seção "Criar setup" gateada por permissão, backtest ressalvado, guardião

**Wave 4** *(blocked on Wave 3 — NÃO autônomo)*

- [ ] 24-05-PLAN.md — bump + publicação do front e checkpoint humano no iPhone; só roda com OK explícito do Alex

**Fora das waves** — planos de fechamento de achado, escritos depois da
verificação goal-backward e dos testes ao vivo (é deles que vem o denominador
11 na tabela de progresso):

- [x] 24-06-PLAN.md — F-01/F-02/F-03 do `24-VERIFICATION.md` (razão ganho/perda, timeout da LLM, auditoria que não derruba a rota)
- [x] 24-07-PLAN.md — F-04: a recusa de tool passou a debitar a viagem que ela custou
- [x] 24-11-PLAN.md — achado ao vivo 2026-09-11: a LEITURA DO ATIVO diz por que cada campo vazio está vazio
- [x] 24-12-PLAN.md — achado ao vivo 2026-09-11: a tela diz a distância em pregões até o último fechado, em vez de herdar o SLA da fonte
- [x] 24-14-PLAN.md — achado ao vivo 2026-09-11: o ensaio diz quando não testou nada (janela que nunca fechou no histórico)
- [x] 24-15-PLAN.md — pedido do Alex 2026-09-11: limite da cota da aba Opções configurável pelo portal admin
- [x] 24-16-PLAN.md — achado 2026-09-12: chave própria (BYOK) destrava o gate mensal do plano, que media consumo da chave do servidor
- [x] 24-17-PLAN.md — pedido do Alex 2026-09-12: o plano da conta muda pelo portal admin (rota gated e auditada), em vez de edição direta no SQLite do container

**UI hint**: yes

Fora de escopo declarado: Fase 4 do PLANO (veredito), Fase 6 (fluxo do
iniciante, glossário, cobertura mobile) e a consolidação dos módulos puros
(ADR-027 Decisão 3 fixa o gatilho; esta fase entrega só o teste de paridade
que o dispara). Detalhes em
`.planning/phases/24-opcoes-mcp-analise-e-setups/24-CONTEXT.md`.

#### Phase 25: Planos comerciais — acesso por função e limites por plano — standalone
**Goal**: O plano da conta deixa de ser um rótulo com um único efeito e vira o
eixo que decide (a) quais funções do app a conta acessa e (b) o limite de cada
ponto de controle de IA — configurável no portal admin, visível para o usuário.
Junto, nasce o papel `owner`: todas as permissões, imune a revogação, ancorado
em e-mail.
**Depends on**: nada em código. Decisões do Alex de 2026-09-12 registradas em
`.planning/phases/25-planos-comerciais/25-CONTEXT.md` (D1 owner irrevogável por
defesa em profundidade; D2 RBAC = administração e plano = produto, com
`opcoes.criar_setup` migrando para o plano; D3 owner ignora só o cap comercial).
**Requirements**: ver 25-CONTEXT.md
**Success Criteria** (what must be TRUE):
  1. O contador que o gate comercial lê mede análise, e só análise — telemetria
     não desconta cota (medido no 25-01: 100% do ledger era telemetria).
  2. Cada ponto de controle de IA tem limite configurável POR PLANO, com
     precedência memória → kv → env → default e a origem visível no portal.
  3. Tetos FÍSICOS (teto global da chave do servidor, 2.000/dia do serviço MCP,
     cota da brapi) NÃO variam por plano — ADR-010, decisão 2.
  4. `owner` não pode ser revogado por rota nenhuma, e é reconcedido se
     escapar por outro caminho.
  5. Sem configuração, `free` e `pro` se comportam exatamente como hoje.
  6. O usuário vê em que plano está, e a recusa por limite diz qual limite bateu.
**Plans**: 6 previstos (um por fase do CONTEXT)

Plans:

**Wave 1**

- [x] 25-01-PLAN.md — conserta o contador antes de configurá-lo: telemetria para de descontar cota; guardião de `month_section` varre todo o app; `snapshot` não mistura baldes

**Ondas seguintes** *(cada plano é escrito quando a fase anterior informa a próxima)*

- [x] 25-02 — papel `owner` (D1)
- [x] 25-03 — catálogo de planos com limites e funções
- [x] 25-04 — gates leem o plano (D2, D3)
- [x] 25-05 — módulo de configuração no portal
- [x] 25-06 — plano visível no app (UI delegada a subagente de UX)

**UI hint**: yes

**Decisão pendente do Alex** (25-01): ativar o gate mensal em `/api/scan/deep`,
`/api/carteira-stopalvo` e `/api/assistente` — hoje elas CONTAM mas não são
barradas. O resíduo de telemetria já gravado só zera na virada do mês, então
ativar antes disso barraria por um defeito, não por uso. Recomendação do
executor: ativar junto com os limites configuráveis (25-03/25-04). O estado
pendente está codificado como `xfail(strict=True)` — no dia da ativação os
casos falham por XPASS e obrigam quem ativar a tirar a marca.

#### Phase 26: Otimização de UX e da camada de IA — standalone
**Goal**: Fechar a distância entre o que o app faz e o que ele diz que faz —
telas invisíveis para o assistente, texto que descreve produto inexistente, e
caminhos de menu mortos — sem adicionar funcionalidade nova.
**Depends on**: nada em código. Briefing e decisões do Alex de 2026-09-12 em
`.planning/phases/26-otimizacao-ux-ia/26-CONTEXT.md`.
**Requirements**: ver 26-CONTEXT.md
**Success Criteria** (what must be TRUE):
  1. Toda aba do `BottomNav` é conhecida por todos os registros de tela
     (assistente, tour, ajuda, snapshot do pet) — nenhuma responde 400 nem cai
     em fallback silencioso de outra tela.
  2. Pergunta coberta pelos 83 verbetes da KB é respondida sem depender da tela
     de origem, sem afrouxar allowlist.
  3. Todo texto de produto citado em prosa pelo backend aponta para um destino
     que existe, travado por guardião que deriva da fonte.
**Plans**: 1 executado; backlog (B2, B3, C1, C2, C3) registrado no CONTEXT

Plans:

**Wave 1**

- [x] 26-01-PLAN.md — Fase A: sete correções baratas e independentes (aba Opções visível ao assistente, KB antes da checagem de tela, tour cobrindo a tela de abertura, três textos mortos corrigidos)

**Ondas seguintes** *(cada plano é escrito quando a fase anterior informa a próxima)*

- [ ] B2 — preservar estado ao trocar de aba (sem decisão de abordagem)
- [ ] B3 — ligar a aba Opções às rotas de execução, com lastro obrigatório e flag opt-in para operação a descoberto (pesquisa concluída; decisão de escopo pendente)
- [ ] C1 — porta de busca para os 83 verbetes da KB
- [ ] C2 — ancorar verbete nas quatro abas sem cobertura
- [ ] C3 — consolidar os cinco registros paralelos de tela do front num ponto único

**UI hint**: yes

#### Phase 27: Aba Opções sobre a carteira — standalone
**Goal**: A aba Opções deixa de ser um consultor de tickers avulsos e passa a
operar sobre o que o usuário tem. O universo vira a carteira, os vigias
(setups) passam a existir fora do ticker que os criou, e a leitura técnica do
ativo chega de graça pelo motor determinístico do próprio app — reservando o
serviço externo de opções para o que só ele sabe (cadeia, vencimentos,
payoff), sob clique explícito e com custo declarado.
**Depends on**: Phase 24 (aba Opções sobre MCP) e Phase 26 (Fase A, que tornou
a aba visível ao assistente). Protótipo de UX aprovado pelo Alex em 2026-09-13.
**Requirements**: ver 27-CONTEXT.md
**Success Criteria** (what must be TRUE):
  1. Um setup gravado continua visível depois de sair e voltar à aba, sem que o
     usuário precise lembrar em qual ativo o criou.
  2. A aba nunca abre vazia para quem tem posição em carteira; para quem não
     tem, o estado vazio explica o porquê e oferece caminho.
     *(Leitura fixada em 2026-09-13: "não abre vazia" = tem CONTEÚDO — a lista
     das posições e o bloco "Seus vigias", os dois de custo zero. NÃO significa
     ativo pré-selecionado: selecionar um ativo dispara uma leitura de custo 3,
     e auto-selecionar violaria o critério 4 logo abaixo.)*
  3. Tendência, volatilidade e suporte/resistência do ativo aparecem sem
     consumir cota do serviço externo.
  4. Toda chamada que consome cota sai de clique explícito, com o custo visível
     no próprio controle (ADR-027 preservado neste ponto).
  5. O lastro livre aparece ANTES da tentativa de operar, não só na recusa.
**Plans**: 5 planos em 4 ondas

Plans:

**Wave 1**

- [x] 27-01-PLAN.md — índice de vigias por usuário, isolamento no armazém compartilhado do MCP e as duas rotas de listagem (custo 0 e custo 2); emenda à Decisão 7 do ADR-027

**Wave 2** *(paralelos — nenhum arquivo em comum)*

- [x] 27-02-PLAN.md — front: universo = carteira, ticker que não nasce vazio, bloco "Seus vigias" no topo, lastro livre no cartão, estado vazio com caminho
- [x] 27-03-PLAN.md — backend: ponte com o motor técnico interno (`opcoes_tecnico.py` + `GET /api/options/tecnico/{ticker}`), Emenda 2 ao ADR-027, assistente falando da aba sobre a carteira

**Wave 3**

- [x] 27-04-PLAN.md — front: bloco de leitura interna com carimbo, régua de regime de 7 pregões, formatador escolhido pela unidade declarada

**Wave 4**

- [x] 27-05-PLAN.md — front: custo declarado em TODO controle (tabela espelhada do `_cap_check`), leitura do serviço sob clique explícito, custo do frescor declarado no cabeçalho

**Nota de planejamento (2026-09-13):** eram 3 planos previstos; viraram 4. O
critério 4 ("custo visível no próprio controle") hoje é falso em sete dos oito
controles da aba, e a régua de 7 pregões do protótipo aprovado é componente
novo — os dois não cabiam no orçamento de contexto do plano de front sem
reduzir escopo, o que não é opção. A fronteira dos três planos originais foi
preservada: 27-03 continua sendo "ponte técnica + emenda ao ADR", e o 27-04 é a
metade de tela dele somada ao custo declarado.

**Revisão de 2026-09-13 (verificação adversarial):** viraram **5 planos em 4
ondas**. O custo declarado saiu do 27-04 para o **27-05** porque cresceu: além
de rotular os controles, ele passou a mover `mcpLeitura` para fora do
`useEffect` (hoje trocar de ativo gasta 3 chamadas sem controle nenhum dizer),
a declarar o custo do frescor no cabeçalho e a cruzar o rótulo do front com o
`_cap_check` de cada rota do backend — seis arquivos e um guardião não-trivial.
Somado às duas tasks que ficaram no 27-04, o plano passaria de 70% de contexto.
Nada foi reduzido: o escopo inteiro continua na fase. Também entrou uma Task 0
no 27-01 (provar, antes de qualquer código, que o serviço aceita um nome
prefixado) e caiu toda a complexidade de legado, por decisão do Alex
(27-CONTEXT, D6).

**UI hint**: yes

**Fora de escopo, explicitamente**: ligar a aba à execução de ordens (B3 da
Fase 26) — a regra de lastro obrigatório × flag de operação a descoberto
continua pendente de decisão e não entra aqui.

#### Phase 28: Sub-aba "Operar" e extração de `PropostaLastreada` — standalone
**Goal**: Toda operação lastreada (venda coberta, put de proteção, collar) que
hoje só existe dentro do card do ativo em Watchlist/Radar passa a existir
dentro da aba Opções, numa sub-aba nova ("Operar") — sem duplicar o
componente que já faz isso (`PropostaLastreada`), extraído para um módulo
compartilhado que os dois lados importam (nenhum dos dois importa do outro,
preservando o isolamento do ADR-027). A aba Opções ganha duas sub-abas:
"Setups" (o que a Fase 27 já entrega, intocado) e "Operar" (nova).
**Depends on**: Phase 27 (aba Opções sobre a carteira — universo, leitura
técnica) e Phase 17/19 (motor de proposta lastreada e multi-candidato,
`opcoes_lastreadas.py`/`store.py`, inalterados nesta fase).
**Requirements**: ver `28-CONTEXT.md`
**Success Criteria** (what must be TRUE):
  1. Abrir e fechar venda coberta, put de proteção e collar funciona a partir
     da sub-aba "Operar", sobre uma posição real da carteira — nenhuma rota
     nova, nenhuma mudança no motor determinístico (`opcoes_lastreadas.py`/
     `store.py`).
  2. O componente que renderiza a proposta (manchete do motor, payoff
     numérico — ganho máximo, perda máxima, breakevens —, CTA de abrir/
     fechar) existe em UM módulo só, importado por `App.jsx` e por
     `OpcoesScreen.jsx` — nenhum dos dois importa do outro (Emenda 3 ao
     ADR-027).
  3. O card de proposta lastreada dentro do `AtivoCard` (Watchlist/Radar) não
     existe mais — abrir/fechar por ali deixa de ser possível; o caminho
     passa a ser a aba Opções. A tira `OportunidadesOpcoes` em Posições
     (Fase 18) permanece intocada (não usa `PropostaLastreada` hoje, não
     depende desta extração).
  4. A sub-aba "Setups" continua idêntica ao que a Fase 27 entrega (vigias,
     leitura técnica, cadeia/possibilidades, criar/desativar setup) — zero
     regressão.
  5. Suíte canônica sem regressão da baseline medida no início da fase;
     `npx vite build` verde.
**Plans:** 3 plans

Plans:
**Wave 1**

- [x] 28-01-PLAN.md — extrai `PropostaLastreada`/`FonteDoDadoProposta`/`ChipDaProposta` + o caminho de aceite para `web/src/opcoes/PropostaLastreada.jsx`, reaponta `App.jsx` e os guardiões

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 28-02-PLAN.md — sub-abas "Setups"/"Operar" em `OpcoesScreen.jsx`, `SubAbaOperar` com a proposta lastreada da posição, chaves de copy nos dois modos e guardião novo

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 28-03-PLAN.md — remove o card de proposta do `AtivoCard` + código órfão, reaponta os 3 guardiões restantes, Emenda 3 ao ADR-027 e checkpoint de verificação ao vivo

**UI hint**: yes

**Checkpoint da Task 3 (28-03) fechado em 2026-09-13** por decisão explícita
do Alex ("Fechar agora"), aceitando risco residual nomeado: passos 4
(fechar lastreada de fato) e 5 (collar) do roteiro de 9 passos não foram
exercitados com o app rodando sobre dado real — só sob provider mock/
mercado forçado aberto, numa verificação feita pelo orquestrador. Os outros
7 passos (custo zero, abrir, CTA vira Fechar, Modo Estudo sem CTA, remoção
do card, Posições intocado, ticker persiste) foram confirmados com
evidência de rede e tela. Detalhe completo em `28-03-SUMMARY.md`.

**Fora de escopo, explicitamente**: opção a descoberto/naked (Fase 29, exige
o flag opt-in em Configurações que ainda não existe); curadoria de IA das 4
melhores estruturas (Fase 30); polish de UX pós-uso real (Fase 31).

**NÃO ESTÁ NO AR**: nenhum push a `origin`, nenhum `bump.sh`/
`publicar-web.sh`. Publicação é passo humano separado, fora do escopo desta
fase.

#### Phase 29: Opção a descoberto com flag opt-in — standalone
**Goal**: `buy_option`/`sell_option` (o caminho "a seco", hoje sem NENHUM
gate de lastro) passam a exigir um flag opt-in em Configurações para abrir
posição nova — lastro obrigatório continua sendo o padrão para toda conta,
sem exceção silenciosa. Fechar uma posição a seco já aberta nunca é
bloqueado pelo flag.
**Depends on**: Phase 28 (aba Opções com sub-abas Setups/Operar — não
tocada por esta fase, ver D2) e a decisão do Alex registrada em
`26-CONTEXT.md` (lastro obrigatório por padrão × flag opt-in).
**Requirements**: ver `29-CONTEXT.md`
**Success Criteria** (what must be TRUE):
  1. Conta nova nasce com o flag desligado — sem exceção, sem migração
     silenciosa de conta existente para "ligado".
  2. `buy_option` recusa abrir posição a seco quando o flag está desligado,
     com mensagem clara apontando para Configurações — recusa no backend,
     nunca só escondida na UI.
  3. Ligar o flag exige o mesmo padrão de fricção do Modo Operador (D1):
     termo de responsabilidade, leitura até o fim, checkbox, versão do
     texto registrada.
  4. `sell_option` (fechar posição a seco já aberta) nunca é bloqueado pelo
     flag, em nenhum estado.
  5. `OpcoesCamada` (Watchlist/Radar) continua sendo a UI da compra a seco
     nesta fase — sem migração para a sub-aba "Operar" (D2, fechada).
  6. Suíte canônica sem regressão da baseline medida no início da fase;
     `npx vite build` verde.
**Plans:** 3 plans

Plans:
**Wave 1**

- [x] 29-01-PLAN.md — backend: `permitirOpcaoADescoberto` + `descobertoTermo` em `config`, gate determinístico em `store.buy_option`, tradução 400 em `/api/options/buy`, e guardião (default off, fail-closed, `sell_option` nunca gateado)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 29-02-PLAN.md — espelho no `deviceStore`: os dois campos com a regra do servidor + sync, gate no ramo LOCAL de `optionsBuy` (o buraco do iOS sem sessão) com a mensagem byte a byte do backend, e guardião de paridade

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 29-03-PLAN.md — UI: termo de responsabilidade versionado (`TermoDescobertoModal`, fricção do Modo Operador reusada) + card "OPÇÕES A DESCOBERTO" em Preferências, guardião do fence D2, e checkpoint de verificação humana

**Baseline da suíte medida em 2026-09-13 (início da fase)**: pytest 2780
passed / 5 skipped / 3 xfailed; 144 arquivos `web/tests/*.mjs` todos `[OK]`;
exit 0.

**Checkpoint da Task 3 (29-03) fechado em 2026-09-13** por aprovação direta
do Alex, depois de um alarme falso investigado no caminho: ele reportou que
o card "OPÇÕES A DESCOBERTO" não aparecia; o orquestrador verificou o mesmo
servidor ativo (mesma conta, card presente) antes de aceitar qualquer
coisa, isolou a causa para o app NATIVO do iPhone não recompilado nesta
sessão (não é defeito — pendência de build/`cap sync` nomeada, fora de
escopo), pediu o roteiro completo na web com ênfase no passo 7 (desligar o
flag não pode bloquear fechar posição já aberta) e recebeu "aprovado"
direto e literal. Detalhe completo em `29-03-SUMMARY.md`.

**UI hint**: yes

**Fora de escopo, explicitamente**: migrar `OpcoesCamada` para a sub-aba
"Operar" (D2 — fase seguinte, sobre o gate já testado); abrir posição de
opção automaticamente pelo Operador IA (lastreada ou a descoberto — sem
precedente de código, não pedido); curadoria de IA das 4 melhores
estruturas (Fase 30); polish de UX pós-uso real (Fase 31).

**NÃO ESTÁ NO AR**: nenhum push a `origin`, nenhum `bump.sh`/
`publicar-web.sh`. Publicação é passo humano separado. **Pendência
operacional nomeada**: o app nativo (iPhone) não reflete esta fase até um
build novo ser gerado e instalado (`cap sync` + Xcode) — não bloqueia,
porque o gate é do servidor, não confia em UI nenhuma.

#### Phase 30: Curadoria de IA das 4 melhores estruturas — standalone
**Goal**: A aba/tela de Posições ganha um bloco novo, ao lado de
"Oportunidades de opções" (Fase 18), mostrando as 4 melhores propostas de
venda coberta da carteira inteira por razão prêmio/perda máxima — a
escolha das 4 é 100% determinística (`rastrear()`/`avaliar()`, já em
produção desde a Fase 15/16), a IA só narra o que o número já decidiu.
Custo ZERO do serviço MCP externo, por arquitetura (a cadeia vem do
`options_provider` mydata/Yahoo, nunca de `mcp.semente.dev`).
**Depends on**: Phase 15/16 (motor `rastrear()`/`avaliar()` e o payoff de
N pernas) e Phase 18 (`OportunidadesOpcoes`, o precedente de UI que este
bloco acompanha). Não depende das Fases 28/29 (sub-aba Operar e flag a
descoberto) — universo aqui é só venda coberta lastreada.
**Requirements**: ver `30-CONTEXT.md`
**Success Criteria** (what must be TRUE):
  1. As 4 estruturas mostradas são sempre as 4 de maior razão prêmio/perda
     máxima entre os candidatos elegíveis (vários strikes, um vencimento
     por posição, piso de liquidez `LIQUIDEZ_NEGOCIAVEL`) — nenhuma
     chamada a LLM decide OU reordena a lista.
  2. Nenhuma chamada nova ao serviço MCP externo (`mcp_client`/
     `options_mcp_api`) — toda leitura de cadeia usa `options_provider`
     já em produção, uma busca por posição elegível, igual ao fluxo de
     proposta única de hoje.
  3. A narração da IA sobre as 4 estruturas consome a MESMA cota mensal de
     `/api/analyze` (Fase 25) — sem orçamento paralelo, sem gate novo.
  4. Put de proteção, collar e qualquer estrutura via MCP NÃO entram no
     ranking desta fase (D1) — só venda coberta.
  5. Suíte canônica sem regressão da baseline medida no início da fase;
     `npx vite build` verde.
**Plans:** 4 plans (4 waves)

Plans:
- [ ] 30-01-PLAN.md — motor PURO: enumera vários strikes de venda coberta na cadeia já em memória, calcula prêmio/perda máxima e ordena o top-4 com desempate total (D1/D2/D3/D5)
- [ ] 30-02-PLAN.md — `GET /api/options/curadoria`: varredura cross-posição com UMA busca de cadeia por posição elegível, provada por guardião de contagem exata (SC-2)
- [ ] 30-03-PLAN.md — narração da IA sobre o top-4 já ordenado, sob o mesmo `_gate_analise` de `/api/analyze` (D6), incapaz de reordenar por construção
- [ ] 30-04-PLAN.md — bloco em Posições ao lado de "Oportunidades de opções" (D4), manchete verbatim do motor, narração rotulada e separada + checkpoint de verificação ao vivo

**UI hint**: yes

**Fora de escopo, explicitamente**: put de proteção e collar no ranking
(D1); estruturas via serviço MCP (D1); múltiplos vencimentos por posição
(D3 — a cadeia hoje só traz um; expandir exigiria chamada de rede nova,
não pedida aqui); estender a lista `candidatos` da Fase 19/28 (esta UI é
nova, não extensão da proposta única por posição); polish de UX pós-uso
real (Fase 31).

#### Phase 31: Varredura de oportunidades de opções — standalone
**Goal**: Estender a curadoria determinística de oportunidades de opções
(Fase 30) de "1 vencimento × 1 estrutura (venda coberta)" para "até 2
vencimentos × as 4 estruturas que o motor interno já executa" (venda
coberta, put de proteção, collar, opção a descoberto), sobre as posições
que o usuário já tem na carteira — mais responsividade mobile do
`PayoffChart.jsx`. A seleção de quais oportunidades aparecem continua 100%
determinística (`opcoes_motor.avaliar()`/`opcoes_curadoria.py`); a IA, se
aparecer, só narra.
**Depends on**: Phase 30 (base determinística a estender, não substituir)
e Phase 29 (gate `permitirOpcaoADescoberto`, intocado na execução; esta
fase introduz a primeira checagem do flag no momento da EXIBIÇÃO da
oportunidade, não só da execução).
**Requirements**: ver `31-CONTEXT.md`
**Success Criteria** (what must be TRUE):
  1. Varredura cobre até 2 vencimentos por posição elegível (o mais
     próximo + o segundo mais próximo publicado por
     `mydata_client.get_vencimentos`), nunca mais — custo declarado de até
     2× `get_options_chain` por posição elegível contra o orçamento
     medido do mydata (60/min · 2.000/dia).
  2. Varredura cobre as 4 estruturas do motor interno (venda coberta, put
     de proteção, collar, opção a descoberto) — não só venda coberta como
     a Fase 30.
  3. Oportunidade a descoberto só aparece na varredura para contas com
     `permitirOpcaoADescoberto = true` já ligado — sem exceção, sem aviso
     substituindo o gate.
  4. Ranking usa uma fórmula só (prêmio ÷ perda máxima) para as 4
     estruturas — sem seções separadas por objetivo.
  5. `PayoffChart.jsx` funciona corretamente em 375px (mobile) sem mudar a
     lógica de exibição (uma estrutura por vez, sem overlay).
  6. Varredura cobre só tickers com posição aberta na carteira do usuário
     — sem estender a watchlist/catálogo.
  7. Suíte canônica sem regressão da baseline medida no início da fase;
     `npx vite build` verde.
**Plans:** 4 plans (3 waves)

Plans:
**Wave 1**

- [ ] 31-01-PLAN.md — motor PURO: as 4 estruturas (venda coberta, put de proteção, collar, opção a descoberto) sobre a mesma cadeia em memória, prêmio líquido COM SINAL, `idCandidato`, `proximos_vencimentos()` e o gate de descoberta `permitir_a_descoberto` (D-04/D-05/D-06)
- [ ] 31-03-PLAN.md — `PayoffChart.jsx` legível em 375px: piso de tipografia no SVG, geometria com respiro, rótulos sem sobreposição; sem overlay e sem interatividade (D-07/D-08)

**Wave 2** *(blocked on Wave 1)*

- [ ] 31-02-PLAN.md — rota: até 2 vencimentos por posição elegível provado por contagem exata, meta `candidatosPorTipo`/`tetoVencimentos`, flag lido só da config do SERVIDOR (nunca do corpo), e cache de vencimentos no mydata (3 requisições/posição em vez de 4) (D-01/D-03/D-05/D-09)

**Wave 3** *(blocked on Wave 2)*

- [ ] 31-04-PLAN.md — bloco de Posições: rótulo de tipo, chave de render estável, resumo da varredura, curva de payoff do nº 1 via adaptador puro, guardiões atualizados + checkpoint de verificação ao vivo em 375px

**Consequência conhecida e aceita de D-06** (registrada no plano, não é
defeito): com uma fórmula só (prêmio líquido ÷ perda máxima), put de
proteção, collar de débito e opção a descoberto têm prêmio líquido NEGATIVO
e rankeiam abaixo de qualquer venda coberta — o top-4 pode ficar todo de
venda coberta. É por isso que a varredura publica `candidatosPorTipo`: a
cobertura das 4 estruturas (SC-2) e o gate do a descoberto (SC-3) ficam
verificáveis sem criar seção separada por objetivo, que D-06 proíbe.

**Fora de escopo, explicitamente**: watchlist/catálogo sem posição
(D-09); overlay de múltiplos candidatos e interatividade no payoff (D-08);
seções de ranking separadas por objetivo receita vs. proteção (D-06).

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
| 17. Fluxo de aceite | 5/6 | In Progress|  |
| 18. Aba Opções | 4/5 | In Progress|  |
| 19. Motor multi-candidato | 3/4 | In Progress|  |
| 20. Fundação estrutural e tipográfica | 4/4 | Complete    | 2026-09-05 |
| 21. Duplicação removida e Portfólio consolidado | 4/4 | Complete    | 2026-09-06 |
| 22. Componentes compartilhados (trilho, ícones, mascote) | 4/4 | Complete    | 2026-09-06 |
| 23. Motion com propósito e ilustração unificada | 4/4 | Complete    | 2026-09-06 |
| 24. Aba Opções sobre MCP — análise e criação de setups | 12/13 | In Progress|  |
| 25. Planos comerciais — acesso por função e limites por plano | 6/6 | Complete | 2026-09-12 |
| 26. Otimização de UX e da camada de IA | 1/6 | In Progress|  |
| 27. Aba Opções sobre a carteira | 5/5 | Code complete | 2026-09-13 |
| 28. Sub-aba "Operar" e extração de `PropostaLastreada` | 3/3 | Code complete | 2026-09-13 |
| 29. Opção a descoberto com flag opt-in | 3/3 | Code complete | 2026-09-13 |
| 30. Curadoria de IA das 4 melhores estruturas | 0/4 | Planned |  |
| 31. Varredura de oportunidades de opções | standalone | Context gathered |  |

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

Milestone em andamento: v1.4 Opções v2 (Phases 15-19, execução
represada por checkpoints humanos pendentes do Alex — Fases 17/18/19).
v1.5 Redesenho de UI (Phases 20-23) shipped em 2026-09-06 — ver
[milestones/v1.5-ROADMAP.md](milestones/v1.5-ROADMAP.md).
