# Plano — Operador IA: separação Estudo/Operador e entrada automática

Spec de trabalho para execução no Claude Code. Origem: relato do Alex de
2026-08-07 ("ontem um stop foi atingido, porém a posição foi mantida") +
decisão de produto de separar Modo Estudo (só orienta) de Modo Operador
(executar ou informar), com config própria para entrada automática limitada a
% do caixa. Status: **aguardando aprovação**.

## 1. O bug relatado — diagnóstico

**Hipótese principal, já documentada no próprio código** ([agent.py:486-500](../server/app/agent.py:486)):
`serverEnabled` (Operador no servidor) e `mode` (executar/sinalizar) são
controles SEPARADOS. `/api/cycle` (app aberto) executa sem checar
`serverEnabled`; o laço do servidor (`scheduler_loop`, app fechado) só avalia
quem tem `serverEnabled=True` (`list_server_users`). Se o app estava fechado
quando o stop foi cruzado e `serverEnabled` estava desligado, ninguém avaliou
a posição naquele instante — a ordem só teria executado se o app estivesse
aberto no momento exato.

**Hipótese secundária, achada nesta investigação**: existe um segundo
interruptor legado, `agent.autonomous` ("Modo autônomo", card "Modo local (com
o app aberto)" na tela do Operador) — se só ele estava ligado (e não
`serverEnabled`), o efeito é o mesmo: proteção só com o app aberto.

**Ainda não confirmado** — três perguntas ao Alex, pendentes:
1. "Operador no servidor" estava LIGADO no momento?
2. O modo era mesmo "Executar", não "Apenas sinalizar"?
3. O app estava aberto ou fechado no telefone?

Este plano não depende da resposta para ser executado — a Fase A fecha a
lacuna estrutural (Modo Estudo nunca executa) e reduz a superfície do
problema, mas não é, sozinha, a causa provada do incidente de ontem. Se as
respostas apontarem outra causa (teto `maxOpsDia` atingido, falha de
cotação), tratamos à parte.

## 2. Decisões fechadas (aprovadas pelo Alex em 2026-08-07)

- **D1 — Migração de conta em Modo Estudo com `mode=executar` salvo**: o
  backend força `mode="sinalizar"` sempre que `appMode != "operador"`,
  silenciosamente. Não é preferência do usuário nesse caso — é trava.
- **D2 — Teto de operações da entrada automática**: soma no MESMO
  `maxOpsDia` que já existe para saída (não cria `maxEntradasDia`).
- **D3 — % do caixa para entrada automática**: configurável por conta, com
  teto absoluto fixo no backend (nunca aceita acima do teto, mesmo que o
  cliente tente mandar mais) — mesmo espírito de `MAX_ALVO_EXTENSOES` não ser
  configurável.
- **D4 — Reaproveitar `allocPct`** ("Alocação por operação", já existe no
  modelo de dados e na UI, 1–20%, default 5%) em vez de criar um campo novo.
  Hoje ele é decorativo (`agent_params()` nunca o lê) — este plano o conecta.
- **D5 — Só lado de COMPRA é executável automaticamente.** `store.py` só tem
  `buy`/`sell` (carteira SIMULADA, sem posição vendida/short). Um plano do
  Radar com `decisao == "VENDER"` (estudo de baixa) não tem como virar ordem
  automática — continua só informativo (push), em qualquer modo. A entrada
  automática se aplica exclusivamente a `decisao == "COMPRAR"`.
- **D6 — Fora de escopo**: não mexo no par `autonomous`/"Modo local" (achado
  2, seção 1) nem faço limpeza geral da tela do Operador — fica registrado
  como pendência separada, não deste plano.

## 3. O que existe hoje (mapa, para não redescobrir)

| Peça | Onde | O que faz |
|---|---|---|
| Ciclo de saída (stop/alvo/trailing) | `agent.py:341-461` (`run_cycle_for`/`_run_cycle_inner`) | Por posição aberta, avalia `breach_stop`/`hit_alvo` contra cotação quase-real (`quotes_getter`); executa `store.sell` se `mode=="executar"` |
| Laço do servidor | `agent.py:592-696` (`scheduler_loop`) | A cada `intervalMin`, roda o ciclo de quem tem `serverEnabled=True`; dispara push só quando `executed>0` |
| Aviso de entrada (push) | `timing_watch.py` inteiro + `agent.py:539-589` (`_avisar_gatilhos`) | Por ticker da watchlist ∪ posições, `timing.montar` decide `estado` (`armado`/`gatilho`/`esticado`); em `gatilho`, push SEMPRE informativo, nunca executa; opt-in via `push.prefs_for` (`pushPrefs.gatilho`), independente de `agent.mode`/`serverEnabled` |
| Núcleo do timing | `timing.py:62-132` (`avaliar`) | `plano.decisao` (`COMPRAR`/`VENDER`) × fechamento da barra 15m × `plano.entrada` → estado. Não sabe nada de execução |
| Config do agente | `agent.py:308-328` (`agent_params`), `store.py:297-330` (`set_agent`), `persistence.js:875-920` (`putAgent`/`SERVER_KEYS`) | 3 lugares que TODO campo novo precisa tocar (armadilha conhecida do repo) |
| UI do Operador | `App.jsx:3497-3754` (`AgenteScreen`) | Toggles executar/sinalizar, regras, trailing, alocação (hoje solta), tetos |

