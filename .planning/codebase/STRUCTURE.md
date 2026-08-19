# Codebase Structure

**Analysis Date:** 2026-08-18

## Directory Layout

```
b3-agente/
├── server/                 # Backend FastAPI (Python) — único que o Railway deploya
│   ├── app/                 # Código-fonte da API (motor, LLM, RBAC, dados)
│   ├── tests/                # Suíte pytest (~600 testes)
│   ├── web_dist/             # Bundle publicado do app consumidor (TRACKED, gerado por scripts/publicar-web.sh)
│   ├── admin_dist/           # Bundle publicado do portal admin (TRACKED, gerado por scripts/publicar-admin.sh)
│   ├── ios_dist/              # Distribuição ad-hoc do .ipa (TestFlight/UDID registrado)
│   ├── data/                  # SQLite runtime (b3_agente.db, analytics.db) — não versionar dado real
│   ├── POLITICA-PRIVACIDADE.md # Fonte única da Privacy Policy (servida em /privacidade)
│   ├── railway.json / Procfile # Deploy config (rootDirectory do Railway = /server)
│   └── requirements.txt / requirements-prod.txt
├── web/                     # App consumidor React (PWA web + shell Capacitor iOS)
│   ├── src/                  # Código-fonte (App.jsx é a UI inteira, single-file)
│   ├── tests/                 # Suíte `.mjs` (guardiões de contrato por regex sobre o fonte)
│   ├── public/                 # Ícones/assets estáticos servidos como estão
│   ├── ios/                    # Projeto Xcode gerado (GITIGNORED — recriado por setup-ios.sh)
│   └── capacitor.config.ts     # appId com.alexandrecamerini.bolsia — NÃO mudar
├── web-admin/               # Portal de administração/observabilidade (React, app separado)
│   └── src/                    # App.jsx (10 abas) + EditorTexto.jsx + api.js
├── docs/                    # Documentação técnica viva
│   ├── adr/                    # Architecture Decision Records (001–014)
│   └── ARQUITETURA.md          # Visão de conjunto mantida a mão (ver nota abaixo)
├── qa/                      # Diário cronológico de rodadas de QA/implementação (00–53+)
├── scripts/                 # Automação de dev/build/deploy/teste massivo
├── resources/               # Assets de ícone/splash/privacy manifest do iOS
├── .planning/                # Artefatos do GSD (este mapeamento, planos de fase)
├── .claude/ / .agents/        # Config de agentes/skills do Claude Code
├── CLAUDE.md                 # Contrato de produto + guardrails do repositório
├── executar.sh                # `bash executar.sh --testes` roda AS DUAS suítes (pytest + .mjs)
├── entregar.sh                 # Pipeline de entrega completo (testes → build → publica → commit → cap sync → Xcode)
└── RELEASES.md / ESTADO-*.md / CHECKOUT-*.md # Histórico — NUNCA reescrever o texto da época
```

## Directory Purposes

**`server/app/`:**
- Purpose: toda a lógica de backend — motor determinístico, LLM, RBAC, autenticação, dados de mercado
- Contains: um módulo Python por responsabilidade (sem subpacotes profundos); `main.py` é o único arquivo com rotas HTTP
- Key files: `main.py` (rotas), `store.py` (motor de carteira), `agent.py` (execução automática), `skill_ref.py` (vocabulário por modo), `rbac.py` (ADR-013), `db.py` (persistência kv thread-safe)

**`server/tests/`:**
- Purpose: suíte pytest, um arquivo por feature/ADR/qa
- Naming: `test_<feature>.py`; ADRs específicos viram `test_adr0XX_*.py`
- Key files: `test_adr013_rbac.py`, `test_adr013_cobertura_rotas.py`, `test_multiuser.py`, `test_thread_safety.py`

**`web/src/`:**
- Purpose: código-fonte do app consumidor — um bundle único que roda como PWA e dentro do shell Capacitor
- Contains: `App.jsx` (UI inteira, ~7600 linhas — deliberado, ver nota de convenção abaixo), módulos de estado/lógica pura (`persistence.js`, `finance.js`, `sync.js`, `plan.js`), vocabulário (`copy.js`, `disclaimers.js`, `catalog.js`), integração de API (`api.js`), assistente/mascote (`pet/`)
- Key files: `App.jsx`, `persistence.js` (dois stores), `finance.js` (motor financeiro puro do front), `api.js` (resolução de base URL nativa vs web)

