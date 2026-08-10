# ESPEC — Análises Técnicas do Boris+
**Fonte metodológica:** skill `analise-tecnica-b3` (Operador Sênior de AT da B3)
**Adaptação obrigatória:** a skill produz DECISÃO OPERACIONAL (comprar/vender);
o Boris+ é educacional por guardrail regulatório inegociável. Esta espec adota
a METODOLOGIA da skill (contrato de dados, validação, confluência, stop por
invalidação/ATR, cenários, teto de confiança) traduzida para o vocabulário
educacional fixo: **"Estudar alta" · "Estudar baixa" · "Monitorar" ·
"Aguardar" · "Não operar" · "Sem setup no momento"**. Verbos de ordem
(compre/venda/entre agora) são PROIBIDOS em qualquer output.

---

## 1. Princípio de divisão (por que assim)

**Determinístico (Python, grátis, reproduzível, testável):** tudo que é
CÁLCULO ou REGRA BINÁRIA sobre números — indicadores, níveis, padrões de
candle, critérios de setup, confluência percentual, referências de stop/alvo
por fórmula. A skill exige "nunca invente preços/indicadores" — a forma mais
forte de garantir isso é a LLM NUNCA calcular nada: ela recebe tudo pronto.

**LLM (pago, sob cota/BYOK):** tudo que é INTERPRETAÇÃO — síntese entre
famílias, leitura didática dos critérios, cenários narrativos, adequação ao
perfil, explicação da memória de cálculo. A LLM interpreta números
pré-calculados; jamais os produz.

## 2. Matriz determinístico × LLM

| Análise | Determinístico (onde) | LLM interpreta |
|---|---|---|
| SMA20/50, EMA9/21, inclinações | `indicators.py` | direção predominante em linguagem didática |
| RSI(14) + estado | `indicators.py` | divergências vs. preço, peso na leitura |
| MACD (linha/sinal/hist) + viradas | `indicators.py` + `scanner.detect_conditions` | aceleração/exaustão do movimento |
| Estocástico %K/%D + cruzamentos | idem | timing dentro da estrutura |
| Bollinger (sup/méd/inf) | `indicators.py` | regime de compressão/expansão |
| ATR(14) + ATR% | `indicators.py` | ruído esperado, distância didática de stop |
| **ADX(14) + DI± (NOVO)** | `indicators.py` | força da tendência (ADX≥25 forte / <20 fraca) |
| OBV + volume relativo (21) | `indicators.py`/`build_context` | confirmação ou divergência do movimento |
| Suportes/resistências (pivôs) | `technical_models._pivots` | qualidade dos níveis, zona de invalidação |
| **Padrões de candle (NOVO):** engolfo ±, martelo, estrela cadente, doji | `technical_models` | contexto do padrão (onde apareceu importa) |
| Setups clássicos (pullback, rompimento, reversão, compressão) + checklist + confluência % | `setups.py` | leitura dos critérios presentes/AUSENTES |
| Extremos da janela do usuário | `scanner.py` | — |
| Referências stop/alvo por fórmula (mín. local − 1×ATR; resistência; ±k×ATR) | `technical_models.riskPlanReference` | adequação ao PERFIL + memória de cálculo em 3 cenários |
| Validação de dados (contrato §4) | endpoints | declarar limitações na resposta |
| Score/ranking do Radar | `scanner.py` | — (IA só no top-N, decisão híbrida) |

**Regra de ouro:** nenhum número novo nasce na LLM. Se a resposta da IA citar
um valor, ele veio do pacote técnico.

## 3. Os três níveis (pipeline)

### N1 · OPORTUNIDADES (mercado inteiro → top-N)
- Varredura: 100% determinística (`/api/scan`, universo completo, grátis).
- Aprofundamento: `/api/scan/deep` roda IA APENAS no top-N por confluência
  (`radarAiTopN`, default 5, teto 10). 1 chamada por ativo; cache por
  (ticker, período, dia); estimativa de custo/cota ANTES de rodar.
- A IA recebe: contexto do `build_context` (janela candlePeriod) + setups
  detectados com checklist. Devolve: leitura de cada setup, critérios
  presentes/ausentes em linguagem didática, cenários de ESTUDO
  (alta/baixa/neutro), riscos, bloco MODELOS UTILIZADOS.

