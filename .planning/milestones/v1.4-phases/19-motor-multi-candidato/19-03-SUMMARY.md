---
phase: 19-motor-multi-candidato
plan: 03
subsystem: web
tags: [react, jsx, opcoes, static-guardians, motor-deterministico]

# Dependency graph
requires:
  - phase: 19-motor-multi-candidato
    plan: 02
    provides: "GET /api/options/proposta/{ticker} expõe candidatos (lista de 0/1/2), proposta==candidatos[0]"
provides:
  - "Componente CandidatoOpcao (web/src/App.jsx) — item de um candidato dentro da linha de N, reusa o padrão visual de OportunidadesOpcoes/PropostaLastreada"
  - "PropostaDaPosicao ramifica em N-candidatos (candidatos.length > 1) vs. candidato único (comportamento de hoje, sem regressão)"
  - "Handler de aceite único e parametrizado (aceitarCandidato(p)), busy compartilhado por posição desabilita todos os CTAs irmãos"
affects: [19-04-motor-multi-candidato]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sub-componente de item dentro de linha horizontal scrollável (reuso verbatim do padrão OportunidadesOpcoes, Fase 18) — nenhum terceiro padrão visual introduzido"
    - "Handler de aceite parametrizado pelo dado clicado em vez de fechar sobre estado único (aceitarCandidato(p) em vez de onAbrirLastreada() fechando sobre r.proposta)"

key-files:
  created:
    - web/tests/test_opcoes_multi_candidato_ui.mjs
  modified:
    - web/src/App.jsx
    - web/tests/test_opcoes_collar_ui.mjs

key-decisions:
  - "Busy único por posição, nunca por candidato — cai de graça da estrutura existente (useState(false) já compartilhado), qualquer CTA de candidato desabilita todos os irmãos ao clicar, sem estado novo (19-UI-SPEC.md Decisão de Interação 1)"
  - "Nenhum refetch após aceite — o candidato irmão obsoleto permanece visualmente normal; se tocado, o servidor (Plano 19-02, ORDER_LOCK) rejeita e o flash existente absorve o erro, sem mensagem inline nova"
  - "Guardião pré-existente (test_opcoes_collar_ui.mjs, contagem de handlers) atualizado com nota citando Fase 19, nunca apagado — a regra protegida (confirmar antes de travar lastro) não mudou, só o nome/assinatura do handler do detalhe de posição"

patterns-established: []

requirements-completed: [MULTI-02]

# Metrics
duration: ~1h10 (leitura completa de contexto/UI-SPEC/PATTERNS + implementação + correção de base de worktree)
completed: 2026-09-04
---

# Phase 19 Plan 03: Motor multi-candidato (N candidatos lado a lado em Posições) Summary

**O detalhe da posição em Posições passa a mostrar os N candidatos de estrutura de opções lado a lado, cada um com manchete, payoff e CTA próprios — via novo componente `CandidatoOpcao`, reusando 100% do padrão visual e do vocabulário já em produção (Fase 14/17/18), zero copy nova, zero função de store nova, zero busca nova.**

## Performance

- **Duration:** ~1h10 (inclui uma correção de base de worktree — worktree criado a partir de commit anterior ao fechamento de `19-02`, mesmo padrão já documentado em `19-01-SUMMARY.md`/`19-02-SUMMARY.md` — e leitura completa de PLAN/CONTEXT/UI-SPEC/PATTERNS antes de qualquer edição)
- **Tasks:** 2/2 completed
- **Files modified:** 3 (1 componente de produto, 2 arquivos de teste — 1 novo, 1 atualizado)

## Accomplishments

