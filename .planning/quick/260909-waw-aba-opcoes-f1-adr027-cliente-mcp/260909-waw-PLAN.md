---
quick_id: 260909-waw
phase: quick-260909-waw
plan: 01
type: quick
wave: 1
depends_on: []
autonomous: true
files_modified:
  - docs/adr/027-consumo-do-servico-mcp-autenticado.md
  - server/requirements.txt
  - server/requirements-prod.txt
  - server/app/rbac.py
  - server/app/mcp_client.py
  - server/app/options_mcp_api.py
  - server/app/metering.py
  - server/app/main.py
  - server/tests/test_opcoes_fronteira.py
  - server/tests/test_adr013_rbac.py
  - server/tests/test_mcp_client.py
  - server/tests/test_mcp_guardioes.py
  - server/tests/test_mcp_cap.py
  - server/tests/test_mcp_vivo.py
must_haves:
  truths:
    - "Exatamente um módulo de server/app/ importa `mcp`/`httpx2`: `mcp_client`."
    - "`GET /api/options/mcp/status` sem sessão responde 401; com sessão e sem segredo responde 503 `mcp_nao_configurado`."
    - "A 61ª chamada com cota 60 responde 402 sem tocar a rede."
    - "O dia do cap vira às 00:00 de São Paulo, não em UTC."
    - "Nenhuma mensagem/log ecoa `MCP_CLIENT_SECRET` nem o access token."
  artifacts:
    - path: server/app/mcp_client.py
      provides: "cliente único do serviço MCP (token à mão, cache L1, tradução de erro)"
    - path: server/app/options_mcp_api.py
      provides: "router /api/options/mcp com require_user + cap por usuário/dia"
    - path: docs/adr/027-consumo-do-servico-mcp-autenticado.md
      provides: "decisão arquitetural que substitui ADR-024 Decisões 1 e 2"
  key_links:
    - from: server/app/main.py
      to: server/app/options_mcp_api.py
      via: "options_mcp_api.configure(_conn, require_user) + app.include_router"
    - from: server/app/options_mcp_api.py
      to: server/app/metering.py
      via: "check/consume nas seções mcpUsage/mcpUsageGlobal/mcpUsageMonth"
---

<objective>
Fase 1 do `docs/PLANO-aba-opcoes.md` (aprovado pelo Alex em 2026-09-09): abrir a
fronteira nova do ADR-027 — um cliente único do serviço MCP autenticado
(`mcp.semente.dev`), com cap por usuário/dia ancorado em São Paulo, uma única
rota (`GET /api/options/mcp/status`) e os guardiões que passam a valer.

**Escopo EXATO:** §2 (ADR-027), §3.1 (cliente), §3.2 (cap), §3.3 só `/status`,
§3.7 (dependências/env) e a "Fase 1" de §4. Nada de front, nada das rotas de
leitura/veredito/setups, nada de deploy.

Purpose: sem isto a aba Opções não tem de onde tirar fato — e o guardião atual
(`test_opcoes_fronteira`) proíbe literalmente a dependência `mcp`.
Output: 1 ADR, 2 módulos novos, 4 arquivos de teste novos, 2 guardiões
reescritos com nota, 1 grupo RBAC.
</objective>

<context>
@docs/PLANO-aba-opcoes.md  (PLANO APROVADO — o executor NÃO edita este arquivo)
@/Users/acamerini/dev/MCP/docs/contrato-mcp-servico.md
@server/app/mydata_client.py  (padrão de cliente HTTP: url validada, retry, nunca eco de token)
@server/app/metering.py
@server/app/options_api.py  (padrão de APIRouter)
@server/app/rbac.py
@server/app/obslog.py
@server/tests/test_opcoes_fronteira.py
@docs/adr/024-limite-interno-rastrear-avaliar.md
@docs/adr/026-execucao-de-estrutura-multiperna.md  (formato/estilo de ADR da casa)

## Fatos do SDK — VERIFICADOS nesta sessão (não re-descobrir)

Rodado contra `server/.venv/bin/python` (Python 3.14, `mcp` **2.2.0**):

- `mcp.shared.exceptions.MCPError` (classe é `MCPError`, NÃO `McpError`).
  Atributos confirmados por `inspect` do fonte
  (`server/.venv/lib/python3.14/site-packages/mcp/shared/exceptions.py`):
  `e.error` é um `ErrorData` com `.code`/`.message`/`.data`, **e** existem as
  properties de conveniência `e.code` / `e.message` / `e.data`. Instância de
  teste `MCPError(code=-32000, message="x", data={"a":1})` devolveu
  `e.error.code == -32000` e `e.error.data == {"a": 1}`.
  **Use `e.error.code` / `e.error.data`** (forma canônica do SDK).
- `streamable_http_client(url: str, *, http_client: httpx2.AsyncClient | None = None,
  terminate_on_close: bool = True)` → **tupla de DOIS** `(leitura, escrita)`.
- `ClientSession.call_tool(name, arguments=None, read_timeout_seconds: float|None = None, ...)`
  — `read_timeout_seconds` é **float**, não `timedelta`.
- `ClientSession.get_prompt(name, arguments: dict[str,str] | None = None, ...)`;
  `ClientSession.read_resource(uri: str, ...)` — `uri` é **str**.
- Resposta em snake_case: `r.structured_content`, `r.is_error`, `info.server_info`.
- Versões instaladas hoje na venv: fastapi 0.141.1, starlette 1.6.0,
  pydantic 2.13.5, uvicorn 0.52.4, mcp 2.2.0, httpx2 2.12.0, httpx 0.28.1,
  mcp_types 2.2.0, python-multipart 0.0.32.
- **NÃO usar `ClientCredentialsOAuthProvider`**: o `async_auth_flow` segura um
  lock durante o round-trip inteiro e serializaria todas as chamadas MCP do
  processo. Token à mão, como o próprio contrato documenta.

## Legitimidade do pacote (gate de instalação)

`mcp` — **[VERIFICADO]**, não `[ASSUMED]`: (a) é o SDK oficial do Model
Context Protocol, (b) já está instalado em `server/.venv` (2.2.0, módulo real
em `.../site-packages/mcp/__init__.py`, exercitado por `inspect` acima), (c) é
a dependência nominal do contrato do serviço
(`~/dev/MCP/docs/contrato-mcp-servico.md`, "Dependência: `mcp>=2.1,<3`"), (d)
está no PLANO aprovado (§3.7). `httpx2`, `mcp_types` e `python-multipart`
entram como transitivos do SDK — nenhuma linha própria nos requirements.
Nenhum pacote `[ASSUMED]`/`[SUS]` nesta quick → sem checkpoint humano de
legitimidade.

