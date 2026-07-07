# B3 Agente — mesa de operações educacional (paper trading)

Simulador **educacional** de operações na B3. Dinheiro é **simulado**; apenas as
**cotações são reais** (Yahoo Finance). A leitura técnica de cada ativo é feita
**pela LLM que você configurar**, sob demanda. Nada aqui é recomendação de
investimento e o app nunca promete lucro.

- **Web (PWA)** — React + Vite.
- **iPhone** — o mesmo app empacotado com Capacitor (nativo).
- **Backend** — **FastAPI + SQLite** (Python): cotações, análise da LLM e
  persistência da versão web.

---










## Endereçamento mobile + B1 implementada

- **Mobile/endereço do backend**: o cliente HTTP exige **base absoluta no app**
  (caminho relativo iria para o próprio app → HTML → "não veio em JSON"). Sem
  endereço, falha com instrução clara (Perfil → Conta & preferências). "Testar
  conexão" detecta resposta não-JSON. Web inalterada.
- **B1**: `equitySnapshots` nos dois stores; 1 snapshot/dia ao abrir (sobrescreve).
  Home Evolução com curva real, retorno acumulado e drawdown. Rota POST /api/snapshot.

## Redesign de layout (Parte 1) + Fatos relevantes (Parte 2)

- **Navegação por ícones** (linha) com rótulo curto, alvos ≥44px.
- **Divulgação progressiva** para acabar com a rolagem longa: Histórico virou
  drill-down dentro de **Carteira** (botão "Ver histórico"); **Perfil** virou um
  hub raso que entra em "Conta & preferências" (Config) e "Agente autônomo" em
  telas focadas (com voltar). Cada tela tem um objetivo. Nada de empilhar telas.
- **Análise do ativo** agora inclui um bloco separado **Fatos relevantes /
  contexto** (notícias, resultados, eventos corporativos), com guardrail
  (informação, não recomendação) e aviso de completude/atualidade. Backend
  retrocompatível: backend antigo sem o campo => bloco simplesmente não aparece.

## Fase A — navegação centrada em progresso

- **4 abas**: **Evolução** (nova home — o app abre aqui), **Mercado** (watchlist +
  análise + indicadores), **Carteira** (curva de capital + posições + caixa + P&L +
  histórico), **Perfil** (agente + perfil do operador + IA/skill + tema +
  notificações). Histórico e Agente foram preservados, agrupados em Carteira e
  Perfil respectivamente — nenhuma funcionalidade removida.
- **Home Evolução**: curva de capital (placeholder na Fase A — patrimônio e retorno
  vs. orçamento já reais; a série diária chega na Fase B1), **streak** de
  consistência (dias seguidos, intrínseco, sem push), **card do Coach** (insight do
  dia, determinístico nesta fase), **desafio da semana** (meta de comportamento) e
  atalhos. Tom calmo/encorajador, enquadrando progresso como aprendizado.
- **Onboarding curtíssimo**: nome + orçamento + perfil de risco → cai na Evolução
  com a curva vazia e a promessa de retorno. Flag `onboarded` lida do STORE.
- **Streak** persistido em `config.streak` (dias seguidos), nos dois stores.

> Próximas fases (na ordem do brief): **B1** snapshot diário de patrimônio
> (`equitySnapshots`, curva real) — parar e testar; **B2** métricas comportamentais
> determinísticas (offline); **B3/C** coach com IA retrospectivo (1x/dia, BYOK).

## Logs do iOS: o que é ruído e o que importa

Ao rodar no iPhone, o console mostra várias linhas que **não são erros do app** —
são logs normais do iOS/Capacitor/WebKit. Se aparecer `⚡️ WebView loaded` e as
chamadas `To Native → … / TO JS {}`, o app subiu corretamente.

Ruído benigno (pode ignorar):
- `Reading from public effective user settings.`
- `Could not create a sandbox extension for '…/App.app'`
- `Unable to hide query parameters from script (missing data)`
- `xpc_user_sessions_get_foreground_uid() failed … Operation not permitted`
- `Loading app at capacitor://localhost…`

