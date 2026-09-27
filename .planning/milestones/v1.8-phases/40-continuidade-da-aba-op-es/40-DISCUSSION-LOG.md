# Phase 40: Continuidade da aba Opções - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-25
**Phase:** 40-continuidade-da-aba-op-es
**Areas discussed:** Mecanismo de sobrevivência, Escopo do que é lembrado, Interação com o deep-link, Expiração da memória, Comportamento pós-restauração (originalmente proposto pelo Alex como "rever UX/UI da aba Opções")

---

## Mecanismo de sobrevivência

| Option | Description | Selected |
|--------|-------------|----------|
| Levantar pro App.jsx | Mesmo padrão do `opcoesAbaInicial` — sobrevive na sessão atual, sem tocar nos stores | ✓ |
| Persistência real (deviceStore/serverStore) | Sobrevive a reload/restart do app, exige campo espelhado nos dois stores (paridade) | |

**User's choice:** Levantar pro App.jsx (recomendado)
**Notes:** Decisão explícita de não acionar o guardrail de paridade dos stores por um ganho (sobreviver a reload) que o requirement não pediu.

---

## Escopo do que é lembrado

| Option | Description | Selected |
|--------|-------------|----------|
| Só o mínimo (ticker + aba ativa) | Sheet de Vigias, expansões e filtros de Comparar sempre voltam default | ✓ |
| Também vencimento/comparação de Montar | | |
| Também se o sheet de Vigias estava aberto | | |

**User's choice:** Só o mínimo (recomendado)
**Notes:** Menos estado pra sincronizar, evita "estado zumbi" (ex. sheet lembrado aberto sem dado vivo por trás).

---

## Interação com o deep-link

| Option | Description | Selected |
|--------|-------------|----------|
| Deep-link sempre vence | Intenção explícita do toque em Posições > estado lembrado passivamente | ✓ |
| Só vence se não houver nada lembrado | | |

**User's choice:** Deep-link sempre vence (recomendado)

---

## Expiração da memória

| Option | Description | Selected |
|--------|-------------|----------|
| Vale a sessão inteira | Mecanismo em memória já zera sozinho ao fechar/recarregar | ✓ |
| Expira em gatilho específico (ex. logout) | | |

**User's choice:** Vale a sessão inteira (recomendado)
**Notes:** Registrada como nota pro planner: se o fluxo de logout já limpa estado semelhante hoje, replicar por consistência; senão, não inventar tratamento novo.

---

## Comportamento pós-restauração

**Contexto:** o Alex inicialmente pediu para discutir "rever UX/UI da aba Opções" — pergunta de esclarecimento confirmou que era sobre o comportamento da restauração especificamente, não uma revisão visual geral da aba (que foi registrada em Deferred Ideas).

| Option | Description | Selected |
|--------|-------------|----------|
| Silencioso, sem indicar nada | Restaura direto, sem salto visual nem aviso | ✓ |
| Sinal sutil (toast/microtexto) | Mais explícito, elemento de UI novo | |

**User's choice:** Silencioso, sem indicar nada (recomendado)

---

## Claude's Discretion

Nenhuma — todas as 5 áreas tiveram decisão explícita do Alex.

## Deferred Ideas

- **Auditoria/revisão de UX-UI geral da aba Opções** — pedido inicial ambíguo, esclarecido como fora de escopo desta fase; se priorizado no futuro, vira fase própria (mesmo tratamento da auditoria "Jornada de Decisão", registrada como v1.9 na fila).
- **Persistência real (deviceStore/serverStore)** do estado da aba Opções — descartada nesta fase, registrada como upgrade futuro possível.
