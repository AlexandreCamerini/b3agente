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
Last activity: 2026-09-10 — **aba Opções EM PRODUÇÃO** (`F10-20260910-01`, confirmado: `/api/options/mcp/leitura/{t}` responde 401 em vez de 404, e o bundle servido na raiz é o publicado). Cadeia MCP provada funcionando no log de produção (`check_data_freshness` em 1-2 s, `bloqueia=False`) — as falhas `McpIndisponivel` eram todas anteriores às 13h de 10/09. **Achado do dia: `railway logs` sem `--environment production` lê STAGING nesta máquina, e foi por isso que o diagnóstico ficou horas travado.** Também no ar: conserto do cabeçalho da aba (260910-d57) e a guarda de `qty` inválido em `/api/buy` (260910-mqs, achado A-00 da auditoria — bug pré-existente, sem relação com opções). Auditoria completa em `docs/AUDITORIA-2026-09-10.md`. Pendências decididas com o Alex: lote do MCP (A-01 a A-06), cota de IA que estoura sob concorrência (A-07), agente anunciando venda que não houve (A-08), dois guardiões provados cegos (A-17/A-18), e o mesmo vazamento de ValueError em `/api/options/buy` que ficou fora do commit do A-00 de propósito.

Anterior (2026-09-08, tarde) — quick 260908-ldg, gate de liquidez em três faixas com consentimento, mesclada e testada (2110 passed). Junto com 260908-dnl (recalibração do score) fecha o achado do dia: opções estavam apagadas em produção por um gate impossível de cruzar com mydata. Front republicado junto no `F10-20260908-02` (o servidor passou a exigir `aceitaLiquidezDificil`; front velho quebraria). PR #32 mesclado e PROMOVIDO em 2026-09-08 — `/api/health` = `F10-20260908-02`, gate ao vivo confirmado (PETR4/ABEV3/VALE3/ITUB4 NEGOCIÁVEL, RADL3 DIFÍCIL 50,9). Produção tinha ficado em `F10-20260907-01` até então: o #31 foi mesclado mas nunca deployado, e o -02 o contém.

Anterior no mesmo dia — as QUATRO quick tasks de 07/09 consolidadas numa publicação só (`F10-20260908-01`, commit 7be6b55, branch empurrada). Todas nasceram da mesma sessão de teste ao vivo em staging/iPhone: 260907-w33 (largura do card de candidato), 260907-x69 (textos do card de fechamento), 260907-vwl (aviso de ordem pendente) e 260907-vzp (setup aposentado, ADR-017). Suíte canônica verde nas duas suites: 2049 passed, 1 skipped.

`origin/main` foi mesclado ANTES do bump — era o que travava a publicação. Ao mesclar, a branch `claude/gallant-volhard-b8dcdb` trouxe um bump para `F10-20260907-01`, o MESMO carimbo que produção já servia, para código diferente: a colisão prevista, resolvida para `F10-20260908-01` (que nunca foi ao ar). Lição operacional: sessão paralela que roda `bump.sh` sem estar em dia com `origin/main` sempre reemite o carimbo de produção — o script deriva do valor LOCAL.

