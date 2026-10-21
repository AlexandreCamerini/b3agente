---
phase: quick-261021-spd
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - server/app/agent.py
  - server/tests/test_agent_lastro_ciclo.py
  - web/src/persistence.js
  - web/tests/test_ciclo_iphone_delega_servidor.mjs
autonomous: true
requirements: [QUICK-261021-SPD-1, QUICK-261021-SPD-2]

must_haves:
  truths:
    - "Com conta (sync.hasSession()), Executar ciclo no iPhone roda o ciclo NO SERVIDOR (POST /api/cycle) e não faz nenhuma venda local nem chama /api/sell"
    - "Com conta, o Diário/carteira do iPhone refletem o que o servidor devolveu (posições, caixa, histórico, eventos do agente)"
    - "Sem conta, stop/alvo em posição 100% travada como lastro não lança exceção: vira 1 aviso warn e o ciclo segue para as próximas posições e opções"
    - "Sem conta, o evento 'vendido' só aparece se a venda local de fato aconteceu"
    - "No servidor, stop rompido em posição 100% travada não chama store.sell, não grava rejeição, não consome teto, e gera 1 só aviso por posição por dia BRT"
    - "No servidor, posição parcialmente travada vende só a parte livre e o evento cita a quantidade vendida"
  artifacts:
    - path: "server/app/agent.py"
      provides: "pré-checagem de lastro em _run_cycle_inner + aviso deduplicado"
      contains: "store.qty_livre("
    - path: "web/src/persistence.js"
      provides: "deviceStore.cycle delega ao servidor com sessão; caminho local tolerante a lastro"
      contains: "api.cycle()"
    - path: "server/tests/test_agent_lastro_ciclo.py"
      provides: "guardião do ciclo do servidor com lastro"
    - path: "web/tests/test_ciclo_iphone_delega_servidor.mjs"
      provides: "guardião do ciclo do iPhone (com e sem sessão)"
  key_links:
    - from: "web/src/persistence.js deviceStore.cycle"
      to: "POST /api/cycle"
      via: "api.cycle() quando sync.hasSession()"
      pattern: "hasSession\\(\\)[\\s\\S]{0,400}api\\.cycle\\(\\)"
    - from: "server/app/agent.py _run_cycle_inner"
      to: "store.qty_livre"
      via: "pré-checagem antes de store.sell"
      pattern: "store\\.qty_livre\\("
---

<objective>
Operador IA — corrigir as duas falhas do ciclo de saída (stop/alvo) diagnosticadas em 2026-10-21:
(1) o iPhone logado roda um Operador LOCAL legado (sem trailing/alvo dinâmico/tetos, gate pela flag
`autonomous`) que tenta vender, recebe 400 de lastro e aborta o ciclo; com conta ele passa a delegar
o ciclo inteiro ao servidor. Sem conta, o caminho local fica tolerante a lastro.
(2) o servidor chama `store.sell` em posição 100% travada a cada ciclo, gravando rejeição nova no
histórico (poda por CAP_REJEICOES descarta rejeições legítimas) e warn novo no Diário; passa a
pré-checar com `store.qty_livre` e avisar 1x por posição/dia.

Fora do escopo (decisão do Alex): item 3, PUT órfã. Não portar trailing/alvo dinâmico para o caminho
sem conta. Não implementar fill parcial (guardrail do CLAUDE.md — venda do livre já existe no motor).

Output: agent.py e persistence.js corrigidos + 1 pytest novo + 1 teste .mjs novo.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md

Regras de execução (CLAUDE.md, "Estratégia de execução"): `web/src/App.jsx` NÃO é tocado nesta quick
e nunca é lido inteiro. Rode só os testes tocados/listados abaixo + `npx vite build`. A suíte
canônica é do orquestrador. Não chame mutadores `gsd-sdk state.*`.

<interfaces>
Extraído do código em 2026-10-21 (não precisa reexplorar):

server/app/store.py
- `def qty_livre(pos: dict) -> int` (l.~801) — ÚNICA fonte de "qty vendável". Guardião
  `test_lastro_trava.py::test_fonte_unica_nenhum_outro_modulo_subtrai_qty_travada` reprova qualquer
  `qty ... - ... qtyTravada` (regex de 20 chars) em outro módulo — NÃO escreva essa subtração nem em
  comentário/f-string de agent.py.
