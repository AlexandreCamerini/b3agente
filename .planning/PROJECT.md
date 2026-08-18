# Boris+ (b3-agente)

## What This Is

Simulador educacional de ações da B3 com dados reais de mercado e dinheiro
exclusivamente virtual. Ensina a mecânica da bolsa brasileira — setups,
indicadores, gestão de risco — através de um Modo Estudo (a IA orienta, nunca
executa) que evolui para um Modo Operador (ferramentas automáticas e análises
mais profundas, com execução simulada). Web/PWA + app iOS nativo (mesmo
bundle via Capacitor), backend Python/FastAPI, portal de administração
separado. Vai ser comercializado: funções básicas grátis com cota pequena de
análises de IA, escalando para planos pagos.

## Core Value

O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado
funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem
acesso a automações do Modo Operador. Se o storyline pedagógico não convencer,
nada mais no produto importa.

## Requirements

### Validated

- ✓ Motor de simulação determinístico (ordens, preço médio, PnL, drawdown)
  server-side em `server/app/store.py`, mirror client-side em
  `web/src/finance.js`/`persistence.js` para uso offline — existing
- ✓ Camada de dados de mercado com fonte declarada e fallback (brapi master,
  Yahoo backup/intraday, ADR-001/ADR-008) — existing
- ✓ Separação Modo Estudo/Modo Operador via flag `appMode`, com vocabulário
  próprio por modo (`skill_ref.py` ↔ `copy.js`) — existing
- ✓ IA multi-provider (Anthropic/OpenAI/Google, BYOK + gerenciada com cota),
  camada didática que explica indicador→correlação→decisão — existing
- ✓ Autenticação multi-método unificada numa única conta (Sign in with Apple,
  Google, e-mail/senha) — existing
- ✓ RBAC/entitlements (ADR-013) e portal de administração/observabilidade
  separado (`web-admin/`, ADR-014, handoff mobile) — existing
- ✓ Estrutura técnica de planos (`plan.py`, `metering.py`) pronta para ligar
  cap comercial, hoje inerte (ADR-010) — existing
- ✓ REVIEW-01: Storyline pedagógico auditado ao vivo (8 passos × 2 modos) —
  jornada confirmada íntegra, CVM conforme, 10 achados (5 Médio, 5 Baixo,
  nenhum Crítico/Alto) — v1.0
- ✓ REVIEW-02: UX/UI auditada ao vivo contra os 10 princípios do CLAUDE.md —
  9 achados, incluindo 1 Crítico (rótulo de fonte de dado hardcoded e
  factualmente errado) — v1.0
- ✓ REVIEW-03: Código/dívida técnica auditada — 10 achados, narrativa de
  causa-raiz dos 3 bugs históricos de `appMode` corrigida com evidência
  linha a linha (nenhum foi causado pela divergência que se supunha) — v1.0
- ✓ REVIEW-04: Arquitetura de gating auditada — hooks de `plan.py` existem
  mas nunca resolvem plano por usuário; achado Crítico (cota brapi
  degradada invisível) — v1.0
- ✓ REVIEW-05: Portal admin/observabilidade auditado — 4 achados (3 Alto, 1
  Médio), incluindo segundo kill-switch invisível e painel cego pro modo de
  falha do provedor de dados — v1.0
- ✓ REVIEW-06: `REPORT-01.md` consolidado — 39 achados (2 Crítico, 8 Alto, 20
  Médio, 9 Baixo), deduplicação evidence-based, validado por checkpoint
  humano com o Alex — v1.0

### Active

- [ ] FIX-01: Corrigir os 2 achados Crítico do REPORT-01 (C-11: rótulo de
      fonte hardcoded no `TechnicalModal`; C-30: estado degradado da cota
      brapi invisível a usuário e admin) — violam o princípio 3 do CLAUDE.md
- [ ] FIX-02: Corrigir os 8 achados Alto do REPORT-01 — ver bloco 1
      ("Sugestão de sequenciamento" do relatório): transparência de
      proveniência/frescor do dado (C-11, C-30) → robustez de erro/
      observabilidade de falha do provedor (C-12, C-36) → guardiões
      estruturais de paridade/regressão (C-20 antes de C-19) → ativação dos
      hooks de gating comercial (C-31 antes de C-32) → visibilidade ativa de
      incidentes operacionais (C-35 antes de C-37)
- [ ] FIX-03 (backlog, não priorizado): os 20 achados Médio e 9 Baixo do
      REPORT-01 — priorizar depois dos Críticos/Altos
- [ ] Decisão comercial pendente (Alex): números do plano gratuito/pago
      (ADR-010) — arquitetura já avaliada como pronta (REVIEW-04); falta só
      a decisão de negócio

### Out of Scope

- Decisão dos números comerciais do plano gratuito/pago (quantos ativos,
  quantas análises/mês, preço, loja) — depende do Alex, ADR-010; a revisão
  avaliou só se a arquitetura aguenta quando a decisão vier (confirmado:
  aguenta, com ressalvas em C-31/C-32)
