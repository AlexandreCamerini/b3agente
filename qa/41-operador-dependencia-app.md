# qa/41 — Operador IA não executa sem o app aberto · Fase 1 (diagnóstico)

Data: 16/07/2026 (quinta, dia útil) · ~09:25 BRT · read-only, zero patch.
Produção: `b3agente-production.up.railway.app`.

## §4 — Veredito por hipótese

```
H1 (deadlock Serverless × intervalo) | DESCARTADA — container bootou 00:57 BRT (03:57:58 UTC),
   radar diário rodou 08:48 BRT (LAST_DAILY em memória, duracaoS 12.5) e o processo respondia
   09:22 BRT. 1 (uma) ocorrência de "Starting Container" no log do deployment. Entre 01:15 BRT e
   09:10 BRT: zero requests inbound no log. Logo o processo sobreviveu ~7h30 sem outbound e sem
   inbound, sem reiniciar. Se o sono de 10 min estivesse ativo, LAST_DAILY estaria vazio e
   haveria um 2º "Starting Container". Além disso, o gatilho literal do H1 não existe:
   B3_AGENT_INTERVAL_S não está setado no Railway → default 300s < 600s (status: intervaloS=300).

H2 (kill switch) | DESCARTADA — `railway variables` não contém B3_AGENT_KILL;
   /api/agent/status retorna killSwitch: false.

H3 (usuariosHabilitados == 0) | DESCARTADA — status retorna usuariosHabilitados: 2 com o app
   fechado. `list_server_users` (agent.py:181) lê SÓ o kv persistido
   ("SELECT key,value FROM kv WHERE key LIKE 'u:%:agent'" + flag serverEnabled) — não exige
   sessão, token nem atividade recente. E `set_agent` (store.py:248) é patch seletivo: só grava
   serverEnabled quando `isinstance(patch.get("serverEnabled"), bool)`, logo o `A.putAgent({})`
   do front NÃO insere nem remove ninguém da lista. Correção factual ao enunciado: esse
   putAgent({}) está em `rodarAgora` (App.jsx:3496), disparado pelo botão "rodar agora" — não
   "10s após abrir o app".

H4 (guard de horário) | DESCARTADA — BRT = timezone(timedelta(hours=-3)) (agent.py:28), offset
   correto (BR sem horário de verão desde 2019). status.agoraBRT "16/07 09:22" bateu com o
   relógio real. pregaoAberto: false às 09:22 está CORRETO — a janela é 10:00–17:59 e o pregão
   ainda não abrira. Nenhum desvio de timezone/janela observado.

H5 (ciclo agendado sem credencial) | DESCARTADA — `run_cycle_for`/`_run_cycle_inner`
   (agent.py:99-180) não referenciam LLM, api_key, BYOK ou sessão: grep por
   "llm|LLM|anthropic|api_key|byok" em agent.py retorna ZERO ocorrências. A única dependência
   externa é `quotes_getter`, injetado pelo scheduler como `yahoo.get_quotes` — sem auth.
   O ciclo já NÃO é silencioso: o except de run_cycle_for grava "Ciclo (agendado) FALHOU..."
   via `store.push_agent_log` e faz re-raise (critério de aceite §6.7 já satisfeito hoje).
```

**Nenhuma das 5 hipóteses sobrevive ao dado.** O estado observável do servidor às 09:22 BRT é
o de um sistema saudável: laço vivo (`proximaPassadaEmS: 46`), 2 usuários habilitados, kill
switch off, timezone certo, container 24/7.

`ultimoCiclo.at: null` é integralmente explicado sem bug: `LAST_RUN` só é escrito dentro de
`if not kill_switch_on() and in_market_hours()` (agent.py:~221). O container bootou 00:57 BRT —
depois do fechamento de 15/07 — e às 09:22 o pregão de 16/07 ainda não abrira. O processo nunca
esteve em market hours. `ultimoCiclo.at: null` não é sintoma; é aritmética.

## H6 — hipótese que o dado levanta (não estava no enunciado)

"Proteção armada" (stop/alvo numa posição) e "Operador no servidor" (`serverEnabled`) são dois
controles **separados**, e armar o primeiro não liga o segundo:

- `serverEnabled` é o ÚNICO critério de `list_server_users` → decide se o laço server-side cuida
  do usuário.
- `rules.stop` / `rules.alvo` + `pos["stop"]` / `pos["alvo"]` são o que `_run_cycle_inner` avalia
  DEPOIS de o usuário já estar na lista.
- `/api/cycle` e `/api/agent/run-now` (caminhos do app aberto) chamam `run_cycle_for`
  diretamente, **sem consultar `serverEnabled`**.

Consequência exata do sintoma relatado: um usuário com stop/alvo armado mas `serverEnabled`
desligado executa com o app aberto (via /api/cycle) e não executa com o app fechado (o laço o
pula). Nenhum bug de código — assimetria de contrato entre os dois caminhos.

