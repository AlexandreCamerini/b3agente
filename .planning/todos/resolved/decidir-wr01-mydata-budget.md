---
title: Decidir WR-01 — race condition em mydata_budget
priority: high
date: 2026-08-30
resolved: 2026-08-31
resolution: "Alex escolheu 'Lock'. Implementado: MYDATA_BUDGET_LOCK (threading.RLock) protege pode_gastar()/debita() em server/app/mydata_budget.py, mesmo padrão de store.ORDER_LOCK/WATCHLIST_LOCK. Nova função reservar(n) faz check+debit atômico; options_provider_mydata._debita() foi migrada pra usar reservar() nos dois pontos de commit real (fecha o TOCTOU, não só a corrupção do contador). candle_provider.py manteve pode_gastar()/debita() como estavam (agora internamente protegidos pelo lock) sem reestruturar a cadeia de fallback multi-provedor — risco/benefício não justificou mexer numa lógica mais arriscada e mais testada pra uma corrida que hoje não tem tráfego real (mydata não está em produção). Testes novos: test_debitos_concorrentes_nao_perdem_incremento e test_reservar_sob_corrida_nunca_ultrapassa_a_cota_e_nunca_debita_em_false (test_mydata_budget.py), 3 asserções de test_options_provider_mydata.py atualizadas pro novo padrão de reavaliação atômica. Suíte canônica verde (1816 passed/1 skipped + todos os web/tests)."
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
