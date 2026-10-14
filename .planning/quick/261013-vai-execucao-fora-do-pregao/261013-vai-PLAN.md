---
phase: quick-261013-vai
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  # Leva A — backend
  - server/app/skill_ref.py
  - server/app/agent.py
  - server/app/main.py
  - server/tests/relogio_pregao.py
  - server/tests/test_execucao_fora_pregao.py
  - server/tests/test_execucao_fora_pregao_rotas.py
  - server/tests/test_fase3_operador.py
  - server/tests/test_agent.py
  - server/tests/test_agent_options.py
  - server/tests/test_agent_modo_estudo.py
  - server/tests/test_opcoes_lastreadas_vencimento.py
  - server/tests/test_push_payload.py
  - server/tests/test_push_prefs_classes.py
  - server/tests/test_opcoes_lastreadas_rotas.py
  - server/tests/test_opcoes_collar_rota.py
  - server/tests/test_curadoria_collar_rota.py
  - server/tests/test_gate_liquidez_rotas.py
  - server/tests/test_fase5_rejeicao_rotas.py
  - server/tests/test_opcoes_cota_reserva_rotas.py
  - server/tests/test_opcao_descoberto_gate.py
  - server/tests/test_fuso_dias_ate_vencimento.py
  - server/tests/test_opcoes_anatomia_rota.py
  - server/tests/test_mydata_budget_prioridade.py
  # (lista de testes dependentes do relógio é CONFIRMADA pela descoberta da Tarefa 1b; arquivo que não falhar não é tocado)
  # Leva B — front/iOS
  - web/src/copy.js
  - web/src/persistence.js
  - web/src/evolucaoPosicao.js
  - web/src/App.jsx
  - web/src/opcoes/OpcoesScreen.jsx
  - web/src/opcoes/ConfirmarEstrutura.jsx
  - web/src/opcoes/ExecutarProposta.jsx
  - web/src/opcoes/SecaoAnalisar.jsx
  - web/src/opcoes/CuradoriaEstruturas.jsx
  - web/src/opcoes/AbaRecomendadas.jsx
  - web/src/opcoes/CandidatoOpcao.jsx
  - web/src/opcoes/PropostaLastreada.jsx
  - web/src/opcoes/PernasAbertas.jsx
  - web/tests/test_vocabulario_espelho.mjs
  - web/tests/test_execucao_fora_pregao.mjs
  - web/tests/test_opcoes_mercado_fechado_ui.mjs
autonomous: true
requirements: [QUICK-261013-vai-D1, QUICK-261013-vai-D2, QUICK-261013-vai-D3, QUICK-261013-vai-D4]

must_haves:
  truths:
    - "Fora do pregão (noite, fim de semana, feriado B3, antes das 10:00, 16:55–17:30, after-market sem opt-in) nenhum ciclo do servidor executa stop, alvo, trailing, alvo dinâmico de ações, stop/alvo/trailing de opção nem entrada automática — vale para scheduler, ciclo imediato, run-now e /api/cycle"
    - "Liquidação de VENCIMENTO de opção (lastreada e legado) NÃO é execução de ordem: roda também fora do pregão, com a mesma regra de preço de hoje (spot do ativo-objeto lido da cadeia no ciclo), nunca antes da abertura do próprio dia do vencimento — servidor e iPhone"
    - "Registrar stop/alvo (PUT /api/position e PUT /api/options/position) funciona sempre; com o mercado fechado o valor é gravado e nada é vendido"
    - "Com o mercado fechado, o Diário recebe UM aviso por (tipo, id) por dia BRT, no vocabulário do modo, sem push: AÇÃO com stop/alvo atingido pela cotação já buscada no ciclo → aviso 'seria atingido' (chave `acao:<ticker>`); OPÇÃO não vencida com stop e/ou alvo definidos → aviso GENÉRICO 'stop/alvo da opção <contrato> será avaliado na abertura', sem preço e sem afirmar que seria atingido (chave `opcao:<contractId>`, D2-emenda) — nenhuma leitura de prêmio ou cota de opção fora do pregão, servidor e iPhone"
    - "No primeiro ciclo com o pregão aberto a posição é reavaliada com o preço corrente e executa se ainda atingido, inclusive com gap pior que o stop (pnl do motor)"
    - "POST /api/agent/run-now e POST /api/cycle com o mercado fechado respondem 200 com mercadoFechado=true e a frase canônica 'Mercado fechado — nada foi executado…'; o front mostra essa frase"
    - "As 6 rotas de execução de opções respondem 409 com detail {code:'mercado_fechado', message, action} fora do pregão, sem consultar o provedor de opções; rotas de leitura/simulação seguem livres"
    - "No iPhone (deviceStore.cycle) o mesmo portão vale: mercado fechado → nada executa + aviso local deduplicado; status indeterminado (rede/erro) → nada executa; o setInterval do modo autônomo não dispara fora do pregão confirmado"
    - "Na aba de Opções, com o pregão confirmado fechado, todo botão de executar/abrir/fechar fica bloqueado com o motivo visível 'Mercado fechado — abre às HH:MM'; botões de stop/alvo nunca são bloqueados"
    - "Herança preservada: B3_AFTER_MARKET=1 na janela 17:30–18:00 e B3_DEV_MERCADO_ABERTO=1 (staging) liberam a execução, porque o portão é agent.in_market_hours → pregao.in_market_hours"
  artifacts:
    - path: "server/app/skill_ref.py"
      provides: "Dict EXECUCAO_FORA_PREGAO (operador/educacional) + execucao_fora_pregao_txt(modo, chave, **dados)"
      contains: "EXECUCAO_FORA_PREGAO = {"
    - path: "server/app/agent.py"
      provides: "Portão em _run_cycle_inner + _gatilho_saida (puro, reusado) + _avisar_fora_pregao (dedupe kv avisoForaPregao por chave tipo:id) + _avaliar_opcoes(somente_vencimento)"
      contains: "def _gatilho_saida"
    - path: "server/app/main.py"
      provides: "_recusar_execucao_fora_do_pregao (409) nas 6 rotas de execução de opções; run-now e /api/cycle com mercadoFechado"
      contains: "def _recusar_execucao_fora_do_pregao"
    - path: "server/tests/relogio_pregao.py"
      provides: "Helpers de relógio injetado (abrir_pregao, injetar_relogio) via monkeypatch de pregao.in_market_hours ciente de `now`"
      contains: "def injetar_relogio"
    - path: "server/tests/test_execucao_fora_pregao.py"
      provides: "Tabela de casos do motor com relógio injetado"
    - path: "server/tests/test_execucao_fora_pregao_rotas.py"
      provides: "Rotas: PUT position, run-now, /api/cycle, 6 rotas de opções 409, leitura livre, guardião estrutural"
    - path: "web/src/copy.js"
      provides: "COPY[modo].execucaoForaPregao (espelho byte a byte) + execucaoForaPregaoTxt"
      contains: "execucaoForaPregao"
    - path: "web/src/persistence.js"
      provides: "deviceStore.cycle com portão de mercado (fechado/indeterminado não executa) e aviso deduplicado"
      contains: "avisoForaPregao"
    - path: "web/tests/test_execucao_fora_pregao.mjs"
      provides: "Comportamento do deviceStore.cycle (fechado/indeterminado/aberto/dedupe) + guardiões estáticos do App.jsx"
    - path: "web/tests/test_opcoes_mercado_fechado_ui.mjs"
      provides: "Guardião dos bloqueios de Opções (prop bloqueioMercado em cada componente de execução, stop/alvo livres)"
  key_links:
    - from: "server/app/agent.py::_run_cycle_inner"
      to: "agent.in_market_hours → pregao.in_market_hours"
      via: "chamada sem argumento antes do bloco de trailing/stop/alvo"
      pattern: "if not in_market_hours\\(\\):"
    - from: "server/app/agent.py::_avisar_fora_pregao"
      to: "skill_ref.execucao_fora_pregao_txt"
      via: "texto do aviso por modo"
      pattern: "execucao_fora_pregao_txt\\("
    - from: "server/app/agent.py::_avisar_fora_pregao (opções)"
      to: "skill_ref.execucao_fora_pregao_txt(modo, \"aviso_opcao\", contrato=...)"
      via: "aviso genérico só com dados da posição (stop/alvo definidos), sem option_quotes_getter"
      pattern: "\"aviso_opcao\""
    - from: "server/app/main.py (6 rotas de execução de opções)"
      to: "_recusar_execucao_fora_do_pregao"
      via: "chamada antes de options_provider.get_options"
      pattern: "_recusar_execucao_fora_do_pregao\\("
    - from: "web/src/persistence.js::deviceStore.cycle"
      to: "api.marketStatus"
      via: "consulta no início do ciclo; erro = indeterminado = não executa"
      pattern: "api\\.marketStatus\\(\\)"
    - from: "web/src/App.jsx (setInterval do modo autônomo e A.* de opções)"
      to: "mercadoRef.current"
      via: "ref espelho do estado `mercado` (sem mexer nas deps do useMemo de A)"
      pattern: "mercadoRef\\.current"
    - from: "web/src/opcoes/OpcoesScreen.jsx"
      to: "componentes de execução de opções"
      via: "prop bloqueioMercado (string|null)"
      pattern: "bloqueioMercado"
