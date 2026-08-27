# Decisions (from ADRs)

19 ADR-classified documents were ingested (`docs/adr/001-*.md` through `019-*.md`). Every entry below is one ADR — one decision record, not deduplicated across ADRs (precedence/conflict analysis is in `../INGEST-CONFLICTS.md`, not applied here).

Legend: **status: locked** = classification `locked: true` (ADR `Status: Aceito`/`Accepted`/`Implementado`, or "Aceito em direção" treated as locked per classifier note). **status: proposed** = classification `locked: false` (ADR `Status: Proposto`/awaiting decision or approval).

---

## ADR-001: Fonte de dados intraday e onde esse dado vive
- source: `docs/adr/001-fonte-de-dados-intraday.md`
- status: **locked** (Aceito, 2026-07-31)
- scope: dados intraday B3, Yahoo Finance, `CandleProvider`, brapi Pro, `candle_cache`, `merge_candles`, `snapshotId`, `scheduler_loop`, granularidade 15m, cobertura de 65 ativos, instrumentação de fetch
- decision:
  1. **Provedor**: Yahoo Finance é a fonte primária de dado intraday, atrás de uma interface `CandleProvider`; brapi Pro é plano B documentado, não implementado. Orçamento aprovado: US$ 0/mês. Gatilho declarado para reabrir a decisão: taxa de falha de fetch intraday > 2% em janela de 3 pregões (FALHA = não-200 OU 200 com série vazia).
  2. **Granularidade**: 15 minutos, sobre velas FECHADAS (nunca a vela em formação). O atraso do feed é constante (~15 min), não escalável pela granularidade — "engrossar a barra piora a informação". Toda afirmação de timing carrega o carimbo da barra e o horário de fechamento (obrigação de interface).
  3. **Cobertura**: os 65 ativos que o Yahoo serve, varridos uma vez por ciclo global (não por usuário/watchlist) — custo O(1) em usuários. 9 ativos (ELET3, ELET6, JBSS3, EMBR3, CPLE6, CRFB3, NTCO3, MRFG3, BRFS3) dão 404 em qualquer intervalo, item separado, não resolvido por este ADR.
  4. **Persistência**: intraday vive só em memória do processo (L1), sem write-through pro SQLite — redeploy/restart perdem e refazem em ~0,45s. Correção obrigatória: chave da vela em `merge_candles` precisa ser timestamp completo no fuso de bolsa, não `%Y-%m-%d`/`gmtime` (bug que colapsava 96% dos candles em silêncio).
  5. **Identidade/instrumentação**: intervalo entra na identidade do snapshot (`_snapshot_id`, `_SNAP_CACHE`); fetch intraday instrumentado (`/api/obs/usage`).
  6. Restrição de produto amarrada aqui: timing só aparece no Modo Operador, vocabulário descritivo, nunca verbo de ordem.
- a revisitar: se a lacuna de 3h do feed (achado do dia 31/07) se repetir → Decisão 1 volta à mesa; se taxa de não-200 > 2%/3 pregões → aciona plano B; se F3 exigir histórico intraday → Decisão 4 volta à mesa.

## ADR-002: Tríade temporal — horizonte × intervalo × período
- source: `docs/adr/002-triade-temporal.md`
- status: **proposed** (Proposto — implementar depois da validação do atraso do ADR-001 §Decisão 2)
- scope: `horizonte`, `intervalo`, `período`, tríade temporal, `resolve_keep`, SMA200, Radar, `candle_cache`, calibragem por intervalo, `masstest-agentes.py`
- decision:
  1. Os três parâmetros temporais deixam de ser campos soltos e formam uma tríade validada em conjunto; `horizonte` é o driver (escolha do usuário), `intervalo`/`período` são consequência sobrescrevível dentro de um envelope legal.
  2. Matriz legal fechada de combinações válidas (intraday curto/default/lento, swing, posição) — todas cabem no limite do Yahoo e entregam SMA200 válida. Combinação fora da matriz é recusada na borda, nunca aceita degradada. Teto declarado: `candle_cache._MAX = 600`.
  3. `resolve_keep(period)` → `resolve_keep(period, interval)`.
  4. Calibragem (limiares de volatilidade, comparativo de volume) viaja com a tríade, por intervalo — não são constantes fixas calibradas só para diário.
  5. Fronteira de custo: Radar roda em intervalo canônico e global (1d hoje, 15m quando F1 entrar); a tríade completa só vale na análise sob demanda (por usuário/ativo).
