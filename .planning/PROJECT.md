# Boris+ (b3-agente)

## What This Is

Simulador educacional de ações da B3 com dados reais de mercado e dinheiro
exclusivamente virtual. Ensina a mecânica da bolsa brasileira — setups,
indicadores, gestão de risco — através de um Modo Estudo (a IA orienta, nunca
executa) que evolui para um Modo Operador (ferramentas automáticas e análises
mais profundas, com execução simulada, agora **gated pela seleção dinâmica**:
entrada automática só dispara em setup com vantagem estatística medida na
janela anterior fechada, não mais em qualquer padrão detectado). Web/PWA +
app iOS nativo (mesmo bundle via Capacitor), backend Python/FastAPI, portal
de administração separado. **Comercializado desde v1.3**: plano gratuito com
teto real (10 ativos na watchlist, 30 análises de IA/mês, motivo exato na
recusa), plano pago (`PLAN_PRO`) ilimitado — ainda sem loja/IAP nem preço
definido, essa ativação foi só a preparação técnica pro upgrade pago.

## Core Value

O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado
funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem
acesso a automações do Modo Operador. Se o storyline pedagógico não convencer,
nada mais no produto importa.

## Current Milestone: v1.5 Redesenho de UI — simplificação e acessibilidade

**Goal:** eliminar a duplicação e as inconsistências visuais achadas numa
auditoria de design ao vivo (mobile 375px, dark/light, Estudo/Operador,
conta nova + conta com ordem pendente) e aplicar uma direção visual mais
coerente — sem tocar no motor determinístico, sem reabrir a navegação de 5
abas, sem sair do Brand Book v2 já aprovado.

**Contexto de abertura:** este milestone abre com o v1.4 (Opções v2) ainda
EM EXECUÇÃO — Fases 17/18/19 têm checkpoint humano bloqueante pendente
(depende de mercado aberto + posição real elegível, ver
`.planning/notes/checkpoints-pendentes-fase-17-18-19.md`). Decisão explícita
do Alex (04-05/09/2026): não esperar esse checkpoint fechar para começar a
planejar o v1.5 — os diretórios de fase 15-19 permanecem intocados
(`phases.clear` não foi executado), e nenhum push para `origin` foi feito em
nenhum dos dois fluxos. Um bug crítico achado durante a auditoria (`cp is
not defined` em `HistoricoScreen`) já foi corrigido e verificado ao vivo à
parte, via quick task `260905-1gb` (fora do escopo deste milestone).

**Target features (derivadas da auditoria + das decisões de design já
aprovadas nesta sessão):**
- Remover duplicação literal: `CapitalCurve` (card "Patrimônio simulado")
  aparece hoje em Acompanhar E Portfólio; card de status do Operador IA
  duplica o que o toggle abaixo já mostra
- Consolidar os 3 cards soltos do Portfólio (Patrimônio total/Resultado
  aberto/Caixa disponível) num único card com colunas, no padrão que
  "Resumo do dia" já usa em Acompanhar
- Unificar os dois padrões de carrossel horizontal (scroll-snap+peek vs.
  overflow simples sem affordance) num componente só
- Substituir os 5 ícones de emoji (🎓/📈/🚀/✨/📈) por SVG no traço do
  `NavIcon` existente
- Corrigir a contenção horizontal do `.b3-shell` (raiz do app rola pro lado
  além do viewport — achado crítico de responsividade) e aplicar
  `maxWidth:720px` ao conteúdo em telas largas (o `BottomNav` já faz isso)
- Tratar o estado "1-2 pontos de patrimônio registrados" no gráfico
  (`CapitalCurve`), que hoje renderiza uma caixa vazia em vez de um
  placeholder dedicado
- Tipografia: `tabular-nums` no stack MONO, escala numérica nomeada
  (`numHero`/`numBody`/`numMicro`), fonte Fredoka estendida para o H1 de
  cada tela (hoje só no wordmark)
- Motion com propósito: entrada de card novo (setup inédito), pulso de
  confirmação de ordem, `prefers-reduced-motion` (hoje ausente)
- Unificar a ilustração do Boris num único estilo (flat/cartoon, o do
  `LogoMark`/`PetFab`/ícone do app já publicado) — refazer só a arte do
  modal de introdução, que hoje é quase-fotorrealista
