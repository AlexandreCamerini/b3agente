---
phase: 22-componentes-compartilhados-trilho-cones-mascote
plan: 04
subsystem: ui
tags: [publish, build-stamp, vite, guardian-test, handoff]

# Dependency graph
requires:
  - phase: 22-componentes-compartilhados-trilho-cones-mascote
    provides: "Planos 22-01/02/03 (SYS-01/02/03 implementados e travados por guardião estático); SYS-03 explicitamente não fechado ao final do 22-03, calibragem visual pendente para este plano"
provides:
  - "Fase 22 publicada: carimbo F10-20260906-01 coerente em web/src/version.js, server/app/main.py:SERVER_BUILD_ID e server/web_dist"
  - "Prova por grep no bundle de produção: seis assinaturas de presença + nove glifos ausentes (a checagem de remoção, mais valiosa que a de adição)"
  - "Descoberta documentada: a assinatura prevista '--shadow-fab' nunca existe como texto literal em NENHUM build (dev ou prod) — é computada em runtime por VARKEY(), mesmo mecanismo do --scrim pré-existente; prova alternativa válida usada (shadowFab + os dois valores rgba literais)"
  - "Servidor de produção local (:8787) no ar, carimbo confirmado por curl, para o orquestrador remedir os 3 critérios do ROADMAP contra o bundle minificado"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - web/src/version.js
    - server/app/main.py
    - server/web_dist

key-decisions:
  - "Assinatura de verificação '--shadow-fab' do plano (seção <assinaturas_no_bundle>) é factualmente incorreta para este mecanismo de tema — CSS custom property names são gerados em runtime por VARKEY() (App.jsx:113), nunca escritos como string literal no código-fonte; usada prova alternativa (property key 'shadowFab' + os dois valores rgba do tema) para a mesma finalidade de aceite. Documentado, não corrigido no plano (histórico não se reescreve)."
  - "Task 2 executada sem ferramenta de navegador (limitação conhecida, ambiente informado antecipadamente) — parte automatizável completa (build, publish, grep, servidor no ar, curl confirmando carimbo); remedição visual dos 3 critérios entregue ao orquestrador como roteiro, seguindo o padrão de handoff de 21-04-SUMMARY.md."
  - "SYS-03 mantido como ABERTO nesta entrega (não fechado), apesar da 22-03-SUMMARY.md já registrar confirmação visual do orquestrador contra o DEV SERVER em ambos os temas — esta fase exige explicitamente a medição contra o BUNDLE DE PRODUÇÃO minificado (:8787), que ainda não foi feita ao vivo. Ver seção dedicada abaixo."

patterns-established: []

requirements-completed: []

# Metrics
duration: ~35min (Task 1 completa; Task 2 automatizável completa + handoff)
completed: 2026-09-06
---

# Phase 22 Plan 04: Publicação da Fase 22 + handoff de remedição em produção Summary

**BUILD_ID F10-20260905-03 → F10-20260906-01; `server/web_dist` republicado com o bundle da Fase 22 (trilho único, ícones SVG, sombra do PetFab por tema) comprovado por grep — inclusive a ausência dos nove emojis removidos; suíte canônica verde depois da publicação; servidor de produção local deixado no ar em `:8787` para o orquestrador remedir os 3 critérios do ROADMAP e fechar (ou não) SYS-03 contra o bundle minificado, já que este subagente não tem ferramenta de navegador.**

## Performance

- **Duration:** ~35 min (Task 1 ponta a ponta; Task 2 até o handoff)
- **Started:** 2026-09-06T02:xx (aproximado, após reset do worktree para `853ce477`)
- **Completed:** 2026-09-06T06:06 (servidor `--prod` confirmado no ar)
- **Tasks:** 2 (Task 1 completa; Task 2 automatizável completa, remedição visual entregue ao orquestrador)
- **Files modified:** 3 grupos (`web/src/version.js`, `server/app/main.py`, `server/web_dist` — 25 arquivos dentro do bundle)

## Accomplishments

