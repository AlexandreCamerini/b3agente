---
phase: 51-seu-dia-na-bolsa
plan: 02
subsystem: vocabulário (skill_ref ↔ copy.js)
tags: [templates, espelho, guardião, ENG-07]
requires: ["51-00"]
provides: ["skill_ref.DIA_NA_BOLSA", "skill_ref.dia_na_bolsa_txt", "skill_ref.dia_na_bolsa_n_variantes", "PUSH_RADAR.corpo_ontem_alvo/stop", "copy.js diaNaBolsa/diaNaBolsaTxt/diaNaBolsaNVariantes"]
affects: ["51-05", "51-08"]
key-files:
  created: [server/tests/test_dia_na_bolsa_vocab.py]
  modified: [server/app/skill_ref.py, web/src/copy.js, web/tests/test_vocabulario_espelho.mjs]
requirements: [ENG-07, ENG-02, ENG-10]
metrics:
  completed: 2026-11-18
  tasks: 2
---

# Fase 51 Plano 02: Templates e espelho do card "Seu dia na bolsa" Summary

`DIA_NA_BOLSA` (96 chaves por modo, regras com 3-4 variantes, alvo e stop com 4 cada) em `skill_ref.py`, espelhado byte a byte em `COPY.estudo/operador.diaNaBolsa`, com render `dia_na_bolsa_txt`/`diaNaBolsaTxt` e guardião de vocabulário proibido.

## Commits
- `feat(51-02)` templates + guardião Python (`server/app/skill_ref.py`, `server/tests/test_dia_na_bolsa_vocab.py`)
- `feat(51-02)` espelho `copy.js` + `test_vocabulario_espelho.mjs` ampliado

## Contrato para 51-05 / 51-08
- `dia_na_bolsa_txt(modo, chave_base, variante, vals)` ↔ `diaNaBolsaTxt(mode, chaveBase, variante, vals)`; `dia_na_bolsa_n_variantes(base, modo)` ↔ `diaNaBolsaNVariantes(base, mode)`.
- Chaves: fixas (`titulo`, `kicker`, `carimbo`, `label_f1..3`, `chip_*`, `placar_semana`, `mais_n`, `f2_carteira_ibov`, `f2_ibov_indisponivel`, `ver_conceito`, `selo_p95`, `selo_atr`, `convite_*`, `erro_*`, `atrasado`, `sr_carregando`, `config_rotulo`, `decisao_4sem[_um|_zero]`); variantes: `chamada_f1/f2/f3`, `f1_alvo|stop|expirou|sem_gatilho`, `f2_stop_subiu|breakeven|stop_executado|alvo_executado|pendente_executada|entrada_auto`, `f3_ibov_raro|amplitude|gap|max52|min52|atr_ativo`; perguntas `f3_pergunta_*` (Operador = "").
- Convenções de placeholders (comentário em `skill_ref.py`): `{pct}` sempre sem sinal, direção em `{direcao}` ("subiu"/"caiu" no IBOV, "subiram"/"caíram" na amplitude, "acima"/"abaixo" no gap); `{R}` = "+1,8R"; `{stop}` é o preço em R$ de stop executado/movido. Placeholder ausente -> "—".
- `PUSH_RADAR.corpo_ontem_alvo/stop` ("Ontem: {T} ..."), sem espelho em copy.js (decisão da divergência 5), travados só pelo guardião Python.

## Deviations from Plan
**1. [Rule 3 - Bloqueio] `erro_tentar` = "Tentar novamente" (UI-SPEC dizia "Tentar de novo").** O guardião de espelho (item 5) reprova qualquer valor do dict que apareça literal em `App.jsx`, e "Tentar de novo" já existe em `App.jsx` (L8752, 9464, 9602, 11482). Mantive o guardião intacto e troquei o texto do template. Se o Alex preferir "Tentar de novo", exige rever o guardião (alternativa não adotada). 51-08 deve ler `erro_tentar` do espelho.

**2. Execução:** o plano não pedia TDD; guardião escrito junto com a implementação e rodado verde.

## Verificação
- `pytest tests/test_dia_na_bolsa_vocab.py tests/test_skill_ref.py` -> 59 passed.
- `node web/tests/test_vocabulario_espelho.mjs` -> "todos os testes passaram".
- `npx vite build` (web/) -> ok.
- Não rodados (fora do escopo, regra de custo): suíte canônica, loop completo de `web/tests/*.mjs`, `cap copy ios`.

## Known Stubs
Nenhum.

## Threat Flags
Nenhum. T-51-03 (substituição só de `{placeholder}` por string; sem HTML) e T-51-04 (guardião de vocabulário/verbo de ordem) mitigados.

## Self-Check: PASSED
- Arquivos criados/modificados existem; 2 commits presentes; STATE.md e ROADMAP.md intocados.
