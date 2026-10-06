---
phase: quick-261006-oav
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - server/app/mydata_budget.py
  - server/tests/test_mydata_budget.py
  - server/tests/test_mydata_budget_prioridade.py
  - server/app/options_provider_mydata.py
  - server/app/main.py
  - server/tests/test_opcoes_cota_reserva_rotas.py
  - server/app/options_api.py
  - server/tests/test_gate_concorrencia.py
  - web/src/filaGate.js
  - web/src/api.js
  - web/tests/test_fila_gate.mjs
autonomous: true
requirements: [QUICK-261006-OAV-RESERVA, QUICK-261006-OAV-RAJADA, QUICK-261006-OAV-LOG]

must_haves:
  truths:
    - "Com o minuto já consumido por consultas de fundo até o teto de fundo, POST /api/options/buy ainda executa (gasta a reserva do usuário) e uma consulta de fundo no mesmo minuto é recusada"
    - "Com a reserva também esgotada (teto útil total 54/min atingido), POST /api/options/buy devolve o MESMO 502 'Cotação de opções indisponível no momento — tente novamente.' de hoje"
    - "Toda recusa por cota de opções gera UMA linha WARNING (obslog cat 'cota') com janela, gasto/teto, classe e origem, no máximo 1 por chave a cada 60 s, sem segredo"
    - "GET /api/options/gate/* nunca roda mais que 2 chamadas ao provedor ao mesmo tempo e nunca gasta mais que 40% do teto útil por minuto (21 de 54)"
    - "O front nunca tem mais que 2 requisições /api/options/gate em voo, deduplica o mesmo ticker e reaproveita gate 'ok' por 120 s"
    - "Teto total (54/min · 1.800/dia) e contrato options_provider.get_options(ticker, expiration) inalterados; sem fallback para outro provedor"
    - "Compra/venda que reaproveita cadeia em cache devolve o último prêmio real lido e a idade da leitura (cotacaoLidaEm/cotacaoIdadeS); idade desconhecida é null, nunca 0"
  artifacts:
    - path: "server/app/mydata_budget.py"
      provides: "classes de prioridade (usuario/fundo/descoberta) via ContextVar, contexto(), registrar_recusa() com limite de taxa"
      contains: "def contexto"
    - path: "server/app/options_provider_mydata.py"
      provides: "log de recusa nos 3 ramos sem cota, reuso cross-key do cache de cadeia, carimbo lidoEm"
      contains: "registrar_recusa"
    - path: "server/app/options_api.py"
      provides: "semáforo de concorrência + classe descoberta no gate"
      contains: "GATE_CONCORRENCIA"
    - path: "web/src/filaGate.js"
      provides: "fila de concorrência pura + dedupe/TTL do gate"
      exports: ["criarFila", "criarGateCacheado", "GATE_CONCORRENCIA_MAX"]
    - path: "server/tests/test_mydata_budget_prioridade.py"
      provides: "guardiões da reserva, da classe descoberta e do limite de taxa do log"
    - path: "server/tests/test_opcoes_cota_reserva_rotas.py"
      provides: "cenários (1) e (2) ponta a ponta via TestClient"
    - path: "server/tests/test_gate_concorrencia.py"
      provides: "cenário (3) limitador do gate"
    - path: "web/tests/test_fila_gate.mjs"
      provides: "cenário (4) front nunca passa de N gates simultâneos"
  key_links:
    - from: "server/app/main.py (buy/sell/lastreada abrir/abrir-collar/fechar/curadoria abrir-collar)"
      to: "mydata_budget.contexto(prioridade=\"usuario\")"
      via: "with envolvendo SÓ o await options_provider.get_options(...)"
      pattern: "contexto\\(prioridade=\"usuario\""
    - from: "server/app/options_api.py liquidity_gate"
      to: "mydata_budget.contexto(prioridade=\"descoberta\")"
      via: "async with semáforo + with contexto"
      pattern: "prioridade=\"descoberta\""
    - from: "server/app/options_provider_mydata.py ramos sem cota"
      to: "mydata_budget.registrar_recusa"
      via: "helper _sem_cota(...)"
      pattern: "registrar_recusa\\("
    - from: "web/src/api.js optionsGate"
      to: "web/src/filaGate.js criarGateCacheado"
      via: "import + wrapper do req"
      pattern: "criarGateCacheado"
---

<objective>
Incidente de produção (boris.semente.dev, F10-20261006-02, 2026-10-06 19:41 UTC): `POST /api/options/buy` devolveu 502 em 2 ms porque `options_provider_mydata._gate` → `mydata_budget.pode_gastar` recusou por cota (recusa DURA, D-04), cota esta consumida no mesmo minuto por dezenas de `GET /api/options/gate/<t>` disparados pelos AtivoCards da Mesa (Radar no Modo Operador) logo após um deploy (cache de cadeia vazio). Três frentes numa quick: (1) reserva de cota para ação do usuário; (2) limitar a rajada de gates (front + backend); (3) registrar a recusa por cota com limite de taxa.

Purpose: a ação do usuário (comprar/vender opção) nunca pode perder a disputa de cota para consulta de fundo; e a recusa tem que deixar rastro.
Output: mydata_budget com classes de prioridade; gate com semáforo e teto de fatia; fila de gate no front; log de recusa; 4 arquivos de teste novos.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@server/app/mydata_budget.py
@server/app/options_provider_mydata.py
@server/app/options_provider.py
@server/app/options_api.py

## Investigação (feita no planejamento — o executor NÃO refaz)

