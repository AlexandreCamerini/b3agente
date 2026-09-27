---
phase: 39-reestrutura-o-de-navega-o-da-aba-op-es
plan: 01
subsystem: api
tags: [black-scholes, options-pricing, fastapi, python, curadoria, ranking]

# Dependency graph
requires: []
provides:
  - "opcoes_curadoria.py: piso de admissão por probabilidade OTM (probOtm >= 0.60, Black-Scholes) — D-08"
  - "opcoes_curadoria.py: ordenação por prêmio anualizado (D-09), substituindo prêmio/perda máxima"
  - "opcoes_curadoria.aplicar_piso(): admissão+contagem (admitidosNoPiso/reprovadosNoPiso/semProbabilidade) separada de rankear() — D-10"
  - "GET /api/options/curadoria: meta com pisoProbOtm + as 3 contagens do D-11, inclusive no fallback do except"
  - "main.py: _hv21_do_ativo lazy (1x por ticker por varredura, só quando IV do contrato é inutilizável)"
  - "options_quant.TAXA_LIVRE_DE_RISCO_REFERENCIA (constante nomeada, valor idêntico ao literal 0.105 anterior)"
affects: ["39-02", "39-03", "39-04", "39-05", "39-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Piso de admissão + critério de ordem são funções SEPARADAS (aplicar_piso vs rankear) — nenhuma delas seleciona contrato (ENG-01 intacto)"
    - "Volatilidade lazy: IV do contrato primeiro, hv21 (candles) só como fallback e só 1x por ticker por varredura — nunca busca incondicional"
    - "Reversão deliberada datada no código: comentário + guardião renomeado, nunca teste apagado"

key-files:
  created:
    - server/tests/test_opcoes_curadoria_piso.py
  modified:
    - server/app/opcoes_curadoria.py
    - server/app/options_quant.py
    - server/app/options_api.py
    - server/app/main.py
    - server/tests/test_opcoes_curadoria.py
    - server/tests/test_opcoes_curadoria_narrativa.py
    - server/tests/test_opcoes_curadoria_rota.py
    - server/tests/test_curadoria_collar_rota.py

key-decisions:
  - "D-08/D-09/D-10/D-11/D-12 do 39-CONTEXT.md implementados literalmente: piso de 0.60 (Black-Scholes), ordem por prêmio anualizado, aplicar_piso separada de rankear, meta com as 3 contagens, zero toque em opcoes_lastreadas.py"
  - "test_curadoria_collar_rota.py (fora do files_modified do plano) teve sua fixture alargada (spot±1 -> spot±3/±5) — Rule 1: o piso D-08 é matematicamente correto e a geometria antiga (collar quase ATM) media probOtm ~0.31, abaixo do piso; PISO_PROB_OTM não foi tocado, nada foi monkeypatchado"

patterns-established:
  - "Fixture de opção OTM para testes de curadoria precisa ficar longe o bastante do spot para sobreviver ao piso de 60% (referência: ~10% de distância a 30 dias com IV 0.30 já é suficiente)"

requirements-completed: [NAV-01]

# Metrics
duration: 35min
completed: 2026-09-24
---

# Phase 39 Plan 1: Piso de probabilidade OTM + ordem por prêmio anualizado Summary

**Motor de curadoria (`opcoes_curadoria.py`) trocou o ranking de "prêmio ÷ perda máxima" por piso de admissão (probOtm >= 60%, Black-Scholes) + ordem por prêmio anualizado, com contrato de dado que distingue "nada varrido" de "varreu e ninguém passou no piso".**

## Performance

- **Duration:** 35 min
- **Started:** 2026-09-24T15:45:00Z
- **Completed:** 2026-09-24T16:20:00Z
- **Tasks:** 2
- **Files modified:** 8 (1 criado, 7 modificados)

## Accomplishments
- Lista de Recomendadas (`GET /api/options/curadoria`) só admite candidatos com `probOtm >= 0.60` (Black-Scholes sobre IV do contrato ou, na falta dela, volatilidade histórica de 21 pregões buscada lazy/memoizada 1x por ticker).
- Ordenação dentro do piso passou a ser por prêmio anualizado `(prêmio/spot) × (365/dias)`, não mais razão prêmio/perda máxima.
- Resposta da rota sempre diz por que a lista está vazia: `candidatosAvaliados` (pré-piso), `admitidosNoPiso`, `reprovadosNoPiso`, `semProbabilidade`, `pisoProbOtm` — inclusive no fallback de erro de última instância.
- `exigir_ranking` (a porta entre o motor e a narração por IA) agora recusa qualquer candidato abaixo do piso ou fora da ordem nova — a IA é estruturalmente incapaz de narrar o que o piso reprovou.
- Zero toque em `opcoes_lastreadas.py` (D-12) — confirmado por `git diff --stat` vazio em todas as verificações.

## Task Commits

Cada task seguiu RED → GREEN (TDD):

1. **Task 1: motor puro — probOtm, prêmio anualizado, piso de admissão, ordem nova**
   - `310c93d` (test): piso de admissão e prêmio anualizado (RED) — `test_opcoes_curadoria_piso.py` criado, 34 testes, falha esperada (funções ainda não existiam)
   - `967ed6c` (feat): piso de probabilidade OTM + ordem por prêmio anualizado na curadoria (GREEN) — `opcoes_curadoria.py`/`options_quant.py`/`options_api.py` + guardiões existentes atualizados com nota de reversão

2. **Task 2: rota — hv21 lazy por ticker, piso antes do rankear, meta do D-11**
   - `cad1ae7` (test): rota da curadoria com piso e hv21 lazy (RED) — casos novos em `test_opcoes_curadoria_rota.py`, falha esperada (main.py ainda não aplicava piso)
   - `c936d62` (feat): meta do piso na rota da curadoria + hv21 lazy (GREEN) — `main.py` (`_hv21_do_ativo`, `_curadoria_scan_posicao`, `_curadoria_top`, fallback do except) + fixture de `test_curadoria_collar_rota.py` alargada (deviation, ver abaixo)

**Plan metadata:** (este commit, docs)

## Files Created/Modified
- `server/tests/test_opcoes_curadoria_piso.py` - guardião novo do piso/ordem/exigir_ranking/narrativa (34 testes)
- `server/app/opcoes_curadoria.py` - `PISO_PROB_OTM`, `VOL_MIN`/`VOL_MAX`, `vol_do_contrato`, `prob_otm`, `premio_anualizado`, `aplicar_piso`; `candidatos_da_posicao` ganha `hv21` kwarg e calcula `probOtm`/`volatilidadeFonte`/`premioAnualizado` nos 4 tipos de estrutura; `rankear`/`exigir_ranking` usam `premioAnualizado`; `narrativa_system`/`narrativa_user` reescritos (nunca mais "razão")
- `server/app/options_quant.py` - `TAXA_LIVRE_DE_RISCO_REFERENCIA = 0.105` (constante nomeada, valor idêntico ao literal anterior)
- `server/app/options_api.py` - `_enrich_contract` usa a constante nomeada em vez do literal `0.105`
- `server/app/main.py` - `_hv21_do_ativo` (novo), `_curadoria_scan_posicao` com cache lazy de hv21 por ticker, `_curadoria_top` aplica `aplicar_piso` antes de `rankear` e estende `meta`, fallback do `except` em `options_curadoria` ganha as 3 contagens
- `server/tests/test_opcoes_curadoria.py` - builders sintéticos (`_candidato_sintetico`/`_sintetico_por_tipo`) ganham `premioAnualizado`/`probOtm`; 2 testes renomeados/comentados com nota de reversão datada; nenhum teste removido (61 antes, 61 depois)
- `server/tests/test_opcoes_curadoria_narrativa.py` - builder `_item` ganha `premioAnualizado`/`probOtm`/`volatilidadeFonte`
- `server/tests/test_opcoes_curadoria_rota.py` - 7 casos novos (contagem de `get_history`, candidato abaixo do piso, contagens do D-11, ordem por prêmio anualizado)
- `server/tests/test_curadoria_collar_rota.py` - fixture `_cadeia`/`_cadeia_2calls` alargada (deviation, ver abaixo)

## Decisions Made
- Piso e ordem implementados como funções PURAS separadas (`aplicar_piso` vs `rankear`) — nenhuma delas escolhe contrato dentro da cadeia, preservando ENG-01 (nota explícita no código, citando `opcoes_payoff.py:22-24`).
- `hv21` é buscada de forma LAZY e memoizada por TICKER dentro de uma varredura (nunca incondicional): `candle_provider.get_history` debita orçamento e não tem cache, então só é chamada quando algum candidato daquele ticker ficou sem IV utilizável.
- Taxa livre de risco continua o literal histórico `0.105`, agora nomeado (`TAXA_LIVRE_DE_RISCO_REFERENCIA`) — troca por Selic/CDI real é melhoria futura deferida explicitamente no 39-CONTEXT.md, não bloqueia esta fase.
- `razao` continua no dict de cada candidato (D-14: só deixa de ser EXIBIDA pela UI numa fase futura, o campo em si não morre e continua sendo usado como critério de desempate secundário nos testes legados).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug/fixture pré-existente incompatível com nova regra] Fixture de `test_curadoria_collar_rota.py` alargada**
- **Found during:** Task 2, verificação cruzada (`test_curadoria_collar_rota.py` faz parte do `<verify>` do Plano mas não do `<files>`)
- **Issue:** `_cadeia()`/`_cadeia_2calls()` desse arquivo construíam call/put a apenas R$1,00 do spot (~3% OTM a 30 dias) — geometria escrita ANTES do piso D-08 existir. Com IV 0.30 e a taxa de referência de 10,5%, o `probOtm` combinado do collar medido nessa geometria é ~0.31, bem abaixo do piso de 0.60: o collar deixava de aparecer em `top`, e 9 testes que localizam o candidato via `GET /api/options/curadoria` para depois executá-lo via `POST /api/options/curadoria/abrir-collar` quebravam.
- **Fix:** Strikes alargados para spot±3 (era ±1) em `_cadeia` e spot+3/+5/-3 (era +1/+3/-1) em `_cadeia_2calls`, verificado analiticamente (Black-Scholes calculado à mão, ver comentário no código) que o `probOtm` combinado passa a ~0.77, acima do piso. `PISO_PROB_OTM` não foi alterado; nenhum monkeypatch do piso foi introduzido. A lógica de re-derivação sob teste (`options_curadoria_abrir_collar`) é intocada — a mudança é só na fixture.
- **Files modified:** `server/tests/test_curadoria_collar_rota.py`
- **Verification:** 13/13 testes do arquivo voltaram a passar; suíte combinada dos 5 arquivos de curadoria (155 testes) verde.
- **Committed in:** `c936d62` (parte do commit GREEN da Task 2, documentado no corpo do commit)