- `def sell(conn, t, price, user_id=None, qty=None, motivo="manual", origem="manual")` (l.876) —
  relê positions; `livre<=0` → `registrar_rejeicao(...)` + `return None`; senão vende
  `sold = livre` (total do livre quando qty=None), retorna `pnl` (float). Grava history[0] com
  `{"type":"VENDA","qty":sold,...}`.
- `store.get(conn, "positions", user_id=scope)`, `store.get(conn, "history", user_id=scope)`.

server/app/agent.py
- `_avisar_fora_pregao(conn, scope, par, app_mode, positions, quotes_data, option_positions=())`
  (l.905) — padrão de dedupe: kv `{"data": _today(), "chaves": [...]}` via `db.kv_get/kv_set`
  try/except best-effort; data diferente zera a lista.
- `_run_cycle_inner` (l.961): laço de posições; após trailing/alvo dinâmico/`_gatilho_saida`:
  `if not (breach_stop or hit_alvo): continue` → `motivo` → `valor_op` → `if par["mode"] != "executar"`
  (warn "apenas sinalizar") → teto `maxOpsDia` → teto `maxValorOp` → `pnl = store.sell(...)` (l.~1067)
  → ramo `if pnl is None:` (A-08, relê posição; MANTER para a corrida "posição sumiu") →
  `executed += 1`, `_bump_ops`, evento `kind:"buy"` com `_txt = f"Proteção simulada: {t} vendido ({motivo}) a R$ {price:.2f}. Resultado realizado: R$ {pnl:+.2f}."`.
- Retorno: `{"events": events, "executed": executed, "appMode": app_mode}` (l.1134).
- Helpers de teste em server/tests/test_agent.py: `_conn()`, `_seed(c, positions, ag)`, `_quotes(prices)`,
  `_run(c, prices)`, fixture autouse `_pregao_aberto` (importa `abrir_pregao` de `.relogio_pregao`).

server/app/main.py `POST /api/cycle` (l.5345) devolve `store.public_state(...)` (positions,
optionPositions, cash, history, agent{...events...}, config, ...) + `quotes` + opcionalmente
`mercadoFechado: True` e `mensagem`.

web/src/api.js: `cycle: () => req("POST", "/api/cycle")` (l.459). `sell` → /api/sell.
web/src/persistence.js
- imports já presentes: `api`, `sync` (`sync.hasSession()` = token em localStorage `b3-auth-token-v1`),
  `qtyLivre` de `./finance.js`, `execucaoForaPregaoTxt`, `hojeBRT`.
- `serverStore.cycle: () => api.cycle()` (l.418) — contrato a reusar.
- `_adotarCarteiraDoServidor(r)` (l.743) — adota positions/optionPositions/cash/history/pendingOrders/
  caixaReservado/equitySnapshots. NÃO adota `agent`.
- `putAgent` (l.~1976) tem `const SERVER_KEYS = ["serverEnabled","mode","rules","trailingPct","trailingMode",...]`
  local à função e adota `doc.agent[k] = ag[k]` para essas chaves.
- `deviceStore.sell(t)` (l.~1880-1898): sem sessão e `qtyLivre(pos) <= 0` → `_registrarRejeicaoLocal` + `throw`.
- `deviceStore.cycle()` (l.1992): portão de pregão (`api.marketStatus`), `api.getQuotes`, laço de
  posições com `if (doc.agent.autonomous) { await this.sell(pos.t); events.push({kind:"buy", ...}) }`
  (l.~2030), depois `avaliarOpcoesLocal`, ramo mercado fechado com dedupe `doc.agent.avisoForaPregao`,
  retorno `pub()` + `out.quotes`. App.jsx (~l.10546) consome `s.quotes`, `s.mercadoFechado`,
  `s.mensagem`, `s.agent.events`.
