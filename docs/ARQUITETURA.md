# Arquitetura técnica do Boris+

> Última revisão: 2026-08-06 (build F10-20260806-01). Este documento é a
> visão de conjunto; a decisão detalhada mora em cada ADR (`docs/adr/`) e o
> porquê de cada regra mora no código, em comentário. Quando este texto e um
> ADR divergirem, o ADR vence — e este arquivo ganha uma correção.

## Em uma frase

Um monólito FastAPI no Railway que serve API e front web da mesma origem,
com o mesmo front React empacotado num shell Capacitor para o iPhone — e uma
divisão rígida de trabalho: **o backend calcula, a LLM interpreta, a pessoa
decide** (Princípio 1, `server/app/skill_ref.py`).

## Topologia

```
┌─ iPhone (Capacitor/WKWebView) ─┐      ┌─ Navegador (PWA) ─┐
│  bundle React DENTRO do app    │      │  server/web_dist   │
│  deviceStore (local-first)     │      │  serverStore       │
└──────────────┬─────────────────┘      └─────────┬──────────┘
               │  /api/* (CapacitorHttp)          │  mesma origem
               ▼                                  ▼
┌──────────────────── Railway · rootDirectory=/server ────────────────┐
│  FastAPI (app/main.py) + uvicorn · SQLite (data/, kv por escopo)    │
│                                                                     │
│  MOTOR DETERMINÍSTICO            CAMADA LLM (opt-in, medida)        │
│  scanner/radar_daily (1x/dia)    llm.py (Anthropic; BYOK ou         │
│  intraday (passada 15m)          gerenciada B3_MANAGED_LLM_*)       │
│  timing/timing_watch (gatilho)   analysis N2, scan_deep,            │
│  setups/indicators/kpi           assistente (teto R$/dia)           │
│  conceitos + pet (didática)      ai_activity (ledger de custo)      │
│                                                                     │
│  skill_ref.py = vocabulário canônico por modo (Estudo × Operador)   │
│  push.py (APNs) · auth.py/siwa.py (Apple/Google/e-mail)             │
└──────────┬──────────────────────────────────────────────────────────┘
           ▼
  Yahoo/brapi (candles+cotações, ~15 min de atraso) · B3 arquivos (opções, v2)
```

Domínio: `acamerini.app` (custom domain do Railway; cadastro obrigatório só
nesse domínio). O serviço Railway enxerga **apenas** `server/` — por isso o
front de produção mora versionado em `server/web_dist`, publicado por
`scripts/publicar-web.sh` (nunca por CI automático; decisão deliberada).

## Front (`web/`)

- **React + Vite, concentrado em `web/src/App.jsx`** — um arquivo grande de
  propósito: o custo de navegar módulos superava o de rolar um arquivo, e os
  guardiões `.mjs` fazem asserções de contrato por regex sobre esse fonte.
- **Dois stores, paridade obrigatória** (`web/src/persistence.js`):
  `serverStore` (web; estado no servidor por escopo) e `deviceStore` (iOS;
  localStorage local-first — `putConfig` NUNCA chama a API, e por isso o
  consentimento de push viaja pelo registro do token, não pela config).
  Método ou campo novo entra **nos dois**; `test_api_parity.mjs` cobre parte.
- **Dois modos** com vocabulário próprio servido pronto pelo backend:
  **Estudo** (descreve condição; vereditos `Estudar alta/baixa, Monitorar,
  Aguardar, Não operar`) e **Operador** (fala como mesa: `COMPRAR, VENDER,
  AGUARDAR CONFIRMAÇÃO, NÃO OPERAR`; exige termo aceito). O front nunca
  compõe vocabulário — recebe a frase pronta.
- **iOS**: shell Capacitor (`web/capacitor.config.ts`, `webDir: "dist"`, sem
  `server.url` — o bundle vai dentro do binário). `CapacitorHttp` faz o fetch
  nativo (ignora CORS). Consequência operacional: **texto do backend muda com
  deploy; JavaScript no iPhone só muda com `bash instalar.sh --iphone`**.

## Backend (`server/app/`)

- **FastAPI monolítico** (`main.py`), SQLite chave-valor por escopo
  (`db.py`/`store.py`; `user_id=None` é o balde anônimo — motivo de o
  assistente LLM exigir conta). Deploy: uvicorn direto (`railway.json`).
- **Agente** (`agent.py`): laço interno do servidor que dispara o radar
  diário (`radar_daily.maybe_run`) e a passada intraday — sem cron externo.
- **Tríade temporal** (ADR-002): plano diário do Radar × barra de 15 min
  FECHADA × timing determinístico (`timing.py`: `armado/gatilho/esticado`,
  zona de perseguição 0,5R). Toda afirmação de timing carrega o carimbo da
  barra e a ressalva do atraso (~15 min medidos, ADR-001).
