---
phase: quick-261006-dvg
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - server/app/main.py
  - server/tests/test_conta_nova_nasce_limpa.py
  - server/tests/test_multiuser.py
  - web/src/persistence.js
  - web/tests/test_conta_nova_ios_nasce_limpa.mjs
  - web/tests/test_oauth_repassa_name_e_code.mjs
autonomous: true
requirements: [QUICK-261006-DVG]

must_haves:
  truths:
    - "Conta nova criada no iPhone com documento local pré-existente (caixa, posições, histórico, snapshots, watchlist, chave BYOK) nasce limpa: estado do servidor = defaults (ensure_defaults), sem nada do aparelho"
    - "O servidor ignora `body.seed` em /api/auth/register, /api/auth/login e /api/auth/oauth — inclusive quando quem manda é um binário iOS antigo já instalado"
    - "No aparelho, o namespace novo `b3-agente-state-v1::u:<id>` NÃO copia mais o documento anônimo (`b3-agente-state-v1`); nasce do estado que o servidor devolveu no login (ou de defaultState() se o servidor não devolveu estado)"
    - "Login de conta EXISTENTE continua carregando o documento do servidor (state da resposta + getState adotando carteira); namespace local já existente não é sobrescrito (FASE 8B N2 preservada)"
    - "O documento local anônimo do aparelho permanece byte a byte intocado após register/login/oauth e após logout"
    - "Guardiões estáticos impedem reintroduzir a adoção automática (cliente e servidor)"
  artifacts:
    - path: "server/app/main.py"
      provides: "_apply_seed sem leitura de body['seed']; sempre ensure_defaults"
      contains: "2026-10-06"
    - path: "server/tests/test_conta_nova_nasce_limpa.py"
      provides: "Testes HTTP register/login/oauth com seed ignorada + guardião estático de main.py"
    - path: "web/src/persistence.js"
      provides: "deviceStore sem _localSeed e sem adoção do BASE_KEY no ensure(); _semearDoServidor(state) nos DOIS stores"
      contains: "_semearDoServidor"
    - path: "web/tests/test_conta_nova_ios_nasce_limpa.mjs"
      provides: "Guardião comportamental + estático do cliente iOS"
  key_links:
    - from: "web/src/persistence.js auth.register/login/oauth"
      to: "store._semearDoServidor(r.state)"
      via: "chamada após _deviceScope(r.user.id), só isNative"
      pattern: "_semearDoServidor"
    - from: "server/app/main.py auth_register/auth_login/auth_oauth"
      to: "store.ensure_defaults"
      via: "_apply_seed(user_id, body) que não lê body['seed']"
      pattern: "ensure_defaults\\(_conn, user_id=user_id\\)"
---

<objective>
Conta nova no iOS nasce limpa (decisão do Alex, 2026-10-06; invariante do CLAUDE.md "conta nova nasce limpa; sem posições-demo no estado inicial"; achado 3 de `46.1-05-SUMMARY.md`). Remover os DOIS caminhos de adoção automática do documento local do aparelho, sem apagar dado local.

Purpose: hoje a conta nova herda caixa, posições, histórico e snapshots do aparelho — origem provável do acumulado com base errada (+10.193 %) visto na 46.1.
Output: servidor que ignora `seed`; deviceStore que não copia o doc anônimo; guardiões no backend e no front.
</objective>

<investigation>
Registro da investigação (feita pelo planner, 2026-10-06). O executor NÃO precisa refazer — usar como contrato.

