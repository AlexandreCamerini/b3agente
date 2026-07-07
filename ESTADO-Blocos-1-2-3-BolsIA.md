# ESTADO — Blocos 1·2·3 (BolsIA / b3-agente)

Entrega com três blocos independentes. **Hard-stop entre blocos**: valide cada
checklist no device antes de considerar o bloco aceito.

---

## BLOCO 1 — Notificações iOS (entrega nativa confiável)

### O que foi encontrado (diagnóstico honesto)
O `notify.js` **já usava** `LocalNotifications.schedule({ at })` no caminho
nativo — o agendamento em si nunca foi por `setTimeout` no iPhone. Os defeitos
reais que faziam notificações "sumirem" eram três:

1. **Colisão de ids entre aberturas do app.** O contador de ids nascia em `1`
   a cada boot. No iOS, agendar com um id já pendente **substitui** o
   agendamento anterior sem erro — qualquer notificação nova "engolia" uma
   agendada na sessão anterior. → O contador agora persiste no
   `localStorage` (`b3-notify-nid`).
2. **`send()` com horário no passado.** A entrega imediata usava
   `at: agora+250ms`; se a ponte JS→nativo demorasse, o horário já tinha
   passado e o iOS **descartava** em silêncio. → Entrega imediata agora vai
   **sem** campo `schedule` (dispara na hora, sem corrida).
3. **`schedule()` sem clamp.** Horário ≤ agora era descartado. → Clamp para
   pelo menos `agora+1s`, e `allowWhileIdle: true` (Android; iOS ignora).

Novos utilitários: `notify.getPending()` (o que o **sistema** tem de fato
agendado) e `diag()` enriquecido com `pendingCount`/`pendingIds` — prova
objetiva de que o iOS aceitou o agendamento, independente do WebView.

Foreground preservado: `setForegroundHandler` → toast in-app continua; a
config `LocalNotifications.presentationOptions` do `capacitor.config.ts` já
cobre o banner nativo em primeiro plano após o `cap sync`.

### Limite honesto (importante)
Alertas de **stop/alvo/variação** são disparados por **condição de preço**,
verificada por um loop JS com o app aberto. Com o WebView suspenso, **ninguém
monitora o preço** — notificação local não resolve isso por definição (iOS só
agenda por horário). Entrega desses alertas com app em background exige **push
(APNs) com monitoramento no servidor** — segue no backlog de publicação. O que
este bloco garante: **qualquer notificação agendada por horário chega no
horário, com app em background ou fechado.**

### Passos no Mac
```bash
cd web && npm install && npm run build && npx cap sync ios
# abrir no Xcode e rebuild no device
```

### ✋ Hard-stop BLOCO 1 (device)
- [ ] Perfil → Config → Notificações: ligar; permissão pedida e concedida.
- [ ] No console do Safari (Develop → iPhone): `localStorage.setItem("b3-debug","1")`,
      recarregar, rodar `await notify.diag()` → `pluginLoaded:true`,
      `permission:"granted"`.
- [ ] Tocar **Testar agendamento (30s)** → `diag()` mostra `pendingCount ≥ 1`.
- [ ] Mandar o app para **segundo plano** → banner chega ~30s após o toque.
- [ ] Repetir o teste e **fechar o app** (swipe) → banner chega mesmo assim.
- [ ] Repetir o teste 2x seguidas na MESMA sessão e depois reabrir o app e
      testar de novo → todas chegam (ids não colidem entre sessões).
- [ ] Com o app **aberto**, teste imediato → toast in-app aparece na hora.

---

## BLOCO 2 — Welcome como portão de boot

### O que mudou
- A tela de boas-vindas renderiza **sempre no boot** (uma vez por abertura),
  independente de `config.onboarded` e de sessão ativa.
- **Com sessão restaurada** (`/auth/me` ok): mostra o cartão
  **“CONECTADO COMO X”** + botão **Entrar** (entra com o estado da conta).
- **Com token salvo mas `/auth/me` ainda pendente**: aviso
  “Restaurando sessão salva…” sobre o formulário; quando a resposta chega, a
  tela troca sozinha para o estado conectado.
- **Sem sessão**: fluxo atual de login/criar conta/“Usar sem conta”.
- `ctx.openWelcomeAuth` (atalho no Perfil) **preservado**.
- “Usar sem conta” só abre o onboarding anônimo (orçamento/risco) para quem
  **nunca** concluiu (`onboarded=false`); veterano entra direto — sem refazer
  onboarding a cada boot.
- `config.onboarded` **muda de papel**: deixa de esconder o welcome e passa a
  governar apenas o atalho do onboarding. `test_welcome.mjs` foi reescrito
  para o novo contrato (o antigo travava o comportamento anterior).
- Debug: `localStorage.setItem("b3-debug-welcome","1")` loga
  `{ bootGate, onboarded, hasSavedSession, willShow }` no boot.

### ✋ Hard-stop BLOCO 2 (device)
- [ ] Matar o app e reabrir **logado** → welcome aparece com “CONECTADO COMO X”;
      tocar **Entrar** → estado da conta restaurado normalmente.
- [ ] Matar e reabrir **anônimo já onboardado** → welcome aparece; “Usar sem
      conta” entra direto (NÃO refaz orçamento/risco).
- [ ] Instalação limpa (apagar app) → welcome; “Usar sem conta” → onboarding
      de orçamento/risco roda uma vez.
