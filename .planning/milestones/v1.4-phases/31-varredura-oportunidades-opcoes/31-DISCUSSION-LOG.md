# Phase 31: Varredura de oportunidades de opções - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-14
**Phase:** 31-varredura-oportunidades-opcoes
**Areas discussed:** D1 (orçamento de vencimentos), D2 (opção a descoberto na varredura), D3 (payoff visual), D1-detalhe (teto N), D2-ranking (fórmula única vs. seções), D4 (universo de tickers)

---

## D1 — Até onde varrer vencimentos

| Option | Description | Selected |
|--------|-------------|----------|
| Teto fixo (ex. 2-3 vencimentos) | N vencimentos mais próximos por posição elegível, custo previsível N× o de hoje | ✓ |
| Janela por prazo (ex. até 60 dias) | Todos os vencimentos dentro de um teto de dias corridos, custo variável por ticker | |
| Só ampliar o piso da Fase 30 (15→X dias) | Aumenta tolerância no vencimento único, sem multiplicar chamadas | |

**User's choice:** Teto fixo.
**Notes:** Achado técnico apresentado antes da pergunta: `get_vencimentos()` é 1 chamada barata (lista inteira), `get_options_chain(t, vencimento=X)` é 1 chamada cara por vencimento — a decisão precisa declarar custo em N× chamadas.

---

## D1-detalhe — Teto exato de N

| Option | Description | Selected |
|--------|-------------|----------|
| 2 vencimentos | Custo máximo 2× o de hoje | ✓ |
| 3 vencimentos | Custo máximo 3×, mais chance de achar oportunidade na janela 15-60 dias | |

**User's choice:** 2 vencimentos.

---

## D2 — Opção a descoberto na varredura

| Option | Description | Selected |
|--------|-------------|----------|
| Mostrar pra todos, com aviso + CTA de ligar o flag | Nunca esconde possibilidade, só bloqueia a ação (princípio geral do produto) | |
| Só mostrar pra quem já tem o flag ligado | Reduz risco de empurrar alguém a ligar um flag de risco maior por ver um número bom | ✓ |

**User's choice:** Só para quem já tem o flag ligado.
**Notes:** Fase 29 (gate de execução) não muda — esta decisão é sobre o momento de DESCOBERTA/exibição, que hoje não existe checagem nenhuma de flag em `opcoes_curadoria.py`.

---

## D2-ranking — Fórmula única vs. seções separadas por objetivo

| Option | Description | Selected |
|--------|-------------|----------|
| Uma fórmula só (prêmio ÷ perda máxima) pras 4 | Mantém a fórmula da Fase 30 para tudo; put/collar ranqueiam mal por design | ✓ |
| Seções separadas por objetivo (receita vs. proteção) | Put/collar numa seção à parte com critério próprio | |

**User's choice:** Uma fórmula só.
**Notes:** Aceito mesmo sabendo que put/collar de proteção vão estruturalmente mal na fórmula, porque o objetivo declarado da varredura é "gerar receita com risco mínimo".

---

## D3 — Payoff visual: o que priorizar

| Option | Description | Selected |
|--------|-------------|----------|
| Responsivo mobile 375px | Sem mudar lógica de exibição, ainda 1 estrutura por vez | ✓ |
| Overlay de múltiplos candidatos | Trabalho novo real, componente não suporta hoje | |
| Interatividade (tocar/zoom) | Trabalho novo, foco em detalhe de 1 candidato | |

**User's choice:** Responsivo mobile 375px.

---

## D4 — Universo de tickers

| Option | Description | Selected |
|--------|-------------|----------|
| Só posições abertas na carteira | Mesmo universo da Fase 30, orçamento previsível | ✓ |
| Também tickers sem posição (watchlist/catálogo) | Mais fiel ao espírito "a descoberto não precisa de lastro", custo maior | |

**User's choice:** Só posições abertas na carteira.
**Notes:** Vale inclusive para a descoberto — mesmo sem exigir lastro no motor, o escopo de BUSCA desta fase continua sendo a carteira do usuário.

---

## Claude's Discretion

- Layout exato do bloco de resultado em Posições (extensão de `CuradoriaEstruturas` vs. bloco novo).
- Texto de narração da IA para put/collar/naked quando rankeados mal pela fórmula única.

## Deferred Ideas

- Varredura sobre watchlist/catálogo sem posição na carteira.
- Overlay de múltiplos candidatos e interatividade no payoff — candidato a fase de "polish" futura.
- Seções de ranking separadas por objetivo (receita vs. proteção) — revisitar se a fórmula única confundir o usuário na prática.