## Achados de inventário que mudam o desenho (verificados no código)

1. **`metering._now` NÃO decide o dia.** `metering.check(..., _now=...)` só
   alimenta o rate limit (`now - t < 60.0`, epoch float); o dia sai de
   `_today()` (linhas 29-30, `datetime.now(timezone.utc)`), sem ponto de
   injeção. Logo, a contingência prevista em §3.2 do PLANO **se aplica**: a
   seção mcp precisa de `_dia`/`_mes` próprios em SP (Task 3).
2. **Import circular no router.** `require_user` e `_conn` nascem em
   `main.py`; `options_mcp_api` não pode importá-los. Solução pelo padrão que
   o repo já usa (`configure_db`, `set_historico_provider`): `configure(conn,
   require_user)` chamado por `main.py`. A dependency local **se chama
   `require_user`** (delegação), o que mantém `test_adr013_cobertura_rotas`
   verde sem mexer na allowlist (que fica em 19).
3. **`test_adr013_rbac.py`** tem DUAS asserções de contagem: o `set` em
   `test_primeiro_usuario_bootstrap_recebe_todas_as_7_permissoes` (8 itens) e
   `len(...) == 8` na linha 113. Ambas sobem para 9.
4. **`web/tests/test_fase5_auditoria_perm.mjs` não é afetado** — ele só lê
   `web-admin/src/App.jsx`, intocado. Confirmado por leitura ([R-11] honrado).
5. **Guardiões que varrem `server/app/*.py` inteiro** (`test_faixas_liquidez`,
   `test_opcoes_collar_vocab`, `test_lastro_trava`) proíbem âncoras de texto de
   liquidez/collar e a subtração `qty - qtyTravada`. Os módulos novos não
   tocam nenhum desses temas — só não introduza esses literais.
6. **pytest roda com rootdir `server/`** (`server/pytest.ini`: `pythonpath = .`,
   `testpaths = tests`). Comando individual:
   `cd /Users/acamerini/dev/borisv2/server && .venv/bin/python -m pytest -q tests/<arquivo>`.

## Decisão que reconcilia duas restrições (registrar no SUMMARY)

O mapeamento HTTP manda `McpErroDeTool → 422`; a regra de frescor manda
`bloqueia = ... OU erro da tool`. Em `/status` as duas se cruzam. **Decisão:**
`/status` captura `McpErroDeTool` e responde **200** com
`frescor.warning = <mensagem da tool>` e `frescor.bloqueia = true` — porque a
finalidade de `/status` é justamente reportar o estado do dado (princípio 9 do
CLAUDE.md: estados completos, "idade desconhecida" nunca vira "em dia"). O 422
segue valendo no helper `_erro_http`, usado pelas rotas das Fases 2+. Ambos os
caminhos são testados. Levar ao Alex no SUMMARY.
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: ADR-027, pins de dependência, guardiões invertidos e grupo RBAC `opcoes`</name>
  <files>docs/adr/027-consumo-do-servico-mcp-autenticado.md, server/requirements.txt, server/requirements-prod.txt, server/app/rbac.py, server/tests/test_opcoes_fronteira.py, server/tests/test_adr013_rbac.py</files>
  <behavior>
    - Guardião B (novo) FALHA agora e passa na Task 2: conjunto de módulos de `server/app/` que importam raiz `mcp` OU `httpx2` deve ser **exatamente** `{"mcp_client"}`; hoje é vazio → RED deliberado.
    - Guardião B-requirements (invertido) PASSA já nesta task: `mcp>=2.1,<3` presente e **idêntico** nos dois requirements.
    - Guardião A PASSA: `httpx2` acrescentado a `_IMPORTS_PROIBIDOS_REDE` (hoje `"httpx2" != "httpx"` passava pelo filtro).
    - Guardião C PASSA inalterado.
    - `test_adr013_rbac`: bootstrap passa a devolver 9 permissões.
  </behavior>
  <action>
**1. `docs/adr/027-consumo-do-servico-mcp-autenticado.md`** — transcreva o §2 do
`docs/PLANO-aba-opcoes.md` (Contexto, Decisões 1–10, Consequências, Guardiões)
no formato de `docs/adr/026-*.md`: cabeçalho `# ADR-027: ...`, `**Status:**
Proposto`, `**Data:** 2026-09-09`, `**Decisor:** Alex (aprovação do
docs/PLANO-aba-opcoes.md, 2026-09-09)`, `**Substitui:** ADR-024 Decisões 1 e 2
(a Decisão 3 — canal único do MyData, Guardião C — permanece e se estende ao
canal MCP)`, `**Relaciona:** ADR-004, 010, 013, 018, 020, 021–026`. Não invente
decisão que não está no §2. Registre em "Consequências" o achado 1 do contexto
(o `_now` do metering não decide o dia — por isso a seção mcp ganha `_dia`/`_mes`
próprios) e a decisão de `/status` do fim do `<context>`. Não edite o ADR-024
(ele fica como está; quem o substitui é este).

**2. `server/requirements.txt` e `server/requirements-prod.txt`** — nos DOIS,
pins exatos (versões medidas hoje na venv) e a dependência nova:

```
fastapi==0.141.1
starlette==1.6.0
pydantic==2.13.5
uvicorn[standard]==0.52.4
httpx>=0.27
# ADR-027 (aba-opcoes F1): SDK do serviço MCP autenticado. Traz httpx2,
# mcp_types e python-multipart como transitivos — sem linha própria.
mcp>=2.1,<3
```

`requirements.txt` mantém `pytest>=8.0` sob o comentário `# dev/test`; os dois
mantêm `PyJWT[crypto]>=2.8` e `h2>=4.1`. A linha do `mcp` tem de ficar
**byte a byte igual** nos dois arquivos (o guardião compara). Comente no
`requirements-prod.txt` que os pins vieram de uma venv 3.14 e que produção roda
3.12 (`server/.python-version`) — se a resolução falhar em 3.12, **pare e
reporte ao Alex**, não relaxe o pin por conta própria.

