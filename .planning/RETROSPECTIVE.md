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

## Milestone: v1.1 — Realismo de Mercado + Correções

**Shipped:** 2026-08-23
**Phases:** 7 (2-8) | **Plans:** 44 | **Sessions:** 2+ (contínuas, com handoff de contexto no meio)

### What Was Built
- Fases 2-5 (REPORT-01): status real de pregão + ordens fora de horário
  (Fase 2); os 2 Crítico + 8 Alto (Fase 3); os 20 Médio, split por coesão —
  STORY/UX (Fase 4) e CODE/GATE/ADMIN (Fase 5)
- Fases 6-8, nascidas de pesquisa ad-hoc sobre o motor de recomendação
  (não do REPORT-01): instrumentação de assertividade que revelou o motor de
  setups com expectância negativa (ADR-015/016), seleção dinâmica por
  desempenho histórico — ledger, bootstrap, hook diário (ADR-017 Bloco 1,
  Fase 7) — e a interface + religamento gated do Modo Operador (ADR-017
  Bloco 3/4, Fase 8)
- 3 achados reais descobertos só na EXECUÇÃO, não no planejamento: iPhone
  rodando persona de IA divergente da web (FIX-C22), gate comercial sem
  contador mensal real (FIX-C33), Yahoo silenciosamente devolvendo velas
  mensais em vez de diárias/semanais (achado que motivou o guard universal
  de granularidade da Fase 7)

### What Worked
- **plan-checker com "extra scrutiny" explícito no prompt** — pedir
  verificação pontual de alegações específicas do planner (não só o
  checklist padrão) pegou discrepâncias reais repetidas vezes: aritmética
  errada num teste (FIX-C26, ×1 vs ×10 por causa da normalização de lote),
  citação de linha errada num UI-SPEC (off-by-one), e confirmou 7 achados
  de descoberta da Fase 5 contra o código ao vivo, não só a palavra do
  planner.
- **UI-SPEC com sign-off explícito pra exceção de padrão** — quando um
  checker bloqueia por "valor fora do grid declarado" mas o valor É um
  reuso legítimo de padrão já existente, a exigência de citar `file:line`
  + a frase literal `developer-approved — matches existing pattern —
  {data}` (só depois de EU mesmo verificar a citação contra o código real)
  aconteceu 3 vezes (Fases 4, 5, 8) e nunca deixou passar uma citação
  inventada — pegou até uma citação genuinamente errada (Fase 5, "8px"
  quando o valor real era 7px).
- **CONTEXT.md manual via ADR-ingest quando o parser automático falha** —
  `adr-parser.cjs` não reconhece o formato "Decisão N" usado nos ADRs deste
  projeto (retorna 0 decisions); escrever o CONTEXT.md à mão, citando
  evidência original linha a linha, funcionou bem nas Fases 7, 4 e 5 sem
  precisar de `discuss-phase` interativo.
- **Correção de critério ANTES de codar** — o Alex rejeitou o critério
  original de aposentadoria de setup (|t|, ADR-017 Bloco 0) com uma crítica
  estatística rigorosa em Plan Mode; a correção pro critério certo
  (magnitude econômica em faixas) aconteceu inteiramente em planejamento,
  sem nenhuma linha de código pra desfazer depois.

### What Was Inefficient
- **Push prematuro em fase com checkpoint bloqueante (Fase 8)** — hábito
  herdado de fases sem checkpoint (6, 7) de dar `git push` depois de cada
  wave colocou o gate de `entradaAuto` em produção horas antes da aprovação
  do Alex. Exposição real avaliada como zero (feature desligada em todas as
  contas), mas foi sorte de contexto, não desenho — o checkpoint existia
  exatamente pra prevenir isso. Corrigido a partir da Fase 5 (regra
  registrada em memória, aplicada corretamente no fechamento do 05-08).
- **Fase sem task de publicação do front (Fase 4)** — os 7 planos fecharam
  os 9 achados com suíte 100% verde, mas nenhum publicava
  `server/web_dist`. Ficou testado, mergeado e commitado, mas INVISÍVEL em
  produção até eu notar manualmente (`git log -- server/web_dist` mostrando
  o último commit de uma fase anterior). Corrigido antes de fechar a fase
  (commit `f2ef08e`); a Fase 5 já nasceu com plano de publicação desde o
  planejamento (05-08).
