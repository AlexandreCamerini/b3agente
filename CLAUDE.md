# CLAUDE.md — Agente do produto Boris+ (b3-agente)

Você é um especialista sênior em produto financeiro educacional, engenharia de
dados de mercado, UX e sistemas de simulação. Este aplicativo é um **simulador
educacional de ações da B3 com dados reais de mercado e dinheiro exclusivamente
virtual**.

## Objetivo do produto

Permitir que o usuário treine decisões de investimento e trading com cotações,
gráficos, indicadores e eventos reais, sem executar operações financeiras
reais e sem colocar o patrimônio do usuário em risco.

**Posicionamento:** "Treine com o mercado real. Aprenda a operar. Sem pôr
dinheiro em risco."

## Princípios obrigatórios

1. O aplicativo deixa claramente visível que todo o saldo é fictício.
2. Nenhuma ação envia ordens para corretora, bolsa ou conta bancária.
3. Dados de mercado exibem fonte, horário da última atualização e se são em
   tempo real, atrasados ou históricos.
4. Se a fonte de dados falhar, estiver atrasada ou incompleta, não invente
   valores. Mostre o estado correto e impeça operações dependentes de dados
   inválidos.
5. Cotações, posições, ordens, saldo, custos, lucro, prejuízo e rentabilidade
   são calculados por regras determinísticas, nunca pela IA.
6. A IA pode explicar indicadores, cenários e resultados; ela não promete
   rentabilidade, não inventa números e não apresenta recomendação
   personalizada como certeza.
7. Toda análise gerada por IA informa quando usa dados históricos, atrasados
   ou insuficientes.
8. Sem linguagem de enriquecimento rápido, promessa de acerto ou garantia de
   lucro.
9. Estados completos: carregamento, vazio, erro, mercado fechado, dado
   atrasado, ordem rejeitada, ordem parcialmente executada, operação concluída.
10. Acessibilidade, linguagem clara, responsividade mobile e transparência
    sobre riscos.

## Modelo de simulação

Antes de alterar qualquer coisa, inspecione o código existente e identifique:
origem dos dados de mercado; frequência de atualização; ativos e bolsas
suportados; motor de ordens; tipos de ordem; regras de execução; custos e
taxas; cálculo de posição, preço médio, lucro e prejuízo; persistência do
saldo e do histórico; componentes que exibem recomendações ou análises de IA.

O sistema mantém (e toda mudança preserva):

- saldo virtual inicial claramente identificado;
- cada ordem simulada com preço, quantidade, horário, tipo, status e motivo de
  rejeição;
- preço de execução respeitando os dados disponíveis no momento da operação;
- custos, spread, slippage e taxas configuráveis e exibidos;
- carteira com patrimônio, dinheiro disponível, posições, exposição,
  lucro/prejuízo e drawdown;
- histórico de todas as decisões e operações;
- comparação de desempenho com um benchmark;
- resultados positivos e negativos apresentados sem manipulação visual.

## Camada educacional

Criar ou preservar explicações objetivas sobre: tendência; momentum; valor;
qualidade; volatilidade; suporte e resistência; rompimentos; reversão à média;
diversificação; risco-retorno; drawdown; expectativa matemática; diferença
entre taxa de acerto e rentabilidade.

A IA responde com base nos dados fornecidos pelo sistema. Quando não houver
evidência suficiente, diz explicitamente: **"Não há dados suficientes para
concluir."**

A IA não deve: garantir que uma operação dará lucro; afirmar que uma
confluência tem 100% de chance de sucesso; inventar estatísticas; ocultar
perdas; transformar uma simulação em recomendação financeira; executar
qualquer operação real.

## Experiência principal

1. escolher ativo → 2. visualizar dados e horário da atualização →
3. analisar contexto e risco → 4. enviar ordem virtual → 5. acompanhar
execução simulada → 6. visualizar resultado → 7. receber explicação
educacional → 8. registrar o aprendizado e comparar com o benchmark.

## Protocolo de trabalho

- Leia a documentação do projeto (`docs/`, `docs/adr/`, `qa/`) e os arquivos
  de instrução locais antes de implementar.
- Faça um inventário do que já existe. Não reescreva a aplicação sem
  necessidade. Não adicione funcionalidades fora do escopo pedido.