Aviso com ação **futura** (não quebra nada hoje):
- `UIScene lifecycle will soon be required…` — a Apple vai exigir o `UISceneDelegate`.
  O template iOS do Capacitor ainda usa `AppDelegate`. Modernização do projeto
  nativo (ver backlog). Erros reais do app aparecem como exceção JS/stack trace ou
  como resposta HTTP de erro (ex.: `TO JS {"status":404,…}`), não como esses logs.

## Cadastro de ativo, boas-vindas/logo e notificações

- **Bug do cadastro corrigido**: a entrada é normalizada (sem espaços, MAIÚSCULAS,
  sem `.SA`), o sufixo `.SA` é aplicado uma única vez e a existência é confirmada
  pelo **Yahoo Finance** (a IA não decide). Agora distinguimos **"não encontrado"**
  (404) de **"serviço indisponível/limite do Yahoo"** (503) — antes um 429 do Yahoo
  aparecia como "ticker inexistente" mesmo para ativos válidos. Lógica testável em
  `server/app/tickers.py` com testes (`tests/test_tickers.py`).
- **Tela de boas-vindas + logo**: `LogoMark` (candles âmbar + fita sobre fundo
  escuro, legível em tamanho de ícone) no Topbar, no onboarding e no "Sobre". O
  onboarding apresenta a proposta (dados reais + dinheiro simulado + IA, uso
  educacional), captura o nome e é reacessível em Config → "Tela de boas-vindas".

### Notificações: LOCAIS agora, PUSH no backlog

- **Implementado agora — notificações LOCAIS** (disparadas pelo próprio app, em
  uso/background): stop acionado, alvo atingido, operação do agente e movimento
  forte (±5%) de uma posição. Nativo via `@capacitor/local-notifications`; web via
  Notification API (`web/src/notify.js`). Boas práticas iOS: permissão pedida no
  **momento certo** (ao ativar na Config, não "de cara"), conteúdo curto/acionável,
  e liga/desliga por tipo na Config (preferências persistidas em `config.notif`).
- **Backlog — PUSH com o app fechado**: exige **APNs + servidor de push + build
  nativo** (e, no Android, FCM). Não está implementado nesta fase; as notificações
  locais cobrem os eventos acima sem depender de servidor.

> Após esta versão: rode `npm install` (nova dependência `@capacitor/local-notifications`)
> e recompile o iOS (`bash scripts/setup-ios.sh`) para o `cap sync` registrar o plugin.

## Ajustes de UX/Design (tema, nome, disclaimer único)

- **Tela inicial**: "Atualizar cotações" e "Editar watchlist" viraram ícones
  discretos no cabeçalho (↻ e ✎), com **pull-to-refresh** no mobile (puxe a
  lista para atualizar). Os cards de ativo ganham protagonismo.
- **Tema claro/escuro** (Config → Personalização): Claro · Escuro · Sistema
  (segue o iPhone). Implementado com **variáveis CSS semânticas** por tema;
  gráficos (canvas/SVG) recebem a paleta real via contexto. Persistente
  (config no backend + espelho em localStorage para evitar flash no boot).
- **Nome do usuário** (Config → Personalização): persistente; usado de forma
  sóbria (saudação no topo e onboarding).
- **Disclaimer concentrado**: deixou de se repetir em cada card. Agora vive em
  **um ponto único** — onboarding na 1ª abertura + item permanente
  "Sobre · Aviso legal" no rodapé da Config (modal com o texto completo).
  Junto ao conteúdo de IA fica só um **marcador mínimo** (ⓘ educacional).
- **Carteira**: stop/alvo propostos pela IA por perfil — se o ativo ainda não
  foi analisado, há um botão "Pedir à IA um stop e alvo para o seu perfil";
  a sugestão mostra o **raciocínio** (resumo por perfil) e o botão "Aplicar".

