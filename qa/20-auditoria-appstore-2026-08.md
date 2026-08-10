# QA 20 — Auditoria App Store · Boris+ · 10/08/2026

*Sucede a qa/17 (07/07). Estado auditado: `main` f4b0253 · produção
`boris.semente.dev` no ar com `F10-20260810-01` (health 200 em 0,7s).
Método: leitura de Info.plist, entitlements, PrivacyInfo, pbxproj,
capacitor.config, código de login/STT/api-base e testes de assets — não
opinião de memória. ✋ = ação do Alex · 🔴 bloqueia · 🟡 defensável com nota.*

## O que mudou desde a qa/17 e invalida partes dela

| Mudança | Efeito na submissão |
|---|---|
| **Login obrigatório** (09/08) | A descrição proposta na qa/17 diz "ou use sem conta nenhuma" — hoje é **falso** (2.3.7, veracidade de metadata). E o risco 5.1.1(i) passa a existir (ver R1). |
| **Rebranding Boris+** | `CFBundleDisplayName` = "Boris+", mas a ficha planejada e o App Store Connect dizem **BolsIA**, e o bundle é `com.alexandrecamerini.bolsia`. Decisão de marca antes de submeter. |
| **Endpoint próprio no ar** | `PROD_BASE = https://boris.semente.dev` embutido no app nativo e respondendo — o build de loja **sem** `--api-base` já nasce apontando para produção. Resolve o que seria o maior bloqueador. |
| **Tela preta no aparelho de dev** | Em aberto, sem diagnóstico. Nada se submete até isolar (ver B1). |

---

## B) BLOQUEADORES — rejeição provável se submeter hoje

### 🔴 B1 · Tela preta no launch (Guideline 2.1 — App Completeness)
O aparelho de teste abre em tela preta. Investigação já feita descartou:
bundle amputado (`test_ios_assets` verde), `server.url` no Capacitor
(não existe — carrega arquivo local), storyboard (referenciado 6× no pbxproj,
VC inicial `CAPBridgeViewController`), SceneDelegate duplicado (embutido no
AppDelegate, como projetado), rede (backend respondia). Preto puro com o app
tendo telas próprias de erro/carregando = **exceção de JS antes do 1º render**.
**Ação ✋:** Safari Web Inspector no aparelho (Ajustes → Safari → Avançado →
Inspetor da Web; Mac: Safari → Desenvolver → iPhone → Boris+) e capturar a
primeira linha vermelha do console. Sem isso, nenhuma submissão.

### 🔴 B2 · Privacy manifest vazio × login obrigatório
`PrivacyInfo.xcprivacy` está com `NSPrivacyCollectedDataTypes` **vazio** — o
próprio arquivo avisa que isso era tolerável só para TestFlight. Com login
obrigatório, **todo** usuário tem e-mail + User ID + conteúdo (carteira
simulada) coletados: o manifesto e os labels do Connect precisam dizer isso, e
**precisam bater entre si**. Bloco pronto para o manifesto:

```xml
<key>NSPrivacyCollectedDataTypes</key>
<array>
  <dict>
    <key>NSPrivacyCollectedDataType</key>
    <string>NSPrivacyCollectedDataTypeEmailAddress</string>
    <key>NSPrivacyCollectedDataTypeLinked</key><true/>
    <key>NSPrivacyCollectedDataTypeTracking</key><false/>
    <key>NSPrivacyCollectedDataTypePurposes</key>
    <array><string>NSPrivacyCollectedDataTypePurposeAppFunctionality</string></array>
  </dict>
  <dict>
    <key>NSPrivacyCollectedDataType</key>
    <string>NSPrivacyCollectedDataTypeUserID</string>
    <key>NSPrivacyCollectedDataTypeLinked</key><true/>
    <key>NSPrivacyCollectedDataTypeTracking</key><false/>
    <key>NSPrivacyCollectedDataTypePurposes</key>
    <array><string>NSPrivacyCollectedDataTypePurposeAppFunctionality</string></array>
  </dict>
  <dict>
    <key>NSPrivacyCollectedDataType</key>
    <string>NSPrivacyCollectedDataTypeDeviceID</string>
    <key>NSPrivacyCollectedDataTypeLinked</key><true/>
    <key>NSPrivacyCollectedDataTypeTracking</key><false/>
    <key>NSPrivacyCollectedDataTypePurposes</key>
    <array><string>NSPrivacyCollectedDataTypePurposeAppFunctionality</string></array>
  </dict>
  <dict>
    <key>NSPrivacyCollectedDataType</key>
    <string>NSPrivacyCollectedDataTypeOtherUserContent</string>
    <key>NSPrivacyCollectedDataTypeLinked</key><true/>
    <key>NSPrivacyCollectedDataTypeTracking</key><false/>
    <key>NSPrivacyCollectedDataTypePurposes</key>
    <array><string>NSPrivacyCollectedDataTypePurposeAppFunctionality</string></array>
  </dict>
</array>
```

