# Deferred Items — Phase 02 (Realismo de Mercado)

## 02-01

- **Web test suite environment gap (out of scope, pre-existing).** `bash
  scripts/executar.sh --testes` reports 7 failing `web/tests/*.mjs` files:
  `test_appmode_sincroniza_servidor.mjs`, `test_carteira_nativa_sincroniza.mjs`,
  `test_fase2_portfolio.mjs`, `test_notif_central.mjs`, `test_notify.mjs`,
  `test_oauth_repassa_name_e_code.mjs`, `test_pet_resumo_modo_web.mjs`. All 7
  fail with the identical root cause: `Error [ERR_MODULE_NOT_FOUND]: Cannot
  find package '@capacitor/core' imported from .../web/src/persistence.js` —
  `web/node_modules/@capacitor/*` packages are not installed in this worktree
  checkout (`ls web/node_modules/@capacitor/` returns nothing), even though
  they're declared in `web/package.json`. This is a worktree-provisioning gap
  (`npm install` was never run for `web/` in this isolated worktree), not a
  code regression — plan 02-01 touched ONLY `server/app/*.py` and
  `server/tests/*.py`, no `web/` file. Per the package-manager-install
  exclusion (Rule 3), this executor does not run `npm install` unilaterally.
  Backend suite (`cd server && ./.venv/bin/python -m pytest -q tests/`) is
  fully green: 1002 passed. Flag for the orchestrator/human: run `npm install`
  inside `web/` in this worktree (or verify CI/merge target has it installed)
  before treating the canonical suite as fully green.
