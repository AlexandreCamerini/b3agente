# qa/39 — Revisão final de QA (go/no-go para testes)

> Build: **F9-20260710-12**. Orquestração: 3 revisores especializados em
> paralelo (persona operador sênior `analise-tecnica-b3`), com **verificação
> numérica executada** (scripts com referências canônicas independentes) e
> confirmação adversarial dos achados críticos antes de qualquer correção.
> Regra: achado não confirmado não reprova release.

## Veredito consolidado: **GO para testes** (após as correções desta rodada)

| Área | Antes | Correções | Depois |
|---|---|---|---|
| Indicadores (`indicators.py`) | ✅ aprovado (0 P0) | RSI flat → 50 | ✅ |
| Setups/planos (`setups.py`) | ❌ 1 P1 + 2 P2 críticos | todos corrigidos | ✅ |
| Prompts/enforcement (`llm.py`/`kpi.py`) | ⚠️ Operador com 4 P1 | todos corrigidos | ✅ |
| KPIs eficiência (`analysis_outcomes.py`) | ✅ fórmulas corretas | guard de expiração | ✅ |
| Operacional (suítes/produção) | ✅ | — | ✅ |

## O que os revisores CONFIRMARAM correto (sem mudança)

- **Indicadores bit-a-bit canônicos**: RSI (Wilder), MACD 12/26/9, EMA/SMA,
  Bollinger 20/2σ, Estocástico 14/3, DI±, OBV — verificados contra referência
  independente em 60 candles sintéticos (tol 1e-9). ATR/ADX com desvio de
  seed que converge a <1e-5% com histórico real.
- **Setups fiéis às definições clássicas** (9.1/9.2/9.3 Stormer, IFR2 Connors
  adaptação BR disclosed, PFR, 123, Inside Bar, Larry Williams, Ponto
  Contínuo modernizado com ADX). Confluência matematicamente sã.
- **Gate R:R 1,5:1 sem exceção** (1,4 reprova; 1,5 exato aprova; entrada a
  mercado usa risco REAL). Preço esticado >0,5R vira não-perseguir.
- **Avaliação pós-fato conservadora**: stop+alvo no mesmo candle → stop;
  R-múltiplo de venda com sinal certo; expectância/profit factor/drawdown
  com fórmulas corretas (verificado numericamente).
- **Limites regulatórios presentes em TODOS os prompts** (nunca prometer,
  execução do usuário, invalidação sempre, não-operar como posição). N1 era
  o caminho mais maduro (prompt + parse + validação por modo + teto imposto).
- Injection: risco baixo (dados via json.dumps, ticker normalizado, guardrails
  depois da skill editável no system).

## Bugs corrigidos nesta rodada (todos com reprodução + guardião)

**setups.py**
1. **P1 — alvo do lado errado passava no gate**: `abs()` no rr2 aceitava
   COMPRA com alvo2 ABAIXO do stop como "R:R 1,6". Agora: alvo2 do lado do
   lucro obrigatório, senão NÃO OPERAR.
2. **P2 — alvo de venda negativo**: projeção 2R sem piso publicava alvo
   −R$1,00 (dado fisicamente impossível). Agora: alvo ≤ 0 → NÃO OPERAR.
3. **P2 — "parcial em 1R" falsa na entrada a mercado**: alvo1 ancorado no
   gatilho dava 0,43R da entrada real com o motivo prometendo 1R. Agora
   `alvo1 = entrada ± risco_real` (rr1 ≡ 1,0 — promessa e número iguais).
4. **P2 — setup legado sem níveis no topo matava o plano**: agora
   `plano_do_resultado` prioriza o melhor direcional COM gatilho/invalidação.

**llm.py / kpi.py (enforcement dos prompts)**
5. **P1-1 — vocabulário da mesa destruído no N2**: a normalização educacional
   reescrevia COMPRAR→"Estudar alta" e derrubava "AGUARDAR CONFIRMAÇÃO".
   Agora `analyze_structured` re-mapeia pós-parse para o enum PRO (a UI já
   tinha os estilos prontos).
6. **P1-2 — teto de convicção não imposto no N2**: "Muito Alto" passava sem
   2º timeframe. Agora cap server-side (→ "Médio") + linha no FORMAT.
7. **P1-3 — R:R do N3 não recomputado**: o gate usava o valor DECLARADO pelo
   modelo. Agora `parse_carteira` recomputa `|alvo−preço|/|preço−stop|`
   (vale nos 2 lados) e força `rrDesfavoravel` < 1,5.
8. **P1-4 — N3 estudo sem guardrails do servidor**: o system era só o prompt
   editável do usuário. Agora GUARDRAILS educacional é apêndice incondicional.
9. **Robustez**: `_deep_fallback` agora passa pela validação por modo (não
   vaza "Monitorar" na mesa); default de `confianca` ausente/ inválida virou
   "baixa" (o teto tinha virado piso).

**prompts default (defaults.py + espelho catalog.js)**
10. **P2 — convite a dado não fornecido** ("complemente com seu conhecimento
    geral") substituído por proibição explícita + prefixo `[contexto geral]`.
11. **R:R mínimo 1,5:1 agora explícito** no prompt educacional da carteira.

**indicators.py / analysis_outcomes.py**
12. **P2 — RSI de série flat = 100** ("sobrecomprado" em papel parado) → 50.
13. **P2 — candle de expiração sem close** levantava TypeError → mantém pendente.

## Aceitos sem correção (documentados, não bloqueiam)

- Seeds de ATR/ADX (desvio <1e-5% com 200+ candles) — comentário é suficiente.
- Arredondamento a 2 casas degrada penny stocks (<R$1) — irrelevante no universo.
- `taxaAcerto` geral do painel não aplica MIN_N (a regra do produto vale para
  células de segmentação; o card mostra o `n` ao lado) — decisão de contrato.
- IFR2 com stop por ATR (Connors não usa stop) — disclosed no docstring.
- `/api/analyze` da aba Mercado ignora o modo (sempre educacional) — degrada
  para o lado seguro; alinhamento com a mesa fica para uma rodada de UX.
- N2 sem fallback estruturado p/ JSON truncado (equivalente ao `_deep_fallback`
  do N1) — mitigado pelo parse tolerante; melhoria futura.

## Guardiões novos

`server/tests/test_qa39.py` (10 casos): alvo lado errado, alvo negativo,
alvo1=1R da entrada real, plano prioriza direcional com níveis, RSI flat,
expiração sem close, vocabulário PRO no N2 (com LLM fake), teto de convicção,
R:R recomputado no N3, guardrails no N3 estudo + enum PRO no mapa.

## Validação

**272 pytest** (262+10) + suítes web (2 ambientais) + parse OK. Espelho
defaults.py ↔ catalog.js editado nos DOIS lados. Produção viva no build
anterior; este build sobe via entregar.sh.

## Hard stop (aparelho, build F9-20260710-12)

1. Modo Operador → N2 de um ativo: a decisão aparece no vocabulário da MESA
   (COMPRAR/VENDER/AGUARDAR CONFIRMAÇÃO/NÃO OPERAR), nunca "Estudar alta".
2. Convicção nunca aparece como "Muito Alto"/"Alto" (teto Médio, timeframe único).
3. Radar/Mesa: nenhum card com alvo abaixo do stop ou alvo negativo.
4. Popup stop/alvo: cenário com R:R incoerente com os números acende
   "desfavorável".
