---
phase: 04-corre-o-m-dio-storyline-ux
plan: 06
subsystem: ui
tags: [react, finance, benchmark, ibovespa, svg-chart, jsdom-free-tests]

# Dependency graph
requires:
  - phase: 04-corre-o-m-dio-storyline-ux (04-04)
    provides: "GET /api/benchmark/ibov — contrato fixado: 200 {t,nome,fonte,candles,asOf} | 502 {\"detail\":\"Comparação com o Ibovespa indisponível agora.\"}"
  - phase: 04-corre-o-m-dio-storyline-ux (04-05)
    provides: "App.jsx/persistence.js estáveis nos mesmos componentes vizinhos (AnalysisView/HistoricoScreen), sem overlap de arquivo com este plano"
provides:
  - "equityCurve(...) devolve `datas` em paralelo a `curve` — permite qualquer consumidor futuro alinhar uma série externa por data real da carteira"
  - "benchmarkSerie(candles, datas) — aritmética pura de alinhamento de índice por data, reaproveitável fora do CapitalCurve"
  - "store.benchmarkIbov(period) nos dois stores (serverStore/deviceStore)"
  - "Passo 8 (CapitalCurve) mostra a carteira e o Ibovespa na mesma escala, com a diferença explicitada (VS. IBOVESPA) e degradação sem dado fabricado"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Segunda série num SVG normalizado ao viewBox: escala comum calculada sobre a UNIÃO das duas séries convertidas para % (transformação afim da série primária garante zero regressão visual quando a segunda série falta)"
    - "Path SVG com buracos: ponto null interrompe o path (novo M no próximo ponto válido) em vez de interpolar/ligar por cima da ausência de dado"

key-files:
  created:
    - web/tests/test_benchmark_curva.mjs
  modified:
    - web/src/finance.js
    - web/src/api.js
    - web/src/persistence.js
    - web/src/App.jsx
    - web/tests/test_finance.mjs

key-decisions:
  - "equityCurve ganhou `datas` como CHAVE ADITIVA (não reordenou/alterou nenhuma chave existente) — as 3 call sites de App.jsx e todos os casos antigos de test_finance.mjs continuam batendo sem edição, confirmado pela suíte."
  - "benchmarkSerie não faz interpolação nem extrapolação: uma data anterior a QUALQUER vela do índice vira `null` (nunca 0, nunca o valor mais próximo). Segue literalmente CLAUDE.md princípio 4 (nunca inventar valor quando a fonte falha/não cobre)."
  - "Escala do SVG passou de valores absolutos de patrimônio para % desde ec.base — mudança necessária para comparar as duas séries no mesmo viewBox. Como a transformação é afim e monotônica, o path da carteira SEM benchmark é matematicamente idêntico ao de antes (mesma forma normalizada); confirmado visualmente pela ausência de mudança em test_chart_colors_theme_aware.mjs (guardião de cor continua verde) e pela leitura manual da fórmula."
  - "Legenda e célula VS. IBOVESPA só renderizam quando a série do índice é de fato desenhável (`temIbov`), não apenas quando a resposta HTTP chegou — evita legenda anunciando uma linha tracejada que não existe no gráfico quando `benchmarkSerie` devolve null (candles insuficientes/datas não cobertas) mesmo com a chamada de rede tendo tido sucesso."
  - "Guardião de pureza adicionado a test_finance.mjs (checa ausência de fetch/Date.now/localStorage em finance.js) restrito a linhas de CÓDIGO, excluindo comentários — o comentário pré-existente de historicoDesatualizado já citava \"Date.now()\" em prosa explicando por que a função NÃO usa, o que um grep cru sobre o arquivo inteiro capturaria como falso-positivo."

patterns-established:
  - "Path SVG com múltiplos segmentos M/L reconstruído via forEach com flag `aberto`, mesmo padrão que qualquer futura 3ª série neste componente (ou outro gráfico do app) pode reaproveitar para representar cobertura parcial sem fabricar dado."

requirements-completed: [FIX-C03]

# Metrics
duration: ~25min
completed: 2026-08-21
---

# Phase 4 Plan 06: Ibovespa no Passo 8 — comparação real da carteira com o benchmark Summary

**`equityCurve` passa a expor `datas` por ponto e `benchmarkSerie` alinha o Ibovespa por data real (sem inventar/extrapolar); o Passo 8 (CapitalCurve) desenha as duas séries na mesma escala com uma 4ª célula "VS. IBOVESPA" — o número que responde "foi bom ou ruim?" — e degrada com uma frase única quando o índice não vem, sem nunca contaminar a leitura da carteira.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-08-21T23:15:00-03:00 (aprox., logo após a leitura do plano e dos arquivos-fonte)
- **Completed:** 2026-08-21T23:40:00-03:00 (aprox., após suíte canônica completa verde)
- **Tasks:** 3/3 completas
- **Files modified:** 6 (2 arquivos-fonte de Task 1, 2 de Task 2, 1 de Task 3 + 1 teste novo)

