# External Integrations

**Analysis Date:** 2026-08-18

## APIs & External Services

**Market data (quotes & candles):**
- **brapi.dev** — master source for daily candles and spot quotes (ADR-008, `docs/adr/008-fonte-de-cotacoes-selecionavel.md`)
  - Client: `server/app/brapi.py` (httpx, `BASE = "https://brapi.dev/api/quote/"`, `Authorization: Bearer`/token header)
  - Auth: `BRAPI_TOKEN` env var (read in `brapi.py:_token()`)
  - Free-plan constraints hard-coded from live measurement: 1 ticker/request, interval `1d` only, ranges `1d/5d/1mo/3mo`, 15,000 req/month quota — a plan-rejected request still debits quota, so client-side validation (`ForaDoPlano`) happens before any network call
  - Budget/quota governor: `server/app/brapi_budget.py` — daily allotment ≈ 700 req/pregão split into slices (spot 400, delta diário 150, fundamentos 30, reserva ~120), soft-stop at 80%, hard-stop at 100%, counter persisted in SQLite `kv`, active only during B3 trading hours (`server/app/pregao.py` calendar)
  - Provider abstraction: `server/app/candle_provider.py` (`CandleProvider` interface, `BrapiProvider`/`YahooProvider` implementations, `get_history()` router)

- **Yahoo Finance** — backup for daily/spot, and sole source for intraday (brapi free plan has no intraday) (ADR-001, `docs/adr/001-fonte-de-dados-intraday.md`)
  - Client: `server/app/yahoo.py` (httpx, hosts `query1/query2.finance.yahoo.com`, browser User-Agent + cookie/crumb session to mitigate 429s, host rotation, backoff retry)
  - No official API key/contract — unofficial endpoint scraping; ToS forbids commercial use, flagged as an accepted risk in ADR-001/008
  - Also used for options chains: `server/app/options_provider_yahoo.py`

- **BolsAI (usebolsai.com)** — primary source for pre-computed fundamentals (P/L, P/VP, EV/EBITDA, ROE, ROA, ROIC, margin, net debt/EBITDA, CAGR 5y, LPA/VPA) across ~350 tickers
  - Client: `server/app/fundamentals.py` (`BOLSAI_BASE = "https://api.usebolsai.com/api/v1/fundamentals/"`, header `X-API-Key`)
  - Auth: `BOLSAI_API_KEY` env var
  - Free tier: 200 req/day; TTL cache 7 days in SQLite (fundamentals change quarterly)
  - Fallback: brapi.dev complementary fields (dividend yield; full modules only for PETR4/VALE3/ITUB4/MGLU3) — `fundamentals.py` falls back to brapi automatically if `BOLSAI_API_KEY` is absent or the call fails

**LLM / AI analysis (multi-provider, BYOK-first):**
- **Anthropic Claude** — `server/app/llm.py:_call_anthropic()`, `https://api.anthropic.com/v1/messages`, header `x-api-key` + `anthropic-version: 2023-06-01`
  - Models cataloged in `server/app/model_catalog.py` (`claude-haiku-4-5`, `claude-sonnet-5`, `claude-opus-5`, etc.)
  - Prompt caching: `_system_cacheavel()` wraps the system prompt with `cache_control: {"type": "ephemeral"}` when it exceeds the per-model token minimum (`_CACHE_MIN` table) — optimizes repeated-system-prompt call sequences (e.g. Radar N1 batch scans)
  - Auth key resolution: BYOK (`config.apiKey`, user-supplied) or server env `ANTHROPIC_API_KEY` (both device- and server-scoped, see `resolve_key()`)
- **OpenAI-compatible** — `server/app/llm.py:_call_openai_compatible()`, generic `{base_url}/chat/completions`, also used for any self-hosted/"local" OpenAI-compatible endpoint (`provider: "local"`, requires user-supplied `baseUrl`)
  - Auth: `OPENAI_API_KEY` (managed) or BYOK