## 4. Fases

### Fase A — Modo Estudo nunca executa (trava estrutural)

**Backend** (`server/app/agent.py`, `server/app/store.py`):
- `agent_params(ag, app_mode=None)` ganha o parâmetro `app_mode`; se
  `app_mode != "operador"`, força `mode="sinalizar"` no dict retornado,
  **independente do que está salvo**. `_run_cycle_inner` (e a segunda
  passada de opções) passam a chamar `agent_params` com o `appMode` real do
  usuário (`store.get(conn, "config", user_id=scope).get("appMode")`).
- `set_agent` (`store.py`): ao gravar `mode="executar"` (ou `autonomous=True`
  — achado 2), se `config.appMode != "operador"` no momento da gravação,
  grava `sinalizar`/`False` mesmo assim — a trava vale tanto na LEITURA
  quanto na ESCRITA (D1: migração silenciosa cobre quem já tinha salvo
  antes desta entrega; a escrita cobre quem tentar religar depois).
- Fortalece o vínculo `mode="executar"` ↔ `serverEnabled`: ao gravar
  `mode="executar"` via `set_agent`, se `serverEnabled` não vier junto no
  mesmo patch E não estiver já `True`, grava `serverEnabled=True` também —
  elimina o estado ambíguo "quero executar mas só protejo com o app aberto"
  que é a hipótese principal do bug. Documentar a decisão no comentário
  (por que acoplar: "Executar" só faz sentido rodando em background).

**Frontend** (`web/src/App.jsx`, `AgenteScreen`):
- O card do Operador ganha a mesma leitura: se `appMode !== "operador"`, o
  botão "Executar" fica desabilitado (não escondido — mostra por que:
  "Disponível no Modo Operador"), e o texto do card muda para deixar claro
  que em Modo Estudo o agente só orienta.
- Sem mudança de rota/aba: `AgenteScreen` continua acessível nos dois modos
  (é onde a pessoa vê o Diário e ORIENTAÇÕES mesmo em Estudo) — só a opção
  de executar é que se torna indisponível fora do Operador.

**Testes**: `server/tests/test_agent_modo_estudo.py` (novo) — confirma que
`agent_params` com `app_mode="estudo"` sempre devolve `mode="sinalizar"`
mesmo com `ag={"mode": "executar"}`; confirma que `set_agent` não grava
`executar` quando `appMode` corrente é estudo; confirma o acoplamento
`mode="executar"` → `serverEnabled=True`. `web/tests/test_agente_modo_estudo_ui.mjs`
(novo) — confirma o botão desabilitado + texto condicional.

### Fase B — Entrada automática (backend)

**Config nova** (mesmos 3 lugares de sempre):
- `agent.py` → `agent_params`: `entradaAuto: bool` (default `False`);
  `allocPct` passa a ser LIDO (hoje é ignorado) com o teto absoluto do
  backend, ex. `max(1, min(20, ...))` — mesmo range que já existe na UI,
  então nenhuma conta perde o que já tinha configurado.
- `store.py` → `set_agent`: `if isinstance(patch.get("entradaAuto"), bool): ag["entradaAuto"] = patch["entradaAuto"]`. Mesma trava de Fase A: só grava
  `True` se `config.appMode == "operador"` no momento.
- `persistence.js` → `SERVER_KEYS` do `putAgent`: adiciona `entradaAuto`
  (allocPct já está lá).

**Lógica de execução** (`server/app/agent.py`, função nova `_avaliar_entradas`,
paralela a `_avaliar_opcoes` em estrutura):
- Chamada de dentro de `_run_cycle_inner`, DEPOIS da avaliação de saída (não
  antes — não faz sentido abrir posição nova no mesmo ciclo em que talvez
  feche outra do mesmo ticker).
- Só roda se `par["entradaAuto"]` E `app_mode == "operador"`.
- Itera a watchlist do usuário (`store.get(conn, "config", ...)["watchlist"]`
  ou equivalente — confirmar campo exato lendo `catalog.js`/`persistence.js`)
  MENOS os tickers já em `positions` (não duplica entrada).