**`web/tests/`:**
- Purpose: guardiões de contrato — muitos são regex sobre o código-fonte (não precisam de build/DOM) para travar comportamento sem exigir Vitest/DOM completo
- Naming: `test_<feature>.mjs`
- Key files: `test_api_parity.mjs` (paridade serverStore/deviceStore), `test_deep_parity.mjs`, `test_wiring_deps.mjs`

**`web-admin/src/`:**
- Purpose: portal de observabilidade/governança — app React separado, deploy independente do app consumidor
- Contains: `App.jsx` (10 abas: Visão Geral, Custos, Comportamento, Eficiência da IA, Automação, LLM, Fontes de dados, Prompts, Usuários e papéis, Auditoria), `EditorTexto.jsx` (editor byte-exato de prompts)
- Key files: `App.jsx`, `api.js` (token próprio `b3-admin-token`, sem suporte a base URL nativa)

**`docs/adr/`:**
- Purpose: registro formal de decisão arquitetural — quando o texto do ARQUITETURA.md e um ADR divergirem, o ADR vence
- Naming: `NNN-titulo-curto.md`, sequencial (001 a 014 nesta data)
- Key files: `013-rbac-papeis-e-entitlements.md` (RBAC), `014-administracao-mobile.md` (handoff admin no app), `002-triade-temporal.md`, `008-fonte-de-cotacoes-selecionavel.md`

**`qa/`:**
- Purpose: diário cronológico de cada rodada de implementação/QA (histórico — nunca reescrever)
- Naming: `NN-titulo.md`, numeração sequencial crescente

**`scripts/`:**
- Purpose: automação de todo o ciclo — dev local, build iOS, deploy, teste massivo
- Naming: `verbo-substantivo.sh` (ex.: `publicar-web.sh`, `ios-bump-build.sh`) ou `substantivo.py` para os harnesses de teste massivo
- Key files: `executar.sh` (suíte canônica de testes), `entregar.sh` (pipeline de entrega completo), `bump.sh` (bump de versão, roda ANTES de publicar), `setup-ios.sh` (bootstrap do projeto Xcode gitignorado)

## Key File Locations

**Entry Points:**
- `server/app/main.py`: instancia o FastAPI app, monta `/admin`, `/ios`, `/` (ordem importa)
- `web/src/main.jsx`: bootstrap React do app consumidor
- `web-admin/src/main.jsx`: bootstrap React do portal admin
- `server/app/agent.py:874` (`scheduler_loop`): laço autônomo do agente, iniciado com o processo do servidor

**Configuration:**
- `server/railway.json` / `server/Procfile`: deploy Railway (rootDirectory=/server)
- `web/capacitor.config.ts`: appId, plugins nativos (push, HTTP nativo) — appId NUNCA muda
- `web/vite.config.js`, `web-admin/vite.config.js`: build do front
- `server/pytest.ini`: config pytest

**Core Logic:**
- `server/app/store.py`: motor de carteira (buy/sell/preço médio/PnL/drawdown)
- `server/app/agent.py`: execução automática, trailing stop, alvo dinâmico, kill-switch
- `web/src/finance.js`: espelho do motor financeiro no front (cálculos puros, sem rede)
- `web/src/persistence.js`: os dois stores (`serverStore`/`deviceStore`) — ponto único de leitura/escrita de estado no front

**Testing:**
- `server/tests/`: pytest do backend
- `web/tests/*.mjs`: guardiões do front (rodam sem build)
- Suíte canônica: `bash scripts/executar.sh --testes` roda as DUAS

## Naming Conventions

**Files:**
- Backend: `snake_case.py`, um módulo por responsabilidade (`brapi_budget.py`, `candle_provider.py`); teste espelha o nome do módulo (`test_brapi_budget.py`)
- Front: `PascalCase.jsx` para componentes isolados (`web/src/pet/Boris.jsx`, `BorisChat.jsx`), `camelCase.js` para módulos de lógica (`finance.js`, `persistence.js`); a maioria da UI vive dentro de `App.jsx` em vez de arquivos separados
- Testes front: `test_<assunto_em_snake_case_pt_br>.mjs` (mistura livremente português e inglês, segue o nome da feature: `test_alvo_dinamico_ui.mjs`, `test_setor_toque.mjs`)
- Scripts: `verbo-substantivo.sh` em português (`instalar.sh`, `atualizar.sh`, `publicar-web.sh`)