- a revisitar: se o atraso do feed derrubar 15m (ADR-001 §Decisão 2), a linha `intraday` desta matriz desloca para 30m.

## ADR-003: Identidade da posição de opção
- source: `docs/adr/003-identidade-posicao-opcao.md`
- status: **locked** (Aceito, 2026-08-04)
- scope: `optionPositions`, `positions`, `store.py`, `persistence.js`/`deviceStore`, P&L de opções, identidade de posição, KPI de patrimônio
- decision: `optionPositions` é uma coleção separada com identidade própria (`id` = `contractSymbol`, não `t`), nunca campos opcionais em `positions`. `underlying` é o único campo que aponta de volta para `positions`/`AtivoCard`. P&L de opção tem função de venda própria (não reusa `store.sell`). `persistence.js`/`deviceStore` precisa espelhar a mesma coleção. Conscientemente aceito: `optionPositions` nasce sem migração de schema, mesma dívida que `positions` já tem.
- a revisitar: se `positions` ganhar mecanismo de migração, `optionPositions` herda o mesmo; se v3 trouxer multi-perna, `id` único por contrato não basta para agrupar pernas (precisa `estrategiaId`, fora de escopo).

## ADR-004: Fonte de opções na v2 — o que o app pode simular com dado degradado
- source: `docs/adr/004-fonte-de-opcoes-na-v2.md`
- status: **locked** (Aceito, 2026-08-04)
- scope: `options_provider_yahoo`, `providerStatus`, `buy_option`, `optionPositions`, MyData/brapi, opções card v2, `OPTIONS-GUARDRAILS`, `/api/obs/usage`
- decision: Ler cadeia de opções degradada é sempre permitido (mostrar com aviso); **simular execução de compra é bloqueado** quando `providerStatus != "ok"` — botão de comprar fica desabilitado com mensagem descritiva. `avg` de posição simulada só é preenchido com preço que o próprio sistema classificou confiável no momento da compra. Gatilho declarado para acionar MyData/brapi como fonte primária: taxa de `providerStatus: degraded` > 20% das aberturas de cadeia em uma semana corrida (medido via extensão de `/api/obs/usage`).
- a revisitar: quando `mydata_client.py` existir, decide se Yahoo vira fallback do MyData ou é desligado; se o gatilho de 20% disparar antes do MyData pronto, prioridade sobe.

## ADR-005: Fechamento por expiração — o terceiro motivo de saída
- source: `docs/adr/005-fechamento-por-expiracao.md`
- status: **locked** (Aceito, 2026-08-04)
- scope: `optionPositions`, `history.motivo`, `agent.py`, `persistence.js`, liquidação por vencimento, aviso D-3, `push_events`
- decision: (1) `history` de `optionPositions` ganha campo estruturado `motivo: "stop"|"alvo"|"vencimento"|"manual"` desde o início — não retroage a `positions` (ação). (2) Fechamento por vencimento roda nos DOIS caminhos que avaliam posições — server (`agent.py`) e foreground iOS (`persistence.js`) — nunca só no server, para não piorar a divergência já existente entre os 5 caminhos de fechamento. Regra: antes do loop de stop/alvo, fora do gate de "sem cotação"; se `hoje >= expiration`, liquida pelo intrínseco e grava `motivo: "vencimento"`; aviso D-3 via push.
- a revisitar: se a divergência dos 5 caminhos de fechamento virar trabalho próprio, "vencimento" precisa ser contemplado na unificação; estender `motivo` estruturado para `positions` (ação) fica fora desta ADR.

## ADR-006: A camada de entendimento é backend-first e determinística
- source: `docs/adr/006-camada-de-entendimento.md`
- status: **locked** (Aceito, 2026-08-05)
- scope: camada de entendimento, `conceitos.py`, `/api/timing`, `skill_ref.TIMING`, didática do produto, guardrail de verbo de ordem, `B3_DIDATICA_OFF`, assistente por LLM (ADR-007)
- decision: texto didático é determinístico, mora no backend (`conceitos.py`), custo zero (nenhuma chamada LLM no caminho padrão — a camada paga/assistente é outra, ADR-007). Rotas NOVAS; `/api/timing` intocado (payload do Operador idêntico por construção, guardião congela o conjunto de chaves). Interpolação por allowlist de campos (`campos`), campo ausente derruba o parágrafo inteiro (nunca estima). Ordem de resposta: "o que o app NÃO faz" primeiro. Uma única afordância ("?" de 44×44) para todos os conceitos, com encadeamento "veja também". Desligável via `B3_DIDATICA_OFF=1` sem rebuild.
- descartado: explicação gerada por LLM na camada padrão; via proativa amarrada ao card expandido (custaria dinheiro no caminho do iniciante); um "?" por afirmação (18 seriam demais).

