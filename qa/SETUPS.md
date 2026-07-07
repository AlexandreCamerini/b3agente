# SETUPS.md — Regras objetivas dos setups detectados (auditável)

*FASE 1 (Revisão Total) · fonte única: `server/app/setups.py` · testes: `tests/test_setups.py` + `tests/test_setups_br.py`*

Modelo do produto: cada setup é um **checklist de critérios objetivos** com pesos.
A **confluência (0–100)** é o percentual ponderado de critérios atendidos — mede
**aderência do ativo ao padrão em dados passados**, nunca probabilidade de
resultado. Critérios marcados como **obrigatórios** definem o padrão: sem eles o
setup não conta, ainda que a confluência passe do mínimo (`MIN_CONFLUENCIA = 50`).

Todo setup BR devolve, além do checklist:
`gatilho` (nível de rompimento que ativaria o estudo), `invalidacao` (nível que
nega o padrão — stop didático), `alvoSugerido` (projeção didática: **2× o risco
a partir do gatilho**, salvo regra própria), `referencia` e `backtestavel: true`.
O LLM apenas traduz para o vocabulário fixo — ex.: *"setup 9.1 detectado →
**Estudar alta** com gatilho em R$ X"*. Nenhum verbo de ordem.

---

## Setups clássicos (Radar v2, pré-existentes)

| Setup | Critérios (obrigatório em **negrito**) |
|---|---|
| Pullback à média (alta/baixa) | **Tendência SMA20×SMA50** (3) · preço reencontrando a SMA20 ±2% (3) · RSI neutro 40–60 (2) |
| Rompimento com volume (alta/baixa) | **Fechamento além do extremo do período** (4) · volume ≥ 1,5× média 20 (3) · fechamento no terço da ponta (1) |
| Reversão de sobrevenda/sobrecompra | **RSI ≤ 30 / ≥ 70** (3) · candle de força (2) · estocástico cruzando (2) |
| Compressão de volatilidade (neutro) | Largura das Bandas de Bollinger no quartil inferior (3) · ≥ 8 leituras de banda (1) |

---

## Setups testados do mercado brasileiro (FASE 1)

### 1. Família 9.x — Alexandre Wolwacz (Stormer)

**9.1 — Virada da MME9.**
- **MME9 virou** no último candle: vinha caindo (e[-2] < e[-3]) e subiu (e[-1] > e[-2]) — espelho na baixa (4, obrigatório);
- Fechamento do lado da média (acima na alta / abaixo na baixa) (2);
- Volume ≥ média de 20 candles (1).
- Gatilho: máxima do candle da virada (alta) / mínima (baixa). Invalidação: extremo oposto do mesmo candle. Alvo: R:R 2:1.

**9.2 — Correção de 1 candle.**
- **MME9 preservada** (subindo na alta / caindo na baixa) (3, obrigatório);
- **Candle de correção**: fechamento menor que o anterior (alta) / maior (baixa) (3, obrigatório);
- RSI fora do extremo contrário (1).
- Gatilho/invalidação: máxima/mínima do candle de correção. Alvo: R:R 2:1.

**9.3 — Retomada após correção.**
- **MME9 preservada** (3, obrigatório);
- **Correção no candle anterior** (fechamento contra a tendência) (2, obrigatório);
- **Retomada** no último candle (fechamento a favor) (3, obrigatório).
- Gatilho: extremo do candle de retomada. Invalidação: extremo da correção (mín/máx dos 2 últimos candles). Alvo: R:R 2:1.

### 2. IFR2 — Larry Connors (muito testado em ações BR)
- **RSI(2) ≤ 25** (3, obrigatório);
- **Preço acima da MMA200** — filtro de tendência de Connors; detectado só no lado comprador, como na difusão BR (3, obrigatório);
- RSI(2) ≤ 10 — sobrevenda extrema (1).
- Setup **de fechamento** (sem rompimento): gatilho = fechamento do candle de sinal. **Saída didática** (alvoSugerido) = máxima dos 2 candles anteriores (regra original de Connors). Connors não usa stop; a invalidação didática exibida é `mínima do candle − 1×ATR`.

