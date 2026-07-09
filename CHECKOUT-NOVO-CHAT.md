# CHECKOUT — retomada em novo chat (BolsIA)
*Atualizado em 10/07/2026 · estado: build F9-20260709-8 aguardando instalação/confirmação no aparelho · pendências = decisões de UX (badge/paleta avançada/reorg do Perfil, ver qa/32) + Fase B (trades reais) + item B(resto)/C/D/E da matriz qa/26*

## 1. Estado exato do projeto

- **Código/git:** tudo commitado localmente nesta sessão (sandbox sem rede —
  push feito da próxima vez que rodar `entregar.sh` no Mac). Backend no
  Railway redeploya no push. Suítes locais (sandbox, offline): **20/20
  backend + 28/28 web — verdes** (1 pulada por dependência ausente no
  sandbox; rode `bash operar.sh testes` no Mac para o pytest completo).
- **Entrega:** `bash entregar.sh "msg"` faz a cadeia inteira (testes → git →
  build → cap sync → patch do AppDelegate → espelho de chunks → verificação de
  carimbo) e abre o Xcode. `bash entregar.sh --so-verificar` só audita.
- **Carimbo de build (protocolo obrigatório):** `web/src/version.js` →
  aparece no rodapé do Perfil e no `/api/health`. NENHUMA avaliação funcional
  vale sem o carimbo conferido no aparelho. Atual: **F9-20260709-8**.
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
  4. Novo pedido do Alex (com mocks `dois-apps-em-um.html` e
     `modo-operador.html` anexados): cores dos gráficos erradas no Modo
     Operador, fraseologia não acompanha a identidade, Radar sem "análise
     inicial rápida", "Plano da mesa (IA)" não achava o modelo, nova feature
     de guardar todas as análises pra medir eficiência depois, e "desenhar o
     prompt como especialista no Claude". **qa/29** resolveu os dois
     primeiros itens funcionais (cores + modelo não encontrado).
  5. Feature de eficiência modelada com o Alex via AskUserQuestion
     (**qa/30**: autoavaliação da IA e trades reais são features SEPARADAS;
     prazo fixo de 10 pregões; N1+N2 alimentam a estatística; job no
     servidor) e a Fase A (autoavaliação da IA) **implementada e testada**
     (**qa/31**): novo módulo `analysis_outcomes.py`, captura em N1/N2, job
     diário no scheduler existente, painel "Eficiência da IA" em Perfil →
     Observabilidade. Fase B (trades reais) segue não iniciada.
  6. Novo pedido do Alex, usando a persona "Apple Product Engineer Sênior"
     (rascunhada em outra sessão) como lente de rigor (**qa/32**): (a)
     página intermediária de login CORRIGIDA — sessão restaurada fecha o
     portão sozinha, sem exigir toque em "Entrar"; (b) cópia "e-mail oculto"
     como título CORRIGIDA (agora "Sua conta Apple"); (c) causa-raiz real de
     "paletas iguais" encontrada — `MODE_OPERADOR.light` não tinha NENHUMA
     diferenciação de fundo/texto/bordas, só acento — CORRIGIDO. (d)
     Validação + propostas (AINDA NÃO IMPLEMENTADAS, aguardando decisão do
     Alex): reorganizar o Perfil em áreas dedicadas (o mapeamento mostrou
     que "Conta & preferências" hoje empilha 7 seções distintas), redesenho
     do badge "MODO OPERADOR" no header, e quanto mais diferenciar as
     paletas além do chrome já corrigido.

## 2. PENDÊNCIAS — o que ainda NÃO foi validado (fonte: `qa/26-matriz-revalidacao.md`)

- **A · Notificações (A1–A6):** ✅ CONFIRMADO funcionando no aparelho após
  qa/28 (build F9-20260709-5). Falta só reconfirmar A5/A6 (push remoto)
  formalmente — dependem das envs APNs no Railway (`APNS_SANDBOX=1`).
- **B · Identidade/Modo Operador (B1–B7):** ⏳ PARCIAL. qa/29 corrigiu as
  cores dos gráficos (sparkline + Patrimônio Simulado) que ficavam azuis no
  Modo Operador — falta confirmação no aparelho com build F9-20260709-6.
  Fraseologia (copy.js) ainda sem auditoria completa contra os mocks. Os
  guardiões de tema (`test_copy_theme.mjs`, `test_modo_operador.mjs`,
  `test_chart_colors_theme_aware.mjs`) passam no repositório.
- **C · IA nas duas vozes (C1–C5):** não testado nesta rodada.
- **D · Conta/Login (D1–D4):** não testado nesta rodada.
- **E · Plataforma (E1–E4):** não testado nesta rodada.

**Fora da matriz, do pedido mais recente do Alex (mocks anexados):**
- ✅ "Plano da mesa (IA)" não achava o modelo LLM — corrigido em qa/29
  (`persistence.js` `scanDeep()` não mandava `config`/BYOK pro servidor).
  Falta confirmação no aparelho.
- ⏳ Radar sem "análise inicial rápida" — não investigado ainda.
- ⏳ "Desenhar o prompt como especialista no Claude" — escopo não confirmado
  com o Alex (provável: revisar `skill`/`skillOperador` em `llm.py`/config).
