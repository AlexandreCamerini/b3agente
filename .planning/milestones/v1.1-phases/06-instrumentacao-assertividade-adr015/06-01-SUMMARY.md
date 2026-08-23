---
phase: 06-instrumentacao-assertividade-adr015
plan: 01
subsystem: api
tags: [analysis-outcomes, adr-015, instrumentacao, pytest]

# Dependency graph
requires: []
provides:
  - "analysis_outcomes.registrar() aceita e persiste entrada/alvo2/rr2/confluencia/entradaAMercado + metodologiaVersao"
  - "helper puro analysis_outcomes._metodologia(entry) com default 1 para registro antigo"
  - "N1 (main.py deep_call) alimenta os 5 campos a partir do plano determinístico já em escopo"
  - "N2 (main.py analyze_technical_model) alimenta só confluencia, com o motivo documentado no código"
  - "to_csv exporta as 6 colunas novas no fim, registro antigo com célula vazia"
affects: [06-02, 06-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "metodologiaVersao carimba CAMPOS gravados na escrita; ancora efetiva (Plano 02) é carimbada separadamente na resolução — os dois nunca se confundem"

key-files:
  created: []
  modified:
    - server/app/analysis_outcomes.py
    - server/app/main.py
    - server/tests/test_analysis_outcomes.py

key-decisions:
  - "N2 não recebe entrada/alvo2/rr2/entradaAMercado — seu stop/alvo vêm da proposal da LLM ancorada no preço, não do plano determinístico; enxertar geometria de um no outro seria a mesma classe de erro que o ADR-015 corrige"
  - "entrada_a_mercado usa startswith('a mercado') em vez de igualdade com a frase inteira — o prefixo é o contrato de setups.py, o resto é texto para humano"
  - "alvo=plano.get('alvo1') do N1 permanece inalterado — trocar a barreira de resolução para alvo2 seria uma segunda mudança de comportamento fora do escopo deste plano"

requirements-completed: [ADR15-01]

# Metrics
duration: 25min
completed: 2026-08-21
---

# Phase 6 Plan 1: Instrumentação — campos de outcome do plano determinístico Summary

**`analysis_outcomes.registrar` grava entrada/alvo2/rr2/confluencia/entradaAMercado do N1 (com metodologiaVersao=2), e só confluencia do N2 — puramente aditivo, sem migrar registro antigo.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3/3 completos
- **Files modified:** 3

## Accomplishments
- `registrar()` ganhou 5 kwargs novos (`entrada`, `alvo2`, `rr2`, `confluencia`, `entrada_a_mercado`), todos `Optional[None]`, sem tocar a guard clause existente.
- `METODOLOGIA_ATUAL = 2` carimbado em todo registro novo (N1 e N2), com comentário obrigatório distinguindo "campos gravados" de "âncora de resolução" (evita que o Plano 02 reintroduza a confusão que o ADR-015 corrige).
- `_metodologia(entry)` — helper puro de leitura com default 1, pronto para os Planos 02/03 consumirem sem reimplementar a regra.
- N1 (`main.py`, `deep_call`) alimenta os 5 campos reusando `plano`/`sres` já em escopo — sem recalcular `plano_do_resultado` nem refazer o snapshot.
- N2 (`main.py`, `analyze_technical_model`) alimenta só `confluencia` — decisão deliberada e documentada no código: seu stop/alvo vêm da `proposal` da LLM, não do plano determinístico.
- `to_csv` exporta as 6 colunas novas sempre no fim da tupla.
- Suíte canônica completa (`bash scripts/executar.sh --testes`) verde: 1115 testes pytest + 85 suítes web `.mjs`.

## Task Commits

Each task was committed atomically:

1. **Task 1: registrar() grava entrada/alvo2/rr2/confluencia/entradaAMercado + versão de metodologia** - `fbd5717` (feat)
2. **Task 2: N1 e N2 (main.py) alimentam os campos novos** - `ecd214d` (feat)
3. **Task 3: verificação canônica das duas suítes + registro da divergência do ROADMAP** - sem commit de código (task de verificação; ver esta seção do SUMMARY)

**Plan metadata:** commit deste SUMMARY (a seguir)

## Files Created/Modified
- `server/app/analysis_outcomes.py` — `METODOLOGIA_ATUAL`, `_metodologia()`, `registrar()` estendido, `to_csv()` com 6 colunas novas
- `server/app/main.py` — os dois call sites de `analysis_outcomes.registrar` (N1 completo, N2 só `confluencia`)
- `server/tests/test_analysis_outcomes.py` — 4 testes novos (campos completos N1, entrada a mercado, ausência de kwargs novos ainda carimba versão 2, helper `_metodologia`) + guardião `test_to_csv_colunas_fixas_e_escape` estendido

## Decisions Made
- N2 não recebe geometria do plano determinístico (ver `key-decisions` acima) — decisão do próprio ADR15-01/06-CONTEXT.md, não uma interpretação nova deste executor.
- `entrada_a_mercado` usa `startswith("a mercado")` sobre `plano["tipo"]`, não igualdade com a frase inteira — o prefixo é o contrato de `setups.py:602-612`.
- Ambiente do worktree não tinha `web/node_modules` instalado (achado conhecido do `PROJECT.md`) — rodei `npm install` em `web/` antes da suíte, como o próprio PROJECT.md recomenda para checkout novo.

## Deviations from Plan

None — plan executado exatamente como escrito. Os dois "achados" acima (posição do comentário de `METODOLOGIA_ATUAL` para satisfazer o critério de aceite `grep -A8`, e `npm install` em `web/`) são ajustes mecânicos dentro do escopo da própria Task 1/3, não desvios de comportamento.

## Issues Encountered
- Primeira versão do comentário de `METODOLOGIA_ATUAL` ficou ANTES da constante; o critério de aceite (`grep -A8 "METODOLOGIA_ATUAL = 2" ... | grep -ci "ancora"`) olha as linhas DEPOIS da declaração. Reposicionei o comentário para depois da linha `METODOLOGIA_ATUAL = 2` — mesmo conteúdo, mesma constante, só a ordem textual mudou.
- O comentário original do N1 citava literalmente `plano_do_resultado` em prosa (explicando que não recalculamos essa função), o que quebrava o critério de aceite "`grep -c plano_do_resultado` não aumentou em relação ao HEAD anterior" — reescrevi para "o plano do resultado" sem citar o nome da função.

## User Setup Required

None - nenhuma configuração de serviço externo necessária.

## Emenda pendente no ROADMAP — critério 1

O critério 1 da Phase 6 em `.planning/ROADMAP.md` hoje diz que `registrar` grava
`entrada`, `alvo2`, `rr2` e `confluencia` "(N1 e N2, `main.py`)". O que este
plano entrega é mais preciso: **N1 grava os quatro + `entradaAMercado`; N2
grava só `confluencia`.** Motivo verificado (não é lacuna, é decisão): o N2
não tem plano determinístico em escopo — seu `stop`/`alvo` vêm da proposta da
LLM ancorada no preço, e enxertar o `entrada` do plano determinístico ali
criaria geometria incoerente (gatilho de um plano com stop/alvo de outro),
exatamente a classe de erro que o ADR-015 existe para corrigir.

**Texto de substituição literal a aplicar** (Plano 03, Task 3 — duas plans da
mesma wave não escrevem no mesmo arquivo):

> 1. `analysis_outcomes.registrar` grava `entrada`, `alvo2`, `rr2`,
> `confluencia` e `entradaAMercado` no outcome do N1 (`main.py`), e
> `confluencia` no outcome do N2 — o N2 não tem plano determinístico em
> escopo e por isso não carrega geometria de gatilho. [ADR15-01]

## Verificação da suíte canônica

`bash scripts/executar.sh --testes` — exit code 0.
- Backend (pytest): **1115 passed**, 0 falhas, 225 warnings (nenhum relacionado a este plano — deprecations pré-existentes de `on_event`/`asyncio.get_event_loop_policy`).
- Web (`web/tests/*.mjs`): **85 suítes**, todas `[OK]`, nenhum `[X]`.
- Nenhum guardião removido: `test_to_csv_colunas_fixas_e_escape` foi ESTENDIDO (não apagado), com comentário explicando que as colunas novas entraram no fim por ADR15-01.

## Next Phase Readiness
- Campos `entrada`/`alvo2`/`rr2`/`confluencia`/`entradaAMercado`/`metodologiaVersao` disponíveis para o Plano 02 (ADR15-02: corrigir a âncora de `_avaliar_entry`) usar `entrada` como `preco0` em vez de `close`, respeitando retrocompatibilidade via `_metodologia()`.
- Nenhum registro de produção existente foi tocado — 100% aditivo, conforme exigido pelo ADR-015.
- Emenda do ROADMAP (acima) pronta para o Plano 03 aplicar.

---
*Phase: 06-instrumentacao-assertividade-adr015*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: server/app/analysis_outcomes.py
- FOUND: server/app/main.py
- FOUND: server/tests/test_analysis_outcomes.py
- FOUND: .planning/phases/06-instrumentacao-assertividade-adr015/06-01-SUMMARY.md
- FOUND commit: fbd5717 (Task 1)
- FOUND commit: ecd214d (Task 2)
