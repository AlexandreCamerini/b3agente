---
phase: 01-auditoria-diagn-stica-consolidada
plan: 02
subsystem: ui
tags: [ux, accessibility, wcag, react, fastapi, audit, claude-md-principles]

requires: []
provides:
  - "FINDINGS-UX.md: auditoria ao vivo dos 10 princípios obrigatórios do CLAUDE.md contra o produto real"
  - "9 achados F-UX-01..09 com severidade (D-02..D-05), evidência arquivo:linha e recomendação"
  - "Matriz de 8 estados (princípio 9) x 4 telas principais, com 7/8 estados provocados via API real"
affects: [01-06-report-consolidado]

tech-stack:
  added: []
  patterns: ["Nível 3 da escada de verificação ao vivo (API real + código) quando MCP browser tools indisponíveis ao subagente"]

key-files:
  created:
    - .planning/phases/01-auditoria-diagn-stica-consolidada/FINDINGS-UX.md
    - .planning/phases/01-auditoria-diagn-stica-consolidada/01-02-SUMMARY.md
  modified: []

key-decisions:
  - "Nível 3 (API real + código) declarado como teto alcançável: ferramentas mcp__claude-in-chrome__* e mcp__computer-use__* não estavam no toolset deste subagente (consistente com anthropics/claude-code#13898)"
  - "Worktree reusou .venv/node_modules da árvore principal (python absoluto + symlink gitignored) em vez de instalar pacotes novos, após confirmar por diff que App.jsx/copy.js/CLAUDE.md são byte-idênticos entre as duas árvores"
  - "F-UX-04 (ordem parcialmente executada) registrado como ausência estrutural do motor, não como bug — decisão de produto pendente, não corrigível nesta fase de diagnóstico"

requirements-completed: [UX-01, UX-02, UX-03, UX-04]

duration: 23min
completed: 2026-08-18
---

# Phase 1 Plan 02: Auditoria UX/UI Summary

**Auditoria ao vivo dos 10 princípios obrigatórios do CLAUDE.md contra o Boris+ real (backend uvicorn + Vite, dados de mercado reais), com 9 achados evidenciados incluindo um rótulo de fonte de dado hardcoded e factualmente errado no painel técnico (violação direta do princípio 3).**

## Performance

- **Duration:** ~23 min
- **Started:** 2026-08-18T12:16:00Z (setup do ambiente)
- **Completed:** 2026-08-18T12:38:55Z (último commit de conteúdo)
- **Tasks:** 3/3
- **Files modified:** 1 (`FINDINGS-UX.md`, criado e completado em 2 commits incrementais)

## Accomplishments
- Subiu um ambiente real (não mockado) neste worktree — backend `uvicorn` na porta 8787 contra Yahoo/brapi de produção, Vite na porta 5176, conta isolada `auditoria-ux@local.test` — e usou-o para provocar de verdade os estados de "vazio", "erro/fonte indisponível", "ordem rejeitada", "mercado fechado" e "operação concluída" via chamadas HTTP reais, não simulação de payload.
- Auditou os 10 princípios obrigatórios do CLAUDE.md um a um com veredito + evidência, encontrando 1 violação real (princípio 3: fonte de dado exibida errada) e 2 parciais (princípio 4: leak de exceção; princípio 9: estado de fill parcial ausente do motor).
- Produziu 9 achados formatados (`F-UX-01`..`F-UX-09`) cobrindo os 4 requisitos UX, cada um com severidade citando a régua D-02..D-05, evidência `arquivo:linha`, verificação declarada (ao vivo/API real/código) e recomendação.
- Descartou explicitamente os falsos positivos do grep de linguagem proibida (todas as ocorrências de "garant"/"promet"/"100%" são negações do guardrail ou uso técnico não relacionado) em vez de listá-los como achados.

## Task Commits

Each task was committed atomically:

1. **Task 1+2: Setup do ambiente, 10 princípios, UX-01 (matriz de estados) e UX-02 (consistência de modo)** - `a29442a` (docs)
2. **Task 3: UX-03 (responsivo/acessibilidade), UX-04 (copy) + cobertura de requisitos** - `2a947a2` (docs)

_Nota: Tasks 1 e 2 do plano foram produzidas no mesmo arquivo em sequência direta e commitadas juntas ao final da Task 2, pois o conteúdo da Task 1 (seções `## Método de verificação` e `## Auditoria dos 10 princípios`) só ficou estável depois de já ter os dados ao vivo usados também pela Task 2 — nenhum task foi pulado, a verificação automatizada de cada um foi conferida individualmente antes do commit._

## Files Created/Modified
- `.planning/phases/01-auditoria-diagn-stica-consolidada/FINDINGS-UX.md` - Achados brutos da dimensão UX/UI: método de verificação, tabela dos 10 princípios, matriz de 8 estados x 4 telas, 9 achados F-UX-01..09, seção "Verificado e conforme", tabela de cobertura dos 4 requisitos UX
- `.planning/phases/01-auditoria-diagn-stica-consolidada/01-02-SUMMARY.md` - Este arquivo

## Decisions Made

- **Nível 3 da escada de verificação ao vivo (não Nível 1/2):** as ferramentas `mcp__claude-in-chrome__*` e `mcp__computer-use__*` exigidas pelos Níveis 1/2 do plano não estavam disponíveis no conjunto de ferramentas atribuído a este subagente executor — nenhuma ferramenta `mcp__*` aparece na lista de ferramentas, consistente com o bug upstream conhecido (anthropics/claude-code#13898) que remove ferramentas MCP de agentes com `tools:` restrito no frontmatter. Não houve insistência: a escada caiu direto para o Nível 3 (API real + código), conforme instruído pelo plano ("não insistir num nível indisponível"). Essa limitação está declarada explicitamente na seção `## Método de verificação` do relatório, e cada linha de veredito que depende de renderização visual real (responsivo, contraste medido em tela) está marcada como inferida/calculada, não observada.
- **Setup do worktree sem instalar pacotes novos:** o worktree deste plano é uma base antiga que antecede a criação de `.planning/` e não tinha `server/.venv` nem `web/node_modules` próprios. Em vez de rodar `pip install`/`npm install` (que a Regra 3 explicitamente proíbe auto-corrigir sem checkpoint humano — risco de pacote sequestrado), a execução: (1) usou o interpretador Python do `.venv` da árvore principal via caminho absoluto para rodar o `uvicorn` deste worktree (só empresta o interpretador+pacotes, o código servido é 100% o código deste worktree); (2) criou um **symlink** `web/node_modules → .../b3-agente/web/node_modules` (gitignored, confirmado com `git check-ignore`; removido ao final da execução para não deixar rastro no `git status`). Antes de reusar os pacotes da árvore principal, foi confirmado por `diff` que `App.jsx`, `copy.js` e `CLAUDE.md` são byte-idênticos entre as duas árvores — ou seja, o código efetivamente auditado é o do worktree, só a infraestrutura de execução (venv/node_modules) foi emprestada.
- **F-UX-04 tratado como lacuna estrutural, não como bug a corrigir:** "ordem parcialmente executada" não existe no motor de simulação (toda ordem executa 100% ou é rejeitada inteira) — a fase é diagnóstico, então isso foi documentado como achado com recomendação de decisão de produto, não implementado.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Worktree sem `.venv`/`node_modules` próprios impedia subir o stack exigido pelo plano**
- **Found during:** Task 1 (subir o ambiente)
- **Issue:** o worktree atribuído a este plano é uma base de código antiga que antecede `.planning/` e não tinha dependências Python/Node instaladas — `server/.venv/bin/python` e `web/node_modules/.bin/vite` não existiam.
- **Fix:** usado o Python do `.venv` da árvore principal via caminho absoluto (`/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python -m uvicorn app.main:app`, cwd no `server/` deste worktree) e um symlink gitignored `web/node_modules` apontando para o `node_modules` já instalado na árvore principal, removido ao final da execução. Nenhum pacote novo foi instalado (confirmado via `pip`/`npm` não invocados) — satisfaz a disposição `accept` do item T-01-SC do threat model do plano ("Nenhum pacote novo instalado").
- **Files modified:** nenhum arquivo versionado — apenas um symlink temporário fora do controle de versão (removido antes do commit final).
- **Verification:** `git check-ignore -v web/node_modules` confirmou que o symlink nunca apareceria em `git status`; `diff` byte-a-byte de `App.jsx`/`copy.js`/`CLAUDE.md` entre as duas árvores confirmou que o código auditado é idêntico ao do worktree antes de reusar a infraestrutura da árvore principal; `curl http://localhost:8787/api/health` confirmou o backend real respondendo antes de qualquer chamada de auditoria.
- **Committed in:** não aplicável (nenhuma alteração de arquivo versionado; documentado aqui e no `01-CONTEXT.md`/`FINDINGS-UX.md` para rastreabilidade).

---

**Total deviations:** 1 auto-fixed (1 blocking, ambiente de execução)
**Impact on plan:** Necessário para viabilizar a verificação ao vivo exigida pelo D-01; nenhum código de produto foi alterado, nenhum pacote novo instalado, sem escopo adicional além do que o plano já previa fazer.

## Issues Encountered

- Chamadas de API iniciais usaram nomes de parâmetro/campo errados (`tickers` em vez de `symbols` para `/api/quotes`; `ticker` em vez de `t` para `/api/buy`/`/api/sell`) — corrigido lendo o código de `main.py` antes de repetir a chamada; não é um achado do produto, foi erro de teste do próprio executor, descartado da lista de achados.
- Durante a investigação de `POST /api/buy` com ticker inválido, a primeira chamada revelou um `HTTP 500` com stack de exceção crua em vez do `502` limpo esperado pelo plano — isso **não** foi tratado como "issue a resolver", foi promovido a achado formal (F-UX-03), pois é exatamente o tipo de comportamento real que a verificação ao vivo existe para capturar.

## User Setup Required

None - nenhuma configuração de serviço externo necessária. O backend/Vite subidos nesta execução são efêmeros (dev local); o Vite exclusivo deste plano (porta 5176) foi encerrado ao final. O backend compartilhado (porta 8787) foi deixado rodando porque outros planos desta wave (01-01, 01-05) podem depender dele — não deve ser encerrado por este plano (guardrail do próprio plano: "NUNCA rodar `--stop`").

## Next Phase Readiness

- `FINDINGS-UX.md` está pronto para consumo pelo plano 01-06 (consolidação): formato `### F-UX-NN` com os 6 campos de rótulo exato, severidade citando D-0X, e um possível cruzamento de duplicata já sinalizado (F-UX-08 ↔ CODE-03, a ser resolvido na consolidação).
- Achado mais crítico para a régua de severidade do REPORT-01: **F-UX-01** (Crítico, D-02) — rótulo de fonte de dado fixo/incorreto no painel técnico, com evidência de que o backend nem devolve o campo necessário para corrigir no front sozinho (mudança de contrato de API, não só de UI).
- Nenhum bloqueio para o plano 01-06 prosseguir; nenhuma correção foi implementada nesta fase (conforme escopo do CONTEXT.md — diagnóstico, não implementação).

---
*Phase: 01-auditoria-diagn-stica-consolidada*
*Completed: 2026-08-18*

## Self-Check: PASSED

- FOUND: `.planning/phases/01-auditoria-diagn-stica-consolidada/FINDINGS-UX.md`
- FOUND: commit `a29442a` (Task 1+2)
- FOUND: commit `2a947a2` (Task 3)
- `git status --porcelain server web web-admin` confirmed empty at time of each commit
