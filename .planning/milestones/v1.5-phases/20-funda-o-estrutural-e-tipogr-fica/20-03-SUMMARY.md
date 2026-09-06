---
phase: 20-funda-o-estrutural-e-tipogr-fica
plan: 03
subsystem: ui
tags: [react, css, typography, accessibility, prefers-reduced-motion, web]

# Dependency graph
requires:
  - phase: 20-funda-o-estrutural-e-tipogr-fica
    plan: "02"
    provides: "Escala numérica tabular-nums/numHero/numBody/numMicro e guardião web/tests/test_fase20_fundacao_visual.mjs estendido com TYPO-01/TYPO-02"
provides:
  - "Fredoka (fontFamily: DISPLAY) nos 15 <h1> de nível-tela, incluindo os dois branches vivos de EficienciaIAScreen (TYPO-03)"
  - "Gate abrangente @media (prefers-reduced-motion: reduce) em GlobalStyle() cobrindo .b3 (raiz), .b3 *, .b3 *::before/::after, .b3-mode-switch e .b3-mode-switch * (MOTION-03)"
  - "Bloco estreito pré-existente (.b3 .tt-track, .b3 .spin -> animation:none) preservado intacto, evitando o strobe que animation-duration:0.01ms produziria em animação infinite"
  - "Guardião estendido com 6 asserções novas (TYPO-03 + MOTION-03), cobrindo agora os 7 requisitos da fase inteira (FIX-01, FIX-02, SYS-04, TYPO-01, TYPO-02, TYPO-03, MOTION-03)"
affects: [21, 22, 23]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "fontFamily: DISPLAY como chave nova no objeto de style inline já existente do <h1>, sem wrapper/classe/componente novo — mesmo idioma já usado no wordmark do Topbar"
    - "Media query CSS pura para prefers-reduced-motion, sem JS/matchMedia novo para esta camada — o app já tinha um REDUCE_MOTION via matchMedia em JS num ponto isolado (drag-sheet), pré-existente e fora do escopo deste plano"
    - "Comentário de decisão em GlobalStyle() escrito para NÃO repetir o literal do seletor CSS que ele descreve, evitando que a própria prosa corrompa uma checagem de ordem de fonte por indexOf/grep (lição já registrada no 20-02-SUMMARY, reaplicada aqui)"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_fase20_fundacao_visual.mjs

key-decisions:
  - "Seguida a correção mecânica travada no próprio plano: o CONTEXT pedia '.b3 *, .b3 *::before, .b3 *::after' mas isso não casa com o próprio '.b3' (onde a transição de tema mora) — a lista de seletores do bloco novo inclui '.b3' e '.b3-mode-switch'/'.b3-mode-switch *' explicitamente, ampliando a cobertura sem reduzir nada do texto original."
  - "Bloco estreito de animation:none (ticker + spinner) mantido intacto e não mesclado ao bloco amplo — animation-duration:0.01ms não para animação infinite, produziria strobe (o oposto do que MOTION-03 existe para evitar); a regra estreita vence por especificidade, mas o posicionamento de fonte (depois das duas regras de transition, antes do bloco estreito) segue prescrito e verificado."
  - "Guardião trava TYPO-03 por IGUALDADE de contagem entre total de <h1> e total de <h1> com fontFamily: DISPLAY, não por número fixo — pensado para pegar um H1 novo de fase futura que chegue sem a fonte da marca (T-20-09 do threat model)."

requirements-completed: [TYPO-03, MOTION-03]

# Metrics
duration: ~55min
completed: 2026-09-05
---

# Phase 20 Plan 03: Fredoka nos títulos de tela + gate de movimento reduzido Summary

**Os 15 `<h1>` de nível-tela (incluindo os dois branches de `EficienciaIAScreen`) passam a usar a fonte da marca (Fredoka) e `GlobalStyle()` ganha um gate `@media (prefers-reduced-motion: reduce)` abrangente que zera a transição de tema/modo na raiz e na troca de modo, preservando intacta a trava específica que impede o marquee do ticker e o spinner de entrarem em strobe.**

## Performance

- **Duration:** ~55 min
- **Completed:** 2026-09-05
- **Tasks:** 3 (Task 1 e Task 2 completas; Task 3 completa exceto a verificação ao vivo por browser — ver "Issues Encountered")
- **Files modified:** 2 (`web/src/App.jsx`, `web/tests/test_fase20_fundacao_visual.mjs`)