**3. `server/app/rbac.py`** — acrescente a `GRUPOS` (crescer é acrescentar, o
módulo diz isso na docstring): `"opcoes": {"opcoes.criar_setup"}`, com comentário
citando ADR-027 §2.7 (armazém de setups sem `owner`; só `role_admin` recebe no
bootstrap; ler/avaliar/ver gráfico valem para todos). **NÃO** acrescente entrada
em `ENTIDADES_POR_PERMISSAO`: nenhum `audit.record` grava entidade de setup
ainda — deixe um comentário de uma linha dizendo que a entrada entra na Fase 5,
quando a rota de escrita existir, para não quebrar o contrato documentado do
mapa ("cobre toda `entity` HOJE gravada").

**4. `server/tests/test_opcoes_fronteira.py`** — reescreva os guardiões COM NOTA
(guardião de teste não se apaga; reversão deliberada atualiza com nota — guardrail
do CLAUDE.md). Acrescente à docstring de topo um bloco datado
`2026-09-09 (aba-opcoes F1, ADR-027)` explicando o que mudou e por quê (os dois
motivos do ADR-024 caíram: `mcp.semente.dev` serve dado real, e o transporte é
streamable-http, não stdio).

- **A:** acrescente `"httpx2"` a `_IMPORTS_PROIBIDOS_REDE` (com comentário: o
  SDK novo trouxe um segundo stack HTTP e o filtro antigo não o via).
- **B:** substitua `test_guardiao_b_nenhum_modulo_do_app_importa_cliente_mcp`
  por `test_guardiao_b_um_unico_modulo_importa_mcp_e_httpx2`, com **igualdade de
  conjunto**:
  ```python
  _RAIZES_MCP = {"mcp", "httpx2"}
  _IMPORTADORES_PERMITIDOS = {"mcp_client"}
  importadores = {c.stem for c in _modulos_app() if _imports(c) & _RAIZES_MCP}
  assert importadores == _IMPORTADORES_PERMITIDOS, ...
  ```
  Mensagem de falha: canal paralelo ao serviço MCP; a resposta não é editar a
  allowlist, é levar a decisão ao Alex. Mantenha uma nota de que a versão
  anterior proibia `mcp` em TODO módulo e por que isso caiu.
- **B-requirements:** substitua `test_guardiao_b_mcp_nao_esta_nos_requirements`
  por `test_guardiao_b_mcp_esta_nos_requirements_e_igual_nos_dois`: extrai as
  linhas que começam com `mcp` (case-insensitive, ignorando comentários e
  espaços) dos dois arquivos, exige exatamente uma em cada, exige que sejam
  iguais entre si e que contenham `>=2.1` e `<3`. Nota: o teste antigo proibia
  a dependência (T-15-SC) e o ADR-027 inverteu a decisão.
- **C, D, E, ENG-04:** intocados.

**5. `server/tests/test_adr013_rbac.py`** — renomeie
`test_primeiro_usuario_bootstrap_recebe_todas_as_7_permissoes` para
`..._todas_as_9_permissoes` (o nome já estava defasado: o `set` tinha 8),
acrescente `"opcoes.criar_setup"` ao `set` esperado, e ajuste a linha 113 para
`== 9` com o comentário atualizado (`# 8 grupos + controlar (execucao_automatica
tem 2)`). Deixe nota de uma linha citando ADR-027 §2.7.

**Commit** ao fim: `feat(260909-waw): ADR-027, pins e guardioes invertidos (aba-opcoes F1)`.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/server && .venv/bin/python -m pytest -q tests/test_opcoes_fronteira.py tests/test_adr013_rbac.py tests/test_opcoes_gatilho.py tests/test_adr013_cobertura_rotas.py --deselect tests/test_opcoes_fronteira.py::test_guardiao_b_um_unico_modulo_importa_mcp_e_httpx2 && ! .venv/bin/python -m pytest -q tests/test_opcoes_fronteira.py::test_guardiao_b_um_unico_modulo_importa_mcp_e_httpx2</automated>
  </verify>
  <done>ADR-027 existe com as 10 decisões do §2; `mcp>=2.1,<3` idêntico nos dois requirements; grupo `opcoes` em `GRUPOS`; bootstrap devolve 9 permissões; o guardião B novo é a ÚNICA falha da suíte (RED deliberado, verde na Task 2).</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: `server/app/mcp_client.py` — o único importador de `mcp`/`httpx2`</name>
  <files>server/app/mcp_client.py, server/tests/test_mcp_client.py, server/tests/test_mcp_guardioes.py</files>
  <behavior>
    - `error` no `structured_content` (com `is_error: false`) → `McpErroDeTool` com `available`/`hint`.
    - `MCPError(code=-32000, data={...})` → `McpTetoAtingido` com `.data["reinicia"]` preservado.
    - Sem `MCP_CLIENT_ID`/`MCP_CLIENT_SECRET` → `McpNaoConfigurado`, sem tocar a rede.
    - Token renovado quando faltam ≤5 min para o `exp` (relógio fixo), e reusado quando falta mais que isso.
    - Cache: 2ª chamada com mesmos `(tool, args)` dentro do TTL não toca a sessão e devolve `cache=True`.
    - `MCP_URL` com esquema diferente de `https` → `ValueError`.
    - Nenhuma mensagem de exceção contém o segredo nem o access token.
  </behavior>
  <action>
Crie `server/app/mcp_client.py`. Docstring de topo no padrão de
`mydata_client.py`: o que é (fronteira única do ADR-027), o que NÃO faz
(nenhuma rota, nenhum cap — isso é `options_mcp_api`), e por que o token é
pedido à mão (o `ClientCredentialsOAuthProvider` segura um lock durante o
round-trip inteiro e serializaria o processo).

**Constantes** (todo literal de URL é do contrato — o guardião (ii) da Task 3
confere):
`URL_CONTRATO = "https://mcp.semente.dev/mcp"`, `URL_TOKEN =
"https://id.semente.dev/token"`, `TIMEOUT_S = 30.0`, `CONCORRENCIA = 4`,
`MARGEM_RENOVACAO_S = 300`, `TTL_DEFAULT_S = 900`, `TTL_FRESCOR_S = 600`,
`TTL_ESTATICO_S = 3600`, `CODIGO_TETO = -32000`.