## ADR-007: O assistente recebe snapshot, e o push do gatilho é opt-in server-side
- source: `docs/adr/007-assistente-e-push-do-gatilho.md`
- status: **locked** (Aceito, 2026-08-05)
- scope: assistente de IA, snapshot estruturado, prompt cache-aware, teto de gasto por escopo/dia, push notification do gatilho, `kv:pushPrefs`, opt-in de alerta de mercado, kill-switch de push
- decision — Parte 1 (assistente): snapshot estruturado (view-model), nunca raspagem de DOM; conteúdo de tela é DADO, não instrução (guardião dedicado); montagem cache-aware (prefixo estável antes, volátil depois); exige conta (motivo técnico: `scope=None` é balde compartilhado de anônimos); `config` (modelo/chave) vai no corpo; teto por escopo/dia (`B3_ASSISTENTE_TETO_BRL`, padrão R$ 1,00). Decisão de não mexer em `_CHARS_POR_TOKEN` (constante global, margem de 0,5% para o modelo padrão — subestimar é a direção segura do erro).
- decision — Parte 2 (push do gatilho): fonte de verdade é `kv:pushPrefs`, alimentada pelo registro do token (não por `config`/`localStorage`, que nunca chega ao servidor no device). Opt-in (classe nova de alerta nasce desligada). Carimbo de timing vai no TÍTULO da notificação (corpo trunca no iOS). Vocabulário de ESTUDO nos dois modos. `esticado` não notifica (evita convocar entrada que o próprio app desaconselha). Teto duplo (usuário/dia e usuário×ticker×dia) + agregação em uma mensagem. Silencioso (priority 5, sem som). Push carrega destino (`{"t": TICKER}`), validado contra formato B3. Vaga consumida mesmo sem entrega (preferir perder aviso a tempestade de retry). Kill-switch próprio (`B3_TIMING_PUSH_KILL=1`).

## ADR-008: brapi (plano gratuito) como fonte master; Yahoo como backup
- source: `docs/adr/008-fonte-de-cotacoes-selecionavel.md`
- status: **locked** ("Aceito em direção" — parte comercial/técnica fechada; pendência restante é só medição de delay do spot em pregão)
- scope: `candle_provider.py`, brapi API, Yahoo Finance API, failover de cotação/candle, orçamento de requisições, spot quotes, daily candles, intraday candles, ciclo do agente (`agent_mod.run_cycle_for`), cache L2, `fundamentals.py`
- decision: brapi (plano gratuito) é fonte MASTER de candles diários e cotação spot; **Yahoo continua sendo a fonte do intraday** (restrição de plano, não escolha) e é o backup de diário/spot. Orçamento de requisições com teto diário (~700 req/pregão, fatiado: spot 400, delta diário 150, fundamentos 30, reserva ~120), soft stop 80%, hard stop 100% (Yahoo assume o resto do dia). Seleção via env (`B3_CANDLE_PROVIDER`, `B3_CANDLE_FALLBACK`, `BRAPI_TOKEN`, `B3_BRAPI_COTA_MES`), sem escolha na UI. Cache com fonte no registro (`src`); no DIÁRIO merge entre fontes É permitido (open/close/volume idênticos medidos); `snapshotId` não carrega a fonte. Failover por requisição+orçamento; retorno automático no pregão seguinte. **Adendo 2026-08-11 (noite)**: o ciclo de execução do Operador (`agent_mod.run_cycle_for`/`scheduler_loop`) usa fonte ÚNICA e EXCLUDENTE — brapi OU Yahoo, nunca as duas na mesma leitura (violaria cálculo determinístico) — controlada por `B3_AGENT_QUOTE_SOURCE` (default `brapi`).
- nota de evolução: este ADR estreita o escopo do ADR-001 (que tratava Yahoo como primário geral) para diário/spot especificamente, sem revogar o orçamento US$ 0 nem a posição do Yahoo como fonte de intraday — ver INGEST-CONFLICTS.md [INFO].
- alternativas descartadas: brapi Pro já (contraria orçamento vigente); intraday na brapi gratuita (não existe no plano); escolha de fonte na UI (descartado nas duas versões deste ADR).

