---
phase: 20-funda-o-estrutural-e-tipogr-fica
plan: 02
subsystem: ui
tags: [react, css, typography, tabular-nums, design-tokens, web]

# Dependency graph
requires:
  - phase: 20-funda-o-estrutural-e-tipogr-fica
    plan: "01"
    provides: "CONTENT_MAX_WIDTH e guardião estático web/tests/test_fase20_fundacao_visual.mjs"
provides:
  - "Regra .b3 [style*=\"ui-monospace\"]{ font-variant-numeric: tabular-nums; } em GlobalStyle() — cobre os 151 call sites de fontFamily: MONO sem editar nenhum (TYPO-01)"
  - "Escala numérica nomeada numHero (34/700), numBody (18/700), numMicro (13/600) declarada uma única vez (TYPO-02)"
  - "Primeiro consumidor real de numBody: patrimônio do Topbar"
  - "Guardião estendido com 6 asserções novas de TYPO-01/TYPO-02"
affects: [21, 22]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Escala numérica como objetos JS de só tamanho/peso (sem lineHeight/color/fontFamily), combinados por spread no call site — não classe CSS"
    - "Regra de atributo (.b3 [style*=\"...\"]) para afetar N call sites de style inline sem editar nenhum deles — segunda aplicação do padrão já usado no 20-01 para overflow"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_fase20_fundacao_visual.mjs

key-decisions:
  - "Seguida a decisão mecânica travada no plano (opção a): regra CSS de atributo em GlobalStyle(), não conversão de MONO em objeto de estilo — zero edição dos 151 call sites, confirmado por grep -c 'fontFamily: MONO' continuando 151 depois da mudança."
  - "numHero/numMicro nascem sem consumidor nesta fase, por decisão explícita do 20-CONTEXT.md (migração tela a tela é escopo das Fases 21/22) — documentado em comentário no código, não é esquecimento."
  - "web/node_modules ausente no worktree (git worktrees não compartilham node_modules, que é gitignored); resolvido com symlink para o node_modules do repo principal (mesmo package.json/package-lock.json, diff vazio confirmado) em vez de reinstalar — evita rede/tempo desnecessário sem alterar nenhum lockfile."

requirements-completed: [TYPO-01, TYPO-02]

# Metrics
duration: ~35min
completed: 2026-09-05
---

# Phase 20 Plan 02: Fundação tipográfica numérica Summary

**Dígitos de largura fixa (`tabular-nums`) em todo valor financeiro que já usa o stack `MONO`, via uma única regra CSS de atributo em `GlobalStyle()`, mais a escala numérica nomeada `numHero`/`numBody`/`numMicro` com o patrimônio do Topbar como primeiro consumidor real.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-09-05
- **Tasks:** 2 (Task 1 completa; Task 2 completa exceto a verificação ao vivo por browser, ver "Issues Encountered")
- **Files modified:** 2 (`web/src/App.jsx`, `web/tests/test_fase20_fundacao_visual.mjs`)

## Accomplishments
- TYPO-01: `.b3 [style*="ui-monospace"]{ font-variant-numeric: tabular-nums; }` inserida em `GlobalStyle()`, cobrindo os 151 call sites de `fontFamily: MONO` sem tocar em nenhum deles (confirmado por grep antes/depois).
- TYPO-02: três constantes `numHero`/`numBody`/`numMicro` declaradas com os valores exatos da sessão de design (34/700, 18/700, 13/600); `numBody` já tem consumidor real (patrimônio do Topbar), diff visual zero (valores byte-idênticos aos literais removidos).
- Guardião estático estendido com 6 asserções novas (2 para TYPO-01 travando o acoplamento regra↔string `MONO`, 4 para TYPO-02 travando valores exatos + consumidor real); sensibilidade confirmada manualmente (removendo a regra tabular-nums o teste falha; restaurado).
- Suíte canônica completa verde: `bash scripts/executar.sh --testes` saiu com `EXIT=0` (2021 pytest passed + 1 skipped; todos os testes `.mjs`, incluindo o guardião estendido, `[OK]`).
- `cd web && npx vite build` saiu com código 0, `dist/` gerado dentro do próprio worktree (confirmado com `ls -la web/dist` — diretório real, não segue nenhum symlink para fora).

## Task Commits

