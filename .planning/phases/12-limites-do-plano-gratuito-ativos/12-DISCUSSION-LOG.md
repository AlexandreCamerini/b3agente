# Phase 12: Limites do plano gratuito ativos - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-29
**Phase:** 12-limites-do-plano-gratuito-ativos
**Areas discussed:** Gate de watchlist (bypass do PUT), grandfather clause, copy de recusa, conta anônima
**Mode:** `--auto` (respostas recomendadas escolhidas sem perguntar; log completo abaixo)

---

## Gate de watchlist — PUT /api/watchlist bypassa o limite

Scout do código encontrou que `POST /api/watchlist/add` já chama `plan.can_add_ticker`
corretamente, mas `PUT /api/watchlist` (usado pelo frontend em dois fluxos de
adicionar ticker — quick-add e seleção em massa do catálogo) não passa por
nenhum gate.

| Option | Description | Selected |
|--------|-------------|----------|
| Deixar como está (só fechar POST) | CAP-01 fica furado — dá pra passar do limite pelo catálogo em massa | |
| Gatear PUT sempre (bloqueia até redução) | Simples, mas bloquearia reordenar/remover — pior UX sem necessidade | |
| Gatear PUT só quando cresce além do limite | Fecha o furo sem afetar reordenação/remoção | ✓ [auto] recomendado |

**Selecionado:** `[auto]` Gatear `PUT /api/watchlist` só quando `len(tickers_novos) > len(watchlist_atual)` e o resultado ultrapassa `max_watchlist` — nunca bloqueia remoção/reordenação (recommended default).
**Notes:** Achado de scout, não pergunta original do usuário — decisão automática registrada pra auditoria.

---

## Grandfather clause — usuário já acima do novo limite

| Option | Description | Selected |
|--------|-------------|----------|
| Forçar remoção até caber no limite | Destrutivo, surpresa ruim pra quem já tinha mais de 10 ativos | |
| Grandfather — mantém o que já tem, só bloqueia crescer | Não-destrutivo, consistente com ADR-010 ("ativação reversível e gradual") | ✓ [auto] recomendado |

**Selecionado:** `[auto]` Grandfather — usuário que já ultrapassa o limite mantém tudo, só não consegue adicionar mais.

---

## Copy de recusa (CAP-07)

| Option | Description | Selected |
|--------|-------------|----------|
| Manter texto atual de `can_add_ticker` | Tem CTA de upgrade ("Faça upgrade para adicionar mais") — viola princípio 8 | |
| Revisar pro padrão de `can_analyze` (só fato + motivo) | `can_analyze` já está conforme; alinhar os dois textos | ✓ [auto] recomendado |

**Selecionado:** `[auto]` Novo texto de `can_add_ticker`: "Você atingiu o limite de {limit} ativos do plano {id}." — mesmo padrão de `can_analyze`, sem CTA.

---

## Conta anônima

| Option | Description | Selected |
|--------|-------------|----------|
| Criar exceção pra conta anônima (sem limite) | Contradiria o próprio objetivo do milestone | |
| Manter fallback `ACTIVE_PLAN` (= free) já existente | Já é o comportamento atual, nenhuma mudança necessária | ✓ [auto] recomendado |

**Selecionado:** `[auto]` Sem mudança — `current_plan(None)` já cai em `ACTIVE_PLAN`/`PLAN_FREE`, os limites valem igual.

---

## Claude's Discretion

- Redação exata dos testes de comportamento que provam D-02/D-03 (cobertura: PUT bloqueia crescimento, PUT nunca bloqueia redução, usuário grandfathered não perde ativos)

## Deferred Ideas

- Expor uso/limite na UI — Fase 13 inteira
- Loja/IAP, preço, features avançadas do pago — fora do milestone v1.3 (CAP-08..11)
- Todo `medir-rate-limit-mydata.md` (match automático score 0.6) — revisado e descartado como falso positivo, domínio não relacionado (mydata rate-limit ≠ cap comercial)
