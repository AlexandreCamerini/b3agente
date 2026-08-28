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

## Resultado (2026-08-27) — PARCIAL, ainda PENDING

Medido offline (Plano 09-04, `scripts/medir-mydata.py --fases projecao`):
volume diário CABE (548 de 2.000/dia projetado, 72,6% de folga), **pico por
minuto NÃO CABE** (148 de 60/min projetado — `scanner.MIN_FETCH_GAP_S`
atual não é apertado o suficiente para o teto do mydata). Item 2
(`provento_b3`) confirmado: rota construída, falta só a primeira carga de
produção do lado do cvm-financas. Perna ao vivo (autenticação real da chave
`f00b4554`, escopo `fonte:b3`) **BLOQUEADA** — `MYDATA_TOKEN` ausente no
ambiente de execução deste plano. Números completos e plano de ação em
[docs/MEDICAO-Mydata-2026-08-27.md](../../../docs/MEDICAO-Mydata-2026-08-27.md).

Este TODO continua em `pending/` (não vai para `done/`): o item 1 (mapear
volume real) está resolvido pela projeção, mas o item 3 (confirmar a chave
autenticando de fato, decidir se cabe/precisa mitigação) só fecha depois da
perna ao vivo rodar com `MYDATA_TOKEN` real e, se o pico por minuto continuar
NÃO CABENDO, da mitigação do gate de espaçamento (item 1 do "Plano de ação"
do documento) ser aplicada ou decidida.

## Resultado (2026-08-28) — autenticação confirmada, mitigação do pico ainda pendente

Perna ao vivo rodada pelo Alex em 2026-08-28T01:57:52Z, fora do ciclo GSD da
fase 9 (`MYDATA_TOKEN` real exportado localmente, nunca commitado): 5
tickers × 2 rotas = 10 chamadas reais contra `mydata.acamerini.app`, `erro:
null` em todas, `precosPresentes=true` nas 5 de `cotacoes` (escopo
`fonte:b3` confirmado ativo na chave `f00b4554`). Reconciliação de cota
bateu com o contador local (10 chamadas, `X-Quota-Restante` final=58 de
60). Números completos em
[docs/MEDICAO-Mydata-2026-08-27.md §4/§5](../../../docs/MEDICAO-Mydata-2026-08-27.md#4-amostra-ao-vivo).

**Item 3 agora tem metade fechada:** a sub-pergunta "a chave autentica de
fato?" — **sim, confirmado**. A sub-pergunta "precisa mitigação?" —
**sim, continua precisando**: a amostra ao vivo usou só 10 chamadas em
~7,5s, não testa rajada equivalente ao padrão real do scanner, então não
muda o veredito de pico/min (148 vs 60/min) da projeção. Este TODO segue em
`pending/` até a mitigação (gate de espaçamento sensível ao provedor, ou
elevar `MIN_FETCH_GAP_S` global) ser aplicada ou decidida — é o que falta
para reabrir o checkpoint `adiar` do Plano 09-06 com veredito `CABE` na
mesa.
