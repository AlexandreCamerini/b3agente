# Technology Stack

**Analysis Date:** 2026-08-18

## Languages

**Primary:**
- Python 3.14 — backend (`server/app/*.py`), FastAPI app, stdlib-first (SQLite via `sqlite3`, PBKDF2 via `hashlib`)
- JavaScript (ES modules, JSX) — web/PWA/iOS client (`web/src/*.js`, `web/src/*.jsx`) and admin portal (`web-admin/src/`)

**Secondary:**
- TypeScript — only `web/capacitor.config.ts` (Capacitor native shell config); root `package.json` pulls in `typescript@^6.0.3` as a devDependency but there is no `tsconfig.json` / typed app code
- Shell (bash) — all operational tooling: `scripts/*.sh`, root-level `*.sh` (deploy, test, audit, release orchestration)

## Runtime

**Backend environment:**
- Python 3.14 (local `.venv` observed at `server/.venv`); no `runtime.txt`/`.python-version` pin found — Railway (Nixpacks) picks its own default unless overridden
- ASGI server: `uvicorn[standard]>=0.29` (`server/requirements.txt`), started as `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (`server/Procfile`, `server/railway.json`)

**Frontend environment:**
- Node.js (version not pinned via `.nvmrc`/`engines`) — Vite 6 build for both `web/` (consumer PWA + Capacitor iOS shell) and `web-admin/` (observability/admin portal)
- Native shell: Capacitor 8 wraps `web/dist` for iOS (`web/capacitor.config.ts`, `appId: com.alexandrecamerini.bolsia`)

**Package Manager:**
- Python: pip, split manifests `server/requirements.txt` (dev/test superset) and `server/requirements-prod.txt` (prod-only, no lockfile/hashes)
- JS: npm — `package-lock.json` present at repo root; `web/` and `web-admin/` are independent npm projects without workspaces (no root lockfile covering their deps was found aggregated — each has its own `package.json`)

## Frameworks

**Core (backend):**
- FastAPI `>=0.110` — single ASGI app in `server/app/main.py`; serves JSON API plus mounts static builds (web app, admin portal, iOS dist) from the same process
- `httpx>=0.27` (async) — all outbound HTTP (brapi, Yahoo, BolsAI, Anthropic/OpenAI/Google LLM calls, Apple SIWA/APNs)
- `PyJWT[crypto]>=2.8` + `h2>=4.1` — ID-token verification (Apple/Google OAuth) and ES256 JWT signing (Sign in with Apple client-secret, APNs auth key); HTTP/2 support for APNs

**Core (frontend):**
- React `^18.3.1` (web + web-admin), no framework router/state library — hand-rolled state in `web/src/App.jsx` and `web/src/persistence.js`
- `lightweight-charts ^4.2.0` — candle/price charting
- `@uiw/react-codemirror` + `@codemirror/*` + `@lezer/*` — prompt/markdown editor in the admin portal (byte-exact prompt editing, see `docs/adr` on portal admin)
- `vite-plugin-pwa ^0.21.1` — PWA manifest/service worker generation for `web/`

**Testing:**
- Python: `pytest>=8.0`, tests under `server/tests/` (87 files)
- JS: no framework dependency listed; `web/tests/*.mjs` run as plain Node scripts (invoked via `scripts/executar.sh --testes`, not through Vitest/Jest)

**Build/Dev:**
- Vite `^6.0.0` (`web/vite.config.js`, `web-admin/`) with `@vitejs/plugin-react`
- Capacitor CLI `^8.0.0` (`cap sync`, `cap open ios`) for the native iOS wrapper

## Key Dependencies

**Critical (backend):**
- `fastapi`, `uvicorn[standard]`, `httpx` — HTTP surface and all outbound calls
- `PyJWT[crypto]` — Sign in with Apple / Google ID-token verification, SIWA client-secret JWT, APNs auth JWT
- stdlib `sqlite3` — sole persistence engine (no ORM, no external DB driver)

**Critical (frontend):**
- `@capgo/capacitor-social-login` (`latest`, unpinned) — single plugin bridging both Apple and Google native login (replaced two abandoned community plugins)
- `@capacitor/push-notifications`, `@capacitor/local-notifications` — APNs bridge and local notification presentation
- `@capacitor-community/text-to-speech` — native TTS for the in-app assistant ("Boris" voice), replacing browser `speechSynthesis`
- `@capacitor/browser`, `@capacitor/app-launcher` — in-app browser handoff (used to open the admin portal from the mobile app, ADR-014)

**Infrastructure:**
- No cache/queue service (Redis, etc.) — caching is in-process memory + SQLite `kv` table (`server/app/db.py`, `candle_cache.py`, `brapi_budget.py`)
- No ORM/migration framework — `server/app/db.py` runs hand-written `CREATE TABLE IF NOT EXISTS` / ad hoc migration functions (e.g. `_migrate_identities_from_users`) on every `connect()`

## Configuration

**Environment:**
- All backend config via `os.environ` (no `.env` loader library in requirements — Railway injects env vars directly; local dev presumably exports vars manually or via `scripts/`)
- Prefix convention: `B3_*` for app config/feature flags, `BRAPI_TOKEN`/`BOLSAI_API_KEY` for market-data providers, `APNS_*`/`SIWA_*`/`APPLE_CLIENT_ID`/`GOOGLE_CLIENT_ID` for auth/push, `B3_MANAGED_LLM_*` for the server-funded (non-BYOK) LLM path
- Frontend build-time config via Vite `import.meta.env.VITE_*` (e.g. `VITE_API_BASE`, `VITE_GOOGLE_IOS_CLIENT_ID`, `VITE_GOOGLE_WEB_CLIENT_ID`) — baked into the JS bundle at build time, not runtime-injectable
- Secrets (`BRAPI_TOKEN`, `BOLSAI_API_KEY`, `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`/`GEMINI_API_KEY` for managed LLM, `SIWA_PRIVATE_KEY`, `APNS_AUTH_KEY`) live only in server env (Railway), never in the client bundle or git — per repo guardrail in `CLAUDE.md`

**Build:**
- `server/railway.json` — Nixpacks builder, health check `/api/health`, restart-on-failure ×3
- `web/vite.config.js` — dev proxy `/api` → `localhost:8787`; PWA manifest with `navigateFallbackDenylist: [/^\/admin/]` so the service worker doesn't hijack the admin portal route
- `web/capacitor.config.ts` — native iOS build config, `CapacitorHttp: { enabled: true }` to bypass CORS for direct brapi calls from the device

## Platform Requirements

**Development:**
- Python 3.14 venv under `server/.venv`
- Node.js + npm for `web/` and `web-admin/` (separate installs, no workspace root)
- Xcode (for `cap open ios` / TestFlight builds) — see `TESTFLIGHT.md`, `resources/ios/`

**Production:**
- Single Railway service running the FastAPI app (`server/`), which also serves the compiled web app (`server/web_dist`), the admin portal (`server/admin_dist`), and the iOS ancillary files (`server/ios_dist`, e.g. `apple-app-site-association`) as static mounts from the same origin
- SQLite database file on Railway's ephemeral disk (`B3_DB_PATH`, default `server/data/b3_agente.db`) — app is documented as "stateless for the phone" (device is source of truth for most user state; server DB backs multi-user accounts, sessions, admin config, budgets)
- No containerfile/Dockerfile found — deploy relies on Railway's Nixpacks auto-detection of `server/requirements.txt`

---

*Stack analysis: 2026-08-18*