- ✅ Nova feature (eficiência das análises) — modelada em qa/30, Fase A
  (autoavaliação da IA) IMPLEMENTADA em qa/31 (código pronto, testado,
  aguardando confirmação no aparelho com F9-20260709-7; validação real do
  job de avaliação só depois de ~10 pregões). Fase B (trades reais, mock
  `modo-operador.html` tela 4) ainda NÃO iniciada.

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
- **F9 (qa/29)**: pedido do Alex com mocks (`dois-apps-em-um.html`,
  `modo-operador.html`) — 2 de 5 itens resolvidos: (1) `OpsSparkline` e
  `CapitalCurve` em `App.jsx` usavam `T.x` (var() cru) em `fill=`/`stroke=`
  SVG, mesma classe de bug do `PriceChart` antigo — agora os 3 usam
  `usePalette()`. (2) `persistence.js` `scanDeep()` era a única chamada de
  IA que não mandava `config` (BYOK/modelo do aparelho) pro servidor —
  corrigido para mandar igual `analyze()`/`analyzeStopAlvo()`. Guardiões:
  `test_chart_colors_theme_aware.mjs`, `test_scandeep_config.mjs`. Build
  F9-20260709-6. Restam: fraseologia (copy.js), Radar sem análise inicial
  rápida, redesenho do prompt, feature de guardar análises p/ eficiência.
- **F9 (qa/30)**: modelagem da feature de eficiência com o Alex
  (AskUserQuestion) — duas features SEPARADAS (autoavaliação da IA × trades
  reais), prazo fixo de 10 pregões, N1+N2 alimentam a estatística, job no
  servidor reaproveitando o scheduler do Radar diário. Design doc, nada
  implementado ainda nesta etapa.
- **F9 (qa/31)**: Fase A (autoavaliação da IA) IMPLEMENTADA. Novo módulo
  `server/app/analysis_outcomes.py` (registro, avaliação pura, métricas, job
  diário); captura best-effort em N1 (`scan_deep_run`) e N2
  (`analyze_technical_model`); endpoints
  `/api/analysis-outcomes`+`/stats`; painel "Eficiência da IA" em Perfil →
  Observabilidade. Guardiões: `test_analysis_outcomes.py` (13 casos),
  `test_analysis_outcomes_ui.mjs` (4 casos). Build F9-20260709-7. Fase B
  (trades reais) segue não iniciada.

## 5. Prompt pronto para o novo chat

```
Contexto: leia CHECKOUT-NOVO-CHAT.md, qa/26-matriz-revalidacao.md, qa/27,
qa/28, qa/29, qa/30, qa/31 e qa/32 na raiz do repo b3-agente. Regras do
projeto valem (baseline verde, causa-raiz, guardião por bug, carimbo de
build antes de qualquer avaliação, docs em qa/). Se uma chamada nativa de
plugin "trava" sem erro, ver armadilha #8 antes de suspeitar de cache/build.

Estado: build F9-20260709-8 instalado e confirmado no rodapé do Perfil.
[SE NÃO: rode 'bash entregar.sh "retomada"' + Xcode ⇧⌘K + Run primeiro.]

Item A (notificações/push): CONFIRMADO OK pelo usuário.
qa/29: cores dos gráficos no Modo Operador + "Plano da mesa" sem modelo —
CORRIGIDOS, aguardando confirmação no aparelho.
qa/31: Fase A da eficiência da IA (autoavaliação, painel em Observabilidade)
IMPLEMENTADA E TESTADA, aguardando confirmação no aparelho — o job de
avaliação só produz resultado depois de ~10 pregões, então "nº de avaliadas
> 0" só é verificável daqui a 2 semanas, não agora.
qa/32: página intermediária de login, cópia "e-mail oculto" e paleta light
do Operador — CORRIGIDOS, aguardando confirmação no aparelho. Propostas de
badge/paleta-avançada/reorganização do Perfil em áreas dedicadas — decisão
do Alex ainda pendente (ver qa/32 seção 8 e o chat onde foram propostas).

Resultado no aparelho (cores certas? plano da mesa roda? painel Eficiência
da IA aparece? login sem tela intermediária? paleta light diferenciada?) +
item B(resto)/C/D/E da matriz qa/26:
- <liste aqui APENAS as falhas, ex.: B2 FALHA — sparkline continua azul>
- <...>

Ainda pendentes do pedido anterior do Alex (não iniciados): decisão sobre
as propostas de UX do qa/32 (badge, paleta avançada, reorg do Perfil em 5
áreas), Fase B da eficiência (trades reais, mock modo-operador.html tela 4
— modelo já em qa/30 seção B), fraseologia não acompanha a identidade
(auditar copy.js contra os mocks), Radar sem "análise inicial rápida",
"desenhar o prompt como especialista no Claude" (escopo não confirmado).

Tarefa: para cada falha, diagnostique a causa-raiz (Logs do servidor,
Diagnóstico do app, console do Web Inspector se algo travar sem erro claro),
corrija cirurgicamente com teste-guardião, rode as suítes completas e feche
com qa/32 + roteiro de hard stop. Ao final, rode
'bash entregar.sh --so-verificar' e me passe o novo carimbo.
```