## ADR-009: Eixo de seleção do Radar — regime + momentum relativo
- source: `docs/adr/009-eixo-de-selecao.md`
- status: **locked** (Aceito, Refactor A aplicado em 2026-08-11)
- scope: Radar, `/api/scan`, `server/app/regime.py`, momentum relativo cross-sectional, confluência, `setups.py`, Snapshot Técnico Único, `radarScore`, N1
- decision: novo eixo primário de ordenação do Radar: **regime (tendência/lateral via SMA200/ADX) + momentum relativo cross-sectional** (percentil de variação entre ativos do universo escaneado). Setups de price action deixam de ordenar o mercado e viram gatilho de timing (só pontuam alinhados à direção do regime; reversão à média só conta em regime lateral). Ordem final: `(tier do regime ↓, momentum relativo ↓, gatilho alinhado ↓, confluência ↓, ticker ↑)` — confluência cai a último desempate, mas permanece no payload (contrato da UI não muda). Degradação declarada: sem 200 candles → SMA50 + `confiavel=False`; sem `change252` → `momentumParcial=True`; regime indefinido → tier 0, nunca promovido.
- dívida assumida: TODO pendente do guardrail de família no prompt N2 (decisão do Alex pendente); percentil é relativo ao universo escaneado (universo pequeno/enviesado enviesa o ranking); `radarScore` ainda não incorpora expectância medida (isso é o interlock com ESPEC-B).
- nota de evolução: ADR-016 (proposed) mede empiricamente e conclui que nenhuma célula setup×regime é positiva com significância, chamando a tese deste ADR de "refutada" nas seções §6 e Adendo 6 — ver INGEST-CONFLICTS.md [INFO]. Este ADR permanece locked/em vigor; ADR-017 (locked) adiciona uma camada corretiva de seleção dinâmica por cima, sem revogar o eixo regime+momentum.

## ADR-010: Modelo de planos — cap gratuito e features pagas
- source: `docs/adr/010-planos-e-cap-gratuito.md`
- status: **proposed** (parte técnica pronta para implementação; parte comercial — preço, loja, limites numéricos — pendente de decisão do Alex)
- scope: modelo de planos, cap gratuito, `plan.py`, `metering.py`, `brapi_budget.py`, freemium/BYOK, monetização, recibo de assinatura (IAP)
- decision (técnica, fechada): unidade do cap é por conta (reusa padrão de `metering.py`). Cap comercial e cota física da brapi são camadas independentes — nenhuma substitui a outra; usuário pago consome da mesma cota física. **Fonte de cotação NÃO é diferencial de plano** (brapi+Yahoo é infraestrutura igual para todos — cobrar por isso contrariaria transparência de dado do CLAUDE.md). Ao atingir o cap: ação específica recusada com motivo exato, resto do app funciona, número real mostrado (nunca estimado/escondido), sem linguagem de "assine e resolve na hora".
- pendente (comercial, decisão do Alex): valor exato dos limites do gratuito; preço/moeda/loja e validação de recibo; lista definitiva de features pagas (candidatas: IA gerenciada sem BYOK, ajuste de intervalo de cotação, recorte de eficiência por regime, alvo dinâmico).

## ADR-011: Módulo de Observabilidade e Governança de Dados
- source: `docs/adr/011-modulo-observabilidade-governanca.md`
- status: **proposed** (Proposto — arquitetura de leitura pronta para implementação; hospedagem/infra e qualquer escrita além do que já existe ficam pendentes de decisão do Alex)
- scope: módulo de observabilidade, governança de dados, Boris+, SQLite (kv/sessions/users/history), `_is_obs_admin`, navegador de tabelas com masking, trilha de eficiência de ações automáticas, `candle_provider`, `metering`, `brapi_budget`, `analysis_outcomes`
- decision (arquitetura de leitura, fechada): aplicação SEPARADA do Boris+ consumidor, mesmo backend, reusando 100% dos endpoints/auth existentes (`_is_obs_admin`). Módulo é somente-leitura sobre o que já existe + uma trilha nova de ações automáticas (campo `origem` em `history`) — não recalcula custo/uso/orçamento do zero. Navegador de tabelas nunca expõe segredo cru (masking por campo, não por tabela). Fronteira de acesso permanece binária nesta rodada (sem RBAC — decisão explícita de escopo).
- pendente: onde hospedar a aplicação nova; autenticação (reusar login existente vs. fluxo próprio); qualquer capacidade de escrita além do existente; RBAC/nível intermediário.
- nota de supersessão registrada no próprio texto: **Decisão 6 (paleta própria) foi superada pelo ADR-012 (Fase 5, 2026-08-14)** — ver INGEST-CONFLICTS.md [INFO].

