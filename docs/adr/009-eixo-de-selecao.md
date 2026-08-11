# ADR-009: Eixo de seleção do Radar — regime + momentum relativo

**Status:** Aceito (Refactor A aplicado em 2026-08-11; origem: projeto
"Bolsa Análise técnica B3 setups" no claude.ai, via
[`docs/refactor/HANDOFF-claude-code.md`](../refactor/HANDOFF-claude-code.md))
**Data:** 2026-08-11 · **Decisor:** Alex
**Spec completa:** [`docs/refactor/ESPEC-A-eixo-selecao.md`](../refactor/ESPEC-A-eixo-selecao.md)
**Escopo:** N1 (Radar / `/api/scan`). Não toca N2/N3, guardrails CVM nem o contrato da UI.

## Problema

O Radar ordenava o universo por `confluencia` do melhor setup — que, pela
definição do próprio `setups.py`, mede **aderência do ativo a um padrão em
dados passados, nunca probabilidade de resultado**. O eixo primário do ranking
media aderência a padrão, não vantagem estatística — exatamente a confusão
taxa-de-acerto ≠ expectância que o CLAUDE.md proíbe. Agravantes: o roster que
domina esse ranking é price action de curto prazo (família com a evidência
acadêmica mais fraca), enquanto tendência e momentum — as famílias com melhor
evidência out-of-sample — só entravam como desempate; e o momentum
implementado era intra-ativo (RSI/MACD), não o relativo/cross-sectional, que é
o de melhor evidência. A hierarquia estava invertida.

## Decisão

Novo eixo primário de ordenação (`server/app/regime.py`, módulo puro):
**regime (tendência/lateral, via SMA200/ADX do Snapshot Técnico Único) +
momentum relativo cross-sectional (percentil de variação entre os ativos do
universo escaneado)**. Setups de price action deixam de ordenar o mercado e
viram **gatilho de timing**: só pontuam quando alinhados à direção do regime;
reversão à média só conta como gatilho em regime lateral.

Ordenação final (`regime.ranquear`, chamada após o `gather` — o percentil
precisa de todos os snapshots juntos):

```
(tier do regime ↓, momentum relativo ↓, gatilho alinhado ↓, confluência ↓, ticker ↑)
```

A `confluencia` cai de chave primária para **último desempate** — e permanece
no payload: o contrato da UI não muda. Campos novos por resultado: `regime`,
`momentumRelPct`, `momentumParcial`, `gatilhoAlinhado`, `radarScore` (score
exibido = momentum relativo + bônus de gatilho; o tier ordena mas não infla o
número mostrado). Nenhum número novo nasce na LLM — tudo é cálculo
determinístico sobre o snapshot.

## Degradação declarada (contrato da skill preservado)

- Janela sem 200 candles → filtro em SMA50, `confiavel=False` (declarado).
- Sem `change252` → `momentumParcial=True`, ranqueia por `change63`.
- Regime indefinido → tier 0, fim da fila; ausência de dado nunca promove.

## Guardiões

- `test_regime.py` (10 testes do módulo puro).
- `test_scan_rankeia_tolera_falha_e_tem_disclaimer` **atualizado com nota**
  (regra do repo: guardião não se apaga): protegia a ordenação por
  confluência; passa a proteger a tupla nova de ordenação + os campos novos +
  o contrato antigo da UI intacto.

## Dívidas assumidas (com dono)

1. **TODO — Fase A parte 2 (decisão do Alex pendente):** guardrail de família
   no prompt do N2 (ESPEC-A §6 — "setups da mesma família não somam
   confirmações independentes"), exige espelho byte a byte
   `server/app/defaults.py` ↔ `web/src/catalog.js` (o teste de paridade trava).
2. O percentil é relativo ao universo escaneado — universo pequeno/enviesado
   gera ranking enviesado; o eixo pressupõe universo amplo (IBOV+).
3. `radarScore` ainda não incorpora expectância medida — isso é o **B**
  (validação por regime, `ESPEC-B-validacao-regime.md`), que depende desta
  fase mergeada; o campo `regime.regime` é o que o B passará a persistir e
  segmentar (interlock A→B).