**Exceções** — hierarquia exata:
`McpErro(RuntimeError)` base; `McpNaoConfigurado(McpErro)`;
`McpNaoAutorizado(McpErro)`; `McpIndisponivel(McpErro)`;
`McpTetoAtingido(McpErro)` com `__init__(self, msg, data=None)` guardando
`self.data = dict(data or {})`; `McpErroDeTool(McpErro)` com
`__init__(self, msg, available=None, hint=None)`.

**Configuração:**
- `configurado() -> bool` — `MCP_CLIENT_ID` e `MCP_CLIENT_SECRET` ambos não
  vazios (após `.strip()`).
- `url() -> str` — lê `MCP_URL` (default `URL_CONTRATO`); valida com
  `urllib.parse.urlsplit`: **só `https`**; qualquer outro esquema levanta
  `ValueError` com a mesma justificativa de `mydata_client.base_url`
  (é o único ponto que decide para onde o token viaja).
- `_ttl_default() -> int` — lê `B3_MCP_CACHE_S` a cada chamada (default
  `TTL_DEFAULT_S`), para o teste poder mexer via `monkeypatch.setenv`.

**Relógios injetáveis** (os testes fixam o tempo sem `freezegun`):
`def _relogio() -> float: return time.time()` (parede, expiração do token) e
`def _mono() -> float: return time.monotonic()` (cache L1). Use SEMPRE essas
duas funções, nunca `time.*` direto no corpo.

**HTTP e SDK com import TARDIO** — `import httpx2` e os três nomes do `mcp`
(`ClientSession`, `streamable_http_client`, `MCPError`) ficam DENTRO das
funções, não no topo. Motivo (escreva no comentário): `main.py` importa este
módulo na cadeia de boot; um SDK ausente derrubaria o app inteiro em vez de só
a aba Opções. `ImportError` vira
`McpNaoConfigurado("SDK do serviço de opções não instalado neste ambiente.")`.
Isto NÃO afeta o guardião B: `_imports()` de `test_opcoes_fronteira` usa
`ast.walk`, que visita corpo de função (a própria docstring do helper diz isso).

**Cliente HTTP:** `_HTTP = None` no módulo; `_cliente_http()` cria uma única
`httpx2.AsyncClient(timeout=TIMEOUT_S)` por processo e a devolve. O header
`Authorization` é escrito em `_HTTP.headers` na renovação do token (o token é o
mesmo para todo o processo; comente isso). Os testes monkeypatcham
`mcp_client._cliente_http`.

**Token à mão** — `_TOKEN: dict = {}` (`{"access_token", "exp"}`),
`_LOCK = asyncio.Lock()`, `_SEM = asyncio.Semaphore(CONCORRENCIA)`:
```
async def _access_token() -> str
```
1. fora do lock: se há token e `_TOKEN["exp"] - MARGEM_RENOVACAO_S > _relogio()`,
   devolve;
2. dentro do `_LOCK`: repete a checagem (double-check — sem isso N corrotinas
   concorrentes pedem N tokens);
3. lê `MCP_CLIENT_ID`/`MCP_CLIENT_SECRET`; vazio → `McpNaoConfigurado(
   "Serviço de opções não configurado no servidor.")`;
4. `POST URL_TOKEN` com `headers={"Authorization": "Basic " +
   base64.b64encode(f"{cid}:{seg}".encode()).decode(),
   "Content-Type": "application/x-www-form-urlencoded"}` e
   `data={"grant_type": "client_credentials", "resource": url()}`;
5. `401/400/403` → `McpNaoAutorizado("o emissor recusou a credencial do serviço
   de opções (confira MCP_CLIENT_ID/MCP_CLIENT_SECRET e o registro do client).")`
   — **sem corpo da resposta na mensagem**; `>=500` ou exceção de transporte →
   `McpIndisponivel`;
6. sucesso: guarda `access_token` e `exp = _relogio() + int(expires_in)`, escreve
   o header no cliente compartilhado, devolve.

**Núcleo de chamada:**
```
async def _chamar(rotulo: str, executar)   # executar(sessao) -> Any
```
- pega token, cliente HTTP e `u = url()`;
- `async with _SEM:` → `async with streamable_http_client(u, http_client=http)
  as (leitura, escrita):` (**tupla de DOIS**) → `async with
  ClientSession(leitura, escrita) as sessao:` → `await sessao.initialize()` →
  `return await executar(sessao)`;
- tradução de exceção, nesta ordem: `McpErro` (re-levanta como está) →
  `MCPError` com `e.error.code == CODIGO_TETO` → `McpTetoAtingido(e.error.message,
  e.error.data)` + `obslog.log("mcp", "teto do serviço atingido", level="error",
  escopo=..., chamadas_hoje=...)`; outro `MCPError` → `McpIndisponivel` (a
  mensagem interna pode citar o código; quem fala com o usuário é a rota) →
  qualquer outra: leia `status = getattr(getattr(e, "response", None),
  "status_code", None)`; `401/403` → `McpNaoAutorizado`; caso geral →
  `McpIndisponivel(f"serviço de opções inacessível: {type(e).__name__}")`.
  **Use só `type(e).__name__`, nunca `{e!r}`** — o repr de um erro de httpx2
  pode arrastar headers (é a diferença deliberada em relação a
  `mydata_client._fetch_json`, comente isso).

**Cache L1** — `_CACHE: dict[tuple[str, str], tuple[float, Any]] = {}`,
chave `(rotulo, json.dumps(args, sort_keys=True, ensure_ascii=False))`, valor
`(_mono(), resultado)`. `_cache_get(chave, ttl)` devolve `None` no miss/expirado;
`_cache_put(chave, valor)` só é chamado no SUCESSO (decisão A-07 do ADR-020 —
cite no comentário). `reset_cache()` limpa `_CACHE` **e** `_TOKEN` (o token
também é cache; documente na docstring da função) — é o que os testes chamam.

**API pública:**
```python
class ResultadoTool(NamedTuple):
    dados: dict
    cache: bool
```
Motivo do `NamedTuple` (comente): o cap precisa saber se a chamada tocou a rede
e um flag global seria racy sob concorrência.

