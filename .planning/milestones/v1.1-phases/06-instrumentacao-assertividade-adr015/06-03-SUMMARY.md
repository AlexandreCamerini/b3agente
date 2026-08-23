---
phase: 06-instrumentacao-assertividade-adr015
plan: 03
subsystem: api
tags: [analysis-outcomes, adr-015, adr15-03, instrumentacao, pytest, roadmap]

# Dependency graph
requires:
  - phase: 06-instrumentacao-assertividade-adr015 (06-01)
    provides: "entrada/alvo2/rr2/confluencia/entradaAMercado + metodologiaVersao gravados por registrar()"
  - phase: 06-instrumentacao-assertividade-adr015 (06-02)
    provides: "campo `ancora` (gatilho|mercado|preco) carimbado na resolução; RESULTADOS_NEUTROS/ANCORAS"
provides:
  - "compute_stats(outcomes, modo, tipo, metodologia=METODOLOGIA_ATUAL) — filtra por versão de metodologia, expõe totalComparaveis/metodologiaLegado/porAncora"
  - "_dedup_por_snapshot(outcomes, modo=None) — dedup modo-independente no N1, modo-dependente no N2"
  - "compute_stats_all_users dedupica ANTES de agregar; outcomes_de_todos_os_usuarios permanece crua"
  - "Critérios 1/2/4 do ROADMAP e entrada ADR15-01 do REQUIREMENTS emendados com a razão verificada pelos Planos 01/02/04"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "escape hatch explícito (metodologia=None) para desligar o filtro de metodologia em teste/diagnóstico, sem afetar o default de produção"
    - "dedup vive só na camada de agregação cross-escopo (compute_stats_all_users), nunca na lista crua que automacao.py consome"

key-files:
  created: []
  modified:
    - server/app/analysis_outcomes.py
    - server/tests/test_analysis_outcomes.py
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "pendentes continua contado sobre o recorte PRÉ-filtro de metodologia (não totalComparaveis) — pendente legado não some do KPI 'AGUARDANDO PRAZO' nos dois fronts, princípios 4/9 do CLAUDE.md"
  - "totalAnalises preserva a semântica de hoje (pré-filtro) pelo mesmo motivo — os dois fronts fecham o painel inteiro quando é 0"
  - "fixtures pré-existentes de compute_stats (_outcome/_outcome_conf/_outcome_regime) ganharam metodologiaVersao=2 — sinal de que o default está correto, não de que o filtro deveria afrouxar (regra explícita do plano)"
  - "web/node_modules do worktree estava incompleto (faltava @capacitor/*) — npm install rodado antes da suíte canônica, mesmo achado documentado em PROJECT.md"

requirements-completed: [ADR15-02, ADR15-03]

# Metrics
duration: ~40min
completed: 2026-08-21
---

# Phase 6 Plan 3: Fecha a fase — compute_stats não mistura metodologia/âncora, dedup por snapshotId, ROADMAP emendado Summary

**`compute_stats` passa a filtrar por metodologia (default = atual), declara o legado excluído e segmenta resolvidos por âncora; `compute_stats_all_users` deduplica por `snapshotId` (modo-independente no N1, modo-dependente no N2) antes de agregar; os critérios 1/2/4 do ROADMAP e a entrada ADR15-01 do REQUIREMENTS foram emendados com o texto literal que os Planos 01/02/04 deixaram prontos.**

## Performance

- **Duration:** ~40 min
- **Tasks:** 3/3 completos
- **Files modified:** 4

## Accomplishments

- `compute_stats(outcomes, modo, tipo, metodologia=METODOLOGIA_ATUAL)`: default agrega só a metodologia atual (2); `metodologia=None` desliga o filtro (escape hatch de teste/diagnóstico); `metodologia=1` agrega só o legado.
- `totalAnalises` preserva a semântica pré-filtro de hoje; `totalComparaveis` expõe o universo pós-filtro; `pendentes` continua contando o recorte INTEIRO pré-filtro (pendente legado não some do KPI "AGUARDANDO PRAZO").
- `metodologiaLegado = {total, avaliadas}` sempre declarado, nunca somado ao agregado comparável.
- `porAncora` segmenta resolvidos por âncora (`gatilho`\|`mercado`\|`preco`\|`"—"`), respeitando `MIN_N` — evita que N1 (gatilho) e N2 (preço) se misturem sob o mesmo rótulo `metodologia: 2`.
- `_dedup_por_snapshot(outcomes, modo=None)`: colapsa registros do mesmo plano determinístico gravado várias vezes sob o mesmo `snapshotId` — chave modo-independente no N1 (`setups.plano_do_resultado` não recebe `modo`), modo-dependente no N2 (prompt difere por modo). Sobrevivente determinístico (resolvido > pendente, depois `criadoEm` mais antigo, empate por `id`).
- `compute_stats_all_users` deduplica ANTES de agregar; `outcomes_de_todos_os_usuarios` permanece crua (contrato de `automacao.py` preservado, `automacao.py` intocado).
- Critérios 1, 2 e 4 do ROADMAP emendados com o texto literal dos SUMMARYs 01/02/04; entrada `ADR15-01` do REQUIREMENTS emendada com o mesmo texto do critério 1.
- Suíte canônica completa (`bash scripts/executar.sh --testes`) verde: **1145 testes pytest**, 0 falhas, 225 warnings pré-existentes (nenhum relacionado a este plano); **86 suítes web `.mjs`**, todas `[OK]`.

