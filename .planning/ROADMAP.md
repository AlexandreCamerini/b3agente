# Roadmap: Boris+ (b3-agente)

## Milestones

- ✅ **v1.0 Revisão Geral** — Phase 1 (shipped 2026-08-18) — [detalhes](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Realismo de Mercado + Correções** — Phases 2-8 (shipped 2026-08-23) — [detalhes](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Camada de opções ancorada na carteira** — Phases 0, 10, 11 (shipped 2026-08-28) — [detalhes](milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Cap comercial (plano gratuito)** — Phases 12-13 (shipped 2026-08-31) — [detalhes](milestones/v1.3-ROADMAP.md)
- 🚧 **v1.4 Opções v2** — Phases 15-19 (in progress)
- 🎨 **v1.5 Redesenho de UI — simplificação e acessibilidade** — Phases 20-23 (planned)

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

### 🎨 v1.5 Redesenho de UI — simplificação e acessibilidade (Planned)

**Milestone Goal:** eliminar a duplicação e as inconsistências visuais achadas
na auditoria de design ao vivo (mobile 375px, dark/light, Estudo/Operador,
conta nova + conta com ordem pendente) e aplicar uma direção visual mais
coerente — sem tocar no motor determinístico, sem reabrir a navegação de 5
abas, sem sair do Brand Book v2.

Numeração continua a partir da última fase do v1.4 (19, motor
multi-candidato) — Fases 20-23, sem `--reset-phase-numbers`. Os diretórios
de fase 15-19 permanecem intocados.

**Escopo técnico invariante das 4 fases:** nenhuma toca `server/app/*.py`,
nenhuma altera contrato de API, nenhuma muda cálculo de carteira/preço/
ordem/timing. Todo o trabalho vive em `web/src/` (estilo inline + tokens
`var(--x)`, sem Tailwind/shadcn — decisão travada no kickoff).

**Fatoração (por que estas 4 fases, nesta ordem):** a Fase 20 junta tudo que
é global e estrutural (contenção de overflow, teto de largura, escala
numérica, `tabular-nums`, `prefers-reduced-motion`, H1 em Fredoka) porque
essas mudanças mexem no shell/`GlobalStyle` e nos tokens que as três fases
seguintes consomem — fazê-las depois obrigaria a revisitar cada tela duas
vezes. As Fases 21 e 22 são independentes entre si e ambas só dependem da
20: a 21 é "remover/consolidar o que está duplicado" (mudança pontual,
verificável abrindo uma tela), a 22 é "unificar o que está divergente"
(componentes compartilhados por várias telas). A Fase 23 fica por último
porque MOTION-01/02 só fazem sentido depois do gate de `prefers-reduced-
motion` existir (Fase 20) e sobre os componentes já unificados (Fase 22), e
porque ILUS-01 depende de um asset novo (arte do Boris) que não bloqueia
nada mais do milestone.

**Risco de convivência com o v1.4:** as Fases 17/18/19 têm checkpoint humano
bloqueante pendente e nada foi enviado a `origin`; elas também editam
`web/src/App.jsx`. Cada fase do v1.5 deve rebasear/mergear sobre o estado
corrente do branch antes de publicar, e a publicação do front
(`scripts/bump.sh` → `scripts/publicar-web.sh`) empurra junto o trabalho
não-verificado do v1.4 no mesmo bundle — a decisão a/b/c registrada em
`STATE.md` Blockers vale também aqui.

#### Phase 20: Fundação estrutural e tipográfica
**Goal**: O esqueleto do app para de vazar horizontalmente, respeita um teto
de largura em tela grande, exibe número financeiro numa escala consistente e
alinhada, e obedece à preferência de movimento reduzido do sistema — a base
que as três fases seguintes consomem.
**Depends on**: Nothing (primeira fase do milestone)
**Requirements**: FIX-01, FIX-02, SYS-04, TYPO-01, TYPO-02, TYPO-03, MOTION-03
**Success Criteria** (what must be TRUE):
  1. Num aparelho de 375px, nenhuma tela do app rola para o lado: focar um
     campo ou tocar um item de um trilho horizontal nunca desloca header,
     conteúdo e barra inferior juntos (FIX-01 — hoje `scrollWidth` 504px vs.
     `clientWidth` 375px).
  2. A mensagem de status de mercado no topo trunca com reticência visível
     quando o texto não cabe, em vez de empurrar conteúdo para fora do
     viewport (FIX-02).
  3. Em janela ≥768px o conteúdo principal fica contido em 720px, alinhado
     com a barra inferior que já respeita esse teto — nada de texto
     edge-to-edge no desktop (SYS-04).
  4. Em qualquer lista de valores (Histórico, cards de Watchlist, Portfólio)
     os dígitos ficam alinhados em coluna, e todo valor financeiro na tela
     usa um dos três tamanhos nomeados (`numHero`/`numBody`/`numMicro`) —
     nunca um tamanho solto (TYPO-01, TYPO-02).
  5. Com "reduzir movimento" ligado no sistema operacional, nenhuma
     transição ou animação do app roda; e o H1 de cada tela aparece na fonte
     da marca (Fredoka), como o wordmark já faz (MOTION-03, TYPO-03).
**Plans**: 4 plans
Plans:
- [x] 20-01-PLAN.md — Contenção horizontal medida ao vivo, truncamento do badge e teto único de 720px (FIX-01, FIX-02, SYS-04)
- [x] 20-02-PLAN.md — Dígitos de largura fixa em todo valor com MONO + escala numérica nomeada (TYPO-01, TYPO-02)
- [x] 20-03-PLAN.md — Fredoka nos 15 H1 de tela + gate de prefers-reduced-motion (TYPO-03, MOTION-03)
- [x] 20-04-PLAN.md — Bump, publicação e remedição dos 5 critérios contra o bundle de produção
**Nota de publicação**: toca `web/src/` — a fase precisa de plano final de
`scripts/bump.sh` + `scripts/publicar-web.sh`, senão fica testada e
invisível em produção. Coberto pelo plano 20-04.
**Ressalva de escopo (critério 4)**: a metade "dígitos alinhados em coluna"
(TYPO-01) fecha nesta fase; a metade "todo valor financeiro usa um dos três
tamanhos nomeados" (TYPO-02) é deferimento explícito do `20-CONTEXT.md` para
as Fases 21/22, que migram tela a tela. A Fase 20 entrega as três constantes
com um consumidor real, não a migração do app inteiro.
**UI hint**: yes

#### Phase 21: Duplicação removida e Portfólio consolidado
**Goal**: O usuário para de ver a mesma informação duas vezes: a curva de
patrimônio existe em uma única tela, o status do Operador aparece uma vez
só, e os números do Portfólio viram um card denso — e o gráfico deixa de
mostrar caixa vazia quando ainda há pouco dado.
**Depends on**: Phase 20 (o card consolidado usa a escala numérica e o teto
de largura definidos lá)
**Requirements**: DEDUP-01, DEDUP-03, DEDUP-02, FIX-03
**Success Criteria** (what must be TRUE):
  1. O card "Patrimônio simulado" (curva de capital) aparece em exatamente
     uma tela do app — percorrer Acompanhar e Portfólio na mesma sessão não
     mostra duas cópias idênticas (DEDUP-01).
  2. Abrir Portfólio mostra um único card com patrimônio total, resultado
     aberto, caixa disponível e em posições em colunas, na mesma densidade
     do "Resumo do dia" de Acompanhar — não quatro cards empilhados
     (DEDUP-03).
  3. Na tela Operador IA, modo do app / operador no servidor /
     executar-sinalizar aparecem uma única vez, sem um card de texto
     repetindo o que o controle logo abaixo já mostra (DEDUP-02).
  4. Numa conta nova, logo depois da primeira operação (1-2 pontos de
     patrimônio registrados), a área do gráfico mostra um placeholder que
     diz que ainda faltam dados — nunca uma caixa vazia com escala
     degenerada (FIX-03).
**Plans**: 4 plans
Plans:
- [x] 21-01-PLAN.md — Curva de patrimônio única em Acompanhar + 4 cards do Portfólio consolidados em 1 grid 2×2 (DEDUP-01, DEDUP-03)
- [x] 21-02-PLAN.md — Card de status redundante removido do Operador IA, com link e transparência do ADR-017 realocados e 3 guardiões reescritos (DEDUP-02)
- [x] 21-03-PLAN.md — Limiar de 3 dias no CapitalCurve + placeholder de pouco dado nos dois modos (FIX-03)
- [x] 21-04-PLAN.md — Bump, publicação e remedição dos 4 critérios contra o bundle de produção
**Nota de publicação**: toca `web/src/` — precisa de plano final de bump +
`publicar-web.sh`. Coberto pelo plano 21-04.
**Nota de sequenciamento**: os 4 planos editam o MESMO `web/src/App.jsx`
(monolito de arquivo único) — ondas estritamente sequenciais, sem
paralelismo dentro da fase, mesmo padrão da Fase 20.
**Achado de planejamento (DEDUP-02)**: três guardiões existentes travam o
card que sai — `test_fase3_c19_card_status.mjs`,
`test_auditoria_status_strip.mjs` e o "Recorte 2" de
`test_historico_setup_card_ui.mjs`, dois deles com `process.exit(1)` em
marcador ausente. Pela regra do CLAUDE.md ("guardiões de teste não se
apagam"), o plano 21-02 os REESCREVE com nota datada de reversão em vez de
apagá-los. Nenhum artefato de fase (`21-UI-SPEC.md`/`21-PATTERNS.md`) tinha
visto isso.
**UI hint**: yes

#### Phase 22: Componentes compartilhados (trilho, ícones, mascote)
**Goal**: Os padrões que hoje divergem de tela para tela passam a ser um só:
um único comportamento de rolagem horizontal, ícones no traço do app no
lugar de emoji do sistema, e o mascote flutuante legível sobre qualquer
fundo.
**Depends on**: Phase 20 (o trilho unificado depende da contenção horizontal
do shell; independente da Phase 21)
**Requirements**: SYS-01, SYS-02, SYS-03
**Success Criteria** (what must be TRUE):
  1. Todo trilho horizontal do app (carrossel de setups da home, filtro
     "Modelo de análise" da Watchlist e qualquer outro) rola com snap e
     deixa o próximo item espiando — o usuário sempre percebe que existe
     mais conteúdo ao lado (SYS-01).
  2. Nenhum emoji do sistema operacional aparece na interface: os cinco usos
     de hoje (seletor de Modo no Perfil, card do Operador IA, chips de ação
     da Watchlist) mostram ícone SVG no mesmo traço da barra de navegação, e
     continuam legíveis nos dois temas (SYS-02).
  3. O mascote flutuante fica visualmente separado do conteúdo atrás dele em
     qualquer tela e nos dois temas — nunca parece cortado pela borda de um
     card (SYS-03).
**Plans**: 4 plans

Plans:
- [x] 22-01-PLAN.md — trilho horizontal único: helper `carouselTrackStyle`/`carouselItemStyle` e os 4 trilhos roteados por ele (SYS-01)
- [x] 22-02-PLAN.md — `NavIcon` generalizado + 8 emojis do Perfil/Watchlist/Posições/config viram SVG; 2 guardiões atualizados com nota (SYS-02)
- [x] 22-03-PLAN.md — Radar (ícone de varredura, ponto de tier, código morto) fecha a varredura de emoji em zero; sombra do PetFab vira token por tema (SYS-02, SYS-03)
- [x] 22-04-PLAN.md — bump + `publicar-web.sh` + suíte, e remedição dos 3 critérios no bundle de produção, incluindo a conferência visual da sombra nos dois temas (SYS-01/02/03)
**Nota de publicação**: toca `web/src/` — precisa de plano final de bump +
`publicar-web.sh` (plano 22-04).
**UI hint**: yes

#### Phase 23: Motion com propósito e ilustração unificada
**Goal**: O movimento passa a comunicar mudança de estado (card novo,
confirmação de ordem) em vez de existir por decoração, e o Boris tem um
único rosto em todo o produto.
**Depends on**: Phase 22 (e, por transitividade, Phase 20 — MOTION-01/02 só
podem entrar depois do gate de `prefers-reduced-motion` existir)
**Requirements**: MOTION-01, MOTION-02, ILUS-01
**Success Criteria** (what must be TRUE):
  1. Quando um setup inédito entra na Watchlist/Radar, o card aparece com
     uma transição curta (fade + subida, ~200ms) em vez de surgir sem aviso
     visual (MOTION-01).
  2. Ao confirmar uma compra ou venda, o valor dá um pulso curto (~120ms)
     antes de virar estado de sucesso (MOTION-02).
  3. Com "reduzir movimento" ligado, nem a entrada de card nem o pulso de
     confirmação animam — o estado final aparece direto, sem perda de
     informação (MOTION-01, MOTION-02 sob o gate da Phase 20).
  4. A arte do modal "Este é o Boris" está no mesmo estilo flat/cartoon do
     `LogoMark`/`PetFab`; lado a lado com o ícone do app, é reconhecível
     como o mesmo personagem (ILUS-01).
  5. O ícone do app já publicado (TestFlight/App Store) permanece
     inalterado — a troca de arte se limita ao modal de introdução
     (ILUS-01, guardrail do kickoff).
**Plans**: 4 plans (3 waves)
- [x] 23-01-PLAN.md — MOTION-01: entrada de card (fade + translateY 200ms) na Watchlist e no Radar, sob o gate de reduced-motion da Fase 20 [wave 1]
- [x] 23-02-PLAN.md — ILUS-01: ilustração flat nova (`web/src/pet/BorisFlat.jsx`) no modal "Este é o Boris", com guardião `test_boris_intro.mjs` atualizado [wave 1]
- [ ] 23-03-PLAN.md — MOTION-02: pulso de 120ms no valor da ordem EXECUTADA (pendente e rejeitada não pulsam), com portão `REDUCE_MOTION` em JS [wave 2]
- [ ] 23-04-PLAN.md — bump + `publicar-web.sh`, prova de bundle novo e remedição dos 5 critérios contra produção [wave 3]
**Nota de publicação**: toca `web/src/` e adiciona asset — precisa de plano
final de bump + `publicar-web.sh`.
**UI hint**: yes

Fora de escopo deste milestone (decidido no kickoff): mudança de arquitetura
de informação (fusão/reordenação de abas), migração de biblioteca de UI,
mudança de paleta/tokens do Brand Book v2, qualquer alteração no motor
determinístico ou em rotas de backend — ver `.planning/REQUIREMENTS.md`
Out of Scope / Future Requirements.

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
| 23. Motion com propósito e ilustração unificada | 2/4 | In Progress|  |

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

Milestones em andamento: v1.4 Opções v2 (Phases 15-19, execução
represada por checkpoints humanos) e v1.5 Redesenho de UI (Phases 20-23,
recém-roteirizado). Próximo passo do v1.5: `/gsd-plan-phase 20`.
