# Prompt: notificações push do Boris+ — ação, clareza, valores, log e horário

> Alvo: **Claude Code** neste repositório (`b3-agente`).
> Uso: cole o bloco abaixo como mensagem inicial. Ele já carrega as âncoras de
> código verificadas em 2026-08-24 — não precisa reinvestigar do zero, mas
> reconfira os `file:line` antes de editar (o `App.jsx` cresce e as linhas andam).

---

## Contexto

As notificações push do Boris+ têm cinco problemas relatados pelo Alex, todos
confirmados no código. Não é um defeito só: são seis causas distintas, e três
decisões de produto que continuam abertas.

O canal de saída é único — `push.send_to_user` (`server/app/push.py:171`), com
quatro call sites vivos:

| # | Origem | Evento | Título hoje |
|---|---|---|---|
| A | `agent.py:324` | kill-switch ligado em pregão (só admins) | `Kill-switch ligado há {h}h…` |
| B | `agent.py:1023` → `timing_watch.py:192-213` | condição/gatilho atingido | `{TICKER} · condição atingida na barra de {hora}` |
| C | `main.py:2760` | `POST /api/push/test` (smoke manual) | — |
| D | `main.py:2789` (`_notify`, injetado como `notify_push`) | funil genérico de 3 eventos | ver abaixo |

O funil **D** serve três eventos com títulos fixos:
`D1` Radar diário (`radar_daily.py:242`, `"Radar do dia 📡"`),
`D2` ordem pendente executada/cancelada (`agent.py:1224`),
`D3` stop/alvo/entrada do Operador (`agent.py:1261`) — os dois últimos com o
título literal `"Agente Boris+ (simulado)"`.

## Causas confirmadas, por sintoma

**S1 — o toque não leva a lugar nenhum.** O mecanismo de navegação existe e
funciona (`web/src/notify.js:374-393` → `web/src/App.jsx:7010-7036`: leva à aba
Mercado e rola até o card do ativo). Ele depende de `data.t` no payload, e
`notify.js:383` descarta em silêncio quando `t` está ausente ou não casa
`/^[A-Z]{4}\d{1,2}$/`. Só o call site **B com um único ativo**
(`agent.py:1013-1015`) preenche `t`. Todo push do Operador, do Radar, do
agregado de N ativos e do kill-switch abre o app sem destino. A closure
`_notify` (`main.py:2789`) nem sequer aceita `extra` na assinatura.
Também não há `aps.category` (`push.py:195-205`), então o banner não oferece
nenhuma ação direta.

**S2 — o marco não fica claro.** O evento estruturado existe no dict Python
(`kind`, `motivo`, `tag`), mas só `ev["text"]` viaja até o push
(`agent.py:1224`, `:1261`). O título vira o literal genérico
`"Agente Boris+ (simulado)"` e o marco real fica diluído no corpo.

**S3 — faltam valores.** Os pushes D2/D3 já trazem ticker, quantidade e preço
no texto (`agent.py:697-699`, `:884`; `pending_orders.py:289-290`). Os do
gatilho (B) e do Radar (D1) não trazem preço nenhum. Nenhum push traz P&L —
embora `store.sell` já calcule `pnl` (`server/app/store.py:650`), ele não entra
no evento (`agent.py:883-884`).

**S4 — não entra no log que o usuário vê.** Existem três estruturas que não
conversam: `history` (`store.py:590-695` → tela `HistoricoScreen`,
`App.jsx:3856`), `agent.events` (`store.py:806-810` → "Eventos e avisos
recentes", `App.jsx:4301-4309`) e `agentLog` (`store.py:946-951` → tela técnica
"Logs & Debug", `App.jsx:5171`). O gatilho (B), o Radar (D1) e o kill-switch (A)
não escrevem em `history` nem em `agent.events`. O único rastro do gatilho é a
linha de *entrega* em `agent.py:1034` ("Aviso enviado a 1/1 aparelho(s)"), que
registra o envio, não o evento de mercado. O Radar é fire-and-forget com
`except: pass` (`radar_daily.py:238-244`). Não existe lista de notificações
recebidas em lugar nenhum do app — a "central de notificações"
(`App.jsx:4333`, `NotifSection`) é central de *controle*, não de histórico.

**S5 — chegam fora do pregão.** A função canônica é
`pregao.in_market_hours()` (`server/app/pregao.py:124`, janela 10:00–16:55 BRT
com feriados). Os call sites A, B, D2 e D3 a respeitam. Duas classes escapam:

- O Radar (D1) usa `pregao.is_trading_day()` e não `in_market_hours`
  (`agent.py:1109`), com alvo `B3_RADAR_DAILY_HHMM` default `"08:45"`
  (`radar_daily.py:27`, `:51-60`) — dispara **1h15 antes da abertura**, para
  todos os tokens registrados (`radar_daily.py:185-195`). Isso é desenho
  deliberado, não acidente.
- As notificações **locais** do front (`App.jsx:7086`, `:7103`, `:7722-7744`)
  não têm nenhuma noção de horário. Não existe equivalente de `in_market_hours`
  em `web/src/` — o front recebe `pregaoAberto` via `/api/agent/status`
  (`agent.py:1309`) mas não consulta antes de notificar. O usuário não
  distingue local de APNs.

