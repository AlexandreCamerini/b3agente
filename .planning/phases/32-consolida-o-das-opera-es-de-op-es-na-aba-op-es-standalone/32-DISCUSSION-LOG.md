# Phase 32: Consolidação das operações de opções na aba Opções - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-15
**Phase:** 32-Consolidação das operações de opções na aba Opções
**Areas discussed:** O que sobra em Posições (as outras três foram delegadas)

---

## Seleção de áreas

Quatro áreas foram apresentadas. O Alex selecionou **uma** e já adiantou a
resposta no mesmo turno.

| Área | Descrição apresentada | Selecionada |
|------|-----------------------|-------------|
| O que sobra em Posições | Posições fica sem nada? Linha de chamada? Ou só o acordeão por posição fica? | ✓ |
| Onde os blocos aterrissam | Sub-aba "Operar" existente, sub-aba nova, ou topo junto dos vigias? | |
| Os dois motores lado a lado | Manter os dois rotulados, unificar, ou matar um? | |
| Rolagem da aba cheia | Aceita e adia, acordeões, ou busca nesta fase? | |

---

## O que sobra em Posições

**Ambiguidade que precisou de desempate:** a resposta inicial foi *"A primeira
opção mas quando vc clica em uma das opções ele te leva para aba opções já na
oportunidade apresentadas"*. "A primeira opção" (= Posições sem nada de
opções) contradizia "quando você clica em uma das opções" — sem card em
Posições não há o que clicar. Foi feita uma pergunta de desempate com as três
leituras possíveis.

| Option | Description | Selected |
|--------|-------------|----------|
| Só uma linha de chamada | Posições perde os 4 blocos e ganha UMA linha discreta com contagem; clicar leva à aba Opções, na lista. Máxima limpeza; a pessoa vê que existe algo, mas não o quê sem trocar de aba. | ✓ |
| Os 4 cards ficam, como vitrine | A lista curada continua em Posições mostrando a manchete, mas sem executar ali; clicar leva à aba Opções já naquela oportunidade. Preserva a descoberta com conteúdo real. | |
| Posições fica 100% sem opções | Nenhuma menção a opções em Posições, nem linha de chamada. Tela mais limpa possível; maior risco de nunca descobrir que a varredura existe. | |

**User's choice:** "Só uma linha de chamada"
**Notes:** Vira D-01/D-02/D-03 no CONTEXT.md. Consequência registrada: o
deep-link para uma oportunidade específica (pedido na formulação inicial) fica
fora, porque não há card de origem — anotado em Deferred Ideas para voltar se
Posições um dia exibir cards de novo.

---

## Claude's Discretion

Pergunta feita: *"As outras três áreas: você decide ou eu decido?"*
**Resposta:** "Decide o resto por mim".

| Option | Description | Selected |
|--------|-------------|----------|
| Decide o resto por mim | Registro como critério meu, com recomendação fundamentada; Alex revisa no CONTEXT.md antes de planejar. | ✓ |
| Quero decidir os dois motores | Só a área de consequência de produto real; as outras duas eu decido. | |
| Quero decidir as três | Uma pergunta por área restante. | |

Áreas delegadas e como foram resolvidas (detalhe e razão em CONTEXT.md):
- **Onde os blocos aterrissam** → D-04: lista curada no topo da aba, fora do
  seletor de ticker (precedente D4 da Fase 27, aprovado); blocos por posição
  na sub-aba "Operar".
- **Os dois motores lado a lado** → D-05: manter os dois com rótulos que
  expliquem a diferença; unificar é fase própria, com peso regulatório.
- **Rolagem da aba cheia** → D-06: aceita e adiada, mesma postura da Fase 27
  ("não inventar busca, mas não impedir depois").

## Deferred Ideas

- Unificar os dois motores de proposta (`propor()` × `opcoes_curadoria`) —
  candidata mais forte a próxima fase depois da 32.
- Busca/filtro na aba Opções para carteiras grandes (herdado da Fase 27).
- Deep-link para uma oportunidade específica — fora por D-01/D-02; volta a
  fazer sentido se Posições voltar a exibir cards.

## Todos revisados e não incorporados

- `medir-rate-limit-mydata.md` — match por palavra-chave, é sobre fonte de
  dados, não UI.
- `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` — match por `mcp`;
  acompanhamento externo, sem relação com consolidação de tela.
