# Phase 13: Uso real visível na interface + enforcement no iOS - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-29
**Phase:** 13-uso-real-vis-vel-na-interface-enforcement-no-ios
**Areas discussed:** Placement dos contadores de uso/limite (CAP-06)

---

## Gray areas apresentadas (multiSelect)

O usuário selecionou apenas "Onde e como mostrar os contadores (CAP-06)"
entre as 4 áreas oferecidas (as outras 3 — exibição no plano Pro,
comportamento de falha no iOS, cadência de busca do limite — não foram
selecionadas para discussão e foram fechadas como premissa declarada, ver
`13-CONTEXT.md`).

## Placement dos contadores (CAP-06)

| Option | Description | Selected |
|--------|-------------|----------|
| Dual — ação + visão passiva | Watchlist (subtítulo) + CatalogModal (ao editar) + Config/Perfil (seção IA) | ✓ |
| Minimalista | Só no ponto de ação (CatalogModal + Config/Perfil), sem subtítulo | |
| Centralizado | Um card de plano único na tela Perfil, nada espalhado | |

**User's choice:** "Dual — ação + visão passiva (recomendado)"
**Notes:** O pedido original do usuário foi "Desenho da UI dos usuários
para analisar a usabilidade e o fluxo de informações do app" — a pergunta
foi construída com mockups ASCII dos 3 pontos de exibição (Watchlist,
CatalogModal, Config/Perfil), reaproveitando padrões já existentes no
código (`App.jsx:6618` "X de Y selecionados"; `App.jsx:5714`/`5569` padrão
"X/Y" de cota). O usuário confirmou a opção que maximiza visibilidade
proativa sem criar UI nova.

---

## Claude's Discretion

- Nome/rota exata do endpoint novo de watchlist quota.
- Redação exata de mensagens de bloqueio/erro (deve seguir vocabulário
  canônico existente, `copy.js`/`skill_ref.py`).
- Limiar visual de "quase no limite" (não pedido como requisito).

## Premissas declaradas (não questões abertas ao usuário, mas decisões
assumidas com justificativa e sinalizadas para correção se divergirem)

- Plano Pro: omitir contador inteiramente (nem "X/∞", nem "ilimitado").
- iOS sem conseguir confirmar `max_watchlist`: fail-closed (bloqueia a
  adição), não fail-open — diverge do padrão de `analisesNoMes()` porque
  aqui não há gate autoritativo no servidor.
- iOS cadência de busca do limite: ao vivo a cada tentativa, sem cache novo
  (mesmo padrão de `analisesNoMes()`/`aiQuota()`).

## Deferred Ideas

Nenhuma — a discussão ficou dentro do escopo da fase.

## Todos revisados (não dobrados)

- `cap-watchlist-robustez-code-review.md` (WR-01/02/03) — já resolvido via
  PR #26, todo desatualizado, não é trabalho pendente.
- `medir-rate-limit-mydata.md` — fora de escopo, pertence ao ciclo de
  virada de produção do mydata (Fase 9).
