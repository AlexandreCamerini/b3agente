# QA 27 — Diagnóstico: notificações/push travados mesmo com o carimbo certo
*09/07/2026 · relato no aparelho físico, build F9-20260709-4 CONFIRMADO no rodapé do Perfil.*

## 1. Sintoma relatado (Alex, aparelho físico)

- A1 FALHA — botão "Pedir permissão" existe mas não faz nada perceptível.
- A5 FALHA — "Ativar push neste aparelho" fica desabilitado (deadlock: Testar
  push diz "nenhum aparelho registrado" e manda usar Ativar push, que está
  travado por não ter permissão concedida).
- Diagnóstico (Perfil → Notificações → botão DIAGNÓSTICO) **não responde
  nada** ao tocar — trava, não abre o painel de resultado.
- A linha de status (abaixo do toggle mestre) **não mostra texto**.
- **Fato mais importante:** o BolsIA **sumiu da lista de Ajustes → Notificações**
  do iOS — ele nem aparece mais lá para o usuário conceder/negar manualmente.

## 2. O que foi DESCARTADO (evidência, não suposição)

Antes de mexer em qualquer coisa, auditei o estado do repositório contra o
protocolo do projeto (baseline verde antes de mexer):

- `git status` limpo, `main == origin/main`.
- Carimbo `F9-20260709-4` consistente em `web/src/version.js`, `web/dist/` e
  `web/ios/App/App/public/assets` (os três elos que o `entregar.sh` trava).
- 19/20 suítes backend offline verdes (1 pulada por dependência ausente no
  sandbox, não relacionada), 21/21 suítes web verdes — **incluindo os dois
  guardiões que existem exatamente para os bugs históricos desta área**:
  `test_push_wiring.mjs` (callbacks do APNs no AppDelegate, presentationOptions
  banner+list) e `test_ios_assets.mjs` (paridade de chunks dist × bundle iOS).
- Conferido manualmente: `Package.swift` (SPM) lista
  `CapacitorLocalNotifications` e `CapacitorPushNotifications` como
  dependências do target; `capacitor.config.json` sincronizado tem
  `packageClassList` com `LocalNotificationsPlugin` e `PushNotificationsPlugin`.

**Conclusão da etapa 2:** o CÓDIGO-FONTE está correto. Não é um bug de lógica
JS nem de configuração desatualizada no repositório — os mesmos arquivos que
os guardiões já vigiam por bugs anteriores (R1 da FASE 8B, o bug do AppDelegate
da FASE 6) estão certos.

## 3. Causa-raiz mais provável

O sintoma — app "compila e roda" mas o plugin nativo nunca é solicitado de
verdade (some de Ajustes → Notificações; qualquer chamada nativa ao plugin,
como o `getPending()` do Diagnóstico, FICA PENDURADA em vez de responder ou
lançar erro) — bate com um problema conhecido do Capacitor com pacotes SPM
**locais** (`path: "../../../node_modules/@capacitor/..."`): o Xcode resolve
e cacheia esses pacotes (DerivedData + `~/Library/Caches/org.swift.swiftpm`),
e esse cache pode ficar preso a uma resolução ANTIGA depois de um `cap sync`
ou `npm install` — mesmo que o `Package.swift` e o `capacitor.config.json` no
disco já estejam certos. O binário instalado no iPhone reflete o cache velho,
não a fonte atual.

Isso explica os DOIS sintomas com uma causa só:
- Plugin de fato não linkado ⇒ `UNUserNotificationCenter` nunca é
  solicitado ⇒ app não aparece em Ajustes.
- Chamada nativa a um plugin "fantasma" (existe na ponte JS, mas a classe
  Swift não foi compilada de verdade no binário) ⇒ a Promise nunca resolve
  nem rejeita ⇒ Diagnóstico e Pedir permissão parecem mortos.

