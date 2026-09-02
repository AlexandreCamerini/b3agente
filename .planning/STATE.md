---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Cap comercial (plano gratuito)
status: Awaiting next milestone
stopped_at: Phase 14 verificada em produção, WR-01 resolvido (PR #28)
last_updated: "2026-08-31T22:15:00.000Z"
last_activity: 2026-09-02 -- Quick task 260901-u2c: escopo v1 da biblioteca de setups de opções fechado (venda coberta+put+collar), ressalva de espaço pra MCP futuro registrada
progress:
  total_phases: 2
  completed_phases: 2
  total_plans: 8
  completed_plans: 8
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-01)

**Core value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.
**Current focus:** Milestone complete; Phase 14 (standalone) também completa

## Current Position

Phase: 14 (op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e) — COMPLETE (standalone, sem milestone ativo)
Plan: 8 of 8 (+ 2 bugfixes de checkpoint)
Status: Checkpoint humano aprovado — fase dormente em produção até B3_OPTIONS_PROVIDER=mydata
Last activity: 2026-08-31 -- Phase 14 completa, checkpoint humano aprovado ao vivo (2 bugs achados e corrigidos)

## Performance Metrics

**Velocity:**

- Total plans completed: 25 (v1.0) + 44 (v1.1) + 6 (Phase 9, standalone) + 8 (v1.2)
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
| 13 | 5 | - | - |

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

- Phase 14 added (2026-08-30, standalone, sem milestone ativo): Opções
  lastreadas — venda coberta e put de proteção sobre posições da carteira.
  Origem: `/gsd-explore` sobre funcionalidades de opções. Redesenho do zero
  (não reaproveita put_bridge/put_lifecycle nem setOptionStop/setOptionAlvo
  existentes). Construída dormente — ativa quando `B3_OPTIONS_PROVIDER=
  mydata` virar produção. Decisões completas em
  `.planning/notes/opcoes-mecanica-lastreada-decisoes.md`.

- Phase 14 encerrada (2026-08-31): WR-01 resolvido (PR #28, lock em
  `mydata_budget.py`) e `B3_OPTIONS_PROVIDER=mydata` virou produção,
  verificado ao vivo (`GET /api/options/chain/PETR4` → `providerStatus:
  "ok"`, cadeia real com Greeks). `B3_CANDLE_PROVIDER` continua `brapi`
  por decisão explícita do Alex — ADR-008 intacto, cenário de pico/min de
  candle em lote não se aplica mais. Dois incidentes de configuração no
  Railway (variáveis coladas juntas; token inválido) achados e corrigidos
  durante a verificação, sem relação com o código da fase. Fechamento
  completo em `docs/adr/023-opcoes-lastreadas.md` (Nota aditiva).

### Pending Todos

