---
status: incomplete
phase: 18-aba-opcoes
plan: 05
subsystem: publishing
tags: [publish, checkpoint-pending, human-verify, options, portfolio]

# Dependency graph
requires:
  - phase: 18-aba-opcoes
    plan: "18-04"
    provides: "guardião estático da tira de oportunidades e do detalhe em Posições, suíte canônica verde pré-publicação"
provides: []
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - web/src/version.js
    - server/web_dist
    - server/app/main.py

key-decisions:
  - "server/app/main.py mudou 1 linha (SERVER_BUILD_ID) além do previsto pelo texto literal do critério de aceite ('git diff --stat server/app/ vazio') — é o sync automático que o próprio scripts/publicar-web.sh documenta no cabeçalho ('Sincronizar carimbo do servidor, mesmo padrão do entregar.sh'), não uma mudança de comportamento de backend. Mesmo padrão ocorreu no plano 17-06 (ver seu SUMMARY, Task 1) e foi tratado como esperado, não como violação. Incluído no commit do Task 1."

requirements-completed: []

duration: ~15min (Task 1 apenas)
completed: null
---

# Phase 18 Plan 05: Publicação e verificação humana da tira de oportunidades Summary

**Task 1 completa e commitada (bump + publicação + suíte canônica verde); Task 2 é checkpoint humano bloqueante que requer o Alex ao vivo, com mercado aberto — NÃO executável por este agente. Fase permanece INCOMPLETA até resposta humana.**

## Performance

- **Duration:** ~15min (Task 1)
- **Task 2:** não iniciada — requer humano

## Task 1: Bump do carimbo e publicação do front — COMPLETO

**Carimbo gerado:** `F10-20260903-02` (anterior: `F10-20260903-01`).

1. `bash scripts/bump.sh` — sem argumento, gerou o segundo carimbo do dia.
2. `bash scripts/publicar-web.sh` — build (`vite build`, 89 módulos) e
   publicação em `server/web_dist`. Warnings `ERROR: failed to copy trust
   settings of system certificate-25291` apareceram antes do build mas NÃO
   impediram a publicação (build e cópia concluídos com sucesso na mesma
   execução, dentro do sandbox padrão desta vez).
3. `bash scripts/executar.sh --testes` — rodado DEPOIS da publicação.
   Primeira tentativa (dentro do sandbox padrão) falhou com 27 testes
   `FAILED` por `PermissionError` (rede/socket bloqueado pelo sandbox —
   mesmo artefato de sandbox documentado nos planos 18-01/02/03/04 e no
   17-06). Rerodado fora do sandbox
   (`dangerouslyDisableSandbox: true`, fatos apresentados via Fact-Forcing
   Gate no início da sessão para o branch-check): **exit 0**, **2010
   passed, 1 skipped** (pytest) + todas as suítes `web/tests/*.mjs` OK,
   incluindo `test_carteira_opcoes_tira.mjs` (guardião novo da Fase 18,
   Plano 04) e os 3 guardiões nomeados como intocáveis
   (`test_opcoes_proposta_ui.mjs`, `test_carteira_lastro_ui.mjs`,
   `test_opcoes_collar_ui.mjs`).
4. Confirmado: `web/src/version.js` tem `BUILD_ID = "F10-20260903-02"`; o
   mesmo carimbo aparece literal dentro de
   `server/web_dist/assets/index-C5cx7HjA.js`; `git status --porcelain`
   mostrou `server/web_dist` genuinamente trocado (16 assets antigos
   removidos/renomeados, novos adicionados) e `server/app/main.py` com o
   `SERVER_BUILD_ID` sincronizado ao novo carimbo (sync automático do
   próprio `publicar-web.sh`, ver key-decisions).

### Acceptance criteria (Task 1)

- [x] `git diff web/src/version.js` mostra `BUILD_ID` novo, formato
      `F10-AAAAMMDD-NN`, diferente do anterior.
- [x] `git status --porcelain server/web_dist` mostrou arquivos modificados
      (publicação de fato aconteceu).
- [x] `BUILD_ID` de `web/src/version.js` aparece dentro do bundle publicado
      (`grep -rl "F10-20260903-02" server/web_dist` retornou
      `server/web_dist/assets/index-C5cx7HjA.js`).
