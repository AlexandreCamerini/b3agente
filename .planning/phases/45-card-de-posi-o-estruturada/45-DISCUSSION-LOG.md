# Phase 45: Card de posição estruturada - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-29
**Phase:** 45-card-de-posi-o-estruturada
**Areas discussed:** Como o card busca a estrutura; O que "Encerrar estrutura…" faz; Blocos herdados do card atual (+ badge CARD-06)
**Not discussed (padrão conservador aprovado):** Estado vencida e linha de fonte

---

## Como o card busca a estrutura

| Pergunta | Opções | Escolha |
|----------|--------|---------|
| Fonte do dado | Reusar options_proposta ✓ / Rota leve /estrutura / Buscar só ao expandir | Reusar options_proposta |
| Carga/erro | Card atual + aviso ✓ / Skeleton / Usar optionPositions locais | Card atual + aviso |
| Refresh | Ao abrir + a cada compra/venda/fechar ✓ / Ritmo da cotação / Manual | Ao abrir + após ações |

## O que "Encerrar estrutura…" faz

| Pergunta | Opções | Escolha |
|----------|--------|---------|
| Ação do botão | Levar à aba Opções > Operar ✓ / Confirmação inline / Só Operador executa, Estudo explica | Levar à aba Opções > Operar |
| Botões | Um botão ✓ / Manter os dois do mock / No Estudo trocar por "Ver em Opções" | Um botão, abre o ativo certo |

Achado do código: `/api/options/lastreada/fechar` fecha um contrato por vez e é 403 em Modo Estudo.

## Blocos herdados do card atual

| Pergunta | Escolha |
|----------|---------|
| Manter (multi) | Stop/alvo (IA); Reanalisar + Histórico; linha dias/% capital/setup. NÃO: Compras desta posição |
| Stop/alvo já definidos | Marcadores na régua da faixa ✓ (vs só texto / manter PlanRuler) |
| Badge CARD-06 | Chips do mock; pill "travada" só com call ✓ (vs pill em toda estrutura / chip + pill) |

## Claude's Discretion

- Estado vencida e linha de fonte/horário: padrão conservador (sem "resultado final", sem horário inventado).
- Tokens `T`/`SP`, AA nas 4 combinações, `aria-label`, extração do componente, `qtyTravada` em "Registrar saída".

## Deferred Ideas

- Rota leve /estrutura; encerrar inline; infos do review da 44; quick task dos `tiraOpcoes*`.