### (a) Chamadores de `mydata_budget` e impacto da reserva
| Chamador | Uso | Classe após esta quick | Impacto |
|---|---|---|---|
| `candle_provider.py:390,402` (`_gate` de candles) | `pode_gastar()` / `debita()` sem args | `fundo` (default do ContextVar) | teto efetivo de candles cai de 54→44/min e 1800→1650/dia. Aceitável: candles têm cadeia mydata→brapi→Yahoo e o último elo serve mesmo sem cota (recusa MOLE); opções não têm alternativa (D-04). |
| `candle_provider.py:150` | `snapshot()` | — | ganha campos aditivos |
| `options_provider_mydata._gate` (l.188) | `pode_gastar(n)` pré-filtro | herda do contexto da rota | é o ponto da recusa do incidente |
| `options_provider_mydata._debita` (l.229) | `reservar(n)` commit atômico | herda do contexto | idem |
| `agent.scheduler_loop` → `_avaliar_opcoes` → `options_provider.get_options` | via provider | `fundo` (task criada no boot, contexto default) | sem mudança de código |
| `put_bridge.py:304`, `main.py` propostas/vigias/curadoria/escada/anatomia (leitura) | via provider | `fundo` | sem mudança |
| `options_mcp_api.py` / `mcp_client.py` | NÃO usam `mydata_budget` | — | orçamento próprio (`TETO_SERVICO_DIA=2000` tools/call, ADR-027) — fora do escopo, intocado |
| `aguarda_vaga()` (pacer de lote) | `pode_gastar` | contexto (fundo) | checagem de dia passa a usar o teto da classe |

Tests monkeypatcham `pode_gastar`/`debita`/`reservar` com `lambda n=1, now=None: ...` (test_options_provider.py:145,170-171; test_mydata_provider.py:155-159; test_agent_options.py:278; test_opcoes_fronteira.py:332; test_options_provider_mydata.py:487,616,645,661,674). DECISÃO: a classe de prioridade trafega por `contextvars.ContextVar` — NENHUM chamador existente passa kwarg novo, e as chamadas internas entre `reservar→pode_gastar/debita` continuam `(n, now=now)`. Isso mantém todos esses lambdas válidos sem editar um único guardião e preserva a assinatura pública `options_provider.get_options(ticker, expiration)` (contrato do seletor/`_PROVEDORES`/`option_quotes_getter` do agente). Precedente da casa: `llm.py:52-53` (`_USAGE_COLLECT` ContextVar).

ARMADILHA: `asyncio.create_task` copia o contexto no momento da criação. Por isso o `with mydata_budget.contexto(...)` envolve SÓ a linha `await options_provider.get_options(...)` (ou a chamada do helper que a contém), nunca a rota inteira — senão um `_disparar_ciclo_imediato`/task criada dentro do bloco herdaria prioridade `usuario`.

### (b) Cache de cadeia/vencimentos e reuso pela compra
- `_cache` (TTL 300 s): chave `"{t}:{expiration}"` quando o vencimento é explícito, `"{t}:first@{hoje}"` quando não. Erro cacheado por 60 s; recusa por cota NUNCA cacheada (A-07 — manter).
- `_venc_cache` (TTL 300 s): lista de vencimentos por `"{t}@{hoje}"`; reduz cadeia de 2→1 requisição.
- O gate e a proposta chamam `get_options(t)` (chave `first@`). A compra/venda chama `get_options(underlying, expiration)` com vencimento EXPLÍCITO (chave `t:exp`) → hoje é MISS mesmo com a mesma cadeia lida 10 s antes pelo gate, e gasta 1-2 requisições.
- DECISÃO: degrau de reuso ANTES de gastar cota — em miss da chave explícita, consultar a entrada `"{t}:first@{hoje}"`; se fresca (< 300 s), `providerStatus == "ok"` e `payload["expiration"] == expiration`, devolver essa MESMA cadeia. Justificativa: (i) o dado do mydata é EOD do COTAHIST (publicado após o fechamento) — a cadeia lida há < 5 min é a mesma que o hub devolveria agora; (ii) é exatamente o prêmio real (`lastPrice`) que o usuário viu na tela; (iii) não há preço inventado nem estimado — é o último prêmio real lido; (iv) o TTL não muda (300 s), só a chave equivalente é reconhecida. O payload ok passa a carregar `lidoEm` (ISO-8601 BRT do instante em que o hub respondeu, gravado no momento da escrita no cache, aditivo). As rotas buy/sell devolvem `cotacaoLidaEm`, `cotacaoIdadeS` (inteiro, segundos) e `pregao` aditivos; ausentes no payload (provedores yahoo/mock) → `null`, NUNCA 0.
- NÃO adotado: single-flight de requisições concorrentes da mesma chave — juntaria uma compra (`usuario`) a uma busca de fundo já recusada; o semáforo do gate (Task 3) já serializa as rajadas da mesma origem, e a segunda chamada do mesmo ticker cai no cache.

