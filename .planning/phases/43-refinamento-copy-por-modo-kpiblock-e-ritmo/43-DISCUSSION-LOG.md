# Phase 43: Refinamento — copy por modo, KpiBlock e ritmo - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 43-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-27
**Phase:** 43-refinamento-copy-por-modo-kpiblock-e-ritmo
**Areas discussed:** Leitura da IA (CHIP-03), Microtexto de reconciliação, Tom por modo, Alcance da escala 4/8pt, Fold-in

Achado do scout apresentado antes das perguntas: `KpiBlock`/`KpiCell` é código morto desde a qa/49, e depois da D-02 da Fase 42 direção/convicção/qualidade da IA não aparecem em tela nenhuma.

---

## Leitura da IA (CHIP-03)

| Option | Description | Selected |
|---|---|---|
| Voltar na leitura IA | SinalChip contexto dentro da AnalysisView, nunca no card | ✓ |
| Voltar no detalhe de candles | Como a CHIP-03 descrevia; mistura IA com indicadores | |
| Não voltam | Apaga código morto, CHIP-03 "não aplicável" | |

| Option | Description | Selected |
|---|---|---|
| 3 chips neutros + rótulo | Sem cor, sem recomendação da IA, omitido sem kpis | ✓ |
| 3 chips + recomendação da IA | Segunda fonte de decisão (tensão CVM) | |
| Direção colorida | Contraria COR-01/D-14 | |

## Microtexto de reconciliação

| Option | Description | Selected |
|---|---|---|
| Substitui os números crus | Chip + frase com n e janela | ✓ |
| Vem junto dos números | Três peças | |
| Substitui o chip | Perde marcador COR-01 | |

| Option | Description | Selected |
|---|---|---|
| Frase própria por estado | Insuficiente / nunca medido / aposentado com texto próprio | ✓ |
| Só elegível/inelegível | Omitir nos outros estados | |

| Option | Description | Selected |
|---|---|---|
| Só na linha do card | Listas por setup ficam com chip + números | ✓ |
| Em todo HistoricoPill não compacto | | |

## Tom por modo

| Option | Description | Selected |
|---|---|---|
| Estudo: frase + "por que importa" (tocável) | | ✓ |
| Estudo: só o fato | | |
| Operador: fato curto com n e expR | | ✓ |
| Operador: fato curto sem expR | | |

## Alcance da escala 4/8pt

| Option | Description | Selected |
|---|---|---|
| Card inteiro, dentro e entre | | ✓ |
| Só entre blocos | | |
| Constante SP no App.jsx | | ✓ |
| Constantes locais do card | | |
| Exceção óptica nomeada e comentada | | ✓ |
| Sem exceção | | |

## Fold-in (pendências da Fase 42)

| Option | Description | Selected |
|---|---|---|
| FUNDAMENTO duplicado | Sai o label do chip, fica o cabeçalho | ✓ |
| Alvo de toque < 44px | Via área de toque | ✓ |

## Claude's Discretion
- Nome do dict/função em skill_ref.py/copy.js; seta e rótulo da linha da IA; mapeamento de cada px avulso para a escala; kpis no scan_deep só se existirem.

## Deferred Ideas
- Tokens --sp-* globais; motion do ConfluenceRing; decisão contra o regime; chips da IA no detalhe de candles.