- Novo componente `CandidatoOpcao({ p, r, cp, operador, busy, onAceitar })` em `web/src/App.jsx`, posicionado exatamente entre `PropostaDaPosicao` e `useOpcoesPropostas` (a fatia que os guardiões da Fase 18 já inspecionam) — reusa verbatim o padrão de item de `OportunidadesOpcoes` (linha horizontal scrollável) e os internos de payoff/CTA de `PropostaLastreada` (eyebrow, manchete, linha mono, chips, caixa de payoff com o helper `porLote` null-safe, split Estudo/Operador, CTA por tipo). NÃO renderiza `<PropostaLastreada>` — decisão deliberada para preservar o guardião de contagem 2x da Fase 18.
- `PropostaDaPosicao` ganha ramo condicional: `candidatos.length > 1` renderiza a linha de N `CandidatoOpcao` + `<FonteDoDadoProposta>`; caso contrário, o card único de hoje (`<PropostaLastreada>`) permanece byte-idêntico em comportamento — nenhuma regressão para posições com um candidato só.
- Handler `onAbrirLastreada` de `PropostaDaPosicao` renomeado para `aceitarCandidato(p)`, parametrizado pelo candidato clicado (corpo idêntico, `const p = r.proposta` virou parâmetro `p`); cada `CandidatoOpcao` chama `onAceitar(p)` com o SEU próprio dado — mesmas duas funções de store já existentes (`A.abrirLastreada`/`A.abrirCollar`), nenhuma nova.
- Guardião pré-existente `test_opcoes_collar_ui.mjs` (contagem de handlers `onAbrirLastreada`) atualizado com nota citando Fase 19 — agora coleta as duas formas de handler de aceite (`onAbrirLastreada` em AtivoCard + `aceitarCandidato` em PropostaDaPosicao), preservando intactas todas as asserções por handler (confirmação antes da execução, em ambos os pontos de entrada).
- Arquivo novo `web/tests/test_opcoes_multi_candidato_ui.mjs` — 27 asserções estáticas: posição de `CandidatoOpcao` no arquivo, manchete verbatim/nunca concatenada (guardrail CVM), cor nunca `T.accent` na manchete, helper null-safe antes de multiplicar por `qtyAcoes`, breakeven sem `qtyAcoes`, CTA só em Modo Operador, `disabled={busy || degradado}` presente, `<PropostaLastreada` preso em exatamente 2 pontos de uso, caminho de aceite único (`onAceitar={aceitarCandidato}`), zero chave de copy nova (toda `cp.X` referenciada existe em `COPY.estudo` e `COPY.operador`).
- `npx vite build` verde; `git diff web/src/copy.js web/src/persistence.js web/src/api.js` vazio (confirmado); nenhum pacote novo (`git diff web/package.json` implícito vazio, não tocado).

## Task Commits

Each task was committed atomically:

1. **Task 1: CandidatoOpcao e ramo de N candidatos em PropostaDaPosicao** - `f1a1026` (feat)
2. **Task 2: guardiões estáticos do multi-candidato + guardião de collar atualizado** - `a0ea582` (test)

## Files Created/Modified

- `web/src/App.jsx` — novo componente `CandidatoOpcao` (~90 linhas) + ramo `multi`/`aceitarCandidato` em `PropostaDaPosicao`. `PropostaLastreada` e `AtivoCard` intocados (confirmado por diff/grep).
- `web/tests/test_opcoes_collar_ui.mjs` — seção 3 (contagem de handlers) generalizada para coletar `onAbrirLastreada` + `aceitarCandidato`, nota "Fase 19" adicionada; nenhuma asserção `ok(` removida.
- `web/tests/test_opcoes_multi_candidato_ui.mjs` (novo) — guardião estático completo do ramo multi-candidato, seguindo o padrão `readFileSync` + `ok()` já em uso nos arquivos vizinhos.

## Decisions Made

- Busy único por posição (não por candidato) — decisão já travada em `19-UI-SPEC.md` (Decisão de Interação 1), implementada sem estado novo: todo CTA de `CandidatoOpcao` lê o mesmo `busy` de `PropostaDaPosicao`.
- Nenhum refetch de candidatos após aceite — staleness do irmão resolvida pelo mecanismo já existente (`ORDER_LOCK` no servidor + `flash` no front), não uma trava/mensagem nova.
- Guardião reapontado, nunca apagado (regra do repositório): `test_opcoes_collar_ui.mjs` ganhou nota explícita citando "Fase 19, MULTI-02" explicando por que a asserção mudou e por que a garantia original (confirmar antes de travar lastro) permanece intacta.

## Deviations from Plan