## Task Commits

Cada task foi commitada em RED→GREEN (TDD) nas tasks 1/2; task 3 é verificação + docs:

1. **Task 1: compute_stats não mistura metodologias nem âncoras, e declara o que excluiu**
   - `81e5211` test(06-03): guardião RED — compute_stats não mistura metodologia/âncora, dedup por snapshotId (RED — cobre também os testes de dedup da Task 2, escritos juntos)
   - `b757dc3` feat(06-03): compute_stats filtra metodologia + declara legado + porAncora (GREEN)
2. **Task 2: compute_stats_all_users deduplica por snapshotId antes de agregar**
   - `6bbdff7` feat(06-03): compute_stats_all_users deduplica por snapshotId antes de agregar (GREEN)
3. **Task 3: verificação canônica + emenda dos critérios do ROADMAP/REQUIREMENTS + registro do impacto no KPI**
   - `3c58fd9` docs(06-03): emenda critérios 1/2/4 do ROADMAP + entrada ADR15-01 do REQUIREMENTS

**Plan metadata:** commit deste SUMMARY (a seguir)

## Files Created/Modified

- `server/app/analysis_outcomes.py` — `compute_stats` com parâmetro `metodologia`, `totalComparaveis`, `metodologiaLegado`, `porAncora`; `_dedup_por_snapshot` nova; `compute_stats_all_users` deduplica antes de agregar, docstring com a assimetria usuário×admin
- `server/tests/test_analysis_outcomes.py` — 14 testes novos (filtro de metodologia default/None/1, pendente legado não some, `porAncora`, 6 casos de `_dedup_por_snapshot`, `compute_stats_all_users` com dedup real via `registrar()` 12x) + 3 fixtures pré-existentes (`_outcome`/`_outcome_conf`/`_outcome_regime`) ganharam `metodologiaVersao: 2` com comentário
- `.planning/ROADMAP.md` — critérios 1, 2 e 4 da Phase 6 substituídos pelo texto literal dos SUMMARYs 01/02/04 (critérios 3 e 5, Goal e lista de planos intocados)
- `.planning/REQUIREMENTS.md` — entrada `ADR15-01` da seção "Assertividade da instrumentação (ADR-015)" substituída pelo mesmo texto do critério 1 (checkbox `[x]` preservado — já estava marcado desde o Plano 01; nenhum outro requirement nem a tabela de rastreio tocados)

## Decisions Made

Ver `key-decisions` no frontmatter. Nenhuma decisão nova fora do que o `<behavior>`/`<action>` do 06-03-PLAN.md já especificava — as regras de `totalAnalises`/`pendentes` pré-filtro e o texto das 3 emendas vieram prontos dos Planos 01/02/03(este)/04.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] `web/node_modules` incompleto no worktree (faltava `@capacitor/*`)**
- **Encontrado em:** Task 3, primeira rodada de `bash scripts/executar.sh --testes` (7 suítes web falharam com `ERR_MODULE_NOT_FOUND: @capacitor/core`).
- **Causa raiz:** mesmo achado já documentado em `PROJECT.md` ("rodar num worktree/checkout novo sem `web/node_modules` instalado faz 7 testes web falharem por ambiente, não por regressão").
- **Fix:** `npm install` em `web/` (439 pacotes instalados). Segunda rodada da suíte: 0 falhas.
- **Arquivos afetados:** nenhum arquivo versionado (dependências instaladas, não commitadas; `web/node_modules` já está no `.gitignore`).

**2. [Rule 3 - Blocking issue] `server/.venv` ausente no worktree**
- **Encontrado em:** início da Task 1, ao tentar rodar `pytest` com o comando exato do plano (`./.venv/bin/python`).
- **Fix:** `ln -s <repo-principal>/server/.venv server/.venv` — symlink em vez de recriar o venv (mesmo Python/deps do repo principal, mais rápido que reinstalar; os comandos `<automated>`/`<acceptance_criteria>` do plano usam literalmente `./.venv/bin/python`, então precisam do caminho existir). O symlink está fora do controle de versão (`server/.venv/` no `.gitignore`; `git status` mostra `??` porque o padrão do `.gitignore` tem barra final e não casa com o symlink em si — verificado, não afeta nenhum commit feito, todos os `git add` foram por arquivo explícito).
- **Arquivos afetados:** nenhum arquivo versionado.