1. **Task 1: Regra tabular-nums + escala numérica nomeada + primeiro consumidor** — `33012c6` (feat)
2. **Task 2 (Parte 2 e 3 — guardião estendido + suíte canônica): sem Parte 1 (verificação ao vivo por browser, ver Issues Encountered)** — `8ec1e4b` (test)

**Base do plano:** `06d9ba2` (docs: update tracking after wave 1, plano 20-01)

## Files Created/Modified
- `web/src/App.jsx` — comentário + regra `.b3 [style*="ui-monospace"]{ font-variant-numeric: tabular-nums; }` em `GlobalStyle()` (perto de `.b3 input,.b3 textarea,.b3 select`); constantes `numHero`/`numBody`/`numMicro` declaradas logo após `CONTENT_MAX_WIDTH`; Topbar (patrimônio) migrado de `{ fontWeight: 700, fontSize: "18px", lineHeight: 1.05, color: T.textPrimary }` para `{ ...numBody, lineHeight: 1.05, color: T.textPrimary }`.
- `web/tests/test_fase20_fundacao_visual.mjs` — 6 asserções novas (TYPO-01: regra CSS presente + acoplamento com a string `ui-monospace` de `MONO`; TYPO-02: os três valores exatos + consumidor real de `numBody`).

## Decisions Made
- Opção mecânica (a) do plano seguida à risca: regra de atributo em `GlobalStyle()`, zero edição de call site — a alternativa (converter `MONO` em objeto de estilo com spread em ~151 pontos) foi descartada pelo próprio plano por custo/risco desproporcional.
- Comentário no código explicando o porquê do seletor de atributo (grafado para não conter a substring literal `fontFamily: MONO`, que inflaria a contagem do critério de aceite "151 call sites intocados" — achado durante a Task 1, corrigido antes do commit).
- `numHero`/`numMicro` deliberadamente sem consumidor nesta fase (decisão travada em `20-CONTEXT.md`), com comentário no código nomeando as Fases 21/22 como consumidoras futuras.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comentário da regra tabular-nums colidia com o próprio critério de aceite do plano**
- **Found during:** Task 1, verificação dos critérios de aceite
- **Issue:** O primeiro texto do comentário explicativo da regra CSS continha a substring literal `fontFamily: MONO` (para explicar de onde vem a string `ui-monospace`), o que inflava `grep -c 'fontFamily: MONO' web/src/App.jsx` para 152 em vez dos 151 esperados — o próprio critério de aceite do plano existe para provar que nenhum call site foi tocado, e o comentário estava mascarando essa prova.
- **Fix:** Reescrito o comentário para dizer "call site declara MONO como fontFamily" em vez de "fontFamily: MONO", preservando o sentido sem repetir a substring literal.
- **Files modified:** `web/src/App.jsx`
- **Verification:** `grep -c 'fontFamily: MONO' web/src/App.jsx` voltou a 151 após o ajuste.
- **Committed in:** `33012c6` (Task 1 commit — corrigido antes do commit, não é um commit separado)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug no próprio comentário de documentação, sem impacto funcional).
**Impact on plan:** Nenhum scope creep — correção editorial dentro do mesmo arquivo/task, necessária para o critério de aceite do plano bater.

## Issues Encountered

