---
phase: 51-seu-dia-na-bolsa
plan: 00
status: complete
completed: 2026-11-18
---
# 51-00 — Bootstrap do ambiente

Ambiente do worktree pronto e AMBIENTE_OK atingido. Nenhum arquivo versionado foi alterado.

- `server/.venv` com Python 3.12.5 (`python3.12 -m venv`). `pip` dentro do sandbox falha porque a regra `**/*.pem` impede o pip de ler o bundle de certificados (PermissionError em `load_verify_locations`). As dependências foram instaladas com `uv pip install --python server/.venv/bin/python -r server/requirements.txt`, com `UV_CACHE_DIR` no `$TMPDIR`; o `uv` usa raízes embutidas e não lê `.pem`. Versão do pytest: 9.2.0.
- `web/` e `web-admin/`: `npm ci` com `npm_config_cache=$TMPDIR/npmcache`, porque o `~/.npm` não pode ser escrito no sandbox. Os dois `node_modules/.bin/vite` existem.
- Smoke: `tests/test_skill_ref.py` 49 passed; `npx vite build` em `web/` ok.

## Nota para as ondas seguintes
- Se um executor precisar de pip, deve usar `uv pip install` (sandbox + `*.pem`).
- Um código de teste que abra TLS real via certifi/httpx pode falhar no sandbox pelo mesmo motivo; os testes devem mockar rede.
- A Task 2 (checkpoint humano) não foi necessária.
