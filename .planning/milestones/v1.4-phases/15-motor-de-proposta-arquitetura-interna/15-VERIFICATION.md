---
phase: 15-motor-de-proposta-arquitetura-interna
verified: 2026-09-02T23:30:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 15: Motor de proposta (arquitetura interna) Verification Report

**Phase Goal:** O motor determinístico de N-pernas, `rastrear()`/`avaliar()`, existe internamente — seleção de contrato, cálculo de payoff N-pernas, limite interno e gatilho técnico — pronto para as estruturas da Fase 16 se apoiarem nele. Sem UI, sem chamada de rede ao b-mcp.
**Verified:** 2026-09-02T23:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `rastrear(cadeia, filtros)` e `avaliar(pernas)` existem em `server/app/opcoes_motor.py` como limite interno trocável por troca de corpo (ROADMAP SC1) | ✓ VERIFIED | Código lido integralmente: `rastrear` (linha 46) e `avaliar` (linha 185) só delegam a `.options_quant`/`.opcoes_payoff`. Guardião `test_eng04_assinatura_de_rastrear_esta_congelada`/`test_eng04_assinatura_de_avaliar_esta_congelada` fixam `(cadeia, filtros)`/`(pernas)` via `inspect.signature`. Guardião `test_eng04_limite_trocavel_opcoes_motor_imports_na_allowlist` fixa allowlist `{options_quant, opcoes_payoff, typing, __future__}`. Guardião `test_eng04_limite_trocavel_opcoes_motor_sem_relogio` proíbe `datetime/date/time/now/today`. |
| 2 | Seleção usa `liquidity_score >= 40` + strike extremo, nunca critério por delta (ROADMAP SC2 / ENG-01) | ✓ VERIFIED | `opcoes_motor._candidato_valido` replica exatamente a régua de `opcoes_lastreadas.py` (lastPrice>0 + `liquidity_score>=liquidez_minima`); `rastrear` ordena por `strike` e fatia — nenhuma referência a `delta` fora de comentário (`grep -vE '^\s*#' ... | grep -c delta` = 0, confirmado). `LIQUIDEZ_MINIMA=40` é fonte única real: `opcoes_lastreadas._LIQUIDEZ_MINIMA = opcoes_motor.LIQUIDEZ_MINIMA` é um REBIND por leitura de atributo no import (não um literal duplicado que coincide) — confirmado em runtime: `opcoes_motor.LIQUIDEZ_MINIMA, opcoes_lastreadas._LIQUIDEZ_MINIMA, ... is ...` imprime `40 40 True`; grep confirma que `_LIQUIDEZ_MINIMA = 40` (literal) não existe mais em `opcoes_lastreadas.py`. |
| 3 | Payoff de `avaliar()` (custo líquido, ganho/perda máximos, breakevens, delta somado) usa aritmética portada/testada de `calculos.py`; venda coberta aparece LIMITADA, collar travado dos DOIS lados, perna malformada recusada nomeando perna/campo, delta parcial declarado (ROADMAP SC3 / ENG-02) | ✓ VERIFIED | `server/app/opcoes_payoff.py` lido integralmente (276 linhas): `_validar_perna`, `custo_liquido`, `_resultado_no_vencimento`, `perfil_da_estrutura`, `_breakevens`, `_delta_total`. 28 testes em `test_opcoes_payoff.py` cobrem exatamente os casos do plano (call seca ilimitada, venda coberta limitada `ganho_maximo=3.5`, collar `ganho_ilimitado=False e perda_ilimitada=False`, perna booleana/negativa recusada com `ValueError` nomeando índice/campo, `delta_total.pernas_sem_delta>0` com `motivo` não-None). Todos os 28 passam. |
| 4 | Nenhuma chamada de rede sai do motor para o b-mcp; único canal para o hub mydata continua sendo `candle_provider`/`options_provider_mydata`/`mydata_budget`; leitura nova respeita o lock `mydata_budget.reservar()` (ROADMAP SC4 / ENG-03 / ENG-05) | ✓ VERIFIED | `grep` confirma zero import de `httpx/requests/urllib/socket/asyncio/mcp` nos 3 módulos novos — só comentários citando "b-mcp" para explicar a proibição. Guardião A (`test_opcoes_fronteira.py`) reprova import de rede + string b-mcp/URL via `ast`, parametrizado nos 3 módulos. Guardião B reprova `mcp` em qualquer módulo de `server/app/` e nos requirements.txt. Guardião C fixa allowlist de importadores de `mydata_client` em `{candle_provider, options_provider_mydata, mydata_budget}` via `ast.walk` sobre a árvore inteira. Guardião D (comportamento, monkeypatch) prova que `mydata_budget.reservar()=False` impede `get_vencimentos`/`get_options_chain` de serem chamados. Guardião E prova que `_debita()` referencia `reservar()`, nunca `debita()` direto (regressão WR-01). **Spot-check empírico realizado nesta verificação**: injetei `import httpx` em `opcoes_motor.py` — 2 dos 15 testes de `test_opcoes_fronteira.py` reprovaram imediatamente (`test_guardiao_a_...` e `test_eng04_limite_trocavel_opcoes_motor_imports_na_allowlist`); revertido via `git checkout --`, suíte voltou a 15/15 verde, `git status` limpo. O guardião funciona de verdade, não é decoração. |
| 5 | Gatilho que decide QUANDO avaliar vem do motor de setups já em produção do Boris (Radar/`setups.py`/`indicators.py`), nunca da DSL de setups do b-mcp (ROADMAP SC5 / ENG-06) | ✓ VERIFIED | `server/app/opcoes_gatilho.py` lido integralmente: `do_plano()` importa `DECISAO_VENDER/DECISAO_AGUARDAR/DECISAO_NAO_OPERAR` de `.setups` (nunca literal duplicado); mapeamento idêntico ao de `opcoes_lastreadas.propor()` (VENDER/lado baixa→proteção; AGUARDAR/NÃO OPERAR/lado neutro→prêmio; COMPRAR/alta/desconhecido→`sem_setup`). Guardião de paridade compara `do_plano()` contra `propor()` em produção para as 6 combinações. Guardião b-mcp (via `ast`) reprova import/string/arquivo `setups.json` do b-mcp nos 3 módulos de opções. |
| 6 | Contrato ADR-004 vira perna por adaptador nomeado; contrato sem prêmio publicado é recusado com motivo nomeado, nunca vira perna de prêmio 0 (15-03 must_haves) | ✓ VERIFIED | `perna_de_contrato`/`perna_de_acao` em `opcoes_motor.py` lidos: `lastPrice` None/0/negativo levanta `ValueError` citando `contractSymbol` e "sem prêmio publicado" — nenhum `float(x or 0)`. Runtime: `perna_de_contrato({...,'lastPrice':None},'venda')` levanta erro citando o símbolo (confirmado no código, comportamento coberto por 14 testes de adaptador em `test_opcoes_motor.py`). |
| 7 | Rastrear/avaliar não conhecem carteira, banco, sessão, texto de UI (15-03 must_haves) | ✓ VERIFIED | Único import de `opcoes_motor.py`: `.options_quant`, `.opcoes_payoff`, `typing`, `__future__` — confirmado por leitura e pelo guardião `test_eng04_limite_trocavel_opcoes_motor_imports_na_allowlist`. Nenhum `store`/`db`/`auth`/`skill_ref`/`main`/`candle_provider`/`mydata_client` referenciado. |
| 8 | Suíte nova passa de verdade agora, e nenhuma suíte pré-existente regrediu | ✓ VERIFIED | `cd server && .venv/bin/python -m pytest tests/test_opcoes_payoff.py tests/test_opcoes_gatilho.py tests/test_opcoes_motor.py tests/test_opcoes_fronteira.py -q` → **89 passed** (executado por este verificador, não copiado do SUMMARY). Suíte completa dentro do sandbox do Bash tool: 27 failed / 1878 passed — todas as 27 falhas confirmadas como `PermissionError: Operation not permitted` em `ssl.SSLContext.load_verify_locations` (spot-checado manualmente em `test_opcoes_lastreadas_rotas.py::test_vender_posicao_100_por_cento...`, que falha por causa de uma chamada Yahoo bloqueada pelo sandbox, não por código da Fase 15). Suíte completa com `dangerouslyDisableSandbox: true`: **1905 passed, 1 skipped, 0 failed** — confirma zero regressão real. |
| 9 | Nenhum arquivo de `web/` tocado; repo externo `~/dev/MCP` intocado; `requirements.txt`/`requirements-prod.txt` intocados (fase backend-only) | ✓ VERIFIED | `git show --name-only` de todos os 11 commits da fase (`1ee89ac`...`37a3da8`) confirma escopo exato: só `server/app/opcoes_*.py`, `server/tests/test_opcoes_*.py`, `docs/adr/024-*.md`. `git -C ~/dev/MCP status --porcelain` vazio. `git diff --stat server/requirements.txt server/requirements-prod.txt` vazio. |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `server/app/opcoes_payoff.py` | Aritmética pura de payoff N-pernas (ENG-02) | ✓ VERIFIED | 276 linhas, exporta `perfil_da_estrutura`, `resultado_no_vencimento`, `custo_liquido`, `TIPOS_PERNA`, `LADOS`. Zero import além de `typing`/`__future__`. |
| `server/tests/test_opcoes_payoff.py` | Guardião da aritmética | ✓ VERIFIED | 28 testes, todos passam. |
| `server/app/opcoes_gatilho.py` | Tradução plano→decisão de avaliar (ENG-06) | ✓ VERIFIED | 72 linhas, exporta `do_plano`, `VIES_PROTECAO`, `VIES_PREMIO`. |
| `server/tests/test_opcoes_gatilho.py` | Guardião de paridade + proibição b-mcp | ✓ VERIFIED | 16 testes, todos passam; usa `ast`, não grep. |
| `server/app/opcoes_motor.py` | Limite interno `rastrear`/`avaliar` + adaptadores (ENG-01, ENG-04) | ✓ VERIFIED | 197 linhas, exporta `rastrear`, `avaliar`, `perna_de_contrato`, `perna_de_acao`, `LIQUIDEZ_MINIMA`. |
| `server/tests/test_opcoes_motor.py` | Guardião da régua + contrato de `avaliar()` | ✓ VERIFIED | 30 testes, todos passam. |
| `server/tests/test_opcoes_fronteira.py` | Guardião ENG-03/ENG-04/ENG-05 | ✓ VERIFIED | 324 linhas, 15 testes, todos passam. Empiricamente comprovado reprovando/aprovando via injeção de falha nesta verificação. |
| `docs/adr/024-limite-interno-rastrear-avaliar.md` | ADR do limite trocável | ✓ VERIFIED | 181 linhas, 7 seções `## `, cita `find_tradable_options`, `evaluate_option_structure`, `mydata_budget`. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `opcoes_lastreadas.py` | `opcoes_motor.py` | import + rebind de `LIQUIDEZ_MINIMA` | ✓ WIRED | `_LIQUIDEZ_MINIMA = opcoes_motor.LIQUIDEZ_MINIMA`; diff mínimo confirmado por `git show`. |
| `opcoes_motor.py` | `opcoes_payoff.py` | `avaliar()` delega a `perfil_da_estrutura()` | ✓ WIRED | Linha 196: `return perfil_da_estrutura(pernas)`. |
| `opcoes_motor.py` | `options_quant.py` | `rastrear()` usa `liquidity_score()` | ✓ WIRED | Linha 22 import + linha 41 uso em `_candidato_valido`. |
| `opcoes_gatilho.py` | `setups.py` | constantes `DECISAO_*` importadas | ✓ WIRED | Linha 23: `from .setups import DECISAO_VENDER, DECISAO_AGUARDAR, DECISAO_NAO_OPERAR`. |
| `test_opcoes_fronteira.py` | `opcoes_motor.py` | análise `ast` dos imports | ✓ WIRED | Guardiões A/ENG-04 parseiam o arquivo real via `ast.parse`. |
| `test_opcoes_fronteira.py` | `mydata_budget.py` | monkeypatch de `reservar()` | ✓ WIRED | Guardião D exercita o caminho real via `asyncio.run(provider.get_options(...))`. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Suíte nova dos 4 módulos passa agora | `cd server && .venv/bin/python -m pytest tests/test_opcoes_payoff.py tests/test_opcoes_gatilho.py tests/test_opcoes_motor.py tests/test_opcoes_fronteira.py -q` | `89 passed` | ✓ PASS |
| Suíte completa sem regressão (fora do sandbox) | `.venv/bin/python -m pytest tests/ -q` com `dangerouslyDisableSandbox` | `1905 passed, 1 skipped` | ✓ PASS |
| `LIQUIDEZ_MINIMA` é fonte única real (não coincidência) | `python -c "from app import opcoes_motor, opcoes_lastreadas; print(..., ... is ...)"` | `40 40 True` | ✓ PASS |
| Guardião de fronteira reprova violação injetada | injeção temporária de `import httpx` em `opcoes_motor.py`, rodar `test_opcoes_fronteira.py`, reverter | 2/15 falharam com a injeção; 15/15 após reverter; `git status` limpo | ✓ PASS |
| Nenhuma string/import de rede/b-mcp nos módulos novos | `grep -niE 'b-mcp|bmcp|semente\.dev|httpx|mcp\b|requests|urllib|socket'` nos 3 módulos | só comentários explicativos | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ENG-01 | 15-03 | Seleção pelo critério já em produção (liquidez+strike) | ✓ SATISFIED | Truth #2 acima |
| ENG-02 | 15-01 | Payoff N-pernas portado de `calculos.py` | ✓ SATISFIED | Truth #3 acima |
| ENG-03 | 15-04 | Zero chamada de rede ao b-mcp em runtime | ✓ SATISFIED | Truth #4 acima |
| ENG-04 | 15-03, 15-04 | Limite interno `rastrear()`/`avaliar()` trocável | ✓ SATISFIED | Truths #1, #6, #7 acima |
| ENG-05 | 15-04 | Canal único com orçamento (`mydata_budget.reservar()`) | ✓ SATISFIED | Truth #4 acima |
| ENG-06 | 15-02 | Gatilho reusa o Radar, não a DSL do b-mcp | ✓ SATISFIED | Truth #5 acima |