## ADR-012: Portal de Observabilidade v2 — tendência no tempo, eficiência da IA e da automação
- source: `docs/adr/012-observabilidade-v2-tendencia-eficiencia.md`
- status: **locked** (Implementado — Fases 1-5 completas, 2026-08-14)
- scope: portal de observabilidade, eficiência da IA (`analysis_outcomes`), eficiência/correlação da automação, tendência/série temporal (`analytics_daily`, `obs_daily_metrics`), campo `origem` em ordens (manual/automatico/sistema), redesenho visual Brand Book v2
- decision (5 fases, todas implementadas): (1) Eficiência da IA agregada — `compute_stats_all_users()`, cache diário, `MIN_N=10`, nunca expõe `user_id` individual. (2) Tendência para Comportamento do Usuário via `analytics_daily` + soma do dia corrente (funil deliberadamente NÃO migrado — dependeria de ordem por usuário que o rollup agregado não guarda). (3) Automação + correlação análise↔operação — `origem` em `buy`/`sell`/`buy_option`/`sell_option` (`manual` default preservado; `automatico` nos 3 call-sites do Operador; `sistema` para liquidação por vencimento, deliberadamente separado de `automatico` pois não é decisão do agente). (4) Série temporal nova (`obs_daily_metrics`, 7 métricas/dia). (5) Redesenho visual com Brand Book v2 (decisão explícita do Alex, 2026-08-14) — **supersede a Decisão 6 do ADR-011** (paleta própria azul).
- guardrails válidos para todas as fases: nenhum endpoint admin novo devolve `user_id` individual/lista bruta; nenhuma métrica de tendência sem indicar desde quando existe; taxa de acerto da IA sempre rotulada autoavaliação interna, nunca garantia.
- fora de escopo: alertas/thresholds; navegador de tabelas genérico e RBAC granular (exclusões já do ADR-011); "tempo de reação"/"slippage vs. previsto" (dado não existe, não será fabricado).

## ADR-013: RBAC, papéis e entitlements — central de administração de verdade
- source: `docs/adr/013-rbac-papeis-e-entitlements.md`
- status: **locked** (Implementado, aprovado pelo Alex em 2026-08-16 — único item pendente é verificação manual em build iOS real, não arquitetural)
- scope: RBAC, papéis e permissões, entitlements/plano comercial, web-admin, `plan.py`, `auth.py`, `admin_audit_log`, prompts (`llmPrompts`/skill), kill-switch de execução automática, fontes de dados (brapi), rotas de `main.py`/`options_api.py`
- decision: duas dimensões ORTOGONAIS — papel de governança (visitante → usuário → 7 grupos de permissão nomeada por macro função de produto: Observabilidade, Operador IA, Execução de ordens automáticas, Mudança de LLM, Fontes de dados, Prompts, Usuários e papéis) e plano comercial (visitante → free → pro, eixo já existente em `plan.py`, ligado a `users.plan` persistido). Checagem sempre no backend via `Depends()` (nunca escondendo botão no front), revogação imediata (não embutida em token). 76/76 rotas mapeadas e cobertas (15 públicas, 45 anônimo-ok, 7 usuário, 9 admin por permissão nomeada). Novo módulo `audit.py`: toda escrita admin gera linha em `admin_audit_log`, sem exceção. Prompts default passam a ser editáveis em runtime com prioridade SEMPRE da edição do usuário (mecanismo reusa `_eh_default_antigo`/histórico de hashes já existente, `defaults.py`/`catalog.js` continuam sendo o piso de recuperação de desastre, intocados). **Invariante explícita**: stop/alvo (`PUT /api/position/{ticker}`, `PUT /api/options/position/{contract_id}`) NUNCA é vetado por papel/plano — nenhuma dependency de plano é adicionada a essas rotas.
- pendente (implementação, não arquitetura): nome exato da permissão de escrita do kill-switch; retenção de `admin_audit_log`; confirmação ao vivo em iOS de que nenhum caminho depende de `llmPrompts` server-side sem mandar o próprio prompt.

