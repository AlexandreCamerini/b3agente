# Roadmap: Boris+ (b3-agente)

## Milestones

- ✅ **v1.0 Revisão Geral** — Phase 1 (shipped 2026-08-18) — [detalhes](milestones/v1.0-ROADMAP.md)
- 🚧 **v1.1 Realismo de Mercado + Correções** — Phases 2-7 (in progress)

## Phases

<details>
<summary>✅ v1.0 Revisão Geral (Phase 1) — SHIPPED 2026-08-18</summary>

- [x] Phase 1: Auditoria Diagnóstica Consolidada (6/6 plans) — completed 2026-08-18

</details>

### 🚧 v1.1 Realismo de Mercado + Correções (In Progress)

**Milestone Goal:** Fechar o gap entre o produto e um pregão real (status de
mercado visível, ordens fora de horário represadas) e corrigir os 2
Crítico + 8 Alto + 20 Médio achados do `REPORT-01.md` (v1.0).

**Phase Numbering:** continua a partir do fim de v1.0 (Phase 1). Fases
inteiras (2, 3, 4, 5) são trabalho planejado; fases decimais (2.1, 2.2)
seriam inserções urgentes, se necessário.

- [x] **Phase 2: Realismo de Mercado** - Status real de pregão na tela de entrada e fila de execução para ordens fora de horário (completed 2026-08-19)
- [x] **Phase 3: Correção Crítico + Alto** - Fecha as 2 violações de princípio (transparência de dado) e os 8 achados que já causaram incidente real ou bloqueiam decisão de negócio (completed 2026-08-19)
- [ ] **Phase 4: Correção Médio — Storyline & UX** - Fecha as lacunas pedagógicas e de experiência (STORY + UX) do REPORT-01
- [ ] **Phase 5: Correção Médio — Código, Gate & Admin** - Fecha a dívida técnica, a ativação incompleta de gating e a observabilidade admin (CODE + GATE + ADMIN) do REPORT-01
- [x] **Phase 6: Instrumentação de Assertividade (ADR-015)** - Conserta a medição de eficiência da IA (âncora errada, `n` inflado por duplicação, motivo de venda não persistido) antes de qualquer decisão de produto sobre o motor de recomendação (completed 2026-08-21)
- [x] **Phase 7: Seleção Dinâmica por Desempenho Histórico (ADR-017 Bloco 1)** - Ledger de sinais resolvidos, bootstrap, hook diário e `regime.ranquear()` passam a pesar cada setup pelo desempenho medido na janela anterior (completed 2026-08-21)

## Phase Details

### Phase 2: Realismo de Mercado

**Goal**: Usuário vê o status real do pregão a qualquer momento (mesmo antes
de logar) e pode colocar ordens fora do horário sem perder controle sobre
elas — preço, caixa e cancelamento ficam claros enquanto a ordem aguarda a
abertura seguinte.
**Depends on**: Nothing (usa `pregao.py`, já existente, como fonte única)
**Requirements**: MERC-01, MERC-02, MERC-03, MERC-04
**Success Criteria** (what must be TRUE):

  1. Usuário não-logado, na tela de entrada/home, vê o status real do
     mercado (aberto/fechado), calculado por `pregao.py` — hoje esse status
     só existe pós-login, na aba Operador.

  2. Ordem enviada fora do horário de pregão fica com status "pendente" (não
     é rejeitada nem executa ao preço do momento do pedido).

  3. Caixa da ordem pendente aparece reservado/indisponível assim que o
     pedido é feito, mas só é debitado do saldo real na execução.

  4. Ordem pendente executa automaticamente ao preço de abertura do pregão
     seguinte.

  5. Usuário pode cancelar uma ordem pendente a qualquer momento antes da
     execução, liberando o caixa reservado de volta ao disponível.
**Plans**: 7 plans
Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Motor determinístico de ordens pendentes (reserva de caixa/posição, cancelamento, execução)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — Rotas: status público de mercado + ramo pendente em /api/buy e /api/sell + cancelamento
- [x] 02-03-PLAN.md — Execução automática no scheduler_loop + contadores no status do servidor

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-04-PLAN.md — Cliente HTTP e os DOIS stores (paridade) + patrimônio com caixa reservado

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 02-05-PLAN.md — Badge de status de mercado na tela de login e no Topbar

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 02-06-PLAN.md — Modais com estado "mercado fechado", seção Pendentes e cancelamento em dois passos

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 02-07-PLAN.md — Exercício ponta-a-ponta, suíte canônica e verificação visual (checkpoint)