### (c) Guardiões que travam o comportamento atual
- `server/tests/test_mydata_budget.py::test_janela_do_minuto_bloqueia_no_teto_e_libera_no_minuto_seguinte` (l.64-70) itera `teto = int(quota_min*MARGEM)` chamadas com `pode_gastar()` default → com default `fundo` falharia na 45ª. Reconciliar: envolver o laço em `with b.contexto(prioridade="usuario")` (o teto útil TOTAL continua 54 — é o que a asserção trava), com comentário `# 2026-10-06 (quick 261006-oav): ...` explicando que o teto total é o da classe usuario e o fundo agora para em teto−reserva (coberto em test_mydata_budget_prioridade.py). NUNCA apagar asserção.
- Demais testes de `test_mydata_budget.py` (dia, virada, persistência, aguarda_vaga, snapshot (subset de chaves), degradado, corrida WR-01) devem continuar passando sem edição; se algum falhar, reconciliar do mesmo jeito (nota datada, asserção preservada).
- `test_opcoes_fronteira.py`: guardião_c (allowlist de quem importa `mydata_client`: candle_provider, options_provider_mydata, mydata_budget — `options_api`/`main` NÃO podem importar `mydata_client`, só `mydata_budget`), guardião_d (`reservar` False ⇒ zero rede), guardião_e (`_debita` usa `reservar`, nunca `debita` direto). Preservar os três.
- `test_options_provider_mydata.py`: ramos sem cota não cacheiam (A-07), caminho feliz debita 2×, cache de vencimentos 3 req e não 4. O reuso cross-key não altera nenhum desses (só age em miss de chave explícita com entrada `first@` fresca). Se algum teste compara payload com `==` exato e quebrar pela chave aditiva `lidoEm`, reconciliar com nota datada (chave aditiva, nunca remover asserção).
- `web/tests/test_carteira_opcoes_tira.mjs:291-299` e `test_opcoes_subabas_ui.mjs:161-169`: `store.optionsGate(` exatamente 1× em App.jsx, 1× em useOpcoesPropostas.js, 1× em web/src/opcoes/, 0× em OpcoesScreen.jsx. A fila mora em `api.js` → nenhum desses contadores muda. App.jsx, useOpcoesPropostas.js e persistence.js NÃO são tocados (paridade deviceStore↔serverStore preservada: os dois já delegam a `api.optionsGate`).
- `test_opcoes_custo_declarado` existe só como `web/tests/test_opcoes_custo_declarado.mjs` (custo declarado de ferramentas MCP) e cita `api.js` — rodar após editar `api.js`; não há `server/tests/test_opcoes_custo_declarado*.py`. `test_mcp_guardioes.py` não referencia `mydata_budget` (MCP tem orçamento próprio) — rodar só como sanidade.
- `server/tests/test_gate_liquidez_rotas.py` monkeypatcha `options_api.get_options` com fake sync/async — o semáforo e o contexto não podem mudar a forma da resposta do gate.

### (d) Invariantes
- CLAUDE.md "Dado de mercado"/D-04: opções têm UM elo (mydata); sem fallback para Yahoo/brapi em runtime; `options_provider.py` continua despacho puro por env (nenhuma lógica de cota nele).
- Teto total intocado: 60/min · 2.000/dia, MARGEM 0.9 → 54/1.800. A reserva é FATIA do teto útil, não acréscimo.
- Princípio 4: sem cota = estado degradado + 502 com a mensagem de hoje; nunca preço estimado.
- `null` nunca 0 para "não sei" (`cotacaoIdadeS`).
- Sem segredo em log (sem `X-API-Key`, sem env de token, sem headers do hub).
- Sem texto novo de UI → skill_ref/copy.js intocados.

<interfaces>
De server/app/mydata_budget.py (atual):
- `MYDATA_BUDGET_LOCK = threading.RLock()`; `MARGEM = 0.9`; `quota_min()`, `quota_dia()`, `_teto_util_min()`, `_teto_util_dia()`
- `_estado = {"dia","gasto"}` (persistido kv), `_minuto = {"chave","gasto"}` (memória), `_carrega(dia)`, `_carrega_minuto(chave)`, `_hoje(now)`, `_chave_minuto(now)`
- `pode_gastar(n=1, now=None) -> bool`, `debita(n=1, now=None) -> None`, `reservar(n=1, now=None) -> bool`, `degradado(now=None)`, `aguarda_vaga(n=1, timeout_s=30.0, now=None)`, `snapshot(now=None) -> dict`, `reset()`

De server/app/options_provider_mydata.py:
- `_gate(n=2) -> Optional[str]` ("sem cota"|None); `_debita(n=1) -> bool` (= `mydata_budget.reservar(n)`)
- `_vencimentos(t, hoje) -> Optional[list]` (None = sem cota)
- `get_options(ticker, expiration=None, hoje=None) -> dict`; três ramos devolvem `_empty_payload(ticker, expiration, MYDATA_ORCAMENTO_WARNING, error="sem cota mydata (60/min · 2.000/dia)")` (l.291, l.302, l.343)
- `_cache[key] = (time.time(), payload)` no sucesso (l.380)

De server/app/obslog.py:
- `log(cat: str, msg: str, level: str = "info", **extra) -> None` (level "warn" = WARNING); `recent(n=200, level=None, cat=None) -> list`; `reset()`. Logger "b3" tem `propagate=False` → teste lê `obslog.recent`, não `caplog`.

De server/app/main.py (rotas que cobram cadeia no ato — envolver SÓ a linha do await):
- l.3036 `buy_option`: `chain = await options_provider.get_options(underlying, body.get("expiration"))`; 502 l.3038
- l.3077 `sell_option`: `chain = await options_provider.get_options(pos["underlying"], pos.get("expiration"))`
- l.4237 `/api/options/lastreada/abrir`: `chain = await options_provider.get_options(underlying, body.get("expiration"))`
- l.4363 `/api/options/lastreada/abrir-collar`: `chain = await options_provider.get_options(underlying)` (dentro de try)
- l.4483 `/api/options/lastreada/fechar`: `chain = await options_provider.get_options(pos["underlying"], pos.get("expiration"))`
- l.~3750 `/api/options/curadoria/abrir-collar` (def em l.3670): `await _curadoria_scan_posicao(...)` (helper faz 1 + até VENCIMENTOS_POR_POSICAO-1 get_options) — envolver a chamada do helper
- linhas exatas: localizar com `grep -n "options_provider.get_options\|_curadoria_scan_posicao(" server/app/main.py`; NUNCA ler main.py inteiro

De server/app/options_api.py:
- `router = APIRouter(prefix="/api/options")`; `from .options_provider import get_options` (nome local monkeypatchado nos testes); `liquidity_gate(ticker)` l.163-198, `data = await get_options(t)` l.182