- `decidir-wr01-mydata-budget.md` (priority high) — race condition
  check-then-debit em `mydata_budget`, um dos dois bloqueios da virada de
  produção do mydata que a Fase 14 depende para deixar de ser dormente.

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
| 260901-1ak | Sincronizar PROJECT.md Active: remover 2 itens stale já resolvidos (mydata cutover, WR-01) | 2026-09-01 | 8509f5e | Verify gate passou (contagem 7→5, diff só-remoção em PROJECT.md, data de referência sincronizada em STATE.md) | [260901-1ak-sincronizar-project-md-active-remover-2-](./quick/260901-1ak-sincronizar-project-md-active-remover-2-/) |
| 260901-2da | Atualizar mydata_client.py: BASE_DEFAULT para o domínio canônico mydata.semente.dev | 2026-09-01 | c2f30bf | Verify gate passou (zero refs ao domínio antigo, py_compile limpo, pytest test_mydata_client.py 40 passed, diff exatamente 3 arquivos) | [260901-2da-atualizar-mydata-client-py-base-default-](./quick/260901-2da-atualizar-mydata-client-py-base-default-/) |
| 260901-r5t | Registrar decisão: Alex escolheu Candidato A (aba própria Opções) na navegação de Opções v2 | 2026-09-01 | da9a118 | Verify gate passou (17 checks, diff restrito a .planning/, zero código tocado) | [260901-r5t-registrar-decis-o-alex-escolheu-candidat](./quick/260901-r5t-registrar-decis-o-alex-escolheu-candidat/) |
| 260901-u2c | Registrar decisão: escopo v1 biblioteca de setups (venda coberta+put+collar), espaço pra MCP futuro | 2026-09-02 | f29490b | Verify gate passou (22 checks, diff restrito a .planning/) — executor sofreu falha de API pós-commit, orquestrador escreveu o SUMMARY.md e completou o merge | [260901-u2c-registrar-decis-o-escopo-v1-biblioteca-d](./quick/260901-u2c-registrar-decis-o-escopo-v1-biblioteca-d/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close (v1.2 → v1.3):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Backlog | 9 achados Baixo do REPORT-01 (C-06..C-10, C-17, C-18, C-28, C-29) | Not mapped to any phase — explicit backlog | v1.0 close |
| verification_gap | Item 8 do checkpoint 08-05 — verificação ao vivo de `entradaAuto` por um pregão inteiro | human_needed | v1.1 close |
| verification_gap | 2 human-checks da Fase 3 (card de status 3 badges reativo; mensagem de "sem permissão" do kill-switch) | human_needed | v1.1 close |
| Production cutover (parcial, resolvido) | Virada de `B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER=mydata` (Fase 9, checkpoint `adiar`) | Resolvido 2026-08-31, com escopo reduzido por decisão do Alex: só `B3_OPTIONS_PROVIDER=mydata` virou produção (verificado ao vivo, `providerStatus: "ok"`). `B3_CANDLE_PROVIDER` continua `brapi` — o cenário de pico/min de 148/min (candle em lote) não se aplica mais, já que candle não migrou. Ver ADR-023 Nota aditiva. | Fase 9 close (2026-08-27), resolvido 2026-08-31 |
| WR-01 (arquitetura, resolvido) | Race condition check-then-debit em `mydata_budget` — até 3 consumidores concorrentes potenciais | Resolvido 2026-08-31: Alex escolheu "Lock" — `MYDATA_BUDGET_LOCK` + `reservar()` atômico, migrado em `options_provider_mydata.py`, PR #28. Ver `.planning/todos/resolved/decidir-wr01-mydata-budget.md`. | v1.2 close (2026-08-28), resolvido 2026-08-31 |
| v2 requirements | CAP-08..11 (loja/IAP, preço/moeda, IA gerenciada sem BYOK como paga, alvo dinâmico exclusivo do pago) | Deferred to future release — depende da decisão comercial de venda em si | v1.3 roadmap (2026-08-29) |
| uat_gap (stale) | Fase 12 `12-HUMAN-UAT.md` | Já `resolved`, 0 cenários pendentes — auditoria só sinaliza a existência do arquivo, não um gap real | v1.3 close (2026-08-31) |
| verification_gap (stale) | Fase 12 `12-VERIFICATION.md` (`human_needed`) | O gap real (bypass do cap no iOS) foi dobrado no escopo da Fase 13 (CAP-12) e fechado lá — o arquivo da Fase 12 não foi reaberto/reexecutado, só o achado foi resolvido a jusante | v1.3 close (2026-08-31) |
| Pending todo (resolvido, movido) | `cap-watchlist-robustez-code-review.md` (WR-01/02/03 do 12-REVIEW.md) | Já corrigido em 3 commits atômicos, mergeado via PR #26 antes do fechamento — confirmado no código e movido pra `todos/resolved/` em 2026-08-31 | v1.3 close (2026-08-31), movido 2026-08-31 |
| Pending todo (aberto, prioridade rebaixada) | `medir-rate-limit-mydata.md` (priority medium, era high) | Escopo reduzido em 2026-08-31: só options foi pro mydata, candle ficou em `brapi` — o cenário de pico/min de lote não se aplica mais. Ainda aberto pra acompanhar volume real de tráfego de opções se crescer. | Fase 9 close (2026-08-27), rebaixado 2026-08-31 |
| Quick tasks (auditoria desatualizada) | 7 quick-tasks com status `missing` (2026-08-20 a 2026-08-30, inclui `260830-eqm-fase-4-adr-23-boris-relying-party-do-sem` de outra sessão concorrente já mergeada, PR #27) | Sem relação com o escopo do v1.3 (cap comercial) — a ferramenta de auditoria não localiza um artefato de status esperado pra esses slugs antigos; nenhum representa trabalho pendente conhecido | v1.3 close (2026-08-31) |

## Session Continuity

Last session: 2026-08-29T22:57:56.315Z
Stopped at: Phase 13 UI-SPEC approved
Resume file: .planning/phases/13-uso-real-vis-vel-na-interface-enforcement-no-ios/13-UI-SPEC.md

## Operator Next Steps

- Start the next milestone with /gsd-new-milestone
