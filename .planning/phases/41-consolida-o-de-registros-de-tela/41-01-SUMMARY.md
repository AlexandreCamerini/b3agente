---
phase: 41-consolida-o-de-registros-de-tela
plan: 01
subsystem: front (registro de telas) + backend (paridade)
tags: [telas-01, registro, paridade, guardiao, refactor-puro]
requires: []
provides:
  - web/src/telas.js (registro único, sem consumidor ainda)
  - web/tests/fixtures/telas_baseline_41.json (comportamento congelado pré-refactor)
  - web/tests/test_telas_registro.mjs (guardião de paridade + equivalência)
  - server/tests/test_telas_paridade.py (segundo ponto testado)
affects:
  - 41-02 (religação dos 4 consumidores ao registro)
tech-stack:
  added: []
  patterns:
    - "módulo puro sem import (web/src/opcoes/memoriaOpcoes.js)"
    - "paridade cross-file sem import cross-language (defaults.py×catalog.js)"
    - "extração de função pura via contagem de chaves + eval (test_tour_opcoes.mjs)"
key-files:
  created:
    - web/tests/fixtures/gerar_telas_baseline_41.mjs
    - web/tests/fixtures/telas_baseline_41.json
    - web/src/telas.js
    - web/tests/test_telas_registro.mjs
    - server/tests/test_telas_paridade.py
  modified: []
decisions:
  - "Registro guarda campos explícitos (nunca omitidos, sempre null quando não se aplica) para o teste Python casar por regex de forma estável"
  - "telas.js não é consumido por App.jsx neste plano (D-04/repo_guardrail) — nasce como rede de segurança pura"
metrics:
  duration: "~1h"
  completed: 2026-09-25
---

# Phase 41 Plan 01: Rede de segurança pré-refactor — registro único de telas Summary

Fixture congelado do comportamento atual das 4 listas de tela do App.jsx +
registro único `web/src/telas.js` (8 telas, D-01) com paridade travada em
dois pontos testados contra `conceitos.PET_TELAS`, sem tocar nenhum arquivo
de produto.

## O que foi entregue

**Task 1 — fixture pré-refactor** (`web/tests/fixtures/gerar_telas_baseline_41.mjs`
+ `telas_baseline_41.json`): gerador que extrai, do `App.jsx` atual (HEAD
`6dbf479`), sem editá-lo: o array `defs` do `BottomNav` (avaliado para 4
combinações de `cp`), `tourPassos`/`ajudaSecoes` (extraídos por contagem de
chaves + `eval`, técnica de `test_tour_opcoes.mjs`), a ternária de `petTela`
(tabela-verdade para 7 tabs × 5 `carteiraView` = 35 combinações) e o corpo
inteiro do `switch (petTela) { … }` do `petSnapshot` (ids dos `case` +
sha256). Conferido à mão: barra 5 abas (estudo=Acompanhar/Radar/Watchlist/
Portfólio/Opções, operador[1][1]="Mesa"), tour 6 passos, ajuda 11 seções ×4
combinações, switch com 7 casos sem "mercado" (snapshot dele vem do
`PetSheet`, por desenho da F4).

**Task 2 — registro `web/src/telas.js`** (TDD): RED primeiro
(`test_telas_registro.mjs` falha com `ERR_MODULE_NOT_FOUND` porque o módulo
não existe), depois GREEN (o registro com as 8 entradas da tabela do plano —
`id, barra, rotuloCp, rotuloPadrao, tour, ajuda, snapshot, subtelaDe,
carteiraView`, cada campo sempre presente, `null` quando não se aplica).
6 funções puras exportadas (`idsDasTelas`, `defsDaBarra`, `telasDoTour`,
`telasDaAjuda`, `telaDoAssistente`, `idsComSnapshotNoSwitch`) reproduzem byte
a byte o fixture da Task 1. Módulo sem nenhum `import` (React/store/copy.js).

**Task 3 — segundo ponto testado** (`server/tests/test_telas_paridade.py`):
pytest lê `web/src/telas.js` como texto (regex sobre o bloco `export const
TELAS = Object.freeze([...])`, extraindo os `id: "..."`) e compara o conjunto
com `conceitos.PET_TELAS` — 8 com 8, sem exceção, sem `subprocess`, sem
import cross-language. `server/app/` intocado.

## Passo-a-passo de "adicionar uma tela nova" (SC#4 do ROADMAP, demonstrado)

Hoje (antes da 41-02): editar 5 lugares (`BottomNav.defs`, `tourPassos`,
`ajudaSecoes`, o `switch` de `petSnapshot`, `conceitos.PET_TELAS`). Depois da
41-02 religar os 4 consumidores ao registro (fora do escopo deste plano):
adicionar 1 entrada em `TELAS` (`web/src/telas.js`) + 1 entrada em
`conceitos.PET_TELAS` (espelho obrigatório, backend) — os 2 testes de
paridade (`test_telas_registro.mjs`, `test_telas_paridade.py`) reprovam se
qualquer um dos dois faltar. Este plano (41-01) já prova a mecânica: a prova
negativa abaixo é exatamente esse cenário invertido (tela removida de um
lado só).