---

<objective>
Fechar o achado W4 da quick 261013-u7w: nenhuma EXECUÇÃO simulada acontece fora do pregão, no servidor e no iPhone. Portão único no motor (D1), aviso deduplicado no Diário e execução na abertura com o preço corrente (D2), mesmo portão no ciclo local do iPhone (D3), rotas manuais de opções recusando com 409 e UI de Opções bloqueada com aviso (D4). Registrar stop/alvo segue sempre permitido (guardrail "stop/alvo nunca são vetados").

Purpose: hoje stop/alvo/trailing/alvo dinâmico/opções do agente/entrada automática executam a qualquer hora quando o ciclo é disparado fora do scheduler (PUT /api/position, buy/sell, run-now, /api/cycle, iPhone) e as rotas manuais de opções executam com prêmio possivelmente velho — viola "preço de execução respeitando os dados disponíveis no momento da operação" e o princípio 4.

Output: backend com portão + aviso + 409 + testes com relógio injetado (Leva A); front/iOS com portão no deviceStore, no setInterval, no A.* de opções, mensagem do ciclo e bloqueio visual na aba de Opções + guardiões (Leva B).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/quick/261013-vai-execucao-fora-do-pregao/261013-vai-CONTEXT.md
@./CLAUDE.md
@.claude/skills/didatica-boris/SKILL.md

Regras de leitura: App.jsx NUNCA inteiro (Grep + Read com offset/limit). Não ler STATE.md/PROJECT.md.

<interfaces>
<!-- Extraído do código em 2026-10-13. O executor usa direto, sem caçar. -->

server/app/agent.py
- `in_market_hours(now=None)` (:369-379) — wrapper que importa `pregao` localmente e delega a `pregao.in_market_hours(now)` em tempo de chamada.
- `_today()` (:137) → "YYYY-MM-DD" em BRT. `_now_str()` (:141).
- `run_cycle_for(conn, scope, quotes_getter, origem="agendado", snapshot_getter=None, option_quotes_getter=None)` (:848) — guard `_CYCLE_BUSY`, chama `_run_cycle_inner`; retorna dict.
- `_run_cycle_inner(...)` (:875-1029). Ordem atual: lê positions/agent/config → `par = agent_params(ag, app_mode)` → `quotes_data = await quotes_getter(...)` (:891) → `sem_cotacao` → ctxs do trailing/alvo dinâmico via `snapshot_getter` (:900-911) → laço de posições: trailing (:921-927), `breach_stop = par["rules"]["stop"] and pos.get("stop") is not None and price <= pos["stop"]` e `hit_alvo = par["rules"]["alvo"] and pos.get("alvo") is not None and price >= pos["alvo"]` (:928-929), alvo dinâmico (:933-942), modo sinalizar/tetos, `store.sell(..., motivo="stop"|"alvo", origem="automatico")` (:962), evento `kind:"buy"` com `tag` → `_avaliar_opcoes` (:1006) → `_avaliar_entradas` (:1012) → resumo → `store.push_events` + `store.push_agent_log` (:1023-1025) → `return {"events", "executed", "appMode"}`.
- `_avaliar_opcoes` (:535-669): EXECUTA liquidação de vencimento lastreada (`store.liquidar_lastreada_vencida`), vencimento legado (`store.close_option_vencida`), trailing de opção (`store.set_option_position`) e stop/alvo de opção (`store.sell_option`) — tudo coberto pelo portão (não é chamado fora do pregão).
- PRECIFICAÇÃO DO VENCIMENTO HOJE (levantado 2026-10-13, ajuste do coordenador): `quotes = await _option_quotes(option_quotes_getter, opts)` (agent.py:550) → `spot = payload.get("underlyingPrice")` (:561), lido do provedor de opções NO MOMENTO DO CICLO; `hoje = _today()` (:552, data BRT). Lastreada: condição `str(pos["expiration"]) <= hoje` (:564) → `store.liquidar_lastreada_vencida(conn, id, float(spot))` (:567; store.py:1445, recompra/liquidação ao intrínseco `max(0, spot-strike)` / put pelo intrínseco). Legado: mesma condição (:598) → `intrinseco_opcao(pos, float(spot))` (agent.py:514) → `store.close_option_vencida` (store.py:1046, `origem="sistema"`, docstring ADR-005 "valor intrínseco na data do vencimento"). Conclusão: o preço DEPENDE do horário do ciclo — com o scheduler (só em pregão) o vencimento de sexta liquida no 1º ciclo de sexta (~10:00, spot da manhã, não o fechamento); um ciclo atrasado para segunda usaria o spot de segunda. Travar no dado do dia do vencimento é mudança maior e NÃO entra neste plano (ver análise devolvida ao coordenador); este plano preserva a regra de preço de hoje e só impede o adiamento causado pelo portão e a liquidação antes da abertura do dia do vencimento.
- `_avaliar_entradas` (:681-789): só roda com `entradaAuto` + appMode operador; compra 1 lote — coberto pelo portão.
- Scheduler: `if not kill_switch_on() and in_market_hours():` (:1308) — inalterado.

server/app/pregao.py
- `BRT`, `ABERTURA=(10,0)`, `FECHAMENTO=(16,55)`, `AFTER_INICIO=(17,30)`, `AFTER_FIM=(18,0)`; `is_holiday(d)`, `is_trading_day(d=None)`, `after_market_ligado()` (env B3_AFTER_MARKET), `dev_mercado_aberto_forcado()` (env B3_DEV_MERCADO_ABERTO), `in_market_hours(now=None)` (:144).

server/app/skill_ref.py
- Padrão a copiar: `ENTRADA_AUTO = {...}` (:412) e `entrada_auto_txt` (:489); `RETORNO_ACUMULADO` (:434) com espelho em copy.js. Cada valor é UMA string literal entre aspas duplas numa linha só, sem aspas internas (o parser regex do test_vocabulario_espelho.mjs exige; concatenação implícita quebra o parse).

server/app/main.py
- `GET /api/market/status` (:1784) → `{aberto, diaDePregao, abertura:"HH:MM", fechamento, agoraBRT, afterMarket, devForcado}`.
- `PUT /api/position/{ticker}` (:3007-3011) → `store.set_position` + `_disparar_ciclo_imediato(scope)`.
- Execução de opções: `/api/options/buy` (:3029), `/api/options/sell` (:3090), `/api/options/curadoria/abrir-collar` (:3693), `/api/options/lastreada/abrir` (:4230, 403 Estudo na primeira linha útil), `/api/options/lastreada/abrir-collar` (:4315), `/api/options/lastreada/fechar` (:4500, 403 Estudo primeiro). Todas chamam `options_provider.get_options` (ou re-derivação que o chama) dentro de `mydata_budget.contexto(...)`.
- Leitura (NÃO bloquear): `/api/options/proposta/{ticker}`, `/vigias`, `/curadoria` (GET), `/curadoria/narrativa`, `/escada/{ticker}`, `/anatomia/{ticker}`, `/escada/leitura`, `/tecnico/{ticker}`, `PUT /api/options/position/{id}` (registrar stop/alvo de opção).
- `_disparar_ciclo_imediato(scope)` (:5258) — task solta com `agent_mod.run_cycle_for(..., origem="imediato")`.
- `POST /api/cycle` (:5295-5304) e `POST /api/agent/run-now` (:5406-5428, 409 só p/ kill-switch; resposta `{ok, iniciado, mensagem}`).
- Formato de detail estruturado: `HTTPException(402, {"code":..., "message":..., ...})` (:1877); o front lê `detail.message/action/hint` em `enrichErrorMessage` (web/src/api.js:78).
- `store.registrar_rejeicao(conn, tipo in ("COMPRA","VENDA"), t, qty, price|None, motivo, user_id, origem="manual")` (store.py:888).