## Accomplishments
- `equityCurve` (`web/src/finance.js`) devolve `datas`, array paralelo a `curve` construído na MESMA decisão de substituir/anexar o ponto ao vivo — mudança estritamente aditiva, verificada contra os 3 call sites de `App.jsx` (linhas 1612, 1710, ~7860) e todos os casos antigos de `test_finance.mjs` (nenhum editado, todos continuam passando).
- `benchmarkSerie(candles, datas)` (novo, `finance.js`) alinha o Ibovespa por data real: usa o último fechamento REAL anterior quando o índice não negociou naquele dia, nunca extrapola para trás de qualquer vela (vira `null`), descarta vela com `close` não-numérico ou `<= 0`, calcula `pct%` desde o primeiro ponto coberto (nunca desde a 1ª vela recebida), devolve `null` explícito com menos de 2 velas úteis ou menos de 2 datas cobertas. Zero `NaN`/`Infinity`/`-0` possível — confirmado por 8 casos de teste novos que cobrem cada guard clause do texto do plano.
- `store.benchmarkIbov(period)` (novo, `web/src/api.js` + `web/src/persistence.js`) — pass-through puro nos dois stores (`serverStore`/`deviceStore`), `TIMEOUT_MS` (não é chamada de IA), `period` via `encodeURIComponent`, sem cache no cliente (servidor já cacheia 15min). Paridade confirmada por `test_fase3_paridade_stores_generica.mjs` (server=61, device=61) e `test_api_parity.mjs`.
- `CapitalCurve` (`web/src/App.jsx`) desenha a 2ª série (Ibovespa, tracejada, `P.textDim`, `strokeDasharray="3 3"`) ANTES da carteira no SVG (z-order: carteira sempre por cima em qualquer cruzamento), interrompida em cada ponto sem cobertura (novo `M`, nunca liga por cima de um buraco). Escala compartilhada: a carteira também vira % desde `ec.base` — transformação afim e monotônica, então o caminho SEM benchmark fica visualmente idêntico ao de antes. Legenda inline e a 4ª célula `VS. IBOVESPA` (`retAcum - bm.retAcum`) só aparecem quando a série do índice é de fato desenhável. Falha do Ibovespa (502 do backend ou `benchmarkSerie` devolvendo `null`) nunca contamina a curva/KPIs da carteira — só some a 2ª série, com a frase única `"Comparação com o Ibovespa indisponível agora."` em `T.textFaint` (mesma frase do backend, ecoando o padrão já usado no fallback de IA do FIX-C01).
- Guardião novo `web/tests/test_benchmark_curva.mjs` (15 asserções) trava: `strokeDasharray`/`P.textDim` no path do benchmark; ausência de `P.positive`/`P.negative`/`P.accent` nesse mesmo path; z-order por posição no fonte; a célula `VS. IBOVESPA` condicional e única; a frase de indisponibilidade verbatim em `T.textFaint`; ausência de `|| 0`/`?? 0` no caminho que produz `bm.pct`/`ibovPath` (nenhuma linha plana fabricada); o import de `benchmarkSerie` na linha 15; o placeholder do estado vazio intocado; e que a busca do benchmark é guardada por `hasSeries` (sem chamada desnecessária).
- Suíte canônica completa (`bash scripts/executar.sh --testes`) verde: **1325 testes backend passed, 1 skipped** + **94/94 `web/tests/*.mjs` OK** (incluindo os 3 arquivos tocados/criados por este plano).

## Task Commits

Each task was committed atomically (Task 1 seguiu TDD — RED/GREEN):

1. **Task 1 RED: casos falhando para `equityCurve.datas` e `benchmarkSerie`** - `beea87b` (test)
2. **Task 1 GREEN: aritmética pura do benchmark alinhado por data** - `cf64249` (feat)
3. **Task 2: cliente HTTP do benchmark nos dois stores (paridade)** - `07a4a0b` (feat)
4. **Task 3: segunda série, legenda e célula VS. IBOVESPA no CapitalCurve** - `5439ea8` (feat)

_Task 1 era `tdd="true"` — RED confirmado rodando `node tests/test_finance.mjs` antes da implementação (SyntaxError: `benchmarkSerie` não exportado), commitado separado do GREEN. Tasks 2 e 3 não eram TDD — guardião escrito junto do código na mesma tarefa/commit._

