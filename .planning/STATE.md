---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: Opções v2
status: executing
stopped_at: Fase 17 — checkpoint humano bloqueante (Task 2 de 17-06-PLAN.md), aguardando o Alex
last_updated: 2026-09-06T18:00:00.000Z
last_activity: 2026-09-06
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 23
  completed_plans: 20
  percent: 40
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-06)

**Core value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.
**Current focus:** v1.5 (Redesenho de UI) shipped e arquivado em 2026-09-06 (ver `.planning/milestones/v1.5-*`); v1.4 (Opções v2) é o único milestone aberto — aguardando checkpoints humanos das Fases 17/18/19

## Current Position

Phase: 17 (checkpoint humano bloqueante, Task 2 de `17-06-PLAN.md`)
Plan: aguardando o Alex (mercado aberto + posição real elegível)
Status: In Progress — travado em checkpoint humano, não em execução
Progress: [████████░░░░░░░░░░░░] 40% (2/5 fases completas do v1.4; Fases 17/18/19 parciais)
Last activity: 2026-09-03 (última atividade real do v1.4 — o v1.5, shipped em 2026-09-06, não o tocou)

## Performance Metrics

**Velocity:**

- Total plans completed: 22 (v1.0) + 44 (v1.1) + 6 (Phase 9, standalone) + 8 (v1.2) + 8 (v1.3) + 8 (Phase 14, standalone)
- Average duration: -
- Total execution time: -

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 (v1.0) | 6 | - | - |
| 2-8 (v1.1) | 44 | - | - |
| 9 (standalone) | 6 | - | - |
| 0, 10, 11 (v1.2) | 8 | - | - |
| 12-13 (v1.3) | 8 | - | - |
| 14 (standalone) | 8 | - | - |
| 15-19 (v1.4) | TBD | - | - |
| 20-23 (v1.5) | TBD | - | - |
| 20 | 4 | - | - |
| 21 | 4 | - | - |
| 22 | 4 | - | - |
| 23 | 4 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- v1.4 roadmap (2026-09-02): numeração de fase continua a partir da última
  fase standalone (14, Opções lastreadas) — Phases 15-18, sem
  `--reset-phase-numbers`. v1.3 (12-13) e Phase 14 arquivadas em
  `.planning/milestones/`.

- v1.4 roadmap: 4 fases derivadas na ordem engine → estruturas → aceite →
  navegação — ENG-01..06 (Phase 15, motor sem UI) primeiro porque
  NAV-02/03 e FLOW-01 precisam do formato de saída do motor existir antes;
  LIB-01..03 (Phase 16) generaliza os motores single-leg já em produção
  (Fase 14) para N-pernas + collar; FLOW-01..04 (Phase 17) exibe a
  proposta via o mecanismo de card já existente (AtivoCard, Fase 14) antes
  da aba dedicada existir; NAV-01..03 (Phase 18) só entra por último, como
  casa definitiva de um fluxo que já funciona.

- v1.4 roadmap: Phase 16 success criteria deliberadamente distintos de
  Phase 15 — não repetem "o motor calcula payoff" (isso é Phase 15), e sim
  o que a biblioteca especificamente contribui (generalização N-pernas +
  collar como nova composição), correção feita após revisão do advisor
  antes de escrever os arquivos.

### Roadmap Evolution

- Milestone v1.5 roteirizado (2026-09-05): Redesenho de UI em 4 fases
  (20-23), numeração continuando a partir da Fase 19 do v1.4 (sem
  `--reset-phase-numbers`, diretórios 15-19 intocados). Fatoração: 20 =
  camada global/estrutural (FIX-01/02, SYS-04, TYPO-01/02/03, MOTION-03),
  porque mexe no shell/`GlobalStyle`/tokens que as outras três consomem;
  21 = duplicação removida e Portfólio consolidado (DEDUP-01/02/03,
  FIX-03 — mesmo componente `CapitalCurve` do DEDUP-01); 22 = componentes
  compartilhados (SYS-01/02/03), independente da 21; 23 = motion com
  propósito + ilustração (MOTION-01/02, ILUS-01), por último porque depende
  do gate de `prefers-reduced-motion` da 20 e dos componentes unificados da

  22. Nenhuma fase toca `server/app/*.py` nem contrato de API.