- **Fonte de dados**: Yahoo/brapi via provedor único (`candle_provider.py` +
  `candle_cache.py`). Dado publicado pelo mercado pertence ao MyData
  (`~/dev/cvm-financas/docs/fundacao-de-dados.md`); a ingestão local existente
  é transitória.
- **LLM** (`llm.py`): Anthropic; chave do usuário (BYOK, sem freio) ou
  gerenciada (`B3_MANAGED_LLM_*`, sob cota). Todo gasto entra no ledger
  `ai_activity.py` (painel de IA). Não mexer em `llm._CHARS_POR_TOKEN` — é
  global e calibrado.
- **Push** (`push.py` + APNs): consentimento/modo/universo vivem no SERVIDOR
  (`kv:pushPrefs`), alimentados pelo registro do token — porque a config do
  iPhone é local e invisível para a API. Aviso de gatilho: opt-in, silencioso
  (priority 5), teto 6/dia + 1 por ativo/dia.

## Camada de entendimento (ADRs 006/007)

Três degraus, do grátis ao pago — o grátis sempre responde primeiro:

1. **Conceitos determinísticos** (`conceitos.py`): catálogo de 7 conceitos
   ancorados nos números do card (campo ausente derruba o parágrafo — nunca
   estima). Afordância: **sublinhado pontilhado + toque** (padrão Duolingo;
   o toque longo foi testado e descartado — sem indicação, a seleção de
   texto do sistema respondia). O front declara regiões (`SetorAlvo`); o que
   cada uma explica vem do registro `conceitos.SETORES`, servido em
   `GET /api/conceitos` — repontear setor é deploy, não build.
2. **Pet** (coruja): mascote do assistente na Watchlist do Estudo. Resumo
   determinístico de `GET /api/pet/resumo` (frases canônicas de
   `timing.montar` + conectivas na rota), voz de saída por `speechSynthesis`
   pt-BR (no WKWebView é o AVSpeechSynthesizer do iOS). Nunca abre sozinho.
3. **Assistente LLM** (`assistente.py`): pergunta livre sobre a tela. Recebe
   SNAPSHOT estruturado (nunca raspa DOM; conteúdo de tela é dado, não
   instrução), prefixo cache-aware, exige conta, teto próprio de gasto/dia
   (`kv:assistenteGasto`, `B3_ASSISTENTE_TETO_BRL`). `tela:` é allowlist
   (`SETORES`/`PET_TELAS`) — id desconhecido é 400, nunca prompt.

Isolamento estrutural: `/api/timing` não ganhou campo nenhum com a didática —
rota nova não muda rota velha, e o payload do Operador é idêntico por
construção, não por promessa testada.

## Operação

- **Chaves de desligamento** (env no Railway, sem build): `B3_DIDATICA_OFF`,
  `B3_ASSISTENTE_OFF`, `B3_TIMING_PUSH_KILL`, `B3_ASSISTENTE_TETO_BRL`.
- **Guardiões**: ~600 testes pytest (`server/tests/`) + suítes `.mjs`
  (`web/tests/`, contratos por regex de fonte, rodam sem build). Regra da
  casa: mudança de comportamento vem com guardião que a trava.
- **Entrega**: `entregar.sh "msg"` faz a cadeia inteira em um comando —
  suítes → sync do `SERVER_BUILD_ID` → **build + publicação em
  `server/web_dist`** → commit+push (Railway redeploya backend E web) →
  `cap sync ios` → verificação do `BUILD_ID` em cada elo → Xcode. A ordem
  build→commit é obrigatória: publicar depois do push deixava a web de
  produção uma entrega atrás, com `/api/health` dizendo que estava tudo certo
  (corrigido em 2026-08-06). Carimbo: `web/src/version.js` (`F10-AAAAMMDD-NN`,
  data real); a prova de deploy é sempre `/api/health`.
- **Testes massivos**: `scripts/masstest-agentes.py` (determinístico, grátis)
  e variantes LLM (BYOK, pagas).

## Fronteiras e pendências conhecidas

- **MyData**: integração pendente (`MYDATA_API_KEY`/`MYDATA_BASE_URL`);
  decisão legal sobre exibir dado da B3 em aberto.
- **Opções v2** (ADRs 003/004/005): backend + UI prontos; sem fonte de
  prêmios da B3 — a camada não aparece em card nenhum até haver cadeia real.
- **`greek_score`** morto no código, aguardando decisão.
- **Voz do pet**: medida no navegador; pendente de medição no WKWebView real.
- Backtest F2/F3 e recalibragem de liquidity/educational score no backlog.

## Como manter este documento

Ele é um mapa, não um espelho: registre aqui **estrutura e fronteira**, não
detalhe de implementação (que envelhece). Gatilhos de revisão: ADR novo,
subsistema novo, mudança de topologia de deploy, ou um "isso aqui mentiu para
mim" — corrija na hora e carimbe a data no topo.
