---
phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa
plan: 06
subsystem: ui
tags: [react, vite, disclaimers, publicacao, adr-020]

# Dependency graph
requires:
  - phase: "09-04/09-05"
    provides: "mydata_client.py atrás dos contratos existentes, medição de rate-limit (docs/MEDICAO-Mydata-2026-08-27.md), ADR-020 registrando a supersessão parcial de ADR-001/004/008/019"
provides:
  - "FONTE_LABEL reconhece source === \"mydata\" -> \"MyData\", sem mascarar fontes futuras"
  - "DISCLAIMERS.appBanner deixou de nomear um provedor fixo (Yahoo Finance) no texto estático"
  - "Textos de contexto do App.jsx (modal Sobre, quote change, painel admin de cotações, modal watchlist) descrevem a cadeia mydata->brapi->Yahoo no diário e brapi no spot"
  - "Front publicado em server/web_dist com carimbo F10-20260827-01 (SERVER_BUILD_ID sincronizado em server/app/main.py)"
affects: [09-06-task3-checkpoint-virada-producao]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/src/disclaimers.js
    - web/src/version.js
    - server/app/main.py
    - server/web_dist (build publicado — árvore gerada, não editada à mão)

key-decisions:
  - "Task 3 (virada de produção B3_CANDLE_PROVIDER/B3_OPTIONS_PROVIDER) NÃO foi executada por este agente — é checkpoint humano bloqueante que exige AskUserQuestion interativo e não pode tocar Railway/produção a partir de um worktree paralelo. Fica pendente para o orquestrador conduzir depois do merge desta wave."
  - "web/node_modules estava ausente no worktree (gitignored, não veio no checkout) — restaurado via 'npm ci' contra o package-lock.json já commitado, sem instalar/alterar nenhuma dependência nova. Tratado como pré-requisito de ambiente, não como deviation de Rule 3 (nenhum pacote novo, nenhuma versão trocada)."
  - "server/app/main.py entrou no commit de publicação porque scripts/publicar-web.sh sincroniza SERVER_BUILD_ID automaticamente a partir de web/src/version.js — não é edição manual, é o comportamento documentado do script."

requirements-completed: []

# Metrics
duration: ~25min
completed: 2026-08-27
---

# Phase 9 Plan 06 (Tasks 1-2): Rótulos de fonte + publicação do front Summary

**FONTE_LABEL e o banner do app deixam de mentir sobre a origem dos dados de mercado (Yahoo Finance fixo, desatualizado desde o ADR-008) e passam a reconhecer o mydata; front buildado e publicado em server/web_dist com carimbo F10-20260827-01. Task 3 (virada de produção) NÃO executada — pendente para o orquestrador.**

## Performance

- **Duration:** ~25 min (Tasks 1-2; Task 3 fora de escopo deste agente)
- **Tasks:** 2/2 completos (Task 3 é checkpoint humano bloqueante, deliberadamente não executado)
- **Files modified:** 5 (App.jsx, disclaimers.js, version.js, main.py, server/web_dist — árvore gerada)

## Accomplishments

- `FONTE_LABEL` (`web/src/App.jsx`) ganhou o caso `source === "mydata"` → `"MyData"`, mantendo o repasse cru de fonte desconhecida como último caso; comentário acima cita ADR-020 ao lado da ADR-008.
- `DISCLAIMERS.appBanner` (`web/src/disclaimers.js`) deixou de nomear um provedor fixo ("Yahoo Finance") — diff de exatamente 1 linha, resto do arquivo intocado.
- Cinco textos de contexto no `App.jsx` (modal "Sobre · Aviso legal", legenda de variação por período, painel admin de cotações sem candles, modal "Editar watchlist" e o comentário do fluxo de validação de ticker novo) atualizados para descrever a cadeia real: diário via MyData com brapi/Yahoo de reserva, spot ao vivo via brapi.
- `cd web && npx vite build` verde; suíte canônica (`bash scripts/executar.sh --testes`) verde ANTES e DEPOIS da publicação.
- `scripts/bump.sh` avançou o carimbo de `F10-20260824-01` para `F10-20260827-01`; `scripts/publicar-web.sh` buildou e publicou em `server/web_dist`, sincronizando `SERVER_BUILD_ID` em `server/app/main.py`.
- Confirmado sem segredo no bundle publicado: `grep -rc 'MYDATA_TOKEN' server/web_dist` retorna 0 em todos os arquivos.

## Task Commits

1. **Task 1: Rótulos de fonte no front reconhecem o mydata** — `c90b102` (feat)
2. **Task 2: Carimbar a entrega e publicar o front** — `a17c251` (chore)

**Task 3 (checkpoint humano bloqueante): NÃO executada por este agente.** Ver seção "Task 3 — pendente" abaixo.

## Files Created/Modified

- `web/src/App.jsx` — `FONTE_LABEL` + comentário (ADR-008/ADR-020); 5 textos de contexto atualizados para a cadeia mydata→brapi→Yahoo (diário) / brapi (spot)
- `web/src/disclaimers.js` — `appBanner` sem provedor nomeado (1 linha alterada)
- `web/src/version.js` — `BUILD_ID`: `F10-20260824-01` → `F10-20260827-01`
- `server/app/main.py` — `SERVER_BUILD_ID` sincronizado ao mesmo carimbo (efeito automático de `publicar-web.sh`, não edição manual)
- `server/web_dist` — árvore de build regenerada e publicada (16 chunks antigos removidos, chunks novos com hash novo, `index.html`/`sw.js` atualizados) — nenhum arquivo `.md`/`.py` no diff além do `main.py` já citado

