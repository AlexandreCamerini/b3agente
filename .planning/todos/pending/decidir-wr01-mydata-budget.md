---
title: Decidir WR-01 — race condition em mydata_budget
priority: high
date: 2026-08-30
---

# Decidir WR-01 — race condition em mydata_budget

`mydata_budget.pode_gastar()`/`debita()` fazem check-then-debit
não-atômico — até 3 consumidores concorrentes possíveis (candle_provider,
options_provider_mydata, e o gate/pacer do scheduler). Decisão de
arquitetura pendente desde o fechamento do v1.2 (2026-08-28), registrada em
`.planning/STATE.md` § Deferred Items.

O Alex pediu para resolver "depois" (2026-08-29) — não implementar sem
apresentar opções antes.

**Opções a apresentar quando isso for retomado:** lock (serializar
check+debit), fila (enfileirar requisições concorrentes), ou aceitar o
risco (medir taxa de estouro real antes de investir em correção).

**Por que importa agora:** é um dos dois bloqueios reais da virada de
produção `B3_OPTIONS_PROVIDER=mydata`/`B3_CANDLE_PROVIDER=mydata` — a fase
"Opções lastreadas" (venda coberta + put de proteção) fica estruturalmente
pronta mas dormente até essa virada acontecer. Ver
`.planning/notes/opcoes-mecanica-lastreada-decisoes.md`.