Nenhum outro desvio — as três tasks foram executadas como escritas no plano.

---

**Total deviations:** 2 auto-fixed (ambos Rule 3 — setup de ambiente do worktree, mesma classe já documentada nos Planos 02/04/05)
**Impact on plan:** Nenhum. Nenhuma mudança de comportamento; setup necessário para rodar a suíte canônica exigida pela própria Task 3.

## Issues Encountered

- RED da Task 1 e da Task 2 foi escrito num único commit (`81e5211`) em vez de dois RED separados — os testes de `compute_stats` (Task 1) e de `_dedup_por_snapshot`/`compute_stats_all_users` (Task 2) foram redigidos juntos por eficiência de leitura do `<behavior>` combinado das duas tasks. O GREEN de cada task foi commitado separadamente (`b757dc3` para compute_stats, `6bbdff7` para dedup), preservando o rastreamento por task pedido pelo protocolo de execução. Não afeta nenhum critério de aceite (todos são sobre o estado final do código, não sobre a granularidade dos commits de teste).

## User Setup Required

None - nenhuma configuração de serviço externo necessária.

## Impacto esperado no painel "Eficiência da IA" (nota de release, ADR-015 "Consequências se aprovado")

- **`totalAnalises` NÃO muda** — continua o total do recorte modo/tipo, PRÉ-filtro de metodologia. O empty-state dos dois fronts (`web/src/App.jsx:4832`, `web-admin/src/App.jsx:361`) continua correto: nenhum usuário com análises verá "Nenhuma análise com plano de stop/alvo definido ainda…" por causa desta mudança.
- **`pendentes` também NÃO muda de universo** — segue contando o recorte inteiro (pré-filtro de metodologia). O KPI "AGUARDANDO PRAZO" (`web/src/App.jsx:4851`, `web-admin/src/App.jsx:368`) continua mostrando os pendentes legados, em vez de zerar no dia do deploy.
- **`totalComparaveis`/`avaliadas` CAEM logo após o deploy** — porque (a) o histórico é quase todo metodologia 1 (0 de 159 resolvidos em produção tinham `entrada` antes do Plano 01) e (b) as duplicatas por `snapshotId` deixam de contar no agregado admin. Isso é a **recalibração do KPI que o ADR-015 pediu, não uma regressão**: o número antigo (`+2,56R`, n=44) media um trade fantasma inflado por duplicação; o número novo, menor e com `n` menor no início, mede o trade que o motor de fato propõe. `metodologia`, `metodologiaLegado` e `totalComparaveis` no próprio payload declaram o recorte, para que o número não pareça "piorar" sem explicação no painel.
- **Assimetria usuário × admin (documentada no docstring de `compute_stats_all_users`)** — o dedup por `snapshotId` vive SÓ na camada de agregação cross-escopo (admin). O painel do próprio usuário (`main.py:2419` → `compute_stats` com os outcomes crus do escopo) continua contando duplicatas. Um usuário com um plano regravado 12x verá um `n` maior no painel dele do que o agregado deduplicado do admin sobre os mesmos dados — intencional (`compute_stats` puro não pode assumir escopo único), mas é o tipo de divergência que vira chamado de suporte se não estiver documentada — por isso entra nesta nota de release.

## Next Phase Readiness

- Fase 6 (Instrumentação de Assertividade, ADR-015) fechada: 5 requirements (ADR15-01..05) completos, 5 plans executados, ROADMAP/REQUIREMENTS emendados com a razão verificada de cada divergência entre o que foi planejado e o que foi entregue.
- Nenhum bloqueio conhecido para o próximo milestone/fase.
- STATE.md e o restante do tracking pós-wave ficam para o orquestrador, após o merge deste worktree (fora do escopo explícito da Task 3 deste plano).

---
*Phase: 06-instrumentacao-assertividade-adr015*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: server/app/analysis_outcomes.py
- FOUND: server/tests/test_analysis_outcomes.py
- FOUND: .planning/ROADMAP.md
- FOUND: .planning/REQUIREMENTS.md
- FOUND: .planning/phases/06-instrumentacao-assertividade-adr015/06-03-SUMMARY.md
- FOUND commit: 81e5211 (Task 1/2 RED)
- FOUND commit: b757dc3 (Task 1 GREEN)
- FOUND commit: 6bbdff7 (Task 2 GREEN)
- FOUND commit: 3c58fd9 (Task 3, docs)