- `PetFab` (mascote flutuante) ganha sombra/halo para não parecer cortado
  contra a borda dos cards atrás dele

**Decisões de arquitetura travadas (não reabrir):**
1. Navegação de 5 abas (Acompanhar/Radar/Watchlist/Portfólio/Operador IA)
   permanece — Nível 1 "toque leve" escolhido explicitamente sobre as
   alternativas de consolidar/fundir abas (reabriria o funil canônico da
   FASE 2, validado com mockup e `navigation-specialist`)
2. Sem migração de stack: o app continua em React com estilo inline +
   tokens `var(--x)` (`PALETTE`/`MODE_OPERADOR`, `App.jsx:61-172`) — nada de
   Tailwind/shadcn, que exigiria reescrever ~9k linhas sem ganho declarado
3. Estilo de ilustração do Boris = flat/cartoon (não o quase-fotorrealista do
   modal de intro) — menor risco, não mexe no ícone do app já publicado no
   TestFlight/App Store

**Fora de escopo (decidido no kickoff):** qualquer mudança de arquitetura de
informação (fusão/reordenação de abas); migração de biblioteca de UI;
mudança de paleta/tokens do Brand Book v2; qualquer alteração no motor
determinístico ou nas rotas de backend — este milestone é puramente de
front-end visual/interação.

## Milestone v1.4 Opções v2 (EM EXECUÇÃO — não shipped)

**Goal:** nova experiência de Opções no Boris+ que propõe setups (venda
coberta, put de proteção, collar) a partir da análise técnica sobre posições
reais da carteira, com aceite manual do usuário — independente do MCP
externo (b-mcp, projeto paralelo) até ele ficar pronto.

**Target features:**
- Tira "Oportunidades de opções" no topo de Posições/Portfólio + detalhe
  completo dentro de cada posição — sem aba nova na navegação inferior
  (Candidato A revertido em 03/09: a barra real tem 5 abas, não 4; ver
  `.planning/ROADMAP.md` Phase 18 e `.planning/notes/opcoes-v2-b-mcp-exploracao.md`)
- Biblioteca v1: venda coberta + put de proteção + collar, só sobre posições
  com cobertura real (sem opção nua)
- Motor de proposta com critério de seleção `liquidity_score ≥ 40` + strike
  extremo (mantém a régua já em produção da Fase 14, não adota o critério
  por delta do b-mcp)
- Matemática de payoff (custo líquido, ganho/perda máximos, breakeven, delta
  somado) portada por cópia de `calculos.py` do b-mcp
- Limite/interface interno `rastrear()`/`avaliar()`, no vocabulário do
  contrato ADR-004/`mydata_client.py` — pronto pra trocar por chamadas MCP
  reais quando `plano-mcp-servico.md` for aprovado, sem redesenho
- Fluxo de aceite reusa o motor de ordens de opções lastreadas da Fase 14 —
  nenhuma automação nova

**Fora de escopo (decidido no kickoff):** plano comercial (gratuito vs.
pago) desta feature — mesmo padrão do v1.3, que ativou infraestrutura sem
loja/IAP ainda; DSL de setups técnicos (`setups.py` do b-mcp) — risco de
sinal já corrigido uma vez (ADR-016/017), gatilho já vem do Radar do Boris;
integração MCP de verdade (Estratégia C) — fica pro próximo milestone que
tratar disso, condicionado à aprovação do `plano-mcp-servico.md`.

Base completa da decisão: `.planning/seeds/opcoes-v2-setups-propostos-via-b-mcp.md`
e `.planning/notes/opcoes-v2-b-mcp-exploracao.md`.

## Milestone v1.3 Cap comercial (plano gratuito) — SHIPPED 2026-08-31

**Goal:** ativar de verdade os limites do plano gratuito que o ADR-010 já
desenhou tecnicamente (watchlist e análises/mês) — sem loja/IAP neste
milestone. `PLAN_PRO` continua ilimitado por enquanto; isso é preparação
pro upgrade pago, não a venda em si.

**Target features:**
- `PLAN_FREE.max_watchlist = 10` (hoje `None` = ilimitado)
- `PLAN_FREE.max_analyses_per_month = 30` (hoje `None` = ilimitado)
- `can_add_ticker`/`can_analyze` (`server/app/plan.py`) passam a bloquear de
  verdade quando o limite bate, com o motivo exato já pronto nos hooks