Agrava: `App.jsx:2652` e `:2660` pintam ATIVO/INATIVO e o toggle como `ag.serverEnabled && logged`.
Deslogado, o toggle é inerte (`onClick={() => logged && setServer(...)}`).

**Dado que falta para decidir H6:** o Alex está entre os 2 `usuariosHabilitados`? Requer o token
de sessão dele (ou ele abrir Perfil → Operador e ler ATIVO/INATIVO). Não obtenível por curl anônimo:
`meuServerEnabled: false` no meu curl é do escopo ANÔNIMO (`current_scope` → None sem Bearer),
não do Alex — não serve de evidência.

## Prova positiva — OBTIDA (10:36 BRT, read-only, zero patch)

**A premissa do enunciado está REFUTADA. O laço executa com o app fechado.**

`RUN_HISTORY` lido às 10:36 BRT, 7 passadas consecutivas, cadência de 5 min exatos:

```
16/07 10:33 | usuarios=1 | executadas=0 | dur=0.2 | erros=[]
16/07 10:28 | usuarios=0 | executadas=0 | dur=0.0 | erros=[]
16/07 10:23 | usuarios=0 | executadas=0 | dur=0.0 | erros=[]
16/07 10:18 | usuarios=0 | executadas=0 | dur=0.0 | erros=[]
16/07 10:13 | usuarios=0 | executadas=0 | dur=0.0 | erros=[]
16/07 10:08 | usuarios=0 | executadas=0 | dur=0.0 | erros=[]
16/07 10:03 | usuarios=2 | executadas=0 | dur=0.3 | erros=[]
```

`ultimoCiclo.at` avançou de `null` → `16/07 10:33`. `pregaoAberto: true`.

Isolamento da prova (log de requests do deployment, dia inteiro, UTC):
```
03:57:58  health (100.64.0.2, interno)     00:57 BRT — boot
03:58:13  health (189.122.252.166)         00:58 BRT
04:15:10  /api/agent/status                01:15 BRT
12:10:22  /api/agent/status                09:10 BRT
12:22:31  /api/agent/status                09:22 BRT  ← meu curl (Fase 1)
13:35:43  /api/agent/status                10:35 BRT  ← meu curl (prova)
13:36:10  /api/agent/status                10:36 BRT  ← meu curl (prova)
```
- Entre 09:22 e 10:35 BRT: **ZERO requests**. As 7 passadas (10:03→10:33) caem inteiras nessa
  janela de silêncio. Nenhum cliente tocou o servidor.
- Nenhum `/api/cycle` nem `/api/agent/run-now` no dia inteiro → o app esteve fechado; nada foi
  disparado por mão humana.
- `Starting Container` continua **1** → mesmo processo desde 00:57 BRT, sem cold boot. Os ciclos
  não foram acordados por request meu. (Sela H1 em definitivo.)

Critérios de aceite §6.3 e §6.4: **SATISFEITOS** — e satisfeitos pelo código como está hoje,
sem uma linha de patch.

## Achado novo: o gate `intervalMin` dos 2 usuários é grande

10:03 rodou os 2 (primeira passada em market hours após boot → `LAST_USER_RUN` vazio, ambos
passam). Depois: 10:08–10:28 = 0 usuários; 10:33 = 1 usuário. Logo 10:03 → 10:33 = **30 min**
para o usuário que voltou, e **> 30 min** para o outro. Nenhum dos dois usa o default de 15.

Isto é candidato forte a explicar a PERCEPÇÃO do sintoma, junto com H6:
- app fechado → o ciclo do usuário roda a cada 30–60+ min (gate `intervalMin`);
- app aberto → botão "rodar agora" (`/api/agent/run-now`) dispara **na hora**, ignorando o gate.

Quem testa abrindo o app e clicando vê executar; quem fecha e espera 5 min não vê nada — porque
o gate dele é 30–60 min, não 5. Comportamento correto do código, expectativa desalinhada.

## Limite honesto desta prova

`executadas: 0` em todas as passadas — nenhum stop/alvo foi atingido na janela. Está provado que
o **ciclo roda** com o app fechado; **não** está provado por observação que ele **executa a venda**
quando o stop bate. O caminho é o mesmo `_run_cycle_inner` do `/api/cycle`, então não há razão
estrutural para divergir — a única divergência real entre os dois caminhos é `serverEnabled` (H6).
Prova definitiva exigiria um stop atingido de verdade (ou um usuário de teste com stop colado no
preço) — não feito nesta sessão por ser escrita em dado de produção.

## Pendências registradas (fora de escopo, NÃO patchear nesta sessão)

- `asyncio.get_event_loop()` deprecado em `main.py:1107` e `:1123` — roda sob loop ativo, não é bug.
- `in_market_hours` não conhece feriado B3 → roda em feriado. Causa over-execution, nunca o
  sintoma relatado. Fora de escopo.
- Janela 10:00–17:59 vs pregão real (fechamento 17:00 / after-market). Não relacionado ao sintoma.
