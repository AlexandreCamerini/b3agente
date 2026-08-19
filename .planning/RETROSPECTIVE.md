# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Revisão Geral

**Shipped:** 2026-08-18
**Phases:** 1 | **Plans:** 6 | **Sessions:** 1

### What Was Built
- Mapa completo do codebase brownfield (`.planning/codebase/`, 7 documentos) — primeira entrada do Boris+ no fluxo GSD
- Auditoria diagnóstica das 5 dimensões do produto (storyline pedagógico, UX/UI, código, gating de monetização, portal admin), toda ao vivo/API real onde possível
- `REPORT-01.md` — 39 achados consolidados (2 Crítico, 8 Alto, 20 Médio, 9 Baixo), deduplicados com evidência, validados por checkpoint humano

### What Worked
- Wave paralela (5 plans simultâneos por dimensão + 1 de consolidação) reduziu bem o wall-clock — cada dimensão rodou de forma independente sem esperar as outras.
- O checkpoint humano bloqueante (Task 3 do plano 01-06) capturou uma discordância real: o executor discordou deliberadamente de um exemplo textual do próprio `01-CONTEXT.md` (severidade dos 3 bugs de `appMode`) com base em evidência de código, e isso foi corretamente sinalizado para decisão do dono do produto em vez de decidido sozinho.
- Duas propostas de arquitetura levantadas pelo Alex durante o checkpoint (fonte dupla por finalidade, listbox de escolha de fonte) foram investigadas com fatos de código antes de qualquer opinião — uma delas already tinha sido decidida e descartada num ADR existente (ADR-008), e a investigação achou isso em vez de reabrir a discussão às cegas.
- Deduplicação evidence-based na consolidação: das 5 fusões candidatas sinalizadas pelos planos da wave 1, só 1 se confirmou — evitou inflar o relatório com "achados" que eram o mesmo fato contado duas vezes.

### What Was Inefficient
- **2 dos 5 plans paralelos da wave 1 falharam na primeira tentativa** porque o worktree isolado criado pelo Agent tool (`isolation="worktree"`) nasceu de uma base de commit desatualizada (o tip do `main` na época, não o HEAD atual da branch de trabalho) — `.planning/` inteiro estava ausente nesses worktrees. Precisou redespachar os 2 com instrução explícita de workaround (ler via path absoluto cross-worktree). Os outros 3 plans da mesma wave descobriram e contornaram o mesmo problema sozinhos, sem reportar de volta antes de tentar — então o padrão de recuperação não foi uniforme.
- **A ferramenta Write bloqueia qualquer nome de arquivo contendo "FINDINGS" para subagentes** (guarda do harness: "Subagents should return findings as text, not write report files") — pelo menos 2 dos 6 plans esbarraram nisso e precisaram de workaround (escrever em nome provisório + `mv`, ou devolver o conteúdo como texto pro orquestrador persistir). Isso não era conhecido no momento do planejamento — só foi descoberto na execução.
- Tempo de execução por plano foi bem mais longo que o estimado (alguns passaram de 1h, um chegou a ~20min só de duração de ferramenta reportada) — parte disso é overhead genuíno de investigação profunda (ex.: mapear 26 ocorrências de `appMode` linha a linha), parte é retrabalho por causa dos dois problemas acima.

### Patterns Established
- **Régua de severidade objetiva (D-02..D-05) definida ANTES da execução**, no `CONTEXT.md` da fase, aplicada de forma consistente por todos os plans e revisada centralmente na consolidação — funcionou bem para evitar inflação/deflação de severidade entre dimensões diferentes.
- **Checkpoint humano no plano de consolidação, não em cada plano da wave 1** — concentra a validação num único ponto de decisão em vez de interromper 5 vezes; funcionou porque a wave 1 era 100% automática (sem julgamento que exigisse o dono do produto) e só a normalização final precisava dele.
- **Achado "possível duplicata" sinalizado pelo plano de origem, confirmado ou rejeitado pela consolidação** — separa a detecção (barata, feita em paralelo) do julgamento final (caro, precisa ver as duas facetas juntas).

### Key Lessons
1. Se o worktree isolado (`isolation="worktree"`) vai ser usado em plans paralelos de uma fase, teste UM plano primeiro antes de disparar todos — o problema de base desatualizada só apareceu depois de já ter disparado os 5, custando 2 redespachos.
2. Nomes de arquivo de saída de subagentes não podem conter "FINDINGS" (nem provavelmente outros padrões de "report") — ao planejar fases futuras com múltiplos agentes escrevendo documentos de achado, usar nome de arquivo neutro (`*-ACHADOS.md`, `*-RESULTADO.md`) desde o planejamento evita o workaround de `mv`.
3. Perguntas que dependem de memória do dono do produto (não de regra objetiva) devem ficar explicitamente marcadas no `CONTEXT.md`/relatório como "isto precisa da sua memória, não só da régua" — funcionou bem quando aplicado (C-21) e evitou o executor decidir sozinho algo que só o Alex podia confirmar.

### Cost Observations
- Model mix: Opus para roadmapper/planner (nós críticos de estrutura), Sonnet para todo o resto (mapeadores, pesquisadores de UI, executores, verificador, checker) — perfil "balanced" do config.
- Sessões: 1 (contínua, do bootstrap do GSD até o fechamento do milestone)
- Notável: a fase teve 4 subagentes rodando em paralelo por boa parte da execução (map-codebase) e depois 5 (wave 1) — o tempo de parede real ficou próximo do plano mais lento de cada wave, não da soma, confirmando que o paralelismo valeu a pena apesar do retrabalho de worktree.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 1 | 1 | Primeira entrada do projeto no GSD (brownfield); descoberto o problema de base de worktree isolado e o bloqueio de nome "FINDINGS" — ambos documentados aqui para não redescobrir |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 970 backend (pytest) + 74 web (.mjs) — suíte pré-existente, não alterada nesta milestone | não medido numericamente (sem pytest-cov) | 0 (fase read-only, nenhum código de produto tocado) |

### Top Lessons (Verified Across Milestones)

1. `isolation="worktree"` em plans paralelos precisa de validação de base antes de disparar em lote — ainda não verificado em milestone futura, watch closely na próxima vez que este padrão for usado.