- **3 checkboxes de requirement nunca atualizados** (ADR15-03, ADR15-04,
  ADR17-B1-03) — código e teste já existiam, só o `[ ]`→`[x]` do
  REQUIREMENTS.md não foi feito quando as respectivas fases fecharam. Só
  achado ao investigar diretamente uma pergunta do Alex ("tem algo
  crítico?") — sem essa pergunta, teria ficado invisível até o fechamento
  do milestone (que também os pegou, no `audit-open`).
- **Falso alarme de bug crítico por metodologia própria (Fase 7)** — um
  teste de verificação via `railway ssh python3 -c "..."` esqueceu
  `from app import main` (o import que dispara a fiação real no boot);
  pareceu que o campo `historico` não estava chegando em produção. Corrigido
  ao perceber que cada `railway ssh` é um processo Python novo, não o
  servidor real rodando — mas custou uma investigação completa antes de
  perceber que o "bug" era do meu próprio script de teste, não do produto.

### Patterns Established
- **Checkpoint humano bloqueante represa o push da FASE INTEIRA**, não só
  da task do checkpoint — nenhuma wave anterior pode ter ido ao ar antes da
  aprovação, mesmo que o commit isolado pareça inócuo.
- **Fase que toca `web/src/` precisa de task explícita de
  bump+publicar-web.sh** — verificar isso no planejamento, não confiar que
  "suíte verde" implica "em produção".
- **Verificação de campo/valor "ao vivo" via processo novo (`railway ssh`)
  não é o mesmo que o servidor real** — se o teste depende de estado de
  boot (providers injetados, conexões configuradas), replicar a MESMA
  sequência de import do processo real (`from app import main` primeiro),
  não só importar o módulo isolado que se quer testar.
- **Achado de execução vira requirement rastreável antes de escrever
  código**, não só uma nota de rodapé no SUMMARY — os 3 achados reais desta
  milestone (C-22, C-33, guard do Yahoo) todos ganharam requirement/task
  formal antes de codar, não foram só "corrigidos de passagem".

### Key Lessons
1. Regra de push em fase com checkpoint bloqueante: represar a fase
   INTEIRA, verificar isso explicitamente antes de dar push em QUALQUER
   wave, não só a última.
2. Plano que toca frontend sempre precisa de um item explícito de
   build+publish no checklist de planejamento — "suíte verde" não implica
   "publicado".
3. Ao pedir a um subagente pra verificar uma alegação de outro subagente,
   pedir verificação PONTUAL de itens específicos (não só "confira o
   plano") — as descobertas mais valiosas desta milestone vieram de
   perguntas de escrutínio extra formuladas pelo orquestrador, não do
   checklist padrão do checker.
4. Perguntar "tem algo crítico?" de vez em quando, mesmo sem sinal de
   problema, vale a pena — foi assim que os 3 checkboxes desatualizados
   apareceram, antes do fechamento formal do milestone os pegar de
   qualquer jeito.

### Cost Observations
- Model mix: Opus para planners (nós de estrutura/decisão), Sonnet para
  pesquisadores de UI, executores, checkers e verificadores — perfil
  "balanced", consistente com v1.0.
- Sessões: pelo menos 2, com handoff de contexto no meio (a sessão
  continuou depois de compactação de contexto, sem perder rastreabilidade
  — STATE.md/ROADMAP.md como fonte de verdade permitiu retomar sem
  releitura manual do histórico).
- Notável: fases com 3-5 planos paralelos por wave (Fases 5 e 8, 5 planos
  na wave 1) tiveram wall-clock próximo do plano mais lento da wave, não da
  soma — o padrão de paralelismo continua valendo a pena, e o problema de
  base desatualizada do worktree (achado na v1.0) NÃO reapareceu nesta
  milestone — a mitigação (push antes de spawnar a wave seguinte) segurou.

---

## Milestone: v1.2 — Camada de opções ancorada na carteira

**Shipped:** 2026-08-28
**Phases:** 3 (0, 10, 11 — numeração não-sequencial deliberada) | **Plans:** 8 | **Sessions:** 1 (execução autônoma noturna contínua)

### What Was Built
- Fase 0 (precondição): 9 tickers 404 do bootstrap do ledger resolvidos com
  evidência real (2 renomeações confirmadas por série de preço, 5 exclusões
  documentadas, 2 deixadas honestamente `INDETERMINADO`); gate de orçamento
  no caminho de opções do mydata, fechando um achado da Fase 9.
- Fase 10: ponte gatilho→put — hook diário seleciona put de proteção com
  dados reais do hub (nunca assumidos), grava numa tabela nova isolada
  (`put_suggestions`), invisível ao usuário e dormente em produção até a
  virada da Fase 9 acontecer.
- Fase 11 (última): máquina de 5 estados para o ciclo de vida da sugestão,
  com a decisão de arquitetura mais substantiva da milestone — a leitura
  literal do ROADMAP ("reusa optionPositions") foi corretamente rejeitada
  com evidência de código (escreveria na carteira REAL, visível), em favor
  de reusar só os CONTRATOS/fórmulas em colunas isoladas.

### What Worked
- **Contrato de autonomia explícito, com hard-stops e viés de desempate
  nomeados antes de começar** — "menor, reversível, mantém invisível"
  funcionou como critério de decisão real em pelo menos 2 momentos que
  teriam virado pergunta ao Alex em execução normal (onde a tabela nova
  deveria morar; se o hook do ciclo de vida deveria respeitar o
  kill-switch). Ambos decididos com evidência de código citada, não
  suposição, e ambos sobreviveram à verificação independente.
- **Cada fase fechou com code review + verificação de objetivo
  independentes, mesmo sem humano no loop** — 3 achados reais (1 Crítico,
  4 Warnings) só apareceram nessa dupla checagem, não no planejamento nem
  na execução original. O padrão "planner→checker→executor→reviewer→
  verifier", cada papel numa chamada de agente separada, pegou bugs de
  correção real (chave de ledger não-normalizada, ticker malformado
  abortando o dia inteiro) que um único agente fazendo tudo teria a maior
  chance de deixar passar.
- **UAT persistido como arquivo, não como pergunta perdida** — quando a
  verificação da última fase voltou `human_needed` (2 divergências do texto
  literal do ROADMAP + 2 achados de baixo impacto), gravar os itens em
  `11-HUMAN-UAT.md` com `status: pending` e fechar a fase mecanicamente
  mesmo assim (sem fingir aprovação) preservou a pergunta real para quando
  o Alex voltasse, sem travar a noite inteira nem mascarar a divergência.

### What Was Inefficient
- **Divergência de indentação não pega por nenhum dos dois checkers** — o
  plan-checker da Fase 11 verificou a inserção do hook contra o `agent.py`
  MERGADO da Fase 10, mas o plano em si (escrito antes do merge) copiou o
  texto literal de um trecho que, depois do merge real, ficava DENTRO do
  gate de kill-switch — só o executor, rodando contra o código real no
  momento da execução, percebeu a contradição com os próprios requisitos do
  plano. Nenhum processo quebrou (o executor corrigiu e documentou como
  D-EXEC-11-02-01), mas é um lembrete de que verificação contra o código
  real precisa acontecer o mais tarde possível na cadeia, não só na
  criação do plano.
- **Aritmética de critério de aceite quebrada 1x** (Fase 10, `grep -c '^+'`
  contando a linha de cabeçalho `+++` do diff) — pego pelo plan-checker
  antes da execução, mas é o tipo de erro mecânico que um teste do próprio
  critério (rodar o grep contra um diff sintético antes de publicar o
  plano) teria pego mais barato ainda.

### Patterns Established
- **Contrato de autonomia por escrito, com PROIBIDO/PARADA DURA/viés de
  desempate nomeados**, não implícito — quando a execução precisa rodar sem
  humano por horas, a especificidade das restrições (não "seja cuidadoso",
  mas "nunca chame `store.buy_option`") é o que faz a decisão autônoma ser
  verificável depois, não só bem-intencionada.
- **UAT como arquivo com `status: pending`, nunca como aprovação
  fabricada** — fechar a fase mecanicamente (sem bloquear a noite) enquanto
  o arquivo de UAT continua genuinamente pendente é diferente de "aprovar
  por mim mesmo" — a distinção importa para auditoria depois.
- **Achado de review corrigido no mesmo commit da fase, com guardião
  novo e nota "Fixed post-review" no REVIEW.md** — mantém o REVIEW.md como
  registro histórico do que foi encontrado (não reescreve o achado) e ainda
  assim deixa óbvio que foi resolvido, sem precisar caçar o commit de
  correção em outro lugar.

### Key Lessons
1. Contrato de autonomia funciona melhor com hard-stops NOMEADOS
   (condições específicas, não "pare se algo parecer errado") e viés de
   desempate explícito — ambos usados de verdade nesta milestone, não só
   documentados.
2. Verificação contra o código MERGADO (não contra o plano nem contra um
   snapshot anterior) é o que pega divergência de indentação/estrutura —
   nem plan-checker nem planner viram isso a tempo; só o executor, rodando
   por último, contra o real.
3. UAT `pending` genuíno (não aprovação fabricada) é o mecanismo certo
   para fechar trabalho mecanicamente sem mascarar uma decisão que só o
   humano pode tomar — a fase fechou, o milestone não foi marcado Shipped,
   e a pergunta sobreviveu exatamente como feita até o Alex responder.

### Cost Observations
- Model mix: Opus para os 3 planners (nós de estrutura/decisão mais
  substantivos da milestone), Sonnet para researchers/executores/checkers/
  reviewers/verifiers — mesmo perfil "balanced" de v1.0/v1.1.
- Sessões: 1 sessão contínua, execução autônoma noturna (~8h de wall-clock
  entre início do roadmap e fechamento da Fase 11), sem handoff de
  contexto — o padrão de ScheduleWakeup + task-notification sustentou o
  ciclo planner→checker→executor→reviewer→verifier por 3 fases sem
  intervenção humana.
- Notável: nenhum push em nenhum momento da execução autônoma (81 commits
  locais acumulados) — o guardrail "sem push" do contrato de autonomia
  segurou por toda a noite; o push/fechamento de milestone só aconteceu
  depois do Alex validar o UAT pela manhã.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 1 | 1 | Primeira entrada do projeto no GSD (brownfield); descoberto o problema de base de worktree isolado e o bloqueio de nome "FINDINGS" — ambos documentados aqui para não redescobrir |
| v1.1 | 2+ | 7 (2-8) | Primeira milestone com checkpoints humanos bloqueantes em produção (Fases 7, 8, 5) e com fases nascidas de descoberta em execução, não só do planejamento original (Fases 6-8, a partir de pesquisa ad-hoc sobre o motor de recomendação) — mitigação do worktree da v1.0 (push antes de spawnar wave seguinte) confirmada eficaz, zero recorrência |
| v1.2 | 1 (autônoma) | 3 (0, 10, 11) | Primeira milestone executada de ponta a ponta sem humano no loop (contrato de autonomia explícito, hard-stops nomeados) — nenhum push durante toda a execução (diferente de v1.1, onde push por wave era o padrão); UAT `human_needed` fechado como arquivo `pending` genuíno em vez de aprovação fabricada, resolvido pelo Alex numa sessão separada antes do fechamento formal do milestone |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 970 backend (pytest) + 74 web (.mjs) — suíte pré-existente, não alterada nesta milestone | não medido numericamente (sem pytest-cov) | 0 (fase read-only, nenhum código de produto tocado) |
| v1.1 | 1365 backend (pytest) + suíte web completa (.mjs), ambas verdes no fechamento — crescimento de ~395 testes backend na milestone | não medido numericamente (sem pytest-cov) | 0 (nenhuma dependência nova — confirmado por `git diff` de todo `package.json`/`package-lock.json` em cada plano que tocou frontend) |
| v1.2 | 1674 backend (pytest) + suíte web completa (.mjs), ambas verdes em toda validação de wave — crescimento de ~135 testes backend (candle/opções/ledger/put_bridge/put_lifecycle) | não medido numericamente (sem pytest-cov) | 0 (nenhuma dependência nova — backend-only, nenhum `package.json` tocado) |

### Top Lessons (Verified Across Milestones)

1. `isolation="worktree"` em plans paralelos precisa de validação de base antes de disparar em lote — **confirmado como mitigação eficaz na v1.1**: dar `git push` antes de spawnar cada wave seguinte eliminou completamente a recorrência do problema descoberto na v1.0.
2. Checkpoint humano bloqueante represa o push da FASE INTEIRA, não só da task do checkpoint — descoberto por incidente real na v1.1 (Fase 8), aplicado corretamente daí em diante (Fase 5).
3. Fase que toca frontend precisa de task explícita de build+publish no planejamento — "suíte verde" não implica "publicado em produção" (achado na v1.1, Fase 4).
4. Execução autônoma sem push (v1.2) é uma variante mais segura do que push-por-wave (v1.1) quando não há humano pra aprovar em tempo real — o contrato de autonomia explícito (hard-stops nomeados, viés de desempate declarado) é o que torna a ausência de checkpoint humano segura, não a ausência de checkpoint em si.
5. UAT `human_needed`/`pending` genuíno, persistido em arquivo e fechado mecanicamente sem aprovação fabricada, é o padrão certo para separar "trabalho mecânico concluído" de "decisão que só o humano pode tomar" (v1.2, Fase 11) — generaliza o padrão de UAT já usado desde v1.1 (Fases 3, 08-05) para o caso específico de execução autônoma.