- **Google Gemini** — `server/app/llm.py:_call_google()`, `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
  - Auth: `GEMINI_API_KEY` (managed) or BYOK
- **Managed (server-funded) LLM path** — `server/app/managed.py`: server-side key for logged-in users without their own BYOK key, quota-gated
  - Env: `B3_MANAGED_LLM_KEY` (required to enable), `B3_MANAGED_LLM_PROVIDER` (default `openai`), `B3_MANAGED_LLM_MODEL` (default `gpt-4o-mini`), `B3_MANAGED_LLM_BASE_URL`, `B3_MANAGED_DAILY_QUOTA` (default 20), `B3_MANAGED_RATE_PER_MIN` (default 6), `B3_MANAGED_GLOBAL_DAILY_CAP`
  - Runtime override of provider/model/quota/rate via admin config (DB) takes precedence over env, per ADR-013; `apiKey`/`baseUrl` stay env-only (never DB-overridable) as a secret-handling guardrail
- Prompt sources: `server/app/defaults.py` (backend canonical prompts/skill text) mirrored byte-for-byte with `web/src/catalog.js` (client copy) — parity enforced by a repo test (see CLAUDE.md guardrail)

## Data Storage

**Databases:**
- SQLite, single file (`server/app/db.py`), no external DB service
  - Path: `B3_DB_PATH` env override, else `<server>/data/b3_agente.db`
  - WAL journal mode + `busy_timeout=5000`; per-thread connection wrapper (`shared()`) to avoid `SQLite objects created in a thread` errors
  - Schema: hand-written `CREATE TABLE IF NOT EXISTS` + ad hoc migrations run on every `connect()` (e.g. `_migrate_identities_from_users`)
  - Model: key-value sections (config, skill, watchlist, cash, positions, history, agent) as JSON blobs, plus relational tables for `users`, `identities` (multi-provider login), sessions, admin_config, kv
  - Deployed on Railway's ephemeral disk — app is designed to treat the phone/device as source of truth for most state; server DB primarily backs multi-user accounts/sessions/admin config/budgets

**File Storage:**
- Local filesystem only — static builds served directly from disk: `server/web_dist` (consumer PWA), `server/admin_dist` (admin portal), `server/ios_dist` (Apple site association, TestFlight assets)

**Caching:**
- In-process memory (module-level dicts) for hot paths: Yahoo quote cache (`yahoo.py:_quote_cache`), Yahoo session cookie/crumb, LLM usage telemetry (`llm.py:USAGE`), managed-config override cache (`managed.py:_CACHE`), brapi budget counters
- SQLite `kv` table as the durable cache layer (survives restarts/deploys) for candle cache (`candle_cache.py`), brapi budget counters, fundamentals (7-day TTL), admin config

## Authentication & Identity

**Multi-provider identity model** (`server/app/auth.py`, `server/app/db.py`, recent commit "identities: uma conta, vários métodos de login"):
- One `users` row can have multiple `identities` rows (one per login method), keyed by `(provider, provider_sub)`; linking by verified email prevents duplicate/orphan accounts across providers
- **E-mail/senha**: stdlib-only path (no FastAPI/network dependency), PBKDF2-HMAC-SHA256, 240,000 iterations, self-describing hash format `pbkdf2_sha256$iter$salt$hash`; password length capped at 128 chars (DoS guard); session TTL `B3_SESSION_TTL_DAYS` (default 90)
- **Sign in with Apple**: ID-token OIDC verification against Apple JWKS (`_OIDC["apple"]`), `aud` checked against `APPLE_CLIENT_ID` (accepts a list); separate module `server/app/siwa.py` handles the `authorizationCode` → token exchange and account-deletion REVOKE flow required by Apple guideline 5.1.1(v)
  - Env: `SIWA_KEY_ID`, `SIWA_PRIVATE_KEY` (.p8 content), `APNS_TEAM_ID` (reused), `APPLE_CLIENT_ID`
  - Refresh token stored in per-user `kv` (`siwaRefresh`), never logged (BYOK-key-equivalent secrecy)
- **Google login**: ID-token OIDC verification against Google JWKS (`_OIDC["google"]`), `aud` checked against `GOOGLE_CLIENT_ID`
  - Client bridge: `web/src/social.js` via `@capgo/capacitor-social-login`, configured with build-time `VITE_GOOGLE_IOS_CLIENT_ID` / `VITE_GOOGLE_WEB_CLIENT_ID` (public client IDs, no secret in client)
  - Web/PWA path also supported (not just native iOS) — bridge registers if both Google client-ID env vars are present at build time
- Client-side ID-token verification uses `PyJWT[crypto]` fetched lazily (import deferred so its absence never breaks boot or email/password login)

**Admin/RBAC:**
- `server/app/rbac.py` — 7 role groups by macro function (ADR-013), gates portal/admin endpoints
- Admin allowlist: `B3_ADMIN_EMAILS` env var

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry/Bugsnag/etc. found) — errors surfaced via structured JSON error payloads to the client (`_provider_error`, `_cfg_payload` in `llm.py`) and internal audit log

**Logs / Internal telemetry:**
- `server/app/audit.py`, `server/app/obslog.py`, `server/app/analytics.py`, `server/app/kpi.py`, `server/app/ai_activity.py` — custom in-house observability stack (ADR-011/012), persisted in SQLite, surfaced through the admin portal (`web-admin/`)
- LLM token usage telemetry: in-memory counters (`llm.py:USAGE`) plus per-operation `ContextVar` collector (`collect_usage()`/`record_usage()`) for per-call cost attribution (FinOps, qa/42/qa/45)
- `print()` statements used for operational warnings (e.g. LLM fallback-model selection, Anthropic temperature-rejection retries) — no structured logging framework (no `logging`/`structlog` config found)

## CI/CD & Deployment

**Hosting:**
- Railway — single service, root directory `server/`, Nixpacks builder (`server/railway.json`)
- Deploy trigger: `git push` (GitHub-connected) auto-redeploys, or manual `railway up` via CLI (`DEPLOY_RAILWAY.md`)
- Health check: `GET /api/health`, 120s timeout, restart-on-failure ×3
- Custom domain planned/pending: `acamerini.app` (per user memory — DNS pending)

**CI Pipeline:**
- None found (no `.github/workflows/`, no other CI config) — testing and release are operator-run shell scripts: `scripts/executar.sh --testes` (canonical: pytest + `web/tests/*.mjs`), `entregar.sh`, `atualizar.sh`, `scripts/publicar-web.sh`, `scripts/publicar-admin.sh`, `scripts/bump.sh`

**iOS distribution:**
- TestFlight via Xcode (`resources/ios/`, `TESTFLIGHT.md`), `scripts/ios-testflight`, `scripts/ios-bump-build` — not automated CI, manual/local build+upload

## Environment Configuration

**Required env vars (server, Railway):**
- Market data: `BRAPI_TOKEN`, `B3_BRAPI_COTA_MES` (default 15000), `BOLSAI_API_KEY`, `B3_CANDLE_PROVIDER`, `B3_CANDLE_FALLBACK`, `B3_INTRADAY_OFF`, `B3_INTRADAY_PERIOD`, `B3_AGENT_QUOTE_SOURCE`
- LLM (BYOK env option + managed path): `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `B3_AGENTE_API_KEY` (generic/local), `B3_MANAGED_LLM_KEY`, `B3_MANAGED_LLM_PROVIDER`, `B3_MANAGED_LLM_MODEL`, `B3_MANAGED_LLM_BASE_URL`, `B3_MANAGED_DAILY_QUOTA`, `B3_MANAGED_RATE_PER_MIN`, `B3_MANAGED_GLOBAL_DAILY_CAP`
- Auth: `APPLE_CLIENT_ID`, `GOOGLE_CLIENT_ID`, `SIWA_KEY_ID`, `SIWA_PRIVATE_KEY`, `APNS_TEAM_ID`, `B3_SESSION_TTL_DAYS`, `B3_AUTH_RL_MAX`, `B3_AUTH_RL_WINDOW_S`, `B3_ADMIN_EMAILS`
- Push: `APNS_KEY_ID`, `APNS_AUTH_KEY`, `APNS_TOPIC`, `APNS_SANDBOX`, `B3_TIMING_PUSH_KILL`
- Misc feature flags/config: `B3_DB_PATH`, `B3_AGENT_INTERVAL_S`, `B3_AGENT_KILL`, `B3_ANALYTICS_OFF`, `B3_ANALYTICS_QUOTA_DIA`, `B3_ANALYTICS_RATE_MIN`, `B3_ASSISTENTE_OFF`, `B3_ASSISTENTE_TETO_BRL`, `B3_DIDATICA_OFF`, `B3_RADAR_DAILY_OFF`, `B3_RADAR_DAILY_HHMM`, `B3_SCAN_UNIVERSE`, `B3_GATED_HOSTS`, `B3_FERIADOS_EXTRA`, `B3_AFTER_MARKET`, `B3_APPLE_APP_ID`

**Required env vars (web build, Vite build-time):**
- `VITE_API_BASE` (points native/iOS build at the deployed backend), `VITE_GOOGLE_IOS_CLIENT_ID`, `VITE_GOOGLE_WEB_CLIENT_ID`

**Secrets location:**
- Server secrets live only in Railway environment variables — never committed, never shipped in the web/iOS bundle (repo guardrail, `CLAUDE.md`)
- `.env`/`.env.*` files: none observed in the repo tree during this scan (not read, per policy)

## Webhooks & Callbacks

**Incoming:**
- None found — no webhook receiver endpoints (no Stripe/payment webhooks, no third-party callback routes) identified in `server/app/main.py` route wiring

**Outgoing:**
- **APNs (Apple Push Notification service)** — `server/app/push.py`, HTTP/2 (`h2` dependency) to `api.push.apple.com` / `api.sandbox.push.apple.com` (`APNS_SANDBOX=1` for dev/TestFlight-adjacent testing; production APNs used even for TestFlight per `APNS-PUSH.md`)
  - Auth: ES256 JWT (`iss`=`APNS_TEAM_ID`, `kid`=`APNS_KEY_ID`, signed with `APNS_AUTH_KEY`), cached ~45 min
  - Device tokens stored per-user in `kv` (`pushTokens`, cap 5 tokens/user), registered via `POST /api/push/register-token`
  - No-op safe: `is_configured()` gates every send — absent env vars degrade to silent no-op, never a crash
- **Apple Sign-in token/revoke** — `server/app/siwa.py` calls `https://appleid.apple.com/auth/token` (authorizationCode exchange) and `https://appleid.apple.com/auth/revoke` (account-deletion compliance), best-effort/non-blocking

## Billing / Monetization

- **No active payment/billing integration.** `server/app/plan.py` is explicitly a **stub/hook module** ("Ganchos para um futuro modelo FREEMIUM — ESTRUTURA, sem cobrança"): `PLAN_FREE`/`PLAN_PRO` limits are all `None` (unlimited), `requires_subscription()` always returns falsy today
- Documented future path (not implemented): App Store / Google Play IAP subscription, with server-side receipt validation as the eventual gate — explicitly noted as "NUNCA confiar só no cliente" when built
- Client-side mirror: `web/src/plan.js` has the same no-op gate today (`requiresSubscription` hook, currently never triggers)
- Cost containment strategy in lieu of billing: BYOK (bring your own LLM key) shifts inference cost to the user; the managed/server-funded LLM path (`managed.py`) is quota-capped per user and globally to control server-borne LLM spend

---

*Integration audit: 2026-08-18*
