# Codebase Concerns

**Analysis Date:** 2026-08-18

Escopo: repositório completo, com foco dirigido em (1) fronteira IA↔cálculo
financeiro determinístico, (2) tratamento de falha/atraso da fonte de
dados de mercado, (3) gating de features pagas, (4) segredos hardcoded, e
(5) incidentes documentados em `docs/`, `qa/` e `CHECKOUT-*.md`.

**Leitura geral:** o núcleo financeiro (ordens, posição, preço médio,
patrimônio, kill-switch, failover de cotação) está bem guardado, com
guardrails explícitos no código e teste de regressão para quase todo
incidente passado. As áreas de risco reais hoje são de UX/estado
distribuído no frontend (`web/src/App.jsx`, monólito de 7599 linhas) e de
disciplina de processo (convenção não reforçada por lint/CI em alguns
pontos), não de vazamento da IA para o dinheiro.

## Tech Debt

**`web/src/App.jsx` é um monólito de 7599 linhas:**
- Issue: componente único concentra todas as telas, todos os modals
  (`BuyModal`, `SellModal`, `OpcaoContrato`, etc.) e toda a lógica de ação
  (`A.confirmBuy`, `A.confirmSell`, `A.buyOption`...). `appMode ===
  "operador"` é recalculado de forma independente em pelo menos 11 pontos
  do arquivo (linhas 1581, 1779, 1954, 3044, 3529, 4029, 5155, 5855, 6271,
  6412...) em vez de vir de uma fonte única.
- Files: `web/src/App.jsx`
- Impact: qualquer mudança de estado que precise valer em toda a tela
  (ex.: modo de trabalho, stop/alvo) tem múltiplos pontos de verdade
  independentes — é exatamente o padrão de erro raiz por trás de 3 bugs
  reais já corrigidos (ver `docs/auditoria-controle-ordens-parametros.md`):
  stop/alvo apagando sozinho, carteira nativa dessincronizada do servidor,
  ciclo do agente não reagindo a gatilho recém-armado.
- Fix approach: extrair pelo menos o estado de `appMode`/modo de trabalho
  para um hook único (`useAppMode()`) consultado em todos os 11+ pontos,
  e separar os modals de ordem (`BuyModal`, `SellModal`, camada de opções)
  em arquivos próprios antes de crescer mais.

**Gate "Executar" mudo em toque (ainda não corrigido):**
- Issue: o botão de modo "Executar" fica desabilitado fora do Modo
  Operador e a ÚNICA explicação é o atributo HTML `title`, que não existe
  em toque (WKWebView/iOS não tem hover). O parágrafo explicativo abaixo
  do botão não linka para onde trocar de modo (Perfil → Modo de trabalho).
  Mesmo padrão se repete em "Entrada automática".
