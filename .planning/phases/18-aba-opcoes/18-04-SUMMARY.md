---
phase: 18-aba-opcoes
plan: 04
subsystem: testing

tags: [static-source-inspection, guardian, react, options, portfolio]

# Dependency graph
requires:
  - phase: 18-aba-opcoes
    plan: "18-01"
    provides: "hook useOpcoesPropostas(tickers), 6 chaves de copy.js"
  - phase: 18-aba-opcoes
    plan: "18-02"
    provides: "PropostaDaPosicao, âncora id={posicao-TICKER}, opcoesFor/setOpcoesFor"
  - phase: 18-aba-opcoes
    plan: "18-03"
    provides: "OportunidadesOpcoes, montagem em CarteiraScreen, abrirOpcoesDe"
provides:
  - "web/tests/test_carteira_opcoes_tira.mjs — guardião estático da tira de oportunidades e do detalhe em Posições, 11 blocos de asserção, 37 chamadas de ok("
  - "prova de mordida registrada: guardião falha quando a manchete é composta e quando a guarda de carteira vazia é removida"
  - "suíte canônica completa (pytest + web/tests/*.mjs) verde com a Fase 18 no ar"
affects: [18-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Caminhamento estrutural de encadeamento .then/.catch/.finally por balanceamento de parênteses, em vez de janela fixa de caracteres, para verificar best-effort — mais robusto a chamadas aninhadas (ver Decisões)"

key-files:
  created:
    - web/tests/test_carteira_opcoes_tira.mjs
  modified: []

key-decisions:
  - "Item (6) do plano (best-effort preservado) especificava checar '.catch( em até 200 caracteres' após cada chamada de store.optionsGate(/store.optionsProposta(. Medido no fonte real: a distância de store.optionsGate( ao SEU PRÓPRIO .catch( é de 587 caracteres (a chamada aninhada de store.optionsProposta( dentro do .then, com seu próprio .then/.catch, empurra o catch externo pra fora de qualquer janela fixa razoável). Uma checagem de janela de 200 chars teria dado FALSO-VERMELHO permanente no código correto. Implementada em vez disso uma função que caminha o encadeamento real (.then/.catch/.finally) por balanceamento de parênteses a partir de cada chamada — mede a mesma garantia (nenhuma chamada sem .catch no próprio encadeamento) sem depender de contagem de caracteres do texto-fonte. Confirmado por leitura do trecho antes de escrever a asserção, conforme instrução do próprio plano ('Antes de escrever qualquer regex, LER o trecho correspondente')."

patterns-established:
  - "Verificação de 'toda promise tem tratamento de erro' por caminhamento estrutural do encadeamento (balanceamento de parênteses), não por distância de caracteres — reutilizável em guardiões futuros que precisem provar 'best-effort' em código com chamadas de rede aninhadas."

requirements-completed: [NAV-01, NAV-02, NAV-03]

duration: ~35min
completed: 2026-09-03
---

# Phase 18 Plan 04: Guardião de guardrail estendido à tira de opções Summary

**`test_carteira_opcoes_tira.mjs` — guardião estático de 37 asserções (11 blocos) trancando manchete-só-do-motor, estado vazio agregado obrigatório, silêncio do card individual, fetch único por ticker e best-effort da tira "Oportunidades de opções"; suíte canônica completa (2010 testes de backend + 113 arquivos `.mjs`) verde.**

## Performance

- **Duration:** ~35 min (leitura de contexto + leitura do fonte real + Task 1 com prova de mordida + Task 2, suíte canônica completa incluindo pytest ~150s)
- **Started:** 2026-09-03T~11:45:00Z (aprox., após fast-forward do worktree)
- **Completed:** 2026-09-03T12:10:31Z
- **Tasks:** 2/2
- **Files modified:** 1 (criado)

## Accomplishments

- `web/tests/test_carteira_opcoes_tira.mjs` criado, padrão "static source inspection" da casa (`readFileSync` + `import { COPY }`, sem build/DOM), 37 chamadas de `ok(` em 11 blocos:
  1. Copy nas 6 chaves novas, nos dois ramos, string literal, `SemCobertura`/`SemSetup` distintas entre e dentro dos ramos.
  2. Guardrail CVM: `{pr.manchete}` renderizado direto na tira, sem template string/concatenação/`"Vender " +` envolvendo manchete, linha da manchete sem `T.accent`.
  3. Estado vazio NAV-03: as três chaves (`tiraOpcoesCarregando`/`SemCobertura`/`SemSetup`) referenciadas, ramo de carregando avaliado antes do vazio.
  4. Tira ausente com carteira vazia: `<OportunidadesOpcoes` entre `function CarteiraScreen(` e a guarda `data.positions.length === 0`, guarda `data.positions.length > 0` nos 120 chars anteriores.
  5. Estrutura só sobre posição real: `useOpcoesPropostas(data.positions.map(` na chamada, sem menção a watchlist/radar.
  6. Best-effort preservado: função de caminhamento estrutural do encadeamento `.then/.catch/.finally` (ver Decisões — desvio do "200 caracteres" do plano) confirma `.catch(` no encadeamento de `store.optionsGate(` e `store.optionsProposta(`.
  7. Uma busca por ticker: exatamente 2 ocorrências de `store.optionsGate(` e de `store.optionsProposta(` no fonte (AtivoCard + hook).
  8. Silêncio do card individual: guarda `if (!r || !r.proposta) return null;` em `PropostaDaPosicao`, sem vazamento das chaves do estado vazio agregado.
  9. Estado por ticker: `opcoesFor`/`setOpcoesFor` declarado, `opcoesFor === p.t` no laço, `histFor`/`editFor` intocados.
  10. Âncora de scroll: `id={"posicao-" + p.t}`, `getElementById("posicao-" + t)` + `scrollIntoView(`, `abrirOpcoesDe` chama `setOpcoesFor(`.
  11. Assinatura de `PropostaLastreada` intocada, 2 ocorrências de `<PropostaLastreada` (AtivoCard original + PropostaDaPosicao novo).
- **Prova de mordida executada e revertida** (ver Deviations/Issues): (a) `{pr.manchete}` trocado temporariamente por `{"Vender " + pr.manchete}` em `OportunidadesOpcoes` → guardião FALHOU em 3 asserções (render direto, "Vender " +, T.accent — nenhuma dessas mudou de fato, mas a nova composição inválida cascateou), revertido via `git checkout -- web/src/App.jsx`, guardião voltou a passar 37/37. (b) guarda `data.positions.length > 0` removida da montagem de `<OportunidadesOpcoes>` → guardião FALHOU em 1 asserção (120 chars antes da tag), revertido, voltou a passar 37/37.
- Suíte canônica completa verde: `npx vite build` limpo (89 módulos, sem erro), `bash scripts/executar.sh --testes`: **2010 passed, 1 skipped** no backend (pytest), **113 arquivos `.mjs`** OK (112 pré-existentes + `test_carteira_opcoes_tira.mjs` novo) — incluindo os 3 guardiões nomeados como intocáveis pelo plano (`test_opcoes_proposta_ui.mjs`, `test_carteira_lastro_ui.mjs`, `test_opcoes_collar_ui.mjs`).

## Task Commits

Each task was committed atomically:

1. **Task 1: Guardião estático da tira de oportunidades e do detalhe em Posições** - `d115cff` (test)
2. **Task 2: Suíte canônica completa verde** - sem commit (nenhum arquivo alterado — tarefa é puramente de verificação: `npm install`/`npx vite build`/`bash scripts/executar.sh --testes` não produziram diff em nenhum arquivo rastreado; `git status --porcelain` ficou vazio ao final)

**Plan metadata:** (this commit, SUMMARY.md)

## Files Created/Modified

- `web/tests/test_carteira_opcoes_tira.mjs` (novo) — guardião estático da Fase 18, 202 linhas, 37 asserções em 11 blocos.

## Decisions Made

- Item (6) do plano ("best-effort preservado", checagem de `.catch(` em até 200 caracteres) foi implementado com caminhamento estrutural do encadeamento de promises em vez de janela fixa de caracteres — ver `key-decisions` no frontmatter para a medição exata (587 chars de distância real vs. 200 especificados) e o raciocínio completo. Escolha necessária para evitar falso-vermelho permanente no código correto; a garantia medida (todo `store.optionsGate(`/`store.optionsProposta(` tem `.catch(` no próprio encadeamento) é a mesma pretendida pelo plano.
- Nenhuma outra decisão de arquitetura — as demais 10 asserções seguem literalmente o texto do plano, verificadas contra o fonte real antes de escrever cada regex (instrução explícita do plano: "regex escrita de memória... produz guardião falso-verde ou falso-vermelho").

## Deviations from Plan

**1. [Rule 1 - Bug] Janela de 200 caracteres do item (6) substituída por caminhamento estrutural**
- **Found during:** Task 1, ao ler o corpo real de `useOpcoesPropostas` antes de escrever a regex (instrução do próprio plano).
- **Issue:** medição do fonte mostrou que `store.optionsGate(` está a 587 caracteres do seu `.catch(` correspondente (a chamada aninhada de `store.optionsProposta(`, com seu próprio `.then`/`.catch`, fica no meio do caminho) — uma janela de 200 chars, como literalmente especificado no plano, teria produzido um guardião falso-vermelho no primeiro `node web/tests/test_carteira_opcoes_tira.mjs` mesmo sem nenhuma regressão real no código.
- **Fix:** implementada `encadeamentoTemCatch(src, chamada)` — caminha `.then(...)`/`.catch(...)`/`.finally(...)` por balanceamento de parênteses a partir da chamada, confirmando se `.catch(` aparece no encadeamento real, independente de distância em caracteres.
- **Files modified:** `web/tests/test_carteira_opcoes_tira.mjs` (não é uma correção em código de produção — é o próprio arquivo sendo criado nesta task).
- **Commit:** `d115cff`.

Fora isso, plano executado como escrito. As demais ações fora do texto literal foram operacionais (ambiente): fast-forward do worktree (`git merge --ff-only`, HEAD era ancestral estrito do commit-base) e `npm install`/`npx vite build`/`bash scripts/executar.sh --testes` fora do sandbox padrão (mesmo artefato de sandbox — bloqueio de certificados/cache root-owned — já documentado nos Planos 18-01/02/03).

## Issues Encountered

- `npm install`/`npx vite build`/`bash scripts/executar.sh --testes` dentro do sandbox padrão falharam com `ERROR: failed to copy trust settings of system certificate`/`EPERM` no cache do npm — mesmo artefato de sandbox documentado nos 3 planos anteriores da fase (bloqueio de acesso a certificados/cache root-owned, não relacionado a nenhuma mudança deste plano). Resolvido reexecutando fora do sandbox (`dangerouslyDisableSandbox`), com apresentação explícita dos fatos exigidos pelo Fact-Forcing Gate para os comandos classificados como destrutivos (`rm -rf node_modules`, os dois `git checkout -- web/src/App.jsx` da prova de mordida). Confirmado após cada operação que nenhum arquivo fora do escopo esperado foi tocado (`git diff --stat web/package.json web/package-lock.json package.json package-lock.json` vazio; `git status --porcelain` vazio ao final de cada revert).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- A Fase 18 (NAV-01/NAV-02/NAV-03) está funcionalmente completa e travada por guardião: tira agregada, detalhe por posição e as regras que os sustentam (manchete só do motor, estado vazio obrigatório, silêncio do card individual, busca best-effort, uma busca por ticker, estrutura só sobre posição real) não podem regredir silenciosamente numa edição futura de `App.jsx`.
- Plano 18-05 (publicação — `scripts/bump.sh` + `publicar-web.sh`) pode prosseguir: este plano deliberadamente NÃO publicou (`git status --porcelain server/web_dist` vazio, confirmado).
- Nenhum bloqueio identificado.

---
*Phase: 18-aba-opcoes*
*Completed: 2026-09-03*