**Achado adicional (paridade, fora dos 5 sintomas).**
`serverStore.syncPushPrefs` (`web/src/persistence.js:153-161`) nunca é chamado,
e `App.jsx:4378` chama `store.registerPushToken(tk)` sem `extra` — no web
logado, ativar push não grava preferência alguma. No iOS o merge funciona
(`persistence.js:878-881`). As preferências server-side existem
(`push.PREFS_PADRAO`, `push.py:86`) mas têm um único campo booleano,
`gatilho` — só o call site B as respeita (`timing_watch.py:229`, `:269`).

## Decisões já fechadas

Trate como dadas, sem re-litigar:

1. O canal de saída continua sendo `push.send_to_user` — a correção enriquece o
   payload, não cria um segundo caminho de envio.
2. O texto visível ao usuário mora em `skill_ref.py` ↔ `copy.js` por modo
   (Estudo/Operador), nunca solto no componente. Se um texto novo entrar em
   `defaults.py`, a paridade byte a byte com `catalog.js` vale e o guardião
   trava.
3. Todo número exibido vem do motor determinístico. A IA não entra no caminho
   da notificação.
4. Nada de fabricar frescor: se o dado que embasa a notificação está atrasado ou
   ausente, a notificação diz isso ou não é enviada.

## Decisões abertas — pergunte ao Alex, não assuma

Estas mudam o resultado e são dele:

1. **Radar às 08:45.** Manter o horário atual (útil como preparação para o
   pregão, e foi desenhado assim) ou mover para depois da abertura? Se manter,
   o texto passa a deixar explícito que é uma prévia pré-abertura.
2. **Granularidade da preferência.** Hoje há um único booleano `gatilho`. Vale
   abrir por classe de evento (execução de ordem, radar, gatilho, proteção)?
   Isso muda `PREFS_PADRAO` e o contrato de `register-token`.
3. **Central de notificações recebidas.** Uma tela nova listando o que chegou é
   escopo de fase, não de quick task. Se o Alex quiser, promova; se não, o
   registro no log existente (`agent.events`) já fecha o S4.

Faça essas três perguntas antes de planejar, e registre as respostas em
CONTEXT.md como decisões travadas.

## Escopo e critério de aceite

Entregue o subconjunto determinístico, com critério verificável para cada item:

| # | Correção | Pronto quando |
|---|---|---|
| 1 | `_notify` (`main.py:2789`) passa a aceitar e repassar `extra` | Um push de execução do Operador chega com `data.t` preenchido e o toque leva ao card do ativo |
| 2 | Título carrega o marco real, vindo do `kind`/`motivo` que já existe no evento | Nenhum push do Operador sai com o título literal `"Agente Boris+ (simulado)"`; teste cobre stop, alvo e entrada |
| 3 | P&L entra no evento de venda (`agent.py:883-884` lê o `pnl` que `store.py:650` já calcula) | Push de stop/alvo mostra o resultado da operação; a origem do número é o motor, não recomposição no texto |
| 4 | Gatilho (B) e Radar (D1) passam a registrar o evento de mercado em `agent.events` | O evento aparece em "Eventos e avisos recentes" (`App.jsx:4301`) depois do push, não só a linha de entrega em `agent.py:1034` |
| 5 | Notificações locais do front respeitam o horário de pregão | `App.jsx:7722-7744` consulta o estado de pregão que o app já recebe via `/api/agent/status`; guardião de teste cobre o caso "mercado fechado, cotação stale" |
| 6 | Paridade do `syncPushPrefs` no web | Ativar push no web logado grava preferência, igual ao iOS; `test_api_parity.mjs` cobre |

Fora de escopo aqui: tela nova de central de notificações (decisão 3 acima) e
mudança do horário do Radar (decisão 1) — ambas dependem da resposta do Alex.

## Como conduzir

Este repositório trabalha por GSD. Comece por `/gsd-quick --discuss` — a flag
existe justamente para fechar as três decisões abertas antes de planejar. Se a
discussão promover a central de notificações a escopo real, pare e proponha uma
fase em vez de esticar o quick task.

Entregue no escopo acordado. Decida sozinho o rotineiro; se discordar de algum
item, diga em uma frase e siga.

## Verificação

- `bash scripts/executar.sh --testes` verde (as duas suítes — pytest do backend
  e `web/tests/*.mjs`; `scripts/test.sh` sozinho é meia baseline).
- `npx vite build` verde para qualquer mudança em `web/src/`.
- Cada correção acima com teste que falharia antes dela.
- Publicação (`bump.sh` → `publicar-web.sh`, `cap sync ios`) é passo separado,
  disparado pelo Alex depois — não faz parte desta entrega.

Um push só é considerado corrigido depois de recebido de verdade num aparelho:
o texto certo, o toque levando ao lugar certo, e o evento visível no log do app.
Peça essa confirmação ao Alex ao fechar — os testes cobrem o payload, não a
entrega.
