# Milestones

## v1.7 Confiabilidade explicativa da aba Opções (Shipped: 2026-09-22)

**Phases completed:** 3 phases, 10 plans, 23 tasks

**Key accomplishments:**

- Dois estágios nomeados (porta de leitura → carril de pills), linha de transição quando a leitura já foi feita, e bug fix que liberava a pill "Setups salvos" do portão de leitura paga que ela nunca precisou.
- Os 3 CTAs que movem a jornada (Ler no serviço de opções, Montar estrutura, Ver possibilidades) passam do estilo neutro genérico a um preenchimento sólido de `T.accent` com texto `T.onAccent` (nunca `#fff` literal — reprova AA em 2 das 4 combinações tema×modo), e os dois re-clicáveis ganham uma marca `✓` discreta quando produzem resultado.
- A jornada guiada do workspace foi aprovada ao vivo pelo Alex — incluindo as 8 leituras de contraste nas 4 combinações tema×modo que fechavam o risco aberto de D-07 — e publicada em produção sob o carimbo `F10-20260921-01`. Fase 35 e milestone v1.7 (3/3 requirements desta fase) formalmente fechados.
- `opcoes_payoff.py` ganhou campo `vencimento` opcional por perna com degradação honesta em vencimentos divergentes (D-03), guarda de entrada degenerada (D-04.1) e correção do breakeven espúrio em S=0 que afetava CALL de prêmio zero, ratio spread de custo zero e box travado em zero (D-04.2), com 20 testes novos nomeados travando os casos-limite de PAYOFF-02.
- `opcoes_payoff.py` ganhou `dominio_da_curva()` (domínio X/Y do gráfico, D-05) e `segmentos_da_curva()` (leitura segmento a segmento cortando só nos strikes, D-06), e a fase fecha com o caso golden do Alex travado como regressão NOMEADA cobrindo as 5 propriedades de PAYOFF-03 e a independência de nome de estratégia provada por teste e por auditoria de leitura (PAYOFF-01).
- Adaptador rename-only (`_perfil_para_curva`/`_dominio_e_segmentos`) liga `POST /api/options/mcp/proposta` e `POST /api/options/mcp/possibilidades` a `opcoes_payoff.dominio_da_curva()`/`segmentos_da_curva()` (Fase 36), fechando CHART-04 — domínio X/Y do gráfico agora calculado no backend, nunca localmente pelo `PayoffChart.jsx`.
- Camada explicativa determinística do payoff (EXPL-01/02/03): 19 chaves novas de copy, `formatarRazao()` extraída como fonte única da razão ganho/perda, e `ExplicacaoPayoff.jsx` — componente React puro, zero I/O — que descreve todos os segmentos da curva de payoff em português leigo, o segmento do spot sempre primeiro.
- `_valor_hoje()` soma o prêmio ATUAL de cada perna via `get_option_chain` (sinal×quantidade×prêmio), anexado como `valorHoje` no envelope de `proposta()` (sempre) e `possibilidades()` (só o candidato de índice 0), corrigindo a regressão de produção onde "hoje" e "no vencimento" se confundiam no mesmo número.
- `PayoffChart.jsx` ganha eixo Y com escala visível de 2 casas decimais, strikes e spot marcados no eixo (reusando o algoritmo de colisão de 44px dos breakevens), setas de lado ilimitado com rótulo curto colado, e o par de blocos "No vencimento"/"Hoje · valor de mercado" — tudo opcional via 3 props novas que preservam os 3 consumidores reais existentes quando não passadas.
- `SecaoAnalisar.jsx`/`SecaoComparar.jsx` passam a passar `dominio`/`segmentos`/`valorHoje` ao `PayoffChart` corrigido (Plano 37-04) e a renderizar `<ExplicacaoPayoff/>` (Plano 37-02) — a onda de fechamento que torna CHART-01..05/EXPL-01..03 observáveis de ponta a ponta nos dois consumidores reais que um usuário vê, publicada em produção com carimbo `F10-20260922-01`.

---

## v1.6 Simplificação da aba Opções (Shipped: 2026-09-20)

**Phases completed:** 2 phases (33-34), 9 plans, 38 tasks. Git range
`f8346d5`→`1a83007`, 2026-09-19 19:37 → 2026-09-20 23:17 (~1 dia), 75
arquivos alterados, +9858/-1712 linhas.

**Key accomplishments:**

- Sub-aba "Setups" da aba Opções deixou de ser uma rolagem única com 5
  trabalhos misturados — cada job (Descobrir, Vigias, Analisar, Comparar,
  Setups salvos) passou a viver em componente próprio, sem nenhuma mudança
  de comportamento/dado/ordem visível ao usuário (Fase 33, REORG-01..07).