**UI hint**: yes

### Phase 3: Correção Crítico + Alto

**Goal**: As 2 violações de princípio (dado de mercado com proveniência
enganosa ou opaca) e os 8 achados Alto (erro cru vazando detalhe interno,
guardiões estruturais que não travam a classe do erro, gating comercial
inerte, kill-switches sem visibilidade operacional) deixam de ser risco
silencioso.
**Depends on**: Nothing (independente de Phase 2 — pode rodar em paralelo)
**Requirements**: FIX-C11, FIX-C30, FIX-C12, FIX-C19, FIX-C20, FIX-C31, FIX-C32, FIX-C35, FIX-C36, FIX-C37
**Success Criteria** (what must be TRUE):

  1. O painel técnico (`TechnicalModal`) mostra a fonte real do dado (brapi
     ou Yahoo, lida do payload), nunca a string fixa "Fonte: Yahoo Finance"
     independente da origem real. [FIX-C11]

  2. Quando o orçamento mensal da brapi passa de 80% (estado `degradado`,
     TTL 3x), usuário e admin veem um sinal explícito (timestamp/badge
     refletindo o dado mais velho), não silêncio total. [FIX-C30]

  3. Comprar/vender um ticker inválido devolve um erro limpo (502 com
     mensagem amigável), sem vazar URL ou parâmetro técnico interno do
     provedor de dados. [FIX-C12]

  4. A suíte de teste ganha um guardião genérico que falha em qualquer
     assimetria de método entre `deviceStore` e `serverStore` não
     documentada como intencional (fecha a classe de erro do bug histórico
     de paridade de stores). [FIX-C20] Um card de status único no topo de
     "Operador IA" resume os 3 interruptores que decidem se uma ordem
     dispara (Modo do app · Operador no servidor · Executar/sinalizar),
     mitigando o padrão-classe "estado que muda num lugar que outro não vê"
     por visibilidade — os outros 2 bugs históricos (blur salvando null,
     gatilho não propagado) continuam com guardião de sintoma apenas, por
     decisão explícita (fora do escopo desta fase). [FIX-C19]

  5. Uma conta com plano `'pro'` não é mais bloqueada pelos limites do plano
     gratuito — os hooks de gate (`can_add_ticker`/`can_analyze`) resolvem o
     plano real do usuário; `can_analyze` e `metering.check` deixam de
     contar a mesma cota de IA de forma duplicada/concorrente na mesma
     requisição. [FIX-C31, FIX-C32]

  6. O portal admin mostra o estado do 2º kill-switch (`timing_watch`), com
     toggle em runtime (sem depender de redeploy); o painel de custos passa
     a exibir `vazios`/`alerta`/`taxaFalha`, não só `erros`; um alerta
     "kill-switch ligado há N horas em horário de pregão" aparece na aba
     Automação. [FIX-C35, FIX-C36, FIX-C37]
**Plans**: 6 plans
Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Proveniência real e estado degradado no painel técnico (backend + app consumidor) [C-11, C-30]
- [x] 03-02-PLAN.md — Falha do provedor: erro limpo na cotação e visibilidade no painel de custos [C-12, C-36]

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-03-PLAN.md — Guardião genérico de paridade dos stores + card de status único no topo do Operador IA [C-20, C-19]
- [x] 03-04-PLAN.md — Gate comercial resolve o plano real da conta e passa a ter contador único [C-31, C-32]

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03-05-PLAN.md — 2º kill-switch (timing_watch): override em runtime, rotas admin e portal [C-35]

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 03-06-PLAN.md — Alerta ativo de "kill-switch ligado há N horas" + verificação humana da fase [C-37]

**UI hint**: yes

### Phase 4: Correção Médio — Storyline & UX

