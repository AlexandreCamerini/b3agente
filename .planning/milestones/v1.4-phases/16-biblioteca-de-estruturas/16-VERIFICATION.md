---
phase: 16-biblioteca-de-estruturas
verified: 2026-09-02T22:35:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 16: Biblioteca de estruturas Verification Report

**Phase Goal:** Venda coberta e put de proteção migram do motor single-leg
(Fase 14) para o motor comum (Fase 15); collar entra como nova composição de
2 pernas.

**Verified:** 2026-09-02T22:35:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria + plan must_haves)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Venda coberta (LIB-01) gerada pelo motor de N pernas, não pelo motor single-leg isolado | ✓ VERIFIED | `server/app/opcoes_lastreadas.py:218-222` chama `opcoes_motor.rastrear()` para selecionar a call; `_candidato_valido`/`_escolher_contrato`/`_LIQUIDEZ_MINIMA` locais não existem mais no arquivo (grep confirma 0 ocorrências fora de comentário) |
| 2 | Put de proteção (LIB-02) gerada pelo mesmo motor de N pernas, mesma fonte de seleção/payoff que a venda coberta | ✓ VERIFIED | Mesmo bloco `propor()` (linhas 232-238) usa `opcoes_motor.rastrear()` para a put; `estrutura`/`caixa` calculados por `opcoes_motor.avaliar()` (linhas 298, 305), idêntico caminho ao da call coberta |
| 3 | Collar (LIB-03) combina call vendida + put comprada num único payoff consolidado (custo líquido, ganho/perda máximos, breakevens, delta somado) | ✓ VERIFIED | `_propor_collar()` (linhas 41-155) monta 3 pernas (ação+call+put) e chama `opcoes_motor.avaliar(pernas)` UMA vez (linha 86); teste `test_opcoes_collar.py` afirma `ganho_ilimitado is False and perda_ilimitada is False` (travado dos dois lados) |
| 4 | `propor()` genuinamente delega a `opcoes_motor.rastrear()` — não há uma segunda implementação de régua de liquidez sob outro nome | ✓ VERIFIED | Leitura completa de `opcoes_lastreadas.py`: nenhuma função `_candidato_valido`/`_escolher_contrato` remanescente; `grep -c 'opcoes_motor.rastrear('` = 3 (call_coberta, put_protecao, collar); nenhuma comparação de strike/liquidez feita fora do motor comum |
| 5 | Vocabulário do collar existe nos dois modos (operador/educacional) em `skill_ref.py`, e é a ÚNICA origem da manchete | ✓ VERIFIED | `skill_ref.py:531,544` — chaves `collar` em ambos sub-dicts de `OPCOES_LASTREADAS`; `grep -rn "trava protetora\|abate o custo"` em `server/app/*.py` e `web/src/*.js(x)` só encontra ocorrências em `skill_ref.py` (as frases) e comentários/docstrings explicativos em `main.py` (não compõem texto exibido); guardião AST `test_nenhum_modulo_backend_fora_do_skill_ref_compoe_manchete_do_collar` e `test_nenhum_arquivo_front_compoe_manchete_do_collar` passam |
| 6 | A chave `collar` não cai no fallback `sem_setup` | ✓ VERIFIED | Teste `test_collar_nao_e_servido_pelo_fallback_sem_setup` passa; frases são distintas por asserção direta |
| 7 | Nenhuma estrutura de mais de uma perna é executada pela rota `/api/options/lastreada/abrir` — recusa do servidor, com motivo nomeado, antes de qualquer escrita | ✓ VERIFIED | `server/app/main.py:2454-2456` levanta `HTTPException(400, "Estrutura de mais de uma perna não é executada por esta rota.")` ANTES de qualquer leitura de `contractSymbol`/chamada a `store.*`; testes `test_abrir_recusa_estrutura_collar_por_tipo_400_sem_efeito_colateral` e `test_abrir_recusa_pernasContratos_de_duas_entradas_mesmo_sem_declarar_tipo` afirmam 400 + `cash`/`optionPositions` inalterados após a chamada (não só o status code) |
| 8 | Cliente que declara `multiperna=1` recebe o collar completo pela rota de proposta; cliente publicado (sem o parâmetro) continua recebendo exatamente a resposta de hoje | ✓ VERIFIED | `main.py:2349` tipagem `multiperna: bool = False`, repassado nomeado a `propor()` (linha 2416); testes de rota cobrem `?multiperna=1`→collar, ausência→`caixa_insuficiente` preservado, `?multiperna=0/false`→ausência, `?multiperna=banana`→422 |
| 9 | Nenhum arquivo `web/` foi tocado nesta fase (fase backend-only) | ✓ VERIFIED | `git diff --stat 7f293ba..HEAD -- web/` vazio; `git status --porcelain web/` vazio |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `server/app/opcoes_lastreadas.py` | `propor()`/`_propor_collar()` apoiados no motor comum | ✓ VERIFIED | 3x `opcoes_motor.rastrear(`, 4x `opcoes_motor.avaliar(`, `perna_de_acao(` presente; `_candidato_valido`/`_escolher_contrato`/`_LIQUIDEZ_MINIMA` ausentes |
| `server/app/skill_ref.py` | Vocabulário `collar` nos dois modos | ✓ VERIFIED | Linhas 531 (operador) e 544 (educacional), textos distintos, sem valor sinalizado em R$ |
| `server/app/main.py` | `multiperna` exposto na rota de proposta + trava de execução em `/lastreada/abrir` | ✓ VERIFIED | `multiperna: bool = False` (linha 2349), repasse nomeado (linha 2416), trava 400 (linhas 2454-2456) antes de qualquer mutação de estado |
| `docs/adr/025-collar-e-estrutura-multiperna.md` | Registro das 5 decisões da fase | ✓ VERIFIED | 8 seções `## `, 5 decisões numeradas cada com alternativa descartada; seção dedicada "Limitação conhecida — guarda por autoidentificação" documenta explicitamente o hardening pendente para a Fase 17 |
| `server/tests/test_opcoes_collar.py`, `test_opcoes_collar_vocab.py`, testes atualizados em `test_opcoes_lastreadas_proposta.py`/`test_opcoes_gatilho.py`/`test_opcoes_motor.py`/`test_opcoes_lastreadas_rotas.py` | Guardiões de comportamento e forma | ✓ VERIFIED | Suíte alvo roda e passa (ver Behavioral/Probe abaixo) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `opcoes_lastreadas.py` | `opcoes_motor.rastrear` | seleção de contrato (call/put/collar) | ✓ WIRED | 3 chamadas confirmadas por leitura direta do código |
| `opcoes_lastreadas.py` | `opcoes_motor.avaliar` | payoff estrutura + caixa (2x single-leg + 2x collar) | ✓ WIRED | 4 chamadas confirmadas |
| `opcoes_lastreadas.py` | `opcoes_motor.perna_de_acao` | perna de lastro | ✓ WIRED | usada em `propor()` (linha 292) e `_propor_collar()` (linha 85) |
| `opcoes_lastreadas.py` | `skill_ref.opcoes_lastreadas_txt` | manchete/didática do collar | ✓ WIRED | linhas 104,107 — nenhum texto literal de manchete no motor (`grep -c 'Vender {n} call'` em `opcoes_lastreadas.py` = 0) |
| `main.py::options_proposta` | `opcoes_lastreadas.propor` | repasse de `multiperna` | ✓ WIRED | linha 2416 |
| `main.py::options_lastreada_abrir` | trava de execução | checagem `tipo`/`pernasContratos` ANTES de `store.*` | ✓ WIRED | ordem de código confirmada (linhas 2436-2461); testes confirmam ausência de efeito colateral |