- Navegação hub+workspace substituiu a rolagem: hub sem ticker mostra
  descoberta cross-carteira + vigias; escolher um ativo abre o workspace
  com 3 pills (Analisar/Comparar/Setups salvos) compartilhando uma única
  leitura paga — trocar de pill nunca dispara nova chamada MCP, travado por
  guardião com prova negativa dupla (Fase 34, NAV-01..06).

- Um bug real de modelo de dados foi pego e corrigido ANTES de virar
  código: a decisão original (D-01) pedia listagem cross-ticker de "setups
  salvos" no hub, mas esse dado é ticker-scoped por construção
  (`leitura.dados`, sempre vazio com `ticker=""`) — corrigido substituindo
  por SecaoVigias, a listagem cross-ticker que já existia de verdade.

- Checkpoint humano ao vivo confirmou por medição real de rede (não por
  leitura de código) que trocar de pill dentro do workspace não paga de
  novo — o item mais frágil de NAV-05, verificado no navegador antes de
  publicar.

- Publicação combinada das Fases 33+34 (a 33 tinha fechado verificada em
  2026-09-16 mas nunca fora ao ar) sob o carimbo `F10-20260920-01`, com
  suíte canônica idêntica à baseline em todos os checkpoints (2923 pytest +
  152-153/153 `.mjs`).

- Disciplina de prova negativa por injeção pegou pelo menos 2 defeitos
  reais de guardião (asserções que ficariam inertes por colisão de
  homônimos em `SubAbaOperar`) antes de chegarem a produção.

**Known deferred items at close:** 54 flagged pela auditoria pré-fechamento
— 49 quick-tasks (`[missing]`) confirmadas já resolvidas por evidência
cruzada (`git log --all` + `STATE.md`, todas com commit e registro
histórico reais; status "missing" é artefato de índice, não trabalho em
aberto); 5 todos pendentes continuam abertos em `.planning/todos/pending/`
sem bloquear esta milestone (nenhum é requirement do v1.6), incluindo um de
prioridade alta (`revisao-arquitetura-mcp-ecossistema-b3.md`) que o Alex
optou explicitamente por tratar depois, não agora.

---

## v1.4 Opções v2 (Shipped: 2026-09-19)

**Phases completed:** 14 phases (15-19, 24-32), 63 plans, ~211 tasks — 13
fases integralmente completas, Fase 26 parcial (1/6 planos, por decisão de
escopo do produto)

**Key accomplishments:**