1. ONDE A ADOÇÃO ACONTECE — são DOIS caminhos independentes, ambos precisam sair:

   (A) Servidor (semente explícita). `web/src/persistence.js`:
       - `deviceStore._localSeed()` (~linha 1731-1754): devolve o doc LOCAL cru do escopo ativo (config INCLUINDO apiKey/BYOK, skill, skillOperador, llmPrompts, watchlist, cash, positions, history, agent, analyses, profile, custom, equitySnapshots, optionPositions, pendingOrders, caixaReservado).
       - `serverStore._localSeed: () => null` (~linha 387-389), comentário FASE 2.
       - `_seedBody()` (~linha 2072-2075) e `auth.register`/`auth.login`/`auth.oauth` (~linhas 2100-2129) fazem `body.seed = seed`.
       `server/app/main.py` `_apply_seed(user_id, body)` (~linha 359-381): se `body["seed"]` é dict → `store.seed_user_from(_conn, user_id, seed)`; senão → `store.ensure_defaults`. Chamado por `auth_register` (419), `auth_login` (440), `auth_oauth` (478).
       `server/app/store.py` `seed_user_from(conn, user_id, seed, only_if_empty=True)` (~linha 1550): REGRA EXATA — semeia todas as `USER_SECTIONS` presentes na semente se e somente se `db.kv_get(conn, "config", None, user_id=user_id) is None` (conta sem `config` no servidor = conta nova). Conta existente: só `ensure_defaults`, sem re-semear.

   (B) Cliente (cópia local). `deviceStore.ensure()` (~linha 441-450): quando `read()` do namespace `b3-agente-state-v1::u:<id>` é null e há `deviceUserId`, copia `readKey(BASE_KEY)` (doc anônimo) para o namespace do usuário ("decisão B, local-first. NÃO apaga o anônimo"). Isso acontece em TODO 1º uso de um namespace no aparelho — conta nova OU conta existente logando num aparelho novo. Mesmo sem (A), (B) faria a conta nova exibir no aparelho snapshots/initialBudget/watchlist/agent/analyses herdados (getState só adota do servidor cash/positions/optionPositions/history/pendingOrders/caixaReservado — `_adotarCarteiraDoServidor`, ~linha 698; `equitySnapshots` são locais, ~linha 1027).

   Por que a 2ª conta nasceu limpa: NÃO confirmado; irrelevante após remover (A) e (B). Hipótese registrada: dependia de qual namespace estava ativo no instante do `_localSeed()` e do conteúdo do doc anônimo naquele momento. Não gastar contexto investigando.

2. QUEM DEPENDE DA ADOÇÃO:
   - Usuário que usava o app sem conta antes do login obrigatório: o modo anônimo foi removido (comentário de 09/08/2026 em `_apply_seed`); o web já nasce limpo desde então. O iOS ficou como último resquício. Consequência aceita pela decisão do Alex: a chave BYOK local não migra para a conta nova (o usuário recadastra).
   - Binários iOS antigos instalados (TestFlight/App Store) continuam mandando `seed` — por isso a remoção no SERVIDOR é a garantia real; a remoção no cliente é higiene + caminho (B).
   - `serverUrl`: hoje chegaria ao namespace novo pela cópia do anônimo, mas já existe a chave GLOBAL `b3-server-url-v1` lida em todo `ensure()` (FASE 6 fix 1) — nada se perde.
   - Testes: `server/tests/test_multiuser.py::test_seed_first_login_adota_local_e_nao_reescreve` testa `store.seed_user_from` direto (unidade do store, não a rota) — continua válido como unidade; `web/tests/test_oauth_repassa_name_e_code.mjs` só cita o seed em comentário histórico; `test_fase5_skill_migracao_legado.mjs` e `test_opcao_descoberto_store.mjs` trocam de escopo com `_setDeviceScope` (precisam continuar verdes: o primeiro pré-grava a chave escopada; o segundo materializa defaults num escopo novo — com (B) removido, passa a vir de defaultState(), que é o que ele espera).

3. DADO LOCAL EXISTENTE: o doc anônimo em `b3-agente-state-v1` nunca é escrito nem removido por este plano; segue no aparelho e volta a ser o escopo ativo após logout (`_deviceScope(null)`). Namespaces de usuário já existentes (ex.: a conta de teste `teate@gmail.com` que herdou dados) NÃO são limpos retroativamente — fora de escopo, sem decisão do Alex. Uma UI de "importar dados deste aparelho" seria funcionalidade nova, não pedida: NÃO implementar; registrar no SUMMARY como limitação conhecida.

4. PARIDADE deviceStore↔serverStore: `_localSeed` sai dos DOIS; o método novo `_semearDoServidor(state)` entra nos DOIS (no-op no serverStore, igual ao padrão de `_setDeviceScope`).

5. Risco de conflito: a quick irmã `261006-dvf` (acumulado com base errada) pode tocar `web/src/persistence.js`/`server/app/store.py`. Se estiver em execução simultânea, serializar (este plano não toca `store.py`).
</investigation>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/phases/46.1-fechamento-das-ressalvas-da-fase-46/46.1-05-SUMMARY.md

Leitura de código: `web/src/persistence.js` NUNCA inteiro — Grep + Read com offset/limit nas faixas citadas em <investigation>. `App.jsx` não precisa ser tocado nem lido (handlers login/register/oauth em ~10261-10289 já chamam `loadState()` no nativo após `auth.*`, o que lê o namespace novo).

<interfaces>
server/app/main.py (atual):
  def _apply_seed(user_id: str, body: dict) -> None   # chamado em auth_register, auth_login, auth_oauth
  def _auth_payload(user: dict) -> dict               # {"token", "user", "state": store.public_state(_conn, user_id=...)}
