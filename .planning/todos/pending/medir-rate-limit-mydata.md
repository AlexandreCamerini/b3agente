---
title: Medir rate-limit real do mydata antes de trocar fontes em produção
date: 2026-08-27
priority: high
---

# Medir rate-limit real do mydata (cvm-financas) antes de migrar

A chave de produção do BolsIA no cvm-financas (`f00b4554`, escopo
`negociacao_b3`+`provento_b3`) tem limite **60/min · 2.000/dia**. A decisão de
migrar COTAHIST diário e Opções para `mydata_client.py` (ver
[nota de centralização](../../notes/boris-pp-centralizacao-dados-mydata.md))
assume que esse limite é suficiente, mas isso não foi medido — é inferência de
arquitetura (COTAHIST é EOD, então o padrão natural é refresh em lote 1×/dia +
cache local, mesmo padrão que ADR-019 já usava).

## O que fazer

1. Antes de implementar `mydata_client.py` em produção: mapear o volume real
   de chamadas necessário — quantos tickers no universo escaneado (ADR-001
   cita 65), com que frequência o refresh diário roda, e quantas chamadas de
   opções por ciclo (on-demand por usuário vs. varredura).
2. Confirmar se `provento_b3` já teve a primeira carga de produção completa
   do lado do cvm-financas (`docs/contrato-consumidor.md:151` marcava como
   pendente em 2026-08-27) — se for usar essa classe também.
3. Se o limite for insuficiente, negociar aumento de quota com o lado
   cvm-financas antes de desligar Yahoo/brapi nas fatias migradas — nunca
   trocar de fonte sem fallback confirmado (princípio 4 do CLAUDE.md: nunca
   inventar valor quando a fonte falha).

Vira critério de aceite da fase "Centralização de dados de mercado
(`mydata_client.py`)" no ROADMAP, não decisão bloqueada agora.
