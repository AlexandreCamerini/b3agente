# Roadmap: Boris+ (b3-agente) — Revisão Geral

## Overview

Projeto de revisão/auditoria (não de construção de feature). Uma única fase
produz um relatório diagnóstico consolidado, cobrindo as 5 dimensões pedidas
pelo Alex com peso igual: storyline pedagógico (Modo Estudo → Operador),
UI/UX, dívida técnica de código, arquitetura de gating de monetização e
portal de administração/observabilidade. Nenhuma correção é implementada
nesta fase — o relatório vira o insumo para o roadmap de correção das fases
seguintes (fora deste milestone).

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Auditoria Diagnóstica Consolidada** - Relatório único, classificado por severidade, cobrindo storyline pedagógico, UX/UI, código, gating de monetização e portal admin. (completed 2026-08-18)

## Phase Details

### Phase 1: Auditoria Diagnóstica Consolidada

**Goal**: Produzir um único relatório (REPORT-01) que documenta, para cada uma
das 5 dimensões do produto, os achados encontrados com severidade
(crítico/alto/médio/baixo), evidência (arquivo:linha quando aplicável) e
recomendação — sem implementar nenhuma correção. O relatório é o insumo
direto para priorizar as fases de correção seguintes (fora deste milestone).
**Depends on**: Nothing (first phase)
**Requirements**: STORY-01, STORY-02, STORY-03, STORY-04, UX-01, UX-02, UX-03, UX-04, CODE-01, CODE-02, CODE-03, CODE-04, GATE-01, GATE-02, GATE-03, ADMIN-01, ADMIN-02, ADMIN-03, REPORT-01
**Success Criteria** (what must be TRUE):

  1. Relatório documenta a jornada pedagógica real do usuário (Estudo→Operador) contra os 8 passos da Experiência Principal do CLAUDE.md, avalia se a transição de modo tem gatilho/narrativa claros, mede a cobertura real da camada educacional e inventaria violações reais de promessa de lucro/confluência — cada achado com severidade e evidência (STORY-01..04).
  2. Relatório documenta achados de UI/UX contra os 10 princípios obrigatórios do CLAUDE.md (saldo fictício visível, transparência de fonte/horário do dado, estados completos, consistência visual Estudo vs. Operador, responsividade mobile, acessibilidade básica, copy sem enriquecimento rápido/garantia de acerto) — cada achado com severidade e evidência (UX-01..04).
  3. Relatório documenta achados de dívida técnica com risco real ao produto: mapa de divergência do `appMode` recalculado em 11+ pontos do `App.jsx`, lacunas dos guardiões de paridade (`deviceStore`/`serverStore`, `defaults.py`/`catalog.js`), severidade/blast radius do defeito já conhecido do gate "Executar", e cobertura da suíte canônica contra os fluxos financeiros críticos — cada achado com severidade e evidência arquivo:linha (CODE-01..04).
  4. Relatório documenta se a arquitetura de gating (`plan.py`/`metering.py`) aguenta escalonamento free→pago sem reescrita estrutural, se a UI comunica com transparência a diferença entre cota física da brapi e cap comercial, e mapeia as features hoje candidatas a tier pago com esforço de ativação — sem decidir números comerciais (GATE-01..03).
  5. Relatório documenta cobertura do portal admin (`web-admin/`) contra os grupos RBAC do ADR-013, se a visibilidade operacional (kill-switch, orçamento brapi, métricas de IA) teria permitido detectar/agir mais rápido no incidente real de 2,5 dias, e a usabilidade do handoff mobile do ADR-014 (ADMIN-01..03).
  6. Todos os achados das 5 dimensões estão consolidados em um único documento (REPORT-01), classificados por severidade e dimensão, sem nenhuma sugestão de correção implementada — pronto para alimentar o roadmap de fases de correção seguintes.

**Plans**: 6 plans (5 em paralelo na wave 1, 1 de consolidação na wave 2)
**UI hint**: yes

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Dimensão STORY: jornada pedagógica Estudo→Operador, verificada ao vivo contra os 8 passos (STORY-01..04) → FINDINGS-STORY.md
- [x] 01-02-PLAN.md — Dimensão UX: os 10 princípios obrigatórios, matriz de estados, responsivo/acessibilidade e copy (UX-01..04) → FINDINGS-UX.md
- [x] 01-03-PLAN.md — Dimensão CODE: mapa do `appMode`, lacunas de paridade, gate "Executar" e cobertura dos fluxos financeiros (CODE-01..04) → FINDINGS-CODE.md
- [x] 01-04-PLAN.md — Dimensão GATE: `plan.py`/`metering.py` frente ao escalonamento free→pago, cota brapi × cap comercial, features candidatas (GATE-01..03) → FINDINGS-GATE.md
- [x] 01-05-PLAN.md — Dimensão ADMIN: 10 abas × RBAC do ADR-013, replay do incidente do kill-switch, handoff mobile do ADR-014 (ADMIN-01..03) → FINDINGS-ADMIN.md

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-06-PLAN.md — Consolidação: dedup entre dimensões, severidade normalizada, sumário executivo e rastreabilidade dos 19 requisitos (REPORT-01) → REPORT-01.md

## Progress

**Execution Order:**
Phase 1 (single phase, coarse granularity — review/audit deliverable)

- Wave 1 (paralelo): 01-01, 01-02, 01-03, 01-04, 01-05
- Wave 2 (depende de toda a wave 1): 01-06

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Auditoria Diagnóstica Consolidada | 6/6 | Complete    | 2026-08-18 |