- `used_this_month` do gate mensal vem do ledger real de `metering.py`
  (contrato C-33 já exige isso — nunca um contador paralelo)
- UI mostra o número real de uso/limite (ex.: "análises deste mês: 30/30"),
  nunca estimado nem escondido (princípio 3/8 do CLAUDE.md)

**Decisões de arquitetura travadas (não reabrir):**
1. Cap comercial (por conta) e cota física da brapi (por app inteiro) são
   camadas independentes — um usuário pago consome da mesma cota física,
   só sem limite comercial próprio (ADR-010, decisão 2)
2. Fonte de cotação (brapi/Yahoo) não é diferencial de plano — infra igual
   pra todo mundo (ADR-010, decisão 3)

**Fora de escopo (decidido no kickoff):** loja/IAP e validação de recibo
server-side; IA gerenciada sem BYOK como feature paga; alvo dinâmico (F3)
virar exclusivo do pago; preço/moeda. Tudo isso fica pra um milestone
futuro, quando a decisão de venda em si vier.

Ver `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` e
`docs/adr/010-planos-e-cap-gratuito.md` (decisão técnica já fechada, só
faltavam os números).

## Requirements

### Validated

- ✓ Motor de simulação determinístico (ordens, preço médio, PnL, drawdown)
  server-side em `server/app/store.py`, mirror client-side em
  `web/src/finance.js`/`persistence.js` para uso offline — existing
- ✓ Camada de dados de mercado com fonte declarada e fallback (brapi master,
  Yahoo backup/intraday, ADR-001/ADR-008) — existing
- ✓ Separação Modo Estudo/Modo Operador via flag `appMode`, com vocabulário
  próprio por modo (`skill_ref.py` ↔ `copy.js`) — existing, fonte única
  reforçada em v1.1 (`ctx.operador`, FIX-C21)
- ✓ IA multi-provider (Anthropic/OpenAI/Google, BYOK + gerenciada com cota),
  camada didática que explica indicador→correlação→decisão — existing
- ✓ Autenticação multi-método unificada numa única conta (Sign in with Apple,
  Google, e-mail/senha) — existing
- ✓ RBAC/entitlements (ADR-013) e portal de administração/observabilidade
  separado (`web-admin/`, ADR-014, handoff mobile) — existing
- ✓ Estrutura técnica de planos (`plan.py`, `metering.py`) pronta para ligar
  cap comercial — v1.1 fechou o último buraco estrutural (FIX-C33, contagem
  real do mês); só falta a decisão de negócio (ADR-010) pra ativar de vez
- ✓ Cap comercial ativado de ponta a ponta (v1.3, Fases 12-13): `PLAN_FREE`
  com `max_watchlist=10`/`max_analyses_per_month=30` reais (eram `None`),
  gates `can_add_ticker`/`can_analyze` bloqueando de verdade com motivo
  exato (CAP-01..05, CAP-07), uso/limite real visível na UI nos dois stores
  — web e iOS (CAP-06), e o bypass do cap no app iOS nativo fechado
  (CAP-12/CR-01) — achado próprio: o code review pós-fase pegou o gate
  fail-closed comparando a contagem do SERVIDOR em vez da do APARELHO
  (iOS é local-first, nunca sincroniza watchlist pro servidor), corrigido e
  mutation-tested (`101335e`). CAP-12 já vale para builds NOVOS; instalações
  existentes via TestFlight só recebem o fix num build novo distribuído
  pelo Alex (pendência nomeada, não escondida, `13-05-SUMMARY.md`)
- ✓ REVIEW-01..06 / `REPORT-01.md` (39 achados, 2 Crítico + 8 Alto + 20 Médio
  + 9 Baixo) — v1.0
- ✓ MERC-01..04: status real de mercado na tela de entrada + fila de
  execução de ordens fora do horário de pregão — v1.1 Fase 2
- ✓ FIX-C11, FIX-C30 (2 Crítico) + FIX-C12, C19, C20, C31, C32, C35, C36, C37
  (8 Alto) — v1.1 Fase 3
