# CHECKOUT — retomada em novo chat (BolsIA)
*Atualizado em 09/07/2026 · estado: build F9-20260709-5 aguardando instalação/confirmação no aparelho · pendências = item B da matriz qa/26*

## 1. Estado exato do projeto

- **Código/git:** tudo commitado e enviado (`main == origin/main`). Backend no
  Railway redeploya no push. Suítes locais (sandbox, offline): **19/20
  backend + 23/23 web — verdes** (1 pulada por dependência ausente no
  sandbox; rode `bash operar.sh testes` no Mac para o pytest completo).
- **Entrega:** `bash entregar.sh "msg"` faz a cadeia inteira (testes → git →
  build → cap sync → patch do AppDelegate → espelho de chunks → verificação de
  carimbo) e abre o Xcode. `bash entregar.sh --so-verificar` só audita.
- **Carimbo de build (protocolo obrigatório):** `web/src/version.js` →
  aparece no rodapé do Perfil e no `/api/health`. NENHUMA avaliação funcional
  vale sem o carimbo conferido no aparelho. Atual: **F9-20260709-5**.
- **Últimos eventos (nesta ordem):**
  1. O bundle do iPhone foi AMPUTADO por um bug do entregar.sh (chunks de
     import dinâmico apagados → "plugin não instalado"). Corrigido + guardião
     de paridade (F9.1).
  2. Item A da matriz (notificações/push) continuou falhando mesmo no build
     íntegro: botão "Pedir permissão" morto, "Ativar push" travado em
     deadlock, app sumindo de Ajustes → Notificações, Diagnóstico travando
     sem responder. Hipótese de cache do Xcode (DerivedData/SPM) testada e
     DESCARTADA (qa/27) — reparo profundo não resolveu.
  3. **Causa-raiz real encontrada via Web Inspector do Safari no aparelho
     físico** (qa/28): bug de "thenable auto-chaining" em `notify.js` — o
     proxy do plugin nativo era retornado cru de uma `async function`, o
     motor JS tratava como Promise aninhada e chamava `.then()` nele, virando
     uma chamada de bridge pro método inexistente `"then"`. Corrigido
     (boxing `{ p }` em todos os 9 call sites) + guardião
     `test_notify_plugin_boxing.mjs`. **Confirmado funcionando pelo usuário
     no aparelho físico** após esta correção.

## 2. PENDÊNCIAS — o que ainda NÃO foi validado (fonte: `qa/26-matriz-revalidacao.md`)

- **A · Notificações (A1–A6):** ✅ CONFIRMADO funcionando no aparelho após
  qa/28 (build F9-20260709-5). Falta só reconfirmar A5/A6 (push remoto)
  formalmente — dependem das envs APNs no Railway (`APNS_SANDBOX=1`).
- **B · Identidade/Modo Operador (B1–B7):** ⏳ AINDA NÃO REPORTADO. O usuário
  mencionou "identidade parcial" de forma genérica, sem apontar quais dos 7
  itens falharam nem o que a tela mostrou. Os guardiões de tema
  (`test_copy_theme.mjs`, `test_modo_operador.mjs`) já passam no
  repositório — se ainda falhar no aparelho, é preciso o mesmo nível de
  detalhe que resolveu o item A (item exato + o que a tela mostra + console
  se travar).
- **C · IA nas duas vozes (C1–C5):** não testado nesta rodada.
- **D · Conta/Login (D1–D4):** não testado nesta rodada.
- **E · Plataforma (E1–E4):** não testado nesta rodada.

**Como reportar no novo chat:** só as falhas, formato `A5 FALHA — <o que viu>`.
Se travar sem mensagem clara, o Web Inspector do Safari (Desenvolver → nome
do iPhone → BolsIA → aba Console) é a ferramenta que resolveu o item A —
usar de novo antes de especular causa.

## 3. Armadilhas conhecidas (não redescobrir)

1. `web/ios/` e `web/dist/` são GITIGNORADOS. A pasta ios/ é regenerável — o
   AppDelegate PERDE os callbacks do APNs quando isso acontece; o
   `scripts/ios-patch-appdelegate.sh` (idempotente) reaplica e o entregar.sh
   o chama sempre. Guardião: `test_push_wiring.mjs`.
2. O Vite gera VÁRIOS `index-*.js` (chunks de import dinâmico). NUNCA apagar
   por padrão de nome; órfão = o que não existe no `dist/` atual. Guardião:
   `test_ios_assets.mjs` (paridade só quando os carimbos coincidem).
3. A URL do Railway é SÓ API (deploy sobe apenas `server/`). Telas mudam
   APENAS via entregar.sh + Xcode (⇧⌘K + Run).
4. Detector de carimbo usa o formato `F<fase>-<AAAAMMDD>-<n>` (minificado
   contém strings tipo `F900-` que já causaram falso positivo).
