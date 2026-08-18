<!-- refreshed: 2026-08-18 -->
# Architecture

**Analysis Date:** 2026-08-18

## System Overview

```text
┌────────────────────────────┐      ┌───────────────────────────┐
│  iPhone (Capacitor/WKWebView)│     │  Navegador (PWA / desktop) │
│  bundle React DENTRO do app  │      │  server/web_dist           │
│  `deviceStore` (local-first) │      │  `serverStore`              │
│  `web/src/persistence.js`    │      │  `web/src/persistence.js`   │
└──────────────┬───────────────┘      └─────────────┬───────────────┘
               │ /api/* (CapacitorHttp,             │ /api/* (mesma origem,
               │ ignora CORS)                        │ fetch normal)
               ▼                                      ▼
┌───────────────────────────────────────────────────────────────────────┐
│      Railway · rootDirectory=/server · FastAPI monolítico             │
│      `server/app/main.py` (app = FastAPI(...)) + uvicorn              │
│      SQLite kv por escopo (`server/app/db.py`, `server/app/store.py`) │
│                                                                        │
│  MOTOR DETERMINÍSTICO                    CAMADA LLM (opt-in, medida)  │
│  `store.py` (buy/sell/posição/PnL)       `llm.py` (Anthropic; BYOK ou │
│  `agent.py` (execução automática,        gerenciada B3_MANAGED_LLM_*) │
│    trailing stop, alvo dinâmico,         `assistente.py` (pergunta    │
│    kill-switch)                          livre, snapshot estruturado) │
│  `scanner.py`/`radar_daily.py` (varredura)`scan_deep.py` (N1 aprofund)│
│  `timing.py`/`timing_watch.py` (gatilho) `ai_activity.py` (ledger)    │
│  `setups.py`/`indicators.py`/`kpi.py`    `conceitos.py` (didática 0$) │
│                                                                        │
│  `skill_ref.py` = vocabulário canônico por modo (Estudo × Operador)   │
│  `rbac.py` (ADR-013) · `plan.py` (ADR-010, eixo comercial separado)   │
│  `auth.py`/`siwa.py` (Apple/Google/e-mail) · `push.py` (APNs)         │
└──────────┬─────────────────────────────────────────┬──────────────────┘
           │ mount("/admin")                          │ mount("/")
           ▼                                          ▼
┌───────────────────────────┐             ┌───────────────────────────┐
│ Portal admin (`web-admin/`)│             │ App consumidor (`web/`)   │
│ servido de `server/admin_dist`│          │ servido de `server/web_dist`│
│ 10 abas, RBAC por permissão│             │ Modo Estudo × Modo Operador│
└───────────────────────────┘             └───────────────────────────┘
           │
           ▼
  Yahoo/brapi (candles+cotações, ~15 min de atraso) · B3 arquivos (opções, v2)
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| API FastAPI | Todas as rotas HTTP, monta os 3 apps estáticos, resolve `current_scope` | `server/app/main.py` |
| Motor de carteira | Compra/venda, preço médio, PnL realizado, snapshot de patrimônio | `server/app/store.py` |
| Agente autônomo | Ciclo de execução server-side (radar diário + intraday), trailing stop, alvo dinâmico, kill-switch | `server/app/agent.py` |
| Timing / gatilho | Tríade temporal (plano diário × barra 15min × timing determinístico) | `server/app/timing.py`, `server/app/timing_watch.py` |
| Setups/indicadores | Cálculo técnico determinístico (STU — fonte única N1/N2/N3) | `server/app/setups.py`, `server/app/indicators.py`, `server/app/technical_snapshot.py` |
| Fonte de cotações | Provedor único de candles/cotações (Yahoo/brapi), cache L2 persistente | `server/app/candle_provider.py`, `server/app/candle_cache.py`, `server/app/brapi.py`, `server/app/yahoo.py` |
| Vocabulário por modo | Frases canônicas Estudo × Operador, Princípio 1 ("backend calcula, LLM interpreta") | `server/app/skill_ref.py` |
| LLM / IA gerenciada | Chamada Anthropic (BYOK ou cota gerenciada), medição de custo | `server/app/llm.py`, `server/app/managed.py`, `server/app/metering.py`, `server/app/ai_activity.py` |
| Assistente conversacional | Pergunta livre sobre snapshot estruturado da tela | `server/app/assistente.py` |
| Didática determinística | Catálogo de conceitos (0 custo), setores tocáveis | `server/app/conceitos.py`, `server/app/kb.py`, `server/app/mercado_ref.py` |
| RBAC / entitlements | Grupos por macro função (ADR-013), bootstrap aditivo do admin | `server/app/rbac.py` |
| Plano comercial | Eixo separado do RBAC (ADR-010): cap de uso por plano | `server/app/plan.py` |
| Autenticação | Sessão por token, Sign in with Apple/Google, e-mail/senha, merge de identidades | `server/app/auth.py`, `server/app/siwa.py` |
| Push | Envio APNs, preferências server-side (config do iPhone é invisível pro backend) | `server/app/push.py` |
| Persistência kv | SQLite chave-valor por escopo (`user_id=None` = balde anônimo), thread-local connection | `server/app/db.py` |
| App consumidor (front) | UI completa (Estudo + Operador), single-file React | `web/src/App.jsx` |
| Camada de estado do front | Dois stores paralelos (`serverStore` web, `deviceStore` iOS), motor financeiro puro | `web/src/persistence.js`, `web/src/finance.js` |
| Vocabulário de front | Textos por modo (Estudo=professor, Operador=mesa), disclaimers | `web/src/copy.js`, `web/src/disclaimers.js` |
| Portal admin | 10 abas de observabilidade/governança, RBAC-gated no backend | `web-admin/src/App.jsx` |

## Pattern Overview

**Overall:** Monólito FastAPI que serve API + 3 bundles estáticos da mesma
origem (app consumidor web, portal admin, distribuição iOS ad-hoc), com o
mesmo bundle React do app consumidor empacotado num shell Capacitor para o
iPhone.

**Key Characteristics:**
- Separação rígida "motor × interpretação": todo número de carteira, preço,
  PnL, drawdown, timing e vocabulário de decisão vem de código determinístico
  em Python (backend) ou JS puro (front); a LLM só explica o que o motor já
  calculou (`server/app/skill_ref.py` — Princípio 1).
- Multi-tenant simples via `user_id` (escopo) numa tabela kv, sem ORM; escopo
  `None` é o "balde anônimo" usado antes do login.
- Dois eixos de controle de acesso independentes: RBAC de governança
  (`rbac.py`, ADR-013 — quem administra) e plano comercial (`plan.py`,
  ADR-010 — quanto de IA cada conta pode gastar). Nunca se sobrepõem.
- "Dois apps em um" no front: o mesmo bundle React roda em Modo Estudo e
  Modo Operador, alternando vocabulário/tema/comportamento por uma única flag
  de config (`appMode`), nunca por rota ou build separado.
- Deploy de superfície administrativa desacoplado do app consumidor: mudar
  `web-admin/` é minutos (`publicar-admin.sh`, sem review de loja); mudar
  `web/` no iPhone exige TestFlight/App Store.

## Layers

**Camada de dados de mercado:**
- Purpose: obter/normalizar candles, cotações, fundamentos e opções
- Location: `server/app/candle_provider.py`, `candle_cache.py`, `brapi.py`, `brapi_budget.py`, `yahoo.py`, `fundamentals.py`, `options_provider_yahoo.py`
- Contains: chamadas HTTP a Yahoo/brapi, cache SQLite L2, orçamento de requisições
- Depends on: nada dentro do repo (fonte externa)
- Used by: motor de setups/indicadores, agente, rotas `/api/quotes`, `/api/history`, `/api/technicals`

**Motor determinístico (simulação):**
- Purpose: regras de negócio da carteira virtual — nunca calculado pela IA
- Location: `server/app/store.py` (buy/sell/posição), `server/app/agent.py` (execução automática), `server/app/setups.py`/`indicators.py`/`kpi.py`/`regime.py` (análise técnica), `server/app/timing.py`/`timing_watch.py` (gatilho)
- Contains: preço médio, PnL realizado/aberto, drawdown, trailing stop, alvo dinâmico, kill-switch
- Depends on: camada de dados de mercado, `db.py` para persistência
- Used by: rotas HTTP em `main.py`, o próprio `agent.py` (scheduler_loop)

**Camada LLM (opt-in, medida):**
- Purpose: interpretação em linguagem natural do que o motor já calculou
- Location: `server/app/llm.py`, `assistente.py`, `scan_deep.py`, `managed.py`, `metering.py`, `ai_activity.py`
- Contains: chamadas Anthropic, ledger de custo, teto diário por conta/gerenciado
- Depends on: motor determinístico (recebe snapshot pronto, nunca lê estado bruto)
- Used by: rotas `/api/analyze`, `/api/technical/analyze`, `/api/assistente`, `/api/scan/deep`

**Governança / acesso:**
- Purpose: quem pode ver/mudar o quê no servidor
- Location: `server/app/rbac.py` (ADR-013), `server/app/auth.py`, `server/app/siwa.py`, `server/app/audit.py`, `server/app/plan.py`
- Contains: grupos de permissão, bootstrap aditivo, log de auditoria de escrita admin
- Depends on: `db.py` (tabela de roles/sessões)
- Used by: `require_permission()`/`require_any_admin_permission()` em rotas `/api/admin/*`

**Front consumidor (`web/`):**
- Purpose: toda a UI do app (Estudo + Operador), única base para web e iOS
- Location: `web/src/App.jsx` (single-file, ~7600 linhas), `web/src/persistence.js`, `web/src/finance.js`, `web/src/copy.js`
- Contains: componentes React, motor financeiro do front (espelho do backend), dois stores de estado
- Depends on: API do backend (`web/src/api.js`)
- Used by: navegador (PWA) e shell Capacitor (iPhone)

**Portal admin (`web-admin/`):**
- Purpose: observabilidade e governança (10 abas), separado do app consumidor
- Location: `web-admin/src/App.jsx`, `web-admin/src/EditorTexto.jsx`, `web-admin/src/api.js`
- Contains: dashboards de custo/uso, kill-switch, editor de prompts, gestão de usuários/papéis
- Depends on: rotas `/api/admin/*`, `/api/obs/*`, `/api/analytics/*` (todas `require_permission`-gated)
- Used by: navegador desktop; a partir de 2026-08-17 também abre dentro de um browser in-app no iOS via handoff de sessão (ADR-014)

## Data Flow

### Compra de ação (Carteira, ambos os modos)

1. Front chama `store.buy(t, qty, meta)` — `web/src/persistence.js:978` (web, via `api.buy`) ou local (`deviceStore`, iOS)
2. Backend recebe `POST /api/buy` (`server/app/main.py:1501`), valida ticker, busca cotação viva via `candle_provider.get_quote`, valida caixa suficiente
3. `store.buy(conn, t, qty, price, ...)` grava posição (preço médio ponderado se já existir), debita caixa, insere entrada no histórico — `server/app/store.py:530-563`
4. `main.py:1515` dispara reavaliação imediata do ciclo do agente (`_disparar_ciclo_imediato`) — não espera o próximo tick agendado
5. Resposta devolve `store.public_state(...)` (estado completo) + `priceUsed`

### Ciclo autônomo do Operador (execução automática)

1. `agent.scheduler_loop` roda dentro do próprio processo do servidor (sem cron externo) — `server/app/agent.py:874`
2. Verifica `kill_switch_on()` (memória → DB → env, mesmo padrão do orçamento brapi) antes de qualquer ação — `server/app/agent.py:154-206`
3. `run_cycle_for`/`_run_cycle_inner` avalia entradas (`_avaliar_entradas`), opções (`_avaliar_opcoes`), trailing stop (`nivel_trailing`) e alvo dinâmico (`avaliar_alvo_dinamico`) por escopo/conta
4. Operações executadas chamam as mesmas funções determinísticas de `store.py` (buy/sell) que a rota manual usa — não há caminho de execução paralelo

**State Management:**
- Backend: SQLite kv por escopo, uma conexão real por thread atrás de um wrapper (`server/app/db.py:51` `_ThreadLocalConnection`) — necessário porque o pool de threads do FastAPI/anyio quebra com uma única conexão SQLite compartilhada.
- Front: dois stores completos e paralelos, escolhidos em runtime por `isNative` — `web/src/persistence.js:1171` (`export const store = isNative ? deviceStore() : serverStore();`).

## Key Abstractions

**Escopo (`user_id`):**
- Purpose: isola dados por conta numa única tabela kv, sem multi-tenância por schema
- Examples: toda função em `store.py`/`db.py` recebe `user_id=None|str`
- Pattern: `None` = "balde anônimo" (pré-login); resolvido por `current_scope()` a partir do Bearer token (`server/app/main.py:94`)

**Vocabulário por modo (`skill_ref.vocab`):**
- Purpose: fonte única de frases/vereditos por Modo Estudo vs Modo Operador
- Examples: `server/app/skill_ref.py` (`vocab["educacional"]`, `vocab["operador"]`, `TIMING[modo][estado]`)
- Pattern: o front nunca compõe vocabulário — recebe a frase pronta do backend; espelhado no front em `web/src/copy.js` (`COPY.estudo`/`COPY.operador`)

**Dois stores paralelos (`serverStore`/`deviceStore`):**
- Purpose: web usa estado no servidor; iOS é local-first (localStorage)
- Examples: `web/src/persistence.js:97` (`serverStore`), `web/src/persistence.js:214` (`deviceStore`)
- Pattern: cada método (buy/sell/putConfig/...) precisa existir nos DOIS, com o mesmo contrato — paridade testada em `web/tests/test_api_parity.mjs`; `deviceStore` reimplementa em JS a mesma aritmética de `store.py` (comentários "espelho de store.py")

**RBAC por grupos de macro função (ADR-013):**
- Purpose: permissão nomeada por função de produto, não lista solta de flags técnicas
- Examples: `server/app/rbac.py` (`GRUPOS`, `ROLE_ADMIN`, `require_permission()`)
- Pattern: composição via `Depends()` no FastAPI — nunca esconder só no botão da UI; bootstrap aditivo garante que quem já era admin binário (`_is_obs_admin`) nunca perde acesso

**Tríade temporal (ADR-002):**
- Purpose: toda afirmação de timing carrega o carimbo da barra e a ressalva de atraso
- Examples: `server/app/timing.py`, `server/app/timing_watch.py`, `server/app/radar_daily.py`
- Pattern: plano diário do Radar × barra de 15min FECHADA × timing determinístico (`armado/gatilho/esticado`)

## Entry Points

**API FastAPI:**
- Location: `server/app/main.py` (`app = FastAPI(...)`, linha 43)
- Triggers: uvicorn (Railway, `server/railway.json` / `server/Procfile`)
- Responsibilities: todas as rotas `/api/*`, monta `/admin` (admin_dist), `/ios` (ios_dist), `/` (web_dist, catch-all — DEVE ser o último `app.mount()`)

**Agente autônomo (scheduler):**
- Location: `server/app/agent.py:874` (`scheduler_loop`)
- Triggers: iniciado junto com o processo do servidor (sem cron externo); também disparável sob demanda via `POST /api/agent/run-now` (`main.py:2190`) ou imediatamente após buy/sell/stop-alvo (`_disparar_ciclo_imediato`)
- Responsibilities: radar diário, passada intraday, trailing stop, alvo dinâmico, avisos de gatilho/push

**App consumidor (React):**
- Location: `web/src/main.jsx` → `web/src/App.jsx`
- Triggers: carregado como PWA (`server/web_dist`, mesma origem do backend) ou dentro do shell Capacitor no iPhone (bundle embutido no binário, sem `server.url`)
- Responsibilities: toda a UI, Modo Estudo × Modo Operador

**Portal admin (React):**
- Location: `web-admin/src/main.jsx` → `web-admin/src/App.jsx`
- Triggers: navegação direta em `/admin/*` (desktop) ou abertura in-app via browser embutido no iOS (handoff de sessão, ADR-014)
- Responsibilities: as 10 abas de observabilidade/governança, todas RBAC-gated no backend

## Architectural Constraints

- **Threading:** FastAPI/uvicorn com pool de threads (anyio); SQLite exige
  uma conexão POR THREAD — resolvido por `_ThreadLocalConnection`
  (`server/app/db.py:51-79`). Nunca crie uma conexão sqlite3 global fora
  desse wrapper — quebra com `SQLite objects created in a thread can only be
  used in that same thread`.
- **Global state:** kill-switch do agente e orçamento da brapi seguem o
  mesmo padrão memória → DB → env (`server/app/agent.py:154-206`,
  `server/app/brapi_budget.py`) — o override precisa ser lido do SQLite em
  runtime, não só do env, senão um deploy zera a proteção.
- **Ordem de `app.mount()` importa:** `/ios` e `/admin` precisam ser
  montados ANTES do mount catch-all `/` (`server/web_dist`), senão o
  StaticFiles genérico intercepta as rotas mais específicas
  (`server/app/main.py:2396-2418`).
- **Deploy só enxerga `server/`:** o `rootDirectory` do Railway é `/server`
  — qualquer arquivo fora dessa árvore (mesmo versionado, mesmo testado
  localmente) não vai para produção. Front web e admin são publicados como
  bundles TRACKED dentro de `server/web_dist`/`server/admin_dist`
  (`scripts/publicar-web.sh`, `scripts/publicar-admin.sh`), nunca por CI
  automático.
- **App nativo carrega bundle local, sem `server.url`:** `web/capacitor.config.ts`
  não define `server` — o JS do iPhone só muda com rebuild
  (`instalar.sh --iphone`); o texto do backend muda com deploy comum. Isso
  significa que `/admin/*` não é uma URL navegável dentro do WKWebView do
  app — precisa do handoff de sessão do ADR-014.
- **Paridade obrigatória entre pares de arquivo:** `server/app/defaults.py`
  ↔ `web/src/catalog.js` (prompts, byte a byte) e `deviceStore` ↔
  `serverStore` em `web/src/persistence.js` — todo campo/método novo entra
  nos DOIS lados, sob pena de o iOS e o web divergirem silenciosamente.

## Anti-Patterns

### Confiar na LLM para números de carteira/decisão

**What happens:** um card ou resposta de assistente calcula preço médio,
PnL, drawdown ou veredito de timing "na hora", sem passar pelo motor
determinístico.
**Why it's wrong:** viola o Princípio 1 (`server/app/skill_ref.py`) e o
guardrail regulatório do CLAUDE.md — a manchete do card e qualquer número
exibido têm que vir do cálculo determinístico, nunca da IA.
**Do this instead:** o backend calcula (`store.py`, `finance.js`,
`timing.py`) e serve o número/frase pronta; a LLM só explica o que já veio
calculado (`assistente.py` recebe snapshot estruturado, nunca lê estado
bruto ou compõe número).

### Esconder admin só no front

**What happens:** um botão ou aba nova do `web-admin/` é escondido pela UI
mas a rota do backend não tem `require_permission`/`require_any_admin_permission`.
**Why it's wrong:** o gate real do ADR-013 é sempre backend — qualquer
chamada direta à API (curl, devtools) contornaria o cosmético do front.
**Do this instead:** toda rota `/api/admin/*` nova entra na tabela de rotas
cobertas por `server/tests/test_adr013_cobertura_rotas.py`; o front só
decide se MOSTRA o botão, nunca se a ação é permitida.

### Adicionar campo em store novo sem espelhar no outro

**What happens:** um campo ou método novo é adicionado só em `serverStore`
(ou só em `deviceStore`) em `web/src/persistence.js`, ou só em
`server/app/defaults.py` sem tocar `web/src/catalog.js`.
**Why it's wrong:** iOS (deviceStore, local-first) e web (serverStore)
divergem silenciosamente — um bug já vazou por isso (ver
`docs/adr/014-administracao-mobile.md`, seção "Alternativas consideradas").
**Do this instead:** todo campo/método novo entra nos DOIS lados do par;
`web/tests/test_api_parity.mjs` e o teste de paridade de `defaults.py`
cobrem parte disso, mas não tudo — revisão manual do par é obrigatória.

## Error Handling

**Strategy:** HTTPException do FastAPI com status code semântico (400
validação, 401/403 auth/permissão, 502 fonte de dados externa indisponível);
o front nunca inventa dado quando a fonte falha — mostra o estado de erro.

**Patterns:**
- Fonte de mercado indisponível: rota levanta `HTTPException(502, "Sem
  cotacao para " + t)` (`server/app/main.py:1509`) em vez de simular um
  preço.
- Rotas admin: `require_permission(perm)` levanta 403 com a permissão
  faltante nomeada (`server/app/main.py:127`); front consumidor auto-esconde
  seções mistas ao capturar 403 (`adminDenied`/`obsDenied` em `App.jsx`).

## Cross-Cutting Concerns

**Logging:** `server/app/obslog.py` — log estruturado + ring buffer,
consumido pela aba Custos/Visão Geral do portal admin.

**Validation:** validação de payload é manual (dict + checagem de tipo/faixa)
em cada rota de `main.py`; não há schema Pydantic/BaseModel — `Body(default={})`
com leitura defensiva por chave.

**Authentication:** Bearer token resolvido por `current_scope()` (opcional,
rotas de dado funcionam sem login) e `require_user()`/`require_permission()`
(obrigatório, rotas de conta e admin) — `server/app/main.py:94-140`.

---

*Architecture analysis: 2026-08-18*