**Goal**: As lacunas pedagógicas (Passo 7/8 da jornada, diversificação,
transição de modo) e de experiência (disclaimer, estados de ordem,
acessibilidade) identificadas no REPORT-01 deixam de ser risco silencioso ao
Core Value.
**Depends on**: Nothing (independente de Phase 3 — pode rodar em paralelo)
**Requirements**: FIX-C01, FIX-C02, FIX-C03, FIX-C04, FIX-C05, FIX-C13, FIX-C14, FIX-C15, FIX-C16
**Success Criteria** (what must be TRUE):

  1. O Passo 7 (explicação educacional) sempre produz alguma explicação
     mínima determinística (via `conceitos.py`/`kb.py`) quando a IA não está
     disponível — nenhum usuário grátis sem chave fica sem explicação
     nenhuma. [FIX-C01]

  2. Toda ordem rejeitada (caixa insuficiente, sem cotação, ticker inválido)
     fica registrada com `status` e `motivo`, visível no histórico; o Passo
     8 mostra o retorno da carteira comparado a um índice real (Ibovespa),
     não só a curva isolada da própria carteira. [FIX-C02, FIX-C03]

  3. A transição Estudo→Operador exige um critério pedagógico mínimo de
     prontidão, além do aceite de termo legal; o conceito de diversificação
     passa a ser ensinado (verbete + aviso de concentração >50% num
     ativo). [FIX-C04, FIX-C05]

  4. O disclaimer de operação simulada renderiza no momento da decisão
     (`BuyModal`/`SellModal`), não só em outros pontos da tela; o estado
     "ordem parcialmente executada" é formalmente declarado (copy/doc) como
     fora do modelo — simulação é tudo-ou-nada por desenho. [FIX-C13,
     FIX-C14]

  5. O toggle "acordeão" responde a teclado (Enter/Espaço ativa); a cor
     `textFaint` atinge contraste mínimo WCAG AA (4.5:1) para texto pequeno,
     nos dois temas. [FIX-C15, FIX-C16]
**Plans**: TBD
**UI hint**: yes

### Phase 5: Correção Médio — Código, Gate & Admin

**Goal**: A dívida técnica (paridade `appMode`/prompt, cobertura de teste em
fluxos financeiros críticos), a ativação incompleta do gating comercial e a
observabilidade do portal admin deixam de depender de disciplina manual.
**Depends on**: Nothing (independente — as 11 correções são CODE/GATE/ADMIN
autocontidas; C33/C34 tocam o mesmo call site de C31/C32, mas como parâmetro
independente, não pré-requisito técnico — sequenciar depois de Phase 3 é só
preferência, não bloqueio)
**Requirements**: FIX-C21, FIX-C22, FIX-C23, FIX-C24, FIX-C25, FIX-C26, FIX-C27, FIX-C33, FIX-C34, FIX-C38, FIX-C39
**Success Criteria** (what must be TRUE):

  1. Os pontos de recomputação redundante de `appMode` em `App.jsx` passam a
     ler `ctx.operador`; o par `default_skill_text()`/`defaultSkillText()`
     ganha guardião de paridade byte-exata, no padrão do par
     `carteiraStopAlvo*`. [FIX-C21, FIX-C22]

  2. O toggle mestre "Entrada automática" ganha atributo HTML `disabled`
     real (não só lógica que impede o efeito) quando fora do Modo Operador,
     com feedback visual próprio. [FIX-C23]

  3. A suíte web roda de forma confiável num checkout/worktree novo (passo
     `npm install` documentado/automatizado antes da suíte canônica);
     rejeição de ordem em `/api/buy`/`/api/sell` (caixa insuficiente, sem
     cotação, ticker inválido) e recompra após venda parcial (preço médio
     reponderado) ganham teste de rota HTTP dedicado; cobertura E2E mínima
     para os fluxos financeiros críticos é avaliada. [FIX-C24, FIX-C25,
     FIX-C26, FIX-C27]

  4. `can_add_ticker`/`can_analyze` são chamados com o estado real do
     usuário (contagem do mês corrente), não dado hardcoded; um medidor de
     orçamento brapi (consumo × limite) fica visível ao usuário final,
     deixando claro que é consumo do app inteiro, não cota pessoal.
     [FIX-C33, FIX-C34]

  5. Um alerta preventivo dispara antes do teto global de gasto de IA (não
     só o hard stop já existente); a aba "Auditoria" do portal admin ganha
     campo `perm`, alinhando com o padrão visual das outras 9 abas.
     [FIX-C38, FIX-C39]
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 2 → 3 → 4 → 5. Todas as 4 fases de v1.1 são
tecnicamente independentes entre si (nenhuma tem pré-requisito técnico real
de outra) e podem ser planejadas/executadas em paralelo (`config.json`:
`parallelization: true`); a ordem numérica é só a sequência sugerida, não um
gate.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|-----------------|--------|-----------|
| 1. Auditoria Diagnóstica Consolidada | v1.0 | 6/6 | Complete | 2026-08-18 |
| 2. Realismo de Mercado | v1.1 | 7/7 | Complete   | 2026-08-19 |
| 3. Correção Crítico + Alto | v1.1 | 6/6 | Complete   | 2026-08-19 |
| 4. Correção Médio — Storyline & UX | v1.1 | 0/TBD | Not started | - |
| 5. Correção Médio — Código, Gate & Admin | v1.1 | 0/TBD | Not started | - |
| 6. Instrumentação de Assertividade (ADR-015) | v1.1 | 5/5 | Complete | 2026-08-21 |
| 7. Seleção Dinâmica por Desempenho Histórico (ADR-017 Bloco 1) | v1.1 | 6/6 | Complete | 2026-08-21 |