- Motor interno de N-pernas nasce atrás de um limite (`opcoes_motor.rastrear()`/`avaliar()`) no vocabulário do contrato ADR-004/`mydata_client.py` — payoff portado e testado de `calculos.py` (b-mcp), seleção pela régua `liquidity_score ≥ 40` + strike extremo já em produção (nunca o critério por delta do b-mcp), zero chamada de rede ao b-mcp, gatilho reusando o Radar/`setups.py` existente — trocável por chamadas reais ao serviço externo sem redesenho (Fase 15).
- Venda coberta e put de proteção migram do motor single-leg isolado da Fase 14 para o motor comum de N-pernas; collar nasce como terceira composição das mesmas duas pernas — prova de que o motor compõe estruturas de verdade (Fase 16).
- Fluxo de aceite: proposta mostra estrutura/pernas/prêmio/breakeven/ganho-perda máximos e fonte+horário do dado antes da decisão; aceite explícito executa pelo motor de ordens já em produção (`store.abrir_collar`, tudo-ou-nada numa única aquisição de `ORDER_LOCK`) — sem automação nova (Fase 17).
- Tira "Oportunidades de opções" agrega propostas ativas no topo de Posições, com detalhe completo por posição e estado vazio explícito — decisão de navegação (sem aba nova) que seria revertida quatro fases depois (Fase 18).
- Motor multi-candidato: `propor()` passa a devolver uma LISTA de candidatos elegíveis (venda coberta, put de proteção, collar) em vez de uma escolha única fixa; usuário aceita exatamente um por rodada, com exclusão mútua provada nas duas ordens (Fase 19).
- Aba Opções passa a ler o serviço `mcp.semente.dev` de verdade — cadeia, catálogo, proposta e possibilidades por vencimento com custo/ganho/perda em reais para o lote — mais criação de setups técnicos por descrição em português com ensaio (dry-run) antes de gravar; paridade `opcoes_payoff` × `evaluate_option_structure` confirmada contra dado real em produção pela primeira vez (Fase 24).
- Plano comercial vira eixo de produto: papel `owner` irrevogável (ancorado em e-mail, imune a revogação por qualquer rota), RBAC (administração) e plano (produto/limites) como eixos independentes, cinco pontos de controle de IA com limite configurável por plano via portal com precedência memória→kv→env→default, plano visível no app (Fase 25).
- Sete correções baratas de UX/IA shippadas (aba Opções visível ao assistente, KB antes da checagem de tela, tour cobrindo a tela de abertura, três textos mortos corrigidos) — mas só esta fatia ("Fase A") da fase, com cinco itens de backlog (B2/B3/C1/C2/C3) nunca executados e carregados adiante como dívida de produto, não escondidos (Fase 26, parcial).
- Universo da aba Opções vira a carteira do usuário — vigias (setups) persistem fora do ticker que os criou, leitura técnica (tendência/volatilidade/suporte-resistência) chega de graça pelo motor interno, reservando o serviço externo para o que só ele sabe sob clique explícito com custo declarado (Fase 27).
- Sub-aba "Operar" nasce dentro da aba Opções; `PropostaLastreada` (antes só dentro do card de ativo em Watchlist/Radar) é extraída para módulo compartilhado sem import cruzado (Emenda 3 ao ADR-027); o card de proposta lastreada some do card de ativo (Fase 28).
- Opção a descoberto exige flag opt-in em Configurações, default OFF para toda conta nova, mesma fricção (termo de responsabilidade versionado) do Modo Operador; fechar posição a seco já aberta nunca é bloqueado pelo flag (Fase 29).
- Bloco de curadoria de IA com as 4 melhores vendas cobertas da carteira por razão prêmio/perda máxima, escolha 100% determinística, custo ZERO do serviço externo, narração de IA sob a mesma cota mensal de `/api/analyze` (Fase 30).
- Varredura de oportunidades estendida de 1 estrutura×1 vencimento para as 4 estruturas do motor interno (venda coberta, put de proteção, collar, opção a descoberto) × até 2 vencimentos, com `PayoffChart.jsx` responsivo em 375px — consequência aceita e documentada: fórmula única de ranking deixa estruturas de prêmio negativo abaixo de qualquer venda coberta (Fase 31).
- Consolidação final: os quatro blocos de opções espalhados em Posições convergem para uma única linha de chamada; a aba Opções ganha os dois motores (interno determinístico custo-zero + serviço MCP custo-declarado) lado a lado sob uma frase-ponte permanente e nunca colapsável; as três cópias residuais do padrão `v * (X || 0)` corrigidas por guard explícito na mesma task, sem exceção de guardião sobrando (Fase 32 + quick `260916-g6p`).
- Auditoria de fechamento (2026-09-19): 18/18 requirements formais (Fases 15-19) mapeados como Complete, com duas ressalvas de verificação humana carregadas explicitamente em vez de apagadas — o roteiro completo de checkpoint das Fases 17/18/19 nunca fechou 100% ao vivo, e o item específico de multi-candidato lado a lado seguia sem confirmação em navegador real mesmo na verificação da última fase da milestone (`32-VERIFICATION.md`, 2026-09-16). Nenhuma fase foi reprovada ou revertida; Fase 26 é a única com escopo genuinamente parcial.

---

## v1.5 Redesenho de UI — simplificação e acessibilidade (Shipped: 2026-09-06)

**Phases completed:** 4 phases, 16 plans, 38 tasks

**Key accomplishments:**