- `BUILD_ID` avançado para `F10-20260906-01` via `bash scripts/bump.sh` (sem argumento — vigente era `F10-20260905-03`, dia virou).
- `bash scripts/publicar-web.sh` buildou e publicou `server/web_dist`; `SERVER_BUILD_ID` sincronizado automaticamente (nunca editado à mão).
- Suíte canônica verde DEPOIS da publicação: pytest `2021 passed, 1 skipped`; 117 arquivos `web/tests/*.mjs` todos `[OK]` (a primeira tentativa mostrou 116 falsos-`[X]` por `mktemp -d` falhar dentro do sandbox padrão — mesmo padrão documentado em `21-04-SUMMARY.md`; rerodado com `dangerouslyDisableSandbox` e confirmado `EXIT:0` isolado).
- Os três elos do carimbo batem: `web/src/version.js` = `server/app/main.py:SERVER_BUILD_ID` = `F10-20260906-01`, presente em `server/web_dist/assets/index-Btka_lGt.js`.
- Cinco das seis assinaturas de presença confirmadas por `grep -rlI` em `server/web_dist`: `x proximity`, `#f59e0b`, `Varredura automática de hoje`, `Stop/alvo (IA)`, `chave configurada` — todas com ≥1 arquivo. A sexta (`--shadow-fab`) NUNCA aparece como texto literal em nenhum build (ver seção dedicada abaixo) — prova alternativa usada e documentada.
- Os NOVE glifos removidos (`🎓 📈 ✨ ✅ 📡 🟢 🟡 ⚪ 🔴`) confirmados **ausentes** de `server/web_dist` — a checagem que só um bundle novo (não um build falho em silêncio) passaria.
- Diff de `server/app/` limitado à linha de `SERVER_BUILD_ID`; `git diff --stat` dos quatro manifests (`web/package.json`, `web/package-lock.json`, `server/requirements.txt`, `server/requirements-prod.txt`) vazio — zero pacote novo.
- Servidor de produção local (`bash scripts/executar.sh --prod`) subiu em `:8787`, confirmado por `curl http://localhost:8787/api/health` → `{"ok":true,"build":"F10-20260906-01"}`, deixado NO AR de propósito (nenhum `--stop`).
- Nenhum `git push` executado em nenhum momento.

## Task Commits

1. **Task 1: Bump do carimbo e publicação do front** - `c09b6d1` (chore)
2. **Task 2: Remedir os três critérios contra o bundle de produção** - automatizável completa nesta sessão (build/publish/grep/servidor), sem commit adicional de código — a remedição visual em si fica com o orquestrador (ver handoff abaixo); nenhuma mudança de `PALETTE.light.shadowFab` foi necessária (ver seção SYS-03).

**Plan metadata:** commit desta entrega (SUMMARY.md) segue nesta mesma sessão.

## Files Created/Modified

- `web/src/version.js` - `BUILD_ID` avançado para `F10-20260906-01`
- `server/app/main.py` - `SERVER_BUILD_ID` sincronizado para `F10-20260906-01` (única linha alterada)
- `server/web_dist` - republicado por completo (25 arquivos: 11 chunks renomeados por hash de conteúdo, criações/remoções de chunks pequenos que mudam de tamanho entre builds — padrão normal do Vite content-hashing, não indica regressão)

## Decisions Made

Ver `key-decisions` no frontmatter. Duas decisões tomadas durante a execução, nenhuma delas de produto:

1. **Assinatura `--shadow-fab` do plano é inverificável por grep, em qualquer build** — ver seção dedicada "Achado: assinatura `--shadow-fab` nunca é literal" abaixo.
2. **SYS-03 permanece ABERTO nesta entrega**, apesar de já ter sido visualmente confirmado no dev server pelo orquestrador (22-03-SUMMARY.md) — porque este plano exige explicitamente a medição contra o bundle de PRODUÇÃO, ainda não feita. Ver seção dedicada.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Assinatura de aceite `--shadow-fab` nunca existe como texto literal em nenhum build — prova alternativa usada**