- Para cada ticker: `timing.montar(radar_stored, intra_stored, ticker, "operador", agora=agora)`
  (mesmos `radar_stored`/`intra_stored` já obtidos em `_avisar_gatilhos` —
  reusar, não buscar de novo).
- Só age quando `estado == "gatilho"` E `decisaoDiaria == "COMPRAR"` (D5 —
  baixa nunca executa).
- **Dedupe com o push de `timing_watch`**: quando a entrada automática
  EXECUTA para um ticker+dia, marca esse ticker como `avisados` no estado do
  `timing_watch` daquele usuário (mesma chave `timingWatch`, mesmo formato)
  — impede o push "nada foi comprado" competir com o push real de compra no
  mesmo ciclo. Ler `timing_watch._estado`/grava via `db.kv_set` com a mesma
  chave; não duplicar a lógica de dedupe, reusar o dado.
- **Cálculo de quantidade — arredonda para BAIXO, nunca estoura o teto**:
  `orcamento = cash * (par["allocPct"] / 100)`; `qty = (orcamento // price // 100) * 100`
  (lotes de 100, para baixo). Se `qty < 100`: registra evento `warn` "orçamento
  de X% do caixa não cobre 1 lote de {ticker} a R$ {price} — sem execução,
  aviso mantido" e NÃO executa (não estoura o teto arredondando pra cima —
  `store.buy` sozinho arredondaria para cima e violaria o % prometido).
- Respeita os MESMOS tetos do lado de saída: `maxOpsDia` (D2, compartilhado)
  e `maxValorOp` (se configurado, também limita a entrada).
- Em caso de execução: `store.buy(conn, ticker, qty, price, user_id=scope, meta={"setup": ..., "auto": True})`;
  evento `kind: "buy"` no Diário com o texto explicando o % usado; push via
  o mesmo `notify_push` do ciclo (reusar o texto de eventos `kind=="buy"`
  que `scheduler_loop` já filtra em `agent.py:677`).
- Quando `entradaAuto=False` (default): **nenhuma mudança de comportamento**
  — o push de `timing_watch` continua exatamente como está hoje.

**Testes**: `server/tests/test_entrada_automatica.py` (novo) — cobre: não
executa com `entradaAuto=False`; não executa em Modo Estudo mesmo com
`entradaAuto=True` salvo (trava da Fase A); não executa lado VENDER; respeita
`maxOpsDia` compartilhado; arredonda para baixo e não executa se `qty<100`
em vez de arredondar pra cima; marca `timingWatch.avisados` ao executar
(sem push duplicado/contraditório); push de confirmação é enviado.

### Fase C — UI da entrada automática

**Arquivos**: `web/src/App.jsx` (`AgenteScreen`).

- Nova seção "Entrada automática", só visível/habilitada em Modo Operador
  (mesmo padrão condicional da Fase A): toggle "Entrar automaticamente" vs
  "Apenas avisar" (default apenas avisar); reaproveita o slider de
  `allocPct` já existente — MOVE ele para dentro desta seção (hoje está solto
  em "Modo local", sem war o que faz) e atualiza o texto explicativo para
  deixar claro que ele agora tem efeito real quando "Entrar automaticamente"
  está ligado.
- Texto segue o vocabulário do modo Operador (`skill_ref.vocab`), sem
  prometer resultado, com o disclaimer de sempre.

**Testes**: `web/tests/test_entrada_automatica_ui.mjs` (novo) — confirma a
seção só aparece/habilita em Modo Operador; confirma que o toggle chama
`putAg({ entradaAuto: ... })`; confirma que `allocPct` está dentro da nova
seção (não mais solto em "Modo local").

### Fase D — Verificação

- `cd server && .venv/bin/python -m pytest -q` (clone principal — este
  worktree não tem venv).
- Suíte web completa.
- Verificação AO VIVO: conta de teste em Modo Operador, `entradaAuto=True`,
  `allocPct` baixo (ex. 3%) para forçar o caminho "orçamento insuficiente,
  sem execução" e confirmar que ele realmente não arredonda pra cima; depois
  `allocPct` alto o bastante para uma execução real (dado de teste/mock),
  confirmar 1 lote comprado, evento no Diário, push único (não dois
  conflitantes), e teto `maxOpsDia` respeitado testando um cenário que já
  bateu o teto.

## 5. Fora de escopo

- Limpeza do `autonomous`/"Modo local" (achado 2, registrado, não tratado
  aqui).
- Qualquer mudança em posição vendida/short (não existe no modelo de dados;
  fora de escopo de produto por ora).
- O Modo Operador de trades REAIS (`PROPOSTA-MODO-OPERADOR.md`) — este plano
  é inteiramente sobre a carteira SIMULADA.
