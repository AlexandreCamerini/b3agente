---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Realismo de Mercado + Correções
status: executing
stopped_at: Phase 08 completa — checkpoint 08-05 aprovado, Bloco 3/4 do ADR-017 em produção
last_updated: "2026-08-21T21:00:00.000Z"
last_activity: 2026-08-21 -- Phase 8 concluída (checkpoint aprovado, deploy confirmado)
progress:
  total_phases: 7
  completed_phases: 5
  total_plans: 29
  completed_plans: 29
  percent: 71
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-18)

**Core value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.
**Current focus:** Phase 4/5 — Correção Médio (REPORT-01), ainda não iniciadas

## Current Position

Phase: 08 (interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref) — COMPLETE
Plan: 5 of 5
Status: Fase 08 concluída — checkpoint 08-05 aprovado, Bloco 3/4 do ADR-017 em produção (item 8 do checkpoint — entrada automática por um pregão inteiro — deferido como acompanhamento)
Last activity: 2026-08-21 -- Phase 8 concluída

Progress: [███████░░] 71% (v1.1, 5/7 fases: 2,3,6,7,8 completas; 4,5 não iniciadas)

## Performance Metrics

**Velocity:**

- Total plans completed: 6 (all in v1.0)
- Average duration: -
- Total execution time: 0h (v1.1)

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 (v1.0) | 6 | - | - |
| 2 (v1.1) | TBD | - | - |
| 3 (v1.1) | TBD | - | - |
| 4 (v1.1) | TBD | - | - |
| 5 (v1.1) | TBD | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap v1.1: severity-based grouping for the 30 FIX-C* corrections
  (Phase 3 = 2 Crítico + 8 Alto together, following REPORT-01's own
  technical-dependency sequencing) instead of pure dimension-based —
  the report's "Sugestão de sequenciamento" already chains C-11→C-30,
  C-12→C-36, C-20→C-19, C-31→C-32, C-35→C-37 by technical prerequisite,
  not by product dimension.

- Roadmap v1.1: the 20 Médio corrections split by cohesion, not severity
  alone — Phase 4 groups STORY+UX (user-facing: pedagogy, disclaimers,
  accessibility), Phase 5 groups CODE+GATE+ADMIN (technical: test
  coverage, gate call-site hygiene, admin observability). All 4 v1.1
  phases marked technically independent (no hard "Depends on" between
  them) — advisor caught an over-claimed Phase 5→Phase 3 dependency
  (C33/C34 touch the same call site as C31/C32 but as an independent
  parameter, not a prerequisite) that would have needlessly serialized
  work given config.json's parallelization:true.

- Phase numbering continues from v1.0 (Phase 1) — v1.1 starts at Phase 2,
  no --reset-phase-numbers used.

### Roadmap Evolution

- Phase 6 added: Instrumentação de Assertividade (ADR-015) — corrige a
  medição de eficiência da IA (`analysis_outcomes`), que fabricava stops
  (âncora no close em vez do gatilho) e inflava `n` por duplicação, na
  direção otimista. Não vem do REPORT-01; nasceu de pesquisa ad-hoc
  (quick task 260820-0hl) pedida pelo Alex sobre por que o produto fecha
  mais por stop que por alvo. Sequenciada depois de Phase 5 por ordem de
  fila (não há dependência técnica real com Phase 4/5).

- Phase 7 added: Seleção Dinâmica por Desempenho Histórico (ADR-017, Bloco
  1) — o motor de setups tem expectância negativa (ADR-016, 15 anos,
  125.938 sinais); Bloco 0 do ADR-017 já aposentou a faixa catastrófica
  (6 setups) fora do fluxo GSD normal, direto em produção (commit
  4a6e7e3, 2026-08-20). Phase 7 é o Bloco 1: ledger de sinais resolvidos,
  bootstrap único, hook diário incremental, guard de granularidade do
  Yahoo, `regime.ranquear` consumindo elegibilidade por janela anual.
  Arquitetura já desenhada e aprovada pelo Alex em Plan Mode — ver
  docs/adr/017-revisao-de-setups-e-selecao-dinamica.md. Não depende de
  Phase 4/5 (Médio do REPORT-01, ainda não iniciadas); sequenciada depois
  de Phase 6 por ordem de fila real (Bloco 2 do ADR-017 pedia Phase 6
  primeiro, para não contrastar retrospectivo × prospectivo com o
  prospectivo ainda quebrado).