- **Found during:** Task 1, passo 5 (grep das seis assinaturas de presença).
- **Issue:** O critério de aceite da Task 1 exige `grep -rlI "--shadow-fab" server/web_dist` retornando ao menos um arquivo. A checagem retornou **zero arquivos**. Investigação: `VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase())` (`App.jsx:113`) gera o nome da CSS custom property em **runtime**, por manipulação de string dentro do JS carregado pelo navegador — o texto `"--shadow-fab"` nunca é escrito como string literal em nenhum lugar do código-fonte, nem antes nem depois da minificação. Confirmado que o mesmo vale para a chave pré-existente `scrim` (`--scrim` também não aparece literalmente em lugar nenhum, mesmo sendo produção já publicada há fases). Ou seja: esta não é uma regressão desta fase nem uma falha da publicação — é uma assinatura de verificação escrita incorretamente no plano (`22-04-PLAN.md`, tabela `<assinaturas_no_bundle>`), que presumiu que a chave sobreviveria como string CSS quando na verdade ela é computada programaticamente.
- **Fix (verificação alternativa, sem alterar código de produto):** Confirmado por grep que a evidência real de que o código do SYS-03 chegou ao bundle está presente por três vias independentes: (a) a property key `shadowFab` aparece 2× em `server/web_dist/assets/index-Btka_lGt.js` (nomes de propriedade de objeto não são mangled pelo minificador padrão do Vite/esbuild); (b) o valor literal `rgba(0,0,0,0.45)` (tema escuro) está presente; (c) o valor literal `rgba(15,20,28,0.22)` (tema claro) está presente. Os três juntos provam que `PALETTE.dark.shadowFab`/`PALETTE.light.shadowFab` e o consumo em `PetFab` chegaram ao bundle publicado — o mesmo fato que a assinatura `--shadow-fab` pretendia provar, por um caminho que de fato sobrevive à publicação.
- **Files modified:** Nenhum (achado é sobre o método de verificação, não sobre o código-fonte).
- **Verification:** `grep -rl -- "--shadow-fab\|shadow-fab" server/web_dist/` retorna vazio (confirmando a ausência em TODO o build, não só num arquivo); `grep -o "shadowFab" server/web_dist/assets/*.js` retorna 2 ocorrências; `grep -o "rgba(0,0,0,0.45)\|rgba(15,20,28,0.22)" server/web_dist/assets/*.js` retorna as duas.
- **Committed in:** `c09b6d1` (nota completa também no corpo da mensagem de commit).

---

**Total deviations:** 1 auto-fixed (1 blocking, Rule 3) — achado de metodologia de verificação, não de código. Nenhuma mudança de comportamento de produto foi necessária.
**Impact on plan:** O critério de aceite literal da Task 1 ("as seis assinaturas de presença retornam ao menos um arquivo cada") falha para 1 das 6 exatamente como escrito — mas a intenção do critério (provar que o código do SYS-03 chegou ao bundle publicado) está satisfeita por prova equivalente e mais forte (property key + os dois valores rgba, o que efetivamente distingue um bundle com SYS-03 de um sem). Recomendação para o próximo plano que tocar `<assinaturas_no_bundle>`: substituir `--shadow-fab` por `shadowFab` (ou pelos dois literais rgba) como assinatura de verificação padrão para chaves de `PALETTE` geradas via `VARKEY`.

## Issues Encountered

- `bash scripts/executar.sh --testes` na primeira tentativa (sandbox padrão) mostrou 117 falsos-`[X]` — `mktemp -d` falhou dentro do sandbox (`Operation not permitted`), fazendo cada teste tentar gravar log num caminho absoluto na raiz do filesystem. Não é falha de teste; é falha de escrita de log, mesmo padrão documentado em `21-04-SUMMARY.md`. Resolvido rerodando com `dangerouslyDisableSandbox`, que confirmou `pytest 2021 passed, 1 skipped` + 117/117 `web/tests/*.mjs` `[OK]`, `EXIT:0`.
- `bash scripts/publicar-web.sh` rodou dentro do sandbox padrão sem erro desta vez (diferente das sessões 22-01/02/03, que tiveram `EPERM` no cache do npm) — `web/node_modules` já existia no worktree desde os planos anteriores, então não houve `npm ci` do zero.
- `bash scripts/executar.sh --prod` (Task 2) precisou de `dangerouslyDisableSandbox` para instalar o venv Python (`server/.venv` ausente neste worktree) e fazer bind da porta `:8787`; `curl` contra `localhost:8787` também precisou de `dangerouslyDisableSandbox` (rede sandboxada nega por padrão até localhost). Ambos consistentes com o padrão documentado nos planos anteriores desta fase e da Fase 21.

