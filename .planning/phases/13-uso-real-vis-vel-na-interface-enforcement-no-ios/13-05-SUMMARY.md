---
phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios
plan: 05
subsystem: infra
tags: [deploy, vite, capacitor, build-id, publicacao]

# Dependency graph
requires:
  - phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios
    plan: 04
    provides: "Checkpoint humano fechado — contraste do T.warn aprovado ao vivo, nome do app corrigido no App Store Connect"
provides:
  - "server/web_dist republicado com os 3 contadores da Fase 13 e o gate iOS, sob o carimbo BUILD_ID F10-20260830-02"
  - "SERVER_BUILD_ID sincronizado (F10-20260830-02) e distinto de qualquer carimbo já usado por um deploy anterior no mesmo dia"
  - "Pendência de TestFlight nomeada explicitamente: CAP-12 só vale no iPhone do usuário após build novo distribuído (web/ios/ não gerado neste ambiente)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - web/src/version.js
    - server/web_dist (34 arquivos — build republicado)
    - server/app/main.py (SERVER_BUILD_ID)

key-decisions:
  - "BUILD_ID sequencial 01 do dia (gerado automaticamente por scripts/bump.sh) colidia com o SERVER_BUILD_ID F10-20260830-01 de um deploy só-backend (ADR-23, PR #27) já confirmado em produção mais cedo no mesmo dia — usei scripts/bump.sh F10-20260830-02 explícito para preservar a garantia de identificação única de entrega que o próprio plano exige (T-13-17)"
  - "web/ios/ não existe neste worktree (diretório gitignorado, gerado localmente por scripts/setup-ios.sh) — não rodei npx cap add ios para criar o projeto do zero, seguindo a instrução explícita do plano de não improvisar; a sincronização do bundle nativo fica registrada como pendência do Alex (junto com o build/upload no TestFlight)"

patterns-established: []

requirements-completed: [CAP-06, CAP-12]

# Metrics
duration: ~30min
completed: 2026-08-30
---

# Phase 13 Plan 05: Publicação — BUILD_ID novo e server/web_dist republicado Summary

**`server/web_dist` republicado a partir de um build real do front (BUILD_ID `F10-20260830-02`), com colisão de carimbo com um deploy só-backend do mesmo dia detectada e corrigida antes do commit; sincronização do bundle iOS não foi possível neste ambiente (`web/ios/` nunca gerado) e fica registrada nominalmente como pendência de TestFlight do Alex.**

## Performance

- **Duration:** ~30min
- **Tasks:** 2/2
- **Files modified:** 26 arquivos no commit de código (1 backend + 25 em `server/web_dist`, incluindo 6 exclusões de assets com hash antigo) + `web/src/version.js`

## Accomplishments
- Suíte canônica (`bash scripts/executar.sh --testes`) verde ANTES de publicar: 1741 passed / 1 skipped (pytest) + todos os `web/tests/*.mjs` OK
- `BUILD_ID` avançado de `F10-20260827-02` para `F10-20260830-02` (formato `<prefixo>-<AAAAMMDD>-<NN>` respeitado)
- `server/web_dist` republicado via `scripts/publicar-web.sh` (npm ci + vite build + `rm -rf`/`cp -r`), sem nenhuma edição manual da árvore
- Carimbo propagado e confirmado dentro do bundle JS publicado (`server/web_dist/assets/index-Cs5oE6Ep.js` contém `F10-20260830-02`)
- `SERVER_BUILD_ID` sincronizado em `server/app/main.py` (comentário também atualizado para refletir esta entrega, evitando um comentário desatualizado apontando para o commit `0385220`, que era um deploy não relacionado)
- Pendência de TestFlight registrada nominalmente (ver seção própria abaixo)

## Task Commits

1. **Task 1: Bump do carimbo e publicação do front** - `a681d21` (feat)
2. **Task 2: Sincronizar o bundle iOS e registrar a pendência de TestFlight** - sem commit de código (nenhum arquivo do repo foi alterado; o único artefato da task é a documentação abaixo e neste SUMMARY, commitado junto com a metadata do plano)

**Plan metadata:** commitado a seguir (`docs(13-05): complete plano`)

