---
phase: 21-duplica-o-removida-e-portf-lio-consolidado
plan: 04
subsystem: infra
tags: [publish, build-stamp, vite, fastapi, prod-server]

# Dependency graph
requires:
  - phase: 21-duplica-o-removida-e-portf-lio-consolidado
    plan: 03
    provides: "código da fase completo (DEDUP-01/02/03, FIX-03) e suíte canônica verde, pronto pra publicar"
provides:
  - "server/web_dist republicado com o carimbo F10-20260905-03, contendo as quatro mudanças da Fase 21"
  - "Servidor de produção local (:8787) no ar, servindo o bundle novo, pronto para a remedição visual do orquestrador"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Handoff 'Pendente de verificação ao vivo (orquestrador)' quando o subagente não tem ferramenta de navegador — mesmo padrão da Fase 20 (20-04-SUMMARY.md) e dos 3 planos anteriores desta fase"

key-files:
  created: []
  modified:
    - web/src/version.js
    - server/app/main.py
    - server/web_dist

key-decisions:
  - "Suíte web/tests/*.mjs rodou 2x: a primeira (sandbox padrão) mostrou 116 falsos-[X] porque `mktemp -d` falhou (Operation not permitted) e todo log de teste tentou gravar em caminho absoluto na raiz do filesystem — não é falha de teste, é falha de escrita de log (mesmo padrão já documentado no 21-03-SUMMARY.md). Rerodei com `dangerouslyDisableSandbox` para eliminar o ruído e confirmar RC=0 de verdade."
  - "Servidor de produção local subiu com `dangerouslyDisableSandbox` (venv setup + bind de porta) e foi deixado NO AR de propósito, sem `--stop`, para o orquestrador reusar sem pagar novo ciclo de build — Task 2 não tem ferramenta de navegador neste ambiente, então a remedição visual dos 4 critérios fica com o orquestrador."

patterns-established: []

requirements-completed: [DEDUP-01, DEDUP-02, DEDUP-03, FIX-03]

# Metrics
duration: ~55min
completed: 2026-09-06
---

# Phase 21 Plan 04: Bump, publicação e handoff da remedição de produção Summary

**BUILD_ID F10-20260905-02 → F10-20260905-03; `server/web_dist` republicado com as quatro mudanças da Fase 21 comprovadas no bundle minificado (inclusive a remoção de "Modo do app:"); suíte canônica verde depois da publicação; servidor de produção local deixado no ar em `:8787` para o orquestrador remedir visualmente os 4 critérios do ROADMAP (sem ferramenta de navegador neste subagente).**

## Performance

- **Duration:** ~55 min
- **Started:** 2026-09-06T00:27:00Z (aprox., após o reset do worktree)
- **Completed:** 2026-09-06T01:22:36Z
- **Tasks:** 2 (Task 1 completa; Task 2 automatizável completa, remedição visual entregue ao orquestrador)
- **Files modified:** 27 (`web/src/version.js`, `server/app/main.py`, 25 arquivos dentro de `server/web_dist`)

## Accomplishments

- `BUILD_ID` avançado para `F10-20260905-03` (`web/src/version.js`), `server/app/main.py:SERVER_BUILD_ID` sincronizado pelo próprio `publicar-web.sh` (nunca editado à mão).
- `server/web_dist` republicado (1,6M) com o bundle minificado da Fase 21 dentro: as quatro assinaturas de adição (`PATRIMÔNIO TOTAL`, `Trocar modo`, `a curva aparece a partir do 3º dia`) presentes, e a assinatura de remoção (`Modo do app:`) **ausente** — a checagem mais valiosa das cinco, porque prova que a remoção do DEDUP-02 chegou ao bundle e não só as adições (um bundle antigo/build silenciosamente falho passaria nas quatro primeiras).
- Suíte canônica verde DEPOIS da publicação: pytest `2021 passed, 1 skipped` + `web/tests/*.mjs` `116 [OK] / 0 [X]`.
- Servidor de produção local (`bash scripts/executar.sh --prod`) no ar em `:8787`, confirmado por `curl http://localhost:8787/api/health` → `{"ok":true,"build":"F10-20260905-03"}` — pronto para a remedição visual do orquestrador, deixado rodando de propósito (nenhum `--stop`).
- Nenhum `git push` executado em nenhum momento. Decisão a/b/c sobre enviar as Fases 17/18/19 (checkpoints humanos pendentes) a `origin` segue em aberto, do Alex.

## Task Commits

1. **Task 1: Bump do carimbo e publicação do front** - `a404ff5` (chore)
2. **Task 2: Remedir os quatro critérios contra o bundle de produção** — sem commit de código (task de verificação); resultado documentado abaixo e entregue como handoff.

