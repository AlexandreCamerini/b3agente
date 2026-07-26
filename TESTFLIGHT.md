# TestFlight — checklist de distribuição do BolsIA

Fluxo para subir o app iOS ao TestFlight. Itens **[script]** eu automatizei;
**[Xcode]** e **[portal]** são manuais (você faz). O backend é à parte
(`DEPLOY_RAILWAY.md`); push em detalhe no `APNS-PUSH.md`.

Bundle id: `com.alexandrecamerini.bolsia` · Team: `LC65399YC9` · Nome: **BolsIA**

---

## 1. Preparo do projeto (uma vez)

1. **[script]** Gere o projeto e sincronize os assets web:
   ```bash
   bash scripts/setup-ios.sh --no-open && (cd web && npx cap sync ios)
   ```
2. **[script]** Aplique os patches de TestFlight (manifesto de privacidade + export compliance):
   ```bash
   bash scripts/ios-testflight.sh
   ```
3. **[Xcode]** AÇÃO ÚNICA que o script pede: arraste
   `web/ios/App/App/PrivacyInfo.xcprivacy` para o grupo **App** no Xcode e marque
   o target **App**. (O projeto é SPM e ignorado no git, então essa referência
   fica no projeto local; persiste entre `cap sync`, só precisa uma vez.)

## 2. Apple Developer (portal)

4. **[portal]** Renomeie o **App ID**: `AppID Prod` → **BolsIA**
   (developer.apple.com → Identifiers). *Não* muda o bundle id; é só o display
   name que hoje bloqueia/atrapalha a distribuição.
5. **[portal]** No App ID, confirme as capabilities: **Push Notifications** e
   **Sign in with Apple** habilitadas.
6. **[portal]** Confirme a **APNs Auth Key (.p8)** ativa (a mesma que o Railway usa
   — ver `APNS-PUSH.md`).

## 3. App Store Connect (uma vez)

7. **[portal]** Crie o app: My Apps → **+** → novo app, bundle id
   `com.alexandrecamerini.bolsia`, nome **BolsIA**, idioma pt-BR.
8. **[portal]** Preencha **App Privacy** (dados coletados). O app tem contas/login
   → declare pelo menos **e-mail** (vinculado à identidade, uso: funcionalidade do
   app; sem tracking). Isso deve BATER com o `PrivacyInfo.xcprivacy`.

## 4. Push em produção (coordenado — só ao cortar o TestFlight)

> TestFlight/App Store usam APNs de **produção**. Hoje o app está em `development`
> e o servidor em sandbox (para o teste via Xcode). Vire os DOIS JUNTOS:

9. **[script]** `bash scripts/ios-testflight.sh --apns-prod`
   (seta `aps-environment=production` no entitlement).
10. **[portal/Railway]** Remova/zere `APNS_SANDBOX` no Railway (produção).
    - Para VOLTAR ao dev local depois: `--apns-dev` + `APNS_SANDBOX=1`.

## 5. Build e upload (a cada envio)

11. **[script]** Incremente o build number (cada upload exige um novo):
    ```bash
    bash scripts/ios-bump-build.sh
    ```
12. **[Xcode]** Product → **Archive** (target genérico "Any iOS Device").
13. **[Xcode]** Organizer → **Distribute App** → **App Store Connect** → Upload.
    Assinatura **Automatic** cuida do provisioning.
14. **[portal]** Aguarde o processamento (minutos) em App Store Connect →
    TestFlight. Com `ITSAppUsesNonExemptEncryption=false` **não** aparece o prompt
    de export compliance.
15. **[portal]** Adicione o build ao grupo de testers (interno primeiro) e convide.

## 6. Verificação pós-install (no iPhone via TestFlight)

16. Abra o app, faça login, confirme o rodapé do Perfil com o BUILD_ID web atual.
17. Toque em **"Ativar push das ações"** e rode o smoke test de push
    (`POST /api/push/test` ou o botão no app). Deve chegar a notificação — se der
    "token de outro ambiente", os itens 9–10 (APNs prod) não estão alinhados.

---

### Referência rápida dos scripts
| Script | O quê |
|---|---|
| `scripts/setup-ios.sh` | gera o projeto iOS (Capacitor) |
| `scripts/ios-testflight.sh` | manifesto de privacidade + export compliance (+`--apns-prod/--apns-dev`) |
| `scripts/ios-bump-build.sh` | incrementa o build number |
| `resources/ios/PrivacyInfo.xcprivacy` | manifesto de privacidade versionado (fonte) |

O que **não** precisa: exceções ATS (o app é HTTPS puro) e `instalar-iphone.sh`
não tem relação com distribuição (é dev local).
