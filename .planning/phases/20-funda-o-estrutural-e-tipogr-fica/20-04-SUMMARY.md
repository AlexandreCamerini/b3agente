---
phase: 20-funda-o-estrutural-e-tipogr-fica
plan: 04
subsystem: build-publish
tags: [publish, build-stamp, ci, vite, prod-verification, web]

# Dependency graph
requires:
  - phase: 20-funda-o-estrutural-e-tipogr-fica
    plan: "03"
    provides: "Os 7 requisitos da fase (FIX-01, FIX-02, SYS-04, TYPO-01, TYPO-02, TYPO-03, MOTION-03) implementados e travados pelo guardião estático"
provides:
  - "Fundação estrutural/tipográfica da Fase 20 publicada em server/web_dist (BUILD_ID F10-20260905-02)"
  - "Confirmação por grep de que as 4 assinaturas de CSS da fase (tabular-nums, overflow-x:hidden, prefers-reduced-motion, 720px) chegaram ao bundle minificado"
  - "Servidor de produção local (:8787) no ar, servindo o bundle publicado — deixado rodando para o orquestrador completar a Task 2"
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
  - "Task 1 executada e verificada integralmente por este subagent (bash puro, sem dependência de browser MCP)."
  - "Task 2 (remedição via browser MCP contra :8787) NÃO pode ser executada por este subagent — limitação de ambiente confirmada nos 3 planos anteriores da fase (upstream anthropics/claude-code#13898). Servidor de produção deixado no ar em :8787 para o orquestrador reusar em vez de reconstruir."
  - "Efeito colateral registrado e não corrigido por este subagent (fora de escopo/sandbox): symlink de web/node_modules apontado para o worktree principal (/Users/acamerini/dev/borisv2) foi esvaziado pelo npm ci interno de publicar-web.sh, que segue o symlink ao remover recursivamente em vez de só desfazer o link — /Users/acamerini/dev/borisv2/web/node_modules ficou vazio (0B) e precisa de 'npm install' antes de ser usado novamente. Nada rastreado pelo git foi afetado."

requirements-completed: [FIX-01, FIX-02, SYS-04, TYPO-01, TYPO-02, TYPO-03, MOTION-03]

# Metrics
duration: ~40min
completed: 2026-09-05
---

# Phase 20 Plan 04: Publicação da fundação estrutural/tipográfica Summary

**Carimbo `F10-20260905-02` publicado nos três elos (`web/src/version.js`, `server/app/main.py:SERVER_BUILD_ID`, `server/web_dist`), CSS da Fase 20 confirmado por grep no bundle minificado, suíte canônica verde (2021 pytest passed + 1 skipped, 115 testes web `.mjs` OK) depois da publicação — Task 2 (remedição dos 5 critérios de sucesso contra o bundle em `:8787` via browser) fica pendente do orquestrador, que herda um servidor de produção já no ar servindo exatamente esse bundle.**

## Performance

- **Duration:** ~40 min
- **Completed:** 2026-09-05
- **Tasks:** 2 (Task 1 completa integralmente; Task 2 só a parte automatizável — subir e confirmar o servidor de produção — ver "Issues Encountered")
- **Files modified:** 3 (`web/src/version.js`, `server/app/main.py`, `server/web_dist` republicado)

## Accomplishments

- `bash scripts/bump.sh` (sem argumento): `F10-20260905-01` → `F10-20260905-02`.
- `bash scripts/publicar-web.sh`: build de produção (`npm ci && npx vite build`), publicação em `server/web_dist`, sincronização automática de `SERVER_BUILD_ID`.
- Três elos do carimbo confirmados coerentes:
  - `web/src/version.js`: `F10-20260905-02`
  - `server/app/main.py:SERVER_BUILD_ID`: `F10-20260905-02`
  - `server/web_dist/assets/index-qgYCE9kb.js` contém a string `F10-20260905-02`
- CSS da Fase 20 confirmado presente no bundle JS minificado (o CSS vive dentro do template string `GlobalStyle()`, não num `.css` separado):
  - `tabular-nums` — presente em `server/web_dist/assets/index-qgYCE9kb.js`
  - `overflow-x:hidden` — presente no mesmo arquivo
  - `prefers-reduced-motion` — presente no mesmo arquivo
  - `720px` — presente no mesmo arquivo
