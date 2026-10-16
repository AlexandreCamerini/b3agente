---
quick_id: 261015-iaf
status: complete
---

# Summary

Backend: `llm.ia_indisponivel_publico`; rotas `/api/analyze` e `/api/technical/analyze` com `iaIndisponivel {code, motivo, mensagem=motivo}`; `scan_deep.run_deep` com `iaIndisponivel` no topo. Front: `IaIndisponivelAviso` + `COPY.iaIndisponivel` (2 modos), Radar deep/lote. Suíte canônica: 3604 passed, 5 skipped, 3 xfailed; `npx vite build` ok. `bump.sh` → F10-20261015-03 (SERVER_BUILD_ID sincroniza no `entregar.sh`). Não publicado, sem commit/push.

Pendente: destaque do Acompanhar não mostra o aviso; sinal no web-admin não feito.
