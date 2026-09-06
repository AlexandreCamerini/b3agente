---
phase: 22-componentes-compartilhados-trilho-cones-mascote
plan: 02
subsystem: ui
tags: [react, jsx, svg, accessibility, guardian-test]

# Dependency graph
requires:
  - phase: 22-componentes-compartilhados-trilho-cones-mascote
    provides: "Plano 22-01 (SYS-01, trilho horizontal único) e o guardião único da Fase 22 (test_fase22_componentes_compartilhados.mjs) que este plano estende com a Seção B"
provides:
  - "NavIcon generalizado (size/color, fallback active?T.accent:T.textMuted preservado) servindo tanto o BottomNav quanto ícones inline fora da barra de navegação"
  - "Três geometrias novas no registro do NavIcon: graduacao, brilho, checado"
  - "8 sites de emoji do Perfil/Watchlist/Posições/config trocados por SVG (ou deletados, nos 2 <option> onde SVG é estruturalmente impossível)"
  - "Seção B do guardião da Fase 22 (test_fase22_componentes_compartilhados.mjs), cobrindo a assinatura do NavIcon, os 3 ids novos, zero emoji desta onda, e os rótulos visíveis preservados"
  - "2 guardiões pré-existentes (test_copy_theme.mjs, test_carteira_lastro_ui.mjs) atualizados com nota datada, sem perder a intenção original"