## ADR-014: Administração e observabilidade no app mobile
- source: `docs/adr/014-administracao-mobile.md`
- status: **locked** (Aceito, implementado — a aprovação e a implementação ocorreram depois da redação deste ADR; confirmado pelo product owner (Alex) em 2026-08-27, consistente com `PROJECT.md`, que já listava este item como "existing". O texto do próprio documento-fonte permanece desatualizado — ver nota abaixo.)
- scope: web-admin, app mobile (Capacitor), RBAC/permissões (ADR-013), handoff de sessão (`POST /api/admin/mobile-handoff`), telas legadas de observabilidade em Perfil, `@capacitor/browser`/`@capacitor/app-launcher`, risco de review da App Store
- decision (Opção C, escolhida entre A/B/C — aprovada e implementada): `web-admin/` inteiro (as 10 abas, sem port/reescrita) abre dentro de um browser in-app via `@capacitor/browser`, disparado por botão em Perfil visível só quando `permissions` (lido de `/api/auth/me`) contém alguma das 7 permissões admin do ADR-013. Handoff de sessão: rota nova `POST /api/admin/mobile-handoff` devolve token de curta duração/uso único trocável por `b3-admin-token`. Fallback sem dependência nova: Opção B (`@capacitor/app-launcher`), mesma arquitetura de handoff, caso o Alex preferisse não adicionar `@capacitor/browser`. Tratamento uniforme para as 10 abas (bundle já é fluido). Correção da Fase 2 sobre as 4 telas legadas em Perfil: 3 delas são dado PESSOAL (não administrativo) e nunca deveriam ter sido tratadas como observabilidade admin; as 2 mistas já se auto-protegem (backend nega 403, front esconde a seção) — **nenhuma das 4 muda nesta rodada**.
- nota de status (fonte desatualizada — correção fora de escopo deste ingest): o arquivo-fonte ainda traz literalmente "Status: Proposto — aguardando aprovação do Alex antes de qualquer implementação (Fase 2 do prompt de execução)" e encerra com "Pare aqui — Fase 2 (implementação) só começa após aceite explícito." Essa linha ficou desatualizada porque o ADR foi escrito antes da aprovação; aprovação e implementação vieram depois e o documento nunca foi corrigido para refletir isso. Do ponto de vista desta síntese não há pendência de aprovação remanescente. Ver INGEST-CONFLICTS.md [INFO].
- checado contra LOCKED-vs-LOCKED: sem contradição encontrada com nenhum outro ADR locked deste lote — complementa o ADR-013 (reusa seus 7 grupos de permissão nomeada) e não sobrepõe a arquitetura do portal de observabilidade do ADR-011/ADR-012 (superfícies e mecanismos de acesso distintos).

## ADR-015: Assertividade do motor de recomendação — diagnóstico e caminho de melhoria
- source: `docs/adr/015-assertividade-do-motor-de-recomendacao.md`
- status: **proposed** ("Proposto — aguardando aprovação. Nenhum código de produção foi alterado nesta rodada")
- scope: motor de recomendação, `analysis_outcomes`, instrumentação de métricas, painel Eficiência da IA, backtest determinístico walk-forward, classificação de regime (ADR-009), TradingView (fonte de dados avaliada e rejeitada), constantes de R:R mínimo
- decision (recomendação, não implementada neste doc): a medição de eficiência da IA fabrica stops (ancora entrada no `close` do dia da análise, ignorando o gatilho real) — direção do erro é OTIMISTA, não pessimista (expectância medida +2,56R vs. corrigida 0,00R nos mesmos dados de dev). Confirmado em produção: 0 de 159 registros resolvidos têm campo `entrada`; ambos os bugs de instrumentação estão em 100% dos registros. Segmentação por regime (tese do ADR-009) tem N=0 hoje, não N baixo — `regime` só começou a ser gravado em 2026-08-11. **TradingView descartado**: sem API pública de dado e ToS proíbe nominalmente price referencing/algorithmic decision-making/risk management programs — risco jurídico/comercial sem contrapartida. Recomendação: Alternativa 1 (consertar instrumentação) imediatamente, Alternativa 2 (backtest com walk-forward + deflação por seleção múltipla) como próxima fase. Nenhuma alternativa recomendada toca Princípio 5 nem guardrail CVM.
- fora de escopo: mudar limiar de R:R antes da Alternativa 1 consolidar numa constante única; implementação de qualquer alternativa (documento é pesquisa+desenho); re-litigar ADR-001/ADR-008.