Nota informativa (não bloqueante): a tabela de Traceability em `.planning/REQUIREMENTS.md` (linhas 103-108) ainda marca ENG-01..06 como "Pending", enquanto `ROADMAP.md` já registra a Fase 15 como "Complete" (linha 193) com os 4 planos marcados `[x]`. É um artefato de sincronização de documentação — a evidência de código/teste para cada ENG-0N é direta e independente dessa tabela; recomenda-se atualizar o status na próxima passagem de documentação, mas isso não bloqueia o resultado desta verificação.

### Anti-Patterns Found

Nenhum. Scan por `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER|coming soon|not yet implemented` nos 8 arquivos da fase não encontrou nenhum marcador de dívida real (únicos matches foram falsos-positivos de "todo"/"TODO" em PT-BR significando "all", ex. "todo chamador").

### Human Verification Required

Nenhum. Fase backend-only, sem UI, sem rota exposta, sem fluxo de usuário — todos os truths são verificáveis programaticamente e foram verificados.

### Gaps Summary

Nenhum gap. Todos os 9 truths (5 Success Criteria do ROADMAP + 4 must-haves adicionais dos planos) foram verificados diretamente no código, não a partir de prosa do SUMMARY: os 3 módulos novos e o arquivo de guardiões foram lidos integralmente linha a linha; a suíte de testes foi executada por este verificador (89/89 novos, 1905/1905 completa fora do sandbox); o guardião estrutural de fronteira foi empiricamente testado por injeção de falha real (import de `httpx`) e confirmado funcionando; a fonte única de `LIQUIDEZ_MINIMA` foi confirmada em runtime como rebind de atributo, não coincidência de literais; todos os 11 commits da fase foram conferidos por hash e escopo de arquivo.

---

*Verified: 2026-09-02T23:30:00Z*
*Verifier: Claude (gsd-verifier)*