- `async def call_tool(nome, args=None, *, read_timeout_seconds=TIMEOUT_S) -> ResultadoTool`
  — TTL: `TTL_FRESCOR_S` se `nome == "check_data_freshness"`, senão
  `_ttl_default()`. No miss: `sessao.call_tool(nome, args or {},
  read_timeout_seconds=read_timeout_seconds)`; `sc = getattr(r,
  "structured_content", None) or {}`; **cheque as duas coisas** (contrato):
  `if getattr(r, "is_error", False) or "error" in sc:` →
  `McpErroDeTool(str(sc.get("error") or "a tool recusou o pedido"),
  available=sc.get("available"), hint=sc.get("hint"))` — e NÃO cacheia.
  Sucesso: cacheia, `obslog.log("mcp", f"tool {nome}", tool=nome, cache=False,
  ms=int((_relogio()-t0)*1000))`; no hit, o mesmo log com `cache=True` e sem `ms`.
- `async def get_prompt(nome, args: dict[str, str] | None = None)` e
  `async def read_resource(uri: str)` — mesma estrutura, TTL `TTL_ESTATICO_S`,
  rótulos `"prompts/get"` e `"resources/read"`, devolvendo `ResultadoTool` com o
  objeto do SDK em `dados`. Ambos são de graça no teto do serviço (protocolo),
  então **não** entram no cap.

**`server/tests/test_mcp_client.py`** — offline, sessão falsa, nenhuma rede.
Fixture `autouse` chamando `mcp_client.reset_cache()` antes e depois. Padrão:
uma classe `_SessaoFalsa` com `call_tool`/`get_prompt`/`read_resource`
contando chamadas, e monkeypatch de `mcp_client._chamar` (para os testes de
cache/erro de tool) ou de `_cliente_http` (para os de token). Cobrir os 7 itens
de `<behavior>` acima, um teste por item, mais:
`asyncio.run(...)` no estilo já usado em `test_opcoes_fronteira.py` (Guardião D).
No teste de `-32000`, construa `MCPError(code=-32000, message="teto diário...",
data={"reinicia": "00:00 America/Sao_Paulo", "escopo": "cliente",
"chamadas_hoje": 2000})` e afirme `exc.value.data["reinicia"]`.
No teste de token, monkeypatche `mcp_client._relogio` para um valor fixo e
confira: (a) `exp` a 10 min de distância → **não** pede token novo; (b) `exp` a
4 min → pede; (c) nenhuma mensagem de exceção contém o valor de
`MCP_CLIENT_SECRET` (afirme `segredo not in str(exc.value)`).

**`server/tests/test_mcp_guardioes.py`** — mesmo estilo AST de
`test_opcoes_fronteira` (reaproveite `_imports`/`_strings` copiando os helpers
com a exclusão de docstring **por posição**, nunca por valor). Nesta task,
três guardiões (os outros dois entram na Task 3; deixe um comentário
`# (iv) e (v) entram na Task 3, com o router`):
- **(i)** nem `"fixture"`, nem `"MYDATA_MODO"`, nem `"b-mcp"` como literal de
  string em `mcp_client.py` (a lista de arquivos vira uma constante
  `_ARQUIVOS_DA_FRONTEIRA`, para a Task 3 só acrescentar `options_mcp_api.py`).
- **(ii)** todo literal de string em `mcp_client.py` que contenha `"://"` tem de
  estar em `{URL_CONTRATO, URL_TOKEN}` — os dois vêm do contrato. (Não use
  "toda URL": `"mcp.semente.dev"` sem esquema é rótulo de fonte, não URL, e é
  legítimo na resposta da rota.)
- **(iii)** nenhum literal em `server/app/*.py` com formato de segredo:
  `re.compile(r"mcp_[A-Za-z0-9]+_[A-Za-z0-9_-]{20,}")` (chave de máquina legada
  do contrato) e `re.compile(r"\beyJ[A-Za-z0-9_-]{10,}")` (JWT). Varra
  `_modulos_app()` inteiro, não só os novos.

**Commit:** `feat(260909-waw): mcp_client, fronteira unica do ADR-027 (aba-opcoes F1)`.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/server && .venv/bin/python -m pytest -q tests/test_mcp_client.py tests/test_mcp_guardioes.py tests/test_opcoes_fronteira.py tests/test_opcoes_gatilho.py</automated>
  </verify>
  <done>`mcp_client.py` existe e é o único módulo de `server/app/` que importa `mcp`/`httpx2` (guardião B agora VERDE); os 7 comportamentos passam offline; nenhum literal de segredo ou URL fora do contrato.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: router `/api/options/mcp/status`, cap por usuário/dia em SP e fiação no main</name>
  <files>server/app/options_mcp_api.py, server/app/metering.py, server/app/main.py, server/tests/test_mcp_cap.py, server/tests/test_mcp_vivo.py, server/tests/test_mcp_guardioes.py</files>
  <behavior>
    - `GET /api/options/mcp/status` sem `Authorization` → 401 (antes do cap).
    - Logado, sem `MCP_CLIENT_SECRET` → 503 com `detail.code == "mcp_nao_configurado"`.
    - Com `mcpUsage.count == 60` e cota 60 → 402 `mcp_cota` e **zero** chamadas ao serviço (espião).
    - `consume` grava em `mcpUsage`/`mcpUsageGlobal`/`mcpUsageMonth` e **não** toca `aiUsage*`.
    - `_dia_sp(2026-09-10T02:30Z) == "2026-09-09"` enquanto `metering._today()` (UTC) diria `2026-09-10`.
    - Cache hit não consome cap (2ª chamada seguida não incrementa `mcpUsage.count`).
    - `McpErroDeTool` em `/status` → 200 com `frescor.bloqueia is True` e `frescor.warning` preenchido.
    - `McpTetoAtingido` → 402 `mcp_teto_servico` com `reinicia` e `escopo` vindos do `data` do serviço.
    - `test_mcp_vivo.py` faz `skip` sem `MCP_CLIENT_SECRET`.
  </behavior>
  <action>
**1. `server/app/metering.py`** — o achado 1 do `<context>`: `_now` não decide o
dia. Acrescente overrides OPCIONAIS de dia/mês, com default `None` preservando
**byte a byte** o comportamento atual (nenhum call site existente muda):
`_today(_dia=None)`, `_month(_mes=None)`, `_load(..., _dia=None)`,
`_load_global(..., _dia=None)`, `_load_month(..., _mes=None)`,
`month_used(..., _mes=None)`, `global_snapshot(..., _dia=None)`,
`check(..., _dia=None)`, `consume(..., _dia=None, _mes=None)`.
Acrescente também `used(conn, user_id, *, section=SECTION, _dia=None) -> int`
(espelho de `month_used`, para a rota ler `usado` sem duplicar a lógica de dia).
Comentário obrigatório no topo dizendo **por que**: `_now` só alimenta o rate
limit; o dia sai de `_today()` em UTC; a aba Opções precisa do mesmo reset do
serviço MCP (00:00 America/Sao_Paulo), então quem chama passa o dia pronto —
`_dia`/`_mes` sempre viajam juntos (a regra que já está escrita em `_month`:
nunca duas noções de tempo diferentes para dia e mês).