### Phase 6: Instrumentação de Assertividade (ADR-015)

**Goal**: A medição de eficiência da IA (`analysis_outcomes`) para de
fabricar stops e de inflar `n` por duplicação — o painel "Eficiência da IA"
passa a refletir o trade que o motor realmente propõe, não um trade
fantasma ancorado no close do dia da análise. Nenhuma mudança nesta fase
toca o motor de decisão em si (confluência, setup, plano operacional) nem
move cálculo para julgamento de IA — são todas correções de instrumentação,
conforme ADR-015 (Alternativa 1).
**Depends on**: Nothing tecnicamente (as 5 correções são independentes do
trabalho de Phase 4/5 — REPORT-01) — sequenciada depois de Phase 5 por
ordem de fila, não por bloqueio técnico.
**Requirements**: ADR15-01, ADR15-02, ADR15-03, ADR15-04, ADR15-05
**Success Criteria** (what must be TRUE):

  1. `analysis_outcomes.registrar` grava `entrada`, `alvo2`, `rr2`,
     `confluencia` e `entradaAMercado` no outcome do N1 (`main.py`), e
     `confluencia` no outcome do N2 — o N2 não tem plano determinístico em
     escopo e por isso não carrega geometria de gatilho. [ADR15-01]

  2. `_avaliar_entry` só abre a barreira tripla depois de o gatilho ser
     tocado — exceto no plano `a mercado` (`ancora='mercado'`, campo
     `entradaAMercado: true`), cuja entrada é imediata: ali a barreira abre no
     candle 0, sem exigir toque, para que o gap adverso do candle seguinte
     continue no denominador em vez de virar `sem_gatilho`. Usa `entrada` (não
     `close`) como preço de referência nos dois casos, e carimba no campo
     `ancora` (`gatilho`\|`mercado`\|`preco`) a âncora que de fato resolveu cada
     registro. Outcomes gravados antes da mudança ficam marcados como
     não-comparáveis (campo de versão de metodologia) e
     `compute_stats`/`compute_stats_all_users` não misturam as duas
     metodologias — nem as duas âncoras — no mesmo agregado. [ADR15-02]

  3. `compute_stats_all_users` deduplica registros pelo mesmo `snapshotId`
     antes de agregar — um plano gravado N vezes conta como 1 observação.
     [ADR15-03]

  4. `store.sell()` aceita `motivo` com o mesmo contrato de `sell_option()`
     (`'manual'|'stop'|'alvo'|'vencimento'`); o ÚNICO call site automático de
     `store.sell` em `agent.py` (linha ~852) passa o motivo real
     (`breach_stop`/`hit_alvo`) — os demais call sites (`pending_orders.py`,
     rota `/api/sell`) são vendas pedidas pelo usuário e ficam no default
     `'manual'`. [ADR15-04]

  5. Existe uma única constante-fonte para o R:R mínimo (`skill_ref.RR_MIN`);
     `setups.RR_MINIMO`, `agent.RR_MINIMO` e os literais do front
     (`copy.js`, `catalog.js`, `App.jsx`) leem dela, e um teste guardião
     cruzado falha se qualquer um divergir. [ADR15-05]
**Plans**: 5 plans (3 waves)
Plans:
**Wave 1**

