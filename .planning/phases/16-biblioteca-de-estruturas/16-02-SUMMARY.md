---
phase: 16-biblioteca-de-estruturas
plan: 02
subsystem: options-vocab
tags: [skill_ref, vocabulario, cvm-guardrail, collar, tdd]

# Dependency graph
requires:
  - phase: 14-opcoes-lastreadas
    provides: "OPCOES_LASTREADAS dict e opcoes_lastreadas_txt(modo, chave, **dados) — padrão de registro por modo (operador/educacional) e guardrail CVM de manchete única"
provides:
  - "Chave `collar` em OPCOES_LASTREADAS['operador'] e ['educacional'] (skill_ref.py)"
  - "Guardião estrutural (AST) que reprova qualquer arquivo fora de skill_ref.py compondo a manchete do collar, backend e front"
affects: [16-03-motor-collar, 17-fase-exibicao-estruturas]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guardião estrutural via `ast.walk` + exclusão de docstring por posição no corpo (Module/ClassDef/FunctionDef), mesmo padrão de test_opcoes_gatilho.py (guardião b-mcp)"
    - "Vocabulário sem valor monetário sinalizado quando o resultado da estrutura pode ser débito OU crédito — valor viaja em campos estruturados (caixa/estrutura/chips), não na frase interpolada por str.replace"

key-files:
  created: [server/tests/test_opcoes_collar_vocab.py]
  modified: [server/app/skill_ref.py]

key-decisions:
  - "Frase do collar não interpola valor em R$ — diferente de call_coberta/put_protecao, o resultado líquido do collar tem sinal (débito ou crédito) e a interpolação é str.replace sem condicional; uma frase única imprimiria valor negativo em metade dos casos. Custo líquido/breakeven/ganho-perda máximos ficam para os campos estruturados que o Plano 16-03 preenche."
  - "'Abate o custo' em vez de 'financiada pelo prêmio da call' — a segunda seria falsa quando o abatimento é só parcial, o que o CLAUDE.md proíbe (promessa não verificável)."

requirements-completed: [LIB-03]

# Metrics
duration: ~15min
completed: 2026-09-02
---

# Phase 16 Plan 02: Vocabulário canônico do collar Summary

**Adiciona a chave `collar` em `skill_ref.OPCOES_LASTREADAS` nos dois modos (operador/educacional) e um guardião AST que prova, por injeção de falha revertida, que a manchete do collar nasce só ali.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-09-02T21:14:07-03:00 (base do worktree corrigida)
- **Completed:** 2026-09-02T21:20:00-03:00
- **Tasks:** 2 (Task 1 com TDD explícito RED→GREEN; Task 2 = guardião, testes escritos junto com a Task 1 e provados por injeção nesta execução)
- **Files modified:** 2 (`server/app/skill_ref.py`, `server/tests/test_opcoes_collar_vocab.py`)

## Accomplishments
- `OPCOES_LASTREADAS["operador"]["collar"]` e `["educacional"]["collar"]` existem, com registro distinto por modo (mesa vs. condicional) e sem valor sinalizado interpolado.
- Guardião estrutural (`ast`) reprova qualquer arquivo backend (exceto `skill_ref.py`) ou front (`web/src/*.js`/`*.jsx`) que componha as strings-âncora "trava protetora"/"abate o custo".
- Prova empírica de que o guardião funciona: injeção temporária da string em `server/app/opcoes_lastreadas.py` fez o teste falhar nomeando o arquivo; revertida, suíte volta a verde.

## Texto final exato das duas frases

**Operador** (mesa, verbo de ordem, sem valor em R$):
```
Vender {n} call(s) de {ticker} strike {strikeCall} e comprar {n} put(s) strike {strikePut} sobre {qtyAcoes} ação(ões) — trava protetora: o prêmio da call abate o custo da put.
```

**Educacional** (condicional, descreve condição, nunca ordem):
```
Se você tivesse montado esta trava protetora agora, {qtyAcoes} ação(ões) ficariam protegidas contra queda abaixo de R$ {strikePut} e o ganho ficaria limitado a partir de R$ {strikeCall} — o prêmio da call vendida abate o custo da put comprada.
```

Interpolação de teste (`n="3", ticker="PETR4", strikeCall="32,00", strikePut="28,00", qtyAcoes="300"`):
- Operador: `"Vender 3 call(s) de PETR4 strike 32,00 e comprar 3 put(s) strike 28,00 sobre 300 ação(ões) — trava protetora: o prêmio da call abate o custo da put."`
- Educacional: `"Se você tivesse montado esta trava protetora agora, 300 ação(ões) ficariam protegidas contra queda abaixo de R$ 28,00 e o ganho ficaria limitado a partir de R$ 32,00 — o prêmio da call vendida abate o custo da put comprada."`

## Task Commits

Each task was committed atomically (Task 1 seguiu o gate TDD explícito RED→GREEN por ter `tdd="true"`; a implementação inicial foi feita fora de ordem e corrigida via reversão manual do trecho de código, sem perder o ciclo):

