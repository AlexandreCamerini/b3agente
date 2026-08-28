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
de administração separado. Vai ser comercializado: funções básicas grátis com
cota pequena de análises de IA, escalando para planos pagos.

## Core Value

O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado
funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem
acesso a automações do Modo Operador. Se o storyline pedagógico não convencer,
nada mais no produto importa.

## Current Milestone: nenhum aberto — v1.1 shipped 2026-08-23

Ver `.planning/milestones/v1.1-ROADMAP.md` (a criar) e
`.planning/MILESTONES.md` para o histórico completo. Próximo milestone ainda
não iniciado — decisão do Alex entre: (a) novo milestone de funcionalidade,
ou (b) fechar o backlog abaixo primeiro (ver "Active").

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
- [ ] Decisão comercial pendente (Alex): números do plano gratuito/pago
  (ADR-010) — arquitetura confirmada pronta (FIX-C33 fechou o último gap
  estrutural); falta só a decisão de negócio
- [ ] `textDim` do tema claro também reprova contraste WCAG AA (4.20:1) —
  achado colateral da Fase 4 (fora do escopo do C-16 original), candidato a
  backlog
- [ ] 9 tickers com 404 no bootstrap do ledger de sinais (ELET3, BRFS3,
  ELET6, JBSS3, CRFB3, NTCO3, CPLE6, MRFG3, EMBR3) — prováveis
  renomeações/deslistagens, não investigado
- [ ] Retomar a virada de produção do mydata (Fase 9, checkpoint `adiar`):
  rodar a perna ao vivo da medição (`MYDATA_TOKEN` real +
  `scripts/medir-mydata.py --fases vivo --vivo`) e resolver o pico/min
  (148 projetado vs. 60/min da chave) antes de religar
  `B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER=mydata` — ver
  `docs/MEDICAO-Mydata-2026-08-27.md` e `09-06-SUMMARY.md`
- [ ] Opções via mydata sem gate de orçamento (`options_provider_mydata.py`)
  — achado do 09-REVIEW.md (WR-01), dormente enquanto `B3_OPTIONS_PROVIDER`
  ficar em `yahoo`; precisa de gate antes de virar

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
*Last updated: 2026-08-27 after Phase 9 (standalone)*
