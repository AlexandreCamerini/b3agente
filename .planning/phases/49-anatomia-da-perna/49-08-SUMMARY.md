---
phase: 49-anatomia-da-perna
plan: 08
subsystem: checkpoint-humano
tags: [checkpoint, anatomia-da-perna]
requires: [49-07]
provides: [anatomia da perna aprovada pelo Alex]
metrics:
  tasks: 2
  files: 0
  completed: 2026-10-06
---

# Phase 49 Plan 08: Pré-voo e checkpoint Summary

**Pré-voo (tarefa 1):** `preflight-ok` — `web/dist` presente, rota `/api/options/anatomia/{ticker}` em `main.py`, 2 montagens de `<PernasAbertas`, guardiões da fase verdes, `App.jsx` sem commit da fase.

**Checkpoint humano (tarefa 2), 2026-10-06:** o Alex respondeu **"aprovado"** sobre a lista consolidada (anatomia da perna, G-01/G-02 do 48-17 e as correções do dia: perna avulsa sem ações, janela de prazo removida, patrimônio com a perna avulsa), testada no web local com MyData e depois publicada em `boris.semente.dev` (carimbo `F10-20261006-01`).

Limite do registro: a resposta não trouxe os números do passo 4 (total, sem a PUT, contribuição) pedidos pelo critério de aceite; **não foram registrados nem inventados**. Os valores esperados (−277,00 / −37,00 / −240,00 em R$ 48,00) estão provados por teste unitário do motor (`test_anatomia_perna.py`).