**Directories:**
- Nomes de domínio funcional em português quando é conceito de produto (`web-admin`, `web`), inglês quando é convenção de framework (`src`, `tests`, `public`)
- ADRs e QA usam prefixo numérico sequencial (`NNN-` ou `NN-`) para ordem cronológica

## Where to Add New Code

**Nova rota de API:**
- Handler: `server/app/main.py` (perto de rotas relacionadas por prefixo `/api/...`)
- Lógica de negócio: módulo dedicado em `server/app/` (não colocar lógica pesada dentro do handler)
- Teste: `server/tests/test_<feature>.py`
- Se a rota for administrativa: gatear com `Depends(require_permission("grupo.acao"))` e adicionar à allowlist de `server/tests/test_adr013_cobertura_rotas.py`

**Novo campo de carteira/config (afeta os dois clientes):**
- Backend: `server/app/store.py` (schema) + `server/app/defaults.py` (default)
- Front web: `web/src/persistence.js` → `serverStore()`
- Front iOS: `web/src/persistence.js` → `deviceStore()` (replicar a MESMA aritmética)
- Catálogo espelhado: `web/src/catalog.js` se o campo tocar prompts/defaults compartilhados com `server/app/defaults.py`
- Teste: `web/tests/test_api_parity.mjs` cobre parte — revisão manual do par é obrigatória

**Novo texto/vocabulário por modo (Estudo × Operador):**
- Fonte backend: `server/app/skill_ref.py` (`vocab["educacional"]`/`vocab["operador"]`, `TIMING[modo][estado]`)
- Espelho front: `web/src/copy.js` (`COPY.estudo`/`COPY.operador`, chaves idênticas nos dois — guardião compara os conjuntos)
- Nunca hardcodar texto sensível a modo direto num componente — sempre ler de `COPY[modo].chave`

**Novo conceito didático (sublinhado/toque):**
- Catálogo: `server/app/conceitos.py` (`SETORES`) — servido em `GET /api/conceitos`
- Front: declarar a região com `SetorAlvo` em `web/src/App.jsx`, usando `SUBLINHADO` como afordância
- Repontear setor/mudar texto = deploy (Railway); região nova na tela = build (`instalar.sh --iphone`)

**Nova aba do portal admin:**
- Componente: `web-admin/src/App.jsx` (`VIEWS`)
- Rota backend correspondente: gatear com a permissão certa do ADR-013 (`server/app/rbac.py` → `GRUPOS`)
- Mapear no handoff mobile se aplicável: `docs/adr/014-administracao-mobile.md`

**Utilities:**
- Backend: funções puras sem estado ficam no módulo temático mais próximo (ex.: cálculo de indicador em `indicators.py`, não em `main.py`)
- Front: lógica pura sem React fica em módulo `.js` dedicado (`finance.js`, `plan.js`), nunca inline dentro de `App.jsx`

## Special Directories

**`server/web_dist/`, `server/admin_dist/`, `server/ios_dist/`:**
- Purpose: bundles de produção prontos, servidos estaticamente pelo FastAPI
- Generated: sim (Vite build de `web/` e `web-admin/`, ou export do Xcode)
- Committed: sim — TRACKED deliberadamente, porque o Railway só enxerga `server/` (rootDirectory); publicar fora daqui = 404 em produção mesmo com deploy "verde"

**`web/ios/`:**
- Purpose: projeto Xcode nativo gerado pelo Capacitor
- Generated: sim (`scripts/setup-ios.sh` / `npx cap sync ios`)
- Committed: não (gitignored) — recriável a qualquer momento a partir de `web/capacitor.config.ts`

**`server/data/`:**
- Purpose: bancos SQLite runtime (`b3_agente.db` estado da app, `analytics.db` eventos separados)
- Generated: sim (criado em runtime pela primeira conexão)
- Committed: os arquivos existem no worktree local mas não devem carregar dado real de produção versionado

**`qa/`, `RELEASES.md`, `ESTADO-*.md`, `CHECKOUT-*.md`:**
- Purpose: histórico textual de cada rodada — auditoria e continuidade entre sessões de trabalho
- Generated: não (escrito manualmente ao fim de cada entrega)
- Committed: sim — texto da época NUNCA é reescrito; correção de rota vira entrada nova, não edição do passado

**`.planning/`:**
- Purpose: artefatos do fluxo GSD (mapeamento de codebase, planos de fase)
- Generated: sim, por comandos `/gsd:*`
- Committed: depende do fluxo em uso — este diretório é o próprio destino deste mapeamento

---

*Structure analysis: 2026-08-18*