## Correções (formatação + candles)

- **Análise renderizada (não crua)**: o corpo vem em markdown limpo (o backend
  remove cercas ```), e o app o renderiza com um componente próprio (títulos,
  **negrito**, listas, ênfase) em React/DOM — nativo na WebView, sem HTML cru.
  KPIs em destaque no topo do card; corpo logo abaixo. Observação: o conteúdo
  rico depende do **backend novo no Railway** — com o backend antigo (campo
  `analysis`, texto plano) o app mostra o texto, mas sem estrutura para formatar.
- **Candles saneados**: OHLC validado antes de desenhar — 0/null tratados como
  ausentes, pregão do dia em aberto vira doji do fechamento, e outliers (vs.
  mediana e vizinho) são descartados para não esticar o eixo. A escala enquadra
  min/max reais (nunca força zero). Saneamento no backend (testado em pytest) e
  também no gráfico.

## Correções desta versão

- **Análise da IA robusta no mobile**: o cliente lê a resposta de forma
  tolerante (sem deixar o `.json()` do WebView quebrar), o backend sempre
  devolve a mesma estrutura com um corpo em **markdown** (validado/normalizado
  no servidor) e o app renderiza markdown de forma nativa (sem HTML cru).
  Timeout da análise ampliado (a IA demora) com mensagem amigável; preço
  ausente mostra estado claro sem travar.
- **Candles corrigidos**: o gráfico (lightweight-charts, padrão de mercado)
  recebe OHLC completo e saneado por vela (sintetiza doji quando falta dado),
  mantendo stop/alvo/preço atual e zoom/pan.
- **Intervalo do agente**: no modo autônomo, há intervalo configurável
  (5/10/15/30/60 min) que **de fato** governa a frequência do ciclo automático
  (timer enquanto o app está aberto). Persistente.

## Destaques desta refatoração

- **Análise da IA só no card**: o botão e o resultado vivem no card do ativo, em
  área que expande/recolhe. A janela de indicadores não tem mais IA.
- **Análise formatada**: a IA responde em JSON estruturado (KPIs + resumo +
  listas de confirmações/invalidações/cuidados + stop/alvo sugeridos). A
  renderização é feita em React puro (sem HTML injetado — XSS-safe).
- **Gráfico de candles**: o gráfico principal agora é candlestick (OHLC real do
  Yahoo), com linhas de stop/alvo/preço atual, zoom/pan por gesto e crosshair.
- **Perfil do operador (Config)**: risco, horizonte, tolerância de perda (%),
  objetivo e experiência. Persistente e injetado no prompt — a IA adapta a
  recomendação e o stop/alvo ao perfil.
- **Stop/alvo sugeridos na carteira**: por perfil + dados reais, com botão
  *Aplicar* e aviso de que são sugestões educacionais.
- **Watchlist editável por digitação**: digite um ticker; a existência na B3 é
  confirmada pelo **Yahoo Finance** (`.SA`), não pela IA. O ativo custom fica
  salvo e passa a valer em cotações, gráfico, análise e compra.

## 1. KPIs executivos no card (vindos da LLM)

Ao analisar um ativo, a LLM devolve **campos estruturados (JSON)** que viram 4
KPIs escaneáveis no card:

| KPI | Valores |
|---|---|
| **Direção mais provável** | Alta (verde) / Baixa (rosa) / Lateral (âmbar) |
| **Grau de convicção** | Muito Alto / Alto / Médio / Baixo |
| **Qualidade da oportunidade** | Excelente / Boa / Regular / Ruim |
| **Recomendação executiva** | Comprar / Comprar parcialmente / Aguardar / Realizar lucro / Reduzir exposição / Vender |

A **recomendação executiva** é a protagonista (faixa colorida no topo); os outros
três são chips de apoio. O texto completo fica sob **"Ver análise da IA"**
(progressive disclosure). Se o modelo não devolver o JSON no formato, os chips
não aparecem — o texto continua funcionando. Parser e normalização (acentos/
caixa) têm teste em `tests/test_kpi.py`.

---

## 2. Persistência

### Web -> servidor (SQLite, caminho absoluto estável)
A versão web persiste em **SQLite**, em caminho **absoluto e estável**, o mesmo de
qualquer diretório de onde você inicie o app:

- Padrão: `server/data/b3_agente.db` (derivado da localização do código, não do
  `cwd`).
- Override opcional: variável de ambiente `B3_DB_PATH`.

Tudo sobrevive a reinício: provedor/modelo/base_url/origem-da-chave, skill,
watchlist, carteira e histórico. Ao reabrir a aba **Config**, os campos
reaparecem preenchidos. A **chave da API nunca é reexibida** — no lugar aparece o
indicador **"chave configurada ✅"**.

**Prova (pytest):** `tests/test_persistence.py` salva a config -> **fecha e recria
a conexão** (simula o reinício) -> relê -> confirma que os valores voltaram. Há o
mesmo teste para a **watchlist** e para carteira/histórico, mais um teste de que o
caminho do banco é absoluto e independe do `cwd`.

```bash
bash scripts/test.sh        # ou, dentro de server/: pytest -q
```

### iPhone -> no próprio aparelho (handset)
No app nativo a **fonte da verdade é o aparelho**: todo o estado (config + chave,
skill, watchlist, carteira, histórico, agente) é salvo no armazenamento do WebView (no próprio iPhone). O servidor é usado apenas para
**cotações** e **análise** — e, para analisar, o aparelho envia a config + chave no
corpo da requisição. Assim seus dados continuam no telefone mesmo sem o Mac por
perto. A escolha de backend é automática (`Capacitor.isNativePlatform()`), em
`web/src/persistence.js`.

---

## 3. Layout mobile

A barra de navegação inferior fica **fixa no rodapé** (sempre visível, sem
scroll), respeitando a *safe area* (notch/home indicator). Só a área central
rola; cabeçalho e navegação ficam fixos. O contêiner usa `100dvh` com
`box-sizing: border-box`, então o respiro do notch é contado **dentro** da altura
da tela — nada fica escondido atrás da barra.

---

## 4. Estrutura

```
b3-agente/
├─ server/                 # backend FastAPI (Python)
│  ├─ app/
│  │  ├─ main.py           # rotas FastAPI + serve o web em producao
│  │  ├─ db.py             # SQLite (caminho absoluto estavel)
│  │  ├─ store.py          # estado sobre o kv store
│  │  ├─ yahoo.py          # cotacoes/historico (httpx, mitigacao 429)
│  │  ├─ llm.py            # provedores + KPIs estruturados
│  │  ├─ kpi.py            # parser dos KPIs (puro/testavel)
│  │  ├─ catalog.py        # 20 blue chips
│  │  └─ defaults.py       # estado inicial + skill padrao
│  ├─ tests/               # pytest (persistencia + KPIs)
│  ├─ requirements.txt
│  └─ pytest.ini
├─ web/                    # React + Vite + Capacitor
│  └─ src/
│     ├─ App.jsx           # UI (cards, KPIs, abas, polimento)
│     ├─ persistence.js    # web=servidor | iPhone=aparelho
│     ├─ catalog.js        # catalogo/estado padrao embutidos (offline no iOS)
│     └─ api.js            # chamadas HTTP ao backend
└─ scripts/                # setup / run / test / build iOS
```

---

## 5. Pré-requisitos

- **Python 3.9+** (recomendado 3.10+)
- **Node 22+** e **npm** (para o app web/iOS)
- Para iOS: **macOS + Xcode 26+**

---

## 6. Instalação e execução

```bash
# 1) instala backend (venv) e web
bash scripts/setup.sh

# 2a) desenvolvimento: backend (8787) + Vite (5173)
bash scripts/run.sh

# 2b) producao: build do web + 1 servidor servindo tudo
bash scripts/run.sh --prod

# testes
bash scripts/test.sh
```

A chave/origem da chave da LLM é definida na aba **Config**. Para usar variável de
ambiente, exporte antes de subir o backend (ex.: `ANTHROPIC_API_KEY`,
`OPENAI_API_KEY`, `GEMINI_API_KEY`, ou a genérica `B3_AGENTE_API_KEY`).

---

## 7. PyCharm

1. **Abra a pasta `b3-agente`** (ou `server/`) como projeto.
2. **Interpretador**: Settings -> Project -> Python Interpreter -> *Add* ->
   *Existing environment* -> selecione `server/.venv/bin/python`.
3. **Run config — servidor** (uvicorn): *Add New Configuration* -> *Python*:
   - *module name*: `uvicorn`
   - *parameters*: `app.main:app --host 0.0.0.0 --port 8787 --reload`
   - *working directory*: `.../b3-agente/server`
4. **Run config — testes**: *Add New Configuration* -> *pytest*:
   - *target*: `tests`
   - *working directory*: `.../b3-agente/server`

> O `pytest.ini` já define `pythonpath = .`, então o pacote `app` é encontrado a
> partir de `server/`.

---

## 8. App no iPhone

```bash
# descubra o IP do Mac na rede Wi-Fi
ipconfig getifaddr en0          # ex.: 192.168.0.12

# suba o backend acessível na LAN
bash scripts/run.sh --prod

# em outro terminal: builda o web e abre o projeto iOS no Xcode
bash scripts/setup-ios.sh --api-base http://192.168.0.12:8787
```

No Xcode, selecione seu iPhone e *Run*. O app passa a guardar tudo **no próprio
aparelho** e só busca cotações/análise no Mac.

O endereço do Mac pode ser definido (e trocado) **dentro do app**, na aba
**Config → "Servidor do app (Mac)"** — útil quando o IP muda de rede, sem precisar
recompilar. O `--api-base` no build apenas define um valor inicial.

Tudo que você gera usando o app (config, watchlist, carteira, histórico e as
**análises da IA** por ativo) fica salvo no aparelho e reaparece ao reabrir.

> **Atualizou o código?** Refaça o build do app no iPhone para o aparelho receber
> a versão nova: rode `bash scripts/setup-ios.sh --api-base http://SEU_IP:8787`
> de novo (ele faz `npm run build` + `cap sync ios`) e *Run* no Xcode. Sem isso,
> o iPhone continua executando o pacote antigo.

### Não conecta? (erro -1004 / "Could not connect")
- **iPhone e Mac na MESMA rede Wi-Fi** (o celular **não** pode estar no 4G/5G).
- Confirme o backend: `curl http://SEU_IP:8787/api/health` deve responder
  `{"ok":true}`.
- Use o **IP da LAN** (192.168.x.x), não `localhost`.
- macOS pode pedir permissão de **firewall** na primeira execução — autorize.
- Redes públicas/convidado às vezes isolam dispositivos (*AP isolation*) — use uma
  rede doméstica.
- O `setup-ios.sh` já libera HTTP local no `Info.plist` (ATS) via
  `ios-allow-http.sh`.

---

## 8.1. Servidor na nuvem (opcional) — usar de qualquer rede

Para não depender de estar na mesma Wi‑Fi do Mac, publique o backend no Railway
(URL pública HTTPS) e aponte o app para lá em **Config → Servidor do app**. Passo
a passo em **`DEPLOY_RAILWAY.md`**.

## 8.2. Análise técnica do ativo (pop-up interativo)

Toque em um **card de ativo** para abrir um **bottom sheet** (arrastável para
fechar) com:

- **Gráfico interativo** (lightweight-charts, da TradingView): **pinça para zoom**,
  **arrastar para navegar no tempo**, **crosshair** ao tocar (preço/data), e linhas
  de **preço atual, preço médio, stop e alvo** rotuladas. Atalhos de período
  **1S / 1M / 3M / 1A** e alternância de **SMA 20/50, Bollinger e Volume**.
- **RSI (14)** e **MACD (12,26,9)** logo abaixo, sincronizados com o trecho visível.
- A **análise textual completa da IA** e o painel de **indicadores** (valores atuais).

Os dados vêm do Yahoo Finance (1 ano contínuo, com warmup para as médias longas)
e ficam **armazenados no aparelho** (cache). Sem servidor disponível, a janela abre
com **dados de exemplo** (protótipo navegável) para iterar o layout.

## 9. Enquadramento educacional

Conteúdo **educacional**, dinheiro **simulado**. As análises são uma leitura
técnica gerada por IA, **não** recomendação de investimento, e o app **nunca**
promete lucro.

## Modelo freemium (estrutura — sem cobrança nesta versão)

O app já roda **100% gratuito**. A base para um futuro freemium está pronta, mas
**nada cobra ou bloqueia hoje**. Pilar de custo: **BYOK** — o usuário pluga a
própria chave de LLM em *Config → Modelo de IA* (primeira classe), o que mantém o
custo de inferência fora do app e viabiliza um tier gratuito generoso.

**Ganchos já marcados no código** (todos liberando tudo hoje):

- `server/app/plan.py` e `web/src/plan.js` — espelhados: `PLAN_FREE`/`PLAN_PRO`,
  `can_add_ticker` / `canAddTicker`, `can_analyze` / `canAnalyze`,
  `requires_subscription` / `requiresSubscription`. Limites = `None`/`null`.
- **Gate de nº de ativos**: `POST /api/watchlist/add` (backend) e `A.addTicker`
  (front) chamam o hook antes de adicionar — hoje sempre permite.
- **Gate de nº de análises/mês**: `POST /api/analyze` (backend) e `A.analyze`
  (front) chamam o hook — hoje sempre permite (contador do mês é TODO).
- **Gate de assinatura**: `requires_subscription(feature)` — ponto único para,
  no futuro, exigir plano pago em recursos premium (ex.: agente autônomo,
  análises ilimitadas). Deve validar **recibo da loja no servidor**, nunca só no
  cliente.

Quando a monetização entrar, basta preencher os limites em `PLAN_FREE`, resolver
`current_plan(user)` pelo recibo validado e devolver `402`/upsell nos gates.

## Backlog de publicação (fase posterior — ainda não implementada)

- [ ] **Conta Apple Developer** (US$ 99/ano) e App Store Connect; equivalente
      Google Play Console para Android.
- [ ] **Build de produção** (EAS Build / `eas build`, ou Xcode Archive direto via
      Capacitor) para iOS e Android.
- [ ] **Ícones e splash** em todas as resoluções (app icon, launch screen).
- [ ] **Onboarding** curto no primeiro uso: explicar simulação, BYOK e perfil.
- [ ] **Política de privacidade e Termos de uso** (URLs públicas), exigidos pelas
      lojas; descrever uso de dados, a chave BYOK (armazenada só no dispositivo) e
      a origem das cotações (Yahoo Finance).
- [ ] **Disclaimers jurídicos** revisados por especialista: simulador
      educacional, sem recomendação de investimento, dinheiro simulado, dados
      podem atrasar/conter erros. (Textos centralizados em `web/src/disclaimers.js`.)
- [ ] **Adotar `UISceneDelegate`** no projeto iOS (Info.plist `UIApplicationSceneManifest` + SceneDelegate), conforme aviso de depreciação da Apple.
- [ ] **Notificações PUSH (app fechado)**: APNs (iOS) + FCM (Android) + servidor de push; ligar nos mesmos eventos das notificações locais.
- [ ] **Fluxo de assinatura (IAP)**: produtos na loja, paywall, restauração de
      compras e **validação de recibo no servidor** (ligar nos ganchos de `plan`).
- [ ] **Conformidade**: rótulos de privacidade (App Privacy), classificação
      etária, e revisão das diretrizes de apps financeiros/educacionais.
