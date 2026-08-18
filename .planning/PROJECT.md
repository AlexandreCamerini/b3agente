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

### Active

- [ ] REVIEW-01: Auditoria do storyline pedagógico do Modo Estudo — a
      sequência escolher ativo → dado → contexto/risco → ordem → execução →
      resultado → explicação → aprendizado realmente ensina a mecânica da B3
      a um leigo, com transição clara e motivada para o Modo Operador?
- [ ] REVIEW-02: Auditoria de UI/UX contra os 10 princípios obrigatórios do
      CLAUDE.md do projeto (saldo fictício visível, estados completos,
      transparência de dado, sem linguagem de enriquecimento rápido,
      acessibilidade/responsividade)
- [ ] REVIEW-03: Auditoria de código — dívida técnica que ameaça a
      confiabilidade do produto (monólito `App.jsx` de 7599 linhas com
      `appMode` recalculado em 11+ lugares, parceria `deviceStore`/
      `serverStore`, gate "Executar" sem feedback visual — já documentado em
      `docs/auditoria-controle-ordens-parametros.md`)
- [ ] REVIEW-04: Auditoria da arquitetura de gating por plano — os hooks
      `can_add_ticker`/`can_analyze`/`requires_subscription` de `plan.py`
      sustentam escalonamento real de features (free → pago) sem exigir
      reescrita, mesmo sem os números comerciais definidos ainda?
- [ ] REVIEW-05: Auditoria do portal de administração/observabilidade —
      cobertura de RBAC, visibilidade operacional (kill-switch, orçamento
      brapi, métricas de IA), usabilidade para quem administra
- [ ] REVIEW-06: Relatório consolidado com achados classificados por
      severidade e dimensão, alimentando o roadmap de correção (fases
      seguintes, fora desta fase 1)

### Out of Scope

- Correção de achados nesta fase — fica para fases seguintes do roadmap,
  priorizadas depois do relatório (decisão explícita: revisão é diagnóstico,
  não implementação)
- Decisão dos números comerciais do plano gratuito/pago (quantos ativos,
  quantas análises/mês, preço, loja) — depende do Alex, ADR-010; a revisão
  avalia só se a arquitetura aguenta quando a decisão vier
- Modo Operador de trades reais — fora do produto por princípio (só carteira
  simulada)
- Posição vendida/short — não existe no modelo de dados, fora de escopo de
  produto

## Context

- Produto já maduro (múltiplos milestones entregues: identidades unificadas,
  Boris UX, rebranding, RBAC/entitlements, camada de entendimento) — esta é a
  primeira vez que o projeto entra no fluxo GSD; `.planning/codebase/`
  (commit `94aa35d`) tem o mapa completo (STACK, ARCHITECTURE, STRUCTURE,
  CONVENTIONS, TESTING, INTEGRATIONS, CONCERNS).
- CLAUDE.md da raiz do repo é a fonte normativa de produto: 10 princípios
  obrigatórios (saldo fictício, sem ordem real, transparência de dado, sem
  invenção de valor, cálculo determinístico, sem promessa de lucro,
  disclosure de dado histórico/atrasado, sem enriquecimento rápido, estados
  completos, acessibilidade) — todo achado desta revisão se mede contra eles.
- ADRs relevantes: 001/008 (fonte de dados), 006/007 (camada de entendimento
  e assistente), 010 (planos e cap gratuito — pendente comercial), 013 (RBAC),
  014 (admin mobile).
- `docs/auditoria-controle-ordens-parametros.md` já documenta um defeito
  conhecido (gate "Executar" trava silenciosamente sem feedback) — insumo
  direto para REVIEW-03, não redescobrir.
- Suíte canônica de teste: `bash scripts/executar.sh --testes` (pytest +
  web/tests/*.mjs); `scripts/test.sh` sozinho é meia baseline.

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
| Bootstrap do GSD via `/gsd:new-project` num produto brownfield maduro | Usuário pediu revisão geral estruturada; GSD dá rastreabilidade de achado→fase de correção | — Pending |
| Fase 1 é só diagnóstico, sem correção inline | Usuário escolheu explicitamente — quer priorizar antes de mexer em código | — Pending |
| Gating avaliado só na arquitetura, não nos números comerciais | Números dependem de decisão de negócio do Alex (ADR-010), fora do alcance desta revisão técnica | — Pending |
| As 5 dimensões (storyline, UX, código, gating, admin) pesam igual na fase 1 | Usuário confirmou que nenhuma é mais crítica agora | — Pending |

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
*Last updated: 2026-08-18 after initialization*