- Phase 8 added: Interface e IA da Seleção Dinâmica (ADR-017, Bloco 3/4) —
  Bloco 1 (Phase 7) entregou o histórico medido por setup só no backend,
  sem vitrine (confirmado ao vivo: card do ativo idêntico ao de antes do
  deploy). Phase 8 é o Bloco 3/4 do ADR-017: vocabulário novo em
  `skill_ref.py`/`copy.js` ("expectância negativa medida", "empate
  estatístico, não lucro" — sem frase canônica hoje), telas do
  Radar/Watchlist/Operador mostrando o `historico` que já chega no JSON,
  e religa `entradaAuto` do Modo Operador (suspenso desde o Bloco 0,
  `agent.ENTRADA_AUTO_SUSPENSA_ADR017`) gated pela elegibilidade da
  seleção dinâmica — ver "Sequenciamento de entrega" item 4 e
  "Consequências" em docs/adr/017-revisao-de-setups-e-selecao-dinamica.md.
  Escolhida pelo Alex entre essa opção e as Fases 4/5 (Médio do
  REPORT-01, ainda sem plano) por ser extensão direta do que acabou de
  ir ao ar.

- Phase 8 fechada (2026-08-21) com um incidente de processo, não de
  código: o orquestrador deu `git push` depois de cada wave (hábito das
  Fases 6/7), mas o Plano 08-05 represava o push da FASE INTEIRA até o
  checkpoint humano — o commit da Wave 1 (Plano 08-02, gate de
  `entradaAuto`) foi ao ar sem aprovação. Exposição real avaliada como
  zero: `entradaAuto` estava desligado em todas as contas durante toda
  a janela. Alex aprovou o checkpoint com o item 8 (entrada automática
  disparando por um pregão inteiro) deferido como acompanhamento — ver
  08-05-SUMMARY.md, seção "Task 2: resolução". **Regra daqui pra
  frente**: fase com checkpoint humano bloqueante não leva push de
  nenhuma wave até a aprovação, mesmo que o commit da wave pareça
  inócuo isolado.

### Pending Todos

- Verificação ao vivo do item 8 do checkpoint 08-05: acompanhar um
  pregão inteiro com `entradaAuto` ligado e confirmar que só dispara
  nos 5 pares elegíveis (123 de fundo alta, IFR2 alta, PFR alta, Setup
  9.1 alta, Setup 9.3 alta), sem evento de aviso em setup inelegível,
  sem salto no consumo de brapi. Confirmar antes que o Alex sabe
  acionar o kill-switch/desligar `entradaAuto` (passo 9 do checkpoint).

### Blockers/Concerns

None yet.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260820-0hl | Pesquisa + design: assertividade do motor de recomendação (ADR-015) | 2026-08-20 | 4f06edb | [260820-0hl-pesquisa-e-design-assertividade-do-motor](./quick/260820-0hl-pesquisa-e-design-assertividade-do-motor/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Backlog | 9 achados Baixo do REPORT-01 (C-06..C-10, C-17, C-18, C-28, C-29) | Not mapped to any phase — explicit backlog | v1.0 close |
| Decision | Números comerciais do plano gratuito/pago (ADR-010) | Pending Alex's business decision | v1.0 close |

## Session Continuity

Last session: 2026-08-21T21:00:00.000Z
Stopped at: Phase 08 concluída — checkpoint 08-05 aprovado
Resume file: .planning/phases/08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref/08-05-SUMMARY.md

## Operator Next Steps

- Item 8 do checkpoint 08-05 (verificação ao vivo da entrada automática
  gated por um pregão inteiro) segue aberto — ver "Pending Todos".
- Fases 4 e 5 (Correção Médio — REPORT-01) seguem não iniciadas, sem plano ainda: `/gsd:plan-phase 4` quando o Alex priorizar.
- 9 tickers com 404 no bootstrap do ledger (ELET3, BRFS3, ELET6, JBSS3, CRFB3, NTCO3, CPLE6, MRFG3, EMBR3) — prováveis renomeações/deslistagens; não investigado, não bloqueia a fase.
