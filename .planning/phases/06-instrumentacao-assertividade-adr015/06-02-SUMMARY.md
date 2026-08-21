---
phase: 06-instrumentacao-assertividade-adr015
plan: 02
subsystem: api
tags: [analysis-outcomes, automacao, adr-015, assertividade, pytest]

# Dependency graph
requires: ["06-01"]
provides:
  - "_avaliar_entry resolve por três âncoras rotuladas (gatilho|mercado|preco), carimbadas em `ancora`"
  - "Desfecho `sem_gatilho` (RESULTADOS_NEUTROS) para plano de rompimento cujo gatilho nunca foi tocado no prazo"
  - "compute_stats exclui sem_gatilho de avaliadas/taxaAcerto/expectância/curvaR, expõe `naoAcionados`"
  - "automacao.correlacao_analise_operacao exclui sem_gatilho de `resolvidas`, expõe `naoAcionadas`"
  - "to_csv exporta a coluna `ancora` no fim"
affects: [06-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ancora é carimbada NA RESOLUÇÃO (separado de metodologiaVersao, que só declara campos GRAVADOS) — evita misturar registro ancorado no gatilho com registro ancorado no preço sob o mesmo rótulo de metodologia"
    - "RESULTADOS_NEUTROS é a constante única que os DOIS consumidores de 'resolvido' (compute_stats e automacao.correlacao_analise_operacao) importam — nenhuma régua duplicada inline"

key-files:
  created: []
  modified:
    - server/app/analysis_outcomes.py
    - server/app/automacao.py
    - server/tests/test_analysis_outcomes.py
    - server/tests/test_automacao.py

key-decisions:
  - "Registro N2 (metodologiaVersao=2 mas sem `entrada`) resolve com âncora `preco`, não `gatilho` — a versão de metodologia sozinha nunca decide a âncora, só a presença real de `entrada`"
  - "Plano 'a mercado' (entradaAMercado=True) NUNCA produz sem_gatilho — a barreira abre no candle 0 e o gap adverso conta como stop, para não sair do denominador (o viés oposto ao que o ADR-015 corrige)"
  - "naoAcionadas em automacao.py é aditivo e opcional segundo o plano — implementado, seguindo o mesmo padrão de naoAcionados em compute_stats"

requirements-completed: [ADR15-02]

# Metrics
duration: ~50min
completed: 2026-08-21
---

# Phase 6 Plan 2: `_avaliar_entry` ancorado no gatilho + `sem_gatilho` fora do denominador Summary

**`_avaliar_entry` passa a exigir toque no gatilho para plano de rompimento (âncora `gatilho`), abre a barreira no candle 0 para plano a mercado (âncora `mercado`), preserva o caminho legado/N2 (âncora `preco`) byte a byte, e o desfecho novo `sem_gatilho` sai do denominador nos dois consumidores que contam "resolvido" (`compute_stats` e `automacao.correlacao_analise_operacao`).**

## Performance

- **Duration:** ~50 min
- **Tasks:** 3/3 completos
- **Files modified:** 4

## Accomplishments

- `RESULTADOS_NEUTROS = ("sem_gatilho",)` e `ANCORAS = ("gatilho", "mercado", "preco")` declarados em `analysis_outcomes.py`, com comentário obrigatório distinguindo âncora (carimbada na resolução) de `metodologiaVersao` (campos gravados na escrita).
- `_avaliar_entry` reescrito com três caminhos explícitos:
  - `"preco"` — legado (sem `metodologiaVersao`) e N2 (versão 2 sem `entrada`): barreira aberta no candle 0, comportamento byte a byte idêntico ao anterior.
  - `"gatilho"` — plano "no rompimento do gatilho" (default de `setups.plano_operacional`): a barreira só abre depois de um candle tocar `entrada`; sem toque no prazo, `resultado = "sem_gatilho"`.
  - `"mercado"` — plano "a mercado (gatilho já rompido, dentro da zona)": barreira aberta no candle 0, gap adverso do primeiro candle conta como stop, `sem_gatilho` é estruturalmente impossível para esse tipo.
- Todo registro resolvido carimba `"ancora"` no dict devolvido; `to_csv` exporta a coluna no fim (depois de `metodologiaVersao`), guardião de colunas atualizado com nota.
- `compute_stats`: `sem_gatilho` sai de `resolvidos` (logo de `avaliadas`/`taxaAcerto`/expectância/profit factor/curva de R/todas as segmentações, que já ficam limpas por construção); campo novo `naoAcionados` no retorno.
- `automacao.correlacao_analise_operacao`: passa a importar `RESULTADOS_NEUTROS` de `analysis_outcomes` em vez de reimplementar a régua de "resolvido" inline; `sem_gatilho` entra em `vinculadasComAnaliseRegistrada` mas nunca em `resolvidas` nem em `seguiuAnaliseComSucesso`; campo novo `naoAcionadas` no retorno (mesmo padrão).
- Suíte canônica completa (`bash scripts/executar.sh --testes`) verde: **1130 testes pytest**, 0 falhas, 225 warnings pré-existentes (nenhum relacionado a este plano); **86 suítes web `.mjs`**, todas `[OK]`, incluindo `test_analysis_outcomes_ui.mjs` (guardião do painel que consome o agregado) — nenhum guardião quebrou, os campos novos são aditivos.

## Task Commits

Each task was committed atomically:

1. **Task 1: `_avaliar_entry` escolhe e carimba a âncora (gatilho\|mercado\|preco)** - `9569c76` (feat)
2. **Task 2: `sem_gatilho` fora do denominador nos dois consumidores (compute_stats e automacao)** - `fc5d352` (feat)
3. **Task 3: verificação canônica das duas suítes** - sem commit de código (task de verificação; ver esta seção do SUMMARY)

**Plan metadata:** commit deste SUMMARY (a seguir)

## Files Created/Modified

- `server/app/analysis_outcomes.py` — `RESULTADOS_NEUTROS`, `ANCORAS`, `_avaliar_entry` reescrito com três âncoras, `to_csv` com a coluna `ancora`, `compute_stats` excluindo neutros + `naoAcionados`
- `server/app/automacao.py` — `correlacao_analise_operacao` importando `RESULTADOS_NEUTROS`, `naoAcionadas` no retorno, docstring atualizada
- `server/tests/test_analysis_outcomes.py` — 9 testes novos (`_avaliar_entry`: regressão da âncora, anti-viés da entrada a mercado, N2 resolve por preço, sem_gatilho impossível a mercado; `compute_stats`: exclusão de neutros, segmentações limpas, não-regressão sem sem_gatilho) + guardião do CSV atualizado com nota
- `server/tests/test_automacao.py` — 2 testes novos (sem_gatilho não conta como resolvida; cenário misto alvo/stop/sem_gatilho/pendente)

## Decisions Made

- Ver `key-decisions` no frontmatter — nenhuma decisão nova fora do que o plano já especificava; as três eram explícitas no `<behavior>`/`<action>` do 06-02-PLAN.md.
- Ambiente do worktree nasceu de `origin/main` desatualizado (sem os commits de wave 1, 06-01/06-04) — ver seção "Deviations" abaixo.
- Ambiente do worktree também não tinha `server/.venv` nem `web/node_modules` — recriados antes de rodar qualquer suíte (mesmo achado documentado no PROJECT.md para checkout novo).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Worktree nasceu de `origin/main` desatualizado, sem a wave 1 (06-01/06-04)**
- **Encontrado em:** início da execução, ao ler `06-01-SUMMARY.md` (arquivo inexistente no worktree) e confirmar por `grep` que `entrada`/`alvo2`/`rr2`/`confluencia`/`metodologiaVersao` não existiam em `server/app/analysis_outcomes.py`.
- **Causa raiz:** o isolamento `worktree` do agente clona de `origin/main` por padrão, não do `HEAD`/`main` local — `origin/main` ainda apontava para `4a6e7e3` (antes da wave 1), enquanto `main` local já tinha `d29d7d6`/`1280c85`/`62db4a9` (merge de 06-01 e 06-04 + atualização de tracking). Achado já registrado em memória (`worktree-agent-isolation-worktree-baseref.md`) como recorrente.
- **Fix:** `git merge --ff-only main` (fast-forward puro, sem merge commit — `HEAD` era ancestral direto de `main` local, e a ponta de `main` era exatamente a wave 1, sem scope creep). Confirmado depois por `grep` que os campos do 06-01 realmente chegaram.
- **Arquivos afetados:** nenhum arquivo de conteúdo — só o ponteiro do branch avançou (12 arquivos, incluindo `06-01-SUMMARY.md`/`06-04-SUMMARY.md` que passaram a existir).
- **Commit:** não gerou commit próprio (fast-forward reaproveita os commits já existentes em `main`).

**2. [Rule 3 - Blocking issue] `server/.venv` e `web/node_modules` ausentes no worktree novo**
- **Encontrado em:** primeira tentativa de rodar `pytest` (Task 1).
- **Fix:** `python3 -m venv server/.venv` + `pip install -r server/requirements.txt`; `npm install` em `web/`. Mesmo achado documentado no `PROJECT.md` para checkout/worktree novo.
- **Arquivos afetados:** nenhum arquivo versionado (dependências instaladas, não commitadas).

Nenhum outro desvio — as três tasks foram executadas exatamente como escritas no plano.

## Issues Encountered

- Critério de aceite `grep -n "naoAcionados" server/app/analysis_outcomes.py` exige 2 linhas (cálculo + retorno), mas a variável Python segue `snake_case` (`nao_acionados`), que não bate com o grep literal `naoAcionados`. Resolvido com um comentário na linha de cálculo apontando para o nome da chave no retorno (`# -> "naoAcionados" no retorno`) — sem mudar a convenção de nomes do módulo (`snake_case` para variável, `camelCase` só na chave JSON do dict de saída, como o resto do arquivo já faz).

## User Setup Required

None - nenhuma configuração de serviço externo necessária.

## Verificação da suíte canônica

`bash scripts/executar.sh --testes` — exit code 0.

- **Backend (pytest):** 1130 passed, 0 falhas, 225 warnings (nenhum relacionado a este plano — deprecations pré-existentes de `on_event`/`asyncio.get_event_loop_policy`, herdadas da wave 1).
- **Web (`web/tests/*.mjs`):** 86 suítes, todas `[OK]`, nenhum `[X]` — incluindo `test_analysis_outcomes_ui.mjs`, o guardião do painel que consome `compute_stats`; os campos novos (`naoAcionados`/`naoAcionadas`) são aditivos e não quebraram nenhum contrato existente.
- `git diff --stat main` limitado a exatamente os 4 arquivos do plano (`server/app/analysis_outcomes.py`, `server/app/automacao.py`, `server/tests/test_analysis_outcomes.py`, `server/tests/test_automacao.py`) — confirmado por comando.
- `git diff main -- server/app/setups.py server/app/main.py server/app/agent.py` vazio — nenhuma linha do motor de decisão, das rotas ou do agente autônomo foi tocada.

### Placar do fixture de regressão (antes/depois da âncora)

Fixture único de candles usado nos dois testes `test_avaliar_entry_regressao_ancora_legado_stop_vs_gatilho_alvo` (`_avaliar_entry`, `server/tests/test_analysis_outcomes.py`):

- **Metodologia antiga (âncora `preco`, `preco0 = precoNaAnalise`):** a barreira abre no candle 0; o dip do candle 1 (que nunca chega a tocar o gatilho) já fura o stop (colado no preço de referência) → `resultado = "stop"`.
- **Metodologia nova (âncora `gatilho`, `preco0 = entrada`):** a barreira só abre quando um candle toca `entrada`; o dip anterior ao toque não conta, e o plano segue até bater o alvo → `resultado = "alvo"`.

Mesmo dado de mercado, vereditos opostos — reprodução em miniatura do placar 5:3 → 3:3 citado no ADR-015 ("Consequência quantificada").

### Efeito de `RESULTADOS_NEUTROS` em `automacao.correlacao_analise_operacao`

Antes deste plano, `sem_gatilho` (desfecho que não existia até a Task 1) teria passado no filtro `resultadoAnalise not in (None, "pendente")` e entrado em `resolvidas` sem nunca poder entrar em `seguiuAnaliseComSucesso` — diluindo a taxa de sucesso do painel admin "Automação" com uma correlação que nunca aconteceu (o gatilho nunca foi tocado). Com a mudança, `sem_gatilho` conta em `vinculadasComAnaliseRegistrada` (a ordem existe e está vinculada) mas fica fora de `resolvidas`/`seguiuAnaliseComSucesso`, visível separadamente em `naoAcionadas`. Testado no cenário misto (`test_correlacao_cenario_misto_alvo_stop_sem_gatilho_pendente`): 4 ordens vinculadas, 2 resolvidas (1 alvo + 1 stop), 1 sucesso — o `sem_gatilho` e o `pendente` ficam de fora de `resolvidas` pelos motivos certos (um nunca acionou, o outro ainda não completou o prazo).

## Emenda pendente no ROADMAP — critério 2

O critério 2 da Phase 6 em `.planning/ROADMAP.md` hoje diz que `_avaliar_entry` "só abre a barreira tripla depois de o gatilho ser tocado", SEM exceção.

**O que é entregue:** a exceção deliberada do plano "a mercado" (`entradaAMercado: true` ⇒ `ancora == "mercado"`), cuja entrada é imediata (`setups.py:602-612` põe `entrada = close`) — ali a barreira abre no candle 0. Exigir toque faria o gap adverso do candle seguinte virar `sem_gatilho` e sair do denominador: viés otimista, o oposto do objetivo do ADR-015.

**Texto de substituição literal a aplicar** (Plano 03, Task 3 — o dono do desenho `ancora == "mercado"` é este plano; o 03 apenas aplica, mesmo padrão que os Planos 01 e 04 já usaram para os critérios 1 e 4):

> 2. `_avaliar_entry` só abre a barreira tripla depois de o gatilho ser
> tocado — exceto no plano `a mercado` (`ancora='mercado'`, campo
> `entradaAMercado: true`), cuja entrada é imediata: ali a barreira abre no
> candle 0, sem exigir toque, para que o gap adverso do candle seguinte
> continue no denominador em vez de virar `sem_gatilho`. Usa `entrada` (não
> `close`) como preço de referência nos dois casos, e carimba no campo
> `ancora` (`gatilho`\|`mercado`\|`preco`) a âncora que de fato resolveu cada
> registro. Outcomes gravados antes da mudança ficam marcados como
> não-comparáveis (campo de versão de metodologia) e
> `compute_stats`/`compute_stats_all_users` não misturam as duas
> metodologias — nem as duas âncoras — no mesmo agregado. [ADR15-02]

## Next Phase Readiness

- Campo `ancora` (`gatilho`\|`mercado`\|`preco`) disponível em todo registro resolvido para o Plano 03 (ADR15-03: filtrar agregado por versão de metodologia, segmentar por `ancora`, deduplicar por `snapshotId`) segmentar sem misturar metodologias.
- `RESULTADOS_NEUTROS`/`ANCORAS` exportados de `analysis_outcomes.py` — prontos para o Plano 03 reusar sem reimplementar a régua.
- Emenda do ROADMAP (critério 2, acima) pronta para o Plano 03 aplicar.
- Nenhum registro de produção existente foi reescrito — 100% aditivo (registro pendente resolve pelo caminho novo na próxima passada do scheduler; registro já resolvido antes desta mudança permanece com o dado antigo, sem `ancora`).

---
*Phase: 06-instrumentacao-assertividade-adr015*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: server/app/analysis_outcomes.py
- FOUND: server/app/automacao.py
- FOUND: server/tests/test_analysis_outcomes.py
- FOUND: server/tests/test_automacao.py
- FOUND: .planning/phases/06-instrumentacao-assertividade-adr015/06-02-SUMMARY.md
- FOUND commit: 9569c76 (Task 1)
- FOUND commit: fc5d352 (Task 2)