**2. `server/app/options_mcp_api.py`** — `APIRouter(prefix="/api/options/mcp",
tags=["options-mcp"])`, no padrão de `options_api.py`.

Fuso: `BRT = timezone(timedelta(hours=-3))` local ao módulo, com o comentário
padrão do repo (`store.py:16-21`, `brapi.py:31-33`: sem horário de verão desde
2019; não há módulo compartilhado de fuso). O texto de reset exposto ao usuário
é a string do contrato: `RESET_TXT = "00:00 America/Sao_Paulo"`.

Injeção (achado 2 do `<context>`): `_conn = None`, `_require_user = None`, e
```python
def configure(conn, require_user_dep) -> None:
```
que preenche os dois globais. A dependency da rota **precisa se chamar
`require_user`** (é o nome que `test_adr013_cobertura_rotas` reconhece, e é o
que ela de fato é):
```python
def require_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """Delegação ao require_user de main.py, injetado por configure() — o
    router não pode importar main (ciclo). Mesmo nome de propósito: é a MESMA
    checagem, e é o nome que o guardião de cobertura de rotas reconhece."""
    if _require_user is None:
        raise HTTPException(503, {...code: "mcp_nao_configurado"...})
    return _require_user(authorization)
```

Envs (lidas a cada chamada, para o teste usar `monkeypatch.setenv`):
`_cota_usuario()` ← `B3_MCP_COTA_USUARIO_DIA` (60), `_rate_min()` ←
`B3_MCP_RATE_MIN` (20), `_cota_global()` ← `B3_MCP_COTA_GLOBAL_DIA` (1800).
Valor não-numérico cai no default (não derrube a rota por env torta).

Dia/mês: `_dia_sp(agora=None)` e `_mes_sp(agora=None)` — aceitam um `datetime`
aware para o teste fixar o relógio, fazem `.astimezone(BRT)` e formatam
`%Y-%m-%d` / `%Y-%m`.

Cap:
```python
SECTION = "mcpUsage"; GLOBAL_SECTION = "mcpUsageGlobal"; MONTH_SECTION = "mcpUsageMonth"

def _cap_check(uid: str, custo: int) -> None      # levanta HTTPException(402)
def _cap_consume(uid: str, custo: int) -> None
```
`_cap_check`: `custo <= 0` → retorna; senão `metering.check(_conn, uid,
quota=_cota_usuario(), rate_per_min=_rate_min(), custo=custo,
cap_global=_cota_global(), section=SECTION, global_section=GLOBAL_SECTION,
_dia=_dia_sp())`. Em `not ok`, **descarte o `reason` do metering** (é copy de
BYOK, §3.2 do PLANO) e levante
`HTTPException(402, {"code": "mcp_cota", "message": "Cota do dia da aba Opções
esgotada.", "usado": metering.used(_conn, uid, section=SECTION, _dia=_dia_sp()),
"limite": _cota_usuario(), "reinicia": RESET_TXT})`.
`_cap_consume`: `custo <= 0` → retorna; senão `metering.consume(_conn, uid,
custo=custo, section=SECTION, global_section=GLOBAL_SECTION,
month_section=MONTH_SECTION, _dia=_dia_sp(), _mes=_mes_sp())` — o
`month_section` explícito é o que o guardião (v) exige.

Tradução de erro — `def _erro_http(e: mcp_client.McpErro) -> HTTPException`,
exatamente:
- `McpNaoConfigurado` → 503 `{"code": "mcp_nao_configurado", "message":
  "Serviço de opções não configurado no servidor.", "action": "Defina
  MCP_CLIENT_ID e MCP_CLIENT_SECRET no Railway."}`
- `McpTetoAtingido` → 402 `{"code": "mcp_teto_servico", "message": <frase sem
  segredo>, "reinicia": e.data.get("reinicia"), "escopo": e.data.get("escopo")}`
- `McpNaoAutorizado` e `McpIndisponivel` → 503 `{"code": "mcp_indisponivel",
  "message": "O serviço de opções não respondeu agora. Tente de novo em alguns
  minutos."}` — **sem número e sem segredo** na mensagem (o detalhe vai só para
  `obslog`).
- `McpErroDeTool` → 422 `{"code": "mcp_erro_de_tool", "message": str(e),
  "available": e.available, "hint": e.hint}`
- qualquer outro `McpErro` → 503 `mcp_indisponivel`. **Nada cai no handler 500.**

Frescor — `def _frescor(sc: dict | None, erro: str | None) -> dict`, tolerante à
forma (a forma real de `check_data_freshness` só se confirma ao vivo; **não
invente número**):
- procure a coleção de classes em `sc` nas chaves `classes`, `class_status`,
  `dados`, `status`; aceite `list[dict]` ou `dict[nome -> info]`; normalize cada
  item para `{"classe": <nome>, "situacao": <status/situacao/estado>,
  "bruto": <item original>}`;
- `stale` = classes com `situacao != "em_dia"`;
- `warning` = `erro` (se houver) **ou** `sc.get("warning")` **ou**, se a classe
  `negociacao_b3` não for encontrada, `"frescor não medido: a classe
  negociacao_b3 não veio na resposta"`;
- `bloqueia` = `bool(warning)` ou `negociacao_b3` com `situacao != "em_dia"`;
- inclua `"bruto": sc` no dicionário devolvido — a Fase 2 vai precisar da forma
  real e não deve gastar outra chamada ao vivo para descobri-la.

Rota:
```python
@router.get("/status")
async def status(user: dict = Depends(require_user)) -> dict:
```
1. `uid = user["id"]`; `_cap_check(uid, 1)` (recusa ANTES de chamar);
2. `try: r = await mcp_client.call_tool("check_data_freshness", {})`
   - `except mcp_client.McpErroDeTool as e:` → `r = None; erro_tool = str(e)`
     (decisão registrada no `<context>`: `/status` reporta o estado, não 422);
   - `except mcp_client.McpErro as e:` → `raise _erro_http(e)`;
