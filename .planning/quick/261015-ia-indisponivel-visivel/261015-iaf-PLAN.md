---
quick_id: 261015-iaf
slug: ia-indisponivel-visivel
date: 2026-10-15
mode: quick
---

# Quick 261015-iaf — IA indisponível visível ao usuário

Problema: IA fora ~2 semanas em produção (saldo Anthropic zerado) sem que ninguém visse; N2 cai no determinístico e scan/deep engole o erro.

Decisões
- D1 — `llm.ia_indisponivel_publico(exc)` → `{code, motivo}` com motivo de lista fechada; nunca texto do provedor. `iaIndisponivel.mensagem` das rotas N2 passa a ser o `motivo` (antes carregava " - {texto cru}").
- D2 — `/api/scan/deep` ganha `iaIndisponivel` (None | `{code,motivo}`); `errors[].erro` de falha de IA = motivo, + `code`.
- D3 — Front: `IaIndisponivelAviso` (role=status, 12px textMuted, caixa neutra) com frase em `COPY[modo].iaIndisponivel`; `quota` segue mostrando a mensagem do servidor. Radar (deep unitário e lote) mostra a frase no lugar de "sem leitura".
- D4 — Guardião `test_fonte_explicacao.mjs` (linha 11px textFaint) revertido de propósito, com nota.
- Fora: destaque do Acompanhar (catch silencioso do deep, bônus) e web-admin (sinal de falhas recentes) — follow-up.

Aceite: pytest `test_ia_indisponivel_publica.py`; `test_fonte_explicacao.mjs`; `npx vite build`; suíte canônica verde (3604 passed).