web/src/persistence.js
- `serverStore.cycle: () => api.cycle()` (:414); `serverStore.marketStatus` (:393).
- `deviceStore.marketStatus()` (:1923), `deviceStore.cycle()` (:1988-2112): busca cotações, stop/alvo de ações → `this.sell(pos.t)` se `doc.agent.autonomous`; opções via `api.optionsChain` (:2018) — vencimento lastreado SEMPRE (:2037-2075, recompra ao `_intrinsecoOpcao(pos, spot)` com `spot = chain.underlyingPrice` do momento do ciclo), vencimento legado só com `autonomous` (:2079-2088), stop/alvo de opção (:2090-2100) → `_sellOptionLocal`. ATENÇÃO: `const hoje = new Date().toISOString().slice(0, 10)` (:2022) é data UTC — entre 21:00 e 24:00 BRT da véspera já vale a data do vencimento e o iPhone liquida UM DIA ANTES, com o spot da véspera. empurra `doc.agent.events`; retorna `pub()` + `quotes`.
- `hojeBRT()` em web/src/evolucaoPosicao.js:38 (data BRT, única leitura de fuso do front).

web/src/App.jsx (offsets aproximados — confirme com grep)
- `const [mercado, setMercado] = useState(null)` (~9542) — `null` = 1ª consulta em voo, `{erro:true}` = falha, senão payload de /api/market/status. Guarda canônica do front: `!!(mercado && !mercado.erro && mercado.aberto)` (~10617).
- `rodarAgora` (~7866) já exibe `s.mensagem`.
- `A.cycle` (~10450): `flash("Ciclo executado.")` incondicional.
- `cycleRef.current = A.cycle` + `setInterval` do modo autônomo (~10556-10565).
- `A.buyOption` (~10176), `A.sellOption` (~10184), `A.abrirLastreada` (~10196), `A.abrirCollar` (~10208), `A.executarCandidatoCurado` (~10225, relança o erro em vez de flash), `A.fecharLastreada` (~10235).
- Deps do useMemo de A guardadas por web/tests/test_wiring_deps.mjs — NÃO adicionar `mercado` às deps; usar ref.

web/src/opcoes/OpcoesScreen.jsx
- `mercadoAberto` (:793-794) = boolean só quando o status é conhecido, senão null. Monta `<PernasAbertas>` (:906, :1027), `<ConfirmarEstrutura>` (:984), `<SecaoAnalisar>` (:1126 → `<ExecutarProposta>` em SecaoAnalisar.jsx:422), `<CandidatoOpcao>` (:1370), `<PropostaLastreada>` (:1385); `AbaRecomendadas` → `<CuradoriaEstruturas>` (AbaRecomendadas.jsx:32).
- Locks existentes: ConfirmarEstrutura `travado` (:69, `disabled={travado}` :92), ExecutarProposta `travado` (:116, :148), CuradoriaEstruturas `executarTravado` (:113, :308), CandidatoOpcao `busy || degradado` (:139), PropostaLastreada `busy || degradado` (:262), PernasAbertas encerrar com confirmação em 2 passos (`aria-disabled="true"` já usado em :106).
</interfaces>
</context>

<tasks>

<!-- ============================ CORTE DE EXECUÇÃO — LEVA A (backend) ============================ -->

<task type="auto" tdd="true">
  <name>Tarefa 1a (Leva A): portão no motor + aviso deduplicado de AÇÃO no Diário + vocabulário</name>
  <files>server/app/skill_ref.py, server/app/agent.py, server/tests/relogio_pregao.py, server/tests/test_execucao_fora_pregao.py</files>
  <behavior>
    Relógio injetado por `injetar_relogio(monkeypatch, datetime(..., tzinfo=pregao.BRT))`, que troca `pregao.in_market_hours` por uma função que, sem `now`, chama a original com o instante injetado (calendário, after-market e dev flag reais). Posição PETR4 qty 100 avg 40, stop 38, alvo 45, agent `{serverEnabled, mode:"executar", maxOpsDia:3, autonomous}`, appMode operador, cotação fake.
    - F1 noite (qua 2026-10-14 22:00), F2 sábado (2026-10-17 14:00), F3 feriado (2026-11-02 14:00 — afirme `pregao.is_holiday(date(2026,11,2))` como pré-condição), F4 antes da abertura (2026-10-14 09:30), F5 call/zona morta (2026-10-14 16:56 e 17:10), F6 after-market SEM opt-in (2026-10-14 17:45, B3_AFTER_MARKET ausente): preço 37.5 → `executed == 0`, positions e cash inalterados, nenhuma VENDA no history, nenhum evento `kind:"buy"`, exatamente 1 evento de aviso com o texto de `skill_ref.execucao_fora_pregao_txt("operador","aviso_diario", ticker="PETR4", motivo="stop")`, retorno com `mercadoFechado is True`.
    - A1 after-market COM opt-in (monkeypatch.setenv B3_AFTER_MARKET=1, 2026-10-14 17:45) → executa (herança D1).
    - A2 dev forçado (monkeypatch.setenv B3_DEV_MERCADO_ABERTO=1, sábado) → executa (herança staging; ÚNICO uso da flag, testando a flag, nunca como muleta).
    - A3 pregão (qua 2026-10-14 14:00) → vende pelo motor, evento `kind:"buy"` tag "stop" (regressão).
    - T1 trailing ligado, fechado, preço acima → stop NÃO sobe. T2 alvoDinamico ligado, fechado, preço ≥ alvo → alvo e alvoExtensoes inalterados. T3 spy em `agent._avaliar_entradas` → não chamado fechado, chamado aberto. T4 spy em snapshot_getter → não chamado fechado.
    - D1 dedupe: dois ciclos fechados no mesmo dia → 1 aviso no agentLog; relógio no dia seguinte fechado → novo aviso; duas ações atingidas → 1 aviso cada; kv `avisoForaPregao` guarda chaves `acao:PETR4`. Sem breach → zero aviso e zero linha nova no Diário.
    - D2 modo Estudo (appMode ausente): texto do aviso é o de "educacional".
    - D3 abertura: ciclo fechado (aviso) e depois ciclo com relógio de pregão e preço 36.0 (gap abaixo do stop 38) → vende a 36.0; `pnl` do evento == retorno de `store.sell` (−400.0), nunca recomposto.
    - D4 modo "apenas sinalizar" fechado → aviso fora do pregão (nenhum "Sinal do agente").
    - S1 `execucao_fora_pregao_txt`: placeholder sem valor levanta ValueError; chave desconhecida KeyError; modo desconhecido cai em educacional.
  </behavior>
  <action>
    (a) skill_ref.py — per D2/D4, novo dict `EXECUCAO_FORA_PREGAO` logo após `ENTRADA_AUTO`, com comentário de decisão "quick 261013-vai (2026-10-13)" e "espelho byte a byte em web/src/copy.js COPY[modo].execucaoForaPregao (Leva B)". Chaves IDÊNTICAS nos dois modos (10): aviso_diario, aviso_opcao, ciclo_fechado, ciclo_fechado_sem_hora, status_indeterminado, opcao_bloqueada, opcao_bloqueada_sem_hora, opcao_bloqueada_acao, botao_bloqueado, botao_bloqueado_sem_hora. Textos (literais únicos por linha, sem aspas internas):
    operador.aviso_diario = Mercado fechado: {motivo} de {ticker} atingido na última cotação. Nada foi executado; a avaliação é refeita na abertura do próximo pregão, ao preço daquele momento (gap possível).
    operador.aviso_opcao = Mercado fechado: stop/alvo da opção {contrato} será avaliado na abertura.
    educacional.aviso_opcao = Mercado fechado: o stop/alvo da opção {contrato} só é conferido na abertura do próximo pregão, com o prêmio daquele momento. Fora do pregão nenhuma ordem é executada, nem a simulada.
    operador.ciclo_fechado = Mercado fechado — nada foi executado. Stop, alvo e entradas são reavaliados na abertura do próximo pregão, às {abertura}.
    operador.ciclo_fechado_sem_hora = Mercado fechado — nada foi executado. Stop, alvo e entradas são reavaliados na abertura do próximo pregão.
    operador.status_indeterminado = Status do mercado indisponível — nada foi executado neste ciclo. Nova tentativa no próximo ciclo.
    educacional.aviso_diario = Mercado fechado: pela última cotação, o {motivo} de {ticker} seria atingido. Fora do pregão nenhuma ordem é executada, nem a simulada. Na abertura do próximo pregão o simulador confere de novo com o preço daquele momento; se o preço abrir além do nível definido (o chamado gap), a execução sai no preço de abertura, que pode ser pior que o {motivo}.
    educacional.ciclo_fechado = Mercado fechado — nada foi executado. A bolsa só negocia no pregão, então stop, alvo e entradas são conferidos de novo na abertura, às {abertura}.
    educacional.ciclo_fechado_sem_hora = Mercado fechado — nada foi executado. A bolsa só negocia no pregão, então stop, alvo e entradas são conferidos de novo na abertura.
    educacional.status_indeterminado = Não foi possível confirmar se o mercado está aberto — por segurança, nada foi executado neste ciclo. O simulador tenta de novo no próximo.
    opcao_bloqueada (os dois modos, fato) = Mercado fechado — a B3 abre às {abertura}; nenhuma ordem de opção é executada fora do pregão.
    opcao_bloqueada_sem_hora (os dois) = Mercado fechado — nenhuma ordem de opção é executada fora do pregão.
    operador.opcao_bloqueada_acao = Aguarde a abertura do pregão para executar. Cadeia, escada e payoff seguem disponíveis para análise.
    educacional.opcao_bloqueada_acao = Enquanto a bolsa está fechada, dá para estudar a cadeia, a escada e o payoff; a ordem só pode ser enviada no pregão.
    botao_bloqueado (os dois) = Mercado fechado — abre às {abertura}
    botao_bloqueado_sem_hora (os dois) = Mercado fechado — execução só no pregão
    Função `execucao_fora_pregao_txt(modo, chave, **dados)`: modo desconhecido cai em "educacional" (padrão de `entrada_auto_txt`); substitui {ticker}/{motivo}/{abertura}/{contrato} pelos valores recebidos; placeholder da frase escolhida SEM valor levanta ValueError (nunca devolve "?" nem inventa hora — quem chama escolhe a variante *_sem_hora quando não tem abertura); chave desconhecida levanta KeyError. Teste: botao_bloqueado sem abertura levanta; botao_bloqueado_sem_hora não tem placeholder.
    (b) agent.py — extrair função pura `_gatilho_saida(par, pos, price) -> tuple[bool, bool]` com EXATAMENTE as duas expressões de :928-929 e usá-la no laço existente (sem mudar comportamento). Nova `_avisar_fora_pregao(conn, scope, par, app_mode, positions, quotes_data, option_positions=()) -> list`: nesta tarefa cobre AÇÕES — para cada posição com preço e `_gatilho_saida` verdadeiro (stop vence alvo), texto `skill_ref.execucao_fora_pregao_txt("operador" if app_mode == "operador" else "educacional", "aviso_diario", ticker=..., motivo="stop"|"alvo")`; dedupe per B2 em kv próprio `avisoForaPregao` = {"data": _today(), "chaves": [...]} por escopo, chave `"acao:" + ticker` (db.kv_get/kv_set; data diferente zera a lista); evento `{"time": _now_str(), "kind": "warn", "t": ticker, "text": ...}` SEM `tag` (o funil de push filtra kind=="buy"; sem tag nenhuma classe de push). O parâmetro de opção fica com default inerte e é preenchido na Tarefa 1b. Em `_run_cycle_inner`, logo APÓS `sem_cotacao` e ANTES do bloco de ctxs (:900), inserir o portão per D1: `if not in_market_hours():` (chamada sem argumento ao wrapper do próprio módulo — NÃO usar a string literal "if not kill_switch_on() and in_market_hours():" aqui) → eventos = `_avisar_fora_pregao(...)`; se houver eventos, `store.push_events` e (se scope) `store.push_agent_log`; retornar `{"events": eventos, "executed": 0, "appMode": app_mode, "mercadoFechado": True}`. Sem resumo "Ciclo (...)" no Diário no ramo fechado. Comentário de decisão no portão citando D1/D2, W4 da 261013-u7w e por que fica depois das cotações (o aviso precisa do preço) e antes de snapshot_getter/opções/entradas. Scheduler e pending_orders intocados.
    (c) server/tests/relogio_pregao.py (helper, sem prefixo test_): `injetar_relogio(monkeypatch, instante)` como descrito no behavior; `abrir_pregao(monkeypatch)` = injetar_relogio com quarta 2026-10-14 14:00 BRT (dia útil confirmado); `fechar_pregao(monkeypatch)` = sábado 2026-10-17 14:00. Patch SÓ em `app.pregao.in_market_hours` — o wrapper de agent e as rotas de main leem em tempo de chamada; chamadas com `now` explícito seguem a função original (os testes de calendário em test_agent.py:350-413 continuam válidos). Docstring: NUNCA usar B3_DEV_MERCADO_ABERTO como muleta.
    (d) server/tests/test_execucao_fora_pregao.py com os casos do behavior (parametrize onde couber), RED antes de (b). Nota: testes ANTIGOS do motor podem ficar vermelhos dependendo da hora até a Tarefa 1b sanear o relógio — por isso o verify desta tarefa roda só os arquivos abaixo.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/server && FAIL=""; for f in tests/test_execucao_fora_pregao.py tests/test_skill_ref.py tests/test_timing.py tests/test_entrada_automatica.py; do ./.venv/bin/python -m pytest -q "$f" >/dev/null 2>&1 || FAIL="$FAIL $f"; done; echo "FALHAS:${FAIL:- nenhuma}"; test -z "$FAIL"</automated>
  </verify>
  <done>F1–F6, A1–A3, T1–T4, D1–D4 e S1 passam; portão presente em `_run_cycle_inner` com o texto `if not in_market_hours():`; dedupe com chave `acao:<ticker>`.</done>