## ADR-016: Qualidade do sinal do motor de setups — diagnóstico e caminho
- source: `docs/adr/016-qualidade-do-sinal-do-motor-de-setups.md`
- status: **proposed** ("Proposto — aguardando decisão. Nenhum código de produção foi alterado")
- scope: motor de setups, confluência, backtest harness, Radar, Modo Operador, Modo Estudo, `regime.ranquear`, IFR2, walk-forward, momentum relativo, trailing stop, gate de regime e volatilidade
- decision (diagnóstico, medido em 15 anos/125.938 sinais/74 tickers, não implementado neste doc): o motor de setups tem **expectância negativa** (−0,105R/operação, t=−39,6) e perde para entrada em dia sorteado com a mesma geometria (placebo −0,016R). A confluência não discrimina (93% dos sinais valem 100%, é artefato de implementação, não sinal). Nenhum dos 17 pares setup×lado sobrevive ao limiar deflacionado exceto IFR2 (alta), positivo e significativo tanto no diário 15 anos (+0,072R, t=+3,99) quanto no semanal 10 anos (+0,164R, t=+2,79). **A tese do ADR-009 (regime como eixo de seleção) não se sustenta como implementada** — texto do documento usa a palavra "refutada" (§6 "A tese do ADR-009 é refutada com mais força" e Adendo 6 "Sinal de entrada... Refutado (...); Gate de regime... Refutado"); nenhuma das 49 células setup×regime é positiva com significância. O Modo Operador real (trailing ATR 2× + alvo dinâmico) é a PIOR das quatro mecânicas de saída medidas (−0,167R) — pior que o Modo Estudo (stop+alvo fixo, −0,115R). Achado que funciona: pesar setups pelo desempenho histórico medido na janela anterior (out-of-sample, walk-forward) leva a expectância de −0,099R para +0,005R (empate estatístico, não lucro) — persistência confirmada (Spearman +0,523, t=+7,52). Recomendação: Alternativa A (parar de apresentar o sinal como operável) imediatamente, Alternativa B (reconstruir seleção sobre o que o backtest validar) em seguida; C (só reconstruir confluência) rejeitada isoladamente.
- **Este é o diagnóstico que o ADR-017 (locked) implementa como decisão de produto.** Ver nota de evolução em ADR-009 e conflito [INFO] em INGEST-CONFLICTS.md.