- [ ] Perfil → “Tela de boas-vindas” continua reabrindo o welcome.
- [ ] Device legado (dados antigos): abrir sem tela branca
      (`backfillStructural` coberto pela suíte).
- [ ] Modo avião com sessão salva: welcome mostra “Restaurando sessão…”, o
      formulário continua utilizável e o app não trava.

---

## BLOCO 3 — Radar de mercado (novo, aditivo)

### Servidor
- **`server/app/scanner.py`** (novo): varredura do universo com o **motor de
  sinais existente** (`indicators.compute`/`slice_tail` — nada duplicado).
  - Universo default: aproximação da composição do **IBOV** (~74 ativos),
    embutida e comentada (atualizar a cada rebalanceamento quadrimestral).
    Sobreponível **sem redeploy** por env `B3_SCAN_UNIVERSE="PETR4,VALE3,…"`
    ou por chamada via `?tickers=` (teto de 120 símbolos).
  - **Cache-first**: cada ativo passa pelo `candle_cache` (miss → série 2y;
    delta → só o recente com `merge_candles`; fresh <45s → zero rede).
  - **Fetch escalonado**: semáforo (4 simultâneos) + espaçamento mínimo de
    0,15s **apenas entre chamadas reais** ao Yahoo (anti-429).
  - **Período do usuário** via `candles.resolve_keep(period)` — nunca
    hardcoded; condições de “máxima/mínima do período” fazem o resultado
    mudar visivelmente ao trocar 1M/3M/6M/1A/2A.
  - Resultado da varredura cacheado por 60s por (período, universo).
  - Payload: `{ period, periodBars, universeSize, scanned, results:[{ticker,
    condicoes_detectadas[], score_tecnico, close, variacaoPeriodoPct, candles,
    cacheStatus}], errors[], disclaimer, timestamp }`. Símbolo com falha cai em
    `errors` sem derrubar a varredura.
  - **Guardrail**: rótulos descritivos/educacionais; o score é **INTENSIDADE
    de sinais** (quantas condições ativas), não direção nem recomendação —
    séries de queda pontuam igual. Teste automatizado bloqueia linguagem
    imperativa (“compre/venda/entre agora”) nos rótulos e no disclaimer.
- **`GET /api/scan?period=&tickers=`** no `main.py` (aditivo).

### Frontend
- Nova aba **Radar** na navegação (6 itens) + `RadarScreen`:
  lista rankeada com chips das condições, barra de “INTENSIDADE DE SINAIS”,
  preço/variação do período, badge **“PERÍODO EM USO: …”**, contagem
  varridos/erros, disclaimer visível (`DISCLAIMERS.radar`, novo na fonte
  única). Zero linguagem imperativa (coberto por teste).
- `candlePeriod` lido da config — **mesma config nos dois stores**.
- Invariante respeitada: `store.scan(period)` existe no `serverStore` **e** no
  `deviceStore` (mesma interface; a varredura roda sempre no servidor).
- `api.scan` com timeout de 120s (a 1ª varredura aquece o cache do universo).

### ✋ Hard-stop BLOCO 3 (device + web)
- [ ] Abrir a aba Radar → varredura completa **sem 429** (1ª vez pode levar
      até ~1 min; aviso na tela). Log do Railway sem rajada de erros Yahoo.
- [ ] Tocar ↻ em seguida → resposta em ≤2s (cache de 60s).
- [ ] Config → trocar período 1A → 1M → voltar ao Radar → badge muda e a
      lista/score muda (condições de máxima/mínima do período).
- [ ] Disclaimer visível no fim da lista; nenhuma frase imperativa.
- [ ] iPhone e web mostram o mesmo resultado (mesmo período configurado).
- [ ] (Opcional) Definir `B3_SCAN_UNIVERSE=PETR4,VALE3,ITUB4` no Railway →
      Radar passa a varrer só esses 3.

---

## Validação executada no sandbox (gate)

| Etapa | Resultado |
|---|---|
| `node /tmp/balance.js web/src/App.jsx` | balanceado |
| `node --check` (10 módulos planos) | ok |
| `py_compile server/app/*.py` | ok |
| Suítes web (7 × `.mjs`, incl. novas `test_radar` e `test_welcome` reescrita) | 7/7 |
| Suítes backend (15 arquivos; `test_scanner.py` novo) | 13 ok · 2 SKIP¹ |

¹ `test_llm_errors` e `test_options_provider_yahoo` pulam SÓ no sandbox por
falta de `httpx` (rede off) — mesmo comportamento das entregas anteriores;
passam no Railway. O `test_scanner.py` segue a convenção do repo (roda no
pytest **e** standalone via `python3 tests/test_scanner.py`).

## Invariantes conferidas
`persistence.js` apenas **estendido** (+2 métodos espelhados) · dois stores com
a **mesma interface** · motor de sinais **reutilizado**, separado dos preços ao
vivo · **nenhum output recomenda** compra/venda (guardrail testado) ·
disclaimers preservados e ampliados (`DISCLAIMERS.radar`) · BYOK intocado.

## Pendências que permanecem (inalteradas)
- Erro de SPM no Xcode (capacitor-swift-pm) — ordem de correção já mapeada.
- Railway: volume `/data` + `B3_DB_PATH` (lembrete das Fases 2/3).
- Login social nativo (plugins + Client IDs). Push/APNs para stop/alvo em
  background (novo item de backlog explicitado pelo Bloco 1).
- Intervalo semanal de candles; persistir candle_cache em SQLite.
