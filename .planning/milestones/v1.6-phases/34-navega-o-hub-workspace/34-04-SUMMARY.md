---
phase: 34-navega-o-hub-workspace
plan: 04
subsystem: release
tags: [checkpoint-humano, publicacao, build-id, docs-fechamento, milestone-v1.6]

# Dependency graph
requires:
  - phase: 34-navega-o-hub-workspace
    plan: 03
    provides: "Navegação hub/workspace completa em código: 3 pills, gate do ramo DADOS por aba, NAV-05 travado por guardião"
provides:
  - "Navegação hub+workspace da sub-aba Setups EM PRODUÇÃO (F10-20260920-01), aprovada por checkpoint humano ao vivo"
  - "Fase 33 (nunca publicada sozinha) e Fase 34 publicadas juntas no mesmo carimbo"
  - "REQUIREMENTS.md/ROADMAP.md/STATE.md fechados à mão, refletindo o estado real do milestone v1.6 (13/13 requirements v1 Done)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - .planning/phases/34-navega-o-hub-workspace/34-04-SUMMARY.md
  modified:
    - server/app/main.py
    - server/web_dist/**
    - web/src/version.js
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md

key-decisions:
  - "Publicação combinada de Fase 33+34 num único carimbo (F10-20260920-01) — decisão já registrada no ROADMAP da Fase 33 (33 fechou verificada em 2026-09-16 mas nunca foi ao ar)."
  - "Pendência do app iOS/TestFlight registrada como decisão do Alex, não executada por conta própria — o app nativo carrega bundle local e só recebe a navegação nova num build de TestFlight."
  - "Pedido novo do Alex nesta mesma sessão (jornada confusa do workspace + gráfico de payoff pouco confiável) registrado em STATE.md como candidato a PRÓXIMO MILESTONE (mapeia a PERS-01/v2 requirements já previstos), não como Fase 35 deste — o ROADMAP.md define v1.6 como exatamente as Fases 33-34, ambas fechadas."

requirements-completed: [NAV-01, NAV-02, NAV-03, NAV-04, NAV-05, NAV-06]

# Metrics
duration: "~40min (checkpoint + publicação, sessão anterior) + ~25min (fechamento de docs, esta sessão)"
completed: 2026-09-20
---

# Phase 34 Plan 04: Checkpoint humano, publicação combinada e fechamento de documentos Summary

**A navegação hub+workspace foi aprovada ao vivo pelo Alex, publicada em produção junto com a Fase 33 (nunca publicada sozinha) sob o carimbo `F10-20260920-01`, e os três documentos de planejamento foram fechados à mão — a Fase 34 e o milestone v1.6 (13/13 requirements v1) estão formalmente encerrados.**

## Performance

- **Duration:** checkpoint + publicação (~40min, sessão anterior) + fechamento de docs (~25min, esta sessão)
- **Tasks:** 3
- **Files modified:** `server/app/main.py`, `server/web_dist/**`, `web/src/version.js` (Task 2); `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` (Task 3)

## Accomplishments

### Task 1 — checkpoint humano bloqueante

- Roteiro de 6 itens verificado ao vivo em navegador real (dev server local, `api-qa-opcoes` mock + mercado forçado aberto): hub sem ticker mostra frase-ponte + Bloco A + Bloco B + vigias + chips, sem nada de análise de ativo; entrar num ticker esconde a descoberta cross-carteira e mostra o header com "Voltar"; voltar reseta o workspace (D-03: comportamento correto, não defeito); as 3 pills (Analisar/Comparar/Setups salvos) trocam de conteúdo sem a pill ativa se confundir com as outras; erro/degradado visível nos dois modos; 375px sem quebra de layout.
- **Item mais importante (NAV-05), medido, não assumido**: contagem de `read_network_requests` confirmou que trocar de pill dentro do workspace NÃO dispara nova leitura MCP — a mesma leitura paga (3 chamadas) serve as 3 abas.
- Aprovação do Alex registrada via seleção explícita ("Aprovado — publicar agora") — checkpoint bloqueante liberado, publicação autorizada.

### Task 2 — publicação combinada (Fases 33+34)

- Merge de segurança com `origin/main` conferido antes do carimbo (evita a colisão de `bump.sh` documentada em `bump-colide-em-sessao-paralela.md`).
- `bash scripts/bump.sh` → `web/src/version.js` `BUILD_ID = "F10-20260920-01"`.
- `bash scripts/publicar-web.sh` → `server/web_dist` regenerado (25 arquivos, hash de conteúdo mudou), `server/app/main.py` com o novo `SERVER_BUILD_ID` e comentário de histórico preservado (Fase 33+34 combinada, entrada anterior virou "HISTÓRICO").
- Suíte canônica confirmada antes do commit: 2923 pytest + 152/153 `.mjs` (única falha ambiental conhecida, `test_ios_assets.mjs`, `web/ios/` gitignored nesse momento).
- Commit `927a2d7` (`feat(34-04): publica Fases 33+34 juntas — F10-20260920-01`), push em `v2/interacao-estrutural` e `origin/main`.
- `/api/health` confirmado em produção servindo o `SERVER_BUILD_ID` derivado do novo carimbo.
- **Pendência declarada, não resolvida aqui**: o app iOS carrega bundle local (sem `server.url`) — a navegação nova só chega ao aparelho num build novo de TestFlight (`scripts/ios-testflight.sh`). Registrada como decisão do Alex, não executada por conta própria.

### Task 3 — fechamento à mão dos documentos (esta sessão)

- `REQUIREMENTS.md`: NAV-01..06 marcados `[x]`/Done (checkboxes + tabela de rastreio) — 13/13 requirements v1 do milestone concluídos.
- `ROADMAP.md`: checkboxes de Fase 33 e Fase 34 marcados no resumo do milestone; item `34-04-PLAN.md` completado na lista de planos da fase (checkpoint + publicação + docs); linha da Fase 34 na tabela de Progresso corrigida de "Executing (3/4)" para "4/4 | Complete"; status do milestone v1.6 atualizado de "in progress" para "código completo e publicado, aguardando `/gsd-complete-milestone`".
- `STATE.md`: `Current Position` reescrita para a Fase 34 fechada; a posição anterior (34 executando 3/4) preservada como histórico sob novo cabeçalho; pendências abertas declaradas explicitamente (iOS/TestFlight, backlog B2 por decisão D-03, 2 todos de bookkeeping já executados na Fase 33 mas ainda em `pending/`, avisos de lint pré-existentes, `.env.local` ausente neste worktree); frontmatter (`status`, `stopped_at`, `last_updated`, `last_activity`, `progress`) atualizado para refletir o milestone fechado (2/2 fases, 9/9 planos, 100%).
- Registrado em `STATE.md` o pedido novo do Alex nesta mesma sessão (jornada confusa do workspace + gráfico de payoff pouco confiável, com screenshot de produção confirmando 3 bugs) como candidato a **próximo milestone** via `/gsd-new-milestone` — explicitamente NÃO uma Fase 35 deste milestone, porque o `ROADMAP.md` define v1.6 como exatamente as Fases 33-34, ambas fechadas.
- Suíte canônica reconferida após as edições de docs: **2923 pytest passed / 0 failed / 5 skipped / 3 xfailed** + **153/153 `.mjs`** (a falha ambiental de `test_ios_assets.mjs` não se repetiu porque `web/ios/` passou a existir localmente após o `cap sync` da instalação no iPhone, mais cedo na mesma sessão — não é regressão, é o ambiente local diferente).
- `git diff .planning/` revisado linha a linha antes do commit — sem texto de sessão antiga sobrescrito, sem linha de métrica fora da tabela, sem contador de planos errado (a assinatura da corrupção que os mutadores do `gsd-sdk` causam neste repo, evitada por edição manual).

## Task Commits

1. **Task 1 (checkpoint humano)** — sem commit próprio (verificação ao vivo + aprovação, sessão anterior).
2. **Task 2: publicação combinada Fases 33+34** — `927a2d7` (feat)
3. **Task 3: fechamento à mão dos documentos** — `8944c71` (docs)

**Plan metadata:** commit deste SUMMARY.md (a seguir)

## Files Created/Modified

- `server/app/main.py` — `SERVER_BUILD_ID` novo + comentário de histórico preservado
- `server/web_dist/**` — 25 arquivos regenerados (hash de conteúdo)
- `web/src/version.js` — `BUILD_ID = "F10-20260920-01"`
- `.planning/REQUIREMENTS.md` — NAV-01..06 Done (+26/-13 linhas)
- `.planning/ROADMAP.md` — checkboxes, item 34-04, Progress table (+16/-6 linhas)
- `.planning/STATE.md` — Current Position reescrita, histórico preservado (+40/-16 linhas)

## Decisions Made

Ver `key-decisions` no frontmatter. Nenhuma decisão de arquitetura nova nesta execução — a Task 1/2 executaram decisões já travadas nas fases anteriores; a única decisão desta sessão foi de **roteamento de processo**: o pedido novo do Alex (jornada + gráfico) não vira Fase 35 do v1.6 (o milestone está definido e fechado como Fases 33-34), vira candidato a `/gsd-new-milestone`.

## Deviations from Plan

**Nenhum desvio de escopo.** A única diferença notável em relação ao texto do plano: a suíte `.mjs` fechou em **153/153** nesta sessão (Task 3), não 152/153 como na Task 2 — `test_ios_assets.mjs` passou a existir e passar porque `web/ios/` foi gerado localmente por `scripts/instalar-iphone.sh` (rodado entre as Tasks 2 e 3, fora do escopo deste plano, a pedido do Alex — "Instalar ultima versao"). Registrado como melhoria incidental do ambiente, não como trabalho desta fase.

## Issues Encountered

Sandbox local bloqueou certificados TLS/rede na primeira rodada da suíte canônica desta sessão (27 falhas de pytest, `PermissionError`/timeout de rede) — mesma classe de falso-positivo já documentada em `worktree-test-setup.md` e nos SUMMARYs anteriores da fase. Confirmado ambiental: rodando fora do sandbox, 2923 pytest passed / 0 failed, contagem idêntica à baseline.

## User Setup Required

Nenhuma configuração de serviço externo necessária para o que este plano entrega. Pendência do usuário, já registrada: rodar `scripts/ios-testflight.sh` quando decidir levar a navegação nova ao app nativo; `web/.env.local` (copiar de `web/env-local.example`) se quiser testar login Google no build local instalado no iPhone nesta sessão.

## Next Phase Readiness

- **Fase 34 e milestone v1.6 fechados.** 13/13 requirements v1 (REORG-01..07 + NAV-01..06) Done, publicados em produção, documentos consistentes com a realidade.
- Próximo passo formal disponível: `/gsd-complete-milestone 1.6` (arquiva ROADMAP/REQUIREMENTS do milestone, evolui PROJECT.md).
- Próximo passo de produto, fora deste milestone: `/gsd-new-milestone` para o pedido do Alex sobre jornada do workspace + confiabilidade do gráfico de payoff (contexto completo, incluindo especificação técnica do motor de payoff e evidência de screenshot de produção, preservado na conversa — ainda não formalizado em `.planning/`).
- Pendências que sobrevivem ao fechamento, sem bloquear nada: app iOS/TestFlight (decisão do Alex), backlog B2 (D-03, aberto por desenho), 2 todos de bookkeeping em `pending/` já executados na Fase 33, avisos de lint pré-existentes em `web/src/opcoes/`.

---
*Phase: 34-navega-o-hub-workspace*
*Completed: 2026-09-20*

## Self-Check: PASSED

- FOUND: web/src/version.js (BUILD_ID F10-20260920-01)
- FOUND: .planning/REQUIREMENTS.md (NAV-01..06 Done)
- FOUND: .planning/ROADMAP.md (Fase 33/34 checkboxes, Progress table)
- FOUND: .planning/STATE.md (Current Position reescrita)
- FOUND: .planning/phases/34-navega-o-hub-workspace/34-04-SUMMARY.md
- FOUND commit: 927a2d7
- FOUND commit: 8944c71