De web/src/api.js:
- l.317 `optionsGate: (t) => req("GET", "/api/options/gate/" + encodeURIComponent(t), undefined, 30000),` dentro de `export const api = {` (l.233)
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: mydata_budget — classes de prioridade (reserva do usuário + fatia de descoberta) e registro de recusa com limite de taxa</name>
  <files>server/app/mydata_budget.py, server/tests/test_mydata_budget_prioridade.py, server/tests/test_mydata_budget.py</files>
  <behavior>
    - Fundo: com `debita(n=44)` no minuto, `pode_gastar(1)` (contexto default) é False; `with contexto(prioridade="usuario")`: `pode_gastar(2)` True e `reservar(2)` True (gasto minuto = 46).
    - Usuario: com gasto do minuto = 54, `pode_gastar(1)` em contexto usuario é False (teto total não cresce).
    - Dia: com gasto do dia = 1650, fundo recusa e usuario aceita; com 1800, os dois recusam.
    - Descoberta: em contexto descoberta, `reservar(1)` aceita 21 vezes e recusa a 22ª mesmo com gasto total do minuto bem abaixo de 44; débito de outras classes não conta na fatia de descoberta, mas o débito de descoberta conta no total.
    - Env `MYDATA_RESERVA_MIN=100` (> teto) → teto fundo 0, usuario 54 (clamp, nunca negativo); valor não numérico → default.
    - `contexto(prioridade="xyz")` levanta ValueError; ao sair do `with` (inclusive por exceção) a prioridade volta ao valor anterior.
    - `reservar(n, prioridade="usuario")` explícito funciona fora de contexto e não vaza a prioridade depois.
    - Compat: com `pode_gastar`/`debita` monkeypatchados por `lambda n=1, now=None: ...`, `reservar(1)` continua funcionando (nenhum kwarg novo nas chamadas internas).
    - `registrar_recusa(2, agora=t0)` chamado 50× dentro de 60 s gera 1 entrada em `obslog.recent(cat="cota")` (level warn) com `janela=minuto`, gasto/teto, `classe=`, `origem=`; em `agora=t0+61` gera a 2ª com `suprimidas=49`; nenhuma entrada contém "X-API-Key", "MYDATA_API_KEY" nem valor de env de chave.
    - `registrar_recusa` com estado que não explica a recusa (ex.: pode_gastar monkeypatchado) registra `janela=indeterminada` e nunca levanta.
    - `snapshot()` mantém as 7 chaves atuais e ganha `reservaUsuarioMin`, `reservaUsuarioDia`, `tetoFundoMin`, `tetoFundoDia`, `tetoDescobertaMin`, `gastoDescobertaMinuto`.
  </behavior>
  <action>
RED: criar `server/tests/test_mydata_budget_prioridade.py` com os casos de `<behavior>` (fixture autouse `mydata_budget.reset()` + `obslog.reset()` antes/depois; usar `now=` fixo como `test_mydata_budget.py` faz com `MIN_10H00`; para o log, passar `agora=` explícito). Rodar e ver falhar.

GREEN em `server/app/mydata_budget.py` (per QUICK-261006-OAV-RESERVA e -LOG; sem aumentar teto total — MARGEM, QUOTA_MIN_DEFAULT=60, QUOTA_DIA_DEFAULT=2000 intocados):
- `import contextvars`, `from contextlib import contextmanager`, `import time`, `from . import obslog` (obslog só importa stdlib — sem ciclo).
- Constantes: `PRIORIDADES = ("usuario", "fundo", "descoberta")`; `RESERVA_USUARIO_MIN_DEFAULT = 10`; `RESERVA_USUARIO_DIA_DEFAULT = 150`; `FRACAO_DESCOBERTA_MIN = 0.4`; `LOG_RECUSA_INTERVALO_S = 60`.
- `_PRIORIDADE = contextvars.ContextVar("mydata_prioridade", default="fundo")`; `_ORIGEM = contextvars.ContextVar("mydata_origem", default=None)`. Getters `prioridade_atual()` / `origem_atual()`.
- `reserva_min()` / `reserva_dia()`: lê env `MYDATA_RESERVA_MIN` / `MYDATA_RESERVA_DIA` a cada chamada (mesmo padrão de `quota_min`, ValueError → default), clamp em `[0, _teto_util_min()]` / `[0, _teto_util_dia()]`.
- `_teto_min(classe)` / `_teto_dia(classe)`: usuario → teto útil total; fundo e descoberta → teto útil − reserva (≥ 0). `_teto_descoberta_min()` = `int(_teto_util_min() * FRACAO_DESCOBERTA_MIN)` (21 com defaults).
- `_minuto` passa a guardar também `"descoberta": 0`; `_carrega_minuto` zera junto na virada.
- `pode_gastar(n=1, now=None, prioridade=None)`: classe = `prioridade or _PRIORIDADE.get()`; dia contra `_teto_dia(classe)`, minuto contra `_teto_min(classe)`, e se classe == "descoberta" também `_minuto["descoberta"] + n <= _teto_descoberta_min()`.
- `debita(n=1, now=None, prioridade=None)`: igual hoje + se classe resolvida == "descoberta", incrementa `_minuto["descoberta"]`.
- `reservar(n=1, now=None, prioridade=None)`: se `prioridade` explícita, validar e fazer `token = _PRIORIDADE.set(prioridade)` com `reset(token)` em finally; por dentro chamar `pode_gastar(n, now=now)` e `debita(n, now=now)` EXATAMENTE nessa forma (sem kwarg novo — compat com os lambdas monkeypatchados listados no contexto). Docstring citando 2026-10-06 / quick 261006-oav e o incidente.
- `@contextmanager def contexto(prioridade: str, origem: Optional[str] = None)`: valida (ValueError fora de PRIORIDADES), seta os dois ContextVars, `yield`, reseta tokens em finally. Docstring com a ARMADILHA do `create_task` (envolver só o await da cadeia).
- `aguarda_vaga`: a checagem de dia passa a usar `_teto_dia(classe do contexto)`.
- `_janela_recusada(n, now, classe) -> tuple[str, int, int]`: devolve ("dia", gasto, teto) | ("minuto", gasto, teto) | ("descoberta-minuto", gasto_desc, teto_desc) | ("indeterminada", gasto_min, teto_min), sob a trava.
- `registrar_recusa(n=1, now=None, agora=None, prioridade=None, origem=None) -> None`: tudo dentro de `try/except Exception: pass` (log nunca derruba). Classe/origem resolvidas do contexto se None (origem None → "nao-identificada"). Chave de limite `(janela, classe, origem)`; dict de módulo `_ultimo_log = {chave: [instante_monotonic, suprimidas]}`; `agora = agora if agora is not None else time.monotonic()`; se dentro de `LOG_RECUSA_INTERVALO_S` desde o último, só incrementa `suprimidas` e retorna; senão `obslog.log("cota", "mydata: recusa por cota", level="warn", janela=..., gasto=..., teto=..., classe=..., origem=..., n=n, suprimidas=K)` e zera K. Só números e rótulos — nenhum header, env de chave nem URL. `reset()` também limpa `_ultimo_log`.
- `snapshot()`: chaves aditivas listadas em `<behavior>`.
- Cabeçalho do módulo: acrescentar item "4. Classes de prioridade (quick 261006-oav, 2026-10-06)" explicando reserva × fatia de descoberta × teto total inalterado e a escolha ContextVar (precedente `llm._USAGE_COLLECT`).