- Modo Operador de trades reais — fora do produto por princípio (só carteira
  simulada)
- Posição vendida/short — não existe no modelo de dados, fora de escopo de
  produto
- Fonte dupla por finalidade (brapi só carteira/watchlist, Yahoo só Radar) —
  discutida no checkpoint da fase 1 e descartada: o Radar intraday (15m) já
  usa Yahoo automaticamente hoje (`brapi.py:28`, plano gratuito não aceita
  15m), o ganho real seria só ~74 req/dia da fatia "delta" — modesto
- Escolha de fonte de dado (brapi/Yahoo) e frequência de atualização na UI
  do usuário — já proposta e rejeitada explicitamente no
  `docs/adr/008-fonte-de-cotacoes-selecionavel.md` ("usuário sem base para
  escolher; consumo dobrado; L2 duplicado e failover frio"); frequência
  configurável por usuário também esbarra no orçamento ser por-app, não
  por-usuário (ADR-010)

## Context

- Produto já maduro (múltiplos milestones entregues: identidades unificadas,
  Boris UX, rebranding, RBAC/entitlements, camada de entendimento) —
  `.planning/codebase/` (commit `94aa35d`) tem o mapa completo (STACK,
  ARCHITECTURE, STRUCTURE, CONVENTIONS, TESTING, INTEGRATIONS, CONCERNS).
- CLAUDE.md da raiz do repo é a fonte normativa de produto: 10 princípios
  obrigatórios (saldo fictício, sem ordem real, transparência de dado, sem
  invenção de valor, cálculo determinístico, sem promessa de lucro,
  disclosure de dado histórico/atrasado, sem enriquecimento rápido, estados
  completos, acessibilidade).
- ADRs relevantes: 001/008 (fonte de dados), 006/007 (camada de entendimento
  e assistente), 010 (planos e cap gratuito — pendente comercial), 013 (RBAC),
  014 (admin mobile).
- **v1.0 entregou a auditoria geral** (`.planning/phases/
  01-auditoria-diagn-stica-consolidada/REPORT-01.md`, 880 linhas, validado
  pelo Alex em checkpoint humano) — nenhuma correção de código foi
  implementada nesta milestone, por decisão explícita (fase diagnóstica).
  Achados brutos por dimensão continuam nos 5 `FINDINGS-*.md` no mesmo
  diretório, como anexo/auditoria do julgamento.
- Nenhum bug financeiro (ordem/posição/saldo) aberto foi encontrado na
  auditoria — o núcleo determinístico está bem guardado. Os 2 achados
  Crítico são ambos de transparência de dado (princípio 3), não de cálculo.
- Suíte canônica de teste: `bash scripts/executar.sh --testes` (pytest +
  web/tests/*.mjs); `scripts/test.sh` sozinho é meia baseline. Achado da
  auditoria: rodar num worktree/checkout novo sem `web/node_modules`
  instalado faz 7 testes web falharem por ambiente, não por regressão —
  inclui os 2 guardiões mais relevantes desta auditoria (paridade de stores,
  sync de `appMode`). Rodar `npm install` em `web/` antes da suíte.

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

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Bootstrap do GSD via `/gsd:new-project` num produto brownfield maduro | Usuário pediu revisão geral estruturada; GSD dá rastreabilidade de achado→fase de correção | ✓ Good — 19/19 requisitos rastreados até o `REPORT-01`, verificação goal-backward passou 6/6 |
| Fase 1 é só diagnóstico, sem correção inline | Usuário escolheu explicitamente — quer priorizar antes de mexer em código | ✓ Good — checkpoint humano confirmou que a régua de severidade bate com a memória do dono do produto antes de qualquer código mudar |
| Gating avaliado só na arquitetura, não nos números comerciais | Números dependem de decisão de negócio do Alex (ADR-010), fora do alcance desta revisão técnica | ✓ Good — achado real (hooks nunca resolvem plano por usuário) veio à tona sem precisar da decisão comercial |
| As 5 dimensões (storyline, UX, código, gating, admin) pesam igual na fase 1 | Usuário confirmou que nenhuma é mais crítica agora | ✓ Good — os 2 Crítico saíram de dimensões diferentes (UX e GATE), confirmando que nenhuma podia ter sido pulada |
| 5 plans paralelos (wave 1) + 1 de consolidação (wave 2) | Mesmo padrão do map-codebase — reduz wall-clock | ⚠️ Revisit — 2 dos 5 plans paralelos falharam na 1ª tentativa por worktree isolado nascendo de base desatualizada (sem `.planning/`); contornado lendo cross-worktree, mas vale investigar a causa antes do próximo milestone usar o mesmo padrão |
| Fonte dupla por finalidade e listbox de escolha de fonte (propostas do Alex no checkpoint) | Ganho de orçamento pareceu grande à primeira vista | ⚠️ Revisit se re-proposto — ambas descartadas com evidência: Radar intraday já usa Yahoo de graça; listbox já rejeitada no ADR-008 duas vezes |

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
*Last updated: 2026-08-18 after v1.0 milestone*