- Apresente um plano curto com arquivos afetados, riscos e critérios de
  aceite; só depois implemente.
- Ao final de cada entrega: resumo do que foi alterado; arquivos modificados;
  testes executados e resultados; limitações conhecidas; instruções para
  validar localmente.

## Validação obrigatória

- Suíte canônica: `bash scripts/executar.sh --testes` — roda as DUAS suítes
  (pytest do backend + `web/tests/*.mjs`). `scripts/test.sh` sozinho é meia
  baseline e não conta como validação.
- Front editado → `npx vite build` antes de declarar ok (grep e teste
  estático não pegam erro de sintaxe JS).
- Cobre: motor de simulação (unitário), integração de dados e ordens, cálculos
  de saldo/posição/preço médio/lucro/prejuízo/drawdown, falha da fonte de
  dados, dados atrasados, ordem rejeitada, responsivo mobile, acessibilidade
  básica.

## Guardrails do repositório (invariantes — não re-litigar)

- **Bundle id `com.alexandrecamerini.bolsia` não muda** (trocá-lo publica
  outro app e quebra o login SIWA). Codinomes internos ficam: `b3-agente/`,
  `B3_*`, chaves `b3-*`, env `BOLSIA_*` do masstest.
- **Paridade obrigatória**: `server/app/defaults.py` ↔ `web/src/catalog.js`
  (prompts, byte a byte — teste trava) e `deviceStore` ↔ `serverStore` em
  `web/src/persistence.js` (método/campo novo entra nos DOIS).
- **Manchete do card vem SÓ do motor determinístico** (guardrail CVM); a IA
  explica, nunca substitui.
- **Stop/alvo nunca são vetados**: `operar: false` é parecer, não veto; a UI
  sempre permite Aplicar proteção.
- **Guardiões de teste não se apagam** — reversão deliberada atualiza o
  guardião com nota.
- **Histórico não se reescreve**: `qa/`, `ESTADO-*`, `CHECKOUT-*`, RELEASES
  preservam o texto da época.
- **Publicação**: `scripts/bump.sh` antes de `publicar-web.sh`; nunca editar
  `server/web_dist` direto. Deploy só-backend: bump manual de
  `SERVER_BUILD_ID`.
- **Fontes de dados**: decisões em `docs/adr/001` e `docs/adr/008` (brapi
  gratuita master de diário/spot com orçamento de requisições; Yahoo backup e
  fonte do intraday). Segredos (`BRAPI_TOKEN` etc.) só em env do
  servidor/Railway, nunca no bundle do front nem commitados.
- **Login obrigatório** (conta é núcleo: sync, Operador server-side, push);
  conta nova nasce limpa; sem posições-demo no estado inicial.

<!-- GSD:project-start source:PROJECT.md -->
## Project

**Boris+ (b3-agente)**

Simulador educacional de ações da B3 com dados reais de mercado e dinheiro
exclusivamente virtual. Ensina a mecânica da bolsa brasileira — setups,
indicadores, gestão de risco — através de um Modo Estudo (a IA orienta, nunca
executa) que evolui para um Modo Operador (ferramentas automáticas e análises
mais profundas, com execução simulada). Web/PWA + app iOS nativo (mesmo
bundle via Capacitor), backend Python/FastAPI, portal de administração
separado. Vai ser comercializado: funções básicas grátis com cota pequena de
análises de IA, escalando para planos pagos.

**Core Value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado
funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem
acesso a automações do Modo Operador. Se o storyline pedagógico não convencer,
nada mais no produto importa.

### Constraints

- **Produto**: bundle id `com.alexandrecamerini.bolsia` não muda (login SIWA
  depende disso) — qualquer achado sobre branding/nome não pode sugerir isso
- **Financeiro**: cotações, posições, ordens, saldo, custos, lucro/prejuízo e
  drawdown são sempre calculados por regra determinística, nunca pela IA —
  qualquer achado que aproxime IA de cálculo financeiro é severidade alta
- **Dado de mercado**: brapi é master gratuita com orçamento de requisições
  (15k/mês para o app inteiro), Yahoo é backup/intraday — não é diferencial
  de plano pago (ADR-010, decisão 3)