(Device ID = token de push, vinculado à conta. Labels do Connect: a lista da
qa/17 §App Privacy continua exata — declarar idêntico ao manifesto.)
**Fonte versionada** é `scripts/ios-testflight.sh` quem copia — editar lá.

### 🔴 B3 · Política de privacidade sem URL pública
O Connect exige URL. `POLITICA-PRIVACIDADE.md` existe no repo, mas **nenhuma
rota a serve** (verificado em `main.py`). Menor caminho: rota
`GET /privacidade` no backend servindo o texto (o domínio próprio já está no
ar), ou GitHub Pages como a qa/17 sugeria. ✋ colar a URL no Connect.

### 🔴 B4 · `aps-environment = development` no entitlement
TestFlight/App Store usam APNs de **produção**. Já previsto no TESTFLIGHT.md §4:
`bash scripts/ios-testflight.sh --apns-prod` **e** remover `APNS_SANDBOX` do
Railway — os dois juntos, senão o push morre num dos lados. ✋

### 🔴 B5 · Botão Google visível sem configuração no build
`Info.plist` atual **não tem `CFBundleURLTypes`** ⇒ o último build saiu sem
`VITE_GOOGLE_IOS_CLIENT_ID`/`VITE_GOOGLE_WEB_CLIENT_ID` (o URL scheme entra
via `setup-ios.sh` quando as vars existem — LOGIN-SOCIAL.md §C). Nesse estado,
o botão "Continuar com o Google" aparece e **falha ao toque** ("Login Google
não configurado neste build") — revisor toca, vê erro, rejeita por 2.1.
**Ação:** ou build de loja com as duas vars (roteiro LOGIN-SOCIAL partes B/C),
ou esconder o botão quando `social.js` reportar Google indisponível. SIWA
continua atendendo a 4.8 sozinho; o problema não é 4.8, é botão quebrado.

### 🔴 B6 · Ficha desatualizada e marca indecisa (2.3.7)
- Descrição da qa/17 promete **"ou use sem conta nenhuma"** — remover.
- Bullet substituto: `• SUA CONTA, SEUS DADOS — entre com Apple ou Google e
  continue de onde parou em qualquer aparelho. Excluir a conta apaga tudo,
  direto no app.`
- **Marca**: exibição "Boris+" × loja "BolsIA" × bundle `…bolsia`. Nome de
  loja ≠ display name não rejeita por si, mas confunde revisor e usuário.
  ✋ Decidir: ou a ficha vira Boris+ (nome + subtítulo + screenshots), ou o
  display name volta a BolsIA. O bundle id pode ficar (invisível ao usuário).

---

## C) RISCOS DEFENSÁVEIS — prováveis perguntas, respostas prontas

### 🟡 R1 · Login obrigatório (5.1.1(i))
A regra: app sem "significant account-based features" deve funcionar sem
login. Defesa real do Boris+: a conta **é** o núcleo — carteira sincronizada
entre aparelhos, Operador IA rodando no servidor com o app fechado, push, e
exclusão de dados via conta. Minimização ok: só e-mail/senha (nome opcional),
SIWA com relay em primeiro. **Exigências práticas ✋:** conta demo em App
Review Information (a qa/17 já pedia; com login obrigatório virou
indispensável) e nota de revisor atualizada:

> "Account is required because the simulated portfolio, server-side automation
> (Operador IA) and push notifications are account-bound and sync across
> devices. Sign in with Apple offered first. Demo: review@… / senha…
> Educational paper-trading simulator: no real money, no brokerage connection,
> no investment advice (fixed educational vocabulary enforced server-side)."

### 🟡 R2 · Dados do Yahoo Finance (5.2.2/5.2.3)
Os termos do Yahoo vedam uso comercial; risco já documentado internamente
(`candle_provider.py`, com gatilho de troca de provedor medido). Mitigações:
app gratuito hoje, fonte não citada na ficha, plano B (Cedro/UP2DATA) definido
para antes de monetizar. Risco aceito conscientemente — decisão sua, não
técnica.

### 🟡 R3 · Conteúdo financeiro gerado por IA
Mitigado por arquitetura: LLM só interpreta números pré-calculados, vocabulário
sem imperativo travado por teste, disclaimer em todo output, dinheiro
simulado, categoria primária **Educação**. 3.1.5/3.2.1 não se aplicam: sem
dinheiro real, sem ordem, sem corretora.

### 🟡 R4 · Microfone (barato de blindar)
O botão de voz do chat usa `SpeechRecognition`/`webkitSpeechRecognition` com
guarda de existência — no WKWebView a API não existe e o botão **não
renderiza**, então hoje nenhuma permissão é exigida. Se um iOS futuro expor a
API, o toque derruba o app por falta de string. Seguro de uma linha cada:
`NSMicrophoneUsageDescription` + `NSSpeechRecognitionUsageDescription` no
Info.plist (via `setup-ios.sh` para sobreviver ao `cap sync`).

---

## D) CONFORME — verificado nesta auditoria, com evidência

| Exigência | Evidência |
|---|---|
| 4.8 Sign in with Apple presente e **primeiro** | tela de login (screenshot da sessão); entitlement `com.apple.developer.applesignin` |
| 5.1.1(v) exclusão de conta in-app | botão "Excluir conta" + `delete_user_data` + revoke SIWA (qa/17 §B) |
| ATS sem exceção ampla | Info.plist: só `NSAllowsLocalNetworking` (+ string de uso); produção em HTTPS |
| Backend de produção embutido | `PROD_BASE=https://boris.semente.dev` (api.js:20) respondendo `{"ok":true}` |
| Export compliance | `ITSAppUsesNonExemptEncryption=false` |
| UIScene (exigência do SDK iOS 27) | manifest no Info.plist + SceneDelegate embutido no AppDelegate (target ok) |
| Ícones/splash | `test_ios_assets.mjs` verde: 1024 sem alpha, íntegro, mesmos chunks |
| Push pedido em contexto | permissão só ao ativar em Config; sem background modes extras |
| Sem tracking | `NSPrivacyTracking=false`, sem IDFA, sem ATT |
| Sem IAP ativo | `plan.py` dormente — nada a declarar em 3.1.1 por ora |
| Versão coerente | MARKETING_VERSION 2.0, build 5 |

---

## E) Ordem de execução até a submissão

1. ✋ **B1** — diagnosticar a tela preta (Web Inspector) e corrigir. Porta de tudo.
2. **B5** — configurar Google (vars + rebuild) *ou* esconder o botão sem config.
3. **B2** — preencher o manifesto (bloco acima) em `scripts/ios-testflight.sh`
   e declarar os labels idênticos no Connect.
4. **B3** — publicar a política e colar a URL no Connect. ✋
5. **B4** — `--apns-prod` + remover `APNS_SANDBOX` no Railway, juntos. ✋
6. **B6** — decidir a marca da ficha ✋ e reescrever a descrição (sem "sem conta").
7. R4 — adicionar as duas strings de permissão (uma linha cada no setup).
8. Build de loja: `setup-ios.sh` **sem `--api-base`** (cai no PROD_BASE) e
   **com** `VITE_GOOGLE_*`; `bump.sh`; archive; TestFlight; conta demo ✋;
   screenshots 6,7"/6,1" ✋; submeter.

*Restante da qa/17 que segue válido sem mudança: categoria Educação+Finanças,
classificação 4+, palavras-chave, App Privacy "não usado para tracking",
respostas de revisor sobre simulação educacional.*

---

## Adendo — correções aplicadas em 10/08 (F10-20260810-02)

| Item | Estado | Como |
|---|---|---|
| B1 | **instrumentado** | Guarda de BOOT em `web/index.html`: JS morrendo antes do React montar pinta o ERRO REAL (mensagem + stack + "Tentar de novo") no lugar da tela preta. Só age com `#root` vazio; só trata falha de `<script>` (fonte offline não dispara); se o app montar, o painel se remove. O diagnóstico no aparelho deixa de exigir cabo + Web Inspector. |
| B2 | **corrigido** | `resources/ios/PrivacyInfo.xcprivacy` (e a cópia gerada) declara EmailAddress, UserID, DeviceID e OtherUserContent — vinculados, sem tracking (`plutil` OK). ✋ resta espelhar nos App Privacy labels do Connect. |
| B3 | **corrigido** | `GET /privacidade` (+ alias `/privacy`) serve o próprio `POLITICA-PRIVACIDADE.md` renderizado. A política foi ATUALIZADA: saiu o "com conta (opcional)"/modo local (login é obrigatório desde F10-20260810-01), marca Boris+, data nova. URL para o Connect: `https://boris.semente.dev/privacidade` (após deploy). |
| B5 | **corrigido** | Botão Google SOME no build nativo sem `VITE_GOOGLE_*` (volta sozinho no build configurado; web inalterado). Apple continua incondicional e primeiro (4.8). |
| R4 | **corrigido** | `NSMicrophoneUsageDescription` + `NSSpeechRecognitionUsageDescription` no `setup-ios.sh` (idempotente) e já aplicadas ao Info.plist gerado. |

Guardiões: `server/tests/test_politica_privacidade.py` (6) + `web/tests/test_qa20_appstore.mjs` (15). Suítes: 753 backend + 67 web.

**Seguem manuais (✋):** B1 causa-raiz (rodar o build novo e ler o painel/console), B4 (`--apns-prod` + `APNS_SANDBOX`), B6 (marca + ficha), labels do Connect, conta demo, screenshots.

**B6 — atualização 10/08:** marca decidida: **Boris+** em tudo que o usuário vê
(`appName` do Capacitor, título, PWA, disclaimers, docs vivas — ver commit do
rename). Bundle id `com.alexandrecamerini.bolsia` MANTIDO (trocar publicaria
outro app e quebraria todo login SIWA). ✋ resta renomear o app no App Store
Connect para "Boris+" e refazer screenshots.