- ✓ FIX-C01..C05, C13..C16 (9 Médio — STORY/UX: fallback determinístico do
  Passo 7, rastro de rejeição, benchmark Ibovespa, prontidão pedagógica,
  diversificação, disclaimer no modal, tudo-ou-nada declarado, acordeão por
  teclado, contraste WCAG AA) — v1.1 Fase 4
- ✓ FIX-C21..C27, C33, C34, C38, C39 (11 Médio — CODE/GATE/ADMIN: fonte
  única de `appMode`, paridade byte-exata de skill text — achou e corrigiu
  divergência REAL de persona entre iPhone e web —, Toggle disabled real,
  suíte autossuficiente, testes de rejeição/reponderação, avaliação de E2E
  via ADR-018, contagem mensal real do gate, alerta preventivo de gasto de
  IA, regra de acesso explícita da aba Auditoria) — v1.1 Fase 5
- ✓ ADR-015 (instrumentação de assertividade): âncora no gatilho real (não
  mais no close), dedup por `snapshotId`, `motivo` em `store.sell()`, R:R
  mínimo consolidado numa fonte única — v1.1 Fase 6 (nasceu de pesquisa
  ad-hoc, não do REPORT-01)
- ✓ ADR-016 (diagnóstico, sem código): motor de setups tinha expectância
  negativa (−0,105R/operação, 15 anos, 125.938 sinais) — achado que motivou
  as Fases 6-8
- ✓ ADR-017 Bloco 0+1 (seleção dinâmica): 6 setups catastróficos aposentados
  (estático, piso de segurança), ledger de sinais resolvidos + bootstrap +
  hook diário + `regime.ranquear()` pesando por elegibilidade medida na
  janela anterior — v1.1 Fase 7
- ✓ ADR-017 Bloco 3+4 (interface): vocabulário canônico do histórico medido,
  Radar/Watchlist/card de setup mostrando elegibilidade, `entradaAuto`
  religado mas GATED pela elegibilidade (nunca mais suspensão cega nem
  "qualquer padrão detectado") — v1.1 Fase 8
- ✓ ADR-020 (centralização de dados no mydata): `mydata_client.py` +
  `mydata_budget.py` (cota 60/min·2.000/dia), fatia diária de candle
  atrás de cadeia mydata→brapi→Yahoo, opções/IV atrás de
  `options_provider_mydata.py` (D-04, sem fallback pro Yahoo), ingestão
  paralela de COTAHIST (`b3_historical.py`) aposentada (commit `b3fdf02`
  recuperável). Rate-limit MEDIDO (não estimado): pico projetado NÃO CABE
  (148/60 por minuto), volume diário CABE com folga — virada de
  `B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER` para mydata em produção
  **adiada** por decisão do Alex no checkpoint da fase, código pronto
  atrás das env vars — Fase 9 (standalone, fora de v1.0/v1.1)
- ✓ LEDGER-01/OPTGATE-01 (precondições do v1.2): 9 tickers 404 do bootstrap
  do ledger resolvidos com evidência (2 `ALIASES` por renomeação real, 5
  `EXCLUIR` por fusão/deslistagem, 2 `INDETERMINADO` documentados sem
  esconder); gate de orçamento (`_gate`/`_debita`) adicionado ao caminho de
  opções do mydata, refusal hard (nunca soft-pass, decisão A-05) — Fase 0
  do v1.2, execução autônoma noturna, 1 Crítico achado e corrigido em
  code review (CR-01, chave do ledger não-normalizada)
- ✓ PUT-01/02/03 (ponte gatilho→put, v1.2): hook diário no `scheduler_loop`
  (mesmo padrão de `signal_ledger_job`) cruza gatilho de setup × `positions`
  do usuário, triagem determinística da put de proteção com dados reais do
  hub (`estilo_exercicio`/strike/IV nunca assumidos), grava em tabela nova
  `put_suggestions` (long-only por CHECK constraint, isolada de
  `signal_ledger`/ADR-017 por desenho) com proveniência. **Dormente em
  produção por desenho**: `B3_OPTIONS_PROVIDER=yahoo` (default, intocado)
  não expõe `estilo_exercicio`, então a triagem sempre zera até a virada da
  Fase 9 acontecer — ver `docs/adr/021-ponte-gatilho-put.md`. Zero
  superfície visível (guardião dedicado). 2 Warnings achados e corrigidos
  em code review (WR-01 ticker malformado abortava o dia inteiro; WR-02
  strike não-positivo) — Fase 10 do v1.2, execução autônoma noturna