1. **Task 1 (RED): guardião do vocabulário do collar** - `4150f48` (test) — `server/tests/test_opcoes_collar_vocab.py` criado com 11 testes (Parte 1: comportamento do collar; Parte 2: guardião CVM); 6/11 falham como esperado (collar ainda não existe em `OPCOES_LASTREADAS`).
2. **Task 1 (GREEN): vocabulário da trava protetora nos dois modos** - `f2695ab` (feat) — `server/app/skill_ref.py` recebe a chave `collar` nos dois sub-dicionários; 35/35 testes verdes (`test_opcoes_collar_vocab.py` + `test_opcoes_lastreadas_proposta.py`).
3. **Task 2: guardião CVM** — implementado dentro do mesmo arquivo de teste da Task 1 (os testes de guardião fazem parte do commit RED acima, já que plano pedia guardião no mesmo arquivo). A prova de injeção-e-reversão exigida pelos critérios de aceite foi executada nesta sessão (ver seção abaixo) e não gerou commit adicional — a injeção foi temporária e revertida antes de qualquer commit.

**Plan metadata:** (este commit de SUMMARY, feito pelo orquestrador ao final da wave)

_Nota: como o guardião CVM (Task 2) já estava escrito junto com o arquivo de teste da Task 1 — plano definia as duas tasks no MESMO arquivo `test_opcoes_collar_vocab.py` — não houve um terceiro commit de código; a Task 2 se materializou como parte do commit RED (`4150f48`) e sua prova de funcionamento (critério de aceite) foi executada e documentada abaixo, sem deixar resíduo no working tree._

## Files Created/Modified
- `server/app/skill_ref.py` — adiciona `"collar"` em `OPCOES_LASTREADAS["operador"]` e `["educacional"]`, com comentário registrando a decisão de não sinalizar valor em R$ na frase.
- `server/tests/test_opcoes_collar_vocab.py` — 11 testes: comportamento do collar (Parte 1) + guardião estrutural CVM via `ast` (Parte 2).

## Decisions Made
- Frase do collar não carrega valor em reais — ver "Decisão registrada" no comentário do código e no frontmatter acima (`key-decisions`).
- Guardião reusa exatamente o padrão de `test_opcoes_gatilho.py` (`ast.walk`, exclusão de docstring por posição no corpo do Module/ClassDef/FunctionDef, para não reprovar comentário/docstring que documenta a proibição).

## Deviations from Plan

None de conteúdo — plano executado exatamente como escrito. Uma correção de PROCESSO ocorreu: implementei `skill_ref.py` antes de escrever o teste (violando a ordem RED→GREEN exigida pelo `tdd="true"` da Task 1). Corrigido nesta mesma sessão, antes de qualquer commit: revertida a implementação prematura via edição manual (não `git checkout`, para não disparar reversão de arquivo fora do escopo), escrito o teste, confirmado RED (6/11 falhas), commitado, reimplementado, confirmado GREEN (35/35), commitado. Nenhum commit espúrio ficou no histórico.

## Issues Encountered

**Prova de injeção do guardião (Task 2, critério de aceite obrigatório):**
- **Rodada 1 (falha esperada):** inserida a linha `_INJECAO_TEMPORARIA_PROVA_GUARDIAO = "trava protetora"` no fim de `server/app/opcoes_lastreadas.py` (string de código, não comentário/docstring). Rodando `pytest tests/test_opcoes_collar_vocab.py -q`: **1 failed, 10 passed** — `test_nenhum_modulo_backend_fora_do_skill_ref_compoe_manchete_do_collar` falhou nomeando o arquivo: `"opcoes_lastreadas.py: a manchete do collar vem SÓ de skill_ref.py (guardrail CVM) — string proibida 'trava protetora' encontrada: 'trava protetora'"`.
- **Reversão:** a linha injetada foi removida (edição manual, arquivo idêntico ao commitado — `git status --porcelain server/app/opcoes_lastreadas.py` vazio confirmado).
- **Rodada 2 (suíte verde de novo):** `pytest tests/test_opcoes_collar_vocab.py -q` → **11 passed**.

**Ambiente de teste — falha de rede não relacionada:** `tests/test_opcoes_lastreadas_rotas.py::test_vender_posicao_100_por_cento_travada_via_sell_devolve_400` falha sob o sandbox padrão do Bash (`get_quote(PETR4) via yahoo falhou: [Errno 1] Operation not permitted` — egress de rede bloqueado pelo sandbox). Confirmado que é puramente ambiental, não uma regressão desta plano: o mesmo comando com sandbox de rede liberado (`dangerouslyDisableSandbox`) passa (`1 passed`). Suíte completa de verificação do plano (`test_opcoes_collar_vocab.py` + `test_opcoes_lastreadas_proposta.py` + `test_opcoes_lastreadas_rotas.py`) rodada com rede liberada: **46 passed**.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plano 16-03 (motor do collar) já tem o vocabulário canônico pronto — não precisa reimprovisar texto; deve popular `caixa`/`estrutura`/`chips` com custo líquido/breakeven/ganho-perda máximos (a frase deliberadamente não carrega esses números).
- Guardião CVM cobre a manchete do collar da mesma forma que já cobre call_coberta/put_protecao — qualquer novo arquivo que tentar compor a frase "trava protetora"/"abate o custo" fora de `skill_ref.py` quebra o teste imediatamente.
- Sem bloqueios.

---
*Phase: 16-biblioteca-de-estruturas*
*Completed: 2026-09-02*