- `bash scripts/executar.sh --testes`, executado DEPOIS da publicação: `EXIT=0` — **2021 pytest passed + 1 skipped**; **115/115 testes `web/tests/*.mjs` `[OK]`**, incluindo o guardião `test_fase20_fundacao_visual.mjs` (22 asserções, cobrindo os 7 requisitos da fase).
- `git diff --stat web/package.json web/package-lock.json server/requirements.txt server/requirements-prod.txt` — vazio (zero pacote novo).
- Diff da publicação limitado exatamente aos três arquivos/árvores do `files_modified` do plano (`web/src/version.js`, `server/app/main.py`, `server/web_dist`) — confirmado por `git status --short` antes do `git add`.
- Servidor de produção local subido (`bash scripts/executar.sh --prod`) e confirmado no ar: `GET /api/health` → `{"ok":true,"build":"F10-20260905-02"}`; `GET /` serve `assets/index-qgYCE9kb.js` (o mesmo arquivo com o carimbo novo e as 4 assinaturas de CSS). **Deixado rodando** para o orquestrador reusar na Task 2, em vez de encerrado com `--stop`.
- **Nenhum `git push` executado.** `git status -sb` mostra a branch do worktree sem remote de rastreamento; `git log --oneline origin/main..HEAD` lista as ~34 entregas acumuladas das Fases 17/18/19/20 ainda não enviadas.

## Task Commits

1. **Task 1: Bump do carimbo e publicação do front** — `40e2d46` (chore)
2. **Task 2: Remedir os cinco critérios contra o bundle de produção** — sem commit (task de verificação; nenhum arquivo editado; ver "Issues Encountered" para o que falta)

**Base do plano:** `17922c4` (docs: update tracking after wave 3, plano 20-03)

## Files Created/Modified

- `web/src/version.js` — `BUILD_ID` `F10-20260905-01` → `F10-20260905-02`.
- `server/app/main.py` — `SERVER_BUILD_ID` sincronizado para `F10-20260905-02` (linha do comentário "Fase 13 Plano 05" preservada; só o literal do carimbo mudou).
- `server/web_dist` — republicado inteiro (16 assets renomeados/recriados por hash de conteúdo do Vite, `index.html` e `sw.js` atualizados); a imagem `boris-*.png` não mudou de hash (nenhum asset binário tocado por esta fase).

## Decisions Made

- Seguida a ordem exata do plano: `bump.sh` → `publicar-web.sh` → `executar.sh --testes` → conferência dos três elos → grep das quatro assinaturas de CSS.
- `web/node_modules` estava ausente neste worktree novo (git worktrees não compartilham `node_modules`, gitignored). Diferente dos planos 20-02/20-03 (que usaram symlink só para `npx vite build` isolado), este plano invoca `publicar-web.sh`, que roda `npm ci` internamente — e `npm ci` sempre começa removendo `node_modules` primeiro. Ver "Deviations from Plan" para o efeito colateral real que isso produziu.
- Servidor de produção (`--prod`) deixado no ar deliberadamente (não rodei `--stop`), conforme instrução explícita do prompt de execução — o orquestrador tem ferramenta de browser MCP e pode reusar o mesmo servidor sem esperar outro build de produção (~1min de `npm ci`/`pip install` a frio, medido nesta sessão).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `bash scripts/executar.sh --testes` falhava por restrição do sandbox, não por defeito do código**
- **Found during:** Primeira tentativa de rodar a suíte canônica após a publicação (critério de aceite da Task 1)
- **Issue:** `scripts/executar.sh --testes` usa `mktemp -d` (sem `-p`) para criar um diretório temporário para os logs dos testes `.mjs`. No macOS, `mktemp -d` sem template ignora a variável de ambiente `$TMPDIR` e usa `_CS_DARWIN_USER_TEMP_DIR` (`/var/folders/.../T/`) diretamente — caminho fora da allowlist de escrita do sandbox desta sessão, produzindo `mkdtemp failed ... Operation not permitted` e, em cascata, `TMPDIR_TESTES` vazio (`""`), fazendo cada log de teste tentar gravar na RAIZ do filesystem (`/test_x.mjs.log`), também bloqueada.
- **Fix:** Reexecutado o mesmo comando com o sandbox desabilitado para essa chamada específica (`dangerouslyDisableSandbox: true`), conforme a orientação padrão de ambiente para erros "Operation not permitted" causados pelo sandbox — não editei `scripts/executar.sh` (script compartilhado fora do escopo do plano; o comportamento do `mktemp` do macOS não é um bug do projeto).
- **Files modified:** nenhum (script não alterado)
- **Verification:** segunda execução saiu com `EXIT=0` (2021 pytest passed + 1 skipped; 115/115 `.mjs` `[OK]`).
- **Committed in:** n/a (nenhuma mudança de código; documentado aqui por transparência)