- ✓ PUTLIFE-01/02/03/04 (ciclo de vida, v1.2): máquina de 5 estados
  (`armada`/`expirada_sem_uso`/`executada_simulada`/`monitorada`/`fechada`)
  vivendo inteiramente em colunas novas de `put_suggestions` — nunca toca
  `optionPositions`/`cash`/`history` reais (provado por teste comportamental
  que monta carteira real e compara JSON byte a byte antes/depois de um
  ciclo completo). `intrinseco()` delega pra `agent.intrinseco_opcao`
  (ADR-005 real, sem fórmula paralela). Hook diário roda mesmo com
  kill-switch ligado — é medição, nunca execução de ordem (decisão do
  executor, override do desenho literal do ROADMAP, ver ADR-022). 0
  Crítico, 2 Warnings de baixo impacto deixados para sua decisão (ver UAT
  abaixo) — Fase 11 do v1.2, execução autônoma noturna, ÚLTIMA fase do
  milestone

### Active

- [ ] Item 8 do checkpoint 08-05: verificação ao vivo da entrada automática
  gated por um pregão inteiro (`entradaAuto` ligado, confirmar que só
  dispara nos setups elegíveis do momento) — depende do Alex ligar a
  feature numa conta de teste
- [ ] 2 human-check da Fase 3 nunca confirmados ao vivo (card de status 3
  badges reativo; mensagem de "sem permissão" no kill-switch pra conta sem
  `execucao_automatica.controlar`) — ver `03-VERIFICATION.md`
- [ ] Backlog (não mapeado a fase ainda): os 9 achados Baixo do REPORT-01
  (C-06..C-10, C-17, C-18, C-28, C-29)
- [ ] `textDim` do tema claro também reprova contraste WCAG AA (4.20:1) —
  achado colateral da Fase 4 (fora do escopo do C-16 original), candidato a
  backlog
- [ ] CAP-12 (bypass do cap de watchlist no iOS) está fechado em código e
  testado desde a Fase 13, mas só passa a valer nos aparelhos que já têm o
  app instalado depois de um build novo distribuído via TestFlight — ação
  sua (`scripts/ios-bump-build.sh` → `scripts/ios-testflight.sh` →
  archive/upload no Xcode, ver `TESTFLIGHT.md`). Você também sinalizou
  interesse em liberar pra testers externos (amigos) antes de qualquer
  submissão à App Store pública — passos documentados em `TESTFLIGHT.md`
  §6 (grupo externo, Beta App Review, Public Link)

### Out of Scope

- Decisão dos números comerciais do plano gratuito/pago (quantos ativos,
  quantas análises/mês, preço, loja) — depende do Alex, ADR-010; a revisão
  avaliou só se a arquitetura aguenta quando a decisão vier (confirmado:
  aguenta, ver FIX-C31/C32/C33)
- Modo Operador de trades reais — fora do produto por princípio (só carteira
  simulada)
- Posição vendida/short — não existe no modelo de dados, fora de escopo de
  produto
- Fill parcial de ordem — reafirmado em v1.1 (FIX-C14): simulação é
  tudo-ou-nada por desenho, defensável pelo princípio 5 (determinismo);
  declarado explicitamente em copy/doc, não é lacuna
- Fonte dupla por finalidade (brapi só carteira/watchlist, Yahoo só Radar) —
  descartada no checkpoint da fase 1: o Radar intraday (15m) já usa Yahoo
  automaticamente, ganho real seria modesto
- Escolha de fonte de dado (brapi/Yahoo) e frequência de atualização na UI
  do usuário — rejeitada explicitamente no `docs/adr/008-...md`
- Suíte E2E/Playwright completa — avaliada em v1.1 (FIX-C27/ADR-018) e
  decidido NÃO adotar agora: os 3 defeitos históricos mais caros do produto
  ocorreram no lado nativo/Capacitor, superfície que Playwright-em-PWA não
  alcançaria; 4 gatilhos objetivos de reavaliação documentados no ADR-018
