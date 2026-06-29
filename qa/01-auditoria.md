# Auditoria priorizada — ciclo 2026-06-27 (web × iOS)

Auditoria refeita lendo o CÓDIGO ATUAL, não os docs de ciclos anteriores.

## Veredito dos 2 bloqueadores do beta
Ambos são bug de AMBIENTE/configuração, não de lógica — o código que os resolve
já está presente e correto.

- **B1 — Endereçamento do backend (IA stop/alvo no mobile).** api.js exige base
  absoluta no nativo (nativeMode), readBody tolerante (nunca JSON.parse cru),
  detecção de resposta-HTML com erro acionável, testServer em /api/health.
  persistence.js reaplica serverUrl via setApiBase (ensure/putConfig). Falha de
  campo = endereço não configurado/sem protocolo. Coberto por paridade 6/6.
- **B2 — Notificações iOS.** notify.js: plugin nativo via import dinâmico vs
  Notification API; permissão no gesto; toggle reflete permissão real do sistema;
  presentationOptions p/ banner em foreground; stop/alvo/variação pelo efeito de
  cotações, agente pelo cycle. Plugin é dependência declarada. Falha de campo =
  web/ios/ git-ignored, plugin não sincronizado (diag pluginLoaded:false ->
  cap sync + rebuild; denied -> Ajustes).

## Achados (priorizados)
- **CRÍTICO C1** (bug de lógica) — Tela branca por render crash não recuperável:
  App.jsx:2178/2507-2508/2514 desreferenciam watchlist/positions sem guarda +
  ensure() não fazia backfill desses arrays + sem Error Boundary. -> CORRIGIDO
  na Etapa C1 (qa/07).
- **MÉDIO M1** (ambiente) — capacitor.config.ts:21 CapacitorHttp habilitado com
  justificativa obsoleta (nenhum fetch externo direto no front); faz patch do
  fetch nativo e pode não honrar o AbortController -> timeouts (15s/90s) podem
  não abortar no iPhone. Decidir na Etapa 5 (remover vs validar no device).
- **MÉDIO M2** (bloqueador TestFlight) — capacitor.config.ts:6 appId
  com.exemplo.b3agente (placeholder). Trocar p/ id próprio antes do upload.
- **MÉDIO M3** (escopo) — Notificação local é foreground-only (efeito por
  cotações + setInterval pausam em background no iOS). Deixar claro ao tester.
- **BAIXO L1** — App.jsx:2428 efeito de notif re-roda demais (dep [quotes,data]);
  armed-flags em ref, correto, só ineficiente.
- **BAIXO L2** — llm.py:40 public_error devolve str(exc); chave fica no header,
  não vaza; hardening: envolver erro HTTP do provedor em LLMUserError.
- **BAIXO L3** — main.py:462 StaticFiles(html=True) sem fallback SPA; app de tela
  única, sem impacto hoje.

## Plano (ordem de risco, hard stops entre etapas)
C1 (feito) -> Etapa 2 HTTP/M1 -> Etapa 3 notificações no device -> Etapa 4 varredura
iOS/Capacitor + L1/L2/L3 + suíte completa -> Etapa 5 TestFlight + smoke + Railway.

## Validado neste ambiente (sem device, sem rede)
- Paridade HTTP 6/6; node --check limpo; balance App.jsx/main.jsx ok.
- Backend puro (indicators/kpi/tickers) verde.
- NÃO rodou: pytest completo (sem rede p/ instalar FastAPI) — reexecutar local.
