---
quick_id: 260909-th4
phase: quick-260909-th4
plan: 01
status: complete
subsystem: backend
tags: [deploy, carimbo, health]
requires: ["260909-oyu (PR #36, f238b53)"]
provides:
  - "SERVER_BUILD_ID = F10-20260909-01 — /api/health rastreia o deploy da correção de fuso"
affects: [main, health, deploy]
---

# Quick 260909-th4: bump do SERVER_BUILD_ID para deploy só-backend

## Commits
- `403d1a7` — chore(server): bump SERVER_BUILD_ID F10-20260909-01 (260909-th4)

## Verificação
- `from app import main` importa e `SERVER_BUILD_ID == "F10-20260909-01"`.
- `pytest -k health`: 1 passed.
- Diff: exatamente 1 linha de `server/app/main.py`.

## O que NÃO foi feito (deliberado)
- **Deploy**: auto-deploy do Railway desligado desde 2026-09-07. Depois do merge, clique manual do Alex no painel. Confirmação = `curl https://<prod>/api/health` responder `F10-20260909-01` (pode levar ~1 min; 502 no meio = swap de container).
- **Front**: `web/src/version.js` fica em `F10-20260908-02`. Correto num deploy só-backend.

## Risco de colisão (memória deploy-backend-carimbo)
Se houver publicação de front AINDA HOJE (2026-09-09), `bash scripts/bump.sh` sem argumento geraria `F10-20260909-01` e colidiria com este carimbo. Passar o valor explícito: `bash scripts/bump.sh F10-20260909-02`.