Reconciliar `server/tests/test_mydata_budget.py::test_janela_do_minuto_bloqueia_no_teto_e_libera_no_minuto_seguinte`: envolver o corpo em `with b.contexto(prioridade="usuario"):` com comentário `# 2026-10-06 (quick 261006-oav): o teto útil TOTAL (54) agora é o da classe usuario; o fundo para em teto−reserva — ver test_mydata_budget_prioridade.py.` Asserções intactas. Rodar o arquivo inteiro; qualquer outra falha reconcilia igual (nota datada, asserção preservada).
  </action>
  <verify>
    <automated>cd server && .venv/bin/python -m pytest tests/test_mydata_budget.py tests/test_mydata_budget_prioridade.py tests/test_options_provider.py tests/test_mydata_provider.py tests/test_agent_options.py tests/test_opcoes_fronteira.py tests/test_options_provider_mydata.py tests/test_brapi_budget.py -q</automated>
  </verify>
  <done>Todos os testes listados passam; `grep -c "def contexto\|def registrar_recusa" server/app/mydata_budget.py` = 2; QUOTA_MIN_DEFAULT=60, QUOTA_DIA_DEFAULT=2000, MARGEM=0.9 inalterados (`git diff server/app/mydata_budget.py | grep -E '^-.*(QUOTA_(MIN|DIA)_DEFAULT|MARGEM) ='` vazio); nenhuma asserção removida de test_mydata_budget.py (`git diff --stat` mostra só inserções + reindentação no teste reconciliado).</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: compra/venda passam na frente — contexto usuario nas rotas de execução, log de recusa e reuso da cadeia em cache com idade</name>
  <files>server/app/options_provider_mydata.py, server/app/main.py, server/tests/test_opcoes_cota_reserva_rotas.py</files>
  <behavior>
    - Cenário (1): provider `mydata` (monkeypatch env `B3_OPTIONS_PROVIDER=mydata`), `mydata_client.get_vencimentos`/`get_options_chain` falsos (async) com 1 call de prêmio 1.25, caches do provider limpos, minuto travado (monkeypatch `mydata_budget._chave_minuto`/`_hoje` para valores fixos) e `mydata_budget.debita(n=44)` (fundo cheio). POST /api/options/buy → 200, `priceUsed == 1.25`, gasto do minuto subiu 2; em seguida `mydata_budget.pode_gastar(1)` (fundo) é False e um `get_options` de outro ticker fora de contexto devolve `providerStatus == "degraded"`.
    - Cenário (2): mesmo setup com `debita(n=54)`. POST /api/options/buy → 502 com detail EXATAMENTE "Cotação de opções indisponível no momento — tente novamente."; os falsos do client NÃO foram chamados; `obslog.recent(cat="cota")` tem entrada warn com `janela=minuto`, `classe=usuario`, `origem=POST /api/options/buy`.
    - Reuso: após `get_options("PETR4")` (chave first@, ok, expiration E), o falso do client é zerado; POST /api/options/buy com `expiration=E` → 200 sem chamar o client e sem débito; resposta traz `cotacaoLidaEm` (str ISO) e `cotacaoIdadeS` inteiro ≥ 0, e `priceUsed` igual ao `lastPrice` lido.
    - Idade desconhecida: com provider falso que não traz `lidoEm`, a resposta de buy tem `cotacaoIdadeS is None` e `cotacaoLidaEm is None` (nunca 0).
    - Sell com o minuto em 44 também executa (contexto usuario).
  </behavior>
  <action>
RED: criar `server/tests/test_opcoes_cota_reserva_rotas.py` com os casos de `<behavior>`. Seguir o setup de TestClient/escopo/caixa de `server/tests/test_opcao_descoberto_gate.py` ou `test_fase5_rejeicao_rotas.py` (Grep para achar a fixture que já faz POST /api/options/buy; não inventar outra). Limpar `options_provider_mydata._cache`, `_venc_cache`, `mydata_budget.reset()`, `obslog.reset()` antes/depois.