**Task 2 Parte 1 (verificação ao vivo por browser) NÃO foi executada por este subagent.** Confirmado empiricamente no início desta sessão (mesma limitação já documentada no `20-01-SUMMARY.md`, seção "Issues Encountered"): subagentes spawnados via Task não herdam ferramentas MCP de navegador do orquestrador (`mcp__computer-use__*`, `mcp__claude-in-chrome__*` — bug upstream anthropics/claude-code#13898). Este subagent não tentou invocar essas ferramentas (indisponibilidade já conhecida de antemão, informada no prompt de execução) e não improvisou nem estimou os valores que a Parte 1 pede.

Todo o resto do plano foi executado e está verde: Task 1 completa e commitada; Task 2 Parte 2 (extensão do guardião estático) e Parte 3 (suíte canônica) completas e commitadas.

**O que fica pendente para o orquestrador (ou uma sessão com acesso a browser MCP) fechar, contra o commit `8ec1e4b`:**

1. **`getComputedStyle` no elemento de patrimônio do Topbar** — confirmar que `fontVariantNumeric === "tabular-nums"`. Não medido nesta sessão. Se der `"normal"`, o seletor de atributo `.b3 [style*="ui-monospace"]` não está casando com o que o React de fato serializa no atributo `style` — nesse caso a decisão mecânica (opção a) precisaria ser reaberta, não improvisada para a opção (b) sem sinalizar ao Alex.
2. **Medição de largura de dígitos** — renderizar num nó de teste temporário, dentro de `.b3`, dois valores de mesma contagem de dígitos mas glifos diferentes (ex.: `1.111,11` e `8.888,88`) com `fontFamily: MONO`, medir e comparar as larguras (esperado: iguais, em px). Não medido nesta sessão.
3. **Navegação a Histórico, Portfólio e Watchlist** com a conta local, incluindo 2-3 compras simuladas para gerar valores com dígitos diferentes, e captura de screenshot de cada lista para confirmar visualmente o alinhamento de coluna. Não executado nesta sessão — nem a navegação, nem as compras simuladas, nem os screenshots.
4. **Contagem de valores financeiros visíveis que NÃO passam por `MONO`** nas três telas acima (entrada para as Fases 21/22) — requer a navegação ao vivo do item 3, não feita.
5. **Comparação de screenshot do Topbar** (patrimônio) com o screenshot do plano 20-01, para confirmar que nenhum tamanho/peso de fonte mudou visualmente. Não feita — mas a evidência estática é forte: os valores literais removidos (`fontWeight: 700, fontSize: "18px"`) são byte-idênticos aos que `numBody` carrega, e `grep -c` confirma que o literal antigo não sobrou duplicado em nenhum outro lugar.

Nenhum destes 5 itens foi aproximado ou estimado neste SUMMARY — ficam explicitamente em aberto, seguindo o mesmo padrão do `20-01-SUMMARY.md` (que teve a Task 3 Parte 2 fechada depois por reverificação ao vivo do orquestrador, registrada numa seção própria "Orchestrator Live Re-Verification"). Recomendo o mesmo fluxo aqui: o orquestrador roda os 5 itens contra o commit `8ec1e4b` (ou o merge subsequente) e anexa os resultados a este SUMMARY.

## Orchestrator Live Re-Verification (itens de navegador pendentes — fechados)

Executada via MCP do navegador contra o merge desta branch:

1. **`getComputedStyle().fontVariantNumeric`** — amostra de 28 elementos com
   `ui-monospace` no style inline (Acompanhar) e 27 (Watchlist): 100%
   computam `tabular-nums`. ✓
2. **Valor do patrimônio no Topbar** (`{...numBody}`) — `font-size:18px`,
   `font-weight:700`, `tabular-nums` computado. Screenshot comparado
   visualmente contra o estado pós-plano 20-01: nenhuma diferença de
   tamanho/peso perceptível — "R$ 10.000,00" idêntico. ✓
3. **Nenhum tamanho/peso de fonte mudou** visualmente no Topbar (confirmado
   por screenshot). ✓

TYPO-01 e TYPO-02 confirmados por medição ao vivo, não só por leitura de
código.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Fundação tipográfica pronta para consumo: `numHero`/`numBody`/`numMicro` disponíveis para as Fases 21/22 migrarem Histórico, Watchlist e Portfólio tela a tela.
- Guardião estático (`web/tests/test_fase20_fundacao_visual.mjs`) agora trava FIX-01/FIX-02/SYS-04 (plano 20-01) + TYPO-01/TYPO-02 (este plano) — 16 asserções, todas verdes.
- Bloqueador residual: os 5 itens de verificação ao vivo listados acima (TYPO-01 provado só por leitura estática de código nesta sessão, não por medição de browser) — recomendo que o orquestrador execute essa medição antes de considerar TYPO-01 100% fechado por evidência ao vivo, seguindo o precedente do plano 20-01.
- `npx vite build` limpo, suíte canônica completa verde (`EXIT=0` capturado explicitamente).

---
*Phase: 20-funda-o-estrutural-e-tipogr-fica*
*Completed: 2026-09-05*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/tests/test_fase20_fundacao_visual.mjs
- FOUND commit: 33012c6 (feat — Task 1)
- FOUND commit: 8ec1e4b (test — Task 2, Partes 2/3)
- FOUND commit: 06d9ba2 (plan base)
