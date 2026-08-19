# Deferred Items — Phase 03 (Correção Crítico + Alto)

## 03-04

- **Web test suite environment gap (out of scope, pre-existing — same as
  phase 02).** `bash scripts/executar.sh --testes` reports 7 failing
  `web/tests/*.mjs` files: `test_appmode_sincroniza_servidor.mjs`,
  `test_carteira_nativa_sincroniza.mjs`, `test_fase2_portfolio.mjs`,
  `test_notif_central.mjs`, `test_notify.mjs`,
  `test_oauth_repassa_name_e_code.mjs`, `test_pet_resumo_modo_web.mjs`. All 7
  fail with the identical root cause: `Error [ERR_MODULE_NOT_FOUND]: Cannot
  find package '@capacitor/core' imported from .../web/src/persistence.js` —
  `web/node_modules` does not exist at all in this worktree checkout
  (`ls web/node_modules` → no such file or directory), even though the
  package is declared in `web/package.json`. This is a worktree-provisioning
  gap (`npm install` was never run for `web/` in this isolated worktree), not
  a code regression — plan 03-04 touched ONLY `server/app/main.py`,
  `server/app/plan.py`, and `server/tests/test_fase3_gate_plano.py`, no
  `web/` file. Per the package-manager-install exclusion (Rule 3), this
  executor does not run `npm install` unilaterally. Backend suite
  (`cd server && ./.venv/bin/python -m pytest -q`) is fully green: 1059
  passed. Flag for the orchestrator/human: run `npm install` inside `web/`
  in this worktree (or verify CI/merge target has it installed) before
  treating the canonical suite as fully green.
