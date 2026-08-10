# F3.3b — Push (APNs) das ações do agente · passo a passo
Pré-requisito confirmado: conta Apple Developer PAGA. O código já está pronto
dos dois lados (servidor: `push.py` + `/api/push/register-token`; app:
`notify.registerPush` + botão em Automatizar). Falta só a configuração:

## 1) Chave de push no portal Apple (uma vez)
1. developer.apple.com → **Certificates, Identifiers & Profiles** → **Keys**
   → **+** → marque **Apple Push Notifications service (APNs)** → Register.
2. **Baixe o arquivo `.p8`** (só dá para baixar UMA vez — guarde) e anote o
   **Key ID**. O **Team ID** está no topo direito da página de Membership.

## 2) Capability no Xcode (uma vez)
`npx cap open ios` → target **App** → **Signing & Capabilities** →
**+ Capability** → **Push Notifications**. (Background Modes não é necessário
para alerts.) Rebuild no aparelho.

## 3) Variáveis no Railway (uma vez)
No serviço → Variables:
- `APNS_TEAM_ID` = seu Team ID
- `APNS_KEY_ID`  = o Key ID da chave
- `APNS_AUTH_KEY` = o CONTEÚDO do .p8 (abra no editor e cole o PEM inteiro)
- `APNS_TOPIC` = bundle id do app (o mesmo do Xcode, ex.: `com.alexandrecamerini.bolsia`)
- `APNS_SANDBOX` = `1` só para build de desenvolvimento (TestFlight/App Store: remova)

## 4) Ativar no app
Aba **Automatizar** → "Agente no servidor" LIGADO → **Ativar push das ações
(iPhone)** → aceitar a permissão. O token do aparelho vai para a sua conta.

## 5) Teste de ponta a ponta
Posição com stop próximo → agente no servidor em modo "executar" → feche o
app → quando o ciclo do servidor vender no stop, o push chega. Sem as
variáveis do passo 3 o app avisa: "token salvo — configure as chaves APNs".

## Comportamento sem APNs (fallback 3.3a, sempre ativo)
Toda ação/sinal fica no **Registro do agente** (aba Automatizar) e, ao abrir
o app, uma notificação local resume: "o agente fez X ações desde sua última
visita".