None de código — plano executado exatamente como escrito (componente `CandidatoOpcao` na posição especificada, handler renomeado com a assinatura exata pedida, guardião atualizado com nota, arquivo de teste novo com >=12 asserções). Um desvio operacional de infraestrutura de worktree, documentado abaixo (mesmo padrão já registrado pelos Planos 19-01/19-02).

Durante a implementação, um comentário de código inicial continha a substring literal `<PropostaLastreada>` (citando o componente por nome, entre colchetes angulares, como prosa explicativa) — isso inflava acidentalmente a contagem bruta de `grep -c "<PropostaLastreada"` para 3 em vez de 2 (o critério de aceite da Task 1). Corrigido reescrevendo o comentário sem os colchetes angulares antes do commit; os guardiões automatizados (`test_carteira_opcoes_tira.mjs`/`test_opcoes_multi_candidato_ui.mjs`) já filtram linhas de comentário e não teriam pego isso — o próprio grep literal do critério de aceite do plano é que pegou, confirmando o valor de rodar os greps exatos do plano, não só os testes automatizados.

## Issues Encountered

**Worktree clonado de uma base desatualizada (não relacionado ao código deste plano) — mesmo padrão dos Planos 19-01/19-02, terceira ocorrência em sequência na Fase 19.** O worktree deste executor foi criado a partir do commit `0b9ead1` (anterior à execução completa do Plano 19-02 e ao commit `docs(19): marca 19-02 completo no ROADMAP`), em vez do commit `5cad375` esperado pelo `worktree_branch_check` do orquestrador.

- **Como foi pego:** o próprio prompt de execução já trazia a nota de correção esperada (`worktree_branch_check`), então a verificação foi feita ANTES de qualquer leitura de plano — `git merge-base HEAD 5cad375...` devolveu o HEAD atual (`0b9ead1`), confirmando que `5cad375` era um commit-filho, não ancestral, do HEAD do worktree.
- **Verificação antes de agir:** `git status --short` confirmou working tree limpo (zero trabalho local a perder) e `git diff --stat 0b9ead1 5cad375` mostrou ~58 arquivos incluindo toda a Fase 18/19 (App.jsx, planos/summaries, ROADMAP/STATE/REQUIREMENTS) — sinal inequívoco de base desatualizada, coerente com o padrão já descrito nos dois planos anteriores.
- **Correção:** `git reset --hard 5cad375d4729f0c19b4265afe85b212b25b98890` direto, sem perda de trabalho (nenhum commit próprio ainda existia sobre a base errada).
- **Nenhum código de produto foi afetado** por este incidente.
- **Recomendação para o orquestrador, reforçada pela terceira ocorrência:** o padrão `worktree.baseRef` clonando de uma base antiga (não o HEAD local mais recente) está confirmado sistemático nesta sessão da Fase 19, não incidental. A recomendação de `worktree.baseRef: "head"` já registrada em `19-01-SUMMARY.md`/`19-02-SUMMARY.md` segue válida e ainda não aplicada antes desta wave (19-03/19-04 rodaram em paralelo).

**Ambiente de teste sem `server/.venv`/`web/node_modules` próprios (gitignored)** — seguindo o mesmo precedente dos Planos 19-01/19-02, ambos foram symlinkados TEMPORARIAMENTE a partir do repositório principal só para rodar a verificação (`npx vite build`, `node web/tests/*.mjs`, `pytest`), e removidos antes do commit final de metadados — nenhum symlink ou artefato de ambiente foi commitado (confirmado por `git status --short` limpo após a remoção).

## User Setup Required

None - nenhuma configuração de serviço externo.

## Verification Evidence

