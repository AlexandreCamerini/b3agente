# Phase 37: Gráfico de Payoff e Explicação Confiáveis - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-21
**Phase:** 37-gráfico-de-payoff-e-explicação-confiáveis
**Areas discussed:** Fonte de "hoje · valor de mercado" (CHART-05), Origem real da divergência de razão G/P (EXPL-03), Arquitetura da camada explicativa (EXPL-01/02/03), Escopo dos consumidores do PayoffChart

---

## Fonte de "hoje · valor de mercado" (CHART-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Sim — buscar prêmio atual via get_option_chain | Novo I/O, backend soma prêmio atual × lado × quantidade por perna | ✓ |
| Não agora — relabeling honesto | Sem I/O novo, mostra net_cost relabelado, CHART-05 parcialmente atendido | |
| Você decide, olhando o custo de cota real | Claude mede o custo real no planejamento | |

**User's choice:** Buscar prêmio atual via `get_option_chain`, vale o custo de cota extra.

| Option | Description | Selected |
|--------|-------------|----------|
| Sob demanda — botão "ver valor de hoje" por candidato | Zero custo automático em Comparar | |
| Automático só no candidato em foco/expandido | Depende de estado de expansão existir | |
| Automático para todos, aceitando o custo de cota | Mais simples, risco real de estourar cota | |

**User's choice (free text):** "É possível trazer o melhor candidato fazer uma análise e apresentar o melhor candidato" — interpretado e confirmado na pergunta seguinte como "buscar só para o 1º candidato do ranking de curadoria".

| Option | Description | Selected |
|--------|-------------|----------|
| O 1º da lista já ordenada pela curadoria | Reusa `opcoes_curadoria.py`, zero lógica nova | ✓ |
| O candidato que o usuário abrir/expandir | Precisa de estado de expansão | |

**Notes:** A resposta livre do Alex foi interpretada como restringir a busca de valor-de-hoje ao melhor candidato (resolve o problema de cota levantado), não como pedido de uma feature nova de "análise automática" — confirmado explicitamente na pergunta de acompanhamento.

---

## Origem real da divergência de razão G/P (EXPL-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, é essa confusão | `cand.razao` (score de curadoria) vs `RazaoGanhoPerda` (ganho/perda real) | ✓ |
| Não, é outro lugar — vou descrever | | |

**User's choice:** Confirmado — `CuradoriaEstruturas.jsx:194` (`cand.razao`) é a origem.

| Option | Description | Selected |
|--------|-------------|----------|
| "Pontuação de curadoria" / "Score" | Deixa claro que é critério de ranking | ✓ |
| Manter "razão" mas qualificar | Ainda compartilha a raiz da confusão | |
| Você decide a redação exata | | |

**User's choice:** "Pontuação de curadoria" / "Score".

**Notes:** Guardrail adicional travado sem pergunta (opção única, sem ambiguidade real): qualquer texto que mencione razão G/P — incluindo a explicação nova desta fase — reusa literalmente a variável já exibida por `RazaoGanhoPerda`, nunca recalcula.

---

## Arquitetura da camada explicativa (EXPL-01/02/03)

| Option | Description | Selected |
|--------|-------------|----------|
| 100% determinístico, JS puro, zero I/O | Função pura tipo finance.js/plan.js | ✓ |
| Backend/LLM parafraseia os segmentos | Risco de reformular número (mesma classe de bug do EXPL-03) | |
| Híbrido: texto determinístico + IA só de conexão | Mais complexo de garantir na prática | |

**User's choice:** 100% determinístico, JS puro, zero I/O.

| Option | Description | Selected |
|--------|-------------|----------|
| Todos os segmentos, spot primeiro, resto na ordem espacial | Quadro completo em texto | ✓ |
| Só o segmento onde o spot está, uma frase | Mais raso | |

**User's choice:** Todos os segmentos, spot primeiro.

---

## Escopo dos consumidores do PayoffChart

| Option | Description | Selected |
|--------|-------------|----------|
| Gráfico corrigido nos 3; texto+hoje só em Analisar/Comparar | CuradoriaEstruturas fica só com o gráfico corrigido | ✓ |
| Tudo (gráfico + texto + hoje) nos 3 de uma vez | Mais trabalho de integração e teste | |

**User's choice:** Gráfico corrigido em todos; texto+hoje só em Analisar/Comparar.

**Notes:** Correção de leitura própria durante a discussão — `PayoffChart.jsx` tem 3 consumidores reais (`SecaoComparar`, `SecaoAnalisar`/`OpcoesScreen`, `CuradoriaEstruturas`), não 4; `CriarSetup.jsx` só cita o componente num comentário, não renderiza. Confirmado com o Alex que isso não muda a decisão tomada.

---

## Claude's Discretion

- Nome exato do campo novo de valor de hoje (`valor_hoje` é ponto de partida) e da função/rota que faz a busca via `get_option_chain`.
- Redação final do rótulo "Pontuação de curadoria"/"Score" e das frases de template da explicação por segmento.
- Localização exata da função pura de explicação (módulo novo vs. `uiOpcoes.jsx`).
- Tratamento visual exato do estado de erro/indisponível do bloco "hoje" quando `get_option_chain` falha.

## Deferred Ideas

- Blocos novos (explicação por segmento, valor de hoje) em `CuradoriaEstruturas.jsx` — fora do escopo desta fase, candidato a fase futura.
- "Análise automática apresentando o melhor candidato" em Comparar, além da busca de valor de hoje restrita ao 1º candidato — não especificada nem decidida; se o Alex quiser algo mais amplo (destaque visual, resumo comparando candidatos), é capacidade nova fora do escopo desta fase.