## Prova negativa (D-01, T-41-01/T-41-02 do threat_model)

**Lado JS** — troquei temporariamente `id: "perfil"` por `id: "perfil2"` em
`web/src/telas.js` e rodei `node tests/test_telas_registro.mjs`:
```
FALHOU o conjunto de ids do registro é IGUAL ao de conceitos.PET_TELAS (8 com 8, sem exceção) — diferença: registro-só=perfil2 | PET_TELAS-só=perfil — uma tela fora de PET_TELAS faz /api/assistente responder 400 'Tela desconhecida.'; ...
FALHOU idsComSnapshotNoSwitch() tem o MESMO conjunto de baseline.switchPetSnapshot.casos — diferença: registro-só=perfil2 | baseline-só=perfil
2 falha(s)
```
Revertido (`diff` confirma arquivo idêntico ao original) → suite volta a
"todos os testes passaram".

**Lado Python** — troquei `id: "perfil"` por `id: "fantasma"` em
`web/src/telas.js` (mesmo arquivo, outro teste) e rodei
`.venv/bin/python -m pytest tests/test_telas_paridade.py -q`:
```
AssertionError: registro de telas do front divergiu de conceitos.PET_TELAS — só no registro: ['fantasma'] (fora da allowlist, /api/assistente responde 400 'Tela desconhecida.'); só em PET_TELAS: ['perfil'] (resumo sem tela que o front chame)
1 failed, 1 passed in 0.65s
```
Revertido (`diff` confirma arquivo idêntico) → `2 passed`.

## Validação

- `cd web && node tests/test_telas_registro.mjs` — verde (57 asserções, PARTES A/B/C).
- `node tests/test_pet_opcoes.mjs` e `node tests/test_tour_opcoes.mjs` — verdes, sem edição (guardiões antigos não tocados nesta rodada; a reconciliação deles é escopo da 41-02).
- `cd server && .venv/bin/python -m pytest tests/test_telas_paridade.py tests/test_pet_todas_telas.py -q` — 31 passed.
- Suíte canônica `bash scripts/executar.sh --testes` (fora do sandbox): **3050 passed, 5 skipped, 3 xfailed** (baseline do 40-02: 3048/5/3 — +2 exatos de `test_telas_paridade.py`, zero regressão) e **165 `[OK]`, 0 falha** nos `.mjs` (baseline citava 1 falha ambiental em `test_ios_assets.mjs`; neste worktree `web/ios/` existe e o teste passou — não é regressão, é diferença de ambiente já esperada pelo guardrail do plano).
- `npx vite build` (web/) — build OK (aviso de chunk >500kB pré-existente, não introduzido por este plano).
- `git diff --quiet web/src/App.jsx web/src/copy.js server/app/conceitos.py server/app/main.py docs/AJUDA.md` — vazio (D-04 confirmado; nenhum arquivo de produto tocado).

## Deviations from Plan

None — plano executado exatamente como escrito. Um ajuste textual sem efeito
de comportamento: o docstring de `test_telas_paridade.py` inicialmente usava
a palavra "subprocess" em prosa (não em código), o que fazia
`grep -c "subprocess"` retornar 1 em vez do 0 exigido pela acceptance
criteria — reescrito para "invoca um processo node" antes do commit, sem
mudar a asserção nem o comportamento do teste.

## Known Stubs

Nenhum. `web/src/telas.js` não tem consumidor neste plano por desenho
(repo_guardrail: "este plano NÃO edita App.jsx") — não é um stub, é o
registro nascendo como rede de segurança antes da religação (41-02).

## Threat Flags

Nenhum. As superfícies tocadas (módulo puro sem I/O, dois arquivos de teste
que só leem fonte como texto) estão inteiramente dentro do `threat_model` do
plano (T-41-01/T-41-02/T-41-03, todas com disposition `mitigate` já
endereçada pelos dois testes de paridade + fixture de equivalência).

## Self-Check: PASSED

- `web/tests/fixtures/gerar_telas_baseline_41.mjs` — FOUND
- `web/tests/fixtures/telas_baseline_41.json` — FOUND
- `web/src/telas.js` — FOUND
- `web/tests/test_telas_registro.mjs` — FOUND
- `server/tests/test_telas_paridade.py` — FOUND
- commit `b80587b` (Task 1) — FOUND em `git log --oneline`
- commit `b5ca27b` (Task 2 RED) — FOUND
- commit `15e01ad` (Task 2 GREEN) — FOUND
- commit `b097351` (Task 3) — FOUND