3. `if r is not None and not r.cache: _cap_consume(uid, 1)` — cache não gasta cap;
4. devolva
```
{"pregao": <sc.get("trading_date") or sc.get("pregao") or None>,
 "fonte": "mcp.semente.dev",
 "at": datetime.now(BRT).strftime("%d/%m/%Y %H:%M") + " BRT",
 "frescor": _frescor(sc, erro_tool),
 "cap": {"usado": metering.used(...), "limite": _cota_usuario(), "reinicia": RESET_TXT}}
```
`pregao` é `None` quando a resposta não traz pregão — **nunca** um valor
fabricado (princípio 4 do CLAUDE.md).
`obslog.log("mcp", "status", rota="/api/options/mcp/status", uid=uid,
cache=..., bloqueia=...)` por chamada.

**3. `server/app/main.py`** — três edições cirúrgicas:
- import junto dos outros de opções (~linha 46): `from . import options_mcp_api
  # aba-opcoes F1 (ADR-027): router do serviço MCP autenticado` e
  `from .options_mcp_api import router as options_mcp_router`;
- **depois** da definição de `require_permission` (~linha 180, porque
  `require_user` precisa já existir):
  ```python
  # aba-opcoes F1 (ADR-027): o router precisa da conexão e do require_user que
  # nascem aqui. Injeção pelo mesmo padrão de configure_db/set_historico_provider
  # — main importa o módulo, nunca o contrário (evita import circular).
  options_mcp_api.configure(_conn, require_user)
  app.include_router(options_mcp_router)
  ```
- aviso de boot de env com espaço (~linha 3427): acrescente `"MCP_"` à tupla
  `("B3_", "APNS_", "APPLE_", "BOLSAI")`.
Nada mais em `main.py`. Não mexa na ordem dos `app.mount()`.

**4. `server/tests/test_mcp_cap.py`** — `TestClient`, no padrão de
`test_adr013_rbac.py` (`_client(monkeypatch)` com DB temporário + registro de
usuário). Um teste por item de `<behavior>`, mais o espião: monkeypatch de
`mcp_client.call_tool` por uma corrotina que registra as chamadas numa lista, e
`assert chamadas == []` no caso de 402. Para o teste de cota cheia, escreva o kv
direto (`db.kv_set(conn, "mcpUsage", {"day": options_mcp_api._dia_sp(),
"count": 60, "rl": []}, user_id=uid)`) — não faça 60 chamadas.
Teste do fuso sem monkeypatch de relógio:
`options_mcp_api._dia_sp(datetime(2026, 9, 10, 2, 30, tzinfo=timezone.utc)) ==
"2026-09-09"`, com um comentário dizendo que `metering._today()` em UTC diria
`2026-09-10` — é essa a diferença que o teste trava.
Teste de não-contaminação: após um `/status` com sucesso, `db.kv_get(conn,
"aiUsageMonth", None, user_id=uid)` continua vazio e `metering.month_used(conn,
uid)` (seção default) continua 0.
Teste de 503 sem segredo: `monkeypatch.delenv("MCP_CLIENT_SECRET",
raising=False)` e afirme `r.status_code == 503` e
`r.json()["detail"]["code"] == "mcp_nao_configurado"`.

**5. `server/tests/test_mcp_vivo.py`** — opt-in:
`pytestmark = pytest.mark.skipif(not os.environ.get("MCP_CLIENT_SECRET"),
reason="teste ao vivo: exige MCP_CLIENT_SECRET no ambiente")`. Dois testes:
(a) token no `id.semente.dev` (afirma `access_token` não vazio e **imprime só o
tamanho**, nunca o valor); (b) `call_tool("get_option_chain", {"ticker":
"PETR4", "limit": 1})` imprime `trading_date` e afirma que é `str`. Acrescente
um terceiro que imprime o `structured_content` cru de `check_data_freshness` —
é dele que a Fase 2 tira a forma real do frescor. Nenhuma asserção sobre número
de mercado (o dado muda todo pregão).

**6. `server/tests/test_mcp_guardioes.py`** (extensão) — acrescente
`"options_mcp_api.py"` a `_ARQUIVOS_DA_FRONTEIRA` (guardião (i)) e os dois
guardiões que faltavam:
- **(iv)** toda rota de `app.routes` cujo `path` comece com
  `/api/options/mcp` tem `"require_user"` entre os nomes de dependência
  (reaproveite `_nomes_dependencias` de `test_adr013_cobertura_rotas`, copiando
  o helper) **e** o corpo da função da rota referencia `_cap_check` (por AST,
  em `options_mcp_api.py`). Afirme também que a lista de rotas não é vazia — um
  guardião que passa por vacuidade não guarda nada.
- **(v)** toda chamada a `metering.consume` dentro de `options_mcp_api.py` tem o
  keyword `month_section` com o literal `"mcpUsageMonth"` (por AST). Motivo na
  mensagem: sem isso o balde mensal do plano (`aiUsageMonth`) seria queimado por
  chamada de tool ([R-1]).
E um guardião de comportamento: `GET /api/options/mcp/status` sem header
`Authorization` → 401 (prova que a delegação de `require_user` é real, não só
um nome que agrada o guardião de cobertura).

**Commit:** `feat(260909-waw): rota /status, cap por usuario em SP e fiacao (aba-opcoes F1)`.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/server && .venv/bin/python -m pytest -q tests/test_mcp_cap.py tests/test_mcp_guardioes.py tests/test_mcp_vivo.py tests/test_adr013_cobertura_rotas.py tests/test_adr013_rbac.py tests/test_fase5_gate_mensal.py tests/test_fase12_cap_analises.py tests/test_opcoes_fronteira.py</automated>
  </verify>
  <done>`GET /api/options/mcp/status` existe, gateada por `require_user` e pelo cap; o dia do cap é o de São Paulo; `mcpUsage*` não contamina `aiUsage*`; allowlist de `test_adr013_cobertura_rotas` continua em 19; os 5 guardiões novos estão verdes e nenhum passa por vacuidade.</done>
</task>

<task type="auto">
  <name>Task 4: suíte canônica inteira e fechamento</name>
  <files>(nenhum arquivo novo — validação e, se preciso, correção pontual)</files>
  <action>
