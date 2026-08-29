# Phase 9: Centralização de dados de mercado (mydata_client.py) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-27
**Phase:** 9-Centralização de dados de mercado (mydata_client.py)
**Areas discussed:** Camada de integração, Degradação quando mydata cai

---

## Todo cross-reference

| Todo | Fold? |
|------|-------|
| Medir rate-limit real do mydata antes de trocar fontes em produção | ✓ dobrado como critério de aceite |

---

## Camada de integração

**Q1 — mydata_client.py entra como provider dentro da interface CandleProvider existente ou como módulo separado com rotas próprias?**

| Option | Description | Selected |
|--------|-------------|----------|
| Provider dentro de CandleProvider | MydataProvider implementa a mesma interface que BrapiProvider/YahooProvider; get_history() roteia pra ele na fatia diária; reusa candle_cache.py e call sites existentes | ✓ |
| Módulo separado | Isolado, com call sites próprios; mais isolamento mas duplica lógica de cache/roteamento | |

**Q2 — Opções seguem o mesmo padrão (MydataOptionsProvider atrás da interface que options_provider_yahoo.py já usa)?**

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, mesma interface | options_api.py continua chamando o mesmo contrato; providerStatus continua bloqueando compra quando != "ok"; ADR-004 não reaberta | ✓ |
| Endpoint dedicado novo | Rota nova paralela, options_provider_yahoo.py inalterado | |

**Notas:** camada de integração ficou clara em duas perguntas — usuário pediu pra avançar sem mais rodadas.

---

## Degradação quando mydata cai

**Q1 — Se GET /v1/cotacoes falhar no refresh diário, o que acontece com o candle daquele dia?**

| Option | Description | Selected |
|--------|-------------|----------|
| Fallback pra brapi/Yahoo | Cai pro próximo da cadeia, candle registrado com `src` de proveniência; prioriza disponibilidade | ✓ |
| Erro explícito, sem fallback | Sem candle novo até mydata voltar; preserva fonte única sem misturar proveniências | |

**Q2 — Se o endpoint de opções do mydata falhar, cai pro Yahoo como fallback, ou vai direto pra providerStatus degradado?**

| Option | Description | Selected |
|--------|-------------|----------|
| Direto pra degradado, sem fallback | ADR-004 já bloqueia compra nesse estado; não reintroduz o Yahoo instável (401/403/429) que motivou a troca | ✓ |
| Fallback pro Yahoo | Tenta Yahoo antes de declarar degradado; reintroduz a fonte instável | |

**Notas:** assimetria deliberada entre candle diário (fallback ativo, disponibilidade prioritária) e opções (sem fallback, pra não reintroduzir a fonte que a migração elimina) — refletida em D-03/D-04 do CONTEXT.md.

---

## Claude's Discretion

- Nome exato do env var de credencial mydata (`MYDATA_URL`/`MYDATA_TOKEN`, seguindo padrão `BRAPI_TOKEN`/`BOLSAI_API_KEY`).
- Se `MydataBudget` entra nesta fase ou fica pra depois de medir o rate-limit real.
- Mecânica exata do job de refresh diário (batch 1×/dia vs. pass-through com TTL).

## Deferred Ideas

Nenhuma — discussão ficou dentro do escopo da fase.
