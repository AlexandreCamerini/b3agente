---
phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura
plan: 06
subsystem: web (publicação) + docs de planejamento
tags: [checkpoint-humano, publicacao, fechamento]
requirements: [COR-01, HIER-01, HIER-02, CHIP-01, CHIP-02]
key-files:
  modified:
    - web/src/version.js
    - server/web_dist
    - server/app/main.py
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
---

# 42-06 — Checkpoint humano, publicação e fechamento da Fase 42

## Task 1 — verificação humana ao vivo

- Preparação automática feita em 2026-09-27 (madrugada): suíte canônica fora do sandbox com exit 0 (3050 pytest passed, 5 skipped, 3 xfailed; 168/168 `.mjs`), `npx vite build` limpo, `git diff cf7c36d -- server/` vazio. Detalhe em `42-06-CHECKPOINT.md`.
- App local (Vite :5174 + API :8787, viewport 375px) subido para o roteiro de 6 itens.
- Resposta do Alex, verbatim: **"aprovado, DP-1 mantém 4%, DP-2 a DP-4 aprovadas"**.
  - DP-1: mantém alpha 4% no tema claro (`warnTint10` = `rgba(161,98,7,0.04)`, 4,68:1). Sem mudança de código.
  - DP-2 (alinhamento só em regime de tendência), DP-3 ("x/y critérios" fora do cabeçalho do Radar), DP-4 (Watchlist com regime+plano; selo de elegibilidade em chip de 7px em todas as telas): aprovadas.
- "FUNDAMENTO" duplicado na `FundamentoTabela`: sem resposta. Fica como pendência.

## Task 2 — publicação

- `git fetch origin`: `origin/main` já estava contida na branch, então não houve merge.
- `scripts/bump.sh` + `scripts/publicar-web.sh`: **rodados pelo Alex**. Quando o agente tentou, o classificador de permissão do modo automático bloqueou ("Production Deploy"). Resultado: `BUILD_ID = F10-20260927-01`, `server/web_dist` regenerado, `SERVER_BUILD_ID` sincronizado.
- Comentário do `SERVER_BUILD_ID` (`server/app/main.py:1662`): entrada da Fase 42 no topo; texto anterior preservado como `HISTORICO (entrega anterior, F10-20260925-02)` (grep == 1). Sintaxe conferida com `ast.parse`.
- Suíte canônica depois do bump, fora do sandbox: exit 0 — **3050 pytest passed / 5 skipped / 3 xfailed + 168/168 `.mjs`** (baseline Fase 41: 3050 + 165; +3 guardiões novos).
- `git diff --stat origin/main -- server/tests server/app/{setups,kpi,signal_ledger,regime}.py`: vazio.
- Commits `274efc9` (publicação) e `ff7ef4a` (docs). Push de `v2/interacao-estrutural` e fast-forward de `origin/main` (`86ab76a..ff7ef4a`): `git log origin/main -1` == `HEAD`.
- **Conferência de `/api/health` em produção: NÃO feita pelo agente** (bloqueada pelo classificador, "Out-of-Place Publication"). Pendente: o Alex confere `curl -s https://boris.semente.dev/api/health` → esperado `"build": "F10-20260927-01"`.
- O commit `073ac8a` (IaC `.railway/railway.ts`, do Alex, feito em paralelo nesta branch) foi junto no push.

## Task 3 — documentos (à mão, sem mutador do gsd-sdk)

- REQUIREMENTS.md: 5 requisitos `[x]` e `Done` na Traceability (grep == 5); notas de correção factual (8→4 combinações, 4→2 contextos) com o texto original preservado; linha "Last updated" nova.
- ROADMAP.md: Fase 42 `[x]` com data e BUILD_ID; 42-06 `[x]`; linha de progresso `6/6 Complete`; SC#1/SC#4 corrigidos no texto ("8 combinações" == 0, "Acompanhar/Mesa/Posições/home" == 0).
- STATE.md: frontmatter coerente (1/2 fases, 6/6 planos, 50%); Current Position da Fase 42 fechada; posição anterior preservada como "Posição anterior (Fase 42, planejamento + execução autônoma — histórico)".

## Decisões autônomas

1. "FUNDAMENTO" duplicado sem resposta do Alex → pendência declarada, não bloqueia nem é corrigido aqui.
2. Aprovação lida como confirmação da leitura em < 3 s: o "aprovado" veio depois do roteiro ao vivo, cujo item 1 é exatamente essa leitura.
3. Suíte canônica rodada de novo depois do bump do Alex, antes do commit da publicação.
4. `/api/health` não conferido (bloqueio de permissão) → registrado como pendência, sem tentar contornar.

## Pendências

- Conferir `/api/health` de produção (`F10-20260927-01`).
- Build iOS/TestFlight: o card novo só chega ao iPhone num build novo (bundle local).
- "FUNDAMENTO" duplicado na `FundamentoTabela`.
- Alvo de toque do chip de fundamento < 44px (herdado).
- Carrossel de alertas da home com pill própria + anel 52px (fora do AtivoCard).

## Self-Check: PASSED (exceto a conferência em produção, pendente do Alex)
