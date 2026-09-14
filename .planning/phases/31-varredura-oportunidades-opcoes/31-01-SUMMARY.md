---
phase: 31-varredura-oportunidades-opcoes
plan: 01
subsystem: api
tags: [python, pytest, opcoes, motor-deterministico, curadoria, skill_ref]

# Dependency graph
requires:
  - phase: 30-curadoria-ia-melhores-estruturas
    provides: opcoes_curadoria.py (motor puro, 1 estrutura x 1 vencimento), rankear()/exigir_ranking(), narrativa_user/system
  - phase: 29-opcao-a-descoberto-flag-opt-in
    provides: permitirOpcaoADescoberto (gate de EXECUÇÃO em store.buy_option, invariante, não tocado)
provides:
  - premio_liquido_unitario(pernas_opcao) — sinal do prêmio líquido (crédito positivo, débito negativo), reusado pelas 4 estruturas
  - id_candidato(tipo, ticker, expiration, contract_symbol=None, *, strike_call=None, strike_put=None) — identidade estável e total do candidato
  - proximos_vencimentos(expirations, hoje, *, teto=VENCIMENTOS_POR_POSICAO) — teto de 2 vencimentos futuros (consumido pelo Plano 31-02)
  - candidatos_da_posicao() estendida para as 4 estruturas (call_coberta, put_protecao, collar, opcao_a_descoberto), com gate de descoberta permitir_a_descoberto=False (fail-closed, D-05)
  - rankear() com ordem total (4 critérios de desempate, inclui idCandidato)
  - narrativa_user/narrativa_system cientes do tipo de cada estrutura
  - skill_ref.OPCOES_LASTREADAS["opcao_a_descoberto"] nos dois registros (operador/educacional)
