# LOGIN-SOCIAL.md — Roteiro guiado: Sign in with Apple + Google
*FASE 4 · Bloco 2 · BolsIA (`com.alexandrecamerini.bolsia`)*

O código já está pronto neste zip (ponte nativa `web/src/social.js`, endpoint
`/api/auth/oauth` com hint de nome, revoke SIWA na exclusão de conta, plugins
no `package.json`, URL scheme automático no `setup-ios.sh`). Este roteiro é a
parte que SÓ VOCÊ pode fazer: portais, chaves e variáveis. Formato de cada
passo: **onde clico → o que preencho → o que copio → onde colo**.

Legenda: 🔑 = feito UMA vez (portais) · 🔁 = repete a cada build.

---

## PARTE A — Portal Apple (🔑 uma vez, ~10 min)

**A1. Capability no App ID** *(se você seguiu a migração de identidade, já
está feito — só confira)*
- developer.apple.com → Certificates, Identifiers & Profiles → Identifiers →
  clique em `com.alexandrecamerini.bolsia` → confira ✅ **Sign in with
  Apple** e ✅ **Push Notifications** → Save.

**A2. Chave "Sign in with Apple" (para o REVOKE na exclusão de conta)**
- Mesma área → **Keys** → **+** → Key Name: `BolsIA SIWA` → marcar **Sign in
  with Apple** → ao lado, **Configure** → Primary App ID:
  `com.alexandrecamerini.bolsia` → Save → Continue → Register → **Download**
  (⚠️ baixa UMA vez — guarde fora do git, junto do .p8 do push).
- **Copie o Key ID** que aparece na tela (10 caracteres).
- ⚠️ É uma chave DIFERENTE da do push (`22Y76F52NJ`) — a do push é "APNs", esta
  é "Sign in with Apple". Não misture os arquivos.

**A3. Railway → Variables** *(cole os valores do A2)*
```
APPLE_CLIENT_ID  = com.alexandrecamerini.bolsia
SIWA_KEY_ID      = <Key ID copiado no A2>
SIWA_PRIVATE_KEY = <conteúdo INTEIRO do AuthKey_XXXX.p8 do A2, com as linhas BEGIN/END>
```
(`APNS_TEAM_ID` já existe e é reaproveitado.)

---

## PARTE B — Google Cloud Console (🔑 uma vez, ~15 min)

**B1. Projeto**
- console.cloud.google.com → seletor de projeto (topo) → **New Project** →
  Name: `BolsIA` → Create → selecione o projeto criado.

**B2. Tela de consentimento (Branding)**
- Menu ☰ → APIs & Services → **OAuth consent screen** → Get started →
  App name: `BolsIA` · User support email: seu e-mail → Audience:
  **External** → Contact: seu e-mail → Finish/Create.
- Em **Audience → Publishing status**: clique **Publish app** (sem isso, só
  contas de teste conseguem logar).

**B3. Credencial iOS**
- APIs & Services → **Credentials** → **+ Create credentials** → **OAuth
  client ID** → Application type: **iOS** → Name: `BolsIA iOS` → Bundle ID:
  `com.alexandrecamerini.bolsia` → Create.
- **Copie o Client ID** (formato `NUMERO-xxxx.apps.googleusercontent.com`).
  → é o **GOOGLE_IOS_CLIENT_ID**.

**B4. Credencial Web (é o `aud` que o servidor valida)**
- **+ Create credentials** → **OAuth client ID** → Application type: **Web
  application** → Name: `BolsIA Server` → Create (sem redirect URIs).
- **Copie o Client ID** → é o **GOOGLE_WEB_CLIENT_ID**.

**B5. Railway → Variables**
```
GOOGLE_CLIENT_ID = <GOOGLE_WEB_CLIENT_ID do B4>
```

---

## PARTE C — Máquina local + Xcode