## Accomplishments
- TYPO-03: `fontFamily: DISPLAY` acrescentado como chave nova em cada um dos 15 `<h1>` de tela (confirmado por `grep -c '<h1'` == `grep -c 'fontFamily: DISPLAY'` == 15), sem alterar nenhuma chave existente (`margin`, `fontSize`, `fontWeight`, `letterSpacing`) — os dois branches vivos de `EficienciaIAScreen` (deslogado e logado) receberam a mudança.
- MOTION-03: novo bloco `@media (prefers-reduced-motion: reduce)` em `GlobalStyle()` cobrindo `.b3` (elemento raiz — correção mecânica sobre o texto literal do CONTEXT, que só cobria descendentes), `.b3 *`, `.b3 *::before/::after`, `.b3-mode-switch` e `.b3-mode-switch *`; posicionado depois das regras de `transition` das linhas 306/337 (empate de especificidade resolvido por ordem de fonte) e antes do bloco estreito existente, que continua intacto.
- Guardião estático estendido com 6 asserções novas (1 para TYPO-03 travando por igualdade de contagem; 5 para MOTION-03 travando os dois blocos, os seletores do bloco amplo, a preservação do bloco estreito e a ordem de fonte); sensibilidade confirmada manualmente (removendo `fontFamily: DISPLAY` de um `<h1>` o teste falha 14/15; restaurado, diff limpo).
- Suíte canônica completa verde: `bash scripts/executar.sh --testes` saiu com `EXIT=0` (2021 pytest passed + 1 skipped; todos os 116 testes `.mjs`, incluindo o guardião estendido, `[OK]`).
- `cd web && npx vite build` saiu com código 0 em todas as três verificações (após Task 1, após Task 2, após a correção do comentário).

## Task Commits

1. **Task 1: Fredoka nos 15 H1 de tela** — `140a011` (feat)
2. **Task 2: Gate de prefers-reduced-motion abrangente em GlobalStyle()** — `e72faa2` (feat)
3. **Correção do próprio Task 2 (comentário continha literal do seletor CSS)** — `deacef6` (fix) — ver "Deviations from Plan"
4. **Task 3 (guardião estendido + suíte canônica; sem a Parte 1 de verificação ao vivo)** — `0d817d1` (test)

**Base do plano:** `d6772c4` (docs: update tracking after wave 2, plano 20-02)

## Files Created/Modified
- `web/src/App.jsx` — `fontFamily: DISPLAY` acrescentado aos 15 `<h1>` de `EvolucaoScreen`, `AjudaScreen`, `MercadoScreen`, `CarteiraScreen`, `HistoricoScreen`, `AgenteScreen`, `AiConfigScreen`, `NotificacoesScreen`, `AtividadeIAScreen`, `EficienciaIAScreen` (dois branches), `LogsDebugScreen`, `FonteDadosScreen`, `RadarScreen` e `ConfigScreen`; novo bloco `@media (prefers-reduced-motion: reduce)` em `GlobalStyle()` com comentário de 3 razões, posicionado antes do bloco estreito existente.
- `web/tests/test_fase20_fundacao_visual.mjs` — 6 asserções novas (TYPO-03: igualdade de contagem `<h1>`/`<h1>` com `fontFamily: DISPLAY`, ≥15; MOTION-03: contagem de dois blocos `prefers-reduced-motion`, seletores `.b3`/`.b3-mode-switch` no bloco amplo, preservação do bloco estreito, ordem de fonte via `indexOf`).