- `.b3-shell`/`<main>` ganham `overflow-x:hidden` na regra de classe (não só no style inline), `MarketStatusBadge` trunca com reticência em vez de vazar layout, e `CONTENT_MAX_WIDTH` (720px) vira a única constante de teto de largura desktop, reusada pelo `BottomNav` que já a tinha (FIX-01, FIX-02, SYS-04).
- Escala numérica nomeada (`numHero`/`numBody`/`numMicro`) com `tabular-nums` no stack `MONO` chega a 151 sites de valor financeiro, e os 15 H1 de tela passam a usar `DISPLAY` (Fredoka), antes restrito ao wordmark (TYPO-01, TYPO-03).
- Um único `matchMedia` (`REDUCE_MOTION`) e exatamente 2 blocos `@media (prefers-reduced-motion)` em todo `GlobalStyle()` — travado por guardião de contagem exata, consumido depois pelas Fases 22/23 sem crescer (MOTION-03).
- `CapitalCurve` (card "Patrimônio simulado") passa a existir numa única tela em vez de duplicado em Acompanhar e Portfólio; os 4 cards soltos do Portfólio viram um grid 2×2 consolidado; o status do Operador IA para de repetir o que o toggle funcional já mostra — 3 guardiões pré-existentes que travavam o card duplicado reescritos com nota de reversão, nunca apagados (DEDUP-01, DEDUP-02, DEDUP-03).
- `CapitalCurve` ganha um placeholder dedicado para o limiar de 1-2 dias de patrimônio registrado, em vez de renderizar uma caixa vazia com escala degenerada (FIX-03).
- Helper único `carouselTrackStyle`/`carouselItemStyle` (scroll-snap + peek do próximo item) unifica os 4 trilhos horizontais do app que hoje divergiam entre si (SYS-01).
- `NavIcon` generalizado (size/color) substitui os 8 sites de emoji nativo do sistema operacional por SVG no mesmo traço da navegação — zero emoji na interface, confirmado por varredura Unicode (SYS-02).
- Sombra/halo do `PetFab` (mascote flutuante) vira token por tema (`PALETTE.{dark,light}.shadowFab`), confirmado nos 2 temas × 2 modos contra o bundle de produção — nunca mais parece cortado pela borda de um card atrás dele (SYS-03).
- Card novo (setup inédito na Watchlist/Radar) entra com fade+translateY (~200ms, `b3cardEnter`), sob o mesmo gate de `prefers-reduced-motion` da Fase 20 (MOTION-01).
- Confirmação de ordem (compra/venda EXECUTADA) dá um pulso de ~120ms (`b3valuePulse`) no valor antes de virar sucesso — pendente e rejeitada nunca pulsam — com portão `REDUCE_MOTION` em JS (não só CSS), provado sob teste adversarial de triplo-clique sem duplicar ordem nem caixa (MOTION-02).
- `BorisFlat.jsx` (nova ilustração flat/cartoon, cores e geometria copiadas do `LogoMark` já publicado) substitui o PNG semi-realista do modal "Este é o Boris" — ícone do app já publicado no TestFlight/App Store permanece intocado, confirmado ao vivo nos 2 temas e no Modo Operador (ILUS-01).
- Auditoria de milestone: 17/17 requirements satisfeitos, 16/17 pontos de integração cruzada `WIRED` com 2 fluxos E2E traçados ponta a ponta, status `tech_debt` não-bloqueante — débito técnico (`numHero` sem consumidor real) e 4 itens de verificação humana consolidados num único documento, nunca fragmentados por fase.

---

## v1.3 Cap comercial (plano gratuito) (Shipped: 2026-08-31)

**Phases completed:** 2 phases, 8 plans, 21 tasks

**Key accomplishments:**

- PLAN_FREE ganhou limites reais (10 ativos / 30 análises-mês) em `server/app/plan.py`, a recusa de watchlist perdeu o tom de CTA, e os dois guardiões pré-existentes que travavam "nenhum limite ativo" foram invertidos com nota de reversão rastreável.
- `PUT /api/watchlist` ganhou gate de plano que compara o tamanho FINAL normalizado (não o cru do body) e só bloqueia crescimento — fechando o bypass que permitia contas free ultrapassarem 10 ativos pelo catálogo, sem nunca recusar remoção, reordenação ou truncar contas grandfathered.
- Suíte de comportamento (10 testes) provando que o cap mensal de 30 análises nega de verdade nas duas rotas via o ledger real, mais registro da ativação técnica v1.3 no ADR-010
- GET /api/watchlist/quota expõe {count, limit, planId} lendo max_watchlist direto de plan.py, travado por 4 testes de contrato (free/anônimo/pro), mais limpeza de 2 resíduos textuais BolsIA→Boris+.
- watchlistQuota() nos dois stores lendo o endpoint real (sem hardcode de 10/30), gate fail-closed em deviceStore.addWatchlistTicker/putWatchlist fechando o bypass do CR-01 no app iOS nativo, e plan.js sem CTA de upgrade com o novo canGrowWatchlistTo espelhando can_grow_watchlist_to do backend.
- Helper `QuotaSeg` único (módulo React) renderizando o par uso/limite com 5 estados travados em 3 pontos da UI — subtítulo da Watchlist, CatalogModal e Atividade da IA — lendo `store.watchlistQuota()`/`store.aiQuota()` sem nenhum limite hardcoded, com guardião estático de 18 asserções incluindo uma mutação manual (T.warn→T.negative) que comprova o teste falha quando a decisão de cor é violada.
- Os dois itens que nenhum agente pode verificar sozinho fecharam com veredito explícito do Alex: o fragmento âmbar (`T.warn`) é legível no tema claro nos 3 pontos de exibição e nos 5 estados testados ao vivo (9/10, 10/10, indisponível, plano sem teto), e o nome exibido do app no App Store Connect — que estava "B3 Ai Agent", não "BolsIA" como o achado original supunha — foi corrigido para "Boris+".
- `server/web_dist` republicado a partir de um build real do front (BUILD_ID `F10-20260830-02`), com colisão de carimbo com um deploy só-backend do mesmo dia detectada e corrigida antes do commit; sincronização do bundle iOS não foi possível neste ambiente (`web/ios/` nunca gerado) e fica registrada nominalmente como pendência de TestFlight do Alex.

---

## v1.2 Camada de opções ancorada na carteira (Shipped: 2026-08-28)

**Phases completed:** 3 phases, 8 plans, 17 tasks