**C1. (🔑) Guardar os IDs do build** — na raiz do repo, crie/edite
`web/.env.local` (o .gitignore já cobre `.env*`; client_id não é segredo, mas
mantemos fora do git por higiene):
```
VITE_GOOGLE_IOS_CLIENT_ID=<GOOGLE_IOS_CLIENT_ID do B3>
VITE_GOOGLE_WEB_CLIENT_ID=<GOOGLE_WEB_CLIENT_ID do B4>
```

**C2. (🔁) Instalar plugins + regenerar o nativo**
```bash
cd web && npm install && cd ..
set -a && source web/.env.local && set +a
bash scripts/setup-ios.sh        # cap sync + URL scheme do Google no Info.plist
```
- ⚠️ Se o `npm install` reclamar de peer dependency dos plugins com o
  Capacitor 8, rode `cd web && npm i @capacitor-community/apple-sign-in@latest
  @codetrix-studio/capacitor-google-auth@latest` e me mande o erro/versões —
  ajusto a ponte se a API tiver mudado.

**C3. (🔑 no projeto gerado; refazer se apagar `web/ios/`) Xcode**
- Abrir `web/ios/App/App.xcworkspace` → target **App** → **Signing &
  Capabilities** → conferir Bundle Identifier + Team → **+ Capability →
  Sign in with Apple** (a de Push você já adicionou na migração).
- Conferir em **Info** → URL Types: deve existir um scheme
  `com.googleusercontent.apps.NUMERO-xxxx` (o setup-ios.sh injeta; se não
  estiver, adicione manualmente: é o GOOGLE_IOS_CLIENT_ID **invertido**).

**C4. (🔁) Product → Clean Build Folder → instalar no iPhone.**

---

## PARTE D — Teste no aparelho (matriz do hard stop)

| # | Cenário | O que conferir |
|---|---------|----------------|
| D1 | **Apple — 1º login** (Perfil → Entrar → Continuar com a Apple) | iOS abre o sheet nativo; escolha compartilhar ou ocultar e-mail; app mostra "Conectado."; Perfil mostra seu NOME (hint do 1º consentimento) e o e-mail (real ou `...@privaterelay.appleid.com`); Diário mostra "SIWA: token de revogação armazenado." |
| D2 | **Apple — login recorrente** (sair e entrar de novo) | Entra sem pedir nome/e-mail de novo (Apple não reenvia) e o nome CONTINUA aparecendo (persistido no D1) |
| D3 | **Google** | Sheet do Google abre; login conclui; nome/e-mail no Perfil |
| D4 | **Logout** | "Você saiu da conta."; app segue funcionando anônimo (local-first) |
| D5 | **Dois usuários isolados** | Logar com Apple, comprar um ativo, sair; logar com Google: carteira NÃO pode mostrar a posição do outro |
| D6 | **Anônimo → conta (semente)** | Sem login, montar carteira; criar conta: os dados locais viram a conta (first-login seed) |
| D7 | **Exclusão de conta** (Perfil → Sua conta → Excluir) | App volta ao anônimo; para conta Apple, o Diário/retorno registra o revoke; em Ajustes → Apple ID → Sign-In & Security → Sign in with Apple, o BolsIA some da lista |
| D8 | **Falha configurada** (opcional) | Sem `GOOGLE_CLIENT_ID` no Railway, o login Google mostra o erro acionável do servidor (não trava a tela) |

Se algo falhar: me mande a mensagem exata (a nota sob os botões e/ou o
Diário) — as mensagens foram escritas para apontar a causa (env faltando,
audience errada, plugin fora do build).

---

## Referência rápida — quem valida o quê

```
Apple  : idToken.aud = bundle id           → servidor: APPLE_CLIENT_ID
Google : idToken.aud = client WEB (B4)     → servidor: GOOGLE_CLIENT_ID
         (a ponte passa serverClientId=WEB justamente para isso)
Revoke : refresh_token trocado no login (authorizationCode, validade 5 min)
         e revogado em DELETE /api/account — best-effort, nunca bloqueia.
```