</task>

<task type="auto" tdd="true">
  <name>Tarefa 1b (Leva A): vencimento fora do portão + aviso GENÉRICO de opção (D2-emenda) + saneamento do relógio, plugins e guardiões</name>
  <files>server/app/agent.py, server/tests/test_execucao_fora_pregao.py, server/tests/test_fase3_operador.py, (+ arquivos de teste confirmados pela descoberta, adicionando só o fixture)</files>
  <behavior>
    Mesmo relógio injetado da 1a. `option_quotes_getter` fake que registra cada chamada.
    - T5 spy em `agent._avaliar_opcoes` → fechado é chamado com `somente_vencimento=True`, aberto com False.
    - V1 vencimento lastreado (CALL coberta vendida, expiration sexta 2026-10-16) com ciclo na sexta 17:20 (fechado) → liquida com o `underlyingPrice` do payload fake, `store.liquidar_lastreada_vencida` chamado uma vez, `qtyTravada` destravada, evento tag "protecao-opcao".
    - V2 mesmo cenário com ciclo no sábado 2026-10-17 14:00 → liquida com o mesmo preço do payload (último pregão = sexta).
    - V3 vencimento legado (sem lastro) expirando sexta, ciclo sábado → `close_option_vencida` pelo intrínseco do payload.
    - V4 sexta 2026-10-16 09:30 → NÃO liquida (o dado disponível é da véspera); mesmo ciclo às 10:30 → liquida (regra de hoje).
    - V5 opção NÃO vencida com stop 1.00 e prêmio 0.80, fechado → não vende, stop e trailing intactos, `sell_option` não chamado; mesma posição em pregão → vende (regressão).
    - V6 fechado com opção não vencida e nenhuma vencida → `option_quotes_getter` NÃO é chamado.
    - V7 fechado, opção não vencida (sem lastro) com stop e/ou alvo definidos → exatamente 1 aviso com chave `opcao:<contractId>` e texto `execucao_fora_pregao_txt(modo, "aviso_opcao", contrato=<contractId>)` nos dois modos; o texto não contém "R$" nem "atingido"; `option_quotes_getter` NÃO chamado; nada vendido, stop/alvo intactos.
    - V8 fechado, opção não vencida SEM stop e SEM alvo → nenhum aviso; `option_quotes_getter` NÃO chamado.
    - V9 segundo ciclo fechado no mesmo dia com a opção do V7 → nenhum aviso novo; dia seguinte fechado → novo aviso.
    - B2 ação PETR4 com stop atingido e opção de PETR4 com stop definido, fechado → 2 avisos (chaves `acao:PETR4` e `opcao:<id>`); segundo ciclo no mesmo dia → nenhum aviso novo.
  </behavior>
  <action>
    (a) Vencimento é evento de calendário, não ordem (ajuste do coordenador, 2026-10-13). `_avaliar_opcoes` ganha `somente_vencimento: bool = False`. Com True: (1) filtra ANTES de `_option_quotes` só as posições com `expiration <= hoje` — se não sobrar nenhuma, retorna sem chamar o provedor; (2) para expiration == hoje e hora BRT < `pregao.ABERTURA`, pula (o pregão do vencimento ainda não aconteceu; o spot seria da véspera); (3) executa os DOIS ramos de vencimento existentes (lastreado :563-590 e legado :598-606) byte a byte, mesma regra de preço (spot do payload no ciclo), mesmo `_bump_ops`, mesmos eventos; (4) nunca entra no trailing/stop/alvo de opção (:607 em diante) — `continue` cedo, sem duplicar ramos. Com False: inalterado. No ramo fechado de `_run_cycle_inner`, depois de `_avisar_fora_pregao`, `executed = await _avaliar_opcoes(conn, scope, ag, par, option_quotes_getter, 0, eventos, app_mode=app_mode, somente_vencimento=True)` e o retorno passa a carregar `executed`.
    (b) Per D2-emenda (LOCKED, Alex 2026-10-14): `_run_cycle_inner` passa `optionPositions` (já lidas do kv, sem I/O) a `_avisar_fora_pregao`. Para cada posição de opção NÃO vencida (`expiration > hoje`, mesma `_today()`) com `stop` e/ou `alvo` definidos (lastreada não tem, D-1), emitir aviso GENÉRICO com `skill_ref.execucao_fora_pregao_txt(modo, "aviso_opcao", contrato=<id>)`, evento `{"time", "kind": "warn", "t": underlying, "text"}` sem `tag`, dedupe com chave `"opcao:" + id` no MESMO kv `avisoForaPregao`. Sem preço, sem `_gatilho_saida`, sem `option_quotes_getter`, sem cache: nenhuma leitura de prêmio/cota de opção fora do pregão. Provedores de opções e main.py intocados por esta tarefa.
    (c) Descoberta dos testes dependentes do relógio: criar em $TMPDIR o plugin `relogio_fechado_plugin.py` cujo `pytest_configure` troca `app.pregao.in_market_hours` por função que devolve False quando `now is None` e a dev flag está desligada (senão delega à original); e `relogio_aberto_plugin.py` simétrico (True em quarta 14:00 via instante injetado). Rodar a suíte do backend com cada plugin (`cd server && PYTHONPATH=".:$TMPDIR" ./.venv/bin/python -m pytest -q -p relogio_fechado_plugin`), DEPOIS do portão (Tarefa 1a) e de (a)/(b) desta tarefa. Cada teste que falhar só no plugin fechado é dependente do relógio: adicionar no arquivo um fixture de módulo `@pytest.fixture(autouse=True) def _pregao_aberto(monkeypatch): abrir_pregao(monkeypatch)` importado de `.relogio_pregao`, com comentário "2026-10-13 (quick 261013-vai): o ciclo não executa fora do pregão; este arquivo testa execução, então fixa o relógio em pregão". Candidatos já mapeados (o executor da 1a pode ter visto alguns vermelhos): test_agent.py, test_agent_options.py, test_agent_modo_estudo.py, test_opcoes_lastreadas_vencimento.py, test_push_payload.py, test_push_prefs_classes.py, test_fase3_operador.py (Leva A) e, após a Tarefa 2, os de rotas de opções do frontmatter. Testes que já fazem monkeypatch próprio de `agent.in_market_hours` (ex.: test_fase3_kill_switch_duracao.py) continuam valendo — o patch por teste sobrepõe o fixture. Nada é apagado; assert existente não é afrouxado.
    (d) Guardião textual test_fase3_operador.py:255-270 (`test_laco_avisa_dentro_do_pregao`): manter o teste e trocar o split por uma âncora robusta — recortar primeiro o corpo de `async def scheduler_loop` e só então dividir por "if not kill_switch_on() and in_market_hours():" — com nota "2026-10-13 (quick 261013-vai): o portão novo de _run_cycle_inner usa outro texto; a âncora passa a ser o corpo do scheduler para não depender da ordem das funções no arquivo". Acrescentar no mesmo arquivo `test_portao_de_pregao_antes_de_qualquer_execucao_no_ciclo` (guardião novo): no corpo de `_run_cycle_inner`, o índice de "if not in_market_hours():" é menor que os de "store.set_position(", "store.sell(", "_avaliar_entradas(" e "snapshot_getter("; e dentro do ramo fechado a única chamada a `_avaliar_opcoes(` carrega `somente_vencimento=True`. Em `_avaliar_opcoes`, o `continue` de `somente_vencimento` aparece antes de "nivel_trailing(" e de "store.sell_option(". Acrescentar também: no ramo fechado não existe chamada a `option_quotes_getter(` fora de `_avaliar_opcoes(..., somente_vencimento=True)`, e `_avisar_fora_pregao` não referencia `option_quotes_getter`.
    (e) Acrescentar T5, V1–V9 e B2 ao test_execucao_fora_pregao.py, RED antes de (a)/(b).
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/server && FAIL=""; for f in tests/test_execucao_fora_pregao.py tests/test_fase3_operador.py tests/test_agent.py tests/test_agent_options.py tests/test_agent_modo_estudo.py tests/test_opcoes_lastreadas_vencimento.py tests/test_push_payload.py tests/test_push_prefs_classes.py tests/test_fase3_kill_switch_duracao.py tests/test_entrada_automatica.py tests/test_ciclo_imediato_apos_carteira.py tests/test_skill_ref.py tests/test_timing.py; do ./.venv/bin/python -m pytest -q "$f" >/dev/null 2>&1 || FAIL="$FAIL $f"; done; for p in relogio_fechado_plugin relogio_aberto_plugin; do PYTHONPATH=".:$TMPDIR" ./.venv/bin/python -m pytest -q -p "$p" tests/test_agent.py tests/test_agent_options.py tests/test_agent_modo_estudo.py tests/test_opcoes_lastreadas_vencimento.py tests/test_push_payload.py tests/test_push_prefs_classes.py tests/test_fase3_operador.py tests/test_execucao_fora_pregao.py >/dev/null 2>&1 || FAIL="$FAIL plugin:$p"; done; echo "FALHAS:${FAIL:- nenhuma}"; test -z "$FAIL"</automated>
  </verify>
  <done>T5, V1–V9 e B2 passam; os arquivos de teste do motor passam com o relógio forçado fechado E forçado aberto; guardião textual atualizado com nota datada e guardião novo de ordem do portão presente; nenhum teste apagado; nenhuma chamada ao provedor de opções fora do pregão exceto para posição vencida.</done>