**Key accomplishments:**

- Fecha LEDGER-01: mapa de resolução (`ledger_tickers.py`) + retry de 404 escopado no bootstrap fazem os 74 tickers de `scanner.DEFAULT_UNIVERSE` atravessarem `signal_ledger_bootstrap` sem 404 residual — 2 renomeações confirmadas por série de preço contínua (MRFG3→MBRF3, EMBR3→EMBJ3), 5 exclusões documentadas (fusão/deslistagem/classe extinta) e 2 lacunas abertas e explícitas (ELET3/ELET6).
- Gate `_gate()`/`_debita()` em `options_provider_mydata.get_options` consultando/debitando `mydata_budget` antes de qualquer chamada de rede, com recusa DURA (degrada, não serve mole) — fecha OPTGATE-01/WR-01 com 10 testes novos de comportamento e nota aditiva no ADR-020.
- `put_suggestions` (tabela + módulo) grava sugestão de put comprada só quando estilo de exercício e IV vêm reais da fonte, e `put_bridge.triar_put` escolhe UM contrato determinístico de uma cadeia real ou devolve `None` com motivo exato — nenhuma chamada de rede, nenhum hook, nenhuma superfície visível.
- `put_bridge.run_diario` cruza o Radar diário já armazenado com as carteiras de todos os usuários, consulta a cadeia de opções sequencialmente (1x por ticker, teto de 10/dia) e grava uma sugestão de put por usuário com proveniência real — pendurado no `scheduler_loop` existente via hook próprio, sem scheduler novo, sem nada visível ao usuário.
- Um teste que lê o fonte (não um diff) prova, de forma permanente, que a ponte gatilho→put não alcança nenhuma rota HTTP, vocabulário, front, portal admin, telemetria do agente nem as agregações do Radar que o ADR-017 usa para ranquear setups — e o ADR-021 registra formalmente onde a sugestão mora, por que é long-only por construção, e a decisão pendente sobre WR-01 (race condition do gate de orçamento) que o Alex ainda precisa validar.
- `put_suggestions` ganha 11 colunas de ciclo de vida e `transicionar()` como única porta de escrita de estado (proveniência da Fase 10 comprovadamente imutável por essa porta), e `put_lifecycle.py` nasce como máquina de decisão pura que cobre as 5 transições do ROADMAP reusando literalmente `agent.intrinseco_opcao` — nenhuma chamada de rede, nenhum hook, nenhuma escrita na carteira real.
- `put_lifecycle.run_diario` varre diariamente toda sugestão de put não-terminal, resolve preço via `candle_cache.peek` (custo zero de rede) e aplica a máquina de decisão pura do Plano 01 através da única porta de escrita (`transicionar`) — pendurado no `scheduler_loop` já existente, FORA de qualquer gate de pregão/kill-switch/radar_fetch porque é medição interna, nunca execução de ordem.
- `test_put_lifecycle_sem_carteira.py` prova por COMPORTAMENTO — carteira montada via `db.kv_set` direto, nunca `store.buy_option`/`sell_option` — que um ciclo de vida completo (armada→executada_simulada→monitorada→fechada) deixa `optionPositions`/`cash`/`history` byte-idênticos, que nenhuma transição de estado fora do produto cartesiano declarado é gravável, e que nenhuma linha fica em limbo silencioso; ADR-022 e o runbook fecham os 4 requisitos da Fase 11 com evidência que sobrevive ao `.planning/`.

---

## v1.1 Realismo de Mercado + Correções (Shipped: 2026-08-23)

**Phases completed:** 7 phases, 44 plans, 105 tasks

**Key accomplishments:**

- Gap de ambiente pré-existente, não causado por este plano — mas com efeito

diferente do já documentado em 02-01/02-02:

- 1. [Rule 1 - Bug] Colisão de nome de variável quebrou um guardião existente
- 1. [Rule 1 - Bug] deviceStore.buy/sell não propagava `r.pendente` pra fora
- `/api/technicals/{ticker}` para de mentir a fonte do dado (Yahoo Finance fixo) e passa a expor `source`/`degradado` reais; TechnicalModal e FonteDadosScreen leem esses campos, fechando os 2 achados Crítico (C-11, C-30) do REPORT-01 que violavam o princípio 3 do CLAUDE.md.
- `candle_provider.get_quote` (singular) alinhado ao try/except já usado por `get_quotes` (plural) — erro de provedor vira `price: None` genérico em vez de HTTP 500 com URL/`crumb` vazando; painel admin "Orçamento brapi" ganha 3 linhas (vazios, taxa de falha, alerta) separadas de `erros`.
- Guardião estático que compara os 58 métodos de `deviceStore()`/`serverStore()` e falha em qualquer assimetria não declarada, e um card de 3 badges read-only no topo de "Operador IA" mostrando Modo do app · Operador no servidor · Executar/sinalizar, cada um lido da mesma fonte canônica que o card-herói.
- `current_plan(user)` deixa de ser código órfão nos 3 call sites de gate, e um único `_gate_analise` substitui os dois mecanismos de contagem (plan + metering) que coexistiam na mesma requisição — zero limite comercial ativado.
- `timing_watch.kill_switch_on()` ganha o mesmo padrão memória→DB→env do kill-switch do agente (ADR-013), com duas rotas admin RBAC-gated, campo em `/api/agent/status`, e o par `TimingWatchKillSwitchBox`/KPI "PUSH DO GATILHO" no portal — o 2º interruptor do sistema deixa de precisar de redeploy para ser revertido.
- Push ativo (APNs) a administradores com "ligado há Nh" quando o kill-switch do Operador está ligado em pregão, calculado best-effort do admin_audit_log e com ressalva explícita (nunca um número inventado) quando a ativação foi por variável de ambiente — mesmo texto no push e no portal admin.
- Conceito/verbete "diversificação" (FIX-C05) e módulo puro `explicacao_det.montar()` que compõe a explicação do Passo 7 a partir do snapshot técnico já calculado, sem nenhuma chamada de IA (FIX-C01) — motor pronto para a fiação de rotas do Plano 04-04.
- `store.registrar_rejeicao()` grava toda tentativa de ordem rejeitada no histórico sem mover dinheiro, e `server/app/benchmark.py` (novo) entrega fechamentos diários do Ibovespa via Yahoo com cache de 15 min — os dois pré-requisitos de estado para FIX-C02/FIX-C03, sem tocar nenhuma rota.
- Os 4 hex de `textFaint` corrigidos para WCAG AA real (medido nas 3 superfícies, não só bgBase), o acordeão de opções com Enter/Espaço/aria-expanded, e um aviso soft (nunca bloqueio) antes de ativar o Modo Operador sem nenhuma análise feita no Estudo.
- As duas rotas de análise nunca mais devolvem 502 por falta de IA (fallback determinístico via `explicacao_det`), `/api/buy`/`/api/sell` gravam toda rejeição de conta logada no histórico antes do erro, e `GET /api/benchmark/ibov` expõe a série do Ibovespa — os 3 contratos de resposta fixados no PLAN.md, verificados também com o servidor real no ar (não só TestClient).
- Disclaimer de operação simulada e declaração tudo-ou-nada plugados nos dois modais de trade, AiNote deixa de afirmar "conteúdo de IA" sobre texto determinístico, e uma ordem rejeitada agora aparece no histórico com pill neutra + motivo, na web e no app nativo.
- `equityCurve` passa a expor `datas` por ponto e `benchmarkSerie` alinha o Ibovespa por data real (sem inventar/extrapolar); o Passo 8 (CapitalCurve) desenha as duas séries na mesma escala com uma 4ª célula "VS. IBOVESPA" — o número que responde "foi bom ou ruim?" — e degrada com uma frase única quando o índice não vem, sem nunca contaminar a leitura da carteira.
- `concentracaoMaxima()` (aritmética pura, mesma família de `portfolioMetrics`) alimenta um card `T.warn` no `CarteiraScreen` que avisa — sem bloquear nada — quando um único ativo passa de 50% do patrimônio simulado, com "saiba mais" abrindo o verbete `diversificacao` (backend do Plano 04-01) ancorado no ticker e no percentual reais da carteira: fecha FIX-C05 e tira "diversificação" da lista de conceitos obrigatórios do CLAUDE.md com zero ocorrência no produto.
- Dois arquivos de teste novos travam 4 caminhos de rejeição HTTP descobertos em /api/buy e /api/sell (FIX-C25) e a reponderação de preço médio na recompra após venda parcial com avg=35.00 travado contra o valor errado 33.75 (FIX-C26) — zero mudança em server/app/.
- Ledger mensal dedicado em `metering.py` substitui o `0` hardcoded no gate de análises (FIX-C33); nova função pura `alerta_gasto` compara o gasto de hoje contra a média da janela e alimenta `/api/obs/usage` com um alerta configurável pelo admin, complementar ao hard stop já existente (FIX-C38).
- `catalog.js` reconciliado byte a byte com `defaults.py` (11 princípios, acentuação, Contrato de saída) e travado por guardião Python + migração automática de aparelhos com texto legado, sem tocar em edição do usuário.
- `scripts/executar.sh --testes` resolve `web/node_modules` sozinho e mostra a causa real de falha web; ADR-018 decide não adotar E2E agora, com 4 gatilhos objetivos de reavaliação.
- Migração mecânica de 7+3 leituras redundantes de `appMode` para a fonte única `ctx.operador`/`appMode`, e atributo HTML `disabled` real no Toggle mestre de Entrada automática, ambos travados por guardião estático.
- Aba Custos do web-admin passa a mostrar o alerta preventivo de gasto de IA (4 estados, tom âmbar no cruzamento do limiar) que o backend já calculava desde o Plano 05-02, e a aba Auditoria ganha declaração explícita de regra de acesso via sentinela `PERM_ANY`, sem alterar o acesso real.
- `analisesNoMes()` nos dois stores lê `monthUsed` do ledger do servidor (mesmo endpoint de `aiQuota()`, sem contador paralelo no aparelho); `A.analyze` substitui `canAnalyze(0)` hardcoded por essa contagem real com falha-aberta documentada; FIX-C34 fechado por confirmação (sem UI nova) de que o Copywriting Contract da Fase 3 segue sem vazar orçamento/cota/limite ao usuário final.
- BUILD_ID F10-20260822-01 → F10-20260823-01; `server/web_dist` e `server/admin_dist` republicados com todas as correções de front da Fase 5; commit local feito (`caf714b`); `git push` para origin/main deliberadamente NÃO executado por este agente — fica para o orquestrador, seguindo o mesmo padrão de merge usado nas 7 waves anteriores da fase.
- `analysis_outcomes.registrar` grava entrada/alvo2/rr2/confluencia/entradaAMercado do N1 (com metodologiaVersao=2), e só confluencia do N2 — puramente aditivo, sem migrar registro antigo.
- `_avaliar_entry` passa a exigir toque no gatilho para plano de rompimento (âncora `gatilho`), abre a barreira no candle 0 para plano a mercado (âncora `mercado`), preserva o caminho legado/N2 (âncora `preco`) byte a byte, e o desfecho novo `sem_gatilho` sai do denominador nos dois consumidores que contam "resolvido" (`compute_stats` e `automacao.correlacao_analise_operacao`).
- `compute_stats` passa a filtrar por metodologia (default = atual), declara o legado excluído e segmenta resolvidos por âncora; `compute_stats_all_users` deduplica por `snapshotId` (modo-independente no N1, modo-dependente no N2) antes de agregar; os critérios 1/2/4 do ROADMAP e a entrada ADR15-01 do REQUIREMENTS foram emendados com o texto literal que os Planos 01/02/04 deixaram prontos.
- `sell()` de ação passa a gravar `motivo` ('manual'|'stop'|'alvo'|'vencimento'), mesmo contrato de `sell_option()` desde o ADR-005; o único call site automático em `agent.py` passa o motivo real derivado de `breach_stop`/`hit_alvo`.
- `setups.RR_MINIMO` e `agent.RR_MINIMO` passam a ler de `skill_ref.RR_MIN`; `web/src/finance.js` exporta `RR_MIN`/`RR_MIN_TXT`; dois guardiões cruzados novos (Python `test_a8iii` e JS `test_rr_min_fonte_unica.mjs`) amarram os 2 motores + 3 arquivos de front + `skill_ref.py` — valor continua 1,5, nenhum comportamento de gate mudou.
- Guard universal de granularidade do Yahoo (`yahoo.confere_granularidade`, todos os intervalos não-intraday) e promoção do replay determinístico/barreira tripla para `server/app/signal_replay.py`, com `scripts/backtest_sinal.py` reduzido a wrapper fino — fecha os dois pré-requisitos que o ledger, bootstrap e hook diário da Fase 7 dependem.
- Tabela `signal_ledger` no banco principal + `server/app/signal_ledger.py` com gravação idempotente, as duas agregações SQL carimbadas (cumulativa e por janela anual, piso `n≥40`) e um provedor de histórico com cache em processo (TTL 300s) que nunca propaga exceção de banco.
- `server/app/signal_ledger_bootstrap.py` — comando manual `python -m app.signal_ledger_bootstrap` que roda o replay determinístico (15 anos × 74 tickers) e grava no ledger, reexecutável via UNIQUE do schema, sem replay próprio, com runbook completo para local e `railway ssh`.
- `candle_cache.peek()` (leitura sem rede) + `server/app/signal_ledger_job.py` completo: avanço incremental do ledger com cursor derivado do próprio dado, gate diário no padrão de `radar_daily`, e fechamento de janela anual alinhado ao calendário da B3 — hook pronto e testado, ainda não pendurado no `scheduler_loop` (isso é o Plano 06).
- `detect_setups()` ganha campo informativo `historico` por setup via provedor injetado (default `None`, sem I/O no caminho quente) e `regime.ranquear()` passa a somar ±10 ao `radarScore` e usar a elegibilidade da janela anual fechada como novo termo de ordenação, entre momentum relativo e gatilho de timing — sem esconder nenhum setup e sem inverter o eixo de regime/momentum validado no ADR-016.
- `signal_ledger_job.maybe_run` pendurado no `scheduler_loop` (depois de `radar_daily`/`fundamentals`, try/except próprio) e `setups.set_historico_provider` ligado no boot de `main.py` — o histórico medido pelo ledger (Planos 01-05) passa a chegar de fato ao Radar em produção, fechando o Bloco 1 do ADR-017 em código; falta só a verificação ao vivo (Task 3, checkpoint humano bloqueante).
- `skill_ref.HISTORICO`/`HISTORICO_ROTULO`/`ENTRADA_AUTO` com os 6 estados do histórico medido por setup (ADR-017 Bloco 3), espelhados byte a byte em `copy.js`, travados por guardião cruzado com sabotagem controlada validada.
- A entrada automática do Modo Operador volta a existir, mas só executa o setup que a seleção dinâmica (ledger, Fase 7) mediu como elegível na janela anterior fechada — sem lista hardcodada, hoje restrito a 5 pares setup×lado (123 de fundo alta, IFR2 alta, PFR alta, Setup 9.1 alta, Setup 9.3 alta), e nenhum deploy foi feito neste plano.
- Componente `HistoricoPill` (6 estados, cor via UI-SPEC, aria-label sempre presente) alimentado por `historicoEstado`/`historicoDesatualizado` puras em `finance.js`, ligado ao `AtivoCard` (Watchlist) e ao `RadarScreen` — o dado que `/api/scan` já entrega desde a Fase 7 finalmente aparece no nível do ticker.
- `HistoricoPill` reusado no nível SETUP (não só ticker) dentro de "Ver critérios do setup", com carimbo de tempo e frase de disponibilidade da entrada automática por setup (`entradaAutoTxt`, mesmo predicado `elegivel is True` do 08-02); card de status único do Operador (C-19) ganha a linha agregada `cp.entradaAuto.regra/.contraste` — guardião novo com sabotagem controlada validada em 4 cenários.
- Task 1 completa: suíte canônica verde, front buildado, BUILD_ID F10-20260821-01 → F10-20260821-02, publicado em `server/web_dist` e commitado localmente (`efa2ca9`) — nenhum comando de produção executado. Task 2 é um checkpoint humano bloqueante (`gate="blocking"`) apresentado ao Alex nesta mesma entrega, ainda SEM aprovação: o agente não pode nem deve resolvê-lo sozinho.