## Decisions Made
- Seguida a correção mecânica travada em `<decisao_do_planner>` do próprio plano: a lista de seletores do bloco amplo inclui `.b3` e `.b3-mode-switch`/`.b3-mode-switch *` além de `.b3 *`/`.b3 *::before`/`.b3 *::after`, porque `.b3 *` sozinho nunca casaria com o próprio elemento `.b3` onde a transição de tema mora — texto literal do CONTEXT corrigido, intenção preservada.
- Bloco estreito de `animation:none` (ticker + spinner) mantido intacto, não mesclado ao bloco amplo: `animation-duration: 0.01ms` não para uma animação `infinite`, produz um ciclo completo a cada 0,01ms para sempre (strobe) — o oposto do que a preferência de movimento reduzido existe para evitar (T-20-07 do threat model). A regra estreita vence por especificidade `(0,2,0)` contra `(0,1,0)` do bloco amplo, independentemente de ordem — mas o posicionamento de fonte prescrito (depois das regras de `transition`, antes do bloco estreito) foi mantido e é verificado pelo guardião.
- Guardião trava TYPO-03 por igualdade de contagem (não por número fixo de 15), para que um `<h1>` novo introduzido por fase futura sem `fontFamily: DISPLAY` quebre o teste em vez de passar silenciosamente (T-20-09 do threat model).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comentário do bloco de MOTION-03 continha literal do seletor CSS que ele descrevia**
- **Found during:** Preparação da Task 3 (escrita das asserções de ordem de fonte do guardião), antes de qualquer commit da Task 3
- **Issue:** O item 3 do comentário explicativo acrescentado na Task 2 continha, em prosa, a substring literal `.b3 .tt-track,.b3 .spin{ animation:none }` — como o guardião só remove comentários de linha (`//...`), não comentários de bloco (`/* ... */`), essa substring aparecia no texto do arquivo ANTES da regra CSS real (que fica mais abaixo). Qualquer verificação por `indexOf`/regex sobre a ordem de fonte das regras (exatamente o que a Task 3 precisa fazer para MOTION-03) encontraria a ocorrência na prosa primeiro, corrompendo a checagem — mesma classe de bug já documentada como deviation no `20-02-SUMMARY.md` (deviation #1: um comentário continha `fontFamily: MONO` e inflava a contagem do critério de aceite de TYPO-01).
- **Fix:** Reescrito o item 3 do comentário para descrever a decisão ("zera para 'none' as duas animações infinitas") sem repetir o seletor CSS literal, preservando o sentido.
- **Files modified:** `web/src/App.jsx`
- **Verification:** `grep -n 'animation:none' web/src/App.jsx` passou a mostrar só a linha da regra real (antes mostrava duas ocorrências, uma no comentário); `npx vite build` ok; a asserção de ordem de fonte do guardião (Task 3) passou a usar `indexOf` sobre um texto sem esse ruído.
- **Committed in:** `deacef6` (fix — commit separado, não amend do commit da Task 2, por proibição do protocolo de execução)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug autodetectado no próprio comentário de documentação desta sessão, sem impacto funcional em produção; a regra CSS em si sempre esteve correta, só a prosa acima dela continha o ruído).
**Impact on plan:** Nenhum scope creep — correção editorial dentro do mesmo arquivo, necessária para a checagem de ordem de fonte do próprio guardião que a Task 3 do plano exige.

### Notas sobre divergência entre texto do plano e estado verificado (não são deviations)

Dois números citados no texto das `<acceptance_criteria>` do plano não batem com o estado real do arquivo — em ambos os casos, verificado via `git show HEAD:web/src/App.jsx` (estado ANTES de qualquer edição desta sessão) que a divergência já existia antes deste plano tocar o arquivo, não foi introduzida pelas Tasks 1/2:

1. **Task 1, critério "grep ... fontSize: \"22px\" continua 11"**: a contagem real, antes e depois da Task 1, é **12** — e a própria tabela de inventário do plano (`<interfaces>`) lista 12 linhas com `22px` (itens 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15), não 11. O número "11" na prosa do critério de aceite conflita com a própria tabela do plano; a tabela e o grep concordam entre si. Nenhum tamanho de H1 mudou (invariante real do plano) — confirmado.
2. **Task 2, critério "grep -c 'prefers-reduced-motion' retorna 2"**: a contagem real após a Task 2 é **3**, porque o arquivo já tinha, antes deste plano, uma constante JS `REDUCE_MOTION` (linha ~1400) usada em um único ponto isolado (transição de um drag-sheet) via `window.matchMedia("(prefers-reduced-motion: reduce)")` — mecanismo pré-existente, fora do escopo declarado deste plano (que só toca `GlobalStyle()`). O critério de aceite do plano contava só ocorrências de CSS, sem prever essa menção em JS. Os dois blocos CSS (existente + novo) estão corretos e na posição certa; a terceira ocorrência é o `matchMedia` pré-existente.

