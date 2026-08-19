# Achados — Dimensão GATE (gating de monetização)

**Data:** 2026-08-18

## Método de verificação

- **Lido (código, arquivo inteiro ou trecho relevante):** `docs/adr/010-planos-e-cap-gratuito.md`,
  `server/app/plan.py` (86 linhas, inteiro), `server/app/metering.py` (134 linhas, inteiro),
  `server/app/managed.py` (135 linhas, inteiro), `server/app/brapi_budget.py` (trechos:
  `cota_mes`, `teto_dia`, `fatia_limite`, `pode_gastar`, `degradado`, `snapshot`, `set_spot_intervalo`,
  `projecao`), `server/app/candle_provider.py` (trecho do TTL degradado), `server/app/agent.py`
  (trecho `avaliar_alvo_dinamico`/`agent_params`/`alvoDinamico`), `server/app/ai_activity.py`
  (assinaturas), `server/app/main.py` (rotas `/api/ai/quota`, `/api/obs/usage`,
  `/api/obs/brapi/projecao`, `/api/analyze/{ticker}`, `/api/technical/analyze/{ticker}`,
  `/api/watchlist/add` — call sites dos hooks de `plan.py`), `web/src/plan.js` (35 linhas,
  inteiro), `web/src/App.jsx` (trechos: uso de `canAddTicker`/`canAnalyze`, tela
  `FonteDadosScreen`, `EficienciaIAScreen`, painel de administração embutido),
  `web-admin/src/App.jsx` (trecho `EficienciaIA`), `docs/adr/008-fonte-de-cotacoes-selecionavel.md`,
  `.planning/codebase/CONCERNS.md` (seção "Missing Critical Features"), `CLAUDE.md` (raiz do repo).
- **Grep real (não inferência):** `can_add_ticker|can_analyze|requires_subscription|plan_at_least|current_plan|ACTIVE_PLAN`
  em `server/app/` e `web/src/`; `metering.check|metering.consume|metering.snapshot` em
  `server/app/main.py`; `degradado(` e `candles.alerta` em `server/app/*.py` e `web/src/App.jsx`;
  `EficienciaIAScreen|iaEficiencia` em `web/src/App.jsx`; `alvoDinamico` em `server/app/agent.py`
  e `server/app/main.py`.
- **Exercitado via API real:** NÃO. O backend local não estava no ar
  (`curl http://localhost:8787/api/health` falhou por conexão recusada) e o plano proíbe
  explicitamente subir o servidor via `scripts/executar.sh`/`run.sh` nesta janela (mataria o
  servidor de planos paralelos da wave 1 rodando em outros worktrees). D-01 já declara
  código+docs suficiente para a dimensão GATE — não subi um servidor standalone por não
  agregar confiança adicional aos achados abaixo (todos decidíveis por leitura de código com
  evidência de linha).
- **Não verificado:** payload real de `GET /api/ai/quota` com/sem sessão (ficaria disponível se
  a API tivesse sido exercitada); comportamento em produção do estado `degradado` sob carga real.

## Estado dos hooks de gating

| Hook | Linha | Retorna hoje | Quem chama (arquivo:linha) | O que falta para funcionar | Reescrita necessária? |
|------|-------|--------------|------------------------------|------------------------------|------------------------|
| `current_plan` | `plan.py:41` | Resolve `users.plan` do banco por usuário logado (ADR-013); `ACTIVE_PLAN` só é fallback pra anônimo | **NINGUÉM** — grep em `server/app/` e `web/src/` não encontra nenhuma chamada de `current_plan(` fora da própria definição em `plan.py:41` | Nada tecnicamente — a função já está pronta e correta; falta ser chamada nos 3 call sites que hoje ignoram o usuário | parcial — plugar `current_plan(user)` nos 3 call sites abaixo |
| `plan_at_least` | `plan.py:52` | `bool` comparando índice em `_ORDEM_PLANO` | **NINGUÉM** — a própria docstring da função já confirma: "nenhuma rota usa isto ainda" (linha 54) | Nenhum `require_plan()`/decorator de rota existe para consumir isto | parcial — precisa nascer o dependency/decorator que chama a função |
| `can_add_ticker` | `plan.py:63` | `(True, None)` sempre, pois `plan.get("max_watchlist")` é `None` | `server/app/main.py:870` — `plan.can_add_ticker(len(store.get(_conn, "watchlist", user_id=scope)))`, **sem** passar `plan=`; cai no fallback `ACTIVE_PLAN` global (`plan.py:66`), não no plano do usuário autenticado | `PLAN_FREE["max_watchlist"]` precisa virar um número (decisão comercial) **e** o call site precisa passar `plan=plan.current_plan(user)` | parcial — call site existe mas ignora o plano real do usuário |
| `can_analyze` | `plan.py:73` | `(True, None)` sempre — os 2 call sites passam `0` hardcoded como uso do mês, nunca a contagem real | `server/app/main.py:1223` (`/api/technical/analyze/{ticker}`) e `server/app/main.py:1370` (`/api/analyze/{ticker}`), ambos `plan.can_analyze(0)`; o próprio comentário na linha 1370 admite `# FUTURO: passar a contagem do mes do usuario` | (a) contador mensal real no padrão de `metering.py`, (b) call sites pararem de hardcodar `0`, (c) decidir a relação com `metering.check` (ver achado F-GATE-02) | sim — depende de resolver a sobreposição com `metering.check` antes de alimentar contador real |
| `requires_subscription` | `plan.py:83` | `False` sempre | **NINGUÉM** — grep confirma zero call sites em `server/app/` ou `web/src/` | Mecanismo de validação de recibo de loja (App Store/Google Play) server-side inteiro — hoje inexistente | sim — feature nova completa (captura de recibo no client + validação server-side + persistência) |