PROMOÇÃO FEITA em 2026-09-08 (PR #32 → main → Deploy manual pelo Alex). O único comando contra o GitHub foi `gh pr merge 32`, autorizado explicitamente; nenhum comando tocou o Railway. Próxima verificação humana: o confirm de consentimento de liquidez no aparelho, e os checkpoints das Fases 17/18/19 que seguem abertos.

RESSALVA HONESTA: a verificação foi estática (suíte + build). As quatro correções nasceram de achados ao vivo, mas nenhuma foi reconfirmada no aparelho depois do fix — o cenário depende de mercado aberto e posição elegível, a mesma dependência que trava os checkpoints das Fases 17/18/19.

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

- **Opções apagadas em produção pelo gate de liquidez — RESOLVIDO e EM PRODUÇÃO
  (F10-20260908-02, deploy 2026-09-08; gate ao vivo confirmado).** Com `B3_OPTIONS_PROVIDER=mydata`
  o `liquidity_score` perdia o `oi_score` inteiro (COTAHIST não publica open
  interest) e levava a penalidade de 25 por "spread desconhecido"; teto 35
  contra corte 40, impossível em qualquer volume — os 60 contratos de PETR4
  empatavam em 35,0. Quick `260908-bzf` mediu; `260908-dnl` recalibrou o score
  (volume carrega sozinho, OI substitui quando existe, livro byte-idêntico);
  `260908-ldg` trocou o corte binário por TRÊS FAIXAS com consentimento
  explícito em DIFÍCIL e bloqueio servidor-side em SEM MERCADO — o usuário
  vê o grau e decide, o simulador nunca inventa um fill. Contra as 20 cadeias
  reais: 282 NEGOCIÁVEL / 227 DIFÍCIL / 83 SEM MERCADO. PR #32 mesclado e promovido em 2026-09-08; `/api/options/gate/PETR4` devolve
  `liquida: true, faixa: NEGOCIÁVEL, melhorScore: 75`. Pendência humana:
  exercitar o confirm de consentimento no aparelho (nunca tocado ao vivo). Pendência de raiz (open interest de verdade) é ingestão do MyData.
  Números: `docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md`.

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
| 260906-vf9 | Corrigir 3 achados de PRODUTO do REPORT-01 (C-07: "Operador IA" nomeado em `ModoTrabalhoCard`; C-09: aviso de drawdown >15% em `CapitalCurve`, limiar decidido pelo orquestrador; C-06: `resumoOperacao(h)` — escopo reduzido a uma frase no Histórico existente) | 2026-09-06 | 72187df | Verified | [260906-vf9](./quick/260906-vf9-corrigir-3-achados-de-produto-do-report-/) |
| 260907-w33 | Corrigir estouro de largura do card de candidato de opção (achado ao vivo em staging/iPhone com put_protecao + collar): `flex: "0 0 210px"` nos dois trilhos de opções, CUMPRINDO a Decisão 1 do 22-UI-SPEC em vez de revertê-la — `minWidth` sempre foi piso, nunca teto. Guardião da asserção 7 intocado. Publicado em F10-20260908-01 | 2026-09-07 | (merge) | Published | [260907-w33](./quick/260907-w33-corrigir-estouro-de-largura-do-card-de-c/) |
| 260907-x69 | Corrigir os textos do card de FECHAMENTO de operação lastreada (achado ao vivo em staging/iPhone): a manchete de fechar uma put dizia "Comprar 1 put(s)…" acima de um botão que VENDE, e o CTA/confirmação falavam em "recomprar a call" e "destrava ações" para uma put que nunca travou ação. Frases `fechar_call_coberta`/`fechar_put_protecao` nos DOIS modos de `skill_ref`; `tipo`/`motivo` intocados (contrato de ~9 guardiões de igualdade exata). O dinheiro já estava certo (`side=="comprada"` → `store.sell_option`, credita) — defeito só de texto. **Dois guardiões afirmavam o texto errado** e foram atualizados com nota datada, não apagados. Publicado em F10-20260908-01 | 2026-09-07 | a90e0bf | Published | [260907-x69](./quick/260907-x69-corrigir-textos-do-card-de-fechamento-de/) |
| 260908-bzf | Documentar que o gate de liquidez de opções ficou IMPOSSÍVEL de cruzar com `B3_OPTIONS_PROVIDER=mydata` (medido em produção ao vivo): os 60 contratos de PETR4 empatam em `liquidity_score=35,0` contra corte 40 — `oi_score` some (COTAHIST não publica open interest) e a penalidade de spread cai no padrão 25 porque o livro vem com um lado zerado. Teto 35 < corte 40, nenhum volume cruza. Fecha o follow-up aberto do ADR-020. **Documentação apenas** — recalibrar o gate é decisão de produto, adiada pelo Alex | 2026-09-08 | — | Documented | [260908-bzf](./quick/260908-bzf-documentar-gate-de-liquidez-impossivel-c/) |
| 260908-dnl | Recalibrar `liquidity_score` para fonte sem open interest (opção 1, escolhida pelo Alex logo após a bzf): atividade = `max(curva(volume), curva(OI))` numa curva única até 75, livro byte-idêntico, corte 40 inalterado; piso sem livro = 1.000 unidades (onde a curva original saturava). Primeira candidata (penalidade de desconhecido 10) descartada por virar pass-through nas 20 cadeias reais. Contra produção: gate 18/18 (antes 2/18), 461/592 contratos (antes 3/592). Dois guardiões atualizados com nota datada, guardião novo com critérios fixados antes dos dados; mock fiel ao mydata (OI None, volume 5000) em commit separado. Suíte 2064 passed. **Em produção desde 2026-09-08 (F10-20260908-02)** | 2026-09-08 | (2 commits) | Deployed | [260908-dnl](./quick/260908-dnl-recalibrar-liquidity-score-para-mydata-s/) |
| 260908-ldg | Gate de liquidez em TRÊS FAIXAS com consentimento (quadro confirmado pelo Alex): NEGOCIÁVEL ≥55 normal · DIFÍCIL 30–54 aparece com a nota, só é selecionado se não houver negociável, e exige `window.confirm` próprio + `aceitaLiquidezDificil: true` no corpo (servidor recusa 400 sem o flag) · SEM MERCADO <30 bloqueado sem override (princípio 4). Limiares centralizados em `options_quant` (55/30, `faixa_de_liquidez`); `rastrear` em duas passadas; `proposta.liquidez` ganha faixa/volume/spreadPct/aviso com frase de `skill_ref` nos dois modos; ramo OFFLINE do `deviceStore` aplica a mesma régua (era o buraco real de paridade); verbete determinístico `liquidez-opcao`; guardião AST prova que o agente não abre estrutura. Fechamento NÃO bloqueia por faixa (deliberado). 12 guardiões atualizados com nota, 46 novos; plan-checker pegou 2 fatos errados do planner (fixture do collar é mista 67/53; 1.000 un. sem livro é DIFÍCIL). Contra as 20 cadeias reais: 282/227/83; RADL3 cai na 2ª passada. Suíte 2110 passed. **Em produção desde 2026-09-08 (F10-20260908-02); gate ao vivo confirmado — PETR4/ABEV3/VALE3/ITUB4 NEGOCIÁVEL, RADL3 DIFÍCIL 50,9** | 2026-09-08 | (3 commits + merge) | Deployed | [260908-ldg](./quick/260908-ldg-gate-de-liquidez-em-tres-faixas-com-cons/) |
| 260909-bwm | Script master de distribuição iOS (`scripts/distribuir-iphone.sh`): localiza o worktree onde `main` está checked out (`git worktree list --porcelain` — este worktree não pode `git checkout main`), fast-forward de `origin/main` (diverge → morre, nunca merge/rebase automático), suíte canônica antes de empacotar, builda contra PRODUÇÃO (nunca staging), sincroniza, e SÓ ENTÃO pergunta o canal — Xcode direto no aparelho × TestFlight. Flag `--no-open` nova em `instalar-iphone.sh` (compat total sem ela). Nunca flipa APNs pra produção sozinho — lê `aps-environment` e avisa se TestFlight for escolhido com push ainda em development. `bash -n` OK nos dois scripts; localização do worktree testada isoladamente (resolve certo). **Rodado ao vivo pelo Alex logo depois**: achou um bug real (caminho do entitlements no resumo final, `ios/App/App.entitlements` faltando um nível `App/` — sempre imprimia "ausente" mesmo com o valor certo no arquivo), corrigido no mesmo dia (commit `60cd0e0`, PR #34, mesclado). Rodou de novo com `--testflight`: canal escolhido corretamente, build 10 gerado, resumo agora lê `aps-environment: development` de verdade | 2026-09-09 | (2 commits) | Deployed to main, run live | [260909-bwm](./quick/260909-bwm-script-master-atualizar-main-e-instalar-/) |
| 260909-dao | Documenta no `TESTFLIGHT.md` (item 7) que o **App Name** do App Store Connect é único NA LOJA INTEIRA, diferente do `CFBundleDisplayName` (nome sob o ícone, continua "Boris+"). Achado ao vivo: "Boris+" sozinho colidiu ("App Record Creation failed... already being used") — vários apps "Boris" já publicados. Alex escolheu **"Boris+ Simulador B3"** entre 4 variantes apresentadas. Documentação apenas, nenhum código tocado | 2026-09-09 | — | Documented | [260909-dao](./quick/260909-dao-documentar-nome-boris-simulador-b3-no-ap/) |
| 260907-vwl | Reforçar aviso visual de ordem pendente (achado ao vivo em staging/iPhone 2026-09-07 — compra de ABEV3 com mercado fechado, aviso "discreto" passou batido): bloco `color-mix(T.warn 14%)` reusando o pill PENDENTE, des-concatenado da frase de execução tudo-ou-nada, simétrico em BuyModal/SellModal; guardião estendido | 2026-09-07 | d78a0a5 | Tested (suíte canônica verde, sem --validate) | [260907-vwl](./quick/260907-vwl-reforcar-aviso-visual-de-ordem-pendente-/) |
| 260907-vzp | Corrigir `setups[0]` cru sem filtrar aposentado em `App.jsx` (ADR-017 Decisão 1) — achado ao vivo em staging (compra ABEV3 gravou `setupEntrada` contraditório, invertendo a leitura de invalidação); `setupOperavel()`/`metaDeEntrada()` em `finance.js`, espelho de `setups.py:725` | 2026-09-07 | ebd23b2, e8dd43e | Verified | [260907-vzp](./quick/260907-vzp-corrigir-setups-0-cru-sem-filtrar-aposen/) |
| 260909-oyu | Carimbo de horário das ordens em BRT (era UTC no Railway): `store.now_str()` (histórico de compra/venda, `abertaEm` das posições, 17 usos) e `main.now_str()` (cotações `at`, agent log, análises — 15 usos) usavam `datetime.now()` naive; container Railway em UTC → 3h à frente e, das 21:00 às 23:59, no dia seguinte. `obslog.ts` idem. Formato das strings preservado; registros antigos não reconvertidos. Guardião cruza a meia-noite UTC. Pendência mapeada: `candle_provider.py:61` e `scan_deep.py:29` (dia local como chave de "hoje") | 2026-09-09 | 88ba707, b129c4f | Tested (suíte canônica verde: 2114 pytest + 124 mjs) | [260909-oyu](./quick/260909-oyu-carimbo-ordens-brt/) |
| 260909-th4 | Bump manual de `SERVER_BUILD_ID` → `F10-20260909-01` para o deploy só-backend da correção de fuso (260909-oyu). `version.js` fica em `-20260908-02` por desenho. Deploy é clique do Alex no Railway; próximo bump de front hoje tem que ser explícito (`bump.sh F10-20260909-02`) | 2026-09-09 | 403d1a7 | Verified (import + pytest -k health) | [260909-th4](./quick/260909-th4-bump-server-build-id-fuso/) |
| 260909-tmi | Pedido do Alex: "mude todos os domínios para boris.semente.dev". Código/scripts já eram boris; trocados os remanescentes `bolsia.semente.dev`, `acamerini.app` e `b3-production-8fc0` em doc viva, comentários e fixtures (11 arquivos). Histórico protegido intocado. `mydata.acamerini.app` → `mydata.semente.dev` (outro serviço). Pendente FORA do repo: valor de `B3_GATED_HOSTS` no Railway e return URLs SIWA/Google | 2026-09-09 | abfa21c | Tested (suíte canônica: 2114 pytest + 124 mjs) | [260909-tmi](./quick/260909-tmi-dominios-para-boris-semente-dev/) |
| 260909-waw | **Aba Opções — Fase 1** (PLANO-aba-opcoes aprovado 2026-09-09): ADR-027 substitui a fronteira do ADR-024 (só serviço autenticado `mcp.semente.dev`, dado real, nunca fixture); `mcp_client.py` único importador de `mcp`/`httpx2` (token client_credentials à mão, cache, semáforo 4, mapeamento de erros); `options_mcp_api.py` com `GET /api/options/mcp/status`, cap por usuário/dia em seções próprias do `metering` (`mcpUsage*`, dia em SP); permissão `opcoes.criar_setup`; pins exatos de fastapi/starlette/pydantic/uvicorn (provado em 3.12 via pip download); guardiões A/B reescritos com nota. Decisão a avalizar: `/status` responde 200 com `bloqueia:true` em erro de tool. Achado alto deferido: `test_adr013_cobertura_rotas` cego a rotas de `include_router` no fastapi 0.141 | 2026-09-09 | 0568271, 0a38cda, 63d038b | Tested (2225 pytest + 124 mjs) | [260909-waw](./quick/260909-waw-aba-opcoes-f1-adr027-cliente-mcp/) |
| 260910-biz | **Aba Opções — Fase 2**: rotas `GET /api/options/mcp/leitura/{ticker}` (behavior+catalog+expirations+setups do ticker, estado `nao_avaliado` com motivo verbatim) e `/setups/{name}/grafico`; front novo em `web/src/opcoes/` (OpcoesScreen, SetupChart, useOpcoesMcp) + `chartutil.js` extraído; **Opções entra na barra no lugar de "Operador IA", que virou sub-tela do Portfólio** (`goAgente`, `carteiraView === "agente"`). 3 guardiões atualizados com nota (pet_ui, benchmark_curva, c07). Desvio: `paletteFor()` extraída porque `usePalette()` fora do Provider leria a paleta default | 2026-09-10 | 3aff231, 404f8e6, 3be7a30, 5de774c | Tested (2239 pytest + 126 mjs + vite build) | [260910-biz](./quick/260910-biz-aba-opcoes-f2-leitura-setups-troca-de-aba/) |
| 260910-d57 | Dois defeitos do cabeçalho da aba Opções, achados no teste ao vivo no iPhone: (1) o chip de frescor nascia com "não medido" como default e afirmava medição que nunca houve quando nenhuma resposta chegou — agora distingue as TRÊS origens (nada consultado omite o chip; `medido:false` mantém o texto, que aí é verdade; `medido:true` em dia/atrasado), e a fonte deixou de afirmar `mcp.semente.dev` sem resposta; (2) `leitura.erro \|\| status.erro` fazia o 404 da leitura mascarar o `mcp_nao_configurado` do status — agora `escolherErroOpcoes()` escolhe por acionabilidade (`code` conhecido do ADR-027 vence erro sem código). Guardião estendido com prova red/green | 2026-09-10 | b79ef75 | Tested (2239 pytest + 126 mjs + vite build) | [260910-d57](./quick/260910-d57-cabecalho-opcoes-chip-e-erro/) |
| 260910-mqs | **Achado CRÍTICO A-00 da auditoria de 2026-09-10**: `POST /api/buy` aceitava `qty` negativo ou zero e EXECUTAVA a ordem (`-500` era coagido ao lote mínimo por `max(100, ...)`, e o mesmo `max` em `pending_orders.criar_compra` engolia o negativo no ramo fora de pregão); `qty` não numérico vazava `ValueError` como 500. Guarda espelhando `/api/sell` (F10-20260819) e `/api/options/buy`, posta depois do ticker normalizado e ANTES de `get_quote` (pedido inválido não queima requisição do orçamento brapi). Contrato de `qty` ausente (lote 100) preservado e travado por teste. 5 testes novos, provados RED antes e GREEN depois. **Sem relação com a aba de Opções** | 2026-09-10 | 45fdbe3 | Verified (RED/GREEN + suíte 2244 pytest + 126 mjs) | [260910-mqs](./quick/260910-mqs-buy-qty-negativo-a00/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close (v1.3 → v1.4):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Backlog | 3 achados Baixo do REPORT-01 sem correção (C-10, C-17, C-29) — C-08 e C-18 corrigidos na quick task 260906-ugb (2026-09-06); C-28 reverificado e encontrado já resolvido (efeito colateral do refactor FIX-C21, sem mudança de código); C-06/C-07/C-09 (achados de PRODUTO, não Baixo) corrigidos na quick task 260906-vf9 (2026-09-06) — C-06 com escopo reduzido (frase no Histórico existente, não tela nova) e C-09 com limiar de drawdown de 15% | Not mapped to any phase — explicit backlog | v1.0 close |
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
Stopped at: Quick tasks 260906-rla (`textDim`), 260906-ugb (C-18/C-08/C-28) e 260906-vf9 (C-06/C-07/C-09, achados de produto) concluídos — todos os 9 achados Baixo/produto do REPORT-01 fechados ou reverificados; milestone v1.5 fechado e arquivado (`.planning/milestones/v1.5-*`); nenhum push a `origin`
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
