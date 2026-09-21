# Phase 36: Motor de Payoff Genérico - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-21
**Phase:** 36-Motor de Payoff Genérico
**Areas discussed:** Arquitetura (estender vs. motor novo), calendário/diagonal (vencimentos diferentes)

---

## Achado pré-discussão (não é área de decisão, é fato verificado)

Antes de levantar áreas cinzentas, leitura de código + execução direta
encontrou que `server/app/opcoes_payoff.py` (`perfil_da_estrutura()`) já é
um motor genérico de N pernas, em produção desde a Fase 15, com 4
consumidores (`opcoes_motor.py`, `opcoes_lastreadas.py`,
`opcoes_curadoria.py`, `options_mcp_api.py`) e 25 testes. Verificado por
execução:
- Caso golden do Alex (trava de alta 49,17/49,67, débito 0,25) → bate
  exato: breakeven 49,42, ganho/perda máx 25,00.
- Straddle (2 pernas, mesmo strike) → 2 breakevens corretos (`[48.0, 52.0]`).
- Entrada degenerada (mesma perna comprada e vendida) → não dá `NaN`, mas
  devolve `breakevens: [0.0, 50.0]` espúrio (defeito real, não do
  planejamento — ver D-04 do CONTEXT.md).

Isso reduziu o escopo real da fase e virou a primeira pergunta.

---

## Arquitetura — estender ou motor novo

Primeira resposta do Alex a essa pergunta foi pedir a comparação completa
(prós/contras/custo de cada opção + custo de manter fonte única) antes de
decidir — não escolheu direto.

| Option | Description | Selected |
|--------|-------------|----------|
| Estender `opcoes_payoff.py` | Funções novas ao lado da existente; zero duplicação; 4 consumidores herdam automaticamente; ~70-80% do trabalho já pronto/testado. | ✓ |
| Motor novo, paralelo | Schema livre (legs/spot/lotSize conforme especificação original); zero risco nos consumidores atuais; mas cria segunda fonte de verdade pra mesma matemática. | |

**User's choice:** Estender o existente
**Notes:** Decisão fundamentada em precedente real deste repositório —
duas fontes divergentes da mesma conta já causaram bug duas vezes
documentadas (`RR_MIN` na Fase 6, CTA de collar na Fase 32/quick
260916-g6p). O Alex pediu a comparação completa antes de decidir, não
aceitou a recomendação sem ver o raciocínio.

---

## Calendário / diagonal (vencimentos diferentes)

| Option | Description | Selected |
|--------|-------------|----------|
| Vencimento por perna + recusa explícita | Cada perna ganha campo de vencimento opcional; se divergirem, função devolve estado explícito de degradação em vez de calcular — nunca aproxima. | ✓ |
| Fora de escopo desta fase | Só recusar se alguém tentar, sem desenhar o campo de verdade. | |

**User's choice:** Vencimento por perna + recusa explícita (Recomendado)
**Notes:** Campo opcional, default `None`, para não quebrar os 4
consumidores atuais que não passam vencimento hoje.

---

*Phase: 36-motor-de-payoff-gen-rico*
*Discussion completed: 2026-09-21*