## User Setup Required

None - no external service configuration required.

## SYS-03 — por que continua ABERTO nesta entrega (não FECHADO)

**Não confundir com a confirmação já registrada em `22-03-SUMMARY.md`.** Aquela seção "Orchestrator Live Re-Verification" mediu `filter: drop-shadow(...)` computado contra o **dev server** (`merge desta branch`, ambiente Vite dev, não minificado) — e concluiu, corretamente para aquele escopo, que o valor de partida (`rgba(15,20,28,0.22)`) não precisava de ajuste.

Este plano (`22-04-PLAN.md`, Task 2, item 3) exige uma medição **adicional e distinta**: o mesmo `--shadow-fab` computado, mas contra o **bundle de produção minificado servido em `:8787`**, em ambos os temas, incluindo o julgamento visual "halo separa sem virar disco/badge" e a passada em Modo Operador. Essa medição específica **não foi feita nesta sessão** (sem ferramenta de navegador neste subagente) — por isso, seguindo o critério de aceite explícito da Task 2 ("SYS-03 fica marcado como ABERTO, jamais como fechado" quando a ferramenta de navegador está indisponível), **SYS-03 permanece ABERTO** até essa medição específica acontecer contra o bundle publicado.

Dado que o mecanismo (`T.shadowFab` → `var(--shadow-fab)` → `PALETTE.{dark,light}.shadowFab`) é idêntico entre dev e produção (só muda a minificação de JS, não o valor computado do CSS custom property em runtime), a expectativa é que a medição confirme o mesmo resultado do 22-03 — mas essa é uma expectativa, não uma medição, e o plano proíbe explicitamente declarar fechado sem medir.

## Next Phase Readiness

- Fase 22 publicada: carimbo novo nos três elos, bundle com as adições E as nove remoções, suíte canônica verde.
- Os 3 critérios do ROADMAP (SYS-01/02/03) têm prova ESTÁTICA completa (guardiões dos planos 22-01/02/03 + grep no bundle publicado desta sessão). A prova DINÂMICA (DOM real, `:8787`, produção) fica com o orquestrador — roteiro abaixo.
- Nenhum `git push` para `origin` foi executado. A decisão a/b/c sobre enviar as Fases 17/18/19 (checkpoints humanos pendentes) a `origin` continua em aberto, do Alex — esta fase não a resolve nem a agrava.

## Orchestrator Live Re-Verification