### Behavioral Spot-Checks / Probe Execution

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Suíte alvo da fase (com rede liberada, fora do sandbox padrão) | `cd server && .venv/bin/python -m pytest tests/test_opcoes_lastreadas_proposta.py tests/test_opcoes_collar_vocab.py tests/test_opcoes_collar.py tests/test_opcoes_lastreadas_rotas.py tests/test_opcoes_gatilho.py tests/test_opcoes_motor.py -q` | 141 passed | ✓ PASS |
| Mesma suíte dentro do sandbox padrão (rede bloqueada) | idem, sem disable de sandbox | 140 passed, 1 failed (`test_vender_posicao_100_por_cento_travada_via_sell_devolve_400`, erro `[Errno 1] Operation not permitted` no Yahoo) | ✓ PASS (falha confirmada como bloqueio de rede do sandbox, pré-existente e documentado em 15-VERIFICATION.md — não regressão desta fase) |
| Suíte completa do backend | `cd server && .venv/bin/python -m pytest tests/ -q` (rede liberada) | 1965 passed, 1 skipped, 0 failed | ✓ PASS |
| Guardião CVM do collar (AST) | `pytest tests/test_opcoes_collar_vocab.py -v` | 11/11 passed, incluindo os dois testes estruturais que varrem `server/app/*.py` e `web/src/*.js(x)` | ✓ PASS |
| Teste da trava de execução server-side | Leitura direta de `test_abrir_recusa_estrutura_collar_por_tipo_400_sem_efeito_colateral` e `test_abrir_recusa_pernasContratos_de_duas_entradas_mesmo_sem_declarar_tipo` — ambos incluídos na execução acima | 400 + `cash`/`optionPositions` inalterados | ✓ PASS |
| `git diff --stat` de `web/` desde o início da fase | `git diff --stat 7f293ba..HEAD -- web/` | vazio | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| LIB-01 | 16-01, 16-04 | Venda coberta via motor de N pernas | ✓ SATISFIED | `opcoes_motor.rastrear`/`avaliar` no caminho `call_coberta`; testes verdes |
| LIB-02 | 16-01, 16-04 | Put de proteção via motor de N pernas | ✓ SATISFIED | mesmo motor, caminho `put_protecao`; testes verdes |
| LIB-03 | 16-02, 16-03, 16-04 | Collar (trava protetora) como composição de 2 pernas | ✓ SATISFIED | `_propor_collar` + vocabulário + rota + trava de execução, todos verificados |