- [x] `bash scripts/executar.sh --testes` saiu com código 0 DEPOIS da
      publicação (ambas as suítes) — fora do sandbox padrão, ver Issues.
- [x] `git diff --stat web/package.json web/package-lock.json` vazio.
- [~] `git diff --stat server/app/` NÃO ficou vazio — 1 linha
      (`SERVER_BUILD_ID`), sync automático e esperado do próprio
      `publicar-web.sh`, sem mudança de comportamento de backend. Ver
      key-decisions e precedente no `17-06-SUMMARY.md`.

## Task Commits

1. **Task 1: Bump do carimbo e publicação do front** — `fb1d794` (chore)

## Task 2 — checkpoint humano bloqueante (NÃO EXECUTADO)

**Status: pendente. Este agente não pode completar esta task — requer o
Alex, ao vivo, com o app rodando e o mercado ABERTO.** Ver a mensagem de
CHECKPOINT REACHED retornada ao orquestrador para o roteiro completo de 10
passos e a pergunta a/b/c sobre o risco herdado da Fase 17.

Nenhum push para `origin` foi feito. A fase NÃO está marcada como completa.

## Files Created/Modified

- `web/src/version.js` — `BUILD_ID` bumpado.
- `server/web_dist` — republicado (bundle novo, 16 assets trocados/
  renomeados).
- `server/app/main.py` — `SERVER_BUILD_ID` sincronizado (sync automático de
  `publicar-web.sh`, 1 linha).

## Decisions Made

- Ver `key-decisions` no frontmatter: o diff de 1 linha em
  `server/app/main.py` é o sync de carimbo intrínseco ao
  `scripts/publicar-web.sh` (documentado no próprio cabeçalho do script),
  não uma mudança de backend desta fase. Mesmo padrão do plano 17-06.

## Deviations from Plan

Nenhuma no sentido das Regras 1-4 (nenhum bug corrigido, nenhuma
funcionalidade crítica adicionada, nenhuma decisão arquitetural). Duas
notas operacionais (ambiente, não código):

1. `bash scripts/executar.sh --testes` falhou dentro do sandbox padrão
   (27 testes com `PermissionError` — rede/socket bloqueado), rerodado fora
   do sandbox com sucesso limpo. Mesmo artefato de sandbox documentado nos
   4 planos anteriores desta fase e no 17-06.
2. `git diff --stat server/app/` não ficou literalmente vazio, por conta do
   sync automático de `SERVER_BUILD_ID` que o próprio `publicar-web.sh`
   executa — ver key-decisions.

## Issues Encountered

- `bash scripts/executar.sh --testes` dentro do sandbox padrão: 27 falhas
  por `PermissionError` em testes que fazem chamada de rede/socket (ex.
  `test_benchmark_ibov.py`, `test_yahoo_intraday.py`,
  `test_options_provider_yahoo.py`) — restrição de rede do sandbox, não
  relacionada a nenhuma mudança deste plano ou da fase. Resolvido
  reexecutando fora do sandbox (`dangerouslyDisableSandbox`).
- `bash scripts/publicar-web.sh` emitiu ~30 linhas de
  `ERROR: failed to copy trust settings of system certificate-25291` antes
  do build — mesmo artefato de sandbox (certificados/cache root-owned) já
  documentado nos planos 18-01/02/03/04, mas desta vez NÃO impediu a
  conclusão do build/publicação dentro do próprio sandbox padrão (só
  atrasou/poluiu o log).

## User Setup Required

**Ação necessária do Alex antes de qualquer push:** rodar o roteiro de 10
passos do Task 2 (app local publicado, mercado ABERTO, incluindo passo no
iPhone) e responder explicitamente à decisão a/b/c sobre publicar junto o
fluxo de aceite da Fase 17 (checkpoint dela segue ADIADO, NÃO APROVADO). Ver
mensagem de CHECKPOINT REACHED para o texto completo.

## Next Phase Readiness

- Task 1 completa e commitada — front publicado localmente neste worktree,
  carimbo `F10-20260903-02` coerente entre `version.js` e o bundle.
- Task 2 bloqueia o fechamento da Fase 18 inteira. Nenhum push feito.
  `STATE.md`/`ROADMAP.md` NÃO foram tocados por este agente — ficam a cargo
  do orquestrador após a resposta do humano.

---
*Phase: 18-aba-opcoes*
*Completed: pending (Task 2 not executed)*