Nenhum destes dois pontos bloqueou tarefa ou exigiu fix — são esclarecimentos para quem reexecutar os mesmos comandos de grep do plano e encontrar um número diferente do texto.

## Issues Encountered

**Task 3 Parte 1 (verificação ao vivo por browser) NÃO foi executada por este subagent.** Confirmado empiricamente no início desta sessão e informado de antemão no prompt de execução: subagentes spawnados via Task não herdam ferramentas MCP de navegador do orquestrador (`mcp__computer-use__*`, `mcp__claude-in-chrome__*` — bug upstream anthropics/claude-code#13898), mesma limitação já documentada em `20-01-SUMMARY.md` e `20-02-SUMMARY.md`. Este subagent não tentou invocar essas ferramentas nem improvisou/estimou os valores que a Parte 1 pede.

Todo o resto do plano foi executado e está verde: Task 1 completa e commitada; Task 2 completa e commitada (com uma correção própria, ver "Deviations from Plan"); Task 3 Parte 2 (extensão do guardião estático) e Parte 3 (suíte canônica) completas e commitadas.

**O que fica pendente para o orquestrador (ou uma sessão com acesso a browser MCP) fechar, contra o commit `0d817d1`, mapeado 1:1 aos critérios de aceite da Task 3:**

1. **`getComputedStyle(document.querySelector('h1')).fontFamily`** em pelo menos 5 telas distintas dentre as 5 abas da barra inferior + Histórico + Preferências (ex.: Acompanhar, Watchlist, Portfólio, Operador IA, Preferências) — esperado começar por `Fredoka` em todas. Não medido nesta sessão.
2. **`document.fonts.check('600 22px Fredoka')`** — confirmar que a Fredoka de fato CARREGOU (não só foi pedida na cascata); se retornar `false`, o título cai visualmente no Nunito e o resultado é indistinguível do estado anterior (T-20-08 do threat model). Não medido nesta sessão.
3. **Screenshot de 3 telas** com H1, para descrever se o título parece a mesma família do wordmark "Boris+" do Topbar. Não capturado nesta sessão.
4. **`getComputedStyle(document.querySelector('.b3-shell')).transitionDuration`** com `prefers-reduced-motion: reduce` emulado — esperado ≈ `0.01ms`. Não medido nesta sessão.
5. **Troca de tema/modo em Preferências, sob a emulação** — confirmar que a mudança de cor é instantânea, sem fade. Não exercitado nesta sessão.
6. **`getComputedStyle(el).animationName`** do elemento `.spin` (spinner) e do `.tt-track` (marquee do ticker), sob a emulação — esperado `"none"` para os dois. Não medido nesta sessão.
7. **Dois screenshots com ~1s de intervalo** do ticker sob a emulação, para confirmar visualmente que está PARADO (mesma posição) e não em flicker acelerado/strobe — este é o teste que separa a implementação certa da armadilha do `0.01ms` em animação infinita (T-20-07 do threat model, a razão de existir do bloco estreito preservado). Não capturado nesta sessão.
8. **Desligar a emulação e confirmar que o ticker volta a andar** — o gate não pode quebrar o comportamento padrão. Não exercitado nesta sessão.

Nenhum destes 8 itens foi aproximado ou estimado neste SUMMARY — ficam explicitamente em aberto, seguindo o mesmo padrão de `20-01-SUMMARY.md`/`20-02-SUMMARY.md` (que tiveram itens de browser fechados depois por reverificação ao vivo do orquestrador, registrada em seção própria "Orchestrator Live Re-Verification"). Recomendo o mesmo fluxo aqui: o orquestrador roda os 8 itens contra o commit `0d817d1` (ou o merge subsequente) e anexa os resultados a este SUMMARY.

## Orchestrator Live Re-Verification

Executada via MCP do navegador contra o merge desta branch:

1. **`document.fonts.check("600 22px Fredoka")` → `true`** — fonte carregada. ✓
2. **`getComputedStyle(h1).fontFamily` em 5 telas** (Acompanhar, Radar,
   Watchlist, Portfólio, Operador IA) — todas retornam `Fredoka` como
   primeira família. ✓ (inventário completo de 15 confere com a suíte
   estática do guardião, que cobre as 10 restantes por leitura de fonte.)
3. **Regra CSS servida de fato** (lida do `<style>` renderizado no DOM, não
   do código-fonte) — a regra ampla nova aparece byte a byte:
   `.b3, .b3 *, .b3 *::before, .b3 *::after, .b3-mode-switch, .b3-mode-switch *{ transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; }`
   — cobre o elemento raiz `.b3` (não só descendentes), inclui
   `animation-iteration-count:1` (mitigação do risco de estroboscópio) e
   aparece ANTES da regra estreita pré-existente
   `.b3 .tt-track,.b3 .spin{animation:none!important}` na ordem de fonte —
   consistente com a análise de especificidade do plano. ✓
4. **Estado normal (sem `prefers-reduced-motion`)** — ticker anima
   normalmente (`animationName:"b3tt"`, `animationDuration:"52s"`), shell
   com `transitionProperty:"background, color"` ativo: nada quebrou no
   caminho comum. ✓

**Limitação de ambiente, registrada sem contornar:** nenhuma ferramenta
disponível nesta sessão expõe emulação de `prefers-reduced-motion` via CDP
(`Emulation.setEmulatedMedia`) — `resize_window` só emula viewport/color-scheme,
e o plugin `chrome-devtools` disponível também não expõe esse parâmetro.
Não é possível, portanto, alternar o media feature e observar o efeito
comportamental ao vivo (`animationName==="none"` sob redução, comparação de
dois screenshots do ticker parado) sem mudar a configuração de acessibilidade
real do sistema operacional do host — o que não é apropriado fazer só para
este teste. A verificação acima (regra CSS servida, byte-idêntica ao
planejado, com escopo e mitigação de estroboscópio corretos) é a evidência
disponível nas ferramentas deste ambiente; o comportamento sob o media
feature ativo fica coberto pelo guardião estático (que trava a string da
regra) e pela leitura de código já feita nos Planos 20-03, não por medição
comportamental ao vivo. Registrado como lacuna de ferramenta, não como "não
verificado por descuido".

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Fundação tipográfica e de movimento pronta: os 7 requisitos da fase (FIX-01, FIX-02, SYS-04, TYPO-01, TYPO-02, TYPO-03, MOTION-03) estão implementados e travados pelo guardião estático (`web/tests/test_fase20_fundacao_visual.mjs`, 22 asserções, todas verdes).
- Fase 23 (motion com propósito) pode depender do gate de `prefers-reduced-motion` desta fase existir — ele existe, cobre a raiz (`.b3`) e a troca de modo (`.b3-mode-switch`), e qualquer transição/animação nova que a Fase 23 adicionar em `.b3`/descendentes já nasce coberta, sem código extra.
- Bloqueador residual: os 8 itens de verificação ao vivo listados acima (TYPO-03 e MOTION-03 provados só por leitura estática de código e pela suíte automatizada nesta sessão, não por medição de browser) — recomendo que o orquestrador execute essa medição antes de considerar a Fase 20 100% fechada por evidência ao vivo, seguindo o precedente dos planos 20-01 e 20-02.
- `npx vite build` limpo, suíte canônica completa verde (`EXIT=0` capturado explicitamente: 2021 pytest passed + 1 skipped, todos os `.mjs` `[OK]`).
- Nota operacional para o orquestrador: `web/node_modules` estava ausente neste worktree (git worktrees não compartilham `node_modules`, gitignored) — resolvido com o mesmo symlink já usado nos planos 20-01/20-02, apontando para `node_modules` do repo principal (mesmo `package.json`/`package-lock.json`, diff vazio confirmado). O symlink em si não foi commitado (aparece como untracked em `git status`, por ser link e não diretório — o padrão `node_modules/` do `.gitignore` só casa com diretórios).

---
*Phase: 20-funda-o-estrutural-e-tipogr-fica*
*Completed: 2026-09-05*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/tests/test_fase20_fundacao_visual.mjs
- FOUND: .planning/phases/20-funda-o-estrutural-e-tipogr-fica/20-03-SUMMARY.md
- FOUND commit: 140a011 (feat — Task 1)
- FOUND commit: e72faa2 (feat — Task 2)
- FOUND commit: deacef6 (fix — correção do comentário da Task 2)
- FOUND commit: 0d817d1 (test — Task 3, guardião + suíte canônica)
- FOUND commit: d6772c4 (plan base)
