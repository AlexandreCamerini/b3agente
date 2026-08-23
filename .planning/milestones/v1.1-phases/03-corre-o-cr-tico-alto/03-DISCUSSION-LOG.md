# Phase 3: Correção Crítico + Alto - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-18
**Phase:** 3-Correção Crítico + Alto
**Areas discussed:** Escopo C-30×C-34, escopo C-19×C-21, escopo gating (C-31/C-32), canal de alerta C-37

---

## Escopo C-30 (orçamento brapi degradado)

| Option | Description | Selected |
|--------|-------------|----------|
| Só o alerta do degradado agora | Fecha o Crítico rápido; medidor completo fica pra fase 5 | ✓ |
| Construir o medidor completo já | Resolve C30 e C34 juntos, mesmo C34 sendo Médio | |

**User's choice:** Só o alerta agora

---

## Escopo C-19 (guardiões de appMode)

| Option | Description | Selected |
|--------|-------------|----------|
| Só o teste estrutural agora | Guardião de regressão sem migrar os 8 pontos | ✓ |
| Fazer a migração junto | Migra os 8 pontos pra `ctx.operador` na fase 3, adianta C-21 | |

**User's choice:** Só o teste estrutural

---

## Escopo gating (C-31/C-32)

| Option | Description | Selected |
|--------|-------------|----------|
| Corrigir sem ativar limite | `current_plan()` conectado, mas `PLAN_FREE` continua ilimitado | ✓ |
| Decidir os números junto | Sai do escopo técnico original | |

**User's choice:** Corrigir sem ativar limite

---

## Canal de alerta C-37

| Option | Description | Selected |
|--------|-------------|----------|
| Só indicador visual no painel | Mais simples, sem depender de push configurado | |
| Push via infra existente | Reusa `push.py` | ✓ (com nota do usuário) |

**User's choice:** Push via infra existente
**Notes:** "o admin também é um usuário, pode usar o push" — decisão explícita de reusar `push.py` em vez do caminho "mais simples" recomendado, porque o admin é tratado como qualquer outro usuário do sistema de notificação.

---

## Claude's Discretion

- Função nova para listar admins (`db.py`, query sobre `user_roles`) — não existe hoje, precisa ser criada; implementação exata fica a critério do planner
- Forma exata de expor a limitação de rastreio de duração do kill-switch (via env var não é rastreado) na UI/alerta

## Deferred Ideas

- C-34 (medidor completo) e C-21 (migração appMode) — confirmados como fase 5, não fase 3
- Ativação comercial real (recibo de loja, números do plano) — fora de escopo da milestone inteira
