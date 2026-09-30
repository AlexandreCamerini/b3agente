---
phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
plan: 05
subsystem: web (publicação) + docs de planejamento
tags: [checkpoint-humano, publicacao, fechamento]
requirements: [HIER-03, CHIP-03, RITMO-01]
key-files:
  modified:
    - web/src/version.js
    - server/web_dist
    - server/app/main.py
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
---

# 43-05 — Checkpoint humano, publicação e fechamento da Fase 43

## Task 1 — verificação humana
- A preparação automática está em `43-05-CHECKPOINT.md`: suíte 3060 + 171 `.mjs`, build e `cap copy` ok, motor sem diff, área de toque do fundamento com 48px.
- Resposta do Alex: "aprovado". As DPs foram respondidas por nome: **DP-1 aprova**, **DP-2 aprova**, **DP-3 alternativa** (dado ausente cai para "sem histórico medido").
- A DP-3 alternativa bloqueou a publicação até o gap `43-06` ser executado (queda para `nunca_medido` em `skill_ref.py` ↔ `copy.js`, guardiões com nota). O gap foi executado e verificado: 3062 pytest.

## Task 2 — publicação
- O Alex rodou o `bump.sh` (`-02`, nunca foi ao ar) e depois o `entregar.sh`: `F10-20260927-03`, `web_dist` e bundle iOS sincronizados, commit `166883d6` "revisao dos cards".
- O `git fetch` mostrou que o `origin/main` divergia em infra: `c2f3580e` remove o `server/railway.json`, e a branch tinha o `6202671b` ("manter de propósito"). O primeiro merge foi abortado e a pergunta foi levada ao Alex. **Decisão dele: vale o `origin/main`.** Merge `920eb2f9` com os 7 arquivos de deploy idênticos ao `origin/main`; `test_backup_pre_deploy` com 11 passed.
- Comentário do `SERVER_BUILD_ID` com a entrada da Fase 43 no topo e a entrega anterior preservada como `HISTORICO (entrega anterior, F10-20260927-01)` (grep == 1, `ast.parse` ok).
- Suíte canônica fora do sandbox, depois do merge: **3062 passed / 5 skipped / 3 xfailed + 171/171 `.mjs`**, exit 0. Motor sem diff contra o `origin/main`.
- `/api/health` de produção: **não conferido pelo agente** (o classificador bloqueia curl à produção). Pendente com o Alex; esperado `"build": "F10-20260927-03"`.

## Task 3 — documentos (à mão, sem mutador do gsd-sdk)
- REQUIREMENTS: HIER-03, CHIP-03 e RITMO-01 com `[x]` e `Done` (grep == 3); nota D-06 na CHIP-03 com o texto original preservado; linha "Last updated".
- ROADMAP: Fase 43 `[x]` com BUILD_ID; SC#2 corrigido no lugar ("grade de caixas cinzas" == 0); 43-05 e 43-06 `[x]`; progresso 6/6.
- STATE: 2/2 fases e 12/12 planos, 100%; Current Position da Fase 43 fechada; posição anterior preservada.

## Decisões autônomas
1. Merge com os arquivos de deploy idênticos ao `origin/main`, incluindo o texto do `railway.ts`/`DEPLOY_RAILWAY.md`. A nota do `6202671b` saiu por obsoleta, depois da decisão do Alex.
2. O milestone v1.9 **não** foi fechado (`/gsd-complete-milestone` é decisão do Alex); só as fases foram marcadas.

## Pendências
- Conferir `/api/health` (`F10-20260927-03`) depois do redeploy.
- Build iOS/TestFlight (Xcode → Archive/Upload).
- KB sem verbete de vantagem estatística / expectativa matemática.
- "amostra insuficiente (n=0 …)" no Operador não cita janela nem n total (observação do checkpoint).

## Self-Check: PASSED (exceto a conferência em produção, pendente do Alex)