- [x] 06-01-PLAN.md — `registrar()` grava entrada/alvo2/rr2/confluencia + versão de metodologia (ADR15-01)
- [x] 06-04-PLAN.md — `store.sell()` ganha `motivo`, em paridade com `sell_option()` (ADR15-04)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 06-02-PLAN.md — `_avaliar_entry` exige toque no gatilho e ancora o R-multiple em `entrada` (ADR15-02)
- [x] 06-05-PLAN.md — `RR_MIN` numa fonte única por camada + guardião de teste cruzado (ADR15-05)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 06-03-PLAN.md — agregado não mistura metodologias e deduplica por `snapshotId` (ADR15-02, ADR15-03)

**UI hint**: no (mudança de backend/instrumentação — sem tela nova; o
número exibido no painel "Eficiência da IA" muda, mas o componente não)

### Phase 7: Seleção Dinâmica por Desempenho Histórico — ledger de sinais resolvidos, bootstrap, hook diário, elegibilidade por setup em regime.ranquear (ADR-017, Bloco 1)

**Goal:** O motor de decisão passa a pesar cada setup pelo desempenho que ele
de fato teve — ledger de sinais resolvidos no banco principal, carga histórica
manual, manutenção diária incremental sem custo extra de brapi, e
`regime.ranquear()` consumindo elegibilidade por janela anual fechada
(`min_n=40`). Backend puro; a interface do histórico é o Bloco 3, fase futura.
**Requirements**: ADR17-B1, ADR17-B1-01..07
**Depends on:** Phase 6
**Plans:** 6/6 plans complete

Plans:

- [x] 07-01-PLAN.md — `signal_replay.py` (fonte única do replay determinístico) + guard de granularidade do Yahoo para todos os intervalos + `backtest_sinal.py` vira wrapper fino
- [x] 07-02-PLAN.md — tabela `signal_ledger` no banco principal, gravação idempotente, as duas agregações SQL (cumulativa e por janela) e o provedor de histórico com cache em processo
- [x] 07-03-PLAN.md — bootstrap manual (`python -m app.signal_ledger_bootstrap`, executável dentro do container) + runbook em `docs/OPERACAO-ledger-de-sinais.md`
- [x] 07-04-PLAN.md — `candle_cache.peek()` + hook diário incremental (`signal_ledger_job`) com fechamento de janela anual alinhado ao calendário da B3
- [x] 07-05-PLAN.md — `detect_setups` anexa `historico` (provedor injetado, sem I/O) e `regime.ranquear` usa `elegivel` no `radarScore` e na ordenação
- [x] 07-06-PLAN.md — fiação: hook no `scheduler_loop`, provedor ligado no boot, adendo no ADR-017 e verificação AO VIVO em produção (checkpoint)

### Phase 8: Interface e IA da Seleção Dinâmica — vocabulário novo (skill_ref.py/copy.js), telas do Radar/Watchlist/Operador mostrando histórico medido por setup, religa entradaAuto do Modo Operador gated pela elegibilidade (ADR-017, Bloco 3/4)

**Goal:** O histórico medido pelo Bloco 1 (elegibilidade, expectância por
janela, amostra) ganha vitrine — vocabulário canônico por modo, Radar/
Watchlist/card de setup mostrando o dado que já chega no JSON — e a entrada
automática do Modo Operador volta a existir, mas só para o setup específico
que a seleção dinâmica mediu como positivo, nunca mais uma suspensão cega.
**Requirements**: ADR17-B34-01, ADR17-B34-02, ADR17-B34-03, ADR17-B34-04
**Depends on:** Phase 7
**Plans:** 3/5 plans executed

Plans:
**Wave 1**

- [x] 08-01-PLAN.md — vocabulário canônico dos 6 estados do histórico medido em `skill_ref.py`, espelho byte-idêntico em `copy.js` e guardião cruzado
- [x] 08-02-PLAN.md — `_avaliar_entradas` troca a suspensão cega pelo gate de elegibilidade (`historico_snapshot`, só `elegivel is True` passa) + Adendo 2 no ADR-017

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 08-03-PLAN.md — derivação pura dos estados em `finance.js`, componente `HistoricoPill` e consumo de `setupElegivel`/`setupHistorico` no Radar e na Watchlist

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 08-04-PLAN.md — histórico por setup na lista do card (4 estados completos, aposentado rotulado) e linha de transparência do gate no card de status do Operador

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 08-05-PLAN.md — build/carimbo/publicação e checkpoint humano bloqueante antes do deploy do religamento gated