---

**Total deviations:** 1 auto-fixed (Rule 1, fixture fora do escopo declarado de arquivos do plano)
**Impact on plan:** Necessário para que o piso D-08 (especificado pelo plano) não regrida um caminho de execução real (abrir collar) só porque a fixture de teste nasceu antes da regra existir. Nenhum enfraquecimento do piso; nenhum código de produção tocado além do já previsto no plano.

## Issues Encountered
- Nenhum bloqueante. O único ponto de atenção real foi a tensão entre a acceptance criteria do Task 2 ("`test_curadoria_collar_rota.py` passa SEM edição") e o comportamento matematicamente correto do piso D-08 sobre uma fixture pré-existente com strikes muito próximos do spot — resolvido como Rule 1 acima, com nota explícita no código e neste SUMMARY (não escondido).

## User Setup Required
None - nenhuma configuração de serviço externo necessária. Mudança é 100% backend, sem novo env var, sem nova dependência.

## Next Phase Readiness
- O contrato de dado do D-11 (`pisoProbOtm`/`admitidosNoPiso`/`reprovadosNoPiso`/`semProbabilidade`) já está disponível na resposta de `GET /api/options/curadoria` para os planos de front (39-03/39-04) construírem os estados vazios corretos da aba Recomendadas.
- Risco já declarado no CONTEXT.md e reconfirmado empiricamente aqui: o piso de 60% quase elimina put de proteção/collar perto do dinheiro da lista publicada — consequência esperada de D-08, não bug; fica para o checkpoint humano do 39-06 decidir se isso é aceitável em produção.
- Nenhum bloqueio para os próximos planos da fase (39-02 em diante).

## Self-Check: PASSED

Arquivos verificados:
- FOUND: server/tests/test_opcoes_curadoria_piso.py
- FOUND: server/app/opcoes_curadoria.py
- FOUND: server/app/options_quant.py
- FOUND: server/app/options_api.py
- FOUND: server/app/main.py
- FOUND: server/tests/test_opcoes_curadoria.py
- FOUND: server/tests/test_opcoes_curadoria_narrativa.py
- FOUND: server/tests/test_opcoes_curadoria_rota.py
- FOUND: server/tests/test_curadoria_collar_rota.py

Commits verificados (git log --oneline --all):
- FOUND: 310c93d
- FOUND: 967ed6c
- FOUND: cad1ae7
- FOUND: c936d62

---
*Phase: 39-reestrutura-o-de-navega-o-da-aba-op-es*
*Completed: 2026-09-24*