## Files Created/Modified
- `web/src/version.js` - `BUILD_ID` avançado para `F10-20260830-02`
- `server/web_dist/**` - árvore republicada por completo (34 entradas no diff: 6 exclusões de asset com hash antigo, 8 criações de asset com hash novo, 10 renomeações de asset com conteúdo idêntico salvo pelo bundler, `index.html` e `sw.js` atualizados)
- `server/app/main.py` - `SERVER_BUILD_ID` sincronizado para `F10-20260830-02`; comentário da linha atualizado de "ADR-23 Fase 4: relying party..." para "Fase 13 Plano 05: publica os 3 contadores + gate iOS"

## Decisions Made
- Ver `key-decisions` no frontmatter (colisão de carimbo corrigida; não recriar `web/ios/` do zero neste ambiente).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `BUILD_ID` sequencial automático colidia com um `SERVER_BUILD_ID` já em produção no mesmo dia**
- **Found during:** Task 1, após o primeiro `bash scripts/bump.sh` (sem argumento) e a primeira publicação
- **Issue:** `scripts/bump.sh` calcula o próximo sequencial olhando só para o `BUILD_ID` atual de `web/src/version.js` (que estava desatualizado, de `2026-08-27`); ele não tem visibilidade sobre o `SERVER_BUILD_ID` que já foi manualmente avançado hoje para `F10-20260830-01` num deploy só-backend (commit `0385220`, ADR-23 relying party, PR #27, já confirmado em produção segundo `STATE.md`). O resultado do primeiro bump (`F10-20260830-01`) reusaria, para uma entrega de front completamente diferente, exatamente o mesmo carimbo que uma entrega anterior distinta já usou em produção — isso quebra a garantia central que o próprio plano declara como mitigação de T-13-17 (Repudiation: "o `BUILD_ID` viaja version.js → dist → web_dist e é registrado no SUMMARY... prova qual entrega está no ar"). Um carimbo reutilizado para dois artefatos diferentes é ambíguo por definição, mesmo respeitando o formato do padrão.
- **Fix:** Re-executei `bash scripts/bump.sh F10-20260830-02` (sequencial explícito) e republiquei com `scripts/publicar-web.sh`, garantindo um carimbo nunca usado antes por nenhum deploy do dia.
- **Files modified:** `web/src/version.js`, `server/web_dist/**`, `server/app/main.py`
- **Verification:** `grep -q "F10-20260830-02" server/web_dist/assets/*.js` confirma o carimbo correto propagado; `git log --oneline --all | grep SERVER_BUILD_ID` confirma que `F10-20260830-02` nunca apareceu antes em nenhum commit do histórico
- **Committed in:** `a681d21` (Task 1 commit)

**2. [Rule 1 - correção de verify command] O `<verify><automated>` literal do plano checa `server/web_dist/index.html`, mas o `BUILD_ID` vive no bundle JS, não no HTML**
- **Found during:** Task 1, ao rodar o comando de verify exatamente como escrito no `13-05-PLAN.md`
- **Issue:** O comando `grep -q "$BUILD_ID" server/web_dist/index.html` falha sempre, mesmo com a publicação correta — o Vite não injeta o `BUILD_ID` no `index.html`, só referencia o chunk JS hasheado (`<script src="/assets/index-HASH.js">`); o próprio `scripts/publicar-web.sh` verifica o carimbo em `web/dist/assets/*.js`, nunca em `index.html`.
- **Fix:** Nenhuma alteração de código — usei o alvo correto (`server/web_dist/assets/*.js`) para a verificação de fato, coerente com o mecanismo que `publicar-web.sh` já usa. Documentando aqui para quem revisar este plano não interpretar o `grep` original como reprovado.
- **Files modified:** nenhum (achado de processo, não de código)
- **Verification:** `grep -q "F10-20260830-02" server/web_dist/assets/*.js` → match confirmado
- **Committed in:** n/a (não é mudança de código)

---

**Total deviations:** 2 auto-fixed (1 bug de colisão de carimbo, 1 correção de verificação de processo)
**Impact on plan:** Ambas as correções são necessárias para que o `BUILD_ID` continue cumprindo seu papel de prova de proveniência (T-13-17). Nenhum scope creep — nenhuma funcionalidade nova foi adicionada, só a garantia de unicidade do carimbo foi restaurada.

## Issues Encountered

- **Task 2 — `web/ios/` não existe neste worktree.** `web/ios/` é gitignorado (gerado localmente por `scripts/setup-ios.sh`/`instalar-iphone.sh`) e este checkout/worktree nunca rodou esse setup. `cd web && npx cap sync ios` retornou:
  ```
  [error] ios platform has not been added yet.
  See the docs for adding the ios platform: https://capacitorjs.com/docs/ios#adding-the-ios-platform
  ```
  Conforme a instrução explícita da Task 2 ("se falhar por ausência de ambiente... NÃO improvisar"), não rodei `npx cap add ios` para criar o projeto do zero — isso geraria um projeto nativo novo dentro de um worktree efêmero, sem vínculo com o projeto Xcode real do Alex (que carrega ajustes manuais como o `PrivacyInfo.xcprivacy` arrastado no Xcode, conforme `TESTFLIGHT.md` item 3). Resultado: nenhuma sincronização de bundle nativo ocorreu nesta execução.
  - `grep -c "com.alexandrecamerini.bolsia" web/capacitor.config.ts` = 1, `git diff web/capacitor.config.ts` vazio — bundle id intocado
  - `git diff web/ios/App/App/App.entitlements` — caminho nem existe neste worktree (gitignorado, nunca gerado); diff vazio de forma trivial, nenhum flip de APNs foi feito ou tentado

## User Setup Required

**Pendência de TestFlight (única via para o CAP-12 valer nos aparelhos em campo):**

CAP-12 (gate do `deviceStore`) está implementado e coberto por teste no código, mas só executa no app nativo — e o app nativo carrega o bundle **embutido no binário** (`web/capacitor.config.ts` não usa `server.url`). Publicar a web (feito neste plano) **não** fecha o CAP-12 para o usuário do iPhone; só um build novo distribuído por TestFlight fecha, porque o bundle atual instalado nos aparelhos em campo continua sendo o anterior a esta publicação.

Caminho manual (do Alex, com ambiente Xcode local), conforme `TESTFLIGHT.md`:
1. Gerar/atualizar o projeto nativo local: `bash scripts/setup-ios.sh --no-open && (cd web && npx cap sync ios)` (ou, se `web/ios/` já existir na máquina do Alex, só `npx cap sync ios`)
2. `bash scripts/ios-bump-build.sh` (incrementa o build number — obrigatório a cada upload)
3. `bash scripts/ios-testflight.sh` (reaplica manifesto de privacidade + export compliance)
4. Archive/upload manual no Xcode (Product → Archive → Organizer → Distribute App → App Store Connect)
5. Adicionar o build ao grupo de testers (interno e/ou externo, ver `TESTFLIGHT.md` itens 15-21)

Nenhum passo de Archive/upload, mudança de bundle id ou flip de `--apns-prod` foi executado ou sugerido nesta plano — fora de escopo por desenho (guardrail T-13-19 do `13-05-PLAN.md`).

## Next Phase Readiness
- Front da Fase 13 (3 contadores + enforcement) está publicado em produção sob `BUILD_ID F10-20260830-02`, pronto para deploy do Railway no próximo `git push` (fora do escopo desta sessão — push é decisão do orquestrador/usuário)
- CAP-12 no iOS segue como pendência explícita e nomeada (não implícita) — não bloqueia o fechamento desta fase no que depende do agente, mas bloqueia a validação de campo do gate no iPhone até o Alex rodar o fluxo de TestFlight
- Nenhum bloqueio técnico conhecido para o encerramento da Fase 13 do lado do código

---
*Phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios*
*Completed: 2026-08-30*

## Self-Check: PASSED

- FOUND: .planning/phases/13-uso-real-vis-vel-na-interface-enforcement-no-ios/13-05-SUMMARY.md
- FOUND: commit a681d21 (Task 1 — bump + publicação)
- FOUND: commit c741a37 (SUMMARY.md deste plano)