---

## v1.0 Revisão Geral (Shipped: 2026-08-18)

**Phases completed:** 1 phases, 6 plans, 13 tasks

**Key accomplishments:**

- Jornada real dos 8 passos da Experiência Principal exercitada ao vivo via API (conta isolada, PETR4, compra real de 100 ações), produzindo 10 achados evidenciados (nenhum Crítico/Alto — 5 Médio, 5 Baixo) e confirmando ao vivo que o guardrail CVM da manchete determinística está conforme.
- Auditoria ao vivo dos 10 princípios obrigatórios do CLAUDE.md contra o Boris+ real (backend uvicorn + Vite, dados de mercado reais), com 9 achados evidenciados incluindo um rótulo de fonte de dado hardcoded e factualmente errado no painel técnico (violação direta do princípio 3).
- Dívida técnica auditada em profundidade (10 achados F-CODE-01..10, com 1 Alto: paridade `deviceStore`/`serverStore` sem guardião exaustivo — já causou 2 incidentes reais); a narrativa de causa-raiz dos 3 bugs históricos do `appMode` foi corrigida com evidência linha a linha.
- Achados evidenciados por grep real: `current_plan(user)` nunca é chamado (código órfão), `can_add_ticker`/`can_analyze` caem no `ACTIVE_PLAN` global em vez do plano do usuário, `can_analyze` e `metering.check` são gates concorrentes na mesma rota, e o estado `degradado` da cota brapi (TTL 3x) é invisível a usuário e admin — violação do princípio 3 do CLAUDE.md.
- 4 achados brutos (3 Alto, 1 Médio) na dimensão ADMIN: o segundo kill-switch (`timing_watch`) é invisível no portal e sem toggle em runtime, o painel de custos não mostra o modo de falha silenciosa do provedor de dados que já causou incidente real em produção (31/07/2026), a aba Auditoria diverge visualmente das outras 9 por não ter campo `perm` (mas o backend já gateia corretamente), e não existe alerta por duração do kill-switch ligado — o mecanismo que teria encurtado o incidente real de 2,5 dias.
- Relatório único de 39 achados (2 Crítico, 8 Alto, 20 Médio, 9 Baixo) consolidando as 5 dimensões da auditoria do Boris+, com severidade normalizada pela régua D-02..D-05, deduplicação evidence-based (só 1 de 5 fusões candidatas se confirmou) e validação humana do Alex no checkpoint.

---