## Os 3 passos de ativação do ADR-010

| Passo (ADR-010) | O que já existe (arquivo:linha) | O que falta | Depende de decisão comercial? | Esforço |
|---|---|---|---|---|
| 1. Resolver `ACTIVE_PLAN` por usuário via recibo de loja validado server-side | `current_plan(user)` já existe e lê `users.plan` corretamente (`plan.py:41-49`); campo `users.plan` já tem default `'free'` persistido (ADR-013) | (a) mecanismo de validação de recibo de loja (App Store/Google Play) — inexistente; (b) os 2 call sites de gate (`can_add_ticker`, `can_analyze`) **não chamam `current_plan(user)`** — usam o fallback `ACTIVE_PLAN` global (ver F-GATE-01) | Sim — preço/loja definem o fluxo de compra que gera o recibo | Alto — integração externa nova (App Store/Google Play server APIs) + correção dos 2 call sites |
| 2. Alimentar `can_analyze` com contador real no padrão de `server/app/metering.py` | `metering.check`/`consume`/`snapshot` já implementam exatamente esse padrão (kv por `user_id`, quota diária, kv seção própria) — mas para OUTRO propósito hoje (custo de IA gerenciada, não plano comercial) | Decidir se `can_analyze` vira wrapper fino sobre `metering.check` (nova seção kv, texto de motivo próprio) ou se os dois convivem como conceitos distintos e documentados — ver veredito abaixo | Não tecnicamente (o padrão já existe); o VALOR do limite é que é comercial | Baixo se reaproveitar `metering.py` como está desenhado; Médio se implementar um terceiro contador do zero |
| 3. `requires_subscription` checar o recibo em vez de sempre `False` | A assinatura da função já existe (`plan.py:83`) | Igual ao passo 1 — depende do mesmo mecanismo de validação de recibo, inexistente hoje | Sim | Alto — mesmo bloqueio de infraestrutura do passo 1 |

**Veredito sobre `can_analyze` × `metering.check` (passo 2):** são **duas implementações
concorrentes do mesmo conceito na mesma requisição**, confirmado por evidência de código. Em
`/api/analyze/{ticker}` (`main.py:1367-1370`) e `/api/technical/analyze/{ticker}`
(`main.py:1218-1223`), a mesma chamada passa por dois gates de "quantas análises você pode
fazer": primeiro `plan.can_analyze(0)` (sempre libera — hardcoded), depois, dentro de
`_ai_apply_managed` (`main.py:342-382`, chamado a partir da linha 367), `metering.check(...)`
com quota diária real, rate limit e teto global — mas só quando o usuário não tem BYOK e a IA
gerenciada está habilitada (`managed.is_available()`). Hoje `can_analyze` é inerte então não há
conflito visível; mas alimentá-lo com um contador real seguindo literalmente o passo 2 do ADR,
sem reconciliar com `metering.check`, criaria **dois contadores independentes** de "análises
restantes" respondendo pela mesma pergunta na mesma chamada, com textos de erro diferentes e
sem nenhuma garantia de que batem entre si. Ativar o passo 2 exige escolher UMA arquitetura
antes de popular o número — não é "só configurar".