- Files: `web/src/App.jsx:3596-3610` (Executar/sinalizar), `web/src/App.jsx:3745-3749` (Entrada automática)
- Impact: usuário toca no botão, nada acontece (sem toast, sem navegação,
  sem pista) — lido como "quebrou", não "falta um passo em outro menu".
  Documentado ao vivo em `docs/auditoria-controle-ordens-parametros.md`
  como pedido real do Alex ("não me deixa mais selecionar o modo
  executar").
- Fix approach: os 3 itens de prioridade já especificados no próprio
  documento: (1) trocar o parágrafo mudo por um botão que navega direto
  para Perfil → Modo de trabalho; (2) nunca depender só de `title` em
  controle desabilitado (toast ao toque ou texto sempre visível); (3) um
  card de status único no topo da tela de Operador IA mostrando os 4
  estados que decidem se uma ordem dispara (`appMode`, `agent.mode`,
  `agent.serverEnabled`, `position.stop/alvo`) juntos.

**Dois nomes "Operador" sem link entre si (parcialmente corrigido):**
- Issue: aba "Operador IA" (config do agente) e "Modo Operador" (dentro de
  Perfil → Modo de trabalho, o interruptor mestre `config.appMode`) usam a
  mesma palavra para coisas diferentes. Um link entre as duas telas foi
  adicionado (F10-20260807-07, memória do projeto), mas a auditoria
  completa (card de status único, ver item acima) segue pendente.
- Files: `web/src/App.jsx` (`ModoTrabalhoCard`, ~linha 1779; nav do
  Operador IA)
- Impact: descoberta do modo correto ainda depende de o usuário entender a
  hierarquia implícita, não de a UI expor.
- Fix approach: ver prioridade 3 do item anterior.

**Convenção de paridade `deviceStore`×`serverStore` é reforçada por
disciplina + testes pontuais, não por checagem exaustiva automática:**
- Issue: `web/src/persistence.js` mantém dois stores (nativo/iOS e
  web/PWA) que precisam expor o mesmo contrato de método/campo. Existem
  testes de paridade PONTUAIS por feature (`web/tests/test_admin_ui.mjs`,
  `web/tests/test_analysis_outcomes_ui.mjs`, `web/tests/
  test_agent_server_toggle.mjs`), mas nenhum teste genérico varre os DOIS
  objetos e falha se um método existir só em um. A garantia de "método
  novo entra nos DOIS" depende de quem escreve o código lembrar da regra
  (documentada em CLAUDE.md do repo) e escrever o teste de paridade daquela
  feature especificamente.
- Files: `web/src/persistence.js` (linhas ~97 `serverStore()`, ~214
  `deviceStore()`)
- Impact: já foi causa raiz documentada de pelo menos 1 incidente real
  (carteira nativa não sincronizava com o servidor — `buy`/`sell`/
  `putPosition` no `deviceStore` eram 100% locais, corrigido
  F10-20260807-05) e do bug de orçamento (`initialBudget` sem sync
  device→servidor, F10-20260809-05).
- Fix approach: um teste genérico que compara `Object.keys(serverStore())`
  vs `Object.keys(deviceStore())` (ou introspecção equivalente) e falha em
  qualquer assimetria não documentada como intencional, complementando (não
  substituindo) os testes pontuais existentes.

**`server/app/main.py` concentra ~80 rotas em 2418 linhas:**
- Issue: todas as rotas HTTP do backend (carteira, agente, admin, opções,
  timing, push, kb, assistente) vivem em um único módulo.
- Files: `server/app/main.py`
- Impact: navegação e revisão de PR mais custosas; risco de import
  circular crescente (o arquivo já faz vários `import` locais dentro de
  função de propósito para evitar ciclo — ver `server/app/agent.py`
  comentários "import local: sem ciclo").
- Fix approach: quebrar por domínio em routers FastAPI (`APIRouter`) já
  seria possível sem mudar contrato de rota; não é urgente hoje porque o
  arquivo é bem comentado e testado, mas cresce a cada fase.

## Known Bugs

Nenhum bug financeiro (ordem/posição/saldo) aberto foi encontrado nesta
auditoria. Os bugs de dado documentados no histórico do repositório
(stop/alvo apagando sozinho, dessincronia device↔servidor, ciclo do
agente não reagindo a gatilho recém-armado, `NameError` em
`fundamentals` derrubando `/api/scan`, event loop bloqueado por I/O
síncrono no warm job, retorno acumulado inflado por edição de
`initialBudget`) estão CORRIGIDOS e com guardião de teste — ver seção
"Fragile Areas" e "Test Coverage Gaps" para os pontos ainda vivos.

**UX do gate "Executar" (ver Tech Debt acima) é o único item real ainda
em aberto** — comportamento correto (trava do Modo Estudo), mas sem
feedback ao toque; tratado como tech debt de UX, não como bug de dado.

## Security Considerations

**CORS liberado (`allow_origins=["*"]`) — mitigado por design:**
- Risk: `server/app/main.py:45` configura `CORSMiddleware` com
  `allow_origins=["*"], allow_credentials=False`. Qualquer origem pode
  chamar a API.
- Files: `server/app/main.py:44-46`
- Current mitigation: `allow_credentials=False` — a API não usa cookies de
  sessão; autenticação é Bearer token no header `Authorization`, que uma
  origem maliciosa não consegue forjar via CORS (CSRF clássico não se
  aplica). Rotas admin exigem RBAC (`Depends(require_permission(...))`).
- Recommendations: se o app algum dia adotar cookie de sessão, restringir
  `allow_origins` antes disso — a combinação atual só é segura enquanto
  `allow_credentials` continuar `False`.

**Segredos: nenhum hardcoded encontrado.** Busca por padrões de chave
(`sk-`, `AIza`, `AKIA`, literais `api_key=`/`secret=`) em
`server/app/*.py` e `web/src/*.js`/`*.jsx` não retornou nenhum segredo
embutido. `BRAPI_TOKEN`, chaves de LLM gerenciado, credenciais do
Google/Apple e afins são lidos via `os.environ`/`os.getenv` e vivem só em
env do servidor (Railway) — nunca no bundle do front nem versionados
(confirma `docs/adr/008-fonte-de-cotacoes-selecionavel.md` e
`server/app/plan.py` sobre "apiKey/baseUrl da IA gerenciada NUNCA entram
aqui — seguem só em env"). Bancos SQLite (`server/data/*.db`) estão em
`.gitignore` (linhas 8-11) e não estão versionados.

**Autenticação: PBKDF2-SHA256 com salt e rate limit — adequado.**
- `server/app/auth.py:41-48` — `hash_password` usa `pbkdf2_hmac("sha256",
  ..., 240_000 iterações)` com salt aleatório por senha
  (`_PBKDF2_ITER = 240_000`, linha 25).
- Rate limit por (ip, e-mail) no login, com reset em sucesso —
  `server/app/main.py:221` e `server/app/auth.py:165` (seção "rate limit
  (login)").
- Login social (Google/Apple): commit mais recente do repositório
  (`403432f`, "identities: uma conta, vários métodos de login",
  2026-08-17) corrigiu uma falha real de modelagem — contas OAuth
  colidindo por e-mail criavam uma TERCEIRA conta em vez de vincular à
  existente. Fix vincula automaticamente SÓ no sentido OAuth→conta
  existente (prova criptográfica de posse do e-mail via
  `email_verified`), nunca o sentido inverso (que seria sequestro de
  conta por digitação de e-mail alheio). Mudança recente — vale
  observação em produção antes de considerar totalmente assentada.

**Kill-switch é controle manual sem expiração automática:**
- Risk: `server/app/agent.py` mantém DOIS kill-switches independentes —
  `agent.kill_switch_on()` (execução de ordens automáticas,
  `agentKillSwitch` no admin) e `timing_watch.kill_switch_on()` (push do
  gatilho, env `B3_TIMING_PUSH_KILL`). Ambos, uma vez ligados
  manualmente, ficam ligados até desligamento manual — não há TTL nem
  alerta de "kill-switch ligado há X dias".
- Files: `server/app/agent.py:126-204`, `server/app/timing_watch.py:39,58-59`
- Current mitigation: o dashboard admin (`web-admin/src/App.jsx:96`)
  expõe o estado do kill-switch como KPI sempre visível ("KILL-SWITCH:
  LIGADO/desligado", tom negativo quando ligado). Isso resolve a
  visibilidade — não a expiração.
- Recommendations: considerar alerta (push/e-mail ao admin) se o
  kill-switch ficar ligado além de N horas em horário de pregão —
  registrado como padrão de incidente real (ver Fragile Areas).

## Performance Bottlenecks

Nenhum gargalo de performance ativo foi identificado nesta auditoria — os
dois problemas de performance documentados no histórico (I/O síncrono
bloqueando o event loop do FastAPI no warm job de fundamentos; scan
varrendo o universo sem cache) já foram corrigidos e têm guardião de
teste (`server/tests/test_fundamentals.py::
test_maybe_warm_roda_em_thread_com_chave`). Ver "Fragile Areas" para o
padrão de risco que os causou, ainda relevante para código novo.

## Fragile Areas

**I/O bloqueante dentro do event loop assíncrono — padrão de incidente
recorrente, mitigado mas não eliminado estruturalmente:**
- Files: `server/app/fundamentals.py` (`_fetch_brapi_raw`,
  `_fetch_bolsai_raw`, `_fetch_merged` — todas síncronas via `httpx.get`,
  chamadas só através de `asyncio.to_thread` em `server/app/main.py` e
  `server/app/agent.py`)
- Why fragile: o incidente de produção documentado em
  `qa/37-hotfix-incidente-fundamentos.md` (build F9-20260710-6) foi
  causado exatamente por uma chamada síncrona bloqueante dentro de uma
  corrotina do scheduler — travou o FastAPI inteiro por dezenas de
  segundos a minutos, healthcheck do Railway falhou, restart, crash loop.
  O fix (rodar via `asyncio.to_thread`) é uma disciplina de chamada, não
  uma barreira estrutural: qualquer função nova que adicione I/O síncrono
  em `fundamentals.py` (ou módulo equivalente) e seja chamada direto de
  uma rota/loop assíncrono reintroduz o mesmo incidente. O próprio
  docstring de `_fetch_merged` (linha ~419) já registra isso em texto:
  "BLOQUEANTE de propósito — DEVE rodar via asyncio.to_thread (nunca no
  event loop)".
- Safe modification: qualquer I/O de rede síncrono novo precisa nascer
  isolado em função própria com o mesmo aviso de docstring E chamado só
  via `asyncio.to_thread` — seguir o padrão de
  `server/app/fundamentals.py:459` (`maybe_warm`). A checklist do projeto
  (memória "Verificar endpoint + async") já cobre isso: "exercite o
  endpoint real e nada de I/O síncrono no event loop".
- Test coverage: guardado por `test_maybe_warm_pula_sem_chave_bolsai` e
  `test_maybe_warm_roda_em_thread_com_chave` — mas esses testes cobrem
  `fundamentals.py` especificamente, não uma regra geral que bloquearia
  I/O síncrono acidental em módulo novo.

**Fonte de dados de mercado — bem guardada, mas com histórico de falha
silenciosa que exige vigilância contínua:**
- Files: `server/app/candle_provider.py` (fronteira única de candles e
  spot), `server/app/brapi.py`, `server/app/yahoo.py`,
  `server/app/brapi_budget.py`
- Why fragile: o modo de falha mais perigoso já observado em produção
  (31/07/2026, documentado em `candle_provider.py:44-52`) não foi
  bloqueio HTTP — foi o Yahoo devolver HTTP 200, `marketState: REGULAR` e
  ZERO velas de B3 por 2 horas de mercado aberto, entregando dados de
  outros ativos (AAPL) normalmente. Um alarme que só contasse "não-200"
  como falha ficaria CEGO para esse cenário. O código já trata resposta
  vazia como falha (linha 78-80, `vazios`), mas esse é o tipo de defeito
  que só se manifesta em produção, sob condição específica do provedor —
  qualquer provedor novo (ou mudança no formato de resposta do atual)
  pode reintroduzir uma variante não coberta pelo alarme atual.
- Safe modification: qualquer provedor novo de candle/spot precisa herdar
  de `CandleProvider` e passar pela mesma fronteira instrumentada
  (`_chama`, `candle_provider.py:253`) — nunca ser chamado direto por
  código de negócio. O agente de execução usa fonte ÚNICA e EXCLUSIVA
  (`agent_quote_source()`, sem cross-fonte no meio de um ciclo) de
  propósito, para não misturar preços de duas origens na mesma decisão —
  ver comentário extenso em `candle_provider.py:411-428` citando
  diretamente a proibição do CLAUDE.md ("cálculos determinísticos", "não
  invente valores").
- Test coverage: `snapshot()`/`alerta` (linha 98-142) é exposto em
  `/api/obs/usage` e monitorado pelo painel admin — mas o gatilho do
  "plano B" (mudar de fonte) ainda depende de decisão humana lendo o
  número, não de failover automático de fonte "master".

**Kill-switch/heartbeat — corrigido, mas o padrão de bug (checagem antes
do heartbeat mascarando "morto" vs "vivo parado") pode se repetir em hook
novo do scheduler:**
- Files: `server/app/agent.py:874-960` (`scheduler_loop`)
- Why fragile: o heartbeat (`agentHeartbeat`, persistido a CADA tick,
  FORA do gate de pregão) foi movido para ANTES de qualquer gate
  (kill-switch, horário de pregão) de propósito — comentário na linha
  892-896 explica que a versão anterior não distinguia "vivo, pregão
  fechado" de "morto". Qualquer hook novo adicionado dentro do loop
  precisa respeitar essa ordem (heartbeat primeiro, gates depois) ou
  reintroduz a ambiguidade.
- Safe modification: novos hooks do scheduler entram DEPOIS do bloco de
  heartbeat (linha ~897-904) e devem ter seu próprio `try/except` que não
  derruba o laço inteiro — padrão já seguido por `analytics_mod.maybe_run`,
  `automacao.maybe_refresh_cache`, `_maybe_registrar_metricas_diarias`
  (linhas 905-919), cada um com try/except próprio e comentário
  "X nunca derruba o laço".
- Test coverage: `test_kill_switch_e_janela_de_pregao`
  (`server/app/agent.py:189`, referência ao teste) cobre o kill-switch em
  runtime; não há teste explícito de "heartbeat continua batendo mesmo
  quando hook novo lança exceção" além da revisão manual do padrão.

## Missing Critical Features

**Gating de features pagas: estrutura pronta, intencionalmente
desativada — decisão de negócio pendente, não bug.**
- Problem: `server/app/plan.py` define `PLAN_FREE`/`PLAN_PRO` e os hooks
  `can_add_ticker`, `can_analyze`, `requires_subscription` — mas TODOS os
  limites são `None` (ilimitado) e `requires_subscription` sempre retorna
  `False` (linha 86: "HOJE: nunca exige"). `ACTIVE_PLAN = PLAN_FREE` é o
  único plano vigente; `current_plan(user)` já lê `users.plan` do banco
  (ADR-013) mas nada popula esse campo além do default `'free'`.
  `plan_at_least()` existe para uso futuro de `require_plan()` mas
  "nenhuma rota usa isto ainda" (linha 54).
- Files: `server/app/plan.py` (módulo inteiro), `docs/adr/010-planos-e-cap-gratuito.md`
- Blocks: qualquer diferenciação comercial entre usuários gratuitos e
  pagos — hoje 100% do produto está liberado para 100% dos usuários. Isso
  é uma decisão DOCUMENTADA e deliberada (ADR-010: "a parte comercial
  [preço, loja, o que entra em cada tier] depende de decisão do Alex e
  fica marcada como pendente"), não uma lacuna de implementação
  descoberta por engenharia. O ADR já especifica os 3 passos técnicos
  para ativar quando a decisão comercial vier: (a) resolver `ACTIVE_PLAN`
  por usuário via recibo de loja validado server-side, (b) alimentar
  `can_analyze` com contador real no padrão de `server/app/metering.py`,
  (c) `requires_subscription` checar o recibo em vez de sempre `False`.
- Priority: não acionar sem decisão de negócio explícita — mas ao
  planejar qualquer feature nova "premium", verificar `plan.py` primeiro
  para não duplicar o mecanismo de gate.

## Test Coverage Gaps

**Paridade `deviceStore`×`serverStore` sem verificação genérica** — ver
Tech Debt acima. Prioridade: Média (mitigado por convenção + testes
pontuais, mas já foi causa raiz de 2 incidentes reais documentados).

**Heartbeat do scheduler sob falha de hook novo** — nenhum teste
verifica que um hook recém-adicionado ao `scheduler_loop` que lança
exceção não bloqueia o heartbeat ou os gates subsequentes além do que a
revisão manual do padrão garante. Prioridade: Baixa (padrão bem
documentado em comentário, mas não travado por teste).

**UX do gate "Executar" mudo em toque** — não é lacuna de teste
automatizado tradicional (é descoberta por uso real), mas não há teste
de acessibilidade/interação que capturaria "controle desabilitado sem
feedback visível ao toque". Prioridade: Alta (item já priorizado em
`docs/auditoria-controle-ordens-parametros.md`, ainda sem fix aplicado).

---

*Concerns audit: 2026-08-18*