**Ambiente confirmado sem ferramentas de navegador (`mcp__computer-use__*`, `mcp__claude-in-chrome__*`) vinculadas a este subagente** — mesma limitação conhecida e documentada nos planos das Fases 20/21 (bug upstream anthropics/claude-code#13898), e antecipada no prompt desta execução. A parte automatizável da Task 2 foi feita por completo; a remedição visual real dos 3 critérios fica para o orquestrador.

**Servidor NO AR, não parado de propósito:**
- Porta: `:8787`
- Carimbo confirmado: `F10-20260906-01` (via `curl http://localhost:8787/api/health` → `{"ok":true,"build":"F10-20260906-01"}`)
- Bundle servido na raiz confirmado: `curl http://localhost:8787/` referencia `index-Btka_lGt.js` (o mesmo chunk onde `shadowFab`/`x proximity`/etc. foram encontrados por grep)
- Log do processo: `/private/tmp/claude-501/-Users-acamerini-dev-borisv2/31307cb9-7fa3-4f76-9369-16d54ae23ca0/scratchpad/executar-prod-22-04.log` (não persiste além desta sessão — se o orquestrador rodar num processo/sessão diferente e a porta não responder, resubir com `bash scripts/executar.sh --prod`; o build já está pronto em `server/web_dist`, então resubir é rápido, sem rebuild do zero).
- Para encerrar quando a remedição terminar: `bash scripts/executar.sh --stop`.

**Gotcha conhecido (precedente das Fases 20/21):** o navegador persistente do orquestrador já teve problema de service-worker/cache PWA obsoleto ao visitar `:8787` depois de um rebuild — resolvido desregistrando o SW e limpando caches no DevTools (`navigator.serviceWorker.getRegistrations()` → `unregister()`), NÃO é defeito de código. Se a tela carregar com conteúdo antigo (carimbo errado, mudanças da Fase 22 ausentes), esse é o primeiro suspeito antes de reabrir investigação.

### Pendente de verificação ao vivo (orquestrador)

Login numa conta local (web em `:8787`, carimbo `F10-20260906-01`) e percorrer os 3 critérios do ROADMAP na ordem abaixo.

**1. Trilho único (SYS-01).** Medir no DOM do container e do primeiro item de cada trilho: `getComputedStyle(el).scrollSnapType` e `getComputedStyle(primeiroItem).scrollSnapAlign`.
   - Home/Acompanhar, carrossel de setups (HERO-CARROSSEL) — esperado `x mandatory` / `center`.
   - Watchlist, filtro "MODELO DE ANÁLISE" — esperado `x proximity` / `start`.
   - Posições, tira "Oportunidades de opções" — esperado `x proximity` / `start`. Se a conta não tiver proposta ativa hoje, registrar como aberto (o snap já está provado estaticamente pelo guardião do plano 22-01) — não forjar dado.
   - Posições, linha de candidatos dentro do detalhe de uma posição com proposta — esperado `x proximity` / `start`. Mesma ressalva de dado real.
   - Em 375×812, para o filtro da Watchlist: `clientWidth` do container ÷ largura de um chip — esperado ~3 chips visíveis, **não 1** (prova de que o peek de 84% do HERO não vazou para o trilho de proximity).

**2. Zero emoji, ícone no traço do NavIcon (SYS-02).** Percorrer Perfil, Watchlist, Posições, Radar e a tela de configuração de chave:
   - Contagem de emoji visível — esperado zero em todas as telas.
   - Para cada um dos 9 sites (Estudo/Operador no Perfil, Indicadores, Reanalisar/`{btnAnalise}`, Stop/alvo (IA), chave configurada, Varredura automática de hoje, tier do Radar Forte/Moderada/Neutra/Fraca) — confirmar que o rótulo textual continua e que o ícone ao lado é um `<svg>` no DOM, não texto.
   - `stroke` computado de pelo menos 2 ícones em CADA tema — confirmar que acompanha `currentColor` (legibilidade nos dois temas).
   - `<select>` de skill do Boris — as 2 `<option>` leem `... · Estudo` / `... · Operador`, sem emoji.
   - Ponto de tier do Radar — `fill` computado do `<circle>` bate com `#22c55e`/`#f59e0b`/`#9ca3af`/`#ef4444` e o rótulo textual do tier aparece ao lado. Se nenhum ativo tiver `confluencia` hoje, registrar como aberto com referência à prova estática do plano 22-03.

**3. Mascote separado do fundo (SYS-03) — a conferência que fecha a fase.** Encontrar uma tela com um card claro diretamente atrás da posição fixa do FAB (`right:14px, bottom:92px`) — Posições ou Watchlist com lista cheia servem.
   - **Tema ESCURO:** confirmar que a silhueta da coruja se separa do card atrás; registrar `getComputedStyle` de `--shadow-fab` (ou o `filter` computado do elemento do FAB) — esperado `rgba(0,0,0,0.45)`, idêntico a antes da fase.
   - **Tema CLARO:** confirmar (a) que o halo separa a silhueta do card e (b) que NÃO aparece um "disco"/badge chapado ao redor da arte. Registrar o valor computado — partida esperada `rgba(15,20,28,0.22)`.
   - Repetir as duas conferências em **Modo Operador** (passada de screenshot, não bateria nova — `MODE_OPERADOR` sobrescreve variáveis de tema por cima do dark/light).
   - **Se o tema claro estiver fraco demais (sem separação) ou pesado demais (borrão/disco):** ajustar SOMENTE `PALETTE.light.shadowFab` em `web/src/App.jsx` (linha ~108, valor atual `"rgba(15,20,28,0.22)"`), refazer `bash scripts/publicar-web.sh` e `bash scripts/executar.sh --testes`, reconferir, e registrar aqui o valor inicial, o valor final e a razão do ajuste. O guardião do plano 22-03 só exige que `light` seja DIFERENTE de `dark` — qualquer valor calibrado passa.
   - **Nota:** `22-03-SUMMARY.md` já registra confirmação visual do orquestrador contra o DEV SERVER (não produção) nos dois temas, com o mesmo valor de partida aprovado sem ajuste — forte indício de que a medição em produção confirmará o mesmo, mas essa é uma expectativa, não uma medição feita. SYS-03 só pode ser marcado FECHADO depois desta conferência específica contra `:8787` acontecer de fato.

### Tabela dos 3 critérios do ROADMAP × resultado

| # | Critério (ROADMAP Fase 22) | Resultado medido |
|---|---|---|
| 1 | SYS-01 — todo trilho horizontal rola com snap e deixa o próximo item espiando | Automatizado: bundle contém `x proximity` (grep confirmado); guardião estático `test_fase22_componentes_compartilhados.mjs` Seção A (plano 22-01) prova os 4 trilhos por análise do JSX-fonte publicado. **Computados em DOM real (`scrollSnapType`/`scrollSnapAlign`, 4 trilhos, contagem de chips em 375px) — aberto, roteiro item 1 acima.** |
| 2 | SYS-02 — zero emoji do sistema operacional, ícone SVG no traço do NavIcon, legível nos dois temas | Automatizado: varredura Unicode completa em `App.jsx` dá zero (fonte); bundle publicado confirma AUSÊNCIA dos nove glifos (grep, checagem de remoção); guardião Seções B/C (planos 22-02/22-03) prova os 9+8 sites por análise estática. **`stroke` computado por tema, rótulos preservados em DOM real, `fill` do tier do Radar, `<option>` sem emoji — aberto, roteiro item 2 acima.** |
| 3 | SYS-03 — mascote flutuante separado do fundo, nos dois temas, sem parecer cortado | Automatizado: bundle contém a property key `shadowFab` (2×) e os dois valores `rgba(0,0,0,0.45)`/`rgba(15,20,28,0.22)` (prova alternativa à assinatura `--shadow-fab`, que nunca é literal — ver Deviations); guardião Seção D (plano 22-03) prova os dois valores por tema por análise estática. **Julgamento visual halo-vs-disco nos dois temas contra o BUNDLE DE PRODUÇÃO — não medido nesta sessão. SYS-03 permanece ABERTO — roteiro item 3 acima, incluindo o caminho de ajuste se necessário.** |

Nenhum valor visual foi aproximado, estimado ou declarado verificado sem medição — os três itens acima estão marcados "aberto" com roteiro explícito e caminho de ajuste, não com adjetivo.

Reafirmando: **nenhum `git push` foi feito nesta sessão**; a decisão a/b/c sobre enviar as Fases 17/18/19 (checkpoints humanos pendentes) a `origin` segue em aberto, do Alex, e esta publicação (Fase 22, local em `server/web_dist`) não a resolve nem a agrava — ela só existe no repositório local até o `origin` receber.

---
*Phase: 22-componentes-compartilhados-trilho-cones-mascote*
*Completed: 2026-09-06*

## Self-Check: PASSED

- FOUND: web/src/version.js
- FOUND: server/app/main.py
- FOUND: server/web_dist
- FOUND: .planning/phases/22-componentes-compartilhados-trilho-cones-mascote/22-04-SUMMARY.md
- FOUND: commit c09b6d1 (Task 1)
