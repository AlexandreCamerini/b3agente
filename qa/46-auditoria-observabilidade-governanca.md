# qa/46 — Auditoria e proposta de escopo: módulo de Observabilidade e Governança de Dados

**Data:** 2026-08-12 · **Status:** auditoria + proposta, nenhum código muda
nesta rodada · **Pedido por:** Alex ("criar uma aplicação de gestão dos dados
que suportam o Boris — observabilidade dos processos, visualização de todas
as tabelas, análise das ações tomadas automaticamente e sua eficiência")
**Lentes usadas:** `engineering:system-design` (arquitetura/dados/fronteiras
de serviço) + `design:design-system` (hierarquia de informação/consistência
visual) · **Companion:** [`docs/adr/011-modulo-observabilidade-governanca.md`](../docs/adr/011-modulo-observabilidade-governanca.md)

---

## Parte 1 — Auditoria (inventário com evidência)

### 1.1 Observabilidade de processos — o que sustenta o app hoje

Onze processos de fundo automáticos, todos ancorados no laço mestre
`scheduler_loop` (`server/app/agent.py:732-843`, tick base
`B3_AGENT_INTERVAL_S`=300s, gate de pregão `in_market_hours` seg-sex
10h-18h BRT, kill-switch `B3_AGENT_KILL`). Nenhum erro por processo derruba o
laço — todos têm `try/except` próprio; o padrão de falha é "degrada e tenta
de novo no próximo tick", sem retry/backoff explícito.

| # | Processo | file:line | Frequência | Observável hoje | Invisível hoje |
|---|---|---|---|---|---|
| 1 | Laço mestre (heartbeat, próxima passada) | `agent.py:732-843` | a cada tick | `LAST_RUN`/`RUN_HISTORY` → `GET /api/agent/status` → tela Diagnóstico (pregão, kill-switch, último ciclo, próxima passada, erro, últimas 5 passadas) | Heartbeat completo (`atBRT`, `haS`, `lacoVivo`) — zero uso em `App.jsx` apesar de existir no snapshot |
| 2 | Ciclo por usuário (stop/alvo/trailing/opções/entrada automática) | `agent.py:464-596` | por tick, respeitando `intervalMin` do usuário (default 15min) | Eventos no Diário (`GET /api/agent/log`) | Contagem de operações do dia por usuário (`opsToday`) sem endpoint próprio |
| 3 | Vigia de gatilho (push "condição atingida") | `agent.py:679-729`, `timing_watch.py` | após passada intraday nova | Entrada textual no Diário por tentativa | Nenhuma contagem agregada de avisos disparados/falhos no dia |
| 4 | Proteção sem Operador | `agent.py:620-676` | a cada tick, no pregão | Contagem agregada e por-usuário **existe no `status_snapshot`** (`agent.py:876`, `main.py:1891`) | **Não é lida em `App.jsx`** — dado pronto, sem UI |
| 5 | Radar diário | `radar_daily.py:47-60,226-257` | 1x/dia útil, 08:45 BRT | `LAST_DAILY` no `status_snapshot["radarDiario"]` | **Não é lida em `App.jsx`** — dado pronto, sem UI |
| 6 | Avaliação de análises pendentes | `analysis_outcomes.py:350-363` | 1x/dia, mesmo hook do radar | `LAST_EVAL` no `status_snapshot["avaliacaoAnalises"]` | **Não é lida em `App.jsx`** — dado pronto, sem UI |
| 7 | Aquecimento de cache de fundamentos | `fundamentals.py:411,459-477` | 1x/dia, TTL 7d/ticker | — | **Nenhum contador exposto em lugar nenhum** — nem no snapshot, nem no diário |
| 8 | Passada intraday global | `intraday.py:167-175` | 1×/tick, no pregão | — | Sem contador dedicado |
| 9 | GC de sessões expiradas | `main.py:1985-1994` | a cada 24h | Só como linha solta em `/api/obs/logs` (admin) | Sem contagem estruturada (nº purgado) |
| 10 | Roteamento de candles (primário/backup) | `candle_provider.py:271-322` | por requisição | `snapshot()` agregado → tela Fonte de dados (provedor, fallback, taxa de falha) | Detalhamento `porDia`/`porProvedor` (req/erros/vazios/msMédio) só no JSON, sem tela |
| 11 | Fonte exclusiva de cotação do agente | `candle_provider.py:428-484` | por ciclo do agente | Indireta ("SEM cotação" no Diário) | Taxa de falha da fonte exclusiva (separada do tráfego geral) não existe |

**Push de notificações** (`push.py:171-249`): teste manual funciona e loga
resultado detalhado no Diário; **falhas de push automático durante execuções
do agente são `except: pass` silencioso** (`agent.py:823-829`) — nem viram
warn no Diário. Gap real: se o push de uma ordem executada falhar, ninguém
sabe.

**Cache de candles (`candle_cache.py`)**: TUDO invisível — `stats()`
(`candle_cache.py:151-152`) existe mas **não tem endpoint**, confirmado por
ausência de chamador fora do próprio módulo/testes. Falhas do L2 (SQLite)
são sempre silenciosas (`except Exception: pass`, `candle_cache.py:99-100,
116-117`).

**Fronteira de acesso hoje**: binária — `_is_obs_admin` (`main.py:382-390`,
`B3_ADMIN_EMAILS` ou primeira conta) dá tudo-ou-nada. Não existe nível
intermediário ("ver métrica agregada sem ver log individual/PII").

### 1.2 Tabelas da aplicação

Só **4 tabelas físicas** SQLite (`server/app/db.py`) — todo o resto do
estado funcional vive multiplexado dentro de uma delas:

| Tabela | file:line | Guarda | Sensível? | Quem lê hoje | Crescimento |
|---|---|---|---|---|---|
| `kv` | `db.py:82` | Estado funcional inteiro do app, endereçado por prefixo de `key` (`config`, `positions`, `history`, `agent`, `analysisOutcomes`, `aiActivity`, `metering`, `radarDaily:*`, `pushTokens`, `siwaRefresh`, `fundamentals:*`, `intraday`, `timingWatch`, `brapiBudget:*`, `brapiSpotIntervaloS` — ~15 "sub-tabelas lógicas" por prefixo) | **Sim** — `siwaRefresh` (token OAuth Apple), `pushTokens` (identificador de push), `config` pode conter API key BYOK do usuário | Fatiado por endpoint: cada rota expõe só a fatia do próprio usuário; agregados admin via `/api/obs/usage`, `/api/obs/brapi/projecao` | Nº de linhas ≈ nº de usuários × seções fixas (baixo); `value` de cada linha pode crescer (JSON, ex. até 500 registros de `analysisOutcomes`) |
| `users` | `db.py:86-96` | Contas (email, provider, `pass_hash`, `provider_sub`, nome) | **Sim** — email (PII), hash de senha, `provider_sub` | `db.list_users()` exclui `pass_hash` mas inclui email/provider/`provider_sub` → `GET /api/admin/summary` (admin) | Baixo — 1 linha/cadastro |
| `sessions` | `db.py:98-106` | Bearer tokens ativos, TTL 90d | **Sim** — `token` é segredo equivalente a senha durante a validade | Só uso interno (`resolve_session`), nunca exposto cru; sem endpoint de "sessões ativas" | Médio, autolimitado (expira + GC 24h) |
| `candle_cache` | `db.py:111-118,121-124` | Séries de candles diários por `symbol@interval`, cap 600 candles | Não — dado público de mercado | Nunca exposto cru; só via `/api/history/*` do próprio ticker pedido | Alto relativo — 1 linha por ticker×intervalo coberto, blob JSON reescrito por inteiro a cada update |

**Achado central para o navegador de tabelas**: `kv` não é uma tabela
homogênea — é ~15 domínios de dado com sensibilidade muito distinta na mesma
estrutura `key/value`. Um navegador ingênuo (SELECT * FROM kv) misturaria
saldo simulado (não sensível) com token OAuth (crítico) na mesma grade.

### 1.3 Ações automáticas × eficiência — o gap estrutural

`analysis_outcomes.py` (base da tela "Eficiência da IA") **só rastreia
recomendações de análise de IA** (N1/N2 — Radar e análise técnica), nunca o
resultado de uma ordem de fato executada. O próprio módulo já declara essa
fronteira (`analysis_outcomes.py:6-9`): *"trades reais... é feature
separada (qa/30 Fase B), com seu próprio armazenamento — não usa nada deste
módulo."* Essa Fase B nunca nasceu.

Toda ação que o agente **executa sozinho** (sem intervenção humana) passa
por `store.buy`/`store.sell`/`store.set_position`/`store.set_option_position`
— os MESMOS métodos usados pelas rotas manuais (`POST /api/buy` etc.) — e
**nenhuma delas** chama `analysis_outcomes.registrar()`:

| Ação automática | Decidida em | Persistida em | Alimenta eficiência? |
|---|---|---|---|
| Trailing stop (ação) | `agent.py:533-534` | `store.set_position` (`agent.py:536`) | **Não — gap** |
| Alvo dinâmico (F3) | `agent.py:178-197,545-546` | `store.set_position` (`agent.py:549-550`) | **Não — gap** |
| Venda por stop/alvo atingido | `agent.py:540-541` | `store.sell` (`agent.py:571`) | **Não — gap** |
| Trailing de opção | `agent.py:267-272` | `store.set_option_position` | **Não — gap** |
| Venda de opção por stop/alvo | `agent.py:276-299` | `store.sell_option` (com `motivo`) | **Não — gap** |
| Liquidação de opção por vencimento | `agent.py:251-256` | `store.close_option_vencida` | **Não — gap** |
| Entrada automática (compra) | `agent.py:353-385` | `store.buy` (com `meta.setup`) | **Não — gap**, mesmo tendo `setup` disponível |

Consequência prática: a entrada de `history` (o ledger real de
compra/venda, `store.py:526-640`) **não distingue origem manual de
automática** — nenhum campo tipo `origem: "agente"`. Hoje é impossível
filtrar "quantas dessas operações o próprio agente decidiu" nem calcular
taxa de acerto separada para elas.

O que existe de mais perto de uma contagem agregada:
- **"Diário do Operador"** (`App.jsx:5016-5038`) — só texto, últimos 30
  eventos, sem nenhuma agregação.
- **`RUN_HISTORY`/"PASSADAS DO SCHEDULER"** (`agent.py:846-881`,
  `App.jsx:5039-5049`) — conta "quantas execuções por passada", agregado
  globalmente (todas as contas), sem breakdown por tipo de ação, sem
  por-usuário, sem medida de resultado.

### 1.4 Decisões, operações e configurações

~38 variáveis de ambiente inventariadas (ver detalhamento completo no
apêndice A1). Classificação por categoria:

| Categoria | Quantidade | Editável via UI hoje |
|---|---|---|
| Segredo (chave/token/credencial) | 11 (`BRAPI_TOKEN`, `BOLSAI_API_KEY`, `B3_MANAGED_LLM_KEY`, `ANTHROPIC/OPENAI/GEMINI_API_KEY`, `APNS_TEAM_ID/KEY_ID/AUTH_KEY`, `SIWA_KEY_ID/PRIVATE_KEY`, `B3_ADMIN_EMAILS`) | Nenhuma |
| Decisão de produto (afeta regra de negócio/monetização) | 8 (`B3_BRAPI_COTA_MES`, `B3_AGENT_QUOTE_SOURCE`, `B3_MANAGED_LLM_MODEL`, `B3_MANAGED_GLOBAL_DAILY_CAP`, `B3_MANAGED_DAILY_QUOTA`, `B3_GATED_HOSTS`, `B3_SCAN_UNIVERSE`, `B3_ASSISTENTE_OFF`) | Nenhuma editável — 4 delas são espelhadas read-only (cota brapi, cota/teto de IA, gate de cadastro) |
| Parâmetro operacional | ~19 (intervalos, timeouts, concorrência, kill-switches diversos) | **Só 1** (`brapiSpotIntervaloS`, único parâmetro com ciclo simular→aplicar completo na UI, `FonteDadosScreen`) |

**Achado-chave**: o maior "buraco" de governança é `server/app/plan.py`
— os caps de monetização futura (`max_watchlist`, `max_analyses_per_month`,
`byok_required`, hoje todos `None`/`False`) não têm **nenhuma** superfície:
nem env var, nem chave `kv`, nem tela. Ativar cobrança hoje exigiria editar
o arquivo-fonte e fazer deploy.

Segundo maior gap: `brapi_budget._FRACOES` (o fatiamento 57%/21%/4% do
orçamento entre spot/delta/fundamentos, `brapi_budget.py:29`) é política do
ADR-008 hoje hardcoded — rebalancear exige deploy, não runtime.

`B3_ADMIN_EMAILS` merece nota à parte: é a própria chave do portão de
admin — corretamente **nunca** deveria ganhar uma tela de auto-concessão de
privilégio, mas hoje também não há log de quem foi promovido/removido dela.

### 1.5 Custos — só o que já está medido

| Métrica | file:line | Já exposta? | Natureza |
|---|---|---|---|
| Mensalidade Railway (US$ 20/mês) | `qa/42-finops.md:8` | Não (só dashboard Railway) | Medido, fonte externa ao código |
| Custo estimado por chamada de LLM (R$) | `ai_activity.py:59-63` | Sim — `AtividadeIAScreen` (ACUMULADO/HOJE/histórico) | Estimativa documentada (preço de tabela × câmbio fixo `USD_BRL=5.40`), rotulada como tal |
| Tokens consumidos (por chamada/dia/total) | `ai_activity.py:90-93,119-138`; `llm.py:93` | Sim (parcial) — `AtividadeIAScreen` mostra total; breakdown por modelo só em `/api/obs/usage` (admin), sem tela | Medido |
| Cota diária de análises por usuário | `metering.py:120-124` | Não há tela de usuário (só erro 402 ao estourar) | Medido |
| Teto/gasto GLOBAL de análises gerenciadas | `metering.py:36-43` | Só `/api/obs/usage` (admin) | Medido |
| Orçamento de requisições brapi (cota, fatias, projeção) | `brapi_budget.py:151-170,230-261` | Sim — `FonteDadosScreen` | Medido/projeção determinística — é contagem de requisição, não dinheiro |
| Custo do assistente por escopo/dia + teto (`B3_ASSISTENTE_TETO_BRL`) | `assistente.py:42-66` | Não — só usado internamente como freio | Medido, sem exposição |

**Lacunas que a auditoria encontrou e não inventa número para preencher**:
fatura Railway detalhada (RAM/CPU/volume/egress), preço real cobrado pelo
provedor de LLM (vs. list price), câmbio em tempo real (hoje constante
fixa), exposição de cota/teto na UI do usuário final, custo por usuário
quando BYOK (por desenho, impossível de instrumentar — o app nunca vê a
chave do usuário).

---

## Parte 2 — As sete decisões

### Decisão 1 — Onde o módulo vive

**Aplicação separada** (novo frontend, mesmo backend) — não uma aba nova
dentro do Boris+ consumidor.

Motivo: o público é outro (Alex/operação, não o usuário final do app de
simulação), o dado é mais sensível (PII de `users`, tokens de `sessions`,
segredos configurados) do que qualquer coisa hoje navegável no bundle
consumidor, e a UX certa para isto — grade densa, drill-down, tabela com
paginação e filtro — é estruturalmente diferente do padrão mobile-first de
cards do Boris+. Reaproveita 100% do backend: mesmo `_is_obs_admin`, mesmos
endpoints `/api/obs/*` e `/api/admin/*`, mesmo fluxo de Bearer token — só
o frontend nasce novo (pode ser um segundo app Vite servido de um subpath/
subdomínio, ex. `admin.boris.semente.dev` ou `/admin/*` num deploy próprio).

**Trade-off**: ganha isolamento (nada de dado sensível trafega no bundle
público do app de simulação; pode evoluir com paradigma de UI diferente sem
arrastar o design system mobile) e paga um pipeline de build/deploy a mais
(embora reaproveite CI/testes do backend). Alternativa descartada — aba nova
em `web/src/App.jsx` — foi rejeitada porque herdaria a fronteira binária
admin/não-admin dentro do MESMO bundle que qualquer usuário final baixa,
mesmo que a rota fique escondida; "não fica visível" não é o mesmo que
"não está no bundle".

### Decisão 2 — Mapa de telas/áreas

Cinco áreas, cada uma lendo dado que já existe (nenhuma duplica fonte de
verdade) mais o que a Decisão 5 propõe instrumentar:

| Área | Conteúdo | Fonte de dado |
|---|---|---|
| **Visão Geral** | Grade de "semáforo" por processo (dos 11 da seção 1.1): status, última execução, erro se houver. Pregão aberto/fechado, kill-switch, próxima passada. | `GET /api/agent/status` (já tem quase tudo — só falta expor os campos hoje invisíveis: heartbeat, radarDiario, avaliacaoAnalises, protecaoSemOperador) |
| **Processos** | Drill-down por processo: frequência configurada, histórico de execuções, taxa de falha, contadores hoje invisíveis (fundamentos, intraday, cache L2, push automático) | Mesmos endpoints + campos novos a expor (Decisão 7, Fase 1) |
| **Dados** (navegador de tabelas) | As 4 tabelas físicas; `kv` agrupada por prefixo lógico; só leitura, paginação, mascaramento (Decisão 4) | Endpoint novo, read-only (Decisão 7, Fase 2) |
| **Ações Automáticas & Eficiência** | Taxa de acerto/R-múltiplo POR TIPO de ação automática (não análise de IA) — a trilha que falta hoje (Decisão 5) | `history` com tag de origem (novo) + `analysis_outcomes`-like compute (novo) |
| **Configuração & Governança** | As ~38 variáveis classificadas (segredo/produto/operacional), o que é editável hoje vs. read-only vs. nem visível — com indicador claro "configurado: sim/não" para segredos, nunca o valor | Consolidação do que já existe espalhado (seção 1.4) |
| **Custos** | Os 7 itens da seção 1.5 num só lugar — sem número novo | Consolidação de `ai_activity`, `metering`, `brapi_budget`, `qa/42` |

### Decisão 3 — Tempo real vs. histórico

**Visão Geral**: polling leve (15s, mesmo padrão já usado por
`LogsDebugScreen` hoje) — é status operacional, precisa ser fresco.
**Processos/Dados/Configuração/Custos**: consulta sob demanda (botão
atualizar), sem polling automático — são dados de auditoria/drill-down, não
monitoramento em tempo real, e cada um desses domínios já é
computacionalmente mais pesado (paginação de tabela, agregação de
histórico). **Regra dura**: nenhuma tela deste módulo cria uma chamada nova
à brapi ou à IA só para se alimentar — tudo lê dado já coletado pelos
processos existentes (reforça o princípio "não duplicar fonte de verdade").

### Decisão 4 — Navegador de tabelas seguro

Por tabela:
- **`users`**: mostra email/provider/`created_at` (já é o que
  `admin_summary` expõe); `pass_hash` nunca sai do backend; `provider_sub`
  mascarado parcial (últimos 4 caracteres).
- **`sessions`**: nunca mostra `token` cru — só metadata (`user_id`,
  `created_at`, `expires_at`) e contagem agregada.
- **`kv`**: agrupada por prefixo lógico (não uma grade `SELECT *`) — cada
  grupo (`u:*:config`, `brapiBudget:*`, `fundamentals:*` etc.) vira uma
  "tabela lógica" na navegação. Dentro do grupo `u:*:config`, campos
  conhecidos como sensíveis (chave BYOK do usuário, se presente no JSON) são
  mascarados por padrão, com um clique extra para revelar (auditado).
  `siwaRefresh`/`pushTokens` nunca aparecem em claro — só "presente: sim/
  não" e `created_at`.
- **`candle_cache`**: sem restrição de conteúdo (dado público de mercado);
  paginação simples pelo volume potencial (1 linha por ticker×intervalo).

**Trade-off**: mascarar por padrão com revelação auditada é mais fricção
para o próprio Alex debugar um caso pontual, mas é a única forma de dar
"visualização de todas as tabelas" sem transformar o módulo num vazamento
de segredo — a alternativa (mostrar tudo cru "porque é só pro Alex") não
sobrevive ao dia em que outra pessoa ganhar acesso admin.

### Decisão 5 — Área de eficiência das ações automáticas

**Não retrofita `analysis_outcomes.py`** (ele já se declarou fora de escopo
para isto, propositalmente). **Reusa a infraestrutura de `history`** que já
existe: adiciona um campo `origem: "manual"|"agente"` em cada entrada,
preenchido nos 7 pontos de chamada de `store.buy`/`sell`/`sell_option`/
`close_option_vencida` já mapeados (agent.py:385,571,299,255 passam
`origem="agente"`; as rotas manuais em `main.py` mantêm `"manual"` como
default). Uma função nova, no formato de `compute_stats()` mas filtrando
`history` por `origem="agente"`, calcula taxa de acerto e R-múltiplo por
tipo de ação (trailing/alvo dinâmico/entrada automática/opções).

**O que falta nascer, tecnicamente**: (a) o campo `origem` no schema de
`history` (`store.py:526-640`) e nos 7 call-sites do agente; (b) a função de
agregação nova; (c) o endpoint que a expõe. Nenhuma mudança em
`analysis_outcomes.py`.

**Trade-off**: reusar `history` em vez de duplicar o padrão de
`analysis_outcomes` é menos código e não cria uma terceira fonte de
verdade sobre "o que o agente fez" — o preço é que `history` foi desenhado
para consumo do usuário (extrato de carteira), então o campo novo precisa
ser adicionado com cuidado para não quebrar consumidores existentes
(campo opcional, default `"manual"` preserva compatibilidade retroativa).

### Decisão 6 — Hierarquia de informação e direção de arte

Referência de **comportamento** (não de marca) em ferramentas de
observabilidade/ops densas em dado — Grafana/Datadog para o padrão de
grade de status + drill-down, Retool/Metabase para o padrão de navegador de
tabela com paginação e filtro. Elementos concretos:
- Grid de status na Visão Geral usa o mesmo vocabulário visual que o app
  consumidor já validou para dado técnico (fonte `MONO` para valores
  numéricos/timestamps, badges coloridos por severidade — mesmo padrão de
  `T.positive`/`T.negative`/`T.warn` do design tokens atual).
- Navegação por drill-down (lista → detalhe), não modais empilhados —
  dado tabular pede URL própria por tabela/processo, não overlay.
- Estados completos em toda tela (princípio #9 do CLAUDE.md): carregamento,
  vazio ("nenhum evento neste filtro"), erro (nunca esconder um 403/500
  atrás de tela em branco — o padrão atual de "esconde a seção" em
  `obsDenied` é aceitável para USUÁRIO comum, mas dentro de uma app que É
  só para admin isso vira ruído — mostrar a mensagem de erro real).
- Timestamp de frescor sempre visível junto de qualquer contador (princípio
  #3 do CLAUDE.md aplicado a dado operacional, não só a cotação).

### Decisão 7 — Ordem de execução

**Fase 1 (só leitura, dado que já existe — baixo risco)**:
- Visão Geral + Processos: expor os campos hoje já computados mas
  invisíveis na UI (heartbeat, radarDiario, avaliacaoAnalises,
  protecaoSemOperador, detalhamento por fatia do orçamento brapi,
  detalhamento por-modelo do uso de IA) — é wiring, não lógica nova.
- Custos: consolidação do que já existe, sem instrumentação nova.

**Fase 2 (precisa nascer no backend, mecânico)**:
- Navegador de tabelas: endpoints read-only novos + masking (Decisão 4).
- Eficiência de ações automáticas: campo `origem` + função de agregação
  (Decisão 5).
- Contadores hoje totalmente ausentes: fundamentos (aquecimento de cache),
  intraday, push automático falho, `candle_cache.stats()` (só falta ligar
  o endpoint — a função já existe).

**Fase 3 / pendente de decisão do Alex**: qualquer ajuste de ESCRITA além
do que já existe hoje (editar `_FRACOES`, ativar caps de `plan.py`,
rebalancear cota — tudo isso é decisão de produto/monetização, coberta pelo
ADR-010, não por este documento).

---

## Riscos abertos / o que esta proposta deliberadamente não resolve

1. **Onde e como a aplicação separada é hospedada/deployada** (subdomínio
   próprio? mesma conta Railway, serviço novo? autenticação própria ou
   reusa o mesmo login do app consumidor?) — decisão de infraestrutura do
   Alex, fora do escopo desta auditoria; ver ADR-011 para o que É decidido
   (contrato de leitura) vs. pendente (hospedagem).
2. **Nenhum candidato concreto avaliado para expandir o nível de acesso**
   além do binário admin/não-admin — a Decisão 4 propõe masking, não um
   sistema de papéis (RBAC). Se o time crescer além do Alex, isso volta à
   mesa.
3. **A trilha de eficiência de ações automáticas (Decisão 5) começa vazia**
   — só passa a acumular dado a partir do dia em que o campo `origem` for
   adicionado; não há como reconstruir retroativamente a origem de
   `history` já gravado (a informação não existia e não pode ser inferida
   com segurança).
4. **Custos por usuário quando BYOK continuam impossíveis de medir** — é
   uma escolha de arquitetura (o app nunca vê a chave do usuário), não uma
   lacuna que este módulo resolve.
5. **`plan.py`/`_FRACOES` continuam hardcoded** — o módulo VÊ que são o
   maior buraco de governança, mas ativar edição em runtime é decisão de
   produto (ADR-010), não desta proposta.

---

## Apêndice A1 — Inventário completo de variáveis de ambiente

| Item | file:line | Categoria | Editável hoje via UI? |
|---|---|---|---|
| `B3_AGENT_KILL` — kill switch global do agente | `agent.py:69` | Operacional | Não (visível read-only no admin) |
| `B3_AGENT_INTERVAL_S` — cadência base do laço (default 300s) | `agent.py:31,743,854,870` | Operacional | Não (visível read-only no admin) |
| `B3_ASSISTENTE_TETO_BRL` — teto de custo/dia do assistente | `assistente.py:44` | Operacional (freio de custo) | Não — nem visível |
| `BRAPI_TOKEN` — chave da API brapi (master de cotações) | `brapi.py:55` | Segredo | Não |
| `B3_BRAPI_COTA_MES` — cota mensal brapi (default 15000) | `brapi_budget.py:48` | Produto/Operacional | Não editável; visível (cota exibida em Fonte de dados) |
| `B3_SESSION_TTL_DAYS` — validade da sessão (default 90d) | `auth.py:27` | Operacional/segurança | Não |
| `B3_AUTH_RL_MAX`/`B3_AUTH_RL_WINDOW_S` — rate limit de login | `auth.py:160-161` | Operacional/segurança | Não |
| `GOOGLE_CLIENT_ID`/`APPLE_CLIENT_ID` — audiência OIDC | `auth.py:209,214,248` | Segredo-adjacente | Não |
| `B3_DIDATICA_OFF` — kill switch da camada didática | `conceitos.py:36` | Operacional | Não |
| `B3_ASSISTENTE_OFF` — kill switch do assistente de IA | `conceitos.py:40` | Produto/Operacional | Não |
| `B3_CANDLE_PROVIDER` — provedor ativo (default yahoo) | `candle_provider.py:194` | Operacional | Não editável; visível ("provedor:") |
| `B3_CANDLE_FALLBACK` — provedor de backup | `candle_provider.py:225` | Operacional | Não editável; visível ("backup:") |
| `B3_AGENT_QUOTE_SOURCE` — fonte exclusiva do ciclo do agente | `candle_provider.py:435` | Produto/Operacional | Não |
| `BOLSAI_API_KEY` — chave de fundamentos (usebolsai.com) | `fundamentals.py:57` | Segredo | Não |
| `B3_DB_PATH` — caminho do SQLite | `db.py:22` | Operacional/infra | Não |
| `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`/`GEMINI_API_KEY`/`B3_AGENTE_API_KEY` — chaves de LLM (modo env) | `llm.py:242-250,255` | Segredo | Não (usuário pode optar por BYOK própria) |
| `B3_INTRADAY_CONC` — concorrência intraday (default 8) | `intraday.py:44,72` | Operacional | Não |
| `B3_INTRADAY_GAP_S` — intervalo mín. entre passadas (default 240s) | `intraday.py:44,73` | Operacional | Não |
| `B3_INTRADAY_PERIOD` — janela intraday (5d\|1mo) | `intraday.py:61` | Operacional | Não |
| `B3_INTRADAY_OFF` — kill switch do intraday | `intraday.py:83` | Operacional | Não |
| `B3_MANAGED_LLM_KEY` — chave da IA gerenciada | `managed.py:24` | Segredo | Não editável; visível ("IA gerenciada: ativa/desligada") |
| `B3_MANAGED_LLM_PROVIDER` (default openai) | `managed.py:28` | Operacional | Não |
| `B3_MANAGED_LLM_MODEL` (default gpt-4o-mini) | `managed.py:29` | Produto/Operacional | Não |
| `B3_MANAGED_LLM_BASE_URL` — endpoint alternativo | `managed.py:33` | Operacional | Não |
| `B3_MANAGED_GLOBAL_DAILY_CAP` — teto global de análises/dia | `managed.py:46` | Produto | Não editável; visível ("teto global/dia") |
| `B3_MANAGED_DAILY_QUOTA` — cota diária por usuário (default 20) | `managed.py:56-58,64` | Produto | Não editável; visível ("cota/usuário/dia") |
| `B3_MANAGED_RATE_PER_MIN` — rate limit por usuário (default 6/min) | `managed.py:56-58,67` | Operacional | Não |
| `B3_GATED_HOSTS` — hosts com cadastro obrigatório | `main.py:244` | Produto | Não editável; visível ("cadastro obrigatório:") |
| `B3_ADMIN_EMAILS` — allowlist do portão de admin | `main.py:386,397,425,437,450,469` | Segredo-adjacente | Não |
| `B3_APPLE_APP_ID` — App ID p/ AutoFill iOS | `main.py:715` | Operacional/infra | Não |
| `APNS_TOPIC` — bundle id do app p/ push | `main.py:1893`, `push.py:26` | Operacional | Não editável; exposto em `/api/agent/status`, sem tela |
| `APNS_SANDBOX` — ambiente APNs | `main.py:1894`, `push.py:57,170` | Operacional | Não editável; exposto no endpoint, sem tela |
| `APNS_TEAM_ID`/`APNS_KEY_ID`/`APNS_AUTH_KEY` — credenciais .p8 | `push.py:26,30,47,50,218` | Segredo | Não |
| `B3_RADAR_DAILY_HHMM` — horário da varredura diária (default 08:45) | `radar_daily.py:38` | Operacional | Não |
| `B3_RADAR_DAILY_OFF` — kill switch do radar diário | `radar_daily.py:48` | Operacional | Não |
| `B3_SCAN_UNIVERSE` — universo de tickers escaneado | `scanner.py:40,101` | Produto | Não |
| `SIWA_KEY_ID`/`SIWA_PRIVATE_KEY` — chave Sign in with Apple | `siwa.py:34,50,52` | Segredo | Não |
| `B3_TIMING_PUSH_KILL` — kill switch de avisos de gatilho por push | `timing_watch.py:59` | Operacional | Não |

Achado de passagem (`main.py:1967-1971`): o servidor já detecta em runtime
nomes de env var com espaço sobrando (`B3_`, `APNS_`, `APPLE_`, `BOLSAI`) e
loga erro — sinal de que esse tipo de erro de configuração silenciosa já
mordeu o projeto antes.