Nota: `.planning/REQUIREMENTS.md` ainda lista LIB-01/02/03 como `[ ]`/"Pending" — checkbox de status é atualizado em passo separado do processo (mesmo padrão observado no fechamento da Fase 15, commit `c9451f4`), não bloqueia esta verificação.

### Anti-Patterns Found

Nenhum. Scan de `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER` nos arquivos tocados pela fase (`opcoes_lastreadas.py`, `skill_ref.py`, `main.py`, ADR-025) não encontrou nenhuma ocorrência real (os únicos matches de "TODO" em `main.py` são substrings de "TODOS", falso-positivo de grep).

### Human Verification Required

Nenhuma — fase backend-only, sem UI hint no ROADMAP, nenhum item deferido pelo planner via `<verify><human-check>`.

### Gaps Summary

Nenhum gap. Os 4 planos da fase entregam exatamente o que o ROADMAP e os
must_haves de frontmatter prometem, com evidência de código lida diretamente
(não só prosa de SUMMARY):

1. `propor()` e `_propor_collar()` usam genuinamente `opcoes_motor.rastrear()`/
   `avaliar()` — as funções antigas de seleção local (`_candidato_valido`,
   `_escolher_contrato`, `_LIQUIDEZ_MINIMA`) foram removidas de fato, não
   apenas renomeadas.
2. O vocabulário do collar é a única origem da manchete, com guardião
   estrutural (AST) provado por injeção de falha e reversão (documentado no
   16-02-SUMMARY e confirmado por execução direta do teste nesta verificação).
3. A trava de execução em `POST /api/options/lastreada/abrir` de fato recusa
   com 400 antes de qualquer mutação de estado — confirmado lendo a ordem do
   código (a checagem vem antes de `_normalize_ticker`/qualquer leitura de
   `contractSymbol`) e rodando os testes que afirmam `cash`/`optionPositions`
   inalterados após a recusa.
4. A limitação conhecida da trava (guarda por autoidentificação, sem
   re-derivação server-side a partir da cadeia) está documentada
   explicitamente no ADR-025, seção dedicada, marcada como item de hardening
   da Fase 17 — não foi omitida.
5. Nenhum arquivo `web/` foi tocado (fase backend-only, confirmado por diff
   vazio desde o commit de criação do contexto da fase).
6. Suíte alvo e suíte completa do backend passam de fato quando executadas
   nesta sessão, com rede liberada (a única falha sob sandbox padrão é o
   bloqueio de rede pré-existente e documentado, não uma regressão).

---

*Verified: 2026-09-02T22:35:00Z*
*Verifier: Claude (gsd-verifier)*