### N2 · ANÁLISE COMPLETA DO ATIVO (5 famílias)
Cobertura didática por família — cada uma com leitura determinística própria
(`families` no build_context) que a IA então sintetiza:
1. **Tendência**: médias, inclinações, ADX/DI±, viés estrutural
2. **Momentum**: RSI, estocástico, MACD, viradas recentes
3. **Volatilidade**: ATR/ATR%, HV21/63, Bollinger (largura/regime)
4. **Price action**: padrões de candle da janela, últimas rejeições, níveis
5. **Volume**: relativo (21), OBV e inclinação, confirmação
+ **Síntese de confluência entre famílias** (quantas apontam na mesma
direção — determinística) que a IA explica.

### N3 · ALVO & STOP (técnico × perfil)
Contexto explícito para a IA: ATR(14), suportes/resistências da janela,
bandas, viés de tendência, PERFIL (risco/horizonte/tolerância) e orçamento.
Resposta ESTRUTURADA (JSON): 3 cenários — conservador/moderado/agressivo —
cada um com stop, alvo, **memória de cálculo** (ex.: "stop didático = mínima
local 36,80 − 1×ATR 0,52 = 36,28") e relação risco-retorno; a UI pré-preenche
com 1 toque e o usuário SEMPRE confirma. Regra da skill preservada: R:R
mínimo 1,5:1 para rotular um cenário como "tecnicamente consistente";
abaixo disso, o cenário é marcado "R:R desfavorável — fins de estudo".

## 4. Contrato de dados e validação (da skill, aplicado no backend)

Antes de qualquer chamada de IA o endpoint valida e ANEXA ao contexto:
- `candles < 50` → flag `serieCurta`: IA instruída a não avaliar estrutura de
  médio prazo com confiança; `< 20` → sem S/R confiável, teto "baixa".
- `volume ausente` em candles relevantes → rompimentos "não confirmados";
  teto de confiança "moderada".
- Timeframe único (só diário hoje) → teto de confiança **"moderada"**,
  declarado na resposta ("confirmação multi-timeframe não realizada").
- Cotação defasada (>15min em pregão) → preço "não acionável para timing".
- ≥2 falhas simultâneas → resposta obrigatória: "Sem setup no momento —
  dados insuficientes para leitura com vantagem estatística."

## 5. Instruções para a LLM (blocos de system prompt)

**Persona (todos os níveis):** operador sênior de AT da B3 em função de
PROFESSOR — disciplina, objetividade, rigor estatístico; explica primeiro em
linguagem simples, depois o termo técnico; nunca confunde convicção com
certeza; nunca fundamenta leitura em UM indicador isolado (peso maior em
estrutura de preço + volume + confluência).

**Regras herdadas da skill (invioláveis):**
1. Não inventar preço, indicador, volume, fato ou notícia — usar SÓ o pacote.
2. Nunca prometer lucro/percentual de acerto.
3. Sinais conflitantes → "Aguardar" ou "Não operar" (nunca forçar leitura).
4. Sempre informar o que INVALIDA a tese de estudo.
5. Diferenciar: confirmado / em formação / especulativo.
6. Movimento esticado → dizer explicitamente.
7. Sem oportunidade → frase fixa: "Sem setup no momento — não há leitura
   com vantagem estatística clara."
8. Probabilidades só relativas (baixa/moderada/alta), nunca % sem base.
9. Confiança ALTA só com confluência ampla E multi-timeframe (logo, hoje o
   teto operacional é MODERADA — dizer isso quando relevante).

**Tradução regulatória (sobrepõe a skill):** proibidos verbos de ordem e
"recomendação"; usar o vocabulário fixo; toda saída termina com o disclaimer
educacional do app; bloco **MODELOS UTILIZADOS** obrigatório (nome, o que é,
o que mede, limitações) — o app ensina, não opina.

**Formatos de saída:** JSON estrito por nível (N1: leituraSetups/cenarios/
riscos/modelosUtilizados; N2: FORMAT existente + seção "## Modelos
utilizados" no corpo; N3: array por ativo com `cenarios[3]` +
`memoriaCalculo` + `modelosUtilizados`). Sem texto fora do JSON.

## 6. Rastreio de assertividade (nota da skill → backlog)
A skill recomenda registrar cada leitura emitida e medir acerto/retorno/
drawdown por regime de mercado. Encaixa na telemetria didática da Fase 2.5
(histórico "o que a IA disse antes vs. o que aconteceu") — registrar
`analysisLog` por posição já nesta rodada de backend viabiliza isso depois.