- Risco nomeado no roadmap do v1.5: as Fases 17/18/19 do v1.4 editam o mesmo
  `web/src/App.jsx` e não foram enviadas a `origin` nem verificadas ao vivo;
  publicar o front de qualquer fase do v1.5 empurra esse trabalho junto no
  mesmo bundle. A decisão a/b/c registrada em Blockers vale para o v1.5
  também.

- Milestone v1.4 aberto (2026-09-02): Opções v2 — nova experiência que
  propõe setups (venda coberta, put de proteção, collar) a partir da
  análise técnica sobre posições reais da carteira, independente do MCP
  externo (b-mcp) até ele ficar pronto. 4 fases: 15 (motor de proposta,
  sem UI), 16 (biblioteca de 3 estruturas), 17 (fluxo de aceite via card
  existente), 18 (aba própria "Opções" na navegação).

- Roadmap revisado em 2026-09-03, depois de verificar a Fase 15/16/17 e
  produzir mockup + revisão com `navigation-specialist` pra Fase 18: a
  barra inferior real tem 5 abas (não 4, presumido em 01/09) — Candidato A
  ("aba própria Opções") descartado. Fase 18 passa a ser "seção dentro de
  Posições" (tira "Oportunidades de opções" + detalhe por posição),
  validado em 2 iterações de mockup com o Alex (artifact
  `https://claude.ai/code/artifact/16ae7543-c58e-4b7f-b164-f8923efa431b`).
  NAV-01..03 reescritos em REQUIREMENTS.md pra essa forma.