- **Regulatório**: manchete do card de decisão vem só do motor determinístico
  (guardrail CVM); IA explica, nunca substitui
- **Deploy**: Railway com `rootDirectory=/server`; só `server/` é publicado,
  por isso `web_dist`/`admin_dist`/`ios_dist` ficam versionados no git
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.14 — backend (`server/app/*.py`), FastAPI app, stdlib-first (SQLite via `sqlite3`, PBKDF2 via `hashlib`)
- JavaScript (ES modules, JSX) — web/PWA/iOS client (`web/src/*.js`, `web/src/*.jsx`) and admin portal (`web-admin/src/`)
- TypeScript — only `web/capacitor.config.ts` (Capacitor native shell config); root `package.json` pulls in `typescript@^6.0.3` as a devDependency but there is no `tsconfig.json` / typed app code
- Shell (bash) — all operational tooling: `scripts/*.sh`, root-level `*.sh` (deploy, test, audit, release orchestration)
## Runtime
- Python 3.14 (local `.venv` observed at `server/.venv`); no `runtime.txt`/`.python-version` pin found — Railway (Nixpacks) picks its own default unless overridden
- ASGI server: `uvicorn[standard]>=0.29` (`server/requirements.txt`), started as `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (`server/Procfile`, `server/railway.json`)
- Node.js (version not pinned via `.nvmrc`/`engines`) — Vite 6 build for both `web/` (consumer PWA + Capacitor iOS shell) and `web-admin/` (observability/admin portal)
- Native shell: Capacitor 8 wraps `web/dist` for iOS (`web/capacitor.config.ts`, `appId: com.alexandrecamerini.bolsia`)
- Python: pip, split manifests `server/requirements.txt` (dev/test superset) and `server/requirements-prod.txt` (prod-only, no lockfile/hashes)
- JS: npm — `package-lock.json` present at repo root; `web/` and `web-admin/` are independent npm projects without workspaces (no root lockfile covering their deps was found aggregated — each has its own `package.json`)
## Frameworks
- FastAPI `>=0.110` — single ASGI app in `server/app/main.py`; serves JSON API plus mounts static builds (web app, admin portal, iOS dist) from the same process
- `httpx>=0.27` (async) — all outbound HTTP (brapi, Yahoo, BolsAI, Anthropic/OpenAI/Google LLM calls, Apple SIWA/APNs)
- `PyJWT[crypto]>=2.8` + `h2>=4.1` — ID-token verification (Apple/Google OAuth) and ES256 JWT signing (Sign in with Apple client-secret, APNs auth key); HTTP/2 support for APNs
- React `^18.3.1` (web + web-admin), no framework router/state library — hand-rolled state in `web/src/App.jsx` and `web/src/persistence.js`
- `lightweight-charts ^4.2.0` — candle/price charting
- `@uiw/react-codemirror` + `@codemirror/*` + `@lezer/*` — prompt/markdown editor in the admin portal (byte-exact prompt editing, see `docs/adr` on portal admin)
- `vite-plugin-pwa ^0.21.1` — PWA manifest/service worker generation for `web/`
- Python: `pytest>=8.0`, tests under `server/tests/` (87 files)
- JS: no framework dependency listed; `web/tests/*.mjs` run as plain Node scripts (invoked via `scripts/executar.sh --testes`, not through Vitest/Jest)
- Vite `^6.0.0` (`web/vite.config.js`, `web-admin/`) with `@vitejs/plugin-react`
- Capacitor CLI `^8.0.0` (`cap sync`, `cap open ios`) for the native iOS wrapper
## Key Dependencies
- `fastapi`, `uvicorn[standard]`, `httpx` — HTTP surface and all outbound calls
- `PyJWT[crypto]` — Sign in with Apple / Google ID-token verification, SIWA client-secret JWT, APNs auth JWT
- stdlib `sqlite3` — sole persistence engine (no ORM, no external DB driver)
- `@capgo/capacitor-social-login` (`latest`, unpinned) — single plugin bridging both Apple and Google native login (replaced two abandoned community plugins)
- `@capacitor/push-notifications`, `@capacitor/local-notifications` — APNs bridge and local notification presentation
- `@capacitor-community/text-to-speech` — native TTS for the in-app assistant ("Boris" voice), replacing browser `speechSynthesis`
- `@capacitor/browser`, `@capacitor/app-launcher` — in-app browser handoff (used to open the admin portal from the mobile app, ADR-014)
- No cache/queue service (Redis, etc.) — caching is in-process memory + SQLite `kv` table (`server/app/db.py`, `candle_cache.py`, `brapi_budget.py`)
- No ORM/migration framework — `server/app/db.py` runs hand-written `CREATE TABLE IF NOT EXISTS` / ad hoc migration functions (e.g. `_migrate_identities_from_users`) on every `connect()`
## Configuration
- All backend config via `os.environ` (no `.env` loader library in requirements — Railway injects env vars directly; local dev presumably exports vars manually or via `scripts/`)
- Prefix convention: `B3_*` for app config/feature flags, `BRAPI_TOKEN`/`BOLSAI_API_KEY` for market-data providers, `APNS_*`/`SIWA_*`/`APPLE_CLIENT_ID`/`GOOGLE_CLIENT_ID` for auth/push, `B3_MANAGED_LLM_*` for the server-funded (non-BYOK) LLM path
- Frontend build-time config via Vite `import.meta.env.VITE_*` (e.g. `VITE_API_BASE`, `VITE_GOOGLE_IOS_CLIENT_ID`, `VITE_GOOGLE_WEB_CLIENT_ID`) — baked into the JS bundle at build time, not runtime-injectable
- Secrets (`BRAPI_TOKEN`, `BOLSAI_API_KEY`, `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`/`GEMINI_API_KEY` for managed LLM, `SIWA_PRIVATE_KEY`, `APNS_AUTH_KEY`) live only in server env (Railway), never in the client bundle or git — per repo guardrail in `CLAUDE.md`
- `server/railway.json` — Nixpacks builder, health check `/api/health`, restart-on-failure ×3
- `web/vite.config.js` — dev proxy `/api` → `localhost:8787`; PWA manifest with `navigateFallbackDenylist: [/^\/admin/]` so the service worker doesn't hijack the admin portal route
- `web/capacitor.config.ts` — native iOS build config, `CapacitorHttp: { enabled: true }` to bypass CORS for direct brapi calls from the device
## Platform Requirements
- Python 3.14 venv under `server/.venv`
- Node.js + npm for `web/` and `web-admin/` (separate installs, no workspace root)
- Xcode (for `cap open ios` / TestFlight builds) — see `TESTFLIGHT.md`, `resources/ios/`
- Single Railway service running the FastAPI app (`server/`), which also serves the compiled web app (`server/web_dist`), the admin portal (`server/admin_dist`), and the iOS ancillary files (`server/ios_dist`, e.g. `apple-app-site-association`) as static mounts from the same origin
- SQLite database file on Railway's ephemeral disk (`B3_DB_PATH`, default `server/data/b3_agente.db`) — app is documented as "stateless for the phone" (device is source of truth for most user state; server DB backs multi-user accounts, sessions, admin config, budgets)
- No containerfile/Dockerfile found — deploy relies on Railway's Nixpacks auto-detection of `server/requirements.txt`
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Project Shape
- `server/` — Python 3 / FastAPI backend (`server/app/*.py`), SQLite persistence.
- `web/` — Vite + React (JSX) frontend, wrapped by Capacitor for iOS (`web/src/*.js`, `*.jsx`).
- `web-admin/` — separate Vite + React admin portal, own `package.json` (`web-admin/src/`).
## Naming Patterns
- Modules: `snake_case.py`, one module per domain concept (`brapi_budget.py`, `candle_cache.py`, `technical_snapshot.py`).
- Functions/variables: `snake_case`. Private/module-internal helpers prefixed `_` (`_eh_default_antigo`, `_call_llm`, `_spy`).
- Portuguese identifiers are common for domain concepts (`ensure_defaults`, `_eh_default_antigo`, `default_llm_prompts_ativo`) — do not force English renames; match the existing mix.
- Constants: `UPPER_SNAKE_CASE` (`SECTIONS`, `LEGACY_PROMPT_SHA256`, `FORMAT_PRO`).
- Files: `camelCase.js`/`PascalCase.jsx` for React components (e.g. `web/src/pet/Boris.jsx`, `web-admin/src/EditorTexto.jsx`); plain modules lowercase (`persistence.js`, `catalog.js`, `finance.js`).
- Functions/variables: `camelCase`. Exported pure functions read as verbs (`portfolioMetrics`, `sizingPlano`, `dayReturnPct`).
- React components: `PascalCase` (`PetFab`, `BorisChat`, `SetorAlvo`).
- Constants: `UPPER_SNAKE_CASE` for module-level fixed values (`PROD_BASE`, `TIMEOUT_MS`, `CATALOG_TICKERS`).
- Backend: `server/tests/test_<feature>.py`, functions `def test_<description_in_snake_case>():`.
- Web: `web/tests/test_<feature>.mjs` — one file per feature/bugfix, not one-per-module.
## Code Style
## Comments — carry decision history, not restatement
## Error Handling
- Domain errors → `raise HTTPException(status_code, message)`, with the message as user-facing PT-BR text (`raise HTTPException(401, "Faça login para continuar.")`).
- A global handler catches anything unhandled and normalizes it to JSON instead of an opaque 500:
- Custom exception classes exist for domain-specific rejections (e.g. `brapi.ForaDoPlano` in `server/app/brapi.py`, tested via `pytest.raises(brapi.ForaDoPlano, match="15m")`). Prefer a named exception over a generic `ValueError` when the caller needs to branch on the failure reason.
- Never invent/estimate a value on failure — return the real error state. This is a product-level invariant from `CLAUDE.md` (item 4), not just a style preference: market-data failures must surface as errors, not fabricated numbers.
- All HTTP responses are read as text first (`readBody`), never `.json()` directly — the iOS WKWebView can throw a raw, unhelpful parse error on non-JSON bodies. `readBody` strips BOM/code-fences before attempting `JSON.parse`.
- `enrichErrorMessage(status, data, path)` turns a raw HTTP error into a structured, actionable message (provider/model/keySource/action/hint), consumed by the UI as `e.message`. When adding a new API-error path, populate `detail.action`/`detail.hint` server-side so the client message stays actionable instead of falling back to `"HTTP 502"`.
- Timeouts are explicit and different per call class: `TIMEOUT_MS = 15000` for regular calls, `TIMEOUT_LLM = 90000` for AI/analysis calls. Use the LLM timeout constant for any new LLM-backed endpoint, not the default.
## Async Patterns
## Module Design
## Function Design
- Small, single-purpose functions preferred, especially in the pure-logic modules (`web/src/finance.js`, `server/app/indicators.py`) — these are unit-tested directly with known inputs/outputs.
- Pure functions (no I/O, no side effects) are deliberately separated from I/O/orchestration code so they can be tested without mocking (`finance.js`, `plan.js`, most of `indicators.py`). When adding new calculation logic, keep it pure and put I/O in the caller.
- Guard clauses over nested conditionals for early-return validation (`if (!risco || risco <= 0 || !entrada || !cap) return null;`).
## Return Values
- Backend: JSON-serializable dicts; nullable numeric fields use `null` explicitly, never `0.0` as a stand-in for "unknown" — this is a house rule enforced by a guardian test (`test_m3_format_pede_null_nunca_zero`, asserting the LLM prompt format text says `"use null (nunca 0.0"`).
- Frontend calculation functions return small result objects (`{ curve, series, days, retAcum, drawdown, base, end }`) rather than tuples/arrays, so callers destructure by name.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## System Overview
```text
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
- Separação rígida "motor × interpretação": todo número de carteira, preço,
- Multi-tenant simples via `user_id` (escopo) numa tabela kv, sem ORM; escopo
- Dois eixos de controle de acesso independentes: RBAC de governança
- "Dois apps em um" no front: o mesmo bundle React roda em Modo Estudo e
- Deploy de superfície administrativa desacoplado do app consumidor: mudar
## Layers
- Purpose: obter/normalizar candles, cotações, fundamentos e opções
- Location: `server/app/candle_provider.py`, `candle_cache.py`, `brapi.py`, `brapi_budget.py`, `yahoo.py`, `fundamentals.py`, `options_provider_yahoo.py`
- Contains: chamadas HTTP a Yahoo/brapi, cache SQLite L2, orçamento de requisições
- Depends on: nada dentro do repo (fonte externa)
- Used by: motor de setups/indicadores, agente, rotas `/api/quotes`, `/api/history`, `/api/technicals`
- Purpose: regras de negócio da carteira virtual — nunca calculado pela IA
- Location: `server/app/store.py` (buy/sell/posição), `server/app/agent.py` (execução automática), `server/app/setups.py`/`indicators.py`/`kpi.py`/`regime.py` (análise técnica), `server/app/timing.py`/`timing_watch.py` (gatilho)
- Contains: preço médio, PnL realizado/aberto, drawdown, trailing stop, alvo dinâmico, kill-switch
- Depends on: camada de dados de mercado, `db.py` para persistência
- Used by: rotas HTTP em `main.py`, o próprio `agent.py` (scheduler_loop)
- Purpose: interpretação em linguagem natural do que o motor já calculou
- Location: `server/app/llm.py`, `assistente.py`, `scan_deep.py`, `managed.py`, `metering.py`, `ai_activity.py`
- Contains: chamadas Anthropic, ledger de custo, teto diário por conta/gerenciado
- Depends on: motor determinístico (recebe snapshot pronto, nunca lê estado bruto)
- Used by: rotas `/api/analyze`, `/api/technical/analyze`, `/api/assistente`, `/api/scan/deep`
- Purpose: quem pode ver/mudar o quê no servidor
- Location: `server/app/rbac.py` (ADR-013), `server/app/auth.py`, `server/app/siwa.py`, `server/app/audit.py`, `server/app/plan.py`
- Contains: grupos de permissão, bootstrap aditivo, log de auditoria de escrita admin
- Depends on: `db.py` (tabela de roles/sessões)
- Used by: `require_permission()`/`require_any_admin_permission()` em rotas `/api/admin/*`
- Purpose: toda a UI do app (Estudo + Operador), única base para web e iOS
- Location: `web/src/App.jsx` (single-file, ~7600 linhas), `web/src/persistence.js`, `web/src/finance.js`, `web/src/copy.js`
- Contains: componentes React, motor financeiro do front (espelho do backend), dois stores de estado
- Depends on: API do backend (`web/src/api.js`)
- Used by: navegador (PWA) e shell Capacitor (iPhone)
- Purpose: observabilidade e governança (10 abas), separado do app consumidor
- Location: `web-admin/src/App.jsx`, `web-admin/src/EditorTexto.jsx`, `web-admin/src/api.js`
- Contains: dashboards de custo/uso, kill-switch, editor de prompts, gestão de usuários/papéis
- Depends on: rotas `/api/admin/*`, `/api/obs/*`, `/api/analytics/*` (todas `require_permission`-gated)
- Used by: navegador desktop; a partir de 2026-08-17 também abre dentro de um browser in-app no iOS via handoff de sessão (ADR-014)
## Data Flow
### Compra de ação (Carteira, ambos os modos)
### Ciclo autônomo do Operador (execução automática)
- Backend: SQLite kv por escopo, uma conexão real por thread atrás de um wrapper (`server/app/db.py:51` `_ThreadLocalConnection`) — necessário porque o pool de threads do FastAPI/anyio quebra com uma única conexão SQLite compartilhada.
- Front: dois stores completos e paralelos, escolhidos em runtime por `isNative` — `web/src/persistence.js:1171` (`export const store = isNative ? deviceStore() : serverStore();`).
## Key Abstractions
- Purpose: isola dados por conta numa única tabela kv, sem multi-tenância por schema
- Examples: toda função em `store.py`/`db.py` recebe `user_id=None|str`
- Pattern: `None` = "balde anônimo" (pré-login); resolvido por `current_scope()` a partir do Bearer token (`server/app/main.py:94`)
- Purpose: fonte única de frases/vereditos por Modo Estudo vs Modo Operador
- Examples: `server/app/skill_ref.py` (`vocab["educacional"]`, `vocab["operador"]`, `TIMING[modo][estado]`)
- Pattern: o front nunca compõe vocabulário — recebe a frase pronta do backend; espelhado no front em `web/src/copy.js` (`COPY.estudo`/`COPY.operador`)
- Purpose: web usa estado no servidor; iOS é local-first (localStorage)
- Examples: `web/src/persistence.js:97` (`serverStore`), `web/src/persistence.js:214` (`deviceStore`)
- Pattern: cada método (buy/sell/putConfig/...) precisa existir nos DOIS, com o mesmo contrato — paridade testada em `web/tests/test_api_parity.mjs`; `deviceStore` reimplementa em JS a mesma aritmética de `store.py` (comentários "espelho de store.py")
- Purpose: permissão nomeada por função de produto, não lista solta de flags técnicas
- Examples: `server/app/rbac.py` (`GRUPOS`, `ROLE_ADMIN`, `require_permission()`)
- Pattern: composição via `Depends()` no FastAPI — nunca esconder só no botão da UI; bootstrap aditivo garante que quem já era admin binário (`_is_obs_admin`) nunca perde acesso
- Purpose: toda afirmação de timing carrega o carimbo da barra e a ressalva de atraso
- Examples: `server/app/timing.py`, `server/app/timing_watch.py`, `server/app/radar_daily.py`
- Pattern: plano diário do Radar × barra de 15min FECHADA × timing determinístico (`armado/gatilho/esticado`)
## Entry Points
- Location: `server/app/main.py` (`app = FastAPI(...)`, linha 43)
- Triggers: uvicorn (Railway, `server/railway.json` / `server/Procfile`)
- Responsibilities: todas as rotas `/api/*`, monta `/admin` (admin_dist), `/ios` (ios_dist), `/` (web_dist, catch-all — DEVE ser o último `app.mount()`)
- Location: `server/app/agent.py:874` (`scheduler_loop`)
- Triggers: iniciado junto com o processo do servidor (sem cron externo); também disparável sob demanda via `POST /api/agent/run-now` (`main.py:2190`) ou imediatamente após buy/sell/stop-alvo (`_disparar_ciclo_imediato`)
- Responsibilities: radar diário, passada intraday, trailing stop, alvo dinâmico, avisos de gatilho/push
- Location: `web/src/main.jsx` → `web/src/App.jsx`
- Triggers: carregado como PWA (`server/web_dist`, mesma origem do backend) ou dentro do shell Capacitor no iPhone (bundle embutido no binário, sem `server.url`)
- Responsibilities: toda a UI, Modo Estudo × Modo Operador
- Location: `web-admin/src/main.jsx` → `web-admin/src/App.jsx`
- Triggers: navegação direta em `/admin/*` (desktop) ou abertura in-app via browser embutido no iOS (handoff de sessão, ADR-014)
- Responsibilities: as 10 abas de observabilidade/governança, todas RBAC-gated no backend
## Architectural Constraints
- **Threading:** FastAPI/uvicorn com pool de threads (anyio); SQLite exige
- **Global state:** kill-switch do agente e orçamento da brapi seguem o
- **Ordem de `app.mount()` importa:** `/ios` e `/admin` precisam ser
- **Deploy só enxerga `server/`:** o `rootDirectory` do Railway é `/server`
- **App nativo carrega bundle local, sem `server.url`:** `web/capacitor.config.ts`
- **Paridade obrigatória entre pares de arquivo:** `server/app/defaults.py`
## Anti-Patterns
### Confiar na LLM para números de carteira/decisão
### Esconder admin só no front
### Adicionar campo em store novo sem espelhar no outro
## Error Handling
- Fonte de mercado indisponível: rota levanta `HTTPException(502, "Sem
- Rotas admin: `require_permission(perm)` levanta 403 com a permissão
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

| Skill | Description | Path |
|-------|-------------|------|
| didatica-boris | Regras da camada de entendimento do Boris+ — vocabulário por modo, princípios de dado, guardiões e caminho de deploy. Use ao escrever ou revisar texto didático, explicação de conceito no card, ou qualquer resposta do assistente de IA que leia dados da tela. | `.claude/skills/didatica-boris/SKILL.md` |
| swiftui-pro | Comprehensively reviews SwiftUI code for best practices on modern APIs, maintainability, and performance. Use when reading, writing, or reviewing SwiftUI projects. | `.agents/skills/swiftui-pro/SKILL.md` |
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