- Medidor de orçamento brapi visível ao usuário final — avaliado em v1.1
  (FIX-C34) e decidido que NÃO é necessário: o fix de FIX-C30 (Fase 3) já
  cobre o efeito prático (aviso de dado degradado, sem vazar número);
  construir um medidor nesse ponto contradiria essa decisão de produto já
  shippada

## Context

- Produto maduro, agora com o motor de recomendação revisado com evidência
  medida (não mais intuição): 15 anos de replay determinístico (ADR-016)
  mostraram que o motor de setups tinha expectância negativa; a seleção
  dinâmica por desempenho histórico (ADR-017) é o mecanismo corretivo, em
  produção desde 2026-08-21/22.
- CLAUDE.md da raiz do repo é a fonte normativa de produto: 10 princípios
  obrigatórios (saldo fictício, sem ordem real, transparência de dado, sem
  invenção de valor, cálculo determinístico, sem promessa de lucro,
  disclosure de dado histórico/atrasado, sem enriquecimento rápido, estados
  completos, acessibilidade).
- ADRs relevantes: 001/008 (fonte de dados), 006/007 (camada de entendimento
  e assistente), 010 (planos e cap gratuito — pendente comercial), 013
  (RBAC), 014 (admin mobile), 015 (assertividade da instrumentação), 016
  (diagnóstico do motor de setups), 017 (seleção dinâmica), 018 (avaliação
  de cobertura E2E — decisão de não adotar agora).
- **v1.1 entregou**: Fases 2-5 (REPORT-01: realismo de mercado + os 30
  achados Crítico/Alto/Médio) + Fases 6-8 (nascidas de pesquisa ad-hoc sobre
  o motor de recomendação: instrumentação de assertividade, seleção
  dinâmica por desempenho histórico, interface do histórico medido).
  7 fases, 44 planos, 343 commits, ~5 dias (2026-08-18 a 2026-08-23).
