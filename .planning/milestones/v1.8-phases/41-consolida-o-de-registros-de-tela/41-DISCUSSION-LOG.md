# Phase 41: Consolidação de registros de tela - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-25
**Phase:** 41-consolida-o-de-registros-de-tela
**Areas discussed:** Quais telas entram no registro, Onde mora o conteúdo de tour/ajuda, Tolerância a mudança visível, Verificação e publicação

---

## Quais telas entram no registro

| Option | Description | Selected |
|--------|-------------|----------|
| Todas as 8 que o assistente conhece | 5 da barra + agente/histórico/perfil, flag "na barra"; paridade 8×8 sem exceção | ✓ |
| Só as 5 da barra | Registro menor; paridade precisaria de exceção para 3 subtelas | |

**User's choice:** Todas as 8 (recomendado)

---

## Onde mora o conteúdo de tour/ajuda

| Option | Description | Selected |
|--------|-------------|----------|
| Textos ficam nas funções, que leem a lista do registro | Registro só com estrutura; strings e vocabulário por modo intocados | ✓ |
| Texto do tour/ajuda como campo do registro | Ponto único real, mas move muitas strings e arrisca copy por modo | |

**User's choice:** Textos ficam nas funções (recomendado)

---

## Tolerância a mudança visível

| Option | Description | Selected |
|--------|-------------|----------|
| Refactor puro, zero mudança | Inconsistências viram achado para depois | ✓ |
| Pode corrigir inconsistências pequenas | Mistura refactor com mudança de produto | |

**User's choice:** Refactor puro (recomendado)

---

## Verificação e publicação

| Option | Description | Selected |
|--------|-------------|----------|
| Checkpoint humano curto antes de publicar | 5 abas × 2 modos, tour, ajuda, assistente em 2-3 telas | ✓ |
| Só testes, sem checkpoint | Mais rápido; nenhum teste cobre tour/assistente renderizando | |

**User's choice:** Checkpoint humano curto (recomendado)

---

## Claude's Discretion

Nome/local do registro, forma do mapeamento id→snapshot, mecanismo de leitura dos rótulos por modo na barra — desde que zero mudança visível.

## Deferred Ideas

- Inconsistências de rótulo/texto encontradas durante o refactor (registrar, não corrigir).
- Textos do tour/ajuda dentro do registro (opção rejeitada).