5. iOS local-first: estado do servidor NUNCA sobrescreve o doc do aparelho
   (auth.me/login). Guardião: `test_copy_theme.mjs` (seção N2).
6. Regras do projeto: baseline verde antes de mexer, causa-raiz primeiro,
   patch cirúrgico + 1 guardião por bug, hard stop no aparelho, docs em qa/.
7. **Projeto é 100% SPM, SEM CocoaPods** — nunca existe `App.xcworkspace`,
   só `App.xcodeproj`. Qualquer script/instrução que mande abrir o
   `.xcworkspace` está errado para este projeto. Guardião:
   `test_ios_open_target.mjs`.
8. **Chamada nativa de plugin Capacitor "trava" sem erro visível na UI ⇒
   suspeitar de thenable auto-chaining, não de cache/build.** Se uma função
   `async` guarda/devolve o objeto de um plugin nativo (`return _plugin;`)
   em vez de um valor "boxed" (`return { p: _plugin };`), o motor JS trata o
   proxy do plugin como uma Promise (porque ele responde a `.then` como
   qualquer outro método) e chama `.then()` nele — vira uma chamada de
   bridge real pro método `"then"`, que não existe:
   `"<Plugin>.then() is not implemented on ios"`. Sintoma: a chamada nunca
   resolve nem rejeita de forma visível na UI, mesmo com o plugin
   corretamente linkado no binário — NENHUM guardião de arquivo estático
   pega isso, só o console real do aparelho (Web Inspector do Safari).
   Fix padrão: toda função que cacheia/devolve um proxy de plugin nativo
   deve embrulhar em `{ p: ... }`, nunca devolver o proxy cru. Ver qa/28 e
   `web/tests/test_notify_plugin_boxing.mjs` para o padrão de guardião.
   **Isso vale para QUALQUER plugin Capacitor futuro (push, camera, etc.),
   não só LocalNotifications** — ao adicionar um novo wrapper de plugin,
   aplique o boxing desde o início.

## 4. Histórico (1 linha por fase; detalhes nos qa/)

- **F5** (qa/18): watchlist via Radar, push callbacks, login hardening,
  observabilidade, cache candles em SQLite, scripts.
- **F6** (qa/19): servidor de produção embutido, formatação N1, toggle do
  Operador-servidor, central de notificações, reasons APNs.
- **F7.1** (qa/20): Modo Operador — plano determinístico (R:R≥1,5, decisões),
  termo, sizing.
- **F8A** (qa/21): "alert"→banner/list (causa real do banner mudo), aud em
  lista no login Apple, logout com reset de escopo.
- **F8B** (qa/22–25): dois-apps-em-um completo (copy.js 35+ chaves, tema por
  modo até nos gráficos, prompts/skills por modo, login unificado, paleta do
  mock, e-mail relay).
- **F9/9.1**: protocolo de entrega com carimbo (entregar.sh), patch
  automático do AppDelegate, reparo do bundle amputado + paridade de chunks.
- **F9 (qa/27)**: item A revalidado — hipótese de cache do Xcode/SPM testada
  e descartada; script de reparo profundo criado mesmo assim (útil pra outros
  casos de cache); bug do fallback `App.xcworkspace` (projeto é SPM puro)
  corrigido nos 3 scripts que abrem o Xcode.
- **F9 (qa/28)**: causa-raiz real do item A — thenable auto-chaining no
  proxy do plugin `LocalNotifications` em `notify.js`. Corrigido com boxing
  `{ p }` nos 9 call sites + guardião. **Confirmado funcionando no
  aparelho.** Build F9-20260709-5.

## 5. Prompt pronto para o novo chat

```
Contexto: leia CHECKOUT-NOVO-CHAT.md, qa/26-matriz-revalidacao.md, qa/27 e
qa/28 na raiz do repo b3-agente. Regras do projeto valem (baseline verde,
causa-raiz, guardião por bug, carimbo de build antes de qualquer avaliação,
docs em qa/). Se uma chamada nativa de plugin "trava" sem erro, ver
armadilha #8 antes de suspeitar de cache/build.

Estado: build F9-20260709-5 instalado e confirmado no rodapé do Perfil.
[SE NÃO: rode 'bash entregar.sh "retomada"' + Xcode ⇧⌘K + Run primeiro.]

Item A (notificações/push): CONFIRMADO OK pelo usuário.

Resultado do item B (Identidade/Modo Operador) e dos itens C/D/E da matriz
qa/26 no aparelho:
- <liste aqui APENAS as falhas, ex.: B2 FALHA — sparkline continua azul>
- <...>

Tarefa: para cada falha, diagnostique a causa-raiz (Logs do servidor,
Diagnóstico do app, console do Web Inspector se algo travar sem erro claro),
corrija cirurgicamente com teste-guardião, rode as suítes completas e feche
com qa/29 + roteiro de hard stop. Ao final, rode
'bash entregar.sh --so-verificar' e me passe o novo carimbo.
```