</task>

<task type="auto" tdd="true">
  <name>Tarefa 2 (Leva A): run-now e /api/cycle com "mercado fechado" + 409 nas 6 rotas de execução de opções + testes de rota</name>
  <files>server/app/main.py, server/tests/test_execucao_fora_pregao_rotas.py, (+ fixture `_pregao_aberto` nos testes de rotas de opções confirmados pela descoberta)</files>
  <behavior>
    Rotas via TestClient no padrão de server/tests/test_ciclo_imediato_apos_carteira.py (`_cliente` com B3_DB_PATH temporário, reimport de app.main, `/api/auth/register`) e, para opções, o de test_opcoes_lastreadas_rotas.py (options_provider_mock + appMode operador). Relógio via `.relogio_pregao`.
    - R1 PUT /api/position/PETR4 fechado com stop 38 e cotação 37.5: 200, stop gravado no estado; depois `await agent.run_cycle_for(..., origem="imediato")` fechado → posição continua, aviso no Diário. `_disparar_ciclo_imediato` continua sendo chamado (spy, como em test_ciclo_imediato_apos_carteira.py).
    - R2 POST /api/agent/run-now fechado: 200, `iniciado is False`, `mercadoFechado is True`, `mensagem == skill_ref.execucao_fora_pregao_txt(modo, "ciclo_fechado", abertura="10:00")`; spy de `main.agent_mod.run_cycle_for` NÃO chamado; Diário recebe a mesma frase (kind info). Aberto: comportamento de hoje (`iniciado is True`). Kill-switch ligado continua 409 (prioridade inalterada).
    - R3 POST /api/cycle fechado: 200, `mercadoFechado is True`, `mensagem` canônica, `quotes` presente, posições intactas.
    - R4 para cada uma das 6 rotas (/api/options/buy, /sell, /curadoria/abrir-collar, /lastreada/abrir, /lastreada/abrir-collar, /lastreada/fechar), conta Operador, fechado: 409; `detail.code == "mercado_fechado"`, `detail.message` contém "10:00", `detail.action` presente; `main.options_provider.get_options` trocado por função que falha o teste se chamada (prova: nenhuma cota de mydata gasta). /buy e /sell logados gravam no history uma entrada `status:"rejeitada"` com o motivo (tipo COMPRA/VENDA).
    - R5 /lastreada/abrir e /lastreada/fechar em Modo Estudo fechado → 403 (ordem de checagem preservada).
    - R6 PUT /api/options/position/{id} fechado → 200 (registrar stop/alvo de opção sempre permitido).
    - R7 guardião estrutural: no fonte de main.py, recortando cada handler pelo decorator, `_recusar_execucao_fora_do_pregao(` aparece exatamente nos 6 handlers de execução e em nenhum `@app.get` nem em /api/options/position, /proposta, /vigias, /curadoria (GET), /curadoria/narrativa, /escada*, /anatomia, /tecnico; e aparece ANTES de `options_provider.get_options` / `_curadoria_scan_posicao` / `opcoes_lastreadas.propor` em cada handler.
    - R8 com pregão aberto, uma rota de opções (buy) segue 200 como hoje (regressão).
  </behavior>
  <action>
    Per D2 e D4, em main.py:
    (a) Helper `_recusar_execucao_fora_do_pregao(scope, tipo=None, t=None, qty=None)`: import local de pregao (padrão do arquivo); se `pregao.in_market_hours()` retorna sem fazer nada; senão lê o appMode do config do escopo para escolher o modo, monta `abertura = "%02d:%02d" % pregao.ABERTURA`, e — quando `scope is not None and tipo` — chama `store.registrar_rejeicao(_conn, tipo, t, qty, None, <opcao_bloqueada>, user_id=scope, origem="manual")`; então levanta `HTTPException(409, {"code": "mercado_fechado", "message": skill_ref.execucao_fora_pregao_txt(modo, "opcao_bloqueada", abertura=abertura), "action": skill_ref.execucao_fora_pregao_txt(modo, "opcao_bloqueada_acao"), "abertura": abertura})`. Comentário de decisão: autoridade é o servidor (T-02-10, mesmo princípio do /api/buy), 409 e não pendente porque ordem pendente de opção está fora de escopo (CONTEXT).
    (b) Chamar o helper nas 6 rotas, ANTES de qualquer consulta ao provedor/re-derivação e DEPOIS do 403 de Modo Estudo onde ele existe: /api/options/buy logo após a validação 400 de contrato (tipo "COMPRA", t=contractSymbol, qty); /api/options/sell logo após achar `pos` (tipo "VENDA", t=contractSymbol); /curadoria/abrir-collar, /lastreada/abrir, /lastreada/abrir-collar, /lastreada/fechar sem `tipo` (409 sem linha no history — estrutura/proposta ainda não é ordem de uma perna; registrar como discretion no SUMMARY). Não tocar rotas de leitura nem PUT /api/options/position.
    (c) POST /api/agent/run-now: depois do 409 de kill-switch, se `not pregao.in_market_hours()`: não criar a task; `store.push_agent_log` com a frase `ciclo_fechado` (kind "info"); responder `{"ok": True, "iniciado": False, "mercadoFechado": True, "mensagem": <ciclo_fechado com abertura>}`. Aberto: inalterado.
    (d) POST /api/cycle: manter a chamada a `run_cycle_for` (o portão interno gera o aviso deduplicado); se o dict retornado tiver `mercadoFechado`, acrescentar `out["mercadoFechado"] = True` e `out["mensagem"] = <ciclo_fechado>`; `out["quotes"]` continua (remarcação é leitura).
    (e) `_disparar_ciclo_imediato` e PUT /api/position: SEM mudança de código (o portão está no motor) — só comentário curto citando a 261013-vai.
    (f) Escrever test_execucao_fora_pregao_rotas.py (RED antes de a–d). Em seguida rodar a descoberta da Tarefa 1b com o plugin fechado sobre os arquivos de rota de opções do frontmatter (test_opcoes_lastreadas_rotas, test_opcoes_collar_rota, test_curadoria_collar_rota, test_gate_liquidez_rotas, test_fase5_rejeicao_rotas, test_opcoes_cota_reserva_rotas, test_opcao_descoberto_gate, test_fuso_dias_ate_vencimento, test_opcoes_anatomia_rota, test_mydata_budget_prioridade, test_ciclo_imediato_apos_carteira, test_rotas_fase4, test_ordens_pendentes_*) e adicionar o fixture `_pregao_aberto` com a nota datada só nos que falharem. Arquivos que já fazem monkeypatch de `pregao.in_market_hours` por teste ficam como estão.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/server && FAIL=""; for f in tests/test_execucao_fora_pregao_rotas.py tests/test_execucao_fora_pregao.py tests/test_ciclo_imediato_apos_carteira.py tests/test_opcoes_lastreadas_rotas.py tests/test_opcoes_collar_rota.py tests/test_curadoria_collar_rota.py tests/test_gate_liquidez_rotas.py tests/test_fase5_rejeicao_rotas.py tests/test_opcoes_cota_reserva_rotas.py tests/test_opcao_descoberto_gate.py tests/test_fuso_dias_ate_vencimento.py tests/test_opcoes_anatomia_rota.py tests/test_mydata_budget_prioridade.py tests/test_rotas_fase4.py tests/test_adr013_cobertura_rotas.py; do ./.venv/bin/python -m pytest -q "$f" >/dev/null 2>&1 || FAIL="$FAIL $f"; done; for p in relogio_fechado_plugin relogio_aberto_plugin; do PYTHONPATH=".:$TMPDIR" ./.venv/bin/python -m pytest -q -p "$p" >/dev/null 2>&1 || FAIL="$FAIL suite-plugin:$p"; done; echo "FALHAS:${FAIL:- nenhuma}"; test -z "$FAIL"</automated>
  </verify>
  <done>R1–R8 passam; a suíte do backend inteira passa com o relógio forçado fechado e forçado aberto (prova de que nenhum teste depende da hora real); nenhuma rota de leitura ganhou o 409. Fim da Leva A: o orquestrador roda a suíte canônica antes da Leva B.</done>
