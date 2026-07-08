# QA 19 — FASE 6: correções finais + proposta Modo Operador
*08/07/2026 · baseline verde antes de mexer (17 suítes backend offline + 17 web)*

## Fix 1 — Servidor não persiste no iOS (bloqueava o login)

- **Causa-raiz (dupla):** (a) sem `VITE_API_BASE` no build, o app nativo nascia
  SEM endereço — nada funcionava até digitar o servidor; (b) `serverUrl` vivia
  DENTRO do doc escopado por usuário — trocar de escopo (login/logout) "perdia"
  o valor e obrigava a recadastrar.
- **Correção:** `PROD_BASE` (URL do Railway) embutida no `api.js` — em modo
  nativo, base vazia = produção (o app funciona de fábrica; login idem);
  `setNativeMode` aplica o padrão já no boot. `serverUrl` virou chave GLOBAL do
  aparelho (`b3-server-url-v1`), lida no `ensure()` de qualquer escopo e
  espelhada no `putConfig`. UI da Config renomeada para "override de
  desenvolvimento" + linha "em uso agora: <base efetiva>".
- **Guardiões:** `test_api_base.mjs` (novo, 9 asserções executáveis) +
  `test_api_parity.mjs` atualizado (contrato antigo de "falhar cedo" foi
  substituído de propósito pelo padrão de produção).

## Fix 2 — "Aprofundar com IA" mal formatado

- **Causa-raiz:** quando o JSON obrigatório do N1 vinha inválido (truncamento
  em 1600 tokens era o gatilho típico), `analyze_deep` devolvia o BLOB CRU em
  `resumo` — o modal renderizava chaves/aspas/JSON pela metade. Além disso o
  resumo usava só `MdInline` (colapsava quebras de linha).
- **Correção:** `llm._deep_fallback()` — salva o campo `"resumo"` do JSON
  parcial; sem ele, remove a sintaxe JSON e devolve frases legíveis; marca
  `parseFalhou: true`. Teto de tokens 1600 → 2200. No modal: resumo em BLOCO
  (`<Markdown/>`) + aviso "leitura veio incompleta — rode de novo" quando
  `parseFalhou`.
- **Guardiões:** 4 testes novos em `test_llm_errors.py` (que também ganhou o
  mini-runner `__main__` que não tinha) + 2 asserções em
  `test_fase4_radar_deepmodal.mjs`.

## Fix 3 — "Ativar no servidor" (Operador IA) não funcionava

- **Causa-raiz (dupla):** (a) no iPhone, `deviceStore.putAgent` tratava só
  `autonomous/allocPct/intervalMin` — `serverEnabled`, `rules`, `mode`,
  `trailingPct`, `maxOpsDia`, `maxValorOp` eram DESCARTADOS em silêncio (o
  toggle nunca chegava ao backend); (b) `A.putAgent` aplicava o patch OTIMISTA
  e engolia o erro — UI mostrava "ligado" sem o servidor ter ligado.
- **Correção:** deviceStore encaminha os parâmetros de servidor via
  `api.putAgent` (LIVE), exige sessão para `serverEnabled` (mensagem clara) e
  espelha no doc local só o que o servidor CONFIRMOU. `A.putAgent` não é mais
  otimista para `serverEnabled` e PROPAGA o erro — `setServer` mostra o motivo
  exato e reconfirma pelo status.
- **Guardião:** `test_agent_server_toggle.mjs` (novo, 9 asserções).

## Fix 4 — Central única de notificações + "pedir permissão"

- **Causa do "pedir permissão não funciona":** após UMA negativa, o iOS nunca
  re-pergunta — `requestPermissions()` volta "denied" na hora e o botão parece
  morto. Não é bug de código; é UX errada para o estado real do sistema.
- **Correção/unificação:** a seção Notificações da Config virou a CENTRAL
  ÚNICA: estado real da permissão → ações por estado ("Pedir permissão" só em
  `default`; "Abrir Ajustes →" em `denied`, via novo `notify.openSettings()`
  com `@capacitor/app-launcher`, degradando com instrução manual) →
  preferências locais → **PUSH DO SERVIDOR** (ativar aparelho + testar,
  exigindo conta e permissão) → testes/diagnóstico. O botão duplicado do
  Operador IA saiu (virou atalho `A.openNotifCentral()` direto para a Config);
  o teste da Observabilidade permanece (é tela de diagnóstico).
- **Dependência nova:** `@capacitor/app-launcher@^8` (exige `npm install` +
  `cap sync` — já cobertos pelo instalar.sh).
- **Guardião:** `test_notif_central.mjs` (novo, 14 asserções).

## Fix 5 — Push rejeitado: BadEnvironmentKeyInToken

- **Diagnóstico:** esse reason significa que a CHAVE .p8 foi criada no portal
  Apple restrita a um ambiente (Development/Production) diferente do host em
  uso — não é problema do token do aparelho (esse é o `BadDeviceToken`).
- **Correção:** `push.explain_reason()` traduz cada reason do APNs em
  instrução exata em pt-BR (incluindo o caminho no portal: Keys → Environment
  "Sandbox & Production", e a regra do `APNS_SANDBOX`); todo detalhe agora
  inclui `[ambiente: produção|sandbox]`. Descarte de token restrito aos
  reasons de token (`BadDeviceToken`, `Unregistered`, `DeviceTokenNotForTopic`)
  — antes um erro de CHAVE podia mascarar tokens bons.
- **Ação de configuração (sua parte):** no portal Apple, confira a chave APNs;
  se estiver restrita, gere uma sem restrição de ambiente e atualize
  `APNS_AUTH_KEY`/`APNS_KEY_ID` no Railway; builds do Xcode = `APNS_SANDBOX=1`,
  TestFlight/produção = variável removida.
- **Guardião:** `test_push_reasons.py` (novo, 5 testes).

## Item 6 — Modo Operador (GATE: aguardando aprovação)

- `PROPOSTA-MODO-OPERADOR.md` (escopo completo, diferenças por tela,
  arquitetura, fases F7.1–F7.4, limites regulatórios) e
  `qa/mocks/modo-operador.html` (4 telas: seletor+termo, card do Radar com
  decisão/plano/sizing, plano completo com checklist, trades reais +
  assertividade). NENHUM código de produto foi alterado para o item 6.

## Evidência de testes

- Backend: 17 suítes offline OK (novas: `test_push_reasons`; `test_llm_errors`
  roda no pytest do venv — no sandbox aparece "pulada" por falta de httpx, com
  a lógica do fallback validada via stub) · `py_compile` OK.
- Web: 17 suítes OK (novas: `test_api_base`, `test_agent_server_toggle`,
  `test_notif_central`) · parse JSX OK.
- Pendente no seu ambiente: `pytest` completo no venv, `npm install` (nova
  dependência), build Xcode e o hard stop do ATUALIZAR.
