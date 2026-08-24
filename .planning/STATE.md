---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Realismo de Mercado + Correções
status: Awaiting next milestone
stopped_at: Phase 05 concluída — checkpoint 05-08 aprovado, deploy confirmado
last_updated: "2026-08-23T22:29:01.638Z"
last_activity: 2026-08-23 — Milestone v1.1 completed and archived
progress:
  total_phases: 7
  completed_phases: 7
  total_plans: 44
  completed_plans: 44
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-18)

**Core value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.
**Current focus:** Milestone v1.1 concluído — decidir próximo milestone/foco com o Alex

## Current Position

Phase: Milestone v1.1 complete
Plan: —
Status: Awaiting next milestone
Last activity: 2026-08-24 - Completed quick task 260823-vu4: Ajuste de UI no cabeçalho: badge mercado fechado vaza no Topbar + espaço desperdiçado até a Dynamic Island

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
| 260823-vu4 | Ajuste de UI no cabeçalho: badge mercado fechado vaza no Topbar + espaço desperdiçado até a Dynamic Island | 2026-08-24 | 8603858 | [260823-vu4-ajuste-de-ui-no-cabecalho-badge-mercado-](./quick/260823-vu4-ajuste-de-ui-no-cabecalho-badge-mercado-/) |

## Deferred Items

Items acknowledged and deferred at milestone close on 2026-08-23:

| Category | Item | Status |
|----------|------|--------|
| verification_gap | Phase 03 (03-VERIFICATION.md): 2 human-check items nunca confirmados ao vivo — card de status 3 badges reativo (troca de Modo do app / toggle Operador no servidor movendo os badges juntos) e mensagem de "sem permissão" no kill-switch do timing_watch pra conta sem `execucao_automatica.controlar`. Passou por checkpoint diferente (03-06 Task 3), que cobriu 7 outros itens mas não estes 2. | human_needed |
| quick_task | 260820-0hl-pesquisa-e-design-assertividade-do-motor | complete de fato (SUMMARY.md `status: complete`, gerou o ADR-015 que virou a Fase 6) — o auditor de milestone reporta "missing" por não casar um padrão esperado; falso positivo, não pendência real |
| quick_task | 260820-cap-pesquisa-qualidade-do-sinal-do-motor-de- | diretório vazio (sem PLAN/SUMMARY) — artefato abandonado do mesmo dia do 0hl, nunca teve conteúdo; seguro remover numa limpeza futura |

Items acknowledged and carried forward from previous milestone close (v1.0):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Backlog | 9 achados Baixo do REPORT-01 (C-06..C-10, C-17, C-18, C-28, C-29) | Not mapped to any phase — explicit backlog | v1.0 close |
| Decision | Números comerciais do plano gratuito/pago (ADR-010) | Pending Alex's business decision | v1.0 close |

## Session Continuity

Last session: 2026-08-23T21:04:28.675Z
Stopped at: Milestone v1.1 fechado e arquivado (tag v1.1)
Resume file: .planning/milestones/v1.1-phases/05-corre-o-m-dio-c-digo-gate-admin/05-08-SUMMARY.md

## Operator Next Steps

**Nenhum milestone novo aberto (decisão do Alex, 2026-08-23) — backlog documentado abaixo, sem processo formal até ele pedir.**

Backlog, em ordem de prioridade sugerida:

1. **Item 8 do checkpoint 08-05** — verificação ao vivo da entrada automática gated por um pregão inteiro com `entradaAuto` ligado; confirmar que só dispara nos setups elegíveis do momento e que o kill-switch está à mão antes de ligar. Único item que envolve execução automática real (dinheiro simulado).
2. **2 human-check da Fase 3** nunca confirmados ao vivo — ver `.planning/milestones/v1.1-phases/03-corre-o-cr-tico-alto/03-VERIFICATION.md` (card de status 3 badges reativo; mensagem de "sem permissão" no kill-switch do timing_watch).
3. **9 achados Baixo do REPORT-01** (C-06..C-10, C-17, C-18, C-28, C-29) — não mapeados a fase, ver `.planning/milestones/v1.0-phases/01-auditoria-diagn-stica-consolidada/REPORT-01.md`.
4. **`textDim` do tema claro falha WCAG AA** (4.20:1, achado colateral da Fase 4, fora do escopo do C-16 original).
5. **9 tickers com 404** no bootstrap do ledger de sinais (ELET3, BRFS3, ELET6, JBSS3, CRFB3, NTCO3, CPLE6, MRFG3, EMBR3) — prováveis renomeações/deslistagens, não investigado.
6. **ADR-010** (números comerciais do plano gratuito/pago) — decisão de negócio do Alex, não técnica; arquitetura já confirmada pronta (FIX-C33 fechou o último gap estrutural).

Quando o Alex quiser abrir milestone novo: `/gsd:new-milestone`.