**Veredito sobre `ACTIVE_PLAN` como constante de módulo em cenário multi-usuário (1d):**
`plan.py:35` (`ACTIVE_PLAN = PLAN_FREE`) é uma constante de módulo — global de processo, não
resolvida por requisição. `current_plan(user)` existe e lê corretamente `users.plan` do banco
por usuário (linhas 41-49) — mas, como a tabela acima evidencia, os 2 call sites de gate reais
(`can_add_ticker` em `main.py:870`, `can_analyze` em `main.py:1223` e `:1370`) chamam os hooks
**sem passar `plan=`**, o que os faz cair no fallback `plan = plan or ACTIVE_PLAN`
(`plan.py:66`, `:76`) — o global fixo, não o plano do usuário autenticado. Ou seja: mesmo que
amanhã uma conta específica tenha `users.plan = 'pro'` persistido no banco, os gates atuais
**nunca leriam esse valor**, porque `current_plan(user)` nunca é chamado em lugar nenhum do
código (grep confirma zero call sites fora da própria definição). Veredito: o "estruturalmente
pronto, só ligar o número" do ADR-010 é otimista nesse ponto específico — ligar
`PLAN_FREE["max_watchlist"] = 10` hoje bloquearia igualmente contas marcadas `'pro'` no banco,
porque o fio que resolveria o plano por usuário está cortado antes de chegar no hook. É uma
reescrita pequena (3 call sites + 1 import), mas é reescrita de código, não apenas
configuração/dado.

## Cota física × cap comercial

| Eixo | Onde é calculado (arquivo:linha) | Escopo | Rota que expõe | O que o usuário vê quando estoura | Confunde com o outro? |
|---|---|---|---|---|---|
| **Cota física da brapi** | `server/app/brapi_budget.py` — `cota_mes` (46), `teto_dia` (53), `fatia_limite` (57), `degradado` (163) | Compartilhada por TODA a base (15k requisições/mês, um único orçamento para o app inteiro) | `GET /api/obs/usage` (`main.py:449`, admin-gated `observabilidade.ver`) e o painel "Fonte de dados" (`web/src/App.jsx:5289-5375`, seção `FONTE DE COTAÇÕES`, também **admin-only** — comentário explícito na linha 5201: "cotações: só admin") | **NADA.** O usuário comum não vê nenhum painel de orçamento brapi — nem admin vê um aviso ativo de "orçamento baixo": o único efeito visível do estado `degradado` é o cache de spot triplicar de TTL silenciosamente (`candle_provider.py:338`), sem nenhum sinal na UI, nem para admin, de que os dados estão mais velhos que o normal (ver F-GATE-04) | Não no texto (nenhum texto sobrepõe as duas), mas por OPACIDADE total do primeiro eixo — ver F-GATE-04 |
| **Cap comercial de IA (gerenciada)** | `server/app/metering.py` — `check` (66), `consume` (114); `server/app/managed.py` — `daily_quota` (120), `global_daily_cap` (86) | Por conta (`user_id`), dentro do que a cota física de LLM do servidor permite | `GET /api/ai/quota` (`main.py:385-397`) devolve `snapshot()` com `used`/`quota`/`remaining`; o erro 402 de `metering.check` devolve o texto exato ("Você atingiu o limite diário de %d análises com a IA do app...") | O texto real do 402 chega à UI via `flash("Erro: " + (e.message \|\| e))` nos catches de `analyze`/`putWatchlist` (`web/src/App.jsx`, ex. linha 6623) — mensagem específica, menciona "análises com a IA do app" e sugere BYOK como alternativa | Não — vocabulário próprio ("análises com a IA"), não usa a palavra "cotação"/"orçamento" que o eixo brapi usa |