server/app/store.py (NÃO modificar):
  def ensure_defaults(conn, user_id=None)
  def public_state(conn, user_id=None) -> dict        # sem apiKey; config.keyStored bool; inclui catalog, analysisLog, agentLog
  def seed_user_from(conn, user_id, seed, only_if_empty=True) -> bool   # permanece como unidade; nenhuma rota chama
  USER_SECTIONS = SECTIONS + ["equitySnapshots", "analysisLog", "agentLog", "pushTokens"]
server/tests harness HTTP: copiar o padrão de server/tests/test_gate_cadastro.py (fixture autouse `_app_main_isolado` + `_reimporta(monkeypatch)` com B3_DB_PATH temporário + TestClient). OAuth: monkeypatch `main.auth.verify_oauth_token` para devolver {"sub": "...", "email": ..., "email_verified": True}.
web/tests harness nativo: copiar o padrão de web/tests/test_oauth_repassa_name_e_code.mjs (globalThis.CapacitorCustomPlatform = {name:"ios"}, localStorage em Map, fetch mockado por rota, `const { auth, store } = await import("../src/persistence.js")`, contador fails + process.exit).
Chaves do aparelho: BASE_KEY "b3-agente-state-v1"; namespace "b3-agente-state-v1::u:" + id; SCOPE_KEY "b3-device-scope-v1"; global "b3-server-url-v1".
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Servidor ignora a semente do cliente — conta nova sempre nasce de ensure_defaults</name>
  <files>server/app/main.py, server/tests/test_conta_nova_nasce_limpa.py, server/tests/test_multiuser.py</files>
  <behavior>
    - register com body.seed = {cash: 1.0, positions:[{t:"VALE3",qty:100,avg:60}], history:[{type:"COMPRA",t:"VALE3"}], equitySnapshots:[{data:"2026-01-02",patrimonio:1}], watchlist:["ZZZZ3"], config:{apiKey:"LOCALKEY", initialBudget:12345, userName:"DoAparelho"}} → resposta state: positions == [], history == [], equitySnapshots == [], cash == cash de uma conta registrada SEM seed (comparar com um segundo register sem seed, não com número fixo), "ZZZZ3" not in watchlist, config.keyStored is False, config.userName != "DoAparelho"; e store.get(conn,"config",user_id=uid) não tem apiKey "LOCALKEY".
    - login de conta EXISTENTE com body.seed hostil → state reflete o documento do servidor (gravar antes, via store no escopo do usuário, uma watchlist ["PETR4"] e config userName "DoServidor"; após o login com seed, watchlist e userName continuam os do servidor).
    - oauth (verify_oauth_token monkeypatched) de conta nova com body.seed → mesma asserção de conta limpa do register.
    - Guardião estático: o fonte de server/app/main.py, sem linhas de comentário (descartar linhas cujo strip começa com "#") e sem o docstring de _apply_seed, não contém "seed_user_from" nem "body.get(\"seed\"" nem "body[\"seed\"]".
  </behavior>
  <action>
    RED: criar `server/tests/test_conta_nova_nasce_limpa.py` com os 4 casos de <behavior>, docstring de módulo explicando a decisão do Alex de 2026-10-06 (conta nova sempre limpa; binário iOS antigo continua mandando seed, por isso o servidor é a garantia). Rodar e confirmar que os casos register/oauth FALHAM antes da mudança.
    GREEN: em `server/app/main.py`, reescrever `_apply_seed(user_id, body)` para sempre chamar só `store.ensure_defaults(_conn, user_id=user_id)` e não ler `body["seed"]` em hipótese nenhuma (manter o nome e a assinatura — os três call sites ficam iguais, incluindo o comentário "idempotente" do login). Atualizar o docstring: registrar que a "Decisão B" (adotar o dado local no 1º login) foi revogada em 2026-10-06 por decisão do Alex (invariante "conta nova nasce limpa"; achado 3 do 46.1-05-SUMMARY), que `seed` enviado por qualquer cliente (inclusive iOS antigo) é ignorado, e preservar o parágrafo histórico de 09/08/2026 sobre o web. Não tocar em `store.py` (`seed_user_from`/`export_sections` ficam como unidade do store).
    `server/tests/test_multiuser.py`: NÃO apagar `test_seed_first_login_adota_local_e_nao_reescreve` nem asserções (é unidade válida de `seed_user_from`); acrescentar nota datada 2026-10-06 no docstring do módulo (item 3) e um comentário no teste dizendo que nenhuma rota HTTP chama mais `seed_user_from` (ver test_conta_nova_nasce_limpa.py).
  </action>
  <verify>
    <automated>cd server && .venv/bin/python -m pytest tests/test_conta_nova_nasce_limpa.py tests/test_multiuser.py tests/test_gate_cadastro.py -q</automated>
  </verify>
  <done>Os 4 casos passam; test_multiuser e test_gate_cadastro verdes; `grep -v '^\s*#' server/app/main.py | grep -c seed_user_from` retorna 0.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: deviceStore deixa de adotar o doc anônimo e de enviar semente; namespace novo nasce do estado do servidor</name>
  <files>web/src/persistence.js, web/tests/test_conta_nova_ios_nasce_limpa.mjs, web/tests/test_oauth_repassa_name_e_code.mjs</files>
  <behavior>
    Cenário nativo (CapacitorCustomPlatform ios), localStorage pré-carregado ANTES do import com o doc anônimo em "b3-agente-state-v1": cash 1000000, positions [{t:"VALE3",qty:100,avg:60}], history [1 COMPRA], equitySnapshots [2 itens], watchlist ["ZZZZ3"], config {apiKey:"LOCALKEY", initialBudget:10000}. Guardar o JSON cru do anônimo para comparar.
    - auth.register: o corpo enviado a /api/auth/register NÃO tem a chave "seed" (idem login e oauth).
    - Conta nova (mock devolve {token, user:{id:"novo1"}, state:{cash:100000, positions:[], history:[], equitySnapshots:[], watchlist:["PETR4"], config:{initialBudget:100000, keyStored:false}}}) → após `await store.getState()`: positions vazio, history vazio, equitySnapshots vazio, cash 100000, watchlist sem "ZZZZ3", config.apiKey vazio/ausente, initialBudget 100000.
    - Conta nova com resposta SEM state → getState devolve defaultState() (positions vazio, sem "ZZZZ3", sem "LOCALKEY"), nunca o doc anônimo.
    - Conta existente com namespace já gravado ("b3-agente-state-v1::u:velho1" com watchlist ["ITUB4"], cash 5000) e mock devolvendo state diferente → o namespace existente NÃO é sobrescrito pelo state do login (watchlist continua ["ITUB4"]) — FASE 8B N2; e getState com sessão adota cash/positions de /api/state (mock do GET devolve cash 7777) → cash 7777.
    - Após todos os logins e um auth.logout(): mem.get("b3-agente-state-v1") === JSON cru guardado (documento local intocado).
    - Guardião estático: persistence.js sem linhas de comentário (`//`) não contém "_localSeed", "_seedBody", "body.seed" nem "readKey(BASE_KEY)"; contém "_semearDoServidor" pelo menos 2 vezes na definição (serverStore e deviceStore) — paridade.
  </behavior>
  <action>
    RED: criar `web/tests/test_conta_nova_ios_nasce_limpa.mjs` com o harness de test_oauth_repassa_name_e_code.mjs (fetch mockado por rota: /api/auth/register, /api/auth/login, /api/auth/oauth, GET /api/state, /api/auth/logout; demais rotas → {}), cobrindo <behavior>; cabeçalho datado 2026-10-06 com a decisão do Alex. Rodar e ver falhar.
    GREEN em `web/src/persistence.js` (per decisão do Alex 2026-10-06, conta nova sempre limpa):
    (a) `deviceStore.ensure()`: remover o bloco que copia `readKey(BASE_KEY)` para o namespace do usuário; fica `doc = loaded || defaultState()`. Comentário datado explicando a revogação da "decisão B" e que o doc anônimo continua no aparelho, intocado.
    (b) Remover `_localSeed` do deviceStore e do serverStore, e `_seedBody()`; em `auth.register`, `auth.login`, `auth.oauth` remover a linha que monta `body.seed`. Atualizar o comentário da superfície `auth` (FASE 2) para não falar mais em semente.
    (c) Novo método `_semearDoServidor(state)` nos DOIS stores. serverStore: no-op (`() => {}`, comentário "web: estado já vem do servidor por token"). deviceStore: se `state` não for objeto, ou não houver `deviceUserId`, ou a chave do namespace atual já existir em localStorage (`read()` não-null) → não faz nada (preserva FASE 8B N2 e o local-first de quem já tem doc no aparelho). Senão monta um doc só com as seções de usuário vindas de `state` (config sem `keyStored`, skill, skillOperador, llmPrompts, watchlist, cash, positions, optionPositions, pendingOrders, caixaReservado, history, agent, analyses, profile, equitySnapshots, custom — ignorar catalog, analysisLog, agentLog), grava direto na chave do namespace via localStorage e zera `doc = null` para que o próximo `ensure()` aplique todos os backfills existentes. Nunca escreve em BASE_KEY.
    (d) Helper `_deviceSeedFromServer(state)` ao lado de `_deviceScope`: só se `isNative` e `typeof store._semearDoServidor === "function"`, chama-o dentro de try/catch silencioso. Em `auth.register`/`login`/`oauth`, chamar `_deviceSeedFromServer(r && r.state)` LOGO APÓS `_deviceScope(r.user.id)` e dentro do mesmo `if (r && r.user)`.
    `web/tests/test_oauth_repassa_name_e_code.mjs`: só acrescentar nota datada 2026-10-06 ao item 1 do cabeçalho dizendo que o seed do 1º login deixou de existir (servidor ignora; cliente não envia). Não alterar asserções.
    NÃO tocar App.jsx (o `loadState()` pós-login já lê o namespace). Não tocar `migrate.js`.
  </action>
  <verify>
    <automated>cd web && node tests/test_conta_nova_ios_nasce_limpa.mjs && node tests/test_oauth_repassa_name_e_code.mjs && node tests/test_fase5_skill_migracao_legado.mjs && node tests/test_opcao_descoberto_store.mjs && node tests/test_carteira_nativa_sincroniza.mjs && node tests/test_fase2_portfolio.mjs && npx vite build</automated>
  </verify>
  <done>Novo guardião verde; os 5 guardiões existentes verdes sem alteração de asserção; `npx vite build` ok; `grep -v '^\s*//' web/src/persistence.js | grep -cE '_localSeed|_seedBody|readKey\(BASE_KEY\)'` retorna 0.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| app iOS → /api/auth/* | corpo da requisição é controlado pelo cliente (inclusive binários antigos e clientes forjados) |
| localStorage do aparelho → conta | doc anônimo local não pertence necessariamente à conta que está logando |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-dvg-01 | Tampering | `_apply_seed` em server/app/main.py | mitigate | servidor ignora `body.seed` por completo; conta nova = `ensure_defaults`; teste HTTP com seed hostil (cash/positions/history forjados) |
| T-dvg-02 | Information Disclosure | doc anônimo do aparelho (BYOK `apiKey`, carteira) | mitigate | cliente não envia mais o doc local; namespace novo não copia BASE_KEY; teste confirma ausência de "seed" no corpo e de "LOCALKEY" no estado |
| T-dvg-03 | Repudiation / perda de dado | doc local existente | mitigate | nenhuma escrita/remoção em BASE_KEY; teste compara o JSON cru antes/depois de register/login/oauth/logout |
| T-dvg-04 | Tampering | `_semearDoServidor` sobrescrevendo namespace existente | mitigate | só age se a chave do namespace estiver ausente; teste da conta existente com namespace pré-gravado |
</threat_model>

<verification>
- Task 1 e Task 2 verdes com os comandos de <verify>.
- Orquestrador (fora do sandbox, uma vez): `cd web && npx vite build && npx cap copy ios`, depois `bash scripts/executar.sh --testes` (suíte canônica, as duas suítes).
- `git diff --stat` mostra só os 6 arquivos de files_modified.
</verification>

<success_criteria>
- Conta nova (register, login de 1ª vez, oauth) nunca herda caixa, posições, histórico, snapshots, watchlist ou chave do aparelho — nem por semente ao servidor, nem por cópia local.
- Conta existente continua vendo o documento do servidor; namespace local existente preservado.
- Documento anônimo local intocado.
- Paridade: `_localSeed` removido dos dois stores; `_semearDoServidor` presente nos dois.
- Guardiões estáticos travam a reintrodução nos dois lados; nenhum guardião antigo apagado (notas datadas 2026-10-06).
</success_criteria>

<output>
Criar `.planning/quick/261006-dvg-conta-nova-no-ios-nasce-limpa-remover-ad/261006-dvg-SUMMARY.md` com: o que mudou, arquivos, testes e resultados, e limitações conhecidas — (1) namespaces já criados por adoção (ex.: conta de teste `teate@gmail.com`) não são limpos retroativamente; (2) BYOK local não migra para conta nova; (3) não há UI para importar o doc anônimo (funcionalidade nova, não pedida); (4) regra que deixou a 2ª conta limpa na 46.1 não confirmada (irrelevante após a remoção). Não editar STATE.md com mutadores do gsd-sdk.
</output>