- `cd web && npx vite build` (rodado 2x, antes e depois da correção do comentário `<PropostaLastreada>`) → **exit 0** nas duas vezes, 89 módulos transformados, sem erro de sintaxe JSX.
- `grep -c "function CandidatoOpcao" web/src/App.jsx` → **1**; índice de `CandidatoOpcao` (4092) MAIOR que `PropostaDaPosicao` (3992) e MENOR que `useOpcoesPropostas` (4199) — confirmado com `grep -n`.
- `grep -c "<PropostaLastreada" web/src/App.jsx` → **2** (após a correção do comentário).
- `grep -c "const aceitarCandidato = async (p) =>" web/src/App.jsx` → **1**; `grep -c "const onAbrirLastreada = async () =>" web/src/App.jsx` → **1** (só o de AtivoCard restou).
- `grep -c "store.optionsGate("` → **2**; `grep -c "store.optionsProposta("` → **2** (nenhuma busca nova).
- `git diff --stat web/src/copy.js` e `git diff --stat web/src/persistence.js web/src/api.js` → **vazio** nos dois.
- `grep -n "T.accent"` cruzado com linhas de `manchete` → nenhuma ocorrência na mesma linha.
- `grep -c 'typeof v === "number"' web/src/App.jsx` → **6** (>= 2 exigido; o helper existe em `PropostaLastreada` e agora também em `CandidatoOpcao`).
- `node web/tests/test_carteira_opcoes_tira.mjs` → **39/39 ok**, exit 0 (guardiões da Fase 18 intactos).
- `node web/tests/test_opcoes_collar_ui.mjs` → **31/31 ok**, exit 0 (guardião atualizado, nenhuma asserção removida).
- `node web/tests/test_opcoes_proposta_ui.mjs` → exit 0 (`PropostaLastreada` não foi tocada).
- `node web/tests/test_opcoes_multi_candidato_ui.mjs` (novo) → **27/27 ok**, exit 0.
- `cd web && for t in tests/*.mjs; do node "$t"; done` → **116/116 arquivos OK**, exit 0 em todos (suíte web completa).
- `cd server && .venv/bin/python -m pytest tests/ -q` → **27 failed, 1994 passed, 1 skipped** — MESMA contagem e MESMA lista de nomes de teste (comparação visual da lista de `FAILED`) documentada como pré-existente/ambiental em `19-01-SUMMARY.md`/`19-02-SUMMARY.md` (sandbox sem egress de rede para Yahoo/Anthropic/OpenAI, `PermissionError: [Errno 1] Operation not permitted` em `ssl.create_default_context`). Nenhuma falha nova introduzida por este plano.
- `bash scripts/executar.sh --testes` → aborta na etapa de backend (`die "backend com falhas"`) ANTES de chegar à suíte web, por causa da mesma falha ambiental acima — por isso a suíte web foi verificada separadamente (ver acima), confirmando 100% verde. Este comportamento do script (`test.sh` bloqueia o restante do pipeline) é do próprio `executar.sh`, não uma decisão deste plano.
- `git status --short` (após remover os symlinks temporários) → limpo, confirmando nenhum artefato de ambiente commitado.
- `git diff --stat 5cad375 HEAD` → limitado a `web/src/App.jsx`, `web/tests/test_opcoes_collar_ui.mjs`, `web/tests/test_opcoes_multi_candidato_ui.mjs` — exatamente os 3 arquivos de `files_modified` do plano.

## Next Phase Readiness

- `CandidatoOpcao` e o ramo multi de `PropostaDaPosicao` estão prontos para consumo visual — nenhum bloqueio técnico para `19-04`.
- **Pendência herdada dos Planos 19-01/19-02, não deste plano:** suíte canônica de backend ainda não roda 100% verde num ambiente com egress de rede liberado — mesma classe de limitação (sandbox), não nova.
- **Pendência herdada da Fase 18 (não desta fase):** o checkpoint humano da Fase 18 (`18-05-PLAN.md` Task 2) segue parcialmente verificado ao vivo — nenhuma posição real do Alex teve proposta ativa no momento da verificação. Este plano (19-03) NÃO reabre nem resolve essa pendência; qualquer publicação da Fase 19 herda esse risco, conforme já registrado em `STATE.md`.
- **Recomendação operacional reforçada para o orquestrador:** aplicar `worktree.baseRef: "head"` antes de spawnar futuras waves desta fase (19-04) — este é o terceiro incidente idêntico em sequência.

---
*Phase: 19-motor-multi-candidato*
*Completed: 2026-09-04*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/tests/test_opcoes_collar_ui.mjs
- FOUND: web/tests/test_opcoes_multi_candidato_ui.mjs
- FOUND: .planning/phases/19-motor-multi-candidato/19-03-SUMMARY.md
- FOUND commit: f1a1026 (Task 1)
- FOUND commit: a0ea582 (Task 2)