## ADR-017: Revisão de setups e seleção dinâmica por desempenho histórico
- source: `docs/adr/017-revisao-de-setups-e-selecao-dinamica.md`
- status: **locked** (Aceito — decisões de produto tomadas pelo Alex em Plan Mode, 2026-08-20; Bloco 1 e Bloco 4 implementados nos Adendos 1-2, 2026-08-21)
- scope: setups de trading, seleção dinâmica de setups, Modo Operador, `entradaAuto`, `signal_ledger`, `regime.ranquear`, `radarScore`, `signal_replay`, `scheduler_loop`
- decision:
  1. **Critério de revisão dos 17 setups**: rejeitado cortar por \|t\| (efeito × tamanho de amostra, não critério de decisão — prova no próprio dado com Setup 9.1). Adotado: magnitude econômica (ExpR) em 3 faixas — só a faixa catastrófica (ExpR ≤ −0,15R, 6 pares) recebe aposentadoria ESTÁTICA do motor de decisão (mas o detector permanece no código, ganha campo `aposentado: true`); faixas intermediária e de ruído ficam para a seleção dinâmica; IFR2 (alta), único positivo, é mantido no motor mas nunca exposto como setup vencedor isolado.
  2. **Arquitetura da seleção dinâmica**: um ledger (`ticker, setup, lado, data_sinal, data_resolucao, resultado, status`) no banco principal, duas agregações (cumulativa e por janela anual fechada, n≥40). Bootstrap manual (15 anos × 74 tickers) roda uma vez fora do `scheduler_loop`; manutenção diária incremental pendurada no `scheduler_loop`. Funções puras de replay promovidas para `server/app/signal_replay.py` (fonte única, scripts viram wrapper fino). `regime.ranquear()` usa `elegivel`/`expR` como peso novo (`W_HISTORICO_ELEGIVEL=+10.0`/`W_HISTORICO_INELEGIVEL=-10.0`) entre `momentumRelPct` e `gatilhoAlinhado` na tupla de ordenação — nunca inverte o eixo regime/momentum do ADR-009.
  3. **Destino do Modo Operador**: `entradaAuto` suspenso imediatamente (gate reversível), religando automaticamente gated pela elegibilidade da seleção dinâmica quando o Bloco 1 estiver em produção. **Guardrail explícito (já vetado no ADR-016)**: isto é regra determinística; se algum dia a proposta for deixar a IA escolher setup/ordenar Radar/decidir entrada, é mudança de natureza que exige aprovação separada.
  - Adendo 2 (2026-08-21): flag `agent.ENTRADA_AUTO_SUSPENSA_ADR017` removida; gate por setup via `signal_ledger.historico_snapshot`; `elegivel is not True` bloqueia em silêncio (não é erro); falha de leitura do ledger falha FECHADO. Deploy em produção passa por checkpoint humano bloqueante (Plano 08-05) — código pronto e testado, mas não foi ao ar sem aprovação explícita registrada neste documento.
- consequência declarada: Radar/card de setup passam a mostrar histórico medido em vez de confluência como proxy de qualidade; Modo Operador fica sem entrada automática até a seleção dinâmica existir.

## ADR-018: Cobertura E2E/browser automation — avaliação (FIX-C27)
- source: `docs/adr/018-cobertura-e2e.md`
- status: **locked** (Aceito, 2026-08-23)
- scope: cobertura E2E, Playwright, device harness (XCUITest/Maestro), Capacitor/WKWebView, suíte de testes (`server/tests`, `web/tests`), `TESTFLIGHT.md` checklist manual, checkpoint humano bloqueante em deploys
- decision: **não adotar E2E/browser automation agora** (opção iii — reforçar guardiões estáticos + checklist manual). Justificativa central: o E2E mais barato (Playwright na PWA) não cobre a superfície nativa/Capacitor onde os 3 defeitos históricos caros de fato ocorreram (sync device→servidor, orçamento sem flush, link do Operador); o E2E que cobriria essa superfície (device harness) tem custo de infraestrutura desproporcional ao estágio do produto (um desenvolvedor, pré-receita). Não é veredito permanente — 4 gatilhos objetivos de reavaliação: (1) terceiro defeito de regressão em fluxo financeiro crítico escapando para produção; (2) entrada de um segundo desenvolvedor; (3) cobrança real ligada (ADR-010); (4) frequência de deploy que torna o checklist manual o gargalo.

## ADR-019: Acervo diário oficial COTAHIST da B3
- source: `docs/adr/019-cotahist-diario-b3.md`
- status: **locked** (Accepted, 2026-08-25)
- scope: COTAHIST, `b3_historical.py`, `b3_daily_imports`, `b3_daily_quotes`, scheduler, CLI admin, `fontes_dados.configurar`, `candle_cache`
- decision: implementar `server/app/b3_historical.py` — download HTTP direto do arquivo diário oficial da B3 (URL derivada da data), validação de ZIP/header/trailer/tamanho de registro/data, persistência SQLite em `b3_daily_imports` (status/hash SHA-256/erro) e `b3_daily_quotes` (linhas normalizadas), reexecução idempotente por data, job no scheduler existente após `B3_COTAHIST_DAILY_HHMM` (default 20:30 BRT), CLI + rotas admin gated por `fontes_dados.configurar`. Este acervo é **fonte histórica rastreável separada** dos provedores de cotação existentes — não substitui `candle_cache` nem é reconstruído a partir de Yahoo/brapi (perderia proveniência oficial).
- alternativas rejeitadas: simular fluxo do navegador contra a página HTML pública (fragilidade de captcha/popup); usar Yahoo/brapi para reconstruir o arquivo (perde proveniência oficial); inserir direto no `candle_cache` (semântica de acervo de arquivo é diferente da série por ticker/provedor).