GREEN em `server/app/options_provider_mydata.py` (per QUICK-261006-OAV-RESERVA, -LOG, investigação (b)):
- Helper `_sem_cota(ticker, expiration, n) -> dict`: chama `mydata_budget.registrar_recusa(n)` e devolve exatamente o `_empty_payload(ticker, expiration, MYDATA_ORCAMENTO_WARNING, error="sem cota mydata (60/min · 2.000/dia)")` de hoje. Usar nos TRÊS ramos sem cota (pré-filtro `_gate`, `venc is None`, segundo `_debita()` False) — mesma mensagem, continua SEM escrever em `_cache` (A-07). `_gate` e `_debita` mantêm nome, assinatura e corpo (guardiões d/e).
- Reuso cross-key: logo após o miss de `_cache.get(key)` e ANTES do `_gate`, quando `expiration` é explícito, olhar `_cache.get(f"{t}:first@{hoje_efetivo.isoformat()}")`; se fresca (< `_OPTIONS_TTL`), `payload.get("providerStatus") == "ok"` e `payload.get("expiration") == expiration`, devolver esse payload (sem rede, sem débito). Comentário datado 2026-10-06 com a justificativa da investigação (b): dado EOD do COTAHIST, último prêmio real lido, sem estimativa, TTL inalterado.
- No payload ok (l.365-377), adicionar `"lidoEm": dt.datetime.now(BRT).isoformat(timespec="seconds")` (aditivo; carimbo do instante em que o hub respondeu).
- Docstring do módulo: parágrafo "quick 261006-oav (2026-10-06)" — classe de prioridade vem do contexto da rota, log de recusa, reuso cross-key.

GREEN em `server/app/main.py` (Grep + Read offset/limit; NUNCA o arquivo inteiro):
- Adicionar `mydata_budget` ao import de módulos `from . import ...` (NÃO importar `mydata_client` — guardião_c).
- Nas 6 rotas de execução listadas em `<interfaces>`, envolver SÓ a linha do `await` (ou do `await _curadoria_scan_posicao(...)` em curadoria/abrir-collar) em `with mydata_budget.contexto(prioridade="usuario", origem="<MÉTODO> <path>"):` (ex.: `origem="POST /api/options/buy"`). Nada de task criada dentro do bloco. Comentário curto de 1 linha datado citando o incidente de 2026-10-06 na primeira ocorrência (buy) e referência a ela nas demais.
- Em `buy_option` e `sell_option`, antes do `return out`, adicionar `out["cotacaoLidaEm"]`, `out["cotacaoIdadeS"]`, `out["pregao"]` via um helper puro de módulo `_idade_cotacao(chain) -> tuple[Optional[str], Optional[int]]` (parse ISO de `chain.get("lidoEm")`; ausente/inválido → (None, None); idade = `max(0, int((agora_brt - lido).total_seconds()))`). Mensagens de 502/400/404 inalteradas byte a byte.
- Não tocar rotas de leitura (proposta, vigias, curadoria GET, escada, anatomia, tecnico) — ficam `fundo`.
  </action>
  <verify>
    <automated>cd server && .venv/bin/python -m pytest tests/test_opcoes_cota_reserva_rotas.py tests/test_options_provider_mydata.py tests/test_opcoes_fronteira.py tests/test_options_provider.py tests/test_opcao_descoberto_gate.py tests/test_fase5_rejeicao_rotas.py tests/test_opcoes_lastreadas_rotas.py tests/test_opcoes_collar_rota.py tests/test_opcoes_curadoria_rota.py tests/test_adr013_cobertura_rotas.py -q</automated>
  </verify>
  <done>Cenários (1) e (2) passam; `grep -c 'prioridade="usuario"' server/app/main.py` = 6; `grep -c "registrar_recusa\|_sem_cota(" server/app/options_provider_mydata.py` ≥ 4; a string "Cotação de opções indisponível no momento — tente novamente." aparece no mesmo número de vezes que antes em main.py (`git diff server/app/main.py | grep -c '^-.*Cotação de opções indisponível'` = 0); nenhum import de `mydata_client` em main.py.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: gate com limitador de concorrência e fatia de descoberta</name>
  <files>server/app/options_api.py, server/tests/test_gate_concorrencia.py</files>
  <behavior>
    - 8 chamadas concorrentes de `options_api.liquidity_gate(t)` (asyncio.gather, tickers distintos) com `options_api.get_options` monkeypatchado por fake async que registra concorrência atual/máxima e dorme 0.05 s → máximo observado ≤ `GATE_CONCORRENCIA` (2) e todas as 8 respondem com a forma de hoje.
    - Dentro do fake, `mydata_budget.prioridade_atual() == "descoberta"` e `origem_atual() == "GET /api/options/gate"`; após o retorno, `prioridade_atual() == "fundo"`.
    - Fake que levanta exceção não vaza slot do semáforo (chamadas seguintes ainda completam).
    - Integração com orçamento real: provider mydata com client falso, `_chave_minuto` travado, 15 tickers distintos via gate → gasto da fatia descoberta no minuto ≤ 21 e os excedentes voltam `{"liquida": false, "providerStatus": "degraded", "faixa": FAIXA_SEM_MERCADO, "melhorScore": None}` (nunca 0.0).
    - Em seguida, `with mydata_budget.contexto(prioridade="usuario")`: `pode_gastar(2)` True (a rajada de descoberta não come a reserva).
  </behavior>
  <action>
RED: criar `server/tests/test_gate_concorrencia.py` (chamar a função da rota direto com `asyncio.run`, como em testes async da casa; para a forma da resposta, espelhar `server/tests/test_gate_liquidez_rotas.py`). Ver falhar.

