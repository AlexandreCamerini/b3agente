# Deferred Items — Fase 07

## Plano 07-02

- **6 falhas em `web/tests/*.mjs`** (`test_appmode_sincroniza_servidor.mjs`,
  `test_carteira_nativa_sincroniza.mjs`, `test_fase2_portfolio.mjs`,
  `test_notif_central.mjs`, `test_notify.mjs`, `test_oauth_repassa_name_e_code.mjs`,
  `test_pet_resumo_modo_web.mjs`) ao rodar `bash scripts/executar.sh --testes`.
  Causa: `ERR_MODULE_NOT_FOUND` para `@capacitor/core` — `web/node_modules` não
  está instalado neste worktree. Pré-existente, fora do escopo do Plano 07-02
  (backend-only: `server/app/db.py`, `server/app/signal_ledger.py`,
  `server/tests/test_signal_ledger.py` — nenhum arquivo em `web/` foi tocado).
  Não corrigido aqui (Scope Boundary — não é causado por este plano). Suíte
  Python (`bash scripts/test.sh`) está 100% verde: 1170 passed.
