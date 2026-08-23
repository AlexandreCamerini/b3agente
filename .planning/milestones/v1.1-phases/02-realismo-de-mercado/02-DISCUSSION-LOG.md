# Phase 2: Realismo de Mercado - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-18
**Phase:** 2-Realismo de Mercado
**Areas discussed:** Precisão do horário de execução, reserva de caixa, reserva de posição, ordens múltiplas, onde exibir status/pendentes

---

## Todas as áreas (delegadas)

O Alex dispensou a discussão item a item: "pode decidir a solução mais fácil
de implementar sem prejuízo ao funcionamento básico. não precisamos de
precisão total."

| Área | Decisão (critério: mais simples, sem quebrar o básico) |
|------|------|
| Precisão do horário de execução | Primeira passada do scheduler (300s) após 10:00 — sem gatilho de precisão maior |
| Reserva de caixa | Debita no pedido (reusa código de débito existente), devolve se cancelar — sem campo novo "reservado" |
| Reserva de posição (venda) | Mesma lógica — subtrai a quantidade no pedido, devolve se cancelar |
| Múltiplas ordens pendentes no mesmo ticker | Permitido, sem bloqueio, processa na ordem de criação |
| Onde mostrar status de mercado | Topbar (visível em toda aba) |
| Onde mostrar ordens pendentes | Dentro da `HistoricoScreen` existente, seção "Pendentes" |

**User's choice:** Delegado ao critério de simplicidade
**Notes:** Nenhuma alternativa foi apresentada formalmente via AskUserQuestion — o Alex pediu pra eu decidir direto, então as opções acima refletem a decisão tomada, não um menu apresentado.

---

## Claude's Discretion

- Texto exato do badge de status de mercado (seguir vocabulário por modo, `copy.js`)
- Nome do campo/enum do novo status "pendente" no modelo de dados
- Timing exato da devolução de caixa/posição ao cancelar (decisão: imediato, na própria ação de cancelar)

## Deferred Ideas

Nenhuma — discussão ficou dentro do escopo da fase.