## Decisions Made

Ver `key-decisions` no frontmatter. Resumo: Task 3 deliberadamente fora do escopo deste agente (checkpoint humano bloqueante, sem acesso a Railway/produção nem a `AskUserQuestion` interativo neste contexto de worktree paralelo); `web/node_modules` restaurado via `npm ci` porque o worktree não carrega diretórios gitignored — não é instalação de pacote novo, é reconstrução do que já está pinado em `package-lock.json`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `web/node_modules` ausente no worktree — restaurado via `npm ci`**
- **Found during:** Task 1, ao rodar `cd web && npx vite build`
- **Issue:** `web/node_modules` não existe no checkout do worktree (é gitignored e não acompanha `git worktree add`); `vite.config.js` falhava ao resolver `vite`, `@vitejs/plugin-react` e `vite-plugin-pwa`
- **Fix:** `cd web && npm ci` contra o `package-lock.json` já commitado — nenhuma dependência nova, nenhuma versão alterada
- **Files modified:** nenhum arquivo versionado (apenas `web/node_modules`, gitignored)
- **Verification:** `cd web && npx vite build` passou a sair com código 0 depois do `npm ci`
- **Committed in:** N/A (node_modules não é versionado; não há commit associado)

---

**Total deviations:** 1 auto-fixed (1 blocking, ambiente)
**Impact on plan:** Pré-requisito de ambiente para rodar qualquer verificação deste plano em um worktree novo. Nenhuma mudança de escopo, comportamento ou dependência declarada.

## Issues Encountered

None além da deviation documentada acima. Suíte canônica verde nas duas rodadas (antes e depois da publicação): backend pytest completo + todas as `web/tests/*.mjs`, exit code 0 em ambas.

## Task 3 — pendente (checkpoint humano bloqueante)

Task 3 do plano ("Virada de produção para o mydata — aprovação e verificação ao vivo") **não foi executada por este agente**, por desenho:

- É `type="checkpoint:human-verify" gate="blocking"` — exige apresentar o veredito de `docs/MEDICAO-Mydata-*.md` ao Alex e aguardar resposta interativa (`aprovado` | `adiar` | falha com número do passo), o que não é executável por um agente de worktree paralelo sem `AskUserQuestion`.
- Envolve mudar `B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER`/`MYDATA_TOKEN` no painel do Railway — ação explicitamente vedada a este agente pelo escopo da tarefa (nenhum acesso a Railway/produção).
- A regra de processo desta fase (lição da Fase 8, registrada em `STATE.md`) proíbe `git push` de qualquer wave antes da aprovação da Task 3 — este agente não deu `git push` em nenhum momento; os commits `c90b102` e `a17c251` são locais, no branch `worktree-agent-ae2c32b1c6f75204a`.
- **B3_CANDLE_PROVIDER e B3_OPTIONS_PROVIDER em produção permanecem nos valores anteriores** (não foram tocados) — a migração inteira (Plans 09-01..09-05 + este 09-06 Tasks 1-2) está pronta e testada, mas ainda atrás das env vars antigas.
- O orquestrador conduz a Task 3 diretamente após o merge desta wave, seguindo o roteiro completo já presente em `09-06-PLAN.md` (`<what-built>`/`<how-to-verify>`/`<acceptance_criteria>`).

## User Setup Required

None neste escopo (Tasks 1-2). A Task 3 pendente exige que o Alex decida a virada de env vars no Railway quando o orquestrador apresentar o checkpoint — ver seção acima.

## Next Phase Readiness

- Front corrigido, buildado e publicado com o rótulo "MyData" pronto para quando `B3_CANDLE_PROVIDER=mydata` for ligado.
- Nenhuma mudança de comportamento em produção ainda — os textos novos só afetam a leitura de `source` quando o payload realmente disser `"mydata"`, o que só acontece depois da Task 3.
- Pendência já conhecida e fora de escopo desta fase (registrada no `<assumptions>` do plano): o bundle iOS (`ios_dist`) não recebe esta mudança de rótulo agora — só na próxima entrega TestFlight, que carrega bundle local sem `server.url`.
- Bloqueio conhecido para fechar a fase: Task 3 precisa da aprovação/decisão do Alex antes de qualquer `git push`.

## Self-Check: PASSED

- FOUND: web/src/App.jsx (FONTE_LABEL com "mydata"/"MyData")
- FOUND: web/src/disclaimers.js (appBanner sem "Yahoo Finance")
- FOUND: web/src/version.js (BUILD_ID F10-20260827-01)
- FOUND: server/web_dist/assets/index-D56ZQIEE.js (contém o carimbo F10-20260827-01)
- FOUND commits: c90b102, a17c251 (verified via `git log --oneline -2`)

---
*Phase: 09-centraliza-o-de-dados-de-mercado-mydata-client-py-implementa*
*Completed: 2026-08-27*