- Fase 19 registrada em 2026-09-03 (decisão explícita do Alex: "Registrar
  como nova fase", em resposta a "no detalhamento da proposta deveríamos
  poder mostrar uma série de setups de opções para a análise do ativo") —
  o motor hoje devolve UMA estrutura por posição (regra fixa de
  `plano.decisao`, ENG-01, Fase 15 verificada, não reaberta); Fase 19
  generaliza pra N candidatos, aditivo sobre `opcoes_motor.rastrear()`/
  `avaliar()`. Novos requirements MULTI-01/02 em REQUIREMENTS.md, success
  criteria detalhados ficam pra `/gsd-plan-phase 19`. Ordem confirmada:
  Fase 18 (navegação, formato hoje single-candidato) primeiro, Fase 19
  (multi-candidato) depois — leitura literal da instrução do Alex, sem
  reordenar sem pedido explícito.

- v1.3 e Phase 14 (standalone) arquivadas em
  `.planning/milestones/v1.3-phases/` e
  `.planning/milestones/phase-14-opcoes-lastreadas/` nesta mesma sessão,
  já que o `/gsd-complete-milestone` anterior não tinha arquivado.

### Pending Todos

- `medir-rate-limit-mydata.md` (priority medium) — acompanhar volume real
  de tráfego de opções se crescer; sem relação direta com v1.4, mas o
  motor de proposta da Phase 15 consulta o hub mydata via o mesmo lock.

### Blockers/Concerns

- 3 itens de backlog pré-existentes bloqueados por dependência humana
  (verificação ao vivo de `entradaAuto`; 2 human-checks da Fase 3) — não
  relacionados a v1.4, seguem em PROJECT.md Active.

- **Fase 17, checkpoint humano (Task 2, `17-06-PLAN.md`) — ADIADO, não
  aprovado.** App local subiu sem erro (bump `F10-20260903-01`, suíte
  canônica 2010+web verde), mas o mercado estava fechado no momento da
  tentativa — cadeia de opções ao vivo indisponível pra exercitar o roteiro
  de 10 passos (payoff real, collar por caixa insuficiente, aceite/
  cancelamento, Radar vs. Watchlist, iPhone). Alex instruiu seguir pra Fase
  18 mesmo assim, risco aceito conscientemente — não é aprovação. Retomar
  o roteiro com o mercado aberto antes de considerar a Fase 17 fechada de
  verdade; push da Fase 17 pra origin segue não feito.

- **Fase 18, checkpoint humano (Task 2, `18-05-PLAN.md`) — PENDENTE, parcialmente
  exercitado ao vivo no iPhone (2026-09-03).** App local publicado com sucesso
  (bump `F10-20260903-02`, suíte canônica 2010+web verde depois da
  publicação). Build instalado no iPhone via `scripts/instalar-iphone.sh`
  (dev local, não TestFlight — localhost não tem dado de mercado real pra
  checar, motivo dado pelo Alex). Confirmado ao vivo, conta real com
  posições: a tira "Oportunidades de opções" aparece em Posições, mostra o
  estado vazio explícito correto (NAV-03) — texto de "cobertura líquida
  existe, mas nenhum setup técnico ativo hoje" (não o de falta de
  cobertura) — nenhuma caixa em branco/silêncio. Isso verifica o fan-out
  gate→proposta (hook `useOpcoesPropostas`, Plano 18-01) e a lógica de
  estado vazio (Plano 18-03) funcionando de ponta a ponta com dado real.
  **Ainda NÃO verificado** (nenhuma das posições reais do Alex tem proposta
  ativa hoje, então esses passos do roteiro de 10 seguem pendentes): tira
  COM item real, manchete idêntica à Watchlist, toque abre no card certo
  (NAV-02), aceite em Modo Operador, Modo Estudo sem CTA, collar por caixa
  insuficiente, Watchlist/Radar intocados. Decisão a/b/c sobre o risco
  herdado da Fase 17 também segue em aberto. Nenhum push pra `origin` foi
  feito. A fase não está fechada até o roteiro completo (o que exige um dia
  em que o Radar dispare um setup ativo sobre alguma posição real do Alex,
  ou teste num ativo/conta com proposta ativa).

- **Fase 19, checkpoint humano (Task 2, `19-04-PLAN.md`) — PENDENTE, não
  exercitado (2026-09-04).** Motor multi-candidato executado e publicado:
  `propor()` devolve `candidatos` (put_protecao + collar em paralelo quando
  ambos cabem, MULTI-01), rotas de leitura/escrita falam a língua de N
  candidatos e fecham o gap put→collar (MULTI-02), front renderiza os N
  lado a lado em `PropostaDaPosicao`/`CandidatoOpcao` reusando o padrão
  visual da Fase 18. Suíte canônica verde (2021 passed, 1 skipped + web
  ok), build `F10-20260904-01` publicado (`server/web_dist`, três elos de
  carimbo coerentes). **Roteiro de 10 passos do Plano 19-04 ainda não
  rodado** — exige mercado aberto E uma posição real com leitura
  VENDER/baixa cujo caixa comporte tanto a put isolada quanto a trava
  protetora (só assim os dois candidatos aparecem juntos); sem isso os
  passos 1-7 não são exercitáveis. Decisão a/b/c do passo 10 (publicar
  Fases 17+18+19 juntas / segurar até 17+18 fecharem / reprovar) segue em
  aberto — **esta fase amplia exatamente o mesmo fluxo de aceite que as
  Fases 17/18 ainda não confirmaram ao vivo**, então a decisão pendente
  cobre agora as três fases empilhadas, não só 19. Nenhum push pra
  `origin` foi feito.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260901-r5t | Registrar decisão: Alex escolheu Candidato A (aba própria Opções) na navegação de Opções v2 | 2026-09-01 | da9a118 | Verified | [260901-r5t](./quick/260901-r5t-registrar-decis-o-alex-escolheu-candidat/) |