GREEN em `server/app/options_api.py` (per QUICK-261006-OAV-RAJADA):
- `import asyncio`; `from . import mydata_budget` (NÃO `mydata_client` — guardião_c).
- `GATE_CONCORRENCIA = 2` e semáforo criado PREGUIÇOSAMENTE por event loop: `_gate_sem: tuple | None = None` + `_semaforo_gate()` que devolve o semáforo do loop corrente (recria se `asyncio.get_running_loop()` mudou — TestClient/`asyncio.run` usam loops diferentes por teste).
- Em `liquidity_gate`, depois da validação de ticker (o 400 continua imediato, fora do semáforo): `async with _semaforo_gate():` e dentro `with mydata_budget.contexto(prioridade="descoberta", origem="GET /api/options/gate"):` envolvendo SÓ o `await get_options(t)` (try/except `yahoo.QuoteUnavailable` mantido). O cálculo de score/faixa fica fora do bloco. Formas de resposta e campos inalterados.
- Docstring de `liquidity_gate`: parágrafo "ATUALIZADO 2026-10-06 (quick 261006-oav)" — incidente, semáforo 2, fatia descoberta 40% do teto útil/min (21/54), reserva do usuário intocável pelo gate, recusa da fatia → mesmo ramo degradado de hoje (sem cache, A-07).
- Não criar fila/espera por cota (A-06: nunca dormir esperando janela); o semáforo só ordena concorrência.
  </action>
  <verify>
    <automated>cd server && .venv/bin/python -m pytest tests/test_gate_concorrencia.py tests/test_gate_liquidez_rotas.py tests/test_opcoes_fronteira.py tests/test_mydata_budget_prioridade.py -q</automated>
  </verify>
  <done>Limitador e fatia comprovados pelos testes; `grep -c "GATE_CONCORRENCIA = 2" server/app/options_api.py` = 1; `grep -c 'prioridade="descoberta"' server/app/options_api.py` = 1; test_gate_liquidez_rotas.py passa sem edição.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 4: front — fila de concorrência e dedupe do gate em api.js</name>
  <files>web/src/filaGate.js, web/src/api.js, web/tests/test_fila_gate.mjs</files>
  <behavior>
    - `criarFila(2)`: 10 tarefas com promessas controladas → nunca mais que 2 rodando; todas resolvem; ordem de início FIFO; tarefa que rejeita libera o slot e propaga o erro só para o próprio chamador.
    - `criarGateCacheado({ buscar, limite: 2, ttlMs: 120000, agora })`: 3 chamadas do MESMO ticker em voo → `buscar` chamado 1×, as 3 recebem o mesmo resultado; resultado `providerStatus: "ok"` reaproveitado dentro do TTL (relógio injetado) e rebuscado após; resultado `degraded`, `liquida` ausente ou erro NÃO é cacheado (A-07 do backend espelhado); 12 tickers distintos → máximo simultâneo de `buscar` ≤ 2.
    - Guardião estático: `web/src/api.js` define `optionsGate` passando por `criarGateCacheado` (regex sobre a fonte sem comentários) e `GATE_CONCORRENCIA_MAX` exportado é ≤ 2; `store.optionsGate(` continua 1× em App.jsx e 1× em useOpcoesPropostas.js (contagem já travada por test_carteira_opcoes_tira.mjs — repetir aqui como sanidade).
  </behavior>
  <action>
RED: criar `web/tests/test_fila_gate.mjs` no estilo dos `web/tests/*.mjs` existentes (Node puro, `ok(nome, cond)` + exit code; ver o cabeçalho de `web/tests/test_carteira_opcoes_tira.mjs` para o helper e o padrão de "fonte sem comentários"), importando `../src/filaGate.js`. Ver falhar.

GREEN — criar `web/src/filaGate.js` (módulo PURO: sem import de api/persistence/Capacitor; ES module) per QUICK-261006-OAV-RAJADA:
- `export const GATE_CONCORRENCIA_MAX = 2;` `export const GATE_TTL_MS = 120000;`
- `export function criarFila(limite)` → devolve `(tarefa) => Promise` (fila FIFO; `ativos` contador; libera slot em `finally`).
- `export function criarGateCacheado({ buscar, limite = GATE_CONCORRENCIA_MAX, ttlMs = GATE_TTL_MS, agora = () => Date.now() })` → `(t) => Promise`: mapa `emVoo` (ticker → promessa) para dedupe; mapa `cache` (ticker → {em, valor}) só para `valor && valor.providerStatus === "ok"`; senão passa por `criarFila(limite)` chamando `buscar(t)`; remove de `emVoo` em finally.
- Comentário de cabeçalho datado 2026-10-06 (quick 261006-oav): incidente da Mesa (N AtivoCards × gate no mount), por que a fila mora em api.js (contadores de `store.optionsGate(` travados por guardião; paridade deviceStore↔serverStore preservada porque ambos delegam a `api.optionsGate`), timeout de 30 s começa quando a requisição sai da fila (não enquanto espera).

Em `web/src/api.js`: importar `{ criarGateCacheado }` de `./filaGate.js`; criar no módulo `const gateCacheado = criarGateCacheado({ buscar: (t) => req("GET", "/api/options/gate/" + encodeURIComponent(t), undefined, 30000) });` e trocar a linha 317 por `optionsGate: (t) => gateCacheado(t),` mantendo o comentário v2 acima. `req` é declarado antes de `export const api` — confirmar com Grep que `req` está definido antes do ponto onde `gateCacheado` é criado (se for function declaration, hoisting cobre). Nenhum outro método muda. App.jsx, useOpcoesPropostas.js e persistence.js NÃO são tocados. Sem texto novo de UI.

