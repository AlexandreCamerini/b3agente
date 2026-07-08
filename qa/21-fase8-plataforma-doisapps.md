# QA 21 — FASE 8: bugs finais de plataforma + gate "Dois apps em um"
*08/07/2026 · baseline verde antes de mexer (18 backend + 18 web)*

## A1 — Notificações locais no iPhone (SOLUÇÃO FINAL)

- **Hipótese investigada e REFUTADA com evidência:** o suposto conflito de
  delegate entre os plugins não existe — no fonte instalado
  (`node_modules/@capacitor/ios/Capacitor/NotificationRouter.swift`) o
  Capacitor 8 usa um `NotificationRouter` COMPARTILHADO que roteia willPresent/
  didReceive para cada plugin pelo tipo do trigger. Nenhuma ponte no
  AppDelegate é necessária (implementá-la seria paliativo arriscado).
- **CAUSA-RAIZ REAL (evidência no fonte do plugin):** o
  `LocalNotificationsHandler.willPresent` só reconhece as opções
  `"banner" | "list" | "badge" | "sound"` — a nossa config usava **"alert"**,
  que cai em `Unrecognized presentation option` ⇒ com o app em FOREGROUND a
  notificação chegava SEM apresentação visual (só som/badge). Assimetria do
  upstream: o handler do PUSH mapeia "alert"→banner+list; o LOCAL não.
- **Correção:** `capacitor.config.ts` → `presentationOptions: ["banner",
  "list", "sound", "badge"]` nos DOIS plugins. Com a permissão do sistema
  concedida (fluxo Abrir Ajustes da FASE 6/8), o quadro completo fica:
  foreground = banner nativo; background/fechado = entrega pelo sistema.
  **Exige `cap sync` + rebuild no Xcode.**
- **Guardião:** `test_push_wiring.mjs` agora proíbe "alert" no
  LocalNotifications e exige banner+list explícitos.

## A2 — Login Apple: "audience doesn't match"

- **Causa:** o servidor valida o `aud` do id_token contra `APPLE_CLIENT_ID`;
  no login NATIVO o `aud` é o **bundle id** (`com.alexandrecamerini.bolsia`).
  A env estava ausente/derivada de outro valor (ex.: Services ID).
- **Correções de código (à prova de futuro):** `APPLE_CLIENT_ID` e
  `GOOGLE_CLIENT_ID` aceitam **lista separada por vírgula** (bundle id +
  Services ID do web); mensagem de erro acionável mostra o `aud` RECEBIDO ×
  esperados e a env exata a corrigir (`_peek_aud` lê o claim sem validar —
  nunca autentica); a mensagem de env ausente já ensina o valor certo.
- **Ação sua (Railway):** `APPLE_CLIENT_ID=com.alexandrecamerini.bolsia`.
- **Testes:** `test_aud_em_lista_e_peek`, `test_oauth_sem_env_menciona_bundle_id_e_lista`.

## A3 — Logout não sai da conta

- **Causa-raiz (dupla, e simétrica no login):** (a) o logout limpava
  token/cache/namespace, mas os estados DERIVADOS em memória (analysis,
  expanded, quotes, wlScan, destaque, notifRef) continuavam com os dados da
  conta — e o merge `{...seed, ...cur}` do loadState preservava o antigo;
  (b) nada levava de volta ao portão de entrada — visualmente "não saiu".
- **Correção:** `_resetScopeState()` (fonte única) roda em TODA troca de
  escopo — logout, exclusão de conta E login/register/oauth; logout/exclusão
  também recarregam o escopo anônimo, atualizam cotações, voltam à aba
  inicial e REABREM o welcome. `persistence.auth.logout` já estava correto
  (token+cache+outbox+namespace) e segue guardado.
- **Guardião:** `test_logout_reset.mjs` (20 asserções).

## PARTE B — gate "Dois apps em um" (aguardando seu OK)

- **`web/src/copy.js` (amostra, ainda não importada):** dicionário COPY com 20
  chaves espelhadas por modo — saudação/tratamento, títulos e subtítulos,
  botões (Simular compra × Registrar entrada), empty states, toasts,
  notificações e rodapés. Professor × mesa de operações; validado em Node
  (chaves idênticas + vocabulário de ordem proibido no ramo estudo).
- **`qa/mocks/dois-apps-em-um.html`:** a MESMA tela nos dois temas, lado a
  lado — Estudo intocado (âmbar) × Operador (verde-mercado #22c55e sobre
  grafite frio, chip MODO OPERADOR, capital/risco no topbar, números mono).
  5 decisões de design listadas no rodapé do mock para você bater o martelo.
- Após o OK: B1 (migração das telas para copy.js + guardião de fraseologia) e
  B2 (tokens de tema por modo + transição) → hard stop → B3 (prompts PRO por
  modo) + B4 (tratamento/notificações por modo) → hard stop.

## Evidência de testes
- Backend: 18 suítes offline verdes (auth +2 testes) · py_compile OK.
- Web: 19/19 suítes (nova: test_logout_reset; test_push_wiring +2) · JSX OK ·
  copy.js validado em Node.
- Pendente no seu ambiente: pytest completo, `cd web && npx cap sync ios` +
  rebuild (A1), env `APPLE_CLIENT_ID` no Railway (A2), hard stop no aparelho.