| 260901-u2c | Registrar decisão: escopo v1 biblioteca de setups (venda coberta+put+collar), espaço pra MCP futuro | 2026-09-02 | f29490b | Verified | [260901-u2c](./quick/260901-u2c-registrar-decis-o-escopo-v1-biblioteca-d/) |
| 260902-km8 | Registrar estratégia de arquitetura: Boris independe do b-mcp até o serviço MCP autenticado ficar pronto | 2026-09-02 | 36cc1d1 | Verified | [260902-km8](./quick/260902-km8-registrar-estrat-gia-de-arquitetura-bori/) |
| 260905-1gb | Corrigir crash `cp is not defined` em HistoricoScreen (achado em auditoria de design ao vivo) | 2026-09-05 | 2715f9a | Verified | [260905-1gb](./quick/260905-1gb-corrigir-crash-cp-is-not-defined-em-hist/) |
| 260906-rla | Corrigir contraste WCAG AA de `textDim` no tema claro (Modo Estudo) — achado colateral da Fase 4/FIX-C16, 4,20:1→4,67:1; guardião de contraste estendido de `textFaint` para `textFaint`+`textDim` | 2026-09-06 | 503363f | Verified | [260906-rla](./quick/260906-rla-corrigir-contraste-wcag-aa-de-textdim-no/) |
| 260906-ugb | Corrigir 3 achados Baixo do REPORT-01: C-18 (`aria-describedby` no gate "Executar"), C-08 (reversão à média nomeada no verbete `setup-ifr2`); C-28 reverificado e encontrado já resolvido (nenhum código mudou) | 2026-09-06 | 9a874c5 | Verified | [260906-ugb](./quick/260906-ugb-corrigir-3-achados-baixo-do-report-01-c-/) |
| 260906-ugb | Corrigir 3 achados Baixo do REPORT-01 (C-18: `aria-describedby` no botão Executar desabilitado; C-08: princípio de reversão à média nomeado no verbete `setup-ifr2`; C-28: reverificado, já resolvido, zero mudança de código) | 2026-09-06 | - | Verified | [260906-ugb](./quick/260906-ugb-corrigir-3-achados-baixo-do-report-01-c-/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close (v1.3 → v1.4):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Backlog | 6 achados Baixo do REPORT-01 (C-06, C-07, C-09, C-10, C-17, C-29) — C-08 e C-18 corrigidos na quick task 260906-ugb (2026-09-06); C-28 reverificado e encontrado já resolvido (efeito colateral do refactor FIX-C21, sem mudança de código) | Not mapped to any phase — explicit backlog | v1.0 close |
| verification_gap | Item 8 do checkpoint 08-05 — verificação ao vivo de `entradaAuto` por um pregão inteiro | human_needed | v1.1 close |
| verification_gap | 2 human-checks da Fase 3 (card de status 3 badges reativo; mensagem de "sem permissão" do kill-switch) | human_needed | v1.1 close |
| v2 requirements | CAP-08..11 (loja/IAP, preço/moeda, IA gerenciada sem BYOK como paga, alvo dinâmico exclusivo do pago) | Deferred to future release — depende da decisão comercial de venda em si | v1.3 roadmap (2026-08-29) |
| Pending todo | `medir-rate-limit-mydata.md` (priority medium) | Ainda aberto pra acompanhar volume real de tráfego de opções se crescer | Fase 9 close (2026-08-27), rebaixado 2026-08-31 |
| v2 requirements (nomeado no kickoff) | Integração MCP real (Estratégia C, `plano-mcp-servico.md`) — troca o corpo de `rastrear()`/`avaliar()` (ENG-04 da Phase 15) sem reabrir requirements quando aprovado | Deferred — condicionado à aprovação do Alex | v1.4 roadmap (2026-09-02) |
| v2 requirements (nomeado no kickoff) | Setup customizado pelo usuário; estruturas adicionais além das 3 do v1 | Deferred — biblioteca fixa por enquanto | v1.4 roadmap (2026-09-02) |
| uat_gap | 20-HUMAN-UAT.md — 3 cenários pendentes (reduced-motion real MOTION-01/02/03; pulso de sucesso real de MOTION-02 em venda total) | partial — limitação de ferramenta (sem CDP Emulation.setEmulatedMedia) + mercado fechado durante toda a janela de execução | v1.5 close (2026-09-06) |
| uat_gap | 22-HUMAN-UAT.md — 1 cenário pendente (snap em DOM real dos 2 trilhos de opções sem dado de mercado ativo) | partial — prova estática completa via guardião, sem dado real disponível | v1.5 close (2026-09-06) |
| verification_gap | 20-VERIFICATION.md, 22-VERIFICATION.md, 23-VERIFICATION.md — status human_needed | Todos com evidência completa em código/bundle; pendência é só de confirmação humana ao vivo, ver .planning/milestones/v1.5-MILESTONE-AUDIT.md | v1.5 close (2026-09-06) |
| Tech debt (achado na auditoria de integração) | `numHero` (token de 34px da escala TYPO-02) sem consumidor real — `CapitalCurve` segue com fontSize hardcoded 27px | Decisão deliberada, documentada em 3 fases sucessivas (20/21/22) — não bloqueia, item de backlog para fase futura de polish | v1.5 close (2026-09-06) |
| Quick tasks pré-existentes (12, não relacionados ao v1.5) | 260820-0hl, 260823-vu4, 260823-x55, 260824-i45, 260824-kc2, 260830-eqm, 260901-1ak, 260901-2da, 260901-r5t, 260901-u2c, 260902-km8, 260905-1gb — todos status "missing" (sem SUMMARY.md) | Pré-datam o milestone v1.5; não fazem parte do seu escopo — não resolvidos nem descartados, seguem no backlog geral | v1.5 close (2026-09-06) |
| Pending todo | `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` (priority medium) | Acompanhar aprovação do serviço MCP autenticado — não relacionado ao v1.5 | v1.5 close (2026-09-06) |

## Session Continuity

Last session: 2026-09-06T22:55:00.000Z
Stopped at: Quick tasks 260906-rla (contraste WCAG AA de `textDim`) e 260906-ugb (C-18/C-08 corrigidos, C-28 confirmado já resolvido) concluídos; milestone v1.5 fechado e arquivado (`.planning/milestones/v1.5-*`); nenhum push a `origin`
Resume file: .planning/v1.5-MILESTONE-AUDIT.md (agora em .planning/milestones/v1.5-MILESTONE-AUDIT.md) — para o v1.4, ver `.planning/notes/checkpoints-pendentes-fase-17-18-19.md`

## Operator Next Steps

**v1.5 (Redesenho de UI) — SHIPPED, sem próximo passo mecânico.** 4 itens de
verificação humana pendentes, consolidados em
`.planning/milestones/v1.5-phases/20-funda-o-estrutural-e-tipogr-fica/20-HUMAN-UAT.md` — sem
urgência (nenhum bloqueia produto, ver `.planning/milestones/v1.5-MILESTONE-AUDIT.md`).

**v1.4 (Opções v2) — único milestone aberto, retomar quando o Alex puder:**
- Retomar o checkpoint humano da Fase 17 (`17-06-PLAN.md` Task 2) com o
  mercado aberto — payoff real, collar por caixa insuficiente, aceite/
  cancelamento, Radar vs. Watchlist, iPhone. Só depois considerar a Fase 17
  de fato fechada (e dar push pra origin).
- `/gsd-plan-phase 18` — seção "Oportunidades de opções" em Posições.
- `/gsd-plan-phase 19` — motor multi-candidato, depois da Fase 18 fechada.

**Depois do v1.4 fechar:** `/gsd-new-milestone` para decidir o próximo
milestone (nenhum roteirizado ainda além do v1.4).
