# MEDIÇÃO — brapi plano gratuito com token real (Fase 0 do qa/43)

**Data:** 2026-08-11, 01:31 BRT (fora de pregão) · **Método:** `railway run`
injetando `BRAPI_TOKEN` do serviço num script stdlib local (token nunca
impresso) · **Custo:** 8 requisições da cota · **Script:** scratchpad da
sessão (descartável; fixture de payload a gravar na Fase 1)

## Resultados

| # | Pergunta (qa/43 Fase 0) | Resultado | Evidência literal |
|---|---|---|---|
| 1 | Cota real | **15.000 confirmada** via header; janela de reset **não exposta** nos headers (`x-ratelimit-reset` ausente) — presumida mensal, confirmar no painel da conta | `x-ratelimit-limit: 15000`, `x-ratelimit-remaining: 14999 → 14998` |
| 1b | **Requisição recusada por plano CONSOME cota** | o batch recusado (400) debitou 1 requisição | remaining caiu para 14999 na própria recusa |
| 2 | Tickers por requisição | **1** | `400 {"error":true,"code":"QUOTES_PER_REQUEST_EXCEEDED","message":"Seu plano permite no máximo 1 ativo(s) por requisição. Você enviou 3."}` |
| 3 | Intervalos no free | **só `1d`** | `400 {"code":"INVALID_INTERVAL","message":"O intervalo \"15m\" não está disponível no seu plano. Intervalos permitidos: 1d"}` |
| 4 | Range máximo no free | **`3mo`** — nem `6mo`/`1y`/`2y` passam | `400 {"code":"INVALID_RANGE","message":"O range \"2y\" não está disponível no seu plano. Ranges permitidos: 1d, 5d, 1mo, 3mo"}` |
| 5 | Delay real do spot | **não confirmado** — medição feita à 01:31 BRT; `regularMarketTime` do WEGE3 = 2026-08-10 18:31 BRT (foto pós-fechamento coerente). Repetir a amostragem de 1h **em pregão** | `time: 2026-08-10T21:31:30Z` |
| 6 | `adjustedClose` vs `close` | **divergem de fato**: ITSA4 3mo/1d → 25 de 62 velas com diferença (ex.: 13/05 close 12,85 vs adj 12,6901) | payload real |
| — | Diário fora do sandbox | ok: WEGE3 `1mo/1d` → 21 velas, `usedInterval: 1d`, epoch meia-noite BRT | HTTP 200 |
| — | Envelope de erro | **duas formas**: violação de plano `{"error":true,"message","code"}` e validação ZodError `{"success":false,"error":{"issues":[...]}}` | capturados |

## Consequências para o desenho (deltas sobre ADR-008/qa/43)

1. **Validação client-side ANTES de chamar é obrigatória** — recusa por plano
   debita cota. O roteador não pode "tentar e cair no erro": intervalo ≠ `1d`
   ou range ∉ {`1d`,`5d`,`1mo`,`3mo`} vai **direto ao Yahoo, sem tocar a
   brapi**. Os códigos `INVALID_INTERVAL`/`INVALID_RANGE`/
   `QUOTES_PER_REQUEST_EXCEEDED` viram guardas de teste, não caminho normal.
2. **Warmup e histórico longo ficam no Yahoo em definitivo** (free não tem
   `1y`/`2y`): a brapi free serve **spot + delta diário de até 3mo**. O
   `FETCH_RANGE=2y` e o período default `1y` do app continuam 100% Yahoo.
   A hipótese do qa/43 Fase 4 ("warmup pode ir ao Yahoo") vira regra.
3. **1 ticker/req confirma o orçamento por unidade** do ADR-008 (fatias
   dimensionadas com essa hipótese — nada muda nos números).
4. **Merge entre fontes proibido, confirmado com dado real** — 40% das velas
   do ITSA4 divergem entre `close` e `adjustedClose`; misturar série brapi com
   série Yahoo corromperia médias e retornos em silêncio.
5. **Monitor de cota de graça**: `x-ratelimit-remaining` vem em toda resposta —
   o contador local do orçamento se **reconcilia** com o header (o header é a
   verdade; o contador local é a previsão). Expor ambos em `/api/status`.

## Pendências da Fase 0

- [ ] Delay real do spot em pregão (amostragem de 1h, dia útil 10h–17h BRT).
- [ ] Janela de reset da cota (mensal? por dia?) — painel da conta brapi ou
  observação do `remaining` ao virar o dia/mês.

Gate do qa/43: **aprovado com ressalva** — a arquitetura fica de pé (spot +
delta ≤3mo na brapi; todo o resto Yahoo), e a ressalva é o delay, que decide
apenas o TTL da fatia de spot, não a direção.