affects: [31-02-rota-cache-vencimentos, 31-04-bloco-posicoes-checkpoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reversão deliberada de guardião com nota datada (Fase 30/D1 -> Fase 31/D-04): test_nenhum_filtro_put_no_arquivo virou test_filtro_de_put_existe_desde_a_fase_31_d04"
    - "Gate de descoberta (pulo silencioso) vs. gate de execução (raise + registrar_rejeicao) são deliberadamente não-unificados — mesmo flag, semânticas opostas por desenho"
    - "Assimetria sinal-no-campo/módulo-na-frase: premioUnitario/premioTotal carregam o sinal real; a frase canônica interpola abs(premioTotal) para não ler 'pagaria R$ -65,00'"

key-files:
  created: []
  modified:
    - server/app/opcoes_curadoria.py
    - server/app/skill_ref.py
    - server/tests/test_opcoes_curadoria.py

key-decisions:
  - "Rótulo de narração do collar mudou de 'trava protetora (collar)' para 'collar (call vendida + put comprada)' — a string-âncora 'trava protetora' é guardada por CVM em test_opcoes_collar_vocab.py (manchete do collar só nasce em skill_ref.py); achado só na suíte canônica completa, não nos testes do módulo isolado"
  - "premio_liquido_unitario recebe SÓ pernas de opção, nunca a perna de ação — incluí-la somaria o preço do papel ao prêmio"
  - "opcao_a_descoberto desta fase é compra de call a seco (caminho já gateado pela Fase 29); venda de call nua não entra — perda_maxima=None (ilimitada) seria descartada pela porta já existente, e publicar razão sobre perda indefinida violaria o princípio 4 do CLAUDE.md"

requirements-completed: [SC-2, SC-3, SC-4]

# Metrics
duration: 45min
completed: 2026-09-14
---

# Phase 31 Plan 01: Motor puro das 4 estruturas Summary

**`opcoes_curadoria.candidatos_da_posicao` estendida de "1 estrutura x 1 vencimento" (Fase 30) para as 4 estruturas do motor interno sobre uma cadeia em memória, com gate de descoberta `permitir_a_descoberto=False` fail-closed (D-05) e ranking de ordem total via 4 critérios de desempate.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-09-14T15:10:00Z (baseline medida em `714101b`)
- **Completed:** 2026-09-14T15:55:00Z
- **Tasks:** 3
- **Files modified:** 3 (`server/app/opcoes_curadoria.py`, `server/app/skill_ref.py`, `server/tests/test_opcoes_curadoria.py`)

## Baseline (medida ANTES da primeira edição, em `714101b`)

`bash scripts/executar.sh --testes` (sandbox local nega `context.load_verify_locations` — `PermissionError: Operation not permitted` — em 27 testes que fazem handshake TLS; rodado com `dangerouslyDisableSandbox: true` para o número real, mesma causa já documentada na memória do projeto como "sandbox mente"):

```
2864 passed, 5 skipped, 3 xfailed, 991 warnings in 158.04s
147/147 .mjs OK
exit 0
```

## Números finais (após as 3 tasks)

```
cd server && .venv/bin/python -m pytest tests/test_opcoes_curadoria.py tests/test_opcoes_curadoria_narrativa.py tests/test_opcoes_collar_vocab.py tests/test_skill_ref.py -q
97 passed, 3 warnings (recorte do módulo — curadoria + narrativa + collar_vocab; 69/69 só em test_opcoes_curadoria.py)
```

```
bash scripts/executar.sh --testes  (dangerouslyDisableSandbox, mesma causa acima)
2899 passed, 5 skipped, 3 xfailed, 0 failed, 991 warnings in 159.03s
147/147 .mjs OK
exit 0
```

Delta: **+35 pytest** (todos os guardiões novos das 3 tasks), **+0 .mjs** (plano não toca `web/`). Nenhuma regressão contra a baseline.

## Accomplishments

- `premio_liquido_unitario()`, `id_candidato()` e `proximos_vencimentos()` — 3 funções puras novas, reusadas pelas 4 estruturas.
- `candidatos_da_posicao()` gera `call_coberta`, `put_protecao`, `collar` e `opcao_a_descoberto` (opt-in) a partir de UMA cadeia já em memória — zero chamada de rede nova dentro do módulo.
- Gate de descoberta `permitir_a_descoberto=False` (D-05) — primeiro ponto do sistema onde `permitirOpcaoADescoberto` é lido na DESCOBERTA, separado e deliberadamente diferente do gate de EXECUÇÃO já existente (`store.buy_option`).
- `rankear()` com ordem total (4 critérios), resolvendo o empate estrutural de dois collars sem `contractSymbol`.
- `narrativa_user`/`narrativa_system` cientes do tipo, com regra explícita contra descrever prêmio negativo como receita.
- Docstrings do módulo e de `candidatos_da_posicao` atualizados, removendo a linguagem "pare" da Fase 30/D1/D3 e citando a supersessão deliberada (Fase 31/D-04/D-01).

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: prêmio líquido com sinal, idCandidato, proximos_vencimentos e a frase da opção a descoberto** - `02cc154` (feat)
2. **Task 2: ramos put_protecao e collar em candidatos_da_posicao** - `8e9e3e5` (feat)
3. **Task 3: ramo opcao_a_descoberto com gate de descoberta (D-05), ordem total e narração ciente do tipo** - `331c842` (feat)

_TDD: cada task seguiu RED (testes escritos e confirmados falhando com as funções ainda ausentes) → GREEN (implementação, testes verdes) num único commit por task — mesmo padrão de granularidade do resto desta base (commit por task, não por fase RED/GREEN separada)._

## Files Created/Modified

- `server/app/opcoes_curadoria.py` — as 3 funções puras novas, os 2 ramos novos (put_protecao/collar) e o ramo opcao_a_descoberto, ordem total em `rankear`, narração ciente do tipo, docstrings atualizados.
- `server/app/skill_ref.py` — chave `opcao_a_descoberto` em `OPCOES_LASTREADAS["operador"]` e `["educacional"]`.
- `server/tests/test_opcoes_curadoria.py` — ~50 testes novos; 1 guardião da Fase 30 invertido com nota datada (`test_nenhum_filtro_put_no_arquivo` → `test_filtro_de_put_existe_desde_a_fase_31_d04`).

## Interface para os Planos 31-02/31-04: campos de cada tipo de candidato

Todos os 4 tipos compartilham o mesmo envelope base; `collar` acrescenta 3 campos próprios (2 pernas, sem contrato único).

**Campos comuns a `call_coberta` / `put_protecao` / `opcao_a_descoberto`:**
`tipo`, `ticker`, `contractSymbol`, `optionType`, `strike`, `expiration`, `diasParaVencimento`, `contratos`, `qtyAcoes`, `premioUnitario` (sinal real: positivo=crédito, negativo=débito), `premioTotal` (mesmo sinal), `liquidez` (via `_bloco_liquidez`), `estrutura` (dict completo de `opcoes_motor.avaliar`), `razao` (premioUnitario/perda_maxima), `manchete`, `didatica`, `precoObjeto`, `idCandidato`.

**`collar` (mesmo envelope + 3 campos, 3 nulos por desenho):**
`contractSymbol: None`, `optionType: None`, `strike: None` (sem contrato único — preencher com uma perna mentiria), mais `strikeCall`, `strikePut`, `pernasContratos` (lista de 2 dicts: `contractSymbol`/`optionType`/`lado`/`strike`/`premioUnitario` de cada perna). `premioUnitario`/`premioTotal`/`razao` no nível do candidato SÃO numéricos (ao contrário de `_propor_collar`, que zera esses campos por não precisar rankear).

**Diferenças de assinatura por tipo (sinal/gate):**
- `call_coberta`: `premioUnitario` sempre positivo (venda de call coberta, sempre crédito).
- `put_protecao`: `premioUnitario` sempre negativo (compra, débito) — permanece no ranking, rankeado mal por desenho (D-06).
- `collar`: sinal natural — crédito quando a call vale mais que a put, débito no caso contrário.
- `opcao_a_descoberto`: `premioUnitario` sempre negativo (compra a seco); `contratos` fixo em `CONTRATOS_A_DESCOBERTO` (1), `qtyAcoes` fixo em 100 — não depende de `qty_livre` da posição (sem lastro); só existe quando `permitir_a_descoberto=True`.

**Contrato de `rankear()`/`exigir_ranking()`:** inalterado na forma — ainda aceita dicts mínimos sem `idCandidato` (usa `.get(...) or <default>`); a chave de ordenação cresceu para `(-razao, -premioUnitario, contractSymbol, idCandidato)`.

## Decisions Made

- **Rótulo de narração do collar renomeado** de `"trava protetora (collar)"` (sugestão literal do plano) para `"collar (call vendida + put comprada)"` — a string-âncora `"trava protetora"` é protegida por um guardião CVM já existente (`test_opcoes_collar_vocab.py::test_nenhum_modulo_backend_fora_do_skill_ref_compoe_manchete_do_collar`, Fase 16/LIB-03): nenhum arquivo fora de `skill_ref.py` pode compor texto que se pareça com a manchete do collar. O rótulo de TIPO da narração não é a manchete, mas o texto literal colidia com a string proibida — só apareceu ao rodar a suíte canônica COMPLETA, não nos testes do módulo isolado (`test_opcoes_curadoria.py` e `test_opcoes_curadoria_narrativa.py` sozinhos não incluem `test_opcoes_collar_vocab.py`). Guardião original intocado.
- `premio_liquido_unitario` recebe só pernas de OPÇÃO, nunca a perna de ação (plano já especificava isso; confirmado com o sinal correto via `opcoes_payoff.custo_liquido`: `sinal=+1` compra/`-1` venda, `custo_liquido = -lastPrice` para venda de call ⇒ `premio_liquido_unitario = +lastPrice`).
- Estrutura "a descoberto" desta fase é compra de call a seco (caminho já gateado pela Fase 29); venda de call nua fica de fora — `perda_maxima=None` (perda ilimitada) já seria descartada pela porta existente, e publicar razão sobre perda indefinida violaria o princípio 4 do CLAUDE.md (decisão já registrada no próprio plano, confirmada na implementação sem desvio).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug, achado só na suíte canônica completa] Rótulo do collar colidia com guardião CVM**
- **Found during:** Task 3, ao rodar `bash scripts/executar.sh --testes` (verificação final, não nos testes do módulo isolado)
- **Issue:** `_ROTULO_TIPO["collar"] = "trava protetora (collar)"` (texto literal sugerido pelo próprio plano) continha a string-âncora `"trava protetora"`, guardada desde a Fase 16 (LIB-03) por `test_opcoes_collar_vocab.py` — nenhum arquivo fora de `skill_ref.py` pode compor esse texto (guardrail regulatório CVM: a manchete do collar nasce só do motor determinístico via `skill_ref`).
- **Fix:** rótulo trocado para `"collar (call vendida + put comprada)"`, descritivo e sem a string proibida. Comentário no código explica a colisão para que uma manutenção futura não reintroduza o mesmo texto.
- **Files modified:** `server/app/opcoes_curadoria.py`, `server/tests/test_opcoes_curadoria.py` (assert do teste de narração atualizado para o novo texto).
- **Verification:** `pytest tests/test_opcoes_curadoria.py tests/test_opcoes_curadoria_narrativa.py tests/test_opcoes_collar_vocab.py -q` → 97 passed; suíte canônica completa → 2899 passed, 0 failed.
- **Committed in:** `331c842` (parte do commit da Task 3 — achado e corrigido antes do commit, não depois).

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug de nomenclatura que colidia com guardrail regulatório pré-existente).
**Impact on plan:** Correção pontual de string literal, sem mudança de comportamento/campo. Nenhum scope creep — a manchete real do collar (em `skill_ref.py`) não foi tocada; só o rótulo de tipo usado na narração de IA.