- Padrão de teste .mjs dinâmico: web/tests/test_execucao_fora_pregao.mjs (stub de `localStorage` +
  `globalThis.fetch` registrando URLs em `chamadas`, `CapacitorCustomPlatform = {name:"ios"}`,
  import de `../src/persistence.js?c<seq>` para store novo).
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Servidor — pré-checagem de lastro no ciclo, aviso deduplicado, quantidade vendida no parcial</name>
  <files>server/app/agent.py, server/tests/test_agent_lastro_ciclo.py</files>
  <behavior>
    - Stop rompido, posição qty=100 com qtyTravada=100, mode "executar", appMode operador: 2 chamadas
      `_run` no mesmo dia → nenhuma entrada nova em history com status de rejeição (compare
      len/conteúdo de history antes/depois), exatamente 1 evento warn mencionando o ticker e "lastro"
      somando os eventos dos 2 ciclos, `executed == 0` nos dois, contador diário de operações intacto
      (mesma leitura que `_ops_today` usa / agent.opsHoje inalterado), posição e cash intactos.
    - Mesmo cenário mas com um segundo ticker sem trava e com stop rompido no mesmo ciclo: o segundo É
      vendido (prova que a pré-checagem não aborta o laço).
    - Virada de dia (monkeypatch `agent._today` para outra data): o aviso volta a aparecer 1x.
    - Parcial: qty=300, qtyTravada=100, stop rompido → posição fica com qty 100, history[0] é VENDA qty
      200, evento `kind:"buy"` tem texto contendo "200" (quantidade vendida) e `pnl` vindo do motor.
    - Venda total sem trava: texto do evento continua o de antes (regressão de test_agent.py verde).
  </behavior>
  <action>
    RED primeiro: criar `server/tests/test_agent_lastro_ciclo.py` reutilizando o padrão de
    `test_agent.py` (copiar `_conn/_seed/_quotes/_run` e a fixture autouse de pregão aberto via
    `from .relogio_pregao import abrir_pregao`; posições com `stop` acima do preço cotado e
    `rules.stop` ligado no agent seed com `mode:"executar"` — conferir em test_agent.py o shape exato
    de `ag` que liga execução e reproduzir). Rodar e ver falhar.

    GREEN em `_run_cycle_inner`: logo DEPOIS do bloco `if par["mode"] != "executar": ... continue` e
    ANTES dos tetos `maxOpsDia`/`maxValorOp` (assim posição travada não gera warn de teto nem conta
    para teto), ler `livre = store.qty_livre(pos)` sobre a posição corrente do laço. Se `livre <= 0`:
    não chamar `store.sell`, não gravar rejeição, emitir warn deduplicado e `continue`.
    Dedupe: novo helper pequeno `_avisar_lastro_travado(conn, scope, ticker, texto) -> list` seguindo
    o mecanismo de `_avisar_fora_pregao` (kv próprio `avisoLastroTravado` = {"data": _today(),
    "chaves": [...]}, chave `lastro:<ticker>`, get/set best-effort em try/except BLE001; data diferente
    zera). Se quiser, extraia o núcleo comum de dedupe para uma função compartilhada pelos dois, sem
    mudar o comportamento de `_avisar_fora_pregao` (os testes dele precisam seguir verdes). Evento:
    `{"time": _now_str(), "kind": "warn", "t": ticker, "text": ...}` SEM `tag` (push só olha
    kind=="buy"). Texto PT-BR, sem número inventado, citando só dados do motor: ex. f"{t} com {motivo}
    (R$ {price:.2f}): nenhuma venda foi feita porque {pos.get('qtyTravada')} ação(ões) estão travadas
    como lastro de uma CALL coberta aberta — recompre a call para liberar. Nada foi debitado do teto
    diário de operações. Este aviso aparece uma vez por dia." Não escrever a subtração qty−qtyTravada
    em lugar nenhum (guardião de fonte única).
    Parcial: com `0 < livre < pos["qty"]`, manter `store.sell(...)` sem `qty=` (o motor já vende só o
    livre); no evento de sucesso, usar `livre` (lido do motor antes da venda) como quantidade vendida
    quando for parcial: texto "Proteção simulada: {t} — {livre} de {qty} ação(ões) vendidas ({motivo})
    a R$ {price:.2f}; {qtd travada} seguem travadas como lastro. Resultado realizado: R$ {pnl:+.2f}."
    — onde a qtd travada vem de `pos.get('qtyTravada')` (campo do motor, sem aritmética). Venda total
    mantém o `_txt` atual. `valor_op` do teto por operação: manter como está (fora do escopo).
    Manter o ramo `if pnl is None:` (A-08) intacto para a corrida "posição sumiu"; atualizar só o
    comentário para dizer que o caso de lastro agora é barrado antes (o ramo de lastro lá vira
    defensivo). Comentários carregam histórico da decisão (convenção da casa), com referência
    "quick 261021-spd".
  </action>
  <verify>
    <automated>cd server && .venv/bin/python -m pytest tests/test_agent_lastro_ciclo.py tests/test_agent.py tests/test_lastro_trava.py tests/test_agent_options.py -q 2>&amp;1 | tail -5; grep -rln "execucao_fora\|avisar_fora_pregao" tests | xargs .venv/bin/python -m pytest -q 2>&amp;1 | tail -3</automated>
  </verify>
  <done>Teste novo verde; test_agent.py, test_lastro_trava.py (incluindo fonte única), test_agent_options.py e os testes de aviso fora do pregão verdes; nenhum `store.sell` é chamado com livre<=0 no ciclo.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: iPhone — deviceStore.cycle delega ao servidor com conta; caminho sem conta tolerante a lastro</name>
  <files>web/src/persistence.js, web/tests/test_ciclo_iphone_delega_servidor.mjs</files>
  <behavior>
    - Com token em `b3-auth-token-v1`: `store.cycle()` faz POST em `/api/cycle`; nenhuma URL `/api/sell`,
      `/api/market/status`, `/api/quotes` nem `/api/options/chain` é chamada pelo iPhone; o retorno tem
      positions/cash/history/agent.events do servidor (stub devolve estado com posição vendida e evento
      do servidor), `quotes`, e repassa `mercadoFechado`/`mensagem` quando o servidor os manda;
      localStorage do doc reflete o estado adotado.
    - Com token e /api/cycle falhando (500 ou fetch lançando): `cycle()` rejeita com erro (App já mostra
      "Ciclo: ..."); NÃO cai em ciclo local e não vende.
    - Sem token, pregão aberto, `doc.agent.autonomous = true`, posição A (qty 100, qtyTravada 100, stop
      rompido) antes de posição B (sem trava, stop rompido): `cycle()` não lança; 1 evento warn de lastro
      para A (sem "vendido"); B vendida com evento "vendido"; A continua na carteira; opções seguem
      avaliadas (o ciclo chega ao fim e grava `doc.agent.events`).
    - Sem token, venda local que lança por outro motivo: evento warn com a mensagem do erro, sem
      "vendido", ciclo continua.
    - Estático: o trecho de `deviceStore.cycle` com sessão contém `api.cycle()` e não contém
      `this.sell(` antes do retorno do ramo logado.
  </behavior>
  <action>
    RED: criar `web/tests/test_ciclo_iphone_delega_servidor.mjs` no padrão dinâmico de
    `test_execucao_fora_pregao.mjs` (stub de localStorage com Map, `CapacitorCustomPlatform`, fetch
    stub que registra URLs e responde `/api/cycle` com um public_state fake, `/api/market/status`
    aberto, `/api/quotes` com preços abaixo do stop; import `../src/persistence.js?c<seq>`). Para o
    caso logado, gravar o token em `b3-auth-token-v1` no Map antes do import (conferir em
    test_agent_server_toggle.mjs/sync.js se o login precisa de mais alguma chave e reproduzir).
    Rodar com `node` e ver falhar.

    GREEN em `deviceStore.cycle()` (per escopo item 1):
    (a) Logo após `ensure()`, `if (sync.hasSession())`: `const r = await api.cycle();` (sem try —
    erro propaga, sem fallback local: rodar o Operador legado em paralelo ao servidor é exatamente o
    defeito); `_adotarCarteiraDoServidor(r)`; adotar do `r.agent` (se objeto) `events` (array, servidor
    é a fonte do Diário com conta) e as chaves de `SERVER_KEYS` — hoisting de `SERVER_KEYS` de dentro
    de `putAgent` para o escopo do closure do deviceStore e reuso nos dois lugares (sem duplicar a
    lista); `write()`; `const out = pub(); out.quotes = (r && r.quotes) || {};` e repassar
    `mercadoFechado`/`mensagem` quando presentes; `return out`. Comentário com histórico: por que
    delega (dois Operadores divergentes: sem trailing/alvo dinâmico/tetos, gate pela flag legada,
    vendia no alvo antes de o servidor estender; 400 de lastro abortava o ciclo) — quick 261021-spd.
    (b) Caminho sem sessão (o laço legado que continua abaixo): antes de vender, `qtyLivre(pos)` (import
    já existente de finance.js — não reimplementar a subtração); `<= 0` → evento warn deduplicado por
    `lastro:<ticker>` por dia BRT reutilizando o mesmo formato de `doc.agent.avisoForaPregao`
    ({data: hojeBRT(), chaves}) num campo próprio `doc.agent.avisoLastroTravado`, texto equivalente ao
    do servidor (sem "vendido"), e `continue`. Com livre > 0: `try { await this.sell(pos.t); push
    evento "vendido" } catch (e) { push warn com e.message, sem "vendido" }` — o evento de sucesso, se
    parcial, diz a quantidade vendida usando `livre` lido via `qtyLivre` antes da venda (mesma regra
    do servidor). Não portar trailing/alvo dinâmico/tetos para este caminho. Manter o gate
    `doc.agent.autonomous` e o ramo de opções/mercado fechado inalterados.
    (c) Paridade: `serverStore.cycle` já delega; não criar método novo em só um store. Se
    `test_api_parity.mjs` reclamar, ajustar o código (não o guardião).
    Textos user-facing: seguir `.claude/skills/didatica-boris/SKILL.md` (ler só a seção de
    vocabulário/princípios de dado) — PT-BR com acentuação correta nos textos NOVOS.
  </action>
  <verify>
    <automated>cd web && node tests/test_ciclo_iphone_delega_servidor.mjs && node tests/test_execucao_fora_pregao.mjs && node tests/test_api_parity.mjs && node tests/test_agent_server_toggle.mjs && for f in $(grep -l "cycle()" tests/*.mjs); do node "$f" >/dev/null || echo "FALHOU $f"; done; npx vite build 2>&amp;1 | tail -3</automated>
  </verify>
  <done>Teste novo verde; test_execucao_fora_pregao, test_api_parity, test_agent_server_toggle e demais .mjs que citam cycle() verdes; `npx vite build` sem erro; com sessão nenhuma venda local ocorre.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| iPhone → /api/cycle | cliente autenticado dispara ciclo do servidor; servidor é a autoridade de execução |
| ciclo server-side → store.sell | motor determinístico é a única fonte de quantidades e PnL |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-spd-01 | Tampering | deviceStore.cycle logado | mitigate | nenhuma venda/aritmética local com sessão; adota só o estado devolvido pelo servidor |
| T-spd-02 | Repudiation/Info | Diário (eventos) | mitigate | evento "vendido" só após venda confirmada pelo motor; lastro vira warn explícito (princípio 9) |
| T-spd-03 | DoS (histórico) | registrar_rejeicao no ciclo | mitigate | pré-checagem com store.qty_livre evita rejeição repetida que pode CAP_REJEICOES e descartar rejeições legítimas |
| T-spd-04 | DoS | /api/cycle chamado pelo timer do app + scheduler | accept | ciclo já tem trava "ciclo já em andamento" (agent.py l.882); comportamento idêntico ao da web hoje |
</threat_model>

<verification>
- `server/tests/test_agent_lastro_ciclo.py`, `test_agent.py`, `test_lastro_trava.py` (fonte única), `test_agent_options.py` verdes.
- `web/tests/test_ciclo_iphone_delega_servidor.mjs`, `test_execucao_fora_pregao.mjs`, `test_api_parity.mjs`, `test_agent_server_toggle.mjs` verdes.
- `npx vite build` em `web/` sem erro.
- `grep -n "qtyTravada" server/app/agent.py` não mostra subtração com qty.
- Suíte canônica `bash scripts/executar.sh --testes`: responsabilidade do orquestrador.
</verification>

<success_criteria>
- iPhone logado: Executar ciclo / timer autônomo = ciclo do servidor (com trailing, alvo dinâmico, tetos, gate por mode/appMode); zero chamadas a /api/sell vindas do ciclo.
- Posição 100% travada: 0 rejeições novas no histórico, 1 aviso por dia, teto intacto (servidor e iPhone sem conta).
- Parcial: vende só o livre, evento cita a quantidade.
- Nenhum número inventado; nenhum guardião apagado.
</success_criteria>

<output>
Create `.planning/quick/261021-spd-operador-ciclo-iphone-delega-ao-servidor/261021-spd-SUMMARY.md` when done
</output>
