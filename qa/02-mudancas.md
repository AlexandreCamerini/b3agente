# 02 — Mudanças (refatoração)

Mudanças cirúrgicas, na ordem de risco. `persistence.js` foi **estendido** (não
reescrito); toda persistência nova passou pelos **dois** stores.

## Fase 1 — Análise do ativo individual volta a ser só texto
- **App.jsx · `AnalysisView`**: removido o bloco de stop/alvo (`STOP/ALVO
  SUGERIDO`). Mantidos texto (Markdown) + FATOS RELEVANTES + nota da IA.
- **Por quê**: o fluxo do ativo não deve disparar stop/alvo. A lógica
  (`localProposal`, campo `proposal`) foi preservada para a Carteira.

## Fase 2 — Config de LLMs e Prompts
- **catalog.js**: `defaultLlmPrompts()` (coleção indexada por chave) + entrada no
  `defaultState`.
- **persistence.js**: `serverStore.putLlmPrompts` (→ API) e `deviceStore`
  (backfill em `ensure()`, exposição em `pub()`, método `putLlmPrompts`).
- **api.js**: `putLlmPrompts` → `PUT /api/llm-prompts`.
- **server**: `defaults.default_llm_prompts()`, `store.set_llm_prompts` +
  `"llmPrompts"` em `SECTIONS`/`public_state` + backfill idempotente; endpoint
  `PUT /api/llm-prompts`.
- **App.jsx**: seção "Config de LLMs e Prompts" (`PromptsSection`) com editor por
  prompt, **Salvar** e **Restaurar default**; ações `editPrompt/savePrompt/
  restorePrompt`.

## Fase 3 — Stop/alvo INDIVIDUAL por card da Carteira (revisado)
- **App.jsx**: ícone "Sugerir stop e alvo (IA)" **em cada card** →
  `StopAlvoModal` **individual** (um ativo). Decisão de **Aplicar em <ativo>** ou
  **Fechar** encerra o popup. Removido o fluxo em lote anterior.
- **server/llm.py**: `analyze_carteira()` usa o prompt configurável
  (`prompts.carteiraStopAlvo`) + BYOK e **`parse_carteira()`** lê a saída em
  **array por ativo** (`{ativo,stop,alvo,explicacao,operar}`); `operar:false` →
  stop/alvo nulos. Fallback para o formato antigo (objeto único) por robustez.
- **server/main.py**: endpoint dedicado `POST /api/carteira-stopalvo/{ticker}`
  (não persiste; transitório p/ o popup).
- **api.js**: `carteiraStopAlvo`. **persistence.js**: `analyzeStopAlvo` nos dois
  stores (device envia config/profile/account no corpo → BYOK no nativo).
- **Prompt default** atualizado para o texto fornecido (análise individual,
  saída em array).
- **Bug "mesmo texto em todas"**: causa era a explicação caindo num fallback que
  dependia só do perfil (igual p/ todos) somada ao conflito de formato. Resolvido
  com caminho dedicado + parser de array (explicação por ativo).

## Fase 4 — Notificações nativas (lacunas)
- **notify.js**: `schedule(title,body,at,id)`, `cancel(id)`, `cancelAll()`
  (nativo via plugin; fallback web via `setTimeout`/timers); `diag()` e logs
  `[b3:notify]` (gated em `b3-debug`) para diagnóstico do import do plugin.
- **App.jsx · NotifSection**: botão "Testar agendada (10s)".
- A migração para o plugin nativo + `requestPermissions` + fallback web **já
  existia**; o gap real era `schedule/cancel` e o ambiente (install + cap add ios).

## Observações de não-regressão
- Análise do Mercado (objeto único, `parse_rich`/`FORMAT`) **inalterada**.
- Dois stores com a mesma interface preservados; nada de unificação/migração.

## Módulo de Opções — MVP1/MVP2 técnico

### Backend
- Criado `server/app/options_quant.py`: funções puras para Black-Scholes, gregos, volatilidade histórica, breakeven, valor intrínseco, score de liquidez e score educacional. Decisão: manter stdlib-only para não aumentar risco de deploy no Railway.
- Criado `server/app/options_provider_yahoo.py`: provider plugável Yahoo Finance para vencimentos e cadeia de opções. Decisão: tratar ausência de dados como warning, não como dado inventado.
- Criado `server/app/options_api.py`: endpoints `/api/options/expirations/{ticker}`, `/api/options/chain/{ticker}` e `/api/options/analyze`.
- Alterado `server/app/main.py`: inclusão do router de opções.

### Frontend
- Alterado `web/src/api.js`: adicionados métodos `optionsExpirations`, `optionsChain` e `analyzeOption`.
- Alterado `web/src/persistence.js`: estendida a interface das duas stores com os métodos de opções, preservando a arquitetura web/iPhone.
- Alterado `web/src/App.jsx`: nova aba “Opções”, tela `OptionsScreen`, tabela calls/puts, leitura de volatilidade/gregos/liquidez e análise educacional do contrato selecionado.

### Testes
- Criado `server/tests/test_options_quant.py`: cobre Black-Scholes, breakeven, volatilidade histórica e score de liquidez.

### Guardrails preservados
- A tela e a análise reforçam que opções são estudo educacional, dinheiro fictício e não recomendação.
- O score é descrito como educacional, sem ordem de compra/venda.
- Dados ausentes do Yahoo são exibidos como indisponibilidade, sem inferência artificial.

## Refatoração mobile-first de análise técnica por modelo

- `server/app/technical_models.py`: novo motor determinístico de contexto técnico. Consolida até 120 candles diários, tendência, momentum, volume, volatilidade, suportes/resistências, plano de risco por ATR e status de opções do yfinance.
- `server/app/main.py`: novos endpoints `GET /api/technical/models` e `POST /api/technical/analyze/{ticker}`. A análise estruturada passa a receber `model` e envia para a LLM apenas dados calculados e candles compactados.
- `server/app/llm.py`: novo prompt de super operador educacional. A LLM interpreta, mas não calcula; saída continua JSON, agora com `recomendacao` tratada como plano educacional, sem ordens de compra/venda.
- `server/app/kpi.py`: compatibilidade com respostas antigas, mas normalização para rótulos educacionais (`Estudar alta`, `Estudar baixa`, `Aguardar`, `Não operar`, etc.).
- `web/src/App.jsx`: seletor horizontal mobile-first de modelos técnicos na tela Mercado; cada card mostra modelo usado e quantidade de candles enviados para a LLM.
- `web/src/api.js` e `web/src/persistence.js`: chamadas novas para análise técnica estruturada preservando web/iOS e BYOK no handset.
- `server/tests/test_technical_models.py`: testes do motor de contexto técnico e compactação.

Validação: backend `45 passed`; frontend `npm run build` OK; teste de paridade HTTP do WebView OK.