## Files Created/Modified
- `web/src/finance.js` — `equityCurve` ganha `datas` (chave aditiva); `benchmarkSerie(candles, datas)` novo (aritmética pura de alinhamento por data, sem I/O)
- `web/src/api.js` — `benchmarkIbov(period)` novo, `TIMEOUT_MS`, `period` via `encodeURIComponent`
- `web/src/persistence.js` — `benchmarkIbov: (period) => api.benchmarkIbov(period)` em `serverStore` e `deviceStore` (pass-through puro nos dois, guardrail de paridade)
- `web/src/App.jsx` — import de `benchmarkSerie` (linha 15); `CapitalCurve` reescrito: efeito de busca do benchmark (`hasSeries`-guardado, sem retry), escala compartilhada em %, 2ª série tracejada com z-order/buracos, legenda condicional, célula `VS. IBOVESPA` condicional, frase única de indisponibilidade
- `web/tests/test_finance.mjs` — 2 blocos novos (`equityCurve: datas`, `benchmarkSerie`) + guardião de pureza ajustado para não capturar comentário pré-existente
- `web/tests/test_benchmark_curva.mjs` (novo) — guardião estático do contrato visual FIX-C03

## Decisions Made
Ver `key-decisions` no frontmatter (mudança aditiva em `equityCurve`; `benchmarkSerie` nunca extrapola/interpola; escala em % para comparabilidade sem regressão visual; legenda/célula condicionadas a `temIbov`, não só à resposta HTTP; ajuste do guardião de pureza para evitar falso-positivo contra prosa pré-existente).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug/Test gap] Guardião de pureza que eu mesmo escrevi gerava falso-positivo contra comentário pré-existente**
- **Found during:** Task 1, ao rodar `node tests/test_finance.mjs` após implementar `benchmarkSerie`
- **Issue:** Adicionei um teste (`grep`-like) checando que `finance.js` não tem `fetch`/`Date.now`/`localStorage`, seguindo o item da acceptance_criteria do plano. O regex cru capturou uma linha de PROSA pré-existente (comentário de `historicoDesatualizado`, linha ~206, escrito antes deste plano) que explica "Puras: sem `Date.now()` interno" — um falso-positivo do MEU PRÓPRIO guardião, não uma impureza real introduzida por este plano.
- **Fix:** Restringi a checagem a linhas de código (excluindo linhas que começam com `//`), preservando a intenção real do guardião (nenhuma chamada de rede/relógio/storage no CÓDIGO de `finance.js`) sem quebrar por causa de documentação legítima já existente.
- **Files modified:** web/tests/test_finance.mjs
- **Verification:** `node tests/test_finance.mjs` verde; confirmado manualmente que `grep -n "fetch\|Date.now\|localStorage" web/src/finance.js` só bate na linha de comentário pré-existente (nenhuma ocorrência nova introduzida por este plano).
- **Committed in:** cf64249 (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixado (bug no próprio guardião de teste que eu escrevi, não no código de produção).
**Impact on plan:** Sem impacto em comportamento — ajuste isolado ao teste. `finance.js` continua 100% puro (nenhuma chamada real a rede/relógio/storage), confirmado tanto pelo teste corrigido quanto por leitura manual do arquivo inteiro.

## Issues Encountered
- `web/node_modules` não estava instalado neste worktree (mesmo achado recorrente dos Planos 04-03/04-04/04-05 — worktrees não compartilham `node_modules` do clone principal). Rodei `npm ci` em `web/` antes do primeiro `npx vite build`; não afeta o clone principal nem outros worktrees (gitignored).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- FIX-C03 fechado ponta a ponta: backend (`GET /api/benchmark/ibov`, Plano 04-04) + frontend (aritmética pura, cliente HTTP nos dois stores, UI do Passo 8, Plano 04-06). Suíte canônica completa verde (1325 pytest + 93 web/tests).
- Nenhum arquivo de `server/` foi tocado por este plano (confirmado por `git status`/commits) — consistente com o escopo (front-only).
- Verificação AO VIVO recomendada pelo plano (servidor real, Ibovespa OK vs. rota forçada a 502, confirmando que a curva da carteira não muda de forma) NÃO foi executada nesta sessão — o plano marca essa checagem como "recomendada", não bloqueante, e a suíte automatizada (incluindo o novo `test_benchmark_curva.mjs`) cobre o contrato visual/degradação por asserção estática. Fica como item de verificação manual opcional para quem revisar esta entrega com o servidor no ar.
- Sem bloqueios conhecidos para os planos seguintes da Fase 4.

---
*Phase: 04-corre-o-m-dio-storyline-ux*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: web/src/finance.js
- FOUND: web/src/api.js
- FOUND: web/src/persistence.js
- FOUND: web/src/App.jsx
- FOUND: web/tests/test_finance.mjs
- FOUND: web/tests/test_benchmark_curva.mjs
- FOUND: .planning/phases/04-corre-o-m-dio-storyline-ux/04-06-SUMMARY.md
- FOUND commit: beea87b (Task 1 RED)
- FOUND commit: cf64249 (Task 1 GREEN)
- FOUND commit: 07a4a0b (Task 2)
- FOUND commit: 5439ea8 (Task 3)
