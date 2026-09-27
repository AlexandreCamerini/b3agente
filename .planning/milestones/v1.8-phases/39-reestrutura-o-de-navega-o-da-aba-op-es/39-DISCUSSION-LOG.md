# Phase 39: Reestruturação de navegação da aba Opções - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-24
**Phase:** 39-reestrutura-o-de-navega-o-da-aba-op-es
**Areas discussed:** TODOs a dobrar, Faixa de corte do ranking, Destino de Comparar, Substituto do "saiba mais"

---

## TODOs a dobrar nesta fase

| Opção | Descrição | Selecionado |
|---|---|---|
| Carimbo de frescor nos blocos cross-carteira | Oportunidades/Recomendadas já mostram dado cross-carteira; dobrar exige carimbo de horário/fonte visível nesses cards | ✓ |
| SubAbaOperar: fetch redundante de gate/proposta | Fica resolvido por REMOÇÃO (a fase dissolve o Operar), não como fix a implementar | ✓ (marcado resolvido-por-remoção, não dobrado como fix) |

**Notas:** os outros 3 TODOs que o matcher trouxe (`medir-rate-limit-mydata`,
`revisao-arquitetura-mcp-ecossistema-b3`, `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp`)
não foram apresentados como opção de dobra — pontuaram só por sobreposição
genérica de palavra-chave ("opções"/"motor"), sem relação real com
navegação. Registrados em Deferred/Reviewed no CONTEXT.md.

---

## Faixa de corte do ranking em Recomendadas

| Option | Description | Selected |
|--------|-------------|----------|
| 70% (conservador) | Padrão de mesa profissional pra escritor iniciante | |
| 60% (moderado) | Mostra mais candidatos, risco de exercício um pouco maior admitido | ✓ |
| Sem piso agora, só ordena | Não filtra por probabilidade ainda; decide depois de ver dado real | |

**User's choice:** 60% (moderado)
**Notes:** nenhuma nota adicional.

---

## Destino de "Comparar" (vencimentos)

| Option | Description | Selected |
|--------|-------------|----------|
| Sub-ação dentro de Montar | Link "ver outros vencimentos" depois de montar uma estrutura | ✓ |
| Fora de escopo desta fase | Montar cobre só um vencimento por vez; Comparar volta como fase futura | |
| Entra dentro de Recomendadas | Compara vencimentos dos candidatos ranqueados, não dos montados à mão | |

**User's choice:** Sub-ação dentro de Montar
**Notes:** preserva a função existente sem aba própria.

---

## O que substitui o "saiba mais"

| Option | Description | Selected |
|--------|-------------|----------|
| Remover | 3 abas autoexplicativas por nome+conteúdo dispensam link de ajuda no topo | |
| Vira tour de 3 passos | Tour específico da navegação nova, mostrado uma vez | |
| Mantém glossário, move pra dentro de cada aba | Sai do topo global, vira ⓘ contextual por aba | ✓ |

**User's choice:** Mantém glossário, move pra dentro de cada aba
**Notes:** preserva a função do glossário, só muda onde mora (ⓘ por aba em vez de link único no topo).

---

## Claude's Discretion

- Ícone exato do badge de Vigias e microcopy do sheet (decisão prévia desta
  sessão: vira ícone/badge no cabeçalho, não aba própria — travada antes
  deste discuss-phase, ver turno anterior da conversa).
- Se `ConfluenceRing` substitui a exibição de posição no ranking em
  Recomendadas.

## Deferred Ideas

- Migração completa do motor de opções pro MCP único (mydata) — fora de escopo.
- Taxa livre de risco real (Selic/CDI) em vez do hardcoded `0.105` — melhoria futura.
- Comparativo visual antes/depois no card de perda máxima (achado de sessão
  anterior sobre `PropostaLastreada.jsx`) — candidato a fase futura, não
  parte desta reestruturação de navegação.
