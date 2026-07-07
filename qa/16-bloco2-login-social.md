# QA 16 — FASE 4 · Bloco 2: login Apple + Google
*07/07/2026 · roteiro de execução em LOGIN-SOCIAL.md*

## O que a Fase 2 já tinha (verificado, intacto)
`/api/auth/oauth` com validação OIDC completa (JWKS, RS256/ES256, audience
por env, issuer, require exp/iss/sub); `upsert_oauth_user` idempotente por
(provider, sub) com tratamento de colisão de e-mail; `_apply_seed` (primeiro
login adota o dado local — invariante da Fase 2); botões Apple/Google na UI
com a Apple em primeiro (diretriz 4.8) e contrato `window.__bolsiaSocial`;
exclusão de conta in-app; `PyJWT[crypto]` já nos requirements.

## O que este bloco adicionou (tudo aditivo)
1. **`web/src/social.js`** — ponte nativa no padrão do notify.js (import
   tardio, guardado; web/PWA sem ponte = aviso amigável). Apple:
   `@capacitor-community/apple-sign-in` (scopes "email name"; devolve
   idToken + name + authorizationCode). Google:
   `@codetrix-studio/capacitor-google-auth` com `serverClientId` = client
   WEB (o `aud` do idToken casa com `GOOGLE_CLIENT_ID` do servidor).
   Config por build: `VITE_GOOGLE_IOS_CLIENT_ID` / `VITE_GOOGLE_WEB_CLIENT_ID`.
2. **`main.jsx`** — registra a ponte só no nativo; falha de import não
   derruba o app.
3. **`App.jsx`** — botões aceitam retorno string OU objeto; `ctx.oauth`
   propaga `name` (a Apple SÓ envia no 1º consentimento) e
   `authorizationCode`.
4. **`server/app/siwa.py`** — client_secret ES256 (chave SIWA própria,
   diferente da do push), troca do code por refresh_token no login (kv
   "siwaRefresh", nunca logado — mesmo tratamento do BYOK) e REVOKE na
   Apple em `DELETE /api/account` (exigência 5.1.1(v)). Tudo best-effort:
   nunca bloqueia login nem exclusão; motivo exato vai ao Diário.
5. **`main.py`** — hint de nome no oauth; exchange no login Apple; revoke
   antes da limpeza no delete (`"siwaRevoke"` no payload).
6. **`setup-ios.sh`** — injeta o URL scheme invertido do Google no
   Info.plist quando `VITE_GOOGLE_IOS_CLIENT_ID` está no ambiente.
7. **`package.json`** — plugins em `latest` (Capacitor 8: majors dos
   plugins não verificáveis offline; lockfile pina na instalação do Alex;
   fallback documentado no roteiro C2).

## Risco conhecido (assumido e documentado)
Versões/API dos dois plugins sob Capacitor 8 não são verificáveis no meu
sandbox sem rede. Mitigação: `latest` + passo C2 do roteiro pede o erro
exato se o npm reclamar; a ponte isola a API dos plugins em um arquivo só.

## Validação no corte
- Backend: **24 suítes ✅** (novo `test_siwa` 4/4: gating de config,
  exchange sem code/config não explode nem grava, revoke sem token é ok,
  wiring do main.py com revoke ANTES da limpeza e refresh_token fora de
  print) + 4 ⏭️ conhecidas do httpx.
- Web: **12/12 ✅** (novo `test_social_login` 14 asserções: contrato da
  ponte, só-nativo, propagação name/code, Apple antes do Google, plugins
  declarados).
- `py_compile` ✅ · `node --check social.js` ✅ · balance App.jsx ✅ ·
  `bash -n setup-ios.sh` ✅.

## Correção pós-hard-stop (07/07): ERESOLVE no npm install
O risco documentado acima se confirmou: `@codetrix-studio/capacitor-google-auth`
(latest = 3.4.0-rc.4) declara peer `@capacitor/core@^6.0.0` — abandonado duas
majors atrás do Capacitor 8 do projeto. Correção: os DOIS plugins foram
substituídos por `@capgo/capacitor-social-login` (mantido ativamente, Apple +
Google em um pacote), a ponte `social.js` foi reescrita com leitura DEFENSIVA
do retorno (`result`|direto, `idToken`|`identityToken`, `authorizationCode`|
`serverAuthCode`, profile aninhado) para tolerar variações de versão, e o
`test_social_login.mjs` agora FALHA se os plugins abandonados voltarem ao
package.json. Contrato da ponte e todo o resto da cadeia (App.jsx, main.py,
siwa.py, setup-ios.sh) permanecem intocados. `--legacy-peer-deps` foi
deliberadamente descartado: forçaria pod nativo de Cap 6 na bridge do Cap 8.