affects: [22-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "NavIcon com fallback de cor (`color || (active ? T.accent : T.textMuted)`) — quem chama de dentro do BottomNav não muda; quem chama de fora passa `size` e `color=\"currentColor\"` para herdar a cor do texto ao lado"
    - "Alinhamento resolvido dentro do componente (`verticalAlign: \"-0.15em\", flexShrink: 0` no <svg>), não repetido em cada um dos 8 call sites"
    - "Reuso de geometria existente (`evolucao`) para os 5 sites de 📈 em vez de desenhar um ícone de gráfico novo — zero duplicação de traço"
    - "Guardião estático estendido por seção, não substituído: Seção A (22-01) intocada, Seção B (este plano) acrescentada ao mesmo arquivo"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_fase22_componentes_compartilhados.mjs
    - web/tests/test_copy_theme.mjs
    - web/tests/test_carteira_lastro_ui.mjs

key-decisions:
  - "Generalização do NavIcon em vez de componente irmão — decisão do 22-02-PLAN.md, retrocompatível (BottomNav não muda), evita duplicar geometria com o plano 22-03 (📡 do Radar reusa o id radar já existente)"
  - "Cinco sites de 📈 reusam o id evolucao já existente — zero geometria de gráfico nova, decisão do planner levada ao limite do 22-UI-SPEC.md (\"reuse one icon id\")"
  - "Cor por currentColor no call site, nunca token novo — cada um dos 8 sites já vive dentro de um elemento que define color; o ícone herda o branch certo (ativo/inativo, dois temas) sem risco de divergir do texto"
  - "<option> não recebe ícone (estruturalmente impossível) — deleção pura do emoji, texto puro sobrevive, decisão já travada no 22-UI-SPEC.md antes deste plano"

patterns-established:
  - "Comentário datado sobre asserção reescrita em guardião: nomeia a fase/requirement/data, descreve o que mudou e reafirma a intenção original que continua travada — nunca substitui a asserção por algo mais fraco"
  - "Checagem de texto fixo em guardião deve ignorar comentários JSX ({/* ... */}) quando o texto de busca é curto o bastante para colidir com prosa explicativa histórica em comentário — ver Deviations"

requirements-completed: [SYS-02]

# Metrics
duration: 12min (commit-a-commit, 00:18:39 → 00:30:17 -03:00)
completed: 2026-09-06
---

# Phase 22 Plan 02: Ícones SVG no lugar de emoji (SYS-02) Summary

**8 sites de emoji (Perfil, Watchlist, Posições, config) trocados por SVG do registro generalizado do `NavIcon` — três geometrias novas (`graduacao`/`brilho`/`checado`), cinco sites reusando `evolucao`, e os 2 `<option>` estruturalmente incapazes de SVG resolvidos por deleção pura do glifo.**

## Performance

- **Duration:** ~12 min commit-a-commit (00:18:39 → 00:30:17, -03:00); tempo de sessão maior — inclui carregamento de 8 arquivos de contexto e leitura ao vivo do App.jsx antes da Task 1
- **Started:** 2026-09-06T00:18:39-03:00
- **Completed:** 2026-09-06T00:30:17-03:00
- **Tasks:** 3 completed
- **Files modified:** 4 (`web/src/App.jsx`, `web/tests/test_fase22_componentes_compartilhados.mjs`, `web/tests/test_copy_theme.mjs`, `web/tests/test_carteira_lastro_ui.mjs`)

## Accomplishments

- `NavIcon` (único fabricante de ícone SVG do app, antes exclusivo do `BottomNav`) generaliza para `size`/`color`, preservando o caminho antigo (`active ? T.accent : T.textMuted`) usado pelo `BottomNav` — retrocompatível, zero mudança visual na barra de navegação.
- Três geometrias novas no mesmo traço/peso do resto (`graduacao`, `brilho`, `checado`); os cinco sites de 📈 reusam a geometria `evolucao` já existente — zero ícone de gráfico duplicado.
- Os 8 sites de emoji desta onda (seletor de Modo no Perfil, fallback do sparkline e chips de ação da Watchlist, botão de Stop/alvo em Posições, aviso de chave configurada, e os 2 `<option>` do select de skill) saíram de `App.jsx` sem perder nenhum rótulo visível nem alterar nenhum `aria-label` (34 antes, 34 depois).
- Guardião da Fase 22 ganhou a Seção B (11 grupos de asserção cobrindo assinatura do `NavIcon`, os 3 ids novos, zero emoji, rótulos preservados e ausência de dependência de ícone), confirmada RED antes da mudança e GREEN depois.
- Os 2 guardiões que travavam o emoji como literal (`test_copy_theme.mjs` qa/34, `test_carteira_lastro_ui.mjs` guardrail de stop/alvo) foram atualizados com nota datada, preservando a intenção original de cada um — nenhuma asserção apagada ou afrouxada.

## Task Commits

Executado como plano `tdd="true"` na Task 1 (RED) e Task 2 (GREEN), com Task 3 de reparo dos guardiões dependentes:

1. **Task 1: Guardião da Fase 22, Seção B (SYS-02, onda 2), escrito antes da mudança (RED)** - `6507089` (test)
2. **Task 2: NavIcon generalizado com três geometrias novas, e os 8 sites trocados (GREEN)** - `82d49d0` (feat)
3. **Task 3: Atualizar com nota os dois guardiões que travavam o emoji como literal** - `4a4cd85` (fix)

**Plan metadata:** commit desta entrega (SUMMARY.md) segue nesta mesma sessão.

## Files Created/Modified

- `web/src/App.jsx` - `NavIcon` generalizado (size/color/fallback), 3 geometrias novas (`graduacao`/`brilho`/`checado`), 8 sites de emoji trocados por `<NavIcon>` ou deletados nos 2 `<option>`
- `web/tests/test_fase22_componentes_compartilhados.mjs` - Seção B (SYS-02) acrescentada: 11 grupos de asserção sobre a generalização do `NavIcon`, os 3 ids novos, zero emoji desta onda, rótulos preservados, e zero dependência de ícone nova
- `web/tests/test_copy_theme.mjs` - asserção qa/34 reescrita para não depender do glifo `✨`, com nota datada; intenção original (chave `btnAnalise` ligada) preservada e reforçada com verificação do novo marcador visual (`id="brilho"`)
- `web/tests/test_carteira_lastro_ui.mjs` - asserção do guardrail "stop/alvo nunca é vetado" reescrita para não depender do glifo `📈`, com nota datada; `✎ Editar stop/alvo` (fora de escopo) intocado

## Decisions Made

Ver `key-decisions` no frontmatter. Nenhuma decisão foi tomada fora do que já
estava travado em `22-CONTEXT.md`/`22-UI-SPEC.md` — este plano seguiu a
generalização do `NavIcon` (em vez de componente irmão), o reuso do id
`evolucao` para os 5 sites de gráfico, e a resolução por deleção pura para os
2 `<option>`, todas já decididas antes da execução.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comentário datado do plano continha o glifo literal que o próprio Task 3 exigia ausente**
- **Found during:** Task 3 (atualização dos dois guardiões)
- **Issue:** O texto de comentário sugerido literalmente pelo `22-02-PLAN.md`
  para as duas notas datadas citava os emojis por escrito
  ("o [emoji de gráfico] do botão de Stop/alvo virou...", "o [emoji de
  fagulha] virou...") — mas os critérios de aceite da própria Task 3 exigem
  `grep -c` desses emojis retornando `0` nos dois arquivos de teste. Copiar o
  comentário verbatim quebraria o próprio critério que a task define.
- **Fix:** Reescritos os dois comentários para descrever o emoji em palavras
  ("o emoji de gráfico", "o emoji de fagulha") em vez de citar o glifo — a
  explicação histórica sobrevive, o glifo não aparece fora da asserção que
  precisa dele (a linha `app.includes("✎ Editar stop/alvo")`, que continua
  com o glifo `✎` porque é o que a asserção precisa verificar em `App.jsx`).
- **Files modified:** `web/tests/test_copy_theme.mjs`, `web/tests/test_carteira_lastro_ui.mjs`
- **Verification:** `grep -c "📈" web/tests/test_carteira_lastro_ui.mjs` e `grep -c "✨" web/tests/test_copy_theme.mjs` retornam `0`; ambos os arquivos continuam saindo com código 0.
- **Committed in:** `4a4cd85` (Task 3 commit — o comentário nunca chegou a ser commitado na forma incorreta)

**2. [Rule 1 - Bug] A checagem literal de "Analisar com IA" (sugerida pelo plano) colidia com um comentário histórico pré-existente em App.jsx**
- **Found during:** Task 3 (reescrita da asserção qa/34)
- **Issue:** A condição sugerida pelo plano,
  `!app.includes("Analisar com IA")`, é mais ampla que a original
  (`!app.includes('"✨ Analisar com IA"')`, que incluía o glifo e as aspas).
  `App.jsx` já tem, desde a Fase 8B, um comentário JSX
  (`{/* qa/34: chave órfã btnAnalise finalmente ligada — ... (antes:
  "Analisar com IA" fixo). */}`) que cita essa frase em prosa, entre aspas,
  para explicar a história da chave — sem relação com o texto voltar a ser
  hardcoded no JSX de verdade. A condição ampla do plano, rodada contra
  `App.jsx` inteiro, encontrava essa citação histórica e falhava mesmo com o
  `App.jsx` correto (comprovado ao rodar o teste após a Task 2: falhou
  exatamente nesta asserção).
- **Fix:** A checagem passou a rodar sobre uma cópia de `App.jsx` com os
  comentários JSX (`{/* ... */}`) removidos
  (`app.replace(/\{\/\*[\s\S]*?\*\/\}/g, "")`), preservando a intenção
  original (nenhum texto fixo "Analisar com IA" voltou a existir como string
  viva no JSX) sem reescrever nem apagar o comentário histórico de `App.jsx`
  (guardrail "Histórico não se reescreve", CLAUDE.md).
- **Files modified:** `web/tests/test_copy_theme.mjs`
- **Verification:** `node web/tests/test_copy_theme.mjs` sai com código 0 (antes do fix, falhava especificamente nesta asserção, confirmado por execução isolada).
- **Committed in:** `4a4cd85` (Task 3 commit — a versão com falso positivo nunca foi commitada)

---

**Total deviations:** 2 auto-fixed (2 bugs, Rule 1) — ambos descobertos e corrigidos dentro da própria Task 3, antes do commit.
**Impact on plan:** Nenhum no escopo entregue. Os dois desvios foram no texto/lógica de comentário e asserção de teste, não no comportamento de produto; a intenção de cada guardião (documentada no `22-02-PLAN.md`) foi preservada e verificada empiricamente (RED→GREEN em cada caso).

## Issues Encountered

- `npx vite build` isolado falhou com `EPERM`/`ERR_MODULE_NOT_FOUND` (cache
  do npm com dono root + `web/node_modules` ausente no worktree novo) — o
  mesmo padrão documentado no `22-01-SUMMARY.md`. Resolvido rodando a suíte
  canônica completa (`bash scripts/executar.sh --testes`, sem sandbox
  restrito), que detecta a ausência de `node_modules` e resolve sozinha
  antes de rodar os testes web — nenhuma ação manual além de desabilitar o
  sandbox para este comando específico.
- Um dos critérios de aceite literais da Task 2 (`grep -c 'width={size}'
  web/src/App.jsx` deveria retornar `1`) assumia que `NavIcon` seria o único
  componente do arquivo com essa assinatura de props — na prática já
  existiam 2 outros componentes pré-existentes e sem relação
  (`LogoMark` em ~L208, um `TierDot`-like em ~L6593) que também recebem uma
  prop chamada `size` e a repassam como `width={size} height={size}`,
  levando a contagem real para `3`. Isso não é um regressão desta task — os
  dois componentes já existiam antes da Fase 22 — e a asserção REAL do
  guardião (Seção B) isola o corpo do `NavIcon` por nome de função antes de
  checar `width={size}`, então não é afetada pela coincidência de padrão.
  Documentado aqui em vez de alterar o critério do plano, para não mascarar
  a diferença entre "o que o plano previu" e "o que o código já tinha".

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- SYS-02 está satisfeito no código e travado por guardião: os 8 sites de
  emoji desta onda saíram de `App.jsx`, `NavIcon` está generalizado e pronto
  para o plano 22-03 reusar (o 📡 do Radar pode reusar o id `radar` já
  existente, ou ganhar um id próprio no mesmo registro).
- `test_fase22_componentes_compartilhados.mjs` tem as Seções A (SYS-01) e B
  (SYS-02, ondas Perfil/Watchlist/Posições/config) completas e verdes; a
  Seção C (SYS-02, Radar + tier dot + varredura de emoji zero) e a Seção D
  (SYS-03, sombra do PetFab) seguem reservadas para o plano 22-03 no MESMO
  arquivo.
- `grep -noP "[\x{1F300}-\x{1FAFF}]" web/src/App.jsx` ainda mostra 🟢/🟡/🔴
  (tier dot, fora de escopo desta onda, aprovado como exceção no
  `22-UI-SPEC.md`) e 📡 (Radar, plano 22-03) — nenhum deles pertence a esta
  onda.
- Nenhum `git push` para `origin` foi executado nesta sessão (execução em
  worktree isolado); publicação do front fica para quando a Fase 22 inteira
  fechar, seguindo a regra já registrada em `PROJECT.md`
  ("Fase sem plano de publicação front").

---
*Phase: 22-componentes-compartilhados-trilho-cones-mascote*
*Completed: 2026-09-06*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/tests/test_fase22_componentes_compartilhados.mjs
- FOUND: web/tests/test_copy_theme.mjs
- FOUND: web/tests/test_carteira_lastro_ui.mjs
- FOUND: .planning/phases/22-componentes-compartilhados-trilho-cones-mascote/22-02-SUMMARY.md
- FOUND: commit 6507089 (Task 1)
- FOUND: commit 82d49d0 (Task 2)
- FOUND: commit 4a4cd85 (Task 3)
- FOUND: commit 1890c15 (SUMMARY.md)
