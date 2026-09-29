# Phase 42: Crítico — cor, chip único e ordem de leitura - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-26
**Phase:** 42-cr-tico-cor-chip-nico-e-ordem-de-leitura
**Areas discussed:** Storyline/coerência (trazida pelo Alex), Canal de cor da elegibilidade, Posição e forma do ConfluenceRing, O que entra em cada bloco da ordem

---

## Seleção de áreas

Alex selecionou 3 das 4 áreas propostas e adicionou em texto livre: "Entender que storytelling vamos ter nos dados conforme vamos lendo. É necessário que todos os indicadores tenham coerência. Não posso ter todos os indicadores apontando alta e fundamento A com confluência 100% e estarmos indicando a venda do ativo." Não selecionou "Cor dentro do peso 'contexto'" — resolvida ao final como decisão derivada, confirmada.

Diagnóstico apresentado antes da pergunta (verificado no motor): confluência é do melhor setup direcional, que pode ser de venda (`setups.py:535`); fundamento é qualidade, não direção; `gatilhoAlinhado` (`regime.py:193`) já existe mas só é dito quando alinhado; `kp.direcao` vem da IA — contradição real de duas fontes.

## Storyline

| Option | Description | Selected |
|--------|-------------|----------|
| Narrar o alinhamento | Indicadores de contexto dizem a favor/contra a decisão, determinístico; motor intocado | ✓ |
| Narrar + backlog de motor | Idem + registrar decisão contra-regime para milestone futuro | |
| Tratar no motor agora | Motor não emite VENDER/COMPRAR contra regime; quebra invariante v1.9 | |

## Chips da IA no card

| Option | Description | Selected |
|--------|-------------|----------|
| Tirar do card | Card mostra só motor; IA fica no KpiBlock | ✓ |
| Manter como "leitura da IA" | Agrupado, rotulado, com aviso de divergência | |
| Manter só convicção/qualidade | Remove só direção da IA | |

## Canal de cor — inelegível

| Option | Description | Selected |
|--------|-------------|----------|
| T.warn existente | Âmbar = honestidade de dado; só falta tint | ✓ |
| Token dedicado "confiab" | Par novo, mais pureza semântica, mais manutenção | |

## Canal de cor — elegível

| Option | Description | Selected |
|--------|-------------|----------|
| Neutro com ✓ | Sem verde; ao lado de VENDER não parece compra | ✓ |
| Manter verde | Proposta da auditoria; colisão verde=COMPRAR permanece | |
| Mesma família do inelegível | Eixo de confiabilidade com intensidades | |

## Marcas de alinhamento

| Option | Description | Selected |
|--------|-------------|----------|
| Neutro, texto + glifo | Verde/vermelho só manchete/preço/P&L | ✓ |
| Âmbar para "contra" | Reusa canal de confiabilidade para outro significado | |

## ConfluenceRing — posição

| Option | Description | Selected |
|--------|-------------|----------|
| Dentro do bloco da manchete | ~36px à direita da decisão | ✓ |
| Linha logo abaixo da manchete | ~44px com rótulo, fora do bloco | |

## ConfluenceRing — rótulo

| Option | Description | Selected |
|--------|-------------|----------|
| Lado + setup + tier | "100% · Forte — padrão de venda: Reversão de sobrecompra"; "confiança" sai | ✓ |
| Só % + tier | Enxuto, não resolve "por que 100% e VENDER" | |

## ConfluenceRing — sem setup

| Option | Description | Selected |
|--------|-------------|----------|
| Nada | Manchete + motivo já dizem | ✓ |
| Anel 0% "sem padrão" | Posição fixa, mais ruído | |

## TimingBadge

| Option | Description | Selected |
|--------|-------------|----------|
| Colado à manchete | "Quando" da mesma decisão | ✓ |
| Dentro do bloco do plano | Some sem plano numérico | |

## Plano por modo

| Option | Description | Selected |
|--------|-------------|----------|
| Operador: números; Estudo: motivo + régua | Um bloco por modo; régua sai do Operador | ✓ |
| Ambos caixa + régua | Completo, bloco alto, duplicação persiste | |

## Resumo da posição

| Option | Description | Selected |
|--------|-------------|----------|
| Acima da manchete, como hoje | Situação do usuário, não sinal | ✓ |
| Depois da elegibilidade | R$ vai para o fim | |

## Fechamento — cor do peso contexto (derivada)

| Option | Description | Selected |
|--------|-------------|----------|
| Confirmo: contexto neutro | Só manchete carrega cor de direção; âmbar só no inelegível | ✓ |
| Regime mantém cor, fundamento neutro | REGIME ALTA verde ao lado de VENDER volta a gritar | |
| Quero discutir mais | — | |

## Claude's Discretion

- Visual exato de cada peso do `SinalChip`.
- Onde vive a âncora didática do setor `analise` (provável: no anel).
- Anel com setup + NÃO OPERAR: mostra.
- Local das strings (copy.js / skill_ref.py).
- Nome do token de tint e necessidade de override no Operador.

## Deferred Ideas

- Motor: decisão contra o regime (AGUARDAR/confirmação) — milestone futuro.
- Motion do ConfluenceRing; tokens `--sp-*` globais (Future Requirements).

## Correções factuais registradas

- 4 combinações tema×modo, não 8.
- 2 call sites do AtivoCard (watchlist, radar), não 4.