</task>

<!-- ============================ CORTE DE EXECUÇÃO — LEVA B (front/iOS) ============================ -->

<task type="auto" tdd="true">
  <name>Tarefa 3 (Leva B): espelho do vocabulário + portão no deviceStore.cycle + setInterval/A.cycle/A.* de opções no App.jsx + guardiões</name>
  <files>web/src/copy.js, web/src/persistence.js, web/src/evolucaoPosicao.js, web/src/App.jsx, web/tests/test_vocabulario_espelho.mjs, web/tests/test_execucao_fora_pregao.mjs</files>
  <behavior>
    test_execucao_fora_pregao.mjs no padrão de web/tests/test_carteira_nativa_sincroniza.mjs (CapacitorCustomPlatform ios, localStorage em memória, fetch stub), SEM sessão, posição PETR4 stop 38, `agent.autonomous = true`, /api/quotes devolvendo 37.5:
    - C1 /api/market/status `{aberto:false, abertura:"10:00"}` → `store.cycle()` não vende (posição e cash iguais, nenhum history VENDA), devolve `mercadoFechado === true` e `mensagem` = execucaoForaPregaoTxt(modo,"ciclo_fechado",{abertura:"10:00"}), `quotes` presentes, `agent.events[0].text` = aviso_diario.
    - C2 segundo ciclo fechado no mesmo dia BRT → nenhum aviso novo (dedupe per B2 em `doc.agent.avisoForaPregao = {data: hojeBRT(), chaves}` com chave `acao:PETR4`; uma chave `opcao:X` pré-existente no doc NÃO suprime o aviso da ação PETR4 — mesmo formato de chave do servidor).
    - C3 /api/market/status responde 500 (ou fetch lança) → não vende; `mercadoFechado === true`, mensagem = status_indeterminado.
    - C4 `{aberto:true}` → vende como hoje (evento "Protecao automatica").
    - C5 opção NÃO vencida com stop atingido e mercado fechado → não vende (posição de opção permanece).
    - C6 CALL coberta lastreada vencida (expiration = sexta) com mercado fechado no sábado e com status indeterminado → liquida pelo intrínseco do `underlyingPrice` da cadeia (regra de hoje), destrava `qtyTravada`. Legado vencido idem, só com `autonomous` (regra de hoje).
    - H1 `horaMinutoBRT` (nova, exportada de evolucaoPosicao.js ao lado de `hojeBRT`, mesma técnica de fuso): `horaMinutoBRT(new Date("2026-10-16T12:30:00Z"))` → "09:30"; `horaMinutoBRT(new Date("2026-10-17T01:00:00Z"))` → "22:00" com `hojeBRT` do mesmo instante = "2026-10-16"; meia-noite BRT ("2026-10-16T03:00:00Z") → "00:00".
    - C8 sem `abertura` na resposta de /api/market/status `{aberto:false}` → mensagem = `ciclo_fechado_sem_hora`; nenhum texto devolvido contém "?".
    - C9 mercado fechado, opção não vencida com stop e/ou alvo → 1 aviso genérico `aviso_opcao` (chave `opcao:<id>` em `doc.agent.avisoForaPregao`), sem chamada a /api/options/* para ela; segundo ciclo no mesmo dia → nenhum aviso novo; opção sem stop/alvo → nenhum aviso (D2-emenda, mesma regra do servidor).
    - C7 relógio fixado (Date fake) em quinta 22:00 BRT (= sexta 01:00 UTC) com expiration sexta → NÃO liquida (correção do `hoje` UTC para `hojeBRT()`); sexta 09:30 BRT → não liquida; sexta 10:30 → liquida.
    - Estáticos sobre App.jsx (recorte por âncora, não arquivo inteiro): existe `mercadoRef.current = mercado`; o callback do setInterval do modo autônomo só chama `cycleRef.current()` com `mercadoRef.current && !mercadoRef.current.erro && mercadoRef.current.aberto`; `A.cycle` usa `s.mercadoFechado` para escolher entre `s.mensagem` e "Ciclo executado."; cada um de buyOption/sellOption/abrirLastreada/abrirCollar/fecharLastreada/executarCandidatoCurado referencia `mercadoRef.current` antes da chamada ao store; `rodarAgora` continua exibindo `s.mensagem`; `applyProposal`/stop-alvo NÃO referencia `mercadoRef` (stop/alvo nunca vetados).
  </behavior>
  <action>
    (a) copy.js — per D2/D4, `execucaoForaPregao` em COPY.estudo e COPY.operador, espelho BYTE A BYTE de skill_ref.EXECUCAO_FORA_PREGAO (educacional↔estudo), com comentário "Quick 261013-vai (2026-10-13): espelho byte a byte de skill_ref.EXECUCAO_FORA_PREGAO". Exportar `execucaoForaPregaoTxt(mode, chave, vals)` no padrão de `retornoAcumuladoTxt` (substitui {ticker}/{motivo}/{abertura}/{contrato}; placeholder sem valor lança Error — nunca devolve "?" —; chave desconhecida lança Error; falha alta, igual ao Python).
    (b) test_vocabulario_espelho.mjs — acrescentar "EXECUCAO_FORA_PREGAO" em DICTS, `EXECUCAO_FORA_PREGAO: "execucaoForaPregao"` em CHAVE_JS e as 10 chaves em CHAVES_ESPERADAS, com nota "2026-10-13 (quick 261013-vai): EXECUCAO_FORA_PREGAO entra no mesmo guardião". Nenhuma asserção existente alterada.
    (c) persistence.js — per D3, no começo de `deviceStore.cycle()` (depois de `ensure()`): consultar `api.marketStatus()` em try/catch; estado = "aberto" só se a resposta tem `aberto === true` e não tem `erro`; `aberto === false` = "fechado"; qualquer outra coisa/exceção = "indeterminado". Buscar as cotações como hoje (remarcação é leitura; falha de cotação no ramo não aberto não derruba o ciclo). Extrair o laço de opções existente para uma função local `avaliarOpcoesLocal({ somenteVencimento })` sem mudar os ramos; trocar `const hoje = new Date().toISOString().slice(0, 10)` por `hojeBRT()` (corrige a liquidação um dia antes entre 21:00 e 24:00 BRT — comentário datado); com `somenteVencimento`, só considera posições com `expiration <= hoje`, pula expiration == hoje antes das 10:00 BRT (via `horaMinutoBRT()`, exportada de evolucaoPosicao.js ao lado de `hojeBRT` — caso H1), busca cadeia SÓ das posições vencidas e nunca entra no stop/alvo de opção. Se não "aberto": NÃO executar stop/alvo de ações nem stop/alvo de opção; o vencimento roda via `avaliarOpcoesLocal({ somenteVencimento: true })` tanto em "fechado" quanto em "indeterminado" (é calendário, não depende do status do pregão; mesma regra de preço de hoje); se "fechado", para cada posição com preço e stop/alvo atingido (mesmas comparações já usadas no laço: `pos.stop != null && price <= pos.stop` / `pos.alvo != null && price >= pos.alvo`, stop vence) emitir 1 aviso por chave `acao:<ticker>` por dia BRT (dedupe em `doc.agent.avisoForaPregao = {data, chaves}`, data via `hojeBRT()` de ./evolucaoPosicao.js; e, para cada opção não vencida com stop e/ou alvo, o aviso genérico `aviso_opcao` com chave `opcao:<id>` — C9, D2-emenda, sem nenhuma leitura de prêmio) com o texto de `execucaoForaPregaoTxt(modo, "aviso_diario", {ticker, motivo})`, modo = `doc.config.appMode === "operador" ? "operador" : "estudo"`; se "indeterminado", um evento warn com `status_indeterminado`. `write()`; retornar `pub()` + `quotes` + `mercadoFechado: true` + `mensagem` (`ciclo_fechado` com `abertura` da resposta; sem `abertura`, `ciclo_fechado_sem_hora`; indeterminado, `status_indeterminado`). Ramo aberto: inalterado. Comentário de decisão citando D3, o espelho com agent._run_cycle_inner e o porquê de indeterminado não executar (princípio 4). Nenhum método novo nos stores (paridade: `cycle` já existe nos dois; o serverStore recebe o mesmo par `mercadoFechado/mensagem` do servidor). Não importar App/React.
    (d) App.jsx (Grep + Read por offset): logo após o `useState` de `mercado`, `const mercadoRef = useRef(null); mercadoRef.current = mercado;` com comentário (ref para não tocar as deps do useMemo de A, guardadas por test_wiring_deps.mjs). setInterval do modo autônomo: só chama `cycleRef.current()` se o pregão está confirmado aberto pela mesma expressão da guarda de notificações (~10617). `A.cycle`: se `s.mercadoFechado`, `flash(s.mensagem)`; senão "Ciclo executado." como hoje. Em buyOption/sellOption/abrirLastreada/abrirCollar/fecharLastreada: primeira linha dentro do `try`, se `mercadoRef.current && !mercadoRef.current.erro && mercadoRef.current.aberto === false`, `throw new Error(...)` com `execucaoForaPregaoTxt(<modo do cp>, "opcao_bloqueada", { abertura })` quando `mercadoRef.current.abertura` existe e `"opcao_bloqueada_sem_hora"` quando não existe (W2: nunca "?") — o catch existente faz o flash (mesmo canal do 409 do servidor). Em executarCandidatoCurado, o mesmo throw antes de `executarCandidato` (o erro já é relançado ao painel do card por desenho). Status indeterminado NÃO bloqueia o caminho manual: o servidor é a autoridade e responde 409 (D4). `rodarAgora` sem mudança (já mostra `s.mensagem`). Não tocar applyProposal/putPosition/openStopAlvo.
    (e) Escrever test_execucao_fora_pregao.mjs (RED antes de c–d).
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && FAIL=""; for t in tests/test_execucao_fora_pregao.mjs tests/test_vocabulario_espelho.mjs tests/test_wiring_deps.mjs tests/test_api_parity.mjs tests/test_fase3_paridade_stores_generica.mjs tests/test_carteira_nativa_sincroniza.mjs tests/test_agente_modo_estudo_ui.mjs tests/test_carteira_lastro_ui.mjs tests/test_cartao_v6_aberto.mjs tests/test_config_debounce_flush.mjs; do node "$t" >/dev/null 2>&1 || FAIL="$FAIL $t"; done; npx vite build >/dev/null 2>&1 || FAIL="$FAIL vite-build"; echo "FALHAS:${FAIL:- nenhuma}"; test -z "$FAIL"</automated>
  </verify>
  <done>C1–C9, H1 e os estáticos passam; espelho skill_ref↔copy.js travado pelo guardião cruzado; paridade dos stores intacta (nenhum método novo); `npx vite build` ok.</done>
</task>

<task type="auto" tdd="true">
  <name>Tarefa 4 (Leva B): bloqueio com aviso nos botões de execução da aba de Opções + guardião</name>
  <files>web/src/opcoes/OpcoesScreen.jsx, web/src/opcoes/ConfirmarEstrutura.jsx, web/src/opcoes/ExecutarProposta.jsx, web/src/opcoes/SecaoAnalisar.jsx, web/src/opcoes/CuradoriaEstruturas.jsx, web/src/opcoes/AbaRecomendadas.jsx, web/src/opcoes/CandidatoOpcao.jsx, web/src/opcoes/PropostaLastreada.jsx, web/src/opcoes/PernasAbertas.jsx, web/tests/test_opcoes_mercado_fechado_ui.mjs</files>
  <behavior>
    test_opcoes_mercado_fechado_ui.mjs (leitura de fonte, sem build):
    - OpcoesScreen.jsx deriva `bloqueioMercado` de `mercadoAberto === false` (nunca de null/erro) usando `execucaoForaPregaoTxt` com "botao_bloqueado" quando há `ctx.mercado.abertura`, senão "botao_bloqueado_sem_hora", e passa `bloqueioMercado=` a ConfirmarEstrutura, os dois PernasAbertas, SecaoAnalisar, AbaRecomendadas (ou onde CuradoriaEstruturas for montada), CandidatoOpcao e PropostaLastreada.
    - SecaoAnalisar repassa a ExecutarProposta; AbaRecomendadas repassa a CuradoriaEstruturas.
    - Cada componente de execução: inclui `bloqueioMercado` na condição de trava do botão de executar/abrir/fechar/encerrar, renderiza o texto com `id` e o botão aponta `aria-describedby` para ele; nenhum `disabled=` NOVO além dos que já existiam (contagem de `disabled=` por arquivo igual à de antes, registrada no próprio teste com a data).
    - Botões de stop/alvo/plano em PernasAbertas e PropostaLastreada não referenciam `bloqueioMercado`.
    - Grep: nenhuma ocorrência de "Mercado fechado" hardcoded nos arquivos de opcoes/ (texto vem só de copy.js).
  </behavior>
  <action>
    Per D4. Antes de editar cada arquivo, `grep -ln "<NomeDoArquivo>" web/tests/*.mjs` e leia as asserções que tocam o botão de execução — manter byte a byte os trechos que elas exigem (ex.: `disabled={travado}`, `onClick={executar}`).
    (a) OpcoesScreen.jsx: abaixo de `mercadoAberto` (:793), `const bloqueioMercado = mercadoAberto === false ? execucaoForaPregaoTxt(mode, ...) : null;` (usar a variável de modo que o arquivo já usa para cp/opcoesEscadaTxt) e repassar como prop nos pontos de montagem listados. Status desconhecido (null) não bloqueia — o servidor recusa com 409 e o erro aparece pelo canal existente.
    (b) Nos componentes com lock em variável e `disabled={var}` nativo (ConfirmarEstrutura `travado`, ExecutarProposta `travado`, CuradoriaEstruturas `executarTravado`): acrescentar `|| !!bloqueioMercado` NA DEFINIÇÃO da variável (o atributo `disabled={...}` fica byte-idêntico) e renderizar, perto do botão, `<p id={idUnico} role="status">` com o texto, ligado ao botão por `aria-describedby`. CandidatoOpcao/PropostaLastreada (`disabled={busy || degradado}`): mesma técnica — introduzir uma const `travadoExec = busy || degradado || !!bloqueioMercado` só se nenhum guardião exigir o texto literal `disabled={busy || degradado}`; se exigir, usar o padrão aria-disabled (abaixo) para o motivo de mercado e deixar o disabled existente intacto. PernasAbertas (encerrar com confirmação em 2 passos, sem disabled nativo): padrão aria-disabled do repo — `aria-disabled={bloqueioMercado ? "true" : undefined}`, onClick que não executa quando bloqueado, motivo visível e `aria-describedby` (mesmo padrão de test_estrutura_card_ui.mjs:67). Estilo do texto: tokens existentes (T.warn, TIPO.corpo/label), sem hex.
    (c) Não bloquear: stop/alvo/plano, leitura de cadeia/escada/payoff/proposta, botões de navegação. Legado OpcaoContrato em App.jsx fica protegido pelo throw da Tarefa 3 (flash com a frase), sem mudança visual — registrar no SUMMARY.
    (d) Escrever o guardião antes (RED), depois implementar.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && FAIL=""; for t in tests/test_opcoes_mercado_fechado_ui.mjs $(grep -lE "ConfirmarEstrutura|ExecutarProposta|SecaoAnalisar|CuradoriaEstruturas|AbaRecomendadas|CandidatoOpcao|PropostaLastreada|PernasAbertas|OpcoesScreen" tests/*.mjs); do node "$t" >/dev/null 2>&1 || FAIL="$FAIL $t"; done; node tests/test_execucao_fora_pregao.mjs >/dev/null 2>&1 || FAIL="$FAIL tests/test_execucao_fora_pregao.mjs"; npx vite build >/dev/null 2>&1 || FAIL="$FAIL vite-build"; echo "FALHAS:${FAIL:- nenhuma}"; test -z "$FAIL"</automated>
  </verify>
  <done>Com `ctx.mercado.aberto === false`, todo botão de execução de opções da aba fica travado com "Mercado fechado — abre às HH:MM" visível e ligado por aria-describedby; stop/alvo intactos; guardiões das telas de opções passam; vite build ok. Fim da Leva B: o orquestrador roda `npx cap copy ios` e a suíte canônica.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| cliente → rotas de execução de opções | corpo e momento da requisição são controlados pelo cliente |
| cliente → run-now / /api/cycle / PUT /api/position | disparo de ciclo a qualquer hora |
| iPhone (deviceStore) → /api/market/status | status pode falhar/mentir por rede; o ciclo local executa no aparelho |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-vai-01 | Tampering | 6 rotas de execução de opções | mitigate | estado do pregão vem SÓ de `pregao.in_market_hours()` no servidor (nunca do corpo); helper chamado antes do provedor; guardião estrutural R7 |
| T-vai-02 | Elevation | run-now / /api/cycle / ciclo imediato | mitigate | portão dentro de `_run_cycle_inner` — qualquer chamador atual ou futuro herda; guardião de ordem do portão (Tarefa 1b) |
| T-vai-03 | Spoofing | deviceStore.cycle com status indeterminado | mitigate | indeterminado = não executa (C3); só `aberto === true` explícito libera |
| T-vai-04 | Denial of Service | spam de PUT/run-now fora do pregão enchendo o Diário | mitigate | aviso deduplicado por (tipo, id)/dia (kv avisoForaPregao); ramo fechado não grava resumo; run-now fechado não cria task |
| T-vai-05 | Information Disclosure | detail do 409 | accept | só calendário público (horário de abertura) e texto canônico; nada de carteira |
| T-vai-06 | Repudiation | rejeição de ordem manual de opção | mitigate | /buy e /sell registram `status:"rejeitada"` com motivo no history (estrutura multi-perna: só 409, decisão registrada) |
</threat_model>

<verification>
Leva A: verify das Tarefas 1a, 1b e 2 (inclui a suíte do backend sob relógio forçado fechado e aberto). Depois, o ORQUESTRADOR roda `bash scripts/executar.sh --testes` fora do sandbox.
Leva B: verify das Tarefas 3 e 4 + `npx vite build`. Depois, o orquestrador roda `npx cap copy ios` e a suíte canônica.
Sem publicar, sem push, sem bump, sem worktree, sem dependência nova.
</verification>

<success_criteria>
- Nenhuma execução simulada de ordem (stop/alvo/trailing/alvo dinâmico de ação, stop/alvo/trailing de opção, entrada automática) acontece fora de `in_market_hours()` no servidor ou no iPhone; liquidação de vencimento segue como evento de calendário (nunca antes da abertura do dia do vencimento); registrar stop/alvo sempre funciona.
- Aviso único por (tipo, id)/dia no Diário, por modo, sem push; aviso de opção genérico e sem preço (D2-emenda); execução na abertura com o preço corrente (gap real).
- run-now e /api/cycle respondem "mercado fechado" e o front mostra a frase; 6 rotas de opções 409 com detail acionável; UI de Opções travada com motivo visível.
- Suíte do backend independente do relógio real (passa forçada fechada e aberta); espelho skill_ref↔copy.js travado; paridade dos stores intacta; guardiões alterados com nota datada, nenhum apagado.
</success_criteria>

<output>
Criar `.planning/quick/261013-vai-execucao-fora-do-pregao/261013-vai-SUMMARY.md` ao final, com: lista exata dos arquivos de teste que receberam o fixture `_pregao_aberto` (resultado da descoberta), decisões de discretion aplicadas e limitações conhecidas — obrigatoriamente: (1) o vencimento de opção liquida com o spot do ativo-objeto lido no 1º ciclo que o alcança (no scheduler, o 1º ciclo do pregão do dia do vencimento, ~10:00) — regra atual, opção A; liquidar pelo fechamento do dia do vencimento (ADR-005) é follow-up; (2) o aviso de opção fora do pregão é genérico (não diz se o stop/alvo seria atingido, por desenho — D2-emenda); (3) estruturas multi-perna recusadas com 409 não ganham linha de rejeição no history.
</output>