## Issues Encountered

None além do desvio documentado acima.

## Provas negativas (comando + saída real)

**1. `proximos_vencimentos` (Task 1) — corpo trocado por `return []` fixo:**
```
$ .venv/bin/python -m pytest tests/test_opcoes_curadoria.py -k proximos_vencimentos -q
4 failed, 3 passed, 45 deselected in 0.06s
FAILED test_proximos_vencimentos_feliz_descarta_passado_ordena_teto_2
FAILED test_proximos_vencimentos_tolera_item_malformado_none_e_data_invalida
FAILED test_proximos_vencimentos_respeita_teto_customizado
FAILED test_proximos_vencimentos_hoje_nunca_entra_estritamente_futuro
```
Revertido; `git diff` limpo (confirmado por reexecução verde: 73 passed).

**2. Gate D-05 (Task 3) — `if permitir_a_descoberto:` trocado por `if True:`:**
```
$ .venv/bin/python -m pytest tests/test_opcoes_curadoria.py -k "permitir_a_descoberto" -q
2 failed, 2 passed, 65 deselected in 0.06s
FAILED test_permitir_a_descoberto_false_por_padrao_nao_gera_naked
FAILED test_permitir_a_descoberto_explicito_false_tambem_nao_gera_naked
```
Revertido; `git diff --stat` limpo (confirmado por reexecução verde: 86 passed em curadoria+narrativa).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plano 31-02** (rota + cache de vencimentos) consome `proximos_vencimentos()` e `VENCIMENTOS_POR_POSICAO` diretamente, e precisa invocar `candidatos_da_posicao(..., permitir_a_descoberto=cfg.get("permitirOpcaoADescoberto"))` explicitamente por posição — o parâmetro é keyword-only e fail-closed, então um chamador que esqueça de passá-lo nunca vaza oportunidade a descoberto (mas também nunca a MOSTRA, mesmo pra quem tem o flag ligado — a leitura de `cfg` é responsabilidade do 31-02).
- **Plano 31-04** (bloco de Posições + checkpoint humano) consome a lista de campos por tipo documentada acima — em particular, o front precisa tratar `collar.contractSymbol === null` (usar `idCandidato` como chave de React, não `contractSymbol`) e exibir `premioUnitario`/`premioTotal` com o sinal correto (nunca assumir positivo).
- Nenhum bloqueio conhecido. `git status --short` mostra só os 3 arquivos declarados em `files_modified` do plano.

---
*Phase: 31-varredura-oportunidades-opcoes*
*Completed: 2026-09-14*

## Self-Check: PASSED

- FOUND: `.planning/phases/31-varredura-oportunidades-opcoes/31-01-SUMMARY.md`
- FOUND: `02cc154` (Task 1 commit)
- FOUND: `8e9e3e5` (Task 2 commit)
- FOUND: `331c842` (Task 3 commit)
