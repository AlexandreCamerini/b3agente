---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Cap comercial (plano gratuito)
status: executing
stopped_at: Phase 13 UI-SPEC approved
last_updated: "2026-08-30T00:05:42.348Z"
last_activity: 2026-08-30 -- Phase 13 execution started
progress:
  total_phases: 2
  completed_phases: 1
  total_plans: 8
  completed_plans: 3
  percent: 38
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-29)

**Core value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.
**Current focus:** Phase 13 — Uso real visível na interface + enforcement no iOS

## Current Position

Phase: 13 (Uso real visível na interface + enforcement no iOS) — EXECUTING
Plan: 1 of 5
Status: Executing Phase 13
Last activity: 2026-08-30 -- Phase 13 execution started

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 20 (v1.0) + 44 (v1.1) + 6 (Phase 9, standalone) + 8 (v1.2)
- Average duration: -
- Total execution time: 0h (v1.3)

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 (v1.0) | 6 | - | - |
| 2-8 (v1.1) | 44 | - | - |
| 9 (standalone) | 6 | - | - |
| 0 (v1.2) | 2 | - | - |
| 10 (v1.2) | 3 | - | - |
| 11 (v1.2) | 3 | - | - |
| 12 (v1.3) | TBD | - | - |
| 13 (v1.3) | TBD | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- v1.3 roadmap: numeração contínua a partir de v1.2 (Phase 11 foi a última) —
  Phase 12/13, sem `--reset-phase-numbers`.

- v1.3 roadmap: investigação de código confirmou que a fiação de gate já
  existe (`_gate_analise` em `main.py` já usa `metering.month_used` real;
  `/api/ai-quota` já devolve `monthLimit` do plano) — Phase 12 é troca de
  números (`PLAN_FREE.max_watchlist`/`max_analyses_per_month`, hoje `None`)

  + revisão de copy de recusa (CAP-07), não infraestrutura nova.

- v1.3 roadmap: Phase 13 (visibilidade na UI) depende de Phase 12 por uma
  razão técnica real, não estética — precisa de um endpoint novo expondo
  `max_watchlist`/contagem da watchlist que nenhum requirement CAP-01..05
  exige (análises já tem `/api/ai-quota`; watchlist não tem equivalente
  hoje). Duas fases mantidas (não colapsadas em uma só) porque cada uma é
  um incremento completo e verificável isoladamente: Fase 12 sozinha já é
  um gate funcionando (usuário é bloqueado corretamente, só sem número
  visível antes de bater no teto); Fase 13 adiciona visibilidade proativa.

- v1.3 roadmap: mensagem de recusa atual de `can_add_ticker`
  ("Faça upgrade para adicionar mais.") tem tom de CTA — CAP-07 exige só
  fato+motivo. Fechado como critério de sucesso explícito da Fase 12 (não
  deixado implícito), para não ser descartado no planejamento.

### Roadmap Evolution

- Milestone v1.3 aberto (2026-08-29) para ativar os limites comerciais do
  plano gratuito (ADR-010) — 2 fases, ambas pequenas: Fase 12 liga os
  números do gate no backend, Fase 13 expõe o uso real na UI (web + iOS).
  Sem loja/IAP, sem preço/moeda — `PLAN_PRO` continua ilimitado por decisão.

- Phase 13 edited: edited fields: success_criteria (adiciona itens 8-9: limpeza de resíduos BolsIA + checkpoint humano App Store Connect/TestFlight)

### Pending Todos

None yet.

### Blockers/Concerns

- Retomada da virada de produção do mydata (Fase 9, checkpoint `adiar`) —
  segue fora de escopo de v1.3, não relacionado a este milestone.

- 3 itens de backlog pré-existentes bloqueados por dependência humana
  (verificação ao vivo de `entradaAuto`; 2 human-checks da Fase 3) — não
  relacionados a v1.3, seguem em PROJECT.md Active.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260830-eqm | Fase 4 do ADR-23 — Boris+ relying party do semente.id, GET /observabilidade, cauda do rename | 2026-08-30 | f534fda | Verified — PR #27 merged, deploy em produção confirmado (build F10-20260830-01), checkpoint aprovado pelo Alex ao vivo | [260830-eqm-fase-4-adr-23-boris-relying-party-do-sem](./quick/260830-eqm-fase-4-adr-23-boris-relying-party-do-sem/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close (v1.2 → v1.3):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Backlog | 9 achados Baixo do REPORT-01 (C-06..C-10, C-17, C-18, C-28, C-29) | Not mapped to any phase — explicit backlog | v1.0 close |
| verification_gap | Item 8 do checkpoint 08-05 — verificação ao vivo de `entradaAuto` por um pregão inteiro | human_needed | v1.1 close |
| verification_gap | 2 human-checks da Fase 3 (card de status 3 badges reativo; mensagem de "sem permissão" do kill-switch) | human_needed | v1.1 close |
| Production cutover | Virada de `B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER=mydata` (Fase 9, checkpoint `adiar`) — pico/min mitigado em código (2026-08-28), falta só religar em produção | blocked_on_operator_action | Fase 9 close (2026-08-27) |
| WR-01 (arquitetura) | Race condition check-then-debit em `mydata_budget` — até 3 consumidores concorrentes potenciais | Decisão de arquitetura pendente | v1.2 close (2026-08-28) |
| v2 requirements | CAP-08..11 (loja/IAP, preço/moeda, IA gerenciada sem BYOK como paga, alvo dinâmico exclusivo do pago) | Deferred to future release — depende da decisão comercial de venda em si | v1.3 roadmap (2026-08-29) |

## Session Continuity

Last session: 2026-08-29T22:57:56.315Z
Stopped at: Phase 13 UI-SPEC approved
Resume file: .planning/phases/13-uso-real-vis-vel-na-interface-enforcement-no-ios/13-UI-SPEC.md

## Operator Next Steps

- Run `/gsd:plan-phase 12` to break Phase 12 into executable plans.