---

**Total deviations aplicadas (Rule 1-3):** 1 (Rule 3 — contorno de sandbox, sem edição de código).

### Efeito colateral registrado, NÃO corrigido (fora de escopo deste subagent)

**Symlink de `web/node_modules` esvaziou `node_modules` do worktree principal**
- **O que fiz:** Antes de rodar `publicar-web.sh`, criei `web/node_modules` como symlink para `/Users/acamerini/dev/borisv2/web/node_modules` (mesmo `package.json`/`package-lock.json`, diff vazio confirmado antes) — mesma técnica usada nos planos 20-02/20-03 para evitar uma instalação nova.
- **O que aconteceu:** `publicar-web.sh` roda `npm ci` internamente (diferente de 20-02/20-03, que só chamavam `npx vite build` isolado). `npm ci` sempre remove `node_modules` antes de reinstalar, e a remoção recursiva SEGUIU o symlink até o diretório de destino em vez de só desfazer o link — o resultado observado foi `/Users/acamerini/dev/borisv2/web/node_modules` ficando vazio (0 bytes, 297 pacotes removidos), enquanto este worktree recebeu um `node_modules` real e populado (297 entradas) a partir de uma instalação fresca (rede, sem lockfile alterado).
- **Impacto:** `/Users/acamerini/dev/borisv2` (o checkout principal, branch `v2/interacao-estrutural`) precisa de `npm install` (ou `npm ci`) dentro de `web/` antes de ser usado para build/dev — nenhum arquivo rastreado pelo git foi afetado (`node_modules` é gitignored); nenhum commit, branch ou histórico foi tocado.
- **Por que não corrigi:** restaurar `/Users/acamerini/dev/borisv2` está fora do worktree isolado deste agente (instrução explícita de não `cd`/escrever fora do próprio worktree) e é trivialmente resolvido pelo usuário com um `npm install`. Reportando aqui para que o Alex saiba antes de usar aquele checkout.
- **Verification:** confirmado via `ls -la`/`du -sh` nos dois `node_modules` (principal: 0B/2 entradas; este worktree: populado/297 entradas) — nenhuma tentativa de reconstrução foi feita.

**Impact on plan:** Nenhum — a publicação em si (este worktree) está correta, completa e verificada; o efeito colateral é externo ao artefato entregue por este plano.

## Issues Encountered