### 3. PFR — Ponto de Força e Reversão (Stormer)
- **Mínima mais baixa que as dos 2 candles anteriores** (compra) / máxima mais alta (venda espelhada) (3, obrigatório);
- **Fechamento acima do fechamento anterior** (compra) / abaixo (lado vendedor) (3, obrigatório);
- Fechamento no terço da ponta do candle (1).
- Gatilho: máxima do candle PFR (alta) / mínima (baixa). Invalidação: extremo oposto. Alvo: R:R 2:1.

### 4. 123 de fundo/topo (clássico, difundido no BR)
- **Estrutura 1-2-3 formada** por pivôs objetivos com asa de 1 candle nos últimos 12: fundo(1) → topo(2) → **fundo mais alto(3)** (compra); espelho no topo (4, obrigatório — a exigência "fundo 3 > fundo 1" está embutida na detecção da estrutura);
- Gatilho (ponto 2) ainda não rompido — padrão armado (2);
- Tendência de fundo favorável (SMA20 × SMA50) (1).
- Gatilho: extremo do candle 2. Invalidação: extremo do candle 3. Alvo: R:R 2:1.

### 5. Ponto Contínuo — Dunnigan (popular no BR)
- **ADX(14) ≥ 25** — tendência definida (3, obrigatório);
- **DI dominante na direção** (DI+ > DI− na alta; inverso na baixa) (2, obrigatório);
- **Preço reencontrando a MME21**: toque (low ≤ MME21 ≤ high) ou fechamento a ±1% (3, obrigatório).
- Gatilho: máxima do candle do toque (alta) / mínima (baixa). Invalidação: extremo oposto. Alvo: R:R 2:1.

### 6. Inside Bar (clássico)
- **Candle contido no anterior** (high ≤ high da mãe e low ≥ low da mãe) (3, obrigatório);
- **Tendência definida** (SMA20 × SMA50) — dá o lado do estudo; sem tendência o padrão **não conta** (3, obrigatório);
- Compressão forte: amplitude ≤ 60% do candle-mãe (1).
- Gatilho: extremo do candle-**mãe** no lado da tendência. Invalidação: extremo oposto da mãe. Alvo: R:R 2:1.

### 7. Máximas/Mínimas de Larry Williams — 9.4
- **Tendência definida** (SMA20 × SMA50) (3, obrigatório);
- **Correção com candle de referência**: nas últimas 5 barras, o candle da mínima mais baixa (alta) / máxima mais alta (baixa), com o extremo além do candle anterior (3, obrigatório);
- Gatilho ainda não rompido — padrão armado (1).
- Gatilho: máxima do candle de referência (alta) / mínima (baixa). Invalidação: extremo oposto do mesmo candle. Alvo: R:R 2:1.

---

## Integração com o STU e o veredito

- Todos os detectores rodam sobre a **janela do usuário** dentro do Snapshot
  Técnico Único (`technical_snapshot.py`) — N1/N2/N3 leem os mesmos resultados.
- Veredito por ativo (vocabulário fixo): melhor setup **direcional** ≥ 50 de
  confluência com obrigatórios completos define "Estudar alta/baixa"; só
  padrões neutros ⇒ "Monitorar"; nada ⇒ "Sem setup no momento".
- Guardrail testado em `test_setups.py::test_estrutura_confluencia_e_guardrail`
  e `test_setups_br.py::test_todos_os_detectores_br_respeitam_shape_e_guardrail`:
  nenhum nome/critério contém verbo de ordem.

## Notas de fidelidade (decisões documentadas)

1. **9.2/9.3**: a literatura do 9.x tem variações; adotamos as formas mais
   difundidas (correção de 1 candle; retomada pós-correção), sempre com a MME9
   preservada como obrigatório — o que define a família.
2. **IFR2 só comprador**: é como o setup foi validado/testado em ações BR
   (Connors long-only sobre índice/ações). O lado vendedor não é detectado.
3. **Alvo R:R 2:1** é projeção didática padrão quando o setup não define alvo
   próprio (IFR2 define: máxima dos 2 anteriores).
4. **Inside Bar sem tendência não conta** — evita falso-positivo em lateral,
   coerente com a regra do pullback pré-existente.
