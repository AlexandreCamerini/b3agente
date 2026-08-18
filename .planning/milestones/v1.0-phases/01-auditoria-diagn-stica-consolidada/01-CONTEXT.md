# Phase 1: Auditoria Diagnóstica Consolidada - Context

**Gathered:** 2026-08-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Produzir um único relatório (REPORT-01) que documenta, para cada uma das 5
dimensões do produto (storyline pedagógico, UX/UI, código, gating de
monetização, portal admin), os achados encontrados com severidade, evidência
(arquivo:linha quando aplicável) e recomendação — **sem implementar nenhuma
correção**. O relatório é o insumo direto para priorizar as fases de
correção seguintes (fora deste milestone).

</domain>

<decisions>
## Implementation Decisions

### Método de verificação
- **D-01:** Achados de storyline (STORY-01..04) e UX (UX-01..04) exigem
  verificação ao vivo — abrir o PWA num browser preview e navegar os fluxos
  reais (escolher ativo → dado → ordem → carteira → Modo Estudo → Modo
  Operador), não só leitura de código/copy. Achados de código, gating e
  admin (CODE/GATE/ADMIN) podem ser inferidos de leitura de código/docs —
  live-test só onde agregar confiança real (ex: telas do web-admin, se
  acessível localmente).

### Régua de severidade (aplica a todos os achados de REPORT-01)
- **D-02:** **Crítico** — viola um dos 10 princípios obrigatórios do
  CLAUDE.md do repo ou o guardrail CVM (manchete do card só do motor
  determinístico).
- **D-03:** **Alto** — já causou incidente real documentado (ex: os 3 bugs
  do padrão `appMode` em `App.jsx`, o kill-switch de 2,5 dias) OU bloqueia
  uma decisão de negócio pendente (ex: gating estruturalmente pronto mas
  inerte).
- **D-04:** **Médio** — risco real, ainda não materializado em incidente
  (ex: dívida técnica documentada em CONCERNS.md sem ocorrência registrada).
- **D-05:** **Baixo** — polimento/consistência sem risco de produto.

### Estrutura de execução
- **D-06:** 5 plans paralelos, um por dimensão (STORY, UX, CODE, GATE,
  ADMIN), cada um produzindo achados brutos com severidade+evidência+
  recomendação; mais 1 plan final de consolidação que aplica a régua de
  severidade de forma consistente entre dimensões e escreve REPORT-01.
  Mesmo padrão usado no `map-codebase` desta sessão (4 agentes paralelos +
  síntese).

### Formato do relatório final
- **D-07:** REPORT-01 é um único documento: abre com sumário executivo
  (achados críticos/altos em bullet, pra decisão rápida), seguido do
  detalhe técnico completo por dimensão (todo achado com evidência
  arquivo:linha e recomendação). Não separar em dois arquivos.

### Claude's Discretion
- Escolha exata de quais telas/fluxos navegar ao vivo dentro de
  STORY/UX (o roteiro dos 8 passos da Experiência Principal do CLAUDE.md é
  o guia, mas a ordem/profundidade da navegação fica a critério de quem
  executa o plan).
- Nível de detalhe da recomendação por achado (uma frase vs. um parágrafo)
  — proporcional à severidade.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Princípios de produto (fonte normativa)
- `CLAUDE.md` (raiz do repo) — 10 princípios obrigatórios, Experiência
  Principal (8 passos), Camada educacional, guardrails de repositório
  (invariantes)

### Mapa do codebase (gerado nesta sessão, commit 94aa35d)
- `.planning/codebase/ARCHITECTURE.md` — motor de simulação, separação
  Estudo/Operador via `appMode`, RBAC, admin portal
- `.planning/codebase/CONCERNS.md` — dívida técnica com evidência
  arquivo:linha já levantada (monólito App.jsx, gate "Executar" mudo,
  paridade deviceStore/serverStore, gating inerte, kill-switch sem TTL)
- `.planning/codebase/STRUCTURE.md`, `STACK.md`, `INTEGRATIONS.md`,
  `CONVENTIONS.md`, `TESTING.md` — referência geral

### ADRs
- `docs/adr/010-planos-e-cap-gratuito.md` — modelo de planos, o que é
  técnico (decidido) vs. comercial (pendente do Alex) — GATE-01..03
- `docs/adr/013-rbac-papeis-e-entitlements.md` — RBAC, grupos — ADMIN-01
- `docs/adr/014-administracao-mobile.md` — handoff mobile do admin —
  ADMIN-03
- `docs/adr/001-fonte-de-dados-intraday.md`,
  `docs/adr/008-fonte-de-cotacoes-selecionavel.md` — fonte de dados,
  transparência — relevante pra UX-01
- `docs/adr/006-camada-de-entendimento.md`,
  `docs/adr/007-assistente-e-push-do-gatilho.md` — camada didática —
  STORY-03

### Defeitos/achados já documentados (não redescobrir)
- `docs/auditoria-controle-ordens-parametros.md` — gate "Executar" mudo em
  toque (`App.jsx:3596-3610`, `:3745-3749`) — insumo direto pra CODE-03
- `docs/plano-operador-entrada-e-modos.md` — separação Estudo/Operador na
  execução automática, status "aguardando aprovação" — verificar se foi
  implementado ou segue pendente, relevante pra STORY-02/CODE-01

### Projeto
- `.planning/PROJECT.md` — Core Value, constraints, requisitos validados
- `.planning/REQUIREMENTS.md` — os 19 requisitos (STORY/UX/CODE/GATE/
  ADMIN/REPORT) desta fase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.planning/codebase/CONCERNS.md` já tem 3 achados de código prontos com
  arquivo:linha (monólito App.jsx, gate Executar mudo, paridade de stores)
  — o plan de CODE deve partir daqui, não redescobrir do zero.

### Established Patterns
- Vocabulário por modo centralizado em `server/app/skill_ref.py` (backend)
  espelhado em `web/src/copy.js` (front) — ponto de verdade pra STORY-04
  (a IA nunca promete lucro).
- `appMode` é lido de `config.appMode`, recalculado em 11+ pontos de
  `App.jsx` — ponto de partida pra CODE-01.

### Integration Points
- `web/vite.config.js` tem proxy `/api` → `localhost:8787` — como rodar o
  app localmente pra verificação ao vivo (D-01).
- `web-admin/` é app Vite separado — verificar se tem dev server próprio
  documentado antes de tentar rodá-lo.

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência visual/exemplo externo trazido pelo usuário — a régua
de qualidade é o próprio CLAUDE.md do repo (10 princípios + Experiência
Principal), não um benchmark de mercado.

</specifics>

<deferred>
## Deferred Ideas

Nenhuma — a discussão ficou dentro do escopo da fase. Correção dos achados,
decisão dos números comerciais do plano, e qualquer expansão de escopo
identificada durante a auditoria ficam para roadmap futuro (ver PROJECT.md
Out of Scope).

</deferred>

---

*Phase: 1-Auditoria Diagnóstica Consolidada*
*Context gathered: 2026-08-18*
