---
phase: 48-opcoes-caminho-b
plan: 01
subsystem: vocabulario
tags: [skill_ref, copy.js, paridade, opcoes]
requires: []
provides:
  - skill_ref.OPCOES_ESCADA + opcoes_escada_txt
  - COPY[modo].opcoesEscada + opcoesEscadaTxt + opcoesTourPasso + opcoesAjudaEstuda
affects: [48-04, 48-08, 48-09, 48-11]
key-files:
  created: [web/tests/test_opcoes_escada_espelho.mjs]
  modified: [server/app/skill_ref.py, server/tests/test_skill_ref.py, web/src/copy.js]
requirements-completed: [OPC-10]
metrics:
  completed: 2026-10-05
---

# Phase 48 Plan 01: Vocabulário do caminho B Summary

Fonte única `skill_ref.OPCOES_ESCADA` (123 chaves idênticas em educacional/operador), espelhada byte a byte em `copy.js`, com guardião de paridade.

## Commits
- c2bd77d3 feat(48-01): OPCOES_ESCADA em skill_ref + helper e testes
- 640f5d9d feat(48-01): espelho opcoesEscada em copy.js e guardião de paridade

## Entregue
- `OPCOES_ESCADA` + `opcoes_escada_txt` (modo desconhecido/"estudo" degrada para educacional; chave inexistente -> None).
- 6 testes novos em `test_skill_ref.py` (chaves iguais, sem frase vazia, vocabulário proibido, Pior/Melhor caso, helper, sem "parcial").
- `copy.js`: `opcoesEscada` nos dois modos, `opcoesEscadaTxt`, `opcoesTourPasso`, `opcoesAjudaEstuda` (sem "Watchlist"; consumo em App.jsx fica para 48-11).
- `test_opcoes_escada_espelho.mjs`: paridade byte a byte, vocabulário proibido, tour/ajuda; prova negativa com `B3_SKILL_REF_PATH` inexistente sai com 1.

## Deviations from Plan
None - plano executado como escrito. Premissa: o texto do Operador é versão curta das frases do Estudo; chaves sem diferença de voz (rótulos, estados) são idênticas nos dois modos. Textos livres (legendas, confirmar_titulo, etc.) redigidos por mim a partir do UI-SPEC quando não havia literal.

## Verificação
- `pytest tests/test_skill_ref.py`: 48 passed.
- `test_opcoes_escada_espelho.mjs`, `test_vocabulario_opcoes.mjs`, `test_consolidacao_opcoes_copy.mjs`, `test_tour_opcoes.mjs`, `test_estrutura_card_espelho.mjs`: verdes.
- `npx vite build`: ok.
- Suíte canônica não rodada (por onda, pelo orquestrador).

## Known Stubs
Nenhum. `opcoesTourPasso`/`opcoesAjudaEstuda` ainda não são consumidos (plano 48-11, intencional).

## Self-Check: PASSED
- skill_ref.py, copy.js, test_opcoes_escada_espelho.mjs presentes; commits c2bd77d3 e 640f5d9d existem; STATE.md/ROADMAP.md intocados.