O próprio `scripts/instalar-iphone.sh` já documentava esse padrão de falha
("a causa do app nem aparecer em Ajustes -> Notificações era build sem
sync") e já tinha o roteiro manual de emergência no rodapé — mas nenhum
script fazia a limpeza de cache de ponta a ponta, e nenhum guardião
conferia o `packageClassList`. Os dois foram fechados agora (seção 4).

**Importante — isto é a causa mais provável com base nas evidências, não uma
confirmação no aparelho** (não tenho acesso físico ao iPhone). O roteiro da
seção 5 é o teste que confirma ou descarta a hipótese.

## 4. Correção aplicada (patch cirúrgico + guardião)

- **Novo:** `scripts/reparo-plugin-nativo.sh` — limpa
  `~/Library/Caches/org.swift.swiftpm`, `~/Library/org.swift.swiftpm`, a
  resolução local de pacotes do projeto e o `DerivedData` do app; reinstala
  dependências; roda `cap sync ios`; reaplica o patch do AppDelegate; **verifica
  programaticamente** que o `packageClassList` sincronizado contém
  `LocalNotificationsPlugin` e `PushNotificationsPlugin` antes de abrir o
  Xcode; imprime o roteiro manual exato (Reset Package Caches → Resolve
  Package Versions → Clean Build Folder → apagar o app do iPhone → Run).
- **Novo guardião** em `web/tests/test_push_wiring.mjs`: tranca que o
  `capacitor.config.json` sincronizado tenha `LocalNotificationsPlugin` e
  `PushNotificationsPlugin` no `packageClassList`. Não pega cache do Xcode
  (isso não é inspecionável por um teste de arquivo), mas pega qualquer
  regressão futura em que o `cap sync` pare de registrar essas classes no
  config — a metade do problema que É verificável por código.
- Suítes completas rodadas de novo após o patch: **19/20 backend offline (1
  pulada, dependência ausente) + 21/21 web, 0 falhas** (mesmo resultado de
  antes, mais o guardião novo passando).

## 5. Roteiro de hard stop (o que o Alex precisa rodar no Mac)

```bash
# 1) Feche o Xcode primeiro (o script recusa rodar com ele aberto)
cd ~/dev/bolsia/b3-agente   # ou o caminho do seu clone
bash scripts/reparo-plugin-nativo.sh
```

No Xcode, quando ele abrir, siga a ordem exata que o script imprime:
1. File → Packages → **Reset Package Caches** (espere a barra de progresso
   terminar).
2. File → Packages → **Resolve Package Versions** (espere terminar de novo).
3. Product → **Clean Build Folder** (⇧⌘K).
4. **No iPhone:** apague o app BolsIA da tela antes de reinstalar — isso
   limpa o registro antigo do app em Ajustes → Notificações.
5. Selecione o iPhone físico (não o simulador) e Product → **Run**.

Depois de instalado:
1. Confirme o carimbo no rodapé do Perfil.
2. Perfil → Notificações → **Diagnóstico** — agora deve responder na hora.
   Reporte o texto exato (as 4 linhas + veredito) se ainda travar.
3. Se `plugin nativo carregado: true` e a permissão estiver em `default`,
   toque em **Pedir permissão** — o BolsIA deve reaparecer em
   Ajustes → Notificações.
4. Retome a matriz A (A1–A6) e reporte só as FALHAS remanescentes, no mesmo
   formato de sempre (`A5 FALHA — ...`).

**Nota sobre A5/A6 (push remoto):** mesmo com o plugin funcionando, push de
verdade com o app fechado depende das chaves APNs configuradas no Railway
(`APNS_SANDBOX=1` no build de Xcode) — se o Diagnóstico já mostrar tudo OK e
"Ativar push" mesmo assim disser "falta configurar as chaves APNs", esse é
um problema DIFERENTE (config do servidor, não do app) — reporte separado.

## 6. Pendências desta rodada

- **Item B (Identidade/Modo Operador, B1–B7):** o Alex reportou "identidade
  parcial" de forma genérica, sem apontar quais dos 7 itens falharam nem o
  que a tela mostrou. Aguardando o detalhamento antes de investigar — os
  guardiões de tema (`test_copy_theme.mjs`, `test_modo_operador.mjs`) já
  passam no repositório, então a mesma pergunta se aplica: é cache/build
  velho no aparelho, ou regressão de código? Precisa dos itens exatos para
  não caçar no escuro.
- Suíte pytest completa (219 casos) não pôde ser confirmada NESTE ambiente de
  sandbox (o venv local é específico do Mac do Alex e o sandbox não tem
  acesso à rede para instalar um venv próprio) — a cobertura offline (19
  suítes puras, 0 falhas) é a evidência disponível aqui. Recomendo rodar
  `bash operar.sh testes` no Mac antes do `entregar.sh` final para confirmar
  os 219 casos completos.
