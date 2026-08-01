# Releases — BolsIA

Notas por versão. Carimbo canônico do backend em `/api/health`
(`SERVER_BUILD_ID`); front em `web/src/version.js` (rodapé do Perfil).

---

## Julho/2026 — Fidelidade da análise, agentes verificados e ferramental

Versão de consolidação: a análise técnica e fundamental passou a ter uma fonte
canônica única, o modo Estudo virou didático, e os três agentes (determinístico,
N2, N1) foram testados em massa em produção — cada teste rendeu um bug real
corrigido.

> **Carimbo em produção: `F9-20260728-07`** (`/api/health`). O bump de backend
> `-0730-01` foi sobrescrito quando o `entregar.sh` re-sincronizou o
> `SERVER_BUILD_ID` a partir de `web/src/version.js` (limitação conhecida do
> carimbo — front e back compartilham o número numa entrega de front). Todo o
> código abaixo está no ar; só o número reflete a última entrega de front.

### Análise (backend)
- **Fonte canônica única** (`skill_ref.py`): persona, 11 princípios, processo de
  9 passos, contrato de dados, conclusões e disclaimer da skill `analise-tecnica-b3`.
  As 4 superfícies de persona (N1, N2, defaults educacional/operador) passam a
  **derivar** dela — fim da tríplice divergência. Doutrina fundamental (3 pilares)
  idem, com `fundamentals.py` derivando os thresholds.
- **Estudo assertivo (opção B)**: leitura fecha com veredito canônico + diretriz de
  assertividade, mantendo o vocabulário de estudo (sem verbo de ordem).
- **Estudo didático**: ensina a cadeia **indicador → correlação → decisão** usando
  `families`/`confluenciaEntreFamilias` já calculados. Backend-only (renderiza no
  markdown existente; sem rebuild do app).
- **Lacunas de fidelidade fechadas**: R:R mínimo no N1 operador; contrato de dados
  no N1; geometria incoerente anulada em rec não-direcional (Monitorar/Aguardar).

### Agentes
- **P1**: `plano.decisao` segue o lado dominante da confluência (Princípio 9) —
  fim da contradição veredito↔plano (era ~14% do universo).
- **P2**: heartbeat persistido do agente autônomo — liveness visível fora do pregão
  e sobrevive a deploy.

### Robustez de provedor
- Retry sem `temperature` no Anthropic/Google (modelos novos rejeitam) — casado
  com o catálogo `model_catalog`/`_params_efetivos` do qa/49.
- N1 educacional não trunca mais (`modelosUtilizados` top-4).
- `_CACHE_MIN` cobre `claude-opus-5`/`mythos-5` (512) + guardião de cobertura do
  catálogo.
- Normalização de markdown no `parse_rich` — formatação consistente em qualquer LLM.

### Ferramental (dev/QA)
- `scripts/masstest-agentes.py` (determinístico, grátis) + `masstest-agentes-llm.py`
  (N2, BYOK) + `masstest-agentes-llm-n1.py` (N1) + wrappers à prova de paste.
- TestFlight: `PrivacyInfo.xcprivacy`, `scripts/ios-testflight.sh`,
  `scripts/ios-bump-build.sh`, checklist `TESTFLIGHT.md`.
- `configurar-e-rodar.sh` — do zero ao app rodando em um comando.

### Pendências conhecidas
- TestFlight manual: rename App ID "AppID Prod"→"BolsIA" no portal, criar app no
  App Store Connect, APNs produção coordenado, Archive/upload.
- Revogar a chave de API que apareceu em texto puro durante os testes.

## F10-20260801-01 — F1 (timing de entrada) + pendências da auditoria

**Backend-only** (sem rebuild do front; carimbo bumpado à mão em `main.py`).

- **F1 — timing de entrada** (`server/app/timing.py` + `GET /api/timing/{ticker}`):
  determinístico, O(1) por consulta (lê os armazenados globais Radar diário +
  passada intraday; zero fetch/LLM). Estados: `sem_plano | sem_dado | armado |
  gatilho | esticado` — gatilho é a condição do plano diário verificada na
  barra 15m FECHADA; >0,5R além vira `esticado` (Princípio 8, mesmo
  `ZONA_PERSEGUICAO` do plano). Lacuna severa (cobertura <70%) ⇒ `sem_dado`.
  Vocabulário canônico por modo em `skill_ref.TIMING` (estudo sem verbo de
  ordem; mesa direta), ressalva do atraso (~15 min) sempre presente. O
  veredito 15m viaja como CONTEXTO com aviso de calibragem (ADR-002 D4), nunca
  como gate. **UI fica para o v11 (sessão do AtivoCard).**
- **A6b**: N1 ganha `confianca: "alta"` — gated em código por
  `dataQuality.multiTimeframe`, que agora é REAL: o N1 anexa o bloco
  `intraday15m` da passada fresca (`timing.enriquecer_contexto`, pura, nunca
  muta o cache de snapshot).
- **Migração `llmPrompts`**: default antigo (hash no git) sobe para o novo;
  edição do usuário intocável (`defaults.LEGACY_PROMPT_SHA256`).
- **Configs intraday por env**: `B3_INTRADAY_GAP_S|CONC|PERIOD` com envelope e
  fallback logado; 15m segue canônico (sem variável).
- **A2a**: telemetria `legacyAnalyze` em `/api/obs/usage` para aposentar a
  rota legada com evidência.
- **FinOps/Railway**: corrigida em produção a variável `B3_MANAGED_LLM_KEY `
  (espaço no fim — a IA gerenciada estava silenciosamente DESLIGADA); aviso de
  higiene de env no boot; docs atualizados com o plano pago de US$ 20/mês.
  Falta (Alex): apagar a variável defeituosa no dashboard e definir
  `B3_MANAGED_GLOBAL_DAILY_CAP` antes de abrir a base.
- Suíte: **445 testes** (eram 415) — `test_timing.py` novo, guardiões de
  migração/env/A6b. Masstest determinístico: 32 violações `fund_score_incoerente`
  PRÉ-EXISTENTES (task própria), sem regressão daqui.