**Veredito cruzado com CLAUDE.md:** o estado `degradado` da brapi (`brapi_budget.py:163`) é um
*soft stop* que **estende o TTL do cache de spot em 3x** (`candle_provider.py:338`) quando uma
fatia do orçamento mensal passa de 80%. Esse é o único efeito rastreável do estado — grep
confirma que `degradado(` só é chamado nesse ponto interno. O único sinal que a UI expõe sobre
saúde da fonte de dados é `candles.alerta` (`web/src/App.jsx:5316-5317`), mas esse campo mede
**taxa de falha do provedor** (`candle_provider.py:141`, gatilho declarado do plano B de troca
de provedor — comentário em `main.py:457-459`), uma métrica **diferente** de "orçamento
degradado". Ou seja: quando o orçamento aperta e os dados passam a ficar até 3x mais
desatualizados, **nem usuário nem admin recebem qualquer indicação disso** — nenhum timestamp,
nenhum badge, nenhum texto. Isso viola diretamente o **princípio 3** do `CLAUDE.md` ("Dados de
mercado exibem fonte, horário da última atualização e se são em tempo real, atrasados ou
históricos") em um cenário concreto e sistemático (todo mês, ao se aproximar do teto). Por
violar um princípio obrigatório do CLAUDE.md, e não apenas representar risco de comunicação, a
classificação correta é **Crítico (D-02)** — ver F-GATE-04.

## Features candidatas a tier pago

| Feature | Onde vive (arquivo:linha) | Ponto exato onde o gate entraria | Mecanismo disponível hoje | Esforço de ativação | Bloqueio |
|---|---|---|---|---|---|
| **IA gerenciada com cota maior** | `server/app/managed.py` (`daily_quota`, linha 120; `global_daily_cap`, linha 86), consumida em `_ai_apply_managed` (`main.py:367`, parâmetro `quota=managed.daily_quota()`) | `main.py:367` — trocar `quota=managed.daily_quota()` por uma quota resolvida a partir de `plan.current_plan(user)` | `metering.check`/`daily_quota()` já aceitam um valor de quota arbitrário — só falta a fonte do valor variar por plano em vez de ser global (`B3_MANAGED_DAILY_QUOTA` único para todos) | Contexto baixo-médio — trocar 1 argumento de chamada + criar uma tabela `plano → quota`, sem tocar `metering.py` | Decisão comercial pendente (valor da quota); depende também de resolver o mesmo problema de F-GATE-01 (call site precisa saber o plano do usuário) |
| **Ajuste de intervalo de atualização de cotação** | `server/app/brapi_budget.set_spot_intervalo` (`brapi_budget.py:244`), rota `POST /api/obs/brapi/projecao` (`main.py:489-500`, hoje admin-only, `require_permission("fontes_dados.configurar")`) | `main.py:489` teria que aceitar `scope` de usuário comum em vez de só `require_permission` admin | **Nenhum** — `_spot_intervalo_mem` (`brapi_budget.py:245`) é uma variável **global de módulo**, um único intervalo vigente para o app inteiro, não por conta. O próprio ADR-010 já registra isso como pergunta aberta, não decisão | Contexto alto — exige repensar a arquitetura de orçamento de **por-app** para **por-usuário** (múltiplos intervalos concorrentes disputando a mesma cota física de 15k/mês) | Mecanismo inexistente (arquitetura atual é inerentemente compartilhada) + decisão comercial pendente |
| **Alvo dinâmico** | `server/app/agent.py` — `avaliar_alvo_dinamico` (320), campo `alvoDinamico` em `agent_params` (580); persistido via `store.set_agent(_conn, body, user_id=scope)` (`main.py:1610`) | `main.py:1610`, antes de persistir `alvoDinamico=true` no corpo — checagem de plano no momento do save | Já é per-conta hoje (campo dentro da config do agente, escopado por `user_id`) — não precisa de nova arquitetura de escopo, só falta o gate em si | Contexto baixo — 1 checagem de plano (`plan.requires_subscription` ou equivalente) no route handler existente | Depende de F-GATE-01 (recibo/plano do usuário) e da decisão comercial de manter opt-in gratuito ou não (o próprio ADR-010 registra isso como pergunta em aberto) |
| **Recorte de eficiência ("Eficiência da IA")** | Tela já existe e está **liberada para qualquer usuário logado hoje**: `EficienciaIAScreen` (`web/src/App.jsx:4643`, roteada em `:7496`), consumindo `ai_activity.snapshot` via API própria | No condicional de render da aba em `web/src/App.jsx:7496` (client) e, para não depender só do client, também no endpoint que alimenta `iaEficiencia` no backend | `requires_subscription()` (`plan.py:83`) já é a assinatura pronta para esse tipo de check — só falta parar de retornar `False` fixo | Contexto baixo na superfície (1 condicional a mais), mas o mecanismo por trás (`requires_subscription` real) tem o mesmo bloqueio de infraestrutura do passo 1/3 do ADR | Depende inteiramente de `requires_subscription` sair do estado "sempre False" — mesmo bloqueio de recibo de loja de F-GATE-01/03 |

## Achados

### F-GATE-01 — Hooks de gate nunca resolvem o plano por usuário; `current_plan` é código órfão
- **Requisito:** GATE-01
- **Severidade:** Alto — D-03 (bloqueia uma decisão de negócio pendente: mesmo com o número
  comercial decidido, ligar o cap hoje não respeitaria diferenciação `free`/`pro` por conta)
- **Evidência:** `server/app/plan.py:66,76` (`plan = plan or ACTIVE_PLAN`); `server/app/main.py:870`
  (`plan.can_add_ticker(len(...))` sem `plan=`); `server/app/main.py:1223,1370`
  (`plan.can_analyze(0)` sem `plan=`); grep confirma zero chamadas de `current_plan(` fora da
  própria definição em `plan.py:41`
- **Verificação:** código
- **Impacto:** quando `PLAN_FREE` ganhar um limite numérico, TODAS as contas — inclusive as
  marcadas `'pro'` no banco — cairiam no mesmo limite do `ACTIVE_PLAN` global, porque os call
  sites de gate não resolvem o plano do usuário autenticado. Ativar o cap exige tocar
  `main.py`, não só `plan.py`
- **Recomendação:** nos 3 call sites (`main.py:870`, `:1223`, `:1370`), passar
  `plan=plan.current_plan(user)` (o objeto de usuário já está disponível via `current_scope`/
  sessão nessas rotas) em vez de deixar cair no fallback global

### F-GATE-02 — `can_analyze` e `metering.check` são gates concorrentes na mesma requisição
- **Requisito:** GATE-01
- **Severidade:** Alto — D-03 (bloqueia decisão pendente: ativar o passo 2 do ADR-010 sem
  reconciliar os dois mecanismos duplica a lógica de contagem)
- **Evidência:** `server/app/main.py:1223` e `:1367-1370` chamam `plan.can_analyze(0)` (sempre
  libera hoje); `server/app/main.py:367` (dentro de `_ai_apply_managed`, chamado a partir da
  mesma rota) chama `metering.check(...)` com quota diária real, rate limit e teto global —
  ambos na MESMA chamada de `/api/analyze/{ticker}` e `/api/technical/analyze/{ticker}`
- **Verificação:** código
- **Impacto:** alimentar `can_analyze` com um contador real, seguindo literalmente o passo 2 do
  ADR-010 ("no padrão de `metering.py`"), sem reconciliar com `metering.check`, cria dois
  contadores independentes de "análises restantes" respondendo à mesma pergunta na mesma
  chamada — risco de UX confusa (limites que não batem entre si) e de contagem duplicada
- **Recomendação:** decidir explicitamente se `can_analyze` vira um wrapper fino sobre
  `metering.check` (reusando o padrão de kv com uma seção própria e texto de motivo
  diferenciado) antes de alimentá-lo com contador real — não implementar um terceiro contador
  paralelo

### F-GATE-03 — `can_add_ticker`/`can_analyze` são chamados com dado hardcoded, não com o estado real do usuário
- **Requisito:** GATE-01
- **Severidade:** Médio — D-04 (risco real, ainda não materializado porque limite=`None` hoje
  torna irrelevante, mas quebraria silenciosamente se o número comercial fosse ligado sem
  tocar o call site)
- **Evidência:** `server/app/main.py:1370` — `plan.can_analyze(0)  # FUTURO: passar a contagem
  do mes do usuario`; `web/src/App.jsx:6627` — `canAnalyze(0); // FUTURO: passar contagem do
  mês` (o próprio código já documenta a lacuna, backend e front)
- **Verificação:** código
- **Impacto:** popular `PLAN_FREE.max_analyses_per_month` hoje, sem tocar esses 2 call sites
  (backend) e o espelho em `App.jsx`, faria o gate sempre comparar `0 >= limite` — ou bloqueia
  todo mundo permanentemente no primeiro uso do dia, ou nunca bloqueia ninguém, dependendo de
  qual lado do request-response o número aterrissa primeiro. O número comercial sozinho não
  ativa nada de útil
- **Recomendação:** os call sites (backend e front) precisam calcular a contagem real do mês
  corrente antes de o gate virar operacional — não basta popular `PLAN_FREE`

### F-GATE-04 — Estado `degradado` da cota brapi é invisível para usuário E admin, violando o princípio 3 do CLAUDE.md
- **Requisito:** GATE-02
- **Severidade:** Crítico — D-02 (viola o princípio 3 obrigatório do CLAUDE.md: "Dados de
  mercado exibem fonte, horário da última atualização e se são em tempo real, atrasados ou
  históricos")
- **Evidência:** `server/app/candle_provider.py:338` — `return base * 3 if
  brapi_budget.degradado("spot") else base` triplica o TTL do cache de spot sem nenhum sinal
  externo; grep confirma que `degradado(` só é chamado nesse ponto interno; o único campo
  exposto à UI sobre saúde de dado, `candles.alerta` (`web/src/App.jsx:5316-5317`, admin-only),
  mede **taxa de falha do provedor** (`candle_provider.py:141`), uma métrica diferente do
  estado de orçamento
- **Verificação:** código
- **Impacto:** quando uma fatia do orçamento mensal da brapi passa de 80%, os dados de
  cotação ficam até 3x mais desatualizados (ex.: TTL de 60s vira 180s) e nem usuário nem admin
  recebem qualquer indicação — nenhum timestamp, badge ou texto reflete o TTL estendido. Isso
  acontece de forma sistemática (todo mês, ao se aproximar do teto), não é hipotético
- **Recomendação:** expor o estado `degradado` por fatia no payload já consumido por
  `FonteDadosScreen`/`/api/obs/usage`, e refletir no timestamp/label de "última atualização"
  mostrado ao usuário quando o TTL estendido estiver ativo — sem isso, o produto está mostrando
  dado mais velho do que declara

### F-GATE-05 — Painel de orçamento brapi é 100% admin-only; usuário comum não tem visibilidade do eixo físico de cota
- **Requisito:** GATE-02
- **Severidade:** Médio — D-04 (risco real de opacidade, ainda não incidente documentado —
  distinto de F-GATE-04, que é a violação ativa do princípio quando o estado degradado ocorre)
- **Evidência:** `web/src/App.jsx:5201` (comentário explícito: "cotações: só admin") e
  `:5372-5375` (`FonteDadosScreen`, ramo `!isNative && !candles`, mensagem própria confirma que
  o painel de orçamento "são visíveis aqui para contas de administração")
- **Verificação:** código
- **Impacto:** o usuário comum nunca vê o orçamento brapi (nem em estado normal, nem
  degradado) — a única cota que ele vê é a de IA (`/api/ai/quota`). Isso por si só não é uma
  violação (a cota física é infraestrutura, não obrigação de UI para o usuário final), mas
  combinado com F-GATE-04 significa que não existe NENHUM canal, nem admin nem usuário, que
  sinalize em tempo real quando o app está operando em modo degradado
- **Recomendação:** não é necessário expor orçamento bruto ao usuário final (seria ruído), mas
  o efeito do degradado (dado mais velho) precisa aparecer no timestamp que o usuário já vê —
  ver recomendação de F-GATE-04, que resolve as duas questões com a mesma mudança

## Verificado e conforme

- **A separação conceitual cota-física-brapi × cap-comercial-de-IA está bem resolvida no
  ADR-010** e implementada como duas camadas de fato independentes no código: `brapi_budget.py`
  (app inteiro, `_estado` module-level) nunca se mistura com `metering.py`/`managed.py` (por
  `user_id`) — não há nenhum ponto de código onde as duas contagens compartilham o mesmo
  contador ou seção de kv. Não precisa virar item de roadmap.
- **O texto de erro quando o cap de IA gerenciada estoura já é claro e não promete "resolve na
  hora com upgrade"** — `metering.check` (`metering.py:94-108`) sempre sugere BYOK como
  alternativa gratuita e imediata, em vez de empurrar para upgrade pago (alinhado ao princípio
  8 do CLAUDE.md, proibição de linguagem de enriquecimento rápido/urgência de compra).
- **`requires_subscription` e `plan_at_least` sendo funções órfãs (zero call sites) não é, por
  si, um achado de severidade alta** — são pontos de extensão deliberadamente não conectados
  ainda (ADR-010 é explícito sobre isso); o achado real é que os OUTROS dois hooks
  (`can_add_ticker`/`can_analyze`) já TÊM call site mas o call site está incompleto
  (F-GATE-01/03), o que é uma lacuna mais concreta.
- **A mensagem de teto global de IA gerenciada (`metering.py:104-108`) já é transparente** sobre
  ser um limite do lado do servidor, não do usuário individual — não confunde os dois eixos.

## Cobertura de requisitos

| Requisito | Achados | Status |
|---|---|---|
| GATE-01 | F-GATE-01, F-GATE-02, F-GATE-03 | com achados |
| GATE-02 | F-GATE-04, F-GATE-05 | com achados |
| GATE-03 | Mapa técnico em "Features candidatas a tier pago" (nenhum achado F-GATE dedicado — a tabela evidencia esforço/bloqueio sem revelar problema estrutural adicional além dos já cobertos por GATE-01) | conforme |