Rode a suíte canônica INTEIRA (`bash scripts/executar.sh --testes` — as DUAS
suítes: pytest do backend + `web/tests/*.mjs`; `scripts/test.sh` sozinho é meia
baseline e não conta). Cole a saída completa no SUMMARY.

Confira, além do verde:
- `bash scripts/test.sh` não regrediu em contagem (compare com a última medida
  registrada no `.planning/STATE.md`: 2110 passed em 2026-09-08);
- `git status` não traz arquivo não rastreado inesperado;
- `git diff --stat` bate com `files_modified` deste plano — **nenhum arquivo de
  `web/`, `web-admin/`, `server/web_dist`, `SERVER_BUILD_ID` ou Railway foi
  tocado** (fora de escopo, restrição do orquestrador);
- `docs/PLANO-aba-opcoes.md` está intocado (`git diff --name-only` não o lista);
- nenhum segredo commitado: `git diff --staged | grep -Ei "MCP_CLIENT_SECRET *=|eyJ[A-Za-z0-9_-]{10,}"` sem resultado.

Se um pin de dependência quebrar a suíte, **não relaxe o pin**: pare, registre a
versão que falhou e o erro, e reporte ao Alex (é decisão dele, §3.7 do PLANO).

Não rode `vite build` (nada em `web/src` mudou). Não faça deploy, não bumpe
`SERVER_BUILD_ID`.

Escreva o SUMMARY com: o que mudou; a saída das duas suítes; a decisão de
`/status` (200 com `bloqueia` em vez de 422) para o Alex confirmar; o achado do
`_dia`/`_mes` em `metering`; e o que fica pendente do lado do Alex (§7 do
PLANO: `MCP_CLIENTES`, `MCP_CLIENT_ID`/`MCP_CLIENT_SECRET` no Railway,
`credencial: "jwt"` em `/observabilidade`, e a premissa D-0.1 sobre onde o
Operador IA vira sub-tela).
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && bash scripts/executar.sh --testes</automated>
  </verify>
  <done>As duas suítes verdes, sem regressão de contagem; diff restrito a `files_modified`; SUMMARY escrito com a saída colada e as três pendências do Alex listadas.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Descrição |
|----------|-----------|
| Boris → id.semente.dev | `MCP_CLIENT_SECRET` sai do processo por TLS; é o único lugar onde o segredo viaja |
| Boris → mcp.semente.dev | access token Bearer; `MCP_URL` é entrada de operador e decide o destino |
| usuário logado → `/api/options/mcp/*` | consumo de cota do servidor (teto de 2.000/dia compartilhado por TODA a base) |

## STRIDE

| ID | Categoria | Componente | Disposição | Mitigação |
|----|-----------|------------|------------|-----------|
| T-waw-01 | Information Disclosure | `mcp_client` mensagens/log | mitigate | mensagens fixas; só `type(e).__name__` (nunca `{e!r}`); guardião (iii) proíbe literal com formato de segredo em `server/app/*.py`; teste afirma `segredo not in str(exc)` |
| T-waw-02 | Tampering | `MCP_URL` | mitigate | `url()` só aceita `https`; guardião (ii) limita literais com `://` às duas URLs do contrato |
| T-waw-03 | Denial of Service | teto de 2.000/dia do serviço | mitigate | cap por usuário (60) + rate (20/min) + teto global (1.800), recusa ANTES de chamar; cache L1 (900s/600s/3600s); semáforo de 4 |
| T-waw-04 | Elevation of Privilege | rota nova sem gate | mitigate | `Depends(require_user)` + guardião (iv) estrutural + teste de 401 sem header |
| T-waw-05 | Repudiation | uso não rastreado | mitigate | `obslog.log("mcp", ...)` por chamada, com `uid`, `cache`, `ms` |
| T-waw-06 | Spoofing | token de outro recurso | transfer | `resource` RFC 8707 obrigatório no `/token`; o `aud` é validado pelo serviço (contrato) |
| T-waw-SC | Tampering | instalação `pip` de `mcp` | accept | pacote `[VERIFICADO]` (SDK oficial, já instalado na venv, nominal no contrato e no PLANO aprovado) — sem checkpoint humano |
| T-waw-07 | Information Disclosure | licença "uso pessoal, sem redistribuição" | accept | risco aceito pelo Alex em D-0.2 do PLANO; registrado no ADR-027 §6 |
</threat_model>

<verification>
- Suíte canônica: `bash scripts/executar.sh --testes` (as DUAS suítes).
- Guardiões novos falham num módulo que aponte para fixture, embuta segredo,
  importe `mcp`/`httpx2` fora de `mcp_client`, ou use URL fora do contrato — e
  passam com o cliente entregue.
- Sem `MCP_CLIENT_SECRET`: `GET /api/options/mcp/status` → 503
  `mcp_nao_configurado`, e o resto do app não muda.
- Ao vivo (opt-in, só se o Alex já tiver posto as envs):
  `MCP_CLIENT_ID=... MCP_CLIENT_SECRET=... .venv/bin/python -m pytest -q tests/test_mcp_vivo.py -s`.
</verification>

<success_criteria>
Quatro commits atômicos em PT-BR referenciando `aba-opcoes F1` e `260909-waw`;
suíte canônica inteira verde com a saída colada no SUMMARY; ADR-027 no repo;
`mcp_client` como fronteira única provada por igualdade de conjunto; `/status`
gateada por sessão e por cap com o dia de São Paulo; zero arquivos de front,
zero deploy, `docs/PLANO-aba-opcoes.md` intocado.
</success_criteria>

<out_of_scope>
Rotas `/leitura`, `/cadeia`, `/operaveis`, `/proposta`, `/possibilidades`,
`/veredito`, `/setups/*`, `/glossario` (Fases 2–5); qualquer arquivo de
`web/` ou `web-admin/`; troca de aba e `goAgente` (Fase 2); compilador NL→DSL
(Fase 5); `FONTES` do `test_guardrail_imperativo` (entra na fase que criar os
textos fixos); `ENTIDADES_POR_PERMISSAO` para `opcoes.criar_setup` (Fase 5, com
a rota de escrita); consolidação dos módulos puros de payoff (ADR futuro, com
gatilho definido em ADR-027 §3); bump/deploy/TestFlight.
</out_of_scope>

<output>
Crie `.planning/quick/260909-waw-aba-opcoes-f1-adr027-cliente-mcp/260909-waw-SUMMARY.md` ao fim.
</output>