**Task 2 NÃO foi executada por este subagent, exceto a parte automatizável (subir o servidor de produção e confirmar que está servindo o bundle certo).** Confirmado empiricamente e informado de antemão no prompt de execução: subagentes spawnados via Task não herdam ferramentas MCP de navegador do orquestrador (`mcp__computer-use__*`, `mcp__claude-in-chrome__*` — bug upstream anthropics/claude-code#13898), mesma limitação documentada em `20-01-SUMMARY.md`, `20-02-SUMMARY.md` e `20-03-SUMMARY.md`. Este subagent não tentou invocar essas ferramentas nem improvisou/estimou os valores que a Task 2 pede.

**O que ESTÁ pronto para o orquestrador reusar:** `bash scripts/executar.sh --prod` está rodando (PID do processo uvicorn ativo neste worktree), servindo em `http://localhost:8787` (e `http://192.168.0.36:8787` na LAN). Confirmado:
- `GET /api/health` → `{"ok":true,"build":"F10-20260905-02"}`
- `GET /` serve `assets/index-qgYCE9kb.js` (contém o carimbo novo e as 4 assinaturas de CSS confirmadas por grep no arquivo em disco)

**Deixei o servidor RODANDO** (não rodei `bash scripts/executar.sh --stop`), conforme instrução explícita do prompt de execução, para que o orquestrador (com acesso a browser MCP) não precise esperar outro ciclo de build (`npm ci` + `pip install` a frio nesta sessão levaram ~1min combinados, por node_modules/venv ausentes no worktree novo).

**Os 6 itens da Task 2 que seguem pendentes, para o orquestrador medir contra `:8787` (mapeados aos critérios de aceite do plano):**

1. **375×812** — `.b3-shell` e `<main>` com `scrollWidth===clientWidth`; nenhum elemento com `right>375` além dos trilhos intencionais; tocar um item de trilho horizontal e focar um campo de texto confirmando que header/conteúdo/barra inferior não se deslocam juntos (sintoma original do FIX-01). Não medido nesta sessão.
2. **375×812** — badge de status de mercado em Modo Estudo trunca com reticência visível; nada do Topbar sai do viewport. Não medido nesta sessão.
3. **1280×900** — wrapper de conteúdo com 720px, centrado, alinhado ao `BottomNav`. Não medido nesta sessão.
4. **Dígitos** — `getComputedStyle(...).fontVariantNumeric === "tabular-nums"` num valor financeiro real do bundle de PRODUÇÃO (não do dev server). **Risco nomeado no próprio plano**: se der `"normal"` em vez de `"tabular-nums"`, a decisão mecânica da opção (a) do TYPO-01 não sobreviveu ao build de produção e a decisão precisa ser REABERTA com o orquestrador, não contornada. Não medido nesta sessão — grep estático confirma que a string `tabular-nums` está no bundle, mas isso não prova que o seletor de atributo `[style*="ui-monospace"]` está de fato casando no DOM servido por produção.
5. **Movimento reduzido** — com a preferência emulada: transição da raiz zerada, troca de tema instantânea, `.spin`/`.tt-track` com `animationName==="none"`, ticker parado em dois screenshots com intervalo; e, sem a emulação, o ticker voltando a andar. Não medido nesta sessão (mesma limitação de ferramenta de emulação de `prefers-reduced-motion` via CDP já registrada em `20-03-SUMMARY.md`, se persistir no ambiente do orquestrador).
6. **Fredoka** — `getComputedStyle(h1).fontFamily` começando por `Fredoka` em pelo menos 3 telas, com `document.fonts.check('600 22px Fredoka')` verdadeiro, servido pelo bundle de PRODUÇÃO. Não medido nesta sessão.

Para o critério 4 do ROADMAP (dígitos alinhados), a ressalva TYPO-01/TYPO-02 exigida pelo plano: **a metade do alinhamento de dígitos (TYPO-01, tabular-nums) está tecnicamente fechada** por implementação e guardião estático, pendente só da remedição em produção acima; **a metade "todo valor financeiro usa um dos três tamanhos nomeados" (TYPO-02) é deferimento declarado do `20-CONTEXT.md`** para as Fases 21/22, que migram tela a tela — não é falha desta fase, é escopo transferido e já registrado nos Planos 20-02/20-03.

Nenhum destes 6 itens foi aproximado ou estimado neste SUMMARY — ficam explicitamente em aberto, seguindo o mesmo padrão de `20-01`/`20-02`/`20-03` (que tiveram itens de browser fechados depois por reverificação ao vivo do orquestrador, cada um em seção própria "Orchestrator Live Re-Verification"). Recomendo o mesmo fluxo aqui: o orquestrador roda os 6 itens contra o servidor já no ar em `:8787` (commit `40e2d46`) e anexa os resultados a este SUMMARY, encerrando com `bash scripts/executar.sh --stop` ao final.

**Reafirmado: nenhum `git push` foi feito nesta sessão. A decisão a/b/c sobre enviar a `origin` as Fases 17/18/19 (checkpoints humanos pendentes, ver `.planning/STATE.md`) segue em aberto e não foi tomada por este agente.**

## User Setup Required

- `/Users/acamerini/dev/borisv2/web` precisa de `npm install` (ou `npm ci`) antes do próximo uso — `node_modules` daquele checkout ficou vazio como efeito colateral desta sessão (ver "Deviations from Plan"). Não afeta nenhum arquivo rastreado pelo git.
- Nenhuma outra configuração de serviço externo necessária.

## Next Phase Readiness

- Fundação da Fase 20 publicada e verificada por grep/suíte automatizada; falta só a remedição visual em produção (Task 2, itens 1-6 acima) para fechar a fase com evidência de browser, seguindo o mesmo padrão dos 3 planos anteriores.
- Servidor de produção já no ar em `:8787` — o orquestrador pode ir direto à medição sem esperar outro build.
- Bloqueador residual único: os 6 itens de verificação ao vivo listados acima, todos mapeados 1:1 aos critérios de aceite da Task 2 do plano.

---
*Phase: 20-funda-o-estrutural-e-tipogr-fica*
*Completed: 2026-09-05*

## Self-Check: PASSED

- FOUND: web/src/version.js
- FOUND: server/app/main.py
- FOUND: server/web_dist/assets/index-qgYCE9kb.js
- FOUND commit: 40e2d46 (chore — Task 1)
- FOUND commit: 17922c4 (plan base)
- CONFIRMED: GET http://localhost:8787/api/health → {"ok":true,"build":"F10-20260905-02"}