**Plan metadata:** (este commit, criado a seguir)

## Files Created/Modified

- `web/src/version.js` — `BUILD_ID`: `F10-20260905-02` → `F10-20260905-03`.
- `server/app/main.py` — `SERVER_BUILD_ID` sincronizado para `F10-20260905-03` pelo `publicar-web.sh` (linha ~1013).
- `server/web_dist/**` — 25 arquivos (index.html, sw.js, workbox, e os chunks JS com hash novo). 5 chunks antigos removidos (substituídos por hash novo do build), 2 chunks novos criados, o restante renomeado (rename detectado pelo git por similaridade de conteúdo). Nenhuma edição manual — tudo produto de `scripts/publicar-web.sh`.

## Decisions Made

- Rodar a suíte web duas vezes (uma com sandbox padrão, uma com `dangerouslyDisableSandbox`) para separar sinal de ruído: a primeira rodada mostrou **116 falsos-`[X]`** porque `mktemp -d` (linha 32 de `scripts/executar.sh`) falhou com "Operation not permitted" dentro do sandbox padrão da ferramenta Bash, deixando `TMPDIR_TESTES` vazio — cada teste tentou gravar seu log em `/test_xxx.mjs.log` (caminho absoluto na raiz do filesystem, fora da allowlist de escrita), e a falha de redirecionamento fez a subshell inteira falhar mesmo que o teste em si tivesse passado. Isso é o MESMO padrão de sandbox já documentado no `21-03-SUMMARY.md` ("Setup do ambiente"), não uma regressão de código desta fase. Confirmado com a segunda rodada (sandbox desabilitado): `116 [OK] / 0 [X]`, `RC=0`.
- Task 2 não tenta improvisar a verificação visual: sem ferramenta de navegador vinculada a este subagente (confirmado nos 3 planos anteriores da fase — `21-01`, `21-02`, `21-03` — e na nota `<ferramenta_de_navegador>` do próprio plano), fiz a parte automatizável (subir `--prod`, confirmar por `curl` que `:8787` serve o carimbo novo) e deixei o servidor NO AR para o orquestrador reusar, em vez de rodar `--stop` e forçar um rebuild depois.

## Deviations from Plan

None - plan executado exatamente como escrito (Task 1 completa de ponta a ponta; Task 2 seguiu o roteiro de handoff explícito previsto pelo próprio plano para o caso de ausência de ferramenta de navegador).

## Issues Encountered

- **Sandbox e `mktemp`/rede localhost (não é deviation de código):** três pontos precisaram de `dangerouslyDisableSandbox: true`, todos com evidência clara de restrição de sandbox (não bug de código):
  1. `npm install` em `web/` (certificados de sistema — warnings inofensivos, install completou).
  2. `bash scripts/executar.sh --testes` (segunda rodada) — `mktemp -d` falhando dentro do sandbox padrão gerava 116 falsos-negativos no runner de testes web (ver "Decisions Made" acima).
  3. `curl http://localhost:8787/...` — o sandbox padrão bloqueia conexão a `localhost`/`127.0.0.1` mesmo para o próprio servidor que acabamos de subir ("Immediate connect fail... Operation not permitted"); necessário desabilitar sandbox para confirmar o health-check.
  4. Subir `bash scripts/executar.sh --prod` — o boot precisou reconstruir o venv Python do zero (pip install de todas as dependências de `server/requirements.txt`) e abrir a porta 8787; ambos bloqueados pelo sandbox padrão.
- **Polling de processo em background:** a primeira tentativa de aguardar a suíte de testes via `pgrep`/`kill -0` falhou porque `pgrep`/`sysmond` não estão disponíveis neste sandbox ("Cannot get process list"); troquei para polling por conteúdo do arquivo de log (`grep` por marcadores de conclusão) em vez de checar o PID.

## Orchestrator Live Re-Verification