- **v1.3 entregou**: Fases 12-13 (cap comercial ponta a ponta — limites reais
  do plano gratuito, gates bloqueando de verdade, UI de uso/limite nos dois
  stores, bypass do iOS fechado). 2 fases, 8 planos, ~82 commits no range
  (inclui 1 merge de trabalho concorrente não relacionado, PR #27/ADR-23),
  ~2 dias (2026-08-29 a 2026-08-31, incluindo checkpoints humanos ao vivo).
- Suíte canônica de teste: `bash scripts/executar.sh --testes` (pytest +
  web/tests/*.mjs); `scripts/test.sh` sozinho é meia baseline. Desde a Fase
  5 (FIX-C24), o próprio `executar.sh` resolve `web/node_modules` ausente
  sozinho (antes precisava de `npm install` manual em checkout/worktree
  novo) e mostra a causa real de falha web em vez de engolir o erro.
- `web-admin/` (portal admin) não tem framework de teste — verificação é
  `npx vite build` + guardiões estáticos em `web/tests/*.mjs` que leem o
  código-fonte do portal (precedente confirmado, `test_fase3_custos_falha_
  brapi.mjs` e outros).
- Deploy: Railway serve só `server/web_dist` (app consumidor) e
  `server/admin_dist` (portal) — publicação é sempre passo manual
  (`scripts/publicar-web.sh`/`publicar-admin.sh`), nunca automático no CI.

## Constraints

- **Produto**: bundle id `com.alexandrecamerini.bolsia` não muda (login SIWA
  depende disso) — qualquer achado sobre branding/nome não pode sugerir isso
- **Financeiro**: cotações, posições, ordens, saldo, custos, lucro/prejuízo e
  drawdown são sempre calculados por regra determinística, nunca pela IA —
  qualquer achado que aproxime IA de cálculo financeiro é severidade alta
- **Dado de mercado**: brapi é master gratuita com orçamento de requisições
  (15k/mês para o app inteiro), Yahoo é backup/intraday — não é diferencial
  de plano pago (ADR-010, decisão 3)
- **Regulatório**: manchete do card de decisão vem só do motor determinístico
  (guardrail CVM); IA explica, nunca substitui
- **Deploy**: Railway com `rootDirectory=/server`; só `server/` é publicado,
  por isso `web_dist`/`admin_dist`/`ios_dist` ficam versionados no git
- **Seleção de setups**: toda elegibilidade/ranking é regra determinística
  sobre o ledger medido (ADR-017) — se algum dia a proposta for deixar a IA
  escolher setup, ordenar o Radar ou decidir entrada, isso é mudança de
  natureza e exige aprovação separada (guardrail explícito do ADR-017)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Bootstrap do GSD via `/gsd:new-project` num produto brownfield maduro | Usuário pediu revisão geral estruturada; GSD dá rastreabilidade de achado→fase de correção | ✓ Good — todos os 50 requirements de v1.1 rastreados até o REPORT-01/ADR-015/016/017, 44/44 planos com SUMMARY |
| Fase 1 é só diagnóstico, sem correção inline | Usuário escolheu explicitamente — quer priorizar antes de mexer em código | ✓ Good — checkpoint humano confirmou a régua de severidade antes de qualquer código mudar |
| 5 plans paralelos (wave 1) + 1 de consolidação (wave 2) | Mesmo padrão do map-codebase — reduz wall-clock | ✓ Good, causa raiz resolvida — o worktree isolado clona de `origin/main`, não do HEAD local; a partir da Fase 6, `git push` sempre roda antes de spawnar a wave seguinte (nunca mais o problema reapareceu) |
| Fonte dupla por finalidade e listbox de escolha de fonte (propostas do Alex no checkpoint) | Ganho de orçamento pareceu grande à primeira vista | ⚠️ Revisit se re-proposto — ambas descartadas com evidência: Radar intraday já usa Yahoo de graça; listbox já rejeitada no ADR-008 duas vezes |
| Critério de aposentadoria de setup: magnitude econômica em faixas, não \|t\| | Alex rejeitou a proposta original (\|t\| conflacia efeito com tamanho de amostra — provado com Setup 9.1 baixa vs alta, dano quase idêntico, veredito oposto só por 426 observações a mais) | ✓ Good — critério revisado incorporado no ADR-017 Decisão 1 antes de qualquer código, evitou aposentar setup errado por artefato estatístico |
| Checkpoint humano bloqueante represa o push da FASE INTEIRA, não só da task do checkpoint | Fase 8: push de wave 1 (hábito herdado das Fases 6/7) colocou o gate de `entradaAuto` em produção horas antes da aprovação do Alex — exposição real avaliada como zero (feature desligada em todas as contas), mas foi sorte, não desenho | ✓ Good — regra aplicada corretamente na Fase 5 (checkpoint do 05-08), nenhuma wave deu push antes da aprovação |
| Plano que toca `web/src/` precisa de task explícita de bump+publicar-web.sh | Fase 4: os 7 planos fecharam os 9 achados com suíte verde, mas nenhum publicou o front — ficou testado, mergeado e invisível em produção até eu notar manualmente | ✓ Good — corrigido antes de fechar a Fase 4 (commit `f2ef08e`); Fase 5 já nasceu com plano de publicação (05-08) desde o planejamento |
| Consultar design specialists dedicados (navigation/typography) antes do UI-SPEC, quando a fase tem decisão de UI real em aberto | Fase 13 tinha 2 perguntas de design não travadas no CONTEXT.md (validar o placement dual, decidir o tratamento tipográfico do "X/Y") — consulta directa aos specialists deu input mais concreto (achou a distinção `data.watchlist.length`×`catalogSel.length` que evita os 2 contadores divergirem) do que deixar o gsd-ui-researcher inferir sozinho | ✓ Good — UI-SPEC nasceu quase pronto, só 1 bloqueio de checker (3º peso de fonte), resolvido em 1 iteração |
| Code review obrigatório pós-fase (`code_review_gate`) não é cerimônia — achou um Critical real na Fase 13 | Gate fail-closed do CAP-12/CR-01 no iOS comparava a contagem do servidor (sempre desconectada, iOS é local-first) em vez da do aparelho; guardião existente só checava ORDEM das chamadas, não qual valor alimentava a decisão — o próprio objetivo da fase (fechar CR-01) não estava de fato fechado até esse achado | ✓ Good — corrigido, guardião reforçado (mutation-tested), e o mesmo padrão replicado preventivamente no caminho irmão (`putWatchlist`) antes mesmo de virar bug lá |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-05 — milestone v1.5 (redesenho de UI) iniciado com v1.4 ainda em execução*
