---
phase: quick-260912-vle
plan: 01
subsystem: docs
tags: [documentacao, manual-de-usuario, onboarding]
dependency-graph:
  requires: []
  provides: [docs/MANUAL-BORIS-PLUS.md]
  affects: []
tech-stack:
  added: []
  patterns: ["cópia verbatim por `cp`+`diff`, nunca por retipagem"]
key-files:
  created:
    - docs/MANUAL-BORIS-PLUS.md
  modified:
    - .planning/STATE.md
decisions:
  - "Cópia por `cp` (não `Write`): retipar 261 linhas à mão admite deriva silenciosa que revisão por leitura não pega com confiabilidade — `diff` prova igualdade byte a byte."
  - "Nenhuma contradição encontrada nas três afirmações 'nesta versão' — texto do manual mantido intacto, sem edição de prosa aprovada."
metrics:
  duration: "~15min"
  completed: "2026-09-12"
---

# Phase quick-260912-vle Plan 01: Manual de utilização do Boris+ Summary

Manual de utilização do Boris+ (análise de UX de 12/09/2026) entra no histórico do
repositório como `docs/MANUAL-BORIS-PLUS.md`, cópia verbatim do artefato de
scratchpad — documentação apenas, nenhum código tocado.

## O que foi feito

**Task 1 — Cópia verbatim.** `cp` do arquivo de scratchpad para
`docs/MANUAL-BORIS-PLUS.md` (não `Write`, para eliminar risco de deriva ao
retipar). `diff -u` entre fonte e destino saiu **vazio** (exit 0) — igualdade
byte a byte provada, não afirmada. 261 linhas, primeira linha
`# Manual de utilização — Boris+`.

**Task 2 — Checagem de contradição + suíte canônica.**

Três afirmações "nesta versão" no manual, conferidas contra o código atual,
sem editar uma linha do texto:

| Afirmação do manual (linha) | Código conferido | Veredito |
|---|---|---|
| "Coruja … Não funciona na aba Opções nesta versão" (linha 191) | `PET_TELAS = ("mercado", "carteira", "evolucao", "radar", "agente", "historico", "perfil")` — `server/app/conceitos.py:555` | **Sustenta-se**: `opcoes` está de fato fora da tupla. |
| "Ler opções da B3 … Esta versão não executa ordem de opção por aqui" (linha 186) | `grep -n "options/buy\|options/sell" web/src/opcoes/*.jsx` — zero ocorrências | **Sustenta-se**: nenhum caminho de execução de ordem de opção dentro da aba Opções. |
| "Rever o tour … Não cobre Acompanhar nem Opções nesta versão" (linha 188) | `tourPassos()` em `web/src/App.jsx:2433` — 4 passos: Bem-vindo, Radar, Watchlist, Portfólio | **Sustenta-se**: nem "Acompanhar" (aba `evolucao`) nem "Opções" aparecem no roteiro do tour. |

**Nenhuma contradição encontrada** — resultado explícito, não silêncio.

Suíte canônica: primeira rodada dentro do sandbox acusou 27 falhas, todas
`PermissionError: [Errno 1] Operation not permitted` em
`ssl.load_verify_locations` — o mesmo padrão de falso-positivo já registrado
na memória do projeto (26 falhas do 260911-pub). Repetida fora do sandbox:
**2682 passed, 5 skipped, 3 xfailed** (pytest) **+ 134 `.mjs`**, exit 0 —
baseline do 25-06 batido exatamente, nenhuma divergência.

**Task 3 — Registro e commit.** Linha `260912-vle` adicionada à tabela
`Quick Tasks Completed` do `STATE.md` (editada à mão, com Edit — nunca pelos
mutadores do `gsd-sdk`, por decisão registrada no `CLAUDE.md`). Frontmatter
do `STATE.md` (`progress`/`percent`/`stopped_at`/`last_activity`) **intocado**
— `git diff --stat .planning/STATE.md` mostra 1 arquivo, 1 inserção.

## Deviations from Plan

None - plano executado exatamente como escrito. As três afirmações "nesta
versão" se sustentam; não houve necessidade de sinalizar contradição nem de
decisão do Alex sobre texto envelhecido.

## Nada publicado

Nenhum deploy, bump de `SERVER_BUILD_ID`, `bump.sh`, `publicar-web.sh`,
`publicar-admin.sh` ou push a `origin`. Commit local na branch
`v2/interacao-estrutural`, contendo `docs/MANUAL-BORIS-PLUS.md`,
`.planning/STATE.md` e os artefatos de `.planning/quick/260912-vle-*`.