**Ambiente confirmado sem ferramentas de navegador (`mcp__computer-use__*`, `mcp__claude-in-chrome__*`) vinculadas a este subagente** — mesma limitação conhecida e documentada nos 4 planos da Fase 20 e nos 3 planos anteriores desta Fase 21 (bug upstream anthropics/claude-code#13898). A parte automatizável da Task 2 foi feita por completo; a remedição visual real dos 4 critérios fica para o orquestrador.

**Servidor NO AR, não parado de propósito:**
- Porta: `:8787`
- Carimbo confirmado: `F10-20260905-03` (via `curl http://localhost:8787/api/health` → `{"ok":true,"build":"F10-20260905-03"}`)
- Log do processo: `/private/tmp/claude-501/-Users-acamerini-dev-borisv2/31307cb9-7fa3-4f76-9369-16d54ae23ca0/scratchpad/executar-prod-21-04.log` (não persiste além desta sessão — se o orquestrador rodar num processo/sessão diferente, pode ser necessário resubir com `bash scripts/executar.sh --prod`; o build já está pronto em `server/web_dist`, então o resubir é rápido, sem rebuild do zero).
- Para encerrar quando a remedição terminar: `bash scripts/executar.sh --stop`.

**Gotcha conhecido (precedente da Fase 20, `20-04-SUMMARY.md`):** o navegador persistente do orquestrador já teve problema de service-worker/cache PWA obsoleto ao visitar `:8787` depois de um rebuild — resolvido desregistrando o SW e limpando caches no DevTools, NÃO é defeito de código. Se a tela carregar com conteúdo antigo (carimbo errado, mudanças da Fase 21 ausentes), esse é o primeiro suspeito antes de reabrir investigação.

### Pendente de verificação ao vivo (orquestrador)

Login numa conta local (web em `:8787`) e percorrer os 4 critérios do ROADMAP na ordem abaixo. Repetir os itens 2 e 3 nos dois temas (claro/escuro) e nos dois modos (Estudo/Operador) — é passada rápida de screenshot, não bateria nova.

1. **Curva única (DEDUP-01).** Ir em Acompanhar, depois Portfólio, mesma sessão.
   - Tela: Acompanhar — texto/seletor: contar ocorrências de `PATRIMÔNIO SIMULADO` no `document.body.innerText` (ou inspeção visual do card) — **esperado: 1**.
   - Tela: Portfólio — mesmo texto — **esperado: 0**.

2. **Card consolidado (DEDUP-03).** Em Portfólio, viewport 375×812.
   - Contar containers de card com os 4 valores (Patrimônio total/Resultado aberto/Caixa disponível/Em posições) — **esperado: 1**, não 4.
   - Medir `gridTemplateColumns` computada (`getComputedStyle`) do grid interno do card — **esperado: `1fr 1fr` ou os dois valores em px equivalentes**.
   - Medir `scrollWidth` vs `clientWidth` do container do card e de cada um dos 4 valores — **esperado: `scrollWidth === clientWidth` em todos**, sem quebra de linha nem overflow em 375px.

3. **Status único (DEDUP-02).** Tela Operador IA.
   - `document.body.innerText` — **esperado: `Modo do app:` AUSENTE**.
   - Card `OPERADOR NO SERVIDOR` com o toggle — **esperado: presente**.
   - Link `Trocar modo →` — **esperado: aparece 1× acima do card-herói**; tocar e confirmar navegação para Perfil.
   - Chip de modo do `Topbar` (`MODO ESTUDO` ou `MODO OPERADOR`) — **esperado: visível na mesma tela**.
   - Rolar até o card `ENTRADA AUTOMÁTICA` — **esperado: as duas linhas de transparência do `entradaAuto` (regra + contraste do backtest) aparecem dentro dele**, entre a descrição e o `<Toggle>`.

4. **Placeholder de pouco dado (FIX-03).**
   - Conta com 0 dias registrados — **esperado: texto `Sua curva começa amanhã` presente** (não regrediu).
   - Se houver conta local com 1-2 dias de snapshot de patrimônio — **esperado: texto `a curva aparece a partir do 3º dia`, e AUSÊNCIA de `<path>` de curva desenhada**. Se não houver conta nesse estado específico, **não forjar dado nem estimar** — registrar como aberto; a evidência determinística já existe por teste unitário real sobre `equityCurve()` no guardião do plano 21-03 (`web/tests/test_fase21_dedup_consolidacao.mjs`, Seção A), que já prova o comportamento sem depender de uma conta real chegar a esse estado.

### Tabela dos 4 critérios do ROADMAP × resultado

| # | Critério (ROADMAP Fase 21) | Resultado medido |
|---|---|---|
| 1 | DEDUP-01 — curva de patrimônio em exatamente uma tela | Automatizado: bundle contém a mudança (grep confirmado); guardião estático `test_fase21_dedup_consolidacao.mjs` (17 asserções, plano 21-01) prova a ausência de `<CapitalCurve>` em `CarteiraScreen` e a presença em `EvolucaoScreen` por análise estática do código-fonte publicado. **Contagem em DOM ao vivo — aberto, roteiro item 1 acima** (orquestrador, sem ferramenta de navegador neste subagente). |
| 2 | DEDUP-03 — card consolidado 2×2 em Portfólio | Automatizado: bundle contém `PATRIMÔNIO TOTAL` (grep confirmado); guardião estático confirma grid 2×2 e ordem das 4 células por análise do JSX-fonte. **Contagem de cards, `gridTemplateColumns` computada e `scrollWidth===clientWidth` em 375px ao vivo — aberto, roteiro item 2 acima.** |
| 3 | DEDUP-02 — status único em Operador IA | Automatizado: bundle contém `Trocar modo` e NÃO contém `Modo do app:` (grep confirmado — a checagem de remoção, mais valiosa que a de adição). Guardiões estáticos reescritos (plano 21-02) provam a realocação do link e da transparência ADR-017 por análise do JSX-fonte. **Confirmação visual em DOM real ao vivo (link 1×, navegação pro Perfil, chip do Topbar, transparência dentro do card certo) — aberto, roteiro item 3 acima.** |
| 4 | FIX-03 — placeholder de pouco dado em CapitalCurve | Automatizado: bundle contém `a curva aparece a partir do 3º dia` (grep confirmado). Prova comportamental REAL (não só estática) já existe: guardião do plano 21-03 chama `equityCurve()` com 1 e 2 snapshots reais e confirma `days`/texto de `curvaPoucosDias()` corretos nos dois modos. **Estado de 0 dias e o estado de 1-2 dias em tela real — aberto, roteiro item 4 acima** (21-03-SUMMARY.md já registrou que forjar uma conta com exatamente 1-2 dias é desproporcional; a prova unitária é aceita como suficiente para fechar o requisito, a visual fica como nice-to-have). |

Nenhum valor visual foi aproximado, estimado ou declarado verificado sem medição — os quatro itens acima estão marcados "aberto" com roteiro explícito, não com adjetivo.

### Fechamento do roteiro pelo orquestrador (2026-09-05)

Executado via MCP do navegador contra `:8787` (build `F10-20260905-03`),
conta local existente. Gotcha de service worker/cache PWA reincidiu
(mesmo precedente da Fase 20) — resolvido com
`navigator.serviceWorker.getRegistrations()`→`unregister()` +
`caches.keys()`→`caches.delete()` antes de medir.

| # | Item do roteiro | Resultado |
|---|---|---|
| 1 | Curva única — Acompanhar tem, Portfólio não | ✓ Confirmado (`PATRIMÔNIO SIMULADO`: presente em Acompanhar, ausente em Portfólio) |
| 2 | Card consolidado — 1 card, grid 2 colunas, sem overflow | ✓ Confirmado (`gridTemplateColumns: "141.5px 141.5px"`, `scrollWidth===clientWidth` em 375px) |
| 3 | Status único — sem "Modo do app:", "Trocar modo →" presente, chip do Topbar visível | ✓ Confirmado (os 3 checáveis via `innerText`/DOM) |
| 4 | Placeholder de pouco dado — estado 0 dias | ✓ Confirmado (verificação da 21-03, "Sua curva começa amanhã" intacto). Estado de 1-2 dias: mantido como "aberto" — prova unitária real já aceita como suficiente (ver 21-03-SUMMARY.md), forjar conta nesse estado exato é desproporcional. |

Os 4 critérios do ROADMAP da Fase 21 estão fechados (3 por medição visual
direta, 1 por prova comportamental unitária + confirmação do estado
adjacente). Nenhum `git push` foi feito em nenhum momento desta fase.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `server/web_dist` publicado com o carimbo `F10-20260905-03`, três elos coerentes (`web/src/version.js`, `server/app/main.py:SERVER_BUILD_ID`, bundle).
- Suíte canônica verde depois da publicação (`2021 passed, 1 skipped` + `116 [OK]/0 [X]`).
- Servidor de produção local NO AR em `:8787`, pronto para o orquestrador remedir os 4 critérios do ROADMAP contra o bundle real, sem precisar rebuildar.
- **Nenhum `git push` foi executado.** A decisão a/b/c sobre enviar a `origin` o trabalho acumulado (Fase 21 + o risco herdado das Fases 17/18/19, checkpoints humanos ainda pendentes/adiados) segue em aberto, do Alex — não foi tomada por este agente.
- Fase 21 fica pronta para fechar assim que o orquestrador completar o roteiro de verificação visual acima (ou registrar formalmente os itens abertos como aceitos, dado que 3 dos 4 critérios já têm prova estática/unitária real e só falta a confirmação em DOM/tela).

---
*Phase: 21-duplica-o-removida-e-portf-lio-consolidado*
*Completed: 2026-09-06*