Depois: `cd web && npx vite build` (front editado).
  </action>
  <verify>
    <automated>cd web && node tests/test_fila_gate.mjs && node tests/test_carteira_opcoes_tira.mjs && node tests/test_opcoes_subabas_ui.mjs && node tests/test_api_parity.mjs && node tests/test_opcoes_custo_declarado.mjs && npx vite build</automated>
  </verify>
  <done>test_fila_gate.mjs passa (fila ≤ 2, dedupe, TTL só para ok, guardião estático); os quatro guardiões de front existentes passam sem edição; `npx vite build` rc=0; `git diff --stat web/src` lista só `api.js` e `filaGate.js`.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| cliente → `/api/options/gate/*` | requisição anônima/logada, disparável em rajada por qualquer cliente |
| cliente → `/api/options/buy|sell` e lastreadas | ação do usuário que consome cota do hub |
| servidor → hub mydata | cota combinada 60/min · 2.000/dia, chave só em env do servidor |
| servidor → log (stdout Railway + buffer obslog/admin) | linha de recusa visível a operadores |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-oav-01 | Denial of Service | `options_api.liquidity_gate` | mitigate | semáforo `GATE_CONCORRENCIA=2` + fatia descoberta 21/min + reserva do usuário fora do alcance do gate (Tasks 1 e 3) |
| T-oav-02 | Denial of Service | rotas buy/sell sem cota | mitigate | contexto `usuario` só nas 6 rotas de execução; teto total inalterado; recusa continua 502 determinístico (Task 2) |
| T-oav-03 | Elevation of Privilege | prioridade `usuario` | mitigate | prioridade NUNCA lida do corpo/headers do cliente — fixada no código da rota; ContextVar envolvendo só o await (sem herança por `create_task`) |
| T-oav-04 | Information Disclosure | `registrar_recusa` | mitigate | linha só com rótulos e contadores; teste afirma ausência de "X-API-Key"/nome de env de chave (Task 1) |
| T-oav-05 | Denial of Service (log flooding) | `registrar_recusa` | mitigate | 1 linha por (janela, classe, origem) a cada 60 s com contador `suprimidas` (Task 1) |
| T-oav-06 | Tampering (preço) | reuso cross-key do cache | mitigate | só reaproveita payload `ok` < 300 s do MESMO vencimento; devolve o último prêmio real e a idade (`cotacaoLidaEm`/`cotacaoIdadeS`, null se desconhecida) — nunca estimativa (Task 2) |
| T-oav-SC | Tampering | npm/pip installs | accept | nenhuma dependência nova (stdlib `contextvars`/`contextlib`; JS puro) |
</threat_model>

<verification>
Executor (dentro do plano): os `<automated>` de cada task.

Orquestrador, fora do sandbox, UMA vez no fechamento:
1. `cd web && npx vite build`
2. `cd web && npx cap copy ios`
3. `bash scripts/executar.sh --testes; echo "rc=$?"` — gravar o rc do próprio script no SUMMARY.

Checagens de invariante (executor, antes do SUMMARY):
- `grep -n "yahoo\|brapi" server/app/options_provider_mydata.py | grep -v '^[0-9]*:\s*#'` não ganhou chamada nova (sem fallback, D-04).
- `git diff server/app/options_provider.py` vazio (seletor continua despacho puro).
- `git diff web/src/App.jsx web/src/persistence.js web/src/opcoes/ server/app/skill_ref.py web/src/copy.js` vazio.
</verification>

<success_criteria>
- Testes (1)–(5) pedidos existem e passam: (1)+(2) em test_opcoes_cota_reserva_rotas.py, (3) em test_gate_concorrencia.py, (4) em web/tests/test_fila_gate.mjs, (5) em test_mydata_budget_prioridade.py.
- Teto total 54/min · 1.800/dia inalterado; fundo 44/min · 1.650/dia; reserva do usuário 10/min · 150/dia; descoberta ≤ 21/min (todos configuráveis por env do servidor, sem segredo).
- Mensagem de 502 de buy/sell byte a byte igual à de hoje.
- Nenhum guardião apagado; reconciliações com nota datada 2026-10-06.
- Suíte canônica verde (rc gravado pelo orquestrador).

## Source coverage audit
| Fonte | Item | Coberto por |
|---|---|---|
| GOAL 1 | reserva para ação do usuário (buy/sell + execuções que cobram cadeia), sem aumentar teto, fundo com recusa dura no teto reduzido | Task 1 (classes), Task 2 (6 rotas) |
| GOAL 2 | front não dispara lista inteira (fila/concorrência baixa) | Task 4 |
| GOAL 2 | limitador de concorrência no backend; Mesa ≤ fração da cota/min | Task 3 (semáforo + fatia 40%) |
| GOAL 3 | WARNING com janela, gasto/teto, chamador, rate-limit, sem segredo | Task 1 (`registrar_recusa`), Task 2 (chamada nos 3 ramos) |
| Investigar (a) | chamadores de reservar/pode_gastar/debita + impacto | contexto, tabela (a) |
| Investigar (b) | cache 300 s / vencimentos; reuso pela compra com idade | contexto (b) + Task 2 |
| Investigar (c) | guardiões e reconciliação datada | contexto (c) + Task 1 reconcilia test_mydata_budget |
| Investigar (d) | custo declarado / sem fallback / orçamento | contexto (d) + verificação |
| Restrição | testes (1)–(5) | Tasks 1–4 |
| Restrição | validação final orquestrador | `<verification>` |

Fora do escopo (declarado): carregar só AtivoCards visíveis (IntersectionObserver) — exigiria editar App.jsx e os contadores travados; a fila + dedupe + fatia de descoberta já limitam o gasto. Exibir `cotacaoIdadeS` na UI — exigiria texto novo em skill_ref↔copy.js; a resposta da API já carrega a idade.
</success_criteria>

<output>
Criar `.planning/quick/261006-oav-cota-do-mydata-reservar-para-compra-vend/261006-oav-SUMMARY.md` ao terminar.
</output>
